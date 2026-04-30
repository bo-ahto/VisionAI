"""v3.3-1: warm saatchi_online 고가 segment residual 진단 (warm KF OOF 정합).

배경 (v3.2-4 새 finding + 코덱스 v3.3-1 P0 fix):
- v3.2-4 / v3.3-1 v1 은 warm 행에 cold-protocol GroupKFold OOF (xgb_preds_gkf_ln) 를
  적용하는 평가 프로토콜 버그가 있었음 → catastrophic over-prediction 결론은 artifact.
- 본 v3.3-1 v2: warm slice KFold OOF (xgb_preds_kf_ln) 정합, production warm path 와 일치.
- warm cohort 의 진짜 residual 분포 / asymmetry / 가격대별 breakdown / 작가 work_count.

방법:
1. warm slice OOF 사용: y_warm_actual_ln, xgb_preds_kf_ln, groups_warm, source_warm
2. df 도 wmask 인덱스 정합 (df_warm = df[wmask].reset_index)
3. cohort: source==saatchi & target_market==online & xgb_pred ≥ 13.7M
4. residual 분포 / asymmetry / 가격대별 stratification
5. row-level KFold conformal (코덱스 R4: warm task 는 known-artist 시나리오라 GroupKFold 부적합)
6. (참고) GroupKFold-by-artist conformal 은 "artist-held-out stress test" 로 별도 라벨

산출물:
    model_test_results/v3_diagnostics/warm_saatchi_high_diag.json

Usage:
    PYTHONPATH=src python3 scripts/v33_warm_saatchi_high_diag.py
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
from sklearn.model_selection import GroupKFold, KFold

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from train_primary_market_v3_filtered import _warm_mask, load_data, prepare_features

from visionai.price_engine._eval_helpers import derive_target_market

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUT_DIR = ROOT / "model_test_results"
DIAG_DIR = OUT_DIR / "v3_diagnostics"
OOF_PATH = DIAG_DIR / "oof_predictions.npz"
OUT_JSON = DIAG_DIR / "warm_saatchi_high_diag.json"

THRESHOLD_KRW = 13_728_873
ALPHA = 0.10
N_SPLITS = 5
RNG_SEED = 42


def quantile_summary(arr: np.ndarray) -> dict:
    if len(arr) == 0:
        return {"n": 0}
    return {
        "n": len(arr),
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "p5": float(np.percentile(arr, 5)),
        "p10": float(np.percentile(arr, 10)),
        "p25": float(np.percentile(arr, 25)),
        "median": float(np.median(arr)),
        "p75": float(np.percentile(arr, 75)),
        "p90": float(np.percentile(arr, 90)),
        "p95": float(np.percentile(arr, 95)),
    }


def asymmetry_metrics(residuals_log: np.ndarray) -> dict:
    if len(residuals_log) == 0:
        return {}
    abs_p10 = float(abs(np.percentile(residuals_log, 10)))
    abs_p90 = float(abs(np.percentile(residuals_log, 90)))
    abs_p5 = float(abs(np.percentile(residuals_log, 5)))
    abs_p95 = float(abs(np.percentile(residuals_log, 95)))
    median = float(np.median(residuals_log))
    mean = float(np.mean(residuals_log))
    std = float(np.std(residuals_log))
    pearson_skew = 3.0 * (mean - median) / std if std > 0 else 0.0
    return {
        "median_log_residual": median,
        "mean_log_residual": mean,
        "pearson_skew": pearson_skew,
        "abs_p10": abs_p10,
        "abs_p90": abs_p90,
        "abs_p5": abs_p5,
        "abs_p95": abs_p95,
        "ratio_p90_over_abs_p10": (abs_p90 / abs_p10) if abs_p10 > 0 else float("inf"),
        "ratio_p95_over_abs_p5": (abs_p95 / abs_p5) if abs_p5 > 0 else float("inf"),
        "interpretation": (
            "log_residual = ln(actual/pred). 음수=over-prediction (model > actual). "
            "ratio_p90_over_abs_p10 > 1 = upper-tail (under-prediction) 이 더 길다는 신호. "
            "< 1 = lower-tail (over-prediction) 이 더 길다는 신호."
        ),
    }


def conformal_kfold_row_level(
    residuals_log: np.ndarray,
    alpha: float = ALPHA,
    n_splits: int = N_SPLITS,
    rng_seed: int = RNG_SEED,
) -> dict:
    """Row-level KFold split conformal (warm known-artist 시나리오 정합)."""
    n = len(residuals_log)
    if n < 30:
        return {"skipped": True, "reason": f"n={n} < 30"}
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=rng_seed)
    fold_q = []
    contains = np.zeros(n, dtype=bool)
    for fold_i, (cal_idx, test_idx) in enumerate(kf.split(np.arange(n))):
        r_cal = residuals_log[cal_idx]
        if len(r_cal) < 10:
            fold_q.append({"fold": fold_i, "n_cal": len(r_cal), "skipped": True})
            continue
        q_low = float(np.quantile(r_cal, alpha / 2))
        q_median = float(np.quantile(r_cal, 0.5))
        q_high = float(np.quantile(r_cal, 1 - alpha / 2))
        fold_q.append(
            {
                "fold": fold_i,
                "n_cal": len(r_cal),
                "n_test": len(test_idx),
                "q_low": q_low,
                "q_median": q_median,
                "q_high": q_high,
            }
        )
        r_test = residuals_log[test_idx]
        contains[test_idx] = (r_test >= q_low) & (r_test <= q_high)

    valid = [f for f in fold_q if not f.get("skipped")]
    if not valid:
        return {"skipped": True, "reason": "no valid fold"}
    q_low_med = float(np.median([f["q_low"] for f in valid]))
    q_median_med = float(np.median([f["q_median"] for f in valid]))
    q_high_med = float(np.median([f["q_high"] for f in valid]))
    return {
        "method": "row-level KFold (warm known-artist 시나리오 정합)",
        "n": n,
        "n_splits": n_splits,
        "alpha": alpha,
        "rng_seed": rng_seed,
        "fold_quantiles": fold_q,
        "median_q_low_log": q_low_med,
        "median_q_median_log": q_median_med,
        "median_q_high_log": q_high_med,
        "low_factor": float(np.exp(q_low_med)),
        "median_factor": float(np.exp(q_median_med)),
        "high_factor": float(np.exp(q_high_med)),
        "interval_width_relative": float(np.exp(q_high_med) - np.exp(q_low_med)),
        "empirical_coverage_pct": float(contains.mean() * 100),
    }


def conformal_groupkfold_stress(
    residuals_log: np.ndarray,
    groups: np.ndarray,
    alpha: float = ALPHA,
    n_splits: int = N_SPLITS,
) -> dict:
    """GroupKFold conformal — artist-held-out stress test 라벨 (warm serving 평가 X)."""
    n = len(residuals_log)
    if n < 30 or len(np.unique(groups)) < n_splits:
        return {"skipped": True, "reason": f"n={n} or unique groups < {n_splits}"}
    gkf = GroupKFold(n_splits=n_splits)
    contains = np.zeros(n, dtype=bool)
    fold_q = []
    for fold_i, (cal_idx, test_idx) in enumerate(gkf.split(residuals_log, groups=groups)):
        r_cal = residuals_log[cal_idx]
        if len(r_cal) < 10:
            fold_q.append({"fold": fold_i, "n_cal": len(r_cal), "skipped": True})
            continue
        q_low = float(np.quantile(r_cal, alpha / 2))
        q_high = float(np.quantile(r_cal, 1 - alpha / 2))
        fold_q.append(
            {
                "fold": fold_i,
                "n_cal": len(r_cal),
                "n_test": len(test_idx),
                "q_low": q_low,
                "q_high": q_high,
            }
        )
        r_test = residuals_log[test_idx]
        contains[test_idx] = (r_test >= q_low) & (r_test <= q_high)
    valid = [f for f in fold_q if not f.get("skipped")]
    if not valid:
        return {"skipped": True, "reason": "no valid fold"}
    q_low_med = float(np.median([f["q_low"] for f in valid]))
    q_high_med = float(np.median([f["q_high"] for f in valid]))
    return {
        "method": "GroupKFold by artist — artist-held-out stress test (warm serving 평가 X)",
        "n": n,
        "n_splits": n_splits,
        "alpha": alpha,
        "fold_quantiles": fold_q,
        "median_q_low_log": q_low_med,
        "median_q_high_log": q_high_med,
        "low_factor": float(np.exp(q_low_med)),
        "high_factor": float(np.exp(q_high_med)),
        "interval_width_relative": float(np.exp(q_high_med) - np.exp(q_low_med)),
        "empirical_coverage_pct": float(contains.mean() * 100),
        "interpretation": (
            "이 cohort 의 같은 작가가 학습에서 통째로 빠지면 어떻게 되는지 측정 — "
            "warm production 라우팅의 known-artist 정합 평가가 아님. coverage 실패가 "
            "warm conformal 자체의 결함을 의미하지 않음."
        ),
    }


def stratified_breakdown(
    y_actual_price: np.ndarray,
    pred_price: np.ndarray,
    bands: list[tuple[float, float, str]],
) -> list[dict]:
    out = []
    for low, high, label in bands:
        mask = (pred_price >= low) & (pred_price < high)
        n = int(mask.sum())
        if n == 0:
            out.append({"band": label, "n": 0, "skipped": True})
            continue
        residuals_log = np.log(y_actual_price[mask] / pred_price[mask])
        signed_pct = (y_actual_price[mask] - pred_price[mask]) / pred_price[mask] * 100
        out.append(
            {
                "band": label,
                "n": n,
                "log_residual": quantile_summary(residuals_log),
                "signed_pct_error": quantile_summary(signed_pct),
                "mdape": float(np.median(np.abs(signed_pct))),
            }
        )
    return out


def main() -> None:
    DIAG_DIR.mkdir(parents=True, exist_ok=True)
    oof = np.load(OOF_PATH, allow_pickle=True)
    y_warm_ln = oof["y_warm_actual_ln"]
    xgb_kf_ln = oof["xgb_preds_kf_ln"]
    groups_warm = oof["groups_warm"]
    source_warm = np.array([str(s) for s in oof["source_warm"]])

    # df 정합: wmask 적용 후 reset_index 하여 OOF warm slice 와 정합
    df = load_data()
    df = df[df.get("is_excluded_for_training", 0) != 1].reset_index(drop=True)
    _, y_check, groups_full = prepare_features(df)
    wmask_full = _warm_mask(groups_full)
    df_warm = df.loc[wmask_full].reset_index(drop=True)
    np.testing.assert_allclose(y_check[wmask_full], y_warm_ln, rtol=1e-10)

    target_market_warm = derive_target_market(df_warm["is_krw"])
    has_birth_year_warm = df_warm["has_birth_year"].astype(bool).to_numpy()

    y_warm_price = np.exp(y_warm_ln)
    xgb_kf_price = np.exp(xgb_kf_ln)

    # cohort: warm slice OOF 위에서 saatchi + online + xgb_kf_pred ≥ 13.7M
    cohort_mask = (
        (source_warm == "saatchi")
        & (target_market_warm == "online")
        & (xgb_kf_price >= THRESHOLD_KRW)
    )
    n_cohort = int(cohort_mask.sum())
    logger.info("warm_saatchi_high cohort (KF OOF 정합) n=%d", n_cohort)

    y_co = y_warm_price[cohort_mask]
    pred_co = xgb_kf_price[cohort_mask]
    artists_co = groups_warm[cohort_mask]
    residuals_log = np.log(y_co / pred_co)
    signed_pct = (y_co - pred_co) / pred_co * 100

    log_resid_summary = quantile_summary(residuals_log)
    asym = asymmetry_metrics(residuals_log)
    signed_pct_summary = quantile_summary(signed_pct)
    mdape = float(np.median(np.abs(signed_pct)))
    logger.info(
        "warm_saatchi_high (KF) log_residual median=%.3f / p10=%.3f / p90=%.3f / MdAPE=%.2f%%",
        log_resid_summary["median"],
        log_resid_summary["p10"],
        log_resid_summary["p90"],
        mdape,
    )

    # row-level KFold conformal (warm 정합)
    warm_conformal_row = conformal_kfold_row_level(residuals_log, ALPHA, N_SPLITS, RNG_SEED)
    if not warm_conformal_row.get("skipped"):
        logger.info(
            "warm row-level conformal: low=%.3f / high=%.3f / width=%.2f / coverage=%.1f%%",
            warm_conformal_row["low_factor"],
            warm_conformal_row["high_factor"],
            warm_conformal_row["interval_width_relative"],
            warm_conformal_row["empirical_coverage_pct"],
        )

    # GroupKFold conformal — stress test 라벨
    stress_conformal = conformal_groupkfold_stress(residuals_log, artists_co, ALPHA, N_SPLITS)
    if not stress_conformal.get("skipped"):
        logger.info(
            "stress (artist-held-out) conformal: coverage=%.1f%% (참고용 — warm 평가 아님)",
            stress_conformal["empirical_coverage_pct"],
        )

    # 가격대별 stratification
    bands = [
        (THRESHOLD_KRW, 30_000_000, "13.7M~30M"),
        (30_000_000, 60_000_000, "30M~60M"),
        (60_000_000, float("inf"), "60M+"),
    ]
    strat = stratified_breakdown(y_co, pred_co, bands)
    for s in strat:
        if s.get("skipped"):
            continue
        logger.info(
            "  [%s] n=%d / median log_resid=%+.3f / MdAPE=%.2f%%",
            s["band"],
            s["n"],
            s["log_residual"]["median"],
            s["mdape"],
        )

    # 작가별 work_count + saatchi-only ratio
    artist_counts_all = df.groupby("artist_slug").size().to_dict()
    cohort_artists = np.unique(artists_co)
    cohort_artist_counts = np.array([artist_counts_all[a] for a in cohort_artists])
    artist_count_summary = quantile_summary(cohort_artist_counts)

    artist_source_breakdown = []
    for a in cohort_artists:
        rows = df[df["artist_slug"] == a]
        n_saatchi = int((rows["source"].astype(str) == "saatchi").sum())
        n_artsy = int((rows["source"].astype(str) == "artsy").sum())
        artist_source_breakdown.append(
            {
                "artist_slug": str(a),
                "n_total": n_saatchi + n_artsy,
                "n_saatchi": n_saatchi,
                "n_artsy": n_artsy,
                "saatchi_ratio": n_saatchi / (n_saatchi + n_artsy)
                if (n_saatchi + n_artsy) > 0
                else None,
            }
        )
    saatchi_only_artists = sum(1 for x in artist_source_breakdown if x["n_artsy"] == 0)
    n_unique_artists = len(cohort_artists)
    logger.info(
        "cohort 작가: %d unique / saatchi-only %d (%.1f%%) / row count median=%.0f, p90=%.0f",
        n_unique_artists,
        saatchi_only_artists,
        saatchi_only_artists / n_unique_artists * 100 if n_unique_artists > 0 else 0,
        artist_count_summary.get("median", 0),
        artist_count_summary.get("p90", 0),
    )

    summary = {
        "config": {
            "scope": (
                "v3.3-1 v2 (코덱스 P0 fix): warm slice KFold OOF (xgb_preds_kf_ln) 정합. "
                "cohort = warm + saatchi + online + xgb_kf_pred ≥ 13.7M. "
                "row-level KFold conformal (warm known-artist 시나리오) + "
                "GroupKFold stress test 별도 보고."
            ),
            "cohort_definition": (
                "warm slice (KF OOF 위) & source==saatchi & target_market==online & "
                "xgb_kf_price >= 13,728,873 KRW"
            ),
            "n_cohort": n_cohort,
            "n_unique_artists": n_unique_artists,
            "alpha": ALPHA,
            "n_splits": N_SPLITS,
            "rng_seed": RNG_SEED,
            "v1_bug_note": (
                "v3.3-1 v1 + v3.2-4 v1 은 warm 행에 cold-protocol GroupKFold OOF "
                "(xgb_preds_gkf_ln, 작가 통째 홀드아웃) 를 적용한 평가 프로토콜 버그가 있었음. "
                "이 catastrophic over-prediction 결론 (median log_resid=-2.272, MdAPE 90.9%) 은 "
                "GKF artifact — 실제 warm path 정합 (KF) 결과는 정상. 본 v2 가 정답."
            ),
        },
        "residual_distribution": {
            "log_residual": log_resid_summary,
            "signed_pct_error": signed_pct_summary,
            "mdape_pct": mdape,
            "asymmetry": asym,
        },
        "warm_conformal_row_level": warm_conformal_row,
        "stress_conformal_groupkfold": stress_conformal,
        "stratified_breakdown_by_pred_price": strat,
        "cohort_artist_distribution": {
            "n_unique_artists": n_unique_artists,
            "saatchi_only_artists": saatchi_only_artists,
            "saatchi_only_ratio": saatchi_only_artists / n_unique_artists
            if n_unique_artists > 0
            else None,
            "row_count_per_artist": artist_count_summary,
        },
        "v33_priority_signal": (
            "본 v2 결과를 토대로 v3.3 우선순위 재평가: "
            "warm saatchi 고가 segment 가 KF 정합 기준 정상이면 v3.3 우선순위는 cold D10 + "
            "feature/data 개선 으로 회귀. asymmetry / band cliff 는 GKF artifact 였으며, "
            "v3.0 보고서 §8.4 정정 필요."
        ),
        "extras": {
            "has_birth_year_ratio_in_cohort": float(has_birth_year_warm[cohort_mask].mean()),
        },
    }

    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    logger.info("JSON 저장: %s", OUT_JSON)

    print("\n" + "=" * 100)
    print("v3.3-1 v2: warm saatchi_online 고가 residual 진단 (KF OOF 정합)")
    print("=" * 100)
    print(f"\nCohort: warm slice + saatchi + online + xgb_kf_pred ≥ {THRESHOLD_KRW:,} KRW")
    print(f"  n={n_cohort} rows / {n_unique_artists} unique artists")
    print(
        f"  saatchi-only artists: {saatchi_only_artists} "
        f"({saatchi_only_artists / n_unique_artists * 100:.1f}%)"
    )
    print(
        f"\nResidual: median ln_resid={log_resid_summary['median']:+.3f} / "
        f"p10={log_resid_summary['p10']:+.3f} / p90={log_resid_summary['p90']:+.3f} / "
        f"MdAPE={mdape:.2f}%"
    )
    print(
        f"Asymmetry: skew={asym['pearson_skew']:+.3f} / "
        f"|p10|={asym['abs_p10']:.3f} vs p90={asym['abs_p90']:.3f} / "
        f"ratio={asym['ratio_p90_over_abs_p10']:.2f}"
    )
    if not warm_conformal_row.get("skipped"):
        print(
            f"\nwarm row-level conformal: [{warm_conformal_row['low_factor']:.3f}, "
            f"{warm_conformal_row['high_factor']:.3f}] / "
            f"width={warm_conformal_row['interval_width_relative']:.2f} / "
            f"empirical coverage={warm_conformal_row['empirical_coverage_pct']:.1f}%"
        )
    if not stress_conformal.get("skipped"):
        print(
            f"stress (artist-held-out) conformal: "
            f"coverage={stress_conformal['empirical_coverage_pct']:.1f}% (참고)"
        )
    print("\nStratified by pred price band:")
    for s in strat:
        if s.get("skipped"):
            continue
        print(
            f"  {s['band']:>15} n={s['n']:>5} / median log_resid={s['log_residual']['median']:>+.3f} "
            f"/ MdAPE={s['mdape']:>6.2f}%"
        )
    print(f"\n저장: {OUT_JSON}")


if __name__ == "__main__":
    main()
