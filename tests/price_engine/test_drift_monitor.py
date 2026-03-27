"""드리프트 모니터링 단위 테스트."""
from __future__ import annotations

import numpy as np
import pandas as pd

from visionai.price_engine.validation.drift_monitor import (
    check_feature_drift,
    compute_ks,
    compute_psi,
    compute_rolling_mape,
)


class TestPSI:
    def test_identical_distributions(self) -> None:
        ref = np.random.normal(0, 1, 1000)
        assert compute_psi(ref, ref) < 0.05

    def test_shifted_distribution(self) -> None:
        ref = np.random.normal(0, 1, 1000)
        cur = np.random.normal(2, 1, 1000)  # 큰 shift
        assert compute_psi(ref, cur) > 0.2

    def test_small_sample(self) -> None:
        assert compute_psi(np.array([1.0, 2.0]), np.array([1.0, 2.0])) == 0.0


class TestKS:
    def test_identical(self) -> None:
        ref = np.random.normal(0, 1, 500)
        stat, pval = compute_ks(ref, ref)
        assert stat == 0.0
        assert pval == 1.0

    def test_different(self) -> None:
        ref = np.random.normal(0, 1, 500)
        cur = np.random.normal(3, 1, 500)
        stat, pval = compute_ks(ref, cur)
        assert stat > 0.5
        assert pval < 0.01


class TestFeatureDrift:
    def test_no_alert_same_data(self) -> None:
        df = pd.DataFrame({"ln_estimate_mid": np.random.normal(15, 2, 200)})
        results = check_feature_drift(df, df, features=["ln_estimate_mid"])
        assert len(results) == 1
        assert not results[0].alert

    def test_alert_on_shift(self) -> None:
        ref = pd.DataFrame({"ln_estimate_mid": np.random.normal(15, 2, 200)})
        cur = pd.DataFrame({"ln_estimate_mid": np.random.normal(20, 2, 200)})
        results = check_feature_drift(ref, cur, features=["ln_estimate_mid"])
        assert results[0].alert


class TestRollingMAPE:
    def test_basic(self) -> None:
        y_true = np.array([100, 200, 300, 400, 500, 600, 700, 800])
        y_pred = np.array([110, 180, 310, 380, 520, 590, 710, 790])
        periods = np.array([1, 1, 2, 2, 3, 3, 4, 4])
        result = compute_rolling_mape(y_true, y_pred, periods, window_size=2)
        assert len(result) >= 1
        assert "mape" in result.columns
