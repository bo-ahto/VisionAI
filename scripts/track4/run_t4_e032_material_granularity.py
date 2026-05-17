#!/usr/bin/env python3
"""Run Track 4 E032 material granularity experiment for Cold prediction."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import QuantileRegressor
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO = Path(__file__).resolve().parents[2]
SPLIT_DIR = REPO / "data" / "track4_split"
RESULT_DIR = REPO / "data" / "track4" / "results"
PRED_DIR = REPO / "data" / "track4" / "predictions"
RESULT_PATH = RESULT_DIR / "t4_e032_material_granularity_metrics.json"
PRED_PATH = PRED_DIR / "t4_e032_material_granularity_predictions.csv"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"
BASE_NUMERIC = ["log_area", "aspect_ratio"]
BASE_CATEGORICAL = ["medium_category"]
MATERIAL_FLAGS = [
    "is_oil",
    "is_acrylic",
    "is_mixed_media",
    "is_print",
    "is_ink",
    "is_sculpture_material",
    "is_other_material",
    "is_rare_material",
]
RARE_MIN_COUNT = 100


def onehot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def add_material_features(train: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    medium = out["medium_category"].fillna("unknown").astype(str)
    train_counts = train["medium_category"].fillna("unknown").value_counts()
    rare_values = set(train_counts[train_counts < RARE_MIN_COUNT].index)
    out["medium_rare_bucket"] = np.where(medium.isin(rare_values), "rare", medium)
    out["is_oil"] = (medium == "oil").astype(int)
    out["is_acrylic"] = (medium == "acrylic").astype(int)
    out["is_mixed_media"] = (medium == "mixed_media").astype(int)
    out["is_print"] = (medium == "print").astype(int)
    out["is_ink"] = (medium == "ink").astype(int)
    out["is_sculpture_material"] = (medium == "sculpture_material").astype(int)
    out["is_other_material"] = medium.isin(["other", "painting_material", "unknown"]).astype(int)
    out["is_rare_material"] = medium.isin(rare_values).astype(int)
    return out


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
            ("model", QuantileRegressor(quantile=0.5, alpha=0.0001, solver="highs")),
        ]
    )


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


def group_metrics(df: pd.DataFrame, pred_log: np.ndarray, column: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for value in sorted(df[column].dropna().unique().tolist()):
        mask = df[column].to_numpy() == value
        if mask.sum() >= 10:
            out[str(value)] = metric_dict(df.loc[mask], pred_log[mask])
    return out


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    train_raw = pd.read_csv(SPLIT_DIR / "track4_train.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE])
    val_raw = pd.read_csv(SPLIT_DIR / "track4_val_cold.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE])
    train = add_material_features(train_raw, train_raw)
    val = add_material_features(train_raw, val_raw)

    feature_sets = {
        "baseline_medium_category": {
            "numeric": BASE_NUMERIC,
            "categorical": BASE_CATEGORICAL,
        },
        "rare_bucket_category": {
            "numeric": BASE_NUMERIC,
            "categorical": ["medium_rare_bucket"],
        },
        "material_flags_only": {
            "numeric": BASE_NUMERIC + MATERIAL_FLAGS,
            "categorical": [],
        },
        "medium_category_plus_flags": {
            "numeric": BASE_NUMERIC + MATERIAL_FLAGS,
            "categorical": BASE_CATEGORICAL,
        },
    }
    results: dict[str, Any] = {
        "experiment_id": "T4-E032",
        "hypothesis_id": "T4-H13",
        "date": date.today().isoformat(),
        "rare_min_count": RARE_MIN_COUNT,
        "train_medium_counts": train_raw["medium_category"].fillna("unknown").value_counts().to_dict(),
        "feature_sets": {},
    }
    pred_frames: list[pd.DataFrame] = []
    for name, cfg in feature_sets.items():
        features = cfg["categorical"] + cfg["numeric"]
        model = build_model(cfg["numeric"], cfg["categorical"])
        model.fit(train[features], train[TARGET_LOG])
        pred_log = model.predict(val[features])
        pred_price = price_from_log(pred_log)
        ape = np.abs(pred_price - val[TARGET_PRICE].to_numpy(dtype=float)) / val[TARGET_PRICE].to_numpy(dtype=float)
        results["feature_sets"][name] = {
            "features": features,
            "metrics": metric_dict(val, pred_log),
            "medium_metrics": group_metrics(val, pred_log, "medium_category"),
            "rare_bucket_metrics": group_metrics(val, pred_log, "medium_rare_bucket"),
        }
        pred_frames.append(
            pd.DataFrame(
                {
                    "experiment_id": "T4-E032",
                    "feature_set": name,
                    "medium_category": val["medium_category"].to_numpy(),
                    "medium_rare_bucket": val["medium_rare_bucket"].to_numpy(),
                    "actual_price_krw": val[TARGET_PRICE].to_numpy(dtype=float),
                    "pred_log_price": pred_log,
                    "pred_price_krw": pred_price,
                    "ape": ape,
                }
            )
        )
    RESULT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.concat(pred_frames, ignore_index=True).to_csv(PRED_PATH, index=False)
    print(RESULT_PATH)
    print(PRED_PATH)


if __name__ == "__main__":
    main()
