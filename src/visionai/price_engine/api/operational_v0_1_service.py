"""Operational service layer for price_prediction v0.1.

The service intentionally uses the frozen files under
`models/track6/price_prediction_v0.1/operational`.  It does not call old
experiment endpoints, and it does not expose experiment IDs to API clients.
"""

from __future__ import annotations

import json
import math
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor

from visionai.price_engine.api.operational_v0_1_schemas import (
    ArtistInput,
    ComparableSample,
    Confidence,
    CurrentModelResponse,
    ExchangeRates,
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
    WarningItem,
)
from visionai.price_engine.api.primary_feature_builder import area_to_ho


MODEL_VERSION = "price_prediction_v0.1"
OPERATIONAL_VERSION = "v0.1-operational"
FX_KRW_PER_UNIT = {
    "USD": 1380.0,
    "EUR": 1530.0,
    "GBP": 1780.0,
    "HKD": 178.0,
    "JPY": 9.5,
}


def find_repo_root(start: Path) -> Path:
    for current in [start, *start.parents]:
        if (current / "src" / "visionai").exists() and (current / "models" / "track6").exists():
            return current
    raise RuntimeError(f"VisionAI repo root를 찾을 수 없습니다: {start}")


REPO = find_repo_root(Path(__file__).resolve())
TRACK6_SCRIPT_DIR = REPO / "scripts" / "track6"
if str(TRACK6_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(TRACK6_SCRIPT_DIR))

import extract_price_prediction_v0_1_features as feature_ops  # noqa: E402
import run_pp_svc1_comparable_stats_feature_validation as svc1  # noqa: E402
from run_pp_l10_warm_l8_feature_variant_experiments import (  # noqa: E402
    add_quantile_features,
    cat_indices as l10_cat_indices,
    cat_ready as l10_cat_ready,
    normalize_frame as l10_normalize_frame,
)


def now_kst_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def normalize_name(value: object) -> str:
    text = "" if value is None or pd.isna(value) else str(value).strip().lower()
    text = text.replace("-", " ")
    text = re.sub(r"[^0-9a-z가-힣]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def safe_int(value: object) -> int | None:
    if value is None or pd.isna(value):
        return None
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return None


def safe_price(value: object) -> int | None:
    if value is None or pd.isna(value):
        return None
    try:
        price = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(price) or price <= 0:
        return None
    return int(round(price))


def exp_price(log_value: object) -> float:
    value = float(log_value)
    return float(np.exp(np.clip(value, math.log(1_000.0), math.log(1_000_000_000_000.0))))


def format_krw(value: int | None) -> str | None:
    if value is None:
        return None
    if value >= 100_000_000:
        eok = value / 100_000_000
        return f"{eok:.1f}억원" if eok < 10 else f"{round(eok):,}억원"
    if value >= 10_000:
        man = round(value / 10_000)
        return f"{man:,}만원"
    return f"{value:,}원"


def format_krw_per_ho(value: int | None) -> str:
    formatted = format_krw(value)
    return "-" if formatted is None else f"{formatted}/호"


def dimension_area(width_cm: float | None, height_cm: float | None) -> float:
    if width_cm is None or height_cm is None:
        return float("nan")
    return float(width_cm) * float(height_cm)


@dataclass(frozen=True)
class ArtistRecord:
    artist_key: str
    name_ko: str | None
    name_en: str | None
    birth_year: int | None
    nationality: str | None
    entity_suffix: str | None
    valid_training_label_count: int


class OperationalV01Service:
    """Cached operational model service for the v0.1 API."""

    def __init__(self, model_root: Path | None = None) -> None:
        self.model_root = model_root or REPO / "models" / "track6" / "price_prediction_v0.1"
        self.operational_root = self.model_root / "operational"
        self.artifact_dir = self.operational_root / "artifacts"
        self.manifest = self._load_json(self.artifact_dir / "operational_policy_manifest.json")
        self.feature_generation = feature_ops.load_artifact_feature_generation(self.model_root)
        self.train = feature_ops.load_training_snapshot(self.model_root)
        self.train_for_svc = feature_ops.add_bucket_features(self.train, self.feature_generation, "warm")
        self.artist_slug_mapping = self._load_artist_slug_mapping()
        self.artist_records = self._build_artist_records()
        self.alias_index = self._build_alias_index()
        self.comparable_source = pd.read_csv(
            self.operational_root / "data" / "warm_comparable_source_train.csv",
            low_memory=False,
        )
        self.svc_payload = joblib.load(REPO / self.manifest["components"]["svc_numeric_seed_mean"]["artifact"])
        self.l10_info = self.manifest["components"]["l10_generated_bucket_seq"]
        self.v2_info = self.manifest["components"]["pp_v2_defensive_component"]
        self.l10_quantile_models = {
            label: self._load_catboost(REPO / self.l10_info["quantile_models"][label])
            for label in ["q10", "q50", "q90"]
        }
        self.l10_huber_payload = joblib.load(REPO / self.l10_info["huber_centerline"])
        self.l10_residual_model = self._load_catboost(REPO / self.l10_info["residual_catboost"])
        self.v2_model = self._load_catboost(REPO / self.v2_info["artifact"])

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _load_catboost(path: Path) -> CatBoostRegressor:
        model = CatBoostRegressor()
        model.load_model(path)
        return model

    @staticmethod
    def _load_artist_slug_mapping() -> pd.DataFrame:
        mapping_path = REPO / "data" / "artist_slug_mapping_expanded.csv"
        if not mapping_path.exists():
            return pd.DataFrame(columns=["ko_name", "en_slug", "en_name"])
        return pd.read_csv(mapping_path, low_memory=False)

    def current_model(self, request_id: str) -> CurrentModelResponse:
        service_primary = self.manifest.get("service_primary", {})
        return CurrentModelResponse(
            request_id=request_id,
            status="success",
            created_at=now_kst_iso(),
            model_version=MODEL_VERSION,
            model_status="active",
            display_policy={"warm": "price_with_range", "cold": "reference_range_only"},
            exchange_rates=ExchangeRates(**FX_KRW_PER_UNIT),
            service_primary_candidate=service_primary.get("warm_candidate", "pp_v8_compact_blend_mape_guarded"),
            service_primary_column=service_primary.get("prediction_column", "service_primary_pred_price_krw"),
        )

    def resolve_artist(self, request_id: str, artist: ArtistInput, max_candidates: int = 5) -> ResolveArtistResponse:
        candidates = self._find_artist_candidates(artist, max_candidates=max_candidates)
        warnings: list[WarningItem] = []
        resolved = len(candidates) == 1 and candidates[0].match_status in {"exact", "alias"}
        requires_selection = len(candidates) > 1
        status = "success" if resolved else "partial_success"
        if not candidates:
            warnings.append(WarningItem(
                code="ARTIST_NOT_RESOLVED",
                message="작가를 모델 artist_key로 확정하지 못했습니다. 작가 후보 선택 또는 운영 검수가 필요합니다.",
            ))
        elif requires_selection:
            warnings.append(WarningItem(
                code="ARTIST_AMBIGUOUS",
                message="유사한 작가 후보가 2명 이상입니다. 후보를 선택한 뒤 가격 예측을 진행해야 합니다.",
            ))
        return ResolveArtistResponse(
            request_id=request_id,
            status=status,
            created_at=now_kst_iso(),
            model_version=MODEL_VERSION,
            resolved=resolved,
            requires_selection=requires_selection,
            selected_artist=candidates[0] if resolved else None,
            candidates=candidates,
            warnings=warnings,
        )

    def estimate_price(self, request_id: str, request: PriceEstimateRequest) -> PriceEstimateResponse:
        warnings: list[WarningItem] = []
        artist_resolution = self.resolve_artist(
            request_id=request_id,
            artist=request.artwork.artist,
            max_candidates=5,
        )
        if not artist_resolution.resolved or artist_resolution.selected_artist is None:
            warnings.extend(artist_resolution.warnings)
            return self._cold_or_unresolved_response(request_id, request, artist_resolution, warnings)

        artist = artist_resolution.selected_artist
        if not artist.warm_available:
            warnings.append(WarningItem(
                code="COLD_ARTIST",
                message="v0.1 운영 패키지는 Cold 자동 예측을 보류합니다. 참고 가격 범위만 제공해야 합니다.",
            ))
            return self._cold_or_unresolved_response(request_id, request, artist_resolution, warnings)

        frame = self._build_feature_frame(request, artist.artist_key)
        pred = self._predict_warm(frame)
        row = pred.iloc[0]
        warnings.extend(self._prediction_warnings(row))
        comparable_samples = (
            self._comparable_samples(frame.iloc[0], request.options.max_comparable_samples)
            if request.options.include_comparable_samples
            else []
        )
        return PriceEstimateResponse(
            request_id=request_id,
            status="success",
            created_at=now_kst_iso(),
            model_version=MODEL_VERSION,
            route="warm",
            display_policy="price_with_range",
            prediction=self._prediction_from_row(row),
            routing=Routing(
                artist_matched=True,
                matched_artist_key=artist.artist_key,
                valid_training_label_count=artist.valid_training_label_count,
                route_policy="v0_1_artist_registry_warm",
                route_reason="작가키가 v0.1 학습 artist registry에 존재해 Warm route를 적용했습니다.",
            ),
            basis=self._basis_from_row(row),
            market_price_card=self._market_price_card(row, frame.iloc[0]),
            comparable_samples=comparable_samples,
            warnings=warnings,
        )

    def _build_artist_records(self) -> dict[str, ArtistRecord]:
        rows: dict[str, ArtistRecord] = {}
        train = self.train.copy()
        grouped = train.groupby("artist_key", dropna=True, observed=False)
        for key, group in grouped:
            key_text = str(key)
            count = int(pd.to_numeric(group["price_krw"], errors="coerce").notna().sum())
            first = group.iloc[0]
            rows[key_text] = ArtistRecord(
                artist_key=key_text,
                name_ko=self._first_text(group, "artist_name_ko"),
                name_en=self._name_en_from_mapping(key_text),
                birth_year=safe_int(first.get("artist_meta_birth_year")),
                nationality=self._first_text(group, "artist_meta_nationality"),
                entity_suffix=self._first_text(group, "artist_entity_suffix"),
                valid_training_label_count=count,
            )
        return rows

    def _build_alias_index(self) -> dict[str, set[str]]:
        aliases: dict[str, set[str]] = {}
        for record in self.artist_records.values():
            values = [record.artist_key, record.name_ko, record.name_en]
            for value in values:
                norm = normalize_name(value)
                if norm:
                    aliases.setdefault(norm, set()).add(record.artist_key)
            slug_norm = normalize_name(record.artist_key.replace(" ", "-"))
            if slug_norm:
                aliases.setdefault(slug_norm, set()).add(record.artist_key)
        if not self.artist_slug_mapping.empty:
            for _, row in self.artist_slug_mapping.iterrows():
                key = normalize_name(str(row.get("en_slug", "")).replace("-", " "))
                if key not in self.artist_records:
                    continue
                for col in ["ko_name", "en_name", "en_slug"]:
                    norm = normalize_name(row.get(col))
                    if norm:
                        aliases.setdefault(norm, set()).add(key)
        return aliases

    def _name_en_from_mapping(self, artist_key: str) -> str | None:
        if self.artist_slug_mapping.empty:
            return None
        key_norm = normalize_name(artist_key)
        hit = self.artist_slug_mapping[
            normal_series(self.artist_slug_mapping["en_slug"].astype(str).str.replace("-", " ")).eq(key_norm)
        ]
        if hit.empty:
            return None
        value = hit.iloc[0].get("en_name")
        return None if pd.isna(value) else str(value)

    @staticmethod
    def _first_text(group: pd.DataFrame, col: str) -> str | None:
        if col not in group.columns:
            return None
        values = group[col].dropna().astype(str)
        if values.empty:
            return None
        value = values.iloc[0].strip()
        return value or None

    def _find_artist_candidates(self, artist: ArtistInput, max_candidates: int) -> list[ResolvedArtist]:
        keys: set[str] = set()
        match_basis = "fuzzy_name"
        match_status = "fuzzy"
        for basis, raw in [
            ("provided_artist_key", artist.artist_key),
            ("verified_ko_name", artist.name_ko),
            ("verified_en_alias", artist.name_en),
        ]:
            norm = normalize_name(raw)
            if not norm:
                continue
            direct = self.alias_index.get(norm, set())
            if direct:
                keys |= direct
                match_basis = basis
                match_status = "exact" if basis == "provided_artist_key" else "alias"
        if not keys:
            query = normalize_name(artist.name_ko or artist.name_en or artist.artist_key)
            scored = []
            if query:
                for alias, alias_keys in self.alias_index.items():
                    score = simple_similarity(query, alias)
                    if score >= 0.78:
                        for key in alias_keys:
                            scored.append((score, key))
            keys = {key for _score, key in sorted(scored, reverse=True)[:max_candidates]}
            match_status = "fuzzy"
            match_basis = "fuzzy_name"
        records = [self.artist_records[key] for key in keys if key in self.artist_records]
        records.sort(key=lambda item: item.valid_training_label_count, reverse=True)
        if len(records) > 1 and match_status in {"exact", "alias"}:
            match_status = "ambiguous"
        return [
            ResolvedArtist(
                artist_key=record.artist_key,
                name_ko=record.name_ko,
                name_en=record.name_en,
                birth_year=record.birth_year,
                nationality=record.nationality,
                entity_suffix=record.entity_suffix,
                match_status=match_status,
                matched_alias=artist.artist_key or artist.name_ko or artist.name_en,
                match_basis=match_basis,
                review_required=match_status in {"ambiguous", "fuzzy"},
                warm_available=record.valid_training_label_count > 0,
                valid_training_label_count=record.valid_training_label_count,
                route_recommendation="warm" if record.valid_training_label_count > 0 else "cold",
            )
            for record in records[:max_candidates]
        ]

    def _build_feature_frame(self, request: PriceEstimateRequest, artist_key: str) -> pd.DataFrame:
        artwork = request.artwork
        width = float(artwork.dimensions.width_cm or 0.0)
        height = float(artwork.dimensions.height_cm or 0.0)
        depth = float(artwork.dimensions.depth_cm or 0.0)
        area = dimension_area(width, height)
        aspect = max(width, height) / min(width, height) if min(width, height) > 0 else np.nan
        base = pd.DataFrame([{
            "_v01_row_id": 0,
            "_track6_row_id": 0,
            "slug": artwork.external_artwork_id or "",
            "title": artwork.title or "",
            "artist_name": artwork.artist.name_en or artwork.artist.name_ko or artist_key,
            "artist_slug": artist_key.replace(" ", "-"),
            "matched_train_artist": artist_key,
            "artist_key": artist_key,
            "artist_match_source": "api_artist_key",
            "artist_match_status": "matched",
            "warm_cold_route": "warm",
            "artwork_url": artwork.artwork_url or "",
            "date": artwork.year,
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
            "medium_support_bucket": f"{artwork.medium.medium_category}__{artwork.medium.support_category}",
            "is_extreme_aspect_ratio": bool(aspect > 10) if math.isfinite(aspect) else False,
            "is_training_candidate": True,
            "collected_material_raw": f"{artwork.medium.medium_category} on {artwork.medium.support_category}",
        }])
        registry = feature_ops.build_artist_registry(self.train)
        base = base.merge(registry, on="artist_key", how="left")
        base["artist_works_count_train"] = pd.to_numeric(base["artist_works_count_train"], errors="coerce").fillna(0).astype(int)
        base["artist_works_log"] = pd.to_numeric(base["artist_works_log"], errors="coerce").fillna(np.log1p(base["artist_works_count_train"]))
        frame = feature_ops.add_bucket_features(base, self.feature_generation, "warm")
        svc = feature_ops.apply_comparable_stats(self.train_for_svc, frame)
        return frame.merge(svc, on="_v01_row_id", how="left")

    def _predict_warm(self, frame: pd.DataFrame) -> pd.DataFrame:
        out = frame.copy()
        out["svc_numeric_seed_mean_pred_log"] = self._predict_svc(frame)
        l10 = self._predict_l10(frame)
        out["l10_q10_pred_log"] = l10["q10"]
        out["l10_q50_pred_log"] = l10["q50"]
        out["l10_q90_pred_log"] = l10["q90"]
        out["l10_quantile_width"] = l10["quantile_width"]
        out["l10_price_range_ratio"] = l10["price_range_ratio"]
        out["l10_generated_bucket_seq_pred_log"] = l10["sequence"]
        out["pp_v2_defensive_pred_log"] = self._predict_v2(frame)
        out["pp_v8_compact_blend_mape_guarded_pred_log"] = (
            0.75 * out["pp_v2_defensive_pred_log"]
            + 0.25 * out["l10_generated_bucket_seq_pred_log"]
        )
        out["v01_operational_pred_log"] = (
            0.70 * out["svc_numeric_seed_mean_pred_log"]
            + 0.30 * out["pp_v8_compact_blend_mape_guarded_pred_log"]
        )
        out["service_primary_pred_log"] = out["pp_v8_compact_blend_mape_guarded_pred_log"]
        for col in [
            "service_primary_pred_log",
            "v01_operational_pred_log",
            "l10_q10_pred_log",
            "l10_q90_pred_log",
        ]:
            out[col.replace("_log", "_price_krw")] = [exp_price(value) for value in out[col]]
        out["svc_group_price_median"] = [exp_price(value) for value in out["svc_group_log_price_median"]]
        out["svc_group_price_q25"] = [exp_price(value) for value in out["svc_group_log_price_q25"]]
        out["svc_group_price_q75"] = [exp_price(value) for value in out["svc_group_log_price_q75"]]
        out["service_confidence_tier"] = self._confidence_tier(out)
        return out

    def _predict_svc(self, frame: pd.DataFrame) -> np.ndarray:
        features = self.svc_payload["features"]
        prepared = svc1.normalize(frame.copy(), features)
        preds = [np.asarray(model.predict(prepared[features]), dtype=float) for model in self.svc_payload["models"]]
        return np.mean(np.vstack(preds), axis=0)

    def _predict_l10(self, frame: pd.DataFrame) -> dict[str, np.ndarray]:
        base_features = self.l10_info["base_features"]
        enriched_features = self.l10_info["enriched_features"]
        numeric = set(self.l10_info["numeric_features"])
        base_numeric = {feature for feature in base_features if feature in numeric}
        q = {
            label: np.asarray(
                model.predict(l10_cat_ready(frame, base_features, base_numeric)),
                dtype=float,
            )
            for label, model in self.l10_quantile_models.items()
        }
        q_payload = {label: {"operation": pred} for label, pred in q.items()}
        enriched = add_quantile_features(frame, q_payload, "operation")
        prepared = l10_normalize_frame(enriched, enriched_features, numeric)
        center = np.asarray(self.l10_huber_payload["model"].predict(prepared[enriched_features]), dtype=float)
        residual = np.asarray(
            self.l10_residual_model.predict(l10_cat_ready(enriched, enriched_features, numeric)),
            dtype=float,
        )
        width = q["q90"] - q["q10"]
        return {
            "q10": q["q10"],
            "q50": q["q50"],
            "q90": q["q90"],
            "sequence": center + residual,
            "quantile_width": width,
            "price_range_ratio": np.exp(np.clip(width, 0.0, math.log(1_000.0))),
        }

    def _predict_v2(self, frame: pd.DataFrame) -> np.ndarray:
        features = self.v2_info["features"]
        numeric = set(self.v2_info["numeric_features"])
        prepared = frame[features].copy()
        for col in features:
            if col in numeric:
                prepared[col] = pd.to_numeric(prepared[col], errors="coerce").fillna(0.0)
            else:
                prepared[col] = prepared[col].astype(str).fillna("__MISSING__").replace({"": "__MISSING__"})
        return np.asarray(self.v2_model.predict(prepared), dtype=float)

    @staticmethod
    def _confidence_tier(frame: pd.DataFrame) -> pd.Series:
        n = pd.to_numeric(frame.get("svc_group_n"), errors="coerce").fillna(0.0)
        ratio = pd.to_numeric(frame.get("l10_price_range_ratio"), errors="coerce").replace([np.inf, -np.inf], np.nan)
        ratio = ratio.fillna(ratio.median() if ratio.notna().any() else 999.0)
        confidence = pd.Series("low", index=frame.index, dtype=object)
        confidence[(n >= 10) & (ratio <= 8.0)] = "medium"
        confidence[(n >= 30) & (ratio <= 4.0)] = "high"
        return confidence

    def _prediction_from_row(self, row: pd.Series) -> Prediction:
        price = safe_price(row.get("service_primary_pred_price_krw"))
        low = safe_price(row.get("l10_q10_pred_price_krw"))
        high = safe_price(row.get("l10_q90_pred_price_krw"))
        if low is not None and high is not None and price is not None:
            low = min(low, price, high)
            high = max(low, price, high)
        reason_codes = ["WARM_ARTIST_MATCHED"]
        if str(row.get("service_confidence_tier")) == "low":
            reason_codes.append("LOW_SIMILAR_SAMPLE_COUNT")
        if float(row.get("l10_price_range_ratio", 0) or 0) > 8:
            reason_codes.append("WIDE_PRICE_RANGE")
        return Prediction(
            price_krw=price,
            price_display=format_krw(price),
            range_krw=PriceRange(low=low, mid=price, high=high),
            range_display=self._range_display(low, high),
            confidence=Confidence(level=str(row.get("service_confidence_tier", "low")), reason_codes=reason_codes),
        )

    @staticmethod
    def _basis_from_row(row: pd.Series) -> PredictionBasis:
        return PredictionBasis(
            similar_group_level=str(row.get("svc_group_level")) if pd.notna(row.get("svc_group_level")) else None,
            similar_sample_count=safe_int(row.get("svc_group_n")),
            similar_coverage_tier=str(row.get("svc_coverage_tier")) if pd.notna(row.get("svc_coverage_tier")) else None,
            similar_price_median_krw=safe_price(row.get("svc_group_price_median")),
            similar_price_q25_krw=safe_price(row.get("svc_group_price_q25")),
            similar_price_q75_krw=safe_price(row.get("svc_group_price_q75")),
        )

    def _market_price_card(self, row: pd.Series, feature_row: pd.Series) -> MarketPriceCard:
        ho = max(area_to_ho(float(feature_row["area_cm2"])), 1)
        median = divide_price(row.get("svc_group_price_median"), ho)
        q25 = divide_price(row.get("svc_group_price_q25"), ho)
        q75 = divide_price(row.get("svc_group_price_q75"), ho)
        distribution = self._medium_distribution(feature_row, ho)
        sample_count = safe_int(row.get("svc_group_n")) or 0
        return MarketPriceCard(
            median_krw_per_ho=median,
            median_display=format_krw_per_ho(median),
            range_krw_per_ho=RangePerHo(low=q25, high=q75),
            range_display=f"{format_krw_per_ho(q25)} - {format_krw_per_ho(q75)}",
            medium_distribution=distribution,
            sample_count=sample_count,
            sample_count_display=f"표본 수 N={sample_count:,}건",
        )

    def _medium_distribution(self, feature_row: pd.Series, ho: int) -> list[MediumDistribution]:
        artist_key = str(feature_row["artist_key"])
        source = self.train_for_svc[self.train_for_svc["artist_key"].astype(str).eq(artist_key)].copy()
        if source.empty:
            return []
        source["unit_per_ho"] = pd.to_numeric(source["price_krw"], errors="coerce") / max(ho, 1)
        rows = []
        for medium, group in source.groupby("medium_category", observed=False):
            median = safe_price(group["unit_per_ho"].median())
            rows.append(MediumDistribution(
                label=str(medium),
                medium_group=str(medium),
                median_krw_per_ho=median,
                display=format_krw(median) or "-",
                sample_count=int(len(group)),
            ))
        rows.sort(key=lambda item: item.sample_count, reverse=True)
        return rows[:4]

    def _comparable_samples(self, feature_row: pd.Series, max_samples: int) -> list[ComparableSample]:
        if max_samples <= 0:
            return []
        source = self.comparable_source[
            self.comparable_source["artist_key"].astype(str).eq(str(feature_row["artist_key"]))
        ].copy()
        if source.empty:
            source = self.comparable_source.copy()
        target_area = float(feature_row.get("area_cm2", 0) or 0)
        source["area_diff"] = (pd.to_numeric(source["area_cm2"], errors="coerce") - target_area).abs()
        source = source.sort_values(["area_diff", "price_krw"], ascending=[True, False]).head(max_samples)
        result = []
        for _, row in source.iterrows():
            result.append(ComparableSample(
                artwork_id=str(row.get("source_artwork_id") or row.get("_track6_row_id") or ""),
                title=str(row.get("title_raw") or ""),
                artist_name=str(row.get("artist_name_ko") or row.get("artist_key") or ""),
                sale_price_krw=safe_price(row.get("price_krw")),
                width_cm=float(row["width_cm"]) if pd.notna(row.get("width_cm")) else None,
                height_cm=float(row["height_cm"]) if pd.notna(row.get("height_cm")) else None,
                medium_category=str(row.get("medium_category") or ""),
                support_category=str(row.get("support_category") or ""),
                similarity_reason="same_artist_closest_area",
            ))
        return result

    @staticmethod
    def _prediction_warnings(row: pd.Series) -> list[WarningItem]:
        warnings = []
        n = float(row.get("svc_group_n") or 0)
        if n < 15:
            warnings.append(WarningItem(
                code="LOW_SIMILAR_SAMPLE_COUNT",
                message="유사 작품 표본 수가 적어 가격 범위를 넓게 해석해야 합니다.",
            ))
        if str(row.get("svc_group_level")) == "global":
            warnings.append(WarningItem(
                code="GLOBAL_FALLBACK_USED",
                message="조건에 맞는 유사 작품 묶음이 부족해 전체 fallback 통계를 사용했습니다.",
            ))
        if float(row.get("l10_price_range_ratio", 0) or 0) > 8:
            warnings.append(WarningItem(
                code="WIDE_PRICE_RANGE",
                message="모델이 계산한 가격 범위가 넓습니다. 단일 확정가보다 범위 중심으로 해석해야 합니다.",
            ))
        return warnings

    def _cold_or_unresolved_response(
        self,
        request_id: str,
        request: PriceEstimateRequest,
        artist_resolution: ResolveArtistResponse,
        warnings: list[WarningItem],
    ) -> PriceEstimateResponse:
        selected = artist_resolution.selected_artist
        return PriceEstimateResponse(
            request_id=request_id,
            status="partial_success",
            created_at=now_kst_iso(),
            model_version=MODEL_VERSION,
            route="cold",
            display_policy="reference_range_only",
            prediction=Prediction(
                price_krw=None,
                price_display=None,
                range_krw=PriceRange(),
                range_display=None,
                confidence=Confidence(level="low", reason_codes=[warning.code for warning in warnings] or ["COLD_ARTIST"]),
            ),
            routing=Routing(
                artist_matched=selected is not None,
                matched_artist_key=selected.artist_key if selected else None,
                valid_training_label_count=selected.valid_training_label_count if selected else None,
                route_policy="v0_1_cold_reference_pending",
                route_reason="v0.1 운영 패키지는 Cold 자동 예측을 보류하고 Warm 예측만 운영 기본값으로 제공합니다.",
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
            warnings=warnings,
        )

    @staticmethod
    def _range_display(low: int | None, high: int | None) -> str | None:
        if low is None or high is None:
            return None
        return f"{format_krw(low)} - {format_krw(high)}"


def normal_series(series: pd.Series) -> pd.Series:
    return series.map(normalize_name)


def simple_similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    try:
        from rapidfuzz import fuzz

        return float(fuzz.token_sort_ratio(left, right)) / 100.0
    except Exception:
        left_set = set(left.split())
        right_set = set(right.split())
        if not left_set or not right_set:
            return 0.0
        return len(left_set & right_set) / len(left_set | right_set)


def divide_price(price: object, denominator: int) -> int | None:
    safe = safe_price(price)
    if safe is None or denominator <= 0:
        return None
    return int(round(safe / denominator))
