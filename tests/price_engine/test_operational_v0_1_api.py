from __future__ import annotations

from fastapi.testclient import TestClient

from visionai.price_engine.api.operational_v0_1_server import app


def test_operational_v0_1_current_model_and_price_estimate() -> None:
    with TestClient(app) as client:
        page = client.get("/test/v0.1")
        assert page.status_code == 200
        assert "가격 예측 v0.1 테스트" in page.text

        current = client.get("/api/v1/price-models/current")
        assert current.status_code == 200
        current_payload = current.json()
        assert current_payload["model_version"] == "price_prediction_v0.1"
        assert current_payload["service_primary_column"] == "service_primary_pred_price_krw"

        resolved = client.post(
            "/api/v1/artists:resolve",
            json={"artist": {"name_en": "Seongeun Moon"}, "options": {"max_candidates": 5}},
        )
        assert resolved.status_code == 200
        resolved_payload = resolved.json()
        assert resolved_payload["resolved"] is True
        assert resolved_payload["selected_artist"]["artist_key"] == "seongeun moon"

        estimate = client.post(
            "/api/v1/artworks/price-estimate",
            json={
                "artwork": {
                    "external_artwork_id": "smoke_001",
                    "title": "After The Flight",
                    "artist": {"artist_key": "seongeun moon", "name_en": "Seongeun Moon"},
                    "year": 2026,
                    "dimensions": {"width_cm": 24.0, "height_cm": 41.0, "depth_cm": 1.8},
                    "medium": {"medium_category": "acrylic", "support_category": "canvas"},
                    "category": "Painting",
                    "artwork_url": "https://example.com/artwork/smoke_001",
                },
                "options": {"include_comparable_samples": True, "max_comparable_samples": 3},
            },
        )
        assert estimate.status_code == 200
        estimate_payload = estimate.json()
        assert estimate_payload["route"] == "warm"
        assert estimate_payload["prediction"]["price_krw"] > 0
        assert estimate_payload["prediction"]["range_krw"]["low"] > 0
        assert estimate_payload["market_price_card"]["sample_count"] > 0
