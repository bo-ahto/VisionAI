"""Saatchi Art 실시간 작가 조회."""
from __future__ import annotations

import json
import logging
import re
import urllib.request
import urllib.parse

from rapidfuzz import fuzz

logger = logging.getLogger(__name__)

CNSTRC_KEY = "key_cn3mctZ73MD3U2jM"
HEADERS = {
    "User-Agent": "VisionAI-API/1.0",
    "Accept": "application/json",
}
HTML_HEADERS = {
    "User-Agent": "VisionAI-API/1.0",
    "Accept": "text/html",
}


def _fetch_json(url: str, timeout: int = 3) -> dict | None:
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        logger.warning("Saatchi JSON error: %s", e)
        return None


def _fetch_html(url: str, timeout: int = 5) -> str | None:
    req = urllib.request.Request(url, headers=HTML_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        logger.warning("Saatchi HTML error: %s", e)
        return None


def search_artist(name: str) -> dict | None:
    """Constructor.io autocomplete으로 작가 검색 → artist_id + 기본 정보."""
    encoded = urllib.parse.quote(name, safe="")
    url = (
        f"https://ac.cnstrc.com/autocomplete/{encoded}"
        f"?c=ciojs-client-2.64.2&key={CNSTRC_KEY}"
        f"&i=visionai&s=1"
    )
    data = _fetch_json(url)
    if not data:
        return None

    # sections에서 작가 관련 결과 찾기
    sections = data.get("sections", {})
    query_lower = name.lower().strip()

    # "Products" 섹션에서 artist 정보가 포함된 결과 찾기
    products = sections.get("Products", [])
    best = None
    best_score = 0

    for p in products[:10]:
        d = p.get("data", {})
        artist_name = f"{d.get('artist_first_name', '')} {d.get('artist_last_name', '')}".strip()
        if not artist_name:
            continue

        score = fuzz.ratio(query_lower, artist_name.lower())
        country = (d.get("country") or "").lower()
        if "korea" in country:
            score += 10

        if score > best_score:
            best_score = score
            best = {
                "artist_id": d.get("artist_id"),
                "name": artist_name,
                "country": d.get("country"),
            }

    if best and best_score >= 70 and best.get("artist_id"):
        return best

    return None


def get_artist_profile(artist_id: int) -> dict | None:
    """__NEXT_DATA__ 파싱으로 프로필 수집."""
    url = f"https://www.saatchiart.com/account/profile/{artist_id}"
    html = _fetch_html(url)
    if not html:
        return None

    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not m:
        return None

    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return None

    page_data = (
        data.get("props", {})
        .get("pageProps", {})
        .get("initialState", {})
        .get("page", {})
        .get("data", {})
    )
    ad = page_data.get("accountData", {})
    if not ad:
        return None

    about = ad.get("aboutArtist") or {}
    bio = (about.get("about") or "")[:500]
    edu = (about.get("education") or "")[:500]
    exh = (about.get("exhibitions") or "")[:500]

    # 생년 추출 (bio에서)
    birth_year = None
    if bio:
        bm = re.search(r"(?:born|b\.)\s*(?:in\s+)?(19\d{2}|20[01]\d)", bio, re.I)
        if bm:
            y = int(bm.group(1))
            if 1920 <= y <= 2005:
                birth_year = y

    followers = ad.get("followersTotal", 0) or 0
    total_artworks = ad.get("artworksTotal", 0) or 0
    completeness = sum([bool(bio), bool(edu), bool(exh)])

    return {
        "source": "saatchi",
        "birth_year": birth_year,
        "birth_year_from_source": birth_year,
        "nationality": ad.get("country"),
        "total_works": total_artworks,
        "followers": followers,
        "solo_count": 0,
        "group_count": 0,
        "fair_count": 0,
        "career_stage": 1,
        "career_age": 0,
        "for_sale_ratio": 1.0,
        "profile_completeness": completeness,
        "gallery_name": "Saatchi Art",
        "gallery_type": "Online Gallery",
        "gallery_tier": 3,
        "bio": bio,
        "education": edu,
        "exhibitions": exh,
    }


def lookup(artist_name: str) -> dict | None:
    """이름으로 검색 → 프로필 수집. 실패 시 None."""
    search_result = search_artist(artist_name)
    if not search_result:
        return None

    profile = get_artist_profile(search_result["artist_id"])
    if profile:
        logger.info("Saatchi: found %s (id=%s)", artist_name, search_result["artist_id"])
    return profile
