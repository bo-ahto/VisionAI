"""Sprint 1: 매크로 지표 피처 테스트."""
from __future__ import annotations

import pandas as pd

from visionai.price_engine.features.macro_indicators import (
    MACRO_FEATURES,
    join_macro_features,
)


class TestJoinMacroFeatures:
    def test_join_lag_1m(self) -> None:
        """1회차 래그: 회차 3 → session 2의 값."""
        df = pd.DataFrame({"회차": [2, 3, 4]})
        macro = pd.DataFrame({
            "session": [1, 2, 3],
            "kauction_sold_rate": [0.8, 0.85, 0.9],
            "kauction_avg_price": [1000, 2000, 3000],
            "kauction_avg_price_mom_3m": [1000, 1500, 2000],
        })
        result = join_macro_features(df, macro, session_col="회차", lag_sessions=1)
        row3 = result[result["회차"] == 3].iloc[0]
        # session 2의 값 → join_session=3에 매핑
        assert row3["kauction_sold_rate_prev"] == 0.85
        assert row3["kauction_avg_price_prev"] == 2000

    def test_missing_session_ffill(self) -> None:
        """결측 회차는 forward-fill로 이전 값 유지."""
        df = pd.DataFrame({"회차": [1, 2, 3, 4, 5]})
        macro = pd.DataFrame({
            "session": [1, 3, 5],
            "kauction_sold_rate": [0.8, 0.9, 0.95],
            "kauction_avg_price": [1000, 3000, 5000],
        })
        result = join_macro_features(df, macro, session_col="회차", lag_sessions=0)
        # 회차 2는 NaN → ffill → 회차 1의 값(0.8)
        row2 = result[result["회차"] == 2].iloc[0]
        assert row2["kauction_sold_rate_prev"] == 0.8

    def test_feature_count_7(self) -> None:
        """매크로 피처 수 = 7개."""
        assert len(MACRO_FEATURES) == 7

    def test_macro_months_ge_12(self) -> None:
        """매크로 세션 데이터 12개 이상 (G16)."""
        macro = pd.DataFrame({
            "session": range(1, 25),
            "kauction_sold_rate": [0.8] * 24,
            "kauction_avg_price": [1000000] * 24,
        })
        assert len(macro) >= 12

    def test_actual_values_not_zero(self) -> None:
        """매칭되는 세션이 있으면 0이 아닌 실제 값."""
        df = pd.DataFrame({"회차": [5, 10]})
        macro = pd.DataFrame({
            "session": [4, 9],
            "kauction_sold_rate": [0.75, 0.82],
            "kauction_avg_price": [5000000, 8000000],
        })
        result = join_macro_features(df, macro, session_col="회차", lag_sessions=1)
        row5 = result[result["회차"] == 5].iloc[0]
        assert row5["kauction_sold_rate_prev"] == 0.75
        assert row5["kauction_avg_price_prev"] == 5000000

    def test_no_session_column_defaults_to_zero(self) -> None:
        """session 컬럼 없으면 모두 0."""
        df = pd.DataFrame({"회차": [1, 2]})
        macro = pd.DataFrame({"year_month": ["202401"], "kospi": [2500]})
        result = join_macro_features(df, macro, session_col="회차")
        assert result["kauction_sold_rate_prev"].sum() == 0
