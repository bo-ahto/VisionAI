"""데이터 클렌징 모듈 테스트."""
from __future__ import annotations

import pandas as pd

from visionai.price_engine.preprocessing.data_cleanser import (
    classify_non_art,
    cleanse_dataframe,
)


class TestEventItems:
    """이벤트/상품권 분류."""

    def test_flight_ticket(self) -> None:
        r = classify_non_art("서울-홍콩 왕복 항공권 2매(economy class)", "")
        assert r.is_non_art is True
        assert r.category == "event"

    def test_hotel_voucher(self) -> None:
        r = classify_non_art("쉐라톤 서울 팔래스 강남 호텔 숙박권", "")
        assert r.is_non_art is True
        assert r.category == "event"

    def test_meal_voucher(self) -> None:
        r = classify_non_art("옥수동화덕피자 식사권 + 하우스 와인 (15만원 상당)", "")
        assert r.is_non_art is True
        assert r.category == "event"

    def test_gift_card(self) -> None:
        r = classify_non_art("유나양 상품권", "")
        assert r.is_non_art is True
        assert r.category == "event"

    def test_dinner_with(self) -> None:
        r = classify_non_art("유현준 교수와의 저녁식사", "")
        assert r.is_non_art is True
        assert r.category == "event"


class TestAlcoholItems:
    """주류/테이스팅 분류."""

    def test_whisky_tasting(self) -> None:
        r = classify_non_art("프라이빗 발베니 위스키 테이스팅 클래스", "")
        assert r.is_non_art is True
        assert r.category == "alcohol"

    def test_sommelier(self) -> None:
        r = classify_non_art("최준선 소믈리에의 와인클래스", "")
        assert r.is_non_art is True
        assert r.category == "alcohol"


class TestLuxuryItems:
    """명품 분류."""

    def test_birkin(self) -> None:
        r = classify_non_art("Birkin 35", "소가죽")
        assert r.is_non_art is True
        assert r.category == "luxury"

    def test_rolex(self) -> None:
        r = classify_non_art("Rolex Submariner", "")
        assert r.is_non_art is True
        assert r.category == "luxury"

    def test_celeb_bag(self) -> None:
        r = classify_non_art("한소희 가방", "")
        assert r.is_non_art is True
        assert r.category == "luxury"


class TestJewelryItems:
    """보석/장신구 분류."""

    def test_diamond_ring_by_material(self) -> None:
        r = classify_non_art("멜리 다이아몬드 팔찌", "18K 화이트 골드 천연 다이아몬드")
        assert r.is_non_art is True
        assert r.category == "jewelry"

    def test_diamond_ring_no_material(self) -> None:
        r = classify_non_art("1캐럿 다이아몬드 반지", "")
        assert r.is_non_art is True
        assert r.category == "jewelry"

    def test_ruby_ring(self) -> None:
        r = classify_non_art("루비 할로우 반지", "")
        assert r.is_non_art is True
        assert r.category == "jewelry"


class TestCraftCeramicItems:
    """도자/공예 분류."""

    def test_pottery(self) -> None:
        r = classify_non_art("백자병", "도자기")
        assert r.is_non_art is True
        assert r.category == "craft_ceramic"

    def test_pottery_painted(self) -> None:
        r = classify_non_art("봉황문병", "도자기에 채색")
        assert r.is_non_art is True
        assert r.category == "craft_ceramic"

    def test_nacre(self) -> None:
        r = classify_non_art("십장생문함", "나무에 옻칠, 나전")
        assert r.is_non_art is True
        assert r.category == "craft_ceramic"


class TestCraftWoodItems:
    """목공예 분류."""

    def test_pine(self) -> None:
        r = classify_non_art("반닫이", "소나무")
        assert r.is_non_art is True
        assert r.category == "craft_wood"

    def test_multi_wood(self) -> None:
        r = classify_non_art("문갑", "괴목, 소나무")
        assert r.is_non_art is True
        assert r.category == "craft_wood"


class TestFalsePositivePrevention:
    """미술 작품이 비미술로 오분류되지 않아야 한다."""

    def test_vase_painting(self) -> None:
        """'화병' 제목이지만 재료가 유화 → 미술."""
        r = classify_non_art("화병", "캔버스에 유채")
        assert r.is_non_art is False

    def test_last_supper(self) -> None:
        """'최후의 만찬' → 미술."""
        r = classify_non_art("최후의 만찬", "캔버스에 유채")
        assert r.is_non_art is False

    def test_travel_print(self) -> None:
        """'여행' 제목이지만 석판화 → 미술."""
        r = classify_non_art("여행", "석판화")
        assert r.is_non_art is False

    def test_bronze_sculpture(self) -> None:
        """브론즈 조각 → 미술 (조각/공예는 미술)."""
        r = classify_non_art("Standing Figure", "Bronze")
        assert r.is_non_art is False

    def test_wine_in_painting(self) -> None:
        """'꽃과 술병' + 수묵담채 → 미술."""
        r = classify_non_art("꽃과 술병", "종이에 수묵담채")
        assert r.is_non_art is False

    def test_diamond_in_title_art(self) -> None:
        """'Hysteric Diamond' + 아크릴 → 미술."""
        r = classify_non_art("Hysteric Diamond", "캔버스에 아크릴, 펄 바니쉬")
        assert r.is_non_art is False


class TestEdgeCases:
    """엣지 케이스."""

    def test_nan_material(self) -> None:
        """pandas NaN 재료 → 미술."""
        r = classify_non_art("작품", float("nan"))
        assert r.is_non_art is False

    def test_none_inputs(self) -> None:
        r = classify_non_art(None, None)
        assert r.is_non_art is False

    def test_bag_with_material_is_art(self) -> None:
        """'가방' 제목이지만 재료가 있으면 미술."""
        r = classify_non_art("가방", "캔버스에 유채")
        assert r.is_non_art is False

    def test_wood_mixed_with_bronze_is_art(self) -> None:
        """소나무 + 브론즈 혼합 → 미술 (순수 목재가 아님)."""
        r = classify_non_art("조각", "소나무, 브론즈")
        assert r.is_non_art is False


class TestCleanseDataframe:
    """DataFrame 클렌징 통합."""

    def test_removes_non_art(self) -> None:
        df = pd.DataFrame({
            "제목": ["작품1", "Birkin 35", "항공권 2매", "작품2"],
            "재료": ["캔버스에 유채", "소가죽", "", "종이에 수묵"],
            "낙찰가": [1000000, 13000000, 670000, 500000],
        })
        cleaned, removed = cleanse_dataframe(df)
        assert len(cleaned) == 2
        assert len(removed) == 2

    def test_min_confidence(self) -> None:
        """confidence threshold로 필터링 수준 조절."""
        df = pd.DataFrame({
            "제목": ["반닫이", "작품1"],
            "재료": ["소나무", "캔버스에 유채"],
            "낙찰가": [500000, 1000000],
        })
        # 목공예 confidence=0.85 → threshold=0.9이면 제거 안 됨
        cleaned_strict, _ = cleanse_dataframe(df, min_confidence=0.9)
        assert len(cleaned_strict) == 2

        # threshold=0.8이면 제거됨
        cleaned_loose, _ = cleanse_dataframe(df, min_confidence=0.8)
        assert len(cleaned_loose) == 1
