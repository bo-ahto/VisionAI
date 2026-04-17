"""Phase 1 1차 시장 가격 예측 API 서버."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
import urllib.request
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
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
    BatchPredictRequest,
    BatchPredictResponse,
    BatchPredictResult,
    ArtistPriceHistory,
    PriceHistoryItem,
    MatchedArtwork,
)
from .artist_matcher import ArtistMatcher
from .primary_feature_builder import build_features
from .primary_predictor import PrimaryPredictor, CB_FEATURES, CAT_FEATURES
from . import external_collector
from . import shap_explainer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ─── 글로벌 상태 ───
_matcher = ArtistMatcher()
_predictor = PrimaryPredictor()
_start_time = time.time()
_model_version = "v3"
_price_history: dict[str, list[dict]] = {}  # artist_slug → [작품 이력]

# ─── 인메모리 모니터링 카운터 ───
_monitor = {
    "total_predictions": 0,
    "by_grade": {"A": 0, "B": 0, "C": 0, "D": 0},
    "by_model": {},
    "total_ms": 0,
    "external_lookup_count": 0,
    "known_artist_count": 0,
}

# ─── 예측 로그 (JSONL 파일) ───
_LOG_DIR = Path(os.getenv("LOG_DIR", "/app/logs"))
_log_file = None


def _init_log() -> None:
    global _log_file
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    _log_file = open(_LOG_DIR / "predictions.jsonl", "a", encoding="utf-8")
    logger.info("Prediction log: %s", _LOG_DIR / "predictions.jsonl")


def _log_prediction(entry: dict) -> None:
    # 인메모리 카운터 업데이트
    _monitor["total_predictions"] += 1
    grade = entry.get("confidence_grade", "D")
    _monitor["by_grade"][grade] = _monitor["by_grade"].get(grade, 0) + 1
    mt = entry.get("model_type", "unknown")
    _monitor["by_model"][mt] = _monitor["by_model"].get(mt, 0) + 1
    _monitor["total_ms"] += entry.get("total_ms", 0)
    if entry.get("is_known_artist"):
        _monitor["known_artist_count"] += 1
    if entry.get("has_manual_profile") or len(entry.get("external_sources", [])) > 0:
        _monitor["external_lookup_count"] += 1

    # 파일 적재
    if _log_file:
        try:
            _log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")
            _log_file.flush()
        except Exception as e:
            logger.warning("Log write failed: %s", e)


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
        "User-Agent": "VisionAI-API/1.0",
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
        # artists와 profiles를 분리, 소스 우선순위 적용 (artsy > saatchi > web)
        SOURCE_PRIORITY = {"artsy": 0, "saatchi": 1, "web": 2}
        artists = []
        profiles = []
        seen_artists = set()
        best_profile: dict[int, tuple[int, dict]] = {}  # artist_id → (priority, profile)

        for r in rows:
            aid = r["id"]
            if aid not in seen_artists:
                seen_artists.add(aid)
                artists.append(r)
            if r.get("total_works") is not None:
                src = r.get("source", "web")
                prio = SOURCE_PRIORITY.get(src, 2)
                prof = {"artist_id": aid, "source": src, **{k: r[k] for k in
                    ["birth_year_from_source", "total_works", "followers",
                     "solo_count", "group_count", "fair_count",
                     "career_stage", "profile_completeness"] if k in r}}
                if aid not in best_profile or prio < best_profile[aid][0]:
                    best_profile[aid] = (prio, prof)

        profiles = [v[1] for v in best_profile.values()]
        _matcher.load_from_data(artists, profiles)
        logger.info("Artist index loaded: %d artists, %d profiles", _matcher.count, len(profiles))
    except Exception as e:
        logger.error("DB load failed: %s (type: %s)", e, type(e).__name__)
        import traceback
        logger.error("Traceback: %s", traceback.format_exc())


def _load_price_history() -> None:
    """학습 데이터에서 작가별 가격 이력을 로드."""
    global _price_history
    data_dir = Path(os.getenv("DATA_DIR", "/app/data"))
    paths = [
        data_dir / "primary_market_dataset.parquet",
        Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "primary_market_dataset.parquet",
    ]
    saatchi_paths = [
        data_dir / "saatchi_cleaned.parquet",
        Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "saatchi_cleaned.parquet",
    ]

    for p in paths:
        if p.exists():
            try:
                df = pd.read_parquet(p, columns=[
                    "artist_slug", "artist_name", "title", "price_krw", "ho",
                    "medium_category", "gallery_name",
                ])
                for slug, grp in df.groupby("artist_slug"):
                    _price_history[str(slug)] = [
                        {"title": str(r.get("title", ""))[:50], "price_krw": int(r["price_krw"]),
                         "ho": int(r.get("ho", 0)), "medium": str(r.get("medium_category", "")),
                         "gallery": str(r.get("gallery_name", "")), "source": "artsy"}
                        for _, r in grp.iterrows()
                    ]
                logger.info("Price history loaded: %d artists from %s", len(_price_history), p)
                break
            except Exception as e:
                logger.warning("Price history load failed: %s", e)

    for p in saatchi_paths:
        if p.exists():
            try:
                df = pd.read_parquet(p, columns=[
                    "artist_slug", "artist_name", "title", "price_krw", "ho",
                    "medium_category", "gallery_name",
                ])
                for slug, grp in df.groupby("artist_slug"):
                    key = str(slug)
                    items = [
                        {"title": str(r.get("title", ""))[:50], "price_krw": int(r["price_krw"]),
                         "ho": int(r.get("ho", 0)), "medium": str(r.get("medium_category", "")),
                         "gallery": "Saatchi Art", "source": "saatchi"}
                        for _, r in grp.iterrows()
                    ]
                    if key in _price_history:
                        _price_history[key].extend(items)
                    else:
                        _price_history[key] = items
                logger.info("Saatchi history added: total %d artists", len(_price_history))
                break
            except Exception as e:
                logger.warning("Saatchi history load failed: %s", e)


def _get_artist_history(artist_slug: str, artist_name: str) -> ArtistPriceHistory | None:
    """작가의 가격 이력 요약."""
    items = _price_history.get(artist_slug, [])
    if not items:
        return None

    prices = [i["price_krw"] for i in items]
    hos = [i["ho"] for i in items]
    mediums = list(set(i["medium"] for i in items if i["medium"]))
    galleries = list(set(i["gallery"] for i in items if i["gallery"]))
    sources = set(i.get("source", "") for i in items)

    # 수집 날짜 (소스별)
    dates = []
    if "artsy" in sources:
        dates.append("Artsy 2026-04-13")
    if "saatchi" in sources:
        dates.append("Saatchi 2026-04-16")
    collected = ", ".join(dates) if dates else "2026-04"

    # 비슷한 크기 순으로 정렬, 상위 5건
    items_sorted = sorted(items, key=lambda x: x["price_krw"], reverse=True)
    samples = [
        PriceHistoryItem(
            title=i["title"], price_krw=i["price_krw"], ho=i["ho"],
            medium=i["medium"], gallery=i["gallery"], source=i.get("source", "")
        )
        for i in items_sorted[:5]
    ]

    return ArtistPriceHistory(
        artist_name=artist_name,
        total_works_in_data=len(items),
        price_min=min(prices),
        price_max=max(prices),
        price_median=int(sorted(prices)[len(prices) // 2]),
        ho_range=f"{min(hos)}~{max(hos)}호",
        mediums=mediums[:5],
        galleries=galleries[:5],
        data_collected_date=collected,
        samples=samples,
    )


def _find_matched_artworks(
    artist_slug: str, title: str | None, ho: int, medium_category: str
) -> list[MatchedArtwork]:
    """학습 데이터에서 동일/유사 작품 매칭."""
    items = _price_history.get(artist_slug, [])
    if not items:
        return []

    matched = []

    # 1. 제목 + 호수 정확 매칭
    if title:
        title_norm = title.lower().strip()
        for item in items:
            if title_norm in item["title"].lower() and item["ho"] == ho:
                matched.append(MatchedArtwork(
                    title=item["title"], price_krw=item["price_krw"],
                    price_usd=item["price_krw"] // 1380,
                    ho=item["ho"], medium=item["medium"],
                    gallery=item["gallery"], source=item.get("source", ""),
                    match_type="exact_title_size",
                ))
        # 제목만 매칭 (크기 다른 경우 참고용)
        if not matched:
            for item in items:
                if title_norm in item["title"].lower():
                    matched.append(MatchedArtwork(
                        title=item["title"], price_krw=item["price_krw"],
                        price_usd=item["price_krw"] // 1380,
                        ho=item["ho"], medium=item["medium"],
                        gallery=item["gallery"], source=item.get("source", ""),
                        match_type="same_title_diff_size",
                    ))

    # 2. 동일 호수 + 동일 매체
    if not matched:
        for item in items:
            if item["ho"] == ho and item["medium"] == medium_category:
                matched.append(MatchedArtwork(
                    title=item["title"], price_krw=item["price_krw"],
                    price_usd=item["price_krw"] // 1380,
                    ho=item["ho"], medium=item["medium"],
                    gallery=item["gallery"], source=item.get("source", ""),
                    match_type="same_size_medium",
                ))

    # 3. 유사 호수 (±1단계)
    if not matched:
        from .primary_feature_builder import HO_TABLE_F
        ho_list = sorted(HO_TABLE_F.keys())
        idx = min(range(len(ho_list)), key=lambda i: abs(ho_list[i] - ho))
        nearby = set()
        if idx > 0: nearby.add(ho_list[idx - 1])
        nearby.add(ho_list[idx])
        if idx < len(ho_list) - 1: nearby.add(ho_list[idx + 1])

        for item in items:
            if item["ho"] in nearby and item["medium"] == medium_category:
                matched.append(MatchedArtwork(
                    title=item["title"], price_krw=item["price_krw"],
                    price_usd=item["price_krw"] // 1380,
                    ho=item["ho"], medium=item["medium"],
                    gallery=item["gallery"], source=item.get("source", ""),
                    match_type="similar_size",
                ))

    # 중복 제거 + 가격순 정렬, 최대 5건
    seen = set()
    unique = []
    for m in matched:
        key = (m.title, m.price_krw, m.ho)
        if key not in seen:
            seen.add(key)
            unique.append(m)
    unique.sort(key=lambda x: abs(x.ho - ho))
    return unique[:5]


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
    _load_price_history()
    _init_log()

    # SHAP explainer 초기화 (CatBoost 모델)
    if _predictor.cb_model:
        shap_explainer.init_explainer(_predictor.cb_model)

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

    status = "ok" if _matcher.count > 0 and db_status == "connected" else "degraded"
    return {
        "status": status,
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


@app.get("/api/v1/monitor")
async def monitor():
    """인메모리 카운터 기반 모니터링."""
    total = _monitor["total_predictions"]
    return {
        "total_predictions": total,
        "by_grade": _monitor["by_grade"],
        "by_model": _monitor["by_model"],
        "avg_ms": round(_monitor["total_ms"] / total, 1) if total else 0,
        "external_lookup_count": _monitor["external_lookup_count"],
        "known_artist_count": _monitor["known_artist_count"],
        "uptime_seconds": round(time.time() - _start_time, 1),
    }


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
    sources_used: list[str] = []
    external_ms = 0

    # 2.5 외부 수집 (DB 미매칭 시, threadpool에서 실행)
    if not is_matched and not req.skip_external_lookup:
        t_ext = time.time()
        loop = asyncio.get_event_loop()
        ext_profile, sources_used = await loop.run_in_executor(
            None, external_collector.collect, req.artist_name, False
        )
        external_ms = int((time.time() - t_ext) * 1000)
        if ext_profile:
            profile = ext_profile

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

    # SHAP 설명 (CatBoost 경로만, threadpool에서 실행)
    feature_contributions = []
    if result["model_type"] == "catboost_v3":
        def _compute_shap():
            df_explain = pd.DataFrame([features])
            for col in CAT_FEATURES:
                if col in df_explain.columns:
                    df_explain[col] = df_explain[col].astype(str).fillna("unknown")
            return shap_explainer.explain(df_explain[CB_FEATURES], CB_FEATURES)
        loop = asyncio.get_event_loop()
        feature_contributions = await loop.run_in_executor(None, _compute_shap)

    total_ms = int((time.time() - t0) * 1000)

    # 예측 로그 (JSONL)
    _log_prediction({
        "id": str(uuid.uuid4()),
        "ts": datetime.now(timezone.utc).isoformat(),
        "artist_name_input": req.artist_name,
        "artist_id": match.artist_id if match else None,
        "artist_matched": match.name if match else None,
        "match_score": match.score if match else 0,
        "width_cm": req.width_cm,
        "height_cm": req.height_cm,
        "medium": req.medium,
        "target_market": req.target_market,
        "predicted_krw": result["price_krw"],
        "price_range_low": result["price_range_low"],
        "price_range_high": result["price_range_high"],
        "confidence_grade": result["confidence_grade"],
        "model_type": result["model_type"],
        "is_known_artist": result["is_known_artist"],
        "training_count": result["training_count"],
        "has_manual_profile": has_manual,
        "total_ms": total_ms,
    })

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
        processing=Processing(total_ms=total_ms, external_fetch_ms=external_ms),
        external_sources_used=sources_used,
        feature_contributions=[
            {"feature": c["feature"], "value": c["value"], "contribution": c["contribution"]}
            for c in feature_contributions
        ],
        matched_artworks=_find_matched_artworks(
            match.slug if match else "", req.title,
            features.get("ho", 0), features.get("medium_category", "")
        ) if is_matched else [],
        artist_price_history=_get_artist_history(
            match.slug if match else "", match.name if match else req.artist_name
        ) if is_matched else None,
    )


@app.post("/api/v1/predict/batch", response_model=BatchPredictResponse)
async def predict_batch(req: BatchPredictRequest):
    """배치 예측 (최대 50건). 작가 중복 시 외부 수집 1회만."""
    t0 = time.time()
    results = []
    success_count = 0
    fail_count = 0

    for i, item in enumerate(req.artworks):
        try:
            # 매칭
            match = _matcher.match(item.artist_name)
            is_matched = match is not None
            training_count = match.training_count if match else 0
            profile = match.profile if match else {}
            sources = []

            # 외부 수집
            if not is_matched and not req.skip_external_lookup:
                ext_profile, sources = external_collector.collect(item.artist_name)
                if ext_profile:
                    profile = ext_profile

            # manual override
            manual = {}
            if item.artist_birth_year is not None:
                manual["artist_birth_year"] = item.artist_birth_year
            if item.artist_total_works is not None:
                manual["artist_total_works"] = item.artist_total_works
            if item.solo_count is not None:
                manual["solo_count"] = item.solo_count
            if item.group_count is not None:
                manual["group_count"] = item.group_count
            if item.followers is not None:
                manual["followers"] = item.followers

            features = build_features(
                width_cm=item.width_cm, height_cm=item.height_cm,
                medium=item.medium, artist_profile=profile,
                target_market=item.target_market, manual_overrides=manual,
            )
            result = _predictor.predict(
                features=features, is_matched=is_matched,
                training_count=training_count, target_market=item.target_market,
                has_manual_profile=len(manual) > 0,
            )

            results.append(BatchPredictResult(
                index=i, status="success",
                prediction=Prediction(
                    price_krw=result["price_krw"], price_usd=result["price_usd"],
                    price_range=PriceRange(low=result["price_range_low"], high=result["price_range_high"]),
                    confidence_grade=result["confidence_grade"], margin=result["margin"],
                ),
                model_info=ModelInfo(
                    model_type=result["model_type"], is_known_artist=result["is_known_artist"],
                    training_count=result["training_count"],
                ),
                external_sources_used=sources,
            ))
            success_count += 1
        except Exception as e:
            results.append(BatchPredictResult(
                index=i, status="error", error=str(e),
            ))
            fail_count += 1

    total_ms = int((time.time() - t0) * 1000)
    return BatchPredictResponse(
        total=len(req.artworks), success=success_count, failed=fail_count,
        results=results, processing=Processing(total_ms=total_ms),
    )
