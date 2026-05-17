#!/usr/bin/env python3
"""Run Track 4 E029 artist-count routing threshold experiment.

Warm/Cold routing is normally based on whether an artist exists in the training
data. This experiment checks whether low-history Warm artists should instead be
routed to the Cold-style model.
"""
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
RESULT_PATH = RESULT_DIR / "t4_e029_routing_threshold_metrics.json"
PRED_PATH = PRED_DIR / "t4_e029_routing_threshold_predictions.csv"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"
THRESHOLDS = [1, 3, 5, 10, 20]

WARM_NUMERIC = ["log_area", "aspect_ratio", "artist_works_log", "artist_works_count_train"]
WARM_CATEGORICAL = ["medium_category", "support_category", "artist_key"]
COLD_NUMERIC = ["log_area", "aspect_ratio"]
COLD_CATEGORICAL = ["medium_category"]

FORBIDDEN_FEATURE_PATTERNS = [
    "source",
    "url",
    "image",
    "gallery",
    "tier",
    "price_krw",
    "ln_price",
]


def onehot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def validate_features(columns: list[str]) -> None:
    lower_cols = [col.lower() for col in columns]
    violations = [
        col
        for col, lower in zip(columns, lower_cols)
        if any(pattern in lower for pattern in FORBIDDEN_FEATURE_PATTERNS)
    ]
    if violations:
        raise ValueError(f"Forbidden features included: {violations}")


def build_preprocessor(numeric: list[str], categorical: list[str]) -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
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
    validate_features(features)
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
    validate_features(features)
    return (
        Pipeline(
            [
                ("preprocess", build_preprocessor(COLD_NUMERIC, COLD_CATEGORICAL)),
                ("model", QuantileRegressor(quantile=0.5, alpha=0.0001, solver="highs")),
            ]
        ),
        features,
    )


def price_from_log(values: np.ndarray) -> np.ndarray:
    return np.exp(values)


def metric_dict(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    y_log = df[TARGET_LOG].to_numpy(dtype=float)
    y_price = df[TARGET_PRICE].to_numpy(dtype=float)
    pred_price = np.maximum(price_from_log(pred_log), 1.0)
    ape = np.abs(pred_price - y_price) / y_price
    return {
        "rows": int(len(df)),
        "artists": int(df["artist_key"].nunique()),
        "median_ape": float(np.median(ape)) if len(ape) else None,
        "mape": float(np.mean(ape)) if len(ape) else None,
        "rmse_log": float(np.sqrt(mean_squared_error(y_log, pred_log))) if len(ape) else None,
        "within_30": float(np.mean(ape <= 0.30)) if len(ape) else None,
        "within_50": float(np.mean(ape <= 0.50)) if len(ape) else None,
        "p95_ape": float(np.quantile(ape, 0.95)) if len(ape) else None,
    }


def slice_metric(df: pd.DataFrame, pred_log: np.ndarray, mask: np.ndarray) -> dict[str, float]:
    if mask.sum() == 0:
        return {"rows": 0, "artists": 0, "median_ape": None, "p95_ape": None}
    return metric_dict(df.loc[mask], pred_log[mask])


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)

    train = pd.read_csv(SPLIT_DIR / "track4_train.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).copy()
    val_warm = pd.read_csv(SPLIT_DIR / "track4_val_warm.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).copy()
    val_cold = pd.read_csv(SPLIT_DIR / "track4_val_cold.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).copy()

    warm_model, warm_features = make_warm_model()
    cold_model, cold_features = make_cold_model()
    warm_model.fit(train[warm_features], train[TARGET_LOG])
    cold_model.fit(train[cold_features], train[TARGET_LOG])

    warm_pred = warm_model.predict(val_warm[warm_features])
    warm_as_cold_pred = cold_model.predict(val_warm[cold_features])
    cold_pred = cold_model.predict(val_cold[cold_features])

    results: dict[str, Any] = {
        "experiment_id": "T4-E029",
        "hypothesis_id": ["T4-H10", "T4-H19"],
        "date": date.today().isoformat(),
        "threshold_rule": "artist_works_count_train >= threshold 이면 Warm 모델, 미만이면 Cold 모델",
        "models": {
            "warm": {"model": "Ridge", "features": warm_features},
            "cold": {"model": "QuantileRegressor", "features": cold_features},
        },
        "base_metrics": {
            "val_warm_all_warm_model": metric_dict(val_warm, warm_pred),
            "val_warm_all_cold_model": metric_dict(val_warm, warm_as_cold_pred),
            "val_cold_cold_model": metric_dict(val_cold, cold_pred),
        },
        "thresholds": {},
    }
    pred_frames: list[pd.DataFrame] = []

    for threshold in THRESHOLDS:
        use_warm = val_warm["artist_works_count_train"].to_numpy() >= threshold
        routed_warm_pred = np.where(use_warm, warm_pred, warm_as_cold_pred)
        threshold_result = {
            "warm_routed": metric_dict(val_warm, routed_warm_pred),
            "warm_high_history": slice_metric(val_warm, routed_warm_pred, use_warm),
            "warm_low_history": slice_metric(val_warm, routed_warm_pred, ~use_warm),
            "warm_low_history_rows": int((~use_warm).sum()),
            "cold": metric_dict(val_cold, cold_pred),
        }
        results["thresholds"][str(threshold)] = threshold_result
        for split_name, df, pred_log in [
            ("val_warm", val_warm, routed_warm_pred),
            ("val_cold", val_cold, cold_pred),
        ]:
            pred_price = price_from_log(pred_log)
            ape = np.abs(pred_price - df[TARGET_PRICE].to_numpy(dtype=float)) / df[TARGET_PRICE].to_numpy(dtype=float)
            pred_frames.append(
                pd.DataFrame(
                    {
                        "experiment_id": "T4-E029",
                        "threshold": threshold,
                        "split": split_name,
                        "artist_key": df["artist_key"].to_numpy(),
                        "artist_works_count_train": df["artist_works_count_train"].to_numpy(),
                        "routed_to": np.where(
                            df["artist_works_count_train"].to_numpy() >= threshold,
                            "warm" if split_name == "val_warm" else "cold",
                            "cold",
                        ),
                        "actual_price_krw": df[TARGET_PRICE].to_numpy(dtype=float),
                        "pred_log_price": pred_log,
                        "pred_price_krw": pred_price,
                        "ape": ape,
                    }
                )
            )

    RESULT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.concat(pred_frames, ignore_index=True).to_csv(PRED_PATH, index=False)
    print(RESULT_PATH)
    print(PRED_PATH)


if __name__ == "__main__":
    main()
