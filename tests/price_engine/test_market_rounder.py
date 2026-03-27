"""호 단위 라운딩 테스트 — half-up rounding 포함."""
from __future__ import annotations

from visionai.price_engine.estimate_generator.market_rounder import round_to_market_unit


class TestMarketRounder:
    def test_under_1m(self) -> None:
        assert round_to_market_unit(800_000) == 800_000
        assert round_to_market_unit(350_000) == 400_000
        assert round_to_market_unit(150_000) == 200_000

    def test_1m_to_5m(self) -> None:
        assert round_to_market_unit(3_500_000) == 3_500_000
        assert round_to_market_unit(3_200_000) == 3_000_000
        assert round_to_market_unit(1_200_000) == 1_000_000

    def test_5m_to_10m(self) -> None:
        assert round_to_market_unit(7_500_000) == 8_000_000
        assert round_to_market_unit(5_400_000) == 5_000_000

    def test_10m_to_50m(self) -> None:
        assert round_to_market_unit(32_000_000) == 30_000_000
        assert round_to_market_unit(13_000_000) == 15_000_000

    def test_50m_to_100m(self) -> None:
        assert round_to_market_unit(75_000_000) == 80_000_000
        assert round_to_market_unit(55_000_000) == 60_000_000

    def test_over_100m(self) -> None:
        assert round_to_market_unit(230_000_000) == 250_000_000
        assert round_to_market_unit(120_000_000) == 100_000_000

    def test_boundary_values(self) -> None:
        assert round_to_market_unit(1_000_000) == 1_000_000
        assert round_to_market_unit(5_000_000) == 5_000_000
        assert round_to_market_unit(10_000_000) == 10_000_000
        assert round_to_market_unit(50_000_000) == 50_000_000
        assert round_to_market_unit(100_000_000) == 100_000_000
        assert round_to_market_unit(0) == 0
        assert round_to_market_unit(-100) == 0

    def test_half_up_tie_cases(self) -> None:
        """Half-up rounding: 0.5 → 올림 (banker's rounding과 다름)."""
        # 50만 단위: 1,250,000 → half-up = 1,500,000
        assert round_to_market_unit(1_250_000) == 1_500_000
        # 500만 단위: 12,500,000 → half-up = 15,000,000
        assert round_to_market_unit(12_500_000) == 15_000_000
        # 10만 단위: 250,000 → half-up = 300,000
        assert round_to_market_unit(250_000) == 300_000
        # 100만 단위: 7,500,000 → half-up = 8,000,000
        assert round_to_market_unit(7_500_000) == 8_000_000
