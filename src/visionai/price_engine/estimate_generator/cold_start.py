"""3-tier 계층적 Cold Start fallback + Bayesian shrinkage.

Phase 3 추정가 생성 엔진 전용.
Phase 1-2의 features/cold_start.py를 대체하지 않음 — 공존.

학술 근거: 계층적 베이즈 모델의 Partial Pooling (기획서 2.5절).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Tier별 최소 샘플 수
_MIN_COUNT_TIER1 = 30  # medium_category x auction_type
_MIN_COUNT_TIER2 = 50  # medium_category

# Bayesian shrinkage 강도
_SHRINKAGE_M = 10


@dataclass(frozen=True)
class ColdStartResult:
    """Cold Start fallback 결과."""

    tier: int  # 0 = 충분한 이력, 1/2/3 = fallback tier
    fallback_ln_price: float
    group_size: int


def compute_bayesian_shrinkage(
    group_mean_ln: float,
    global_mean_ln: float,
    n: int,
    m: int = _SHRINKAGE_M,
) -> float:
    """Bayesian shrinkage on log-price scale.

    (n * group_mean_ln + m * global_mean_ln) / (n + m)
    """
    return (n * group_mean_ln + m * global_mean_ln) / (n + m)


def get_cold_start_fallback(
    medium_category: str,
    auction_type: str,
    works: pd.DataFrame,
    cutoff: int,
    session_col: str = "회차",
    medium_col: str = "medium_category",
    type_col: str = "타입",
    price_col: str = "낙찰가",
) -> ColdStartResult:
    """3-tier 계층적 fallback으로 Cold Start 작가의 prior를 산출한다.

    Tier 1: medium_category x auction_type (min ≥ 30) + shrinkage
    Tier 2: medium_category (min ≥ 50) + shrinkage
    Tier 3: auction_type (항상 가용) — 전체 ln(price) 평균

    Returns:
        ColdStartResult with tier, fallback_ln_price, group_size.
    """
    mask = (works[session_col] < cutoff) & (works[price_col] > 0)
    subset = works.loc[mask]

    if subset.empty:
        return ColdStartResult(tier=3, fallback_ln_price=0.0, group_size=0)

    global_mean_ln = float(np.log(subset[price_col]).mean())

    # Tier 1: medium x auction_type
    t1_mask = (subset[medium_col] == medium_category) & (subset[type_col] == auction_type)
    t1_subset = subset.loc[t1_mask]
    if len(t1_subset) >= _MIN_COUNT_TIER1:
        group_mean_ln = float(np.log(t1_subset[price_col]).mean())
        shrunk = compute_bayesian_shrinkage(group_mean_ln, global_mean_ln, len(t1_subset))
        return ColdStartResult(tier=1, fallback_ln_price=shrunk, group_size=len(t1_subset))

    # Tier 2: medium only
    t2_mask = subset[medium_col] == medium_category
    t2_subset = subset.loc[t2_mask]
    if len(t2_subset) >= _MIN_COUNT_TIER2:
        group_mean_ln = float(np.log(t2_subset[price_col]).mean())
        shrunk = compute_bayesian_shrinkage(group_mean_ln, global_mean_ln, len(t2_subset))
        return ColdStartResult(tier=2, fallback_ln_price=shrunk, group_size=len(t2_subset))

    # Tier 3: auction_type only (항상 가용)
    t3_mask = subset[type_col] == auction_type
    t3_subset = subset.loc[t3_mask]
    if not t3_subset.empty:
        group_mean_ln = float(np.log(t3_subset[price_col]).mean())
        return ColdStartResult(tier=3, fallback_ln_price=group_mean_ln, group_size=len(t3_subset))

    # 최후 수단: 전체 평균
    return ColdStartResult(tier=3, fallback_ln_price=global_mean_ln, group_size=len(subset))


def assign_confidence_grade(
    artist_total_sold: int,
    is_new_artist: bool,
    cold_start_tier: int,
    artist_unsold_rate: float | None = None,
    group_unsold_rate: float | None = None,
) -> str:
    """Phase 3 전용 신뢰도 등급 결정 규칙.

    Phase 1-2의 validation/confidence_grade.py를 대체하지 않음.
    - Phase 1-2: estimate_mid 기반, sold≥20 + est 30M~1B
    - Phase 3: cold_start_tier + unsold_rate 기반, 추정가 없이 동작

    등급 기준:
    - A: artist_total_sold ≥ 20 AND cold_start_tier == 0
    - B: 5 ≤ artist_total_sold < 20
    - C: 1 ≤ artist_total_sold < 5
         OR artist_unsold_rate > 50% OR group_unsold_rate > 40%
    - D: is_new_artist == True OR cold_start_tier ≥ 2
    """
    # D등급 우선 (가장 낮은 신뢰도)
    if is_new_artist or cold_start_tier >= 2:
        return "D"

    # C등급 조건
    unsold_flag = False
    if artist_unsold_rate is not None and artist_unsold_rate > 0.5:
        unsold_flag = True
    if group_unsold_rate is not None and group_unsold_rate > 0.4:
        unsold_flag = True

    if artist_total_sold < 5 or unsold_flag:
        return "C"

    # B등급
    if artist_total_sold < 20:
        return "B"

    # A등급
    if cold_start_tier == 0:
        return "A"

    return "B"
