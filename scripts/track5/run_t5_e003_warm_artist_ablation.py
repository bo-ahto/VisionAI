#!/usr/bin/env python3
"""Run Track 5 E003 Warm artist feature ablation."""
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
SPLIT_DIR = REPO / "data" / "track5_split"
RESULT_DIR = REPO / "data" / "track5" / "results"
PRED_DIR = REPO / "data" / "track5" / "predictions"
RESULT_PATH = RESULT_DIR / "t5_e003_warm_artist_ablation_metrics.json"
PRED_PATH = PRED_DIR / "t5_e003_warm_artist_ablation_predictions.csv"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"
STRUCTURE_NUMERIC = ["log_area", "aspect_ratio", "has_depth", "is_3d_candidate"]
STRUCTURE_CATEGORICAL = ["medium_category", "support_category"]
ARTIST_HISTORY_NUMERIC = ["artist_works_log", "artist_works_count_train"]
ARTIST_PRICE_NUMERIC = [
    "artist_train_median_log_price",
    "artist_train_mean_log_price",
    "artist_train_iqr_log_price",
]
ARTIST_KEY_CATEGORICAL = ["artist_key"]
FORBIDDEN_PATTERNS = ["source", "url", "image", "gallery", "tier", "price_krw", "ln_price"]


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
    FeatureSet("structure_only", STRUCTURE_NUMERIC, STRUCTURE_CATEGORICAL, "작품 구조 정보만 사용"),
    FeatureSet(
        "structure_plus_artist_history",
        STRUCTURE_NUMERIC + ARTIST_HISTORY_NUMERIC,
        STRUCTURE_CATEGORICAL,
        "작품 구조 + train 기준 작가 작품 수",
    ),
    FeatureSet(
        "structure_plus_artist_key",
        STRUCTURE_NUMERIC,
        STRUCTURE_CATEGORICAL + ARTIST_KEY_CATEGORICAL,
        "작품 구조 + 작가 key",
    ),
    FeatureSet(
        "structure_plus_artist_key_history",
        STRUCTURE_NUMERIC + ARTIST_HISTORY_NUMERIC,
        STRUCTURE_CATEGORICAL + ARTIST_KEY_CATEGORICAL,
        "작품 구조 + 작가 key + 작품 수",
    ),
    FeatureSet(
        "structure_plus_artist_key_history_price_stats",
        STRUCTURE_NUMERIC + ARTIST_HISTORY_NUMERIC + ARTIST_PRICE_NUMERIC,
        STRUCTURE_CATEGORICAL + ARTIST_KEY_CATEGORICAL,
        "작품 구조 + 작가 key + 작품 수 + train 기준 작가 가격 통계",
    ),
]


def onehot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def validate_features(features: list[str]) -> None:
    violations = [f for f in features if any(pattern in f.lower() for pattern in FORBIDDEN_PATTERNS)]
    if violations:
        raise ValueError(f"Forbidden features included: {violations}")


def add_artist_train_stats(train: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    grouped = train.groupby("artist_key")[TARGET_LOG]
    stats = grouped.agg(["median", "mean"]).rename(
        columns={"median": "artist_train_median_log_price", "mean": "artist_train_mean_log_price"}
    )
    stats["artist_train_iqr_log_price"] = grouped.quantile(0.75) - grouped.quantile(0.25)
    out = out.merge(stats, left_on="artist_key", right_index=True, how="left")
    out["artist_train_median_log_price"] = out["artist_train_median_log_price"].fillna(float(train[TARGET_LOG].median()))
    out["artist_train_mean_log_price"] = out["artist_train_mean_log_price"].fillna(float(train[TARGET_LOG].mean()))
    out["artist_train_iqr_log_price"] = out["artist_train_iqr_log_price"].fillna(0.0)
    return out


def build_model(feature_set: FeatureSet) -> Pipeline:
    numeric = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())])
    categorical = Pipeline(
        [("imputer", SimpleImputer(strategy="constant", fill_value="unknown")), ("onehot", onehot_encoder())]
    )
    preprocess = ColumnTransformer(
        [
            ("numeric", numeric, feature_set.numeric),
            ("categorical", categorical, feature_set.categorical),
        ],
        remainder="drop",
    )
    return Pipeline([("preprocess", preprocess), ("model", Ridge(alpha=10.0, random_state=42))])


def metric_dict(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, Any]:
    actual_log = df[TARGET_LOG].to_numpy(dtype=float)
    actual_price = df[TARGET_PRICE].to_numpy(dtype=float)
    pred_price = np.maximum(np.exp(pred_log), 1.0)
    ape = np.abs(pred_price - actual_price) / actual_price
    return {
        "rows": int(len(df)),
        "artists": int(df["artist_key"].nunique()),
        "median_ape": float(np.median(ape)),
        "mape": float(np.mean(ape)),
        "rmse_log": float(np.sqrt(mean_squared_error(actual_log, pred_log))),
        "within_30": float(np.mean(ape <= 0.30)),
        "within_50": float(np.mean(ape <= 0.50)),
        "p90_ape": float(np.quantile(ape, 0.90)),
        "p95_ape": float(np.quantile(ape, 0.95)),
    }


def load_split(name: str) -> pd.DataFrame:
    return pd.read_csv(SPLIT_DIR / f"track5_{name}.csv", low_memory=False).dropna(subset=[TARGET_LOG, TARGET_PRICE]).copy()


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    train_raw = load_split("train")
    val_raw = load_split("val_warm")
    train = add_artist_train_stats(train_raw, train_raw)
    val = add_artist_train_stats(train_raw, val_raw)

    result: dict[str, Any] = {
        "experiment_id": "T5-E003",
        "hypothesis_id": "T5-H3",
        "date": date.today().isoformat(),
        "target": TARGET_LOG,
        "model": "Ridge",
        "models": {},
    }
    pred_frames: list[pd.DataFrame] = []
    for feature_set in FEATURE_SETS:
        validate_features(feature_set.features)
        model = build_model(feature_set)
        model.fit(train[feature_set.features], train[TARGET_LOG])
        pred_log = model.predict(val[feature_set.features])
        metrics = metric_dict(val, pred_log)
        result["models"][feature_set.name] = {
            "description": feature_set.description,
            "features": feature_set.features,
            "metrics": metrics,
        }
        pred_price = np.maximum(np.exp(pred_log), 1.0)
        actual_price = val[TARGET_PRICE].to_numpy(dtype=float)
        pred_frames.append(
            pd.DataFrame(
                {
                    "experiment_id": "T5-E003",
                    "feature_set": feature_set.name,
                    "split": "val_warm",
                    "artist_key": val["artist_key"].to_numpy(),
                    "artist_name_ko": val["artist_name_ko"].to_numpy(),
                    "artist_works_count_train": val["artist_works_count_train"].to_numpy(),
                    "actual_price_krw": actual_price,
                    "pred_log_price": pred_log,
                    "pred_price_krw": pred_price,
                    "ape": np.abs(pred_price - actual_price) / actual_price,
                }
            )
        )

    RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.concat(pred_frames, ignore_index=True).to_csv(PRED_PATH, index=False)
    print(RESULT_PATH)
    print(PRED_PATH)
    print(json.dumps(result["models"], ensure_ascii=False))


if __name__ == "__main__":
    main()
