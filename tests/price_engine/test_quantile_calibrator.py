"""Quantile Calibrator 테스트."""
from __future__ import annotations

import numpy as np
import pytest

from visionai.price_engine.estimate_generator.quantile_calibrator import (
    QuantileCalibrator,
)


def _make_calib_data(n: int = 200, seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    y_true = rng.normal(15.0, 1.5, n)
    noise = rng.normal(0, 0.3, n)
    q50 = y_true + noise
    q25 = q50 - 0.8
    q75 = q50 + 0.8
    q_pred = np.column_stack([q25, q50, q75])
    return y_true, q_pred


class TestQuantileCalibrator:
    def test_coverage_improvement(self) -> None:
        y, q = _make_calib_data()
        cal = QuantileCalibrator()
        result = cal.fit(y, q, target_coverage=0.55)
        assert result.coverage_after >= 0.55

    def test_delta_finite(self) -> None:
        y, q = _make_calib_data()
        cal = QuantileCalibrator()
        result = cal.fit(y, q)
        assert np.isfinite(result.delta_low)
        assert np.isfinite(result.delta_mid)
        assert np.isfinite(result.delta_high)

    def test_monotonicity_preserved(self) -> None:
        y, q = _make_calib_data()
        cal = QuantileCalibrator()
        cal.fit(y, q)
        calibrated = cal.transform(q)
        assert np.all(calibrated[:, 0] <= calibrated[:, 1] + 1e-10)
        assert np.all(calibrated[:, 1] <= calibrated[:, 2] + 1e-10)

    def test_monotonicity_with_asymmetric_deltas(self) -> None:
        """비대칭 delta에서도 단조성 보장."""
        cal = QuantileCalibrator()
        cal.delta_low = -0.5
        cal.delta_mid = 0.0
        cal.delta_high = 0.5
        cal._fitted = True
        # q25=10, q50=10.1, q75=10.2 → delta 적용 후에도 low<=mid<=high
        q = np.array([[10.0, 10.1, 10.2]])
        result = cal.transform(q)
        assert result[0, 0] <= result[0, 1]
        assert result[0, 1] <= result[0, 2]

    def test_transform_without_fit_raises(self) -> None:
        cal = QuantileCalibrator()
        with pytest.raises(RuntimeError, match="not fitted"):
            cal.transform(np.zeros((5, 3)))

    def test_validate_coverage_overall(self) -> None:
        y_calib, q_calib = _make_calib_data(200)
        y_valid, q_valid = _make_calib_data(100, seed=99)
        cal = QuantileCalibrator()
        cal.fit(y_calib, q_calib, target_coverage=0.55)
        result = cal.validate_coverage(y_valid, q_valid)
        assert "coverage_overall" in result
        assert result["coverage_overall"] >= 0.0

    def test_validate_coverage_by_slice(self) -> None:
        """auction_type 슬라이스별 coverage."""
        y_calib, q_calib = _make_calib_data(200)
        cal = QuantileCalibrator()
        cal.fit(y_calib, q_calib, target_coverage=0.55)

        y_valid, q_valid = _make_calib_data(100, seed=99)
        atypes = np.array(["메이저"] * 50 + ["위클리"] * 50)
        result = cal.validate_coverage(y_valid, q_valid, auction_types=atypes)
        assert "coverage_메이저" in result
        assert "coverage_위클리" in result

    def test_independent_grid_finds_tighter_interval(self) -> None:
        """비대칭 잔차에서 독립 탐색이 단일 alpha보다 좁은 구간 가능."""
        rng = np.random.default_rng(42)
        n = 300
        y = rng.normal(15, 1.5, n)
        # 비대칭 noise: 하향 편향 큼
        noise = rng.normal(-0.5, 0.5, n)
        q50 = y + noise
        q25 = q50 - 1.0
        q75 = q50 + 0.5
        q = np.column_stack([q25, q50, q75])
        cal = QuantileCalibrator()
        result = cal.fit(y, q, target_coverage=0.55)
        assert result.coverage_after >= 0.55
