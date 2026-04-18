"""영문명 기반 Artsy 검색 — 한글 검색 실패 작가 재시도.

주요 한국 작가의 영문명으로 Artsy 검색.

Usage:
    PYTHONPATH=src python3 scripts/collectors/expand_artsy_english.py
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

import pandas as pd
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent.parent
MAPPING_PATH = ROOT / "data" / "artist_slug_mapping_expanded.csv"
OUTPUT_PATH = ROOT / "data" / "artist_slug_mapping_expanded.csv"

ARTSY_SEARCH_URL = "https://metaphysics-cdn.artsy.net/v2"

# 한글→영문 수동 매핑 (Artsy에 있을 가능성 높은 작가)
MANUAL_EN_NAMES = {
    "윤형근": "Yun Hyong-keun",
    "하종현": "Ha Chong-Hyun",
    "박수근": "Park Soo Keun",
    "이응노": "Lee Ungno",
    "김구림": "Kim Kulim",
    "문신": "Moon Shin",
    "곽인식": "Quac Insik",
    "안창홍": "Ahn Chang Hong",
    "이동기": "Lee Dong-gi",
    "우국원": "Woo Kukwon",
    "이성자": "Lee Seung-Ja",
    "박생광": "Park Saeng-Kwang",
    "최울가": "Choi Ul-Ga",
    "정창섭": "Chung Chang-Sup",
    "곽훈": "Kwak Hoon",
    "하인두": "Ha In-Du",
    "오치균": "Oh Chi-Gyun",
    "임옥상": "Im Ok-Sang",
    "권순철": "Kwon Soon-Chul",
    "데미안 허스트": "Damien Hirst",
    "데이비드 호크니": "David Hockney",
    "요시토모 나라": "Yoshitomo Nara",
    "아야코 록카쿠": "Ayako Rokkaku",
    "알렉스 카츠": "Alex Katz",
    "마르크 샤갈": "Marc Chagall",
    "줄리안 오피": "Julian Opie",
    "살바도르 달리": "Salvador Dali",
    "치하루 시오타": "Chiharu Shiota",
    "앤디 워홀": "Andy Warhol",
    "우고 론디노네": "Ugo Rondinone",
    "제임스 진": "James Jean",
    "아담 핸들러": "Adam Handler",
    "에바 알머슨": "Eva Armisen",
    "변시지": "Byun Shi-Ji",
    "남춘모": "Nam Tchun-Mo",
    "민병헌": "Min Byung-Hun",
    "배동신": "Bae Dong-Shin",
    "류병엽": "Ryu Byung-Yup",
    "이숙자": "Lee Sook-Ja",
    "김강용": "Kim Kang-Yong",
}


def search_artsy(name: str) -> dict | None:
    """Artsy GraphQL 검색."""
    query = """
    query SearchArtist($query: String!) {
      searchConnection(query: $query, first: 3, entities: [ARTIST]) {
        edges {
          node {
            ... on Artist {
              slug
              name
              nationality
              birthday
            }
          }
        }
      }
    }
    """
    try:
        resp = requests.post(
            ARTSY_SEARCH_URL,
            json={"query": query, "variables": {"query": name}},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        edges = resp.json().get("data", {}).get("searchConnection", {}).get("edges", [])
        if not edges:
            return None
        node = edges[0].get("node", {})
        return {"slug": node.get("slug", ""), "name": node.get("name", "")} if node.get("slug") else None
    except Exception:
        return None


def main() -> None:
    """영문명 기반 Artsy 매핑 확장."""
    logger.info("=== 영문명 Artsy 검색 ===")

    existing = pd.read_csv(MAPPING_PATH)
    existing_slugs = set(existing["en_slug"].values)
    existing_ko = set(existing["ko_name"].values)
    logger.info("기존 매핑: %d명", len(existing))

    new_found = []
    for ko_name, en_name in MANUAL_EN_NAMES.items():
        if ko_name in existing_ko:
            continue

        result = search_artsy(en_name)
        if result and result["slug"] not in existing_slugs:
            new_found.append({
                "ko_name": ko_name,
                "en_slug": result["slug"],
                "en_name": result["name"],
            })
            existing_slugs.add(result["slug"])
            logger.info("  %s → %s (%s) ✓", ko_name, result["slug"], result["name"])
        else:
            logger.info("  %s (%s) → Not found", ko_name, en_name)
        time.sleep(0.5)

    if new_found:
        expanded = pd.concat([existing, pd.DataFrame(new_found)], ignore_index=True)
        expanded.to_csv(OUTPUT_PATH, index=False)
        logger.info("Total: %d (+%d new)", len(expanded), len(new_found))
    else:
        logger.info("No new mappings found")


if __name__ == "__main__":
    main()
