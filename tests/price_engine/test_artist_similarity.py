"""Sprint 2: Artist Similarity 테스트."""
from __future__ import annotations

import numpy as np
import pandas as pd

from visionai.price_engine.features.artist_similarity import (
    SimilarArtist,
    build_artist_feature_vectors,
    compute_similarity_features,
    find_similar_artists,
)


def _make_works(n_artists: int = 50, n_per_artist: int = 10) -> pd.DataFrame:
    """테스트용 합성 작품 데이터 — 50명 작가 (decile filter에 충분한 수)."""
    rng = np.random.default_rng(42)
    rows = []
    for i in range(n_artists):
        # 가격 그룹: 3개 tier (저/중/고), 각 tier 내 유사 가격
        tier = i % 3
        base_price = [2_000_000, 5_000_000, 15_000_000][tier]
        for _ in range(n_per_artist):
            rows.append({
                "artist_clean": f"작가{i}",
                "medium_category": "유화" if tier < 2 else "수묵",
                "타입": ["메이저", "프리미엄", "위클리"][tier],
                "surface_area": rng.uniform(500, 3000),
                "낙찰가": base_price * rng.uniform(0.7, 1.3),
                "회차": rng.integers(1, 400),
            })
    return pd.DataFrame(rows)


class TestBuildVectors:
    def test_vectors_feature_count(self) -> None:
        """작가 벡터 피처 5개 + total_sold."""
        works = _make_works()
        vectors = build_artist_feature_vectors(
            works, cutoff=500,
            session_col="회차", type_col="타입", price_col="낙찰가",
        )
        expected = {"medium_main", "avg_surface_area", "avg_ln_price",
                    "auction_type_main", "career_length", "total_sold"}
        assert set(vectors.columns) == expected

    def test_vectors_artist_count(self) -> None:
        """10명 작가 벡터 생성."""
        works = _make_works(n_artists=10)
        vectors = build_artist_feature_vectors(
            works, cutoff=500,
            session_col="회차", type_col="타입", price_col="낙찰가",
        )
        assert len(vectors) == 10


class TestFindSimilar:
    def test_similar_medium_filter(self) -> None:
        """매체 필터 시 결과 모두 동일 매체."""
        works = _make_works()
        vectors = build_artist_feature_vectors(
            works, cutoff=500,
            session_col="회차", type_col="타입", price_col="낙찰가",
        )
        results = find_similar_artists("작가0", vectors, k=3, medium_filter="유화")
        for r in results:
            assert vectors.loc[r.artist_name, "medium_main"] == "유화"

    def test_similar_k_count(self) -> None:
        """K개 이하 반환."""
        works = _make_works()
        vectors = build_artist_feature_vectors(
            works, cutoff=500,
            session_col="회차", type_col="타입", price_col="낙찰가",
        )
        results = find_similar_artists("작가0", vectors, k=3)
        assert len(results) <= 3

    def test_distance_sorted(self) -> None:
        """거리 오름차순 정���."""
        works = _make_works()
        vectors = build_artist_feature_vectors(
            works, cutoff=500,
            session_col="회차", type_col="타입", price_col="낙찰가",
        )
        results = find_similar_artists("작가0", vectors, k=5)
        distances = [r.distance for r in results]
        assert distances == sorted(distances)

    def test_price_hard_filter_excludes_outliers(self) -> None:
        """가격대 밖 작가는 hard filter로 제외."""
        vectors = pd.DataFrame(
            {
                "medium_main": ["oil", "oil", "oil"],
                "avg_surface_area": [1.0, 2.0, 3.0],
                "avg_ln_price": [10.0, 20.0, 30.0],
                "auction_type_main": ["a", "a", "a"],
                "career_length": [1, 1, 1],
                "total_sold": [10, 10, 10],
            },
            index=["target", "b", "c"],
        )
        results = find_similar_artists("target", vectors, k=5)
        # target(10.0)의 decile 범위에 b(20.0), c(30.0)는 포함 안 됨
        assert len(results) == 0

    def test_cold_artist_gets_similar(self) -> None:
        """Cold 작가 (벡터에 없는) 도 유사 작가 반환."""
        works = _make_works()
        vectors = build_artist_feature_vectors(
            works, cutoff=500,
            session_col="회차", type_col="타입", price_col="낙찰가",
        )
        results = find_similar_artists("미등록작가", vectors, k=3, medium_filter="유화")
        assert len(results) > 0


class TestSimilarityFeatures:
    def test_similarity_features_keys(self) -> None:
        """4개 피처 키 반환."""
        artists = [
            SimilarArtist("A", 0.5, 15.0, 10),
            SimilarArtist("B", 1.0, 14.5, 8),
        ]
        feats = compute_similarity_features("target", artists)
        expected = {"sim_avg_price_ln", "sim_weighted_price_ln",
                    "sim_count", "sim_avg_distance"}
        assert set(feats.keys()) == expected

    def test_empty_similar_returns_zeros(self) -> None:
        """유사 작가 없으면 0."""
        feats = compute_similarity_features("target", [])
        assert feats["sim_count"] == 0
        assert feats["sim_avg_price_ln"] == 0.0

    def test_fallback_usage_rate(self) -> None:
        """5-tier에서 fallback(Tier 3+4) 사용률 < 40% 시뮬레이션."""
        works = _make_works(n_artists=50, n_per_artist=10)
        vectors = build_artist_feature_vectors(
            works, cutoff=500,
            session_col="회차", type_col="타입", price_col="낙찰가",
        )
        matched = sum(
            1 for a in vectors.index
            if len(find_similar_artists(a, vectors, k=3)) >= 3
        )
        assert matched / len(vectors) >= 0.6

    def test_cold_subgroup_coverage_ge_90(self) -> None:
        """Cold subgroup tier 배정률 ≥ 90% (G17)."""
        works = _make_works(n_artists=50, n_per_artist=10)
        vectors = build_artist_feature_vectors(
            works, cutoff=500,
            session_col="회차", type_col="타입", price_col="낙찰가",
        )

        # 모든 작가에 대해 similarity 탐색 → tier 배정 가능 확인
        covered = 0
        total = len(vectors)
        for artist in vectors.index:
            results = find_similar_artists(artist, vectors, k=3)
            if len(results) >= 1:
                covered += 1
        coverage = covered / total if total > 0 else 0
        assert coverage >= 0.9
