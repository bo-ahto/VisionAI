#!/usr/bin/env python3
"""Run Track 4 E033 size feature reduction experiment."""
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
RESULT_PATH = RESULT_DIR / "t4_e033_size_feature_reduction_metrics.json"
PRED_PATH = PRED_DIR / "t4_e033_size_feature_reduction_predictions.csv"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"


@dataclass(frozen=True)
class SizeSet:
    name: str
    numeric: list[str]
    description: str


SIZE_SETS = [
    SizeSet("no_size", [], "크기 피처 제외"),
    SizeSet("area_only", ["log_area"], "대표 크기값 log_area만 사용"),
    SizeSet("area_aspect", ["log_area", "aspect_ratio"], "면적과 가로세로 비율 사용"),
    SizeSet("raw_width_height", ["width_cm", "height_cm"], "원본 가로/세로 사용"),
    SizeSet("full_size", ["width_cm", "height_cm", "log_area", "aspect_ratio", "has_depth", "is_3d_candidate"], "가용 크기 피처 모두 사용"),
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


def make_model(split: str, size_set: SizeSet) -> tuple[Pipeline, list[str]]:
    if split == "warm":
        numeric = size_set.numeric + ["artist_works_log", "artist_works_count_train"]
        categorical = ["medium_category", "support_category", "artist_key"]
        model = Ridge(alpha=10.0, random_state=42)
    else:
        numeric = size_set.numeric
        categorical = ["medium_category"]
        model = QuantileRegressor(quantile=0.5, alpha=0.0001, solver="highs")
    features = categorical + numeric
    return Pipeline([("preprocess", build_preprocessor(numeric, categorical)), ("model", model)]), features


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


def run_one(split: str, train: pd.DataFrame, eval_df: pd.DataFrame, size_set: SizeSet) -> tuple[dict[str, Any], pd.DataFrame]:
    model, features = make_model(split, size_set)
    model.fit(train[features], train[TARGET_LOG])
    pred_log = model.predict(eval_df[features])
    pred_price = price_from_log(pred_log)
    ape = np.abs(pred_price - eval_df[TARGET_PRICE].to_numpy(dtype=float)) / eval_df[TARGET_PRICE].to_numpy(dtype=float)
    pred_df = pd.DataFrame(
        {
            "experiment_id": "T4-E033",
            "split": f"val_{split}",
            "size_set": size_set.name,
            "actual_price_krw": eval_df[TARGET_PRICE].to_numpy(dtype=float),
            "pred_log_price": pred_log,
            "pred_price_krw": pred_price,
            "ape": ape,
        }
    )
    return {"description": size_set.description, "features": features, "metrics": metric_dict(eval_df, pred_log)}, pred_df


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    train = pd.read_csv(SPLIT_DIR / "track4_train.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE])
    warm = pd.read_csv(SPLIT_DIR / "track4_val_warm.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE])
    cold = pd.read_csv(SPLIT_DIR / "track4_val_cold.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE])
    results: dict[str, Any] = {"experiment_id": "T4-E033", "hypothesis_id": "T4-H15", "date": date.today().isoformat(), "size_sets": {}}
    pred_frames = []
    for size_set in SIZE_SETS:
        warm_result, warm_pred = run_one("warm", train, warm, size_set)
        cold_result, cold_pred = run_one("cold", train, cold, size_set)
        results["size_sets"][size_set.name] = {"warm": warm_result, "cold": cold_result}
        pred_frames.extend([warm_pred, cold_pred])
    RESULT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.concat(pred_frames, ignore_index=True).to_csv(PRED_PATH, index=False)
    print(RESULT_PATH)
    print(PRED_PATH)


if __name__ == "__main__":
    main()
