"""Model-A: CatBoost MultiQuantile 낙찰가 분위수 예측.

타깃: y = ln(낙찰가)
손실: MultiQuantile:alpha=0.25,0.5,0.75
역변환: exp() 직접 역변환 (smearing 없음 — Koenker 2005, Ch. 2.3)
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostError, CatBoostRegressor

from visionai.price_engine.estimate_generator.hedonic_features import (
    CAT_FEATURE_NAMES,
    HEDONIC_FEATURES,
)

logger = logging.getLogger(__name__)


def _enforce_monotonicity(preds: np.ndarray) -> np.ndarray:
    """Isotonic rearrangement: q25 <= q50 <= q75 보장.

    Pooled Adjacent Violators (PAV) 알고리즘 적용.
    Bondell et al. (2010, Biometrics): non-crossing quantile via isotonic regression.

    3개 분위수에서 PAV는:
    - 위반 쌍을 찾아 pooled average로 병합
    - 단순 정렬과 달리 원래 값의 가중 평균을 유지
    """
    out = preds.copy()
    for i in range(len(out)):
        vals = list(out[i, :3])
        # PAV for 3 elements (equal weights)
        # Pass 1: merge adjacent violators
        if vals[0] > vals[1]:
            avg = (vals[0] + vals[1]) / 2
            vals[0] = avg
            vals[1] = avg
        if vals[1] > vals[2]:
            avg = (vals[1] + vals[2]) / 2
            vals[1] = avg
            vals[2] = avg
        # Pass 2: check again after merge
        if vals[0] > vals[1]:
            avg = (vals[0] + vals[1] + vals[2]) / 3
            vals[0] = avg
            vals[1] = avg
            vals[2] = avg
        out[i, 0] = vals[0]
        out[i, 1] = vals[1]
        out[i, 2] = vals[2]
    return out

# Hedonic 피처에서 범주형 인덱스
HEDONIC_CAT_INDICES: list[int] = [
    i for i, f in enumerate(HEDONIC_FEATURES) if f in CAT_FEATURE_NAMES
]


def _prepare_hedonic_features(
    df: pd.DataFrame, extra_features: list[str] | None = None,
) -> pd.DataFrame:
    """HEDONIC_FEATURES (+extra) 순서로 피처 추출, 범주형 str 변환.

    predict 시 extra_features가 df에 없으면 NaN으로 채워 추가한다.
    CatBoost는 학습 시점의 피처 개수/순서와 일치해야 하므로 silent drop 금지.
    """
    features = list(HEDONIC_FEATURES)
    if extra_features:
        features = [*features, *extra_features]
    out = pd.DataFrame(index=df.index)
    for col in features:
        if col in df.columns:
            out[col] = df[col]
        else:
            # 학습 시 있었지만 추론 입력에 없는 extra feature → NaN 기본값
            out[col] = np.nan
    for col in CAT_FEATURE_NAMES:
        if col in out.columns:
            out[col] = out[col].astype(str)
    return out


class HedonicQuantileModel:
    """Model-A: 낙찰가 분위수 예측 (추정가 없이).

    CatBoost MultiQuantile로 q25/q50/q75를 동시 학습.
    MultiQuantile 미지원 시 독립 3모델 + isotonic rearrangement fallback.
    """

    def __init__(
        self,
        iterations: int = 2500,
        depth: int = 9,
        learning_rate: float = 0.03,
        l2_leaf_reg: float = 4.0,
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
        self._models_independent: list[CatBoostRegressor] | None = None
        self._use_multi: bool = True
        self._extra_features: list[str] | None = None

    def fit(
        self,
        train_df: pd.DataFrame,
        valid_df: pd.DataFrame | None = None,
        target_col: str = "ln_price",
        extra_features: list[str] | None = None,
        sample_weight_col: str | None = None,
    ) -> None:
        """CatBoost MultiQuantile 학습."""
        self._extra_features = extra_features
        x_train = _prepare_hedonic_features(train_df, extra_features)
        y_train = train_df[target_col].values
        mask = ~np.isnan(y_train)
        x_train = x_train[mask]
        y_train = y_train[mask]
        w_train = None
        if sample_weight_col and sample_weight_col in train_df.columns:
            w_train = train_df[sample_weight_col].values[mask]

        # 동적 cat_features 계산 (extra 포함)
        cat_indices = [
            i for i, col in enumerate(x_train.columns)
            if col in CAT_FEATURE_NAMES
        ]

        eval_set = None
        if valid_df is not None:
            x_valid = _prepare_hedonic_features(valid_df, extra_features)
            y_valid = valid_df[target_col].values
            v_mask = ~np.isnan(y_valid)
            eval_set = (x_valid[v_mask], y_valid[v_mask])

        logger.info("Training Model-A (MultiQuantile): train=%d", len(x_train))

        self._model = CatBoostRegressor(
            iterations=self.iterations,
            depth=self.depth,
            learning_rate=self.learning_rate,
            l2_leaf_reg=self.l2_leaf_reg,
            loss_function="MultiQuantile:alpha=0.25,0.5,0.75",
            cat_features=cat_indices,
            random_seed=self.random_seed,
            verbose=100,
            early_stopping_rounds=self.early_stopping_rounds,
        )

        try:
            self._model.fit(x_train, y_train, eval_set=eval_set, use_best_model=True,
                            sample_weight=w_train)
            logger.info("Model-A (MultiQuantile) best iteration: %d", self._model.best_iteration_)
            self._use_multi = True
        except (CatBoostError, ValueError) as exc:
            if "MultiQuantile" not in str(exc):
                raise  # MultiQuantile 비지원 외의 오류는 재발생
            logger.warning("MultiQuantile not supported (%s). Falling back.", exc)
            self._model = None
            self._use_multi = False
            self._models_independent = []
            for tau in [0.25, 0.50, 0.75]:
                m = CatBoostRegressor(
                    iterations=self.iterations,
                    depth=self.depth,
                    learning_rate=self.learning_rate,
                    l2_leaf_reg=self.l2_leaf_reg,
                    loss_function=f"Quantile:alpha={tau}",
                    cat_features=cat_indices,
                    random_seed=self.random_seed,
                    verbose=100,
                    early_stopping_rounds=self.early_stopping_rounds,
                )
                m.fit(x_train, y_train, eval_set=eval_set, use_best_model=True)
                self._models_independent.append(m)
                logger.info("Model-A (tau=%.2f) best iteration: %d", tau, m.best_iteration_)

    def predict_raw(self, df: pd.DataFrame) -> np.ndarray:
        """Raw quantile 예측 (log scale). shape: (n, 3) = [q25, q50, q75].

        MultiQuantile crossing이 발생하면 isotonic rearrangement를 적용한다.
        독립 3모델 fallback 시에도 동일하게 적용.
        """
        if self._model is None and self._models_independent is None:
            msg = "Model not fitted. Call fit() first."
            raise RuntimeError(msg)

        x_feat = _prepare_hedonic_features(df, self._extra_features)

        if self._use_multi and self._model is not None:
            preds = self._model.predict(x_feat)
            if preds.ndim == 1:
                preds = preds.reshape(-1, 1)
        else:
            # 독립 3모델 fallback
            cols = []
            for m in self._models_independent:  # type: ignore[union-attr]
                cols.append(m.predict(x_feat))
            preds = np.column_stack(cols)

        if preds.shape[1] >= 3:
            preds = _enforce_monotonicity(preds)
        return preds

    def predict(self, df: pd.DataFrame) -> dict[str, np.ndarray]:
        """exp 역변환된 가격 예측 (smearing 없음).

        Returns:
            dict with 'price_low', 'price_mid', 'price_high' (연속값).
        """
        raw = self.predict_raw(df)
        return {
            "price_low": np.exp(raw[:, 0]),
            "price_mid": np.exp(raw[:, 1]),
            "price_high": np.exp(raw[:, 2]),
        }

    def check_monotonicity(self, df: pd.DataFrame) -> float:
        """q25 <= q50 <= q75 만족 비율."""
        raw = self.predict_raw(df)
        q25, q50, q75 = raw[:, 0], raw[:, 1], raw[:, 2]
        monotone = (q25 <= q50) & (q50 <= q75)
        return float(monotone.mean())

    def save(self, path: str | Path) -> None:
        """모델 저장. fallback 시 3개 모델 개별 저장. extra_features 메타도 저장."""
        import json as _json

        p = Path(path)
        if self._use_multi and self._model is not None:
            self._model.save_model(str(p))
            logger.info("Model-A (multi) saved to %s", p)
        elif self._models_independent:
            for i, m in enumerate(self._models_independent):
                tau_path = p.with_stem(f"{p.stem}_q{i}")
                m.save_model(str(tau_path))
            logger.info("Model-A (3 independent) saved to %s_q*", p.stem)

        # extra_features ���타 저장
        meta_path = p.with_suffix(".meta.json")
        meta = {"extra_features": self._extra_features}
        with open(meta_path, "w") as f:
            _json.dump(meta, f)

    def load(self, path: str | Path) -> None:
        """모델 로드. fallback 파일 존재 시 3개 모델 로드. 메타도 복원."""
        import json as _json

        p = Path(path)
        q0_path = p.with_stem(f"{p.stem}_q0")
        if q0_path.exists():
            self._use_multi = False
            self._models_independent = []
            for i in range(3):
                tau_path = p.with_stem(f"{p.stem}_q{i}")
                m = CatBoostRegressor()
                m.load_model(str(tau_path))
                self._models_independent.append(m)
            logger.info("Model-A (3 independent) loaded from %s", p)
        else:
            self._use_multi = True
            self._model = CatBoostRegressor()
            self._model.load_model(str(p))
            logger.info("Model-A (multi) loaded from %s", p)

        # extra_features 메타 복원
        meta_path = p.with_suffix(".meta.json")
        if meta_path.exists():
            with open(meta_path) as f:
                meta = _json.load(f)
            self._extra_features = meta.get("extra_features")
        else:
            self._extra_features = None
