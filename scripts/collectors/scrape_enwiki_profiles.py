"""영문 위키백과 작가 프로필 수집.

MediaWiki API로 영문명 검색 → extract에서 생몰년 추출.
해외 작가(WS) + 한국 작가 중 영문명만 있는 경우 대상.

1초 간격, 100명마다 중간 저장, 이어하기 지원.

Usage:
    PYTHONPATH=src python3 scripts/collectors/scrape_enwiki_profiles.py
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
OUTPUT_PATH = ROOT / "data" / "enwiki_profiles.csv"

API_URL = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "VisionAI-ArtistProfile/1.0 (art-price-research)"}
DELAY = 1.0

# English Wikipedia birth/death patterns
# "John Doe (born 1 January 1900, died 5 March 1970)"
# "John Doe (1900–1970)"
# "John Doe (born 1900)"
BORN_DIED_RE = re.compile(
    r"[(\uff08]"
    r"[^)]*?"
    r"(?:born|b\.)\s*"
    r"(?:\d{1,2}\s+\w+\s+)?"
    r"(\d{4})"
    r"[^)]*?"
    r"(?:died|d\.)\s*"
    r"(?:\d{1,2}\s+\w+\s+)?"
    r"(\d{4})"
    r"[^)]*?"
    r"[)\uff09]",
    re.IGNORECASE,
)

YEAR_RANGE_RE = re.compile(
    r"[(\uff08][^)]*?"
    r"(?:\w+\s+\d{1,2},?\s+)?"
    r"(\d{4})\s*"
    r"[–\-—~]\s*"
    r"(?:\w+\s+\d{1,2},?\s+)?"
    r"(\d{4})"
    r"[^)]*?"
    r"[)\uff09]"
)

BORN_ONLY_RE = re.compile(
    r"[(\uff08][^)]*?(?:born|b\.)\s*(?:\d{1,2}\s+\w+\s+)?(\d{4})[^)]*?[)\uff09]",
    re.IGNORECASE,
)


def extract_years_en(text: str) -> tuple[int, int]:
    """English extract에서 생몰년 추출.

    전략: 첫 200자에서 모든 4자리 연도를 찾고, 1800~2030 범위 필터 후
    첫 번째=생년, 두 번째=몰년 (사이에 –/- 구분자가 있으면).
    """
    intro = text[:300]

    # 모든 4자리 연도 추출
    all_years = [int(m.group(1)) for m in re.finditer(r"(\d{4})", intro)]
    valid_years = [y for y in all_years if 1800 <= y <= 2030]

    if not valid_years:
        return -1, -1

    # 구분자 (– - — ~) 확인
    has_sep = bool(re.search(r"[–\-—~]", intro))

    if len(valid_years) >= 2 and has_sep:
        by, dy = valid_years[0], valid_years[1]
        if by < dy:
            return by, dy
        return by, -1

    # "born" 키워드 확인
    if re.search(r"(?:born|b\.)", intro, re.IGNORECASE):
        return valid_years[0], -1

    # 단일 연도
    return valid_years[0], -1


def is_artist_page_en(extract: str) -> bool:
    """영문 extract가 미술 작가 관련인지 판단."""
    art_keywords = [
        "painter", "artist", "sculptor", "printmaker", "photographer",
        "installation", "contemporary art", "fine art", "visual art",
        "abstract", "oil on canvas", "watercolor", "lithograph",
        "mixed media", "ceramics", "gallery", "exhibition",
    ]
    lower = extract[:500].lower()
    return any(kw in lower for kw in art_keywords)


def fetch_enwiki_profile(name: str) -> dict | None:
    """영문 위키백과에서 작가 프로필 조회."""
    try:
        # Step 1: Search for the page
        resp = requests.get(
            API_URL,
            params={
                "action": "query",
                "titles": name,
                "prop": "pageprops|extracts",
                "ppprop": "wikibase_item",
                "exintro": True,
                "explaintext": True,
                "format": "json",
                "redirects": 1,
            },
            headers=HEADERS,
            timeout=10,
        )
        if resp.status_code != 200:
            return None

        pages = resp.json().get("query", {}).get("pages", {})
        for pid, page in pages.items():
            if pid == "-1":
                # Try opensearch as fallback
                return _search_fallback(name)

            extract = page.get("extract", "")
            if not extract:
                return None

            wikidata_id = page.get("pageprops", {}).get("wikibase_item", "")
            birth_year, death_year = extract_years_en(extract)

            return {
                "title": page.get("title", ""),
                "wikidata_id": wikidata_id,
                "extract": extract[:200],
                "birth_year": birth_year,
                "death_year": death_year,
                "is_artist": is_artist_page_en(extract),
            }
    except Exception:
        return None
    return None


def _search_fallback(name: str) -> dict | None:
    """Direct title match 실패 시 opensearch로 재시도."""
    try:
        resp = requests.get(
            API_URL,
            params={
                "action": "opensearch",
                "search": name,
                "limit": 3,
                "format": "json",
            },
            headers=HEADERS,
            timeout=10,
        )
        if resp.status_code != 200:
            return None

        data = resp.json()
        if len(data) < 2 or not data[1]:
            return None

        # 첫 번째 결과로 재시도
        best_title = data[1][0]
        resp2 = requests.get(
            API_URL,
            params={
                "action": "query",
                "titles": best_title,
                "prop": "pageprops|extracts",
                "ppprop": "wikibase_item",
                "exintro": True,
                "explaintext": True,
                "format": "json",
            },
            headers=HEADERS,
            timeout=10,
        )
        if resp2.status_code != 200:
            return None

        pages = resp2.json().get("query", {}).get("pages", {})
        for pid, page in pages.items():
            if pid == "-1":
                return None
            extract = page.get("extract", "")
            if not extract:
                return None

            wikidata_id = page.get("pageprops", {}).get("wikibase_item", "")
            birth_year, death_year = extract_years_en(extract)

            return {
                "title": page.get("title", ""),
                "wikidata_id": wikidata_id,
                "extract": extract[:200],
                "birth_year": birth_year,
                "death_year": death_year,
                "is_artist": is_artist_page_en(extract),
            }
    except Exception:
        return None
    return None


def main() -> None:
    """대량 수집."""
    profiles = pd.read_csv(PROFILES_PATH, encoding="utf-8-sig")

    # 대상: birth_year 미수집 + 영문명 있는 작가
    targets = profiles[
        (profiles["birth_year"] <= 0)
        & (profiles["name_eng"].apply(
            lambda x: bool(re.search(r"[a-zA-Z]{3,}", str(x)))
        ))
    ].copy()
    logger.info("대상: %d명 (지연: %.1f초)", len(targets), DELAY)

    # 이어하기
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

        checked += 1
        data = fetch_enwiki_profile(name_eng)

        if data and data["birth_year"] > 0:
            results.append({
                "name_kor": name_kor,
                "name_eng": name_eng,
                "wiki_title": data["title"],
                "wikidata_id": data["wikidata_id"],
                "birth_year": data["birth_year"],
                "death_year": data["death_year"],
                "is_artist": data["is_artist"],
                "extract_preview": data["extract"][:100],
            })
            found += 1
            if data["is_artist"]:
                logger.info("  [%d] %s (%s) → %d~%d (artist)",
                            checked, name_eng, name_kor,
                            data["birth_year"], data["death_year"])

        # 100명마다 중간 저장
        if checked % 100 == 0:
            pd.DataFrame(results).to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
            logger.info("  [%d checked, %d found] saved", checked, found)

        time.sleep(DELAY)

    # 최종 저장
    res_df = pd.DataFrame(results)
    res_df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    logger.info("=== 완료: %d found / %d checked ===", found, checked)

    # 아티스트 확인된 것만 프로필 업데이트
    artist_results = res_df[res_df["is_artist"] == True] if len(res_df) > 0 else res_df  # noqa: E712
    updated = 0
    for _, r in artist_results.iterrows():
        mask = profiles["name_kor"] == r["name_kor"]
        if mask.any() and profiles.loc[mask, "birth_year"].iloc[0] <= 0:
            if r["birth_year"] > 0:
                profiles.loc[mask, "birth_year"] = int(r["birth_year"])
                profiles.loc[mask, "profile_source"] = "enwiki"
                profiles.loc[mask, "match_confidence"] = 0.85
                updated += 1
            if r["death_year"] > 0:
                profiles.loc[mask, "death_year"] = int(r["death_year"])
                profiles.loc[mask, "is_deceased"] = True

    profiles.to_csv(PROFILES_PATH, index=False, encoding="utf-8-sig")
    has_birth = (profiles["birth_year"] > 0).sum()
    logger.info(
        "프로필 업데이트: +%d명, 총 생년: %d명 (%.1f%%)",
        updated, has_birth, has_birth / len(profiles) * 100,
    )


if __name__ == "__main__":
    main()
