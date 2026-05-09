"""PR2B-prereq.1 Shadow dual-logging tests.

Coverage:
- simulate_route_on() helper
- _run_shadow_inference() (mode=off / shadow / on)
- _log_prediction count_toward_monitor 분기
- DDL migration script 정합
- ETL whitelist additive
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DDL_FILE = REPO_ROOT / "monitoring/sql/002_predict_logs_router_columns.sql"


class TestSimulateRouteOn:
    def test_simulate_route_on_artsy(self):
        """simulate_route_on = decide_route(mode='on')."""
        from visionai.price_engine.api.source_router import (
            ARTSY_VARIANT,
            simulate_route_on,
        )
        d = simulate_route_on(is_matched=True, match_profile_source="artsy")
        assert d.variant == ARTSY_VARIANT
        assert d.routing_reason == "matched_artsy"

    def test_simulate_route_on_saatchi(self):
        from visionai.price_engine.api.source_router import (
            SAATCHI_VARIANT,
            simulate_route_on,
        )
        d = simulate_route_on(is_matched=True, match_profile_source="saatchi")
        assert d.variant == SAATCHI_VARIANT

    def test_simulate_route_on_unmatched_fallback(self):
        from visionai.price_engine.api.source_router import (
            UNIFIED_VARIANT,
            simulate_route_on,
        )
        d = simulate_route_on(is_matched=False, match_profile_source=None)
        assert d.variant == UNIFIED_VARIANT
        assert d.routing_reason == "unmatched_fallback"


class TestGetPredictorForVariant:
    def test_get_unified_default(self):
        if "SOURCE_ROUTER_MODE" in os.environ:
            del os.environ["SOURCE_ROUTER_MODE"]
        from visionai.price_engine.api.source_router import (
            UNIFIED_VARIANT,
            SourceRouter,
        )
        r = SourceRouter()
        assert r.get_predictor_for_variant(UNIFIED_VARIANT) is r.unified

    def test_get_artsy_when_not_loaded(self):
        if "SOURCE_ROUTER_MODE" in os.environ:
            del os.environ["SOURCE_ROUTER_MODE"]
        from visionai.price_engine.api.source_router import (
            ARTSY_VARIANT,
            SourceRouter,
        )
        r = SourceRouter()
        # default OFF: artsy not loaded
        assert r.get_predictor_for_variant(ARTSY_VARIANT) is None

    def test_get_unknown_variant_returns_none(self):
        if "SOURCE_ROUTER_MODE" in os.environ:
            del os.environ["SOURCE_ROUTER_MODE"]
        from visionai.price_engine.api.source_router import SourceRouter
        r = SourceRouter()
        assert r.get_predictor_for_variant("unknown_variant") is None


class TestRunShadowInference:
    def test_off_mode_returns_empty(self, monkeypatch):
        """mode=off → empty dict (no shadow log)."""
        monkeypatch.setenv("SOURCE_ROUTER_MODE", "off")
        from visionai.price_engine.api import primary_server
        from visionai.price_engine.api.source_router import SourceRouter
        monkeypatch.setattr(primary_server, "_router", SourceRouter())
        result = primary_server._run_shadow_inference(
            features={"ho": 10}, is_matched=True, match_profile_source="artsy",
            training_count=5, target_market="gallery",
            has_manual_profile=False, artist_slug="test_artist",
        )
        assert result == {}

    def test_on_mode_returns_empty(self, monkeypatch):
        """mode=on → empty dict (shadow only when mode=shadow)."""
        monkeypatch.setenv("SOURCE_ROUTER_MODE", "on")
        from visionai.price_engine.api import primary_server
        from visionai.price_engine.api.source_router import SourceRouter
        monkeypatch.setattr(primary_server, "_router", SourceRouter())
        result = primary_server._run_shadow_inference(
            features={"ho": 10}, is_matched=True, match_profile_source="artsy",
            training_count=5, target_market="gallery",
            has_manual_profile=False, artist_slug="test",
        )
        assert result == {}

    def test_shadow_mode_predictor_not_loaded_returns_error(self, monkeypatch):
        """mode=shadow + artsy/saatchi not loaded → shadow_error."""
        monkeypatch.setenv("SOURCE_ROUTER_MODE", "shadow")
        from visionai.price_engine.api import primary_server
        from visionai.price_engine.api.source_router import SourceRouter
        # mode=shadow but predictors not loaded (load_models 미호출)
        monkeypatch.setattr(primary_server, "_router", SourceRouter())
        result = primary_server._run_shadow_inference(
            features={"ho": 10}, is_matched=True, match_profile_source="artsy",
            training_count=5, target_market="gallery",
            has_manual_profile=False, artist_slug="test",
        )
        assert "shadow_error" in result
        assert "predictor_not_loaded" in result["shadow_error"]
        assert result["shadow_routed_variant"] == "source_conditional_v1_artsy"
        assert result["shadow_routing_source"] == "artsy"

    def test_shadow_mode_inference_exception_fail_open(self, monkeypatch):
        """Shadow predict() exception → shadow_error / fail-open (no propagation)."""
        monkeypatch.setenv("SOURCE_ROUTER_MODE", "shadow")
        from visionai.price_engine.api import primary_server
        from visionai.price_engine.api.source_router import SourceRouter

        # Setup: mode=shadow / artsy mock raises
        router = SourceRouter()
        router.artsy = MagicMock()
        router.artsy.predict.side_effect = RuntimeError("test_failure")
        router.saatchi = MagicMock()
        monkeypatch.setattr(primary_server, "_router", router)

        result = primary_server._run_shadow_inference(
            features={"ho": 10}, is_matched=True, match_profile_source="artsy",
            training_count=5, target_market="gallery",
            has_manual_profile=False, artist_slug="test",
        )
        assert "shadow_error" in result
        assert "test_failure" in result["shadow_error"]


class TestLogPredictionCountToward:
    def test_count_toward_monitor_default_true(self, monkeypatch, tmp_path):
        """Default: count_toward_monitor=True / counter 증가."""
        monkeypatch.setattr("visionai.price_engine.api.primary_server._LOG_DIR", tmp_path)
        from visionai.price_engine.api import primary_server
        primary_server._init_log()
        before = primary_server._monitor["total_predictions"]
        primary_server._log_prediction({
            "id": "test1", "ts": "2026-01-01", "confidence_grade": "A",
            "model_type": "catboost_test", "is_known_artist": False,
            "total_ms": 100,
        })
        assert primary_server._monitor["total_predictions"] == before + 1

    def test_count_toward_monitor_false_no_counter_increment(self, monkeypatch, tmp_path):
        """count_toward_monitor=False (shadow log) / counter 증가 X."""
        monkeypatch.setattr("visionai.price_engine.api.primary_server._LOG_DIR", tmp_path)
        from visionai.price_engine.api import primary_server
        primary_server._init_log()
        before = primary_server._monitor["total_predictions"]
        primary_server._log_prediction(
            {"id": "shadow1", "ts": "2026-01-01"},
            count_toward_monitor=False,
        )
        assert primary_server._monitor["total_predictions"] == before


class TestDDLMigration:
    def test_ddl_file_exists(self):
        assert DDL_FILE.exists(), f"Missing DDL: {DDL_FILE}"

    def test_ddl_adds_routing_columns(self):
        ddl = DDL_FILE.read_text()
        for col in [
            "routing_source", "routing_reason", "routed_variant",
            "router_mode", "cohort_in_canary",
        ]:
            assert col in ddl, f"Missing routing column in DDL: {col}"

    def test_ddl_adds_shadow_columns(self):
        ddl = DDL_FILE.read_text()
        for col in [
            "shadow_routed_variant", "shadow_routing_source",
            "shadow_routing_reason", "shadow_prediction_price_krw",
        ]:
            assert col in ddl, f"Missing shadow column in DDL: {col}"

    def test_ddl_uses_if_not_exists(self):
        """idempotent migration."""
        ddl = DDL_FILE.read_text()
        assert "IF NOT EXISTS" in ddl


class TestETLWhitelistAdditive:
    def test_etl_includes_routing_columns(self):
        from etl_predict_logs import PREDICT_LOGS_COLUMNS
        for col in [
            "routing_source", "routing_reason", "routed_variant",
            "router_mode", "cohort_in_canary",
            "shadow_routed_variant", "shadow_routing_source",
            "shadow_routing_reason", "shadow_prediction_price_krw",
        ]:
            assert col in PREDICT_LOGS_COLUMNS, f"Missing in ETL whitelist: {col}"

    def test_etl_preserves_existing_columns(self):
        """Backward compat: 기존 column 유지."""
        from etl_predict_logs import PREDICT_LOGS_COLUMNS
        for col in [
            "request_id", "timestamp", "predicted_price_krw",
            "model_variant", "artifact_version",
        ]:
            assert col in PREDICT_LOGS_COLUMNS

    def test_etl_column_count(self):
        """25 (existing) + 9 (new) = 34 columns."""
        from etl_predict_logs import PREDICT_LOGS_COLUMNS
        assert len(PREDICT_LOGS_COLUMNS) == 34
