#!/usr/bin/env python3
"""Run Track 4 E035 medium-size combination feature experiment."""
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
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO = Path(__file__).resolve().parents[2]
SPLIT_DIR = REPO / "data" / "track4_split"
RESULT_DIR = REPO / "data" / "track4" / "results"
PRED_DIR = REPO / "data" / "track4" / "predictions"
RESULT_PATH = RESULT_DIR / "t4_e035_medium_size_combo_metrics.json"
PRED_PATH = PRED_DIR / "t4_e035_medium_size_combo_predictions.csv"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"


@dataclass(frozen=True)
class FeatureSet:
    name: str
    warm_numeric: list[str]
    warm_categorical: list[str]
    cold_numeric: list[str]
    cold_categorical: list[str]
    description: str


FEATURE_SETS = [
    FeatureSet(
        "baseline_area_aspect",
        ["log_area", "aspect_ratio", "artist_works_log", "artist_works_count_train"],
        ["medium_category", "support_category", "artist_key"],
        ["log_area", "aspect_ratio"],
        ["medium_category"],
        "H33 기준: 면적/비율 중심 baseline",
    ),
    FeatureSet(
        "size_bucket",
        ["log_area", "aspect_ratio", "artist_works_log", "artist_works_count_train"],
        ["medium_category", "support_category", "artist_key", "size_bucket"],
        ["log_area", "aspect_ratio"],
        ["medium_category", "size_bucket"],
        "작품 크기 구간만 추가",
    ),
    FeatureSet(
        "medium_size_bucket",
        ["log_area", "aspect_ratio", "artist_works_log", "artist_works_count_train"],
        ["medium_category", "support_category", "artist_key", "medium_size_bucket"],
        ["log_area", "aspect_ratio"],
        ["medium_category", "medium_size_bucket"],
        "재료와 크기 구간을 묶은 피처 추가",
    ),
    FeatureSet(
        "support_size_bucket",
        ["log_area", "aspect_ratio", "artist_works_log", "artist_works_count_train"],
        ["medium_category", "support_category", "artist_key", "support_size_bucket"],
        ["log_area", "aspect_ratio"],
        ["medium_category", "support_size_bucket"],
        "지지체와 크기 구간을 묶은 피처 추가",
    ),
    FeatureSet(
        "combo_flags",
        [
            "log_area",
            "aspect_ratio",
            "artist_works_log",
            "artist_works_count_train",
            "is_large_oil",
            "is_large_acrylic",
            "is_large_mixed_media",
            "is_small_print",
            "is_large_unknown_support",
        ],
        ["medium_category", "support_category", "artist_key"],
        [
            "log_area",
            "aspect_ratio",
            "is_large_oil",
            "is_large_acrylic",
            "is_large_mixed_media",
            "is_small_print",
            "is_large_unknown_support",
        ],
        ["medium_category"],
        "해석 가능한 재료-크기 rule flag 추가",
    ),
]


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


def add_combo_features(train: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    q33, q67 = train["log_area"].quantile([0.33, 0.67]).tolist()
    out["size_bucket"] = pd.cut(
        out["log_area"],
        bins=[-np.inf, q33, q67, np.inf],
        labels=["small", "medium", "large"],
    ).astype(str)
    medium = out["medium_category"].fillna("unknown").astype(str)
    support = out["support_category"].fillna("unknown").astype(str)
    out["medium_size_bucket"] = medium + "__" + out["size_bucket"]
    out["support_size_bucket"] = support + "__" + out["size_bucket"]
    for column in ["medium_size_bucket", "support_size_bucket"]:
        train_tmp = train.copy()
        train_medium = train_tmp["medium_category"].fillna("unknown").astype(str)
        train_support = train_tmp["support_category"].fillna("unknown").astype(str)
        train_bucket = pd.cut(
            train_tmp["log_area"],
            bins=[-np.inf, q33, q67, np.inf],
            labels=["small", "medium", "large"],
        ).astype(str)
        if column == "medium_size_bucket":
            train_values = train_medium + "__" + train_bucket
        else:
            train_values = train_support + "__" + train_bucket
        frequent = set(train_values.value_counts()[lambda s: s >= 50].index)
        out[column] = np.where(out[column].isin(frequent), out[column], "rare_combo")
    out["is_large_oil"] = ((medium == "oil") & (out["size_bucket"] == "large")).astype(int)
    out["is_large_acrylic"] = ((medium == "acrylic") & (out["size_bucket"] == "large")).astype(int)
    out["is_large_mixed_media"] = ((medium == "mixed_media") & (out["size_bucket"] == "large")).astype(int)
    out["is_small_print"] = ((medium == "print") & (out["size_bucket"] == "small")).astype(int)
    out["is_large_unknown_support"] = ((support == "unknown") & (out["size_bucket"] == "large")).astype(int)
    return out


def build_model(split: str, numeric: list[str], categorical: list[str]) -> Pipeline:
    if split == "warm":
        estimator = Ridge(alpha=10.0, random_state=42)
    else:
        estimator = HuberRegressor(alpha=0.0001, epsilon=1.35, max_iter=300)
    return Pipeline([("preprocess", build_preprocessor(numeric, categorical)), ("model", estimator)])


def price_from_log(values: np.ndarray) -> np.ndarray:
    return np.exp(values)


def metric_dict(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
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


def run_one(split: str, train: pd.DataFrame, eval_df: pd.DataFrame, feature_set: FeatureSet) -> tuple[dict[str, Any], pd.DataFrame]:
    if split == "warm":
        numeric = feature_set.warm_numeric
        categorical = feature_set.warm_categorical
    else:
        numeric = feature_set.cold_numeric
        categorical = feature_set.cold_categorical
    features = categorical + numeric
    model = build_model(split, numeric, categorical)
    model.fit(train[features], train[TARGET_LOG])
    pred_log = model.predict(eval_df[features])
    pred_price = price_from_log(pred_log)
    ape = np.abs(pred_price - eval_df[TARGET_PRICE].to_numpy(dtype=float)) / eval_df[TARGET_PRICE].to_numpy(dtype=float)
    pred_df = pd.DataFrame(
        {
            "experiment_id": "T4-E035",
            "split": f"val_{split}",
            "feature_set": feature_set.name,
            "actual_price_krw": eval_df[TARGET_PRICE].to_numpy(dtype=float),
            "pred_log_price": pred_log,
            "pred_price_krw": pred_price,
            "ape": ape,
            "size_bucket": eval_df["size_bucket"].to_numpy(),
            "medium_category": eval_df["medium_category"].to_numpy(),
            "support_category": eval_df["support_category"].to_numpy(),
        }
    )
    return {
        "description": feature_set.description,
        "features": features,
        "metrics": metric_dict(eval_df, pred_log),
    }, pred_df


def best_by_metric(results: dict[str, Any], split: str, metric: str) -> dict[str, Any]:
    values = [
        (name, cfg[split]["metrics"][metric])
        for name, cfg in results["feature_sets"].items()
    ]
    best_name, best_value = min(values, key=lambda item: item[1])
    return {"feature_set": best_name, metric: best_value}


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    train_raw = pd.read_csv(SPLIT_DIR / "track4_train.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE])
    warm_raw = pd.read_csv(SPLIT_DIR / "track4_val_warm.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE])
    cold_raw = pd.read_csv(SPLIT_DIR / "track4_val_cold.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE])
    train = add_combo_features(train_raw, train_raw)
    warm = add_combo_features(train_raw, warm_raw)
    cold = add_combo_features(train_raw, cold_raw)
    results: dict[str, Any] = {
        "experiment_id": "T4-E035",
        "hypothesis_id": "T4-H28",
        "date": date.today().isoformat(),
        "size_bucket_cutoffs": {
            "small_medium_log_area": float(train_raw["log_area"].quantile(0.33)),
            "medium_large_log_area": float(train_raw["log_area"].quantile(0.67)),
        },
        "feature_sets": {},
    }
    pred_frames = []
    for feature_set in FEATURE_SETS:
        warm_result, warm_pred = run_one("warm", train, warm, feature_set)
        cold_result, cold_pred = run_one("cold", train, cold, feature_set)
        results["feature_sets"][feature_set.name] = {"warm": warm_result, "cold": cold_result}
        pred_frames.extend([warm_pred, cold_pred])
    results["best"] = {
        "warm_median_ape": best_by_metric(results, "warm", "median_ape"),
        "cold_median_ape": best_by_metric(results, "cold", "median_ape"),
        "warm_p95_ape": best_by_metric(results, "warm", "p95_ape"),
        "cold_p95_ape": best_by_metric(results, "cold", "p95_ape"),
    }
    RESULT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.concat(pred_frames, ignore_index=True).to_csv(PRED_PATH, index=False)
    print(RESULT_PATH)
    print(PRED_PATH)


if __name__ == "__main__":
    main()
