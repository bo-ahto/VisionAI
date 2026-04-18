"""Two-Step + Ensemble 계약 테스트."""
from __future__ import annotations

import numpy as np
import pandas as pd

from visionai.price_engine.estimate_generator.hedonic_features import HEDONIC_FEATURES
from visionai.price_engine.estimate_generator.two_step_model import (
    PRICE_BINS,
    PRICE_LABELS,
)


class TestTwoStepContract:
    def test_price_bins(self) -> None:
        assert len(PRICE_BINS) == 6
        assert len(PRICE_LABELS) == 5
        assert PRICE_LABELS == ["budget", "low", "mid", "high", "premium"]

    def test_bin_boundaries(self) -> None:
        prices = pd.Series([500_000, 3_000_000, 10_000_000, 50_000_000, 200_000_000])
        cuts = pd.cut(prices, bins=PRICE_BINS, labels=PRICE_LABELS)
        assert cuts.iloc[0] == "budget"   # 500K
        assert cuts.iloc[1] == "low"     # 3M
        assert cuts.iloc[2] == "mid"     # 10M
        assert cuts.iloc[3] == "high"    # 50M
        assert cuts.iloc[4] == "premium" # 200M


class TestEnsembleContract:
    def test_import(self) -> None:
        from visionai.price_engine.estimate_generator.ensemble_model import (
            EnsembleStackingModel,
        )
        model = EnsembleStackingModel()
        assert not model._fitted

    def test_feature_count(self) -> None:
        # 2026-04-17 Cold Start SHAP 분석 후 해로운 4개 제거 (50 → 46).
        assert len(HEDONIC_FEATURES) == 46
