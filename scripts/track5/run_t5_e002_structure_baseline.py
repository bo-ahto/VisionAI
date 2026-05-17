#!/usr/bin/env python3
"""Run Track 5 E002 structure-only Warm/Cold baseline."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO = Path(__file__).resolve().parents[2]
SPLIT_DIR = REPO / "data" / "track5_split"
RESULT_DIR = REPO / "data" / "track5" / "results"
PRED_DIR = REPO / "data" / "track5" / "predictions"
RESULT_PATH = RESULT_DIR / "t5_e002_structure_baseline_metrics.json"
PRED_PATH = PRED_DIR / "t5_e002_structure_baseline_predictions.csv"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"
NUMERIC_FEATURES = ["log_area", "aspect_ratio", "has_depth", "is_3d_candidate"]
CATEGORICAL_FEATURES = ["medium_category", "support_category"]
FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES
FORBIDDEN_PATTERNS = ["artist", "source", "url", "image", "gallery", "tier", "price_krw", "ln_price"]


def validate_features(features: list[str]) -> None:
    violations = [f for f in features if any(pattern in f.lower() for pattern in FORBIDDEN_PATTERNS)]
    if violations:
        raise ValueError(f"Forbidden features included: {violations}")


def onehot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def preprocessor() -> ColumnTransformer:
    numeric = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())])
    categorical = Pipeline(
        [("imputer", SimpleImputer(strategy="constant", fill_value="unknown")), ("onehot", onehot_encoder())]
    )
    return ColumnTransformer(
        [
            ("numeric", numeric, NUMERIC_FEATURES),
            ("categorical", categorical, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )


def models() -> dict[str, Pipeline]:
    return {
        "dummy_median": Pipeline([("preprocess", preprocessor()), ("model", DummyRegressor(strategy="median"))]),
        "ridge": Pipeline([("preprocess", preprocessor()), ("model", Ridge(alpha=10.0, random_state=42))]),
        "huber": Pipeline(
            [
                ("preprocess", preprocessor()),
                ("model", HuberRegressor(alpha=0.0001, epsilon=1.35, max_iter=500)),
            ]
        ),
    }


def load_split(name: str) -> pd.DataFrame:
    return pd.read_csv(SPLIT_DIR / f"track5_{name}.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).copy()


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


def prediction_frame(experiment_id: str, model_name: str, split: str, df: pd.DataFrame, pred_log: np.ndarray) -> pd.DataFrame:
    pred_price = np.maximum(np.exp(pred_log), 1.0)
    actual_price = df[TARGET_PRICE].to_numpy(dtype=float)
    return pd.DataFrame(
        {
            "experiment_id": experiment_id,
            "model": model_name,
            "split": split,
            "artist_key": df["artist_key"].to_numpy(),
            "artist_name_ko": df["artist_name_ko"].to_numpy(),
            "actual_price_krw": actual_price,
            "pred_log_price": pred_log,
            "pred_price_krw": pred_price,
            "ape": np.abs(pred_price - actual_price) / actual_price,
            **{feature: df[feature].to_numpy() for feature in FEATURES},
        }
    )


def main() -> None:
    validate_features(FEATURES)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)

    train = load_split("train")
    eval_splits = {"val_warm": load_split("val_warm"), "val_cold": load_split("val_cold")}
    output: dict[str, Any] = {
        "experiment_id": "T5-E002",
        "hypothesis_id": "T5-H2",
        "date": date.today().isoformat(),
        "target": TARGET_LOG,
        "features": FEATURES,
        "forbidden_feature_check": "passed",
        "models": {},
    }
    pred_frames: list[pd.DataFrame] = []
    for model_name, model in models().items():
        model.fit(train[FEATURES], train[TARGET_LOG])
        output["models"][model_name] = {}
        for split_name, df in eval_splits.items():
            pred_log = model.predict(df[FEATURES])
            output["models"][model_name][split_name] = metric_dict(df, pred_log)
            pred_frames.append(prediction_frame("T5-E002", model_name, split_name, df, pred_log))

    RESULT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.concat(pred_frames, ignore_index=True).to_csv(PRED_PATH, index=False)
    print(RESULT_PATH)
    print(PRED_PATH)
    print(json.dumps(output["models"], ensure_ascii=False))


if __name__ == "__main__":
    main()
