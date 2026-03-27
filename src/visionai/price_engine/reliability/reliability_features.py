"""Reliability Model 메타피처 추출.

기획서 5.2 Phase 2: 항상 사용 가능한 5개 기본 피처로 학습.
Champion 모델 독립 — 어떤 모델을 쓰든 동일한 메타피처 세트.

기본 5개 피처:
  1. artist_total_sold    (작가 낙찰 건수)
  2. artist_premium_std   (작가 프리미엄 변동성)
  3. artist_recent_count  (최근 20회차 내 거래 건수)
  4. estimate_ratio       (추정가 불확실성)
  5. is_new_artist        (Cold Start 여부)
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def extract_reliability_features(
    df: pd.DataFrame,
    works_full: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Reliability Model용 메타피처를 추출한다.

    Args:
        df: 예측 대상 DataFrame (피처 + 작가 통계 포함).
        works_full: 전체 데이터 (최근 거래 건수 계산용).

    Returns:
        5개 메타피처 DataFrame (같은 인덱스).
    """
    meta = pd.DataFrame(index=df.index)

    # 1. artist_total_sold
    meta["rel_artist_sold"] = df["artist_total_sold"].fillna(0).astype(float)

    # 2. artist_premium_std (추정가 대비 낙찰가 비율의 변동성)
    if "artist_premium_std" in df.columns:
        meta["rel_premium_std"] = df["artist_premium_std"].fillna(0).astype(float)
    else:
        # 간이 계산: estimate_ratio를 proxy로 사용
        meta["rel_premium_std"] = df["estimate_ratio"].fillna(1.0).astype(float) - 1.0

    # 3. artist_recent_count (최근 20회차 내 거래 건수)
    if works_full is not None and "artist_clean" in df.columns:
        recent_counts = []
        for idx in df.index:
            artist = df.loc[idx, "artist_clean"]
            session = df.loc[idx, "회차"]
            atype = df.loc[idx, "타입"]

            if works_full is not None:
                recent = works_full[
                    (works_full["타입"] == atype)
                    & (works_full["artist_clean"] == artist)
                    & (works_full["회차"] >= session - 20)
                    & (works_full["회차"] < session)
                ]
                recent_counts.append(len(recent))
            else:
                recent_counts.append(0)
        meta["rel_recent_count"] = recent_counts
    else:
        meta["rel_recent_count"] = 0.0

    # 4. estimate_ratio (추정가 불확실성)
    meta["rel_estimate_ratio"] = df["estimate_ratio"].fillna(1.0).astype(float)

    # 5. is_new_artist
    meta["rel_is_new_artist"] = df["is_new_artist"].astype(float)

    return meta
