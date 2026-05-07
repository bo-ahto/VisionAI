"""Stage 3 Warm-start Feature 재탐색 (코덱스 권고).

코덱스 권고:
- 1순위: Huber epsilon warm 전용 튜닝 (D)
- 2순위: FE only 유지 여부 재확인
- 3순위 (스크리닝): gallery_tier (A2), log_area × log_artist_total_works (B1)
- 보류: medium_category 확장, 다중 interaction, Core 5 조합 (Stage 4 까지)

평가 metric: MdAPE / artist-cluster bootstrap CI / artist win rate / top-k worst tail
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
    out["birth_year_centered"] = out["artist_birth_year"] - out["artist_birth_year"].mean()
    out["log_artist_total_works"] = np.log1p(out["artist_total_works"])
    out["log_price"] = np.log(out["price_krw"].clip(lower=1))
    out["interaction_area_works"] = out["log_area"] * out["log_artist_total_works"]
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


def add_gallery_tier(X, df):
    X = X.copy()
    # tier 2 base, tier 3 / 4 dummy
    for t in [3, 4]:
        X[f"tier_{t}"] = (df["gallery_tier"] == t).astype(float).values
    return X


def add_interaction_area_works(X, df):
    X = X.copy()
    X["log_area_x_log_works"] = df["interaction_area_works"].values
    return X


def fit_predict(Xtr, ytr, Xte, eps=1.35):
    m = HuberRegressor(epsilon=eps, max_iter=2000, alpha=0.0001)
    m.fit(Xtr[:, 1:], ytr)
    return Xte[:, 1:] @ m.coef_ + m.intercept_


def mdape(yte_log, pred_log):
    ape = np.abs(np.exp(pred_log) - np.exp(yte_log)) / np.exp(yte_log)
    return float(np.median(ape) * 100)


def p90_ape(yte_log, pred_log):
    ape = np.abs(np.exp(pred_log) - np.exp(yte_log)) / np.exp(yte_log)
    return float(np.percentile(ape, 90) * 100)


def artist_win_rate(yte_log, pred_a, pred_b, test_artists):
    """artist 단위로 a vs b 비교 — a 가 b 보다 작은 MdAPE 가진 artist 비율."""
    wins = 0
    total = 0
    for art in set(test_artists):
        mask = test_artists == art
        if mask.sum() < 2:
            continue
        a_med = np.median(np.abs(np.exp(pred_a[mask]) - np.exp(yte_log[mask])) / np.exp(yte_log[mask]))
        b_med = np.median(np.abs(np.exp(pred_b[mask]) - np.exp(yte_log[mask])) / np.exp(yte_log[mask]))
        if a_med < b_med:
            wins += 1
        total += 1
    return float(wins / total * 100) if total > 0 else None


def cluster_bootstrap_ci(yte_log, pred_a, pred_b, test_artists, n_boot=500, seed=42):
    """artist cluster bootstrap CI for (mdape_a - mdape_b)."""
    rng = np.random.default_rng(seed)
    unique = list(set(test_artists))
    diffs = []
    for _ in range(n_boot):
        sample = rng.choice(unique, size=len(unique), replace=True)
        mask = np.isin(test_artists, sample)
        if mask.sum() < 3:
            continue
        d = mdape(yte_log[mask], pred_a[mask]) - mdape(yte_log[mask], pred_b[mask])
        diffs.append(d)
    diffs = np.array(diffs)
    return {
        "mean": float(np.mean(diffs)),
        "ci_lo_95": float(np.percentile(diffs, 2.5)),
        "ci_hi_95": float(np.percentile(diffs, 97.5)),
        "p_below_zero": float((diffs < 0).mean()),
    }


# ─────────────────────────────────────
# Build feature variants
# ─────────────────────────────────────
def build_models(df, warm_artists):
    """모델 후보 dict: name → X DataFrame."""
    Xb = build_X_baseline(df)
    return {
        "baseline": Xb,
        "fe_only": add_artist_fe(Xb, df, warm_artists),
        "tier": add_gallery_tier(Xb, df),
        "interaction": add_interaction_area_works(Xb, df),
        "fe_tier": add_gallery_tier(add_artist_fe(Xb, df, warm_artists), df),
        "fe_interaction": add_interaction_area_works(add_artist_fe(Xb, df, warm_artists), df),
    }


# ─────────────────────────────────────
# Eval at given cutoff
# ─────────────────────────────────────
def eval_cutoff(df_feat, y, cutoff, eps=1.35):
    train_mask = df_feat["year_made"] <= cutoff
    test_mask = ~train_mask
    train_counts = Counter(df_feat[train_mask]["artist_slug"])
    warm_artists = {a for a, n in train_counts.items() if n >= WARM_THRESHOLD}
    warm_test_mask = test_mask & df_feat["artist_slug"].isin(warm_artists)
    if warm_test_mask.sum() < 8:
        return None

    models = build_models(df_feat, warm_artists)
    ytr = y[train_mask].values.astype(float)
    yte = y[warm_test_mask].values.astype(float)
    test_artists = df_feat[warm_test_mask]["artist_slug"].values

    preds = {}
    metrics = {}
    for name, X in models.items():
        Xtr = X[train_mask.values].values.astype(float)
        Xte = X[warm_test_mask.values].values.astype(float)
        pred = fit_predict(Xtr, ytr, Xte, eps=eps)
        preds[name] = pred
        metrics[name] = {
            "mdape": mdape(yte, pred),
            "p90_ape": p90_ape(yte, pred),
        }

    # vs baseline win rate + cluster bootstrap CI
    base_pred = preds["baseline"]
    for name, pred in preds.items():
        if name == "baseline":
            continue
        metrics[name]["win_rate_vs_baseline"] = artist_win_rate(yte, pred, base_pred, test_artists)
        metrics[name]["bootstrap_diff_vs_baseline"] = cluster_bootstrap_ci(
            yte, pred, base_pred, test_artists, n_boot=500
        )

    return {
        "cutoff": int(cutoff),
        "n_train": int(train_mask.sum()),
        "n_test_warm": int(warm_test_mask.sum()),
        "n_warm_artists": int(len(warm_artists)),
        "n_test_artists": int(len(set(test_artists))),
        "eps": float(eps),
        "models": metrics,
    }


# ─────────────────────────────────────
# Huber eps tuning (D)
# ─────────────────────────────────────
def huber_eps_tuning(df_feat, y, cutoff=2023):
    rows = []
    for eps in [1.0, 1.35, 1.5, 2.0]:
        r = eval_cutoff(df_feat, y, cutoff=cutoff, eps=eps)
        if r is None:
            continue
        rows.append({
            "eps": eps,
            "baseline_mdape": r["models"]["baseline"]["mdape"],
            "fe_only_mdape": r["models"]["fe_only"]["mdape"],
            "fe_only_diff": r["models"]["fe_only"]["mdape"] - r["models"]["baseline"]["mdape"],
        })
    return rows


# ─────────────────────────────────────
# Main
# ─────────────────────────────────────
def run():
    df = pd.read_parquet(DATA)
    df_feat = make_features(df)
    y = df_feat["log_price"]

    summary = {}

    # 1. Cutoff 별 6 모델 평가 (eps=1.35)
    logger.info("=" * 80)
    logger.info("Stage 3 Warm-start Feature 재탐색 (코덱스 권고)")
    logger.info("=" * 80)
    logger.info("\n--- 1. 6-model rolling (eps=1.35) ---")
    cutoff_results = []
    for c in [2022, 2023, 2024]:
        r = eval_cutoff(df_feat, y, c)
        if r is None:
            continue
        cutoff_results.append(r)
        logger.info(f"\n[cutoff {c}]  n_test={r['n_test_warm']}  n_artists={r['n_test_artists']}")
        logger.info(f"  {'model':>16} {'mdape':>8} {'p90':>8} {'win%':>6} {'CI mean':>9} {'CI [lo, hi]':>20} {'P<0':>6}")
        for name, m in r["models"].items():
            wr = m.get("win_rate_vs_baseline")
            wr_str = f"{wr:>5.1f}" if wr is not None else "  n/a"
            boot = m.get("bootstrap_diff_vs_baseline")
            if boot:
                ci_str = f"[{boot['ci_lo_95']:+5.2f}, {boot['ci_hi_95']:+5.2f}]"
                logger.info(
                    f"  {name:>16} {m['mdape']:>6.2f}% {m['p90_ape']:>6.2f}% {wr_str}  "
                    f"{boot['mean']:>+6.2f}  {ci_str:>20}  {boot['p_below_zero']:>5.1%}"
                )
            else:
                logger.info(f"  {name:>16} {m['mdape']:>6.2f}% {m['p90_ape']:>6.2f}%   (baseline)")
    summary["1_cutoff_6model"] = cutoff_results

    # 2. Huber eps 튜닝 (cutoff 2023)
    logger.info("\n--- 2. Huber eps 튜닝 (cutoff 2023, baseline + fe_only 비교) ---")
    eps_results = huber_eps_tuning(df_feat, y, cutoff=2023)
    logger.info(f"\n  {'eps':>5} {'baseline':>10} {'fe_only':>10} {'fe diff':>10}")
    for r in eps_results:
        logger.info(
            f"  {r['eps']:>5.2f} {r['baseline_mdape']:>8.2f}% {r['fe_only_mdape']:>8.2f}% "
            f"{r['fe_only_diff']:>+7.2f}%p"
        )
    summary["2_huber_eps_tuning"] = eps_results

    out = RESULTS / "stage3_warm_feature_exploration.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(f"\nSaved: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    run()
