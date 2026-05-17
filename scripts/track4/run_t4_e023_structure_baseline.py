#!/usr/bin/env python3
"""Run Track 4 E023 structure-only Warm/Cold baseline.

This experiment intentionally excludes artist, source, gallery, URL, and price-derived
post-outcome features. It tests whether artwork structure alone can beat a simple
median-price baseline on fixed Track 4 Warm/Cold validation splits.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO = Path(__file__).resolve().parents[2]
SPLIT_DIR = REPO / "data" / "track4_split"
RESULT_DIR = REPO / "data" / "track4" / "results"
PRED_DIR = REPO / "data" / "track4" / "predictions"
RESULT_PATH = RESULT_DIR / "t4_e023_structure_baseline_metrics.json"
PRED_PATH = PRED_DIR / "t4_e023_structure_baseline_predictions.csv"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"

NUMERIC_FEATURES = [
    "log_area",
    "aspect_ratio",
    "has_depth",
    "is_3d_candidate",
]
CATEGORICAL_FEATURES = [
    "medium_category",
    "support_category",
]
FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES
FORBIDDEN_FEATURE_PATTERNS = [
    "artist",
    "source",
    "url",
    "image",
    "gallery",
    "tier",
    "price_krw",
    "ln_price",
]


@dataclass(frozen=True)
class SplitData:
    train: pd.DataFrame
    val_warm: pd.DataFrame
    val_cold: pd.DataFrame


def load_data() -> SplitData:
    return SplitData(
        train=pd.read_csv(SPLIT_DIR / "track4_train.csv"),
        val_warm=pd.read_csv(SPLIT_DIR / "track4_val_warm.csv"),
        val_cold=pd.read_csv(SPLIT_DIR / "track4_val_cold.csv"),
    )


def validate_features(columns: list[str]) -> None:
    lower_cols = [col.lower() for col in columns]
    violations = [
        col
        for col, lower in zip(columns, lower_cols)
        if any(pattern in lower for pattern in FORBIDDEN_FEATURE_PATTERNS)
    ]
    if violations:
        raise ValueError(f"Forbidden features included: {violations}")


def onehot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def build_preprocessor() -> ColumnTransformer:
    numeric = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="unknown")),
            ("onehot", onehot_encoder()),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("numeric", numeric, NUMERIC_FEATURES),
            ("categorical", categorical, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )


def build_models() -> dict[str, Pipeline]:
    preprocessor = build_preprocessor()
    return {
        "dummy_median": Pipeline(
            steps=[
                ("preprocess", preprocessor),
                ("model", DummyRegressor(strategy="median")),
            ]
        ),
        "ridge": Pipeline(
            steps=[
                ("preprocess", build_preprocessor()),
                ("model", Ridge(alpha=10.0, random_state=42)),
            ]
        ),
        "huber": Pipeline(
            steps=[
                ("preprocess", build_preprocessor()),
                ("model", HuberRegressor(alpha=0.0001, epsilon=1.35, max_iter=500)),
            ]
        ),
    }


def price_from_log(values: np.ndarray) -> np.ndarray:
    return np.exp(values)


def metric_dict(y_log: np.ndarray, pred_log: np.ndarray, y_price: np.ndarray) -> dict[str, float]:
    pred_price = price_from_log(pred_log)
    pred_price = np.maximum(pred_price, 1.0)
    ape = np.abs(pred_price - y_price) / y_price
    return {
        "median_ape": float(np.median(ape)),
        "mape": float(np.mean(ape)),
        "rmse_log": float(np.sqrt(mean_squared_error(y_log, pred_log))),
        "within_30": float(np.mean(ape <= 0.30)),
        "within_50": float(np.mean(ape <= 0.50)),
        "p90_ape": float(np.quantile(ape, 0.90)),
        "p95_ape": float(np.quantile(ape, 0.95)),
    }


def evaluate_model(model: Pipeline, train: pd.DataFrame, eval_df: pd.DataFrame) -> tuple[dict[str, float], np.ndarray]:
    pred_log = model.predict(eval_df[FEATURES])
    metrics = metric_dict(
        eval_df[TARGET_LOG].to_numpy(dtype=float),
        pred_log,
        eval_df[TARGET_PRICE].to_numpy(dtype=float),
    )
    return metrics, pred_log


def summarize_split(df: pd.DataFrame) -> dict[str, Any]:
    return {
        "rows": int(len(df)),
        "artists": int(df["artist_key"].nunique()) if "artist_key" in df else None,
        "price_min": float(df[TARGET_PRICE].min()),
        "price_median": float(df[TARGET_PRICE].median()),
        "price_max": float(df[TARGET_PRICE].max()),
    }


def main() -> None:
    validate_features(FEATURES)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)

    data = load_data()
    train = data.train.dropna(subset=[TARGET_LOG, TARGET_PRICE]).copy()
    val_warm = data.val_warm.dropna(subset=[TARGET_LOG, TARGET_PRICE]).copy()
    val_cold = data.val_cold.dropna(subset=[TARGET_LOG, TARGET_PRICE]).copy()

    models = build_models()
    results: dict[str, Any] = {
        "experiment_id": "T4-E023",
        "hypothesis_id": "T4-H1",
        "date": date.today().isoformat(),
        "target": TARGET_LOG,
        "features": FEATURES,
        "forbidden_feature_check": "passed",
        "splits": {
            "train": summarize_split(train),
            "val_warm": summarize_split(val_warm),
            "val_cold": summarize_split(val_cold),
        },
        "models": {},
    }
    pred_frames: list[pd.DataFrame] = []

    for model_name, model in models.items():
        model.fit(train[FEATURES], train[TARGET_LOG])
        model_result: dict[str, Any] = {}
        for split_name, eval_df in [("val_warm", val_warm), ("val_cold", val_cold)]:
            metrics, pred_log = evaluate_model(model, train, eval_df)
            model_result[split_name] = metrics
            pred_price = price_from_log(pred_log)
            ape = np.abs(pred_price - eval_df[TARGET_PRICE].to_numpy(dtype=float)) / eval_df[TARGET_PRICE].to_numpy(dtype=float)
            pred_frames.append(
                pd.DataFrame(
                    {
                        "experiment_id": "T4-E023",
                        "model": model_name,
                        "split": split_name,
                        "artist_key": eval_df["artist_key"].to_numpy(),
                        "artist_name_ko": eval_df["artist_name_ko"].to_numpy(),
                        "actual_price_krw": eval_df[TARGET_PRICE].to_numpy(dtype=float),
                        "pred_log_price": pred_log,
                        "pred_price_krw": pred_price,
                        "ape": ape,
                        "medium_category": eval_df["medium_category"].to_numpy(),
                        "support_category": eval_df["support_category"].to_numpy(),
                        "log_area": eval_df["log_area"].to_numpy(dtype=float),
                        "aspect_ratio": eval_df["aspect_ratio"].to_numpy(dtype=float),
                        "has_depth": eval_df["has_depth"].to_numpy(),
                        "is_3d_candidate": eval_df["is_3d_candidate"].to_numpy(),
                    }
                )
            )
        results["models"][model_name] = model_result

    RESULT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.concat(pred_frames, ignore_index=True).to_csv(PRED_PATH, index=False)
    print(RESULT_PATH)
    print(PRED_PATH)


if __name__ == "__main__":
    main()
