"""Model-A (HedonicQuantileModel) 단위 테스트."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from visionai.price_engine.estimate_generator.hedonic_features import HEDONIC_FEATURES


class TestHedonicQuantileModelContract:
    """Model-A의 인터페이스 계약 검증 (실제 학습 없이)."""

    def test_hedonic_features_count(self) -> None:
        # 2026-04-17 Cold Start SHAP 분석 후 해로운 4개 제거 (50 → 46).
        assert len(HEDONIC_FEATURES) == 46

    def test_cat_feature_indices(self) -> None:
        from visionai.price_engine.estimate_generator.quantile_model import HEDONIC_CAT_INDICES
        # 범주형: artist_clean(0), medium_category(1), support_category(2), is_3d(3),
        # is_untitled(4), title_subject(35), size_bucket(39), orientation(40),
        # artist_nationality(45)
        expected = [0, 1, 2, 3, 4, 35, 39, 40, 45]
        assert HEDONIC_CAT_INDICES == expected

    def test_predict_without_fit_raises(self) -> None:
        from visionai.price_engine.estimate_generator.quantile_model import HedonicQuantileModel
        model = HedonicQuantileModel()
        df = pd.DataFrame({f: [0] for f in HEDONIC_FEATURES})
        with pytest.raises(RuntimeError, match="not fitted"):
            model.predict_raw(df)

    def test_prepare_features_converts_cat_to_str(self) -> None:
        from visionai.price_engine.estimate_generator.quantile_model import _prepare_hedonic_features
        df = pd.DataFrame({f: [1] for f in HEDONIC_FEATURES})
        df["is_3d"] = True
        df["is_untitled"] = False
        result = _prepare_hedonic_features(df)
        assert pd.api.types.is_string_dtype(result["is_3d"])
        assert pd.api.types.is_string_dtype(result["is_untitled"])


class TestMonotonicity:
    """Isotonic rearrangement 검증."""

    def test_already_monotone(self) -> None:
        from visionai.price_engine.estimate_generator.quantile_model import _enforce_monotonicity
        preds = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        result = _enforce_monotonicity(preds)
        np.testing.assert_array_equal(result, preds)

    def test_crossing_fixed_pav(self) -> None:
        from visionai.price_engine.estimate_generator.quantile_model import _enforce_monotonicity
        # q25=3, q50=1, q75=2 → crossing → PAV pooled average
        preds = np.array([[3.0, 1.0, 2.0]])
        result = _enforce_monotonicity(preds)
        assert result[0, 0] <= result[0, 1] <= result[0, 2]
        # PAV: (3,1)→2.0, then (2.0,2)→2.0 → all 2.0
        np.testing.assert_allclose(result[0], [2.0, 2.0, 2.0])

    def test_all_equal(self) -> None:
        from visionai.price_engine.estimate_generator.quantile_model import _enforce_monotonicity
        preds = np.array([[5.0, 5.0, 5.0]])
        result = _enforce_monotonicity(preds)
        assert result[0, 0] == result[0, 1] == result[0, 2]

    def test_reverse_order_fixed(self) -> None:
        from visionai.price_engine.estimate_generator.quantile_model import _enforce_monotonicity
        preds = np.array([[10.0, 5.0, 1.0]])
        result = _enforce_monotonicity(preds)
        assert result[0, 0] <= result[0, 1] <= result[0, 2]


class TestEmptyMetrics:
    """빈 배열 방어 테스트."""

    def test_pinball_empty(self) -> None:
        from visionai.price_engine.validation.metrics import compute_pinball_loss
        assert np.isnan(compute_pinball_loss(np.array([]), np.array([]), 0.5))

    def test_interval_score_empty(self) -> None:
        from visionai.price_engine.validation.metrics import compute_interval_score
        assert np.isnan(compute_interval_score(np.array([]), np.array([]), np.array([])))

    def test_coverage_empty(self) -> None:
        from visionai.price_engine.validation.metrics import compute_coverage_rate
        assert np.isnan(compute_coverage_rate(np.array([]), np.array([]), np.array([])))
