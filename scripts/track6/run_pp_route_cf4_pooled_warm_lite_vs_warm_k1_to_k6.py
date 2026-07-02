#!/usr/bin/env python3
"""PP-ROUTE-CF4: pooled-condition Warm-lite retraining vs Warm.

Question:
- If Warm-lite is trained on all k=1..6 low-history exposure conditions as one
  pooled model, how does it compare with the retrained Warm clean stack?

Design:
- Same evaluation rows as CF3: Warm fixed-test rows that can support k=1..6.
- Warm-lite pooled retraining:
  * For each seed, build one augmented training set from k=1..6 exposure caps.
  * Fit one Quantile + LightGBM Huber residual stack per seed.
  * Evaluate that same model on k=1..6 truncated histories.
- Warm comparator:
  * Reuse CF3 Warm retrained clean stack predictions for identical seed/k/rows.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning


warnings.filterwarnings("ignore", message="X does not have valid feature names")
warnings.filterwarnings("ignore", category=ConvergenceWarning)

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_cgrp1_cold_group_price_stats_base as cgrp  # noqa: E402
import run_pp_wlite_q3_quantile_residual_correction_validation as q3  # noqa: E402
from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402


REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-ROUTE-CF4_pooled_warm_lite_vs_warm_k1_to_k6"
CF3_PREDS = REPO / "experiments" / "track6" / "PP-ROUTE-CF3_retrained_warm_vs_warm_lite_k1_to_k6" / "outputs" / "predictions_all_conditions.csv"

SEEDS = [20260612, 20260613, 20260614]
KS = [1, 2, 3, 4, 5, 6]


def ensure_dirs() -> None:
    for sub in ["artifacts", "outputs", "reports", "logs", "scripts"]:
        (EXP / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(__file__), EXP / "scripts" / Path(__file__).name)


def fmt(value: Any) -> str:
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (float, np.floating)):
        if not np.isfinite(value):
            return ""
        if abs(float(value) - round(float(value))) < 1e-9 and abs(float(value)) >= 1:
            return str(int(round(float(value))))
        return f"{float(value):.6f}"
    return str(value)


def md_table(frame: pd.DataFrame, cols: list[str], max_rows: int = 120) -> str:
    if frame.empty:
        return "_결과 없음_"
    view = frame[cols].head(max_rows).copy()
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(fmt(row[col]) for col in cols) + " |")
    if len(frame) > max_rows:
        lines.append(f"\n_Only first {max_rows} of {len(frame)} rows shown._")
    return "\n".join(lines)


def metrics(actual_price: np.ndarray, actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    actual_price = np.asarray(actual_price, dtype=float)
    actual_log = np.asarray(actual_log, dtype=float)
    pred_log = np.asarray(pred_log, dtype=float)
    valid = np.isfinite(actual_price) & (actual_price > 0) & np.isfinite(actual_log) & np.isfinite(pred_log)
    pred_price = np.clip(np.exp(pred_log[valid]), 1_000.0, None)
    ape = np.abs(pred_price - actual_price[valid]) / np.clip(actual_price[valid], 1.0, None)
    return {
        "n": int(valid.sum()),
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean((pred_log[valid] - actual_log[valid]) ** 2))),
    }


def add_ape(frame: pd.DataFrame, pred_col: str, out_col: str) -> pd.DataFrame:
    out = frame.copy()
    pred_price = np.clip(np.exp(pd.to_numeric(out[pred_col], errors="coerce")), 1_000.0, None)
    actual = pd.to_numeric(out["actual_price"], errors="coerce")
    out[out_col] = np.abs(pred_price - actual) / np.clip(actual, 1.0, None)
    return out


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def load_frames() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    warm_base = artifact_features()["warm"]
    needed = unique(
        warm_base
        + q3.cb3.NUM_BASE
        + q3.CAT_COLS
        + ["medium_support_bucket", "ln_price_krw", "price_krw", "_track6_row_id", "artist_key"]
    )
    needed = [col for col in needed if col != "grp_price_proxy"]
    train, _val, test = load_scope("warm", needed)
    train = train[unique([c for c in needed if c in train.columns] + ["ln_price_krw", "price_krw"])].reset_index(drop=True)
    test = test[unique([c for c in needed if c in test.columns] + ["ln_price_krw", "price_krw"])].reset_index(drop=True)

    counts = train.groupby(train["artist_key"].astype(str)).size()
    test["full_train_artist_history_n"] = test["artist_key"].astype(str).map(counts).fillna(0).astype(int)
    eligible = test["full_train_artist_history_n"] >= max(KS)
    test_eval = test.loc[eligible].sort_values("_track6_row_id").reset_index(drop=True)
    audit = {
        "warm_fixed_test_rows_total": int(len(test)),
        "exact_k1_to_k6_eligible_rows": int(len(test_eval)),
        "excluded_rows_with_less_than_6_history": int((~eligible).sum()),
        "min_full_train_artist_history_n": int(test_eval["full_train_artist_history_n"].min()),
        "max_full_train_artist_history_n": int(test_eval["full_train_artist_history_n"].max()),
    }
    return train, test_eval, audit


def cap_all_artists_for_training(train: pd.DataFrame, seed: int, exposure_k: int) -> pd.DataFrame:
    """Keep at most k+1 rows per artist so a train row can see roughly k peers."""
    rng = np.random.default_rng(seed + exposure_k * 10_000)
    cap_n = exposure_k + 1
    keep: list[np.ndarray] = []
    for _artist, idx in train.groupby(train["artist_key"].astype(str), sort=False).indices.items():
        idx_arr = np.asarray(idx, dtype=int)
        if len(idx_arr) > cap_n:
            keep.append(np.asarray(rng.choice(idx_arr, size=cap_n, replace=False), dtype=int))
        else:
            keep.append(idx_arr)
    out = train.iloc[np.concatenate(keep)].sort_values("_track6_row_id").reset_index(drop=True)
    out["training_exposure_k"] = exposure_k
    return out


def truncate_target_artists(train: pd.DataFrame, target_artists: set[str], seed: int, k: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    keep: list[np.ndarray] = []
    for artist, idx in train.groupby(train["artist_key"].astype(str), sort=False).indices.items():
        idx_arr = np.asarray(idx, dtype=int)
        if artist in target_artists and len(idx_arr) > k:
            keep.append(np.asarray(rng.choice(idx_arr, size=k, replace=False), dtype=int))
        else:
            keep.append(idx_arr)
    return train.iloc[np.concatenate(keep)].sort_values("_track6_row_id").reset_index(drop=True)


def train_pooled_warm_lite_stack(train: pd.DataFrame, seed: int) -> tuple[dict[str, object], pd.DataFrame]:
    base_ladder = list(cgrp.LADDER)
    parts: list[pd.DataFrame] = []
    stats_rows = []
    cgrp.LADDER = q3.LITE_LADDER + base_ladder
    try:
        for k in KS:
            capped = cap_all_artists_for_training(train, seed, k)
            capped_s = cgrp.train_with_internal_stats(capped)
            capped_s["training_exposure_k"] = k
            parts.append(capped_s)
            stats_rows.append(
                {
                    "seed": seed,
                    "training_exposure_k": k,
                    "rows": int(len(capped_s)),
                    "artists": int(capped_s["artist_key"].astype(str).nunique()),
                    "median_rows_per_artist": float(capped_s.groupby(capped_s["artist_key"].astype(str)).size().median()),
                }
            )
    finally:
        cgrp.LADDER = base_ladder
    pooled = pd.concat(parts, ignore_index=True)
    stack = q3.train_stack(pooled)
    return stack, pd.DataFrame(stats_rows)


def run_pooled_warm_lite_for_seed(train: pd.DataFrame, test: pd.DataFrame, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    stack, training_audit = train_pooled_warm_lite_stack(train, seed)
    base_ladder = list(cgrp.LADDER)
    target_artists = set(test["artist_key"].astype(str))
    parts: list[pd.DataFrame] = []
    cgrp.LADDER = q3.LITE_LADDER + base_ladder
    try:
        for k in KS:
            train_k = truncate_target_artists(train, target_artists, seed, k)
            test_s = cgrp.assign_group_stats(train_k, test)
            qpred = q3.apply_stack(test_s, stack)
            correction = np.clip(0.50 * qpred["lgb_residual"].to_numpy(dtype=float), -0.10, 0.10)
            pred_log = qpred["lgbq_full_lean_avg"].to_numpy(dtype=float) + correction
            out = test[["_track6_row_id", "artist_key", "price_krw", "ln_price_krw"]].copy()
            out = out.rename(columns={"price_krw": "actual_price", "ln_price_krw": "actual_log"})
            out["candidate"] = "Warm-lite pooled retrained"
            out["trunc_seed"] = seed
            out["k"] = k
            out["pred_log"] = pred_log
            out["q50_full_log"] = qpred["lgbq_full_q50"].to_numpy(dtype=float)
            out["q50_lean_log"] = qpred["lgbq_lean_q50"].to_numpy(dtype=float)
            out["quantile_uncertainty_width_log"] = qpred["lgbq_width"].to_numpy(dtype=float)
            out["lgb_huber_residual_log"] = qpred["lgb_residual"].to_numpy(dtype=float)
            out["applied_residual_correction_log"] = correction
            out["artist_history_n"] = k
            parts.append(out)
    finally:
        cgrp.LADDER = base_ladder
    return pd.concat(parts, ignore_index=True), training_audit


def load_warm_cf3(test_ids: set[int]) -> pd.DataFrame:
    if not CF3_PREDS.exists():
        raise RuntimeError(f"CF3 predictions missing: {CF3_PREDS}")
    raw = pd.read_csv(CF3_PREDS)
    warm = raw[raw["candidate"].eq("Warm retrained clean stack")].copy()
    warm = warm[warm["_track6_row_id"].astype(int).isin(test_ids)].copy()
    needed = len(SEEDS) * len(KS) * len(test_ids)
    if len(warm) != needed:
        raise RuntimeError(f"CF3 Warm row mismatch: got {len(warm)} expected {needed}")
    keep = ["_track6_row_id", "artist_key", "actual_price", "actual_log", "candidate", "trunc_seed", "k", "pred_log"]
    return warm[keep].copy()


def repeated_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (candidate, seed, k), group in predictions.groupby(["candidate", "trunc_seed", "k"], sort=True):
        row = {"candidate": candidate, "trunc_seed": int(seed), "k": int(k)}
        row.update(metrics(group["actual_price"].to_numpy(), group["actual_log"].to_numpy(), group["pred_log"].to_numpy()))
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["k", "candidate", "trunc_seed"]).reset_index(drop=True)


def seed_mean_predictions(predictions: pd.DataFrame) -> pd.DataFrame:
    return (
        predictions.groupby(["candidate", "k", "_track6_row_id"], as_index=False)
        .agg(
            artist_key=("artist_key", "first"),
            actual_price=("actual_price", "first"),
            actual_log=("actual_log", "first"),
            pred_log=("pred_log", "mean"),
            seed_n=("trunc_seed", "nunique"),
        )
        .sort_values(["k", "candidate", "_track6_row_id"])
        .reset_index(drop=True)
    )


def same_n_metrics(seed_mean: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (candidate, k), group in seed_mean.groupby(["candidate", "k"], sort=True):
        row = {"candidate": candidate, "k": int(k), "condition": f"k={int(k)} seed-mean"}
        row.update(metrics(group["actual_price"].to_numpy(), group["actual_log"].to_numpy(), group["pred_log"].to_numpy()))
        rows.append(row)
    out = pd.DataFrame(rows)
    for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
        out[f"rank_{metric}"] = out[metric].rank(method="min").astype(int)
    return out.sort_values(["k", "candidate"]).reset_index(drop=True)


def paired_by_k(seed_mean: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    warm = seed_mean[seed_mean["candidate"].eq("Warm retrained clean stack")].rename(columns={"pred_log": "warm_pred_log"})
    lite = seed_mean[seed_mean["candidate"].eq("Warm-lite pooled retrained")].rename(columns={"pred_log": "warm_lite_pooled_pred_log"})
    wide = warm[["_track6_row_id", "artist_key", "actual_price", "actual_log", "k", "warm_pred_log"]].merge(
        lite[["_track6_row_id", "k", "warm_lite_pooled_pred_log"]],
        on=["_track6_row_id", "k"],
        how="inner",
        validate="one_to_one",
    )
    wide = add_ape(wide, "warm_pred_log", "warm_ape")
    wide = add_ape(wide, "warm_lite_pooled_pred_log", "warm_lite_pooled_ape")
    rows = []
    for k, group in wide.groupby("k", sort=True):
        warm_ape = group["warm_ape"].to_numpy(dtype=float)
        lite_ape = group["warm_lite_pooled_ape"].to_numpy(dtype=float)
        rows.append(
            {
                "k": int(k),
                "n": int(len(group)),
                "warm_better_share": float(np.mean(warm_ape < lite_ape)),
                "warm_lite_pooled_better_share": float(np.mean(lite_ape < warm_ape)),
                "tie_share": float(np.mean(np.isclose(warm_ape, lite_ape))),
                "median_ape_delta_warm_minus_warm_lite_pooled": float(np.nanmedian(warm_ape - lite_ape)),
                "mean_ape_delta_warm_minus_warm_lite_pooled": float(np.nanmean(warm_ape - lite_ape)),
            }
        )
    return pd.DataFrame(rows), wide


def write_report(
    metrics_df: pd.DataFrame,
    repeated_df: pd.DataFrame,
    paired_df: pd.DataFrame,
    training_audit: pd.DataFrame,
    config: dict[str, Any],
) -> None:
    best_by_metric = {
        metric: str(metrics_df.sort_values(metric).iloc[0]["candidate"]) + " " + str(metrics_df.sort_values(metric).iloc[0]["condition"])
        for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]
    }
    lines = [
        "# PP-ROUTE-CF4 Pooled Warm-lite vs Warm k=1~6",
        "",
        "## 1. 목적",
        "",
        "Warm-lite를 k=1~6 전체 저이력 조건으로 한 번에 학습한 단일 모델로 만들고, 같은 seed/k/row에서 CF3 Warm retrained clean stack과 비교한다.",
        "",
        "## 2. 설계",
        "",
        "- Warm-lite pooled는 seed별 1개 모델이다. k=1~6 노출 조건을 합친 augmented train으로 학습한다.",
        "- 학습용 각 k 조건은 작가당 최대 k+1개 행을 남긴다. train 행 하나를 예측할 때 자기 행을 제외하고 대략 k개 같은작가 이력을 볼 수 있게 하기 위한 구성이다.",
        "- 평가 시에는 같은 작가 이력을 정확히 k개만 보이도록 test 작가 train history를 자른다.",
        "- Warm 비교값은 CF3에서 같은 조건으로 재학습한 `Warm retrained clean stack`을 재사용한다.",
        "",
        "## 3. Same-n seed-mean metrics",
        "",
        md_table(metrics_df, ["candidate", "condition", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "rank_MAPE", "rank_p95_APE"], 80),
        "",
        "## 4. 관찰 요약",
        "",
        f"- Best by MdAPE: `{best_by_metric['MdAPE']}`.",
        f"- Best by MAPE: `{best_by_metric['MAPE']}`.",
        f"- Best by p95 APE: `{best_by_metric['p95_APE']}`.",
        f"- Best by RMSE log: `{best_by_metric['RMSE_log']}`.",
        "",
        "## 5. Paired row-level comparison",
        "",
        md_table(paired_df, ["k", "n", "warm_better_share", "warm_lite_pooled_better_share", "median_ape_delta_warm_minus_warm_lite_pooled", "mean_ape_delta_warm_minus_warm_lite_pooled"], 20),
        "",
        "## 6. Repeated seed metrics",
        "",
        md_table(repeated_df, ["candidate", "trunc_seed", "k", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"], 80),
        "",
        "## 7. Pooled training audit",
        "",
        md_table(training_audit, ["seed", "training_exposure_k", "rows", "artists", "median_rows_per_artist"], 40),
        "",
        "## 8. 해석 주의",
        "",
        "- 이 실험은 Warm-lite를 전체 k 조건으로 학습한 단일 모델의 가능성을 보는 실험이다.",
        "- Warm 비교값은 CF3 clean stack 기준이며, 운영 WMIN8 artifact 전체 재생성 결과와 동일한 이름으로 부르면 안 된다.",
        "- k=5~6 Warm-lite는 여전히 공식 라우팅 범위 밖의 정책 스트레스 비교다.",
        "",
        "## 9. Config",
        "",
        "```json",
        json.dumps(config, ensure_ascii=False, indent=2),
        "```",
        "",
    ]
    (EXP / "reports" / "result_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    start = time.time()
    ensure_dirs()
    train, test, eligibility_audit = load_frames()
    warm_cf3 = load_warm_cf3(set(test["_track6_row_id"].astype(int)))

    pooled_parts: list[pd.DataFrame] = []
    training_audit_parts: list[pd.DataFrame] = []
    for seed in SEEDS:
        condition_start = time.time()
        preds, audit = run_pooled_warm_lite_for_seed(train, test, seed)
        pooled_parts.append(preds)
        training_audit_parts.append(audit)
        print(
            json.dumps(
                {
                    "done": "pooled_seed",
                    "seed": seed,
                    "rows": len(preds),
                    "seconds": round(time.time() - condition_start, 2),
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    pooled = pd.concat(pooled_parts, ignore_index=True)
    training_audit = pd.concat(training_audit_parts, ignore_index=True)
    predictions = pd.concat([warm_cf3, pooled], ignore_index=True, sort=False)
    repeated_df = repeated_metrics(predictions)
    seed_mean = seed_mean_predictions(predictions)
    if not seed_mean["seed_n"].eq(len(SEEDS)).all():
        raise RuntimeError("Seed mean table has missing seeds")
    metrics_df = same_n_metrics(seed_mean)
    paired_df, paired_rows = paired_by_k(seed_mean)

    predictions.to_csv(EXP / "outputs" / "predictions_all_conditions.csv", index=False)
    pooled.to_csv(EXP / "outputs" / "warm_lite_pooled_predictions_all_conditions.csv", index=False)
    training_audit.to_csv(EXP / "outputs" / "pooled_training_audit.csv", index=False)
    repeated_df.to_csv(EXP / "outputs" / "repeated_condition_metrics.csv", index=False)
    seed_mean.to_csv(EXP / "outputs" / "seed_mean_predictions_by_k.csv", index=False)
    metrics_df.to_csv(EXP / "outputs" / "same_n_metrics_by_k.csv", index=False)
    paired_df.to_csv(EXP / "outputs" / "paired_warm_vs_warm_lite_pooled_by_k.csv", index=False)
    paired_rows.to_csv(EXP / "outputs" / "paired_row_level_ape_by_k.csv", index=False)

    config = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment_id": "PP-ROUTE-CF4",
        "experiment_slug": EXP.name,
        "seeds": SEEDS,
        "k_values": KS,
        "base_eval_set": "Warm fixed-test rows with at least 6 same-artist train-history rows",
        "eligibility_audit": eligibility_audit,
        "warm_lite_pooled_training": {
            "training_exposures": "k=1..6 pooled per seed",
            "artist_cap_rule": "training exposure k keeps at most k+1 rows per artist",
            "group_stats": "5-fold internal stats on each capped exposure frame, then pooled",
            "model": "LightGBM Quantile full/lean + LightGBM objective=huber residual",
            "candidate": "lgbq_full_lean_avg + clip(0.50 * lgb_huber_residual, -0.10, +0.10)",
        },
        "warm_comparator": {
            "source": str(CF3_PREDS.relative_to(REPO)),
            "candidate": "Warm retrained clean stack",
        },
        "limitations": [
            "Warm comparator is CF3 clean stack, not exact historical WMIN8/PPV8 full artifact rebuild.",
            "Warm-lite k=5~6 remains outside the official Warm-lite route and is included as a stress comparison.",
            "Pooled training intentionally augments repeated low-history exposure conditions, so it should be treated as a new candidate family.",
        ],
        "seconds": round(time.time() - start, 2),
    }
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(metrics_df, repeated_df, paired_df, training_audit, config)

    print("[same-n metrics]")
    print(metrics_df.to_string(index=False))
    print("\n[paired by k]")
    print(paired_df.to_string(index=False))
    print("\n[config]")
    print(json.dumps(config, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
