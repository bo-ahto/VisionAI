#!/usr/bin/env python3
"""Compare Warm final feature set across linear and nonlinear models."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from lightgbm import LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBRegressor


REPO = Path(__file__).resolve().parents[2]
SPLIT_DIR = REPO / "data" / "track4_split"
RESULT_DIR = REPO / "data" / "track4" / "results"
PRED_DIR = REPO / "data" / "track4" / "predictions"
RESULT_PATH = RESULT_DIR / "t4_e047_warm_nonlinear_model_comparison_metrics.json"
PRED_PATH = PRED_DIR / "t4_e047_warm_nonlinear_model_comparison_predictions.csv"

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
CONDITIONAL_PRICE_STATS = [
    "artist_train_median_log_price",
    "artist_train_mean_log_price",
    "artist_train_iqr_log_price",
]


@dataclass(frozen=True)
class ModelSpec:
    name: str
    model_type: str
    pipeline: Pipeline


def onehot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def build_preprocessor(scale_numeric: bool) -> ColumnTransformer:
    numeric_steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
    if scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))
    numeric = Pipeline(numeric_steps)
    categorical = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="constant", fill_value="unknown")),
            ("onehot", onehot_encoder()),
        ]
    )
    return ColumnTransformer(
        [
            ("numeric", numeric, NUMERIC_FEATURES),
            ("categorical", categorical, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )


def build_specs(seed: int) -> list[ModelSpec]:
    return [
        ModelSpec(
            "ridge",
            "linear",
            Pipeline([("preprocess", build_preprocessor(scale_numeric=True)), ("model", Ridge(alpha=10.0, random_state=seed))]),
        ),
        ModelSpec(
            "hist_gradient_boosting",
            "tree",
            Pipeline(
                [
                    ("preprocess", build_preprocessor(scale_numeric=False)),
                    (
                        "model",
                        HistGradientBoostingRegressor(
                            loss="squared_error",
                            max_iter=220,
                            learning_rate=0.04,
                            l2_regularization=0.1,
                            random_state=seed,
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
                    ("preprocess", build_preprocessor(scale_numeric=False)),
                    (
                        "model",
                        RandomForestRegressor(
                            n_estimators=260,
                            min_samples_leaf=8,
                            max_features=0.75,
                            random_state=seed,
                            n_jobs=-1,
                        ),
                    ),
                ]
            ),
        ),
        ModelSpec(
            "lightgbm",
            "tree",
            Pipeline(
                [
                    ("preprocess", build_preprocessor(scale_numeric=False)),
                    (
                        "model",
                        LGBMRegressor(
                            objective="regression",
                            n_estimators=320,
                            learning_rate=0.03,
                            num_leaves=24,
                            min_child_samples=20,
                            subsample=0.85,
                            colsample_bytree=0.85,
                            reg_lambda=3.0,
                            random_state=seed,
                            verbosity=-1,
                        ),
                    ),
                ]
            ),
        ),
        ModelSpec(
            "xgboost",
            "tree",
            Pipeline(
                [
                    ("preprocess", build_preprocessor(scale_numeric=False)),
                    (
                        "model",
                        XGBRegressor(
                            objective="reg:squarederror",
                            n_estimators=320,
                            learning_rate=0.03,
                            max_depth=4,
                            min_child_weight=8,
                            subsample=0.85,
                            colsample_bytree=0.85,
                            reg_lambda=3.0,
                            random_state=seed,
                            n_jobs=1,
                            verbosity=0,
                        ),
                    ),
                ]
            ),
        ),
        ModelSpec(
            "catboost",
            "tree",
            Pipeline(
                [
                    ("preprocess", build_preprocessor(scale_numeric=False)),
                    (
                        "model",
                        CatBoostRegressor(
                            loss_function="RMSE",
                            iterations=320,
                            learning_rate=0.03,
                            depth=5,
                            l2_leaf_reg=6.0,
                            random_seed=seed,
                            verbose=False,
                        ),
                    ),
                ]
            ),
        ),
    ]


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


def metric_dict(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
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


def group_metrics(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for group in sorted(df["history_group"].unique()):
        mask = df["history_group"].to_numpy() == group
        out[group] = metric_dict(df.loc[mask], pred_log[mask])
    return out


def validate_features(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame) -> None:
    missing = sorted(set(FEATURES) - (set(train.columns) & set(val.columns) & set(test.columns)))
    if missing:
        raise ValueError(f"Missing required features: {missing}")


def evaluate_model(spec: ModelSpec, train: pd.DataFrame, eval_df: pd.DataFrame) -> tuple[dict[str, Any], np.ndarray]:
    spec.pipeline.fit(train[FEATURES], train[TARGET_LOG])
    pred_log = spec.pipeline.predict(eval_df[FEATURES])
    return {
        "model_type": spec.model_type,
        "metrics": metric_dict(eval_df, pred_log),
        "history_groups": group_metrics(eval_df, pred_log),
    }, pred_log


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)

    train_raw = pd.read_csv(SPLIT_DIR / "track4_train.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    val_raw = pd.read_csv(SPLIT_DIR / "track4_val_warm.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    test_raw = pd.read_csv(SPLIT_DIR / "track4_test_warm.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    train = add_history_group(add_artist_train_stats(train_raw, train_raw))
    val = add_history_group(add_artist_train_stats(train_raw, val_raw))
    test = add_history_group(add_artist_train_stats(train_raw, test_raw))
    validate_features(train, val, test)

    seeds = [42, 2026, 777]
    results: dict[str, Any] = {
        "experiment_id": "T4-E047",
        "hypothesis_id": "T4-H36",
        "date": date.today().isoformat(),
        "target": TARGET_LOG,
        "features": FEATURES,
        "conditional_price_stats": CONDITIONAL_PRICE_STATS,
        "splits": {
            "train_rows": int(len(train)),
            "val_warm_rows": int(len(val)),
            "test_warm_rows": int(len(test)),
        },
        "models": {},
    }
    pred_frames: list[pd.DataFrame] = []

    for seed in seeds:
        for spec in build_specs(seed):
            model_key = spec.name
            if model_key not in results["models"]:
                results["models"][model_key] = {"model_type": spec.model_type, "runs": []}
            val_result, val_pred = evaluate_model(spec, train, val)
            test_result, test_pred = evaluate_model(spec, train, test)
            run_result = {
                "seed": seed,
                "val_warm": val_result,
                "test_warm": test_result,
            }
            results["models"][model_key]["runs"].append(run_result)
            for split_name, eval_df, pred_log in [("val_warm", val, val_pred), ("test_warm", test, test_pred)]:
                pred_price = np.maximum(np.exp(pred_log), 1.0)
                actual_price = eval_df[TARGET_PRICE].to_numpy(dtype=float)
                pred_frames.append(
                    pd.DataFrame(
                        {
                            "experiment_id": "T4-E047",
                            "seed": seed,
                            "model": model_key,
                            "model_type": spec.model_type,
                            "split": split_name,
                            "artist_key": eval_df["artist_key"].to_numpy(),
                            "artist_name_ko": eval_df["artist_name_ko"].to_numpy(),
                            "history_group": eval_df["history_group"].to_numpy(),
                            "actual_price_krw": actual_price,
                            "pred_log_price": pred_log,
                            "pred_price_krw": pred_price,
                            "ape": np.abs(pred_price - actual_price) / actual_price,
                        }
                    )
                )

    summary: dict[str, Any] = {}
    for model_name, model_result in results["models"].items():
        runs = model_result["runs"]
        for split in ["val_warm", "test_warm"]:
            medians = [run[split]["metrics"]["median_ape"] for run in runs]
            p95s = [run[split]["metrics"]["p95_ape"] for run in runs]
            summary.setdefault(model_name, {})[split] = {
                "median_ape_mean": float(np.mean(medians)),
                "median_ape_std": float(np.std(medians)),
                "median_ape_min": float(np.min(medians)),
                "p95_ape_mean": float(np.mean(p95s)),
                "p95_ape_std": float(np.std(p95s)),
                "p95_ape_min": float(np.min(p95s)),
            }
    best_test_model = min(summary, key=lambda name: (summary[name]["test_warm"]["median_ape_mean"], summary[name]["test_warm"]["p95_ape_mean"]))
    ridge_test = summary["ridge"]["test_warm"]
    best_test = summary[best_test_model]["test_warm"]
    results["summary"] = summary
    results["best_test_model"] = best_test_model
    results["recommendation"] = {
        "replace_ridge": bool(
            best_test_model != "ridge"
            and best_test["median_ape_mean"] + 0.005 < ridge_test["median_ape_mean"]
            and best_test["p95_ape_mean"] <= ridge_test["p95_ape_mean"] * 1.05
        ),
        "reason": "Ridge 대비 test median APE 개선과 p95 안정성을 함께 확인해 교체 여부를 판단한다.",
    }

    RESULT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.concat(pred_frames, ignore_index=True).to_csv(PRED_PATH, index=False)
    print(RESULT_PATH)
    print(PRED_PATH)
    print(
        json.dumps(
            {
                "best_test_model": best_test_model,
                "replace_ridge": results["recommendation"]["replace_ridge"],
                "ridge_test_median_mean": ridge_test["median_ape_mean"],
                "best_test_median_mean": best_test["median_ape_mean"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
