"""Stage 3 추가 검증 (final report 진입 전).

1. Warm threshold 정밀 fine-tuning (1, 2, 3, 5, 7, 10, 15)
2. Time + warm threshold 결합
3. Bootstrap 95% CI (OLS / ME / two-track)
4. Per-segment (medium / tier / 가격대) 균형
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit, ShuffleSplit

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent.parent
DATA = ROOT / "data" / "curated" / "stage3_1000x100.parquet"
RESULTS = Path(__file__).parent / "results"

N_SEEDS = 30
TEST_SIZE = 0.20


def make_features(df):
    out = df.copy()
    out["log_area"] = np.log(out["area_cm2"].clip(lower=1))
    out["birth_year_centered"] = (
        out["artist_birth_year"] - out["artist_birth_year"].mean()
    )
    out["log_artist_total_works"] = np.log1p(out["artist_total_works"])
    out["log_price"] = np.log(out["price_krw"].clip(lower=1))
    return out


def ols_fit(X, y):
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta, y - X @ beta


def fit_random_intercept(X, y, groups):
    beta, resid = ols_fit(X, y)
    for _ in range(20):
        unique_g, inv = np.unique(groups, return_inverse=True)
        u_j = np.zeros(len(unique_g))
        for j in range(len(unique_g)):
            mask = inv == j
            u_j[j] = resid[mask].mean()
        y_adj = y - u_j[inv]
        beta_new, _ = ols_fit(X, y_adj)
        if np.max(np.abs(beta_new - beta)) < 1e-5:
            break
        beta = beta_new
        resid = y - X @ beta - u_j[inv]
    unique_g, inv = np.unique(groups, return_inverse=True)
    u_j = np.zeros(len(unique_g))
    for j in range(len(unique_g)):
        mask = inv == j
        u_j[j] = (y[mask] - X[mask] @ beta).mean()
    return beta, u_j, unique_g


def predict_re(Xte, te_groups, beta, u_j, train_groups):
    pred = Xte @ beta
    g_to_u = dict(zip(train_groups, u_j))
    for i, g in enumerate(te_groups):
        if g in g_to_u:
            pred[i] += g_to_u[g]
    return pred


def metrics(yte, pred):
    ape = np.abs(np.exp(pred) - np.exp(yte)) / np.exp(yte)
    return {
        "mdape": float(np.median(ape) * 100),
        "w30": float((ape <= 0.30).mean() * 100),
        "w50": float((ape <= 0.50).mean() * 100),
    }


def build_X(df_feat):
    X_cols = ["log_area", "birth_year_centered", "log_artist_total_works"]
    X = df_feat[X_cols].copy()
    X.insert(0, "const", 1.0)
    return X


# ───────────────────────────────────────
# 1. Warm threshold 정밀 fine-tuning
# ───────────────────────────────────────
def warm_threshold_fine(df_feat, y, groups, n_seeds=30):
    X = build_X(df_feat)
    thresholds = [1, 2, 3, 5, 7, 10, 15]
    results = {t: {"warm_mdape": [], "warm_n": [],
                   "cold_mdape": [], "cold_n": []} for t in thresholds}

    for seed in range(42, 42 + n_seeds):
        ss = ShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=seed)
        tr, te = next(ss.split(X, y))
        Xtr = X.iloc[tr].values.astype(float)
        ytr = y.iloc[tr].values.astype(float)
        Xte = X.iloc[te].values.astype(float)
        yte = y.iloc[te].values.astype(float)
        gtr = groups[tr]
        gte = groups[te]

        beta_me, u_j, ug = fit_random_intercept(Xtr, ytr, gtr)
        train_counts = Counter(gtr)

        for t in thresholds:
            warm_mask = np.array([train_counts.get(g, 0) >= t for g in gte])
            if warm_mask.sum() < 10 or (~warm_mask).sum() < 10:
                continue

            pred_warm = predict_re(Xte[warm_mask], gte[warm_mask], beta_me, u_j, ug)
            m_warm = metrics(yte[warm_mask], pred_warm)
            results[t]["warm_mdape"].append(m_warm["mdape"])
            results[t]["warm_n"].append(int(warm_mask.sum()))

            pred_cold = Xte[~warm_mask] @ beta_me
            m_cold = metrics(yte[~warm_mask], pred_cold)
            results[t]["cold_mdape"].append(m_cold["mdape"])
            results[t]["cold_n"].append(int((~warm_mask).sum()))

    summary = {}
    for t in thresholds:
        if results[t]["warm_mdape"]:
            wn = np.mean(results[t]["warm_n"])
            cn = np.mean(results[t]["cold_n"])
            warm_total_n = wn + cn
            warm_pct = wn / warm_total_n * 100
            summary[f"min_works_{t}"] = {
                "warm_mdape_mean": float(np.mean(results[t]["warm_mdape"])),
                "warm_mdape_std": float(np.std(results[t]["warm_mdape"])),
                "warm_n_avg": float(wn),
                "cold_mdape_mean": float(np.mean(results[t]["cold_mdape"])),
                "cold_mdape_std": float(np.std(results[t]["cold_mdape"])),
                "cold_n_avg": float(cn),
                "warm_ratio_pct": float(warm_pct),
            }
    return summary


# ───────────────────────────────────────
# 2. Time + warm threshold 결합
# ───────────────────────────────────────
def time_warm_combined(df_feat, y, groups):
    X = build_X(df_feat)
    splits = {
        "≤2022 (현실)": df_feat["year_made"] <= 2022,
        "≤2023": df_feat["year_made"] <= 2023,
    }
    thresholds = [3, 5, 10]
    results = {}

    for split_name, train_mask in splits.items():
        if train_mask.sum() < 50:
            continue
        Xtr = X[train_mask].values.astype(float)
        ytr = y[train_mask].values.astype(float)
        Xte = X[~train_mask].values.astype(float)
        yte = y[~train_mask].values.astype(float)
        gtr = groups[train_mask.values]
        gte = groups[(~train_mask).values]

        beta_me, u_j, ug = fit_random_intercept(Xtr, ytr, gtr)
        train_counts = Counter(gtr)

        results[split_name] = {}
        for t in thresholds:
            warm_mask = np.array([train_counts.get(g, 0) >= t for g in gte])
            if warm_mask.sum() < 10:
                continue

            pred_warm = predict_re(Xte[warm_mask], gte[warm_mask], beta_me, u_j, ug)
            m_warm = metrics(yte[warm_mask], pred_warm)
            pred_cold = Xte[~warm_mask] @ beta_me
            m_cold = metrics(yte[~warm_mask], pred_cold) if (~warm_mask).sum() > 0 else None

            # Combined two-track
            all_pred = np.concatenate([pred_warm, pred_cold])
            all_yte = np.concatenate([yte[warm_mask], yte[~warm_mask]])
            m_two_track = metrics(all_yte, all_pred)

            results[split_name][f"min_works_{t}"] = {
                "warm_mdape": m_warm["mdape"],
                "warm_n": int(warm_mask.sum()),
                "cold_mdape": m_cold["mdape"] if m_cold else None,
                "cold_n": int((~warm_mask).sum()),
                "two_track_mdape": m_two_track["mdape"],
                "two_track_w30": m_two_track["w30"],
                "two_track_w50": m_two_track["w50"],
            }
    return results


# ───────────────────────────────────────
# 3. Bootstrap 95% CI
# ───────────────────────────────────────
def bootstrap_ci(df_feat, y, groups, n_boot=500, seed=42):
    X = build_X(df_feat)
    rng = np.random.default_rng(seed)

    # 1. LAO 30-seed → bootstrap on metrics
    lao_mdapes_ols = []
    lao_mdapes_me = []
    for s in range(42, 72):
        gss = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=s)
        tr, te = next(gss.split(X, y, groups))
        Xtr = X.iloc[tr].values.astype(float)
        ytr = y.iloc[tr].values.astype(float)
        Xte = X.iloc[te].values.astype(float)
        yte = y.iloc[te].values.astype(float)

        beta_ols, _ = ols_fit(Xtr, ytr)
        pred_ols = Xte @ beta_ols
        ape = np.abs(np.exp(pred_ols) - np.exp(yte)) / np.exp(yte)
        lao_mdapes_ols.append(np.median(ape) * 100)

        beta_me, u_j, ug = fit_random_intercept(Xtr, ytr, groups[tr])
        pred_me = predict_re(Xte, groups[te], beta_me, u_j, ug)
        ape_me = np.abs(np.exp(pred_me) - np.exp(yte)) / np.exp(yte)
        lao_mdapes_me.append(np.median(ape_me) * 100)

    # Bootstrap CI on the seed metrics
    def ci_from_array(arr, n_boot=n_boot):
        boot_medians = []
        arr = np.array(arr)
        for _ in range(n_boot):
            idx = rng.integers(0, len(arr), size=len(arr))
            boot_medians.append(np.median(arr[idx]))
        return {
            "median": float(np.median(arr)),
            "ci_lo_95": float(np.percentile(boot_medians, 2.5)),
            "ci_hi_95": float(np.percentile(boot_medians, 97.5)),
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
        }

    return {
        "ols_lao": ci_from_array(lao_mdapes_ols),
        "me_lao": ci_from_array(lao_mdapes_me),
    }


# ───────────────────────────────────────
# 4. Per-segment 균형 (medium / tier / 가격대)
# ───────────────────────────────────────
def per_segment_eval(df_feat, y, groups, n_seeds=30):
    X = build_X(df_feat)
    seg_metrics = {
        "medium_category": {},
        "gallery_tier": {},
        "price_range": {},
    }

    all_pred_ols = []
    all_pred_me = []
    all_yte = []
    all_idx_te = []

    for s in range(42, 42 + n_seeds):
        gss = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=s)
        tr, te = next(gss.split(X, y, groups))
        Xtr = X.iloc[tr].values.astype(float)
        ytr = y.iloc[tr].values.astype(float)
        Xte = X.iloc[te].values.astype(float)
        yte = y.iloc[te].values.astype(float)

        beta_ols, _ = ols_fit(Xtr, ytr)
        pred_ols = Xte @ beta_ols
        beta_me, u_j, ug = fit_random_intercept(Xtr, ytr, groups[tr])
        pred_me = predict_re(Xte, groups[te], beta_me, u_j, ug)

        all_pred_ols.extend(pred_ols.tolist())
        all_pred_me.extend(pred_me.tolist())
        all_yte.extend(yte.tolist())
        all_idx_te.extend(te.tolist())

    all_pred_ols = np.array(all_pred_ols)
    all_pred_me = np.array(all_pred_me)
    all_yte = np.array(all_yte)
    all_idx_te = np.array(all_idx_te)

    # Medium category
    df_te_meta = df_feat.iloc[all_idx_te]
    for cat in df_te_meta["medium_category"].unique():
        mask = df_te_meta["medium_category"].values == cat
        if mask.sum() < 30:
            continue
        ape_ols = np.abs(np.exp(all_pred_ols[mask]) - np.exp(all_yte[mask])) / np.exp(all_yte[mask])
        ape_me = np.abs(np.exp(all_pred_me[mask]) - np.exp(all_yte[mask])) / np.exp(all_yte[mask])
        seg_metrics["medium_category"][str(cat)] = {
            "n": int(mask.sum()),
            "ols_mdape": float(np.median(ape_ols) * 100),
            "me_mdape": float(np.median(ape_me) * 100),
        }

    # Gallery tier
    for tier in df_te_meta["gallery_tier"].unique():
        mask = df_te_meta["gallery_tier"].values == tier
        if mask.sum() < 30:
            continue
        ape_ols = np.abs(np.exp(all_pred_ols[mask]) - np.exp(all_yte[mask])) / np.exp(all_yte[mask])
        ape_me = np.abs(np.exp(all_pred_me[mask]) - np.exp(all_yte[mask])) / np.exp(all_yte[mask])
        seg_metrics["gallery_tier"][f"tier_{tier}"] = {
            "n": int(mask.sum()),
            "ols_mdape": float(np.median(ape_ols) * 100),
            "me_mdape": float(np.median(ape_me) * 100),
        }

    # Price range
    prices = np.exp(all_yte)
    quantiles = np.quantile(prices, [0.20, 0.40, 0.60, 0.80])
    bin_edges = [-np.inf] + list(quantiles) + [np.inf]
    bin_labels = ["저가 (<20%)", "20-40%", "40-60%", "60-80%", "고가 (>80%)"]
    for label, (lo, hi) in zip(bin_labels, zip(bin_edges[:-1], bin_edges[1:])):
        mask = (prices > lo) & (prices <= hi)
        if mask.sum() < 30:
            continue
        ape_ols = np.abs(np.exp(all_pred_ols[mask]) - np.exp(all_yte[mask])) / np.exp(all_yte[mask])
        ape_me = np.abs(np.exp(all_pred_me[mask]) - np.exp(all_yte[mask])) / np.exp(all_yte[mask])
        seg_metrics["price_range"][label] = {
            "n": int(mask.sum()),
            "ols_mdape": float(np.median(ape_ols) * 100),
            "me_mdape": float(np.median(ape_me) * 100),
        }
    return seg_metrics


def run():
    df = pd.read_parquet(DATA)
    df_feat = make_features(df)
    y = df_feat["log_price"]
    groups = df_feat["artist_slug"].astype(str).to_numpy()

    summary = {}

    logger.info("=" * 80)
    logger.info("1. Warm threshold 정밀 fine-tuning (1~15)")
    logger.info("=" * 80)
    wt_fine = warm_threshold_fine(df_feat, y, groups, N_SEEDS)
    logger.info(
        f"\n  {'min_works':<14} {'warm MdAPE':>14} {'cold MdAPE':>14} {'warm비율':>10}"
    )
    for label, m in wt_fine.items():
        logger.info(
            f"  {label:<14} "
            f"{m['warm_mdape_mean']:>6.2f}±{m['warm_mdape_std']:>4.2f}% "
            f"{m['cold_mdape_mean']:>6.2f}±{m['cold_mdape_std']:>4.2f}% "
            f"{m['warm_ratio_pct']:>7.1f}%"
        )
    summary["1_warm_threshold_fine"] = wt_fine

    logger.info("\n" + "=" * 80)
    logger.info("2. Time + warm threshold 결합 (실제 운영 시뮬레이션)")
    logger.info("=" * 80)
    tw = time_warm_combined(df_feat, y, groups)
    for split_name, ms in tw.items():
        logger.info(f"\n  [{split_name}]")
        for thr_label, m in ms.items():
            cold_str = f"{m['cold_mdape']:.2f}%" if m['cold_mdape'] else "n=0"
            logger.info(
                f"    {thr_label}: warm={m['warm_n']}({m['warm_mdape']:.2f}%) / "
                f"cold={m['cold_n']}({cold_str}) / "
                f"통합={m['two_track_mdape']:.2f}%"
            )
    summary["2_time_warm"] = tw

    logger.info("\n" + "=" * 80)
    logger.info("3. Bootstrap 95% CI (LAO 30-seed 기준)")
    logger.info("=" * 80)
    boot = bootstrap_ci(df_feat, y, groups)
    for name, c in boot.items():
        logger.info(
            f"  {name}: median {c['median']:.2f}%, "
            f"95% CI [{c['ci_lo_95']:.2f}, {c['ci_hi_95']:.2f}]"
        )
    summary["3_bootstrap_ci"] = boot

    logger.info("\n" + "=" * 80)
    logger.info("4. Per-segment 균형")
    logger.info("=" * 80)
    seg = per_segment_eval(df_feat, y, groups, N_SEEDS)
    for seg_name, segments in seg.items():
        logger.info(f"\n  [{seg_name}]")
        logger.info(
            f"    {'segment':<22} {'n':>6} {'OLS':>8} {'ME':>8} {'Δ':>7}"
        )
        for s_label, m in segments.items():
            diff = m["me_mdape"] - m["ols_mdape"]
            logger.info(
                f"    {s_label:<22} {m['n']:>6} "
                f"{m['ols_mdape']:>6.2f}% "
                f"{m['me_mdape']:>6.2f}% "
                f"{diff:>+5.2f}%p"
            )
    summary["4_per_segment"] = seg

    with (RESULTS / "stage3_extra_validation.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(
        f"\nSaved: {(RESULTS / 'stage3_extra_validation.json').relative_to(ROOT)}"
    )


if __name__ == "__main__":
    run()
