"""Phase 1 1차 시장 가격 예측 API 서버."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import urllib.request
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException

from . import external_collector, shap_explainer
from .artist_matcher import ArtistMatcher
from .artwork_year_cache import (
    get_artwork_year,
    get_global_cache,
    seed_artwork_year,
)
from .primary_feature_builder import build_features
from .primary_predictor import (
    CAT_FEATURES,
    CB_FEATURES,
    SUPPORTED_VARIANTS,
    PrimaryPredictor,
)
from .primary_schemas import (
    ArtistPriceHistory,
    BatchPredictRequest,
    BatchPredictResponse,
    BatchPredictResult,
    ErrorResponse,
    HealthResponse,
    MatchedArtwork,
    ModelInfo,
    ModelInfoResponse,
    Prediction,
    PredictRequest,
    PredictResponse,
    PriceHistoryItem,
    PriceRange,
    Processing,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ─── 글로벌 상태 ───
_matcher = ArtistMatcher()
_predictor = PrimaryPredictor()
_start_time = time.time()
_model_version = "v3-tuned"  # 기본값. calibration artifact 로드 시 'v3-tuned-cal' (DB VARCHAR(20) 호환)
_model_info_cache: ModelInfoResponse | None = None  # startup에서 캐시 (Codex 5차 P2: stale 방지)
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
                        {"title": str(r.get("title", ""))[:200], "price_krw": int(r["price_krw"]),
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
                        {"title": str(r.get("title", ""))[:200], "price_krw": int(r["price_krw"]),
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


def _normalize_title(title: str) -> str:
    """제목 정규화: 소문자, 공백/특수문자 제거."""
    import re
    t = title.lower().strip()[:200]  # 200자 제한 (DoS 방지)
    t = re.sub(r"[^\w가-힣]", "", t)
    return t


# 전역 제목 인덱스 (startup 시 구축)
_title_index: dict[str, list[tuple[str, int]]] = {}  # normalized_title → [(artist_slug, item_idx)]


def _build_title_index() -> None:
    """제목 정규화 인덱스 구축 (global scan 최적화)."""
    global _title_index
    _title_index = {}
    for slug, items in _price_history.items():
        for i, item in enumerate(items):
            norm = _normalize_title(item["title"])
            if len(norm) >= 3:  # 너무 짧은 제목 제외 (과매칭 방지)
                if norm not in _title_index:
                    _title_index[norm] = []
                _title_index[norm].append((slug, i))
    logger.info("Title index built: %d unique titles", len(_title_index))


def _title_score(query: str, candidate: str) -> float:
    """제목 유사도 점수 (0~100)."""
    from rapidfuzz import fuzz
    q_norm = _normalize_title(query)
    c_norm = _normalize_title(candidate)
    if not q_norm or not c_norm:
        return 0
    if q_norm == c_norm:
        return 100
    # 부분 포함 (최소 4자 이상일 때만, 과매칭 방지)
    if len(q_norm) >= 4 and (q_norm in c_norm or c_norm in q_norm):
        return 95
    return fuzz.ratio(q_norm, c_norm)


def _find_matched_artworks(
    artist_slug: str, title: str | None, ho: int, medium_category: str
) -> list[MatchedArtwork]:
    """학습 데이터에서 동일/유사 작품 매칭.

    매칭 우선순위:
    1. 제목+작가+크기 정확 매칭
    2. 제목+작가 (크기 다름, 참고용)
    3. 작가+크기+매체 (제목 없을 때)
    4. 제목만 (작가 DB에 없을 때) — 전체 데이터 검색
    5. 유사 호수 (±1단계)
    """
    # 작가 매칭된 경우: 해당 작가 작품에서 검색
    items = _price_history.get(artist_slug, [])

    matched = []

    if title and items:
        # 1회 스캔으로 제목+크기 매칭과 제목만 매칭 동시 수집
        title_size_matches = []
        title_only_matches = []
        for item in items:
            score = _title_score(title, item["title"])
            if score >= 90 and item["ho"] == ho:
                title_size_matches.append(MatchedArtwork(
                    title=item["title"], price_krw=item["price_krw"],
                    price_usd=item["price_krw"] // 1380,
                    ho=item["ho"], medium=item["medium"],
                    gallery=item["gallery"], source=item.get("source", ""),
                    match_type="exact_title_size",
                ))
            elif score >= 80:
                title_only_matches.append(MatchedArtwork(
                    title=item["title"], price_krw=item["price_krw"],
                    price_usd=item["price_krw"] // 1380,
                    ho=item["ho"], medium=item["medium"],
                    gallery=item["gallery"], source=item.get("source", ""),
                    match_type="same_title_diff_size",
                ))
        matched = title_size_matches if title_size_matches else title_only_matches

    # 3. 제목만 있고 작가 매칭 안 된 경우 — 인덱스 기반 검색 (O(1))
    if title and not items and not matched:
        title_norm = _normalize_title(title)
        if title_norm in _title_index:
            for slug, idx in _title_index[title_norm][:10]:
                item = _price_history.get(slug, [None])[idx] if slug in _price_history and idx < len(_price_history[slug]) else None
                if item:
                    matched.append(MatchedArtwork(
                        title=item["title"], price_krw=item["price_krw"],
                        price_usd=item["price_krw"] // 1380,
                        ho=item["ho"], medium=item["medium"],
                        gallery=item["gallery"], source=item.get("source", ""),
                        match_type="title_only_global",
                    ))

    # 4. 동일 호수 + 동일 매체 (작가 매칭된 경우)
    if not matched and items:
        for item in items:
            if item["ho"] == ho and item["medium"] == medium_category:
                matched.append(MatchedArtwork(
                    title=item["title"], price_krw=item["price_krw"],
                    price_usd=item["price_krw"] // 1380,
                    ho=item["ho"], medium=item["medium"],
                    gallery=item["gallery"], source=item.get("source", ""),
                    match_type="same_size_medium",
                ))

    # 5. 유사 호수 (±1단계)
    if not matched and items:
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

    # 중복 제거 + 매칭 품질순 정렬, 최대 5건
    TYPE_ORDER = {"exact_title_size": 0, "same_title_diff_size": 1,
                  "title_only_global": 2, "same_size_medium": 3, "similar_size": 4}
    seen = set()
    unique = []
    for m in matched:
        key = (m.title, m.price_krw, m.ho)
        if key not in seen:
            seen.add(key)
            unique.append(m)
    unique.sort(key=lambda x: (TYPE_ORDER.get(x.match_type, 9), abs(x.ho - ho)))
    return unique[:5]


def _resolve_model_dir() -> Path:
    """MODEL_DIR 환경변수 → repo-relative fallback. 모든 곳에서 동일 resolver 사용
    (Codex 6차 P2 — model_info와 _load_models 경로 정합 보장)."""
    model_dir = Path(os.getenv("MODEL_DIR", "/app/models"))
    if not model_dir.exists():
        model_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / "model_test_results"
    return model_dir


def _load_models() -> None:
    """모델 파일 로드 — fail-closed (Codex 12차).

    PrimaryPredictor.load_models가 4개 artifact (cb/xgb/warm/label_maps)를
    한 번에 로드 + schema 검증. 누락 또는 invalid 시 RuntimeError.

    Codex 5차 P2: 같은 model_dir 스냅샷에서 model_info를 캐시 (런타임 disk 변경 무관).
    """
    model_dir = _resolve_model_dir()
    _predictor.load_models(model_dir)
    _build_model_info_cache(model_dir)


def _build_model_info_cache(model_dir: Path) -> None:
    """startup 시점의 metrics + calibration으로 model_info 응답 캐시.

    이후 disk가 바뀌어도 메모리 cache 사용 → version과 metrics가 같은 세대 보장.

    v3.6 PR7 (코덱스 P1 fix): predictor 의 variant prefix 와 정합. MODEL_VARIANT 적용
    시 metrics.json + calibration JSON + metrics dict 의 model_type key 모두 variant
    prefix 로 갱신. 이전 hardcoded 'integrated_v3_filtered_tuned_*' 는 deprecated.
    """
    global _model_info_cache
    # PR7: variant prefix 로 artifact path 결정 (predictor 와 정합)
    variant_prefix = SUPPORTED_VARIANTS[_predictor.variant]["prefix"]
    metrics_path = model_dir / f"{variant_prefix}_metrics.json"
    calib_path = model_dir / f"{variant_prefix}_source_calibration.json"
    if not metrics_path.exists():
        logger.warning("metrics file 없음 (%s) — model_info cache fallback", metrics_path)
        _model_info_cache = ModelInfoResponse(
            model_version=_predictor.model_version_label(_model_version),
            training_count=0, artist_count=0,
            mdape_groupkfold=0.0, mdape_kfold=0.0,
            features_count=len(_predictor.cb_features),
        )
        return
    with metrics_path.open(encoding="utf-8") as f:
        metrics = json.load(f)
    # PR7: metrics.json 안의 catboost / xgboost key 도 variant prefix
    cb_key = f"catboost_{_predictor.variant}"
    xgb_key = f"xgboost_{_predictor.variant}"
    cold_cb = metrics.get("groupkfold", {}).get(cb_key, {})
    warm_xgb = metrics.get("kfold", {}).get("warm_slice", {}).get(xgb_key, {})
    if not warm_xgb:
        warm_xgb = metrics.get("kfold", {}).get(xgb_key, {})
    cold_mdape = float(cold_cb.get("MdAPE", 0.0))
    warm_mdape = float(warm_xgb.get("MdAPE", 0.0))
    if calib_path.exists():
        with calib_path.open(encoding="utf-8") as f:
            cal = json.load(f)
        # Cold만 calibration 적용 — warm은 baseline 그대로 보고 (Codex 6차 P2)
        cold_cal = cal.get("cold_overall", {}).get("calibrated_mdape_cross_fit_guarded")
        if isinstance(cold_cal, (int, float)) and cold_cal > 0:
            cold_mdape = float(cold_cal)
        # warm은 predict()에서 calibration 적용 안 하므로 baseline metric 유지
    _model_info_cache = ModelInfoResponse(
        model_version=_predictor.model_version_label(_model_version),
        training_count=int(cold_cb.get("n", 0)),
        artist_count=int(metrics.get("artists", 0)),
        mdape_groupkfold=cold_mdape,
        mdape_kfold=warm_mdape,
        features_count=int(metrics.get("features", 0)),
    )
    logger.info("model_info cache built: version=%s, cold=%.2f, warm=%.2f, features=%d",
                _model_info_cache.model_version, cold_mdape, warm_mdape,
                _model_info_cache.features_count)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작/종료 시 리소스 관리."""
    global _start_time
    _start_time = time.time()

    _load_models()
    _load_artist_index()
    _load_price_history()
    _build_title_index()
    _init_log()

    # SHAP explainer 초기화 (CatBoost 모델)
    if _predictor.cb_model:
        shap_explainer.init_explainer(_predictor.cb_model)

    logger.info("=== VisionAI Price Prediction API Ready ===")
    yield
    logger.info("=== Shutting down ===")


from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="VisionAI 1차 시장 가격 예측 API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/demo", response_class=HTMLResponse)
async def demo():
    """가격 예측 데모 페이지."""
    demo_path = Path(__file__).resolve().parent / "demo.html"
    if not demo_path.exists():
        # 컨테이너 내 경로
        demo_path = Path("/app/demo.html")
    if demo_path.exists():
        return demo_path.read_text(encoding="utf-8")
    return HTMLResponse("<h1>Demo page not found</h1>", status_code=404)


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
        "model_version": _predictor.model_version_label(_model_version),
        "artists_loaded": _matcher.count,
        "uptime_seconds": round(time.time() - _start_time, 1),
        "db_status": db_status,
    }


@app.get("/api/v1/model/info", response_model=ModelInfoResponse)
async def model_info():
    """모델 정보 — startup cache 사용 (Codex 5차 P2: 런타임 disk 변경 무관).

    같은 model_dir 스냅샷의 metrics + calibration을 _load_models() 시점에 캐시.
    version과 metrics가 항상 같은 세대 보장. 재배포 시 컨테이너 재기동으로 갱신.
    """
    if _model_info_cache is None:
        # 발생할 일 없음 (lifespan에서 _load_models 호출됨) — defensive
        # v3.6 PR8 (코덱스 PR7 review P2 fix): defensive fallback 도 variant-aware.
        # CB_FEATURES (32) hardcode → predictor.cb_features 길이 (variant 별 32/35).
        return ModelInfoResponse(
            model_version=_predictor.model_version_label(_model_version),
            training_count=0, artist_count=0,
            mdape_groupkfold=0.0, mdape_kfold=0.0,
            features_count=len(_predictor.cb_features),
        )
    return _model_info_cache


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

    # 3.5 v3.6 PR8: V_year_saatchi_warm cohort gating + year resolution
    # Cohort authority (v3.5 step 2 §2.3): match.profile.source + warm_artist_slugs.
    # external_collector 로 채워진 profile.source 는 비권위 (is_matched=False 면 무시).
    artist_slug_for_routing = match.slug if match else None
    is_saatchi_warm = (
        is_matched
        and isinstance(profile, dict)
        and profile.get("source") == "saatchi"
        and bool(artist_slug_for_routing)
        and _predictor.is_warm_artist(artist_slug_for_routing)
    )

    # year_made resolution: manual (request) > cache.get > fetch (saatchi-only).
    # 비대상 cohort 면 year resolve skip → route='disabled' (v3.5 step 3 §3.2 schema).
    # PR8a (P0 fix): fetch 는 run_in_executor 로 분리 (event loop 차단 방지) +
    # rate-limit / cool-down gate (v3.5 step 3 §3.2.3).
    # PR8b (P1 fix): route 계약 — 'disabled' (비대상), 'manual' (no cache),
    # 'rate_limited' (gate suspend) 사용.
    year_made: int | None = None
    year_made_route: str = "disabled"
    if is_saatchi_warm:
        if req.year_made is not None:
            year_made = int(req.year_made)
            if req.artwork_id:
                # write-through: cache seed (route = manual_seed_cache_write 또는 parse_invalid)
                year_made_route = seed_artwork_year(
                    req.artwork_id, year_made, artwork_url=req.artwork_url
                )
            else:
                year_made_route = "manual"
        else:
            cache = get_global_cache()
            loop = asyncio.get_event_loop()
            year_made, year_made_route = await loop.run_in_executor(
                None,
                lambda: get_artwork_year(req.artwork_id, req.artwork_url, cache=cache),
            )

    # 4. 피처 생성
    features = build_features(
        width_cm=req.width_cm,
        height_cm=req.height_cm,
        medium=req.medium,
        artist_profile=profile,
        target_market=req.target_market,
        manual_overrides=manual,
        is_saatchi_warm=is_saatchi_warm,
        year_made=year_made,
    )

    # 5. 예측 — artist_slug 전달 (학습 시 warm artist set lookup용, Codex 5차 P1)
    result = _predictor.predict(
        features=features,
        is_matched=is_matched,
        training_count=training_count,
        target_market=req.target_market,
        has_manual_profile=has_manual,
        artist_slug=artist_slug_for_routing,
    )

    # SHAP 설명 (CatBoost 경로만, threadpool에서 실행)
    # v3.6 PR7: variant-aware model_type → 'catboost_*' prefix 로 분기
    feature_contributions = []
    if result["model_type"].startswith("catboost_"):
        cb_features_for_shap = _predictor.cb_features  # variant-aware

        def _compute_shap():
            df_explain = pd.DataFrame([features])
            for col in CAT_FEATURES:
                if col in df_explain.columns:
                    df_explain[col] = df_explain[col].astype(str).fillna("unknown")
            return shap_explainer.explain(df_explain[cb_features_for_shap], cb_features_for_shap)

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
        # v3.6 PR8: V_year_saatchi_warm cohort 관측 (PR10 full schema 전 minimal).
        "is_saatchi_warm": bool(is_saatchi_warm),
        "year_made_route": year_made_route,
        "year_made_used": year_made,
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
        ),
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
                artist_slug=match.slug if match else None,
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
