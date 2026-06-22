from __future__ import annotations
import warnings
from pathlib import Path
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parents[4]
STORE = REPO / "data" / "track6" / "service_v0_1" / "official_v0_1_cold_feature_store.csv"

FEATURES = ["width_cm", "height_cm", "depth_cm", "area_cm2", "log_area", "aspect_ratio",
            "has_depth", "is_3d_candidate", "medium_category", "support_category",
            "size_bucket", "support_size_bucket"]
CATS = ["medium_category", "support_category", "size_bucket", "support_size_bucket"]

def lgb_params(alpha: float) -> dict:
    return dict(objective="quantile", alpha=alpha, n_estimators=430, num_leaves=31,
               learning_rate=0.035, min_child_samples=35, subsample=0.9,
               colsample_bytree=0.9, reg_alpha=0.0, reg_lambda=1.2, max_depth=-1,
               subsample_freq=1, n_jobs=-1, verbose=-1)

def load_splits() -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(STORE, low_memory=False)
    df["price_krw"] = pd.to_numeric(df["price_krw"], errors="coerce")
    df["area_cm2"] = pd.to_numeric(df["area_cm2"], errors="coerce")
    df = df[(df["price_krw"] > 0) & (df["area_cm2"] > 0)].copy()
    df["ln_price"] = np.log(df["price_krw"])
    df["ln_coef"] = df["ln_price"] - np.log(df["area_cm2"])
    train = df[df["split_name"] == "train"].dropna(subset=["ln_price"]).copy()
    test = df[df["split_name"] == "test"].dropna(subset=["ln_price"]).copy()
    return train, test

def prep(df: pd.DataFrame) -> pd.DataFrame:
    x = df[FEATURES].copy()
    for c in CATS:
        x[c] = x[c].astype("category")
    for c in [f for f in FEATURES if f not in CATS]:
        x[c] = pd.to_numeric(x[c], errors="coerce")
    return x

def metrics(actual_log, pred_log) -> dict:
    actual = np.exp(np.asarray(actual_log, dtype=float))
    pred = np.clip(np.exp(np.asarray(pred_log, dtype=float)), 1000.0, None)
    ape = np.abs(pred - actual) / np.clip(actual, 1.0, None)
    return {"MdAPE": float(np.median(ape)), "MAPE": float(np.mean(ape)),
            "p95_APE": float(np.quantile(ape, 0.95))}

def assert_disjoint(train: pd.DataFrame, test: pd.DataFrame) -> None:
    shared = set(train["artist_key"].dropna()) & set(test["artist_key"].dropna())
    assert not shared, f"leakage: {len(shared)} shared artists"
