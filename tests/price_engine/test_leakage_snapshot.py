"""Leakage Unit Test — fold별 미래 데이터 미포함 검증.

기획서 참조: 3.3 규칙 4
"""
from __future__ import annotations

import pandas as pd
import pytest

from visionai.price_engine.features.artist_stats_snapshot import (
    compute_artist_stats_snapshot,
)
from visionai.price_engine.features.splits import assign_split


@pytest.fixture()
def sample_works() -> pd.DataFrame:
    """테스트용 소규모 작품 데이터."""
    return pd.DataFrame(
        {
            "타입": ["위클리"] * 6,
            "회차": [100, 200, 300, 400, 450, 460],
            "Lot": [1, 1, 1, 1, 1, 1],
            "작가": ["A", "A", "A", "B", "B", "A"],
            "낙찰가": [1000000, 2000000, 3000000, 5000000, 6000000, 4000000],
            "추정가(최저)": [500000] * 6,
            "추정가(최고)": [1500000] * 6,
        }
    )


class TestLeakageSnapshot:
    """작가 통계 스냅샷이 미래 데이터를 포함하지 않는지 검증."""

    def test_snapshot_excludes_future(self, sample_works: pd.DataFrame) -> None:
        """cutoff=300이면 회차 300 이상 데이터는 미포함."""
        stats = compute_artist_stats_snapshot(
            sample_works, session_col="회차", type_col="타입", price_col="낙찰가", cutoff_session=300, auction_type="위클리"
        )
        # 작가 A: 회차 100, 200만 포함 (300은 strict <이므로 미포함)
        assert stats.loc["A", "artist_total_sold"] == 2
        assert stats.loc["A", "artist_avg_price"] == 1500000
        # 작가 B: 회차 300 미만 데이터 없음
        assert "B" not in stats.index

    def test_snapshot_empty_for_first_session(
        self, sample_works: pd.DataFrame
    ) -> None:
        """첫 회차에서는 스냅샷이 비어있어야 한다."""
        stats = compute_artist_stats_snapshot(
            sample_works, session_col="회차", type_col="타입", price_col="낙찰가", cutoff_session=100, auction_type="위클리"
        )
        assert stats.empty

    def test_no_same_session_leakage(self, sample_works: pd.DataFrame) -> None:
        """같은 회차 데이터는 포함되지 않는다 (strict <)."""
        stats = compute_artist_stats_snapshot(
            sample_works, session_col="회차", type_col="타입", price_col="낙찰가", cutoff_session=200, auction_type="위클리"
        )
        # 회차 200은 미포함, 회차 100만 포함
        assert stats.loc["A", "artist_total_sold"] == 1


class TestSplitAssignment:
    """시계열 분할 테스트."""

    def test_split_labels(self, sample_works: pd.DataFrame) -> None:
        splits = assign_split(sample_works)
        # 회차 100, 200, 300 → train (≤ 380)
        assert splits.iloc[0] == "train"
        assert splits.iloc[2] == "train"
        # 회차 400 → valid (381~430)
        assert splits.iloc[3] == "valid"
        # 회차 450, 460 → test (> 430)
        assert splits.iloc[4] == "test"
        assert splits.iloc[5] == "test"

    def test_no_unknown_labels(self, sample_works: pd.DataFrame) -> None:
        splits = assign_split(sample_works)
        assert "unknown" not in splits.values
