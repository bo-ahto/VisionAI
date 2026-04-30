"""v3 Group 1.4: Baseline 비교 (HARD gate).

1차 시장 모델 (integrated_v3_filtered_tuned) 의 정확도가 trivial baseline 대비
얼마나 우수한지 정량 비교한다. v3.0 acceptance gate의 유일한 HARD gate:
"v2 MdAPE이 Global median baseline 대비 ≥ 30%p 우수".

3가지 baseline:
1. Global median: 학습 데이터 전체의 ln_price 중앙값을 모든 작품에 동일 예측
2. Per-category mean: medium_category × source 조합 평균 ln_price를 그 셀 모든 작품에 예측
3. Random Forest: scikit-learn RF (n_estimators=200, max_depth=10) — 32 피처
   GroupKFold 5-fold OOF로 cold path 비교 / KFold 5-fold warm slice OOF

산출물:
    model_test_results/v3_diagnostics/baseline_comparison.json

Usage:
    PYTHONPATH=src python3 scripts/v3_baseline_comparison.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold, KFold

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from train_primary_market_v3_filtered import (
    CB_FEATURES, CAT_FEATURES, _warm_mask, load_data, prepare_features,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OOF_PATH = ROOT / "model_test_results" / "v3_diagnostics" / "oof_predictions.npz"
OUT_PATH = ROOT / "model_test_results" / "v3_diagnostics" / "baseline_comparison.json"
N_BOOTSTRAP = 10_000
RNG_SEED = 42


def mdape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    valid = y_true > 0
    return float(np.median(np.abs(y_true[valid] - y_pred[valid]) / y_true[valid]) * 100)


def w30(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    valid = y_true > 0
    return float(np.mean(np.abs(y_true[valid] - y_pred[valid]) / y_true[valid] <= 0.30) * 100)


def bootstrap_ci(
    y_true: np.ndarray, y_pred: np.ndarray, metric_fn,
    n_iter: int = N_BOOTSTRAP, alpha: float = 0.05, rng_seed: int = RNG_SEED,
) -> dict:
    rng = np.random.default_rng(rng_seed)
    n = len(y_true)
    values = np.empty(n_iter)
    for i in range(n_iter):
        idx = rng.integers(0, n, size=n)
        values[i] = metric_fn(y_true[idx], y_pred[idx])
    return {
        "point": float(metric_fn(y_true, y_pred)),
        "ci_low": float(np.percentile(values, 100 * alpha / 2)),
        "ci_high": float(np.percentile(values, 100 * (1 - alpha / 2))),
    }


def metrics(y_true: np.ndarray, y_pred: np.ndarray, n: int) -> dict:
    return {
        "n": int(n),
        "MdAPE": bootstrap_ci(y_true, y_pred, mdape),
        "W30": bootstrap_ci(y_true, y_pred, w30),
    }


def rf_oof_groupkfold(
    X: pd.DataFrame, y: np.ndarray, groups: np.ndarray, n_splits: int = 5,
) -> np.ndarray:
    """RF baseline GroupKFold OOF 예측."""
    gkf = GroupKFold(n_splits=n_splits)
    preds = np.zeros(len(y))
    # categorical → label encoding (RF는 categorical 직접 처리 안함)
    X_enc = X.copy()
    for col in CAT_FEATURES:
        X_enc[col] = pd.Categorical(X_enc[col].astype(str)).codes.astype(float)
    X_enc = X_enc.astype(float)
    for fold, (tr, te) in enumerate(gkf.split(X_enc, y, groups), 1):
        logger.info("[RF GKF %d/%d] train=%d test=%d", fold, n_splits, len(tr), len(te))
        rf = RandomForestRegressor(
            n_estimators=200, max_depth=10, random_state=RNG_SEED, n_jobs=-1,
        )
        rf.fit(X_enc.iloc[tr], y[tr])
        preds[te] = rf.predict(X_enc.iloc[te])
    return preds


def rf_oof_kfold(
    X: pd.DataFrame, y: np.ndarray, n_splits: int = 5,
) -> np.ndarray:
    """RF baseline KFold OOF 예측 (warm slice)."""
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=RNG_SEED)
    preds = np.zeros(len(y))
    X_enc = X.copy()
    for col in CAT_FEATURES:
        X_enc[col] = pd.Categorical(X_enc[col].astype(str)).codes.astype(float)
    X_enc = X_enc.astype(float)
    for fold, (tr, te) in enumerate(kf.split(X_enc), 1):
        logger.info("[RF KF %d/%d] train=%d test=%d", fold, n_splits, len(tr), len(te))
        rf = RandomForestRegressor(
            n_estimators=200, max_depth=10, random_state=RNG_SEED, n_jobs=-1,
        )
        rf.fit(X_enc.iloc[tr], y[tr])
        preds[te] = rf.predict(X_enc.iloc[te])
    return preds


def category_mean_oof(
    df: pd.DataFrame, y: np.ndarray, groups: np.ndarray, n_splits: int = 5,
    keys: tuple[str, ...] = ("medium_category", "source"),
) -> np.ndarray:
    """Per-category mean baseline GroupKFold OOF 예측.

    각 fold의 train 데이터로 (medium_category × source) 별 평균 ln_price 산출 →
    test fold에 적용. unseen 셀은 train 전체 평균으로 fallback.
    """
    gkf = GroupKFold(n_splits=n_splits)
    preds = np.zeros(len(y))
    cell = df[list(keys)].astype(str).agg("|".join, axis=1).to_numpy()
    for fold, (tr, te) in enumerate(gkf.split(df, y, groups), 1):
        logger.info("[CategoryMean GKF %d/%d] train=%d test=%d", fold, n_splits, len(tr), len(te))
        cell_tr = cell[tr]
        y_tr = y[tr]
        # train 셀별 평균
        mean_table: dict[str, float] = {}
        for c in set(cell_tr):
            mean_table[c] = float(np.mean(y_tr[cell_tr == c]))
        global_mean = float(np.mean(y_tr))
        cell_te = cell[te]
        preds[te] = np.array([mean_table.get(c, global_mean) for c in cell_te])
    return preds


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # OOF 산출물 로드 (v2 메트릭 비교용)
    oof = np.load(OOF_PATH, allow_pickle=True)
    y_actual_ln = oof["y_actual_ln"]
    cb_gkf_ln = oof["cb_preds_gkf_ln"]
    xgb_gkf_ln = oof["xgb_preds_gkf_ln"]
    y_warm_ln = oof["y_warm_actual_ln"]
    cb_kf_ln = oof["cb_preds_kf_ln"]
    xgb_kf_ln = oof["xgb_preds_kf_ln"]

    # 데이터 로드 (RF / category mean 학습용)
    df = load_data()
    df_train = df[df.get("is_excluded_for_training", 0) != 1].reset_index(drop=True)
    X, y_train, groups = prepare_features(df_train)
    if len(y_train) != len(y_actual_ln):
        raise RuntimeError(f"length mismatch: y_train={len(y_train)} vs OOF={len(y_actual_ln)}")
    np.testing.assert_allclose(y_train, y_actual_ln, rtol=1e-10, err_msg="y order mismatch")

    # ln → 가격
    y_full = np.exp(y_actual_ln)
    cb_v2_cold = np.exp(cb_gkf_ln)
    xgb_v2_cold = np.exp(xgb_gkf_ln)
    ens_v2_cold = np.exp((cb_gkf_ln + xgb_gkf_ln) / 2)
    y_warm = np.exp(y_warm_ln)
    cb_v2_warm = np.exp(cb_kf_ln)
    xgb_v2_warm = np.exp(xgb_kf_ln)
    ens_v2_warm = np.exp((cb_kf_ln + xgb_kf_ln) / 2)

    # 1. Global median baseline
    logger.info("=== Global median baseline ===")
    global_med = np.full_like(y_full, np.median(y_full))

    # 2. Per-category mean baseline (medium_category × source) — GroupKFold OOF
    logger.info("=== Category mean baseline (medium_category × source) ===")
    cat_mean_ln_cold = category_mean_oof(df_train, y_train, groups, keys=("medium_category", "source"))
    cat_mean_cold = np.exp(cat_mean_ln_cold)

    # 3. Random Forest baseline
    logger.info("=== RF baseline GroupKFold (cold) ===")
    rf_ln_cold = rf_oof_groupkfold(X, y_train, groups)
    rf_cold = np.exp(rf_ln_cold)

    # warm slice용 RF
    wmask = _warm_mask(groups)
    X_warm = X.iloc[wmask].reset_index(drop=True)
    y_warm_train = y_train[wmask]
    np.testing.assert_allclose(y_warm_train, y_warm_ln, rtol=1e-10)
    logger.info("=== RF baseline KFold (warm slice) ===")
    rf_ln_warm = rf_oof_kfold(X_warm, y_warm_train)
    rf_warm = np.exp(rf_ln_warm)

    # 메트릭 산출
    logger.info("=== 메트릭 + Bootstrap CI 산출 ===")
    cold_baselines = {
        "global_median": metrics(y_full, global_med, len(y_full)),
        "category_mean_groupkfold": metrics(y_full, cat_mean_cold, len(y_full)),
        "random_forest_groupkfold": metrics(y_full, rf_cold, len(y_full)),
    }
    cold_v2 = {
        "catboost_v3_filtered_tuned (raw)": metrics(y_full, cb_v2_cold, len(y_full)),
        "xgboost_v3_filtered_tuned (raw)": metrics(y_full, xgb_v2_cold, len(y_full)),
        "ensemble (raw)": metrics(y_full, ens_v2_cold, len(y_full)),
    }
    warm_baselines = {
        "global_median": metrics(y_warm, np.full_like(y_warm, np.median(y_warm)), len(y_warm)),
        "random_forest_kfold": metrics(y_warm, rf_warm, len(y_warm)),
    }
    warm_v2 = {
        "catboost_v3_filtered_tuned": metrics(y_warm, cb_v2_warm, len(y_warm)),
        "xgboost_v3_filtered_tuned": metrics(y_warm, xgb_v2_warm, len(y_warm)),
        "ensemble": metrics(y_warm, ens_v2_warm, len(y_warm)),
    }

    # HARD gate 평가
    v2_cold_best_mdape = cold_v2["ensemble (raw)"]["MdAPE"]["point"]  # 38.66 (raw 기준 최선)
    median_baseline_mdape = cold_baselines["global_median"]["MdAPE"]["point"]
    gap_pp = median_baseline_mdape - v2_cold_best_mdape
    hard_gate_threshold = 30.0
    hard_gate_pass = gap_pp >= hard_gate_threshold

    output = {
        "config": {
            "n_bootstrap": N_BOOTSTRAP,
            "rng_seed": RNG_SEED,
            "rf_params": {"n_estimators": 200, "max_depth": 10, "random_state": RNG_SEED},
            "category_mean_keys": ["medium_category", "source"],
            "method": "v2 OOF (production tuned) vs 3 baselines (global median / per-category mean / RandomForest)",
        },
        "cold_groupkfold": {
            "n": int(len(y_full)),
            "baselines": cold_baselines,
            "v2_models": cold_v2,
        },
        "warm_kfold": {
            "n": int(len(y_warm)),
            "baselines": warm_baselines,
            "v2_models": warm_v2,
        },
        "hard_gate_evaluation": {
            "rule": "v2 cold MdAPE ≤ Global median baseline MdAPE − 30%p",
            "v2_cold_best_mdape": v2_cold_best_mdape,
            "v2_cold_best_model": "ensemble (raw OOF)",
            "global_median_mdape": median_baseline_mdape,
            "gap_pp": gap_pp,
            "threshold_pp": hard_gate_threshold,
            "pass": bool(hard_gate_pass),
        },
    }

    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Console summary
    print("\n" + "=" * 100)
    print("v3 Group 1.4 Baseline Comparison Summary (1차 시장 모델, GroupKFold + KFold OOF)")
    print("=" * 100)
    print(f"\n{'Slice':<22} {'Model':<35} {'n':>6} {'MdAPE':>8} {'95% CI':>22} {'W30':>8}")
    print("-" * 105)
    print("Cold GroupKFold:")
    for k, m in cold_baselines.items():
        print(f"  {'baseline':<20} {k:<35} {m['n']:>6} {m['MdAPE']['point']:>7.2f}% "
              f"[{m['MdAPE']['ci_low']:>5.2f}, {m['MdAPE']['ci_high']:>5.2f}] {m['W30']['point']:>7.2f}%")
    for k, m in cold_v2.items():
        print(f"  {'v2 model':<20} {k:<35} {m['n']:>6} {m['MdAPE']['point']:>7.2f}% "
              f"[{m['MdAPE']['ci_low']:>5.2f}, {m['MdAPE']['ci_high']:>5.2f}] {m['W30']['point']:>7.2f}%")
    print("\nWarm KFold:")
    for k, m in warm_baselines.items():
        print(f"  {'baseline':<20} {k:<35} {m['n']:>6} {m['MdAPE']['point']:>7.2f}% "
              f"[{m['MdAPE']['ci_low']:>5.2f}, {m['MdAPE']['ci_high']:>5.2f}] {m['W30']['point']:>7.2f}%")
    for k, m in warm_v2.items():
        print(f"  {'v2 model':<20} {k:<35} {m['n']:>6} {m['MdAPE']['point']:>7.2f}% "
              f"[{m['MdAPE']['ci_low']:>5.2f}, {m['MdAPE']['ci_high']:>5.2f}] {m['W30']['point']:>7.2f}%")

    print("\n" + "=" * 100)
    print(f"HARD GATE: v2 cold ≤ median baseline − 30%p")
    print(f"  v2 cold best (ensemble raw): {v2_cold_best_mdape:.2f}%")
    print(f"  Global median baseline:      {median_baseline_mdape:.2f}%")
    print(f"  gap:                         {gap_pp:.2f}%p (threshold: {hard_gate_threshold:.1f}%p)")
    print(f"  PASS:                        {'YES ✓' if hard_gate_pass else 'NO ✗'}")
    print("=" * 100)
    print(f"\n저장: {OUT_PATH}")


if __name__ == "__main__":
    main()
