"""Phase 6 — ADD-C (engineered / source_conditional_ho_power only / cap 6).

prereg §3.7 정합. Decision binding ❌ X.

Phase 6.A 코덱스 사전 자문 = GO with P2 (4 fix 적용):
1. baseline split: cycle reference=32 / phase-local incumbent=33 (Phase 4 PASS
   carry-forward = artist_total_works_x_ho)
2. Δ 산출 = vs 33 baseline (phase-local)
3. G1-G4 모두 PASS 명시
4. source assertion (currency-based / KRW vs other) — prereg β=0.74 KRW /
   β=0.84 USD literal 의도 정합

Currency assertion 영역:
  saatchi 100% USD / artsy USD 85% / KRW 12% / 기타 3%
  → "source-based" 영역 의 의무 영역 의 의무 X / "currency-based" 정합

Method:
- 33 baseline (Phase 4 carry-forward = artist_total_works × ho 포함)
- ADD: source_conditional_ho_power = ho^0.74 if KRW else ho^0.84 (USD/EUR/GBP/HKD)
- 1 iter / cap 6 / 1 candidate
- Local primary: Δ Cold MdAPE ≤ -0.1%p (개선)
- PASS: Δ Cold ≤ -0.1 AND G1-G4 모두 PASS
"""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from catboost import CatBoostRegressor, Pool
from sklearn.model_selection import GroupKFold, KFold

REPO = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from train_primary_market_v3_filtered import (  # noqa: E402
    CB_FEATURES,
    CAT_FEATURES,
    _label_encode_xgb,
    _mdape,
    _warm_mask,
    load_data,
    prepare_features,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ARTIFACTS = REPO / "model_test_results"
OUT = Path(__file__).parent / "phase6_add_c_results.json"

# Phase 4 PASS carry-forward = artist_total_works × ho
PHASE4_INTERACTION = "artist_total_works_x_ho"

# Phase 6 candidate
NEW_FEATURE_NAME = "source_conditional_ho_power"

ITERATION_CAP = 6  # prereg

# Cycle reference baseline (32 / Phase 0 fold std mean)
CYCLE_REF_BASELINE = {
    "cold_ensemble":          38.6224,
    "cold_artsy_ensemble":    33.5200,
    "cold_saatchi_ensemble":  41.7400,
    "warm_kfold_xgboost":     9.7140,
    "warm_kfold_ensemble":    10.4680,
}

# Phase-local baseline (33 / Phase 4 PASS carry-forward / iter 2 metric)
PHASE_LOCAL_BASELINE = {
    "cold_catboost":           39.6660,  # Phase 4 iter 2 mean
    "cold_xgboost":            38.5240,  # Phase 4 iter 2 mean
    "cold_ensemble":           38.6073,  # phase-local 33 mean
    "cold_artsy_catboost":     34.4860,  # Phase 4 iter 2 mean
    "cold_artsy_ensemble":     33.9726,  # phase-local 33 mean
    "cold_saatchi_catboost":   41.5660,  # Phase 4 iter 2 mean
    "cold_saatchi_ensemble":   41.2108,  # phase-local 33 mean
    "warm_kfold_xgboost":      9.5971,   # phase-local 33 mean
    "warm_kfold_ensemble":     10.3000,  # approx (Phase 4 iter 2)
    "warm_groupkfold_xgboost": 40.5740,  # approx
    "warm_groupkfold_ensemble": 40.4400, # approx
}

GUARD_LOCKED = {
    "G1_warm_kfold":      {"metric": "warm_kfold_xgboost", "threshold_pp": 0.5},
    "G2_overall_ensemble":{"metric": "cold_ensemble", "threshold_pp": 0.8},
    "G3_artsy_cold":      {"metric": "cold_artsy_ensemble", "threshold_pp": 1.0},
    "G4_saatchi_cold":    {"metric": "cold_saatchi_ensemble", "threshold_pp": 1.0},
}

PRIMARY_IMPROVEMENT_PP = -0.1  # Δ Cold ≤ -0.1


def _summary_fold(y_true_price: np.ndarray, y_pred_price: np.ndarray) -> dict:
    return {"n": len(y_true_price), "MdAPE": float(_mdape(y_true_price, y_pred_price))}


def _cb_pool(X: pd.DataFrame, y: np.ndarray | None, cat_features: list[str]) -> Pool:
    cat_idx = [X.columns.get_loc(c) for c in cat_features if c in X.columns]
    return Pool(X, label=y, cat_features=cat_idx)


def _cv_run(
    X: pd.DataFrame, y: np.ndarray, splits: list, source: np.ndarray | None,
    cb_params: dict, xgb_params: dict, cat_features: list[str], *, label: str,
) -> dict:
    fold_results: list[dict] = []
    for fold, (tr, te) in enumerate(splits, 1):
        t0 = time.time()
        cb = CatBoostRegressor(
            **cb_params, loss_function="RMSE", verbose=0, random_seed=42,
            allow_writing_files=False,
        )
        cb.fit(_cb_pool(X.iloc[tr], y[tr], cat_features))
        cb_pred = cb.predict(_cb_pool(X.iloc[te], None, cat_features))

        Xtr_e, Xte_e, _ = _label_encode_xgb(X.iloc[tr], X.iloc[te])
        dtrain = xgb.DMatrix(Xtr_e, label=y[tr])
        dtest = xgb.DMatrix(Xte_e, label=y[te])
        xgb_p = {k: v for k, v in xgb_params.items() if k != "num_boost_round"}
        m = xgb.train(
            params={**xgb_p, "objective": "reg:squarederror", "verbosity": 0, "seed": 42},
            dtrain=dtrain, num_boost_round=xgb_params.get("num_boost_round", 1000),
        )
        xgb_pred = m.predict(dtest)

        y_te_price = np.exp(y[te])
        cb_price = np.exp(cb_pred)
        xgb_price = np.exp(xgb_pred)
        ens_price = np.exp((cb_pred + xgb_pred) / 2)

        f = {
            "fold": fold,
            "n_train": int(len(tr)),
            "n_test": int(len(te)),
            "catboost": _summary_fold(y_te_price, cb_price),
            "xgboost": _summary_fold(y_te_price, xgb_price),
            "ensemble": _summary_fold(y_te_price, ens_price),
            "elapsed_sec": round(time.time() - t0, 1),
        }
        if source is not None:
            src_te = source[te]
            for src_name in sorted(set(src_te)):
                mask = src_te == src_name
                if mask.sum() == 0:
                    continue
                f[f"{src_name}_catboost"] = _summary_fold(y_te_price[mask], cb_price[mask])
                f[f"{src_name}_ensemble"] = _summary_fold(y_te_price[mask], ens_price[mask])
        fold_results.append(f)
        logger.info(f"    {label} fold {fold}/{len(splits)}: cb={f['catboost']['MdAPE']:.2f} "
                    f"xgb={f['xgboost']['MdAPE']:.2f} ens={f['ensemble']['MdAPE']:.2f} "
                    f"({f['elapsed_sec']}s)")
    return {"folds": fold_results, "n_total": int(len(y))}


def _mean_metric(folds: list[dict], path: list[str]) -> float | None:
    vals = []
    for f in folds:
        cur = f
        for k in path:
            cur = cur.get(k, {})
        if isinstance(cur, dict) and "MdAPE" in cur:
            vals.append(cur["MdAPE"])
    if not vals:
        return None
    return float(np.mean(vals))


def add_phase4_interaction(X: pd.DataFrame) -> pd.DataFrame:
    """Phase 4 PASS carry-forward = artist_total_works × ho."""
    X = X.copy()
    a = pd.to_numeric(X["artist_total_works"], errors="coerce").fillna(0.0)
    b = pd.to_numeric(X["ho"], errors="coerce").fillna(0.0)
    X[PHASE4_INTERACTION] = (a * b).astype(float)
    return X


def add_source_conditional_ho_power(X: pd.DataFrame, df_meta: pd.DataFrame) -> pd.DataFrame:
    """source_conditional_ho_power = ho^0.74 if KRW else ho^0.84 (USD/EUR/GBP/HKD).

    Currency-based (prereg β literal 의도 정합 / artsy ≠ KRW 영역 의 의무 영역 의 의무).
    """
    X = X.copy()
    ho = pd.to_numeric(X["ho"], errors="coerce").fillna(0.0).astype(float)
    currency = df_meta["price_currency"].astype(str).reset_index(drop=True)
    is_krw = (currency == "KRW").to_numpy()

    # Assertion (silent fallback X)
    valid_currencies = {"KRW", "USD", "EUR", "GBP", "HKD"}
    unknown = set(currency.unique()) - valid_currencies
    assert not unknown, f"Unknown currency: {unknown}"

    out = np.where(is_krw, np.power(ho.to_numpy(), 0.74), np.power(ho.to_numpy(), 0.84))
    X[NEW_FEATURE_NAME] = out
    return X


def main() -> None:
    t0 = time.time()
    logger.info("=" * 70)
    logger.info("Phase 6 — ADD-C (source_conditional_ho_power / 33 baseline)")
    logger.info("=" * 70)
    logger.info(f"Carry-forward Phase 4: {PHASE4_INTERACTION} ✓")
    logger.info(f"New feature: {NEW_FEATURE_NAME} (currency-based)")

    best_params = json.loads((ARTIFACTS / "integrated_v3_filtered_tuned_best_params.json").read_text())
    cb_best = best_params["catboost"]
    xgb_best = best_params["xgboost"]

    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].reset_index(drop=True).copy()
    X_full, y, groups = prepare_features(df)
    source = df["source"].astype(str).to_numpy()

    # X_full / df 영역 의 의무 row order 영역 의 의무 정합 검증
    assert len(X_full) == len(df), f"row mismatch: X_full={len(X_full)} df={len(df)}"

    # Phase 4 carry-forward + Phase 6 ADD
    X_aug = add_phase4_interaction(X_full)
    X_aug = add_source_conditional_ho_power(X_aug, df)

    feature_set = list(CB_FEATURES) + [PHASE4_INTERACTION, NEW_FEATURE_NAME]
    cat_features_iter = [c for c in CAT_FEATURES if c in feature_set]
    X = X_aug[feature_set].copy()
    logger.info(f"Phase 6 features: {len(feature_set)} cols (32 + 1 Phase 4 + 1 ADD-C)")

    # cold GroupKFold-5
    logger.info("\n--- Cold GroupKFold-5 ---")
    gkf = GroupKFold(n_splits=5)
    cold = _cv_run(X, y, list(gkf.split(X, y, groups)), source, cb_best, xgb_best, cat_features_iter, label="GKF")

    # warm slice
    warm_mask = _warm_mask(groups)
    X_warm = X[warm_mask].reset_index(drop=True)
    y_warm = y[warm_mask]
    g_warm = groups[warm_mask]

    logger.info("\n--- Warm KFold-5 (main) ---")
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    warm_kfold = _cv_run(X_warm, y_warm, list(kf.split(X_warm, y_warm)), None, cb_best, xgb_best, cat_features_iter, label="KF")

    logger.info("\n--- Warm GroupKFold-5 (guard) ---")
    gkf2 = GroupKFold(n_splits=5)
    warm_gkfold = _cv_run(X_warm, y_warm, list(gkf2.split(X_warm, y_warm, g_warm)), None, cb_best, xgb_best, cat_features_iter, label="wGKF")

    metrics = {
        "cold_catboost":           _mean_metric(cold["folds"], ["catboost"]),
        "cold_xgboost":            _mean_metric(cold["folds"], ["xgboost"]),
        "cold_ensemble":           _mean_metric(cold["folds"], ["ensemble"]),
        "cold_artsy_catboost":     _mean_metric(cold["folds"], ["artsy_catboost"]),
        "cold_artsy_ensemble":     _mean_metric(cold["folds"], ["artsy_ensemble"]),
        "cold_saatchi_catboost":   _mean_metric(cold["folds"], ["saatchi_catboost"]),
        "cold_saatchi_ensemble":   _mean_metric(cold["folds"], ["saatchi_ensemble"]),
        "warm_kfold_xgboost":      _mean_metric(warm_kfold["folds"], ["xgboost"]),
        "warm_kfold_ensemble":     _mean_metric(warm_kfold["folds"], ["ensemble"]),
        "warm_groupkfold_xgboost": _mean_metric(warm_gkfold["folds"], ["xgboost"]),
        "warm_groupkfold_ensemble":_mean_metric(warm_gkfold["folds"], ["ensemble"]),
    }
    deltas_local = {k: round(metrics[k] - PHASE_LOCAL_BASELINE[k], 4)
                    for k in metrics if metrics[k] is not None and k in PHASE_LOCAL_BASELINE}
    deltas_cycle = {k: round(metrics[k] - CYCLE_REF_BASELINE[k], 4)
                    for k in metrics if metrics[k] is not None and k in CYCLE_REF_BASELINE}

    # Guard 4 (vs phase-local baseline)
    guards = {}
    for guard_name, gd in GUARD_LOCKED.items():
        delta = deltas_local.get(gd["metric"])
        guards[guard_name] = {
            "delta_local": delta,
            "threshold_pp": gd["threshold_pp"],
            "pass": bool(delta is not None and delta <= gd["threshold_pp"]),
        }

    delta_cold = deltas_local.get("cold_ensemble")
    primary_pass = (delta_cold is not None and delta_cold <= PRIMARY_IMPROVEMENT_PP)
    all_guards_pass = all(g["pass"] for g in guards.values())
    iter_pass = primary_pass and all_guards_pass

    out = {
        "phase": 6,
        "strategy": "ADD-C (source_conditional_ho_power only / 33 → 34)",
        "scope": "prereg §3.7 / gallery_avg + medium_avg = same as-of contract / 보류",
        "n_features_before": 33,
        "n_features_after": len(feature_set),
        "added_feature": NEW_FEATURE_NAME,
        "phase4_carry_forward": PHASE4_INTERACTION,
        "currency_mapping": {
            "KRW": "ho^0.74 (β prereg literal)",
            "USD/EUR/GBP/HKD": "ho^0.84 (β prereg literal)",
        },
        "cycle_ref_baseline_32": CYCLE_REF_BASELINE,
        "phase_local_baseline_33": PHASE_LOCAL_BASELINE,
        "guard_locked": GUARD_LOCKED,
        "primary_improvement_pp": PRIMARY_IMPROVEMENT_PP,
        "metrics": metrics,
        "deltas_vs_phase_local_33": deltas_local,
        "deltas_vs_cycle_ref_32": deltas_cycle,
        "guard_check_locked": guards,
        "primary_pass": primary_pass,
        "all_guards_pass": all_guards_pass,
        "iter_pass": iter_pass,
        "verdict": "PASS" if iter_pass else "FAIL",
        "elapsed_sec": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    logger.info(f"\n[OK] {OUT.name} (elapsed {out['elapsed_sec']}s)")

    print("\n" + "=" * 80)
    print(f"Phase 6 RESULTS")
    print("=" * 80)
    print(f"\n{'metric':30s} {'phase6':>10s} {'33-base':>10s} {'Δ local':>9s} {'32-ref':>10s} {'Δ cycle':>9s}")
    for k in sorted(metrics.keys()):
        m = metrics[k]
        bl = PHASE_LOCAL_BASELINE.get(k)
        cr = CYCLE_REF_BASELINE.get(k)
        dl = deltas_local.get(k)
        dc = deltas_cycle.get(k)
        bl_s = f"{bl:>10.3f}" if bl is not None else f"{'—':>10s}"
        cr_s = f"{cr:>10.3f}" if cr is not None else f"{'—':>10s}"
        dl_s = f"{dl:>+9.3f}" if dl is not None else f"{'—':>9s}"
        dc_s = f"{dc:>+9.3f}" if dc is not None else f"{'—':>9s}"
        print(f"{k:30s} {m:>10.3f} {bl_s} {dl_s} {cr_s} {dc_s}")
    print()
    print("=== Guard 4 (locked / vs phase-local 33) ===")
    for guard_name, g in guards.items():
        sym = "✓" if g["pass"] else "✗"
        print(f"  {sym} {guard_name}: Δ local={g['delta_local']:+.3f}%p ≤ +{g['threshold_pp']}%p")
    print()
    print(f"=== PASS criterion (Δ Cold local ≤ -0.1 AND G1-G4 all pass) ===")
    print(f"  Δ Cold ens (local) = {delta_cold:+.3f}%p")
    print(f"  primary_pass: {primary_pass}")
    print(f"  all_guards_pass: {all_guards_pass}")
    print(f"\n=== VERDICT: {out['verdict']} ===")


if __name__ == "__main__":
    main()
