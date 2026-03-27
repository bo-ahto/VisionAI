"""Reliability Model — Pr(APE ≤ threshold) 예측.

기획서 5.2 Phase 2: holdout에서 실제 APE를 구한 뒤,
메타피처로 "이 예측이 얼마나 믿을 만한가"를 학습한다.

등급 산정:
  Pr(APE ≤ 0.2) ≥ 0.65  →  A
  Pr(APE ≤ 0.3) ≥ 0.60  →  B
  Pr(APE ≤ 0.3) ≥ 0.40  →  C
  나머지                  →  D
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV

logger = logging.getLogger(__name__)


class ReliabilityModel:
    """Pr(APE ≤ threshold) 이진 분류 모델."""

    def __init__(self, threshold: float = 0.2) -> None:
        self.threshold = threshold
        self.model: CalibratedClassifierCV | None = None

    def fit(
        self,
        meta_features: pd.DataFrame,
        y_true: np.ndarray,
        y_pred: np.ndarray,
    ) -> None:
        """holdout에서 학습한다.

        Args:
            meta_features: 메타피처 DataFrame (5개 컬럼).
            y_true: 실제 낙찰가.
            y_pred: 모델 예측 낙찰가.
        """
        ape = np.abs(y_true - y_pred) / y_true
        target = (ape <= self.threshold).astype(int)

        logger.info(
            "Reliability training: N=%d, positive rate=%.1f%% (APE ≤ %.0f%%)",
            len(target), target.mean() * 100, self.threshold * 100,
        )

        base = GradientBoostingClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.1,
            random_state=42,
        )

        # Platt scaling으로 확률 calibration
        self.model = CalibratedClassifierCV(base, cv=3, method="sigmoid")
        self.model.fit(meta_features.values, target)

        # 학습 세트 성능
        proba = self.model.predict_proba(meta_features.values)[:, 1]
        from sklearn.metrics import roc_auc_score
        auc = roc_auc_score(target, proba)
        logger.info("Reliability AUC: %.4f", auc)

    def predict_proba(self, meta_features: pd.DataFrame) -> np.ndarray:
        """Pr(APE ≤ threshold) 확률을 반환한다."""
        if self.model is None:
            msg = "Model not fitted"
            raise RuntimeError(msg)
        return self.model.predict_proba(meta_features.values)[:, 1]

    def assign_grades(self, meta_features: pd.DataFrame) -> pd.Series:
        """확률 기반 A/B/C/D 등급을 산정한다.

        기획서 5.2:
          Pr(APE ≤ 0.2) ≥ 0.65  →  A
          Pr(APE ≤ 0.3) ≥ 0.60  →  B  (threshold 0.3은 별도 모델 필요)
          Pr(APE ≤ 0.3) ≥ 0.40  →  C
          나머지                  →  D

        현재는 단일 threshold(0.2)로 간소화:
          Pr ≥ 0.65 → A
          Pr ≥ 0.45 → B
          Pr ≥ 0.25 → C
          나머지    → D
        """
        proba = self.predict_proba(meta_features)
        grades = pd.Series("D", index=meta_features.index, dtype="object")
        grades[proba >= 0.25] = "C"
        grades[proba >= 0.45] = "B"
        grades[proba >= 0.65] = "A"
        return grades
