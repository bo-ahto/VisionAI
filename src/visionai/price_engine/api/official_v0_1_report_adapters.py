"""Report-model compatible adapters for the official v0.1 service.

These adapters bridge raw service input to the final report-layer formulas.
They are intentionally marked as proxy adapters because the exact PP252 and
Cold search-upstream models are fixed-test artifacts, not complete raw-input
runtime packages.
"""

from __future__ import annotations

import importlib.util
import json
import math
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from visionai.price_engine.api import operational_v0_1_schemas as op1s
from visionai.price_engine.api.official_v0_1_schemas import PriceEstimateRequest
from visionai.price_engine.api.operational_v0_1_service import (
    REPO,
    OperationalV01Service,
    dimension_area,
    feature_ops,
)


COLD_V02_BUNDLE = REPO / "models" / "track6" / "cold_prediction_v0.2_operational"
WARM_PP258_FINAL_LAYER_PATH = (
    REPO
    / "experiments"
    / "track6"
    / "SUB-WARM-PP258_operational_fixed_test_submission"
    / "scripts"
    / "pp258_reproduce_fixed_test.py"
)
COLD_V03_POSTPROCESSOR_PATH = (
    REPO
    / "models"
    / "track6"
    / "cold_prediction_v0.3"
    / "predict"
    / "apply_cold_postprocess_v0_3.py"
)
WARM_REFREEZE_DIR = REPO / "models" / "track6" / "warm_pp252_upstream_refreeze_candidate" / "artifacts"
WARM_WMIN4_MANIFEST_PATH = REPO / "models" / "track6" / "warm_wmin4_operational_candidate" / "manifest.json"
WARM_WMIN8_MANIFEST_PATH = REPO / "models" / "track6" / "warm_wmin8_operational_candidate" / "manifest.json"
WARM_WMIN8_EXACT_RUNTIME_DIR = REPO / "models" / "track6" / "warm_wmin8_exact_runtime_candidate"
WARM_WMIN8_EXACT_RUNTIME_MANIFEST_PATH = WARM_WMIN8_EXACT_RUNTIME_DIR / "manifest.json"
WARM_WMIN8_FEATURE_STORE_PATH = WARM_WMIN8_EXACT_RUNTIME_DIR / "artifacts" / "fixed_test_feature_store.csv"
WARM_LITE_PREDICTOR_PATH = REPO / "models" / "track6" / "warm_lite_v0.1" / "predict" / "predict_warm_lite_v0_1.py"
COLD_REFREEZE_DIR = REPO / "models" / "track6" / "cold_v03_research_upstream_refreeze_candidate" / "artifacts"
DEFAULT_OFFICIAL_DB_PATH = REPO / "data" / "track6" / "service_v0_1" / "price_prediction_v0_1.sqlite"
COLD_EXTERNAL_FEATURE_CACHE_PATH = (
    REPO / "data" / "track6" / "service_v0_1" / "official_v0_1_artist_external_feature_cache.csv"
)
COLD_FEATURE_STORE_PATH = (
    REPO / "data" / "track6" / "service_v0_1" / "official_v0_1_cold_feature_store.csv"
)


@dataclass(frozen=True)
class ReportAdapterResult:
    route: str
    execution_level: str
    price_krw: int | None
    low_krw: int | None
    high_krw: int | None
    confidence_tier: str
    warning_code: str
    warning_message: str
    formula: str
    input_columns: list[str]
    output: dict[str, Any] = field(default_factory=dict)
    steps: list[dict[str, Any]] = field(default_factory=list)


def _load_module(path: Path, module_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"module load failed: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _safe_price(value: object) -> int | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number <= 0:
        return None
    return int(round(number))


def _clip_probability_from_delta(delta: float) -> float:
    # Conservative proxy only: exact direction model is not available as a
    # raw-input artifact. Keep probability near 0.5 so PP258 cap remains tiny.
    return float(np.clip(0.5 + np.clip(delta, -0.24, 0.24) * 0.25, 0.40, 0.60))


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _maybe_joblib(path: Path) -> Any | None:
    return joblib.load(path) if path.exists() else None


def _prediction_probability(model: Any, features: pd.DataFrame) -> np.ndarray:
    classes = list(model.named_steps["clf"].classes_)
    proba = model.predict_proba(features)
    pos_idx = classes.index(1) if 1 in classes else None
    if pos_idx is None:
        return np.full(len(features), 0.5, dtype=float)
    return np.nan_to_num(proba[:, pos_idx], nan=0.5, posinf=0.5, neginf=0.5)


def _safe_log1p(value: object) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(number):
        return 0.0
    return float(np.log1p(max(number, 0.0)))


def _normalize_search_name(value: object) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"\s+", "", text)
    return re.sub(r"[()\\[\\]{}.,'\"`~!@#$%^&*_+=:;|/?<>-]", "", text)


PLACEHOLDER_NORMALIZED_SEARCH_NAMES = {
    "missing",
    "__missing__",
    "nan",
    "__nan__",
    "none",
    "__none__",
    "null",
    "__null__",
    "unknown",
    "__unknown__",
    "미상",
    "없음",
}


def _valid_normalized_search_name(value: object) -> str:
    normalized = _normalize_search_name(value)
    return "" if normalized in PLACEHOLDER_NORMALIZED_SEARCH_NAMES else normalized


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(number):
        return default
    return number


def _normalize_model_input_frame(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for col in out.columns:
        if out[col].dtype == bool or str(out[col].dtype) == "boolean":
            out[col] = out[col].astype(str)
        elif out[col].dtype == object:
            values = out[col].dropna()
            if len(values) and values.map(lambda value: isinstance(value, (bool, np.bool_))).all():
                out[col] = out[col].astype(str)
    return out


def _price_band_from_log(log_price: float) -> str:
    if log_price < math.log(5_000_000):
        return "low_price"
    if log_price < math.log(20_000_000):
        return "mid_price"
    if log_price < math.log(80_000_000):
        return "high_price"
    return "very_high_price"


def _qwidth_band(width: float) -> str:
    if width < 0.60:
        return "qwidth_low"
    if width < 1.10:
        return "qwidth_mid"
    if width < 1.75:
        return "qwidth_high"
    return "qwidth_extreme"


def _svc_group_n_band(value: float) -> str:
    if value >= 50:
        return "n_50_plus"
    if value >= 20:
        return "n_20_49"
    if value >= 10:
        return "n_10_19"
    return "n_5_9"


def _area_bin(area_cm2: float) -> str:
    if area_cm2 < 1_200:
        return "0"
    if area_cm2 < 7_000:
        return "2"
    return "3"


def _rank_like(value: float, scale: float) -> float:
    if not math.isfinite(value) or scale <= 0:
        return 0.0
    return float(np.clip(value / scale, 0.0, 1.0))


class ReportModelProxyAdapter:
    """Raw-input proxy bridge to the report final layers."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DEFAULT_OFFICIAL_DB_PATH
        self.warm_runtime = OperationalV01Service()
        self.pp258 = _load_module(WARM_PP258_FINAL_LAYER_PATH, "official_v01_pp258_proxy_runtime")
        self.warm_wmin4_manifest = _load_json(WARM_WMIN4_MANIFEST_PATH)
        self.warm_wmin8_manifest = _load_json(WARM_WMIN8_MANIFEST_PATH)
        self.warm_wmin8_exact_manifest = _load_json(WARM_WMIN8_EXACT_RUNTIME_MANIFEST_PATH)
        self.warm_wmin8_exact_runtime = _load_json(WARM_WMIN8_EXACT_RUNTIME_DIR / "artifacts" / "wmin8_huber_runtime.json")
        self.warm_wmin8_shrinkage_runtime = _load_json(WARM_WMIN8_EXACT_RUNTIME_DIR / "artifacts" / "shrinkage_runtime.json")
        self.warm_wmin8_shrunk_huber_model = _maybe_joblib(
            WARM_WMIN8_EXACT_RUNTIME_DIR / "artifacts" / "shrunk_huber_refit_model.joblib"
        )
        self.warm_wmin8_base_model = _maybe_joblib(
            WARM_WMIN8_EXACT_RUNTIME_DIR / "artifacts" / "base_w700_huber_refit_pipeline.joblib"
        )
        self.warm_wmin8_alternative_model = _maybe_joblib(
            WARM_WMIN8_EXACT_RUNTIME_DIR / "artifacts" / "alternative_w850_huber_refit_pipeline.joblib"
        )
        self.warm_wmin8_feature_store = self._load_warm_wmin8_feature_store()
        self.warm_lite = _load_module(WARM_LITE_PREDICTOR_PATH, "official_v01_warm_lite_runtime")
        self.warm_lite_params = self.warm_lite.load_params()
        self.warm_lite_models = self.warm_lite.load_models()
        self.warm_refreeze_schema = _load_json(WARM_REFREEZE_DIR / "feature_schema.json")
        self.warm_direction_model = _maybe_joblib(WARM_REFREEZE_DIR / "direction_hist_gbc_35_seed17_fullfit.joblib")
        self.warm_huber_residual_model = _maybe_joblib(WARM_REFREEZE_DIR / "huber_residual_epsilon1p15_fullfit.joblib")
        self.cold_v02 = _load_module(
            COLD_V02_BUNDLE / "predict" / "predict_cold_operational_v0_2.py",
            "official_v01_cold_v02_proxy_runtime",
        )
        self.cold_v02_models = self.cold_v02.load_models()
        self.cold_v02_guard = self.cold_v02.load_guard()
        self.cold_v03 = _load_module(COLD_V03_POSTPROCESSOR_PATH, "official_v01_cold_v03_proxy_runtime")
        self.cold_v03_params = self.cold_v03.load_params()
        self.cold_v03_lookup = self.cold_v03.load_search_lookup()
        self.cold_refreeze_schema = _load_json(COLD_REFREEZE_DIR / "feature_schema.json")
        self.cold_y2_models = {
            "q10": _maybe_joblib(COLD_REFREEZE_DIR / "pp_y2_search_external_lgbq_q10.joblib"),
            "q50": _maybe_joblib(COLD_REFREEZE_DIR / "pp_y2_search_external_lgbq_q50.joblib"),
            "q90": _maybe_joblib(COLD_REFREEZE_DIR / "pp_y2_search_external_lgbq_q90.joblib"),
        }
        self.cold_qr1_q40_model = _maybe_joblib(COLD_REFREEZE_DIR / "qr1_lightgbm_q40.joblib")
        self.cold_y16_segment_map = _load_json(COLD_REFREEZE_DIR / "pp_y16_segment_map.json")
        self.cold_external_feature_cache = self._load_external_feature_cache()
        self.cold_feature_store = self._load_cold_feature_store()

    def predict_warm(self, request: PriceEstimateRequest, artist_key: str) -> ReportAdapterResult:
        if self._wmin8_exact_ready():
            snapshot, status = self._lookup_warm_wmin8_feature_store_snapshot(request, artist_key)
            if snapshot:
                row = pd.Series(snapshot)
                row["wmin8_feature_store_hit"] = True
                row["wmin8_feature_store_lookup_basis"] = status["lookup_basis"]
                return self._predict_warm_wmin8_exact(
                    request,
                    artist_key,
                    row,
                    feature_store_status=status,
                    lookup_feature_store=False,
                )

        op_request = self._to_operational_v01_request(request, artist_key)
        frame = self.warm_runtime._build_feature_frame(op_request, artist_key)
        pred = self.warm_runtime._predict_warm(frame)
        row = pred.iloc[0]

        if self._wmin8_exact_ready():
            try:
                return self._predict_warm_wmin8_exact(request, artist_key, row)
            except Exception:
                # Keep the public endpoint available. The fallback result keeps
                # explicit proxy warnings so the response is not misrepresented.
                pass

        source_log = float(row["v01_operational_pred_log"])
        stability_log = float(row["service_primary_pred_log"])
        component_values = [
            float(row["svc_numeric_seed_mean_pred_log"]),
            float(row["l10_generated_bucket_seq_pred_log"]),
            float(row["pp_v2_defensive_pred_log"]),
            float(row["pp_v8_compact_blend_mape_guarded_pred_log"]),
            source_log,
        ]
        residual_proxy = stability_log - source_log
        warm_model_features = self._build_warm_refreeze_features(row, source_log, stability_log, component_values)
        if self.warm_direction_model is not None and self.warm_huber_residual_model is not None:
            direction_probability = float(_prediction_probability(self.warm_direction_model, warm_model_features)[0])
            residual_raw = float(np.asarray(self.warm_huber_residual_model.predict(warm_model_features), dtype=float)[0])
            residual = float(np.clip(residual_raw, -0.8, 0.8))
            refreeze_note = "저장된 Warm 방향 분류 모델과 Huber 잔차 모델을 호출했고, 운영 입력 분포 방어를 위해 Huber 잔차를 로그 기준 ±0.8 안으로 제한했습니다."
        else:
            direction_probability = _clip_probability_from_delta(residual_proxy)
            residual_raw = residual_proxy
            residual = residual_proxy
            refreeze_note = "저장된 Warm 상류 모델을 찾지 못해 기존 proxy 값을 사용했습니다."
        pp258_input = pd.DataFrame([{
            "pp252_log": source_log,
            "pp252_stability_log": stability_log,
            "prob_hist35_pp252": direction_probability,
            "resid_huber_pp252": residual,
            "quantile_width": float(row["l10_quantile_width"]),
            "l10_price_range_ratio": float(row["l10_price_range_ratio"]),
            "component_prediction_spread": float(max(component_values) - min(component_values)),
            "confidence_tier": str(row.get("service_confidence_tier") or "low"),
            "svc_group_n": float(row.get("svc_group_n") or 0.0),
        }])
        final = self.pp258.calculate_pp258_predictions(pp258_input).iloc[0]
        final_price = _safe_price(final["final_price"])
        low = _safe_price(row.get("l10_q10_pred_price_krw"))
        high = _safe_price(row.get("l10_q90_pred_price_krw"))
        if final_price and low and high:
            low = min(low, final_price, high)
            high = max(low, final_price, high)
        warm_target_manifest = self.warm_wmin8_manifest or self.warm_wmin4_manifest

        return ReportAdapterResult(
            route="warm",
            execution_level="report_final_layer_proxy",
            price_krw=final_price,
            low_krw=low,
            high_krw=high,
            confidence_tier=str(row.get("service_confidence_tier") or "low"),
            warning_code="WARM_REPORT_PROXY_ADAPTER_APPLIED",
            warning_message=(
                "Warm 신규 입력 계산은 현재 PP258 최종층 proxy adapter로 수행됩니다. "
                "선택된 WMIN8 목표 후보는 운영 후보 산출물로 등록됐지만, "
                "min1 유사작품 통계 SVC와 조건부 라우팅 raw adapter 연결 전이라 "
                "이 응답 가격은 WMIN8 fixed-test 성능을 그대로 재현한 값으로 보지 않습니다."
            ),
            formula=(
                "partial_refreeze_pp258_log = PP258최종층("
                "운영70대30기준로그가격, 운영안정후보로그가격, 저장방향확률, 저장Huber잔차, Quantile폭)"
            ),
            input_columns=list(pp258_input.columns),
            output={
                "source_log_price": source_log,
                "stability_log_price": stability_log,
                "partial_refreeze_adapter_used": self.warm_direction_model is not None and self.warm_huber_residual_model is not None,
                "refreeze_note": refreeze_note,
                "direction_probability": float(pp258_input.iloc[0]["prob_hist35_pp252"]),
                "huber_residual": residual,
                "huber_residual_raw": residual_raw,
                "basis_proxy_residual": residual_proxy,
                "target_warm_candidate_label": str(warm_target_manifest.get("selected_candidate_label") or ""),
                "target_warm_exact_raw_adapter_ready": bool(
                    warm_target_manifest.get("readiness", {}).get("exact_raw_adapter_ready")
                ),
                "raw_correction_log": float(final["raw_correction_log"]),
                "applied_cap_log": float(final["applied_cap_log"]),
                "applied_correction_log": float(final["applied_correction_log"]),
                "final_log_price": float(final["final_price_log"]),
                "final_price_krw": final_price,
            },
            steps=[
                {
                    "name": "운영 Warm 후보 생성",
                    "formula": "운영 70:30 로그가격 = 0.70 * 유사작품통계 로그가격 + 0.30 * 안정 후보 로그가격",
                    "output": {
                        "v01_operational_pred_log": source_log,
                        "pp_v8_stability_pred_log": stability_log,
                    },
                },
                {
                    "name": "Warm 상류 모델 부분 재동결 호출",
                    "formula": "방향확률 = 저장된 방향분류모델(feature), Huber잔차 = 저장된 Huber잔차모델(feature)",
                    "output": {
                        "partial_refreeze_adapter_used": self.warm_direction_model is not None and self.warm_huber_residual_model is not None,
                        "direction_probability": direction_probability,
                        "huber_residual": residual,
                        "huber_residual_raw": residual_raw,
                        "feature_columns": list(warm_model_features.columns),
                    },
                },
                {
                    "name": "PP258 입력 컬럼 구성",
                    "formula": "PP252 기준/안정 후보값은 운영 Warm 후보값으로 임시 매핑하고, 방향/잔차는 저장 모델 출력 사용",
                    "output": pp258_input.iloc[0].to_dict(),
                },
                {
                    "name": "선택된 Warm 목표 후보 상태",
                    "formula": "WMIN8 목표 후보 = min1 유사작품 통계 기준가 + partial Huber residual refit + 조건부 고 SVC 비율 라우팅",
                    "output": {
                        "target_candidate_label": str(warm_target_manifest.get("selected_candidate_label") or ""),
                        "target_artifact_ready": bool(warm_target_manifest),
                        "exact_raw_adapter_ready": bool(
                            warm_target_manifest.get("readiness", {}).get("exact_raw_adapter_ready")
                        ),
                    },
                },
                {
                    "name": "PP258 최종 미세 보정",
                    "formula": "최종로그가격 = 기준로그가격 + clip(원시보정로그값, -동적상한, +동적상한)",
                    "output": {
                        "applied_correction_log": float(final["applied_correction_log"]),
                        "final_price_krw": final_price,
                    },
                },
            ],
        )

    def _wmin8_exact_ready(self) -> bool:
        return bool(
            self.warm_wmin8_exact_manifest
            and self.warm_wmin8_exact_runtime
            and self.warm_wmin8_shrinkage_runtime
            and self.warm_wmin8_shrunk_huber_model is not None
            and self.warm_wmin8_base_model is not None
            and self.warm_wmin8_alternative_model is not None
        )

    def _load_warm_wmin8_feature_store(self) -> pd.DataFrame:
        if not WARM_WMIN8_FEATURE_STORE_PATH.exists():
            return pd.DataFrame()
        store = pd.read_csv(WARM_WMIN8_FEATURE_STORE_PATH, low_memory=False)
        for col in ["source_artwork_id_normalized", "artwork_url_normalized", "artist_key"]:
            if col not in store.columns:
                store[col] = ""
            store[col] = store[col].astype("string").fillna("")
        return store

    def _lookup_warm_wmin8_feature_store_snapshot(
        self,
        request: PriceEstimateRequest,
        artist_key: str | None,
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        status = {"found": False, "lookup_basis": "feature_store_not_available"}
        store = self.warm_wmin8_feature_store
        if store.empty:
            return None, status
        artwork = request.artwork
        url = str(artwork.artwork_url or "").strip()
        if url:
            matched = store[store["artwork_url_normalized"].eq(url)]
            if artist_key:
                exact_artist = matched[matched["artist_key"].astype(str).eq(str(artist_key))]
                if not exact_artist.empty:
                    matched = exact_artist
            if not matched.empty:
                status.update({"found": True, "lookup_basis": "wmin8_feature_store_artwork_url"})
                return matched.iloc[0].to_dict(), status
        source_id = getattr(artwork, "source_artwork_id", None) or getattr(artwork, "external_artwork_id", None)
        if source_id:
            normalized_source_id = _normalize_search_name(source_id)
            matched = store[store["source_artwork_id_normalized"].eq(normalized_source_id)]
            if artist_key:
                exact_artist = matched[matched["artist_key"].astype(str).eq(str(artist_key))]
                if not exact_artist.empty:
                    matched = exact_artist
            if not matched.empty:
                status.update({"found": True, "lookup_basis": "wmin8_feature_store_source_artwork_id"})
                return matched.iloc[0].to_dict(), status
        status["lookup_basis"] = "feature_store_not_found"
        return None, status

    def _wmin8_runtime_row(
        self,
        request: PriceEstimateRequest,
        artist_key: str,
        row: pd.Series,
    ) -> tuple[pd.Series, dict[str, Any]]:
        snapshot, status = self._lookup_warm_wmin8_feature_store_snapshot(request, artist_key)
        if not snapshot:
            return row, status
        merged = row.copy()
        for key, value in snapshot.items():
            if key.endswith("_normalized"):
                continue
            merged[key] = value
        merged["wmin8_feature_store_hit"] = True
        merged["wmin8_feature_store_lookup_basis"] = status["lookup_basis"]
        return merged, status

    @staticmethod
    def _runtime_norm(value: object) -> str:
        text = str(value or "").strip()
        return text if text else "__MISSING__"

    def _wmin8_size_bin(self, area_cm2: float) -> str:
        edges = np.asarray(self.warm_wmin8_shrinkage_runtime.get("size_edges") or [], dtype=float)
        area = float(area_cm2) if math.isfinite(float(area_cm2)) else -1.0
        return str(int(np.digitize(np.nan_to_num(area, nan=-1.0), edges, right=False)))

    def _wmin8_level_keys(self, row: pd.Series) -> dict[str, str]:
        artist_key = self._runtime_norm(row.get("artist_key"))
        medium = self._runtime_norm(row.get("medium_category"))
        support = self._runtime_norm(row.get("support_category"))
        size_bin = self._wmin8_size_bin(_safe_float(row.get("area_cm2"), -1.0))
        return {
            "L1_artist": artist_key,
            "L2_artist_size": "||".join([artist_key, size_bin]),
            "L3_artist_medium_support_size": "||".join([artist_key, medium, support, size_bin]),
        }

    def _wmin8_comparable_priors(self, row: pd.Series) -> tuple[float, float]:
        runtime = self.warm_wmin8_shrinkage_runtime
        groups = runtime.get("groups") or {}
        levels = runtime.get("levels") or ["L1_artist", "L2_artist_size", "L3_artist_medium_support_size"]
        global_median = _safe_float(runtime.get("global_median_log_price"), 0.0)
        raw_min_n = int(runtime.get("raw_min_n") or 5)
        k = _safe_float(runtime.get("shrinkage_k"), 5.0)
        keys = self._wmin8_level_keys(row)

        raw = global_median
        shrunk = global_median
        for level in levels:
            group = (groups.get(level) or {}).get(keys.get(level, ""))
            if not group:
                continue
            median = _safe_float(group.get("median"), global_median)
            count = int(group.get("count") or 0)
            if count >= raw_min_n:
                raw = median
            weight = count / (count + k) if count + k > 0 else 0.0
            shrunk = weight * median + (1.0 - weight) * shrunk
        return float(raw), float(shrunk)

    def _wmin8_shrunk_huber_refit(self, row: pd.Series, shrunk_prior: float) -> float:
        frame = pd.DataFrame(
            [
                {
                    "width_cm": _safe_float(row.get("width_cm"), 0.0),
                    "height_cm": _safe_float(row.get("height_cm"), 0.0),
                    "depth_cm": _safe_float(row.get("depth_cm"), 0.0),
                    "area_cm2": _safe_float(row.get("area_cm2"), 0.0),
                    "log_area": _safe_float(row.get("log_area"), 0.0),
                    "cmp_median": float(shrunk_prior),
                    "medium_category": self._runtime_norm(row.get("medium_category")),
                    "support_category": self._runtime_norm(row.get("support_category")),
                    "medium_support_bucket": self._runtime_norm(row.get("medium_support_bucket")),
                    "artist_key": self._runtime_norm(row.get("artist_key")),
                }
            ]
        )
        return float(np.asarray(self.warm_wmin8_shrunk_huber_model.predict(frame), dtype=float)[0])

    def _wmin8_huber_input(
        self,
        row: pd.Series,
        weight: float,
    ) -> tuple[pd.DataFrame, dict[str, float]]:
        svc_log = _safe_float(
            row.get("svc_numeric_seed_mean_pred_log"),
            _safe_float(row.get("svc_fallback"), 0.0),
        )
        ppv8_log = _safe_float(
            row.get("pp_v8_compact_blend_mape_guarded_pred_log"),
            _safe_float(row.get("ppv8_defensive"), 0.0),
        )
        current_log = float(weight) * svc_log + (1.0 - float(weight)) * ppv8_log
        raw_prior_store = row.get("raw_svc_prior")
        shrunk_prior_store = row.get("shrunk_svc_prior")
        shrunk_huber_store = row.get("shrunk_huber_refit")
        if raw_prior_store is not None and shrunk_prior_store is not None:
            raw_prior = _safe_float(raw_prior_store, np.nan)
            shrunk_prior = _safe_float(shrunk_prior_store, np.nan)
            if not math.isfinite(raw_prior) or not math.isfinite(shrunk_prior):
                raw_prior, shrunk_prior = self._wmin8_comparable_priors(row)
        else:
            raw_prior, shrunk_prior = self._wmin8_comparable_priors(row)
        shrunk_huber = _safe_float(shrunk_huber_store, np.nan)
        if not math.isfinite(shrunk_huber):
            shrunk_huber = self._wmin8_shrunk_huber_refit(row, shrunk_prior)
        values = {
            "current_70_30": current_log,
            "ppv8_defensive": ppv8_log,
            "svc_fallback": svc_log,
            "shrunk_huber_refit": shrunk_huber,
            "shrunk_svc_prior": shrunk_prior,
            "log_area": _safe_float(row.get("log_area"), 0.0),
            "svc_group_n_log": _safe_float(row.get("svc_group_n_log"), 0.0),
            "svc_prior_iqr": _safe_float(row.get("svc_group_log_price_iqr"), 0.0),
            "current_ppv8_gap": current_log - ppv8_log,
            "current_shrunk_huber_gap": current_log - shrunk_huber,
            "raw_shrunk_prior_gap": raw_prior - shrunk_prior,
            "raw_svc_prior": raw_prior,
        }
        feature_columns = self.warm_wmin8_exact_runtime.get("feature_columns") or [
            "ppv8_defensive",
            "svc_fallback",
            "shrunk_huber_refit",
            "shrunk_svc_prior",
            "log_area",
            "svc_group_n_log",
            "svc_prior_iqr",
            "current_ppv8_gap",
            "current_shrunk_huber_gap",
            "raw_shrunk_prior_gap",
        ]
        return pd.DataFrame([{col: values.get(col, 0.0) for col in feature_columns}]), values

    def _wmin8_refit_prediction(
        self,
        row: pd.Series,
        role_name: str,
        model: Any,
    ) -> tuple[float, dict[str, Any]]:
        model_config = (self.warm_wmin8_exact_runtime.get("models") or {}).get(role_name) or {}
        weight = _safe_float(model_config.get("weight"), 0.70)
        feature_frame, feature_values = self._wmin8_huber_input(row, weight)
        raw = float(np.asarray(model.predict(feature_frame), dtype=float)[0])
        stable_config = self.warm_wmin8_exact_runtime.get("stable_config") or {}
        cap = _safe_float(stable_config.get("cap"), 0.05)
        strength = _safe_float(stable_config.get("strength"), 0.5)
        correction = float(np.clip(raw, -cap, cap) * strength)
        pred_log = float(feature_values["current_70_30"] + correction)
        return pred_log, {
            "role": role_name,
            "candidate_label": str(model_config.get("candidate_label") or ""),
            "svc_weight": weight,
            "ppv8_weight": 1.0 - weight,
            "raw_residual_correction_log": raw,
            "applied_residual_correction_log": correction,
            "feature_values": feature_values,
        }

    @staticmethod
    def _wmin8_confidence_tier(row: pd.Series) -> str:
        confidence = str(row.get("confidence_tier") or row.get("service_confidence_tier") or "low")
        return confidence if confidence.endswith("_confidence") else f"{confidence}_confidence"

    def _wmin8_route_decision(
        self,
        row: pd.Series,
        base_log: float,
        alternative_log: float,
    ) -> dict[str, Any]:
        qwidth = _safe_float(row.get("quantile_width"), _safe_float(row.get("l10_quantile_width"), 1.50))
        component_values = [
            _safe_float(row.get("svc_numeric_seed_mean_pred_log"), base_log),
            _safe_float(row.get("l10_generated_bucket_seq_pred_log"), base_log),
            _safe_float(row.get("pp_v2_defensive_pred_log"), base_log),
            _safe_float(row.get("pp_v8_compact_blend_mape_guarded_pred_log"), base_log),
            base_log,
            alternative_log,
        ]
        spread = _safe_float(row.get("component_prediction_spread"), np.nan)
        if not math.isfinite(spread):
            spread = float(max(component_values) - min(component_values))
        ppv8_log = _safe_float(row.get("pp_v8_compact_blend_mape_guarded_pred_log"), base_log)
        gap = _safe_float(row.get("current_vs_stable_gap_abs"), np.nan)
        if not math.isfinite(gap):
            gap = abs(base_log - ppv8_log)
        confidence = self._wmin8_confidence_tier(row)
        price_band = str(row.get("stable_price_band") or "").strip() or _price_band_from_log(ppv8_log)
        risk = float(
            np.clip(
                0.38 * np.clip((qwidth - 1.20) / 0.95, 0.0, 1.0)
                + 0.22 * np.clip(spread / 0.18, 0.0, 1.0)
                + 0.14 * np.clip(gap / 0.06, 0.0, 1.0)
                + 0.16 * (1.0 if confidence == "low_confidence" else 0.0)
                + 0.10 * (1.0 if price_band == "very_high_price" else 0.0),
                0.0,
                1.0,
            )
        )
        gate = self.warm_wmin8_exact_manifest.get("route_gate") or {}
        threshold = _safe_float(gate.get("threshold"), 0.2534165869100283)
        min_gap = _safe_float(gate.get("gap"), 0.005)
        alt_gap = abs(alternative_log - base_log)
        use_alternative = bool(risk >= threshold and alternative_log < base_log and alt_gap >= min_gap)
        return {
            "risk_score": risk,
            "threshold": threshold,
            "minimum_alternative_gap_log": min_gap,
            "alternative_gap_log": alt_gap,
            "alternative_is_lower": bool(alternative_log < base_log),
            "use_alternative": use_alternative,
            "quantile_width": qwidth,
            "component_prediction_spread": spread,
            "current_vs_stable_gap_abs": gap,
            "confidence_tier": confidence,
            "stable_price_band": price_band,
        }

    def _predict_warm_wmin8_exact(
        self,
        request: PriceEstimateRequest,
        artist_key: str,
        row: pd.Series,
        feature_store_status: dict[str, Any] | None = None,
        lookup_feature_store: bool = True,
    ) -> ReportAdapterResult:
        if lookup_feature_store:
            row, feature_store_status = self._wmin8_runtime_row(request, artist_key, row)
        if feature_store_status is None:
            feature_store_status = {"found": False, "lookup_basis": "not_checked"}
        base_log, base_detail = self._wmin8_refit_prediction(row, "base_w700", self.warm_wmin8_base_model)
        alt_log, alt_detail = self._wmin8_refit_prediction(row, "alternative_w850", self.warm_wmin8_alternative_model)
        route = self._wmin8_route_decision(row, base_log, alt_log)
        final_log = alt_log if route["use_alternative"] else base_log
        final_price = _safe_price(math.exp(final_log))
        low = _safe_price(row.get("l10_q10_pred_price_krw"))
        high = _safe_price(row.get("l10_q90_pred_price_krw"))
        if final_price and low and high:
            low = min(low, final_price, high)
            high = max(low, final_price, high)
        selected_role = "alternative_w850" if route["use_alternative"] else "base_w700"
        return ReportAdapterResult(
            route="warm",
            execution_level="report_model_adapter",
            price_krw=final_price,
            low_krw=low,
            high_krw=high,
            confidence_tier=str(row.get("service_confidence_tier") or "low"),
            warning_code="WARM_WMIN8_EXACT_ADAPTER_APPLIED",
            warning_message=(
                "5건 이상 이력 기반 Warm 경로에 WMIN8 runtime adapter를 적용했습니다. "
                "WMIN8은 기본 70% SVC 후보와 85% SVC 방어 후보를 각각 계산한 뒤, "
                "위험 점수와 후보 간 차이에 따라 더 낮은 방어 후보로 라우팅합니다."
            ),
            formula=(
                "WMIN8 로그가격 = if(risk_score >= threshold and alt < base - 0.005) "
                "then 85% SVC Huber 후보 else 70% SVC Huber 후보"
            ),
            input_columns=list((self.warm_wmin8_exact_runtime.get("feature_columns") or [])),
            output={
                "selected_wmin8_candidate_label": str(
                    self.warm_wmin8_exact_manifest.get("selected_wmin8_candidate_label") or ""
                ),
                "selected_runtime_role": selected_role,
                "base_log_price": base_log,
                "alternative_log_price": alt_log,
                "final_log_price": final_log,
                "final_price_krw": final_price,
                "route_gate": route,
                "base_detail": base_detail,
                "alternative_detail": alt_detail,
                "fixed_test_feature_store": feature_store_status,
                "runtime_manifest_status": str(self.warm_wmin8_exact_manifest.get("status") or ""),
            },
            steps=[
                {
                    "name": "WMIN8 기본 후보 계산",
                    "formula": "기본 후보 = 0.70 * min1 SVC 로그가격 + 0.30 * PPV8 로그가격 + Huber 잔차 보정",
                    "output": {
                        "candidate_label": base_detail["candidate_label"],
                        "pred_log": base_log,
                        "pred_price_krw": _safe_price(math.exp(base_log)),
                        "applied_residual_correction_log": base_detail["applied_residual_correction_log"],
                    },
                },
                {
                    "name": "WMIN8 방어 후보 계산",
                    "formula": "방어 후보 = 0.85 * min1 SVC 로그가격 + 0.15 * PPV8 로그가격 + Huber 잔차 보정",
                    "output": {
                        "candidate_label": alt_detail["candidate_label"],
                        "pred_log": alt_log,
                        "pred_price_krw": _safe_price(math.exp(alt_log)),
                        "applied_residual_correction_log": alt_detail["applied_residual_correction_log"],
                    },
                },
                {
                    "name": "WMIN8 조건부 라우팅",
                    "formula": "risk_score >= 0.2534165869 AND alternative < base AND |alternative-base| >= 0.005",
                    "output": route,
                },
                {
                    "name": "최종 Warm 가격",
                    "formula": "최종가격 = exp(선택된 WMIN8 로그가격)",
                    "output": {
                        "selected_runtime_role": selected_role,
                        "final_log_price": final_log,
                        "final_price_krw": final_price,
                    },
                },
            ],
        )

    def predict_warm_lite(self, request: PriceEstimateRequest, artist_key: str) -> ReportAdapterResult:
        frame = self._build_warm_lite_feature_frame(request)
        history = self._build_warm_lite_artist_history(artist_key)
        pred = self.warm_lite.predict(
            frame,
            history,
            models=self.warm_lite_models,
            params=self.warm_lite_params,
        ).iloc[0]
        final_price = _safe_price(pred["warm_lite_pred_price_krw"])
        history_n = int(pred["artist_history_n"])
        if final_price:
            if history_n == 1:
                low = _safe_price(final_price * 0.45)
                high = _safe_price(final_price * 1.90)
            else:
                low = _safe_price(final_price * 0.65)
                high = _safe_price(final_price * 1.55)
        else:
            low = None
            high = None
        confidence = "low" if history_n == 1 else "medium"
        return ReportAdapterResult(
            route="warm_lite",
            execution_level="report_model_adapter",
            price_krw=final_price,
            low_krw=low,
            high_krw=high,
            confidence_tier=confidence,
            warning_code="WARM_LITE_MODEL_ADAPTER_APPLIED",
            warning_message=(
                "같은 작가 가격 이력 1~4건 전용 Warm-lite 모델을 적용했습니다. "
                "이력 수가 적기 때문에 k=1은 넓은 범위와 검수 플래그를 권장합니다."
            ),
            formula="Warm-lite 로그가격 = Huber앙상블(작품조건 + 같은작가 1~4건 이력 통계 + 비작가 fallback 통계)",
            input_columns=list(frame.columns) + ["artist_history_1_to_4"],
            output={
                "warm_lite_pred_log": float(pred["warm_lite_pred_log"]),
                "warm_lite_pred_price_krw": final_price,
                "artist_history_n": history_n,
                "confidence_grade": str(pred["confidence_grade"]),
                "display_policy": str(pred["display_policy"]),
                "range_low_krw": low,
                "range_high_krw": high,
            },
            steps=[
                {
                    "name": "Warm-lite 입력 피처 생성",
                    "formula": "작품 피처 = 크기/면적/비율/재료/지지체/size bucket/medium-support bucket",
                    "output": frame.iloc[0].to_dict(),
                },
                {
                    "name": "같은 작가 저이력 통계 생성",
                    "formula": "작가 이력 1~4건에서 동일 재료·크기 -> 동일 크기 -> 작가 전체 순서로 중앙값/IQR 통계 계산",
                    "output": {
                        "artist_key": artist_key,
                        "artist_history_n": history_n,
                        "history_price_median": float(history["ln_price_krw"].median()),
                        "history_rows": history[["ln_price_krw", "medium_support_bucket", "size_bucket"]].to_dict(orient="records"),
                    },
                },
                {
                    "name": "Warm-lite Huber 앙상블",
                    "formula": "최종 로그가격 = mean(Huber_1...Huber_6)",
                    "output": {
                        "warm_lite_pred_log": float(pred["warm_lite_pred_log"]),
                        "final_price_krw": final_price,
                        "confidence_grade": str(pred["confidence_grade"]),
                    },
                },
            ],
        )

    def predict_cold(self, request: PriceEstimateRequest, artist_key: str | None) -> ReportAdapterResult:
        frame, search_status, external_status = self._build_cold_refreeze_feature_frame(request, artist_key)
        feature_store_hit = bool(external_status.get("cold_feature_store_hit"))
        if feature_store_hit:
            feature_input_mode = "row_feature_store_replay"
        elif search_status["found"] and external_status["found"]:
            feature_input_mode = "service_search_external_cache"
        elif search_status["found"]:
            feature_input_mode = "service_search_cache"
        elif external_status["found"]:
            feature_input_mode = "service_external_cache"
        else:
            feature_input_mode = "service_default_missing"
        refreeze_ready = (
            all(model is not None for model in self.cold_y2_models.values())
            and self.cold_qr1_q40_model is not None
            and bool(self.cold_y16_segment_map)
        )
        if refreeze_ready:
            y2_q10 = float(np.asarray(self.cold_y2_models["q10"].predict(frame), dtype=float)[0])
            y2_q50 = float(np.asarray(self.cold_y2_models["q50"].predict(frame), dtype=float)[0])
            y2_q90 = float(np.asarray(self.cold_y2_models["q90"].predict(frame), dtype=float)[0])
            q40 = float(np.asarray(self.cold_qr1_q40_model.predict(frame), dtype=float)[0])
            qwidth = max(y2_q90 - y2_q10, 0.0)
            representative_log = self._apply_cold_y16_segment_correction(y2_q50, qwidth)
            low_price = _safe_price(np.exp(y2_q10))
            high_price = _safe_price(np.exp(y2_q90))
            refreeze_note = "저장된 Cold LightGBM Quantile, q40, qwidth segment 보정 모델을 호출했습니다."
        else:
            raw_frame = self._build_cold_feature_frame(request)
            v02 = self.cold_v02.predict(raw_frame, models=self.cold_v02_models, guard=self.cold_v02_guard)
            row = v02.iloc[0]
            representative_log = float(row["representative_pred_log"])
            q40 = float(row["q40_pred_log"])
            qwidth = float(row["qwidth_log"])
            low_price = _safe_price(row.get("range_low_price_krw"))
            high_price = _safe_price(row.get("range_high_price_krw"))
            refreeze_note = "저장된 Cold 상류 모델을 찾지 못해 기존 v0.2 proxy 값을 사용했습니다."
        lookup_key = artist_key or self._cold_fallback_artist_key(request)
        v03_input = pd.DataFrame([{
            "y18_qwidth_pred_log": representative_log,
            "lgb_q40_pred_log": q40,
            "quantile_width_log": qwidth,
            "artist_key": lookup_key,
        }])
        final = self.cold_v03.apply(v03_input, params=self.cold_v03_params, lookup=self.cold_v03_lookup).iloc[0]
        final_price = _safe_price(final["cold_defense_pred_price_krw"])
        low = low_price
        high = high_price
        if final_price and low and high:
            low = min(low, final_price, high)
            high = max(low, final_price, high)

        search_covered = bool(final["search_covered"])
        qwidth_q67 = float(self.cold_v03_params["guard"]["qwidth_q67"])
        confidence = "medium" if search_covered and qwidth < qwidth_q67 else "low"
        return ReportAdapterResult(
            route="cold",
            execution_level="report_final_layer_proxy",
            price_krw=final_price,
            low_krw=low,
            high_krw=high,
            confidence_tier=confidence,
            warning_code="COLD_REPORT_PROXY_ADAPTER_APPLIED",
            warning_message=(
                "Cold 보고서 v0.3 guard+search 후처리층을 raw 입력 호환 adapter로 적용했습니다. "
                "저장된 Cold LightGBM Quantile 상류 후보를 호출하지만, "
                "row-level feature store가 적중하면 실험 입력 피처를 재사용하고, "
                "신규 입력은 공식 v0.1 DB snapshot과 작가 단위 전시/갤러리 cache를 적용하며 없으면 missing/default로 채웁니다."
            ),
            formula=(
                "partial_refreeze_cold_log = v0.3후처리("
                "저장LightGBMQuantile대표로그가격, 저장LightGBM_q40로그가격, Quantile폭, 작가검색보정lookup)"
            ),
            input_columns=list(v03_input.columns),
            output={
                "partial_refreeze_adapter_used": refreeze_ready,
                "refreeze_note": refreeze_note,
                "cold_feature_input_mode": feature_input_mode,
                "search_feature_pipeline_ready": search_status["found"],
                "search_feature_snapshot_id": search_status["snapshot_id"],
                "search_feature_lookup_basis": search_status["lookup_basis"],
                "external_feature_pipeline_ready": external_status["found"],
                "external_feature_lookup_basis": external_status["lookup_basis"],
                "external_feature_row_count": external_status["row_count"],
                "external_feature_preview": external_status.get("feature_preview"),
                "cold_feature_store_hit": bool(external_status.get("cold_feature_store_hit")),
                "representative_log_price": representative_log,
                "lightgbm_q40_log_price": q40,
                "quantile_width_log": qwidth,
                "search_lookup_artist_key": lookup_key,
                "search_covered": search_covered,
                "search_delta_log": float(final["search_delta_applied"]),
                "guard_search_final_log_price": float(final["cold_defense_pred_log"]),
                "final_price_krw": final_price,
            },
            steps=[
                {
                    "name": "Cold 상류 모델 부분 재동결 호출",
                    "formula": "q10/q50/q90 = 저장 LightGBM Quantile(작품조건+작가메타+검색피처+전시/갤러리피처), q40 = 저장 LightGBM Quantile(작품조건)",
                    "output": {
                        "partial_refreeze_adapter_used": refreeze_ready,
                        "cold_feature_input_mode": feature_input_mode,
                        "search_feature_pipeline_ready": search_status["found"],
                        "search_feature_snapshot_id": search_status["snapshot_id"],
                        "search_feature_lookup_basis": search_status["lookup_basis"],
                        "external_feature_pipeline_ready": external_status["found"],
                        "external_feature_lookup_basis": external_status["lookup_basis"],
                        "external_feature_row_count": external_status["row_count"],
                        "external_feature_preview": external_status.get("feature_preview"),
                        "cold_feature_store_hit": bool(external_status.get("cold_feature_store_hit")),
                        "q40_pred_log": q40,
                        "q50_pred_log": representative_log,
                        "qwidth_log": qwidth,
                    },
                },
                {
                    "name": "v0.3 guard+search 입력 매핑",
                    "formula": "대표로그가격=q50, 방어기준=q40, 검색보정키=artist_key",
                    "output": v03_input.iloc[0].to_dict(),
                },
                {
                    "name": "Cold v0.3 후처리",
                    "formula": "최종로그가격 = guard(대표, q40, 폭) + search_delta_lookup[artist_key]",
                    "output": {
                        "search_covered": search_covered,
                        "search_delta_log": float(final["search_delta_applied"]),
                        "final_price_krw": final_price,
                    },
                },
            ],
        )

    @staticmethod
    def _to_operational_v01_request(request: PriceEstimateRequest, artist_key: str) -> op1s.PriceEstimateRequest:
        artwork = request.artwork
        return op1s.PriceEstimateRequest(
            artwork=op1s.ArtworkInput(
                external_artwork_id=None,
                title=artwork.title,
                artist=op1s.ArtistInput(
                    artist_key=artist_key,
                    name_ko=artwork.artist.name_ko,
                    name_en=artwork.artist.name_en,
                ),
                year=artwork.year,
                dimensions=op1s.Dimensions(
                    width_cm=artwork.dimensions.width_cm,
                    height_cm=artwork.dimensions.height_cm,
                    depth_cm=artwork.dimensions.depth_cm,
                ),
                medium=op1s.Medium(
                    medium_category=artwork.medium.medium_category or "unknown",
                    support_category=artwork.medium.support_category or "unknown",
                ),
                category=artwork.category,
                artwork_url=artwork.artwork_url,
            ),
            options=op1s.PriceEstimateOptions(
                currency="KRW",
                include_comparable_samples=False,
                max_comparable_samples=0,
            ),
        )

    def _build_warm_lite_feature_frame(self, request: PriceEstimateRequest) -> pd.DataFrame:
        frame = self._build_cold_feature_frame(request)
        required = list(self.warm_lite.REQUIRED)
        missing = [col for col in required if col not in frame.columns]
        if missing:
            raise ValueError(f"warm_lite target feature missing: {missing}")
        return frame[required].copy()

    def _build_warm_lite_artist_history(self, artist_key: str) -> pd.DataFrame:
        with sqlite3.connect(self.db_path) as conn:
            rows = pd.read_sql_query(
                """
                SELECT price_krw, log_price_krw, width_cm, height_cm, depth_cm,
                       area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate,
                       medium_category, support_category, medium_support_bucket
                FROM artwork_price_observations
                WHERE artist_key = ?
                  AND price_krw IS NOT NULL
                  AND price_krw > 0
                  AND area_cm2 IS NOT NULL
                  AND area_cm2 > 0
                ORDER BY price_krw DESC
                """,
                conn,
                params=(artist_key,),
            )
        if not 1 <= len(rows) <= 4:
            raise ValueError(f"Warm-lite artist history must be 1~4 rows, got {len(rows)}")
        base = rows.copy()
        base["ln_price_krw"] = pd.to_numeric(base["log_price_krw"], errors="coerce")
        missing_log = base["ln_price_krw"].isna()
        if missing_log.any():
            base.loc[missing_log, "ln_price_krw"] = np.log(pd.to_numeric(base.loc[missing_log, "price_krw"], errors="coerce"))
        base["depth_cm"] = pd.to_numeric(base["depth_cm"], errors="coerce").fillna(0.0)
        if "medium_support_bucket" not in base.columns or base["medium_support_bucket"].isna().any():
            base["medium_support_bucket"] = (
                base["medium_category"].fillna("unknown").astype(str)
                + "__"
                + base["support_category"].fillna("unknown").astype(str)
            )
        featured = feature_ops.add_bucket_features(base, self.warm_runtime.feature_generation, "cold")
        required = ["ln_price_krw", "log_area", "medium_support_bucket", "size_bucket", "medium_category", "support_category"]
        missing = [col for col in required if col not in featured.columns]
        if missing:
            raise ValueError(f"warm_lite history feature missing: {missing}")
        return featured[required].copy()

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
            "medium_category": artwork.medium.medium_category or "unknown",
            "support_category": artwork.medium.support_category or "unknown",
        }])
        base["medium_support_bucket"] = (
            base["medium_category"].fillna("unknown").astype(str)
            + "__"
            + base["support_category"].fillna("unknown").astype(str)
        )
        return feature_ops.add_bucket_features(base, self.warm_runtime.feature_generation, "cold")

    def _build_warm_refreeze_features(
        self,
        row: pd.Series,
        source_log: float,
        stability_log: float,
        component_values: list[float],
    ) -> pd.DataFrame:
        qwidth = float(row.get("l10_quantile_width") or 0.0)
        price_range = float(row.get("l10_price_range_ratio") or 0.0)
        svc_n = float(row.get("svc_group_n") or 0.0)
        spread = float(max(component_values) - min(component_values))
        gap = abs(stability_log - source_log)
        area = float(row.get("area_cm2") or 0.0)
        confidence = str(row.get("service_confidence_tier") or "low")
        if not confidence.endswith("_confidence"):
            confidence = f"{confidence}_confidence"
        risk = np.clip(
            0.25 * _rank_like(qwidth, 2.0)
            + 0.20 * _rank_like(math.log(max(price_range, 1.0)), 2.5)
            + 0.20 * _rank_like(spread, 1.2)
            + 0.18 * _rank_like(gap, 0.8)
            + 0.09 * (1.0 if "low" in confidence else 0.0)
            + 0.08 * np.clip((10.0 - svc_n) / 10.0, 0.0, 1.0),
            0.0,
            1.0,
        )
        feature = {
            "stable_price_band": _price_band_from_log(source_log),
            "confidence_tier": confidence,
            "qwidth_band": _qwidth_band(qwidth),
            "medium_support_bucket": str(row.get("medium_support_bucket") or "__MISSING__"),
            "svc_group_n_band": _svc_group_n_band(svc_n),
            "area_bin": _area_bin(area),
            "quantile_width": qwidth,
            "l10_price_range_ratio": price_range,
            "svc_group_n": svc_n,
            "component_prediction_spread": spread,
            "current_vs_stable_gap_abs": gap,
            "gap_operational_abs": gap,
            "gap_mape_abs": gap,
            "gap_guarded_abs": gap,
            "gap_recovery_abs": gap,
            "row_risk_operational": risk,
            "row_risk_mape": risk,
            "row_risk_guarded": risk,
            "row_risk_recovery": risk,
            "pp246_minus_pp234_abs": gap,
            "p95_recovery_delta_abs": gap,
            "operational_delta_abs": gap,
            "p95_guarded_delta_abs": gap,
            "p95_extreme_delta_abs": gap,
            "pp246_log_centered": source_log - math.log(10_000_000),
            "qwidth_rank": _rank_like(qwidth, 2.0),
            "component_spread_rank": _rank_like(spread, 1.2),
            "model_gap_rank": _rank_like(gap, 0.8),
        }
        columns = self.warm_refreeze_schema.get("feature_columns") or list(feature.keys())
        return pd.DataFrame([{col: feature.get(col, 0.0) for col in columns}])

    def _build_cold_refreeze_feature_frame(
        self,
        request: PriceEstimateRequest,
        artist_key: str | None,
    ) -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
        frame = self._build_cold_feature_frame(request).copy()
        artist_key = str(artist_key or "").strip() or None
        features = self.cold_refreeze_schema.get("pp_y2_feature_columns") or list(getattr(self.cold_y2_models.get("q50"), "feature_names_in_", []))
        exact_snapshot, exact_status = self._lookup_cold_feature_store_snapshot(request, artist_key)
        if exact_snapshot:
            exact_frame = pd.DataFrame([{col: exact_snapshot.get(col, np.nan) for col in features}])
            search_found = _safe_float(exact_snapshot.get("search_collected_flag"), 0.0) > 0
            external_found = (
                _safe_float(exact_snapshot.get("gallery_tier_any_available_flag"), 0.0) > 0
                or _safe_float(exact_snapshot.get("artist_exhibition_available_count"), 0.0) > 0
            )
            search_status = {
                "found": search_found,
                "snapshot_id": str(exact_snapshot.get("_track6_row_id") or ""),
                "lookup_basis": exact_status["lookup_basis"],
                "cold_feature_store_hit": True,
            }
            external_status = {
                "found": external_found,
                "lookup_basis": exact_status["lookup_basis"],
                "row_count": 1,
                "cold_feature_store_hit": True,
                "feature_preview": {
                    "artist_exhibition_available_count": _safe_float(exact_snapshot.get("artist_exhibition_available_count"), 0.0),
                    "artist_exhibition_total_count": _safe_float(exact_snapshot.get("artist_exhibition_total_count"), 0.0),
                    "gallery_tier_any_available_flag": _safe_float(exact_snapshot.get("gallery_tier_any_available_flag"), 0.0),
                    "gallery_feature_source": str(exact_snapshot.get("gallery_feature_source") or "missing"),
                },
            }
            return _normalize_model_input_frame(exact_frame), search_status, external_status
        record = self.warm_runtime.artist_records.get(artist_key or "") if artist_key else None
        birth_year = float(record.birth_year) if record and record.birth_year else np.nan
        total_works = float(record.valid_training_label_count) if record else np.nan
        nationality = record.nationality if record and record.nationality else "__MISSING__"
        for col, value in {
            "artist_meta_birth_year": birth_year,
            "artist_meta_total_works": total_works,
            "artist_meta_for_sale_works": np.nan,
            "artist_meta_followers": np.nan,
            "artist_meta_for_sale_ratio": np.nan,
            "artist_meta_career_stage": (2026.0 - birth_year) if math.isfinite(birth_year) else np.nan,
            "artist_meta_source": "service_artist_registry" if record else "__MISSING__",
            "artist_meta_nationality": nationality,
            "artist_meta_nationality_ko": nationality,
            "artist_meta_is_p1_flag": 0.0,
            "artist_meta_has_international_flag": 0.0,
            "is_high_price_candidate_flag": 0.0,
        }.items():
            frame[col] = value
        for col in ["artist_meta_birth_year", "artist_meta_total_works", "artist_meta_for_sale_works", "artist_meta_followers", "artist_meta_career_stage"]:
            frame[f"{col}_missing"] = pd.to_numeric(frame[col], errors="coerce").isna().astype(float)
        frame["artist_meta_total_works_log"] = _safe_log1p(frame.iloc[0].get("artist_meta_total_works"))
        frame["artist_meta_for_sale_works_log"] = _safe_log1p(frame.iloc[0].get("artist_meta_for_sale_works"))
        frame["artist_meta_followers_log"] = _safe_log1p(frame.iloc[0].get("artist_meta_followers"))

        search_snapshot, search_status = self._lookup_search_snapshot(request, artist_key)
        search_defaults = {
            "search_result_count": 0.0,
            "search_source_count": 0.0,
            "search_art_context_count": 0.0,
            "search_exhibition_context_count": 0.0,
            "search_gallery_context_count": 0.0,
            "search_award_institution_context_count": 0.0,
            "search_social_context_count": 0.0,
            "search_market_context_count": 0.0,
            "search_homonym_context_count": 0.0,
            "search_art_match_ratio": 0.0,
            "search_exhibition_ratio": 0.0,
            "search_source_ratio": 0.0,
            "search_quality_score": 0.0,
            "search_collected_flag": 0.0,
            "search_success_flag": 0.0,
        }
        for col, value in search_defaults.items():
            frame[col] = value
        if search_snapshot:
            for col in search_defaults:
                if col in search_snapshot:
                    frame[col] = _safe_float(search_snapshot.get(col), 0.0)
            for col in ["search_quality_grade", "search_homonym_risk_grade"]:
                frame[col] = str(search_snapshot.get(col) or "missing")
        frame["search_result_count_log"] = _safe_log1p(frame.iloc[0].get("search_result_count"))
        frame["search_art_context_count_log"] = _safe_log1p(frame.iloc[0].get("search_art_context_count"))
        frame["search_exhibition_context_count_log"] = _safe_log1p(frame.iloc[0].get("search_exhibition_context_count"))
        frame["search_source_count_log"] = _safe_log1p(frame.iloc[0].get("search_source_count"))
        frame["search_quality_x_log_area"] = 0.0
        frame["search_art_match_x_followers_log"] = 0.0
        frame["search_exhibition_x_career_stage"] = 0.0
        if not search_snapshot:
            frame["search_quality_grade"] = "missing"
            frame["search_homonym_risk_grade"] = "missing"
        frame["search_size_quality_bucket"] = frame["size_bucket"].astype(str) + "__missing"
        frame["search_source_ratio"] = _safe_float(search_snapshot.get("search_source_ratio"), 0.0) if search_snapshot else 0.0
        frame["search_quality_x_log_area"] = pd.to_numeric(frame["search_quality_score"], errors="coerce").fillna(0.0) * pd.to_numeric(frame["log_area"], errors="coerce").fillna(0.0)
        frame["search_art_match_x_followers_log"] = pd.to_numeric(frame["search_art_match_ratio"], errors="coerce").fillna(0.0) * pd.to_numeric(frame["artist_meta_followers_log"], errors="coerce").fillna(0.0)
        frame["search_exhibition_x_career_stage"] = pd.to_numeric(frame["search_exhibition_ratio"], errors="coerce").fillna(0.0) * pd.to_numeric(frame["artist_meta_career_stage"], errors="coerce").fillna(0.0)
        frame["search_size_quality_bucket"] = frame["size_bucket"].astype(str) + "__" + frame["search_quality_grade"].astype(str)

        external_snapshot, external_status = self._lookup_external_feature_snapshot(request, artist_key)
        for col in [
            "artist_exhibition_solo_count",
            "artist_exhibition_group_count",
            "artist_exhibition_fair_count",
            "artist_exhibition_total_count",
            "gallery_tier_raw_numeric",
            "gallery_tier_validated_score",
            "gallery_city_count",
        ]:
            frame[col] = np.nan
        for col in ["artist_exhibition_solo_count", "artist_exhibition_group_count", "artist_exhibition_fair_count"]:
            frame[f"{col}_missing"] = 1.0
            frame[f"{col}_log"] = 0.0
        frame["artist_exhibition_available_count"] = 0.0
        frame["artist_exhibition_total_count_log"] = 0.0
        frame["gallery_tier_raw_available_flag"] = 0.0
        frame["gallery_tier_validated_available_flag"] = 0.0
        frame["gallery_tier_any_available_flag"] = 0.0
        frame["gallery_city_count_log"] = 0.0
        frame["gallery_tier_raw_bucket"] = "__MISSING__"
        frame["gallery_tier_validated"] = "__MISSING__"
        frame["gallery_ref_type"] = "__MISSING__"
        frame["gallery_audit_status"] = "__MISSING__"
        frame["gallery_feature_source"] = "missing"
        if external_snapshot:
            numeric_cols = [
                "artist_exhibition_solo_count",
                "artist_exhibition_group_count",
                "artist_exhibition_fair_count",
                "artist_exhibition_total_count",
                "gallery_tier_raw_numeric",
                "gallery_tier_validated_score",
                "gallery_city_count",
                "artist_exhibition_available_count",
                "artist_exhibition_solo_count_missing",
                "artist_exhibition_group_count_missing",
                "artist_exhibition_fair_count_missing",
                "artist_exhibition_solo_count_log",
                "artist_exhibition_group_count_log",
                "artist_exhibition_fair_count_log",
                "artist_exhibition_total_count_log",
                "gallery_tier_raw_available_flag",
                "gallery_tier_validated_available_flag",
                "gallery_tier_any_available_flag",
                "gallery_city_count_log",
            ]
            for col in numeric_cols:
                if col in external_snapshot:
                    frame[col] = _safe_float(external_snapshot.get(col), 0.0)
            for col in [
                "gallery_tier_raw_bucket",
                "gallery_tier_validated",
                "gallery_ref_type",
                "gallery_audit_status",
                "gallery_feature_source",
            ]:
                if col in external_snapshot:
                    value = external_snapshot.get(col)
                    frame[col] = str(value) if value not in [None, ""] else "__MISSING__"
        self._apply_external_feature_interactions(frame)

        out = frame.reindex(columns=features)
        return _normalize_model_input_frame(out), search_status, external_status

    def _load_cold_feature_store(self) -> pd.DataFrame:
        if not COLD_FEATURE_STORE_PATH.exists():
            return pd.DataFrame()
        store = pd.read_csv(COLD_FEATURE_STORE_PATH, low_memory=False)
        for col in ["artist_key_normalized", "artist_name_ko_normalized", "source_artwork_id_normalized", "artwork_url_normalized"]:
            if col not in store.columns:
                store[col] = ""
            store[col] = store[col].astype("string").fillna("")
        return store

    def _lookup_cold_feature_store_snapshot(self, request: PriceEstimateRequest, artist_key: str | None) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        status = {"found": False, "lookup_basis": "feature_store_not_available"}
        store = self.cold_feature_store
        if store.empty:
            return None, status
        artwork = request.artwork
        url = str(artwork.artwork_url or "").strip()
        if url:
            matched = store[store["artwork_url_normalized"].eq(url)]
            if not matched.empty:
                status.update({"found": True, "lookup_basis": "cold_feature_store_artwork_url"})
                return matched.iloc[0].to_dict(), status
        source_id = getattr(artwork, "source_artwork_id", None) or getattr(artwork, "external_artwork_id", None)
        if source_id:
            normalized_source_id = _normalize_search_name(source_id)
            matched = store[store["source_artwork_id_normalized"].eq(normalized_source_id)]
            if not matched.empty:
                status.update({"found": True, "lookup_basis": "cold_feature_store_source_artwork_id"})
                return matched.iloc[0].to_dict(), status
        status["lookup_basis"] = "feature_store_not_found"
        return None, status

    def _load_external_feature_cache(self) -> pd.DataFrame:
        if not COLD_EXTERNAL_FEATURE_CACHE_PATH.exists():
            return pd.DataFrame()
        cache = pd.read_csv(COLD_EXTERNAL_FEATURE_CACHE_PATH, low_memory=False)
        for col in ["artist_name_ko_normalized", "artist_name_en_normalized"]:
            if col not in cache.columns:
                cache[col] = ""
            cache[col] = cache[col].map(_valid_normalized_search_name).astype("string").fillna("")
        if "artist_key" not in cache.columns:
            cache["artist_key"] = ""
        cache["artist_key"] = cache["artist_key"].astype("string").fillna("")
        return cache

    def _lookup_external_feature_snapshot(self, request: PriceEstimateRequest, artist_key: str | None) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        status = {"found": False, "lookup_basis": "not_available", "row_count": 0}
        cache = self.cold_external_feature_cache
        if cache.empty:
            status["lookup_basis"] = "cache_missing"
            return None, status
        artist_key = str(artist_key or "").strip() or None
        row = None
        if artist_key:
            matched = cache[cache["artist_key"].astype(str).eq(str(artist_key))]
            if not matched.empty:
                row = matched.iloc[0]
                status["lookup_basis"] = "artist_key"
        if row is None:
            artist = request.artwork.artist
            normalized_names = [
                _valid_normalized_search_name(value)
                for value in [artist.name_ko, artist.name_en]
                if _valid_normalized_search_name(value)
            ]
            if normalized_names:
                mask = cache["artist_name_ko_normalized"].isin(normalized_names) | cache["artist_name_en_normalized"].isin(normalized_names)
                matched = cache[mask]
                if not matched.empty:
                    row = matched.iloc[0]
                    status["lookup_basis"] = "normalized_artist_name"
        if row is None:
            status["lookup_basis"] = "external_cache_not_found"
            return None, status
        data = row.to_dict()
        status["found"] = True
        status["row_count"] = int(_safe_float(data.get("external_feature_row_count"), 0.0))
        status["feature_preview"] = {
            "artist_exhibition_available_count": _safe_float(data.get("artist_exhibition_available_count"), 0.0),
            "artist_exhibition_total_count": _safe_float(data.get("artist_exhibition_total_count"), 0.0),
            "gallery_tier_any_available_flag": _safe_float(data.get("gallery_tier_any_available_flag"), 0.0),
            "gallery_feature_source": str(data.get("gallery_feature_source") or "missing"),
        }
        return data, status

    @staticmethod
    def _apply_external_feature_interactions(frame: pd.DataFrame) -> None:
        total_log = pd.to_numeric(frame["artist_exhibition_total_count_log"], errors="coerce").fillna(0.0)
        total_count = float(pd.to_numeric(frame["artist_exhibition_total_count"], errors="coerce").fillna(0.0).iloc[0])
        log_area = pd.to_numeric(frame["log_area"], errors="coerce").fillna(0.0)
        followers_log = pd.to_numeric(frame.get("artist_meta_followers_log"), errors="coerce").fillna(0.0)
        tier_score = pd.to_numeric(frame["gallery_tier_validated_score"], errors="coerce").fillna(0.0)
        frame["exhibition_total_x_log_area"] = total_log * log_area
        frame["exhibition_total_x_followers_log"] = total_log * followers_log
        frame["gallery_validated_x_followers_log"] = tier_score * followers_log
        frame["gallery_tier_x_exhibition_total_log"] = tier_score * total_log
        if total_count <= 0:
            exhibition_bucket = "none"
        elif total_count <= 3:
            exhibition_bucket = "low"
        elif total_count <= 8:
            exhibition_bucket = "mid"
        else:
            exhibition_bucket = "high"
        frame["exhibition_size_bucket"] = frame["size_bucket"].astype(str) + "__" + exhibition_bucket
        frame["gallery_exhibition_bucket"] = frame["gallery_feature_source"].astype(str) + "__" + exhibition_bucket

    def _lookup_search_snapshot(self, request: PriceEstimateRequest, artist_key: str | None) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        status = {"found": False, "snapshot_id": None, "lookup_basis": "not_available"}
        if not self.db_path.exists():
            status["lookup_basis"] = "db_missing"
            return None, status
        artist_key = str(artist_key or "").strip() or None
        artist = request.artwork.artist
        names = [
            artist.name_ko,
            artist.name_en,
        ]
        normalized_names = [_valid_normalized_search_name(name) for name in names if _valid_normalized_search_name(name)]
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = None
            if artist_key:
                row = conn.execute(
                    """
                    SELECT *
                    FROM artist_search_feature_snapshots
                    WHERE artist_key = ?
                    ORDER BY search_collected_flag DESC, search_quality_score DESC, created_at DESC
                    LIMIT 1
                    """,
                    (artist_key,),
                ).fetchone()
                if row:
                    status["lookup_basis"] = "artist_key"
            if row is None and normalized_names:
                row = conn.execute(
                    f"""
                    SELECT *
                    FROM artist_search_feature_snapshots
                    WHERE artist_search_name_normalized IN ({",".join("?" for _ in normalized_names)})
                    ORDER BY search_collected_flag DESC, search_quality_score DESC, created_at DESC
                    LIMIT 1
                    """,
                    tuple(normalized_names),
                ).fetchone()
                if row:
                    status["lookup_basis"] = "normalized_artist_name"
        if row is None:
            status["lookup_basis"] = "snapshot_not_found"
            return None, status
        data = dict(row)
        raw = data.get("raw_feature_json")
        if raw:
            try:
                raw_data = json.loads(str(raw))
                data.update(raw_data)
            except json.JSONDecodeError:
                pass
        status["found"] = True
        status["snapshot_id"] = data.get("search_snapshot_id")
        return data, status

    def _apply_cold_y16_segment_correction(self, q50_log: float, qwidth_log: float) -> float:
        segment_map = self.cold_y16_segment_map.get("correction_map") or {}
        edges = ((self.cold_y16_segment_map.get("bin_config") or {}).get("qwidth_edges") or [])
        idx = 0
        numeric_edges = []
        for raw in edges:
            if raw == "-Infinity":
                numeric_edges.append(float("-inf"))
            elif raw == "Infinity":
                numeric_edges.append(float("inf"))
            else:
                numeric_edges.append(float(raw))
        for i in range(max(len(numeric_edges) - 1, 0)):
            if numeric_edges[i] <= qwidth_log < numeric_edges[i + 1]:
                idx = i
                break
        correction = float(segment_map.get(f"w{idx}", self.cold_y16_segment_map.get("global_correction", 0.0)))
        cap = float((self.cold_refreeze_schema.get("pp_y16_segment_policy") or {}).get("cap", 0.25))
        return float(q50_log + np.clip(correction, -cap, cap))

    @staticmethod
    def _cold_fallback_artist_key(request: PriceEstimateRequest) -> str:
        artist = request.artwork.artist
        raw = artist.artist_key or artist.selected_artist_key or artist.name_en or artist.name_ko or "unknown_artist"
        return str(raw).strip().lower().replace("-", " ") or "unknown_artist"
