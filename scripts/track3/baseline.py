"""Track 3 — Phase 0 baseline.

Plan v2.1 §5 Phase 0 구현:
1. Median baseline (Cold + Warm)
2. estimated_ho vs log_area ablation (LightGBM 빠른 baseline)

평가 metric (Plan §3.3):
    - median APE   primary (cold)
    - log-RMSE     secondary primary
    - Within-30%   business
    - MAPE, Within-50%  reference

Cold-start은 GroupKFold(5) × seed 1회 (Phase 0 빠른 진행).
Warm은 N=3 seeds로 분포 측정 (Phase 0 빠르게, 최종은 N=20).
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
OUT_PATH = REPO / "data" / "track3_baseline_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"

# Feature 변형 (ho/area ablation)
COMMON_FEATURES = [
    "medium_category", "support_category", "has_depth", "orientation",
]
VARIANTS = {
    "both":     COMMON_FEATURES + ["log_area", "estimated_ho"],
    "area_only": COMMON_FEATURES + ["log_area"],
    "ho_only":   COMMON_FEATURES + ["estimated_ho"],
}

CATEGORICAL_COLS = {"medium_category", "support_category", "orientation"}

LGB_PARAMS = {
    "objective": "regression",
    "metric": "rmse",
    "learning_rate": 0.05,
    "num_leaves": 63,
    "min_data_in_leaf": 20,
    "feature_fraction": 0.9,
    "bagging_fraction": 0.9,
    "bagging_freq": 5,
    "verbose": -1,
}


def compute_metrics(y_true_ln: np.ndarray, y_pred_ln: np.ndarray) -> dict:
    """log 공간 예측 → 원본 KRW 복원 후 metric 계산."""
    y_true = np.exp(y_true_ln)
    y_pred = np.exp(y_pred_ln)
    ape = np.abs(y_pred - y_true) / y_true
    log_resid = y_pred_ln - y_true_ln
    return {
        "median_ape": float(np.median(ape)),
        "mape": float(np.mean(ape)),
        "rmse_log": float(np.sqrt(np.mean(log_resid ** 2))),
        "within_30pct": float(np.mean(np.abs(y_pred / y_true - 1) < 0.30)),
        "within_50pct": float(np.mean(np.abs(y_pred / y_true - 1) < 0.50)),
    }


def to_categorical(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    """LightGBM categorical dtype 변환."""
    df = df[features].copy()
    for col in features:
        if col in CATEGORICAL_COLS:
            df[col] = df[col].astype("category")
    return df


# ────────── 1. Median Baseline ──────────

def median_baseline_cold(df: pd.DataFrame, cold_folds: list, dev_df: pd.DataFrame) -> dict:
    """Cold-start median baseline: train fold의 median(ln_price)을 test에 그대로 예측."""
    fold_results = []
    for fold in cold_folds:
        train_idx = fold["train_indices"]
        test_idx = fold["test_indices"]
        median_ln = dev_df.iloc[train_idx][TARGET].median()
        y_pred = np.full(len(test_idx), median_ln)
        y_true = dev_df.iloc[test_idx][TARGET].values
        m = compute_metrics(y_true, y_pred)
        m["fold"] = fold["fold"]
        fold_results.append(m)

    # Aggregate
    agg = {
        "n_folds": len(fold_results),
        "per_fold": fold_results,
        "median": {k: float(np.median([f[k] for f in fold_results]))
                   for k in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct"]},
        "mean": {k: float(np.mean([f[k] for f in fold_results]))
                 for k in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct"]},
    }
    return agg


def median_baseline_warm(dev_df: pd.DataFrame, warm_splits: list, n_seeds: int = 3) -> dict:
    """Warm-start median baseline (multi-seed)."""
    seed_results = []
    for split in warm_splits[:n_seeds]:
        train_idx = split["train_indices"]
        test_idx = split["test_indices"]
        median_ln = dev_df.iloc[train_idx][TARGET].median()
        y_pred = np.full(len(test_idx), median_ln)
        y_true = dev_df.iloc[test_idx][TARGET].values
        m = compute_metrics(y_true, y_pred)
        m["seed"] = split["seed"]
        seed_results.append(m)

    agg = {
        "n_seeds": len(seed_results),
        "per_seed": seed_results,
        "mean": {k: float(np.mean([s[k] for s in seed_results]))
                 for k in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct"]},
        "std": {k: float(np.std([s[k] for s in seed_results]))
                for k in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct"]},
    }
    return agg


# ────────── 2. LightGBM Cold-start (ho/area ablation) ──────────

def lgb_cold_variant(
    dev_df: pd.DataFrame, cold_folds: list, features: list[str], seed: int = 42
) -> dict:
    """Cold-start GroupKFold(5)로 단일 LightGBM 학습 + 평가."""
    fold_results = []
    for fold in cold_folds:
        train_idx = fold["train_indices"]
        test_idx = fold["test_indices"]
        X_train = to_categorical(dev_df.iloc[train_idx], features)
        X_test = to_categorical(dev_df.iloc[test_idx], features)
        y_train = dev_df.iloc[train_idx][TARGET].values
        y_test = dev_df.iloc[test_idx][TARGET].values

        # Train-only val split (10%)
        n_train = len(X_train)
        rng = np.random.default_rng(seed)
        val_size = int(n_train * 0.1)
        idx_perm = rng.permutation(n_train)
        val_idx_inner = idx_perm[:val_size]
        train_idx_inner = idx_perm[val_size:]

        cat_features = [c for c in features if c in CATEGORICAL_COLS]
        train_set = lgb.Dataset(X_train.iloc[train_idx_inner], y_train[train_idx_inner],
                                categorical_feature=cat_features)
        val_set = lgb.Dataset(X_train.iloc[val_idx_inner], y_train[val_idx_inner],
                              categorical_feature=cat_features, reference=train_set)
        model = lgb.train(
            {**LGB_PARAMS, "seed": seed},
            train_set,
            num_boost_round=1000,
            valid_sets=[val_set],
            callbacks=[lgb.early_stopping(stopping_rounds=30, verbose=False)],
        )
        y_pred = model.predict(X_test)
        m = compute_metrics(y_test, y_pred)
        m["fold"] = fold["fold"]
        m["best_iter"] = int(model.best_iteration)
        fold_results.append(m)

    agg = {
        "n_features": len(features),
        "features": features,
        "n_folds": len(fold_results),
        "per_fold": fold_results,
        "median": {k: float(np.median([f[k] for f in fold_results]))
                   for k in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct"]},
    }
    return agg


def main() -> None:
    logger.info("=" * 70)
    logger.info("Track 3 Phase 0 — Baseline + estimated_ho vs log_area ablation")
    logger.info("=" * 70)

    # Load split metadata
    outer_meta = json.loads((SPLITS_DIR / "outer_holdout_artists.json").read_text())
    cold_meta = json.loads((SPLITS_DIR / "cold_folds.json").read_text())
    warm_meta = json.loads((SPLITS_DIR / "warm_splits.json").read_text())

    # Reconstruct dev_df (outer holdout 제외)
    df = pd.read_csv(DATA_PATH)
    dev_artists = set(outer_meta["dev_artists"])
    dev_df = df[df[ARTIST_COL].isin(dev_artists)].reset_index(drop=True)
    logger.info(f"Dev pool: {len(dev_df):,} rows / {dev_df[ARTIST_COL].nunique():,} 작가")

    # 1. Median baseline
    logger.info("\n--- Step 1: Median Baseline ---")
    cold_median = median_baseline_cold(df, cold_meta["folds"], dev_df)
    warm_median = median_baseline_warm(dev_df, warm_meta["splits"], n_seeds=3)
    logger.info(f"Cold median baseline (5-fold): median_APE = {cold_median['median']['median_ape']:.3f}")
    logger.info(f"Warm median baseline (3 seeds): median_APE = {warm_median['mean']['median_ape']:.3f}")

    # 2. ho/area ablation (LightGBM, Cold-only)
    logger.info("\n--- Step 2: estimated_ho vs log_area ablation (LightGBM Cold) ---")
    ablation = {}
    for variant_name, features in VARIANTS.items():
        logger.info(f"\nVariant '{variant_name}': {len(features)} features = {features}")
        res = lgb_cold_variant(dev_df, cold_meta["folds"], features, seed=42)
        ablation[variant_name] = res
        logger.info(
            f"  median_APE={res['median']['median_ape']:.3f} "
            f"MAPE={res['median']['mape']:.3f} "
            f"RMSE_log={res['median']['rmse_log']:.3f} "
            f"W30={res['median']['within_30pct']:.3f}"
        )

    # 결과 출력
    print()
    print("=" * 80)
    print("📊 Phase 0 결과 — Cold (GroupKFold 5) Baseline + ho/area Ablation")
    print("=" * 80)
    print(f"{'Variant':<20} {'med_APE':>9} {'MAPE':>8} {'RMSE_log':>9} {'W30':>7} {'W50':>7}")
    print("-" * 80)
    print(f"{'median baseline':<20} {cold_median['median']['median_ape']:>9.3f} "
          f"{cold_median['median']['mape']:>8.3f} {cold_median['median']['rmse_log']:>9.3f} "
          f"{cold_median['median']['within_30pct']:>7.3f} {cold_median['median']['within_50pct']:>7.3f}")
    for variant_name, res in ablation.items():
        m = res["median"]
        print(f"{'LGB ' + variant_name:<20} {m['median_ape']:>9.3f} {m['mape']:>8.3f} "
              f"{m['rmse_log']:>9.3f} {m['within_30pct']:>7.3f} {m['within_50pct']:>7.3f}")

    print()
    print("📝 해석:")
    print(f"  - median baseline = 단일 값 예측 (cold) — 75% 목표 대비 출발점")
    print(f"  - LGB '{min(ablation, key=lambda k: ablation[k]['median'][_ := 'median_ape'])}'가 가장 우수")
    print(f"  - both vs area_only/ho_only 차이 → estimated_ho 추가 가치 판단")
    print()

    # Warm summary
    print("=" * 80)
    print("📊 Phase 0 결과 — Warm (random 80/10/10, N=3 seeds) Median Baseline")
    print("=" * 80)
    m_w = warm_median["mean"]
    s_w = warm_median["std"]
    print(f"{'median baseline':<20} med_APE={m_w['median_ape']:.3f}±{s_w['median_ape']:.3f}  "
          f"MAPE={m_w['mape']:.3f}±{s_w['mape']:.3f}  "
          f"RMSE_log={m_w['rmse_log']:.3f}±{s_w['rmse_log']:.3f}")
    print()

    # Save
    output = {
        "phase": 0,
        "cold_median_baseline": cold_median,
        "warm_median_baseline": warm_median,
        "cold_lgb_ablation": ablation,
    }
    OUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    logger.info(f"✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
