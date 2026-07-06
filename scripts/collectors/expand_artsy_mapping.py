"""K-Auction 상위 작가 → Artsy slug 자동 매핑 확장.

Artsy search API로 한글 작가명을 영문 slug로 변환.
기존 매핑에 없는 작가만 검색.

Usage:
    PYTHONPATH=src python3 scripts/collectors/expand_artsy_mapping.py
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
DATA_PATH = ROOT / "data" / "k-auction-works-20260325.csv"
MAPPING_PATH = ROOT / "data" / "artist_slug_mapping.csv"
OUTPUT_PATH = ROOT / "data" / "artist_slug_mapping_expanded.csv"

# Artsy public search (no auth needed)
ARTSY_SEARCH_URL = "https://metaphysics-cdn.artsy.net/v2"


def search_artsy_artist(name: str) -> dict | None:
    """Artsy GraphQL API로 작가 검색.

    Returns:
        dict with slug, name, nationality or None.
    """
    # 한글 이름에서 호(號) 접두사 제거
    clean_name = name
    prefixes = [
        "운보 ", "산정 ", "유산 ", "의재 ", "남농 ", "고암 ",
        "청전 ", "월전 ", "이당 ", "소정 ", "근원 ", "수화 ",
        "석재 ", "무호 ", "남천 ", "일중 ",
    ]
    for prefix in prefixes:
        if clean_name.startswith(prefix):
            clean_name = clean_name[len(prefix):]
            break

    # "(사후판화)" 등 부가 설명 제거
    if "(" in clean_name:
        clean_name = clean_name[:clean_name.index("(")].strip()

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
              deathday
            }
          }
        }
      }
    }
    """

    try:
        resp = requests.post(
            ARTSY_SEARCH_URL,
            json={"query": query, "variables": {"query": clean_name}},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if resp.status_code != 200:
            return None

        data = resp.json()
        edges = data.get("data", {}).get("searchConnection", {}).get("edges", [])
        if not edges:
            return None

        node = edges[0].get("node", {})
        if not node.get("slug"):
            return None

        return {
            "slug": node["slug"],
            "name": node.get("name", ""),
            "nationality": node.get("nationality", ""),
            "birthday": node.get("birthday", ""),
        }
    except Exception:
        return None


def main() -> None:
    """Artsy slug 매핑 확장."""
    logger.info("=== Artsy Slug 매핑 확장 ===")

    # K-Auction 작가 빈도순
    df = pd.read_csv(DATA_PATH, low_memory=False)
    artist_counts = df["작가"].value_counts()

    # 기존 매핑
    existing = pd.read_csv(MAPPING_PATH)
    existing_names = set(existing["ko_name"].values)
    logger.info("기존 매핑: %d명", len(existing_names))

    # 상위 200 중 미매핑
    candidates = [
        (name, int(count))
        for name, count in artist_counts.head(200).items()
        if name not in existing_names and name != "작자미상"
    ]
    logger.info("검색 대상: %d명", len(candidates))

    new_mappings = []
    for i, (name, count) in enumerate(candidates):
        result = search_artsy_artist(name)
        if result:
            new_mappings.append({
                "ko_name": name,
                "en_slug": result["slug"],
                "en_name": result["name"],
                "nationality": result.get("nationality", ""),
                "kauction_count": count,
            })
            logger.info(
                "[%d/%d] %s → %s (%s) ✓",
                i + 1, len(candidates), name, result["slug"], result["name"],
            )
        else:
            logger.info("[%d/%d] %s → Not found", i + 1, len(candidates), name)

        time.sleep(0.5)  # rate limit

    # 결과 저장
    if new_mappings:
        new_df = pd.DataFrame(new_mappings)
        # 기존 + 신규 병합
        expanded = pd.concat([
            existing,
            new_df[["ko_name", "en_slug", "en_name"]],
        ], ignore_index=True)
        expanded.to_csv(OUTPUT_PATH, index=False)
        logger.info("Saved: %d total (%d new)", len(expanded), len(new_mappings))

        # 신규 매핑 별도 저장
        new_df.to_csv(ROOT / "data" / "artsy_new_mappings.csv", index=False)
    else:
        logger.warning("No new mappings found!")

    logger.info("=== 완료 ===")


if __name__ == "__main__":
    main()
