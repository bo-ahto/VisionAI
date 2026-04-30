"""v3 Group 1.3: 출처 플립 통제 실험의 통계 검정.

source_flip_results_warm.json (warm 30명 통제 실험 결과)에 paired statistical
test를 적용해 출처 라벨 효과의 통계적 유의성·효과 크기·신뢰 구간을 산출한다.

검정:
- Wilcoxon signed-rank test (비정규 분포 대응)
- Paired t-test (정규성 가정 시)
- Cohen's d_z (paired 효과 크기)
- 95% CI (bootstrap on differences)

산출물:
    model_test_results/v3_diagnostics/source_flip_stats.json

Usage:
    python3 scripts/v3_source_flip_stats.py
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
from scipy import stats

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
RESULTS_PATH = ROOT / "model_test_results" / "source_flip_results_warm.json"
OUT_PATH = ROOT / "model_test_results" / "v3_diagnostics" / "source_flip_stats.json"
N_BOOTSTRAP = 10_000
RNG_SEED = 42


def cohens_dz(differences: np.ndarray) -> float:
    """Paired Cohen's d_z = mean(diff) / std(diff, ddof=1).

    Lakens (2013): https://doi.org/10.3389/fpsyg.2013.00863
    """
    sd = np.std(differences, ddof=1)
    if sd == 0:
        return 0.0
    return float(np.mean(differences) / sd)


def bootstrap_ci_mean(values: np.ndarray, n_iter: int = N_BOOTSTRAP, alpha: float = 0.05) -> dict:
    rng = np.random.default_rng(RNG_SEED)
    n = len(values)
    means = np.array([
        rng.choice(values, size=n, replace=True).mean()
        for _ in range(n_iter)
    ])
    return {
        "mean": float(np.mean(values)),
        "ci_low": float(np.percentile(means, 100 * alpha / 2)),
        "ci_high": float(np.percentile(means, 100 * (1 - alpha / 2))),
        "n_bootstrap": n_iter,
    }


def bootstrap_ci_median(values: np.ndarray, n_iter: int = N_BOOTSTRAP, alpha: float = 0.05) -> dict:
    rng = np.random.default_rng(RNG_SEED)
    n = len(values)
    meds = np.array([
        np.median(rng.choice(values, size=n, replace=True))
        for _ in range(n_iter)
    ])
    return {
        "median": float(np.median(values)),
        "ci_low": float(np.percentile(meds, 100 * alpha / 2)),
        "ci_high": float(np.percentile(meds, 100 * (1 - alpha / 2))),
        "n_bootstrap": n_iter,
    }


def analyze_cohort(rows: list[dict], cohort_name: str) -> dict:
    """코호트 단위 통계 검정.

    각 작품에 대해 paired observation: (price_artsy, price_saatchi). 검정은
    log-ratio (= log(price_saatchi / price_artsy)) 위에서 진행하여 가격대 차이를
    정규화 (가격이 right-skewed라 직접 차이는 부적절).
    """
    p_artsy = np.array([r["price_krw_artsy"] for r in rows], dtype=float)
    p_saatchi = np.array([r["price_krw_saatchi"] for r in rows], dtype=float)

    # log-ratio (= ln(saatchi) - ln(artsy)); paired difference
    log_ratio = np.log(p_saatchi) - np.log(p_artsy)
    delta_pct = np.array([r["delta_pct"] for r in rows], dtype=float)

    # Wilcoxon signed-rank (비정규 대응). zero-method='wilcox': 0 차이 제외
    try:
        wilcoxon_stat, wilcoxon_p = stats.wilcoxon(
            log_ratio, alternative="two-sided", zero_method="wilcox",
        )
    except ValueError:
        # 모든 차이가 0이면 wilcoxon 미정의
        wilcoxon_stat, wilcoxon_p = float("nan"), 1.0

    # Paired t-test (정규성 가정)
    t_stat, t_p = stats.ttest_rel(np.log(p_saatchi), np.log(p_artsy))

    # Cohen's d_z (paired)
    d_z = cohens_dz(log_ratio)

    # Shapiro-Wilk normality test (warning용)
    if len(log_ratio) >= 3:
        shapiro_stat, shapiro_p = stats.shapiro(log_ratio)
    else:
        shapiro_stat, shapiro_p = float("nan"), 1.0

    # Bootstrap CI for mean log-ratio + mean delta_pct
    log_ratio_ci = bootstrap_ci_mean(log_ratio)
    delta_pct_ci = bootstrap_ci_mean(delta_pct)
    delta_pct_median_ci = bootstrap_ci_median(delta_pct)

    return {
        "cohort": cohort_name,
        "n": len(rows),
        "delta_pct": {
            "mean": float(np.mean(delta_pct)),
            "median": float(np.median(delta_pct)),
            "std": float(np.std(delta_pct, ddof=1)),
            "min": float(np.min(delta_pct)),
            "max": float(np.max(delta_pct)),
            "mean_95ci": [delta_pct_ci["ci_low"], delta_pct_ci["ci_high"]],
            "median_95ci": [delta_pct_median_ci["ci_low"], delta_pct_median_ci["ci_high"]],
        },
        "log_ratio": {
            "mean": float(np.mean(log_ratio)),
            "median": float(np.median(log_ratio)),
            "std": float(np.std(log_ratio, ddof=1)),
            "mean_95ci": [log_ratio_ci["ci_low"], log_ratio_ci["ci_high"]],
        },
        "wilcoxon_signed_rank": {
            "statistic": float(wilcoxon_stat),
            "p_value": float(wilcoxon_p),
            "significant_at_0.05": bool(wilcoxon_p < 0.05),
        },
        "paired_t_test": {
            "statistic": float(t_stat),
            "p_value": float(t_p),
            "significant_at_0.05": bool(t_p < 0.05),
        },
        "cohens_dz": {
            "value": d_z,
            "interpretation": (
                "negligible (|d|<0.2)" if abs(d_z) < 0.2 else
                "small (0.2≤|d|<0.5)" if abs(d_z) < 0.5 else
                "medium (0.5≤|d|<0.8)" if abs(d_z) < 0.8 else
                "large (|d|≥0.8)"
            ),
        },
        "shapiro_normality": {
            "statistic": float(shapiro_stat),
            "p_value": float(shapiro_p),
            "is_normal_at_0.05": bool(shapiro_p >= 0.05),
        },
    }


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with RESULTS_PATH.open(encoding="utf-8") as f:
        data = json.load(f)

    results = data["results"]
    output = {
        "config": {
            "test_design": "paired observation per artwork (artsy vs saatchi prediction)",
            "test_unit": "log-price ratio (= ln(price_saatchi) - ln(price_artsy))",
            "n_bootstrap": N_BOOTSTRAP,
            "rng_seed": RNG_SEED,
        },
        "per_cohort": {},
        "pooled": None,
    }

    cohort_titles = {
        "both": "Cohort A — 양쪽 학습 (Artsy ∩ Saatchi warm)",
        "artsy_only": "Cohort B — Artsy만 warm",
        "saatchi_only": "Cohort C — Saatchi만 warm",
    }

    all_rows = []
    for k, rows in results.items():
        title = cohort_titles.get(k, k)
        logger.info("Analyzing cohort: %s (n=%d)", title, len(rows))
        output["per_cohort"][k] = analyze_cohort(rows, title)
        all_rows.extend(rows)

    # Pooled analysis (전체 30명)
    logger.info("Analyzing pooled (n=%d)", len(all_rows))
    output["pooled"] = analyze_cohort(all_rows, "Pooled (warm 30명 전체)")

    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=str)

    # Console summary
    print("\n=== Source Flip Statistical Test Summary (warm n=30) ===\n")
    print(f"{'Cohort':<36} {'n':>3} {'Δ% mean':>10} {'95% CI':>22} {'Wilcoxon p':>12} {'Cohen d_z':>10}")
    print("-" * 100)
    for k in ["both", "artsy_only", "saatchi_only"]:
        c = output["per_cohort"][k]
        ci = c["delta_pct"]["mean_95ci"]
        print(f"{cohort_titles[k]:<36} {c['n']:>3} "
              f"{c['delta_pct']['mean']:>+9.3f}% [{ci[0]:>+6.3f}, {ci[1]:>+6.3f}] "
              f"{c['wilcoxon_signed_rank']['p_value']:>11.4f} "
              f"{c['cohens_dz']['value']:>+10.3f}")
    p = output["pooled"]
    ci = p["delta_pct"]["mean_95ci"]
    print("-" * 100)
    print(f"{'Pooled (warm 30명 전체)':<36} {p['n']:>3} "
          f"{p['delta_pct']['mean']:>+9.3f}% [{ci[0]:>+6.3f}, {ci[1]:>+6.3f}] "
          f"{p['wilcoxon_signed_rank']['p_value']:>11.4f} "
          f"{p['cohens_dz']['value']:>+10.3f}")
    print(f"\n저장: {OUT_PATH}")


if __name__ == "__main__":
    main()
