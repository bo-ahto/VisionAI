"""v3.6 PR9: batch endpoint cohort gating + year resolution endpoint test.

검증:
- /predict/batch 의 각 item 마다 cohort gating + year resolve 적용
- per-item logging row (single 과 동일 schema 15 fields)
- helper 공유 (_decide_saatchi_warm_cohort + _resolve_year_sync) 가
  단건/batch 동일 동작
- 50 item 동시 fetch 가 token bucket / inflight gate 로 직렬화
"""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from visionai.price_engine.api import artwork_year_cache as ayc
from visionai.price_engine.api import primary_server
from visionai.price_engine.api.artist_matcher import MatchResult
from visionai.price_engine.api.primary_schemas import BatchItem, BatchPredictRequest


@pytest.fixture(autouse=True)
def reset_state(monkeypatch):
    # PR10/11b token bucket + warmup 우회
    monkeypatch.setattr(ayc, "FETCH_QPS_CAPACITY", 100_000)
    monkeypatch.setattr(ayc, "FETCH_QPS_REFILL_PER_SEC", 100_000.0)
    monkeypatch.setattr(ayc, "FETCH_WARMUP_QPS_CAPACITY", 100_000)
    monkeypatch.setattr(ayc, "FETCH_WARMUP_QPS_REFILL_PER_SEC", 100_000.0)
    ayc.reset_global_cache()
    ayc.reset_global_gate()
    yield
    ayc.reset_global_cache()
    ayc.reset_global_gate()


def _make_predictor_mock(*, warm_slugs: set[str]):
    pred = MagicMock()
    pred.is_warm_artist = lambda s: s in warm_slugs
    pred.cb_features = ["f"] * 35
    pred.variant = "v3_5_v_year_saatchi_warm"
    pred.predict.return_value = {
        "price_krw": 1_000_000, "price_usd": 750.0,
        "price_range_low": 800_000, "price_range_high": 1_200_000,
        "confidence_grade": "B",
        "model_type": "xgboost_v3_5_v_year_saatchi_warm",
        "is_known_artist": True, "training_count": 12, "margin": 0.15,
    }
    return pred


def _saatchi_match(slug: str) -> MatchResult:
    return MatchResult(
        artist_id=42, name="Kim", score=95.0, training_count=12,
        source="saatchi", profile={"source": "saatchi"}, slug=slug,
    )


def _artsy_match(slug: str) -> MatchResult:
    return MatchResult(
        artist_id=99, name="Lee", score=90.0, training_count=8,
        source="artsy", profile={"source": "artsy"}, slug=slug,
    )


def _make_batch_item(artist_name: str, **kw) -> BatchItem:
    base = dict(
        artist_name=artist_name,
        width_cm=50.0,
        height_cm=50.0,
        medium="oil on canvas",
        target_market="gallery",
    )
    base.update(kw)
    return BatchItem(**base)


def _patch_server(predictor, matcher_side_effects):
    """matcher.match 가 입력별 다른 결과 반환 (artist_name → MatchResult|None)."""
    mtcher = MagicMock()
    mtcher.match.side_effect = matcher_side_effects
    return [
        patch.object(primary_server, "_predictor", predictor),
        patch.object(primary_server, "_matcher", mtcher),
        patch.object(primary_server, "_log_prediction"),
    ]


def _enter(ctxs):
    return [c.__enter__() for c in ctxs]


def _exit(ctxs):
    for c in ctxs:
        c.__exit__(None, None, None)


# ---- T1: batch 안의 각 item 이 단건과 동일 cohort 결정 ----


def test_batch_per_item_cohort_decision():
    pred = _make_predictor_mock(warm_slugs={"warm_kim"})
    # 3 item: saatchi+warm / artsy / saatchi+cold
    matches = [
        _saatchi_match("warm_kim"),
        _artsy_match("artsy_lee"),
        _saatchi_match("cold_park"),
    ]
    ctxs = _patch_server(pred, matches)
    _enter(ctxs)
    try:
        req = BatchPredictRequest(artworks=[
            _make_batch_item("Kim", year_made=2020, artwork_id="aw1",
                             artwork_url="https://saatchi.com/x/aw1/view"),
            _make_batch_item("Lee", year_made=2019),
            _make_batch_item("Park", year_made=2018),
        ])
        asyncio.run(primary_server.predict_batch(req))

        log_calls = primary_server._log_prediction.call_args_list
        assert len(log_calls) == 3
        log0, log1, log2 = (c[0][0] for c in log_calls)

        # T1.1 saatchi + warm + manual → cohort=True, route='manual_seed_cache_write'
        assert log0["is_saatchi_warm"] is True
        assert log0["year_made_route"] == "manual_seed_cache_write"
        assert log0["year_made_used"] == 2020
        assert log0["match_profile_source"] == "saatchi"

        # T1.2 artsy → cohort=False, route='disabled'
        assert log1["is_saatchi_warm"] is False
        assert log1["year_made_route"] == "disabled"
        assert log1["year_made_used"] is None
        assert log1["match_profile_source"] == "artsy"

        # T1.3 saatchi+cold → cohort=False (warm set 외부)
        assert log2["is_saatchi_warm"] is False
        assert log2["year_made_route"] == "disabled"
        assert log2["match_profile_source"] == "saatchi"  # 매칭은 saatchi
        assert log2["slug_in_warm_set"] is False
    finally:
        _exit(ctxs)


# ---- T2: batch 의 logging schema 가 단건과 동일 fields ----


def test_batch_logging_schema_matches_single():
    pred = _make_predictor_mock(warm_slugs={"warm_kim"})
    matches = [_saatchi_match("warm_kim")]
    ctxs = _patch_server(pred, matches)
    _enter(ctxs)
    try:
        req = BatchPredictRequest(artworks=[
            _make_batch_item("Kim", year_made=2020, artwork_id="aw1",
                             artwork_url="https://saatchi.com/x/aw1/view"),
        ])
        asyncio.run(primary_server.predict_batch(req))
        log = primary_server._log_prediction.call_args[0][0]

        # PR10 spec 의 모든 필드 (단건 logging schema 와 동일)
        required = [
            "is_saatchi_warm", "match_profile_source", "slug_in_warm_set",
            "external_collector_source", "year_made_route", "year_made_used",
            "artwork_id", "artwork_url", "enrichment_latency_ms",
            "model_variant", "artifact_version", "warm_artist_slugs_version",
            "rollout_rule_version", "server_instance", "cache_epoch",
        ]
        for field in required:
            assert field in log, f"missing field: {field}"

        # batch 전용 필드
        assert log["batch_index"] == 0
        # PR9b (코덱스 P1 fix): total_ms / predict_total_latency_ms 가 item end-to-end.
        assert "total_ms" in log
        assert isinstance(log["total_ms"], int)
        # predict_total_latency_ms == total_ms (둘 다 item 전체)
        assert log["predict_total_latency_ms"] == log["total_ms"]
        # enrichment_latency_ms ≤ total_ms (enrichment 는 일부 단계)
        assert log["enrichment_latency_ms"] <= log["total_ms"] + 1  # rounding margin
    finally:
        _exit(ctxs)


# ---- T3: matcher.side_effect 의 None (unmatched) 처리 ----


def test_batch_unmatched_item_cohort_false():
    pred = _make_predictor_mock(warm_slugs={"warm_kim"})
    matches = [None]  # 미매칭
    ctxs = _patch_server(pred, matches)
    # external_collector 도 mock
    ext_patch = patch.object(
        primary_server, "external_collector",
        MagicMock(collect=MagicMock(return_value=({}, []))),
    )
    _enter(ctxs)
    ext_patch.__enter__()
    try:
        req = BatchPredictRequest(artworks=[
            _make_batch_item("Unknown", year_made=2020, artwork_id="aw_u"),
        ])
        asyncio.run(primary_server.predict_batch(req))
        log = primary_server._log_prediction.call_args[0][0]
        assert log["is_saatchi_warm"] is False
        assert log["year_made_route"] == "disabled"
        # PR10b: unmatched 시 match_profile_source=None (external 비권위)
        assert log["match_profile_source"] is None
    finally:
        ext_patch.__exit__(None, None, None)
        _exit(ctxs)


# ---- T4: batch 안에서 build_features 받는 parameter 정합 (단건과 동일) ----


def test_batch_build_features_called_with_cohort_and_year():
    pred = _make_predictor_mock(warm_slugs={"warm_kim"})
    matches = [_saatchi_match("warm_kim")]
    ctxs = _patch_server(pred, matches)
    _enter(ctxs)
    bf_spy = patch.object(primary_server, "build_features",
                          wraps=primary_server.build_features)
    bf_mock = bf_spy.__enter__()
    try:
        req = BatchPredictRequest(artworks=[
            _make_batch_item("Kim", year_made=2019),
        ])
        asyncio.run(primary_server.predict_batch(req))
        kwargs = bf_mock.call_args.kwargs
        assert kwargs.get("is_saatchi_warm") is True
        assert kwargs.get("year_made") == 2019
    finally:
        bf_spy.__exit__(None, None, None)
        _exit(ctxs)


# ---- T5: helper 공유 — 단건/batch 동일 결과 ----


def test_decide_saatchi_warm_cohort_helper_consistency():
    """단건/batch 의 cohort 결정이 같은 helper 사용 — 같은 입력 → 같은 결과."""
    pred = _make_predictor_mock(warm_slugs={"warm_kim"})
    with patch.object(primary_server, "_predictor", pred):
        # saatchi + warm
        assert primary_server._decide_saatchi_warm_cohort(
            True, {"source": "saatchi"}, "warm_kim"
        ) is True
        # artsy
        assert primary_server._decide_saatchi_warm_cohort(
            True, {"source": "artsy"}, "warm_kim"
        ) is False
        # cold
        assert primary_server._decide_saatchi_warm_cohort(
            True, {"source": "saatchi"}, "cold_park"
        ) is False
        # unmatched
        assert primary_server._decide_saatchi_warm_cohort(
            False, {"source": "saatchi"}, "warm_kim"
        ) is False


def test_batch_external_collector_dedup_and_executor_wrap():
    """PR13 (코덱스 PR9 review P2): batch 안 unmatched 작가 중복 시 1회만 lookup +
    external_collector.collect 가 await loop.run_in_executor 로 분리."""
    pred = _make_predictor_mock(warm_slugs={"warm_kim"})
    # 3 item 모두 unmatched + 같은 artist_name "Unknown" (중복)
    matches = [None, None, None]
    ctxs = _patch_server(pred, matches)
    collect_calls = []

    def _fake_collect(name, _flag=False):
        collect_calls.append(name)
        return ({}, [])

    ext_patch = patch.object(
        primary_server, "external_collector",
        MagicMock(collect=MagicMock(side_effect=_fake_collect)),
    )
    _enter(ctxs)
    ext_patch.__enter__()
    try:
        # 같은 작가명 3번 → dedup 으로 1회만 lookup
        req = BatchPredictRequest(artworks=[
            _make_batch_item("Unknown"),
            _make_batch_item("Unknown"),
            _make_batch_item("Unknown"),
        ])
        asyncio.run(primary_server.predict_batch(req))
        # 같은 artist_name 3번 → 1회 lookup (dedup)
        unique_calls = list(set(collect_calls))
        assert unique_calls == ["Unknown"]
        assert len(collect_calls) == 1
    finally:
        ext_patch.__exit__(None, None, None)
        _exit(ctxs)


def test_batch_external_collector_separate_artists_lookup_per_unique():
    """다른 artist_name 들은 각각 1회씩 lookup."""
    pred = _make_predictor_mock(warm_slugs=set())
    matches = [None, None, None]
    ctxs = _patch_server(pred, matches)
    collect_calls = []

    def _fake_collect(name, _flag=False):
        collect_calls.append(name)
        return ({}, [])

    ext_patch = patch.object(
        primary_server, "external_collector",
        MagicMock(collect=MagicMock(side_effect=_fake_collect)),
    )
    _enter(ctxs)
    ext_patch.__enter__()
    try:
        req = BatchPredictRequest(artworks=[
            _make_batch_item("Alice"),
            _make_batch_item("Bob"),
            _make_batch_item("Alice"),  # 중복 — Alice 2회면 1 lookup
        ])
        asyncio.run(primary_server.predict_batch(req))
        # Alice + Bob = 2 lookups (Alice 의 두 번째 call 은 cache hit)
        assert sorted(collect_calls) == ["Alice", "Bob"]
    finally:
        ext_patch.__exit__(None, None, None)
        _exit(ctxs)


def test_resolve_year_sync_helper_consistency():
    """_resolve_year_sync helper 단위 검증."""
    # disabled
    y, r = primary_server._resolve_year_sync(
        is_saatchi_warm=False, manual_year=2020,
        artwork_id="x", artwork_url=None,
    )
    assert (y, r) == (None, "disabled")
    # manual + cache seed
    y, r = primary_server._resolve_year_sync(
        is_saatchi_warm=True, manual_year=2020, artwork_id="aw_seeded",
        artwork_url=None,
    )
    assert y == 2020
    assert r == "manual_seed_cache_write"
    # manual without artwork_id
    y, r = primary_server._resolve_year_sync(
        is_saatchi_warm=True, manual_year=2018, artwork_id=None, artwork_url=None,
    )
    assert (y, r) == (2018, "manual")
