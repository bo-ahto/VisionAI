#!/usr/bin/env python3
"""Evaluate blind predictions when labels are provided separately."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


def safe_exp(values: pd.Series | np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    return np.exp(np.clip(arr, math.log(1_000.0), math.log(1_000_000_000_000.0)))


def metric(frame: pd.DataFrame) -> dict[str, float | int]:
    actual = pd.to_numeric(frame["actual_price"], errors="coerce")
    actual_log = pd.to_numeric(frame["actual_log"], errors="coerce")
    pred_log = pd.to_numeric(frame["final_price_log"], errors="coerce")
    pred = safe_exp(pred_log)
    valid = actual.gt(0) & actual_log.notna() & pred_log.notna()
    ape = ((pd.Series(pred, index=frame.index) - actual).abs() / actual.clip(lower=1.0)).loc[valid]
    log_error = (actual_log - pred_log).loc[valid]
    return {
        "n": int(len(ape)),
        "MdAPE": float(ape.median()),
        "MAPE": float(ape.mean()),
        "p95_APE": float(ape.quantile(0.95)),
        "RMSE_log": float(np.sqrt(np.mean(np.square(log_error)))),
        "within_15": float((ape <= 0.15).mean()),
        "within_30": float((ape <= 0.30).mean()),
        "within_50": float((ape <= 0.50).mean()),
        "over_50pct_error_rate": float((ape > 0.50).mean()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--labels", required=True, help="CSV containing _track6_row_id or external_artwork_id plus actual_log, actual_price.")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    pred = pd.read_csv(args.predictions, low_memory=False)
    labels = pd.read_csv(args.labels, low_memory=False)
    join_key = "_track6_row_id" if "_track6_row_id" in pred.columns and "_track6_row_id" in labels.columns else "external_artwork_id"
    if join_key not in pred.columns or join_key not in labels.columns:
        raise ValueError("Predictions and labels must share _track6_row_id or external_artwork_id.")
    merged = pred.merge(labels[[join_key, "actual_log", "actual_price"]], on=join_key, how="inner")
    metrics = metric(merged)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([metrics]).to_csv(output_path, index=False)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
