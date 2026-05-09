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

    # v3.6 Phase 1 PR1: V_year_saatchi_warm enrichment 후크
    # (v3.5 step 2 §2.1 spec — saatchi-and-warm cohort 만 활성화)
    artwork_id: str | None = Field(
        None,
        max_length=64,
        description=(
            "Saatchi artwork ID. Saatchi & warm 작가 작품에 한해 year_made enrichment "
            "cache key 로 사용. 미제공 시 enrichment skip (cohort gating fail 시에도 무관)."
        ),
    )
    artwork_url: str | None = Field(
        None,
        max_length=500,
        description=(
            "Saatchi artwork detail page URL. artwork_id 미제공 시 fallback enrichment "
            "lookup 용. URL alias cache 등록."
        ),
    )
    year_made: int | None = Field(
        None,
        ge=1800,
        le=2030,
        description=(
            "작품 제작년도 (manual override). client 직접 제공 시 enrichment fetch skip + "
            "cache write-through (artwork_id 함께 제공 시). [1800, 2030] 범위 외 → 422 reject."
        ),
    )


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
    # PR2A.5: source-conditional routing (additive / backward compat / default OFF)
    routing_source: str | None = None  # "artsy" / "saatchi" / "unified"
    routing_reason: str | None = None  # "matched_artsy" / "router_off" / 등
    routed_variant: str | None = None  # "source_conditional_v1_artsy" / "v3_filtered_tuned" / 등


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

    # v3.6 Phase 1 PR1: PredictRequest 와 동일 V_year_saatchi_warm 후크
    artwork_id: str | None = Field(None, max_length=64)
    artwork_url: str | None = Field(None, max_length=500)
    year_made: int | None = Field(None, ge=1800, le=2030)


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
    """모델 정보 응답.

    NOTE on metrics interpretation:
    - mdape_groupkfold: cold path (CatBoost) MdAPE.
      v3-tuned-cal 모델인 경우 source x target_market cell calibration 적용된
      cross-fit guarded 추정치. guard cell selection이 동일 OOF 결과 보고 결정되어
      post-hoc selection bias 잔존 — 보수적 추정치로 해석 권장.
    - mdape_kfold: warm path (XGBoost) MdAPE on warm slice (artist_count>=5) baseline.
      서빙은 warm path에 calibration 적용 안 함 (factor 1.0 근처, noise).
    """

    model_version: str
    training_count: int
    artist_count: int
    mdape_groupkfold: float
    mdape_kfold: float
    features_count: int
    # PR2A.5: router metadata (additive / backward compat)
    router_mode: str | None = None  # "off" / "shadow" / "canary" / "on"
    default_variant: str | None = None  # default = "v3_filtered_tuned"
    available_variants: list[str] | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    model_version: str
    artists_loaded: int
    uptime_seconds: float


# v3.6 PR12 (코덱스 PR11d Nit): /api/v1/monitor response_model — backward compat
# consumer 계약 고정. additive change OK, key 삭제/rename 은 break.


class FetchGateStats(BaseModel):
    """v3.5 step 3 §3.2.3 fetch gate runtime metrics."""
    concurrent: int
    miss_5min: int
    consecutive_fails: int
    cool_down_remaining_sec: int
    tokens_available: float
    inflight: int
    warmup_mode: bool
    warmup_remaining_sec: int


class MonitorResponse(BaseModel):
    total_predictions: int
    by_grade: dict[str, int]
    by_model: dict[str, int]
    avg_ms: float
    external_lookup_count: int
    known_artist_count: int
    uptime_seconds: float
    fetch_gate: FetchGateStats
    cache_epoch: str
    server_instance: str
    worker_instance_id: str  # PR12: process-local uuid (multi-worker 식별)
