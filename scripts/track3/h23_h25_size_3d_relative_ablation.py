"""Track 3 H23-H25 — size, 3D, and relative-size ablation suite.

Tests whether additional size-related features improve prediction after the
H19-H22 ho-feature candidate.
Covers:
- H23: size buckets and extreme size flags
- H24: 3D volume / side-length features
- H25: size percentile within medium category
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
OUT_PATH = REPO / "data" / "track3_h23_h25_size_3d_relative_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"

BASE_CAT = [
    "medium_category",
    "support_category",
    "orientation",
    "medium_ho_bucket",
    "ho_bucket_refined",
    "area_size_bucket",
]
COMMON = [
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


def train_percentile_reference(train_df: pd.DataFrame, value_col: str) -> dict[str, np.ndarray]:
    refs = {}
    for medium, grp in train_df.groupby(train_df["medium_category"].fillna("unknown").astype(str)):
        refs[medium] = np.sort(grp[value_col].fillna(0).to_numpy())
    refs["__all__"] = np.sort(train_df[value_col].fillna(0).to_numpy())
    return refs


def percentile_from_ref(values: pd.Series, mediums: pd.Series, refs: dict[str, np.ndarray]) -> np.ndarray:
    out = np.zeros(len(values), dtype=float)
    all_ref = refs["__all__"]
    for idx, (value, medium) in enumerate(zip(values.fillna(0).to_numpy(), mediums.fillna("unknown").astype(str))):
        ref = refs.get(medium, all_ref)
        if len(ref) == 0:
            ref = all_ref
        out[idx] = np.searchsorted(ref, value, side="right") / max(len(ref), 1)
    return out


def add_features(
    df: pd.DataFrame,
    artist_counts: dict[str, int],
    area_refs: dict[str, np.ndarray],
    ho_refs: dict[str, np.ndarray],
) -> pd.DataFrame:
    out = df.copy()
    medium = out["medium_category"].fillna("unknown").astype(str)
    ho = out["estimated_ho"].clip(lower=0).fillna(0)
    area = np.expm1(out["log_area"].fillna(0)).clip(lower=0)
    depth = out["depth_cm"].fillna(0).clip(lower=0)
    width = out["width_cm"].fillna(0).clip(lower=0)
    height = out["height_cm"].fillna(0).clip(lower=0)

    out["ho_bucket"] = pd.cut(
        ho,
        bins=[-0.1, 5, 20, 50, 200],
        labels=["0-5", "5-20", "20-50", "50+"],
    ).astype(str)
    out["medium_ho_bucket"] = medium + "_" + out["ho_bucket"]
    out["ho_bucket_refined"] = pd.cut(
        ho,
        bins=[-0.1, 3, 6, 10, 20, 50, 100, 300],
        labels=["0-3", "4-6", "7-10", "11-20", "21-50", "51-100", "100+"],
    ).astype(str)
    out["aspect_ratio"] = np.log(out["width_cm"] / out["height_cm"].replace(0, 1))
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
    volume = (width * height * depth).clip(lower=0)
    out["volume_log"] = np.log1p(volume)
    out["max_side_log"] = np.log1p(np.maximum.reduce([width.to_numpy(), height.to_numpy(), depth.to_numpy()]))
    out["min_side_log"] = np.log1p(np.minimum.reduce([width.to_numpy(), height.to_numpy(), depth.to_numpy()]))
    out["medium_area_percentile"] = percentile_from_ref(out["log_area"], medium, area_refs)
    out["medium_ho_percentile"] = percentile_from_ref(ho, medium, ho_refs)
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


def slice_metric(df: pd.DataFrame, pred: np.ndarray, mask_col: str) -> dict:
    mask = df[mask_col].astype(bool).to_numpy()
    if mask.sum() == 0:
        return {"n": 0}
    return strip_ape(metric(df.loc[mask, TARGET].values, pred[mask]))


def main() -> None:
    train_raw = pd.read_csv(SPLIT / "track3_train.csv")
    warm_raw = pd.read_csv(SPLIT / "track3_test_warm.csv")
    cold_raw = pd.read_csv(SPLIT / "track3_test_cold.csv")
    artist_counts = train_raw[ARTIST_COL].value_counts().to_dict()
    area_refs = train_percentile_reference(train_raw, "log_area")
    ho_refs = train_percentile_reference(train_raw, "estimated_ho")

    train = add_features(train_raw, artist_counts, area_refs, ho_refs)
    warm = add_features(warm_raw, artist_counts, area_refs, ho_refs)
    cold = add_features(cold_raw, artist_counts, area_refs, ho_refs)

    variants = {
        "V0_ho_enhanced_base": COMMON,
        "V1_area_size_bucket": COMMON + ["area_size_bucket", "is_tiny_work", "is_very_large_area"],
        "V2_3d_volume_sides": COMMON + ["is_3d_work", "volume_log", "max_side_log", "min_side_log"],
        "V3_medium_relative_size": COMMON + ["medium_area_percentile", "medium_ho_percentile"],
        "V4_all_size_3d_relative": COMMON
        + [
            "area_size_bucket",
            "is_tiny_work",
            "is_very_large_area",
            "is_3d_work",
            "volume_log",
            "max_side_log",
            "min_side_log",
            "medium_area_percentile",
            "medium_ho_percentile",
        ],
    }

    result = {
        "experiment_id": "H23_H25_size_3d_relative_ablation",
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
        if name == "V0_ho_enhanced_base":
            base_apes = {"cold": cold_m["ape_array"], "warm": warm_m["ape_array"]}
        result["variants"][name] = {
            "features": features,
            "categorical": cat_cols,
            "cold": strip_ape(cold_m),
            "warm": strip_ape(warm_m),
            "slice": {
                "cold_3d": slice_metric(cold, cold_pred, "is_3d_work"),
                "warm_3d": slice_metric(warm, warm_pred, "is_3d_work"),
            },
            "paired_vs_base": {
                "cold": paired(base_apes["cold"], cold_m["ape_array"]) if name != "V0_ho_enhanced_base" else None,
                "warm": paired(base_apes["warm"], warm_m["ape_array"]) if name != "V0_ho_enhanced_base" else None,
            },
        }

    base_cold = result["variants"]["V0_ho_enhanced_base"]["cold"]["median_ape"]
    base_warm = result["variants"]["V0_ho_enhanced_base"]["warm"]["median_ape"]
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
        "size_bucket_accepted": bool(
            result["variants"]["V1_area_size_bucket"]["delta_median_ape"]["cold"] <= -0.002
            or result["variants"]["V1_area_size_bucket"]["delta_median_ape"]["warm"] <= -0.002
        ),
        "three_d_features_accepted": bool(
            result["variants"]["V2_3d_volume_sides"]["delta_median_ape"]["cold"] <= -0.002
            or result["variants"]["V2_3d_volume_sides"]["delta_median_ape"]["warm"] <= -0.002
        ),
        "relative_size_accepted": bool(
            result["variants"]["V3_medium_relative_size"]["delta_median_ape"]["cold"] <= -0.002
            or result["variants"]["V3_medium_relative_size"]["delta_median_ape"]["warm"] <= -0.002
        ),
    }
    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    print("H23-H25 size/3D/relative ablation")
    print(f"saved: {OUT_PATH}")
    for name, row in result["variants"].items():
        print(
            f"{name:<28} cold={row['cold']['median_ape']:.4f} "
            f"({row['delta_median_ape']['cold']:+.4f}) "
            f"warm={row['warm']['median_ape']:.4f} "
            f"({row['delta_median_ape']['warm']:+.4f}) "
            f"cold3d={row['slice']['cold_3d'].get('median_ape', None)}"
        )
    print(f"best_cold={best_cold} best_warm={best_warm}")
    print(json.dumps(result["judgement"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
