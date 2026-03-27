"""Selection bias 보정 테스트."""
from __future__ import annotations

from visionai.price_engine.estimate_generator.selection_bias import (
    adjust_for_selection_bias,
)


class TestSelectionBias:
    def test_no_adjustment_below_threshold(self) -> None:
        low, mid, high, grade = adjust_for_selection_bias(
            price_low=800, price_mid=1000, price_high=1200,
            artist_unsold_rate=0.3, group_unsold_rate=0.2,
            confidence_grade="B",
        )
        assert low == 800
        assert high == 1200
        assert grade == "B"

    def test_expansion_on_high_artist_unsold(self) -> None:
        low, mid, high, grade = adjust_for_selection_bias(
            price_low=800, price_mid=1000, price_high=1200,
            artist_unsold_rate=0.6, group_unsold_rate=0.2,
            confidence_grade="B",
        )
        # 구간 확장: half_width=200 → 200*1.3=260
        assert low == 1000 - 260  # 740
        assert high == 1000 + 260  # 1260
        assert grade == "C"

    def test_expansion_on_high_group_unsold(self) -> None:
        low, mid, high, grade = adjust_for_selection_bias(
            price_low=800, price_mid=1000, price_high=1200,
            artist_unsold_rate=0.2, group_unsold_rate=0.45,
            confidence_grade="A",
        )
        assert high > 1200
        assert grade == "C"

    def test_grade_downgrade_a_to_c(self) -> None:
        _, _, _, grade = adjust_for_selection_bias(
            price_low=800, price_mid=1000, price_high=1200,
            artist_unsold_rate=0.6, group_unsold_rate=None,
            confidence_grade="A",
        )
        assert grade == "C"

    def test_grade_d_stays_d(self) -> None:
        _, _, _, grade = adjust_for_selection_bias(
            price_low=800, price_mid=1000, price_high=1200,
            artist_unsold_rate=0.6, group_unsold_rate=None,
            confidence_grade="D",
        )
        assert grade == "D"

    def test_none_rates_no_adjustment(self) -> None:
        low, mid, high, grade = adjust_for_selection_bias(
            price_low=800, price_mid=1000, price_high=1200,
            artist_unsold_rate=None, group_unsold_rate=None,
            confidence_grade="A",
        )
        assert low == 800
        assert grade == "A"

    def test_negative_low_clamped_to_zero(self) -> None:
        low, mid, high, grade = adjust_for_selection_bias(
            price_low=50, price_mid=100, price_high=150,
            artist_unsold_rate=0.6, group_unsold_rate=None,
            confidence_grade="B",
        )
        assert low >= 0

    def test_asymmetric_interval_expands_both_sides(self) -> None:
        """비대칭 구간에서 상한이 축소되지 않아야 한다."""
        low, mid, high, grade = adjust_for_selection_bias(
            price_low=90, price_mid=100, price_high=200,
            artist_unsold_rate=0.6, group_unsold_rate=None,
            confidence_grade="B",
        )
        # low→mid=10, mid→high=100. 각각 1.3배 확장
        assert low < 90   # 100 - 10*1.3 = 87
        assert high > 200  # 100 + 100*1.3 = 230
        assert grade == "C"

    def test_symmetric_interval_expands_evenly(self) -> None:
        low, mid, high, grade = adjust_for_selection_bias(
            price_low=800, price_mid=1000, price_high=1200,
            artist_unsold_rate=0.6, group_unsold_rate=None,
            confidence_grade="A",
        )
        # 대칭: 200 * 1.3 = 260
        assert abs(low - 740) < 1
        assert abs(high - 1260) < 1
