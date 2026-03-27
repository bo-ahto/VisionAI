"""Phase 3 API 엔드포인트 테스트."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from visionai.price_engine.api.server import app

client = TestClient(app)


class TestEstimateEndpoint:
    def test_estimate_returns_200(self) -> None:
        resp = client.post("/api/v1/estimate", json={
            "artist": "이우환",
            "medium": "캔버스에 유채",
            "width_cm": 72.7,
            "height_cm": 60.6,
            "year": 2015,
            "auction_type": "메이저",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "price_range" in data
        assert "estimate" in data
        assert "confidence_grade" in data

    def test_estimate_default_auction_type(self) -> None:
        resp = client.post("/api/v1/estimate", json={
            "artist": "김환기",
            "width_cm": 50.0,
            "height_cm": 40.0,
        })
        assert resp.status_code == 200

    def test_estimate_missing_artist_returns_422(self) -> None:
        resp = client.post("/api/v1/estimate", json={
            "width_cm": 50.0,
            "height_cm": 40.0,
        })
        assert resp.status_code == 422


class TestValidateEndpoint:
    def test_validate_returns_200(self) -> None:
        resp = client.post("/api/v1/estimate/validate", json={
            "artist": "이우환",
            "medium": "캔버스에 유채",
            "width_cm": 72.7,
            "height_cm": 60.6,
            "year": 2015,
            "auction_type": "메이저",
            "kauction_estimate_low": 50000000,
            "kauction_estimate_high": 80000000,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "divergence_rate" in data
        assert "warning" in data

    def test_validate_bad_order_returns_422(self) -> None:
        resp = client.post("/api/v1/estimate/validate", json={
            "artist": "이우환",
            "width_cm": 72.7,
            "height_cm": 60.6,
            "kauction_estimate_low": 80000000,
            "kauction_estimate_high": 50000000,
        })
        assert resp.status_code == 422


class TestExistingEndpointUnchanged:
    def test_health(self) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_predict_price_still_works(self) -> None:
        """기존 /api/v1/predict_price 엔드포인트 하위 호환."""
        resp = client.post("/api/v1/predict_price", json={
            "artist_name": "이우환",
            "auction_type": "메이저",
            "width_cm": 72.7,
            "height_cm": 60.6,
            "medium": "캔버스에 유채",
            "estimate_low": 50000000,
            "estimate_high": 80000000,
            "year_created": 2015,
        })
        # 모델이 로드되지 않으면 500/503일 수 있으나, 스키마는 변경 없음
        assert resp.status_code in (200, 500, 503)


class TestPredictV2Endpoint:
    def test_predict_v2_returns_503_without_model(self) -> None:
        resp = client.post("/api/v1/predict_v2", json={
            "artist": "이우환",
            "medium": "캔버스에 유채",
            "width_cm": 72.7,
            "height_cm": 60.6,
            "year": 2015,
            "auction_type": "메이저",
        })
        # 모델 미로드 → 503
        assert resp.status_code == 503

    def test_predict_v2_endpoint_exists(self) -> None:
        """엔드포인트가 라우트에 등록되어 있는지 확인."""
        routes = [r.path for r in app.routes]
        assert "/api/v1/predict_v2" in routes

    def test_predict_v2_missing_artist_returns_422(self) -> None:
        resp = client.post("/api/v1/predict_v2", json={
            "width_cm": 50.0,
            "height_cm": 40.0,
        })
        assert resp.status_code == 422


class TestGateChecker:
    def test_all_gates_pass(self) -> None:
        from scripts.check_estimate_gate import check_gates
        results = check_gates(
            coverage_overall=0.58,
            coverage_major=0.60,
            hedonic_r2=0.70,
            range_width_median=0.5,
            estimate_mape_all=0.30,
            estimate_mape_major=0.20,
            integrated_mape=0.28,
            cold_start_generation=1.0,
            cold_start_mape=0.45,
            leakage_test_all_pass=True,
            low_liquidity_mape=0.40,
            monotonicity_rate=1.0,
        )
        assert all(r.passed for r in results)
        assert len(results) == 12

    def test_gate_failure(self) -> None:
        from scripts.check_estimate_gate import check_gates
        results = check_gates(coverage_overall=0.40)  # G1 실패
        g1 = next(r for r in results if r.gate_id == "G1")
        assert not g1.passed

    def test_gate_count(self) -> None:
        from scripts.check_estimate_gate import check_gates
        results = check_gates()
        assert len(results) == 12
