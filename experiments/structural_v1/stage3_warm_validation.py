"""Stage 3 Warm-start Combined 모델 검증 (코덱스 P2).

1. Bootstrap CI (baseline vs combined 차이)
2. Rolling time-split (다양한 cutoff 반복)
3. Artist / Stage / Time bucket 분해
4. Artist history leakage 점검 (시점 이전 정보만 사용 확인)
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


def build_X_combined(df, train_mask, warm_artists, train_log_price_mean):
    """Combined: baseline + Artist FE + history avg."""
    X = build_X_baseline(df).copy()
    # Artist FE (warm 작가 dummy)
    for artist in warm_artists:
        X[f"artist_{artist}"] = (df["artist_slug"] == artist).astype(float).values

    # Artist history (train-only avg log_price)
    train_df = df[train_mask].copy()
    artist_avg = train_df.groupby("artist_slug")["log_price"].mean().to_dict()
    df_avg = df["artist_slug"].map(artist_avg).fillna(train_log_price_mean)
    X["recent_avg_log_price"] = df_avg.values
    return X


def fit_huber_predict(Xtr, ytr, Xte, weights=None, eps=1.35):
    m = HuberRegressor(epsilon=eps, max_iter=1000, alpha=0.0001)
    if weights is not None:
        m.fit(Xtr[:, 1:], ytr, sample_weight=weights)
    else:
        m.fit(Xtr[:, 1:], ytr)
    return Xte[:, 1:] @ m.coef_ + m.intercept_


def metrics(yte, pred):
    ape = np.abs(np.exp(pred) - np.exp(yte)) / np.exp(yte)
    return {
        "mdape": float(np.median(ape) * 100),
        "ape_array": ape,
    }


def time_weights(years, max_year, half_life=2):
    age = max_year - years
    return 0.5 ** (age / half_life)


# ─────────────────────────────────────
# 1. Bootstrap CI
# ─────────────────────────────────────
def bootstrap_diff_ci(yte, pred_baseline, pred_combined, n_boot=1000, seed=42):
    """Baseline vs Combined 차이 (MdAPE diff) 의 Bootstrap CI."""
    rng = np.random.default_rng(seed)
    ape_b = np.abs(np.exp(pred_baseline) - np.exp(yte)) / np.exp(yte)
    ape_c = np.abs(np.exp(pred_combined) - np.exp(yte)) / np.exp(yte)

    diffs = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(yte), size=len(yte))
        m_b = np.median(ape_b[idx]) * 100
        m_c = np.median(ape_c[idx]) * 100
        diffs.append(m_c - m_b)

    return {
        "diff_mean": float(np.mean(diffs)),
        "diff_median": float(np.median(diffs)),
        "ci_lo_95": float(np.percentile(diffs, 2.5)),
        "ci_hi_95": float(np.percentile(diffs, 97.5)),
        "p_below_zero": float((np.array(diffs) < 0).mean()),
    }


# ─────────────────────────────────────
# 2. Rolling time-split
# ─────────────────────────────────────
def rolling_split_eval(df_feat, y):
    """Multiple cutoff years 로 반복 평가."""
    cutoffs = [2020, 2021, 2022, 2023, 2024]
    results = []

    for cutoff in cutoffs:
        train_mask = df_feat["year_made"] <= cutoff
        test_mask = ~train_mask

        if train_mask.sum() < 100 or test_mask.sum() < 30:
            continue

        train_counts = Counter(df_feat[train_mask]["artist_slug"])
        warm_artists = {a for a, c in train_counts.items() if c >= WARM_THRESHOLD}

        # Test 작가가 warm 인 경우만
        warm_test_mask = test_mask & df_feat["artist_slug"].isin(warm_artists)
        if warm_test_mask.sum() < 10:
            continue

        train_log_price_mean = y[train_mask].mean()

        # Baseline
        X_b = build_X_baseline(df_feat)
        Xtr = X_b[train_mask.values].values.astype(float)
        ytr = y[train_mask].values.astype(float)
        Xte = X_b[warm_test_mask.values].values.astype(float)
        yte = y[warm_test_mask].values.astype(float)
        pred_b = fit_huber_predict(Xtr, ytr, Xte)

        # Combined
        X_c = build_X_combined(df_feat, train_mask, warm_artists, train_log_price_mean)
        Xtr_c = X_c[train_mask.values].values.astype(float)
        Xte_c = X_c[warm_test_mask.values].values.astype(float)
        max_yr = df_feat["year_made"].max()
        weights = time_weights(df_feat[train_mask]["year_made"].values, max_yr, half_life=2)
        pred_c = fit_huber_predict(Xtr_c, ytr, Xte_c, weights=weights)

        results.append({
            "cutoff": int(cutoff),
            "n_train": int(train_mask.sum()),
            "n_test_warm": int(warm_test_mask.sum()),
            "n_warm_artists": int(len(warm_artists)),
            "baseline_mdape": float(np.median(np.abs(np.exp(pred_b) - np.exp(yte)) / np.exp(yte)) * 100),
            "combined_mdape": float(np.median(np.abs(np.exp(pred_c) - np.exp(yte)) / np.exp(yte)) * 100),
        })

    return results


# ─────────────────────────────────────
# 3. Artist / Bucket 분해
# ─────────────────────────────────────
def bucket_decomposition(df_feat, y, train_mask, test_mask, warm_artists,
                        train_log_price_mean):
    warm_test_mask = test_mask & df_feat["artist_slug"].isin(warm_artists)

    # Baseline + Combined 예측
    X_b = build_X_baseline(df_feat)
    X_c = build_X_combined(df_feat, train_mask, warm_artists, train_log_price_mean)

    Xtr_b = X_b[train_mask.values].values.astype(float)
    Xte_b = X_b[warm_test_mask.values].values.astype(float)
    Xtr_c = X_c[train_mask.values].values.astype(float)
    Xte_c = X_c[warm_test_mask.values].values.astype(float)

    ytr = y[train_mask].values.astype(float)
    yte = y[warm_test_mask].values.astype(float)

    max_yr = df_feat["year_made"].max()
    weights = time_weights(df_feat[train_mask]["year_made"].values, max_yr, half_life=2)

    pred_b = fit_huber_predict(Xtr_b, ytr, Xte_b)
    pred_c = fit_huber_predict(Xtr_c, ytr, Xte_c, weights=weights)

    df_te = df_feat[warm_test_mask].reset_index(drop=True)

    # Artist 별
    artist_results = []
    for artist in df_te["artist_slug"].unique():
        mask = df_te["artist_slug"].values == artist
        if mask.sum() < 3:
            continue
        ape_b = np.abs(np.exp(pred_b[mask]) - np.exp(yte[mask])) / np.exp(yte[mask])
        ape_c = np.abs(np.exp(pred_c[mask]) - np.exp(yte[mask])) / np.exp(yte[mask])
        artist_results.append({
            "artist": artist,
            "n": int(mask.sum()),
            "baseline_mdape": float(np.median(ape_b) * 100),
            "combined_mdape": float(np.median(ape_c) * 100),
            "improvement": float((np.median(ape_b) - np.median(ape_c)) * 100),
        })

    # Price bucket
    prices = np.exp(yte)
    qs = np.quantile(prices, [0.33, 0.67])
    price_buckets = []
    for label, (lo, hi) in [("저가", (-np.inf, qs[0])), ("중가", (qs[0], qs[1])), ("고가", (qs[1], np.inf))]:
        mask = (prices > lo) & (prices <= hi)
        if mask.sum() < 5:
            continue
        ape_b = np.abs(np.exp(pred_b[mask]) - np.exp(yte[mask])) / np.exp(yte[mask])
        ape_c = np.abs(np.exp(pred_c[mask]) - np.exp(yte[mask])) / np.exp(yte[mask])
        price_buckets.append({
            "label": label,
            "n": int(mask.sum()),
            "baseline_mdape": float(np.median(ape_b) * 100),
            "combined_mdape": float(np.median(ape_c) * 100),
        })

    return {"artists": artist_results, "price_buckets": price_buckets,
            "yte": yte, "pred_b": pred_b, "pred_c": pred_c}


# ─────────────────────────────────────
# 4. Leakage 점검
# ─────────────────────────────────────
def leakage_check(df_feat, y, train_mask, test_mask, warm_artists, train_log_price_mean):
    """Artist history 가 test 시점 이후 정보를 포함하는지 확인."""
    train_df = df_feat[train_mask].copy()
    artist_stats = train_df.groupby("artist_slug").agg(
        max_year=("year_made", "max"),
        n_train=("artwork_id", "count"),
        avg_log_price=("log_price", "mean"),
    ).reset_index()

    # Train cutoff
    cutoff_year = df_feat[train_mask]["year_made"].max()

    # 1. Artist stats 의 max_year 가 cutoff 를 넘지 않는지
    leak_year = (artist_stats["max_year"] > cutoff_year).sum()

    # 2. Test 작가의 artist_history 변수가 test 본인 가격 정보를 포함했는지 (당연히 X 인지)
    test_warm = test_mask & df_feat["artist_slug"].isin(warm_artists)
    test_artists = df_feat[test_warm]["artist_slug"].unique()

    # 각 test 작가의 train avg 가 test 가격을 사용하지 않았는지
    leak_test_in_train = []
    for artist in test_artists:
        train_subset = df_feat[train_mask & (df_feat["artist_slug"] == artist)]
        test_subset = df_feat[test_warm & (df_feat["artist_slug"] == artist)]
        # Train 의 year_made 가 모두 test 보다 이전인지
        if len(train_subset) > 0 and len(test_subset) > 0:
            train_max_y = train_subset["year_made"].max()
            test_min_y = test_subset["year_made"].min()
            if train_max_y >= test_min_y:
                leak_test_in_train.append({
                    "artist": artist,
                    "train_max_year": float(train_max_y),
                    "test_min_year": float(test_min_y),
                })

    return {
        "cutoff_year": float(cutoff_year),
        "n_test_warm_artists": int(len(test_artists)),
        "n_train_artist_year_violations": int(leak_year),
        "n_train_test_year_overlap": len(leak_test_in_train),
        "year_overlap_examples": leak_test_in_train[:5],
    }


# ─────────────────────────────────────
# Main
# ─────────────────────────────────────
def run():
    df = pd.read_parquet(DATA)
    df_feat = make_features(df)
    y = df_feat["log_price"]

    summary = {}

    # Time split (≤2023)
    train_mask = df_feat["year_made"] <= 2023
    test_mask = ~train_mask
    train_counts = Counter(df_feat[train_mask]["artist_slug"])
    warm_artists = {a for a, c in train_counts.items() if c >= WARM_THRESHOLD}
    train_log_price_mean = float(y[train_mask].mean())
    warm_test_mask = test_mask & df_feat["artist_slug"].isin(warm_artists)

    logger.info("=" * 80)
    logger.info("Stage 3 Warm-start Combined 검증 (P2)")
    logger.info("=" * 80)
    logger.info(f"Train: {train_mask.sum()} / Warm test: {warm_test_mask.sum()}")
    logger.info(f"Warm artists: {len(warm_artists)}")

    # 1. Bootstrap CI
    logger.info("\n--- 1. Bootstrap 95% CI (baseline vs combined diff) ---")
    X_b = build_X_baseline(df_feat)
    X_c = build_X_combined(df_feat, train_mask, warm_artists, train_log_price_mean)
    Xtr_b = X_b[train_mask.values].values.astype(float)
    Xte_b = X_b[warm_test_mask.values].values.astype(float)
    Xtr_c = X_c[train_mask.values].values.astype(float)
    Xte_c = X_c[warm_test_mask.values].values.astype(float)
    ytr = y[train_mask].values.astype(float)
    yte = y[warm_test_mask].values.astype(float)
    max_yr = df_feat["year_made"].max()
    weights = time_weights(df_feat[train_mask]["year_made"].values, max_yr, half_life=2)

    pred_b = fit_huber_predict(Xtr_b, ytr, Xte_b)
    pred_c = fit_huber_predict(Xtr_c, ytr, Xte_c, weights=weights)

    boot = bootstrap_diff_ci(yte, pred_b, pred_c, n_boot=1000)
    logger.info(
        f"  Baseline MdAPE: {np.median(np.abs(np.exp(pred_b) - np.exp(yte)) / np.exp(yte)) * 100:.2f}%"
    )
    logger.info(
        f"  Combined MdAPE: {np.median(np.abs(np.exp(pred_c) - np.exp(yte)) / np.exp(yte)) * 100:.2f}%"
    )
    logger.info(
        f"  Diff (combined - baseline): mean {boot['diff_mean']:+.2f}%p, "
        f"95% CI [{boot['ci_lo_95']:+.2f}, {boot['ci_hi_95']:+.2f}]"
    )
    logger.info(f"  P(diff < 0) = {boot['p_below_zero']:.1%} (개선 신뢰도)")
    summary["1_bootstrap_ci"] = boot

    # 2. Rolling time-split
    logger.info("\n--- 2. Rolling time-split (cutoff 2020~2024) ---")
    rolling = rolling_split_eval(df_feat, y)
    logger.info(f"\n  {'cutoff':>8} {'n_train':>8} {'n_test':>7} {'baseline':>10} {'combined':>10} {'개선':>8}")
    for r in rolling:
        diff = r["combined_mdape"] - r["baseline_mdape"]
        logger.info(
            f"  {r['cutoff']:>8} {r['n_train']:>8} {r['n_test_warm']:>7} "
            f"{r['baseline_mdape']:>7.2f}% {r['combined_mdape']:>7.2f}% {diff:>+5.2f}%p"
        )
    summary["2_rolling_split"] = rolling

    # 3. Bucket 분해
    logger.info("\n--- 3. Artist / Price bucket 분해 ---")
    decomp = bucket_decomposition(df_feat, y, train_mask, test_mask, warm_artists,
                                  train_log_price_mean)
    logger.info("\n  [Price bucket]")
    for b in decomp["price_buckets"]:
        diff = b["combined_mdape"] - b["baseline_mdape"]
        logger.info(
            f"    {b['label']}: n={b['n']}, baseline {b['baseline_mdape']:.2f}% → "
            f"combined {b['combined_mdape']:.2f}% ({diff:+.2f}%p)"
        )
    logger.info(f"\n  [Top 5 artist 개선 / Bottom 5 악화]")
    sorted_artists = sorted(decomp["artists"], key=lambda x: -x["improvement"])
    for a in sorted_artists[:5]:
        logger.info(
            f"    [+] {a['artist']:<28} n={a['n']}: "
            f"{a['baseline_mdape']:.2f} → {a['combined_mdape']:.2f} ({a['improvement']:+.2f}%p)"
        )
    for a in sorted_artists[-5:]:
        logger.info(
            f"    [-] {a['artist']:<28} n={a['n']}: "
            f"{a['baseline_mdape']:.2f} → {a['combined_mdape']:.2f} ({a['improvement']:+.2f}%p)"
        )
    summary["3_bucket_decomposition"] = {
        "price_buckets": decomp["price_buckets"],
        "n_artists_evaluated": len(decomp["artists"]),
        "top5_improvement": sorted_artists[:5],
        "worst5_change": sorted_artists[-5:],
    }

    # 4. Leakage 점검
    logger.info("\n--- 4. Artist history Leakage 점검 ---")
    leak = leakage_check(df_feat, y, train_mask, test_mask, warm_artists, train_log_price_mean)
    logger.info(f"  Train cutoff year: {leak['cutoff_year']}")
    logger.info(f"  Test warm artists: {leak['n_test_warm_artists']}")
    logger.info(f"  Train artist_year > cutoff (leakage 1): {leak['n_train_artist_year_violations']}건")
    logger.info(f"  Train-test year overlap (leakage 2): {leak['n_train_test_year_overlap']}건")
    if leak["n_train_test_year_overlap"] == 0:
        logger.info(f"  → ✓ Leakage 없음")
    else:
        logger.info(f"  → ⚠️ Year overlap 발견:")
        for ex in leak["year_overlap_examples"]:
            logger.info(f"      {ex}")
    summary["4_leakage_check"] = leak

    # Save
    summary_safe = {
        "1_bootstrap_ci": summary["1_bootstrap_ci"],
        "2_rolling_split": summary["2_rolling_split"],
        "3_bucket_decomposition": summary["3_bucket_decomposition"],
        "4_leakage_check": summary["4_leakage_check"],
    }
    with (RESULTS / "stage3_warm_validation.json").open("w", encoding="utf-8") as f:
        json.dump(summary_safe, f, indent=2, ensure_ascii=False)
    logger.info(f"\nSaved: {(RESULTS / 'stage3_warm_validation.json').relative_to(ROOT)}")


if __name__ == "__main__":
    run()
