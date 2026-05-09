"""Per-source calibration 재산출 (Phase 2 / decision-binding).

PR1 산출 시 per-source `source_calibration.json` = no-op (모든 cell=1.0).
본 cycle: per-source artifact 영역 의 의무 영역 의 의무 cross-fit 5-fold OOF →
real factors + per-cell guard.

Usage:
    python3 scripts/calibrate_source_bias_per_source.py --source artsy
    python3 scripts/calibrate_source_bias_per_source.py --source saatchi

Output:
    model_test_results/source_conditional_v1_<src>_source_calibration.json
        version="v1-source-conditional-fitted" / model_target=source_conditional_v1_<src>
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from calibrate_source_bias import (
    _cell_key,
    _cold_oof_with_fold_id,
    _cross_fit_eval,
    _mdape,
    _warm_oof_with_fold_id,
)
from train_primary_market_v3_filtered import load_data, prepare_features

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

OUT_DIR = REPO / "model_test_results"
PREFIX = "source_conditional_v1"
CALIBRATION_VERSION = "v1-source-conditional-fitted"

VALID_SOURCES = ("artsy", "saatchi")


def _load_tuned_params() -> tuple[dict, dict]:
    """Reuse 운영 best_params (per-source artifact 영역 의 의무 영역 의 의무 영역 의 의무 동일).

    PR1 retrain 영역 의 의무 영역 의 의무 = best_params 동일 사용 (per-source HP X / Phase 3).
    """
    params_path = OUT_DIR / "integrated_v3_filtered_tuned_best_params.json"
    if not params_path.exists():
        raise FileNotFoundError(f"tuned params 없음 ({params_path})")
    with params_path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data["catboost"], data["xgboost"]


def calibrate_per_source(source_name: str) -> dict:
    """Per-source cross-fit cell calibration."""
    if source_name not in VALID_SOURCES:
        raise ValueError(f"Invalid source: {source_name} / valid: {VALID_SOURCES}")

    logger.info("=" * 70)
    logger.info("Per-source calibration: %s", source_name)
    logger.info("=" * 70)

    cb_params, xgb_params = _load_tuned_params()

    # Per-source filter (PR1 artifact = source_conditional_v1_<src>_*)
    df = load_data()
    df = df[df["is_excluded_for_training"] == 0]
    df = df[df["source"] == source_name].reset_index(drop=True)
    logger.info("Filtered (source=%s): %d rows / %d artists",
                source_name, len(df), df["artist_slug"].nunique())

    X, y, groups = prepare_features(df)
    src = df["source"].astype(str).to_numpy()
    target_market = np.where(df["is_krw"].fillna(0).astype(int) == 1, "gallery", "online")
    cells = np.array([_cell_key(s, tm) for s, tm in zip(src, target_market, strict=False)])
    cell_dist = pd.Series(cells).value_counts().to_dict()
    logger.info("Cells: %s", cell_dist)

    # Cold OOF (CatBoost / GroupKFold-5)
    logger.info("--- Cold CatBoost OOF (GroupKFold-5) ---")
    cb_preds_ln, cold_fold_ids = _cold_oof_with_fold_id(X, y, groups, cb_params)
    y_price = np.exp(y)
    cb_pred_price = np.exp(cb_preds_ln)

    # Warm OOF (XGBoost / KFold-5 / warm slice)
    logger.info("--- Warm XGBoost OOF (KFold-5 / warm slice) ---")
    xgb_preds_ln, warm_fold_ids, warm_indices = _warm_oof_with_fold_id(X, y, groups, xgb_params)
    y_warm_price = np.exp(y[warm_indices])
    xgb_pred_price = np.exp(xgb_preds_ln)
    cells_warm = cells[warm_indices]

    # Cold cross-fit
    logger.info("--- Cold cross-fit evaluation ---")
    cold_factors, cold_baseline, cold_calibrated, cold_cal_pred = _cross_fit_eval(
        y_price, cb_pred_price, cells, cold_fold_ids
    )
    logger.info("Cold baseline=%.2f → calibrated=%.2f (Δ=%+.2f)",
                cold_baseline, cold_calibrated, cold_calibrated - cold_baseline)
    logger.info("Cold factors: %s", cold_factors)

    # Warm cross-fit
    logger.info("--- Warm cross-fit evaluation ---")
    warm_factors, warm_baseline, warm_calibrated, warm_cal_pred = _cross_fit_eval(
        y_warm_price, xgb_pred_price, cells_warm, warm_fold_ids
    )
    logger.info("Warm baseline=%.2f → calibrated=%.2f (Δ=%+.2f)",
                warm_baseline, warm_calibrated, warm_calibrated - warm_baseline)
    logger.info("Warm factors: %s", warm_factors)

    # Per-cell guard (cold)
    cold_breakdown = {}
    cold_applied: dict[str, float] = {}
    for cell in sorted(set(cells)):
        mask = cells == cell
        if mask.sum() == 0:
            continue
        b = _mdape(y_price[mask], cb_pred_price[mask])
        c = _mdape(y_price[mask], cold_cal_pred[mask])
        proposed = cold_factors.get(cell, 1.0)
        applied = proposed if c <= b else 1.0
        cold_breakdown[cell] = {
            "n": int(mask.sum()),
            "baseline_mdape": round(b, 2),
            "calibrated_mdape_cross_fit_unguarded": round(c, 2),
            "proposed_factor_full_data": proposed,
            "applied_factor": applied,
            "delta_unguarded": round(c - b, 2),
            "skipped_due_to_regression": applied == 1.0 and proposed != 1.0,
        }
        cold_applied[cell] = applied

    # Per-cell guard (warm)
    warm_breakdown = {}
    warm_applied: dict[str, float] = {}
    for cell in sorted(set(cells_warm)):
        mask = cells_warm == cell
        if mask.sum() == 0:
            continue
        b = _mdape(y_warm_price[mask], xgb_pred_price[mask])
        c = _mdape(y_warm_price[mask], warm_cal_pred[mask])
        proposed = warm_factors.get(cell, 1.0)
        applied = proposed if c <= b else 1.0
        warm_breakdown[cell] = {
            "n": int(mask.sum()),
            "baseline_mdape": round(b, 2),
            "calibrated_mdape_cross_fit_unguarded": round(c, 2),
            "proposed_factor_full_data": proposed,
            "applied_factor": applied,
            "delta_unguarded": round(c - b, 2),
            "skipped_due_to_regression": applied == 1.0 and proposed != 1.0,
        }
        warm_applied[cell] = applied

    # Guarded overall MdAPE
    cold_pred_guarded = cb_pred_price.copy()
    for cell, applied in cold_applied.items():
        if applied != 1.0:
            mask = cells == cell
            cold_pred_guarded[mask] = cold_cal_pred[mask]
    cold_guarded_mdape = _mdape(y_price, cold_pred_guarded)

    warm_pred_guarded = xgb_pred_price.copy()
    for cell, applied in warm_applied.items():
        if applied != 1.0:
            mask = cells_warm == cell
            warm_pred_guarded[mask] = warm_cal_pred[mask]
    warm_guarded_mdape = _mdape(y_warm_price, warm_pred_guarded)

    logger.info("Cold guarded MdAPE=%.2f / Warm guarded MdAPE=%.2f",
                cold_guarded_mdape, warm_guarded_mdape)
    logger.info("Cold applied: %s / Warm applied: %s", cold_applied, warm_applied)

    model_target = f"{PREFIX}_{source_name}"
    output = {
        "version": CALIBRATION_VERSION,
        "model_target": model_target,
        "method": (
            "per-source cross-fit 5-fold cell-level (source × target_market) median-ratio "
            "calibration + per-cell guard (cross-fit 악화 cell은 factor=1.0)"
        ),
        "source": source_name,
        "data": f"{len(df)} rows / {df['artist_slug'].nunique()} artists / source={source_name}",
        "cells_definition": "is_krw==1 → target_market='gallery', else 'online'",
        "cell_distribution": cell_dist,
        "cold_factors": cold_applied,
        "warm_factors": warm_applied,
        "cold_factors_proposed_full_data": cold_factors,
        "warm_factors_proposed_full_data": warm_factors,
        "cold_overall": {
            "baseline_mdape": round(cold_baseline, 2),
            "calibrated_mdape_cross_fit_unguarded": round(cold_calibrated, 2),
            "calibrated_mdape_cross_fit_guarded": round(cold_guarded_mdape, 2),
            "delta_guarded": round(cold_guarded_mdape - cold_baseline, 2),
        },
        "warm_overall": {
            "baseline_mdape": round(warm_baseline, 2),
            "calibrated_mdape_cross_fit_unguarded": round(warm_calibrated, 2),
            "calibrated_mdape_cross_fit_guarded": round(warm_guarded_mdape, 2),
            "delta_guarded": round(warm_guarded_mdape - warm_baseline, 2),
        },
        "cold_per_cell": cold_breakdown,
        "warm_per_cell": warm_breakdown,
        "calibrated_at": datetime.now(UTC).isoformat(),
    }

    out_path = OUT_DIR / f"{model_target}_source_calibration.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    logger.info("[OK] Saved: %s", out_path.name)

    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Per-source calibration (artsy / saatchi)")
    parser.add_argument("--source", required=True, choices=VALID_SOURCES)
    args = parser.parse_args()

    output = calibrate_per_source(args.source)
    print(f"\n=== Summary: {args.source} ===")
    print(f"  cold guarded MdAPE: {output['cold_overall']['calibrated_mdape_cross_fit_guarded']:.2f}")
    print(f"  warm guarded MdAPE: {output['warm_overall']['calibrated_mdape_cross_fit_guarded']:.2f}")
    print(f"  cold factors: {output['cold_factors']}")
    print(f"  warm factors: {output['warm_factors']}")


if __name__ == "__main__":
    main()
