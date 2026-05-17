#!/usr/bin/env python3
"""Run Track 4 E026 support unknown ablation.

The experiment checks whether support-related fields should be kept, removed,
or converted into simpler unknown/combo flags. Warm and Cold use their current
validation-stage candidate model families separately.
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
from sklearn.impute import SimpleImputer
from sklearn.linear_model import QuantileRegressor, Ridge
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO = Path(__file__).resolve().parents[2]
SPLIT_DIR = REPO / "data" / "track4_split"
RESULT_DIR = REPO / "data" / "track4" / "results"
PRED_DIR = REPO / "data" / "track4" / "predictions"
RESULT_PATH = RESULT_DIR / "t4_e026_support_unknown_ablation_metrics.json"
PRED_PATH = PRED_DIR / "t4_e026_support_unknown_ablation_predictions.csv"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"

BASE_NUMERIC = ["log_area", "aspect_ratio", "has_depth", "is_3d_candidate"]
BASE_CATEGORICAL = ["medium_category"]
WARM_ARTIST_NUMERIC = ["artist_works_log", "artist_works_count_train"]
WARM_ARTIST_CATEGORICAL = ["artist_key"]

FORBIDDEN_FEATURE_PATTERNS = [
    "source",
    "url",
    "image",
    "gallery",
    "tier",
    "price_krw",
    "ln_price",
]


@dataclass(frozen=True)
class FeatureSet:
    name: str
    numeric: list[str]
    categorical: list[str]
    description: str

    @property
    def features(self) -> list[str]:
        return self.categorical + self.numeric


SUPPORT_FEATURE_SETS = [
    FeatureSet(
        name="no_support",
        numeric=BASE_NUMERIC,
        categorical=BASE_CATEGORICAL,
        description="support 정보를 모두 제외",
    ),
    FeatureSet(
        name="support_category",
        numeric=BASE_NUMERIC,
        categorical=BASE_CATEGORICAL + ["support_category"],
        description="support_category를 범주형으로 사용",
    ),
    FeatureSet(
        name="support_unknown_flag",
        numeric=BASE_NUMERIC + ["is_support_unknown"],
        categorical=BASE_CATEGORICAL,
        description="support_category 대신 unknown 여부만 사용",
    ),
    FeatureSet(
        name="medium_support_bucket",
        numeric=BASE_NUMERIC,
        categorical=BASE_CATEGORICAL + ["medium_support_bucket"],
        description="재료와 지지체 조합 bucket 사용",
    ),
    FeatureSet(
        name="support_category_plus_unknown_flag",
        numeric=BASE_NUMERIC + ["is_support_unknown"],
        categorical=BASE_CATEGORICAL + ["support_category"],
        description="support_category와 unknown 여부를 함께 사용",
    ),
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


def add_support_flags(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    support = out["support_category"].fillna("unknown").astype(str)
    out["is_support_unknown"] = (support == "unknown").astype(int)
    out["medium_support_bucket"] = (
        out["medium_category"].fillna("unknown").astype(str) + "__" + support
    )
    return out


def build_preprocessor(numeric_features: list[str], categorical_features: list[str]) -> ColumnTransformer:
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
            ("numeric", numeric, numeric_features),
            ("categorical", categorical, categorical_features),
        ],
        remainder="drop",
    )


def build_warm_model(feature_set: FeatureSet) -> tuple[Pipeline, list[str]]:
    numeric = feature_set.numeric + WARM_ARTIST_NUMERIC
    categorical = feature_set.categorical + WARM_ARTIST_CATEGORICAL
    features = categorical + numeric
    return (
        Pipeline(
            steps=[
                ("preprocess", build_preprocessor(numeric, categorical)),
                ("model", Ridge(alpha=10.0, random_state=42)),
            ]
        ),
        features,
    )


def build_cold_model(feature_set: FeatureSet) -> tuple[Pipeline, list[str]]:
    numeric = feature_set.numeric
    categorical = feature_set.categorical
    features = categorical + numeric
    return (
        Pipeline(
            steps=[
                ("preprocess", build_preprocessor(numeric, categorical)),
                ("model", QuantileRegressor(quantile=0.5, alpha=0.0001, solver="highs")),
            ]
        ),
        features,
    )


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


def eval_slice_metrics(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, dict[str, float]]:
    pred_price = np.maximum(price_from_log(pred_log), 1.0)
    y_price = df[TARGET_PRICE].to_numpy(dtype=float)
    ape = np.abs(pred_price - y_price) / y_price
    support_unknown = df["is_support_unknown"].to_numpy(dtype=int) == 1
    slices: dict[str, dict[str, float]] = {}
    for name, mask in [("support_known", ~support_unknown), ("support_unknown", support_unknown)]:
        if mask.sum() == 0:
            slices[name] = {"rows": 0, "median_ape": None, "p95_ape": None}
        else:
            slices[name] = {
                "rows": int(mask.sum()),
                "median_ape": float(np.median(ape[mask])),
                "p95_ape": float(np.quantile(ape[mask], 0.95)),
            }
    return slices


def summarize_split(df: pd.DataFrame) -> dict[str, Any]:
    return {
        "rows": int(len(df)),
        "artists": int(df["artist_key"].nunique()),
        "support_unknown_rows": int(df["is_support_unknown"].sum()),
        "support_unknown_rate": float(df["is_support_unknown"].mean()),
    }


def run_one(
    split_name: str,
    train: pd.DataFrame,
    eval_df: pd.DataFrame,
    feature_set: FeatureSet,
    model_builder,
) -> tuple[dict[str, Any], pd.DataFrame]:
    model, features = model_builder(feature_set)
    validate_features(features)
    model.fit(train[features], train[TARGET_LOG])
    pred_log = model.predict(eval_df[features])
    metrics = metric_dict(
        eval_df[TARGET_LOG].to_numpy(dtype=float),
        pred_log,
        eval_df[TARGET_PRICE].to_numpy(dtype=float),
    )
    slices = eval_slice_metrics(eval_df, pred_log)
    pred_price = price_from_log(pred_log)
    ape = np.abs(pred_price - eval_df[TARGET_PRICE].to_numpy(dtype=float)) / eval_df[TARGET_PRICE].to_numpy(dtype=float)
    pred_df = pd.DataFrame(
        {
            "experiment_id": "T4-E026",
            "split": split_name,
            "feature_set": feature_set.name,
            "actual_price_krw": eval_df[TARGET_PRICE].to_numpy(dtype=float),
            "pred_log_price": pred_log,
            "pred_price_krw": pred_price,
            "ape": ape,
            "support_category": eval_df["support_category"].to_numpy(),
            "is_support_unknown": eval_df["is_support_unknown"].to_numpy(),
            "medium_category": eval_df["medium_category"].to_numpy(),
        }
    )
    return {
        "description": feature_set.description,
        "features": features,
        "metrics": metrics,
        "slice_metrics": slices,
    }, pred_df


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)

    train = add_support_flags(pd.read_csv(SPLIT_DIR / "track4_train.csv")).dropna(subset=[TARGET_LOG, TARGET_PRICE])
    val_warm = add_support_flags(pd.read_csv(SPLIT_DIR / "track4_val_warm.csv")).dropna(subset=[TARGET_LOG, TARGET_PRICE])
    val_cold = add_support_flags(pd.read_csv(SPLIT_DIR / "track4_val_cold.csv")).dropna(subset=[TARGET_LOG, TARGET_PRICE])

    results: dict[str, Any] = {
        "experiment_id": "T4-E026",
        "hypothesis_id": ["T4-H6", "T4-H14"],
        "date": date.today().isoformat(),
        "target": TARGET_LOG,
        "warm_model": "ridge",
        "cold_model": "quantile_median",
        "splits": {
            "train": summarize_split(train),
            "val_warm": summarize_split(val_warm),
            "val_cold": summarize_split(val_cold),
        },
        "feature_sets": {},
    }
    pred_frames: list[pd.DataFrame] = []

    for feature_set in SUPPORT_FEATURE_SETS:
        warm_result, warm_pred = run_one("val_warm", train, val_warm, feature_set, build_warm_model)
        cold_result, cold_pred = run_one("val_cold", train, val_cold, feature_set, build_cold_model)
        results["feature_sets"][feature_set.name] = {
            "warm": warm_result,
            "cold": cold_result,
        }
        pred_frames.extend([warm_pred, cold_pred])

    RESULT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.concat(pred_frames, ignore_index=True).to_csv(PRED_PATH, index=False)
    print(RESULT_PATH)
    print(PRED_PATH)


if __name__ == "__main__":
    main()
