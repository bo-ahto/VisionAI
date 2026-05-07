"""Stage 3 Quantile Regression Cycle — 운영 가격 범위 산출.

코덱스 권고:
- Linear QuantileRegressor (sklearn) — F4 + log_area spline
- Quantile q25 / q50 / q75 (3 quantile)
- Independent fit + post-hoc sorting
- Metric: Pinball loss / Coverage / Width / Raw crossing rate
- Slice: 가격 tertile / ink / tier 3 / extreme area

평가:
- Cold-start LAO 100-seed (primary)
- Time-split 2022/2023/2024 (참고)
- Slice harm (가드레일 segment)
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import HuberRegressor, QuantileRegressor

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent.parent
DATA = ROOT / "data" / "curated" / "stage3_1000x100.parquet"
RESULTS = Path(__file__).parent / "results"
N_SEEDS = 100
QUANTILES = [0.25, 0.50, 0.75]


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


def lao_split(df, seed):
    rng = np.random.default_rng(seed)
    artists = df["artist_slug"].unique()
    n_test = max(1, int(len(artists) * 0.2))
    test_artists = set(rng.choice(artists, size=n_test, replace=False))
    test_mask = df["artist_slug"].isin(test_artists).values
    return ~test_mask, test_mask


def fit_quantile(Xtr, ytr, Xte, q, alpha=0.0001):
    """Linear quantile regression. Returns predictions on Xte."""
    m = QuantileRegressor(quantile=q, alpha=alpha, solver="highs")
    m.fit(Xtr[:, 1:], ytr)
    return Xte[:, 1:] @ m.coef_ + m.intercept_


def fit_huber(Xtr, ytr, Xte, eps=1.35, alpha=0.0001):
    m = HuberRegressor(epsilon=eps, alpha=alpha, max_iter=2000)
    m.fit(Xtr[:, 1:], ytr)
    return Xte[:, 1:] @ m.coef_ + m.intercept_


def pinball_loss(y, pred, q):
    err = y - pred
    return float(np.mean(np.maximum(q * err, (q - 1) * err)))


def coverage(y, pred):
    return float((y <= pred).mean())


def central_coverage(y, pred_lo, pred_hi):
    return float(((y >= pred_lo) & (y <= pred_hi)).mean())


def width_avg(pred_lo, pred_hi):
    return float(np.mean(pred_hi - pred_lo))


def crossing_rate_raw(pred_q25, pred_q50, pred_q75):
    """Raw monotone violation rate."""
    violations = (pred_q25 > pred_q50) | (pred_q50 > pred_q75)
    return float(violations.mean())


def post_hoc_sort(pred_q25, pred_q50, pred_q75):
    """Sort each row to ensure q25 ≤ q50 ≤ q75."""
    stacked = np.column_stack([pred_q25, pred_q50, pred_q75])
    sorted_arr = np.sort(stacked, axis=1)
    return sorted_arr[:, 0], sorted_arr[:, 1], sorted_arr[:, 2]


def mdape(y, pred):
    return float(np.median(np.abs(np.exp(pred) - np.exp(y)) / np.exp(y)) * 100)


# ─────────────────────────────────────
# M2 baseline: Huber + global residual quantile band
# ─────────────────────────────────────
def fit_huber_residual_band(Xtr, ytr, Xte):
    """Fit Huber on train, derive residual quantile from train, apply to test."""
    pred_tr = fit_huber(Xtr, ytr, Xtr)
    residuals = ytr - pred_tr
    q25_resid = float(np.quantile(residuals, 0.25))
    q75_resid = float(np.quantile(residuals, 0.75))

    pred_te_point = fit_huber(Xtr, ytr, Xte)
    return {
        "q25": pred_te_point + q25_resid,
        "q50": pred_te_point,
        "q75": pred_te_point + q75_resid,
    }


# ─────────────────────────────────────
# One-seed evaluation
# ─────────────────────────────────────
def eval_one_seed(df_feat, y, seed, model_type="quantile"):
    train_mask, test_mask = lao_split(df_feat, seed)
    Xb = build_X_baseline(df_feat)
    Xtr = Xb[train_mask].values.astype(float)
    Xte = Xb[test_mask].values.astype(float)
    ytr = y[train_mask].values.astype(float)
    yte = y[test_mask].values.astype(float)

    if model_type == "quantile":
        pred_q25_raw = fit_quantile(Xtr, ytr, Xte, q=0.25)
        pred_q50_raw = fit_quantile(Xtr, ytr, Xte, q=0.50)
        pred_q75_raw = fit_quantile(Xtr, ytr, Xte, q=0.75)
        crossing_raw = crossing_rate_raw(pred_q25_raw, pred_q50_raw, pred_q75_raw)
        pred_q25, pred_q50, pred_q75 = post_hoc_sort(pred_q25_raw, pred_q50_raw, pred_q75_raw)
    elif model_type == "huber_residual":
        pb = fit_huber_residual_band(Xtr, ytr, Xte)
        pred_q25, pred_q50, pred_q75 = pb["q25"], pb["q50"], pb["q75"]
        crossing_raw = 0.0  # by construction monotone
    else:
        raise ValueError(model_type)

    return {
        "yte": yte,
        "q25": pred_q25,
        "q50": pred_q50,
        "q75": pred_q75,
        "crossing_raw": crossing_raw,
        "df_eval_idx": np.where(test_mask)[0],
    }


def aggregate_seeds(df_feat, y, model_type, n_seeds=N_SEEDS):
    pinball_q25, pinball_q50, pinball_q75 = [], [], []
    cov_q25, cov_q50, cov_q75 = [], [], []
    cov_central, widths, crossings, q50_mdapes = [], [], [], []

    for s in range(n_seeds):
        try:
            r = eval_one_seed(df_feat, y, s, model_type)
        except Exception:
            continue
        yte = r["yte"]
        pinball_q25.append(pinball_loss(yte, r["q25"], 0.25))
        pinball_q50.append(pinball_loss(yte, r["q50"], 0.50))
        pinball_q75.append(pinball_loss(yte, r["q75"], 0.75))
        cov_q25.append(coverage(yte, r["q25"]))
        cov_q50.append(coverage(yte, r["q50"]))
        cov_q75.append(coverage(yte, r["q75"]))
        cov_central.append(central_coverage(yte, r["q25"], r["q75"]))
        widths.append(width_avg(r["q25"], r["q75"]))
        crossings.append(r["crossing_raw"])
        q50_mdapes.append(mdape(yte, r["q50"]))

    return {
        "model": model_type,
        "n_seeds_kept": len(pinball_q25),
        "pinball_q25_mean": float(np.mean(pinball_q25)),
        "pinball_q50_mean": float(np.mean(pinball_q50)),
        "pinball_q75_mean": float(np.mean(pinball_q75)),
        "pinball_total": float(np.mean(pinball_q25) + np.mean(pinball_q50) + np.mean(pinball_q75)),
        "coverage_q25": float(np.mean(cov_q25)),
        "coverage_q50": float(np.mean(cov_q50)),
        "coverage_q75": float(np.mean(cov_q75)),
        "central_coverage_q25_q75": float(np.mean(cov_central)),
        "width_avg_log_price": float(np.mean(widths)),
        "crossing_rate_raw": float(np.mean(crossings)),
        "q50_mdape_mean": float(np.mean(q50_mdapes)),
        "q50_mdape_std": float(np.std(q50_mdapes)),
    }


# ─────────────────────────────────────
# Slice analysis (single seed for clarity)
# ─────────────────────────────────────
def slice_analysis(df_feat, y, model_type, seed=42):
    """Per-slice coverage / width."""
    train_mask, test_mask = lao_split(df_feat, seed)
    df_eval = df_feat[test_mask].reset_index(drop=True)
    r = eval_one_seed(df_feat, y, seed, model_type)
    yte = r["yte"]

    rows = []
    # Price tertile (KRW)
    prices = np.exp(yte)
    qs = np.quantile(prices, [0.33, 0.67])
    for label, lo, hi in [("저가 (P33↓)", -np.inf, qs[0]),
                          ("중가 (P33-67)", qs[0], qs[1]),
                          ("고가 (P67↑)", qs[1], np.inf)]:
        m = (prices > lo) & (prices <= hi)
        if m.sum() < 5:
            continue
        rows.append({
            "slice_type": "price_tertile",
            "label": label,
            "n": int(m.sum()),
            "coverage_q25": coverage(yte[m], r["q25"][m]),
            "coverage_q50": coverage(yte[m], r["q50"][m]),
            "coverage_q75": coverage(yte[m], r["q75"][m]),
            "central_coverage": central_coverage(yte[m], r["q25"][m], r["q75"][m]),
            "width_avg": width_avg(r["q25"][m], r["q75"][m]),
        })
    # 가드레일 segments
    for col, val, label in [("medium_category", "ink", "medium=ink"),
                            ("gallery_tier", 3, "tier=3")]:
        m = (df_eval[col] == val).values
        if m.sum() < 5:
            continue
        rows.append({
            "slice_type": "guardrail",
            "label": label,
            "n": int(m.sum()),
            "coverage_q25": coverage(yte[m], r["q25"][m]),
            "coverage_q50": coverage(yte[m], r["q50"][m]),
            "coverage_q75": coverage(yte[m], r["q75"][m]),
            "central_coverage": central_coverage(yte[m], r["q25"][m], r["q75"][m]),
            "width_avg": width_avg(r["q25"][m], r["q75"][m]),
        })
    # Extreme area (P5/P95 of train)
    train_log_area = df_feat[train_mask]["log_area"].values
    p5, p95 = np.percentile(train_log_area, [5, 95])
    eval_log_area = df_eval["log_area"].values
    m = (eval_log_area < p5) | (eval_log_area > p95)
    if m.sum() >= 5:
        rows.append({
            "slice_type": "guardrail",
            "label": "extreme_area (<P5 or >P95)",
            "n": int(m.sum()),
            "coverage_q25": coverage(yte[m], r["q25"][m]),
            "coverage_q50": coverage(yte[m], r["q50"][m]),
            "coverage_q75": coverage(yte[m], r["q75"][m]),
            "central_coverage": central_coverage(yte[m], r["q25"][m], r["q75"][m]),
            "width_avg": width_avg(r["q25"][m], r["q75"][m]),
        })
    return rows


# ─────────────────────────────────────
# Main
# ─────────────────────────────────────
def run():
    df = pd.read_parquet(DATA)
    df_feat = make_features(df)
    y = df_feat["log_price"]

    summary = {"n_seeds": N_SEEDS, "quantiles": QUANTILES}

    logger.info("=" * 80)
    logger.info("Stage 3 Quantile Regression Cycle (코덱스 권고)")
    logger.info("=" * 80)

    # M1: Linear Quantile
    logger.info(f"\n--- M1: Linear Quantile (q25/q50/q75 independent + post-hoc sort) ---")
    m1 = aggregate_seeds(df_feat, y, "quantile", n_seeds=N_SEEDS)
    summary["M1_quantile"] = m1
    logger.info(f"  n_seeds_kept: {m1['n_seeds_kept']}")
    logger.info(f"  Pinball loss — q25: {m1['pinball_q25_mean']:.4f} / q50: {m1['pinball_q50_mean']:.4f} / q75: {m1['pinball_q75_mean']:.4f}")
    logger.info(f"  Pinball total: {m1['pinball_total']:.4f}")
    logger.info(f"  Coverage — q25: {m1['coverage_q25']:.1%} (목표 25%) / q50: {m1['coverage_q50']:.1%} (목표 50%) / q75: {m1['coverage_q75']:.1%} (목표 75%)")
    logger.info(f"  Central coverage q25-q75: {m1['central_coverage_q25_q75']:.1%} (목표 50%)")
    logger.info(f"  Width avg (log price): {m1['width_avg_log_price']:.3f}")
    logger.info(f"  Raw crossing rate: {m1['crossing_rate_raw']:.1%} (목표 ≤5%)")
    logger.info(f"  q50 MdAPE: {m1['q50_mdape_mean']:.2f}% (운영 baseline 24.27%)")

    # M2: Huber + residual band
    logger.info(f"\n--- M2: Huber + global residual quantile band (baseline 비교) ---")
    m2 = aggregate_seeds(df_feat, y, "huber_residual", n_seeds=N_SEEDS)
    summary["M2_huber_residual"] = m2
    logger.info(f"  Pinball total: {m2['pinball_total']:.4f}")
    logger.info(f"  Coverage — q25: {m2['coverage_q25']:.1%} / q50: {m2['coverage_q50']:.1%} / q75: {m2['coverage_q75']:.1%}")
    logger.info(f"  Central coverage q25-q75: {m2['central_coverage_q25_q75']:.1%}")
    logger.info(f"  Width avg (log price): {m2['width_avg_log_price']:.3f}")
    logger.info(f"  q50 MdAPE: {m2['q50_mdape_mean']:.2f}%")

    # 비교
    logger.info(f"\n--- M1 vs M2 비교 ---")
    pinball_better = "M1 우위" if m1["pinball_total"] < m2["pinball_total"] else "M2 우위"
    width_better = "M1 좁음" if m1["width_avg_log_price"] < m2["width_avg_log_price"] else "M2 좁음"
    logger.info(f"  Pinball total: M1={m1['pinball_total']:.4f} vs M2={m2['pinball_total']:.4f} → {pinball_better}")
    logger.info(f"  Width: M1={m1['width_avg_log_price']:.3f} vs M2={m2['width_avg_log_price']:.3f} → {width_better}")
    logger.info(f"  q50 MdAPE: M1={m1['q50_mdape_mean']:.2f}% vs M2={m2['q50_mdape_mean']:.2f}%")

    # Slice analysis (M1)
    logger.info(f"\n--- M1 Slice analysis (single seed=42) ---")
    slices = slice_analysis(df_feat, y, "quantile", seed=42)
    summary["M1_slices"] = slices
    logger.info(f"\n  {'slice':>30} {'n':>4} {'cov_q25':>9} {'cov_q50':>9} {'cov_q75':>9} {'central':>9} {'width':>7}")
    for s in slices:
        logger.info(
            f"  {s['label']:>30} {s['n']:>4} "
            f"{s['coverage_q25']:>7.1%} {s['coverage_q50']:>7.1%} {s['coverage_q75']:>7.1%} "
            f"{s['central_coverage']:>7.1%} {s['width_avg']:>5.2f}"
        )

    # 합격 판정
    logger.info(f"\n--- 합격 기준 판정 (사전 고정 §4.1) ---")
    checks = []
    checks.append(("Pinball M1 < M2", m1["pinball_total"] < m2["pinball_total"]))
    checks.append(("q25 cov ∈ [20%, 30%]", 0.20 <= m1["coverage_q25"] <= 0.30))
    checks.append(("q50 cov ∈ [45%, 55%]", 0.45 <= m1["coverage_q50"] <= 0.55))
    checks.append(("q75 cov ∈ [70%, 80%]", 0.70 <= m1["coverage_q75"] <= 0.80))
    checks.append(("central cov ∈ [45%, 55%]", 0.45 <= m1["central_coverage_q25_q75"] <= 0.55))
    checks.append(("q50 MdAPE 운영 +1%p 이내", m1["q50_mdape_mean"] - 24.27 <= 1.0))
    checks.append(("crossing rate ≤ 5%", m1["crossing_rate_raw"] <= 0.05))
    checks.append(("Width M1 ≤ M2", m1["width_avg_log_price"] <= m2["width_avg_log_price"]))

    summary["checks"] = []
    for name, ok in checks:
        logger.info(f"  {'✓' if ok else '✗'} {name}")
        summary["checks"].append({"name": name, "pass": bool(ok)})

    n_pass = sum(1 for _, ok in checks if ok)
    logger.info(f"\n  → {n_pass}/{len(checks)} 합격 기준 통과")
    if n_pass == len(checks):
        verdict = "합격 (운영 shadow / internal flag 도입 가능)"
    elif n_pass >= len(checks) - 2:
        verdict = "보류 (1-2 항목 재시도 필요)"
    else:
        verdict = "폐기 (본 cycle 종결, ±20% band 유지)"
    logger.info(f"  판정: {verdict}")
    summary["verdict"] = verdict
    summary["n_pass"] = n_pass
    summary["n_total_checks"] = len(checks)

    out = RESULTS / "stage3_quantile_regression.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(f"\nSaved: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    run()
