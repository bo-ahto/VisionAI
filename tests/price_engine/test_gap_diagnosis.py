"""Sprint 0: Gap 진단 함수 단위 테스트."""
from __future__ import annotations

# diagnose_gap은 scripts/에 있으므로 sys.path에 추가
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from diagnose_gap import (  # noqa: E402
    compute_missingness_drift,
    compute_psi,
    compute_segment_performance,
    compute_time_performance_curve,
)


class TestComputePSI:
    def test_psi_identical(self) -> None:
        """동일 분포 PSI는 0에 가까워야 함."""
        rng = np.random.default_rng(42)
        data = rng.normal(0, 1, 1000)
        psi = compute_psi(data, data)
        assert psi < 0.01

    def test_psi_shifted(self) -> None:
        """평균이 크게 shift된 분포는 PSI > 0.1."""
        rng = np.random.default_rng(42)
        expected = rng.normal(0, 1, 1000)
        actual = rng.normal(3, 1, 1000)  # 평균 3 shift
        psi = compute_psi(expected, actual)
        assert psi > 0.1


class TestMissingnessDrift:
    def test_missingness_no_change(self) -> None:
        """결측률 동일 시 drift ≈ 0."""
        df_v = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        df_t = pd.DataFrame({"a": [7, 8, 9], "b": [10, 11, 12]})
        result = compute_missingness_drift(df_v, df_t, ["a", "b"])
        assert all(abs(row["drift"]) < 0.01 for _, row in result.iterrows())

    def test_missingness_increase(self) -> None:
        """결측률 증가 시 drift > 0."""
        df_v = pd.DataFrame({"a": [1, 2, 3]})
        df_t = pd.DataFrame({"a": [np.nan, np.nan, 3]})
        result = compute_missingness_drift(df_v, df_t, ["a"])
        assert result.iloc[0]["drift"] > 0


class TestSegmentPerformance:
    def test_segment_keys(self) -> None:
        """세그먼트별 결과에 mdape, r2, n 키 포함."""
        df = pd.DataFrame({"seg": ["A", "A", "B", "B"]})
        y_pred = np.array([100, 200, 300, 400])
        y_true = np.array([110, 190, 310, 390])
        result = compute_segment_performance(df, y_pred, y_true, "seg")
        for seg_val in ["A", "B"]:
            assert "mdape" in result[seg_val]
            assert "r2" in result[seg_val]
            assert "n" in result[seg_val]


class TestTimeCurve:
    def test_time_curve_sorted(self) -> None:
        """회차별 결과가 session 오름차순."""
        df = pd.DataFrame({"회차": [3, 1, 2, 3, 1, 2]})
        y_pred = np.array([100, 200, 300, 100, 200, 300])
        y_true = np.array([110, 190, 310, 110, 190, 310])
        result = compute_time_performance_curve(df, y_pred, y_true)
        sessions = result["session"].tolist()
        assert sessions == sorted(sessions)
