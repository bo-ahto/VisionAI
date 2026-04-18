"""dimension_parser 단위 테스트."""
from __future__ import annotations

import pytest

from visionai.price_engine.preprocessing.dimension_parser import (
    DimensionResult,
    impute_surface_area,
    parse_dimension,
)


class TestParseDimension:
    """5개 패턴별 파싱 테스트."""

    def test_2d_standard(self) -> None:
        # 2026-04-17 코덱스 P2: 원본 순서 보존 (v1=width, v2=height) — K-Auction 관행 "가로×세로"
        r = parse_dimension("81×116cm")
        assert r.width_cm == 81.0
        assert r.height_cm == 116.0
        assert r.surface_area == pytest.approx(116.0 * 81.0)
        assert r.is_3d is False
        assert r.pattern_used == "2d"

    def test_2d_lowercase_x(self) -> None:
        r = parse_dimension("53.0x45.5cm")
        assert r.width_cm == 53.0
        assert r.height_cm == 45.5
        assert r.pattern_used == "2d"

    def test_2d_with_spaces(self) -> None:
        r = parse_dimension("72.7 × 60.6 cm")
        assert r.width_cm == 72.7
        assert r.height_cm == 60.6

    def test_3d_with_h_marker(self) -> None:
        r = parse_dimension("31×13×22(h)cm")
        assert r.height_cm == 22.0
        assert r.width_cm == 31.0
        assert r.is_3d is True
        assert r.pattern_used == "3d_h"

    def test_3d_standard(self) -> None:
        r = parse_dimension("30×20×15cm")
        assert r.height_cm == 30.0
        assert r.width_cm == 20.0
        assert r.is_3d is True
        assert r.pattern_used == "3d"

    def test_height_only_korean(self) -> None:
        r = parse_dimension("高48")
        assert r.height_cm == 48.0
        assert r.width_cm is None
        assert r.is_3d is True
        assert r.pattern_used == "height_only"

    def test_height_only_english(self) -> None:
        r = parse_dimension("H35.5cm")
        assert r.height_cm == 35.5

    def test_diameter(self) -> None:
        r = parse_dimension("diameter 6.5cm")
        assert r.height_cm == 6.5
        assert r.width_cm == 6.5
        assert r.surface_area == pytest.approx(6.5 * 6.5)
        assert r.pattern_used == "diameter"

    def test_diameter_symbol(self) -> None:
        r = parse_dimension("Ø39cm")
        assert r.height_cm == 39.0
        assert r.width_cm == 39.0

    def test_missing_none(self) -> None:
        r = parse_dimension(None)
        assert r.height_cm is None
        assert r.is_size_imputed is True
        assert r.pattern_used == "missing"

    def test_missing_empty(self) -> None:
        r = parse_dimension("")
        assert r.is_size_imputed is True

    def test_unparseable(self) -> None:
        r = parse_dimension("기타 크기")
        assert r.height_cm is None
        assert r.pattern_used == "failed"

    def test_aspect_ratio(self) -> None:
        r = parse_dimension("100×50cm")
        assert r.aspect_ratio == pytest.approx(2.0, rel=0.01)


class TestImputeSurfaceArea:
    """결측 면적 대체 테스트."""

    def test_no_imputation_needed(self) -> None:
        area, imputed = impute_surface_area(5000.0, "A", "유화")
        assert area == 5000.0
        assert imputed is False

    def test_artist_medium_median(self) -> None:
        medians = {("김환기", "유화"): 8000.0}
        area, imputed = impute_surface_area(
            None, "김환기", "유화", artist_medium_medians=medians
        )
        assert area == 8000.0
        assert imputed is True

    def test_medium_median_fallback(self) -> None:
        area, imputed = impute_surface_area(
            None, "신규작가", "유화", medium_medians={"유화": 6000.0}
        )
        assert area == 6000.0

    def test_global_median_fallback(self) -> None:
        area, imputed = impute_surface_area(None, None, None)
        assert area == 2800.0
        assert imputed is True
