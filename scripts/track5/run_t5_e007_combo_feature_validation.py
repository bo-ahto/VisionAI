#!/usr/bin/env python3
"""Run Track 5 E007 generated combo feature validation."""
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
RESULT_PATH = RESULT_DIR / "t5_e007_combo_feature_validation_metrics.json"
PRED_PATH = PRED_DIR / "t5_e007_combo_feature_validation_predictions.csv"

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


WARM_BASE_NUMERIC = [
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
]
WARM_BASE_CATEGORICAL = ["artist_key", "medium_category", "support_category"]
COLD_BASE_NUMERIC = ["log_area", "aspect_ratio", "width_cm", "height_cm", "has_depth", "is_3d_candidate"]
COLD_BASE_CATEGORICAL = ["medium_category", "support_category"]

COMBO_CATEGORICAL = ["size_bucket", "medium_size_bucket", "support_size_bucket", "medium_support_bucket"]
COMBO_NUMERIC = ["is_large_work", "is_very_large_work", "is_large_oil", "is_large_acrylic", "is_3d_large"]

WARM_SETS = [
    FeatureSet("warm_full_size", WARM_BASE_NUMERIC, WARM_BASE_CATEGORICAL, "E006 Warm full_size 기준"),
    FeatureSet(
        "warm_plus_size_bucket",
        WARM_BASE_NUMERIC,
        WARM_BASE_CATEGORICAL + ["size_bucket"],
        "크기 구간 추가",
    ),
    FeatureSet(
        "warm_plus_medium_size",
        WARM_BASE_NUMERIC,
        WARM_BASE_CATEGORICAL + ["size_bucket", "medium_size_bucket"],
        "재료-크기 조합 추가",
    ),
    FeatureSet(
        "warm_plus_support_size",
        WARM_BASE_NUMERIC,
        WARM_BASE_CATEGORICAL + ["size_bucket", "support_size_bucket"],
        "지지체-크기 조합 추가",
    ),
    FeatureSet(
        "warm_plus_rule_flags",
        WARM_BASE_NUMERIC + COMBO_NUMERIC,
        WARM_BASE_CATEGORICAL,
        "대형/재료/3D rule flag 추가",
    ),
    FeatureSet(
        "warm_all_combo",
        WARM_BASE_NUMERIC + COMBO_NUMERIC,
        WARM_BASE_CATEGORICAL + COMBO_CATEGORICAL,
        "모든 조합 피처 추가",
    ),
]

COLD_SETS = [
    FeatureSet("cold_full_size", COLD_BASE_NUMERIC, COLD_BASE_CATEGORICAL, "E006 Cold full_size 기준"),
    FeatureSet(
        "cold_plus_size_bucket",
        COLD_BASE_NUMERIC,
        COLD_BASE_CATEGORICAL + ["size_bucket"],
        "크기 구간 추가",
    ),
    FeatureSet(
        "cold_plus_medium_size",
        COLD_BASE_NUMERIC,
        COLD_BASE_CATEGORICAL + ["size_bucket", "medium_size_bucket"],
        "재료-크기 조합 추가",
    ),
    FeatureSet(
        "cold_plus_support_size",
        COLD_BASE_NUMERIC,
        COLD_BASE_CATEGORICAL + ["size_bucket", "support_size_bucket"],
        "지지체-크기 조합 추가",
    ),
    FeatureSet(
        "cold_plus_rule_flags",
        COLD_BASE_NUMERIC + COMBO_NUMERIC,
        COLD_BASE_CATEGORICAL,
        "대형/재료/3D rule flag 추가",
    ),
    FeatureSet(
        "cold_all_combo",
        COLD_BASE_NUMERIC + COMBO_NUMERIC,
        COLD_BASE_CATEGORICAL + COMBO_CATEGORICAL,
        "모든 조합 피처 추가",
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


def size_bucket(log_area: pd.Series) -> pd.Series:
    q = log_area.quantile([0.25, 0.50, 0.75]).to_numpy()
    return pd.cut(log_area, bins=[-np.inf, q[0], q[1], q[2], np.inf], labels=["small", "mid_small", "mid_large", "large"]).astype(str)


def add_combo_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["size_bucket"] = size_bucket(pd.to_numeric(out["log_area"], errors="coerce"))
    medium = out["medium_category"].fillna("unknown").astype(str)
    support = out["support_category"].fillna("unknown").astype(str)
    size = out["size_bucket"].fillna("unknown").astype(str)
    out["medium_size_bucket"] = medium + "__" + size
    out["support_size_bucket"] = support + "__" + size
    out["is_large_work"] = (out["size_bucket"] == "large").astype(int)
    out["is_very_large_work"] = (pd.to_numeric(out["area_cm2"], errors="coerce") >= 10000).fillna(False).astype(int)
    out["is_large_oil"] = (medium.str.contains("oil", case=False, na=False) & (out["is_large_work"] == 1)).astype(int)
    out["is_large_acrylic"] = (medium.str.contains("acrylic", case=False, na=False) & (out["is_large_work"] == 1)).astype(int)
    out["is_3d_large"] = (out["is_3d_candidate"].astype(bool) & (out["is_large_work"] == 1)).astype(int)
    if "medium_support_bucket" not in out:
        out["medium_support_bucket"] = medium + "__" + support
    return out


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
    model = Ridge(alpha=10.0, random_state=42) if task == "warm" else QuantileRegressor(quantile=0.5, alpha=0.0001, solver="highs")
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
    result: dict[str, Any] = {}
    frames: list[pd.DataFrame] = []
    for feature_set in feature_sets:
        validate_features(feature_set.features, allow_artist=task == "warm")
        model = build_pipeline(feature_set, task)
        model.fit(train[feature_set.features], train[TARGET_LOG])
        pred_log = model.predict(val[feature_set.features])
        result[feature_set.name] = {
            "description": feature_set.description,
            "features": feature_set.features,
            "metrics": metrics(val, pred_log),
        }
        pred_price = np.maximum(np.exp(pred_log), 1.0)
        actual_price = val[TARGET_PRICE].to_numpy(dtype=float)
        frames.append(
            pd.DataFrame(
                {
                    "experiment_id": "T5-E007",
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
    return result, frames


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    train_raw = add_combo_features(load_split("train"))
    val_warm_raw = add_combo_features(load_split("val_warm"))
    val_cold = add_combo_features(load_split("val_cold"))
    train = add_artist_train_stats(train_raw, train_raw)
    val_warm = add_artist_train_stats(train_raw, val_warm_raw)

    warm_result, warm_frames = run_task("warm", train, val_warm, WARM_SETS)
    cold_result, cold_frames = run_task("cold", train_raw, val_cold, COLD_SETS)
    output = {
        "experiment_id": "T5-E007",
        "hypothesis_id": "T5-H10",
        "date": date.today().isoformat(),
        "warm_model": "Ridge",
        "cold_model": "QuantileRegressor",
        "warm": warm_result,
        "cold": cold_result,
    }
    RESULT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.concat(warm_frames + cold_frames, ignore_index=True).to_csv(PRED_PATH, index=False)
    print(RESULT_PATH)
    print(PRED_PATH)
    print(json.dumps({"warm": warm_result, "cold": cold_result}, ensure_ascii=False))


if __name__ == "__main__":
    main()
