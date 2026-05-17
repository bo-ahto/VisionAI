#!/usr/bin/env python3
"""Run Track 5 E010 final candidate test evaluation."""
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
from sklearn.linear_model import HuberRegressor, QuantileRegressor
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO = Path(__file__).resolve().parents[2]
SPLIT_DIR = REPO / "data" / "track5_split"
RESULT_DIR = REPO / "data" / "track5" / "results"
PRED_DIR = REPO / "data" / "track5" / "predictions"
RESULT_PATH = RESULT_DIR / "t5_e010_final_candidate_test_metrics.json"
PRED_PATH = PRED_DIR / "t5_e010_final_candidate_test_predictions.csv"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"


@dataclass(frozen=True)
class Candidate:
    task: str
    name: str
    model_name: str
    numeric: list[str]
    categorical: list[str]

    @property
    def features(self) -> list[str]:
        return self.categorical + self.numeric


WARM_FULL_NUMERIC = [
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
WARM_FULL_CATEGORICAL = ["artist_key", "medium_category", "support_category"]
COLD_FULL_NUMERIC = ["log_area", "aspect_ratio", "width_cm", "height_cm", "has_depth", "is_3d_candidate"]
COLD_FULL_CATEGORICAL = ["medium_category", "support_category"]
COMBO_NUMERIC = ["is_large_work", "is_very_large_work", "is_large_oil", "is_large_acrylic", "is_3d_large"]
COMBO_CATEGORICAL = ["size_bucket", "medium_size_bucket", "support_size_bucket", "medium_support_bucket"]

CANDIDATES = [
    Candidate("warm", "warm_full_size_huber", "huber", WARM_FULL_NUMERIC, WARM_FULL_CATEGORICAL),
    Candidate("warm", "warm_all_combo_huber", "huber", WARM_FULL_NUMERIC + COMBO_NUMERIC, WARM_FULL_CATEGORICAL + COMBO_CATEGORICAL),
    Candidate("cold", "cold_full_size_quantile", "quantile_median", COLD_FULL_NUMERIC, COLD_FULL_CATEGORICAL),
    Candidate("cold", "cold_all_combo_quantile", "quantile_median", COLD_FULL_NUMERIC + COMBO_NUMERIC, COLD_FULL_CATEGORICAL + COMBO_CATEGORICAL),
]


def onehot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def add_combo_features(df: pd.DataFrame, reference: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    q = reference["log_area"].quantile([0.25, 0.50, 0.75]).to_numpy()
    out["size_bucket"] = pd.cut(
        out["log_area"],
        bins=[-np.inf, q[0], q[1], q[2], np.inf],
        labels=["small", "mid_small", "mid_large", "large"],
    ).astype(str)
    medium = out["medium_category"].fillna("unknown").astype(str)
    support = out["support_category"].fillna("unknown").astype(str)
    size = out["size_bucket"].fillna("unknown").astype(str)
    out["medium_size_bucket"] = medium + "__" + size
    out["support_size_bucket"] = support + "__" + size
    out["medium_support_bucket"] = medium + "__" + support
    out["is_large_work"] = (out["size_bucket"] == "large").astype(int)
    out["is_very_large_work"] = (pd.to_numeric(out["area_cm2"], errors="coerce") >= 10000).fillna(False).astype(int)
    out["is_large_oil"] = (medium.str.contains("oil", case=False, na=False) & (out["is_large_work"] == 1)).astype(int)
    out["is_large_acrylic"] = (medium.str.contains("acrylic", case=False, na=False) & (out["is_large_work"] == 1)).astype(int)
    out["is_3d_large"] = (out["is_3d_candidate"].astype(bool) & (out["is_large_work"] == 1)).astype(int)
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


def build_pipeline(candidate: Candidate) -> Pipeline:
    numeric = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())])
    categorical = Pipeline(
        [("imputer", SimpleImputer(strategy="constant", fill_value="unknown")), ("onehot", onehot_encoder())]
    )
    preprocess = ColumnTransformer(
        [
            ("numeric", numeric, candidate.numeric),
            ("categorical", categorical, candidate.categorical),
        ],
        remainder="drop",
    )
    if candidate.model_name == "huber":
        model = HuberRegressor(alpha=0.0001, epsilon=1.35, max_iter=1000)
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


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    train_base = load_split("train")
    test_warm_base = load_split("test_warm")
    test_cold_base = load_split("test_cold")
    train_combo = add_combo_features(train_base, train_base)
    test_warm_combo = add_combo_features(test_warm_base, train_base)
    test_cold_combo = add_combo_features(test_cold_base, train_base)
    train_warm = add_artist_train_stats(train_combo, train_combo)
    test_warm = add_artist_train_stats(train_combo, test_warm_combo)

    data = {
        "warm": (train_warm, test_warm),
        "cold": (train_combo, test_cold_combo),
    }
    output: dict[str, Any] = {
        "experiment_id": "T5-E010",
        "hypothesis_id": "T5-H13",
        "date": date.today().isoformat(),
        "results": {},
    }
    frames: list[pd.DataFrame] = []
    for candidate in CANDIDATES:
        train, test = data[candidate.task]
        model = build_pipeline(candidate)
        model.fit(train[candidate.features], train[TARGET_LOG])
        pred_log = model.predict(test[candidate.features])
        output["results"][candidate.name] = {
            "task": candidate.task,
            "model": candidate.model_name,
            "features": candidate.features,
            "metrics": metrics(test, pred_log),
        }
        pred_price = np.maximum(np.exp(pred_log), 1.0)
        actual_price = test[TARGET_PRICE].to_numpy(dtype=float)
        frames.append(
            pd.DataFrame(
                {
                    "experiment_id": "T5-E010",
                    "task": candidate.task,
                    "candidate": candidate.name,
                    "split": f"test_{candidate.task}",
                    "artist_key": test["artist_key"].to_numpy(),
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
