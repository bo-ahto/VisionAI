"""v3.2-3: D10 split conformal calibration (tail-aware).

배경 (v3.1-1 코덱스 P1):
- v3.1-1 단일 multiplicative factor (median calibration) 는 D10 saatchi log-residual
  median 만 0 으로 옮김 — P10 (-0.46→-0.72, under-prediction 25% 악화). 분포 균일
  shift 의 한계.
- 코덱스 권고: quantile/conformal 도입으로 tail-aware approach. v3.2-3 의 본 작업.

방법: Split conformal prediction (artist-cluster cross-fit):
1. Production cold path baseline: CB OOF × cold cell factor
2. D10 segment: saatchi_online + cold + pred ≥ 13.7M KRW (v3.1-1 best threshold)
3. Cross-fit 5-fold by artist (within-artist 의존성 보존):
   - calibration fold (4/5): D10 segment 의 ln-residual r = ln(actual) - ln(pred_baseline)
     의 quantile (α/2, 1−α/2) 추정. median q50 도 함께 (point shift 용).
   - test fold (1/5): D10 segment 행에 적용
     · pred_point = pred_baseline × exp(q50)  (median shift = v3.1-1 단일 factor 와 등가)
     · pred_low = pred_baseline × exp(q_low)
     · pred_high = pred_baseline × exp(q_high)
4. 평가 (D10 segment 만):
   - point MdAPE (vs baseline + vs v3.1-1 단일 factor 비교)
   - log(pred_corrected/actual) 분포 (median 0 으로 이동, P10/P90 변화)
   - 90% interval coverage (목표: ~90%)
   - interval median width (운영 측 신뢰 구간 크기)

α=0.10 (90% prediction interval) 사용.

산출물:
    model_test_results/v3_diagnostics/d10_conformal.json

Usage:
    PYTHONPATH=src python3 scripts/v32_d10_conformal.py
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
from sklearn.model_selection import GroupKFold

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from train_primary_market_v3_filtered import load_data, prepare_features
from visionai.price_engine._eval_helpers import (
    apply_cell_calibration,
    cell_keys,
    derive_target_market,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUT_DIR = ROOT / "model_test_results"
DIAG_DIR = OUT_DIR / "v3_diagnostics"
OOF_PATH = DIAG_DIR / "oof_predictions.npz"
OUT_JSON = DIAG_DIR / "d10_conformal.json"

THRESHOLD_KRW = 13_728_873  # v3.1-1 best
ALPHA = 0.10  # 90% prediction interval
N_SPLITS = 5
RNG_SEED = 42


def mdape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    valid = y_true > 0
    if not valid.any():
        return float("nan")
    return float(np.median(np.abs(y_true[valid] - y_pred[valid]) / y_true[valid]) * 100)


def w30(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    valid = y_true > 0
    if not valid.any():
        return float("nan")
    return float(np.mean(np.abs(y_true[valid] - y_pred[valid]) / y_true[valid] <= 0.30) * 100)


def log_ratio_quantiles(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """log(pred/actual) — 양수=과대, 음수=과소예측."""
    valid = (y_true > 0) & (y_pred > 0)
    if not valid.any():
        return {}
    lr = np.log(y_pred[valid] / y_true[valid])
    return {
        "p10": float(np.percentile(lr, 10)),
        "p25": float(np.percentile(lr, 25)),
        "median": float(np.median(lr)),
        "p75": float(np.percentile(lr, 75)),
        "p90": float(np.percentile(lr, 90)),
        "mean": float(np.mean(lr)),
        "std": float(np.std(lr)),
    }


def main() -> None:
    DIAG_DIR.mkdir(parents=True, exist_ok=True)
    oof = np.load(OOF_PATH, allow_pickle=True)
    y_actual_ln = oof["y_actual_ln"]
    cb_gkf_ln = oof["cb_preds_gkf_ln"]

    df = load_data()
    df = df[df.get("is_excluded_for_training", 0) != 1].reset_index(drop=True)
    _, y_check, groups = prepare_features(df)
    np.testing.assert_allclose(y_check, y_actual_ln, rtol=1e-10)
    source = df["source"].astype(str).to_numpy()
    target_market = derive_target_market(df["is_krw"])

    # production cold path baseline: CB × cold cell factor
    cal = json.loads(
        (OUT_DIR / "integrated_v3_filtered_tuned_source_calibration.json").read_text()
    )
    cold_factors = cal["cold_factors"]
    cb_price = np.exp(cb_gkf_ln)
    cell = cell_keys(source, target_market)
    pred_baseline = apply_cell_calibration(cb_price, cell, cold_factors)
    pred_baseline_ln = np.log(pred_baseline)
    y_full_price = np.exp(y_actual_ln)

    # D10 segment mask
    d10_mask = (
        (source == "saatchi") & (target_market == "online") & (pred_baseline >= THRESHOLD_KRW)
    )
    n_d10 = int(d10_mask.sum())
    logger.info(
        "D10 segment n=%d (threshold=%s KRW, alpha=%.2f → %d%% interval)",
        n_d10,
        f"{THRESHOLD_KRW:,}",
        ALPHA,
        int((1 - ALPHA) * 100),
    )

    # Cross-fit split conformal (5-fold by artist)
    pred_corrected_point = pred_baseline.copy()  # median-shifted point
    pred_corrected_low = pred_baseline.copy()
    pred_corrected_high = pred_baseline.copy()
    fold_quantiles: list[dict] = []

    gkf = GroupKFold(n_splits=N_SPLITS)
    for fold_i, (tr, te) in enumerate(gkf.split(y_full_price, y_full_price, groups), 1):
        # calibration set: train fold 의 D10 segment ln-residual 잔차
        train_d10_mask = np.zeros(len(y_full_price), dtype=bool)
        train_d10_mask[tr] = d10_mask[tr]
        if not train_d10_mask.any():
            logger.warning("[fold %d] calibration D10 empty — skip", fold_i)
            fold_quantiles.append({"fold": fold_i, "n_cal": 0, "skipped": True})
            continue

        # ln(actual) - ln(pred_baseline) — calibration 잔차
        # 양수 = 모델이 과소예측, 음수 = 과대예측
        residuals_cal = y_actual_ln[train_d10_mask] - pred_baseline_ln[train_d10_mask]
        q_low = float(np.quantile(residuals_cal, ALPHA / 2))
        q_median = float(np.quantile(residuals_cal, 0.5))
        q_high = float(np.quantile(residuals_cal, 1 - ALPHA / 2))

        # test fold D10 segment 에 적용
        test_d10_mask = np.zeros(len(y_full_price), dtype=bool)
        test_d10_mask[te] = d10_mask[te]
        n_test = int(test_d10_mask.sum())
        if n_test == 0:
            fold_quantiles.append(
                {
                    "fold": fold_i,
                    "n_cal": int(train_d10_mask.sum()),
                    "n_test": 0,
                    "q_low": q_low,
                    "q_median": q_median,
                    "q_high": q_high,
                    "skipped": True,
                }
            )
            continue

        pred_corrected_point[test_d10_mask] = pred_baseline[test_d10_mask] * np.exp(q_median)
        pred_corrected_low[test_d10_mask] = pred_baseline[test_d10_mask] * np.exp(q_low)
        pred_corrected_high[test_d10_mask] = pred_baseline[test_d10_mask] * np.exp(q_high)

        fold_quantiles.append(
            {
                "fold": fold_i,
                "n_cal": int(train_d10_mask.sum()),
                "n_test": n_test,
                "q_low": q_low,
                "q_median": q_median,
                "q_high": q_high,
            }
        )
        logger.info(
            "[fold %d] n_cal=%d n_test=%d q_low=%+.3f q_med=%+.3f q_high=%+.3f",
            fold_i,
            int(train_d10_mask.sum()),
            n_test,
            q_low,
            q_median,
            q_high,
        )

    # 평가 (D10 segment 만)
    y_d10 = y_full_price[d10_mask]
    pred_baseline_d10 = pred_baseline[d10_mask]
    pred_point_d10 = pred_corrected_point[d10_mask]
    pred_low_d10 = pred_corrected_low[d10_mask]
    pred_high_d10 = pred_corrected_high[d10_mask]

    # Point metrics
    metrics_baseline = {
        "MdAPE": mdape(y_d10, pred_baseline_d10),
        "W30": w30(y_d10, pred_baseline_d10),
        "log_ratio": log_ratio_quantiles(y_d10, pred_baseline_d10),
    }
    metrics_corrected = {
        "MdAPE": mdape(y_d10, pred_point_d10),
        "W30": w30(y_d10, pred_point_d10),
        "log_ratio": log_ratio_quantiles(y_d10, pred_point_d10),
    }

    # Interval coverage + width
    interval_contains = (y_d10 >= pred_low_d10) & (y_d10 <= pred_high_d10)
    coverage = float(interval_contains.mean() * 100)
    interval_width_relative = (pred_high_d10 - pred_low_d10) / pred_baseline_d10
    interval_width = {
        "median": float(np.median(interval_width_relative)),
        "mean": float(np.mean(interval_width_relative)),
        "p25": float(np.percentile(interval_width_relative, 25)),
        "p75": float(np.percentile(interval_width_relative, 75)),
    }

    # v3.1-1 단일 factor 비교 (loaded from existing JSON)
    v31_compare: dict | None = None
    v31_path = DIAG_DIR / "d10_calibration_v31.json"
    if v31_path.exists():
        v31 = json.loads(v31_path.read_text())
        for t in v31.get("thresholds", []):
            if not t.get("skipped") and abs(t["threshold_krw"] - THRESHOLD_KRW) < 1:
                seg = t["segment_metrics"]
                v31_compare = {
                    "threshold_krw": t["threshold_krw"],
                    "v31_factor": t.get("full_data_factor"),
                    "after_MdAPE": seg["after"]["MdAPE"],
                    "after_W30": seg["after"]["W30"],
                    "after_log_ratio": seg["after"]["log_ratio"],
                }
                break

    summary = {
        "config": {
            "method": (
                "Split conformal prediction with artist-cluster cross-fit (5-fold). "
                "calibration fold 위 ln-residual 잔차 quantile 추정 → test fold D10 segment 에 "
                "적용. point = exp(q_median) shift, interval = exp(q_low/q_high) 곱셈."
            ),
            "production_cold_path_baseline": "CB OOF × cold_cell_factor[cell]",
            "d10_segment": (
                f"source=saatchi AND target_market=online AND pred_baseline >= "
                f"{THRESHOLD_KRW:,} KRW"
            ),
            "n_segment": n_d10,
            "alpha": ALPHA,
            "interval_coverage_target_pct": int((1 - ALPHA) * 100),
            "n_splits": N_SPLITS,
            "rng_seed": RNG_SEED,
            "comparison_to_v31_1": (
                "v3.1-1 단일 multiplicative factor (full_data_factor 0.7569) 는 분포 균일 shift — "
                "P10 -0.26 추가 음수 (under-prediction 25% 악화). 본 conformal 은 동일 median "
                "shift + α/2 quantile interval 로 tail-aware 신뢰 구간 산출. Point estimate 는 "
                "v3.1-1 와 동일 — 본 작업의 새 가치는 interval 만."
            ),
            "deploy_caveats": [
                "P1 coverage guarantee 약화 (codex v3.2-3): 본 실험은 artist GroupKFold cross-fit "
                "+ post-hoc segment 선택 (pred_baseline ≥ 13.7M) 위에서 residual quantile 적용 — "
                "고전적 split conformal 의 exchangeability 가정 그대로 가져오기 어려움. "
                "89.9% empirical coverage 는 본 평가에서 작동 입증, '90% guaranteed coverage' 단정 "
                "회피.",
                "P2 UX 폭 한계: median width 1.73 = P×0.24~P×2.23 (예: P=14M → [3.4M, 31M]). "
                "정직성은 있으나 사용자 가격 제안으로는 거의 무용. 실질적 narrow interval 은 "
                "**기저 모델/segment 피처 개선** 이 본질적 답 (LWC/QR 확장보다 우선) — "
                "irreducible spread 신호 (코덱스 v3.2-3 P2/P3).",
                "P2 v3.1-1 stopgap 과의 layering: point estimate 는 v3.1-1 와 정확히 동일 → "
                "본 작업의 새 가치는 interval layer 만. 운영 deploy 시 v3.1-1 (point) + "
                "v3.2-3 (interval) 별도 layer 로 분리 가능.",
            ],
            "interpretation": (
                "Research artifact: PASS (interval coverage 작동 입증). Deploy-ready 90% "
                "guaranteed interval: NOT PASS (coverage guarantee post-hoc segment + cluster "
                "cross-fit 으로 약화 + UX 폭 한계). 본 작업의 운영 가치는 'D10 saatchi 가격 "
                "불확실성의 정량 입증' (irreducible spread 강조 → v3.3 모델/feature 개선 동기) "
                "에 한정."
            ),
        },
        "fold_quantiles": fold_quantiles,
        "d10_segment_evaluation": {
            "n": n_d10,
            "before_baseline": metrics_baseline,
            "after_conformal_point": metrics_corrected,
            "interval": {
                "alpha": ALPHA,
                "target_coverage_pct": int((1 - ALPHA) * 100),
                "actual_coverage_pct": coverage,
                "width_relative": interval_width,
            },
        },
        "comparison_v31_1": v31_compare,
    }

    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    logger.info("JSON 저장: %s", OUT_JSON)

    print("\n" + "=" * 100)
    print("v3.2-3 D10 split conformal calibration (tail-aware)")
    print("=" * 100)

    print(
        f"\nD10 segment: n={n_d10}, threshold={THRESHOLD_KRW:,} KRW, α={ALPHA} ({int((1 - ALPHA) * 100)}% interval)"
    )

    print("\n[Point metrics]")
    print(
        f"  Before (baseline = CB × cell factor): MdAPE={metrics_baseline['MdAPE']:.2f}% "
        f"W30={metrics_baseline['W30']:.2f}%"
    )
    print(
        f"    log_ratio: P10={metrics_baseline['log_ratio']['p10']:+.3f} "
        f"med={metrics_baseline['log_ratio']['median']:+.3f} "
        f"P90={metrics_baseline['log_ratio']['p90']:+.3f}"
    )
    print(
        f"  After (conformal median shift): MdAPE={metrics_corrected['MdAPE']:.2f}% "
        f"W30={metrics_corrected['W30']:.2f}%"
    )
    print(
        f"    log_ratio: P10={metrics_corrected['log_ratio']['p10']:+.3f} "
        f"med={metrics_corrected['log_ratio']['median']:+.3f} "
        f"P90={metrics_corrected['log_ratio']['p90']:+.3f}"
    )

    if v31_compare:
        print(f"\n[Reference: v3.1-1 단일 factor (factor={v31_compare['v31_factor']:.4f})]")
        print(f"  MdAPE={v31_compare['after_MdAPE']:.2f}% W30={v31_compare['after_W30']:.2f}%")
        v31_lr = v31_compare["after_log_ratio"]
        print(
            f"    log_ratio: P10={v31_lr['p10']:+.3f} med={v31_lr['median']:+.3f} "
            f"P90={v31_lr['p90']:+.3f}"
        )

    print(f"\n[Interval (α={ALPHA}, target {int((1 - ALPHA) * 100)}% coverage)]")
    print(f"  actual coverage: {coverage:.1f}% (target {int((1 - ALPHA) * 100)}%)")
    print(
        f"  interval width relative to pred (median): {interval_width['median']:.2f} "
        f"(P25-P75: [{interval_width['p25']:.2f}, {interval_width['p75']:.2f}])"
    )
    print(f"\n저장: {OUT_JSON}")


if __name__ == "__main__":
    main()
