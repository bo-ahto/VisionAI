"""Stage 3 — Warm-start + Calibration 검증 (코덱스 권고).

1. Warm-start split (작품 단위, 작가 train/test 모두 포함) ME 재평가
2. 가격대별 calibration 적용 전후 holdout 비교
3. 이원 전략 (cold = OLS / warm = ME) 시뮬레이션
"""

from __future__ import annotations

import json
import logging
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
    resid = y - X @ beta
    return beta, resid


def fit_random_intercept(X, y, groups):
    n_iter = 20
    tol = 1e-5
    beta_prev = None
    beta, resid = ols_fit(X, y)
    for i in range(n_iter):
        unique_g, inv = np.unique(groups, return_inverse=True)
        u_j = np.zeros(len(unique_g))
        for j, g in enumerate(unique_g):
            mask = inv == j
            u_j[j] = resid[mask].mean()
        y_adj = y - u_j[inv]
        beta_new, _ = ols_fit(X, y_adj)
        if beta_prev is not None and np.max(np.abs(beta_new - beta_prev)) < tol:
            break
        beta_prev = beta_new
        beta = beta_new
        resid = y - X @ beta - u_j[inv]
    unique_g, inv = np.unique(groups, return_inverse=True)
    u_j = np.zeros(len(unique_g))
    for j, g in enumerate(unique_g):
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


# ───────────────────────────────────────
# 1. Warm-start split (작품 단위)
# ───────────────────────────────────────
def warm_start_eval(df_feat, y, groups, n_seeds=30):
    """Warm-start: 작품 단위 random split (작가 train/test 모두 포함)."""
    X_cols = ["log_area", "birth_year_centered", "log_artist_total_works"]
    X = df_feat[X_cols].copy()
    X.insert(0, "const", 1.0)

    ols_metrics_list = []
    me_metrics_list = []

    for seed in range(42, 42 + n_seeds):
        ss = ShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=seed)
        tr, te = next(ss.split(X, y))
        Xtr = X.iloc[tr].values.astype(float)
        ytr = y.iloc[tr].values.astype(float)
        Xte = X.iloc[te].values.astype(float)
        yte = y.iloc[te].values.astype(float)
        gtr = groups[tr]
        gte = groups[te]

        # OLS
        beta_ols, _ = ols_fit(Xtr, ytr)
        pred_ols = Xte @ beta_ols
        ols_metrics_list.append(metrics(yte, pred_ols))

        # ME
        beta_me, u_j, ug = fit_random_intercept(Xtr, ytr, gtr)
        pred_me = predict_re(Xte, gte, beta_me, u_j, ug)
        me_metrics_list.append(metrics(yte, pred_me))

    def aggregate(lst):
        return {
            metric: {
                "mean": float(np.mean([x[metric] for x in lst])),
                "std": float(np.std([x[metric] for x in lst])),
            }
            for metric in ["mdape", "w30", "w50"]
        }

    return aggregate(ols_metrics_list), aggregate(me_metrics_list)


# ───────────────────────────────────────
# 2. Calibration 적용 전후 비교
# ───────────────────────────────────────
def build_calibration_table(df_feat, y, groups, n_seeds=30):
    """LAO holdout 으로 calibration 테이블 생성."""
    X_cols = ["log_area", "birth_year_centered", "log_artist_total_works"]
    X = df_feat[X_cols].copy()
    X.insert(0, "const", 1.0)

    all_yte = []
    all_pred = []
    for seed in range(42, 42 + n_seeds):
        gss = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=seed)
        tr, te = next(gss.split(X, y, groups))
        Xtr = X.iloc[tr].values.astype(float)
        ytr = y.iloc[tr].values.astype(float)
        Xte = X.iloc[te].values.astype(float)
        yte = y.iloc[te].values.astype(float)
        beta, _ = ols_fit(Xtr, ytr)
        pred = Xte @ beta
        all_yte.extend(yte.tolist())
        all_pred.extend(pred.tolist())
    all_yte = np.array(all_yte)
    all_pred = np.array(all_pred)

    # 예측 quantile 기준 bin 보정 (예측가 기준이 운영에 적합)
    pred_quantiles = np.quantile(np.exp(all_pred), [0.20, 0.40, 0.60, 0.80])
    bin_edges = [-np.inf] + list(pred_quantiles) + [np.inf]
    bin_labels = ["저가 (<20%)", "20-40%", "40-60%", "60-80%", "고가 (>80%)"]

    cal_table = []
    for label, edges in zip(bin_labels, zip(bin_edges[:-1], bin_edges[1:])):
        lo, hi = edges
        mask = (np.exp(all_pred) > lo) & (np.exp(all_pred) <= hi)
        if mask.sum() > 0:
            resid = all_yte[mask] - all_pred[mask]
            cal_table.append({
                "label": label,
                "lower": float(lo) if lo > -np.inf else None,
                "upper": float(hi) if hi < np.inf else None,
                "n": int(mask.sum()),
                "median_log_resid": float(np.median(resid)),
                "correction_factor": float(np.exp(np.median(resid))),
            })
    return cal_table


def apply_calibration(pred_log: np.ndarray, cal_table: list) -> np.ndarray:
    """예측 가격 기준 bin 보정 적용."""
    pred_price = np.exp(pred_log)
    corrected = np.zeros_like(pred_log)
    for i, p in enumerate(pred_price):
        for entry in cal_table:
            lo = entry["lower"] if entry["lower"] is not None else -np.inf
            hi = entry["upper"] if entry["upper"] is not None else np.inf
            if lo < p <= hi:
                corrected[i] = pred_log[i] + entry["median_log_resid"]
                break
        else:
            corrected[i] = pred_log[i]
    return corrected


def calibration_compare(df_feat, y, groups, n_seeds=30):
    """Calibration 적용 전후 holdout 비교."""
    X_cols = ["log_area", "birth_year_centered", "log_artist_total_works"]
    X = df_feat[X_cols].copy()
    X.insert(0, "const", 1.0)

    # Train cal table on first 15 seeds, test on last 15
    train_seeds = list(range(42, 42 + 15))
    test_seeds = list(range(42 + 15, 42 + 30))

    # Train cal table
    all_yte_tr = []
    all_pred_tr = []
    for seed in train_seeds:
        gss = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=seed)
        tr, te = next(gss.split(X, y, groups))
        Xtr = X.iloc[tr].values.astype(float)
        ytr = y.iloc[tr].values.astype(float)
        Xte = X.iloc[te].values.astype(float)
        yte = y.iloc[te].values.astype(float)
        beta, _ = ols_fit(Xtr, ytr)
        all_yte_tr.extend(yte.tolist())
        all_pred_tr.extend((Xte @ beta).tolist())
    all_yte_tr = np.array(all_yte_tr)
    all_pred_tr = np.array(all_pred_tr)

    pred_q = np.quantile(np.exp(all_pred_tr), [0.20, 0.40, 0.60, 0.80])
    bin_edges = [-np.inf] + list(pred_q) + [np.inf]
    cal_table = []
    for i, edges in enumerate(zip(bin_edges[:-1], bin_edges[1:])):
        lo, hi = edges
        mask = (np.exp(all_pred_tr) > lo) & (np.exp(all_pred_tr) <= hi)
        if mask.sum() > 0:
            resid = all_yte_tr[mask] - all_pred_tr[mask]
            cal_table.append({
                "lower": float(lo) if lo > -np.inf else None,
                "upper": float(hi) if hi < np.inf else None,
                "median_log_resid": float(np.median(resid)),
            })

    # Test on held-out seeds with calibration applied
    raw_metrics_list = []
    cal_metrics_list = []
    for seed in test_seeds:
        gss = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=seed)
        tr, te = next(gss.split(X, y, groups))
        Xtr = X.iloc[tr].values.astype(float)
        ytr = y.iloc[tr].values.astype(float)
        Xte = X.iloc[te].values.astype(float)
        yte = y.iloc[te].values.astype(float)
        beta, _ = ols_fit(Xtr, ytr)
        pred_raw = Xte @ beta
        pred_cal = apply_calibration(pred_raw, cal_table)
        raw_metrics_list.append(metrics(yte, pred_raw))
        cal_metrics_list.append(metrics(yte, pred_cal))

    def agg(lst):
        return {
            metric: {
                "mean": float(np.mean([x[metric] for x in lst])),
                "std": float(np.std([x[metric] for x in lst])),
            }
            for metric in ["mdape", "w30", "w50"]
        }

    return agg(raw_metrics_list), agg(cal_metrics_list), cal_table


# ───────────────────────────────────────
# 3. 이원 전략 시뮬레이션
# ───────────────────────────────────────
def two_track_strategy(df_feat, y, groups, warm_threshold=5, n_seeds=30):
    """
    이원 전략:
    - Test 작가가 train 에 있으면 (warm) → ME prediction
    - Test 작가가 train 에 없으면 (cold) → OLS prediction

    실제로 LAO 는 항상 cold 라서 의미 X. 대신 partial-overlap split 사용.
    train 작가가 일부 test 에 portion 으로 들어오는 시나리오.
    """
    # Mixed split: 작가 단위 그룹 분할 후 각 그룹 일부 작품을 test 에 뺌
    X_cols = ["log_area", "birth_year_centered", "log_artist_total_works"]
    X = df_feat[X_cols].copy()
    X.insert(0, "const", 1.0)

    results = {"warm": [], "cold": [], "two_track": []}

    for seed in range(42, 42 + n_seeds):
        rng = np.random.default_rng(seed)
        unique_artists = np.unique(groups)
        rng.shuffle(unique_artists)

        # 80% 작가 = warm pool, 20% 작가 = cold pool
        n_warm = int(len(unique_artists) * 0.80)
        warm_artists = set(unique_artists[:n_warm])
        cold_artists = set(unique_artists[n_warm:])

        # Train: warm 작가의 80% 작품
        # Test (warm): warm 작가의 나머지 20% 작품
        # Test (cold): cold 작가의 모든 작품
        warm_mask = np.array([g in warm_artists for g in groups])
        cold_mask = ~warm_mask

        # Warm 작가 작품 80/20 split
        warm_idx = np.where(warm_mask)[0]
        rng.shuffle(warm_idx)
        n_warm_tr = int(len(warm_idx) * 0.80)
        warm_tr = warm_idx[:n_warm_tr]
        warm_te = warm_idx[n_warm_tr:]

        # Cold = test only
        cold_te = np.where(cold_mask)[0]

        Xtr = X.iloc[warm_tr].values.astype(float)
        ytr = y.iloc[warm_tr].values.astype(float)
        gtr = groups[warm_tr]

        # Train ME on warm train
        beta_me, u_j, ug = fit_random_intercept(Xtr, ytr, gtr)

        # Test on warm
        Xte_w = X.iloc[warm_te].values.astype(float)
        yte_w = y.iloc[warm_te].values.astype(float)
        gte_w = groups[warm_te]
        pred_w_me = predict_re(Xte_w, gte_w, beta_me, u_j, ug)
        pred_w_ols = Xte_w @ beta_me  # OLS = ME without u_j (since RE=0 for warm-not-fit)
        # ↑ 수정: warm test 작가는 train 에 있으므로 ME 가 u_j 사용

        # Test on cold
        Xte_c = X.iloc[cold_te].values.astype(float)
        yte_c = y.iloc[cold_te].values.astype(float)
        gte_c = groups[cold_te]
        pred_c_ols = Xte_c @ beta_me  # cold = OLS (u_j=0 for unknown artists)

        # Two-track combined
        all_yte = np.concatenate([yte_w, yte_c])
        all_pred_two = np.concatenate([pred_w_me, pred_c_ols])
        all_pred_ols_only = np.concatenate([
            Xte_w @ beta_me,
            pred_c_ols,
        ])

        results["warm"].append(metrics(yte_w, pred_w_me))
        results["cold"].append(metrics(yte_c, pred_c_ols))
        results["two_track"].append(metrics(all_yte, all_pred_two))

    def agg(lst):
        return {
            metric: {
                "mean": float(np.mean([x[metric] for x in lst])),
                "std": float(np.std([x[metric] for x in lst])),
            }
            for metric in ["mdape", "w30", "w50"]
        }

    return {k: agg(v) for k, v in results.items()}


def run():
    df = pd.read_parquet(DATA)
    df_feat = make_features(df)
    y = df_feat["log_price"]
    groups = df_feat["artist_slug"].astype(str).to_numpy()

    summary = {}

    # 1. Warm-start
    logger.info("=" * 80)
    logger.info("1. Warm-start split (작품 단위) — ME 재평가")
    logger.info("=" * 80)
    ols_w, me_w = warm_start_eval(df_feat, y, groups, N_SEEDS)
    for metric in ["mdape", "w30", "w50"]:
        diff = me_w[metric]["mean"] - ols_w[metric]["mean"]
        logger.info(
            f"  {metric.upper():<6} "
            f"OLS: {ols_w[metric]['mean']:>6.2f}±{ols_w[metric]['std']:>4.2f}% / "
            f"ME: {me_w[metric]['mean']:>6.2f}±{me_w[metric]['std']:>4.2f}% / "
            f"Δ: {diff:+.2f}%p"
        )
    summary["1_warm_start"] = {"ols": ols_w, "me": me_w}

    # 2. Calibration
    logger.info("\n" + "=" * 80)
    logger.info("2. Calibration 적용 전후 holdout 비교")
    logger.info("=" * 80)
    raw_m, cal_m, cal_table = calibration_compare(df_feat, y, groups, N_SEEDS)
    for metric in ["mdape", "w30", "w50"]:
        diff = cal_m[metric]["mean"] - raw_m[metric]["mean"]
        logger.info(
            f"  {metric.upper():<6} "
            f"raw: {raw_m[metric]['mean']:>6.2f}±{raw_m[metric]['std']:>4.2f}% / "
            f"cal: {cal_m[metric]['mean']:>6.2f}±{cal_m[metric]['std']:>4.2f}% / "
            f"Δ: {diff:+.2f}%p"
        )
    logger.info(f"\n  Calibration 테이블:")
    for entry in cal_table:
        lo = f"{entry['lower']:>10,.0f}원" if entry['lower'] else "  -inf"
        hi = f"{entry['upper']:>10,.0f}원" if entry['upper'] else "  +inf"
        logger.info(
            f"    예측가 {lo}~{hi}: "
            f"보정 {np.exp(entry['median_log_resid']):.3f}× "
            f"(log_resid {entry['median_log_resid']:+.3f})"
        )
    summary["2_calibration"] = {
        "raw": raw_m,
        "calibrated": cal_m,
        "table": cal_table,
    }

    # 3. Two-track strategy
    logger.info("\n" + "=" * 80)
    logger.info("3. 이원 전략 (warm = ME / cold = OLS)")
    logger.info("=" * 80)
    two_track = two_track_strategy(df_feat, y, groups, n_seeds=N_SEEDS)
    for split_name, m in two_track.items():
        logger.info(
            f"  [{split_name}] MdAPE: {m['mdape']['mean']:.2f}±{m['mdape']['std']:.2f}% / "
            f"W30: {m['w30']['mean']:.2f}% / W50: {m['w50']['mean']:.2f}%"
        )
    summary["3_two_track"] = two_track

    with (RESULTS / "stage3_warm_calibration.json").open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(
        f"\nSaved: {(RESULTS / 'stage3_warm_calibration.json').relative_to(ROOT)}"
    )


if __name__ == "__main__":
    run()
