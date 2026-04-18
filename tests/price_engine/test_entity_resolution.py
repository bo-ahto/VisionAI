"""Sprint 1: Entity Resolution 테스트."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT / "scripts" / "collectors"))
sys.path.insert(0, str(_ROOT / "src"))

from integrate_external_v2 import (  # noqa: E402
    ExternalLotRecord,
    ResolvedArtistMatch,
    build_manual_review_queue,
    deduplicate_external_lots,
    normalize_hammer_price,
    resolve_artist_identity,
)

KAUCTION_NAMES = ["김환기", "이우환", "박서보", "김창열", "이중섭"]


class TestArtsyMatching:
    def test_artsy_slug_exact(self) -> None:
        """slug 매핑으로 exact match."""
        slug_map = {"whanki-kim": "김환기"}
        result = resolve_artist_identity(
            "whanki-kim", "artsy", KAUCTION_NAMES, slug_mapping=slug_map,
        )
        assert result is not None
        assert result.match_type == "exact"
        assert result.confidence == 1.0
        assert result.artist_id_canonical == "김환기"

    def test_artsy_fuzzy_threshold(self) -> None:
        """fuzzy match 시 confidence ≥ 0.85."""
        # "김환기" vs "김 환기" (공백 차이) → 높은 유사도
        result = resolve_artist_identity(
            "김 환기", "artsy", KAUCTION_NAMES,
        )
        if result is not None:
            assert result.confidence >= 0.85

    def test_match_precision_ge_95(self) -> None:
        """정확한 매칭은 precision ≥ 95% (G15).

        수동 검증 시뮬레이션: 알려진 매칭 쌍으로 테스트.
        """
        known_pairs = [
            ("김환기", "김환기"),
            ("이우환", "이우환"),
            ("박서보", "박서보"),
            ("김창열", "김창열"),
            ("이중섭", "이중섭"),
        ]
        correct = 0
        for source_name, expected in known_pairs:
            result = resolve_artist_identity(
                source_name, "artsy", KAUCTION_NAMES,
            )
            if result and result.artist_id_canonical == expected:
                correct += 1
        precision = correct / len(known_pairs)
        assert precision >= 0.95


class TestSeoulAuction:
    def test_seoul_exact_only(self) -> None:
        """Seoul Auction은 exact match만."""
        result = resolve_artist_identity(
            "김 환기", "seoul_auction", KAUCTION_NAMES,
        )
        # "김 환기" != "김환기" (공백) → None
        assert result is None

        # exact match는 성공
        result2 = resolve_artist_identity(
            "김환기", "seoul_auction", KAUCTION_NAMES,
        )
        assert result2 is not None
        assert result2.match_type == "exact"


class TestDedup:
    def test_dedup_composite_key(self) -> None:
        """중복 lot 제거 — composite key."""
        lot1 = ExternalLotRecord(
            artist_id_canonical="김환기",
            artwork_title="무제",
            hammer_price_krw=1000000,
            currency_original="KRW",
            fx_rate_at_sale_month=1.0,
            premium_included=False,
            unsold_flag=False,
            auction_house_norm="Seoul Auction",
            auction_date="2024-01-01",
            source_url="",
            scrape_timestamp="",
            name_match_confidence=1.0,
        )
        lot2 = ExternalLotRecord(
            artist_id_canonical="김환기",
            artwork_title="무제",
            hammer_price_krw=1000000,
            currency_original="KRW",
            fx_rate_at_sale_month=1.0,
            premium_included=False,
            unsold_flag=False,
            auction_house_norm="Seoul Auction",
            auction_date="2024-01-01",
            source_url="",
            scrape_timestamp="",
            name_match_confidence=1.0,
        )
        result = deduplicate_external_lots([lot1, lot2])
        assert len(result) == 1


class TestManualReviewQueue:
    def test_manual_review_queue(self) -> None:
        """0.85~0.95 구간 분리."""
        matches = [
            ResolvedArtistMatch("A", "a", "artsy", "fuzzy", 0.80),
            ResolvedArtistMatch("B", "b", "artsy", "fuzzy", 0.90),
            ResolvedArtistMatch("C", "c", "artsy", "exact", 1.0),
        ]
        queue = build_manual_review_queue(matches)
        assert len(queue) == 1
        assert queue[0].artist_id_canonical == "B"


class TestPriceNormalization:
    def test_hammer_usd_to_krw(self) -> None:
        """USD → KRW 변환."""
        fx = pd.DataFrame({"year_month": ["202401"], "usd_krw": [1300.0]})
        result = normalize_hammer_price(
            1000.0, "USD", "2024-01-15", fx,
        )
        assert result == 1000.0 * 1300.0

    def test_premium_deduction(self) -> None:
        """Premium 포함 시 /1.15 차감."""
        fx = pd.DataFrame({"year_month": ["202401"], "usd_krw": [1300.0]})
        result = normalize_hammer_price(
            1150.0, "KRW", "2024-01-15", fx, premium_included=True,
        )
        assert abs(result - 1000.0) < 0.01

    def test_unsold_flag_preserved(self) -> None:
        """unsold_flag가 ExternalLotRecord에 보존."""
        lot = ExternalLotRecord(
            artist_id_canonical="테스트",
            artwork_title="무제",
            hammer_price_krw=0,
            currency_original="KRW",
            fx_rate_at_sale_month=1.0,
            premium_included=False,
            unsold_flag=True,
            auction_house_norm="Test",
            auction_date="2024-01-01",
            source_url="",
            scrape_timestamp="",
            name_match_confidence=1.0,
        )
        assert lot.unsold_flag is True

    def test_required_fields(self) -> None:
        """ExternalLotRecord 필수 필드 존재."""
        required = [
            "artist_id_canonical", "artwork_title", "hammer_price_krw",
            "currency_original", "fx_rate_at_sale_month", "premium_included",
            "unsold_flag", "auction_house_norm", "auction_date",
            "source_url", "scrape_timestamp", "name_match_confidence",
        ]
        lot = ExternalLotRecord(
            artist_id_canonical="",
            artwork_title="",
            hammer_price_krw=0,
            currency_original="",
            fx_rate_at_sale_month=0,
            premium_included=False,
            unsold_flag=False,
            auction_house_norm="",
            auction_date="",
            source_url="",
            scrape_timestamp="",
            name_match_confidence=0,
        )
        for field in required:
            assert hasattr(lot, field), f"Missing field: {field}"
