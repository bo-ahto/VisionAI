"""year_parser 단위 테스트."""
from __future__ import annotations

from visionai.price_engine.preprocessing.year_parser import parse_year


class TestParseYear:
    """제작연도 파싱 테스트."""

    def test_simple_year(self) -> None:
        r = parse_year("1937")
        assert r.year_created == 1937
        assert r.is_year_missing is False

    def test_circa_year(self) -> None:
        r = parse_year("ca.1970")
        assert r.year_created == 1970

    def test_year_with_suffix(self) -> None:
        r = parse_year("2023년")
        assert r.year_created == 2023

    def test_year_in_title(self) -> None:
        r = parse_year("22-X-73 #325")
        # 73 is not a 4-digit year
        assert r.is_year_missing is True

    def test_none(self) -> None:
        r = parse_year(None)
        assert r.year_created is None
        assert r.is_year_missing is True

    def test_empty_string(self) -> None:
        r = parse_year("")
        assert r.is_year_missing is True

    def test_nan_float(self) -> None:
        r = parse_year(float("nan"))
        assert r.is_year_missing is True

    def test_ancient_year(self) -> None:
        r = parse_year("1649")
        assert r.year_created == 1649

    def test_too_far_future(self) -> None:
        r = parse_year("2099")
        assert r.is_year_missing is True

    def test_range_year(self) -> None:
        # "1960-70" — 첫 번째 4자리만 추출
        r = parse_year("1960-70")
        assert r.year_created == 1960
