"""Source-specific median-ratio calibration (Codex 권장 P2).

배경:
- v3-filtered-tuned 모델의 source별 mean(predicted/actual) 비율:
  · Cold CatBoost: Artsy 1.19, Saatchi 1.31 (12%p 격차)
  · Warm XGBoost: Artsy 1.06, Saatchi 1.05 (격차 작음)
- 모델이 source 컬럼을 입력으로 쓰지만 여전히 source별 잔여 bias 존재
- split-model보다 안전: 모델 분리 없이 후처리 보정

방법:
- 5-fold GroupKFold (cold) + KFold warm slice (warm) 각각 OOF predictions 수집
- 각 (route × source) 별로 median(actual / predicted) 계산
- predicted *= median_ratio → 가격 보정

산출물:
- model_test_results/integrated_v3_filtered_tuned_source_calibration.json

Usage:
    PYTHONPATH=src python3 scripts/calibrate_source_bias.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from catboost import CatBoostRegressor
from sklearn.model_selection import GroupKFold, KFold

sys.path.insert(0, str(Path(__file__).resolve().parent))
from train_primary_market_v3_filtered import (
    CB_FEATURES, CAT_FEATURES, _cb_pool, _label_encode_xgb,
    _warm_mask, load_data, prepare_features,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "model_test_results"


def _load_tuned_params() -> tuple[dict, dict]:
    params_path = OUT_DIR / "integrated_v3_filtered_tuned_best_params.json"
    if not params_path.exists():
        raise FileNotFoundError(
            f"tuned params 없음 ({params_path}) — calibration은 production tuned 모델 평가 필요"
        )
    with params_path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data["catboost"], data["xgboost"]


def _cold_oof_predictions(
    X: pd.DataFrame, y: np.ndarray, groups: np.ndarray, cb_params: dict,
    n_splits: int = 5,
) -> np.ndarray:
    """GroupKFold (cold start) CV → CatBoost OOF predictions (ln_price)."""
    gkf = GroupKFold(n_splits=n_splits)
    cb_preds = np.zeros(len(y))
    for fold, (tr, te) in enumerate(gkf.split(X, y, groups), 1):
        logger.info("[Cold fold %d/%d] train=%d test=%d", fold, n_splits, len(tr), len(te))
        cb = CatBoostRegressor(
            **cb_params, loss_function="RMSE", verbose=0, random_seed=42,
            allow_writing_files=False,
        )
        cb.fit(_cb_pool(X.iloc[tr], y[tr]), eval_set=_cb_pool(X.iloc[te], y[te]),
               early_stopping_rounds=50)
        cb_preds[te] = cb.predict(_cb_pool(X.iloc[te]))
    return cb_preds


def _warm_oof_predictions(
    X: pd.DataFrame, y: np.ndarray, groups: np.ndarray, xgb_params: dict,
    n_splits: int = 5,
) -> tuple[np.ndarray, np.ndarray]:
    """warm slice 만으로 KFold CV → XGBoost OOF predictions.

    Returns (oof_preds, warm_indices_in_original_X).
    """
    wmask = _warm_mask(groups)
    X_warm = X.iloc[wmask].reset_index(drop=True)
    y_warm = y[wmask]
    n_warm = len(y_warm)

    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    xgb_preds = np.zeros(n_warm)
    for fold, (tr, te) in enumerate(kf.split(X_warm), 1):
        logger.info("[Warm fold %d/%d] train=%d test=%d", fold, n_splits, len(tr), len(te))
        Xtr_e, Xte_e, _ = _label_encode_xgb(X_warm.iloc[tr], X_warm.iloc[te])
        dtrain = xgb.DMatrix(Xtr_e, label=y_warm[tr])
        dtest = xgb.DMatrix(Xte_e, label=y_warm[te])
        xgb_p = {k: v for k, v in xgb_params.items() if k != "num_boost_round"}
        m = xgb.train(
            params={**xgb_p, "objective": "reg:squarederror", "verbosity": 0, "seed": 42},
            dtrain=dtrain, num_boost_round=xgb_params.get("num_boost_round", 1000),
            evals=[(dtest, "test")], early_stopping_rounds=50, verbose_eval=False,
        )
        xgb_preds[te] = m.predict(dtest)

    warm_indices = np.where(wmask)[0]
    return xgb_preds, warm_indices


def _compute_median_ratio(y_true_price: np.ndarray, y_pred_price: np.ndarray) -> float:
    """median(actual / predicted) — 보정 시 multiplier 직접 사용."""
    valid = (y_pred_price > 0) & (y_true_price > 0)
    if valid.sum() == 0:
        return 1.0
    return float(np.median(y_true_price[valid] / y_pred_price[valid]))


def _mdape(y_true_price: np.ndarray, y_pred_price: np.ndarray) -> float:
    valid = y_true_price > 0
    return float(np.median(np.abs(y_true_price[valid] - y_pred_price[valid]) / y_true_price[valid]) * 100)


def calibrate() -> dict:
    """Source-specific median-ratio calibration."""
    logger.info("=" * 70)
    logger.info("Source-specific median-ratio calibration")
    logger.info("=" * 70)

    cb_params, xgb_params = _load_tuned_params()
    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].reset_index(drop=True)
    X, y, groups = prepare_features(df)
    source = df["source"].astype(str).to_numpy()
    logger.info("Data: %d rows, %d artists", len(df), len(set(groups)))

    # Cold OOF (GroupKFold, full data)
    logger.info("--- Cold CatBoost OOF predictions ---")
    cb_preds_ln = _cold_oof_predictions(X, y, groups, cb_params)
    y_price = np.exp(y)
    cb_pred_price = np.exp(cb_preds_ln)

    # Warm OOF (KFold on warm slice)
    logger.info("--- Warm XGBoost OOF predictions (warm slice) ---")
    xgb_preds_ln, warm_indices = _warm_oof_predictions(X, y, groups, xgb_params)
    y_warm_price = np.exp(y[warm_indices])
    xgb_pred_price = np.exp(xgb_preds_ln)
    source_warm = source[warm_indices]

    # Per-source median ratio
    cold_factors: dict[str, float] = {}
    warm_factors: dict[str, float] = {}
    cold_baseline_mdape: dict[str, float] = {}
    cold_calibrated_mdape: dict[str, float] = {}
    warm_baseline_mdape: dict[str, float] = {}
    warm_calibrated_mdape: dict[str, float] = {}

    for src in sorted(set(source)):
        mask = source == src
        if mask.sum() == 0:
            continue
        # Cold
        ratio = _compute_median_ratio(y_price[mask], cb_pred_price[mask])
        cold_factors[src] = ratio
        baseline = _mdape(y_price[mask], cb_pred_price[mask])
        calibrated = _mdape(y_price[mask], cb_pred_price[mask] * ratio)
        cold_baseline_mdape[src] = baseline
        cold_calibrated_mdape[src] = calibrated
        logger.info("Cold %s: ratio=%.4f, baseline MdAPE=%.2f → calibrated=%.2f (Δ=%+.2f)",
                    src, ratio, baseline, calibrated, calibrated - baseline)

    for src in sorted(set(source_warm)):
        mask = source_warm == src
        if mask.sum() == 0:
            continue
        ratio = _compute_median_ratio(y_warm_price[mask], xgb_pred_price[mask])
        warm_factors[src] = ratio
        baseline = _mdape(y_warm_price[mask], xgb_pred_price[mask])
        calibrated = _mdape(y_warm_price[mask], xgb_pred_price[mask] * ratio)
        warm_baseline_mdape[src] = baseline
        warm_calibrated_mdape[src] = calibrated
        logger.info("Warm %s: ratio=%.4f, baseline MdAPE=%.2f → calibrated=%.2f (Δ=%+.2f)",
                    src, ratio, baseline, calibrated, calibrated - baseline)

    # Overall (calibration applied per-row via source)
    cold_overall_baseline = _mdape(y_price, cb_pred_price)
    cb_pred_calibrated = cb_pred_price * np.array([cold_factors.get(s, 1.0) for s in source])
    cold_overall_cal = _mdape(y_price, cb_pred_calibrated)
    warm_overall_baseline = _mdape(y_warm_price, xgb_pred_price)
    xgb_pred_calibrated = xgb_pred_price * np.array([warm_factors.get(s, 1.0) for s in source_warm])
    warm_overall_cal = _mdape(y_warm_price, xgb_pred_calibrated)

    logger.info("=" * 70)
    logger.info("Cold overall: baseline=%.2f → calibrated=%.2f (Δ=%+.2f)",
                cold_overall_baseline, cold_overall_cal, cold_overall_cal - cold_overall_baseline)
    logger.info("Warm overall: baseline=%.2f → calibrated=%.2f (Δ=%+.2f)",
                warm_overall_baseline, warm_overall_cal, warm_overall_cal - warm_overall_baseline)

    return {
        "cold_factors": cold_factors,
        "warm_factors": warm_factors,
        "cold_baseline_mdape_by_source": cold_baseline_mdape,
        "cold_calibrated_mdape_by_source": cold_calibrated_mdape,
        "warm_baseline_mdape_by_source": warm_baseline_mdape,
        "warm_calibrated_mdape_by_source": warm_calibrated_mdape,
        "cold_overall_baseline_mdape": cold_overall_baseline,
        "cold_overall_calibrated_mdape": cold_overall_cal,
        "warm_overall_baseline_mdape": warm_overall_baseline,
        "warm_overall_calibrated_mdape": warm_overall_cal,
        "method": "median(actual_price / predicted_price)",
        "n_total": len(y),
        "n_warm": len(y_warm_price),
        "note": (
            "predicted_price *= factors[source] for cold and warm routes. "
            "Source unknown → factor=1.0. seed=42, KFold shuffle=True."
        ),
    }


def main() -> None:
    result = calibrate()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "integrated_v3_filtered_tuned_source_calibration.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    logger.info("Saved: %s", out)


if __name__ == "__main__":
    main()
