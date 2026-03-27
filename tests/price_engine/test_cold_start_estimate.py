"""3-tier Cold Start fallback + Bayesian shrinkage 테스트."""
from __future__ import annotations

import numpy as np
import pandas as pd

from visionai.price_engine.estimate_generator.cold_start import (
    assign_confidence_grade,
    compute_bayesian_shrinkage,
    get_cold_start_fallback,
)


def _make_works(n: int, medium: str, atype: str, session: int, price: float) -> pd.DataFrame:
    return pd.DataFrame({
        "회차": [session] * n,
        "타입": [atype] * n,
        "medium_category": [medium] * n,
        "낙찰가": [price] * n,
        "artist_clean": [f"artist_{i}" for i in range(n)],
        "상태": ["낙찰"] * n,
    })


class TestBayesianShrinkage:
    def test_formula(self) -> None:
        result = compute_bayesian_shrinkage(15.0, 14.0, n=20, m=10)
        expected = (20 * 15.0 + 10 * 14.0) / (20 + 10)
        assert abs(result - expected) < 1e-10

    def test_zero_count_equals_global(self) -> None:
        result = compute_bayesian_shrinkage(15.0, 14.0, n=0, m=10)
        assert abs(result - 14.0) < 1e-10

    def test_large_count_approaches_group(self) -> None:
        result = compute_bayesian_shrinkage(15.0, 14.0, n=10000, m=10)
        assert abs(result - 15.0) < 0.01


class TestColdStartFallback:
    def test_tier1_fallback(self) -> None:
        works = _make_works(50, "유화", "메이저", session=10, price=5_000_000)
        result = get_cold_start_fallback("유화", "메이저", works, cutoff=100)
        assert result.tier == 1
        assert result.group_size == 50

    def test_tier2_fallback(self) -> None:
        works = _make_works(60, "유화", "메이저", session=10, price=5_000_000)
        # Tier 1 부족 (다른 auction_type 요청)
        result = get_cold_start_fallback("유화", "위클리", works, cutoff=100)
        assert result.tier == 2
        assert result.group_size == 60

    def test_tier3_fallback(self) -> None:
        works = _make_works(10, "조각/공예", "위클리", session=10, price=3_000_000)
        result = get_cold_start_fallback("사진/디지털", "위클리", works, cutoff=100)
        assert result.tier == 3

    def test_min_count_tier1(self) -> None:
        works = _make_works(20, "유화", "메이저", session=10, price=5_000_000)
        result = get_cold_start_fallback("유화", "메이저", works, cutoff=100)
        # 20 < 30 → Tier 1 미달, Tier 2 시도 (20 < 50 → Tier 3)
        assert result.tier == 3


class TestConfidenceGrade:
    def test_a_grade(self) -> None:
        grade = assign_confidence_grade(
            artist_total_sold=25, is_new_artist=False, cold_start_tier=0
        )
        assert grade == "A"

    def test_b_grade(self) -> None:
        grade = assign_confidence_grade(
            artist_total_sold=10, is_new_artist=False, cold_start_tier=0
        )
        assert grade == "B"

    def test_c_grade_low_sold(self) -> None:
        grade = assign_confidence_grade(
            artist_total_sold=3, is_new_artist=False, cold_start_tier=0
        )
        assert grade == "C"

    def test_c_grade_high_unsold(self) -> None:
        grade = assign_confidence_grade(
            artist_total_sold=10, is_new_artist=False, cold_start_tier=0,
            artist_unsold_rate=0.6,
        )
        assert grade == "C"

    def test_d_grade_new_artist(self) -> None:
        grade = assign_confidence_grade(
            artist_total_sold=0, is_new_artist=True, cold_start_tier=3
        )
        assert grade == "D"

    def test_d_grade_high_tier(self) -> None:
        grade = assign_confidence_grade(
            artist_total_sold=5, is_new_artist=False, cold_start_tier=2
        )
        assert grade == "D"
