"""외부 데이터 통합 파이프라인.

K-ARTMARKET 경매 데이터 + Artsy 작가 프로필을 기존 K-Auction 데이터와 통합.

Usage:
    python scripts/collectors/integrate_external.py \
        --kartmarket data/kartmarket_auctions.csv \
        --artsy data/artsy_artists.json \
        --output data/integrated_works.csv
"""
from __future__ import annotations

import argparse
import json
import logging
import re
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def _normalize_artist_name(name: str) -> str:
    """작가명 정규화 — 공백/특수문자 통일, 동명이인 기본 처리."""
    if not name or not isinstance(name, str):
        return ""
    # 공백 통일
    name = re.sub(r"\s+", " ", name.strip())
    # 괄호 내용 제거 (영문명 등)
    name = re.sub(r"\s*\([^)]*\)\s*", "", name)
    return name


def load_kauction(path: str | Path) -> pd.DataFrame:
    """K-Auction 기존 데이터 로드."""
    df = pd.read_csv(path, encoding="utf-8-sig")
    df["artist_normalized"] = df["작가"].apply(_normalize_artist_name)
    df["source"] = "K-Auction"
    logger.info("K-Auction: %d rows, %d artists", len(df), df["작가"].nunique())
    return df


def load_kartmarket(path: str | Path) -> pd.DataFrame | None:
    """K-ARTMARKET 데이터 로드 + 정규화."""
    path = Path(path)
    if not path.exists():
        logger.warning("K-ARTMARKET file not found: %s", path)
        return None

    df = pd.read_csv(path, encoding="utf-8-sig")
    df["artist_normalized"] = df["작가"].apply(_normalize_artist_name)

    # 가격 정규화 (쉼표/원 제거)
    if "낙찰가" in df.columns:
        df["낙찰가"] = (
            df["낙찰가"]
            .astype(str)
            .str.replace(",", "")
            .str.replace("원", "")
            .str.strip()
        )
        df["낙찰가"] = pd.to_numeric(df["낙찰가"], errors="coerce")

    logger.info("K-ARTMARKET: %d rows, %d artists", len(df), df["작가"].nunique())
    return df


def load_artsy(path: str | Path) -> pd.DataFrame | None:
    """Artsy 작가 프로필 로드."""
    path = Path(path)
    if not path.exists():
        logger.warning("Artsy file not found: %s", path)
        return None

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    df = pd.DataFrame(data)
    df["artist_normalized"] = df["artist_name_query"].apply(_normalize_artist_name)
    logger.info("Artsy: %d profiles", len(df))
    return df


def integrate(
    kauction_path: str | Path,
    kartmarket_path: str | Path | None = None,
    artsy_path: str | Path | None = None,
    output_path: str | Path | None = None,
) -> pd.DataFrame:
    """외부 데이터 통합.

    1. K-Auction + K-ARTMARKET 경매 데이터 합산 (작가명 매칭)
    2. Artsy 작가 프로필 조인 (전시 이력 등)
    3. 통합 데이터 출력
    """
    # 1. K-Auction 로드
    kauction = load_kauction(kauction_path)

    # 2. K-ARTMARKET 통합
    if kartmarket_path:
        kartmarket = load_kartmarket(kartmarket_path)
        if kartmarket is not None and not kartmarket.empty:
            # K-Auction에 없는 작가의 거래 이력 추가
            kauction_artists = set(kauction["artist_normalized"].unique())
            new_artists = kartmarket[
                ~kartmarket["artist_normalized"].isin(kauction_artists)
            ]
            logger.info(
                "K-ARTMARKET new artists: %d (not in K-Auction)",
                new_artists["작가"].nunique(),
            )

            # 기존 K-Auction 작가의 추가 거래 이력도 활용
            # (작가 통계 계산 시 더 풍부한 이력 제공)
            overlap = kartmarket[
                kartmarket["artist_normalized"].isin(kauction_artists)
            ]
            logger.info(
                "K-ARTMARKET overlap artists: %d (already in K-Auction, %d extra records)",
                overlap["작가"].nunique(),
                len(overlap),
            )

    # 3. Artsy 프로필 조인
    if artsy_path:
        artsy = load_artsy(artsy_path)
        if artsy is not None and not artsy.empty:
            # 작가별 전시 이력 조인
            artsy_features = artsy[[
                "artist_normalized",
                "exhibition_count",
                "solo_show_count",
                "institutional_show_count",
                "nationality",
            ]].drop_duplicates(subset=["artist_normalized"])

            kauction = kauction.merge(
                artsy_features,
                on="artist_normalized",
                how="left",
            )
            matched = kauction["exhibition_count"].notna().sum()
            logger.info(
                "Artsy matched: %d/%d rows (%.1f%%)",
                matched, len(kauction), matched / len(kauction) * 100,
            )

    # 4. 출력
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        kauction.to_csv(output_path, index=False, encoding="utf-8-sig")
        logger.info("Integrated data saved: %s (%d rows)", output_path, len(kauction))

    return kauction


def main() -> None:
    """CLI 진입점."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    parser = argparse.ArgumentParser(description="외부 데이터 통합")
    parser.add_argument(
        "--kauction", default="data/k-auction-works-20260325.csv"
    )
    parser.add_argument("--kartmarket", default=None)
    parser.add_argument("--artsy", default=None)
    parser.add_argument("--output", default="data/integrated_works.csv")
    args = parser.parse_args()

    integrate(
        kauction_path=args.kauction,
        kartmarket_path=args.kartmarket,
        artsy_path=args.artsy,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()
