"""Track 3 H8 — Cold 2D fallback confirm on release split.

Baseline:
- Train one Cold LAD on all train rows and predict all test_cold rows.

Variant:
- Keep baseline prediction for Cold 3D rows.
- For Cold 2D rows only, use a 2D-only Cold LAD trained on train 2D rows.

This tests whether a limited Cold 2D fallback is better than replacing the
entire Cold model.
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
OUT_PATH = REPO / "data" / "track3_h8_cold_2d_fallback_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"

BASE_FEATURES = [
    "medium_category",
    "support_category",
    "depth_cm",
    "log_area",
    "estimated_ho",
    "orientation",
]
BASE_CAT = ["medium_category", "support_category", "orientation"]
ALL_FEATURES = BASE_FEATURES + ["medium_ho_bucket", "artist_works_log", "aspect_ratio"]
ALL_CAT = BASE_CAT + ["medium_ho_bucket"]
TWO_D_FEATURES = [
    "medium_category",
    "support_category",
    "log_area",
    "estimated_ho",
    "orientation",
    "medium_ho_bucket",
    "artist_works_log",
    "aspect_ratio",
]
TWO_D_CAT = ["medium_category", "support_category", "orientation", "medium_ho_bucket"]


def make_features(df: pd.DataFrame, artist_counts: dict[str, int]) -> pd.DataFrame:
    df = df.copy()
    df["ho_bucket"] = pd.cut(
        df["estimated_ho"],
        bins=[-0.1, 5, 20, 50, 200],
        labels=["0-5", "5-20", "20-50", "50+"],
    ).astype(str)
    df["medium_ho_bucket"] = df["medium_category"].astype(str) + "_" + df["ho_bucket"]
    df["aspect_ratio"] = np.log(df["width_cm"] / df["height_cm"].replace(0, 1))
    df["artist_works_log"] = np.log1p(df[ARTIST_COL].map(artist_counts).fillna(0))
    df["is_3d"] = (df["depth_cm"] > 0).astype(int)
    return df


def build_lad(features: list[str], cat_cols: list[str]) -> Pipeline:
    cat = [col for col in features if col in cat_cols]
    num = [col for col in features if col not in cat_cols]
    preprocess = ColumnTransformer(
        [
            ("cat", OneHotEncoder(handle_unknown="ignore", drop="first", max_categories=100), cat),
            ("num", StandardScaler(), num),
        ]
    )
    return Pipeline(
        [
            ("prep", preprocess),
            ("est", QuantileRegressor(quantile=0.5, solver="highs", alpha=0.0)),
        ]
    )


def metrics(y_true_ln: np.ndarray, y_pred_ln: np.ndarray) -> dict:
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
        "p99_ape": float(np.quantile(ape, 0.99)),
        "max_ape": float(np.max(ape)),
        "n_10x_errors": int(np.sum(ape >= 1.0)),
        "pct_10x_errors": float(np.mean(ape >= 1.0)),
        "ape_array": ape.tolist(),
    }


def paired(base_ape: list[float], variant_ape: list[float]) -> dict:
    base = np.asarray(base_ape)
    variant = np.asarray(variant_ape)
    delta = variant - base
    return {
        "n": int(len(delta)),
        "median_delta": float(np.median(delta)),
        "mean_delta": float(np.mean(delta)),
        "win_rate_variant": float(np.mean(variant < base)),
        "catastrophic_2x": float(np.mean(variant > 2 * base)),
        "variant_better_10pp": int(np.sum(delta <= -0.10)),
        "variant_worse_10pp": int(np.sum(delta >= 0.10)),
    }


def strip_ape(metric: dict) -> dict:
    return {k: v for k, v in metric.items() if k != "ape_array"}


def main() -> None:
    train = pd.read_csv(SPLIT / "track3_train.csv")
    test_cold = pd.read_csv(SPLIT / "track3_test_cold.csv")
    artist_counts = train[ARTIST_COL].value_counts().to_dict()

    train_f = make_features(train, artist_counts)
    test_f = make_features(test_cold, artist_counts)
    mask_2d = test_f["is_3d"].values == 0
    mask_3d = ~mask_2d

    # Cold-start sanity check.
    overlap = set(train_f[ARTIST_COL]) & set(test_f[ARTIST_COL])
    assert not overlap, f"Cold split overlap: {len(overlap)} artists"

    base_model = build_lad(ALL_FEATURES, ALL_CAT)
    base_model.fit(train_f[ALL_FEATURES], train_f[TARGET].values)
    pred_base = base_model.predict(test_f[ALL_FEATURES])

    train_2d = train_f[train_f["is_3d"] == 0].copy()
    model_2d = build_lad(TWO_D_FEATURES, TWO_D_CAT)
    model_2d.fit(train_2d[TWO_D_FEATURES], train_2d[TARGET].values)

    pred_variant = pred_base.copy()
    pred_variant[mask_2d] = model_2d.predict(test_f.loc[mask_2d, TWO_D_FEATURES])

    y = test_f[TARGET].values
    result = {
        "experiment_id": "H8_cold_2d_fallback_confirm",
        "data": {
            "train_rows": int(len(train_f)),
            "train_artists": int(train_f[ARTIST_COL].nunique()),
            "test_cold_rows": int(len(test_f)),
            "test_cold_artists": int(test_f[ARTIST_COL].nunique()),
            "test_cold_2d_rows": int(mask_2d.sum()),
            "test_cold_3d_rows": int(mask_3d.sum()),
        },
        "features": {
            "baseline": ALL_FEATURES,
            "fallback_2d": TWO_D_FEATURES,
        },
        "overall": {},
        "cold_2d": {},
        "cold_3d": {},
        "judgement": {},
    }

    for name, mask in [("overall", np.ones(len(test_f), dtype=bool)), ("cold_2d", mask_2d), ("cold_3d", mask_3d)]:
        base_m = metrics(y[mask], pred_base[mask])
        variant_m = metrics(y[mask], pred_variant[mask])
        result[name] = {
            "baseline": strip_ape(base_m),
            "fallback": strip_ape(variant_m),
            "delta": {
                key: float(variant_m[key] - base_m[key])
                for key in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct", "p95_ape", "p99_ape", "max_ape"]
            },
            "paired": paired(base_m["ape_array"], variant_m["ape_array"]),
        }

    overall = result["overall"]
    cold_2d = result["cold_2d"]
    cold_3d = result["cold_3d"]
    result["judgement"] = {
        "overall_not_worse": bool(overall["delta"]["median_ape"] <= 0.005 and overall["delta"]["p95_ape"] <= 0.05),
        "cold_2d_improved": bool(cold_2d["delta"]["median_ape"] < -0.005 or cold_2d["delta"]["within_30pct"] > 0.01),
        "cold_3d_unchanged": bool(abs(cold_3d["delta"]["median_ape"]) < 1e-12),
        "adoptable": False,
    }
    result["judgement"]["adoptable"] = bool(
        result["judgement"]["overall_not_worse"]
        and result["judgement"]["cold_2d_improved"]
        and result["judgement"]["cold_3d_unchanged"]
    )

    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    print("H8 Cold 2D fallback confirm")
    print(f"saved: {OUT_PATH}")
    for name in ["overall", "cold_2d", "cold_3d"]:
        row = result[name]
        print(
            f"{name:<8} base={row['baseline']['median_ape']:.4f} "
            f"fallback={row['fallback']['median_ape']:.4f} "
            f"delta={row['delta']['median_ape']:+.4f} "
            f"w30_delta={row['delta']['within_30pct']:+.4f} "
            f"wr={row['paired']['win_rate_variant']:.4f}"
        )
    print(f"adoptable={result['judgement']['adoptable']}")


if __name__ == "__main__":
    main()
