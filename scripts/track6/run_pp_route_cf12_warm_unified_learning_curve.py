#!/usr/bin/env python3
"""PP-ROUTE-CF12: learning-curve check for the unified Warm route.

Question: if Warm training data grows, does the currently promoted
Warm-lite unified route_gap_q50 model improve?

Design:
- Keep the fixed test split unchanged.
- Train the same model family with deterministic row-level subsets of the
  original warm train split.
- Evaluate (1) all test rows that are Warm-routable at each subset size and
  (2) a fixed cohort that is Warm-routable at every subset size.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import freeze_warm_lite_unified_route_gap_q50_candidate as freeze  # noqa: E402
import run_pp_cgrp1_cold_group_price_stats_base as cgrp  # noqa: E402
import run_pp_wlite_q3_quantile_residual_correction_validation as q3  # noqa: E402
from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402


REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-ROUTE-CF12_warm_unified_learning_curve"
SAMPLE_SEEDS = [20260617, 20260618, 20260619]
MODEL_SEED = 20260617
TRAIN_FRACTIONS = [0.25, 0.50, 0.75, 1.00]
ROUTE_GAP_THRESHOLD = 0.0252975144340901


def ensure_dirs() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def metrics(frame: pd.DataFrame, pred_col: str = "pred_log") -> dict[str, float]:
    actual_price = frame["price_krw"].to_numpy(dtype=float)
    actual_log = frame["ln_price_krw"].to_numpy(dtype=float)
    pred_log = frame[pred_col].to_numpy(dtype=float)
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


def md_table(frame: pd.DataFrame) -> str:
    cols = list(frame.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in frame.iterrows():
        vals = []
        for col in cols:
            value = row[col]
            if isinstance(value, float):
                vals.append(f"{value:.6f}")
            else:
                vals.append(str(value))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def load_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    needed = unique(
        artifact_features()["warm"]
        + q3.cb3.NUM_BASE
        + q3.CAT_COLS
        + ["medium_support_bucket", "ln_price_krw", "log_area", "price_krw", "_track6_row_id", "artist_key"]
    )
    needed = [col for col in needed if col != "grp_price_proxy"]
    train, _val, test = load_scope("warm", needed)
    keep = unique([c for c in needed if c in train.columns] + ["ln_price_krw", "log_area", "price_krw"])
    return (
        train[keep].sort_values("_track6_row_id").reset_index(drop=True),
        test[keep].sort_values("_track6_row_id").reset_index(drop=True),
    )


def sample_train(train: pd.DataFrame, fraction: float, sample_seed: int) -> pd.DataFrame:
    if fraction >= 0.999:
        return train.copy().reset_index(drop=True)
    rng = np.random.default_rng(sample_seed)
    order = rng.permutation(len(train))
    n = max(1, int(round(len(train) * fraction)))
    keep = np.sort(order[:n])
    return train.iloc[keep].sort_values("_track6_row_id").reset_index(drop=True)


def history_counts(train_subset: pd.DataFrame, test: pd.DataFrame) -> pd.Series:
    counts = train_subset.groupby(train_subset["artist_key"].astype(str)).size()
    return test["artist_key"].astype(str).map(counts).fillna(0).astype(int)


def assign_eval_stats(train_subset: pd.DataFrame, test_subset: pd.DataFrame) -> pd.DataFrame:
    base_ladder = list(cgrp.LADDER)
    cgrp.LADDER = q3.LITE_LADDER + base_ladder
    try:
        return cgrp.assign_group_stats(train_subset, test_subset)
    finally:
        cgrp.LADDER = base_ladder


def predict_with_stack(stack: dict[str, object], eval_s: pd.DataFrame) -> pd.DataFrame:
    qpred = q3.apply_stack(eval_s, stack)
    current = qpred["lgbq_full_lean_avg"].to_numpy(dtype=float) + np.clip(
        0.50 * qpred["lgb_residual"].to_numpy(dtype=float),
        -0.10,
        0.10,
    )
    cf7 = qpred["lgbq_full_lean_avg"].to_numpy(dtype=float) + np.clip(
        qpred["lgb_residual"].to_numpy(dtype=float),
        -0.15,
        0.15,
    )
    gap = np.abs(
        qpred["lgbq_full_q50"].to_numpy(dtype=float) - qpred["lgbq_lean_q50"].to_numpy(dtype=float)
    )
    route_to_cf7 = gap >= ROUTE_GAP_THRESHOLD
    pred = current.copy()
    pred[route_to_cf7] = cf7[route_to_cf7]
    out = pd.DataFrame(index=eval_s.index)
    out["pred_log"] = pred
    out["current_pred_log"] = current
    out["cf7_pred_log"] = cf7
    out["route_to_cf7"] = route_to_cf7
    out["full_lean_gap_abs_log"] = gap
    out["lgbq_width"] = qpred["lgbq_width"].to_numpy(dtype=float)
    out["lgb_huber_residual_log"] = qpred["lgb_residual"].to_numpy(dtype=float)
    return out


def run_fraction(
    train: pd.DataFrame,
    test: pd.DataFrame,
    fraction: float,
    sample_seed: int,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    train_subset = sample_train(train, fraction, sample_seed)
    train_s = freeze.train_with_stats(train_subset)
    stack = freeze.train_seed_stack(train_s, MODEL_SEED)
    audit = {
        "sample_seed": sample_seed,
        "model_seed": MODEL_SEED,
        "train_rows": int(len(train_s)),
        "train_artists": int(train_s["artist_key"].astype(str).nunique()),
        "median_train_rows_per_artist": float(train_s.groupby(train_s["artist_key"].astype(str)).size().median()),
    }
    counts = history_counts(train_subset, test)
    eligible_mask = counts >= 1
    eval_frame = test.loc[eligible_mask].copy().reset_index(drop=True)
    eval_frame["artist_history_n"] = counts.loc[eligible_mask].to_numpy(dtype=int)
    eval_s = assign_eval_stats(train_subset, eval_frame)
    pred = predict_with_stack(stack, eval_s)
    out = eval_frame.copy()
    for col in pred.columns:
        out[col] = pred[col].to_numpy()
    out["train_fraction"] = fraction
    out["sample_seed"] = sample_seed
    out["model_seed"] = MODEL_SEED
    out["train_rows"] = len(train_subset)
    out["train_artists"] = train_subset["artist_key"].astype(str).nunique()
    out["test_warm_eligible_rows"] = len(out)
    out["test_warm_coverage"] = len(out) / len(test)
    audit.update(
        {
            "train_fraction": fraction,
            "sampled_train_rows": int(len(train_subset)),
            "sampled_train_artists": int(train_subset["artist_key"].astype(str).nunique()),
            "test_rows_total": int(len(test)),
            "test_warm_eligible_rows": int(len(out)),
            "test_warm_coverage": float(len(out) / len(test)),
            "history_n_median_on_eligible_test": float(out["artist_history_n"].median()) if len(out) else None,
        }
    )
    return out, audit


def main() -> None:
    ensure_dirs()
    train, test = load_frames()
    predictions = []
    audits = []
    for sample_seed in SAMPLE_SEEDS:
        for fraction in TRAIN_FRACTIONS:
            pred, audit = run_fraction(train, test, fraction, sample_seed)
            predictions.append(pred)
            audits.append(audit)

    all_preds = pd.concat(predictions, ignore_index=True)
    all_preds.to_csv(EXP / "outputs" / "learning_curve_predictions.csv", index=False)
    pd.DataFrame(audits).to_csv(EXP / "outputs" / "training_audit.csv", index=False)

    rows = []
    for (sample_seed, fraction), group in all_preds.groupby(["sample_seed", "train_fraction"], sort=True):
        row = {"sample_seed": sample_seed, "cohort": "eligible_at_each_fraction", "train_fraction": fraction}
        row.update(metrics(group))
        row["coverage"] = float(group["test_warm_coverage"].iloc[0])
        row["train_rows"] = int(group["train_rows"].iloc[0])
        row["train_artists"] = int(group["train_artists"].iloc[0])
        row["median_history_n"] = float(group["artist_history_n"].median())
        rows.append(row)

    fixed_parts = []
    fixed_ids_by_seed: dict[int, set[int]] = {}
    for sample_seed, seed_preds in all_preds.groupby("sample_seed", sort=True):
        ids_by_fraction = {
            fraction: set(group["_track6_row_id"].astype(int))
            for fraction, group in seed_preds.groupby("train_fraction", sort=True)
        }
        fixed_ids = set.intersection(*ids_by_fraction.values())
        fixed_ids_by_seed[int(sample_seed)] = fixed_ids
        fixed_seed = seed_preds[seed_preds["_track6_row_id"].astype(int).isin(fixed_ids)].copy()
        fixed_parts.append(fixed_seed)
        for fraction, group in fixed_seed.groupby("train_fraction", sort=True):
            row = {
                "sample_seed": sample_seed,
                "cohort": "fixed_cohort_eligible_all_fractions",
                "train_fraction": fraction,
            }
            row.update(metrics(group))
            row["coverage"] = float(len(fixed_ids) / len(test))
            row["train_rows"] = int(group["train_rows"].iloc[0])
            row["train_artists"] = int(group["train_artists"].iloc[0])
            row["median_history_n"] = float(group["artist_history_n"].median())
            rows.append(row)
    fixed = pd.concat(fixed_parts, ignore_index=True)
    fixed.to_csv(EXP / "outputs" / "fixed_cohort_predictions.csv", index=False)

    summary = pd.DataFrame(rows).sort_values(["sample_seed", "cohort", "train_fraction"]).reset_index(drop=True)
    summary.to_csv(EXP / "outputs" / "learning_curve_metrics.csv", index=False)

    deltas_by_seed = []
    for sample_seed, seed_summary in summary.groupby("sample_seed", sort=True):
        fixed_summary = seed_summary[seed_summary["cohort"].eq("fixed_cohort_eligible_all_fractions")]
        baseline_fixed = fixed_summary[fixed_summary["train_fraction"].eq(min(TRAIN_FRACTIONS))].iloc[0]
        final_fixed = fixed_summary[fixed_summary["train_fraction"].eq(max(TRAIN_FRACTIONS))].iloc[0]
        eligible_summary = seed_summary[seed_summary["cohort"].eq("eligible_at_each_fraction")]
        deltas_by_seed.append(
            {
                "sample_seed": int(sample_seed),
                "fixed_cohort_n": int(final_fixed["n"]),
                "from_fraction": float(min(TRAIN_FRACTIONS)),
                "to_fraction": float(max(TRAIN_FRACTIONS)),
                "delta_MdAPE": float(final_fixed["MdAPE"] - baseline_fixed["MdAPE"]),
                "delta_MAPE": float(final_fixed["MAPE"] - baseline_fixed["MAPE"]),
                "delta_p95_APE": float(final_fixed["p95_APE"] - baseline_fixed["p95_APE"]),
                "delta_RMSE_log": float(final_fixed["RMSE_log"] - baseline_fixed["RMSE_log"]),
                "coverage_at_min_fraction": float(
                    eligible_summary[eligible_summary["train_fraction"].eq(min(TRAIN_FRACTIONS))].iloc[0]["coverage"]
                ),
                "coverage_at_full_fraction": float(
                    eligible_summary[eligible_summary["train_fraction"].eq(max(TRAIN_FRACTIONS))].iloc[0]["coverage"]
                ),
            }
        )
    deltas_frame = pd.DataFrame(deltas_by_seed)
    deltas_frame.to_csv(EXP / "outputs" / "learning_curve_deltas_by_seed.csv", index=False)

    agg = (
        summary.groupby(["cohort", "train_fraction"], as_index=False)
        .agg(
            n_mean=("n", "mean"),
            MdAPE_mean=("MdAPE", "mean"),
            MdAPE_std=("MdAPE", "std"),
            MAPE_mean=("MAPE", "mean"),
            MAPE_std=("MAPE", "std"),
            p95_APE_mean=("p95_APE", "mean"),
            p95_APE_std=("p95_APE", "std"),
            RMSE_log_mean=("RMSE_log", "mean"),
            RMSE_log_std=("RMSE_log", "std"),
            coverage_mean=("coverage", "mean"),
            median_history_n_mean=("median_history_n", "mean"),
        )
        .sort_values(["cohort", "train_fraction"])
        .reset_index(drop=True)
    )
    agg.to_csv(EXP / "outputs" / "learning_curve_metrics_aggregate.csv", index=False)

    deltas = {
        "sample_seeds": SAMPLE_SEEDS,
        "model_seed": MODEL_SEED,
        "from_fraction": float(min(TRAIN_FRACTIONS)),
        "to_fraction": float(max(TRAIN_FRACTIONS)),
        "delta_mean": {
            "MdAPE": float(deltas_frame["delta_MdAPE"].mean()),
            "MAPE": float(deltas_frame["delta_MAPE"].mean()),
            "p95_APE": float(deltas_frame["delta_p95_APE"].mean()),
            "RMSE_log": float(deltas_frame["delta_RMSE_log"].mean()),
            "coverage": float(
                (deltas_frame["coverage_at_full_fraction"] - deltas_frame["coverage_at_min_fraction"]).mean()
            ),
        },
        "delta_min": {
            "MdAPE": float(deltas_frame["delta_MdAPE"].max()),
            "MAPE": float(deltas_frame["delta_MAPE"].max()),
            "p95_APE": float(deltas_frame["delta_p95_APE"].max()),
            "RMSE_log": float(deltas_frame["delta_RMSE_log"].max()),
        },
        "deltas_by_seed": deltas_by_seed,
    }
    (EXP / "artifacts" / "learning_curve_summary.json").write_text(
        json.dumps(
            {
                "experiment_id": "PP-ROUTE-CF12",
                "question": "Does unified Warm accuracy improve as training data grows?",
                "sample_seeds": SAMPLE_SEEDS,
                "model_seed": MODEL_SEED,
                "train_fractions": TRAIN_FRACTIONS,
                "route_gap_threshold": ROUTE_GAP_THRESHOLD,
                "deltas": deltas,
                "interpretation": (
                    "Negative deltas indicate improvement. This is a controlled offline learning-curve proxy, "
                    "not a guarantee that arbitrary future data improves production."
                ),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    report = "\n".join(
        [
            "# PP-ROUTE-CF12 Warm unified learning curve",
            "",
            "## 목적",
            "",
            "운영 중 학습 데이터가 늘어나면 현재 official 0.1v Warm 기본 모델의 정확도가 개선될 가능성이 있는지 확인한다.",
            "",
            "## 설계",
            "",
            "- fixed test split은 고정한다.",
            "- warm train split만 25%, 50%, 75%, 100%로 늘린다.",
            "- 각 비율마다 같은 모델 계열을 재학습한다.",
            "- `eligible_at_each_fraction`은 각 비율에서 Warm 이력이 1건 이상 있는 test 행 전체다.",
            "- `fixed_cohort_eligible_all_fractions`은 모든 비율에서 Warm으로 처리 가능한 동일 test 행만 비교한다.",
            "",
            "## 결과",
            "",
            "### Seed별 결과",
            "",
            md_table(summary),
            "",
            "### Seed 평균",
            "",
            md_table(agg),
            "",
            "## 25% -> 100% fixed cohort 변화",
            "",
            "```json",
            json.dumps(deltas, ensure_ascii=False, indent=2),
            "```",
            "",
            "## 해석",
            "",
            "- fixed cohort에서 음수 delta는 학습 데이터 증가에 따른 성능 개선이다.",
            "- coverage 증가는 더 많은 test 작품이 Warm 경로로 처리 가능해졌다는 뜻이다.",
            "- 이 실험은 과거 train split을 줄였다가 늘리는 offline proxy이므로, 운영 데이터가 품질 검수 없이 들어와도 자동 개선된다는 뜻은 아니다.",
            "",
        ]
    )
    (EXP / "reports" / "result_report.md").write_text(report, encoding="utf-8")
    print(json.dumps({"deltas": deltas, "summary_rows": len(summary)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
