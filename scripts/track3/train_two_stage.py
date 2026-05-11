"""Track 3 — Phase 4.5 거장 long-tail 2-stage 모델.

Plan v2.1 §4.5:
  Stage 1: 고가 분류기 (>10M binary)
  Stage 2: 구간별 회귀 (일반 / 고가 별도 LightGBM)

Cold + Warm 양쪽.
Trigger 발동 (B4 med_APE 64%, >100M 98.6%) → 즉시 실행.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
DATA_PATH = REPO / "data" / "track3_unified_v1_train.csv"
SPLITS_DIR = REPO / "data" / "track3_splits"
OUT_PATH = REPO / "data" / "track3_phase45_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
PRICE_COL = "price_krw_unified"
COLD_FEATURES = ["medium_category", "support_category", "has_depth",
                 "log_area", "estimated_ho", "orientation"]
WARM_FEATURES = COLD_FEATURES + ["artist_name_ko"]
CAT_COLS_COLD = ["medium_category", "support_category", "orientation"]
CAT_COLS_WARM = ["artist_name_ko", "medium_category", "support_category", "orientation"]
SEED = 42
HIGH_THRESHOLD = 10_000_000  # B4 cut


def compute_metrics(y_true_ln, y_pred_ln):
    y_true = np.exp(y_true_ln); y_pred = np.exp(y_pred_ln)
    ape = np.abs(y_pred - y_true) / y_true
    log_resid = y_pred_ln - y_true_ln
    return {"median_ape": float(np.median(ape)), "mape": float(np.mean(ape)),
            "rmse_log": float(np.sqrt(np.mean(log_resid**2))),
            "within_30pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.30)),
            "within_50pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.50)),
            "n": int(len(y_true))}


def to_cat(df, features, cat_cols):
    df = df[features].copy()
    for c in cat_cols:
        if c in df.columns:
            df[c] = df[c].astype("category")
    return df


def train_lgb_reg(X_tr, y_tr, X_val, y_val, cat_feat, seed=SEED):
    params = {"objective": "regression", "metric": "rmse", "learning_rate": 0.05,
              "num_leaves": 127, "min_data_in_leaf": 20, "feature_fraction": 0.9,
              "bagging_fraction": 0.9, "bagging_freq": 5, "verbose": -1, "seed": seed}
    tr_set = lgb.Dataset(X_tr, y_tr, categorical_feature=cat_feat)
    val_set = lgb.Dataset(X_val, y_val, categorical_feature=cat_feat, reference=tr_set)
    return lgb.train(params, tr_set, num_boost_round=2000, valid_sets=[val_set],
                     callbacks=[lgb.early_stopping(30, verbose=False)])


def train_lgb_clf(X_tr, y_tr, X_val, y_val, cat_feat, seed=SEED):
    params = {"objective": "binary", "metric": "binary_logloss", "learning_rate": 0.05,
              "num_leaves": 63, "min_data_in_leaf": 20, "feature_fraction": 0.9,
              "verbose": -1, "seed": seed}
    tr_set = lgb.Dataset(X_tr, y_tr, categorical_feature=cat_feat)
    val_set = lgb.Dataset(X_val, y_val, categorical_feature=cat_feat, reference=tr_set)
    return lgb.train(params, tr_set, num_boost_round=1000, valid_sets=[val_set],
                     callbacks=[lgb.early_stopping(30, verbose=False)])


def two_stage_predict(tr_df, te_df, features, cat_cols, seed=SEED):
    """1단계: high price 분류기. 2단계: 분류별 별도 회귀."""
    # Inner val split (10%)
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(tr_df))
    cut = int(len(tr_df) * 0.1)
    va_idx = perm[:cut]; tr_idx = perm[cut:]
    tr_in = tr_df.iloc[tr_idx]
    va_in = tr_df.iloc[va_idx]

    # Stage 1 — classifier (high price binary)
    y_high_tr = (tr_in[PRICE_COL] > HIGH_THRESHOLD).astype(int).values
    y_high_va = (va_in[PRICE_COL] > HIGH_THRESHOLD).astype(int).values
    X_tr = to_cat(tr_in, features, cat_cols)
    X_va = to_cat(va_in, features, cat_cols)
    X_te = to_cat(te_df, features, cat_cols)
    clf = train_lgb_clf(X_tr, y_high_tr, X_va, y_high_va, cat_cols, seed=seed)
    high_prob_te = clf.predict(X_te)
    high_pred_te = (high_prob_te > 0.5).astype(int)

    # Stage 2A — normal regression (price ≤ 10M)
    normal_mask = tr_in[PRICE_COL] <= HIGH_THRESHOLD
    if normal_mask.sum() > 100:
        X_n_tr = X_tr[normal_mask.values]
        y_n_tr = tr_in[normal_mask][TARGET].values
        normal_va_mask = va_in[PRICE_COL] <= HIGH_THRESHOLD
        X_n_va = X_va[normal_va_mask.values] if normal_va_mask.sum() > 10 else X_va.iloc[:50]
        y_n_va = va_in[normal_va_mask][TARGET].values if normal_va_mask.sum() > 10 else va_in[TARGET].values[:50]
        model_normal = train_lgb_reg(X_n_tr, y_n_tr, X_n_va, y_n_va, cat_cols, seed=seed)
        pred_normal_te = model_normal.predict(X_te)
    else:
        pred_normal_te = np.full(len(te_df), tr_in[TARGET].mean())

    # Stage 2B — high regression (price > 10M)
    high_mask = tr_in[PRICE_COL] > HIGH_THRESHOLD
    if high_mask.sum() > 100:
        X_h_tr = X_tr[high_mask.values]
        y_h_tr = tr_in[high_mask][TARGET].values
        high_va_mask = va_in[PRICE_COL] > HIGH_THRESHOLD
        X_h_va = X_va[high_va_mask.values] if high_va_mask.sum() > 10 else X_va.iloc[:50]
        y_h_va = va_in[high_va_mask][TARGET].values if high_va_mask.sum() > 10 else va_in[TARGET].values[:50]
        model_high = train_lgb_reg(X_h_tr, y_h_tr, X_h_va, y_h_va, cat_cols, seed=seed)
        pred_high_te = model_high.predict(X_te)
    else:
        pred_high_te = np.full(len(te_df), tr_in[TARGET].mean())

    # Soft combination: classifier prob weighted
    y_pred = (1 - high_prob_te) * pred_normal_te + high_prob_te * pred_high_te
    return y_pred, high_pred_te


def two_stage_cold(dev_df, cold_folds):
    fold_results = []
    for fold in cold_folds:
        tr_df = dev_df.iloc[fold["train_indices"]]
        te_df = dev_df.iloc[fold["test_indices"]]
        y_pred, _ = two_stage_predict(tr_df, te_df, COLD_FEATURES, CAT_COLS_COLD)
        y_true = te_df[TARGET].values
        m = compute_metrics(y_true, y_pred)
        m["fold"] = fold["fold"]
        # B4 / >100M breakdown
        prices = te_df[PRICE_COL].values
        for band, mask in [("B4", prices > 10_000_000), (">100M", prices > 100_000_000)]:
            if mask.sum() > 0:
                m[f"{band}_median_ape"] = float(np.median(np.abs(np.exp(y_pred[mask]) - np.exp(y_true[mask])) / np.exp(y_true[mask])))
                m[f"{band}_n"] = int(mask.sum())
        fold_results.append(m)
        logger.info(f"  Cold fold {fold['fold']}: med_APE={m['median_ape']:.3f}, "
                    f"B4_med_APE={m.get('B4_median_ape', 0):.3f}, >100M_med_APE={m.get('>100M_median_ape', 0):.3f}")

    return {"model": "Cold_2stage", "n_folds": len(fold_results), "per_fold": fold_results,
            "median": {k: float(np.median([f.get(k, 0) for f in fold_results]))
                       for k in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct",
                                "B4_median_ape", ">100M_median_ape"]}}


def two_stage_warm(dev_df, warm_splits, n_seeds=3):
    seed_results = []
    for split in warm_splits[:n_seeds]:
        tr_df = dev_df.iloc[split["train_indices"]]
        te_df = dev_df.iloc[split["test_indices"]]
        y_pred, _ = two_stage_predict(tr_df, te_df, WARM_FEATURES, CAT_COLS_WARM, seed=split["seed"])
        y_true = te_df[TARGET].values
        m = compute_metrics(y_true, y_pred)
        m["seed"] = split["seed"]
        prices = te_df[PRICE_COL].values
        for band, mask in [("B4", prices > 10_000_000), (">100M", prices > 100_000_000)]:
            if mask.sum() > 0:
                m[f"{band}_median_ape"] = float(np.median(np.abs(np.exp(y_pred[mask]) - np.exp(y_true[mask])) / np.exp(y_true[mask])))
                m[f"{band}_n"] = int(mask.sum())
        seed_results.append(m)
        logger.info(f"  Warm seed {split['seed']}: med_APE={m['median_ape']:.3f}, "
                    f"B4={m.get('B4_median_ape', 0):.3f}")

    return {"model": "Warm_2stage", "n_seeds": len(seed_results), "per_seed": seed_results,
            "mean": {k: float(np.mean([s.get(k, 0) for s in seed_results]))
                     for k in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct",
                              "B4_median_ape", ">100M_median_ape"]}}


def main():
    logger.info("=" * 70)
    logger.info("Track 3 Phase 4.5 — 2-stage 거장 long-tail 모델")
    logger.info("=" * 70)

    outer_meta = json.loads((SPLITS_DIR / "outer_holdout_artists.json").read_text())
    cold_meta = json.loads((SPLITS_DIR / "cold_folds.json").read_text())
    warm_meta = json.loads((SPLITS_DIR / "warm_splits.json").read_text())
    df = pd.read_csv(DATA_PATH)
    dev_artists = set(outer_meta["dev_artists"])
    dev_df = df[df[ARTIST_COL].isin(dev_artists)].reset_index(drop=True)
    logger.info(f"Dev pool: {len(dev_df):,} rows")

    logger.info("\n--- Cold 2-stage ---")
    cold_res = two_stage_cold(dev_df, cold_meta["folds"])
    logger.info(f"Cold 2-stage median: med_APE={cold_res['median']['median_ape']:.3f}, "
                f"B4_med_APE={cold_res['median']['B4_median_ape']:.3f}, "
                f">100M_med_APE={cold_res['median']['>100M_median_ape']:.3f}")

    logger.info("\n--- Warm 2-stage ---")
    warm_res = two_stage_warm(dev_df, warm_meta["splits"])
    logger.info(f"Warm 2-stage mean: med_APE={warm_res['mean']['median_ape']:.3f}, "
                f"B4_med_APE={warm_res['mean']['B4_median_ape']:.3f}")

    print()
    print("=" * 80)
    print("📊 Phase 4.5 — 2-stage 거장 long-tail 결과")
    print("=" * 80)
    print(f"{'Model':<14} {'med_APE':>9} {'B4':>8} {'>100M':>9} {'W30':>7}")
    print("-" * 60)
    cm = cold_res["median"]
    wm = warm_res["mean"]
    print(f"{'Cold 2-stage':<14} {cm['median_ape']:>9.3f} {cm['B4_median_ape']:>8.3f} {cm['>100M_median_ape']:>9.3f} {cm['within_30pct']:>7.3f}")
    print(f"{'Warm 2-stage':<14} {wm['median_ape']:>9.3f} {wm['B4_median_ape']:>8.3f} {wm['>100M_median_ape']:>9.3f} {wm['within_30pct']:>7.3f}")

    print()
    print("📝 Phase 2 LightGBM 단일 vs Phase 4.5 2-stage:")
    print(f"  Cold:   0.473 (B4 0.640, >100M 0.986) → 2-stage: med_APE {cm['median_ape']:.3f} "
          f"(B4 {cm['B4_median_ape']:.3f}, >100M {cm['>100M_median_ape']:.3f})")
    print(f"  Warm:   0.119 (Phase 2)              → 2-stage: med_APE {wm['median_ape']:.3f} "
          f"(B4 {wm['B4_median_ape']:.3f})")

    OUT_PATH.write_text(json.dumps({"cold": cold_res, "warm": warm_res}, indent=2, ensure_ascii=False))
    logger.info(f"✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
