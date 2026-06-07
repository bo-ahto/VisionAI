"""Pydantic schemas for the price_prediction v0.1 operational API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Status = Literal["success", "partial_success", "failed"]
Currency = Literal["KRW", "USD", "EUR", "GBP", "HKD", "JPY"]
Route = Literal["warm", "cold"]
ConfidenceLevel = Literal["high", "medium", "low"]


class WarningItem(BaseModel):
    code: str
    severity: Literal["info", "warning", "critical"] = "warning"
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    field: str | None = None


class ErrorResponse(BaseModel):
    request_id: str
    status: Literal["failed"] = "failed"
    created_at: str
    error: ErrorBody


class ExchangeRates(BaseModel):
    base_currency: Literal["KRW"] = "KRW"
    USD: float
    EUR: float
    GBP: float
    HKD: float
    JPY: float


class CurrentModelResponse(BaseModel):
    request_id: str
    status: Status
    created_at: str
    model_version: str
    model_status: Literal["candidate", "active", "archived"]
    display_policy: dict[str, str]
    exchange_rates: ExchangeRates
    service_primary_candidate: str
    service_primary_column: str


class ArtistInput(BaseModel):
    artist_key: str | None = None
    name_ko: str | None = None
    name_en: str | None = None


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
    review_required: bool = False
    warm_available: bool
    valid_training_label_count: int | None = None
    route_recommendation: Literal["warm", "cold", "review_required"] | None = None


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


class Dimensions(BaseModel):
    width_cm: float | None = Field(None, gt=0)
    height_cm: float | None = Field(None, gt=0)
    depth_cm: float | None = Field(None, ge=0)


class Medium(BaseModel):
    medium_category: str = Field(..., min_length=1)
    support_category: str = Field(..., min_length=1)


class ArtworkInput(BaseModel):
    external_artwork_id: str | None = None
    title: str | None = None
    artist: ArtistInput
    year: int | None = None
    dimensions: Dimensions
    medium: Medium
    category: str | None = "Painting"
    artwork_url: str | None = None


class PriceEstimateOptions(BaseModel):
    currency: Currency = "KRW"
    include_comparable_samples: bool = False
    max_comparable_samples: int = Field(10, ge=0, le=50)


class PriceEstimateRequest(BaseModel):
    artwork: ArtworkInput
    options: PriceEstimateOptions = Field(default_factory=PriceEstimateOptions)


class PriceRange(BaseModel):
    low: int | None = None
    mid: int | None = None
    high: int | None = None


class Confidence(BaseModel):
    level: ConfidenceLevel
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
    valid_training_label_count: int | None = None
    route_policy: str | None = None
    route_reason: str


class PredictionBasis(BaseModel):
    similar_group_level: str | None = None
    similar_sample_count: int | None = None
    similar_coverage_tier: str | None = None
    similar_price_median_krw: int | None = None
    similar_price_q25_krw: int | None = None
    similar_price_q75_krw: int | None = None


class MediumDistribution(BaseModel):
    label: str
    medium_group: str | None = None
    median_krw_per_ho: int | None = None
    display: str
    sample_count: int


class RangePerHo(BaseModel):
    low: int | None = None
    high: int | None = None


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


class ComparableSample(BaseModel):
    artwork_id: str | None = None
    title: str | None = None
    artist_name: str | None = None
    sale_price_krw: int | None = None
    width_cm: float | None = None
    height_cm: float | None = None
    medium_category: str | None = None
    support_category: str | None = None
    similarity_reason: str | None = None


class PriceEstimateResponse(BaseModel):
    request_id: str
    status: Status
    created_at: str
    model_version: str
    route: Route
    display_policy: Literal["price_with_range", "reference_range_only"]
    prediction: Prediction
    routing: Routing
    basis: PredictionBasis
    market_price_card: MarketPriceCard
    comparable_samples: list[ComparableSample] = Field(default_factory=list)
    warnings: list[WarningItem] = Field(default_factory=list)
