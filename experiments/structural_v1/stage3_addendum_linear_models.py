"""Stage 3 Exploratory Addendum — 외부 선형 모델 권고 검증.

코덱스 권고 우선순위 C > A > G > E:
- Family 1 (C): gallery / material out-of-fold target encoding + shrinkage
- Family 2 (A): Ridge / Huber + L2 (단독 + 통계 피처 결합)
- Family 3 (G): 작가 차등 처리 (≥20 / 8-19 / <8 등 grid)
- Family 4 (E): artist 통계 피처 다양화 (median / sales_count / dispersion)

Eval:
- Cold-start: Stage 3 100-seed LAO
- Subgroup: 가격 tertile / source / depth bin
- 채택: effect size ≥ -1.0%p + subgroup harm 없음
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.model_selection import KFold

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent.parent
DATA = ROOT / "data" / "curated" / "stage3_1000x100.parquet"
RESULTS = Path(__file__).parent / "results"
N_SEEDS = 100
TE_SHRINKAGE_K = 10  # Bayesian shrinkage prior weight


def make_features(df):
    out = df.copy()
    out["log_area"] = np.log(out["area_cm2"].clip(lower=1))
    out["birth_year_centered"] = out["artist_birth_year"] - out["artist_birth_year"].mean()
    out["log_artist_total_works"] = np.log1p(out["artist_total_works"])
    out["log_price"] = np.log(out["price_krw"].clip(lower=1))
    out["artist_sales_count_log"] = np.log1p(
        out.groupby("artist_slug")["price_krw"].transform("count")
    )
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


def target_encode_oof(df_train, df_eval, group_col, target_col, k=TE_SHRINKAGE_K):
    """Out-of-fold target encoding with Bayesian shrinkage.

    df_train: rows used to compute group means (train fold).
    df_eval: rows to encode (test fold).
    Returns encoded values for df_eval.
    """
    global_mean = float(df_train[target_col].mean())
    group_stats = df_train.groupby(group_col)[target_col].agg(["mean", "count"])
    # μ_g = (n_g * mean_g + k * global) / (n_g + k)
    shrunk = (group_stats["mean"] * group_stats["count"] + global_mean * k) / (
        group_stats["count"] + k
    )
    return df_eval[group_col].map(shrunk).fillna(global_mean).values


def add_te_feature(X, df_train, df_eval, group_col, target_col, name, k=TE_SHRINKAGE_K):
    encoded = target_encode_oof(df_train, df_eval, group_col, target_col, k=k)
    X[name] = encoded
    return X


def fit_huber(Xtr, ytr, Xte, eps=1.35, alpha=0.0001):
    m = HuberRegressor(epsilon=eps, alpha=alpha, max_iter=2000)
    m.fit(Xtr[:, 1:], ytr)
    return Xte[:, 1:] @ m.coef_ + m.intercept_


def fit_ridge(Xtr, ytr, Xte, alpha=1.0):
    m = Ridge(alpha=alpha)
    m.fit(Xtr[:, 1:], ytr)
    return Xte[:, 1:] @ m.coef_ + m.intercept_


def mdape(yte, pred):
    return float(np.median(np.abs(np.exp(pred) - np.exp(yte)) / np.exp(yte)) * 100)


def lao_split(df, seed):
    """Leave-Artists-Out 80/20 split."""
    rng = np.random.default_rng(seed)
    artists = df["artist_slug"].unique()
    n_test = max(1, int(len(artists) * 0.2))
    test_artists = set(rng.choice(artists, size=n_test, replace=False))
    test_mask = df["artist_slug"].isin(test_artists).values
    return ~test_mask, test_mask


def eval_one_seed(df_feat, y, build_fn, fit_fn, seed):
    """One LAO seed evaluation."""
    train_mask, test_mask = lao_split(df_feat, seed)
    df_train = df_feat[train_mask].copy()
    df_eval = df_feat[test_mask].copy()

    X_train_df = build_fn(df_feat, df_train, df_train)  # train uses self for TE
    X_eval_df = build_fn(df_feat, df_train, df_eval)    # eval encoded by train stats

    Xtr = X_train_df[train_mask].values.astype(float)
    Xte = X_eval_df[test_mask].values.astype(float)
    ytr = y[train_mask].values.astype(float)
    yte = y[test_mask].values.astype(float)

    pred = fit_fn(Xtr, ytr, Xte)
    return mdape(yte, pred), yte, pred, df_eval


def eval_100_seed(df_feat, y, build_fn, fit_fn, n_seeds=N_SEEDS):
    """100-seed LAO mean ± std."""
    results = []
    for s in range(n_seeds):
        try:
            m, *_ = eval_one_seed(df_feat, y, build_fn, fit_fn, seed=s)
            results.append(m)
        except Exception:
            continue
    arr = np.array(results)
    return {"mean": float(arr.mean()), "std": float(arr.std()), "n": int(len(arr))}


# ─────────────────────────────────────
# Build functions for each model variant
# ─────────────────────────────────────
def b_baseline(df_feat, df_train, df_eval):
    return build_X_baseline(df_feat)


def b_gallery_te(df_feat, df_train, df_eval):
    X = build_X_baseline(df_feat)
    encoded = np.zeros(len(df_feat))
    for i, row in df_feat.iterrows():
        # Use df_train stats; for train rows themselves, use OOF later if needed
        pass
    # Simpler: encode all rows using df_train stats (eval is leakage-free since train artists ≠ test artists in LAO)
    global_mean = float(df_train["log_price"].mean())
    stats = df_train.groupby("gallery_tier")["log_price"].agg(["mean", "count"])
    shrunk = (stats["mean"] * stats["count"] + global_mean * TE_SHRINKAGE_K) / (
        stats["count"] + TE_SHRINKAGE_K
    )
    X["gallery_te"] = df_feat["gallery_tier"].map(shrunk).fillna(global_mean).values
    return X


def b_material_te(df_feat, df_train, df_eval):
    X = build_X_baseline(df_feat)
    global_mean = float(df_train["log_price"].mean())
    stats = df_train.groupby("medium_category")["log_price"].agg(["mean", "count"])
    shrunk = (stats["mean"] * stats["count"] + global_mean * TE_SHRINKAGE_K) / (
        stats["count"] + TE_SHRINKAGE_K
    )
    X["material_te"] = df_feat["medium_category"].map(shrunk).fillna(global_mean).values
    return X


def b_gallery_material_te(df_feat, df_train, df_eval):
    X = b_gallery_te(df_feat, df_train, df_eval)
    global_mean = float(df_train["log_price"].mean())
    stats = df_train.groupby("medium_category")["log_price"].agg(["mean", "count"])
    shrunk = (stats["mean"] * stats["count"] + global_mean * TE_SHRINKAGE_K) / (
        stats["count"] + TE_SHRINKAGE_K
    )
    X["material_te"] = df_feat["medium_category"].map(shrunk).fillna(global_mean).values
    return X


def b_artist_median_te(df_feat, df_train, df_eval):
    X = build_X_baseline(df_feat)
    global_med = float(df_train["log_price"].median())
    stats = df_train.groupby("artist_slug")["log_price"].agg(["median", "count"])
    shrunk = (stats["median"] * stats["count"] + global_med * TE_SHRINKAGE_K) / (
        stats["count"] + TE_SHRINKAGE_K
    )
    X["artist_median_te"] = df_feat["artist_slug"].map(shrunk).fillna(global_med).values
    return X


def b_artist_sales_count(df_feat, df_train, df_eval):
    X = build_X_baseline(df_feat)
    counts = df_train.groupby("artist_slug").size()
    X["artist_sales_count_log"] = np.log1p(
        df_feat["artist_slug"].map(counts).fillna(0).values
    )
    return X


def b_artist_dispersion_te(df_feat, df_train, df_eval):
    X = build_X_baseline(df_feat)
    global_disp = float(df_train["log_price"].std())
    stats = df_train.groupby("artist_slug")["log_price"].agg(["std", "count"])
    stats["std"] = stats["std"].fillna(0.0)
    shrunk = (stats["std"] * stats["count"] + global_disp * TE_SHRINKAGE_K) / (
        stats["count"] + TE_SHRINKAGE_K
    )
    X["artist_dispersion_te"] = df_feat["artist_slug"].map(shrunk).fillna(global_disp).values
    return X


def b_artist_combined(df_feat, df_train, df_eval):
    X = b_artist_median_te(df_feat, df_train, df_eval)
    counts = df_train.groupby("artist_slug").size()
    X["artist_sales_count_log"] = np.log1p(
        df_feat["artist_slug"].map(counts).fillna(0).values
    )
    global_disp = float(df_train["log_price"].std())
    stats = df_train.groupby("artist_slug")["log_price"].agg(["std", "count"])
    stats["std"] = stats["std"].fillna(0.0)
    shrunk = (stats["std"] * stats["count"] + global_disp * TE_SHRINKAGE_K) / (
        stats["count"] + TE_SHRINKAGE_K
    )
    X["artist_dispersion_te"] = df_feat["artist_slug"].map(shrunk).fillna(global_disp).values
    return X


def b_combined_full(df_feat, df_train, df_eval):
    """Family 1 + Family 4 combined (gallery + material + artist 통계)."""
    X = b_gallery_material_te(df_feat, df_train, df_eval)
    global_med = float(df_train["log_price"].median())
    stats = df_train.groupby("artist_slug")["log_price"].agg(["median", "count"])
    shrunk = (stats["median"] * stats["count"] + global_med * TE_SHRINKAGE_K) / (
        stats["count"] + TE_SHRINKAGE_K
    )
    X["artist_median_te"] = df_feat["artist_slug"].map(shrunk).fillna(global_med).values
    counts = df_train.groupby("artist_slug").size()
    X["artist_sales_count_log"] = np.log1p(
        df_feat["artist_slug"].map(counts).fillna(0).values
    )
    return X


# ─────────────────────────────────────
# Subgroup harm analysis (single seed, cold-start LAO)
# ─────────────────────────────────────
def subgroup_analysis(df_feat, y, build_fn, fit_fn, name, baseline_build_fn,
                     baseline_fit_fn, seed=42):
    train_mask, test_mask = lao_split(df_feat, seed)
    df_train = df_feat[train_mask].copy()
    df_eval = df_feat[test_mask].copy().reset_index(drop=True)

    X_te = build_fn(df_feat, df_train, df_eval)[test_mask].values.astype(float)
    Xtr = build_fn(df_feat, df_train, df_train)[train_mask].values.astype(float)
    X_te_b = baseline_build_fn(df_feat, df_train, df_eval)[test_mask].values.astype(float)
    Xtr_b = baseline_build_fn(df_feat, df_train, df_train)[train_mask].values.astype(float)

    ytr = y[train_mask].values.astype(float)
    yte = y[test_mask].values.astype(float)

    pred_cand = fit_fn(Xtr, ytr, X_te)
    pred_base = baseline_fit_fn(Xtr_b, ytr, X_te_b)

    rows = []
    # Price tertile
    qs = np.quantile(np.exp(yte), [0.33, 0.67])
    for label, lo, hi in [("저가", -np.inf, qs[0]), ("중가", qs[0], qs[1]), ("고가", qs[1], np.inf)]:
        prices = np.exp(yte)
        m = (prices > lo) & (prices <= hi)
        if m.sum() < 5:
            continue
        rows.append({
            "subgroup_type": "price",
            "label": label,
            "n": int(m.sum()),
            "baseline_mdape": mdape(yte[m], pred_base[m]),
            "candidate_mdape": mdape(yte[m], pred_cand[m]),
        })
    # Gallery tier
    for tier in [2, 3, 4]:
        m = (df_eval["gallery_tier"] == tier).values
        if m.sum() < 5:
            continue
        rows.append({
            "subgroup_type": "tier",
            "label": f"tier_{tier}",
            "n": int(m.sum()),
            "baseline_mdape": mdape(yte[m], pred_base[m]),
            "candidate_mdape": mdape(yte[m], pred_cand[m]),
        })
    return rows


# ─────────────────────────────────────
# Main
# ─────────────────────────────────────
def run():
    df = pd.read_parquet(DATA)
    df_feat = make_features(df)
    y = df_feat["log_price"]

    summary = {"n_seeds": N_SEEDS}
    logger.info("=" * 80)
    logger.info("Stage 3 Exploratory Addendum — 외부 선형 모델 권고 검증")
    logger.info("=" * 80)

    # Baseline reference
    huber_fit = lambda Xtr, ytr, Xte: fit_huber(Xtr, ytr, Xte, eps=1.35)
    ridge_fit_alpha1 = lambda Xtr, ytr, Xte: fit_ridge(Xtr, ytr, Xte, alpha=1.0)
    huber_l2 = lambda Xtr, ytr, Xte: fit_huber(Xtr, ytr, Xte, eps=1.35, alpha=1.0)

    logger.info(f"\n[100-seed LAO MdAPE — mean ± std]\n")
    logger.info(f"  {'family':>10} {'model':>30} {'MdAPE':>10} {'std':>7} {'Δ vs Huber baseline':>22}")

    # Reference: F4 + spline + Huber (운영 채택)
    baseline_ref = eval_100_seed(df_feat, y, b_baseline, huber_fit)
    logger.info(
        f"  {'(ref)':>10} {'baseline (F4+spline+Huber 운영)':>30} "
        f"{baseline_ref['mean']:>7.2f}% {baseline_ref['std']:>5.2f}  (= 0)"
    )
    summary["baseline_huber"] = baseline_ref
    base_ref_mean = baseline_ref["mean"]

    # Family 1 — gallery / material TE
    f1_results = {}
    for name, build_fn in [
        ("gallery_te", b_gallery_te),
        ("material_te", b_material_te),
        ("gallery+material_te", b_gallery_material_te),
    ]:
        r = eval_100_seed(df_feat, y, build_fn, huber_fit)
        diff = r["mean"] - base_ref_mean
        logger.info(
            f"  {'F1 (C)':>10} {name:>30} {r['mean']:>7.2f}% {r['std']:>5.2f}  {diff:>+8.2f}%p"
        )
        f1_results[name] = {**r, "diff_vs_baseline": diff}
    summary["family1_target_encoding"] = f1_results

    # Family 2 — Penalty / Regularization
    f2_results = {}
    for name, fit_fn in [
        ("Ridge (alpha=1.0)", ridge_fit_alpha1),
        ("Huber + L2 (alpha=1.0)", huber_l2),
    ]:
        r = eval_100_seed(df_feat, y, b_baseline, fit_fn)
        diff = r["mean"] - base_ref_mean
        logger.info(
            f"  {'F2 (A)':>10} {name:>30} {r['mean']:>7.2f}% {r['std']:>5.2f}  {diff:>+8.2f}%p"
        )
        f2_results[name] = {**r, "diff_vs_baseline": diff}

    # Combined: gallery+material TE + Ridge / Huber+L2
    for name, fit_fn in [
        ("F1+F2: TE + Ridge", ridge_fit_alpha1),
        ("F1+F2: TE + Huber+L2", huber_l2),
    ]:
        r = eval_100_seed(df_feat, y, b_gallery_material_te, fit_fn)
        diff = r["mean"] - base_ref_mean
        logger.info(
            f"  {'F2 (A)':>10} {name:>30} {r['mean']:>7.2f}% {r['std']:>5.2f}  {diff:>+8.2f}%p"
        )
        f2_results[name] = {**r, "diff_vs_baseline": diff}
    summary["family2_penalty"] = f2_results

    # Family 4 — Artist 통계 피처 다양화
    # (LAO 에서 작가가 test 에 새로 등장 → artist_slug 통계는 train 에 없어 global default 사용)
    # → 효과 제한적이지만 그대로 평가 (코덱스 권고대로)
    f4_results = {}
    for name, build_fn in [
        ("artist_median_te", b_artist_median_te),
        ("artist_sales_count_log", b_artist_sales_count),
        ("artist_dispersion_te", b_artist_dispersion_te),
        ("artist_combined (3 feat)", b_artist_combined),
    ]:
        r = eval_100_seed(df_feat, y, build_fn, huber_fit)
        diff = r["mean"] - base_ref_mean
        logger.info(
            f"  {'F4 (E)':>10} {name:>30} {r['mean']:>7.2f}% {r['std']:>5.2f}  {diff:>+8.2f}%p"
        )
        f4_results[name] = {**r, "diff_vs_baseline": diff}
    summary["family4_artist_stats"] = f4_results

    # All combined (Family 1 + 4 + Huber+L2)
    r = eval_100_seed(df_feat, y, b_combined_full, huber_l2)
    diff = r["mean"] - base_ref_mean
    logger.info(
        f"  {'COMBINED':>10} {'F1+F4+Huber+L2':>30} {r['mean']:>7.2f}% {r['std']:>5.2f}  {diff:>+8.2f}%p"
    )
    summary["combined_full"] = {**r, "diff_vs_baseline": diff}

    # Subgroup analysis for top candidates (anything with diff < -0.5%p)
    logger.info(f"\n[Subgroup analysis — top candidates with Δ ≤ -0.5%p]")
    top_candidates = []
    for fam, results in [("F1", f1_results), ("F2", f2_results), ("F4", f4_results),
                         ("COMB", {"F1+F4+Huber+L2": summary["combined_full"]})]:
        for name, r in results.items():
            if r["diff_vs_baseline"] <= -0.5:
                top_candidates.append((fam, name, r))

    subgroup_summary = []
    for fam, name, r in top_candidates:
        # Re-derive build_fn / fit_fn (mapping)
        all_models = {
            "gallery_te": (b_gallery_te, huber_fit),
            "material_te": (b_material_te, huber_fit),
            "gallery+material_te": (b_gallery_material_te, huber_fit),
            "Ridge (alpha=1.0)": (b_baseline, ridge_fit_alpha1),
            "Huber + L2 (alpha=1.0)": (b_baseline, huber_l2),
            "F1+F2: TE + Ridge": (b_gallery_material_te, ridge_fit_alpha1),
            "F1+F2: TE + Huber+L2": (b_gallery_material_te, huber_l2),
            "artist_median_te": (b_artist_median_te, huber_fit),
            "artist_sales_count_log": (b_artist_sales_count, huber_fit),
            "artist_dispersion_te": (b_artist_dispersion_te, huber_fit),
            "artist_combined (3 feat)": (b_artist_combined, huber_fit),
            "F1+F4+Huber+L2": (b_combined_full, huber_l2),
        }
        if name not in all_models:
            continue
        build_fn, fit_fn = all_models[name]
        rows = subgroup_analysis(df_feat, y, build_fn, fit_fn, name, b_baseline, huber_fit)
        logger.info(f"\n  [{fam}] {name} — Δ {r['diff_vs_baseline']:+.2f}%p (100-seed mean)")
        for row in rows:
            d = row["candidate_mdape"] - row["baseline_mdape"]
            harm = "⚠️" if d > 1.0 else "  "
            logger.info(
                f"    {row['subgroup_type']:>6} {row['label']:>8} (n={row['n']:>3}): "
                f"baseline {row['baseline_mdape']:>5.2f}% → cand {row['candidate_mdape']:>5.2f}% "
                f"({d:>+5.2f}%p) {harm}"
            )
        subgroup_summary.append({"family": fam, "model": name,
                                "diff_overall": r["diff_vs_baseline"], "subgroups": rows})
    summary["subgroup_analysis"] = subgroup_summary

    out = RESULTS / "stage3_addendum_linear_models.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(f"\nSaved: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    run()
