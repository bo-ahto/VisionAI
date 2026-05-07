"""Stage 3 Warm-start 정확도 개선 실험 (코덱스 P1).

1. Artist Fixed Effects (n_train ≥ 10 작가만)
2. 시간 가중 (최근 작품 더 무겁게)
3. Artist-history 요약 변수 (최근 평균가격 / 평균 면적당 가격)

baseline: F4 + spline + Huber, time-split ≤2023 warm = 21.74%
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
DATA = ROOT / "data" / "curated" / "stage3_1000x100.parquet"
RESULTS = Path(__file__).parent / "results"

WARM_THRESHOLD = 10


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


def metrics(yte, pred):
    ape = np.abs(np.exp(pred) - np.exp(yte)) / np.exp(yte)
    return {
        "mdape": float(np.median(ape) * 100),
        "w30": float((ape <= 0.30).mean() * 100),
        "w50": float((ape <= 0.50).mean() * 100),
    }


def fit_huber_predict(Xtr, ytr, Xte, weights=None, eps=1.35):
    m = HuberRegressor(epsilon=eps, max_iter=1000, alpha=0.0001)
    if weights is not None:
        m.fit(Xtr[:, 1:], ytr, sample_weight=weights)
    else:
        m.fit(Xtr[:, 1:], ytr)
    return Xte[:, 1:] @ m.coef_ + m.intercept_


def fit_ols_predict(Xtr, ytr, Xte):
    beta, *_ = np.linalg.lstsq(Xtr, ytr, rcond=None)
    return Xte @ beta


def build_X_baseline(df):
    """F4 + log_area spline (운영 채택 모델)."""
    knots = np.percentile(df["log_area"].values, [10, 50, 90])
    sp = restricted_cubic_spline(df["log_area"].values, knots)
    X = pd.DataFrame({
        "const": 1.0,
        "log_area": df["log_area"].values,
        "birth_year_centered": df["birth_year_centered"].values,
        "log_artist_total_works": df["log_artist_total_works"].values,
        "log_area_spline": sp[:, 0],
    })
    return X


def build_X_with_artist_fe(df, train_mask, warm_artists):
    """Baseline + Artist FE (warm artists 만)."""
    X = build_X_baseline(df).copy()
    # warm artist dummy (학습 시 알고 있는 작가만)
    for artist in warm_artists:
        col = f"artist_{artist}"
        X[col] = (df["artist_slug"] == artist).astype(float).values
    return X


def time_split(df, train_year=2023):
    """≤2023 train / >2023 test."""
    train_mask = df["year_made"] <= train_year
    test_mask = ~train_mask
    return train_mask, test_mask


def evaluate_warm_test(df_feat, X, y, train_mask, test_mask, warm_artists,
                       fit_func=fit_huber_predict, weights=None):
    """Warm-only test: test 작가가 train 에 있는 케이스만."""
    test_idx = test_mask.values
    warm_test_mask = test_idx & df_feat["artist_slug"].isin(warm_artists).values

    Xtr = X[train_mask.values].values.astype(float)
    ytr = y[train_mask].values.astype(float)
    Xte = X[warm_test_mask].values.astype(float)
    yte = y[warm_test_mask].values.astype(float)

    if weights is not None:
        wtr = weights[train_mask.values]
        pred = fit_func(Xtr, ytr, Xte, weights=wtr)
    elif fit_func == fit_huber_predict:
        pred = fit_func(Xtr, ytr, Xte)
    else:
        pred = fit_func(Xtr, ytr, Xte)

    return metrics(yte, pred), int(warm_test_mask.sum())


# ─────────────────────────────────────
# 실험들
# ─────────────────────────────────────

def exp_baseline(df_feat, y, train_mask, test_mask, warm_artists):
    X = build_X_baseline(df_feat)
    return evaluate_warm_test(df_feat, X, y, train_mask, test_mask, warm_artists)


def exp_artist_fe(df_feat, y, train_mask, test_mask, warm_artists):
    X = build_X_with_artist_fe(df_feat, train_mask, warm_artists)
    return evaluate_warm_test(df_feat, X, y, train_mask, test_mask, warm_artists)


def exp_time_weight(df_feat, y, train_mask, test_mask, warm_artists, half_life=2):
    """시간 가중 (최근 작품 더 무겁게, exponential decay)."""
    X = build_X_baseline(df_feat)
    current_year = df_feat["year_made"].max()
    age = current_year - df_feat["year_made"].values
    weights = 0.5 ** (age / half_life)  # half-life = 2년
    return evaluate_warm_test(df_feat, X, y, train_mask, test_mask, warm_artists, weights=weights)


def exp_artist_history(df_feat, y, train_mask, test_mask, warm_artists):
    """Artist history 요약 변수 추가."""
    X_base = build_X_baseline(df_feat)

    # Train 데이터로 작가별 통계 계산
    train_df = df_feat[train_mask].copy()
    artist_stats = train_df.groupby("artist_slug").agg(
        recent_avg_log_price=("log_price", "mean"),
        recent_avg_log_area=("log_area", "mean"),
        n_train_works=("artwork_id", "count"),
    ).reset_index()

    # 작가별 평균 가격을 면적으로 정규화 (단위 가격)
    artist_stats["avg_price_per_log_area"] = (
        artist_stats["recent_avg_log_price"] / artist_stats["recent_avg_log_area"].clip(lower=1)
    )

    # df_feat 에 merge
    df_with_hist = df_feat.merge(artist_stats, on="artist_slug", how="left")

    # Cold artist 는 결측 → global mean 으로 대체
    global_avg_log_price = train_df["log_price"].mean()
    df_with_hist["recent_avg_log_price"] = df_with_hist["recent_avg_log_price"].fillna(
        global_avg_log_price
    )
    df_with_hist["avg_price_per_log_area"] = df_with_hist["avg_price_per_log_area"].fillna(
        df_with_hist["avg_price_per_log_area"].mean()
    )

    X = X_base.copy()
    X["recent_avg_log_price"] = df_with_hist["recent_avg_log_price"].values
    X["avg_price_per_log_area"] = df_with_hist["avg_price_per_log_area"].values

    return evaluate_warm_test(df_feat, X, y, train_mask, test_mask, warm_artists)


def exp_combined(df_feat, y, train_mask, test_mask, warm_artists):
    """시간 가중 + artist FE + history 변수 모두 결합."""
    # Artist history 추가
    train_df = df_feat[train_mask].copy()
    artist_stats = train_df.groupby("artist_slug").agg(
        recent_avg_log_price=("log_price", "mean"),
    ).reset_index()
    df_with_hist = df_feat.merge(artist_stats, on="artist_slug", how="left")
    df_with_hist["recent_avg_log_price"] = df_with_hist["recent_avg_log_price"].fillna(
        train_df["log_price"].mean()
    )

    X = build_X_with_artist_fe(df_feat, train_mask, warm_artists).copy()
    X["recent_avg_log_price"] = df_with_hist["recent_avg_log_price"].values

    # 시간 가중
    current_year = df_feat["year_made"].max()
    age = current_year - df_feat["year_made"].values
    weights = 0.5 ** (age / 2)

    return evaluate_warm_test(df_feat, X, y, train_mask, test_mask, warm_artists, weights=weights)


def run():
    global WARM_THRESHOLD
    df = pd.read_parquet(DATA)
    df_feat = make_features(df)
    y = df_feat["log_price"]

    summary = {}

    # Time split
    train_mask, test_mask = time_split(df_feat, 2023)
    train_artists = set(df_feat[train_mask]["artist_slug"])
    train_counts = Counter(df_feat[train_mask]["artist_slug"])
    warm_artists = {a for a, c in train_counts.items() if c >= WARM_THRESHOLD}

    logger.info("=" * 80)
    logger.info(f"Stage 3 Warm-start 개선 실험 (time-split ≤2023, warm threshold ≥{WARM_THRESHOLD})")
    logger.info("=" * 80)
    logger.info(f"Train: {train_mask.sum()} / Test: {test_mask.sum()}")
    logger.info(f"Train 작가: {len(train_artists)}, warm 작가 (≥{WARM_THRESHOLD}): {len(warm_artists)}")

    # Test 작가 중 warm 인 케이스
    test_warm = test_mask & df_feat["artist_slug"].isin(warm_artists)
    logger.info(f"Test (warm only): {test_warm.sum()}")

    if test_warm.sum() < 30:
        logger.warning("Warm test 표본 부족 — n_train_threshold 낮춰서 재시도")
        WARM_THRESHOLD = 3
        warm_artists = {a for a, c in train_counts.items() if c >= WARM_THRESHOLD}
        test_warm = test_mask & df_feat["artist_slug"].isin(warm_artists)
        logger.info(f"Threshold 3 으로: warm 작가 {len(warm_artists)}, test {test_warm.sum()}")

    # 1. Baseline
    logger.info("\n--- 1. Baseline (F4 + spline + Huber, warm test only) ---")
    res, n = exp_baseline(df_feat, y, train_mask, test_mask, warm_artists)
    logger.info(f"  n={n}: MdAPE {res['mdape']:.2f}% / W30 {res['w30']:.1f} / W50 {res['w50']:.1f}")
    summary["baseline_warm"] = {**res, "n": n}

    # 2. Artist FE
    logger.info("\n--- 2. + Artist Fixed Effects (warm artist dummy) ---")
    res, n = exp_artist_fe(df_feat, y, train_mask, test_mask, warm_artists)
    logger.info(f"  n={n}: MdAPE {res['mdape']:.2f}% / W30 {res['w30']:.1f} / W50 {res['w50']:.1f}")
    summary["artist_fe"] = {**res, "n": n}

    # 3. Time weight (half-life 2년)
    logger.info("\n--- 3. + Time weighting (half-life 2년) ---")
    res, n = exp_time_weight(df_feat, y, train_mask, test_mask, warm_artists, half_life=2)
    logger.info(f"  n={n}: MdAPE {res['mdape']:.2f}% / W30 {res['w30']:.1f} / W50 {res['w50']:.1f}")
    summary["time_weight_2y"] = {**res, "n": n}

    # 3b. Time weight (half-life 4년)
    logger.info("\n--- 3b. + Time weighting (half-life 4년) ---")
    res, n = exp_time_weight(df_feat, y, train_mask, test_mask, warm_artists, half_life=4)
    logger.info(f"  n={n}: MdAPE {res['mdape']:.2f}% / W30 {res['w30']:.1f} / W50 {res['w50']:.1f}")
    summary["time_weight_4y"] = {**res, "n": n}

    # 4. Artist history 변수
    logger.info("\n--- 4. + Artist history 요약 변수 (recent_avg_log_price + per_area) ---")
    res, n = exp_artist_history(df_feat, y, train_mask, test_mask, warm_artists)
    logger.info(f"  n={n}: MdAPE {res['mdape']:.2f}% / W30 {res['w30']:.1f} / W50 {res['w50']:.1f}")
    summary["artist_history"] = {**res, "n": n}

    # 5. Combined (FE + 시간가중 + history)
    logger.info("\n--- 5. + Combined (FE + 시간가중 + history) ---")
    res, n = exp_combined(df_feat, y, train_mask, test_mask, warm_artists)
    logger.info(f"  n={n}: MdAPE {res['mdape']:.2f}% / W30 {res['w30']:.1f} / W50 {res['w50']:.1f}")
    summary["combined"] = {**res, "n": n}

    # Save
    with (RESULTS / "stage3_warm_improvements.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # Final
    logger.info("\n" + "=" * 80)
    logger.info("Warm-start 개선 비교 (vs baseline)")
    logger.info("=" * 80)
    base = summary["baseline_warm"]["mdape"]
    logger.info(f"{'Method':<28} {'n':>5} {'MdAPE':>10} {'개선':>10}")
    for name, m in summary.items():
        diff = m["mdape"] - base
        logger.info(
            f"{name:<28} {m['n']:>5} {m['mdape']:>7.2f}% {diff:>+5.2f}%p"
        )


if __name__ == "__main__":
    run()
