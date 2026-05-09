"""Per-source calibration reproducibility validation (Reprod cycle / decision-binding).

Prereg: docs/calibration_per_source_reproducibility_prereg_20260509.md
Codex 자문: 1차/2차/3차 LGTM (session 019e0bb1)

Method (Held-out 20% / dual-track):
- Holdout split: cold = GroupShuffleSplit(0.20, seed=31337) / warm = train_test_split(0.20, seed=31337)
- Refit (80% pool): cross-fit 5-fold OOF + per-cell guard (e3367ed 동일 절차)
- Holdout eval (Primary): PR1 artifact 그대로 prediction × original (e3367ed) factor → 운영 채택 결정
- Holdout eval (Secondary): refit factor → procedure 재현성 진단
- Paired bootstrap CI (small cell / n_holdout < 500)
- Cell 분류: load_bearing (original_factor != 1.0) / consistency_only (== 1.0)

Usage:
    python3 scripts/validate_per_source_calibration_reproducibility.py
    python3 scripts/validate_per_source_calibration_reproducibility.py --source artsy
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
HOLDOUT_DIR = REPO / "data" / "reproducibility_holdout_20260509"
RESULTS_PATH = ARTIFACTS_DIR / "calibration_reproducibility_20260509.json"

PREFIX = "source_conditional_v1"
SPLIT_SEED = 31337
FOLD_SEED = 42
DRIFT_THRESHOLD_LOG = float(np.log(1.3))
SMALL_CELL_N_THRESHOLD = 500
BOOTSTRAP_ITERATIONS = 1000
BOOTSTRAP_CI_PCT = 0.90
VALID_SOURCES = ("artsy", "saatchi")

ORIGINAL_FACTORS: dict[str, dict[str, dict[str, float]]] = {
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


def _load_pr1_catboost(source: str) -> CatBoostRegressor:
    cb = CatBoostRegressor()
    cb.load_model(str(ARTIFACTS_DIR / f"{PREFIX}_{source}_catboost.cbm"))
    return cb


def _load_pr1_xgboost(source: str) -> tuple[xgb.Booster, dict[str, dict[str, int]]]:
    booster = xgb.Booster()
    booster.load_model(str(ARTIFACTS_DIR / f"{PREFIX}_{source}_xgboost.json"))
    label_maps_path = ARTIFACTS_DIR / f"{PREFIX}_{source}_xgboost_label_maps.json"
    with label_maps_path.open(encoding="utf-8") as f:
        label_maps = json.load(f)
    return booster, label_maps


def _apply_label_maps(X: pd.DataFrame, label_maps: dict[str, dict[str, int]]) -> pd.DataFrame:
    Xe = X.copy()
    for col, mapping in label_maps.items():
        if col in Xe.columns:
            Xe[col] = Xe[col].astype(str).map(mapping).fillna(-1).astype(int)
    return Xe


def _cb_pool_for_predict(X: pd.DataFrame) -> Pool:
    cat_idx = [X.columns.get_loc(c) for c in CAT_FEATURES if c in X.columns]
    return Pool(X, cat_features=cat_idx)


def _cross_fit_warm_oof_on_subset(
    X_warm: pd.DataFrame,
    y_warm: np.ndarray,
    xgb_params: dict,
    n_splits: int = 5,
) -> tuple[np.ndarray, np.ndarray]:
    """Replicate _warm_oof_with_fold_id on already-warm-filtered subset (no internal warm_mask)."""
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=FOLD_SEED)
    n = len(y_warm)
    preds = np.zeros(n)
    fold_ids = np.full(n, -1, dtype=int)
    for fold, (tr, te) in enumerate(kf.split(X_warm)):
        logger.info("  [Warm refit fold %d/%d] train=%d test=%d", fold + 1, n_splits, len(tr), len(te))
        Xtr_e, Xte_e, _ = _label_encode_xgb(X_warm.iloc[tr], X_warm.iloc[te])
        dtrain = xgb.DMatrix(Xtr_e, label=y_warm[tr])
        dtest = xgb.DMatrix(Xte_e, label=y_warm[te])
        xgb_p = {k: v for k, v in xgb_params.items() if k != "num_boost_round"}
        m = xgb.train(
            params={**xgb_p, "objective": "reg:squarederror", "verbosity": 0, "seed": FOLD_SEED},
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
    """Per-cell guard. Returns (applied, cf_baseline, cf_unguarded)."""
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


def _paired_bootstrap_ci(
    y_true: np.ndarray,
    pred_baseline: np.ndarray,
    pred_calibrated: np.ndarray,
    n_iter: int,
    ci: float,
    seed: int,
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    n = len(y_true)
    deltas = np.empty(n_iter)
    for i in range(n_iter):
        idx = rng.integers(0, n, size=n)
        b = _mdape(y_true[idx], pred_baseline[idx])
        c = _mdape(y_true[idx], pred_calibrated[idx])
        deltas[i] = c - b
    alpha = (1 - ci) / 2
    return float(np.quantile(deltas, alpha)), float(np.quantile(deltas, 1 - alpha))


def _classify_decision(
    category: str,
    delta_original: float,
    drift: float,
    refit_factor: float,
    original_factor: float,
    ci_hi: float | None,
    cf_unguarded: float | None,
    cf_baseline: float | None,
) -> str:
    if category == "consistency_only":
        if cf_unguarded is None or cf_baseline is None:
            return "GUARD_OK"
        if cf_unguarded > cf_baseline and refit_factor != 1.0:
            return "GUARD_VIOLATION"
        return "GUARD_OK"
    # load_bearing
    if delta_original > 0:
        return "FAIL"
    if (refit_factor - 1.0) * (original_factor - 1.0) < 0:
        return "FAIL"
    drift_ok = drift <= DRIFT_THRESHOLD_LOG
    ci_ok = ci_hi is None or ci_hi <= 0
    return "PASS" if (drift_ok and ci_ok) else "INCONCLUSIVE"


def _per_cell_eval(
    path: str,
    y_h_price: np.ndarray,
    pred_h_price: np.ndarray,
    cells_h: np.ndarray,
    groups_h: np.ndarray,
    cells_pool: np.ndarray,
    groups_pool: np.ndarray,
    refit_applied: dict[str, float],
    original_factors: dict[str, float],
    cf_baseline: dict[str, float],
    cf_unguarded: dict[str, float],
) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    cell_set = sorted(set(cells_h.tolist()) | set(original_factors.keys()))
    for cell in cell_set:
        original = float(original_factors.get(cell, 1.0))
        refit = float(refit_applied.get(cell, 1.0))
        category = "load_bearing" if abs(original - 1.0) > 1e-9 else "consistency_only"
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
        }
        if n_h == 0:
            entry["decision"] = "GUARD_OK" if category == "consistency_only" else "FAIL"
            entry.update({
                "baseline_mdape": None,
                "calibrated_mdape_original": None,
                "calibrated_mdape_refit": None,
                "delta_original_pp": None,
                "delta_refit_pp": None,
                "factor_relative_drift": None,
                "bootstrap_computed": False,
                "paired_bootstrap_ci90_delta_original": None,
            })
            out[cell] = entry
            continue
        baseline = _mdape(y_h_price[m_h], pred_h_price[m_h])
        cal_orig = pred_h_price[m_h] * original
        cal_refit = pred_h_price[m_h] * refit
        cal_orig_mdape = _mdape(y_h_price[m_h], cal_orig)
        cal_refit_mdape = _mdape(y_h_price[m_h], cal_refit)
        delta_orig = cal_orig_mdape - baseline
        delta_refit = cal_refit_mdape - baseline
        drift = float(abs(np.log(refit / original))) if (original > 0 and refit > 0) else 0.0
        small_cell = n_h < SMALL_CELL_N_THRESHOLD
        ci: list[float] | None = None
        ci_hi: float | None = None
        if small_cell and category == "load_bearing":
            lo, hi = _paired_bootstrap_ci(
                y_h_price[m_h], pred_h_price[m_h], cal_orig,
                n_iter=BOOTSTRAP_ITERATIONS, ci=BOOTSTRAP_CI_PCT, seed=SPLIT_SEED,
            )
            ci = [round(lo, 4), round(hi, 4)]
            ci_hi = hi
        decision = _classify_decision(
            category=category,
            delta_original=delta_orig,
            drift=drift,
            refit_factor=refit,
            original_factor=original,
            ci_hi=ci_hi,
            cf_unguarded=cf_unguarded.get(cell),
            cf_baseline=cf_baseline.get(cell),
        )
        entry.update({
            "baseline_mdape": round(baseline, 4),
            "calibrated_mdape_original": round(cal_orig_mdape, 4),
            "calibrated_mdape_refit": round(cal_refit_mdape, 4),
            "delta_original_pp": round(delta_orig, 4),
            "delta_refit_pp": round(delta_refit, 4),
            "factor_relative_drift": round(drift, 4),
            "bootstrap_computed": ci is not None,
            "paired_bootstrap_ci90_delta_original": ci,
            "decision": decision,
        })
        out[cell] = entry
    return out


def reproduce_per_source(source: str) -> dict[str, Any]:
    if source not in VALID_SOURCES:
        raise ValueError(f"Invalid source: {source}")
    logger.info("=" * 70)
    logger.info("Reproducibility validation: %s", source)
    logger.info("=" * 70)

    df = load_data()
    df = df[df["is_excluded_for_training"] == 0]
    df = df[df["source"] == source].reset_index(drop=True)
    n_total = len(df)
    fingerprint = _dataset_fingerprint(df)
    logger.info("Source=%s rows=%d artists=%d fp=%s...",
                source, n_total, df["artist_slug"].nunique(), fingerprint[:12])

    X, y, groups = prepare_features(df)
    is_krw = df["is_krw"].fillna(0).astype(int).to_numpy()
    target_market = np.where(is_krw == 1, "gallery", "online")
    cells_all = np.array([_cell_key(source, tm) for tm in target_market])
    y_price = np.exp(y)

    # Cold holdout split
    gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=SPLIT_SEED)
    pool_cold, hold_cold = next(gss.split(X, y, groups))
    pool_cold = np.sort(pool_cold)
    hold_cold = np.sort(hold_cold)
    logger.info("Cold split: pool=%d / holdout=%d (artists pool=%d / holdout=%d)",
                len(pool_cold), len(hold_cold),
                pd.unique(groups[pool_cold]).size, pd.unique(groups[hold_cold]).size)

    # Warm holdout split (warm-filtered first, then row-level)
    wmask = _warm_mask(groups)
    warm_global = np.where(wmask)[0]
    warm_local = np.arange(len(warm_global))
    pool_warm_local, hold_warm_local = train_test_split(
        warm_local, test_size=0.20, random_state=SPLIT_SEED, shuffle=True,
    )
    pool_warm_local = np.sort(pool_warm_local)
    hold_warm_local = np.sort(hold_warm_local)
    pool_warm = warm_global[pool_warm_local]
    hold_warm = warm_global[hold_warm_local]
    logger.info("Warm split: pool=%d / holdout=%d", len(pool_warm), len(hold_warm))

    # Refit factors on 80% pool
    cb_params, xgb_params = _load_tuned_params()

    # Cold refit
    logger.info("--- Cold refit: cross-fit OOF on 80%% pool ---")
    X_pool_cold = X.iloc[pool_cold].reset_index(drop=True)
    y_pool_cold = y[pool_cold]
    groups_pool_cold = groups[pool_cold]
    cells_pool_cold = cells_all[pool_cold]
    cb_preds_pool_ln, fold_ids_cold = _cold_oof_with_fold_id(
        X_pool_cold, y_pool_cold, groups_pool_cold, cb_params,
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
    logger.info("Cold refit (guarded): %s", cold_refit_applied)

    # Warm refit
    logger.info("--- Warm refit: cross-fit OOF on 80%% warm pool ---")
    X_pool_warm = X.iloc[pool_warm].reset_index(drop=True)
    y_pool_warm = y[pool_warm]
    groups_pool_warm = groups[pool_warm]
    cells_pool_warm = cells_all[pool_warm]
    xgb_preds_pool_ln, fold_ids_warm = _cross_fit_warm_oof_on_subset(
        X_pool_warm, y_pool_warm, xgb_params,
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
    logger.info("Warm refit (guarded): %s", warm_refit_applied)

    # Holdout prediction with PR1 artifact (no retrain)
    logger.info("--- Holdout prediction (PR1 artifact / no retrain) ---")
    cb_artifact = _load_pr1_catboost(source)
    xgb_artifact, label_maps = _load_pr1_xgboost(source)

    X_hold_cold = X.iloc[hold_cold].reset_index(drop=True)
    cb_hold_pred_ln = cb_artifact.predict(_cb_pool_for_predict(X_hold_cold))
    cb_hold_pred_price = np.exp(cb_hold_pred_ln)

    X_hold_warm = X.iloc[hold_warm].reset_index(drop=True)
    X_hold_warm_e = _apply_label_maps(X_hold_warm, label_maps)
    xgb_hold_pred_ln = xgb_artifact.predict(xgb.DMatrix(X_hold_warm_e))
    xgb_hold_pred_price = np.exp(xgb_hold_pred_ln)

    # Per-cell holdout evaluation
    holdout_per_cell = {
        "cold": _per_cell_eval(
            "cold",
            y_price[hold_cold], cb_hold_pred_price, cells_all[hold_cold], groups[hold_cold],
            cells_pool_cold, groups_pool_cold,
            cold_refit_applied, ORIGINAL_FACTORS[source]["cold"],
            cf_b_cold, cf_u_cold,
        ),
        "warm": _per_cell_eval(
            "warm",
            y_price[hold_warm], xgb_hold_pred_price, cells_all[hold_warm], groups[hold_warm],
            cells_pool_warm, groups_pool_warm,
            warm_refit_applied, ORIGINAL_FACTORS[source]["warm"],
            cf_b_warm, cf_u_warm,
        ),
    }

    # Save holdout indices
    HOLDOUT_DIR.mkdir(parents=True, exist_ok=True)
    holdout_payload = {
        "source": source,
        "split_seed": SPLIT_SEED,
        "fingerprint": fingerprint,
        "cold": {
            "pool_indices": pool_cold.tolist(),
            "holdout_indices": hold_cold.tolist(),
        },
        "warm": {
            "pool_indices": pool_warm.tolist(),
            "holdout_indices": hold_warm.tolist(),
        },
    }
    (HOLDOUT_DIR / f"{source}_holdout_indices.json").write_text(
        json.dumps(holdout_payload, indent=2),
    )

    return {
        "n_total": n_total,
        "n_train_pool_cold": int(len(pool_cold)),
        "n_holdout_cold": int(len(hold_cold)),
        "n_artists_pool_cold": int(pd.unique(groups[pool_cold]).size),
        "n_artists_holdout_cold": int(pd.unique(groups[hold_cold]).size),
        "n_train_pool_warm": int(len(pool_warm)),
        "n_holdout_warm": int(len(hold_warm)),
        "fingerprint": fingerprint,
        "refit_factors": {"cold": cold_refit_applied, "warm": warm_refit_applied},
        "original_factors": ORIGINAL_FACTORS[source],
        "holdout_per_cell": holdout_per_cell,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Per-source calibration reproducibility")
    parser.add_argument("--source", choices=("artsy", "saatchi", "all"), default="all")
    args = parser.parse_args()
    sources = VALID_SOURCES if args.source == "all" else (args.source,)

    results: dict[str, Any] = {src: reproduce_per_source(src) for src in sources}

    output = {
        "version": "v1-source-conditional-reproducibility",
        "split_seed": SPLIT_SEED,
        "fold_seed": FOLD_SEED,
        "drift_threshold_log": round(DRIFT_THRESHOLD_LOG, 4),
        "small_cell_n_threshold": SMALL_CELL_N_THRESHOLD,
        "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
        "bootstrap_ci_pct": BOOTSTRAP_CI_PCT,
        "dataset_fingerprint": {src: results[src]["fingerprint"] for src in results},
        "per_source": results,
        "evaluated_at": datetime.now(UTC).isoformat(),
    }
    RESULTS_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    logger.info("[OK] Saved: %s", RESULTS_PATH.name)

    # Summary
    print("\n" + "=" * 70)
    print("REPRODUCIBILITY SUMMARY (load_bearing cells)")
    print("=" * 70)
    for src in sources:
        for path in ("cold", "warm"):
            for cell, e in results[src]["holdout_per_cell"][path].items():
                if e.get("category") != "load_bearing":
                    continue
                ci = e.get("paired_bootstrap_ci90_delta_original")
                ci_str = f"CI90=[{ci[0]:+.3f}, {ci[1]:+.3f}]" if ci else "CI=N/A"
                print(
                    f"  {src}/{path}/{cell}: decision={e['decision']:13s} | "
                    f"Δ_original={e['delta_original_pp']:+.3f}pp | "
                    f"refit={results[src]['refit_factors'][path].get(cell, 1.0):.4f} | "
                    f"drift={e['factor_relative_drift']:.4f} | {ci_str}"
                )
    print("=" * 70)
    print("CONSISTENCY_ONLY cells (guard 정합 점검):")
    for src in sources:
        for path in ("cold", "warm"):
            for cell, e in results[src]["holdout_per_cell"][path].items():
                if e.get("category") != "consistency_only":
                    continue
                print(f"  {src}/{path}/{cell}: decision={e['decision']} | n_holdout={e['n_holdout']}")


if __name__ == "__main__":
    main()
