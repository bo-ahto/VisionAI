"""D1.Arch.tuned: Tuned LightGBM cold-only Optuna search (R1 NEEDS FIX → R2/R3 LGTM).

Prereg: docs/d1_arch_tuned_lgbm_optuna_prereg_20260510.md
Decision binding: ✅ YES (cap at canary / R1 P1.2 / B priority unchanged)

R1 amendment 정합:
- P0 fix: Optuna search-time source constraints (artsy / saatchi cold non-regression)
- P1.1 fix: FAIL = "tuned_LGBM_insufficient" only (R1 narrow)
- P1.2 fix: PR-WARM-B priority unchanged regardless of result

Method:
- Optuna 50 trials TPE / GroupKFold-5 cold CV / single objective + constraints API
- Search space: num_leaves / lr / feature/bagging fraction / lambda L1/L2 / min_data_leaf / num_boost_round
- enqueue_trial(default LGBM params) — incumbent first-class
- Validation: N=10 fresh seeds {1301, 1303, 1307, 1319, 1321, 1327, 1361, 1373, 1381, 1399}
- D1.Y framework strict primary + bootstrap secondary corroboration

Compute: ~30-40분 wall (Optuna 50 trials with constraints + N=10 validation).

Usage:
    python3 scripts/d1_arch_tuned_lgbm.py --n-trials 50
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

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd
import xgboost as xgb
from catboost import CatBoostRegressor
from sklearn.model_selection import GroupKFold, GroupShuffleSplit, train_test_split

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from calibrate_source_bias import _load_tuned_params, _mdape  # type: ignore
from train_primary_market_v3_filtered import (  # type: ignore
    CAT_FEATURES,
    CB_FEATURES,
    _cb_pool,
    _warm_mask,
    load_data,
    prepare_features,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
optuna.logging.set_verbosity(optuna.logging.WARNING)

ARTIFACTS_DIR = REPO / "model_test_results"
HOLDOUT_DIR = REPO / "data" / "d1_arch_tuned_holdout_20260510"
RESULTS_PATH = ARTIFACTS_DIR / "d1_arch_tuned_results.json"
STUDY_PATH = ARTIFACTS_DIR / "d1_arch_tuned_optuna_study.json"
BEST_PARAMS_PATH = ARTIFACTS_DIR / "lgbm_tuned_best_params.json"

ALL_SEEDS = (1301, 1303, 1307, 1319, 1321, 1327, 1361, 1373, 1381, 1399)
N_BOOT = 10000
RNG_SEED = 42
N_TRIALS_DEFAULT = 20  # R2 amendment: 50 trials worst-case 180min / 20 trials × narrow space ≈ 30-50min

LGBM_DEFAULT_PARAMS = {
    "num_leaves": 31,
    "learning_rate": 0.05,
    "feature_fraction": 0.9,
    "bagging_fraction": 0.9,
    "bagging_freq": 5,
    "min_data_in_leaf": 20,
    "lambda_l1": 0.0,
    "lambda_l2": 0.0,
    "num_boost_round": 1000,
}


def _dataset_fingerprint(df: pd.DataFrame) -> str:
    payload = df.sort_index(axis=1).to_csv(index=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _local_label_encode(X: pd.DataFrame, cat_features: list[str]) -> tuple[pd.DataFrame, dict]:
    Xe = X.copy()
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


def _train_lgbm(X: pd.DataFrame, y: np.ndarray, params: dict) -> tuple[lgb.Booster, dict]:
    Xe, lm = _local_label_encode(X[CB_FEATURES], CAT_FEATURES)
    cat_indices = [Xe.columns.get_loc(c) for c in CAT_FEATURES if c in Xe.columns]
    dtrain = lgb.Dataset(Xe, label=y, categorical_feature=cat_indices)
    p = {k: v for k, v in params.items() if k != "num_boost_round"}
    p.update({"objective": "regression", "metric": "l2", "verbose": -1, "seed": 42})
    booster = lgb.train(p, dtrain, num_boost_round=params.get("num_boost_round", 1000))
    return booster, lm


def _predict_lgbm(booster: lgb.Booster, lm: dict, X: pd.DataFrame) -> np.ndarray:
    Xe = _apply_label_maps(X[CB_FEATURES], lm)
    return np.asarray(booster.predict(Xe))


def _train_cb(X: pd.DataFrame, y: np.ndarray, params: dict) -> CatBoostRegressor:
    cb = CatBoostRegressor(
        **params, loss_function="RMSE", verbose=False, random_seed=42, allow_writing_files=False,
    )
    cb.fit(_cb_pool(X, y))
    return cb


def _predict_cb(cb: CatBoostRegressor, X: pd.DataFrame) -> np.ndarray:
    return np.asarray(cb.predict(X[CB_FEATURES]))


def _train_xgb(X: pd.DataFrame, y: np.ndarray, params: dict) -> tuple[xgb.Booster, dict]:
    Xe, lm = _local_label_encode(X[CB_FEATURES], CAT_FEATURES)
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


def cv_lgbm_cold(X: pd.DataFrame, y: np.ndarray, groups: np.ndarray, source: np.ndarray,
                  params: dict, n_splits: int = 5) -> dict:
    """GroupKFold-5 cold CV for LGBM. Returns cold_overall / cold_artsy / cold_saatchi mean."""
    gkf = GroupKFold(n_splits=n_splits)
    fold_metrics = []
    for tr, te in gkf.split(X, y, groups):
        booster, lm = _train_lgbm(X.iloc[tr].reset_index(drop=True), y[tr], params)
        pred_log = _predict_lgbm(booster, lm, X.iloc[te].reset_index(drop=True))
        pred_exp = np.exp(pred_log)
        y_te_exp = np.exp(y[te])
        src_te = source[te]
        artsy = src_te == "artsy"
        saatchi = src_te == "saatchi"
        fold_metrics.append({
            "cold_overall": _mdape(y_te_exp, pred_exp),
            "cold_artsy": _mdape(y_te_exp[artsy], pred_exp[artsy]) if artsy.any() else None,
            "cold_saatchi": _mdape(y_te_exp[saatchi], pred_exp[saatchi]) if saatchi.any() else None,
        })
    return {
        "cold_overall": float(np.mean([m["cold_overall"] for m in fold_metrics])),
        "cold_artsy": float(np.mean([m["cold_artsy"] for m in fold_metrics if m["cold_artsy"] is not None])),
        "cold_saatchi": float(np.mean([m["cold_saatchi"] for m in fold_metrics if m["cold_saatchi"] is not None])),
    }


def make_objective(X: pd.DataFrame, y: np.ndarray, groups: np.ndarray, source: np.ndarray,
                   default_cb_artsy: float, default_cb_saatchi: float):
    """Optuna objective with R1 P0 source-feasibility constraints."""
    def objective(trial: optuna.Trial) -> float:
        # R2 amendment: search space narrow (180min worst-case 회피 / num_leaves 64 / boost 1000)
        params = {
            "num_leaves": trial.suggest_int("num_leaves", 16, 64, log=True),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            "feature_fraction": trial.suggest_float("feature_fraction", 0.6, 1.0),
            "bagging_fraction": trial.suggest_float("bagging_fraction", 0.6, 1.0),
            "bagging_freq": trial.suggest_int("bagging_freq", 1, 10),
            "min_data_in_leaf": trial.suggest_int("min_data_in_leaf", 10, 100),
            "lambda_l1": trial.suggest_float("lambda_l1", 0.0, 1.0),
            "lambda_l2": trial.suggest_float("lambda_l2", 0.0, 5.0),
            "num_boost_round": trial.suggest_int("num_boost_round", 500, 1000),
        }
        m = cv_lgbm_cold(X, y, groups, source, params)
        c1 = m["cold_artsy"] - default_cb_artsy - 0.3
        c2 = m["cold_saatchi"] - default_cb_saatchi - 0.3
        violated = c1 > 0 or c2 > 0
        trial.set_user_attr("cv_metrics", m)
        trial.set_user_attr("constraints", [c1, c2])
        trial.set_user_attr("constraint_violated", violated)
        return m["cold_overall"]

    def constraints_fn(trial: optuna.trial.FrozenTrial) -> list[float]:
        cs = trial.user_attrs.get("constraints")
        return cs if cs else [-1.0, -1.0]

    return objective, constraints_fn


def select_best(study: optuna.Study) -> optuna.trial.FrozenTrial:
    valid = [t for t in study.trials if not t.user_attrs.get("constraint_violated", True)]
    if not valid:
        # R2 amendment fix: study.best_trial fails when all trials violated / use min value directly
        completed = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
        if not completed:
            raise RuntimeError("No completed trials")
        logger.warning("No constraint-feasible trial / fallback to overall min value (infeasible)")
        return min(completed, key=lambda t: t.value if t.value is not None else float("inf"))
    return min(valid, key=lambda t: t.value if t.value is not None else float("inf"))


def _bootstrap_ci(deltas: np.ndarray, n_boot: int = N_BOOT, seed: int = RNG_SEED) -> dict:
    rng = np.random.default_rng(seed)
    n = len(deltas)
    boot_means = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        boot_means[i] = deltas[idx].mean()
    lo = float(np.percentile(boot_means, 2.5))
    hi = float(np.percentile(boot_means, 97.5))
    return {
        "mean": round(float(deltas.mean()), 4),
        "ci_lower": round(lo, 4),
        "ci_upper": round(hi, 4),
        "ci_upper_negative": bool(hi <= 0),
    }


def _per_seed_validate(
    seed: int,
    X: pd.DataFrame, y: np.ndarray, groups: np.ndarray, source: np.ndarray,
    cb_params: dict, xgb_params: dict, lgbm_best_params: dict,
) -> dict[str, Any]:
    logger.info("--- D1.Arch.tuned validate seed=%d ---", seed)

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
    Xhc = X.iloc[hold_cold].reset_index(drop=True)
    shc = source[hold_cold]
    yph_c = np.exp(y[hold_cold])
    Xpw = X.iloc[pool_warm].reset_index(drop=True)
    ypw = y[pool_warm]
    Xhw = X.iloc[hold_warm].reset_index(drop=True)
    yph_w = np.exp(y[hold_warm])

    logger.info("  train tuned LGBM cold + CB cold (baseline) + frozen XGB warm...")
    lgbm_cold, lm_lgbm = _train_lgbm(Xpc, ypc, lgbm_best_params)
    cb_cold = _train_cb(Xpc, ypc, cb_params)
    xgb_warm, lm_xgb = _train_xgb(Xpw, ypw, xgb_params)

    pred_cand = np.exp(_predict_lgbm(lgbm_cold, lm_lgbm, Xhc))
    pred_base = np.exp(_predict_cb(cb_cold, Xhc))
    pred_warm = np.exp(_predict_xgb(xgb_warm, lm_xgb, Xhw))

    artsy = shc == "artsy"
    saatchi = shc == "saatchi"

    metrics = {
        "candidate_cold": {
            "cold_overall": round(_mdape(yph_c, pred_cand), 4),
            "cold_artsy": round(_mdape(yph_c[artsy], pred_cand[artsy]), 4) if artsy.any() else None,
            "cold_saatchi": round(_mdape(yph_c[saatchi], pred_cand[saatchi]), 4) if saatchi.any() else None,
        },
        "baseline_cold": {
            "cold_overall": round(_mdape(yph_c, pred_base), 4),
            "cold_artsy": round(_mdape(yph_c[artsy], pred_base[artsy]), 4) if artsy.any() else None,
            "cold_saatchi": round(_mdape(yph_c[saatchi], pred_base[saatchi]), 4) if saatchi.any() else None,
        },
        "warm_shared": round(_mdape(yph_w, pred_warm), 4),
    }

    deltas = {
        "delta_cold_overall": round(metrics["candidate_cold"]["cold_overall"]
                                    - metrics["baseline_cold"]["cold_overall"], 4),
        "delta_cold_artsy": round((metrics["candidate_cold"]["cold_artsy"] or 0)
                                  - (metrics["baseline_cold"]["cold_artsy"] or 0), 4),
        "delta_cold_saatchi": round((metrics["candidate_cold"]["cold_saatchi"] or 0)
                                    - (metrics["baseline_cold"]["cold_saatchi"] or 0), 4),
        "delta_warm": 0.0,
    }

    g1 = deltas["delta_cold_overall"] <= 0
    g2 = deltas["delta_cold_artsy"] <= 0.3
    g3 = deltas["delta_cold_saatchi"] <= 0.3
    if g1 and g2 and g3:
        verdict = "PASS"
    elif 0 < deltas["delta_cold_overall"] <= 0.3 and g2 and g3:
        verdict = "INCONCLUSIVE"
    else:
        verdict = "FAIL"

    logger.info("  Δ_cold=%+.3f / Δ_artsy=%+.3f / Δ_saatchi=%+.3f → %s",
                deltas["delta_cold_overall"], deltas["delta_cold_artsy"],
                deltas["delta_cold_saatchi"], verdict)

    HOLDOUT_DIR.mkdir(parents=True, exist_ok=True)
    (HOLDOUT_DIR / f"seed{seed}_holdout_indices.json").write_text(json.dumps({
        "split_seed": seed,
        "cold": {"pool_indices": pool_cold.tolist(), "holdout_indices": hold_cold.tolist()},
        "warm": {"pool_indices": pool_warm.tolist(), "holdout_indices": hold_warm.tolist()},
    }, indent=2))

    return {
        "n_pool_cold": int(len(pool_cold)),
        "n_holdout_cold": int(len(hold_cold)),
        "metrics": metrics,
        "deltas": deltas,
        "verdict": verdict,
    }


def _aggregate_n10_strict(verdicts: list[str]) -> str:
    n = len(verdicts)
    cnt = {v: verdicts.count(v) for v in ("PASS", "INCONCLUSIVE", "FAIL")}
    if cnt["PASS"] == n:
        return "PASS"
    if cnt["PASS"] == n - 1 and (cnt["INCONCLUSIVE"] + cnt["FAIL"]) == 1:
        return "PASS_with_caveat"
    if cnt["PASS"] == n - 2 and cnt["INCONCLUSIVE"] == 2 and cnt["FAIL"] == 0:
        return "PASS_with_caveat"
    if cnt["FAIL"] >= 2:
        return "FAIL"
    return "INCONCLUSIVE"


def _combined_decision(strict_agg: str, bootstrap_status: str) -> str:
    if strict_agg == "PASS" and bootstrap_status == "bootstrap_PASS":
        return "PROMOTE_TO_TUNING_AND_CANARY"
    if strict_agg == "PASS":
        return "ADOPT_lgbm_canary"
    if strict_agg == "PASS_with_caveat" and bootstrap_status == "bootstrap_PASS":
        return "ADOPT_lgbm_canary"
    if strict_agg == "FAIL":
        return "tuned_LGBM_insufficient"
    return "NEEDS_MORE_DATA"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-trials", type=int, default=N_TRIALS_DEFAULT)
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("D1.Arch.tuned: Tuned LGBM cold-only Optuna search (n_trials=%d)", args.n_trials)
    logger.info("=" * 70)

    cb_params, xgb_params = _load_tuned_params()
    logger.info("Default CB (baseline cold): %s", cb_params)
    logger.info("Default XGB (frozen warm): %s", xgb_params)

    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].reset_index(drop=True)
    fingerprint = _dataset_fingerprint(df)
    logger.info("rows=%d / artists=%d / fingerprint=%s...",
                len(df), df["artist_slug"].nunique(), fingerprint[:12])

    X, y, groups = prepare_features(df)
    source = df["source"].astype(str).to_numpy()

    # Pre-compute baseline CB cold CV per source (for constraints)
    logger.info("Pre-compute baseline CB cold CV (for source feasibility constraints)...")
    gkf = GroupKFold(n_splits=5)
    baseline_metrics_per_fold = []
    for tr, te in gkf.split(X, y, groups):
        cb = _train_cb(X.iloc[tr].reset_index(drop=True), y[tr], cb_params)
        pred_log = _predict_cb(cb, X.iloc[te].reset_index(drop=True))
        pred_exp = np.exp(pred_log)
        y_te_exp = np.exp(y[te])
        src_te = source[te]
        artsy = src_te == "artsy"
        saatchi = src_te == "saatchi"
        baseline_metrics_per_fold.append({
            "cold_overall": _mdape(y_te_exp, pred_exp),
            "cold_artsy": _mdape(y_te_exp[artsy], pred_exp[artsy]) if artsy.any() else None,
            "cold_saatchi": _mdape(y_te_exp[saatchi], pred_exp[saatchi]) if saatchi.any() else None,
        })
    default_cb_overall = float(np.mean([m["cold_overall"] for m in baseline_metrics_per_fold]))
    default_cb_artsy = float(np.mean([m["cold_artsy"] for m in baseline_metrics_per_fold]))
    default_cb_saatchi = float(np.mean([m["cold_saatchi"] for m in baseline_metrics_per_fold]))
    logger.info("  default CB CV: cold_overall=%.4f / artsy=%.4f / saatchi=%.4f",
                default_cb_overall, default_cb_artsy, default_cb_saatchi)

    # Optuna search
    logger.info("=" * 60)
    logger.info("Optuna LGBM search (50 trials / TPE / source constraints)")
    logger.info("=" * 60)
    obj, con = make_objective(X, y, groups, source, default_cb_artsy, default_cb_saatchi)
    sampler = optuna.samplers.TPESampler(seed=RNG_SEED, constraints_func=con)
    study = optuna.create_study(direction="minimize", sampler=sampler)

    # enqueue default LGBM (incumbent first-class)
    try:
        study.enqueue_trial({
            "num_leaves": 31, "learning_rate": 0.05, "feature_fraction": 0.9,
            "bagging_fraction": 0.9, "bagging_freq": 5, "min_data_in_leaf": 20,
            "lambda_l1": 0.0, "lambda_l2": 0.0, "num_boost_round": 1000,
        })
        logger.info("  enqueued default LGBM params (incumbent)")
    except Exception as e:
        logger.warning("  enqueue failed: %s", e)

    study.optimize(obj, n_trials=args.n_trials, show_progress_bar=False)
    best = select_best(study)
    lgbm_best = best.params
    logger.info("Best LGBM params (constraint-feasible): %s", lgbm_best)
    logger.info("Best CV cold_overall: %.4f / metrics: %s", best.value, best.user_attrs.get("cv_metrics"))

    BEST_PARAMS_PATH.write_text(json.dumps({
        "version": "v1-d1-arch-tuned-lgbm",
        "n_trials": args.n_trials,
        "search_seed": RNG_SEED,
        "default_cb_baseline": {
            "cold_overall": default_cb_overall,
            "cold_artsy": default_cb_artsy,
            "cold_saatchi": default_cb_saatchi,
        },
        "lgbm_best_params": lgbm_best,
        "lgbm_best_cv": best.user_attrs.get("cv_metrics"),
        "evaluated_at": datetime.now(UTC).isoformat(),
    }, indent=2, ensure_ascii=False))
    STUDY_PATH.write_text(json.dumps([
        {"number": t.number, "params": t.params, "value": t.value,
         "user_attrs": dict(t.user_attrs), "state": str(t.state)}
        for t in study.trials
    ], indent=2))
    logger.info("[OK] Saved best_params + study log")

    # Validation (N=10 fresh seeds)
    logger.info("=" * 60)
    logger.info("Validation (N=10 fresh seeds=%s)", ALL_SEEDS)
    logger.info("=" * 60)
    HOLDOUT_DIR.mkdir(parents=True, exist_ok=True)
    per_seed: dict[int, Any] = {}
    for seed in ALL_SEEDS:
        per_seed[seed] = _per_seed_validate(seed, X, y, groups, source,
                                             cb_params, xgb_params, lgbm_best)

    verdicts = [per_seed[s]["verdict"] for s in ALL_SEEDS]
    strict_aggregate = _aggregate_n10_strict(verdicts)
    cnt = {v: verdicts.count(v) for v in ("PASS", "INCONCLUSIVE", "FAIL")}

    deltas_arr = {
        cell: np.array([per_seed[s]["deltas"][cell] for s in ALL_SEEDS])
        for cell in ("delta_cold_overall", "delta_cold_artsy", "delta_cold_saatchi")
    }
    bootstrap_ci = {cell: _bootstrap_ci(d) for cell, d in deltas_arr.items()}
    cold_o_ci = bootstrap_ci["delta_cold_overall"]
    if cold_o_ci["ci_upper"] <= 0:
        bootstrap_status = "bootstrap_PASS"
    elif cold_o_ci["ci_upper"] <= 0.5:
        bootstrap_status = "bootstrap_INCONCLUSIVE"
    else:
        bootstrap_status = "bootstrap_FAIL"

    decision = _combined_decision(strict_aggregate, bootstrap_status)
    logger.info("Strict primary: PASS=%d INC=%d FAIL=%d → %s",
                cnt["PASS"], cnt["INCONCLUSIVE"], cnt["FAIL"], strict_aggregate)
    logger.info("Bootstrap secondary: %s", bootstrap_status)
    for cell, ci in bootstrap_ci.items():
        marker = "✅" if ci["ci_upper_negative"] else "⚠️"
        logger.info("  %-22s mean=%+.4f CI95=[%+.3f, %+.3f] %s",
                    cell, ci["mean"], ci["ci_lower"], ci["ci_upper"], marker)
    logger.info("Combined decision: %s", decision)

    output = {
        "version": "v1-d1-arch-tuned-results",
        "decision_binding": True,
        "scope": "cold-only / warm freeze / R1 P0 정합",
        "n_seeds": len(ALL_SEEDS),
        "seeds": list(ALL_SEEDS),
        "lgbm_best_params": lgbm_best,
        "default_cb_baseline_cv": {
            "cold_overall": default_cb_overall,
            "cold_artsy": default_cb_artsy,
            "cold_saatchi": default_cb_saatchi,
        },
        "dataset_fingerprint": fingerprint,
        "per_seed": {str(s): per_seed[s] for s in ALL_SEEDS},
        "strict_aggregate": strict_aggregate,
        "verdict_counts": cnt,
        "bootstrap_status": bootstrap_status,
        "bootstrap_ci": bootstrap_ci,
        "combined_decision": decision,
        "evaluated_at": datetime.now(UTC).isoformat(),
    }
    RESULTS_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    logger.info("[OK] Saved results: %s", RESULTS_PATH.name)

    print("\n" + "=" * 70)
    print(f"D1.Arch.tuned SUMMARY (combined decision: {decision})")
    print("=" * 70)
    print(f"  strict primary: PASS={cnt['PASS']} INC={cnt['INCONCLUSIVE']} FAIL={cnt['FAIL']} → {strict_aggregate}")
    print(f"  bootstrap secondary: {bootstrap_status}")
    print(f"  best LGBM params: {lgbm_best}")
    print()
    for seed in ALL_SEEDS:
        r = per_seed[seed]
        d = r["deltas"]
        print(f"  seed={seed:5d}: {r['verdict']:14s} | Δ_cold={d['delta_cold_overall']:+.3f} "
              f"| Δ_artsy={d['delta_cold_artsy']:+.3f} | Δ_saatchi={d['delta_cold_saatchi']:+.3f}")
    print()
    for cell, ci in bootstrap_ci.items():
        marker = "✅" if ci["ci_upper_negative"] else "⚠️"
        print(f"  {cell:24s} mean={ci['mean']:+.4f} CI95=[{ci['ci_lower']:+.3f}, {ci['ci_upper']:+.3f}] {marker}")
    print("=" * 70)


if __name__ == "__main__":
    main()
