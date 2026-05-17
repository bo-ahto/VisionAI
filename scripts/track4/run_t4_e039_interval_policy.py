#!/usr/bin/env python3
"""Run Track 4 E039 interval and confidence policy for final candidates."""
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
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO = Path(__file__).resolve().parents[2]
SPLIT_DIR = REPO / "data" / "track4_split"
RESULT_DIR = REPO / "data" / "track4" / "results"
PRED_DIR = REPO / "data" / "track4" / "predictions"
RESULT_PATH = RESULT_DIR / "t4_e039_interval_policy_metrics.json"
PRED_PATH = PRED_DIR / "t4_e039_interval_policy_predictions.csv"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"
TARGET_COVERAGES = [0.70, 0.80, 0.90]
MIN_GROUP_ROWS = 30


@dataclass(frozen=True)
class Candidate:
    name: str
    split_type: str
    model_name: str
    numeric: list[str]
    categorical: list[str]
    description: str


CANDIDATES = [
    Candidate(
        "warm_performance_artist_price_stats",
        "warm",
        "ridge",
        [
            "log_area",
            "aspect_ratio",
            "artist_works_log",
            "artist_works_count_train",
            "artist_train_median_log_price",
            "artist_train_mean_log_price",
            "artist_train_iqr_log_price",
        ],
        ["medium_category", "support_category", "artist_key"],
        "Warm 성능 최고 후보",
    ),
    Candidate(
        "warm_operational_artist_count",
        "warm",
        "ridge",
        ["log_area", "aspect_ratio", "artist_works_log", "artist_works_count_train"],
        ["medium_category", "support_category", "artist_key"],
        "Warm 운영 보수 후보",
    ),
    Candidate(
        "cold_full_size",
        "cold",
        "quantile",
        ["width_cm", "height_cm", "log_area", "aspect_ratio", "has_depth", "is_3d_candidate"],
        ["medium_category"],
        "Cold median APE 후보",
    ),
    Candidate(
        "cold_area_only",
        "cold",
        "quantile",
        ["log_area"],
        ["medium_category"],
        "Cold tail risk 비교 후보",
    ),
]


def onehot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def build_preprocessor(numeric: list[str], categorical: list[str]) -> ColumnTransformer:
    return ColumnTransformer(
        [
            (
                "numeric",
                Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]),
                numeric,
            ),
            (
                "categorical",
                Pipeline([("imputer", SimpleImputer(strategy="constant", fill_value="unknown")), ("onehot", onehot_encoder())]),
                categorical,
            ),
        ],
        remainder="drop",
    )


def build_model(candidate: Candidate) -> Pipeline:
    if candidate.model_name == "ridge":
        estimator = Ridge(alpha=10.0, random_state=42)
    elif candidate.model_name == "quantile":
        estimator = QuantileRegressor(quantile=0.5, alpha=0.0001, solver="highs")
    else:
        raise ValueError(candidate.model_name)
    return Pipeline([("preprocess", build_preprocessor(candidate.numeric, candidate.categorical)), ("model", estimator)])


def add_artist_train_stats(train: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    grouped = train.groupby("artist_key")[TARGET_LOG]
    stats = grouped.agg(["median", "mean", "count"]).rename(
        columns={"median": "artist_train_median_log_price", "mean": "artist_train_mean_log_price", "count": "artist_train_price_count"}
    )
    stats["artist_train_iqr_log_price"] = grouped.quantile(0.75) - grouped.quantile(0.25)
    out = out.merge(stats, left_on="artist_key", right_index=True, how="left")
    out["artist_train_median_log_price"] = out["artist_train_median_log_price"].fillna(float(train[TARGET_LOG].median()))
    out["artist_train_mean_log_price"] = out["artist_train_mean_log_price"].fillna(float(train[TARGET_LOG].mean()))
    out["artist_train_iqr_log_price"] = out["artist_train_iqr_log_price"].fillna(0.0)
    return out


def add_confidence_groups(train: pd.DataFrame, df: pd.DataFrame, split_type: str) -> pd.DataFrame:
    out = df.copy()
    if split_type == "warm":
        count = out["artist_works_count_train"].fillna(0)
        out["confidence_group"] = np.select([count < 5, count < 20], ["low_history", "mid_history"], default="high_history")
        out["confidence_score"] = np.where(count < 5, 2, np.where(count < 20, 1, 0))
    else:
        area_q90 = train["log_area"].quantile(0.90)
        flags = pd.DataFrame(index=out.index)
        flags["risk_3d"] = out["is_3d_candidate"].fillna(0).astype(int)
        flags["risk_support_unknown"] = (out["support_category"].fillna("unknown") == "unknown").astype(int)
        flags["risk_large_area"] = (out["log_area"] >= area_q90).astype(int)
        flags["risk_extreme_aspect"] = out["is_extreme_aspect_ratio"].fillna(0).astype(int)
        out["confidence_score"] = flags.sum(axis=1)
        out["confidence_group"] = np.where(out["confidence_score"] == 0, "low_risk", np.where(out["confidence_score"] == 1, "mid_risk", "high_risk"))
    return out


def price_from_log(values: np.ndarray) -> np.ndarray:
    return np.exp(values)


def fit_predict(candidate: Candidate, train: pd.DataFrame, df: pd.DataFrame) -> np.ndarray:
    features = candidate.categorical + candidate.numeric
    model = build_model(candidate)
    model.fit(train[features], train[TARGET_LOG])
    return model.predict(df[features])


def learn_quantiles(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, Any]:
    residual = np.abs(df[TARGET_LOG].to_numpy(dtype=float) - pred_log)
    out: dict[str, Any] = {}
    for coverage in TARGET_COVERAGES:
        key = f"q{int(coverage * 100)}"
        overall_q = float(np.quantile(residual, coverage))
        groups: dict[str, Any] = {}
        for group in sorted(df["confidence_group"].unique()):
            mask = df["confidence_group"].to_numpy() == group
            use_group = int(mask.sum()) >= MIN_GROUP_ROWS
            q = float(np.quantile(residual[mask], coverage)) if use_group else overall_q
            groups[group] = {
                "rows": int(mask.sum()),
                "abs_log_error": q,
                "half_width_multiplier": float(np.exp(q)),
                "full_range_multiplier": float(np.exp(2 * q)),
                "fallback_to_overall": not use_group,
            }
        out[key] = {
            "target_coverage": coverage,
            "overall": {
                "rows": int(len(df)),
                "abs_log_error": overall_q,
                "half_width_multiplier": float(np.exp(overall_q)),
                "full_range_multiplier": float(np.exp(2 * overall_q)),
            },
            "groups": groups,
        }
    return out


def apply_quantile_policy(df: pd.DataFrame, pred_log: np.ndarray, quantile_policy: dict[str, Any]) -> tuple[dict[str, Any], pd.DataFrame]:
    actual_log = df[TARGET_LOG].to_numpy(dtype=float)
    pred_price = np.maximum(price_from_log(pred_log), 1.0)
    rows = []
    summary: dict[str, Any] = {}
    for q_name, policy in quantile_policy.items():
        q_values = []
        for group in df["confidence_group"]:
            q_values.append(policy["groups"].get(group, policy["overall"])["abs_log_error"])
        q_arr = np.array(q_values, dtype=float)
        residual = np.abs(actual_log - pred_log)
        covered = residual <= q_arr
        lower = np.maximum(price_from_log(pred_log - q_arr), 1.0)
        upper = price_from_log(pred_log + q_arr)
        multiplier = upper / lower
        q_summary = {
            "target_coverage": policy["target_coverage"],
            "overall": {
                "rows": int(len(df)),
                "coverage": float(covered.mean()),
                "median_full_range_multiplier": float(np.median(multiplier)),
                "p90_full_range_multiplier": float(np.quantile(multiplier, 0.90)),
            },
            "groups": {},
        }
        for group in sorted(df["confidence_group"].unique()):
            mask = df["confidence_group"].to_numpy() == group
            q_summary["groups"][group] = {
                "rows": int(mask.sum()),
                "coverage": float(covered[mask].mean()),
                "median_full_range_multiplier": float(np.median(multiplier[mask])),
                "p90_full_range_multiplier": float(np.quantile(multiplier[mask], 0.90)),
            }
        summary[q_name] = q_summary
        frame = df[["artist_key", "artist_name_ko", "track4_source", "confidence_group", TARGET_PRICE]].copy()
        frame["quantile_policy"] = q_name
        frame["pred_log_price"] = pred_log
        frame["pred_price_krw"] = pred_price
        frame["range_lower_krw"] = lower
        frame["range_upper_krw"] = upper
        frame["covered"] = covered
        frame["range_full_multiplier"] = multiplier
        rows.append(frame)
    return summary, pd.concat(rows, ignore_index=True)


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


def run_candidate(candidate: Candidate, train: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame) -> tuple[dict[str, Any], pd.DataFrame]:
    val_pred = fit_predict(candidate, train, val_df)
    test_pred = fit_predict(candidate, train, test_df)
    policy = learn_quantiles(val_df, val_pred)
    interval_summary, pred_frame = apply_quantile_policy(test_df, test_pred, policy)
    pred_frame["experiment_id"] = "T4-E039"
    pred_frame["candidate"] = candidate.name
    result = {
        "description": candidate.description,
        "features": candidate.categorical + candidate.numeric,
        "point_metrics": {
            "validation": point_metrics(val_df, val_pred),
            "test": point_metrics(test_df, test_pred),
        },
        "validation_policy": policy,
        "test_interval_summary": interval_summary,
    }
    return result, pred_frame


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    train_raw = pd.read_csv(SPLIT_DIR / "track4_train.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    train = add_artist_train_stats(train_raw, train_raw)
    raw_splits = {
        "val_warm": pd.read_csv(SPLIT_DIR / "track4_val_warm.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True),
        "test_warm": pd.read_csv(SPLIT_DIR / "track4_test_warm.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True),
        "val_cold": pd.read_csv(SPLIT_DIR / "track4_val_cold.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True),
        "test_cold": pd.read_csv(SPLIT_DIR / "track4_test_cold.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True),
    }
    splits = {
        "val_warm": add_confidence_groups(train_raw, add_artist_train_stats(train_raw, raw_splits["val_warm"]), "warm"),
        "test_warm": add_confidence_groups(train_raw, add_artist_train_stats(train_raw, raw_splits["test_warm"]), "warm"),
        "val_cold": add_confidence_groups(train_raw, raw_splits["val_cold"], "cold"),
        "test_cold": add_confidence_groups(train_raw, raw_splits["test_cold"], "cold"),
    }
    results: dict[str, Any] = {
        "experiment_id": "T4-E039",
        "hypothesis_id": ["T4-H11", "T4-H24", "T4-H29"],
        "date": date.today().isoformat(),
        "target_coverages": TARGET_COVERAGES,
        "min_group_rows": MIN_GROUP_ROWS,
        "candidates": {},
    }
    frames = []
    for candidate in CANDIDATES:
        if candidate.split_type == "warm":
            result, pred_frame = run_candidate(candidate, train, splits["val_warm"], splits["test_warm"])
        else:
            result, pred_frame = run_candidate(candidate, train, splits["val_cold"], splits["test_cold"])
        results["candidates"][candidate.name] = result
        frames.append(pred_frame)
    RESULT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.concat(frames, ignore_index=True).to_csv(PRED_PATH, index=False)
    print(RESULT_PATH)
    print(PRED_PATH)


if __name__ == "__main__":
    main()
