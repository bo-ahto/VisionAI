"""회차→시간 proxy 타당성 검증.

기획서 참조: 3.3 time proxy 한계
"""
from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def check_session_monotonicity(
    df: pd.DataFrame,
    session_col: str = "회차",
    type_col: str = "타입",
) -> pd.DataFrame:
    """auction_type별 회차가 단조증가하는지 확인한다.

    Returns:
        DataFrame: auction_type, total_sessions, is_monotonic, inversions
    """
    rows = []
    for atype in df[type_col].unique():
        sessions = df[df[type_col] == atype][session_col].sort_values().values
        unique_sessions = sorted(set(sessions))
        is_mono = all(a <= b for a, b in zip(unique_sessions, unique_sessions[1:]))
        inversions = sum(1 for a, b in zip(unique_sessions, unique_sessions[1:]) if a > b)

        rows.append({
            "auction_type": atype,
            "total_sessions": len(unique_sessions),
            "is_monotonic": is_mono,
            "inversions": inversions,
        })
        logger.info(
            "%s: %d sessions, monotonic=%s, inversions=%d",
            atype, len(unique_sessions), is_mono, inversions,
        )

    return pd.DataFrame(rows)
