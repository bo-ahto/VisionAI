#!/usr/bin/env python3
"""PP-PCOLD1: pseudo-cold 평가셋 구축 (Cold 로드맵 Phase 0.5).

0604가 Warm 시험 제출 전용으로 분리되면서 Cold에는 외부 검증 축이 없다.
대체재로, train의 거래량 하위 작가를 작가 단위로 마스킹해 unseen-artist 상황을
시뮬레이션하는 pseudo-cold 평가셋을 만든다.

- 마스킹 작가의 train 행 = pseudo-cold 평가행 (모델은 해당 작가를 본 적 없음)
- search-free v0.2식 LGB Quantile 파이프라인을 마스킹 train으로 재학습
  (v0.3/PP-Y18 체인은 상류 search 피처 의존으로 재학습 불가 → 커버리지만 감사)
- guard 임계값은 v0.2 방식 그대로 real cold validation 예측의 label-free 분위수로 재산정
- seed 3개 반복, real cold validation/test 대비 근사도와 선택 bias를 감사
- 용도: 이후 Cold 후보의 외부 검증 축. 후보/경계값 선택에는 사용 금지.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_cold_prediction_operational_v0_2 import (  # noqa: E402
    GUARD_WEIGHT, QUANTILES, quantile_pipeline,
)
from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-PCOLD1_pseudo_cold_eval_set"
V03_LOOKUP = REPO / "models" / "track6" / "cold_prediction_v0.3" / "config" / "search_delta_lookup_v0_3.json"

SEEDS = [20260610, 20260611, 20260612]
ARTIST_ROWS_MIN = 3
ARTIST_ROWS_MAX = 10
TARGET_EVAL_ROWS = 1200
MAX_ARTISTS = 250


def metric_row(price: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pred_price = np.clip(np.exp(np.asarray(pred_log, dtype=float)), 1_000.0, None)
    ape = np.abs(pred_price - price) / np.clip(price, 1.0, None)
    return {
        "n": int(len(ape)),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "within_30": float(np.mean(ape <= 0.30)),
        "over_50pct_error_rate": float(np.mean(ape > 0.50)),
    }


def fit_predict(train: pd.DataFrame, eval_frames: dict[str, pd.DataFrame], features: list[str]) -> dict[str, dict[str, np.ndarray]]:
    y = train["ln_price_krw"].to_numpy(dtype=float)
    models = {}
    for q, alpha in QUANTILES.items():
        pipe = quantile_pipeline(features, alpha)
        pipe.fit(train[features], y)
        models[q] = pipe
    out: dict[str, dict[str, np.ndarray]] = {}
    for name, frame in eval_frames.items():
        out[name] = {q: np.asarray(models[q].predict(frame[features]), dtype=float) for q in QUANTILES}
    return out


def guard_apply(preds: dict[str, np.ndarray], width_q67: float, gap_q50: float) -> tuple[np.ndarray, np.ndarray]:
    rep = preds["q50"]
    width = preds["q90"] - preds["q10"]
    comp = preds["q40"]
    mask = (width >= width_q67) & ((rep - comp) >= gap_q50) & (comp < rep)
    defense = rep.copy()
    defense[mask] = (1.0 - GUARD_WEIGHT) * rep[mask] + GUARD_WEIGHT * comp[mask]
    return defense, width


def main() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)

    features = artifact_features()["cold_lightgbm"]
    train, val, test = load_scope("cold", features)
    lookup_artists = set(json.loads(V03_LOOKUP.read_text(encoding="utf-8"))["artist_delta"].keys())

    counts = train.groupby("artist_key").size()
    pool = counts[(counts >= ARTIST_ROWS_MIN) & (counts <= ARTIST_ROWS_MAX)].index.to_numpy()

    metric_rows: list[dict] = []
    seed_summaries: list[dict] = []
    locked_rows: list[pd.DataFrame] = []

    for seed in SEEDS:
        rng = np.random.default_rng(seed)
        order = rng.permutation(pool)
        masked, total = [], 0
        for artist in order:
            if total >= TARGET_EVAL_ROWS or len(masked) >= MAX_ARTISTS:
                break
            masked.append(artist)
            total += int(counts[artist])
        masked_set = set(masked)

        is_masked = train["artist_key"].isin(masked_set)
        train_masked = train[~is_masked]
        pseudo = train[is_masked].copy()

        preds = fit_predict(train_masked, {"pseudo": pseudo, "val": val, "test": test}, features)

        # v0.2 방식 그대로: guard 임계값은 real cold validation 예측의 label-free 분위수.
        val_rep = preds["val"]["q50"]
        val_width = preds["val"]["q90"] - preds["val"]["q10"]
        width_q67 = float(np.quantile(val_width, 0.67))
        gap_q50 = float(np.quantile(val_rep - preds["val"]["q40"], 0.50))

        per_split = {}
        for name, frame in (("pseudo_cold", pseudo), ("real_cold_validation", val), ("real_cold_test", test)):
            key = "pseudo" if name == "pseudo_cold" else ("val" if name == "real_cold_validation" else "test")
            defense, width = guard_apply(preds[key], width_q67, gap_q50)
            price = frame["price_krw"].to_numpy(dtype=float)
            for cand, pred_log in (("representative_q50", preds[key]["q50"]), ("defense_guard", defense)):
                metric_rows.append({"seed": seed, "eval_set": name, "candidate": cand,
                                    **metric_row(price, pred_log)})
            per_split[name] = {"defense": defense, "width": width}

        defense, width = per_split["pseudo_cold"]["defense"], per_split["pseudo_cold"]["width"]
        locked = pd.DataFrame({
            "seed": seed,
            "_track6_row_id": pseudo["_track6_row_id"].to_numpy(),
            "artist_key": pseudo["artist_key"].to_numpy(),
            "actual_price": pseudo["price_krw"].to_numpy(dtype=float),
            "actual_log": pseudo["ln_price_krw"].to_numpy(dtype=float),
            "rep_pred_log": preds["pseudo"]["q50"],
            "defense_pred_log": defense,
            "qwidth_log": width,
            "search_lookup_covered": pseudo["artist_key"].astype(str).isin(lookup_artists).to_numpy(),
        })
        locked_rows.append(locked)

        seed_summaries.append({
            "seed": seed,
            "masked_artists": len(masked),
            "pseudo_rows": int(len(pseudo)),
            "train_rows_remaining": int(len(train_masked)),
            "search_lookup_coverage_pseudo": float(locked["search_lookup_covered"].mean()),
            "guard_width_q67": width_q67,
            "guard_gap_q50": gap_q50,
        })

    metrics = pd.DataFrame(metric_rows)
    metrics.to_csv(EXP / "outputs" / "pseudo_cold_metrics.csv", index=False)
    pd.concat(locked_rows, ignore_index=True).to_csv(EXP / "outputs" / "pseudo_cold_rows.csv", index=False)

    # 선택 bias 감사: pseudo-cold 행 vs real cold validation/test 분포.
    def dist_profile(frame: pd.DataFrame, label: str, price_col: str) -> dict:
        med = frame.groupby("medium_category").size().sort_values(ascending=False)
        return {
            "set": label,
            "n": int(len(frame)),
            "price_median_krw": float(frame[price_col].median()),
            "price_q90_krw": float(frame[price_col].quantile(0.90)),
            "log_area_median": float(frame["log_area"].median()),
            "top3_medium_share": float(med.head(3).sum() / max(len(frame), 1)),
            "top_medium": str(med.index[0]) if len(med) else "",
        }

    pseudo_all = pd.concat([train[train["artist_key"].isin(set(s))] for s in
                            [pd.concat(locked_rows)["artist_key"].unique()]], ignore_index=True)
    bias = pd.DataFrame([
        dist_profile(pseudo_all, "pseudo_cold(all seeds)", "price_krw"),
        dist_profile(val, "real_cold_validation", "price_krw"),
        dist_profile(test, "real_cold_test", "price_krw"),
    ])
    bias.to_csv(EXP / "outputs" / "bias_audit.csv", index=False)

    agg = (metrics.groupby(["eval_set", "candidate"])[["MdAPE", "MAPE", "p95_APE"]]
           .agg(["mean", "std"]).round(4))

    config = {
        "experiment_id": "PP-PCOLD1",
        "purpose": "pseudo-cold 평가셋 (0604 대체 외부 검증 축, 후보 선택 사용 금지)",
        "mask_rule": f"train 작가 중 행수 {ARTIST_ROWS_MIN}~{ARTIST_ROWS_MAX} 작가를 seed별 무작위 마스킹 "
                     f"(목표 {TARGET_EVAL_ROWS}행 또는 최대 {MAX_ARTISTS}작가)",
        "seeds": SEEDS,
        "pipeline": "v0.2 search-free LGB Quantile (q10/q40/q50/q90) + label-free guard 재산정",
        "limitation": "v0.3/PP-Y18 체인은 상류 search 피처 의존으로 pseudo-cold 재학습 불가 — 검색 lookup 커버리지만 감사",
        "seed_summaries": seed_summaries,
        "base_reference": "experiments/track6/PP-CBASE1_cold_base_lock/outputs/cold_base_performance_summary.csv",
    }
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    report = [
        "# PP-PCOLD1 pseudo-cold 평가셋",
        "",
        "- 용도: Cold 후보의 외부 검증 축 (0604는 Warm 시험 제출 전용이므로 사용 금지).",
        "- 후보/경계값 선택에는 사용하지 않는다.",
        "",
        "## seed별 구성",
        "",
        json.dumps(seed_summaries, ensure_ascii=False, indent=2),
        "",
        "## 지표 (seed 평균/표준편차)",
        "",
        agg.to_string(),
        "",
        "## 선택 bias 감사",
        "",
        bias.to_string(index=False),
    ]
    (EXP / "reports" / "result_report.md").write_text("\n".join(report), encoding="utf-8")

    print(agg.to_string())
    print()
    print(bias.to_string(index=False))
    print()
    print(json.dumps(seed_summaries, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
