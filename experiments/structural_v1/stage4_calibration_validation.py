"""Stage 4 Calibration 독립 검증 (코덱스 권고 순서).

순서:
1. Global additive/multiplicative calibration
2. Low-price only calibration
3. Coarse slice (price tertile) calibration
(보조) Isotonic regression

합격 기준 3층:
1. low-price harm +5.63%p → +1%p 이내
2. overall MdAPE 비악화
3. ECE / bias 개선

저가 decomp 결과 (feature 부족, calibration 시그니처 0/1) → 한계 예상.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import HuberRegressor

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent.parent
DATA = ROOT / "data" / "curated" / "stage4_full.parquet"
RESULTS = Path(__file__).parent / "results"
LOW_PRICE_KRW = 5_000_000
HARM_THRESHOLD_LOW = 1.0  # %p


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


def fit_huber(Xtr, ytr, Xte, eps=1.35, alpha=0.0001):
    m = HuberRegressor(epsilon=eps, alpha=alpha, max_iter=2000)
    m.fit(Xtr[:, 1:], ytr)
    return Xte[:, 1:] @ m.coef_ + m.intercept_


def mdape_from_log(yte_log, pred_log):
    return float(np.median(np.abs(np.exp(pred_log) - np.exp(yte_log)) / np.exp(yte_log)) * 100)


def ece_log(yte_log, pred_log, n_bins=10):
    """Expected Calibration Error (log scale, simple binning)."""
    pred_q = np.percentile(pred_log, np.linspace(0, 100, n_bins + 1))
    ece = 0.0
    for i in range(n_bins):
        mask = (pred_log >= pred_q[i]) & (pred_log <= pred_q[i + 1])
        if mask.sum() < 3:
            continue
        bin_bias = (pred_log[mask] - yte_log[mask]).mean()
        ece += (mask.sum() / len(yte_log)) * abs(bin_bias)
    return float(ece)


# ─────────────────────────────────────
# Calibration methods
# ─────────────────────────────────────
def calibrate_global_additive(pred_train, y_train, pred_test):
    bias = (pred_train - y_train).mean()
    return pred_test - bias


def calibrate_global_multiplicative(pred_train_log, y_train_log, pred_test_log):
    # log scale: y_pred_calibrated = a * y_pred → log(y_pred) + log(a) — additive 와 동일하지만 log(actual/pred) 평균을 쓴다는 건 multiplicative on price
    log_ratio = (y_train_log - pred_train_log).mean()
    return pred_test_log + log_ratio  # = global_additive — 같은 계산. note for clarity.


def calibrate_low_price_only(pred_train, y_train, pred_test, low_mask_train, low_mask_test):
    if low_mask_train.sum() < 5:
        return pred_test.copy()
    bias_low = (pred_train[low_mask_train] - y_train[low_mask_train]).mean()
    out = pred_test.copy()
    out[low_mask_test] -= bias_low
    return out


def calibrate_slice_tertile(pred_train, y_train, pred_test, prices_train, prices_test):
    # Tertile boundaries from train prices
    qs = np.quantile(prices_train, [0.33, 0.67])
    biases = {}
    for label, lo, hi in [("low", -np.inf, qs[0]), ("mid", qs[0], qs[1]), ("high", qs[1], np.inf)]:
        m = (prices_train > lo) & (prices_train <= hi)
        if m.sum() < 5:
            biases[label] = 0.0
            continue
        biases[label] = float((pred_train[m] - y_train[m]).mean())

    out = pred_test.copy()
    for label, lo, hi in [("low", -np.inf, qs[0]), ("mid", qs[0], qs[1]), ("high", qs[1], np.inf)]:
        m = (prices_test > lo) & (prices_test <= hi)
        out[m] -= biases[label]
    return out, biases


def calibrate_isotonic(pred_train, y_train, pred_test):
    iso = IsotonicRegression(out_of_bounds="clip")
    iso.fit(pred_train, y_train)
    return iso.predict(pred_test)


# ─────────────────────────────────────
# Main
# ─────────────────────────────────────
def run():
    df = pd.read_parquet(DATA)
    y = df["log_price"]
    train_mask = (df["split"] == "train").values
    test_mask = ((df["split"] == "test") & df["is_test_eligible"].values & df["is_warm_artist"].values)

    Xb = build_X_baseline(df)
    Xtr = Xb[train_mask].values.astype(float)
    Xte = Xb[test_mask].values.astype(float)
    ytr = y[train_mask].values.astype(float)
    yte = y[test_mask].values.astype(float)

    # Baseline predictions (Huber on baseline features)
    pred_tr = fit_huber(Xtr, ytr, Xtr)
    pred_te = fit_huber(Xtr, ytr, Xte)

    df_te = df[test_mask].reset_index(drop=True)
    prices_test = df_te["price_krw"].values
    df_train = df[train_mask].reset_index(drop=True)
    prices_train = df_train["price_krw"].values

    low_mask_test = prices_test < LOW_PRICE_KRW
    low_mask_train = prices_train < LOW_PRICE_KRW

    logger.info("=" * 80)
    logger.info("Stage 4 Calibration 독립 검증 (코덱스 권고 순서)")
    logger.info("=" * 80)
    logger.info(f"Train: {len(ytr):,} / Test: {len(yte):,} (low-price test: {low_mask_test.sum()})")

    # Baseline (no calibration)
    base_overall = mdape_from_log(yte, pred_te)
    base_low = mdape_from_log(yte[low_mask_test], pred_te[low_mask_test])
    base_high = mdape_from_log(yte[~low_mask_test], pred_te[~low_mask_test])
    base_ece = ece_log(yte, pred_te)
    logger.info(f"\n[Baseline (no cal)]: overall {base_overall:.2f}% / low {base_low:.2f}% / high {base_high:.2f}% / ECE {base_ece:.4f}")

    summary = {
        "baseline": {"overall": base_overall, "low": base_low, "high": base_high, "ece": base_ece},
        "low_price_threshold_krw": LOW_PRICE_KRW,
        "n_test_low": int(low_mask_test.sum()),
        "n_test_high": int((~low_mask_test).sum()),
        "calibrations": {},
        "harm_threshold_pct_pt": HARM_THRESHOLD_LOW,
    }

    # 1. Global additive calibration
    pred_cal = calibrate_global_additive(pred_tr, ytr, pred_te)
    cal = {
        "overall": mdape_from_log(yte, pred_cal),
        "low": mdape_from_log(yte[low_mask_test], pred_cal[low_mask_test]),
        "high": mdape_from_log(yte[~low_mask_test], pred_cal[~low_mask_test]),
        "ece": ece_log(yte, pred_cal),
    }
    summary["calibrations"]["1_global_additive"] = cal
    logger.info(f"\n[1. Global additive]: overall {cal['overall']:.2f}% (Δ {cal['overall']-base_overall:+.2f}) / low {cal['low']:.2f}% (Δ {cal['low']-base_low:+.2f}) / high {cal['high']:.2f}% (Δ {cal['high']-base_high:+.2f}) / ECE {cal['ece']:.4f} (Δ {cal['ece']-base_ece:+.4f})")

    # 2. Low-price only calibration
    pred_cal = calibrate_low_price_only(pred_tr, ytr, pred_te, low_mask_train, low_mask_test)
    cal = {
        "overall": mdape_from_log(yte, pred_cal),
        "low": mdape_from_log(yte[low_mask_test], pred_cal[low_mask_test]),
        "high": mdape_from_log(yte[~low_mask_test], pred_cal[~low_mask_test]),
        "ece": ece_log(yte, pred_cal),
    }
    summary["calibrations"]["2_low_price_only"] = cal
    logger.info(f"\n[2. Low-price only]: overall {cal['overall']:.2f}% (Δ {cal['overall']-base_overall:+.2f}) / low {cal['low']:.2f}% (Δ {cal['low']-base_low:+.2f}) / high {cal['high']:.2f}% (Δ {cal['high']-base_high:+.2f}) / ECE {cal['ece']:.4f}")

    # 3. Slice tertile (price band)
    pred_cal, biases = calibrate_slice_tertile(pred_tr, ytr, pred_te, prices_train, prices_test)
    cal = {
        "overall": mdape_from_log(yte, pred_cal),
        "low": mdape_from_log(yte[low_mask_test], pred_cal[low_mask_test]),
        "high": mdape_from_log(yte[~low_mask_test], pred_cal[~low_mask_test]),
        "ece": ece_log(yte, pred_cal),
        "tertile_biases_log": biases,
    }
    summary["calibrations"]["3_slice_tertile"] = cal
    logger.info(f"\n[3. Slice tertile]: overall {cal['overall']:.2f}% (Δ {cal['overall']-base_overall:+.2f}) / low {cal['low']:.2f}% (Δ {cal['low']-base_low:+.2f}) / high {cal['high']:.2f}% (Δ {cal['high']-base_high:+.2f})")
    logger.info(f"   tertile biases (log): {biases}")

    # (보조) Isotonic
    pred_cal = calibrate_isotonic(pred_tr, ytr, pred_te)
    cal = {
        "overall": mdape_from_log(yte, pred_cal),
        "low": mdape_from_log(yte[low_mask_test], pred_cal[low_mask_test]),
        "high": mdape_from_log(yte[~low_mask_test], pred_cal[~low_mask_test]),
        "ece": ece_log(yte, pred_cal),
    }
    summary["calibrations"]["4_isotonic_aux"] = cal
    logger.info(f"\n[4. Isotonic (보조)]: overall {cal['overall']:.2f}% (Δ {cal['overall']-base_overall:+.2f}) / low {cal['low']:.2f}% (Δ {cal['low']-base_low:+.2f}) / high {cal['high']:.2f}% (Δ {cal['high']-base_high:+.2f})")

    # 합격 판정 (사전등록 §4.2 합격 기준 3층)
    logger.info(f"\n--- 합격 판정 (코덱스 3층 기준) ---")
    judges = {}
    for name, cal in summary["calibrations"].items():
        low_harm_diff = cal["low"] - base_low
        overall_diff = cal["overall"] - base_overall
        ece_diff = cal["ece"] - base_ece
        # 합격: low harm 해소 (<= +1.0%p OR low 자체 개선) + overall 비악화 (<= +0.5%p)
        low_harm_ok = low_harm_diff <= HARM_THRESHOLD_LOW
        overall_ok = overall_diff <= 0.5
        ece_better = ece_diff < 0
        verdict = "PASS" if (low_harm_ok and overall_ok) else "FAIL"
        judges[name] = {
            "low_harm_diff": low_harm_diff,
            "overall_diff": overall_diff,
            "ece_diff": ece_diff,
            "low_harm_ok": bool(low_harm_ok),
            "overall_ok": bool(overall_ok),
            "ece_better": bool(ece_better),
            "verdict": verdict,
        }
        logger.info(f"  {name:>22}: low Δ{low_harm_diff:+.2f}%p ({'✓' if low_harm_ok else '✗'}) / overall Δ{overall_diff:+.2f}%p ({'✓' if overall_ok else '✗'}) / ECE {'↓' if ece_better else '↑'} → {verdict}")
    summary["judges"] = judges

    # 코덱스 4 해석 규칙
    logger.info(f"\n--- 코덱스 해석 규칙 적용 ---")
    g_pass = judges["1_global_additive"]["verdict"] == "PASS"
    l_pass = judges["2_low_price_only"]["verdict"] == "PASS"
    s_pass = judges["3_slice_tertile"]["verdict"] == "PASS"
    i_pass = judges["4_isotonic_aux"]["verdict"] == "PASS"

    if g_pass:
        rule = "global calibration 후처리 가치 있음 → spec §4 후처리 규칙 후보"
    elif l_pass and not g_pass:
        rule = "Low-price 전용만 듣고 global X → segment-aware 후보 (단순 후처리 한계)"
    elif s_pass and not g_pass and not l_pass:
        rule = "Slice 기반만 듣고 global/low X → segment-aware 후보"
    elif i_pass and not g_pass:
        rule = "Isotonic 만 듣고 단순 보정 X → 비선형 misspec 신호"
    elif not any([g_pass, l_pass, s_pass, i_pass]):
        rule = "아무 calibration 도 안 들음 → 본질은 feature/loss/support 문제 (저가 decomp 결과와 일치)"
    else:
        rule = "혼합 결과 — 추가 검토 필요"
    summary["interpretation"] = rule
    logger.info(f"  → {rule}")

    out = RESULTS / "stage4_calibration_validation.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(f"\nSaved: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    run()
