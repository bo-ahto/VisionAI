"""타깃 변환 모델 — log(price / estimate_mid) 회귀.

기획서 참조: 4.2절 ②
추정가 대비 할인/프리미엄율을 직접 예측하여:
1. 추정가 지배력 문제를 구조적으로 해소
2. 재변환 편향을 완화 (예측 → 원가 복원이 곱셈이므로 극단값 압축 감소)
3. K-Auction 핵심 패턴(추정가 60% 낙찰)과 정확히 정렬

공식:
  y_new = ln(P_i / estimate_mid_i)   ← 할인율의 log
  P̂_i = estimate_mid_i × exp(ŷ_new)  ← 복원
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor

from visionai.price_engine.models.predictor import (
    BASELINE_FEATURES,
    CAT_FEATURE_INDICES,
    prepare_features,
)

logger = logging.getLogger(__name__)


def build_transform_target(df: pd.DataFrame) -> pd.Series:
    """ln(낙찰가 / estimate_mid)를 계산한다.

    Returns:
        pd.Series: 타깃 변환값. estimate_mid=0이면 NaN.
    """
    price = df["낙찰가"].astype(float)
    est_mid = df["estimate_mid"].astype(float)

    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = price / est_mid
        ratio[est_mid <= 0] = np.nan
        ratio[price <= 0] = np.nan

    return np.log(ratio)


def train_transform_model(
    train_df: pd.DataFrame,
    valid_df: pd.DataFrame,
    iterations: int = 3000,
    depth: int = 8,
    learning_rate: float = 0.05,
    l2_leaf_reg: float = 5.0,
    early_stopping_rounds: int = 200,
    random_seed: int = 42,
) -> CatBoostRegressor:
    """타깃 변환 CatBoost를 학습한다.

    타깃: ln(price / estimate_mid)
    """
    X_train = prepare_features(train_df)
    y_train = build_transform_target(train_df).values

    X_valid = prepare_features(valid_df)
    y_valid = build_transform_target(valid_df).values

    # NaN 제거
    train_mask = ~np.isnan(y_train)
    valid_mask = ~np.isnan(y_valid)
    X_train = X_train[train_mask]
    y_train = y_train[train_mask]
    X_valid = X_valid[valid_mask]
    y_valid = y_valid[valid_mask]

    logger.info(
        "Training target-transform model: train=%d, valid=%d",
        len(X_train), len(X_valid),
    )

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

    return model


def predict_transform(
    model: CatBoostRegressor,
    df: pd.DataFrame,
) -> np.ndarray:
    """타깃 변환 모델로 예측 → 원래 스케일(원)로 복원.

    P̂ = estimate_mid × exp(ŷ_transform)
    """
    X = prepare_features(df)
    y_transform_pred = model.predict(X)

    est_mid = (
        df["추정가(최저)"].astype(float) + df["추정가(최고)"].astype(float)
    ) / 2

    return est_mid.values * np.exp(y_transform_pred)
