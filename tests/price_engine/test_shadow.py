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
            "record_id": ["abc123", "def456"],
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

    def test_dedupe_removes_duplicates(self) -> None:
        """동일 record_id는 중복 제거."""
        records = [
            {
                "record_id": "same_id",
                "input": {"타입": "메이저", "회차": 180, "Lot": 1},
                "prediction": {"predicted_calibrated": 60000000},
                "actual": None,
            },
            {
                "record_id": "same_id",
                "input": {"타입": "메이저", "회차": 180, "Lot": 1},
                "prediction": {"predicted_calibrated": 60000000},
                "actual": None,
            },
        ]
        actuals = {("메이저", 180, 1): 65000000}
        scored = score_shadow_logs(records, actuals)
        assert len(scored) == 1

    def test_invalid_actual_not_scored(self) -> None:
        """actual ≤ 0은 scored=False."""
        records = [
            {
                "record_id": "inv1",
                "input": {"타입": "위클리", "회차": 450, "Lot": 3},
                "prediction": {"predicted_calibrated": 500000},
                "actual": None,
            },
        ]
        actuals = {("위클리", 450, 3): 0}
        scored = score_shadow_logs(records, actuals)
        assert not scored["scored"].any()

    def test_malformed_json_skipped(self) -> None:
        """손상된 JSONL 라인은 건너뜀."""
        import tempfile
        from visionai.price_engine.experiments.shadow_scorer import load_shadow_logs

        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "shadow_20260327.jsonl"
            log_file.write_text(
                '{"record_id":"a","input":{"타입":"메이저","회차":180,"Lot":1},"prediction":{"predicted_calibrated":60000000}}\n'
                'BROKEN LINE\n'
                '{"record_id":"b","input":{"타입":"메이저","회차":180,"Lot":2},"prediction":{"predicted_calibrated":70000000}}\n',
                encoding="utf-8",
            )
            records = load_shadow_logs(shadow_dir=Path(tmpdir))
            assert len(records) == 2  # broken line skipped
