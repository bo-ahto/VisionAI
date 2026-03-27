"""Ablation 재현 Test — 피처 그룹 제거 시 MAPE 변화.

기획서 참조: 9장 #7
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor

from visionai.price_engine.models.predictor import BASELINE_FEATURES, prepare_features
from visionai.price_engine.validation.metrics import compute_metrics

logger = logging.getLogger(__name__)

# 피처 그룹 정의
ABLATION_GROUPS: dict[str, list[str]] = {
    "추정가 3종": ["ln_estimate_mid", "estimate_ratio", "estimate_range"],
    "작가 통계 3종": ["artist_total_sold", "artist_avg_price", "artist_max_price"],
    "크기 4종": ["height_cm", "width_cm", "surface_area", "aspect_ratio"],
}


def run_ablation(
    model: CatBoostRegressor,
    df: pd.DataFrame,
    y_true: np.ndarray,
) -> pd.DataFrame:
    """각 피처 그룹을 0으로 마스킹한 후 MAPE 변화를 측정한다.

    Note: CatBoost 모델을 재학습하지 않고 입력값만 0으로 치환하여
    해당 피처 그룹의 기여도를 근사 측정한다 (permutation 기반은 아님).

    Returns:
        DataFrame: group, baseline_mape, ablated_mape, delta_mape
    """
    X_base = prepare_features(df)
    y_base_log = model.predict(X_base)
    y_base = np.exp(y_base_log)
    base_metrics = compute_metrics(y_true, y_base)

    rows = []
    for group_name, feature_names in ABLATION_GROUPS.items():
        X_ablated = X_base.copy()
        for feat in feature_names:
            if feat in X_ablated.columns:
                X_ablated[feat] = 0

        y_abl_log = model.predict(X_ablated)
        y_abl = np.exp(y_abl_log)
        abl_metrics = compute_metrics(y_true, y_abl)

        delta = round(abl_metrics.mape - base_metrics.mape, 2)
        rows.append({
            "group": group_name,
            "baseline_mape": base_metrics.mape,
            "ablated_mape": abl_metrics.mape,
            "delta_mape": delta,
        })
        logger.info(
            "Ablation [%s]: MAPE %.2f → %.2f (Δ%+.2f)",
            group_name, base_metrics.mape, abl_metrics.mape, delta,
        )

    return pd.DataFrame(rows)
