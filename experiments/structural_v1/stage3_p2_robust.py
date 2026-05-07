"""Stage 3 — 코덱스 P2 (robust / weighted / transform).

1. Robust regression (Huber loss)
2. Heteroskedastic weighting (가격대별 weight)
3. Target transform variants (Box-Cox, Yeo-Johnson)
4. Predicted bias-corrected back-transform

baseline: F4 + log_area spline (-1.34%p, P1 winner)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import optimize, stats
from sklearn.linear_model import HuberRegressor, LinearRegression
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import PowerTransformer

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


def restricted_cubic_spline(x, knots):
    k = len(knots)
    last_k, pre_last_k = knots[-1], knots[-2]
    denom = (last_k - knots[0]) ** 2
    out = []
    for i in range(k - 2):
        ti = knots[i]
        cube = lambda u: np.maximum(u, 0) ** 3
        spline = (
            cube(x - ti)
            - cube(x - pre_last_k) * (last_k - ti) / (last_k - pre_last_k)
            + cube(x - last_k) * (pre_last_k - ti) / (last_k - pre_last_k)
        )
        out.append(spline / denom)
    return np.column_stack(out)


def build_X_baseline(df_feat):
    """F4 + log_area spline (P1 winner)."""
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


def metrics(yte, pred):
    ape = np.abs(np.exp(pred) - np.exp(yte)) / np.exp(yte)
    return {
        "mdape": float(np.median(ape) * 100),
        "w30": float((ape <= 0.30).mean() * 100),
        "w50": float((ape <= 0.50).mean() * 100),
    }


# ─────────────────────────────────────────
# 실험 함수들
# ─────────────────────────────────────────
def fit_ols(Xtr, ytr):
    beta, *_ = np.linalg.lstsq(Xtr, ytr, rcond=None)
    return lambda Xte: Xte @ beta


def fit_huber(Xtr, ytr):
    """Huber regression (robust to outliers)."""
    m = HuberRegressor(epsilon=1.35, max_iter=500, alpha=0.0)
    m.fit(Xtr[:, 1:], ytr)  # exclude const
    return lambda Xte: Xte[:, 1:] @ m.coef_ + m.intercept_


def fit_weighted(Xtr, ytr, weights):
    """가중 최소제곱."""
    W = np.diag(weights)
    XtWX = Xtr.T @ W @ Xtr
    XtWy = Xtr.T @ W @ ytr
    beta = np.linalg.solve(XtWX, XtWy)
    return lambda Xte: Xte @ beta


def heteroskedastic_weights(ytr):
    """가격대별 weight: 양 끝단 (저가/고가) 가중."""
    quantiles = np.quantile(np.exp(ytr), [0.20, 0.80])
    prices = np.exp(ytr)
    w = np.ones_like(prices)
    w[(prices < quantiles[0]) | (prices > quantiles[1])] = 1.5  # 양 끝단 50% 가중
    return w


def lao_eval(X, y, groups, fit_func, n_seeds=30, **fit_kwargs):
    mdapes, w30s, w50s = [], [], []
    X_arr = X.values.astype(float)
    y_arr = y.values.astype(float)
    for seed in range(42, 42 + n_seeds):
        gss = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=seed)
        tr, te = next(gss.split(X, y, groups))
        Xtr, ytr = X_arr[tr], y_arr[tr]
        Xte, yte = X_arr[te], y_arr[te]

        if "weight_func" in fit_kwargs:
            weights = fit_kwargs["weight_func"](ytr)
            predict = fit_weighted(Xtr, ytr, weights)
        else:
            predict = fit_func(Xtr, ytr)

        pred = predict(Xte)
        m = metrics(yte, pred)
        mdapes.append(m["mdape"])
        w30s.append(m["w30"])
        w50s.append(m["w50"])
    return {
        "mdape_mean": float(np.mean(mdapes)),
        "mdape_std": float(np.std(mdapes)),
        "w30_mean": float(np.mean(w30s)),
        "w50_mean": float(np.mean(w50s)),
    }


# ─────────────────────────────────────────
# Target transform 실험
# ─────────────────────────────────────────
def target_transform_eval(df_feat, X, groups, transform: str, n_seeds=30):
    """Box-Cox / Yeo-Johnson 변환 후 학습 → 역변환 후 metric."""
    prices = df_feat["price_krw"].values

    if transform == "box-cox":
        # Box-Cox requires positive
        pt = PowerTransformer(method="box-cox")
        y_trans_full = pt.fit_transform(prices.reshape(-1, 1)).flatten()
    elif transform == "yeo-johnson":
        pt = PowerTransformer(method="yeo-johnson")
        y_trans_full = pt.fit_transform(prices.reshape(-1, 1)).flatten()
    elif transform == "sqrt":
        y_trans_full = np.sqrt(prices)
    else:
        raise ValueError(transform)

    X_arr = X.values.astype(float)
    mdapes, w30s, w50s = [], [], []
    for seed in range(42, 42 + n_seeds):
        gss = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=seed)
        tr, te = next(gss.split(X, y_trans_full, groups))
        Xtr, ytr = X_arr[tr], y_trans_full[tr]
        Xte, yte_orig = X_arr[te], prices[te]
        beta, *_ = np.linalg.lstsq(Xtr, ytr, rcond=None)
        pred_trans = Xte @ beta
        # 역변환
        if transform == "sqrt":
            pred_orig = pred_trans ** 2
        else:
            pred_orig = pt.inverse_transform(pred_trans.reshape(-1, 1)).flatten()
        ape = np.abs(pred_orig - yte_orig) / yte_orig
        mdapes.append(float(np.median(ape) * 100))
        w30s.append(float((ape <= 0.30).mean() * 100))
        w50s.append(float((ape <= 0.50).mean() * 100))
    return {
        "mdape_mean": float(np.mean(mdapes)),
        "mdape_std": float(np.std(mdapes)),
        "w30_mean": float(np.mean(w30s)),
        "w50_mean": float(np.mean(w50s)),
    }


# ─────────────────────────────────────────
# Smearing correction
# ─────────────────────────────────────────
def smearing_eval(X, y, groups, n_seeds=30):
    """Duan's smearing estimator: $E[P] = exp(\\hat y) \\cdot mean(exp(resid))$."""
    X_arr = X.values.astype(float)
    y_arr = y.values.astype(float)
    mdapes_smear, mdapes_normal = [], []
    for seed in range(42, 42 + n_seeds):
        gss = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=seed)
        tr, te = next(gss.split(X, y, groups))
        Xtr, ytr = X_arr[tr], y_arr[tr]
        Xte, yte = X_arr[te], y_arr[te]
        beta, *_ = np.linalg.lstsq(Xtr, ytr, rcond=None)
        resid_tr = ytr - Xtr @ beta
        smear = np.mean(np.exp(resid_tr))  # smearing factor

        pred_log = Xte @ beta

        # Normal: exp(pred)
        ape_normal = np.abs(np.exp(pred_log) - np.exp(yte)) / np.exp(yte)
        mdapes_normal.append(float(np.median(ape_normal) * 100))

        # Smearing-corrected: exp(pred) * smear
        ape_smear = np.abs(np.exp(pred_log) * smear - np.exp(yte)) / np.exp(yte)
        mdapes_smear.append(float(np.median(ape_smear) * 100))

    return {
        "normal_mdape": float(np.mean(mdapes_normal)),
        "smearing_mdape": float(np.mean(mdapes_smear)),
        "smearing_diff": float(np.mean(mdapes_smear) - np.mean(mdapes_normal)),
    }


def run():
    df = pd.read_parquet(DATA)
    df_feat = make_features(df)
    y = df_feat["log_price"]
    groups = df_feat["artist_slug"].astype(str).to_numpy()
    X = build_X_baseline(df_feat)

    summary = {}

    # 1. Baseline (F4 + spline)
    logger.info("=" * 80)
    logger.info("Baseline: F4 + log_area spline (P1 winner)")
    logger.info("=" * 80)
    res = lao_eval(X, y, groups, fit_ols, N_SEEDS)
    logger.info(f"  baseline: MdAPE {res['mdape_mean']:.2f}±{res['mdape_std']:.2f}%")
    summary["baseline_p1_winner"] = res

    # 2. Huber regression
    logger.info("\n" + "=" * 80)
    logger.info("P2-1. Huber regression (robust)")
    logger.info("=" * 80)
    res = lao_eval(X, y, groups, fit_huber, N_SEEDS)
    logger.info(f"  Huber: MdAPE {res['mdape_mean']:.2f}±{res['mdape_std']:.2f}%")
    summary["p2_huber"] = res

    # 3. Heteroskedastic weighting
    logger.info("\n" + "=" * 80)
    logger.info("P2-2. Weighted regression (heteroskedastic, 양 끝단 가중)")
    logger.info("=" * 80)
    res = lao_eval(X, y, groups, fit_ols, N_SEEDS, weight_func=heteroskedastic_weights)
    logger.info(f"  Weighted: MdAPE {res['mdape_mean']:.2f}±{res['mdape_std']:.2f}%")
    summary["p2_weighted"] = res

    # 4. Target transform 비교
    logger.info("\n" + "=" * 80)
    logger.info("P2-3. Target transform 변경")
    logger.info("=" * 80)
    for tr in ["box-cox", "yeo-johnson", "sqrt"]:
        res = target_transform_eval(df_feat, X, groups, tr, N_SEEDS)
        logger.info(f"  {tr}: MdAPE {res['mdape_mean']:.2f}±{res['mdape_std']:.2f}%")
        summary[f"p2_transform_{tr}"] = res

    # 5. Smearing correction (mean estimation)
    logger.info("\n" + "=" * 80)
    logger.info("P2-4. Smearing 보정 (Duan estimator)")
    logger.info("=" * 80)
    res = smearing_eval(X, y, groups, N_SEEDS)
    logger.info(f"  Normal:    MdAPE {res['normal_mdape']:.2f}%")
    logger.info(f"  Smearing:  MdAPE {res['smearing_mdape']:.2f}%")
    logger.info(f"  Diff:      {res['smearing_diff']:+.2f}%p")
    summary["p2_smearing"] = res

    # Save
    with (RESULTS / "stage3_p2_robust.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("최종 비교 (vs F4 + spline baseline)")
    logger.info("=" * 80)
    base_mdape = summary["baseline_p1_winner"]["mdape_mean"]
    logger.info(f"{'Method':<35} {'MdAPE':>14} {'개선':>10}")
    for name in ["baseline_p1_winner", "p2_huber", "p2_weighted",
                 "p2_transform_box-cox", "p2_transform_yeo-johnson",
                 "p2_transform_sqrt"]:
        m = summary[name]
        diff = m["mdape_mean"] - base_mdape
        logger.info(
            f"{name:<35} {m['mdape_mean']:>6.2f}±{m['mdape_std']:>4.2f}% "
            f"{diff:>+5.2f}%p"
        )


if __name__ == "__main__":
    run()
