"""Stage 4 Low-price Error Decomposition (사전등록 적용).

사전등록: docs/stage4_low_price_decomp_prereg_20260507.md
- Low-price 정의: price_krw < 5,000,000 (운영 guardrail)
- 지표 3개: bias / residual spread / artist support
- 판정: feature 부족 (1순위) / loss 한계 (2순위) / support 부족 (3순위) / calibration (4순위)
- 비목표: 재학습 / 모델 변경 (별도 후속)
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
DATA = ROOT / "data" / "curated" / "stage4_full.parquet"
ARTSY_RAW = ROOT / "data" / "artsy_kr_artworks.csv"
RESULTS = Path(__file__).parent / "results"
LOW_PRICE_KRW = 5_000_000


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
    fe_cols = {f"artist_{a}": (df["artist_slug"] == a).astype(float).values for a in warm_artists}
    return pd.concat([X, pd.DataFrame(fe_cols, index=X.index)], axis=1)


def fit_huber(Xtr, ytr, Xte, eps=1.35, alpha=0.0001):
    m = HuberRegressor(epsilon=eps, alpha=alpha, max_iter=2000)
    m.fit(Xtr[:, 1:], ytr)
    return Xte[:, 1:] @ m.coef_ + m.intercept_


def run():
    df = pd.read_parquet(DATA)
    y = df["log_price"]
    train_mask = (df["split"] == "train").values
    test_mask = ((df["split"] == "test") & df["is_test_eligible"].values & df["is_warm_artist"].values)

    warm_artists = set(df[train_mask & df["is_warm_artist"]]["artist_slug"].unique())
    logger.info("=" * 80)
    logger.info("Stage 4 Low-price Error Decomposition (사전등록 적용)")
    logger.info("=" * 80)
    logger.info(f"Test-eligible warm: {test_mask.sum()} 작품 / {len(warm_artists)} train warm artists")

    # 1. Predictions (baseline + FE only, 사전등록 §2)
    Xb = build_X_baseline(df)
    X_fe = add_artist_fe(Xb, df, warm_artists)

    Xtr_b = Xb[train_mask].values.astype(float)
    Xte_b = Xb[test_mask].values.astype(float)
    Xtr_fe = X_fe[train_mask].values.astype(float)
    Xte_fe = X_fe[test_mask].values.astype(float)
    ytr = y[train_mask].values.astype(float)
    yte = y[test_mask].values.astype(float)

    pred_b = fit_huber(Xtr_b, ytr, Xte_b)
    pred_fe = fit_huber(Xtr_fe, ytr, Xte_fe)

    df_te = df[test_mask].reset_index(drop=True)
    is_low = (df_te["price_krw"] < LOW_PRICE_KRW).values
    is_high = ~is_low

    summary = {
        "low_price_threshold_krw": LOW_PRICE_KRW,
        "n_test_low": int(is_low.sum()),
        "n_test_mid_high": int(is_high.sum()),
    }
    logger.info(f"\n--- 1. Slicing ({summary['n_test_low']} low / {summary['n_test_mid_high']} mid-high) ---")

    # 2. Bias / spread (사전등록 §3 지표 1, 2)
    logger.info(f"\n--- 2. Bias / Residual spread ---")
    decomp = {}
    for label, model_pred in [("baseline", pred_b), ("fe_only", pred_fe)]:
        residuals = model_pred - yte
        decomp_model = {}
        for slice_label, mask in [("low", is_low), ("mid_high", is_high)]:
            r = residuals[mask]
            decomp_model[slice_label] = {
                "n": int(mask.sum()),
                "bias_log": float(r.mean()),
                "bias_pct": float((np.exp(r.mean()) - 1) * 100),  # %
                "residual_std": float(r.std()),
                "residual_iqr": float(np.percentile(r, 75) - np.percentile(r, 25)),
            }
        decomp[label] = decomp_model
        logger.info(f"  [{label}]")
        for s, m in decomp_model.items():
            logger.info(f"    {s} (n={m['n']}): bias log {m['bias_log']:+.3f} ({m['bias_pct']:+.1f}%), std {m['residual_std']:.3f}, IQR {m['residual_iqr']:.3f}")
    summary["bias_spread"] = decomp

    # 3. Artist support (사전등록 §3 지표 3)
    logger.info(f"\n--- 3. Artist support ---")
    train_df = df[train_mask]
    train_counts = train_df.groupby("artist_slug").size()
    test_low_artists = set(df_te[is_low]["artist_slug"].unique())
    test_high_artists = set(df_te[is_high]["artist_slug"].unique())

    support_low = train_counts[list(test_low_artists & set(train_counts.index))].values
    support_high = train_counts[list(test_high_artists & set(train_counts.index))].values

    sup = {
        "low_n_artists": int(len(test_low_artists)),
        "low_train_works_median": float(np.median(support_low)) if len(support_low) else None,
        "low_train_works_p25": float(np.percentile(support_low, 25)) if len(support_low) else None,
        "low_train_works_p75": float(np.percentile(support_low, 75)) if len(support_low) else None,
        "high_n_artists": int(len(test_high_artists)),
        "high_train_works_median": float(np.median(support_high)) if len(support_high) else None,
        "high_train_works_p25": float(np.percentile(support_high, 25)) if len(support_high) else None,
        "high_train_works_p75": float(np.percentile(support_high, 75)) if len(support_high) else None,
    }
    logger.info(f"  Low-price test artists ({sup['low_n_artists']}): train works median {sup['low_train_works_median']}, P25 {sup['low_train_works_p25']}, P75 {sup['low_train_works_p75']}")
    logger.info(f"  Mid-high test artists ({sup['high_n_artists']}): train works median {sup['high_train_works_median']}, P25 {sup['high_train_works_p25']}, P75 {sup['high_train_works_p75']}")
    summary["artist_support"] = sup

    # 4. Proxy variable analysis (사전등록 §3 부수) — stage4_full 이 raw 컬럼 모두 포함
    logger.info(f"\n--- 4. Proxy variables (현재 모델 미사용 컬럼) ---")
    proxy_summary = {}
    for col in ["medium_type", "category", "availability", "gallery_type", "attribution_class"]:
        if col not in df_te.columns:
            logger.info(f"  [{col}] 컬럼 없음 — skip")
            continue
        low_vals = df_te.loc[is_low, col]
        high_vals = df_te.loc[is_high, col]
        low_dist = low_vals.value_counts(normalize=True, dropna=False).head(3).to_dict()
        high_dist = high_vals.value_counts(normalize=True, dropna=False).head(3).to_dict()
        proxy_summary[col] = {
            "low_top3": {str(k): float(v) for k, v in low_dist.items()},
            "high_top3": {str(k): float(v) for k, v in high_dist.items()},
            "low_missing_rate": float(low_vals.isna().mean()),
            "high_missing_rate": float(high_vals.isna().mean()),
        }
        logger.info(f"  [{col}] low missing {proxy_summary[col]['low_missing_rate']:.1%} / high missing {proxy_summary[col]['high_missing_rate']:.1%}")
        logger.info(f"    low top3: {[(str(k)[:25], f'{v:.1%}') for k,v in list(low_dist.items())[:3]]}")
        logger.info(f"    high top3: {[(str(k)[:25], f'{v:.1%}') for k,v in list(high_dist.items())[:3]]}")
    summary["proxy_variables"] = proxy_summary

    # 5. 판정 시그니처 (사전등록 §5)
    logger.info(f"\n--- 5. 가설 시그니처 판정 (사전등록 §5) ---")
    low_b = decomp["fe_only"]["low"]
    high_b = decomp["fe_only"]["mid_high"]

    # 시그니처 평가
    bias_diff = abs(low_b["bias_log"] - high_b["bias_log"])
    spread_diff = low_b["residual_std"] - high_b["residual_std"]
    support_ratio = (sup["low_train_works_median"] / sup["high_train_works_median"]) if sup["high_train_works_median"] else None

    logger.info(f"  Bias 차이 (|low - high|): {bias_diff:.3f} log")
    logger.info(f"  Spread 차이 (low - high): {spread_diff:+.3f} log std")
    logger.info(f"  Support 비율 (low / high median train works): {support_ratio:.2f}")

    sig = {
        "feature_signature": {
            "bias_structural": bias_diff > 0.1,
            "spread_high_low": spread_diff > 0.1,
            "support_sufficient": support_ratio >= 0.7 if support_ratio else False,
        },
        "loss_signature": {
            "bias_small": abs(low_b["bias_log"]) < 0.05,
            "spread_high_low": spread_diff > 0.1,
            "support_sufficient": support_ratio >= 0.7 if support_ratio else False,
        },
        "support_signature": {
            "low_support_smaller": (support_ratio is not None) and (support_ratio < 0.5),
        },
        "calibration_signature": {
            "bias_only": (abs(low_b["bias_log"]) > 0.1) and (spread_diff < 0.05),
        },
    }
    summary["hypothesis_signatures"] = sig
    logger.info(f"\n  [시그니처]")
    for hyp, items in sig.items():
        n_match = sum(items.values())
        logger.info(f"    {hyp}: {n_match}/{len(items)} 일치 — {items}")

    # 최종 가설 우선순위
    n_feature = sum(sig["feature_signature"].values())
    n_loss = sum(sig["loss_signature"].values())
    n_support = sum(sig["support_signature"].values())
    n_calib = sum(sig["calibration_signature"].values())
    scores = {"feature": n_feature, "loss": n_loss, "support": n_support, "calibration": n_calib}
    winner = max(scores.items(), key=lambda x: x[1])
    summary["winner_hypothesis"] = {"name": winner[0], "score": winner[1], "all_scores": scores}
    logger.info(f"\n  → 최우세 가설: {winner[0]} (score {winner[1]})")

    out = RESULTS / "stage4_low_price_decomp.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(f"\nSaved: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    run()
