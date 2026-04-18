"""Sprint 3: Strict/Distilled 2-트랙 격리 테스트."""
from __future__ import annotations

from visionai.price_engine.features.track_config import (
    _ESTIMATE_DERIVED,
    DISTILLED_TRAIN_ONLY_FEATURES,
    INFERENCE_FEATURES,
    STRICT_FEATURES,
    Track,
    get_distilled_train_features,
)


class TestTrackIsolation:
    def test_strict_no_estimate_cols(self) -> None:
        """Strict 트랙에 estimate-derived 피처 0개 (G10)."""
        for feat in STRICT_FEATURES:
            assert feat not in _ESTIMATE_DERIVED, (
                f"Strict feature '{feat}' is in _ESTIMATE_DERIVED"
            )

    def test_distilled_train_only(self) -> None:
        """Distilled train-only 피처가 estimate 관련."""
        assert "teacher_pred_oof" in DISTILLED_TRAIN_ONLY_FEATURES
        assert "global_estimate_avg" in DISTILLED_TRAIN_ONLY_FEATURES
        assert len(DISTILLED_TRAIN_ONLY_FEATURES) == 2

    def test_distilled_infer_no_teacher(self) -> None:
        """Inference 피처에 teacher/estimate 신호 없음 (G10)."""
        for feat in INFERENCE_FEATURES:
            assert "teacher" not in feat
            assert "estimate" not in feat.lower() or feat in STRICT_FEATURES

    def test_artifact_names(self) -> None:
        """Track enum 값이 artifact 명명과 일치."""
        assert Track.STRICT.value == "strict"
        assert Track.DISTILLED.value == "distilled"

    def test_distilled_train_features_superset(self) -> None:
        """Distilled train = Strict + train-only."""
        full = get_distilled_train_features()
        assert len(full) == len(STRICT_FEATURES) + len(DISTILLED_TRAIN_ONLY_FEATURES)
        for feat in STRICT_FEATURES:
            assert feat in full
        for feat in DISTILLED_TRAIN_ONLY_FEATURES:
            assert feat in full
