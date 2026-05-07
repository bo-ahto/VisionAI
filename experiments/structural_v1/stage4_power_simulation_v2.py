"""Stage 4 Power Simulation v2 — 실제 가용 풀 (40 clusters) 기반 재실행.

v1 (`stage4_power_simulation.py`) 은 Stage 3 cutoff 2023 의 10 artists effect 분포에서 resample.
v2 는 **Stage 4 전체 가용 풀** (Artsy cleansed train ≤2023 ≥10 작품 warm + test 2025 n≥3) 의
실제 per-artist effect 분포 사용 → 더 현실적 power.

해석 초점 (코덱스 권고): Power 자체보다 **effect stability**.
"""

from __future__ import annotations

import json
import logging
import re
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import HuberRegressor

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent.parent
DATA = ROOT / "data" / "artsy_kr_artworks.csv"
RESULTS = Path(__file__).parent / "results"
WARM_THRESHOLD = 10
N_SIM = 1000
N_BOOT = 500


def parse_year(date_str):
    if pd.isna(date_str):
        return None
    m = re.search(r"\b(19|20)\d{2}\b", str(date_str))
    return int(m.group()) if m else None


def make_features(df):
    out = df.copy()
    out["log_area"] = np.log((out["width_cm"] * out["height_cm"]).clip(lower=1))
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


def add_artist_fe(X, df, warm_artists):
    X = X.copy()
    for a in warm_artists:
        X[f"artist_{a}"] = (df["artist_slug"] == a).astype(float).values
    return X


def fit_huber(Xtr, ytr, Xte):
    m = HuberRegressor(epsilon=1.35, alpha=0.0001, max_iter=2000)
    m.fit(Xtr[:, 1:], ytr)
    return Xte[:, 1:] @ m.coef_ + m.intercept_


def mdape(y, pred):
    return float(np.median(np.abs(np.exp(pred) - np.exp(y)) / np.exp(y)) * 100)


def measure_per_artist_effect(df_feat, y):
    """Train ≤2023 / Test 2025 split 에서 per-artist effect 측정."""
    train_mask = df_feat["year_made"] <= 2023
    test_mask = df_feat["year_made"] == 2025
    train_counts = Counter(df_feat[train_mask]["artist_slug"])
    warm_artists = {a for a, n in train_counts.items() if n >= WARM_THRESHOLD}
    warm_test_mask = test_mask & df_feat["artist_slug"].isin(warm_artists)

    Xb = build_X_baseline(df_feat)
    X_fe = add_artist_fe(Xb, df_feat, warm_artists)

    Xtr_b = Xb[train_mask].values.astype(float)
    Xte_b = Xb[warm_test_mask].values.astype(float)
    Xtr_fe = X_fe[train_mask].values.astype(float)
    Xte_fe = X_fe[warm_test_mask].values.astype(float)
    ytr = y[train_mask].values.astype(float)
    yte = y[warm_test_mask].values.astype(float)

    pred_b = fit_huber(Xtr_b, ytr, Xte_b)
    pred_fe = fit_huber(Xtr_fe, ytr, Xte_fe)
    test_artists = df_feat[warm_test_mask]["artist_slug"].values

    per_artist_effect = []
    n_per_artist = []
    for a in set(test_artists):
        m = test_artists == a
        if m.sum() < 3:  # test n ≥ 3 (test-eligible)
            continue
        eff = mdape(yte[m], pred_fe[m]) - mdape(yte[m], pred_b[m])
        per_artist_effect.append(eff)
        n_per_artist.append(int(m.sum()))
    return np.array(per_artist_effect), np.array(n_per_artist)


def simulate_power(observed_effects, n_clusters, n_sim=N_SIM, n_boot=N_BOOT, seed=42):
    rng = np.random.default_rng(seed)
    rejects = 0
    for _ in range(n_sim):
        sample = rng.choice(observed_effects, size=n_clusters, replace=True)
        boot_means = np.empty(n_boot)
        for b in range(n_boot):
            idx = rng.integers(0, n_clusters, size=n_clusters)
            boot_means[b] = sample[idx].mean()
        ci_upper = float(np.percentile(boot_means, 97.5))
        if ci_upper <= 0:
            rejects += 1
    return rejects / n_sim


def run():
    df = pd.read_csv(DATA)
    df["year_made"] = df["date"].apply(parse_year)
    clean = df[
        df["price_krw"].notna() & (df["price_krw"] > 1) &
        df["width_cm"].notna() & df["height_cm"].notna() &
        (df["width_cm"] > 0) & (df["height_cm"] > 0) &
        df["artist_birth_year"].notna() &
        df["year_made"].notna() &
        (df["year_made"] >= 1900) & (df["year_made"] <= 2026)
    ].copy()

    df_feat = make_features(clean).reset_index(drop=True)
    y = df_feat["log_price"]

    logger.info("=" * 80)
    logger.info("Stage 4 Power Simulation v2 (실제 가용 풀 기반)")
    logger.info("=" * 80)
    logger.info(f"Source: Artsy cleansed {len(df_feat):,} 작품 / {df_feat['artist_slug'].nunique()} 작가")

    logger.info("\n--- Step 1-2: Train ≤2023 / Test 2025 per-artist effect 측정 (test n≥3) ---")
    effects, n_per = measure_per_artist_effect(df_feat, y)
    logger.info(f"  Test-eligible warm artists: {len(effects)} (목표 가용 풀 = 40)")
    logger.info(f"  per-artist effect: mean {effects.mean():+.2f}%p, median {np.median(effects):+.2f}%p, std {effects.std():.2f}%p")
    logger.info(f"  분포: min {effects.min():+.2f}, max {effects.max():+.2f}, P25 {np.percentile(effects, 25):+.2f}, P75 {np.percentile(effects, 75):+.2f}")
    logger.info(f"  per-artist test rows: mean {n_per.mean():.1f}, range [{n_per.min()}, {n_per.max()}]")

    logger.info("\n--- Step 3: Power simulation ---")
    cluster_sizes = [13, 25, 40, 50, 80, 100, 200]
    powers = {}
    logger.info(f"\n  {'n_clusters':>11} {'power':>7}  {'verdict':>20}")
    for n in cluster_sizes:
        if n > len(effects) and n != 200 and n != 100 and n != 80:
            # 가용 초과 (40) 시 resample with replacement 통해 simulate (실 데이터 없음)
            pass
        p = simulate_power(effects, n_clusters=n)
        powers[n] = p
        verdict = "✓ ≥ 0.8" if p >= 0.8 else ("△ 0.6-0.8" if p >= 0.6 else "✗ < 0.6")
        marker = " ← Stage 3 baseline" if n == 13 else (" ← Stage 4 가용 (40)" if n == 40 else "")
        logger.info(f"  {n:>11d} {p:>6.1%}  {verdict:>20}{marker}")

    n_for_80 = next((n for n in cluster_sizes if powers[n] >= 0.8), None)
    logger.info("\n--- 결론 (코덱스 권고: power 자체보다 effect stability) ---")
    actual_power = powers.get(40, None)
    if actual_power and actual_power >= 0.8:
        logger.info(f"  ✓ 실제 가용 40 clusters 에서 {actual_power:.1%} power 달성")
        verdict_text = f"PASS @ 40 clusters ({actual_power:.1%} power)"
    else:
        logger.info(f"  △ 40 clusters 에서 {actual_power:.1%} power — 0.8 미달 가능성")
        verdict_text = f"BORDERLINE @ 40 clusters ({actual_power:.1%} power)"

    logger.info(f"\n  ⚠️ 해석: power 보다 effect stability 우선 (코덱스 권고)")
    logger.info(f"     - Effect heterogeneity / outlier dilution / 2025 test sparsity / depth bin imbalance 가 진짜 위험")
    logger.info(f"     - Effect mean {effects.mean():+.2f}%p / median {np.median(effects):+.2f}%p / std {effects.std():.2f}%p")
    logger.info(f"     - std 가 mean 의 절대값 대비 큼 → CI 폭 좁히기 어려울 수 있음")

    summary = {
        "n_sim": N_SIM,
        "n_boot": N_BOOT,
        "source": "Artsy cleansed 8,891 / 823 artists, train ≤2023 / test 2025",
        "observed_effects": {
            "n_artists": int(len(effects)),
            "mean_pct_pt": float(effects.mean()),
            "median_pct_pt": float(np.median(effects)),
            "std_pct_pt": float(effects.std()),
            "min_pct_pt": float(effects.min()),
            "max_pct_pt": float(effects.max()),
            "p25_pct_pt": float(np.percentile(effects, 25)),
            "p75_pct_pt": float(np.percentile(effects, 75)),
            "n_per_artist": {"mean": float(n_per.mean()), "min": int(n_per.min()), "max": int(n_per.max())},
        },
        "power_by_n_clusters": {str(n): float(p) for n, p in powers.items()},
        "n_clusters_for_80_power": n_for_80,
        "actual_n_clusters_available": int(len(effects)),
        "actual_power": float(actual_power) if actual_power else None,
        "verdict": verdict_text,
        "interpretation_note": "Power 자체보다 effect stability 우선 — heterogeneity / outlier / sparsity / bin imbalance 가 진짜 위험",
    }

    out = RESULTS / "stage4_power_simulation_v2.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(f"\nSaved: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    run()
