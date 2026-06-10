#!/usr/bin/env python3
"""PP-CCONF1: Cold 신뢰도 tier 정책 (Cold 로드맵 Phase 2-1).

Warm PP-CF1의 신뢰도 tier 방식을 Cold에 이식한다. 점 예측은 바꾸지 않고,
정답을 사용하지 않는 신호만으로 행 단위 신뢰도 tier를 정의해 서비스 표시
정책(점 예측/가격 범위/검수 플래그)의 근거를 만든다.

- tier 경계는 validation 분위수로 동결(test/pseudo-cold는 확인 전용)
- research tier: qwidth + 모델 gap(|y18 - v0.2|) + 검색 lookup 커버리지
- operational tier: v0.2 qwidth 단독 (raw-input 환경에서 계산 가능한 신호만)
- v0.2 q10~q90 가격 범위의 tier별 실제 적중률 감사
- 기존 v0.3 검수 플래그(qwidth>=q67 OR 미커버, test 검수율 45.2%)와 통합 비교
- 외부 검증: PP-PCOLD1 pseudo-cold에서 tier 분리 방향 일치(seed 3개) 확인
- 0604는 Warm 시험 제출 전용 — 사용하지 않는다.
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

from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
CBASE = REPO / "experiments" / "track6" / "PP-CBASE1_cold_base_lock" / "outputs" / "fixed_cold_base_rows.csv"
PCOLD = REPO / "experiments" / "track6" / "PP-PCOLD1_pseudo_cold_eval_set" / "outputs" / "pseudo_cold_rows.csv"
V02 = REPO / "models" / "track6" / "cold_prediction_v0.2_operational"
V03_PARAMS = REPO / "models" / "track6" / "cold_prediction_v0.3" / "config" / "cold_postprocess_params_v0_3.json"
EXP = REPO / "experiments" / "track6" / "PP-CCONF1_cold_confidence_tier_policy"

BASES = {"research": "research_base_pred_log", "operational": "v02_defense_pred_log"}


def load_module(path: Path, name: str):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def metric_block(part: pd.DataFrame, ape_col: str) -> dict[str, float]:
    ape = part[ape_col].to_numpy(dtype=float)
    return {
        "n": int(len(ape)),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "within_30": float(np.mean(ape <= 0.30)),
        "over_50pct_error_rate": float(np.mean(ape > 0.50)),
    }


def main() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(CBASE)
    df["model_gap_abs"] = (df["y18_qwidth_pred_log"] - df["v02_defense_pred_log"]).abs()
    for name, col in BASES.items():
        pred_price = np.clip(np.exp(df[col]), 1_000.0, None)
        df[f"ape_{name}"] = np.abs(pred_price - df["actual_price"]) / np.clip(df["actual_price"], 1.0, None)

    val = df[df["split"] == "validation"]
    bounds = {
        "qw_q33": float(val["quantile_width_log"].quantile(0.33)),
        "qw_q90": float(val["quantile_width_log"].quantile(0.90)),
        "gap_q50": float(val["model_gap_abs"].quantile(0.50)),
        "gap_q90": float(val["model_gap_abs"].quantile(0.90)),
        "v02_qw_q33": float(val["v02_qwidth_log"].quantile(0.33)),
        "v02_qw_q90": float(val["v02_qwidth_log"].quantile(0.90)),
    }

    def research_tier(d: pd.DataFrame) -> pd.Series:
        low = (d["quantile_width_log"] >= bounds["qw_q90"]) | (d["model_gap_abs"] >= bounds["gap_q90"])
        high = ((d["quantile_width_log"] <= bounds["qw_q33"]) & (d["model_gap_abs"] <= bounds["gap_q50"])
                & d["search_covered"].astype(bool) & ~low)
        return pd.Series(np.select([low, high], ["low", "high"], default="medium"), index=d.index)

    def operational_tier(qwidth: pd.Series) -> pd.Series:
        low = qwidth >= bounds["v02_qw_q90"]
        high = (qwidth <= bounds["v02_qw_q33"]) & ~low
        return pd.Series(np.select([low, high], ["low", "high"], default="medium"), index=qwidth.index)

    df["tier_research"] = research_tier(df)
    df["tier_operational"] = operational_tier(df["v02_qwidth_log"])

    # v0.2 q10/q90 가격 범위 적중률 (직렬화 예측기로 재계산, 재현 가능)
    features = artifact_features()["cold_lightgbm"]
    _, fval, ftest = load_scope("cold", features)
    predictor = load_module(V02 / "predict" / "predict_cold_operational_v0_2.py", "predict_cold_operational_v0_2")
    models = predictor.load_models()
    guard = predictor.load_guard()
    ranges = []
    for split, frame in (("validation", fval), ("test", ftest)):
        out = predictor.predict(frame, models=models, guard=guard)
        ranges.append(pd.DataFrame({
            "split": split,
            "_track6_row_id": frame["_track6_row_id"].to_numpy(),
            "range_low_log": out["q10_pred_log"].to_numpy(dtype=float),
            "range_high_log": out["q90_pred_log"].to_numpy(dtype=float),
        }))
    df = df.merge(pd.concat(ranges, ignore_index=True), on=["split", "_track6_row_id"],
                  how="left", validate="one_to_one")
    df["range_hit"] = (df["actual_log"] >= df["range_low_log"]) & (df["actual_log"] <= df["range_high_log"])

    # tier별 성능/범위 적중률
    rows = []
    for tier_col in ("tier_research", "tier_operational"):
        for (split, tier), part in df.groupby(["split", tier_col]):
            for base in BASES:
                rows.append({
                    "tier_scheme": tier_col, "split": split, "tier": tier, "base": base,
                    **metric_block(part, f"ape_{base}"),
                    "share": float(len(part) / len(df[df["split"] == split])),
                    "range_q10_q90_hit_rate": float(part["range_hit"].mean()),
                })
    tier_metrics = pd.DataFrame(rows).sort_values(["tier_scheme", "split", "base", "tier"])
    tier_metrics.to_csv(EXP / "outputs" / "tier_metrics.csv", index=False)

    # 기존 v0.3 검수 플래그와 비교
    v03_qw_q67 = float(json.loads(V03_PARAMS.read_text(encoding="utf-8"))["guard"]["qwidth_q67"])
    df["review_flag_v03"] = (df["quantile_width_log"] >= v03_qw_q67) | (~df["search_covered"].astype(bool))
    review = []
    for split, part in df.groupby("split"):
        review.append({
            "split": split,
            "v03_review_rate": float(part["review_flag_v03"].mean()),
            "tier_low_rate": float((part["tier_research"] == "low").mean()),
            "low_and_v03_overlap": float(((part["tier_research"] == "low") & part["review_flag_v03"]).mean()),
            "v03_review_MAPE_research": float(part.loc[part["review_flag_v03"], "ape_research"].mean()),
            "tier_low_MAPE_research": float(part.loc[part["tier_research"] == "low", "ape_research"].mean()),
        })
    review_df = pd.DataFrame(review)
    review_df.to_csv(EXP / "outputs" / "review_flag_comparison.csv", index=False)

    # 외부 검증: pseudo-cold에서 operational tier 분리 방향 (seed별)
    pc = pd.read_csv(PCOLD)
    pc["tier"] = operational_tier(pc["qwidth_log"])
    pc_pred = np.clip(np.exp(pc["defense_pred_log"]), 1_000.0, None)
    pc["ape"] = np.abs(pc_pred - pc["actual_price"]) / np.clip(pc["actual_price"], 1.0, None)
    pc_rows = []
    for (seed, tier), part in pc.groupby(["seed", "tier"]):
        pc_rows.append({"seed": int(seed), "tier": tier, "n": int(len(part)),
                        "MdAPE": float(part["ape"].median()), "MAPE": float(part["ape"].mean())})
    pc_metrics = pd.DataFrame(pc_rows).sort_values(["seed", "tier"])
    pc_metrics.to_csv(EXP / "outputs" / "pseudo_cold_tier_metrics.csv", index=False)
    direction_ok = []
    for seed, part in pc_metrics.groupby("seed"):
        m = part.set_index("tier")["MdAPE"]
        ok = bool(m.get("high", np.inf) < m.get("medium", np.inf) < m.get("low", -np.inf) or
                  (m.get("high", np.inf) < m.get("medium", np.inf) and m.get("medium", np.inf) < m.get("low", np.inf)))
        direction_ok.append({"seed": int(seed), "high_lt_medium_lt_low_MdAPE": ok})

    df[["split", "_track6_row_id", "artist_key", "tier_research", "tier_operational",
        "review_flag_v03", "range_low_log", "range_high_log", "range_hit"]].to_csv(
        EXP / "outputs" / "tier_assignments.csv", index=False)

    config = {
        "experiment_id": "PP-CCONF1",
        "purpose": "Cold 신뢰도 tier 정책 (점 예측 변경 없음, 표시/검수 정책 근거)",
        "tier_bounds_frozen_from_validation": bounds,
        "tier_rules": {
            "research": "low: qwidth>=val_q90 OR model_gap>=val_q90; "
                        "high: qwidth<=val_q33 AND model_gap<=val_q50 AND search_covered; else medium",
            "operational": "low: v02_qwidth>=val_q90; high: v02_qwidth<=val_q33; else medium",
        },
        "v03_review_flag_rule": f"qwidth >= {v03_qw_q67} OR not search_covered",
        "pseudo_cold_direction_check": direction_ok,
        "sources": {
            "base_rows": str(CBASE.relative_to(REPO)),
            "pseudo_cold_rows": str(PCOLD.relative_to(REPO)),
            "v0_2_predictor": "models/track6/cold_prediction_v0.2_operational/predict/predict_cold_operational_v0_2.py",
        },
        "prohibitions": ["0604 사용 금지", "tier 경계의 test/pseudo-cold 기반 조정 금지"],
    }
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    show = tier_metrics.copy()
    for c in ("MdAPE", "MAPE", "p95_APE", "within_30", "over_50pct_error_rate", "share", "range_q10_q90_hit_rate"):
        show[c] = show[c].map(lambda v: f"{v:.4f}")
    report = [
        "# PP-CCONF1 Cold 신뢰도 tier 정책",
        "",
        "- tier 경계는 validation 분위수 동결. test/pseudo-cold는 확인 전용.",
        "- 0604 미사용 (Warm 시험 제출 전용).",
        "",
        "## tier별 성능",
        "",
        show.to_string(index=False),
        "",
        "## 기존 v0.3 검수 플래그 비교",
        "",
        review_df.to_string(index=False),
        "",
        "## pseudo-cold 방향 일치 (operational tier)",
        "",
        pc_metrics.to_string(index=False),
        "",
        json.dumps(direction_ok, ensure_ascii=False),
    ]
    (EXP / "reports" / "result_report.md").write_text("\n".join(report), encoding="utf-8")

    print(show.to_string(index=False))
    print()
    print(review_df.to_string(index=False))
    print()
    print(pc_metrics.to_string(index=False))
    print(json.dumps(direction_ok, ensure_ascii=False))


if __name__ == "__main__":
    main()
