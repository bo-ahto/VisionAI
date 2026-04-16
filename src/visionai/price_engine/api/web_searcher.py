"""웹검색으로 작가 생년 보강 (Phase 3).

WEB_SEARCH_API_KEY 환경변수가 없으면 스킵 (graceful degradation).
"""
from __future__ import annotations

import json
import logging
import os
import re
import urllib.request
import urllib.parse

logger = logging.getLogger(__name__)

# Naver Search API 또는 Google CSE
_API_KEY = os.getenv("WEB_SEARCH_API_KEY", "")
_API_TYPE = os.getenv("WEB_SEARCH_API_TYPE", "naver")  # naver | google
_NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
_NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")

# 미술 관련 키워드 (검증용)
ART_KEYWORDS = {"전시", "갤러리", "작가", "painting", "exhibition", "gallery", "artist",
                "미술", "개인전", "단체전", "아트", "art", "작품"}
EXCLUDE_KEYWORDS = {"배우", "가수", "영화", "드라마", "actor", "singer", "movie",
                    "드라마", "방송", "연예", "스포츠", "선수"}


def _naver_search(query: str) -> list[dict]:
    """Naver Search API로 검색."""
    if not _NAVER_CLIENT_ID:
        return []
    encoded = urllib.parse.quote(query)
    url = f"https://openapi.naver.com/v1/search/webkr.json?query={encoded}&display=5"
    req = urllib.request.Request(url, headers={
        "X-Naver-Client-Id": _NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": _NAVER_CLIENT_SECRET,
        "User-Agent": "VisionAI-API/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            return data.get("items", [])
    except Exception as e:
        logger.warning("Naver search error: %s", e)
        return []


def _google_search(query: str) -> list[dict]:
    """Google Custom Search API로 검색."""
    if not _API_KEY:
        return []
    encoded = urllib.parse.quote(query)
    cx = os.getenv("GOOGLE_CSE_ID", "")
    url = f"https://www.googleapis.com/customsearch/v1?key={_API_KEY}&cx={cx}&q={encoded}&num=5"
    req = urllib.request.Request(url, headers={"User-Agent": "VisionAI-API/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            return [{"title": i.get("title", ""), "description": i.get("snippet", ""),
                      "link": i.get("link", "")} for i in data.get("items", [])]
    except Exception as e:
        logger.warning("Google search error: %s", e)
        return []


def _extract_birth_years(text: str) -> list[int]:
    """텍스트에서 생년 후보 추출."""
    years = []
    patterns = [
        r"(\d{4})년\s*생",
        r"(\d{4})년\s*출생",
        r"(?:born|b\.)\s*(?:in\s+)?(19\d{2}|20[01]\d)",
        r"Born.*?(19\d{2}|20[01]\d)",
        r"\((\d{4})\s*[-~]\s*\)",  # (1985-)
        r"\((\d{4})\s*[-~]\s*\d{4}\)",  # (1985-2020)
    ]
    for pat in patterns:
        for m in re.finditer(pat, text, re.I):
            y = int(m.group(1))
            if 1930 <= y <= 2005:
                years.append(y)
    return years


def _has_art_context(text: str) -> bool:
    """텍스트에 미술 관련 키워드가 있는지."""
    lower = text.lower()
    has_art = any(kw in lower for kw in ART_KEYWORDS)
    has_exclude = any(kw in lower for kw in EXCLUDE_KEYWORDS)
    return has_art and not has_exclude


def search_birth_year(artist_name: str, medium: str = "") -> int | None:
    """웹검색으로 생년 추출. 동명이인 5단계 필터.

    Returns: birth_year if confident, None otherwise.
    """
    # API 키 없으면 스킵
    if not (_API_KEY or _NAVER_CLIENT_ID):
        logger.debug("Web search skipped: no API key")
        return None

    # 검색어: 작가 + 회화 한정어
    query = f'"{artist_name}" 작가 회화 생년'

    # 검색 실행
    if _API_TYPE == "naver" and _NAVER_CLIENT_ID:
        results = _naver_search(query)
    else:
        results = _google_search(query)

    if not results:
        return None

    # 동명이인 5단계 필터
    birth_years_by_domain: dict[str, list[int]] = {}

    for item in results:
        text = f"{item.get('title', '')} {item.get('description', '')}"

        # Step 2: 미술 키워드 확인 + 비미술 제외
        if not _has_art_context(text):
            continue

        # Step 3: 생년 추출 + 범위 검증 (1930~2005)
        years = _extract_birth_years(text)
        if not years:
            continue

        # 도메인 추출
        link = item.get("link", "")
        domain = link.split("/")[2] if link.count("/") >= 2 else "unknown"
        if domain not in birth_years_by_domain:
            birth_years_by_domain[domain] = []
        birth_years_by_domain[domain].extend(years)

    if not birth_years_by_domain:
        return None

    # Step 4: 2개 이상 독립 도메인에서 동일 생년
    all_years = []
    for years in birth_years_by_domain.values():
        all_years.extend(years)

    from collections import Counter
    year_counts = Counter(all_years)
    domains_per_year: dict[int, int] = {}
    for year in year_counts:
        domains_per_year[year] = sum(
            1 for d_years in birth_years_by_domain.values() if year in d_years
        )

    # Step 5: pass/fail — 2개 독립 도메인에서 동일 생년
    for year, domain_count in sorted(domains_per_year.items(), key=lambda x: -x[1]):
        if domain_count >= 2:
            logger.info("Web search: %s → birth_year=%d (%d domains)", artist_name, year, domain_count)
            return year

    # 2개 독립 도메인 미충족 → 미채택 (동명이인 리스크)
    logger.info("Web search: %s → no confident birth year (single domain only)", artist_name)
    return None
