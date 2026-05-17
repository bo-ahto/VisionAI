#!/usr/bin/env python3
"""Generate final Track 4 artifacts with conditional feature manifest policy."""
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
RESULT_PATH = RESULT_DIR / "t4_e045_final_artifact_dry_run.json"
TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"


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


def reasons_for_feature(feature: str, manifest: dict[str, Any], allow_conditional: bool) -> list[str]:
    if allow_conditional and feature in set(manifest.get("conditional_allow_exact", [])):
        return []
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
    violations = {
        feature: reasons_for_feature(feature, manifest, allow_conditional=True)
        for feature in features
        if reasons_for_feature(feature, manifest, allow_conditional=True)
    }
    return {
        "name": name,
        "features": features,
        "conditional_allow_exact": sorted(manifest.get("conditional_allow_exact", [])),
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


def group_metrics(df: pd.DataFrame, pred_log: np.ndarray, group_col: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for group in sorted(df[group_col].unique()):
        mask = df[group_col].to_numpy() == group
        out[group] = metrics(df.loc[mask], pred_log[mask])
    return out


def train_eval_save(
    train: pd.DataFrame,
    test: pd.DataFrame,
    features: list[str],
    categorical: list[str],
    model_name: str,
    artifact_name: str,
    group_col: str,
) -> dict[str, Any]:
    model = build_pipeline(features, categorical, model_name)
    model.fit(train[features], train[TARGET_LOG])
    pred = model.predict(test[features])
    artifact_path = MODEL_DIR / artifact_name
    joblib.dump(
        {
            "model": model,
            "features": features,
            "categorical_features": categorical,
            "target": TARGET_LOG,
            "created_by": "scripts/track4/run_t4_e045_final_artifact_dry_run.py",
        },
        artifact_path,
    )
    return {
        "artifact": str(artifact_path.relative_to(REPO)),
        "features": features,
        "metrics": metrics(test, pred),
        "group_metrics": group_metrics(test, pred, group_col),
    }


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    feature_sets = manifest["model_feature_sets"]
    warm_features = feature_sets["warm_final_conditional_stats"]
    cold_features = feature_sets["cold_final_full_size"]

    train_raw = pd.read_csv(SPLIT_DIR / "track4_train.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    test_warm_raw = pd.read_csv(SPLIT_DIR / "track4_test_warm.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    test_cold_raw = pd.read_csv(SPLIT_DIR / "track4_test_cold.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)

    train = add_history_group(add_artist_train_stats(train_raw, train_raw))
    test_warm = add_history_group(add_artist_train_stats(train_raw, test_warm_raw))
    test_cold = add_cold_risk_group(train_raw, test_cold_raw)
    columns = set(train.columns) | set(test_warm.columns) | set(test_cold.columns)

    checks = [
        feature_check("warm_final_conditional_stats", warm_features, manifest, columns),
        feature_check("cold_final_full_size", cold_features, manifest, columns),
    ]
    if not all(check["passed"] for check in checks):
        RESULT_PATH.write_text(json.dumps({"experiment_id": "T4-E045", "feature_checks": checks, "passed": False}, ensure_ascii=False, indent=2), encoding="utf-8")
        raise SystemExit(1)

    warm = train_eval_save(
        train,
        test_warm,
        warm_features,
        ["artist_key", "medium_category", "support_category"],
        "ridge",
        "track4_warm_final_conditional_stats_ridge.joblib",
        "history_group",
    )
    cold = train_eval_save(
        train_raw,
        test_cold,
        cold_features,
        ["medium_category"],
        "quantile",
        "track4_cold_final_full_size_quantile.joblib",
        "cold_risk_group",
    )
    result = {
        "experiment_id": "T4-E045",
        "hypothesis_id": ["T4-H12", "T4-H30", "T4-H35"],
        "date": date.today().isoformat(),
        "manifest": str(MANIFEST_PATH.relative_to(REPO)),
        "feature_checks": checks,
        "routing_policy": {
            "warm": "입력 작가가 train 작가 집합에 있으면 Warm final 모델 사용",
            "cold": "입력 작가가 train 작가 집합에 없으면 Cold final 모델 사용",
        },
        "conditional_feature_policy": manifest.get("conditional_allow_rules", {}),
        "output_policy": {
            "warm_low_history": "경고 + q90 넓은 범위 후보",
            "warm_mid_high_history": "일반 q80 범위 후보",
            "cold_low_risk": "q90 제한적 범위 후보",
            "cold_mid_high_risk": "단일 가격 보류 또는 강한 경고",
        },
        "artifacts": {
            "warm_final_conditional_stats": warm,
            "cold_final_full_size": cold,
        },
        "passed": True,
    }
    RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(RESULT_PATH)
    print(
        json.dumps(
            {
                "passed": True,
                "warm_median_ape": warm["metrics"]["median_ape"],
                "cold_median_ape": cold["metrics"]["median_ape"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
