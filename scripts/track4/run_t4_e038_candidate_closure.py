#!/usr/bin/env python3
"""Run Track 4 E038 candidate closure validation/test evaluation."""
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
RESULT_PATH = RESULT_DIR / "t4_e038_candidate_closure_metrics.json"
PRED_PATH = PRED_DIR / "t4_e038_candidate_closure_predictions.csv"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"


@dataclass(frozen=True)
class Candidate:
    name: str
    split_type: str
    model_name: str
    numeric: list[str]
    categorical: list[str]
    description: str
    operating_note: str


CANDIDATES = [
    Candidate(
        "warm_structure_only",
        "warm",
        "ridge",
        ["log_area", "aspect_ratio"],
        ["medium_category", "support_category"],
        "작가 정보 없는 Warm 비교 기준",
        "운영 가능하지만 Warm 최종 후보 아님",
    ),
    Candidate(
        "warm_operational_artist_count",
        "warm",
        "ridge",
        ["log_area", "aspect_ratio", "artist_works_log", "artist_works_count_train"],
        ["medium_category", "support_category", "artist_key"],
        "작가 key와 작가 작품 수 기반 보수 후보",
        "현재 데이터만으로 운영 재현 가능",
    ),
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
        "작가 key와 train 기준 작가 가격 통계 기반 성능 후보",
        "운영에서 작가별 과거 가격 DB를 만들 수 있을 때만 사용 가능",
    ),
    Candidate(
        "cold_area_only",
        "cold",
        "quantile",
        ["log_area"],
        ["medium_category"],
        "Cold p95 안정 후보",
        "운영 가능",
    ),
    Candidate(
        "cold_full_size",
        "cold",
        "quantile",
        ["width_cm", "height_cm", "log_area", "aspect_ratio", "has_depth", "is_3d_candidate"],
        ["medium_category"],
        "Cold median APE 후보",
        "운영 가능",
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
        columns={
            "median": "artist_train_median_log_price",
            "mean": "artist_train_mean_log_price",
            "count": "artist_train_price_count",
        }
    )
    stats["artist_train_iqr_log_price"] = grouped.quantile(0.75) - grouped.quantile(0.25)
    out = out.merge(stats, left_on="artist_key", right_index=True, how="left")
    out["artist_train_median_log_price"] = out["artist_train_median_log_price"].fillna(float(train[TARGET_LOG].median()))
    out["artist_train_mean_log_price"] = out["artist_train_mean_log_price"].fillna(float(train[TARGET_LOG].mean()))
    out["artist_train_iqr_log_price"] = out["artist_train_iqr_log_price"].fillna(0.0)
    return out


def price_from_log(values: np.ndarray) -> np.ndarray:
    return np.exp(values)


def metric_dict(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, Any]:
    if len(df) == 0:
        return {"rows": 0}
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


def source_metrics(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for source, source_df in df.reset_index().groupby("track4_source", dropna=False):
        idx = source_df["index"].to_numpy()
        out[str(source)] = metric_dict(df.loc[idx], pred_log[idx])
    return out


def risk_metrics(df: pd.DataFrame, pred_log: np.ndarray, train: pd.DataFrame) -> dict[str, Any]:
    area_q90 = train["log_area"].quantile(0.90)
    risk = pd.DataFrame(index=df.index)
    risk["risk_3d"] = df["is_3d_candidate"].fillna(0).astype(int)
    risk["risk_support_unknown"] = (df["support_category"].fillna("unknown") == "unknown").astype(int)
    risk["risk_large_area"] = (df["log_area"] >= area_q90).astype(int)
    risk["risk_extreme_aspect"] = df["is_extreme_aspect_ratio"].fillna(0).astype(int)
    risk["risk_score"] = risk.sum(axis=1)
    risk["risk_group"] = np.where(risk["risk_score"] == 0, "low", np.where(risk["risk_score"] == 1, "medium", "high"))
    merged = pd.concat([df, risk], axis=1)
    out: dict[str, Any] = {}
    for group, group_df in merged.reset_index().groupby("risk_group"):
        idx = group_df["index"].to_numpy()
        out[str(group)] = metric_dict(df.loc[idx], pred_log[idx])
    return out


def run_candidate(candidate: Candidate, train: pd.DataFrame, eval_sets: dict[str, pd.DataFrame]) -> tuple[dict[str, Any], list[pd.DataFrame]]:
    model = build_model(candidate)
    features = candidate.categorical + candidate.numeric
    model.fit(train[features], train[TARGET_LOG])
    result: dict[str, Any] = {
        "model": candidate.model_name,
        "description": candidate.description,
        "operating_note": candidate.operating_note,
        "features": features,
        "eval": {},
    }
    frames: list[pd.DataFrame] = []
    for split_name, eval_df in eval_sets.items():
        pred_log = model.predict(eval_df[features])
        pred_price = price_from_log(pred_log)
        ape = np.abs(pred_price - eval_df[TARGET_PRICE].to_numpy(dtype=float)) / eval_df[TARGET_PRICE].to_numpy(dtype=float)
        result["eval"][split_name] = {
            "overall": metric_dict(eval_df, pred_log),
            "source": source_metrics(eval_df, pred_log),
        }
        if candidate.split_type == "cold":
            result["eval"][split_name]["risk"] = risk_metrics(eval_df, pred_log, train)
        frame = eval_df[["artist_key", "artist_name_ko", "track4_source", "medium_category", "support_category", "log_area", "aspect_ratio"]].copy()
        frame["experiment_id"] = "T4-E038"
        frame["candidate"] = candidate.name
        frame["split"] = split_name
        frame["actual_price_krw"] = eval_df[TARGET_PRICE].to_numpy(dtype=float)
        frame["pred_log_price"] = pred_log
        frame["pred_price_krw"] = pred_price
        frame["ape"] = ape
        frames.append(frame)
    return result, frames


def best_candidate(results: dict[str, Any], split_name: str, metric: str, candidates: list[str]) -> dict[str, Any]:
    values = []
    for name in candidates:
        value = results["candidates"][name]["eval"][split_name]["overall"][metric]
        values.append((name, value))
    best_name, best_value = min(values, key=lambda item: item[1])
    return {"candidate": best_name, metric: best_value}


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    train_raw = pd.read_csv(SPLIT_DIR / "track4_train.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    val_warm_raw = pd.read_csv(SPLIT_DIR / "track4_val_warm.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    test_warm_raw = pd.read_csv(SPLIT_DIR / "track4_test_warm.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    val_cold = pd.read_csv(SPLIT_DIR / "track4_val_cold.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    test_cold = pd.read_csv(SPLIT_DIR / "track4_test_cold.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).reset_index(drop=True)
    train = add_artist_train_stats(train_raw, train_raw)
    val_warm = add_artist_train_stats(train_raw, val_warm_raw)
    test_warm = add_artist_train_stats(train_raw, test_warm_raw)
    results: dict[str, Any] = {
        "experiment_id": "T4-E038",
        "hypothesis_id": ["T4-H1", "T4-H2", "T4-H3", "T4-H4", "T4-H15", "T4-H21", "T4-H23"],
        "date": date.today().isoformat(),
        "candidates": {},
    }
    pred_frames: list[pd.DataFrame] = []
    for candidate in CANDIDATES:
        if candidate.split_type == "warm":
            eval_sets = {"val_warm": val_warm, "test_warm": test_warm}
        else:
            eval_sets = {"val_cold": val_cold, "test_cold": test_cold}
        result, frames = run_candidate(candidate, train, eval_sets)
        results["candidates"][candidate.name] = result
        pred_frames.extend(frames)
    results["best"] = {
        "warm_val_median_ape": best_candidate(results, "val_warm", "median_ape", ["warm_structure_only", "warm_operational_artist_count", "warm_performance_artist_price_stats"]),
        "warm_test_median_ape": best_candidate(results, "test_warm", "median_ape", ["warm_structure_only", "warm_operational_artist_count", "warm_performance_artist_price_stats"]),
        "cold_val_median_ape": best_candidate(results, "val_cold", "median_ape", ["cold_area_only", "cold_full_size"]),
        "cold_test_median_ape": best_candidate(results, "test_cold", "median_ape", ["cold_area_only", "cold_full_size"]),
        "cold_val_p95_ape": best_candidate(results, "val_cold", "p95_ape", ["cold_area_only", "cold_full_size"]),
        "cold_test_p95_ape": best_candidate(results, "test_cold", "p95_ape", ["cold_area_only", "cold_full_size"]),
    }
    RESULT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.concat(pred_frames, ignore_index=True).to_csv(PRED_PATH, index=False)
    print(RESULT_PATH)
    print(PRED_PATH)


if __name__ == "__main__":
    main()
