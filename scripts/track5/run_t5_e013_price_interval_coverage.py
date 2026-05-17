#!/usr/bin/env python3
"""Evaluate Track 5 price interval coverage using validation residual widths."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RESULT_DIR = REPO / "data" / "track5" / "results"
PRED_DIR = REPO / "data" / "track5" / "predictions"
RESULT_PATH = RESULT_DIR / "t5_e013_price_interval_coverage_metrics.json"


def interval_metrics(df: pd.DataFrame, log_width: float) -> dict[str, Any]:
    actual = df["actual_price_krw"].to_numpy(dtype=float)
    pred_log = df["pred_log_price"].to_numpy(dtype=float)
    lower = np.exp(pred_log - log_width)
    upper = np.exp(pred_log + log_width)
    covered = (actual >= lower) & (actual <= upper)
    width_ratio = upper / lower
    return {
        "rows": int(len(df)),
        "log_width": float(log_width),
        "price_multiplier": float(np.exp(log_width)),
        "full_width_ratio_upper_over_lower": float(np.median(width_ratio)),
        "coverage": float(np.mean(covered)),
        "median_ape": float(np.median(df["ape"].to_numpy(dtype=float))),
        "p95_ape": float(np.quantile(df["ape"].to_numpy(dtype=float), 0.95)),
    }


def calibration_widths(val: pd.DataFrame) -> dict[str, float]:
    actual_log = np.log(val["actual_price_krw"].to_numpy(dtype=float))
    pred_log = val["pred_log_price"].to_numpy(dtype=float)
    abs_log_error = np.abs(pred_log - actual_log)
    return {
        "p50": float(np.quantile(abs_log_error, 0.50)),
        "p80": float(np.quantile(abs_log_error, 0.80)),
        "p90": float(np.quantile(abs_log_error, 0.90)),
    }


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    val_pred = pd.read_csv(PRED_DIR / "t5_e008_candidate_model_comparison_predictions.csv")
    test_pred = pd.read_csv(PRED_DIR / "t5_e010_final_candidate_test_predictions.csv")

    pairs = {
        "warm_full_size_huber": {
            "val": val_pred[
                (val_pred["task"] == "warm")
                & (val_pred["feature_set"] == "warm_full_size")
                & (val_pred["model"] == "huber")
            ].copy(),
            "test": test_pred[(test_pred["task"] == "warm") & (test_pred["candidate"] == "warm_full_size_huber")].copy(),
        },
        "cold_full_size_quantile": {
            "val": val_pred[
                (val_pred["task"] == "cold")
                & (val_pred["feature_set"] == "cold_full_size")
                & (val_pred["model"] == "quantile_median")
            ].copy(),
            "test": test_pred[(test_pred["task"] == "cold") & (test_pred["candidate"] == "cold_full_size_quantile")].copy(),
        },
    }
    output: dict[str, Any] = {
        "experiment_id": "T5-E013",
        "hypothesis_id": "T5-H16",
        "date": date.today().isoformat(),
        "results": {},
    }
    for name, data in pairs.items():
        widths = calibration_widths(data["val"])
        output["results"][name] = {
            "validation_widths": widths,
            "test_coverage": {level: interval_metrics(data["test"], width) for level, width in widths.items()},
        }
    RESULT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(RESULT_PATH)
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
