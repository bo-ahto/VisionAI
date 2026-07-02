"""Local operational service for price_prediction v0.2.

v0.2 keeps the existing Warm runtime path and adds a runnable Cold path based on
the serialized LightGBM Quantile artifact.  The service is intentionally local
and deterministic so the frontend can be exercised without external search APIs.
"""

from __future__ import annotations

import importlib.util
import json
import math
import os
import uuid
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from visionai.price_engine.api import operational_v0_1_schemas as v01s
from visionai.price_engine.api.operational_v0_1_service import (
    FX_KRW_PER_UNIT,
    REPO,
    OperationalV01Service,
    dimension_area,
    exp_price,
    feature_ops,
    format_krw,
    format_krw_per_ho,
    normalize_name,
    now_kst_iso,
    safe_int,
    safe_price,
)
from visionai.price_engine.api.primary_feature_builder import area_to_ho
from visionai.price_engine.api.operational_v0_2_schemas import (
    ArtistInput,
    CalculationComponent,
    CalculationSummary,
    ComparableSample,
    Confidence,
    CurrentModelResponse,
    ExchangeRates,
    FeedbackGuide,
    InputQuality,
    MarketPriceCard,
    MediumDistribution,
    Prediction,
    PredictionBasis,
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
    WarningItem,
)


MODEL_VERSION = "price_prediction_v0.2"
WARM_MODEL_VERSION = "warm_runtime_v0.1_with_v0.2_routing_policy"
COLD_MODEL_VERSION = "cold_prediction_v0.2_operational_search_free"
COLD_V03_MODEL_VERSION = "cold_prediction_v0.3_guard_search_research_replay"
WARM_MATCH_SCORE_MIN = 0.90
WARM_TRAINING_PRICE_MIN = 5
COLD_V03_Y18_CANDIDATE = "stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min30_cap0.25"
COLD_V03_Y2_QWIDTH_CANDIDATE = "lgbq_search_all_external_interaction"
COLD_V03_CAT_Q40_CANDIDATE = "catboost_quantile_q40"
COLD_V03_LGB_Q40_CANDIDATE = "lightgbm_quantile_q40"
COLD_V03_SEARCH_SOURCE = "h23_gallery_museum_median_cap0.2"
REFERENCE_SAMPLE_POLICY = {
    "warm": {
        "scope": "same_artist",
        "label": "동일 작가의 재료/크기 유사 참고 사례",
        "medium_match_weight": 2,
        "support_match_weight": 1,
        "dedupe_key": "artist_name_width_height_price",
        "sort_order": "material_support_match_score_desc_then_target_area_distance_asc_then_price_desc",
        "similarity_reason": "same_artist_material_support_area_reference",
    },
    "cold": {
        "scope": "cross_artist_allowed",
        "label": "타 작가 포함 참고 사례",
        "medium_match_weight": 2,
        "support_match_weight": 1,
        "max_per_artist": 2,
        "dedupe_key": "artist_name_width_height_price",
        "sort_order": "material_support_match_score_desc_then_target_area_distance_asc_then_price_desc",
        "similarity_reason": "cross_artist_medium_support_area_reference",
    },
}


def prediction_id() -> str:
    return f"pred_{uuid.uuid4().hex[:16]}"


def _load_module(path: Path, module_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"모듈을 로드할 수 없습니다: {path}")
    spec.loader.exec_module(module)
    return module


class OperationalV02Service:
    """Cached model service for the v0.2 local API."""

    def __init__(
        self,
        v01_model_root: Path | None = None,
        cold_bundle_root: Path | None = None,
        feedback_store: Path | None = None,
    ) -> None:
        self.v01 = OperationalV01Service(model_root=v01_model_root)
        self.title_lookup = self._load_title_lookup()
        self.cold_bundle_root = cold_bundle_root or REPO / "models" / "track6" / "cold_prediction_v0.2_operational"
        self.cold_predictor = _load_module(
            self.cold_bundle_root / "predict" / "predict_cold_operational_v0_2.py",
            "predict_cold_operational_v0_2_runtime",
        )
        self.cold_models = self.cold_predictor.load_models()
        self.cold_guard = self.cold_predictor.load_guard()
        self.cold_v03_bundle_root = REPO / "models" / "track6" / "cold_prediction_v0.3"
        self._cold_v03_postprocessor: Any | None = None
        self._cold_v03_frame: pd.DataFrame | None = None
        self._cold_v03_policy: dict[str, Any] | None = None
        self._cold_v03_params: dict[str, Any] | None = None
        self._cold_v03_lookup: dict[str, float] | None = None
        self.artist_meta_lookup = self._load_artist_meta_lookup()
        self.artist_reference_profiles = self._build_artist_reference_profiles()
        self.feedback_store = feedback_store or Path(
            os.getenv("PRICE_PREDICTION_V02_FEEDBACK_STORE", "/private/tmp/visionai_price_prediction_v0_2_feedback.jsonl")
        )

    def current_model(self, request_id: str) -> CurrentModelResponse:
        return CurrentModelResponse(
            request_id=request_id,
            status="success",
            created_at=now_kst_iso(),
            model_version=MODEL_VERSION,
            model_status="candidate",
            display_policy={
                "warm": "price_with_range",
                "cold": "estimated_price_with_reference_warning",
                "review_required": "no_single_price",
            },
            routing_policy={
                "warm_artist_match_score_min": WARM_MATCH_SCORE_MIN,
                "warm_same_artist_training_price_min": WARM_TRAINING_PRICE_MIN,
                "ambiguous_artist_policy": "review_required",
                "cold_policy": "minimum_artwork_input_passed_with_warning_price",
            },
            exchange_rates=ExchangeRates(**FX_KRW_PER_UNIT),
            warm_model_version=WARM_MODEL_VERSION,
            cold_model_version=COLD_MODEL_VERSION,
            feedback_policy={
                "storage": "local_jsonl_for_review",
                "promotion_rule": "actual_sale_price + evidence + consent + manual_review",
            },
        )

    def resolve_artist(self, request_id: str, artist: ArtistInput, max_candidates: int = 5) -> ResolveArtistResponse:
        base = self.v01.resolve_artist(request_id=request_id, artist=artist, max_candidates=max_candidates)
        candidates = [self._convert_artist_candidate(candidate, artist, len(base.candidates)) for candidate in base.candidates]

        warnings = [WarningItem(**warning.model_dump()) for warning in base.warnings]
        if not candidates:
            warnings = [warning for warning in warnings if warning.code != "ARTIST_NOT_RESOLVED"]
        requires_selection = len(candidates) > 1 or any(candidate.review_required for candidate in candidates)
        selected = candidates[0] if len(candidates) == 1 and not candidates[0].review_required else None
        resolved = selected is not None

        if not candidates:
            warnings.append(WarningItem(
                code="ARTIST_NOT_RESOLVED_COLD_ALLOWED",
                severity="info",
                message="작가를 기존 artist_key로 확정하지 못했습니다. 최소 작품 정보가 있으면 Cold 참고 가격을 계산할 수 있습니다.",
            ))
        elif requires_selection and selected is None:
            warnings.append(WarningItem(
                code="ARTIST_REVIEW_REQUIRED",
                message="작가 후보가 불명확하여 운영 검수 또는 사용자 선택이 필요합니다.",
            ))

        return ResolveArtistResponse(
            request_id=request_id,
            status="success" if resolved else "partial_success",
            created_at=now_kst_iso(),
            model_version=MODEL_VERSION,
            resolved=resolved,
            requires_selection=requires_selection,
            selected_artist=selected,
            candidates=candidates,
            warnings=warnings,
        )

    def estimate_price(self, request_id: str, request: PriceEstimateRequest) -> PriceEstimateResponse:
        artist_resolution = self.resolve_artist(request_id, request.artwork.artist, max_candidates=5)
        input_quality = self._input_quality(request)
        warnings = list(artist_resolution.warnings)

        if artist_resolution.requires_selection:
            warnings.append(WarningItem(
                code="NO_SINGLE_PRICE_ARTIST_AMBIGUOUS",
                message="동명이인 또는 유사 후보가 있어 단일 가격을 표시하지 않습니다.",
            ))
            return self._review_required_response(request_id, request, artist_resolution, input_quality, warnings)

        selected = artist_resolution.selected_artist
        if selected and selected.warm_available:
            return self._estimate_warm(request_id, request, selected, input_quality, warnings)

        if input_quality.minimum_input_status == "passed":
            return self._estimate_cold(request_id, request, selected, input_quality, warnings)

        warnings.append(WarningItem(
            code="MINIMUM_INPUT_FAILED",
            message="최소 입력값이 부족하여 가격을 계산하지 않습니다.",
        ))
        return self._review_required_response(request_id, request, artist_resolution, input_quality, warnings)

    def record_sale_price_feedback(
        self,
        request_id: str,
        payload: SalePriceFeedbackRequest,
    ) -> SalePriceFeedbackResponse:
        row = payload.model_dump()
        row["request_id"] = request_id
        row["created_at"] = now_kst_iso()
        row["review_status"] = "needs_review"
        self.feedback_store.parent.mkdir(parents=True, exist_ok=True)
        with self.feedback_store.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return SalePriceFeedbackResponse(
            request_id=request_id,
            status="success",
            created_at=now_kst_iso(),
            accepted=True,
            review_status="needs_review",
            message="실제 판매가 피드백을 저장했습니다. 검수 승인 후 학습 후보로 승격할 수 있습니다.",
        )

    def cold_v03_research_samples(self, request_id: str, split: str = "test", limit: int = 20) -> dict[str, Any]:
        """Return fixed-split rows that can replay the v0.3 guard+search path."""
        split = self._cold_v03_split(split)
        limit = max(1, min(int(limit or 20), 100))
        frame = self._cold_v03_replay_frame()
        part = frame[frame["split"].eq(split)].copy()
        if part.empty:
            raise ValueError(f"split has no v0.3 replay rows: {split}")
        part["_final_ape_sort"] = pd.to_numeric(part["cold_v03_final_ape"], errors="coerce").fillna(0.0)
        part = part.sort_values(["_final_ape_sort", "_track6_row_id"], ascending=[False, True]).head(limit)
        policy = self._cold_v03_policy_info()
        return {
            "request_id": request_id,
            "status": "success",
            "created_at": now_kst_iso(),
            "model_version": COLD_V03_MODEL_VERSION,
            "mode": "fixed_test_replay",
            "notice": "사용자 입력으로 새 예측을 만드는 것이 아니라 기존 fixed validation/test row의 v0.3 guard+search 계산을 재현하는 조회 모드입니다.",
            "split": split,
            "limit": limit,
            "available_rows": int(frame["split"].eq(split).sum()),
            "metrics": self._cold_v03_metrics(policy),
            "rows": [self._cold_v03_row_summary(row) for _, row in part.iterrows()],
        }

    def cold_v03_research_replay(self, request_id: str, row_id: int, split: str = "test") -> dict[str, Any]:
        """Replay one fixed-split row through the shipped v0.3 postprocessor."""
        split = self._cold_v03_split(split)
        frame = self._cold_v03_replay_frame()
        row_match = frame[
            frame["split"].eq(split)
            & pd.to_numeric(frame["_track6_row_id"], errors="coerce").eq(int(row_id))
        ]
        if row_match.empty:
            raise ValueError(f"v0.3 replay row not found: split={split}, row_id={row_id}")
        row = row_match.iloc[0]
        policy = self._cold_v03_policy_info()
        params = self._cold_v03_params_info()
        y18 = float(row["y18_qwidth_pred_log"])
        lgb_q40 = float(row["lgb_q40_pred_log"])
        qwidth = float(row["quantile_width_log"])
        guard_log = float(row["cold_v03_guard_only_pred_log"])
        search_delta = float(row["search_delta_applied"])
        final_log = float(row["cold_defense_pred_log"])
        qwidth_q67 = float(params["guard"]["qwidth_q67"])
        gap_q50 = float(params["guard"]["gap_q50"])
        guard_weight = float(params["guard"]["weight"])
        gap = y18 - lgb_q40
        return {
            "request_id": request_id,
            "status": "success",
            "created_at": now_kst_iso(),
            "model_version": COLD_V03_MODEL_VERSION,
            "mode": "fixed_test_replay",
            "notice": "사용자 입력으로 새 예측을 만드는 것이 아니라 기존 fixed validation/test row의 v0.3 guard+search 계산을 재현하는 조회 모드입니다.",
            "split": split,
            "metrics": self._cold_v03_metrics(policy),
            "row": self._cold_v03_row_detail(row),
            "calculation": {
                "inputs": {
                    "row_id": int(row["_track6_row_id"]),
                    "artist_key": str(row.get("artist_key") or ""),
                    "artist_search_name": str(row.get("artist_search_name") or ""),
                    "actual_price_krw": safe_price(row.get("actual_price")),
                    "y18_representative_log_price": y18,
                    "lightgbm_q40_log_price": lgb_q40,
                    "quantile_width_log": qwidth,
                    "price_range_ratio": float(row.get("price_range_ratio") or math.exp(max(qwidth, 0.0))),
                },
                "steps": [
                    {
                        "name": "대표 기준 로그가격",
                        "role": "PP-Y18 검색 피처 포함 Quantile 후보가 만든 대표 예측값입니다.",
                        "formula": "대표_로그가격 = y18_qwidth_pred_log",
                        "result_log": y18,
                        "result_price_krw": safe_price(row.get("cold_representative_pred_price_krw")),
                        "result_display": format_krw(safe_price(row.get("cold_representative_pred_price_krw"))),
                    },
                    {
                        "name": "과대예측 방어 guard",
                        "role": "예측 폭이 넓고 LightGBM q40이 대표가보다 충분히 낮으면 대표가를 q40 방향으로 낮춥니다.",
                        "formula": "조건 충족 시 guard_로그가격 = (1 - 0.5) * 대표_로그가격 + 0.5 * LightGBM_q40_로그가격",
                        "condition": (
                            f"quantile_width_log({qwidth:.6f}) >= qwidth_q67({qwidth_q67:.6f}) "
                            f"AND 대표-q40({gap:.6f}) >= gap_q50({gap_q50:.6f}) "
                            "AND q40 < 대표"
                        ),
                        "applied": bool(row.get("cold_v03_guard_applied")),
                        "weight": guard_weight,
                        "result_log": guard_log,
                        "result_price_krw": safe_price(row.get("cold_v03_guard_only_pred_price_krw")),
                        "result_display": format_krw(safe_price(row.get("cold_v03_guard_only_pred_price_krw"))),
                    },
                    {
                        "name": "작가별 search 보정",
                        "role": "검색/전시/갤러리 정보 실험에서 동결한 작가별 로그 보정값을 guard 결과에 더합니다.",
                        "formula": "search_보정_로그값 = search_delta_lookup[artist_key], 미보유 작가 = 0",
                        "covered": bool(row.get("search_covered")),
                        "search_delta_log": search_delta,
                        "source": COLD_V03_SEARCH_SOURCE,
                    },
                    {
                        "name": "최종 guard+search 가격",
                        "role": "guard 로그가격에 search 보정 로그값을 더한 뒤 원화 가격으로 되돌립니다.",
                        "formula": "최종_로그가격 = guard_로그가격 + search_보정_로그값, 최종_원화가격 = exp(최종_로그가격)",
                        "result_log": final_log,
                        "result_price_krw": safe_price(row.get("cold_defense_pred_price_krw")),
                        "result_display": format_krw(safe_price(row.get("cold_defense_pred_price_krw"))),
                    },
                ],
            },
        }

    def _convert_artist_candidate(
        self,
        candidate: v01s.ResolvedArtist,
        requested: ArtistInput,
        candidate_count: int,
    ) -> ResolvedArtist:
        direct_key = bool(requested.artist_key and normalize_name(requested.artist_key) == normalize_name(candidate.artist_key))
        if direct_key:
            match_score = 1.0
            homonym_risk = 0.0
            review_required = candidate_count > 1
        elif candidate.match_status in {"exact", "alias"}:
            match_score = 0.95
            homonym_risk = 0.05 if candidate_count == 1 else 0.45
            review_required = candidate_count > 1
        elif candidate.match_status == "fuzzy":
            match_score = 0.80
            homonym_risk = 0.25 if candidate_count == 1 else 0.55
            review_required = True
        else:
            match_score = 0.65
            homonym_risk = 0.60
            review_required = True

        count = candidate.valid_training_label_count or 0
        warm_available = (
            match_score >= WARM_MATCH_SCORE_MIN
            and count >= WARM_TRAINING_PRICE_MIN
            and not review_required
        )
        route = "warm" if warm_available else ("review_required" if review_required else "cold")
        return ResolvedArtist(
            artist_key=candidate.artist_key,
            name_ko=candidate.name_ko,
            name_en=candidate.name_en,
            birth_year=candidate.birth_year,
            nationality=candidate.nationality,
            entity_suffix=candidate.entity_suffix,
            match_status=candidate.match_status,
            matched_alias=candidate.matched_alias,
            match_basis=candidate.match_basis,
            artist_match_score=match_score,
            homonym_risk_score=homonym_risk,
            review_required=review_required,
            warm_available=warm_available,
            same_artist_training_price_count=count,
            route_recommendation=route,
            representative_artworks=self._representative_artist_samples(candidate.artist_key, max_samples=3),
        )

    def _representative_artist_samples(self, artist_key: str, max_samples: int = 3) -> list[RepresentativeArtwork]:
        if max_samples <= 0:
            return []
        source = self.v01.comparable_source[
            self.v01.comparable_source["artist_key"].astype(str).eq(str(artist_key))
        ].copy()
        if source.empty:
            return []
        source["price_krw"] = pd.to_numeric(source["price_krw"], errors="coerce")
        source = source.dropna(subset=["price_krw"]).sort_values("price_krw", ascending=False)
        samples: list[RepresentativeArtwork] = []
        seen: set[tuple[str, float | None, float | None, int | None]] = set()
        for _, row in source.iterrows():
            artist_name = str(row.get("artist_name_ko") or row.get("artist_key") or "")
            width = float(row["width_cm"]) if pd.notna(row.get("width_cm")) else None
            height = float(row["height_cm"]) if pd.notna(row.get("height_cm")) else None
            price = safe_price(row.get("price_krw"))
            artwork_id = str(row.get("source_artwork_id") or row.get("_track6_row_id") or "")
            title = self._title_for_identifier(artwork_id) or self._best_title_from_row(row) or "제목 정보 없음"
            signature = (title, width, height, price)
            if signature in seen:
                continue
            seen.add(signature)
            ho_size: int | None = None
            if width is not None and height is not None:
                ho_value = area_to_ho(width * height)
                ho_size = int(round(ho_value)) if ho_value > 0 else None
            samples.append(RepresentativeArtwork(
                artwork_id=artwork_id,
                title=title,
                artist_name=artist_name,
                sale_price_krw=price,
                width_cm=width,
                height_cm=height,
                medium_category=str(row.get("medium_category") or ""),
                support_category=str(row.get("support_category") or ""),
                ho_size=ho_size,
                ho_size_display=f"{ho_size}호" if ho_size else None,
            ))
            if len(samples) >= max_samples:
                break
        return samples

    def _estimate_warm(
        self,
        request_id: str,
        request: PriceEstimateRequest,
        selected: ResolvedArtist,
        input_quality: InputQuality,
        warnings: list[WarningItem],
    ) -> PriceEstimateResponse:
        v01_request = self._to_v01_request(request, selected.artist_key)
        v01_response = self.v01.estimate_price(request_id, v01_request)
        prediction = self._convert_prediction(v01_response.prediction, extra_reason="WARM_ROUTE_APPLIED", score=0.80)
        warnings.extend(WarningItem(**warning.model_dump()) for warning in v01_response.warnings)
        return PriceEstimateResponse(
            request_id=request_id,
            status="success",
            created_at=now_kst_iso(),
            model_version=MODEL_VERSION,
            prediction_id=prediction_id(),
            route="warm",
            display_policy="price_with_range",
            prediction=prediction,
            routing=Routing(
                artist_matched=True,
                matched_artist_key=selected.artist_key,
                artist_match_score=selected.artist_match_score,
                homonym_risk_score=selected.homonym_risk_score,
                same_artist_training_price_count=selected.same_artist_training_price_count,
                route_policy="artist_match_score>=0.90 AND same_artist_training_price_count>=5",
                route_reason="작가 매칭 신뢰도와 동일 작가 학습 가격 수가 Warm 기준을 충족했습니다.",
            ),
            basis=PredictionBasis(**v01_response.basis.model_dump()),
            market_price_card=MarketPriceCard(**v01_response.market_price_card.model_dump()),
            comparable_samples=(
                self._warm_reference_samples(v01_request, selected.artist_key, request.options.max_comparable_samples)
                if request.options.include_comparable_samples
                else []
            ),
            similar_artists=self._warm_similar_artists(selected.artist_key, max_artists=5),
            input_quality=input_quality,
            calculation_summary=self._warm_calculation_summary(),
            feedback=self._feedback_guide(),
            warnings=warnings,
        )

    def _estimate_cold(
        self,
        request_id: str,
        request: PriceEstimateRequest,
        selected: ResolvedArtist | None,
        input_quality: InputQuality,
        warnings: list[WarningItem],
    ) -> PriceEstimateResponse:
        frame = self._build_cold_feature_frame(request)
        out = self.cold_predictor.predict(frame, models=self.cold_models, guard=self.cold_guard)
        row = out.iloc[0]
        price = safe_price(row.get("defense_pred_price_krw"))
        low = safe_price(row.get("range_low_price_krw"))
        high = safe_price(row.get("range_high_price_krw"))
        if low is not None and high is not None and price is not None:
            low = min(low, price, high)
            high = max(low, price, high)

        qwidth = float(row.get("qwidth_log") or 0.0)
        guard_applied = abs(float(row["defense_pred_log"]) - float(row["representative_pred_log"])) > 1e-12
        confidence_level = "medium" if qwidth <= float(self.cold_guard["width_q67"]) else "low"
        confidence_score = 0.55 if confidence_level == "medium" else 0.35
        reason_codes = ["COLD_ROUTE_APPLIED", "SEARCH_FREE_COLD_MODEL"]
        if guard_applied:
            reason_codes.append("OVERPREDICTION_GUARD_APPLIED")
        if selected is None:
            reason_codes.append("ARTIST_NOT_IN_WARM_REGISTRY")
        warnings.append(WarningItem(
            code="COLD_REFERENCE_PRICE",
            message="Cold 경로는 작가 이력 기반 Warm보다 불확실성이 높아 참고 가격과 넓은 범위로 표시해야 합니다.",
        ))
        if guard_applied:
            warnings.append(WarningItem(
                code="OVERPREDICTION_GUARD_APPLIED",
                severity="info",
                message="예측 불확실성이 큰 구간이라 과대예측 방어 보정을 적용했습니다.",
            ))

        comparable_samples = (
            self._cold_reference_samples(frame.iloc[0], request.options.max_comparable_samples)
            if request.options.include_comparable_samples
            else []
        )

        return PriceEstimateResponse(
            request_id=request_id,
            status="partial_success",
            created_at=now_kst_iso(),
            model_version=MODEL_VERSION,
            prediction_id=prediction_id(),
            route="cold",
            display_policy="estimated_price_with_reference_warning",
            prediction=Prediction(
                price_krw=price,
                price_display=format_krw(price),
                range_krw=PriceRange(low=low, mid=price, high=high),
                range_display=self._range_display(low, high),
                confidence=Confidence(level=confidence_level, score=confidence_score, reason_codes=reason_codes),
            ),
            routing=Routing(
                artist_matched=selected is not None,
                matched_artist_key=selected.artist_key if selected else None,
                artist_match_score=selected.artist_match_score if selected else None,
                homonym_risk_score=selected.homonym_risk_score if selected else None,
                same_artist_training_price_count=selected.same_artist_training_price_count if selected else 0,
                route_policy="warm criteria failed AND minimum artwork input passed",
                route_reason="Warm 기준을 충족하지 못했지만 작품 크기/재료/지지체 최소 입력값이 있어 Cold 참고 가격을 계산했습니다.",
            ),
            basis=PredictionBasis(),
            market_price_card=self._cold_market_price_card(frame.iloc[0]),
            comparable_samples=comparable_samples,
            similar_artists=self._cold_similar_artists(frame.iloc[0], max_artists=5),
            input_quality=input_quality,
            calculation_summary=self._cold_calculation_summary(guard_applied),
            feedback=self._feedback_guide(),
            warnings=warnings,
        )

    def _review_required_response(
        self,
        request_id: str,
        request: PriceEstimateRequest,
        artist_resolution: ResolveArtistResponse,
        input_quality: InputQuality,
        warnings: list[WarningItem],
    ) -> PriceEstimateResponse:
        selected = artist_resolution.selected_artist
        return PriceEstimateResponse(
            request_id=request_id,
            status="partial_success",
            created_at=now_kst_iso(),
            model_version=MODEL_VERSION,
            prediction_id=prediction_id(),
            route="review_required",
            display_policy="no_single_price",
            prediction=Prediction(
                price_krw=None,
                price_display=None,
                range_krw=PriceRange(),
                range_display=None,
                confidence=Confidence(level="low", score=0.0, reason_codes=[warning.code for warning in warnings]),
            ),
            routing=Routing(
                artist_matched=selected is not None,
                matched_artist_key=selected.artist_key if selected else None,
                artist_match_score=selected.artist_match_score if selected else None,
                homonym_risk_score=selected.homonym_risk_score if selected else None,
                same_artist_training_price_count=selected.same_artist_training_price_count if selected else None,
                route_policy="ambiguous artist OR minimum input failed",
                route_reason="작가 확정 또는 최소 입력값 조건이 부족하여 단일 가격을 표시하지 않습니다.",
            ),
            basis=PredictionBasis(),
            market_price_card=MarketPriceCard(
                median_display="-",
                range_krw_per_ho=RangePerHo(),
                range_display="-",
                medium_distribution=[],
                sample_count=0,
                sample_count_display="표본 수 N=0건",
            ),
            comparable_samples=[],
            input_quality=input_quality,
            calculation_summary=self._review_calculation_summary(),
            feedback=self._feedback_guide(),
            warnings=warnings,
        )

    def _to_v01_request(self, request: PriceEstimateRequest, artist_key: str) -> v01s.PriceEstimateRequest:
        artwork = request.artwork.model_copy(deep=True)
        artwork.artist.artist_key = artist_key
        return v01s.PriceEstimateRequest(
            artwork=artwork,
            options=v01s.PriceEstimateOptions(
                currency=request.options.currency,
                include_comparable_samples=request.options.include_comparable_samples,
                max_comparable_samples=request.options.max_comparable_samples,
            ),
        )

    def _build_cold_feature_frame(self, request: PriceEstimateRequest) -> pd.DataFrame:
        artwork = request.artwork
        width = float(artwork.dimensions.width_cm or 0.0)
        height = float(artwork.dimensions.height_cm or 0.0)
        depth = float(artwork.dimensions.depth_cm or 0.0)
        area = dimension_area(width, height)
        aspect = max(width, height) / min(width, height) if min(width, height) > 0 else np.nan
        base = pd.DataFrame([{
            "_v02_row_id": 0,
            "width_cm": width,
            "height_cm": height,
            "depth_cm": depth,
            "area_cm2": area,
            "log_area": np.log(area) if area > 0 else np.nan,
            "aspect_ratio": aspect,
            "has_depth": bool(depth > 0),
            "is_3d_candidate": bool(depth > 0 or str(artwork.category or "").lower() in {"sculpture", "installation"}),
            "medium_category": artwork.medium.medium_category,
            "support_category": artwork.medium.support_category,
        }])
        frame = feature_ops.add_bucket_features(base, self.v01.feature_generation, "cold")
        return frame

    @staticmethod
    def _cold_v03_split(split: str) -> str:
        normalized = str(split or "test").strip().lower()
        if normalized not in {"test", "validation"}:
            raise ValueError("split must be one of: test, validation")
        return normalized

    def _cold_v03_policy_info(self) -> dict[str, Any]:
        if self._cold_v03_policy is None:
            path = self.cold_v03_bundle_root / "config" / "cold_model_policy_v0_3.json"
            self._cold_v03_policy = json.loads(path.read_text(encoding="utf-8"))
        return self._cold_v03_policy

    def _cold_v03_params_info(self) -> dict[str, Any]:
        if self._cold_v03_params is None:
            path = self.cold_v03_bundle_root / "config" / "cold_postprocess_params_v0_3.json"
            self._cold_v03_params = json.loads(path.read_text(encoding="utf-8"))
        return self._cold_v03_params

    def _cold_v03_lookup_info(self) -> dict[str, float]:
        if self._cold_v03_lookup is None:
            path = self.cold_v03_bundle_root / "config" / "search_delta_lookup_v0_3.json"
            raw = json.loads(path.read_text(encoding="utf-8"))
            self._cold_v03_lookup = {str(key): float(value) for key, value in raw["artist_delta"].items()}
        return self._cold_v03_lookup

    def _cold_v03_postprocess_module(self) -> Any:
        if self._cold_v03_postprocessor is None:
            self._cold_v03_postprocessor = _load_module(
                self.cold_v03_bundle_root / "predict" / "apply_cold_postprocess_v0_3.py",
                "apply_cold_postprocess_v0_3_runtime",
            )
        return self._cold_v03_postprocessor

    @staticmethod
    def _cold_v03_read_candidate(path: Path, candidate: str, pred_col: str) -> pd.DataFrame:
        raw = pd.read_csv(path, low_memory=False)
        part = raw[raw["candidate"].eq(candidate)].copy()
        if part.empty:
            raise ValueError(f"missing v0.3 candidate {candidate}: {path}")
        return part[["split", "_track6_row_id", "pred_log"]].rename(columns={"pred_log": pred_col})

    def _cold_v03_replay_frame(self) -> pd.DataFrame:
        if self._cold_v03_frame is not None:
            return self._cold_v03_frame

        y18_path = REPO / "experiments" / "track6" / "PP-Y18_cold_y16_top_candidate_stability" / "outputs" / "predictions.csv"
        y2_path = REPO / "experiments" / "track6" / "PP-Y2_cold_lgbq_search_external_combo" / "outputs" / "predictions.csv"
        qr1_path = REPO / "experiments" / "track6" / "PP-QR1_cold_quantile_regression_alpha_grid" / "outputs" / "predictions.csv"
        h28_path = REPO / "experiments" / "track6" / "PP-H20_H26_search_feature_expansion" / "outputs" / "candidate_predictions.csv"

        y18_raw = pd.read_csv(y18_path, low_memory=False)
        y18 = y18_raw[y18_raw["candidate"].eq(COLD_V03_Y18_CANDIDATE)].copy()
        if y18.empty:
            raise ValueError(f"missing v0.3 representative candidate: {COLD_V03_Y18_CANDIDATE}")
        frame = y18[
            [
                "split",
                "_track6_row_id",
                "actual_log",
                "actual_price",
                "quantile_width_log",
                "price_range_ratio",
                "artist_key",
                "pred_log",
            ]
        ].rename(columns={"pred_log": "y18_qwidth_pred_log"})

        if frame["quantile_width_log"].isna().all():
            y2_raw = pd.read_csv(y2_path, low_memory=False)
            y2 = y2_raw[y2_raw["candidate"].eq(COLD_V03_Y2_QWIDTH_CANDIDATE)].copy()
            if y2.empty:
                raise ValueError(f"missing v0.3 qwidth candidate: {COLD_V03_Y2_QWIDTH_CANDIDATE}")
            y2 = y2[["split", "_track6_row_id", "quantile_width_log", "price_range_ratio"]].rename(
                columns={
                    "quantile_width_log": "y2_quantile_width_log",
                    "price_range_ratio": "y2_price_range_ratio",
                }
            )
            frame = frame.merge(y2, on=["split", "_track6_row_id"], how="left")
            frame["quantile_width_log"] = frame["quantile_width_log"].fillna(frame["y2_quantile_width_log"])
            frame["price_range_ratio"] = frame["price_range_ratio"].fillna(frame["y2_price_range_ratio"])
            frame = frame.drop(columns=["y2_quantile_width_log", "y2_price_range_ratio"])

        if frame["quantile_width_log"].isna().any() and frame["price_range_ratio"].notna().any():
            frame["quantile_width_log"] = frame["quantile_width_log"].fillna(
                np.log(pd.to_numeric(frame["price_range_ratio"], errors="coerce").clip(lower=1.0))
            )
        if frame["price_range_ratio"].isna().any() and frame["quantile_width_log"].notna().any():
            frame["price_range_ratio"] = frame["price_range_ratio"].fillna(
                np.exp(pd.to_numeric(frame["quantile_width_log"], errors="coerce").clip(lower=0.0, upper=8.0))
            )

        frame = frame.merge(
            self._cold_v03_read_candidate(qr1_path, COLD_V03_CAT_Q40_CANDIDATE, "cat_q40_pred_log"),
            on=["split", "_track6_row_id"],
            how="inner",
        )
        frame = frame.merge(
            self._cold_v03_read_candidate(qr1_path, COLD_V03_LGB_Q40_CANDIDATE, "lgb_q40_pred_log"),
            on=["split", "_track6_row_id"],
            how="inner",
        )

        h28 = pd.read_csv(h28_path, low_memory=False)
        h28_source_col = f"{COLD_V03_SEARCH_SOURCE}__pred_log"
        required = ["split", "_track6_row_id", "artist_search_name", "recommended_action", "qwidth_bin", "pred_log", h28_source_col]
        missing = [col for col in required if col not in h28.columns]
        if missing:
            raise ValueError(f"missing v0.3 search columns: {missing}")
        h28 = h28[required].rename(
            columns={
                "pred_log": "search_shared_base_pred_log",
                h28_source_col: "search_source_pred_log",
            }
        )
        frame = frame.merge(h28, on=["split", "_track6_row_id"], how="inner")
        frame["search_delta_from_source"] = frame["search_source_pred_log"] - frame["search_shared_base_pred_log"]

        params = self._cold_v03_params_info()
        lookup = self._cold_v03_lookup_info()
        postprocessor = self._cold_v03_postprocess_module()
        out = postprocessor.apply(frame, params=params, lookup=lookup)
        guard_log = postprocessor.guard_pred_log(
            out["y18_qwidth_pred_log"].to_numpy(dtype=float),
            out["lgb_q40_pred_log"].to_numpy(dtype=float),
            out["quantile_width_log"].to_numpy(dtype=float),
            params,
        )
        out["cold_v03_guard_only_pred_log"] = guard_log
        out["cold_v03_guard_only_pred_price_krw"] = np.clip(np.exp(guard_log), 1_000.0, None)
        out["cold_v03_guard_applied"] = np.abs(guard_log - out["y18_qwidth_pred_log"].to_numpy(dtype=float)) > 1e-12
        actual_price = pd.to_numeric(out["actual_price"], errors="coerce").clip(lower=1.0)
        final_price = pd.to_numeric(out["cold_defense_pred_price_krw"], errors="coerce")
        out["cold_v03_final_ape"] = (final_price - actual_price).abs() / actual_price
        out["cold_v03_guard_ape"] = (
            pd.to_numeric(out["cold_v03_guard_only_pred_price_krw"], errors="coerce") - actual_price
        ).abs() / actual_price
        out["cold_v03_representative_ape"] = (
            pd.to_numeric(out["cold_representative_pred_price_krw"], errors="coerce") - actual_price
        ).abs() / actual_price
        self._cold_v03_frame = out.sort_values(["split", "_track6_row_id"]).reset_index(drop=True)
        return self._cold_v03_frame

    @staticmethod
    def _cold_v03_metrics(policy: dict[str, Any]) -> dict[str, Any]:
        defense = policy.get("defense_policy", {})
        representative = policy.get("representative_policy", {})
        return {
            "fixed_test_rows": 3099,
            "representative_test": representative.get("metrics_test", {}),
            "guard_only_test": defense.get("guard_only_metrics_test", {}),
            "guard_search_test": defense.get("metrics_test", {}),
            "search_coverage_test": defense.get("search_coverage_test"),
            "review_rate_test": policy.get("review_flag_policy", {}).get("review_rate_test"),
        }

    @staticmethod
    def _cold_v03_price_dict(row: pd.Series, log_col: str, price_col: str, ape_col: str | None = None) -> dict[str, Any]:
        price = safe_price(row.get(price_col))
        out: dict[str, Any] = {
            "log_price": float(row[log_col]) if pd.notna(row.get(log_col)) else None,
            "price_krw": price,
            "price_display": format_krw(price),
        }
        if ape_col:
            ape = row.get(ape_col)
            out["ape"] = float(ape) if pd.notna(ape) else None
        return out

    def _cold_v03_row_summary(self, row: pd.Series) -> dict[str, Any]:
        row_id = int(row["_track6_row_id"])
        artist_key = str(row.get("artist_key") or "")
        return {
            "row_id": row_id,
            "split": str(row.get("split") or ""),
            "artist_key": artist_key,
            "artist_search_name": str(row.get("artist_search_name") or ""),
            "actual_price_krw": safe_price(row.get("actual_price")),
            "actual_price_display": format_krw(safe_price(row.get("actual_price"))),
            "final_price_krw": safe_price(row.get("cold_defense_pred_price_krw")),
            "final_price_display": format_krw(safe_price(row.get("cold_defense_pred_price_krw"))),
            "final_ape": float(row.get("cold_v03_final_ape") or 0.0),
            "representative_price_display": format_krw(safe_price(row.get("cold_representative_pred_price_krw"))),
            "guard_only_price_display": format_krw(safe_price(row.get("cold_v03_guard_only_pred_price_krw"))),
            "quantile_width_log": float(row.get("quantile_width_log") or 0.0),
            "price_range_ratio": float(row.get("price_range_ratio") or 0.0),
            "guard_applied": bool(row.get("cold_v03_guard_applied")),
            "search_covered": bool(row.get("search_covered")),
            "search_delta_log": float(row.get("search_delta_applied") or 0.0),
            "review_flag": bool(row.get("cold_review_flag")),
            "confidence_tier": str(row.get("cold_confidence_tier") or ""),
        }

    def _cold_v03_row_detail(self, row: pd.Series) -> dict[str, Any]:
        detail = self._cold_v03_row_summary(row)
        detail.update({
            "actual": {
                "log_price": float(row["actual_log"]),
                "price_krw": safe_price(row.get("actual_price")),
                "price_display": format_krw(safe_price(row.get("actual_price"))),
            },
            "representative": self._cold_v03_price_dict(
                row,
                "cold_representative_pred_log",
                "cold_representative_pred_price_krw",
                "cold_v03_representative_ape",
            ),
            "lightgbm_q40": {
                "log_price": float(row["lgb_q40_pred_log"]),
                "price_krw": safe_price(math.exp(float(row["lgb_q40_pred_log"]))),
                "price_display": format_krw(safe_price(math.exp(float(row["lgb_q40_pred_log"])))),
            },
            "catboost_q40": {
                "log_price": float(row["cat_q40_pred_log"]),
                "price_krw": safe_price(math.exp(float(row["cat_q40_pred_log"]))),
                "price_display": format_krw(safe_price(math.exp(float(row["cat_q40_pred_log"])))),
            },
            "guard_only": self._cold_v03_price_dict(
                row,
                "cold_v03_guard_only_pred_log",
                "cold_v03_guard_only_pred_price_krw",
                "cold_v03_guard_ape",
            ),
            "guard_search_final": self._cold_v03_price_dict(
                row,
                "cold_defense_pred_log",
                "cold_defense_pred_price_krw",
                "cold_v03_final_ape",
            ),
            "search": {
                "source": COLD_V03_SEARCH_SOURCE,
                "artist_search_name": str(row.get("artist_search_name") or ""),
                "shared_base_log": float(row.get("search_shared_base_pred_log") or 0.0),
                "source_log": float(row.get("search_source_pred_log") or 0.0),
                "delta_from_source_log": float(row.get("search_delta_from_source") or 0.0),
                "delta_applied_log": float(row.get("search_delta_applied") or 0.0),
                "covered": bool(row.get("search_covered")),
                "recommended_action": str(row.get("recommended_action") or ""),
                "qwidth_bin": str(row.get("qwidth_bin") or ""),
            },
        })
        return detail

    def _load_title_lookup(self) -> dict[str, str]:
        paths = [
            self.v01.model_root / "data" / "training" / "track6_split" / "track6_train_title_lookup_complete.csv",
            REPO / "data" / "track6_split" / "track6_train_title_lookup_complete.csv",
        ]
        path = next((candidate for candidate in paths if candidate.exists()), None)
        if path is None:
            return {}

        usecols = ["_track6_row_id", "title_resolved", "title_raw", "title_url_slug", "source_artwork_id"]
        lookup_frame = pd.read_csv(path, usecols=usecols)
        lookup: dict[str, str] = {}
        for _, row in lookup_frame.iterrows():
            title = self._best_title_from_row(row)
            if not title:
                continue
            row_id = row.get("_track6_row_id")
            source_id = row.get("source_artwork_id")
            if pd.notna(row_id):
                lookup[str(int(row_id))] = title
                lookup[str(row_id)] = title
            if pd.notna(source_id) and str(source_id).strip():
                lookup[str(source_id).strip()] = title
        return lookup

    @staticmethod
    def _clean_title_value(value: object, from_slug: bool = False) -> str | None:
        if value is None or pd.isna(value):
            return None
        text = str(value).strip()
        if not text or text.lower() in {"nan", "none", "null"}:
            return None
        if from_slug:
            text = text.rsplit("/", 1)[-1]
            text = text.replace("_", " ").replace("-", " ").strip()
            text = text.removeprefix("Painting ").removeprefix("painting ").strip()
        return text or None

    @classmethod
    def _best_title_from_row(cls, row: pd.Series) -> str | None:
        for column, from_slug in [
            ("title_resolved", False),
            ("title_raw", False),
            ("title_url_slug", True),
        ]:
            title = cls._clean_title_value(row.get(column), from_slug=from_slug)
            if title:
                return title
        return None

    def _title_for_identifier(self, identifier: object) -> str | None:
        if identifier is None or pd.isna(identifier):
            return None
        text = str(identifier).strip()
        if not text:
            return None
        if text in self.title_lookup:
            return self.title_lookup[text]
        try:
            numeric_key = str(int(float(text)))
        except (TypeError, ValueError):
            numeric_key = text
        return self.title_lookup.get(numeric_key)

    def _normalize_sample_title(self, sample: v01s.ComparableSample | ComparableSample) -> ComparableSample:
        data = sample.model_dump()
        title = str(data.get("title") or "").strip()
        data["title"] = title or self._title_for_identifier(data.get("artwork_id")) or "제목 정보 없음"
        return ComparableSample(**data)

    @staticmethod
    def _reference_similarity_reason(scope: str, match_score: int) -> str:
        if match_score >= 3:
            return f"{scope}_material_support_area_reference"
        if match_score == 2:
            return f"{scope}_material_area_reference"
        if match_score == 1:
            return f"{scope}_support_area_reference"
        return f"{scope}_area_reference"

    def _warm_reference_samples(
        self,
        request: v01s.PriceEstimateRequest,
        artist_key: str,
        max_samples: int,
    ) -> list[ComparableSample]:
        if max_samples <= 0:
            return []
        source = self.v01.comparable_source[
            self.v01.comparable_source["artist_key"].astype(str).eq(str(artist_key))
        ].copy()
        if source.empty:
            return []

        feature_row = self.v01._build_feature_frame(request, artist_key).iloc[0]
        target_area = float(feature_row.get("area_cm2", 0) or 0)
        target_medium = str(feature_row.get("medium_category") or "")
        target_support = str(feature_row.get("support_category") or "")
        policy = REFERENCE_SAMPLE_POLICY["warm"]
        source["_area_diff"] = (pd.to_numeric(source["area_cm2"], errors="coerce") - target_area).abs()
        source["_medium_match"] = source["medium_category"].astype(str).eq(target_medium).astype(int)
        source["_support_match"] = source["support_category"].astype(str).eq(target_support).astype(int)
        source["_match_score"] = (
            policy["medium_match_weight"] * source["_medium_match"]
            + policy["support_match_weight"] * source["_support_match"]
        )
        source = source.sort_values(
            ["_match_score", "_area_diff", "price_krw"],
            ascending=[False, True, False],
        )

        samples: list[ComparableSample] = []
        seen_signatures: set[tuple[str, float | None, float | None, int | None]] = set()
        for _, row in source.iterrows():
            artist_name = str(row.get("artist_name_ko") or row.get("artist_key") or "")
            width = float(row["width_cm"]) if pd.notna(row.get("width_cm")) else None
            height = float(row["height_cm"]) if pd.notna(row.get("height_cm")) else None
            price = safe_price(row.get("price_krw"))
            signature = (artist_name, width, height, price)
            if signature in seen_signatures:
                continue
            seen_signatures.add(signature)
            artwork_id = str(row.get("source_artwork_id") or row.get("_track6_row_id") or "")
            reason = self._reference_similarity_reason("same_artist", int(row.get("_match_score") or 0))
            samples.append(ComparableSample(
                artwork_id=artwork_id,
                title=self._title_for_identifier(artwork_id) or self._best_title_from_row(row) or "제목 정보 없음",
                artist_name=artist_name,
                sale_price_krw=price,
                width_cm=width,
                height_cm=height,
                medium_category=str(row.get("medium_category") or ""),
                support_category=str(row.get("support_category") or ""),
                similarity_reason=reason,
            ))
            if len(samples) >= max_samples:
                break
        return samples

    def _cold_reference_samples(self, feature_row: pd.Series, max_samples: int) -> list[ComparableSample]:
        if max_samples <= 0:
            return []
        source = self.v01.comparable_source.copy()
        if source.empty:
            return []

        target_area = float(feature_row.get("area_cm2", 0) or 0)
        target_medium = str(feature_row.get("medium_category") or "")
        target_support = str(feature_row.get("support_category") or "")
        policy = REFERENCE_SAMPLE_POLICY["cold"]
        source["_area_diff"] = (pd.to_numeric(source["area_cm2"], errors="coerce") - target_area).abs()
        source["_medium_match"] = source["medium_category"].astype(str).eq(target_medium).astype(int)
        source["_support_match"] = source["support_category"].astype(str).eq(target_support).astype(int)
        source["_match_score"] = (
            policy["medium_match_weight"] * source["_medium_match"]
            + policy["support_match_weight"] * source["_support_match"]
        )
        source = source.sort_values(
            ["_match_score", "_area_diff", "price_krw"],
            ascending=[False, True, False],
        )

        samples: list[ComparableSample] = []
        artist_counts: dict[str, int] = {}
        seen_signatures: set[tuple[str, float | None, float | None, int | None]] = set()
        for _, row in source.iterrows():
            artist_name = str(row.get("artist_name_ko") or row.get("artist_key") or "")
            width = float(row["width_cm"]) if pd.notna(row.get("width_cm")) else None
            height = float(row["height_cm"]) if pd.notna(row.get("height_cm")) else None
            price = safe_price(row.get("price_krw"))
            signature = (artist_name, width, height, price)
            if signature in seen_signatures:
                continue
            if artist_counts.get(artist_name, 0) >= policy["max_per_artist"]:
                continue
            seen_signatures.add(signature)
            artist_counts[artist_name] = artist_counts.get(artist_name, 0) + 1
            artwork_id = str(row.get("source_artwork_id") or row.get("_track6_row_id") or "")
            samples.append(ComparableSample(
                artwork_id=artwork_id,
                title=self._title_for_identifier(artwork_id) or self._best_title_from_row(row) or "제목 정보 없음",
                artist_name=artist_name,
                sale_price_krw=price,
                width_cm=width,
                height_cm=height,
                medium_category=str(row.get("medium_category") or ""),
                support_category=str(row.get("support_category") or ""),
                similarity_reason=self._reference_similarity_reason("cross_artist", int(row.get("_match_score") or 0)),
            ))
            if len(samples) >= max_samples:
                break
        return samples

    def _load_artist_meta_lookup(self) -> dict[str, dict[str, Any]]:
        path = REPO / "data" / "track6_split" / "track6_train.csv"
        if not path.exists():
            return {}
        columns = [
            "artist_key",
            "artist_meta_birth_year",
            "artist_meta_nationality_ko",
            "artist_meta_nationality",
            "artist_meta_career_stage",
            "artist_meta_is_p1",
            "artist_meta_has_international",
        ]
        available_columns = pd.read_csv(path, nrows=0).columns
        frame = pd.read_csv(path, usecols=[col for col in columns if col in available_columns], low_memory=False)
        lookup: dict[str, dict[str, Any]] = {}
        for artist_key, group in frame.groupby("artist_key", dropna=False):
            key = str(artist_key)
            if not key or key == "nan":
                continue
            row: dict[str, Any] = {}
            for col in columns[1:]:
                if col not in group.columns:
                    continue
                values = group[col].dropna()
                row[col] = values.iloc[0] if not values.empty else None
            lookup[key] = row
        return lookup

    @staticmethod
    def _mode_or_empty(series: pd.Series) -> str:
        values = series.astype("string").fillna("")
        values = values[values.str.len() > 0]
        if values.empty:
            return ""
        return str(values.mode().iloc[0])

    @staticmethod
    def _birth_decade(value: object) -> str:
        numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
        if pd.isna(numeric):
            return ""
        year = int(numeric)
        if year < 1200 or year > 2026:
            return ""
        return f"{year // 10 * 10}s"

    def _build_artist_reference_profiles(self) -> pd.DataFrame:
        source = self.v01.comparable_source.copy()
        if source.empty:
            return pd.DataFrame()
        source["price_krw"] = pd.to_numeric(source["price_krw"], errors="coerce")
        source["area_cm2"] = pd.to_numeric(source["area_cm2"], errors="coerce")
        source = source.dropna(subset=["artist_key", "price_krw", "area_cm2"])
        source = source[(source["price_krw"] > 0) & (source["area_cm2"] > 0)].copy()
        source["_log_price"] = np.log(source["price_krw"])
        source["_log_area"] = np.log(source["area_cm2"])
        source["_log_unit_area"] = source["_log_price"] - source["_log_area"]
        grouped = source.groupby("artist_key", dropna=False, observed=False)
        profiles = grouped.agg(
            name_ko=("artist_name_ko", self._mode_or_empty),
            price_history_count=("price_krw", "size"),
            median_price_krw=("price_krw", "median"),
            log_price_median=("_log_price", "median"),
            log_unit_area_median=("_log_unit_area", "median"),
            log_area_median=("_log_area", "median"),
            primary_medium=("medium_category", self._mode_or_empty),
            primary_support=("support_category", self._mode_or_empty),
        ).reset_index()
        profiles["artist_key"] = profiles["artist_key"].astype(str)
        profiles["price_history_count_log"] = np.log1p(pd.to_numeric(profiles["price_history_count"], errors="coerce").fillna(0))
        meta_rows = []
        for artist_key in profiles["artist_key"]:
            meta = self.artist_meta_lookup.get(str(artist_key), {})
            birth_year = meta.get("artist_meta_birth_year")
            nationality = meta.get("artist_meta_nationality_ko") or meta.get("artist_meta_nationality")
            meta_rows.append({
                "artist_key": artist_key,
                "birth_year": safe_int(birth_year),
                "birth_decade": self._birth_decade(birth_year),
                "nationality": "" if nationality is None or pd.isna(nationality) else str(nationality),
                "career_stage": "" if meta.get("artist_meta_career_stage") is None else str(meta.get("artist_meta_career_stage")),
                "is_p1": "" if meta.get("artist_meta_is_p1") is None else str(meta.get("artist_meta_is_p1")),
                "has_international": "" if meta.get("artist_meta_has_international") is None else str(meta.get("artist_meta_has_international")),
            })
        meta_frame = pd.DataFrame(meta_rows)
        profiles = profiles.merge(meta_frame, on="artist_key", how="left")
        try:
            profiles["artist_market_tier"] = pd.qcut(
                profiles["log_price_median"].rank(method="first"),
                q=5,
                labels=["낮은 가격대", "중저가", "중간 가격대", "중고가", "높은 가격대"],
            ).astype(str)
        except ValueError:
            profiles["artist_market_tier"] = "가격대 미분류"
        return profiles

    def _profile_for_artist(self, artist_key: str) -> dict[str, Any] | None:
        profiles = self.artist_reference_profiles
        if profiles.empty:
            return None
        hit = profiles[profiles["artist_key"].astype(str).eq(str(artist_key))]
        if hit.empty:
            return None
        return hit.iloc[0].to_dict()

    def _target_profile_from_feature_row(self, feature_row: pd.Series) -> dict[str, Any]:
        area = float(feature_row.get("area_cm2", 0) or 0)
        return {
            "artist_key": "",
            "name_ko": "",
            "price_history_count": 0,
            "log_price_median": np.nan,
            "log_unit_area_median": np.nan,
            "log_area_median": np.log(area) if area > 0 else np.nan,
            "primary_medium": str(feature_row.get("medium_category") or ""),
            "primary_support": str(feature_row.get("support_category") or ""),
            "birth_decade": "",
            "nationality": "",
            "career_stage": "",
            "artist_market_tier": "",
            "is_p1": "",
            "has_international": "",
        }

    def _similarity_reasons(self, target: dict[str, Any], candidate: pd.Series) -> list[str]:
        reasons: list[str] = []
        if str(candidate.get("primary_medium") or "") and str(candidate.get("primary_medium") or "") == str(target.get("primary_medium") or ""):
            reasons.append("주 사용 재료 일치")
        if str(candidate.get("primary_support") or "") and str(candidate.get("primary_support") or "") == str(target.get("primary_support") or ""):
            reasons.append("주 사용 지지체 일치")
        if str(candidate.get("birth_decade") or "") and str(candidate.get("birth_decade") or "") == str(target.get("birth_decade") or ""):
            reasons.append("생년대 유사")
        if str(candidate.get("nationality") or "") and str(candidate.get("nationality") or "") == str(target.get("nationality") or ""):
            reasons.append("국적 유사")
        if str(candidate.get("artist_market_tier") or "") and str(candidate.get("artist_market_tier") or "") == str(target.get("artist_market_tier") or ""):
            reasons.append("가격대 유사")
        if not reasons:
            reasons.append("가격 이력과 작품 조건 기반 근접")
        return reasons[:4]

    def _similar_artist_references(
        self,
        target: dict[str, Any],
        max_artists: int,
        basis: str,
    ) -> list[SimilarArtistReference]:
        profiles = self.artist_reference_profiles.copy()
        if profiles.empty:
            return []
        profiles = profiles[pd.to_numeric(profiles["price_history_count"], errors="coerce").fillna(0) >= 5].copy()
        target_artist_key = str(target.get("artist_key") or "")
        if target_artist_key:
            profiles = profiles[~profiles["artist_key"].astype(str).eq(target_artist_key)].copy()
        if profiles.empty:
            return []

        numeric_cols = ["log_price_median", "log_unit_area_median", "log_area_median", "price_history_count_log"]
        available = [
            col for col in numeric_cols
            if col in profiles.columns and pd.notna(pd.to_numeric(pd.Series([target.get(col)]), errors="coerce").iloc[0])
        ]
        if available:
            values = profiles[available].apply(pd.to_numeric, errors="coerce")
            mean = values.mean()
            std = values.std().replace(0, 1.0).fillna(1.0)
            target_values = pd.Series({col: float(target[col]) for col in available})
            numeric_distance = ((values.fillna(mean) - target_values) / std).pow(2).mean(axis=1).pow(0.5)
            numeric_score = 1.0 / (1.0 + numeric_distance)
        else:
            numeric_score = pd.Series(0.5, index=profiles.index)

        cat_score = pd.Series(0.0, index=profiles.index)
        cat_weight = 0.0
        for col, weight in [
            ("birth_decade", 0.20),
            ("nationality", 0.18),
            ("career_stage", 0.16),
            ("artist_market_tier", 0.14),
            ("primary_medium", 0.16),
            ("primary_support", 0.10),
            ("is_p1", 0.04),
            ("has_international", 0.02),
        ]:
            target_value = str(target.get(col) or "")
            if not target_value:
                continue
            cat_score += weight * profiles[col].astype(str).eq(target_value).astype(float)
            cat_weight += weight
        cat_score = cat_score / cat_weight if cat_weight > 0 else pd.Series(0.5, index=profiles.index)
        history_available = pd.notna(pd.to_numeric(pd.Series([target.get("log_price_median")]), errors="coerce").iloc[0])
        profiles["_similarity_score"] = (
            0.55 * numeric_score + 0.45 * cat_score
            if history_available
            else 0.30 * numeric_score + 0.70 * cat_score
        )
        profiles = profiles.sort_values(["_similarity_score", "price_history_count"], ascending=[False, False])
        selected = profiles[profiles["_similarity_score"] >= 0.45].head(max_artists)
        if selected.empty:
            selected = profiles.head(max_artists)
        references: list[SimilarArtistReference] = []
        for _, row in selected.iterrows():
            references.append(SimilarArtistReference(
                artist_key=str(row.get("artist_key") or ""),
                name_ko=str(row.get("name_ko") or ""),
                birth_year=safe_int(row.get("birth_year")),
                nationality=str(row.get("nationality") or "") or None,
                similarity_score=float(min(max(row.get("_similarity_score", 0.0), 0.0), 1.0)),
                price_history_count=int(row.get("price_history_count") or 0),
                primary_medium=str(row.get("primary_medium") or "") or None,
                primary_support=str(row.get("primary_support") or "") or None,
                median_price_display=format_krw(safe_price(row.get("median_price_krw"))),
                similarity_basis=basis,
                match_reasons=self._similarity_reasons(target, row),
            ))
        return references

    def _warm_similar_artists(self, artist_key: str, max_artists: int) -> list[SimilarArtistReference]:
        target = self._profile_for_artist(artist_key)
        if target is None:
            return []
        return self._similar_artist_references(target, max_artists=max_artists, basis="동일 작가 이력의 가격대, 주 재료, 지지체, 크기 중심과 가까운 작가")

    def _cold_similar_artists(self, feature_row: pd.Series, max_artists: int) -> list[SimilarArtistReference]:
        target = self._target_profile_from_feature_row(feature_row)
        return self._similar_artist_references(target, max_artists=max_artists, basis="입력 작품의 재료, 지지체, 크기와 가까운 이력 보유 작가")

    def _cold_market_price_card(self, feature_row: pd.Series) -> MarketPriceCard:
        source = self.v01.comparable_source.copy()
        target_area = float(feature_row.get("area_cm2", 0) or 0)
        target_medium = str(feature_row.get("medium_category") or "")
        target_support = str(feature_row.get("support_category") or "")
        source["_area_diff"] = (pd.to_numeric(source["area_cm2"], errors="coerce") - target_area).abs()
        source["_medium_match"] = source["medium_category"].astype(str).eq(target_medium)
        source["_support_match"] = source["support_category"].astype(str).eq(target_support)
        filtered = source[source["_medium_match"] & source["_support_match"]].copy()
        if len(filtered) < 20:
            filtered = source[source["_medium_match"]].copy()
        if len(filtered) < 20:
            filtered = source.copy()
        filtered = filtered.sort_values("_area_diff").head(80).copy()
        ho = max(area_to_ho(target_area), 1)
        unit = pd.to_numeric(filtered["price_krw"], errors="coerce") / ho
        unit = unit.replace([np.inf, -np.inf], np.nan).dropna()
        if unit.empty:
            return MarketPriceCard(
                title="조건 기반 1차 시장 참고 가격",
                median_display="-",
                range_krw_per_ho=RangePerHo(),
                range_display="-",
                medium_distribution=[],
                sample_count=0,
                sample_count_display="조건 기반 표본 수 N=0건",
            )
        median = safe_price(unit.median())
        q25 = safe_price(unit.quantile(0.25))
        q75 = safe_price(unit.quantile(0.75))
        distribution: list[MediumDistribution] = []
        for medium, group in filtered.groupby("medium_category", observed=False):
            group_unit = pd.to_numeric(group["price_krw"], errors="coerce") / ho
            group_median = safe_price(group_unit.median())
            distribution.append(MediumDistribution(
                label=str(medium),
                medium_group=str(medium),
                median_krw_per_ho=group_median,
                display=format_krw(group_median) or "-",
                sample_count=int(len(group)),
            ))
        distribution.sort(key=lambda item: item.sample_count, reverse=True)
        return MarketPriceCard(
            title="조건 기반 1차 시장 참고 가격",
            metric_label="조건 유사 작품 호당가 중앙값",
            median_krw_per_ho=median,
            median_display=format_krw_per_ho(median),
            range_krw_per_ho=RangePerHo(low=q25, high=q75),
            range_display=f"{format_krw_per_ho(q25)} - {format_krw_per_ho(q75)}",
            medium_distribution=distribution[:4],
            sample_count=int(len(filtered)),
            sample_count_display=f"조건 기반 표본 수 N={len(filtered):,}건",
        )

    def _input_quality(self, request: PriceEstimateRequest) -> InputQuality:
        artwork = request.artwork
        required: list[str] = []
        recommended: list[str] = []
        if not (artwork.artist.artist_key or artwork.artist.name_ko or artwork.artist.name_en):
            required.append("artist.name_ko 또는 artist.name_en")
        if artwork.dimensions.width_cm is None:
            required.append("dimensions.width_cm")
        if artwork.dimensions.height_cm is None:
            required.append("dimensions.height_cm")
        if not artwork.medium.medium_category:
            required.append("medium.medium_category")
        if not artwork.medium.support_category:
            required.append("medium.support_category")
        if artwork.year is None:
            recommended.append("year")
        if artwork.title is None:
            recommended.append("title")
        return InputQuality(
            minimum_input_status="passed" if not required else "failed",
            missing_required_fields=required,
            missing_recommended_fields=recommended,
            confidence_penalty_reasons=["MISSING_RECOMMENDED_FIELDS"] if recommended else [],
        )

    @staticmethod
    def _convert_prediction(v01_prediction: v01s.Prediction, extra_reason: str, score: float) -> Prediction:
        reasons = list(v01_prediction.confidence.reason_codes)
        if extra_reason not in reasons:
            reasons.append(extra_reason)
        return Prediction(
            price_krw=v01_prediction.price_krw,
            price_display=v01_prediction.price_display,
            range_krw=PriceRange(**v01_prediction.range_krw.model_dump()),
            range_display=v01_prediction.range_display,
            confidence=Confidence(level=v01_prediction.confidence.level, score=score, reason_codes=reasons),
        )

    @staticmethod
    def _warm_calculation_summary() -> CalculationSummary:
        return CalculationSummary(
            route="warm",
            user_facing_formula="최종 예상가격 = exp(안정 블렌드 로그가격)",
            model_components=[
                CalculationComponent(
                    name="작가 이력량 피처",
                    role="확정된 작가키와 동일 작가 학습 가격 수를 사용해 작가 이력의 깊이를 표현",
                    formula="artist_works_log = ln(1 + artist_works_count_train)",
                    output_field="artist_key/artist_works_count_train/artist_works_log",
                ),
                CalculationComponent(
                    name="작가 기반 유사작품 가격 통계 피처",
                    role="동일 작가 또는 충분한 표본이 있는 가까운 비교군의 가격 중앙값과 분산을 계산",
                    formula="비교군 우선순위 = 작가+재료/지지체+크기 → 작가+크기 → 작가 전체 → 재료/지지체+크기 → 전체",
                    output_field="svc_group_log_price_median/svc_group_n/svc_coverage_tier",
                ),
                CalculationComponent(
                    name="유사작품 통계 기반 기준 후보",
                    role="동일 작가와 유사 작품의 가격 분포를 기반으로 기준 로그가격 후보를 산출",
                    formula="기준 후보 로그가격 = Huber seed 모델 10개 예측값의 평균",
                    output_field="svc_numeric_seed_mean_pred_log",
                ),
                CalculationComponent(
                    name="방어형 CatBoost 후보",
                    role="작품 피처와 동일 작가 유사작품 통계를 함께 사용해 보수적인 보정 후보를 계산",
                    formula="방어형 후보 로그가격 = CatBoost(작품 피처 + 작가키 + 유사작품 통계 피처)",
                    output_field="pp_v2_defensive_pred_log",
                ),
                CalculationComponent(
                    name="Quantile 순차 보정 후보",
                    role="하위/중앙/상위 분위 예측 폭을 사용해 불확실성을 반영한 순차 보정 후보를 계산",
                    formula="순차 보정 로그가격 = Huber 중심선 + CatBoost 잔차 보정(q10, q50, q90 폭 포함)",
                    output_field="l10_generated_bucket_seq_pred_log",
                ),
                CalculationComponent(
                    name="안정 블렌드 후보",
                    role="방어형 CatBoost 후보와 Quantile 순차 보정 후보를 섞어 운영 표시값으로 사용",
                    formula="안정 블렌드 로그가격 = 0.75 * 방어형 CatBoost 후보 로그가격 + 0.25 * Quantile 순차 보정 후보 로그가격",
                    output_field="pp_v8_compact_blend_mape_guarded_pred_log",
                ),
                CalculationComponent(
                    name="운영 표시가격",
                    role="현재 운영 표시값은 안정 블렌드 로그가격을 원화로 변환한 값이며, 70:30 결합 후보는 비교용으로만 유지",
                    formula="표시 원화가격 = exp(안정 블렌드 로그가격)",
                    output_field="service_primary_pred_price_krw",
                ),
            ],
            guard_applied=False,
            explanation="이력 기반 예측은 작가 매칭이 확실하고 동일 작가 학습 가격이 충분한 경우 적용합니다.",
        )

    @staticmethod
    def _cold_calculation_summary(guard_applied: bool) -> CalculationSummary:
        return CalculationSummary(
            route="cold",
            user_facing_formula="참고 예상가격 = exp(방어 로그가격)",
            model_components=[
                CalculationComponent(
                    name="작가 정보 사용 범위",
                    role="기본 정보 기반 참고 예측에서는 작가키를 가격 모델 직접 입력으로 쓰지 않고 라우팅과 설명 정보로만 사용",
                    formula="가격 모델 입력 = 작품 크기 + 재료 + 지지체 + 크기 구간 피처",
                    output_field="artist_key_not_used_in_cold_price_model",
                ),
                CalculationComponent(
                    name="LightGBM Quantile 가격 범위 모델",
                    role="작품 크기, 재료, 지지체, 크기 구간으로 하위/중앙/상위 로그가격을 예측",
                    formula="q10, q40, q50, q90 로그가격 = LightGBM Quantile(작품 크기 + 재료 + 지지체 + 구간 피처)",
                    output_field="q10/q50/q90_pred_log",
                ),
                CalculationComponent(
                    name="기본 정보 기반 대표가격",
                    role="중앙 분위 예측값을 기본 참고가격 후보로 사용",
                    formula="대표 로그가격 = q50 로그가격",
                    output_field="representative_pred_log",
                ),
                CalculationComponent(
                    name="과대예측 방어 보정",
                    role="불확실성 폭이 크고 q40이 q50보다 충분히 낮을 때 q40 방향으로 낮춤",
                    formula="방어 로그가격 = 0.5 * q50 로그가격 + 0.5 * q40 로그가격",
                    output_field="defense_pred_log",
                ),
                CalculationComponent(
                    name="참고 가격 범위",
                    role="하위/상위 분위 예측값을 원화로 변환해 넓은 참고 범위를 표시",
                    formula="참고 범위 = exp(q10 로그가격) ~ exp(q90 로그가격)",
                    output_field="range_low_price_krw/range_high_price_krw",
                ),
            ],
            guard_applied=guard_applied,
            explanation="기본 정보 기반 참고 예측은 동일 작가 가격 이력이 부족할 때 참고 가격으로 제공합니다.",
        )

    @staticmethod
    def _review_calculation_summary() -> CalculationSummary:
        return CalculationSummary(
            route="review_required",
            user_facing_formula="작가 확정 또는 최소 입력값 검수 후 가격 계산",
            model_components=[],
            guard_applied=False,
            explanation="입력 정보만으로는 가격 표시 기준을 만족하지 못해 운영 검수가 필요합니다.",
        )

    @staticmethod
    def _feedback_guide() -> FeedbackGuide:
        return FeedbackGuide(
            can_submit_actual_sale_price=True,
            feedback_endpoint="/api/v2/feedback/sale-price",
            required_fields=["prediction_id", "actual_sale_price_krw", "evidence_status", "consent_for_training"],
            note="실제 판매가와 증빙이 들어오면 검수 후 다음 학습 후보로 사용할 수 있습니다.",
        )

    @staticmethod
    def _range_display(low: int | None, high: int | None) -> str | None:
        if low is None or high is None:
            return None
        return f"{format_krw(low)} - {format_krw(high)}"
