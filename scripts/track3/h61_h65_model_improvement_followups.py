"""Track 3 H61-H65 model-improvement follow-up experiments."""
from __future__ import annotations

import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import HuberRegressor, QuantileRegressor, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from h34_h43_followup_validation import (
    COLD_3D_FEATURES,
    COLD_BASE_FEATURES,
    REPO,
    SPLIT,
    TARGET,
    WARM_H31_CAT,
    WARM_H31_FEATURES,
    add_features,
    add_history,
    average_predictions,
    build_artist_history,
    metric,
    to_cat,
    train_lgb,
)


OUT_PATH = REPO / "data" / "track3_h61_h65_model_improvement_followups_results.json"
ARTIST_COL = "artist_name_ko"
COLD_CAT_COLS = [
    "medium_category",
    "support_category",
    "orientation",
    "medium_ho_bucket",
    "ho_bucket_refined",
    "area_size_bucket",
    "medium_support_combo_clean",
]


def build_linear(features: list[str], kind: str, alpha: float = 0.0) -> Pipeline:
    cat = [col for col in features if col in COLD_CAT_COLS]
    num = [col for col in features if col not in COLD_CAT_COLS]
    prep = ColumnTransformer(
        [
            ("cat", OneHotEncoder(handle_unknown="ignore", drop="first", max_categories=100), cat),
            ("num", StandardScaler(), num),
        ]
    )
    if kind == "quantile":
        est = QuantileRegressor(quantile=0.5, solver="highs", alpha=alpha)
    elif kind == "huber":
        est = HuberRegressor(alpha=alpha, max_iter=1000)
    elif kind == "ridge":
        est = Ridge(alpha=max(alpha, 1.0))
    else:
        raise ValueError(f"unknown model kind: {kind}")
    return Pipeline([("prep", prep), ("est", est)])


def train_lgb_fixed(train_df: pd.DataFrame, features: list[str], cat_cols: list[str], params: dict, seed: int = 11) -> lgb.Booster:
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(train_df))
    cut = int(len(train_df) * 0.1)
    val_idx = perm[:cut]
    tr_idx = perm[cut:]
    base_params = {
        "objective": "regression",
        "metric": "rmse",
        "verbose": -1,
        "seed": seed,
    }
    base_params.update(params)
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
    return lgb.train(base_params, ds_tr, num_boost_round=2000, valid_sets=[ds_val], callbacks=[lgb.early_stopping(30, verbose=False)])


def slice_metric(df: pd.DataFrame, pred: np.ndarray, mask: np.ndarray, min_n: int = 20) -> dict | None:
    if int(mask.sum()) < min_n:
        return None
    return metric(df.loc[mask, TARGET].values, pred[mask])


def main() -> None:
    train_raw = pd.read_csv(SPLIT / "track3_train.csv")
    warm_raw = pd.read_csv(SPLIT / "track3_test_warm.csv")
    cold_raw = pd.read_csv(SPLIT / "track3_test_cold.csv")
    hist, global_values = build_artist_history(train_raw)
    train = add_history(add_features(train_raw), hist, global_values)
    warm = add_history(add_features(warm_raw), hist, global_values)
    cold = add_history(add_features(cold_raw), hist, global_values)

    # Reference predictions.
    h31_pred, h31_per_seed = average_predictions(train, warm, WARM_H31_FEATURES, WARM_H31_CAT, [11, 22, 33])
    h31_metric = metric(warm[TARGET].values, h31_pred)

    base_lad = build_linear(COLD_BASE_FEATURES, "quantile", alpha=0.0)
    base_lad.fit(train[COLD_BASE_FEATURES], train[TARGET].values)
    cold_base_pred = base_lad.predict(cold[COLD_BASE_FEATURES])

    model_3d = build_linear(COLD_3D_FEATURES, "quantile", alpha=0.0)
    model_3d.fit(train[COLD_3D_FEATURES], train[TARGET].values)
    cold_3d_pred = model_3d.predict(cold[COLD_3D_FEATURES])
    mask_3d = cold["is_3d_work"].astype(bool).to_numpy()
    h32_pred = cold_base_pred.copy()
    h32_pred[mask_3d] = cold_3d_pred[mask_3d]
    h32_metric = metric(cold[TARGET].values, h32_pred)

    # H62: bounded LightGBM tuning on H31 features.
    h62_param_grid = {
        "h31_current_like": {
            "learning_rate": 0.04,
            "num_leaves": 198,
            "min_data_in_leaf": 75,
            "feature_fraction": 0.987,
            "bagging_fraction": 0.978,
            "bagging_freq": 5,
            "reg_alpha": 0.36,
            "reg_lambda": 4.75,
        },
        "smaller_regularized": {
            "learning_rate": 0.035,
            "num_leaves": 96,
            "min_data_in_leaf": 120,
            "feature_fraction": 0.90,
            "bagging_fraction": 0.90,
            "bagging_freq": 5,
            "reg_alpha": 1.0,
            "reg_lambda": 8.0,
        },
        "larger_low_lr": {
            "learning_rate": 0.025,
            "num_leaves": 256,
            "min_data_in_leaf": 60,
            "feature_fraction": 0.95,
            "bagging_fraction": 0.95,
            "bagging_freq": 5,
            "reg_alpha": 0.2,
            "reg_lambda": 4.0,
        },
    }
    h62 = {}
    for name, params in h62_param_grid.items():
        model = train_lgb_fixed(train, WARM_H31_FEATURES, WARM_H31_CAT, params, seed=11)
        pred = model.predict(to_cat(warm, WARM_H31_FEATURES, WARM_H31_CAT))
        h62[name] = {"params": params, "metric": metric(warm[TARGET].values, pred), "best_iteration": int(model.best_iteration)}

    # H63: Cold LAD alpha tuning.
    h63 = {}
    for alpha in [0.0, 0.0001, 0.001, 0.01]:
        model = build_linear(COLD_BASE_FEATURES, "quantile", alpha=alpha)
        model.fit(train[COLD_BASE_FEATURES], train[TARGET].values)
        pred = model.predict(cold[COLD_BASE_FEATURES])
        h63[f"alpha_{alpha:g}"] = {"alpha": alpha, "metric": metric(cold[TARGET].values, pred)}

    # H65: Warm low-history blending with artist median.
    artist_median = warm["artist_ln_price_median"].to_numpy()
    blend_rules = {
        "blend_20pct_for_1_to_3": np.where(warm["artist_count"].le(3), 0.20, 0.0),
        "blend_35pct_for_1_to_3": np.where(warm["artist_count"].le(3), 0.35, 0.0),
        "graded_35_20_0": np.select(
            [warm["artist_count"].eq(1), warm["artist_count"].between(2, 3)],
            [0.35, 0.20],
            default=0.0,
        ),
    }
    h65_masks = {
        "artist_count_1": warm["artist_count"].eq(1).to_numpy(),
        "artist_count_1_to_3": warm["artist_count"].le(3).to_numpy(),
        "all_warm": np.ones(len(warm), dtype=bool),
    }
    h65 = {"h31": {name: slice_metric(warm, h31_pred, mask, min_n=10) for name, mask in h65_masks.items()}}
    for name, weight in blend_rules.items():
        pred = (1 - weight) * h31_pred + weight * artist_median
        h65[name] = {slice_name: slice_metric(warm, pred, mask, min_n=10) for slice_name, mask in h65_masks.items()}

    # H61: tree expert for Cold slices.
    cold_tree = train_lgb_fixed(
        train,
        COLD_3D_FEATURES,
        [col for col in COLD_CAT_COLS if col in COLD_3D_FEATURES],
        {
            "learning_rate": 0.04,
            "num_leaves": 64,
            "min_data_in_leaf": 120,
            "feature_fraction": 0.90,
            "bagging_fraction": 0.90,
            "bagging_freq": 5,
            "reg_alpha": 1.0,
            "reg_lambda": 8.0,
        },
        seed=11,
    )
    cold_tree_pred = cold_tree.predict(to_cat(cold, COLD_3D_FEATURES, [col for col in COLD_CAT_COLS if col in COLD_3D_FEATURES]))
    mask_large = cold["is_large_ho"].astype(bool).to_numpy()
    mask_very_large = cold["is_very_large_area"].astype(bool).to_numpy()
    h61_variants = {
        "h32_base": h32_pred,
        "tree_for_3d": np.where(mask_3d, cold_tree_pred, h32_pred),
        "tree_for_large": np.where(mask_large, cold_tree_pred, h32_pred),
        "tree_for_3d_or_large": np.where(mask_3d | mask_large, cold_tree_pred, h32_pred),
        "tree_for_very_large": np.where(mask_very_large, cold_tree_pred, h32_pred),
    }
    h61 = {
        name: {
            "all": metric(cold[TARGET].values, pred),
            "3d": slice_metric(cold, pred, mask_3d),
            "large": slice_metric(cold, pred, mask_large),
            "very_large": slice_metric(cold, pred, mask_very_large),
        }
        for name, pred in h61_variants.items()
    }

    # H64: robust linear ensemble.
    huber = build_linear(COLD_BASE_FEATURES, "huber", alpha=0.0001)
    huber.fit(train[COLD_BASE_FEATURES], train[TARGET].values)
    huber_pred = huber.predict(cold[COLD_BASE_FEATURES])
    ridge = build_linear(COLD_BASE_FEATURES, "ridge", alpha=10.0)
    ridge.fit(train[COLD_BASE_FEATURES], train[TARGET].values)
    ridge_pred = ridge.predict(cold[COLD_BASE_FEATURES])
    h64_variants = {
        "lad": cold_base_pred,
        "huber": huber_pred,
        "ridge": ridge_pred,
        "mean_lad_huber": (cold_base_pred + huber_pred) / 2,
        "median_lad_huber_ridge": np.median(np.vstack([cold_base_pred, huber_pred, ridge_pred]), axis=0),
    }
    h64 = {name: metric(cold[TARGET].values, pred) for name, pred in h64_variants.items()}

    result = {
        "experiment_id": "H61_H65_model_improvement_followups",
        "date": "2026-05-14",
        "data": {"train_rows": len(train), "warm_rows": len(warm), "cold_rows": len(cold)},
        "references": {
            "h31_warm_avg_pred_metric": h31_metric,
            "h31_warm_per_seed": h31_per_seed,
            "h32_cold_conditional_metric": h32_metric,
        },
        "h62_warm_lgbm_h31_retuning": h62,
        "h63_cold_lad_alpha_tuning": h63,
        "h65_warm_low_history_blending": h65,
        "h61_cold_slice_tree_expert": h61,
        "h64_cold_robust_ensemble": h64,
        "judgement": {
            "h62": "Adopt only if a tuned variant beats the H31 reference without worsening stability.",
            "h63": "Adopt alpha only if it improves Cold median APE and does not worsen tail metrics materially.",
            "h65": "Adopt blending only if low-history Warm improves without harming all-Warm median APE.",
            "h61": "Adopt a tree expert only if both the target slice and all-Cold improve.",
            "h64": "Adopt ensemble only if it improves Cold median APE or tail risk versus LAD.",
        },
    }
    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print("H61-H65 model improvement followups")
    print(f"saved: {OUT_PATH}")
    print("H62 warm:", {k: round(v["metric"]["median_ape"], 4) for k, v in h62.items()})
    print("H63 cold:", {k: round(v["metric"]["median_ape"], 4) for k, v in h63.items()})
    print("H65 warm all:", {k: round(v["all_warm"]["median_ape"], 4) for k, v in h65.items()})
    print("H61 cold all:", {k: round(v["all"]["median_ape"], 4) for k, v in h61.items()})
    print("H64 cold:", {k: round(v["median_ape"], 4) for k, v in h64.items()})


if __name__ == "__main__":
    main()
