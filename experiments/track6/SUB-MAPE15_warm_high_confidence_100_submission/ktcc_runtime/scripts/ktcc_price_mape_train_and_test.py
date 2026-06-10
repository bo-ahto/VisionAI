#!/usr/bin/env python3
"""Retrain and evaluate the KTCC price MAPE submission from packaged CSV files.

This script is stricter than ktcc_price_mape_test.py:

- train data: data/price_train_reference_110.csv
- test features: data/price_test_features_100.csv
- test labels: data/price_test_labels_100.csv

It does not read upstream experiment folders and does not use the frozen joblib
model. The model is fitted from the packaged train CSV, then evaluated on the
packaged 100-row test CSV.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.model_selection import KFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


SEED = 20260608
BASE_CANDIDATE = "hcoef_stable"
CANDIDATE_RESIDUAL_CAPS = [0.0, 0.01, 0.02, 0.03, 0.05, 0.08]

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


def add_engineered_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    required = COMPONENT_COLUMNS + ["quantile_width", "l10_price_range_ratio", "svc_group_n", "log_area"]
    missing = [col for col in required if col not in out.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    for col in required:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    out["component_prediction_spread"] = out[COMPONENT_COLUMNS].std(axis=1)
    out["current_vs_stable_gap_abs"] = (out["current_70_30"] - out[BASE_CANDIDATE]).abs()
    out["svc_group_n_log"] = np.log1p(out["svc_group_n"].fillna(0.0))
    out["current_minus_stable_log"] = out["current_70_30"] - out[BASE_CANDIDATE]
    out["ppv8_minus_stable_log"] = out["ppv8_service_proxy"] - out[BASE_CANDIDATE]
    out["svc_minus_stable_log"] = out["svc_numeric_seed_mean"] - out[BASE_CANDIDATE]
    out["l10_minus_stable_log"] = out["l10_seq_pred_log"] - out[BASE_CANDIDATE]
    out["stable_warm_price_log"] = out[BASE_CANDIDATE]
    out["stable_warm_price"] = safe_exp(out["stable_warm_price_log"])
    return out


def make_model() -> Any:
    return make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        HuberRegressor(alpha=0.001, epsilon=1.35, max_iter=1000),
    )


def metric(actual_price: pd.Series | np.ndarray, actual_log: pd.Series | np.ndarray, pred_log: pd.Series | np.ndarray) -> dict[str, Any]:
    actual_price_arr = np.asarray(actual_price, dtype=float)
    actual_log_arr = np.asarray(actual_log, dtype=float)
    pred_log_arr = np.asarray(pred_log, dtype=float)
    pred_price = safe_exp(pred_log_arr)
    valid = np.isfinite(actual_price_arr) & (actual_price_arr > 0) & np.isfinite(actual_log_arr) & np.isfinite(pred_log_arr)
    ape = np.abs(pred_price[valid] - actual_price_arr[valid]) / np.clip(actual_price_arr[valid], 1.0, None)
    log_error = actual_log_arr[valid] - pred_log_arr[valid]
    return {
        "n": int(valid.sum()),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.mean(np.square(log_error)))),
        "within_15": float(np.mean(ape <= 0.15)),
        "within_30": float(np.mean(ape <= 0.30)),
        "within_50": float(np.mean(ape <= 0.50)),
        "over_50pct_error_rate": float(np.mean(ape > 0.50)),
        "pass_mape_15pct": bool(float(np.mean(ape)) <= 0.15),
    }


def select_cap_with_oof(train: pd.DataFrame) -> tuple[float, list[dict[str, Any]]]:
    x_train = train[FEATURE_COLUMNS]
    residual_target = train["actual_log"].astype(float) - train[BASE_CANDIDATE].astype(float)
    kfold = KFold(n_splits=5, shuffle=True, random_state=SEED)

    cap_rows: list[dict[str, Any]] = []
    best_cap = 0.0
    best_metrics = metric(train["actual_price"], train["actual_log"], train[BASE_CANDIDATE])

    for cap in CANDIDATE_RESIDUAL_CAPS:
        if cap == 0.0:
            adjustment = pd.Series(0.0, index=train.index, dtype=float)
        else:
            adjustment = pd.Series(np.nan, index=train.index, dtype=float)
            for train_idx, valid_idx in kfold.split(x_train):
                fold_model = make_model()
                fold_model.fit(x_train.iloc[train_idx], residual_target.iloc[train_idx])
                fold_raw = fold_model.predict(x_train.iloc[valid_idx])
                adjustment.iloc[valid_idx] = np.clip(fold_raw, -cap, cap)

        oof_pred_log = train[BASE_CANDIDATE].astype(float) + adjustment
        oof_metrics = metric(train["actual_price"], train["actual_log"], oof_pred_log)
        cap_rows.append({"cap": cap, **oof_metrics})
        if (oof_metrics["MAPE"], oof_metrics["p95_APE"]) < (best_metrics["MAPE"], best_metrics["p95_APE"]):
            best_cap = cap
            best_metrics = oof_metrics

    return best_cap, cap_rows


def fit_and_predict(train: pd.DataFrame, test_features: pd.DataFrame, residual_cap: float) -> pd.DataFrame:
    model = make_model()
    x_train = train[FEATURE_COLUMNS]
    residual_target = train["actual_log"].astype(float) - train[BASE_CANDIDATE].astype(float)
    model.fit(x_train, residual_target)

    out = test_features.copy()
    raw_adjustment = model.predict(out[FEATURE_COLUMNS])
    out["residual_adjustment_log"] = np.clip(raw_adjustment, -residual_cap, residual_cap)
    out["final_price_log"] = out[BASE_CANDIDATE].astype(float) + out["residual_adjustment_log"]
    out["final_price"] = safe_exp(out["final_price_log"])
    return out


def calculate_metrics(predictions: pd.DataFrame, labels: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    merged = predictions.merge(labels[["_track6_row_id", "actual_log", "actual_price"]], on="_track6_row_id", how="inner")
    if len(merged) != len(predictions):
        raise ValueError(f"Predictions {len(predictions)} rows, labels joined {len(merged)} rows.")

    pred_price = pd.Series(safe_exp(merged["final_price_log"]), index=merged.index)
    actual_price = pd.to_numeric(merged["actual_price"], errors="coerce")
    merged["absolute_percentage_error"] = (pred_price - actual_price).abs() / actual_price.clip(lower=1.0)
    metrics = metric(merged["actual_price"], merged["actual_log"], merged["final_price_log"])
    return merged, metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=None, help="ktcc_runtime folder path. Defaults to parent of this script.")
    parser.add_argument("--train", default="data/price_train_reference_110.csv")
    parser.add_argument("--features", default="data/price_test_features_100.csv")
    parser.add_argument("--labels", default="data/price_test_labels_100.csv")
    parser.add_argument("--output-dir", default="outputs")
    args = parser.parse_args()

    runtime_root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[1]
    output_dir = runtime_root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    train = add_engineered_features(pd.read_csv(runtime_root / args.train, low_memory=False))
    test_features = add_engineered_features(pd.read_csv(runtime_root / args.features, low_memory=False))
    labels = pd.read_csv(runtime_root / args.labels, low_memory=False)

    residual_cap, cap_search = select_cap_with_oof(train)
    predictions = fit_and_predict(train, test_features, residual_cap)
    evaluated, metrics = calculate_metrics(predictions, labels)

    payload = {
        "train_rows": int(len(train)),
        "test_rows": int(len(test_features)),
        "selected_residual_adjustment_cap_log": float(residual_cap),
        "cap_search_metrics": cap_search,
        "test_metrics": metrics,
    }

    evaluated.to_csv(output_dir / "ktcc_retrained_price_predictions_100.csv", index=False)
    pd.DataFrame([metrics]).to_csv(output_dir / "ktcc_retrained_price_mape_metrics.csv", index=False)
    (output_dir / "ktcc_retrained_price_mape_metrics.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("KTCC 가격예측 MAPE 재학습 시험 결과")
    print(f"- 학습 건수: {len(train)}")
    print(f"- 평가 건수: {metrics['n']}")
    print(f"- 선택 보정 cap(log): {residual_cap:.3f}")
    print(f"- MdAPE: {metrics['MdAPE']:.4f}")
    print(f"- MAPE: {metrics['MAPE']:.4f} ({metrics['MAPE'] * 100:.2f}%)")
    print(f"- p95_APE: {metrics['p95_APE']:.4f}")
    print(f"- 15% 이하 목표 통과 여부: {'PASS' if metrics['pass_mape_15pct'] else 'FAIL'}")
    print(f"- 결과 JSON: {output_dir / 'ktcc_retrained_price_mape_metrics.json'}")


if __name__ == "__main__":
    main()
