"""파서 로버스트니스 테스트 — 오타, 혼합언어, 특수 패턴.

기획서 참조: 9장 #6 Parser Robustness Test
"""
from __future__ import annotations

from visionai.price_engine.preprocessing.dimension_parser import parse_dimension
from visionai.price_engine.preprocessing.medium_parser import parse_medium
from visionai.price_engine.preprocessing.year_parser import parse_year


class TestDimensionRobustness:
    """크기 파서 엣지 케이스."""

    def test_multiple_pieces(self) -> None:
        # "22.5×22cm, 3점" — 첫 번째 크기만
        r = parse_dimension("22.5×22cm, 3점")
        assert r.height_cm == 22.5
        assert r.width_cm == 22.0

    def test_parentheses(self) -> None:
        r = parse_dimension("(45.5×53.0)cm")
        assert r.height_cm == 53.0

    def test_mixed_separator(self) -> None:
        r = parse_dimension("100X80cm")
        assert r.height_cm == 100.0

    def test_trailing_text(self) -> None:
        r = parse_dimension("72.7×60.6cm (20호)")
        assert r.height_cm == 72.7

    def test_very_small(self) -> None:
        r = parse_dimension("3.5×2.5cm")
        assert r.height_cm == 3.5

    def test_very_large(self) -> None:
        r = parse_dimension("300×200cm")
        assert r.height_cm == 300.0

    def test_decimal_only(self) -> None:
        r = parse_dimension("0.5×0.3")
        assert r.height_cm == 0.5

    def test_korean_height(self) -> None:
        r = parse_dimension("高 25.5")
        assert r.height_cm == 25.5

    def test_whitespace_only(self) -> None:
        r = parse_dimension("   ")
        assert r.is_size_imputed is True

    def test_special_characters(self) -> None:
        r = parse_dimension("???")
        assert r.pattern_used == "failed"

    def test_diameter_korean(self) -> None:
        r = parse_dimension("지름 30cm")
        assert r.height_cm == 30.0


class TestMediumRobustness:
    """재료 파서 엣지 케이스."""

    def test_mixed_language(self) -> None:
        r = parse_medium("Oil on Canvas")
        assert r.medium_category == "유화"
        assert r.support_category == "캔버스"

    def test_long_description(self) -> None:
        r = parse_medium("Bronze, Aluminium, Stainless Steel, Urethan paint")
        assert r.medium_category == "조각/공예"

    def test_multiple_media(self) -> None:
        # "수묵채색" — 수묵이 먼저 매칭
        r = parse_medium("수묵채색")
        assert r.medium_category == "수묵"

    def test_ink_wash(self) -> None:
        r = parse_medium("종이에 먹, 채색")
        assert r.medium_category == "수묵"
        assert r.support_category == "종이"

    def test_etching(self) -> None:
        r = parse_medium("에칭")
        assert r.medium_category == "판화"

    def test_pigment_print(self) -> None:
        r = parse_medium("피그먼트 프린트")
        assert r.medium_category == "사진/디지털"

    def test_number_only(self) -> None:
        r = parse_medium("12345")
        assert r.medium_category == "기타"

    def test_silk_on_silk(self) -> None:
        r = parse_medium("비단에 수묵채색")
        assert r.medium_category == "수묵"
        assert r.support_category == "비단"


class TestYearRobustness:
    """제작연도 파서 엣지 케이스."""

    def test_year_with_dash(self) -> None:
        r = parse_year("1960-1970")
        assert r.year_created == 1960

    def test_year_with_s(self) -> None:
        r = parse_year("1980s")
        assert r.year_created == 1980

    def test_number_not_year(self) -> None:
        r = parse_year("325")
        assert r.is_year_missing is True

    def test_float_year(self) -> None:
        r = parse_year(2023.0)
        assert r.year_created == 2023

    def test_mixed_text(self) -> None:
        r = parse_year("circa 1850, unsigned")
        assert r.year_created == 1850
