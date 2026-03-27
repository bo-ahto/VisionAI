"""Shadow deployment 단위 테스트."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from visionai.price_engine.experiments.shadow_scorer import (
    generate_shadow_report,
    score_shadow_logs,
)


class TestShadowScorer:
    """retrospective scoring 테스트."""

    def test_score_with_actuals(self) -> None:
        records = [
            {
                "timestamp": "2026-03-27T10:00:00",
                "input": {"타입": "메이저", "회차": 180, "Lot": 1, "추정가_최저": 5e7, "추정가_최고": 8e7},
                "prediction": {"predicted_raw": 60000000, "predicted_calibrated": 62000000, "estimate_mid": 65000000},
                "actual": None,
                "scored": False,
            },
            {
                "timestamp": "2026-03-27T10:00:01",
                "input": {"타입": "메이저", "회차": 180, "Lot": 2, "추정가_최저": 3e7, "추정가_최고": 5e7},
                "prediction": {"predicted_raw": 35000000, "predicted_calibrated": 36000000, "estimate_mid": 40000000},
                "actual": None,
                "scored": False,
            },
        ]
        actuals = {
            ("메이저", 180, 1): 65000000,
            ("메이저", 180, 2): 40000000,
        }
        scored = score_shadow_logs(records, actuals)
        assert len(scored) == 2
        assert scored["scored"].all()
        assert scored["ape"].notna().all()

    def test_score_without_actuals_pending(self) -> None:
        records = [
            {
                "timestamp": "2026-03-27T10:00:00",
                "input": {"타입": "위클리", "회차": 450, "Lot": 5, "추정가_최저": 1e6, "추정가_최고": 2e6},
                "prediction": {"predicted_raw": 1200000, "predicted_calibrated": 1100000, "estimate_mid": 1500000},
                "actual": None,
                "scored": False,
            },
        ]
        scored = score_shadow_logs(records)
        assert not scored["scored"].any()

    def test_report_empty(self) -> None:
        scored = pd.DataFrame({"타입": [], "회차": [], "Lot": [], "predicted": [], "actual": [], "ape": [], "scored": []})
        report = generate_shadow_report(scored)
        assert "아직 scoring된 기록이 없습니다" in report

    def test_report_with_data(self) -> None:
        scored = pd.DataFrame({
            "타입": ["메이저", "메이저"],
            "회차": [180, 180],
            "Lot": [1, 2],
            "predicted": [62000000, 36000000],
            "actual": [65000000, 40000000],
            "ape": [4.6, 10.0],
            "scored": [True, True],
        })
        report = generate_shadow_report(scored)
        assert "MAPE" in report
        assert "메이저" in report
