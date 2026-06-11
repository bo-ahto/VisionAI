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
    normalize_name,
    now_kst_iso,
    safe_int,
    safe_price,
)
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
    ResolveArtistResponse,
    ResolvedArtist,
    Routing,
    SalePriceFeedbackRequest,
    SalePriceFeedbackResponse,
    WarningItem,
)


MODEL_VERSION = "price_prediction_v0.2"
WARM_MODEL_VERSION = "warm_runtime_v0.1_with_v0.2_routing_policy"
COLD_MODEL_VERSION = "cold_prediction_v0.2_operational_search_free"
WARM_MATCH_SCORE_MIN = 0.90
WARM_TRAINING_PRICE_MIN = 5
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
        )

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
            market_price_card=MarketPriceCard(
                median_display="-",
                range_krw_per_ho=RangePerHo(),
                range_display="-",
                medium_distribution=[],
                sample_count=0,
                sample_count_display="Cold 경로는 동일 작가 시장가 카드가 없습니다.",
            ),
            comparable_samples=comparable_samples,
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
            user_facing_formula="예측가격 = 유사작품 기준가격 + 안정 보정가격",
            model_components=[
                CalculationComponent(
                    name="유사작품 통계 기반 기준가격",
                    role="동일 작가와 유사 작품의 가격 분포를 기반으로 기준 로그가격을 산출",
                    formula="기준 로그가격 = seed별 유사작품 통계 모델 예측값의 평균",
                    output_field="svc_numeric_seed_mean_pred_log",
                ),
                CalculationComponent(
                    name="안정 보정가격",
                    role="CatBoost 후보와 Quantile 기반 순차 보정 후보를 섞어 기준가격의 과대/과소 이동을 완화",
                    formula="안정 보정 로그가격 = 0.75 * 방어형 후보 로그가격 + 0.25 * Quantile 순차 보정 로그가격",
                    output_field="pp_v8_compact_blend_mape_guarded_pred_log",
                ),
                CalculationComponent(
                    name="운영 표시가격",
                    role="현재 운영 표시값은 안정 보정 로그가격을 원화로 변환한 값",
                    formula="표시 원화가격 = exp(안정 보정 로그가격)",
                    output_field="service_primary_pred_price_krw",
                ),
            ],
            guard_applied=False,
            explanation="Warm은 작가 매칭이 확실하고 동일 작가 학습 가격이 충분한 경우 적용합니다.",
        )

    @staticmethod
    def _cold_calculation_summary(guard_applied: bool) -> CalculationSummary:
        return CalculationSummary(
            route="cold",
            user_facing_formula="참고 예측가격 = LightGBM Quantile 중앙값 후보 + 과대예측 방어 보정",
            model_components=[
                CalculationComponent(
                    name="LightGBM Quantile 가격 범위 모델",
                    role="작품 크기, 재료, 지지체, 크기 구간으로 하위/중앙/상위 로그가격을 예측",
                    formula="가격범위 = exp(q10 로그가격) ~ exp(q90 로그가격)",
                    output_field="q10/q50/q90_pred_log",
                ),
                CalculationComponent(
                    name="Cold 대표가격",
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
            ],
            guard_applied=guard_applied,
            explanation="Cold는 동일 작가 가격 이력이 부족할 때 참고 가격만 제공합니다.",
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
