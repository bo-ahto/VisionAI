"""Track 3 H10 — artist history feature confirm.

Tests whether structured artist history features from the training split can
replace or complement raw artist_name_ko for Warm prediction.
"""
from __future__ import annotations

import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parent.parent.parent
SPLIT = REPO / "data" / "release_split"
OUT_PATH = REPO / "data" / "track3_h10_artist_history_feature_results.json"

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
    hist = grouped.agg(["count", "median", "mean", "quantile"]).rename(
        columns={"count": "artist_count", "median": "artist_ln_price_median", "mean": "artist_ln_price_mean"}
    )
    q75 = grouped.quantile(0.75)
    q25 = grouped.quantile(0.25)
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


def to_cat(df: pd.DataFrame, features: list[str], cat_cols: list[str]) -> pd.DataFrame:
    out = df[features].copy()
    for col in cat_cols:
        if col in out.columns:
            out[col] = out[col].astype("category")
    return out


def train_lgb(train_df: pd.DataFrame, features: list[str], cat_cols: list[str]) -> lgb.Booster:
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


def main() -> None:
    train_raw = pd.read_csv(SPLIT / "track3_train.csv")
    warm_raw = pd.read_csv(SPLIT / "track3_test_warm.csv")
    hist, global_values = build_artist_history(train_raw)
    train = add_history(add_base_features(train_raw), hist, global_values)
    warm = add_history(add_base_features(warm_raw), hist, global_values)

    variants = {
        "V0_artist_name": (COMMON_FEATURES + [ARTIST_COL], COMMON_CAT + [ARTIST_COL]),
        "V1_history_only": (COMMON_FEATURES + HISTORY_FEATURES, COMMON_CAT),
        "V2_artist_name_history": (COMMON_FEATURES + [ARTIST_COL] + HISTORY_FEATURES, COMMON_CAT + [ARTIST_COL]),
    }

    result = {
        "experiment_id": "H10_artist_history_feature_confirm",
        "data": {
            "train_rows": int(len(train)),
            "test_warm_rows": int(len(warm)),
            "train_artists": int(train[ARTIST_COL].nunique()),
            "test_warm_artists": int(warm[ARTIST_COL].nunique()),
            "note": "artist history features are computed from train split only; no temporal transaction date is available",
        },
        "variants": {},
    }

    base_ape = None
    for name, (features, cat_cols) in variants.items():
        model = train_lgb(train, features, cat_cols)
        pred = model.predict(to_cat(warm, features, cat_cols))
        m = metric(warm[TARGET].values, pred)
        if name == "V0_artist_name":
            base_ape = m["ape_array"]
        result["variants"][name] = {
            "features": features,
            "categorical": cat_cols,
            "warm": strip_ape(m),
            "paired_vs_artist_name": paired(base_ape, m["ape_array"]) if name != "V0_artist_name" else None,
        }

    base = result["variants"]["V0_artist_name"]["warm"]["median_ape"]
    for row in result["variants"].values():
        row["delta_median_ape_vs_artist_name"] = float(row["warm"]["median_ape"] - base)

    best = min(result["variants"], key=lambda k: result["variants"][k]["warm"]["median_ape"])
    result["judgement"] = {
        "best_variant": best,
        "history_replaces_artist_name": bool(
            result["variants"]["V1_history_only"]["delta_median_ape_vs_artist_name"] <= 0.005
        ),
        "history_complements_artist_name": bool(
            result["variants"]["V2_artist_name_history"]["delta_median_ape_vs_artist_name"] <= -0.005
        ),
        "adoptable": bool(best != "V0_artist_name"),
        "temporal_caveat": "requires transaction-date-safe feature generation before production use",
    }

    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    print("H10 artist history feature confirm")
    print(f"saved: {OUT_PATH}")
    for name, row in result["variants"].items():
        print(f"{name:<24} warm={row['warm']['median_ape']:.4f} ({row['delta_median_ape_vs_artist_name']:+.4f})")
    print(
        f"adoptable={result['judgement']['adoptable']} "
        f"best={best} temporal_caveat=True"
    )


if __name__ == "__main__":
    main()
