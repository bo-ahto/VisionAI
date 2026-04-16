"""Artsy GraphQL 실시간 작가 조회."""
from __future__ import annotations

import json
import logging
import re
import urllib.request

from rapidfuzz import fuzz

logger = logging.getLogger(__name__)

GRAPHQL_URL = "https://metaphysics-cdn.artsy.net/v2"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "VisionAI-API/1.0",
}

SEARCH_QUERY = """
query SearchArtist($query: String!) {
  searchConnection(query: $query, first: 5, entities: [ARTIST]) {
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

PROFILE_QUERY = """
query ArtistProfile($slug: String!) {
  artist(id: $slug) {
    name
    slug
    nationality
    birthday
    gender
    formattedNationalityAndBirthday
    biographyBlurb { text }
    counts { artworks forSaleArtworks follows }
    showsConnection(first: 100, sort: END_AT_DESC) {
      totalCount
      edges {
        node {
          name
          kind
          startAt
          city
          partner { ... on Partner { name } }
        }
      }
    }
  }
}
"""


def _graphql(query: str, variables: dict | None = None, timeout: int = 3) -> dict | None:
    payload = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(GRAPHQL_URL, data=payload, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        logger.warning("Artsy GraphQL error: %s", e)
        return None


def search_artist(name: str) -> dict | None:
    """이름으로 Artsy 작가 검색 → slug + 기본 정보 반환."""
    data = _graphql(SEARCH_QUERY, {"query": name})
    if not data:
        return None

    edges = (data.get("data") or {}).get("searchConnection", {}).get("edges", [])
    if not edges:
        return None

    query_lower = name.lower().strip()

    # Korean 작가 우선, fuzzy 매칭
    best = None
    best_score = 0

    for edge in edges:
        node = edge.get("node", {})
        if not node.get("slug"):
            continue
        artist_name = node.get("name", "")
        score = fuzz.ratio(query_lower, artist_name.lower())

        # Korean nationality 보너스
        nat = (node.get("nationality") or "").lower()
        if "korea" in nat:
            score += 10

        if score > best_score:
            best_score = score
            best = node

    if best and best_score >= 75:
        return {
            "slug": best["slug"],
            "name": best.get("name", ""),
            "nationality": best.get("nationality"),
            "birthday": best.get("birthday"),
        }

    return None


def get_artist_profile(slug: str) -> dict | None:
    """slug로 프로필 + 전시 이력 수집 → profile dict 반환."""
    data = _graphql(PROFILE_QUERY, {"slug": slug}, timeout=5)
    if not data:
        return None

    artist = (data.get("data") or {}).get("artist")
    if not artist:
        return None

    counts = artist.get("counts", {})
    shows = artist.get("showsConnection", {}).get("edges", [])

    solo_count = sum(1 for s in shows if s.get("node", {}).get("kind") == "solo")
    group_count = sum(1 for s in shows if s.get("node", {}).get("kind") == "group")
    fair_count = sum(1 for s in shows if s.get("node", {}).get("kind") == "fair")

    # 생년 추출
    birth_year = None
    birthday = artist.get("birthday") or ""
    m = re.search(r"(\d{4})", birthday)
    if m:
        y = int(m.group(1))
        if 1900 <= y <= 2010:
            birth_year = y

    # career_stage 추정
    age = 2026 - birth_year if birth_year else None
    if age and age >= 60 and solo_count >= 5:
        career_stage = 4
    elif solo_count >= 3:
        career_stage = 3
    elif solo_count >= 1 or group_count >= 5:
        career_stage = 2
    else:
        career_stage = 1

    bio = ""
    bio_blurb = artist.get("biographyBlurb") or {}
    if bio_blurb.get("text"):
        bio = bio_blurb["text"][:500]

    completeness = sum([bool(birth_year), bool(solo_count or group_count), bool(bio)])

    return {
        "source": "artsy",
        "birth_year": birth_year,
        "birth_year_from_source": birth_year,
        "nationality": artist.get("nationality"),
        "total_works": counts.get("artworks", 0) or 0,
        "followers": counts.get("follows", 0) or 0,
        "solo_count": solo_count,
        "group_count": group_count,
        "fair_count": fair_count,
        "career_stage": career_stage,
        "career_age": 0,
        "for_sale_ratio": 1.0,
        "profile_completeness": completeness,
        "gallery_name": "Artsy",
        "gallery_type": "Gallery",
        "gallery_tier": 3,
        "bio": bio,
    }


def lookup(artist_name: str) -> dict | None:
    """이름으로 검색 → 프로필 수집. 실패 시 None."""
    search_result = search_artist(artist_name)
    if not search_result:
        return None

    profile = get_artist_profile(search_result["slug"])
    if profile:
        logger.info("Artsy: found %s (slug=%s)", artist_name, search_result["slug"])
    return profile
