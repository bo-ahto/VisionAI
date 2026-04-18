"""Hedonic 피처 생성 검증 테스트."""
from __future__ import annotations

import numpy as np
import pandas as pd

from visionai.price_engine.features.hedonic_stats import (
    compute_artist_median_price,
    compute_artist_price_trend,
    compute_artist_unsold_rate,
    compute_medium_avg_price,
    compute_size_ho,
    compute_size_ho_above40,
    parse_edition,
)


def _sample_works() -> pd.DataFrame:
    return pd.DataFrame({
        "회차": [10, 10, 20, 20, 30, 30, 40, 40],
        "타입": ["메이저"] * 8,
        "artist_clean": ["A", "A", "A", "B", "B", "B", "B", "B"],
        "낙찰가": [1_000_000, 2_000_000, 3_000_000, 500_000, 800_000, 1_200_000, 1_500_000, 2_000_000],
        "medium_category": ["유화", "유화", "유화", "수채", "수채", "수채", "수채", "수채"],
        "상태": ["낙찰", "낙찰", "낙찰", "낙찰", "유찰", "낙찰", "낙찰", "낙찰"],
    })


class TestArtistMedianPrice:
    def test_basic(self) -> None:
        works = _sample_works()
        result = compute_artist_median_price(works, cutoff=50, session_col="회차", type_col="타입", price_col="낙찰가")
        assert "A" in result.index
        assert "B" in result.index
        assert result["A"] > 0

    def test_strict_cutoff(self) -> None:
        works = _sample_works()
        result = compute_artist_median_price(works, cutoff=20, session_col="회차", type_col="타입", price_col="낙찰가")
        # 회차 < 20 → 회차 10만 포함
        assert "A" in result.index
        # A의 회차 10 데이터만: 1M, 2M → 중앙값 1.5M
        assert result["A"] > 0

    def test_empty_returns_empty(self) -> None:
        works = _sample_works()
        result = compute_artist_median_price(works, cutoff=1, session_col="회차", type_col="타입", price_col="낙찰가")
        assert len(result) == 0


class TestArtistPriceTrend:
    def test_insufficient_data_returns_nan(self) -> None:
        works = _sample_works()
        result = compute_artist_price_trend(works, cutoff=30, session_col="회차", type_col="타입", price_col="낙찰가")
        # A: 2건 (< 5) → NaN
        assert np.isnan(result.get("A", np.nan))

    def test_sufficient_data(self) -> None:
        works = _sample_works()
        result = compute_artist_price_trend(works, cutoff=50, session_col="회차", type_col="타입", price_col="낙찰가")
        # B: 5건 → trend 계산 가능
        assert "B" in result.index


class TestMediumAvgPrice:
    def test_basic(self) -> None:
        works = _sample_works()
        result = compute_medium_avg_price(works, cutoff=50, session_col="회차", type_col="타입", price_col="낙찰가")
        assert "유화" in result.index or "수채" in result.index

    def test_strict_cutoff(self) -> None:
        works = _sample_works()
        r1 = compute_medium_avg_price(works, cutoff=20, session_col="회차", type_col="타입", price_col="낙찰가")
        r2 = compute_medium_avg_price(works, cutoff=50, session_col="회차", type_col="타입", price_col="낙찰가")
        if "유화" in r1.index and "유화" in r2.index:
            assert r1["유화"] != r2["유화"]

    def test_uses_mean_of_log_not_log_of_mean(self) -> None:
        """shrinkage 입력이 mean(log(price))인지 검증 (log(mean(price))이 아님)."""
        works = pd.DataFrame({
            "회차": [10] * 40,
            "타입": ["메이저"] * 40,
            "artist_clean": [f"A{i}" for i in range(40)],
            "낙찰가": [100_000] * 20 + [10_000_000] * 20,  # 극단적 이분포
            "medium_category": ["유화"] * 40,
            "상태": ["낙찰"] * 40,
        })
        result = compute_medium_avg_price(works, cutoff=50, auction_type="메이저")
        # mean(log) 방식: exp(mean(log(100K), log(10M))) ≈ exp(mean(11.5, 16.1)) ≈ exp(13.8) ≈ 1M
        # log(mean) 방식: exp(log(mean(100K, 10M))) = exp(log(5.05M)) ≈ 5.05M
        # mean(log) 방식이면 결과는 5M보다 훨씬 작아야 함
        assert result["유화"] < 3_000_000  # mean(log) 방식 확인


class TestSizeHo:
    def test_conversion(self) -> None:
        area = pd.Series([132.0, 264.0, 660.0, 0.0])
        ho = compute_size_ho(area)
        np.testing.assert_allclose(ho.values, [1.0, 2.0, 5.0, 0.0])

    def test_above40(self) -> None:
        ho = pd.Series([30.0, 40.0, 50.0, 100.0])
        above = compute_size_ho_above40(ho)
        np.testing.assert_allclose(above.values, [0.0, 0.0, 10.0, 60.0])


class TestArtistUnsoldRate:
    def test_basic(self) -> None:
        works = _sample_works()
        result = compute_artist_unsold_rate(works, cutoff=50, session_col="회차", type_col="타입", status_col="상태")
        # B: 1 유찰 / 5 출품 = 0.2
        assert "B" in result.index
        assert abs(result["B"] - 0.2) < 0.01

    def test_insufficient_returns_nan(self) -> None:
        works = _sample_works()
        result = compute_artist_unsold_rate(works, cutoff=15, session_col="회차", type_col="타입", status_col="상태")
        # A: 2건 (< 3) → NaN
        if "A" in result.index:
            assert np.isnan(result["A"])


class TestParseEdition:
    def test_has_edition(self) -> None:
        assert parse_edition("작품 23/50") is True
        assert parse_edition("Edition 1 / 30") is True

    def test_no_edition(self) -> None:
        assert parse_edition("무제 2023") is False
        assert parse_edition("Untitled") is False

    def test_empty(self) -> None:
        assert parse_edition("") is None
        assert parse_edition(None) is None
