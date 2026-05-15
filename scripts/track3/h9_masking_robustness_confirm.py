"""Track 3 H9 — masking robustness confirm.

Compares a normal model with a model trained after intentionally masking
some inputs. The goal is to check whether masking during training improves
robustness when operational inputs are incomplete.
"""
from __future__ import annotations

import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import QuantileRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO = Path(__file__).resolve().parent.parent.parent
SPLIT = REPO / "data" / "release_split"
OUT_PATH = REPO / "data" / "track3_h9_masking_robustness_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"

RAW_CAT = ["medium_category", "support_category", "orientation"]
RAW_SIZE = ["depth_cm", "width_cm", "height_cm", "log_area", "estimated_ho"]

BASE_FEATURES = [
    "medium_category",
    "support_category",
    "depth_cm",
    "log_area",
    "estimated_ho",
    "orientation",
    "medium_ho_bucket",
    "artist_works_log",
    "aspect_ratio",
    "missing_medium",
    "missing_support",
    "missing_size",
    "missing_count",
    "info_completeness_score",
]
BASE_CAT = ["medium_category", "support_category", "orientation", "medium_ho_bucket"]


def metric(y_true_ln: np.ndarray, y_pred_ln: np.ndarray) -> dict:
    y_true = np.exp(y_true_ln)
    y_pred = np.exp(y_pred_ln)
    ape = np.abs(y_pred - y_true) / y_true
    log_resid = y_pred_ln - y_true_ln
    return {
        "n": int(len(y_true)),
        "median_ape": float(np.median(ape)),
        "mape": float(np.mean(ape)),
        "rmse_log": float(np.sqrt(np.mean(log_resid**2))),
        "within_30pct": float(np.mean(ape <= 0.30)),
        "within_50pct": float(np.mean(ape <= 0.50)),
        "p95_ape": float(np.quantile(ape, 0.95)),
    }


def paired(base_pred: np.ndarray, robust_pred: np.ndarray, y_true_ln: np.ndarray) -> dict:
    y_true = np.exp(y_true_ln)
    base_ape = np.abs(np.exp(base_pred) - y_true) / y_true
    robust_ape = np.abs(np.exp(robust_pred) - y_true) / y_true
    delta = robust_ape - base_ape
    return {
        "median_delta": float(np.median(delta)),
        "mean_delta": float(np.mean(delta)),
        "robust_win_rate": float(np.mean(robust_ape < base_ape)),
        "robust_worse_10pp": int(np.sum(delta >= 0.10)),
        "robust_better_10pp": int(np.sum(delta <= -0.10)),
    }


def strip_missing_markers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in RAW_CAT:
        df[col] = df[col].fillna("unknown").astype(str)
    for col in RAW_SIZE:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def apply_mask(df: pd.DataFrame, scenario: str, rng: np.random.Generator | None = None) -> pd.DataFrame:
    df = strip_missing_markers(df)
    out = df.copy()
    if rng is None:
        mask = np.ones(len(out), dtype=bool)
    else:
        mask = rng.random(len(out)) < 0.25

    if scenario in {"material", "material_size"}:
        out.loc[mask, ["medium_category", "support_category"]] = "__missing__"
    if scenario in {"size", "material_size"}:
        out.loc[mask, RAW_SIZE] = np.nan
    return out


def add_features(df: pd.DataFrame, artist_counts: dict[str, int], medians: dict[str, float]) -> pd.DataFrame:
    df = strip_missing_markers(df)
    out = df.copy()

    out["missing_medium"] = (out["medium_category"].astype(str) == "__missing__").astype(int)
    out["missing_support"] = (out["support_category"].astype(str) == "__missing__").astype(int)
    out["missing_size"] = out[RAW_SIZE].isna().any(axis=1).astype(int)

    for col in RAW_SIZE:
        out[col] = out[col].fillna(medians[col])

    out["ho_bucket"] = pd.cut(
        out["estimated_ho"],
        bins=[-0.1, 5, 20, 50, 200],
        labels=["0-5", "5-20", "20-50", "50+"],
    ).astype(str)
    out["medium_ho_bucket"] = out["medium_category"].astype(str) + "_" + out["ho_bucket"]
    out["aspect_ratio"] = np.log(out["width_cm"] / out["height_cm"].replace(0, 1))
    out["artist_works_log"] = np.log1p(out[ARTIST_COL].map(artist_counts).fillna(0))
    out["missing_count"] = out[["missing_medium", "missing_support", "missing_size"]].sum(axis=1)
    out["info_completeness_score"] = 1.0 - (out["missing_count"] / 3.0)
    return out


def build_lad(features: list[str], cat_cols: list[str]) -> Pipeline:
    cat = [c for c in features if c in cat_cols]
    num = [c for c in features if c not in cat_cols]
    prep = ColumnTransformer(
        [
            ("cat", OneHotEncoder(handle_unknown="ignore", drop="first", max_categories=100), cat),
            ("num", StandardScaler(), num),
        ]
    )
    return Pipeline([("prep", prep), ("est", QuantileRegressor(quantile=0.5, solver="highs", alpha=0.0))])


def to_cat(df: pd.DataFrame, features: list[str], cat_cols: list[str]) -> pd.DataFrame:
    out = df[features].copy()
    for col in cat_cols:
        if col in out.columns:
            out[col] = out[col].astype("category")
    return out


def train_warm_lgb(train_df: pd.DataFrame, features: list[str], cat_cols: list[str]) -> lgb.Booster:
    rng = np.random.default_rng(42)
    perm = rng.permutation(len(train_df))
    cut = int(len(train_df) * 0.1)
    val_idx = perm[:cut]
    tr_idx = perm[cut:]
    x_tr = to_cat(train_df.iloc[tr_idx], features, cat_cols)
    x_val = to_cat(train_df.iloc[val_idx], features, cat_cols)
    y_tr = train_df.iloc[tr_idx][TARGET].values
    y_val = train_df.iloc[val_idx][TARGET].values
    params = {
        "objective": "regression",
        "metric": "rmse",
        "learning_rate": 0.04,
        "num_leaves": 198,
        "min_data_in_leaf": 75,
        "feature_fraction": 0.987,
        "bagging_fraction": 0.978,
        "bagging_freq": 5,
        "reg_alpha": 0.36,
        "reg_lambda": 4.75,
        "verbose": -1,
        "seed": 42,
    }
    ds_tr = lgb.Dataset(x_tr, y_tr, categorical_feature=cat_cols)
    ds_val = lgb.Dataset(x_val, y_val, categorical_feature=cat_cols, reference=ds_tr)
    return lgb.train(params, ds_tr, num_boost_round=2000, valid_sets=[ds_val], callbacks=[lgb.early_stopping(30, verbose=False)])


def predict_cold(train_df: pd.DataFrame, test_df: pd.DataFrame, features: list[str], cat_cols: list[str]) -> np.ndarray:
    model = build_lad(features, cat_cols)
    model.fit(train_df[features], train_df[TARGET].values)
    return model.predict(test_df[features])


def main() -> None:
    train_raw = pd.read_csv(SPLIT / "track3_train.csv")
    warm_raw = pd.read_csv(SPLIT / "track3_test_warm.csv")
    cold_raw = pd.read_csv(SPLIT / "track3_test_cold.csv")

    artist_counts = train_raw[ARTIST_COL].value_counts().to_dict()
    medians = {col: float(pd.to_numeric(train_raw[col], errors="coerce").median()) for col in RAW_SIZE}

    clean_train = add_features(train_raw, artist_counts, medians)
    rng = np.random.default_rng(42)
    masked_train_raw = apply_mask(train_raw, "material", rng)
    masked_train_raw = apply_mask(masked_train_raw, "size", rng)
    masked_train = add_features(masked_train_raw, artist_counts, medians)

    scenarios = {
        "clean": ("none", None),
        "material_missing": ("material", None),
        "size_missing": ("size", None),
        "material_size_missing": ("material_size", None),
    }

    warm_features = BASE_FEATURES + [ARTIST_COL]
    warm_cat = BASE_CAT + [ARTIST_COL]
    cold_features = BASE_FEATURES
    cold_cat = BASE_CAT

    cold_base_model = build_lad(cold_features, cold_cat)
    cold_base_model.fit(clean_train[cold_features], clean_train[TARGET].values)
    cold_robust_model = build_lad(cold_features, cold_cat)
    cold_robust_model.fit(masked_train[cold_features], masked_train[TARGET].values)

    warm_base_model = train_warm_lgb(clean_train, warm_features, warm_cat)
    warm_robust_model = train_warm_lgb(masked_train, warm_features, warm_cat)

    result = {
        "experiment_id": "H9_masking_robustness_confirm",
        "data": {
            "train_rows": int(len(train_raw)),
            "test_warm_rows": int(len(warm_raw)),
            "test_cold_rows": int(len(cold_raw)),
            "train_mask_rate": {
                "missing_medium": float(masked_train["missing_medium"].mean()),
                "missing_support": float(masked_train["missing_support"].mean()),
                "missing_size": float(masked_train["missing_size"].mean()),
            },
        },
        "features": {
            "base_features": BASE_FEATURES,
            "warm_extra": [ARTIST_COL],
            "categorical": BASE_CAT,
        },
        "scenarios": {},
    }

    for scenario_name, (mask_scenario, _) in scenarios.items():
        if mask_scenario == "none":
            warm_raw_s = warm_raw.copy()
            cold_raw_s = cold_raw.copy()
        else:
            warm_raw_s = apply_mask(warm_raw, mask_scenario)
            cold_raw_s = apply_mask(cold_raw, mask_scenario)
        warm_s = add_features(warm_raw_s, artist_counts, medians)
        cold_s = add_features(cold_raw_s, artist_counts, medians)

        cold_base_pred = cold_base_model.predict(cold_s[cold_features])
        cold_robust_pred = cold_robust_model.predict(cold_s[cold_features])
        warm_base_pred = warm_base_model.predict(to_cat(warm_s, warm_features, warm_cat))
        warm_robust_pred = warm_robust_model.predict(to_cat(warm_s, warm_features, warm_cat))

        result["scenarios"][scenario_name] = {
            "cold": {
                "baseline": metric(cold_s[TARGET].values, cold_base_pred),
                "masked_training": metric(cold_s[TARGET].values, cold_robust_pred),
                "paired": paired(cold_base_pred, cold_robust_pred, cold_s[TARGET].values),
            },
            "warm": {
                "baseline": metric(warm_s[TARGET].values, warm_base_pred),
                "masked_training": metric(warm_s[TARGET].values, warm_robust_pred),
                "paired": paired(warm_base_pred, warm_robust_pred, warm_s[TARGET].values),
            },
        }

    clean_cold_delta = (
        result["scenarios"]["clean"]["cold"]["masked_training"]["median_ape"]
        - result["scenarios"]["clean"]["cold"]["baseline"]["median_ape"]
    )
    clean_warm_delta = (
        result["scenarios"]["clean"]["warm"]["masked_training"]["median_ape"]
        - result["scenarios"]["clean"]["warm"]["baseline"]["median_ape"]
    )
    masked_cold_deltas = [
        result["scenarios"][s]["cold"]["masked_training"]["median_ape"]
        - result["scenarios"][s]["cold"]["baseline"]["median_ape"]
        for s in ["material_missing", "size_missing", "material_size_missing"]
    ]
    masked_warm_deltas = [
        result["scenarios"][s]["warm"]["masked_training"]["median_ape"]
        - result["scenarios"][s]["warm"]["baseline"]["median_ape"]
        for s in ["material_missing", "size_missing", "material_size_missing"]
    ]
    result["judgement"] = {
        "adoptable": bool(
            clean_cold_delta <= 0.005
            and clean_warm_delta <= 0.005
            and np.median(masked_cold_deltas) < -0.005
            and np.median(masked_warm_deltas) < -0.005
        ),
        "clean_delta": {
            "cold": float(clean_cold_delta),
            "warm": float(clean_warm_delta),
        },
        "masked_scenario_median_delta": {
            "cold": float(np.median(masked_cold_deltas)),
            "warm": float(np.median(masked_warm_deltas)),
        },
    }

    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    print("H9 masking robustness confirm")
    print(f"saved: {OUT_PATH}")
    for scenario_name, row in result["scenarios"].items():
        c0 = row["cold"]["baseline"]["median_ape"]
        c1 = row["cold"]["masked_training"]["median_ape"]
        w0 = row["warm"]["baseline"]["median_ape"]
        w1 = row["warm"]["masked_training"]["median_ape"]
        print(f"{scenario_name:<22} cold={c0:.4f}->{c1:.4f} warm={w0:.4f}->{w1:.4f}")
    print(f"adoptable={result['judgement']['adoptable']}")


if __name__ == "__main__":
    main()
