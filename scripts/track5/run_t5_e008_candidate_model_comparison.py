#!/usr/bin/env python3
"""Run Track 5 E008 model comparison on selected candidate feature sets."""
from __future__ import annotations

import importlib
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor, QuantileRegressor, Ridge
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO = Path(__file__).resolve().parents[2]
SPLIT_DIR = REPO / "data" / "track5_split"
RESULT_DIR = REPO / "data" / "track5" / "results"
PRED_DIR = REPO / "data" / "track5" / "predictions"
RESULT_PATH = RESULT_DIR / "t5_e008_candidate_model_comparison_metrics.json"
PRED_PATH = PRED_DIR / "t5_e008_candidate_model_comparison_predictions.csv"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"


@dataclass(frozen=True)
class FeatureSet:
    task: str
    name: str
    numeric: list[str]
    categorical: list[str]

    @property
    def features(self) -> list[str]:
        return self.categorical + self.numeric


@dataclass(frozen=True)
class ModelSpec:
    name: str
    family: str
    scale_numeric: bool
    estimator: Any


WARM_FULL_SIZE = FeatureSet(
    "warm",
    "warm_full_size",
    [
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
    ],
    ["artist_key", "medium_category", "support_category"],
)
WARM_ALL_COMBO = FeatureSet(
    "warm",
    "warm_all_combo",
    WARM_FULL_SIZE.numeric + ["is_large_work", "is_very_large_work", "is_large_oil", "is_large_acrylic", "is_3d_large"],
    WARM_FULL_SIZE.categorical + ["size_bucket", "medium_size_bucket", "support_size_bucket", "medium_support_bucket"],
)
COLD_FULL_SIZE = FeatureSet(
    "cold",
    "cold_full_size",
    ["log_area", "aspect_ratio", "width_cm", "height_cm", "has_depth", "is_3d_candidate"],
    ["medium_category", "support_category"],
)
COLD_ALL_COMBO = FeatureSet(
    "cold",
    "cold_all_combo",
    COLD_FULL_SIZE.numeric + ["is_large_work", "is_very_large_work", "is_large_oil", "is_large_acrylic", "is_3d_large"],
    COLD_FULL_SIZE.categorical + ["size_bucket", "medium_size_bucket", "support_size_bucket", "medium_support_bucket"],
)
FEATURE_SETS = [WARM_FULL_SIZE, WARM_ALL_COMBO, COLD_FULL_SIZE, COLD_ALL_COMBO]


def onehot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def add_combo_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    q = out["log_area"].quantile([0.25, 0.50, 0.75]).to_numpy()
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


def base_specs() -> list[ModelSpec]:
    specs = [
        ModelSpec("ridge", "linear", True, Ridge(alpha=10.0, random_state=42)),
        ModelSpec("huber", "robust_linear", True, HuberRegressor(alpha=0.0001, epsilon=1.35, max_iter=500)),
        ModelSpec("quantile_median", "robust_linear", True, QuantileRegressor(quantile=0.5, alpha=0.0001, solver="highs")),
        ModelSpec(
            "hist_gradient_boosting",
            "tree",
            False,
            HistGradientBoostingRegressor(loss="squared_error", max_iter=220, learning_rate=0.05, l2_regularization=0.1, random_state=42),
        ),
        ModelSpec(
            "random_forest",
            "tree",
            False,
            RandomForestRegressor(n_estimators=260, min_samples_leaf=8, max_features=0.75, random_state=42, n_jobs=-1),
        ),
    ]
    if importlib.util.find_spec("lightgbm"):
        from lightgbm import LGBMRegressor

        specs.append(
            ModelSpec(
                "lightgbm",
                "tree",
                False,
                LGBMRegressor(
                    objective="regression",
                    n_estimators=260,
                    learning_rate=0.04,
                    num_leaves=24,
                    min_child_samples=40,
                    subsample=0.85,
                    colsample_bytree=0.85,
                    reg_lambda=2.0,
                    random_state=42,
                    verbosity=-1,
                ),
            )
        )
    return specs


def build_pipeline(feature_set: FeatureSet, spec: ModelSpec) -> Pipeline:
    numeric_steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
    if spec.scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))
    numeric = Pipeline(numeric_steps)
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
    return Pipeline([("preprocess", preprocess), ("model", spec.estimator)])


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
    train_raw = add_combo_features(load_split("train"))
    val_warm_raw = add_combo_features(load_split("val_warm"))
    val_cold = add_combo_features(load_split("val_cold"))
    train = add_artist_train_stats(train_raw, train_raw)
    val_warm = add_artist_train_stats(train_raw, val_warm_raw)
    eval_data = {"warm": val_warm, "cold": val_cold}
    train_data = {"warm": train, "cold": train_raw}

    output: dict[str, Any] = {"experiment_id": "T5-E008", "hypothesis_id": "T5-H11", "date": date.today().isoformat(), "results": {}}
    frames: list[pd.DataFrame] = []
    for feature_set in FEATURE_SETS:
        output["results"][feature_set.name] = {}
        task = feature_set.task
        for spec in base_specs():
            model = build_pipeline(feature_set, spec)
            model.fit(train_data[task][feature_set.features], train_data[task][TARGET_LOG])
            pred_log = model.predict(eval_data[task][feature_set.features])
            output["results"][feature_set.name][spec.name] = {"family": spec.family, "metrics": metrics(eval_data[task], pred_log)}
            pred_price = np.maximum(np.exp(pred_log), 1.0)
            actual_price = eval_data[task][TARGET_PRICE].to_numpy(dtype=float)
            frames.append(
                pd.DataFrame(
                    {
                        "experiment_id": "T5-E008",
                        "task": task,
                        "feature_set": feature_set.name,
                        "model": spec.name,
                        "split": f"val_{task}",
                        "artist_key": eval_data[task]["artist_key"].to_numpy(),
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
