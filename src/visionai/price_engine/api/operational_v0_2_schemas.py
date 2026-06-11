"""Pydantic schemas for the price_prediction v0.2 local operational API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from visionai.price_engine.api.operational_v0_1_schemas import (
    ArtistInput,
    ArtworkInput,
    ComparableSample,
    ErrorBody,
    ErrorResponse,
    ExchangeRates,
    MediumDistribution,
    PredictionBasis,
    PriceRange,
    RangePerHo,
    WarningItem,
)


Status = Literal["success", "partial_success", "failed"]
Currency = Literal["KRW", "USD", "EUR", "GBP", "HKD", "JPY"]
Route = Literal["warm", "cold", "review_required"]
DisplayPolicy = Literal["price_with_range", "estimated_price_with_reference_warning", "no_single_price"]
ConfidenceLevel = Literal["high", "medium", "low"]


class CurrentModelResponse(BaseModel):
    request_id: str
    status: Status
    created_at: str
    model_version: str
    model_status: Literal["candidate", "active", "archived"]
    display_policy: dict[str, str]
    routing_policy: dict[str, float | int | str]
    exchange_rates: ExchangeRates
    warm_model_version: str
    cold_model_version: str
    feedback_policy: dict[str, str]


class ResolveArtistOptions(BaseModel):
    max_candidates: int = Field(5, ge=1, le=20)


class ResolveArtistRequest(BaseModel):
    artist: ArtistInput
    options: ResolveArtistOptions = Field(default_factory=ResolveArtistOptions)


class ResolvedArtist(BaseModel):
    artist_key: str
    name_ko: str | None = None
    name_en: str | None = None
    birth_year: int | None = None
    nationality: str | None = None
    entity_suffix: str | None = None
    match_status: Literal["exact", "alias", "fuzzy", "ambiguous", "not_found"]
    matched_alias: str | None = None
    match_basis: str | None = None
    artist_match_score: float = Field(..., ge=0.0, le=1.0)
    homonym_risk_score: float = Field(..., ge=0.0, le=1.0)
    review_required: bool = False
    warm_available: bool
    same_artist_training_price_count: int | None = None
    route_recommendation: Route | None = None


class ResolveArtistResponse(BaseModel):
    request_id: str
    status: Status
    created_at: str
    model_version: str
    resolved: bool
    requires_selection: bool
    selected_artist: ResolvedArtist | None = None
    candidates: list[ResolvedArtist]
    warnings: list[WarningItem] = Field(default_factory=list)


class PriceEstimateOptions(BaseModel):
    currency: Currency = "KRW"
    include_comparable_samples: bool = False
    max_comparable_samples: int = Field(10, ge=0, le=50)
    include_calculation_summary: bool = True
    include_feedback_guide: bool = True


class PriceEstimateRequest(BaseModel):
    artwork: ArtworkInput
    options: PriceEstimateOptions = Field(default_factory=PriceEstimateOptions)


class Confidence(BaseModel):
    level: ConfidenceLevel
    score: float | None = Field(None, ge=0.0, le=1.0)
    reason_codes: list[str]


class Prediction(BaseModel):
    price_krw: int | None = None
    price_display: str | None = None
    range_krw: PriceRange
    range_display: str | None = None
    confidence: Confidence


class Routing(BaseModel):
    artist_matched: bool
    matched_artist_key: str | None = None
    artist_match_score: float | None = Field(None, ge=0.0, le=1.0)
    homonym_risk_score: float | None = Field(None, ge=0.0, le=1.0)
    same_artist_training_price_count: int | None = None
    route_policy: str
    route_reason: str


class InputQuality(BaseModel):
    minimum_input_status: Literal["passed", "failed"]
    missing_required_fields: list[str] = Field(default_factory=list)
    missing_recommended_fields: list[str] = Field(default_factory=list)
    confidence_penalty_reasons: list[str] = Field(default_factory=list)


class CalculationComponent(BaseModel):
    name: str
    role: str
    formula: str | None = None
    output_field: str | None = None


class CalculationSummary(BaseModel):
    route: Route
    user_facing_formula: str
    model_components: list[CalculationComponent] = Field(default_factory=list)
    guard_applied: bool = False
    explanation: str


class MarketPriceCard(BaseModel):
    title: str = "1차 시장 가격"
    metric_label: str = "호당가 중앙값"
    median_krw_per_ho: int | None = None
    median_display: str
    range_krw_per_ho: RangePerHo
    range_display: str
    medium_distribution: list[MediumDistribution]
    sample_count: int
    sample_count_display: str


class FeedbackGuide(BaseModel):
    can_submit_actual_sale_price: bool
    feedback_endpoint: str
    required_fields: list[str]
    note: str


class PriceEstimateResponse(BaseModel):
    request_id: str
    status: Status
    created_at: str
    model_version: str
    prediction_id: str
    route: Route
    display_policy: DisplayPolicy
    prediction: Prediction
    routing: Routing
    basis: PredictionBasis
    market_price_card: MarketPriceCard
    comparable_samples: list[ComparableSample] = Field(default_factory=list)
    input_quality: InputQuality
    calculation_summary: CalculationSummary | None = None
    feedback: FeedbackGuide | None = None
    warnings: list[WarningItem] = Field(default_factory=list)


class SalePriceFeedbackRequest(BaseModel):
    prediction_id: str
    external_artwork_id: str | None = None
    actual_sale_price_krw: int = Field(..., gt=0)
    sale_date: str | None = None
    sale_channel: str | None = None
    evidence_status: Literal["none", "partial", "verified"] = "partial"
    consent_for_training: bool = True
    note: str | None = None


class SalePriceFeedbackResponse(BaseModel):
    request_id: str
    status: Status
    created_at: str
    accepted: bool
    review_status: Literal["needs_review", "queued_for_training", "rejected"]
    message: str
