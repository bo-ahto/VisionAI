"""트랙 1 vs 트랙 2 직접 비교 실험 (Descriptive / Supportive Only).

Pre-registered analysis plan: docs/track1_vs_track2_comparison_prereg_20260508.md

본 실험 = supportive analysis (decision-binding X):
- 트랙 1 surrogate: CatBoost (14 derivable features from stage4_full.parquet)
- 트랙 2: F4 + log_area spline + Huber (Cycle 1 spec)
- 같은 dataset / 같은 split (Random LAO + Time-split) / 같은 cold 정의 / 같은 metric

Caveat: Track 1 surrogate ≠ 운영 Track 1 (32 features 중 14 만 / 운영 학습 데이터 X).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import HuberRegressor
from sklearn.model_selection import GroupShuffleSplit
from catboost import CatBoostRegressor

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent.parent
DATA = ROOT / "data" / "curated" / "stage4_full.parquet"
RESULTS_DIR = Path(__file__).parent / "results"

# Pre-registered constants (cycle 1 동일)
TEST_SIZE = 0.20
N_BOOT = 2000
SEED = 42
COLD_TRAIN_COUNT_THRESHOLD = 10
TIME_SPLIT_YEAR = 2023

# Track 2 (cycle 1 spec)
HUBER_EPS = 1.35
HUBER_ALPHA = 0.0001

# Track 1 surrogate spec
CB_ITERATIONS = 1000
CB_LEARNING_RATE = 0.05
CB_DEPTH = 6


# ─── Track 1 surrogate features (14, derivable from stage4_full.parquet) ───
def build_track1_surrogate_features(df: pd.DataFrame) -> pd.DataFrame:
    """14 derivable features. 운영 Track 1 의 32 features 중 derive 가능 한 부분집합."""
    out = pd.DataFrame(index=df.index)
    out["ln_area"] = df["log_area"].values  # already computed
    out["aspect_ratio"] = (df["width_cm"] / df["height_cm"].replace(0, np.nan)).fillna(1.0).clip(0.1, 10.0)
    out["is_small"] = (df["area_cm2"] < 1000).astype(int)
    out["has_depth"] = (df["depth_cm"].fillna(0) > 0).astype(int)
    out["artist_birth_year"] = df["artist_birth_year"].fillna(df["artist_birth_year"].median())
    out["has_birth_year"] = df["artist_birth_year"].notna().astype(int)
    out["ln_followers"] = np.log1p(df["artist_followers"].fillna(0))
    out["for_sale_ratio"] = (df["artist_for_sale"] / df["artist_total_works"].replace(0, np.nan)).fillna(0).clip(0, 1)
    out["has_seoul"] = df["gallery_cities"].fillna("").str.contains("Seoul", case=False).astype(int)

    def _city_count(s):
        if pd.isna(s) or s == "":
            return 0
        return len([c.strip() for c in s.split(",") if c.strip()])

    out["gallery_city_count"] = df["gallery_cities"].apply(_city_count)

    def _has_intl(s):
        if pd.isna(s) or s == "":
            return 0
        cities = [c.strip().lower() for c in s.split(",")]
        return int(any(c not in ("seoul", "") for c in cities))

    out["has_international"] = df["gallery_cities"].apply(_has_intl)
    out["is_krw"] = (df["price_currency"] == "KRW").astype(int)
    # Categorical
    out["gallery_type"] = df["gallery_type"].fillna("unknown").astype(str)
    out["attribution_class"] = df["attribution_class"].fillna("unknown").astype(str)

    return out


CAT_FEATURES_T1 = ["gallery_type", "attribution_class"]


# ─── Track 2 features (cycle 1 spec, F4 + spline) ───
def restricted_cubic_spline(x: np.ndarray, knots: np.ndarray) -> np.ndarray:
    last_k, pre_last_k = knots[-1], knots[-2]
    denom = (last_k - knots[0]) ** 2
    out = []
    for i in range(len(knots) - 2):
        ti = knots[i]
        cube = lambda u: np.maximum(u, 0) ** 3
        spline = (
            cube(x - ti)
            - cube(x - pre_last_k) * (last_k - ti) / (last_k - pre_last_k)
            + cube(x - last_k) * (pre_last_k - ti) / (last_k - pre_last_k)
        )
        out.append(spline / denom)
    return np.column_stack(out)


def build_track2_features(df: pd.DataFrame, train_knot_log_area: np.ndarray | None = None) -> pd.DataFrame:
    if train_knot_log_area is None:
        knots = np.percentile(df["log_area"].values, [10, 50, 90])
    else:
        knots = np.percentile(train_knot_log_area, [10, 50, 90])
    sp = restricted_cubic_spline(df["log_area"].values, knots)
    return pd.DataFrame({
        "log_area": df["log_area"].values,
        "birth_year_centered": df["birth_year_centered"].values,
        "log_artist_total_works": df["log_artist_total_works"].values,
        "log_area_spline": sp[:, 0],
    })


# ─── Common ───
def mdape_pct(y_true_log: np.ndarray, y_pred_log: np.ndarray) -> float:
    actual = np.exp(y_true_log)
    pred = np.exp(y_pred_log)
    ape = np.abs(pred - actual) / actual
    return float(np.median(ape) * 100)


def cluster_bootstrap_ci(test_df: pd.DataFrame, y_pred_log: np.ndarray, n_boot: int = N_BOOT) -> tuple[float, float]:
    test_df = test_df.copy()
    test_df["__y_pred_log"] = y_pred_log
    artists = test_df["artist_slug"].unique()
    boot_mdapes = []
    for b in range(n_boot):
        rng = np.random.default_rng(b)
        sampled = rng.choice(artists, size=len(artists), replace=True)
        boot_df = pd.concat(
            [test_df[test_df["artist_slug"] == a] for a in sampled],
            ignore_index=True,
        )
        boot_mdapes.append(mdape_pct(boot_df["log_price"].values, boot_df["__y_pred_log"].values))
    arr = np.array(boot_mdapes)
    return float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5))


def fit_track1_surrogate(train_df: pd.DataFrame, test_df: pd.DataFrame) -> np.ndarray:
    Xtr = build_track1_surrogate_features(train_df)
    Xte = build_track1_surrogate_features(test_df)
    ytr = train_df["log_price"].values
    cat_idx = [Xtr.columns.get_loc(c) for c in CAT_FEATURES_T1]
    model = CatBoostRegressor(
        iterations=CB_ITERATIONS,
        learning_rate=CB_LEARNING_RATE,
        depth=CB_DEPTH,
        loss_function="RMSE",
        random_seed=SEED,
        cat_features=cat_idx,
        verbose=0,
    )
    model.fit(Xtr, ytr)
    return model.predict(Xte)


def fit_track2(train_df: pd.DataFrame, test_df: pd.DataFrame) -> np.ndarray:
    Xtr = build_track2_features(train_df)
    Xte = build_track2_features(test_df, train_knot_log_area=train_df["log_area"].values)
    ytr = train_df["log_price"].values
    m = HuberRegressor(epsilon=HUBER_EPS, max_iter=500, alpha=HUBER_ALPHA)
    m.fit(Xtr.values, ytr)
    return Xte.values @ m.coef_ + m.intercept_


def evaluate_random_lao(df: pd.DataFrame) -> dict:
    """Random LAO 80/20 (cycle 1 동일)."""
    logger.info("=== Random LAO 80/20 ===")
    groups = df["artist_slug"].values
    gss = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=SEED)
    train_idx, test_idx = next(gss.split(df, df["log_price"], groups))
    train_df = df.iloc[train_idx].copy()
    test_df = df.iloc[test_idx].copy()

    out = {"n_train": len(train_df), "n_test": len(test_df)}

    logger.info("Track 1 surrogate fit + predict...")
    t1_pred = fit_track1_surrogate(train_df, test_df)
    t1_mdape = mdape_pct(test_df["log_price"].values, t1_pred)
    t1_ci = cluster_bootstrap_ci(test_df, t1_pred)
    out["track1_surrogate"] = {
        "cold_mdape": t1_mdape,
        "ci_95": list(t1_ci),
    }
    logger.info("  Track 1 surrogate cold_mdape=%.2f%% CI=[%.2f, %.2f]", t1_mdape, t1_ci[0], t1_ci[1])

    logger.info("Track 2 fit + predict...")
    t2_pred = fit_track2(train_df, test_df)
    t2_mdape = mdape_pct(test_df["log_price"].values, t2_pred)
    t2_ci = cluster_bootstrap_ci(test_df, t2_pred)
    out["track2"] = {
        "cold_mdape": t2_mdape,
        "ci_95": list(t2_ci),
    }
    logger.info("  Track 2 cold_mdape=%.2f%% CI=[%.2f, %.2f]", t2_mdape, t2_ci[0], t2_ci[1])

    out["delta_t2_minus_t1"] = t2_mdape - t1_mdape
    return out


def evaluate_time_split(df: pd.DataFrame) -> dict:
    """Time-split (train ≤ 2023 / test 2024+)."""
    logger.info("=== Time-split ===")
    train_df = df[df["year_made"] <= TIME_SPLIT_YEAR].copy()
    test_df = df[df["year_made"] >= TIME_SPLIT_YEAR + 1].copy()

    train_cnt = train_df.groupby("artist_slug").size()
    test_df["__train_count"] = test_df["artist_slug"].map(train_cnt).fillna(0).astype(int)
    cold_mask = test_df["__train_count"] < COLD_TRAIN_COUNT_THRESHOLD

    out = {
        "n_train": len(train_df), "n_test": len(test_df),
        "n_test_cold": int(cold_mask.sum()),
    }

    logger.info("Track 1 surrogate fit + predict...")
    t1_pred = fit_track1_surrogate(train_df, test_df)
    t1_cold_mdape = mdape_pct(test_df.loc[cold_mask, "log_price"].values, t1_pred[cold_mask.values])
    cold_test_df = test_df[cold_mask].copy()
    t1_ci = cluster_bootstrap_ci(cold_test_df, t1_pred[cold_mask.values])
    out["track1_surrogate"] = {
        "cold_mdape": t1_cold_mdape,
        "ci_95_cold": list(t1_ci),
    }
    # Train cold (in-sample for degradation)
    t1_pred_tr = fit_track1_surrogate(train_df, train_df)
    train_cnt_train = train_df.groupby("artist_slug").size()
    train_df["__train_count"] = train_df["artist_slug"].map(train_cnt_train).fillna(0).astype(int)
    train_cold_mask = train_df["__train_count"] < COLD_TRAIN_COUNT_THRESHOLD
    t1_train_cold_mdape = mdape_pct(train_df.loc[train_cold_mask, "log_price"].values, t1_pred_tr[train_cold_mask.values])
    out["track1_surrogate"]["train_cold_mdape"] = t1_train_cold_mdape
    out["track1_surrogate"]["time_degradation_pp"] = t1_cold_mdape - t1_train_cold_mdape
    logger.info("  Track 1 surrogate cold_mdape=%.2f%% degradation=%.2f%%p", t1_cold_mdape, t1_cold_mdape - t1_train_cold_mdape)

    logger.info("Track 2 fit + predict...")
    t2_pred = fit_track2(train_df, test_df)
    t2_cold_mdape = mdape_pct(test_df.loc[cold_mask, "log_price"].values, t2_pred[cold_mask.values])
    t2_ci = cluster_bootstrap_ci(cold_test_df, t2_pred[cold_mask.values])
    out["track2"] = {
        "cold_mdape": t2_cold_mdape,
        "ci_95_cold": list(t2_ci),
    }
    t2_pred_tr = fit_track2(train_df, train_df)
    t2_train_cold_mdape = mdape_pct(train_df.loc[train_cold_mask, "log_price"].values, t2_pred_tr[train_cold_mask.values])
    out["track2"]["train_cold_mdape"] = t2_train_cold_mdape
    out["track2"]["time_degradation_pp"] = t2_cold_mdape - t2_train_cold_mdape
    logger.info("  Track 2 cold_mdape=%.2f%% degradation=%.2f%%p", t2_cold_mdape, t2_cold_mdape - t2_train_cold_mdape)

    out["delta_t2_minus_t1"] = t2_cold_mdape - t1_cold_mdape
    return out


def main() -> None:
    logger.info("Loading: %s", DATA)
    df = pd.read_parquet(DATA)
    logger.info("shape=%s artists=%d", df.shape, df["artist_slug"].nunique())

    rlao = evaluate_random_lao(df)
    tsplit = evaluate_time_split(df)

    out = {
        "prereg": "docs/track1_vs_track2_comparison_prereg_20260508.md",
        "decision_binding": False,
        "caveat": "Track 1 surrogate (14 derivable features, CatBoost) ≠ 운영 Track 1 (32 features). decision-binding X / supportive only.",
        "dataset": str(DATA.name),
        "n_total": int(len(df)),
        "random_lao": rlao,
        "time_split": tsplit,
        "spec": {
            "track1_surrogate": {
                "model": "CatBoost",
                "n_features": 14,
                "iterations": CB_ITERATIONS,
                "learning_rate": CB_LEARNING_RATE,
                "depth": CB_DEPTH,
            },
            "track2": {
                "model": "HuberRegressor (sklearn)",
                "epsilon": HUBER_EPS,
                "alpha": HUBER_ALPHA,
                "n_features": 4,
                "features": "F4 + log_area_spline",
            },
            "n_boot": N_BOOT,
            "seed": SEED,
            "cold_threshold": COLD_TRAIN_COUNT_THRESHOLD,
        },
    }
    out_path = RESULTS_DIR / "track1_vs_track2_comparison.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    logger.info("Wrote %s", out_path)


if __name__ == "__main__":
    main()
