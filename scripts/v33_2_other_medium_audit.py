"""v3.3-2 v2: 'other' medium 라벨 정제 — KT strong/ambiguous 분리 + stratified.

배경 (v3.0 보고서 §8.5 + 코덱스 v3.3-2 P0/P1):
- v1 결과: KT 후보 n=308 MdAPE 9.06% ≈ acrylic 9.04% (p=0.44). 라벨 정제 가치 낮아 보임.
- 코덱스 P0: silk / lacquer / gold leaf 등은 한국 전통 전용 X → keyword 를
  strong / ambiguous / silk_only 분리 필요. silk 가 가장 큰 false positive 원인.
- 코덱스 P0: "이미 다른 신호로 안정 학습됨" vs "우연히 쉬운 집단" 구분 위해
  strong KT 의 warm/cold × source × work_count stratified stability check.
- 결론 framing: "korean_traditional 신설 즉시 재학습 우선순위 낮다" 까지 (close 가능).
  "라벨 정제 가치 없음" 까지 닫지 않음.

방법:
1. KT keyword 3-tier 분리:
   - strong_kt: hanji, jangji, korean paper, mulberry paper, gofun, bunchae,
                stone powder, korean traditional, korean painting
   - silk_only: silk (단독 매칭, false positive 검증용 별도 cohort)
   - ambiguous: lacquer, mother of pearl, gold leaf, silver leaf, mulberry
2. cohort 분리:
   - strong_kt / silk_only / ambiguous_kt / other_residual / acrylic / oil
3. strong_kt cohort 의 stratified stability check:
   - warm vs cold
   - source (saatchi / artsy)
   - work_count bucket (1-2 / 3-4 / 5-9 / 10+)

산출물:
    model_test_results/v3_diagnostics/other_medium_audit.json

Usage:
    PYTHONPATH=src python3 scripts/v33_2_other_medium_audit.py
"""

from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path

import numpy as np
from scipy.stats import mannwhitneyu

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from train_primary_market_v3_filtered import _warm_mask, load_data, prepare_features

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
OUT_JSON = DIAG_DIR / "other_medium_audit.json"

# KT keyword 3-tier (코덱스 v3.3-2 P0)
STRONG_KT_KEYWORDS = [
    "hanji",
    "jangji",
    "korean paper",
    "mulberry paper",
    "gofun",
    "bunchae",
    "stone powder",
    "stone, burnt paper",
    "korean traditional",
    "korean painting",
]
SILK_KEYWORDS = ["silk"]  # 단독 매칭 (false positive 검증)
AMBIGUOUS_KT_KEYWORDS = [
    "lacquer",
    "mother of pearl",
    "gold leaf",
    "silver leaf",
    "mulberry",  # mulberry paper 외 단독 mulberry
]

STRONG_KT_PATTERN = re.compile(r"|".join(re.escape(k) for k in STRONG_KT_KEYWORDS), re.IGNORECASE)
SILK_PATTERN = re.compile(r"\bsilk\b", re.IGNORECASE)
AMBIG_PATTERN = re.compile(r"|".join(re.escape(k) for k in AMBIGUOUS_KT_KEYWORDS), re.IGNORECASE)

EXCLUDE_RAW_VALUES = {"", "none", "nan", "(null)", "other", "color", "color, other"}


def classify_kt(raw: str) -> str:
    """3-tier KT 분류: strong / silk_only / ambiguous / none."""
    if not raw or raw.lower() in EXCLUDE_RAW_VALUES:
        return "none"
    has_strong = bool(STRONG_KT_PATTERN.search(raw))
    has_silk = bool(SILK_PATTERN.search(raw))
    has_ambig = bool(AMBIG_PATTERN.search(raw))
    if has_strong:
        return "strong"
    if has_silk and not has_strong:
        return "silk_only"
    if has_ambig:
        return "ambiguous"
    return "none"


def quantile_summary(arr: np.ndarray) -> dict:
    if len(arr) == 0:
        return {"n": 0}
    return {
        "n": len(arr),
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "p10": float(np.percentile(arr, 10)),
        "p25": float(np.percentile(arr, 25)),
        "median": float(np.median(arr)),
        "p75": float(np.percentile(arr, 75)),
        "p90": float(np.percentile(arr, 90)),
    }


def cohort_residual_stats(
    y_actual_price: np.ndarray,
    pred_price: np.ndarray,
    mask: np.ndarray,
    label: str,
) -> dict:
    n = int(mask.sum())
    if n == 0:
        return {"label": label, "n": 0, "skipped": True}
    y = y_actual_price[mask]
    p = pred_price[mask]
    log_resid = np.log(y / p)
    signed_pct = (y - p) / p * 100
    abs_pct = np.abs(signed_pct)
    return {
        "label": label,
        "n": n,
        "mdape_pct": float(np.median(abs_pct)),
        "median_signed_pct": float(np.median(signed_pct)),
        "p10_signed_pct": float(np.percentile(signed_pct, 10)),
        "p90_signed_pct": float(np.percentile(signed_pct, 90)),
        "log_residual_summary": quantile_summary(log_resid),
        "_log_resid_arr": log_resid,  # for paired test (popped before JSON)
    }


def main() -> None:
    DIAG_DIR.mkdir(parents=True, exist_ok=True)
    oof = np.load(OOF_PATH, allow_pickle=True)
    y_actual_ln = oof["y_actual_ln"]
    cb_gkf_ln = oof["cb_preds_gkf_ln"]
    xgb_kf_ln_warm = oof["xgb_preds_kf_ln"]

    df = load_data()
    df = df[df.get("is_excluded_for_training", 0) != 1].reset_index(drop=True)
    _, y_check, groups = prepare_features(df)
    np.testing.assert_allclose(y_check, y_actual_ln, rtol=1e-10)

    source = df["source"].astype(str).to_numpy()
    target_market = derive_target_market(df["is_krw"])
    medium_cat = df["medium_category"].astype(str).fillna("unknown").to_numpy()
    medium_raw = df["medium"].fillna("").astype(str).to_numpy()

    # production routing (KF OOF 정합)
    wmask = _warm_mask(groups)
    assert int(wmask.sum()) == len(xgb_kf_ln_warm)
    np.testing.assert_allclose(oof["y_warm_actual_ln"], y_actual_ln[wmask], rtol=1e-10)
    cb_price = np.exp(cb_gkf_ln)
    cell = cell_keys(source, target_market)
    cal = json.loads(
        (OUT_DIR / "integrated_v3_filtered_tuned_source_calibration.json").read_text()
    )
    cb_calibrated = apply_cell_calibration(cb_price, cell, cal["cold_factors"])
    xgb_kf_full_ln = np.full_like(y_actual_ln, np.nan)
    xgb_kf_full_ln[wmask] = xgb_kf_ln_warm
    xgb_kf_price = np.exp(xgb_kf_full_ln)
    pred_routed = np.where(wmask, xgb_kf_price, cb_calibrated)
    y_full_price = np.exp(y_actual_ln)

    # 3-tier KT 분류 (코덱스 P0)
    other_mask = medium_cat == "other"
    kt_class = np.array([classify_kt(r) for r in medium_raw])
    strong_kt_mask = other_mask & (kt_class == "strong")
    silk_only_mask = other_mask & (kt_class == "silk_only")
    ambiguous_kt_mask = other_mask & (kt_class == "ambiguous")
    other_residual_mask = other_mask & (kt_class == "none")
    acrylic_mask = medium_cat == "acrylic"
    oil_mask = medium_cat == "oil"

    n_other = int(other_mask.sum())
    n_strong = int(strong_kt_mask.sum())
    n_silk = int(silk_only_mask.sum())
    n_ambig = int(ambiguous_kt_mask.sum())
    n_other_res = int(other_residual_mask.sum())
    logger.info(
        "other n=%d / strong KT=%d / silk_only=%d / ambiguous=%d / 잔여=%d",
        n_other,
        n_strong,
        n_silk,
        n_ambig,
        n_other_res,
    )

    # raw label 분포
    from collections import Counter

    raw_top_by_class = {
        "strong": dict(Counter(medium_raw[strong_kt_mask]).most_common(15)),
        "silk_only": dict(Counter(medium_raw[silk_only_mask]).most_common(15)),
        "ambiguous": dict(Counter(medium_raw[ambiguous_kt_mask]).most_common(15)),
    }

    # source × cohort raw count + silk_only QA (코덱스 P0 4)
    artist_slugs = df["artist_slug"].astype(str).to_numpy()
    source_x_cohort = {}
    for cohort_label, cohort_mask in [
        ("strong_kt", strong_kt_mask),
        ("silk_only", silk_only_mask),
        ("ambiguous_kt", ambiguous_kt_mask),
        ("other_residual", other_residual_mask),
    ]:
        n_co = int(cohort_mask.sum())
        if n_co == 0:
            source_x_cohort[cohort_label] = {"saatchi": 0, "artsy": 0}
            continue
        source_x_cohort[cohort_label] = {
            "saatchi": int((source[cohort_mask] == "saatchi").sum()),
            "artsy": int((source[cohort_mask] == "artsy").sum()),
        }

    silk_qa = {}
    if n_silk > 0:
        silk_artists = artist_slugs[silk_only_mask]
        silk_top_artists = dict(Counter(silk_artists).most_common(10))
        silk_prices = y_full_price[silk_only_mask]
        silk_qa = {
            "n": n_silk,
            "source": source_x_cohort["silk_only"],
            "top_10_artists_concentration": silk_top_artists,
            "n_unique_artists": len(set(silk_artists)),
            "price_quantiles": {
                "min": float(silk_prices.min()),
                "p25": float(np.percentile(silk_prices, 25)),
                "median": float(np.median(silk_prices)),
                "p75": float(np.percentile(silk_prices, 75)),
                "max": float(silk_prices.max()),
            },
            "warm_count": int((silk_only_mask & wmask).sum()),
            "cold_count": int((silk_only_mask & ~wmask).sum()),
        }

    # cohort residual stats
    cohorts = {}
    for label, mask in [
        ("strong_kt", strong_kt_mask),
        ("silk_only", silk_only_mask),
        ("ambiguous_kt", ambiguous_kt_mask),
        ("other_residual", other_residual_mask),
        ("acrylic", acrylic_mask),
        ("oil", oil_mask),
    ]:
        cohorts[label] = cohort_residual_stats(y_full_price, pred_routed, mask, label)

    # Mann-Whitney U comparisons (각 KT 그룹 vs other_residual / acrylic)
    comparisons = {}

    def _mwu(label_a: str, arr_a: np.ndarray, label_b: str, arr_b: np.ndarray) -> dict:
        u, p = mannwhitneyu(arr_a, arr_b, alternative="two-sided")
        return {
            "U_statistic": float(u),
            "p_value": float(p),
            f"median_{label_a}": float(np.median(arr_a)),
            f"median_{label_b}": float(np.median(arr_b)),
            f"n_{label_a}": len(arr_a),
            f"n_{label_b}": len(arr_b),
        }

    for kt_label in ["strong_kt", "silk_only", "ambiguous_kt"]:
        if cohorts[kt_label].get("skipped"):
            continue
        kt_abs = np.abs(cohorts[kt_label]["_log_resid_arr"])
        for ref_label in ["other_residual", "acrylic"]:
            if cohorts[ref_label].get("skipped"):
                continue
            ref_abs = np.abs(cohorts[ref_label]["_log_resid_arr"])
            comparisons[f"{kt_label}_vs_{ref_label}"] = _mwu(kt_label, kt_abs, ref_label, ref_abs)

    # strong_kt stratified stability check (코덱스 P0 R2)
    # warm/cold × source × work_count bucket
    strong_strat = {}
    if n_strong > 0:
        artist_counts_all = df.groupby("artist_slug").size().to_dict()
        training_count_arr = np.array(
            [int(artist_counts_all.get(a, 0)) for a in df["artist_slug"].astype(str)]
        )

        def _bucket(c: int) -> str:
            if c <= 2:
                return "1-2"
            if c <= 4:
                return "3-4"
            if c <= 9:
                return "5-9"
            return "10+"

        wc_bucket_arr = np.array([_bucket(c) for c in training_count_arr])

        strong_strat["by_warm_cold"] = {}
        for is_warm_label, m_path in [("warm", wmask), ("cold", ~wmask)]:
            sub = strong_kt_mask & m_path
            stats = cohort_residual_stats(
                y_full_price, pred_routed, sub, f"strong_kt_{is_warm_label}"
            )
            stats.pop("_log_resid_arr", None)
            strong_strat["by_warm_cold"][is_warm_label] = stats

        strong_strat["by_source"] = {}
        for s in ["saatchi", "artsy"]:
            sub = strong_kt_mask & (source == s)
            stats = cohort_residual_stats(y_full_price, pred_routed, sub, f"strong_kt_{s}")
            stats.pop("_log_resid_arr", None)
            strong_strat["by_source"][s] = stats

        strong_strat["by_work_count_bucket"] = {}
        for b in ["1-2", "3-4", "5-9", "10+"]:
            sub = strong_kt_mask & (wc_bucket_arr == b)
            stats = cohort_residual_stats(y_full_price, pred_routed, sub, f"strong_kt_wc_{b}")
            stats.pop("_log_resid_arr", None)
            strong_strat["by_work_count_bucket"][b] = stats

    # JSON serialization 전 _log_resid_arr 제거
    cohorts_clean = {
        k: {kk: vv for kk, vv in v.items() if kk != "_log_resid_arr"} for k, v in cohorts.items()
    }

    # log
    for label, c in cohorts.items():
        if c.get("skipped"):
            continue
        logger.info(
            "[%s] n=%d / MdAPE=%.2f%% / median signed=%+.2f%% / log_resid median=%+.3f",
            c["label"],
            c["n"],
            c["mdape_pct"],
            c["median_signed_pct"],
            c["log_residual_summary"]["median"],
        )

    summary = {
        "config": {
            "scope": (
                "v3.3-2 v2 (코덱스 P0/P1 fix): KT keyword 3-tier 분리 (strong / silk_only / "
                "ambiguous) + strong_kt 의 warm/cold × source × work_count stratified stability "
                "check. v1 결론 'KT 가 acrylic 수준 = 라벨 정제 가치 없음' 은 과감 — 본 v2 는 "
                "'우연히 쉬운 집단' vs '이미 다른 신호로 안정 학습됨' 구분."
            ),
            "production_routing": "warm = xgb_kf, cold = CB × cold_cell_factor (정합 KF OOF)",
            "kt_keywords_strong": STRONG_KT_KEYWORDS,
            "kt_keywords_silk_only": SILK_KEYWORDS,
            "kt_keywords_ambiguous": AMBIGUOUS_KT_KEYWORDS,
            "n_other_total": n_other,
            "n_strong_kt": n_strong,
            "n_silk_only": n_silk,
            "n_ambiguous_kt": n_ambig,
            "n_other_residual": n_other_res,
        },
        "raw_label_distribution_by_class": raw_top_by_class,
        "source_x_cohort_raw_count": source_x_cohort,
        "silk_only_qa": silk_qa,
        "cohort_residual_stats": cohorts_clean,
        "comparisons": comparisons,
        "strong_kt_stratified_stability": strong_strat,
        "interpretation_signal": (
            "코덱스 P0 R2 판정 기준: strong_kt 가 warm/cold × source × work_count 전 strata 에서 "
            "일관되게 acrylic 수준이면 → '이미 다른 신호로 안정 학습됨' (라벨 정제 즉시 우선순위 낮음). "
            "특정 strata (예: cold-only 또는 saatchi-only) 에서만 잘 맞으면 → '우연히 쉬운 집단' "
            "(라벨 정제 가치 남음). 완전 판정은 재학습 ablation 필요 — 본 진단은 비용 대비 좋은 사전 검증."
        ),
        "close_framing": (
            "v3.3-2 결론: 'korean_traditional 신설의 즉시 재학습 우선순위 낮다' 까지 (코덱스 권장). "
            "'라벨 정제 가치 없음' 까지 닫지 X. 향후 모델 재학습 사이클에서 strong_kt 라벨 추가는 "
            "low-cost low-risk 개선 candidate 로 유지."
        ),
    }

    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    logger.info("JSON 저장: %s", OUT_JSON)

    print("\n" + "=" * 100)
    print("v3.3-2 v2: 'other' medium / KT 3-tier + stratified stability check")
    print("=" * 100)
    print(
        f"\n'other' medium n={n_other}: strong KT={n_strong} / silk_only={n_silk} / "
        f"ambiguous={n_ambig} / 잔여={n_other_res}"
    )
    print("\nCohort residual stats:")
    print(f"  {'cohort':<22} {'n':>5} {'MdAPE':>9} {'median signed':>15} {'log_resid med':>15}")
    print("  " + "-" * 75)
    for label, c in cohorts_clean.items():
        if c.get("skipped"):
            continue
        print(
            f"  {label:<22} {c['n']:>5} {c['mdape_pct']:>8.2f}% "
            f"{c['median_signed_pct']:>+13.2f}% "
            f"{c['log_residual_summary']['median']:>+14.3f}"
        )

    print("\nMann-Whitney U comparisons (|log_resid|):")
    for name, comp in comparisons.items():
        keys = [k for k in comp if k.startswith("median_")]
        print(
            f"  {name}: p={comp['p_value']:.4f} | {keys[0]}={comp[keys[0]]:.3f} vs {keys[1]}={comp[keys[1]]:.3f}"
        )

    print("\nstrong_kt stratified stability (코덱스 P0 R2):")
    for stratum_name, stratum in strong_strat.items():
        print(f"  [{stratum_name}]")
        for sub_label, sub in stratum.items():
            if sub.get("skipped"):
                print(f"    {sub_label:<10}  (skipped, n=0)")
                continue
            print(
                f"    {sub_label:<10}  n={sub['n']:>4}  MdAPE={sub['mdape_pct']:>6.2f}%  "
                f"median_signed={sub['median_signed_pct']:>+7.2f}%"
            )
    print(f"\n저장: {OUT_JSON}")


if __name__ == "__main__":
    main()
