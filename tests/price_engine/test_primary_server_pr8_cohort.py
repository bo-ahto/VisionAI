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
    yield
    ayc.reset_global_cache()


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
    """server.predict 안의 year resolve 로직 단위화. fetch_fn 으로 외부 호출 격리."""
    if not is_saatchi_warm:
        return None, "no_id"
    if manual_year is not None:
        if artwork_id:
            route = ayc.seed_artwork_year(
                artwork_id, manual_year, artwork_url=artwork_url
            )
        else:
            route = "manual_no_cache"
        return int(manual_year), route
    return ayc.get_artwork_year(
        artwork_id, artwork_url, fetch_fn=fetch_fn
    )


def test_year_skipped_when_cohort_false():
    """비대상 cohort → year resolve 안 함."""
    year, route = _resolve_year(
        is_saatchi_warm=False, manual_year=2020, artwork_id="abc", artwork_url=None,
    )
    assert year is None
    assert route == "no_id"


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
    year, route = _resolve_year(
        is_saatchi_warm=True, manual_year=2018, artwork_id=None, artwork_url=None,
    )
    assert year == 2018
    assert route == "manual_no_cache"
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
