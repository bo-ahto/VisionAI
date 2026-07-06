"""Artsy Price Database 경매 결과 스크래핑.

Playwright로 로그인 세션 유지 + 작가별 경매 결과 자동 수집.

Usage:
    # 1. 먼저 브라우저에서 Artsy 로그인
    # 2. 실행
    python scripts/collectors/scrape_artsy_auctions.py --sample 5
    python scripts/collectors/scrape_artsy_auctions.py --output data/artsy_auctions.csv
"""
from __future__ import annotations

import argparse
import csv
import logging
import re
import time
from pathlib import Path

logger = logging.getLogger(__name__)

REQUEST_DELAY = 2.0


def _extract_auction_results(page) -> list[dict]:
    """현재 페이지에서 경매 결과 추출."""
    results = page.evaluate("""() => {
        const links = document.querySelectorAll('a[href*="auction-result/"]');
        const results = [];
        for (const link of links) {
            const href = link.getAttribute('href');
            if (!href || href === '/artist/') continue;
            // auction-result ID만 (auction-results 페이지 링크 제외)
            if (!href.match(/\\/auction-result\\/\\d+/)) continue;

            const text = link.innerText;
            const lines = text.split('\\n').map(l => l.trim()).filter(l => l);

            // 파싱: 작품명, 재료, 크기, 날짜, 경매사, 카테고리, Lot, 가격/추정가
            const result = {
                url: href,
                raw_text: lines.join(' | '),
                title: lines[0] || '',
                medium: lines[1] || '',
                dimensions: lines[2] || '',
                date: lines[3] || '',
                auction_house: lines[4] || '',
                sale_name: lines[5] || '',
                lot: lines[6] || '',
            };

            // 가격/추정가 패턴 찾기
            for (const line of lines) {
                if (line.match(/sold|bought in/i)) {
                    result.sold_status = line;
                }
                if (line.match(/[\\$€£¥]|HK\\$|JPY|KRW|GBP|USD|EUR/i)) {
                    if (line.includes('est')) {
                        result.estimate = line;
                    } else if (!result.price) {
                        result.price = line;
                    }
                }
                if (line.match(/Awaiting results/i)) {
                    result.sold_status = 'Awaiting results';
                }
            }

            results.push(result);
        }
        return results;
    }""")
    return results


def _get_artist_slug(artist_name: str) -> str:
    """작가명 → Artsy slug 변환."""
    slug = artist_name.lower().strip()
    slug = re.sub(r"[^a-z0-9가-힣\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    return slug


def scrape_artist_auctions(
    page,
    artist_name: str,
    artist_slug: str | None = None,
    max_pages: int = 10,
) -> list[dict]:
    """단일 작가의 경매 결과 스크래핑."""
    if not artist_slug:
        artist_slug = _get_artist_slug(artist_name)

    all_results: list[dict] = []
    url = f"https://www.artsy.net/artist/{artist_slug}/auction-results"

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)  # JS 렌더링 대기

        # Auction Results 섹션으로 스크롤
        page.evaluate("""() => {
            const h2s = document.querySelectorAll('h2');
            for (const h of h2s) {
                if (h.textContent.includes('Auction Results')) {
                    h.scrollIntoView({behavior: 'instant', block: 'start'});
                    return true;
                }
            }
            return false;
        }""")
        time.sleep(1)

        results = _extract_auction_results(page)
        for r in results:
            r["artist_name"] = artist_name
            r["artist_slug"] = artist_slug
        all_results.extend(results)

    except Exception as e:
        logger.warning("Failed for '%s': %s", artist_name, e)

    return all_results


def _search_artist_slug(page, artist_name: str) -> str | None:
    """Artsy 검색으로 정확한 slug 찾기."""
    try:
        page.goto(
            "https://www.artsy.net/price-database",
            wait_until="domcontentloaded",
            timeout=30000,
        )
        time.sleep(1)

        # 검색 입력
        search_box = page.get_by_role("combobox", name="Search by Artist Name")
        search_box.click()
        search_box.fill(artist_name)
        time.sleep(1.5)

        # 자동완성 결과에서 slug 추출
        slug = page.evaluate(f"""() => {{
            const options = document.querySelectorAll('[role="option"]');
            for (const opt of options) {{
                const text = opt.textContent.toLowerCase();
                if (text.includes('{artist_name.lower()}')) {{
                    return opt.textContent.trim();
                }}
            }}
            return null;
        }}""")

        if slug:
            return _get_artist_slug(slug)
    except Exception as e:
        logger.warning("Search failed for '%s': %s", artist_name, e)

    return None


def scrape_all(
    artists: list[str],
    output_path: str | Path,
    headless: bool = False,
    max_pages_per_artist: int = 5,
) -> int:
    """전체 작가 경매 결과 스크래핑.

    브라우저 세션을 재사용하여 로그인 상태 유지.
    """
    from playwright.sync_api import sync_playwright

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    all_results: list[dict] = []

    with sync_playwright() as p:
        # 기존 브라우저 세션 사용 (로그인 상태 유지)
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            storage_state=str(Path.home() / ".artsy_session.json")
            if (Path.home() / ".artsy_session.json").exists()
            else None,
        )
        page = context.new_page()

        for i, artist in enumerate(artists):
            logger.info("[%d/%d] Scraping: %s", i + 1, len(artists), artist)

            # 한국어 작가명 → 영어 slug 매핑 시도
            # 일반적인 한국 작가: "이우환" → "lee-ufan"
            results = scrape_artist_auctions(
                page, artist, max_pages=max_pages_per_artist
            )

            if not results:
                # slug가 안 맞으면 검색으로 재시도
                logger.info("  → No results. Trying search...")
                slug = _search_artist_slug(page, artist)
                if slug:
                    results = scrape_artist_auctions(
                        page, artist, artist_slug=slug,
                        max_pages=max_pages_per_artist,
                    )

            all_results.extend(results)
            logger.info(
                "  → %d results (total: %d)", len(results), len(all_results)
            )
            time.sleep(REQUEST_DELAY)

        # 세션 저장 (다음 실행 시 재사용)
        context.storage_state(
            path=str(Path.home() / ".artsy_session.json")
        )
        browser.close()

    # CSV 저장
    if all_results:
        fieldnames = [
            "artist_name", "artist_slug", "title", "medium", "dimensions",
            "date", "auction_house", "sale_name", "lot",
            "price", "estimate", "sold_status", "url", "raw_text",
        ]
        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(all_results)
        logger.info("Saved %d results to %s", len(all_results), output_path)

    return len(all_results)


def save_browser_session() -> None:
    """현재 브라우저 세션을 저장 (최초 1회 로그인 후 실행)."""
    from playwright.sync_api import sync_playwright

    print("브라우저가 열립니다. Artsy에 로그인하세요.")
    print("로그인 완료 후 이 터미널에서 Enter를 누르세요.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.artsy.net/log_in")

        input("로그인 완료 후 Enter 키를 누르세요...")

        session_path = str(Path.home() / ".artsy_session.json")
        context.storage_state(path=session_path)
        print(f"세션 저장 완료: {session_path}")
        browser.close()


def main() -> None:
    """CLI 진입점."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(message)s"
    )
    parser = argparse.ArgumentParser(
        description="Artsy 경매 결과 스크래핑"
    )
    parser.add_argument(
        "--output", default="data/artsy_auctions.csv"
    )
    parser.add_argument("--sample", type=int, default=0)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--save-session", action="store_true",
        help="브라우저를 열어 로그인 세션 저장",
    )
    args = parser.parse_args()

    if args.save_session:
        save_browser_session()
        return

    # K-Auction 작가 리스트
    import pandas as pd

    works_path = Path("data/k-auction-works-20260325.csv")
    df = pd.read_csv(works_path, encoding="utf-8-sig")
    artists = sorted(df["작가"].dropna().unique().tolist())
    logger.info("Loaded %d artists", len(artists))

    if args.sample > 0:
        # 유명 작가 우선 (거래 수 기준)
        top_artists = (
            df.groupby("작가")
            .size()
            .sort_values(ascending=False)
            .head(args.sample)
            .index.tolist()
        )
        artists = top_artists

    scrape_all(artists, args.output, headless=args.headless)


if __name__ == "__main__":
    main()
