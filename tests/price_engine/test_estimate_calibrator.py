"""Estimate Calibrator 테스트."""
from __future__ import annotations

import numpy as np
import pytest

from visionai.price_engine.estimate_generator.estimate_calibrator import (
    EstimateCalibrator,
)


def _make_estimate_calib_data(
    n: int = 200, seed: int = 42
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    y_actual = rng.normal(15.0, 1.5, n)
    y_pred = y_actual + rng.normal(0, 0.2, n)
    est_mid = np.exp(y_actual) * (1 + rng.normal(0, 0.1, n))
    est_low = est_mid * rng.uniform(0.7, 0.9, n)
    est_high = est_mid * rng.uniform(1.1, 1.3, n)
    return y_pred, y_actual, est_low, est_mid, est_high


class TestEstimateCalibrator:
    def test_segment_bin_balance(self) -> None:
        y_pred, y_actual, est_low, est_mid, est_high = _make_estimate_calib_data()
        cal = EstimateCalibrator()
        cal.fit(y_pred, y_actual, est_low, est_mid, est_high)
        assert cal.boundaries is not None
        assert len(cal.boundaries) == 4

    def test_boundaries_from_actual_not_predicted(self) -> None:
        """경계가 실제 추정가(y_actual) 분위수 기준인지 검증."""
        y_pred, y_actual, est_low, est_mid, est_high = _make_estimate_calib_data()
        cal = EstimateCalibrator()
        cal.fit(y_pred, y_actual, est_low, est_mid, est_high)
        expected = np.quantile(y_actual, [0.2, 0.4, 0.6, 0.8])
        np.testing.assert_allclose(cal.boundaries, expected, rtol=1e-10)

    def test_smearing_factor_positive(self) -> None:
        y_pred, y_actual, est_low, est_mid, est_high = _make_estimate_calib_data()
        cal = EstimateCalibrator()
        cal.fit(y_pred, y_actual, est_low, est_mid, est_high)
        for seg, sf in cal.smearing_factors.items():
            assert sf > 0

    def test_ratio_range(self) -> None:
        y_pred, y_actual, est_low, est_mid, est_high = _make_estimate_calib_data()
        cal = EstimateCalibrator()
        cal.fit(y_pred, y_actual, est_low, est_mid, est_high)
        for seg in cal.ratios_low:
            assert cal.ratios_low[seg] < 1.0
            assert cal.ratios_high[seg] > 1.0

    def test_transform_output_shape(self) -> None:
        y_pred, y_actual, est_low, est_mid, est_high = _make_estimate_calib_data()
        cal = EstimateCalibrator()
        cal.fit(y_pred, y_actual, est_low, est_mid, est_high)
        result = cal.transform(y_pred)
        assert result["est_low"].shape == y_pred.shape

    def test_transform_low_le_mid_le_high(self) -> None:
        y_pred, y_actual, est_low, est_mid, est_high = _make_estimate_calib_data()
        cal = EstimateCalibrator()
        cal.fit(y_pred, y_actual, est_low, est_mid, est_high)
        result = cal.transform(y_pred)
        assert np.all(result["est_low"] <= result["est_mid"] + 1e-6)
        assert np.all(result["est_mid"] <= result["est_high"] + 1e-6)

    def test_bootstrap_stability_strict(self) -> None:
        """기획서 기준: bootstrap CI 폭 <= 0.2 (±0.1)."""
        y_pred, y_actual, est_low, est_mid, est_high = _make_estimate_calib_data(500)
        cal = EstimateCalibrator()
        cal.fit(y_pred, y_actual, est_low, est_mid, est_high)
        ci = cal.validate_stability(y_pred, y_actual, n_bootstrap=100)
        for seg, (lo, hi) in ci.items():
            if np.isfinite(lo) and np.isfinite(hi):
                width = hi - lo
                assert width <= 0.2, f"Segment {seg} CI width {width:.3f} > 0.2"

    def test_small_bin_merge(self) -> None:
        """nₛ < 30이면 인접 bin 병합."""
        rng = np.random.default_rng(42)
        # 대부분 1개 세그먼트에 몰리는 데이터
        y_actual = np.concatenate([rng.normal(15, 0.1, 180), rng.normal(20, 0.1, 20)])
        y_pred = y_actual + rng.normal(0, 0.1, 200)
        est_mid = np.exp(y_actual)
        est_low = est_mid * 0.8
        est_high = est_mid * 1.2
        cal = EstimateCalibrator()
        cal.fit(y_pred, y_actual, est_low, est_mid, est_high)
        # 모든 segment에 smearing factor가 있어야 함 (merge 후)
        for seg in range(5):
            assert seg in cal.smearing_factors

    def test_transform_without_fit_raises(self) -> None:
        cal = EstimateCalibrator()
        with pytest.raises(RuntimeError, match="not fitted"):
            cal.transform(np.zeros(10))

    def test_empty_calib_not_fitted(self) -> None:
        """빈 calib set이면 fitted 상태가 되지 않아야 함."""
        cal = EstimateCalibrator()
        cal.fit(np.array([]), np.array([]), np.array([]), np.array([]), np.array([]))
        assert not cal._fitted

    def test_refit_empty_resets_state(self) -> None:
        """이미 fit된 인스턴스에 빈 calib → _fitted=False로 리셋."""
        y_pred, y_actual, est_low, est_mid, est_high = _make_estimate_calib_data()
        cal = EstimateCalibrator()
        cal.fit(y_pred, y_actual, est_low, est_mid, est_high)
        assert cal._fitted
        # 빈 데이터로 re-fit
        cal.fit(np.array([]), np.array([]), np.array([]), np.array([]), np.array([]))
        assert not cal._fitted
        assert cal.boundaries is None
        assert len(cal.smearing_factors) == 0
