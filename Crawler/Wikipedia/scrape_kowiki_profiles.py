"""한국어 위키백과 작가 프로필 수집.

MediaWiki API로 한글명 검색 → extract에서 생몰년 추출.
Wikidata ID도 수집하여 추후 SPARQL 보충 가능.

1초 간격, 100명마다 중간 저장, 이어하기 지원.

Usage:
    PYTHONPATH=src python3 Crawler/Wikipedia/scrape_kowiki_profiles.py
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
OUTPUT_PATH = ROOT / "data" / "kowiki_profiles.csv"

API_URL = "https://ko.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "VisionAI-ArtistProfile/1.0 (art-price-research)"}
DELAY = 1.0  # 요청 간격 (초)

# 생몰년 패턴: 첫 번째 4자리 ~ 두 번째 4자리 (괄호 무관)
BIRTH_DEATH_RE = re.compile(
    r"(\d{4})\s*년?"
    r".*?"
    r"[~\-–—]"
    r".*?"
    r"(\d{4})\s*년?"
)

# 생년만 패턴: 4자리년 뒤에 ~ 만 있고 몰년 없음
BIRTH_ONLY_RE = re.compile(
    r"(\d{4})\s*년"
    r"[^~\-–—]*?"
    r"[~\-–—]"
    r"\s*[)\uff09]"
)

# 단순 4자리 연도 (첫 문장)
YEAR_ONLY_RE = re.compile(r"(\d{4})\s*년")


def extract_years(text: str) -> tuple[int, int]:
    """Extract에서 생년/몰년 추출.

    위키백과 인물 기사 첫 줄: "이름(漢字, 1914년 2월 21일 ~ 1965년 5월 6일)은 ..."
    """
    # 첫 번째 닫는 괄호까지만 (인물 정보 괄호)
    # 중첩 괄호 처리: 가장 바깥 괄호를 찾음
    paren_start = text.find("(")
    if paren_start == -1:
        paren_start = text.find("（")
    if paren_start == -1:
        return -1, -1

    # 중첩 괄호를 고려하여 매칭되는 닫는 괄호 찾기
    depth = 0
    paren_end = -1
    for i in range(paren_start, min(len(text), paren_start + 200)):
        if text[i] in "（(":
            depth += 1
        elif text[i] in "）)":
            depth -= 1
            if depth == 0:
                paren_end = i
                break

    if paren_end == -1:
        bio_text = text[paren_start:paren_start + 200]
    else:
        bio_text = text[paren_start:paren_end + 1]

    # 연도 추출: 괄호 내에서 "YYYY년" 패턴 모두 찾기
    years = [int(m.group(1)) for m in re.finditer(r"(\d{4})\s*년", bio_text)]
    # 범위 필터: 1800~2030
    years = [y for y in years if 1800 <= y <= 2030]

    if not years:
        return -1, -1

    # ~ 또는 - 구분자 확인
    has_sep = bool(re.search(r"[~\-–—]", bio_text))

    if len(years) >= 2 and has_sep:
        by, dy = years[0], years[-1]
        if by < dy:
            return by, dy
        return by, -1
    elif len(years) == 1:
        return years[0], -1

    return years[0], -1


def is_artist_page(extract: str) -> bool:
    """위키 extract가 미술 작가 관련인지 판단."""
    art_keywords = [
        "화가", "미술가", "조각가", "판화가", "설치미술", "서양화",
        "동양화", "수묵", "추상", "미술", "작품", "전시", "캔버스",
        "artist", "painter", "sculptor", "printmaker",
    ]
    lower = extract[:500].lower()
    return any(kw in lower for kw in art_keywords)


def fetch_wiki_profile(name: str) -> dict | None:
    """한국어 위키백과에서 작가 프로필 조회."""
    try:
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
            },
            headers=HEADERS,
            timeout=10,
        )
        if resp.status_code != 200:
            return None

        pages = resp.json().get("query", {}).get("pages", {})
        for pid, page in pages.items():
            if pid == "-1":
                return None  # Page not found
            extract = page.get("extract", "")
            if not extract:
                return None

            wikidata_id = page.get("pageprops", {}).get("wikibase_item", "")
            birth_year, death_year = extract_years(extract)

            return {
                "title": page.get("title", ""),
                "wikidata_id": wikidata_id,
                "extract": extract[:200],
                "birth_year": birth_year,
                "death_year": death_year,
                "is_artist": is_artist_page(extract),
            }
    except Exception:
        return None
    return None


def main() -> None:
    """대량 수집."""
    profiles = pd.read_csv(PROFILES_PATH, encoding="utf-8-sig")

    # 대상: 한국 작가 + birth_year 미수집
    targets = profiles[
        (profiles["artist_nationality"] == "KR")
        & (profiles["birth_year"] <= 0)
    ].copy()

    # 영문 이름만 있는 경우 제외 (한국어 위키 검색 불가)
    targets = targets[
        targets["name_kor"].apply(
            lambda x: bool(re.search(r"[\uac00-\ud7a3]{2,}", str(x)))
        )
    ]
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
        if name_kor in existing:
            continue

        checked += 1
        data = fetch_wiki_profile(name_kor)

        if data and data["birth_year"] > 0:
            results.append({
                "name_kor": name_kor,
                "wiki_title": data["title"],
                "wikidata_id": data["wikidata_id"],
                "birth_year": data["birth_year"],
                "death_year": data["death_year"],
                "is_artist": data["is_artist"],
                "extract_preview": data["extract"][:100],
            })
            found += 1
            if data["is_artist"]:
                logger.info("  [%d] %s → %d~%d (artist)",
                            checked, name_kor, data["birth_year"], data["death_year"])

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
                profiles.loc[mask, "profile_source"] = "kowiki"
                profiles.loc[mask, "match_confidence"] = 0.90
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
