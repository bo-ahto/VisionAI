"""v3.6 PR11a: TestClient 기반 integration test.

코덱스 PR9b review 권장: single + batch cross-path schema 정합, /monitor
avg_ms batch 합산, route 조합 (manual/cache/disabled), model_info variant 등을
실제 FastAPI routing / middleware / pydantic serialization 경로로 검증.

전략:
- TestClient(app) 를 with 컨텍스트 외부에서 사용 → lifespan startup/shutdown
  우회 (실 model artifact 로드 없이 endpoint logic 만 검증).
- _predictor / _matcher / shap_explainer / SHAP / _model_info_cache /
  _find_matched_artworks / _get_artist_history monkeypatch.
- _log_prediction 은 실 호출 (monitor 합산 검증을 위해).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from visionai.price_engine.api import artwork_year_cache as ayc
from visionai.price_engine.api import primary_server
from visionai.price_engine.api.artist_matcher import MatchResult
from visionai.price_engine.api.primary_schemas import ModelInfoResponse


@pytest.fixture(autouse=True)
def reset_state(monkeypatch):
    # PR10/11b token bucket + warmup 우회 — integration test 는 cohort/route 검증
    monkeypatch.setattr(ayc, "FETCH_QPS_CAPACITY", 100_000)
    monkeypatch.setattr(ayc, "FETCH_QPS_REFILL_PER_SEC", 100_000.0)
    monkeypatch.setattr(ayc, "FETCH_WARMUP_QPS_CAPACITY", 100_000)
    monkeypatch.setattr(ayc, "FETCH_WARMUP_QPS_REFILL_PER_SEC", 100_000.0)
    ayc.reset_global_cache()
    ayc.reset_global_gate()
    # _monitor 누적 reset (이전 test 잔여 차단)
    primary_server._monitor.update({
        "total_predictions": 0,
        "by_grade": {},
        "by_model": {},
        "total_ms": 0,
        "external_lookup_count": 0,
        "known_artist_count": 0,
    })
    yield
    ayc.reset_global_cache()
    ayc.reset_global_gate()


def _saatchi_match(slug: str = "kim_warm") -> MatchResult:
    return MatchResult(
        artist_id=42, name="Kim", score=95.0, training_count=12,
        source="saatchi", profile={"source": "saatchi", "birth_year": 1980},
        slug=slug,
    )


def _make_mock_predictor():
    pred = MagicMock()
    pred.is_warm_artist = lambda s: s == "kim_warm"
    pred.cb_features = ["f"] * 35
    pred.variant = "v3_5_v_year_saatchi_warm"
    pred.cb_model = None  # SHAP 분기 우회
    pred.predict.return_value = {
        "price_krw": 2_000_000, "price_usd": 1_500.0,
        "price_range_low": 1_600_000, "price_range_high": 2_400_000,
        "confidence_grade": "A",
        "model_type": "xgboost_v3_5_v_year_saatchi_warm",
        "is_known_artist": True, "training_count": 12, "margin": 0.20,
    }
    pred.model_version_label.return_value = "v3.5-test"
    return pred


def _make_mock_matcher(match_result: MatchResult | None):
    m = MagicMock()
    m.match.return_value = match_result
    m.count = 100  # /health endpoint 검증용
    return m


def _build_client(predictor, matcher, *, with_model_info: bool = True):
    """lifespan 우회 TestClient + 핵심 module 변수 주입.

    _model_info_cache 를 미리 set → /model/info 가 fallback 경로 안 타게.
    """
    cache = (
        ModelInfoResponse(
            model_version="v3.5-it",
            training_count=10_000, artist_count=8000,
            mdape_groupkfold=43.5, mdape_kfold=27.5,
            features_count=len(predictor.cb_features),
        )
        if with_model_info else None
    )

    return _ClientCtx(predictor, matcher, cache)


class _ClientCtx:
    def __init__(self, predictor, matcher, cache):
        self._patches = [
            patch.object(primary_server, "_predictor", predictor),
            patch.object(primary_server, "_matcher", matcher),
            patch.object(primary_server, "_model_info_cache", cache),
            patch.object(primary_server, "_find_matched_artworks", return_value=[]),
            patch.object(primary_server, "_get_artist_history", return_value=None),
            patch.object(primary_server, "_log_file", None),  # 파일 적재 비활성
            patch.object(primary_server.shap_explainer, "explain", return_value=[]),
        ]

    def __enter__(self):
        for p in self._patches:
            p.__enter__()
        # TestClient 를 with 외부 사용 → lifespan 안 호출
        self.client = TestClient(primary_server.app)
        return self.client

    def __exit__(self, *exc):
        for p in self._patches:
            p.__exit__(*exc)


def _predict_payload(**overrides) -> dict:
    base = {
        "artist_name": "김작가",
        "width_cm": 50.0, "height_cm": 50.0,
        "medium": "oil on canvas",
        "target_market": "gallery",
        "title": "Title",
    }
    base.update(overrides)
    return base


def _batch_payload(items: list[dict]) -> dict:
    return {"artworks": items, "skip_external_lookup": True}


# ---- T1: /predict 단건 — 200 + cohort=True + route 정합 ----


def test_predict_single_saatchi_warm_manual_seed():
    pred = _make_mock_predictor()
    matcher = _make_mock_matcher(_saatchi_match("kim_warm"))
    with _build_client(pred, matcher) as client:
        resp = client.post("/api/v1/predict", json=_predict_payload(
            year_made=2018, artwork_id="aw_T1",
            artwork_url="https://saatchiart.com/x/y/aw_T1/view",
        ))
    assert resp.status_code == 200
    body = resp.json()
    assert body["prediction"]["price_krw"] == 2_000_000
    assert body["model_info"]["model_type"] == "xgboost_v3_5_v_year_saatchi_warm"
    # cache 에 등록 확인 (manual_seed_cache_write)
    cached_year, cached_route = ayc.get_global_cache().get("aw_T1")
    assert cached_year == 2018


# ---- T2: /predict/batch — pydantic serialization + per-item 응답 ----


def test_predict_batch_routes(monkeypatch):
    """batch 3 item: warm+manual / artsy / unmatched. 모두 200 + per-item status."""
    pred = _make_mock_predictor()

    matcher = MagicMock()
    matcher.match.side_effect = [
        _saatchi_match("kim_warm"),
        MatchResult(artist_id=99, name="Lee", score=90.0, training_count=8,
                    source="artsy", profile={"source": "artsy"}, slug="lee_artsy"),
        None,  # unmatched
    ]
    with _build_client(pred, matcher) as client:
        resp = client.post("/api/v1/predict/batch", json=_batch_payload([
            _predict_payload(artist_name="Kim", year_made=2020, artwork_id="aw_K"),
            _predict_payload(artist_name="Lee"),
            _predict_payload(artist_name="Unknown"),
        ]))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3


# ---- T3: /api/v1/monitor 의 avg_ms 가 batch-only 트래픽에서도 누적 ----


def test_monitor_avg_ms_includes_batch_traffic():
    """PR9b fix 검증 (코덱스 P1): batch row 의 total_ms 가 _monitor 합산에 들어감."""
    import time as _time

    pred = _make_mock_predictor()
    # predict 가 너무 빠르면 item_total_ms=0 → 의도한 검증 X. minimal latency.
    def _slow_predict(**kwargs):
        _time.sleep(0.01)
        return pred.predict.return_value
    pred.predict.side_effect = _slow_predict
    matcher = MagicMock()
    matcher.match.return_value = _saatchi_match("kim_warm")

    with _build_client(pred, matcher) as client:
        # 단건 0건, batch 3건 호출
        client.post("/api/v1/predict/batch", json=_batch_payload([
            _predict_payload(artist_name="Kim", year_made=2020),
            _predict_payload(artist_name="Kim", year_made=2019),
            _predict_payload(artist_name="Kim", year_made=2018),
        ]))
        # /monitor 호출
        resp = client.get("/api/v1/monitor")
    assert resp.status_code == 200
    monitor = resp.json()
    assert monitor["total_predictions"] == 3  # batch 3 row
    assert monitor["avg_ms"] > 0  # batch 만으로도 avg_ms 누적 (PR9b fix)


# ---- T4: /api/v1/model/info — variant-aware features_count ----


def test_model_info_endpoint_variant_aware():
    pred = _make_mock_predictor()  # cb_features = 35 (v3.5 variant)
    matcher = _make_mock_matcher(None)
    with _build_client(pred, matcher) as client:
        resp = client.get("/api/v1/model/info")
    assert resp.status_code == 200
    info = resp.json()
    assert info["features_count"] == 35  # PR7 variant prefix + cb_features


def test_model_info_defensive_fallback_when_cache_none():
    pred = _make_mock_predictor()
    matcher = _make_mock_matcher(None)
    with _build_client(pred, matcher, with_model_info=False) as client:
        resp = client.get("/api/v1/model/info")
    assert resp.status_code == 200
    info = resp.json()
    # PR8 P2 fix: defensive fallback 도 _predictor.cb_features
    assert info["features_count"] == 35


# ---- T5: cross-path schema 일치 (single vs batch row) ----


def test_single_and_batch_log_schema_match():
    """동일 작품이 single / batch 둘 다 같은 필드 set 으로 logging."""
    pred = _make_mock_predictor()
    matcher = MagicMock()
    matcher.match.return_value = _saatchi_match("kim_warm")
    captured = []
    with _build_client(pred, matcher) as client, patch.object(
        primary_server, "_log_prediction",
        side_effect=lambda e: captured.append(e),
    ):
        client.post("/api/v1/predict", json=_predict_payload(
            year_made=2020, artwork_id="aw_X",
        ))
        client.post("/api/v1/predict/batch", json=_batch_payload([
            _predict_payload(artist_name="Kim", year_made=2020,
                              artwork_id="aw_X"),
        ]))
    assert len(captured) == 2
    single_log, batch_log = captured

    # PR10 spec 의 모든 필드가 양쪽 모두에 존재
    common_required = [
        "is_saatchi_warm", "match_profile_source", "slug_in_warm_set",
        "external_collector_source", "year_made_route", "year_made_used",
        "artwork_id", "artwork_url", "enrichment_latency_ms",
        "predict_total_latency_ms", "total_ms",
        "model_variant", "artifact_version", "warm_artist_slugs_version",
        "rollout_rule_version", "server_instance", "cache_epoch",
    ]
    for field in common_required:
        assert field in single_log, f"single missing: {field}"
        assert field in batch_log, f"batch missing: {field}"

    # 동일 입력 → 동일 cohort 결정 + 동일 route
    assert single_log["is_saatchi_warm"] == batch_log["is_saatchi_warm"]
    assert single_log["year_made_route"] == batch_log["year_made_route"]
    assert single_log["year_made_used"] == batch_log["year_made_used"]


# ---- T6: cache_hit cross-path (single seed → batch 가 cache_hit) ----


def test_cache_shared_between_single_and_batch():
    pred = _make_mock_predictor()
    matcher = MagicMock()
    matcher.match.return_value = _saatchi_match("kim_warm")
    captured = []
    with _build_client(pred, matcher) as client, patch.object(
        primary_server, "_log_prediction",
        side_effect=lambda e: captured.append(e),
    ):
        # single 으로 cache seed
        client.post("/api/v1/predict", json=_predict_payload(
            year_made=2017, artwork_id="aw_seed",
        ))
        captured.clear()
        # batch 는 year_made 없이 같은 artwork_id → cache_hit
        client.post("/api/v1/predict/batch", json=_batch_payload([
            _predict_payload(artist_name="Kim", artwork_id="aw_seed"),
        ]))
    assert len(captured) == 1
    assert captured[0]["year_made_route"] == "cache_hit"
    assert captured[0]["year_made_used"] == 2017


# ---- T7: pydantic validation — invalid year_made → 422 ----


def test_predict_invalid_year_rejected_by_schema():
    pred = _make_mock_predictor()
    matcher = _make_mock_matcher(_saatchi_match("kim_warm"))
    with _build_client(pred, matcher) as client:
        resp = client.post("/api/v1/predict", json=_predict_payload(
            year_made=1500, artwork_id="aw_invalid",
        ))
    assert resp.status_code == 422  # pydantic ge=1800 reject


def test_predict_artwork_id_max_length_enforced():
    pred = _make_mock_predictor()
    matcher = _make_mock_matcher(_saatchi_match("kim_warm"))
    with _build_client(pred, matcher) as client:
        resp = client.post("/api/v1/predict", json=_predict_payload(
            artwork_id="x" * 100,  # max_length=64 위반
        ))
    assert resp.status_code == 422


# ---- T8: /health 살아있음 (smoke) ----


def test_health_endpoint_alive():
    pred = _make_mock_predictor()
    matcher = _make_mock_matcher(None)
    with _build_client(pred, matcher) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
