"""모델 추론 모듈.

CatBoost 모델을 로드하고 예측을 수행한다.
기획서 참조: 5.1
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor


# baseline 모델의 정확한 피처 순서
BASELINE_FEATURES: list[str] = [
    "artist_clean", "medium_category", "support_category", "타입",
    "is_3d", "is_untitled",
    "ln_estimate_mid", "estimate_ratio", "estimate_range",
    "height_cm", "width_cm", "surface_area", "aspect_ratio",
    "Lot", "회차",
    "artist_total_sold", "artist_avg_price", "artist_max_price",
    "artist_sell_rate",  # baseline 모델에 포함 (importance=0, 0으로 채움)
    "is_size_imputed", "is_year_missing", "is_new_artist",
]

CAT_FEATURE_INDICES: list[int] = [0, 1, 2, 3, 4, 5]


def load_model(model_path: str | Path) -> CatBoostRegressor:
    """CatBoost 모델을 로드한다."""
    model = CatBoostRegressor()
    model.load_model(str(model_path))
    return model


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """DataFrame에서 모델 입력 피처를 추출하고 순서를 맞춘다.

    baseline 모델의 artist_sell_rate는 0으로 채운다 (전량 낙찰 데이터).
    """
    out = df.copy()

    # artist_sell_rate: baseline 모델에 포함되어 있으나 importance=0
    # 전량 낙찰 데이터에서 계산 불가 → 0으로 채움
    if "artist_sell_rate" not in out.columns:
        out["artist_sell_rate"] = 0.0

    # bool → str 변환 (CatBoost 범주형)
    for col in ["is_3d", "is_untitled"]:
        if col in out.columns:
            out[col] = out[col].astype(str)

    # 피처 순서 맞추기
    missing = [c for c in BASELINE_FEATURES if c not in out.columns]
    if missing:
        msg = f"Missing features: {missing}"
        raise ValueError(msg)

    return out[BASELINE_FEATURES]


def predict(
    model: CatBoostRegressor,
    df: pd.DataFrame,
) -> np.ndarray:
    """log-price 예측 → 원래 스케일(원)로 복원한다.

    Returns:
        예측 낙찰가 (원 단위) ndarray.
    """
    X = prepare_features(df)
    y_log_pred = model.predict(X)
    return np.exp(y_log_pred)
