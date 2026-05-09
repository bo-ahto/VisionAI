"""N=15 HP Retuning cycle (decision-binding).

Prereg: docs/n15_hp_retuning_prereg_20260509.md (R3 LGTM 잠금)
코덱스 자문 R1-R3 LGTM.

Method (per prereg §2):
- Pre-compute baselines (default Ens@N=32 + default XGB@N=15) on full data 5-fold CV.
- Optuna TPE 50 trials with constraints_func (4 constraints aligned to Step 1/2 endpoints).
- Objective: minimize warm_cv_mdape (warm-pool 5-fold CV mean).
- Constraints: c1-c3 vs Ens@N=32 (Step 2 G1/G2/G3) + c4 vs default XGB@N=15 (Step 1).
- Best params = warm-min trial among constraint_violated=False.
- Validation: fresh seeds {23, 47, 71} multi-seed holdout / Step 1+2 evaluation.

Usage:
    python3 scripts/optuna_xgb_n15_retune.py
    python3 scripts/optuna_xgb_n15_retune.py --n-trials 30  # quick mode
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
HOLDOUT_DIR = REPO / "data" / "n15_hp_retune_holdout_20260509"
RESULTS_PATH = ARTIFACTS_DIR / "n15_hp_retune_validation_20260509.json"
STUDY_PATH = ARTIFACTS_DIR / "xgb_n15_retune_optuna_study.json"
BEST_PARAMS_PATH = ARTIFACTS_DIR / "xgb_n15_retuned_best_params.json"

VALIDATION_SEEDS = (23, 47, 71)
ARTIFACT_SEED = 42
N_TRIALS_DEFAULT = 50
CV_SEED = 42

N15_FEATURES = [
    "ln_area", "artist_total_works", "career_stage", "area_cm2",
    "ln_followers", "artist_birth_year", "ho_x_support", "has_seoul",
    "ho", "ho_power", "medium_category", "aspect_ratio",
    "ln_ho", "for_sale_ratio", "has_depth",
]
CAT_FEATURES_N15 = [f for f in CAT_FEATURES if f in N15_FEATURES]
CAT_FEATURES_N32 = list(CAT_FEATURES)


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


def _apply_label_maps(
    X: pd.DataFrame, label_maps: dict[str, dict[str, int]],
) -> pd.DataFrame:
    Xe = X.copy()
    for col, mapping in label_maps.items():
        if col in Xe.columns:
            unseen_idx = len(mapping)
            Xe[col] = Xe[col].map(mapping).fillna(unseen_idx).astype(float)
    return Xe


def _train_xgb(
    X_train: pd.DataFrame, y_train: np.ndarray, features: list[str],
    cat_features: list[str], xgb_params: dict, seed: int = ARTIFACT_SEED,
) -> tuple[xgb.Booster, dict[str, dict[str, int]]]:
    Xe, label_maps = _local_label_encode_xgb(X_train[features], cat_features)
    dtrain = xgb.DMatrix(Xe, label=y_train)
    xgb_p = {k: v for k, v in xgb_params.items() if k != "num_boost_round"}
    booster = xgb.train(
        params={**xgb_p, "objective": "reg:squarederror", "verbosity": 0, "seed": seed},
        dtrain=dtrain, num_boost_round=xgb_params.get("num_boost_round", 1000),
    )
    return booster, label_maps


def _predict_xgb(
    booster: xgb.Booster, label_maps: dict[str, dict[str, int]],
    X: pd.DataFrame, features: list[str],
) -> np.ndarray:
    Xe = _apply_label_maps(X[features], label_maps)
    return np.asarray(booster.predict(xgb.DMatrix(Xe)))


def _train_cb(
    X_train: pd.DataFrame, y_train: np.ndarray, features: list[str],
    cat_features: list[str], cb_params: dict, seed: int = ARTIFACT_SEED,
) -> CatBoostRegressor:
    cb = CatBoostRegressor(
        **cb_params, loss_function="RMSE", verbose=0,
        random_seed=seed, allow_writing_files=False,
    )
    cat_idx = [features.index(c) for c in cat_features if c in features]
    pool = Pool(X_train[features], label=y_train, cat_features=cat_idx)
    cb.fit(pool)
    return cb


def _predict_cb(
    cb: CatBoostRegressor, X: pd.DataFrame, features: list[str], cat_features: list[str],
) -> np.ndarray:
    cat_idx = [features.index(c) for c in cat_features if c in features]
    pool = Pool(X[features], cat_features=cat_idx)
    return np.asarray(cb.predict(pool))


def cv_xgb_warm_cold(
    X: pd.DataFrame, y: np.ndarray, source: np.ndarray, groups: np.ndarray, wmask: np.ndarray,
    features: list[str], cat_features: list[str], xgb_params: dict, n_splits: int = 5,
) -> dict[str, float]:
    """Run XGB CV: cold = GroupKFold-5(artist_slug) / warm = KFold-5 on warm-only subset.
    R4 fix (codex): cold path now uses GroupKFold (artist isolated) to match operational scale.
    Returns {warm_mdape, cold_mdape, cold_artsy, cold_saatchi}.
    """
    # Cold CV (full data / GroupKFold artist isolation)
    gkf = GroupKFold(n_splits=n_splits)
    cold_preds_ln = np.zeros(len(y))
    for tr, te in gkf.split(X, y, groups):
        booster, lm = _train_xgb(X.iloc[tr].reset_index(drop=True), y[tr], features, cat_features, xgb_params)
        cold_preds_ln[te] = _predict_xgb(booster, lm, X.iloc[te].reset_index(drop=True), features)
    y_price = np.exp(y)
    cold_pred = np.exp(cold_preds_ln)
    cold_mdape = _mdape(y_price, cold_pred)
    cold_artsy = _mdape(y_price[source == "artsy"], cold_pred[source == "artsy"])
    cold_saatchi = _mdape(y_price[source == "saatchi"], cold_pred[source == "saatchi"])

    # Warm CV (warm-only / KFold per e3367ed convention)
    warm_idx = np.where(wmask)[0]
    X_warm = X.iloc[warm_idx].reset_index(drop=True)
    y_warm = y[warm_idx]
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=CV_SEED)
    warm_preds_ln = np.zeros(len(y_warm))
    for tr, te in kf.split(X_warm):
        booster, lm = _train_xgb(X_warm.iloc[tr].reset_index(drop=True), y_warm[tr], features, cat_features, xgb_params)
        warm_preds_ln[te] = _predict_xgb(booster, lm, X_warm.iloc[te].reset_index(drop=True), features)
    warm_mdape = _mdape(np.exp(y_warm), np.exp(warm_preds_ln))

    return {
        "warm_mdape": float(warm_mdape),
        "cold_mdape": float(cold_mdape),
        "cold_artsy": float(cold_artsy),
        "cold_saatchi": float(cold_saatchi),
    }


def cv_ens_n32_cold(
    X: pd.DataFrame, y: np.ndarray, source: np.ndarray, groups: np.ndarray,
    cb_params: dict, xgb_params: dict, n_splits: int = 5,
) -> dict[str, float]:
    """Cold GroupKFold-5(artist_slug) for Ensemble@N=32 (CB+XGB)/2.
    R4 fix: GroupKFold artist isolation."""
    gkf = GroupKFold(n_splits=n_splits)
    cb_preds_ln = np.zeros(len(y))
    xgb_preds_ln = np.zeros(len(y))
    for tr, te in gkf.split(X, y, groups):
        Xtr = X.iloc[tr].reset_index(drop=True)
        Xte = X.iloc[te].reset_index(drop=True)
        cb = _train_cb(Xtr, y[tr], CB_FEATURES, CAT_FEATURES_N32, cb_params)
        cb_preds_ln[te] = _predict_cb(cb, Xte, CB_FEATURES, CAT_FEATURES_N32)
        booster, lm = _train_xgb(Xtr, y[tr], CB_FEATURES, CAT_FEATURES_N32, xgb_params)
        xgb_preds_ln[te] = _predict_xgb(booster, lm, Xte, CB_FEATURES)
    y_price = np.exp(y)
    ens_pred = (np.exp(cb_preds_ln) + np.exp(xgb_preds_ln)) / 2
    cold_mdape = _mdape(y_price, ens_pred)
    cold_artsy = _mdape(y_price[source == "artsy"], ens_pred[source == "artsy"])
    cold_saatchi = _mdape(y_price[source == "saatchi"], ens_pred[source == "saatchi"])
    return {
        "cold_mdape": float(cold_mdape),
        "cold_artsy": float(cold_artsy),
        "cold_saatchi": float(cold_saatchi),
    }


def make_objective_and_constraints(
    X: pd.DataFrame, y: np.ndarray, source: np.ndarray, groups: np.ndarray, wmask: np.ndarray,
    baseline_ens32: dict, baseline_xgb_n15_default: dict,
):
    def objective(trial: optuna.Trial) -> float:
        params = {
            "max_depth": trial.suggest_int("max_depth", 4, 10),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            "num_boost_round": trial.suggest_int("num_boost_round", 500, 4000),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 20),
            "gamma": trial.suggest_float("gamma", 0.0, 0.5),
            "reg_alpha": trial.suggest_float("reg_alpha", 0.0, 1.0),
            "reg_lambda": trial.suggest_float("reg_lambda", 0.0, 5.0),
        }
        metrics = cv_xgb_warm_cold(
            X, y, source, groups, wmask, N15_FEATURES, CAT_FEATURES_N15, params,
        )

        c1 = metrics["cold_mdape"] - baseline_ens32["cold_mdape"] - 0.5
        c2 = metrics["cold_artsy"] - baseline_ens32["cold_artsy"] - 0.8
        c3 = metrics["cold_saatchi"] - baseline_ens32["cold_saatchi"] - 1.0
        c4 = metrics["cold_mdape"] - baseline_xgb_n15_default["cold_mdape"] - 0.3
        constraints = [c1, c2, c3, c4]
        violated = any(c > 0 for c in constraints)

        trial.set_user_attr("warm_cv_mdape", metrics["warm_mdape"])
        trial.set_user_attr("cold_cv_mdape", metrics["cold_mdape"])
        trial.set_user_attr("cold_cv_artsy", metrics["cold_artsy"])
        trial.set_user_attr("cold_cv_saatchi", metrics["cold_saatchi"])
        trial.set_user_attr("constraints", constraints)
        trial.set_user_attr("constraint_violated", violated)

        return metrics["warm_mdape"]

    def constraints_func(trial: optuna.trial.FrozenTrial) -> list[float]:
        cs = trial.user_attrs.get("constraints")
        if cs is None:
            return [-1.0, -1.0, -1.0, -1.0]
        return list(cs)

    return objective, constraints_func


def validate_one_seed(
    seed: int, X: pd.DataFrame, y: np.ndarray, groups: np.ndarray, source: np.ndarray,
    cb_params: dict, xgb_params_default: dict, xgb_params_retuned: dict,
) -> dict[str, Any]:
    logger.info("--- validate seed=%d ---", seed)

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

    X_pool_cold_df = X.iloc[pool_cold].reset_index(drop=True)
    y_pool_cold = y[pool_cold]
    X_pool_warm_df = X.iloc[pool_warm].reset_index(drop=True)
    y_pool_warm = y[pool_warm]

    # Train all needed models on each pool
    cb_n32 = _train_cb(X_pool_cold_df, y_pool_cold, CB_FEATURES, CAT_FEATURES_N32, cb_params)
    xgb_n32_cold, lm_x32c = _train_xgb(X_pool_cold_df, y_pool_cold, CB_FEATURES, CAT_FEATURES_N32, xgb_params_default)
    xgb_n15_def_cold, lm_x15d_c = _train_xgb(X_pool_cold_df, y_pool_cold, N15_FEATURES, CAT_FEATURES_N15, xgb_params_default)
    xgb_n15_ret_cold, lm_x15r_c = _train_xgb(X_pool_cold_df, y_pool_cold, N15_FEATURES, CAT_FEATURES_N15, xgb_params_retuned)

    xgb_n32_warm, lm_x32w = _train_xgb(X_pool_warm_df, y_pool_warm, CB_FEATURES, CAT_FEATURES_N32, xgb_params_default)
    xgb_n15_def_warm, lm_x15d_w = _train_xgb(X_pool_warm_df, y_pool_warm, N15_FEATURES, CAT_FEATURES_N15, xgb_params_default)
    xgb_n15_ret_warm, lm_x15r_w = _train_xgb(X_pool_warm_df, y_pool_warm, N15_FEATURES, CAT_FEATURES_N15, xgb_params_retuned)

    # Predict
    X_hc = X.iloc[hold_cold].reset_index(drop=True)
    X_hw = X.iloc[hold_warm].reset_index(drop=True)
    y_p_cold = np.exp(y[hold_cold])
    y_p_warm = np.exp(y[hold_warm])
    src_cold = source[hold_cold]

    cb_p_cold = np.exp(_predict_cb(cb_n32, X_hc, CB_FEATURES, CAT_FEATURES_N32))
    xgb_n32_p_cold = np.exp(_predict_xgb(xgb_n32_cold, lm_x32c, X_hc, CB_FEATURES))
    xgb_n15_def_p_cold = np.exp(_predict_xgb(xgb_n15_def_cold, lm_x15d_c, X_hc, N15_FEATURES))
    xgb_n15_ret_p_cold = np.exp(_predict_xgb(xgb_n15_ret_cold, lm_x15r_c, X_hc, N15_FEATURES))
    ens_n32_p_cold = (cb_p_cold + xgb_n32_p_cold) / 2

    xgb_n32_p_warm = np.exp(_predict_xgb(xgb_n32_warm, lm_x32w, X_hw, CB_FEATURES))
    xgb_n15_def_p_warm = np.exp(_predict_xgb(xgb_n15_def_warm, lm_x15d_w, X_hw, N15_FEATURES))
    xgb_n15_ret_p_warm = np.exp(_predict_xgb(xgb_n15_ret_warm, lm_x15r_w, X_hw, N15_FEATURES))

    # Metrics
    artsy = src_cold == "artsy"
    saatchi = src_cold == "saatchi"

    def cold_mds(pred):
        return {
            "cold_overall_mdape": round(_mdape(y_p_cold, pred), 4),
            "cold_artsy_mdape": round(_mdape(y_p_cold[artsy], pred[artsy]), 4) if artsy.any() else None,
            "cold_saatchi_mdape": round(_mdape(y_p_cold[saatchi], pred[saatchi]), 4) if saatchi.any() else None,
        }

    metrics = {
        "ens_n32": cold_mds(ens_n32_p_cold),
        "xgb_n15_default": {**cold_mds(xgb_n15_def_p_cold),
                            "warm_mdape": round(_mdape(y_p_warm, xgb_n15_def_p_warm), 4)},
        "xgb_n15_retuned": {**cold_mds(xgb_n15_ret_p_cold),
                            "warm_mdape": round(_mdape(y_p_warm, xgb_n15_ret_p_warm), 4)},
        "xgb_n32": {"warm_mdape": round(_mdape(y_p_warm, xgb_n32_p_warm), 4)},
    }

    # Step 1: retuned vs default XGB@N=15
    delta_warm_step1 = metrics["xgb_n15_retuned"]["warm_mdape"] - metrics["xgb_n15_default"]["warm_mdape"]
    delta_cold_step1 = metrics["xgb_n15_retuned"]["cold_overall_mdape"] - metrics["xgb_n15_default"]["cold_overall_mdape"]

    # Step 2: retuned XGB@N=15 vs Ens@N=32 (cold) / vs XGB@N=32 (warm) — N15.A strong-adoption
    delta_cold_overall_step2 = metrics["xgb_n15_retuned"]["cold_overall_mdape"] - metrics["ens_n32"]["cold_overall_mdape"]
    delta_cold_artsy_step2 = (metrics["xgb_n15_retuned"]["cold_artsy_mdape"] or 0) - (metrics["ens_n32"]["cold_artsy_mdape"] or 0)
    delta_cold_saatchi_step2 = (metrics["xgb_n15_retuned"]["cold_saatchi_mdape"] or 0) - (metrics["ens_n32"]["cold_saatchi_mdape"] or 0)
    delta_warm_step2 = metrics["xgb_n15_retuned"]["warm_mdape"] - metrics["xgb_n32"]["warm_mdape"]

    # Step 1 verdict (R4 fix / G4-consistent)
    if delta_cold_step1 > 0.3 or delta_warm_step1 > 0.3:
        step1_verdict = "FAIL"
    elif delta_warm_step1 <= 0 and delta_cold_step1 <= 0.3:
        step1_verdict = "PASS"
    elif 0 < delta_warm_step1 <= 0.3 and delta_cold_step1 <= 0.3:
        step1_verdict = "INCONCLUSIVE"
    else:
        step1_verdict = "INCONCLUSIVE"

    # Step 2 verdict (N15.A strong + R4 warm rule fix)
    g_pass = (delta_cold_overall_step2 <= 0.5 and delta_cold_artsy_step2 <= 0.8
              and delta_cold_saatchi_step2 <= 1.0 and delta_warm_step2 <= 0.3)
    if not g_pass:
        step2_verdict = "FAIL"
    elif delta_cold_overall_step2 <= 0.5 and delta_warm_step2 <= 0:
        step2_verdict = "PASS"
    elif 0 < delta_warm_step2 <= 0.3 or 0.5 < delta_cold_overall_step2 <= 1.0:
        step2_verdict = "INCONCLUSIVE"
    else:
        step2_verdict = "INCONCLUSIVE"

    logger.info("  step1: Δ_cold=%+.3f / Δ_warm=%+.3f → %s",
                delta_cold_step1, delta_warm_step1, step1_verdict)
    logger.info("  step2: Δ_cold=%+.3f / Δ_artsy=%+.3f / Δ_saatchi=%+.3f / Δ_warm=%+.3f → %s",
                delta_cold_overall_step2, delta_cold_artsy_step2,
                delta_cold_saatchi_step2, delta_warm_step2, step2_verdict)

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
        "deltas_step1_retuned_vs_default_xgbn15": {
            "delta_cold_overall": round(delta_cold_step1, 4),
            "delta_warm": round(delta_warm_step1, 4),
        },
        "deltas_step2_retuned_vs_ens32": {
            "delta_cold_overall": round(delta_cold_overall_step2, 4),
            "delta_cold_artsy": round(delta_cold_artsy_step2, 4),
            "delta_cold_saatchi": round(delta_cold_saatchi_step2, 4),
            "delta_warm": round(delta_warm_step2, 4),
        },
        "step1_verdict": step1_verdict,
        "step2_verdict": step2_verdict,
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
    logger.info("N=15 HP Retuning cycle / n_trials=%d", args.n_trials)
    logger.info("=" * 70)

    cb_params, xgb_params_default = _load_tuned_params()

    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].reset_index(drop=True)
    fingerprint = _dataset_fingerprint(df)
    logger.info("rows=%d / artists=%d / fp=%s...", len(df), df["artist_slug"].nunique(), fingerprint[:12])
    X, y, groups = prepare_features(df)
    source = df["source"].astype(str).to_numpy()
    wmask = _warm_mask(groups)

    # Pre-compute baselines
    logger.info("Pre-computing baseline Ens@N=32 (5-fold CV cold) ...")
    t0 = time.time()
    baseline_ens32 = cv_ens_n32_cold(X, y, source, groups, cb_params, xgb_params_default)
    logger.info("  ens_n32 cold: %s (%.1fs)", baseline_ens32, time.time() - t0)

    logger.info("Pre-computing baseline default XGB@N=15 (5-fold CV warm + cold) ...")
    t0 = time.time()
    baseline_xgb_n15_default = cv_xgb_warm_cold(
        X, y, source, groups, wmask, N15_FEATURES, CAT_FEATURES_N15, xgb_params_default,
    )
    logger.info("  xgb_n15_default: %s (%.1fs)", baseline_xgb_n15_default, time.time() - t0)

    # Optuna study
    logger.info("Starting Optuna TPE study (%d trials) ...", args.n_trials)
    objective_fn, constraints_fn = make_objective_and_constraints(
        X, y, source, groups, wmask, baseline_ens32, baseline_xgb_n15_default,
    )
    sampler = optuna.samplers.TPESampler(seed=CV_SEED, constraints_func=constraints_fn)
    study = optuna.create_study(direction="minimize", sampler=sampler)
    t0 = time.time()
    study.optimize(objective_fn, n_trials=args.n_trials, show_progress_bar=False)
    elapsed = time.time() - t0
    logger.info("Study complete (%.1fs)", elapsed)

    # Best (constraint_violated == False, warm_cv_mdape min)
    valid = [t for t in study.trials if not t.user_attrs.get("constraint_violated", True)]
    if valid:
        best = min(valid, key=lambda t: t.user_attrs.get("warm_cv_mdape", float("inf")))
    else:
        logger.warning("No constraint-feasible trial / falling back to overall best")
        best = study.best_trial

    logger.info("Best params: %s", best.params)
    logger.info("Best warm_cv_mdape=%.4f (default=%.4f / Δ=%+.4f)",
                best.user_attrs.get("warm_cv_mdape"),
                baseline_xgb_n15_default["warm_mdape"],
                best.user_attrs.get("warm_cv_mdape") - baseline_xgb_n15_default["warm_mdape"])

    best_params_n15 = best.params  # raw search params

    # Save best params
    BEST_PARAMS_PATH.write_text(json.dumps({
        "version": "v1-xgb-n15-retuned",
        "model_target": "xgb_n15_warm_optimized",
        "frozen_n15_features": N15_FEATURES,
        "n_trials": args.n_trials,
        "n_constraint_feasible_trials": len(valid),
        "best_params": best_params_n15,
        "best_value_warm_mdape": best.user_attrs.get("warm_cv_mdape"),
        "best_cold_cv_mdape": best.user_attrs.get("cold_cv_mdape"),
        "best_cold_cv_artsy": best.user_attrs.get("cold_cv_artsy"),
        "best_cold_cv_saatchi": best.user_attrs.get("cold_cv_saatchi"),
        "baseline_ens32": baseline_ens32,
        "baseline_xgb_n15_default": baseline_xgb_n15_default,
        "search_seed": CV_SEED,
        "elapsed_sec": round(elapsed, 1),
        "evaluated_at": datetime.now(UTC).isoformat(),
    }, indent=2, ensure_ascii=False))
    logger.info("[OK] Saved best_params: %s", BEST_PARAMS_PATH.name)

    # Save full study trials
    STUDY_PATH.write_text(json.dumps([
        {
            "number": t.number,
            "params": t.params,
            "value": t.value,
            "user_attrs": {k: v for k, v in t.user_attrs.items()},
            "state": str(t.state),
        } for t in study.trials
    ], indent=2, ensure_ascii=False))
    logger.info("[OK] Saved study log: %s", STUDY_PATH.name)

    # Validation on fresh seeds
    logger.info("\n" + "=" * 70)
    logger.info("Validation on fresh seeds=%s", VALIDATION_SEEDS)
    logger.info("=" * 70)
    per_seed: dict[int, Any] = {}
    for seed in VALIDATION_SEEDS:
        per_seed[seed] = validate_one_seed(
            seed, X, y, groups, source, cb_params, xgb_params_default, best_params_n15,
        )

    aggregate_step1 = _aggregate([per_seed[s]["step1_verdict"] for s in VALIDATION_SEEDS])
    aggregate_step2 = _aggregate([per_seed[s]["step2_verdict"] for s in VALIDATION_SEEDS])

    if aggregate_step1 == "PASS" and aggregate_step2 == "PASS":
        overall = "ADOPT_retuned"
    elif aggregate_step1 == "PASS" and aggregate_step2 == "INCONCLUSIVE":
        overall = "RETUNED_EFFECTIVE_PROCEED_TO_N15C"
    elif aggregate_step1 == "FAIL":
        overall = "HOLD"
    else:
        overall = "NEEDS_MORE_DATA"

    output = {
        "version": "v1-n15-hp-retune-validation",
        "validation_seeds": list(VALIDATION_SEEDS),
        "n_trials_run": args.n_trials,
        "frozen_n15_features": N15_FEATURES,
        "best_params_retuned": best_params_n15,
        "default_xgb_params_n32": xgb_params_default,
        "baseline_ens32_cv": baseline_ens32,
        "baseline_xgb_n15_default_cv": baseline_xgb_n15_default,
        "best_warm_cv_mdape": best.user_attrs.get("warm_cv_mdape"),
        "dataset_fingerprint": fingerprint,
        "per_seed": per_seed,
        "aggregate": {
            "step1_retuned_vs_default_xgbn15": aggregate_step1,
            "step2_retuned_vs_ens32": aggregate_step2,
        },
        "overall_verdict": overall,
        "evaluated_at": datetime.now(UTC).isoformat(),
    }
    RESULTS_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    logger.info("[OK] Saved validation: %s", RESULTS_PATH.name)

    print("\n" + "=" * 70)
    print(f"N=15 HP RETUNE SUMMARY (overall: {overall})")
    print("=" * 70)
    print(f"  Step 1 (retuned vs default XGB@N=15): {aggregate_step1}")
    print(f"  Step 2 (retuned vs Ens@N=32):         {aggregate_step2}")
    print()
    for seed in VALIDATION_SEEDS:
        r = per_seed[seed]
        print(f"  seed={seed}:")
        print(f"    Step 1: {r['step1_verdict']:14s} | Δ_cold={r['deltas_step1_retuned_vs_default_xgbn15']['delta_cold_overall']:+.3f} | Δ_warm={r['deltas_step1_retuned_vs_default_xgbn15']['delta_warm']:+.3f}")
        print(f"    Step 2: {r['step2_verdict']:14s} | Δ_cold={r['deltas_step2_retuned_vs_ens32']['delta_cold_overall']:+.3f} | Δ_warm={r['deltas_step2_retuned_vs_ens32']['delta_warm']:+.3f}")
    print("=" * 70)


if __name__ == "__main__":
    main()
