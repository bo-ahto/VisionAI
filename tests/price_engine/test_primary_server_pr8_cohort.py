"""v3.6 Phase 1 PR8: 단건 server cohort gating + year resolution 단위 테스트.

검증 (build_features 호출까지의 server 결정 로직, FastAPI request 우회):
- cohort=True: is_matched + profile.source=='saatchi' + warm slug
- cohort=False: 위 조건 중 하나라도 깨지면 False (external_collector profile 비권위)
- year resolution: manual > cache.get > fetch (saatchi-only)
- build_features 가 받는 is_saatchi_warm/year_made parameter 정합
- model_info() defensive fallback 의 features_count 가 _predictor.cb_features (P2 fix)
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from visionai.price_engine.api import artwork_year_cache as ayc


@pytest.fixture(autouse=True)
def reset_cache():
    ayc.reset_global_cache()
    ayc.reset_global_gate()
    yield
    ayc.reset_global_cache()
    ayc.reset_global_gate()


# ---- Cohort 결정 (server logic 모사: 의존성 주입으로 단위화) ----


def _decide_cohort(is_matched: bool, profile: dict | None, slug: str | None,
                   is_warm_fn) -> bool:
    """server.predict 안의 cohort 결정 로직을 단위 함수로 추출 (단위 검증용)."""
    return (
        is_matched
        and isinstance(profile, dict)
        and profile.get("source") == "saatchi"
        and bool(slug)
        and is_warm_fn(slug)
    )


def test_cohort_true_when_saatchi_and_warm():
    is_warm = lambda s: s == "kim"  # noqa: E731
    assert _decide_cohort(True, {"source": "saatchi"}, "kim", is_warm) is True


def test_cohort_false_when_unmatched():
    is_warm = lambda s: True  # noqa: E731
    assert _decide_cohort(False, {"source": "saatchi"}, "kim", is_warm) is False


def test_cohort_false_when_not_saatchi_source():
    """artsy / external_collector profile 은 cohort 결정에 사용 X."""
    is_warm = lambda s: True  # noqa: E731
    assert _decide_cohort(True, {"source": "artsy"}, "kim", is_warm) is False
    assert _decide_cohort(True, {"source": "external"}, "kim", is_warm) is False
    assert _decide_cohort(True, {}, "kim", is_warm) is False


def test_cohort_false_when_cold_artist():
    """source=saatchi 라도 warm set 외부면 False (cold 보호)."""
    is_warm = lambda s: s in {"warm_a", "warm_b"}  # noqa: E731
    assert _decide_cohort(True, {"source": "saatchi"}, "cold_x", is_warm) is False


def test_cohort_false_when_no_slug():
    is_warm = lambda s: True  # noqa: E731
    assert _decide_cohort(True, {"source": "saatchi"}, None, is_warm) is False
    assert _decide_cohort(True, {"source": "saatchi"}, "", is_warm) is False


def test_cohort_false_when_warm_set_empty():
    """warm artifact 미로드 시 is_warm_artist 항상 False → cohort 자동 보호."""
    is_warm = lambda s: False  # noqa: E731
    assert _decide_cohort(True, {"source": "saatchi"}, "kim", is_warm) is False


# ---- Year resolution flow (server logic 모사) ----


def _resolve_year(*, is_saatchi_warm: bool, manual_year: int | None,
                  artwork_id: str | None, artwork_url: str | None,
                  fetch_fn=None):
    """server.predict 안의 year resolve 로직 단위화. fetch_fn 으로 외부 호출 격리.

    v3.6 PR8b: route 계약 — 'disabled' (비대상), 'manual' (no cache),
    'manual_seed_cache_write' (manual + cache).
    """
    if not is_saatchi_warm:
        return None, "disabled"
    if manual_year is not None:
        if artwork_id:
            route = ayc.seed_artwork_year(
                artwork_id, manual_year, artwork_url=artwork_url
            )
        else:
            route = "manual"
        return int(manual_year), route
    return ayc.get_artwork_year(
        artwork_id, artwork_url, fetch_fn=fetch_fn
    )


def test_year_skipped_when_cohort_false():
    """비대상 cohort → year resolve 안 함, route='disabled' (PR8b)."""
    year, route = _resolve_year(
        is_saatchi_warm=False, manual_year=2020, artwork_id="abc", artwork_url=None,
    )
    assert year is None
    assert route == "disabled"


def test_year_manual_with_artwork_id_writes_through():
    year, route = _resolve_year(
        is_saatchi_warm=True, manual_year=2020, artwork_id="aw1",
        artwork_url="https://saatchiart.com/x/y/aw1/view",
    )
    assert year == 2020
    assert route == "manual_seed_cache_write"
    # 다음 cache hit 까지 검증
    cached_year, cached_route = ayc.get_global_cache().get("aw1")
    assert cached_year == 2020
    assert cached_route == "cache_hit"


def test_year_manual_without_artwork_id_no_cache():
    """manual override 만 있고 cache 등록 X — route='manual' (PR8b 계약)."""
    year, route = _resolve_year(
        is_saatchi_warm=True, manual_year=2018, artwork_id=None, artwork_url=None,
    )
    assert year == 2018
    assert route == "manual"
    assert ayc.get_global_cache().stats()["size"] == 0


def test_year_manual_invalid_range_returns_parse_invalid_route():
    """seed 가 invalid year 거부 — manual 값은 그대로 사용 (caller 책임), route 만 표시."""
    year, route = _resolve_year(
        is_saatchi_warm=True, manual_year=1500, artwork_id="aw_invalid",
        artwork_url=None,
    )
    assert year == 1500  # caller 가 manual 값 사용 (build_features 안에서 range guard)
    assert route == "parse_invalid"


def test_year_cache_hit_when_seeded():
    ayc.seed_artwork_year("aw_seeded", 2019, artwork_url="https://x/aw_seeded/view")
    year, route = _resolve_year(
        is_saatchi_warm=True, manual_year=None, artwork_id="aw_seeded",
        artwork_url=None,
    )
    assert year == 2019
    assert route == "cache_hit"


def test_year_fetch_ok_path_caches_result():
    """cache miss + fetch_fn 가 ok → fetch_ok + 다음에는 cache_hit."""
    fake_result = MagicMock()
    fake_result.fetch_status = "ok"
    fake_result.year_created = 2017
    fetch_fn = MagicMock(return_value=fake_result)

    # Saatchi URL pattern: /art/<title>/<artist_id>/<artwork_id>/view (artwork_id digits)
    url = "https://www.saatchiart.com/art/title/artist_id/123456/view"
    year, route = _resolve_year(
        is_saatchi_warm=True, manual_year=None, artwork_id=None, artwork_url=url,
        fetch_fn=fetch_fn,
    )
    assert year == 2017
    assert route == "fetch_ok"
    fetch_fn.assert_called_once_with(url)
    # 다음 호출 cache_hit
    year2, route2 = _resolve_year(
        is_saatchi_warm=True, manual_year=None, artwork_id=None, artwork_url=url,
        fetch_fn=fetch_fn,
    )
    assert year2 == 2017
    assert route2 == "cache_hit"
    fetch_fn.assert_called_once()  # 두 번째 호출은 cache 에서


def test_year_fetch_fail_returns_none():
    fake_result = MagicMock()
    fake_result.fetch_status = "blocked"
    fake_result.year_created = None
    fetch_fn = MagicMock(return_value=fake_result)

    year, route = _resolve_year(
        is_saatchi_warm=True, manual_year=None, artwork_id="x",
        artwork_url="https://x/y/x/view", fetch_fn=fetch_fn,
    )
    assert year is None
    assert route == "fetch_fail"


def test_year_no_id_when_nothing_provided():
    year, route = _resolve_year(
        is_saatchi_warm=True, manual_year=None, artwork_id=None, artwork_url=None,
    )
    assert year is None
    assert route == "no_id"


# ---- FetchGate (PR8a P0 fix): rate-limit / cool-down / stampede ----


def test_fetch_gate_acquires_under_limits():
    gate = ayc.FetchGate()
    acquired, reason = gate.try_acquire("a1")
    assert acquired is True
    assert reason == "ok"
    gate.release("a1", success=True)


def test_fetch_gate_blocks_when_concurrent_max():
    gate = ayc.FetchGate()
    for i in range(ayc.FETCH_CONCURRENT_MAX):
        ok, _ = gate.try_acquire(f"a{i}")
        assert ok is True
    blocked, reason = gate.try_acquire("over")
    assert blocked is False
    assert reason == "concurrent"


def test_fetch_gate_blocks_when_5min_burst_exceeds():
    gate = ayc.FetchGate()
    # 5min window 안에 burst max 채움 (acquire 후 release 로 concurrent 는 비움)
    for i in range(ayc.FETCH_5MIN_BURST_MAX):
        ok, _ = gate.try_acquire(f"a{i}")
        assert ok is True
        gate.release(f"a{i}", success=True)
    blocked, reason = gate.try_acquire("burst_over")
    assert blocked is False
    assert reason == "burst"


def test_fetch_gate_cool_down_after_consecutive_fails():
    gate = ayc.FetchGate()
    for i in range(ayc.FETCH_FAIL_COOL_DOWN_THRESHOLD):
        ok, _ = gate.try_acquire(f"f{i}")
        assert ok is True
        gate.release(f"f{i}", success=False)
    # cool-down 활성 → 다음 try_acquire 차단
    blocked, reason = gate.try_acquire("after_fail")
    assert blocked is False
    assert reason == "cool_down"
    stats = gate.stats()
    assert stats["cool_down_remaining_sec"] > 0


def test_fetch_gate_recovers_after_success():
    gate = ayc.FetchGate()
    # 실패 1건 → 누적
    ok, _ = gate.try_acquire("k1")
    gate.release("k1", success=False)
    # 성공 1건 → consecutive_fails 리셋
    ok2, _ = gate.try_acquire("k2")
    gate.release("k2", success=True)
    assert gate.stats()["consecutive_fails"] == 0


def test_get_artwork_year_returns_rate_limited_when_gate_blocks():
    """gate suspend 시 fetch 안 하고 'rate_limited' route 반환."""
    gate = ayc.FetchGate()
    # 5 concurrent 채워서 gate 차단
    for i in range(ayc.FETCH_CONCURRENT_MAX):
        ok, _ = gate.try_acquire(f"hold{i}")
        assert ok is True
    fetch_fn = MagicMock()  # 호출되면 안 됨
    cache = ayc.ArtworkYearCache()
    year, route = ayc.get_artwork_year(
        "x", "https://x/y/x/view", fetch_fn=fetch_fn, cache=cache, gate=gate,
    )
    assert year is None
    assert route == "rate_limited"
    fetch_fn.assert_not_called()


def test_get_artwork_year_releases_gate_on_fetch_fail():
    """fetch 실패해도 gate.release 호출 — concurrent 카운터 누수 방지."""
    fake_result = MagicMock()
    fake_result.fetch_status = "blocked"
    fake_result.year_created = None
    fetch_fn = MagicMock(return_value=fake_result)
    gate = ayc.FetchGate()
    cache = ayc.ArtworkYearCache()

    year, route = ayc.get_artwork_year(
        "x", "https://x/y/x/view", fetch_fn=fetch_fn, cache=cache, gate=gate,
    )
    assert year is None
    assert route == "fetch_fail"
    assert gate.stats()["concurrent"] == 0
    assert gate.stats()["consecutive_fails"] == 1


def test_get_artwork_year_releases_gate_on_fetch_ok():
    fake_result = MagicMock()
    fake_result.fetch_status = "ok"
    fake_result.year_created = 2017
    fetch_fn = MagicMock(return_value=fake_result)
    gate = ayc.FetchGate()
    cache = ayc.ArtworkYearCache()

    year, route = ayc.get_artwork_year(
        None, "https://www.saatchiart.com/art/t/a/123456/view",
        fetch_fn=fetch_fn, cache=cache, gate=gate,
    )
    assert year == 2017
    assert route == "fetch_ok"
    assert gate.stats()["concurrent"] == 0
    assert gate.stats()["consecutive_fails"] == 0


# ---- PR8d: per-key inflight dedup (코덱스 review P1 fix) ----


def test_fetch_gate_blocks_duplicate_inflight_key():
    """같은 key 가 inflight 면 두 번째 try_acquire 거부 (stampede 방지)."""
    gate = ayc.FetchGate()
    ok1, _ = gate.try_acquire("artwork_X")
    assert ok1 is True
    blocked, reason = gate.try_acquire("artwork_X")
    assert blocked is False
    assert reason == "inflight"
    # 다른 key 는 통과
    ok2, _ = gate.try_acquire("artwork_Y")
    assert ok2 is True


def test_fetch_gate_releases_inflight_on_completion():
    """release 후 같은 key 다시 acquire 가능."""
    gate = ayc.FetchGate()
    ok, _ = gate.try_acquire("artwork_Z")
    assert ok is True
    gate.release("artwork_Z", success=True)
    ok2, _ = gate.try_acquire("artwork_Z")
    assert ok2 is True


def test_get_artwork_year_default_fetch_uses_short_timeout(monkeypatch):
    """PR8d (코덱스 P0 fix): default fetcher 가 FETCH_TIMEOUT_SEC (5s) 사용."""
    captured = {}

    def fake_fetcher(url: str, *, timeout: int = 999):
        captured["timeout"] = timeout
        r = MagicMock()
        r.fetch_status = "ok"
        r.year_created = 2018
        return r

    # saatchi_detail_enricher.fetch_and_parse_saatchi_detail 을 monkeypatch
    import sys
    fake_module = MagicMock()
    fake_module.fetch_and_parse_saatchi_detail = fake_fetcher
    monkeypatch.setitem(sys.modules, "saatchi_detail_enricher", fake_module)

    cache = ayc.ArtworkYearCache()
    gate = ayc.FetchGate()
    # fetch_fn=None 으로 default path 강제
    year, route = ayc.get_artwork_year(
        None, "https://www.saatchiart.com/art/t/a/777/view",
        fetch_fn=None, cache=cache, gate=gate,
    )
    assert year == 2018
    assert route == "fetch_ok"
    assert captured["timeout"] == int(ayc.FETCH_TIMEOUT_SEC)
    assert captured["timeout"] == 5  # spec 기준


def test_fetch_gate_inflight_per_key_independent():
    """다른 key 들은 inflight 영향 없음 (concurrent_max 한도 안에서)."""
    gate = ayc.FetchGate()
    keys = [f"k{i}" for i in range(ayc.FETCH_CONCURRENT_MAX)]
    for k in keys:
        ok, _ = gate.try_acquire(k)
        assert ok is True
    # 같은 key 재시도 — gate 평가 순서: cool_down → concurrent → burst → inflight.
    # concurrent_max 가 먼저 차단 → reason='concurrent'.
    blocked, reason = gate.try_acquire("k0")
    assert blocked is False
    assert reason == "concurrent"  # concurrent 가 inflight 보다 먼저 평가


# ---- model_info() defensive fallback (P2 fix) ----


def test_model_info_defensive_fallback_uses_predictor_cb_features():
    """v3.6 PR8 P2 fix: defensive fallback 도 _predictor.cb_features 길이 사용."""
    from visionai.price_engine.api import primary_server

    fake_predictor = MagicMock()
    fake_predictor.cb_features = ["f"] * 35  # v3.5 variant
    fake_predictor.model_version_label.return_value = "v3.5-fb"

    with patch.object(primary_server, "_predictor", fake_predictor), \
         patch.object(primary_server, "_model_info_cache", None):
        # 비동기 endpoint 의 본문 로직만 직접 호출 위해 await 없이 call
        import asyncio
        info = asyncio.run(primary_server.model_info())

    assert info.features_count == 35
    assert info.training_count == 0
    assert info.mdape_groupkfold == 0.0


def test_model_info_defensive_fallback_v3_filtered_tuned():
    from visionai.price_engine.api import primary_server

    fake_predictor = MagicMock()
    fake_predictor.cb_features = ["f"] * 32  # default variant
    fake_predictor.model_version_label.return_value = "v3-fb"

    with patch.object(primary_server, "_predictor", fake_predictor), \
         patch.object(primary_server, "_model_info_cache", None):
        import asyncio
        info = asyncio.run(primary_server.model_info())

    assert info.features_count == 32
