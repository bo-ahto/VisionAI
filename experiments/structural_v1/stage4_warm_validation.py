"""Stage 4 Warm Path 확장 검증 — 사전등록 적용 (`docs/stage4_확장검증계획_20260507.md` §6.0).

Primary: FE only vs baseline 단일 비교 (1-sided 95% CI cluster bootstrap, unadjusted)
Secondary (Holm m=5 별도 family):
  - Combined vs baseline
  - Combined-shrunk vs baseline
  - FE only @ depth bin 10-14 / 15-24 / 25+ vs baseline

Composition-shift + Segment harm budget 동시 산출.
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
DATA = ROOT / "data" / "curated" / "stage4_full.parquet"
RESULTS = Path(__file__).parent / "results"
N_BOOT_PRIMARY = 2000
N_BOOT_SECONDARY = 1000
N_SEEDS_STABILITY = 10

# Stage 3 (1378/100) 작가 set (composition-shift 비교용)
STAGE3_PATH = ROOT / "data" / "curated" / "stage3_1000x100.parquet"


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
    fe_cols = {f"artist_{a}": (df["artist_slug"] == a).astype(float).values for a in warm_artists}
    return pd.concat([X, pd.DataFrame(fe_cols, index=X.index)], axis=1)


def empirical_bayes_shrink(train_df):
    grand = float(train_df["log_price"].mean())
    grouped = train_df.groupby("artist_slug")["log_price"]
    means = grouped.mean()
    n_per = grouped.size()
    within = grouped.var().fillna(0.0)
    sigma_w2 = float((within * (n_per - 1).clip(lower=0)).sum() / max((n_per - 1).clip(lower=0).sum(), 1.0))
    sigma_b2 = float(means.var(ddof=1)) if len(means) > 1 else 0.0
    shrunk = {}
    for a, n_a in n_per.items():
        m = float(means[a])
        B = sigma_w2 / (sigma_w2 + n_a * sigma_b2) if sigma_b2 > 0 else 1.0
        shrunk[a] = (1 - B) * m + B * grand
    return shrunk, grand


def time_weights(years, max_year, half_life=2):
    return 0.5 ** ((max_year - years) / half_life)


def fit_huber(Xtr, ytr, Xte, weights=None, eps=1.35, alpha=0.0001):
    m = HuberRegressor(epsilon=eps, alpha=alpha, max_iter=2000)
    if weights is not None:
        m.fit(Xtr[:, 1:], ytr, sample_weight=weights)
    else:
        m.fit(Xtr[:, 1:], ytr)
    return Xte[:, 1:] @ m.coef_ + m.intercept_


def mdape(y, pred):
    return float(np.median(np.abs(np.exp(pred) - np.exp(y)) / np.exp(y)) * 100)


def cluster_bootstrap_diff(yte, pred_a, pred_b, test_artists, n_boot, seed=42):
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
        "p_value_1sided": float((diffs >= 0).mean()),
    }


def holm_adjust(pvals, alpha=0.05):
    m = len(pvals)
    order = np.argsort(pvals)
    sorted_p = np.array(pvals)[order]
    rejects_sorted = np.zeros(m, dtype=bool)
    for i in range(m):
        threshold = alpha / (m - i)
        if sorted_p[i] <= threshold:
            rejects_sorted[i] = True
        else:
            break
    rejects = np.zeros(m, dtype=bool)
    rejects[order] = rejects_sorted
    return rejects.tolist()


# ─────────────────────────────────────
# 모델 fit 함수들
# ─────────────────────────────────────
def fit_baseline(df, train_mask, test_mask, y):
    X = build_X_baseline(df)
    Xtr = X[train_mask].values.astype(float)
    Xte = X[test_mask].values.astype(float)
    return fit_huber(Xtr, y[train_mask].values.astype(float), Xte)


def fit_fe_only(df, train_mask, test_mask, y, warm_artists):
    Xb = build_X_baseline(df)
    X = add_artist_fe(Xb, df, warm_artists)
    Xtr = X[train_mask].values.astype(float)
    Xte = X[test_mask].values.astype(float)
    return fit_huber(Xtr, y[train_mask].values.astype(float), Xte)


def fit_combined(df, train_mask, test_mask, y, warm_artists, max_year):
    Xb = build_X_baseline(df)
    X = add_artist_fe(Xb, df, warm_artists)
    train_df = df[train_mask].copy()
    artist_avg = train_df.groupby("artist_slug")["log_price"].mean().to_dict()
    grand = float(y[train_mask].mean())
    X = X.copy()
    X["recent_avg_log_price"] = df["artist_slug"].map(artist_avg).fillna(grand).values
    Xtr = X[train_mask].values.astype(float)
    Xte = X[test_mask].values.astype(float)
    weights = time_weights(df[train_mask]["year_made"].values, max_year, half_life=2)
    return fit_huber(Xtr, y[train_mask].values.astype(float), Xte, weights=weights)


def fit_combined_shrunk(df, train_mask, test_mask, y, warm_artists, max_year):
    Xb = build_X_baseline(df)
    X = add_artist_fe(Xb, df, warm_artists)
    train_df = df[train_mask].copy()
    eb, grand = empirical_bayes_shrink(train_df)
    X = X.copy()
    X["recent_avg_log_price"] = df["artist_slug"].map(eb).fillna(grand).values
    Xtr = X[train_mask].values.astype(float)
    Xte = X[test_mask].values.astype(float)
    weights = time_weights(df[train_mask]["year_made"].values, max_year, half_life=2)
    return fit_huber(Xtr, y[train_mask].values.astype(float), Xte, weights=weights)


# ─────────────────────────────────────
# Main experiment
# ─────────────────────────────────────
def run():
    df = pd.read_parquet(DATA)
    y = df["log_price"]
    logger.info("=" * 80)
    logger.info("Stage 4 Warm Path Validation (v3, 사전등록 적용)")
    logger.info("=" * 80)
    logger.info(f"Source: {DATA.relative_to(ROOT)} — {len(df):,} 작품 / {df['artist_slug'].nunique()} 작가")

    train_mask = (df["split"] == "train").values
    test_mask_full = (df["split"] == "test").values
    warm_artists = set(df[train_mask & df["is_warm_artist"]]["artist_slug"].unique())
    test_mask = test_mask_full & df["is_test_eligible"].values & df["is_warm_artist"].values
    test_artists = df[test_mask]["artist_slug"].values
    yte = y[test_mask].values.astype(float)
    max_year = df[train_mask]["year_made"].max()

    logger.info(f"\nTrain: {train_mask.sum():,} 작품 / {df[train_mask]['artist_slug'].nunique()} 작가")
    logger.info(f"Warm artists (train ≥10): {len(warm_artists)}")
    logger.info(f"Test-eligible warm test: {test_mask.sum()} 작품 / {len(set(test_artists))} 작가")
    logger.info(f"Per-cluster test rows: min {Counter(test_artists).most_common()[-1][1]}, "
                f"max {Counter(test_artists).most_common()[0][1]}")

    # 4 모델 fit
    logger.info(f"\n--- 1. 4-model fit + Primary (FE only vs baseline) ---")
    pred_baseline = fit_baseline(df, train_mask, test_mask, y)
    pred_fe = fit_fe_only(df, train_mask, test_mask, y, warm_artists)
    pred_combined = fit_combined(df, train_mask, test_mask, y, warm_artists, max_year)
    pred_combined_shrunk = fit_combined_shrunk(df, train_mask, test_mask, y, warm_artists, max_year)

    base_mdape = mdape(yte, pred_baseline)
    fe_mdape = mdape(yte, pred_fe)
    comb_mdape = mdape(yte, pred_combined)
    cs_mdape = mdape(yte, pred_combined_shrunk)
    logger.info(f"\n  Model            MdAPE")
    logger.info(f"  baseline        {base_mdape:>6.2f}%")
    logger.info(f"  FE only         {fe_mdape:>6.2f}% (Δ {fe_mdape - base_mdape:+.2f}%p)")
    logger.info(f"  Combined        {comb_mdape:>6.2f}% (Δ {comb_mdape - base_mdape:+.2f}%p)")
    logger.info(f"  Combined-shrunk {cs_mdape:>6.2f}% (Δ {cs_mdape - base_mdape:+.2f}%p)")

    # Primary cluster bootstrap (n=2000)
    logger.info(f"\n--- 2. Primary cluster bootstrap (n={N_BOOT_PRIMARY}, FE only - baseline) ---")
    boot_primary = cluster_bootstrap_diff(yte, pred_fe, pred_baseline, test_artists, n_boot=N_BOOT_PRIMARY, seed=42)
    logger.info(f"  diff mean: {boot_primary['mean']:+.2f}%p")
    logger.info(f"  95% CI: [{boot_primary['ci_lo_95']:+.2f}, {boot_primary['ci_hi_95']:+.2f}]")
    logger.info(f"  P(diff ≥ 0) (1-sided p): {boot_primary['p_value_1sided']:.4f}")
    primary_pass_stat = boot_primary["ci_hi_95"] <= 0
    primary_pass_practical = (fe_mdape - base_mdape) <= -0.8
    logger.info(f"  Primary 합격 (CI 상한 ≤ 0): {'✓' if primary_pass_stat else '✗'}")
    logger.info(f"  Primary 합격 (Δ ≤ -0.8%p practical): {'✓' if primary_pass_practical else '✗'}")

    # Seed stability (10 seeds)
    logger.info(f"\n--- 3. Primary seed stability (10 seeds × n=500) ---")
    stab = []
    for s in range(10, 110, 10):
        b = cluster_bootstrap_diff(yte, pred_fe, pred_baseline, test_artists, n_boot=500, seed=s)
        stab.append(b["mean"])
    stab = np.array(stab)
    logger.info(f"  mean diff (10 seeds): {stab.mean():+.2f}%p (std {stab.std():.3f})")
    logger.info(f"  std ≤ 0.5%p 요구: {'✓' if stab.std() <= 0.5 else '✗'}")

    # Secondary 5 (Holm m=5)
    logger.info(f"\n--- 4. Secondary (Holm m=5, primary 와 별도 family) ---")
    sec_results = []
    sec_results.append(("Combined vs baseline", cluster_bootstrap_diff(yte, pred_combined, pred_baseline, test_artists, n_boot=N_BOOT_SECONDARY)))
    sec_results.append(("Combined-shrunk vs baseline", cluster_bootstrap_diff(yte, pred_combined_shrunk, pred_baseline, test_artists, n_boot=N_BOOT_SECONDARY)))

    # FE only by depth bin
    df_te = df[test_mask].reset_index(drop=True)
    for bin_label in ["10-14", "15-24", "25+"]:
        bin_mask = (df_te["depth_bin"] == bin_label).values
        if bin_mask.sum() < 10:
            sec_results.append((f"FE only @ depth {bin_label}", {"n_boot_kept": 0, "skip": True}))
            continue
        bin_artists = df_te[bin_mask]["artist_slug"].values
        yte_bin = yte[bin_mask]
        b = cluster_bootstrap_diff(yte_bin, pred_fe[bin_mask], pred_baseline[bin_mask], bin_artists, n_boot=N_BOOT_SECONDARY)
        sec_results.append((f"FE only @ depth {bin_label}", b))

    pvals = [r[1].get("p_value_1sided", 1.0) for r in sec_results]
    holm_rejects = holm_adjust(pvals, alpha=0.05)
    logger.info(f"\n  {'name':>30} {'mean':>8} {'CI lo':>8} {'CI hi':>8} {'p_raw':>8} {'Holm':>5}")
    for (name, b), reject in zip(sec_results, holm_rejects):
        if b.get("skip"):
            logger.info(f"  {name:>30} (skip — n<10)")
            continue
        logger.info(f"  {name:>30} {b['mean']:>+6.2f}  {b['ci_lo_95']:>+6.2f}  {b['ci_hi_95']:>+6.2f}  {b['p_value_1sided']:>6.3f}  {'YES' if reject else 'no':>5}")

    # Composition shift (Stage 3 vs Stage 4)
    logger.info(f"\n--- 5. Composition-shift (Stage 3 vs Stage 4) ---")
    if STAGE3_PATH.exists():
        df_s3 = pd.read_parquet(STAGE3_PATH)
        s3_artists = set(df_s3["artist_slug"].unique())
        new_warm = warm_artists - s3_artists
        existing_warm = warm_artists & s3_artists
        logger.info(f"  Stage 3 작가 100명 중 Stage 4 warm 에 포함: {len(existing_warm)}")
        logger.info(f"  Stage 4 신규 warm (Stage 3 에 없던): {len(new_warm)}")

        # 신규 vs 기존 warm 분리 평가
        test_new_mask = np.isin(test_artists, list(new_warm))
        test_existing_mask = np.isin(test_artists, list(existing_warm))
        if test_new_mask.sum() >= 3:
            new_mdape_b = mdape(yte[test_new_mask], pred_baseline[test_new_mask])
            new_mdape_fe = mdape(yte[test_new_mask], pred_fe[test_new_mask])
            logger.info(f"  신규 warm test (n={test_new_mask.sum()}): baseline {new_mdape_b:.2f}% / FE {new_mdape_fe:.2f}% (Δ {new_mdape_fe - new_mdape_b:+.2f}%p)")
        if test_existing_mask.sum() >= 3:
            ex_mdape_b = mdape(yte[test_existing_mask], pred_baseline[test_existing_mask])
            ex_mdape_fe = mdape(yte[test_existing_mask], pred_fe[test_existing_mask])
            logger.info(f"  기존 warm test (n={test_existing_mask.sum()}): baseline {ex_mdape_b:.2f}% / FE {ex_mdape_fe:.2f}% (Δ {ex_mdape_fe - ex_mdape_b:+.2f}%p)")

    # Segment harm budget (가격 tertile / depth bin)
    logger.info(f"\n--- 6. Segment harm budget (FE only vs baseline) ---")
    harm_results = []
    # Price tertile
    prices = np.exp(yte)
    qs = np.quantile(prices, [0.33, 0.67])
    harm_thresholds_price = {"저가": 1.0, "중가": 0.5, "고가": 1.0}
    for label, lo, hi in [("저가", -np.inf, qs[0]), ("중가", qs[0], qs[1]), ("고가", qs[1], np.inf)]:
        m = (prices > lo) & (prices <= hi)
        if m.sum() < 5:
            continue
        b_md = mdape(yte[m], pred_baseline[m])
        fe_md = mdape(yte[m], pred_fe[m])
        diff = fe_md - b_md
        threshold = harm_thresholds_price[label]
        violation = diff > threshold
        harm_results.append({"slice": f"price_{label}", "n": int(m.sum()), "baseline": b_md, "fe": fe_md, "diff": diff, "threshold": threshold, "violation": bool(violation)})
        logger.info(f"  price {label} (n={m.sum()}): {b_md:.2f} → {fe_md:.2f} (Δ {diff:+.2f}%p, 임계 +{threshold:.1f}) {'⚠️ violation' if violation else '✓'}")

    # Depth bin
    harm_thresholds_depth = {"10-14": 1.5, "15-24": 1.0, "25+": 0.5}
    for bin_label, threshold in harm_thresholds_depth.items():
        m = (df_te["depth_bin"] == bin_label).values
        if m.sum() < 5:
            continue
        b_md = mdape(yte[m], pred_baseline[m])
        fe_md = mdape(yte[m], pred_fe[m])
        diff = fe_md - b_md
        violation = diff > threshold
        harm_results.append({"slice": f"depth_{bin_label}", "n": int(m.sum()), "baseline": b_md, "fe": fe_md, "diff": diff, "threshold": threshold, "violation": bool(violation)})
        logger.info(f"  depth {bin_label} (n={m.sum()}): {b_md:.2f} → {fe_md:.2f} (Δ {diff:+.2f}%p, 임계 +{threshold:.1f}) {'⚠️ violation' if violation else '✓'}")

    n_violations = sum(1 for r in harm_results if r["violation"])

    # 최종 합격 판정 (사전등록 §6.1)
    logger.info(f"\n--- 7. 최종 합격 판정 (사전등록 §6.1) ---")
    primary_stat_ok = primary_pass_stat
    primary_practical_ok = primary_pass_practical
    seed_ok = stab.std() <= 0.5
    harm_ok = n_violations == 0

    logger.info(f"  Primary CI 상한 ≤ 0:       {'✓' if primary_stat_ok else '✗'}")
    logger.info(f"  Primary practical Δ ≤ -0.8%p: {'✓' if primary_practical_ok else '✗'}")
    logger.info(f"  Seed std ≤ 0.5%p:          {'✓' if seed_ok else '✗'}")
    logger.info(f"  Segment harm 0건:          {'✓' if harm_ok else '✗'} ({n_violations} violations)")

    primary_pass = primary_stat_ok and primary_practical_ok and seed_ok and harm_ok
    if primary_pass:
        verdict = "PASS — Phase 2 (Artsy-only full confirmatory) 진입 자격"
    elif primary_practical_ok and (boot_primary["ci_hi_95"] <= 1.0):
        verdict = "BORDERLINE — 보류, Stage 5 재검토 또는 외부 source 보강"
    elif (fe_mdape - base_mdape) >= 0:
        verdict = "REJECT — warm-only path 후보 폐기"
    else:
        verdict = "BORDERLINE — 보류 (실용 효과 또는 segment harm)"
    logger.info(f"\n  판정: {verdict}")

    summary = {
        "data_source": str(DATA.relative_to(ROOT)),
        "n_train": int(train_mask.sum()),
        "n_warm_artists": len(warm_artists),
        "n_test_eligible_artists": int(len(set(test_artists))),
        "n_test_rows": int(test_mask.sum()),
        "models": {
            "baseline_mdape": base_mdape,
            "fe_only_mdape": fe_mdape,
            "combined_mdape": comb_mdape,
            "combined_shrunk_mdape": cs_mdape,
        },
        "primary": {
            "diff_point": fe_mdape - base_mdape,
            "bootstrap": boot_primary,
            "ci_upper_le_0": bool(primary_stat_ok),
            "practical_le_neg08": bool(primary_practical_ok),
            "seed_std": float(stab.std()),
            "seed_std_le_05": bool(seed_ok),
        },
        "secondary": [
            {"name": name, "result": result}
            for (name, result), reject in zip(sec_results, holm_rejects)
        ],
        "secondary_holm_rejects": [
            name for (name, _), reject in zip(sec_results, holm_rejects) if reject
        ],
        "harm_budget": {
            "results": harm_results,
            "n_violations": int(n_violations),
            "all_pass": bool(harm_ok),
        },
        "verdict": verdict,
    }

    out = RESULTS / "stage4_warm_validation.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(f"\nSaved: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    run()
