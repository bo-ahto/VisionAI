"""K-NN 기반 유사 작가 탐색 + 피처 생성.

Cold Start 작가에게 유사한 Warm 작가의 통계를 이전하여 정보 보강.
Phase 5 Sprint 2 기획서 참조.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SimilarArtist:
    """유사 작가 매칭 결과."""

    artist_name: str
    distance: float
    avg_price_ln: float
    total_sold: int


def _career_length_days(x: pd.Series) -> float:
    """작가 커리어 길이 계산. session_col이 str/datetime/int 셋 다 지원."""
    if x.empty:
        return 0
    if pd.api.types.is_datetime64_any_dtype(x) or isinstance(x.iloc[0], (str, pd.Timestamp)):
        return (pd.to_datetime(x.max()) - pd.to_datetime(x.min())).days + 1
    return x.max() - x.min() + 1


def build_artist_feature_vectors(
    works: pd.DataFrame,
    cutoff: int | str = "9999-12-31",
    session_col: str = "회차",
    artist_col: str = "artist_clean",
    medium_col: str = "medium_category",
    type_col: str = "타입",
    price_col: str = "낙찰가",
) -> pd.DataFrame:
    """작가별 특성 벡터 구성.

    피처: medium_main (최빈 매체), avg_surface_area, avg_ln_price,
          auction_type_main (최빈 타입), career_length (활동 회차 수).
    strict < cutoff.

    Returns:
        DataFrame indexed by artist_clean with 5 features.
    """
    mask = works[session_col] < cutoff
    subset = works.loc[mask].copy()

    if subset.empty:
        return pd.DataFrame()

    sold_mask = pd.to_numeric(subset[price_col], errors="coerce") > 0
    subset_sold = subset.loc[sold_mask].copy()
    subset_sold[price_col] = pd.to_numeric(subset_sold[price_col], errors="coerce")

    if subset_sold.empty:
        return pd.DataFrame()

    # 작가별 집계
    grouped = subset_sold.groupby(artist_col)

    vectors = pd.DataFrame({
        "medium_main": grouped[medium_col].agg(
            lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else "unknown"
        ),
        "avg_surface_area": grouped["surface_area"].mean().fillna(0),
        "avg_ln_price": grouped[price_col].agg(lambda x: np.log(x).mean()),
        "auction_type_main": grouped[type_col].agg(
            lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else "unknown"
        ),
        "career_length": grouped[session_col].agg(_career_length_days),
        "total_sold": grouped[price_col].count(),
    })

    return vectors


def find_similar_artists(
    target_artist: str,
    artist_vectors: pd.DataFrame,
    k: int = 5,
    medium_filter: str | None = None,
    min_sold: int = 5,
) -> list[SimilarArtist]:
    """K-NN으로 유사 작가 탐색.

    1. Candidate generation: medium_filter로 동일 매체 필터
    2. Hard filter: 가격대 ±1 tier (10분위)
    3. Distance: Euclidean on standardized numeric features
    4. Weighted pooling: w_i = 1 / (1 + d_i²)

    Returns:
        상위 K개 유사 작가 리스트 (거리순).
    """
    # Warm-only donor: total_sold >= min_sold인 작가만 후보
    warm_vectors = artist_vectors[artist_vectors["total_sold"] >= min_sold]

    if target_artist not in artist_vectors.index:
        # Cold artist — 매체/타입 기반으로 warm 후보 선택
        if medium_filter is not None:
            candidates = warm_vectors[
                warm_vectors["medium_main"] == medium_filter
            ]
        else:
            candidates = warm_vectors
    else:
        target = artist_vectors.loc[target_artist]
        medium_filter = target.get("medium_main", None)
        candidates = warm_vectors.drop(index=target_artist, errors="ignore")

        # Medium filter
        if medium_filter:
            filtered = candidates[candidates["medium_main"] == medium_filter]
            if len(filtered) >= k:
                candidates = filtered

        # Price tier hard filter: +/- 1 decile
        if "avg_ln_price" in candidates.columns and "avg_ln_price" in target.index:
            target_price = target["avg_ln_price"]
            deciles = artist_vectors["avg_ln_price"].quantile(
                [i / 10 for i in range(11)]
            ).values
            target_decile = int(
                np.searchsorted(deciles, target_price, side="right") - 1
            )
            low_bound = deciles[max(0, target_decile - 1)]
            high_bound = deciles[min(10, target_decile + 2)]
            price_filtered = candidates[
                (candidates["avg_ln_price"] >= low_bound)
                & (candidates["avg_ln_price"] <= high_bound)
            ]
            # Hard filter: decile 밖 후보는 무조건 제외
            candidates = price_filtered

    if candidates.empty:
        return []

    # Numeric features for distance
    numeric_cols = ["avg_surface_area", "avg_ln_price", "career_length"]
    available = [c for c in numeric_cols if c in candidates.columns]

    if not available:
        return []

    cand_numeric = candidates[available].fillna(0).values
    # Standardize
    mean = cand_numeric.mean(axis=0)
    std = cand_numeric.std(axis=0)
    std[std == 0] = 1.0
    cand_std = (cand_numeric - mean) / std

    if target_artist in artist_vectors.index:
        target_vals = artist_vectors.loc[target_artist, available].fillna(0).values
        target_std = (target_vals - mean) / std
    else:
        # Cold artist: 매체 평균을 target으로
        target_std = cand_std.mean(axis=0)

    # Euclidean distance
    distances = np.sqrt(np.sum((cand_std - target_std) ** 2, axis=1))
    top_k_idx = np.argsort(distances)[:k]

    results: list[SimilarArtist] = []
    for idx in top_k_idx:
        artist_name = candidates.index[idx]
        results.append(SimilarArtist(
            artist_name=str(artist_name),
            distance=float(distances[idx]),
            avg_price_ln=float(candidates.iloc[idx].get("avg_ln_price", 0)),
            total_sold=int(candidates.iloc[idx].get("total_sold", 0)),
        ))

    return results


def compute_similarity_features(
    artist_name: str,
    similar_artists: list[SimilarArtist],
) -> dict[str, float]:
    """유사 작가 통계에서 피처 생성.

    Returns:
        dict with: sim_avg_price_ln, sim_weighted_price_ln,
                   sim_count, sim_avg_distance.
    """
    if not similar_artists:
        return {
            "sim_avg_price_ln": 0.0,
            "sim_weighted_price_ln": 0.0,
            "sim_count": 0.0,
            "sim_avg_distance": 0.0,
        }

    prices = [s.avg_price_ln for s in similar_artists]
    distances = [s.distance for s in similar_artists]
    weights = [1.0 / (1.0 + d ** 2) for d in distances]

    w_sum = sum(weights)
    weighted_price = (
        sum(w * p for w, p in zip(weights, prices, strict=False)) / w_sum
        if w_sum > 0 else 0
    )

    return {
        "sim_avg_price_ln": float(np.mean(prices)),
        "sim_weighted_price_ln": float(weighted_price),
        "sim_count": float(len(similar_artists)),
        "sim_avg_distance": float(np.mean(distances)),
    }
