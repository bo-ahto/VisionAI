"""Artsy 스크래핑 테스트 — 영문 slug로 5명 작가."""
from __future__ import annotations

import csv
import logging
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("test")

TEST_ARTISTS = [
    ("이우환", "lee-ufan"),
    ("박서보", "park-seo-bo"),
    ("김환기", "kim-whan-ki"),
    ("타카시 무라카미", "takashi-murakami"),
    ("김창열", "kim-tschang-yeul"),
]

JS_EXTRACT = """() => {
    const links = document.querySelectorAll('a[href*="auction-result/"]');
    const results = [];
    for (const link of links) {
        const href = link.getAttribute('href');
        if (!href || !href.match(/\\/auction-result\\/\\d+/)) continue;
        const lines = link.innerText.split('\\n').map(l => l.trim()).filter(l => l);
        const r = {
            title: lines[0] || '',
            medium: lines[1] || '',
            dimensions: lines[2] || '',
            date: lines[3] || '',
            auction_house: lines[4] || '',
            sale_name: lines[5] || '',
            lot: lines[6] || '',
            price: '',
            estimate: '',
            url: href,
        };
        for (const line of lines) {
            if (/[\\$\\€\\£\\¥]|HK\\$|JPY|KRW/i.test(line) && line.includes('est')) {
                r.estimate = line;
            } else if (/[\\$\\€\\£\\¥]|HK\\$|Bought in/i.test(line) && !r.price) {
                r.price = line;
            }
        }
        results.push(r);
    }
    return results;
}"""


def main() -> None:
    all_results: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            storage_state=str(Path.home() / ".artsy_session.json"),
        )
        page = context.new_page()

        for korean, slug in TEST_ARTISTS:
            url = f"https://www.artsy.net/artist/{slug}/auction-results"
            logger.info("Fetching: %s (%s)", korean, slug)
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(3)

                results = page.evaluate(JS_EXTRACT)
                for r in results:
                    r["artist_kr"] = korean
                    r["artist_slug"] = slug
                all_results.extend(results)
                logger.info("  → %d results", len(results))
            except Exception as e:
                logger.warning("  → Error: %s", str(e)[:100])
            time.sleep(2)

        context.storage_state(path=str(Path.home() / ".artsy_session.json"))
        browser.close()

    logger.info("Total: %d results from %d artists", len(all_results), len(TEST_ARTISTS))

    if all_results:
        out = Path("data/artsy_auctions_test.csv")
        out.parent.mkdir(exist_ok=True)
        fields = [
            "artist_kr", "artist_slug", "title", "medium", "dimensions",
            "date", "auction_house", "sale_name", "lot", "price", "estimate", "url",
        ]
        with open(out, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(all_results)
        logger.info("Saved to %s", out)

        # 샘플 출력
        print("\n=== 샘플 결과 ===")
        for r in all_results[:8]:
            print(
                f"{r['artist_kr']} | {r['title'][:30]} | "
                f"{r['auction_house'][:20]} | {r.get('price', 'N/A')} | "
                f"{r.get('estimate', 'N/A')[:40]}"
            )


if __name__ == "__main__":
    main()
