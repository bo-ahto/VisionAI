"""Phase 1 — DROP-A (placeholder 3 features 제거 / 32 → 29).

prereg §3.2 정합. Decision binding ❌ X.

P2 (코덱스 사전 자문):
  Phase 1 모든 Δ = Phase 0 동일 CV/protocol/best_params rerun mean baseline
  대비 계산. 운영 reported single retrain 수치 = reference only.

Baseline anchor (Phase 0 fold std mean):
  cold_ensemble       = 38.62
  cold_catboost       = 39.56
  cold_xgboost        = 39.20
  cold_artsy_ensemble = 33.52
  cold_saatchi_ensemble = 41.74
  warm_kfold_xgboost  = 9.71
  warm_kfold_ensemble = 10.47
  warm_gkfold_xgboost = 40.49

DROP candidates (literal 4/4 zero / Phase 0 코덱스 GO):
  - ho_price_level
  - medium_price_level
  - profile_completeness
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
OUT = Path(__file__).parent / "phase1_drop_a_results.json"

DROP_FEATURES = ["ho_price_level", "medium_price_level", "profile_completeness"]
PHASE1_FEATURES = [f for f in CB_FEATURES if f not in DROP_FEATURES]
PHASE1_CAT_FEATURES = [c for c in CAT_FEATURES if c in PHASE1_FEATURES]


def _summary_fold(y_true_price: np.ndarray, y_pred_price: np.ndarray) -> dict:
    return {"n": len(y_true_price), "MdAPE": float(_mdape(y_true_price, y_pred_price))}


def _cb_pool(X: pd.DataFrame, y: np.ndarray | None = None) -> Pool:
    cat_idx = [X.columns.get_loc(c) for c in PHASE1_CAT_FEATURES if c in X.columns]
    return Pool(X, label=y, cat_features=cat_idx)


def _cv_run(
    X: pd.DataFrame, y: np.ndarray, splits: list, source: np.ndarray | None,
    cb_params: dict, xgb_params: dict, *, label: str,
) -> dict:
    fold_results: list[dict] = []
    for fold, (tr, te) in enumerate(splits, 1):
        t0 = time.time()
        cb = CatBoostRegressor(
            **cb_params, loss_function="RMSE", verbose=0, random_seed=42,
            allow_writing_files=False,
        )
        cb.fit(_cb_pool(X.iloc[tr], y[tr]))
        cb_pred = cb.predict(_cb_pool(X.iloc[te]))

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
        logger.info(f"  {label} fold {fold}/{len(splits)} done: cb={f['catboost']['MdAPE']:.2f} "
                    f"xgb={f['xgboost']['MdAPE']:.2f} ens={f['ensemble']['MdAPE']:.2f} "
                    f"({f['elapsed_sec']}s)")
    return {"folds": fold_results, "n_total": int(len(y))}


def compute_std(folds: list[dict], path: list[str]) -> dict:
    vals = []
    for f in folds:
        cur = f
        for k in path:
            cur = cur.get(k, {})
        if isinstance(cur, dict) and "MdAPE" in cur:
            vals.append(cur["MdAPE"])
    if not vals:
        return {"std": None, "mean": None, "n_folds": 0, "values": []}
    arr = np.array(vals)
    return {
        "std": float(arr.std(ddof=0)),
        "mean": float(arr.mean()),
        "min": float(arr.min()),
        "max": float(arr.max()),
        "n_folds": len(vals),
        "values": [round(float(v), 3) for v in vals],
    }


# ─── Baseline anchor (Phase 0) ────────────────────────────────────────
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


def main() -> None:
    t0 = time.time()
    logger.info("=" * 70)
    logger.info("Phase 1 — DROP-A (placeholder 3 / 32 → 29)")
    logger.info("=" * 70)
    logger.info(f"DROP features: {DROP_FEATURES}")
    logger.info(f"N features: {len(CB_FEATURES)} → {len(PHASE1_FEATURES)}")

    best_params = json.loads((ARTIFACTS / "integrated_v3_filtered_tuned_best_params.json").read_text())
    cb_best = best_params["catboost"]
    xgb_best = best_params["xgboost"]

    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].copy()
    X_full, y, groups = prepare_features(df)
    source = df["source"].astype(str).to_numpy()

    # Phase 1: 29 features
    X = X_full[PHASE1_FEATURES].copy()
    logger.info(f"Phase 1 features: {len(X.columns)} cols (verified)")
    assert len(X.columns) == 29, f"Expected 29 features, got {len(X.columns)}"

    logger.info("\n--- Cold GroupKFold-5 ---")
    gkf = GroupKFold(n_splits=5)
    cold_splits = list(gkf.split(X, y, groups))
    cold = _cv_run(X, y, cold_splits, source, cb_best, xgb_best, label="GroupKFold")

    logger.info("\n--- Warm slice ---")
    warm_mask = _warm_mask(groups)
    X_warm = X[warm_mask].reset_index(drop=True)
    y_warm = y[warm_mask]
    g_warm = groups[warm_mask]
    logger.info(f"  warm n={len(X_warm)} / artists={len(set(g_warm))}")

    logger.info("\n--- Warm KFold-5 (main) ---")
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    warm_kfold_splits = list(kf.split(X_warm, y_warm))
    warm_kfold = _cv_run(X_warm, y_warm, warm_kfold_splits, None, cb_best, xgb_best, label="kfold")

    logger.info("\n--- Warm GroupKFold-5 (guard) ---")
    gkf2 = GroupKFold(n_splits=5)
    warm_gkfold_splits = list(gkf2.split(X_warm, y_warm, g_warm))
    warm_gkfold = _cv_run(X_warm, y_warm, warm_gkfold_splits, None, cb_best, xgb_best, label="groupkfold")

    # Summary stats
    summary = {
        "cold_catboost":     compute_std(cold["folds"], ["catboost"]),
        "cold_xgboost":      compute_std(cold["folds"], ["xgboost"]),
        "cold_ensemble":     compute_std(cold["folds"], ["ensemble"]),
        "cold_artsy_catboost":   compute_std(cold["folds"], ["artsy_catboost"]),
        "cold_artsy_ensemble":   compute_std(cold["folds"], ["artsy_ensemble"]),
        "cold_saatchi_catboost": compute_std(cold["folds"], ["saatchi_catboost"]),
        "cold_saatchi_ensemble": compute_std(cold["folds"], ["saatchi_ensemble"]),
        "warm_kfold_xgboost":      compute_std(warm_kfold["folds"], ["xgboost"]),
        "warm_kfold_ensemble":     compute_std(warm_kfold["folds"], ["ensemble"]),
        "warm_groupkfold_xgboost": compute_std(warm_gkfold["folds"], ["xgboost"]),
        "warm_groupkfold_ensemble": compute_std(warm_gkfold["folds"], ["ensemble"]),
    }

    # Δ vs baseline anchor
    deltas = {}
    for k, v in summary.items():
        if v["mean"] is None:
            continue
        baseline = BASELINE_ANCHOR.get(k)
        if baseline is None:
            continue
        deltas[k] = {
            "phase1_mean": round(v["mean"], 4),
            "baseline_mean": baseline,
            "delta": round(v["mean"] - baseline, 4),
        }

    # Guard 4 evaluation (locked thresholds)
    GUARD = {
        "G1_warm_kfold": {"metric": "warm_kfold_xgboost", "threshold_pp": 0.5},
        "G2_overall_ensemble": {"metric": "cold_ensemble", "threshold_pp": 0.8},
        "G3_artsy_cold": {"metric": "cold_artsy_ensemble", "threshold_pp": 1.0},
        "G4_saatchi_cold": {"metric": "cold_saatchi_ensemble", "threshold_pp": 1.0},
    }
    guards = {}
    for guard_name, gd in GUARD.items():
        delta = deltas.get(gd["metric"], {}).get("delta", None)
        if delta is None:
            guards[guard_name] = {"delta": None, "threshold_pp": gd["threshold_pp"], "pass": None}
        else:
            guards[guard_name] = {
                "delta": delta,
                "threshold_pp": gd["threshold_pp"],
                "pass": bool(delta <= gd["threshold_pp"]),
            }

    # Local primary (Δ Cold ensemble) check (PASS criterion: ≤ +0.1%p)
    local_primary_delta = deltas.get("cold_ensemble", {}).get("delta", None)
    local_warm_delta = deltas.get("warm_kfold_xgboost", {}).get("delta", None)
    primary_pass = (local_primary_delta is not None and local_primary_delta <= 0.1
                    and local_warm_delta is not None and local_warm_delta <= 0.1)

    all_guards_pass = all(g.get("pass") for g in guards.values() if g.get("pass") is not None)

    verdict = "PASS" if (primary_pass and all_guards_pass) else "FAIL"

    out = {
        "phase": 1,
        "strategy": "DROP-A",
        "n_features_before": 32,
        "n_features_after": 29,
        "features_dropped": DROP_FEATURES,
        "best_params": best_params,
        "cold_groupkfold": cold,
        "warm_kfold_main": warm_kfold,
        "warm_groupkfold_guard": warm_gkfold,
        "summary_std": summary,
        "deltas_vs_baseline_anchor": deltas,
        "baseline_anchor": BASELINE_ANCHOR,
        "guard_check_locked": guards,
        "primary_pass": primary_pass,
        "all_guards_pass": all_guards_pass,
        "verdict": verdict,
        "elapsed_sec": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    logger.info(f"\n[OK] {OUT.name} (elapsed {out['elapsed_sec']}s)")

    # Print summary
    print("\n" + "=" * 70)
    print(f"Phase 1 RESULTS (32 → 29 / DROP {DROP_FEATURES})")
    print("=" * 70)
    print(f"\n{'metric':30s} {'phase1':>10s} {'baseline':>10s} {'Δ':>9s}")
    for k, d in deltas.items():
        print(f"{k:30s} {d['phase1_mean']:>10.3f} {d['baseline_mean']:>10.3f} {d['delta']:>+9.3f}")
    print()
    print("=== Guard 4 (locked) ===")
    for guard_name, g in guards.items():
        sym = "✓" if g["pass"] else "✗"
        print(f"  {sym} {guard_name}: Δ={g['delta']:+.3f}%p (threshold ≤+{g['threshold_pp']}%p)")
    print()
    print(f"=== PASS criterion (Δ Cold ≤ +0.1 AND Δ Warm ≤ +0.1) ===")
    print(f"  Δ Cold ensemble = {local_primary_delta:+.3f}%p")
    print(f"  Δ Warm xgboost  = {local_warm_delta:+.3f}%p")
    print(f"  primary_pass: {primary_pass}")
    print(f"\n=== VERDICT: {verdict} ===")


if __name__ == "__main__":
    main()
