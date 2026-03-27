"""Phase 3 metrics 함수 테스트."""
from __future__ import annotations

import numpy as np

from visionai.price_engine.validation.metrics import (
    compute_coverage_rate,
    compute_estimate_bias,
    compute_estimate_mape,
    compute_interval_score,
    compute_pinball_loss,
    compute_pinball_loss_total,
    compute_range_width,
)


class TestPinballLoss:
    def test_perfect_prediction(self) -> None:
        y = np.array([1.0, 2.0, 3.0])
        assert compute_pinball_loss(y, y, tau=0.5) == 0.0

    def test_underprediction_tau50(self) -> None:
        y = np.array([10.0])
        q = np.array([8.0])
        # residual = 2, tau=0.5 → loss = 0.5*2 = 1.0
        assert abs(compute_pinball_loss(y, q, tau=0.5) - 1.0) < 1e-10

    def test_overprediction_tau50(self) -> None:
        y = np.array([8.0])
        q = np.array([10.0])
        # residual = -2, tau=0.5 → loss = (0.5-1)*(-2) = 1.0
        assert abs(compute_pinball_loss(y, q, tau=0.5) - 1.0) < 1e-10

    def test_asymmetric_tau25(self) -> None:
        y = np.array([10.0])
        q = np.array([8.0])
        # residual = 2, tau=0.25 → loss = 0.25*2 = 0.5
        assert abs(compute_pinball_loss(y, q, tau=0.25) - 0.5) < 1e-10

    def test_total_sums_across_quantiles(self) -> None:
        y = np.array([10.0, 10.0])
        q = np.column_stack([
            np.array([8.0, 8.0]),   # q25
            np.array([10.0, 10.0]), # q50
            np.array([12.0, 12.0]), # q75
        ])
        total = compute_pinball_loss_total(y, q)
        # q25: 0.25*2=0.5, q50: 0, q75: (0.75-1)*(-2)=0.5 → total=1.0
        assert abs(total - 1.0) < 1e-10


class TestIntervalScore:
    def test_perfect_coverage(self) -> None:
        y = np.array([5.0, 5.0])
        q_low = np.array([3.0, 3.0])
        q_high = np.array([7.0, 7.0])
        # width=4, no undershoot/overshoot → IS = 4
        assert abs(compute_interval_score(y, q_low, q_high) - 4.0) < 1e-10

    def test_undershoot_penalty(self) -> None:
        y = np.array([2.0])
        q_low = np.array([3.0])
        q_high = np.array([7.0])
        # width=4, undershoot=1, penalty=2/0.5*1=4 → IS=8
        assert abs(compute_interval_score(y, q_low, q_high, alpha=0.5) - 8.0) < 1e-10


class TestCoverageRate:
    def test_all_covered(self) -> None:
        y = np.array([5.0, 6.0])
        assert compute_coverage_rate(y, np.array([4.0, 4.0]), np.array([7.0, 7.0])) == 1.0

    def test_none_covered(self) -> None:
        y = np.array([1.0, 2.0])
        assert compute_coverage_rate(y, np.array([5.0, 5.0]), np.array([10.0, 10.0])) == 0.0

    def test_half_covered(self) -> None:
        y = np.array([5.0, 1.0])
        rate = compute_coverage_rate(y, np.array([4.0, 4.0]), np.array([6.0, 6.0]))
        assert abs(rate - 0.5) < 1e-10


class TestRangeWidth:
    def test_basic(self) -> None:
        q_low = np.array([80.0, 90.0])
        q_mid = np.array([100.0, 100.0])
        q_high = np.array([120.0, 110.0])
        # ratios: 40/100=0.4, 20/100=0.2 → median=0.3
        assert abs(compute_range_width(q_low, q_mid, q_high) - 0.3) < 1e-10


class TestEstimateMAPE:
    def test_perfect(self) -> None:
        actual = np.array([100.0, 200.0])
        assert compute_estimate_mape(actual, actual) == 0.0

    def test_basic(self) -> None:
        gen = np.array([120.0, 180.0])
        actual = np.array([100.0, 200.0])
        # ape: 20/100=0.2, 20/200=0.1 → mean=0.15 → 15%
        assert abs(compute_estimate_mape(gen, actual) - 15.0) < 1e-10


class TestEstimateBias:
    def test_no_bias(self) -> None:
        actual = np.array([100.0, 200.0])
        assert abs(compute_estimate_bias(actual, actual) - 1.0) < 1e-10

    def test_overestimate(self) -> None:
        gen = np.array([120.0, 240.0])
        actual = np.array([100.0, 200.0])
        # ratios: 1.2, 1.2 → median=1.2
        assert abs(compute_estimate_bias(gen, actual) - 1.2) < 1e-10
