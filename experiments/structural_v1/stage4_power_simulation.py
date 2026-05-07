"""Stage 4 Power Simulation (코덱스 권고).

목적: Stage 4 합격 기준 (cluster bootstrap CI 상한 ≤ 0) 이 25 clusters 에서
    0.8 power 를 실제로 주는지 검증. 부족 시 목표 상향 (30-35 권고).

방법:
1. Stage 3 cutoff 2023 LAO 에서 baseline (Huber) vs FE only 모델 fit
2. test 의 13 warm artists 별 per-artist MdAPE 차이 측정 → observed effect distribution
3. Simulation:
   - n_clusters ∈ [15, 20, 25, 30, 35, 40]
   - 각 trial: observed distribution 에서 n_clusters 샘플 → cluster bootstrap CI → reject 여부
   - power = P(CI 상한 ≤ 0)
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
N_SIM = 1000
N_BOOT = 500


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


# ─────────────────────────────────────
# Step 1-2: per-artist observed effect (Stage 3 cutoff 2023)
# ─────────────────────────────────────
def measure_per_artist_effect(df_feat, y, cutoff=2023):
    train_mask = df_feat["year_made"] <= cutoff
    test_mask = ~train_mask
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

    # Per-artist effect = MdAPE(FE) - MdAPE(baseline) (음수 = 개선)
    per_artist_effect = []
    for a in set(test_artists):
        m = test_artists == a
        if m.sum() < 2:
            continue
        eff = mdape(yte[m], pred_fe[m]) - mdape(yte[m], pred_b[m])
        per_artist_effect.append(eff)
    return np.array(per_artist_effect)


# ─────────────────────────────────────
# Step 3: Power simulation
# ─────────────────────────────────────
def simulate_power(observed_effects, n_clusters, n_sim=N_SIM, n_boot=N_BOOT, seed=42):
    """Bootstrap-based power for cluster bootstrap CI 상한 ≤ 0."""
    rng = np.random.default_rng(seed)
    rejects = 0
    for _ in range(n_sim):
        # Sample n_clusters artists' effects from observed distribution
        sample = rng.choice(observed_effects, size=n_clusters, replace=True)
        # Cluster bootstrap on this sample
        boot_means = np.empty(n_boot)
        for b in range(n_boot):
            idx = rng.integers(0, n_clusters, size=n_clusters)
            boot_means[b] = sample[idx].mean()
        ci_upper = float(np.percentile(boot_means, 97.5))
        if ci_upper <= 0:
            rejects += 1
    return rejects / n_sim


def run():
    df = pd.read_parquet(DATA)
    df_feat = make_features(df)
    y = df_feat["log_price"]

    logger.info("=" * 80)
    logger.info("Stage 4 Power Simulation (코덱스 권고)")
    logger.info("=" * 80)

    logger.info("\n--- Step 1-2: Stage 3 cutoff 2023 LAO 에서 per-artist effect 측정 ---")
    effects = measure_per_artist_effect(df_feat, y, cutoff=2023)
    logger.info(f"  관측 작가 수 (n≥2 작품): {len(effects)}")
    logger.info(f"  per-artist effect: mean {effects.mean():+.2f}%p, "
                f"median {np.median(effects):+.2f}%p, std {effects.std():.2f}%p")
    logger.info(f"  분포: min {effects.min():+.2f}, max {effects.max():+.2f}, "
                f"P25 {np.percentile(effects, 25):+.2f}, P75 {np.percentile(effects, 75):+.2f}")

    logger.info("\n--- Step 3: Power simulation (cluster bootstrap CI 상한 ≤ 0) ---")
    logger.info(f"  n_sim = {N_SIM}, n_boot = {N_BOOT}")
    logger.info(f"  observed effect 분포 (Stage 3 cutoff 2023, n≥2 작품 작가만 = 10명) 에서 resample\n")

    cluster_sizes = [15, 20, 25, 30, 35, 40, 50]
    powers = {}
    logger.info(f"  {'n_clusters':>11} {'power':>7}  {'verdict':>15}")
    for n in cluster_sizes:
        p = simulate_power(effects, n_clusters=n)
        powers[n] = p
        verdict = "✓ ≥ 0.8" if p >= 0.8 else ("△ 0.6-0.8" if p >= 0.6 else "✗ < 0.6")
        logger.info(f"  {n:>11d} {p:>6.1%}  {verdict:>15}")

    # 의사결정
    n_for_80 = next((n for n in cluster_sizes if powers[n] >= 0.8), None)
    logger.info("\n--- 결론 ---")
    if n_for_80 is None:
        logger.info(f"  ⚠️  현 effect 분포에서 50 clusters 까지도 0.8 power 미달")
        logger.info(f"  → Stage 4 합격 기준 (CI 상한 ≤ 0) 이 매우 빡빡 — 기준 재정의 또는 표본 대폭 확장 필요")
        verdict_text = "FAIL — 기준 재정의 필요"
    elif n_for_80 <= 25:
        logger.info(f"  ✓ {n_for_80} clusters 에서 0.8 power 도달 — Stage 4 plan 25 clusters 목표 적절")
        verdict_text = f"PASS @ {n_for_80} clusters"
    else:
        logger.info(f"  △ {n_for_80} clusters 에서 0.8 power 도달 — Stage 4 plan 목표 25→{n_for_80}+ 상향 권고")
        verdict_text = f"BORDERLINE — 목표 25→{n_for_80}+ 상향 권고"

    summary = {
        "n_sim": N_SIM,
        "n_boot": N_BOOT,
        "observed_effects": {
            "n_artists": int(len(effects)),
            "mean_pct_pt": float(effects.mean()),
            "median_pct_pt": float(np.median(effects)),
            "std_pct_pt": float(effects.std()),
            "values": [float(e) for e in effects],
        },
        "power_by_n_clusters": {str(n): float(p) for n, p in powers.items()},
        "n_clusters_for_80_power": n_for_80,
        "verdict": verdict_text,
    }

    out = RESULTS / "stage4_power_simulation.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(f"\nSaved: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    run()
