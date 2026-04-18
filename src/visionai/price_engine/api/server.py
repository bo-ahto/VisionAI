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
    EstimateRequest,
    EstimateResponse,
    EstimateValidateRequest,
    EstimateValidateResponse,
    ModelInfoResponse,
    PredictRequest,
    PredictResponse,
    PredictV2Request,
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
_max_session: int = 486  # 데이터 로드 시 갱신

CONFIDENCE_MARGINS = {"A": 0.20, "B": 0.30, "C": 0.50, "D": 0.70}


def _load_resources() -> None:
    """모델 + calibration factors + 작가 데이터를 로드한다."""
    global _model, _factors, _works_full

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
    est_v = (
        (valid["추정가(최저)"].astype(float) + valid["추정가(최고)"].astype(float)) / 2
    ).values
    _factors = fit_calibration(y_true_v, y_pred_v, valid["타입"].values, est_v)

    global _max_session
    _max_session = int(df["회차"].max())
    logger.info("Resources loaded successfully (max session: %d)", _max_session)


def _load_estimate_generator() -> None:
    """Phase 3 추정가 생성기 로드 (모델 파일 존재 시)."""
    global _estimate_generator
    model_a_path = ROOT / "model_test_results" / "model_a_quantile.cbm"
    model_b_path = ROOT / "model_test_results" / "model_b_estimate.cbm"

    if not model_a_path.exists() or not model_b_path.exists():
        logger.info("Phase 3 models not found. Estimate generator not loaded.")
        return

    from visionai.price_engine.estimate_generator.estimate_calibrator import (
        EstimateCalibrator,
    )
    from visionai.price_engine.estimate_generator.estimate_model import (
        EstimateRegressorModel,
    )
    from visionai.price_engine.estimate_generator.generator import EstimateGenerator
    from visionai.price_engine.estimate_generator.quantile_calibrator import (
        QuantileCalibrator,
    )
    from visionai.price_engine.estimate_generator.quantile_model import (
        HedonicQuantileModel,
    )

    model_a = HedonicQuantileModel()
    model_a.load(model_a_path)
    model_b = EstimateRegressorModel()
    model_b.load(model_b_path)
    q_cal = QuantileCalibrator()
    q_cal_path = ROOT / "model_test_results" / "quantile_calibrator.pkl"
    if q_cal_path.exists():
        q_cal.load(str(q_cal_path))
    else:
        logger.warning("Quantile calibrator not found. Using uncalibrated.")
        q_cal._fitted = True

    e_cal = EstimateCalibrator()
    e_cal_path = ROOT / "model_test_results" / "estimate_calibrator.pkl"
    if e_cal_path.exists():
        e_cal.load(str(e_cal_path))
    else:
        logger.warning("Estimate calibrator not found. Using uncalibrated.")
        e_cal._fitted = True

    # v2 엔진 로드 (모델 파일 존재 시)
    v2_path = ROOT / "model_test_results" / "price_engine_v2.cbm"
    price_engine_v2 = None
    if v2_path.exists():
        from visionai.price_engine.models.target_transform_v2 import PriceEngineV2

        price_engine_v2 = PriceEngineV2()
        # v2 모델은 CatBoost로 직접 로드
        price_engine_v2._model = CatBoostRegressor()
        price_engine_v2._model.load_model(str(v2_path))
        logger.info("v2 engine loaded from %s", v2_path)

    _estimate_generator = EstimateGenerator(
        model_a=model_a, model_b=model_b,
        quantile_calibrator=q_cal, estimate_calibrator=e_cal,
        price_engine_v2=price_engine_v2,
    )
    logger.info("Phase 3 estimate generator loaded.")


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    """서버 시작 시 모델 로드."""
    _load_resources()
    _load_estimate_generator()
    yield


app = FastAPI(
    title="VisionAI Price Prediction API",
    description="K-Auction 미술품 경매 가격 예측 엔진",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, object]:
    """헬스체크."""
    return {"status": "ok", "model_loaded": _model is not None}


@app.post("/api/v1/predict_price", response_model=PredictResponse)
async def predict_price(req: PredictRequest) -> PredictResponse:
    """단건 가격 예측."""
    if _model is None or _factors is None or _works_full is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        return _run_prediction(req)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Prediction failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Prediction error: {type(e).__name__}") from e


def _run_prediction(req: PredictRequest) -> PredictResponse:
    """예측 내부 로직 (예외 처리 분리)."""
    # 입력 → 피처 조립
    dim = parse_dimension(f"{req.width_cm}x{req.height_cm}cm")
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

    row = pd.DataFrame(
        [
            {
                "artist_clean": artist_clean,
                "medium_category": med.medium_category,
                "support_category": med.support_category,
                "타입": req.auction_type.value,
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
                "회차": _max_session,
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
            }
        ]
    )

    # 예측
    y_pred_raw = predict_transform(_model, row)
    est_mid_arr = np.array([est_mid])
    y_pred = apply_calibration(
        y_pred_raw, np.array([req.auction_type.value]), est_mid_arr, _factors, blend_weight=0.0
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
        features_count=22,  # BASELINE_FEATURES 22개 (artist_sell_rate 포함)
        test_mape=27.01,
        test_r2=0.936,
        a_grade_within_20pct=71.6,
        gate_status="9/9 passed",
    )


# ─── Phase 3: 추정가 생성 엔드포인트 ───


_estimate_generator = None  # Phase 3 모델 — lifespan에서 로드


def _build_estimate_input(req: EstimateRequest) -> pd.DataFrame:
    """EstimateRequest → 50개 HEDONIC_FEATURES DataFrame (단건).

    HEDONIC_FEATURES 스키마 변경 시 이 함수도 반드시 동기화할 것.
    현재 50개 피처 + API 내부용 보조 컬럼(타입/회차/Lot 등)을 함께 생성.
    """
    dim = parse_dimension(f"{req.width_cm}x{req.height_cm}cm")
    med = parse_medium(req.medium)
    _year = parse_year(str(req.year) if req.year else None)  # 향후 year 피처 사용
    sa = dim.surface_area or 0.0
    width = dim.width_cm or 0.0
    height = dim.height_cm or 0.0
    short_side = float(min(width, height)) if (width > 0 and height > 0) else float(max(width, height))
    long_side = float(max(width, height))
    size_ho_val = sa / 132.0 if sa > 0 else 0.0

    df_input = pd.DataFrame([{
        # ── 선두 범주형 (5) ──
        "artist_clean": req.artist,
        "medium_category": med.medium_category,
        "support_category": med.support_category,
        "is_3d": dim.is_3d,
        "is_untitled": False,
        # ── 작가 집계/프로필 (서빙 시 기본값, 엔진 내부 조인으로 덮어씀) ──
        "artist_avg_price": 0.0,
        "artist_median_price": 0.0,
        "artist_max_price": 0.0,
        "artist_price_volatility": np.nan,
        "artist_total_sold": 0,
        "is_new_artist": True,
        "is_deceased": False,
        "artist_birth_year": np.nan,
        "artist_age_at_sale": np.nan,
        # ── 인터랙션 ──
        "artist_medium_price_ratio": 1.0,
        "artist_medium_frequency": 0.0,
        "medium_size_avg_price": np.nan,
        "medium_avg_price": np.nan,
        "price_segment_median": np.nan,
        "auction_house_tier": 3,
        # ── 크기 블록 ──
        "ln_surface_area": float(np.log(sa)) if sa > 0 else 0.0,
        "short_side_cm": short_side,
        "long_side_cm": long_side,
        "size_ho": size_ho_val,
        "size_ho_above40": max(0.0, size_ho_val - 40.0),
        "aspect_ratio": dim.aspect_ratio or 1.0,
        # ── 시장/작가 시계열 ──
        "market_price_index": 0.0,
        "artist_price_trend": np.nan,
        "artist_price_momentum": np.nan,
        "artist_auctions_since_last": np.nan,
        "artist_last_hammer_price": np.nan,
        "artist_recent_avg_price": np.nan,
        "artist_sale_frequency": np.nan,
        "artist_lot_count_trend": np.nan,
        "artist_career_length": np.nan,
        "artist_unsold_rate": np.nan,
        # ── 비교 거래 ──
        "comp_artist_avg": np.nan,
        "title_subject": "",
        "comp_weighted": np.nan,
        "comp_match_count": 0.0,
        "comp_medium_avg": np.nan,
        "size_bucket": "",
        "orientation": "",
        "comp_to_avg_ratio": np.nan,
        "comp_match_level": 4.0,
        "source_count": 0,
        "global_median_price": np.nan,
        "global_auction_count": 0.0,
        "has_global_price": 0,
        "artist_nationality": "UN",
        # ── API 내부용 보조 컬럼 (HEDONIC_FEATURES에는 없지만 파이프라인/로그용) ──
        "height_cm": height,
        "width_cm": width,
        "surface_area": sa,
        "is_size_imputed": dim.is_size_imputed,
        "회차": _max_session,
        "타입": req.auction_type.value,
        "Lot": 0,
        "is_year_missing": _year.is_year_missing if _year else True,
    }])

    # Phase 4 NLP 피처 — 실제 제목에서 추출
    from visionai.price_engine.features.title_nlp import extract_title_features

    title_text = req.title if hasattr(req, "title") and req.title else ""
    nlp = extract_title_features(pd.Series([title_text]))
    for col in nlp.columns:
        df_input[col] = nlp[col].values

    return df_input


@app.post("/api/v1/estimate", response_model=EstimateResponse)
async def generate_estimate_endpoint(req: EstimateRequest) -> EstimateResponse:
    """추정가 생성 API — Model-A + Model-B 통합 파이프라인."""
    if _estimate_generator is None:
        return EstimateResponse(
            price_range={"low": 0, "mid": 0, "high": 0},
            estimate={"low": 0, "mid": 0, "high": 0},
            confidence_grade="D",
            cold_start_tier=None,
            warnings=["Phase 3 모델 미로드"],
        )

    df = _build_estimate_input(req)
    result = _estimate_generator.generate(df, is_new_artist=True)
    pr = result["price_range"]
    est = result["estimate"]
    return EstimateResponse(
        price_range={
            "low": int(pr["low"][0]),
            "mid": int(pr["mid"][0]),
            "high": int(pr["high"][0]),
        },
        estimate={
            "low": int(est["low"][0]),
            "mid": int(est["mid"][0]),
            "high": int(est["high"][0]),
        },
        confidence_grade=result["confidence_grade"],
        cold_start_tier=result["cold_start_tier"],
        warnings=[],
    )


@app.post("/api/v1/estimate/validate", response_model=EstimateValidateResponse)
async def validate_estimate_endpoint(
    req: EstimateValidateRequest,
) -> EstimateValidateResponse:
    """추정가 검증 API — 세그먼트별 차등 경고 기준."""
    if _estimate_generator is None:
        kauction_mid = int(
            (req.kauction_estimate_low + req.kauction_estimate_high) / 2
        )
        return EstimateValidateResponse(
            ai_estimate_mid=0,
            kauction_mid=kauction_mid,
            divergence_rate=0.0,
            threshold_pct=30.0,
            warning=False,
            message="Phase 3 모델 미로드",
        )

    df = _build_estimate_input(req)
    result = _estimate_generator.validate_estimate(
        df,
        kauction_low=req.kauction_estimate_low,
        kauction_high=req.kauction_estimate_high,
        auction_type=req.auction_type.value,
    )
    return EstimateValidateResponse(**result)


@app.post("/api/v1/predict_v2")
async def predict_v2_endpoint(req: PredictV2Request) -> dict:
    """v2 모드: 생성 추정가 기반 낙찰가 예측.

    추정가 미입력 시 Model-B가 자동 생성.
    """
    if _estimate_generator is None:
        raise HTTPException(503, "Phase 3 모델 미로드")

    df = _build_estimate_input(
        EstimateRequest(
            artist=req.artist,
            medium=req.medium,
            width_cm=req.width_cm,
            height_cm=req.height_cm,
            year=req.year,
            auction_type=req.auction_type,
        )
    )

    if _estimate_generator.price_engine_v2 is None:
        raise HTTPException(503, "v2 엔진 미로드")

    # 사용자 입력 추정가가 있으면 사용, 없으면 Model-B 자동 생성
    if req.estimate_low is not None and req.estimate_high is not None:
        import numpy as np

        est_mid_arr = np.array([(req.estimate_low + req.estimate_high) / 2])
        est_low_arr = np.array([req.estimate_low])
        est_high_arr = np.array([req.estimate_high])
        predicted = _estimate_generator.price_engine_v2.predict(
            df, est_mid=est_mid_arr, est_low=est_low_arr, est_high=est_high_arr,
        )
        return {
            "predicted_price": int(predicted[0]),
            "estimate_used": {
                "low": req.estimate_low,
                "mid": int(est_mid_arr[0]),
                "high": req.estimate_high,
            },
        }

    result = _estimate_generator.predict_with_v2(df)
    return {
        "predicted_price": int(result["predicted_price"][0]),
        "estimate_used": {
            "low": int(result["estimate_used"]["low"][0]),
            "mid": int(result["estimate_used"]["mid"][0]),
            "high": int(result["estimate_used"]["high"][0]),
        },
    }
