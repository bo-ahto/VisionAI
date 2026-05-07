"""Stage 3 Warm-start P3 검증 (코덱스 권고).

1. FE only 재확인 (단독 효과 강건성)
2. History-shrink 버전 (empirical Bayes)
3. Warm-depth bin 분해 (10-14 / 15-24 / 25+)
4. 2024 cutoff 구성분석
5. Artist-cluster bootstrap
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


def empirical_bayes_shrink(train_df):
    """작가별 EB shrinkage μ̂_a = (1-B_a)·ȳ_a + B_a·grand_mean."""
    grand_mean = float(train_df["log_price"].mean())
    grouped = train_df.groupby("artist_slug")["log_price"]
    artist_means = grouped.mean()
    n_per = grouped.size()

    # within-variance (pooled)
    within_var = grouped.var().fillna(0.0)
    df_pool = (n_per - 1).clip(lower=0)
    sigma_w2 = float((within_var * df_pool).sum() / max(df_pool.sum(), 1.0))
    sigma_b2 = float(artist_means.var(ddof=1)) if len(artist_means) > 1 else 0.0

    shrunk = {}
    B_factors = {}
    for a, n_a in n_per.items():
        mean_a = float(artist_means[a])
        if sigma_b2 > 0:
            B_a = sigma_w2 / (sigma_w2 + n_a * sigma_b2)
        else:
            B_a = 1.0
        shrunk[a] = (1 - B_a) * mean_a + B_a * grand_mean
        B_factors[a] = B_a
    return shrunk, grand_mean, sigma_w2, sigma_b2, B_factors


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


def evaluate_models(df_feat, y, train_mask, test_mask, warm_artists,
                    train_log_price_mean, eb_shrunk):
    """Baseline / FE only / Combined (단순 history) / Combined-shrunk."""
    warm_test_mask = test_mask & df_feat["artist_slug"].isin(warm_artists)

    # Baseline
    X_b = build_X_baseline(df_feat)
    Xtr_b = X_b[train_mask.values].values.astype(float)
    Xte_b = X_b[warm_test_mask.values].values.astype(float)
    ytr = y[train_mask].values.astype(float)
    yte = y[warm_test_mask].values.astype(float)
    pred_baseline = fit_predict(Xtr_b, ytr, Xte_b)

    # FE only
    X_fe = add_artist_fe(X_b, df_feat, warm_artists)
    Xtr_fe = X_fe[train_mask.values].values.astype(float)
    Xte_fe = X_fe[warm_test_mask.values].values.astype(float)
    pred_fe = fit_predict(Xtr_fe, ytr, Xte_fe)

    # Time weights for combined variants
    max_yr = df_feat["year_made"].max()
    weights = time_weights(df_feat[train_mask]["year_made"].values, max_yr, half_life=2)

    # Combined (단순 history)
    train_df = df_feat[train_mask].copy()
    artist_avg = train_df.groupby("artist_slug")["log_price"].mean().to_dict()
    history_simple = df_feat["artist_slug"].map(artist_avg).fillna(train_log_price_mean).values
    X_c = X_fe.copy()
    X_c["recent_avg_log_price"] = history_simple
    Xtr_c = X_c[train_mask.values].values.astype(float)
    Xte_c = X_c[warm_test_mask.values].values.astype(float)
    pred_combined = fit_predict(Xtr_c, ytr, Xte_c, weights=weights)

    # Combined-shrunk (EB)
    history_shrunk = df_feat["artist_slug"].map(eb_shrunk).fillna(train_log_price_mean).values
    X_cs = X_fe.copy()
    X_cs["recent_avg_log_price"] = history_shrunk
    Xtr_cs = X_cs[train_mask.values].values.astype(float)
    Xte_cs = X_cs[warm_test_mask.values].values.astype(float)
    pred_combined_shrunk = fit_predict(Xtr_cs, ytr, Xte_cs, weights=weights)

    return {
        "yte": yte,
        "preds": {
            "baseline": pred_baseline,
            "fe_only": pred_fe,
            "combined": pred_combined,
            "combined_shrunk": pred_combined_shrunk,
        },
        "test_idx": np.where(warm_test_mask.values)[0],
    }


# ─────────────────────────────────────
# 1. FE only 재확인 + Rolling
# ─────────────────────────────────────
def fe_only_rolling(df_feat, y):
    cutoffs = [2020, 2021, 2022, 2023, 2024]
    rows = []
    for c in cutoffs:
        train_mask = df_feat["year_made"] <= c
        test_mask = ~train_mask
        if train_mask.sum() < 100 or test_mask.sum() < 30:
            continue
        train_counts = Counter(df_feat[train_mask]["artist_slug"])
        warm_artists = {a for a, n in train_counts.items() if n >= WARM_THRESHOLD}
        warm_test_mask = test_mask & df_feat["artist_slug"].isin(warm_artists)
        if warm_test_mask.sum() < 8:
            continue

        train_df = df_feat[train_mask].copy()
        eb, gm, _, _, _ = empirical_bayes_shrink(train_df)

        result = evaluate_models(df_feat, y, train_mask, test_mask, warm_artists, gm, eb)
        yte = result["yte"]
        rows.append({
            "cutoff": int(c),
            "n_train": int(train_mask.sum()),
            "n_test_warm": int(warm_test_mask.sum()),
            "n_warm_artists": int(len(warm_artists)),
            "baseline": mdape(yte, result["preds"]["baseline"]),
            "fe_only": mdape(yte, result["preds"]["fe_only"]),
            "combined": mdape(yte, result["preds"]["combined"]),
            "combined_shrunk": mdape(yte, result["preds"]["combined_shrunk"]),
        })
    return rows


# ─────────────────────────────────────
# 3. Warm-depth bin
# ─────────────────────────────────────
def depth_bin_decomp(df_feat, y, train_mask, test_mask, warm_artists,
                     train_log_price_mean, eb_shrunk):
    train_counts = Counter(df_feat[train_mask]["artist_slug"])
    bins = {"10-14": [], "15-24": [], "25+": []}
    for a in warm_artists:
        n = train_counts[a]
        if n <= 14:
            bins["10-14"].append(a)
        elif n <= 24:
            bins["15-24"].append(a)
        else:
            bins["25+"].append(a)

    res = evaluate_models(df_feat, y, train_mask, test_mask, warm_artists,
                          train_log_price_mean, eb_shrunk)
    yte = res["yte"]
    test_artists = df_feat.iloc[res["test_idx"]]["artist_slug"].values

    rows = []
    for label, artists in bins.items():
        mask = np.isin(test_artists, list(artists))
        if mask.sum() < 3:
            rows.append({"depth_bin": label, "n_artists": len(artists),
                         "n_test": int(mask.sum()), "skip": True})
            continue
        rows.append({
            "depth_bin": label,
            "n_artists": len(artists),
            "n_test": int(mask.sum()),
            "baseline": mdape(yte[mask], res["preds"]["baseline"][mask]),
            "fe_only": mdape(yte[mask], res["preds"]["fe_only"][mask]),
            "combined": mdape(yte[mask], res["preds"]["combined"][mask]),
            "combined_shrunk": mdape(yte[mask], res["preds"]["combined_shrunk"][mask]),
        })
    return rows


# ─────────────────────────────────────
# 4. 2024 cutoff composition
# ─────────────────────────────────────
def composition_2024(df_feat):
    train23 = df_feat["year_made"] <= 2023
    train24 = df_feat["year_made"] <= 2024
    counts23 = Counter(df_feat[train23]["artist_slug"])
    counts24 = Counter(df_feat[train24]["artist_slug"])
    warm23 = {a for a, n in counts23.items() if n >= WARM_THRESHOLD}
    warm24 = {a for a, n in counts24.items() if n >= WARM_THRESHOLD}
    new_warm = warm24 - warm23

    test23 = df_feat[~train23 & df_feat["artist_slug"].isin(warm23)]
    test24 = df_feat[~train24 & df_feat["artist_slug"].isin(warm24)]

    def desc(test):
        if len(test) == 0:
            return {}
        return {
            "n": int(len(test)),
            "price_median_krw": float(test["price_krw"].median()),
            "price_mean_krw": float(test["price_krw"].mean()),
            "n_unique_artists": int(test["artist_slug"].nunique()),
            "year_made_median": float(test["year_made"].median()),
        }

    return {
        "warm23_artists": int(len(warm23)),
        "warm24_artists": int(len(warm24)),
        "new_warm_in_2024": int(len(new_warm)),
        "test_2023_set": desc(test23),
        "test_2024_set": desc(test24),
        "test_overlap_artists": int(len(set(test23["artist_slug"]) & set(test24["artist_slug"]))),
    }


# ─────────────────────────────────────
# 5. Artist-cluster bootstrap
# ─────────────────────────────────────
def cluster_bootstrap(df_feat, y, train_mask, test_mask, warm_artists,
                      train_log_price_mean, eb_shrunk, n_boot=500, seed=42):
    rng = np.random.default_rng(seed)
    res = evaluate_models(df_feat, y, train_mask, test_mask, warm_artists,
                          train_log_price_mean, eb_shrunk)
    yte = res["yte"]
    test_idx = res["test_idx"]
    test_artists = df_feat.iloc[test_idx]["artist_slug"].values
    unique_artists = list(set(test_artists))

    def diff_for(model_a, model_b, sample_artists):
        mask = np.isin(test_artists, sample_artists)
        if mask.sum() < 3:
            return np.nan
        return mdape(yte[mask], res["preds"][model_b][mask]) - \
               mdape(yte[mask], res["preds"][model_a][mask])

    diffs = {"fe_only_vs_baseline": [], "combined_vs_baseline": [],
             "combined_shrunk_vs_baseline": []}
    for _ in range(n_boot):
        sample = rng.choice(unique_artists, size=len(unique_artists), replace=True)
        diffs["fe_only_vs_baseline"].append(diff_for("baseline", "fe_only", sample))
        diffs["combined_vs_baseline"].append(diff_for("baseline", "combined", sample))
        diffs["combined_shrunk_vs_baseline"].append(diff_for("baseline", "combined_shrunk", sample))

    out = {}
    for k, vals in diffs.items():
        v = np.array(vals)
        v = v[~np.isnan(v)]
        out[k] = {
            "n_boot": int(len(v)),
            "mean": float(np.mean(v)),
            "ci_lo_95": float(np.percentile(v, 2.5)),
            "ci_hi_95": float(np.percentile(v, 97.5)),
            "p_below_zero": float((v < 0).mean()),
        }
    return out


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
    train_df = df_feat[train_mask].copy()
    eb, gm, sw2, sb2, _ = empirical_bayes_shrink(train_df)

    logger.info("=" * 80)
    logger.info("Stage 3 Warm-start P3 검증 (코덱스 권고)")
    logger.info("=" * 80)
    logger.info(f"EB params: grand_mean={gm:.3f}, σ_w²={sw2:.3f}, σ_b²={sb2:.3f}, "
                f"avg_B={np.mean(list(eb.values())):.3f}")

    summary = {"eb_params": {"grand_mean": gm, "sigma_w2": sw2, "sigma_b2": sb2}}

    # 1+2. 4-model rolling
    logger.info("\n--- 1+2. 4-model rolling (Baseline / FE only / Combined / Combined-shrunk) ---")
    rolling = fe_only_rolling(df_feat, y)
    logger.info(f"\n  {'cutoff':>6} {'n_te':>5} {'baseline':>9} {'fe_only':>9} {'combined':>9} {'comb_shrunk':>12}")
    for r in rolling:
        logger.info(
            f"  {r['cutoff']:>6} {r['n_test_warm']:>5} "
            f"{r['baseline']:>7.2f}% {r['fe_only']:>7.2f}% "
            f"{r['combined']:>7.2f}% {r['combined_shrunk']:>10.2f}%"
        )
    summary["1_4model_rolling"] = rolling

    # 3. Warm-depth bin (≤2023)
    logger.info("\n--- 3. Warm-depth bin 분해 (≤2023, n=44) ---")
    depth = depth_bin_decomp(df_feat, y, train_mask, test_mask, warm_artists, gm, eb)
    logger.info(f"\n  {'depth':>8} {'n_art':>5} {'n_te':>5} {'baseline':>9} {'fe_only':>9} {'combined':>9} {'shrunk':>9}")
    for d in depth:
        if d.get("skip"):
            logger.info(f"  {d['depth_bin']:>8} {d['n_artists']:>5} {d['n_test']:>5}  (skip, n<3)")
            continue
        logger.info(
            f"  {d['depth_bin']:>8} {d['n_artists']:>5} {d['n_test']:>5} "
            f"{d['baseline']:>7.2f}% {d['fe_only']:>7.2f}% "
            f"{d['combined']:>7.2f}% {d['combined_shrunk']:>7.2f}%"
        )
    summary["3_depth_bins"] = depth

    # 4. 2024 cutoff composition
    logger.info("\n--- 4. 2024 cutoff 구성분석 ---")
    comp = composition_2024(df_feat)
    logger.info(f"  warm artists: 2023→{comp['warm23_artists']} / 2024→{comp['warm24_artists']} (신규 +{comp['new_warm_in_2024']})")
    logger.info(f"  test 2023 set: {comp['test_2023_set']}")
    logger.info(f"  test 2024 set: {comp['test_2024_set']}")
    logger.info(f"  test 작가 overlap: {comp['test_overlap_artists']}명")
    summary["4_composition_2024"] = comp

    # 5. Artist-cluster bootstrap (≤2023)
    logger.info("\n--- 5. Artist-cluster bootstrap (≤2023, 500 iters) ---")
    boot = cluster_bootstrap(df_feat, y, train_mask, test_mask, warm_artists, gm, eb, n_boot=500)
    for k, v in boot.items():
        logger.info(
            f"  {k}: mean {v['mean']:+.2f}%p, 95% CI [{v['ci_lo_95']:+.2f}, {v['ci_hi_95']:+.2f}], "
            f"P(<0)={v['p_below_zero']:.1%}"
        )
    summary["5_cluster_bootstrap"] = boot

    out = RESULTS / "stage3_warm_p3_validation.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(f"\nSaved: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    run()
