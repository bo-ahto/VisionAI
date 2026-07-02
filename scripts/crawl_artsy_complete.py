"""Artsy 한국 작가 31K 완전 수집.

API 10K offset 제한을 카테고리+재료 분할로 우회.
기존 수집된 artwork_id는 중복 제거.
"""
from __future__ import annotations

import base64
import csv
import json
import logging
import re
import argparse
import time
import urllib.request
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_BASELINE_CSV: Path | None = None
GRAPHQL_URL = "https://metaphysics-cdn.artsy.net/v2"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}

FX = {"USD": 1380, "GBP": 1780, "EUR": 1530, "HKD": 178}

QUERY = """query Collect($input: FilterArtworksInput) {
  viewer {
    artworksConnection(input: $input) {
      counts { total }
      pageInfo { hasNextPage endCursor }
      edges {
        node {
          internalID slug href title date medium category
          dimensions { in cm }
          saleMessage priceListedDisplay availability
          collectingInstitution series artistNames
          attributionClass { name }
          mediumType { filterGene { name } }
          image(includeAll: false) { url(version: ["large"]) aspectRatio }
          artists(shallow: true) {
            internalID slug name formattedNationalityAndBirthday
            nationality birthday gender hometown location
            counts { artworks forSaleArtworks follows }
            targetSupply { isP1 }
          }
          partner(shallow: true) { name href type cities }
          sale { isAuction isClosed name }
          certificateOfAuthenticity { details }
          signatureInfo { details }
          framed { details }
        }
      }
    }
  }
}"""

SHOW_QUERY_TPL = """query ArtistShows {
  artist(id: "%SLUG%") {
    name slug formattedNationalityAndBirthday
    biographyBlurb { text }
    counts { artworks forSaleArtworks follows }
    showsConnection(first: 100, sort: END_AT_DESC) {
      totalCount
      edges { node { name kind startAt endAt city partner { ... on Partner { name type } } } }
    }
  }
}"""


def parse_price(s: str | None) -> dict:
    r = {"price_raw": s or "", "price_currency": None, "price_amount": None, "price_krw": None}
    if not s:
        return r
    for cur, pat, fk in [
        ("KRW", r"(?:KRW|₩)\s*₩?\s*([\d,]+)", None),
        ("USD", r"US?\$\s*([\d,]+)", "USD"),
        ("GBP", r"£\s*([\d,]+)", "GBP"),
        ("EUR", r"€\s*([\d,]+)", "EUR"),
        ("HKD", r"HK\$\s*([\d,]+)", "HKD"),
    ]:
        m = re.search(pat, s)
        if m:
            a = int(m.group(1).replace(",", ""))
            r.update(
                price_currency=cur,
                price_amount=a,
                price_krw=a if cur == "KRW" else int(a * FX[fk]),
            )
            return r
    return r


def parse_dims(d: str | None) -> dict:
    r = {"width_cm": None, "height_cm": None, "depth_cm": None}
    if not d:
        return r
    nums = re.findall(r"([\d.]+)", d)
    if len(nums) >= 2:
        r["width_cm"], r["height_cm"] = float(nums[0]), float(nums[1])
    if len(nums) >= 3:
        r["depth_cm"] = float(nums[2])
    m = re.search(r"diameter\s*([\d.]+)", d, re.IGNORECASE)
    if m:
        r["width_cm"] = r["height_cm"] = float(m.group(1))
    return r


def parse_birth(b: str | None) -> int | None:
    if not b:
        return None
    m = re.match(r"(\d{4})", b)
    return int(m.group(1)) if m else None


def gql(query: str, variables: dict | None = None) -> dict:
    body = {"query": query}
    if variables:
        body["variables"] = variables
    payload = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(GRAPHQL_URL, data=payload, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def node_to_work(n: dict) -> dict:
    price = parse_price(n.get("saleMessage"))
    dr = n.get("dimensions") or {}
    dims = parse_dims(dr.get("cm"))
    a = n["artists"][0] if n.get("artists") else {}
    p = n.get("partner") or {}
    return {
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
        "collecting_institution": n.get("collectingInstitution", ""),
        "certificate": (n.get("certificateOfAuthenticity") or {}).get("details", ""),
        "signature": (n.get("signatureInfo") or {}).get("details", ""),
        "framed": (n.get("framed") or {}).get("details", ""),
        "image_url": (n.get("image") or {}).get("url", ""),
        "image_aspect_ratio": (n.get("image") or {}).get("aspectRatio"),
        "dimensions_cm": dr.get("cm", ""),
        "dimensions_in": dr.get("in", ""),
        **dims,
        **price,
        "artist_slug": a.get("slug", ""),
        "artist_name": a.get("name", ""),
        "artist_id": a.get("internalID", ""),
        "artist_nationality": a.get("nationality", ""),
        "artist_birthday": a.get("birthday", ""),
        "artist_birth_year": parse_birth(a.get("birthday")),
        "artist_gender": a.get("gender", ""),
        "artist_hometown": a.get("hometown", ""),
        "artist_location": a.get("location", ""),
        "artist_total_works": a.get("counts", {}).get("artworks", 0),
        "artist_for_sale": a.get("counts", {}).get("forSaleArtworks", 0),
        "artist_followers": a.get("counts", {}).get("follows", 0),
        "artist_is_p1": a.get("targetSupply", {}).get("isP1", False),
        "gallery_name": p.get("name", ""),
        "gallery_type": p.get("type", ""),
        "gallery_cities": ", ".join(p.get("cities") or []),
        "gallery_href": p.get("href", ""),
        "is_auction": (n.get("sale") or {}).get("isAuction", False),
        "auction_name": (n.get("sale") or {}).get("name", ""),
    }


def load_existing_artwork_ids(path: Path | None, source_family: str = "artsy") -> set[str]:
    """증분 수집에서 건너뛸 기존 artwork_id를 읽는다."""
    if not path or not path.exists():
        return set()
    ids: set[str] = set()
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row.get("source_family") or "").strip().lower() != source_family:
                continue
            artwork_id = (row.get("source_artwork_id") or "").strip()
            if artwork_id:
                ids.add(artwork_id)
    return ids


def fetch_batch(
    extra_input: dict,
    label: str,
    seen_ids: set[str],
    existing_ids: set[str],
) -> tuple[list[dict], int, int]:
    """하나의 필터 조합으로 최대 10K 수집."""
    works = []
    cursor = None
    skipped_existing = 0
    skipped_duplicate = 0

    for page in range(1, 101):
        inp = {
            "sort": "-decayed_merch",
            "artistNationalities": ["South Korean", "Korean"],
            "locationCities": ["Seoul, South Korea", "Busan, South Korea"],
            "first": 100,
            **extra_input,
        }
        if cursor:
            inp["after"] = cursor

        try:
            data = gql(QUERY, {"input": inp})
            conn = data["data"]["viewer"]["artworksConnection"]
        except Exception as e:
            logger.warning("[%s] page %d error: %s", label, page, e)
            time.sleep(5)
            try:
                data = gql(QUERY, {"input": inp})
                conn = data["data"]["viewer"]["artworksConnection"]
            except Exception:
                break

        if not conn or not conn.get("edges"):
            break

        edges = conn["edges"]
        cursor = conn["pageInfo"]["endCursor"]
        has_next = conn["pageInfo"]["hasNextPage"]

        for edge in edges:
            n = edge["node"]
            aid = n["internalID"]
            if aid in existing_ids:
                skipped_existing += 1
                continue
            if aid in seen_ids:
                skipped_duplicate += 1
                continue
            seen_ids.add(aid)
            works.append(node_to_work(n))

        if not has_next:
            break
        time.sleep(1.0)

    return works, skipped_existing, skipped_duplicate


def parse_args() -> argparse.Namespace:
    """수집 실행 옵션을 해석한다."""
    parser = argparse.ArgumentParser(description="Artsy 한국 작가 작품을 수집합니다.")
    parser.add_argument(
        "--baseline-csv",
        type=Path,
        default=DEFAULT_BASELINE_CSV,
        help="증분 수집에서 이미 수집된 작품을 건너뛰기 위한 1차 정리 CSV.",
    )
    parser.add_argument(
        "--full-refresh",
        action="store_true",
        help="baseline을 무시하고 전체 재수집합니다.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logger.info("=== Artsy 31K 완전 수집 시작 ===")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    seen_ids: set = set()
    existing_ids = set() if args.full_refresh else load_existing_artwork_ids(args.baseline_csv)
    all_works: list[dict] = []
    total_skipped_existing = 0
    total_skipped_duplicate = 0

    if args.full_refresh:
        logger.info("수집 모드: full-refresh")
    else:
        logger.info("수집 모드: incremental, baseline existing Artsy IDs=%d", len(existing_ids))

    # 배치 정의: 각 배치가 10K 이하가 되도록 분할
    # Non-painting categories (각각 < 10K)
    batches = [
        ({"additionalGeneIDs": ["sculpture"]}, "sculpture"),
        ({"additionalGeneIDs": ["photography"]}, "photography"),
        ({"additionalGeneIDs": ["print"]}, "print"),
        ({"additionalGeneIDs": ["drawing"]}, "drawing"),
        ({"additionalGeneIDs": ["mixed-media"]}, "mixed-media"),
        ({"additionalGeneIDs": ["installation"]}, "installation"),
        ({"additionalGeneIDs": ["work-on-paper"]}, "work-on-paper"),
        ({"additionalGeneIDs": ["video-film-animation"]}, "video"),
        ({"additionalGeneIDs": ["textile-arts"]}, "textile"),
        ({"additionalGeneIDs": ["design"]}, "design"),
        # Painting 21K → 재료별 분할 (각 < 10K)
        ({"additionalGeneIDs": ["painting"], "materialsTerms": ["oil"]}, "painting-oil"),
        ({"additionalGeneIDs": ["painting"], "materialsTerms": ["acrylic"]}, "painting-acrylic"),
        ({"additionalGeneIDs": ["painting"], "materialsTerms": ["ink"]}, "painting-ink"),
        ({"additionalGeneIDs": ["painting"], "materialsTerms": ["gouache"]}, "painting-gouache"),
        ({"additionalGeneIDs": ["painting"], "materialsTerms": ["watercolor"]}, "painting-watercolor"),
        ({"additionalGeneIDs": ["painting"], "materialsTerms": ["pastel"]}, "painting-pastel"),
        ({"additionalGeneIDs": ["painting"], "materialsTerms": ["lacquer"]}, "painting-lacquer"),
        ({"additionalGeneIDs": ["painting"], "materialsTerms": ["pigment"]}, "painting-pigment"),
        ({"additionalGeneIDs": ["painting"], "materialsTerms": ["silk"]}, "painting-silk"),
        # Painting 나머지 (재료 필터 없이, 다른 정렬)
        ({"additionalGeneIDs": ["painting"], "sort": "-published_at"}, "painting-newest"),
        ({"additionalGeneIDs": ["painting"], "sort": "published_at"}, "painting-oldest"),
        ({"additionalGeneIDs": ["painting"], "sort": "-prices"}, "painting-expensive"),
        ({"additionalGeneIDs": ["painting"], "sort": "prices"}, "painting-cheapest"),
        # 전체 (정렬 변형으로 추가 수집)
        ({"sort": "-published_at"}, "all-newest"),
        ({"sort": "published_at"}, "all-oldest"),
    ]

    t0 = time.time()

    for extra_input, label in batches:
        # sort가 extra_input에 있으면 기본 sort 제거
        batch_works, skipped_existing, skipped_duplicate = fetch_batch(
            extra_input,
            label,
            seen_ids,
            existing_ids,
        )
        all_works.extend(batch_works)
        total_skipped_existing += skipped_existing
        total_skipped_duplicate += skipped_duplicate
        logger.info(
            "[%s] +%d new, skipped_existing=%d, duplicate_in_run=%d (total new: %d)",
            label,
            len(batch_works),
            skipped_existing,
            skipped_duplicate,
            len(all_works),
        )

    t1 = time.time()
    logger.info("Phase 1 완료: %d works in %.0fs", len(all_works), t1 - t0)

    # 작가 추출
    artists: dict[str, dict] = {}
    for w in all_works:
        slug = w.get("artist_slug", "")
        if slug and slug not in artists:
            artists[slug] = {
                "slug": slug,
                "name": w["artist_name"],
                "internalID": w.get("artist_id", ""),
                "nationality": w.get("artist_nationality", ""),
                "birth_year": w.get("artist_birth_year"),
                "gender": w.get("artist_gender", ""),
                "total_works": w.get("artist_total_works", 0),
                "for_sale_works": w.get("artist_for_sale", 0),
                "followers": w.get("artist_followers", 0),
                "is_p1": w.get("artist_is_p1", False),
                "formatted": "",
            }
    artists_list = sorted(artists.values(), key=lambda x: -x["total_works"])

    # 저장 - 작품
    with open(DATA_DIR / "artsy_kr_artworks.json", "w", encoding="utf-8") as f:
        json.dump(all_works, f, ensure_ascii=False, indent=2)

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
        writer.writerows(all_works)

    # 저장 - 작가 기본
    with open(DATA_DIR / "artsy_kr_artists.json", "w", encoding="utf-8") as f:
        json.dump(artists_list, f, ensure_ascii=False, indent=2)

    logger.info("Saved artworks: %d, artists: %d", len(all_works), len(artists_list))

    # Phase 2: 작가 전시 이력 (works 5건+)
    logger.info("--- Phase 2: 작가 전시 이력 ---")
    active_slugs = [a["slug"] for a in artists_list if a["total_works"] >= 5]
    logger.info("대상: %d명", len(active_slugs))
    t2 = time.time()

    shows_data: dict = {}
    for i, slug in enumerate(active_slugs):
        try:
            q = SHOW_QUERY_TPL.replace("%SLUG%", slug)
            data = gql(q)
            ar = data["data"].get("artist")
            if not ar:
                continue
            sc = ar.get("showsConnection") or {}
            show_list = []
            for edge in sc.get("edges", []):
                nd = edge["node"]
                show_list.append({
                    "name": nd.get("name", ""),
                    "kind": nd.get("kind", ""),
                    "start_at": (nd.get("startAt") or "")[:10],
                    "city": nd.get("city", ""),
                    "partner": (nd.get("partner") or {}).get("name", ""),
                })
            solo = sum(1 for s in show_list if s["kind"] == "solo")
            group = sum(1 for s in show_list if s["kind"] == "group")
            fair = sum(1 for s in show_list if s["kind"] == "fair")
            shows_data[slug] = {
                "name": ar["name"],
                "formatted": ar.get("formattedNationalityAndBirthday", ""),
                "bio": (ar.get("biographyBlurb") or {}).get("text", ""),
                "followers": (ar.get("counts") or {}).get("follows", 0),
                "total_shows": sc.get("totalCount", 0),
                "solo_count": solo,
                "group_count": group,
                "fair_count": fair,
                "shows": show_list,
            }
        except Exception as e:
            logger.warning("[%d] %s: %s", i, slug, e)
        if (i + 1) % 100 == 0:
            logger.info("Shows: %d/%d", i + 1, len(active_slugs))
        time.sleep(0.5)

    t3 = time.time()
    logger.info("Phase 2 완료: %d artists in %.0fs", len(shows_data), t3 - t2)

    with open(DATA_DIR / "artsy_kr_artist_shows.json", "w", encoding="utf-8") as f:
        json.dump(shows_data, f, ensure_ascii=False, indent=2)

    # Phase 3: 통합 프로필
    for a in artists_list:
        sd = shows_data.get(a["slug"], {})
        a["bio"] = sd.get("bio", "")
        a["formatted"] = sd.get("formatted", a.get("formatted", ""))
        a["solo_count"] = sd.get("solo_count", 0)
        a["group_count"] = sd.get("group_count", 0)
        a["fair_count"] = sd.get("fair_count", 0)
        a["total_shows"] = sd.get("total_shows", 0)

    with open(DATA_DIR / "artsy_kr_artists_full.json", "w", encoding="utf-8") as f:
        json.dump(artists_list, f, ensure_ascii=False, indent=2)

    af = [
        "slug", "name", "nationality", "birth_year", "gender",
        "total_works", "for_sale_works", "followers", "is_p1",
        "solo_count", "group_count", "fair_count", "total_shows", "formatted",
    ]
    with open(DATA_DIR / "artsy_kr_artists_full.csv", "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=af, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(artists_list)

    # 요약
    priced = sum(1 for w in all_works if w.get("price_krw"))
    has_dims = sum(1 for w in all_works if w.get("width_cm"))
    model_ok = sum(1 for w in all_works
                   if w.get("price_krw") and w.get("width_cm") and w.get("artist_birth_year"))
    unique_a = len(artists_list)
    has_shows = sum(1 for a in artists_list if a.get("total_shows", 0) > 0)

    cats = {}
    for w in all_works:
        c = w.get("category") or "기타"
        cats[c] = cats.get(c, 0) + 1
    curs = {}
    for w in all_works:
        c = w.get("price_currency")
        if c:
            curs[c] = curs.get(c, 0) + 1

    prices_krw = sorted(w["price_krw"] for w in all_works if w.get("price_krw"))

    print(f"\n{'='*70}")
    print("Artsy 한국 작가 전체 수집 최종 결과")
    print(f"{'='*70}")
    print(f"\n  [작품]")
    print(f"  신규 작품: {len(all_works):,}건")
    print(f"  baseline 기존 작품 skip: {total_skipped_existing:,}건")
    print(f"  수집 중 중복 skip: {total_skipped_duplicate:,}건")
    denom = max(len(all_works), 1)
    print(f"  가격 있음: {priced:,}건 ({priced*100//denom}%)")
    print(f"  크기 있음: {has_dims:,}건 ({has_dims*100//denom}%)")
    print(f"  모델 학습 가능 (가격+크기+생년): {model_ok:,}건")

    print(f"\n  [통화]")
    for c, n in sorted(curs.items(), key=lambda x: -x[1]):
        print(f"    {c}: {n:,}건")

    if prices_krw:
        mid = prices_krw[len(prices_krw) // 2]
        print(f"\n  [가격 KRW 환산]")
        print(f"    최소: {prices_krw[0]:,}원")
        print(f"    중앙: {mid:,}원")
        print(f"    최대: {prices_krw[-1]:,}원")

    print(f"\n  [카테고리]")
    for c, n in sorted(cats.items(), key=lambda x: -x[1])[:10]:
        print(f"    {c}: {n:,}건")

    print(f"\n  [작가]")
    print(f"  고유 작가: {unique_a:,}명")
    print(f"  전시 이력: {has_shows:,}명")
    print(f"  P1: {sum(1 for a in artists_list if a.get('is_p1')):,}명")

    print(f"\n  [시간]")
    print(f"    작품: {t1 - t0:.0f}초")
    print(f"    전시: {t3 - t2:.0f}초")
    print(f"    총: {t3 - t0:.0f}초")


if __name__ == "__main__":
    main()
