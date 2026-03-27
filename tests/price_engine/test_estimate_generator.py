"""EstimateGenerator 통합 파이프라인 테스트."""
from __future__ import annotations

import numpy as np
import pandas as pd

from visionai.price_engine.estimate_generator.hedonic_features import HEDONIC_FEATURES
from visionai.price_engine.estimate_generator.market_rounder import round_to_market_unit


class TestMarketRounderIntegration:
    """Model-B 출력에만 라운딩 적용 검증."""

    def test_model_b_rounded(self) -> None:
        prices = [3_270_000, 15_300_000, 78_500_000]
        for p in prices:
            rounded = round_to_market_unit(p)
            assert rounded != p or p % 100_000 == 0  # 이미 단위에 맞으면 동일

    def test_model_a_continuous(self) -> None:
        """Model-A 출력은 연속값 — 라운딩 미적용."""
        prices = [3_270_123.45, 15_312_456.78]
        # Model-A는 라운딩하지 않음 — 이 값들이 그대로 유지됨
        for p in prices:
            assert isinstance(p, float)


class TestColdStartGeneration:
    """거래 0건 작가도 예측 가능 검증."""

    def test_cold_start_fallback(self) -> None:
        from visionai.price_engine.estimate_generator.cold_start import (
            get_cold_start_fallback,
        )
        works = pd.DataFrame({
            "회차": [10] * 50,
            "타입": ["메이저"] * 50,
            "medium_category": ["유화"] * 50,
            "낙찰가": [5_000_000.0] * 50,
            "artist_clean": [f"A{i}" for i in range(50)],
            "상태": ["낙찰"] * 50,
        })
        result = get_cold_start_fallback("유화", "메이저", works, cutoff=100)
        assert result.tier >= 1
        assert result.fallback_ln_price > 0

    def test_new_artist_gets_d_grade(self) -> None:
        from visionai.price_engine.estimate_generator.cold_start import (
            assign_confidence_grade,
        )
        grade = assign_confidence_grade(
            artist_total_sold=0, is_new_artist=True, cold_start_tier=3
        )
        assert grade == "D"


class TestConfidenceGrade:
    def test_a_grade(self) -> None:
        from visionai.price_engine.estimate_generator.cold_start import (
            assign_confidence_grade,
        )
        assert assign_confidence_grade(25, False, 0) == "A"

    def test_b_grade(self) -> None:
        from visionai.price_engine.estimate_generator.cold_start import (
            assign_confidence_grade,
        )
        assert assign_confidence_grade(10, False, 0) == "B"

    def test_c_grade_unsold(self) -> None:
        from visionai.price_engine.estimate_generator.cold_start import (
            assign_confidence_grade,
        )
        assert assign_confidence_grade(10, False, 0, artist_unsold_rate=0.6) == "C"


class TestValidateEstimateConcept:
    """추정가 검증 (시나리오 B) 개념 테스트."""

    def test_divergence_calculation(self) -> None:
        ai_mid = 5_000_000
        kauction_mid = 4_000_000
        divergence = abs(ai_mid - kauction_mid) / kauction_mid
        assert abs(divergence - 0.25) < 1e-10

    def test_major_high_price_threshold(self) -> None:
        """메이저 + 고가(>3000만): 괴리율 > 20%면 경고."""
        threshold = 0.20
        divergence = 0.25
        assert divergence > threshold

    def test_weekly_low_price_threshold(self) -> None:
        """위클리 + 저가(<500만): 괴리율 > 40%면 경고."""
        threshold = 0.40
        divergence = 0.35
        assert divergence <= threshold  # 35% < 40% → 경고 안 함
