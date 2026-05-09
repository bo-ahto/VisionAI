"""N=15 Confirmatory cycle (decision-binding).

Prereg: docs/n15_confirmatory_prereg_20260509.md (R3 LGTM 잠금)
코덱스 자문 R1-R3 LGTM (prereg locked).

Method (per prereg §2):
- Multi-seed: split_seed ∈ (31337, 7, 13)
- Holdout split: cold = GroupShuffleSplit(0.20) / warm = train_test_split(0.20, shuffle)
- Per (seed) 80% pool 위에서 4 model 학습:
    cb_n15, xgb_n15, cb_n32, xgb_n32
- Predictions on holdout:
    Cold path: ens = (cb + xgb)/2 / pure XGB / pure CB (per N)
    Warm path: XGB only (e3367ed convention)
- Per-source MdAPE (artsy / saatchi) + overall
- 4 Guards × 2 candidates (strong XGB@N=15 / weak Ens@N=15)
- Per-seed verdict (PASS/INCONCLUSIVE/FAIL) → multi-seed aggregate (PASS×3 only ADOPT)

Usage:
    python3 scripts/validate_n15_confirmatory.py
    python3 scripts/validate_n15_confirmatory.py --seeds 31337
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import xgboost as xgb
from catboost import CatBoostRegressor, Pool
from sklearn.model_selection import GroupShuffleSplit, train_test_split

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from calibrate_source_bias import _load_tuned_params, _mdape
from train_primary_market_v3_filtered import (
    CAT_FEATURES,
    CB_FEATURES,
    _warm_mask,
    load_data,
    prepare_features,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ARTIFACTS_DIR = REPO / "model_test_results"
HOLDOUT_DIR = REPO / "data" / "n15_confirmatory_holdout_20260509"
RESULTS_PATH = ARTIFACTS_DIR / "n15_confirmatory_20260509.json"

SPLIT_SEEDS = (31337, 7, 13)
ARTIFACT_SEED = 42
BOOTSTRAP_ITERATIONS = 1000
BOOTSTRAP_CI_PCT = 0.90
SMALL_CELL_N_THRESHOLD = 500

N15_FEATURES = [
    "ln_area", "artist_total_works", "career_stage", "area_cm2",
    "ln_followers", "artist_birth_year", "ho_x_support", "has_seoul",
    "ho", "ho_power", "medium_category", "aspect_ratio",
    "ln_ho", "for_sale_ratio", "has_depth",
]
CAT_FEATURES_N15 = [f for f in CAT_FEATURES if f in N15_FEATURES]
CAT_FEATURES_N32 = list(CAT_FEATURES)

GUARDS_STRONG: dict[str, tuple[str, float]] = {
    "G1_xgb": ("delta_cold_overall_xgb_vs_ens32", 0.5),
    "G2_xgb": ("delta_cold_artsy_xgb_vs_ens32", 0.8),
    "G3_xgb": ("delta_cold_saatchi_xgb_vs_ens32", 1.0),
    "G4_xgb": ("delta_warm_xgb_vs_xgb32", 0.3),
}
GUARDS_WEAK: dict[str, tuple[str, float]] = {
    "G1_ens": ("delta_cold_overall_ens_vs_ens32", 0.5),
    "G2_ens": ("delta_cold_artsy_ens_vs_ens32", 0.8),
    "G3_ens": ("delta_cold_saatchi_ens_vs_ens32", 1.0),
    "G4_ens": ("delta_warm_xgb_vs_xgb32", 0.3),
}


def _dataset_fingerprint(df: pd.DataFrame) -> str:
    payload = df.sort_index(axis=1).to_csv(index=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _train_cb(
    X_pool: pd.DataFrame, y_pool: np.ndarray, features: list[str],
    cat_features: list[str], cb_params: dict,
) -> CatBoostRegressor:
    cb = CatBoostRegressor(
        **cb_params, loss_function="RMSE", verbose=0,
        random_seed=ARTIFACT_SEED, allow_writing_files=False,
    )
    cat_idx = [features.index(c) for c in cat_features if c in features]
    pool = Pool(X_pool[features], label=y_pool, cat_features=cat_idx)
    cb.fit(pool)
    return cb


def _local_label_encode_xgb(
    X_train: pd.DataFrame, cat_features: list[str],
) -> tuple[pd.DataFrame, dict[str, dict[str, int]]]:
    """Local version that only encodes provided cat_features (bypasses global CAT_FEATURES)."""
    Xe = X_train.copy()
    label_maps: dict[str, dict[str, int]] = {}
    for col in cat_features:
        if col not in Xe.columns:
            continue
        train_vals = Xe[col].unique()
        mapping = {v: i for i, v in enumerate(sorted(train_vals, key=lambda x: (x is None, x)))}
        label_maps[col] = mapping
        Xe[col] = Xe[col].map(mapping).astype(float)
    return Xe, label_maps


def _train_xgb(
    X_pool: pd.DataFrame, y_pool: np.ndarray, features: list[str],
    cat_features: list[str], xgb_params: dict,
) -> tuple[xgb.Booster, dict[str, dict[str, int]]]:
    Xe, label_maps = _local_label_encode_xgb(X_pool[features], cat_features)
    dtrain = xgb.DMatrix(Xe, label=y_pool)
    xgb_p = {k: v for k, v in xgb_params.items() if k != "num_boost_round"}
    booster = xgb.train(
        params={**xgb_p, "objective": "reg:squarederror", "verbosity": 0,
                "seed": ARTIFACT_SEED},
        dtrain=dtrain,
        num_boost_round=xgb_params.get("num_boost_round", 1000),
    )
    return booster, label_maps


def _predict_cb(
    cb: CatBoostRegressor, X: pd.DataFrame, features: list[str], cat_features: list[str],
) -> np.ndarray:
    cat_idx = [features.index(c) for c in cat_features if c in features]
    pool = Pool(X[features], cat_features=cat_idx)
    return np.asarray(cb.predict(pool))


def _predict_xgb(
    booster: xgb.Booster, label_maps: dict[str, dict[str, int]],
    X: pd.DataFrame, features: list[str],
) -> np.ndarray:
    Xe = X[features].copy()
    for col, mapping in label_maps.items():
        if col in Xe.columns:
            unseen_idx = len(mapping)
            Xe[col] = Xe[col].map(mapping).fillna(unseen_idx).astype(float)
    return np.asarray(booster.predict(xgb.DMatrix(Xe)))


def _paired_bootstrap_ci(
    y_true: np.ndarray, pred_a: np.ndarray, pred_b: np.ndarray,
    n_iter: int, ci: float, seed: int,
) -> tuple[float, float]:
    """Δ = mdape(a) - mdape(b) per resampled index. Returns 90% CI [lo, hi]."""
    rng = np.random.default_rng(seed)
    n = len(y_true)
    deltas = np.empty(n_iter)
    for i in range(n_iter):
        idx = rng.integers(0, n, size=n)
        deltas[i] = _mdape(y_true[idx], pred_a[idx]) - _mdape(y_true[idx], pred_b[idx])
    alpha = (1 - ci) / 2
    return float(np.quantile(deltas, alpha)), float(np.quantile(deltas, 1 - alpha))


def _classify_per_seed(
    deltas: dict[str, float],
    guards: dict[str, tuple[str, float]],
    cold_overall_key: str,
    warm_key: str,
    warm_ci_hi: float | None,
    pass_cold_threshold: float,
    inconclusive_cold_threshold: float,
) -> tuple[str, dict[str, str]]:
    """Per-seed verdict (PASS / INCONCLUSIVE / FAIL) + guard pass/fail dict."""
    guard_status = {}
    any_guard_fail = False
    for gname, (delta_key, threshold) in guards.items():
        delta = deltas.get(delta_key, float("nan"))
        passed = delta <= threshold
        guard_status[gname] = "PASS" if passed else "FAIL"
        if not passed:
            any_guard_fail = True

    if any_guard_fail:
        return "FAIL", guard_status

    cold_delta = deltas[cold_overall_key]
    warm_delta = deltas[warm_key]

    # FAIL: large degradation
    if cold_delta > inconclusive_cold_threshold:
        return "FAIL", guard_status
    if warm_delta > 0:
        # warm regression — FAIL per prereg §3.2
        return "FAIL", guard_status

    # INCONCLUSIVE: cold in band OR warm CI uncertain
    cold_inconclusive = cold_delta > pass_cold_threshold
    warm_inconclusive = warm_ci_hi is not None and warm_ci_hi > 0
    if cold_inconclusive or warm_inconclusive:
        return "INCONCLUSIVE", guard_status

    return "PASS", guard_status


def _aggregate_3seeds(per_seed_verdicts: list[str]) -> str:
    cnt = {v: per_seed_verdicts.count(v) for v in ("PASS", "INCONCLUSIVE", "FAIL")}
    n = len(per_seed_verdicts)
    if cnt["PASS"] == n:
        return "PASS"
    if cnt["FAIL"] >= 2:
        return "FAIL"
    return "INCONCLUSIVE"


def run_one_seed(
    seed: int, X: pd.DataFrame, y: np.ndarray, groups: np.ndarray,
    source: np.ndarray, cb_params: dict, xgb_params: dict,
) -> dict[str, Any]:
    logger.info("=== seed=%d ===", seed)

    # Cold split
    gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=seed)
    pool_cold, hold_cold = next(gss.split(X, y, groups))
    pool_cold = np.sort(pool_cold)
    hold_cold = np.sort(hold_cold)
    logger.info("  cold split: pool=%d / holdout=%d", len(pool_cold), len(hold_cold))

    # Warm split
    wmask = _warm_mask(groups)
    warm_global = np.where(wmask)[0]
    warm_local = np.arange(len(warm_global))
    pool_w_loc, hold_w_loc = train_test_split(
        warm_local, test_size=0.20, random_state=seed, shuffle=True,
    )
    pool_w_loc = np.sort(pool_w_loc)
    hold_w_loc = np.sort(hold_w_loc)
    pool_warm = warm_global[pool_w_loc]
    hold_warm = warm_global[hold_w_loc]
    logger.info("  warm split: pool=%d / holdout=%d", len(pool_warm), len(hold_warm))

    X_pool_cold_df = X.iloc[pool_cold].reset_index(drop=True)
    y_pool_cold = y[pool_cold]
    X_pool_warm_df = X.iloc[pool_warm].reset_index(drop=True)
    y_pool_warm = y[pool_warm]

    # Train cold-pool models (used for cold path predictions)
    logger.info("  training cb_n15 / cb_n32 / xgb_n15 / xgb_n32 on cold pool")
    cb_n15_cold = _train_cb(X_pool_cold_df, y_pool_cold, N15_FEATURES, CAT_FEATURES_N15, cb_params)
    cb_n32_cold = _train_cb(X_pool_cold_df, y_pool_cold, CB_FEATURES, CAT_FEATURES_N32, cb_params)
    xgb_n15_cold, lm_xgb15_cold = _train_xgb(
        X_pool_cold_df, y_pool_cold, N15_FEATURES, CAT_FEATURES_N15, xgb_params,
    )
    xgb_n32_cold, lm_xgb32_cold = _train_xgb(
        X_pool_cold_df, y_pool_cold, CB_FEATURES, CAT_FEATURES_N32, xgb_params,
    )

    # Train warm-pool models (used for warm path predictions; e3367ed convention)
    logger.info("  training xgb_n15 / xgb_n32 on warm pool")
    xgb_n15_warm, lm_xgb15_warm = _train_xgb(
        X_pool_warm_df, y_pool_warm, N15_FEATURES, CAT_FEATURES_N15, xgb_params,
    )
    xgb_n32_warm, lm_xgb32_warm = _train_xgb(
        X_pool_warm_df, y_pool_warm, CB_FEATURES, CAT_FEATURES_N32, xgb_params,
    )

    # Predict on cold holdout
    X_hold_cold = X.iloc[hold_cold].reset_index(drop=True)
    y_price_cold = np.exp(y[hold_cold])
    src_cold = source[hold_cold]
    cb_n15_p_cold = np.exp(_predict_cb(cb_n15_cold, X_hold_cold, N15_FEATURES, CAT_FEATURES_N15))
    cb_n32_p_cold = np.exp(_predict_cb(cb_n32_cold, X_hold_cold, CB_FEATURES, CAT_FEATURES_N32))
    xgb_n15_p_cold = np.exp(_predict_xgb(xgb_n15_cold, lm_xgb15_cold, X_hold_cold, N15_FEATURES))
    xgb_n32_p_cold = np.exp(_predict_xgb(xgb_n32_cold, lm_xgb32_cold, X_hold_cold, CB_FEATURES))
    ens_n15_p_cold = (cb_n15_p_cold + xgb_n15_p_cold) / 2
    ens_n32_p_cold = (cb_n32_p_cold + xgb_n32_p_cold) / 2

    # Predict on warm holdout (warm-pool-trained xgb)
    X_hold_warm = X.iloc[hold_warm].reset_index(drop=True)
    y_price_warm = np.exp(y[hold_warm])
    xgb_n15_p_warm = np.exp(_predict_xgb(xgb_n15_warm, lm_xgb15_warm, X_hold_warm, N15_FEATURES))
    xgb_n32_p_warm = np.exp(_predict_xgb(xgb_n32_warm, lm_xgb32_warm, X_hold_warm, CB_FEATURES))

    # Compute per-source masks
    artsy_mask = src_cold == "artsy"
    saatchi_mask = src_cold == "saatchi"

    def per_path(y_p: np.ndarray, pred: np.ndarray, mask_a: np.ndarray, mask_s: np.ndarray) -> dict:
        return {
            "cold_overall_mdape": round(_mdape(y_p, pred), 4),
            "cold_artsy_mdape": round(_mdape(y_p[mask_a], pred[mask_a]), 4)
                if mask_a.any() else None,
            "cold_saatchi_mdape": round(_mdape(y_p[mask_s], pred[mask_s]), 4)
                if mask_s.any() else None,
        }

    metrics = {
        "cb_n15": per_path(y_price_cold, cb_n15_p_cold, artsy_mask, saatchi_mask),
        "cb_n32": per_path(y_price_cold, cb_n32_p_cold, artsy_mask, saatchi_mask),
        "xgb_n15": per_path(y_price_cold, xgb_n15_p_cold, artsy_mask, saatchi_mask),
        "xgb_n32": per_path(y_price_cold, xgb_n32_p_cold, artsy_mask, saatchi_mask),
        "ens_n15": per_path(y_price_cold, ens_n15_p_cold, artsy_mask, saatchi_mask),
        "ens_n32": per_path(y_price_cold, ens_n32_p_cold, artsy_mask, saatchi_mask),
    }
    # Warm metrics (xgb only)
    warm_xgb_n15 = round(_mdape(y_price_warm, xgb_n15_p_warm), 4)
    warm_xgb_n32 = round(_mdape(y_price_warm, xgb_n32_p_warm), 4)
    metrics["xgb_n15"]["warm_mdape"] = warm_xgb_n15
    metrics["xgb_n32"]["warm_mdape"] = warm_xgb_n32

    # Deltas (Δ = candidate - baseline / negative is improvement)
    deltas_strong = {
        "delta_cold_overall_xgb_vs_ens32": round(metrics["xgb_n15"]["cold_overall_mdape"]
                                                 - metrics["ens_n32"]["cold_overall_mdape"], 4),
        "delta_cold_artsy_xgb_vs_ens32": round((metrics["xgb_n15"]["cold_artsy_mdape"] or 0)
                                               - (metrics["ens_n32"]["cold_artsy_mdape"] or 0), 4),
        "delta_cold_saatchi_xgb_vs_ens32": round((metrics["xgb_n15"]["cold_saatchi_mdape"] or 0)
                                                 - (metrics["ens_n32"]["cold_saatchi_mdape"] or 0), 4),
        "delta_warm_xgb_vs_xgb32": round(warm_xgb_n15 - warm_xgb_n32, 4),
    }
    deltas_weak = {
        "delta_cold_overall_ens_vs_ens32": round(metrics["ens_n15"]["cold_overall_mdape"]
                                                 - metrics["ens_n32"]["cold_overall_mdape"], 4),
        "delta_cold_artsy_ens_vs_ens32": round((metrics["ens_n15"]["cold_artsy_mdape"] or 0)
                                               - (metrics["ens_n32"]["cold_artsy_mdape"] or 0), 4),
        "delta_cold_saatchi_ens_vs_ens32": round((metrics["ens_n15"]["cold_saatchi_mdape"] or 0)
                                                 - (metrics["ens_n32"]["cold_saatchi_mdape"] or 0), 4),
        "delta_warm_xgb_vs_xgb32": deltas_strong["delta_warm_xgb_vs_xgb32"],
    }

    # Bootstrap CI for Δ Warm (small holdout case)
    warm_ci: list[float] | None = None
    warm_ci_hi: float | None = None
    if len(hold_warm) < SMALL_CELL_N_THRESHOLD:
        lo, hi = _paired_bootstrap_ci(
            y_price_warm, xgb_n15_p_warm, xgb_n32_p_warm,
            n_iter=BOOTSTRAP_ITERATIONS, ci=BOOTSTRAP_CI_PCT, seed=seed,
        )
        warm_ci = [round(lo, 4), round(hi, 4)]
        warm_ci_hi = hi

    # Per-seed verdicts
    verdict_xgb, guards_strong_status = _classify_per_seed(
        deltas=deltas_strong, guards=GUARDS_STRONG,
        cold_overall_key="delta_cold_overall_xgb_vs_ens32",
        warm_key="delta_warm_xgb_vs_xgb32",
        warm_ci_hi=warm_ci_hi,
        pass_cold_threshold=0.5, inconclusive_cold_threshold=1.0,
    )
    verdict_ens, guards_weak_status = _classify_per_seed(
        deltas=deltas_weak, guards=GUARDS_WEAK,
        cold_overall_key="delta_cold_overall_ens_vs_ens32",
        warm_key="delta_warm_xgb_vs_xgb32",
        warm_ci_hi=warm_ci_hi,
        pass_cold_threshold=0.3, inconclusive_cold_threshold=0.5,
    )

    logger.info("  deltas_strong: cold=%+.3f / warm=%+.3f → %s",
                deltas_strong["delta_cold_overall_xgb_vs_ens32"],
                deltas_strong["delta_warm_xgb_vs_xgb32"], verdict_xgb)
    logger.info("  deltas_weak: cold=%+.3f / warm=%+.3f → %s",
                deltas_weak["delta_cold_overall_ens_vs_ens32"],
                deltas_weak["delta_warm_xgb_vs_xgb32"], verdict_ens)

    # Save holdout indices
    HOLDOUT_DIR.mkdir(parents=True, exist_ok=True)
    holdout_payload = {
        "split_seed": seed,
        "cold": {"pool_indices": pool_cold.tolist(), "holdout_indices": hold_cold.tolist()},
        "warm": {"pool_indices": pool_warm.tolist(), "holdout_indices": hold_warm.tolist()},
    }
    (HOLDOUT_DIR / f"seed{seed}_holdout_indices.json").write_text(
        json.dumps(holdout_payload, indent=2),
    )

    return {
        "n_pool_cold": int(len(pool_cold)),
        "n_holdout_cold": int(len(hold_cold)),
        "n_pool_warm": int(len(pool_warm)),
        "n_holdout_warm": int(len(hold_warm)),
        "n_artists_pool_cold": int(pd.unique(groups[pool_cold]).size),
        "n_artists_holdout_cold": int(pd.unique(groups[hold_cold]).size),
        "models": metrics,
        "deltas_strong": deltas_strong,
        "deltas_weak": deltas_weak,
        "guards_strong": guards_strong_status,
        "guards_weak": guards_weak_status,
        "warm_paired_bootstrap_ci90": warm_ci,
        "verdict_xgb_n15": verdict_xgb,
        "verdict_ens_n15": verdict_ens,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="N=15 Confirmatory cycle")
    parser.add_argument("--seeds", type=int, nargs="*", default=None)
    args = parser.parse_args()
    seeds = tuple(args.seeds) if args.seeds else SPLIT_SEEDS

    cb_params, xgb_params = _load_tuned_params()

    logger.info("=" * 70)
    logger.info("N=15 Confirmatory cycle / seeds=%s", seeds)
    logger.info("=" * 70)
    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].reset_index(drop=True)
    n_total = len(df)
    fingerprint = _dataset_fingerprint(df)
    X, y, groups = prepare_features(df)
    source = df["source"].astype(str).to_numpy()
    logger.info("Total rows: %d / artists: %d / fp: %s...",
                n_total, df["artist_slug"].nunique(), fingerprint[:12])

    per_seed: dict[int, Any] = {
        seed: run_one_seed(seed, X, y, groups, source, cb_params, xgb_params)
        for seed in seeds
    }

    # Aggregate
    aggregate_xgb = _aggregate_3seeds([per_seed[s]["verdict_xgb_n15"] for s in seeds])
    aggregate_ens = _aggregate_3seeds([per_seed[s]["verdict_ens_n15"] for s in seeds])

    if aggregate_xgb == "PASS":
        overall = "ADOPT_xgb"
    elif aggregate_ens == "PASS":
        overall = "ADOPT_ens"
    elif aggregate_xgb == "FAIL" and aggregate_ens == "FAIL":
        overall = "HOLD"
    else:
        overall = "NEEDS_MORE_DATA"

    output = {
        "version": "v1-n15-confirmatory",
        "split_seeds": list(seeds),
        "artifact_seed": ARTIFACT_SEED,
        "small_cell_n_threshold": SMALL_CELL_N_THRESHOLD,
        "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
        "bootstrap_ci_pct": BOOTSTRAP_CI_PCT,
        "frozen_n15_features": N15_FEATURES,
        "n32_features": list(CB_FEATURES),
        "guards_strong_locked": {k: {"name": v[0], "threshold": v[1]}
                                 for k, v in GUARDS_STRONG.items()},
        "guards_weak_locked": {k: {"name": v[0], "threshold": v[1]}
                               for k, v in GUARDS_WEAK.items()},
        "dataset_fingerprint": fingerprint,
        "n_total": n_total,
        "per_seed": per_seed,
        "aggregate": {"xgb_n15": aggregate_xgb, "ens_n15": aggregate_ens},
        "overall_verdict": overall,
        "evaluated_at": datetime.now(UTC).isoformat(),
    }
    RESULTS_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    logger.info("[OK] Saved: %s", RESULTS_PATH.name)

    # Summary
    print("\n" + "=" * 70)
    print(f"N=15 CONFIRMATORY SUMMARY (overall: {overall})")
    print("=" * 70)
    print(f"  XGB@N=15 aggregate: {aggregate_xgb}")
    print(f"  Ens@N=15 aggregate: {aggregate_ens}")
    print()
    for seed in seeds:
        r = per_seed[seed]
        print(f"  seed={seed}:")
        print(f"    XGB@N=15: {r['verdict_xgb_n15']:14s} | Δ_cold={r['deltas_strong']['delta_cold_overall_xgb_vs_ens32']:+.3f} | "
              f"Δ_warm={r['deltas_strong']['delta_warm_xgb_vs_xgb32']:+.3f}")
        print(f"    Ens@N=15: {r['verdict_ens_n15']:14s} | Δ_cold={r['deltas_weak']['delta_cold_overall_ens_vs_ens32']:+.3f} | "
              f"Δ_warm={r['deltas_weak']['delta_warm_xgb_vs_xgb32']:+.3f}")
        print(f"    guards_strong: {r['guards_strong']}")
        print(f"    guards_weak:   {r['guards_weak']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
