#!/usr/bin/env python3
"""Run Track 4 E037 Warm train-only artist history feature experiment."""
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
RESULT_PATH = RESULT_DIR / "t4_e037_warm_artist_history_metrics.json"
PRED_PATH = PRED_DIR / "t4_e037_warm_artist_history_predictions.csv"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"


@dataclass(frozen=True)
class FeatureSet:
    name: str
    numeric: list[str]
    categorical: list[str]
    description: str


FEATURE_SETS = [
    FeatureSet(
        "structure_only",
        ["log_area", "aspect_ratio"],
        ["medium_category", "support_category"],
        "작가 관련 피처 제외",
    ),
    FeatureSet(
        "artist_key_only",
        ["log_area", "aspect_ratio"],
        ["medium_category", "support_category", "artist_key"],
        "작가 key만 추가",
    ),
    FeatureSet(
        "artist_count_only",
        ["log_area", "aspect_ratio", "artist_works_log", "artist_works_count_train"],
        ["medium_category", "support_category"],
        "train 기준 작가 작품 수만 추가",
    ),
    FeatureSet(
        "artist_price_stats_only",
        [
            "log_area",
            "aspect_ratio",
            "artist_works_log",
            "artist_works_count_train",
            "artist_train_median_log_price",
            "artist_train_mean_log_price",
            "artist_train_iqr_log_price",
        ],
        ["medium_category", "support_category"],
        "train 기준 작가 가격 통계만 추가",
    ),
    FeatureSet(
        "artist_key_count",
        ["log_area", "aspect_ratio", "artist_works_log", "artist_works_count_train"],
        ["medium_category", "support_category", "artist_key"],
        "현재 Warm 기준 후보",
    ),
    FeatureSet(
        "artist_key_price_stats",
        [
            "log_area",
            "aspect_ratio",
            "artist_works_log",
            "artist_works_count_train",
            "artist_train_median_log_price",
            "artist_train_mean_log_price",
            "artist_train_iqr_log_price",
        ],
        ["medium_category", "support_category", "artist_key"],
        "작가 key와 train 기준 가격 통계를 함께 사용",
    ),
]


def onehot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def build_model(numeric: list[str], categorical: list[str]) -> Pipeline:
    return Pipeline(
        [
            (
                "preprocess",
                ColumnTransformer(
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
                ),
            ),
            ("model", Ridge(alpha=10.0, random_state=42)),
        ]
    )


def add_artist_train_stats(train: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    grouped = train.groupby("artist_key")[TARGET_LOG]
    stats = grouped.agg(["median", "mean", "count"]).rename(
        columns={
            "median": "artist_train_median_log_price",
            "mean": "artist_train_mean_log_price",
            "count": "artist_train_price_count",
        }
    )
    q75 = grouped.quantile(0.75)
    q25 = grouped.quantile(0.25)
    stats["artist_train_iqr_log_price"] = q75 - q25
    out = out.merge(stats, left_on="artist_key", right_index=True, how="left")
    global_median = float(train[TARGET_LOG].median())
    global_mean = float(train[TARGET_LOG].mean())
    out["artist_train_median_log_price"] = out["artist_train_median_log_price"].fillna(global_median)
    out["artist_train_mean_log_price"] = out["artist_train_mean_log_price"].fillna(global_mean)
    out["artist_train_iqr_log_price"] = out["artist_train_iqr_log_price"].fillna(0.0)
    return out


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


def run_one(train: pd.DataFrame, warm: pd.DataFrame, feature_set: FeatureSet) -> tuple[dict[str, Any], pd.DataFrame]:
    features = feature_set.categorical + feature_set.numeric
    model = build_model(feature_set.numeric, feature_set.categorical)
    model.fit(train[features], train[TARGET_LOG])
    pred_log = model.predict(warm[features])
    pred_price = price_from_log(pred_log)
    ape = np.abs(pred_price - warm[TARGET_PRICE].to_numpy(dtype=float)) / warm[TARGET_PRICE].to_numpy(dtype=float)
    pred_df = warm[
        [
            "artist_key",
            "artist_name_ko",
            "track4_source",
            "medium_category",
            "support_category",
            "artist_works_count_train",
            "artist_works_log",
        ]
    ].copy()
    pred_df["experiment_id"] = "T4-E037"
    pred_df["feature_set"] = feature_set.name
    pred_df["actual_price_krw"] = warm[TARGET_PRICE].to_numpy(dtype=float)
    pred_df["pred_log_price"] = pred_log
    pred_df["pred_price_krw"] = pred_price
    pred_df["ape"] = ape
    return {
        "description": feature_set.description,
        "features": features,
        "metrics": metric_dict(warm, pred_log),
    }, pred_df


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    train_raw = pd.read_csv(SPLIT_DIR / "track4_train.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    warm_raw = pd.read_csv(SPLIT_DIR / "track4_val_warm.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    train = add_artist_train_stats(train_raw, train_raw)
    warm = add_artist_train_stats(train_raw, warm_raw)
    results: dict[str, Any] = {
        "experiment_id": "T4-E037",
        "hypothesis_id": "T4-H3",
        "date": date.today().isoformat(),
        "important_note": "artist price stats are calculated from track4_train only. No validation target is used.",
        "feature_sets": {},
    }
    pred_frames: list[pd.DataFrame] = []
    for feature_set in FEATURE_SETS:
        result, pred_df = run_one(train, warm, feature_set)
        results["feature_sets"][feature_set.name] = result
        pred_frames.append(pred_df)
    best = min(
        ((name, cfg["metrics"]["median_ape"]) for name, cfg in results["feature_sets"].items()),
        key=lambda item: item[1],
    )
    results["best_by_median_ape"] = {"feature_set": best[0], "median_ape": best[1]}
    RESULT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.concat(pred_frames, ignore_index=True).to_csv(PRED_PATH, index=False)
    print(RESULT_PATH)
    print(PRED_PATH)


if __name__ == "__main__":
    main()
