"""D1.SC: Source-Conditional Validation cycle (R1 NEEDS FIX → R2/R3 LGTM amendment).

Prereg: docs/d1_sc_source_conditional_validation_prereg_20260510.md
연계: PR1 v1 (commit f74f73b) source-conditional artifacts / D1-extended D1 axis abandon 후 codex Q7 추천.

R1 amendment 정합:
- P0 fix: candidate AND baseline 둘 다 80% pool 위 fresh retrain (in-sample bias 회피)
- P1.1 fix: per-source binding primaries (artsy_primary / saatchi_primary / overall_primary)
- P1.2 fix: explicit serving contract — cold by source CB / warm by unified XGB (orthogonal to PR-WARM-B)
- R2 amendment: 양 arm calibration 미적용 (raw output)

Method:
- 각 seed (10 fresh): GroupShuffleSplit 80/20 cold + train_test_split 80/20 warm
- Candidate retrain: artsy_cb (artsy pool) + saatchi_cb (saatchi pool) + unified_xgb_warm (warm pool)
- Baseline retrain: unified_cb (full cold pool) + unified_xgb_warm (warm pool / shared with candidate)
- Holdout serving:
  - cold rows: candidate route by source / baseline unified
  - warm rows: 양쪽 모두 unified_xgb_warm (orthogonal)
- Per-cell MdAPE: cold_overall / cold_artsy / cold_saatchi / warm
- Δ_cell = candidate − baseline

Endpoints (R1 amendment):
- Primary 1: artsy_primary (Δ_cold_artsy strict aggregate)
- Primary 2: saatchi_primary (Δ_cold_saatchi strict aggregate)
- Primary 3: overall_primary (D1.Y G1-G4 aggregate)
- Secondary: bootstrap CI corroboration

Compute: ~10-15분 wall (10 seed × ~50-90s).

Usage:
    python3 scripts/d1_sc_validation.py
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
HOLDOUT_DIR = REPO / "data" / "d1_sc_holdout_20260510"
RESULTS_PATH = ARTIFACTS_DIR / "d1_sc_results.json"

ALL_SEEDS = (941, 967, 991, 1009, 1031, 1049, 1069, 1093, 1117, 1129)
N_BOOT = 10000
RNG_SEED = 42


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
        "mean": float(deltas.mean()),
        "ci_lower": round(lo, 4),
        "ci_upper": round(hi, 4),
        "ci_upper_negative": bool(hi <= 0),
    }


def _per_seed_validate(
    seed: int,
    X: pd.DataFrame, y: np.ndarray, groups: np.ndarray, source: np.ndarray,
    cb_params: dict, xgb_params: dict,
) -> dict[str, Any]:
    logger.info("--- D1.SC validate seed=%d ---", seed)

    # Cold split (artist groups)
    gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=seed)
    pool_cold, hold_cold = next(gss.split(X, y, groups))
    pool_cold = np.sort(pool_cold)
    hold_cold = np.sort(hold_cold)

    # Warm split (rows / D1.Y 정합)
    wmask = _warm_mask(groups)
    warm_g = np.where(wmask)[0]
    pool_w_loc, hold_w_loc = train_test_split(
        np.arange(len(warm_g)), test_size=0.20, random_state=seed, shuffle=True,
    )
    pool_warm = warm_g[np.sort(pool_w_loc)]
    hold_warm = warm_g[np.sort(hold_w_loc)]

    # Pool slices
    Xpc = X.iloc[pool_cold].reset_index(drop=True)
    ypc = y[pool_cold]
    spc = source[pool_cold]
    Xhc = X.iloc[hold_cold].reset_index(drop=True)
    shc = source[hold_cold]
    yph_c = np.exp(y[hold_cold])

    Xpw = X.iloc[pool_warm].reset_index(drop=True)
    ypw = y[pool_warm]
    Xhw = X.iloc[hold_warm].reset_index(drop=True)
    yph_w = np.exp(y[hold_warm])

    # Source-partitioned cold pools
    artsy_pool_mask = spc == "artsy"
    saatchi_pool_mask = spc == "saatchi"
    Xpc_artsy = Xpc[artsy_pool_mask].reset_index(drop=True)
    ypc_artsy = ypc[artsy_pool_mask]
    Xpc_saatchi = Xpc[saatchi_pool_mask].reset_index(drop=True)
    ypc_saatchi = ypc[saatchi_pool_mask]

    # Train candidate (source-conditional CB) + baseline (unified CB) + shared unified XGB warm
    logger.info("  train candidate (artsy_cb / saatchi_cb / unified_xgb_warm) + baseline (unified_cb)...")
    artsy_cb = _train_cb(Xpc_artsy, ypc_artsy, cb_params)
    saatchi_cb = _train_cb(Xpc_saatchi, ypc_saatchi, cb_params)
    unified_cb = _train_cb(Xpc, ypc, cb_params)
    unified_xgb_warm, lm_warm = _train_xgb(Xpw, ypw, xgb_params)

    # Cold holdout prediction
    artsy_hold_mask = shc == "artsy"
    saatchi_hold_mask = shc == "saatchi"

    # Candidate: route by source
    pred_cand = np.zeros(len(yph_c))
    if artsy_hold_mask.any():
        pred_cand[artsy_hold_mask] = _predict_cb(artsy_cb, Xhc[artsy_hold_mask].reset_index(drop=True))
    if saatchi_hold_mask.any():
        pred_cand[saatchi_hold_mask] = _predict_cb(saatchi_cb, Xhc[saatchi_hold_mask].reset_index(drop=True))
    pred_cand_exp = np.exp(pred_cand)

    # Baseline: unified
    pred_base = np.exp(_predict_cb(unified_cb, Xhc))

    # Warm holdout prediction (shared unified XGB / 양쪽 동일)
    pred_warm = np.exp(_predict_xgb(unified_xgb_warm, lm_warm, Xhw))

    # Per-cell MdAPE
    artsy = artsy_hold_mask
    saatchi = saatchi_hold_mask
    metrics = {
        "candidate_cold": {
            "cold_overall": round(_mdape(yph_c, pred_cand_exp), 4),
            "cold_artsy": round(_mdape(yph_c[artsy], pred_cand_exp[artsy]), 4) if artsy.any() else None,
            "cold_saatchi": round(_mdape(yph_c[saatchi], pred_cand_exp[saatchi]), 4) if saatchi.any() else None,
        },
        "baseline_cold": {
            "cold_overall": round(_mdape(yph_c, pred_base), 4),
            "cold_artsy": round(_mdape(yph_c[artsy], pred_base[artsy]), 4) if artsy.any() else None,
            "cold_saatchi": round(_mdape(yph_c[saatchi], pred_base[saatchi]), 4) if saatchi.any() else None,
        },
        # warm 동일 (orthogonal axis / 양쪽 동일 prediction)
        "warm_shared": round(_mdape(yph_w, pred_warm), 4),
    }

    deltas = {
        "delta_cold_overall": round(metrics["candidate_cold"]["cold_overall"]
                                    - metrics["baseline_cold"]["cold_overall"], 4),
        "delta_cold_artsy": round((metrics["candidate_cold"]["cold_artsy"] or 0)
                                  - (metrics["baseline_cold"]["cold_artsy"] or 0), 4),
        "delta_cold_saatchi": round((metrics["candidate_cold"]["cold_saatchi"] or 0)
                                    - (metrics["baseline_cold"]["cold_saatchi"] or 0), 4),
        "delta_warm": 0.0,  # orthogonal / shared XGB
    }

    # Per-source verdict (artsy_primary / saatchi_primary)
    def _src_verdict(d: float) -> str:
        if d <= 0:
            return "PASS"
        if d <= 0.3:
            return "INCONCLUSIVE"
        return "FAIL"

    artsy_v = _src_verdict(deltas["delta_cold_artsy"])
    saatchi_v = _src_verdict(deltas["delta_cold_saatchi"])

    # Overall verdict (D1.Y G1-G4 정합 / warm Δ=0이라 G4 무조건 PASS)
    g1 = deltas["delta_cold_overall"] <= 0
    g2 = deltas["delta_cold_artsy"] <= 0.3
    g3 = deltas["delta_cold_saatchi"] <= 0.3
    g4 = True  # warm shared / Δ=0
    if g1 and g2 and g3 and g4:
        overall_v = "PASS"
    elif 0 < deltas["delta_cold_overall"] <= 0.3 and g2 and g3:
        overall_v = "INCONCLUSIVE"
    else:
        overall_v = "FAIL"

    logger.info("  Δ_cold=%+.3f / Δ_artsy=%+.3f / Δ_saatchi=%+.3f → artsy=%s saatchi=%s overall=%s",
                deltas["delta_cold_overall"], deltas["delta_cold_artsy"],
                deltas["delta_cold_saatchi"], artsy_v, saatchi_v, overall_v)

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
        "artsy_verdict": artsy_v,
        "saatchi_verdict": saatchi_v,
        "overall_verdict": overall_v,
    }


def _aggregate_n10(verdicts: list[str]) -> str:
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


def _combined_decision(artsy_agg: str, saatchi_agg: str, overall_agg: str) -> str:
    """R1 P1.1 amendment / per-source binding primaries."""
    if overall_agg == "PASS" and artsy_agg in ("PASS", "PASS_with_caveat") and saatchi_agg in ("PASS", "PASS_with_caveat"):
        return "ADOPT_full_migration"
    if overall_agg == "PASS_with_caveat" and artsy_agg in ("PASS", "PASS_with_caveat") and saatchi_agg in ("PASS", "PASS_with_caveat"):
        return "ADOPT_canary_full"
    if artsy_agg in ("PASS", "PASS_with_caveat") and saatchi_agg == "FAIL":
        return "ADOPT_artsy_only_canary"
    if saatchi_agg in ("PASS", "PASS_with_caveat") and artsy_agg == "FAIL":
        return "ADOPT_saatchi_only_canary"
    if artsy_agg == "FAIL" and saatchi_agg == "FAIL":
        return "HOLD_source_conditional_axis_abandon"
    return "NEEDS_MORE_DATA"


def main() -> None:
    logger.info("=" * 70)
    logger.info("D1.SC: Source-Conditional Validation cycle (per-source binding primaries)")
    logger.info("=" * 70)

    cb_params, xgb_params = _load_tuned_params()
    logger.info("CB params: %s", cb_params)
    logger.info("XGB params: %s", xgb_params)

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

    # Aggregate per primary
    artsy_verdicts = [per_seed[s]["artsy_verdict"] for s in ALL_SEEDS]
    saatchi_verdicts = [per_seed[s]["saatchi_verdict"] for s in ALL_SEEDS]
    overall_verdicts = [per_seed[s]["overall_verdict"] for s in ALL_SEEDS]
    artsy_agg = _aggregate_n10(artsy_verdicts)
    saatchi_agg = _aggregate_n10(saatchi_verdicts)
    overall_agg = _aggregate_n10(overall_verdicts)

    logger.info("=" * 60)
    logger.info("Aggregate per primary:")
    logger.info("  artsy_primary:   PASS=%d INC=%d FAIL=%d → %s",
                artsy_verdicts.count("PASS"), artsy_verdicts.count("INCONCLUSIVE"),
                artsy_verdicts.count("FAIL"), artsy_agg)
    logger.info("  saatchi_primary: PASS=%d INC=%d FAIL=%d → %s",
                saatchi_verdicts.count("PASS"), saatchi_verdicts.count("INCONCLUSIVE"),
                saatchi_verdicts.count("FAIL"), saatchi_agg)
    logger.info("  overall_primary: PASS=%d INC=%d FAIL=%d → %s",
                overall_verdicts.count("PASS"), overall_verdicts.count("INCONCLUSIVE"),
                overall_verdicts.count("FAIL"), overall_agg)
    logger.info("=" * 60)

    # Bootstrap CI
    deltas_arr = {
        "delta_cold_overall": np.array([per_seed[s]["deltas"]["delta_cold_overall"] for s in ALL_SEEDS]),
        "delta_cold_artsy": np.array([per_seed[s]["deltas"]["delta_cold_artsy"] for s in ALL_SEEDS]),
        "delta_cold_saatchi": np.array([per_seed[s]["deltas"]["delta_cold_saatchi"] for s in ALL_SEEDS]),
    }
    bootstrap_ci = {cell: _bootstrap_ci(d) for cell, d in deltas_arr.items()}
    logger.info("Bootstrap CI (corroboration only):")
    for cell, ci in bootstrap_ci.items():
        marker = "✅" if ci["ci_upper_negative"] else "⚠️"
        logger.info("  %-22s mean=%+.4f CI95=[%+.3f, %+.3f] %s",
                    cell, ci["mean"], ci["ci_lower"], ci["ci_upper"], marker)

    decision = _combined_decision(artsy_agg, saatchi_agg, overall_agg)
    logger.info("Combined decision: %s", decision)

    output = {
        "version": "v1-d1-sc-source-conditional",
        "decision_binding": True,
        "n_seeds": len(ALL_SEEDS),
        "seeds": list(ALL_SEEDS),
        "cb_params": cb_params,
        "xgb_params": xgb_params,
        "dataset_fingerprint": fingerprint,
        "per_seed": {str(s): per_seed[s] for s in ALL_SEEDS},
        "artsy_aggregate": artsy_agg,
        "saatchi_aggregate": saatchi_agg,
        "overall_aggregate": overall_agg,
        "bootstrap_ci": bootstrap_ci,
        "combined_decision": decision,
        "evaluated_at": datetime.now(UTC).isoformat(),
    }
    RESULTS_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    logger.info("[OK] Saved: %s", RESULTS_PATH.name)

    print("\n" + "=" * 70)
    print(f"D1.SC SUMMARY (combined decision: {decision})")
    print("=" * 70)
    print(f"  artsy_primary:   {artsy_agg}")
    print(f"  saatchi_primary: {saatchi_agg}")
    print(f"  overall_primary: {overall_agg}")
    print()
    for seed in ALL_SEEDS:
        r = per_seed[seed]
        d = r["deltas"]
        print(f"  seed={seed:4d}: artsy={r['artsy_verdict']:14s} saatchi={r['saatchi_verdict']:14s} "
              f"overall={r['overall_verdict']:14s} | Δ_cold={d['delta_cold_overall']:+.3f}")
    print()
    print("Bootstrap CI (corroboration):")
    for cell, ci in bootstrap_ci.items():
        marker = "✅" if ci["ci_upper_negative"] else "⚠️"
        print(f"  {cell:24s} mean={ci['mean']:+.4f} CI95=[{ci['ci_lower']:+.3f}, {ci['ci_upper']:+.3f}] {marker}")
    print("=" * 70)


if __name__ == "__main__":
    main()
