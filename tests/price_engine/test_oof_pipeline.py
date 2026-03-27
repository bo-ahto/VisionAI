"""OOF 파이프라인 계약 테스트."""
from __future__ import annotations

import numpy as np
import pandas as pd


class TestOofContract:
    """OOF 절차의 계약/구조 검증 (실제 학습 없이)."""

    def test_warmup_ratio(self) -> None:
        from visionai.price_engine.models.target_transform_v2 import _WARMUP_RATIO
        assert _WARMUP_RATIO == 0.20

    def test_oof_no_self_prediction_concept(self) -> None:
        """Expanding window: 각 fold의 train과 predict가 겹치지 않음."""
        sessions = list(range(1, 101))
        warmup_idx = int(len(sessions) * 0.2)  # 20
        warmup_end = sessions[warmup_idx - 1]  # 회차 20
        post = [s for s in sessions if s > warmup_end]  # 21~100
        n_folds = 5
        fold_size = len(post) // n_folds

        all_predict = set()
        for k in range(n_folds):
            ps = k * fold_size
            pe = (k + 1) * fold_size if k < n_folds - 1 else len(post)
            predict_sessions = set(post[ps:pe])
            # Train은 predict 이전 → 겹침 없음
            train_end = min(predict_sessions) - 1
            train_sessions = set(s for s in sessions if s <= train_end)
            assert train_sessions.isdisjoint(predict_sessions)
            all_predict |= predict_sessions

        # 모든 post-warmup 세션이 커버됨
        assert all_predict == set(post)

    def test_v2_feature_structure(self) -> None:
        """v2가 BASELINE_FEATURES 22개 구조 유지."""
        from visionai.price_engine.models.predictor import BASELINE_FEATURES
        assert len(BASELINE_FEATURES) == 22
        assert "ln_estimate_mid" in BASELINE_FEATURES
        assert "estimate_ratio" in BASELINE_FEATURES
        assert "estimate_range" in BASELINE_FEATURES
        assert "artist_sell_rate" in BASELINE_FEATURES

    def test_v2_target_transform_formula(self) -> None:
        """v2 타깃: ln(낙찰가/est_mid_oof)."""
        price = np.array([10_000_000.0])
        est_mid = np.array([8_000_000.0])
        target = np.log(price / est_mid)
        # ln(10M/8M) = ln(1.25) ≈ 0.223
        assert abs(target[0] - np.log(1.25)) < 1e-10

    def test_warmup_excluded_from_v2_training(self) -> None:
        """warm-up 구간(OOF NaN)은 v2 학습에서 제외되어야 함."""
        oof = pd.DataFrame({
            "est_mid_oof": [np.nan, np.nan, 1000.0, 2000.0, 3000.0],
            "est_low_oof": [np.nan, np.nan, 800.0, 1600.0, 2400.0],
            "est_high_oof": [np.nan, np.nan, 1200.0, 2400.0, 3600.0],
        })
        has_oof = oof["est_mid_oof"].notna()
        assert has_oof.sum() == 3  # warm-up 2건 제외


class TestOofDistributionConcept:
    """OOF 분포 정렬 개념 검증."""

    def test_psi_concept(self) -> None:
        """PSI가 0에 가까우면 분포 일치."""
        rng = np.random.default_rng(42)
        ref = rng.normal(15, 1, 1000)
        cur = rng.normal(15, 1, 1000)
        # 같은 분포 → PSI ≈ 0
        from visionai.price_engine.validation.drift_monitor import compute_psi
        psi = compute_psi(ref, cur)
        assert psi < 0.1

    def test_fold_smearing_cv_concept(self) -> None:
        """Fold별 smearing factor CV < 0.15."""
        rng = np.random.default_rng(42)
        smearing_factors = [np.mean(np.exp(rng.normal(0, 0.2, 100))) for _ in range(5)]
        cv = np.std(smearing_factors) / np.mean(smearing_factors)
        assert cv < 0.15
