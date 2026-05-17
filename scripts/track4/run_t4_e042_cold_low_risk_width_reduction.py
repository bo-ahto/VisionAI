#!/usr/bin/env python3
"""Search practical ways to reduce Cold low-risk interval width."""
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
from sklearn.linear_model import HuberRegressor, QuantileRegressor, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO = Path(__file__).resolve().parents[2]
SPLIT_DIR = REPO / "data" / "track4_split"
RESULT_DIR = REPO / "data" / "track4" / "results"
RESULT_PATH = RESULT_DIR / "t4_e042_cold_low_risk_width_reduction_metrics.json"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"
COVERAGES = [0.80, 0.85, 0.90]
BASELINE_COVERAGE = 0.783418553688824
BASELINE_RANGE = 5.540431493013646


@dataclass(frozen=True)
class Candidate:
    name: str
    model_name: str
    numeric: list[str]
    categorical: list[str]


CANDIDATES = [
    Candidate("quantile_full_size", "quantile", ["width_cm", "height_cm", "log_area", "aspect_ratio", "has_depth", "is_3d_candidate"], ["medium_category"]),
    Candidate("quantile_area_only", "quantile", ["log_area"], ["medium_category"]),
    Candidate("quantile_area_aspect", "quantile", ["log_area", "aspect_ratio"], ["medium_category"]),
    Candidate(
        "quantile_support_area_aspect",
        "quantile",
        ["log_area", "aspect_ratio"],
        ["medium_category", "support_category"],
    ),
    Candidate("huber_full_size", "huber", ["width_cm", "height_cm", "log_area", "aspect_ratio", "has_depth", "is_3d_candidate"], ["medium_category"]),
    Candidate("huber_area_aspect", "huber", ["log_area", "aspect_ratio"], ["medium_category"]),
    Candidate("ridge_full_size", "ridge", ["width_cm", "height_cm", "log_area", "aspect_ratio", "has_depth", "is_3d_candidate"], ["medium_category"]),
    Candidate("ridge_area_aspect", "ridge", ["log_area", "aspect_ratio"], ["medium_category"]),
]


def onehot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def build_model(candidate: Candidate) -> Pipeline:
    preprocessor = ColumnTransformer(
        [
            (
                "numeric",
                Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]),
                candidate.numeric,
            ),
            (
                "categorical",
                Pipeline([("imputer", SimpleImputer(strategy="constant", fill_value="unknown")), ("onehot", onehot_encoder())]),
                candidate.categorical,
            ),
        ],
        remainder="drop",
    )
    if candidate.model_name == "quantile":
        estimator = QuantileRegressor(quantile=0.5, alpha=0.0001, solver="highs")
    elif candidate.model_name == "huber":
        estimator = HuberRegressor(alpha=0.0001, epsilon=1.35, max_iter=1000)
    elif candidate.model_name == "ridge":
        estimator = Ridge(alpha=10.0, random_state=42)
    else:
        raise ValueError(candidate.model_name)
    return Pipeline([("preprocess", preprocessor), ("model", estimator)])


def add_risk_groups(train: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    area_q90 = train["log_area"].quantile(0.90)
    flags = pd.DataFrame(index=out.index)
    flags["risk_3d"] = out["is_3d_candidate"].fillna(0).astype(int)
    flags["risk_support_unknown"] = (out["support_category"].fillna("unknown") == "unknown").astype(int)
    flags["risk_large_area"] = (out["log_area"] >= area_q90).astype(int)
    flags["risk_extreme_aspect"] = out["is_extreme_aspect_ratio"].fillna(0).astype(int)
    out["confidence_score"] = flags.sum(axis=1)
    out["confidence_group"] = np.where(
        out["confidence_score"] == 0,
        "low_risk",
        np.where(out["confidence_score"] == 1, "mid_risk", "high_risk"),
    )
    return out


def price_from_log(values: np.ndarray) -> np.ndarray:
    return np.exp(values)


def point_metrics(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, Any]:
    y_price = df[TARGET_PRICE].to_numpy(dtype=float)
    pred_price = np.maximum(price_from_log(pred_log), 1.0)
    ape = np.abs(pred_price - y_price) / y_price
    return {
        "rows": int(len(df)),
        "median_ape": float(np.median(ape)),
        "p95_ape": float(np.quantile(ape, 0.95)),
        "within_30": float(np.mean(ape <= 0.30)),
        "within_50": float(np.mean(ape <= 0.50)),
    }


def interval_metrics(val_df: pd.DataFrame, val_pred: np.ndarray, test_df: pd.DataFrame, test_pred: np.ndarray) -> dict[str, Any]:
    val_residual = np.abs(val_df[TARGET_LOG].to_numpy(dtype=float) - val_pred)
    test_residual = np.abs(test_df[TARGET_LOG].to_numpy(dtype=float) - test_pred)
    out: dict[str, Any] = {}
    for coverage in COVERAGES:
        q_name = f"q{int(coverage * 100)}"
        q = float(np.quantile(val_residual, coverage))
        covered = test_residual <= q
        full_range = float(np.exp(2 * q))
        out[q_name] = {
            "target_coverage": coverage,
            "validation_abs_log_error": q,
            "test_coverage": float(covered.mean()),
            "full_range_multiplier": full_range,
            "range_reduction_vs_baseline": float((BASELINE_RANGE - full_range) / BASELINE_RANGE),
            "coverage_delta_vs_baseline": float(covered.mean() - BASELINE_COVERAGE),
        }
    return out


def train_scope_metrics(candidate: Candidate, train: pd.DataFrame, val_low: pd.DataFrame, test_low: pd.DataFrame, scope_name: str) -> dict[str, Any]:
    features = candidate.categorical + candidate.numeric
    model = build_model(candidate)
    model.fit(train[features], train[TARGET_LOG])
    val_pred = model.predict(val_low[features])
    test_pred = model.predict(test_low[features])
    intervals = interval_metrics(val_low, val_pred, test_low, test_pred)
    q90 = intervals["q90"]
    practical = q90["test_coverage"] >= BASELINE_COVERAGE and q90["full_range_multiplier"] < BASELINE_RANGE
    return {
        "train_scope": scope_name,
        "features": features,
        "point_metrics": point_metrics(test_low, test_pred),
        "interval_metrics": intervals,
        "practical_improvement": bool(practical),
        "decision": "improved_candidate" if practical else "not_improved",
    }


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    train_raw = pd.read_csv(SPLIT_DIR / "track4_train.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    val_cold = pd.read_csv(SPLIT_DIR / "track4_val_cold.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    test_cold = pd.read_csv(SPLIT_DIR / "track4_test_cold.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)

    train_risk = add_risk_groups(train_raw, train_raw)
    val_risk = add_risk_groups(train_raw, val_cold)
    test_risk = add_risk_groups(train_raw, test_cold)
    train_low = train_risk[train_risk["confidence_group"] == "low_risk"].reset_index(drop=True)
    val_low = val_risk[val_risk["confidence_group"] == "low_risk"].reset_index(drop=True)
    test_low = test_risk[test_risk["confidence_group"] == "low_risk"].reset_index(drop=True)

    results: dict[str, Any] = {
        "experiment_id": "T4-E042",
        "hypothesis_id": ["T4-H33"],
        "date": date.today().isoformat(),
        "baseline": {
            "source": "T4-E040 cold_full_size low_risk q90",
            "coverage": BASELINE_COVERAGE,
            "full_range_multiplier": BASELINE_RANGE,
        },
        "row_counts": {
            "train_all": int(len(train_raw)),
            "train_low_risk": int(len(train_low)),
            "val_low_risk": int(len(val_low)),
            "test_low_risk": int(len(test_low)),
        },
        "candidates": {},
    }
    for candidate in CANDIDATES:
        results["candidates"][f"{candidate.name}__train_all"] = train_scope_metrics(candidate, train_raw, val_low, test_low, "train_all")
        results["candidates"][f"{candidate.name}__train_low_risk"] = train_scope_metrics(candidate, train_low, val_low, test_low, "train_low_risk")

    improved = [
        {"candidate": name, **value["interval_metrics"]["q90"], "median_ape": value["point_metrics"]["median_ape"]}
        for name, value in results["candidates"].items()
        if value["practical_improvement"]
    ]
    improved.sort(key=lambda item: (item["full_range_multiplier"], -item["test_coverage"]))
    results["improved_candidates"] = improved
    results["conclusion"] = (
        "improved_candidate_found"
        if improved
        else "no_candidate_reduced_width_without_losing_baseline_coverage"
    )
    RESULT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(RESULT_PATH)


if __name__ == "__main__":
    main()
