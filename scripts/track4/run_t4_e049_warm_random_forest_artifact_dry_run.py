#!/usr/bin/env python3
"""Create the Warm RandomForest artifact and recalculate Warm interval policy."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


REPO = Path(__file__).resolve().parents[2]
SPLIT_DIR = REPO / "data" / "track4_split"
RESULT_DIR = REPO / "data" / "track4" / "results"
MODEL_DIR = REPO / "data" / "track4" / "models"
RESULT_PATH = RESULT_DIR / "t4_e049_warm_random_forest_artifact_dry_run.json"
MODEL_PATH = MODEL_DIR / "track4_warm_final_conditional_stats_random_forest.joblib"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"
CATEGORICAL_FEATURES = ["artist_key", "medium_category", "support_category"]
NUMERIC_FEATURES = [
    "artist_works_log",
    "artist_works_count_train",
    "artist_train_median_log_price",
    "artist_train_mean_log_price",
    "artist_train_iqr_log_price",
    "log_area",
    "aspect_ratio",
]
FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES


def onehot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


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
    stats["artist_train_iqr_log_price"] = grouped.quantile(0.75) - grouped.quantile(0.25)
    out = out.merge(stats, left_on="artist_key", right_index=True, how="left")
    out["artist_train_median_log_price"] = out["artist_train_median_log_price"].fillna(float(train[TARGET_LOG].median()))
    out["artist_train_mean_log_price"] = out["artist_train_mean_log_price"].fillna(float(train[TARGET_LOG].mean()))
    out["artist_train_iqr_log_price"] = out["artist_train_iqr_log_price"].fillna(0.0)
    return out


def add_history_group(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    count = out["artist_works_count_train"].fillna(0)
    out["history_group"] = np.select([count < 5, count < 20], ["low_history", "mid_history"], default="high_history")
    return out


def build_model(seed: int = 42) -> Pipeline:
    preprocessor = ColumnTransformer(
        [
            ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median"))]), NUMERIC_FEATURES),
            (
                "categorical",
                Pipeline([("imputer", SimpleImputer(strategy="constant", fill_value="unknown")), ("onehot", onehot_encoder())]),
                CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
    )
    model = RandomForestRegressor(
        n_estimators=260,
        min_samples_leaf=8,
        max_features=0.75,
        random_state=seed,
        n_jobs=-1,
    )
    return Pipeline([("preprocess", preprocessor), ("model", model)])


def metrics(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, Any]:
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


def group_metrics(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for group in sorted(df["history_group"].unique()):
        mask = df["history_group"].to_numpy() == group
        out[group] = metrics(df.loc[mask], pred_log[mask])
    return out


def interval_policy(val: pd.DataFrame, val_pred: np.ndarray, test: pd.DataFrame, test_pred: np.ndarray) -> dict[str, Any]:
    abs_log_error = np.abs(val_pred - val[TARGET_LOG].to_numpy(dtype=float))
    result: dict[str, Any] = {}
    actual = test[TARGET_PRICE].to_numpy(dtype=float)
    pred = np.maximum(np.exp(test_pred), 1.0)
    for name, q in [("q80", 0.80), ("q90", 0.90)]:
        width_log = float(np.quantile(abs_log_error, q))
        lower = pred / np.exp(width_log)
        upper = pred * np.exp(width_log)
        result[name] = {
            "width_log": width_log,
            "range_multiplier": float(np.exp(width_log * 2)),
            "coverage": float(np.mean((actual >= lower) & (actual <= upper))),
        }
    return result


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    train_raw = pd.read_csv(SPLIT_DIR / "track4_train.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    val_raw = pd.read_csv(SPLIT_DIR / "track4_val_warm.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    test_raw = pd.read_csv(SPLIT_DIR / "track4_test_warm.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    train = add_history_group(add_artist_train_stats(train_raw, train_raw))
    val = add_history_group(add_artist_train_stats(train_raw, val_raw))
    test = add_history_group(add_artist_train_stats(train_raw, test_raw))

    model = build_model(seed=42)
    model.fit(train[FEATURES], train[TARGET_LOG])
    val_pred = model.predict(val[FEATURES])
    test_pred = model.predict(test[FEATURES])
    joblib.dump({"model": model, "features": FEATURES, "target": TARGET_LOG}, MODEL_PATH, compress=3)

    result = {
        "experiment_id": "T4-E049",
        "hypothesis_id": "T4-H38",
        "date": date.today().isoformat(),
        "artifact": str(MODEL_PATH.relative_to(REPO)),
        "features": FEATURES,
        "model": "RandomForestRegressor",
        "val_warm": {
            "overall": metrics(val, val_pred),
            "history_groups": group_metrics(val, val_pred),
        },
        "test_warm": {
            "overall": metrics(test, test_pred),
            "history_groups": group_metrics(test, test_pred),
            "interval_policy_from_val": interval_policy(val, val_pred, test, test_pred),
        },
        "passed": True,
    }
    RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(RESULT_PATH)
    print(MODEL_PATH)
    print(json.dumps(result["test_warm"]["overall"], ensure_ascii=False))


if __name__ == "__main__":
    main()
