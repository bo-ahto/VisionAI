"""앙상블 스태킹 모델 — Level-0 base learners + Level-1 meta-learner.

Level-0: CatBoost + RandomForest (2개 base)
Level-1: Ridge Regression (Calib set으로 메타 학습, Validation에서 평가)

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
    """Level-0 2개 base (CatBoost + RF) + Level-1 Ridge meta-learner.

    q50 중앙값 예측 기준. 추후 base learner 추가 가능.
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
        calib_df: pd.DataFrame | None = None,
        valid_df: pd.DataFrame | None = None,
        target_col: str = "ln_price",
    ) -> dict[str, float]:
        """Level-0 학습(train) + Level-1 메타 학습(calib) + 평가(valid).

        핵심: meta-learner는 calib에서만 학습. valid는 순수 평가만.
        OOF 누수 방지: base는 train, meta는 calib, 성능은 valid.

        Returns:
            dict with base/ensemble R² on validation.
        """
        x_train = _prepare_hedonic_features(train_df)
        y_train = train_df[target_col].values
        mask = np.isfinite(y_train)
        x_train = x_train[mask]
        y_train = y_train[mask]

        # 범주형 인코딩 매핑 저장 (train 기준, 일관성 보장)
        self._cat_mapping: dict[str, dict] = {}
        for col in x_train.select_dtypes(include=["object", "category"]).columns:
            cats = x_train[col].astype("category").cat.categories
            self._cat_mapping[col] = {v: i for i, v in enumerate(cats)}

        # --- Level-0: Base learners (train으로 학습) ---
        results: dict[str, float] = {}

        # early stopping용 eval_set: calib 사용 (valid 아님)
        eval_set = None
        x_calib = None
        y_calib = None
        if calib_df is not None:
            x_calib = _prepare_hedonic_features(calib_df)
            y_calib = calib_df[target_col].values
            c_mask = np.isfinite(y_calib)
            x_calib = x_calib[c_mask]
            y_calib = y_calib[c_mask]
            eval_set = (x_calib, y_calib) if x_calib is not None else None

        logger.info("Training base: CatBoost (train=%d)", len(x_train))
        cb = CatBoostRegressor(
            iterations=self.iterations,
            depth=self.depth,
            learning_rate=0.05,
            cat_features=HEDONIC_CAT_INDICES,
            random_seed=self.random_seed,
            verbose=0,
            early_stopping_rounds=100,
        )
        cb.fit(x_train, y_train, eval_set=eval_set, use_best_model=True)
        self._base_models["catboost"] = cb

        logger.info("Training base: RandomForest")
        rf = RandomForestRegressor(
            n_estimators=300,
            max_depth=12,
            random_state=self.random_seed,
            n_jobs=-1,
        )
        rf.fit(self._to_numeric(x_train), y_train)
        self._base_models["rf"] = rf

        # --- Level-1: Meta-learner (calib에서 학습, valid에서 평가) ---
        if calib_df is not None and eval_set is not None:
            # calib에서 base 예측 → meta 학습
            calib_preds = np.column_stack([
                cb.predict(x_calib),
                rf.predict(self._to_numeric(x_calib)),
            ])
            logger.info("Training Level-1: Ridge meta-learner (calib=%d)", len(y_calib))
            self._meta = Ridge(alpha=1.0)
            self._meta.fit(calib_preds, y_calib)

        # --- 평가: valid (meta 학습에 사용하지 않은 데이터) ---
        if valid_df is not None:
            x_valid = _prepare_hedonic_features(valid_df)
            y_valid = valid_df[target_col].values
            v_mask = np.isfinite(y_valid)
            x_valid = x_valid[v_mask]
            y_valid = y_valid[v_mask]

            ss_tot = np.sum((y_valid - y_valid.mean()) ** 2)
            for name, model in self._base_models.items():
                pred_v = self._predict_base(model, x_valid)
                ss_r = np.sum((y_valid - pred_v) ** 2)
                r2 = 1 - ss_r / ss_tot if ss_tot > 0 else 0
                results[f"r2_{name}"] = round(float(r2), 4)

            if self._meta is not None:
                valid_preds = np.column_stack([
                    self._predict_base(m, x_valid)
                    for m in self._base_models.values()
                ])
                meta_pred = self._meta.predict(valid_preds)
                ss_res = np.sum((y_valid - meta_pred) ** 2)
                r2_meta = 1 - ss_res / ss_tot if ss_tot > 0 else 0
                results["r2_ensemble"] = round(float(r2_meta), 4)

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
        """범주형 → 수치 변환 (RF용). train 기준 매핑 사용으로 일관성 보장."""
        out = df.copy()
        for col in out.select_dtypes(include=["object", "category"]).columns:
            if hasattr(self, "_cat_mapping") and col in self._cat_mapping:
                mapping = self._cat_mapping[col]
                out[col] = out[col].map(mapping).fillna(-1)
            else:
                out[col] = out[col].astype("category").cat.codes
        return out.fillna(-1).values
