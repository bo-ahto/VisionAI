#!/usr/bin/env python3
"""Recheck Track 5 Warm Huber convergence settings."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

REPO = Path(__file__).resolve().parents[2]
SPLIT_DIR = REPO / "data" / "track5_split"
RESULT_DIR = REPO / "data" / "track5" / "results"
PRED_DIR = REPO / "data" / "track5" / "predictions"
RESULT_PATH = RESULT_DIR / "t5_e011_warm_huber_convergence_recheck_metrics.json"
PRED_PATH = PRED_DIR / "t5_e011_warm_huber_convergence_recheck_predictions.csv"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"

NUMERIC = [
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
CATEGORICAL = ["artist_key", "medium_category", "support_category"]
FEATURES = CATEGORICAL + NUMERIC


def onehot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def load_split(name: str) -> pd.DataFrame:
    return pd.read_csv(SPLIT_DIR / f"track5_{name}.csv", low_memory=False).dropna(subset=[TARGET_LOG, TARGET_PRICE]).copy()


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


def build_pipeline(max_iter: int) -> Pipeline:
    numeric = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())])
    categorical = Pipeline(
        [("imputer", SimpleImputer(strategy="constant", fill_value="unknown")), ("onehot", onehot_encoder())]
    )
    preprocess = ColumnTransformer(
        [("numeric", numeric, NUMERIC), ("categorical", categorical, CATEGORICAL)],
        remainder="drop",
    )
    model = HuberRegressor(alpha=0.0001, epsilon=1.35, max_iter=max_iter)
    return Pipeline([("preprocess", preprocess), ("model", model)])


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


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    train_raw = load_split("train")
    val_raw = load_split("val_warm")
    test_raw = load_split("test_warm")
    train = add_artist_train_stats(train_raw, train_raw)
    val = add_artist_train_stats(train_raw, val_raw)
    test = add_artist_train_stats(train_raw, test_raw)

    output: dict[str, Any] = {
        "experiment_id": "T5-E011",
        "hypothesis_id": "T5-H14",
        "date": date.today().isoformat(),
        "results": {},
    }
    frames: list[pd.DataFrame] = []
    for max_iter in [1000, 3000, 5000]:
        model = build_pipeline(max_iter=max_iter)
        model.fit(train[FEATURES], train[TARGET_LOG])
        n_iter = int(model.named_steps["model"].n_iter_)
        key = f"huber_max_iter_{max_iter}"
        output["results"][key] = {"n_iter": n_iter, "metrics": {}}
        for split_name, df in [("val_warm", val), ("test_warm", test)]:
            pred_log = model.predict(df[FEATURES])
            output["results"][key]["metrics"][split_name] = metrics(df, pred_log)
            pred_price = np.maximum(np.exp(pred_log), 1.0)
            actual_price = df[TARGET_PRICE].to_numpy(dtype=float)
            frames.append(
                pd.DataFrame(
                    {
                        "experiment_id": "T5-E011",
                        "setting": key,
                        "split": split_name,
                        "artist_key": df["artist_key"].to_numpy(),
                        "actual_price_krw": actual_price,
                        "pred_log_price": pred_log,
                        "pred_price_krw": pred_price,
                        "ape": np.abs(pred_price - actual_price) / actual_price,
                    }
                )
            )
    RESULT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.concat(frames, ignore_index=True).to_csv(PRED_PATH, index=False)
    print(RESULT_PATH)
    print(PRED_PATH)
    print(json.dumps(output["results"], ensure_ascii=False))


if __name__ == "__main__":
    main()
