"""Phase 0.C — baseline fold-level std (운영 best_params 영역 retrain 5 fold).

prereg §4.2 정합. Decision binding ❌ X / 운영 artifact 영역 의 의무 변경 X.
산출: cold GroupKFold-5 + warm KFold-5 + warm GroupKFold-5 (guard) 영역 의 fold-level MdAPE std.
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
from catboost import CatBoostRegressor
from sklearn.model_selection import GroupKFold, KFold

REPO = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from train_primary_market_v3_filtered import (  # noqa: E402
    CB_FEATURES,
    CAT_FEATURES,
    _cb_pool,
    _label_encode_xgb,
    _mdape,
    _warm_mask,
    load_data,
    prepare_features,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ARTIFACTS = REPO / "model_test_results"
OUT = Path(__file__).parent / "phase0_baseline_fold_std.json"


def _summary_fold(y_true_price: np.ndarray, y_pred_price: np.ndarray) -> dict:
    """fold-level summary."""
    return {
        "n": len(y_true_price),
        "MdAPE": float(_mdape(y_true_price, y_pred_price)),
    }


def cv_groupkfold_fold_metrics(
    X: pd.DataFrame, y: np.ndarray, groups: np.ndarray, source: np.ndarray,
    cb_params: dict, xgb_params: dict,
) -> dict:
    """5-fold GroupKFold with per-fold MdAPE dump."""
    gkf = GroupKFold(n_splits=5)
    fold_results: list[dict] = []
    for fold, (tr, te) in enumerate(gkf.split(X, y, groups), 1):
        t0 = time.time()
        # CatBoost
        cb = CatBoostRegressor(
            **cb_params, loss_function="RMSE", verbose=0, random_seed=42,
            allow_writing_files=False,
        )
        cb.fit(_cb_pool(X.iloc[tr], y[tr]))
        cb_pred = cb.predict(_cb_pool(X.iloc[te]))

        # XGBoost
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

        src_te = source[te]
        f = {
            "fold": fold,
            "n_train": int(len(tr)),
            "n_test": int(len(te)),
            "catboost": _summary_fold(y_te_price, cb_price),
            "xgboost": _summary_fold(y_te_price, xgb_price),
            "ensemble": _summary_fold(y_te_price, ens_price),
            "elapsed_sec": round(time.time() - t0, 1),
        }
        for src_name in sorted(set(src_te)):
            mask = src_te == src_name
            if mask.sum() == 0:
                continue
            f[f"{src_name}_catboost"] = _summary_fold(y_te_price[mask], cb_price[mask])
            f[f"{src_name}_ensemble"] = _summary_fold(y_te_price[mask], ens_price[mask])
        fold_results.append(f)
        logger.info(f"  GroupKFold fold {fold}/5 done: cb={f['catboost']['MdAPE']:.2f} "
                    f"xgb={f['xgboost']['MdAPE']:.2f} ens={f['ensemble']['MdAPE']:.2f} "
                    f"({f['elapsed_sec']}s)")
    return {"folds": fold_results, "n_total": int(len(y))}


def cv_kfold_fold_metrics(
    X: pd.DataFrame, y: np.ndarray, cb_params: dict, xgb_params: dict,
    *, kind: str = "kfold", groups: np.ndarray | None = None,
) -> dict:
    """5-fold KFold (or GroupKFold guard) with per-fold MdAPE dump."""
    if kind == "kfold":
        cv = KFold(n_splits=5, shuffle=True, random_state=42)
        splits = list(cv.split(X, y))
    elif kind == "groupkfold":
        assert groups is not None
        cv = GroupKFold(n_splits=5)
        splits = list(cv.split(X, y, groups))
    else:
        raise ValueError(kind)

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
        ens_price = np.exp((cb_pred + xgb_pred) / 2)

        f = {
            "fold": fold,
            "n_train": int(len(tr)),
            "n_test": int(len(te)),
            "catboost": _summary_fold(y_te_price, np.exp(cb_pred)),
            "xgboost": _summary_fold(y_te_price, np.exp(xgb_pred)),
            "ensemble": _summary_fold(y_te_price, ens_price),
            "elapsed_sec": round(time.time() - t0, 1),
        }
        fold_results.append(f)
        logger.info(f"  {kind} fold {fold}/5 done: cb={f['catboost']['MdAPE']:.2f} "
                    f"xgb={f['xgboost']['MdAPE']:.2f} ens={f['ensemble']['MdAPE']:.2f} "
                    f"({f['elapsed_sec']}s)")
    return {"folds": fold_results, "n_total": int(len(y))}


def compute_std(folds: list[dict], path: list[str]) -> dict:
    """fold-level std 산출."""
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
    logger.info("Phase 0.C — Baseline fold-level std")
    logger.info("=" * 70)

    best_params = json.loads((ARTIFACTS / "integrated_v3_filtered_tuned_best_params.json").read_text())
    cb_best = best_params["catboost"]
    xgb_best = best_params["xgboost"]
    logger.info(f"CB params: {cb_best}")
    logger.info(f"XGB params: {xgb_best}")

    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].copy()
    X, y, groups = prepare_features(df)
    source = df["source"].astype(str).to_numpy()

    logger.info(f"\n--- Cold GroupKFold-5 ---")
    cold = cv_groupkfold_fold_metrics(X, y, groups, source, cb_best, xgb_best)

    logger.info(f"\n--- Warm slice (작품수 >= 5) ---")
    warm_mask = _warm_mask(groups)
    X_warm, y_warm, g_warm = X[warm_mask].reset_index(drop=True), y[warm_mask], groups[warm_mask]
    logger.info(f"  warm n={len(X_warm)} / artists={len(set(g_warm))}")

    logger.info(f"\n--- Warm KFold-5 (main) ---")
    warm_kfold = cv_kfold_fold_metrics(X_warm, y_warm, cb_best, xgb_best, kind="kfold")

    logger.info(f"\n--- Warm GroupKFold-5 (guard) ---")
    warm_gkfold = cv_kfold_fold_metrics(X_warm, y_warm, cb_best, xgb_best, kind="groupkfold", groups=g_warm)

    out = {
        "phase": 0,
        "method": "fold-level std (운영 best_params retrain 5 fold)",
        "best_params": best_params,
        "cold_groupkfold": cold,
        "warm_kfold_main": warm_kfold,
        "warm_groupkfold_guard": warm_gkfold,
        "summary_std": {
            "cold_catboost": compute_std(cold["folds"], ["catboost"]),
            "cold_xgboost": compute_std(cold["folds"], ["xgboost"]),
            "cold_ensemble": compute_std(cold["folds"], ["ensemble"]),
            "cold_artsy_catboost": compute_std(cold["folds"], ["artsy_catboost"]),
            "cold_saatchi_catboost": compute_std(cold["folds"], ["saatchi_catboost"]),
            "cold_artsy_ensemble": compute_std(cold["folds"], ["artsy_ensemble"]),
            "cold_saatchi_ensemble": compute_std(cold["folds"], ["saatchi_ensemble"]),
            "warm_kfold_xgboost": compute_std(warm_kfold["folds"], ["xgboost"]),
            "warm_kfold_ensemble": compute_std(warm_kfold["folds"], ["ensemble"]),
            "warm_groupkfold_xgboost": compute_std(warm_gkfold["folds"], ["xgboost"]),
            "warm_groupkfold_ensemble": compute_std(warm_gkfold["folds"], ["ensemble"]),
        },
        "elapsed_sec": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    logger.info(f"\n[OK] {OUT.name} (elapsed {out['elapsed_sec']}s)")

    print("\n=== fold-level std summary ===")
    for k, v in out["summary_std"].items():
        if v["std"] is not None:
            print(f"  {k:30s} mean={v['mean']:>6.2f} std={v['std']:>5.3f} "
                  f"range=[{v['min']:.2f}, {v['max']:.2f}] (n={v['n_folds']})")


if __name__ == "__main__":
    main()
