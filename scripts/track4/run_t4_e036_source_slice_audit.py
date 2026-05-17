#!/usr/bin/env python3
"""Run Track 4 E036 source slice audit without using source as a model feature."""
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
RESULT_PATH = RESULT_DIR / "t4_e036_source_slice_audit_metrics.json"
PRED_PATH = PRED_DIR / "t4_e036_source_slice_audit_predictions.csv"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"
MIN_SOURCE_ROWS = 20


@dataclass(frozen=True)
class ModelSpec:
    name: str
    split: str
    numeric: list[str]
    categorical: list[str]
    description: str


MODEL_SPECS = [
    ModelSpec(
        "warm_area_aspect",
        "warm",
        ["log_area", "aspect_ratio", "artist_works_log", "artist_works_count_train"],
        ["medium_category", "support_category", "artist_key"],
        "현재 Warm 기준 후보",
    ),
    ModelSpec(
        "cold_area_only",
        "cold",
        ["log_area"],
        ["medium_category"],
        "Cold p95 안정 후보",
    ),
    ModelSpec(
        "cold_full_size",
        "cold",
        ["width_cm", "height_cm", "log_area", "aspect_ratio", "has_depth", "is_3d_candidate"],
        ["medium_category"],
        "Cold median APE 기준 후보",
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


def build_model(spec: ModelSpec) -> Pipeline:
    if spec.split == "warm":
        estimator = Ridge(alpha=10.0, random_state=42)
    else:
        estimator = QuantileRegressor(quantile=0.5, alpha=0.0001, solver="highs")
    return Pipeline([("preprocess", build_preprocessor(spec.numeric, spec.categorical)), ("model", estimator)])


def price_from_log(values: np.ndarray) -> np.ndarray:
    return np.exp(values)


def metric_dict(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, Any]:
    if len(df) == 0:
        return {"rows": 0}
    y_log = df[TARGET_LOG].to_numpy(dtype=float)
    y_price = df[TARGET_PRICE].to_numpy(dtype=float)
    pred_price = np.maximum(price_from_log(pred_log), 1.0)
    ape = np.abs(pred_price - y_price) / y_price
    return {
        "rows": int(len(df)),
        "artists": int(df["artist_key"].nunique()),
        "median_ape": float(np.median(ape)),
        "mape": float(np.mean(ape)),
        "rmse_log": float(np.sqrt(mean_squared_error(y_log, pred_log))),
        "within_30": float(np.mean(ape <= 0.30)),
        "within_50": float(np.mean(ape <= 0.50)),
        "p95_ape": float(np.quantile(ape, 0.95)),
        "median_price_krw": float(np.median(y_price)),
        "missing_support_rate": float((df["support_category"].fillna("unknown") == "unknown").mean()),
        "missing_medium_rate": float((df["medium_category"].fillna("unknown") == "unknown").mean()),
        "three_d_rate": float(df["is_3d_candidate"].fillna(0).astype(int).mean()),
    }


def source_metrics(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for source, source_df in df.groupby("track4_source", dropna=False):
        idx = source_df.index.to_numpy()
        metrics = metric_dict(source_df, pred_log[idx])
        metrics["sample_warning"] = bool(metrics["rows"] < MIN_SOURCE_ROWS)
        out[str(source)] = metrics
    return out


def run_spec(train: pd.DataFrame, warm: pd.DataFrame, cold: pd.DataFrame, spec: ModelSpec) -> tuple[dict[str, Any], pd.DataFrame]:
    eval_df = warm.copy() if spec.split == "warm" else cold.copy()
    eval_df = eval_df.reset_index(drop=True)
    model = build_model(spec)
    features = spec.categorical + spec.numeric
    model.fit(train[features], train[TARGET_LOG])
    pred_log = model.predict(eval_df[features])
    pred_price = price_from_log(pred_log)
    ape = np.abs(pred_price - eval_df[TARGET_PRICE].to_numpy(dtype=float)) / eval_df[TARGET_PRICE].to_numpy(dtype=float)
    pred_df = eval_df[
        [
            "artist_key",
            "artist_name_ko",
            "track4_source",
            "medium_category",
            "support_category",
            "log_area",
            "aspect_ratio",
            "is_3d_candidate",
        ]
    ].copy()
    pred_df["experiment_id"] = "T4-E036"
    pred_df["model_spec"] = spec.name
    pred_df["split"] = spec.split
    pred_df["actual_price_krw"] = eval_df[TARGET_PRICE].to_numpy(dtype=float)
    pred_df["pred_log_price"] = pred_log
    pred_df["pred_price_krw"] = pred_price
    pred_df["ape"] = ape
    return {
        "description": spec.description,
        "split": spec.split,
        "features": features,
        "overall": metric_dict(eval_df, pred_log),
        "source_metrics": source_metrics(eval_df, pred_log),
    }, pred_df


def source_distribution(df: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for source, source_df in df.groupby("track4_source", dropna=False):
        out[str(source)] = {
            "rows": int(len(source_df)),
            "artists": int(source_df["artist_key"].nunique()),
            "median_price_krw": float(source_df[TARGET_PRICE].median()),
            "missing_support_rate": float((source_df["support_category"].fillna("unknown") == "unknown").mean()),
            "missing_medium_rate": float((source_df["medium_category"].fillna("unknown") == "unknown").mean()),
            "three_d_rate": float(source_df["is_3d_candidate"].fillna(0).astype(int).mean()),
        }
    return out


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    train = pd.read_csv(SPLIT_DIR / "track4_train.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    warm = pd.read_csv(SPLIT_DIR / "track4_val_warm.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    cold = pd.read_csv(SPLIT_DIR / "track4_val_cold.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    results: dict[str, Any] = {
        "experiment_id": "T4-E036",
        "hypothesis_id": "T4-H23",
        "date": date.today().isoformat(),
        "important_note": "track4_source is used only for audit grouping, not as a model feature.",
        "source_distribution": {
            "train": source_distribution(train),
            "val_warm": source_distribution(warm),
            "val_cold": source_distribution(cold),
        },
        "model_specs": {},
    }
    pred_frames: list[pd.DataFrame] = []
    for spec in MODEL_SPECS:
        result, pred_df = run_spec(train, warm, cold, spec)
        results["model_specs"][spec.name] = result
        pred_frames.append(pred_df)
    RESULT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.concat(pred_frames, ignore_index=True).to_csv(PRED_PATH, index=False)
    print(RESULT_PATH)
    print(PRED_PATH)


if __name__ == "__main__":
    main()
