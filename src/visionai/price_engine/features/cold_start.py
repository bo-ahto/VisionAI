"""Cold Start 작가 fallback 로직.

기획서 참조: 3.2.4, 5.2 D등급
D등급(작가 낙찰 0건) 또는 작자미상 작가에 대한 대체값을 생성한다.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

MIN_GROUP_SIZE = 10  # fallback 그룹 최소 크기 (기획서 5.2)


def compute_estimate_tier(estimate_mid: pd.Series) -> pd.Series:
    """추정가 중앙값을 5단계 구간으로 분류한다.

    구간 (기획서 3.1):
      <500만 / 500~3000만 / 3000만~1억 / 1억~10억 / 10억+
    """
    bins = [0, 5_000_000, 30_000_000, 100_000_000, 1_000_000_000, np.inf]
    labels = ["하위", "중하", "중상", "상위", "최상"]
    return pd.cut(estimate_mid, bins=bins, labels=labels, right=True)


def build_cold_start_fallback(
    works: pd.DataFrame,
    cutoff_session: int,
    session_col: str = "회차",
    type_col: str = "타입",
    price_col: str = "낙찰가",
) -> pd.DataFrame:
    """estimate_tier + auction_type 그룹별 평균 통계를 계산한다.

    기획서 3.3 규칙 1에 따라 cutoff_session 이전 데이터만 사용.

    Returns:
        DataFrame with (estimate_tier, auction_type) 인덱스 + 통계 컬럼.
    """
    past = works[works[session_col] < cutoff_session].copy()

    if "estimate_mid" not in past.columns:
        past["estimate_mid"] = (
            past["추정가(최저)"].astype(float) + past["추정가(최고)"].astype(float)
        ) / 2

    past["estimate_tier"] = compute_estimate_tier(past["estimate_mid"])

    grouped = past.groupby(["estimate_tier", type_col], observed=True)[price_col].agg(
        fallback_avg_price="mean",
        fallback_max_price="max",
        fallback_total_sold="count",
    )

    # 그룹 크기 검증
    small_groups = grouped[grouped["fallback_total_sold"] < MIN_GROUP_SIZE]
    if len(small_groups) > 0:
        logger.warning(
            "Cold Start fallback 그룹 크기 < %d인 그룹 %d개: %s",
            MIN_GROUP_SIZE,
            len(small_groups),
            small_groups.index.tolist(),
        )

    grouped["fallback_avg_price"] = grouped["fallback_avg_price"].round(0).astype(int)

    return grouped
