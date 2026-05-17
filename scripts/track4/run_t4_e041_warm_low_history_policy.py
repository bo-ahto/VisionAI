#!/usr/bin/env python3
"""Validate Warm low-history confidence and interval policy in Track 4."""
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
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO = Path(__file__).resolve().parents[2]
SPLIT_DIR = REPO / "data" / "track4_split"
RESULT_DIR = REPO / "data" / "track4" / "results"
PRED_DIR = REPO / "data" / "track4" / "predictions"
RESULT_PATH = RESULT_DIR / "t4_e041_warm_low_history_policy_metrics.json"
PRED_PATH = PRED_DIR / "t4_e041_warm_low_history_policy_predictions.csv"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"
TARGET_COVERAGES = [0.70, 0.80, 0.90]
MIN_GROUP_ROWS = 30

Q80_MIN_COVERAGE = 0.80
Q80_MAX_RANGE = 4.0
LOW_HISTORY_Q90_MIN_COVERAGE = 0.80
LOW_HISTORY_Q90_MAX_RANGE = 5.5


@dataclass(frozen=True)
class Candidate:
    name: str
    numeric: list[str]
    categorical: list[str]
    description: str


CANDIDATES = [
    Candidate(
        "warm_performance_artist_price_stats",
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
        "Warm 성능 후보",
    ),
    Candidate(
        "warm_operational_artist_count",
        ["log_area", "aspect_ratio", "artist_works_log", "artist_works_count_train"],
        ["medium_category", "support_category", "artist_key"],
        "Warm 운영 보수 후보",
    ),
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
    return Pipeline([("preprocess", preprocessor), ("model", Ridge(alpha=10.0, random_state=42))])


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


def add_warm_history_groups(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    count = out["artist_works_count_train"].fillna(0)
    out["history_group"] = np.select([count < 5, count < 20], ["low_history", "mid_history"], default="high_history")
    out["history_score"] = np.where(count < 5, 2, np.where(count < 20, 1, 0))
    return out


def fit_predict(candidate: Candidate, train: pd.DataFrame, df: pd.DataFrame) -> np.ndarray:
    features = candidate.categorical + candidate.numeric
    model = build_model(candidate)
    model.fit(train[features], train[TARGET_LOG])
    return model.predict(df[features])


def price_from_log(values: np.ndarray) -> np.ndarray:
    return np.exp(values)


def point_metrics(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, Any]:
    actual_price = df[TARGET_PRICE].to_numpy(dtype=float)
    pred_price = np.maximum(price_from_log(pred_log), 1.0)
    ape = np.abs(pred_price - actual_price) / actual_price
    return {
        "rows": int(len(df)),
        "median_ape": float(np.median(ape)),
        "p95_ape": float(np.quantile(ape, 0.95)),
        "within_30": float(np.mean(ape <= 0.30)),
        "within_50": float(np.mean(ape <= 0.50)),
    }


def grouped_point_metrics(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for group in sorted(df["history_group"].unique()):
        mask = df["history_group"].to_numpy() == group
        out[group] = point_metrics(df.loc[mask], pred_log[mask])
    return out


def learn_group_quantiles(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, Any]:
    residual = np.abs(df[TARGET_LOG].to_numpy(dtype=float) - pred_log)
    policy: dict[str, Any] = {}
    for coverage in TARGET_COVERAGES:
        q_name = f"q{int(coverage * 100)}"
        overall_q = float(np.quantile(residual, coverage))
        groups: dict[str, Any] = {}
        for group in sorted(df["history_group"].unique()):
            mask = df["history_group"].to_numpy() == group
            use_group = int(mask.sum()) >= MIN_GROUP_ROWS
            q = float(np.quantile(residual[mask], coverage)) if use_group else overall_q
            groups[group] = {
                "rows": int(mask.sum()),
                "abs_log_error": q,
                "half_width_multiplier": float(np.exp(q)),
                "full_range_multiplier": float(np.exp(2 * q)),
                "fallback_to_overall": not use_group,
            }
        policy[q_name] = {
            "target_coverage": coverage,
            "overall": {
                "rows": int(len(df)),
                "abs_log_error": overall_q,
                "half_width_multiplier": float(np.exp(overall_q)),
                "full_range_multiplier": float(np.exp(2 * overall_q)),
            },
            "groups": groups,
        }
    return policy


def apply_policy(df: pd.DataFrame, pred_log: np.ndarray, policy: dict[str, Any]) -> tuple[dict[str, Any], pd.DataFrame]:
    actual_log = df[TARGET_LOG].to_numpy(dtype=float)
    pred_price = np.maximum(price_from_log(pred_log), 1.0)
    summaries: dict[str, Any] = {}
    frames = []
    for q_name, q_policy in policy.items():
        q_values = np.array(
            [q_policy["groups"].get(group, q_policy["overall"])["abs_log_error"] for group in df["history_group"]],
            dtype=float,
        )
        residual = np.abs(actual_log - pred_log)
        covered = residual <= q_values
        lower = np.maximum(price_from_log(pred_log - q_values), 1.0)
        upper = price_from_log(pred_log + q_values)
        multiplier = upper / lower

        q_summary = {
            "target_coverage": q_policy["target_coverage"],
            "overall": {
                "rows": int(len(df)),
                "coverage": float(covered.mean()),
                "median_full_range_multiplier": float(np.median(multiplier)),
                "p90_full_range_multiplier": float(np.quantile(multiplier, 0.90)),
            },
            "groups": {},
        }
        for group in sorted(df["history_group"].unique()):
            mask = df["history_group"].to_numpy() == group
            q_summary["groups"][group] = {
                "rows": int(mask.sum()),
                "coverage": float(covered[mask].mean()),
                "median_full_range_multiplier": float(np.median(multiplier[mask])),
                "p90_full_range_multiplier": float(np.quantile(multiplier[mask], 0.90)),
            }
        summaries[q_name] = q_summary

        frame = df[["artist_key", "artist_name_ko", "track4_source", "history_group", "history_score", TARGET_PRICE]].copy()
        frame["quantile_policy"] = q_name
        frame["pred_log_price"] = pred_log
        frame["pred_price_krw"] = pred_price
        frame["range_lower_krw"] = lower
        frame["range_upper_krw"] = upper
        frame["covered"] = covered
        frame["range_full_multiplier"] = multiplier
        frames.append(frame)
    return summaries, pd.concat(frames, ignore_index=True)


def decision_for_group(interval_summary: dict[str, Any], point_summary: dict[str, Any], group: str) -> dict[str, Any]:
    q80 = interval_summary["q80"]["groups"][group]
    q90 = interval_summary["q90"]["groups"][group]
    point = point_summary[group]
    if q80["coverage"] >= Q80_MIN_COVERAGE and q80["median_full_range_multiplier"] <= Q80_MAX_RANGE:
        decision = "normal_range_candidate"
        reason = "q80 기준 coverage와 범위 폭이 허용 기준을 통과"
    elif (
        group == "low_history"
        and q90["coverage"] >= LOW_HISTORY_Q90_MIN_COVERAGE
        and q90["median_full_range_multiplier"] <= LOW_HISTORY_Q90_MAX_RANGE
    ):
        decision = "warning_plus_wider_range_candidate"
        reason = "q80은 부족하지만 q90 기준 더 넓은 범위와 경고는 가능"
    else:
        decision = "needs_warning_or_more_validation"
        reason = "coverage 또는 범위 폭이 기준 미달"
    return {
        "decision": decision,
        "reason": reason,
        "rows": point["rows"],
        "median_ape": point["median_ape"],
        "p95_ape": point["p95_ape"],
        "q80_coverage": q80["coverage"],
        "q80_median_range_multiplier": q80["median_full_range_multiplier"],
        "q90_coverage": q90["coverage"],
        "q90_median_range_multiplier": q90["median_full_range_multiplier"],
    }


def run_candidate(candidate: Candidate, train: pd.DataFrame, val_warm: pd.DataFrame, test_warm: pd.DataFrame) -> tuple[dict[str, Any], pd.DataFrame]:
    val_pred = fit_predict(candidate, train, val_warm)
    test_pred = fit_predict(candidate, train, test_warm)
    policy = learn_group_quantiles(val_warm, val_pred)
    interval_summary, pred_frame = apply_policy(test_warm, test_pred, policy)
    point_summary = {
        "validation": point_metrics(val_warm, val_pred),
        "test": point_metrics(test_warm, test_pred),
        "test_groups": grouped_point_metrics(test_warm, test_pred),
    }
    decisions = {
        group: decision_for_group(interval_summary, point_summary["test_groups"], group)
        for group in sorted(test_warm["history_group"].unique())
    }
    pred_frame["experiment_id"] = "T4-E041"
    pred_frame["candidate"] = candidate.name
    return (
        {
            "description": candidate.description,
            "features": candidate.categorical + candidate.numeric,
            "point_metrics": point_summary,
            "validation_policy": policy,
            "test_interval_summary": interval_summary,
            "service_decisions": decisions,
        },
        pred_frame,
    )


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    train_raw = pd.read_csv(SPLIT_DIR / "track4_train.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    val_raw = pd.read_csv(SPLIT_DIR / "track4_val_warm.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    test_raw = pd.read_csv(SPLIT_DIR / "track4_test_warm.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)

    train = add_warm_history_groups(add_artist_train_stats(train_raw, train_raw))
    val_warm = add_warm_history_groups(add_artist_train_stats(train_raw, val_raw))
    test_warm = add_warm_history_groups(add_artist_train_stats(train_raw, test_raw))

    results: dict[str, Any] = {
        "experiment_id": "T4-E041",
        "hypothesis_id": ["T4-H3", "T4-H32"],
        "date": date.today().isoformat(),
        "target_coverages": TARGET_COVERAGES,
        "decision_thresholds": {
            "q80_min_coverage": Q80_MIN_COVERAGE,
            "q80_max_range": Q80_MAX_RANGE,
            "low_history_q90_min_coverage": LOW_HISTORY_Q90_MIN_COVERAGE,
            "low_history_q90_max_range": LOW_HISTORY_Q90_MAX_RANGE,
        },
        "history_group_definition": {
            "low_history": "train 기준 작가 작품 수 5개 미만",
            "mid_history": "train 기준 작가 작품 수 5개 이상 20개 미만",
            "high_history": "train 기준 작가 작품 수 20개 이상",
        },
        "candidates": {},
    }
    frames = []
    for candidate in CANDIDATES:
        result, pred_frame = run_candidate(candidate, train, val_warm, test_warm)
        results["candidates"][candidate.name] = result
        frames.append(pred_frame)

    RESULT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.concat(frames, ignore_index=True).to_csv(PRED_PATH, index=False)
    print(RESULT_PATH)
    print(PRED_PATH)


if __name__ == "__main__":
    main()
