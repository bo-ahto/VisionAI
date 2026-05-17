#!/usr/bin/env python3
"""Run a Track 4 production candidate dry-run."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import QuantileRegressor, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO = Path(__file__).resolve().parents[2]
SPLIT_DIR = REPO / "data" / "track4_split"
MODEL_DIR = REPO / "data" / "track4" / "models"
RESULT_DIR = REPO / "data" / "track4" / "results"
MANIFEST_PATH = REPO / "configs" / "track4" / "feature_manifest.json"
RESULT_PATH = RESULT_DIR / "t4_e043_production_dry_run.json"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"

WARM_PERFORMANCE_FEATURES = [
    "medium_category",
    "support_category",
    "artist_key",
    "log_area",
    "aspect_ratio",
    "artist_works_log",
    "artist_works_count_train",
    "artist_train_median_log_price",
    "artist_train_mean_log_price",
    "artist_train_iqr_log_price",
]
WARM_DEPLOYABLE_FEATURES = [
    "medium_category",
    "support_category",
    "artist_key",
    "log_area",
    "aspect_ratio",
    "artist_works_log",
    "artist_works_count_train",
]
COLD_DEPLOYABLE_FEATURES = [
    "medium_category",
    "width_cm",
    "height_cm",
    "log_area",
    "aspect_ratio",
    "has_depth",
    "is_3d_candidate",
]


def onehot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def build_pipeline(features: list[str], categorical: list[str], model_name: str) -> Pipeline:
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
    if model_name == "ridge":
        estimator = Ridge(alpha=10.0, random_state=42)
    elif model_name == "quantile":
        estimator = QuantileRegressor(quantile=0.5, alpha=0.0001, solver="highs")
    else:
        raise ValueError(model_name)
    return Pipeline([("preprocess", preprocessor), ("model", estimator)])


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


def add_cold_risk_group(train: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    area_q90 = train["log_area"].quantile(0.90)
    score = (
        out["is_3d_candidate"].fillna(0).astype(int)
        + (out["support_category"].fillna("unknown") == "unknown").astype(int)
        + (out["log_area"] >= area_q90).astype(int)
        + out["is_extreme_aspect_ratio"].fillna(0).astype(int)
    )
    out["cold_risk_group"] = np.where(score == 0, "low_risk", np.where(score == 1, "mid_risk", "high_risk"))
    return out


def reasons_for_feature(feature: str, manifest: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if feature in set(manifest.get("forbidden_exact", [])):
        reasons.append("forbidden_exact")
    lower = feature.lower()
    for pattern in manifest.get("forbidden_patterns", []):
        if pattern.lower() in lower:
            reasons.append(f"forbidden_pattern:{pattern}")
    return reasons


def feature_check(name: str, features: list[str], manifest: dict[str, Any], columns: set[str]) -> dict[str, Any]:
    missing = sorted(feature for feature in features if feature not in columns)
    violations = {feature: reasons_for_feature(feature, manifest) for feature in features if reasons_for_feature(feature, manifest)}
    return {
        "name": name,
        "features": features,
        "missing_columns": missing,
        "violations": violations,
        "passed": not missing and not violations,
    }


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


def train_and_eval(train: pd.DataFrame, test: pd.DataFrame, features: list[str], categorical: list[str], model_name: str, artifact_name: str) -> dict[str, Any]:
    pipeline = build_pipeline(features, categorical, model_name)
    pipeline.fit(train[features], train[TARGET_LOG])
    pred = pipeline.predict(test[features])
    artifact_path = MODEL_DIR / artifact_name
    joblib.dump({"model": pipeline, "features": features, "target": TARGET_LOG}, artifact_path)
    return {
        "artifact": str(artifact_path.relative_to(REPO)),
        "features": features,
        "metrics": metrics(test, pred),
    }


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    train_raw = pd.read_csv(SPLIT_DIR / "track4_train.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    test_warm_raw = pd.read_csv(SPLIT_DIR / "track4_test_warm.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    test_cold_raw = pd.read_csv(SPLIT_DIR / "track4_test_cold.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    train = add_history_group(add_artist_train_stats(train_raw, train_raw))
    test_warm = add_history_group(add_artist_train_stats(train_raw, test_warm_raw))
    test_cold = add_cold_risk_group(train_raw, test_cold_raw)
    columns = set(train.columns) | set(test_warm.columns) | set(test_cold.columns)

    checks = [
        feature_check("warm_performance_artist_price_stats", WARM_PERFORMANCE_FEATURES, manifest, columns),
        feature_check("warm_deployable_artist_count", WARM_DEPLOYABLE_FEATURES, manifest, columns),
        feature_check("cold_deployable_full_size", COLD_DEPLOYABLE_FEATURES, manifest, columns),
    ]

    warm_deployable = train_and_eval(
        train,
        test_warm,
        WARM_DEPLOYABLE_FEATURES,
        ["medium_category", "support_category", "artist_key"],
        "ridge",
        "track4_warm_deployable_ridge.joblib",
    )
    cold_deployable = train_and_eval(
        train_raw,
        test_cold,
        COLD_DEPLOYABLE_FEATURES,
        ["medium_category"],
        "quantile",
        "track4_cold_deployable_quantile.joblib",
    )

    result = {
        "experiment_id": "T4-E043",
        "hypothesis_id": ["T4-H12", "T4-H30"],
        "date": date.today().isoformat(),
        "feature_checks": checks,
        "routing_policy": {
            "warm": "artist_key가 train 작가 집합에 있으면 Warm 모델 사용",
            "cold": "artist_key가 train 작가 집합에 없으면 Cold 모델 사용",
        },
        "output_policy": {
            "warm_low_history": "경고 + q90 넓은 범위 후보",
            "warm_mid_high_history": "일반 q80 범위 후보",
            "cold_low_risk": "q90 제한적 범위 후보",
            "cold_mid_high_risk": "단일 가격 보류 또는 강한 경고",
        },
        "trained_artifacts": {
            "warm_deployable_artist_count": warm_deployable,
            "cold_deployable_full_size": cold_deployable,
        },
        "blocked_candidate": {
            "name": "warm_performance_artist_price_stats",
            "reason": "현재 manifest가 price 패턴 피처를 금지하므로 최종 운영 후보로 자동 통과하지 못함",
            "required_decision": "과거 거래 가격 통계를 운영 피처로 허용할지 별도 정책 결정 필요",
        },
    }
    result["passed"] = (
        next(check for check in checks if check["name"] == "warm_deployable_artist_count")["passed"]
        and next(check for check in checks if check["name"] == "cold_deployable_full_size")["passed"]
        and not next(check for check in checks if check["name"] == "warm_performance_artist_price_stats")["passed"]
    )
    RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(RESULT_PATH)
    print(json.dumps({"passed": result["passed"], "artifacts": list(result["trained_artifacts"].keys())}, ensure_ascii=False))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
