"""Track 3 H31 — retest size/ho features on the H17 Warm champion.

The H19-H22 feature experiments used a weaker Warm baseline. This script
checks whether those feature gains still hold when the H17 artist-history
Warm champion is used as the base.
"""
from __future__ import annotations

import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parent.parent.parent
SPLIT = REPO / "data" / "release_split"
OUT_PATH = REPO / "data" / "track3_h31_warm_champion_feature_retest_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
SEEDS = [11, 22, 33]

BASE_FEATURES = [
    "medium_category",
    "support_category",
    "depth_cm",
    "log_area",
    "estimated_ho",
    "orientation",
    "medium_ho_bucket",
    "aspect_ratio",
]
BASE_CAT = ["medium_category", "support_category", "orientation", "medium_ho_bucket"]
HISTORY_FEATURES = [
    "artist_works_log",
    "artist_ln_price_median",
    "artist_ln_price_mean",
    "artist_ln_price_iqr",
]


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    medium = out["medium_category"].fillna("unknown").astype(str)
    ho = out["estimated_ho"].clip(lower=0).fillna(0)
    width = out["width_cm"].fillna(0).clip(lower=0)
    height = out["height_cm"].fillna(0).clip(lower=0)
    depth = out["depth_cm"].fillna(0).clip(lower=0)
    area = np.expm1(out["log_area"].fillna(0)).clip(lower=0)

    out["ho_bucket"] = pd.cut(
        ho,
        bins=[-0.1, 5, 20, 50, 200],
        labels=["0-5", "5-20", "20-50", "50+"],
    ).astype(str)
    out["medium_ho_bucket"] = medium + "_" + out["ho_bucket"]
    out["aspect_ratio"] = np.log(width / height.replace(0, 1)).replace([np.inf, -np.inf], 0).fillna(0)
    out["ho_bucket_refined"] = pd.cut(
        ho,
        bins=[-0.1, 3, 6, 10, 20, 50, 100, 300],
        labels=["0-3", "4-6", "7-10", "11-20", "21-50", "51-100", "100+"],
    ).astype(str)
    out["log_ho"] = np.log1p(ho)
    out["is_large_ho"] = (ho >= 50).astype(int)
    out["is_extra_large_ho"] = (ho >= 100).astype(int)
    out["area_per_ho_log"] = np.log1p(area / ho.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan).fillna(0)
    out["ho_per_area_log"] = np.log1p(ho / area.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan).fillna(0)
    out["ho_area_gap_abs"] = (out["log_area"].fillna(0) - out["log_ho"]).abs()
    out["is_3d_work"] = (depth > 0).astype(int)
    volume = (width * height * depth).clip(lower=0)
    out["volume_log"] = np.log1p(volume)
    out["max_side_log"] = np.log1p(np.maximum.reduce([width.to_numpy(), height.to_numpy(), depth.to_numpy()]))
    out["min_side_log"] = np.log1p(np.minimum.reduce([width.to_numpy(), height.to_numpy(), depth.to_numpy()]))
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


def summarize(per_seed: list[dict], base_mean: float) -> dict:
    med = np.array([row["median_ape"] for row in per_seed], dtype=float)
    return {
        "mean_median_ape": float(med.mean()),
        "std_median_ape": float(med.std()),
        "best_median_ape": float(med.min()),
        "worst_median_ape": float(med.max()),
        "delta_vs_h17_champion_mean": float(med.mean() - base_mean),
    }


def main() -> None:
    train_raw = pd.read_csv(SPLIT / "track3_train.csv")
    warm_raw = pd.read_csv(SPLIT / "track3_test_warm.csv")
    hist, global_values = build_artist_history(train_raw)
    train = add_history(add_features(train_raw), hist, global_values)
    warm = add_history(add_features(warm_raw), hist, global_values)

    champion = BASE_FEATURES + [ARTIST_COL] + HISTORY_FEATURES
    champion_cat = BASE_CAT + [ARTIST_COL]
    variants = {
        "V0_h17_champion": (champion, champion_cat),
        "V1_plus_refined_ho_bucket": (champion + ["ho_bucket_refined"], champion_cat + ["ho_bucket_refined"]),
        "V2_plus_large_ho_flags": (champion + ["is_large_ho", "is_extra_large_ho"], champion_cat),
        "V3_plus_all_ho_features": (
            champion
            + ["ho_bucket_refined", "is_large_ho", "is_extra_large_ho", "area_per_ho_log", "ho_per_area_log", "ho_area_gap_abs", "log_ho"],
            champion_cat + ["ho_bucket_refined"],
        ),
        "V4_plus_3d_features": (champion + ["is_3d_work", "volume_log", "max_side_log", "min_side_log"], champion_cat),
        "V5_plus_all_ho_and_3d": (
            champion
            + [
                "ho_bucket_refined",
                "is_large_ho",
                "is_extra_large_ho",
                "area_per_ho_log",
                "ho_per_area_log",
                "ho_area_gap_abs",
                "log_ho",
                "is_3d_work",
                "volume_log",
                "max_side_log",
                "min_side_log",
            ],
            champion_cat + ["ho_bucket_refined"],
        ),
    }

    result = {
        "experiment_id": "H31_warm_champion_feature_retest",
        "date": "2026-05-14",
        "reason": "Retest H19-H30 feature gains against the H17 Warm champion baseline.",
        "seeds": SEEDS,
        "data": {"train_rows": int(len(train)), "warm_rows": int(len(warm))},
        "variants": {name: {"features": features, "categorical": cat_cols, "per_seed": []} for name, (features, cat_cols) in variants.items()},
    }

    for seed in SEEDS:
        for name, (features, cat_cols) in variants.items():
            model = train_lgb(train, features, cat_cols, seed)
            pred = model.predict(to_cat(warm, features, cat_cols))
            row = metric(warm[TARGET].values, pred)
            row["seed"] = seed
            result["variants"][name]["per_seed"].append(row)

    base_mean = float(np.mean([r["median_ape"] for r in result["variants"]["V0_h17_champion"]["per_seed"]]))
    for row in result["variants"].values():
        row["summary"] = summarize(row["per_seed"], base_mean)

    best = min(result["variants"], key=lambda k: result["variants"][k]["summary"]["mean_median_ape"])
    result["judgement"] = {
        "best_variant": best,
        "best_mean_median_ape": result["variants"][best]["summary"]["mean_median_ape"],
        "h17_champion_mean_median_ape": base_mean,
        "adopt_feature_addition": bool(result["variants"][best]["summary"]["delta_vs_h17_champion_mean"] <= -0.003),
        "note": "Lower median APE is better. Adoption requires a clear mean improvement over the H17 champion.",
    }
    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    print("H31 warm champion feature retest")
    print(f"saved: {OUT_PATH}")
    for name, row in result["variants"].items():
        s = row["summary"]
        print(f"{name:<30} mean={s['mean_median_ape']:.4f} std={s['std_median_ape']:.4f} delta={s['delta_vs_h17_champion_mean']:+.4f}")
    print(json.dumps(result["judgement"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
