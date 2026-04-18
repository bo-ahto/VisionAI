"""앙상블 스태킹 모델 — CatBoost + LightGBM + Ridge meta-learner.

Level-0: CatBoost MultiQuantile + LightGBM Quantile (2개 base, q25/q50/q75)
Level-1: Ridge Regression × 3 (분위수별 독립 메타 학습)

Holdout stacking: train→base, calib→meta, valid→평가.
학술 근거: Fedderke & Carugno (2025), Karakasis et al. (2024).
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.linear_model import QuantileRegressor

from visionai.price_engine.estimate_generator.hedonic_features import CAT_FEATURE_NAMES
from visionai.price_engine.estimate_generator.quantile_model import (
    HEDONIC_CAT_INDICES,
    _enforce_monotonicity,
    _prepare_hedonic_features,
)

logger = logging.getLogger(__name__)


class EnsembleStackingModel:
    """CatBoost + LightGBM → Ridge (q25/q50/q75 분위수별 스태킹)."""

    def __init__(
        self,
        iterations: int = 2000,
        depth: int = 8,
        random_seed: int = 42,
    ) -> None:
        self.iterations = iterations
        self.depth = depth
        self.random_seed = random_seed
        self._base_models: dict[str, object] = {}
        self._meta: dict[int, QuantileRegressor] = {}  # q_idx → QuantileRegressor
        self._fitted = False
        self._extra_features: list[str] | None = None
        # XGBoost 범주형 코드 매핑 (학습 시 고정 → 추론/평가 시 재사용).
        # key: 범주형 컬럼명, value: pd.Index of categories 순서.
        self._xgb_cat_vocab: dict[str, pd.Index] = {}

    def fit(
        self,
        train_df: pd.DataFrame,
        calib_df: pd.DataFrame | None = None,
        valid_df: pd.DataFrame | None = None,
        target_col: str = "ln_price",
        extra_features: list[str] | None = None,
        sample_weight_col: str | None = None,
    ) -> dict[str, float]:
        """Level-0 학습(train) + Level-1 메타 학습(calib).

        Returns:
            dict with base/ensemble metrics.
        """
        self._extra_features = extra_features
        x_train = _prepare_hedonic_features(train_df, extra_features)
        y_train = train_df[target_col].values
        mask = np.isfinite(y_train)
        w_train = None
        if sample_weight_col and sample_weight_col in train_df.columns:
            w_train = train_df[sample_weight_col].values[mask]
        x_train, y_train = x_train[mask], y_train[mask]

        results: dict[str, float] = {}

        # Calib set
        x_calib, y_calib = None, None
        if calib_df is not None:
            x_calib = _prepare_hedonic_features(calib_df, extra_features)
            y_calib = calib_df[target_col].values
            c_mask = np.isfinite(y_calib)
            x_calib, y_calib = x_calib[c_mask], y_calib[c_mask]

        # --- Level-0: CatBoost MultiQuantile ---
        logger.info("Training base: CatBoost MultiQuantile (train=%d)", len(x_train))
        cb = CatBoostRegressor(
            iterations=self.iterations,
            depth=self.depth,
            learning_rate=0.05,
            loss_function="MultiQuantile:alpha=0.25,0.5,0.75",
            cat_features=HEDONIC_CAT_INDICES,
            random_seed=self.random_seed,
            verbose=0,
            early_stopping_rounds=100,
        )
        eval_set = (x_calib, y_calib) if x_calib is not None else None
        cb.fit(x_train, y_train, eval_set=eval_set, use_best_model=True,
               sample_weight=w_train)
        self._base_models["catboost"] = cb

        # --- Level-0: LightGBM (q25, q50, q75 각각) ---
        try:
            import lightgbm as lgb

            # LightGBM은 category dtype 필요
            x_train_lgb = x_train.copy()
            x_calib_lgb = x_calib.copy() if x_calib is not None else None
            cat_cols = []
            for col in CAT_FEATURE_NAMES:
                if col in x_train_lgb.columns:
                    x_train_lgb[col] = x_train_lgb[col].astype("category")
                    if x_calib_lgb is not None:
                        x_calib_lgb[col] = x_calib_lgb[col].astype("category")
                    cat_cols.append(col)

            lgb_models = {}
            for qi, alpha in enumerate([0.25, 0.50, 0.75]):
                logger.info("Training base: LightGBM q%.2f", alpha)
                lgb_model = lgb.LGBMRegressor(
                    n_estimators=self.iterations,
                    max_depth=self.depth,
                    learning_rate=0.03,
                    num_leaves=63,
                    min_child_samples=10,
                    objective="quantile",
                    alpha=alpha,
                    random_state=self.random_seed,
                    verbose=-1,
                )
                lgb_model.fit(
                    x_train_lgb, y_train,
                    sample_weight=w_train,
                    categorical_feature=cat_cols,
                    eval_set=[(x_calib_lgb, y_calib)] if x_calib_lgb is not None else None,
                    callbacks=[lgb.early_stopping(100, verbose=False)]
                    if x_calib_lgb is not None else None,
                )
                lgb_models[f"lgb_q{qi}"] = lgb_model
            self._base_models.update(lgb_models)
        except (ImportError, ValueError, TypeError) as exc:
            logger.warning("LightGBM failed (%s), using CatBoost only", exc)

        # --- Level-0: XGBoost (q25, q50, q75 각각) ---
        try:
            import xgboost as xgb

            # XGBoost는 범주형 직접 지원 안 함 → 학습 시점 카테고리 목록을 고정 저장.
            # pd.Categorical을 호출마다 새로 만들면 동일 값이 다른 코드로 매핑될 수 있으므로,
            # train 데이터의 unique 카테고리 순서를 self._xgb_cat_vocab에 기록하고
            # calib/inference에서 동일 매핑을 재사용한다. 미등장 값은 -1(NaN 코드).
            x_train_num = x_train.copy()
            x_calib_num = x_calib.copy() if x_calib is not None else None
            for col in CAT_FEATURE_NAMES:
                if col in x_train_num.columns:
                    train_cat = pd.Categorical(x_train_num[col])
                    self._xgb_cat_vocab[col] = train_cat.categories
                    x_train_num[col] = train_cat.codes
                    if x_calib_num is not None:
                        x_calib_num[col] = pd.Categorical(
                            x_calib_num[col], categories=train_cat.categories,
                        ).codes

            xgb_models = {}
            for qi, alpha in enumerate([0.25, 0.50, 0.75]):
                logger.info("Training base: XGBoost q%.2f", alpha)
                xgb_model = xgb.XGBRegressor(
                    n_estimators=self.iterations,
                    max_depth=self.depth,
                    learning_rate=0.03,
                    objective="reg:quantileerror",
                    quantile_alpha=alpha,
                    random_state=self.random_seed,
                    verbosity=0,
                    early_stopping_rounds=100,
                )
                eval_xgb = [(x_calib_num, y_calib)] if x_calib_num is not None else None
                xgb_model.fit(x_train_num, y_train, sample_weight=w_train,
                              eval_set=eval_xgb, verbose=False)
                xgb_models[f"xgb_q{qi}"] = xgb_model
            self._base_models.update(xgb_models)
            self._xgb_cat_encoded = True
            logger.info("XGBoost base learners trained")
        except Exception as exc:  # noqa: BLE001 — XGBoost는 선택 backend, XGBoostError 포함 모든 실패 시 skip
            logger.warning(
                "XGBoost failed (%s: %s), skipping", type(exc).__name__, exc,
            )
            self._xgb_cat_encoded = False

        # --- Level-1: 분위수별 QuantileRegressor meta-learner ---
        # Ridge(MSE)는 조건부 평균으로 회귀시켜 스택 결과가 더 이상 유효 분위수가 아님.
        # → pinball loss를 최소화하는 QuantileRegressor로 각 quantile을 별도 학습.
        if x_calib is not None and y_calib is not None:
            calib_base = self._get_base_predictions(x_calib)
            n_base_cols = calib_base.shape[1]
            n_models = n_base_cols // 3  # CB=1 + LGB=1 + XGB=1 = 3 (or 2 or 1)
            logger.info("Level-1 meta: %d base predictions (%d models × 3 quantiles)",
                         n_base_cols, n_models)
            for qi, alpha_q in enumerate([0.25, 0.50, 0.75]):
                # 각 base model의 qi번째 분위수 예측을 수집
                cols = [qi + m * 3 for m in range(n_models)]
                meta_x = calib_base[:, cols]
                self._meta[qi] = QuantileRegressor(
                    quantile=alpha_q, alpha=0.01, solver="highs",
                )
                self._meta[qi].fit(meta_x, y_calib)
            logger.info("Level-1 QuantileRegressor trained for q25/q50/q75")

        self._fitted = True
        logger.info("Ensemble training complete")
        return results

    def predict_raw(self, df: pd.DataFrame) -> np.ndarray:
        """앙상블 예측 (log scale). shape: (n, 3)."""
        if not self._fitted:
            raise RuntimeError("Model not fitted.")

        x_feat = _prepare_hedonic_features(df, self._extra_features)
        base_preds = self._get_base_predictions(x_feat)

        if self._meta:
            out = np.zeros((len(x_feat), 3))
            n_models = base_preds.shape[1] // 3
            for qi in range(3):
                cols = [qi + m * 3 for m in range(n_models)]
                out[:, qi] = self._meta[qi].predict(base_preds[:, cols])
            return _enforce_monotonicity(out)

        # fallback: CatBoost만
        cb_pred = self._base_models["catboost"].predict(x_feat)
        if cb_pred.ndim == 1:
            return cb_pred.reshape(-1, 1)
        return _enforce_monotonicity(cb_pred)

    def predict(self, df: pd.DataFrame) -> dict[str, np.ndarray]:
        """exp 역변환."""
        raw = self.predict_raw(df)
        if raw.ndim == 2 and raw.shape[1] >= 3:
            return {
                "price_low": np.exp(raw[:, 0]),
                "price_mid": np.exp(raw[:, 1]),
                "price_high": np.exp(raw[:, 2]),
            }
        return {"price_mid": np.exp(raw.ravel())}

    def _get_base_predictions(self, x_feat: pd.DataFrame) -> np.ndarray:
        """모든 base learner 예측 결합. shape: (n, n_bases×3)."""
        cols = []

        # CatBoost MultiQuantile → (n, 3)
        cb = self._base_models["catboost"]
        cb_pred = cb.predict(x_feat)
        if cb_pred.ndim == 1:
            cols.extend([cb_pred, cb_pred, cb_pred])
        else:
            for qi in range(min(3, cb_pred.shape[1])):
                cols.append(cb_pred[:, qi])

        # LightGBM q0, q1, q2 → 각 (n,)
        has_lgb = any(f"lgb_q{qi}" in self._base_models for qi in range(3))
        if has_lgb:
            x_lgb = x_feat.copy()
            for col in CAT_FEATURE_NAMES:
                if col in x_lgb.columns:
                    x_lgb[col] = x_lgb[col].astype("category")
        for qi in range(3):
            key = f"lgb_q{qi}"
            if key in self._base_models:
                cols.append(self._base_models[key].predict(x_lgb))

        # XGBoost q0, q1, q2 → 각 (n,)
        # 학습 시 저장한 self._xgb_cat_vocab으로 코드 재매핑 (동일 값 = 동일 코드 보장).
        has_xgb = any(f"xgb_q{qi}" in self._base_models for qi in range(3))
        x_num: pd.DataFrame | None = None
        if has_xgb:
            x_num = x_feat.copy()
            for col in CAT_FEATURE_NAMES:
                if col in x_num.columns:
                    vocab = self._xgb_cat_vocab.get(col)
                    if vocab is not None:
                        x_num[col] = pd.Categorical(x_num[col], categories=vocab).codes
                    else:
                        # 학습 시 등장하지 않은 컬럼 (fallback, should not happen)
                        x_num[col] = pd.Categorical(x_num[col]).codes
        for qi in range(3):
            key = f"xgb_q{qi}"
            if key in self._base_models:
                cols.append(self._base_models[key].predict(x_num))

        return np.column_stack(cols)
