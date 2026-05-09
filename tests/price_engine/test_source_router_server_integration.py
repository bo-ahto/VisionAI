"""PR2A.5 Server integration tests (router default OFF / backward compat).

End-to-end smoke: server module imports + global state initialization +
schema 정합 (additive routing fields).

Full FastAPI integration tests (predict / batch endpoint with mock predictor)
영역 의 의무 영역 의 의무 = PR2B 의무.
"""

from __future__ import annotations

import os

import pytest


def test_server_module_imports():
    """server module 영역 의 의무 영역 의 의무 import 정합."""
    from visionai.price_engine.api import primary_server  # noqa: F401


def test_default_router_mode_is_off():
    """기본 영역 의 의무 영역 의 의무 = SOURCE_ROUTER_MODE=off (backward compat)."""
    # Env unset 영역 의 의무 영역 의 의무 default off
    if "SOURCE_ROUTER_MODE" in os.environ:
        del os.environ["SOURCE_ROUTER_MODE"]
    from visionai.price_engine.api.source_router import SourceRouter
    router = SourceRouter()
    assert router.mode == "off"
    assert router.percent == 0
    assert router.rule_version == "v1"


def test_router_globals_initialized():
    """primary_server module _router + _predictor 정합 (default OFF)."""
    from visionai.price_engine.api import primary_server
    assert primary_server._router is not None
    assert primary_server._predictor is not None
    # default OFF: _predictor = _router.unified
    assert primary_server._predictor is primary_server._router.unified


def test_predictresponse_schema_routing_fields_optional():
    """ModelInfo schema routing fields = optional (additive)."""
    from visionai.price_engine.api.primary_schemas import ModelInfo

    # Backward compat: routing fields 영역 의 의무 영역 의 의무 미지정 = None
    info_legacy = ModelInfo(
        model_type="catboost_v3_filtered_tuned",
        is_known_artist=True,
        training_count=10,
    )
    assert info_legacy.routing_source is None
    assert info_legacy.routing_reason is None
    assert info_legacy.routed_variant is None

    # PR2A.5: routing fields 영역 의 의무 영역 의 의무 명시 정합
    info_routed = ModelInfo(
        model_type="catboost_source_conditional_v1_artsy",
        is_known_artist=True,
        training_count=10,
        routing_source="artsy",
        routing_reason="matched_artsy",
        routed_variant="source_conditional_v1_artsy",
    )
    assert info_routed.routing_source == "artsy"


def test_modelinforesponse_schema_router_fields_optional():
    """ModelInfoResponse 영역 의 의무 영역 의 의무 router fields = optional."""
    from visionai.price_engine.api.primary_schemas import ModelInfoResponse

    # Backward compat
    legacy = ModelInfoResponse(
        model_version="v3-tuned",
        training_count=28376,
        artist_count=1551,
        mdape_groupkfold=39.4,
        mdape_kfold=9.7,
        features_count=32,
    )
    assert legacy.router_mode is None
    assert legacy.default_variant is None

    # PR2A.5: router fields 명시
    routed = ModelInfoResponse(
        model_version="v3-tuned",
        training_count=28376,
        artist_count=1551,
        mdape_groupkfold=39.4,
        mdape_kfold=9.7,
        features_count=32,
        router_mode="off",
        default_variant="v3_filtered_tuned",
        available_variants=["v3_filtered_tuned", "source_conditional_v1_artsy",
                            "source_conditional_v1_saatchi"],
    )
    assert routed.router_mode == "off"
    assert "source_conditional_v1_artsy" in routed.available_variants


def test_supported_variants_contains_source_conditional():
    """SUPPORTED_VARIANTS 영역 의 의무 영역 의 의무 source-conditional 추가 정합."""
    from visionai.price_engine.api.primary_predictor import SUPPORTED_VARIANTS
    assert "source_conditional_v1_artsy" in SUPPORTED_VARIANTS
    assert "source_conditional_v1_saatchi" in SUPPORTED_VARIANTS
    # Backward compat: 기존 variant 영역 의 의무 영역 의 의무 변경 X
    assert "v3_filtered_tuned" in SUPPORTED_VARIANTS
    assert "v3_5_v_year_saatchi_warm" in SUPPORTED_VARIANTS

    # Schema 정합: prefix / cb_features / expected_target
    artsy = SUPPORTED_VARIANTS["source_conditional_v1_artsy"]
    assert artsy["prefix"] == "source_conditional_v1_artsy"
    assert artsy["expected_target"] == "source_conditional_v1_artsy"
    assert "ho_power" in artsy["cb_features"]  # 32 base features


def test_router_default_off_no_artsy_saatchi_predictors():
    """default OFF: artsy / saatchi predictor = None (memory 절약)."""
    if "SOURCE_ROUTER_MODE" in os.environ:
        del os.environ["SOURCE_ROUTER_MODE"]
    from visionai.price_engine.api.source_router import SourceRouter
    router = SourceRouter()
    assert router.artsy is None
    assert router.saatchi is None


def test_router_invalid_mode_fails_init():
    """Invalid SOURCE_ROUTER_MODE → RuntimeError (fail-closed)."""
    os.environ["SOURCE_ROUTER_MODE"] = "invalid_mode"
    try:
        from visionai.price_engine.api.source_router import SourceRouter
        with pytest.raises(RuntimeError, match="Invalid SOURCE_ROUTER_MODE"):
            SourceRouter()
    finally:
        del os.environ["SOURCE_ROUTER_MODE"]


def test_router_dispatch_off_returns_unified_predictor():
    """OFF mode dispatch: 모든 row → unified predictor."""
    if "SOURCE_ROUTER_MODE" in os.environ:
        del os.environ["SOURCE_ROUTER_MODE"]
    from visionai.price_engine.api.source_router import SourceRouter
    router = SourceRouter()
    pred, decision = router.dispatch(
        is_matched=True, match_profile_source="artsy", cohort_key="any"
    )
    assert pred is router.unified
    assert decision.routing_source == "unified"
    assert decision.routing_reason == "router_off"


def test_router_dispatch_active_mode_artsy_fail_closed():
    """Active mode + artsy 누락 → RuntimeError (fail-closed)."""
    os.environ["SOURCE_ROUTER_MODE"] = "on"
    try:
        from visionai.price_engine.api.source_router import SourceRouter
        router = SourceRouter()  # artsy + saatchi load 영역 의 의무 영역 의 의무 X
        # router.artsy = None (load_models 미호출 / load 영역 의 의무 영역 의 의무 영역 의 의무 X)
        with pytest.raises(RuntimeError, match="artsy predictor not loaded"):
            router.dispatch(is_matched=True, match_profile_source="artsy")
    finally:
        del os.environ["SOURCE_ROUTER_MODE"]
