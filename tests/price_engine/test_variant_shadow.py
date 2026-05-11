"""Tests for PR-WARM-B Stage 3 옵션 A — VARIANT_SHADOW env var integration.

Coverage:
- _init_variant_shadow_predictor() env var behavior (off / valid / invalid / same-as-primary)
- _run_variant_shadow_inference() fail-open + result format
- predict_logs schema: shadow_variant + shadow_prediction_price_krw 필드
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))


def test_variant_shadow_off_when_env_unset(monkeypatch):
    """VARIANT_SHADOW env var 미설정 → _variant_shadow_predictor=None."""
    from visionai.price_engine.api import primary_server
    monkeypatch.delenv("VARIANT_SHADOW", raising=False)
    primary_server._init_variant_shadow_predictor(Path("/tmp/dummy"))
    assert primary_server._variant_shadow_predictor is None


def test_variant_shadow_off_when_empty_env(monkeypatch):
    """VARIANT_SHADOW=빈 문자열 → off."""
    from visionai.price_engine.api import primary_server
    monkeypatch.setenv("VARIANT_SHADOW", "")
    primary_server._init_variant_shadow_predictor(Path("/tmp/dummy"))
    assert primary_server._variant_shadow_predictor is None


def test_variant_shadow_off_when_equals_primary(monkeypatch):
    """VARIANT_SHADOW == primary variant → no-op / shadow disabled (avoid duplicate)."""
    from visionai.price_engine.api import primary_server
    monkeypatch.setenv("VARIANT_SHADOW", primary_server._predictor.variant)
    primary_server._init_variant_shadow_predictor(Path("/tmp/dummy"))
    assert primary_server._variant_shadow_predictor is None


def test_variant_shadow_off_when_invalid_variant(monkeypatch):
    """VARIANT_SHADOW=unknown_variant → fail-open / shadow disabled / warning log."""
    from visionai.price_engine.api import primary_server
    monkeypatch.setenv("VARIANT_SHADOW", "unknown_variant_xyz")
    primary_server._init_variant_shadow_predictor(Path("/tmp/dummy"))
    assert primary_server._variant_shadow_predictor is None


def test_variant_shadow_load_failure_fail_open(monkeypatch):
    """VARIANT_SHADOW valid BUT load fail (missing artifact) → fail-open / shadow disabled."""
    from visionai.price_engine.api import primary_server
    # b_warm variant valid in SUPPORTED_VARIANTS / 그러나 model_dir 가짜 → load 실패
    monkeypatch.setenv("VARIANT_SHADOW", "v3_filtered_tuned_b_warm")
    fake_dir = Path("/nonexistent/path/that/does/not/exist")
    primary_server._init_variant_shadow_predictor(fake_dir)
    # load 실패 → shadow None (fail-open)
    assert primary_server._variant_shadow_predictor is None


def test_run_variant_shadow_inference_off_returns_empty():
    """_variant_shadow_predictor=None → 빈 dict 반환."""
    from visionai.price_engine.api import primary_server
    original = primary_server._variant_shadow_predictor
    primary_server._variant_shadow_predictor = None
    try:
        result = primary_server._run_variant_shadow_inference(
            features={}, is_matched=False, training_count=0,
            target_market="online", has_manual_profile=False, artist_slug=None,
        )
        assert result == {}
    finally:
        primary_server._variant_shadow_predictor = original


def test_run_variant_shadow_inference_success_format():
    """Shadow predictor 성공 시 shadow_variant + shadow_prediction_price_krw 필드 반환."""
    from visionai.price_engine.api import primary_server
    original = primary_server._variant_shadow_predictor
    mock_predictor = MagicMock()
    mock_predictor.variant = "v3_filtered_tuned_b_warm"
    mock_predictor.predict.return_value = {
        "price_krw": 1234567,
        "price_range_low": 1100000,
        "price_range_high": 1400000,
    }
    primary_server._variant_shadow_predictor = mock_predictor
    try:
        result = primary_server._run_variant_shadow_inference(
            features={"ho": 10}, is_matched=True, training_count=5,
            target_market="online", has_manual_profile=False, artist_slug="kim",
        )
        # R1 P1 amendment: variant_shadow_* prefix (PR2B-prereq.1 shadow_* collision 회피)
        assert result == {
            "variant_shadow_variant": "v3_filtered_tuned_b_warm",
            "variant_shadow_prediction_price_krw": 1234567,
        }
        # predict was called with all expected kwargs
        mock_predictor.predict.assert_called_once()
        call_kwargs = mock_predictor.predict.call_args.kwargs
        assert call_kwargs["features"] == {"ho": 10}
        assert call_kwargs["is_matched"] is True
        assert call_kwargs["artist_slug"] == "kim"
    finally:
        primary_server._variant_shadow_predictor = original


def test_run_variant_shadow_inference_predict_exception_fail_open():
    """Shadow predict 예외 → fail-open / shadow_variant_error 필드 / primary 영향 X."""
    from visionai.price_engine.api import primary_server
    original = primary_server._variant_shadow_predictor
    mock_predictor = MagicMock()
    mock_predictor.variant = "v3_filtered_tuned_b_warm"
    mock_predictor.predict.side_effect = RuntimeError("predict failed inside")
    primary_server._variant_shadow_predictor = mock_predictor
    try:
        result = primary_server._run_variant_shadow_inference(
            features={}, is_matched=False, training_count=0,
            target_market="online", has_manual_profile=False, artist_slug=None,
        )
        # R1 P1 amendment: variant_shadow_error 명시 (shadow_* collision 회피)
        assert "variant_shadow_error" in result
        assert "predict failed inside" in result["variant_shadow_error"]
        # primary 영역 의 의무 영향 X (no raise)
    finally:
        primary_server._variant_shadow_predictor = original


def test_both_shadow_modes_no_log_key_collision():
    """R1 P1 amendment: 둘 다 활성화 시 두 shadow 결과 모두 log payload 보존 (key collision X)."""
    from visionai.price_engine.api import primary_server
    # variant shadow mock
    original_shadow = primary_server._variant_shadow_predictor
    mock_predictor = MagicMock()
    mock_predictor.variant = "v3_filtered_tuned_b_warm"
    mock_predictor.predict.return_value = {"price_krw": 555, "price_range_low": 500,
                                            "price_range_high": 600}
    primary_server._variant_shadow_predictor = mock_predictor
    try:
        # 둘 다 호출 / 결과 spread 시 collision 없는지 확인
        # PR2B-prereq.1 shadow (mock simulate_route_on + predictor)
        s_shadow = {
            "shadow_routed_variant": "source_conditional_v1_artsy",
            "shadow_routing_source": "router_decision",
            "shadow_routing_reason": "artsy_matched",
            "shadow_prediction_price_krw": 777,  # PR2B-prereq.1 결과
        }
        # PR-WARM-B 옵션 A variant shadow
        v_shadow = primary_server._run_variant_shadow_inference(
            features={}, is_matched=True, training_count=10,
            target_market="online", has_manual_profile=False, artist_slug="test",
        )
        # Log payload simulation
        log_entry = {**s_shadow, **v_shadow}
        # 둘 다 unique key
        assert "shadow_prediction_price_krw" in log_entry  # PR2B-prereq.1
        assert log_entry["shadow_prediction_price_krw"] == 777
        assert "variant_shadow_prediction_price_krw" in log_entry  # PR-WARM-B 옵션 A
        assert log_entry["variant_shadow_prediction_price_krw"] == 555
        assert "shadow_routed_variant" in log_entry
        assert "variant_shadow_variant" in log_entry
        assert log_entry["shadow_routed_variant"] == "source_conditional_v1_artsy"
        assert log_entry["variant_shadow_variant"] == "v3_filtered_tuned_b_warm"
    finally:
        primary_server._variant_shadow_predictor = original_shadow


def test_run_variant_shadow_inference_orthogonal_to_source_router_shadow():
    """PR-WARM-B 옵션 A는 PR2B-prereq.1 source_router shadow와 직교 / 둘 다 활성화 가능."""
    from visionai.price_engine.api import primary_server
    # Mock: 옵션 A 활성 + source_router mode=off (source_router shadow inactive)
    original_shadow = primary_server._variant_shadow_predictor
    original_router_mode = primary_server._router.mode
    mock_predictor = MagicMock()
    mock_predictor.variant = "v3_filtered_tuned_b_warm"
    mock_predictor.predict.return_value = {"price_krw": 999, "price_range_low": 800,
                                            "price_range_high": 1200}
    primary_server._variant_shadow_predictor = mock_predictor
    primary_server._router.mode = "off"
    try:
        # 옵션 A 활성 / mode=off
        v_shadow = primary_server._run_variant_shadow_inference(
            features={}, is_matched=True, training_count=10,
            target_market="online", has_manual_profile=False, artist_slug="test",
        )
        assert v_shadow.get("variant_shadow_variant") == "v3_filtered_tuned_b_warm"
        # source_router shadow off → _run_shadow_inference 빈 dict
        s_shadow = primary_server._run_shadow_inference(
            features={}, is_matched=True, match_profile_source=None, training_count=10,
            target_market="online", has_manual_profile=False, artist_slug="test",
        )
        assert s_shadow == {}
    finally:
        primary_server._variant_shadow_predictor = original_shadow
        primary_server._router.mode = original_router_mode
