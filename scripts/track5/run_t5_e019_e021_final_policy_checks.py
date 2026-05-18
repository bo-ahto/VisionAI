#!/usr/bin/env python3
"""Run Track 5 E019-E021 final policy checks."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

REPO = Path(__file__).resolve().parents[2]
SPLIT_DIR = REPO / "data" / "track5_split"
RESULT_DIR = REPO / "data" / "track5" / "results"
PRED_DIR = REPO / "data" / "track5" / "predictions"
MANIFEST_DIR = REPO / "data" / "track5" / "manifests"
RESULT_PATH = RESULT_DIR / "t5_e019_e021_final_policy_checks_metrics.json"
PRED_PATH = PRED_DIR / "t5_e019_e021_final_policy_checks_predictions.csv"
MANIFEST_PATH = MANIFEST_DIR / "track5_candidate_artifact_precheck_manifest.json"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"

WARM_EXTENDED_NUMERIC = [
    "artist_works_log",
    "artist_works_count_train",
    "artist_train_median_log_price",
    "artist_train_mean_log_price",
    "artist_train_iqr_log_price",
    "log_area",
    "aspect_ratio",
    "width_cm",
    "height_cm",
    "has_depth",
    "is_3d_candidate",
    "artist_train_q10_log_price",
    "artist_train_q25_log_price",
    "artist_train_q75_log_price",
    "artist_train_q90_log_price",
    "artist_train_min_log_price",
    "artist_train_max_log_price",
    "artist_train_std_log_price",
    "artist_train_price_span_log",
]
WARM_EXTENDED_CATEGORICAL = ["artist_key", "medium_category", "support_category", "artist_train_count_bucket"]
WARM_EXTENDED_FEATURES = WARM_EXTENDED_CATEGORICAL + WARM_EXTENDED_NUMERIC


@dataclass(frozen=True)
class FeatureSpec:
    numeric: list[str]
    categorical: list[str]


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def onehot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def load_split(name: str) -> pd.DataFrame:
    return pd.read_csv(SPLIT_DIR / f"track5_{name}.csv", low_memory=False).dropna(subset=[TARGET_LOG, TARGET_PRICE]).copy()


def count_bucket(count: pd.Series) -> pd.Series:
    return pd.cut(
        count.fillna(0),
        bins=[-np.inf, 2, 5, 10, 30, np.inf],
        labels=["le2", "le5", "le10", "le30", "gt30"],
    ).astype(str)


def artist_stats_from(reference: pd.DataFrame) -> pd.DataFrame:
    grouped = reference.groupby("artist_key")[TARGET_LOG]
    stats = grouped.agg(["median", "mean", "min", "max", "std", "count"]).rename(
        columns={
            "median": "artist_train_median_log_price",
            "mean": "artist_train_mean_log_price",
            "min": "artist_train_min_log_price",
            "max": "artist_train_max_log_price",
            "std": "artist_train_std_log_price",
            "count": "artist_works_count_train",
        }
    )
    stats["artist_train_q10_log_price"] = grouped.quantile(0.10)
    stats["artist_train_q25_log_price"] = grouped.quantile(0.25)
    stats["artist_train_q75_log_price"] = grouped.quantile(0.75)
    stats["artist_train_q90_log_price"] = grouped.quantile(0.90)
    stats["artist_train_iqr_log_price"] = stats["artist_train_q75_log_price"] - stats["artist_train_q25_log_price"]
    stats["artist_train_price_span_log"] = stats["artist_train_max_log_price"] - stats["artist_train_min_log_price"]
    stats["artist_train_count_bucket"] = count_bucket(stats["artist_works_count_train"])
    return stats


def fill_artist_stat_defaults(train: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    global_values = {
        "artist_train_median_log_price": float(train[TARGET_LOG].median()),
        "artist_train_mean_log_price": float(train[TARGET_LOG].mean()),
        "artist_train_min_log_price": float(train[TARGET_LOG].min()),
        "artist_train_max_log_price": float(train[TARGET_LOG].max()),
        "artist_train_q10_log_price": float(train[TARGET_LOG].quantile(0.10)),
        "artist_train_q25_log_price": float(train[TARGET_LOG].quantile(0.25)),
        "artist_train_q75_log_price": float(train[TARGET_LOG].quantile(0.75)),
        "artist_train_q90_log_price": float(train[TARGET_LOG].quantile(0.90)),
        "artist_train_std_log_price": float(train[TARGET_LOG].std()),
        "artist_train_iqr_log_price": float(train[TARGET_LOG].quantile(0.75) - train[TARGET_LOG].quantile(0.25)),
        "artist_train_price_span_log": float(train[TARGET_LOG].max() - train[TARGET_LOG].min()),
        "artist_works_count_train": 0.0,
    }
    for column, value in global_values.items():
        out[column] = out[column].fillna(value)
    out["artist_train_count_bucket"] = out["artist_train_count_bucket"].fillna("missing")
    out["artist_train_std_log_price"] = out["artist_train_std_log_price"].fillna(0.0)
    out["artist_works_log"] = np.log1p(out["artist_works_count_train"])
    return out


def add_artist_stats(train: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    stats = artist_stats_from(train)
    for col in stats.columns:
        if col in out.columns:
            out = out.drop(columns=[col])
    out = out.merge(stats, left_on="artist_key", right_index=True, how="left")
    return fill_artist_stat_defaults(train, out)


def add_oof_artist_stats(train: pd.DataFrame, folds: int = 5) -> pd.DataFrame:
    out = train.copy()
    stat_columns = list(artist_stats_from(train).columns)
    for col in stat_columns:
        out[col] = pd.Series([None] * len(out), dtype="object") if col == "artist_train_count_bucket" else np.nan
    kf = KFold(n_splits=folds, shuffle=True, random_state=42)
    for ref_idx, hold_idx in kf.split(train):
        ref = train.iloc[ref_idx]
        hold = train.iloc[hold_idx]
        stats = artist_stats_from(ref)
        merged = hold[["artist_key"]].merge(stats, left_on="artist_key", right_index=True, how="left")
        for col in stat_columns:
            out.iloc[hold_idx, out.columns.get_loc(col)] = merged[col].to_numpy()
    return fill_artist_stat_defaults(train, out)


def build_warm_huber() -> Pipeline:
    numeric = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())])
    categorical = Pipeline(
        [("imputer", SimpleImputer(strategy="constant", fill_value="unknown")), ("onehot", onehot_encoder())]
    )
    preprocess = ColumnTransformer(
        [("numeric", numeric, WARM_EXTENDED_NUMERIC), ("categorical", categorical, WARM_EXTENDED_CATEGORICAL)],
        remainder="drop",
    )
    model = HuberRegressor(alpha=0.0001, epsilon=1.35, max_iter=3000)
    return Pipeline([("preprocess", preprocess), ("model", model)])


def metrics(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, Any]:
    actual_log = df[TARGET_LOG].to_numpy(dtype=float)
    actual_price = df[TARGET_PRICE].to_numpy(dtype=float)
    pred_price = np.maximum(np.exp(pred_log), 1.0)
    ape = np.abs(pred_price - actual_price) / actual_price
    return {
        "rows": int(len(df)),
        "artists": int(df["artist_key"].nunique()),
        "median_ape": float(np.median(ape)),
        "mape": float(np.mean(ape)),
        "rmse_log": float(np.sqrt(mean_squared_error(actual_log, pred_log))),
        "within_30": float(np.mean(ape <= 0.30)),
        "within_50": float(np.mean(ape <= 0.50)),
        "p90_ape": float(np.quantile(ape, 0.90)),
        "p95_ape": float(np.quantile(ape, 0.95)),
    }


def e019_warm_oof_extended_recheck() -> tuple[dict[str, Any], pd.DataFrame]:
    train_raw = load_split("train")
    val_raw = load_split("val_warm")
    test_raw = load_split("test_warm")
    train = add_oof_artist_stats(train_raw)
    val = add_artist_stats(train_raw, val_raw)
    test = add_artist_stats(train_raw, test_raw)
    model = build_warm_huber()
    model.fit(train[WARM_EXTENDED_FEATURES], train[TARGET_LOG])
    output = {"n_iter": int(model.named_steps["model"].n_iter_), "metrics": {}}
    frames = []
    for split, df in [("val_warm", val), ("test_warm", test)]:
        pred_log = model.predict(df[WARM_EXTENDED_FEATURES])
        output["metrics"][split] = metrics(df, pred_log)
        pred_price = np.maximum(np.exp(pred_log), 1.0)
        actual = df[TARGET_PRICE].to_numpy(dtype=float)
        frames.append(
            pd.DataFrame(
                {
                    "experiment_id": "T5-E019",
                    "setting": "warm_oof_extended_huber_max_iter_3000",
                    "split": split,
                    "artist_key": df["artist_key"].to_numpy(),
                    "actual_price_krw": actual,
                    "pred_log_price": pred_log,
                    "pred_price_krw": pred_price,
                    "ape": np.abs(pred_price - actual) / actual,
                }
            )
        )
    return output, pd.concat(frames, ignore_index=True)


def add_cold_risk_flags(df: pd.DataFrame, train: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    medium = out["medium_category"].fillna("unknown").astype(str).str.lower()
    support = out["support_category"].fillna("unknown").astype(str).str.lower()
    out["medium_unknown"] = medium.isin(["unknown", "other", "nan", ""]).astype(int)
    out["support_unknown"] = support.isin(["unknown", "other", "nan", ""]).astype(int)
    out["is_very_large_work"] = (pd.to_numeric(out["area_cm2"], errors="coerce") >= 10000).fillna(False).astype(int)
    out["is_large_work"] = (out["log_area"] >= float(train["log_area"].quantile(0.75))).astype(int)
    out["policy_risk_score"] = out["medium_unknown"] + out["support_unknown"] + out["is_very_large_work"]
    out["policy_group"] = np.where(out["policy_risk_score"] >= 1, "caution", "standard")
    return out


def summarize_ape(df: pd.DataFrame) -> dict[str, Any]:
    ape = df["ape"].to_numpy(dtype=float)
    return {
        "rows": int(len(df)),
        "artists": int(df["artist_key"].nunique()),
        "median_ape": float(np.median(ape)),
        "mape": float(np.mean(ape)),
        "within_30": float(np.mean(ape <= 0.30)),
        "within_50": float(np.mean(ape <= 0.50)),
        "p90_ape": float(np.quantile(ape, 0.90)),
        "p95_ape": float(np.quantile(ape, 0.95)),
    }


def e020_cold_correction_policy() -> dict[str, Any]:
    train = load_split("train")
    test = load_split("test_cold").reset_index(drop=True)
    risk = add_cold_risk_flags(test, train)
    baseline = pd.read_csv(PRED_DIR / "t5_e010_final_candidate_test_predictions.csv")
    baseline = baseline[(baseline["task"] == "cold") & (baseline["candidate"] == "cold_full_size_quantile")].reset_index(drop=True)
    corrected = pd.read_csv(PRED_DIR / "t5_e014_e018_followup_improvement_predictions.csv")
    corrected = corrected[corrected["experiment_id"] == "T5-E018"].reset_index(drop=True)
    for frame in [baseline, corrected]:
        frame["policy_group"] = risk["policy_group"].to_numpy()
        frame["medium_unknown"] = risk["medium_unknown"].to_numpy()
        frame["support_unknown"] = risk["support_unknown"].to_numpy()
        frame["is_very_large_work"] = risk["is_very_large_work"].to_numpy()
    output = {
        "baseline_overall": summarize_ape(baseline),
        "corrected_overall": summarize_ape(corrected),
        "baseline_by_policy_group": {k: summarize_ape(g) for k, g in baseline.groupby("policy_group")},
        "corrected_by_policy_group": {k: summarize_ape(g) for k, g in corrected.groupby("policy_group")},
        "policy_definition": {
            "standard": "medium/support known and not very_large",
            "caution": "medium unknown or support unknown or very_large",
        },
    }
    hybrid = baseline.copy()
    standard_mask = hybrid["policy_group"] == "standard"
    for col in ["pred_log_price", "pred_price_krw", "ape"]:
        hybrid.loc[standard_mask, col] = corrected.loc[standard_mask, col].to_numpy()
    output["hybrid_standard_corrected_caution_baseline"] = summarize_ape(hybrid)
    output["hybrid_by_policy_group"] = {k: summarize_ape(g) for k, g in hybrid.groupby("policy_group")}
    return output


def e021_manifest_precheck() -> dict[str, Any]:
    required = [
        SPLIT_DIR / "track5_train.csv",
        SPLIT_DIR / "track5_val_warm.csv",
        SPLIT_DIR / "track5_val_cold.csv",
        SPLIT_DIR / "track5_test_warm.csv",
        SPLIT_DIR / "track5_test_cold.csv",
        RESULT_DIR / "t5_e010_final_candidate_test_metrics.json",
        RESULT_DIR / "t5_e019_e021_final_policy_checks_metrics.json",
        PRED_DIR / "t5_e010_final_candidate_test_predictions.csv",
        PRED_DIR / "t5_e014_e018_followup_improvement_predictions.csv",
    ]
    files = {}
    missing = []
    for path in required:
        if path.exists():
            files[str(path.relative_to(REPO))] = {"sha256": file_sha256(path), "bytes": path.stat().st_size}
        else:
            missing.append(str(path.relative_to(REPO)))
    manifest = {
        "date": date.today().isoformat(),
        "status": "ready_for_artifact_generation" if not missing else "blocked",
        "missing_files": missing,
        "final_candidates": {
            "warm": {
                "primary": "HuberRegressor + warm_full_size",
                "challenger": "HuberRegressor + OOF extended artist stats",
                "decision": "primary retained unless E019 test p95 improvement is prioritized over median simplicity",
            },
            "cold": {
                "primary": "QuantileRegressor + cold_full_size",
                "postprocess": "prediction price band correction",
                "policy": "caution when medium/support unknown or very_large",
            },
        },
        "files": files,
    }
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    output: dict[str, Any] = {
        "date": date.today().isoformat(),
        "results": {},
    }
    e019_result, e019_pred = e019_warm_oof_extended_recheck()
    output["results"]["T5-E019"] = e019_result
    output["results"]["T5-E020"] = e020_cold_correction_policy()
    RESULT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    output["results"]["T5-E021"] = e021_manifest_precheck()
    RESULT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    e019_pred.to_csv(PRED_PATH, index=False)
    print(RESULT_PATH)
    print(PRED_PATH)
    print(MANIFEST_PATH)
    print(json.dumps(output["results"], ensure_ascii=False))


if __name__ == "__main__":
    main()
