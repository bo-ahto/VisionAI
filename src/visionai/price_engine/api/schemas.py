"""API 요청/응답 스키마.

기획서 참조: Sprint 3 API 엔드포인트
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator


class AuctionType(str, Enum):
    """경매 타입."""

    위클리 = "위클리"
    프리미엄 = "프리미엄"
    메이저 = "메이저"


class PredictRequest(BaseModel):
    """가격 예측 요청."""

    artist_name: str = Field(..., description="작가명", examples=["김환기"])
    auction_type: AuctionType = Field(..., description="경매 타입", examples=["메이저"])
    width_cm: float = Field(..., description="가로 cm", ge=0, examples=[72.7])
    height_cm: float = Field(..., description="세로 cm", ge=0, examples=[60.6])
    medium: str = Field("", description="재료", examples=["캔버스에 유채"])
    estimate_low: int = Field(..., description="추정가 최저 (원)", ge=0, examples=[50000000])
    estimate_high: int = Field(..., description="추정가 최고 (원)", ge=0, examples=[80000000])
    year_created: int | None = Field(None, description="제작연도", examples=[1970])

    @model_validator(mode="after")
    def check_estimate_order(self) -> "PredictRequest":
        """estimate_low ≤ estimate_high 검증."""
        if self.estimate_low > self.estimate_high:
            msg = f"estimate_low({self.estimate_low}) > estimate_high({self.estimate_high})"
            raise ValueError(msg)
        return self


class PredictResponse(BaseModel):
    """가격 예측 응답."""

    predicted_price: int = Field(..., description="예측 낙찰가 (원)")
    price_range: list[int] = Field(..., description="가격 범위 [하한, 상한]")
    confidence_grade: str = Field(..., description="신뢰도 등급 (A/B/C/D)")
    estimate_vs_prediction: float = Field(..., description="추정가 대비 예측 비율 (%)")
    model_version: str = Field(..., description="모델 버전")
    prediction_method: str = Field("target_transform+calibration", description="예측 방식")


class ModelInfoResponse(BaseModel):
    """모델 정보 응답."""

    model_config = {"protected_namespaces": ()}

    model_version: str
    model_type: str
    features_count: int
    test_mape: float
    test_r2: float
    a_grade_within_20pct: float
    gate_status: str
