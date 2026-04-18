"""Artsy 작가 프로필 대량 스크래핑.

GraphQL API로 영문명 기반 slug 검색 → 생년/몰년/국적 수집.
1.5초 간격, 100명마다 중간 저장.

Usage:
    PYTHONPATH=src python3 scripts/collectors/scrape_artsy_profiles_bulk.py
"""
from __future__ import annotations

import logging
import re
import time
from pathlib import Path

import pandas as pd
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent.parent
PROFILES_PATH = ROOT / "data" / "artist_profiles.csv"
OUTPUT_PATH = ROOT / "data" / "artsy_new_profiles.csv"

ARTSY_GQL = "https://metaphysics-cdn.artsy.net/v2"
DELAY = 1.5  # 요청 간격 (초)

QUERY = """
query ArtistProfile($slug: String!) {
  artist(id: $slug) {
    name
    nationality
    birthday
    deathday
    counts { artworks forSaleArtworks }
  }
}
"""


def name_to_slug(name: str) -> str:
    """영문명 → Artsy slug."""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9\s]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s


def fetch_profile(slug: str) -> dict | None:
    """Artsy GraphQL로 작가 프로필 조회."""
    try:
        resp = requests.post(
            ARTSY_GQL,
            json={"query": QUERY, "variables": {"slug": slug}},
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        return resp.json().get("data", {}).get("artist")
    except Exception:
        return None


def main() -> None:
    """대량 스크래핑."""
    profiles = pd.read_csv(PROFILES_PATH, encoding="utf-8-sig")

    # 미수집 + 영문명 있는 작가
    targets = profiles[
        (profiles["profile_source"] == "none")
        & (profiles["name_eng"].str.contains(r"[a-zA-Z]{2,}", na=False))
    ].copy()
    logger.info("대상: %d명 (지연: %.1f초)", len(targets), DELAY)

    # 이미 수집된 결과 로드 (이어하기)
    existing = set()
    results = []
    if OUTPUT_PATH.exists():
        prev = pd.read_csv(OUTPUT_PATH, encoding="utf-8-sig")
        results = prev.to_dict("records")
        existing = set(prev["name_kor"])
        logger.info("기존 수집: %d명 (이어서 진행)", len(existing))

    found = 0
    checked = 0

    for _, row in targets.iterrows():
        name_kor = row["name_kor"]
        name_eng = str(row["name_eng"]).strip()

        if name_kor in existing or not name_eng or name_eng == "unknown":
            continue

        slug = name_to_slug(name_eng)
        if len(slug) < 3:
            continue

        checked += 1
        data = fetch_profile(slug)

        if data and data.get("name"):
            birth = str(data.get("birthday", ""))[:4]
            death = str(data.get("deathday", ""))[:4]
            results.append({
                "name_kor": name_kor,
                "name_eng": name_eng,
                "slug": slug,
                "artsy_name": data.get("name", ""),
                "nationality": data.get("nationality", ""),
                "birth_year": int(birth) if birth.isdigit() else -1,
                "death_year": int(death) if death.isdigit() else -1,
                "artworks_count": data.get("counts", {}).get("artworks", 0),
            })
            found += 1

        # 100명마다 중간 저장 + 로그
        if checked % 100 == 0:
            pd.DataFrame(results).to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
            logger.info("  [%d checked, %d found] saved", checked, found)

        time.sleep(DELAY)

    # 최종 저장
    res_df = pd.DataFrame(results)
    res_df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    logger.info("=== 완료: %d found / %d checked ===", found, checked)

    # 프로필 업데이트
    updated = 0
    for _, r in res_df.iterrows():
        mask = profiles["name_kor"] == r["name_kor"]
        if mask.any() and profiles.loc[mask, "birth_year"].iloc[0] == -1:
            if r["birth_year"] > 0:
                profiles.loc[mask, "birth_year"] = r["birth_year"]
                profiles.loc[mask, "profile_source"] = "artsy_scrape"
                profiles.loc[mask, "match_confidence"] = 0.85
                updated += 1
            if r["death_year"] > 0:
                profiles.loc[mask, "death_year"] = r["death_year"]
                profiles.loc[mask, "is_deceased"] = True

    profiles.to_csv(PROFILES_PATH, index=False, encoding="utf-8-sig")
    has_birth = (profiles["birth_year"] > 0).sum()
    logger.info("프로필 업데이트: +%d명, 총 생년: %d명 (%.1f%%)",
                updated, has_birth, has_birth / len(profiles) * 100)


if __name__ == "__main__":
    main()
