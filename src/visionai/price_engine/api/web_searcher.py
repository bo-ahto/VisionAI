"""웹검색으로 작가 생년 보강 (Phase 3).

DuckDuckGo (키 불필요) 기본 사용. Naver/Google API 키가 있으면 우선 사용.
"""
from __future__ import annotations

import json
import logging
import os
import re
import urllib.request
import urllib.parse

logger = logging.getLogger(__name__)

_NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
_NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")

# 미술 관련 키워드 (검증용)
ART_KEYWORDS = {"전시", "갤러리", "작가", "painting", "exhibition", "gallery", "artist",
                "미술", "개인전", "단체전", "아트", "art", "작품", "화가", "유화", "수채"}
EXCLUDE_KEYWORDS = {"배우", "가수", "영화", "드라마", "actor", "singer", "movie",
                    "방송", "연예", "스포츠", "선수"}


def _ddg_search(query: str) -> list[dict]:
    """DuckDuckGo 검색 (키 불필요)."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            return [{"title": r.get("title", ""), "description": r.get("body", ""),
                      "link": r.get("href", "")} for r in results]
    except Exception as e:
        logger.warning("DuckDuckGo search error: %s", e)
        return []


def _naver_search(query: str) -> list[dict]:
    """Naver Search API로 검색 (키 필요)."""
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


def _extract_birth_years(text: str) -> list[int]:
    """텍스트에서 생년 후보 추출."""
    years = []
    patterns = [
        r"(\d{4})년\s*생",
        r"(\d{4})년\s*출생",
        r"(\d{4})년\s*\d{1,2}월",  # 1913년 4월
        r"(?:born|b\.)\s*(?:in\s+)?(?:on\s+)?(?:\w+\s+\d{1,2},?\s+)?(19\d{2}|20[01]\d)",
        r"Born.*?(19\d{2}|20[01]\d)",
        r"\((?:金煥基,\s*)?(\d{4})년",  # (金煥基, 1913년
        r"\((\d{4})\s*[-~∼]\s*\)",  # (1985-)
        r"\((\d{4})\s*[-~∼]\s*\d{4}\)",  # (1985-2020)
        r",\s*(19\d{2})\s*[-~∼]",  # , 1913~1974
        r"(\d{4})\s*[-~∼]\s*\d{4}\)\s*[은는이가]",  # 1913~1974)는
    ]
    for pat in patterns:
        for m in re.finditer(pat, text, re.I):
            y = int(m.group(1))
            if 1900 <= y <= 2005:
                years.append(y)
    return list(set(years))


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
    # 검색어: 작가 + 회화 한정어
    query = f'"{artist_name}" 작가 화가 생년'

    # 검색 실행 (Naver API 우선, 없으면 DuckDuckGo)
    if _NAVER_CLIENT_ID:
        results = _naver_search(query)
    else:
        results = _ddg_search(query)

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
