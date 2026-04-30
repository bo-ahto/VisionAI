"""v3 Group 1.1: warm/cold MdAPE + W30 Bootstrap 95% CI.

기존 OOF 예측(`oof_predictions.npz`)에 10,000회 resample bootstrap을 적용해
production 메트릭의 통계적 신뢰 구간을 산출한다. v3.0 acceptance gate (§6) 의
첫 작업.

두 가지 cold path 메트릭을 분리하여 산출:
- raw cold: GroupKFold OOF 예측 그대로 (calibration 미적용)
- calibrated cold: cell factor 적용 후 (production path, v2 보고서 38.3% 정합)
  cell factor는 source × target_market 으로 결정.
  target_market: is_krw==1 → 'gallery', else → 'online'.
  cold_factors (model_test_results/integrated_v3_filtered_tuned_source_calibration.json):
    artsy_gallery=1.0, artsy_online=0.9426, saatchi_online=0.9569

산출물:
    model_test_results/v3_diagnostics/bootstrap_ci.json

Usage:
    python3 scripts/v3_bootstrap_ci.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

OOF_PATH = ROOT / "model_test_results" / "v3_diagnostics" / "oof_predictions.npz"
CAL_PATH = ROOT / "model_test_results" / "integrated_v3_filtered_tuned_source_calibration.json"
OUT_PATH = ROOT / "model_test_results" / "v3_diagnostics" / "bootstrap_ci.json"
N_BOOTSTRAP = 10_000
RNG_SEED = 42


def _load_is_krw_aligned() -> np.ndarray:
    """v3_extract_oof.py와 동일한 row order의 is_krw 배열 산출 (calibration 적용용)."""
    from train_primary_market_v3_filtered import load_data
    df = load_data()
    df_train = df[df.get("is_excluded_for_training", 0) != 1].reset_index(drop=True)
    return df_train["is_krw"].astype(int).to_numpy()


def _load_cold_factors() -> dict[str, float]:
    with CAL_PATH.open(encoding="utf-8") as f:
        return json.load(f)["cold_factors"]


def _apply_cell_calibration(
    cb_pred: np.ndarray, source: np.ndarray, is_krw: np.ndarray, cold_factors: dict[str, float],
) -> np.ndarray:
    """primary_predictor.py 와 동일하게 cell factor 적용 — _eval_helpers wrapper."""
    from visionai.price_engine._eval_helpers import (
        apply_cell_calibration as _ac, cell_keys, derive_target_market,
    )
    target_market = derive_target_market(is_krw)
    cells = cell_keys(source, target_market)
    return _ac(cb_pred, cells, cold_factors)


def mdape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    valid = y_true > 0
    return float(np.median(np.abs(y_true[valid] - y_pred[valid]) / y_true[valid]) * 100)


def w30(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    valid = y_true > 0
    return float(np.mean(np.abs(y_true[valid] - y_pred[valid]) / y_true[valid] <= 0.30) * 100)


def w50(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    valid = y_true > 0
    return float(np.mean(np.abs(y_true[valid] - y_pred[valid]) / y_true[valid] <= 0.50) * 100)


def bootstrap_metric(
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
        "mean": float(np.mean(values)),
        "ci_low": float(np.percentile(values, 100 * alpha / 2)),
        "ci_high": float(np.percentile(values, 100 * (1 - alpha / 2))),
        "ci_width": float(np.percentile(values, 100 * (1 - alpha / 2)) -
                          np.percentile(values, 100 * alpha / 2)),
        "std": float(np.std(values, ddof=1)),
    }


def metrics_with_ci(y_true: np.ndarray, y_pred: np.ndarray, n: int) -> dict:
    return {
        "n": int(n),
        "MdAPE": bootstrap_metric(y_true, y_pred, mdape),
        "W30": bootstrap_metric(y_true, y_pred, w30),
        "W50": bootstrap_metric(y_true, y_pred, w50),
    }


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    oof = np.load(OOF_PATH, allow_pickle=True)
    y_actual_ln = oof["y_actual_ln"]
    cb_gkf_ln = oof["cb_preds_gkf_ln"]
    xgb_gkf_ln = oof["xgb_preds_gkf_ln"]
    source_full = oof["source"]
    y_warm_ln = oof["y_warm_actual_ln"]
    cb_kf_ln = oof["cb_preds_kf_ln"]
    xgb_kf_ln = oof["xgb_preds_kf_ln"]
    source_warm = oof["source_warm"]

    # ln → 가격 공간 변환
    y_full = np.exp(y_actual_ln)
    cb_gkf = np.exp(cb_gkf_ln)
    xgb_gkf = np.exp(xgb_gkf_ln)
    ens_gkf = np.exp((cb_gkf_ln + xgb_gkf_ln) / 2)
    baseline_gkf = np.full_like(y_full, np.median(y_full))

    y_warm = np.exp(y_warm_ln)
    cb_kf = np.exp(cb_kf_ln)
    xgb_kf = np.exp(xgb_kf_ln)
    ens_kf = np.exp((cb_kf_ln + xgb_kf_ln) / 2)

    logger.info("Cold GroupKFold (n=%d) Bootstrap CI 산출 (raw)", len(y_full))
    cold = {
        "n": int(len(y_full)),
        "baseline": metrics_with_ci(y_full, baseline_gkf, len(y_full)),
        "catboost_v3_filtered_tuned": metrics_with_ci(y_full, cb_gkf, len(y_full)),
        "xgboost_v3_filtered_tuned": metrics_with_ci(y_full, xgb_gkf, len(y_full)),
        "ensemble": metrics_with_ci(y_full, ens_gkf, len(y_full)),
    }
    for src in sorted(set(source_full)):
        mask = source_full == src
        if mask.sum() == 0:
            continue
        cold[src] = {
            "n": int(mask.sum()),
            "catboost_v3_filtered_tuned": metrics_with_ci(y_full[mask], cb_gkf[mask], int(mask.sum())),
            "xgboost_v3_filtered_tuned": metrics_with_ci(y_full[mask], xgb_gkf[mask], int(mask.sum())),
            "ensemble": metrics_with_ci(y_full[mask], ens_gkf[mask], int(mask.sum())),
        }

    # Calibrated cold path (production path = CatBoost + cell calibration)
    logger.info("Cold GroupKFold (n=%d) calibrated CatBoost (production path) Bootstrap CI 산출", len(y_full))
    is_krw = _load_is_krw_aligned()
    if len(is_krw) != len(y_full):
        raise RuntimeError(f"is_krw length mismatch: {len(is_krw)} vs {len(y_full)}")
    cold_factors = _load_cold_factors()
    cb_gkf_calibrated = _apply_cell_calibration(cb_gkf, source_full, is_krw, cold_factors)
    cold_calibrated = {
        "n": int(len(y_full)),
        "method": "CatBoost OOF × cell factor (production cold path, v2 보고서 38.3% 정합)",
        "cold_factors_applied": cold_factors,
        "catboost_v3_filtered_tuned_calibrated": metrics_with_ci(
            y_full, cb_gkf_calibrated, len(y_full),
        ),
    }
    for src in sorted(set(source_full)):
        mask = source_full == src
        if mask.sum() == 0:
            continue
        cold_calibrated[src] = {
            "n": int(mask.sum()),
            "catboost_v3_filtered_tuned_calibrated": metrics_with_ci(
                y_full[mask], cb_gkf_calibrated[mask], int(mask.sum()),
            ),
        }

    logger.info("Warm KFold (n=%d) Bootstrap CI 산출", len(y_warm))
    warm = {
        "n": int(len(y_warm)),
        "catboost_v3_filtered_tuned": metrics_with_ci(y_warm, cb_kf, len(y_warm)),
        "xgboost_v3_filtered_tuned": metrics_with_ci(y_warm, xgb_kf, len(y_warm)),
        "ensemble": metrics_with_ci(y_warm, ens_kf, len(y_warm)),
    }
    for src in sorted(set(source_warm)):
        mask = source_warm == src
        if mask.sum() == 0:
            continue
        warm[src] = {
            "n": int(mask.sum()),
            "catboost_v3_filtered_tuned": metrics_with_ci(y_warm[mask], cb_kf[mask], int(mask.sum())),
            "xgboost_v3_filtered_tuned": metrics_with_ci(y_warm[mask], xgb_kf[mask], int(mask.sum())),
            "ensemble": metrics_with_ci(y_warm[mask], ens_kf[mask], int(mask.sum())),
        }

    output = {
        "config": {
            "n_bootstrap": N_BOOTSTRAP,
            "alpha": 0.05,
            "rng_seed": RNG_SEED,
            "method": "non-parametric percentile bootstrap on (y_true, y_pred) pairs (row-level, not artist-cluster)",
            "oof_source": "tune_primary_market_v3_filtered.py:_final_cv_groupkfold_5 / _final_cv_kfold_5 동일 로직 재현 (scripts/v3_extract_oof.py)",
            "cold_path_note": "두 메트릭 분리 보고: (1) cold_groupkfold = raw OOF (calibration 미적용). (2) cold_groupkfold_calibrated = cell factor 적용 후 (production path, v2 보고서 §8.2 38.3% 정합).",
        },
        "cold_groupkfold": cold,
        "cold_groupkfold_calibrated": cold_calibrated,
        "warm_kfold": warm,
    }

    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Console summary
    print(f"\n{'='*100}")
    print(f"v3 Group 1.1 Bootstrap CI Summary (n_bootstrap={N_BOOTSTRAP}, seed={RNG_SEED})")
    print(f"{'='*100}\n")
    print(f"{'Slice':<22} {'Model':<22} {'n':>6} {'MdAPE point':>12} {'MdAPE 95% CI':>22} {'W30 point':>10}")
    print("-" * 100)
    print("Cold GroupKFold (raw OOF):")
    for k in ["catboost_v3_filtered_tuned", "xgboost_v3_filtered_tuned", "ensemble"]:
        m = cold[k]
        print(f"  {'':<20} {k.replace('_v3_filtered_tuned', ''):<22} {m['n']:>6} "
              f"{m['MdAPE']['point']:>11.2f}% [{m['MdAPE']['ci_low']:>5.2f}, {m['MdAPE']['ci_high']:>5.2f}] "
              f"{m['W30']['point']:>9.2f}%")
    print("Cold GroupKFold (calibrated, production path):")
    m = cold_calibrated["catboost_v3_filtered_tuned_calibrated"]
    print(f"  {'':<20} {'catboost+cell_cal':<22} {m['n']:>6} "
          f"{m['MdAPE']['point']:>11.2f}% [{m['MdAPE']['ci_low']:>5.2f}, {m['MdAPE']['ci_high']:>5.2f}] "
          f"{m['W30']['point']:>9.2f}%")
    for src in ["artsy", "saatchi"]:
        if src in cold_calibrated:
            m = cold_calibrated[src]["catboost_v3_filtered_tuned_calibrated"]
            print(f"  {src:<20} {'catboost+cell_cal':<22} {m['n']:>6} "
                  f"{m['MdAPE']['point']:>11.2f}% [{m['MdAPE']['ci_low']:>5.2f}, {m['MdAPE']['ci_high']:>5.2f}] "
                  f"{m['W30']['point']:>9.2f}%")
    print("Cold by source (raw):")
    for src in ["artsy", "saatchi"]:
        if src in cold:
            for k in ["catboost_v3_filtered_tuned", "ensemble"]:
                m = cold[src][k]
                print(f"  {src:<20} {k.replace('_v3_filtered_tuned', ''):<22} {m['n']:>6} "
                      f"{m['MdAPE']['point']:>11.2f}% [{m['MdAPE']['ci_low']:>5.2f}, {m['MdAPE']['ci_high']:>5.2f}] "
                      f"{m['W30']['point']:>9.2f}%")
    print("\nWarm KFold:")
    for k in ["catboost_v3_filtered_tuned", "xgboost_v3_filtered_tuned", "ensemble"]:
        m = warm[k]
        print(f"  {'':<20} {k.replace('_v3_filtered_tuned', ''):<22} {m['n']:>6} "
              f"{m['MdAPE']['point']:>11.2f}% [{m['MdAPE']['ci_low']:>5.2f}, {m['MdAPE']['ci_high']:>5.2f}] "
              f"{m['W30']['point']:>9.2f}%")
    print("Warm by source:")
    for src in ["artsy", "saatchi"]:
        if src in warm:
            for k in ["xgboost_v3_filtered_tuned", "ensemble"]:
                m = warm[src][k]
                print(f"  {'warm '+src:<20} {k.replace('_v3_filtered_tuned', ''):<22} {m['n']:>6} "
                      f"{m['MdAPE']['point']:>11.2f}% [{m['MdAPE']['ci_low']:>5.2f}, {m['MdAPE']['ci_high']:>5.2f}] "
                      f"{m['W30']['point']:>9.2f}%")
    print(f"\n저장: {OUT_PATH}")


if __name__ == "__main__":
    main()
