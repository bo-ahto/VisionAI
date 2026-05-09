"""Per-source calibration OOS verification (retrained-artifact + multi-seed / decision-binding).

Prereg: docs/calibration_per_source_oos_verification_prereg_20260509.md
코덱스 R1-R4 LGTM (jamming locked).

Method (per prereg §2):
- Multi-seed: split_seed ∈ (31337, 7, 13)
- Holdout split: cold = GroupShuffleSplit(0.20) / warm = train_test_split(0.20, shuffle)
- Base artifact retrain on 80% pool: CatBoost (cold pool) + XGBoost (warm pool)
- Calibration factor refit on 80% pool: cross-fit 5-fold OOF + per-cell guard
- Holdout eval: predict with retrained artifact (truly OOS)
- Dual-endpoint:
    Primary = per-pool refit factor → procedure OOS value
    Secondary = e3367ed shipped factor → shipped-factor non-regression
- Paired bootstrap CI (small cell / both endpoints / same indices)
- Per-seed cell decision: primary 4-tier (PASS/GUARD_FIRED/INCONCLUSIVE/FAIL) +
  secondary 3-tier (SHIPPED_PASS/INCONCLUSIVE/FAIL)
- Multi-seed aggregate per cell + per-cell adoption matrix (§3.4)

Usage:
    python3 scripts/validate_per_source_calibration_oos.py
    python3 scripts/validate_per_source_calibration_oos.py --source artsy --seeds 31337
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
from sklearn.model_selection import GroupShuffleSplit, KFold, train_test_split

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from calibrate_source_bias import (
    _cell_key,
    _cold_oof_with_fold_id,
    _cross_fit_eval,
    _load_tuned_params,
    _mdape,
)
from train_primary_market_v3_filtered import (
    CAT_FEATURES,
    _label_encode_xgb,
    _warm_mask,
    load_data,
    prepare_features,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ARTIFACTS_DIR = REPO / "model_test_results"
HOLDOUT_DIR = REPO / "data" / "oos_holdout_20260509"
RESULTS_PATH = ARTIFACTS_DIR / "calibration_oos_20260509.json"

SPLIT_SEEDS = (31337, 7, 13)
FOLD_SEED = 42
ARTIFACT_SEED = 42
DRIFT_THRESHOLD_LOG = float(np.log(1.3))
SMALL_CELL_N_THRESHOLD = 500
BOOTSTRAP_ITERATIONS = 1000
BOOTSTRAP_CI_PCT = 0.90
VALID_SOURCES = ("artsy", "saatchi")

SHIPPED_FACTORS: dict[str, dict[str, dict[str, float]]] = {
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


def _cb_pool_for_predict(X: pd.DataFrame) -> Pool:
    cat_idx = [X.columns.get_loc(c) for c in CAT_FEATURES if c in X.columns]
    return Pool(X, cat_features=cat_idx)


def _cb_pool_for_train(X: pd.DataFrame, y: np.ndarray) -> Pool:
    cat_idx = [X.columns.get_loc(c) for c in CAT_FEATURES if c in X.columns]
    return Pool(X, label=y, cat_features=cat_idx)


def _retrain_cold_artifact(
    X_pool: pd.DataFrame, y_pool: np.ndarray, cb_params: dict,
) -> CatBoostRegressor:
    cb = CatBoostRegressor(
        **cb_params, loss_function="RMSE", verbose=0,
        random_seed=ARTIFACT_SEED, allow_writing_files=False,
    )
    cb.fit(_cb_pool_for_train(X_pool, y_pool))
    return cb


def _retrain_warm_artifact(
    X_warm_pool: pd.DataFrame, y_warm_pool: np.ndarray, xgb_params: dict,
) -> tuple[xgb.Booster, dict[str, dict[str, int]]]:
    Xe, _, label_maps = _label_encode_xgb(X_warm_pool, X_warm_pool.iloc[:1])
    dtrain = xgb.DMatrix(Xe, label=y_warm_pool)
    xgb_p = {k: v for k, v in xgb_params.items() if k != "num_boost_round"}
    booster = xgb.train(
        params={**xgb_p, "objective": "reg:squarederror", "verbosity": 0,
                "seed": ARTIFACT_SEED},
        dtrain=dtrain,
        num_boost_round=xgb_params.get("num_boost_round", 1000),
    )
    return booster, label_maps


def _apply_label_maps(X: pd.DataFrame, label_maps: dict[str, dict[str, int]]) -> pd.DataFrame:
    Xe = X.copy()
    for col, mapping in label_maps.items():
        if col in Xe.columns:
            Xe[col] = Xe[col].astype(str).map(mapping).fillna(-1).astype(int)
    return Xe


def _cross_fit_warm_oof_on_subset(
    X_warm: pd.DataFrame,
    y_warm: np.ndarray,
    xgb_params: dict,
    n_splits: int = 5,
) -> tuple[np.ndarray, np.ndarray]:
    """Replicate _warm_oof_with_fold_id on already-warm-filtered subset."""
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=FOLD_SEED)
    n = len(y_warm)
    preds = np.zeros(n)
    fold_ids = np.full(n, -1, dtype=int)
    for fold, (tr, te) in enumerate(kf.split(X_warm)):
        logger.info("    [Warm refit fold %d/%d] train=%d test=%d",
                    fold + 1, n_splits, len(tr), len(te))
        Xtr_e, Xte_e, _ = _label_encode_xgb(X_warm.iloc[tr], X_warm.iloc[te])
        dtrain = xgb.DMatrix(Xtr_e, label=y_warm[tr])
        dtest = xgb.DMatrix(Xte_e, label=y_warm[te])
        xgb_p = {k: v for k, v in xgb_params.items() if k != "num_boost_round"}
        m = xgb.train(
            params={**xgb_p, "objective": "reg:squarederror", "verbosity": 0,
                    "seed": FOLD_SEED},
            dtrain=dtrain,
            num_boost_round=xgb_params.get("num_boost_round", 1000),
        )
        preds[te] = m.predict(dtest)
        fold_ids[te] = fold
    return preds, fold_ids


def _apply_guard(
    cells_pool: np.ndarray,
    y_price_pool: np.ndarray,
    pred_price_pool: np.ndarray,
    cal_pred_pool: np.ndarray,
    proposed_factors: dict[str, float],
) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    applied: dict[str, float] = {}
    cf_baseline: dict[str, float] = {}
    cf_unguarded: dict[str, float] = {}
    for cell in sorted(set(cells_pool)):
        m = cells_pool == cell
        if not m.any():
            continue
        b = _mdape(y_price_pool[m], pred_price_pool[m])
        c = _mdape(y_price_pool[m], cal_pred_pool[m])
        proposed = proposed_factors.get(cell, 1.0)
        applied[cell] = proposed if c <= b else 1.0
        cf_baseline[cell] = b
        cf_unguarded[cell] = c
    return applied, cf_baseline, cf_unguarded


def _paired_bootstrap_ci_dual(
    y_true: np.ndarray,
    pred_baseline: np.ndarray,
    pred_refit: np.ndarray,
    pred_shipped: np.ndarray,
    n_iter: int,
    ci: float,
    seed: int,
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Paired bootstrap returning (refit_ci, shipped_ci) on same resampled indices."""
    rng = np.random.default_rng(seed)
    n = len(y_true)
    deltas_refit = np.empty(n_iter)
    deltas_shipped = np.empty(n_iter)
    for i in range(n_iter):
        idx = rng.integers(0, n, size=n)
        b = _mdape(y_true[idx], pred_baseline[idx])
        c_r = _mdape(y_true[idx], pred_refit[idx])
        c_s = _mdape(y_true[idx], pred_shipped[idx])
        deltas_refit[i] = c_r - b
        deltas_shipped[i] = c_s - b
    alpha = (1 - ci) / 2
    return (
        (float(np.quantile(deltas_refit, alpha)),
         float(np.quantile(deltas_refit, 1 - alpha))),
        (float(np.quantile(deltas_shipped, alpha)),
         float(np.quantile(deltas_shipped, 1 - alpha))),
    )


def _classify_primary_per_seed(
    category: str,
    delta_refit: float,
    applied_factor_refit: float,
    ci_hi_refit: float | None,
    cf_unguarded: float | None,
    cf_baseline: float | None,
) -> str:
    if category == "consistency_only":
        if cf_unguarded is None or cf_baseline is None:
            return "GUARD_OK"
        if cf_unguarded > cf_baseline and applied_factor_refit != 1.0:
            return "GUARD_VIOLATION"
        return "GUARD_OK"
    # load_bearing 4-tier
    if delta_refit > 0:
        return "FAIL"
    if (cf_unguarded is not None and cf_baseline is not None
            and cf_unguarded > cf_baseline and applied_factor_refit != 1.0):
        return "FAIL"  # guard implementation violation
    if applied_factor_refit == 1.0:
        return "GUARD_FIRED"
    # applied_factor != 1.0 AND delta <= 0
    ci_ok = ci_hi_refit is None or ci_hi_refit <= 0
    return "PASS" if ci_ok else "INCONCLUSIVE"


def _classify_secondary_per_seed(
    category: str,
    delta_shipped: float,
    ci_hi_shipped: float | None,
) -> str | None:
    if category == "consistency_only":
        return None  # N/A — shipped == 1.0
    if delta_shipped > 0:
        return "SHIPPED_FAIL"
    ci_ok = ci_hi_shipped is None or ci_hi_shipped <= 0
    return "SHIPPED_PASS" if ci_ok else "SHIPPED_INCONCLUSIVE"


def _aggregate_primary(per_seed_decisions: list[str]) -> str:
    cnt = {d: per_seed_decisions.count(d) for d in
           ("PASS", "GUARD_FIRED", "INCONCLUSIVE", "FAIL")}
    n = len(per_seed_decisions)
    if cnt["PASS"] == n:
        return "PRIMARY_PASS"
    if cnt["PASS"] == n - 1 and (cnt["INCONCLUSIVE"] == 1 or cnt["GUARD_FIRED"] == 1):
        return "PRIMARY_PASS_with_caveat"
    if cnt["GUARD_FIRED"] == n:
        return "PROCEDURE_NULL"
    if cnt["GUARD_FIRED"] == n - 1 and (cnt["INCONCLUSIVE"] == 1 or cnt["PASS"] == 1):
        return "PROCEDURE_NULL_likely"
    if cnt["FAIL"] >= 2:
        return "PRIMARY_FAIL"
    if cnt["INCONCLUSIVE"] == n:
        return "INCONCLUSIVE"
    return "INCONCLUSIVE"


def _aggregate_secondary(per_seed_decisions: list[str]) -> str:
    cnt = {d: per_seed_decisions.count(d) for d in
           ("SHIPPED_PASS", "SHIPPED_INCONCLUSIVE", "SHIPPED_FAIL")}
    n = len(per_seed_decisions)
    if cnt["SHIPPED_PASS"] == n:
        return "SECONDARY_PASS"
    if cnt["SHIPPED_PASS"] == n - 1 and cnt["SHIPPED_INCONCLUSIVE"] == 1:
        return "SECONDARY_PASS_with_caveat"
    if cnt["SHIPPED_FAIL"] >= 2:
        return "SECONDARY_FAIL"
    if cnt["SHIPPED_INCONCLUSIVE"] == n:
        return "SECONDARY_INCONCLUSIVE"
    return "SECONDARY_INCONCLUSIVE"


def _classify_cell_adoption(primary_agg: str, secondary_agg: str | None) -> str:
    # secondary_agg is None for consistency_only
    if secondary_agg is None:
        return "N/A_consistency_only"
    if primary_agg == "PRIMARY_PASS" and secondary_agg == "SECONDARY_PASS":
        return "ADOPT"
    if primary_agg == "PRIMARY_PASS" and secondary_agg == "SECONDARY_PASS_with_caveat":
        return "ADOPT_with_caveat"
    if primary_agg == "PRIMARY_PASS_with_caveat" and secondary_agg in (
            "SECONDARY_PASS", "SECONDARY_PASS_with_caveat"):
        return "ADOPT_with_caveat"
    if primary_agg in ("PROCEDURE_NULL", "PROCEDURE_NULL_likely") and secondary_agg in (
            "SECONDARY_PASS", "SECONDARY_PASS_with_caveat"):
        return "ADOPT_shipped_only"
    if secondary_agg == "SECONDARY_FAIL":
        return "HOLD"
    if primary_agg == "PRIMARY_FAIL":
        return "HOLD"
    return "NEEDS_MORE_DATA"


def reproduce_per_source_per_seed(
    source: str, seed: int, df: pd.DataFrame, X: pd.DataFrame, y: np.ndarray,
    groups: np.ndarray, cells_all: np.ndarray, y_price: np.ndarray,
    cb_params: dict, xgb_params: dict,
) -> dict[str, Any]:
    """One (source, seed) iteration. Pre-loaded data passed in to avoid reload."""
    logger.info("--- %s / seed=%d ---", source, seed)

    # Cold holdout split
    gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=seed)
    pool_cold, hold_cold = next(gss.split(X, y, groups))
    pool_cold = np.sort(pool_cold)
    hold_cold = np.sort(hold_cold)

    # Warm holdout split
    wmask = _warm_mask(groups)
    warm_global = np.where(wmask)[0]
    warm_local = np.arange(len(warm_global))
    pool_warm_local, hold_warm_local = train_test_split(
        warm_local, test_size=0.20, random_state=seed, shuffle=True,
    )
    pool_warm_local = np.sort(pool_warm_local)
    hold_warm_local = np.sort(hold_warm_local)
    pool_warm = warm_global[pool_warm_local]
    hold_warm = warm_global[hold_warm_local]
    logger.info("  cold pool=%d hold=%d / warm pool=%d hold=%d",
                len(pool_cold), len(hold_cold), len(pool_warm), len(hold_warm))

    # Retrain base artifacts on 80% pool
    logger.info("  Retrain cold (CatBoost on cold pool)")
    cb_artifact = _retrain_cold_artifact(
        X.iloc[pool_cold].reset_index(drop=True), y[pool_cold], cb_params,
    )
    logger.info("  Retrain warm (XGBoost on warm pool)")
    X_pool_warm_df = X.iloc[pool_warm].reset_index(drop=True)
    xgb_artifact, label_maps = _retrain_warm_artifact(
        X_pool_warm_df, y[pool_warm], xgb_params,
    )

    # Cold refit factor (cross-fit OOF on 80% pool / fold-trained models)
    logger.info("  Cold refit (cross-fit OOF on 80%% pool)")
    X_pool_cold_df = X.iloc[pool_cold].reset_index(drop=True)
    y_pool_cold = y[pool_cold]
    groups_pool_cold = groups[pool_cold]
    cells_pool_cold = cells_all[pool_cold]
    cb_preds_pool_ln, fold_ids_cold = _cold_oof_with_fold_id(
        X_pool_cold_df, y_pool_cold, groups_pool_cold, cb_params,
    )
    y_price_pool_cold = np.exp(y_pool_cold)
    cb_pred_price_pool = np.exp(cb_preds_pool_ln)
    cold_factors_proposed, _, _, cold_cal_pred_pool = _cross_fit_eval(
        y_price_pool_cold, cb_pred_price_pool, cells_pool_cold, fold_ids_cold,
    )
    cold_refit_applied, cf_b_cold, cf_u_cold = _apply_guard(
        cells_pool_cold, y_price_pool_cold, cb_pred_price_pool, cold_cal_pred_pool,
        cold_factors_proposed,
    )
    logger.info("  cold refit (guarded): %s", cold_refit_applied)

    # Warm refit factor (cross-fit OOF on 80% warm pool)
    logger.info("  Warm refit (cross-fit OOF on 80%% warm pool)")
    y_pool_warm = y[pool_warm]
    groups_pool_warm = groups[pool_warm]
    cells_pool_warm = cells_all[pool_warm]
    xgb_preds_pool_ln, fold_ids_warm = _cross_fit_warm_oof_on_subset(
        X_pool_warm_df, y_pool_warm, xgb_params,
    )
    y_price_pool_warm = np.exp(y_pool_warm)
    xgb_pred_price_pool = np.exp(xgb_preds_pool_ln)
    warm_factors_proposed, _, _, warm_cal_pred_pool = _cross_fit_eval(
        y_price_pool_warm, xgb_pred_price_pool, cells_pool_warm, fold_ids_warm,
    )
    warm_refit_applied, cf_b_warm, cf_u_warm = _apply_guard(
        cells_pool_warm, y_price_pool_warm, xgb_pred_price_pool, warm_cal_pred_pool,
        warm_factors_proposed,
    )
    logger.info("  warm refit (guarded): %s", warm_refit_applied)

    # Holdout prediction with retrained artifacts (truly OOS)
    X_hold_cold = X.iloc[hold_cold].reset_index(drop=True)
    cb_hold_pred_ln = cb_artifact.predict(_cb_pool_for_predict(X_hold_cold))
    cb_hold_pred_price = np.exp(cb_hold_pred_ln)

    X_hold_warm = X.iloc[hold_warm].reset_index(drop=True)
    X_hold_warm_e = _apply_label_maps(X_hold_warm, label_maps)
    xgb_hold_pred_ln = xgb_artifact.predict(xgb.DMatrix(X_hold_warm_e))
    xgb_hold_pred_price = np.exp(xgb_hold_pred_ln)

    # Per-cell holdout evaluation (dual-endpoint)
    holdout_per_cell = {
        "cold": _per_cell_eval_dual(
            "cold", source,
            y_price[hold_cold], cb_hold_pred_price, cells_all[hold_cold], groups[hold_cold],
            cells_pool_cold, groups_pool_cold,
            cold_refit_applied, SHIPPED_FACTORS[source]["cold"],
            cf_b_cold, cf_u_cold, seed,
        ),
        "warm": _per_cell_eval_dual(
            "warm", source,
            y_price[hold_warm], xgb_hold_pred_price, cells_all[hold_warm], groups[hold_warm],
            cells_pool_warm, groups_pool_warm,
            warm_refit_applied, SHIPPED_FACTORS[source]["warm"],
            cf_b_warm, cf_u_warm, seed,
        ),
    }

    # Save holdout indices
    HOLDOUT_DIR.mkdir(parents=True, exist_ok=True)
    holdout_payload = {
        "source": source, "split_seed": seed,
        "cold": {
            "pool_indices": pool_cold.tolist(),
            "holdout_indices": hold_cold.tolist(),
        },
        "warm": {
            "pool_indices": pool_warm.tolist(),
            "holdout_indices": hold_warm.tolist(),
        },
    }
    (HOLDOUT_DIR / f"{source}_seed{seed}_holdout_indices.json").write_text(
        json.dumps(holdout_payload, indent=2),
    )

    return {
        "n_train_pool_cold": int(len(pool_cold)),
        "n_holdout_cold": int(len(hold_cold)),
        "n_artists_pool_cold": int(pd.unique(groups[pool_cold]).size),
        "n_artists_holdout_cold": int(pd.unique(groups[hold_cold]).size),
        "n_train_pool_warm": int(len(pool_warm)),
        "n_holdout_warm": int(len(hold_warm)),
        "fitted_factors": {"cold": cold_refit_applied, "warm": warm_refit_applied},
        "holdout_per_cell": holdout_per_cell,
    }


def _per_cell_eval_dual(
    path: str,
    source: str,
    y_h_price: np.ndarray,
    pred_h_price: np.ndarray,
    cells_h: np.ndarray,
    groups_h: np.ndarray,
    cells_pool: np.ndarray,
    groups_pool: np.ndarray,
    refit_applied: dict[str, float],
    shipped_factors: dict[str, float],
    cf_baseline: dict[str, float],
    cf_unguarded: dict[str, float],
    seed: int,
) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    cell_set = sorted(set(cells_h.tolist()) | set(shipped_factors.keys()))
    for cell in cell_set:
        shipped = float(shipped_factors.get(cell, 1.0))
        refit = float(refit_applied.get(cell, 1.0))
        category = "load_bearing" if abs(shipped - 1.0) > 1e-9 else "consistency_only"
        m_h = cells_h == cell
        m_p = cells_pool == cell
        n_h = int(m_h.sum())
        n_p = int(m_p.sum())
        entry: dict[str, Any] = {
            "category": category,
            "n_train_pool": n_p,
            "n_holdout": n_h,
            "n_artists_train_pool": int(pd.unique(groups_pool[m_p]).size) if n_p else 0,
            "n_artists_holdout": int(pd.unique(groups_h[m_h]).size) if n_h else 0,
            "applied_factor_refit": refit,
            "shipped_factor": shipped,
        }
        if n_h == 0:
            entry["decision_primary_per_seed"] = (
                "GUARD_OK" if category == "consistency_only" else "FAIL"
            )
            entry["decision_secondary_per_seed"] = (
                None if category == "consistency_only" else "SHIPPED_FAIL"
            )
            entry.update({
                "baseline_mdape": None,
                "calibrated_mdape_refit": None, "calibrated_mdape_shipped": None,
                "delta_refit_pp": None, "delta_shipped_pp": None,
                "bootstrap_computed": False,
                "paired_bootstrap_ci90_delta_refit": None,
                "paired_bootstrap_ci90_delta_shipped": None,
            })
            out[cell] = entry
            continue
        baseline = _mdape(y_h_price[m_h], pred_h_price[m_h])
        cal_refit = pred_h_price[m_h] * refit
        cal_shipped = pred_h_price[m_h] * shipped
        cal_refit_mdape = _mdape(y_h_price[m_h], cal_refit)
        cal_shipped_mdape = _mdape(y_h_price[m_h], cal_shipped)
        delta_refit = cal_refit_mdape - baseline
        delta_shipped = cal_shipped_mdape - baseline
        small_cell = n_h < SMALL_CELL_N_THRESHOLD
        ci_refit = None
        ci_shipped = None
        ci_hi_refit = None
        ci_hi_shipped = None
        if small_cell and category == "load_bearing":
            (lo_r, hi_r), (lo_s, hi_s) = _paired_bootstrap_ci_dual(
                y_h_price[m_h], pred_h_price[m_h], cal_refit, cal_shipped,
                n_iter=BOOTSTRAP_ITERATIONS, ci=BOOTSTRAP_CI_PCT, seed=seed,
            )
            ci_refit = [round(lo_r, 4), round(hi_r, 4)]
            ci_shipped = [round(lo_s, 4), round(hi_s, 4)]
            ci_hi_refit = hi_r
            ci_hi_shipped = hi_s
        decision_primary = _classify_primary_per_seed(
            category=category, delta_refit=delta_refit,
            applied_factor_refit=refit, ci_hi_refit=ci_hi_refit,
            cf_unguarded=cf_unguarded.get(cell), cf_baseline=cf_baseline.get(cell),
        )
        decision_secondary = _classify_secondary_per_seed(
            category=category, delta_shipped=delta_shipped, ci_hi_shipped=ci_hi_shipped,
        )
        entry.update({
            "baseline_mdape": round(baseline, 4),
            "calibrated_mdape_refit": round(cal_refit_mdape, 4),
            "calibrated_mdape_shipped": round(cal_shipped_mdape, 4),
            "delta_refit_pp": round(delta_refit, 4),
            "delta_shipped_pp": round(delta_shipped, 4),
            "bootstrap_computed": ci_refit is not None,
            "paired_bootstrap_ci90_delta_refit": ci_refit,
            "paired_bootstrap_ci90_delta_shipped": ci_shipped,
            "decision_primary_per_seed": decision_primary,
            "decision_secondary_per_seed": decision_secondary,
        })
        out[cell] = entry
    return out


def aggregate_per_source(per_seed: dict[int, dict]) -> dict[str, Any]:
    """Aggregate per-cell across seeds. Returns per-cell aggregate per path."""
    aggregate: dict[str, dict[str, Any]] = {"cold": {}, "warm": {}}
    for path in ("cold", "warm"):
        # collect cells across seeds
        cells = set()
        for seed_data in per_seed.values():
            cells.update(seed_data["holdout_per_cell"][path].keys())
        for cell in sorted(cells):
            primary_decisions = []
            secondary_decisions = []
            category = None
            for seed_data in per_seed.values():
                e = seed_data["holdout_per_cell"][path].get(cell)
                if e is None:
                    continue
                category = e["category"]
                primary_decisions.append(e["decision_primary_per_seed"])
                if e["decision_secondary_per_seed"] is not None:
                    secondary_decisions.append(e["decision_secondary_per_seed"])
            if category == "load_bearing":
                primary_agg = _aggregate_primary(primary_decisions)
                secondary_agg = (
                    _aggregate_secondary(secondary_decisions)
                    if secondary_decisions else None
                )
            else:
                # consistency_only — aggregate guard outcomes only
                primary_agg = (
                    "PRIMARY_PASS"
                    if all(d == "GUARD_OK" for d in primary_decisions)
                    else "GUARD_VIOLATION_DETECTED"
                )
                secondary_agg = None
            aggregate[path][cell] = {
                "category": category,
                "primary_decisions_per_seed": primary_decisions,
                "secondary_decisions_per_seed": secondary_decisions,
                "primary_aggregate": primary_agg,
                "secondary_aggregate": secondary_agg,
                "cell_adoption": (
                    _classify_cell_adoption(primary_agg, secondary_agg)
                    if category == "load_bearing"
                    else "N/A_consistency_only"
                ),
            }
    return aggregate


def per_source_verdict(aggregate_per_cell: dict) -> str:
    """Per prereg §3.5."""
    statuses: list[str] = []
    for path in ("cold", "warm"):
        for cell, data in aggregate_per_cell[path].items():
            if data["category"] != "load_bearing":
                continue
            statuses.append(data["cell_adoption"])
    if not statuses:
        return "N/A_no_load_bearing"
    if all(s in ("ADOPT", "ADOPT_with_caveat", "ADOPT_shipped_only") for s in statuses):
        return "ADOPT"
    if any(s == "HOLD" for s in statuses):
        return "HOLD"
    return "NEEDS_MORE_DATA"


def overall_verdict(per_source: dict[str, str]) -> str:
    if all(v in ("ADOPT", "N/A_no_load_bearing") for v in per_source.values()):
        return "ADOPT"
    if any(v == "HOLD" for v in per_source.values()):
        return "HOLD"
    return "NEEDS_MORE_DATA"


def main() -> None:
    parser = argparse.ArgumentParser(description="Per-source calibration OOS verification")
    parser.add_argument("--source", choices=("artsy", "saatchi", "all"), default="all")
    parser.add_argument("--seeds", type=int, nargs="*", default=None)
    args = parser.parse_args()
    sources = VALID_SOURCES if args.source == "all" else (args.source,)
    seeds = tuple(args.seeds) if args.seeds else SPLIT_SEEDS

    cb_params, xgb_params = _load_tuned_params()

    per_source_results: dict[str, Any] = {}
    for source in sources:
        logger.info("=" * 70)
        logger.info("OOS verification: %s (seeds=%s)", source, seeds)
        logger.info("=" * 70)
        df = load_data()
        df = df[df["is_excluded_for_training"] == 0]
        df = df[df["source"] == source].reset_index(drop=True)
        n_total = len(df)
        fingerprint = _dataset_fingerprint(df)
        X, y, groups = prepare_features(df)
        is_krw = df["is_krw"].fillna(0).astype(int).to_numpy()
        target_market = np.where(is_krw == 1, "gallery", "online")
        cells_all = np.array([_cell_key(source, tm) for tm in target_market])
        y_price = np.exp(y)
        logger.info("source=%s rows=%d artists=%d fp=%s...",
                    source, n_total, df["artist_slug"].nunique(), fingerprint[:12])

        per_seed_results: dict[int, Any] = {}
        for seed in seeds:
            per_seed_results[seed] = reproduce_per_source_per_seed(
                source, seed, df, X, y, groups, cells_all, y_price, cb_params, xgb_params,
            )
        aggregate = aggregate_per_source(per_seed_results)
        per_source_results[source] = {
            "n_total": n_total,
            "fingerprint": fingerprint,
            "per_seed": per_seed_results,
            "aggregate_per_cell": aggregate,
            "source_verdict": per_source_verdict(aggregate),
        }

    overall = overall_verdict({s: per_source_results[s]["source_verdict"] for s in sources})

    output = {
        "version": "v1-source-conditional-oos",
        "split_seeds": list(seeds),
        "fold_seed": FOLD_SEED,
        "artifact_seed": ARTIFACT_SEED,
        "drift_threshold_log": round(DRIFT_THRESHOLD_LOG, 4),
        "small_cell_n_threshold": SMALL_CELL_N_THRESHOLD,
        "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
        "bootstrap_ci_pct": BOOTSTRAP_CI_PCT,
        "dataset_fingerprint": {s: per_source_results[s]["fingerprint"] for s in sources},
        "per_source": per_source_results,
        "per_source_verdict": {s: per_source_results[s]["source_verdict"] for s in sources},
        "overall_verdict": overall,
        "evaluated_at": datetime.now(UTC).isoformat(),
    }
    RESULTS_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    logger.info("[OK] Saved: %s", RESULTS_PATH.name)

    # Summary
    print("\n" + "=" * 70)
    print(f"OOS VERIFICATION SUMMARY (overall: {overall})")
    print("=" * 70)
    for source in sources:
        sv = per_source_results[source]["source_verdict"]
        print(f"\n  Source [{source}] verdict: {sv}")
        for path in ("cold", "warm"):
            for cell, data in per_source_results[source]["aggregate_per_cell"][path].items():
                if data["category"] != "load_bearing":
                    continue
                print(
                    f"    {path}/{cell}: {data['cell_adoption']:25s} | "
                    f"primary={data['primary_aggregate']:30s} "
                    f"secondary={data['secondary_aggregate']}"
                )
                print(f"      per-seed primary: {data['primary_decisions_per_seed']}")
                print(f"      per-seed secondary: {data['secondary_decisions_per_seed']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
