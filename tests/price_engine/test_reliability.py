"""Reliability Model 단위 테스트."""
from __future__ import annotations

import numpy as np
import pandas as pd

from visionai.price_engine.reliability.reliability_features import extract_reliability_features
from visionai.price_engine.reliability.reliability_model import ReliabilityModel


class TestReliabilityFeatures:
    """메타피처 추출 테스트."""

    def test_basic_extraction(self) -> None:
        df = pd.DataFrame({
            "artist_total_sold": [50, 0, 10],
            "estimate_ratio": [1.5, 2.0, 1.2],
            "is_new_artist": [False, True, False],
            "artist_clean": ["A", "B", "C"],
            "회차": [400, 400, 400],
            "타입": ["위클리"] * 3,
        })
        meta = extract_reliability_features(df)
        assert len(meta) == 3
        assert "rel_artist_sold" in meta.columns
        assert "rel_estimate_ratio" in meta.columns
        assert "rel_is_new_artist" in meta.columns
        assert meta["rel_artist_sold"].iloc[0] == 50.0
        assert meta["rel_is_new_artist"].iloc[1] == 1.0

    def test_missing_columns_handled(self) -> None:
        df = pd.DataFrame({
            "artist_total_sold": [10],
            "estimate_ratio": [1.5],
            "is_new_artist": [False],
        })
        meta = extract_reliability_features(df)
        assert len(meta.columns) == 5


class TestReliabilityModel:
    """모델 학습/예측 테스트."""

    def test_fit_and_predict(self) -> None:
        np.random.seed(42)
        n = 200
        meta = pd.DataFrame({
            "rel_artist_sold": np.random.randint(0, 100, n).astype(float),
            "rel_premium_std": np.random.rand(n),
            "rel_recent_count": np.random.randint(0, 20, n).astype(float),
            "rel_estimate_ratio": 1.0 + np.random.rand(n),
            "rel_is_new_artist": np.random.choice([0.0, 1.0], n),
        })
        y_true = np.random.uniform(1e6, 1e8, n)
        y_pred = y_true * np.random.uniform(0.7, 1.3, n)

        model = ReliabilityModel(threshold=0.2)
        model.fit(meta, y_true, y_pred)

        proba = model.predict_proba(meta)
        assert len(proba) == n
        assert all(0 <= p <= 1 for p in proba)

    def test_grades_distribution(self) -> None:
        np.random.seed(42)
        n = 200
        meta = pd.DataFrame({
            "rel_artist_sold": np.random.randint(0, 100, n).astype(float),
            "rel_premium_std": np.random.rand(n),
            "rel_recent_count": np.random.randint(0, 20, n).astype(float),
            "rel_estimate_ratio": 1.0 + np.random.rand(n),
            "rel_is_new_artist": np.random.choice([0.0, 1.0], n),
        })
        y_true = np.random.uniform(1e6, 1e8, n)
        y_pred = y_true * np.random.uniform(0.7, 1.3, n)

        model = ReliabilityModel(threshold=0.2)
        model.fit(meta, y_true, y_pred)

        grades = model.assign_grades(meta)
        assert set(grades.unique()).issubset({"A", "B", "C", "D"})
        assert len(grades) == n
