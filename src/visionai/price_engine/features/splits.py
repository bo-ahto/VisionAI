"""시계열 데이터 분할 스펙.

auction_type별 독립 시간축으로 train/valid/test를 분할한다.
기획서 참조: 3.3 규칙 2, Implementation Strategy Step 1-1

Phase 3 확장: 4-way 분할 (Train/Calib/Valid/Test)
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

    return result
