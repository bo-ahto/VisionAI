"""워크포워드 백테스트 러너.

각 cutoff에서 재학습 → 평가하여 MAPE 안정성을 확인한다.
기획서 참조: 9장 #1

워크포워드 = 각 cutoff마다 train(cutoff 이전) → test(cutoff 이후) 재학습.
단순 cutoff 평가(재학습 없음)와 구분된다.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor

from visionai.price_engine.models.predictor import predict, prepare_features, CAT_FEATURE_INDICES
from visionai.price_engine.validation.metrics import compute_metrics

logger = logging.getLogger(__name__)


def run_walkforward_backtest(
    df: pd.DataFrame,
    cutoffs: list[int] | None = None,
    session_col: str = "회차",
    price_col: str = "낙찰가",
    target_col: str = "ln_price",
    retrain: bool = True,
    model: CatBoostRegressor | None = None,
) -> pd.DataFrame:
    """워크포워드 백테스트: 각 cutoff에서 재학습 + 평가.

    Args:
        df: 전체 피처 DataFrame.
        cutoffs: 테스트 시작 회차 리스트. None이면 [350, 380, 410, 440].
        retrain: True면 각 cutoff에서 재학습 (진짜 워크포워드).
                 False면 기존 model로만 평가 (간이 모드).
        model: retrain=False일 때 사용할 모델.

    Returns:
        DataFrame: cutoff, mape, mdape, within_20pct, n, mode
    """
    if cutoffs is None:
        cutoffs = [350, 380, 410, 440]

    rows = []
    for cutoff in cutoffs:
        train_mask = df[session_col] < cutoff
        test_mask = df[session_col] >= cutoff

        train_data = df[train_mask]
        test_data = df[test_mask]

        if len(test_data) < 10 or len(train_data) < 100:
            logger.warning("Cutoff %d: insufficient data (train=%d, test=%d)", cutoff, len(train_data), len(test_data))
            continue

        if retrain:
            # 각 cutoff에서 재학습
            X_train = prepare_features(train_data)
            y_train = train_data[target_col].values
            valid_mask = ~np.isnan(y_train)
            X_train = X_train[valid_mask]
            y_train = y_train[valid_mask]

            fold_model = CatBoostRegressor(
                iterations=1000,
                depth=8,
                learning_rate=0.05,
                l2_leaf_reg=5,
                loss_function="RMSE",
                cat_features=CAT_FEATURE_INDICES,
                random_seed=42,
                verbose=0,
                early_stopping_rounds=100,
            )
            # valid = cutoff 직전 15%
            split_idx = int(len(X_train) * 0.85)
            fold_model.fit(
                X_train.iloc[:split_idx], y_train[:split_idx],
                eval_set=(X_train.iloc[split_idx:], y_train[split_idx:]),
                use_best_model=True,
            )
            mode = "retrained"
        else:
            if model is None:
                msg = "retrain=False requires model argument"
                raise ValueError(msg)
            fold_model = model
            mode = "fixed_model"

        y_pred = predict(fold_model, test_data, apply_low_price_cap=False)
        y_true = test_data[price_col].astype(float).values
        m = compute_metrics(y_true, y_pred)

        rows.append({
            "cutoff": cutoff,
            "mape": m.mape,
            "mdape": m.mdape,
            "within_20pct": m.within_20pct,
            "n": m.n,
            "mode": mode,
        })
        logger.info("Cutoff %d [%s]: MAPE=%.2f%% N=%d", cutoff, mode, m.mape, m.n)

    result = pd.DataFrame(rows)

    if len(result) >= 2:
        mape_std = result["mape"].std()
        logger.info("MAPE std across cutoffs: %.2f%%p (stable if < 3%%p)", mape_std)

    return result
