"""D1.Arch: LightGBM cold-only replacement (R1 NEEDS FIX → R2/R3 LGTM amendment).

Prereg: docs/d1_arch_lightgbm_replacement_prereg_20260510.md
Decision binding: ✅ YES (cold-only narrow scope / PROMOTE_TO_TUNING_AND_CANARY cap)

R1 amendment 정합:
- P0 fix: cold-only / warm = default XGB freeze (B와 orthogonal)
- P1.1 fix: FAIL = "default LGBM insufficient" only (narrow)
- P1.2 fix: cap at PROMOTE_TO_TUNING_AND_CANARY / 단일 cycle full migration X

Method:
- 10 fresh seeds {1153, 1171, 1187, 1201, 1217, 1231, 1249, 1259, 1277, 1289}
- Candidate: LGBM cold (default params) + default XGB warm freeze
- Baseline: default CB cold + default XGB warm freeze
- Cold-only Δ measurement (warm Δ=0 by design)
- D1.Y framework strict primary + bootstrap secondary corroboration

Compute: ~5-10분 wall (LGBM 빠름 / cold-only / D1.Y 정합).

Usage:
    python3 scripts/d1_arch_lgbm_validation.py
"""

from __future__ import annotations

import hashlib
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import lightgbm as lgb
import numpy as np
import pandas as pd
import xgboost as xgb
from catboost import CatBoostRegressor
from sklearn.model_selection import GroupShuffleSplit, train_test_split

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

ARTIFACTS_DIR = REPO / "model_test_results"
HOLDOUT_DIR = REPO / "data" / "d1_arch_holdout_20260510"
RESULTS_PATH = ARTIFACTS_DIR / "d1_arch_results.json"

ALL_SEEDS = (1153, 1171, 1187, 1201, 1217, 1231, 1249, 1259, 1277, 1289)
N_BOOT = 10000
RNG_SEED = 42

# LGBM default params (R1 amendment / no HP search this cycle)
LGBM_PARAMS = {
    "objective": "regression",
    "metric": "l2",
    "num_leaves": 31,
    "learning_rate": 0.05,
    "feature_fraction": 0.9,
    "bagging_fraction": 0.9,
    "bagging_freq": 5,
    "verbose": -1,
    "seed": 42,
}
LGBM_NUM_BOOST_ROUND = 1000


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


def _train_lgbm(X: pd.DataFrame, y: np.ndarray) -> tuple[lgb.Booster, dict]:
    """Train LightGBM with native categorical handling."""
    Xe, lm = _local_label_encode(X[CB_FEATURES], CAT_FEATURES)
    cat_indices = [Xe.columns.get_loc(c) for c in CAT_FEATURES if c in Xe.columns]
    dtrain = lgb.Dataset(Xe, label=y, categorical_feature=cat_indices)
    booster = lgb.train(LGBM_PARAMS, dtrain, num_boost_round=LGBM_NUM_BOOST_ROUND)
    return booster, lm


def _predict_lgbm(booster: lgb.Booster, lm: dict, X: pd.DataFrame) -> np.ndarray:
    Xe = _apply_label_maps(X[CB_FEATURES], lm)
    return np.asarray(booster.predict(Xe))


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
    cb_params: dict, xgb_params: dict,
) -> dict[str, Any]:
    logger.info("--- D1.Arch validate seed=%d ---", seed)

    # Cold split (artist groups)
    gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=seed)
    pool_cold, hold_cold = next(gss.split(X, y, groups))
    pool_cold = np.sort(pool_cold)
    hold_cold = np.sort(hold_cold)

    # Warm split (rows)
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

    # Train candidate (LGBM cold + freeze warm) + baseline (CB cold + freeze warm)
    logger.info("  train LGBM cold + CB cold + frozen warm XGB...")
    lgbm_cold, lm_lgbm = _train_lgbm(Xpc, ypc)
    cb_cold = _train_cb(Xpc, ypc, cb_params)
    xgb_warm, lm_xgb_warm = _train_xgb(Xpw, ypw, xgb_params)  # frozen / shared

    # Cold inference
    pred_cand_log = _predict_lgbm(lgbm_cold, lm_lgbm, Xhc)
    pred_base_log = _predict_cb(cb_cold, Xhc)
    pred_cand = np.exp(pred_cand_log)
    pred_base = np.exp(pred_base_log)

    # Warm inference (orthogonal / shared XGB / Δ_warm = 0 by design)
    pred_warm = np.exp(_predict_xgb(xgb_warm, lm_xgb_warm, Xhw))

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
        "delta_warm": 0.0,  # orthogonal / frozen warm
    }

    g1 = deltas["delta_cold_overall"] <= 0
    g2 = deltas["delta_cold_artsy"] <= 0.3
    g3 = deltas["delta_cold_saatchi"] <= 0.3
    g4 = True  # warm frozen / Δ=0
    if g1 and g2 and g3 and g4:
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
    """R1 P1.2 amendment / cap at canary."""
    if strict_agg == "PASS" and bootstrap_status == "bootstrap_PASS":
        return "PROMOTE_TO_TUNING_AND_CANARY"
    if strict_agg == "PASS":
        return "ADOPT_lgbm_canary"
    if strict_agg == "PASS_with_caveat" and bootstrap_status == "bootstrap_PASS":
        return "ADOPT_lgbm_canary"
    if strict_agg == "FAIL":
        return "default_LGBM_insufficient"  # R1 P1.1 narrow
    return "NEEDS_MORE_DATA"


def main() -> None:
    logger.info("=" * 70)
    logger.info("D1.Arch: LightGBM cold-only replacement (R1 amendment / cold-only narrow)")
    logger.info("=" * 70)

    cb_params, xgb_params = _load_tuned_params()
    logger.info("Default CB params (baseline cold): %s", cb_params)
    logger.info("Default XGB params (frozen warm): %s", xgb_params)
    logger.info("LGBM params (candidate cold / default): %s", LGBM_PARAMS)

    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].reset_index(drop=True)
    fingerprint = _dataset_fingerprint(df)
    logger.info("rows=%d / artists=%d / fingerprint=%s...",
                len(df), df["artist_slug"].nunique(), fingerprint[:12])

    X, y, groups = prepare_features(df)
    source = df["source"].astype(str).to_numpy()

    HOLDOUT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("Per-seed validation (seeds=%s)", ALL_SEEDS)
    logger.info("=" * 60)
    per_seed: dict[int, Any] = {}
    for seed in ALL_SEEDS:
        per_seed[seed] = _per_seed_validate(seed, X, y, groups, source, cb_params, xgb_params)

    # Aggregate
    verdicts = [per_seed[s]["verdict"] for s in ALL_SEEDS]
    strict_aggregate = _aggregate_n10_strict(verdicts)
    cnt = {v: verdicts.count(v) for v in ("PASS", "INCONCLUSIVE", "FAIL")}

    # Bootstrap CI corroboration
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

    logger.info("=" * 60)
    logger.info("Strict primary (D1.Y rule):")
    logger.info("  PASS=%d INCONCLUSIVE=%d FAIL=%d → %s",
                cnt["PASS"], cnt["INCONCLUSIVE"], cnt["FAIL"], strict_aggregate)
    logger.info("Bootstrap CI corroboration (N=10 / hierarchical cold_overall):")
    for cell, ci in bootstrap_ci.items():
        marker = "✅" if ci["ci_upper_negative"] else "⚠️"
        logger.info("  %-22s mean=%+.4f CI95=[%+.3f, %+.3f] %s",
                    cell, ci["mean"], ci["ci_lower"], ci["ci_upper"], marker)
    logger.info("Combined decision: %s", decision)
    logger.info("=" * 60)

    output = {
        "version": "v1-d1-arch-lgbm-cold-only",
        "decision_binding": True,
        "scope": "cold-only / warm freeze (R1 P0 amendment)",
        "n_seeds": len(ALL_SEEDS),
        "seeds": list(ALL_SEEDS),
        "lgbm_params": LGBM_PARAMS,
        "lgbm_num_boost_round": LGBM_NUM_BOOST_ROUND,
        "cb_params_baseline": cb_params,
        "xgb_params_frozen_warm": xgb_params,
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
    logger.info("[OK] Saved: %s", RESULTS_PATH.name)

    print("\n" + "=" * 70)
    print(f"D1.Arch SUMMARY (combined decision: {decision})")
    print("=" * 70)
    print(f"  strict primary: PASS={cnt['PASS']} INC={cnt['INCONCLUSIVE']} FAIL={cnt['FAIL']} → {strict_aggregate}")
    print(f"  bootstrap secondary: {bootstrap_status}")
    print()
    for seed in ALL_SEEDS:
        r = per_seed[seed]
        d = r["deltas"]
        print(f"  seed={seed:5d}: {r['verdict']:14s} | Δ_cold={d['delta_cold_overall']:+.3f} "
              f"| Δ_artsy={d['delta_cold_artsy']:+.3f} | Δ_saatchi={d['delta_cold_saatchi']:+.3f}")
    print()
    print("Bootstrap CI:")
    for cell, ci in bootstrap_ci.items():
        marker = "✅" if ci["ci_upper_negative"] else "⚠️"
        print(f"  {cell:24s} mean={ci['mean']:+.4f} CI95=[{ci['ci_lower']:+.3f}, {ci['ci_upper']:+.3f}] {marker}")
    print("=" * 70)


if __name__ == "__main__":
    main()
