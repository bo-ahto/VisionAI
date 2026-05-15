"""Track 3 H14 — medium × size combination feature confirm.

Tests whether targeted medium-size combination features improve Warm/Cold.
Baseline already includes medium_ho_bucket, so this confirms whether additional
explicit combination flags add value beyond the existing interaction.
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
OUT_PATH = REPO / "data" / "track3_h14_medium_size_combo_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"

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
]
BASE_CAT = ["medium_category", "support_category", "orientation", "medium_ho_bucket"]
COMBO_CAT = ["medium_size_bucket"]
COMBO_FLAGS = [
    "is_large_oil",
    "is_large_acrylic",
    "is_large_other",
    "is_small_drawing",
    "is_large_2d",
    "is_small_2d",
]


def add_features(df: pd.DataFrame, artist_counts: dict[str, int]) -> pd.DataFrame:
    df = df.copy()
    medium = df["medium_category"].fillna("unknown").astype(str)
    df["ho_bucket"] = pd.cut(
        df["estimated_ho"],
        bins=[-0.1, 5, 20, 50, 200],
        labels=["0-5", "5-20", "20-50", "50+"],
    ).astype(str)
    df["size_bucket"] = pd.cut(
        df["estimated_ho"],
        bins=[-0.1, 5, 20, 50, 200],
        labels=["small", "medium", "large", "xlarge"],
    ).astype(str)
    df["medium_ho_bucket"] = medium + "_" + df["ho_bucket"]
    df["medium_size_bucket"] = medium + "_" + df["size_bucket"]
    df["aspect_ratio"] = np.log(df["width_cm"] / df["height_cm"].replace(0, 1))
    df["artist_works_log"] = np.log1p(df[ARTIST_COL].map(artist_counts).fillna(0))
    is_2d = df["depth_cm"] <= 0
    is_large = df["estimated_ho"] >= 50
    is_small = df["estimated_ho"] <= 5
    df["is_large_oil"] = ((medium == "oil") & is_large).astype(int)
    df["is_large_acrylic"] = ((medium == "acrylic") & is_large).astype(int)
    df["is_large_other"] = ((medium == "other") & is_large).astype(int)
    df["is_small_drawing"] = (medium.isin(["pencil", "pastel", "ink"]) & is_small).astype(int)
    df["is_large_2d"] = (is_2d & is_large).astype(int)
    df["is_small_2d"] = (is_2d & is_small).astype(int)
    return df


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
        "p99_ape": float(np.quantile(ape, 0.99)),
        "max_ape": float(np.max(ape)),
        "ape_array": ape.tolist(),
    }


def strip_ape(row: dict) -> dict:
    return {k: v for k, v in row.items() if k != "ape_array"}


def paired(base_ape: list[float], var_ape: list[float]) -> dict:
    base = np.asarray(base_ape)
    var = np.asarray(var_ape)
    delta = var - base
    return {
        "median_delta": float(np.median(delta)),
        "mean_delta": float(np.mean(delta)),
        "win_rate_variant": float(np.mean(var < base)),
        "catastrophic_2x": float(np.mean(var > 2 * base)),
        "variant_better_10pp": int(np.sum(delta <= -0.10)),
        "variant_worse_10pp": int(np.sum(delta >= 0.10)),
    }


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


def run_cold(train: pd.DataFrame, test: pd.DataFrame, features: list[str], cat_cols: list[str]) -> np.ndarray:
    model = build_lad(features, cat_cols)
    model.fit(train[features], train[TARGET].values)
    return model.predict(test[features])


def run_warm(train: pd.DataFrame, test: pd.DataFrame, features: list[str], cat_cols: list[str]) -> np.ndarray:
    model = train_warm_lgb(train, features, cat_cols)
    return model.predict(to_cat(test, features, cat_cols))


def main() -> None:
    train_raw = pd.read_csv(SPLIT / "track3_train.csv")
    warm_raw = pd.read_csv(SPLIT / "track3_test_warm.csv")
    cold_raw = pd.read_csv(SPLIT / "track3_test_cold.csv")
    artist_counts = train_raw[ARTIST_COL].value_counts().to_dict()
    train = add_features(train_raw, artist_counts)
    warm = add_features(warm_raw, artist_counts)
    cold = add_features(cold_raw, artist_counts)

    variants = {
        "V0_base": (BASE_FEATURES, BASE_CAT),
        "V1_combo_cat": (BASE_FEATURES + COMBO_CAT, BASE_CAT + COMBO_CAT),
        "V2_combo_flags": (BASE_FEATURES + COMBO_FLAGS, BASE_CAT),
        "V3_combo_all": (BASE_FEATURES + COMBO_CAT + COMBO_FLAGS, BASE_CAT + COMBO_CAT),
    }
    result = {
        "experiment_id": "H14_medium_size_combo_confirm",
        "data": {
            "train_rows": int(len(train)),
            "test_warm_rows": int(len(warm)),
            "test_cold_rows": int(len(cold)),
        },
        "variants": {},
    }
    base_apes = {}
    for name, (features, cat_cols) in variants.items():
        warm_features = features + [ARTIST_COL]
        warm_cat = cat_cols + [ARTIST_COL]
        pred_cold = run_cold(train, cold, features, cat_cols)
        pred_warm = run_warm(train, warm, warm_features, warm_cat)
        cold_m = metric(cold[TARGET].values, pred_cold)
        warm_m = metric(warm[TARGET].values, pred_warm)
        if name == "V0_base":
            base_apes = {"cold": cold_m["ape_array"], "warm": warm_m["ape_array"]}
        result["variants"][name] = {
            "features": features,
            "cold": strip_ape(cold_m),
            "warm": strip_ape(warm_m),
            "paired_vs_base": {
                "cold": paired(base_apes["cold"], cold_m["ape_array"]) if name != "V0_base" else None,
                "warm": paired(base_apes["warm"], warm_m["ape_array"]) if name != "V0_base" else None,
            },
        }

    base_cold = result["variants"]["V0_base"]["cold"]["median_ape"]
    base_warm = result["variants"]["V0_base"]["warm"]["median_ape"]
    for row in result["variants"].values():
        row["delta_median_ape"] = {
            "cold": float(row["cold"]["median_ape"] - base_cold),
            "warm": float(row["warm"]["median_ape"] - base_warm),
        }
    best_cold = min(result["variants"], key=lambda k: result["variants"][k]["cold"]["median_ape"])
    best_warm = min(result["variants"], key=lambda k: result["variants"][k]["warm"]["median_ape"])
    result["judgement"] = {
        "best_cold": best_cold,
        "best_warm": best_warm,
        "adoptable": bool(
            best_cold != "V0_base"
            and result["variants"][best_cold]["delta_median_ape"]["cold"] <= -0.005
            and result["variants"][best_cold]["delta_median_ape"]["warm"] <= 0.005
        ),
    }
    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    print("H14 medium-size combo confirm")
    print(f"saved: {OUT_PATH}")
    for name, row in result["variants"].items():
        print(
            f"{name:<16} cold={row['cold']['median_ape']:.4f} "
            f"({row['delta_median_ape']['cold']:+.4f}) "
            f"warm={row['warm']['median_ape']:.4f} "
            f"({row['delta_median_ape']['warm']:+.4f})"
        )
    print(f"adoptable={result['judgement']['adoptable']} best_cold={best_cold} best_warm={best_warm}")


if __name__ == "__main__":
    main()
