"""Saatchi Art 한국 작가 작품 + 프로필 수집기.

Constructor.io API로 작품 10,000건 수집 후,
고유 작가의 프로필 페이지(__NEXT_DATA__)에서 교육/전시 이력 수집.
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

# 이 저장소의 루트가 곧 스크립트 위치 (flat) — data/ 는 sibling
DATA_DIR = Path(__file__).resolve().parent / "data"
DELAY = 0.5

CNSTRC_BASE = (
    "https://ac.cnstrc.com/browse/group_id/all"
    "?c=ciojs-client-2.64.2"
    "&key=key_cn3mctZ73MD3U2jM"
    "&i=visionai"
    "&s=1&us=US&us=desktop&us=guest"
    "&filters%5Boriginal_availability_status%5D=avail"
    "&filters%5Bcountry%5D=south%20korea"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
}


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": HEADERS["User-Agent"],
        "Accept": "text/html",
    })
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


# ─── Phase 1: 작품 수집 (Constructor.io API) ───

def collect_artworks() -> tuple[list[dict], dict[int, dict]]:
    """한국 작가 작품 10,000건 수집."""
    all_works: list[dict] = []
    artists: dict[int, dict] = {}  # artist_id → basic info

    for page in range(1, 101):
        url = f"{CNSTRC_BASE}&page={page}&num_results_per_page=100"
        try:
            data = fetch_json(url)
        except Exception as e:
            logger.warning("Page %d failed: %s", page, e)
            time.sleep(5)
            continue

        results = data.get("response", {}).get("results", [])
        if not results:
            logger.info("Page %d: empty — done", page)
            break

        for r in results:
            d = r.get("data", {})
            geo_prices = d.get("geo_prices", {})
            price_usd_cents = geo_prices.get("US", 0)
            price_usd = price_usd_cents / 100 if price_usd_cents else 0

            work = {
                "artwork_id": d.get("id"),
                "title": r.get("value", ""),
                "price_usd": price_usd,
                "price_krw": int(price_usd * 1380) if price_usd else 0,
                "width_cm": d.get("width"),
                "height_cm": d.get("height"),
                "depth_cm": d.get("depth"),
                "materials": ", ".join(d.get("materials", [])),
                "mediums": ", ".join(d.get("mediums", [])),
                "category": d.get("artwork_category", ""),
                "subject": d.get("subject", ""),
                "styles": ", ".join(d.get("styles", [])),
                "orientation": d.get("orientation", ""),
                "size_bin": d.get("size_bin", ""),
                "is_framed": d.get("is_framed", False),
                "color": d.get("color", ""),
                "image_url": d.get("image_url", ""),
                "artwork_url": f"https://www.saatchiart.com{d.get('url', '')}",
                "artist_id": d.get("artist_id"),
                "artist_first_name": d.get("artist_first_name", ""),
                "artist_last_name": d.get("artist_last_name", ""),
                "artist_gender": d.get("artist_gender", ""),
                "artist_ethnicity": d.get("artist_ethnicity", ""),
                "artist_city": d.get("city", ""),
                "country": d.get("country", ""),
            }
            all_works.append(work)

            # 작가 기본 정보
            aid = d.get("artist_id")
            if aid and aid not in artists:
                artists[aid] = {
                    "artist_id": aid,
                    "first_name": d.get("artist_first_name", ""),
                    "last_name": d.get("artist_last_name", ""),
                    "gender": d.get("artist_gender", ""),
                    "ethnicity": d.get("artist_ethnicity", ""),
                    "city": d.get("city", ""),
                    "country": d.get("country", ""),
                    "profile_url": d.get("artist_profile_url", ""),
                    "recognition": d.get("artist_recognition", []),
                }

        logger.info("Page %d: +%d works (total %d, artists %d)",
                     page, len(results), len(all_works), len(artists))
        time.sleep(DELAY)

    return all_works, artists


# ─── Phase 2: 작가 프로필 수집 (__NEXT_DATA__) ───

def collect_artist_profiles(artists: dict[int, dict]) -> dict[int, dict]:
    """작가 프로필 페이지에서 교육/전시/바이오 수집."""
    profiles: dict[int, dict] = {}
    total = len(artists)

    for i, (aid, info) in enumerate(artists.items()):
        profile_path = info.get("profile_url", "")
        if not profile_path:
            profile_path = f"/account/profile/{aid}"

        url = f"https://www.saatchiart.com{profile_path}"
        try:
            html = fetch_html(url)
            m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
            if not m:
                continue

            data = json.loads(m.group(1))
            page_data = data.get("props", {}).get("pageProps", {}).get("initialState", {}).get("page", {}).get("data", {})
            ad = page_data.get("accountData", {})

            if not ad:
                continue

            about = ad.get("aboutArtist", {})

            profile = {
                "artist_id": aid,
                "display_name": f"{ad.get('firstName', '')} {ad.get('lastName', '')}".strip(),
                "username": ad.get("userName", ""),
                "country": ad.get("country", ""),
                "state": ad.get("state", ""),
                "followers": ad.get("followersTotal", 0),
                "total_artworks": ad.get("artworksTotal", 0),
                "joined_date": ad.get("joinedDate", ""),
                "badges": [b.get("title", "") for b in ad.get("badges", [])],
                "bio": about.get("about", ""),
                "education": about.get("education", ""),
                "exhibitions": about.get("exhibitions", ""),
                "events": about.get("events", ""),
                "social_links": ad.get("socialLinks", {}),
            }
            profiles[aid] = profile

        except Exception as e:
            logger.warning("[%d/%d] %s: %s", i + 1, total, aid, e)

        if (i + 1) % 50 == 0:
            logger.info("Profiles: %d/%d", i + 1, total)

        time.sleep(DELAY)

    return profiles


# ─── Main ───

def main() -> None:
    logger.info("=== Saatchi Art 한국 작가 수집 시작 ===")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Phase 1
    logger.info("--- Phase 1: 작품 수집 ---")
    t0 = time.time()
    artworks, artists = collect_artworks()
    t1 = time.time()
    logger.info("Phase 1 완료: %d works, %d artists in %.0fs", len(artworks), len(artists), t1 - t0)

    # 저장
    with open(DATA_DIR / "saatchi_kr_artworks.json", "w", encoding="utf-8") as f:
        json.dump(artworks, f, ensure_ascii=False, indent=2)

    csv_fields = [
        "artwork_id", "title", "price_usd", "price_krw",
        "width_cm", "height_cm", "depth_cm", "materials", "mediums",
        "category", "subject", "styles", "orientation", "size_bin",
        "artist_id", "artist_first_name", "artist_last_name",
        "artist_gender", "artist_city", "country",
        "image_url", "artwork_url",
    ]
    with open(DATA_DIR / "saatchi_kr_artworks.csv", "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(artworks)

    # Phase 2
    logger.info("--- Phase 2: 작가 프로필 수집 (%d명) ---", len(artists))
    t2 = time.time()
    profiles = collect_artist_profiles(artists)
    t3 = time.time()
    logger.info("Phase 2 완료: %d profiles in %.0fs", len(profiles), t3 - t2)

    # 프로필 저장
    profiles_list = sorted(profiles.values(), key=lambda x: -x.get("total_artworks", 0))
    with open(DATA_DIR / "saatchi_kr_artists.json", "w", encoding="utf-8") as f:
        json.dump(profiles_list, f, ensure_ascii=False, indent=2)

    # 요약
    priced = [w for w in artworks if w.get("price_krw", 0) > 0]
    has_bio = sum(1 for p in profiles_list if p.get("bio"))
    has_edu = sum(1 for p in profiles_list if p.get("education"))
    has_exh = sum(1 for p in profiles_list if p.get("exhibitions"))

    print(f"\n{'='*70}")
    print("Saatchi Art 한국 작가 수집 완료")
    print(f"{'='*70}")
    print(f"\n  [작품]")
    print(f"  총 작품: {len(artworks):,}건")
    print(f"  가격 있음: {len(priced):,}건")
    if priced:
        prices = sorted(w["price_krw"] for w in priced)
        print(f"  가격 범위: {prices[0]:,}~{prices[-1]:,}원")
        print(f"  가격 중앙: {prices[len(prices)//2]:,}원")

    print(f"\n  [작가]")
    print(f"  고유 작가: {len(artists):,}명")
    print(f"  프로필 수집: {len(profiles):,}명")
    print(f"  바이오: {has_bio}명")
    print(f"  교육: {has_edu}명")
    print(f"  전시: {has_exh}명")

    print(f"\n  [시간]")
    print(f"  작품: {t1-t0:.0f}초")
    print(f"  프로필: {t3-t2:.0f}초")
    print(f"  총: {t3-t0:.0f}초")

    print(f"\n  [저장]")
    print(f"  data/saatchi_kr_artworks.json / .csv")
    print(f"  data/saatchi_kr_artists.json")


if __name__ == "__main__":
    main()
