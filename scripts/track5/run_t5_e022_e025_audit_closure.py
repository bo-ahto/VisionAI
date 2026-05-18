#!/usr/bin/env python3
"""Close Track 5 audit risks with auxiliary validation experiments.

This script does not replace the frozen Track5 split. It adds audit experiments
that check whether the current conclusions depend too much on one split, artist
name features, cold name overlap, or test-based policy choice.
"""
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
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO = Path(__file__).resolve().parents[2]
SPLIT_DIR = REPO / "data" / "track5_split"
RESULT_DIR = REPO / "data" / "track5" / "results"
PRED_DIR = REPO / "data" / "track5" / "predictions"
AUDIT_SPLIT_DIR = REPO / "data" / "track5" / "audit_splits"
RESULT_PATH = RESULT_DIR / "t5_e022_e025_audit_closure_metrics.json"
PRED_PATH = PRED_DIR / "t5_e022_e025_audit_closure_predictions.csv"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"

STRUCT_NUMERIC = ["log_area", "aspect_ratio", "width_cm", "height_cm", "has_depth", "is_3d_candidate"]
STRUCT_CATEGORICAL = ["medium_category", "support_category"]
WARM_FULL_NUMERIC = [
    "artist_works_log",
    "artist_works_count_train",
    "artist_train_median_log_price",
    "artist_train_mean_log_price",
    "artist_train_iqr_log_price",
] + STRUCT_NUMERIC
WARM_FULL_CATEGORICAL = ["artist_key"] + STRUCT_CATEGORICAL


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    numeric: list[str]
    categorical: list[str]
    model_name: str

    @property
    def features(self) -> list[str]:
        return self.categorical + self.numeric


def onehot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def load_split(name: str) -> pd.DataFrame:
    path = SPLIT_DIR / f"track5_{name}.csv"
    return pd.read_csv(path, low_memory=False).dropna(subset=[TARGET_LOG, TARGET_PRICE]).copy()


def load_full_track5_rows() -> pd.DataFrame:
    frames = [load_split(name) for name in ["train", "val_warm", "test_warm", "val_cold", "test_cold"]]
    df = pd.concat(frames, ignore_index=True)
    if "_track5_row_id" in df.columns:
        df = df.drop_duplicates("_track5_row_id")
    return df.reset_index(drop=True)


def build_pipeline(spec: FeatureSpec) -> Pipeline:
    numeric = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())])
    categorical = Pipeline(
        [("imputer", SimpleImputer(strategy="constant", fill_value="unknown")), ("onehot", onehot_encoder())]
    )
    preprocess = ColumnTransformer(
        [("numeric", numeric, spec.numeric), ("categorical", categorical, spec.categorical)],
        remainder="drop",
    )
    if spec.model_name == "huber":
        model = HuberRegressor(alpha=0.0001, epsilon=1.35, max_iter=500)
    elif spec.model_name == "quantile":
        model = QuantileRegressor(quantile=0.5, alpha=0.0001, solver="highs")
    else:
        raise ValueError(f"unknown model: {spec.model_name}")
    return Pipeline([("preprocess", preprocess), ("model", model)])


def add_artist_train_stats(train: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    grouped = train.groupby("artist_key")[TARGET_LOG]
    stats = grouped.agg(["median", "mean", "count"]).rename(
        columns={
            "median": "artist_train_median_log_price",
            "mean": "artist_train_mean_log_price",
            "count": "artist_works_count_train",
        }
    )
    stats["artist_train_iqr_log_price"] = grouped.quantile(0.75) - grouped.quantile(0.25)
    for col in stats.columns:
        if col in out.columns:
            out = out.drop(columns=[col])
    out = out.merge(stats, left_on="artist_key", right_index=True, how="left")
    out["artist_train_median_log_price"] = out["artist_train_median_log_price"].fillna(float(train[TARGET_LOG].median()))
    out["artist_train_mean_log_price"] = out["artist_train_mean_log_price"].fillna(float(train[TARGET_LOG].mean()))
    out["artist_train_iqr_log_price"] = out["artist_train_iqr_log_price"].fillna(0.0)
    out["artist_works_count_train"] = out["artist_works_count_train"].fillna(0.0)
    out["artist_works_log"] = np.log1p(out["artist_works_count_train"])
    return out


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


def summarize(values: list[float]) -> dict[str, float]:
    arr = np.asarray(values, dtype=float)
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
    }


def predict_frame(
    experiment_id: str,
    split: str,
    setting: str,
    df: pd.DataFrame,
    pred_log: np.ndarray,
    extra: dict[str, Any] | None = None,
) -> pd.DataFrame:
    actual = df[TARGET_PRICE].to_numpy(dtype=float)
    pred_price = np.maximum(np.exp(pred_log), 1.0)
    out = pd.DataFrame(
        {
            "experiment_id": experiment_id,
            "split": split,
            "setting": setting,
            "artist_key": df["artist_key"].to_numpy(),
            "artist_name_ko": df.get("artist_name_ko", pd.Series([""] * len(df))).to_numpy(),
            "actual_price_krw": actual,
            "pred_log_price": pred_log,
            "pred_price_krw": pred_price,
            "ape": np.abs(pred_price - actual) / actual,
        }
    )
    if extra:
        for key, value in extra.items():
            out[key] = value
    return out


def create_aux_split(all_rows: pd.DataFrame, seed: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    counts = all_rows.groupby("artist_key").size()
    cold_pool = counts[counts >= 3].index.to_numpy()
    cold_n = max(150, int(len(cold_pool) * 0.10))
    cold_artists = set(rng.choice(cold_pool, size=min(cold_n, len(cold_pool)), replace=False))
    cold_test = all_rows[all_rows["artist_key"].isin(cold_artists)].copy()
    train_pool = all_rows[~all_rows["artist_key"].isin(cold_artists)].copy()

    train_indices = set(train_pool.index.tolist())
    warm_indices: list[int] = []
    warm_counts = train_pool.groupby("artist_key").size()
    warm_pool = warm_counts[warm_counts >= 5].index.to_numpy()
    warm_n = max(120, int(len(warm_pool) * 0.12))
    warm_artists = set(rng.choice(warm_pool, size=min(warm_n, len(warm_pool)), replace=False))
    for artist in warm_artists:
        artist_idx = train_pool[train_pool["artist_key"] == artist].index.to_numpy()
        holdout_n = min(3, max(1, len(artist_idx) - 2))
        sampled = rng.choice(artist_idx, size=holdout_n, replace=False).tolist()
        warm_indices.extend(sampled)
        train_indices.difference_update(sampled)
    train = all_rows.loc[sorted(train_indices)].copy()
    warm_test = all_rows.loc[sorted(warm_indices)].copy()
    return train.reset_index(drop=True), warm_test.reset_index(drop=True), cold_test.reset_index(drop=True)


def run_model(train: pd.DataFrame, test: pd.DataFrame, spec: FeatureSpec) -> tuple[dict[str, Any], np.ndarray]:
    model = build_pipeline(spec)
    model.fit(train[spec.features], train[TARGET_LOG])
    pred_log = model.predict(test[spec.features])
    result = metrics(test, pred_log)
    if spec.model_name == "huber":
        result["n_iter"] = int(model.named_steps["model"].n_iter_)
    return result, pred_log


def e022_repeated_split_stability() -> tuple[dict[str, Any], pd.DataFrame]:
    all_rows = load_full_track5_rows()
    warm_spec = FeatureSpec("warm_full_size_huber", WARM_FULL_NUMERIC, WARM_FULL_CATEGORICAL, "huber")
    cold_spec = FeatureSpec("cold_full_size_quantile", STRUCT_NUMERIC, STRUCT_CATEGORICAL, "quantile")
    seeds = [20260518, 20260519, 20260520]
    rows: dict[str, Any] = {"seeds": seeds, "runs": []}
    pred_frames: list[pd.DataFrame] = []
    AUDIT_SPLIT_DIR.mkdir(parents=True, exist_ok=True)
    for seed in seeds:
        train_raw, warm_test_raw, cold_test_raw = create_aux_split(all_rows, seed)
        train_raw[["_track5_row_id", "artist_key"]].to_csv(AUDIT_SPLIT_DIR / f"t5_e022_seed_{seed}_train_rows.csv", index=False)
        warm_test_raw[["_track5_row_id", "artist_key"]].to_csv(
            AUDIT_SPLIT_DIR / f"t5_e022_seed_{seed}_warm_test_rows.csv", index=False
        )
        cold_test_raw[["_track5_row_id", "artist_key"]].to_csv(
            AUDIT_SPLIT_DIR / f"t5_e022_seed_{seed}_cold_test_rows.csv", index=False
        )
        train_warm = add_artist_train_stats(train_raw, train_raw)
        warm_test = add_artist_train_stats(train_raw, warm_test_raw)
        warm_result, warm_pred = run_model(train_warm, warm_test, warm_spec)
        cold_result, cold_pred = run_model(train_raw, cold_test_raw, cold_spec)
        rows["runs"].append(
            {
                "seed": seed,
                "train_rows": int(len(train_raw)),
                "warm_test_rows": int(len(warm_test)),
                "cold_test_rows": int(len(cold_test_raw)),
                "warm": warm_result,
                "cold": cold_result,
            }
        )
        pred_frames.append(predict_frame("T5-E022", f"seed_{seed}_warm", warm_spec.name, warm_test, warm_pred))
        pred_frames.append(predict_frame("T5-E022", f"seed_{seed}_cold", cold_spec.name, cold_test_raw, cold_pred))
    rows["summary"] = {
        "warm_median_ape": summarize([r["warm"]["median_ape"] for r in rows["runs"]]),
        "cold_median_ape": summarize([r["cold"]["median_ape"] for r in rows["runs"]]),
        "warm_p95_ape": summarize([r["warm"]["p95_ape"] for r in rows["runs"]]),
        "cold_p95_ape": summarize([r["cold"]["p95_ape"] for r in rows["runs"]]),
    }
    return rows, pd.concat(pred_frames, ignore_index=True)


def e023_warm_artist_feature_audit() -> tuple[dict[str, Any], pd.DataFrame]:
    train_raw = load_split("train")
    test_raw = load_split("test_warm")
    train = add_artist_train_stats(train_raw, train_raw)
    test = add_artist_train_stats(train_raw, test_raw)
    specs = [
        FeatureSpec("structure_only_huber", STRUCT_NUMERIC, STRUCT_CATEGORICAL, "huber"),
        FeatureSpec("plus_artist_key_huber", STRUCT_NUMERIC, ["artist_key"] + STRUCT_CATEGORICAL, "huber"),
        FeatureSpec(
            "plus_artist_history_huber",
            ["artist_works_log", "artist_works_count_train"] + STRUCT_NUMERIC,
            ["artist_key"] + STRUCT_CATEGORICAL,
            "huber",
        ),
        FeatureSpec("warm_full_size_huber", WARM_FULL_NUMERIC, WARM_FULL_CATEGORICAL, "huber"),
        FeatureSpec(
            "no_artist_key_stats_only_huber",
            WARM_FULL_NUMERIC,
            STRUCT_CATEGORICAL,
            "huber",
        ),
    ]
    output: dict[str, Any] = {"results": {}, "slices": {}}
    frames: list[pd.DataFrame] = []
    for spec in specs:
        result, pred = run_model(train, test, spec)
        output["results"][spec.name] = {"features": spec.features, "metrics": result}
        pred_df = predict_frame("T5-E023", "test_warm", spec.name, test, pred)
        pred_df["artist_works_count_train"] = test["artist_works_count_train"].to_numpy()
        frames.append(pred_df)
        slice_rows: dict[str, Any] = {}
        for label, mask in {
            "train_count_le5": test["artist_works_count_train"] <= 5,
            "train_count_6_20": (test["artist_works_count_train"] > 5) & (test["artist_works_count_train"] <= 20),
            "train_count_gt20": test["artist_works_count_train"] > 20,
        }.items():
            sub = pred_df[mask.to_numpy()]
            slice_rows[label] = {
                "rows": int(len(sub)),
                "artists": int(sub["artist_key"].nunique()),
                "median_ape": float(sub["ape"].median()) if len(sub) else None,
                "p95_ape": float(sub["ape"].quantile(0.95)) if len(sub) else None,
            }
        output["slices"][spec.name] = slice_rows
    return output, pd.concat(frames, ignore_index=True)


def e024_cold_name_overlap_audit() -> dict[str, Any]:
    train = load_split("train")
    test = load_split("test_cold").reset_index(drop=True)
    pred = pd.read_csv(PRED_DIR / "t5_e010_final_candidate_test_predictions.csv")
    pred = pred[(pred["task"] == "cold") & (pred["candidate"] == "cold_full_size_quantile")].reset_index(drop=True)
    train_names = set(train["artist_name_ko"].dropna().astype(str))
    train_orig_names = set(train["artist_name_ko_orig"].dropna().astype(str))
    test_names = test["artist_name_ko"].fillna("").astype(str)
    test_orig_names = test["artist_name_ko_orig"].fillna("").astype(str)
    name_overlap = test_names.isin(train_names) | test_orig_names.isin(train_orig_names)
    groups = {
        "strict_cold_name_no_overlap": ~name_overlap,
        "cold_name_overlap": name_overlap,
    }
    output: dict[str, Any] = {
        "train_artist_key_overlap": int(test["artist_key"].isin(set(train["artist_key"])).sum()),
        "name_overlap_rows": int(name_overlap.sum()),
        "name_overlap_artists": int(test.loc[name_overlap, "artist_key"].nunique()),
        "groups": {},
    }
    for label, mask in groups.items():
        sub = pred[mask.to_numpy()]
        output["groups"][label] = {
            "rows": int(len(sub)),
            "artists": int(test.loc[mask, "artist_key"].nunique()),
            "median_ape": float(sub["ape"].median()) if len(sub) else None,
            "p95_ape": float(sub["ape"].quantile(0.95)) if len(sub) else None,
            "within_50": float((sub["ape"] <= 0.50).mean()) if len(sub) else None,
        }
    return output


def add_cold_risk_flags(df: pd.DataFrame, train: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    medium = out["medium_category"].fillna("unknown").astype(str).str.lower()
    support = out["support_category"].fillna("unknown").astype(str).str.lower()
    out["medium_unknown"] = medium.isin(["unknown", "other", "nan", ""]).astype(int)
    out["support_unknown"] = support.isin(["unknown", "other", "nan", ""]).astype(int)
    out["is_very_large_work"] = (pd.to_numeric(out["area_cm2"], errors="coerce") >= 10000).fillna(False).astype(int)
    out["policy_risk_score"] = out["medium_unknown"] + out["support_unknown"] + out["is_very_large_work"]
    out["policy_group"] = np.where(out["policy_risk_score"] >= 1, "caution", "standard")
    return out


def residual_table(calib: pd.DataFrame, bins: int = 6) -> pd.Series:
    tmp = calib.copy()
    tmp["band"] = pd.qcut(tmp["pred_log_price"], q=bins, duplicates="drop")
    tmp["log_residual"] = np.log(tmp["actual_price_krw"].clip(lower=1.0)) - tmp["pred_log_price"]
    return tmp.groupby("band", observed=False)["log_residual"].median()


def apply_residual_correction(df: pd.DataFrame, table: pd.Series) -> pd.DataFrame:
    out = df.copy()
    bands = table.index
    correction = []
    for value in out["pred_log_price"]:
        matched = 0.0
        for band, residual in table.items():
            if value in band:
                matched = float(residual)
                break
        correction.append(matched)
    out["corrected_pred_log_price"] = out["pred_log_price"] + np.asarray(correction)
    out["corrected_pred_price_krw"] = np.maximum(np.exp(out["corrected_pred_log_price"]), 1.0)
    out["corrected_ape"] = np.abs(out["corrected_pred_price_krw"] - out["actual_price_krw"]) / out["actual_price_krw"]
    return out


def ape_summary(df: pd.DataFrame, column: str = "ape") -> dict[str, Any]:
    ape = df[column].to_numpy(dtype=float)
    return {
        "rows": int(len(df)),
        "median_ape": float(np.median(ape)),
        "within_50": float(np.mean(ape <= 0.50)),
        "p95_ape": float(np.quantile(ape, 0.95)),
    }


def e025_validation_policy_retest() -> tuple[dict[str, Any], pd.DataFrame]:
    train = load_split("train")
    val_raw = load_split("val_cold").reset_index(drop=True)
    test_raw = load_split("test_cold").reset_index(drop=True)
    val_pred = pd.read_csv(PRED_DIR / "t5_e008_candidate_model_comparison_predictions.csv")
    val_pred = val_pred[
        (val_pred["task"] == "cold")
        & (val_pred["feature_set"] == "cold_full_size")
        & (val_pred["model"] == "quantile_median")
    ].reset_index(drop=True)
    test_pred = pd.read_csv(PRED_DIR / "t5_e010_final_candidate_test_predictions.csv")
    test_pred = test_pred[(test_pred["task"] == "cold") & (test_pred["candidate"] == "cold_full_size_quantile")].reset_index(drop=True)

    val_risk = add_cold_risk_flags(val_raw, train)
    test_risk = add_cold_risk_flags(test_raw, train)
    val = val_pred.join(val_risk[["artist_key", "policy_group"]], rsuffix="_risk")
    test = test_pred.join(test_risk[["artist_key", "policy_group"]], rsuffix="_risk")

    artists = np.array(sorted(val["artist_key"].unique()))
    rng = np.random.default_rng(20260518)
    calib_artists = set(rng.choice(artists, size=max(1, int(len(artists) * 0.5)), replace=False))
    calib = val[val["artist_key"].isin(calib_artists)].copy()
    policy_val = val[~val["artist_key"].isin(calib_artists)].copy()
    table = residual_table(calib)
    corrected_policy_val = apply_residual_correction(policy_val, table)
    policy_decision: dict[str, str] = {}
    for group in ["standard", "caution"]:
        sub = corrected_policy_val[corrected_policy_val["policy_group"] == group]
        if len(sub) == 0:
            policy_decision[group] = "baseline"
            continue
        before = float(sub["ape"].median())
        after = float(sub["corrected_ape"].median())
        policy_decision[group] = "corrected" if after < before else "baseline"

    final_table = residual_table(val)
    test_corrected = apply_residual_correction(test, final_table)
    test_corrected["hybrid_ape"] = np.where(
        test_corrected["policy_group"].map(policy_decision) == "corrected",
        test_corrected["corrected_ape"],
        test_corrected["ape"],
    )
    test_corrected["hybrid_pred_price_krw"] = np.where(
        test_corrected["policy_group"].map(policy_decision) == "corrected",
        test_corrected["corrected_pred_price_krw"],
        test_corrected["pred_price_krw"],
    )
    output = {
        "calibration_artists": int(len(calib_artists)),
        "policy_validation_artists": int(policy_val["artist_key"].nunique()),
        "policy_decision_from_validation": policy_decision,
        "policy_validation": {
            "baseline": ape_summary(policy_val, "ape"),
            "corrected": ape_summary(corrected_policy_val, "corrected_ape"),
        },
        "test_fixed_policy": {
            "baseline": ape_summary(test_corrected, "ape"),
            "corrected_all": ape_summary(test_corrected, "corrected_ape"),
            "hybrid": ape_summary(test_corrected, "hybrid_ape"),
        },
        "test_fixed_policy_by_group": {},
    }
    for group, sub in test_corrected.groupby("policy_group"):
        output["test_fixed_policy_by_group"][group] = {
            "baseline": ape_summary(sub, "ape"),
            "corrected": ape_summary(sub, "corrected_ape"),
            "hybrid": ape_summary(sub, "hybrid_ape"),
        }
    return output, test_corrected


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    output: dict[str, Any] = {
        "date": date.today().isoformat(),
        "experiments": {},
    }
    frames: list[pd.DataFrame] = []
    output["experiments"]["T5-E022"], pred = e022_repeated_split_stability()
    frames.append(pred)
    output["experiments"]["T5-E023"], pred = e023_warm_artist_feature_audit()
    frames.append(pred)
    output["experiments"]["T5-E024"] = e024_cold_name_overlap_audit()
    output["experiments"]["T5-E025"], policy_pred = e025_validation_policy_retest()
    policy_pred["experiment_id"] = "T5-E025"
    policy_pred["setting"] = "validation_selected_cold_policy"
    policy_pred["split"] = "test_cold"
    frames.append(policy_pred)
    RESULT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.concat(frames, ignore_index=True, sort=False).to_csv(PRED_PATH, index=False)
    print(RESULT_PATH)
    print(PRED_PATH)
    print(json.dumps(output["experiments"], ensure_ascii=False))


if __name__ == "__main__":
    main()
