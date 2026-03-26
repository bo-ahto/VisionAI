"""규칙 기반 신뢰도 등급 산정.

기획서 참조: 5.2 Phase 1
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def assign_confidence_grade(
    df: pd.DataFrame,
    sold_col: str = "artist_total_sold",
    session_col: str = "회차",
    type_col: str = "타입",
    artist_col: str = "artist_clean",
    estimate_low_col: str = "추정가(최저)",
    estimate_high_col: str = "추정가(최고)",
    works_full: pd.DataFrame | None = None,
) -> pd.Series:
    """각 행에 A/B/C/D 등급을 부여한다.

    기획서 5.2 Phase 1 규칙 (3개 조건):
      A: 추정가 있음 + 작가 낙찰 ≥ 20건 + 최근 20회차 내 거래 있음
      B: 추정가 있음 + 작가 낙찰 6~19건
      C: 추정가 있음 + 작가 낙찰 1~5건
      D: 추정가 있음 + 작가 낙찰 0건 (신규/미상)
    """
    grade = pd.Series("D", index=df.index, dtype="object")
    sold = df[sold_col].fillna(0).astype(int)

    # 추정가 유무 확인
    has_estimate = (
        df[estimate_low_col].fillna(0).astype(float) > 0
    ) | (
        df[estimate_high_col].fillna(0).astype(float) > 0
    )

    # 기본 등급: 건수 기반
    grade[has_estimate & (sold >= 1)] = "C"
    grade[has_estimate & (sold >= 6)] = "B"
    grade[has_estimate & (sold >= 20)] = "A"

    # A등급 추가 조건: 최근 20회차 내 거래 있음
    if works_full is not None:
        # 각 행에 대해 해당 작가가 최근 20회차 내 거래가 있는지 확인
        a_mask = grade == "A"
        for idx in df.index[a_mask]:
            row = df.loc[idx]
            artist = row[artist_col]
            current_session = row[session_col]
            atype = row[type_col]

            # 같은 타입에서 최근 20회차 내 해당 작가 거래
            recent = works_full[
                (works_full[type_col] == atype)
                & (works_full[artist_col] == artist)
                & (works_full[session_col] >= current_session - 20)
                & (works_full[session_col] < current_session)
            ]
            if len(recent) == 0:
                grade.loc[idx] = "B"  # 최근 거래 없으면 B로 강등
    else:
        # works_full 없으면 session 기반 근사: 마지막 회차 - 현재 회차로 판단 불가
        # 이 경우 A등급을 sold >= 20으로만 유지 (보수적이지 않음 — 주의)
        pass

    return grade
