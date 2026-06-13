"""DB/cache-backed service skeleton for official price_prediction_v0.1."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from visionai.price_engine.api.official_v0_1_schemas import (
    CalculationStep,
    CalculationSummary,
    Confidence,
    CurrentModelResponse,
    FeedbackGuide,
    HealthResponse,
    InputQuality,
    MarketReference,
    MediumDistribution,
    ModelAuditResponse,
    Prediction,
    PredictionBasis,
    PredictionLookupResponse,
    PriceEstimateRequest,
    PriceEstimateResponse,
    PriceRange,
    RangePerHo,
    RepresentativeArtwork,
    ResolveArtistResponse,
    ResolvedArtist,
    Routing,
    SalePriceFeedbackRequest,
    SalePriceFeedbackResponse,
    SimilarArtistReference,
    SimilarArtwork,
    WarningItem,
)


SERVICE_VERSION = "price_prediction_v0.1"
SNAPSHOT_VERSION = "official_v0_1_initial_cache"
HO_AREA_CM2 = 220.5
WARM_MATCH_SCORE_MIN = 0.80
WARM_LITE_PRICE_COUNT_MIN = 1
WARM_FULL_PRICE_COUNT_MIN = 5
WARM_PRICE_COUNT_MIN = WARM_FULL_PRICE_COUNT_MIN
DEFAULT_DB_PATH = Path("data/track6/service_v0_1/price_prediction_v0_1.sqlite")
EXACT_ADAPTER_READINESS_JSON = (
    Path("docs")
    / "track6"
    / "experiments"
    / "price_prediction_official_v0_1_exact_adapter_readiness.json"
)
EXTERNAL_FEATURE_PROMOTION_JSON = (
    Path("docs")
    / "track6"
    / "experiments"
    / "price_prediction_official_v0_1_external_feature_promotion.json"
)
EXTERNAL_FEATURE_PROMOTION_IMPACT_JSON = (
    Path("docs")
    / "track6"
    / "experiments"
    / "price_prediction_official_v0_1_external_feature_promotion_impact.json"
)
ARTIST_IDENTITY_MIGRATION_AUDIT_JSON = (
    Path("docs")
    / "track6"
    / "experiments"
    / "price_prediction_official_v0_1_artist_identity_migration_audit.json"
)
ARTIST_IDENTITY_REVIEW_PRIORITY_JSON = (
    Path("docs")
    / "track6"
    / "experiments"
    / "price_prediction_official_v0_1_identity_external_review_priority.json"
)
ARTIST_IDENTITY_MERGE_DRY_RUN_JSON = (
    Path("docs")
    / "track6"
    / "experiments"
    / "price_prediction_official_v0_1_artist_identity_merge_dry_run.json"
)
ARTIST_IDENTITY_MERGE_SHADOW_JSON = (
    Path("docs")
    / "track6"
    / "experiments"
    / "price_prediction_official_v0_1_artist_identity_merge_shadow.json"
)
ARTIST_IDENTITY_POST_MERGE_CACHE_REBUILD_JSON = (
    Path("docs")
    / "track6"
    / "experiments"
    / "price_prediction_official_v0_1_artist_identity_post_merge_cache_rebuild.json"
)
ARTIST_IDENTITY_POST_MERGE_PREDICTION_IMPACT_JSON = (
    Path("docs")
    / "track6"
    / "experiments"
    / "price_prediction_official_v0_1_artist_identity_post_merge_prediction_impact.json"
)


def find_repo_root(start: Path) -> Path:
    for current in [start, *start.parents]:
        if (current / "src" / "visionai").exists() and (current / "data" / "track6").exists():
            return current
    raise RuntimeError(f"VisionAI repo root not found from {start}")


REPO = find_repo_root(Path(__file__).resolve())
WARM_PP258_FINAL_LAYER_PATH = (
    REPO
    / "experiments"
    / "track6"
    / "SUB-WARM-PP258_operational_fixed_test_submission"
    / "scripts"
    / "pp258_reproduce_fixed_test.py"
)
WARM_WMIN4_ARTIFACT_DIR = REPO / "models" / "track6" / "warm_wmin4_operational_candidate"
WARM_WMIN4_MANIFEST_PATH = WARM_WMIN4_ARTIFACT_DIR / "manifest.json"
WARM_WMIN8_ARTIFACT_DIR = REPO / "models" / "track6" / "warm_wmin8_operational_candidate"
WARM_WMIN8_MANIFEST_PATH = WARM_WMIN8_ARTIFACT_DIR / "manifest.json"
WARM_WMIN8_EXACT_RUNTIME_DIR = REPO / "models" / "track6" / "warm_wmin8_exact_runtime_candidate"
WARM_WMIN8_EXACT_RUNTIME_MANIFEST_PATH = WARM_WMIN8_EXACT_RUNTIME_DIR / "manifest.json"
WARM_LITE_ARTIFACT_DIR = REPO / "models" / "track6" / "warm_lite_v0.1"
WARM_LITE_POLICY_PATH = WARM_LITE_ARTIFACT_DIR / "config" / "warm_lite_policy_v0_1.json"
COLD_V03_POSTPROCESSOR_PATH = (
    REPO
    / "models"
    / "track6"
    / "cold_prediction_v0.3"
    / "predict"
    / "apply_cold_postprocess_v0_3.py"
)
COLD_V02_RAW_PREDICTOR_PATH = (
    REPO
    / "models"
    / "track6"
    / "cold_prediction_v0.2_operational"
    / "predict"
    / "predict_cold_operational_v0_2.py"
)
COLD_EXTERNAL_FEATURE_CACHE_PATH = (
    REPO / "data" / "track6" / "service_v0_1" / "official_v0_1_artist_external_feature_cache.csv"
)
COLD_FEATURE_STORE_PATH = (
    REPO / "data" / "track6" / "service_v0_1" / "official_v0_1_cold_feature_store.csv"
)
WARM_PP258_REQUIRED_UPSTREAM_COLUMNS = [
    "pp252_log",
    "pp252_stability_log",
    "prob_hist35_pp252",
    "resid_huber_pp252",
    "quantile_width",
    "l10_price_range_ratio",
    "component_prediction_spread",
    "confidence_tier",
    "svc_group_n",
]
COLD_V03_REQUIRED_UPSTREAM_COLUMNS = [
    "y18_qwidth_pred_log",
    "lgb_q40_pred_log",
    "quantile_width_log",
    "artist_key",
]


def now_kst_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def normalize_name(value: object) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[()\\[\\]{}.,'\"`~!@#$%^&*_+=:;|/?<>-]", "", text)
    return text


def stable_id(prefix: str, payload: object) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:20]
    return f"{prefix}_{digest}"


def safe_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return int(round(number))


def safe_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def format_krw(value: int | None) -> str | None:
    if value is None:
        return None
    if value >= 100_000_000:
        eok = value / 100_000_000
        return f"{eok:.1f}억원" if eok < 10 else f"{round(eok):,}억원"
    if value >= 10_000:
        return f"{round(value / 10_000):,}만원"
    return f"{value:,}원"


def format_range(low: int | None, high: int | None) -> str | None:
    if low is None or high is None:
        return None
    return f"{format_krw(low)} - {format_krw(high)}"


def area_cm2(width_cm: float | None, height_cm: float | None) -> float | None:
    if width_cm is None or height_cm is None:
        return None
    if width_cm <= 0 or height_cm <= 0:
        return None
    return float(width_cm) * float(height_cm)


def ho_size_from_area(area: float | None) -> int | None:
    if area is None or area <= 0:
        return None
    return max(1, int(round(area / HO_AREA_CM2)))


def size_bucket(area: float | None) -> str:
    if area is None or area <= 0:
        return "unknown"
    if area < 1200:
        return "small"
    if area < 3000:
        return "medium"
    if area < 7000:
        return "large"
    return "xlarge"


def clean_category(value: object) -> str | None:
    text = str(value or "").strip().lower()
    return text or None


@lru_cache(maxsize=8)
def module_exports_available(path: str, required_exports: tuple[str, ...]) -> bool:
    module_path = Path(path)
    if not module_path.exists():
        return False
    spec = importlib.util.spec_from_file_location(f"_visionai_adapter_{module_path.stem}", module_path)
    if spec is None or spec.loader is None:
        return False
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        return False
    return all(hasattr(module, name) for name in required_exports)


@dataclass(frozen=True)
class ArtistMatch:
    artist: ResolvedArtist | None
    candidates: list[ResolvedArtist]
    resolved: bool
    requires_selection: bool
    warnings: list[WarningItem]


@dataclass(frozen=True)
class StatChoice:
    row: sqlite3.Row | None
    scope: str | None
    source: str


class OfficialV01Service:
    """Official v0.1 service foundation backed by the generated SQLite DB."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = (db_path or (REPO / DEFAULT_DB_PATH)).resolve()
        if not self.db_path.exists():
            raise FileNotFoundError(f"official v0.1 DB not found: {self.db_path}")
        self._report_proxy_adapter: Any | None = None

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def health(self, request_id: str) -> HealthResponse:
        counts = self._table_counts()
        return HealthResponse(
            request_id=request_id,
            status="success",
            created_at=now_kst_iso(),
            service_version=SERVICE_VERSION,
            service_loaded=True,
            db_loaded=self.db_path.exists(),
            warm_adapter_loaded=self._report_proxy_adapter_available(),
            cold_adapter_loaded=self._report_proxy_adapter_available(),
            search_cache_loaded=counts.get("artist_search_feature_snapshots", 0) > 0,
            model_registry_loaded=counts.get("model_artifact_registry", 0) > 0,
            table_counts=counts,
        )

    def current_model(self, request_id: str) -> CurrentModelResponse:
        artifacts = self._active_artifacts()
        counts = self._table_counts()
        return CurrentModelResponse(
            request_id=request_id,
            status="success",
            created_at=now_kst_iso(),
            service_version=SERVICE_VERSION,
            model_status="candidate",
            routing_policy={
                "warm_artist_match_score_min": WARM_MATCH_SCORE_MIN,
                "warm_lite_same_artist_price_count_min": WARM_LITE_PRICE_COUNT_MIN,
                "warm_lite_same_artist_price_count_max": WARM_FULL_PRICE_COUNT_MIN - 1,
                "warm_same_artist_price_count_min": WARM_FULL_PRICE_COUNT_MIN,
                "ambiguous_artist_policy": "review_required",
                "cold_minimum_input_policy": "artist_name + width_cm + height_cm + medium + support",
            },
            display_policy={
                "warm": "이력 기반 예측",
                "warm_lite": "저이력 기반 예측",
                "cold": "참고 예측",
                "review_required": "확인 필요",
            },
            artifact_versions={
                "warm_display_name": artifacts.get("warm", {}).get("display_name"),
                "warm_internal_trace_id": artifacts.get("warm", {}).get("internal_trace_id"),
                "cold_display_name": artifacts.get("cold", {}).get("display_name"),
                "cold_internal_trace_id": artifacts.get("cold", {}).get("internal_trace_id"),
                "db_cache_snapshot": SNAPSHOT_VERSION,
                "warm_final_layer_module": str(WARM_PP258_FINAL_LAYER_PATH.relative_to(REPO)),
                **self._warm_target_artifact_versions(),
                "cold_final_layer_module": str(COLD_V03_POSTPROCESSOR_PATH.relative_to(REPO)),
            },
            adapter_status={
                "db_cache_foundation_ready": True,
                "warm_final_layer_module_loaded": self._warm_final_layer_available(),
                "warm_report_proxy_adapter_ready": self._report_proxy_adapter_available(),
                "warm_raw_upstream_adapter_ready": self._warm_wmin8_exact_runtime_ready(),
                "warm_report_model_adapter_ready": self._warm_wmin8_exact_runtime_ready(),
                "warm_required_upstream_columns": ", ".join(WARM_PP258_REQUIRED_UPSTREAM_COLUMNS),
                **self._warm_lite_status(),
                **self._warm_wmin4_status(),
                **self._warm_wmin8_status(),
                "cold_final_layer_module_loaded": self._cold_final_layer_available(),
                "cold_report_proxy_adapter_ready": self._report_proxy_adapter_available(),
                "cold_raw_upstream_adapter_ready": False,
                "cold_search_snapshot_feature_adapter_ready": counts.get("artist_search_feature_snapshots", 0) > 0,
                "cold_external_feature_cache_ready": COLD_EXTERNAL_FEATURE_CACHE_PATH.exists(),
                "cold_external_feature_cache_rows": self._line_count(COLD_EXTERNAL_FEATURE_CACHE_PATH),
                "cold_row_feature_store_ready": COLD_FEATURE_STORE_PATH.exists(),
                "cold_row_feature_store_rows": self._line_count(COLD_FEATURE_STORE_PATH),
                "cold_new_input_cache_feature_pipeline_ready": True,
                "cold_live_external_collection_pipeline_ready": False,
                "cold_feature_input_modes": (
                    "row_feature_store_replay, service_search_external_cache, "
                    "service_search_cache, service_external_cache, service_default_missing"
                ),
                **self._artist_identity_review_status(),
                **self._feature_review_queue_status(),
                "cold_report_model_adapter_ready": False,
                "cold_required_upstream_columns": ", ".join(COLD_V03_REQUIRED_UPSTREAM_COLUMNS),
                **self._readiness_adapter_status(),
                "note": "보고서 최종 계산층은 raw 호환 partial refreeze proxy adapter로 연결했습니다. Warm 방향/Huber와 Cold Quantile 일부는 저장 모델을 호출합니다. Cold fixed-test 행은 row-level feature store 기준 exact feature/prediction parity를 통과했습니다.",
            },
        )

    def resolve_artist(self, request_id: str, artist_input: Any, max_candidates: int = 5) -> ResolveArtistResponse:
        match = self._resolve_artist_internal(artist_input, max_candidates=max_candidates)
        status = "success" if match.resolved else "partial_success"
        return ResolveArtistResponse(
            request_id=request_id,
            status=status,
            created_at=now_kst_iso(),
            service_version=SERVICE_VERSION,
            resolved=match.resolved,
            requires_selection=match.requires_selection,
            selected_artist=match.artist if match.resolved else None,
            candidates=match.candidates,
            warnings=match.warnings,
        )

    def estimate_price(self, request_id: str, request: PriceEstimateRequest) -> PriceEstimateResponse:
        input_quality = self._input_quality(request)
        warnings: list[WarningItem] = []
        if input_quality.minimum_input_status == "failed":
            warnings.append(WarningItem(
                code="MINIMUM_INPUT_FAILED",
                severity="warning",
                message="최소 입력값이 부족해 단일 가격 예측을 보류했습니다.",
            ))

        match = self._resolve_artist_internal(request.artwork.artist, max_candidates=5)
        warnings.extend(match.warnings)
        if match.requires_selection and not match.resolved:
            warnings.append(WarningItem(
                code="ARTIST_REVIEW_REQUIRED",
                severity="warning",
                message="동명이인 또는 유사 후보가 있어 작가 선택 후 예측하는 것이 안전합니다.",
            ))

        route = self._route(match)
        if input_quality.minimum_input_status == "failed":
            route = "review_required"

        target_area = area_cm2(request.artwork.dimensions.width_cm, request.artwork.dimensions.height_cm)
        ho_size = ho_size_from_area(target_area)
        medium = clean_category(request.artwork.medium.medium_category)
        support = clean_category(request.artwork.medium.support_category)
        artist_key = match.artist.artist_key if match.artist else None
        stats = self._choose_stats(route, artist_key, medium, support, size_bucket(target_area))
        price, low, high = self._price_from_stats(route, stats, ho_size, match.artist)
        adapter_result = self._try_report_proxy_adapter(route, request, artist_key)
        if adapter_result and adapter_result.price_krw:
            price = adapter_result.price_krw
            low = adapter_result.low_krw
            high = adapter_result.high_krw
        confidence = self._confidence(route, match.artist, stats, input_quality)
        prediction_id = self._prediction_id(request, route, artist_key, stats.scope)
        display_route = self._display_route(route)
        calculation_steps = self._calculation_steps(
            route,
            request,
            stats,
            price,
            low,
            high,
            ho_size,
            match.artist,
            adapter_result,
        )

        if route != "review_required":
            adapter_status = self._route_adapter_status(route, adapter_result)
            warnings.append(WarningItem(
                code=adapter_status["warning_code"],
                severity="info",
                message=adapter_status["warning_message"],
            ))

        response = PriceEstimateResponse(
            request_id=request_id,
            status="partial_success" if warnings else "success",
            created_at=now_kst_iso(),
            service_version=SERVICE_VERSION,
            prediction_id=prediction_id,
            route=route,
            display_route=display_route,
            display_policy=self._display_policy(route),
            prediction=Prediction(
                price_krw=price,
                price_display=format_krw(price),
                range_krw=PriceRange(low=low, mid=price, high=high),
                range_display=format_range(low, high),
                confidence=confidence,
            ),
            routing=Routing(
                artist_matched=match.artist is not None,
                matched_artist_key=artist_key,
                artist_match_score=match.artist.artist_match_score if match.artist else None,
                homonym_risk_score=match.artist.homonym_risk_score if match.artist else None,
                same_artist_training_price_count=match.artist.same_artist_training_price_count if match.artist else None,
                route_policy=(
                    f"artist_match_score >= {WARM_MATCH_SCORE_MIN} AND "
                    f"same_artist_training_price_count 1~{WARM_FULL_PRICE_COUNT_MIN - 1} => warm_lite, "
                    f">= {WARM_FULL_PRICE_COUNT_MIN} => warm"
                ),
                route_reason=self._route_reason(route, match.artist),
            ),
            basis=PredictionBasis(
                similar_group_level=stats.scope,
                similar_sample_count=safe_int(stats.row["sample_count"]) if stats.row else None,
                similar_coverage_tier=stats.row["coverage_tier"] if stats.row else None,
                similar_price_median_krw=safe_int(stats.row["median_price_krw"]) if stats.row else None,
                similar_price_q25_krw=safe_int(stats.row["q25_price_krw"]) if stats.row else None,
                similar_price_q75_krw=safe_int(stats.row["q75_price_krw"]) if stats.row else None,
                median_krw_per_ho=safe_int(stats.row["median_krw_per_ho"]) if stats.row else None,
            ),
            market_reference=self._market_reference(stats, ho_size, price),
            similar_artworks=self._similar_artworks(
                route,
                artist_key,
                medium,
                support,
                target_area,
                request.options.max_comparable_samples if request.options.include_comparable_samples else 0,
            ),
            similar_artists=self._similar_artists(artist_key),
            input_quality=input_quality,
            calculation_summary=CalculationSummary(
                route=route,
                display_route=display_route,
                user_facing_formula=self._user_formula(route),
                explanation=self._calculation_explanation(route),
                adapter_execution_level=(adapter_result.execution_level if adapter_result else "db_cache_foundation"),
                steps=calculation_steps if request.options.include_calculation_steps else [],
            ),
            feedback=FeedbackGuide(
                can_submit_actual_sale_price=route != "review_required",
                feedback_endpoint="/api/v1/feedback/sale-price",
                required_fields=["prediction_id", "actual_sale_price_krw"],
                note="실제 판매가는 검수 전 학습에 반영하지 않고 학습 후보로만 저장됩니다.",
            ),
            warnings=warnings,
        )
        self._store_prediction(response, request, calculation_steps)
        return response

    def lookup_prediction(self, request_id: str, prediction_id: str) -> PredictionLookupResponse:
        with self._connect() as conn:
            event = conn.execute(
                "SELECT * FROM prediction_events WHERE prediction_id = ?",
                (prediction_id,),
            ).fetchone()
            steps = conn.execute(
                """
                SELECT step_order, step_name, step_role, formula_text, input_json, output_json, display_flag, created_at
                FROM prediction_calculation_steps
                WHERE prediction_id = ?
                ORDER BY step_order
                """,
                (prediction_id,),
            ).fetchall()
        return PredictionLookupResponse(
            request_id=request_id,
            status="success" if event else "partial_success",
            created_at=now_kst_iso(),
            service_version=SERVICE_VERSION,
            prediction_id=prediction_id,
            prediction_event=self._row_to_json(event) if event else None,
            calculation_steps=[self._row_to_json(row) for row in steps],
        )

    def record_sale_price_feedback(
        self,
        request_id: str,
        payload: SalePriceFeedbackRequest,
    ) -> SalePriceFeedbackResponse:
        feedback_id = stable_id("feedback", payload.model_dump())
        with self._connect() as conn:
            event = conn.execute(
                "SELECT prediction_id, route, artist_key FROM prediction_events WHERE prediction_id = ?",
                (payload.prediction_id,),
            ).fetchone()
            if not event:
                return SalePriceFeedbackResponse(
                    request_id=request_id,
                    status="partial_success",
                    created_at=now_kst_iso(),
                    service_version=SERVICE_VERSION,
                    accepted=False,
                    review_status="rejected",
                    message="prediction_id를 찾을 수 없어 피드백을 저장하지 않았습니다.",
                )
            conn.execute(
                """
                INSERT OR REPLACE INTO sale_price_feedback (
                  feedback_id, prediction_id, actual_sale_price_krw, sale_date,
                  sale_channel, evidence_status, consent_for_training,
                  review_status, review_note, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    feedback_id,
                    payload.prediction_id,
                    payload.actual_sale_price_krw,
                    payload.sale_date,
                    payload.sale_channel,
                    payload.evidence_status,
                    1 if payload.consent_for_training else 0,
                    "needs_review",
                    payload.note,
                    now_kst_iso(),
                ),
            )
            conn.commit()
        return SalePriceFeedbackResponse(
            request_id=request_id,
            status="success",
            created_at=now_kst_iso(),
            service_version=SERVICE_VERSION,
            accepted=True,
            review_status="needs_review",
            message="실제 판매가 피드백을 저장했습니다. 검수 승인 후 학습 후보로 승격할 수 있습니다.",
        )

    def model_audit(self, request_id: str) -> ModelAuditResponse:
        counts = self._table_counts()
        return ModelAuditResponse(
            request_id=request_id,
            status="success",
            created_at=now_kst_iso(),
            service_version=SERVICE_VERSION,
            checks={
                "artist_registry_rows": counts.get("artist_registry", 0),
                "price_observation_rows": counts.get("artwork_price_observations", 0),
                "search_snapshot_rows": counts.get("artist_search_feature_snapshots", 0),
                "similar_stats_rows": counts.get("similar_artwork_stats_cache", 0),
                "similar_artist_rows": counts.get("similar_artist_cache", 0),
                "model_registry_rows": counts.get("model_artifact_registry", 0),
                "db_cache_foundation_ready": True,
                "warm_final_layer_module_loaded": self._warm_final_layer_available(),
                "warm_report_proxy_adapter_ready": self._report_proxy_adapter_available(),
                "warm_raw_upstream_adapter_ready": self._warm_wmin8_exact_runtime_ready(),
                "warm_report_model_adapter_ready": self._warm_wmin8_exact_runtime_ready(),
                "warm_required_upstream_columns": ", ".join(WARM_PP258_REQUIRED_UPSTREAM_COLUMNS),
                **self._warm_lite_status(),
                **self._warm_wmin4_status(),
                **self._warm_wmin8_status(),
                "cold_final_layer_module_loaded": self._cold_final_layer_available(),
                "cold_report_proxy_adapter_ready": self._report_proxy_adapter_available(),
                "cold_raw_upstream_adapter_ready": False,
                "cold_search_snapshot_feature_adapter_ready": counts.get("artist_search_feature_snapshots", 0) > 0,
                "cold_external_feature_cache_ready": COLD_EXTERNAL_FEATURE_CACHE_PATH.exists(),
                "cold_external_feature_cache_rows": self._line_count(COLD_EXTERNAL_FEATURE_CACHE_PATH),
                "cold_row_feature_store_ready": COLD_FEATURE_STORE_PATH.exists(),
                "cold_row_feature_store_rows": self._line_count(COLD_FEATURE_STORE_PATH),
                "cold_new_input_cache_feature_pipeline_ready": True,
                "cold_live_external_collection_pipeline_ready": False,
                "cold_feature_input_modes": (
                    "row_feature_store_replay, service_search_external_cache, "
                    "service_search_cache, service_external_cache, service_default_missing"
                ),
                **self._artist_identity_review_status(),
                **self._feature_review_queue_status(),
                "cold_report_model_adapter_ready": False,
                "cold_required_upstream_columns": ", ".join(COLD_V03_REQUIRED_UPSTREAM_COLUMNS),
                **self._readiness_audit_checks(),
                "fixed_test_parity_checked": False,
                "deterministic_repeat_checked": False,
                "db_path": str(self.db_path),
            },
        )

    def _table_counts(self) -> dict[str, int]:
        tables = [
            "artist_registry",
            "artist_aliases",
            "artwork_price_observations",
            "artist_search_feature_snapshots",
            "artist_search_results",
            "similar_artwork_stats_cache",
            "similar_artist_cache",
            "model_artifact_registry",
            "prediction_events",
            "prediction_calculation_steps",
            "sale_price_feedback",
            "training_candidates",
            "external_feature_review_queue",
            "external_feature_review_decisions",
            "artist_identity_review_queue",
            "artist_identity_review_decisions",
        ]
        counts: dict[str, int] = {}
        with self._connect() as conn:
            for table in tables:
                exists = conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                    (table,),
                ).fetchone()
                counts[table] = int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]) if exists else 0
        return counts

    @staticmethod
    def _line_count(path: Path) -> str:
        if not path.exists():
            return "0"
        with path.open("r", encoding="utf-8") as fh:
            return str(max(sum(1 for _ in fh) - 1, 0))

    def _artist_identity_review_status(self) -> dict[str, bool | str]:
        path = REPO / ARTIST_IDENTITY_MIGRATION_AUDIT_JSON
        payload: dict[str, Any] = {}
        if path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                payload = {}
        priority_path = REPO / ARTIST_IDENTITY_REVIEW_PRIORITY_JSON
        priority_payload: dict[str, Any] = {}
        if priority_path.exists():
            try:
                priority_payload = json.loads(priority_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                priority_payload = {}
        merge_path = REPO / ARTIST_IDENTITY_MERGE_DRY_RUN_JSON
        merge_payload: dict[str, Any] = {}
        if merge_path.exists():
            try:
                merge_payload = json.loads(merge_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                merge_payload = {}
        shadow_path = REPO / ARTIST_IDENTITY_MERGE_SHADOW_JSON
        shadow_payload: dict[str, Any] = {}
        if shadow_path.exists():
            try:
                shadow_payload = json.loads(shadow_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                shadow_payload = {}
        rebuild_path = REPO / ARTIST_IDENTITY_POST_MERGE_CACHE_REBUILD_JSON
        rebuild_payload: dict[str, Any] = {}
        if rebuild_path.exists():
            try:
                rebuild_payload = json.loads(rebuild_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                rebuild_payload = {}
        prediction_impact_path = REPO / ARTIST_IDENTITY_POST_MERGE_PREDICTION_IMPACT_JSON
        prediction_impact_payload: dict[str, Any] = {}
        if prediction_impact_path.exists():
            try:
                prediction_impact_payload = json.loads(prediction_impact_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                prediction_impact_payload = {}
        with self._connect() as conn:
            exists = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'artist_identity_review_queue'"
            ).fetchone()
            if not exists:
                return {
                    "artist_identity_review_queue_ready": False,
                    "artist_identity_review_queue_rows": "0",
                    "artist_identity_merge_review_rows": "0",
                    "artist_identity_human_review_rows": "0",
                    "artist_identity_audit_loaded": bool(payload),
                    "artist_identity_review_priority_loaded": bool(priority_payload),
                    "artist_identity_merge_dry_run_loaded": bool(merge_payload),
                    "artist_identity_merge_shadow_loaded": bool(shadow_payload),
                    "artist_identity_post_merge_cache_rebuild_loaded": bool(rebuild_payload),
                    "artist_identity_post_merge_prediction_impact_loaded": bool(prediction_impact_payload),
                }
            rows = conn.execute("SELECT COUNT(*) FROM artist_identity_review_queue").fetchone()[0]
            status_rows = conn.execute(
                """
                SELECT review_status, COUNT(*) AS n
                FROM artist_identity_review_queue
                GROUP BY review_status
                """
            ).fetchall()
        counts = {str(row[0]): int(row[1]) for row in status_rows}
        return {
            "artist_identity_review_queue_ready": rows > 0,
            "artist_identity_review_queue_rows": str(rows),
            "artist_identity_merge_review_rows": str(counts.get("needs_merge_review", 0)),
            "artist_identity_human_review_rows": str(counts.get("needs_human_review", 0)),
            "artist_identity_audit_loaded": bool(payload),
            "artist_identity_conflict_groups": str(payload.get("total_conflict_groups", rows if rows else 0)),
            "artist_identity_likely_false_split_groups": str(payload.get("likely_false_split_count", 0)),
            "artist_identity_possible_false_split_groups": str(payload.get("possible_false_split_count", 0)),
            "artist_identity_keep_separate_groups": str(payload.get("keep_separate_count", 0)),
            "artist_identity_total_split_loss_price_count": str(payload.get("total_split_loss_price_count", 0)),
            "artist_identity_likely_false_split_loss_price_count": str(payload.get("likely_false_split_loss_price_count", 0)),
            "artist_identity_auto_merge_applied": False,
            "artist_identity_audit_path": str(ARTIST_IDENTITY_MIGRATION_AUDIT_JSON),
            "artist_identity_review_priority_loaded": bool(priority_payload),
            "artist_identity_review_priority_rows": str(priority_payload.get("priority_rows", 0)),
            "artist_identity_review_priority_p0_rows": str(priority_payload.get("p0_rows", 0)),
            "artist_identity_review_priority_p1_rows": str(priority_payload.get("p1_rows", 0)),
            "artist_identity_review_priority_p2_rows": str(priority_payload.get("p2_rows", 0)),
            "artist_identity_review_priority_path": str(ARTIST_IDENTITY_REVIEW_PRIORITY_JSON),
            "artist_identity_merge_dry_run_loaded": bool(merge_payload),
            "artist_identity_merge_dry_run_component_rows": str(merge_payload.get("merge_component_rows", 0)),
            "artist_identity_merge_dry_run_source_keys": str(merge_payload.get("source_artist_keys_to_merge", 0)),
            "artist_identity_merge_dry_run_reassigned_price_count": str(merge_payload.get("reassigned_valid_price_count", 0)),
            "artist_identity_merge_dry_run_projected_registry_rows": str(merge_payload.get("projected_artist_registry_rows_after_merge", 0)),
            "artist_identity_merge_dry_run_applied": False,
            "artist_identity_merge_dry_run_path": str(ARTIST_IDENTITY_MERGE_DRY_RUN_JSON),
            "artist_identity_merge_shadow_loaded": bool(shadow_payload),
            "artist_identity_merge_shadow_groups": str(shadow_payload.get("evaluated_merge_groups", 0)),
            "artist_identity_merge_shadow_single_candidate_groups": str(shadow_payload.get("resolved_to_single_candidate_groups", 0)),
            "artist_identity_merge_shadow_reassigned_price_count": str(shadow_payload.get("total_valid_price_count_gain_vs_previous_max", 0)),
            "artist_identity_merge_shadow_db": str(shadow_payload.get("shadow_db", "")),
            "artist_identity_merge_shadow_operational_db_modified": False,
            "artist_identity_merge_shadow_path": str(ARTIST_IDENTITY_MERGE_SHADOW_JSON),
            "artist_identity_post_merge_cache_rebuild_loaded": bool(rebuild_payload),
            "artist_identity_post_merge_cache_rebuild_operational_db_modified": bool(rebuild_payload.get("operational_db_modified", False)),
            "artist_identity_post_merge_cache_rebuild_alias_after_rows": str(rebuild_payload.get("alias_dedup", {}).get("after", 0)),
            "artist_identity_post_merge_cache_rebuild_registry_after_rows": str(rebuild_payload.get("count_diff", {}).get("artist_registry", {}).get("after", 0)),
            "artist_identity_post_merge_cache_rebuild_similar_stats_after_rows": str(rebuild_payload.get("similar_cache_rebuild", {}).get("similar_artwork_stats_after", 0)),
            "artist_identity_post_merge_cache_rebuild_similar_artist_after_rows": str(rebuild_payload.get("similar_cache_rebuild", {}).get("similar_artist_after", 0)),
            "artist_identity_post_merge_cache_rebuild_external_artist_rows": str(rebuild_payload.get("external_artist_count", 0)),
            "artist_identity_post_merge_cache_rebuild_shadow_db": str(rebuild_payload.get("rebuilt_shadow_db", "")),
            "artist_identity_post_merge_cache_rebuild_path": str(ARTIST_IDENTITY_POST_MERGE_CACHE_REBUILD_JSON),
            "artist_identity_post_merge_prediction_impact_loaded": bool(prediction_impact_payload),
            "artist_identity_post_merge_prediction_impact_components": str(prediction_impact_payload.get("evaluated_components", 0)),
            "artist_identity_post_merge_prediction_impact_alias_resolved_after": str(prediction_impact_payload.get("alias_resolved_after_merge", 0)),
            "artist_identity_post_merge_prediction_impact_review_required_before": str(prediction_impact_payload.get("alias_review_required_before", 0)),
            "artist_identity_post_merge_prediction_impact_review_required_after": str(prediction_impact_payload.get("alias_review_required_after", 0)),
            "artist_identity_post_merge_prediction_impact_direct_price_changed_rows": str(prediction_impact_payload.get("direct_price_changed_rows", 0)),
            "artist_identity_post_merge_prediction_impact_high_impact_rows": str(prediction_impact_payload.get("direct_high_impact_rows_abs_delta_gte_50pct", 0)),
            "artist_identity_post_merge_prediction_impact_operational_db_modified": bool(prediction_impact_payload.get("operational_db_modified", False)),
            "artist_identity_post_merge_prediction_impact_path": str(ARTIST_IDENTITY_POST_MERGE_PREDICTION_IMPACT_JSON),
        }

    def _feature_review_queue_status(self) -> dict[str, bool | str]:
        with self._connect() as conn:
            exists = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'external_feature_review_queue'"
            ).fetchone()
            if not exists:
                return {
                    "cold_live_feature_review_queue_ready": False,
                    "cold_live_feature_review_queue_rows": "0",
                    "cold_live_feature_promotion_requires_review": True,
                    **self._external_feature_promotion_status(),
                }
            rows = conn.execute("SELECT COUNT(*) FROM external_feature_review_queue").fetchone()[0]
            status_rows = conn.execute(
                """
                SELECT review_status, COUNT(*) AS n
                FROM external_feature_review_queue
                GROUP BY review_status
                """
            ).fetchall()
        counts = {str(row[0]): int(row[1]) for row in status_rows}
        pending = counts.get("needs_human_review", 0) + counts.get("needs_improvement", 0) + counts.get("needs_review", 0)
        return {
            "cold_live_feature_review_queue_ready": rows > 0,
            "cold_live_feature_review_queue_rows": str(rows),
            "cold_live_feature_review_pending_rows": str(pending),
            "cold_live_feature_review_needs_human_rows": str(counts.get("needs_human_review", 0)),
            "cold_live_feature_review_needs_improvement_rows": str(counts.get("needs_improvement", 0)),
            "cold_live_feature_review_auto_reject_duplicate_rows": str(counts.get("auto_reject_duplicate", 0)),
            "cold_live_feature_promotion_requires_review": True,
            **self._external_feature_promotion_status(),
        }

    def _external_feature_promotion_status(self) -> dict[str, bool | str]:
        path = REPO / EXTERNAL_FEATURE_PROMOTION_JSON
        if not path.exists():
            return {
                "cold_external_feature_promotion_dry_run_ready": False,
                "cold_external_feature_promotion_applied": False,
            }
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {
                "cold_external_feature_promotion_dry_run_ready": False,
                "cold_external_feature_promotion_applied": False,
            }
        return {
            "cold_external_feature_promotion_dry_run_ready": True,
            "cold_external_feature_promotion_gate_pass": bool(payload.get("gate_pass")),
            "cold_external_feature_promotion_applied": bool(payload.get("applied")),
            "cold_external_feature_promoted_candidate_rows": str(payload.get("promoted_cache_rows", 0)),
            "cold_external_feature_promotion_blocked_rows": str(payload.get("blocked_candidate_rows", 0)),
            **self._external_feature_promotion_impact_status(),
        }

    def _external_feature_promotion_impact_status(self) -> dict[str, bool | str]:
        path = REPO / EXTERNAL_FEATURE_PROMOTION_IMPACT_JSON
        if not path.exists():
            return {
                "cold_external_feature_promotion_impact_audit_ready": False,
            }
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {
                "cold_external_feature_promotion_impact_audit_ready": False,
            }
        return {
            "cold_external_feature_promotion_impact_audit_ready": True,
            "cold_external_feature_promotion_impact_mode": str(payload.get("mode") or ""),
            "cold_external_feature_promotion_impact_rows": str(payload.get("evaluated_rows", 0)),
            "cold_external_feature_promotion_changed_rows": str(payload.get("changed_prediction_rows", 0)),
            "cold_external_feature_promotion_coverage_loss_rows": str(payload.get("external_feature_loss_rows", 0)),
            "cold_external_feature_promotion_p95_abs_delta_pct": str(payload.get("p95_abs_price_delta_pct", 0.0)),
        }

    def _active_artifacts(self) -> dict[str, dict[str, str | None]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT route, display_name, internal_trace_id, artifact_path, feature_schema_version
                FROM model_artifact_registry
                WHERE service_version = ? AND active_flag = 1
                """,
                (SERVICE_VERSION,),
            ).fetchall()
        return {row["route"]: dict(row) for row in rows}

    @staticmethod
    def _warm_wmin4_manifest() -> dict[str, Any]:
        if not WARM_WMIN4_MANIFEST_PATH.exists():
            return {}
        try:
            return json.loads(WARM_WMIN4_MANIFEST_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _fmt_metric(value: object) -> str:
        number = safe_float(value)
        return "" if number is None else f"{number:.6f}"

    def _warm_wmin4_artifact_versions(self) -> dict[str, str | None]:
        payload = self._warm_wmin4_manifest()
        if not payload:
            return {
                "warm_selected_target_display_name": None,
                "warm_selected_target_internal_trace_id": None,
                "warm_selected_target_artifact_path": None,
                "warm_selected_target_candidate_label": None,
            }
        return {
            "warm_selected_target_display_name": str(payload.get("display_name") or ""),
            "warm_selected_target_internal_trace_id": str(payload.get("internal_trace_id") or ""),
            "warm_selected_target_artifact_path": str(WARM_WMIN4_ARTIFACT_DIR.relative_to(REPO)),
            "warm_selected_target_candidate_label": str(payload.get("selected_candidate_label") or ""),
        }

    @staticmethod
    def _warm_wmin8_manifest() -> dict[str, Any]:
        if not WARM_WMIN8_MANIFEST_PATH.exists():
            return {}
        try:
            return json.loads(WARM_WMIN8_MANIFEST_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _warm_wmin8_exact_runtime_manifest() -> dict[str, Any]:
        if not WARM_WMIN8_EXACT_RUNTIME_MANIFEST_PATH.exists():
            return {}
        try:
            return json.loads(WARM_WMIN8_EXACT_RUNTIME_MANIFEST_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _warm_wmin8_exact_runtime_ready(self) -> bool:
        payload = self._warm_wmin8_exact_runtime_manifest()
        parity = payload.get("huber_pipeline_parity", {}) if payload else {}
        files = payload.get("files", {}) if payload else {}
        required = [
            files.get("shrinkage_runtime"),
            files.get("shrunk_huber_refit_model"),
            files.get("huber_runtime"),
            files.get("base_huber_refit_pipeline"),
            files.get("alternative_huber_refit_pipeline"),
        ]
        return bool(
            payload
            and parity.get("passes_prediction_csv_replay") is True
            and all(item and (WARM_WMIN8_EXACT_RUNTIME_DIR / str(item)).exists() for item in required)
        )

    def _warm_target_artifact_versions(self) -> dict[str, str | None]:
        payload = self._warm_wmin8_manifest() or self._warm_wmin4_manifest()
        artifact_dir = WARM_WMIN8_ARTIFACT_DIR if self._warm_wmin8_manifest() else WARM_WMIN4_ARTIFACT_DIR
        if not payload:
            return {
                "warm_selected_target_display_name": None,
                "warm_selected_target_internal_trace_id": None,
                "warm_selected_target_artifact_path": None,
                "warm_selected_target_candidate_label": None,
            }
        return {
            "warm_selected_target_display_name": str(payload.get("display_name") or ""),
            "warm_selected_target_internal_trace_id": str(payload.get("internal_trace_id") or ""),
            "warm_selected_target_artifact_path": str(artifact_dir.relative_to(REPO)),
            "warm_selected_target_candidate_label": str(payload.get("selected_candidate_label") or ""),
        }

    def _warm_lite_status(self) -> dict[str, bool | str]:
        if not WARM_LITE_POLICY_PATH.exists():
            return {
                "warm_lite_candidate_artifact_ready": False,
                "warm_lite_raw_adapter_ready": False,
            }
        try:
            policy = json.loads(WARM_LITE_POLICY_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            policy = {}
        return {
            "warm_lite_candidate_artifact_ready": True,
            "warm_lite_raw_adapter_ready": True,
            "warm_lite_artifact_path": str(WARM_LITE_ARTIFACT_DIR.relative_to(REPO)),
            "warm_lite_policy_version": str(policy.get("version") or "v0.1"),
            "warm_lite_route_rule": "artist_match_score >= 0.80 AND same_artist_training_price_count 1~4",
            "warm_lite_fixed_model_status": str(policy.get("status") or ""),
        }

    def _warm_wmin8_status(self) -> dict[str, bool | str]:
        payload = self._warm_wmin8_manifest()
        if not payload:
            return {
                "warm_wmin8_candidate_artifact_ready": False,
                "warm_wmin8_exact_raw_adapter_ready": False,
            }
        exact_payload = self._warm_wmin8_exact_runtime_manifest()
        exact_ready = self._warm_wmin8_exact_runtime_ready()
        readiness = payload.get("readiness", {})
        api_parity = payload.get("api_fixed_test_parity", {})
        api_parity_ready = bool(readiness.get("api_fixed_test_parity_ready") or api_parity.get("parity_pass"))
        fixed = payload.get("metrics", {}).get("fixed_test", {})
        validation = payload.get("metrics", {}).get("validation_oof", {})
        return {
            "warm_wmin8_candidate_artifact_ready": True,
            "warm_wmin8_selected_candidate_label": str(payload.get("selected_candidate_label") or ""),
            "warm_wmin8_artifact_path": str(WARM_WMIN8_ARTIFACT_DIR.relative_to(REPO)),
            "warm_wmin8_fixed_test_MAPE": self._fmt_metric(fixed.get("MAPE")),
            "warm_wmin8_fixed_test_MdAPE": self._fmt_metric(fixed.get("MdAPE")),
            "warm_wmin8_fixed_test_p95_APE": self._fmt_metric(fixed.get("p95_APE")),
            "warm_wmin8_fixed_test_RMSE_log": self._fmt_metric(fixed.get("RMSE_log")),
            "warm_wmin8_validation_MAPE": self._fmt_metric(validation.get("MAPE")),
            "warm_wmin8_validation_p95_APE": self._fmt_metric(validation.get("p95_APE")),
            "warm_wmin8_proxy_adapter_ready": bool(readiness.get("proxy_adapter_ready")),
            "warm_wmin8_exact_runtime_artifact_ready": bool(exact_payload),
            "warm_wmin8_exact_runtime_path": (
                str(WARM_WMIN8_EXACT_RUNTIME_DIR.relative_to(REPO)) if exact_payload else ""
            ),
            "warm_wmin8_exact_pipeline_replay_pass": bool(
                (exact_payload.get("huber_pipeline_parity", {}) if exact_payload else {}).get("passes_prediction_csv_replay")
            ),
            "warm_wmin8_exact_raw_adapter_ready": exact_ready,
            "warm_wmin8_api_fixed_test_parity_ready": api_parity_ready,
            "warm_wmin8_api_fixed_test_parity_n": str(api_parity.get("n_success") or ""),
            "warm_wmin8_api_fixed_test_max_abs_log_diff": self._fmt_metric(api_parity.get("max_abs_log_diff")),
            "warm_wmin8_adapter_state": (
                "exact_raw_adapter_api_parity_passed"
                if exact_ready and api_parity_ready
                else "exact_raw_adapter_candidate_connected"
                if exact_ready
                else "target_artifact_ready_but_exact_raw_adapter_pending"
                if not readiness.get("exact_raw_adapter_ready")
                else "exact_raw_adapter_ready"
            ),
            "warm_wmin8_raw_adapter_blocker": (
                ""
                if exact_ready and api_parity_ready
                else "run fixed-test parity through the official API endpoint"
                if exact_ready
                else "; ".join(str(item) for item in readiness.get("blocking_items", []))
            ),
        }

    def _warm_wmin4_status(self) -> dict[str, bool | str]:
        payload = self._warm_wmin4_manifest()
        if not payload:
            return {
                "warm_wmin4_candidate_artifact_ready": False,
                "warm_wmin4_exact_raw_adapter_ready": False,
            }
        readiness = payload.get("readiness", {})
        fixed = payload.get("metrics", {}).get("fixed_test", {})
        validation = payload.get("metrics", {}).get("validation_oof", {})
        return {
            "warm_wmin4_candidate_artifact_ready": True,
            "warm_wmin4_selected_candidate_label": str(payload.get("selected_candidate_label") or ""),
            "warm_wmin4_artifact_path": str(WARM_WMIN4_ARTIFACT_DIR.relative_to(REPO)),
            "warm_wmin4_fixed_test_MAPE": self._fmt_metric(fixed.get("MAPE")),
            "warm_wmin4_fixed_test_MdAPE": self._fmt_metric(fixed.get("MdAPE")),
            "warm_wmin4_fixed_test_p95_APE": self._fmt_metric(fixed.get("p95_APE")),
            "warm_wmin4_fixed_test_RMSE_log": self._fmt_metric(fixed.get("RMSE_log")),
            "warm_wmin4_validation_MAPE": self._fmt_metric(validation.get("MAPE")),
            "warm_wmin4_validation_p95_APE": self._fmt_metric(validation.get("p95_APE")),
            "warm_wmin4_proxy_adapter_ready": bool(readiness.get("proxy_adapter_ready")),
            "warm_wmin4_exact_raw_adapter_ready": bool(readiness.get("exact_raw_adapter_ready")),
            "warm_wmin4_adapter_state": (
                "target_artifact_ready_but_exact_raw_adapter_pending"
                if not readiness.get("exact_raw_adapter_ready")
                else "exact_raw_adapter_ready"
            ),
            "warm_wmin4_raw_adapter_blocker": "; ".join(str(item) for item in readiness.get("blocking_items", [])),
        }

    @staticmethod
    def _readiness_payload() -> dict[str, Any]:
        path = REPO / EXACT_ADAPTER_READINESS_JSON
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _readiness_adapter_status(self) -> dict[str, bool | str]:
        payload = self._readiness_payload()
        if not payload:
            return {
                "readiness_audit_loaded": False,
            }
        return {
            "readiness_audit_loaded": True,
            "warm_final_layer_fixed_test_replay_ready": bool(payload.get("warm", {}).get("final_layer", {}).get("final_layer_replay_ready")),
            "warm_partial_upstream_refreeze_ready": bool(payload.get("warm", {}).get("exact_raw", {}).get("partial_upstream_refreeze_ready")),
            "warm_exact_raw_adapter_ready": bool(
                self._warm_wmin8_exact_runtime_ready()
                or payload.get("warm", {}).get("exact_raw", {}).get("exact_raw_adapter_ready")
            ),
            "cold_final_layer_fixed_test_replay_ready": bool(payload.get("cold", {}).get("final_layer", {}).get("final_layer_replay_ready")),
            "cold_partial_upstream_refreeze_ready": bool(payload.get("cold", {}).get("exact_raw", {}).get("partial_upstream_refreeze_ready")),
            "cold_exact_raw_adapter_ready": bool(payload.get("cold", {}).get("exact_raw", {}).get("exact_raw_adapter_ready")),
            "readiness_audit_path": str(EXACT_ADAPTER_READINESS_JSON),
        }

    def _readiness_audit_checks(self) -> dict[str, int | bool | str]:
        return self._readiness_adapter_status()

    def _resolve_artist_internal(self, artist_input: Any, max_candidates: int = 5) -> ArtistMatch:
        selected_key = artist_input.selected_artist_key or artist_input.artist_key
        warnings: list[WarningItem] = []
        with self._connect() as conn:
            if selected_key:
                row = conn.execute(
                    "SELECT * FROM artist_registry WHERE artist_key = ?",
                    (selected_key,),
                ).fetchone()
                if row:
                    artist = self._resolved_artist(conn, row, 1.0, 0.0, "direct_key", selected_key, "artist_key 직접 지정")
                    return ArtistMatch(artist, [artist], True, False, warnings)

            names = [artist_input.name_ko, artist_input.name_en]
            normalized_names = [normalize_name(name) for name in names if normalize_name(name)]
            if not normalized_names:
                warnings.append(WarningItem(
                    code="ARTIST_NAME_MISSING",
                    message="작가명이 없어 작가 후보를 조회하지 못했습니다.",
                ))
                return ArtistMatch(None, [], False, False, warnings)

            rows = conn.execute(
                f"""
                SELECT DISTINCT r.*, a.alias_text, a.alias_normalized
                FROM artist_aliases a
                JOIN artist_registry r ON r.artist_key = a.artist_key
                WHERE a.alias_normalized IN ({",".join("?" for _ in normalized_names)})
                ORDER BY r.valid_price_count DESC
                """,
                tuple(normalized_names),
            ).fetchall()
            match_status = "alias"
            match_basis = "정규화 작가명 일치"

            if not rows:
                like_patterns = [f"%{name}%" for name in normalized_names if len(name) >= 2]
                if like_patterns:
                    rows = conn.execute(
                        f"""
                        SELECT DISTINCT r.*, a.alias_text, a.alias_normalized
                        FROM artist_aliases a
                        JOIN artist_registry r ON r.artist_key = a.artist_key
                        WHERE {" OR ".join("a.alias_normalized LIKE ?" for _ in like_patterns)}
                        ORDER BY r.valid_price_count DESC
                        LIMIT ?
                        """,
                        (*like_patterns, max_candidates),
                    ).fetchall()
                    match_status = "fuzzy"
                    match_basis = "부분 작가명 일치"

            if not rows:
                warnings.append(WarningItem(
                    code="ARTIST_NOT_RESOLVED",
                    message="입력 작가명을 학습 작가 사전에서 찾지 못했습니다.",
                ))
                return ArtistMatch(None, [], False, False, warnings)

            candidate_count = len({row["artist_key"] for row in rows})
            candidates: list[ResolvedArtist] = []
            seen: set[str] = set()
            for row in rows:
                if row["artist_key"] in seen:
                    continue
                seen.add(row["artist_key"])
                score = 1.0 if match_status == "alias" else 0.78
                if artist_input.birth_year and row["birth_year"]:
                    score += 0.05 if int(artist_input.birth_year) == int(row["birth_year"]) else -0.15
                score = max(0.0, min(score, 1.0 if match_status == "alias" else 0.95))
                homonym_risk = min(1.0, max(0.0, (candidate_count - 1) * 0.35 + int(row["is_homonym"] or 0) * 0.25))
                candidates.append(self._resolved_artist(
                    conn,
                    row,
                    score,
                    homonym_risk,
                    match_status,
                    row["alias_text"],
                    match_basis,
                ))
                if len(candidates) >= max_candidates:
                    break

        requires_selection = len(candidates) > 1
        resolved = len(candidates) == 1 and not candidates[0].review_required
        if requires_selection:
            warnings.append(WarningItem(
                code="ARTIST_AMBIGUOUS",
                message="같은 이름 또는 유사 이름의 작가 후보가 2명 이상입니다. 후보 선택 후 예측하는 것이 안전합니다.",
            ))
        return ArtistMatch(candidates[0] if resolved else None, candidates, resolved, requires_selection, warnings)

    def _resolved_artist(
        self,
        conn: sqlite3.Connection,
        row: sqlite3.Row,
        score: float,
        homonym_risk: float,
        match_status: str,
        matched_alias: str | None,
        match_basis: str,
    ) -> ResolvedArtist:
        count = int(row["valid_price_count"] or 0)
        warm_available = score >= WARM_MATCH_SCORE_MIN and count >= WARM_LITE_PRICE_COUNT_MIN and homonym_risk < 0.60
        if warm_available and count >= WARM_FULL_PRICE_COUNT_MIN:
            route = "warm"
        elif warm_available:
            route = "warm_lite"
        else:
            route = "cold"
        review_required = homonym_risk >= 0.60 and match_status != "direct_key"
        if review_required:
            route = "review_required"
        return ResolvedArtist(
            artist_key=row["artist_key"],
            name_ko=row["name_ko"],
            name_en=row["name_en"],
            birth_year=safe_int(row["birth_year"]),
            nationality=row["nationality"],
            nationality_ko=row["nationality_ko"],
            entity_suffix=row["entity_suffix"],
            match_status=match_status,  # type: ignore[arg-type]
            matched_alias=matched_alias,
            match_basis=match_basis,
            artist_match_score=round(score, 4),
            homonym_risk_score=round(homonym_risk, 4),
            review_required=review_required,
            warm_available=warm_available,
            same_artist_training_price_count=count,
            route_recommendation=route,  # type: ignore[arg-type]
            display_route_recommendation=self._display_route(route),
            representative_artworks=self._representative_artworks(conn, row["artist_key"]),
        )

    def _representative_artworks(self, conn: sqlite3.Connection, artist_key: str, limit: int = 3) -> list[RepresentativeArtwork]:
        rows = conn.execute(
            """
            SELECT source_artwork_id, title, artist_name_ko, price_krw, width_cm, height_cm,
                   medium_category, support_category, area_cm2
            FROM artwork_price_observations
            WHERE artist_key = ? AND price_krw IS NOT NULL
            ORDER BY price_krw DESC
            LIMIT ?
            """,
            (artist_key, limit),
        ).fetchall()
        return [
            RepresentativeArtwork(
                artwork_id=row["source_artwork_id"],
                title=row["title"] or "제목 정보 없음",
                artist_name=row["artist_name_ko"],
                sale_price_krw=safe_int(row["price_krw"]),
                sale_price_display=format_krw(safe_int(row["price_krw"])),
                width_cm=safe_float(row["width_cm"]),
                height_cm=safe_float(row["height_cm"]),
                medium_category=row["medium_category"],
                support_category=row["support_category"],
                ho_size=ho_size_from_area(safe_float(row["area_cm2"])),
                ho_size_display=self._ho_display(ho_size_from_area(safe_float(row["area_cm2"]))),
            )
            for row in rows
        ]

    def _input_quality(self, request: PriceEstimateRequest) -> InputQuality:
        missing_required: list[str] = []
        missing_recommended: list[str] = []
        artist = request.artwork.artist
        if not any([artist.artist_key, artist.selected_artist_key, artist.name_ko, artist.name_en]):
            missing_required.append("artist.name_ko 또는 artist.name_en")
        if request.artwork.dimensions.width_cm is None:
            missing_required.append("dimensions.width_cm")
        if request.artwork.dimensions.height_cm is None:
            missing_required.append("dimensions.height_cm")
        if not request.artwork.medium.medium_category:
            missing_required.append("medium.medium_category")
        if not request.artwork.medium.support_category:
            missing_required.append("medium.support_category")
        if request.artwork.year is None:
            missing_recommended.append("year")
        if not request.artwork.title:
            missing_recommended.append("title")
        return InputQuality(
            minimum_input_status="failed" if missing_required else "passed",
            missing_required_fields=missing_required,
            missing_recommended_fields=missing_recommended,
            confidence_penalty_reasons=["권장 입력값 일부 누락"] if missing_recommended else [],
        )

    def _route(self, match: ArtistMatch) -> str:
        if match.requires_selection and not match.resolved:
            return "review_required"
        if match.artist and match.artist.review_required:
            return "review_required"
        if match.artist and match.artist.warm_available:
            count = match.artist.same_artist_training_price_count
            if count >= WARM_FULL_PRICE_COUNT_MIN:
                return "warm"
            if count >= WARM_LITE_PRICE_COUNT_MIN:
                return "warm_lite"
        return "cold"

    def _choose_stats(
        self,
        route: str,
        artist_key: str | None,
        medium: str | None,
        support: str | None,
        bucket: str,
    ) -> StatChoice:
        priorities: list[tuple[str, tuple[Any, ...], str]]
        if route in {"warm", "warm_lite"} and artist_key:
            priorities = [
                (
                    "same_artist_medium_support_size",
                    (artist_key, medium, support, bucket),
                    "같은 작가 + 같은 재료/지지체 + 유사 크기",
                ),
                (
                    "same_artist_medium_support",
                    (artist_key, medium, support, None),
                    "같은 작가 + 같은 재료/지지체",
                ),
                (
                    "cross_artist_medium_support_size",
                    (None, medium, support, bucket),
                    "다른 작가 포함 + 같은 재료/지지체 + 유사 크기",
                ),
                (
                    "cross_artist_medium_support",
                    (None, medium, support, None),
                    "다른 작가 포함 + 같은 재료/지지체",
                ),
                ("market_size", (None, None, None, bucket), "전체 시장 + 유사 크기"),
                ("market_global", (None, None, None, None), "전체 시장"),
            ]
        else:
            priorities = [
                (
                    "cross_artist_medium_support_size",
                    (None, medium, support, bucket),
                    "다른 작가 포함 + 같은 재료/지지체 + 유사 크기",
                ),
                (
                    "cross_artist_medium_support",
                    (None, medium, support, None),
                    "다른 작가 포함 + 같은 재료/지지체",
                ),
                ("market_size", (None, None, None, bucket), "전체 시장 + 유사 크기"),
                ("market_global", (None, None, None, None), "전체 시장"),
            ]
        with self._connect() as conn:
            for scope, values, source in priorities:
                row = self._stats_query(conn, scope, *values)
                if row:
                    return StatChoice(row=row, scope=scope, source=source)
        return StatChoice(row=None, scope=None, source="가격 통계 없음")

    def _stats_query(
        self,
        conn: sqlite3.Connection,
        scope: str,
        artist_key: str | None,
        medium: str | None,
        support: str | None,
        bucket: str | None,
    ) -> sqlite3.Row | None:
        clauses = ["cache_version = ?", "scope = ?"]
        params: list[Any] = [SNAPSHOT_VERSION, scope]
        for column, value in [
            ("artist_key", artist_key),
            ("medium_category", medium),
            ("support_category", support),
            ("size_bucket", bucket),
        ]:
            if value is None:
                clauses.append(f"{column} IS NULL")
            else:
                clauses.append(f"{column} = ?")
                params.append(value)
        return conn.execute(
            f"""
            SELECT *
            FROM similar_artwork_stats_cache
            WHERE {" AND ".join(clauses)}
            ORDER BY sample_count DESC
            LIMIT 1
            """,
            tuple(params),
        ).fetchone()

    def _price_from_stats(
        self,
        route: str,
        stats: StatChoice,
        ho_size: int | None,
        artist: ResolvedArtist | None,
    ) -> tuple[int | None, int | None, int | None]:
        if stats.row is None:
            return None, None, None
        median_per_ho = safe_int(stats.row["median_krw_per_ho"])
        q25_per_ho = safe_int(stats.row["q25_krw_per_ho"])
        q75_per_ho = safe_int(stats.row["q75_krw_per_ho"])
        if ho_size and median_per_ho:
            mid = median_per_ho * ho_size
            low = q25_per_ho * ho_size if q25_per_ho else safe_int(stats.row["q25_price_krw"])
            high = q75_per_ho * ho_size if q75_per_ho else safe_int(stats.row["q75_price_krw"])
        else:
            mid = safe_int(stats.row["median_price_krw"])
            low = safe_int(stats.row["q25_price_krw"])
            high = safe_int(stats.row["q75_price_krw"])
        if route in {"warm", "warm_lite"} and artist and stats.scope and stats.scope.startswith("same_artist"):
            # The final report model will replace this small foundation blend.
            artist_median = self._artist_median_price(artist.artist_key)
            if artist_median and mid:
                mid = int(round(0.70 * mid + 0.30 * artist_median))
        if mid and low and high:
            low = min(low, mid)
            high = max(high, mid)
        return mid, low, high

    def _artist_median_price(self, artist_key: str) -> int | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT median_price_krw FROM artist_registry WHERE artist_key = ?",
                (artist_key,),
            ).fetchone()
        return safe_int(row["median_price_krw"]) if row else None

    def _confidence(
        self,
        route: str,
        artist: ResolvedArtist | None,
        stats: StatChoice,
        input_quality: InputQuality,
    ) -> Confidence:
        if route == "review_required":
            return Confidence(level="low", score=0.20, reason_codes=["ARTIST_REVIEW_REQUIRED"])
        count = safe_int(stats.row["sample_count"]) if stats.row else 0
        coverage_score = min(1.0, (count or 0) / 20.0)
        match_score = artist.artist_match_score if artist else 0.45
        input_score = 1.0 if input_quality.minimum_input_status == "passed" else 0.2
        score = 0.45 * match_score + 0.35 * coverage_score + 0.20 * input_score
        if route == "cold":
            score = min(score, 0.62)
        level = "high" if score >= 0.75 else "medium" if score >= 0.45 else "low"
        reasons = ["MINIMUM_INPUT_PASSED" if input_score >= 1.0 else "MINIMUM_INPUT_FAILED"]
        if artist:
            reasons.append("ARTIST_MATCHED")
        if count and count >= 5:
            reasons.append("SIMILAR_PRICE_HISTORY_USED")
        if route == "warm_lite":
            reasons.append("LOW_HISTORY_WARM_LITE")
        if route == "cold":
            reasons.append("REFERENCE_PREDICTION")
        return Confidence(level=level, score=round(score, 4), reason_codes=reasons)

    def _market_reference(self, stats: StatChoice, ho_size: int | None, price: int | None) -> MarketReference:
        median_per_ho = safe_int(stats.row["median_krw_per_ho"]) if stats.row else None
        q25_per_ho = safe_int(stats.row["q25_krw_per_ho"]) if stats.row else None
        q75_per_ho = safe_int(stats.row["q75_krw_per_ho"]) if stats.row else None
        converted = median_per_ho * ho_size if median_per_ho and ho_size else None
        return MarketReference(
            target_ho_size=ho_size,
            target_ho_size_display=self._ho_display(ho_size),
            median_krw_per_ho=median_per_ho,
            median_display=f"{format_krw(median_per_ho)}/호" if median_per_ho else "-",
            range_krw_per_ho=RangePerHo(low=q25_per_ho, high=q75_per_ho),
            range_display=(
                f"{format_krw(q25_per_ho)}/호 - {format_krw(q75_per_ho)}/호"
                if q25_per_ho and q75_per_ho
                else "-"
            ),
            converted_total_price_krw=converted,
            converted_total_price_display=format_krw(converted),
            medium_distribution=self._medium_distribution(stats),
            sample_count=safe_int(stats.row["sample_count"]) if stats.row else 0,
            sample_count_display=f"N={safe_int(stats.row['sample_count']) or 0}건",
        )

    def _medium_distribution(self, stats: StatChoice) -> list[MediumDistribution]:
        if not stats.row:
            return []
        scope = stats.scope or ""
        artist_key = stats.row["artist_key"]
        params: list[Any] = []
        clauses = ["price_krw IS NOT NULL", "area_cm2 IS NOT NULL", "area_cm2 > 0"]
        if scope.startswith("same_artist") and artist_key:
            clauses.append("artist_key = ?")
            params.append(artist_key)
        medium = stats.row["medium_category"]
        support = stats.row["support_category"]
        if medium:
            clauses.append("medium_category = ?")
            params.append(medium)
        if support:
            clauses.append("support_category = ?")
            params.append(support)
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT medium_category, price_krw, area_cm2
                FROM artwork_price_observations
                WHERE {" AND ".join(clauses)}
                """,
                tuple(params),
            ).fetchall()
        grouped: dict[str, list[int]] = {}
        for row in rows:
            ho = max(float(row["area_cm2"]) / HO_AREA_CM2, 1.0)
            per_ho = int(round(float(row["price_krw"]) / ho))
            grouped.setdefault(row["medium_category"] or "unknown", []).append(per_ho)
        items: list[MediumDistribution] = []
        for label, values in sorted(grouped.items(), key=lambda item: len(item[1]), reverse=True)[:5]:
            values_sorted = sorted(values)
            median_value = values_sorted[len(values_sorted) // 2]
            items.append(MediumDistribution(
                label=label,
                median_krw_per_ho=median_value,
                display=f"{label} {format_krw(median_value)}/호 · {len(values)}건",
                sample_count=len(values),
            ))
        return items

    def _similar_artworks(
        self,
        route: str,
        artist_key: str | None,
        medium: str | None,
        support: str | None,
        target_area: float | None,
        limit: int,
    ) -> list[SimilarArtwork]:
        if limit <= 0:
            return []
        clauses = ["price_krw IS NOT NULL"]
        params: list[Any] = []
        reason = "같은 재료/지지체"
        tier = "medium"
        if route in {"warm", "warm_lite"} and artist_key:
            clauses.append("artist_key = ?")
            params.append(artist_key)
            reason = "같은 작가 + 같은 재료/지지체"
            tier = "strong"
        if medium:
            clauses.append("medium_category = ?")
            params.append(medium)
        if support:
            clauses.append("support_category = ?")
            params.append(support)
        order_expr = "price_krw DESC"
        if target_area:
            order_expr = "ABS(area_cm2 - ?) ASC"
            params.append(target_area)
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT source_artwork_id, title, artist_name_ko, price_krw, width_cm,
                       height_cm, medium_category, support_category, area_cm2
                FROM artwork_price_observations
                WHERE {" AND ".join(clauses)}
                ORDER BY {order_expr}
                LIMIT ?
                """,
                (*params, limit),
            ).fetchall()
        return [
            SimilarArtwork(
                artwork_id=row["source_artwork_id"],
                title=row["title"] or "제목 정보 없음",
                artist_name=row["artist_name_ko"],
                sale_price_krw=safe_int(row["price_krw"]),
                sale_price_display=format_krw(safe_int(row["price_krw"])),
                width_cm=safe_float(row["width_cm"]),
                height_cm=safe_float(row["height_cm"]),
                medium_category=row["medium_category"],
                support_category=row["support_category"],
                ho_size=ho_size_from_area(safe_float(row["area_cm2"])),
                ho_size_display=self._ho_display(ho_size_from_area(safe_float(row["area_cm2"]))),
                similarity_tier=tier,  # type: ignore[arg-type]
                similarity_reason=reason,
            )
            for row in rows
        ]

    def _similar_artists(self, artist_key: str | None, limit: int = 5) -> list[SimilarArtistReference]:
        if not artist_key:
            return []
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT s.similarity_score, s.price_history_count, s.match_reasons_json,
                       r.artist_key, r.name_ko, r.birth_year, r.nationality,
                       r.primary_medium_category, r.primary_support_category, r.median_price_krw
                FROM similar_artist_cache s
                JOIN artist_registry r ON r.artist_key = s.candidate_artist_key
                WHERE s.cache_version = ? AND s.target_artist_key = ?
                ORDER BY s.similarity_score DESC, s.price_history_count DESC
                LIMIT ?
                """,
                (SNAPSHOT_VERSION, artist_key, limit),
            ).fetchall()
        refs: list[SimilarArtistReference] = []
        for row in rows:
            reasons_json = json.loads(row["match_reasons_json"] or "{}")
            reason_labels = []
            if reasons_json.get("same_nationality"):
                reason_labels.append("국적 유사")
            if reasons_json.get("same_career_stage"):
                reason_labels.append("활동 단계 유사")
            if reasons_json.get("same_primary_medium"):
                reason_labels.append("주요 재료 유사")
            if reasons_json.get("same_primary_support"):
                reason_labels.append("주요 지지체 유사")
            refs.append(SimilarArtistReference(
                artist_key=row["artist_key"],
                name_ko=row["name_ko"],
                birth_year=safe_int(row["birth_year"]),
                nationality=row["nationality"],
                similarity_score=round(float(row["similarity_score"]), 4),
                price_history_count=safe_int(row["price_history_count"]) or 0,
                primary_medium=row["primary_medium_category"],
                primary_support=row["primary_support_category"],
                median_price_display=format_krw(safe_int(row["median_price_krw"])),
                match_reasons=reason_labels,
            ))
        return refs

    def _calculation_steps(
        self,
        route: str,
        request: PriceEstimateRequest,
        stats: StatChoice,
        price: int | None,
        low: int | None,
        high: int | None,
        ho_size: int | None,
        artist: ResolvedArtist | None,
        adapter_result: Any | None = None,
    ) -> list[CalculationStep]:
        display_route = self._display_route(route)
        adapter_status = self._route_adapter_status(route, adapter_result)
        return [
            CalculationStep(
                step_order=1,
                name="입력값 표준화",
                role="작가명, 크기, 재료, 지지체를 DB 조회 가능한 값으로 정리",
                formula="작품면적 = 가로(cm) * 세로(cm), 호수 = round(작품면적 / 220.5)",
                input={
                    "width_cm": request.artwork.dimensions.width_cm,
                    "height_cm": request.artwork.dimensions.height_cm,
                    "medium_category": request.artwork.medium.medium_category,
                    "support_category": request.artwork.medium.support_category,
                },
                output={"ho_size": ho_size, "display_route": display_route},
            ),
            CalculationStep(
                step_order=2,
                name="작가 매칭과 경로 판단",
                role="같은 작가 이력이 충분하면 이력 기반 예측, 부족하면 참고 예측으로 분기",
                formula=(
                    f"작가매칭점수 >= {WARM_MATCH_SCORE_MIN}일 때 "
                    f"가격이력 1~{WARM_FULL_PRICE_COUNT_MIN - 1}건은 저이력 기반 예측, "
                    f"{WARM_FULL_PRICE_COUNT_MIN}건 이상은 이력 기반 예측, 0건은 참고 예측"
                ),
                output={
                    "artist_key": artist.artist_key if artist else None,
                    "artist_match_score": artist.artist_match_score if artist else None,
                    "same_artist_training_price_count": artist.same_artist_training_price_count if artist else None,
                    "route": route,
                },
            ),
            CalculationStep(
                step_order=3,
                name="가격 근거 통계 선택",
                role="유사작품 통계 cache에서 가장 구체적인 가격 근거를 선택",
                formula="우선순위 = 같은작가+같은재료/지지체+유사크기 -> 같은작가+같은재료/지지체 -> 타작가포함+같은재료/지지체 -> 전체시장",
                output={
                    "selected_scope": stats.scope,
                    "selected_source": stats.source,
                    "sample_count": safe_int(stats.row["sample_count"]) if stats.row else None,
                },
            ),
            CalculationStep(
                step_order=4,
                name="DB/cache 기반 기준 가격 계산",
                role="호당 중앙값과 입력 작품 호수를 이용해 1차 기준 가격을 계산",
                formula="기준가격 = 호당중앙값 * 입력작품호수",
                output={
                    "price_krw": price,
                    "range_low_krw": low,
                    "range_high_krw": high,
                },
            ),
            CalculationStep(
                step_order=5,
                name="보고서 최종 adapter 연결 상태",
                role="보고서 기준 최종 계산층과 raw 입력 상류 feature adapter의 연결 상태를 확인",
                formula=adapter_status["formula"],
                output={
                    "adapter_execution_level": adapter_status["execution_level"],
                    "final_layer_module_loaded": adapter_status["final_layer_module_loaded"],
                    "raw_upstream_adapter_ready": adapter_status["raw_upstream_adapter_ready"],
                    "raw_proxy_adapter_ready": adapter_status.get("raw_proxy_adapter_ready", False),
                    "missing_upstream_columns": adapter_status["required_upstream_columns"],
                    "proxy_input_columns": adapter_status.get("proxy_input_columns"),
                    "adapter_output": adapter_status.get("adapter_output"),
                    "adapter_steps": adapter_status.get("adapter_steps"),
                },
            ),
        ]

    def _store_prediction(
        self,
        response: PriceEstimateResponse,
        request: PriceEstimateRequest,
        steps: list[CalculationStep],
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO prediction_events (
                  prediction_id, request_id, service_version, route, display_route,
                  artist_key, artist_match_score, same_artist_training_price_count,
                  input_snapshot_json, input_quality_json, prediction_price_krw,
                  range_low_krw, range_high_krw, confidence_tier,
                  model_artifacts_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    response.prediction_id,
                    response.request_id,
                    SERVICE_VERSION,
                    response.route,
                    response.display_route,
                    response.routing.matched_artist_key,
                    response.routing.artist_match_score,
                    response.routing.same_artist_training_price_count,
                    request.model_dump_json(),
                    response.input_quality.model_dump_json(),
                    response.prediction.price_krw,
                    response.prediction.range_krw.low,
                    response.prediction.range_krw.high,
                    response.prediction.confidence.level,
                    json.dumps(self._active_artifacts(), ensure_ascii=False, sort_keys=True),
                    response.created_at,
                ),
            )
            conn.execute("DELETE FROM prediction_calculation_steps WHERE prediction_id = ?", (response.prediction_id,))
            for step in steps:
                conn.execute(
                    """
                    INSERT INTO prediction_calculation_steps (
                      step_id, prediction_id, step_order, step_name, step_role,
                      formula_text, input_json, output_json, display_flag, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        stable_id("step", [response.prediction_id, step.step_order]),
                        response.prediction_id,
                        step.step_order,
                        step.name,
                        step.role,
                        step.formula,
                        json.dumps(step.input, ensure_ascii=False, sort_keys=True),
                        json.dumps(step.output, ensure_ascii=False, sort_keys=True),
                        1,
                        response.created_at,
                    ),
                )
            conn.commit()

    @staticmethod
    def _row_to_json(row: sqlite3.Row | None) -> dict[str, object] | None:
        if row is None:
            return None
        result: dict[str, object] = {}
        for key in row.keys():
            value = row[key]
            if isinstance(value, str) and key.endswith("_json"):
                try:
                    result[key] = json.loads(value)
                    continue
                except json.JSONDecodeError:
                    pass
            result[key] = value
        return result

    @staticmethod
    def _display_route(route: str) -> str:
        if route == "warm":
            return "이력 기반 예측"
        if route == "warm_lite":
            return "저이력 기반 예측"
        if route == "cold":
            return "참고 예측"
        return "확인 필요"

    @staticmethod
    def _display_policy(route: str) -> str:
        if route == "warm":
            return "price_with_range"
        if route == "warm_lite":
            return "price_with_range"
        if route == "cold":
            return "reference_range_only"
        return "review_required"

    @staticmethod
    def _route_reason(route: str, artist: ResolvedArtist | None) -> str:
        if route == "warm":
            return "작가 매칭 신뢰도와 같은 작가 가격 이력이 이력 기반 예측 기준을 충족했습니다."
        if route == "warm_lite":
            return "작가 매칭 신뢰도는 충분하지만 같은 작가 가격 이력이 1~4건이라 저이력 기반 예측을 적용했습니다."
        if route == "cold":
            return "같은 작가 가격 이력이 부족하거나 작가 매칭 신뢰도가 낮아 참고 예측을 적용했습니다."
        if artist and artist.review_required:
            return "동명이인 위험이 있어 작가 후보 선택 또는 검수가 필요합니다."
        return "최소 입력값이 부족하거나 작가 확인이 필요합니다."

    @staticmethod
    def _user_formula(route: str) -> str:
        if route == "warm":
            return "예측가격 = 기준가격 + 미세보정값"
        if route == "warm_lite":
            return "예측가격 = 저이력 작가 기준가격 + Warm-lite 보정값"
        if route == "cold":
            return "참고가격 = 조건이 비슷한 작품군의 시장 기준가격 + 검색/방어 보정값"
        return "작가 확인 후 가격 계산"

    @staticmethod
    def _calculation_explanation(route: str) -> str:
        if route == "warm":
            return "같은 작가 가격 이력과 유사작품 통계로 기준가격을 만들고, 연결 가능한 보고서 기준 Warm 보정 adapter를 적용합니다."
        if route == "warm_lite":
            return "같은 작가 가격 이력이 1~4건일 때 저이력 전용 Warm-lite 모델로 기준가격과 보정값을 함께 계산합니다."
        if route == "cold":
            return "같은 작가 이력이 부족한 경우 작품 조건 기반 참고가격을 만들고, feature store 또는 proxy feature로 보고서 기준 Cold 후처리 adapter를 적용합니다."
        return "동명이인 또는 최소 입력 부족으로 단일 가격 계산을 보류했습니다."

    @staticmethod
    def _warm_final_layer_available() -> bool:
        return module_exports_available(
            str(WARM_PP258_FINAL_LAYER_PATH),
            ("calculate_pp258_predictions", "MODEL_PARAMS"),
        )

    @staticmethod
    def _cold_final_layer_available() -> bool:
        return module_exports_available(
            str(COLD_V03_POSTPROCESSOR_PATH),
            ("apply", "load_params", "load_search_lookup"),
        )

    @staticmethod
    def _report_proxy_adapter_available() -> bool:
        return (
            COLD_V02_RAW_PREDICTOR_PATH.exists()
            and OfficialV01Service._warm_final_layer_available()
            and OfficialV01Service._cold_final_layer_available()
        )

    def _report_adapter(self) -> Any:
        if self._report_proxy_adapter is None:
            from visionai.price_engine.api.official_v0_1_report_adapters import ReportModelProxyAdapter

            self._report_proxy_adapter = ReportModelProxyAdapter(db_path=self.db_path)
        return self._report_proxy_adapter

    def _try_report_proxy_adapter(
        self,
        route: str,
        request: PriceEstimateRequest,
        artist_key: str | None,
    ) -> Any | None:
        if route == "warm" and artist_key:
            try:
                return self._report_adapter().predict_warm(request, artist_key)
            except Exception:
                return None
        if route == "warm_lite" and artist_key:
            try:
                return self._report_adapter().predict_warm_lite(request, artist_key)
            except Exception:
                return None
        if route == "cold":
            try:
                return self._report_adapter().predict_cold(request, artist_key)
            except Exception:
                return None
        return None

    def _route_adapter_status(self, route: str, adapter_result: Any | None = None) -> dict[str, Any]:
        if adapter_result is not None:
            if adapter_result.route == "warm_lite":
                required_columns: Any = [
                    "width_cm",
                    "height_cm",
                    "area_cm2",
                    "log_area",
                    "medium_category",
                    "support_category",
                    "size_bucket",
                    "medium_support_bucket",
                    "artist_history_1_to_4",
                ]
            else:
                required_columns = (
                    WARM_PP258_REQUIRED_UPSTREAM_COLUMNS
                    if adapter_result.route == "warm"
                    else COLD_V03_REQUIRED_UPSTREAM_COLUMNS
                )
            return {
                "execution_level": adapter_result.execution_level,
                "final_layer_module_loaded": True,
                "raw_upstream_adapter_ready": adapter_result.execution_level == "report_model_adapter",
                "raw_proxy_adapter_ready": True,
                "required_upstream_columns": required_columns,
                "proxy_input_columns": adapter_result.input_columns,
                "warning_code": adapter_result.warning_code,
                "warning_message": adapter_result.warning_message,
                "formula": adapter_result.formula,
                "adapter_output": adapter_result.output,
                "adapter_steps": adapter_result.steps,
            }
        if route == "warm":
            return {
                "execution_level": "db_cache_foundation",
                "final_layer_module_loaded": self._warm_final_layer_available(),
                "raw_upstream_adapter_ready": False,
                "required_upstream_columns": WARM_PP258_REQUIRED_UPSTREAM_COLUMNS,
                "warning_code": "WARM_REPORT_UPSTREAM_ADAPTER_PENDING",
                "warning_message": (
                    "보고서 기준 Warm 최종 계산층 파일은 확인됐지만, 사용자 입력에서 "
                    "pp252 기준 로그가격, 방향 확률, Huber 잔차, 불확실성 피처를 생성하는 "
                    "상류 adapter 연결 전입니다. 현재 가격은 DB/cache 기반 기준가격입니다."
                ),
                "formula": (
                    "보고서 Warm 최종가격 = PP258최종층("
                    "pp252기준로그가격, 안정성기준로그가격, 방향확률, Huber잔차, 불확실성피처)"
                ),
            }
        if route == "warm_lite":
            return {
                "execution_level": "db_cache_foundation",
                "final_layer_module_loaded": WARM_LITE_POLICY_PATH.exists(),
                "raw_upstream_adapter_ready": WARM_LITE_POLICY_PATH.exists(),
                "required_upstream_columns": [
                    "width_cm",
                    "height_cm",
                    "area_cm2",
                    "log_area",
                    "medium_category",
                    "support_category",
                    "size_bucket",
                    "medium_support_bucket",
                    "artist_history_1_to_4",
                ],
                "warning_code": "WARM_LITE_ADAPTER_PENDING",
                "warning_message": "Warm-lite 아티팩트는 확인됐지만 adapter 실행 결과가 없어 DB/cache 기반 기준가격을 표시했습니다.",
                "formula": "Warm-lite 예측가격 = Huber앙상블(작품조건 + 작가 1~4건 이력 통계 + 비작가 fallback 통계)",
            }
        if route == "cold":
            return {
                "execution_level": "db_cache_foundation",
                "final_layer_module_loaded": self._cold_final_layer_available(),
                "raw_upstream_adapter_ready": False,
                "required_upstream_columns": COLD_V03_REQUIRED_UPSTREAM_COLUMNS,
                "warning_code": "COLD_REPORT_UPSTREAM_ADAPTER_PENDING",
                "warning_message": (
                    "보고서 기준 Cold 최종 후처리 파일은 확인됐지만, 사용자 입력에서 "
                    "LightGBM Quantile 후보, 대표 후보, 가격범위폭, 작가 검색 보정값을 생성하는 "
                    "상류 adapter 연결 전입니다. 현재 가격은 DB/cache 기반 참고가격입니다."
                ),
                "formula": (
                    "보고서 Cold 최종가격 = v0.3후처리("
                    "대표로그가격, LightGBM Quantile 로그가격, 가격범위폭, 작가검색보정)"
                ),
            }
        return {
            "execution_level": "db_cache_foundation",
            "final_layer_module_loaded": False,
            "raw_upstream_adapter_ready": False,
            "required_upstream_columns": [],
            "warning_code": "REPORT_MODEL_ADAPTER_NOT_APPLIED",
            "warning_message": "작가 확인 또는 최소 입력 보완 전에는 보고서 최종 adapter를 적용하지 않습니다.",
            "formula": "작가 확인 후 보고서 모델 adapter 적용",
        }

    @staticmethod
    def _prediction_id(request: PriceEstimateRequest, route: str, artist_key: str | None, stats_scope: str | None) -> str:
        payload = {
            "service_version": SERVICE_VERSION,
            "snapshot_version": SNAPSHOT_VERSION,
            "route": route,
            "artist_key": artist_key,
            "stats_scope": stats_scope,
            "request": request.model_dump(mode="json"),
        }
        return stable_id("pred", payload)

    @staticmethod
    def _ho_display(ho_size: int | None) -> str | None:
        if ho_size is None:
            return None
        return f"{ho_size}호"
