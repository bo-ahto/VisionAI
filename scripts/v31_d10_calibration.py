"""v3.1-1: D10 saatchi_online 전용 calibration layer 시도.

배경 (v3.0 Group 1.7 발견):
- D10 (예측가 최고 decile, n=2,838) ∩ saatchi_online (n=1,499) 에서
  log(pred/actual) median +1.359 (≈ 3.9× 과대예측). SDD01-SDD08 (D10 안의 actual
  하위 80%) 모두 강한 음수 → broad cell saturation. 단일 cold cell factor
  saatchi_online=0.9569 로는 부족.

방법:
1. Production cold path baseline: CatBoost OOF × cold_cell_factor[cell]
2. D10 segment 정의 (production-friendly absolute threshold):
   · 임계값 후보: 10M / 13.7M / 20M KRW (sensitivity)
   · D10 segment = (cold artist) AND (source=saatchi) AND (target_market=online)
                   AND (pred_price ≥ threshold)
3. D10 factor 추정 (cross-fit 5-fold by artist):
   · 각 GroupKFold split 에서 train fold (4/5) 의 D10 saatchi cold 행에서
     factor = median(actual / pred) 산출
   · test fold 의 D10 saatchi cold 행에 factor 적용 → 보정 예측
4. MdAPE 비교 (segment + 전체 cold):
   · before: cold path = CB × cold_cell_factor
   · after: cold path = CB × cold_cell_factor × (d10_factor if D10 segment else 1.0)
5. Threshold sensitivity: 임계값 3개 비교

산출물:
    model_test_results/v3_diagnostics/d10_calibration_v31.json

Usage:
    PYTHONPATH=src python3 scripts/v31_d10_calibration.py
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
OUT_JSON = DIAG_DIR / "d10_calibration_v31.json"
OOF_PATH = DIAG_DIR / "oof_predictions.npz"

THRESHOLDS_KRW = (10_000_000, 13_728_873, 20_000_000)
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
    }


def compute_d10_factor(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    mask: np.ndarray,
) -> float | None:
    """train fold D10 saatchi cold 행에서 median(actual/pred) 산출."""
    if not mask.any():
        return None
    valid = mask & (y_true > 0) & (y_pred > 0)
    if not valid.any():
        return None
    ratios = y_true[valid] / y_pred[valid]
    return float(np.median(ratios))


def paired_cluster_bootstrap_delta(
    y_true: np.ndarray,
    pred_before: np.ndarray,
    pred_after: np.ndarray,
    groups: np.ndarray,
    *,
    n_iter: int = 5000,
    alpha: float = 0.05,
    rng_seed: int = RNG_SEED,
) -> dict:
    """artist-cluster bootstrap on Δ MdAPE = MdAPE(after) - MdAPE(before).

    음수면 개선. CI 상한 < 0 ⇒ 통계적으로 명확한 개선.
    """
    rng = np.random.default_rng(rng_seed)
    valid = y_true > 0
    unique_groups = np.unique(groups)
    indices_by_group: dict = {g: np.where(groups == g)[0] for g in unique_groups}
    n_g = len(unique_groups)
    diffs = np.empty(n_iter)
    for i in range(n_iter):
        chosen = rng.choice(n_g, size=n_g, replace=True)
        idx = np.concatenate([indices_by_group[unique_groups[c]] for c in chosen])
        v = valid[idx]
        if not v.any():
            diffs[i] = 0.0
            continue
        ape_b = np.abs(y_true[idx][v] - pred_before[idx][v]) / y_true[idx][v]
        ape_a = np.abs(y_true[idx][v] - pred_after[idx][v]) / y_true[idx][v]
        diffs[i] = (np.median(ape_a) - np.median(ape_b)) * 100
    point_b = np.median(np.abs(y_true[valid] - pred_before[valid]) / y_true[valid]) * 100
    point_a = np.median(np.abs(y_true[valid] - pred_after[valid]) / y_true[valid]) * 100
    return {
        "method": "paired cluster (artist) bootstrap, Δ = MdAPE_after - MdAPE_before (음수=개선)",
        "delta_pp": float(point_a - point_b),
        "ci_low": float(np.percentile(diffs, 100 * alpha / 2)),
        "ci_high": float(np.percentile(diffs, 100 * (1 - alpha / 2))),
        "before_mdape": float(point_b),
        "after_mdape": float(point_a),
    }


def evaluate_threshold(
    y_full_price: np.ndarray,
    pred_baseline: np.ndarray,  # CB × cold_cell_factor 적용된 production cold path
    source: np.ndarray,
    target_market: np.ndarray,
    groups: np.ndarray,
    threshold_krw: float,
    n_splits: int = N_SPLITS,
) -> dict:
    """단일 임계값에서 cross-fit D10 factor + before/after 비교."""
    cold_d10_saatchi_mask_full = (
        (source == "saatchi") & (target_market == "online") & (pred_baseline >= threshold_krw)
    )
    n_d10_segment = int(cold_d10_saatchi_mask_full.sum())
    if n_d10_segment == 0:
        return {"threshold_krw": float(threshold_krw), "n_segment": 0, "skipped": True}

    # cross-fit by artist (1.7 분석과 정합 — within-artist 의존성 보존)
    pred_calibrated = pred_baseline.copy()
    fold_factors: list[float] = []
    fold_n_train: list[int] = []
    fold_n_test: list[int] = []
    gkf = GroupKFold(n_splits=n_splits)
    for tr, te in gkf.split(y_full_price, y_full_price, groups):
        train_d10_mask = np.zeros(len(y_full_price), dtype=bool)
        train_d10_mask[tr] = cold_d10_saatchi_mask_full[tr]
        factor = compute_d10_factor(y_full_price, pred_baseline, train_d10_mask)
        if factor is None:
            fold_factors.append(float("nan"))
            fold_n_train.append(int(train_d10_mask.sum()))
            fold_n_test.append(int(cold_d10_saatchi_mask_full[te].sum()))
            continue
        fold_factors.append(float(factor))
        fold_n_train.append(int(train_d10_mask.sum()))
        # apply on test fold D10 saatchi cold 행
        test_d10_mask = np.zeros(len(y_full_price), dtype=bool)
        test_d10_mask[te] = cold_d10_saatchi_mask_full[te]
        fold_n_test.append(int(test_d10_mask.sum()))
        pred_calibrated[test_d10_mask] = pred_baseline[test_d10_mask] * factor

    # full-data factor (서버 적용용 — production factor 추정값)
    full_factor = compute_d10_factor(y_full_price, pred_baseline, cold_d10_saatchi_mask_full)

    # 메트릭 (segment + 전체 cold)
    segment_metrics = {
        "before": {
            "MdAPE": mdape(
                y_full_price[cold_d10_saatchi_mask_full], pred_baseline[cold_d10_saatchi_mask_full]
            ),
            "W30": w30(
                y_full_price[cold_d10_saatchi_mask_full], pred_baseline[cold_d10_saatchi_mask_full]
            ),
            "log_ratio": log_ratio_quantiles(
                y_full_price[cold_d10_saatchi_mask_full],
                pred_baseline[cold_d10_saatchi_mask_full],
            ),
        },
        "after": {
            "MdAPE": mdape(
                y_full_price[cold_d10_saatchi_mask_full],
                pred_calibrated[cold_d10_saatchi_mask_full],
            ),
            "W30": w30(
                y_full_price[cold_d10_saatchi_mask_full],
                pred_calibrated[cold_d10_saatchi_mask_full],
            ),
            "log_ratio": log_ratio_quantiles(
                y_full_price[cold_d10_saatchi_mask_full],
                pred_calibrated[cold_d10_saatchi_mask_full],
            ),
        },
    }
    overall_metrics = {
        "before": {
            "MdAPE": mdape(y_full_price, pred_baseline),
            "W30": w30(y_full_price, pred_baseline),
        },
        "after": {
            "MdAPE": mdape(y_full_price, pred_calibrated),
            "W30": w30(y_full_price, pred_calibrated),
        },
    }
    # saatchi_online overall (D10 segment 외 saatchi 영향 점검)
    saatchi_online_mask = (source == "saatchi") & (target_market == "online")
    saatchi_metrics = {
        "before": {
            "MdAPE": mdape(y_full_price[saatchi_online_mask], pred_baseline[saatchi_online_mask]),
            "W30": w30(y_full_price[saatchi_online_mask], pred_baseline[saatchi_online_mask]),
        },
        "after": {
            "MdAPE": mdape(
                y_full_price[saatchi_online_mask], pred_calibrated[saatchi_online_mask]
            ),
            "W30": w30(y_full_price[saatchi_online_mask], pred_calibrated[saatchi_online_mask]),
        },
    }

    # Paired cluster bootstrap CI on Δ overall MdAPE (artist 단위)
    delta_overall_ci = paired_cluster_bootstrap_delta(
        y_full_price,
        pred_baseline,
        pred_calibrated,
        groups,
    )

    return {
        "threshold_krw": float(threshold_krw),
        "n_segment": n_d10_segment,
        "fold_factors": fold_factors,
        "fold_n_train": fold_n_train,
        "fold_n_test": fold_n_test,
        "full_data_factor": full_factor,
        "segment_metrics": segment_metrics,
        "overall_cold_metrics": overall_metrics,
        "overall_cold_paired_cluster_ci": delta_overall_ci,
        "saatchi_online_full_metrics": saatchi_metrics,
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

    # production cold path baseline: CB OOF × cold_cell_factor
    cal = json.loads(
        (OUT_DIR / "integrated_v3_filtered_tuned_source_calibration.json").read_text()
    )
    cold_factors = cal["cold_factors"]
    cb_price = np.exp(cb_gkf_ln)
    cell = cell_keys(source, target_market)
    pred_baseline = apply_cell_calibration(cb_price, cell, cold_factors)
    y_full_price = np.exp(y_actual_ln)

    # 임계값 후보 평가
    results: list[dict] = []
    for t in THRESHOLDS_KRW:
        logger.info("=== threshold = %s KRW ===", f"{int(t):,}")
        res = evaluate_threshold(
            y_full_price,
            pred_baseline,
            source,
            target_market,
            groups,
            t,
        )
        results.append(res)
        if res.get("skipped"):
            logger.info("  skipped (n_segment=0)")
            continue
        seg = res["segment_metrics"]
        logger.info(
            "  segment n=%d | before MdAPE=%.2f%% W30=%.2f%% / after MdAPE=%.2f%% W30=%.2f%%",
            res["n_segment"],
            seg["before"]["MdAPE"],
            seg["before"]["W30"],
            seg["after"]["MdAPE"],
            seg["after"]["W30"],
        )
        logger.info(
            "  segment log_ratio median: before=%+.3f / after=%+.3f",
            seg["before"]["log_ratio"]["median"],
            seg["after"]["log_ratio"]["median"],
        )
        ovc = res["overall_cold_metrics"]
        logger.info(
            "  overall cold n=%d | before MdAPE=%.2f%% / after MdAPE=%.2f%% (Δ=%+.3f%%p)",
            len(y_full_price),
            ovc["before"]["MdAPE"],
            ovc["after"]["MdAPE"],
            ovc["after"]["MdAPE"] - ovc["before"]["MdAPE"],
        )
        logger.info(
            "  full_data factor=%.4f, fold factors=%s",
            res["full_data_factor"] if res["full_data_factor"] else float("nan"),
            [f"{f:.4f}" for f in res["fold_factors"]],
        )

    summary = {
        "config": {
            "method": (
                "Cross-fit 5-fold by artist (GroupKFold). 각 fold 의 train (4/5) D10 saatchi "
                "cold 행에서 factor = median(actual/pred) 추정 → test fold (1/5) D10 saatchi "
                "cold 행에 적용. 평가 메트릭은 cross-fit 적용 후 OOF 기준."
            ),
            "production_cold_path_baseline": "CB OOF × cold_cell_factor[cell]",
            "d10_segment_definition": (
                "source=saatchi AND target_market=online AND pred_baseline >= threshold_krw"
            ),
            "thresholds_evaluated_krw": list(THRESHOLDS_KRW),
            "n_splits": N_SPLITS,
            "rng_seed": RNG_SEED,
            "status": "v3.1 stopgap candidate — deploy 결정 보류",
            "deploy_caveats": [
                "P1 nested purity: 본 평가는 기존 OOF predictions 위에 cross-fit factor 추정 "
                "+ 적용 형태. baseline OOF 자체가 GroupKFold 5-fold OOF이므로 nested 평가 "
                "보다 낙관적일 수 있음. deploy 전 GroupKFold split 안에서 'baseline 생성→"
                "threshold 판정→factor 추정→test 적용' 일괄 재평가 필요.",
                "P1 threshold post-hoc selection: 13.7M / 10M / 20M 후보 중 13.7M 이 최선이지만 "
                "동일 데이터에서 선택. v3.2 에선 holdout validation set 으로 검증 필요. "
                "13.7M 동결 정당화 = 1.7 분석에서 도출된 D10 boundary (예측가 quantile 90%) "
                "를 inference-time absolute threshold 로 동결.",
                "P1 under-prediction tail 악화: 단일 multiplicative factor 는 분포 균일 shift. "
                "median 은 0 으로 보정되나 P10 은 약 -0.26 추가 음수 (under-prediction 25% "
                "악화). 운영 의사결정: '고가 saatchi 일부 사용자에게 더 낮게 틀릴 위험을 "
                "의도적으로 수용' 명문화 필요.",
                "P1 confidence/range 재검토 부재: point estimate 만 이동, margin 변경 없음. "
                "deploy 전 D10 segment grade/margin 재정의 필요.",
                "P1 server PR: 별도 PR + artifact/config 기반 + regression test + shadow/A/B "
                "계획. mainline primary_predictor.py 즉시 변경 비권장.",
            ],
            "interpretation_caveat": (
                "단일 multiplicative factor 는 median 만 0 으로 옮기므로 분포 좌측 (P10) 은 더 "
                "음수가 됨. 즉 D10 saatchi 안의 underpriced art 일부는 보정 후 더 부정확해질 수 "
                "있음. MdAPE / W30 개선이 일관적이라면 50% 다수에 대한 이득이 10% 손실보다 큼을 "
                "의미. Quantile/conformal 보강은 v3.2 항목."
            ),
            "next_steps": [
                "v3.1.5: Group 5 라벨 정제 (korean_traditional 신설) → 매체 신호 강화로 D10 "
                "factor 크기 자체를 줄일 수 있는지 확인",
                "v3.2: quantile regression / conformal prediction 도입 (tail-aware)",
                "v3.2: D10 segment grade/margin 재정의 (D 등급 등 별도 신뢰도 단계)",
                "v3.2: Saatchi 고가 segment 추가 신호 (view count, sold ratio 등) 수집",
            ],
        },
        "thresholds": results,
    }

    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    logger.info("JSON 저장: %s", OUT_JSON)

    print("\n" + "=" * 100)
    print("v3.1-1 D10 saatchi calibration — threshold sensitivity")
    print("=" * 100)
    print(
        f"\n{'threshold':>13} {'n_seg':>6} {'factor':>8} {'seg before':>11} {'seg after':>11} "
        f"{'Δ seg':>9} {'cold before':>12} {'cold after':>11} {'Δ overall':>10}"
    )
    print("-" * 100)
    for r in results:
        if r.get("skipped"):
            continue
        seg_b = r["segment_metrics"]["before"]["MdAPE"]
        seg_a = r["segment_metrics"]["after"]["MdAPE"]
        ov_b = r["overall_cold_metrics"]["before"]["MdAPE"]
        ov_a = r["overall_cold_metrics"]["after"]["MdAPE"]
        f_str = f"{r['full_data_factor']:.4f}" if r["full_data_factor"] else "n/a"
        print(
            f"{int(r['threshold_krw']):>10,}KRW {r['n_segment']:>6} {f_str:>8} "
            f"{seg_b:>10.2f}% {seg_a:>10.2f}% {seg_a - seg_b:>+8.2f}%p "
            f"{ov_b:>11.2f}% {ov_a:>10.2f}% {ov_a - ov_b:>+9.2f}%p"
        )

    print(f"\n저장: {OUT_JSON}")


if __name__ == "__main__":
    main()
