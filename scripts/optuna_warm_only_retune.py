"""B: Warm-only path optimization — XGB Optuna with warm-only objective (no cold constraints).

Prereg: docs/b_warm_only_optimization_prereg_20260510.md (R1 LGTM)
코덱스 R1 LGTM (combined D3+B / single round).

Method:
- Cold path 동결 / XGB warm-only Optuna 50 trials
- Warm CV: KFold-5 on warm-mask filtered subset (e3367ed convention)
- Single objective: warm_cv_mdape minimization
- Single constraint: warm_cv ≤ default + 0.1pp (search-time loose / validation strict)
- enqueue_trial(default warm params)
- Validation: 5 fresh seeds {541, 619, 743, 829, 947} / strict Δ_warm ≤ 0

Usage:
    python3 scripts/optuna_warm_only_retune.py
    python3 scripts/optuna_warm_only_retune.py --n-trials 30
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
from sklearn.model_selection import KFold, train_test_split

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
HOLDOUT_DIR = REPO / "data" / "b_warm_holdout_20260510"
RESULTS_PATH = ARTIFACTS_DIR / "b_warm_validation.json"
BEST_PARAMS_PATH = ARTIFACTS_DIR / "warm_only_retuned_best_params.json"
STUDY_PATH = ARTIFACTS_DIR / "warm_only_optuna_study.json"

VALIDATION_SEEDS = (541, 619, 743, 829, 947)
ARTIFACT_SEED = 42
FOLD_SEED = 42
N_TRIALS_DEFAULT = 50


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


def cv_warm(X: pd.DataFrame, y: np.ndarray, wmask: np.ndarray, params: dict, n_splits: int = 5) -> float:
    """KFold-5 warm CV (warm-only subset)."""
    warm_idx = np.where(wmask)[0]
    X_warm = X.iloc[warm_idx].reset_index(drop=True)
    y_warm = y[warm_idx]
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=FOLD_SEED)
    preds_ln = np.zeros(len(y_warm))
    for tr, te in kf.split(X_warm):
        booster, lm = _train_xgb(X_warm.iloc[tr].reset_index(drop=True), y_warm[tr], params)
        preds_ln[te] = _predict_xgb(booster, lm, X_warm.iloc[te].reset_index(drop=True))
    return float(_mdape(np.exp(y_warm), np.exp(preds_ln)))


def make_objective(X: pd.DataFrame, y: np.ndarray, wmask: np.ndarray, baseline_warm: float):
    def objective(trial: optuna.Trial) -> float:
        params = {
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
        warm_mdape = cv_warm(X, y, wmask, params)
        c1 = warm_mdape - baseline_warm - 0.1
        violated = c1 > 0
        trial.set_user_attr("warm_cv_mdape", warm_mdape)
        trial.set_user_attr("constraints", [c1])
        trial.set_user_attr("constraint_violated", violated)
        return warm_mdape

    def constraints_fn(trial: optuna.trial.FrozenTrial) -> list[float]:
        cs = trial.user_attrs.get("constraints")
        return cs if cs else [-1.0]

    return objective, constraints_fn


def select_best(study: optuna.Study) -> optuna.trial.FrozenTrial:
    valid = [t for t in study.trials if not t.user_attrs.get("constraint_violated", True)]
    if not valid:
        logger.warning("No constraint-feasible trial / fallback to overall best")
        return study.best_trial
    return min(valid, key=lambda t: t.value if t.value is not None else float("inf"))


def validate_seed(
    seed: int, X: pd.DataFrame, y: np.ndarray, groups: np.ndarray,
    xgb_default: dict, xgb_retuned: dict,
) -> dict[str, Any]:
    logger.info("--- validate seed=%d ---", seed)
    wmask = _warm_mask(groups)
    warm_g = np.where(wmask)[0]
    pool_w_loc, hold_w_loc = train_test_split(
        np.arange(len(warm_g)), test_size=0.20, random_state=seed, shuffle=True,
    )
    pool_warm = warm_g[np.sort(pool_w_loc)]
    hold_warm = warm_g[np.sort(hold_w_loc)]

    Xpw = X.iloc[pool_warm].reset_index(drop=True)
    ypw = y[pool_warm]
    Xhw = X.iloc[hold_warm].reset_index(drop=True)
    yph = np.exp(y[hold_warm])

    booster_def, lm_def = _train_xgb(Xpw, ypw, xgb_default)
    booster_ret, lm_ret = _train_xgb(Xpw, ypw, xgb_retuned)

    pred_def = np.exp(_predict_xgb(booster_def, lm_def, Xhw))
    pred_ret = np.exp(_predict_xgb(booster_ret, lm_ret, Xhw))

    base_warm = _mdape(yph, pred_def)
    cand_warm = _mdape(yph, pred_ret)
    delta = round(cand_warm - base_warm, 4)

    if delta <= 0:
        verdict = "PASS"
    elif delta <= 0.1:
        verdict = "INCONCLUSIVE"
    else:
        verdict = "FAIL"

    logger.info("  Δ_warm=%+.3f / base=%.4f / retuned=%.4f → %s",
                delta, base_warm, cand_warm, verdict)

    HOLDOUT_DIR.mkdir(parents=True, exist_ok=True)
    (HOLDOUT_DIR / f"seed{seed}_holdout_indices.json").write_text(json.dumps({
        "split_seed": seed,
        "warm": {"pool_indices": pool_warm.tolist(), "holdout_indices": hold_warm.tolist()},
    }, indent=2))

    return {
        "n_pool_warm": int(len(pool_warm)), "n_holdout_warm": int(len(hold_warm)),
        "warm_default": round(base_warm, 4),
        "warm_retuned": round(cand_warm, 4),
        "delta_warm": delta,
        "verdict": verdict,
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
    parser.add_argument("--n-trials", type=int, default=N_TRIALS_DEFAULT)
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("B: Warm-only path optimization / n_trials=%d", args.n_trials)
    logger.info("=" * 70)

    _, xgb_default = _load_tuned_params()

    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].reset_index(drop=True)
    fingerprint = _dataset_fingerprint(df)
    logger.info("rows=%d / artists=%d", len(df), df["artist_slug"].nunique())
    X, y, groups = prepare_features(df)
    wmask = _warm_mask(groups)

    # Pre-compute baseline warm
    logger.info("Pre-compute baseline warm CV (default XGB)")
    t0 = time.time()
    baseline_warm = cv_warm(X, y, wmask, xgb_default)
    logger.info("  baseline_warm = %.4f (%.1fs)", baseline_warm, time.time() - t0)

    # Optuna study
    logger.info("Starting Optuna TPE study (%d trials / warm-only)", args.n_trials)
    obj, con = make_objective(X, y, wmask, baseline_warm)
    sampler = optuna.samplers.TPESampler(seed=FOLD_SEED, constraints_func=con)
    study = optuna.create_study(direction="minimize", sampler=sampler)
    xgb_default_for_enqueue = {k: v for k, v in xgb_default.items()
                               if k in ("num_boost_round", "max_depth", "learning_rate",
                                        "subsample", "colsample_bytree", "min_child_weight",
                                        "gamma", "reg_alpha", "reg_lambda")}
    if xgb_default_for_enqueue:
        try:
            study.enqueue_trial(xgb_default_for_enqueue)
            logger.info("  enqueued default XGB params")
        except Exception as e:
            logger.warning("  enqueue failed: %s", e)
    t0 = time.time()
    study.optimize(obj, n_trials=args.n_trials, show_progress_bar=False)
    elapsed = time.time() - t0
    logger.info("Study complete (%.1fs)", elapsed)

    best = select_best(study)
    xgb_retuned = best.params
    logger.info("  Best params: %s", xgb_retuned)
    logger.info("  Best warm_cv = %.4f (default %.4f / Δ=%+.4f)",
                best.user_attrs.get("warm_cv_mdape"),
                baseline_warm,
                best.user_attrs.get("warm_cv_mdape") - baseline_warm)

    BEST_PARAMS_PATH.write_text(json.dumps({
        "version": "v1-warm-only-retuned",
        "n_trials": args.n_trials,
        "xgb_default_warm": xgb_default,
        "xgb_retuned_warm": xgb_retuned,
        "baseline_warm_cv": baseline_warm,
        "best_warm_cv": best.user_attrs.get("warm_cv_mdape"),
        "search_seed": FOLD_SEED,
        "elapsed_sec": round(elapsed, 1),
        "evaluated_at": datetime.now(UTC).isoformat(),
    }, indent=2, ensure_ascii=False))
    logger.info("[OK] Saved best_params: %s", BEST_PARAMS_PATH.name)

    STUDY_PATH.write_text(json.dumps([
        {"number": t.number, "params": t.params, "value": t.value,
         "user_attrs": dict(t.user_attrs), "state": str(t.state)}
        for t in study.trials
    ], indent=2))
    logger.info("[OK] Saved study log")

    # Validation
    logger.info("=" * 60)
    logger.info("Validation on fresh seeds=%s", VALIDATION_SEEDS)
    logger.info("=" * 60)
    per_seed: dict[int, Any] = {}
    for seed in VALIDATION_SEEDS:
        per_seed[seed] = validate_seed(
            seed, X, y, groups, xgb_default, xgb_retuned,
        )

    aggregate = _aggregate([per_seed[s]["verdict"] for s in VALIDATION_SEEDS])

    if aggregate == "PASS":
        overall = "ADOPT_warm_retuned"
    elif aggregate == "PASS_with_caveat":
        overall = "ADOPT_canary_warm"
    elif aggregate == "FAIL":
        overall = "HOLD_warm_default"
    else:
        overall = "NEEDS_MORE_DATA"

    output = {
        "version": "v1-b-warm-validation",
        "validation_seeds": list(VALIDATION_SEEDS),
        "n_trials": args.n_trials,
        "xgb_default_warm": xgb_default,
        "xgb_retuned_warm": xgb_retuned,
        "baseline_warm_cv": baseline_warm,
        "best_warm_cv": best.user_attrs.get("warm_cv_mdape"),
        "dataset_fingerprint": fingerprint,
        "per_seed": per_seed,
        "aggregate": aggregate,
        "overall_verdict": overall,
        "evaluated_at": datetime.now(UTC).isoformat(),
    }
    RESULTS_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    logger.info("[OK] Saved validation: %s", RESULTS_PATH.name)

    print("\n" + "=" * 70)
    print(f"B WARM-ONLY RETUNE SUMMARY (overall: {overall})")
    print("=" * 70)
    print(f"  Best warm_cv = {best.user_attrs.get('warm_cv_mdape'):.4f} (default {baseline_warm:.4f})")
    print(f"  Validation aggregate: {aggregate}")
    for seed in VALIDATION_SEEDS:
        r = per_seed[seed]
        print(f"  seed={seed}: {r['verdict']:14s} | Δ_warm={r['delta_warm']:+.3f}")
    print("=" * 70)


if __name__ == "__main__":
    main()
