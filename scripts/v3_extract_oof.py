"""v3 Group 1 인프라: OOF 예측 추출.

production tuned best_params로 GroupKFold (cold path) + KFold (warm path) OOF
예측을 산출하여 npz로 저장한다. v2 metrics.json의 9.7% / 38.3% 산출 경로와 동일
(`tune_primary_market_v3_filtered.py:_final_cv_groupkfold_5/_final_cv_kfold_5`).

용도:
- Group 1.1 Bootstrap CI for MdAPE
- Group 1.2 v1 vs v2 paired test
- Group 1.6 Calibration plot
- Group 1.7 Residual analysis

산출물:
    model_test_results/v3_diagnostics/oof_predictions.npz
        - y_actual_ln          (n,)         : ln_price 실제값
        - cb_preds_gkf_ln      (n,)         : CatBoost GroupKFold OOF (cold)
        - xgb_preds_gkf_ln     (n,)         : XGBoost GroupKFold OOF (cold)
        - groups               (n,)         : artist_slug
        - source               (n,)         : artsy / saatchi
        - warm_mask            (n_warm,)    : warm slice 인덱스 (>=5건)
        - cb_preds_kf_ln       (n_warm,)    : CatBoost KFold OOF (warm only)
        - xgb_preds_kf_ln      (n_warm,)    : XGBoost KFold OOF (warm only)

Usage:
    PYTHONPATH=src python3 scripts/v3_extract_oof.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from catboost import CatBoostRegressor
from sklearn.model_selection import GroupKFold, KFold

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from train_primary_market_v3_filtered import (
    CB_FEATURES,
    _cb_pool,
    _label_encode_xgb,
    _warm_mask,
    load_data,
    prepare_features,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUT_DIR = ROOT / "model_test_results"
DIAG_DIR = OUT_DIR / "v3_diagnostics"
RANDOM_SEED = 42


def _load_best_params() -> tuple[dict, dict]:
    path = OUT_DIR / "integrated_v3_filtered_tuned_best_params.json"
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data["catboost"], data["xgboost"]


def gkf_oof(
    X: pd.DataFrame, y: np.ndarray, groups: np.ndarray,
    cb_params: dict, xgb_params: dict, n_splits: int = 5,
) -> tuple[np.ndarray, np.ndarray]:
    """GroupKFold OOF 산출 (cold path 평가)."""
    gkf = GroupKFold(n_splits=n_splits)
    cb_preds = np.zeros(len(y))
    xgb_preds = np.zeros(len(y))
    for fold, (tr, te) in enumerate(gkf.split(X, y, groups), 1):
        logger.info("[GKF %d/%d] train=%d test=%d", fold, n_splits, len(tr), len(te))
        cb = CatBoostRegressor(
            **cb_params, loss_function="RMSE", verbose=0,
            random_seed=RANDOM_SEED, allow_writing_files=False,
        )
        cb.fit(_cb_pool(X.iloc[tr], y[tr]))
        cb_preds[te] = cb.predict(_cb_pool(X.iloc[te]))

        Xtr_e, Xte_e, _ = _label_encode_xgb(X.iloc[tr], X.iloc[te])
        xgb_p = {k: v for k, v in xgb_params.items() if k != "num_boost_round"}
        m = xgb.train(
            params={**xgb_p, "objective": "reg:squarederror", "verbosity": 0, "seed": RANDOM_SEED},
            dtrain=xgb.DMatrix(Xtr_e, label=y[tr]),
            num_boost_round=xgb_params.get("num_boost_round", 1000),
        )
        xgb_preds[te] = m.predict(xgb.DMatrix(Xte_e, label=y[te]))
    return cb_preds, xgb_preds


def kf_oof_warm(
    X_warm: pd.DataFrame, y_warm: np.ndarray,
    cb_params: dict, xgb_params: dict, n_splits: int = 5,
) -> tuple[np.ndarray, np.ndarray]:
    """KFold OOF 산출 (warm slice — 작품 단위 분할)."""
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_SEED)
    cb_preds = np.zeros(len(y_warm))
    xgb_preds = np.zeros(len(y_warm))
    for fold, (tr, te) in enumerate(kf.split(X_warm), 1):
        logger.info("[KF warm %d/%d] train=%d test=%d", fold, n_splits, len(tr), len(te))
        cb = CatBoostRegressor(
            **cb_params, loss_function="RMSE", verbose=0,
            random_seed=RANDOM_SEED, allow_writing_files=False,
        )
        cb.fit(_cb_pool(X_warm.iloc[tr], y_warm[tr]))
        cb_preds[te] = cb.predict(_cb_pool(X_warm.iloc[te]))

        Xtr_e, Xte_e, _ = _label_encode_xgb(X_warm.iloc[tr], X_warm.iloc[te])
        xgb_p = {k: v for k, v in xgb_params.items() if k != "num_boost_round"}
        m = xgb.train(
            params={**xgb_p, "objective": "reg:squarederror", "verbosity": 0, "seed": RANDOM_SEED},
            dtrain=xgb.DMatrix(Xtr_e, label=y_warm[tr]),
            num_boost_round=xgb_params.get("num_boost_round", 1000),
        )
        xgb_preds[te] = m.predict(xgb.DMatrix(Xte_e, label=y_warm[te]))
    return cb_preds, xgb_preds


def main() -> None:
    DIAG_DIR.mkdir(parents=True, exist_ok=True)

    cb_params, xgb_params = _load_best_params()
    logger.info("Best params loaded: CB iterations=%d depth=%d / XGB num_boost=%d depth=%d",
                cb_params["iterations"], cb_params["depth"],
                xgb_params["num_boost_round"], xgb_params["max_depth"])

    df = load_data()
    df_train = df[df.get("is_excluded_for_training", 0) != 1].reset_index(drop=True)
    X, y, groups = prepare_features(df_train)
    source = df_train["source"].astype(str).to_numpy()
    logger.info("Data: n=%d, features=%d, artists=%d", len(df_train), len(CB_FEATURES), len(set(groups)))

    # Cold path OOF (전체 28,376건)
    logger.info("=== GroupKFold OOF (cold path, n=%d) ===", len(df_train))
    cb_gkf_ln, xgb_gkf_ln = gkf_oof(X, y, groups, cb_params, xgb_params)

    # Warm slice OOF
    wmask = _warm_mask(groups)
    X_warm = X.iloc[wmask].reset_index(drop=True)
    y_warm = y[wmask]
    groups_warm = groups[wmask]
    source_warm = source[wmask]
    logger.info("=== KFold OOF (warm slice, n=%d, artists=%d) ===",
                len(X_warm), len(set(groups_warm)))
    cb_kf_ln, xgb_kf_ln = kf_oof_warm(X_warm, y_warm, cb_params, xgb_params)

    out_path = DIAG_DIR / "oof_predictions.npz"
    np.savez(
        out_path,
        y_actual_ln=y,
        cb_preds_gkf_ln=cb_gkf_ln,
        xgb_preds_gkf_ln=xgb_gkf_ln,
        groups=groups.astype(str),
        source=source,
        warm_mask=wmask,
        y_warm_actual_ln=y_warm,
        cb_preds_kf_ln=cb_kf_ln,
        xgb_preds_kf_ln=xgb_kf_ln,
        groups_warm=groups_warm.astype(str),
        source_warm=source_warm,
    )
    logger.info("OOF 저장: %s (size=%d KB)", out_path, out_path.stat().st_size // 1024)
    logger.info("done")


if __name__ == "__main__":
    main()
