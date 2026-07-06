"""K-ARTMARKET (한국미술시장정보시스템) 경매 데이터 수집.

URL: https://k-artmarket.kr/
운영: 문화체육관광부 + 예술경영지원센터 (KAMS)

수집 항목:
- 작가명, 작품명, 낙찰가, 경매사, 경매일
- 작품 크기, 재료, 제작연도

Usage:
    python Crawler/Kartmarket/collect_kartmarket.py --output data/kartmarket_auctions.csv
    python Crawler/Kartmarket/collect_kartmarket.py \
        --artists data/k-auction-artists.txt --output data/kartmarket_auctions.csv
"""
from __future__ import annotations

import argparse
import csv
import logging
import time
import urllib.parse
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

BASE_URL = "https://k-artmarket.kr"
SEARCH_URL = f"{BASE_URL}/mypage/auctionSearch.do"

# 요청 간 대기 (서버 부하 방지)
REQUEST_DELAY = 2.0


def _fetch_page(artist_name: str, page: int = 1) -> str | None:
    """K-ARTMARKET 경매 검색 페이지 요청."""
    params = urllib.parse.urlencode({
        "searchKeyword": artist_name,
        "pageIndex": page,
    })
    url = f"{SEARCH_URL}?{params}"

    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "ko-KR,ko;q=0.9",
        })
        resp = urllib.request.urlopen(req, timeout=15)
        return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        logger.warning("Failed to fetch page for '%s' (page %d): %s", artist_name, page, e)
        return None


def _parse_auction_results(html: str) -> list[dict]:
    """HTML에서 경매 결과 파싱 (간이 파서).

    K-ARTMARKET의 정확한 HTML 구조에 따라 조정 필요.
    현재는 구조 탐색용 기본 구현.
    """
    results = []
    # K-ARTMARKET은 동적 렌더링일 수 있어 실제 구조 확인 필요
    # 여기서는 테이블 기반 파싱 시도
    import re

    # 경매 결과 테이블 행 탐색
    rows = re.findall(r'<tr[^>]*class="[^"]*auction[^"]*"[^>]*>(.*?)</tr>', html, re.DOTALL)
    if not rows:
        # 대안: 일반 테이블 행 탐색
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)

    for row in rows:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
        if len(cells) >= 5:
            result = {
                "작가": re.sub(r'<[^>]+>', '', cells[0]).strip(),
                "작품명": re.sub(r'<[^>]+>', '', cells[1]).strip(),
                "크기": re.sub(r'<[^>]+>', '', cells[2]).strip() if len(cells) > 2 else "",
                "재료": re.sub(r'<[^>]+>', '', cells[3]).strip() if len(cells) > 3 else "",
                "낙찰가": re.sub(r'<[^>]+>', '', cells[4]).strip() if len(cells) > 4 else "",
                "경매사": re.sub(r'<[^>]+>', '', cells[5]).strip() if len(cells) > 5 else "",
                "경매일": re.sub(r'<[^>]+>', '', cells[6]).strip() if len(cells) > 6 else "",
                "source": "K-ARTMARKET",
            }
            if result["작가"] and result["작가"] != "작가":
                results.append(result)

    return results


def collect_artist_auctions(artist_name: str, max_pages: int = 10) -> list[dict]:
    """단일 작가의 경매 결과 수집."""
    all_results = []
    for page in range(1, max_pages + 1):
        html = _fetch_page(artist_name, page)
        if html is None:
            break
        results = _parse_auction_results(html)
        if not results:
            break
        all_results.extend(results)
        logger.info("  %s page %d: %d results", artist_name, page, len(results))
        time.sleep(REQUEST_DELAY)
    return all_results


def collect_all(
    artist_names: list[str],
    output_path: str | Path,
    max_pages_per_artist: int = 5,
) -> int:
    """전체 작가 리스트에 대해 경매 결과 수집.

    Returns:
        총 수집 건수.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    all_results: list[dict] = []
    for i, artist in enumerate(artist_names):
        logger.info("[%d/%d] Collecting: %s", i + 1, len(artist_names), artist)
        results = collect_artist_auctions(artist, max_pages=max_pages_per_artist)
        all_results.extend(results)
        logger.info("  → %d results (total: %d)", len(results), len(all_results))

    if all_results:
        fieldnames = list(all_results[0].keys())
        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_results)
        logger.info("Saved %d results to %s", len(all_results), output_path)

    return len(all_results)


def main() -> None:
    """CLI 진입점."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    parser = argparse.ArgumentParser(description="K-ARTMARKET 경매 데이터 수집")
    parser.add_argument("--artists", type=str, help="작가명 리스트 파일 (줄당 1명)")
    parser.add_argument("--output", type=str, default="data/kartmarket_auctions.csv")
    parser.add_argument("--max-pages", type=int, default=5)
    parser.add_argument("--sample", type=int, default=0, help="샘플 작가 수 (0=전체)")
    args = parser.parse_args()

    # 작가 리스트 로드
    if args.artists:
        with open(args.artists, encoding="utf-8") as f:
            artists = [line.strip() for line in f if line.strip()]
    else:
        # K-Auction 데이터에서 작가 추출
        import pandas as pd
        works_path = Path("data/k-auction-works-20260325.csv")
        if works_path.exists():
            df = pd.read_csv(works_path, encoding="utf-8-sig")
            artists = sorted(df["작가"].dropna().unique().tolist())
            logger.info("Loaded %d artists from K-Auction data", len(artists))
        else:
            logger.error("No artist list or K-Auction data found.")
            return

    if args.sample > 0:
        artists = artists[:args.sample]

    total = collect_all(artists, args.output, max_pages_per_artist=args.max_pages)
    logger.info("Collection complete: %d total results", total)


if __name__ == "__main__":
    main()
