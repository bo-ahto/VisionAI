"""Strict / Distilled 2-트랙 피처 분리 설정.

Phase 5 기획서 참조:
- Strict: train/infer 모두 estimate-derived signal 없음
- Distilled: infer 시 estimate 없음, train 시 teacher/external estimate aggregate 허용
"""
from __future__ import annotations

from enum import Enum

from visionai.price_engine.estimate_generator.hedonic_features import HEDONIC_FEATURES


class Track(str, Enum):
    """2-트랙 구분."""

    STRICT = "strict"
    DISTILLED = "distilled"


# Strict 트랙: 추정가 파생 신호 일체 금지
# Phase 3 hedonic 49개에서 estimate 관련 제외 (현재 HEDONIC_FEATURES에 estimate 없음)
_ESTIMATE_DERIVED = {
    "global_estimate_avg",
    "teacher_pred_oof",
    "ln_estimate_mid",
    "estimate_ratio",
    "estimate_range",
    "estimate_mid",
}

STRICT_FEATURES: list[str] = [
    f for f in HEDONIC_FEATURES if f not in _ESTIMATE_DERIVED
]

# Distilled 트랙: Strict + teacher soft target (train only)
DISTILLED_TRAIN_ONLY_FEATURES: list[str] = [
    "teacher_pred_oof",
    "global_estimate_avg",
]

# Inference 피처: 두 트랙 모두 동일 (추정가/teacher 신호 없음)
INFERENCE_FEATURES: list[str] = STRICT_FEATURES


def get_distilled_train_features() -> list[str]:
    """Distilled 트랙의 전체 학습 피처 반환.

    = STRICT_FEATURES + DISTILLED_TRAIN_ONLY_FEATURES
    """
    return STRICT_FEATURES + DISTILLED_TRAIN_ONLY_FEATURES
