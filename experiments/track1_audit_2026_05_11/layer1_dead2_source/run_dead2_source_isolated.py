"""Layer 1+ isolated cycle — dead 2 + source 제거 (32 → 29).

User 결정: source feature는 서비스 운영에서 user-controllable 아님 (default "manual" / mismatch).
Codex R1 검수: source 제거 isolated cycle 실행 → B anchor 대비 비교 → 교체 여부 결정.

Drops: ho_price_level, medium_price_level (dead) + source (train/serve mismatch)
Categorical: 6 → 5 (source 제거)
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
    _mdape,
    _warm_mask,
    load_data,
    prepare_features,
)


def _label_encode_xgb_local(
    X_train: pd.DataFrame, X_test: pd.DataFrame, cat_cols: list,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, dict[str, int]]]:
    X_train_e = X_train.copy()
    X_test_e = X_test.copy()
    label_maps: dict[str, dict[str, int]] = {}
    for col in cat_cols:
        if col not in X_train_e.columns:
            continue
        train_vals = X_train_e[col].unique()
        mapping = {v: i for i, v in enumerate(sorted(train_vals))}
        unseen_idx = len(mapping)
        label_maps[col] = mapping
        X_train_e[col] = X_train_e[col].map(mapping).astype(float)
        X_test_e[col] = X_test_e[col].map(mapping).fillna(unseen_idx).astype(float)
    return X_train_e, X_test_e, label_maps

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ARTIFACTS = REPO / "model_test_results"
OUT = Path(__file__).parent / "layer1_dead2_source_results.json"

DROP_FEATURES = ["ho_price_level", "medium_price_level", "source"]
NEW_FEATURES = [f for f in CB_FEATURES if f not in DROP_FEATURES]
NEW_CAT_FEATURES = [c for c in CAT_FEATURES if c in NEW_FEATURES]

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
}


def _summary_fold(y_true_price: np.ndarray, y_pred_price: np.ndarray) -> dict:
    return {"n": len(y_true_price), "MdAPE": float(_mdape(y_true_price, y_pred_price))}


def _cb_pool(X: pd.DataFrame, y: np.ndarray | None = None) -> Pool:
    cat_idx = [X.columns.get_loc(c) for c in NEW_CAT_FEATURES if c in X.columns]
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

        Xtr_e, Xte_e, _ = _label_encode_xgb_local(X.iloc[tr], X.iloc[te], NEW_CAT_FEATURES)
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


def main() -> None:
    t0 = time.time()
    logger.info("=" * 70)
    logger.info("Layer 1+ isolated — Dead 2 + Source 제거 (32 → 29)")
    logger.info("=" * 70)
    logger.info(f"DROP features: {DROP_FEATURES}")
    logger.info(f"N features: {len(CB_FEATURES)} → {len(NEW_FEATURES)}")
    logger.info(f"Categorical: {len(CAT_FEATURES)} → {len(NEW_CAT_FEATURES)}")

    best_params = json.loads((ARTIFACTS / "integrated_v3_filtered_tuned_best_params.json").read_text())
    cb_best = best_params["catboost"]
    xgb_best = best_params["xgboost"]

    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].copy()
    X_full, y, groups = prepare_features(df)
    source_arr = df["source"].astype(str).to_numpy()  # eval slice 용도 (input X)

    X = X_full[NEW_FEATURES].copy()
    logger.info(f"Active features: {len(X.columns)} cols")
    assert len(X.columns) == 29, f"Expected 29 features, got {len(X.columns)}"
    assert "source" not in X.columns, "source must be excluded from model input"

    logger.info("\n--- Cold GroupKFold-5 ---")
    gkf = GroupKFold(n_splits=5)
    cold_splits = list(gkf.split(X, y, groups))
    cold = _cv_run(X, y, cold_splits, source_arr, cb_best, xgb_best, label="GroupKFold")

    logger.info("\n--- Warm slice ---")
    warm_mask = _warm_mask(groups)
    X_warm = X[warm_mask].reset_index(drop=True)
    y_warm = y[warm_mask]
    g_warm = groups[warm_mask]
    logger.info(f"  warm n={len(X_warm)} / artists={len(set(g_warm))}")

    logger.info("\n--- Warm KFold-5 ---")
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    warm_kfold_splits = list(kf.split(X_warm, y_warm))
    warm_kfold = _cv_run(X_warm, y_warm, warm_kfold_splits, None, cb_best, xgb_best, label="kfold")

    summary = {
        "cold_catboost":     compute_std(cold["folds"], ["catboost"]),
        "cold_xgboost":      compute_std(cold["folds"], ["xgboost"]),
        "cold_ensemble":     compute_std(cold["folds"], ["ensemble"]),
        "cold_artsy_catboost":   compute_std(cold["folds"], ["artsy_catboost"]),
        "cold_artsy_ensemble":   compute_std(cold["folds"], ["artsy_ensemble"]),
        "cold_saatchi_catboost": compute_std(cold["folds"], ["saatchi_catboost"]),
        "cold_saatchi_ensemble": compute_std(cold["folds"], ["saatchi_ensemble"]),
        "warm_kfold_xgboost":  compute_std(warm_kfold["folds"], ["xgboost"]),
        "warm_kfold_ensemble": compute_std(warm_kfold["folds"], ["ensemble"]),
    }

    deltas = {}
    for k, v in summary.items():
        if v["mean"] is None:
            continue
        baseline = BASELINE_ANCHOR.get(k)
        if baseline is None:
            continue
        deltas[k] = {
            "isolated_mean": round(v["mean"], 4),
            "baseline_mean": baseline,
            "delta": round(v["mean"] - baseline, 4),
        }

    local_primary_delta = deltas.get("cold_ensemble", {}).get("delta", None)
    local_warm_delta = deltas.get("warm_kfold_xgboost", {}).get("delta", None)
    cold_std = summary["cold_ensemble"]["std"] or 0
    delta_in_noise = abs(local_primary_delta or 0) < 0.5 * cold_std

    out = {
        "cycle": "Layer 1+ isolated — Dead 2 + Source 제거",
        "n_features_before": 32,
        "n_features_after": 29,
        "features_dropped": DROP_FEATURES,
        "rationale": "source feature는 서비스 운영에서 user-controllable 아님 (train/serve mismatch)",
        "best_params": best_params,
        "cold_groupkfold": cold,
        "warm_kfold": warm_kfold,
        "summary_std": summary,
        "deltas_vs_baseline_anchor": deltas,
        "baseline_anchor": BASELINE_ANCHOR,
        "delta_cold_ensemble_pp": local_primary_delta,
        "delta_warm_xgb_pp": local_warm_delta,
        "cold_ensemble_std_pp": round(cold_std, 4),
        "delta_within_noise": delta_in_noise,
        "verdict": "PASS_WITHIN_NOISE" if delta_in_noise else "FAIL_BEYOND_NOISE",
        "elapsed_sec": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    logger.info(f"\n[OK] {OUT.name} (elapsed {out['elapsed_sec']}s)")

    print("\n" + "=" * 70)
    print(f"Layer 1+ isolated RESULTS (32 → 29 / DROP {DROP_FEATURES})")
    print("=" * 70)
    print(f"\n{'metric':30s} {'isolated':>10s} {'baseline':>10s} {'Δ':>9s}")
    for k, d in deltas.items():
        print(f"{k:30s} {d['isolated_mean']:>10.3f} {d['baseline_mean']:>10.3f} {d['delta']:>+9.3f}")
    print()
    print(f"=== Noise check (Δ vs 0.5*std) ===")
    print(f"  Δ Cold ensemble = {local_primary_delta:+.3f}pp")
    print(f"  Cold std        = {cold_std:.3f}pp")
    print(f"  Within noise    = {delta_in_noise}")
    print(f"\n=== VERDICT: {out['verdict']} ===")


if __name__ == "__main__":
    main()
