"""fold별 작가 통계 스냅샷 생성.

기획서 3.3 규칙 1: 모든 집계 피처는 fold별 train window 안에서 재계산.
artists.csv는 참조용이며, 모델 입력은 works에서 동적 계산한다.
"""
from __future__ import annotations

import pandas as pd


def compute_artist_stats_snapshot(
    works: pd.DataFrame,
    cutoff_session: int | str,
    auction_type: str | None = None,
    session_col: str = "회차",
    type_col: str = "타입",
    artist_col: str = "작가",
    price_col: str = "낙찰가",
) -> pd.DataFrame:
    """cutoff 이전(strict <) 데이터로 작가 통계를 계산한다.

    cutoff_session이 문자열(날짜)이고 session_col="sale_date"이면 날짜 비교.

    Args:
        works: 전체 작품 DataFrame.
        cutoff_session: 이 값 미만의 데이터만 사용 (정수 또는 날짜 문자열).
        auction_type: 특정 경매 타입 필터. None이면 전체.
        session_col: 시간 컬럼명.
        type_col: 타입 컬럼명.
        artist_col: 작가 컬럼명.
        price_col: 가격 컬럼명.

    Returns:
        작가별 통계 DataFrame (인덱스: 작가명).
        컬럼: artist_total_sold, artist_avg_price, artist_max_price
    """
    # 컬럼 자동 감지
    if session_col not in works.columns:
        session_col = "회차" if "회차" in works.columns else session_col
    if type_col not in works.columns:
        type_col = "타입" if "타입" in works.columns else type_col
    if price_col not in works.columns:
        price_col = "낙찰가" if "낙찰가" in works.columns else price_col

    if isinstance(cutoff_session, str) and session_col == "sale_date":
        dates = pd.to_datetime(works[session_col], errors="coerce")
        mask = dates < pd.Timestamp(cutoff_session)
    else:
        mask = works[session_col] < cutoff_session
    if auction_type is not None and type_col in works.columns:
        mask = mask & (works[type_col] == auction_type)
    # C1-fix: 미낙찰(가격=0) 제외
    mask = mask & (works[price_col] > 0)

    past = works.loc[mask]

    if past.empty:
        return pd.DataFrame(
            columns=["artist_total_sold", "artist_avg_price", "artist_max_price"],
        )

    stats = past.groupby(artist_col)[price_col].agg(
        artist_total_sold="count",
        artist_avg_price="mean",
        artist_max_price="max",
    )

    stats["artist_avg_price"] = stats["artist_avg_price"].round(0).astype(int)

    return stats
