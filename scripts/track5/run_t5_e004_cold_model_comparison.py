#!/usr/bin/env python3
"""Run Track 5 E004 Cold model comparison on structure-only features."""
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
from sklearn.dummy import DummyRegressor
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
RESULT_PATH = RESULT_DIR / "t5_e004_cold_model_comparison_metrics.json"
PRED_PATH = PRED_DIR / "t5_e004_cold_model_comparison_predictions.csv"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"
NUMERIC_FEATURES = ["log_area", "aspect_ratio", "has_depth", "is_3d_candidate"]
CATEGORICAL_FEATURES = ["medium_category", "support_category"]
FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES
FORBIDDEN_PATTERNS = ["artist", "source", "url", "image", "gallery", "tier", "price_krw", "ln_price"]


@dataclass(frozen=True)
class ModelSpec:
    name: str
    family: str
    pipeline: Pipeline


def validate_features(features: list[str]) -> None:
    violations = [f for f in features if any(pattern in f.lower() for pattern in FORBIDDEN_PATTERNS)]
    if violations:
        raise ValueError(f"Forbidden features included: {violations}")


def onehot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def preprocessor(scale_numeric: bool = True) -> ColumnTransformer:
    numeric_steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
    if scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))
    numeric = Pipeline(numeric_steps)
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


def optional_model_specs() -> list[ModelSpec]:
    specs: list[ModelSpec] = []
    if importlib.util.find_spec("lightgbm"):
        from lightgbm import LGBMRegressor

        specs.append(
            ModelSpec(
                "lightgbm",
                "tree",
                Pipeline(
                    [
                        ("preprocess", preprocessor(scale_numeric=False)),
                        (
                            "model",
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
                        ),
                    ]
                ),
            )
        )
    if importlib.util.find_spec("xgboost"):
        from xgboost import XGBRegressor

        specs.append(
            ModelSpec(
                "xgboost",
                "tree",
                Pipeline(
                    [
                        ("preprocess", preprocessor(scale_numeric=False)),
                        (
                            "model",
                            XGBRegressor(
                                objective="reg:squarederror",
                                n_estimators=260,
                                learning_rate=0.04,
                                max_depth=4,
                                min_child_weight=20,
                                subsample=0.85,
                                colsample_bytree=0.85,
                                reg_lambda=2.0,
                                random_state=42,
                                n_jobs=1,
                            ),
                        ),
                    ]
                ),
            )
        )
    if importlib.util.find_spec("catboost"):
        from catboost import CatBoostRegressor

        specs.append(
            ModelSpec(
                "catboost",
                "tree",
                Pipeline(
                    [
                        ("preprocess", preprocessor(scale_numeric=False)),
                        (
                            "model",
                            CatBoostRegressor(
                                loss_function="RMSE",
                                iterations=260,
                                learning_rate=0.04,
                                depth=5,
                                l2_leaf_reg=5.0,
                                random_seed=42,
                                verbose=False,
                            ),
                        ),
                    ]
                ),
            )
        )
    return specs


def model_specs() -> list[ModelSpec]:
    specs = [
        ModelSpec(
            "dummy_median",
            "baseline",
            Pipeline([("preprocess", preprocessor()), ("model", DummyRegressor(strategy="median"))]),
        ),
        ModelSpec("ridge", "linear", Pipeline([("preprocess", preprocessor()), ("model", Ridge(alpha=10.0))])),
        ModelSpec(
            "huber",
            "robust_linear",
            Pipeline(
                [
                    ("preprocess", preprocessor()),
                    ("model", HuberRegressor(alpha=0.0001, epsilon=1.35, max_iter=500)),
                ]
            ),
        ),
        ModelSpec(
            "quantile_median",
            "robust_linear",
            Pipeline(
                [
                    ("preprocess", preprocessor()),
                    ("model", QuantileRegressor(quantile=0.5, alpha=0.0001, solver="highs")),
                ]
            ),
        ),
        ModelSpec(
            "hist_gradient_boosting",
            "tree",
            Pipeline(
                [
                    ("preprocess", preprocessor(scale_numeric=False)),
                    (
                        "model",
                        HistGradientBoostingRegressor(
                            loss="squared_error",
                            max_iter=220,
                            learning_rate=0.05,
                            l2_regularization=0.1,
                            random_state=42,
                        ),
                    ),
                ]
            ),
        ),
        ModelSpec(
            "random_forest",
            "tree",
            Pipeline(
                [
                    ("preprocess", preprocessor(scale_numeric=False)),
                    (
                        "model",
                        RandomForestRegressor(
                            n_estimators=280,
                            min_samples_leaf=20,
                            max_features=0.8,
                            random_state=42,
                            n_jobs=-1,
                        ),
                    ),
                ]
            ),
        ),
    ]
    return specs + optional_model_specs()


def load_split(name: str) -> pd.DataFrame:
    return pd.read_csv(SPLIT_DIR / f"track5_{name}.csv", low_memory=False).dropna(subset=[TARGET_LOG, TARGET_PRICE]).copy()


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


def main() -> None:
    validate_features(FEATURES)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    train = load_split("train")
    val = load_split("val_cold")
    result: dict[str, Any] = {
        "experiment_id": "T5-E004",
        "hypothesis_id": "T5-H4",
        "date": date.today().isoformat(),
        "target": TARGET_LOG,
        "features": FEATURES,
        "models": {},
    }
    pred_frames: list[pd.DataFrame] = []
    for spec in model_specs():
        spec.pipeline.fit(train[FEATURES], train[TARGET_LOG])
        pred_log = spec.pipeline.predict(val[FEATURES])
        metrics = metric_dict(val, pred_log)
        result["models"][spec.name] = {"family": spec.family, "metrics": metrics}
        pred_price = np.maximum(np.exp(pred_log), 1.0)
        actual_price = val[TARGET_PRICE].to_numpy(dtype=float)
        pred_frames.append(
            pd.DataFrame(
                {
                    "experiment_id": "T5-E004",
                    "model": spec.name,
                    "family": spec.family,
                    "split": "val_cold",
                    "artist_key": val["artist_key"].to_numpy(),
                    "artist_name_ko": val["artist_name_ko"].to_numpy(),
                    "actual_price_krw": actual_price,
                    "pred_log_price": pred_log,
                    "pred_price_krw": pred_price,
                    "ape": np.abs(pred_price - actual_price) / actual_price,
                }
            )
        )
    RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.concat(pred_frames, ignore_index=True).to_csv(PRED_PATH, index=False)
    print(RESULT_PATH)
    print(PRED_PATH)
    print(json.dumps(result["models"], ensure_ascii=False))


if __name__ == "__main__":
    main()
