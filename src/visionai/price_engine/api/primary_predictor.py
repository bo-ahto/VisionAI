"""Phase 1 모델 라우팅 + 예측."""
from __future__ import annotations

import json
import math
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
import xgboost as xgb

logger = logging.getLogger(__name__)

USD_TO_KRW = 1380

RATIO_CORRECTION = {
    "gallery": 0.0,
    "online": -0.075,
}

CB_FEATURES = [
    "ho", "ho_power", "ln_ho", "area_cm2", "ln_area", "aspect_ratio", "is_small",
    "support_factor", "ho_x_support",
    "is_unique", "is_edition", "has_depth",
    "artist_birth_year", "has_birth_year", "career_stage",
    "ln_followers", "artist_total_works", "for_sale_ratio",
    "ho_price_level", "medium_price_level",
    "profile_completeness",
    "gallery_tier", "gallery_city_count", "has_seoul", "has_international",
    "is_krw",
    "support_type", "medium_category", "attribution_class",
    "gallery_name", "gallery_type", "price_currency", "source",
]
# Removed (Codex 4차 리뷰 P1, 2026-04-28):
# - career_age, work_age, vintage_premium, freshness_discount
#   학습 데이터는 정상 계산, 서빙은 0 하드코딩 (artist_matcher/feature_builder).
#   모델이 활용 중이라 (importance: career_age 2.0, vintage 1.5, work_age 0.4 XGB gain)
#   학습/서빙 드리프트 → offline metric ≠ serving accuracy. 제거로 정렬 보장.

CAT_FEATURES = [
    "support_type", "medium_category", "attribution_class",
    "gallery_name", "gallery_type", "price_currency", "source",
]


def determine_confidence(
    is_matched: bool,
    training_count: int,
    has_birth_year: bool,
    has_manual_profile: bool,
    is_warm_artist: bool | None = None,
) -> tuple[str, float]:
    """(grade, margin) 반환.

    Codex 7차 P1 (2026-04-28): is_warm_artist tri-state (True/False/None).
    - None: warm set 정보 미보유 → 구 legacy fallback (training_count >= 5)
    - True: 학습 시 warm slice 포함 → A 등급
    - False: 학습 시 warm slice 미포함 (set 권위적) → A 부여 X (B 이하)
      → 라우팅(CatBoost)과 grade가 일관되게 정합

    이전 6차 fix는 is_warm=False일 때도 training_count fallback이 열려 있어
    warm set 외부 + DB training_count>=5인 작가가 CatBoost+A 모순 발생.
    """
    # warm set authoritative branch
    if is_warm_artist is True:
        if is_matched:
            return ("A", 0.20)
        # 매칭 안 됐는데 warm 표기? 이론상 발생 X — 안전하게 fallthrough
    if is_warm_artist is False:
        # warm set 권위적: 매칭 됐으면 B 이하 (A 부여 X)
        if is_matched and training_count >= 1:
            return ("B", 0.30)
        if has_birth_year or has_manual_profile:
            return ("C", 0.50)
        return ("D", 0.70)
    # is_warm_artist is None — 구 legacy fallback (warm set 미보유 환경)
    if is_matched and training_count >= 5:
        return ("A", 0.20)
    if is_matched and training_count >= 1:
        return ("B", 0.30)
    if has_birth_year or has_manual_profile:
        return ("C", 0.50)
    return ("D", 0.70)


class PrimaryPredictor:
    """CatBoost + XGBoost 모델 라우팅."""

    def __init__(self) -> None:
        self.cb_model: CatBoostRegressor | None = None
        self.xgb_model: xgb.Booster | None = None
        self._label_maps: dict[str, dict[str, int]] = {}
        # Codex 5차 P1: 학습 시 저장된 warm artist set (서빙 라우팅 정합)
        self._warm_artist_slugs: set[str] = set()
        # Codex 9차 P1: artifact 로드 여부 별도 플래그 — set 비어있음과 미로드 구분
        self._warm_artifact_loaded: bool = False

    def load_models(self, model_dir: Path, training_data_path: Path | None = None) -> None:
        """v3-filtered-tuned 모델 로드 — atomic-ish (Codex 10차 P2).

        Build new state in local vars first, then atomically swap to instance state.
        중간 실패 시 instance state는 이전 값 그대로 유지.

        Aritfacts:
        - CatBoost: 입체 985건 제외 + Optuna 30 trials 튜닝 (cold start GroupKFold)
        - XGBoost: 입체 제외 + warm slice(작품 수≥5) Optuna 튜닝 (warm KFold)
        - label_maps: 학습 시 매핑 그대로 보존된 아티팩트 (warm slice 기준)
        - warm_artists: 학습 시 warm slice에 포함된 작가 slug 집합
        """
        # 1) 모든 state를 local vars에 build (instance에 아직 안 씀)
        cb_path = model_dir / "integrated_v3_filtered_tuned_catboost.cbm"
        xgb_path = model_dir / "integrated_v3_filtered_tuned_xgboost.json"
        warm_path = model_dir / "integrated_v3_filtered_tuned_warm_artists.json"
        label_maps_path = model_dir / "integrated_v3_filtered_tuned_xgboost_label_maps.json"

        new_cb = CatBoostRegressor()
        new_cb.load_model(str(cb_path))

        new_xgb = xgb.Booster()
        new_xgb.load_model(str(xgb_path))

        new_warm_slugs: set[str] = set()
        new_warm_loaded = False
        if warm_path.exists():
            with warm_path.open(encoding="utf-8") as f:
                data = json.load(f)
            new_warm_slugs = set(data.get("warm_artist_slugs", []))
            new_warm_loaded = True

        new_label_maps: dict[str, dict[str, int]] = {}
        if label_maps_path.exists():
            with label_maps_path.open(encoding="utf-8") as f:
                new_label_maps = json.load(f)
        elif training_data_path and training_data_path.exists():
            # warm slice 필터 fallback (Codex 10차 P1): warm-only XGBoost와 일치
            import pandas as pd_local
            df = pd_local.read_parquet(training_data_path)
            if "is_excluded_for_training" in df.columns:
                df = df[df["is_excluded_for_training"] == 0].copy()
            if new_warm_loaded and new_warm_slugs and "artist_slug" in df.columns:
                df = df[df["artist_slug"].astype(str).isin(new_warm_slugs)].copy()
            for col in CAT_FEATURES:
                if col in df.columns:
                    vals = df[col].astype(str).unique()
                    new_label_maps[col] = {v: i for i, v in enumerate(sorted(vals))}
        else:
            raise RuntimeError(
                f"label_maps.json 미존재 ({label_maps_path}) and training_data_path 미제공 — "
                "warm XGBoost categorical ID 일관성 보장 불가"
            )

        # 2) 모든 build 성공 시에만 instance state에 atomic swap
        self.cb_model = new_cb
        self.xgb_model = new_xgb
        self._warm_artist_slugs = new_warm_slugs
        self._warm_artifact_loaded = new_warm_loaded
        self._label_maps = new_label_maps

        # 3) 로깅
        logger.info("CatBoost loaded: %s", cb_path)
        logger.info("XGBoost loaded: %s", xgb_path)
        if new_warm_loaded:
            logger.info("Warm artists loaded: %d (학습 시 warm slice 작가)", len(new_warm_slugs))
        else:
            logger.warning("Warm artist list 없음 — DB training_count로 fallback (라우팅 불일치 위험)")
        if label_maps_path.exists():
            logger.info("XGBoost label maps loaded from artifact: %s", label_maps_path)
        else:
            logger.warning("XGBoost label maps fallback path 사용 (ID shift 위험)")

    def is_warm_artist(self, artist_slug: str | None) -> bool:
        """학습 시 warm slice 정의를 그대로 사용 (라우팅 정합)."""
        if not artist_slug or not self._warm_artist_slugs:
            return False
        return str(artist_slug) in self._warm_artist_slugs

    def predict(
        self,
        features: dict,
        is_matched: bool,
        training_count: int,
        target_market: str = "gallery",
        has_manual_profile: bool = False,
        artist_slug: str | None = None,
    ) -> dict:
        """예측 수행. dict로 결과 반환.

        라우팅 (Codex 5차 P1 정렬): warm_artist_slugs lookup 우선,
        없으면 fallback으로 DB training_count >= 5.
        """
        # 피처 DataFrame 생성
        df = pd.DataFrame([features])
        for col in CAT_FEATURES:
            if col in df.columns:
                df[col] = df[col].astype(str).fillna("unknown")

        # 모델 라우팅 (학습 시 warm slice와 정합) — Codex 9차 P1 정합 강화
        # _warm_artifact_loaded 플래그로 'loaded(empty 포함)' vs 'not loaded' 구분
        # loaded면 권위적: slug 누락 = cold, set 외부 = cold
        # 라우팅 + grade 양쪽에서 같은 결정 사용 (self-consistency 보장)
        if self._warm_artifact_loaded:
            is_warm = bool(artist_slug) and self.is_warm_artist(artist_slug)
            use_xgb = bool(is_matched) and is_warm  # 매칭 + warm 둘 다 필요
        else:
            is_warm = None  # warm set 미로드 → grade도 legacy fallback
            use_xgb = is_matched and training_count >= 5
        model_type = "xgboost_v3_filtered_tuned" if use_xgb else "catboost_v3_filtered_tuned"

        if use_xgb:
            # XGBoost는 categorical을 label encoding
            df_xgb = df[CB_FEATURES].copy()
            for col in CAT_FEATURES:
                if col not in self._label_maps:
                    self._label_maps[col] = {}
                mapping = self._label_maps[col]
                for val in df_xgb[col].unique():
                    if val not in mapping:
                        mapping[val] = len(mapping)
                df_xgb[col] = df_xgb[col].map(mapping).astype(float)

            dmat = xgb.DMatrix(df_xgb)
            ln_price = float(self.xgb_model.predict(dmat)[0])
        else:
            X = df[CB_FEATURES]
            ln_price = float(self.cb_model.predict(X)[0])

        # Source ratio 보정 (Cold Start만)
        if not use_xgb:
            correction = RATIO_CORRECTION.get(target_market, 0.0)
            ln_price += correction

        price_krw = int(math.exp(ln_price))
        price_usd = int(price_krw / USD_TO_KRW)

        # 신뢰도 (Codex 6차 P1: is_warm_artist로 라우팅과 grade 정렬)
        has_birth = bool(features.get("artist_birth_year") and not math.isnan(features["artist_birth_year"]))
        grade, margin = determine_confidence(
            is_matched, training_count, has_birth, has_manual_profile,
            is_warm_artist=is_warm,
        )

        price_low = int(price_krw * (1 - margin))
        price_high = int(price_krw * (1 + margin))

        return {
            "price_krw": price_krw,
            "price_usd": price_usd,
            "price_range_low": price_low,
            "price_range_high": price_high,
            "confidence_grade": grade,
            "margin": margin,
            "model_type": model_type,
            "is_known_artist": is_matched,
            "training_count": training_count,
        }

    def build_xgb_label_maps(
        self,
        training_data_path: Path | None = None,
        label_maps_path: Path | None = None,
    ) -> None:
        """XGBoost label encoding 매핑 구축.

        우선순위 (Codex 10차 P1):
        1. label_maps_path JSON 아티팩트 — 학습 시 사용된 매핑 그대로 보존 (필수)
        2. training_data_path + warm artist set 필터 — XGBoost가 warm-only로 학습되므로
           full parquet으로 fallback하면 categorical ID shift 발생 (warm vs full
           sorted unique 순서가 다름 → 'attribution_class', 'gallery_name' 등 ID mismatch)

        Codex 10차 P1: warm-slice 학습 도입으로 full parquet fallback이 invalid.
        warm_artifact_loaded일 때는 warm artist set으로 parquet을 필터링해서 매핑 빌드.
        """
        if label_maps_path and label_maps_path.exists():
            with label_maps_path.open(encoding="utf-8") as f:
                self._label_maps = json.load(f)
            logger.info("XGBoost label maps loaded from artifact: %s", label_maps_path)
            return
        # Fallback path: warm slice 정합 보장
        if training_data_path and training_data_path.exists():
            df = pd.read_parquet(training_data_path)
            # is_excluded_for_training 적용 (production train과 동일)
            if "is_excluded_for_training" in df.columns:
                df = df[df["is_excluded_for_training"] == 0].copy()
            # warm artifact 로드된 경우 warm slice로 필터 (XGBoost 학습 정합)
            if self._warm_artifact_loaded and self._warm_artist_slugs and "artist_slug" in df.columns:
                df = df[df["artist_slug"].astype(str).isin(self._warm_artist_slugs)].copy()
                logger.info("XGBoost label maps fallback: warm slice 필터 적용 (%d rows)", len(df))
            else:
                logger.warning(
                    "XGBoost label maps fallback: warm artifact 미로드 — full parquet 사용 (ID shift 위험)"
                )
            for col in CAT_FEATURES:
                if col in df.columns:
                    vals = df[col].astype(str).unique()
                    self._label_maps[col] = {v: i for i, v in enumerate(sorted(vals))}
            logger.info("XGBoost label maps built from %s", training_data_path)
            return
        # 학습 시 사용된 값 하드코딩 (마지막 fallback — 운영에서는 발생 X)
        logger.error(
            "XGBoost label maps: artifact + parquet 모두 없음 → 하드코딩 default 사용 "
            "(ID shift 위험 — warm 예측 신뢰 불가)"
        )
        self._label_maps = {
            "support_type": {v: i for i, v in enumerate(sorted(
                ["canvas", "linen", "metal", "other", "panel", "paper", "silk"]))},
            "medium_category": {v: i for i, v in enumerate(sorted(
                ["acrylic", "ink", "mixed", "oil", "other", "pastel", "pencil", "pigment", "watercolor"]))},
            "attribution_class": {v: i for i, v in enumerate(sorted(
                ["Limited edition", "Unique", "Unknown edition"]))},
            "gallery_name": {},  # 동적 할당
            "gallery_type": {v: i for i, v in enumerate(sorted(
                ["Gallery", "Online Gallery", "Unknown"]))},
            "price_currency": {v: i for i, v in enumerate(sorted(
                ["KRW", "USD"]))},
            "source": {v: i for i, v in enumerate(sorted(
                ["artsy", "artsy_artue", "manual", "printbakery", "saatchi"]))},
        }
