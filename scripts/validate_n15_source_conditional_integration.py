"""N=15 + Source-Conditional Integration cycle (decision-binding / final follow-up).

Prereg: docs/n15_source_conditional_integration_prereg_20260509.md (R3 LGTM 잠금)
코덱스 R1-R3 LGTM.

Method (per prereg §2):
- Multi-seed: split_seed ∈ (31337, 7, 13)
- Per-source × per-seed:
    - Holdout split: cold = GroupShuffleSplit(0.20) / warm = train_test_split(0.20)
    - Train BOTH v2_pool (N=15) AND v1_pool (N=32) on 80% pool (default xgb_params)
    - Cross-fit 5-fold OOF on 80% pool → per-cell guard factor for both v2 + v1_pool
    - Holdout prediction with both pool-trained artifacts × respective factor
- Per-cell verdict (PASS / INCONCLUSIVE / FAIL) for both load_bearing + consistency_only
- Multi-seed aggregate + per-source verdict + safety gate
- Overall: ADOPT_v2 / HOLD / NEEDS_MORE_DATA

Usage:
    python3 scripts/validate_n15_source_conditional_integration.py
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
from sklearn.model_selection import GroupKFold, GroupShuffleSplit, KFold, train_test_split

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from calibrate_source_bias import _cell_key, _compute_factor, _load_tuned_params, _mdape
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
HOLDOUT_DIR = REPO / "data" / "n15_sc_integration_holdout_20260509"
RESULTS_PATH = ARTIFACTS_DIR / "n15_sc_integration_20260509.json"

SPLIT_SEEDS = (31337, 7, 13)
ARTIFACT_SEED = 42
FOLD_SEED = 42
BOOTSTRAP_ITERATIONS = 1000
BOOTSTRAP_CI_PCT = 0.90
SMALL_CELL_N_THRESHOLD = 500
PASS_TOLERANCE_PP = 0.5
INCONCLUSIVE_TOLERANCE_PP = 1.0
VALID_SOURCES = ("artsy", "saatchi")

N15_FEATURES = [
    "ln_area", "artist_total_works", "career_stage", "area_cm2",
    "ln_followers", "artist_birth_year", "ho_x_support", "has_seoul",
    "ho", "ho_power", "medium_category", "aspect_ratio",
    "ln_ho", "for_sale_ratio", "has_depth",
]
CAT_FEATURES_N15 = [f for f in CAT_FEATURES if f in N15_FEATURES]
CAT_FEATURES_N32 = list(CAT_FEATURES)

SHIPPED_FACTORS_V1 = {
    "artsy": {
        "cold": {"artsy_gallery": 0.9152, "artsy_online": 0.9757},
        "warm": {"artsy_gallery": 1.0, "artsy_online": 1.0},
    },
    "saatchi": {
        "cold": {"saatchi_online": 1.0},
        "warm": {"saatchi_online": 1.0},
    },
}


def _dataset_fingerprint(df: pd.DataFrame) -> str:
    payload = df.sort_index(axis=1).to_csv(index=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _local_label_encode_xgb(
    X_train: pd.DataFrame, cat_features: list[str],
) -> tuple[pd.DataFrame, dict[str, dict[str, int]]]:
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


def _apply_label_maps(X: pd.DataFrame, label_maps: dict[str, dict[str, int]]) -> pd.DataFrame:
    Xe = X.copy()
    for col, mapping in label_maps.items():
        if col in Xe.columns:
            unseen_idx = len(mapping)
            Xe[col] = Xe[col].map(mapping).fillna(unseen_idx).astype(float)
    return Xe


def _train_cb(
    X: pd.DataFrame, y: np.ndarray, features: list[str], cat_features: list[str], cb_params: dict,
) -> CatBoostRegressor:
    cb = CatBoostRegressor(
        **cb_params, loss_function="RMSE", verbose=0,
        random_seed=ARTIFACT_SEED, allow_writing_files=False,
    )
    cat_idx = [features.index(c) for c in cat_features if c in features]
    pool = Pool(X[features], label=y, cat_features=cat_idx)
    cb.fit(pool)
    return cb


def _predict_cb(
    cb: CatBoostRegressor, X: pd.DataFrame, features: list[str], cat_features: list[str],
) -> np.ndarray:
    cat_idx = [features.index(c) for c in cat_features if c in features]
    return np.asarray(cb.predict(Pool(X[features], cat_features=cat_idx)))


def _train_xgb(
    X: pd.DataFrame, y: np.ndarray, features: list[str],
    cat_features: list[str], xgb_params: dict,
) -> tuple[xgb.Booster, dict[str, dict[str, int]]]:
    Xe, label_maps = _local_label_encode_xgb(X[features], cat_features)
    dtrain = xgb.DMatrix(Xe, label=y)
    xgb_p = {k: v for k, v in xgb_params.items() if k != "num_boost_round"}
    booster = xgb.train(
        params={**xgb_p, "objective": "reg:squarederror", "verbosity": 0,
                "seed": ARTIFACT_SEED},
        dtrain=dtrain, num_boost_round=xgb_params.get("num_boost_round", 1000),
    )
    return booster, label_maps


def _predict_xgb(
    booster: xgb.Booster, label_maps: dict[str, dict[str, int]],
    X: pd.DataFrame, features: list[str],
) -> np.ndarray:
    Xe = _apply_label_maps(X[features], label_maps)
    return np.asarray(booster.predict(xgb.DMatrix(Xe)))


def _cold_oof_factor(
    X_pool: pd.DataFrame, y_pool: np.ndarray, groups_pool: np.ndarray,
    cells_pool: np.ndarray, features: list[str], cat_features: list[str],
    cb_params: dict, n_splits: int = 5,
) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    """Cold cross-fit OOF (CatBoost) → cell factor + guard. Returns (applied, cf_baseline, cf_unguarded)."""
    gkf = GroupKFold(n_splits=n_splits)
    cb_preds_ln = np.zeros(len(y_pool))
    for tr, te in gkf.split(X_pool, y_pool, groups_pool):
        cb = _train_cb(X_pool.iloc[tr].reset_index(drop=True), y_pool[tr],
                      features, cat_features, cb_params)
        cb_preds_ln[te] = _predict_cb(cb, X_pool.iloc[te].reset_index(drop=True),
                                       features, cat_features)
    y_price = np.exp(y_pool)
    cb_pred_price = np.exp(cb_preds_ln)
    return _factor_with_guard(cells_pool, y_price, cb_pred_price)


def _warm_oof_factor(
    X_warm_pool: pd.DataFrame, y_warm_pool: np.ndarray,
    cells_warm_pool: np.ndarray, features: list[str], cat_features: list[str],
    xgb_params: dict, n_splits: int = 5,
) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    """Warm cross-fit OOF (XGBoost) → cell factor + guard."""
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=FOLD_SEED)
    xgb_preds_ln = np.zeros(len(y_warm_pool))
    for tr, te in kf.split(X_warm_pool):
        booster, lm = _train_xgb(X_warm_pool.iloc[tr].reset_index(drop=True),
                                 y_warm_pool[tr], features, cat_features, xgb_params)
        xgb_preds_ln[te] = _predict_xgb(booster, lm,
                                         X_warm_pool.iloc[te].reset_index(drop=True),
                                         features)
    y_price = np.exp(y_warm_pool)
    xgb_pred_price = np.exp(xgb_preds_ln)
    return _factor_with_guard(cells_warm_pool, y_price, xgb_pred_price)


def _factor_with_guard(
    cells: np.ndarray, y_price: np.ndarray, pred_price: np.ndarray,
) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    """Per-cell median-ratio factor + guard fallback (e3367ed pattern)."""
    applied: dict[str, float] = {}
    cf_baseline: dict[str, float] = {}
    cf_unguarded: dict[str, float] = {}
    for cell in sorted(set(cells)):
        m = cells == cell
        if not m.any():
            continue
        proposed = _compute_factor(y_price[m], pred_price[m])
        b = _mdape(y_price[m], pred_price[m])
        c = _mdape(y_price[m], pred_price[m] * proposed)
        applied[cell] = proposed if c <= b else 1.0
        cf_baseline[cell] = b
        cf_unguarded[cell] = c
    return applied, cf_baseline, cf_unguarded


def _paired_bootstrap_ci_delta(
    y: np.ndarray, pred_a: np.ndarray, pred_b: np.ndarray,
    n_iter: int, ci: float, seed: int,
) -> tuple[float, float]:
    """Δ = mdape(a) - mdape(b) per resampled index. Returns CI [lo, hi]."""
    rng = np.random.default_rng(seed)
    n = len(y)
    deltas = np.empty(n_iter)
    for i in range(n_iter):
        idx = rng.integers(0, n, size=n)
        deltas[i] = _mdape(y[idx], pred_a[idx]) - _mdape(y[idx], pred_b[idx])
    alpha = (1 - ci) / 2
    return float(np.quantile(deltas, alpha)), float(np.quantile(deltas, 1 - alpha))


def _classify_cell_per_seed(
    delta_v2_v1: float, ci_hi: float | None,
) -> str:
    """3-tier verdict per cell × seed. Same thresholds for load_bearing + consistency_only."""
    if delta_v2_v1 > INCONCLUSIVE_TOLERANCE_PP:
        return "FAIL"
    # Apply CI for small cells
    ci_ok = ci_hi is None or ci_hi <= PASS_TOLERANCE_PP
    if delta_v2_v1 <= PASS_TOLERANCE_PP and ci_ok:
        return "PASS"
    return "INCONCLUSIVE"


def _aggregate_3seeds(per_seed: list[str]) -> str:
    cnt = {v: per_seed.count(v) for v in ("PASS", "INCONCLUSIVE", "FAIL")}
    if cnt["PASS"] == len(per_seed):
        return "PASS"
    if cnt["FAIL"] >= 2:
        return "FAIL"
    return "INCONCLUSIVE"


def reproduce_one(
    source: str, seed: int, df: pd.DataFrame, X: pd.DataFrame, y: np.ndarray,
    groups: np.ndarray, cb_params: dict, xgb_params: dict,
) -> dict[str, Any]:
    """One (source, seed) iteration. Trains v2_pool (N=15) + v1_pool (N=32) + evaluates."""
    logger.info("=== %s seed=%d ===", source, seed)

    is_krw = df["is_krw"].fillna(0).astype(int).to_numpy()
    target_market = np.where(is_krw == 1, "gallery", "online")
    cells_all = np.array([_cell_key(source, tm) for tm in target_market])
    y_price = np.exp(y)

    # Cold split
    gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=seed)
    pool_cold, hold_cold = next(gss.split(X, y, groups))
    pool_cold = np.sort(pool_cold)
    hold_cold = np.sort(hold_cold)

    # Warm split
    wmask = _warm_mask(groups)
    warm_global = np.where(wmask)[0]
    warm_local = np.arange(len(warm_global))
    pool_w_loc, hold_w_loc = train_test_split(
        warm_local, test_size=0.20, random_state=seed, shuffle=True,
    )
    pool_warm = warm_global[np.sort(pool_w_loc)]
    hold_warm = warm_global[np.sort(hold_w_loc)]
    logger.info("  cold pool=%d hold=%d / warm pool=%d hold=%d",
                len(pool_cold), len(hold_cold), len(pool_warm), len(hold_warm))

    X_pool_cold = X.iloc[pool_cold].reset_index(drop=True)
    y_pool_cold = y[pool_cold]
    groups_pool_cold = groups[pool_cold]
    cells_pool_cold = cells_all[pool_cold]
    X_pool_warm = X.iloc[pool_warm].reset_index(drop=True)
    y_pool_warm = y[pool_warm]
    cells_pool_warm = cells_all[pool_warm]

    # Train artifacts on pool (v2 N=15 + v1 N=32)
    logger.info("  training v2 N=15 (CB cold + XGB warm) and v1_pool N=32 (CB cold + XGB warm)")
    cb_v2_cold = _train_cb(X_pool_cold, y_pool_cold, N15_FEATURES, CAT_FEATURES_N15, cb_params)
    cb_v1_cold = _train_cb(X_pool_cold, y_pool_cold, CB_FEATURES, CAT_FEATURES_N32, cb_params)
    xgb_v2_warm, lm_v2_w = _train_xgb(X_pool_warm, y_pool_warm, N15_FEATURES,
                                       CAT_FEATURES_N15, xgb_params)
    xgb_v1_warm, lm_v1_w = _train_xgb(X_pool_warm, y_pool_warm, CB_FEATURES,
                                       CAT_FEATURES_N32, xgb_params)

    # Cross-fit OOF for cell factors
    logger.info("  cross-fit OOF cold + warm for v2 N=15 + v1_pool N=32 (4 paths × 5 folds)")
    v2_cold_factor, _, _ = _cold_oof_factor(
        X_pool_cold, y_pool_cold, groups_pool_cold, cells_pool_cold,
        N15_FEATURES, CAT_FEATURES_N15, cb_params,
    )
    v1_cold_factor, _, _ = _cold_oof_factor(
        X_pool_cold, y_pool_cold, groups_pool_cold, cells_pool_cold,
        CB_FEATURES, CAT_FEATURES_N32, cb_params,
    )
    v2_warm_factor, _, _ = _warm_oof_factor(
        X_pool_warm, y_pool_warm, cells_pool_warm,
        N15_FEATURES, CAT_FEATURES_N15, xgb_params,
    )
    v1_warm_factor, _, _ = _warm_oof_factor(
        X_pool_warm, y_pool_warm, cells_pool_warm,
        CB_FEATURES, CAT_FEATURES_N32, xgb_params,
    )
    logger.info("  v2 cold factors: %s / warm: %s", v2_cold_factor, v2_warm_factor)
    logger.info("  v1_pool cold factors: %s / warm: %s", v1_cold_factor, v1_warm_factor)

    # Holdout prediction
    X_hc = X.iloc[hold_cold].reset_index(drop=True)
    X_hw = X.iloc[hold_warm].reset_index(drop=True)
    y_p_hc = y_price[hold_cold]
    y_p_hw = y_price[hold_warm]
    cells_hc = cells_all[hold_cold]
    cells_hw = cells_all[hold_warm]

    # v2 (N=15) cold predictions
    v2_pred_cold = np.exp(_predict_cb(cb_v2_cold, X_hc, N15_FEATURES, CAT_FEATURES_N15))
    v1_pred_cold = np.exp(_predict_cb(cb_v1_cold, X_hc, CB_FEATURES, CAT_FEATURES_N32))
    v2_pred_warm = np.exp(_predict_xgb(xgb_v2_warm, lm_v2_w, X_hw, N15_FEATURES))
    v1_pred_warm = np.exp(_predict_xgb(xgb_v1_warm, lm_v1_w, X_hw, CB_FEATURES))

    # Per-cell evaluation (cold + warm)
    holdout_per_cell: dict[str, dict[str, Any]] = {"cold": {}, "warm": {}}
    bootstrap_seed = seed * 1000 + 1

    def _eval_path(path: str, y_h: np.ndarray, v2_pred: np.ndarray, v1_pred: np.ndarray,
                   cells_h: np.ndarray, v2_factor: dict, v1_factor: dict) -> None:
        all_cells = sorted(set(cells_h.tolist())
                           | set(SHIPPED_FACTORS_V1[source][path].keys()))
        for cell in all_cells:
            shipped = float(SHIPPED_FACTORS_V1[source][path].get(cell, 1.0))
            v2_f = float(v2_factor.get(cell, 1.0))
            v1_f = float(v1_factor.get(cell, 1.0))
            category = "load_bearing" if abs(shipped - 1.0) > 1e-9 else "consistency_only"
            mask = cells_h == cell
            n = int(mask.sum())
            entry: dict[str, Any] = {
                "category": category,
                "n_holdout": n,
                "v2_factor_pool": v2_f,
                "v1_factor_pool": v1_f,
                "v1_factor_shipped": shipped,
            }
            if n == 0:
                entry["decision_per_seed"] = "FAIL"
                entry.update({k: None for k in (
                    "baseline_v2_mdape", "baseline_v1_pool_mdape",
                    "calibrated_v2_mdape", "calibrated_v1_pool_mdape",
                    "delta_v2_vs_v1pool", "paired_bootstrap_ci90",
                    "bootstrap_computed",
                )})
                holdout_per_cell[path][cell] = entry
                continue
            v2_baseline = _mdape(y_h[mask], v2_pred[mask])
            v1_baseline = _mdape(y_h[mask], v1_pred[mask])
            v2_cal = v2_pred[mask] * v2_f
            v1_cal = v1_pred[mask] * v1_f
            v2_cal_mdape = _mdape(y_h[mask], v2_cal)
            v1_cal_mdape = _mdape(y_h[mask], v1_cal)
            delta = v2_cal_mdape - v1_cal_mdape
            ci = None
            ci_hi = None
            if n < SMALL_CELL_N_THRESHOLD:
                lo, hi = _paired_bootstrap_ci_delta(
                    y_h[mask], v2_cal, v1_cal,
                    BOOTSTRAP_ITERATIONS, BOOTSTRAP_CI_PCT, bootstrap_seed,
                )
                ci = [round(lo, 4), round(hi, 4)]
                ci_hi = hi
            decision = _classify_cell_per_seed(delta, ci_hi)
            entry.update({
                "baseline_v2_mdape": round(v2_baseline, 4),
                "baseline_v1_pool_mdape": round(v1_baseline, 4),
                "calibrated_v2_mdape": round(v2_cal_mdape, 4),
                "calibrated_v1_pool_mdape": round(v1_cal_mdape, 4),
                "delta_v2_vs_v1pool": round(delta, 4),
                "bootstrap_computed": ci is not None,
                "paired_bootstrap_ci90": ci,
                "decision_per_seed": decision,
            })
            holdout_per_cell[path][cell] = entry

    _eval_path("cold", y_p_hc, v2_pred_cold, v1_pred_cold, cells_hc,
               v2_cold_factor, v1_cold_factor)
    _eval_path("warm", y_p_hw, v2_pred_warm, v1_pred_warm, cells_hw,
               v2_warm_factor, v1_warm_factor)

    # Save indices
    HOLDOUT_DIR.mkdir(parents=True, exist_ok=True)
    (HOLDOUT_DIR / f"{source}_seed{seed}_holdout_indices.json").write_text(json.dumps({
        "source": source, "split_seed": seed,
        "cold": {"pool_indices": pool_cold.tolist(), "holdout_indices": hold_cold.tolist()},
        "warm": {"pool_indices": pool_warm.tolist(), "holdout_indices": hold_warm.tolist()},
    }, indent=2))

    return {
        "n_pool_cold": int(len(pool_cold)),
        "n_holdout_cold": int(len(hold_cold)),
        "n_pool_warm": int(len(pool_warm)),
        "n_holdout_warm": int(len(hold_warm)),
        "v2_fitted_factors": {"cold": v2_cold_factor, "warm": v2_warm_factor},
        "v1_pool_fitted_factors": {"cold": v1_cold_factor, "warm": v1_warm_factor},
        "holdout_per_cell": holdout_per_cell,
    }


def aggregate_per_source(per_seed: dict[int, dict]) -> dict[str, Any]:
    aggregate: dict[str, dict[str, Any]] = {"cold": {}, "warm": {}}
    for path in ("cold", "warm"):
        cells = set()
        for s in per_seed.values():
            cells.update(s["holdout_per_cell"][path].keys())
        for cell in sorted(cells):
            decisions: list[str] = []
            category = None
            for s in per_seed.values():
                e = s["holdout_per_cell"][path].get(cell)
                if e is None:
                    continue
                category = e["category"]
                decisions.append(e["decision_per_seed"])
            agg = _aggregate_3seeds(decisions)
            aggregate[path][cell] = {
                "category": category,
                "decisions_per_seed": decisions,
                "aggregate": agg,
            }
    return aggregate


def per_source_verdict(aggregate: dict) -> str:
    """Per prereg §3.5: load_bearing all PASS + consistency_only no FAIL → ADOPT."""
    load_bearing_aggs: list[str] = []
    consistency_aggs: list[str] = []
    for path in ("cold", "warm"):
        for cell, data in aggregate[path].items():
            if data["category"] == "load_bearing":
                load_bearing_aggs.append(data["aggregate"])
            else:
                consistency_aggs.append(data["aggregate"])
    if not load_bearing_aggs:
        return "N/A_no_load_bearing"
    # Safety gate
    if any(a == "FAIL" for a in consistency_aggs):
        return "HOLD"
    if any(a == "FAIL" for a in load_bearing_aggs):
        return "HOLD"
    if all(a == "PASS" for a in load_bearing_aggs):
        return "ADOPT"
    if any(a == "INCONCLUSIVE" for a in load_bearing_aggs):
        return "NEEDS_MORE_DATA"
    return "NEEDS_MORE_DATA"


def overall_verdict(per_source_v: dict[str, str]) -> str:
    if all(v in ("ADOPT", "N/A_no_load_bearing") for v in per_source_v.values()):
        return "ADOPT_v2"
    if any(v == "HOLD" for v in per_source_v.values()):
        return "HOLD"
    return "NEEDS_MORE_DATA"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=("artsy", "saatchi", "all"), default="all")
    parser.add_argument("--seeds", type=int, nargs="*", default=None)
    args = parser.parse_args()
    sources = VALID_SOURCES if args.source == "all" else (args.source,)
    seeds = tuple(args.seeds) if args.seeds else SPLIT_SEEDS

    cb_params, xgb_params = _load_tuned_params()

    per_source_results: dict[str, Any] = {}
    for source in sources:
        logger.info("=" * 70)
        logger.info("N=15 + Source-Conditional Integration: %s / seeds=%s", source, seeds)
        logger.info("=" * 70)
        df = load_data()
        df = df[df["is_excluded_for_training"] == 0]
        df = df[df["source"] == source].reset_index(drop=True)
        n_total = len(df)
        fingerprint = _dataset_fingerprint(df)
        X, y, groups = prepare_features(df)
        logger.info("source=%s rows=%d artists=%d fp=%s...",
                    source, n_total, df["artist_slug"].nunique(), fingerprint[:12])

        per_seed: dict[int, Any] = {
            seed: reproduce_one(source, seed, df, X, y, groups, cb_params, xgb_params)
            for seed in seeds
        }
        aggregate = aggregate_per_source(per_seed)
        per_source_results[source] = {
            "n_total": n_total,
            "fingerprint": fingerprint,
            "per_seed": per_seed,
            "aggregate_per_cell": aggregate,
            "source_verdict": per_source_verdict(aggregate),
        }

    overall = overall_verdict({s: per_source_results[s]["source_verdict"] for s in sources})

    output = {
        "version": "v1-n15-sc-integration",
        "split_seeds": list(seeds),
        "artifact_seed": ARTIFACT_SEED,
        "fold_seed": FOLD_SEED,
        "pass_tolerance_pp": PASS_TOLERANCE_PP,
        "inconclusive_tolerance_pp": INCONCLUSIVE_TOLERANCE_PP,
        "frozen_n15_features": N15_FEATURES,
        "default_cb_params": cb_params,
        "default_xgb_params": xgb_params,
        "shipped_factors_v1": SHIPPED_FACTORS_V1,
        "per_source": per_source_results,
        "per_source_verdict": {s: per_source_results[s]["source_verdict"] for s in sources},
        "overall_verdict": overall,
        "evaluated_at": datetime.now(UTC).isoformat(),
    }
    RESULTS_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    logger.info("[OK] Saved: %s", RESULTS_PATH.name)

    print("\n" + "=" * 70)
    print(f"N=15 + SOURCE-CONDITIONAL INTEGRATION SUMMARY (overall: {overall})")
    print("=" * 70)
    for source in sources:
        sv = per_source_results[source]["source_verdict"]
        print(f"\n  Source [{source}] verdict: {sv}")
        for path in ("cold", "warm"):
            for cell, data in per_source_results[source]["aggregate_per_cell"][path].items():
                print(
                    f"    {path}/{cell:18s}: {data['aggregate']:14s} | "
                    f"per_seed={data['decisions_per_seed']} | category={data['category']}"
                )
    print("=" * 70)


if __name__ == "__main__":
    main()
