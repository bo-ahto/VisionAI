"""Stage 3 Warm-start 다중비교 보정 (Holm-Bonferroni) 재계산.

코덱스 권고:
- Phase 1 결과 다중비교 보정 후 신뢰구간 재산출
- Holm primary, Bonferroni 부록 sensitivity
- baseline 대비 5 모델 (fe_only / Combined / Combined-shrunk / + tier / + interaction) 비교
- 1-sided test (개선 방향)

방법:
- 각 비교의 cluster bootstrap n=2000 → 1-sided p-value 계산 (P(diff ≥ 0))
- Holm step-down: p-value 오름차순, α/(m-i+1) 와 비교
- Bonferroni: α/m 일괄
- 보정 후 q-value 보고
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import HuberRegressor

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent.parent
DATA = ROOT / "data" / "curated" / "stage3_1000x100.parquet"
RESULTS = Path(__file__).parent / "results"
WARM_THRESHOLD = 10
ALPHA = 0.05


def make_features(df):
    out = df.copy()
    out["log_area"] = np.log(out["area_cm2"].clip(lower=1))
    out["birth_year_centered"] = out["artist_birth_year"] - out["artist_birth_year"].mean()
    out["log_artist_total_works"] = np.log1p(out["artist_total_works"])
    out["log_price"] = np.log(out["price_krw"].clip(lower=1))
    out["interaction_area_works"] = out["log_area"] * out["log_artist_total_works"]
    return out


def restricted_cubic_spline(x, knots):
    last_k, pre_last_k = knots[-1], knots[-2]
    denom = (last_k - knots[0]) ** 2
    out = []
    for i in range(len(knots) - 2):
        ti = knots[i]
        cube = lambda u: np.maximum(u, 0) ** 3
        spline = (
            cube(x - ti)
            - cube(x - pre_last_k) * (last_k - ti) / (last_k - pre_last_k)
            + cube(x - last_k) * (pre_last_k - ti) / (last_k - pre_last_k)
        )
        out.append(spline / denom)
    return np.column_stack(out)


def build_X_baseline(df):
    knots = np.percentile(df["log_area"].values, [10, 50, 90])
    sp = restricted_cubic_spline(df["log_area"].values, knots)
    return pd.DataFrame({
        "const": 1.0,
        "log_area": df["log_area"].values,
        "birth_year_centered": df["birth_year_centered"].values,
        "log_artist_total_works": df["log_artist_total_works"].values,
        "log_area_spline": sp[:, 0],
    })


def add_artist_fe(X, df, warm_artists):
    X = X.copy()
    for a in warm_artists:
        X[f"artist_{a}"] = (df["artist_slug"] == a).astype(float).values
    return X


def add_gallery_tier(X, df):
    X = X.copy()
    for t in [3, 4]:
        X[f"tier_{t}"] = (df["gallery_tier"] == t).astype(float).values
    return X


def add_interaction_aw(X, df):
    X = X.copy()
    X["log_area_x_log_works"] = df["interaction_area_works"].values
    return X


def empirical_bayes_shrink(train_df):
    grand_mean = float(train_df["log_price"].mean())
    grouped = train_df.groupby("artist_slug")["log_price"]
    artist_means = grouped.mean()
    n_per = grouped.size()
    within_var = grouped.var().fillna(0.0)
    df_pool = (n_per - 1).clip(lower=0)
    sigma_w2 = float((within_var * df_pool).sum() / max(df_pool.sum(), 1.0))
    sigma_b2 = float(artist_means.var(ddof=1)) if len(artist_means) > 1 else 0.0
    shrunk = {}
    for a, n_a in n_per.items():
        m = float(artist_means[a])
        B = sigma_w2 / (sigma_w2 + n_a * sigma_b2) if sigma_b2 > 0 else 1.0
        shrunk[a] = (1 - B) * m + B * grand_mean
    return shrunk, grand_mean


def time_weights(years, max_year, half_life=2):
    age = max_year - years
    return 0.5 ** (age / half_life)


def fit_predict(Xtr, ytr, Xte, weights=None, eps=1.35):
    m = HuberRegressor(epsilon=eps, max_iter=2000, alpha=0.0001)
    if weights is not None:
        m.fit(Xtr[:, 1:], ytr, sample_weight=weights)
    else:
        m.fit(Xtr[:, 1:], ytr)
    return Xte[:, 1:] @ m.coef_ + m.intercept_


def mdape(yte_log, pred_log):
    return float(np.median(np.abs(np.exp(pred_log) - np.exp(yte_log)) / np.exp(yte_log)) * 100)


def cluster_bootstrap_diff(yte, pred_a, pred_b, test_artists, n_boot, seed):
    """1-sided p-value (P(diff >= 0)) + 95% CI for (mdape_a - mdape_b)."""
    rng = np.random.default_rng(seed)
    unique = list(set(test_artists))
    diffs = []
    for _ in range(n_boot):
        sample = rng.choice(unique, size=len(unique), replace=True)
        mask = np.isin(test_artists, sample)
        if mask.sum() < 3:
            continue
        diffs.append(mdape(yte[mask], pred_a[mask]) - mdape(yte[mask], pred_b[mask]))
    diffs = np.array(diffs)
    return {
        "n_boot_kept": int(len(diffs)),
        "mean": float(np.mean(diffs)),
        "ci_lo_95": float(np.percentile(diffs, 2.5)),
        "ci_hi_95": float(np.percentile(diffs, 97.5)),
        "p_value_1sided": float((diffs >= 0).mean()),  # H0: improvement 없음 (diff >= 0)
    }


def holm_adjust(pvals, alpha=0.05):
    """Holm step-down. Returns (sorted_pvals, thresholds, rejects)."""
    m = len(pvals)
    order = np.argsort(pvals)
    sorted_p = np.array(pvals)[order]
    thresholds = np.array([alpha / (m - i) for i in range(m)])
    rejects_sorted = np.zeros(m, dtype=bool)
    for i in range(m):
        if sorted_p[i] <= thresholds[i]:
            rejects_sorted[i] = True
        else:
            break  # step-down 중단
    rejects = np.zeros(m, dtype=bool)
    rejects[order] = rejects_sorted
    return rejects.tolist(), [float(x) for x in thresholds]


def bonferroni_threshold(m, alpha=0.05):
    return alpha / m


# ─────────────────────────────────────
# Main
# ─────────────────────────────────────
def run():
    df = pd.read_parquet(DATA)
    df_feat = make_features(df)
    y = df_feat["log_price"]

    train_mask = df_feat["year_made"] <= 2023
    test_mask = ~train_mask
    train_counts = Counter(df_feat[train_mask]["artist_slug"])
    warm_artists = {a for a, n in train_counts.items() if n >= WARM_THRESHOLD}
    warm_test_mask = test_mask & df_feat["artist_slug"].isin(warm_artists)
    train_df = df_feat[train_mask].copy()
    eb, gm = empirical_bayes_shrink(train_df)

    logger.info("=" * 80)
    logger.info("Stage 3 Warm Holm-Bonferroni 보정 재계산")
    logger.info("=" * 80)
    logger.info(f"Train: {train_mask.sum()} / Warm test: {warm_test_mask.sum()} / Warm artists: {len(warm_artists)}")

    # 6 model variants
    Xb = build_X_baseline(df_feat)
    X_fe = add_artist_fe(Xb, df_feat, warm_artists)
    X_tier = add_gallery_tier(Xb, df_feat)
    X_inter = add_interaction_aw(Xb, df_feat)

    artist_avg = train_df.groupby("artist_slug")["log_price"].mean().to_dict()
    history_simple = df_feat["artist_slug"].map(artist_avg).fillna(gm).values
    history_shrunk = df_feat["artist_slug"].map(eb).fillna(gm).values

    X_combined = X_fe.copy()
    X_combined["recent_avg_log_price"] = history_simple
    X_combined_shrunk = X_fe.copy()
    X_combined_shrunk["recent_avg_log_price"] = history_shrunk

    ytr = y[train_mask].values.astype(float)
    yte = y[warm_test_mask].values.astype(float)
    test_artists = df_feat[warm_test_mask]["artist_slug"].values
    max_yr = df_feat["year_made"].max()
    weights = time_weights(df_feat[train_mask]["year_made"].values, max_yr, half_life=2)

    # Predictions
    def fit(X, w=None):
        Xtr = X[train_mask.values].values.astype(float)
        Xte = X[warm_test_mask.values].values.astype(float)
        return fit_predict(Xtr, ytr, Xte, weights=w)

    pred_baseline = fit(Xb)
    pred_fe = fit(X_fe)
    pred_tier = fit(X_tier)
    pred_inter = fit(X_inter)
    pred_combined = fit(X_combined, w=weights)
    pred_combined_shrunk = fit(X_combined_shrunk, w=weights)

    base_mdape = mdape(yte, pred_baseline)
    logger.info(f"\nBaseline MdAPE: {base_mdape:.2f}%\n")

    # 5 candidate models (1-sided test, H0: improvement 없음)
    candidates = [
        ("fe_only", pred_fe),
        ("combined", pred_combined),
        ("combined_shrunk", pred_combined_shrunk),
        ("tier", pred_tier),
        ("interaction", pred_inter),
    ]

    boots = []
    for name, pred in candidates:
        # diff = candidate - baseline (negative = improvement)
        b = cluster_bootstrap_diff(yte, pred, pred_baseline, test_artists, n_boot=2000, seed=42)
        b["name"] = name
        b["candidate_mdape"] = mdape(yte, pred)
        boots.append(b)
        logger.info(
            f"  {name:>16}: MdAPE {b['candidate_mdape']:>5.2f}% "
            f"(diff {b['mean']:+5.2f}%p), CI [{b['ci_lo_95']:+6.2f}, {b['ci_hi_95']:+6.2f}], "
            f"raw 1-sided p = {b['p_value_1sided']:.4f}"
        )

    # Multi-comparison correction
    pvals = [b["p_value_1sided"] for b in boots]
    holm_rejects, holm_thresholds = holm_adjust(pvals, alpha=ALPHA)
    bonf_thr = bonferroni_threshold(len(pvals), alpha=ALPHA)
    bonf_rejects = [p <= bonf_thr for p in pvals]

    logger.info(f"\n--- 다중비교 보정 (m={len(pvals)}, α=0.05, 1-sided) ---")
    logger.info(f"  Bonferroni threshold (α/m): {bonf_thr:.4f}")
    logger.info(f"  Holm thresholds (sorted): {[f'{t:.4f}' for t in holm_thresholds]}")

    logger.info(f"\n  {'name':>16} {'p_raw':>8} {'p<0.05?':>9} {'Holm reject?':>14} {'Bonf reject?':>14}")
    for b, hr, br in zip(boots, holm_rejects, bonf_rejects):
        logger.info(
            f"  {b['name']:>16} {b['p_value_1sided']:>8.4f} "
            f"{'YES' if b['p_value_1sided'] < 0.05 else 'no':>9} "
            f"{'YES' if hr else 'no':>14} "
            f"{'YES' if br else 'no':>14}"
        )

    # 결론
    logger.info(f"\n--- 결론 ---")
    fe_b = boots[0]
    logger.info(
        f"Primary (FE only vs baseline 단일 비교): raw p = {fe_b['p_value_1sided']:.4f}, "
        f"{'유의' if fe_b['p_value_1sided'] < 0.05 else '비유의'} (단일 비교 기준)"
    )
    logger.info(
        f"Multi-comparison (m=5): Holm 후 reject 모델 = "
        f"{[b['name'] for b, r in zip(boots, holm_rejects) if r] or '없음'}"
    )
    logger.info(
        f"                       Bonferroni 후 reject 모델 = "
        f"{[b['name'] for b, r in zip(boots, bonf_rejects) if r] or '없음'}"
    )

    summary = {
        "baseline_mdape": base_mdape,
        "n_test": int(warm_test_mask.sum()),
        "n_artists": int(len(set(test_artists))),
        "alpha": ALPHA,
        "m_comparisons": len(pvals),
        "bonferroni_threshold": bonf_thr,
        "holm_thresholds_sorted": holm_thresholds,
        "candidates": [
            {**b, "holm_reject": hr, "bonferroni_reject": br}
            for b, hr, br in zip(boots, holm_rejects, bonf_rejects)
        ],
    }
    out = RESULTS / "stage3_warm_holm_adjusted.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(f"\nSaved: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    run()
