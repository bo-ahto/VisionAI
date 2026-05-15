"""Track 3 H3 — Warm artist feature confirm on release split.

Compares Warm LightGBM variants:
- no_artist: artwork structure only
- artist_name: add artist_name_ko categorical
- artist_works: add train-only artist_works_log
- artist_both: add both artist_name_ko and artist_works_log
"""
from __future__ import annotations

import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parent.parent.parent
DATA_DIR = REPO / "data" / "release_split"
OUT_PATH = REPO / "data" / "track3_h3_artist_feature_confirm_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"

BASE_FEATURES = [
    "medium_category",
    "support_category",
    "has_depth",
    "depth_cm",
    "width_cm",
    "height_cm",
    "log_area",
    "estimated_ho",
    "orientation",
]
CAT_BASE = ["medium_category", "support_category", "orientation"]


def compute_metrics(y_true_ln: np.ndarray, y_pred_ln: np.ndarray) -> dict:
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
        "p95_ape": float(np.quantile(ape, 0.95)),
        "p99_ape": float(np.quantile(ape, 0.99)),
        "max_ape": float(np.max(ape)),
    }


def add_artist_works(train_df: pd.DataFrame, test_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    train_df = train_df.copy()
    test_df = test_df.copy()
    train_counts = train_df[ARTIST_COL].value_counts().to_dict()
    train_df["artist_works_log"] = np.log1p(train_df[ARTIST_COL].map(train_counts).fillna(0))
    test_df["artist_works_log"] = np.log1p(test_df[ARTIST_COL].map(train_counts).fillna(0))
    return train_df, test_df


def to_lgb_frame(df: pd.DataFrame, features: list[str], cat_cols: list[str]) -> pd.DataFrame:
    out = df[features].copy()
    for col in cat_cols:
        if col in out.columns:
            out[col] = out[col].astype("category")
    return out


def train_predict(train_df: pd.DataFrame, test_df: pd.DataFrame, features: list[str], cat_cols: list[str]) -> np.ndarray:
    x_train = to_lgb_frame(train_df, features, cat_cols)
    x_test = to_lgb_frame(test_df, features, cat_cols)
    y_train = train_df[TARGET].values

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
    dataset = lgb.Dataset(x_train, y_train, categorical_feature=cat_cols)
    model = lgb.train(params, dataset, num_boost_round=420)
    return model.predict(x_test)


def main() -> None:
    train_df = pd.read_csv(DATA_DIR / "track3_train.csv")
    test_df = pd.read_csv(DATA_DIR / "track3_test_warm.csv")
    train_df, test_df = add_artist_works(train_df, test_df)

    variants = {
        "no_artist": (BASE_FEATURES, CAT_BASE),
        "artist_name": (BASE_FEATURES + [ARTIST_COL], CAT_BASE + [ARTIST_COL]),
        "artist_works": (BASE_FEATURES + ["artist_works_log"], CAT_BASE),
        "artist_both": (BASE_FEATURES + ["artist_works_log", ARTIST_COL], CAT_BASE + [ARTIST_COL]),
    }

    y_true = test_df[TARGET].values
    results = {
        "data": {
            "train_rows": int(len(train_df)),
            "test_warm_rows": int(len(test_df)),
            "train_artists": int(train_df[ARTIST_COL].nunique()),
            "test_warm_artists": int(test_df[ARTIST_COL].nunique()),
        },
        "variants": {},
    }

    for name, (features, cat_cols) in variants.items():
        pred = train_predict(train_df, test_df, features, cat_cols)
        results["variants"][name] = {
            "features": features,
            "metrics": compute_metrics(y_true, pred),
        }

    base = results["variants"]["no_artist"]["metrics"]["median_ape"]
    for name, result in results["variants"].items():
        result["delta_median_ape_vs_no_artist"] = float(result["metrics"]["median_ape"] - base)

    OUT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2))

    print("H3 artist feature confirm")
    print(f"saved: {OUT_PATH}")
    for name, result in results["variants"].items():
        metrics = result["metrics"]
        print(
            f"{name:<14} median_ape={metrics['median_ape']:.4f} "
            f"mape={metrics['mape']:.4f} w30={metrics['within_30pct']:.4f} "
            f"delta={result['delta_median_ape_vs_no_artist']:+.4f}"
        )


if __name__ == "__main__":
    main()
