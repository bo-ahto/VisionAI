"""Track 3 H34-H43 follow-up validation.

This script tests the next set of hypotheses after H31/H32:
- Warm: whether the H31 champion is stable by artist-history slices.
- Cold: whether the H32 3D conditional fallback should be more narrowly applied.
- Policy: whether separate Warm/Cold models remain preferable to one shared model.
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
OUT_PATH = REPO / "data" / "track3_h34_h43_followup_validation_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
SEEDS = [11, 22, 33]

BASE_CAT = ["medium_category", "support_category", "orientation", "medium_ho_bucket"]
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
HISTORY_FEATURES = [
    "artist_works_log",
    "artist_ln_price_median",
    "artist_ln_price_mean",
    "artist_ln_price_iqr",
]
HO_3D_FEATURES = [
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
]
WARM_H31_FEATURES = BASE_FEATURES + [ARTIST_COL] + HISTORY_FEATURES + HO_3D_FEATURES
WARM_H31_CAT = BASE_CAT + [ARTIST_COL, "ho_bucket_refined"]

COLD_CAT_COLS = [
    "medium_category",
    "support_category",
    "orientation",
    "medium_ho_bucket",
    "ho_bucket_refined",
    "area_size_bucket",
]
COLD_BASE_FEATURES = [
    "medium_category",
    "support_category",
    "orientation",
    "medium_ho_bucket",
    "artist_works_log",
    "depth_cm",
    "log_area",
    "estimated_ho",
    "aspect_ratio",
    "ho_bucket_refined",
    "is_large_ho",
    "is_extra_large_ho",
    "area_per_ho_log",
    "ho_per_area_log",
    "ho_area_gap_abs",
    "log_ho",
]
COLD_3D_FEATURES = COLD_BASE_FEATURES + ["is_3d_work", "volume_log", "max_side_log", "min_side_log"]


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
    out["area_size_bucket"] = pd.cut(
        out["log_area"].fillna(0),
        bins=[-0.1, 6.0, 7.0, 8.0, 9.0, 20.0],
        labels=["tiny", "small", "medium", "large", "xlarge"],
    ).astype(str)
    out["is_tiny_work"] = (out["log_area"].fillna(0) < 6.0).astype(int)
    out["is_very_large_area"] = (out["log_area"].fillna(0) >= 9.0).astype(int)
    out["is_3d_work"] = (depth > 0).astype(int)
    out["is_2d_work"] = (depth <= 0).astype(int)
    volume = (width * height * depth).clip(lower=0)
    out["volume_log"] = np.log1p(volume)
    out["max_side_log"] = np.log1p(np.maximum.reduce([width.to_numpy(), height.to_numpy(), depth.to_numpy()]))
    out["min_side_log"] = np.log1p(np.minimum.reduce([width.to_numpy(), height.to_numpy(), depth.to_numpy()]))
    return out


def build_artist_history(train: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
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


def add_history(df: pd.DataFrame, hist: pd.DataFrame, global_values: dict[str, float]) -> pd.DataFrame:
    out = df.copy()
    joined = out[[ARTIST_COL]].join(hist, on=ARTIST_COL)
    for col, default in global_values.items():
        out[col] = joined[col].fillna(default)
    out["artist_works_log"] = np.log1p(out["artist_count"])
    return out


def metric(y_true_ln: np.ndarray, y_pred_ln: np.ndarray) -> dict[str, float | int]:
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
        "p90_ape": float(np.quantile(ape, 0.90)),
        "p95_ape": float(np.quantile(ape, 0.95)),
    }


def ape_values(y_true_ln: np.ndarray, y_pred_ln: np.ndarray) -> np.ndarray:
    return np.abs(np.exp(y_pred_ln) - np.exp(y_true_ln)) / np.exp(y_true_ln)


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
        categorical_feature=[col for col in cat_cols if col in features],
    )
    ds_val = lgb.Dataset(
        to_cat(train_df.iloc[val_idx], features, cat_cols),
        train_df.iloc[val_idx][TARGET].values,
        categorical_feature=[col for col in cat_cols if col in features],
        reference=ds_tr,
    )
    return lgb.train(params, ds_tr, num_boost_round=2000, valid_sets=[ds_val], callbacks=[lgb.early_stopping(30, verbose=False)])


def build_lad(features: list[str]) -> Pipeline:
    cat = [col for col in features if col in COLD_CAT_COLS]
    num = [col for col in features if col not in COLD_CAT_COLS]
    prep = ColumnTransformer(
        [
            ("cat", OneHotEncoder(handle_unknown="ignore", drop="first", max_categories=100), cat),
            ("num", StandardScaler(), num),
        ]
    )
    return Pipeline([("prep", prep), ("est", QuantileRegressor(quantile=0.5, solver="highs", alpha=0.0))])


def slice_metric_table(df: pd.DataFrame, pred: np.ndarray, masks: dict[str, np.ndarray], min_n: int = 20) -> dict[str, dict]:
    out = {}
    for name, mask in masks.items():
        if int(mask.sum()) < min_n:
            continue
        out[name] = metric(df.loc[mask, TARGET].values, pred[mask])
    return out


def average_predictions(train: pd.DataFrame, test: pd.DataFrame, features: list[str], cat_cols: list[str], seeds: list[int]) -> tuple[np.ndarray, list[dict]]:
    preds = []
    per_seed = []
    for seed in seeds:
        model = train_lgb(train, features, cat_cols, seed)
        pred = model.predict(to_cat(test, features, cat_cols))
        preds.append(pred)
        row = metric(test[TARGET].values, pred)
        row["seed"] = seed
        per_seed.append(row)
    return np.mean(preds, axis=0), per_seed


def h38_variant(train: pd.DataFrame, warm: pd.DataFrame, name: str, features: list[str], cat_cols: list[str]) -> dict:
    pred, per_seed = average_predictions(train, warm, features, cat_cols, [11])
    return {"name": name, "features": features, "metric": metric(warm[TARGET].values, pred), "per_seed": per_seed}


def main() -> None:
    train_raw = pd.read_csv(SPLIT / "track3_train.csv")
    warm_raw = pd.read_csv(SPLIT / "track3_test_warm.csv")
    cold_raw = pd.read_csv(SPLIT / "track3_test_cold.csv")
    hist, global_values = build_artist_history(train_raw)
    train = add_history(add_features(train_raw), hist, global_values)
    warm = add_history(add_features(warm_raw), hist, global_values)
    cold = add_history(add_features(cold_raw), hist, global_values)

    warm_h31_pred, warm_h31_per_seed = average_predictions(train, warm, WARM_H31_FEATURES, WARM_H31_CAT, SEEDS)
    warm_h31_metric = metric(warm[TARGET].values, warm_h31_pred)

    cold_base_model = build_lad(COLD_BASE_FEATURES)
    cold_base_model.fit(train[COLD_BASE_FEATURES], train[TARGET].values)
    cold_base_pred = cold_base_model.predict(cold[COLD_BASE_FEATURES])

    cold_3d_model = build_lad(COLD_3D_FEATURES)
    cold_3d_model.fit(train[COLD_3D_FEATURES], train[TARGET].values)
    cold_3d_all_pred = cold_3d_model.predict(cold[COLD_3D_FEATURES])
    mask_3d = cold["is_3d_work"].astype(bool).to_numpy()
    cold_cond_pred = cold_base_pred.copy()
    cold_cond_pred[mask_3d] = cold_3d_all_pred[mask_3d]

    # H34: check whether the 3D fallback only helps specific 3D slices.
    cold_3d = cold[mask_3d].copy()
    volume_q = cold_3d["volume_log"].quantile([0.33, 0.66]).to_list() if len(cold_3d) else [0, 0]
    h34_masks = {
        "3d_all": mask_3d,
        "3d_low_volume": (cold["is_3d_work"].eq(1) & cold["volume_log"].le(volume_q[0])).to_numpy(),
        "3d_mid_volume": (cold["is_3d_work"].eq(1) & cold["volume_log"].gt(volume_q[0]) & cold["volume_log"].le(volume_q[1])).to_numpy(),
        "3d_high_volume": (cold["is_3d_work"].eq(1) & cold["volume_log"].gt(volume_q[1])).to_numpy(),
        "3d_large_ho": (cold["is_3d_work"].eq(1) & cold["is_large_ho"].eq(1)).to_numpy(),
        "3d_not_large_ho": (cold["is_3d_work"].eq(1) & cold["is_large_ho"].eq(0)).to_numpy(),
    }
    h34_base = slice_metric_table(cold, cold_base_pred, h34_masks)
    h34_cond = slice_metric_table(cold, cold_cond_pred, h34_masks)
    h34_delta = {
        name: h34_cond[name]["median_ape"] - h34_base[name]["median_ape"]
        for name in h34_cond.keys()
        if name in h34_base
    }

    # H35: compare separated policy against one shared Warm model applied to both Warm and Cold.
    shared_pred_warm = warm_h31_pred
    shared_pred_cold, shared_cold_per_seed = average_predictions(train, cold, WARM_H31_FEATURES, WARM_H31_CAT, [11])
    h35 = {
        "separate_policy": {"warm": warm_h31_metric, "cold": metric(cold[TARGET].values, cold_cond_pred)},
        "shared_h31_like_lgbm_policy": {"warm": metric(warm[TARGET].values, shared_pred_warm), "cold": metric(cold[TARGET].values, shared_pred_cold), "cold_per_seed": shared_cold_per_seed},
    }

    # H36/H37: Warm performance by artist-history amount.
    count_bins = pd.cut(
        warm["artist_count"],
        bins=[-0.1, 1, 3, 10, 50, 100000],
        labels=["1", "2-3", "4-10", "11-50", "51+"],
    ).astype(str)
    h36_masks = {f"artist_count_{label}": count_bins.eq(label).to_numpy() for label in ["1", "2-3", "4-10", "11-50", "51+"]}
    h36 = slice_metric_table(warm, warm_h31_pred, h36_masks, min_n=10)
    warm_ape = ape_values(warm[TARGET].values, warm_h31_pred)
    h37 = {
        "spearman_artist_works_log_vs_ape": float(pd.Series(warm["artist_works_log"]).corr(pd.Series(warm_ape), method="spearman")),
        "artist_history_slices": h36,
        "interpretation_hint": "Negative correlation means more artist history tends to reduce error.",
    }

    # H38: compare artist identity vs structured history features.
    common = BASE_FEATURES + HO_3D_FEATURES
    common_cat = BASE_CAT + ["ho_bucket_refined"]
    h38_variants = [
        h38_variant(train, warm, "artist_name_only", common + [ARTIST_COL], common_cat + [ARTIST_COL]),
        h38_variant(train, warm, "history_only", common + HISTORY_FEATURES, common_cat),
        h38_variant(train, warm, "artist_name_plus_history", common + [ARTIST_COL] + HISTORY_FEATURES, common_cat + [ARTIST_COL]),
    ]

    # H39/H40/H42: large-work, feature-group ablation, and high-risk patterns.
    h39_masks = {
        "warm_large_ho": warm["is_large_ho"].eq(1).to_numpy(),
        "warm_extra_large_ho": warm["is_extra_large_ho"].eq(1).to_numpy(),
        "warm_very_large_area": warm["is_very_large_area"].eq(1).to_numpy(),
        "cold_large_ho": cold["is_large_ho"].eq(1).to_numpy(),
        "cold_extra_large_ho": cold["is_extra_large_ho"].eq(1).to_numpy(),
        "cold_very_large_area": cold["is_very_large_area"].eq(1).to_numpy(),
    }
    h39 = {
        "warm": slice_metric_table(warm, warm_h31_pred, {k.removeprefix("warm_"): v for k, v in h39_masks.items() if k.startswith("warm_")}, min_n=10),
        "cold": slice_metric_table(cold, cold_cond_pred, {k.removeprefix("cold_"): v for k, v in h39_masks.items() if k.startswith("cold_")}, min_n=10),
    }

    h40_feature_sets = {
        "full": COLD_BASE_FEATURES,
        "no_material": [f for f in COLD_BASE_FEATURES if f not in {"medium_category", "support_category", "medium_ho_bucket"}],
        "no_size_ho": [
            f
            for f in COLD_BASE_FEATURES
            if f
            not in {
                "depth_cm",
                "log_area",
                "estimated_ho",
                "aspect_ratio",
                "ho_bucket_refined",
                "is_large_ho",
                "is_extra_large_ho",
                "area_per_ho_log",
                "ho_per_area_log",
                "ho_area_gap_abs",
                "log_ho",
            }
        ],
        "no_form": [f for f in COLD_BASE_FEATURES if f not in {"orientation", "aspect_ratio", "depth_cm"}],
    }
    h40 = {}
    for name, features in h40_feature_sets.items():
        model = build_lad(features)
        model.fit(train[features], train[TARGET].values)
        pred = model.predict(cold[features])
        h40[name] = {"features": features, "metric": metric(cold[TARGET].values, pred)}

    h41 = {
        "warm_h31_per_seed": warm_h31_per_seed,
        "warm_h31_mean_median_ape": float(np.mean([row["median_ape"] for row in warm_h31_per_seed])),
        "warm_h31_std_median_ape": float(np.std([row["median_ape"] for row in warm_h31_per_seed])),
        "cold_h32_deterministic_note": "QuantileRegressor is deterministic for this setup; repeat-seed variance is not applicable.",
        "cold_h32_metric": metric(cold[TARGET].values, cold_cond_pred),
    }

    cold_ape = ape_values(cold[TARGET].values, cold_cond_pred)
    h42_masks = {
        "warm_error_top10": warm_ape >= np.quantile(warm_ape, 0.90),
        "cold_error_top10": cold_ape >= np.quantile(cold_ape, 0.90),
    }
    h42 = {
        "warm_top10_error_profile": {
            "n": int(h42_masks["warm_error_top10"].sum()),
            "artist_count_median": float(warm.loc[h42_masks["warm_error_top10"], "artist_count"].median()),
            "is_3d_rate": float(warm.loc[h42_masks["warm_error_top10"], "is_3d_work"].mean()),
            "large_ho_rate": float(warm.loc[h42_masks["warm_error_top10"], "is_large_ho"].mean()),
            "median_log_area": float(warm.loc[h42_masks["warm_error_top10"], "log_area"].median()),
        },
        "cold_top10_error_profile": {
            "n": int(h42_masks["cold_error_top10"].sum()),
            "is_3d_rate": float(cold.loc[h42_masks["cold_error_top10"], "is_3d_work"].mean()),
            "large_ho_rate": float(cold.loc[h42_masks["cold_error_top10"], "is_large_ho"].mean()),
            "median_log_area": float(cold.loc[h42_masks["cold_error_top10"], "log_area"].median()),
        },
    }

    # H43: lightweight empirical interval check around current point predictions.
    warm_abs_log_resid = np.abs(warm_h31_pred - warm[TARGET].values)
    cold_abs_log_resid = np.abs(cold_cond_pred - cold[TARGET].values)
    h43 = {
        "warm_empirical_q80_abs_log_error": float(np.quantile(warm_abs_log_resid, 0.80)),
        "warm_empirical_q90_abs_log_error": float(np.quantile(warm_abs_log_resid, 0.90)),
        "cold_empirical_q80_abs_log_error": float(np.quantile(cold_abs_log_resid, 0.80)),
        "cold_empirical_q90_abs_log_error": float(np.quantile(cold_abs_log_resid, 0.90)),
        "note": "This is not a production interval model. It estimates how wide a simple error band would need to be on the current release tests.",
    }

    result = {
        "experiment_id": "H34_H43_followup_validation",
        "date": "2026-05-14",
        "data": {"train_rows": len(train), "warm_rows": len(warm), "cold_rows": len(cold), "cold_3d_rows": int(mask_3d.sum())},
        "h34_cold_3d_slice_policy": {"base": h34_base, "conditional": h34_cond, "delta_median_ape": h34_delta},
        "h35_separate_vs_shared_policy": h35,
        "h36_warm_artist_count_slices": h36,
        "h37_artist_history_error_relation": h37,
        "h38_artist_identity_vs_history": h38_variants,
        "h39_large_work_risk": h39,
        "h40_cold_feature_group_ablation": h40,
        "h41_stability": h41,
        "h42_high_error_profile": h42,
        "h43_price_range_band_width": h43,
        "judgement": {
            "h34": "3D fallback is useful overall; check delta table before narrowing further.",
            "h35": "Separate Warm/Cold policy remains the safer default if shared cold is worse than H32.",
            "h36_h37": "Warm confidence should consider artist history amount if low-history slices are worse.",
            "h38": "Prefer the best of artist_name/history variants only if it beats H31-like combined features.",
            "h39_h42": "Large or high-error profiles are candidates for warning/fallback, not automatic retraining.",
            "h43": "Use as interval sizing reference only; final interval needs calibration on validation data.",
        },
    }
    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print("H34-H43 follow-up validation")
    print(f"saved: {OUT_PATH}")
    print(f"H31 warm median APE: {warm_h31_metric['median_ape']:.4f}")
    print(f"H32 cold conditional median APE: {metric(cold[TARGET].values, cold_cond_pred)['median_ape']:.4f}")
    print(f"H35 shared cold median APE: {h35['shared_h31_like_lgbm_policy']['cold']['median_ape']:.4f}")
    print("H34 3D slice deltas:", {k: round(v, 4) for k, v in h34_delta.items()})
    print("H40 cold ablation:", {k: round(v["metric"]["median_ape"], 4) for k, v in h40.items()})


if __name__ == "__main__":
    main()
