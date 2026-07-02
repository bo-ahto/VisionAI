#!/usr/bin/env python3
"""KTCC submission runtime script for price prediction MAPE evaluation.

Run from the ktcc_runtime folder or from any path:

    python scripts/ktcc_price_mape_test.py

The script loads the frozen Warm high-confidence residual Huber model, predicts
100 high-confidence test rows, joins the provided labels, and prints/saves MAPE
metrics. No model training or parameter tuning is performed in this script.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


FEATURE_COLUMNS = [
    "quantile_width",
    "l10_price_range_ratio",
    "svc_group_n_log",
    "log_area",
    "component_prediction_spread",
    "current_vs_stable_gap_abs",
    "current_minus_stable_log",
    "ppv8_minus_stable_log",
    "svc_minus_stable_log",
    "l10_minus_stable_log",
]

COMPONENT_COLUMNS = [
    "hcoef_stable",
    "current_70_30",
    "ppv8_service_proxy",
    "svc_numeric_seed_mean",
    "l10_seq_pred_log",
]


def safe_exp(values: pd.Series | np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    return np.exp(np.clip(arr, math.log(1_000.0), math.log(1_000_000_000_000.0)))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def add_engineered_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    required = COMPONENT_COLUMNS + ["quantile_width", "l10_price_range_ratio", "svc_group_n", "log_area"]
    missing = [col for col in required if col not in out.columns]
    if missing:
        raise ValueError(f"필수 입력 컬럼이 없습니다: {missing}")

    for col in required:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    out["component_prediction_spread"] = out[COMPONENT_COLUMNS].std(axis=1)
    out["current_vs_stable_gap_abs"] = (out["current_70_30"] - out["hcoef_stable"]).abs()
    out["svc_group_n_log"] = np.log1p(out["svc_group_n"].fillna(0.0))
    out["current_minus_stable_log"] = out["current_70_30"] - out["hcoef_stable"]
    out["ppv8_minus_stable_log"] = out["ppv8_service_proxy"] - out["hcoef_stable"]
    out["svc_minus_stable_log"] = out["svc_numeric_seed_mean"] - out["hcoef_stable"]
    out["l10_minus_stable_log"] = out["l10_seq_pred_log"] - out["hcoef_stable"]
    out["stable_warm_price_log"] = out["hcoef_stable"]
    out["stable_warm_price"] = safe_exp(out["stable_warm_price_log"])
    return out


def predict(features: pd.DataFrame, model: Any, residual_cap: float) -> pd.DataFrame:
    out = add_engineered_features(features)
    adjustment = np.clip(model.predict(out[FEATURE_COLUMNS]), -residual_cap, residual_cap)
    out["residual_adjustment_log"] = adjustment
    out["final_price_log"] = out["stable_warm_price_log"] + adjustment
    out["final_price"] = safe_exp(out["final_price_log"])
    return out


def calculate_metrics(predictions: pd.DataFrame, labels: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    merged = predictions.merge(labels[["_track6_row_id", "actual_log", "actual_price"]], on="_track6_row_id", how="inner")
    if len(merged) != len(predictions):
        raise ValueError(f"예측 데이터 {len(predictions)}건 중 label 조인 결과가 {len(merged)}건입니다.")

    actual_price = pd.to_numeric(merged["actual_price"], errors="coerce")
    actual_log = pd.to_numeric(merged["actual_log"], errors="coerce")
    pred_log = pd.to_numeric(merged["final_price_log"], errors="coerce")
    pred_price = pd.Series(safe_exp(pred_log), index=merged.index)
    valid = actual_price.gt(0) & actual_log.notna() & pred_log.notna()

    merged["absolute_percentage_error"] = ((pred_price - actual_price).abs() / actual_price.clip(lower=1.0))
    log_error = actual_log.loc[valid] - pred_log.loc[valid]
    ape = merged.loc[valid, "absolute_percentage_error"]

    metrics = {
        "n": int(len(ape)),
        "MdAPE": float(ape.median()),
        "MAPE": float(ape.mean()),
        "p95_APE": float(ape.quantile(0.95)),
        "RMSE_log": float(np.sqrt(np.mean(np.square(log_error)))),
        "within_15": float((ape <= 0.15).mean()),
        "within_30": float((ape <= 0.30).mean()),
        "within_50": float((ape <= 0.50).mean()),
        "over_50pct_error_rate": float((ape > 0.50).mean()),
        "pass_mape_15pct": bool(float(ape.mean()) <= 0.15),
    }
    return merged, metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=None, help="ktcc_runtime folder path. Defaults to parent of this script.")
    parser.add_argument("--features", default="data/price_test_features_100.csv")
    parser.add_argument("--labels", default="data/price_test_labels_100.csv")
    parser.add_argument("--model-config", default="artifacts/model_config.json")
    parser.add_argument("--model", default="artifacts/warm_high_confidence_residual_huber.joblib")
    parser.add_argument("--output-dir", default="outputs")
    args = parser.parse_args()

    runtime_root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[1]
    output_dir = runtime_root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    model_config = load_json(runtime_root / args.model_config)
    residual_cap = float(model_config["residual_adjustment_cap_log"])
    model = joblib.load(runtime_root / args.model)

    features = pd.read_csv(runtime_root / args.features, low_memory=False)
    labels = pd.read_csv(runtime_root / args.labels, low_memory=False)
    predictions = predict(features, model, residual_cap)
    evaluated, metrics = calculate_metrics(predictions, labels)

    prediction_cols = [
        "_track6_row_id",
        "artist_key",
        "artist_name_ko",
        "stable_warm_price_log",
        "stable_warm_price",
        "residual_adjustment_log",
        "final_price_log",
        "final_price",
        "actual_log",
        "actual_price",
        "absolute_percentage_error",
    ]
    prediction_cols = [col for col in prediction_cols if col in evaluated.columns]
    evaluated[prediction_cols].to_csv(output_dir / "ktcc_price_predictions_100.csv", index=False)
    pd.DataFrame([metrics]).to_csv(output_dir / "ktcc_price_mape_metrics.csv", index=False)
    (output_dir / "ktcc_price_mape_metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("KTCC 가격예측 MAPE 시험 결과")
    print(f"- 평가 건수: {metrics['n']}")
    print(f"- MdAPE: {metrics['MdAPE']:.4f}")
    print(f"- MAPE: {metrics['MAPE']:.4f} ({metrics['MAPE'] * 100:.2f}%)")
    print(f"- p95_APE: {metrics['p95_APE']:.4f}")
    print(f"- RMSE_log: {metrics['RMSE_log']:.4f}")
    print(f"- 15% 이하 목표 통과 여부: {'PASS' if metrics['pass_mape_15pct'] else 'FAIL'}")
    print(f"- 결과 CSV: {output_dir / 'ktcc_price_mape_metrics.csv'}")


if __name__ == "__main__":
    main()
