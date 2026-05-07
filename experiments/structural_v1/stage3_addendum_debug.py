"""Stage 3 Addendum 디버깅 + Huber alpha sensitivity (코덱스 D + E).

D. artist_sales_count_log +27%p 악화 디버깅
   - LAO 에서 unseen artist 비율 / fillna(0) 비중 / 분포 확인
E. Huber alpha sensitivity
   - alpha 1e-4 / 1e-2 / 1 / 10 sweep
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import HuberRegressor

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent.parent
DATA = ROOT / "data" / "curated" / "stage3_1000x100.parquet"
RESULTS = Path(__file__).parent / "results"
N_SEEDS = 100


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


def fit_huber(Xtr, ytr, Xte, eps=1.35, alpha=0.0001):
    m = HuberRegressor(epsilon=eps, alpha=alpha, max_iter=2000)
    m.fit(Xtr[:, 1:], ytr)
    return Xte[:, 1:] @ m.coef_ + m.intercept_, m.coef_, m.intercept_


def mdape(yte, pred):
    return float(np.median(np.abs(np.exp(pred) - np.exp(yte)) / np.exp(yte)) * 100)


# ─────────────────────────────────────
# D. artist_sales_count_log 디버깅
# ─────────────────────────────────────
def debug_sales_count(df_feat, y, n_seeds=10):
    logger.info("\n=== D. artist_sales_count_log 디버깅 ===")

    # LAO 기준으로 unseen artist 비율 + fillna(0) 비중 추적
    unseen_pct = []
    fillna_zero_pct = []
    feature_stats_per_seed = []

    for seed in range(n_seeds):
        train_mask, test_mask = lao_split(df_feat, seed)
        df_train = df_feat[train_mask]
        df_eval = df_feat[test_mask]
        train_artists = set(df_train["artist_slug"].unique())
        test_artists = set(df_eval["artist_slug"].unique())
        unseen = test_artists - train_artists
        unseen_pct.append(len(unseen) / max(len(test_artists), 1) * 100)

        counts = df_train.groupby("artist_slug").size()
        eval_counts = df_eval["artist_slug"].map(counts).fillna(0)
        fillna_zero_pct.append((eval_counts == 0).mean() * 100)

        # train 의 sales_count_log 분포
        train_counts = df_train.groupby("artist_slug").size()
        train_log = np.log1p(df_train["artist_slug"].map(train_counts).values)
        eval_log = np.log1p(eval_counts.values)
        feature_stats_per_seed.append({
            "train_mean": float(train_log.mean()),
            "train_std": float(train_log.std()),
            "eval_mean": float(eval_log.mean()),
            "eval_std": float(eval_log.std()),
            "eval_zero_pct": float((eval_log == 0).mean() * 100),
        })

    logger.info(
        f"  LAO 평균 unseen artist 비율: {np.mean(unseen_pct):.1f}% "
        f"(test 작가의 {np.mean(unseen_pct):.0f}% 가 train 에 없음)"
    )
    logger.info(f"  Eval 의 fillna(0) 비중 평균: {np.mean(fillna_zero_pct):.1f}%")

    avg_train_mean = np.mean([s["train_mean"] for s in feature_stats_per_seed])
    avg_eval_mean = np.mean([s["eval_mean"] for s in feature_stats_per_seed])
    avg_eval_zero = np.mean([s["eval_zero_pct"] for s in feature_stats_per_seed])
    logger.info(
        f"  Train artist_sales_count_log 평균: {avg_train_mean:.2f} / "
        f"Eval 평균: {avg_eval_mean:.2f} (zero 비중 {avg_eval_zero:.1f}%)"
    )
    logger.info(
        f"  → Train 분포 vs Eval 분포 차이: {avg_train_mean - avg_eval_mean:+.2f} "
        f"(eval 이 0 으로 채워져 분포 어긋남)"
    )

    # 단독 효과: artist_sales_count_log 만 추가 시 회귀계수
    coef_seed = []
    for seed in range(n_seeds):
        train_mask, test_mask = lao_split(df_feat, seed)
        df_train = df_feat[train_mask]
        Xb_full = build_X_baseline(df_feat)
        counts_tr = df_train.groupby("artist_slug").size()
        Xb_full["artist_sales_count_log"] = np.log1p(
            df_feat["artist_slug"].map(counts_tr).fillna(0).values
        )
        Xtr = Xb_full[train_mask].values.astype(float)
        Xte = Xb_full[test_mask].values.astype(float)
        ytr = y[train_mask].values.astype(float)
        yte = y[test_mask].values.astype(float)
        try:
            pred, coef, intercept = fit_huber(Xtr, ytr, Xte, eps=1.35)
            coef_seed.append({"seed": seed, "sales_count_coef": float(coef[-1]),
                            "mdape": mdape(yte, pred)})
        except Exception:
            continue

    avg_coef = np.mean([c["sales_count_coef"] for c in coef_seed])
    logger.info(f"\n  artist_sales_count_log 회귀계수 평균 (10 seed): {avg_coef:+.4f}")
    logger.info(f"  → 양수면 sales_count 클수록 가격 ↑ 예측 / 음수면 반대")

    return {
        "lao_unseen_artist_pct_mean": float(np.mean(unseen_pct)),
        "eval_fillna_zero_pct_mean": float(np.mean(fillna_zero_pct)),
        "train_eval_distribution_gap": float(avg_train_mean - avg_eval_mean),
        "coef_mean_10seed": float(avg_coef),
        "interpretation": (
            "LAO 평가에서 test 작가는 정의상 train 에 없음 → fillna(0) 비중 100% → "
            "feature 가 상수화 (모두 0) 또는 분포가 train 과 완전히 어긋남. "
            "train 에서 학습된 큰 양의 계수가 eval 에서 0 ≈ -∞ 효과로 모델 예측을 왜곡."
        ),
    }


# ─────────────────────────────────────
# E. Huber alpha sensitivity
# ─────────────────────────────────────
def huber_alpha_sweep(df_feat, y, n_seeds=N_SEEDS):
    logger.info("\n=== E. Huber alpha sensitivity (100-seed LAO) ===")

    alphas = [1e-4, 1e-2, 1.0, 10.0]
    results = {}
    for alpha in alphas:
        mdapes = []
        for seed in range(n_seeds):
            train_mask, test_mask = lao_split(df_feat, seed)
            Xb = build_X_baseline(df_feat)
            Xtr = Xb[train_mask].values.astype(float)
            Xte = Xb[test_mask].values.astype(float)
            ytr = y[train_mask].values.astype(float)
            yte = y[test_mask].values.astype(float)
            try:
                pred, _, _ = fit_huber(Xtr, ytr, Xte, eps=1.35, alpha=alpha)
                mdapes.append(mdape(yte, pred))
            except Exception:
                continue
        arr = np.array(mdapes)
        results[f"alpha_{alpha}"] = {
            "mean": float(arr.mean()),
            "std": float(arr.std()),
            "n": int(len(arr)),
        }
        logger.info(
            f"  alpha = {alpha:>8.4g}: MdAPE {arr.mean():.2f}% (std {arr.std():.2f}, n={len(arr)})"
        )

    best = min(results.items(), key=lambda kv: kv[1]["mean"])
    logger.info(f"\n  Best alpha: {best[0]} (MdAPE {best[1]['mean']:.2f}%)")
    return results


def run():
    df = pd.read_parquet(DATA)
    df_feat = make_features(df)
    y = df_feat["log_price"]

    logger.info("=" * 80)
    logger.info("Stage 3 Addendum 후속 — D (디버깅) + E (Huber alpha)")
    logger.info("=" * 80)

    summary = {}
    summary["D_sales_count_debug"] = debug_sales_count(df_feat, y, n_seeds=10)
    summary["E_huber_alpha_sweep"] = huber_alpha_sweep(df_feat, y, n_seeds=N_SEEDS)

    out = RESULTS / "stage3_addendum_debug.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(f"\nSaved: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    run()
