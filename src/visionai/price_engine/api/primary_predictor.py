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

    def load_models(self, model_dir: Path) -> None:
        """v3-filtered-tuned 모델 로드 — fail-closed + schema 검증 (Codex 12차).

        Required artifacts (모두 필수, 누락 또는 schema invalid 시 RuntimeError):
        - integrated_v3_filtered_tuned_catboost.cbm
        - integrated_v3_filtered_tuned_xgboost.json
        - integrated_v3_filtered_tuned_xgboost_label_maps.json
            · dict[str, dict[str, int]] schema 검증 (CAT_FEATURES 7개 모두 존재)
        - integrated_v3_filtered_tuned_warm_artists.json
            · 'warm_artist_slugs' key 존재 + list 타입 검증

        Build new state in local vars first, then swap to instance state at end.
        중간 실패 시 instance state는 이전 값 그대로 유지.

        Note (Codex 11차 P2 ack): 진짜 thread-safe atomicity 아님 (no lock).
        현재 _load_models는 startup-only 호출이라 race 위험 적음.
        런타임 reload 도입 시 별도 lock 필요.
        """
        # 1) artifact 경로 — 모두 필수
        cb_path = model_dir / "integrated_v3_filtered_tuned_catboost.cbm"
        xgb_path = model_dir / "integrated_v3_filtered_tuned_xgboost.json"
        warm_path = model_dir / "integrated_v3_filtered_tuned_warm_artists.json"
        label_maps_path = model_dir / "integrated_v3_filtered_tuned_xgboost_label_maps.json"

        for path, label in (
            (cb_path, "CatBoost model"),
            (xgb_path, "XGBoost model"),
            (warm_path, "warm artists"),
            (label_maps_path, "XGBoost label maps"),
        ):
            if not path.exists():
                raise RuntimeError(
                    f"{label} artifact 미존재: {path} — fail-closed (학습/서빙 정합 보장 불가)"
                )

        # 2) 모든 state를 local vars에 build + schema 검증
        new_cb = CatBoostRegressor()
        new_cb.load_model(str(cb_path))

        new_xgb = xgb.Booster()
        new_xgb.load_model(str(xgb_path))

        with warm_path.open(encoding="utf-8") as f:
            warm_data = json.load(f)
        if not isinstance(warm_data, dict) or "warm_artist_slugs" not in warm_data:
            raise RuntimeError(
                f"warm artifact schema invalid ({warm_path}): 'warm_artist_slugs' key 필요"
            )
        slugs_list = warm_data["warm_artist_slugs"]
        if not isinstance(slugs_list, list):
            raise RuntimeError(
                f"warm artifact schema invalid ({warm_path}): 'warm_artist_slugs' must be list"
            )
        new_warm_slugs: set[str] = {str(s) for s in slugs_list}
        new_warm_loaded = True

        with label_maps_path.open(encoding="utf-8") as f:
            new_label_maps = json.load(f)
        if not isinstance(new_label_maps, dict):
            raise RuntimeError(
                f"label_maps schema invalid ({label_maps_path}): must be dict"
            )
        # Codex 13차 P2: schema 검증을 predict() 요구사항과 정합 — non-empty + int values
        for col in CAT_FEATURES:
            if col not in new_label_maps:
                raise RuntimeError(
                    f"label_maps schema invalid ({label_maps_path}): '{col}' key 누락 "
                    f"(CAT_FEATURES={CAT_FEATURES})"
                )
            cat_map = new_label_maps[col]
            if not isinstance(cat_map, dict):
                raise RuntimeError(
                    f"label_maps schema invalid ({label_maps_path}): "
                    f"'{col}' value must be dict[str, int]"
                )
            if not cat_map:
                raise RuntimeError(
                    f"label_maps schema invalid ({label_maps_path}): "
                    f"'{col}' mapping is empty — predict() requires non-empty"
                )
            # inner value 타입 검증 (int 외 타입은 sentinel encoding 시 astype(float) 실패)
            for k, v in cat_map.items():
                if not isinstance(v, int):
                    raise RuntimeError(
                        f"label_maps schema invalid ({label_maps_path}): "
                        f"'{col}[{k!r}]' value must be int, got {type(v).__name__}"
                    )

        # 3) 모든 build + 검증 성공 시 instance state로 swap
        self.cb_model = new_cb
        self.xgb_model = new_xgb
        self._warm_artist_slugs = new_warm_slugs
        self._warm_artifact_loaded = new_warm_loaded
        self._label_maps = new_label_maps

        # 4) 로깅
        logger.info("CatBoost loaded: %s", cb_path)
        logger.info("XGBoost loaded: %s", xgb_path)
        logger.info("Warm artists loaded: %d (학습 시 warm slice 작가)", len(new_warm_slugs))
        logger.info("XGBoost label maps loaded: %d categories",
                    sum(len(v) for v in new_label_maps.values() if isinstance(v, dict)))

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
        Codex 13차 P1: categorical normalization을 학습과 일치 (nan/None → 'unknown').
        """
        # 피처 DataFrame 생성 — 학습 train_primary_market_v3_filtered.py:120과 동일 정규화
        df = pd.DataFrame([features])
        for col in CAT_FEATURES:
            if col in df.columns:
                df[col] = df[col].astype(str).fillna("unknown").replace(
                    {"nan": "unknown", "None": "unknown"}
                )

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
            # Codex 12차 P1: 학습 시 _label_encode_xgb와 동일하게 unseen=sentinel(len(mapping)) 사용.
            # 런타임에 mapping을 mutate하지 않음 — artifact가 권위적이며 새 ID 추가는 ID shift 위험.
            df_xgb = df[CB_FEATURES].copy()
            for col in CAT_FEATURES:
                mapping = self._label_maps.get(col, {})
                if not mapping:
                    raise RuntimeError(
                        f"label_maps에 카테고리 '{col}' 없음 — artifact 손상 (load_models 시점에 검증됐어야 함)"
                    )
                unseen_idx = len(mapping)  # train script와 동일 sentinel
                df_xgb[col] = df_xgb[col].map(lambda v, m=mapping, u=unseen_idx: m.get(str(v), u)).astype(float)

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

    # build_xgb_label_maps 제거 (Codex 11차):
    # 학습은 Artsy+Saatchi 합본 + warm 필터로 label_maps 빌드. 서버 fallback이
    # 동일 데이터 합본을 보장하기 어려워 폐기. label_maps.json artifact가 필수.
    # load_models()에서 fail-closed 처리.
