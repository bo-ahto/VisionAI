"""Phase 2 — DROP-B (low-importance / 1-by-1 누적 / max 8 iter).

prereg §3.3 정합. Decision binding ❌ X.

Phase 2.A 코덱스 사전 자문 P2 fix:
1. baseline anchor = §2 frozen + Phase 0 fold std mean (둘 다 record)
   - primary anchor (Δ 산출) = Phase 0 fold std mean (Phase 1 사전+사후 정합)
   - reference = §2 frozen baseline (운영 reported)
2. 후보 순서 = SHAP avg ASC (tie-break primary / 4 method consensus + SHAP 우선)
3. N 변화 = 32 → 24 (cap 8)
4. PASS 문구 = Local primary (Δ Cold ≤+0.05 AND Δ Warm ≤+0.05) AND Guard 4 PASS
   termination Δ = Cold ensemble (Δ > +0.1 → phase 종료)

Method:
- 매 iter = 1 feature 누적 제거 (B sequential)
- 32 baseline 시작 (Phase 1 carry-forward X)
- iter 1: 32→31 (DROP top-1 = is_edition)
- iter 2: 31→30 (DROP top-2 = is_unique)
- ...
- iter 8: 25→24 (max cap)
- 매 iter PASS → 누적 / FAIL or Δ Cold > +0.1 → phase 종료
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
OUT = Path(__file__).parent / "phase2_drop_b_results.json"

# Phase 2 후보 (SHAP avg ASC / tie-break primary)
DROP_CANDIDATES_ORDERED = [
    "is_edition",          # SHAP_avg 0.003%
    "is_unique",           # 0.011%
    "attribution_class",   # 0.114%
    "price_currency",      # 0.141%
    "gallery_city_count",  # 0.217%
    "is_krw",              # 0.234%
    "is_small",            # 0.353%
    "support_factor",      # 0.493%
    # 9-10번 (gallery_type 0.507 / has_international 0.664) = cap 8 / 영역 의 의무 X
]
ITERATION_CAP = 8

# Baseline anchor (Phase 0 fold std mean / Phase 1 사전+사후 정합)
BASELINE_ANCHOR = {
    "cold_ensemble":          38.6224,
    "cold_catboost":          39.5616,
    "cold_xgboost":           39.2000,
    "cold_artsy_catboost":    33.7600,
    "cold_artsy_ensemble":    33.5200,
    "cold_saatchi_catboost":  41.9465,
    "cold_saatchi_ensemble":  41.7400,
    "warm_kfold_xgboost":     9.7140,
    "warm_kfold_ensemble":    10.4680,
    "warm_groupkfold_xgboost": 40.4936,
    "warm_groupkfold_ensemble": 40.2773,
}

REFERENCE_PREREG_S2 = {
    "cold_ensemble_overall": 38.7,
    "cold_catboost": 39.4,
    "warm_xgboost": 9.7,
    "artsy_cold_catboost": 33.5,
    "saatchi_cold_catboost": 41.7,
}

GUARD_LOCKED = {
    "G1_warm_kfold":      {"metric": "warm_kfold_xgboost", "threshold_pp": 0.5},
    "G2_overall_ensemble":{"metric": "cold_ensemble", "threshold_pp": 0.8},
    "G3_artsy_cold":      {"metric": "cold_artsy_ensemble", "threshold_pp": 1.0},
    "G4_saatchi_cold":    {"metric": "cold_saatchi_ensemble", "threshold_pp": 1.0},
}

PASS_CRITERION_PP = 0.05  # Δ Cold + Δ Warm ≤ +0.05
TERMINATION_DELTA_PP = 0.1  # 1 iter Δ Cold ensemble > +0.1 → phase 종료


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


def run_iteration(
    X_full: pd.DataFrame, y: np.ndarray, groups: np.ndarray, source: np.ndarray,
    feature_set: list[str], cat_features: list[str],
    cb_best: dict, xgb_best: dict, *, iter_idx: int, dropped_feature: str,
) -> dict:
    """1 iter = 1 feature 누적 제거 + retrain."""
    t0 = time.time()
    X = X_full[feature_set].copy()
    logger.info(f"\n=== Phase 2 iter {iter_idx} (DROP {dropped_feature}) ===")
    logger.info(f"  feature_set: {len(feature_set)} cols")

    # cold GroupKFold-5
    gkf = GroupKFold(n_splits=5)
    cold_splits = list(gkf.split(X, y, groups))
    cold = _cv_run(X, y, cold_splits, source, cb_best, xgb_best, cat_features, label="GKF")

    # warm slice
    warm_mask = _warm_mask(groups)
    X_warm = X[warm_mask].reset_index(drop=True)
    y_warm = y[warm_mask]
    g_warm = groups[warm_mask]

    # warm KFold-5 (main)
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    warm_kfold_splits = list(kf.split(X_warm, y_warm))
    warm_kfold = _cv_run(X_warm, y_warm, warm_kfold_splits, None, cb_best, xgb_best, cat_features, label="KF")

    # warm GroupKFold-5 (guard)
    gkf2 = GroupKFold(n_splits=5)
    warm_gkfold_splits = list(gkf2.split(X_warm, y_warm, g_warm))
    warm_gkfold = _cv_run(X_warm, y_warm, warm_gkfold_splits, None, cb_best, xgb_best, cat_features, label="wGKF")

    # mean metrics
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
    deltas = {k: round(metrics[k] - BASELINE_ANCHOR[k], 4)
              for k in metrics if metrics[k] is not None and k in BASELINE_ANCHOR}

    # Guard 4
    guards = {}
    for guard_name, gd in GUARD_LOCKED.items():
        delta = deltas.get(gd["metric"])
        guards[guard_name] = {
            "delta": delta,
            "threshold_pp": gd["threshold_pp"],
            "pass": bool(delta is not None and delta <= gd["threshold_pp"]),
        }

    # Local primary check (Δ Cold ≤+0.05 AND Δ Warm ≤+0.05)
    delta_cold = deltas.get("cold_ensemble")
    delta_warm = deltas.get("warm_kfold_xgboost")
    primary_pass = (delta_cold is not None and delta_cold <= PASS_CRITERION_PP
                    and delta_warm is not None and delta_warm <= PASS_CRITERION_PP)
    all_guards_pass = all(g["pass"] for g in guards.values())

    # Termination check (Δ Cold ensemble > +0.1 → phase 종료)
    termination_triggered = (delta_cold is not None and delta_cold > TERMINATION_DELTA_PP)

    iter_pass = primary_pass and all_guards_pass

    elapsed = round(time.time() - t0, 1)
    logger.info(f"  Δ Cold ens={delta_cold:+.3f}  Δ Warm xgb={delta_warm:+.3f}  "
                f"primary_pass={primary_pass}  guards_pass={all_guards_pass}  "
                f"iter_pass={iter_pass}  termination={termination_triggered}  ({elapsed}s)")

    return {
        "iter": iter_idx,
        "dropped_feature": dropped_feature,
        "feature_set": feature_set,
        "n_features": len(feature_set),
        "cold_groupkfold": cold,
        "warm_kfold_main": warm_kfold,
        "warm_groupkfold_guard": warm_gkfold,
        "metrics": metrics,
        "deltas_vs_baseline": deltas,
        "guard_check_locked": guards,
        "primary_pass": primary_pass,
        "all_guards_pass": all_guards_pass,
        "iter_pass": iter_pass,
        "termination_triggered": termination_triggered,
        "elapsed_sec": elapsed,
    }


def main() -> None:
    t0 = time.time()
    logger.info("=" * 70)
    logger.info("Phase 2 — DROP-B (low-importance / 1-by-1 누적 / max 8 iter)")
    logger.info("=" * 70)
    logger.info(f"Candidates (SHAP avg ASC): {DROP_CANDIDATES_ORDERED}")
    logger.info(f"Baseline anchor (primary): Phase 0 fold std mean")
    logger.info(f"Reference (§2 frozen): {REFERENCE_PREREG_S2}")

    best_params = json.loads((ARTIFACTS / "integrated_v3_filtered_tuned_best_params.json").read_text())
    cb_best = best_params["catboost"]
    xgb_best = best_params["xgboost"]

    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].copy()
    X_full, y, groups = prepare_features(df)
    source = df["source"].astype(str).to_numpy()

    # 32 baseline 시작 (Phase 1 carry-forward X)
    feature_set = list(CB_FEATURES)
    iters: list[dict] = []
    phase_terminated = False
    termination_reason = None
    accepted_drops: list[str] = []

    for i, candidate in enumerate(DROP_CANDIDATES_ORDERED[:ITERATION_CAP], 1):
        if candidate not in feature_set:
            logger.warning(f"iter {i}: {candidate} not in feature_set, skipping")
            continue
        # 누적 제거: 직전 PASS 면 누적 / FAIL 면 phase 종료 (다만 본 round 영역 의 의무
        # = 모든 candidate 영역 의 의무 retrain 영역 의 의무 record 영역 의 의무 / FAIL 후
        # 영역 의 의무 영역 의 의무 stop 영역 의 의무).
        candidate_set = [f for f in feature_set if f != candidate]
        cat_features_iter = [c for c in CAT_FEATURES if c in candidate_set]
        result = run_iteration(
            X_full, y, groups, source, candidate_set, cat_features_iter,
            cb_best, xgb_best, iter_idx=i, dropped_feature=candidate,
        )
        iters.append(result)

        # phase 종료 조건: termination_triggered (Δ Cold > +0.1)
        if result["termination_triggered"]:
            phase_terminated = True
            termination_reason = f"iter {i} Δ Cold ensemble {result['deltas_vs_baseline']['cold_ensemble']:+.3f} > +{TERMINATION_DELTA_PP}%p"
            logger.warning(f"\n!!! Phase 2 종료: {termination_reason}")
            break

        # PASS / FAIL 처리
        if result["iter_pass"]:
            feature_set = candidate_set  # 누적 제거 (PASS)
            accepted_drops.append(candidate)
            logger.info(f"  → iter {i} PASS: 누적 제거 ({len(feature_set)} features 남음)")
        else:
            # FAIL but not termination: log only / 다음 iter 시도 X (phase 종료)
            phase_terminated = True
            termination_reason = f"iter {i} primary FAIL or guard FAIL (no termination but stop)"
            logger.warning(f"\n!!! Phase 2 종료 (FAIL): {termination_reason}")
            break

    out = {
        "phase": 2,
        "strategy": "DROP-B (low-importance / 1-by-1 누적)",
        "n_features_before": 32,
        "n_features_after": len(feature_set),
        "candidates_ordered": DROP_CANDIDATES_ORDERED,
        "candidates_processed": len(iters),
        "accepted_drops": accepted_drops,
        "phase_terminated": phase_terminated,
        "termination_reason": termination_reason,
        "best_params": best_params,
        "baseline_anchor": BASELINE_ANCHOR,
        "reference_prereg_s2": REFERENCE_PREREG_S2,
        "guard_locked": GUARD_LOCKED,
        "pass_criterion_pp": PASS_CRITERION_PP,
        "termination_delta_pp": TERMINATION_DELTA_PP,
        "iteration_cap": ITERATION_CAP,
        "iterations": iters,
        "elapsed_sec": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    logger.info(f"\n[OK] {OUT.name} (elapsed {out['elapsed_sec']}s)")

    # Print summary
    print("\n" + "=" * 80)
    print(f"Phase 2 SUMMARY")
    print("=" * 80)
    print(f"\nStarting features: 32")
    print(f"Final features: {len(feature_set)}")
    print(f"Iterations processed: {len(iters)}")
    print(f"Accepted drops: {accepted_drops}")
    print(f"Phase terminated: {phase_terminated}")
    if termination_reason:
        print(f"Reason: {termination_reason}")
    print()
    print(f"{'iter':>4} {'feature':25s} {'Δ Cold':>9s} {'Δ Warm':>9s} {'guards':>8s} {'verdict':>10s}")
    for it in iters:
        d_c = it["deltas_vs_baseline"].get("cold_ensemble", "—")
        d_w = it["deltas_vs_baseline"].get("warm_kfold_xgboost", "—")
        guards_pass = it["all_guards_pass"]
        verdict = "PASS" if it["iter_pass"] else ("TERM" if it["termination_triggered"] else "FAIL")
        print(f"{it['iter']:>4} {it['dropped_feature']:25s} {d_c:>+9.3f} {d_w:>+9.3f} "
              f"{str(guards_pass):>8s} {verdict:>10s}")


if __name__ == "__main__":
    main()
