"""v3.6 PR8c: endpoint-level integration test.

코덱스 PR8 review P2 후속: 단위 helper test 가 실 endpoint 미커버 → /predict
async 함수 직접 호출 테스트로 cohort 결정 + year resolution + 로깅 계약 검증.

비-endpoint 의존성 (DB matcher / predictor / SHAP) 은 module-level monkeypatch.
실 ML 모델 / artifact 없이 server 결정 로직만 격리 검증.
"""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from visionai.price_engine.api import artwork_year_cache as ayc
from visionai.price_engine.api import primary_server
from visionai.price_engine.api.artist_matcher import MatchResult
from visionai.price_engine.api.primary_schemas import PredictRequest


@pytest.fixture(autouse=True)
def reset_state():
    ayc.reset_global_cache()
    ayc.reset_global_gate()
    yield
    ayc.reset_global_cache()
    ayc.reset_global_gate()


def _make_predictor_mock(*, warm_slugs: set[str], cb_features_len: int = 35):
    pred = MagicMock()
    pred.is_warm_artist = lambda s: s in warm_slugs
    pred.cb_features = ["f"] * cb_features_len
    pred.predict.return_value = {
        "price_krw": 1_000_000,
        "price_usd": 750.0,
        "price_range_low": 800_000,
        "price_range_high": 1_200_000,
        "confidence_grade": "B",
        "model_type": "xgboost_v3_5_v_year_saatchi_warm",  # SHAP 분기 우회
        "is_known_artist": True,
        "training_count": 12,
        "margin": 0.15,
    }
    return pred


def _make_matcher_mock(match: MatchResult | None):
    m = MagicMock()
    m.match.return_value = match
    return m


def _make_request(**overrides) -> PredictRequest:
    base = dict(
        artist_name="김작가",
        width_cm=50.0,
        height_cm=50.0,
        medium="oil on canvas",
        target_market="gallery",
        title="title",
    )
    base.update(overrides)
    return PredictRequest(**base)


def _saatchi_match(slug: str = "kim_artist") -> MatchResult:
    return MatchResult(
        artist_id=42,
        name="Kim",
        score=95.0,
        training_count=12,
        source="saatchi",
        profile={"source": "saatchi", "birth_year": 1980},
        slug=slug,
    )


def _artsy_match(slug: str = "kim_artsy") -> MatchResult:
    return MatchResult(
        artist_id=99,
        name="Kim",
        score=90.0,
        training_count=8,
        source="artsy",
        profile={"source": "artsy", "birth_year": 1980},
        slug=slug,
    )


def _run_predict(req: PredictRequest):
    """primary_server.predict async 함수 직접 호출."""
    return asyncio.run(primary_server.predict(req))


def _patch_server(predictor, matcher):
    """공통 patch — 실 ML 의존성 우회."""
    return [
        patch.object(primary_server, "_predictor", predictor),
        patch.object(primary_server, "_matcher", matcher),
        patch.object(primary_server, "_log_prediction"),
        patch.object(primary_server, "_find_matched_artworks", return_value=[]),
        patch.object(primary_server, "_get_artist_history", return_value=None),
    ]


def _enter_all(ctxs):
    return [c.__enter__() for c in ctxs]


def _exit_all(ctxs):
    for c in ctxs:
        c.__exit__(None, None, None)


# ---- T1: 비-saatchi (artsy) 매칭 → cohort=False, route='disabled' ----


def test_endpoint_artsy_match_cohort_false_route_disabled():
    pred = _make_predictor_mock(warm_slugs={"kim_artsy"})
    matcher = _make_matcher_mock(_artsy_match("kim_artsy"))
    ctxs = _patch_server(pred, matcher)
    _enter_all(ctxs)
    try:
        req = _make_request(year_made=2020, artwork_id="123")
        _run_predict(req)
        # _log_prediction 호출 args 검증
        log_call = primary_server._log_prediction.call_args[0][0]
        assert log_call["is_saatchi_warm"] is False
        assert log_call["year_made_route"] == "disabled"
        assert log_call["year_made_used"] is None
    finally:
        _exit_all(ctxs)


# ---- T2: saatchi + cold artist → cohort=False ----


def test_endpoint_saatchi_cold_artist_cohort_false():
    pred = _make_predictor_mock(warm_slugs={"other_warm"})
    matcher = _make_matcher_mock(_saatchi_match("kim_cold"))
    ctxs = _patch_server(pred, matcher)
    _enter_all(ctxs)
    try:
        req = _make_request(year_made=2019)
        _run_predict(req)
        log_call = primary_server._log_prediction.call_args[0][0]
        assert log_call["is_saatchi_warm"] is False
        assert log_call["year_made_route"] == "disabled"
    finally:
        _exit_all(ctxs)


# ---- T3: saatchi + warm + manual year + artwork_id → manual_seed_cache_write ----


def test_endpoint_saatchi_warm_manual_with_id_seeds_cache():
    pred = _make_predictor_mock(warm_slugs={"kim_artist"})
    matcher = _make_matcher_mock(_saatchi_match("kim_artist"))
    ctxs = _patch_server(pred, matcher)
    _enter_all(ctxs)
    try:
        req = _make_request(
            year_made=2018,
            artwork_id="9876",
            artwork_url="https://saatchiart.com/x/y/9876/view",
        )
        _run_predict(req)
        log_call = primary_server._log_prediction.call_args[0][0]
        assert log_call["is_saatchi_warm"] is True
        assert log_call["year_made_route"] == "manual_seed_cache_write"
        assert log_call["year_made_used"] == 2018
        # cache 에 실제 등록 검증
        cached_year, cached_route = ayc.get_global_cache().get("9876")
        assert cached_year == 2018
        assert cached_route == "cache_hit"
    finally:
        _exit_all(ctxs)


# ---- T4: saatchi + warm + manual year (no artwork_id) → 'manual' ----


def test_endpoint_saatchi_warm_manual_without_id_route_manual():
    pred = _make_predictor_mock(warm_slugs={"kim_artist"})
    matcher = _make_matcher_mock(_saatchi_match("kim_artist"))
    ctxs = _patch_server(pred, matcher)
    _enter_all(ctxs)
    try:
        req = _make_request(year_made=2015)
        _run_predict(req)
        log_call = primary_server._log_prediction.call_args[0][0]
        assert log_call["is_saatchi_warm"] is True
        assert log_call["year_made_route"] == "manual"
        assert log_call["year_made_used"] == 2015
        assert ayc.get_global_cache().stats()["size"] == 0
    finally:
        _exit_all(ctxs)


# ---- T5: saatchi + warm + cache hit → 'cache_hit', fetch 호출 X ----


def test_endpoint_saatchi_warm_cache_hit_no_fetch():
    pred = _make_predictor_mock(warm_slugs={"kim_artist"})
    matcher = _make_matcher_mock(_saatchi_match("kim_artist"))
    ayc.seed_artwork_year("seeded_aw", 2017,
                          artwork_url="https://saatchiart.com/x/y/seeded_aw/view")
    ctxs = _patch_server(pred, matcher)
    _enter_all(ctxs)
    try:
        req = _make_request(artwork_id="seeded_aw")  # year_made 없음
        _run_predict(req)
        log_call = primary_server._log_prediction.call_args[0][0]
        assert log_call["year_made_route"] == "cache_hit"
        assert log_call["year_made_used"] == 2017
    finally:
        _exit_all(ctxs)


# ---- T6: saatchi + warm + gate 차단 → 'rate_limited' (fetch 미실행) ----


def test_endpoint_saatchi_warm_rate_limited_when_gate_blocks():
    pred = _make_predictor_mock(warm_slugs={"kim_artist"})
    matcher = _make_matcher_mock(_saatchi_match("kim_artist"))
    # gate 5 concurrent 채워서 차단
    gate = ayc.get_global_gate()
    for i in range(ayc.FETCH_CONCURRENT_MAX):
        gate.try_acquire(f"hold{i}")
    ctxs = _patch_server(pred, matcher)
    _enter_all(ctxs)
    try:
        req = _make_request(artwork_id="999",
                            artwork_url="https://saatchiart.com/x/y/999/view")
        _run_predict(req)
        log_call = primary_server._log_prediction.call_args[0][0]
        assert log_call["is_saatchi_warm"] is True
        assert log_call["year_made_route"] == "rate_limited"
        assert log_call["year_made_used"] is None
    finally:
        _exit_all(ctxs)


# ---- T7: 비매칭 (matcher None) + external_collector 도 saatchi 라도 cohort=False ----


def test_endpoint_unmatched_cohort_false_even_if_external_saatchi():
    """external_collector 로 채워진 profile.source 는 비권위. is_matched=False
    이므로 cohort=False (v3.5 step 2 §2.3 cohort authority)."""
    pred = _make_predictor_mock(warm_slugs={"kim_artist"})
    matcher = _make_matcher_mock(None)  # 미매칭
    ctxs = _patch_server(pred, matcher)
    # external_collector 가 saatchi profile 반환하는 시나리오
    ext_patch = patch.object(
        primary_server, "external_collector",
        MagicMock(collect=MagicMock(return_value=({"source": "saatchi"}, ["saatchi"]))),
    )
    _enter_all(ctxs)
    ext_patch.__enter__()
    try:
        req = _make_request(year_made=2020, artwork_id="123")
        _run_predict(req)
        log_call = primary_server._log_prediction.call_args[0][0]
        # is_matched=False → cohort=False (external 비권위)
        assert log_call["is_saatchi_warm"] is False
        assert log_call["year_made_route"] == "disabled"
    finally:
        ext_patch.__exit__(None, None, None)
        _exit_all(ctxs)


# ---- T8: build_features 가 받는 parameter 정합 ----


def test_endpoint_build_features_called_with_cohort_and_year():
    """cohort=True 면 build_features 가 is_saatchi_warm=True + year_made=실제값 으로 호출."""
    pred = _make_predictor_mock(warm_slugs={"kim_artist"})
    matcher = _make_matcher_mock(_saatchi_match("kim_artist"))
    ctxs = _patch_server(pred, matcher)
    _enter_all(ctxs)
    bf_spy = patch.object(primary_server, "build_features",
                          wraps=primary_server.build_features)
    bf_mock = bf_spy.__enter__()
    try:
        req = _make_request(year_made=2019)
        _run_predict(req)
        bf_kwargs = bf_mock.call_args.kwargs
        assert bf_kwargs.get("is_saatchi_warm") is True
        assert bf_kwargs.get("year_made") == 2019
    finally:
        bf_spy.__exit__(None, None, None)
        _exit_all(ctxs)
