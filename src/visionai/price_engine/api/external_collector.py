"""외부 소스 수집 오케스트레이터."""
from __future__ import annotations

import logging
import time

from . import artsy_client, saatchi_client, web_searcher

logger = logging.getLogger(__name__)

# 인메모리 캐시 (서버 수명 동안)
_cache: dict[str, dict | None] = {}


def collect(artist_name: str, skip: bool = False) -> tuple[dict | None, list[str]]:
    """외부 소스에서 작가 프로필 수집.

    Returns:
        (profile_dict | None, sources_used: list[str])
    """
    if skip:
        return None, []

    # 인메모리 캐시 확인
    cache_key = artist_name.lower().strip()
    if cache_key in _cache:
        cached = _cache[cache_key]
        sources = [cached["source"]] if cached else []
        logger.debug("Cache hit: %s", artist_name)
        return cached, sources

    t0 = time.time()
    sources_used = []
    profile = None

    # 1. Artsy (우선순위 1)
    try:
        artsy_profile = artsy_client.lookup(artist_name)
        if artsy_profile:
            profile = artsy_profile
            sources_used.append("artsy")
    except Exception as e:
        logger.warning("Artsy lookup failed: %s", e)

    # 2. Saatchi (Artsy에서 못 찾았거나 생년 부족 시)
    if not profile or not profile.get("birth_year"):
        try:
            saatchi_profile = saatchi_client.lookup(artist_name)
            if saatchi_profile:
                if not profile:
                    profile = saatchi_profile
                    sources_used.append("saatchi")
                else:
                    # Artsy 프로필에 Saatchi 정보 보강
                    if not profile.get("birth_year") and saatchi_profile.get("birth_year"):
                        profile["birth_year"] = saatchi_profile["birth_year"]
                        profile["birth_year_from_source"] = saatchi_profile["birth_year"]
                    if saatchi_profile.get("profile_completeness", 0) > profile.get("profile_completeness", 0):
                        profile["profile_completeness"] = saatchi_profile["profile_completeness"]
                    sources_used.append("saatchi")
        except Exception as e:
            logger.warning("Saatchi lookup failed: %s", e)

    # 3. 웹검색 (생년 미확보 시만, Phase 3)
    if profile and not profile.get("birth_year"):
        try:
            birth = web_searcher.search_birth_year(artist_name)
            if birth:
                profile["birth_year"] = birth
                profile["birth_year_from_source"] = birth
                sources_used.append("web")
        except Exception as e:
            logger.warning("Web search failed: %s", e)
    elif not profile:
        # 아무것도 못 찾은 경우에도 생년만이라도
        try:
            birth = web_searcher.search_birth_year(artist_name)
            if birth:
                profile = {
                    "source": "web",
                    "birth_year": birth,
                    "birth_year_from_source": birth,
                    "total_works": 0,
                    "followers": 0,
                    "solo_count": 0,
                    "group_count": 0,
                    "fair_count": 0,
                    "career_stage": 1,
                    "career_age": 0,
                    "for_sale_ratio": 1.0,
                    "profile_completeness": 1,
                    "gallery_name": "Unknown",
                    "gallery_type": "Unknown",
                    "gallery_tier": 4,
                }
                sources_used.append("web")
        except Exception as e:
            logger.warning("Web search failed: %s", e)

    elapsed = time.time() - t0
    logger.info(
        "External collect: %s → %s (%.1fs, sources=%s)",
        artist_name,
        "found" if profile else "not found",
        elapsed,
        sources_used,
    )

    # 인메모리 캐시 저장
    _cache[cache_key] = profile

    return profile, sources_used


def clear_cache() -> None:
    """인메모리 캐시 클리어."""
    _cache.clear()
