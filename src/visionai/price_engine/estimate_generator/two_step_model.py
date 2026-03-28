"""Two-Step 가격대별 모델 — Kim & Kim (2024) 한국 경매 데이터 기반.

Step 1: CatBoost Classifier → 3-bin 가격대 분류
Step 2: 가격대별 전용 CatBoost MultiQuantile Regressor

기획서 Phase 4 Tier 2, 2.5절 참조.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier, CatBoostRegressor

from visionai.price_engine.estimate_generator.quantile_model import (
    HEDONIC_CAT_INDICES,
    _enforce_monotonicity,
    _prepare_hedonic_features,
)

logger = logging.getLogger(__name__)

# 3-bin 경계: 저가 < 500만, 중가 500만~3000만, 고가 3000만+
PRICE_BINS = [0, 5_000_000, 30_000_000, float("inf")]
PRICE_LABELS = ["low", "mid", "high"]


class TwoStepModel:
    """Two-Step 가격대별 모델.

    Step 1: 가격대 분류 (CatBoost Classifier)
    Step 2: 가격대별 전용 회귀 (CatBoost MultiQuantile)
    """

    def __init__(
        self,
        iterations: int = 1500,
        depth: int = 7,
        learning_rate: float = 0.05,
        random_seed: int = 42,
    ) -> None:
        self.iterations = iterations
        self.depth = depth
        self.learning_rate = learning_rate
        self.random_seed = random_seed
        self._classifier: CatBoostClassifier | None = None
        self._regressors: dict[str, CatBoostRegressor] = {}

    def fit(
        self,
        train_df: pd.DataFrame,
        valid_df: pd.DataFrame | None = None,
        target_col: str = "ln_price",
        price_col: str = "낙찰가",
    ) -> dict[str, int]:
        """Two-Step 학습.

        Returns:
            dict with bin counts.
        """
        x_train = _prepare_hedonic_features(train_df)
        y_train = train_df[target_col].values
        prices = pd.to_numeric(train_df[price_col], errors="coerce").values

        # bin 라벨 생성
        bin_labels = pd.cut(
            prices, bins=PRICE_BINS, labels=PRICE_LABELS, right=True
        ).astype(str)
        bin_labels[pd.isna(prices) | (prices <= 0)] = "low"

        # Step 1: Classifier 학습
        logger.info("Step 1: Training price-class classifier")
        self._classifier = CatBoostClassifier(
            iterations=self.iterations,
            depth=self.depth,
            learning_rate=self.learning_rate,
            cat_features=HEDONIC_CAT_INDICES,
            random_seed=self.random_seed,
            verbose=0,
            auto_class_weights="Balanced",
        )
        self._classifier.fit(x_train, bin_labels)

        # Step 2: 가격대별 Regressor 학습
        bin_counts = {}
        for label in PRICE_LABELS:
            mask = (bin_labels == label) & np.isfinite(y_train)
            n = int(mask.sum())
            bin_counts[label] = n
            logger.info("Step 2: Training regressor for bin '%s' (n=%d)", label, n)

            if n < 100:
                logger.warning("Bin '%s' has < 100 samples. Skipping.", label)
                continue

            x_bin = x_train[mask]
            y_bin = y_train[mask]

            eval_set = None
            if valid_df is not None:
                x_val = _prepare_hedonic_features(valid_df)
                y_val = valid_df[target_col].values
                prices_val = pd.to_numeric(valid_df[price_col], errors="coerce").values
                val_bins = pd.cut(
                    prices_val, bins=PRICE_BINS, labels=PRICE_LABELS, right=True
                ).astype(str)
                val_mask = (val_bins == label) & np.isfinite(y_val)
                if val_mask.sum() > 0:
                    eval_set = (x_val[val_mask], y_val[val_mask])

            reg = CatBoostRegressor(
                iterations=self.iterations,
                depth=self.depth,
                learning_rate=self.learning_rate,
                loss_function="MultiQuantile:alpha=0.25,0.5,0.75",
                cat_features=HEDONIC_CAT_INDICES,
                random_seed=self.random_seed,
                verbose=0,
                early_stopping_rounds=100,
            )
            reg.fit(x_bin, y_bin, eval_set=eval_set, use_best_model=True)
            self._regressors[label] = reg

        logger.info("Two-Step training complete. Bin counts: %s", bin_counts)
        return bin_counts

    def predict_raw(self, df: pd.DataFrame) -> np.ndarray:
        """Two-Step 예측. shape: (n, 3) = [q25, q50, q75]."""
        if self._classifier is None:
            msg = "Model not fitted."
            raise RuntimeError(msg)

        x_feat = _prepare_hedonic_features(df)

        # Step 1: 가격대 분류
        pred_bins = self._classifier.predict(x_feat).flatten()

        # Step 2: 가격대별 예측
        n = len(df)
        result = np.zeros((n, 3))

        for label in PRICE_LABELS:
            mask = pred_bins == label
            if not mask.any():
                continue

            if label in self._regressors:
                preds = self._regressors[label].predict(x_feat[mask])
                if preds.ndim == 1:
                    preds = preds.reshape(-1, 1)
                result[mask] = preds[:, :3] if preds.shape[1] >= 3 else preds
            else:
                # fallback: 전체 데이터 기반 (가장 큰 bin의 regressor 사용)
                fallback = next(iter(self._regressors.values()), None)
                if fallback is not None:
                    preds = fallback.predict(x_feat[mask])
                    if preds.ndim == 1:
                        preds = preds.reshape(-1, 1)
                    result[mask] = preds[:, :3] if preds.shape[1] >= 3 else preds

        result = _enforce_monotonicity(result)
        return result

    def predict(self, df: pd.DataFrame) -> dict[str, np.ndarray]:
        """exp 역변환."""
        raw = self.predict_raw(df)
        return {
            "price_low": np.exp(raw[:, 0]),
            "price_mid": np.exp(raw[:, 1]),
            "price_high": np.exp(raw[:, 2]),
        }
