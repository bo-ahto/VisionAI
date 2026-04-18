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
    cutoff: int | str = "9999-12-31",
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
    # 컬럼 자동 감지
    if session_col not in works.columns:
        session_col = "회차" if "회차" in works.columns else session_col
    if type_col not in works.columns:
        type_col = "타입" if "타입" in works.columns else type_col
    if price_col not in works.columns:
        price_col = "낙찰가" if "낙찰가" in works.columns else price_col

    # cutoff 타입 자동 정합: 기본값은 날짜 문자열("9999-12-31")이지만
    # session 기반(정수) 데이터에서는 int<str 비교 TypeError를 피하기 위해 대형 상수로 치환.
    if pd.api.types.is_numeric_dtype(works[session_col]) and isinstance(cutoff, str):
        cutoff = 10**9  # 모든 session을 포함하는 sentinel

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


# Phase 5: 5-tier 확장용 상수
_MIN_SOLD_WARM = 5  # Tier 0: K-Auction 거래 ≥ 5건
_MIN_EXTERNAL_RECORDS = 3  # Tier 1: 글로벌/타 경매사 데이터
_MIN_SIMILAR_ARTISTS = 3  # Tier 2: K-NN 유사 작가


def get_cold_start_fallback_v2(
    artist_name: str,
    medium_category: str,
    auction_type: str,
    works: pd.DataFrame,
    cutoff: int | str = "9999-12-31",
    external_stats: dict[str, float] | None = None,
    similar_artists: list | None = None,
    session_col: str = "회차",
    artist_col: str = "artist_clean",
    medium_col: str = "medium_category",
    type_col: str = "타입",
    price_col: str = "낙찰가",
) -> ColdStartResult:
    """5-tier Cold Start fallback.

    Tier 0: K-Auction 자체 거래 ≥ 5건 → 작가 통계 직접 사용
    Tier 1: 외부 경매 데이터 (Artsy/Seoul Auction) ≥ 3건 → 외부 통계
    Tier 2: K-NN 유사 작가 ≥ 3명 → 거리 가중 평균
    Tier 3: medium x auction_type Bayesian shrinkage (n ≥ 30)
    Tier 4: medium only / global Bayesian shrinkage (n ≥ 50)
    """
    # 컬럼 자동 감지
    if session_col not in works.columns:
        session_col = "회차" if "회차" in works.columns else session_col
    if type_col not in works.columns:
        type_col = "타입" if "타입" in works.columns else type_col
    if price_col not in works.columns:
        price_col = "낙찰가" if "낙찰가" in works.columns else price_col

    # 코덱스 P1 (2026-04-18): v1과 동일하게 session 기반 데이터(int)에 str cutoff 쓰면
    # TypeError. session_col dtype에 맞춰 cutoff 기본값 자동 coerce.
    if pd.api.types.is_numeric_dtype(works[session_col]) and isinstance(cutoff, str):
        cutoff = 10**9

    mask = (works[session_col] < cutoff)
    sold_mask = mask & (pd.to_numeric(works[price_col], errors="coerce") > 0)
    subset = works.loc[sold_mask].copy()
    subset[price_col] = pd.to_numeric(subset[price_col], errors="coerce")

    if subset.empty:
        return ColdStartResult(tier=4, fallback_ln_price=0.0, group_size=0)

    global_mean_ln = float(np.log(subset[price_col]).mean())

    # Tier 0: K-Auction 자체 거래 ≥ 5건
    artist_mask = subset[artist_col] == artist_name
    artist_subset = subset.loc[artist_mask]
    if len(artist_subset) >= _MIN_SOLD_WARM:
        group_mean_ln = float(np.log(artist_subset[price_col]).mean())
        return ColdStartResult(
            tier=0, fallback_ln_price=group_mean_ln, group_size=len(artist_subset),
        )

    # Tier 1: 외부 경매 데이터 ≥ 3건
    if external_stats and external_stats.get("count", 0) >= _MIN_EXTERNAL_RECORDS:
        ext_ln = external_stats.get("avg_ln_price", global_mean_ln)
        return ColdStartResult(
            tier=1,
            fallback_ln_price=float(ext_ln),
            group_size=int(external_stats.get("count", 0)),
        )

    # Tier 2: K-NN 유사 작가 ≥ 3명
    if similar_artists and len(similar_artists) >= _MIN_SIMILAR_ARTISTS:
        from visionai.price_engine.features.artist_similarity import (
            compute_similarity_features,
        )

        sim_feats = compute_similarity_features(artist_name, similar_artists)
        sim_ln = sim_feats.get("sim_weighted_price_ln", global_mean_ln)
        if sim_ln > 0:
            return ColdStartResult(
                tier=2, fallback_ln_price=float(sim_ln), group_size=len(similar_artists),
            )

    # Tier 3: medium x auction_type (기존 Tier 1)
    t3_mask = (subset[medium_col] == medium_category) & (subset[type_col] == auction_type)
    t3_subset = subset.loc[t3_mask]
    if len(t3_subset) >= _MIN_COUNT_TIER1:
        group_mean_ln = float(np.log(t3_subset[price_col]).mean())
        shrunk = compute_bayesian_shrinkage(group_mean_ln, global_mean_ln, len(t3_subset))
        return ColdStartResult(tier=3, fallback_ln_price=shrunk, group_size=len(t3_subset))

    # Tier 4a: medium only (기존 Tier 2)
    t4a_mask = subset[medium_col] == medium_category
    t4a_subset = subset.loc[t4a_mask]
    if len(t4a_subset) >= _MIN_COUNT_TIER2:
        group_mean_ln = float(np.log(t4a_subset[price_col]).mean())
        shrunk = compute_bayesian_shrinkage(group_mean_ln, global_mean_ln, len(t4a_subset))
        return ColdStartResult(tier=4, fallback_ln_price=shrunk, group_size=len(t4a_subset))

    # Tier 4b: auction_type only (기존 Tier 3 — 하위 호환)
    t4b_mask = subset[type_col] == auction_type
    t4b_subset = subset.loc[t4b_mask]
    if not t4b_subset.empty:
        group_mean_ln = float(np.log(t4b_subset[price_col]).mean())
        return ColdStartResult(
            tier=4, fallback_ln_price=group_mean_ln, group_size=len(t4b_subset),
        )

    # 최후 수단: 전체 평균
    return ColdStartResult(tier=4, fallback_ln_price=global_mean_ln, group_size=len(subset))


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
