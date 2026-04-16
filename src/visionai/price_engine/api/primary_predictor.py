"""Phase 1 모델 라우팅 + 예측."""
from __future__ import annotations

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
    "is_unique", "is_edition", "work_age", "has_depth",
    "artist_birth_year", "has_birth_year", "career_age", "career_stage",
    "ln_followers", "artist_total_works", "for_sale_ratio",
    "ho_price_level", "medium_price_level",
    "profile_completeness",
    "gallery_tier", "gallery_city_count", "has_seoul", "has_international",
    "is_krw", "vintage_premium", "freshness_discount",
    "support_type", "medium_category", "attribution_class",
    "gallery_name", "gallery_type", "price_currency", "source",
]

CAT_FEATURES = [
    "support_type", "medium_category", "attribution_class",
    "gallery_name", "gallery_type", "price_currency", "source",
]


def determine_confidence(
    is_matched: bool,
    training_count: int,
    has_birth_year: bool,
    has_manual_profile: bool,
) -> tuple[str, float]:
    """(grade, margin) 반환."""
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

    def load_models(self, model_dir: Path) -> None:
        cb_path = model_dir / "integrated_v3_catboost.cbm"
        xgb_path = model_dir / "integrated_v3_xgboost.json"

        self.cb_model = CatBoostRegressor()
        self.cb_model.load_model(str(cb_path))
        logger.info("CatBoost loaded: %s", cb_path)

        self.xgb_model = xgb.Booster()
        self.xgb_model.load_model(str(xgb_path))
        logger.info("XGBoost loaded: %s", xgb_path)

    def predict(
        self,
        features: dict,
        is_matched: bool,
        training_count: int,
        target_market: str = "gallery",
        has_manual_profile: bool = False,
    ) -> dict:
        """예측 수행. dict로 결과 반환."""
        # 피처 DataFrame 생성
        df = pd.DataFrame([features])
        for col in CAT_FEATURES:
            if col in df.columns:
                df[col] = df[col].astype(str).fillna("unknown")

        # 모델 라우팅
        use_xgb = is_matched and training_count >= 5
        model_type = "xgboost_v3" if use_xgb else "catboost_v3"

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

        # 신뢰도
        has_birth = bool(features.get("artist_birth_year") and not math.isnan(features["artist_birth_year"]))
        grade, margin = determine_confidence(is_matched, training_count, has_birth, has_manual_profile)

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

    def build_xgb_label_maps(self, training_data_path: Path | None = None) -> None:
        """학습 데이터에서 XGBoost label encoding 매핑 구축."""
        if training_data_path and training_data_path.exists():
            df = pd.read_parquet(training_data_path)
            for col in CAT_FEATURES:
                if col in df.columns:
                    vals = df[col].astype(str).unique()
                    self._label_maps[col] = {v: i for i, v in enumerate(sorted(vals))}
            logger.info("XGBoost label maps built from %s", training_data_path)
