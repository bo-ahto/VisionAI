#!/usr/bin/env python3
"""Run Track 4 E024 Warm artist feature ablation.

This experiment uses the fixed Track 4 train/val_warm split and compares
structure-only features against train-derived artist history and artist key
categorical features. It does not use source, gallery, URL, or target price
statistics as input features.
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
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO = Path(__file__).resolve().parents[2]
SPLIT_DIR = REPO / "data" / "track4_split"
RESULT_DIR = REPO / "data" / "track4" / "results"
PRED_DIR = REPO / "data" / "track4" / "predictions"
RESULT_PATH = RESULT_DIR / "t4_e024_warm_artist_ablation_metrics.json"
PRED_PATH = PRED_DIR / "t4_e024_warm_artist_ablation_predictions.csv"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"

STRUCTURE_NUMERIC = [
    "log_area",
    "aspect_ratio",
    "has_depth",
    "is_3d_candidate",
]
STRUCTURE_CATEGORICAL = [
    "medium_category",
    "support_category",
]
ARTIST_HISTORY_NUMERIC = [
    "artist_works_log",
    "artist_works_count_train",
]
ARTIST_KEY_CATEGORICAL = [
    "artist_key",
]
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


FEATURE_SETS = [
    FeatureSet(
        name="structure_only",
        numeric=STRUCTURE_NUMERIC,
        categorical=STRUCTURE_CATEGORICAL,
        description="작가 정보 제외, 작품 구조 정보만 사용",
    ),
    FeatureSet(
        name="structure_plus_artist_history",
        numeric=STRUCTURE_NUMERIC + ARTIST_HISTORY_NUMERIC,
        categorical=STRUCTURE_CATEGORICAL,
        description="작품 구조 정보 + train 기준 작가 작품 수",
    ),
    FeatureSet(
        name="structure_plus_artist_key",
        numeric=STRUCTURE_NUMERIC,
        categorical=STRUCTURE_CATEGORICAL + ARTIST_KEY_CATEGORICAL,
        description="작품 구조 정보 + 작가 key categorical",
    ),
    FeatureSet(
        name="structure_plus_artist_key_history",
        numeric=STRUCTURE_NUMERIC + ARTIST_HISTORY_NUMERIC,
        categorical=STRUCTURE_CATEGORICAL + ARTIST_KEY_CATEGORICAL,
        description="작품 구조 정보 + 작가 key + train 기준 작가 작품 수",
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


def build_preprocessor(feature_set: FeatureSet) -> ColumnTransformer:
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
            ("numeric", numeric, feature_set.numeric),
            ("categorical", categorical, feature_set.categorical),
        ],
        remainder="drop",
    )


def build_model(feature_set: FeatureSet) -> Pipeline:
    return Pipeline(
        steps=[
            ("preprocess", build_preprocessor(feature_set)),
            ("model", Ridge(alpha=10.0, random_state=42)),
        ]
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


def summarize_split(df: pd.DataFrame) -> dict[str, Any]:
    return {
        "rows": int(len(df)),
        "artists": int(df["artist_key"].nunique()),
        "price_median": float(df[TARGET_PRICE].median()),
        "artist_count_min": float(df["artist_works_count_train"].min()),
        "artist_count_median": float(df["artist_works_count_train"].median()),
        "artist_count_max": float(df["artist_works_count_train"].max()),
    }


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)

    train = pd.read_csv(SPLIT_DIR / "track4_train.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).copy()
    val_warm = pd.read_csv(SPLIT_DIR / "track4_val_warm.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).copy()

    results: dict[str, Any] = {
        "experiment_id": "T4-E024",
        "hypothesis_id": ["T4-H2", "T4-H20"],
        "date": date.today().isoformat(),
        "target": TARGET_LOG,
        "splits": {
            "train": summarize_split(train),
            "val_warm": summarize_split(val_warm),
        },
        "models": {},
    }
    pred_frames: list[pd.DataFrame] = []

    for feature_set in FEATURE_SETS:
        validate_features(feature_set.features)
        model = build_model(feature_set)
        model.fit(train[feature_set.features], train[TARGET_LOG])
        pred_log = model.predict(val_warm[feature_set.features])
        metrics = metric_dict(
            val_warm[TARGET_LOG].to_numpy(dtype=float),
            pred_log,
            val_warm[TARGET_PRICE].to_numpy(dtype=float),
        )
        results["models"][feature_set.name] = {
            "description": feature_set.description,
            "features": feature_set.features,
            "metrics": metrics,
        }
        pred_price = price_from_log(pred_log)
        ape = np.abs(pred_price - val_warm[TARGET_PRICE].to_numpy(dtype=float)) / val_warm[TARGET_PRICE].to_numpy(dtype=float)
        pred_frames.append(
            pd.DataFrame(
                {
                    "experiment_id": "T4-E024",
                    "feature_set": feature_set.name,
                    "split": "val_warm",
                    "artist_key": val_warm["artist_key"].to_numpy(),
                    "artist_name_ko": val_warm["artist_name_ko"].to_numpy(),
                    "artist_works_count_train": val_warm["artist_works_count_train"].to_numpy(),
                    "actual_price_krw": val_warm[TARGET_PRICE].to_numpy(dtype=float),
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
