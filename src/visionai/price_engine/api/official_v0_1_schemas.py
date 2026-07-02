"""Schemas for the official price_prediction_v0.1 service test API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Status = Literal["success", "partial_success", "failed"]
Route = Literal["warm", "warm_lite", "cold", "review_required"]
DisplayRoute = Literal["이력 기반 예측", "저이력 기반 예측", "참고 예측", "확인 필요"]
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
    service_version: str
    error: ErrorBody


class HealthResponse(BaseModel):
    request_id: str
    status: Status
    created_at: str
    service_version: str
    service_loaded: bool
    db_loaded: bool
    warm_adapter_loaded: bool
    cold_adapter_loaded: bool
    search_cache_loaded: bool
    model_registry_loaded: bool
    table_counts: dict[str, int]


class CurrentModelResponse(BaseModel):
    request_id: str
    status: Status
    created_at: str
    service_version: str
    model_status: Literal["candidate", "active", "archived"]
    routing_policy: dict[str, float | int | str]
    display_policy: dict[str, str]
    artifact_versions: dict[str, str | None]
    adapter_status: dict[str, bool | str]


class ArtistInput(BaseModel):
    artist_key: str | None = None
    selected_artist_key: str | None = None
    name_ko: str | None = None
    name_en: str | None = None
    birth_year: int | None = None


class ResolveArtistOptions(BaseModel):
    max_candidates: int = Field(5, ge=1, le=20)


class ResolveArtistRequest(BaseModel):
    artist: ArtistInput
    options: ResolveArtistOptions = Field(default_factory=ResolveArtistOptions)


class RepresentativeArtwork(BaseModel):
    artwork_id: str | None = None
    title: str | None = None
    artist_name: str | None = None
    sale_price_krw: int | None = None
    sale_price_display: str | None = None
    width_cm: float | None = None
    height_cm: float | None = None
    medium_category: str | None = None
    support_category: str | None = None
    ho_size: int | None = None
    ho_size_display: str | None = None


class ResolvedArtist(BaseModel):
    artist_key: str
    name_ko: str | None = None
    name_en: str | None = None
    birth_year: int | None = None
    nationality: str | None = None
    nationality_ko: str | None = None
    entity_suffix: str | None = None
    match_status: Literal["exact", "alias", "fuzzy", "direct_key", "not_found"]
    matched_alias: str | None = None
    match_basis: str | None = None
    artist_match_score: float = Field(..., ge=0.0, le=1.0)
    homonym_risk_score: float = Field(..., ge=0.0, le=1.0)
    review_required: bool
    warm_available: bool
    same_artist_training_price_count: int
    route_recommendation: Route
    display_route_recommendation: DisplayRoute
    representative_artworks: list[RepresentativeArtwork] = Field(default_factory=list)


class ResolveArtistResponse(BaseModel):
    request_id: str
    status: Status
    created_at: str
    service_version: str
    resolved: bool
    requires_selection: bool
    selected_artist: ResolvedArtist | None = None
    candidates: list[ResolvedArtist]
    warnings: list[WarningItem] = Field(default_factory=list)


class Dimensions(BaseModel):
    width_cm: float | None = Field(None, gt=0)
    height_cm: float | None = Field(None, gt=0)
    depth_cm: float | None = Field(None, ge=0)


class MediumInput(BaseModel):
    medium_category: str | None = None
    support_category: str | None = None


class ArtworkInput(BaseModel):
    title: str | None = None
    artist: ArtistInput
    year: int | None = None
    category: str | None = "Painting"
    dimensions: Dimensions
    medium: MediumInput
    artwork_url: str | None = None
    source_artwork_id: str | None = None
    external_artwork_id: str | None = None


class PriceEstimateOptions(BaseModel):
    currency: Literal["KRW"] = "KRW"
    include_comparable_samples: bool = True
    max_comparable_samples: int = Field(10, ge=0, le=50)
    include_calculation_steps: bool = True
    include_debug_fields: bool = False


class PriceEstimateRequest(BaseModel):
    artwork: ArtworkInput
    options: PriceEstimateOptions = Field(default_factory=PriceEstimateOptions)


class PriceRange(BaseModel):
    low: int | None = None
    mid: int | None = None
    high: int | None = None


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


class CalculationStep(BaseModel):
    step_order: int
    name: str
    role: str
    formula: str | None = None
    input: dict[str, object] = Field(default_factory=dict)
    output: dict[str, object] = Field(default_factory=dict)


class CalculationSummary(BaseModel):
    route: Route
    display_route: DisplayRoute
    user_facing_formula: str
    explanation: str
    adapter_execution_level: Literal["db_cache_foundation", "report_final_layer_proxy", "report_model_adapter"]
    steps: list[CalculationStep] = Field(default_factory=list)


class PredictionBasis(BaseModel):
    similar_group_level: str | None = None
    similar_sample_count: int | None = None
    similar_coverage_tier: str | None = None
    similar_price_median_krw: int | None = None
    similar_price_q25_krw: int | None = None
    similar_price_q75_krw: int | None = None
    median_krw_per_ho: int | None = None


class RangePerHo(BaseModel):
    low: int | None = None
    high: int | None = None


class MediumDistribution(BaseModel):
    label: str
    median_krw_per_ho: int | None = None
    display: str
    sample_count: int


class MarketReference(BaseModel):
    title: str = "1차 시장 가격"
    metric_label: str = "호당가 중앙값"
    target_ho_size: int | None = None
    target_ho_size_display: str | None = None
    median_krw_per_ho: int | None = None
    median_display: str
    range_krw_per_ho: RangePerHo
    range_display: str
    converted_total_price_krw: int | None = None
    converted_total_price_display: str | None = None
    medium_distribution: list[MediumDistribution] = Field(default_factory=list)
    sample_count: int
    sample_count_display: str


class SimilarArtwork(BaseModel):
    artwork_id: str | None = None
    title: str | None = None
    artist_name: str | None = None
    sale_price_krw: int | None = None
    sale_price_display: str | None = None
    width_cm: float | None = None
    height_cm: float | None = None
    medium_category: str | None = None
    support_category: str | None = None
    ho_size: int | None = None
    ho_size_display: str | None = None
    similarity_tier: Literal["strong", "medium", "weak"]
    similarity_reason: str


class SimilarArtistReference(BaseModel):
    artist_key: str
    name_ko: str | None = None
    birth_year: int | None = None
    nationality: str | None = None
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    price_history_count: int
    primary_medium: str | None = None
    primary_support: str | None = None
    median_price_display: str | None = None
    match_reasons: list[str] = Field(default_factory=list)


class FeedbackGuide(BaseModel):
    can_submit_actual_sale_price: bool
    feedback_endpoint: str
    required_fields: list[str]
    note: str


class PriceEstimateResponse(BaseModel):
    request_id: str
    status: Status
    created_at: str
    service_version: str
    prediction_id: str
    route: Route
    display_route: DisplayRoute
    display_policy: Literal["price_with_range", "reference_range_only", "review_required"]
    prediction: Prediction
    routing: Routing
    basis: PredictionBasis
    market_reference: MarketReference
    similar_artworks: list[SimilarArtwork] = Field(default_factory=list)
    similar_artists: list[SimilarArtistReference] = Field(default_factory=list)
    input_quality: InputQuality
    calculation_summary: CalculationSummary | None = None
    feedback: FeedbackGuide | None = None
    warnings: list[WarningItem] = Field(default_factory=list)


class PredictionLookupResponse(BaseModel):
    request_id: str
    status: Status
    created_at: str
    service_version: str
    prediction_id: str
    prediction_event: dict[str, object] | None
    calculation_steps: list[dict[str, object]]


class SalePriceFeedbackRequest(BaseModel):
    prediction_id: str
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
    service_version: str
    accepted: bool
    review_status: Literal["needs_review", "queued_for_training", "rejected"]
    message: str


class ModelAuditResponse(BaseModel):
    request_id: str
    status: Status
    created_at: str
    service_version: str
    checks: dict[str, int | bool | str]
