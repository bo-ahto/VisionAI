"""Artsy GraphQL 기반 한국 작가 작품+프로필 수집기.

Artsy의 공개 GraphQL endpoint(metaphysics-cdn.artsy.net/v2)를 사용하여
한국 작가의 작품 데이터를 수집한다. Playwright 불필요.

수집 항목:
- 작품: 제목, 연도, 매체, 크기, 가격, 갤러리
- 작가: 이름, slug, 국적, 생년, 팔로워, 작품수
- 작가별 전시 이력 (showsConnection)
"""
from __future__ import annotations

import json
import logging
import time
import urllib.request
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
GRAPHQL_URL = "https://metaphysics-cdn.artsy.net/v2"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}
DELAY = 1.0  # 요청 간 대기 (초)
PAGE_SIZE = 100  # 페이지당 작품 수

# --- GraphQL Queries ---

ARTWORKS_QUERY = """query ArtworkCollect($input: FilterArtworksInput) {
  viewer {
    artworksConnection(input: $input) {
      counts { total }
      pageInfo { hasNextPage endCursor }
      edges {
        node {
          internalID
          slug
          title
          date
          medium
          category
          dimensions { cm }
          sale_message: saleMessage
          collecting_institution: collectingInstitution
          artists(shallow: true) {
            internalID
            slug
            name
            formattedNationalityAndBirthday
            counts { artworks forSaleArtworks }
          }
          partner(shallow: true) {
            name
            href
          }
        }
      }
    }
  }
}"""

ARTIST_SHOWS_QUERY = """query ArtistShows($slug: String!) {
  artist(id: $slug) {
    name
    slug
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
          endAt
          city
          partner {
            ... on Partner { name }
          }
        }
      }
    }
  }
}"""


def graphql_request(query: str, variables: dict | None = None) -> dict:
    """GraphQL 요청을 실행한다."""
    payload = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
    req = urllib.request.Request(GRAPHQL_URL, data=payload, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def collect_artworks(max_pages: int = 0) -> tuple[list[dict], dict]:
    """한국 작가 작품 데이터를 페이지네이션으로 수집한다.

    Returns:
        (artworks_list, artists_dict): 작품 리스트, 고유 작가 딕셔너리
    """
    all_artworks: list[dict] = []
    artists: dict[str, dict] = {}  # slug -> artist info
    cursor = None
    page = 0

    while True:
        page += 1
        variables: dict = {
            "input": {
                "sort": "-decayed_merch",
                "artistNationalities": ["South Korean", "Korean"],
                "locationCities": ["Seoul, South Korea", "Busan, South Korea"],
                "first": PAGE_SIZE,
            }
        }
        if cursor:
            variables["input"]["after"] = cursor

        try:
            data = graphql_request(ARTWORKS_QUERY, variables)
        except Exception as e:
            logger.error("Page %d failed: %s", page, e)
            time.sleep(5)
            continue

        conn = data["data"]["viewer"]["artworksConnection"]
        edges = conn["edges"]
        total = conn["counts"]["total"]
        cursor = conn["pageInfo"]["endCursor"]
        has_next = conn["pageInfo"]["hasNextPage"]

        for edge in edges:
            node = edge["node"]
            artwork = {
                "artwork_id": node["internalID"],
                "slug": node["slug"],
                "title": node["title"],
                "date": node.get("date", ""),
                "medium": node.get("medium", ""),
                "category": node.get("category", ""),
                "dimensions_cm": node.get("dimensions", {}).get("cm", ""),
                "price": node.get("sale_message", ""),
                "collecting_institution": node.get("collecting_institution", ""),
                "gallery": node.get("partner", {}).get("name", "") if node.get("partner") else "",
                "gallery_href": node.get("partner", {}).get("href", "") if node.get("partner") else "",
            }

            # 작가 정보
            if node.get("artists"):
                artist = node["artists"][0]
                artwork["artist_name"] = artist["name"]
                artwork["artist_slug"] = artist["slug"]
                artwork["artist_nat_birthday"] = artist.get("formattedNationalityAndBirthday", "")
                artwork["artist_total_works"] = artist.get("counts", {}).get("artworks", 0)
                artwork["artist_for_sale"] = artist.get("counts", {}).get("forSaleArtworks", 0)

                # 고유 작가 추적
                if artist["slug"] not in artists:
                    artists[artist["slug"]] = {
                        "slug": artist["slug"],
                        "name": artist["name"],
                        "internalID": artist["internalID"],
                        "nationality_birthday": artist.get("formattedNationalityAndBirthday", ""),
                        "total_works": artist.get("counts", {}).get("artworks", 0),
                        "for_sale_works": artist.get("counts", {}).get("forSaleArtworks", 0),
                    }

            all_artworks.append(artwork)

        logger.info(
            "Page %d: %d artworks (total %d/%d, artists %d)",
            page, len(edges), len(all_artworks), total, len(artists),
        )

        if not has_next:
            break
        if max_pages and page >= max_pages:
            logger.info("Max pages (%d) reached", max_pages)
            break

        time.sleep(DELAY)

    return all_artworks, artists


def collect_artist_shows(artist_slugs: list[str]) -> dict[str, dict]:
    """작가별 전시 이력을 수집한다."""
    results: dict[str, dict] = {}

    for i, slug in enumerate(artist_slugs):
        try:
            data = graphql_request(ARTIST_SHOWS_QUERY, {"slug": slug})
            artist = data["data"]["artist"]
            if not artist:
                continue

            shows = artist.get("showsConnection", {})
            show_list = []
            for edge in shows.get("edges", []):
                node = edge["node"]
                show_list.append({
                    "name": node.get("name", ""),
                    "kind": node.get("kind", ""),
                    "start_at": node.get("startAt", "")[:10] if node.get("startAt") else "",
                    "end_at": node.get("endAt", "")[:10] if node.get("endAt") else "",
                    "city": node.get("city", ""),
                    "partner": node.get("partner", {}).get("name", "") if node.get("partner") else "",
                })

            solo = [s for s in show_list if s["kind"] == "solo"]
            group = [s for s in show_list if s["kind"] == "group"]
            fair = [s for s in show_list if s["kind"] == "fair"]

            results[slug] = {
                "name": artist["name"],
                "slug": slug,
                "nationality_birthday": artist.get("formattedNationalityAndBirthday", ""),
                "bio": artist.get("biographyBlurb", {}).get("text", "") if artist.get("biographyBlurb") else "",
                "followers": artist.get("counts", {}).get("follows", 0),
                "total_shows": shows.get("totalCount", 0),
                "solo_count": len(solo),
                "group_count": len(group),
                "fair_count": len(fair),
                "shows": show_list,
            }

            if (i + 1) % 50 == 0:
                logger.info("Shows: %d/%d artists processed", i + 1, len(artist_slugs))

        except Exception as e:
            logger.warning("Shows for %s failed: %s", slug, e)

        time.sleep(0.5)

    return results


def main() -> None:
    logger.info("=== Artsy 한국 작가 데이터 수집 시작 ===")

    # Phase 1: 작품 데이터 수집
    # max_pages=0 → 전체 수집, 테스트 시 max_pages=5 등으로 제한
    artworks, artists = collect_artworks(max_pages=5)  # 테스트: 5페이지 (500건)

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 작품 저장
    artworks_path = DATA_DIR / "artsy_korean_artworks.json"
    with open(artworks_path, "w", encoding="utf-8") as f:
        json.dump(artworks, f, ensure_ascii=False, indent=2)
    logger.info("Artworks saved: %s (%d works)", artworks_path, len(artworks))

    # 작가 저장
    artists_path = DATA_DIR / "artsy_korean_artists.json"
    artists_list = sorted(artists.values(), key=lambda x: -x["total_works"])
    with open(artists_path, "w", encoding="utf-8") as f:
        json.dump(artists_list, f, ensure_ascii=False, indent=2)
    logger.info("Artists saved: %s (%d artists)", artists_path, len(artists_list))

    # Phase 2: 상위 작가 전시 이력 수집
    top_slugs = [a["slug"] for a in artists_list[:100]]  # 상위 100명
    if top_slugs:
        logger.info("Phase 2: 상위 %d명 전시 이력 수집", len(top_slugs))
        shows = collect_artist_shows(top_slugs)

        shows_path = DATA_DIR / "artsy_korean_artist_shows.json"
        with open(shows_path, "w", encoding="utf-8") as f:
            json.dump(shows, f, ensure_ascii=False, indent=2)
        logger.info("Shows saved: %s (%d artists)", shows_path, len(shows))

    # 요약
    prices = [a["price"] for a in artworks if a.get("price") and "$" in a["price"]]
    galleries = set(a.get("gallery", "") for a in artworks if a.get("gallery"))

    print(f"\n{'='*70}")
    print("Artsy 한국 작가 데이터 수집 완료")
    print(f"{'='*70}")
    print(f"  총 작품: {len(artworks)}건")
    print(f"  고유 작가: {len(artists)}명")
    print(f"  가격 표시 작품: {len(prices)}건")
    print(f"  갤러리 수: {len(galleries)}개")
    if artists_list:
        print(f"\n  상위 작가 (작품수 기준):")
        for a in artists_list[:10]:
            print(f"    {a['name']} ({a['slug']}) — {a['total_works']}작품, 판매중 {a['for_sale_works']}")


if __name__ == "__main__":
    main()
