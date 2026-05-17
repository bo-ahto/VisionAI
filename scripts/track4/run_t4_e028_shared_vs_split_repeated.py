#!/usr/bin/env python3
"""Run Track 4 E028 repeated shared-vs-split validation."""
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
RESULT_PATH = RESULT_DIR / "t4_e028_shared_vs_split_repeated_metrics.json"
PRED_PATH = PRED_DIR / "t4_e028_shared_vs_split_repeated_predictions.csv"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"
SEEDS = [11, 22, 33, 44, 55]

STRUCTURE_NUMERIC = ["log_area", "aspect_ratio"]
STRUCTURE_CATEGORICAL = ["medium_category"]
WARM_NUMERIC = STRUCTURE_NUMERIC + ["artist_works_log", "artist_works_count_train"]
WARM_CATEGORICAL = STRUCTURE_CATEGORICAL + ["support_category", "artist_key"]

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
class Fold:
    seed: int
    train: pd.DataFrame
    warm: pd.DataFrame
    cold: pd.DataFrame


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


def make_model(policy: str) -> tuple[Pipeline, list[str]]:
    if policy == "shared_structure":
        numeric = STRUCTURE_NUMERIC
        categorical = STRUCTURE_CATEGORICAL
        model = QuantileRegressor(quantile=0.5, alpha=0.0001, solver="highs")
    elif policy == "split_warm":
        numeric = WARM_NUMERIC
        categorical = WARM_CATEGORICAL
        model = Ridge(alpha=10.0, random_state=42)
    elif policy == "split_cold":
        numeric = STRUCTURE_NUMERIC
        categorical = STRUCTURE_CATEGORICAL
        model = QuantileRegressor(quantile=0.5, alpha=0.0001, solver="highs")
    else:
        raise ValueError(policy)
    features = categorical + numeric
    validate_features(features)
    return Pipeline([("preprocess", build_preprocessor(numeric, categorical)), ("model", model)]), features


def recompute_artist_counts(train: pd.DataFrame, *evals: pd.DataFrame) -> tuple[pd.DataFrame, list[pd.DataFrame]]:
    counts = train["artist_key"].value_counts()
    out_train = train.copy()
    out_train["artist_works_count_train"] = out_train["artist_key"].map(counts).fillna(0).astype(int)
    out_train["artist_works_log"] = np.log1p(out_train["artist_works_count_train"])
    out_evals: list[pd.DataFrame] = []
    for df in evals:
        out = df.copy()
        out["artist_works_count_train"] = out["artist_key"].map(counts).fillna(0).astype(int)
        out["artist_works_log"] = np.log1p(out["artist_works_count_train"])
        out_evals.append(out)
    return out_train, out_evals


def make_fold(df: pd.DataFrame, seed: int) -> Fold:
    rng = np.random.default_rng(seed)
    artists = np.array(sorted(df["artist_key"].unique()))
    cold_n = max(50, int(len(artists) * 0.08))
    cold_artists = set(rng.choice(artists, size=cold_n, replace=False))

    cold = df[df["artist_key"].isin(cold_artists)].copy()
    remaining = df[~df["artist_key"].isin(cold_artists)].copy()

    warm_candidates = remaining.groupby("artist_key").filter(lambda group: len(group) >= 2)
    warm_idx = (
        warm_candidates.groupby("artist_key", group_keys=False)
        .sample(n=1, random_state=seed)
        .index
    )
    warm = remaining.loc[warm_idx].copy()
    train = remaining.drop(index=warm_idx).copy()
    train, [warm, cold] = recompute_artist_counts(train, warm, cold)
    return Fold(seed=seed, train=train, warm=warm, cold=cold)


def price_from_log(values: np.ndarray) -> np.ndarray:
    return np.exp(values)


def metric_dict(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
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


def fit_predict(train: pd.DataFrame, eval_df: pd.DataFrame, policy: str) -> tuple[np.ndarray, list[str]]:
    model, features = make_model(policy)
    model.fit(train[features], train[TARGET_LOG])
    return model.predict(eval_df[features]), features


def aggregate(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    metrics = ["median_ape", "mape", "rmse_log", "within_30", "within_50", "p95_ape"]
    out: dict[str, dict[str, float]] = {}
    for metric in metrics:
        values = np.array([row[metric] for row in rows], dtype=float)
        out[metric] = {
            "mean": float(values.mean()),
            "std": float(values.std(ddof=0)),
            "min": float(values.min()),
            "max": float(values.max()),
        }
    return out


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(SPLIT_DIR / "track4_train.csv").dropna(subset=[TARGET_LOG, TARGET_PRICE]).copy()

    fold_results: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []
    for seed in SEEDS:
        fold = make_fold(df, seed)
        shared_model, shared_features = make_model("shared_structure")
        shared_model.fit(fold.train[shared_features], fold.train[TARGET_LOG])
        for split_name, eval_df in [("warm", fold.warm), ("cold", fold.cold)]:
            pred_log = shared_model.predict(eval_df[shared_features])
            metrics = metric_dict(eval_df, pred_log)
            fold_results.append({"seed": seed, "policy": "shared_structure", "split": split_name, **metrics})
            pred_frames.append(make_pred_frame(seed, "shared_structure", split_name, eval_df, pred_log))

        warm_pred, _ = fit_predict(fold.train, fold.warm, "split_warm")
        cold_pred, _ = fit_predict(fold.train, fold.cold, "split_cold")
        for policy, split_name, eval_df, pred_log in [
            ("split_policy", "warm", fold.warm, warm_pred),
            ("split_policy", "cold", fold.cold, cold_pred),
        ]:
            metrics = metric_dict(eval_df, pred_log)
            fold_results.append({"seed": seed, "policy": policy, "split": split_name, **metrics})
            pred_frames.append(make_pred_frame(seed, policy, split_name, eval_df, pred_log))

    summary: dict[str, Any] = {}
    for policy in ["shared_structure", "split_policy"]:
        summary[policy] = {}
        for split_name in ["warm", "cold"]:
            rows = [row for row in fold_results if row["policy"] == policy and row["split"] == split_name]
            summary[policy][split_name] = aggregate(rows)

    results = {
        "experiment_id": "T4-E028",
        "hypothesis_id": ["T4-H21", "T4-H22"],
        "date": date.today().isoformat(),
        "seeds": SEEDS,
        "fold_results": fold_results,
        "summary": summary,
        "policies": {
            "shared_structure": "하나의 구조-only Quantile 모델을 Warm/Cold에 모두 적용",
            "split_policy": "Warm은 artist_key 포함 Ridge, Cold는 구조-only Quantile 적용",
        },
    }
    RESULT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.concat(pred_frames, ignore_index=True).to_csv(PRED_PATH, index=False)
    print(RESULT_PATH)
    print(PRED_PATH)


def make_pred_frame(seed: int, policy: str, split_name: str, df: pd.DataFrame, pred_log: np.ndarray) -> pd.DataFrame:
    pred_price = price_from_log(pred_log)
    ape = np.abs(pred_price - df[TARGET_PRICE].to_numpy(dtype=float)) / df[TARGET_PRICE].to_numpy(dtype=float)
    return pd.DataFrame(
        {
            "experiment_id": "T4-E028",
            "seed": seed,
            "policy": policy,
            "split": split_name,
            "artist_key": df["artist_key"].to_numpy(),
            "actual_price_krw": df[TARGET_PRICE].to_numpy(dtype=float),
            "pred_log_price": pred_log,
            "pred_price_krw": pred_price,
            "ape": ape,
            "artist_works_count_train": df["artist_works_count_train"].to_numpy(),
        }
    )


if __name__ == "__main__":
    main()
