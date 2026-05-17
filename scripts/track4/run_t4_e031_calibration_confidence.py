#!/usr/bin/env python3
"""Run Track 4 E031 price range calibration and confidence policy."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import QuantileRegressor, Ridge
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO = Path(__file__).resolve().parents[2]
SPLIT_DIR = REPO / "data" / "track4_split"
RESULT_DIR = REPO / "data" / "track4" / "results"
PRED_DIR = REPO / "data" / "track4" / "predictions"
RESULT_PATH = RESULT_DIR / "t4_e031_calibration_confidence_metrics.json"
PRED_PATH = PRED_DIR / "t4_e031_calibration_confidence_predictions.csv"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"
TARGET_COVERAGE = 0.80
MIN_GROUP_ROWS = 30

WARM_NUMERIC = ["log_area", "aspect_ratio", "artist_works_log", "artist_works_count_train"]
WARM_CATEGORICAL = ["medium_category", "support_category", "artist_key"]
COLD_NUMERIC = ["log_area", "aspect_ratio"]
COLD_CATEGORICAL = ["medium_category"]


def onehot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def build_preprocessor(numeric: list[str], categorical: list[str]) -> ColumnTransformer:
    return ColumnTransformer(
        [
            (
                "numeric",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric,
            ),
            (
                "categorical",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="constant", fill_value="unknown")),
                        ("onehot", onehot_encoder()),
                    ]
                ),
                categorical,
            ),
        ],
        remainder="drop",
    )


def make_warm_model() -> tuple[Pipeline, list[str]]:
    features = WARM_CATEGORICAL + WARM_NUMERIC
    return (
        Pipeline(
            [
                ("preprocess", build_preprocessor(WARM_NUMERIC, WARM_CATEGORICAL)),
                ("model", Ridge(alpha=10.0, random_state=42)),
            ]
        ),
        features,
    )


def make_cold_model() -> tuple[Pipeline, list[str]]:
    features = COLD_CATEGORICAL + COLD_NUMERIC
    return (
        Pipeline(
            [
                ("preprocess", build_preprocessor(COLD_NUMERIC, COLD_CATEGORICAL)),
                ("model", QuantileRegressor(quantile=0.5, alpha=0.0001, solver="highs")),
            ]
        ),
        features,
    )


def add_groups(train: pd.DataFrame, df: pd.DataFrame, split_type: str) -> pd.DataFrame:
    out = df.copy()
    if split_type == "warm":
        count = out["artist_works_count_train"].fillna(0)
        out["confidence_group"] = np.select(
            [count < 5, count < 20],
            ["low_history", "mid_history"],
            default="high_history",
        )
    else:
        area_q90 = train["log_area"].quantile(0.90)
        risk_3d = out["is_3d_candidate"].fillna(0).astype(int)
        risk_support_unknown = (out["support_category"].fillna("unknown") == "unknown").astype(int)
        risk_large_area = (out["log_area"] >= area_q90).astype(int)
        risk_high_price = out["is_high_price_candidate"].fillna(0).astype(int)
        risk_extreme_aspect = out["is_extreme_aspect_ratio"].fillna(0).astype(int)
        out["risk_score"] = risk_3d + risk_support_unknown + risk_large_area + risk_high_price + risk_extreme_aspect
        out["confidence_group"] = np.where(out["risk_score"] == 0, "low", np.where(out["risk_score"] == 1, "medium", "high"))
    return out


def price_from_log(values: np.ndarray) -> np.ndarray:
    return np.exp(values)


def point_metrics(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    y_log = df[TARGET_LOG].to_numpy(dtype=float)
    y_price = df[TARGET_PRICE].to_numpy(dtype=float)
    pred_price = np.maximum(price_from_log(pred_log), 1.0)
    ape = np.abs(pred_price - y_price) / y_price
    return {
        "rows": int(len(df)),
        "median_ape": float(np.median(ape)),
        "mape": float(np.mean(ape)),
        "rmse_log": float(np.sqrt(mean_squared_error(y_log, pred_log))),
        "within_30": float(np.mean(ape <= 0.30)),
        "within_50": float(np.mean(ape <= 0.50)),
        "p95_ape": float(np.quantile(ape, 0.95)),
    }


def learn_calibration(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, Any]:
    residual = np.abs(df[TARGET_LOG].to_numpy(dtype=float) - pred_log)
    overall_q = float(np.quantile(residual, TARGET_COVERAGE))
    groups: dict[str, dict[str, Any]] = {}
    for group in sorted(df["confidence_group"].unique()):
        mask = df["confidence_group"].to_numpy() == group
        use_group = int(mask.sum()) >= MIN_GROUP_ROWS
        q = float(np.quantile(residual[mask], TARGET_COVERAGE)) if use_group else overall_q
        groups[group] = {
            "rows": int(mask.sum()),
            "abs_log_error_q80": q,
            "half_width_multiplier": float(np.exp(q)),
            "full_range_multiplier": float(np.exp(2 * q)),
            "fallback_to_overall": not use_group,
        }
    return {
        "overall": {
            "rows": int(len(df)),
            "abs_log_error_q80": overall_q,
            "half_width_multiplier": float(np.exp(overall_q)),
            "full_range_multiplier": float(np.exp(2 * overall_q)),
        },
        "groups": groups,
    }


def apply_calibration(df: pd.DataFrame, pred_log: np.ndarray, calibration: dict[str, Any]) -> tuple[dict[str, Any], pd.DataFrame]:
    actual_log = df[TARGET_LOG].to_numpy(dtype=float)
    residual = np.abs(actual_log - pred_log)
    q_values = []
    for group in df["confidence_group"]:
        group_info = calibration["groups"].get(group, calibration["overall"])
        q_values.append(group_info["abs_log_error_q80"])
    q_arr = np.array(q_values, dtype=float)
    covered = residual <= q_arr
    pred_price = np.maximum(price_from_log(pred_log), 1.0)
    lower = np.maximum(price_from_log(pred_log - q_arr), 1.0)
    upper = price_from_log(pred_log + q_arr)
    out = df[["artist_key", "artist_name_ko", "confidence_group", TARGET_PRICE]].copy()
    out["pred_log_price"] = pred_log
    out["pred_price_krw"] = pred_price
    out["range_lower_krw"] = lower
    out["range_upper_krw"] = upper
    out["abs_log_error"] = residual
    out["calibrated_abs_log_q80"] = q_arr
    out["covered"] = covered
    out["range_full_multiplier"] = upper / lower
    summary = {
        "overall": {
            "rows": int(len(df)),
            "coverage": float(covered.mean()),
            "avg_full_range_multiplier": float(np.mean(upper / lower)),
            "median_full_range_multiplier": float(np.median(upper / lower)),
        },
        "groups": {},
    }
    for group in sorted(df["confidence_group"].unique()):
        mask = df["confidence_group"].to_numpy() == group
        summary["groups"][group] = {
            "rows": int(mask.sum()),
            "coverage": float(covered[mask].mean()),
            "avg_full_range_multiplier": float(np.mean((upper / lower)[mask])),
            "median_full_range_multiplier": float(np.median((upper / lower)[mask])),
        }
    return summary, out


def fit_predict(train: pd.DataFrame, df: pd.DataFrame, split_type: str) -> np.ndarray:
    if split_type == "warm":
        model, features = make_warm_model()
    else:
        model, features = make_cold_model()
    model.fit(train[features], train[TARGET_LOG])
    return model.predict(df[features])


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    train = pd.read_csv(SPLIT_DIR / "track4_train.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).copy()
    val_warm = add_groups(train, pd.read_csv(SPLIT_DIR / "track4_val_warm.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]), "warm")
    test_warm = add_groups(train, pd.read_csv(SPLIT_DIR / "track4_test_warm.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]), "warm")
    val_cold = add_groups(train, pd.read_csv(SPLIT_DIR / "track4_val_cold.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]), "cold")
    test_cold = add_groups(train, pd.read_csv(SPLIT_DIR / "track4_test_cold.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]), "cold")

    val_warm_pred = fit_predict(train, val_warm, "warm")
    test_warm_pred = fit_predict(train, test_warm, "warm")
    val_cold_pred = fit_predict(train, val_cold, "cold")
    test_cold_pred = fit_predict(train, test_cold, "cold")

    warm_calibration = learn_calibration(val_warm, val_warm_pred)
    cold_calibration = learn_calibration(val_cold, val_cold_pred)
    warm_test_summary, warm_pred_frame = apply_calibration(test_warm, test_warm_pred, warm_calibration)
    cold_test_summary, cold_pred_frame = apply_calibration(test_cold, test_cold_pred, cold_calibration)

    results = {
        "experiment_id": "T4-E031",
        "hypothesis_id": ["T4-H18", "T4-H29"],
        "date": date.today().isoformat(),
        "target_coverage": TARGET_COVERAGE,
        "min_group_rows": MIN_GROUP_ROWS,
        "point_metrics": {
            "val_warm": point_metrics(val_warm, val_warm_pred),
            "test_warm": point_metrics(test_warm, test_warm_pred),
            "val_cold": point_metrics(val_cold, val_cold_pred),
            "test_cold": point_metrics(test_cold, test_cold_pred),
        },
        "calibration": {
            "warm_from_val": warm_calibration,
            "cold_from_val": cold_calibration,
        },
        "test_interval_summary": {
            "warm": warm_test_summary,
            "cold": cold_test_summary,
        },
    }
    RESULT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    warm_pred_frame["experiment_id"] = "T4-E031"
    warm_pred_frame["split"] = "test_warm"
    cold_pred_frame["experiment_id"] = "T4-E031"
    cold_pred_frame["split"] = "test_cold"
    pd.concat([warm_pred_frame, cold_pred_frame], ignore_index=True).to_csv(PRED_PATH, index=False)
    print(RESULT_PATH)
    print(PRED_PATH)


if __name__ == "__main__":
    main()
