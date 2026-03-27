"""CatBoost 모델 학습 모듈.

기획서 참조: 4.1
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor

from visionai.price_engine.models.predictor import BASELINE_FEATURES, CAT_FEATURE_INDICES

logger = logging.getLogger(__name__)


def train_catboost(
    train_df: pd.DataFrame,
    valid_df: pd.DataFrame,
    target_col: str = "ln_price",
    iterations: int = 3000,
    depth: int = 8,
    learning_rate: float = 0.05,
    l2_leaf_reg: float = 5.0,
    early_stopping_rounds: int = 200,
    random_seed: int = 42,
    save_path: str | Path | None = None,
) -> CatBoostRegressor:
    """CatBoost 모델을 학습한다.

    Args:
        train_df: 학습 데이터 (BASELINE_FEATURES + target_col 포함).
        valid_df: 검증 데이터.
        target_col: 타겟 컬럼명 (기본: ln_price).
        save_path: 모델 저장 경로 (.cbm).

    Returns:
        학습된 CatBoostRegressor.
    """
    from visionai.price_engine.models.predictor import prepare_features

    X_train = prepare_features(train_df)
    y_train = train_df[target_col].values

    X_valid = prepare_features(valid_df)
    y_valid = valid_df[target_col].values

    # NaN 타겟 제거
    train_mask = ~np.isnan(y_train)
    valid_mask = ~np.isnan(y_valid)
    X_train = X_train[train_mask]
    y_train = y_train[train_mask]
    X_valid = X_valid[valid_mask]
    y_valid = y_valid[valid_mask]

    logger.info("Training CatBoost: train=%d, valid=%d", len(X_train), len(X_valid))

    model = CatBoostRegressor(
        iterations=iterations,
        depth=depth,
        learning_rate=learning_rate,
        l2_leaf_reg=l2_leaf_reg,
        loss_function="RMSE",
        cat_features=CAT_FEATURE_INDICES,
        random_seed=random_seed,
        verbose=100,
        early_stopping_rounds=early_stopping_rounds,
    )

    model.fit(X_train, y_train, eval_set=(X_valid, y_valid), use_best_model=True)

    logger.info("Best iteration: %d", model.best_iteration_)

    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        model.save_model(str(save_path))
        logger.info("Model saved to %s", save_path)

    return model
