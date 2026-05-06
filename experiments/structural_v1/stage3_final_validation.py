"""Stage 3 — Final Validation (코덱스 마지막 점검 4가지).

1. Time-split (시간 기준 train/test) warm-start ME 평가
2. Warm threshold sensitivity (최소 작품 수 별 정확도)
3. Calibration drift check (시간대별 cal table 안정성)
4. (artist holdout 이미 30-seed 진행 — 결과 참조)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent.parent
DATA = ROOT / "data" / "curated" / "stage3_1000x100.parquet"
RESULTS = Path(__file__).parent / "results"


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
# 1. Time-split warm-start
# ───────────────────────────────────────
def time_split_warm(df_feat, y, groups):
    """시간 기준 train/test split — warm-start (작가 둘 다 포함 가능)."""
    X = build_X(df_feat)
    year_quantiles = df_feat["year_made"].quantile([0.50, 0.65, 0.80])

    splits = {
        "≤2020 → 2021+": df_feat["year_made"] <= 2020,
        "≤2022 → 2023+": df_feat["year_made"] <= 2022,
        "≤2023 → 2024+": df_feat["year_made"] <= 2023,
    }
    results = {}
    for name, train_mask in splits.items():
        if train_mask.sum() < 50 or (~train_mask).sum() < 50:
            continue
        Xtr = X[train_mask].values.astype(float)
        ytr = y[train_mask].values.astype(float)
        Xte = X[~train_mask].values.astype(float)
        yte = y[~train_mask].values.astype(float)
        gtr = groups[train_mask.values]
        gte = groups[(~train_mask).values]

        # OLS
        beta_ols, _ = ols_fit(Xtr, ytr)
        pred_ols = Xte @ beta_ols
        m_ols = metrics(yte, pred_ols)

        # ME
        beta_me, u_j, ug = fit_random_intercept(Xtr, ytr, gtr)
        pred_me = predict_re(Xte, gte, beta_me, u_j, ug)
        m_me = metrics(yte, pred_me)

        # Cold/warm 비율 (test 작가 train 포함 비율)
        train_artists = set(gtr)
        warm_count = sum(1 for g in gte if g in train_artists)
        warm_ratio = warm_count / len(gte) * 100

        results[name] = {
            "n_train": int(train_mask.sum()),
            "n_test": int((~train_mask).sum()),
            "warm_ratio_pct": float(warm_ratio),
            "ols": m_ols,
            "me": m_me,
        }
    return results


# ───────────────────────────────────────
# 2. Warm threshold sensitivity
# ───────────────────────────────────────
def warm_threshold_sensitivity(df_feat, y, groups, n_seeds=30):
    """warm 판정 기준 (작가 train 작품 수) 변화에 따른 정확도."""
    from sklearn.model_selection import GroupShuffleSplit

    X = build_X(df_feat)
    thresholds = [1, 2, 3, 5, 10]
    results = {t: {"warm_mdape": [], "cold_mdape": []} for t in thresholds}

    for seed in range(42, 42 + n_seeds):
        # 작품 단위 split (warm-start 시나리오)
        from sklearn.model_selection import ShuffleSplit
        ss = ShuffleSplit(n_splits=1, test_size=0.20, random_state=seed)
        tr, te = next(ss.split(X, y))
        Xtr = X.iloc[tr].values.astype(float)
        ytr = y.iloc[tr].values.astype(float)
        Xte = X.iloc[te].values.astype(float)
        yte = y.iloc[te].values.astype(float)
        gtr = groups[tr]
        gte = groups[te]

        # ME fit
        beta_me, u_j, ug = fit_random_intercept(Xtr, ytr, gtr)

        # train 의 작가별 작품 수 카운트
        from collections import Counter
        train_counts = Counter(gtr)

        # threshold 별 warm/cold 분류
        for t in thresholds:
            warm_mask = np.array([train_counts.get(g, 0) >= t for g in gte])
            if warm_mask.sum() == 0 or (~warm_mask).sum() == 0:
                continue

            # Warm test: ME 사용
            pred_warm = predict_re(
                Xte[warm_mask], gte[warm_mask], beta_me, u_j, ug
            )
            m_warm = metrics(yte[warm_mask], pred_warm)
            results[t]["warm_mdape"].append(m_warm["mdape"])

            # Cold test: OLS (u_j=0 default)
            pred_cold = Xte[~warm_mask] @ beta_me
            m_cold = metrics(yte[~warm_mask], pred_cold)
            results[t]["cold_mdape"].append(m_cold["mdape"])

    summary = {}
    for t in thresholds:
        if results[t]["warm_mdape"]:
            summary[f"min_works_{t}"] = {
                "warm_mdape_mean": float(np.mean(results[t]["warm_mdape"])),
                "warm_mdape_std": float(np.std(results[t]["warm_mdape"])),
                "cold_mdape_mean": float(np.mean(results[t]["cold_mdape"])),
                "cold_mdape_std": float(np.std(results[t]["cold_mdape"])),
            }
    return summary


# ───────────────────────────────────────
# 3. Calibration drift check
# ───────────────────────────────────────
def calibration_drift(df_feat, y, groups):
    """시간 기준 train cal table → 다른 시간대 test 적용."""
    X = build_X(df_feat)

    # Train cal on ≤2022, test on 2023+
    train_mask = df_feat["year_made"] <= 2022
    if train_mask.sum() < 50:
        return {}

    Xtr = X[train_mask].values.astype(float)
    ytr = y[train_mask].values.astype(float)
    Xte = X[~train_mask].values.astype(float)
    yte = y[~train_mask].values.astype(float)

    beta, _ = ols_fit(Xtr, ytr)
    pred_tr = Xtr @ beta  # in-sample
    pred_te = Xte @ beta  # out-time

    # Build cal table on train pred
    pred_q = np.quantile(np.exp(pred_tr), [0.20, 0.40, 0.60, 0.80])
    bin_edges = [-np.inf] + list(pred_q) + [np.inf]
    cal_train = []
    for lo, hi in zip(bin_edges[:-1], bin_edges[1:]):
        mask = (np.exp(pred_tr) > lo) & (np.exp(pred_tr) <= hi)
        if mask.sum() > 0:
            resid = ytr[mask] - pred_tr[mask]
            cal_train.append({"lo": lo, "hi": hi, "median_log_resid": float(np.median(resid))})

    # Apply to out-time test
    pred_te_cal = pred_te.copy()
    for i, p in enumerate(np.exp(pred_te)):
        for entry in cal_train:
            if entry["lo"] < p <= entry["hi"]:
                pred_te_cal[i] = pred_te[i] + entry["median_log_resid"]
                break

    raw_m = metrics(yte, pred_te)
    cal_m = metrics(yte, pred_te_cal)

    # Test 의 실제 cal table (compare)
    cal_test = []
    for lo, hi in zip(bin_edges[:-1], bin_edges[1:]):
        mask = (np.exp(pred_te) > lo) & (np.exp(pred_te) <= hi)
        if mask.sum() > 0:
            resid = yte[mask] - pred_te[mask]
            cal_test.append({"lo": lo, "hi": hi, "median_log_resid": float(np.median(resid))})

    # Drift = train vs test cal table 차이
    drift = []
    for ctr, cte in zip(cal_train, cal_test):
        drift.append({
            "lo": float(ctr["lo"]) if ctr["lo"] > -np.inf else None,
            "hi": float(ctr["hi"]) if ctr["hi"] < np.inf else None,
            "train_resid": ctr["median_log_resid"],
            "test_resid": cte["median_log_resid"],
            "drift": cte["median_log_resid"] - ctr["median_log_resid"],
        })

    return {
        "raw_mdape": raw_m["mdape"],
        "cal_mdape": cal_m["mdape"],
        "improvement": raw_m["mdape"] - cal_m["mdape"],
        "drift_per_bin": drift,
    }


def run():
    df = pd.read_parquet(DATA)
    df_feat = make_features(df)
    y = df_feat["log_price"]
    groups = df_feat["artist_slug"].astype(str).to_numpy()

    summary = {}

    # 1. Time-split warm-start
    logger.info("=" * 80)
    logger.info("1. Time-split warm-start (시간 기준 train/test)")
    logger.info("=" * 80)
    ts = time_split_warm(df_feat, y, groups)
    for name, m in ts.items():
        logger.info(
            f"  {name}: train={m['n_train']}, test={m['n_test']}, "
            f"warm_ratio={m['warm_ratio_pct']:.1f}%"
        )
        logger.info(
            f"    OLS MdAPE={m['ols']['mdape']:.2f}% / "
            f"ME MdAPE={m['me']['mdape']:.2f}% / "
            f"Δ: {m['me']['mdape'] - m['ols']['mdape']:+.2f}%p"
        )
    summary["1_time_split"] = ts

    # 2. Warm threshold sensitivity
    logger.info("\n" + "=" * 80)
    logger.info("2. Warm threshold sensitivity")
    logger.info("=" * 80)
    threshold_results = warm_threshold_sensitivity(df_feat, y, groups)
    logger.info(f"\n  {'min_works':<12} {'warm MdAPE':>15} {'cold MdAPE':>15}")
    for t_label, m in threshold_results.items():
        logger.info(
            f"  {t_label:<12} "
            f"{m['warm_mdape_mean']:>6.2f}±{m['warm_mdape_std']:>4.2f}% "
            f"{m['cold_mdape_mean']:>6.2f}±{m['cold_mdape_std']:>4.2f}%"
        )
    summary["2_warm_threshold"] = threshold_results

    # 3. Calibration drift
    logger.info("\n" + "=" * 80)
    logger.info("3. Calibration drift check (≤2022 train cal → 2023+ test)")
    logger.info("=" * 80)
    drift_results = calibration_drift(df_feat, y, groups)
    if drift_results:
        logger.info(f"\n  Out-of-time raw MdAPE: {drift_results['raw_mdape']:.2f}%")
        logger.info(f"  Out-of-time cal MdAPE: {drift_results['cal_mdape']:.2f}%")
        logger.info(f"  개선: {drift_results['improvement']:+.2f}%p")
        logger.info(f"\n  Drift per bin (train_resid → test_resid):")
        for d in drift_results["drift_per_bin"]:
            lo = f"{d['lo']:>10,.0f}원" if d['lo'] else "    -inf"
            hi = f"{d['hi']:>10,.0f}원" if d['hi'] else "    +inf"
            logger.info(
                f"    {lo}~{hi}: "
                f"{d['train_resid']:+.3f} → {d['test_resid']:+.3f} "
                f"(drift {d['drift']:+.3f})"
            )
    summary["3_calibration_drift"] = drift_results

    with (RESULTS / "stage3_final_validation.json").open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(
        f"\nSaved: {(RESULTS / 'stage3_final_validation.json').relative_to(ROOT)}"
    )


if __name__ == "__main__":
    run()
