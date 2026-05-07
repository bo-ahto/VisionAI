"""Stage 6B — Partial Pooling (statsmodels MixedLM, registered follow-up).

사전등록 v2 freeze: docs/stage6b_partial_pooling_prereg_20260507.md (2026-05-07)
- Model: F4 + spline + artist random intercept (Stage 3 ME 동일, is_low_price 삭제 — 타깃 누수)
- Implementation: statsmodels MixedLM, REML, optimizer fallback (lbfgs → bfgs → nm)
- Primary: Δ ≤ -1.0%p + CI 상한 ≤ 0
- 🔴 Hard gate: Δ_low ≤ 0%p
- Secondary Holm m=4: low / mid-high / sparse-warm / newly-warm
- Mechanistic (Holm 외): ICC CI lower bound > 0
- 100-seed LAO + cluster bootstrap n=2000
"""

from __future__ import annotations

import json
import logging
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import HuberRegressor
from statsmodels.regression.mixed_linear_model import MixedLM

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore")  # Suppress convergence warnings (handled by fallback)

ROOT = Path(__file__).parent.parent.parent
DATA = ROOT / "data" / "curated" / "stage4_full.parquet"
RESULTS = Path(__file__).parent / "results"
LOW_PRICE_KRW = 5_000_000
N_SEEDS = 100
N_BOOT = 2000
SPARSE_THRESHOLD = 5  # train count ≤ 5

# Stage 3 reference (newly-warm definition)
STAGE3 = ROOT / "data" / "curated" / "stage3_1000x100.parquet"


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


def build_features(df):
    out = df[["log_area", "birth_year_centered", "log_artist_total_works"]].copy()
    knots = np.percentile(df["log_area"].values, [10, 50, 90])
    sp = restricted_cubic_spline(df["log_area"].values, knots)
    out["log_area_spline"] = sp[:, 0]
    return out


def fit_baseline_huber(Xtr, ytr, Xte):
    if len(ytr) < 5:
        return np.full(len(Xte), float(np.mean(ytr) if len(ytr) else 0.0))
    m = HuberRegressor(epsilon=1.35, alpha=0.0001, max_iter=2000)
    m.fit(Xtr, ytr)
    return Xte @ m.coef_ + m.intercept_


def fit_mixedlm(Xtr_df, ytr, groups_tr, Xte_df, groups_te):
    """Stage 6B partial pooling: MixedLM with artist random intercept.

    Optimizer fallback (prereg §2.2): lbfgs → bfgs → nm
    First successful = canonical.
    Returns predictions (with random intercept for known artists, fixed-only for unseen).
    """
    formula_data = Xtr_df.copy()
    formula_data["y"] = ytr
    formula = "y ~ log_area + birth_year_centered + log_artist_total_works + log_area_spline"

    res = None
    icc_artist_var = None
    for opt in ["lbfgs", "bfgs", "nm"]:
        try:
            m = MixedLM.from_formula(formula, groups=groups_tr, data=formula_data)
            res = m.fit(method=opt, reml=True, disp=False)
            if res.converged:
                break
        except Exception:
            continue

    if res is None or not res.converged:
        # Fallback: simple OLS-like fit (artist effect = 0)
        return None, None, None

    # Fixed effect predictions
    fe_params = res.fe_params  # Intercept + 4 features
    feat_cols = ["Intercept"] + ["log_area", "birth_year_centered", "log_artist_total_works", "log_area_spline"]

    Xte_with_const = Xte_df.copy()
    Xte_with_const.insert(0, "Intercept", 1.0)
    pred_fixed = Xte_with_const[feat_cols].values @ fe_params.values

    # Random intercepts (for known artists)
    re = res.random_effects  # dict: artist_slug -> Series with "Group"
    pred = pred_fixed.copy()
    for i, artist in enumerate(groups_te):
        if artist in re:
            pred[i] += float(re[artist].iloc[0])
        # Unseen artist: u_j = 0 (Stage 3 ME 패턴 — cold-start 무력화)

    # ICC: artist-level variance / (artist + residual)
    artist_var = float(res.cov_re.iloc[0, 0])
    resid_var = float(res.scale)
    if (artist_var + resid_var) > 0:
        icc = artist_var / (artist_var + resid_var)
    else:
        icc = 0.0

    return pred, artist_var, icc


def mdape_log(yte, pred):
    if len(yte) == 0:
        return None
    return float(np.median(np.abs(np.exp(pred) - np.exp(yte)) / np.exp(yte)) * 100)


def lao_split(df, seed):
    rng = np.random.default_rng(seed)
    artists = df["artist_slug"].unique()
    n_test = max(1, int(len(artists) * 0.2))
    test_artists = set(rng.choice(artists, size=n_test, replace=False))
    return ~df["artist_slug"].isin(test_artists).values, df["artist_slug"].isin(test_artists).values


def eval_one_seed(df, y, seed, stage3_artists):
    train_mask, test_mask = lao_split(df, seed)
    df_tr = df[train_mask].reset_index(drop=True)
    df_te = df[test_mask].reset_index(drop=True)
    if len(df_tr) < 50 or len(df_te) < 5:
        return None

    feat_tr = build_features(df_tr)
    feat_te = build_features(df_te)
    y_tr = y[train_mask].values.astype(float)
    y_te = y[test_mask].values.astype(float)

    # Baseline (운영 채택): Huber
    pred_baseline = fit_baseline_huber(feat_tr.values, y_tr, feat_te.values)

    # 6B: MixedLM partial pooling
    pred_mixed, artist_var, icc = fit_mixedlm(
        feat_tr, y_tr, df_tr["artist_slug"].values, feat_te, df_te["artist_slug"].values
    )
    if pred_mixed is None:
        return {"seed": seed, "skip": True}

    is_low_te = (df_te["price_krw"].values < LOW_PRICE_KRW)

    # Sparse-warm: train count ≤ 5 (per artist)
    train_counts = df_tr.groupby("artist_slug").size()
    sparse_artists = set(train_counts[train_counts <= SPARSE_THRESHOLD].index)
    is_sparse_te = df_te["artist_slug"].isin(sparse_artists).values

    # Newly-warm: not in Stage 3 cohort
    is_newly_warm_te = ~df_te["artist_slug"].isin(stage3_artists).values

    return {
        "seed": seed,
        "n_test": int(len(y_te)),
        "n_test_low": int(is_low_te.sum()),
        "n_test_high": int((~is_low_te).sum()),
        "n_test_sparse": int(is_sparse_te.sum()),
        "n_test_newly_warm": int(is_newly_warm_te.sum()),
        "baseline_overall": mdape_log(y_te, pred_baseline),
        "mixed_overall": mdape_log(y_te, pred_mixed),
        "baseline_low": mdape_log(y_te[is_low_te], pred_baseline[is_low_te]) if is_low_te.sum() else None,
        "mixed_low": mdape_log(y_te[is_low_te], pred_mixed[is_low_te]) if is_low_te.sum() else None,
        "baseline_high": mdape_log(y_te[~is_low_te], pred_baseline[~is_low_te]) if (~is_low_te).sum() else None,
        "mixed_high": mdape_log(y_te[~is_low_te], pred_mixed[~is_low_te]) if (~is_low_te).sum() else None,
        "baseline_sparse": mdape_log(y_te[is_sparse_te], pred_baseline[is_sparse_te]) if is_sparse_te.sum() else None,
        "mixed_sparse": mdape_log(y_te[is_sparse_te], pred_mixed[is_sparse_te]) if is_sparse_te.sum() else None,
        "baseline_newly": mdape_log(y_te[is_newly_warm_te], pred_baseline[is_newly_warm_te]) if is_newly_warm_te.sum() else None,
        "mixed_newly": mdape_log(y_te[is_newly_warm_te], pred_mixed[is_newly_warm_te]) if is_newly_warm_te.sum() else None,
        "icc": icc,
        "artist_var": artist_var,
        "test_artists": df_te["artist_slug"].values.tolist(),
        "y_te": y_te.tolist(),
        "pred_baseline": pred_baseline.tolist(),
        "pred_mixed": pred_mixed.tolist(),
    }


def cluster_bootstrap_diff(yte, pred_a, pred_b, test_artists, n_boot=N_BOOT, seed=42):
    rng = np.random.default_rng(seed)
    yte = np.asarray(yte)
    pred_a = np.asarray(pred_a)
    pred_b = np.asarray(pred_b)
    test_artists = np.asarray(test_artists)
    unique = list(set(test_artists))
    diffs = []
    for _ in range(n_boot):
        sample = rng.choice(unique, size=len(unique), replace=True)
        mask = np.isin(test_artists, sample)
        if mask.sum() < 3:
            continue
        diffs.append(mdape_log(yte[mask], pred_a[mask]) - mdape_log(yte[mask], pred_b[mask]))
    diffs = np.array(diffs)
    return {
        "mean": float(np.mean(diffs)),
        "ci_lo_95": float(np.percentile(diffs, 2.5)),
        "ci_hi_95": float(np.percentile(diffs, 97.5)),
        "p_1sided": float((diffs >= 0).mean()),
    }


def run():
    df = pd.read_parquet(DATA)
    y = df["log_price"]

    # Stage 3 cohort (newly-warm 정의)
    if STAGE3.exists():
        stage3_artists = set(pd.read_parquet(STAGE3)["artist_slug"].unique())
    else:
        stage3_artists = set()

    logger.info("=" * 80)
    logger.info("Stage 6B — Partial Pooling (MixedLM, registered follow-up)")
    logger.info("=" * 80)
    logger.info(f"Source: {DATA.relative_to(ROOT)} ({len(df):,} 작품)")
    logger.info(f"Stage 3 cohort artists (newly-warm 정의용): {len(stage3_artists)}")

    seed_results = []
    skipped = 0
    for s in range(N_SEEDS):
        try:
            r = eval_one_seed(df, y, s, stage3_artists)
            if r is None or r.get("skip"):
                skipped += 1
                continue
            seed_results.append(r)
        except Exception as e:
            skipped += 1
        if (s + 1) % 25 == 0:
            logger.info(f"  ... {s+1}/{N_SEEDS} done")

    logger.info(f"\n[100-seed LAO] 완료 {len(seed_results)} / skip {skipped}")

    # Aggregate
    def agg(key):
        vals = [r[key] for r in seed_results if r.get(key) is not None]
        return np.array(vals)

    base_overall = agg("baseline_overall")
    mixed_overall = agg("mixed_overall")
    base_low = agg("baseline_low")
    mixed_low = agg("mixed_low")
    base_high = agg("baseline_high")
    mixed_high = agg("mixed_high")
    base_sparse = agg("baseline_sparse")
    mixed_sparse = agg("mixed_sparse")
    base_newly = agg("baseline_newly")
    mixed_newly = agg("mixed_newly")

    diff_overall = mixed_overall - base_overall
    # Subgroup diff (matched per seed via index)
    diff_low = []
    for r in seed_results:
        if r.get("baseline_low") is not None and r.get("mixed_low") is not None:
            diff_low.append(r["mixed_low"] - r["baseline_low"])
    diff_low = np.array(diff_low)
    diff_high = np.array([r["mixed_high"] - r["baseline_high"] for r in seed_results if r.get("baseline_high") is not None and r.get("mixed_high") is not None])
    diff_sparse = np.array([r["mixed_sparse"] - r["baseline_sparse"] for r in seed_results if r.get("baseline_sparse") is not None and r.get("mixed_sparse") is not None])
    diff_newly = np.array([r["mixed_newly"] - r["baseline_newly"] for r in seed_results if r.get("baseline_newly") is not None and r.get("mixed_newly") is not None])

    iccs = agg("icc")

    logger.info(f"\n{'metric':>22} {'baseline':>10} {'mixed':>10} {'Δ (mean)':>12} {'n_seeds':>8}")
    logger.info(f"{'overall MdAPE':>22} {base_overall.mean():>8.2f}% {mixed_overall.mean():>8.2f}% {diff_overall.mean():>+9.2f}%p {len(diff_overall):>5}")
    logger.info(f"{'low MdAPE':>22} {base_low.mean():>8.2f}% {mixed_low.mean():>8.2f}% {diff_low.mean():>+9.2f}%p {len(diff_low):>5}")
    logger.info(f"{'mid/high MdAPE':>22} {base_high.mean():>8.2f}% {mixed_high.mean():>8.2f}% {diff_high.mean():>+9.2f}%p {len(diff_high):>5}")
    logger.info(f"{'sparse-warm MdAPE':>22} {base_sparse.mean():>8.2f}% {mixed_sparse.mean():>8.2f}% {diff_sparse.mean():>+9.2f}%p {len(diff_sparse):>5}")
    logger.info(f"{'newly-warm MdAPE':>22} {base_newly.mean():>8.2f}% {mixed_newly.mean():>8.2f}% {diff_newly.mean():>+9.2f}%p {len(diff_newly):>5}")

    logger.info(f"\n[ICC mechanism (100-seed)] mean {iccs.mean():.4f}, 95% CI [{np.percentile(iccs, 2.5):.4f}, {np.percentile(iccs, 97.5):.4f}]")

    # Primary cluster bootstrap (single representative seed=0)
    rep = seed_results[0]
    boot = cluster_bootstrap_diff(rep["y_te"], rep["pred_mixed"], rep["pred_baseline"], rep["test_artists"])
    logger.info(f"\n[Primary cluster bootstrap (rep seed=0, n=2000)]")
    logger.info(f"  Δ overall (mixed - baseline) mean: {boot['mean']:+.2f}%p")
    logger.info(f"  95% CI: [{boot['ci_lo_95']:+.2f}, {boot['ci_hi_95']:+.2f}]")
    logger.info(f"  P(diff ≥ 0) = {boot['p_1sided']:.4f}")

    # 사전등록 §3 PASS/BORDERLINE/FAIL 판정
    primary_ci_pass = boot["ci_hi_95"] <= 0
    primary_practical_pass = diff_overall.mean() <= -1.0
    low_harm_pass = diff_low.mean() <= 0  # Hard gate: Δ_low ≤ 0%p (point estimate)

    logger.info(f"\n[PASS/BORDERLINE/FAIL 판정 (사전등록 §3)]")
    logger.info(f"  Primary CI 상한 ≤ 0:        {'✓' if primary_ci_pass else '✗'} ({boot['ci_hi_95']:+.2f}%p)")
    logger.info(f"  Primary practical Δ ≤ -1.0%p: {'✓' if primary_practical_pass else '✗'} ({diff_overall.mean():+.2f}%p)")
    logger.info(f"  🔴 Hard gate Δ_low ≤ 0%p:    {'✓' if low_harm_pass else '✗'} ({diff_low.mean():+.2f}%p)")

    if not low_harm_pass:
        verdict = "FAIL (🔴 Hard gate Δ_low > 0)"
    elif primary_ci_pass and primary_practical_pass:
        verdict = "PASS (Phase 3 shadow 진입 후보)"
    elif (-1.0 < diff_overall.mean() <= -0.3) and low_harm_pass:
        verdict = "BORDERLINE (소폭 개선 -1.0 < Δ ≤ -0.3%p, 6C 우선 검토)"
    elif diff_overall.mean() > -0.3:
        verdict = "FAIL (Δ > -0.3%p, 개선 미달)"
    else:
        verdict = "BORDERLINE (Primary 1개 미달)"
    logger.info(f"\n  → 판정: {verdict}")

    # Mechanism (ICC)
    icc_lo = float(np.percentile(iccs, 2.5))
    icc_pass = icc_lo > 0
    logger.info(f"  ICC mechanism (CI 하한 > 0): {'✓' if icc_pass else '✗'} ({icc_lo:.4f})")

    summary = {
        "n_seeds": len(seed_results),
        "n_skipped": skipped,
        "metrics_100seed_mean": {
            "baseline_overall": float(base_overall.mean()),
            "mixed_overall": float(mixed_overall.mean()),
            "diff_overall_mean": float(diff_overall.mean()),
            "diff_overall_std": float(diff_overall.std()),
            "diff_low_mean": float(diff_low.mean()),
            "diff_high_mean": float(diff_high.mean()),
            "diff_sparse_mean": float(diff_sparse.mean()),
            "diff_newly_mean": float(diff_newly.mean()),
        },
        "icc_mechanism": {
            "mean": float(iccs.mean()),
            "ci_lo_95": float(np.percentile(iccs, 2.5)),
            "ci_hi_95": float(np.percentile(iccs, 97.5)),
            "ci_lower_gt_zero": bool(icc_pass),
        },
        "cluster_bootstrap_seed0": boot,
        "verdict": verdict,
        "primary_pass": {
            "ci_upper_le_0": bool(primary_ci_pass),
            "practical_le_neg1": bool(primary_practical_pass),
            "hard_gate_low_le_0": bool(low_harm_pass),
        },
    }

    out = RESULTS / "stage6b_partial_pooling.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(f"\nSaved: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    run()
