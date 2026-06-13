"""FastAPI server for the official price_prediction_v0.1 service test."""

from __future__ import annotations

import logging
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from visionai.price_engine.api.official_v0_1_schemas import (
    CurrentModelResponse,
    ErrorBody,
    ErrorResponse,
    HealthResponse,
    ModelAuditResponse,
    PredictionLookupResponse,
    PriceEstimateRequest,
    PriceEstimateResponse,
    ResolveArtistRequest,
    ResolveArtistResponse,
    SalePriceFeedbackRequest,
    SalePriceFeedbackResponse,
)
from visionai.price_engine.api.official_v0_1_service import (
    OfficialV01Service,
    SERVICE_VERSION,
    now_kst_iso,
)


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

_service: OfficialV01Service | None = None
STATIC_DIR = Path(__file__).resolve().parent / "static"


def request_id() -> str:
    return f"req_{uuid.uuid4().hex[:16]}"


def db_path_from_env() -> Path | None:
    value = os.getenv("PRICE_PREDICTION_OFFICIAL_V01_DB_PATH")
    return Path(value).expanduser().resolve() if value else None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global _service
    _service = OfficialV01Service(db_path=db_path_from_env())
    logger.info("official price_prediction v0.1 service loaded")
    yield


app = FastAPI(
    title="VisionAI Official Price Prediction API v0.1",
    version="0.1.0",
    description="공식 테스트 v0.1 가격 예측 API",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def service() -> OfficialV01Service:
    if _service is None:
        raise HTTPException(status_code=503, detail="MODEL_UNAVAILABLE")
    return _service


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    code = str(exc.detail) if isinstance(exc.detail, str) else "INVALID_INPUT"
    status_code = exc.status_code
    if status_code == 503:
        code = "MODEL_UNAVAILABLE"
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            request_id=request_id(),
            created_at=now_kst_iso(),
            service_version=SERVICE_VERSION,
            error=ErrorBody(code=code, message=_error_message(code)),
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled official v0.1 API error: %s", exc)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            request_id=request_id(),
            created_at=now_kst_iso(),
            service_version=SERVICE_VERSION,
            error=ErrorBody(
                code="PREDICTION_FAILED",
                message="공식 v0.1 API 처리 중 오류가 발생했습니다.",
            ),
        ).model_dump(),
    )


@app.get("/health", response_model=HealthResponse)
@app.get("/api/v1/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return service().health(request_id())


@app.get("/test/v0.1", response_class=HTMLResponse)
@app.get("/test/v0.1/result", response_class=HTMLResponse)
async def official_test_page() -> HTMLResponse:
    page = STATIC_DIR / "official_v0_1_test.html"
    if not page.exists():
        raise HTTPException(status_code=404, detail="TEST_PAGE_NOT_FOUND")
    return HTMLResponse(page.read_text(encoding="utf-8"))


@app.get("/api/v1/price-models/current", response_model=CurrentModelResponse)
async def current_model() -> CurrentModelResponse:
    return service().current_model(request_id())


@app.post("/api/v1/artists/resolve", response_model=ResolveArtistResponse)
async def resolve_artist(payload: ResolveArtistRequest) -> ResolveArtistResponse:
    return service().resolve_artist(
        request_id=request_id(),
        artist_input=payload.artist,
        max_candidates=payload.options.max_candidates,
    )


@app.post("/api/v1/artworks/price-estimate", response_model=PriceEstimateResponse)
async def price_estimate(payload: PriceEstimateRequest) -> PriceEstimateResponse:
    if payload.artwork.dimensions.width_cm is None or payload.artwork.dimensions.height_cm is None:
        raise HTTPException(status_code=422, detail="INVALID_DIMENSIONS")
    return service().estimate_price(request_id(), payload)


@app.get("/api/v1/predictions/{prediction_id}", response_model=PredictionLookupResponse)
async def prediction_lookup(prediction_id: str) -> PredictionLookupResponse:
    return service().lookup_prediction(request_id(), prediction_id)


@app.post("/api/v1/feedback/sale-price", response_model=SalePriceFeedbackResponse)
async def sale_price_feedback(payload: SalePriceFeedbackRequest) -> SalePriceFeedbackResponse:
    return service().record_sale_price_feedback(request_id(), payload)


@app.get("/api/v1/admin/model-audit", response_model=ModelAuditResponse)
async def model_audit() -> ModelAuditResponse:
    return service().model_audit(request_id())


def _error_message(code: str) -> str:
    messages = {
        "MODEL_UNAVAILABLE": "모델 또는 DB/cache를 사용할 수 없습니다.",
        "DB_UNAVAILABLE": "DB/cache 연결에 실패했습니다.",
        "INVALID_INPUT": "입력 형식이 올바르지 않습니다.",
        "INVALID_DIMENSIONS": "작품 크기 값이 비정상입니다.",
        "ARTIST_REVIEW_REQUIRED": "작가 후보 선택 또는 검수가 필요합니다.",
        "MINIMUM_INPUT_FAILED": "최소 입력값이 부족합니다.",
        "PREDICTION_FAILED": "예측 계산 중 오류가 발생했습니다.",
        "TEST_PAGE_NOT_FOUND": "테스트 화면 파일을 찾을 수 없습니다.",
    }
    return messages.get(code, "요청 처리 중 오류가 발생했습니다.")
