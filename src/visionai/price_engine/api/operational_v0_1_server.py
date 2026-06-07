"""FastAPI server for the price_prediction v0.1 operational package."""

from __future__ import annotations

import logging
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse

from visionai.price_engine.api.operational_v0_1_schemas import (
    CurrentModelResponse,
    ErrorBody,
    ErrorResponse,
    PriceEstimateRequest,
    PriceEstimateResponse,
    ResolveArtistRequest,
    ResolveArtistResponse,
)
from visionai.price_engine.api.operational_v0_1_service import (
    OperationalV01Service,
    now_kst_iso,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

_service: OperationalV01Service | None = None
STATIC_DIR = Path(__file__).resolve().parent / "static"


def request_id() -> str:
    return f"req_{uuid.uuid4().hex[:16]}"


def model_root_from_env() -> Path | None:
    value = os.getenv("PRICE_PREDICTION_V01_MODEL_ROOT")
    return Path(value).expanduser().resolve() if value else None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global _service
    _service = OperationalV01Service(model_root=model_root_from_env())
    logger.info("price_prediction v0.1 operational service loaded")
    yield


app = FastAPI(
    title="VisionAI Price Prediction API",
    version="0.1.0",
    description="price_prediction_v0.1 운영용 가격 예측 API",
    lifespan=lifespan,
)


def service() -> OperationalV01Service:
    if _service is None:
        raise HTTPException(status_code=503, detail="MODEL_UNAVAILABLE")
    return _service


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    code = str(exc.detail) if isinstance(exc.detail, str) else "INVALID_REQUEST"
    status_code = exc.status_code
    if status_code == 503:
        code = "MODEL_UNAVAILABLE"
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            request_id=request_id(),
            created_at=now_kst_iso(),
            error=ErrorBody(code=code, message=_error_message(code)),
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled operational v0.1 API error: %s", exc)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            request_id=request_id(),
            created_at=now_kst_iso(),
            error=ErrorBody(
                code="MODEL_INFERENCE_FAILED",
                message="모델 추론 중 오류가 발생했습니다.",
            ),
        ).model_dump(),
    )


@app.get("/health")
async def health() -> dict[str, object]:
    loaded = _service is not None
    return {
        "status": "ok" if loaded else "loading",
        "model_version": "price_prediction_v0.1",
        "operational_loaded": loaded,
    }


@app.get("/test/v0.1", response_class=HTMLResponse)
@app.get("/test/v0.1/result", response_class=HTMLResponse)
async def operational_test_page() -> HTMLResponse:
    page = STATIC_DIR / "operational_v0_1_test.html"
    if not page.exists():
        raise HTTPException(status_code=404, detail="TEST_PAGE_NOT_FOUND")
    return HTMLResponse(page.read_text(encoding="utf-8"))


@app.get("/api/v1/price-models/current", response_model=CurrentModelResponse)
async def current_model() -> CurrentModelResponse:
    return service().current_model(request_id())


@app.post("/api/v1/artists:resolve", response_model=ResolveArtistResponse)
async def resolve_artist(payload: ResolveArtistRequest) -> ResolveArtistResponse:
    return service().resolve_artist(
        request_id=request_id(),
        artist=payload.artist,
        max_candidates=payload.options.max_candidates,
    )


@app.post("/api/v1/artworks/price-estimate", response_model=PriceEstimateResponse)
async def price_estimate(payload: PriceEstimateRequest) -> PriceEstimateResponse:
    if payload.artwork.dimensions.width_cm is None or payload.artwork.dimensions.height_cm is None:
        raise HTTPException(status_code=422, detail="INVALID_DIMENSIONS")
    return service().estimate_price(request_id(), payload)


def _error_message(code: str) -> str:
    messages = {
        "MODEL_UNAVAILABLE": "모델 서버 또는 artifact를 사용할 수 없습니다.",
        "INVALID_DIMENSIONS": "width_cm 또는 height_cm 값이 비정상입니다.",
        "MODEL_INFERENCE_FAILED": "모델 추론 중 오류가 발생했습니다.",
        "INVALID_REQUEST": "요청 형식이 올바르지 않습니다.",
    }
    return messages.get(code, "요청 처리 중 오류가 발생했습니다.")
