"""Phase 1 1차 시장 가격 예측 API 서버."""
from __future__ import annotations

import json
import logging
import os
import time
import urllib.request
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException

from .primary_schemas import (
    ErrorResponse,
    HealthResponse,
    ModelInfoResponse,
    PredictRequest,
    PredictResponse,
    Prediction,
    PriceRange,
    ModelInfo,
    Processing,
)
from .artist_matcher import ArtistMatcher
from .primary_feature_builder import build_features
from .primary_predictor import PrimaryPredictor

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ─── 글로벌 상태 ───
_matcher = ArtistMatcher()
_predictor = PrimaryPredictor()
_start_time = time.time()
_model_version = "v3"


def _db_query(sql: str) -> dict:
    """postgres-proxy를 통한 DB 쿼리."""
    proxy_url = os.getenv("POSTGRES_PROXY_URL", "https://postgres-proxy.ahto.city")
    api_key = os.getenv("POSTGRES_PROXY_API_KEY", "")
    db_name = os.getenv("VISIONAI_DB", "visionai_dev")

    url = f"{proxy_url}/db/{db_name}/query"
    data = json.dumps({"sql": sql}).encode()
    req = urllib.request.Request(url, data=data, headers={
        "x-api-key": api_key,
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def _load_artist_index() -> None:
    """DB에서 작가 + 프로필 데이터를 단일 JOIN 쿼리로 로드."""
    logger.info("Loading artist index from DB...")
    try:
        result = _db_query(
            "SELECT a.id, a.name, a.name_ko, a.name_en, a.name_normalized, "
            "a.birth_year, a.source, a.artsy_slug, a.saatchi_id, "
            "a.is_in_training, a.training_count, "
            "p.birth_year_from_source, p.total_works, p.followers, "
            "p.solo_count, p.group_count, p.fair_count, "
            "p.career_stage, p.profile_completeness "
            "FROM artists a "
            "LEFT JOIN artist_profiles p ON a.id = p.artist_id AND p.status = 'success'"
        )
        rows = result.get("rows", [])
        # artists와 profiles를 분리해서 matcher에 전달
        artists = []
        profiles = []
        seen_artists = set()
        for r in rows:
            aid = r["id"]
            if aid not in seen_artists:
                seen_artists.add(aid)
                artists.append(r)
            if r.get("total_works") is not None:  # profile join이 있는 경우
                profiles.append({"artist_id": aid, **{k: r[k] for k in
                    ["birth_year_from_source", "total_works", "followers",
                     "solo_count", "group_count", "fair_count",
                     "career_stage", "profile_completeness"] if k in r}})
        _matcher.load_from_data(artists, profiles)
        logger.info("Artist index loaded: %d artists (from %d rows)", _matcher.count, len(rows))
    except Exception as e:
        logger.error("DB load failed: %s (type: %s)", e, type(e).__name__)
        import traceback
        logger.error("Traceback: %s", traceback.format_exc())


def _load_models() -> None:
    """모델 파일 로드."""
    model_dir = Path(os.getenv("MODEL_DIR", "/app/models"))
    if not model_dir.exists():
        # 로컬 개발 환경 폴백
        model_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / "model_test_results"

    _predictor.load_models(model_dir)

    # XGBoost label map 구축
    data_dir = Path(os.getenv("DATA_DIR", "/app/data"))
    training_path = data_dir / "primary_market_dataset.parquet"
    if not training_path.exists():
        training_path = Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "primary_market_dataset.parquet"
    _predictor.build_xgb_label_maps(training_path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작/종료 시 리소스 관리."""
    global _start_time
    _start_time = time.time()

    _load_models()
    _load_artist_index()

    logger.info("=== VisionAI Price Prediction API Ready ===")
    yield
    logger.info("=== Shutting down ===")


app = FastAPI(
    title="VisionAI 1차 시장 가격 예측 API",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    # DB 연결 테스트
    db_status = "unknown"
    try:
        r = _db_query("SELECT 1 AS ok")
        db_status = "connected" if r.get("rows") else "empty"
    except Exception as e:
        db_status = f"error: {e}"

    return {
        "status": "ok",
        "model_version": _model_version,
        "artists_loaded": _matcher.count,
        "uptime_seconds": round(time.time() - _start_time, 1),
        "db_status": db_status,
    }


@app.get("/api/v1/model/info", response_model=ModelInfoResponse)
async def model_info():
    return ModelInfoResponse(
        model_version=_model_version,
        training_count=29361,
        artist_count=1589,
        mdape_groupkfold=38.7,
        mdape_kfold=11.7,
        features_count=37,
    )


@app.post("/api/v1/predict", response_model=PredictResponse)
async def predict(req: PredictRequest):
    t0 = time.time()

    # 1. 입력 검증
    if req.target_market not in ("gallery", "online"):
        raise HTTPException(status_code=400, detail="target_market must be 'gallery' or 'online'")

    # 2. 작가 매칭
    match = _matcher.match(req.artist_name)
    is_matched = match is not None
    training_count = match.training_count if match else 0
    profile = match.profile if match else {}

    # 3. manual override 구성
    manual = {}
    if req.artist_birth_year is not None:
        manual["artist_birth_year"] = req.artist_birth_year
    if req.artist_total_works is not None:
        manual["artist_total_works"] = req.artist_total_works
    if req.solo_count is not None:
        manual["solo_count"] = req.solo_count
    if req.group_count is not None:
        manual["group_count"] = req.group_count
    if req.followers is not None:
        manual["followers"] = req.followers

    has_manual = len(manual) > 0

    # 4. 피처 생성
    features = build_features(
        width_cm=req.width_cm,
        height_cm=req.height_cm,
        medium=req.medium,
        artist_profile=profile,
        target_market=req.target_market,
        manual_overrides=manual,
    )

    # 5. 예측
    result = _predictor.predict(
        features=features,
        is_matched=is_matched,
        training_count=training_count,
        target_market=req.target_market,
        has_manual_profile=has_manual,
    )

    total_ms = int((time.time() - t0) * 1000)

    return PredictResponse(
        prediction=Prediction(
            price_krw=result["price_krw"],
            price_usd=result["price_usd"],
            price_range=PriceRange(low=result["price_range_low"], high=result["price_range_high"]),
            confidence_grade=result["confidence_grade"],
            margin=result["margin"],
        ),
        model_info=ModelInfo(
            model_type=result["model_type"],
            is_known_artist=result["is_known_artist"],
            training_count=result["training_count"],
        ),
        processing=Processing(total_ms=total_ms),
    )
