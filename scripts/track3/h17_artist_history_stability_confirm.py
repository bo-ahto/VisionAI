"""Track 3 H17 — artist history feature stability confirm."""
from __future__ import annotations

import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parent.parent.parent
SPLIT = REPO / "data" / "release_split"
OUT_PATH = REPO / "data" / "track3_h17_artist_history_stability_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
SEEDS = [11, 22, 33]

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
        "median_ape": float(np.median(ape)),
        "mape": float(np.mean(ape)),
        "rmse_log": float(np.sqrt(np.mean(log_resid**2))),
        "within_30pct": float(np.mean(ape <= 0.30)),
        "within_50pct": float(np.mean(ape <= 0.50)),
    }


def to_cat(df: pd.DataFrame, features: list[str], cat_cols: list[str]) -> pd.DataFrame:
    out = df[features].copy()
    for col in cat_cols:
        if col in out.columns:
            out[col] = out[col].astype("category")
    return out


def train_lgb(train_df: pd.DataFrame, features: list[str], cat_cols: list[str], seed: int) -> lgb.Booster:
    rng = np.random.default_rng(seed)
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
        "seed": seed,
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
        "experiment_id": "H17_artist_history_stability_confirm",
        "seeds": SEEDS,
        "variants": {name: {"per_seed": []} for name in variants},
    }
    for seed in SEEDS:
        for name, (features, cat_cols) in variants.items():
            model = train_lgb(train, features, cat_cols, seed)
            pred = model.predict(to_cat(warm, features, cat_cols))
            row = metric(warm[TARGET].values, pred)
            row["seed"] = seed
            result["variants"][name]["per_seed"].append(row)

    base_mean = np.mean([r["median_ape"] for r in result["variants"]["V0_artist_name"]["per_seed"]])
    for name, row in result["variants"].items():
        vals = np.array([r["median_ape"] for r in row["per_seed"]])
        row["summary"] = {
            "mean_median_ape": float(vals.mean()),
            "std_median_ape": float(vals.std()),
            "best_median_ape": float(vals.min()),
            "worst_median_ape": float(vals.max()),
            "delta_vs_artist_name_mean": float(vals.mean() - base_mean),
        }

    best = min(result["variants"], key=lambda k: result["variants"][k]["summary"]["mean_median_ape"])
    result["judgement"] = {
        "best_variant": best,
        "history_stable": bool(
            result["variants"]["V2_artist_name_history"]["summary"]["delta_vs_artist_name_mean"] <= -0.05
            and result["variants"]["V2_artist_name_history"]["summary"]["std_median_ape"] <= 0.02
        ),
        "temporal_caveat": "stability is confirmed on release split, but temporal-safe feature generation is still blocked without date columns",
    }
    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    print("H17 artist history stability confirm")
    print(f"saved: {OUT_PATH}")
    for name, row in result["variants"].items():
        s = row["summary"]
        print(f"{name:<24} mean={s['mean_median_ape']:.4f} std={s['std_median_ape']:.4f} delta={s['delta_vs_artist_name_mean']:+.4f}")
    print(f"best={best} stable={result['judgement']['history_stable']}")


if __name__ == "__main__":
    main()
