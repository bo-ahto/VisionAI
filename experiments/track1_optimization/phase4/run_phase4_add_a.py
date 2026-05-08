"""Phase 4 — ADD-A (interaction / 1-by-1 sequential 누적 / cap 6).

prereg §3.5 정합. Decision binding ❌ X.

Phase 4.A 코덱스 사전 자문 = NEEDS FIX (P1) → fix 적용:
1. termination = cap 6 만 (Δ Cold > +0.1 hard stop X / prereg ADD-A 영역 의 의무
   영역 의 의무 termination rule 영역 의 의무 영역 의 의무 X)
2. candidate 3 (ln_followers × medium_category) = 보류 (label_encode 곱셈 비권고 /
   post-hoc note 영역 의 의무)
   → candidates = 2 영역 의 의무

Method:
- baseline = 32 (Phase 1+2+3 carry-forward 모두 X)
- 후보 (prereg literal 영역 의 의무 1→2):
  1. career_stage × gallery_tier (numeric × numeric)
  2. artist_total_works × ho     (numeric × numeric)
- 1 interaction / 1 iteration / sequential 누적
- iteration cap = 6 (다만 candidates = 2 / max 2 iter)
- Local primary: dual-primary
- PASS: (Δ Cold ≤ -0.1 OR Δ Warm ≤ -0.1) AND Guard 4 PASS
- termination: cap 6 도달 OR all candidates exhausted
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
OUT = Path(__file__).parent / "phase4_add_a_results.json"

# Phase 4 후보 (prereg literal 1→2 / candidate 3 보류)
INTERACTIONS = [
    {
        "name": "career_stage_x_gallery_tier",
        "feat_a": "career_stage",
        "feat_b": "gallery_tier",
        "type": "numeric_x_numeric",
    },
    {
        "name": "artist_total_works_x_ho",
        "feat_a": "artist_total_works",
        "feat_b": "ho",
        "type": "numeric_x_numeric",
    },
]
ITERATION_CAP = 6  # prereg / candidates = 2

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

GUARD_LOCKED = {
    "G1_warm_kfold":      {"metric": "warm_kfold_xgboost", "threshold_pp": 0.5},
    "G2_overall_ensemble":{"metric": "cold_ensemble", "threshold_pp": 0.8},
    "G3_artsy_cold":      {"metric": "cold_artsy_ensemble", "threshold_pp": 1.0},
    "G4_saatchi_cold":    {"metric": "cold_saatchi_ensemble", "threshold_pp": 1.0},
}

# ADD-A dual-primary PASS criterion (Δ Cold OR Δ Warm 개선)
PRIMARY_IMPROVEMENT_PP = -0.1  # 개선 영역 의 의무 영역 의 의무 -0.1%p (작을수록 좋음)


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


def add_interaction(X_full: pd.DataFrame, interaction: dict) -> pd.DataFrame:
    """numeric × numeric interaction term 추가."""
    X = X_full.copy()
    a = pd.to_numeric(X[interaction["feat_a"]], errors="coerce").fillna(0.0)
    b = pd.to_numeric(X[interaction["feat_b"]], errors="coerce").fillna(0.0)
    X[interaction["name"]] = (a * b).astype(float)
    return X


def run_iteration(
    X_full: pd.DataFrame, y: np.ndarray, groups: np.ndarray, source: np.ndarray,
    feature_set: list[str], cat_features: list[str],
    cb_best: dict, xgb_best: dict, *, iter_idx: int, added_interaction: dict,
) -> dict:
    t0 = time.time()
    X = X_full[feature_set].copy()
    logger.info(f"\n=== Phase 4 iter {iter_idx} (ADD {added_interaction['name']}) ===")
    logger.info(f"  feature_set: {len(feature_set)} cols")

    gkf = GroupKFold(n_splits=5)
    cold = _cv_run(X, y, list(gkf.split(X, y, groups)), source, cb_best, xgb_best, cat_features, label="GKF")

    warm_mask = _warm_mask(groups)
    X_warm = X[warm_mask].reset_index(drop=True)
    y_warm = y[warm_mask]
    g_warm = groups[warm_mask]

    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    warm_kfold = _cv_run(X_warm, y_warm, list(kf.split(X_warm, y_warm)), None, cb_best, xgb_best, cat_features, label="KF")

    gkf2 = GroupKFold(n_splits=5)
    warm_gkfold = _cv_run(X_warm, y_warm, list(gkf2.split(X_warm, y_warm, g_warm)), None, cb_best, xgb_best, cat_features, label="wGKF")

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

    guards = {}
    for guard_name, gd in GUARD_LOCKED.items():
        delta = deltas.get(gd["metric"])
        guards[guard_name] = {
            "delta": delta,
            "threshold_pp": gd["threshold_pp"],
            "pass": bool(delta is not None and delta <= gd["threshold_pp"]),
        }

    delta_cold = deltas.get("cold_ensemble")
    delta_warm = deltas.get("warm_kfold_xgboost")
    # ADD-A dual-primary: Δ Cold ≤ -0.1 OR Δ Warm ≤ -0.1
    primary_pass = (
        (delta_cold is not None and delta_cold <= PRIMARY_IMPROVEMENT_PP)
        or (delta_warm is not None and delta_warm <= PRIMARY_IMPROVEMENT_PP)
    )
    all_guards_pass = all(g["pass"] for g in guards.values())
    iter_pass = primary_pass and all_guards_pass

    elapsed = round(time.time() - t0, 1)
    logger.info(f"  Δ Cold ens={delta_cold:+.3f}  Δ Warm xgb={delta_warm:+.3f}  "
                f"primary_pass={primary_pass}  guards_pass={all_guards_pass}  "
                f"iter_pass={iter_pass}  ({elapsed}s)")

    return {
        "iter": iter_idx,
        "added_interaction": added_interaction,
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
        "elapsed_sec": elapsed,
    }


def main() -> None:
    t0 = time.time()
    logger.info("=" * 70)
    logger.info("Phase 4 — ADD-A (interaction / sequential 누적 / cap 6)")
    logger.info("=" * 70)
    logger.info(f"Candidates (literal 1→2 / candidate 3 보류): {[i['name'] for i in INTERACTIONS]}")

    best_params = json.loads((ARTIFACTS / "integrated_v3_filtered_tuned_best_params.json").read_text())
    cb_best = best_params["catboost"]
    xgb_best = best_params["xgboost"]

    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].copy()
    X_full, y, groups = prepare_features(df)
    source = df["source"].astype(str).to_numpy()

    # 32 baseline 시작
    feature_set = list(CB_FEATURES)
    X_aug = X_full.copy()
    iters: list[dict] = []
    accepted_interactions: list[str] = []

    for i, interaction in enumerate(INTERACTIONS[:ITERATION_CAP], 1):
        # interaction term 추가 (sequential 누적)
        X_aug = add_interaction(X_aug, interaction)
        candidate_set = feature_set + [interaction["name"]]
        cat_features_iter = [c for c in CAT_FEATURES if c in candidate_set]

        result = run_iteration(
            X_aug, y, groups, source, candidate_set, cat_features_iter,
            cb_best, xgb_best, iter_idx=i, added_interaction=interaction,
        )
        iters.append(result)

        if result["iter_pass"]:
            feature_set = candidate_set
            accepted_interactions.append(interaction["name"])
            logger.info(f"  → iter {i} PASS: 누적 추가 ({len(feature_set)} features)")
        else:
            logger.info(f"  → iter {i} FAIL: 영역 의 의무 추가 X (rollback / 다음 candidate)")
            # rollback: X_aug 영역 의 의무 영역 의 의무 column 영역 의 의무 영역 의 의무 제거
            X_aug = X_aug.drop(columns=[interaction["name"]])

    # cap 6 / candidates = 2 / 영역 의 의무 영역 의 의무 모두 영역 의 의무 영역 의 의무 영역 의 의무
    out = {
        "phase": 4,
        "strategy": "ADD-A (interaction / sequential 누적)",
        "n_features_before": 32,
        "n_features_after": len(feature_set),
        "candidates_total": len(INTERACTIONS),
        "candidates_processed": len(iters),
        "accepted_interactions": accepted_interactions,
        "candidate_3_deferred": "ln_followers × medium_category (label_encode 비권고 / post-hoc only)",
        "best_params": best_params,
        "baseline_anchor": BASELINE_ANCHOR,
        "guard_locked": GUARD_LOCKED,
        "primary_improvement_pp": PRIMARY_IMPROVEMENT_PP,
        "iteration_cap": ITERATION_CAP,
        "iterations": iters,
        "elapsed_sec": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    logger.info(f"\n[OK] {OUT.name} (elapsed {out['elapsed_sec']}s)")

    print("\n" + "=" * 80)
    print(f"Phase 4 SUMMARY")
    print("=" * 80)
    print(f"\nStarting features: 32")
    print(f"Final features: {len(feature_set)}")
    print(f"Iterations processed: {len(iters)}")
    print(f"Accepted interactions: {accepted_interactions}")
    print()
    print(f"{'iter':>4} {'interaction':30s} {'Δ Cold':>9s} {'Δ Warm':>9s} {'guards':>8s} {'verdict':>10s}")
    for it in iters:
        d_c = it["deltas_vs_baseline"].get("cold_ensemble", "—")
        d_w = it["deltas_vs_baseline"].get("warm_kfold_xgboost", "—")
        guards_pass = it["all_guards_pass"]
        verdict = "PASS" if it["iter_pass"] else "FAIL"
        print(f"{it['iter']:>4} {it['added_interaction']['name']:30s} {d_c:>+9.3f} {d_w:>+9.3f} "
              f"{str(guards_pass):>8s} {verdict:>10s}")


if __name__ == "__main__":
    main()
