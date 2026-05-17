#!/usr/bin/env python3
"""Run Track 4 E027 2D/3D depth feature and fallback experiment."""
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
RESULT_PATH = RESULT_DIR / "t4_e027_3d_depth_slice_metrics.json"
PRED_PATH = PRED_DIR / "t4_e027_3d_depth_slice_predictions.csv"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"

BASE_NUMERIC = ["log_area", "aspect_ratio"]
BASE_CATEGORICAL = ["medium_category"]
DEPTH_NUMERIC = ["log_area", "aspect_ratio", "depth_cm_filled", "log_volume", "longest_edge_cm"]
WARM_EXTRA_NUMERIC = ["artist_works_log", "artist_works_count_train"]
WARM_EXTRA_CATEGORICAL = ["artist_key", "support_category"]

FORBIDDEN_FEATURE_PATTERNS = [
    "source",
    "url",
    "image",
    "gallery",
    "tier",
    "price_krw",
    "ln_price",
]


@dataclass(frozen=True)
class Strategy:
    name: str
    description: str
    depth_features: bool
    conditional: bool


STRATEGIES = [
    Strategy("base_no_depth", "2D/3D 공통 기본 크기 피처만 사용", False, False),
    Strategy("global_depth_features", "depth/volume/longest edge를 전체 작품에 일괄 적용", True, False),
    Strategy("conditional_3d_fallback", "2D는 기본 모델, 3D는 depth 피처 모델로 조건부 예측", True, True),
]


def onehot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def validate_features(columns: list[str]) -> None:
    lower_cols = [col.lower() for col in columns]
    violations = [
        col
        for col, lower in zip(columns, lower_cols)
        if any(pattern in lower for pattern in FORBIDDEN_FEATURE_PATTERNS)
    ]
    if violations:
        raise ValueError(f"Forbidden features included: {violations}")


def add_3d_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    width = out["width_cm"].fillna(0).clip(lower=0)
    height = out["height_cm"].fillna(0).clip(lower=0)
    depth = out["depth_cm"].fillna(0).clip(lower=0)
    depth_for_volume = depth.where(depth > 0, 1.0)
    out["depth_cm_filled"] = depth
    out["log_volume"] = np.log1p(width * height * depth_for_volume)
    out["longest_edge_cm"] = pd.concat([width, height, depth], axis=1).max(axis=1)
    return out


def build_preprocessor(numeric: list[str], categorical: list[str]) -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
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


def build_model(model_family: str, numeric: list[str], categorical: list[str]) -> Pipeline:
    if model_family == "warm_ridge":
        model = Ridge(alpha=10.0, random_state=42)
    elif model_family == "cold_quantile":
        model = QuantileRegressor(quantile=0.5, alpha=0.0001, solver="highs")
    else:
        raise ValueError(model_family)
    return Pipeline([("preprocess", build_preprocessor(numeric, categorical)), ("model", model)])


def feature_policy(split_name: str, depth_features: bool) -> tuple[list[str], list[str]]:
    numeric = DEPTH_NUMERIC.copy() if depth_features else BASE_NUMERIC.copy()
    categorical = BASE_CATEGORICAL.copy()
    if split_name == "warm":
        numeric += WARM_EXTRA_NUMERIC
        categorical += WARM_EXTRA_CATEGORICAL
    return numeric, categorical


def price_from_log(values: np.ndarray) -> np.ndarray:
    return np.exp(values)


def metrics(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    y_log = df[TARGET_LOG].to_numpy(dtype=float)
    y_price = df[TARGET_PRICE].to_numpy(dtype=float)
    pred_price = np.maximum(price_from_log(pred_log), 1.0)
    ape = np.abs(pred_price - y_price) / y_price
    return {
        "rows": int(len(df)),
        "median_ape": float(np.median(ape)) if len(ape) else None,
        "mape": float(np.mean(ape)) if len(ape) else None,
        "rmse_log": float(np.sqrt(mean_squared_error(y_log, pred_log))) if len(ape) else None,
        "within_30": float(np.mean(ape <= 0.30)) if len(ape) else None,
        "within_50": float(np.mean(ape <= 0.50)) if len(ape) else None,
        "p95_ape": float(np.quantile(ape, 0.95)) if len(ape) else None,
    }


def slice_metrics(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {"overall": metrics(df, pred_log)}
    is_3d = df["is_3d_candidate"].astype(bool).to_numpy()
    for name, mask in [("2d", ~is_3d), ("3d", is_3d)]:
        if mask.sum() == 0:
            out[name] = {"rows": 0, "median_ape": None, "p95_ape": None}
        else:
            out[name] = metrics(df.loc[mask], pred_log[mask])
    return out


def fit_predict_regular(
    train: pd.DataFrame,
    eval_df: pd.DataFrame,
    split_name: str,
    strategy: Strategy,
) -> tuple[np.ndarray, list[str]]:
    numeric, categorical = feature_policy(split_name, strategy.depth_features)
    features = categorical + numeric
    validate_features(features)
    model_family = "warm_ridge" if split_name == "warm" else "cold_quantile"
    model = build_model(model_family, numeric, categorical)
    model.fit(train[features], train[TARGET_LOG])
    return model.predict(eval_df[features]), features


def fit_predict_conditional(
    train: pd.DataFrame,
    eval_df: pd.DataFrame,
    split_name: str,
) -> tuple[np.ndarray, dict[str, list[str]]]:
    model_family = "warm_ridge" if split_name == "warm" else "cold_quantile"
    is_train_3d = train["is_3d_candidate"].astype(bool)
    is_eval_3d = eval_df["is_3d_candidate"].astype(bool).to_numpy()

    base_numeric, base_categorical = feature_policy(split_name, depth_features=False)
    depth_numeric, depth_categorical = feature_policy(split_name, depth_features=True)
    base_features = base_categorical + base_numeric
    depth_features = depth_categorical + depth_numeric
    validate_features(base_features)
    validate_features(depth_features)

    base_model = build_model(model_family, base_numeric, base_categorical)
    depth_model = build_model(model_family, depth_numeric, depth_categorical)
    base_model.fit(train.loc[~is_train_3d, base_features], train.loc[~is_train_3d, TARGET_LOG])
    depth_model.fit(train.loc[is_train_3d, depth_features], train.loc[is_train_3d, TARGET_LOG])

    pred = np.empty(len(eval_df), dtype=float)
    if (~is_eval_3d).sum():
        pred[~is_eval_3d] = base_model.predict(eval_df.loc[~is_eval_3d, base_features])
    if is_eval_3d.sum():
        pred[is_eval_3d] = depth_model.predict(eval_df.loc[is_eval_3d, depth_features])
    return pred, {"base_features": base_features, "depth_features": depth_features}


def summarize_split(df: pd.DataFrame) -> dict[str, Any]:
    return {
        "rows": int(len(df)),
        "artists": int(df["artist_key"].nunique()),
        "3d_rows": int(df["is_3d_candidate"].sum()),
        "depth_positive_rows": int((df["depth_cm"].fillna(0) > 0).sum()),
    }


def run_strategy(train: pd.DataFrame, eval_df: pd.DataFrame, split_name: str, strategy: Strategy) -> tuple[dict[str, Any], pd.DataFrame]:
    if strategy.conditional:
        pred_log, features = fit_predict_conditional(train, eval_df, split_name)
    else:
        pred_log, features = fit_predict_regular(train, eval_df, split_name, strategy)
    pred_price = price_from_log(pred_log)
    ape = np.abs(pred_price - eval_df[TARGET_PRICE].to_numpy(dtype=float)) / eval_df[TARGET_PRICE].to_numpy(dtype=float)
    pred_df = pd.DataFrame(
        {
            "experiment_id": "T4-E027",
            "split": f"val_{split_name}",
            "strategy": strategy.name,
            "actual_price_krw": eval_df[TARGET_PRICE].to_numpy(dtype=float),
            "pred_log_price": pred_log,
            "pred_price_krw": pred_price,
            "ape": ape,
            "is_3d_candidate": eval_df["is_3d_candidate"].to_numpy(),
            "depth_cm": eval_df["depth_cm"].to_numpy(),
            "medium_category": eval_df["medium_category"].to_numpy(),
        }
    )
    return {
        "description": strategy.description,
        "features": features,
        "slice_metrics": slice_metrics(eval_df, pred_log),
    }, pred_df


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)

    train = add_3d_features(pd.read_csv(SPLIT_DIR / "track4_train.csv")).dropna(subset=[TARGET_LOG, TARGET_PRICE])
    val_warm = add_3d_features(pd.read_csv(SPLIT_DIR / "track4_val_warm.csv")).dropna(subset=[TARGET_LOG, TARGET_PRICE])
    val_cold = add_3d_features(pd.read_csv(SPLIT_DIR / "track4_val_cold.csv")).dropna(subset=[TARGET_LOG, TARGET_PRICE])

    results: dict[str, Any] = {
        "experiment_id": "T4-E027",
        "hypothesis_id": ["T4-H8", "T4-H16", "T4-H27"],
        "date": date.today().isoformat(),
        "target": TARGET_LOG,
        "warm_model": "ridge",
        "cold_model": "quantile_median",
        "splits": {
            "train": summarize_split(train),
            "val_warm": summarize_split(val_warm),
            "val_cold": summarize_split(val_cold),
        },
        "strategies": {},
    }
    pred_frames: list[pd.DataFrame] = []
    for strategy in STRATEGIES:
        warm_result, warm_pred = run_strategy(train, val_warm, "warm", strategy)
        cold_result, cold_pred = run_strategy(train, val_cold, "cold", strategy)
        results["strategies"][strategy.name] = {
            "warm": warm_result,
            "cold": cold_result,
        }
        pred_frames.extend([warm_pred, cold_pred])

    RESULT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.concat(pred_frames, ignore_index=True).to_csv(PRED_PATH, index=False)
    print(RESULT_PATH)
    print(PRED_PATH)


if __name__ == "__main__":
    main()
