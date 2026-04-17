"""Phase 1 1차 시장 가격 예측 API 스키마."""
from __future__ import annotations

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    artist_name: str = Field(..., min_length=1, description="작가명")
    width_cm: float = Field(..., gt=0, le=500, description="가로 cm")
    height_cm: float = Field(..., gt=0, le=500, description="세로 cm")
    medium: str = Field(..., min_length=1, description="매체 (예: acrylic on canvas)")
    title: str | None = Field(None, max_length=200, description="작품 제목 (기존 작품 매칭용)")
    target_market: str = Field("gallery", description="gallery | online")
    skip_external_lookup: bool = Field(False, description="외부 수집 스킵 여부")

    # 선택 (수동 입력, 미입력 시 DB 프로필 사용)
    artist_birth_year: int | None = Field(None, ge=1900, le=2010)
    artist_total_works: int | None = Field(None, ge=0)
    solo_count: int | None = Field(None, ge=0)
    group_count: int | None = Field(None, ge=0)
    followers: int | None = Field(None, ge=0)


class PriceRange(BaseModel):
    low: int
    high: int


class Prediction(BaseModel):
    price_krw: int
    price_usd: int
    price_range: PriceRange
    confidence_grade: str
    margin: float


class ModelInfo(BaseModel):
    model_type: str
    is_known_artist: bool
    training_count: int


class Processing(BaseModel):
    total_ms: int
    external_fetch_ms: int = 0


class MatchedArtwork(BaseModel):
    title: str
    price_krw: int
    price_usd: int
    ho: int
    medium: str
    gallery: str
    source: str
    artwork_url: str = ""
    match_type: str = ""  # exact_title | same_size_medium | similar_size


class PriceHistoryItem(BaseModel):
    title: str
    price_krw: int
    ho: int
    medium: str
    gallery: str
    source: str


class ArtistPriceHistory(BaseModel):
    artist_name: str
    total_works_in_data: int
    price_min: int
    price_max: int
    price_median: int
    ho_range: str
    mediums: list[str]
    galleries: list[str]
    data_collected_date: str
    samples: list[PriceHistoryItem]


class FeatureContribution(BaseModel):
    feature: str
    value: str
    contribution: str


class PredictResponse(BaseModel):
    status: str = "success"
    prediction: Prediction
    model_info: ModelInfo
    processing: Processing
    external_sources_used: list[str] = []
    feature_contributions: list[FeatureContribution] = []
    matched_artworks: list[MatchedArtwork] = []
    artist_price_history: ArtistPriceHistory | None = None


class BatchItem(BaseModel):
    artist_name: str = Field(..., min_length=1)
    width_cm: float = Field(..., gt=0, le=500)
    height_cm: float = Field(..., gt=0, le=500)
    medium: str = Field(..., min_length=1)
    target_market: str = Field("gallery", pattern="^(gallery|online)$")
    artist_birth_year: int | None = None
    artist_total_works: int | None = None
    solo_count: int | None = None
    group_count: int | None = None
    followers: int | None = None


class BatchPredictRequest(BaseModel):
    artworks: list[BatchItem] = Field(..., max_length=50)
    skip_external_lookup: bool = False


class BatchPredictResult(BaseModel):
    index: int
    status: str
    prediction: Prediction | None = None
    model_info: ModelInfo | None = None
    external_sources_used: list[str] = []
    error: str | None = None


class BatchPredictResponse(BaseModel):
    total: int
    success: int
    failed: int
    results: list[BatchPredictResult]
    processing: Processing


class ErrorResponse(BaseModel):
    status: str = "error"
    error_code: str
    message: str


class ModelInfoResponse(BaseModel):
    model_version: str
    training_count: int
    artist_count: int
    mdape_groupkfold: float
    mdape_kfold: float
    features_count: int


class HealthResponse(BaseModel):
    status: str = "ok"
    model_version: str
    artists_loaded: int
    uptime_seconds: float
