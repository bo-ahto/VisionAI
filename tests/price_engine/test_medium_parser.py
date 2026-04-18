"""medium_parser 단위 테스트."""
from __future__ import annotations

from visionai.price_engine.preprocessing.medium_parser import MediumResult, parse_medium


class TestParseMedium:
    """매체/지지체 분류 테스트."""

    def test_oil_on_canvas(self) -> None:
        r = parse_medium("캔버스에 유채")
        assert r.medium_category == "유화"
        assert r.support_category == "캔버스"

    def test_ink_on_paper(self) -> None:
        r = parse_medium("종이에 수묵")
        assert r.medium_category == "수묵"
        assert r.support_category == "종이"

    def test_acrylic_on_canvas(self) -> None:
        r = parse_medium("캔버스에 아크릴")
        assert r.medium_category == "아크릴"
        assert r.support_category == "캔버스"

    def test_print(self) -> None:
        r = parse_medium("석판화")
        assert r.medium_category == "판화"

    def test_silkscreen(self) -> None:
        r = parse_medium("실크스크린")
        assert r.medium_category == "실크스크린"

    def test_mixed_media(self) -> None:
        r = parse_medium("혼합재료")
        assert r.medium_category == "혼합재료"

    def test_coloring(self) -> None:
        r = parse_medium("비단에 채색")
        assert r.medium_category == "채색"
        assert r.support_category == "비단"

    def test_bronze(self) -> None:
        r = parse_medium("Bronze, Aluminium, Stainless Steel")
        assert r.medium_category == "조각"

    def test_ceramic(self) -> None:
        r = parse_medium("도자")
        assert r.medium_category == "도자"

    def test_photo(self) -> None:
        r = parse_medium("C-print")
        assert r.medium_category == "사진/디지털"

    def test_wood_support(self) -> None:
        r = parse_medium("나무에 유채")
        assert r.medium_category == "유화"
        assert r.support_category == "목재"

    def test_panel_support(self) -> None:
        r = parse_medium("패널에 아크릴")
        assert r.support_category == "목재"  # 패널은 목재로 통합

    def test_unknown_missing(self) -> None:
        r = parse_medium(None)
        assert r.medium_category == "unknown"
        assert r.support_category == "unknown"

    def test_unknown_empty(self) -> None:
        r = parse_medium("")
        assert r.medium_category == "unknown"

    def test_other(self) -> None:
        r = parse_medium("특수재료XYZ")
        assert r.medium_category == "기타"
        assert r.support_category == "기타"

    def test_oil_english(self) -> None:
        r = parse_medium("Oil on canvas")
        assert r.medium_category == "유화"
        assert r.support_category == "캔버스"

    def test_ink_with_muk(self) -> None:
        r = parse_medium("종이에 먹")
        assert r.medium_category == "수묵"
