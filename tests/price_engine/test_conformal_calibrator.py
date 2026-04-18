"""Sprint 3: Conformalized Quantile Regression (CQR) 테스트."""
from __future__ import annotations

import numpy as np

from visionai.price_engine.estimate_generator.conformal_calibrator import (
    ConformalQuantileCalibrator,
)


def _make_calib_data(
    n: int = 500, seed: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    """합성 calib 데이터: y와 q_pred (q25/q50/q75)."""
    rng = np.random.default_rng(seed)
    y = rng.normal(15, 1, n)
    noise = rng.normal(0, 0.3, (n, 3))
    q_pred = np.column_stack([
        y - 0.5 + noise[:, 0],  # q25
        y + noise[:, 1],         # q50
        y + 0.5 + noise[:, 2],  # q75
    ])
    return y, q_pred


class TestCQRCoverage:
    def test_cqr_coverage(self) -> None:
        """CQR coverage ≥ 1-alpha (G11)."""
        y, q_pred = _make_calib_data(500)
        cqr = ConformalQuantileCalibrator(alpha=0.45)

        # Calib: 전반부, Valid: 후반부
        cqr.fit(y[:250], q_pred[:250])
        result = cqr.validate_coverage(y[250:], q_pred[250:])
        assert result["coverage_overall"] >= 1 - 0.45 - 0.05  # 5%p 마진

    def test_cqr_adaptive_width(self) -> None:
        """CQR 구간 폭이 적응적 (고분산 vs 저분산)."""
        rng = np.random.default_rng(42)
        n = 200

        # 저분산 그룹
        y_low = rng.normal(15, 0.3, n)
        q_low = np.column_stack([y_low - 0.3, y_low, y_low + 0.3])

        # 고분산 그룹
        y_high = rng.normal(15, 2.0, n)
        q_high = np.column_stack([y_high - 2.0, y_high, y_high + 2.0])

        y = np.concatenate([y_low, y_high])
        q = np.vstack([q_low, q_high])

        cqr = ConformalQuantileCalibrator(alpha=0.45)
        cqr.fit(y, q)
        calibrated = cqr.predict(q)

        width_low = np.median(calibrated[:n, 2] - calibrated[:n, 0])
        width_high = np.median(calibrated[n:, 2] - calibrated[n:, 0])

        # 고분산 그룹의 구간이 더 넓어야 함
        assert width_high > width_low

    def test_temporal_3_windows(self) -> None:
        """3개 시간 윈도우 모두 coverage 충족 (G11)."""
        y, q_pred = _make_calib_data(600)
        cqr = ConformalQuantileCalibrator(alpha=0.45)
        cqr.fit(y[:200], q_pred[:200])

        y_windows = [y[200:300], y[300:400], y[400:500]]
        q_windows = [q_pred[200:300], q_pred[300:400], q_pred[400:500]]

        result = cqr.validate_temporal_coverage(y_windows, q_windows)
        assert result["all_pass"] == 1.0

    def test_width_not_excessive(self) -> None:
        """CQR 구간 폭이 기존 대비 과도하지 않음."""
        y, q_pred = _make_calib_data(500)
        cqr = ConformalQuantileCalibrator(alpha=0.45)
        cqr.fit(y[:250], q_pred[:250])

        calibrated = cqr.predict(q_pred[250:])
        original_width = np.median(q_pred[250:, 2] - q_pred[250:, 0])
        cqr_width = np.median(calibrated[:, 2] - calibrated[:, 0])

        # CQR 구간이 원본의 3배를 넘지 않아야 함
        assert cqr_width < original_width * 3.0

    def test_save_load(self, tmp_path) -> None:
        """CQR save/load 후 동일 Q."""
        y, q_pred = _make_calib_data(200)
        cqr = ConformalQuantileCalibrator(alpha=0.45)
        cqr.fit(y, q_pred)
        q_before = cqr._Q

        path = str(tmp_path / "cqr.pkl")
        cqr.save(path)

        cqr2 = ConformalQuantileCalibrator()
        cqr2.load(path)
        assert q_before == cqr2._Q
        assert cqr2._fitted is True

    def test_vs_additive(self) -> None:
        """CQR coverage ≥ additive shift coverage."""
        y, q_pred = _make_calib_data(500)

        # CQR
        cqr = ConformalQuantileCalibrator(alpha=0.45)
        cqr.fit(y[:250], q_pred[:250])
        cqr_result = cqr.validate_coverage(y[250:], q_pred[250:])

        # 기존 additive shift (전역 상수)
        r_low = y[:250] - q_pred[:250, 0]
        r_high = y[:250] - q_pred[:250, 2]
        delta_low = float(np.median(r_low))
        delta_high = float(np.median(r_high))
        additive_low = q_pred[250:, 0] + delta_low
        additive_high = q_pred[250:, 2] + delta_high
        additive_covered = (y[250:] >= additive_low) & (y[250:] <= additive_high)
        additive_cov = float(np.mean(additive_covered))

        assert cqr_result["coverage_overall"] >= additive_cov - 0.05
