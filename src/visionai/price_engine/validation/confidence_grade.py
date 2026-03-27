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
      A: 추정가 있음 + sold≥20 + 추정가 3000만~10억 + 최근 10회차 내 거래 있음
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

    # 추정가 범위 폭 (estimate_ratio)
    est_low = df[estimate_low_col].fillna(0).astype(float)
    est_high = df[estimate_high_col].fillna(0).astype(float)
    est_mid = (est_low + est_high) / 2

    # 기본 등급: 건수 기반
    grade[has_estimate & (sold >= 1)] = "C"
    grade[has_estimate & (sold >= 6)] = "B"

    # A등급: 강화된 조건 (Codex 2차 리뷰 + 데이터 기반 튜닝)
    #   sold >= 20
    #   + 추정가 있음
    #   + 추정가 중앙값 3000만 이상 (within-20% 69.7% 실증)
    #   + 10억 이하 (초고가 제외)
    a_candidate = (
        has_estimate
        & (sold >= 20)
        & (est_mid >= 30_000_000)
        & (est_mid <= 1_000_000_000)
    )
    grade[a_candidate] = "A"

    # A등급 추가 조건: 최근 10회차 내 거래 있음 (기존 20 → 10으로 강화)
    if works_full is not None and artist_col in works_full.columns:
        a_mask = grade == "A"
        for idx in df.index[a_mask]:
            row = df.loc[idx]
            artist = row[artist_col]
            current_session = row[session_col]
            atype = row[type_col]

            recent = works_full[
                (works_full[type_col] == atype)
                & (works_full[artist_col] == artist)
                & (works_full[session_col] >= current_session - 10)
                & (works_full[session_col] < current_session)
            ]
            if len(recent) == 0:
                grade.loc[idx] = "B"
    else:
        pass

    return grade
