"""FastAPI 서버 단위 테스트."""
from __future__ import annotations

import pytest
from visionai.price_engine.api.schemas import PredictRequest, PredictResponse, ModelInfoResponse


class TestSchemas:
    """스키마 검증 테스트."""

    def test_predict_request_valid(self) -> None:
        req = PredictRequest(
            artist_name="김환기",
            auction_type="메이저",
            width_cm=72.7,
            height_cm=60.6,
            medium="캔버스에 유채",
            estimate_low=50000000,
            estimate_high=80000000,
            year_created=1970,
        )
        assert req.artist_name == "김환기"
        assert req.estimate_low == 50000000

    def test_predict_request_minimal(self) -> None:
        req = PredictRequest(
            artist_name="테스트",
            auction_type="위클리",
            width_cm=50,
            height_cm=40,
            estimate_low=1000000,
            estimate_high=2000000,
        )
        assert req.year_created is None
        assert req.medium == ""

    def test_predict_response(self) -> None:
        resp = PredictResponse(
            predicted_price=65000000,
            price_range=[52000000, 78000000],
            confidence_grade="A",
            estimate_vs_prediction=81.3,
            model_version="test_v1",
        )
        assert resp.confidence_grade == "A"
        assert len(resp.price_range) == 2

    def test_model_info_response(self) -> None:
        info = ModelInfoResponse(
            model_version="v1",
            model_type="CatBoost",
            features_count=22,
            test_mape=27.01,
            test_r2=0.936,
            a_grade_within_20pct=71.6,
            gate_status="9/9",
        )
        assert info.gate_status == "9/9"

    def test_predict_request_rejects_negative(self) -> None:
        with pytest.raises(Exception):
            PredictRequest(
                artist_name="test",
                auction_type="메이저",
                width_cm=-1,  # invalid
                height_cm=50,
                estimate_low=1000000,
                estimate_high=2000000,
            )

    def test_predict_request_rejects_low_gt_high(self) -> None:
        """estimate_low > estimate_high는 거부."""
        with pytest.raises(Exception):
            PredictRequest(
                artist_name="test",
                auction_type="메이저",
                width_cm=50,
                height_cm=40,
                estimate_low=5000000,
                estimate_high=3000000,  # low > high
            )

    def test_predict_request_rejects_invalid_auction_type(self) -> None:
        """유효하지 않은 경매 타입은 거부."""
        with pytest.raises(Exception):
            PredictRequest(
                artist_name="test",
                auction_type="존재하지않는타입",
                width_cm=50,
                height_cm=40,
                estimate_low=1000000,
                estimate_high=2000000,
            )
