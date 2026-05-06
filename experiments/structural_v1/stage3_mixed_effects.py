"""Stage 3 Mixed-Effects (random intercept).

Stage 2 freeze: F4 = log_area + birth_year_centered + log_artist_total_works
Stage 3: F4 fixed effects + (1 | artist_slug) random intercept.

작가별 미관측 고유효과를 random intercept 로 흡수.
artist_total_works (관측 생산성) + RE (미관측 고유효과) 공존.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.model_selection import GroupShuffleSplit

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent.parent
DATA = ROOT / "data" / "curated" / "stage3_1000x100.parquet"
RESULTS = Path(__file__).parent / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

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


def ols_fit(X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """OLS β̂ + residuals."""
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    return beta, resid


def fit_random_intercept(
    X: np.ndarray, y: np.ndarray, groups: np.ndarray
) -> dict:
    """Iterative random intercept estimator.

    Approach:
    1. OLS fit β
    2. Compute group means of residuals → u_j (random intercept)
    3. y_adj = y - u_j[group]
    4. Re-fit OLS on y_adj
    5. Repeat until convergence

    더 정확히는 EM/REML 이지만 statsmodels 호환 안 되어 간이 구현.
    """
    n_iter = 20
    tol = 1e-5
    beta_prev = None

    # 1. Initial OLS
    beta, resid = ols_fit(X, y)

    for i in range(n_iter):
        # 2. Group means of residuals = random intercept
        unique_g, inv = np.unique(groups, return_inverse=True)
        u_j = np.zeros(len(unique_g))
        for j, g in enumerate(unique_g):
            mask = inv == j
            u_j[j] = resid[mask].mean()

        # 3. Subtract u_j from y
        y_adj = y - u_j[inv]

        # 4. Re-fit OLS
        beta_new, resid_new = ols_fit(X, y_adj)

        # 5. Convergence
        if beta_prev is not None and np.max(np.abs(beta_new - beta_prev)) < tol:
            break
        beta_prev = beta_new
        beta = beta_new
        # Add back u_j to compute new total residual
        resid = y - X @ beta - u_j[inv]

    # Final
    unique_g, inv = np.unique(groups, return_inverse=True)
    u_j = np.zeros(len(unique_g))
    for j, g in enumerate(unique_g):
        mask = inv == j
        u_j[j] = (y[mask] - X[mask] @ beta).mean()

    fitted = X @ beta + u_j[inv]
    final_resid = y - fitted

    # Variance decomposition
    var_re = np.var(u_j)
    var_resid = np.var(final_resid)
    var_total = var_re + var_resid
    icc = var_re / var_total if var_total > 0 else 0  # intra-class correlation

    return {
        "beta": beta,
        "u_j": u_j,
        "groups": unique_g,
        "var_re": float(var_re),
        "var_resid": float(var_resid),
        "icc": float(icc),
        "n_iter": int(i + 1),
    }


def predict_re(X_te: np.ndarray, te_groups: np.ndarray, model: dict) -> np.ndarray:
    """ME 예측: cold-start (test 작가 train 에 없음) 시 u_j = 0 (population mean)."""
    pred = X_te @ model["beta"]
    g_to_u = dict(zip(model["groups"], model["u_j"]))
    for i, g in enumerate(te_groups):
        if g in g_to_u:
            pred[i] += g_to_u[g]
        # else: cold-start → u_j = 0 (default)
    return pred


def metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    ape = np.abs(np.exp(y_pred) - np.exp(y_true)) / np.exp(y_true)
    return {
        "mdape_pct": float(np.median(ape) * 100),
        "w30_pct": float((ape <= 0.30).mean() * 100),
        "w50_pct": float((ape <= 0.50).mean() * 100),
    }


def lao_eval_ols_vs_me(df_feat, y, groups, n_seeds=30):
    """OLS vs ME random intercept 30-seed 비교."""
    X_cols = ["log_area", "birth_year_centered", "log_artist_total_works"]
    X = df_feat[X_cols].copy()
    X.insert(0, "const", 1.0)

    ols_results = {"mdape": [], "w30": [], "w50": []}
    me_results = {"mdape": [], "w30": [], "w50": [], "icc": [], "var_re": []}

    for seed in range(42, 42 + n_seeds):
        gss = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=seed)
        tr, te = next(gss.split(X, y, groups))
        Xtr = X.iloc[tr].values.astype(float)
        ytr = y.iloc[tr].values.astype(float)
        Xte = X.iloc[te].values.astype(float)
        yte = y.iloc[te].values.astype(float)
        gtr = groups[tr]
        gte = groups[te]

        # OLS
        beta_ols, _ = ols_fit(Xtr, ytr)
        pred_ols = Xte @ beta_ols
        m_ols = metrics(yte, pred_ols)
        for k in ["mdape_pct", "w30_pct", "w50_pct"]:
            ols_results[k.replace("_pct", "")].append(m_ols[k])

        # ME random intercept
        me_model = fit_random_intercept(Xtr, ytr, gtr)
        pred_me = predict_re(Xte, gte, me_model)
        m_me = metrics(yte, pred_me)
        for k in ["mdape_pct", "w30_pct", "w50_pct"]:
            me_results[k.replace("_pct", "")].append(m_me[k])
        me_results["icc"].append(me_model["icc"])
        me_results["var_re"].append(me_model["var_re"])

    return ols_results, me_results


def calibration_table(
    df_feat: pd.DataFrame, y: pd.Series, groups: np.ndarray
) -> dict:
    """저가/고가 가격대별 calibration 테이블 생성.

    각 가격 quantile bin 별 median residual 측정 → 보정 수치.
    """
    X_cols = ["log_area", "birth_year_centered", "log_artist_total_works"]
    X = df_feat[X_cols].copy()
    X.insert(0, "const", 1.0)

    all_yte = []
    all_pred_ols = []
    all_pred_me = []

    for seed in range(42, 72):
        gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=seed)
        tr, te = next(gss.split(X, y, groups))
        Xtr = X.iloc[tr].values.astype(float)
        ytr = y.iloc[tr].values.astype(float)
        Xte = X.iloc[te].values.astype(float)
        yte = y.iloc[te].values.astype(float)

        beta_ols, _ = ols_fit(Xtr, ytr)
        pred_ols = Xte @ beta_ols
        me_model = fit_random_intercept(Xtr, ytr, groups[tr])
        pred_me = predict_re(Xte, groups[te], me_model)

        all_yte.extend(yte.tolist())
        all_pred_ols.extend(pred_ols.tolist())
        all_pred_me.extend(pred_me.tolist())

    all_yte = np.array(all_yte)
    all_pred_ols = np.array(all_pred_ols)
    all_pred_me = np.array(all_pred_me)

    # Quantile bin (실제 가격 기준)
    prices = np.exp(all_yte)
    quantiles = np.quantile(prices, [0.20, 0.40, 0.60, 0.80])
    bin_edges = [-np.inf] + list(quantiles) + [np.inf]
    bin_labels = ["저가 (<20%)", "20-40%", "40-60%", "60-80%", "고가 (>80%)"]

    cal_table = {"ols": {}, "me": {}}
    for label, edges in zip(bin_labels, zip(bin_edges[:-1], bin_edges[1:])):
        lo, hi = edges
        mask = (prices > lo) & (prices <= hi)
        if mask.sum() > 0:
            for name, pred in [("ols", all_pred_ols), ("me", all_pred_me)]:
                resid = all_yte[mask] - pred[mask]
                cal_table[name][label] = {
                    "n": int(mask.sum()),
                    "median_log_resid": float(np.median(resid)),
                    "correction_factor": float(np.exp(np.median(resid))),
                    "mdape_pct": float(
                        np.median(np.abs(np.exp(resid) - 1)) * 100
                    ),
                }
    return cal_table


def coefficient_table(df_feat, y, groups):
    """Full-sample OLS + ME 계수 비교."""
    X_cols = ["log_area", "birth_year_centered", "log_artist_total_works"]
    X = df_feat[X_cols].copy()
    X.insert(0, "const", 1.0)
    X_arr = X.values.astype(float)
    y_arr = y.values.astype(float)
    groups_arr = groups

    # OLS
    beta_ols, resid_ols = ols_fit(X_arr, y_arr)
    n, k = X_arr.shape
    sigma2 = (resid_ols**2).sum() / (n - k)
    XtX_inv = np.linalg.inv(X_arr.T @ X_arr)
    se_ols = np.sqrt(np.diag(sigma2 * XtX_inv))

    # ME (full-sample)
    me_model = fit_random_intercept(X_arr, y_arr, groups_arr)
    beta_me = me_model["beta"]
    # ME SE 는 간이 추정 (within transformation 잔차 기반)
    # cold-start 가정상 ME SE 정확 계산 pymer4 등 필요. 여기서는 OLS SE 차용.

    rows = []
    for i, name in enumerate(X.columns):
        rows.append(
            {
                "feature": name,
                "ols_coef": float(beta_ols[i]),
                "ols_se": float(se_ols[i]),
                "ols_t": float(beta_ols[i] / se_ols[i]),
                "me_coef": float(beta_me[i]),
                "diff": float(beta_me[i] - beta_ols[i]),
            }
        )
    return rows, me_model


def run():
    df = pd.read_parquet(DATA)
    df_feat = make_features(df)
    y = df_feat["log_price"]
    groups = df_feat["artist_slug"].astype(str).to_numpy()

    logger.info(
        f"Stage 3: {len(df)} rows / {df['artist_slug'].nunique()} artists / "
        f"{N_SEEDS}-seed LAO"
    )

    # 1. OLS vs ME 30-seed 비교
    logger.info("\n" + "=" * 80)
    logger.info("1. OLS vs ME Random Intercept 비교 (30-seed LAO)")
    logger.info("=" * 80)
    ols_r, me_r = lao_eval_ols_vs_me(df_feat, y, groups, N_SEEDS)
    for metric in ["mdape", "w30", "w50"]:
        ols_m, ols_s = np.mean(ols_r[metric]), np.std(ols_r[metric])
        me_m, me_s = np.mean(me_r[metric]), np.std(me_r[metric])
        logger.info(
            f"  {metric.upper():<8} "
            f"OLS: {ols_m:>6.2f}±{ols_s:>5.2f}% / "
            f"ME: {me_m:>6.2f}±{me_s:>5.2f}% / "
            f"Δ: {me_m - ols_m:+.2f}%p"
        )
    icc_m = np.mean(me_r["icc"])
    var_re_m = np.mean(me_r["var_re"])
    logger.info(f"\n  ICC: {icc_m:.3f} (작가 분산 비중)")
    logger.info(f"  Var(RE): {var_re_m:.4f}")

    # 2. Coefficient 비교
    logger.info("\n" + "=" * 80)
    logger.info("2. Full-sample OLS vs ME Coefficient 비교")
    logger.info("=" * 80)
    coef_rows, full_me = coefficient_table(df_feat, y, groups)
    logger.info(f"\n{'feature':<28} {'OLS β':>10} {'(SE)':>10} {'ME β':>10} {'Δ':>8}")
    for r in coef_rows:
        logger.info(
            f"  {r['feature']:<28} "
            f"{r['ols_coef']:>10.4f} ({r['ols_se']:>6.4f}) "
            f"{r['me_coef']:>10.4f} {r['diff']:>+8.4f}"
        )
    logger.info(f"\n  Full-sample ICC: {full_me['icc']:.3f}")
    logger.info(f"  Var(RE) artist: {full_me['var_re']:.4f}")
    logger.info(f"  Var(residual): {full_me['var_resid']:.4f}")

    # 3. Calibration table
    logger.info("\n" + "=" * 80)
    logger.info("3. 가격대별 Calibration 테이블")
    logger.info("=" * 80)
    cal = calibration_table(df_feat, y, groups)
    for model_name in ["ols", "me"]:
        logger.info(f"\n  [{model_name.upper()}]")
        logger.info(
            f"  {'segment':<15} {'n':>6} {'median_resid':>15} "
            f"{'보정배수':>10} {'MdAPE':>8}"
        )
        for label, m in cal[model_name].items():
            logger.info(
                f"  {label:<15} {m['n']:>6} "
                f"{m['median_log_resid']:>13.4f}   "
                f"{m['correction_factor']:>8.3f}× "
                f"{m['mdape_pct']:>6.2f}%"
            )

    # Save
    summary = {
        "stage": "stage3",
        "n_records": len(df),
        "n_artists": int(df["artist_slug"].nunique()),
        "ols_metrics": {
            metric: {
                "mean": float(np.mean(ols_r[metric])),
                "std": float(np.std(ols_r[metric])),
            }
            for metric in ["mdape", "w30", "w50"]
        },
        "me_metrics": {
            metric: {
                "mean": float(np.mean(me_r[metric])),
                "std": float(np.std(me_r[metric])),
            }
            for metric in ["mdape", "w30", "w50"]
        },
        "icc_mean": float(icc_m),
        "var_re_mean": float(var_re_m),
        "coefficients": coef_rows,
        "full_sample_me": {
            "icc": full_me["icc"],
            "var_re": full_me["var_re"],
            "var_resid": full_me["var_resid"],
        },
        "calibration_table": cal,
    }

    with (RESULTS / "stage3_mixed_effects.json").open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(
        f"\nSaved: {(RESULTS / 'stage3_mixed_effects.json').relative_to(ROOT)}"
    )


if __name__ == "__main__":
    run()
