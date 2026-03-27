"""FastAPI 가격 예측 서버.

기획서 참조: Sprint 3, 5.1 파이프라인
엔드포인트:
  POST /api/v1/predict_price — 단건 예측
  GET  /api/v1/model_info    — 모델 정보
  GET  /health               — 헬스체크
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from fastapi import FastAPI, HTTPException

from visionai.price_engine.api.schemas import (
    ModelInfoResponse,
    PredictRequest,
    PredictResponse,
)
from visionai.price_engine.models.segment_calibrator import (
    CalibrationFactors,
    apply_calibration,
    fit_calibration,
)
from visionai.price_engine.models.target_transform import predict_transform
from visionai.price_engine.preprocessing.dimension_parser import parse_dimension
from visionai.price_engine.preprocessing.medium_parser import parse_medium
from visionai.price_engine.preprocessing.year_parser import parse_year
from visionai.price_engine.validation.confidence_grade import assign_confidence_grade

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent

# 글로벌 상태
_model: CatBoostRegressor | None = None
_factors: CalibrationFactors | None = None
_works_full: pd.DataFrame | None = None

CONFIDENCE_MARGINS = {"A": 0.20, "B": 0.30, "C": 0.50, "D": 0.70}


def _load_resources() -> None:
    """모델 + calibration factors + 작가 데이터를 로드한다."""
    global _model, _factors, _works_full  # noqa: PLW0603

    model_path = ROOT / "model_test_results" / "target_transform_v1.cbm"
    data_path = ROOT / "data" / "preprocessed_features.parquet"

    logger.info("Loading model: %s", model_path)
    _model = CatBoostRegressor()
    _model.load_model(str(model_path))

    logger.info("Loading data: %s", data_path)
    df = pd.read_parquet(data_path)
    _works_full = df

    # Calibration from validation set
    valid = df[df["split"] == "valid"]
    y_pred_v = predict_transform(_model, valid)
    y_true_v = valid["낙찰가"].astype(float).values
    est_v = ((valid["추정가(최저)"].astype(float) + valid["추정가(최고)"].astype(float)) / 2).values
    _factors = fit_calibration(y_true_v, y_pred_v, valid["타입"].values, est_v)

    logger.info("Resources loaded successfully")


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    """서버 시작 시 모델 로드."""
    _load_resources()
    yield


app = FastAPI(
    title="VisionAI Price Prediction API",
    description="K-Auction 미술품 경매 가격 예측 엔진",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, str]:
    """헬스체크."""
    return {"status": "ok", "model_loaded": str(_model is not None)}


@app.post("/api/v1/predict_price", response_model=PredictResponse)
async def predict_price(req: PredictRequest) -> PredictResponse:
    """단건 가격 예측."""
    if _model is None or _factors is None or _works_full is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    # 입력 → 피처 조립
    dim = parse_dimension(f"{req.width_cm}×{req.height_cm}cm")
    med = parse_medium(req.medium)
    year = parse_year(str(req.year_created) if req.year_created else None)

    est_mid = (req.estimate_low + req.estimate_high) / 2
    est_range = req.estimate_high - req.estimate_low
    est_ratio = req.estimate_high / req.estimate_low if req.estimate_low > 0 else np.nan
    ln_est_mid = np.log(est_mid) if est_mid > 0 else 0

    # 작가 통계 조회 (최신 데이터 기준)
    artist_clean = req.artist_name if req.artist_name else "__UNKNOWN__"
    artist_data = _works_full[_works_full["artist_clean"] == artist_clean]
    artist_sold = int(artist_data["artist_total_sold"].max()) if len(artist_data) > 0 else 0
    artist_avg = int(artist_data["artist_avg_price"].max()) if len(artist_data) > 0 else 0
    artist_max = int(artist_data["artist_max_price"].max()) if len(artist_data) > 0 else 0
    is_new = len(artist_data) == 0

    row = pd.DataFrame([{
        "artist_clean": artist_clean,
        "medium_category": med.medium_category,
        "support_category": med.support_category,
        "타입": req.auction_type,
        "is_3d": str(dim.is_3d),
        "is_untitled": str(False),
        "ln_estimate_mid": ln_est_mid,
        "estimate_ratio": est_ratio,
        "estimate_range": est_range,
        "height_cm": dim.height_cm or 0,
        "width_cm": dim.width_cm or 0,
        "surface_area": dim.surface_area or 0,
        "aspect_ratio": dim.aspect_ratio or 0,
        "Lot": 1,
        "회차": 486,
        "artist_total_sold": artist_sold,
        "artist_avg_price": artist_avg,
        "artist_max_price": artist_max,
        "artist_sell_rate": 0,
        "is_size_imputed": 1 if dim.is_size_imputed else 0,
        "is_year_missing": 1 if year.is_year_missing else 0,
        "is_new_artist": 1 if is_new else 0,
        "추정가(최저)": req.estimate_low,
        "추정가(최고)": req.estimate_high,
        "estimate_mid": est_mid,
    }])

    # 예측
    y_pred_raw = predict_transform(_model, row)
    est_mid_arr = np.array([est_mid])
    y_pred = apply_calibration(
        y_pred_raw, np.array([req.auction_type]), est_mid_arr, _factors, blend_weight=0.0
    )
    predicted = int(y_pred[0])

    # 신뢰도
    grades = assign_confidence_grade(row, works_full=_works_full)
    grade = grades.iloc[0]
    margin = CONFIDENCE_MARGINS.get(grade, 0.50)

    price_low = int(predicted * (1 - margin))
    price_high = int(predicted * (1 + margin))
    ratio_vs_est = round(predicted / est_mid * 100, 1) if est_mid > 0 else 0

    return PredictResponse(
        predicted_price=predicted,
        price_range=[price_low, price_high],
        confidence_grade=grade,
        estimate_vs_prediction=ratio_vs_est,
        model_version="target_transform_v1+calibration",
    )


@app.get("/api/v1/model_info", response_model=ModelInfoResponse)
async def model_info() -> ModelInfoResponse:
    """모델 정보."""
    return ModelInfoResponse(
        model_version="target_transform_v1+calibration",
        model_type="CatBoost + Segment Calibration",
        features_count=21,
        test_mape=27.01,
        test_r2=0.936,
        a_grade_within_20pct=71.6,
        gate_status="9/9 passed",
    )
