"""PR2B-prereq.2 Prometheus per-route metrics + naming consistency tests."""

from __future__ import annotations

import os

from fastapi.testclient import TestClient


class TestMonitorRouteCounters:
    def test_monitor_has_routing_counters(self, monkeypatch, tmp_path):
        """_monitor 영역 by_routed_variant + by_routing_decision + shadow_total."""
        monkeypatch.setattr(
            "visionai.price_engine.api.primary_server._LOG_DIR", tmp_path
        )
        from visionai.price_engine.api import primary_server
        primary_server._init_log()
        # reset counters for isolated test
        primary_server._monitor["by_routed_variant"] = {}
        primary_server._monitor["by_routing_decision"] = {}
        primary_server._monitor["shadow_total"] = 0

        primary_server._log_prediction({
            "id": "t1", "ts": "2026-01-01", "confidence_grade": "A",
            "model_type": "catboost_v3_filtered_tuned",
            "routed_variant": "v3_filtered_tuned",
            "routing_source": "unified",
            "routing_reason": "router_off",
            "is_known_artist": False, "total_ms": 100,
        })
        primary_server._log_prediction({
            "id": "t2", "ts": "2026-01-01", "confidence_grade": "B",
            "model_type": "xgboost_v3_filtered_tuned",
            "routed_variant": "v3_filtered_tuned",
            "routing_source": "unified",
            "routing_reason": "router_off",
            "is_known_artist": True, "total_ms": 50,
        })
        # mode=shadow row simulation
        primary_server._log_prediction({
            "id": "t3", "ts": "2026-01-01", "confidence_grade": "A",
            "model_type": "catboost_v3_filtered_tuned",
            "routed_variant": "v3_filtered_tuned",
            "routing_source": "unified",
            "routing_reason": "shadow_mode_primary_unified",
            "shadow_routed_variant": "source_conditional_v1_artsy",
            "is_known_artist": True, "total_ms": 80,
        })

        assert primary_server._monitor["by_routed_variant"]["v3_filtered_tuned"] == 3
        assert primary_server._monitor["by_routing_decision"]["unified|router_off"] == 2
        assert primary_server._monitor["by_routing_decision"][
            "unified|shadow_mode_primary_unified"
        ] == 1
        assert primary_server._monitor["shadow_total"] == 1


class TestPrometheusEndpoint:
    def test_metrics_endpoint_includes_routing(self, monkeypatch, tmp_path):
        """/api/v1/metrics 영역 영역 의 의무 prediction_total_by_routed_variant /
        routing_decision_total / shadow_inferences_total."""
        monkeypatch.setattr(
            "visionai.price_engine.api.primary_server._LOG_DIR", tmp_path
        )
        from visionai.price_engine.api import primary_server
        primary_server._init_log()
        # Inject metrics
        primary_server._monitor["by_routed_variant"] = {
            "v3_filtered_tuned": 100,
            "source_conditional_v1_artsy": 5,
        }
        primary_server._monitor["by_routing_decision"] = {
            "unified|router_off": 95,
            "artsy|matched_artsy": 5,
            "unified|unmatched_fallback": 5,
        }
        primary_server._monitor["shadow_total"] = 10

        client = TestClient(primary_server.app)
        r = client.get("/api/v1/metrics")
        assert r.status_code == 200
        body = r.text
        # New per-route counters
        assert "visionai_predictions_total_by_routed_variant" in body
        assert 'routed_variant="v3_filtered_tuned"' in body
        assert 'routed_variant="source_conditional_v1_artsy"' in body
        assert "visionai_routing_decision_total" in body
        assert 'routing_source="artsy"' in body
        assert 'routing_reason="matched_artsy"' in body
        assert "visionai_shadow_inferences_total" in body


class TestNamingConsistency:
    def test_log_entry_includes_source_router_rule_version(self):
        """log entry 영역 의 의무 source_router_rule_version 영역 의 의무 의무 (PR2B-prereq.2)."""
        # Static check via primary_server module — log key 영역 의 의무 의무 (단순 string check)
        import inspect

        from visionai.price_engine.api import primary_server
        source = inspect.getsource(primary_server)
        assert '"source_router_rule_version"' in source
        # Both fields present (rollout vs router)
        assert '"rollout_rule_version"' in source

    def test_etl_includes_source_router_rule_version(self):
        from etl_predict_logs import PREDICT_LOGS_COLUMNS
        assert "source_router_rule_version" in PREDICT_LOGS_COLUMNS
        assert "rollout_rule_version" in PREDICT_LOGS_COLUMNS

    def test_default_router_rule_version(self):
        if "SOURCE_ROUTER_RULE_VERSION" in os.environ:
            del os.environ["SOURCE_ROUTER_RULE_VERSION"]
        from visionai.price_engine.api.source_router import SourceRouter
        r = SourceRouter()
        assert r.rule_version == "v1"


class TestDDLPrereq2Column:
    def test_ddl_includes_source_router_rule_version(self):
        from pathlib import Path
        ddl_path = Path(__file__).resolve().parent.parent.parent / \
            "monitoring/sql/002_predict_logs_router_columns.sql"
        ddl = ddl_path.read_text()
        assert "source_router_rule_version" in ddl
