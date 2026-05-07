"""Stage 3 FE only 추가 검증 (코덱스 권고).

cutoff 2024 기준으로:
1. Artist-cluster bootstrap n_boot 2000 으로 확장
2. Seed 안정성 (10 seed 평균 + std)
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


def make_features(df):
    out = df.copy()
    out["log_area"] = np.log(out["area_cm2"].clip(lower=1))
    out["birth_year_centered"] = out["artist_birth_year"] - out["artist_birth_year"].mean()
    out["log_artist_total_works"] = np.log1p(out["artist_total_works"])
    out["log_price"] = np.log(out["price_krw"].clip(lower=1))
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


def fit_predict(Xtr, ytr, Xte, eps=1.35):
    m = HuberRegressor(epsilon=eps, max_iter=2000, alpha=0.0001)
    m.fit(Xtr[:, 1:], ytr)
    return Xte[:, 1:] @ m.coef_ + m.intercept_


def mdape(yte, pred):
    return float(np.median(np.abs(np.exp(pred) - np.exp(yte)) / np.exp(yte)) * 100)


def cluster_bootstrap_diff(yte, pred_a, pred_b, test_artists, n_boot, seed):
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
        "p_below_zero": float((diffs < 0).mean()),
    }


def setup(df_feat, y, cutoff=2024):
    train_mask = df_feat["year_made"] <= cutoff
    test_mask = ~train_mask
    train_counts = Counter(df_feat[train_mask]["artist_slug"])
    warm_artists = {a for a, n in train_counts.items() if n >= WARM_THRESHOLD}
    warm_test_mask = test_mask & df_feat["artist_slug"].isin(warm_artists)

    X_b = build_X_baseline(df_feat)
    X_fe = add_artist_fe(X_b, df_feat, warm_artists)

    Xtr_b = X_b[train_mask.values].values.astype(float)
    Xte_b = X_b[warm_test_mask.values].values.astype(float)
    Xtr_fe = X_fe[train_mask.values].values.astype(float)
    Xte_fe = X_fe[warm_test_mask.values].values.astype(float)
    ytr = y[train_mask].values.astype(float)
    yte = y[warm_test_mask].values.astype(float)
    test_artists = df_feat[warm_test_mask]["artist_slug"].values

    pred_b = fit_predict(Xtr_b, ytr, Xte_b)
    pred_fe = fit_predict(Xtr_fe, ytr, Xte_fe)
    return yte, pred_b, pred_fe, test_artists, int(warm_test_mask.sum()), int(len(set(test_artists)))


def run():
    df = pd.read_parquet(DATA)
    df_feat = make_features(df)
    y = df_feat["log_price"]

    summary = {}

    logger.info("=" * 80)
    logger.info("Stage 3 FE only 추가 검증 (코덱스 권고)")
    logger.info("=" * 80)

    # 1. cutoff 2024 + bootstrap n=2000 (seed=42)
    yte24, pb24, pfe24, ta24, n24, na24 = setup(df_feat, y, cutoff=2024)
    base24 = mdape(yte24, pb24)
    fe24 = mdape(yte24, pfe24)
    logger.info(f"\n[cutoff 2024]  n_test={n24}  n_artists={na24}")
    logger.info(f"  baseline MdAPE: {base24:.2f}% / fe_only MdAPE: {fe24:.2f}% (diff {fe24 - base24:+.2f}%p)")

    boot24_2000 = cluster_bootstrap_diff(yte24, pfe24, pb24, ta24, n_boot=2000, seed=42)
    logger.info(
        f"\n--- 1. Bootstrap n=2000 (cutoff 2024, seed=42) ---\n"
        f"  diff mean: {boot24_2000['mean']:+.2f}%p\n"
        f"  95% CI: [{boot24_2000['ci_lo_95']:+.2f}, {boot24_2000['ci_hi_95']:+.2f}]\n"
        f"  P(<0) = {boot24_2000['p_below_zero']:.1%}"
    )
    summary["1_bootstrap_n2000"] = boot24_2000

    # 2. Seed 안정성 (10 seed × n_boot=500)
    logger.info("\n--- 2. Seed 안정성 (10 seed × n=500, cutoff 2024) ---")
    seed_results = []
    for s in range(10, 110, 10):
        b = cluster_bootstrap_diff(yte24, pfe24, pb24, ta24, n_boot=500, seed=s)
        seed_results.append({
            "seed": s,
            "mean": b["mean"],
            "ci_lo_95": b["ci_lo_95"],
            "ci_hi_95": b["ci_hi_95"],
            "p_below_zero": b["p_below_zero"],
        })
        logger.info(
            f"  seed {s:>3}: mean {b['mean']:+6.2f}%p, "
            f"CI [{b['ci_lo_95']:+6.2f}, {b['ci_hi_95']:+6.2f}], P<0={b['p_below_zero']:.1%}"
        )

    means = np.array([r["mean"] for r in seed_results])
    p0s = np.array([r["p_below_zero"] for r in seed_results])
    logger.info(
        f"\n  종합 (10 seed): mean diff {means.mean():+.2f}%p (std {means.std():.3f}), "
        f"P<0 {p0s.mean():.1%} (std {p0s.std():.3f})"
    )
    summary["2_seed_stability"] = {
        "results": seed_results,
        "mean_diff_avg": float(means.mean()),
        "mean_diff_std": float(means.std()),
        "p_below_zero_avg": float(p0s.mean()),
        "p_below_zero_std": float(p0s.std()),
    }

    # 3. cutoff 2022/2023 도 동일 seed 안정성 (간이)
    logger.info("\n--- 3. Cutoff 별 seed 안정성 종합 (10 seed × n=500) ---")
    for c in [2022, 2023, 2024]:
        try:
            yte_c, pb_c, pfe_c, ta_c, n_c, na_c = setup(df_feat, y, cutoff=c)
        except Exception:
            continue
        means_c = []
        for s in range(10, 110, 10):
            b = cluster_bootstrap_diff(yte_c, pfe_c, pb_c, ta_c, n_boot=500, seed=s)
            means_c.append(b["mean"])
        means_c = np.array(means_c)
        logger.info(
            f"  cutoff {c} (n_te={n_c}, art={na_c}): "
            f"mean {means_c.mean():+5.2f}%p (std {means_c.std():.3f}), "
            f"all neg = {(means_c < 0).all()}"
        )
    summary["3_per_cutoff_stability"] = "see logs"

    out = RESULTS / "stage3_warm_fe_robustness.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(f"\nSaved: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    run()
