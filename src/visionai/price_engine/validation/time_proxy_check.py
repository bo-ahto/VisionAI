"""회차→시간 proxy 타당성 검증.

기획서 참조: 3.3 time proxy 한계

주의: 원본 CSV의 행 순서(등장 순서)를 기준으로 검사한다.
정렬 후 검사하면 항상 단조증가이므로 의미 없다.
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
    """auction_type별 원본 행 순서에서 회차가 단조증가하는지 확인한다.

    원본 CSV의 행 순서(인덱스 순서)를 그대로 사용하여,
    경매 데이터가 실제 시간순으로 기록됐는지 검증한다.

    Returns:
        DataFrame: auction_type, total_rows, total_sessions, is_monotonic,
                   inversions, inversion_rate_pct
    """
    rows = []
    for atype in df[type_col].unique():
        subset = df[df[type_col] == atype]
        # 원본 인덱스 순서대로 회차값 추출 (정렬하지 않음)
        sessions = subset[session_col].values

        # 연속 행 간 회차 역전 횟수
        inversions = sum(1 for a, b in zip(sessions, sessions[1:]) if a > b)
        total_rows = len(sessions)
        unique_sessions = len(set(sessions))
        is_mono = inversions == 0
        inversion_rate = inversions / max(total_rows - 1, 1) * 100

        rows.append({
            "auction_type": atype,
            "total_rows": total_rows,
            "total_sessions": unique_sessions,
            "is_monotonic": is_mono,
            "inversions": inversions,
            "inversion_rate_pct": round(inversion_rate, 2),
        })
        logger.info(
            "%s: %d rows, %d sessions, monotonic=%s, inversions=%d (%.1f%%)",
            atype, total_rows, unique_sessions, is_mono, inversions, inversion_rate,
        )

    return pd.DataFrame(rows)
