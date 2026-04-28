"""Cell-level calibration: (source × target_market) median-ratio + cross-fit 평가.

Codex P1 review (2026-04-28):
- 이전 버전: in-sample calibration (factor 학습/평가가 같은 fold) → 효과 과대평가
- 이전 버전: source-only calibration이 RATIO_CORRECTION (target_market='online' -0.075)과
  entangle → double-correct 위험
  · Saatchi 학습 데이터는 100% online이라 source factor에 online 효과 흡수됨
  · 서빙 시 사용자가 Saatchi 작가의 gallery 가격 요청하면 잘못된 보정 적용

수정:
1. Cross-fit 5-fold: 각 held-out fold마다 다른 4개 fold에서 factor 계산 후 적용
   → 정직한 out-of-sample MdAPE 측정
2. Cell 결합: (source × target_market) 기준 factor 계산
   · is_krw=1 → target_market='gallery' / else → 'online'
   · cell 4개: artsy_gallery, artsy_online, saatchi_gallery (training X), saatchi_online
3. 적용 시 학습 시점의 RATIO_CORRECTION을 흡수 → 별도 처리

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

CALIBRATION_VERSION = "v1-cross-fit-cell"


def _load_tuned_params() -> tuple[dict, dict]:
    params_path = OUT_DIR / "integrated_v3_filtered_tuned_best_params.json"
    if not params_path.exists():
        raise FileNotFoundError(
            f"tuned params 없음 ({params_path}) — calibration은 production tuned 모델 평가 필요"
        )
    with params_path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data["catboost"], data["xgboost"]


def _cell_key(source: str, target_market: str) -> str:
    """Calibration cell key — (source, target_market) 결합."""
    return f"{source}_{target_market}"


def _compute_factor(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """median(actual / predicted) — predicted * factor → actual에 가까워짐."""
    valid = (y_pred > 0) & (y_true > 0)
    if valid.sum() == 0:
        return 1.0
    return float(np.median(y_true[valid] / y_pred[valid]))


def _mdape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    valid = y_true > 0
    if valid.sum() == 0:
        return float("nan")
    return float(np.median(np.abs(y_true[valid] - y_pred[valid]) / y_true[valid]) * 100)


def _cold_oof_with_fold_id(
    X: pd.DataFrame, y: np.ndarray, groups: np.ndarray, cb_params: dict, n_splits: int = 5,
) -> tuple[np.ndarray, np.ndarray]:
    """GroupKFold (cold start) → CatBoost OOF predictions + fold ID per row.

    Codex P1 (2026-04-28): early stopping leakage 방지 — 학습 fold의 test split(eval_set)을
    early_stopping_rounds로 쓰면 test labels가 모델 선택에 leak.
    수정: tuned 'iterations'를 그대로 사용 (early stopping 제거). production tune 시점에
    이미 한 번 검증된 iteration count.
    """
    gkf = GroupKFold(n_splits=n_splits)
    cb_preds = np.zeros(len(y))
    fold_ids = np.full(len(y), -1, dtype=int)
    for fold, (tr, te) in enumerate(gkf.split(X, y, groups)):
        logger.info("[Cold fold %d/%d] train=%d test=%d", fold + 1, n_splits, len(tr), len(te))
        cb = CatBoostRegressor(
            **cb_params, loss_function="RMSE", verbose=0, random_seed=42, allow_writing_files=False,
        )
        # No eval_set → no leakage from test fold to early stopping
        cb.fit(_cb_pool(X.iloc[tr], y[tr]))
        cb_preds[te] = cb.predict(_cb_pool(X.iloc[te]))
        fold_ids[te] = fold
    return cb_preds, fold_ids


def _warm_oof_with_fold_id(
    X: pd.DataFrame, y: np.ndarray, groups: np.ndarray, xgb_params: dict, n_splits: int = 5,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """warm slice KFold → XGBoost OOF predictions + fold ID + warm indices.

    Codex P1: early stopping leakage 방지 — eval_set 제거.
    """
    wmask = _warm_mask(groups)
    X_warm = X.iloc[wmask].reset_index(drop=True)
    y_warm = y[wmask]
    n_warm = len(y_warm)

    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    xgb_preds = np.zeros(n_warm)
    fold_ids = np.full(n_warm, -1, dtype=int)
    for fold, (tr, te) in enumerate(kf.split(X_warm)):
        logger.info("[Warm fold %d/%d] train=%d test=%d", fold + 1, n_splits, len(tr), len(te))
        Xtr_e, Xte_e, _ = _label_encode_xgb(X_warm.iloc[tr], X_warm.iloc[te])
        dtrain = xgb.DMatrix(Xtr_e, label=y_warm[tr])
        dtest = xgb.DMatrix(Xte_e, label=y_warm[te])
        xgb_p = {k: v for k, v in xgb_params.items() if k != "num_boost_round"}
        m = xgb.train(
            params={**xgb_p, "objective": "reg:squarederror", "verbosity": 0, "seed": 42},
            dtrain=dtrain, num_boost_round=xgb_params.get("num_boost_round", 1000),
        )
        xgb_preds[te] = m.predict(dtest)
        fold_ids[te] = fold

    warm_indices = np.where(wmask)[0]
    return xgb_preds, fold_ids, warm_indices


def _cross_fit_eval(
    y_price: np.ndarray, pred_price: np.ndarray, cells: np.ndarray, fold_ids: np.ndarray,
    n_splits: int = 5,
) -> tuple[dict[str, float], float, float, np.ndarray]:
    """Cross-fit calibrator 평가.

    각 fold k 마다:
    1. OTHER fold (1..K) 의 predictions로 cell별 factor 학습
    2. 그 factor를 fold k에 적용
    3. 모든 fold 통합해서 calibrated MdAPE 계산

    Returns: (final_factors_per_cell, baseline_mdape, calibrated_mdape, calibrated_pred)
    final_factors는 전체 데이터로 fit한 production용 factor.
    calibrated_pred는 cross-fit으로 계산된 fold-별 factor 적용 결과 (per-cell breakdown용).
    """
    baseline_mdape = _mdape(y_price, pred_price)

    calibrated_pred = pred_price.copy()
    for k in range(n_splits):
        held_out = fold_ids == k
        train_mask = (fold_ids != k) & (fold_ids >= 0)
        if held_out.sum() == 0 or train_mask.sum() == 0:
            continue
        cell_factors_for_this_split: dict[str, float] = {}
        for cell in set(cells[train_mask]):
            cell_train = train_mask & (cells == cell)
            if cell_train.sum() == 0:
                cell_factors_for_this_split[cell] = 1.0
                continue
            cell_factors_for_this_split[cell] = _compute_factor(
                y_price[cell_train], pred_price[cell_train]
            )
        for i in np.where(held_out)[0]:
            cell = cells[i]
            factor = cell_factors_for_this_split.get(cell, 1.0)
            calibrated_pred[i] = pred_price[i] * factor

    calibrated_mdape = _mdape(y_price, calibrated_pred)

    final_factors: dict[str, float] = {}
    for cell in sorted(set(cells)):
        cell_mask = cells == cell
        if cell_mask.sum() == 0:
            continue
        final_factors[cell] = _compute_factor(y_price[cell_mask], pred_price[cell_mask])

    return final_factors, baseline_mdape, calibrated_mdape, calibrated_pred


def calibrate() -> dict:
    """Cross-fit cell-level calibration."""
    logger.info("=" * 70)
    logger.info("Cell-level (source × target_market) median-ratio calibration + cross-fit")
    logger.info("=" * 70)

    cb_params, xgb_params = _load_tuned_params()
    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].reset_index(drop=True)
    X, y, groups = prepare_features(df)
    source = df["source"].astype(str).to_numpy()
    # target_market: is_krw=1 → 'gallery', else 'online' (학습 시 정의 일관)
    target_market = np.where(df["is_krw"].fillna(0).astype(int) == 1, "gallery", "online")
    cells = np.array([_cell_key(s, tm) for s, tm in zip(source, target_market)])
    logger.info("Data: %d rows, %d artists, cells=%s",
                len(df), len(set(groups)), dict(pd.Series(cells).value_counts()))

    # Cold OOF
    logger.info("--- Cold CatBoost OOF predictions (GroupKFold 5) ---")
    cb_preds_ln, cold_fold_ids = _cold_oof_with_fold_id(X, y, groups, cb_params)
    y_price = np.exp(y)
    cb_pred_price = np.exp(cb_preds_ln)

    # Warm OOF
    logger.info("--- Warm XGBoost OOF predictions (KFold 5, warm slice) ---")
    xgb_preds_ln, warm_fold_ids, warm_indices = _warm_oof_with_fold_id(X, y, groups, xgb_params)
    y_warm_price = np.exp(y[warm_indices])
    xgb_pred_price = np.exp(xgb_preds_ln)
    cells_warm = cells[warm_indices]

    # Cross-fit evaluation
    logger.info("--- Cold cross-fit evaluation ---")
    cold_factors, cold_baseline, cold_calibrated, cold_calibrated_pred = _cross_fit_eval(
        y_price, cb_pred_price, cells, cold_fold_ids
    )
    logger.info("Cold baseline MdAPE=%.2f → calibrated (cross-fit)=%.2f (Δ=%+.2f)",
                cold_baseline, cold_calibrated, cold_calibrated - cold_baseline)
    logger.info("Cold final factors: %s", cold_factors)

    logger.info("--- Warm cross-fit evaluation ---")
    warm_factors, warm_baseline, warm_calibrated, warm_calibrated_pred = _cross_fit_eval(
        y_warm_price, xgb_pred_price, cells_warm, warm_fold_ids
    )
    logger.info("Warm baseline MdAPE=%.2f → calibrated (cross-fit)=%.2f (Δ=%+.2f)",
                warm_baseline, warm_calibrated, warm_calibrated - warm_baseline)
    logger.info("Warm final factors: %s", warm_factors)

    # Per-cell breakdown — cross-fit predictions 사용 (Codex P2: post-hoc 적용 X)
    # baseline은 raw OOF pred, calibrated는 cross-fit factor 적용 결과 (held-out factor)
    # Codex 4차 P2: per-cell guard — calibration이 MdAPE 악화시키는 cell은 factor=1.0
    cold_breakdown = {}
    cold_applied_factors: dict[str, float] = {}
    for cell in sorted(set(cells)):
        mask = cells == cell
        if mask.sum() == 0:
            continue
        b = _mdape(y_price[mask], cb_pred_price[mask])
        c = _mdape(y_price[mask], cold_calibrated_pred[mask])
        proposed_factor = cold_factors.get(cell, 1.0)
        applied_factor = proposed_factor if c <= b else 1.0
        cold_breakdown[cell] = {
            "n": int(mask.sum()),
            "proposed_factor_full_data": proposed_factor,
            "applied_factor": applied_factor,  # cross-fit 결과 보고 결정
            "baseline_mdape": b,
            "calibrated_mdape_cross_fit": c,
            "skipped_due_to_regression": applied_factor == 1.0 and proposed_factor != 1.0,
        }
        cold_applied_factors[cell] = applied_factor

    warm_breakdown = {}
    warm_applied_factors: dict[str, float] = {}
    for cell in sorted(set(cells_warm)):
        mask = cells_warm == cell
        if mask.sum() == 0:
            continue
        b = _mdape(y_warm_price[mask], xgb_pred_price[mask])
        c = _mdape(y_warm_price[mask], warm_calibrated_pred[mask])
        proposed_factor = warm_factors.get(cell, 1.0)
        applied_factor = proposed_factor if c <= b else 1.0
        warm_breakdown[cell] = {
            "n": int(mask.sum()),
            "proposed_factor_full_data": proposed_factor,
            "applied_factor": applied_factor,
            "baseline_mdape": b,
            "calibrated_mdape_cross_fit": c,
            "skipped_due_to_regression": applied_factor == 1.0 and proposed_factor != 1.0,
        }
        warm_applied_factors[cell] = applied_factor

    # Per-cell guard 적용한 final overall MdAPE (서빙과 동일 동작)
    cold_pred_guarded = cb_pred_price * np.array(
        [cold_applied_factors.get(c, 1.0) for c in cells]
    )
    cold_calibrated_guarded_mdape = _mdape(y_price, cold_pred_guarded)
    warm_pred_guarded = xgb_pred_price * np.array(
        [warm_applied_factors.get(c, 1.0) for c in cells_warm]
    )
    warm_calibrated_guarded_mdape = _mdape(y_warm_price, warm_pred_guarded)
    logger.info("Cold guarded overall MdAPE=%.2f (vs cross-fit unguarded=%.2f)",
                cold_calibrated_guarded_mdape, cold_calibrated)
    logger.info("Warm guarded overall MdAPE=%.2f (vs cross-fit unguarded=%.2f)",
                warm_calibrated_guarded_mdape, warm_calibrated)

    # 서버에 보내는 factors는 per-cell guard 적용된 applied_factors (cross-fit 회귀 cell 제외)
    return {
        "version": CALIBRATION_VERSION,
        "model_target": "integrated_v3_filtered_tuned",
        "method": "median(actual_price / predicted_price), cell = source × target_market, "
                  "per-cell guard (cross-fit 악화 cell은 factor=1.0 적용)",
        "cells_definition": "is_krw==1 → target_market='gallery', else 'online'",
        "cold_factors": cold_applied_factors,
        "warm_factors": warm_applied_factors,
        "cold_factors_proposed_full_data": cold_factors,
        "warm_factors_proposed_full_data": warm_factors,
        "cold_overall": {
            "baseline_mdape": cold_baseline,
            "calibrated_mdape_cross_fit_unguarded": cold_calibrated,
            "calibrated_mdape_cross_fit_guarded": cold_calibrated_guarded_mdape,
            "delta_guarded": cold_calibrated_guarded_mdape - cold_baseline,
        },
        "warm_overall": {
            "baseline_mdape": warm_baseline,
            "calibrated_mdape_cross_fit_unguarded": warm_calibrated,
            "calibrated_mdape_cross_fit_guarded": warm_calibrated_guarded_mdape,
            "delta_guarded": warm_calibrated_guarded_mdape - warm_baseline,
        },
        "cold_breakdown": cold_breakdown,
        "warm_breakdown": warm_breakdown,
        "n_total": len(y),
        "n_warm": len(y_warm_price),
        "note": (
            "Cross-fit 5-fold: factor를 train fold에서만 fit, held-out fold에 적용 → 정직한 out-of-sample. "
            "Final factors는 전체 데이터 fit (production용). "
            "Server는 features['source'] + target_market 기반으로 cell key 결정."
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
