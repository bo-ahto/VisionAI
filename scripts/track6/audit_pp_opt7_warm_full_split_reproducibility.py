#!/usr/bin/env python3
"""Audit PP-OPT7 Warm final metrics against the full base Warm splits.

This checks the non-submission setting:

- base validation split: data/.../track6_val_warm.csv, 519 rows
- base fixed test split: data/.../track6_test_warm.csv, 607 rows

The script verifies that PP-OPT7 final predictions cover the same row ids as
the base splits and recomputes MdAPE/MAPE/p95 from the prediction table.
"""
from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
SPLIT_ROOT = REPO / "data" / "track6_split_with_year_type_edition_size_artist_name"
EXP_DIR = REPO / "experiments" / "track6" / "PP-OPT7_warm_final_operational_freeze"
FINAL_PREDICTIONS = EXP_DIR / "outputs" / "final_candidate_predictions.csv"
FINAL_REPORTED_METRICS = EXP_DIR / "outputs" / "final_candidate_metrics.csv"
OUT_DIR = EXP_DIR / "reproduction"

BASELINE_MODEL_ID = "baseline_hcoef_stable"


def safe_exp(values: pd.Series | np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    return np.exp(np.clip(arr, math.log(1_000.0), math.log(1_000_000_000_000.0)))


def metrics_for(group: pd.DataFrame) -> dict[str, Any]:
    actual_price = pd.to_numeric(group["actual_price"], errors="coerce")
    actual_log = pd.to_numeric(group["actual_log"], errors="coerce")
    pred_log = pd.to_numeric(group["pred_log"], errors="coerce")
    valid = actual_price.gt(0) & actual_log.notna() & pred_log.notna()
    ape = (safe_exp(pred_log.loc[valid]) - actual_price.loc[valid].to_numpy(dtype=float))
    ape = np.abs(ape) / np.clip(actual_price.loc[valid].to_numpy(dtype=float), 1.0, None)
    log_error = actual_log.loc[valid].to_numpy(dtype=float) - pred_log.loc[valid].to_numpy(dtype=float)
    return {
        "n": int(valid.sum()),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.mean(np.square(log_error)))),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
    }


def read_split_ids() -> dict[str, set[str]]:
    mapping = {
        "validation_oof": SPLIT_ROOT / "track6_val_warm.csv",
        "test": SPLIT_ROOT / "track6_test_warm.csv",
    }
    out: dict[str, set[str]] = {}
    for split, path in mapping.items():
        frame = pd.read_csv(path, usecols=["_track6_row_id"], low_memory=False)
        out[split] = set(frame["_track6_row_id"].astype(str))
    return out


def recompute_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (model_id, eval_split), group in predictions.groupby(["model_id", "eval_split"], sort=True):
        row = {
            "model_id": model_id,
            "candidate": str(group["candidate"].iloc[0]),
            "family": str(group["family"].iloc[0]),
            "eval_split": eval_split,
        }
        row.update(metrics_for(group))
        rows.append(row)
    metrics = pd.DataFrame(rows)
    base = metrics[metrics["model_id"].eq(BASELINE_MODEL_ID)][
        ["eval_split", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]
    ].rename(
        columns={
            "MdAPE": "base_MdAPE",
            "MAPE": "base_MAPE",
            "p95_APE": "base_p95_APE",
            "RMSE_log": "base_RMSE_log",
        }
    )
    metrics = metrics.merge(base, on="eval_split", how="left")
    for col in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
        metrics[f"delta_{col}"] = metrics[col] - metrics[f"base_{col}"]
    return metrics.sort_values(["eval_split", "model_id"]).reset_index(drop=True)


def row_coverage_audit(predictions: pd.DataFrame, split_ids: dict[str, set[str]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (model_id, eval_split), group in predictions.groupby(["model_id", "eval_split"], sort=True):
        expected = split_ids[eval_split]
        actual = set(group["_track6_row_id"].astype(str))
        rows.append(
            {
                "model_id": model_id,
                "eval_split": eval_split,
                "expected_rows": len(expected),
                "prediction_rows": int(len(group)),
                "unique_prediction_row_ids": len(actual),
                "missing_from_predictions": len(expected - actual),
                "extra_in_predictions": len(actual - expected),
                "row_id_set_match": actual == expected,
            }
        )
    return pd.DataFrame(rows).sort_values(["eval_split", "model_id"]).reset_index(drop=True)


def compare_to_reported(recomputed: pd.DataFrame) -> pd.DataFrame:
    reported = pd.read_csv(FINAL_REPORTED_METRICS)
    keep = [
        "model_id",
        "eval_split",
        "n",
        "MdAPE",
        "MAPE",
        "p95_APE",
        "RMSE_log",
        "delta_MdAPE",
        "delta_MAPE",
        "delta_p95_APE",
    ]
    reported = reported[keep].rename(columns={col: f"reported_{col}" for col in keep if col not in {"model_id", "eval_split"}})
    merged = recomputed.merge(reported, on=["model_id", "eval_split"], how="left")
    for col in ["n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_MdAPE", "delta_MAPE", "delta_p95_APE"]:
        if col == "n":
            merged[f"diff_{col}"] = merged[col] - merged[f"reported_{col}"]
        else:
            merged[f"diff_{col}"] = merged[col] - merged[f"reported_{col}"]
    return merged


def markdown_table(frame: pd.DataFrame) -> str:
    view = frame.copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda value: "" if pd.isna(value) else f"{value:.12f}")
        else:
            view[col] = view[col].map(lambda value: "" if pd.isna(value) else str(value))
    lines = [
        "| " + " | ".join(view.columns) + " |",
        "| " + " | ".join("---" for _ in view.columns) + " |",
    ]
    lines.extend("| " + " | ".join(map(str, row)) + " |" for row in view.itertuples(index=False, name=None))
    return "\n".join(lines)


def write_report(metrics: pd.DataFrame, coverage: pd.DataFrame, comparison: pd.DataFrame) -> None:
    final_rows = metrics[metrics["model_id"].eq("warm_catboost_artist_qcap_risk_strict_v1")].copy()
    report = f"""# PP-OPT7 Warm Full Split Reproducibility Audit

- created_at: {datetime.now().isoformat(timespec="seconds")}
- validation split: `data/track6_split_with_year_type_edition_size_artist_name/track6_val_warm.csv`
- fixed test split: `data/track6_split_with_year_type_edition_size_artist_name/track6_test_warm.csv`
- prediction table: `{FINAL_PREDICTIONS.relative_to(REPO)}`
- reported metrics: `{FINAL_REPORTED_METRICS.relative_to(REPO)}`

## Scope

This audit is not the high-confidence 100-row submission benchmark.
It checks the full base Warm validation/test split.

The current PP-OPT7 prediction table is an upstream-frozen feature/prediction
table. It can reproduce the full-split metrics exactly, but the raw
`track6_train.csv` alone is not enough to retrain the whole PP-SVC3/HCOEF/L10/
CatBoost/artist-correction chain from scratch without running the upstream
experiment scripts and their artifacts.

## Final Candidate Full Split Metrics

{markdown_table(final_rows[['model_id', 'eval_split', 'n', 'MdAPE', 'MAPE', 'p95_APE', 'RMSE_log', 'Within_30', 'Within_50', 'delta_MdAPE', 'delta_MAPE', 'delta_p95_APE']])}

## Row Coverage Audit

{markdown_table(coverage)}

## All Recomputed Metrics

{markdown_table(metrics[['model_id', 'eval_split', 'n', 'MdAPE', 'MAPE', 'p95_APE', 'RMSE_log', 'Within_30', 'Within_50', 'delta_MdAPE', 'delta_MAPE', 'delta_p95_APE']])}

## Difference From Reported Metrics

{markdown_table(comparison[['model_id', 'eval_split', 'diff_n', 'diff_MdAPE', 'diff_MAPE', 'diff_p95_APE', 'diff_RMSE_log', 'diff_delta_MdAPE', 'diff_delta_MAPE', 'diff_delta_p95_APE']])}
"""
    (OUT_DIR / "full_split_reproducibility_report.md").write_text(report, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    split_ids = read_split_ids()
    predictions = pd.read_csv(FINAL_PREDICTIONS, low_memory=False)
    metrics = recompute_metrics(predictions)
    coverage = row_coverage_audit(predictions, split_ids)
    comparison = compare_to_reported(metrics)

    metrics.to_csv(OUT_DIR / "full_split_recomputed_metrics.csv", index=False)
    coverage.to_csv(OUT_DIR / "full_split_row_coverage_audit.csv", index=False)
    comparison.to_csv(OUT_DIR / "full_split_reported_metric_comparison.csv", index=False)
    audit = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "split_root": str(SPLIT_ROOT.relative_to(REPO)),
        "prediction_table": str(FINAL_PREDICTIONS.relative_to(REPO)),
        "reported_metric_table": str(FINAL_REPORTED_METRICS.relative_to(REPO)),
        "row_coverage_pass": bool(coverage["row_id_set_match"].all()),
        "max_abs_metric_diff_vs_reported": float(
            comparison[
                [
                    "diff_MdAPE",
                    "diff_MAPE",
                    "diff_p95_APE",
                    "diff_RMSE_log",
                    "diff_delta_MdAPE",
                    "diff_delta_MAPE",
                    "diff_delta_p95_APE",
                ]
            ]
            .abs()
            .max()
            .max()
        ),
        "final_candidate_metrics": metrics[
            metrics["model_id"].eq("warm_catboost_artist_qcap_risk_strict_v1")
        ].to_dict(orient="records"),
        "reproducibility_level": (
            "full split metrics are reproducible from the base split row ids and PP-OPT7 frozen prediction table; "
            "raw train/test-only end-to-end retraining requires upstream component-chain artifactization"
        ),
    }
    (OUT_DIR / "full_split_reproducibility_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_report(metrics, coverage, comparison)
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
