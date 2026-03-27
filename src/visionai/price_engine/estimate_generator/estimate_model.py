"""Model-B: CatBoost RMSE 전문가 추정가 재현.

타깃: y = ln(추정가 중앙) = ln((추정가_최저 + 추정가_최고) / 2)
손실: RMSE
역변환: exp(y_hat) * smearing_factor(segment) — Sprint 2에서 적용
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor

from visionai.price_engine.estimate_generator.quantile_model import (
    HEDONIC_CAT_INDICES,
    _prepare_hedonic_features,
)

logger = logging.getLogger(__name__)


class EstimateRegressorModel:
    """Model-B: 전문가 추정가 재현.

    기존 가격 예측 엔진의 입력(estimate_mid)을 대체하기 위한 모델.
    Sprint 2에서 세그먼트별 Duan smearing + ratio 보정이 추가된다.
    """

    def __init__(
        self,
        iterations: int = 2000,
        depth: int = 8,
        learning_rate: float = 0.05,
        l2_leaf_reg: float = 5.0,
        early_stopping_rounds: int = 100,
        random_seed: int = 42,
    ) -> None:
        self.iterations = iterations
        self.depth = depth
        self.learning_rate = learning_rate
        self.l2_leaf_reg = l2_leaf_reg
        self.early_stopping_rounds = early_stopping_rounds
        self.random_seed = random_seed
        self._model: CatBoostRegressor | None = None

    def fit(
        self,
        train_df: pd.DataFrame,
        valid_df: pd.DataFrame | None = None,
        target_col: str = "ln_estimate_mid_target",
    ) -> None:
        """CatBoost RMSE 학습."""
        x_train = _prepare_hedonic_features(train_df)
        y_train = train_df[target_col].values
        mask = ~np.isnan(y_train)
        x_train = x_train[mask]
        y_train = y_train[mask]

        eval_set = None
        if valid_df is not None:
            x_valid = _prepare_hedonic_features(valid_df)
            y_valid = valid_df[target_col].values
            v_mask = ~np.isnan(y_valid)
            eval_set = (x_valid[v_mask], y_valid[v_mask])

        logger.info("Training Model-B (RMSE): train=%d", len(x_train))

        self._model = CatBoostRegressor(
            iterations=self.iterations,
            depth=self.depth,
            learning_rate=self.learning_rate,
            l2_leaf_reg=self.l2_leaf_reg,
            loss_function="RMSE",
            cat_features=HEDONIC_CAT_INDICES,
            random_seed=self.random_seed,
            verbose=100,
            early_stopping_rounds=self.early_stopping_rounds,
        )

        self._model.fit(x_train, y_train, eval_set=eval_set, use_best_model=True)
        logger.info("Model-B best iteration: %d", self._model.best_iteration_)

    def predict_raw(self, df: pd.DataFrame) -> np.ndarray:
        """Raw 예측 (log scale). shape: (n,)."""
        if self._model is None:
            msg = "Model not fitted. Call fit() first."
            raise RuntimeError(msg)
        x_feat = _prepare_hedonic_features(df)
        return self._model.predict(x_feat)

    def predict(self, df: pd.DataFrame, smearing_factor: float = 1.0) -> np.ndarray:
        """exp 역변환 + smearing 적용된 추정가 중앙값.

        Args:
            df: 피처 DataFrame.
            smearing_factor: Duan smearing factor (Sprint 2에서 세그먼트별 적용).
                기본값 1.0 = smearing 없음.

        Returns:
            추정가 중앙값 배열 (원화).
        """
        raw = self.predict_raw(df)
        return np.exp(raw) * smearing_factor

    def save(self, path: str | Path) -> None:
        """모델 저장."""
        if self._model is not None:
            self._model.save_model(str(path))
            logger.info("Model-B saved to %s", path)

    def load(self, path: str | Path) -> None:
        """모델 로드."""
        self._model = CatBoostRegressor()
        self._model.load_model(str(path))
        logger.info("Model-B loaded from %s", path)
