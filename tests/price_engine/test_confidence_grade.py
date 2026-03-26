"""confidence_grade 단위 테스트."""
from __future__ import annotations

import pandas as pd

from visionai.price_engine.validation.confidence_grade import assign_confidence_grade


def _make_df(sold: int, est_low: int = 40_000_000, est_high: int = 60_000_000) -> pd.DataFrame:
    return pd.DataFrame({
        "artist_total_sold": [sold],
        "artist_clean": ["TestArtist"],
        "회차": [400],
        "타입": ["위클리"],
        "추정가(최저)": [est_low],
        "추정가(최고)": [est_high],
    })


class TestConfidenceGrade:
    """등급 경계 테스트."""

    def test_d_grade_zero_sold(self) -> None:
        grades = assign_confidence_grade(_make_df(sold=0))
        assert grades.iloc[0] == "D"

    def test_c_grade_1_sold(self) -> None:
        grades = assign_confidence_grade(_make_df(sold=1))
        assert grades.iloc[0] == "C"

    def test_c_grade_5_sold(self) -> None:
        grades = assign_confidence_grade(_make_df(sold=5))
        assert grades.iloc[0] == "C"

    def test_b_grade_6_sold(self) -> None:
        grades = assign_confidence_grade(_make_df(sold=6))
        assert grades.iloc[0] == "B"

    def test_b_grade_19_sold(self) -> None:
        grades = assign_confidence_grade(_make_df(sold=19))
        assert grades.iloc[0] == "B"

    def test_a_grade_20_sold_high_price(self) -> None:
        """sold≥20 + 추정가 3000만 이상이면 A."""
        grades = assign_confidence_grade(_make_df(sold=20))
        assert grades.iloc[0] == "A"

    def test_b_grade_20_sold_low_price(self) -> None:
        """sold≥20이라도 추정가 < 3000만이면 B."""
        grades = assign_confidence_grade(_make_df(sold=20, est_low=3_000_000, est_high=5_000_000))
        assert grades.iloc[0] == "B"

    def test_a_excluded_ultra_high_price(self) -> None:
        """>10억 추정가는 A 불가."""
        grades = assign_confidence_grade(
            _make_df(sold=100, est_low=1_500_000_000, est_high=2_000_000_000)
        )
        assert grades.iloc[0] == "B"

    def test_d_when_no_estimate(self) -> None:
        """추정가 없으면 sold 많아도 D."""
        grades = assign_confidence_grade(_make_df(sold=50, est_low=0, est_high=0))
        assert grades.iloc[0] == "D"

    def test_a_demoted_without_recent(self) -> None:
        """최근 거래 없으면 A→B 강등."""
        df = _make_df(sold=60)
        # works_full에 최근 20회차 내 거래 없음
        works = pd.DataFrame({
            "타입": ["위클리"],
            "artist_clean": ["TestArtist"],
            "회차": [100],  # 400 - 100 = 300 > 20
        })
        grades = assign_confidence_grade(df, works_full=works)
        assert grades.iloc[0] == "B"

    def test_a_kept_with_recent(self) -> None:
        """최근 거래 있으면 A 유지."""
        df = _make_df(sold=60)
        works = pd.DataFrame({
            "타입": ["위클리"],
            "artist_clean": ["TestArtist"],
            "회차": [390],  # 400 - 390 = 10 < 20
        })
        grades = assign_confidence_grade(df, works_full=works)
        assert grades.iloc[0] == "A"
