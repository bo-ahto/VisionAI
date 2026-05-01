"""v3.6 Phase 1 PR3: artwork-level year_made cache.

v3.5 step 2 §2.2 + step 3 §2.3 spec.

Cache 정책:
- key: artwork_id (artist_name 아님)
- TTL: 7 days (sold / page 제거 대응)
- capacity: 50,000 (saatchi raw 30,607 + 여유)
- eviction: LRU
- artwork_url → artwork_id alias cache (URL-only 요청 hit 보장)
- in-memory only (persistent DB cache 는 v3.6+ optimization)

Manual override write-through (v3.5 step 3 §2.3):
- valid manual year + artwork_id → cache write (source='manual_seed')
- 충돌 시 manual 우선 사용, cache 항목 그대로 유지

Routes (year_made_route):
- cache_hit: cache 에서 즉시 반환
- fetch_ok: detail page fetch + parse 성공
- fetch_fail: 5xx / network_error / timeout
- no_id: artwork_id + artwork_url 둘 다 None
- parse_invalid: fetch ok but year out of [1800, 2030]
- manual_seed_cache_write: client manual + cache write-through
"""

from __future__ import annotations

import logging
import sys
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

# Saatchi enricher 는 src/ 외부 (scripts/) — sys.path 통해 import
_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_ROOT / "scripts"))


CACHE_TTL_SEC: int = 7 * 86400  # 7 days
CACHE_MAX_SIZE: int = 50_000
VALID_YEAR_MIN: int = 1800
VALID_YEAR_MAX: int = 2030

YearRoute = Literal[
    "cache_hit",
    "fetch_ok",
    "fetch_fail",
    "no_id",
    "parse_invalid",
    "manual_seed_cache_write",
]


class ArtworkYearCache:
    """Thread-safe in-memory LRU cache + TTL for artwork year_made.

    Stores:
        artwork_id (str) → {year_made: int, fetched_at: float, source: str}
        artwork_url (str) → artwork_id (alias)
    """

    def __init__(
        self,
        ttl_sec: int = CACHE_TTL_SEC,
        max_size: int = CACHE_MAX_SIZE,
    ) -> None:
        self._ttl_sec = ttl_sec
        self._max_size = max_size
        self._cache: OrderedDict[str, dict] = OrderedDict()
        self._url_to_id: dict[str, str] = {}
        self._lock = threading.Lock()

    def __len__(self) -> int:
        with self._lock:
            return len(self._cache)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._url_to_id.clear()

    def _is_expired(self, entry: dict, now: float) -> bool:
        return now - entry["fetched_at"] > self._ttl_sec

    def _purge_aliases_for_locked(self, artwork_id: str) -> None:
        """lock 안에서 호출. artwork_id 가 evict/expire 될 때 해당 alias 모두 제거.

        코덱스 P1 fix: alias map 무한 증가 방지 (메모리 누수 + url_alias_count 신뢰성).
        """
        stale = [u for u, aid in self._url_to_id.items() if aid == artwork_id]
        for u in stale:
            del self._url_to_id[u]

    def _evict_expired_locked(self, now: float) -> None:
        """lock 안에서 호출. 만료 entry + 해당 alias 제거."""
        expired_keys = [k for k, v in self._cache.items() if self._is_expired(v, now)]
        for k in expired_keys:
            del self._cache[k]
            self._purge_aliases_for_locked(k)

    def _evict_lru_locked(self) -> None:
        """lock 안에서 호출. capacity 초과 시 가장 오래된 entry + alias 제거."""
        while len(self._cache) > self._max_size:
            evicted_id, _ = self._cache.popitem(last=False)  # FIFO (oldest first)
            self._purge_aliases_for_locked(evicted_id)

    def get(
        self, artwork_id: str | None, artwork_url: str | None = None
    ) -> tuple[int | None, YearRoute | None]:
        """Cache lookup. artwork_id 우선, artwork_url alias fallback.

        Returns:
            (year_made, route) — hit 시 ('cache_hit'), miss 시 (None, None).
        """
        if not artwork_id and not artwork_url:
            return None, None

        now = time.time()
        with self._lock:
            resolved_id = artwork_id
            if not resolved_id and artwork_url:
                resolved_id = self._url_to_id.get(artwork_url)
            if not resolved_id:
                return None, None

            entry = self._cache.get(resolved_id)
            if entry is None:
                return None, None
            if self._is_expired(entry, now):
                del self._cache[resolved_id]
                self._purge_aliases_for_locked(resolved_id)
                return None, None

            # LRU: move to end (most recent)
            self._cache.move_to_end(resolved_id)
            return entry["year_made"], "cache_hit"

    def put(
        self,
        artwork_id: str,
        year_made: int,
        source: str,
        artwork_url: str | None = None,
    ) -> None:
        """Cache put. valid year range 검증 후 저장. URL alias 등록."""
        if not artwork_id:
            return
        if not (VALID_YEAR_MIN <= year_made <= VALID_YEAR_MAX):
            logger.warning(
                "skip cache put — year %d out of [%d, %d]",
                year_made,
                VALID_YEAR_MIN,
                VALID_YEAR_MAX,
            )
            return

        now = time.time()
        with self._lock:
            self._cache[artwork_id] = {
                "year_made": int(year_made),
                "fetched_at": now,
                "source": source,
            }
            self._cache.move_to_end(artwork_id)
            if artwork_url:
                self._url_to_id[artwork_url] = artwork_id
            self._evict_expired_locked(now)
            self._evict_lru_locked()

    def stats(self) -> dict:
        """현재 cache 상태 (monitoring용)."""
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "ttl_sec": self._ttl_sec,
                "url_alias_count": len(self._url_to_id),
            }


# 모듈 단위 singleton (production server 에서 공유)
_global_cache: ArtworkYearCache | None = None


def get_global_cache() -> ArtworkYearCache:
    global _global_cache
    if _global_cache is None:
        _global_cache = ArtworkYearCache()
    return _global_cache


def reset_global_cache() -> None:
    """테스트용. production 에서 호출 X."""
    global _global_cache
    _global_cache = ArtworkYearCache()


def get_artwork_year(
    artwork_id: str | None,
    artwork_url: str | None = None,
    *,
    fetch_fn=None,
    cache: ArtworkYearCache | None = None,
) -> tuple[int | None, YearRoute]:
    """artwork_id 또는 artwork_url 로 year_made 조회.

    Args:
        artwork_id: Saatchi artwork ID
        artwork_url: 대체 lookup URL (artwork_id 미제공 시)
        fetch_fn: cache miss 시 detail page fetch 함수.
                  signature: fetch_fn(url) -> EnrichmentResult.
                  None 이면 saatchi_detail_enricher.fetch_and_parse_saatchi_detail 사용.
        cache: 사용할 cache instance. None 이면 global_cache.

    Returns:
        (year_made, route): year_made (int) or None, route ∈ YearRoute.
    """
    if cache is None:
        cache = get_global_cache()

    if not artwork_id and not artwork_url:
        return None, "no_id"

    # 1. cache lookup
    cached_year, cached_route = cache.get(artwork_id, artwork_url)
    if cached_route == "cache_hit":
        return cached_year, "cache_hit"

    # 2. cache miss → fetch
    if fetch_fn is None:
        from saatchi_detail_enricher import fetch_and_parse_saatchi_detail

        fetch_fn = fetch_and_parse_saatchi_detail

    fetch_url = artwork_url
    if not fetch_url:
        # artwork_id 만 있는데 URL fallback 없음 — fetch 불가 (saatchi URL pattern 알 수 X)
        logger.warning("get_artwork_year: artwork_id=%s but no artwork_url", artwork_id)
        return None, "no_id"

    try:
        result = fetch_fn(fetch_url)
    except Exception as e:
        logger.warning("fetch_fn raised: %s", e)
        return None, "fetch_fail"

    fetch_status = getattr(result, "fetch_status", None)
    year = getattr(result, "year_created", None)

    if fetch_status != "ok":
        return None, "fetch_fail"

    if year is None:
        return None, "parse_invalid"

    if not (VALID_YEAR_MIN <= year <= VALID_YEAR_MAX):
        return None, "parse_invalid"

    # 3. cache write (artwork_id 결정 — fetch_url 에서 추출 또는 받은 그대로)
    cache_key = artwork_id or _extract_artwork_id_from_url(fetch_url)
    if cache_key:
        cache.put(cache_key, year, source="fetch", artwork_url=fetch_url)
    return int(year), "fetch_ok"


def seed_artwork_year(
    artwork_id: str | None,
    year_made: int,
    *,
    artwork_url: str | None = None,
    cache: ArtworkYearCache | None = None,
) -> YearRoute:
    """Manual override write-through (v3.5 step 3 §2.3).

    valid manual year + artwork_id 제공 시 cache 등록.
    artwork_id 미제공 시 cache 등록 X (단순 manual 사용만).

    Returns:
        route: 'manual_seed_cache_write' (등록됨) or 'parse_invalid' (range 외) or 'no_id'.
    """
    if cache is None:
        cache = get_global_cache()

    if not (VALID_YEAR_MIN <= year_made <= VALID_YEAR_MAX):
        return "parse_invalid"
    if not artwork_id:
        return "no_id"

    cache.put(artwork_id, year_made, source="manual_seed", artwork_url=artwork_url)
    return "manual_seed_cache_write"


def _extract_artwork_id_from_url(url: str) -> str | None:
    """Saatchi URL → artwork_id 추출.

    Pattern: https://www.saatchiart.com/art/<title>/<artist_id>/<artwork_id>/view
    """
    if not url:
        return None
    parts = url.rstrip("/").split("/")
    # 마지막 segment 가 'view' 면 그 직전이 artwork_id
    if len(parts) >= 2 and parts[-1] == "view":
        candidate = parts[-2]
        if candidate.isdigit():
            return candidate
    return None
