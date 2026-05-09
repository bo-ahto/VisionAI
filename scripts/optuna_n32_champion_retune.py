"""D1: N=32 Champion HP Re-optimization (decision-binding).

Prereg: docs/d1_n32_champion_hp_reoptimization_prereg_20260510.md (R3 LGTM)
코덱스 R1-R3 LGTM (prereg locked).

Method (per prereg §2):
- Phase 1: CB Optuna search with XGB_default fixed → cold ensemble metric optimization.
- Phase 2: XGB Optuna search with CB_best_phase1 fixed → warm + cold ensemble guard.
- enqueue_trial(default_params) for both phases (incumbent first-class).
- Optuna constraints API (loose +0.1pp search-time / strict +0 validation).
- Validation: fresh seeds {97, 113, 199} / Step 1 = retuned vs default ensemble.

Usage:
    python3 scripts/optuna_n32_champion_retune.py
    python3 scripts/optuna_n32_champion_retune.py --n-trials 20  # quick mode
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
import optuna
import pandas as pd
import xgboost as xgb
from catboost import CatBoostRegressor, Pool
from sklearn.model_selection import GroupKFold, GroupShuffleSplit, KFold, train_test_split

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
optuna.logging.set_verbosity(optuna.logging.WARNING)

ARTIFACTS_DIR = REPO / "model_test_results"
HOLDOUT_DIR = REPO / "data" / "d1_holdout_20260510"
RESULTS_PATH = ARTIFACTS_DIR / "d1_validation_20260510.json"
BEST_PARAMS_PATH = ARTIFACTS_DIR / "n32_champion_retuned_best_params.json"
STUDY_CB_PATH = ARTIFACTS_DIR / "n32_champion_optuna_study_cb.json"
STUDY_XGB_PATH = ARTIFACTS_DIR / "n32_champion_optuna_study_xgb.json"

VALIDATION_SEEDS = (97, 113, 199)
ARTIFACT_SEED = 42
FOLD_SEED = 42
N_TRIALS_DEFAULT = 30


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


def _train_xgb(
    X: pd.DataFrame, y: np.ndarray, params: dict,
) -> tuple[xgb.Booster, dict[str, dict[str, int]]]:
    Xe, lm = _local_label_encode_xgb(X[CB_FEATURES], CAT_FEATURES)
    dtrain = xgb.DMatrix(Xe, label=y)
    xgb_p = {k: v for k, v in params.items() if k != "num_boost_round"}
    booster = xgb.train(
        params={**xgb_p, "objective": "reg:squarederror", "verbosity": 0,
                "seed": ARTIFACT_SEED},
        dtrain=dtrain, num_boost_round=params.get("num_boost_round", 1000),
    )
    return booster, lm


def _predict_xgb(
    booster: xgb.Booster, lm: dict, X: pd.DataFrame,
) -> np.ndarray:
    Xe = _apply_label_maps(X[CB_FEATURES], lm)
    return np.asarray(booster.predict(xgb.DMatrix(Xe)))


def _norm_cb_params(params: dict) -> dict:
    """Bernoulli bootstrap when subsample present + drop bagging_temperature (Bayesian only).
    R1 P2 (underspec avoid) + crash fix (CatBoost rejects bagging_temperature with Bernoulli).
    """
    p = dict(params)
    if "subsample" in p:
        p["bootstrap_type"] = "Bernoulli"
        p.pop("bagging_temperature", None)
    return p


def cv_cold_ensemble(
    X: pd.DataFrame, y: np.ndarray, source: np.ndarray, groups: np.ndarray,
    cb_params: dict, xgb_params: dict, n_splits: int = 5,
) -> dict[str, float]:
    """GroupKFold cold ensemble CV. Returns {cold_overall, cold_artsy, cold_saatchi}."""
    gkf = GroupKFold(n_splits=n_splits)
    cb_preds_ln = np.zeros(len(y))
    xgb_preds_ln = np.zeros(len(y))
    for tr, te in gkf.split(X, y, groups):
        Xtr = X.iloc[tr].reset_index(drop=True)
        Xte = X.iloc[te].reset_index(drop=True)
        cb = _train_cb(Xtr, y[tr], _norm_cb_params(cb_params))
        cb_preds_ln[te] = _predict_cb(cb, Xte)
        booster, lm = _train_xgb(Xtr, y[tr], xgb_params)
        xgb_preds_ln[te] = _predict_xgb(booster, lm, Xte)
    y_p = np.exp(y)
    ens = (np.exp(cb_preds_ln) + np.exp(xgb_preds_ln)) / 2
    return {
        "cold_overall": float(_mdape(y_p, ens)),
        "cold_artsy": float(_mdape(y_p[source == "artsy"], ens[source == "artsy"])),
        "cold_saatchi": float(_mdape(y_p[source == "saatchi"], ens[source == "saatchi"])),
    }


def cv_warm_xgb(
    X: pd.DataFrame, y: np.ndarray, wmask: np.ndarray, xgb_params: dict, n_splits: int = 5,
) -> float:
    """KFold warm-only XGBoost CV."""
    warm_idx = np.where(wmask)[0]
    X_warm = X.iloc[warm_idx].reset_index(drop=True)
    y_warm = y[warm_idx]
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=FOLD_SEED)
    preds_ln = np.zeros(len(y_warm))
    for tr, te in kf.split(X_warm):
        booster, lm = _train_xgb(
            X_warm.iloc[tr].reset_index(drop=True), y_warm[tr], xgb_params,
        )
        preds_ln[te] = _predict_xgb(booster, lm, X_warm.iloc[te].reset_index(drop=True))
    return float(_mdape(np.exp(y_warm), np.exp(preds_ln)))


def make_phase1_objective(
    X: pd.DataFrame, y: np.ndarray, source: np.ndarray, groups: np.ndarray,
    xgb_default: dict, baseline_ens: dict,
):
    """Phase 1: CB search with XGB_default fixed → cold ensemble metric."""
    def objective(trial: optuna.Trial) -> float:
        cb_params = {
            "iterations": trial.suggest_int("iterations", 500, 2000),
            "depth": trial.suggest_int("depth", 4, 10),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1.0, 10.0),
            "random_strength": trial.suggest_float("random_strength", 0.0, 5.0),
            "border_count": trial.suggest_int("border_count", 32, 255),
            "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        }
        m = cv_cold_ensemble(X, y, source, groups, cb_params, xgb_default)
        c1 = m["cold_overall"] - baseline_ens["cold_overall"] - 0.1
        c2 = m["cold_artsy"] - baseline_ens["cold_artsy"] - 0.4
        c3 = m["cold_saatchi"] - baseline_ens["cold_saatchi"] - 0.4
        violated = any(c > 0 for c in (c1, c2, c3))
        trial.set_user_attr("cold_overall", m["cold_overall"])
        trial.set_user_attr("cold_artsy", m["cold_artsy"])
        trial.set_user_attr("cold_saatchi", m["cold_saatchi"])
        trial.set_user_attr("constraints", [c1, c2, c3])
        trial.set_user_attr("constraint_violated", violated)
        return m["cold_overall"]

    def constraints_fn(trial: optuna.trial.FrozenTrial) -> list[float]:
        cs = trial.user_attrs.get("constraints")
        return cs if cs else [-1.0, -1.0, -1.0]

    return objective, constraints_fn


def make_phase2_objective(
    X: pd.DataFrame, y: np.ndarray, source: np.ndarray, groups: np.ndarray, wmask: np.ndarray,
    cb_best_phase1: dict, baseline_ens: dict, baseline_warm: float,
):
    """Phase 2: XGB search with CB_best_phase1 fixed → warm + cold sanity."""
    def objective(trial: optuna.Trial) -> float:
        xgb_params = {
            "num_boost_round": trial.suggest_int("num_boost_round", 500, 4000),
            "max_depth": trial.suggest_int("max_depth", 4, 10),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 20),
            "gamma": trial.suggest_float("gamma", 0.0, 0.5),
            "reg_alpha": trial.suggest_float("reg_alpha", 0.0, 1.0),
            "reg_lambda": trial.suggest_float("reg_lambda", 0.0, 5.0),
        }
        warm_m = cv_warm_xgb(X, y, wmask, xgb_params)
        cold_m = cv_cold_ensemble(X, y, source, groups, cb_best_phase1, xgb_params)
        c1 = warm_m - baseline_warm - 0.1
        c2 = cold_m["cold_overall"] - baseline_ens["cold_overall"] - 0.1
        c3 = cold_m["cold_artsy"] - baseline_ens["cold_artsy"] - 0.4
        c4 = cold_m["cold_saatchi"] - baseline_ens["cold_saatchi"] - 0.4
        violated = any(c > 0 for c in (c1, c2, c3, c4))
        trial.set_user_attr("warm_mdape", warm_m)
        trial.set_user_attr("cold_overall", cold_m["cold_overall"])
        trial.set_user_attr("cold_artsy", cold_m["cold_artsy"])
        trial.set_user_attr("cold_saatchi", cold_m["cold_saatchi"])
        trial.set_user_attr("constraints", [c1, c2, c3, c4])
        trial.set_user_attr("constraint_violated", violated)
        return warm_m

    def constraints_fn(trial: optuna.trial.FrozenTrial) -> list[float]:
        cs = trial.user_attrs.get("constraints")
        return cs if cs else [-1.0, -1.0, -1.0, -1.0]

    return objective, constraints_fn


def select_best(study: optuna.Study) -> optuna.trial.FrozenTrial:
    valid = [t for t in study.trials if not t.user_attrs.get("constraint_violated", True)]
    if not valid:
        logger.warning("No constraint-feasible trial / fallback to overall best")
        return study.best_trial
    return min(valid, key=lambda t: t.value if t.value is not None else float("inf"))


def validate_seed(
    seed: int, X: pd.DataFrame, y: np.ndarray, groups: np.ndarray, source: np.ndarray,
    cb_default: dict, xgb_default: dict, cb_retuned: dict, xgb_retuned: dict,
) -> dict[str, Any]:
    logger.info("--- validate seed=%d ---", seed)
    gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=seed)
    pool_cold, hold_cold = next(gss.split(X, y, groups))
    pool_cold = np.sort(pool_cold)
    hold_cold = np.sort(hold_cold)
    wmask = _warm_mask(groups)
    warm_g = np.where(wmask)[0]
    pool_w_loc, hold_w_loc = train_test_split(
        np.arange(len(warm_g)), test_size=0.20, random_state=seed, shuffle=True,
    )
    pool_warm = warm_g[np.sort(pool_w_loc)]
    hold_warm = warm_g[np.sort(hold_w_loc)]

    Xpc = X.iloc[pool_cold].reset_index(drop=True)
    ypc = y[pool_cold]
    Xpw = X.iloc[pool_warm].reset_index(drop=True)
    ypw = y[pool_warm]
    Xhc = X.iloc[hold_cold].reset_index(drop=True)
    Xhw = X.iloc[hold_warm].reset_index(drop=True)
    yph_c = np.exp(y[hold_cold])
    yph_w = np.exp(y[hold_warm])
    src_c = source[hold_cold]

    # Train both candidates on cold pool / warm pool
    cb_def = _train_cb(Xpc, ypc, _norm_cb_params(cb_default))
    cb_ret = _train_cb(Xpc, ypc, _norm_cb_params(cb_retuned))
    xgb_def_cold, lm_def_c = _train_xgb(Xpc, ypc, xgb_default)
    xgb_ret_cold, lm_ret_c = _train_xgb(Xpc, ypc, xgb_retuned)
    xgb_def_warm, lm_def_w = _train_xgb(Xpw, ypw, xgb_default)
    xgb_ret_warm, lm_ret_w = _train_xgb(Xpw, ypw, xgb_retuned)

    # Predict on holdout
    cb_def_p = np.exp(_predict_cb(cb_def, Xhc))
    cb_ret_p = np.exp(_predict_cb(cb_ret, Xhc))
    xgb_def_p_cold = np.exp(_predict_xgb(xgb_def_cold, lm_def_c, Xhc))
    xgb_ret_p_cold = np.exp(_predict_xgb(xgb_ret_cold, lm_ret_c, Xhc))
    xgb_def_p_warm = np.exp(_predict_xgb(xgb_def_warm, lm_def_w, Xhw))
    xgb_ret_p_warm = np.exp(_predict_xgb(xgb_ret_warm, lm_ret_w, Xhw))

    ens_def = (cb_def_p + xgb_def_p_cold) / 2
    ens_ret = (cb_ret_p + xgb_ret_p_cold) / 2

    artsy = src_c == "artsy"
    saatchi = src_c == "saatchi"
    metrics = {
        "ens_default": {
            "cold_overall": round(_mdape(yph_c, ens_def), 4),
            "cold_artsy": round(_mdape(yph_c[artsy], ens_def[artsy]), 4) if artsy.any() else None,
            "cold_saatchi": round(_mdape(yph_c[saatchi], ens_def[saatchi]), 4) if saatchi.any() else None,
        },
        "ens_retuned": {
            "cold_overall": round(_mdape(yph_c, ens_ret), 4),
            "cold_artsy": round(_mdape(yph_c[artsy], ens_ret[artsy]), 4) if artsy.any() else None,
            "cold_saatchi": round(_mdape(yph_c[saatchi], ens_ret[saatchi]), 4) if saatchi.any() else None,
        },
        "warm_default": round(_mdape(yph_w, xgb_def_p_warm), 4),
        "warm_retuned": round(_mdape(yph_w, xgb_ret_p_warm), 4),
    }

    deltas = {
        "delta_cold_overall": round(metrics["ens_retuned"]["cold_overall"]
                                     - metrics["ens_default"]["cold_overall"], 4),
        "delta_cold_artsy": round((metrics["ens_retuned"]["cold_artsy"] or 0)
                                   - (metrics["ens_default"]["cold_artsy"] or 0), 4),
        "delta_cold_saatchi": round((metrics["ens_retuned"]["cold_saatchi"] or 0)
                                     - (metrics["ens_default"]["cold_saatchi"] or 0), 4),
        "delta_warm": round(metrics["warm_retuned"] - metrics["warm_default"], 4),
    }

    # Per prereg §3.1 strict thresholds
    g1 = deltas["delta_cold_overall"] <= 0
    g2 = deltas["delta_cold_artsy"] <= 0.3
    g3 = deltas["delta_cold_saatchi"] <= 0.3
    g4 = deltas["delta_warm"] <= 0.1
    guards = {"G1": "PASS" if g1 else "FAIL",
              "G2": "PASS" if g2 else "FAIL",
              "G3": "PASS" if g3 else "FAIL",
              "G4": "PASS" if g4 else "FAIL"}
    if all(g for g in (g1, g2, g3, g4)) and deltas["delta_cold_overall"] <= 0:
        verdict = "PASS"
    elif all(g for g in (g1, g2, g3, g4)) and 0 < deltas["delta_cold_overall"] <= 0.3:
        verdict = "INCONCLUSIVE"
    else:
        verdict = "FAIL"

    logger.info("  Δ_cold=%+.3f / Δ_artsy=%+.3f / Δ_saatchi=%+.3f / Δ_warm=%+.3f → %s",
                deltas["delta_cold_overall"], deltas["delta_cold_artsy"],
                deltas["delta_cold_saatchi"], deltas["delta_warm"], verdict)

    HOLDOUT_DIR.mkdir(parents=True, exist_ok=True)
    (HOLDOUT_DIR / f"seed{seed}_holdout_indices.json").write_text(json.dumps({
        "split_seed": seed,
        "cold": {"pool_indices": pool_cold.tolist(), "holdout_indices": hold_cold.tolist()},
        "warm": {"pool_indices": pool_warm.tolist(), "holdout_indices": hold_warm.tolist()},
    }, indent=2))

    return {
        "n_pool_cold": int(len(pool_cold)),
        "n_holdout_cold": int(len(hold_cold)),
        "n_pool_warm": int(len(pool_warm)),
        "n_holdout_warm": int(len(hold_warm)),
        "metrics": metrics,
        "deltas": deltas,
        "guards": guards,
        "verdict": verdict,
    }


def _aggregate(per_seed_verdicts: list[str]) -> str:
    cnt = {v: per_seed_verdicts.count(v) for v in ("PASS", "INCONCLUSIVE", "FAIL")}
    if cnt["PASS"] == len(per_seed_verdicts):
        return "PASS"
    if cnt["FAIL"] >= 2:
        return "FAIL"
    return "INCONCLUSIVE"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-trials", type=int, default=N_TRIALS_DEFAULT)
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("D1: N=32 Champion HP Re-optimization / n_trials=%d per phase", args.n_trials)
    logger.info("=" * 70)

    cb_default, xgb_default = _load_tuned_params()

    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].reset_index(drop=True)
    fingerprint = _dataset_fingerprint(df)
    logger.info("rows=%d / artists=%d / fp=%s...",
                len(df), df["artist_slug"].nunique(), fingerprint[:12])
    X, y, groups = prepare_features(df)
    source = df["source"].astype(str).to_numpy()
    wmask = _warm_mask(groups)

    # Pre-compute baselines (default ensemble + default warm)
    logger.info("Pre-compute baseline ensemble (default CB + default XGB) ...")
    t0 = time.time()
    baseline_ens = cv_cold_ensemble(X, y, source, groups, cb_default, xgb_default)
    logger.info("  baseline_ens cold: %s (%.1fs)", baseline_ens, time.time() - t0)

    logger.info("Pre-compute baseline warm (default XGB) ...")
    t0 = time.time()
    baseline_warm = cv_warm_xgb(X, y, wmask, xgb_default)
    logger.info("  baseline_warm: %.4f (%.1fs)", baseline_warm, time.time() - t0)

    # Phase 1: CB search (XGB_default fixed)
    logger.info("=" * 60)
    logger.info("Phase 1: CB Optuna search (%d trials / XGB_default fixed)", args.n_trials)
    logger.info("=" * 60)
    p1_obj, p1_con = make_phase1_objective(X, y, source, groups, xgb_default, baseline_ens)
    sampler1 = optuna.samplers.TPESampler(seed=FOLD_SEED, constraints_func=p1_con)
    study1 = optuna.create_study(direction="minimize", sampler=sampler1)
    # Enqueue default CB params (R1 P2)
    cb_default_for_enqueue = {k: v for k, v in cb_default.items()
                              if k in ("iterations", "depth", "learning_rate", "l2_leaf_reg",
                                       "random_strength", "border_count", "subsample")}
    if cb_default_for_enqueue:
        try:
            study1.enqueue_trial(cb_default_for_enqueue)
            logger.info("  enqueued default CB params: %s", cb_default_for_enqueue)
        except Exception as e:
            logger.warning("  enqueue default CB failed: %s", e)
    t0 = time.time()
    study1.optimize(p1_obj, n_trials=args.n_trials, show_progress_bar=False)
    elapsed1 = time.time() - t0
    logger.info("Phase 1 complete (%.1fs)", elapsed1)
    best1 = select_best(study1)
    cb_best = best1.params
    logger.info("  CB best params: %s", cb_best)
    logger.info("  CB best cold_overall=%.4f (default=%.4f / Δ=%+.4f)",
                best1.user_attrs.get("cold_overall", 0),
                baseline_ens["cold_overall"],
                best1.user_attrs.get("cold_overall", 0) - baseline_ens["cold_overall"])

    STUDY_CB_PATH.write_text(json.dumps([
        {"number": t.number, "params": t.params, "value": t.value,
         "user_attrs": dict(t.user_attrs), "state": str(t.state)}
        for t in study1.trials
    ], indent=2))

    # Phase 2: XGB search (CB_best fixed)
    logger.info("=" * 60)
    logger.info("Phase 2: XGB Optuna search (%d trials / CB_best_phase1 fixed)", args.n_trials)
    logger.info("=" * 60)
    p2_obj, p2_con = make_phase2_objective(
        X, y, source, groups, wmask, cb_best, baseline_ens, baseline_warm,
    )
    sampler2 = optuna.samplers.TPESampler(seed=FOLD_SEED, constraints_func=p2_con)
    study2 = optuna.create_study(direction="minimize", sampler=sampler2)
    # Enqueue default XGB
    xgb_default_for_enqueue = {k: v for k, v in xgb_default.items()
                               if k in ("num_boost_round", "max_depth", "learning_rate",
                                        "subsample", "colsample_bytree", "min_child_weight",
                                        "gamma", "reg_alpha", "reg_lambda")}
    if xgb_default_for_enqueue:
        try:
            study2.enqueue_trial(xgb_default_for_enqueue)
            logger.info("  enqueued default XGB params: %s", xgb_default_for_enqueue)
        except Exception as e:
            logger.warning("  enqueue default XGB failed: %s", e)
    t0 = time.time()
    study2.optimize(p2_obj, n_trials=args.n_trials, show_progress_bar=False)
    elapsed2 = time.time() - t0
    logger.info("Phase 2 complete (%.1fs)", elapsed2)
    best2 = select_best(study2)
    xgb_best = best2.params
    logger.info("  XGB best params: %s", xgb_best)
    logger.info("  XGB best warm_mdape=%.4f (default=%.4f / Δ=%+.4f)",
                best2.user_attrs.get("warm_mdape", 0),
                baseline_warm,
                best2.user_attrs.get("warm_mdape", 0) - baseline_warm)

    STUDY_XGB_PATH.write_text(json.dumps([
        {"number": t.number, "params": t.params, "value": t.value,
         "user_attrs": dict(t.user_attrs), "state": str(t.state)}
        for t in study2.trials
    ], indent=2))

    # Save best params (commit 대상)
    BEST_PARAMS_PATH.write_text(json.dumps({
        "version": "v1-n32-champion-retuned",
        "n_trials_per_phase": args.n_trials,
        "cb_default": cb_default,
        "xgb_default": xgb_default,
        "cb_retuned": cb_best,
        "xgb_retuned": xgb_best,
        "baseline_ens_cv": baseline_ens,
        "baseline_warm_cv": baseline_warm,
        "phase1_best_cold_overall_cv": best1.user_attrs.get("cold_overall"),
        "phase1_best_cold_artsy_cv": best1.user_attrs.get("cold_artsy"),
        "phase1_best_cold_saatchi_cv": best1.user_attrs.get("cold_saatchi"),
        "phase2_best_warm_cv": best2.user_attrs.get("warm_mdape"),
        "phase2_best_cold_overall_cv": best2.user_attrs.get("cold_overall"),
        "search_seed": FOLD_SEED,
        "elapsed_phase1_sec": round(elapsed1, 1),
        "elapsed_phase2_sec": round(elapsed2, 1),
        "evaluated_at": datetime.now(UTC).isoformat(),
    }, indent=2, ensure_ascii=False))
    logger.info("[OK] Saved best_params: %s", BEST_PARAMS_PATH.name)

    # Validation on fresh seeds
    logger.info("=" * 60)
    logger.info("Validation on fresh seeds=%s", VALIDATION_SEEDS)
    logger.info("=" * 60)
    per_seed: dict[int, Any] = {}
    for seed in VALIDATION_SEEDS:
        per_seed[seed] = validate_seed(
            seed, X, y, groups, source,
            _norm_cb_params(cb_default), xgb_default,
            _norm_cb_params(cb_best), xgb_best,
        )

    aggregate = _aggregate([per_seed[s]["verdict"] for s in VALIDATION_SEEDS])

    if aggregate == "PASS":
        overall = "ADOPT_retuned_n32"
    elif aggregate == "FAIL":
        overall = "HOLD"
    else:
        overall = "NEEDS_MORE_DATA"

    output = {
        "version": "v1-d1-validation",
        "validation_seeds": list(VALIDATION_SEEDS),
        "n_trials_per_phase": args.n_trials,
        "cb_default": cb_default, "xgb_default": xgb_default,
        "cb_retuned": cb_best, "xgb_retuned": xgb_best,
        "baseline_ens_cv": baseline_ens,
        "baseline_warm_cv": baseline_warm,
        "dataset_fingerprint": fingerprint,
        "per_seed": per_seed,
        "aggregate": aggregate,
        "overall_verdict": overall,
        "evaluated_at": datetime.now(UTC).isoformat(),
    }
    RESULTS_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    logger.info("[OK] Saved validation: %s", RESULTS_PATH.name)

    print("\n" + "=" * 70)
    print(f"D1 N=32 CHAMPION RETUNE SUMMARY (overall: {overall})")
    print("=" * 70)
    print(f"  Phase 1 best cold_overall_cv: {best1.user_attrs.get('cold_overall'):.4f} (default={baseline_ens['cold_overall']:.4f})")
    print(f"  Phase 2 best warm_cv:         {best2.user_attrs.get('warm_mdape'):.4f} (default={baseline_warm:.4f})")
    print(f"  Validation aggregate: {aggregate}")
    for seed in VALIDATION_SEEDS:
        r = per_seed[seed]
        d = r["deltas"]
        print(f"  seed={seed}: {r['verdict']:14s} | Δ_cold={d['delta_cold_overall']:+.3f} | Δ_artsy={d['delta_cold_artsy']:+.3f} | Δ_saatchi={d['delta_cold_saatchi']:+.3f} | Δ_warm={d['delta_warm']:+.3f}")
    print("=" * 70)


if __name__ == "__main__":
    main()
