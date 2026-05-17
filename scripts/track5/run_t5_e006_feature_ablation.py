#!/usr/bin/env python3
"""Run Track 5 E006 feature ablation on frozen Warm/Cold baseline models."""
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
SPLIT_DIR = REPO / "data" / "track5_split"
RESULT_DIR = REPO / "data" / "track5" / "results"
PRED_DIR = REPO / "data" / "track5" / "predictions"
RESULT_PATH = RESULT_DIR / "t5_e006_feature_ablation_metrics.json"
PRED_PATH = PRED_DIR / "t5_e006_feature_ablation_predictions.csv"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"
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


WARM_SETS = [
    FeatureSet(
        "warm_baseline",
        [
            "artist_works_log",
            "artist_works_count_train",
            "artist_train_median_log_price",
            "artist_train_mean_log_price",
            "artist_train_iqr_log_price",
            "log_area",
            "aspect_ratio",
        ],
        ["artist_key", "medium_category", "support_category"],
        "T5-E005 Warm 기준선",
    ),
    FeatureSet(
        "warm_no_support",
        [
            "artist_works_log",
            "artist_works_count_train",
            "artist_train_median_log_price",
            "artist_train_mean_log_price",
            "artist_train_iqr_log_price",
            "log_area",
            "aspect_ratio",
        ],
        ["artist_key", "medium_category"],
        "support_category 제거",
    ),
    FeatureSet(
        "warm_full_size",
        [
            "artist_works_log",
            "artist_works_count_train",
            "artist_train_median_log_price",
            "artist_train_mean_log_price",
            "artist_train_iqr_log_price",
            "log_area",
            "aspect_ratio",
            "width_cm",
            "height_cm",
            "has_depth",
            "is_3d_candidate",
        ],
        ["artist_key", "medium_category", "support_category"],
        "width/height/3D flag 추가",
    ),
    FeatureSet(
        "warm_area_only",
        [
            "artist_works_log",
            "artist_works_count_train",
            "artist_train_median_log_price",
            "artist_train_mean_log_price",
            "artist_train_iqr_log_price",
            "log_area",
        ],
        ["artist_key", "medium_category", "support_category"],
        "aspect_ratio 제거",
    ),
]

COLD_SETS = [
    FeatureSet(
        "cold_baseline",
        ["log_area", "aspect_ratio", "has_depth", "is_3d_candidate"],
        ["medium_category", "support_category"],
        "T5-E005 Cold 기준선",
    ),
    FeatureSet(
        "cold_no_support",
        ["log_area", "aspect_ratio", "has_depth", "is_3d_candidate"],
        ["medium_category"],
        "support_category 제거",
    ),
    FeatureSet(
        "cold_full_size",
        ["log_area", "aspect_ratio", "width_cm", "height_cm", "has_depth", "is_3d_candidate"],
        ["medium_category", "support_category"],
        "width/height 추가",
    ),
    FeatureSet(
        "cold_area_only",
        ["log_area"],
        ["medium_category", "support_category"],
        "aspect_ratio와 3D flag 제거",
    ),
    FeatureSet(
        "cold_no_3d_flags",
        ["log_area", "aspect_ratio"],
        ["medium_category", "support_category"],
        "3D flag만 제거",
    ),
]


def onehot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def validate_features(features: list[str], allow_artist: bool) -> None:
    patterns = FORBIDDEN_PATTERNS if allow_artist else FORBIDDEN_PATTERNS + ["artist"]
    violations = [f for f in features if any(pattern in f.lower() for pattern in patterns)]
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


def build_pipeline(feature_set: FeatureSet, task: str) -> Pipeline:
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
    if task == "warm":
        model = Ridge(alpha=10.0, random_state=42)
    else:
        model = QuantileRegressor(quantile=0.5, alpha=0.0001, solver="highs")
    return Pipeline([("preprocess", preprocess), ("model", model)])


def load_split(name: str) -> pd.DataFrame:
    return pd.read_csv(SPLIT_DIR / f"track5_{name}.csv", low_memory=False).dropna(subset=[TARGET_LOG, TARGET_PRICE]).copy()


def metrics(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, Any]:
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


def run_task(task: str, train: pd.DataFrame, val: pd.DataFrame, feature_sets: list[FeatureSet]) -> tuple[dict[str, Any], list[pd.DataFrame]]:
    out: dict[str, Any] = {}
    pred_frames: list[pd.DataFrame] = []
    allow_artist = task == "warm"
    for feature_set in feature_sets:
        validate_features(feature_set.features, allow_artist=allow_artist)
        model = build_pipeline(feature_set, task)
        model.fit(train[feature_set.features], train[TARGET_LOG])
        pred_log = model.predict(val[feature_set.features])
        out[feature_set.name] = {
            "description": feature_set.description,
            "features": feature_set.features,
            "metrics": metrics(val, pred_log),
        }
        pred_price = np.maximum(np.exp(pred_log), 1.0)
        actual_price = val[TARGET_PRICE].to_numpy(dtype=float)
        pred_frames.append(
            pd.DataFrame(
                {
                    "experiment_id": "T5-E006",
                    "task": task,
                    "feature_set": feature_set.name,
                    "split": f"val_{task}",
                    "artist_key": val["artist_key"].to_numpy(),
                    "actual_price_krw": actual_price,
                    "pred_log_price": pred_log,
                    "pred_price_krw": pred_price,
                    "ape": np.abs(pred_price - actual_price) / actual_price,
                }
            )
        )
    return out, pred_frames


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    train_raw = load_split("train")
    val_warm_raw = load_split("val_warm")
    val_cold = load_split("val_cold")
    train = add_artist_train_stats(train_raw, train_raw)
    val_warm = add_artist_train_stats(train_raw, val_warm_raw)

    warm_results, warm_preds = run_task("warm", train, val_warm, WARM_SETS)
    cold_results, cold_preds = run_task("cold", train_raw, val_cold, COLD_SETS)
    result = {
        "experiment_id": "T5-E006",
        "hypothesis_id": "T5-H9",
        "date": date.today().isoformat(),
        "warm_model": "Ridge",
        "cold_model": "QuantileRegressor",
        "warm": warm_results,
        "cold": cold_results,
    }
    RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.concat(warm_preds + cold_preds, ignore_index=True).to_csv(PRED_PATH, index=False)
    print(RESULT_PATH)
    print(PRED_PATH)
    print(json.dumps({"warm": warm_results, "cold": cold_results}, ensure_ascii=False))


if __name__ == "__main__":
    main()
