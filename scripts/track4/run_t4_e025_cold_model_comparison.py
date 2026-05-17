#!/usr/bin/env python3
"""Run Track 4 E025 Cold model comparison.

This experiment compares robust linear models and tree models using the same
structure-only feature set. Artist, source, gallery, URL, and target price
columns are explicitly forbidden as model inputs.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from lightgbm import LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor, QuantileRegressor, Ridge
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBRegressor


REPO = Path(__file__).resolve().parents[2]
SPLIT_DIR = REPO / "data" / "track4_split"
RESULT_DIR = REPO / "data" / "track4" / "results"
PRED_DIR = REPO / "data" / "track4" / "predictions"
RESULT_PATH = RESULT_DIR / "t4_e025_cold_model_comparison_metrics.json"
PRED_PATH = PRED_DIR / "t4_e025_cold_model_comparison_predictions.csv"

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
class ModelSpec:
    name: str
    model_type: str
    pipeline: Pipeline


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


def build_preprocessor(scale_numeric: bool = True) -> ColumnTransformer:
    numeric_steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
    if scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))
    numeric = Pipeline(steps=numeric_steps)
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


def build_specs() -> list[ModelSpec]:
    return [
        ModelSpec(
            "dummy_median",
            "baseline",
            Pipeline([("preprocess", build_preprocessor()), ("model", DummyRegressor(strategy="median"))]),
        ),
        ModelSpec(
            "ridge",
            "linear",
            Pipeline([("preprocess", build_preprocessor()), ("model", Ridge(alpha=10.0, random_state=42))]),
        ),
        ModelSpec(
            "huber",
            "robust_linear",
            Pipeline(
                [
                    ("preprocess", build_preprocessor()),
                    ("model", HuberRegressor(alpha=0.0001, epsilon=1.35, max_iter=500)),
                ]
            ),
        ),
        ModelSpec(
            "quantile_median",
            "robust_linear",
            Pipeline(
                [
                    ("preprocess", build_preprocessor()),
                    ("model", QuantileRegressor(quantile=0.5, alpha=0.0001, solver="highs")),
                ]
            ),
        ),
        ModelSpec(
            "hist_gradient_boosting",
            "tree",
            Pipeline(
                [
                    ("preprocess", build_preprocessor(scale_numeric=False)),
                    (
                        "model",
                        HistGradientBoostingRegressor(
                            loss="squared_error",
                            max_iter=220,
                            learning_rate=0.05,
                            l2_regularization=0.1,
                            random_state=42,
                        ),
                    ),
                ]
            ),
        ),
        ModelSpec(
            "random_forest",
            "tree",
            Pipeline(
                [
                    ("preprocess", build_preprocessor(scale_numeric=False)),
                    (
                        "model",
                        RandomForestRegressor(
                            n_estimators=280,
                            min_samples_leaf=20,
                            max_features=0.8,
                            random_state=42,
                            n_jobs=-1,
                        ),
                    ),
                ]
            ),
        ),
        ModelSpec(
            "lightgbm",
            "tree",
            Pipeline(
                [
                    ("preprocess", build_preprocessor(scale_numeric=False)),
                    (
                        "model",
                        LGBMRegressor(
                            objective="regression",
                            n_estimators=260,
                            learning_rate=0.04,
                            num_leaves=24,
                            min_child_samples=40,
                            subsample=0.85,
                            colsample_bytree=0.85,
                            reg_lambda=2.0,
                            random_state=42,
                            verbosity=-1,
                        ),
                    ),
                ]
            ),
        ),
        ModelSpec(
            "xgboost",
            "tree",
            Pipeline(
                [
                    ("preprocess", build_preprocessor(scale_numeric=False)),
                    (
                        "model",
                        XGBRegressor(
                            objective="reg:squarederror",
                            n_estimators=260,
                            learning_rate=0.04,
                            max_depth=4,
                            min_child_weight=20,
                            subsample=0.85,
                            colsample_bytree=0.85,
                            reg_lambda=2.0,
                            random_state=42,
                            n_jobs=1,
                            verbosity=0,
                        ),
                    ),
                ]
            ),
        ),
        ModelSpec(
            "catboost",
            "tree",
            Pipeline(
                [
                    ("preprocess", build_preprocessor(scale_numeric=False)),
                    (
                        "model",
                        CatBoostRegressor(
                            loss_function="RMSE",
                            iterations=260,
                            learning_rate=0.04,
                            depth=5,
                            l2_leaf_reg=5.0,
                            random_seed=42,
                            verbose=False,
                        ),
                    ),
                ]
            ),
        ),
    ]


def price_from_log(values: np.ndarray) -> np.ndarray:
    return np.exp(values)


def metric_dict(y_log: np.ndarray, pred_log: np.ndarray, y_price: np.ndarray) -> dict[str, float]:
    pred_price = np.maximum(price_from_log(pred_log), 1.0)
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


def summarize_split(df: pd.DataFrame) -> dict[str, Any]:
    return {
        "rows": int(len(df)),
        "artists": int(df["artist_key"].nunique()),
        "price_min": float(df[TARGET_PRICE].min()),
        "price_median": float(df[TARGET_PRICE].median()),
        "price_max": float(df[TARGET_PRICE].max()),
        "is_3d_candidate_rows": int(df["is_3d_candidate"].sum()),
        "support_unknown_rows": int((df["support_category"].fillna("unknown") == "unknown").sum()),
    }


def main() -> None:
    validate_features(FEATURES)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)

    train = pd.read_csv(SPLIT_DIR / "track4_train.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).copy()
    val_cold = pd.read_csv(SPLIT_DIR / "track4_val_cold.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).copy()

    results: dict[str, Any] = {
        "experiment_id": "T4-E025",
        "hypothesis_id": "T4-H4",
        "date": date.today().isoformat(),
        "target": TARGET_LOG,
        "features": FEATURES,
        "forbidden_feature_check": "passed",
        "splits": {
            "train": summarize_split(train),
            "val_cold": summarize_split(val_cold),
        },
        "models": {},
    }
    pred_frames: list[pd.DataFrame] = []

    for spec in build_specs():
        spec.pipeline.fit(train[FEATURES], train[TARGET_LOG])
        pred_log = spec.pipeline.predict(val_cold[FEATURES])
        metrics = metric_dict(
            val_cold[TARGET_LOG].to_numpy(dtype=float),
            pred_log,
            val_cold[TARGET_PRICE].to_numpy(dtype=float),
        )
        results["models"][spec.name] = {
            "model_type": spec.model_type,
            "metrics": metrics,
        }
        pred_price = price_from_log(pred_log)
        ape = np.abs(pred_price - val_cold[TARGET_PRICE].to_numpy(dtype=float)) / val_cold[TARGET_PRICE].to_numpy(dtype=float)
        pred_frames.append(
            pd.DataFrame(
                {
                    "experiment_id": "T4-E025",
                    "model": spec.name,
                    "model_type": spec.model_type,
                    "split": "val_cold",
                    "artist_key": val_cold["artist_key"].to_numpy(),
                    "artist_name_ko": val_cold["artist_name_ko"].to_numpy(),
                    "actual_price_krw": val_cold[TARGET_PRICE].to_numpy(dtype=float),
                    "pred_log_price": pred_log,
                    "pred_price_krw": pred_price,
                    "ape": ape,
                    "medium_category": val_cold["medium_category"].to_numpy(),
                    "support_category": val_cold["support_category"].to_numpy(),
                    "log_area": val_cold["log_area"].to_numpy(dtype=float),
                    "aspect_ratio": val_cold["aspect_ratio"].to_numpy(dtype=float),
                    "has_depth": val_cold["has_depth"].to_numpy(),
                    "is_3d_candidate": val_cold["is_3d_candidate"].to_numpy(),
                }
            )
        )

    RESULT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.concat(pred_frames, ignore_index=True).to_csv(PRED_PATH, index=False)
    print(RESULT_PATH)
    print(PRED_PATH)


if __name__ == "__main__":
    main()
