"""D3.B: Stacking meta-learner cycle (decision-binding).

Prereg: docs/d3_b_stacking_metalearner_prereg_20260510.md (R1+R2+R3+R4 LGTM)
연계: D3 scalar w (commit fd0f14e) HOLD_50_50 → advanced blend axis.

Method:
- Per-seed primary endpoint: GroupShuffleSplit(test=0.20) → 80% pool GroupKFold-5 OOF → meta fit on pool OOF → apply on 20% holdout
- Secondary frozen-meta gate: full-data OOF meta → fresh seed holdout 적용 / dual-gate adoption
- Linear regression with source dummy (옵션 A / R1 Q1 채택)
- Features: cb_oof_log, xgb_oof_log, source_dummy (artsy=1, saatchi=0), cb_xgb_diff
- 5 fresh seeds: {149, 211, 277, 353, 449}

Compute: ~15-20분 wall (per-seed pool OOF generation + meta fit + final retrain + holdout predict).

Usage:
    python3 scripts/d3_b_stacking_search.py
"""

from __future__ import annotations

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
from catboost import CatBoostRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import GroupKFold, GroupShuffleSplit

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from calibrate_source_bias import _load_tuned_params, _mdape  # type: ignore
from train_primary_market_v3_filtered import (  # type: ignore
    CAT_FEATURES,
    CB_FEATURES,
    _cb_pool,
    load_data,
    prepare_features,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ARTIFACTS_DIR = REPO / "model_test_results"
HOLDOUT_DIR = REPO / "data" / "d3_b_holdout_20260510"
RESULTS_PATH = ARTIFACTS_DIR / "d3_b_stacking_results.json"
STACKER_PATH = ARTIFACTS_DIR / "d3_b_stacker.json"

VALIDATION_SEEDS = (149, 211, 277, 353, 449)
FOLD_SEED = 42


def _dataset_fingerprint(df: pd.DataFrame) -> str:
    payload = df.sort_index(axis=1).to_csv(index=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _train_cb(X: pd.DataFrame, y: np.ndarray, params: dict) -> CatBoostRegressor:
    cb = CatBoostRegressor(
        **params, loss_function="RMSE", verbose=False, random_seed=42, allow_writing_files=False,
    )
    cb.fit(_cb_pool(X, y))
    return cb


def _predict_cb(cb: CatBoostRegressor, X: pd.DataFrame) -> np.ndarray:
    return np.asarray(cb.predict(X[CB_FEATURES]))


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


def _apply_label_maps(X: pd.DataFrame, lm: dict) -> pd.DataFrame:
    Xe = X.copy()
    for col, mapping in lm.items():
        if col in Xe.columns:
            unseen_idx = len(mapping)
            Xe[col] = Xe[col].map(mapping).fillna(unseen_idx).astype(float)
    return Xe


def _train_xgb(X: pd.DataFrame, y: np.ndarray, params: dict) -> tuple[xgb.Booster, dict]:
    Xe, lm = _local_label_encode_xgb(X[CB_FEATURES], CAT_FEATURES)
    dtrain = xgb.DMatrix(Xe, label=y)
    xgb_p = {k: v for k, v in params.items() if k != "num_boost_round"}
    booster = xgb.train(
        params={**xgb_p, "objective": "reg:squarederror", "verbosity": 0, "seed": 42},
        dtrain=dtrain, num_boost_round=params.get("num_boost_round", 1000),
    )
    return booster, lm


def _predict_xgb(booster: xgb.Booster, lm: dict, X: pd.DataFrame) -> np.ndarray:
    Xe = _apply_label_maps(X[CB_FEATURES], lm)
    return np.asarray(booster.predict(xgb.DMatrix(Xe)))


def _make_meta_features(cb_log: np.ndarray, xgb_log: np.ndarray, source: np.ndarray) -> np.ndarray:
    """Meta features (R1 Q2 / 4 features minimal)."""
    artsy_dummy = (source == "artsy").astype(int)
    cb_xgb_diff = cb_log - xgb_log
    return np.column_stack([cb_log, xgb_log, artsy_dummy, cb_xgb_diff])


def generate_pool_oof(
    X_pool: pd.DataFrame, y_pool: np.ndarray, groups_pool: np.ndarray,
    cb_params: dict, xgb_params: dict, n_splits: int = 5,
) -> tuple[np.ndarray, np.ndarray]:
    """80% pool 위 GroupKFold-5 OOF generation (D3 scalar w generator 정합)."""
    gkf = GroupKFold(n_splits=n_splits)
    cb_oof = np.zeros(len(y_pool))
    xgb_oof = np.zeros(len(y_pool))
    for fold_idx, (tr, te) in enumerate(gkf.split(X_pool, y_pool, groups_pool)):
        cb = _train_cb(X_pool.iloc[tr].reset_index(drop=True), y_pool[tr], cb_params)
        cb_oof[te] = _predict_cb(cb, X_pool.iloc[te].reset_index(drop=True))
        booster, lm = _train_xgb(X_pool.iloc[tr].reset_index(drop=True), y_pool[tr], xgb_params)
        xgb_oof[te] = _predict_xgb(booster, lm, X_pool.iloc[te].reset_index(drop=True))
    return cb_oof, xgb_oof


def validate_seed(
    seed: int,
    X: pd.DataFrame, y: np.ndarray, groups: np.ndarray, source: np.ndarray,
    cb_params: dict, xgb_params: dict,
    frozen_meta: LinearRegression,
) -> dict[str, Any]:
    logger.info("--- D3.B validate seed=%d ---", seed)

    # GroupShuffleSplit 80/20 (R2 P2 amendment)
    gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=seed)
    pool_idx, hold_idx = next(gss.split(X, y, groups))
    pool_idx = np.sort(pool_idx)
    hold_idx = np.sort(hold_idx)

    X_pool = X.iloc[pool_idx].reset_index(drop=True)
    y_pool = y[pool_idx]
    groups_pool = groups[pool_idx]
    source_pool = source[pool_idx]
    X_hold = X.iloc[hold_idx].reset_index(drop=True)
    y_hold = np.exp(y[hold_idx])
    source_hold = source[hold_idx]

    # 1. Pool OOF generation (per-seed primary endpoint)
    logger.info("  pool OOF generation (n=%d)...", len(y_pool))
    cb_pool_oof_log, xgb_pool_oof_log = generate_pool_oof(
        X_pool, y_pool, groups_pool, cb_params, xgb_params,
    )

    # 2. Per-seed meta fit on pool OOF
    X_meta_pool = _make_meta_features(cb_pool_oof_log, xgb_pool_oof_log, source_pool)
    meta_seed = LinearRegression(fit_intercept=True)
    meta_seed.fit(X_meta_pool, y_pool)

    # 3. Final retrain on full pool
    cb_final = _train_cb(X_pool, y_pool, cb_params)
    xgb_final, lm_final = _train_xgb(X_pool, y_pool, xgb_params)

    # 4. Holdout prediction
    cb_hold_log = _predict_cb(cb_final, X_hold)
    xgb_hold_log = _predict_xgb(xgb_final, lm_final, X_hold)
    X_meta_hold = _make_meta_features(cb_hold_log, xgb_hold_log, source_hold)

    # 5. Primary candidate: per-seed meta-learner prediction
    pred_primary_log = meta_seed.predict(X_meta_hold)
    pred_primary = np.exp(pred_primary_log)

    # 6. Secondary candidate: frozen full-data meta
    pred_secondary_log = frozen_meta.predict(X_meta_hold)
    pred_secondary = np.exp(pred_secondary_log)

    # 7. Baseline: 50/50 ensemble
    pred_baseline_log = (cb_hold_log + xgb_hold_log) / 2
    pred_baseline = np.exp(pred_baseline_log)

    # 8. Per-cell MdAPE / Δ
    artsy = source_hold == "artsy"
    saatchi = source_hold == "saatchi"

    def _per_cell(pred: np.ndarray) -> dict:
        return {
            "cold_overall": round(_mdape(y_hold, pred), 4),
            "cold_artsy": round(_mdape(y_hold[artsy], pred[artsy]), 4) if artsy.any() else None,
            "cold_saatchi": round(_mdape(y_hold[saatchi], pred[saatchi]), 4) if saatchi.any() else None,
        }

    metrics = {
        "baseline_50_50": _per_cell(pred_baseline),
        "primary_per_seed_meta": _per_cell(pred_primary),
        "secondary_frozen_meta": _per_cell(pred_secondary),
    }

    def _delta(cand: dict, base: dict) -> dict:
        return {
            "delta_cold_overall": round(cand["cold_overall"] - base["cold_overall"], 4),
            "delta_cold_artsy": round((cand["cold_artsy"] or 0) - (base["cold_artsy"] or 0), 4),
            "delta_cold_saatchi": round((cand["cold_saatchi"] or 0) - (base["cold_saatchi"] or 0), 4),
        }

    deltas_primary = _delta(metrics["primary_per_seed_meta"], metrics["baseline_50_50"])
    deltas_secondary = _delta(metrics["secondary_frozen_meta"], metrics["baseline_50_50"])

    def _verdict(d: dict) -> str:
        g1 = d["delta_cold_overall"] <= 0
        g2 = d["delta_cold_artsy"] <= 0.3
        g3 = d["delta_cold_saatchi"] <= 0.3
        if g1 and g2 and g3:
            return "PASS"
        if 0 < d["delta_cold_overall"] <= 0.3 and g2 and g3:
            return "INCONCLUSIVE"
        return "FAIL"

    primary_verdict = _verdict(deltas_primary)
    secondary_verdict = _verdict(deltas_secondary)

    logger.info("  primary: Δ=%+.3f / artsy=%+.3f / saatchi=%+.3f → %s",
                deltas_primary["delta_cold_overall"], deltas_primary["delta_cold_artsy"],
                deltas_primary["delta_cold_saatchi"], primary_verdict)
    logger.info("  secondary: Δ=%+.3f / artsy=%+.3f / saatchi=%+.3f → %s",
                deltas_secondary["delta_cold_overall"], deltas_secondary["delta_cold_artsy"],
                deltas_secondary["delta_cold_saatchi"], secondary_verdict)

    HOLDOUT_DIR.mkdir(parents=True, exist_ok=True)
    (HOLDOUT_DIR / f"seed{seed}_holdout_indices.json").write_text(json.dumps({
        "split_seed": seed,
        "pool_indices": pool_idx.tolist(),
        "holdout_indices": hold_idx.tolist(),
    }, indent=2))

    return {
        "n_pool": int(len(pool_idx)),
        "n_holdout": int(len(hold_idx)),
        "metrics": metrics,
        "deltas_primary": deltas_primary,
        "deltas_secondary": deltas_secondary,
        "primary_verdict": primary_verdict,
        "secondary_verdict": secondary_verdict,
        "meta_coef_primary": meta_seed.coef_.tolist(),
        "meta_intercept_primary": float(meta_seed.intercept_),
    }


def _aggregate_n5(verdicts: list[str]) -> str:
    n = len(verdicts)
    cnt = {v: verdicts.count(v) for v in ("PASS", "INCONCLUSIVE", "FAIL")}
    if cnt["PASS"] == n:
        return "PASS"
    if n >= 5 and cnt["PASS"] == n - 1 and cnt["INCONCLUSIVE"] == 1:
        return "PASS_with_caveat"
    if cnt["FAIL"] >= max(3, n - 2):
        return "FAIL"
    return "INCONCLUSIVE"


def main() -> None:
    logger.info("=" * 70)
    logger.info("D3.B: Stacking meta-learner cycle (per-seed refit + frozen secondary gate)")
    logger.info("=" * 70)

    # Default tuned params load
    cb_params, xgb_params = _load_tuned_params()
    logger.info("CB params: %s", cb_params)
    logger.info("XGB params: %s", xgb_params)

    # Data load
    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].reset_index(drop=True)
    fingerprint = _dataset_fingerprint(df)
    logger.info("rows=%d / artists=%d / fingerprint=%s...",
                len(df), df["artist_slug"].nunique(), fingerprint[:12])

    X, y, groups = prepare_features(df)
    source = df["source"].astype(str).to_numpy()

    # Frozen full-data OOF generation (secondary endpoint)
    logger.info("=" * 60)
    logger.info("Secondary endpoint: full-data OOF generation (GroupKFold-5)")
    logger.info("=" * 60)
    cb_full_oof_log = np.zeros(len(y))
    xgb_full_oof_log = np.zeros(len(y))
    gkf = GroupKFold(n_splits=5)
    for fold_idx, (tr, te) in enumerate(gkf.split(X, y, groups)):
        logger.info("  full OOF fold %d/5 (train=%d test=%d)", fold_idx + 1, len(tr), len(te))
        cb = _train_cb(X.iloc[tr].reset_index(drop=True), y[tr], cb_params)
        cb_full_oof_log[te] = _predict_cb(cb, X.iloc[te].reset_index(drop=True))
        booster, lm = _train_xgb(X.iloc[tr].reset_index(drop=True), y[tr], xgb_params)
        xgb_full_oof_log[te] = _predict_xgb(booster, lm, X.iloc[te].reset_index(drop=True))

    # Frozen meta-learner fit on full OOF
    X_meta_full = _make_meta_features(cb_full_oof_log, xgb_full_oof_log, source)
    frozen_meta = LinearRegression(fit_intercept=True)
    frozen_meta.fit(X_meta_full, y)
    logger.info("Frozen meta coef: %s / intercept: %.4f",
                frozen_meta.coef_.tolist(), frozen_meta.intercept_)

    # Save frozen meta
    STACKER_PATH.write_text(json.dumps({
        "version": "v1-frozen-fulldata-meta",
        "model": "LinearRegression",
        "features": ["cb_oof_log", "xgb_oof_log", "artsy_dummy", "cb_xgb_diff"],
        "coef": frozen_meta.coef_.tolist(),
        "intercept": float(frozen_meta.intercept_),
        "trained_on": f"full_data_OOF (n={len(y)} / GroupKFold-5)",
    }, indent=2, ensure_ascii=False))
    logger.info("[OK] Saved frozen meta: %s", STACKER_PATH.name)

    # Per-seed validation (primary endpoint)
    logger.info("=" * 60)
    logger.info("Primary endpoint: per-seed re-fit validation (seeds=%s)", VALIDATION_SEEDS)
    logger.info("=" * 60)

    HOLDOUT_DIR.mkdir(parents=True, exist_ok=True)
    per_seed: dict[int, Any] = {}
    for seed in VALIDATION_SEEDS:
        per_seed[seed] = validate_seed(
            seed, X, y, groups, source, cb_params, xgb_params, frozen_meta,
        )

    # Aggregate
    primary_verdicts = [per_seed[s]["primary_verdict"] for s in VALIDATION_SEEDS]
    secondary_verdicts = [per_seed[s]["secondary_verdict"] for s in VALIDATION_SEEDS]
    primary_aggregate = _aggregate_n5(primary_verdicts)
    secondary_aggregate = _aggregate_n5(secondary_verdicts)

    # Dual-gate decision (R2 P1 amendment)
    if primary_aggregate == "PASS" and secondary_aggregate != "FAIL":
        overall = "ADOPT_stacker"
    elif primary_aggregate == "PASS" and secondary_aggregate == "FAIL":
        overall = "INCONCLUSIVE_gap_analysis_needed"
    elif primary_aggregate == "PASS_with_caveat" and secondary_aggregate != "FAIL":
        overall = "ADOPT_canary_stacker"
    elif primary_aggregate == "FAIL":
        overall = "HOLD_50_50_blend_axis_terminate"
    else:
        overall = "NEEDS_MORE_DATA"

    output = {
        "version": "v1-d3-b-stacking",
        "validation_seeds": list(VALIDATION_SEEDS),
        "cb_params": cb_params,
        "xgb_params": xgb_params,
        "frozen_meta_coef": frozen_meta.coef_.tolist(),
        "frozen_meta_intercept": float(frozen_meta.intercept_),
        "dataset_fingerprint": fingerprint,
        "per_seed": per_seed,
        "primary_aggregate": primary_aggregate,
        "secondary_aggregate": secondary_aggregate,
        "overall_verdict": overall,
        "evaluated_at": datetime.now(UTC).isoformat(),
    }
    RESULTS_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    logger.info("[OK] Saved results: %s", RESULTS_PATH.name)

    # Summary
    print("\n" + "=" * 70)
    print(f"D3.B STACKING SUMMARY (overall: {overall})")
    print("=" * 70)
    print(f"  Primary aggregate (per-seed refit): {primary_aggregate}")
    print(f"  Secondary aggregate (frozen meta):  {secondary_aggregate}")
    print()
    for seed in VALIDATION_SEEDS:
        r = per_seed[seed]
        dp = r["deltas_primary"]
        ds = r["deltas_secondary"]
        print(f"  seed={seed:3d}: primary {r['primary_verdict']:14s} Δ={dp['delta_cold_overall']:+.3f} | "
              f"secondary {r['secondary_verdict']:14s} Δ={ds['delta_cold_overall']:+.3f}")
    print("=" * 70)


if __name__ == "__main__":
    main()
