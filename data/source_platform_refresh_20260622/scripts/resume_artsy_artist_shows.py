#!/usr/bin/env python3
"""
Artsy 전시 이력 수집을 이어서 수행한다.

사용 상황:
  - run_artsy_latest_from_platform.py 실행 중 네트워크 오류가 발생했거나
  - artsy_kr_artist_shows.json에 일부 작가만 저장된 경우

입력:
  - artsy_latest/artsy_kr_artists.json
  - artsy_latest/artsy_kr_artist_shows.json

출력:
  - artsy_latest/artsy_kr_artist_shows.json
  - artsy_latest/artsy_kr_artists_full.json
  - artsy_latest/artsy_kr_artists_full.csv
  - artsy_latest/artsy_artist_shows_resume_summary.json

처리:
  - total_works >= 5인 작가를 전시 이력 대상자로 본다.
  - 이미 전시 이력이 있는 작가는 건너뛴다.
  - 누락된 작가만 재시도한다.
  - 성공할 때마다 JSON을 저장해 다시 끊겨도 이어서 실행할 수 있게 한다.
"""

from __future__ import annotations

import csv
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PACKAGE_DIR = Path(__file__).resolve().parents[1]
ARTSY_DIR = PACKAGE_DIR / "artsy_latest"
ARTISTS_PATH = ARTSY_DIR / "artsy_kr_artists.json"
SHOWS_PATH = ARTSY_DIR / "artsy_kr_artist_shows.json"
ARTISTS_FULL_JSON = ARTSY_DIR / "artsy_kr_artists_full.json"
ARTISTS_FULL_CSV = ARTSY_DIR / "artsy_kr_artists_full.csv"
SUMMARY_PATH = ARTSY_DIR / "artsy_artist_shows_resume_summary.json"

GRAPHQL_URL = "https://metaphysics-cdn.artsy.net/v2"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}

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


def gql(query: str) -> dict[str, Any]:
    body = json.dumps({"query": query}).encode("utf-8")
    req = urllib.request.Request(GRAPHQL_URL, data=body, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_show_profile(slug: str) -> dict[str, Any] | None:
    q = SHOW_QUERY_TPL.replace("%SLUG%", slug)
    data = gql(q)
    artist = data.get("data", {}).get("artist")
    if not artist:
        return None

    shows_conn = artist.get("showsConnection") or {}
    show_list = []
    for edge in shows_conn.get("edges", []):
        node = edge.get("node") or {}
        partner = node.get("partner") or {}
        show_list.append(
            {
                "name": node.get("name", ""),
                "kind": node.get("kind", ""),
                "start_at": (node.get("startAt") or "")[:10],
                "city": node.get("city", ""),
                "partner": partner.get("name", ""),
            }
        )

    solo_count = sum(1 for item in show_list if item["kind"] == "solo")
    group_count = sum(1 for item in show_list if item["kind"] == "group")
    fair_count = sum(1 for item in show_list if item["kind"] == "fair")

    return {
        "name": artist.get("name", ""),
        "formatted": artist.get("formattedNationalityAndBirthday", ""),
        "bio": (artist.get("biographyBlurb") or {}).get("text", ""),
        "followers": (artist.get("counts") or {}).get("follows", 0),
        "total_shows": shows_conn.get("totalCount", 0),
        "solo_count": solo_count,
        "group_count": group_count,
        "fair_count": fair_count,
        "shows": show_list,
    }


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def rebuild_artist_full(artists: list[dict[str, Any]], shows_data: dict[str, Any]) -> None:
    for artist in artists:
        slug = artist.get("slug", "")
        show = shows_data.get(slug, {})
        artist["bio"] = show.get("bio", "")
        artist["formatted"] = show.get("formatted", artist.get("formatted", ""))
        artist["solo_count"] = show.get("solo_count", 0)
        artist["group_count"] = show.get("group_count", 0)
        artist["fair_count"] = show.get("fair_count", 0)
        artist["total_shows"] = show.get("total_shows", 0)

    write_json(ARTISTS_FULL_JSON, artists)

    fields = [
        "slug",
        "name",
        "nationality",
        "birth_year",
        "gender",
        "total_works",
        "for_sale_works",
        "followers",
        "is_p1",
        "solo_count",
        "group_count",
        "fair_count",
        "total_shows",
        "formatted",
    ]
    with ARTISTS_FULL_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(artists)


def main() -> None:
    artists = load_json(ARTISTS_PATH, [])
    shows_data = load_json(SHOWS_PATH, {})
    if not artists:
        raise FileNotFoundError(f"작가 기본 파일이 없습니다: {ARTISTS_PATH}")

    active_slugs = [a["slug"] for a in artists if int(a.get("total_works") or 0) >= 5]
    missing = [slug for slug in active_slugs if slug not in shows_data]
    failures: list[dict[str, str]] = []

    print(f"active artists: {len(active_slugs):,}")
    print(f"already collected: {len(shows_data):,}")
    print(f"missing: {len(missing):,}")

    for idx, slug in enumerate(missing, start=1):
        last_error = ""
        profile = None
        for attempt in range(1, 4):
            try:
                profile = fetch_show_profile(slug)
                break
            except Exception as exc:  # 네트워크 오류는 다음 attempt에서 재시도한다.
                last_error = f"{type(exc).__name__}: {exc}"
                wait = 3 * attempt
                print(f"[{idx}/{len(missing)}] retry {attempt}/3 {slug}: {last_error}")
                time.sleep(wait)

        if profile is not None:
            shows_data[slug] = profile
            write_json(SHOWS_PATH, shows_data)
        else:
            failures.append({"slug": slug, "error": last_error})

        if idx % 25 == 0 or idx == len(missing):
            print(f"progress: {idx}/{len(missing)} collected_total={len(shows_data):,}")

        time.sleep(0.5)

    rebuild_artist_full(artists, shows_data)

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "active_artist_count": len(active_slugs),
        "collected_artist_show_count": len(shows_data),
        "remaining_missing_count": len([slug for slug in active_slugs if slug not in shows_data]),
        "failure_count": len(failures),
        "failures": failures,
        "outputs": {
            "shows_json": str(SHOWS_PATH.relative_to(PACKAGE_DIR)),
            "artists_full_json": str(ARTISTS_FULL_JSON.relative_to(PACKAGE_DIR)),
            "artists_full_csv": str(ARTISTS_FULL_CSV.relative_to(PACKAGE_DIR)),
        },
    }
    write_json(SUMMARY_PATH, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
