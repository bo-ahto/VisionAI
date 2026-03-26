"""규칙 기반 신뢰도 등급 산정.

기획서 참조: 5.2 Phase 1
"""
from __future__ import annotations

import pandas as pd


def assign_confidence_grade(
    df: pd.DataFrame,
    sold_col: str = "artist_total_sold",
    new_col: str = "is_new_artist",
    session_col: str = "회차",
) -> pd.Series:
    """각 행에 A/B/C/D 등급을 부여한다.

    기획서 5.2 Phase 1 규칙:
      A: 추정가 있음 + 작가 낙찰 ≥ 20건 + 최근 20회차 내 거래
      B: 추정가 있음 + 작가 낙찰 6~19건
      C: 추정가 있음 + 작가 낙찰 1~5건
      D: 추정가 있음 + 작가 낙찰 0건 (신규/미상)
    """
    grade = pd.Series("D", index=df.index, dtype="object")

    sold = df[sold_col].fillna(0).astype(int)

    grade[sold >= 1] = "C"
    grade[sold >= 6] = "B"
    grade[sold >= 20] = "A"

    return grade
