"""Phase 5 Sprint 1 — Entity Resolution + 외부 데이터 정합화.

K-Auction 작가명과 외부 소스(Artsy, Seoul Auction, NamuWiki) 간
작가명 매칭, 가격 정규화, 중복 제거.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

import pandas as pd
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResolvedArtistMatch:
    """작가명 매칭 결과."""

    artist_id_canonical: str
    source_name: str
    source: str  # "artsy" | "seoul_auction" | "namuwiki"
    match_type: str  # "exact" | "fuzzy"
    confidence: float  # 0.0~1.0


@dataclass
class ExternalLotRecord:
    """외부 경매 lot 정규화 결과."""

    artist_id_canonical: str
    artwork_title: str
    hammer_price_krw: float
    currency_original: str
    fx_rate_at_sale_month: float
    premium_included: bool
    unsold_flag: bool
    auction_house_norm: str
    auction_date: str
    source_url: str
    scrape_timestamp: str
    name_match_confidence: float


def normalize_artist_name(name: str) -> str:
    """작가명 정규화 — 공백, 특수문자 통일."""
    if not name:
        return ""
    # 양쪽 공백 제거, 연속 공백 단일화
    result = " ".join(name.strip().split())
    return result


def resolve_artist_identity(
    source_name: str,
    source: str,
    kauction_names: list[str],
    slug_mapping: dict[str, str] | None = None,
    threshold: float = 0.85,
) -> ResolvedArtistMatch | None:
    """소스별 작가명 매칭.

    - Artsy: slug exact → fuzzy (rapidfuzz)
    - Seoul Auction: 한글 exact only
    - NamuWiki: exact → fuzzy 보완

    Args:
        source_name: 외부 소스 작가명.
        source: 소스 식별자.
        kauction_names: K-Auction 작가명 리스트.
        slug_mapping: {slug: kauction_name} 매핑 (Artsy용).
        threshold: fuzzy match 최소 점수.

    Returns:
        매칭 결과 또는 None.
    """
    norm_source = normalize_artist_name(source_name)

    # Artsy: slug 매핑 우선
    if source == "artsy" and slug_mapping:
        for slug, canonical in slug_mapping.items():
            if slug == norm_source or canonical == norm_source:
                return ResolvedArtistMatch(
                    artist_id_canonical=canonical,
                    source_name=source_name,
                    source=source,
                    match_type="exact",
                    confidence=1.0,
                )

    # Exact match
    for kname in kauction_names:
        if normalize_artist_name(kname) == norm_source:
            return ResolvedArtistMatch(
                artist_id_canonical=kname,
                source_name=source_name,
                source=source,
                match_type="exact",
                confidence=1.0,
            )

    # Seoul Auction: exact only
    if source == "seoul_auction":
        return None

    # Fuzzy match (Artsy, NamuWiki)
    best_score = 0.0
    best_match = ""
    for kname in kauction_names:
        score = fuzz.ratio(norm_source, normalize_artist_name(kname)) / 100.0
        if score > best_score:
            best_score = score
            best_match = kname

    if best_score >= threshold:
        return ResolvedArtistMatch(
            artist_id_canonical=best_match,
            source_name=source_name,
            source=source,
            match_type="fuzzy",
            confidence=round(best_score, 4),
        )

    return None


def deduplicate_external_lots(
    lots: list[ExternalLotRecord],
) -> list[ExternalLotRecord]:
    """중복 제거.

    Composite key: (artist_id_canonical, artwork_title, auction_date, auction_house_norm).
    """
    seen: set[tuple[str, str, str, str]] = set()
    result: list[ExternalLotRecord] = []
    for lot in lots:
        key = (
            lot.artist_id_canonical,
            lot.artwork_title,
            lot.auction_date,
            lot.auction_house_norm,
        )
        if key not in seen:
            seen.add(key)
            result.append(lot)
    return result


def build_manual_review_queue(
    matches: list[ResolvedArtistMatch],
    threshold_low: float = 0.85,
    threshold_high: float = 0.95,
) -> list[ResolvedArtistMatch]:
    """Confidence 0.85~0.95 구간의 매칭을 수동 검토 큐로 분리."""
    return [
        m for m in matches
        if threshold_low <= m.confidence < threshold_high
    ]


def normalize_hammer_price(
    price: float,
    currency: str,
    auction_date: str,
    fx_df: pd.DataFrame,
    premium_included: bool = False,
) -> float:
    """경매 가격을 KRW hammer price로 통일.

    Args:
        price: 원본 가격.
        currency: 통화 코드 ("USD", "KRW", "EUR" 등).
        auction_date: 경매 날짜 (YYYY-MM-DD).
        fx_df: 환율 DataFrame (year_month, usd_krw 컬럼).
        premium_included: True이면 buyer's premium 15% 차감.

    Returns:
        KRW hammer price.
    """
    if premium_included and price > 0:
        price = price / 1.15

    if currency.upper() == "KRW":
        return price

    # 경매 월 환율 조회
    try:
        ym = datetime.strptime(auction_date[:7], "%Y-%m").strftime("%Y%m")
    except (ValueError, TypeError):
        ym = ""

    fx_rate = 1300.0  # 기본 환율 (조회 실패 시)
    if ym and "year_month" in fx_df.columns and "usd_krw" in fx_df.columns:
        match = fx_df[fx_df["year_month"] == ym]
        if len(match) > 0 and pd.notna(match.iloc[0]["usd_krw"]):
            fx_rate = float(match.iloc[0]["usd_krw"])

    if currency.upper() == "USD":
        return price * fx_rate
    if currency.upper() == "EUR":
        return price * fx_rate * 1.08  # EUR/USD 근사
    if currency.upper() == "GBP":
        return price * fx_rate * 1.27  # GBP/USD 근사

    return price * fx_rate  # 기타: USD 기준 근사
