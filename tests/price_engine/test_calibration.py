"""calibration 단위 테스트."""
from __future__ import annotations

import numpy as np
import pandas as pd

from visionai.price_engine.validation.calibration import compute_calibration_table
from visionai.price_engine.validation.metrics import compute_metrics


class TestCalibration:
    """coverage 테이블 계산 테스트."""

    def test_perfect_prediction(self) -> None:
        y_true = np.array([100.0, 200.0, 300.0])
        y_pred = np.array([100.0, 200.0, 300.0])
        grades = pd.Series(["A", "A", "B"])
        cal = compute_calibration_table(y_true, y_pred, grades)
        a_row = cal[cal["grade"] == "A"]
        assert a_row.iloc[0]["within_20pct"] == 100.0

    def test_bad_prediction(self) -> None:
        y_true = np.array([100.0, 200.0])
        y_pred = np.array([200.0, 400.0])  # 100% 오차
        grades = pd.Series(["D", "D"])
        cal = compute_calibration_table(y_true, y_pred, grades)
        d_row = cal[cal["grade"] == "D"]
        assert d_row.iloc[0]["within_20pct"] == 0.0

    def test_all_grades_present(self) -> None:
        y_true = np.array([100.0] * 8)
        y_pred = np.array([100.0] * 8)
        grades = pd.Series(["A", "A", "B", "B", "C", "C", "D", "D"])
        cal = compute_calibration_table(y_true, y_pred, grades)
        assert set(cal["grade"].values) == {"A", "B", "C", "D"}


class TestMetrics:
    """metrics 계산 테스트."""

    def test_perfect(self) -> None:
        y = np.array([100.0, 200.0, 300.0])
        m = compute_metrics(y, y)
        assert m.mape == 0.0
        assert m.r2 == 1.0

    def test_known_mape(self) -> None:
        y_true = np.array([100.0, 200.0])
        y_pred = np.array([120.0, 160.0])  # 20%, 20%
        m = compute_metrics(y_true, y_pred)
        assert m.mape == 20.0
