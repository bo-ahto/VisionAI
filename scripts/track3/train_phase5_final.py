"""Track 3 — Phase 5 최종 평가 통합.

Plan v2.1 §5 Phase 5:
  - Cold: LAD 5-fold × 3 seed = 15 runs (GroupKFold deterministic, seed로 LAD 자체는 deterministic이나 inner split변동)
  - Warm: LightGBM N=20 seeds
  - Outer holdout 평가 (격리 426 작가)
  - Source-stratified + Price-band stratified
  - Source-balanced weighting stress test (inverse-frequency)
  - Bootstrapping 95% CI

최종 모델:
  Cold = LAD (Quantile_q05) — Phase 1 best
  Warm = LightGBM — Phase 2 best
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
OUT_PATH = REPO / "data" / "track3_phase5_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
PRICE_COL = "price_krw_unified"
SOURCE_COL = "source_platform"
COLD_FEATURES = ["medium_category", "support_category", "has_depth",
                 "log_area", "estimated_ho", "orientation"]
WARM_FEATURES = COLD_FEATURES + ["artist_name_ko"]
CAT_COLS_LIN = ["medium_category", "support_category", "orientation"]
CAT_COLS_TREE_WARM = ["artist_name_ko", "medium_category", "support_category", "orientation"]
SEED_BASE = 42
N_SEEDS_WARM = 20
TE_SMOOTHING = 20.0

PRICE_BANDS = {"B1": (0, 1_000_000), "B2": (1_000_000, 3_000_000),
               "B3": (3_000_000, 10_000_000), "B4": (10_000_000, float("inf"))}


def compute_metrics(y_true_ln, y_pred_ln):
    y_true = np.exp(y_true_ln); y_pred = np.exp(y_pred_ln)
    ape = np.abs(y_pred - y_true) / y_true
    log_resid = y_pred_ln - y_true_ln
    return {"median_ape": float(np.median(ape)), "mape": float(np.mean(ape)),
            "rmse_log": float(np.sqrt(np.mean(log_resid**2))),
            "within_30pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.30)),
            "within_50pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.50)),
            "n": int(len(y_true))}


def source_breakdown(y_true_ln, y_pred_ln, sources):
    result = {}
    for src in ["artsy", "saatchi", "artue"]:
        mask = sources == src
        if mask.sum() > 0:
            result[src] = compute_metrics(y_true_ln[mask], y_pred_ln[mask])
    return result


def price_band_breakdown(y_true_ln, y_pred_ln, prices):
    result = {}
    for band, (lo, hi) in PRICE_BANDS.items():
        mask = (prices > lo) & (prices <= hi)
        if mask.sum() > 0:
            result[band] = compute_metrics(y_true_ln[mask], y_pred_ln[mask])
    for thr_name, thr in [(">100M", 100_000_000)]:
        mask = prices > thr
        if mask.sum() > 0:
            result[thr_name] = compute_metrics(y_true_ln[mask], y_pred_ln[mask])
    return result


def bootstrap_ci(values, n_boot=2000, ci=0.95, seed=SEED_BASE):
    rng = np.random.default_rng(seed)
    boots = []
    n = len(values)
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        boots.append(np.median([values[i] for i in idx]))
    lo, hi = np.percentile(boots, [(1 - ci) * 50, (1 + ci) * 50])
    return float(lo), float(hi)


def smoothed_te(train_df, group_col, target_col, smoothing=TE_SMOOTHING):
    global_mean = train_df[target_col].mean()
    stats = train_df.groupby(group_col)[target_col].agg(["mean", "count"])
    smoothed = (stats["count"] * stats["mean"] + smoothing * global_mean) / (stats["count"] + smoothing)
    return smoothed.to_dict(), float(global_mean)


def to_cat(df, features, cat_cols):
    df = df[features].copy()
    for c in cat_cols:
        if c in df.columns:
            df[c] = df[c].astype("category")
    return df


def build_lad_pipeline(features):
    cat = [c for c in features if c in CAT_COLS_LIN]
    num = [c for c in features if c not in CAT_COLS_LIN]
    preprocess = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", drop="first"), cat),
        ("num", StandardScaler(), num),
    ])
    return Pipeline([("prep", preprocess),
                     ("est", QuantileRegressor(quantile=0.5, solver="highs", alpha=0.0))])


def train_lgb(X_tr, y_tr, X_val, y_val, cat_feat, seed, sample_weight=None):
    params = {"objective": "regression", "metric": "rmse", "learning_rate": 0.05,
              "num_leaves": 127, "min_data_in_leaf": 20, "feature_fraction": 0.9,
              "bagging_fraction": 0.9, "bagging_freq": 5, "verbose": -1, "seed": seed}
    tr_set = lgb.Dataset(X_tr, y_tr, categorical_feature=cat_feat, weight=sample_weight)
    val_set = lgb.Dataset(X_val, y_val, categorical_feature=cat_feat, reference=tr_set)
    return lgb.train(params, tr_set, num_boost_round=2000, valid_sets=[val_set],
                     callbacks=[lgb.early_stopping(30, verbose=False)])


# ─── 1. Cold LAD: 5-fold × 1 (LAD deterministic) — extended report ───

def run_cold_lad(dev_df, cold_folds):
    """Cold LAD on 5-fold GroupKFold. (LAD self deterministic, so 1 run suffices)"""
    fold_results = []
    oof_pred = np.full(len(dev_df), np.nan)
    for fold in cold_folds:
        tr_df = dev_df.iloc[fold["train_indices"]]
        te_df = dev_df.iloc[fold["test_indices"]]
        lad = build_lad_pipeline(COLD_FEATURES)
        lad.fit(tr_df[COLD_FEATURES], tr_df[TARGET].values)
        pred = lad.predict(te_df[COLD_FEATURES])
        oof_pred[fold["test_indices"]] = pred
        m = compute_metrics(te_df[TARGET].values, pred)
        m["fold"] = fold["fold"]
        fold_results.append(m)
        logger.info(f"  Cold LAD fold {fold['fold']}: med_APE={m['median_ape']:.3f}")

    y_true_oof = dev_df[TARGET].values
    sources = dev_df[SOURCE_COL].values
    prices = dev_df[PRICE_COL].values

    fold_meds = [f["median_ape"] for f in fold_results]
    ci_lo, ci_hi = bootstrap_ci(fold_meds)

    return {
        "model": "Cold_LAD",
        "n_folds": 5,
        "per_fold": fold_results,
        "median": {k: float(np.median([f[k] for f in fold_results]))
                   for k in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct"]},
        "median_ape_95ci": [ci_lo, ci_hi],
        "source_breakdown": source_breakdown(y_true_oof, oof_pred, sources),
        "price_band_breakdown": price_band_breakdown(y_true_oof, oof_pred, prices),
    }


# ─── 2. Warm LightGBM: N=20 seeds ───

def run_warm_lgb(dev_df, warm_splits, sample_weight_fn=None, n_seeds=N_SEEDS_WARM):
    seed_results = []
    for split in warm_splits[:n_seeds]:
        train_idx = split["train_indices"]
        val_idx = split["val_indices"]
        test_idx = split["test_indices"]
        tr_df = dev_df.iloc[train_idx]
        va_df = dev_df.iloc[val_idx]
        te_df = dev_df.iloc[test_idx]

        X_tr = to_cat(tr_df, WARM_FEATURES, CAT_COLS_TREE_WARM)
        X_va = to_cat(va_df, WARM_FEATURES, CAT_COLS_TREE_WARM)
        X_te = to_cat(te_df, WARM_FEATURES, CAT_COLS_TREE_WARM)
        y_tr = tr_df[TARGET].values
        y_va = va_df[TARGET].values

        weights = sample_weight_fn(tr_df) if sample_weight_fn else None

        model = train_lgb(X_tr, y_tr, X_va, y_va, CAT_COLS_TREE_WARM,
                          seed=split["seed"], sample_weight=weights)
        pred = model.predict(X_te)
        m = compute_metrics(te_df[TARGET].values, pred)
        m["seed"] = split["seed"]
        seed_results.append(m)

    medians = [s["median_ape"] for s in seed_results]
    ci_lo, ci_hi = bootstrap_ci(medians)

    return {
        "n_seeds": len(seed_results),
        "per_seed": seed_results,
        "mean": {k: float(np.mean([s[k] for s in seed_results]))
                 for k in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct"]},
        "std": {k: float(np.std([s[k] for s in seed_results]))
                for k in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct"]},
        "median_ape_95ci": [ci_lo, ci_hi],
    }


def source_balanced_weights(tr_df):
    """inverse-frequency weighting with cap=3 (Plan v2.1)."""
    counts = tr_df[SOURCE_COL].value_counts()
    total = len(tr_df)
    inv_freq = {src: total / (3 * n) for src, n in counts.items()}
    # cap at 3.0 max weight (relative to min)
    max_w = min(3.0, max(inv_freq.values()))
    weights_dict = {src: min(max_w, w) for src, w in inv_freq.items()}
    return tr_df[SOURCE_COL].map(weights_dict).values


# ─── 3. Outer holdout 평가 ───

def evaluate_outer_holdout(dev_df, holdout_df):
    """전체 dev로 학습 → outer holdout 평가 (Cold + Warm)."""
    results = {}

    # Cold LAD (artist 미사용)
    lad = build_lad_pipeline(COLD_FEATURES)
    lad.fit(dev_df[COLD_FEATURES], dev_df[TARGET].values)
    pred_cold = lad.predict(holdout_df[COLD_FEATURES])
    y_true = holdout_df[TARGET].values
    results["cold_lad_holdout"] = compute_metrics(y_true, pred_cold)
    results["cold_lad_source"] = source_breakdown(y_true, pred_cold, holdout_df[SOURCE_COL].values)
    results["cold_lad_price_band"] = price_band_breakdown(y_true, pred_cold, holdout_df[PRICE_COL].values)
    logger.info(f"  Cold LAD outer: med_APE={results['cold_lad_holdout']['median_ape']:.3f}")

    # Warm LightGBM (artist 사용)
    # For unseen artist in holdout, native categorical handles via "default" branch (pandas Categorical unknowns)
    rng = np.random.default_rng(SEED_BASE)
    perm = rng.permutation(len(dev_df))
    cut = int(len(dev_df) * 0.1)
    va_idx = perm[:cut]
    tr_idx = perm[cut:]
    X_tr = to_cat(dev_df.iloc[tr_idx], WARM_FEATURES, CAT_COLS_TREE_WARM)
    X_va = to_cat(dev_df.iloc[va_idx], WARM_FEATURES, CAT_COLS_TREE_WARM)
    # Holdout: pandas Categorical with same set as train (unseen 작가는 NaN으로 처리됨)
    # 더 안전: TE 같이 fallback
    X_ho = to_cat(holdout_df, WARM_FEATURES, CAT_COLS_TREE_WARM)
    model = train_lgb(X_tr, dev_df.iloc[tr_idx][TARGET].values,
                      X_va, dev_df.iloc[va_idx][TARGET].values, CAT_COLS_TREE_WARM, seed=SEED_BASE)
    pred_warm = model.predict(X_ho)
    results["warm_lgb_holdout"] = compute_metrics(y_true, pred_warm)
    results["warm_lgb_source"] = source_breakdown(y_true, pred_warm, holdout_df[SOURCE_COL].values)
    results["warm_lgb_price_band"] = price_band_breakdown(y_true, pred_warm, holdout_df[PRICE_COL].values)
    logger.info(f"  Warm LGB outer: med_APE={results['warm_lgb_holdout']['median_ape']:.3f}")
    # Note: outer holdout = all unseen artists (cold-start scenario), Warm 모델은 이 케이스 unfavorable
    logger.info("  (Note: outer holdout = unseen artists. Warm 모델은 본질적으로 cold-start 상황)")

    return results


def main():
    logger.info("=" * 70)
    logger.info("Track 3 Phase 5 — 최종 평가")
    logger.info("=" * 70)

    outer_meta = json.loads((SPLITS_DIR / "outer_holdout_artists.json").read_text())
    cold_meta = json.loads((SPLITS_DIR / "cold_folds.json").read_text())
    warm_meta = json.loads((SPLITS_DIR / "warm_splits.json").read_text())
    df = pd.read_csv(DATA_PATH)

    dev_artists = set(outer_meta["dev_artists"])
    holdout_artists = set(outer_meta["holdout_artists"])
    dev_df = df[df[ARTIST_COL].isin(dev_artists)].reset_index(drop=True)
    holdout_df = df[df[ARTIST_COL].isin(holdout_artists)].reset_index(drop=True)
    logger.info(f"Dev: {len(dev_df):,} rows / {dev_df[ARTIST_COL].nunique():,} 작가")
    logger.info(f"Outer holdout: {len(holdout_df):,} rows / {holdout_df[ARTIST_COL].nunique():,} 작가")

    final = {}

    # 1. Cold LAD
    logger.info("\n--- Cold LAD (5-fold GroupKFold) ---")
    final["cold_lad"] = run_cold_lad(dev_df, cold_meta["folds"])
    cl = final["cold_lad"]
    logger.info(f"  fold-median: med_APE={cl['median']['median_ape']:.3f} 95%CI=[{cl['median_ape_95ci'][0]:.3f}, {cl['median_ape_95ci'][1]:.3f}]")

    # 2. Warm LightGBM N=20
    logger.info(f"\n--- Warm LightGBM (N={N_SEEDS_WARM} seeds) ---")
    final["warm_lgb"] = run_warm_lgb(dev_df, warm_meta["splits"])
    wm = final["warm_lgb"]
    logger.info(f"  mean: med_APE={wm['mean']['median_ape']:.3f}±{wm['std']['median_ape']:.3f} "
                f"95%CI=[{wm['median_ape_95ci'][0]:.3f}, {wm['median_ape_95ci'][1]:.3f}]")

    # 3. Source-balanced stress (Warm)
    logger.info(f"\n--- Warm LightGBM source-balanced (inverse-freq weight, cap=3) ---")
    final["warm_lgb_balanced"] = run_warm_lgb(dev_df, warm_meta["splits"], sample_weight_fn=source_balanced_weights, n_seeds=3)
    wb = final["warm_lgb_balanced"]
    logger.info(f"  mean: med_APE={wb['mean']['median_ape']:.3f}±{wb['std']['median_ape']:.3f}")

    # 4. Outer holdout
    logger.info("\n--- Outer holdout 평가 (격리 426 작가) ---")
    final["outer_holdout"] = evaluate_outer_holdout(dev_df, holdout_df)

    # ─── 결과 출력 ───
    print()
    print("=" * 80)
    print("📊 Phase 5 — Track 3 최종 평가 결과")
    print("=" * 80)
    print()
    print("[1] Cold LAD (5-fold GroupKFold OOF)")
    print("-" * 80)
    m = cl["median"]
    print(f"  med_APE={m['median_ape']:.3f}  95% CI = [{cl['median_ape_95ci'][0]:.3f}, {cl['median_ape_95ci'][1]:.3f}]")
    print(f"  MAPE={m['mape']:.3f}  RMSE_log={m['rmse_log']:.3f}  W30={m['within_30pct']:.3f}  W50={m['within_50pct']:.3f}")
    print("  Source breakdown:")
    for src, ms in cl["source_breakdown"].items():
        print(f"    {src:<8} n={ms['n']:>6,}  med_APE={ms['median_ape']:.3f}  W30={ms['within_30pct']:.3f}")
    print("  Price-band breakdown:")
    for band, ms in cl["price_band_breakdown"].items():
        print(f"    {band:<6} n={ms['n']:>6,}  med_APE={ms['median_ape']:.3f}  W30={ms['within_30pct']:.3f}")

    print()
    print(f"[2] Warm LightGBM (N={N_SEEDS_WARM} random splits)")
    print("-" * 80)
    m, s = wm["mean"], wm["std"]
    print(f"  med_APE={m['median_ape']:.3f}±{s['median_ape']:.3f}  95% CI = [{wm['median_ape_95ci'][0]:.3f}, {wm['median_ape_95ci'][1]:.3f}]")
    print(f"  MAPE={m['mape']:.3f}±{s['mape']:.3f}  RMSE_log={m['rmse_log']:.3f}  W30={m['within_30pct']:.3f}")

    print()
    print("[3] Warm Source-balanced stress test (N=3)")
    print("-" * 80)
    m, s = wb["mean"], wb["std"]
    print(f"  med_APE={m['median_ape']:.3f}±{s['median_ape']:.3f}  W30={m['within_30pct']:.3f}")
    print(f"  (메인 vs balanced 차이 = {wb['mean']['median_ape'] - wm['mean']['median_ape']:+.3f})")

    print()
    print("[4] Outer Holdout 최종 평가 (격리 426 작가 / 7,246 rows)")
    print("-" * 80)
    oh = final["outer_holdout"]
    print(f"  Cold LAD outer: med_APE={oh['cold_lad_holdout']['median_ape']:.3f}  "
          f"W30={oh['cold_lad_holdout']['within_30pct']:.3f}")
    print(f"  Warm LGB outer: med_APE={oh['warm_lgb_holdout']['median_ape']:.3f}  "
          f"W30={oh['warm_lgb_holdout']['within_30pct']:.3f}")
    print("  (outer = all unseen artists → Warm 모델 본질적으로 cold-start)")

    OUT_PATH.write_text(json.dumps(final, indent=2, ensure_ascii=False))
    logger.info(f"✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
