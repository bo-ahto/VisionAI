"""Artsy Price Database 확장 스크래핑 — 71명 작가.

MCP Playwright 사용 (Cloudflare 우회).
기존 artsy_auctions.csv에 추가 수집.

Usage:
    # MCP Playwright로 Artsy 로그인 후 실행
    # 이 스크립트는 slug 목록 + URL을 생성하여 MCP로 전달용
    PYTHONPATH=src python3 scripts/collectors/scrape_artsy_expanded.py
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent.parent
MAPPING_PATH = ROOT / "data" / "artist_slug_mapping_expanded.csv"
EXISTING_PATH = ROOT / "data" / "artsy_auctions.csv"


def generate_scrape_urls() -> list[dict]:
    """스크래핑 대상 URL 목록 생성."""
    mapping = pd.read_csv(MAPPING_PATH)

    # 기존 수집 작가 확인
    existing_slugs: set[str] = set()
    if EXISTING_PATH.exists():
        existing = pd.read_csv(EXISTING_PATH)
        if "artist_slug" in existing.columns:
            existing_slugs = set(existing["artist_slug"].values)

    urls = []
    for _, row in mapping.iterrows():
        slug = row["en_slug"]
        if slug in existing_slugs:
            continue
        url = f"https://www.artsy.net/artist/{slug}/auction-results"
        urls.append({
            "ko_name": row["ko_name"],
            "en_slug": slug,
            "en_name": row.get("en_name", ""),
            "url": url,
        })

    return urls


def main() -> None:
    """스크래핑 대상 URL 생성 + 요약."""
    urls = generate_scrape_urls()
    logger.info("=== Artsy 스크래핑 대상 ===")
    logger.info("총 %d명 (기존 수집 제외)", len(urls))

    for i, item in enumerate(urls[:10]):
        logger.info("  %d. %s (%s) → %s", i + 1, item["ko_name"], item["en_name"], item["url"])
    if len(urls) > 10:
        logger.info("  ... 외 %d명", len(urls) - 10)

    # URL 목록 저장
    output = ROOT / "data" / "artsy_scrape_targets.csv"
    pd.DataFrame(urls).to_csv(output, index=False)
    logger.info("Saved to %s", output)
    logger.info(
        "\n다음 단계: MCP Playwright로 각 URL 접속하여 경매 결과 스크래핑\n"
        "또는 기존 scrape_artsy_auctions.py에 slug 목록 전달"
    )


if __name__ == "__main__":
    main()
