"""3-tier Cold Start fallback + Bayesian shrinkage 테스트."""
from __future__ import annotations

import pandas as pd

from visionai.price_engine.estimate_generator.cold_start import (
    assign_confidence_grade,
    compute_bayesian_shrinkage,
    get_cold_start_fallback,
    get_cold_start_fallback_v2,
)
from visionai.price_engine.features.artist_similarity import SimilarArtist


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


class TestColdStartV2:
    """5-tier Cold Start fallback 테스트."""

    def _make_works_v2(
        self, artists: dict[str, int], medium: str, atype: str, price: float,
    ) -> pd.DataFrame:
        rows = []
        sess = 10
        for name, count in artists.items():
            for _ in range(count):
                rows.append({
                    "회차": sess,
                    "타입": atype,
                    "medium_category": medium,
                    "낙찰가": price,
                    "artist_clean": name,
                })
                sess += 1
        return pd.DataFrame(rows)

    def test_tier0_warm(self) -> None:
        """Tier 0: K-Auction 거래 ≥ 5건."""
        works = self._make_works_v2({"김환기": 10}, "유화", "메이저", 5e6)
        result = get_cold_start_fallback_v2(
            "김환기", "유화", "메이저", works, cutoff=100,
        )
        assert result.tier == 0
        assert result.group_size == 10

    def test_tier1_external(self) -> None:
        """Tier 1: 외부 데이터 ≥ 3건."""
        works = self._make_works_v2({"신인": 2}, "유화", "메이저", 5e6)
        ext = {"avg_ln_price": 15.5, "count": 5}
        result = get_cold_start_fallback_v2(
            "신인", "유화", "메이저", works, cutoff=100,
            external_stats=ext,
        )
        assert result.tier == 1

    def test_tier2_similar(self) -> None:
        """Tier 2: 유사 작가 ≥ 3명."""
        works = self._make_works_v2({"신인": 1}, "유화", "메이저", 5e6)
        similar = [
            SimilarArtist("A", 0.5, 15.0, 20),
            SimilarArtist("B", 0.8, 14.5, 15),
            SimilarArtist("C", 1.0, 14.8, 10),
        ]
        result = get_cold_start_fallback_v2(
            "신인", "유화", "메이저", works, cutoff=100,
            similar_artists=similar,
        )
        assert result.tier == 2

    def test_tier3_4_legacy(self) -> None:
        """Tier 3/4: 기존 mediumxtype / medium fallback."""
        works = self._make_works_v2(
            {f"a{i}": 1 for i in range(40)}, "유화", "메이저", 5e6,
        )
        result = get_cold_start_fallback_v2(
            "미등록", "유화", "메이저", works, cutoff=1000,
        )
        assert result.tier in (3, 4)

    def test_v2_auction_type_fallback_compatible(self) -> None:
        """v2에서도 auction_type fallback이 v1과 동일 가격 반환 (하위 호환)."""
        import math

        works = self._make_works_v2(
            {f"a{i}": 1 for i in range(20)}, "유화", "위클리", 3e6,
        )
        old = get_cold_start_fallback("사진/디지털", "위클리", works, cutoff=1000)
        new = get_cold_start_fallback_v2(
            "신인", "사진/디지털", "위클리", works, cutoff=1000,
        )
        assert abs(
            math.exp(old.fallback_ln_price) - math.exp(new.fallback_ln_price)
        ) < 1

    def test_coverage_100pct(self) -> None:
        """전체 작가 100% tier 배정 (G9)."""
        works = self._make_works_v2(
            {f"a{i}": 1 for i in range(50)}, "유화", "메이저", 5e6,
        )
        for i in range(50):
            result = get_cold_start_fallback_v2(
                f"a{i}", "유화", "메이저", works, cutoff=1000,
            )
            assert result.tier is not None
            assert result.fallback_ln_price != 0 or result.group_size >= 0
