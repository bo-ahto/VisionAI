#!/usr/bin/env python3
"""Evaluate whether Warm historical price statistics should be conditionally allowed."""
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
MANIFEST_PATH = REPO / "configs" / "track4" / "feature_manifest.json"
RESULT_PATH = RESULT_DIR / "t4_e044_warm_price_stats_policy_metrics.json"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"
CONDITIONAL_PRICE_STATS = [
    "artist_train_median_log_price",
    "artist_train_mean_log_price",
    "artist_train_iqr_log_price",
]


@dataclass(frozen=True)
class Candidate:
    name: str
    features: list[str]
    description: str


BASE_FEATURES = [
    "medium_category",
    "support_category",
    "artist_key",
    "log_area",
    "aspect_ratio",
    "artist_works_log",
    "artist_works_count_train",
]

CANDIDATES = [
    Candidate("deployable_count_only", BASE_FEATURES, "현재 manifest 통과 보수 후보"),
    Candidate("stats_median_only", BASE_FEATURES + ["artist_train_median_log_price"], "작가 train 중앙 가격만 추가"),
    Candidate("stats_median_iqr", BASE_FEATURES + ["artist_train_median_log_price", "artist_train_iqr_log_price"], "작가 train 중앙 가격과 변동 폭 추가"),
    Candidate("stats_mean_only", BASE_FEATURES + ["artist_train_mean_log_price"], "작가 train 평균 가격만 추가"),
    Candidate("stats_all", BASE_FEATURES + CONDITIONAL_PRICE_STATS, "작가 train 가격 통계 전체 추가"),
]


def onehot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def build_pipeline(features: list[str]) -> Pipeline:
    categorical = ["medium_category", "support_category", "artist_key"]
    numeric = [feature for feature in features if feature not in categorical]
    preprocessor = ColumnTransformer(
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


def add_history_group(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    count = out["artist_works_count_train"].fillna(0)
    out["history_group"] = np.select([count < 5, count < 20], ["low_history", "mid_history"], default="high_history")
    return out


def metrics(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, Any]:
    actual_price = df[TARGET_PRICE].to_numpy(dtype=float)
    pred_price = np.maximum(np.exp(pred_log), 1.0)
    ape = np.abs(pred_price - actual_price) / actual_price
    return {
        "rows": int(len(df)),
        "median_ape": float(np.median(ape)),
        "p95_ape": float(np.quantile(ape, 0.95)),
        "within_30": float(np.mean(ape <= 0.30)),
        "within_50": float(np.mean(ape <= 0.50)),
    }


def group_metrics(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for group in sorted(df["history_group"].unique()):
        mask = df["history_group"].to_numpy() == group
        out[group] = metrics(df.loc[mask], pred_log[mask])
    return out


def reasons_for_feature(feature: str, manifest: dict[str, Any], conditional_allow: bool) -> list[str]:
    if conditional_allow and feature in CONDITIONAL_PRICE_STATS:
        return []
    reasons: list[str] = []
    if feature in set(manifest.get("forbidden_exact", [])):
        reasons.append("forbidden_exact")
    lower = feature.lower()
    for pattern in manifest.get("forbidden_patterns", []):
        if pattern.lower() in lower:
            reasons.append(f"forbidden_pattern:{pattern}")
    return reasons


def feature_check(name: str, features: list[str], manifest: dict[str, Any], columns: set[str], conditional_allow: bool) -> dict[str, Any]:
    missing = sorted(feature for feature in features if feature not in columns)
    violations = {
        feature: reasons_for_feature(feature, manifest, conditional_allow)
        for feature in features
        if reasons_for_feature(feature, manifest, conditional_allow)
    }
    return {
        "name": name,
        "conditional_price_stats_allowed": conditional_allow,
        "missing_columns": missing,
        "violations": violations,
        "passed": not missing and not violations,
    }


def evaluate_candidate(candidate: Candidate, train: pd.DataFrame, test: pd.DataFrame) -> dict[str, Any]:
    model = build_pipeline(candidate.features)
    model.fit(train[candidate.features], train[TARGET_LOG])
    pred = model.predict(test[candidate.features])
    return {
        "description": candidate.description,
        "features": candidate.features,
        "overall": metrics(test, pred),
        "history_groups": group_metrics(test, pred),
    }


def improvement(base: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    base_median = base["overall"]["median_ape"]
    cand_median = candidate["overall"]["median_ape"]
    base_p95 = base["overall"]["p95_ape"]
    cand_p95 = candidate["overall"]["p95_ape"]
    return {
        "median_ape_abs_delta": float(base_median - cand_median),
        "median_ape_relative_reduction": float((base_median - cand_median) / base_median),
        "p95_ape_abs_delta": float(base_p95 - cand_p95),
        "p95_ape_relative_reduction": float((base_p95 - cand_p95) / base_p95),
    }


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    train_raw = pd.read_csv(SPLIT_DIR / "track4_train.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    test_warm_raw = pd.read_csv(SPLIT_DIR / "track4_test_warm.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    train = add_history_group(add_artist_train_stats(train_raw, train_raw))
    test_warm = add_history_group(add_artist_train_stats(train_raw, test_warm_raw))
    columns = set(train.columns) | set(test_warm.columns)

    candidates = {candidate.name: evaluate_candidate(candidate, train, test_warm) for candidate in CANDIDATES}
    base = candidates["deployable_count_only"]
    improvements = {
        name: improvement(base, value)
        for name, value in candidates.items()
        if name != "deployable_count_only"
    }
    best_name = min(candidates, key=lambda name: candidates[name]["overall"]["median_ape"])
    best = candidates[best_name]

    feature_checks = {
        name: {
            "current_manifest": feature_check(name, value["features"], manifest, columns, conditional_allow=False),
            "conditional_allow_price_stats": feature_check(name, value["features"], manifest, columns, conditional_allow=True),
        }
        for name, value in candidates.items()
    }

    best_improvement = improvements.get(best_name, {"median_ape_abs_delta": 0.0, "p95_ape_abs_delta": 0.0})
    recommend_allow = (
        best_name != "deployable_count_only"
        and best_improvement["median_ape_abs_delta"] >= 0.03
        and best_improvement["p95_ape_abs_delta"] > 0
        and feature_checks[best_name]["conditional_allow_price_stats"]["passed"]
    )

    result = {
        "experiment_id": "T4-E044",
        "hypothesis_id": ["T4-H34"],
        "date": date.today().isoformat(),
        "policy_question": "Warm 과거 가격 통계 피처를 운영 피처로 조건부 허용할지 여부",
        "condition_for_allowing": [
            "예측 시점 이전 학습/거래 데이터만 사용해 계산한다.",
            "예측 대상 작품의 정답 가격은 절대 포함하지 않는다.",
            "운영 데이터 파이프라인에서 같은 계산을 재현할 수 있어야 한다.",
        ],
        "candidates": candidates,
        "improvements_vs_deployable_count_only": improvements,
        "feature_checks": feature_checks,
        "best_candidate": best_name,
        "recommendation": {
            "allow_conditionally": bool(recommend_allow),
            "reason": (
                "성능 개선 폭이 크고 조건부 manifest에서는 통과하므로 예측 시점 이전 가격 통계로만 계산한다는 조건에서 허용 권장"
                if recommend_allow
                else "성능 개선 또는 운영 조건이 충분하지 않아 보류 권장"
            ),
            "best_candidate_median_ape": best["overall"]["median_ape"],
            "deployable_candidate_median_ape": base["overall"]["median_ape"],
            "best_candidate_p95_ape": best["overall"]["p95_ape"],
            "deployable_candidate_p95_ape": base["overall"]["p95_ape"],
        },
    }
    RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(RESULT_PATH)
    print(
        json.dumps(
            {
                "best_candidate": best_name,
                "allow_conditionally": result["recommendation"]["allow_conditionally"],
                "median_ape": result["recommendation"]["best_candidate_median_ape"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
