"""시계열 데이터 분할.

다중 출처 지원:
- assign_split_by_date(): 날짜 기반 비율 분할 (다중 경매사/갤러리)
- assign_split_4way(): 레거시 — K-Auction 타입별 하드코딩 분할

기획서 참조: 3.3 규칙 2, Implementation Strategy Step 1-1
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class SplitSpec:
    """단일 auction_type의 3-way 분할 경계 (Phase 1-2)."""

    auction_type: str
    train_max_session: int
    valid_max_session: int
    # test는 valid_max_session 초과 전체


@dataclass(frozen=True)
class SplitSpec4Way:
    """단일 auction_type의 4-way 분할 경계 (Phase 3).

    Train → Calib → Validation → Test 순서.
    후처리 파라미터(smearing, ratio, quantile calibration)는 Calib에서 학습,
    Validation에서 평가. Test 정보는 어떤 경로에서도 후처리에 유입되지 않는다.
    """

    auction_type: str
    train_max_session: int
    calib_max_session: int
    valid_max_session: int
    # test는 valid_max_session 초과 전체


# Phase 1-2 기본 분할 경계
DEFAULT_SPLITS: list[SplitSpec] = [
    SplitSpec(auction_type="위클리", train_max_session=380, valid_max_session=430),
    SplitSpec(auction_type="프리미엄", train_max_session=180, valid_max_session=200),
    SplitSpec(auction_type="메이저", train_max_session=160, valid_max_session=175),
]

# Phase 3: 4-way 분할 경계 (Calib 블록 추가)
DEFAULT_SPLITS_4WAY: list[SplitSpec4Way] = [
    SplitSpec4Way(
        auction_type="위클리",
        train_max_session=360,
        calib_max_session=380,
        valid_max_session=430,
    ),
    SplitSpec4Way(
        auction_type="프리미엄",
        train_max_session=170,
        calib_max_session=180,
        valid_max_session=200,
    ),
    SplitSpec4Way(
        auction_type="메이저",
        train_max_session=150,
        calib_max_session=160,
        valid_max_session=175,
    ),
]


def assign_split(
    df: pd.DataFrame,
    splits: list[SplitSpec] | None = None,
    session_col: str = "회차",
    type_col: str = "타입",
) -> pd.Series:
    """각 행에 'train'/'valid'/'test' 라벨을 부여한다.

    Args:
        df: 작품 DataFrame (session_col, type_col 필수).
        splits: 분할 스펙. None이면 DEFAULT_SPLITS 사용.
        session_col: 회차 컬럼명.
        type_col: 경매 타입 컬럼명.

    Returns:
        pd.Series with 'train'/'valid'/'test' labels (같은 인덱스).
    """
    if splits is None:
        splits = DEFAULT_SPLITS

    split_map = {s.auction_type: s for s in splits}
    result = pd.Series("unknown", index=df.index, dtype="object")

    for atype, spec in split_map.items():
        mask = df[type_col] == atype
        session = df.loc[mask, session_col]
        result.loc[mask & (session <= spec.train_max_session)] = "train"
        result.loc[
            mask
            & (session > spec.train_max_session)
            & (session <= spec.valid_max_session)
        ] = "valid"
        result.loc[mask & (session > spec.valid_max_session)] = "test"

    return result


def assign_split_4way(
    df: pd.DataFrame,
    splits: list[SplitSpec4Way] | None = None,
    session_col: str = "회차",
    type_col: str = "타입",
) -> pd.Series:
    """각 행에 'train'/'calib'/'valid'/'test' 라벨을 부여한다 (Phase 3).

    Args:
        df: 작품 DataFrame (session_col, type_col 필수).
        splits: 4-way 분할 스펙. None이면 DEFAULT_SPLITS_4WAY 사용.
        session_col: 회차 컬럼명.
        type_col: 경매 타입 컬럼명.

    Returns:
        pd.Series with 'train'/'calib'/'valid'/'test' labels.
    """
    if splits is None:
        splits = DEFAULT_SPLITS_4WAY

    split_map = {s.auction_type: s for s in splits}
    result = pd.Series("unknown", index=df.index, dtype="object")

    for atype, spec in split_map.items():
        mask = df[type_col] == atype
        session = df.loc[mask, session_col]
        result.loc[mask & (session <= spec.train_max_session)] = "train"
        result.loc[
            mask
            & (session > spec.train_max_session)
            & (session <= spec.calib_max_session)
        ] = "calib"
        result.loc[
            mask
            & (session > spec.calib_max_session)
            & (session <= spec.valid_max_session)
        ] = "valid"
        result.loc[mask & (session > spec.valid_max_session)] = "test"

    # 미지정 타입에 대해 회차 기반 비율 분할 (80/5/5/10)
    unknown_mask = result == "unknown"
    if unknown_mask.any():
        for atype in df.loc[unknown_mask, type_col].unique():
            type_mask = unknown_mask & (df[type_col] == atype)
            sessions = df.loc[type_mask, session_col].sort_values()
            if sessions.empty:
                continue
            unique_sessions = sorted(sessions.unique())
            n = len(unique_sessions)
            train_cut = unique_sessions[int(n * 0.80) - 1] if n > 4 else unique_sessions[-1]
            calib_cut = unique_sessions[int(n * 0.85) - 1] if n > 4 else train_cut
            valid_cut = unique_sessions[int(n * 0.90) - 1] if n > 4 else calib_cut
            s = df.loc[type_mask, session_col]
            result.loc[type_mask & (s <= train_cut)] = "train"
            result.loc[type_mask & (s > train_cut) & (s <= calib_cut)] = "calib"
            result.loc[type_mask & (s > calib_cut) & (s <= valid_cut)] = "valid"
            result.loc[type_mask & (s > valid_cut)] = "test"

    return result


def assign_split_by_date(
    df: pd.DataFrame,
    date_col: str = "sale_date",
    train_ratio: float = 0.80,
    calib_ratio: float = 0.05,
    valid_ratio: float = 0.05,
) -> pd.Series:
    """날짜 기반 4-way 비율 분할 (다중 출처 지원).

    타입·회차 의존 없이, 날짜 순서만으로 분할한다.
    test_ratio = 1 - train - calib - valid.

    Args:
        df: DataFrame with date_col.
        date_col: 날짜 컬럼명 (YYYY-MM-DD 문자열 또는 datetime).
        train_ratio: train 비율 (기본 80%).
        calib_ratio: calib 비율 (기본 5%).
        valid_ratio: valid 비율 (기본 5%).

    Returns:
        pd.Series with 'train'/'calib'/'valid'/'test' labels.
    """
    dates = pd.to_datetime(df[date_col], errors="coerce")
    result = pd.Series("train", index=df.index, dtype="object")

    # 유효 날짜가 있는 행만 분할
    valid_dates = dates.dropna()
    if valid_dates.empty:
        return result

    unique_dates = sorted(valid_dates.unique())
    n = len(unique_dates)
    if n < 5:
        return result

    train_cut = unique_dates[int(n * train_ratio) - 1]
    calib_cut = unique_dates[int(n * (train_ratio + calib_ratio)) - 1]
    valid_cut = unique_dates[int(n * (train_ratio + calib_ratio + valid_ratio)) - 1]

    result.loc[dates <= train_cut] = "train"
    result.loc[(dates > train_cut) & (dates <= calib_cut)] = "calib"
    result.loc[(dates > calib_cut) & (dates <= valid_cut)] = "valid"
    result.loc[dates > valid_cut] = "test"

    # 날짜 결측 행은 "unknown"으로 라벨링 (코덱스 P2 2026-04-17):
    # 이전엔 모두 train으로 강제 분류했으나, K-Auction 날짜 추론 실패 행이
    # test 기간일 수도 있어 train 오염 위험.
    # 호출자가 session_col 대체 로직이나 exclusion을 처리해야 함.
    result.loc[dates.isna()] = "unknown"

    return result
