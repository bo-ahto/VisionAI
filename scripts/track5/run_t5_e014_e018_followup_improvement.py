#!/usr/bin/env python3
"""Run Track 5 follow-up improvement experiments E014-E018."""
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
from sklearn.linear_model import HuberRegressor, QuantileRegressor
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

REPO = Path(__file__).resolve().parents[2]
SPLIT_DIR = REPO / "data" / "track5_split"
RESULT_DIR = REPO / "data" / "track5" / "results"
PRED_DIR = REPO / "data" / "track5" / "predictions"
RESULT_PATH = RESULT_DIR / "t5_e014_e018_followup_improvement_metrics.json"
PRED_PATH = PRED_DIR / "t5_e014_e018_followup_improvement_predictions.csv"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    numeric: list[str]
    categorical: list[str]

    @property
    def features(self) -> list[str]:
        return self.categorical + self.numeric


WARM_BASE_NUMERIC = [
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
]
WARM_BASE_CATEGORICAL = ["artist_key", "medium_category", "support_category"]
WARM_EXTENDED_NUMERIC = WARM_BASE_NUMERIC + [
    "artist_train_q10_log_price",
    "artist_train_q25_log_price",
    "artist_train_q75_log_price",
    "artist_train_q90_log_price",
    "artist_train_min_log_price",
    "artist_train_max_log_price",
    "artist_train_std_log_price",
    "artist_train_price_span_log",
]
WARM_EXTENDED_CATEGORICAL = WARM_BASE_CATEGORICAL + ["artist_train_count_bucket"]
COLD_BASE_NUMERIC = ["log_area", "aspect_ratio", "width_cm", "height_cm", "has_depth", "is_3d_candidate"]
COLD_BASE_CATEGORICAL = ["medium_category", "support_category"]
COLD_MISSING_NUMERIC = COLD_BASE_NUMERIC + ["medium_unknown", "support_unknown", "missing_info_count"]


def onehot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def load_split(name: str) -> pd.DataFrame:
    return pd.read_csv(SPLIT_DIR / f"track5_{name}.csv", low_memory=False).dropna(subset=[TARGET_LOG, TARGET_PRICE]).copy()


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


def build_pipeline(spec: FeatureSpec, estimator: Any, scale_numeric: bool = True) -> Pipeline:
    numeric_steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
    if scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))
    numeric = Pipeline(numeric_steps)
    categorical = Pipeline(
        [("imputer", SimpleImputer(strategy="constant", fill_value="unknown")), ("onehot", onehot_encoder())]
    )
    preprocess = ColumnTransformer(
        [("numeric", numeric, spec.numeric), ("categorical", categorical, spec.categorical)],
        remainder="drop",
    )
    return Pipeline([("preprocess", preprocess), ("model", estimator)])


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


def add_artist_stats(train: pd.DataFrame, df: pd.DataFrame, stats: pd.DataFrame | None = None) -> pd.DataFrame:
    out = df.copy()
    if stats is None:
        stats = artist_stats_from(train)
    out = out.merge(stats, left_on="artist_key", right_index=True, how="left", suffixes=("", "_stat"))
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


def add_missing_flags(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    medium = out["medium_category"].fillna("unknown").astype(str).str.lower()
    support = out["support_category"].fillna("unknown").astype(str).str.lower()
    out["medium_unknown"] = medium.isin(["unknown", "other", "nan", ""]).astype(int)
    out["support_unknown"] = support.isin(["unknown", "other", "nan", ""]).astype(int)
    out["missing_info_count"] = out["medium_unknown"] + out["support_unknown"]
    return out


def fit_predict(name: str, train: pd.DataFrame, eval_df: pd.DataFrame, spec: FeatureSpec, estimator: Any, split: str) -> tuple[dict[str, Any], pd.DataFrame]:
    model = build_pipeline(spec, estimator)
    model.fit(train[spec.features], train[TARGET_LOG])
    pred_log = model.predict(eval_df[spec.features])
    pred_price = np.maximum(np.exp(pred_log), 1.0)
    actual = eval_df[TARGET_PRICE].to_numpy(dtype=float)
    frame = pd.DataFrame(
        {
            "experiment_id": name.split(":")[0],
            "setting": name,
            "split": split,
            "artist_key": eval_df["artist_key"].to_numpy(),
            "actual_price_krw": actual,
            "pred_log_price": pred_log,
            "pred_price_krw": pred_price,
            "ape": np.abs(pred_price - actual) / actual,
        }
    )
    return metrics(eval_df, pred_log), frame


def cold_fallback_experiment(train: pd.DataFrame, val: pd.DataFrame) -> tuple[dict[str, Any], pd.DataFrame]:
    spec = FeatureSpec("cold_missing_flags", COLD_MISSING_NUMERIC, COLD_BASE_CATEGORICAL)
    global_model = build_pipeline(spec, QuantileRegressor(quantile=0.5, alpha=0.0001, solver="highs"))
    global_model.fit(train[spec.features], train[TARGET_LOG])
    pred = global_model.predict(val[spec.features])
    support_unknown_mask = val["support_unknown"] == 1
    train_unknown = train[train["support_unknown"] == 1]
    val_pred = pred.copy()
    used_fallback = False
    if len(train_unknown) >= 200 and support_unknown_mask.any():
        unknown_model = build_pipeline(spec, QuantileRegressor(quantile=0.5, alpha=0.0001, solver="highs"))
        unknown_model.fit(train_unknown[spec.features], train_unknown[TARGET_LOG])
        val_pred[support_unknown_mask.to_numpy()] = unknown_model.predict(val.loc[support_unknown_mask, spec.features])
        used_fallback = True
    pred_price = np.maximum(np.exp(val_pred), 1.0)
    actual = val[TARGET_PRICE].to_numpy(dtype=float)
    frame = pd.DataFrame(
        {
            "experiment_id": "T5-E017",
            "setting": "cold_support_unknown_fallback",
            "split": "val_cold",
            "artist_key": val["artist_key"].to_numpy(),
            "actual_price_krw": actual,
            "pred_log_price": val_pred,
            "pred_price_krw": pred_price,
            "ape": np.abs(pred_price - actual) / actual,
            "support_unknown": val["support_unknown"].to_numpy(),
        }
    )
    result = {
        "used_fallback": used_fallback,
        "train_support_unknown_rows": int(len(train_unknown)),
        "overall": metrics(val, val_pred),
        "support_known": {
            "rows": int((~support_unknown_mask).sum()),
            "median_ape": float(frame.loc[~support_unknown_mask, "ape"].median()),
            "p95_ape": float(frame.loc[~support_unknown_mask, "ape"].quantile(0.95)),
        },
        "support_unknown": {
            "rows": int(support_unknown_mask.sum()),
            "median_ape": float(frame.loc[support_unknown_mask, "ape"].median()),
            "p95_ape": float(frame.loc[support_unknown_mask, "ape"].quantile(0.95)),
        },
    }
    return result, frame


def price_band_correction() -> tuple[dict[str, Any], pd.DataFrame]:
    val_pred = pd.read_csv(PRED_DIR / "t5_e008_candidate_model_comparison_predictions.csv")
    test_pred = pd.read_csv(PRED_DIR / "t5_e010_final_candidate_test_predictions.csv")
    val = val_pred[
        (val_pred["task"] == "cold")
        & (val_pred["feature_set"] == "cold_full_size")
        & (val_pred["model"] == "quantile_median")
    ].copy()
    test = test_pred[(test_pred["task"] == "cold") & (test_pred["candidate"] == "cold_full_size_quantile")].copy()
    val["pred_band"] = pd.qcut(val["pred_log_price"], q=5, duplicates="drop")
    corrections = val.groupby("pred_band", observed=True).apply(
        lambda g: float(np.median(np.log(g["actual_price_krw"].to_numpy(dtype=float)) - g["pred_log_price"].to_numpy(dtype=float)))
    )
    bins = [interval.left for interval in corrections.index] + [corrections.index[-1].right]
    test["pred_band"] = pd.cut(test["pred_log_price"], bins=bins, include_lowest=True)
    correction_map = {interval: corrections.loc[interval] for interval in corrections.index}
    default_correction = float(np.median(np.log(val["actual_price_krw"].to_numpy(dtype=float)) - val["pred_log_price"].to_numpy(dtype=float)))
    test["correction"] = test["pred_band"].map(correction_map).astype(float).fillna(default_correction)
    corrected_log = test["pred_log_price"].to_numpy(dtype=float) + test["correction"].to_numpy(dtype=float)
    pseudo = test.rename(columns={"actual_price_krw": TARGET_PRICE}).copy()
    pseudo[TARGET_LOG] = np.log(pseudo[TARGET_PRICE].to_numpy(dtype=float))
    result = {"baseline": metrics(pseudo, test["pred_log_price"].to_numpy(dtype=float)), "corrected": metrics(pseudo, corrected_log)}
    pred_price = np.maximum(np.exp(corrected_log), 1.0)
    actual = test["actual_price_krw"].to_numpy(dtype=float)
    frame = pd.DataFrame(
        {
            "experiment_id": "T5-E018",
            "setting": "cold_pred_price_band_correction",
            "split": "test_cold",
            "artist_key": test["artist_key"].to_numpy(),
            "actual_price_krw": actual,
            "pred_log_price": corrected_log,
            "pred_price_krw": pred_price,
            "ape": np.abs(pred_price - actual) / actual,
        }
    )
    return result, frame


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    train_raw = load_split("train")
    val_warm_raw = load_split("val_warm")
    val_cold_raw = load_split("val_cold")

    train_warm = add_artist_stats(train_raw, train_raw)
    val_warm = add_artist_stats(train_raw, val_warm_raw)
    train_warm_oof = add_oof_artist_stats(train_raw)
    train_cold = add_missing_flags(train_raw)
    val_cold = add_missing_flags(val_cold_raw)

    output: dict[str, Any] = {"date": date.today().isoformat(), "results": {}}
    frames: list[pd.DataFrame] = []

    warm_base = FeatureSpec("warm_full_size", WARM_BASE_NUMERIC, WARM_BASE_CATEGORICAL)
    warm_extended = FeatureSpec("warm_extended_artist_stats", WARM_EXTENDED_NUMERIC, WARM_EXTENDED_CATEGORICAL)
    # Follow-up exploration uses the same Huber family with a smaller iteration
    # budget so candidate checks finish quickly. E011 already confirmed max_iter
    # 3000 is the safer final training setting.
    huber = HuberRegressor(alpha=0.0001, epsilon=1.35, max_iter=1000)
    for exp_id, train_df, spec in [
        ("T5-E014:warm_base_stats", train_warm, warm_base),
        ("T5-E014:warm_extended_stats", train_warm, warm_extended),
        ("T5-E015:warm_oof_base_stats", train_warm_oof, warm_base),
        ("T5-E015:warm_oof_extended_stats", train_warm_oof, warm_extended),
    ]:
        result, frame = fit_predict(exp_id, train_df, val_warm, spec, huber, "val_warm")
        output["results"][exp_id] = result
        frames.append(frame)

    cold_base = FeatureSpec("cold_full_size", COLD_BASE_NUMERIC, COLD_BASE_CATEGORICAL)
    cold_missing = FeatureSpec("cold_missing_flags", COLD_MISSING_NUMERIC, COLD_BASE_CATEGORICAL)
    quantile = QuantileRegressor(quantile=0.5, alpha=0.0001, solver="highs")
    for exp_id, spec in [
        ("T5-E016:cold_base", cold_base),
        ("T5-E016:cold_missing_flags", cold_missing),
    ]:
        result, frame = fit_predict(exp_id, train_cold, val_cold, spec, quantile, "val_cold")
        output["results"][exp_id] = result
        frames.append(frame)

    result, frame = cold_fallback_experiment(train_cold, val_cold)
    output["results"]["T5-E017:cold_support_unknown_fallback"] = result
    frames.append(frame)

    result, frame = price_band_correction()
    output["results"]["T5-E018:cold_price_band_correction"] = result
    frames.append(frame)

    RESULT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.concat(frames, ignore_index=True).to_csv(PRED_PATH, index=False)
    print(RESULT_PATH)
    print(PRED_PATH)
    print(json.dumps(output["results"], ensure_ascii=False))


if __name__ == "__main__":
    main()
