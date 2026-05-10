"""D3: Ensemble Blend Refinement — 1D scalar w grid search on OOF + fresh holdout validation.

Prereg: docs/d3_ensemble_blend_refinement_prereg_20260510.md (R1 LGTM)
코덱스 R1 LGTM (combined D3+B / single round).

Method:
- OOF generation: GroupKFold-5(artist_slug) cold / KFold-5 warm (warm path 변경 X)
- Default base_params (운영 그대로 / D1 retune 별도)
- 21-point grid: w ∈ {0.0, 0.05, ..., 1.0}
- Best w* = constraint-feasible (artsy/saatchi non-regression vs 0.5) overall cold MdAPE 최소
- Validation: 5 fresh seeds {127, 233, 269, 311, 419}

Usage:
    python3 scripts/d3_blend_search.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import xgboost as xgb
from catboost import CatBoostRegressor, Pool
from sklearn.model_selection import GroupKFold, GroupShuffleSplit

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from calibrate_source_bias import _load_tuned_params, _mdape
from train_primary_market_v3_filtered import (
    CAT_FEATURES,
    CB_FEATURES,
    load_data,
    prepare_features,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ARTIFACTS_DIR = REPO / "model_test_results"
HOLDOUT_DIR = REPO / "data" / "d3_holdout_20260510"
RESULTS_PATH = ARTIFACTS_DIR / "d3_blend_search_results.json"
BEST_W_PATH = ARTIFACTS_DIR / "d3_blend_winner.json"

VALIDATION_SEEDS = (127, 233, 269, 311, 419)
ARTIFACT_SEED = 42
FOLD_SEED = 42
W_GRID = np.round(np.arange(0.0, 1.0001, 0.05), 4).tolist()  # 21-point grid


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


def _apply_label_maps(X: pd.DataFrame, lm: dict) -> pd.DataFrame:
    Xe = X.copy()
    for col, mapping in lm.items():
        if col in Xe.columns:
            unseen_idx = len(mapping)
            Xe[col] = Xe[col].map(mapping).fillna(unseen_idx).astype(float)
    return Xe


def _train_cb(X: pd.DataFrame, y: np.ndarray, params: dict) -> CatBoostRegressor:
    cat_idx = [CB_FEATURES.index(c) for c in CAT_FEATURES if c in CB_FEATURES]
    cb = CatBoostRegressor(
        **params, loss_function="RMSE", verbose=0,
        random_seed=ARTIFACT_SEED, allow_writing_files=False,
    )
    cb.fit(Pool(X[CB_FEATURES], label=y, cat_features=cat_idx))
    return cb


def _predict_cb(cb: CatBoostRegressor, X: pd.DataFrame) -> np.ndarray:
    cat_idx = [CB_FEATURES.index(c) for c in CAT_FEATURES if c in CB_FEATURES]
    return np.asarray(cb.predict(Pool(X[CB_FEATURES], cat_features=cat_idx)))


def _train_xgb(X: pd.DataFrame, y: np.ndarray, params: dict) -> tuple[xgb.Booster, dict]:
    Xe, lm = _local_label_encode_xgb(X[CB_FEATURES], CAT_FEATURES)
    dtrain = xgb.DMatrix(Xe, label=y)
    xgb_p = {k: v for k, v in params.items() if k != "num_boost_round"}
    booster = xgb.train(
        params={**xgb_p, "objective": "reg:squarederror", "verbosity": 0,
                "seed": ARTIFACT_SEED},
        dtrain=dtrain, num_boost_round=params.get("num_boost_round", 1000),
    )
    return booster, lm


def _predict_xgb(booster: xgb.Booster, lm: dict, X: pd.DataFrame) -> np.ndarray:
    Xe = _apply_label_maps(X[CB_FEATURES], lm)
    return np.asarray(booster.predict(xgb.DMatrix(Xe)))


def generate_cold_oof(
    X: pd.DataFrame, y: np.ndarray, groups: np.ndarray,
    cb_params: dict, xgb_params: dict, n_splits: int = 5,
) -> tuple[np.ndarray, np.ndarray]:
    """GroupKFold-5 cold OOF predictions for CB and XGB. Returns (cb_oof, xgb_oof) in price scale."""
    gkf = GroupKFold(n_splits=n_splits)
    cb_preds_ln = np.zeros(len(y))
    xgb_preds_ln = np.zeros(len(y))
    for fold, (tr, te) in enumerate(gkf.split(X, y, groups)):
        logger.info("  cold OOF fold %d/%d (train=%d test=%d)", fold + 1, n_splits, len(tr), len(te))
        Xtr = X.iloc[tr].reset_index(drop=True)
        Xte = X.iloc[te].reset_index(drop=True)
        cb = _train_cb(Xtr, y[tr], cb_params)
        cb_preds_ln[te] = _predict_cb(cb, Xte)
        booster, lm = _train_xgb(Xtr, y[tr], xgb_params)
        xgb_preds_ln[te] = _predict_xgb(booster, lm, Xte)
    return np.exp(cb_preds_ln), np.exp(xgb_preds_ln)


def grid_search_blend(
    y_price: np.ndarray, cb_oof: np.ndarray, xgb_oof: np.ndarray,
    source: np.ndarray, w_grid: list[float],
) -> tuple[float, dict[str, Any], list[dict]]:
    """1D scalar w grid search. Returns (best_w, best_metrics, all_w_records)."""
    # Baseline (50/50)
    base_ens = 0.5 * cb_oof + 0.5 * xgb_oof
    base_artsy = _mdape(y_price[source == "artsy"], base_ens[source == "artsy"])
    base_saatchi = _mdape(y_price[source == "saatchi"], base_ens[source == "saatchi"])
    logger.info("  baseline (w=0.5): cold_overall=%.4f / artsy=%.4f / saatchi=%.4f",
                _mdape(y_price, base_ens), base_artsy, base_saatchi)

    records = []
    for w in w_grid:
        ens = w * cb_oof + (1 - w) * xgb_oof
        cold_overall = _mdape(y_price, ens)
        cold_artsy = _mdape(y_price[source == "artsy"], ens[source == "artsy"])
        cold_saatchi = _mdape(y_price[source == "saatchi"], ens[source == "saatchi"])
        c2_violated = (cold_artsy - base_artsy) > 0.3
        c3_violated = (cold_saatchi - base_saatchi) > 0.3
        records.append({
            "w": float(w),
            "cold_overall": round(cold_overall, 4),
            "cold_artsy": round(cold_artsy, 4),
            "cold_saatchi": round(cold_saatchi, 4),
            "delta_artsy_vs_base": round(cold_artsy - base_artsy, 4),
            "delta_saatchi_vs_base": round(cold_saatchi - base_saatchi, 4),
            "c2_violated": c2_violated,
            "c3_violated": c3_violated,
            "constraint_violated": c2_violated or c3_violated,
        })

    # Best = constraint-feasible w with min cold_overall
    feasible = [r for r in records if not r["constraint_violated"]]
    if not feasible:
        logger.warning("No constraint-feasible w / fallback to w=0.5")
        best = next(r for r in records if r["w"] == 0.5)
    else:
        best = min(feasible, key=lambda r: r["cold_overall"])
    return best["w"], best, records


def _norm_cb_params(params: dict) -> dict:
    p = dict(params)
    if "subsample" in p:
        p["bootstrap_type"] = "Bernoulli"
        p.pop("bagging_temperature", None)
    return p


def validate_seed(
    seed: int, X: pd.DataFrame, y: np.ndarray, groups: np.ndarray, source: np.ndarray,
    cb_params: dict, xgb_params: dict, w_star: float,
) -> dict[str, Any]:
    logger.info("--- validate seed=%d ---", seed)
    gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=seed)
    pool_cold, hold_cold = next(gss.split(X, y, groups))
    pool_cold = np.sort(pool_cold)
    hold_cold = np.sort(hold_cold)

    Xpc = X.iloc[pool_cold].reset_index(drop=True)
    ypc = y[pool_cold]
    Xhc = X.iloc[hold_cold].reset_index(drop=True)
    yph = np.exp(y[hold_cold])
    src_h = source[hold_cold]

    cb = _train_cb(Xpc, ypc, _norm_cb_params(cb_params))
    booster, lm = _train_xgb(Xpc, ypc, xgb_params)
    cb_p = np.exp(_predict_cb(cb, Xhc))
    xgb_p = np.exp(_predict_xgb(booster, lm, Xhc))

    base_ens = 0.5 * cb_p + 0.5 * xgb_p
    cand_ens = w_star * cb_p + (1 - w_star) * xgb_p

    artsy = src_h == "artsy"
    saatchi = src_h == "saatchi"

    def ms(pred):
        return {
            "cold_overall": round(_mdape(yph, pred), 4),
            "cold_artsy": round(_mdape(yph[artsy], pred[artsy]), 4) if artsy.any() else None,
            "cold_saatchi": round(_mdape(yph[saatchi], pred[saatchi]), 4) if saatchi.any() else None,
        }

    base_m = ms(base_ens)
    cand_m = ms(cand_ens)
    deltas = {
        "delta_cold_overall": round(cand_m["cold_overall"] - base_m["cold_overall"], 4),
        "delta_cold_artsy": round((cand_m["cold_artsy"] or 0) - (base_m["cold_artsy"] or 0), 4),
        "delta_cold_saatchi": round((cand_m["cold_saatchi"] or 0) - (base_m["cold_saatchi"] or 0), 4),
    }
    g1 = deltas["delta_cold_overall"] <= 0
    g2 = deltas["delta_cold_artsy"] <= 0.3
    g3 = deltas["delta_cold_saatchi"] <= 0.3
    if all((g1, g2, g3)) and deltas["delta_cold_overall"] <= 0:
        verdict = "PASS"
    elif all((g1, g2, g3)) and 0 < deltas["delta_cold_overall"] <= 0.3:
        verdict = "INCONCLUSIVE"
    else:
        verdict = "FAIL"

    logger.info("  Δ_cold=%+.3f / Δ_artsy=%+.3f / Δ_saatchi=%+.3f → %s",
                deltas["delta_cold_overall"], deltas["delta_cold_artsy"],
                deltas["delta_cold_saatchi"], verdict)

    HOLDOUT_DIR.mkdir(parents=True, exist_ok=True)
    (HOLDOUT_DIR / f"seed{seed}_holdout_indices.json").write_text(json.dumps({
        "split_seed": seed, "w_star": w_star,
        "cold": {"pool_indices": pool_cold.tolist(), "holdout_indices": hold_cold.tolist()},
    }, indent=2))

    return {
        "n_pool": int(len(pool_cold)), "n_holdout": int(len(hold_cold)),
        "baseline": base_m, "candidate": cand_m,
        "deltas": deltas, "verdict": verdict,
    }


def _aggregate(per_seed: list[str]) -> str:
    n = len(per_seed)
    cnt = {v: per_seed.count(v) for v in ("PASS", "INCONCLUSIVE", "FAIL")}
    if cnt["PASS"] == n:
        return "PASS"
    if n >= 5 and cnt["PASS"] == n - 1 and cnt["INCONCLUSIVE"] == 1:
        return "PASS_with_caveat"
    if cnt["FAIL"] >= max(3, n - 2):
        return "FAIL"
    return "INCONCLUSIVE"


def main() -> None:
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("D3: Ensemble Blend Refinement (1D scalar w grid search)")
    logger.info("=" * 70)

    cb_params, xgb_params = _load_tuned_params()
    cb_params_norm = _norm_cb_params(cb_params)

    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].reset_index(drop=True)
    fingerprint = _dataset_fingerprint(df)
    logger.info("rows=%d / artists=%d", len(df), df["artist_slug"].nunique())
    X, y, groups = prepare_features(df)
    source = df["source"].astype(str).to_numpy()
    y_price = np.exp(y)

    # Generate cold OOF (default params)
    logger.info("Generate cold OOF (default params / GroupKFold-5)")
    t0 = time.time()
    cb_oof, xgb_oof = generate_cold_oof(X, y, groups, cb_params_norm, xgb_params)
    logger.info("Cold OOF generated (%.1fs)", time.time() - t0)

    # Grid search blend weight
    logger.info("=" * 60)
    logger.info("Grid search w ∈ %s", W_GRID[:5] + ['...'] + W_GRID[-3:])
    logger.info("=" * 60)
    w_star, best_record, all_records = grid_search_blend(y_price, cb_oof, xgb_oof, source, W_GRID)
    logger.info("Best w* = %.4f (cold_overall=%.4f)", w_star, best_record["cold_overall"])

    # Save best w
    BEST_W_PATH.write_text(json.dumps({
        "version": "v1-d3-blend-winner",
        "w_star": w_star,
        "w_grid": W_GRID,
        "best_record": best_record,
        "all_records": all_records,
        "default_baseline_w": 0.5,
        "evaluated_at": datetime.now(UTC).isoformat(),
    }, indent=2, ensure_ascii=False))
    logger.info("[OK] Saved blend winner: %s", BEST_W_PATH.name)

    # Validation
    logger.info("=" * 60)
    logger.info("Validation on fresh seeds=%s", VALIDATION_SEEDS)
    logger.info("=" * 60)
    per_seed: dict[int, Any] = {}
    for seed in VALIDATION_SEEDS:
        per_seed[seed] = validate_seed(
            seed, X, y, groups, source, cb_params, xgb_params, w_star,
        )

    aggregate = _aggregate([per_seed[s]["verdict"] for s in VALIDATION_SEEDS])

    if aggregate == "PASS":
        overall = "ADOPT_blend_w_star"
    elif aggregate == "PASS_with_caveat":
        overall = "ADOPT_canary_blend"
    elif aggregate == "FAIL":
        overall = "HOLD_50_50"
    else:
        overall = "NEEDS_MORE_DATA"

    output = {
        "version": "v1-d3-validation",
        "validation_seeds": list(VALIDATION_SEEDS),
        "w_grid": W_GRID,
        "w_star": w_star,
        "best_record_oof": best_record,
        "default_baseline_w": 0.5,
        "dataset_fingerprint": fingerprint,
        "per_seed": per_seed,
        "aggregate": aggregate,
        "overall_verdict": overall,
        "evaluated_at": datetime.now(UTC).isoformat(),
    }
    RESULTS_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    logger.info("[OK] Saved validation: %s", RESULTS_PATH.name)

    print("\n" + "=" * 70)
    print(f"D3 BLEND REFINEMENT SUMMARY (overall: {overall})")
    print("=" * 70)
    print(f"  Best w* = {w_star:.4f} (vs default 0.5)")
    print(f"  OOF cold_overall: {best_record['cold_overall']:.4f}")
    print(f"  Validation aggregate: {aggregate}")
    for seed in VALIDATION_SEEDS:
        r = per_seed[seed]
        d = r["deltas"]
        print(f"  seed={seed}: {r['verdict']:14s} | Δ_cold={d['delta_cold_overall']:+.3f} | "
              f"Δ_artsy={d['delta_cold_artsy']:+.3f} | Δ_saatchi={d['delta_cold_saatchi']:+.3f}")
    print("=" * 70)


if __name__ == "__main__":
    main()
