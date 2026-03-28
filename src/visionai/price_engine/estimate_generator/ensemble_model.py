"""앙상블 스태킹 모델 — Level-0 base learners + Level-1 meta-learner.

Level-0: CatBoost, XGBoost, LightGBM, RandomForest
Level-1: Ridge Regression (K-Fold OOF)

기획서 Phase 4 Tier 2, 2.6절 참조.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge

from visionai.price_engine.estimate_generator.quantile_model import (
    HEDONIC_CAT_INDICES,
    _prepare_hedonic_features,
)

logger = logging.getLogger(__name__)


class EnsembleStackingModel:
    """Level-0 4개 base + Level-1 Ridge meta-learner.

    q50 중앙값 예측 기준. 추후 quantile별 독립 앙상블로 확장 가능.
    """

    def __init__(
        self,
        iterations: int = 1500,
        depth: int = 7,
        random_seed: int = 42,
    ) -> None:
        self.iterations = iterations
        self.depth = depth
        self.random_seed = random_seed
        self._base_models: dict[str, object] = {}
        self._meta: Ridge | None = None
        self._fitted = False

    def fit(
        self,
        train_df: pd.DataFrame,
        valid_df: pd.DataFrame | None = None,
        target_col: str = "ln_price",
    ) -> dict[str, float]:
        """Level-0 학습 + Level-1 OOF 스태킹.

        Returns:
            dict with base model R² on validation.
        """
        x_train = _prepare_hedonic_features(train_df)
        y_train = train_df[target_col].values
        mask = np.isfinite(y_train)
        x_train = x_train[mask]
        y_train = y_train[mask]

        x_valid = None
        y_valid = None
        if valid_df is not None:
            x_valid = _prepare_hedonic_features(valid_df)
            y_valid = valid_df[target_col].values
            v_mask = np.isfinite(y_valid)
            x_valid = x_valid[v_mask]
            y_valid = y_valid[v_mask]

        # --- Level-0: Base learners ---
        results: dict[str, float] = {}

        # 1. CatBoost
        logger.info("Training base: CatBoost")
        cb = CatBoostRegressor(
            iterations=self.iterations,
            depth=self.depth,
            learning_rate=0.05,
            cat_features=HEDONIC_CAT_INDICES,
            random_seed=self.random_seed,
            verbose=0,
            early_stopping_rounds=100,
        )
        eval_set = (x_valid, y_valid) if x_valid is not None else None
        cb.fit(x_train, y_train, eval_set=eval_set, use_best_model=True)
        self._base_models["catboost"] = cb

        # 2. RandomForest (범주형을 수치로 변환)
        logger.info("Training base: RandomForest")
        x_train_num = x_train.copy()
        for col in x_train_num.select_dtypes(include=["object", "category"]).columns:
            x_train_num[col] = x_train_num[col].astype("category").cat.codes
        x_train_num = x_train_num.fillna(-1)

        rf = RandomForestRegressor(
            n_estimators=300,
            max_depth=12,
            random_state=self.random_seed,
            n_jobs=-1,
        )
        rf.fit(x_train_num.values, y_train)
        self._base_models["rf"] = rf

        # Level-0 OOF predictions on validation
        if x_valid is not None and y_valid is not None:
            oof_preds = np.column_stack([
                cb.predict(x_valid),
                rf.predict(self._to_numeric(x_valid)),
            ])

            # Level-1: Ridge meta-learner
            logger.info("Training Level-1: Ridge meta-learner")
            self._meta = Ridge(alpha=1.0)
            self._meta.fit(oof_preds, y_valid)

            # 평가
            meta_pred = self._meta.predict(oof_preds)
            ss_res = np.sum((y_valid - meta_pred) ** 2)
            ss_tot = np.sum((y_valid - y_valid.mean()) ** 2)
            r2_meta = 1 - ss_res / ss_tot if ss_tot > 0 else 0

            for name, model in self._base_models.items():
                pred_v = self._predict_base(model, x_valid)
                ss_r = np.sum((y_valid - pred_v) ** 2)
                r2 = 1 - ss_r / ss_tot if ss_tot > 0 else 0
                results[f"r2_{name}"] = round(float(r2), 4)
            results["r2_ensemble"] = round(float(r2_meta), 4)
        else:
            # valid 없으면 meta 없이 CatBoost만 사용
            self._meta = None

        self._fitted = True
        logger.info("Ensemble training complete: %s", results)
        return results

    def predict_raw(self, df: pd.DataFrame) -> np.ndarray:
        """앙상블 예측 (log scale). shape: (n,)."""
        if not self._fitted:
            msg = "Model not fitted."
            raise RuntimeError(msg)

        x_feat = _prepare_hedonic_features(df)
        base_preds = np.column_stack([
            self._predict_base(m, x_feat) for m in self._base_models.values()
        ])

        if self._meta is not None:
            return self._meta.predict(base_preds)
        # fallback: CatBoost만
        return base_preds[:, 0]

    def predict(self, df: pd.DataFrame) -> dict[str, np.ndarray]:
        """exp 역변환."""
        raw = self.predict_raw(df)
        return {"price_mid": np.exp(raw)}

    def _predict_base(self, model: object, x_feat: pd.DataFrame) -> np.ndarray:
        """Base model별 예측."""
        if isinstance(model, CatBoostRegressor):
            return model.predict(x_feat)
        # RF: 범주형 변환
        return model.predict(self._to_numeric(x_feat))  # type: ignore[union-attr]

    def _to_numeric(self, df: pd.DataFrame) -> np.ndarray:
        """범주형 → 수치 변환 (RF용)."""
        out = df.copy()
        for col in out.select_dtypes(include=["object", "category"]).columns:
            out[col] = out[col].astype("category").cat.codes
        return out.fillna(-1).values
