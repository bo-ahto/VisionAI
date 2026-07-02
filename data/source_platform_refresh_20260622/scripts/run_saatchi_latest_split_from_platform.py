#!/usr/bin/env python3
"""
Saatchi 원본 플랫폼에서 10,000건 제한을 피해서 더 많은 작품을 수집한다.

기존 run_saatchi_latest_from_platform.py와 같은 원본 API를 사용하되,
단일 검색 결과가 10,000건에서 잘리는 문제를 피하기 위해 size_bin별로 나눠 받는다.
기본값은 1차 정리 CSV를 baseline으로 읽어 기존 작품을 건너뛰는 증분 수집이다.

수집 조건:
  - original_availability_status = avail
  - country = south korea
  - size_bin = oversized / large / medium / small

출력:
  - saatchi_latest_split/saatchi_kr_artworks.json
  - saatchi_latest_split/saatchi_kr_artworks.csv
  - saatchi_latest_split/saatchi_kr_artists.json
  - saatchi_latest_split/saatchi_split_collection_summary.json

주의:
  - 가격을 새로 계산하지 않고 API의 geo_prices US 값을 KRW 환산만 한다.
  - 중복 artwork_id는 제거한다.
  - 전체 재수집이 필요하면 --full-refresh 옵션을 사용한다.
  - 기존 data/ 폴더는 덮어쓰지 않는다.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PACKAGE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PACKAGE_DIR / "saatchi_latest_split"
COLLECTION_MODE = "incremental_after_stage1_baseline"
DELAY = 0.5

CNSTRC_BASE = (
    "https://ac.cnstrc.com/browse/group_id/all"
    "?c=ciojs-client-2.64.2"
    "&key=key_cn3mctZ73MD3U2jM"
    "&i=visionai"
    "&s=1&us=US&us=desktop&us=guest"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
}

SIZE_BINS = ["oversized", "large", "medium", "small"]


def default_baseline_csv() -> Path:
    """1차 정리 산출물 중 존재하는 baseline CSV를 찾는다."""
    output_dir = PACKAGE_DIR / "csv_collected_20260622/03_outputs"
    candidates = [
        output_dir / "standardized_artworks_merged_deduped.csv",
        output_dir / "standardized_artworks_merged_deduped_0622.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


DEFAULT_BASELINE_CSV = default_baseline_csv()


def clean_text(value: Any) -> str:
    """비교용 문자열을 정리한다."""
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"", "nan", "none", "null", "<na>"}:
        return ""
    return text


def load_existing_artwork_keys(path: Path | None, source_family: str = "saatchi") -> tuple[set[str], set[str]]:
    """증분 수집에서 건너뛸 기존 artwork_id와 artwork_url을 읽는다."""
    if not path or not path.exists():
        return set(), set()

    ids: set[str] = set()
    urls: set[str] = set()
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if clean_text(row.get("source_family")).lower() != source_family:
                continue
            artwork_id = clean_text(row.get("source_artwork_id"))
            artwork_url = clean_text(row.get("artwork_url")).lower().rstrip("/")
            if artwork_id:
                ids.add(artwork_id)
            if artwork_url:
                urls.add(artwork_url)
    return ids, urls


def build_url(filters: dict[str, str], page: int, per_page: int = 100) -> str:
    query = "".join(
        "&" + urllib.parse.urlencode({f"filters[{key}]": value})
        for key, value in filters.items()
    )
    return f"{CNSTRC_BASE}{query}&page={page}&num_results_per_page={per_page}"


def fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_html(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": HEADERS["User-Agent"],
            "Accept": "text/html",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def result_to_work(result: dict[str, Any], split_name: str) -> tuple[dict[str, Any], dict[str, Any] | None]:
    data = result.get("data", {})
    geo_prices = data.get("geo_prices", {}) or {}
    price_usd_cents = geo_prices.get("US", 0) or 0
    price_usd = price_usd_cents / 100 if price_usd_cents else 0

    work = {
        "artwork_id": data.get("id"),
        "title": result.get("value", ""),
        "price_usd": price_usd,
        "price_krw": int(price_usd * 1380) if price_usd else 0,
        "width_cm": data.get("width"),
        "height_cm": data.get("height"),
        "depth_cm": data.get("depth"),
        "materials": ", ".join(data.get("materials", []) or []),
        "mediums": ", ".join(data.get("mediums", []) or []),
        "category": data.get("artwork_category", ""),
        "subject": data.get("subject", ""),
        "styles": ", ".join(data.get("styles", []) or []),
        "orientation": data.get("orientation", ""),
        "size_bin": data.get("size_bin", ""),
        "is_framed": data.get("is_framed", False),
        "color": data.get("color", ""),
        "image_url": data.get("image_url", ""),
        "artwork_url": f"https://www.saatchiart.com{data.get('url', '')}",
        "artist_id": data.get("artist_id"),
        "artist_first_name": data.get("artist_first_name", ""),
        "artist_last_name": data.get("artist_last_name", ""),
        "artist_gender": data.get("artist_gender", ""),
        "artist_ethnicity": data.get("artist_ethnicity", ""),
        "artist_city": data.get("city", ""),
        "country": data.get("country", ""),
        "collection_split": split_name,
    }

    artist = None
    artist_id = data.get("artist_id")
    if artist_id:
        artist = {
            "artist_id": artist_id,
            "first_name": data.get("artist_first_name", ""),
            "last_name": data.get("artist_last_name", ""),
            "gender": data.get("artist_gender", ""),
            "ethnicity": data.get("artist_ethnicity", ""),
            "city": data.get("city", ""),
            "country": data.get("country", ""),
            "profile_url": data.get("artist_profile_url", ""),
            "recognition": data.get("artist_recognition", []),
        }

    return work, artist


def collect_artworks_by_size(
    existing_artwork_ids: set[str],
    existing_artwork_urls: set[str],
) -> tuple[list[dict[str, Any]], dict[int, dict[str, Any]], dict[str, Any]]:
    seen_artwork_ids: set[str] = set()
    artworks: list[dict[str, Any]] = []
    artists: dict[int, dict[str, Any]] = {}
    split_summary: dict[str, Any] = {}
    total_existing_skipped = 0

    for size_bin in SIZE_BINS:
        filters = {
            "original_availability_status": "avail",
            "country": "south korea",
            "size_bin": size_bin,
        }
        split_new = 0
        split_seen = 0
        split_existing = 0
        expected_count = None

        for page in range(1, 101):
            url = build_url(filters, page=page)
            try:
                payload = fetch_json(url)
            except Exception as exc:
                logger.warning("[%s] page %d failed: %s", size_bin, page, exc)
                time.sleep(5)
                payload = fetch_json(url)

            response = payload.get("response", {})
            if expected_count is None:
                expected_count = (
                    response.get("result_sources", {})
                    .get("token_match", {})
                    .get("count", response.get("total_num_results"))
                )

            results = response.get("results", []) or []
            if not results:
                break

            for result in results:
                work, artist = result_to_work(result, size_bin)
                artwork_id = str(work.get("artwork_id") or "")
                artwork_url = clean_text(work.get("artwork_url")).lower().rstrip("/")
                if not artwork_id:
                    continue
                if artwork_id in existing_artwork_ids or artwork_url in existing_artwork_urls:
                    split_existing += 1
                    total_existing_skipped += 1
                    continue
                if artwork_id in seen_artwork_ids:
                    split_seen += 1
                    continue
                seen_artwork_ids.add(artwork_id)
                artworks.append(work)
                split_new += 1

                if artist:
                    artist_id = int(artist["artist_id"])
                    artists.setdefault(artist_id, artist)

            logger.info(
                "[%s] page %d: +%d new, total=%d, artists=%d",
                size_bin,
                page,
                split_new,
                len(artworks),
                len(artists),
            )

            if len(results) < 100:
                break
            time.sleep(DELAY)

        split_summary[size_bin] = {
            "expected_count": int(expected_count or 0),
            "new_unique_artworks": split_new,
            "existing_baseline_skipped": split_existing,
            "duplicate_artworks": split_seen,
        }

    split_summary["_total_existing_baseline_skipped"] = total_existing_skipped
    return artworks, artists, split_summary


def collect_artist_profiles(artists: dict[int, dict[str, Any]]) -> dict[int, dict[str, Any]]:
    import re

    profiles: dict[int, dict[str, Any]] = {}
    total = len(artists)

    for idx, (artist_id, info) in enumerate(artists.items(), start=1):
        profile_path = info.get("profile_url") or f"/account/profile/{artist_id}"
        url = f"https://www.saatchiart.com{profile_path}"
        try:
            html = fetch_html(url)
            match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
            if not match:
                continue

            payload = json.loads(match.group(1))
            page_data = (
                payload.get("props", {})
                .get("pageProps", {})
                .get("initialState", {})
                .get("page", {})
                .get("data", {})
            )
            account = page_data.get("accountData", {})
            about = account.get("aboutArtist", {}) if account else {}
            if not account:
                continue

            profiles[artist_id] = {
                "artist_id": artist_id,
                "display_name": f"{account.get('firstName', '')} {account.get('lastName', '')}".strip(),
                "username": account.get("userName", ""),
                "country": account.get("country", ""),
                "state": account.get("state", ""),
                "followers": account.get("followersTotal", 0),
                "total_artworks": account.get("artworksTotal", 0),
                "joined_date": account.get("joinedDate", ""),
                "badges": [badge.get("title", "") for badge in account.get("badges", [])],
                "bio": about.get("about", ""),
                "education": about.get("education", ""),
                "exhibitions": about.get("exhibitions", ""),
                "events": about.get("events", ""),
                "social_links": account.get("socialLinks", {}),
            }
        except Exception as exc:
            logger.warning("[%d/%d] artist %s failed: %s", idx, total, artist_id, exc)

        if idx % 50 == 0:
            logger.info("profiles: %d/%d", idx, total)
        time.sleep(DELAY)

    return profiles


def write_outputs(
    artworks: list[dict[str, Any]],
    artists: dict[int, dict[str, Any]],
    profiles: dict[int, dict[str, Any]],
    split_summary: dict[str, Any],
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with (OUTPUT_DIR / "saatchi_kr_artworks.json").open("w", encoding="utf-8") as f:
        json.dump(artworks, f, ensure_ascii=False, indent=2)

    csv_fields = [
        "artwork_id",
        "title",
        "price_usd",
        "price_krw",
        "width_cm",
        "height_cm",
        "depth_cm",
        "materials",
        "mediums",
        "category",
        "subject",
        "styles",
        "orientation",
        "size_bin",
        "is_framed",
        "color",
        "image_url",
        "artwork_url",
        "artist_id",
        "artist_first_name",
        "artist_last_name",
        "artist_gender",
        "artist_ethnicity",
        "artist_city",
        "country",
        "collection_split",
    ]
    with (OUTPUT_DIR / "saatchi_kr_artworks.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(artworks)

    profiles_list = sorted(profiles.values(), key=lambda row: -int(row.get("total_artworks") or 0))
    with (OUTPUT_DIR / "saatchi_kr_artists.json").open("w", encoding="utf-8") as f:
        json.dump(profiles_list, f, ensure_ascii=False, indent=2)

    summary = {
        "method": "split_by_size_bin_to_avoid_constructor_10000_cap",
        "collection_mode": COLLECTION_MODE,
        "filters": {
            "original_availability_status": "avail",
            "country": "south korea",
            "size_bin": SIZE_BINS,
        },
        "split_summary": split_summary,
        "unique_artworks": len(artworks),
        "unique_artists_from_artworks": len(artists),
        "artist_profiles_collected": len(profiles),
        "outputs": {
            "artworks_json": "saatchi_kr_artworks.json",
            "artworks_csv": "saatchi_kr_artworks.csv",
            "artists_json": "saatchi_kr_artists.json",
        },
    }
    with (OUTPUT_DIR / "saatchi_split_collection_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(json.dumps(summary, ensure_ascii=False, indent=2))


def parse_args() -> argparse.Namespace:
    """명령행 옵션을 해석한다."""
    parser = argparse.ArgumentParser(description="Saatchi 한국 작가 작품을 size_bin별로 수집합니다.")
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
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="수집 결과 저장 폴더.",
    )
    return parser.parse_args()


def main() -> None:
    global OUTPUT_DIR, COLLECTION_MODE
    args = parse_args()
    OUTPUT_DIR = args.output_dir.resolve()

    logger.info("=== Saatchi split 수집 시작 ===")
    if args.full_refresh:
        existing_artwork_ids, existing_artwork_urls = set(), set()
        COLLECTION_MODE = "full_refresh"
        logger.info("수집 모드: full-refresh")
    else:
        existing_artwork_ids, existing_artwork_urls = load_existing_artwork_keys(args.baseline_csv)
        COLLECTION_MODE = "incremental_after_stage1_baseline"
        logger.info(
            "수집 모드: incremental, baseline existing Saatchi IDs=%d, URLs=%d",
            len(existing_artwork_ids),
            len(existing_artwork_urls),
        )

    t0 = time.time()
    artworks, artists, split_summary = collect_artworks_by_size(
        existing_artwork_ids,
        existing_artwork_urls,
    )
    t1 = time.time()
    logger.info("작품 수집 완료: %d works, %d artists, %.0fs", len(artworks), len(artists), t1 - t0)

    profiles = collect_artist_profiles(artists)
    t2 = time.time()
    logger.info("프로필 수집 완료: %d profiles, %.0fs", len(profiles), t2 - t1)

    write_outputs(artworks, artists, profiles, split_summary)
    logger.info("전체 완료: %.0fs", t2 - t0)


if __name__ == "__main__":
    main()
