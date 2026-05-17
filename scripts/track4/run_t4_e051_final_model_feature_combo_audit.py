#!/usr/bin/env python3
"""Audit generated feature combinations with the current final Track 4 models."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import QuantileRegressor
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


REPO = Path(__file__).resolve().parents[2]
SPLIT_DIR = REPO / "data" / "track4_split"
RESULT_DIR = REPO / "data" / "track4" / "results"
RESULT_PATH = RESULT_DIR / "t4_e051_final_model_feature_combo_audit_metrics.json"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"
PRICE_STATS = [
    "artist_train_median_log_price",
    "artist_train_mean_log_price",
    "artist_train_iqr_log_price",
]
COMBO_FLAGS = [
    "is_large_oil",
    "is_large_acrylic",
    "is_large_mixed_media",
    "is_small_print",
    "is_large_unknown_support",
]


@dataclass(frozen=True)
class FeatureSet:
    name: str
    warm_numeric: list[str]
    warm_categorical: list[str]
    cold_numeric: list[str]
    cold_categorical: list[str]
    description: str


BASE_WARM_NUMERIC = [
    "artist_works_log",
    "artist_works_count_train",
    *PRICE_STATS,
    "log_area",
    "aspect_ratio",
]
BASE_WARM_CATEGORICAL = ["artist_key", "medium_category", "support_category"]
BASE_COLD_NUMERIC = ["width_cm", "height_cm", "log_area", "aspect_ratio", "has_depth", "is_3d_candidate"]
BASE_COLD_CATEGORICAL = ["medium_category"]

FEATURE_SETS = [
    FeatureSet("baseline_final", BASE_WARM_NUMERIC, BASE_WARM_CATEGORICAL, BASE_COLD_NUMERIC, BASE_COLD_CATEGORICAL, "현재 최종 후보 피처"),
    FeatureSet(
        "medium_size_bucket",
        BASE_WARM_NUMERIC,
        BASE_WARM_CATEGORICAL + ["medium_size_bucket"],
        BASE_COLD_NUMERIC,
        BASE_COLD_CATEGORICAL + ["medium_size_bucket"],
        "재료와 크기 구간 조합 추가",
    ),
    FeatureSet(
        "support_size_bucket",
        BASE_WARM_NUMERIC,
        BASE_WARM_CATEGORICAL + ["support_size_bucket"],
        BASE_COLD_NUMERIC,
        BASE_COLD_CATEGORICAL + ["support_size_bucket"],
        "지지체와 크기 구간 조합 추가",
    ),
    FeatureSet(
        "combo_flags",
        BASE_WARM_NUMERIC + COMBO_FLAGS,
        BASE_WARM_CATEGORICAL,
        BASE_COLD_NUMERIC + COMBO_FLAGS,
        BASE_COLD_CATEGORICAL,
        "재료-크기 rule flag 추가",
    ),
]


def onehot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=True)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=True)


def add_artist_train_stats(train: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    grouped = train.groupby("artist_key")[TARGET_LOG]
    stats = grouped.agg(["median", "mean", "count"]).rename(
        columns={"median": "artist_train_median_log_price", "mean": "artist_train_mean_log_price", "count": "artist_train_price_count"}
    )
    stats["artist_train_iqr_log_price"] = grouped.quantile(0.75) - grouped.quantile(0.25)
    out = out.merge(stats, left_on="artist_key", right_index=True, how="left")
    out["artist_train_median_log_price"] = out["artist_train_median_log_price"].fillna(float(train[TARGET_LOG].median()))
    out["artist_train_mean_log_price"] = out["artist_train_mean_log_price"].fillna(float(train[TARGET_LOG].mean()))
    out["artist_train_iqr_log_price"] = out["artist_train_iqr_log_price"].fillna(0.0)
    return out


def add_combo_features(train: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    q33, q67 = train["log_area"].quantile([0.33, 0.67]).tolist()
    out["size_bucket"] = pd.cut(out["log_area"], bins=[-np.inf, q33, q67, np.inf], labels=["small", "medium", "large"]).astype(str)
    medium = out["medium_category"].fillna("unknown").astype(str)
    support = out["support_category"].fillna("unknown").astype(str)
    out["medium_size_bucket"] = medium + "__" + out["size_bucket"]
    out["support_size_bucket"] = support + "__" + out["size_bucket"]

    train_bucket = pd.cut(train["log_area"], bins=[-np.inf, q33, q67, np.inf], labels=["small", "medium", "large"]).astype(str)
    train_medium = train["medium_category"].fillna("unknown").astype(str)
    train_support = train["support_category"].fillna("unknown").astype(str)
    frequent_medium = set((train_medium + "__" + train_bucket).value_counts()[lambda s: s >= 50].index)
    frequent_support = set((train_support + "__" + train_bucket).value_counts()[lambda s: s >= 50].index)
    out["medium_size_bucket"] = np.where(out["medium_size_bucket"].isin(frequent_medium), out["medium_size_bucket"], "rare_combo")
    out["support_size_bucket"] = np.where(out["support_size_bucket"].isin(frequent_support), out["support_size_bucket"], "rare_combo")
    out["is_large_oil"] = ((medium == "oil") & (out["size_bucket"] == "large")).astype(int)
    out["is_large_acrylic"] = ((medium == "acrylic") & (out["size_bucket"] == "large")).astype(int)
    out["is_large_mixed_media"] = ((medium == "mixed_media") & (out["size_bucket"] == "large")).astype(int)
    out["is_small_print"] = ((medium == "print") & (out["size_bucket"] == "small")).astype(int)
    out["is_large_unknown_support"] = ((support == "unknown") & (out["size_bucket"] == "large")).astype(int)
    return out


def build_preprocessor(numeric: list[str], categorical: list[str]) -> ColumnTransformer:
    return ColumnTransformer(
        [
            ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median"))]), numeric),
            ("categorical", Pipeline([("imputer", SimpleImputer(strategy="constant", fill_value="unknown")), ("onehot", onehot_encoder())]), categorical),
        ],
        remainder="drop",
    )


def build_warm_model(numeric: list[str], categorical: list[str]) -> Pipeline:
    model = RandomForestRegressor(n_estimators=260, min_samples_leaf=8, max_features=0.75, random_state=42, n_jobs=-1)
    return Pipeline([("preprocess", build_preprocessor(numeric, categorical)), ("model", model)])


def build_cold_model(numeric: list[str], categorical: list[str]) -> Pipeline:
    model = QuantileRegressor(quantile=0.5, alpha=0.0001, solver="highs")
    return Pipeline([("preprocess", build_preprocessor(numeric, categorical)), ("model", model)])


def metrics(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    actual_price = df[TARGET_PRICE].to_numpy(dtype=float)
    pred_price = np.maximum(np.exp(pred_log), 1.0)
    ape = np.abs(pred_price - actual_price) / actual_price
    return {
        "rows": int(len(df)),
        "median_ape": float(np.median(ape)),
        "mape": float(np.mean(ape)),
        "rmse_log": float(np.sqrt(mean_squared_error(df[TARGET_LOG].to_numpy(dtype=float), pred_log))),
        "within_30": float(np.mean(ape <= 0.30)),
        "within_50": float(np.mean(ape <= 0.50)),
        "p90_ape": float(np.quantile(ape, 0.90)),
        "p95_ape": float(np.quantile(ape, 0.95)),
    }


def evaluate(train: pd.DataFrame, eval_df: pd.DataFrame, feature_set: FeatureSet, split: str) -> dict[str, Any]:
    if split == "warm":
        numeric = feature_set.warm_numeric
        categorical = feature_set.warm_categorical
        model = build_warm_model(numeric, categorical)
    else:
        numeric = feature_set.cold_numeric
        categorical = feature_set.cold_categorical
        model = build_cold_model(numeric, categorical)
    features = categorical + numeric
    model.fit(train[features], train[TARGET_LOG])
    pred = model.predict(eval_df[features])
    return {"features": features, "metrics": metrics(eval_df, pred)}


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    train_raw = pd.read_csv(SPLIT_DIR / "track4_train.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    val_warm_raw = pd.read_csv(SPLIT_DIR / "track4_val_warm.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    test_warm_raw = pd.read_csv(SPLIT_DIR / "track4_test_warm.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    val_cold_raw = pd.read_csv(SPLIT_DIR / "track4_val_cold.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    test_cold_raw = pd.read_csv(SPLIT_DIR / "track4_test_cold.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)

    train = add_combo_features(train_raw, add_artist_train_stats(train_raw, train_raw))
    val_warm = add_combo_features(train_raw, add_artist_train_stats(train_raw, val_warm_raw))
    test_warm = add_combo_features(train_raw, add_artist_train_stats(train_raw, test_warm_raw))
    val_cold = add_combo_features(train_raw, val_cold_raw)
    test_cold = add_combo_features(train_raw, test_cold_raw)

    result: dict[str, Any] = {
        "experiment_id": "T4-E051",
        "hypothesis_id": ["T4-H39"],
        "date": date.today().isoformat(),
        "question": "생성 조합 피처가 최종 Warm/Cold 모델 기준으로도 성능을 개선하는가",
        "feature_sets": {},
    }
    for feature_set in FEATURE_SETS:
        result["feature_sets"][feature_set.name] = {
            "description": feature_set.description,
            "warm_val": evaluate(train, val_warm, feature_set, "warm"),
            "warm_test": evaluate(train, test_warm, feature_set, "warm"),
            "cold_val": evaluate(train, val_cold, feature_set, "cold"),
            "cold_test": evaluate(train, test_cold, feature_set, "cold"),
        }
    result["best"] = {
        split: min(result["feature_sets"], key=lambda name: result["feature_sets"][name][split]["metrics"]["median_ape"])
        for split in ["warm_val", "warm_test", "cold_val", "cold_test"]
    }
    RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(RESULT_PATH)
    print(json.dumps({k: result["best"][k] for k in result["best"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
