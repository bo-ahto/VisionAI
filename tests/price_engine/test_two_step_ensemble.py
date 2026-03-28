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
        assert len(PRICE_BINS) == 4
        assert len(PRICE_LABELS) == 3
        assert PRICE_LABELS == ["low", "mid", "high"]

    def test_bin_boundaries(self) -> None:
        prices = pd.Series([1_000_000, 10_000_000, 50_000_000])
        cuts = pd.cut(prices, bins=PRICE_BINS, labels=PRICE_LABELS)
        assert cuts.iloc[0] == "low"
        assert cuts.iloc[1] == "mid"
        assert cuts.iloc[2] == "high"


class TestEnsembleContract:
    def test_import(self) -> None:
        from visionai.price_engine.estimate_generator.ensemble_model import (
            EnsembleStackingModel,
        )
        model = EnsembleStackingModel()
        assert not model._fitted

    def test_feature_count(self) -> None:
        assert len(HEDONIC_FEATURES) == 42
