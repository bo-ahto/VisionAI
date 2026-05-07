"""Stage 3 — F4 + spline + Huber 운영 검증 (B 단계).

1. Bootstrap 95% CI (Huber vs OLS)
2. Per-segment 균형 (medium / gallery_tier / 가격대) — Huber 효과
3. 가드레일 검증 (저가 / ink / tier 3 segment)
4. Coefficient 안정성 (sign / 크기) — 100-seed
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import HuberRegressor
from sklearn.model_selection import GroupShuffleSplit

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent.parent
DATA = ROOT / "data" / "curated" / "stage3_1000x100.parquet"
RESULTS = Path(__file__).parent / "results"

TEST_SIZE = 0.20
N_SEEDS = 30


def make_features(df):
    out = df.copy()
    out["log_area"] = np.log(out["area_cm2"].clip(lower=1))
    out["birth_year_centered"] = (
        out["artist_birth_year"] - out["artist_birth_year"].mean()
    )
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


def build_X(df_feat):
    knots = np.percentile(df_feat["log_area"].values, [10, 50, 90])
    sp = restricted_cubic_spline(df_feat["log_area"].values, knots)
    X = pd.DataFrame({
        "const": 1.0,
        "log_area": df_feat["log_area"].values,
        "birth_year_centered": df_feat["birth_year_centered"].values,
        "log_artist_total_works": df_feat["log_artist_total_works"].values,
        "log_area_spline": sp[:, 0],
    })
    return X


def fit_huber(Xtr, ytr, Xte, eps=1.35):
    m = HuberRegressor(epsilon=eps, max_iter=500, alpha=0.0001)
    m.fit(Xtr[:, 1:], ytr)
    pred = Xte[:, 1:] @ m.coef_ + m.intercept_
    return pred, np.concatenate([[m.intercept_], m.coef_])


def fit_ols(Xtr, ytr, Xte):
    beta, *_ = np.linalg.lstsq(Xtr, ytr, rcond=None)
    pred = Xte @ beta
    return pred, beta


def metrics(yte, pred):
    ape = np.abs(np.exp(pred) - np.exp(yte)) / np.exp(yte)
    return {
        "mdape": float(np.median(ape) * 100),
        "w30": float((ape <= 0.30).mean() * 100),
        "w50": float((ape <= 0.50).mean() * 100),
    }


# ─────────────────────────────────────────
# 1. Bootstrap 95% CI
# ─────────────────────────────────────────
def bootstrap_ci(X, y, groups, n_seeds=30, n_boot=500, seed=42):
    X_arr = X.values.astype(float)
    y_arr = y.values.astype(float)

    huber_mdapes, ols_mdapes = [], []
    for s in range(42, 42 + n_seeds):
        gss = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=s)
        tr, te = next(gss.split(X, y, groups))
        Xtr, ytr = X_arr[tr], y_arr[tr]
        Xte, yte = X_arr[te], y_arr[te]

        pred_h, _ = fit_huber(Xtr, ytr, Xte)
        ape_h = np.abs(np.exp(pred_h) - np.exp(yte)) / np.exp(yte)
        huber_mdapes.append(np.median(ape_h) * 100)

        pred_o, _ = fit_ols(Xtr, ytr, Xte)
        ape_o = np.abs(np.exp(pred_o) - np.exp(yte)) / np.exp(yte)
        ols_mdapes.append(np.median(ape_o) * 100)

    rng = np.random.default_rng(seed)

    def boot_ci(arr):
        arr = np.array(arr)
        boot = [np.median(arr[rng.integers(0, len(arr), size=len(arr))]) for _ in range(n_boot)]
        return {
            "median": float(np.median(arr)),
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "ci_lo_95": float(np.percentile(boot, 2.5)),
            "ci_hi_95": float(np.percentile(boot, 97.5)),
        }

    return {"huber": boot_ci(huber_mdapes), "ols": boot_ci(ols_mdapes)}


# ─────────────────────────────────────────
# 2. Per-segment 분석
# ─────────────────────────────────────────
def per_segment(df_feat, X, y, groups, n_seeds=30):
    X_arr = X.values.astype(float)
    y_arr = y.values.astype(float)

    all_yte, all_pred_h, all_pred_o, all_idx = [], [], [], []
    for s in range(42, 42 + n_seeds):
        gss = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=s)
        tr, te = next(gss.split(X, y, groups))
        Xtr, ytr = X_arr[tr], y_arr[tr]
        Xte, yte = X_arr[te], y_arr[te]

        pred_h, _ = fit_huber(Xtr, ytr, Xte)
        pred_o, _ = fit_ols(Xtr, ytr, Xte)
        all_yte.extend(yte.tolist())
        all_pred_h.extend(pred_h.tolist())
        all_pred_o.extend(pred_o.tolist())
        all_idx.extend(te.tolist())

    all_yte = np.array(all_yte)
    all_pred_h = np.array(all_pred_h)
    all_pred_o = np.array(all_pred_o)
    all_idx = np.array(all_idx)
    df_te = df_feat.iloc[all_idx].reset_index(drop=True)

    seg_results = {}

    # Medium
    seg_results["medium"] = {}
    for cat in df_te["medium_category"].unique():
        mask = df_te["medium_category"].values == cat
        if mask.sum() < 30:
            continue
        ape_h = np.abs(np.exp(all_pred_h[mask]) - np.exp(all_yte[mask])) / np.exp(all_yte[mask])
        ape_o = np.abs(np.exp(all_pred_o[mask]) - np.exp(all_yte[mask])) / np.exp(all_yte[mask])
        seg_results["medium"][str(cat)] = {
            "n": int(mask.sum()),
            "ols_mdape": float(np.median(ape_o) * 100),
            "huber_mdape": float(np.median(ape_h) * 100),
            "improvement": float(np.median(ape_o) * 100 - np.median(ape_h) * 100),
        }

    # Gallery tier
    seg_results["gallery_tier"] = {}
    for tier in df_te["gallery_tier"].unique():
        mask = df_te["gallery_tier"].values == tier
        if mask.sum() < 30:
            continue
        ape_h = np.abs(np.exp(all_pred_h[mask]) - np.exp(all_yte[mask])) / np.exp(all_yte[mask])
        ape_o = np.abs(np.exp(all_pred_o[mask]) - np.exp(all_yte[mask])) / np.exp(all_yte[mask])
        seg_results["gallery_tier"][f"tier_{tier}"] = {
            "n": int(mask.sum()),
            "ols_mdape": float(np.median(ape_o) * 100),
            "huber_mdape": float(np.median(ape_h) * 100),
            "improvement": float(np.median(ape_o) * 100 - np.median(ape_h) * 100),
        }

    # Price range
    prices = np.exp(all_yte)
    quantiles = np.quantile(prices, [0.20, 0.40, 0.60, 0.80])
    bin_edges = [-np.inf] + list(quantiles) + [np.inf]
    bin_labels = ["저가 (<20%)", "20-40%", "40-60%", "60-80%", "고가 (>80%)"]
    seg_results["price_range"] = {}
    for label, (lo, hi) in zip(bin_labels, zip(bin_edges[:-1], bin_edges[1:])):
        mask = (prices > lo) & (prices <= hi)
        if mask.sum() < 30:
            continue
        ape_h = np.abs(np.exp(all_pred_h[mask]) - np.exp(all_yte[mask])) / np.exp(all_yte[mask])
        ape_o = np.abs(np.exp(all_pred_o[mask]) - np.exp(all_yte[mask])) / np.exp(all_yte[mask])
        seg_results["price_range"][label] = {
            "n": int(mask.sum()),
            "ols_mdape": float(np.median(ape_o) * 100),
            "huber_mdape": float(np.median(ape_h) * 100),
            "improvement": float(np.median(ape_o) * 100 - np.median(ape_h) * 100),
        }

    return seg_results


# ─────────────────────────────────────────
# 3. Coefficient 안정성 (100-seed)
# ─────────────────────────────────────────
def coef_stability(X, y, groups, n_seeds=100):
    X_arr = X.values.astype(float)
    y_arr = y.values.astype(float)

    feature_names = ["const"] + list(X.columns[1:])
    huber_betas = {fn: [] for fn in feature_names}
    ols_betas = {fn: [] for fn in feature_names}

    for s in range(42, 42 + n_seeds):
        gss = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=s)
        tr, _ = next(gss.split(X, y, groups))
        Xtr, ytr = X_arr[tr], y_arr[tr]

        _, beta_h = fit_huber(Xtr, ytr, Xtr)
        _, beta_o = fit_ols(Xtr, ytr, Xtr)

        for i, fn in enumerate(feature_names):
            huber_betas[fn].append(beta_h[i])
            ols_betas[fn].append(beta_o[i])

    stability = {}
    for fn in feature_names:
        h = np.array(huber_betas[fn])
        o = np.array(ols_betas[fn])
        stability[fn] = {
            "huber": {
                "mean": float(np.mean(h)),
                "std": float(np.std(h)),
                "sign_consistency_pct": float(
                    max(np.sum(h > 0), np.sum(h < 0)) / len(h) * 100
                ),
            },
            "ols": {
                "mean": float(np.mean(o)),
                "std": float(np.std(o)),
                "sign_consistency_pct": float(
                    max(np.sum(o > 0), np.sum(o < 0)) / len(o) * 100
                ),
            },
        }
    return stability


def run():
    df = pd.read_parquet(DATA)
    df_feat = make_features(df)
    y = df_feat["log_price"]
    groups = df_feat["artist_slug"].astype(str).to_numpy()
    X = build_X(df_feat)

    summary = {}

    # 1. Bootstrap CI
    logger.info("=" * 80)
    logger.info("1. Bootstrap 95% CI (Huber vs OLS)")
    logger.info("=" * 80)
    boot = bootstrap_ci(X, y, groups, N_SEEDS)
    for name, c in boot.items():
        logger.info(
            f"  {name.upper():<6}: median {c['median']:.2f}%, "
            f"95% CI [{c['ci_lo_95']:.2f}, {c['ci_hi_95']:.2f}], "
            f"std {c['std']:.2f}"
        )
    summary["1_bootstrap_ci"] = boot

    # 2. Per-segment
    logger.info("\n" + "=" * 80)
    logger.info("2. Per-segment 분석 (Huber 효과)")
    logger.info("=" * 80)
    seg = per_segment(df_feat, X, y, groups, N_SEEDS)
    for seg_name, segments in seg.items():
        logger.info(f"\n  [{seg_name}]")
        logger.info(f"    {'segment':<20} {'n':>6} {'OLS':>8} {'Huber':>8} {'개선':>10}")
        for s_label, m in segments.items():
            logger.info(
                f"    {s_label:<20} {m['n']:>6} "
                f"{m['ols_mdape']:>6.2f}% "
                f"{m['huber_mdape']:>6.2f}% "
                f"{m['improvement']:>+5.2f}%p"
            )
    summary["2_per_segment"] = seg

    # 3. Coefficient stability (100-seed)
    logger.info("\n" + "=" * 80)
    logger.info("3. Coefficient stability (100-seed)")
    logger.info("=" * 80)
    stab = coef_stability(X, y, groups, n_seeds=100)
    logger.info(
        f"\n  {'feature':<26} {'Huber β (std)':>22} {'OLS β (std)':>22} {'sign 일관 %':>15}"
    )
    for fn, s in stab.items():
        logger.info(
            f"  {fn:<26} "
            f"{s['huber']['mean']:>+8.4f} ({s['huber']['std']:.4f})  "
            f"{s['ols']['mean']:>+8.4f} ({s['ols']['std']:.4f})  "
            f"H {s['huber']['sign_consistency_pct']:>3.0f}% / O {s['ols']['sign_consistency_pct']:>3.0f}%"
        )
    summary["3_coef_stability"] = stab

    # Save
    with (RESULTS / "stage3_huber_validation.json").open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(
        f"\nSaved: {(RESULTS / 'stage3_huber_validation.json').relative_to(ROOT)}"
    )


if __name__ == "__main__":
    run()
