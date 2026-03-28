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
    def check_estimate_order(self) -> PredictRequest:
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


# ─── Phase 3: 추정가 생성 엔진 스키마 ───


class EstimateRequest(BaseModel):
    """추정가 생성 요청 — 추정가 입력 불필요."""

    artist: str = Field(..., description="작가명", examples=["이우환"])
    medium: str = Field("", description="재료", examples=["캔버스에 유채"])
    width_cm: float = Field(..., description="가로 cm", ge=0, examples=[72.7])
    height_cm: float = Field(..., description="세로 cm", ge=0, examples=[60.6])
    year: int | None = Field(None, description="제작연도", examples=[2015])
    title: str = Field("", description="작품 제목 (NLP 피처용)", examples=["Dialogue"])
    auction_type: AuctionType = Field(
        AuctionType.프리미엄, description="경매 타입"
    )


class EstimateValidateRequest(EstimateRequest):
    """추정가 검증 요청 — K-Auction 추정가와 비교."""

    kauction_estimate_low: int = Field(
        ..., description="K-Auction 추정가 최저", ge=0
    )
    kauction_estimate_high: int = Field(
        ..., description="K-Auction 추정가 최고", ge=0
    )

    @model_validator(mode="after")
    def check_kauction_order(self) -> EstimateValidateRequest:
        if self.kauction_estimate_low > self.kauction_estimate_high:
            msg = "kauction_estimate_low > kauction_estimate_high"
            raise ValueError(msg)
        return self


class PredictV2Request(BaseModel):
    """v2 모드: 생성 추정가 기반 낙찰가 예측."""

    artist: str = Field(..., description="작가명")
    medium: str = Field("", description="재료")
    width_cm: float = Field(..., ge=0)
    height_cm: float = Field(..., ge=0)
    year: int | None = None
    auction_type: AuctionType = Field(AuctionType.프리미엄)
    estimate_low: int | None = Field(
        None, description="추정가 최저 (미입력 시 자동 생성)", ge=0
    )
    estimate_high: int | None = Field(
        None, description="추정가 최고 (미입력 시 자동 생성)", ge=0
    )

    @model_validator(mode="after")
    def check_estimate_pair(self) -> PredictV2Request:
        """추정가는 둘 다 있거나 둘 다 없어야 함. low <= high 검증."""
        has_low = self.estimate_low is not None
        has_high = self.estimate_high is not None
        if has_low != has_high:
            msg = "estimate_low와 estimate_high는 함께 입력하거나 함께 생략해야 합니다."
            raise ValueError(msg)
        if has_low and has_high and self.estimate_low > self.estimate_high:
            msg = f"estimate_low({self.estimate_low}) > estimate_high({self.estimate_high})"
            raise ValueError(msg)
        return self


class PriceRangeSchema(BaseModel):
    """가격 범위 (low/mid/high)."""

    low: int = Field(..., description="하한")
    mid: int = Field(..., description="중앙")
    high: int = Field(..., description="상한")


class EstimateResponse(BaseModel):
    """추정가 생성 응답."""

    price_range: PriceRangeSchema | dict = Field(
        ..., description="Model-A 가격 구간 {low, mid, high} (연속값)"
    )
    estimate: PriceRangeSchema | dict = Field(
        ..., description="Model-B 추정가 {low, mid, high} (라운딩)"
    )
    confidence_grade: str = Field(..., description="신뢰도 등급 A/B/C/D")
    cold_start_tier: int | None = Field(None, description="Cold Start tier")
    warnings: list[str] = Field(default_factory=list)


class EstimateValidateResponse(BaseModel):
    """추정가 검증 응답."""

    ai_estimate_mid: int
    kauction_mid: int
    divergence_rate: float = Field(..., description="괴리율 (%)")
    threshold_pct: float
    warning: bool
    message: str = ""
