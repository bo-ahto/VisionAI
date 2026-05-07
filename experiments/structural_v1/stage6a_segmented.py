"""Stage 6A — Segmented Architecture (low vs mid/high) confirmatory.

사전등록: docs/stage6a_segmented_prereg_20260507.md (2026-05-07 freeze)
- Routing: (b) Meta-router (LogisticRegression, F4+spline 입력, threshold 0.5)
- Model L: Huber on train low (price < 5M, n=1,906)
- Model H: Huber on train mid/high (n=2,301)
- Baseline: Huber on train 전체 4,207 (운영 채택)

Primary: cold-start LAO 100-seed MdAPE, cluster bootstrap n=2000
Practical Δ ≤ -1.0%p / Hard gate: 저가 harm 0 violations
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import HuberRegressor, LogisticRegression
from sklearn.metrics import balanced_accuracy_score, brier_score_loss

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent.parent
DATA = ROOT / "data" / "curated" / "stage4_full.parquet"
RESULTS = Path(__file__).parent / "results"
LOW_PRICE_KRW = 5_000_000
N_SEEDS = 100
N_BOOT = 2000


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


def build_X(df):
    knots = np.percentile(df["log_area"].values, [10, 50, 90])
    sp = restricted_cubic_spline(df["log_area"].values, knots)
    return np.column_stack([
        df["log_area"].values,
        df["birth_year_centered"].values,
        df["log_artist_total_works"].values,
        sp[:, 0],
    ])


def fit_huber(Xtr, ytr, Xte):
    if len(ytr) < 5:
        # 표본 부족 시 mean fallback
        return np.full(len(Xte), float(np.mean(ytr) if len(ytr) else 0.0))
    m = HuberRegressor(epsilon=1.35, alpha=0.0001, max_iter=2000)
    m.fit(Xtr, ytr)
    return Xte @ m.coef_ + m.intercept_


def fit_router(Xtr, is_low_train):
    """Meta-router: LogisticRegression price<5M binary classifier."""
    m = LogisticRegression(max_iter=1000, class_weight="balanced")
    m.fit(Xtr, is_low_train.astype(int))
    return m


def mdape_log(yte, pred):
    return float(np.median(np.abs(np.exp(pred) - np.exp(yte)) / np.exp(yte)) * 100)


def lao_split(df, seed):
    rng = np.random.default_rng(seed)
    artists = df["artist_slug"].unique()
    n_test = max(1, int(len(artists) * 0.2))
    test_artists = set(rng.choice(artists, size=n_test, replace=False))
    return ~df["artist_slug"].isin(test_artists).values, df["artist_slug"].isin(test_artists).values


def eval_one_seed(df, y, seed):
    train_mask, test_mask = lao_split(df, seed)
    df_tr = df[train_mask]
    df_te = df[test_mask]
    if len(df_tr) < 50 or len(df_te) < 5:
        return None

    X_tr = build_X(df_tr)
    X_te = build_X(df_te)
    y_tr = y[train_mask].values.astype(float)
    y_te = y[test_mask].values.astype(float)
    is_low_tr = (df_tr["price_krw"].values < LOW_PRICE_KRW)
    is_low_te = (df_te["price_krw"].values < LOW_PRICE_KRW)

    # Baseline (운영): Huber on 전체 train
    pred_baseline = fit_huber(X_tr, y_tr, X_te)

    # Segmented: Meta-router + Model L + Model H
    router = fit_router(X_tr, is_low_tr)
    router_proba = router.predict_proba(X_te)[:, 1]  # P(low)
    router_pred_low = router_proba >= 0.5

    # Model L (low train 만)
    Xtr_L, ytr_L = X_tr[is_low_tr], y_tr[is_low_tr]
    # Model H (mid/high train 만)
    Xtr_H, ytr_H = X_tr[~is_low_tr], y_tr[~is_low_tr]

    pred_L = fit_huber(Xtr_L, ytr_L, X_te)
    pred_H = fit_huber(Xtr_H, ytr_H, X_te)
    pred_segmented = np.where(router_pred_low, pred_L, pred_H)

    # Router 품질
    router_recall_low = float(((router_pred_low) & is_low_te).sum() / max(is_low_te.sum(), 1))
    router_balanced_acc = float(balanced_accuracy_score(is_low_te, router_pred_low))
    try:
        router_brier = float(brier_score_loss(is_low_te, router_proba))
    except Exception:
        router_brier = None

    return {
        "n_test": int(len(y_te)),
        "n_test_low": int(is_low_te.sum()),
        "n_test_high": int((~is_low_te).sum()),
        "baseline_overall": mdape_log(y_te, pred_baseline),
        "baseline_low": mdape_log(y_te[is_low_te], pred_baseline[is_low_te]) if is_low_te.sum() else None,
        "baseline_high": mdape_log(y_te[~is_low_te], pred_baseline[~is_low_te]) if (~is_low_te).sum() else None,
        "segmented_overall": mdape_log(y_te, pred_segmented),
        "segmented_low": mdape_log(y_te[is_low_te], pred_segmented[is_low_te]) if is_low_te.sum() else None,
        "segmented_high": mdape_log(y_te[~is_low_te], pred_segmented[~is_low_te]) if (~is_low_te).sum() else None,
        "router_recall_low": router_recall_low,
        "router_balanced_acc": router_balanced_acc,
        "router_brier": router_brier,
        "test_artists": df_te["artist_slug"].values.tolist(),
        "y_te": y_te.tolist(),
        "pred_baseline": pred_baseline.tolist(),
        "pred_segmented": pred_segmented.tolist(),
        "is_low_te": is_low_te.tolist(),
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
    # 평가 = train 전체 (cold-start LAO 100-seed)
    y = df["log_price"]

    logger.info("=" * 80)
    logger.info("Stage 6A — Segmented Architecture (Meta-router + Model L + Model H)")
    logger.info("=" * 80)
    logger.info(f"Source: {DATA.relative_to(ROOT)} ({len(df):,} 작품)")

    # 100-seed LAO (Stage 3/4 동일 protocol — train+test 전체 사용)
    # cold-start LAO: train+test 전체 풀 → 무작위 작가 holdout
    df_all = df  # 전체 (train+val+test) — 100-seed LAO 는 무작위 split

    # 100-seed evaluation
    logger.info(f"\n[100-seed LAO MdAPE] (train_pool = 전체 {len(df_all):,})")
    seed_results = []
    skipped = 0
    for s in range(N_SEEDS):
        try:
            r = eval_one_seed(df_all, y, s)
            if r is None:
                skipped += 1
                continue
            seed_results.append(r)
        except Exception as e:
            skipped += 1
    logger.info(f"  완료 {len(seed_results)} / skip {skipped}")

    # Aggregate
    base_overall = np.array([r["baseline_overall"] for r in seed_results])
    base_low = np.array([r["baseline_low"] for r in seed_results if r["baseline_low"] is not None])
    base_high = np.array([r["baseline_high"] for r in seed_results if r["baseline_high"] is not None])
    seg_overall = np.array([r["segmented_overall"] for r in seed_results])
    seg_low = np.array([r["segmented_low"] for r in seed_results if r["segmented_low"] is not None])
    seg_high = np.array([r["segmented_high"] for r in seed_results if r["segmented_high"] is not None])

    diff_overall = seg_overall - base_overall
    diff_low = seg_low - base_low[:len(seg_low)]
    diff_high = seg_high - base_high[:len(seg_high)]

    logger.info(f"\n  {'metric':>22} {'baseline':>10} {'segmented':>10} {'Δ':>10}")
    logger.info(f"  {'overall MdAPE':>22} {base_overall.mean():>8.2f}% {seg_overall.mean():>8.2f}% {diff_overall.mean():>+7.2f}%p")
    logger.info(f"  {'low MdAPE':>22} {base_low.mean():>8.2f}% {seg_low.mean():>8.2f}% {diff_low.mean():>+7.2f}%p")
    logger.info(f"  {'mid/high MdAPE':>22} {base_high.mean():>8.2f}% {seg_high.mean():>8.2f}% {diff_high.mean():>+7.2f}%p")

    # Router 품질 (100-seed mean)
    recalls = np.array([r["router_recall_low"] for r in seed_results])
    bacc = np.array([r["router_balanced_acc"] for r in seed_results])
    brier = np.array([r["router_brier"] for r in seed_results if r["router_brier"] is not None])
    logger.info(f"\n[Router 품질 (100-seed mean)]")
    logger.info(f"  Low recall (목표 ≥ 0.85): {recalls.mean():.3f}")
    logger.info(f"  Balanced acc (목표 ≥ 0.75): {bacc.mean():.3f}")
    logger.info(f"  Brier score (목표 ≤ 0.20): {brier.mean():.4f}")

    # Cluster bootstrap (single representative seed=42)
    rep = next(r for r in seed_results if r is not None)  # seed 0 의 첫 결과
    boot = cluster_bootstrap_diff(rep["y_te"], rep["pred_segmented"], rep["pred_baseline"], rep["test_artists"])
    logger.info(f"\n[Primary cluster bootstrap (seed=42, n=2000)]")
    logger.info(f"  Δ overall (segmented - baseline) mean: {boot['mean']:+.2f}%p")
    logger.info(f"  95% CI: [{boot['ci_lo_95']:+.2f}, {boot['ci_hi_95']:+.2f}]")
    logger.info(f"  P(diff ≥ 0) = {boot['p_1sided']:.4f}")

    # 사전등록 §3 PASS/BORDERLINE/FAIL 판정
    primary_ci_pass = boot["ci_hi_95"] <= 0
    primary_practical_pass = diff_overall.mean() <= -1.0
    low_harm_violations = int((diff_low > 0).sum())  # 저가 악화 seed 수
    high_harm_violations = int((diff_high > 0.5).sum())  # mid/high 악화 +0.5%p 이상

    logger.info(f"\n[PASS/BORDERLINE/FAIL 판정 (사전등록 §3)]")
    logger.info(f"  Primary CI 상한 ≤ 0:       {'✓' if primary_ci_pass else '✗'} ({boot['ci_hi_95']:+.2f}%p)")
    logger.info(f"  Practical Δ ≤ -1.0%p:      {'✓' if primary_practical_pass else '✗'} ({diff_overall.mean():+.2f}%p)")
    logger.info(f"  🔴 Hard gate 저가 harm = 0: {'✓' if low_harm_violations == 0 else '✗'} ({low_harm_violations}/{len(seed_results)} seeds 저가 악화)")
    logger.info(f"  Mid/high 비악화 (≤ +0.5%p): {'✓' if high_harm_violations == 0 else '✗'} ({high_harm_violations}/{len(seed_results)})")
    logger.info(f"  Router low recall ≥ 0.85:  {'✓' if recalls.mean() >= 0.85 else '✗'} ({recalls.mean():.3f})")
    logger.info(f"  Router balanced acc ≥ 0.75: {'✓' if bacc.mean() >= 0.75 else '✗'} ({bacc.mean():.3f})")

    if low_harm_violations >= 1:
        verdict = "FAIL (🔴 저가 harm hard gate 위반)"
    elif primary_ci_pass and primary_practical_pass:
        verdict = "PASS (Phase 3 shadow 진입 후보)"
    elif (primary_ci_pass or primary_practical_pass):
        verdict = "BORDERLINE (1개만 미달)"
    else:
        verdict = "FAIL (CI + practical 둘 다 미달)"
    logger.info(f"\n  → 판정: {verdict}")

    summary = {
        "n_seeds": len(seed_results),
        "n_skipped": skipped,
        "low_price_threshold_krw": LOW_PRICE_KRW,
        "metrics_100seed_mean": {
            "baseline_overall": float(base_overall.mean()),
            "baseline_low": float(base_low.mean()),
            "baseline_high": float(base_high.mean()),
            "segmented_overall": float(seg_overall.mean()),
            "segmented_low": float(seg_low.mean()),
            "segmented_high": float(seg_high.mean()),
            "diff_overall_mean": float(diff_overall.mean()),
            "diff_low_mean": float(diff_low.mean()),
            "diff_high_mean": float(diff_high.mean()),
            "diff_overall_std": float(diff_overall.std()),
        },
        "router_quality_100seed": {
            "low_recall_mean": float(recalls.mean()),
            "balanced_acc_mean": float(bacc.mean()),
            "brier_mean": float(brier.mean()),
        },
        "cluster_bootstrap_seed42": boot,
        "harm_violations": {
            "low_harm_violations_n_seeds": low_harm_violations,
            "high_harm_violations_n_seeds": high_harm_violations,
            "hard_gate_pass": bool(low_harm_violations == 0),
        },
        "verdict": verdict,
    }

    out = RESULTS / "stage6a_segmented.json"
    with out.open("w", encoding="utf-8") as f:
        # remove large per-seed details
        clean = {k: v for k, v in summary.items()}
        json.dump(clean, f, indent=2, ensure_ascii=False)
    logger.info(f"\nSaved: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    run()
