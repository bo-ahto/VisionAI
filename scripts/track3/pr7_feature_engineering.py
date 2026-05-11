"""Track 3 PR7 — Feature Engineering 묶음.

Codex 권장: 최저 노력 / 최대 효과 4건 묶음.
1. Source feature 추가 (PR5에서 +45.5% bias 입증)
2. Interaction terms (medium × estimated_ho)
3. Artist popularity (작가별 작품 수)
4. Aspect ratio (연속값, width/height)

평가:
- Cold LAD: 5-fold GroupKFold OOF
- Warm Tuned LGB: 80/10/10 N=3 seeds

각 feature 추가 효과를 ablation으로 분리:
  baseline → +source → +interaction → +popularity → +aspect → ALL
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.linear_model import QuantileRegressor
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
DATA_PATH = REPO / "data" / "track3_unified_v1_train.csv"
SPLITS_DIR = REPO / "data" / "track3_splits"
OUT_PATH = REPO / "data" / "track3_pr7_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
SOURCE_COL = "source_platform"
SEED = 42

# Base features
BASE_FEATURES = ["medium_category", "support_category", "has_depth",
                 "log_area", "estimated_ho", "orientation"]
BASE_CAT = ["medium_category", "support_category", "orientation"]

# 신규 features
NEW_CAT = ["source_platform", "medium_ho_bucket"]  # source + interaction
NEW_NUM = ["artist_works_log", "aspect_ratio"]


def compute_metrics(y_true_ln, y_pred_ln):
    y_true = np.exp(y_true_ln); y_pred = np.exp(y_pred_ln)
    ape = np.abs(y_pred - y_true) / y_true
    log_resid = y_pred_ln - y_true_ln
    return {"median_ape": float(np.median(ape)),
            "mape": float(np.mean(ape)),
            "rmse_log": float(np.sqrt(np.mean(log_resid**2))),
            "within_30pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.30)),
            "within_50pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.50))}


def make_features(df, variant: str, train_artist_counts: dict | None = None):
    """variant: baseline / source / interaction / popularity / aspect / all
    artist_works_log은 train fold 기준 count를 받음 (leakage 방지)."""
    df = df.copy()

    # Always compute these (used selectively)
    # Interaction: medium × ho bucket
    df["ho_bucket"] = pd.cut(df["estimated_ho"],
                              bins=[-0.1, 5, 20, 50, 200],
                              labels=["0-5", "5-20", "20-50", "50+"]).astype(str)
    df["medium_ho_bucket"] = df["medium_category"].astype(str) + "_" + df["ho_bucket"]

    # Aspect ratio
    df["aspect_ratio"] = np.log(df["width_cm"] / df["height_cm"].replace(0, 1))

    # Artist popularity (train fold count)
    if train_artist_counts is not None:
        df["artist_works"] = df[ARTIST_COL].map(train_artist_counts).fillna(0)
        df["artist_works_log"] = np.log1p(df["artist_works"])
    else:
        df["artist_works_log"] = 0.0

    return df


def get_feature_list(variant: str, include_artist: bool):
    """variant별로 features 결정."""
    feats = list(BASE_FEATURES)
    cat = list(BASE_CAT)
    if include_artist:
        feats.append(ARTIST_COL)
        cat.append(ARTIST_COL)

    if variant in ["source", "all"]:
        feats.append(SOURCE_COL); cat.append(SOURCE_COL)
    if variant in ["interaction", "all"]:
        feats.append("medium_ho_bucket"); cat.append("medium_ho_bucket")
    if variant in ["popularity", "all"]:
        feats.append("artist_works_log")
    if variant in ["aspect", "all"]:
        feats.append("aspect_ratio")
    return feats, cat


def build_lad(features, cat_cols):
    cat = [c for c in features if c in cat_cols]
    num = [c for c in features if c not in cat_cols]
    preprocess = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", drop="first", max_categories=100), cat),
        ("num", StandardScaler(), num),
    ])
    return Pipeline([("prep", preprocess),
                     ("est", QuantileRegressor(quantile=0.5, solver="highs", alpha=0.0))])


def to_cat(df, features, cat_cols):
    df = df[features].copy()
    for c in cat_cols:
        if c in df.columns:
            df[c] = df[c].astype("category")
    return df


def train_lgb(X_tr, y_tr, X_val, y_val, cat_feat, seed):
    """Tuned LGB params from PR1."""
    params = {"objective": "regression", "metric": "rmse",
              "learning_rate": 0.04, "num_leaves": 198, "min_data_in_leaf": 75,
              "feature_fraction": 0.987, "bagging_fraction": 0.978, "bagging_freq": 5,
              "reg_alpha": 0.36, "reg_lambda": 4.75, "verbose": -1, "seed": seed}
    tr_set = lgb.Dataset(X_tr, y_tr, categorical_feature=cat_feat)
    val_set = lgb.Dataset(X_val, y_val, categorical_feature=cat_feat, reference=tr_set)
    return lgb.train(params, tr_set, num_boost_round=2000, valid_sets=[val_set],
                     callbacks=[lgb.early_stopping(30, verbose=False)])


# ─── Cold evaluation ───

def evaluate_cold(dev_df, cold_folds, variant):
    """Cold LAD with given variant. GroupKFold 5-fold OOF."""
    fold_results = []
    for fold in cold_folds:
        train_idx = fold["train_indices"]; test_idx = fold["test_indices"]
        tr_df = dev_df.iloc[train_idx]
        te_df = dev_df.iloc[test_idx]

        # Artist popularity from train only
        artist_counts = tr_df[ARTIST_COL].value_counts().to_dict()

        # Feature engineering
        tr_feat = make_features(tr_df, variant, artist_counts)
        te_feat = make_features(te_df, variant, artist_counts)
        features, cat_cols = get_feature_list(variant, include_artist=False)

        model = build_lad(features, cat_cols)
        model.fit(tr_feat[features], tr_feat[TARGET].values)
        pred = model.predict(te_feat[features])

        m = compute_metrics(te_feat[TARGET].values, pred)
        m["fold"] = fold["fold"]
        fold_results.append(m)

    return {
        "variant": variant,
        "n_folds": len(fold_results),
        "per_fold": fold_results,
        "median": {k: float(np.median([f[k] for f in fold_results]))
                   for k in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct"]},
    }


# ─── Warm evaluation ───

def evaluate_warm(dev_df, warm_splits, variant, n_seeds=3):
    """Warm Tuned LGB with given variant. N=3 seeds."""
    seed_results = []
    for split in warm_splits[:n_seeds]:
        train_idx = split["train_indices"]; val_idx = split["val_indices"]; test_idx = split["test_indices"]
        tr_df = dev_df.iloc[train_idx]
        va_df = dev_df.iloc[val_idx]
        te_df = dev_df.iloc[test_idx]
        artist_counts = tr_df[ARTIST_COL].value_counts().to_dict()

        tr_feat = make_features(tr_df, variant, artist_counts)
        va_feat = make_features(va_df, variant, artist_counts)
        te_feat = make_features(te_df, variant, artist_counts)
        features, cat_cols = get_feature_list(variant, include_artist=True)

        X_tr = to_cat(tr_feat, features, cat_cols)
        X_va = to_cat(va_feat, features, cat_cols)
        X_te = to_cat(te_feat, features, cat_cols)
        y_tr = tr_feat[TARGET].values
        y_va = va_feat[TARGET].values
        y_te = te_feat[TARGET].values

        model = train_lgb(X_tr, y_tr, X_va, y_va, cat_cols, split["seed"])
        pred = model.predict(X_te)

        m = compute_metrics(y_te, pred)
        m["seed"] = split["seed"]
        seed_results.append(m)

    return {
        "variant": variant,
        "n_seeds": len(seed_results),
        "per_seed": seed_results,
        "mean": {k: float(np.mean([s[k] for s in seed_results]))
                 for k in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct"]},
        "std": {k: float(np.std([s[k] for s in seed_results]))
                for k in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct"]},
    }


def main():
    logger.info("=" * 70)
    logger.info("Track 3 PR7 — Feature Engineering 묶음")
    logger.info("=" * 70)

    outer_meta = json.loads((SPLITS_DIR / "outer_holdout_artists.json").read_text())
    cold_meta = json.loads((SPLITS_DIR / "cold_folds.json").read_text())
    warm_meta = json.loads((SPLITS_DIR / "warm_splits.json").read_text())
    df = pd.read_csv(DATA_PATH)
    dev_artists = set(outer_meta["dev_artists"])
    dev_df = df[df[ARTIST_COL].isin(dev_artists)].reset_index(drop=True)
    logger.info(f"Dev pool: {len(dev_df):,} rows")

    variants = ["baseline", "source", "interaction", "popularity", "aspect", "all"]

    # Cold ablation
    logger.info("\n--- Cold LAD ablation ---")
    cold_results = {}
    for v in variants:
        logger.info(f"  Cold variant '{v}'...")
        res = evaluate_cold(dev_df, cold_meta["folds"], v)
        cold_results[v] = res
        m = res["median"]
        logger.info(f"    med_APE={m['median_ape']:.3f}  MAPE={m['mape']:.3f}  W30={m['within_30pct']:.3f}")

    # Warm ablation
    logger.info("\n--- Warm Tuned LGB ablation ---")
    warm_results = {}
    for v in variants:
        logger.info(f"  Warm variant '{v}'...")
        res = evaluate_warm(dev_df, warm_meta["splits"], v)
        warm_results[v] = res
        m = res["mean"]; s = res["std"]
        logger.info(f"    med_APE={m['median_ape']:.3f}±{s['median_ape']:.3f}  W30={m['within_30pct']:.3f}")

    print()
    print("=" * 80)
    print("📊 PR7 — Feature Engineering Ablation 결과")
    print("=" * 80)
    print()
    print("[Cold LAD] (5-fold GroupKFold OOF, fold-median)")
    print(f"{'Variant':<14} {'med_APE':>9} {'MAPE':>8} {'RMSE_log':>9} {'W30':>7} {'vs base':>10}")
    print("-" * 70)
    base_cold = cold_results["baseline"]["median"]["median_ape"]
    for v, res in cold_results.items():
        m = res["median"]
        delta = m["median_ape"] - base_cold
        mark = "★" if v == "all" else ""
        print(f"{v:<14} {m['median_ape']:>9.3f} {m['mape']:>8.3f} {m['rmse_log']:>9.3f} "
              f"{m['within_30pct']:>7.3f} {delta:>+10.3f} {mark}")

    print()
    print("[Warm Tuned LGB] (random 80/10/10 × N=3)")
    print(f"{'Variant':<14} {'med_APE':>13} {'MAPE':>8} {'W30':>7} {'vs base':>10}")
    print("-" * 70)
    base_warm = warm_results["baseline"]["mean"]["median_ape"]
    for v, res in warm_results.items():
        m = res["mean"]; s = res["std"]
        delta = m["median_ape"] - base_warm
        mark = "★" if v == "all" else ""
        print(f"{v:<14} {m['median_ape']:.3f}±{s['median_ape']:.3f}  "
              f"{m['mape']:>8.3f} {m['within_30pct']:>7.3f} {delta:>+10.3f} {mark}")

    print()
    print("📝 해석:")
    cold_best = min(cold_results, key=lambda v: cold_results[v]["median"]["median_ape"])
    warm_best = min(warm_results, key=lambda v: warm_results[v]["mean"]["median_ape"])
    print(f"  Cold best variant: '{cold_best}' (med_APE={cold_results[cold_best]['median']['median_ape']:.3f})")
    print(f"  Warm best variant: '{warm_best}' (med_APE={warm_results[warm_best]['mean']['median_ape']:.3f})")

    output = {
        "cold": cold_results,
        "warm": warm_results,
        "cold_best_variant": cold_best,
        "warm_best_variant": warm_best,
    }
    OUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    logger.info(f"\n✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
