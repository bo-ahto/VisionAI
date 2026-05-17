#!/usr/bin/env python3
"""Run Track 4 E030 Cold risk segmentation and output policy experiment."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import QuantileRegressor
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO = Path(__file__).resolve().parents[2]
SPLIT_DIR = REPO / "data" / "track4_split"
RESULT_DIR = REPO / "data" / "track4" / "results"
PRED_DIR = REPO / "data" / "track4" / "predictions"
RESULT_PATH = RESULT_DIR / "t4_e030_cold_risk_policy_metrics.json"
PRED_PATH = PRED_DIR / "t4_e030_cold_risk_policy_predictions.csv"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"
NUMERIC = ["log_area", "aspect_ratio"]
CATEGORICAL = ["medium_category"]
FEATURES = CATEGORICAL + NUMERIC


def onehot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def build_model() -> Pipeline:
    return Pipeline(
        [
            (
                "preprocess",
                ColumnTransformer(
                    [
                        (
                            "numeric",
                            Pipeline(
                                [
                                    ("imputer", SimpleImputer(strategy="median")),
                                    ("scaler", StandardScaler()),
                                ]
                            ),
                            NUMERIC,
                        ),
                        (
                            "categorical",
                            Pipeline(
                                [
                                    ("imputer", SimpleImputer(strategy="constant", fill_value="unknown")),
                                    ("onehot", onehot_encoder()),
                                ]
                            ),
                            CATEGORICAL,
                        ),
                    ],
                    remainder="drop",
                ),
            ),
            ("model", QuantileRegressor(quantile=0.5, alpha=0.0001, solver="highs")),
        ]
    )


def price_from_log(values: np.ndarray) -> np.ndarray:
    return np.exp(values)


def add_risk_flags(train: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    area_q90 = train["log_area"].quantile(0.90)
    out["risk_3d"] = out["is_3d_candidate"].fillna(0).astype(int)
    out["risk_support_unknown"] = (out["support_category"].fillna("unknown") == "unknown").astype(int)
    out["risk_medium_unknown"] = (out["medium_category"].fillna("unknown") == "unknown").astype(int)
    out["risk_large_area"] = (out["log_area"] >= area_q90).astype(int)
    out["risk_high_price_candidate"] = out["is_high_price_candidate"].fillna(0).astype(int)
    out["risk_extreme_aspect"] = out["is_extreme_aspect_ratio"].fillna(0).astype(int)
    risk_cols = [
        "risk_3d",
        "risk_support_unknown",
        "risk_medium_unknown",
        "risk_large_area",
        "risk_high_price_candidate",
        "risk_extreme_aspect",
    ]
    out["risk_score"] = out[risk_cols].sum(axis=1)
    out["risk_group"] = np.where(out["risk_score"] == 0, "low", np.where(out["risk_score"] == 1, "medium", "high"))
    return out


def metric_dict(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    if len(df) == 0:
        return {"rows": 0, "median_ape": None, "mape": None, "rmse_log": None, "within_30": None, "within_50": None, "p95_ape": None}
    y_log = df[TARGET_LOG].to_numpy(dtype=float)
    y_price = df[TARGET_PRICE].to_numpy(dtype=float)
    pred_price = np.maximum(price_from_log(pred_log), 1.0)
    ape = np.abs(pred_price - y_price) / y_price
    return {
        "rows": int(len(df)),
        "artists": int(df["artist_key"].nunique()),
        "median_ape": float(np.median(ape)),
        "mape": float(np.mean(ape)),
        "rmse_log": float(np.sqrt(mean_squared_error(y_log, pred_log))),
        "within_30": float(np.mean(ape <= 0.30)),
        "within_50": float(np.mean(ape <= 0.50)),
        "p95_ape": float(np.quantile(ape, 0.95)),
    }


def group_metrics(df: pd.DataFrame, pred_log: np.ndarray, column: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for value in sorted(df[column].dropna().unique().tolist()):
        mask = df[column].to_numpy() == value
        out[str(value)] = metric_dict(df.loc[mask], pred_log[mask])
    return out


def flag_metrics(df: pd.DataFrame, pred_log: np.ndarray, flag: str) -> dict[str, Any]:
    values = {}
    for label, mask in [("false", df[flag].to_numpy() == 0), ("true", df[flag].to_numpy() == 1)]:
        values[label] = metric_dict(df.loc[mask], pred_log[mask])
    return values


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    train = pd.read_csv(SPLIT_DIR / "track4_train.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).copy()
    val_cold = pd.read_csv(SPLIT_DIR / "track4_val_cold.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).copy()
    val_cold = add_risk_flags(train, val_cold)

    model = build_model()
    model.fit(train[FEATURES], train[TARGET_LOG])
    pred_log = model.predict(val_cold[FEATURES])
    pred_price = price_from_log(pred_log)
    ape = np.abs(pred_price - val_cold[TARGET_PRICE].to_numpy(dtype=float)) / val_cold[TARGET_PRICE].to_numpy(dtype=float)

    flags = [
        "risk_3d",
        "risk_support_unknown",
        "risk_medium_unknown",
        "risk_large_area",
        "risk_high_price_candidate",
        "risk_extreme_aspect",
    ]
    results = {
        "experiment_id": "T4-E030",
        "hypothesis_id": ["T4-H17", "T4-H24"],
        "date": date.today().isoformat(),
        "model": "QuantileRegressor",
        "features": FEATURES,
        "overall": metric_dict(val_cold, pred_log),
        "risk_group_metrics": group_metrics(val_cold, pred_log, "risk_group"),
        "risk_score_metrics": group_metrics(val_cold, pred_log, "risk_score"),
        "flag_metrics": {flag: flag_metrics(val_cold, pred_log, flag) for flag in flags},
        "policy_candidate": {
            "low": "단일 가격 + 일반 범위 표시 후보",
            "medium": "단일 가격 + 넓은 범위 또는 주의 표시 후보",
            "high": "단일 가격 단독 사용 지양, 넓은 범위와 낮은 신뢰도 표시 후보",
        },
    }
    RESULT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    out = val_cold[
        [
            "artist_key",
            "artist_name_ko",
            "medium_category",
            "support_category",
            "log_area",
            "aspect_ratio",
            "is_3d_candidate",
            "is_high_price_candidate",
            "is_extreme_aspect_ratio",
            "risk_score",
            "risk_group",
        ]
    ].copy()
    out["experiment_id"] = "T4-E030"
    out["actual_price_krw"] = val_cold[TARGET_PRICE].to_numpy(dtype=float)
    out["pred_log_price"] = pred_log
    out["pred_price_krw"] = pred_price
    out["ape"] = ape
    out.to_csv(PRED_PATH, index=False)
    print(RESULT_PATH)
    print(PRED_PATH)


if __name__ == "__main__":
    main()
