#!/usr/bin/env python3
"""Validate whether Cold low-risk predictions are usable in Track 4."""
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
from sklearn.linear_model import QuantileRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO = Path(__file__).resolve().parents[2]
SPLIT_DIR = REPO / "data" / "track4_split"
RESULT_DIR = REPO / "data" / "track4" / "results"
PRED_DIR = REPO / "data" / "track4" / "predictions"
RESULT_PATH = RESULT_DIR / "t4_e040_cold_low_risk_policy_metrics.json"
PRED_PATH = PRED_DIR / "t4_e040_cold_low_risk_policy_predictions.csv"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"
TARGET_COVERAGES = [0.70, 0.80, 0.90]
MIN_GROUP_ROWS = 30

Q80_MIN_COVERAGE = 0.80
Q80_MAX_SINGLE_PRICE_RANGE = 4.0
Q90_MIN_RANGE_ONLY_COVERAGE = 0.78
Q90_MAX_LOW_RISK_RANGE = 6.0
MID_HIGH_MAX_RANGE = 10.0


@dataclass(frozen=True)
class Candidate:
    name: str
    numeric: list[str]
    categorical: list[str]
    description: str


CANDIDATES = [
    Candidate(
        "cold_full_size",
        ["width_cm", "height_cm", "log_area", "aspect_ratio", "has_depth", "is_3d_candidate"],
        ["medium_category"],
        "Cold median APE 후보",
    ),
    Candidate(
        "cold_area_only",
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
    return Pipeline(
        [
            ("preprocess", preprocessor),
            ("model", QuantileRegressor(quantile=0.5, alpha=0.0001, solver="highs")),
        ]
    )


def add_cold_risk_groups(train: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
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
    for col in flags.columns:
        out[col] = flags[col]
    return out


def fit_predict(candidate: Candidate, train: pd.DataFrame, df: pd.DataFrame) -> np.ndarray:
    features = candidate.categorical + candidate.numeric
    model = build_model(candidate)
    model.fit(train[features], train[TARGET_LOG])
    return model.predict(df[features])


def price_from_log(values: np.ndarray) -> np.ndarray:
    return np.exp(values)


def ape_values(df: pd.DataFrame, pred_log: np.ndarray) -> np.ndarray:
    y_price = df[TARGET_PRICE].to_numpy(dtype=float)
    pred_price = np.maximum(price_from_log(pred_log), 1.0)
    return np.abs(pred_price - y_price) / y_price


def point_metrics(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, Any]:
    ape = ape_values(df, pred_log)
    return {
        "rows": int(len(df)),
        "median_ape": float(np.median(ape)),
        "p95_ape": float(np.quantile(ape, 0.95)),
        "within_30": float(np.mean(ape <= 0.30)),
        "within_50": float(np.mean(ape <= 0.50)),
    }


def grouped_point_metrics(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for group in sorted(df["confidence_group"].unique()):
        mask = df["confidence_group"].to_numpy() == group
        out[group] = point_metrics(df.loc[mask], pred_log[mask])
    return out


def learn_group_quantiles(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, Any]:
    residual = np.abs(df[TARGET_LOG].to_numpy(dtype=float) - pred_log)
    policy: dict[str, Any] = {}
    for coverage in TARGET_COVERAGES:
        q_name = f"q{int(coverage * 100)}"
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
    frames = []
    summary: dict[str, Any] = {}

    for q_name, q_policy in policy.items():
        q_values = np.array(
            [q_policy["groups"].get(group, q_policy["overall"])["abs_log_error"] for group in df["confidence_group"]],
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
        for group in sorted(df["confidence_group"].unique()):
            mask = df["confidence_group"].to_numpy() == group
            q_summary["groups"][group] = {
                "rows": int(mask.sum()),
                "coverage": float(covered[mask].mean()),
                "median_full_range_multiplier": float(np.median(multiplier[mask])),
                "p90_full_range_multiplier": float(np.quantile(multiplier[mask], 0.90)),
            }
        summary[q_name] = q_summary

        frame = df[
            [
                "artist_key",
                "artist_name_ko",
                "track4_source",
                "confidence_group",
                "confidence_score",
                "risk_3d",
                "risk_support_unknown",
                "risk_large_area",
                "risk_extreme_aspect",
                TARGET_PRICE,
            ]
        ].copy()
        frame["quantile_policy"] = q_name
        frame["pred_log_price"] = pred_log
        frame["pred_price_krw"] = pred_price
        frame["range_lower_krw"] = lower
        frame["range_upper_krw"] = upper
        frame["covered"] = covered
        frame["range_full_multiplier"] = multiplier
        frames.append(frame)

    return summary, pd.concat(frames, ignore_index=True)


def decision_for_group(interval_summary: dict[str, Any], point_summary: dict[str, Any], group: str) -> dict[str, Any]:
    q80 = interval_summary["q80"]["groups"][group]
    q90 = interval_summary["q90"]["groups"][group]
    point = point_summary[group]

    if q80["coverage"] >= Q80_MIN_COVERAGE and q80["median_full_range_multiplier"] <= Q80_MAX_SINGLE_PRICE_RANGE:
        decision = "single_price_plus_range_candidate"
        reason = "q80 기준 coverage와 범위 폭이 모두 허용 기준을 통과"
    elif (
        group == "low_risk"
        and q90["coverage"] >= Q90_MIN_RANGE_ONLY_COVERAGE
        and q90["median_full_range_multiplier"] <= Q90_MAX_LOW_RISK_RANGE
    ):
        decision = "range_only_borderline_candidate"
        reason = "q80은 부족하지만 q90 기준 가격 범위는 제한 운영 후보"
    elif q90["median_full_range_multiplier"] > MID_HIGH_MAX_RANGE:
        decision = "warning_or_hold"
        reason = "필요한 가격 범위가 넓어 서비스 설명력이 낮음"
    else:
        decision = "needs_more_validation"
        reason = "coverage 또는 범위 폭 중 하나가 기준 미달"

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


def run_candidate(candidate: Candidate, train: pd.DataFrame, val_cold: pd.DataFrame, test_cold: pd.DataFrame) -> tuple[dict[str, Any], pd.DataFrame]:
    val_pred = fit_predict(candidate, train, val_cold)
    test_pred = fit_predict(candidate, train, test_cold)
    policy = learn_group_quantiles(val_cold, val_pred)
    interval_summary, pred_frame = apply_policy(test_cold, test_pred, policy)
    point_summary = {
        "overall": point_metrics(test_cold, test_pred),
        "groups": grouped_point_metrics(test_cold, test_pred),
    }
    decisions = {
        group: decision_for_group(interval_summary, point_summary["groups"], group)
        for group in sorted(test_cold["confidence_group"].unique())
    }
    pred_frame["experiment_id"] = "T4-E040"
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
    train = pd.read_csv(SPLIT_DIR / "track4_train.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    val_cold = pd.read_csv(SPLIT_DIR / "track4_val_cold.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    test_cold = pd.read_csv(SPLIT_DIR / "track4_test_cold.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)

    val_cold = add_cold_risk_groups(train, val_cold)
    test_cold = add_cold_risk_groups(train, test_cold)

    results: dict[str, Any] = {
        "experiment_id": "T4-E040",
        "hypothesis_id": ["T4-H31"],
        "date": date.today().isoformat(),
        "target_coverages": TARGET_COVERAGES,
        "decision_thresholds": {
            "q80_min_coverage": Q80_MIN_COVERAGE,
            "q80_max_single_price_range": Q80_MAX_SINGLE_PRICE_RANGE,
            "q90_min_range_only_coverage": Q90_MIN_RANGE_ONLY_COVERAGE,
            "q90_max_low_risk_range": Q90_MAX_LOW_RISK_RANGE,
            "mid_high_max_range": MID_HIGH_MAX_RANGE,
        },
        "risk_group_definition": {
            "low_risk": "risk flag 0개",
            "mid_risk": "risk flag 1개",
            "high_risk": "risk flag 2개 이상",
            "risk_flags": ["3D 후보", "지지체 unknown", "train 기준 상위 10% 대형", "극단 가로세로비"],
        },
        "candidates": {},
    }
    frames = []
    for candidate in CANDIDATES:
        result, pred_frame = run_candidate(candidate, train, val_cold, test_cold)
        results["candidates"][candidate.name] = result
        frames.append(pred_frame)

    RESULT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.concat(frames, ignore_index=True).to_csv(PRED_PATH, index=False)
    print(RESULT_PATH)
    print(PRED_PATH)


if __name__ == "__main__":
    main()
