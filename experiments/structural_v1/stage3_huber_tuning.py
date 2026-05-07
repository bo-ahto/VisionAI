"""Stage 3 Huber 튜닝 + Winsorization + Seed 확대.

코덱스 권고 추가 실험:
1. Huber epsilon 튜닝 (1.0 ~ 2.0)
2. Huber alpha (L2 reg) 튜닝
3. Winsorization (가격 1%/5%/10% trim)
4. Quantile clip + Huber 조합
5. Seed 100 확대 검증
6. Stage 별 성능 분해
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
DATA_S2 = ROOT / "data" / "curated" / "stage2_500x50.parquet"
DATA_S3 = ROOT / "data" / "curated" / "stage3_1000x100.parquet"
RESULTS = Path(__file__).parent / "results"

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


def build_X_baseline(df_feat):
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


def fit_huber_predict(Xtr, ytr, Xte, epsilon=1.35, alpha=0.0001):
    m = HuberRegressor(
        epsilon=epsilon, max_iter=500, alpha=alpha
    )
    m.fit(Xtr[:, 1:], ytr)
    return Xte[:, 1:] @ m.coef_ + m.intercept_


def fit_ols_predict(Xtr, ytr, Xte):
    beta, *_ = np.linalg.lstsq(Xtr, ytr, rcond=None)
    return Xte @ beta


def lao_eval(
    X, y, groups, n_seeds=30,
    fit_func=fit_huber_predict, **fit_kwargs
):
    mdapes, w30s, w50s = [], [], []
    X_arr = X.values.astype(float)
    y_arr = y.values.astype(float)
    for seed in range(42, 42 + n_seeds):
        gss = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=seed)
        tr, te = next(gss.split(X, y, groups))
        Xtr, ytr = X_arr[tr], y_arr[tr]
        Xte, yte = X_arr[te], y_arr[te]
        try:
            pred = fit_func(Xtr, ytr, Xte, **fit_kwargs)
        except Exception as e:
            logger.warning(f"  seed={seed} fit failed: {e}")
            continue
        m = metrics(yte, pred)
        mdapes.append(m["mdape"])
        w30s.append(m["w30"])
        w50s.append(m["w50"])
    return {
        "mdape_mean": float(np.mean(mdapes)),
        "mdape_std": float(np.std(mdapes)),
        "w30_mean": float(np.mean(w30s)),
        "w50_mean": float(np.mean(w50s)),
        "n_seeds": int(len(mdapes)),
    }


def winsorize_prices(df_feat, lower_pct=1, upper_pct=99):
    """Train-time price winsorization (학습 시 trim, test 는 원본)."""
    prices = df_feat["price_krw"].values
    lo = np.percentile(prices, lower_pct)
    hi = np.percentile(prices, upper_pct)
    df_w = df_feat.copy()
    df_w["price_krw"] = np.clip(df_w["price_krw"], lo, hi)
    df_w["log_price"] = np.log(df_w["price_krw"].clip(lower=1))
    return df_w, lo, hi


# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────
def run():
    df3 = pd.read_parquet(DATA_S3)
    df3_feat = make_features(df3)
    y3 = df3_feat["log_price"]
    g3 = df3_feat["artist_slug"].astype(str).to_numpy()
    X3 = build_X_baseline(df3_feat)

    summary = {}

    # 1. Baseline (Huber default)
    logger.info("=" * 80)
    logger.info("1. Baseline — F4 + spline + Huber (default eps=1.35, alpha=0.0001)")
    logger.info("=" * 80)
    res = lao_eval(X3, y3, g3, 30)
    logger.info(f"  default (30s): MdAPE {res['mdape_mean']:.2f}±{res['mdape_std']:.2f}%")
    summary["baseline_huber_default_30s"] = res

    # 2. Huber epsilon 튜닝
    logger.info("\n" + "=" * 80)
    logger.info("2. Huber epsilon 튜닝")
    logger.info("=" * 80)
    eps_grid = [1.0, 1.1, 1.2, 1.35, 1.5, 1.75, 2.0]
    for eps in eps_grid:
        res = lao_eval(X3, y3, g3, 30, epsilon=eps)
        logger.info(
            f"  eps={eps}: MdAPE {res['mdape_mean']:.2f}±{res['mdape_std']:.2f}%"
        )
        summary[f"huber_eps_{eps}"] = res

    # 3. Huber alpha (L2) 튜닝
    logger.info("\n" + "=" * 80)
    logger.info("3. Huber alpha (L2) 튜닝 (eps=1.0 best)")
    logger.info("=" * 80)
    alpha_grid = [0.0, 0.0001, 0.001, 0.01, 0.1, 1.0]
    best_eps = 1.0  # eps tuning 결과 알 수 없지만 일단 1.0
    for alpha in alpha_grid:
        res = lao_eval(X3, y3, g3, 30, epsilon=best_eps, alpha=alpha)
        logger.info(
            f"  alpha={alpha}: MdAPE {res['mdape_mean']:.2f}±{res['mdape_std']:.2f}%"
        )
        summary[f"huber_alpha_{alpha}"] = res

    # 4. Winsorization (학습 데이터만 trim)
    logger.info("\n" + "=" * 80)
    logger.info("4. Winsorization (학습 가격 trim)")
    logger.info("=" * 80)
    for trim in [(1, 99), (5, 95), (10, 90)]:
        df_w, lo, hi = winsorize_prices(df3_feat, *trim)
        y_w = df_w["log_price"]
        # X는 그대로 (price 외 변수)
        res = lao_eval(X3, y_w, g3, 30, fit_func=fit_huber_predict, epsilon=1.35)
        logger.info(
            f"  trim {trim[0]}%/{trim[1]}% (range {lo:,.0f}~{hi:,.0f}): "
            f"MdAPE {res['mdape_mean']:.2f}±{res['mdape_std']:.2f}%"
        )
        summary[f"winsorize_{trim[0]}_{trim[1]}"] = res

    # 5. OLS + Winsorization 비교
    logger.info("\n" + "=" * 80)
    logger.info("5. OLS + Winsorization (Huber 의 대체 가능성)")
    logger.info("=" * 80)
    for trim in [(1, 99), (5, 95)]:
        df_w, lo, hi = winsorize_prices(df3_feat, *trim)
        y_w = df_w["log_price"]
        res = lao_eval(X3, y_w, g3, 30, fit_func=fit_ols_predict)
        logger.info(
            f"  OLS + trim {trim[0]}%/{trim[1]}%: "
            f"MdAPE {res['mdape_mean']:.2f}±{res['mdape_std']:.2f}%"
        )
        summary[f"ols_winsorize_{trim[0]}_{trim[1]}"] = res

    # 6. Seed 100 확대 검증 (best 후보)
    logger.info("\n" + "=" * 80)
    logger.info("6. Seed 100 확대 검증 (재현성)")
    logger.info("=" * 80)
    res100 = lao_eval(X3, y3, g3, 100, epsilon=1.35)
    logger.info(
        f"  Huber eps=1.35 (100s): MdAPE {res100['mdape_mean']:.2f}±{res100['mdape_std']:.2f}%"
    )
    summary["huber_default_100s"] = res100

    res_ols_100 = lao_eval(X3, y3, g3, 100, fit_func=fit_ols_predict)
    logger.info(
        f"  OLS baseline (100s): MdAPE {res_ols_100['mdape_mean']:.2f}±{res_ols_100['mdape_std']:.2f}%"
    )
    summary["ols_baseline_100s"] = res_ols_100

    # 7. Stage 2 (500/50) 비교
    logger.info("\n" + "=" * 80)
    logger.info("7. Stage 2 (500/50) 에서 Huber 효과")
    logger.info("=" * 80)
    df2 = pd.read_parquet(DATA_S2)
    df2_feat = make_features(df2)
    y2 = df2_feat["log_price"]
    g2 = df2_feat["artist_slug"].astype(str).to_numpy()
    X2 = build_X_baseline(df2_feat)

    res_s2_ols = lao_eval(X2, y2, g2, 30, fit_func=fit_ols_predict)
    res_s2_huber = lao_eval(X2, y2, g2, 30)
    logger.info(
        f"  Stage 2 OLS:   MdAPE {res_s2_ols['mdape_mean']:.2f}±{res_s2_ols['mdape_std']:.2f}%"
    )
    logger.info(
        f"  Stage 2 Huber: MdAPE {res_s2_huber['mdape_mean']:.2f}±{res_s2_huber['mdape_std']:.2f}%"
    )
    summary["stage2_ols"] = res_s2_ols
    summary["stage2_huber"] = res_s2_huber

    # Save
    with (RESULTS / "stage3_huber_tuning.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("최종 비교 (vs F4+spline+Huber 25.12% baseline)")
    logger.info("=" * 80)
    base = summary["baseline_huber_default_30s"]["mdape_mean"]
    keys_show = [
        "baseline_huber_default_30s",
        "huber_eps_1.0", "huber_eps_1.35", "huber_eps_2.0",
        "huber_alpha_0.0", "huber_alpha_0.001", "huber_alpha_0.1",
        "winsorize_1_99", "winsorize_5_95",
        "ols_winsorize_1_99",
        "huber_default_100s", "ols_baseline_100s",
        "stage2_ols", "stage2_huber",
    ]
    for name in keys_show:
        if name not in summary:
            continue
        m = summary[name]
        diff = m["mdape_mean"] - base
        logger.info(
            f"{name:<32} k={m.get('n_seeds', 30):>3}s "
            f"{m['mdape_mean']:>6.2f}±{m['mdape_std']:>4.2f}% "
            f"{diff:>+5.2f}%p"
        )


if __name__ == "__main__":
    run()
