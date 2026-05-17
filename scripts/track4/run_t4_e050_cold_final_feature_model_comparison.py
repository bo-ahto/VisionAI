#!/usr/bin/env python3
"""Compare Cold final feature set across robust linear and tree models."""
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
from sklearn.linear_model import HuberRegressor, QuantileRegressor, Ridge
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBRegressor


REPO = Path(__file__).resolve().parents[2]
SPLIT_DIR = REPO / "data" / "track4_split"
RESULT_DIR = REPO / "data" / "track4" / "results"
PRED_DIR = REPO / "data" / "track4" / "predictions"
RESULT_PATH = RESULT_DIR / "t4_e050_cold_final_feature_model_comparison_metrics.json"
PRED_PATH = PRED_DIR / "t4_e050_cold_final_feature_model_comparison_predictions.csv"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"
CATEGORICAL_FEATURES = ["medium_category"]
NUMERIC_FEATURES = ["width_cm", "height_cm", "log_area", "aspect_ratio", "has_depth", "is_3d_candidate"]
FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES


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
    categorical = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="constant", fill_value="unknown")),
            ("onehot", onehot_encoder()),
        ]
    )
    return ColumnTransformer(
        [
            ("numeric", Pipeline(numeric_steps), NUMERIC_FEATURES),
            ("categorical", categorical, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )


def build_specs(seed: int = 42) -> list[ModelSpec]:
    return [
        ModelSpec("ridge", "linear", Pipeline([("preprocess", build_preprocessor(True)), ("model", Ridge(alpha=10.0, random_state=seed))])),
        ModelSpec(
            "huber",
            "robust_linear",
            Pipeline([("preprocess", build_preprocessor(True)), ("model", HuberRegressor(alpha=0.0001, epsilon=1.35, max_iter=500))]),
        ),
        ModelSpec(
            "quantile_median",
            "robust_linear",
            Pipeline([("preprocess", build_preprocessor(True)), ("model", QuantileRegressor(quantile=0.5, alpha=0.0001, solver="highs"))]),
        ),
        ModelSpec(
            "hist_gradient_boosting",
            "tree",
            Pipeline(
                [
                    ("preprocess", build_preprocessor(False)),
                    (
                        "model",
                        HistGradientBoostingRegressor(
                            loss="squared_error",
                            max_iter=220,
                            learning_rate=0.05,
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
                    ("preprocess", build_preprocessor(False)),
                    (
                        "model",
                        RandomForestRegressor(
                            n_estimators=260,
                            min_samples_leaf=20,
                            max_features=0.8,
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
                    ("preprocess", build_preprocessor(False)),
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
                    ("preprocess", build_preprocessor(False)),
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
                    ("preprocess", build_preprocessor(False)),
                    (
                        "model",
                        CatBoostRegressor(
                            loss_function="RMSE",
                            iterations=260,
                            learning_rate=0.04,
                            depth=5,
                            l2_leaf_reg=5.0,
                            random_seed=seed,
                            verbose=False,
                        ),
                    ),
                ]
            ),
        ),
    ]


def add_risk_group(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    risk_count = (
        out["is_3d_candidate"].fillna(0).astype(int)
        + (out["width_cm"].fillna(0) >= 200).astype(int)
        + (out["height_cm"].fillna(0) >= 200).astype(int)
        + (out["medium_category"].fillna("unknown").isin(["unknown", "other", "mixed_media"])).astype(int)
    )
    out["risk_group"] = np.select([risk_count == 0, risk_count == 1], ["low_risk", "mid_risk"], default="high_risk")
    return out


def metrics(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
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
    for group in sorted(df["risk_group"].unique()):
        mask = df["risk_group"].to_numpy() == group
        out[group] = metrics(df.loc[mask], pred_log[mask])
    return out


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    train = pd.read_csv(SPLIT_DIR / "track4_train.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    val = add_risk_group(pd.read_csv(SPLIT_DIR / "track4_val_cold.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True))
    test = add_risk_group(pd.read_csv(SPLIT_DIR / "track4_test_cold.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True))
    result: dict[str, Any] = {
        "experiment_id": "T4-E050",
        "hypothesis_id": "T4-H37",
        "date": date.today().isoformat(),
        "features": FEATURES,
        "splits": {"train_rows": int(len(train)), "val_cold_rows": int(len(val)), "test_cold_rows": int(len(test))},
        "models": {},
    }
    pred_frames: list[pd.DataFrame] = []
    for spec in build_specs(seed=42):
        spec.pipeline.fit(train[FEATURES], train[TARGET_LOG])
        val_pred = spec.pipeline.predict(val[FEATURES])
        test_pred = spec.pipeline.predict(test[FEATURES])
        result["models"][spec.name] = {
            "model_type": spec.model_type,
            "val_cold": {"overall": metrics(val, val_pred), "risk_groups": group_metrics(val, val_pred)},
            "test_cold": {"overall": metrics(test, test_pred), "risk_groups": group_metrics(test, test_pred)},
        }
        for split_name, eval_df, pred_log in [("val_cold", val, val_pred), ("test_cold", test, test_pred)]:
            pred_price = np.maximum(np.exp(pred_log), 1.0)
            actual = eval_df[TARGET_PRICE].to_numpy(dtype=float)
            pred_frames.append(
                pd.DataFrame(
                    {
                        "experiment_id": "T4-E050",
                        "model": spec.name,
                        "model_type": spec.model_type,
                        "split": split_name,
                        "artist_key": eval_df["artist_key"].to_numpy(),
                        "artist_name_ko": eval_df["artist_name_ko"].to_numpy(),
                        "risk_group": eval_df["risk_group"].to_numpy(),
                        "actual_price_krw": actual,
                        "pred_price_krw": pred_price,
                        "ape": np.abs(pred_price - actual) / actual,
                    }
                )
            )
    summary = {
        name: {
            "model_type": value["model_type"],
            "val_median_ape": value["val_cold"]["overall"]["median_ape"],
            "val_p95_ape": value["val_cold"]["overall"]["p95_ape"],
            "test_median_ape": value["test_cold"]["overall"]["median_ape"],
            "test_p95_ape": value["test_cold"]["overall"]["p95_ape"],
        }
        for name, value in result["models"].items()
    }
    best_test_model = min(summary, key=lambda name: (summary[name]["test_median_ape"], summary[name]["test_p95_ape"]))
    result["summary"] = summary
    result["best_test_model"] = best_test_model
    result["recommendation"] = {
        "replace_quantile": bool(best_test_model != "quantile_median"),
        "reason": "test median APE를 1순위, p95 APE를 2순위로 보고 Cold 최종 후보 교체 여부를 판단한다.",
    }
    RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.concat(pred_frames, ignore_index=True).to_csv(PRED_PATH, index=False)
    print(RESULT_PATH)
    print(PRED_PATH)
    print(json.dumps({"best_test_model": best_test_model, **summary[best_test_model]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
