"""v3.6 Phase 1 PR3: artwork_year_cache 단위 테스트.

검증:
- ArtworkYearCache: get / put / TTL / LRU eviction / URL alias
- get_artwork_year: cache hit / fetch_ok / fetch_fail / parse_invalid / no_id
- seed_artwork_year: manual_seed_cache_write / parse_invalid / no_id
- _extract_artwork_id_from_url
- Thread safety smoke (lock)
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from visionai.price_engine.api import artwork_year_cache as ayc
from visionai.price_engine.api.artwork_year_cache import (
    ArtworkYearCache,
    _extract_artwork_id_from_url,
    get_artwork_year,
    seed_artwork_year,
)


@pytest.fixture(autouse=True)
def _bypass_token_bucket(monkeypatch):
    """v3.6 PR10 token bucket 우회 — 이 파일은 cache / fetch / TTL / LRU 검증 전용."""
    monkeypatch.setattr(ayc, "FETCH_QPS_CAPACITY", 100_000)
    monkeypatch.setattr(ayc, "FETCH_QPS_REFILL_PER_SEC", 100_000.0)
    ayc.reset_global_gate()
    yield
    ayc.reset_global_gate()

# ---- ArtworkYearCache: get / put ----


def test_cache_put_and_get_basic():
    cache = ArtworkYearCache()
    cache.put("art1", 2020, source="fetch")
    year, route = cache.get("art1")
    assert year == 2020
    assert route == "cache_hit"


def test_cache_get_miss_returns_none():
    cache = ArtworkYearCache()
    year, route = cache.get("art_missing")
    assert year is None
    assert route is None


def test_cache_get_with_no_id_or_url():
    cache = ArtworkYearCache()
    year, route = cache.get(None, None)
    assert year is None
    assert route is None


def test_cache_put_rejects_invalid_year_range():
    cache = ArtworkYearCache()
    cache.put("art1", 1799, source="fetch")  # < 1800
    cache.put("art1", 2031, source="fetch")  # > 2030
    assert len(cache) == 0


def test_cache_put_accepts_boundary_years():
    cache = ArtworkYearCache()
    cache.put("art1", 1800, source="fetch")
    cache.put("art2", 2030, source="fetch")
    assert len(cache) == 2


# ---- TTL ----


def test_cache_ttl_expiry():
    cache = ArtworkYearCache(ttl_sec=1)  # 1 sec TTL
    cache.put("art1", 2020, source="fetch")
    year, route = cache.get("art1")
    assert year == 2020
    time.sleep(1.5)
    year, route = cache.get("art1")
    assert year is None
    assert route is None


def test_cache_ttl_does_not_expire_within_window():
    cache = ArtworkYearCache(ttl_sec=10)
    cache.put("art1", 2020, source="fetch")
    time.sleep(0.1)
    year, _route = cache.get("art1")
    assert year == 2020


# ---- LRU eviction ----


def test_cache_lru_eviction_when_over_capacity():
    cache = ArtworkYearCache(max_size=2)
    cache.put("art1", 2020, source="fetch")
    cache.put("art2", 2021, source="fetch")
    cache.put("art3", 2022, source="fetch")  # eviction triggers
    # art1 evicted (oldest), art2/art3 retained
    assert cache.get("art1") == (None, None)
    assert cache.get("art2")[0] == 2021
    assert cache.get("art3")[0] == 2022


def test_cache_lru_get_resets_recency():
    cache = ArtworkYearCache(max_size=2)
    cache.put("art1", 2020, source="fetch")
    cache.put("art2", 2021, source="fetch")
    cache.get("art1")  # art1 → most recent
    cache.put("art3", 2022, source="fetch")  # art2 evicted (oldest)
    assert cache.get("art1")[0] == 2020
    assert cache.get("art2") == (None, None)
    assert cache.get("art3")[0] == 2022


# ---- URL alias ----


def test_cache_url_alias_lookup():
    cache = ArtworkYearCache()
    cache.put("art1", 2020, source="fetch", artwork_url="https://example.com/art1")
    year, route = cache.get(None, "https://example.com/art1")
    assert year == 2020
    assert route == "cache_hit"


def test_cache_url_alias_miss_when_url_unknown():
    cache = ArtworkYearCache()
    cache.put("art1", 2020, source="fetch", artwork_url="https://example.com/art1")
    year, route = cache.get(None, "https://example.com/other")
    assert year is None
    assert route is None


# ---- stats ----


def test_cache_stats_reports_size_and_aliases():
    cache = ArtworkYearCache(max_size=100, ttl_sec=3600)
    cache.put("art1", 2020, source="fetch", artwork_url="https://example.com/art1")
    cache.put("art2", 2021, source="fetch")
    s = cache.stats()
    assert s["size"] == 2
    assert s["max_size"] == 100
    assert s["ttl_sec"] == 3600
    assert s["url_alias_count"] == 1


# ---- get_artwork_year wrapper ----


def _make_fetch_result(status: str, year: int | None):
    """EnrichmentResult-like 객체 mock."""
    m = MagicMock()
    m.fetch_status = status
    m.year_created = year
    return m


def test_get_artwork_year_cache_hit():
    cache = ArtworkYearCache()
    cache.put("art1", 2020, source="fetch", artwork_url="https://example.com/art1")
    fetch_fn = MagicMock()  # 호출되면 안 됨
    year, route = get_artwork_year(
        "art1", "https://example.com/art1", fetch_fn=fetch_fn, cache=cache
    )
    assert year == 2020
    assert route == "cache_hit"
    fetch_fn.assert_not_called()


def test_get_artwork_year_fetch_ok():
    cache = ArtworkYearCache()
    fetch_fn = MagicMock(return_value=_make_fetch_result("ok", 2018))
    year, route = get_artwork_year(
        "art1", "https://www.saatchiart.com/art/x/1/art1/view", fetch_fn=fetch_fn, cache=cache
    )
    assert year == 2018
    assert route == "fetch_ok"
    fetch_fn.assert_called_once()
    # cache write 됨
    year2, _route2 = cache.get("art1")
    assert year2 == 2018


def test_get_artwork_year_fetch_fail_5xx():
    cache = ArtworkYearCache()
    fetch_fn = MagicMock(return_value=_make_fetch_result("5xx", None))
    year, route = get_artwork_year(
        "art1", "https://www.saatchiart.com/art/x/1/art1/view", fetch_fn=fetch_fn, cache=cache
    )
    assert year is None
    assert route == "fetch_fail"
    # cache write 안 됨
    assert len(cache) == 0


def test_get_artwork_year_parse_invalid_year_out_of_range():
    cache = ArtworkYearCache()
    fetch_fn = MagicMock(return_value=_make_fetch_result("ok", 1500))  # < 1800
    year, route = get_artwork_year(
        "art1", "https://www.saatchiart.com/art/x/1/art1/view", fetch_fn=fetch_fn, cache=cache
    )
    assert year is None
    assert route == "parse_invalid"


def test_get_artwork_year_parse_invalid_year_none():
    cache = ArtworkYearCache()
    fetch_fn = MagicMock(return_value=_make_fetch_result("ok", None))
    year, route = get_artwork_year(
        "art1", "https://www.saatchiart.com/art/x/1/art1/view", fetch_fn=fetch_fn, cache=cache
    )
    assert year is None
    assert route == "parse_invalid"


def test_get_artwork_year_no_id():
    cache = ArtworkYearCache()
    year, route = get_artwork_year(None, None, cache=cache)
    assert year is None
    assert route == "no_id"


def test_get_artwork_year_artwork_id_only_no_url_returns_no_id():
    """artwork_id 만 있고 URL fallback 없으면 fetch 불가."""
    cache = ArtworkYearCache()
    year, route = get_artwork_year("art1", None, cache=cache)
    assert year is None
    assert route == "no_id"


def test_get_artwork_year_fetch_exception_returns_fetch_fail():
    cache = ArtworkYearCache()
    fetch_fn = MagicMock(side_effect=RuntimeError("network error"))
    year, route = get_artwork_year(
        "art1", "https://www.saatchiart.com/art/x/1/art1/view", fetch_fn=fetch_fn, cache=cache
    )
    assert year is None
    assert route == "fetch_fail"


# ---- seed_artwork_year (manual write-through) ----


def test_seed_artwork_year_valid():
    cache = ArtworkYearCache()
    route = seed_artwork_year("art1", 2020, cache=cache)
    assert route == "manual_seed_cache_write"
    year, _ = cache.get("art1")
    assert year == 2020


def test_seed_artwork_year_invalid_year_range():
    cache = ArtworkYearCache()
    route = seed_artwork_year("art1", 1799, cache=cache)
    assert route == "parse_invalid"
    assert len(cache) == 0


def test_seed_artwork_year_no_artwork_id():
    cache = ArtworkYearCache()
    route = seed_artwork_year(None, 2020, cache=cache)
    assert route == "no_id"
    assert len(cache) == 0


def test_seed_artwork_year_with_url_alias():
    cache = ArtworkYearCache()
    seed_artwork_year("art1", 2020, artwork_url="https://example.com/art1", cache=cache)
    year, route = cache.get(None, "https://example.com/art1")
    assert year == 2020
    assert route == "cache_hit"


# ---- _extract_artwork_id_from_url ----


def test_extract_artwork_id_from_saatchi_url():
    url = "https://www.saatchiart.com/art/Painting-Title/1234/567890/view"
    assert _extract_artwork_id_from_url(url) == "567890"


def test_extract_artwork_id_handles_trailing_slash():
    url = "https://www.saatchiart.com/art/Painting-Title/1234/567890/view/"
    assert _extract_artwork_id_from_url(url) == "567890"


def test_extract_artwork_id_returns_none_for_invalid_url():
    assert _extract_artwork_id_from_url("") is None
    assert _extract_artwork_id_from_url("https://example.com/foo") is None
    # 마지막이 'view' 가 아니거나 직전이 숫자 아님
    assert _extract_artwork_id_from_url("https://www.saatchiart.com/foo/bar/view") is None


# ---- Cache clear ----


def test_cache_clear_resets_state():
    cache = ArtworkYearCache()
    cache.put("art1", 2020, source="fetch", artwork_url="https://example.com/x")
    assert len(cache) == 1
    cache.clear()
    assert len(cache) == 0
    assert cache.stats()["url_alias_count"] == 0


# ---- Thread safety smoke ----


def test_cache_thread_safety_smoke():
    """다중 thread 에서 동시 put/get 시 race condition / corruption 없음."""
    import threading

    cache = ArtworkYearCache(max_size=1000)

    def worker(start_idx: int):
        for i in range(100):
            key = f"art_{start_idx}_{i}"
            cache.put(key, 2020, source="fetch")
            cache.get(key)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(cache) <= 500
    assert len(cache) > 0


# ---- Cache write 후 만료 → 재 fetch ----


def test_get_artwork_year_after_ttl_expiry_refetches():
    cache = ArtworkYearCache(ttl_sec=1)
    cache.put(
        "art1", 2020, source="fetch", artwork_url="https://www.saatchiart.com/art/x/1/art1/view"
    )
    time.sleep(1.5)
    fetch_fn = MagicMock(return_value=_make_fetch_result("ok", 2025))
    year, route = get_artwork_year(
        "art1", "https://www.saatchiart.com/art/x/1/art1/view", fetch_fn=fetch_fn, cache=cache
    )
    assert year == 2025
    assert route == "fetch_ok"
    fetch_fn.assert_called_once()


# ---- 코덱스 P1 fix: alias cleanup on TTL/LRU eviction ----


def test_alias_cleanup_on_ttl_expiry():
    """TTL expiry 시 url_to_id alias 도 정리 (메모리 누수 방지)."""
    cache = ArtworkYearCache(ttl_sec=1)
    cache.put("art1", 2020, source="fetch", artwork_url="https://example.com/art1")
    cache.put("art2", 2021, source="fetch", artwork_url="https://example.com/art2")
    assert cache.stats()["url_alias_count"] == 2
    time.sleep(1.5)
    # get() 호출로 expiry trigger
    cache.get("art1")
    cache.get("art2")
    assert len(cache) == 0
    assert cache.stats()["url_alias_count"] == 0


def test_alias_cleanup_on_lru_eviction():
    """LRU eviction 시 url_to_id alias 도 정리."""
    cache = ArtworkYearCache(max_size=2)
    cache.put("art1", 2020, source="fetch", artwork_url="https://example.com/art1")
    cache.put("art2", 2021, source="fetch", artwork_url="https://example.com/art2")
    cache.put("art3", 2022, source="fetch", artwork_url="https://example.com/art3")
    assert len(cache) == 2
    assert cache.stats()["url_alias_count"] == 2  # art1 alias 도 제거됨
    year, _ = cache.get(None, "https://example.com/art1")
    assert year is None


def test_alias_does_not_grow_unbounded():
    """capacity 초과 후 alias map 도 capacity 이하 유지."""
    cache = ArtworkYearCache(max_size=10)
    for i in range(50):
        cache.put(f"art{i}", 2020, source="fetch", artwork_url=f"https://example.com/art{i}")
    assert len(cache) == 10
    assert cache.stats()["url_alias_count"] == 10


# ---- 코덱스 P1 fix: 추가 fetch_status branch coverage ----


def test_get_artwork_year_blocked_status():
    cache = ArtworkYearCache()
    fetch_fn = MagicMock(return_value=_make_fetch_result("blocked", None))
    year, route = get_artwork_year(
        "art1", "https://www.saatchiart.com/art/x/1/art1/view", fetch_fn=fetch_fn, cache=cache
    )
    assert year is None
    assert route == "fetch_fail"
    assert len(cache) == 0


def test_get_artwork_year_timeout_status():
    cache = ArtworkYearCache()
    fetch_fn = MagicMock(return_value=_make_fetch_result("timeout", None))
    year, route = get_artwork_year(
        "art1", "https://www.saatchiart.com/art/x/1/art1/view", fetch_fn=fetch_fn, cache=cache
    )
    assert year is None
    assert route == "fetch_fail"


def test_get_artwork_year_network_error_status():
    cache = ArtworkYearCache()
    fetch_fn = MagicMock(return_value=_make_fetch_result("network_error", None))
    year, route = get_artwork_year(
        "art1", "https://www.saatchiart.com/art/x/1/art1/view", fetch_fn=fetch_fn, cache=cache
    )
    assert year is None
    assert route == "fetch_fail"


def test_get_artwork_year_short_response_status():
    cache = ArtworkYearCache()
    fetch_fn = MagicMock(return_value=_make_fetch_result("short_response", None))
    year, route = get_artwork_year(
        "art1", "https://www.saatchiart.com/art/x/1/art1/view", fetch_fn=fetch_fn, cache=cache
    )
    assert year is None
    assert route == "fetch_fail"


# ---- 코덱스 P1 fix: URL-only fetch → alias 등록 → 다음 URL-only hit 경로 ----


def test_url_only_request_fetches_then_aliases_for_next_hit():
    """URL-only 요청 (artwork_id=None):
    1) cache miss → fetch + URL 에서 artwork_id 추출 → cache write + alias 등록
    2) 다음 같은 URL 요청 → cache_hit (artwork_id 없이도 hit)
    """
    cache = ArtworkYearCache()
    fetch_fn = MagicMock(return_value=_make_fetch_result("ok", 2019))
    url = "https://www.saatchiart.com/art/Title/1234/567890/view"

    year, route = get_artwork_year(None, url, fetch_fn=fetch_fn, cache=cache)
    assert year == 2019
    assert route == "fetch_ok"
    assert len(cache) == 1
    assert cache.stats()["url_alias_count"] == 1

    fetch_fn.reset_mock()
    year2, route2 = get_artwork_year(None, url, fetch_fn=fetch_fn, cache=cache)
    assert year2 == 2019
    assert route2 == "cache_hit"
    fetch_fn.assert_not_called()
