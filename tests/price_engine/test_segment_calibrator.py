"""segment_calibrator 단위 테스트."""
from __future__ import annotations

import numpy as np
import pandas as pd

from visionai.price_engine.models.segment_calibrator import (
    CalibrationFactors,
    apply_calibration,
    fit_calibration,
)


class TestFitCalibration:
    """calibration factor 학습 테스트."""

    def test_perfect_prediction_factor_is_one(self) -> None:
        y_true = np.array([100.0, 200.0, 300.0, 400.0, 500.0] * 3)
        y_pred = np.array([100.0, 200.0, 300.0, 400.0, 500.0] * 3)
        types = np.array(["위클리"] * 15)
        mids = np.array([1e6] * 15)
        factors = fit_calibration(y_true, y_pred, types, mids)
        assert abs(factors.by_auction_type["위클리"] - 1.0) < 0.01

    def test_overestimation_factor_below_one(self) -> None:
        y_true = np.array([100.0] * 15)
        y_pred = np.array([150.0] * 15)  # 과대추정
        types = np.array(["메이저"] * 15)
        mids = np.array([5e7] * 15)
        factors = fit_calibration(y_true, y_pred, types, mids)
        assert factors.by_auction_type["메이저"] < 1.0

    def test_underestimation_factor_above_one(self) -> None:
        y_true = np.array([200.0] * 15)
        y_pred = np.array([100.0] * 15)  # 과소추정
        types = np.array(["프리미엄"] * 15)
        mids = np.array([1e7] * 15)
        factors = fit_calibration(y_true, y_pred, types, mids)
        assert factors.by_auction_type["프리미엄"] > 1.0

    def test_auto_adjust_boosts_high_tier(self) -> None:
        """1억+ 구간은 자동 3% 상향."""
        y_true = np.array([2e8] * 15)
        y_pred = np.array([2e8] * 15)  # factor ≈ 1.0
        types = np.array(["메이저"] * 15)
        mids = np.array([2e8] * 15)
        factors = fit_calibration(y_true, y_pred, types, mids)
        # 1억+ tier의 factor가 1.0 × 1.03 = 1.03 근처
        tier_factor = factors.by_price_tier.get("1억+", 1.0)
        assert tier_factor > 1.0


class TestApplyCalibration:
    """calibration 적용 테스트."""

    def test_no_change_when_factor_is_one(self) -> None:
        y_pred = np.array([100.0, 200.0])
        factors = CalibrationFactors(
            by_auction_type={"메이저": 1.0},
            by_price_tier={"3000만~1억": 1.0},
        )
        types = np.array(["메이저", "메이저"])
        mids = np.array([5e7, 5e7])
        result = apply_calibration(y_pred, types, mids, factors, blend_weight=0.5)
        np.testing.assert_array_almost_equal(result, y_pred)

    def test_blend_weight_zero_uses_tier_only(self) -> None:
        y_pred = np.array([100.0])
        factors = CalibrationFactors(
            by_auction_type={"메이저": 2.0},  # type says 2x
            by_price_tier={"3000만~1억": 0.5},  # tier says 0.5x
        )
        types = np.array(["메이저"])
        mids = np.array([5e7])
        result = apply_calibration(y_pred, types, mids, factors, blend_weight=0.0)
        assert result[0] == 50.0  # 100 * 0.5

    def test_blend_weight_one_uses_type_only(self) -> None:
        y_pred = np.array([100.0])
        factors = CalibrationFactors(
            by_auction_type={"메이저": 2.0},
            by_price_tier={"3000만~1억": 0.5},
        )
        types = np.array(["메이저"])
        mids = np.array([5e7])
        result = apply_calibration(y_pred, types, mids, factors, blend_weight=1.0)
        assert result[0] == 200.0  # 100 * 2.0
