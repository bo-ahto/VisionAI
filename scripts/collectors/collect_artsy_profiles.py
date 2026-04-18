"""Artsy 작가 프로필 수집 — 71명 확장 매핑 기반.

공개 GraphQL API로 수집 가능한 데이터:
- nationality, birthday, deathday
- bio, artworks count
- insights (전시, 컬렉션, 리뷰 등)

Usage:
    PYTHONPATH=src python3 scripts/collectors/collect_artsy_profiles.py
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import pandas as pd
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent.parent
MAPPING_PATH = ROOT / "data" / "artist_slug_mapping_expanded.csv"
OUTPUT_PATH = ROOT / "data" / "artsy_artist_profiles.csv"

ARTSY_GQL = "https://metaphysics-cdn.artsy.net/v2"

QUERY = """
query ArtistProfile($slug: String!) {
  artist(id: $slug) {
    name
    nationality
    birthday
    deathday
    bio
    counts { artworks forSaleArtworks }
    insights { type label entities }
  }
}
"""


def fetch_profile(slug: str) -> dict | None:
    """작가 프로필 조회."""
    try:
        resp = requests.post(
            ARTSY_GQL,
            json={"query": QUERY, "variables": {"slug": slug}},
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        artist = resp.json().get("data", {}).get("artist")
        return artist
    except Exception:
        return None


def parse_insights(insights: list[dict]) -> dict:
    """insights → 피처 변환."""
    result = {
        "solo_show_institution": "",
        "group_show_institution": "",
        "private_collection": "",
        "museum_collection": "",
        "review_count": 0,
        "artsy_vanguard": False,
    }
    for insight in insights:
        itype = insight.get("type", "")
        entities = insight.get("entities", [])
        if itype == "SOLO_SHOW" and entities:
            result["solo_show_institution"] = entities[0]
        elif itype == "GROUP_SHOW" and entities:
            result["group_show_institution"] = entities[0]
        elif itype == "PRIVATE_COLLECTIONS" and entities:
            result["private_collection"] = entities[0]
        elif itype == "COLLECTED" and entities:
            result["museum_collection"] = entities[0]
        elif itype == "REVIEWED":
            result["review_count"] = len(entities)
        elif itype == "ARTSY_VANGUARD_YEAR":
            result["artsy_vanguard"] = True
    return result


def main() -> None:
    """71명 작가 프로필 수집."""
    logger.info("=== Artsy 작가 프로필 수집 ===")
    mapping = pd.read_csv(MAPPING_PATH)
    logger.info("대상: %d명", len(mapping))

    profiles = []
    for i, row in mapping.iterrows():
        slug = row["en_slug"]
        ko_name = row["ko_name"]

        data = fetch_profile(slug)
        if data is None:
            logger.info("[%d/%d] %s → Failed", i + 1, len(mapping), ko_name)
            profiles.append({"ko_name": ko_name, "en_slug": slug, "found": False})
            time.sleep(0.3)
            continue

        insights = parse_insights(data.get("insights", []))
        counts = data.get("counts", {})

        profile = {
            "ko_name": ko_name,
            "en_slug": slug,
            "en_name": data.get("name", ""),
            "nationality": data.get("nationality", ""),
            "birth_year": data.get("birthday", ""),
            "death_year": data.get("deathday", ""),
            "bio": (data.get("bio", "") or "")[:200],
            "artworks_count": counts.get("artworks", 0),
            "for_sale_count": counts.get("forSaleArtworks", 0),
            "found": True,
            **insights,
        }
        profiles.append(profile)
        logger.info(
            "[%d/%d] %s → %s, %s, artworks=%d",
            i + 1, len(mapping), ko_name, data.get("nationality", "?"),
            data.get("birthday", "?"), counts.get("artworks", 0),
        )
        time.sleep(0.3)

    df = pd.DataFrame(profiles)
    df.to_csv(OUTPUT_PATH, index=False)

    found = df["found"].sum()
    logger.info("=== 결과: %d/%d 수집 완료 ===", found, len(mapping))
    logger.info("Saved to %s", OUTPUT_PATH)


if __name__ == "__main__":
    main()
