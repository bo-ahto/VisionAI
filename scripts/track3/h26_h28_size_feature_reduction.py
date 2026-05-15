"""Track 3 H26-H28 — size feature reduction suite.

Tests whether size-related features can be reduced without losing Warm/Cold
performance. Covers:
- H26: size feature redundancy reduction
- H27: estimated_ho vs log_area
- H28: width/height replacement by log_area + aspect_ratio
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
OUT_PATH = REPO / "data" / "track3_h26_h28_size_feature_reduction_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"

BASE_CAT = ["medium_category", "support_category", "orientation", "medium_ho_bucket"]
COMMON_NON_SIZE = [
    "medium_category",
    "support_category",
    "orientation",
    "medium_ho_bucket",
    "artist_works_log",
]


def add_features(df: pd.DataFrame, artist_counts: dict[str, int]) -> pd.DataFrame:
    out = df.copy()
    medium = out["medium_category"].fillna("unknown").astype(str)
    out["ho_bucket"] = pd.cut(
        out["estimated_ho"],
        bins=[-0.1, 5, 20, 50, 200],
        labels=["0-5", "5-20", "20-50", "50+"],
    ).astype(str)
    out["medium_ho_bucket"] = medium + "_" + out["ho_bucket"]
    out["aspect_ratio"] = np.log(out["width_cm"] / out["height_cm"].replace(0, 1))
    out["log_ho"] = np.log1p(out["estimated_ho"])
    out["artist_works_log"] = np.log1p(out[ARTIST_COL].map(artist_counts).fillna(0))
    return out


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
        "ape_array": ape.tolist(),
    }


def paired(base_ape: list[float], var_ape: list[float]) -> dict:
    base = np.asarray(base_ape)
    var = np.asarray(var_ape)
    delta = var - base
    return {
        "median_delta": float(np.median(delta)),
        "mean_delta": float(np.mean(delta)),
        "variant_win_rate": float(np.mean(var < base)),
        "variant_worse_10pp": int(np.sum(delta >= 0.10)),
        "variant_better_10pp": int(np.sum(delta <= -0.10)),
    }


def strip_ape(row: dict) -> dict:
    return {k: v for k, v in row.items() if k != "ape_array"}


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
    ds_tr = lgb.Dataset(
        to_cat(train_df.iloc[tr_idx], features, cat_cols),
        train_df.iloc[tr_idx][TARGET].values,
        categorical_feature=cat_cols,
    )
    ds_val = lgb.Dataset(
        to_cat(train_df.iloc[val_idx], features, cat_cols),
        train_df.iloc[val_idx][TARGET].values,
        categorical_feature=cat_cols,
        reference=ds_tr,
    )
    return lgb.train(params, ds_tr, num_boost_round=2000, valid_sets=[ds_val], callbacks=[lgb.early_stopping(30, verbose=False)])


def main() -> None:
    train_raw = pd.read_csv(SPLIT / "track3_train.csv")
    warm_raw = pd.read_csv(SPLIT / "track3_test_warm.csv")
    cold_raw = pd.read_csv(SPLIT / "track3_test_cold.csv")
    artist_counts = train_raw[ARTIST_COL].value_counts().to_dict()

    train = add_features(train_raw, artist_counts)
    warm = add_features(warm_raw, artist_counts)
    cold = add_features(cold_raw, artist_counts)

    variants = {
        "V0_all_size": COMMON_NON_SIZE + ["depth_cm", "width_cm", "height_cm", "log_area", "estimated_ho", "aspect_ratio"],
        "V1_no_width_height": COMMON_NON_SIZE + ["depth_cm", "log_area", "estimated_ho", "aspect_ratio"],
        "V2_log_area_only": COMMON_NON_SIZE + ["depth_cm", "log_area", "aspect_ratio"],
        "V3_ho_only": COMMON_NON_SIZE + ["depth_cm", "estimated_ho"],
        "V4_log_area_no_aspect": COMMON_NON_SIZE + ["depth_cm", "log_area"],
        "V5_log_ho_bucket": COMMON_NON_SIZE + ["depth_cm", "log_ho"],
    }

    result = {
        "experiment_id": "H26_H28_size_feature_reduction",
        "data": {
            "train_rows": int(len(train)),
            "test_warm_rows": int(len(warm)),
            "test_cold_rows": int(len(cold)),
        },
        "variants": {},
    }

    base_apes: dict[str, list[float]] = {}
    for name, features in variants.items():
        cat_cols = [c for c in BASE_CAT if c in features]
        cold_model = build_lad(features, cat_cols)
        cold_model.fit(train[features], train[TARGET].values)
        cold_pred = cold_model.predict(cold[features])

        warm_features = features + [ARTIST_COL]
        warm_cat = cat_cols + [ARTIST_COL]
        warm_model = train_warm_lgb(train, warm_features, warm_cat)
        warm_pred = warm_model.predict(to_cat(warm, warm_features, warm_cat))

        cold_m = metric(cold[TARGET].values, cold_pred)
        warm_m = metric(warm[TARGET].values, warm_pred)
        if name == "V0_all_size":
            base_apes = {"cold": cold_m["ape_array"], "warm": warm_m["ape_array"]}
        result["variants"][name] = {
            "features": features,
            "categorical": cat_cols,
            "cold": strip_ape(cold_m),
            "warm": strip_ape(warm_m),
            "paired_vs_base": {
                "cold": paired(base_apes["cold"], cold_m["ape_array"]) if name != "V0_all_size" else None,
                "warm": paired(base_apes["warm"], warm_m["ape_array"]) if name != "V0_all_size" else None,
            },
        }

    base_cold = result["variants"]["V0_all_size"]["cold"]["median_ape"]
    base_warm = result["variants"]["V0_all_size"]["warm"]["median_ape"]
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
        "can_remove_width_height": bool(
            result["variants"]["V1_no_width_height"]["delta_median_ape"]["cold"] <= 0.005
            and result["variants"]["V1_no_width_height"]["delta_median_ape"]["warm"] <= 0.005
        ),
        "log_area_only_acceptable": bool(
            result["variants"]["V2_log_area_only"]["delta_median_ape"]["cold"] <= 0.01
            and result["variants"]["V2_log_area_only"]["delta_median_ape"]["warm"] <= 0.01
        ),
        "ho_only_acceptable": bool(
            result["variants"]["V3_ho_only"]["delta_median_ape"]["cold"] <= 0.01
            and result["variants"]["V3_ho_only"]["delta_median_ape"]["warm"] <= 0.01
        ),
    }
    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    print("H26-H28 size feature reduction")
    print(f"saved: {OUT_PATH}")
    for name, row in result["variants"].items():
        print(
            f"{name:<22} cold={row['cold']['median_ape']:.4f} "
            f"({row['delta_median_ape']['cold']:+.4f}) "
            f"warm={row['warm']['median_ape']:.4f} "
            f"({row['delta_median_ape']['warm']:+.4f})"
        )
    print(f"best_cold={best_cold} best_warm={best_warm}")
    print(
        "can_remove_width_height="
        f"{result['judgement']['can_remove_width_height']} "
        "log_area_only_acceptable="
        f"{result['judgement']['log_area_only_acceptable']} "
        "ho_only_acceptable="
        f"{result['judgement']['ho_only_acceptable']}"
    )


if __name__ == "__main__":
    main()
