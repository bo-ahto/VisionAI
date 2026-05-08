"""Phase 0.D — SHAP + Permutation importance.

Decision binding ❌ X / read-only.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import shap
import xgboost as xgb
from catboost import CatBoostRegressor, Pool
from sklearn.inspection import permutation_importance
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
OUT_DIR = Path(__file__).parent
OUT = OUT_DIR / "phase0_importance_shap_permutation.json"


def _mdape_scorer(estimator, X, y):
    pred = estimator.predict(X)
    return -_mdape(y.values if hasattr(y, "values") else y, pred)


def main() -> None:
    t0 = time.time()
    logger.info("=" * 70)
    logger.info("Phase 0.D — SHAP + Permutation Importance")
    logger.info("=" * 70)

    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].copy()
    X, y, groups = prepare_features(df)
    source = df["source"].astype(str).to_numpy()
    logger.info(f"Loaded {len(df)} rows, {len(CB_FEATURES)} features")

    # Models load
    cb = CatBoostRegressor()
    cb.load_model(str(ARTIFACTS / "integrated_v3_filtered_tuned_catboost.cbm"))

    booster = xgb.Booster()
    booster.load_model(str(ARTIFACTS / "integrated_v3_filtered_tuned_xgboost.json"))

    # Pool 영역 의 의무 = CatBoost 영역 의 의무 (cat features 영역 의 의무 정합)
    cat_idx = [X.columns.get_loc(c) for c in CAT_FEATURES if c in X.columns]
    pool = Pool(X, y, cat_features=cat_idx)

    # ─── SHAP TreeSHAP (CatBoost) ─────────────────────────────────────
    logger.info("--- SHAP TreeSHAP (CatBoost) ---")
    t1 = time.time()
    cb_shap = cb.get_feature_importance(data=pool, type="ShapValues")
    # cb_shap shape: (n_rows, n_features+1) with bias column at end
    cb_shap_values = cb_shap[:, :-1]  # exclude bias
    cb_shap_mean_abs = np.abs(cb_shap_values).mean(axis=0)
    cb_shap_total = cb_shap_mean_abs.sum() or 1.0
    cb_shap_pct = {f: float(v / cb_shap_total * 100) for f, v in zip(CB_FEATURES, cb_shap_mean_abs)}
    logger.info(f"  CB SHAP done in {time.time() - t1:.1f}s")

    # ─── SHAP TreeSHAP (XGBoost) ──────────────────────────────────────
    logger.info("--- SHAP TreeSHAP (XGBoost) ---")
    t1 = time.time()
    # XGBoost 영역 의 의무 label encode (full data / artifact label_maps 영역)
    label_maps_path = ARTIFACTS / "integrated_v3_filtered_tuned_xgboost_label_maps.json"
    label_maps = json.loads(label_maps_path.read_text())
    X_xgb_le = X.copy()
    for col in CAT_FEATURES:
        if col in X_xgb_le.columns and col in label_maps:
            mapping = label_maps[col]
            unseen_idx = len(mapping)
            X_xgb_le[col] = X_xgb_le[col].map(mapping).fillna(unseen_idx).astype(float)
    xgb_explainer = shap.TreeExplainer(booster)
    xgb_shap_values = xgb_explainer.shap_values(X_xgb_le)
    xgb_shap_mean_abs = np.abs(xgb_shap_values).mean(axis=0)
    xgb_shap_total = xgb_shap_mean_abs.sum() or 1.0
    xgb_shap_pct = {f: float(v / xgb_shap_total * 100) for f, v in zip(CB_FEATURES, xgb_shap_mean_abs)}
    logger.info(f"  XGB SHAP done in {time.time() - t1:.1f}s")

    # ─── Permutation Importance (CatBoost / cold subset) ──────────────
    logger.info("--- Permutation Importance (CatBoost / sample 5000) ---")
    t1 = time.time()
    rng = np.random.RandomState(42)
    sample_idx = rng.choice(len(X), size=min(5000, len(X)), replace=False)
    X_sample = X.iloc[sample_idx]
    y_sample = y.iloc[sample_idx] if hasattr(y, "iloc") else pd.Series(y).iloc[sample_idx]

    pi_cb = permutation_importance(
        cb, X_sample, y_sample,
        scoring=_mdape_scorer,
        n_repeats=5, random_state=42, n_jobs=1,
    )
    pi_cb_total = pi_cb.importances_mean.sum() or 1.0
    pi_cb_pct = {f: float(v / pi_cb_total * 100) for f, v in zip(CB_FEATURES, pi_cb.importances_mean)}
    logger.info(f"  PI CB done in {time.time() - t1:.1f}s")

    # ─── 정량 영역 의 의무 dump ──────────────────────────────────────
    out = {
        "phase": 0,
        "method": "SHAP TreeSHAP + Permutation Importance",
        "n_features": len(CB_FEATURES),
        "features": CB_FEATURES,
        "catboost_shap_pct": cb_shap_pct,
        "xgboost_shap_pct": xgb_shap_pct,
        "permutation_catboost_pct": pi_cb_pct,
        "permutation_catboost_raw": {f: float(v) for f, v in zip(CB_FEATURES, pi_cb.importances_mean)},
        "permutation_catboost_std": {f: float(v) for f, v in zip(CB_FEATURES, pi_cb.importances_std)},
        "elapsed_sec": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    logger.info(f"\n[OK] {OUT.name} (elapsed {out['elapsed_sec']}s)")

    print("\n=== CatBoost SHAP (top 10) ===")
    for f, v in sorted(cb_shap_pct.items(), key=lambda x: -x[1])[:10]:
        print(f"  {f:30s} {v:>7.2f}%")
    print("\n=== XGBoost SHAP (top 10) ===")
    for f, v in sorted(xgb_shap_pct.items(), key=lambda x: -x[1])[:10]:
        print(f"  {f:30s} {v:>7.2f}%")
    print("\n=== Permutation CatBoost (top 10) ===")
    for f, v in sorted(pi_cb_pct.items(), key=lambda x: -x[1])[:10]:
        print(f"  {f:30s} {v:>7.2f}%")


if __name__ == "__main__":
    main()
