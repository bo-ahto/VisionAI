"""SHAP 기반 피처 기여도 설명."""
from __future__ import annotations

import logging
import math

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

_explainer = None
_base_value = None


def init_explainer(model) -> None:
    """CatBoost 모델로 TreeExplainer 초기화."""
    global _explainer, _base_value
    try:
        import shap
        _explainer = shap.TreeExplainer(model)
        _base_value = float(_explainer.expected_value)
        logger.info("SHAP explainer initialized (base=%.3f)", _base_value)
    except Exception as e:
        logger.warning("SHAP init failed: %s", e)


def explain(features_df: pd.DataFrame, feature_names: list[str]) -> list[dict]:
    """피처 기여도 계산. 상위 5개 반환.

    Returns:
        [{"feature": "artist_total_works", "value": 120, "contribution": "+15.2%"}, ...]
    """
    if _explainer is None:
        return []

    try:
        shap_values = _explainer.shap_values(features_df)
        if shap_values.ndim == 1:
            vals = shap_values
        else:
            vals = shap_values[0]

        # SHAP 값을 % 기여도로 변환 (log scale → % 영향)
        contribs = []
        for i, (feat, shap_val) in enumerate(zip(feature_names, vals)):
            raw_value = features_df.iloc[0, i]
            # ln_price 변화량 → % 변화
            pct = (math.exp(shap_val) - 1) * 100
            contribs.append({
                "feature": feat,
                "value": _format_value(feat, raw_value),
                "contribution": f"{pct:+.1f}%",
                "shap_raw": round(float(shap_val), 4),
            })

        # 절대값 기준 상위 5개
        contribs.sort(key=lambda x: -abs(x["shap_raw"]))
        return contribs[:5]

    except Exception as e:
        logger.warning("SHAP explain failed: %s", e)
        return []


def _format_value(feature: str, value) -> str:
    """피처 값을 사람이 읽기 좋은 형태로."""
    if pd.isna(value):
        return "N/A"
    if isinstance(value, (float, np.floating)):
        if feature in ("artist_birth_year",):
            return str(int(value)) if not math.isnan(value) else "N/A"
        if abs(value) > 100:
            return f"{value:,.0f}"
        return f"{value:.2f}"
    return str(value)
