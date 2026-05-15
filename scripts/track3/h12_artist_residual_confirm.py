"""Track 3 H12 — artist baseline + artwork residual confirm."""
from __future__ import annotations

import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parent.parent.parent
SPLIT = REPO / "data" / "release_split"
OUT_PATH = REPO / "data" / "track3_h12_artist_residual_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"

COMMON_FEATURES = [
    "medium_category",
    "support_category",
    "depth_cm",
    "log_area",
    "estimated_ho",
    "orientation",
    "medium_ho_bucket",
    "aspect_ratio",
]
COMMON_CAT = ["medium_category", "support_category", "orientation", "medium_ho_bucket"]
HISTORY_FEATURES = [
    "artist_works_log",
    "artist_ln_price_median",
    "artist_ln_price_mean",
    "artist_ln_price_iqr",
]


def add_base_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    medium = out["medium_category"].fillna("unknown").astype(str)
    out["ho_bucket"] = pd.cut(
        out["estimated_ho"],
        bins=[-0.1, 5, 20, 50, 200],
        labels=["0-5", "5-20", "20-50", "50+"],
    ).astype(str)
    out["medium_ho_bucket"] = medium + "_" + out["ho_bucket"]
    out["aspect_ratio"] = np.log(out["width_cm"] / out["height_cm"].replace(0, 1))
    return out


def build_artist_history(train: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    grouped = train.groupby(ARTIST_COL)[TARGET]
    q75 = grouped.quantile(0.75)
    q25 = grouped.quantile(0.25)
    hist = grouped.agg(["count", "median", "mean"]).rename(
        columns={"count": "artist_count", "median": "artist_ln_price_median", "mean": "artist_ln_price_mean"}
    )
    hist["artist_ln_price_iqr"] = q75 - q25
    global_values = {
        "artist_count": 0.0,
        "artist_ln_price_median": float(train[TARGET].median()),
        "artist_ln_price_mean": float(train[TARGET].mean()),
        "artist_ln_price_iqr": float((q75 - q25).median()),
    }
    return hist, global_values


def add_history(df: pd.DataFrame, hist: pd.DataFrame, global_values: dict) -> pd.DataFrame:
    out = df.copy()
    joined = out[[ARTIST_COL]].join(hist, on=ARTIST_COL)
    for col, default in global_values.items():
        out[col] = joined[col].fillna(default)
    out["artist_works_log"] = np.log1p(out["artist_count"])
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
    }


def to_cat(df: pd.DataFrame, features: list[str], cat_cols: list[str]) -> pd.DataFrame:
    out = df[features].copy()
    for col in cat_cols:
        if col in out.columns:
            out[col] = out[col].astype("category")
    return out


def train_lgb(train_df: pd.DataFrame, features: list[str], cat_cols: list[str], target: np.ndarray) -> lgb.Booster:
    rng = np.random.default_rng(42)
    perm = rng.permutation(len(train_df))
    cut = int(len(train_df) * 0.1)
    val_idx = perm[:cut]
    tr_idx = perm[cut:]
    x_tr = to_cat(train_df.iloc[tr_idx], features, cat_cols)
    x_val = to_cat(train_df.iloc[val_idx], features, cat_cols)
    y_tr = target[tr_idx]
    y_val = target[val_idx]
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


def main() -> None:
    train_raw = pd.read_csv(SPLIT / "track3_train.csv")
    warm_raw = pd.read_csv(SPLIT / "track3_test_warm.csv")
    hist, global_values = build_artist_history(train_raw)
    train = add_history(add_base_features(train_raw), hist, global_values)
    warm = add_history(add_base_features(warm_raw), hist, global_values)

    direct_features = COMMON_FEATURES + [ARTIST_COL] + HISTORY_FEATURES
    direct_cat = COMMON_CAT + [ARTIST_COL]
    residual_features = COMMON_FEATURES + HISTORY_FEATURES
    residual_cat = COMMON_CAT

    direct_model = train_lgb(train, direct_features, direct_cat, train[TARGET].values)
    direct_pred = direct_model.predict(to_cat(warm, direct_features, direct_cat))

    baseline_pred = warm["artist_ln_price_median"].values
    residual_target = train[TARGET].values - train["artist_ln_price_median"].values
    residual_model = train_lgb(train, residual_features, residual_cat, residual_target)
    residual_pred = warm["artist_ln_price_median"].values + residual_model.predict(to_cat(warm, residual_features, residual_cat))

    result = {
        "experiment_id": "H12_artist_residual_confirm",
        "data": {
            "train_rows": int(len(train)),
            "test_warm_rows": int(len(warm)),
            "note": "artist baseline is computed from train split only; temporal-safe transaction history is still required",
        },
        "variants": {
            "V0_artist_median_only": metric(warm[TARGET].values, baseline_pred),
            "V1_direct_artist_history_model": metric(warm[TARGET].values, direct_pred),
            "V2_artist_baseline_plus_residual": metric(warm[TARGET].values, residual_pred),
        },
    }
    base = result["variants"]["V1_direct_artist_history_model"]["median_ape"]
    result["judgement"] = {
        "residual_beats_direct": bool(result["variants"]["V2_artist_baseline_plus_residual"]["median_ape"] <= base - 0.005),
        "residual_interpretable": True,
        "adoptable": bool(result["variants"]["V2_artist_baseline_plus_residual"]["median_ape"] <= base + 0.005),
        "temporal_caveat": "requires transaction-date-safe artist baseline before production use",
    }
    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    print("H12 artist residual confirm")
    print(f"saved: {OUT_PATH}")
    for name, row in result["variants"].items():
        print(f"{name:<36} warm={row['median_ape']:.4f} W30={row['within_30pct']:.4f}")
    print(
        f"adoptable={result['judgement']['adoptable']} "
        f"residual_beats_direct={result['judgement']['residual_beats_direct']}"
    )


if __name__ == "__main__":
    main()
