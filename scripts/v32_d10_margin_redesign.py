"""v3.2-4: D10 segment grade/margin 재정의 ablation (production-routed, KF OOF 정합 v2).

배경 (v3.1-1 코덱스 P1 + v3.2-4 코덱스 R1 P0 + v3.3-1 코덱스 P0 fix):
- v3.1-1 단일 multiplicative factor 0.7569 는 **cold path 의 D10 segment** 만
  point estimate 를 이동. margin 변경 없음.
- 현재 grade/margin: A ±20% / B ±30% / C ±50% / D ±70% (additive symmetric).
- v3.2-3 conformal: D10 segment 90% interval median width 1.73 = [P×0.243, P×1.990].
- v3.2-4 v1 은 warm 행에 cold-protocol GroupKFold OOF (xgb_preds_gkf_ln, 작가 통째 홀드아웃)
  를 적용한 평가 프로토콜 버그가 있었음 → "warm A grade ±20% 13.6% coverage" 결론은 GKF artifact.
- 본 v2 (정정): warm slice KFold OOF (xgb_preds_kf_ln) 를 production routing 의 warm 위치에
  주입. cold 는 CB OOF × cell factor 그대로.

방법:
1. Production-routed prediction (KF OOF 정합):
   pred_routed[warm] = xgb_preds_kf_ln (warm slice OOF, full 길이로 broadcast)
   pred_routed[cold] = exp(cb_preds_gkf_ln) × cold_cell_factor[cell]
2. v3.1-1 layer 적용 (cold + saatchi_online + cold-baseline ≥ 13.7M 에만):
   pred_routed[cold_d10] *= 0.7569
3. 3개 cohort 분리 보고:
   - cold D10 : v3.1-1 layer 가 적용된 cohort (~27 행)
   - warm saatchi high-price : warm + saatchi + online + xgb_kf_pred ≥ 13.7M
   - all D10 routed : saatchi+online+pred_routed≥13.7M (참고용)
4. Grade 부여: server `determine_confidence()` 그대로 호출
5. 옵션 ablation (3개): A_existing / B_d10_grade_conformal / C_existing_boost_1.5x

산출물:
    model_test_results/v3_diagnostics/d10_margin_ablation.json

Usage:
    PYTHONPATH=src python3 scripts/v32_d10_margin_redesign.py
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from train_primary_market_v3_filtered import _warm_mask, load_data, prepare_features

from visionai.price_engine._eval_helpers import (
    apply_cell_calibration,
    cell_keys,
    derive_target_market,
)
from visionai.price_engine.api.primary_predictor import determine_confidence

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUT_DIR = ROOT / "model_test_results"
DIAG_DIR = OUT_DIR / "v3_diagnostics"
OOF_PATH = DIAG_DIR / "oof_predictions.npz"
CONFORMAL_JSON = DIAG_DIR / "d10_conformal.json"
OUT_JSON = DIAG_DIR / "d10_margin_ablation.json"

THRESHOLD_KRW = 13_728_873
TARGET_COVERAGE_PCT = 90.0
V31_FACTOR = 0.7569

# 기존 confidence grade margin (primary_predictor.py:71-89)
GRADE_MARGIN = {
    "A": 0.20,
    "B": 0.30,
    "C": 0.50,
    "D": 0.70,
}


def coverage_within_margin(
    y_true: np.ndarray,
    pred: np.ndarray,
    margin: float | np.ndarray,
) -> dict:
    """Additive symmetric margin: [pred*(1-m), pred*(1+m)] 안에 actual 포함 비율."""
    if isinstance(margin, float | int):
        margin = np.full(len(pred), float(margin))
    low = pred * (1 - margin)
    high = pred * (1 + margin)
    contains = (y_true >= low) & (y_true <= high)
    width_relative = (high - low) / pred
    return {
        "coverage_pct": float(contains.mean() * 100),
        "width_median": float(np.median(width_relative)),
        "width_p25": float(np.percentile(width_relative, 25)),
        "width_p75": float(np.percentile(width_relative, 75)),
        "low_median": float(np.median(low)),
        "high_median": float(np.median(high)),
    }


def coverage_within_multiplicative(
    y_true: np.ndarray,
    pred: np.ndarray,
    low_factor: float,
    high_factor: float,
) -> dict:
    """Multiplicative interval: [pred * low_factor, pred * high_factor]."""
    low = pred * low_factor
    high = pred * high_factor
    contains = (y_true >= low) & (y_true <= high)
    width_relative = np.full(len(pred), high_factor - low_factor)
    return {
        "coverage_pct": float(contains.mean() * 100),
        "width_median": float(np.median(width_relative)),
        "width_p25": float(np.percentile(width_relative, 25)),
        "width_p75": float(np.percentile(width_relative, 75)),
        "low_median": float(np.median(low)),
        "high_median": float(np.median(high)),
    }


def grade_distribution(grades: np.ndarray) -> dict:
    return {g: int((grades == g).sum()) for g in ["A", "B", "C", "D"] if (grades == g).any()}


def evaluate_cohort(
    label: str,
    mask: np.ndarray,
    y_full_price: np.ndarray,
    pred_routed: np.ndarray,
    grades_all: np.ndarray,
    margins_all: np.ndarray,
    new_d10_low_factor: float,
    new_d10_high_factor: float,
) -> dict:
    """Cohort 별 3 옵션 평가."""
    n = int(mask.sum())
    if n == 0:
        return {"n": 0, "skipped": True, "reason": "empty cohort"}

    y = y_full_price[mask]
    pred = pred_routed[mask]
    grades = grades_all[mask]
    margins_existing = margins_all[mask]
    margins_boosted = np.minimum(margins_existing * 1.5, 0.99)

    options = {
        "A_existing": coverage_within_margin(y, pred, margins_existing),
        "B_d10_grade_conformal": coverage_within_multiplicative(
            y, pred, new_d10_low_factor, new_d10_high_factor
        ),
        "C_existing_boost_1.5x": coverage_within_margin(y, pred, margins_boosted),
    }
    options["A_existing"]["description"] = (
        "기존 grade margin (server determine_confidence 그대로) — additive symmetric"
    )
    options["B_d10_grade_conformal"]["description"] = (
        f"D10 신설 등급, multiplicative margin from v3.2-3 conformal "
        f"(low_factor={new_d10_low_factor:.3f}, high_factor={new_d10_high_factor:.3f})"
    )
    options["C_existing_boost_1.5x"]["description"] = (
        "기존 grade margin × 1.5 boost (D → ±105% capped at 99%) — additive"
    )

    for opt_label, m in options.items():
        marker = "PASS" if m["coverage_pct"] >= TARGET_COVERAGE_PCT else "FAIL"
        logger.info(
            "  [%s | %s] coverage=%.1f%% (%s) / width=%.2f / [%.0f, %.0f] KRW",
            label,
            opt_label,
            m["coverage_pct"],
            marker,
            m["width_median"],
            m["low_median"],
            m["high_median"],
        )
    return {
        "n": n,
        "grade_distribution": grade_distribution(grades),
        "options": options,
    }


def main() -> None:
    DIAG_DIR.mkdir(parents=True, exist_ok=True)
    oof = np.load(OOF_PATH, allow_pickle=True)
    y_actual_ln = oof["y_actual_ln"]
    cb_gkf_ln = oof["cb_preds_gkf_ln"]
    xgb_kf_ln_warm = oof["xgb_preds_kf_ln"]  # warm slice OOF (n=27062)

    df = load_data()
    df = df[df.get("is_excluded_for_training", 0) != 1].reset_index(drop=True)
    _, y_check, groups = prepare_features(df)
    np.testing.assert_allclose(y_check, y_actual_ln, rtol=1e-10)

    source = df["source"].astype(str).to_numpy()
    target_market = derive_target_market(df["is_krw"])
    has_birth_year = df["has_birth_year"].astype(bool).to_numpy()

    # training_count: 학습 데이터 기준 작가별 row count
    artist_counts = df.groupby("artist_slug").size().to_dict()
    training_count = np.array(
        [int(artist_counts.get(a, 0)) for a in df["artist_slug"].astype(str)]
    )

    # production routing — KF OOF 정합 (코덱스 P0 fix)
    wmask = _warm_mask(groups)
    cb_price = np.exp(cb_gkf_ln)
    cell = cell_keys(source, target_market)

    cal = json.loads(
        (OUT_DIR / "integrated_v3_filtered_tuned_source_calibration.json").read_text()
    )
    cold_factors = cal["cold_factors"]
    cb_calibrated = apply_cell_calibration(cb_price, cell, cold_factors)

    # warm slice OOF (xgb_preds_kf_ln) 를 full 길이 array 로 broadcast
    # 정합 assert (코덱스 P2): warm slice 길이 + y 일치 검증 — silent mismatch 방지
    assert int(wmask.sum()) == len(xgb_kf_ln_warm), (
        f"warm slice OOF 길이 mismatch: wmask.sum()={int(wmask.sum())} vs "
        f"len(xgb_kf_ln_warm)={len(xgb_kf_ln_warm)}"
    )
    np.testing.assert_allclose(oof["y_warm_actual_ln"], y_actual_ln[wmask], rtol=1e-10)
    xgb_kf_full_ln = np.full_like(y_actual_ln, np.nan)
    xgb_kf_full_ln[wmask] = xgb_kf_ln_warm
    xgb_kf_price = np.exp(xgb_kf_full_ln)

    # warm → xgb_kf_price (KF OOF) / cold → cb_calibrated
    pred_routed_pre_v31 = np.where(wmask, xgb_kf_price, cb_calibrated)

    # v3.1-1 layer: cold + saatchi_online + cb_calibrated ≥ THRESHOLD
    cold_d10_mask = (
        (~wmask)
        & (source == "saatchi")
        & (target_market == "online")
        & (cb_calibrated >= THRESHOLD_KRW)
    )
    pred_routed = pred_routed_pre_v31.copy()
    pred_routed[cold_d10_mask] = pred_routed_pre_v31[cold_d10_mask] * V31_FACTOR

    y_full_price = np.exp(y_actual_ln)

    # server determine_confidence 룰 그대로 적용
    # - is_matched = True (학습 데이터 모두 matched)
    # - has_manual_profile = False (학습 데이터에 컬럼 없음, 보수적)
    grades_list = []
    for i in range(len(df)):
        grade, _ = determine_confidence(
            is_matched=True,
            training_count=int(training_count[i]),
            has_birth_year=bool(has_birth_year[i]),
            has_manual_profile=False,
            is_warm_artist=bool(wmask[i]),
        )
        grades_list.append(grade)
    grades_all = np.array(grades_list)
    margins_all = np.array([GRADE_MARGIN[g] for g in grades_all])

    # conformal quantiles 로딩
    if CONFORMAL_JSON.exists():
        conf = json.loads(CONFORMAL_JSON.read_text())
        fold_q = conf["fold_quantiles"]
        valid = [f for f in fold_q if not f.get("skipped")]
        q_low_avg = float(np.median([f["q_low"] for f in valid]))
        q_high_avg = float(np.median([f["q_high"] for f in valid]))
    else:
        q_low_avg = -1.43
        q_high_avg = 0.80
    new_d10_low_factor = float(np.exp(q_low_avg))
    new_d10_high_factor = float(np.exp(q_high_avg))

    # 3 cohort 정의 (코덱스 P0 액션) — warm 임계도 KF pred 기준
    saatchi_online_mask = (source == "saatchi") & (target_market == "online")
    high_price_routed_mask = pred_routed >= THRESHOLD_KRW
    cold_d10_eval_mask = cold_d10_mask  # v3.1-1 layer 가 닿는 행 (정확히 같은 정의)
    warm_saatchi_high_mask = wmask & saatchi_online_mask & (xgb_kf_price >= THRESHOLD_KRW)
    all_d10_routed_mask = saatchi_online_mask & high_price_routed_mask

    logger.info(
        "Cohort 크기: cold_d10=%d / warm_saatchi_high=%d / all_d10_routed=%d",
        int(cold_d10_eval_mask.sum()),
        int(warm_saatchi_high_mask.sum()),
        int(all_d10_routed_mask.sum()),
    )
    logger.info("전체 grade 분포: %s", grade_distribution(grades_all))

    cohort_eval = {
        "cold_d10": evaluate_cohort(
            "cold_d10",
            cold_d10_eval_mask,
            y_full_price,
            pred_routed,
            grades_all,
            margins_all,
            new_d10_low_factor,
            new_d10_high_factor,
        ),
        "warm_saatchi_high": evaluate_cohort(
            "warm_saatchi_high",
            warm_saatchi_high_mask,
            y_full_price,
            pred_routed,
            grades_all,
            margins_all,
            new_d10_low_factor,
            new_d10_high_factor,
        ),
        "all_d10_routed": evaluate_cohort(
            "all_d10_routed",
            all_d10_routed_mask,
            y_full_price,
            pred_routed,
            grades_all,
            margins_all,
            new_d10_low_factor,
            new_d10_high_factor,
        ),
    }

    summary = {
        "config": {
            "scope": (
                "v2 (KF OOF 정합): warm → xgb_preds_kf_ln (warm slice KFold OOF), "
                "cold → CB × cell factor. v3.1-1 cold-D10 layer factor=0.7569 는 cold + "
                f"saatchi_online + cb_calibrated ≥ {THRESHOLD_KRW:,} KRW 에만 적용. "
                "v1 은 warm 행에 cold-protocol GroupKFold OOF (xgb_preds_gkf_ln) 를 적용한 "
                "평가 프로토콜 버그 — '13.6% coverage' 결론은 GKF artifact, 본 v2 가 정답."
            ),
            "threshold_krw": THRESHOLD_KRW,
            "target_coverage_pct": TARGET_COVERAGE_PCT,
            "existing_grade_margins": GRADE_MARGIN,
            "v31_point_factor": V31_FACTOR,
            "grade_rule_source": "server determine_confidence (primary_predictor.py:52)",
            "grade_simplification_caveats": (
                "is_matched=True (학습 데이터 모두 matched 가정), has_manual_profile=False "
                "(학습 데이터 컬럼 없음, 보수적). training_count = 학습 데이터 기준 작가별 row count."
            ),
            "conformal_quantiles_used": {
                "q_low_log": q_low_avg,
                "q_high_log": q_high_avg,
                "low_factor": new_d10_low_factor,
                "high_factor": new_d10_high_factor,
            },
            "cohorts": {
                "cold_d10": (
                    "v3.1-1 layer 가 닿는 cohort: cold artist + saatchi + online + "
                    "cb_calibrated ≥ threshold. 본 ablation 의 primary cohort. n=27."
                ),
                "warm_saatchi_high": (
                    "warm artist + saatchi + online + xgb_kf_pred ≥ threshold. v3.1-1 미적용. "
                    "n=1,757 (KF OOF 정합)."
                ),
                "all_d10_routed": (
                    "saatchi + online + pred_routed ≥ threshold (warm/cold 합쳐서). "
                    "참고용 — production 의 D10 라우팅 평균 효과. n=1,767 중 warm 1,757 (99.4%)."
                ),
            },
            "cohort_comparability_caveat": (
                "cold_d10 cohort 정의는 cb_calibrated ≥ 13.7M, warm_saatchi_high 는 "
                "xgb_kf_price ≥ 13.7M — 임계 모델이 다르므로 cold vs warm 1:1 성능 비교는 unfair. "
                "production exposure 관점에서 all_d10_routed n=1,767 중 warm 1,757 (99.4%) — "
                "warm 결과 (A_existing 71.9%, conformal 97.4%) 가 cold (33.3%/77.8%) 보다 "
                "통계적으로 훨씬 안정적이지만, KF 정합 평가 = known-artist 시나리오 라는 제한 그대로."
            ),
            "conformal_warm_application_caveat": (
                "B_d10_grade_conformal 의 quantile (low_factor 0.243 / high_factor 1.990) 은 "
                "cold D10 calibration set 에서 학습된 split conformal 결과 (v3.2-3). warm cohort 에 "
                "그대로 적용한 97.4% coverage 는 over-cover (cold quantile 폭이 warm 에선 너무 wide) — "
                "deploy-valid 수치 X. warm 전용 row-level conformal (90.1%, width 0.96) 가 정합 결과 "
                "(v3.3-1 v2). 다만 row-level conformal 은 같은 cohort empirical coverage 이므로 "
                "운영 보장치로 과해석 X."
            ),
            "warm_cohort_generalization_caveat": (
                "warm_saatchi_high cohort 는 saatchi-only artists 100% (artsy 거래 0). source-mix "
                "일반화 결론으로 확장 X. KF 정합 평가는 known-artist 시나리오 = artist-held-out "
                "일반화 성능 주장 아님 (stress conformal coverage 88.3% 참고)."
            ),
            "deploy_caveat": (
                "본 ablation 은 research/comparison only. 실제 deploy 결정은 운영 측 + 별도 PR. "
                "warm row-level conformal width 0.96 > 기존 A-grade 0.40 → 통계적으로 합리적이나 "
                "현행 grade/margin 체계 대체는 제품 변경. cold D10 (n=27) 은 v3.1-1 paired Wilcoxon "
                "p=0.7 와 일관 — 본질 해결은 v3.3 모델/feature 개선."
            ),
        },
        "global_grade_distribution": grade_distribution(grades_all),
        "cohorts": cohort_eval,
    }

    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    logger.info("JSON 저장: %s", OUT_JSON)

    print("\n" + "=" * 100)
    print("v3.2-4 D10 segment grade/margin ablation (production-routed)")
    print("=" * 100)
    print(f"\n전체 grade 분포: {grade_distribution(grades_all)}")
    for cname, ce in cohort_eval.items():
        if ce.get("skipped"):
            continue
        print(f"\n[{cname}] n={ce['n']}, grade={ce['grade_distribution']}")
        print(
            f"  {'Option':<28} {'coverage':>10} {'width median':>13} "
            f"{'low_med (KRW)':>14} {'high_med (KRW)':>14}"
        )
        print("  " + "-" * 96)
        for opt_label, m in ce["options"].items():
            marker = "PASS" if m["coverage_pct"] >= TARGET_COVERAGE_PCT else "FAIL"
            print(
                f"  {opt_label:<28} {m['coverage_pct']:>9.1f}% {marker:>4} "
                f"{m['width_median']:>10.2f} {m['low_median']:>13,.0f} "
                f"{m['high_median']:>13,.0f}"
            )

    print(f"\n저장: {OUT_JSON}")


if __name__ == "__main__":
    main()
