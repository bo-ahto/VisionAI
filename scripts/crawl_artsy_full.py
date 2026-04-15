"""Artsy 한국 작가 작품+프로필 전체 수집기.

GraphQL API로 31,000건 전체를 수집하고,
고유 작가별 전시 이력을 추가 수집한 뒤,
작품-작가 매칭 데이터셋을 생성한다.
"""
from __future__ import annotations

import csv
import json
import logging
import re
import time
import urllib.request
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
GRAPHQL_URL = "https://metaphysics-cdn.artsy.net/v2"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}
DELAY = 1.0
PAGE_SIZE = 100

# 환율 (2026-04-13 기준 근사치)
FX_RATES = {
    "USD": 1380,   # 1 USD = 1,380 KRW
    "GBP": 1780,   # 1 GBP = 1,780 KRW
    "EUR": 1530,   # 1 EUR = 1,530 KRW
    "HKD": 178,    # 1 HKD = 178 KRW
}

# ─── GraphQL Queries ────────────────────────────────────────────────

ARTWORKS_QUERY = """query CollectKorean($input: FilterArtworksInput) {
  viewer {
    artworksConnection(input: $input) {
      counts { total }
      pageInfo { hasNextPage endCursor }
      edges {
        node {
          internalID
          slug
          href
          title
          date
          medium
          category
          dimensions { in cm }
          saleMessage
          priceListedDisplay
          availability
          collectingInstitution
          additionalInformation
          provenance
          series
          artistNames
          attributionClass { name }
          mediumType { filterGene { name } }
          image(includeAll: false) {
            url(version: ["large"])
            aspectRatio
          }
          artists(shallow: true) {
            internalID
            slug
            name
            formattedNationalityAndBirthday
            nationality
            birthday
            gender
            hometown
            location
            counts { artworks forSaleArtworks follows }
            targetSupply { isP1 }
          }
          partner(shallow: true) {
            name
            href
            type
            cities
          }
          sale {
            isAuction
            isClosed
            name
          }
          certificateOfAuthenticity { details }
          signatureInfo { details }
          framed { details }
        }
      }
    }
  }
}"""

ARTIST_SHOWS_QUERY = """query ArtistShows {
  artist(id: "%SLUG%") {
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
            ... on Partner { name type }
          }
        }
      }
    }
  }
}"""


# ─── Price Parsing ──────────────────────────────────────────────────

def parse_price(price_str: str | None) -> dict:
    """가격 문자열을 파싱하여 원화로 변환."""
    result = {
        "price_raw": price_str or "",
        "price_currency": None,
        "price_amount": None,
        "price_krw": None,
    }
    if not price_str:
        return result

    # KRW
    m = re.search(r"(?:KRW|₩)\s*[₩]?\s*([\d,]+)", price_str)
    if m:
        amount = int(m.group(1).replace(",", ""))
        result.update(price_currency="KRW", price_amount=amount, price_krw=amount)
        return result

    # USD
    m = re.search(r"US?\$\s*([\d,]+)", price_str)
    if m:
        amount = int(m.group(1).replace(",", ""))
        result.update(price_currency="USD", price_amount=amount, price_krw=int(amount * FX_RATES["USD"]))
        return result

    # GBP
    m = re.search(r"£\s*([\d,]+)", price_str)
    if m:
        amount = int(m.group(1).replace(",", ""))
        result.update(price_currency="GBP", price_amount=amount, price_krw=int(amount * FX_RATES["GBP"]))
        return result

    # EUR
    m = re.search(r"€\s*([\d,]+)", price_str)
    if m:
        amount = int(m.group(1).replace(",", ""))
        result.update(price_currency="EUR", price_amount=amount, price_krw=int(amount * FX_RATES["EUR"]))
        return result

    # HKD
    m = re.search(r"HK\$\s*([\d,]+)", price_str)
    if m:
        amount = int(m.group(1).replace(",", ""))
        result.update(price_currency="HKD", price_amount=amount, price_krw=int(amount * FX_RATES["HKD"]))
        return result

    return result


def parse_dimensions(dims_cm: str | None) -> dict:
    """cm 문자열을 파싱하여 width, height, depth 추출."""
    result = {"width_cm": None, "height_cm": None, "depth_cm": None}
    if not dims_cm:
        return result

    # "90.9 × 60.6 cm" or "27.3 × 22 × 3 cm"
    nums = re.findall(r"([\d.]+)", dims_cm)
    if len(nums) >= 2:
        result["width_cm"] = float(nums[0])
        result["height_cm"] = float(nums[1])
    if len(nums) >= 3:
        result["depth_cm"] = float(nums[2])

    # diameter
    m = re.search(r"diameter\s*([\d.]+)", dims_cm, re.IGNORECASE)
    if m:
        d = float(m.group(1))
        result["width_cm"] = d
        result["height_cm"] = d

    return result


def parse_birth_year(birthday_str: str | None) -> int | None:
    """생년 문자열에서 연도 추출."""
    if not birthday_str:
        return None
    m = re.match(r"(\d{4})", birthday_str)
    return int(m.group(1)) if m else None


# ─── GraphQL Request ────────────────────────────────────────────────

def gql(query: str, variables: dict | None = None) -> dict:
    """GraphQL 요청 실행."""
    body = {"query": query}
    if variables:
        body["variables"] = variables
    payload = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(GRAPHQL_URL, data=payload, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ─── Phase 1: Artworks ─────────────────────────────────────────────

def collect_all_artworks() -> tuple[list[dict], dict[str, dict]]:
    """전체 31K 작품 + 고유 작가 수집."""
    all_works: list[dict] = []
    artists: dict[str, dict] = {}  # slug -> info
    cursor = None
    page = 0
    total_expected = 0

    while True:
        page += 1
        variables = {
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
            data = gql(ARTWORKS_QUERY, variables)
        except Exception as e:
            logger.error("Page %d FAILED: %s — retrying in 10s", page, e)
            time.sleep(10)
            try:
                data = gql(ARTWORKS_QUERY, variables)
            except Exception as e2:
                logger.error("Page %d RETRY FAILED: %s — skipping", page, e2)
                continue

        conn = data["data"]["viewer"]["artworksConnection"]
        edges = conn["edges"]
        total_expected = conn["counts"]["total"]
        cursor = conn["pageInfo"]["endCursor"]
        has_next = conn["pageInfo"]["hasNextPage"]

        for edge in edges:
            n = edge["node"]

            # 가격 파싱
            price_data = parse_price(n.get("saleMessage"))

            # 크기 파싱
            dims_raw = n.get("dimensions", {}) or {}
            dims = parse_dimensions(dims_raw.get("cm"))

            # 작가 정보
            artist = n["artists"][0] if n.get("artists") else {}
            artist_slug = artist.get("slug", "")
            birth_year = parse_birth_year(artist.get("birthday"))

            # 갤러리 정보
            partner = n.get("partner") or {}

            work = {
                # 작품 기본
                "artwork_id": n["internalID"],
                "artwork_slug": n["slug"],
                "artwork_url": f"https://www.artsy.net{n.get('href', '')}",
                "title": n.get("title", ""),
                "date": n.get("date", ""),
                "medium": n.get("medium", ""),
                "category": n.get("category", ""),
                "medium_type": ((n.get("mediumType") or {}).get("filterGene") or {}).get("name", ""),
                "attribution_class": (n.get("attributionClass") or {}).get("name", ""),
                "availability": n.get("availability", ""),
                "series": n.get("series", ""),
                "provenance": n.get("provenance", ""),
                "collecting_institution": n.get("collectingInstitution", ""),
                "additional_info": (n.get("additionalInformation") or "")[:500],
                "certificate": (n.get("certificateOfAuthenticity") or {}).get("details", ""),
                "signature": (n.get("signatureInfo") or {}).get("details", ""),
                "framed": (n.get("framed") or {}).get("details", ""),
                "image_url": (n.get("image") or {}).get("url", ""),
                "image_aspect_ratio": (n.get("image") or {}).get("aspectRatio"),

                # 크기
                "dimensions_cm": dims_raw.get("cm", ""),
                "dimensions_in": dims_raw.get("in", ""),
                "width_cm": dims["width_cm"],
                "height_cm": dims["height_cm"],
                "depth_cm": dims["depth_cm"],

                # 가격
                "price_raw": price_data["price_raw"],
                "price_currency": price_data["price_currency"],
                "price_amount": price_data["price_amount"],
                "price_krw": price_data["price_krw"],

                # 작가
                "artist_slug": artist_slug,
                "artist_name": artist.get("name", ""),
                "artist_id": artist.get("internalID", ""),
                "artist_nationality": artist.get("nationality", ""),
                "artist_birthday": artist.get("birthday", ""),
                "artist_birth_year": birth_year,
                "artist_gender": artist.get("gender", ""),
                "artist_hometown": artist.get("hometown", ""),
                "artist_location": artist.get("location", ""),
                "artist_total_works": artist.get("counts", {}).get("artworks", 0),
                "artist_for_sale": artist.get("counts", {}).get("forSaleArtworks", 0),
                "artist_followers": artist.get("counts", {}).get("follows", 0),
                "artist_is_p1": artist.get("targetSupply", {}).get("isP1", False),

                # 갤러리
                "gallery_name": partner.get("name", ""),
                "gallery_type": partner.get("type", ""),
                "gallery_cities": ", ".join(partner.get("cities") or []),
                "gallery_href": partner.get("href", ""),

                # 경매 여부
                "is_auction": (n.get("sale") or {}).get("isAuction", False),
                "auction_name": (n.get("sale") or {}).get("name", ""),
            }

            all_works.append(work)

            # 고유 작가 등록
            if artist_slug and artist_slug not in artists:
                artists[artist_slug] = {
                    "slug": artist_slug,
                    "name": artist.get("name", ""),
                    "internalID": artist.get("internalID", ""),
                    "nationality": artist.get("nationality", ""),
                    "birthday": artist.get("birthday", ""),
                    "birth_year": birth_year,
                    "gender": artist.get("gender", ""),
                    "hometown": artist.get("hometown", ""),
                    "location": artist.get("location", ""),
                    "total_works": artist.get("counts", {}).get("artworks", 0),
                    "for_sale_works": artist.get("counts", {}).get("forSaleArtworks", 0),
                    "followers": artist.get("counts", {}).get("follows", 0),
                    "is_p1": artist.get("targetSupply", {}).get("isP1", False),
                    "formatted": artist.get("formattedNationalityAndBirthday", ""),
                }

        logger.info(
            "Page %d: +%d works (total %d/%d, artists %d)",
            page, len(edges), len(all_works), total_expected, len(artists),
        )

        if not has_next:
            break

        time.sleep(DELAY)

    return all_works, artists


# ─── Phase 2: Artist Shows ─────────────────────────────────────────

def collect_artist_shows(slugs: list[str]) -> dict[str, dict]:
    """작가별 전시 이력 수집."""
    results: dict[str, dict] = {}
    total = len(slugs)

    for i, slug in enumerate(slugs):
        try:
            q = ARTIST_SHOWS_QUERY.replace("%SLUG%", slug)
            data = gql(q)
            artist = data["data"].get("artist")
            if not artist:
                continue

            shows_conn = artist.get("showsConnection") or {}
            show_list = []
            for edge in shows_conn.get("edges", []):
                node = edge["node"]
                show_list.append({
                    "name": node.get("name", ""),
                    "kind": node.get("kind", ""),
                    "start_at": (node.get("startAt") or "")[:10],
                    "end_at": (node.get("endAt") or "")[:10],
                    "city": node.get("city", ""),
                    "partner": (node.get("partner") or {}).get("name", ""),
                    "partner_type": (node.get("partner") or {}).get("type", ""),
                })

            solo = [s for s in show_list if s["kind"] == "solo"]
            group = [s for s in show_list if s["kind"] == "group"]
            fair = [s for s in show_list if s["kind"] == "fair"]

            results[slug] = {
                "name": artist["name"],
                "slug": slug,
                "formatted": artist.get("formattedNationalityAndBirthday", ""),
                "bio": (artist.get("biographyBlurb") or {}).get("text", ""),
                "followers": (artist.get("counts") or {}).get("follows", 0),
                "total_shows": shows_conn.get("totalCount", 0),
                "solo_count": len(solo),
                "group_count": len(group),
                "fair_count": len(fair),
                "shows": show_list,
            }

        except Exception as e:
            logger.warning("[%d/%d] %s: %s", i + 1, total, slug, e)

        if (i + 1) % 100 == 0:
            logger.info("Shows: %d/%d artists", i + 1, total)

        time.sleep(0.5)

    return results


# ─── Main ───────────────────────────────────────────────────────────

def main() -> None:
    logger.info("=== Artsy 한국 작가 전체 수집 시작 ===")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Phase 1: 전체 작품 수집
    logger.info("--- Phase 1: 작품 수집 ---")
    t0 = time.time()
    artworks, artists = collect_all_artworks()
    t1 = time.time()
    logger.info("Phase 1 완료: %d works, %d artists in %.0fs", len(artworks), len(artists), t1 - t0)

    # 작품 JSON 저장
    with open(DATA_DIR / "artsy_kr_artworks.json", "w", encoding="utf-8") as f:
        json.dump(artworks, f, ensure_ascii=False, indent=2)

    # 작품 CSV 저장
    csv_fields = [
        "artwork_id", "title", "date", "medium", "category", "medium_type",
        "attribution_class", "availability",
        "dimensions_cm", "width_cm", "height_cm", "depth_cm",
        "price_raw", "price_currency", "price_amount", "price_krw",
        "artist_slug", "artist_name", "artist_nationality", "artist_birth_year",
        "artist_total_works", "artist_for_sale", "artist_followers", "artist_is_p1",
        "gallery_name", "gallery_type", "gallery_cities",
        "is_auction", "image_url", "artwork_url",
    ]
    with open(DATA_DIR / "artsy_kr_artworks.csv", "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(artworks)

    # 작가 JSON 저장
    artists_list = sorted(artists.values(), key=lambda x: -x["total_works"])
    with open(DATA_DIR / "artsy_kr_artists.json", "w", encoding="utf-8") as f:
        json.dump(artists_list, f, ensure_ascii=False, indent=2)

    logger.info("Saved: artsy_kr_artworks.json/csv, artsy_kr_artists.json")

    # Phase 2: 작가 전시 이력 (작품 5건 이상인 작가)
    logger.info("--- Phase 2: 작가 전시 이력 수집 ---")
    active_slugs = [a["slug"] for a in artists_list if a["total_works"] >= 5]
    logger.info("대상 작가: %d명 (작품 5건+)", len(active_slugs))

    t2 = time.time()
    shows_data = collect_artist_shows(active_slugs)
    t3 = time.time()
    logger.info("Phase 2 완료: %d artists in %.0fs", len(shows_data), t3 - t2)

    with open(DATA_DIR / "artsy_kr_artist_shows.json", "w", encoding="utf-8") as f:
        json.dump(shows_data, f, ensure_ascii=False, indent=2)

    # Phase 3: 통합 작가 프로필 (shows 병합)
    logger.info("--- Phase 3: 통합 프로필 생성 ---")
    for a in artists_list:
        slug = a["slug"]
        if slug in shows_data:
            sd = shows_data[slug]
            a["bio"] = sd.get("bio", "")
            a["solo_count"] = sd["solo_count"]
            a["group_count"] = sd["group_count"]
            a["fair_count"] = sd["fair_count"]
            a["total_shows"] = sd["total_shows"]
        else:
            a["bio"] = ""
            a["solo_count"] = 0
            a["group_count"] = 0
            a["fair_count"] = 0
            a["total_shows"] = 0

    with open(DATA_DIR / "artsy_kr_artists_full.json", "w", encoding="utf-8") as f:
        json.dump(artists_list, f, ensure_ascii=False, indent=2)

    # 작가 CSV
    artist_fields = [
        "slug", "name", "nationality", "birth_year", "gender",
        "total_works", "for_sale_works", "followers", "is_p1",
        "solo_count", "group_count", "fair_count", "total_shows",
        "formatted",
    ]
    with open(DATA_DIR / "artsy_kr_artists_full.csv", "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=artist_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(artists_list)

    # ─── 요약 ───
    priced = [w for w in artworks if w["price_krw"]]
    has_dims = [w for w in artworks if w["width_cm"]]
    galleries = set(w["gallery_name"] for w in artworks if w["gallery_name"])
    categories = {}
    for w in artworks:
        c = w.get("category") or "기타"
        categories[c] = categories.get(c, 0) + 1

    currencies = {}
    for w in priced:
        c = w["price_currency"]
        currencies[c] = currencies.get(c, 0) + 1

    has_shows = [a for a in artists_list if a.get("total_shows", 0) > 0]

    print(f"\n{'='*70}")
    print("Artsy 한국 작가 전체 수집 완료")
    print(f"{'='*70}")
    print(f"\n  [작품]")
    print(f"  총 작품: {len(artworks):,}건")
    print(f"  가격 있음: {len(priced):,}건 ({len(priced)*100//len(artworks) if artworks else 0}%)")
    print(f"  크기 있음: {len(has_dims):,}건 ({len(has_dims)*100//len(artworks) if artworks else 0}%)")
    print(f"  갤러리 수: {len(galleries):,}개")

    print(f"\n  [통화 분포]")
    for c, n in sorted(currencies.items(), key=lambda x: -x[1]):
        print(f"    {c}: {n:,}건")

    if priced:
        prices_krw = sorted(w["price_krw"] for w in priced)
        mid = prices_krw[len(prices_krw) // 2]
        print(f"\n  [가격 (KRW 환산)]")
        print(f"    최소: {prices_krw[0]:,}원")
        print(f"    중앙: {mid:,}원")
        print(f"    최대: {prices_krw[-1]:,}원")

    print(f"\n  [카테고리]")
    for c, n in sorted(categories.items(), key=lambda x: -x[1])[:8]:
        print(f"    {c}: {n:,}건")

    print(f"\n  [작가]")
    print(f"  고유 작가: {len(artists_list):,}명")
    print(f"  전시 이력 있음: {len(has_shows):,}명")
    print(f"  P1 작가: {sum(1 for a in artists_list if a.get('is_p1')):,}명")

    print(f"\n  [상위 작가 — 작품수]")
    for a in artists_list[:10]:
        shows = a.get("total_shows", 0)
        print(f"    {a['name']} ({a.get('formatted','')}) "
              f"| works:{a['total_works']} sale:{a['for_sale_works']} "
              f"| shows:{shows} followers:{a['followers']}")

    print(f"\n  [수집 시간]")
    print(f"    작품: {t1-t0:.0f}초")
    print(f"    전시: {t3-t2:.0f}초")
    print(f"    총: {t3-t0:.0f}초")

    print(f"\n  [저장 파일]")
    print(f"    data/artsy_kr_artworks.json / .csv")
    print(f"    data/artsy_kr_artists_full.json / .csv")
    print(f"    data/artsy_kr_artist_shows.json")


if __name__ == "__main__":
    main()
