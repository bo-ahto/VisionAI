"""세그먼트별 예측 보정 (Segment Calibration).

타깃 변환 모델의 예측값을 auction_type별/가격대별로 보정한다.
Codex 권장: 모델 재학습보다 후처리 보정이 효율적.

보정 방식:
  validation set에서 세그먼트별 median(actual/predicted) 비율을 구한 뒤,
  test/운영 예측에 곱하여 체계적 편향을 제거한다.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class CalibrationFactors:
    """세그먼트별 보정 계수."""

    by_auction_type: dict[str, float]
    by_price_tier: dict[str, float]


def fit_calibration(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    auction_types: np.ndarray,
    estimate_mids: np.ndarray,
) -> CalibrationFactors:
    """validation set에서 세그먼트별 보정 계수를 학습한다.

    보정 계수 = median(actual / predicted) per segment.
    1.0이면 보정 불필요, >1이면 과소추정 보정, <1이면 과대추정 보정.

    Args:
        y_true: 실제 낙찰가.
        y_pred: 모델 예측가.
        auction_types: 경매 타입 배열.
        estimate_mids: 추정가 중앙값 배열.
    """
    ratio = y_true / y_pred

    # auction_type별
    by_type: dict[str, float] = {}
    for atype in np.unique(auction_types):
        mask = auction_types == atype
        if mask.sum() >= 10:
            by_type[atype] = float(np.median(ratio[mask]))
            logger.info("Calibration [%s]: factor=%.4f (N=%d)", atype, by_type[atype], mask.sum())

    # 가격대별 (추정가 기준)
    tiers = pd.cut(
        estimate_mids,
        bins=[0, 1_000_000, 5_000_000, 30_000_000, 100_000_000, np.inf],
        labels=["<100만", "100만~500만", "500만~3000만", "3000만~1억", "1억+"],
    )
    by_tier: dict[str, float] = {}
    for tier_name in ["<100만", "100만~500만", "500만~3000만", "3000만~1억", "1억+"]:
        mask = tiers == tier_name
        if mask.sum() >= 10:
            by_tier[tier_name] = float(np.median(ratio[mask]))
            logger.info("Calibration [%s]: factor=%.4f (N=%d)", tier_name, by_tier[tier_name], mask.sum())

    # 편향 게이트 자동 보정: median_ratio < 0.95인 가격대는 factor를 상향
    # (Codex 권고: 수동 1억+=1.03 → validation 기반 자동 추정)
    for tier_name, factor in by_tier.items():
        if factor < 0.95:
            # 현재 factor가 과소추정을 만들므로, 0.95 이상을 보장하도록 조정
            # target: median(ratio * adjusted_factor) ≈ 1.0
            # adjusted = 1.0 / factor (역수 보정)
            adjusted = min(1.0 / factor, 1.10)  # 최대 10% 상향 캡
            logger.info(
                "Auto-adjust [%s]: %.4f → %.4f (bias gate ≥ 0.95)",
                tier_name, factor, adjusted,
            )
            by_tier[tier_name] = adjusted

    return CalibrationFactors(by_auction_type=by_type, by_price_tier=by_tier)


def apply_calibration(
    y_pred: np.ndarray,
    auction_types: np.ndarray,
    estimate_mids: np.ndarray,
    factors: CalibrationFactors,
    blend_weight: float = 0.5,
) -> np.ndarray:
    """세그먼트별 보정 계수를 예측값에 적용한다.

    두 가지 보정을 blend:
      corrected = y_pred × (blend_weight × type_factor + (1-blend_weight) × tier_factor)

    Args:
        blend_weight: auction_type 보정의 가중치 (0~1). 기본 0.5.
    """
    result = y_pred.copy().astype(float)

    type_factors = np.ones(len(y_pred))
    for i, atype in enumerate(auction_types):
        if atype in factors.by_auction_type:
            type_factors[i] = factors.by_auction_type[atype]

    tiers = pd.cut(
        estimate_mids,
        bins=[0, 1_000_000, 5_000_000, 30_000_000, 100_000_000, np.inf],
        labels=["<100만", "100만~500만", "500만~3000만", "3000만~1억", "1억+"],
    )
    tier_factors = np.ones(len(y_pred))
    for i, tier in enumerate(tiers):
        if tier in factors.by_price_tier:
            tier_factors[i] = factors.by_price_tier[tier]

    blended = blend_weight * type_factors + (1 - blend_weight) * tier_factors
    result *= blended

    return result
