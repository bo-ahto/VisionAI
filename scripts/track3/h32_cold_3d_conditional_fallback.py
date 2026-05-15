"""Track 3 H32 — Cold 3D conditional fallback retest.

H29-H30 showed that 3D features improved Cold 3D slices but hurt Cold 2D.
This script checks a conditional policy: use the base Cold model for 2D works
and the 3D-feature Cold model only for 3D works.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import QuantileRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO = Path(__file__).resolve().parent.parent.parent
SPLIT = REPO / "data" / "release_split"
OUT_PATH = REPO / "data" / "track3_h32_cold_3d_conditional_fallback_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"

CAT_COLS = [
    "medium_category",
    "support_category",
    "orientation",
    "medium_ho_bucket",
    "ho_bucket_refined",
    "area_size_bucket",
]
BASE_FEATURES = [
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
THREED_FEATURES = BASE_FEATURES + ["is_3d_work", "volume_log", "max_side_log", "min_side_log"]


def add_features(df: pd.DataFrame, artist_counts: dict[str, int]) -> pd.DataFrame:
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
    out["aspect_ratio"] = np.log(width / height.replace(0, 1)).replace([np.inf, -np.inf], 0).fillna(0)
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
    }


def build_lad(features: list[str]) -> Pipeline:
    cat = [col for col in features if col in CAT_COLS]
    num = [col for col in features if col not in CAT_COLS]
    prep = ColumnTransformer(
        [
            ("cat", OneHotEncoder(handle_unknown="ignore", drop="first", max_categories=100), cat),
            ("num", StandardScaler(), num),
        ]
    )
    return Pipeline([("prep", prep), ("est", QuantileRegressor(quantile=0.5, solver="highs", alpha=0.0))])


def slice_metrics(df: pd.DataFrame, pred: np.ndarray) -> dict:
    slices = {
        "all": np.ones(len(df), dtype=bool),
        "2d": df["is_2d_work"].astype(bool).to_numpy(),
        "3d": df["is_3d_work"].astype(bool).to_numpy(),
        "large_ho": df["is_large_ho"].astype(bool).to_numpy(),
        "extra_large_ho": df["is_extra_large_ho"].astype(bool).to_numpy(),
        "tiny_area": df["is_tiny_work"].astype(bool).to_numpy(),
        "very_large_area": df["is_very_large_area"].astype(bool).to_numpy(),
    }
    for medium in df["medium_category"].fillna("unknown").astype(str).value_counts().head(5).index:
        slices[f"medium_{medium}"] = df["medium_category"].fillna("unknown").astype(str).eq(medium).to_numpy()

    out = {}
    for name, mask in slices.items():
        if int(mask.sum()) < 20:
            continue
        out[name] = metric(df.loc[mask, TARGET].values, pred[mask])
    return out


def main() -> None:
    train_raw = pd.read_csv(SPLIT / "track3_train.csv")
    cold_raw = pd.read_csv(SPLIT / "track3_test_cold.csv")
    artist_counts = train_raw[ARTIST_COL].value_counts().to_dict()
    train = add_features(train_raw, artist_counts)
    cold = add_features(cold_raw, artist_counts)

    base_model = build_lad(BASE_FEATURES)
    base_model.fit(train[BASE_FEATURES], train[TARGET].values)
    base_pred = base_model.predict(cold[BASE_FEATURES])

    model_3d = build_lad(THREED_FEATURES)
    model_3d.fit(train[THREED_FEATURES], train[TARGET].values)
    pred_3d_all = model_3d.predict(cold[THREED_FEATURES])

    conditional_pred = base_pred.copy()
    mask_3d = cold["is_3d_work"].astype(bool).to_numpy()
    conditional_pred[mask_3d] = pred_3d_all[mask_3d]

    variants = {
        "V0_base_for_all": base_pred,
        "V1_3d_features_for_all": pred_3d_all,
        "V2_conditional_3d_fallback": conditional_pred,
    }
    result = {
        "experiment_id": "H32_cold_3d_conditional_fallback",
        "date": "2026-05-14",
        "reason": "Retest Cold 3D features as a conditional policy because they hurt the Cold 2D slice.",
        "data": {"train_rows": int(len(train)), "cold_rows": int(len(cold)), "cold_3d_rows": int(mask_3d.sum()), "cold_2d_rows": int((~mask_3d).sum())},
        "variants": {},
    }
    for name, pred in variants.items():
        result["variants"][name] = {
            "cold": metric(cold[TARGET].values, pred),
            "cold_slices": slice_metrics(cold, pred),
        }

    base = result["variants"]["V0_base_for_all"]["cold"]["median_ape"]
    for row in result["variants"].values():
        row["delta_vs_base_median_ape"] = float(row["cold"]["median_ape"] - base)

    best = min(result["variants"], key=lambda k: result["variants"][k]["cold"]["median_ape"])
    conditional = result["variants"]["V2_conditional_3d_fallback"]
    result["judgement"] = {
        "best_variant": best,
        "adopt_conditional_fallback": bool(
            conditional["cold"]["median_ape"] < base
            and conditional["cold_slices"]["2d"]["median_ape"] <= result["variants"]["V0_base_for_all"]["cold_slices"]["2d"]["median_ape"] + 0.001
        ),
        "note": "Adopt only if overall Cold improves while 2D is not harmed.",
    }
    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    print("H32 cold 3d conditional fallback")
    print(f"saved: {OUT_PATH}")
    for name, row in result["variants"].items():
        cold = row["cold"]
        two_d = row["cold_slices"]["2d"]
        three_d = row["cold_slices"]["3d"]
        print(
            f"{name:<28} cold={cold['median_ape']:.4f} "
            f"delta={row['delta_vs_base_median_ape']:+.4f} "
            f"2d={two_d['median_ape']:.4f} 3d={three_d['median_ape']:.4f}"
        )
    print(json.dumps(result["judgement"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
