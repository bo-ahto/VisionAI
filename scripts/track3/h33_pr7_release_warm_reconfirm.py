"""Track 3 H33 — reconfirm PR7 Warm features on the release split.

PR7 had the best exploratory Warm record, but it was measured on the dev/CV
setup and included variants that are not all available in the release split.
This script retests only operationally reproducible PR7 features on the fixed
release train/warm split.
"""
from __future__ import annotations

import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parent.parent.parent
SPLIT = REPO / "data" / "release_split"
OUT_PATH = REPO / "data" / "track3_h33_pr7_release_warm_reconfirm_results.json"
H31_PATH = REPO / "data" / "track3_h31_warm_champion_feature_retest_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
SEEDS = [11, 22, 33]


def add_pr7_features(df: pd.DataFrame, artist_counts: dict[str, int]) -> pd.DataFrame:
    out = df.copy()
    medium = out["medium_category"].fillna("unknown").astype(str)
    ho = out["estimated_ho"].clip(lower=0).fillna(0)
    width = out["width_cm"].fillna(0).clip(lower=0)
    height = out["height_cm"].fillna(0).clip(lower=0)

    out["ho_bucket"] = pd.cut(
        ho,
        bins=[-0.1, 5, 20, 50, 200],
        labels=["0-5", "5-20", "20-50", "50+"],
    ).astype(str)
    out["medium_ho_bucket"] = medium + "_" + out["ho_bucket"]
    out["aspect_ratio"] = np.log(width / height.replace(0, 1)).replace([np.inf, -np.inf], 0).fillna(0)
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
    vals = np.array([row["median_ape"] for row in per_seed], dtype=float)
    return {
        "mean_median_ape": float(vals.mean()),
        "std_median_ape": float(vals.std()),
        "best_median_ape": float(vals.min()),
        "worst_median_ape": float(vals.max()),
        "delta_vs_pr7_release_baseline": float(vals.mean() - base_mean),
    }


def main() -> None:
    train_raw = pd.read_csv(SPLIT / "track3_train.csv")
    warm_raw = pd.read_csv(SPLIT / "track3_test_warm.csv")
    artist_counts = train_raw[ARTIST_COL].value_counts().to_dict()
    train = add_pr7_features(train_raw, artist_counts)
    warm = add_pr7_features(warm_raw, artist_counts)

    base_features = ["medium_category", "support_category", "has_depth", "log_area", "estimated_ho", "orientation", ARTIST_COL]
    base_cat = ["medium_category", "support_category", "orientation", ARTIST_COL]
    variants = {
        "V0_pr7_release_baseline": (base_features, base_cat),
        "V1_pr7_interaction": (base_features + ["medium_ho_bucket"], base_cat + ["medium_ho_bucket"]),
        "V2_pr7_popularity": (base_features + ["artist_works_log"], base_cat),
        "V3_pr7_aspect": (base_features + ["aspect_ratio"], base_cat),
        "V4_pr7_all_operational": (base_features + ["medium_ho_bucket", "artist_works_log", "aspect_ratio"], base_cat + ["medium_ho_bucket"]),
    }

    result = {
        "experiment_id": "H33_pr7_release_warm_reconfirm",
        "date": "2026-05-14",
        "reason": "Reconfirm PR7 operational Warm features on the fixed release split.",
        "excluded_pr7_features": {
            "source_platform": "Not available in release_split and difficult to use in production.",
        },
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

    base_mean = float(np.mean([r["median_ape"] for r in result["variants"]["V0_pr7_release_baseline"]["per_seed"]]))
    for row in result["variants"].values():
        row["summary"] = summarize(row["per_seed"], base_mean)

    h31_best = None
    if H31_PATH.exists():
        h31 = json.loads(H31_PATH.read_text())
        h31_best = h31["judgement"]["best_mean_median_ape"]
    best = min(result["variants"], key=lambda k: result["variants"][k]["summary"]["mean_median_ape"])
    best_mean = result["variants"][best]["summary"]["mean_median_ape"]
    result["judgement"] = {
        "best_pr7_release_variant": best,
        "best_pr7_release_mean_median_ape": best_mean,
        "pr7_exploration_best_mean_median_ape": 0.10306780111374098,
        "h31_best_mean_median_ape": h31_best,
        "beats_h31": bool(h31_best is not None and best_mean < h31_best),
        "note": "Lower median APE is better. This release-split retest excludes source_platform.",
    }
    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    print("H33 PR7 release warm reconfirm")
    print(f"saved: {OUT_PATH}")
    for name, row in result["variants"].items():
        s = row["summary"]
        print(f"{name:<28} mean={s['mean_median_ape']:.4f} std={s['std_median_ape']:.4f} delta={s['delta_vs_pr7_release_baseline']:+.4f}")
    print(json.dumps(result["judgement"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
