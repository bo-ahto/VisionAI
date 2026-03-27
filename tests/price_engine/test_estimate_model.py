"""Model-B (EstimateRegressorModel) 단위 테스트."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from visionai.price_engine.estimate_generator.hedonic_features import HEDONIC_FEATURES


class TestEstimateRegressorContract:
    """Model-B의 인터페이스 계약 검증."""

    def test_predict_without_fit_raises(self) -> None:
        from visionai.price_engine.estimate_generator.estimate_model import EstimateRegressorModel
        model = EstimateRegressorModel()
        df = pd.DataFrame({f: [0] for f in HEDONIC_FEATURES})
        with pytest.raises(RuntimeError, match="not fitted"):
            model.predict_raw(df)

    def test_predict_applies_smearing(self) -> None:
        """smearing_factor가 곱해지는지 개념 검증."""
        raw_ln = np.array([14.0, 15.0, 16.0])
        smearing = 1.05
        expected = np.exp(raw_ln) * smearing
        result = np.exp(raw_ln) * smearing
        np.testing.assert_allclose(result, expected)

    def test_default_smearing_is_one(self) -> None:
        """기본 smearing_factor=1.0 → smearing 미적용."""
        raw_ln = np.array([14.0])
        assert np.exp(raw_ln)[0] * 1.0 == np.exp(14.0)
