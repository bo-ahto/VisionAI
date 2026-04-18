"""매크로 지표 피처 모듈.

K-Auction 회차별 통계를 작품 DataFrame에 조인.
1회차 래그: 예측 시점에서 이미 관측 가능한 값만 사용.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

MACRO_FEATURES: list[str] = [
    "kospi_close",
    "usd_krw",
    "apartment_index",
    "cpi",
    "kauction_sold_rate_prev",
    "kauction_avg_price_prev",
    "kauction_avg_price_mom_3m",
]


def load_macro_monthly(path: str | Path) -> pd.DataFrame:
    """매크로 지표 CSV 로드."""
    df = pd.read_csv(path, dtype={"year_month": str})
    logger.info("Loaded macro data: %d rows", len(df))
    return df


def load_macro_session(path: str | Path) -> pd.DataFrame:
    """회차별 매크로 통계 CSV 로드.

    Args:
        path: macro_session.csv 경로 (session, kauction_sold_rate, kauction_avg_price 등).

    Returns:
        DataFrame with session + 통계 컬럼.
    """
    df = pd.read_csv(path)
    logger.info("Loaded session macro data: %d sessions", len(df))
    return df


def join_macro_features(
    df: pd.DataFrame,
    macro_df: pd.DataFrame,
    session_col: str = "회차",
    lag_sessions: int = 1,
) -> pd.DataFrame:
    """작품 DataFrame에 매크로 피처 조인.

    회차 기준으로 lag_sessions만큼 이전 회차의 통계를 사용.
    (예측 시점에서 이미 관측 가능한 값만)

    Args:
        df: 작품 DataFrame (session_col 포함).
        macro_df: 매크로 DataFrame. 'session' 컬럼 필수.
        session_col: 회차 컬럼명.
        lag_sessions: 래그 회차 수 (기본 1).

    Returns:
        df에 매크로 피처 추가된 DataFrame.
    """
    out = df.copy()

    if "session" not in macro_df.columns:
        logger.warning("No 'session' column in macro_df. Setting macro features to 0.")
        for col in MACRO_FEATURES:
            out[col] = 0.0
        return out

    # 1. 원시 컬럼명 → 최종 피처명 rename
    macro_work = macro_df.copy()
    rename_map = {
        "kauction_sold_rate": "kauction_sold_rate_prev",
        "kauction_avg_price": "kauction_avg_price_prev",
    }
    macro_work = macro_work.rename(columns=rename_map)

    # 2. 래그 적용: join_session = session + lag
    macro_work["join_session"] = macro_work["session"] + lag_sessions

    # 3. 조인할 피처 선택
    available_features = [c for c in MACRO_FEATURES if c in macro_work.columns]
    if not available_features:
        logger.warning("No matching macro features after rename. Setting to 0.")
        for col in MACRO_FEATURES:
            out[col] = 0.0
        return out

    join_cols = ["join_session", *available_features]
    macro_for_join = macro_work[join_cols].drop_duplicates("join_session")

    # 4. 머지
    out = out.merge(
        macro_for_join,
        left_on=session_col,
        right_on="join_session",
        how="left",
    )
    if "join_session" in out.columns:
        out = out.drop(columns=["join_session"])

    # 5. 누락 피처 기본값 + forward-fill
    for col in MACRO_FEATURES:
        if col not in out.columns:
            out[col] = 0.0
        else:
            out[col] = out[col].ffill().fillna(0.0)

    return out
