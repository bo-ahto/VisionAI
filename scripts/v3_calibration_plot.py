"""v3 Group 1.6: Calibration plot.

OOF 예측의 calibration 진단. production routing 정합 + offline diagnostic 분리:

Production paths (primary_predictor.py 와 일치):
- Cold: CatBoost only + cold cell factors (artsy_gallery=1.0 skipped /
  artsy_online=0.9426 / saatchi_online=0.9569)
- Warm: XGBoost only, no calibration

Offline diagnostic paths (참고용 — server에서 안 씀):
- Cold/Warm ensemble = (CB + XGB) / 2

각 경로에서 가격 decile별 median(actual)/median(predicted) 비율을 산출하여
모델이 어느 가격대에서 과대/과소 예측하는지 확인. cell × decile 분해 포함.

핵심 caveat:
- 셀별 calibrated ratio가 1.000에 매우 가까운 것은 production factor가 full-data
  median-ratio로 정의돼 같은 cell OOF에 다시 곱했기 때문 (구조적으로 자연스러움).
  factor의 일반화 효과는 별도 cross-fit MdAPE 개선으로 평가 (calibration JSON 참조).
- Decile binning은 calibrated y_pred 기준 재정렬이라 cell 내부 ranking은 보존되지만
  global decile membership은 cell 간 순서 변경으로 일부 이동 가능.

산출물:
    model_test_results/v3_diagnostics/calibration.json
    model_test_results/v3_diagnostics/calibration_production_cold.png
    model_test_results/v3_diagnostics/calibration_production_warm.png
    model_test_results/v3_diagnostics/calibration_offline_cold_ensemble.png

Usage:
    PYTHONPATH=src python3 scripts/v3_calibration_plot.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from train_primary_market_v3_filtered import load_data, prepare_features
from visionai.price_engine._eval_helpers import (
    apply_cell_calibration as _apply_cell_calibration_helper,
    cell_keys as _cell_keys_helper,
    derive_target_market as _derive_target_market_helper,
    warm_mask as _warm_mask,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUT_DIR = ROOT / "model_test_results"
DIAG_DIR = OUT_DIR / "v3_diagnostics"
OUT_JSON = DIAG_DIR / "calibration.json"
N_DECILES = 10


def _derive_target_market(df: pd.DataFrame) -> np.ndarray:
    """v3 cell calibration의 target_market 정의 — _eval_helpers wrapper."""
    return _derive_target_market_helper(df["is_krw"])


def _cell_keys(source: np.ndarray, target_market: np.ndarray) -> np.ndarray:
    return _cell_keys_helper(source, target_market)


def _apply_cell_calibration(
    pred_price: np.ndarray, cell: np.ndarray, factors: dict[str, float],
) -> np.ndarray:
    """Production multiplicative calibration — _eval_helpers wrapper."""
    return _apply_cell_calibration_helper(pred_price, cell, factors)


def _decile_stats(
    y_true: np.ndarray, y_pred: np.ndarray, n_bins: int = N_DECILES,
) -> list[dict]:
    """예측가격 기준 decile별 calibration 통계."""
    quantiles = np.quantile(y_pred, np.linspace(0, 1, n_bins + 1))
    quantiles[-1] = quantiles[-1] * 1.000001  # right-edge inclusion
    stats = []
    for b in range(n_bins):
        lo, hi = quantiles[b], quantiles[b + 1]
        mask = (y_pred >= lo) & (y_pred < hi)
        if not mask.any():
            continue
        yt = y_true[mask]
        yp = y_pred[mask]
        valid = yt > 0
        if not valid.any():
            continue
        ratio = yt[valid] / yp[valid]
        ape = np.abs(yt[valid] - yp[valid]) / yt[valid]
        stats.append({
            "bin": int(b + 1),
            "pred_low": float(lo),
            "pred_high": float(hi),
            "n": int(valid.sum()),
            "median_pred": float(np.median(yp[valid])),
            "median_actual": float(np.median(yt[valid])),
            "median_ratio": float(np.median(ratio)),
            "mean_ratio": float(np.mean(ratio)),
            "mdape": float(np.median(ape) * 100),
        })
    return stats


def _cell_breakdown(
    y_true: np.ndarray, y_pred: np.ndarray, cell: np.ndarray,
) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for k in sorted(set(cell.tolist())):
        m = cell == k
        if not m.any():
            continue
        yt = y_true[m]
        yp = y_pred[m]
        valid = yt > 0
        if not valid.any():
            continue
        ratio = yt[valid] / yp[valid]
        ape = np.abs(yt[valid] - yp[valid]) / yt[valid]
        out[k] = {
            "n": int(valid.sum()),
            "median_ratio": float(np.median(ratio)),
            "mean_ratio": float(np.mean(ratio)),
            "mdape": float(np.median(ape) * 100),
        }
    return out


def _plot_calibration(
    stats: list[dict], title: str, out_path: Path,
    secondary_stats: list[dict] | None = None, secondary_label: str = "",
) -> None:
    if not stats:
        return
    fig, ax1 = plt.subplots(figsize=(9, 5.5), facecolor="#1a1a1a")
    ax1.set_facecolor("#1a1a1a")
    bins = [s["bin"] for s in stats]
    ratios = [s["median_ratio"] for s in stats]
    mdapes = [s["mdape"] for s in stats]

    ax1.axhline(1.0, color="#888", linestyle="--", linewidth=1, label="완벽 보정 (ratio=1.0)")
    ax1.plot(bins, ratios, "o-", color="#4FC3F7", linewidth=2, markersize=8, label=f"raw ratio = median(actual/pred)")
    if secondary_stats:
        bins2 = [s["bin"] for s in secondary_stats]
        ratios2 = [s["median_ratio"] for s in secondary_stats]
        ax1.plot(bins2, ratios2, "s-", color="#FFB74D", linewidth=2, markersize=8, label=f"{secondary_label} ratio")
    ax1.set_xlabel("예측 가격 decile (1=저가 → 10=고가)", color="white")
    ax1.set_ylabel("median(actual/pred)", color="#4FC3F7")
    ax1.tick_params(colors="white")
    for spine in ax1.spines.values():
        spine.set_color("white")
    ax1.set_xticks(bins)
    ax1.grid(alpha=0.2)

    ax2 = ax1.twinx()
    ax2.set_facecolor("#1a1a1a")
    ax2.plot(bins, mdapes, "^--", color="#E57373", linewidth=1.5, markersize=7, label="MdAPE per bin (%)")
    ax2.set_ylabel("MdAPE (%) per decile", color="#E57373")
    ax2.tick_params(colors="white")
    for spine in ax2.spines.values():
        spine.set_color("white")

    ax1.legend(loc="upper left", framealpha=0.85)
    ax2.legend(loc="upper right", framealpha=0.85)
    fig.suptitle(title, color="white", fontsize=13)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120, facecolor="#1a1a1a")
    plt.close(fig)
    logger.info("plot saved: %s", out_path)


def main() -> None:
    DIAG_DIR.mkdir(parents=True, exist_ok=True)

    oof = np.load(DIAG_DIR / "oof_predictions.npz", allow_pickle=True)
    y_actual_ln = oof["y_actual_ln"]
    cb_gkf_ln = oof["cb_preds_gkf_ln"]
    xgb_gkf_ln = oof["xgb_preds_gkf_ln"]
    y_warm_ln = oof["y_warm_actual_ln"]
    cb_kf_ln = oof["cb_preds_kf_ln"]
    xgb_kf_ln = oof["xgb_preds_kf_ln"]

    df = load_data()
    df = df[df.get("is_excluded_for_training", 0) != 1].reset_index(drop=True)
    X, y_check, groups = prepare_features(df)
    np.testing.assert_allclose(y_check, y_actual_ln, rtol=1e-10)
    target_market = _derive_target_market(df)
    source = df["source"].astype(str).to_numpy()
    cell = _cell_keys(source, target_market)

    wmask = _warm_mask(groups)
    cell_warm = cell[wmask]

    # 모델 출력
    y_full = np.exp(y_actual_ln)
    y_warm_full = np.exp(y_warm_ln)
    # Production routing (primary_predictor.py): cold=CB only + 셀 보정 / warm=XGB only (보정 X)
    cb_cold = np.exp(cb_gkf_ln)  # production cold raw
    xgb_warm = np.exp(xgb_kf_ln)  # production warm
    # Offline diagnostic / what-if: ensemble (CB+XGB)/2
    ens_cold_raw = np.exp((cb_gkf_ln + xgb_gkf_ln) / 2)
    ens_warm_raw = np.exp((cb_kf_ln + xgb_kf_ln) / 2)

    # 셀 보정 적용
    cal_path = OUT_DIR / "integrated_v3_filtered_tuned_source_calibration.json"
    cal = json.loads(cal_path.read_text())
    cold_factors = cal["cold_factors"]
    warm_factors = cal["warm_factors"]
    cb_cold_calibrated = _apply_cell_calibration(cb_cold, cell, cold_factors)  # production cold
    ens_cold_calibrated = _apply_cell_calibration(ens_cold_raw, cell, cold_factors)
    ens_warm_calibrated = _apply_cell_calibration(ens_warm_raw, cell_warm, warm_factors)

    # decile + cell breakdown 산출
    out: dict = {
        "config": {
            "n_deciles": N_DECILES,
            "production_routing": {
                "cold": "CatBoost only + cold cell factors (primary_predictor.py:351-371)",
                "warm": "XGBoost only, no calibration (primary_predictor.py:328 use_xgb)",
            },
            "ensemble_note": (
                "Ensemble (CB+XGB)/2 paths labeled 'offline_diagnostic' — "
                "production은 라우팅된 단일 모델 + cold path만 calibration."
            ),
            "cold_factors": cold_factors,
            "warm_factors": warm_factors,
            "interpretation": (
                "median_ratio = median(actual/pred). 1.0 이면 완벽 보정. "
                "ratio > 1: 과소예측 (실제 > 예측). ratio < 1: 과대예측. "
                "Cell-level calibrated ratio가 1.000에 매우 가까운 것은 production factor가 "
                "full-data median-ratio로 정의된 것을 같은 cell OOF에 다시 곱한 결과 — 구조적으로 "
                "자연스러움. factor의 일반화 효과는 별도 cross-fit MdAPE 개선 (calibration JSON의 "
                "delta_guarded)으로 평가. "
                "Decile binning은 calibrated y_pred로 재정렬: cell 내부 ranking은 보존되지만 "
                "global decile membership은 일부 변함."
            ),
        },
        "production_cold": {  # CB only + cold cell factors (server 와 정합)
            "model": "catboost_v3_filtered_tuned",
            "n": int(len(y_full)),
            "raw_deciles": _decile_stats(y_full, cb_cold),
            "raw_cell_breakdown": _cell_breakdown(y_full, cb_cold, cell),
            "calibrated_deciles": _decile_stats(y_full, cb_cold_calibrated),
            "calibrated_cell_breakdown": _cell_breakdown(y_full, cb_cold_calibrated, cell),
        },
        "production_warm": {  # XGB only, no calibration
            "model": "xgboost_v3_filtered_tuned",
            "n": int(len(y_warm_full)),
            "deciles": _decile_stats(y_warm_full, xgb_warm),
            "cell_breakdown": _cell_breakdown(y_warm_full, xgb_warm, cell_warm),
        },
        "offline_diagnostic_cold_ensemble": {
            "n": int(len(y_full)),
            "raw_deciles": _decile_stats(y_full, ens_cold_raw),
            "raw_cell_breakdown": _cell_breakdown(y_full, ens_cold_raw, cell),
            "calibrated_deciles": _decile_stats(y_full, ens_cold_calibrated),
            "calibrated_cell_breakdown": _cell_breakdown(y_full, ens_cold_calibrated, cell),
        },
        "offline_diagnostic_warm_ensemble": {
            "n": int(len(y_warm_full)),
            "raw_deciles": _decile_stats(y_warm_full, ens_warm_raw),
            "raw_cell_breakdown": _cell_breakdown(y_warm_full, ens_warm_raw, cell_warm),
            "calibrated_deciles": _decile_stats(y_warm_full, ens_warm_calibrated),
            "calibrated_cell_breakdown": _cell_breakdown(y_warm_full, ens_warm_calibrated, cell_warm),
        },
    }

    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    logger.info("JSON 저장: %s", OUT_JSON)

    # PNG plot — production cold/warm 우선
    _plot_calibration(
        out["production_cold"]["raw_deciles"],
        "Production cold path (CatBoost only, n=28,376) — raw vs cell-calibrated",
        DIAG_DIR / "calibration_production_cold.png",
        secondary_stats=out["production_cold"]["calibrated_deciles"],
        secondary_label="cell-calibrated",
    )
    _plot_calibration(
        out["production_warm"]["deciles"],
        "Production warm path (XGBoost only, n=27,062, no calibration)",
        DIAG_DIR / "calibration_production_warm.png",
    )
    _plot_calibration(
        out["offline_diagnostic_cold_ensemble"]["raw_deciles"],
        "Offline diagnostic — Cold ensemble (CB+XGB)/2 raw vs calibrated",
        DIAG_DIR / "calibration_offline_cold_ensemble.png",
        secondary_stats=out["offline_diagnostic_cold_ensemble"]["calibrated_deciles"],
        secondary_label="cell-calibrated",
    )

    # Console summary
    print("\n" + "=" * 100)
    print("v3 Group 1.6 Calibration Summary")
    print("=" * 100)

    def _print_cells(label: str, cells: dict[str, dict]) -> None:
        print(f"  {label}:")
        for k, v in cells.items():
            print(f"    {k:<20} n={v['n']:>5} ratio={v['median_ratio']:>5.3f} MdAPE={v['mdape']:>5.2f}%")

    print("\n[production_cold] CatBoost only (server 와 정합)")
    _print_cells("raw cells", out["production_cold"]["raw_cell_breakdown"])
    _print_cells("calibrated cells", out["production_cold"]["calibrated_cell_breakdown"])
    print(f"  raw decile spread: min={min(d['median_ratio'] for d in out['production_cold']['raw_deciles']):.3f} "
          f"max={max(d['median_ratio'] for d in out['production_cold']['raw_deciles']):.3f}")
    print(f"  calibrated decile spread: min={min(d['median_ratio'] for d in out['production_cold']['calibrated_deciles']):.3f} "
          f"max={max(d['median_ratio'] for d in out['production_cold']['calibrated_deciles']):.3f}")

    print("\n[production_warm] XGBoost only (no calibration)")
    _print_cells("cells", out["production_warm"]["cell_breakdown"])
    print(f"  decile spread: min={min(d['median_ratio'] for d in out['production_warm']['deciles']):.3f} "
          f"max={max(d['median_ratio'] for d in out['production_warm']['deciles']):.3f}")

    print("\n[offline_diagnostic_cold_ensemble] (CB+XGB)/2")
    _print_cells("raw cells", out["offline_diagnostic_cold_ensemble"]["raw_cell_breakdown"])
    _print_cells("calibrated cells", out["offline_diagnostic_cold_ensemble"]["calibrated_cell_breakdown"])

    print(f"\n저장: {OUT_JSON}")


if __name__ == "__main__":
    main()
