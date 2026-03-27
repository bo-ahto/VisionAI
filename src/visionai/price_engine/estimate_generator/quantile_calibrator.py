"""Prediction Interval Calibration — additive shift.

Raw Quantile(Model-A) → Calibrated Prediction Interval.
Calib set에서 학습, Validation에서 검증, Test에서 1회 적용.

기획서 3.2.1절 참조.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class CalibrationResult:
    """Calibration 결과."""

    delta_low: float
    delta_mid: float
    delta_high: float
    coverage_before: float
    coverage_after: float


class QuantileCalibrator:
    """Prediction Interval calibration via additive shift.

    Raw Quantile → Calibrated Prediction Interval:
    - 보정 하한 = q_25 + delta_low
    - 보정 중앙 = q_50 + delta_mid
    - 보정 상한 = q_75 + delta_high

    delta는 Calib set 잔차 분포에서 목표 coverage를 달성하도록 산출.
    """

    def __init__(self) -> None:
        self.delta_low: float = 0.0
        self.delta_mid: float = 0.0
        self.delta_high: float = 0.0
        self._fitted: bool = False

    def fit(
        self,
        y_calib: np.ndarray,
        q_pred_calib: np.ndarray,
        target_coverage: float = 0.55,
    ) -> CalibrationResult:
        """Calib set에서 delta_low, delta_high, delta_mid 산출.

        Args:
            y_calib: 실제 ln(낙찰가), shape (n,).
            q_pred_calib: raw quantile 예측, shape (n, 3) = [q25, q50, q75].
            target_coverage: 목표 coverage 비율.

        Returns:
            CalibrationResult with deltas and coverage before/after.
        """
        q25 = q_pred_calib[:, 0]
        q50 = q_pred_calib[:, 1]
        q75 = q_pred_calib[:, 2]

        # 보정 전 coverage
        covered_before = (y_calib >= q25) & (y_calib <= q75)
        coverage_before = float(np.mean(covered_before))

        # 잔차 계산
        r_low = y_calib - q25   # 양수 = 실제가 q25 위
        r_high = y_calib - q75  # 음수 = 실제가 q75 아래

        # 중앙값 bias 보정
        r_mid = y_calib - q50
        self.delta_mid = float(np.median(r_mid))

        # 독립 2D grid search: alpha_low, alpha_high를 각각 탐색 (기획서 3.2.1절)
        grid = np.linspace(0.01, 0.99, 50)
        best_delta_low = 0.0
        best_delta_high = 0.0
        best_coverage = coverage_before
        best_width = float("inf")

        for a_low in grid:
            d_low = float(np.quantile(r_low, a_low))
            adj_low = q25 + d_low
            for a_high in grid:
                d_high = float(np.quantile(r_high, a_high))
                adj_high = q75 + d_high
                covered = (y_calib >= adj_low) & (y_calib <= adj_high)
                cov = float(np.mean(covered))
                width = float(np.mean(adj_high - adj_low))

                if cov >= target_coverage and width < best_width:
                    best_delta_low = d_low
                    best_delta_high = d_high
                    best_coverage = cov
                    best_width = width

        # target 미달 시 최대 확장
        if best_coverage < target_coverage:
            best_delta_low = float(np.quantile(r_low, 0.01))
            best_delta_high = float(np.quantile(r_high, 0.99))
            adj_low = q25 + best_delta_low
            adj_high = q75 + best_delta_high
            covered = (y_calib >= adj_low) & (y_calib <= adj_high)
            best_coverage = float(np.mean(covered))

        self.delta_low = best_delta_low
        self.delta_high = best_delta_high
        self._fitted = True

        logger.info(
            "QuantileCalibrator fit: delta_low=%.4f, delta_mid=%.4f, delta_high=%.4f, "
            "coverage %.1f%% → %.1f%%",
            self.delta_low, self.delta_mid, self.delta_high,
            coverage_before * 100, best_coverage * 100,
        )

        return CalibrationResult(
            delta_low=self.delta_low,
            delta_mid=self.delta_mid,
            delta_high=self.delta_high,
            coverage_before=coverage_before,
            coverage_after=best_coverage,
        )

    def transform(self, q_pred: np.ndarray) -> np.ndarray:
        """Raw quantile에 additive shift 적용.

        Args:
            q_pred: shape (n, 3) = [q25, q50, q75] (log scale).

        Returns:
            Calibrated prediction interval, shape (n, 3).
        """
        if not self._fitted:
            msg = "Calibrator not fitted. Call fit() first."
            raise RuntimeError(msg)

        out = q_pred.copy()
        out[:, 0] += self.delta_low
        out[:, 1] += self.delta_mid
        out[:, 2] += self.delta_high
        # 단조성 보장: low <= mid <= high
        out[:, 0] = np.minimum(out[:, 0], out[:, 1])
        out[:, 2] = np.maximum(out[:, 2], out[:, 1])
        return out

    def validate_coverage(
        self,
        y_valid: np.ndarray,
        q_pred_valid: np.ndarray,
        auction_types: np.ndarray | None = None,
    ) -> dict[str, float]:
        """Validation set에서 calibrated coverage 검증.

        Args:
            y_valid: 실제 ln(낙찰가).
            q_pred_valid: raw quantile 예측, shape (n, 3).
            auction_types: 경매 유형 배열 (slice별 coverage 계산용).

        Returns:
            dict with coverage_overall + slice별 coverage.
        """
        calibrated = self.transform(q_pred_valid)
        covered = (y_valid >= calibrated[:, 0]) & (y_valid <= calibrated[:, 2])
        result: dict[str, float] = {
            "coverage_overall": float(np.mean(covered)),
            "n": float(len(y_valid)),
        }

        if auction_types is not None:
            for atype in np.unique(auction_types):
                mask = auction_types == atype
                if mask.sum() > 0:
                    key = f"coverage_{atype}"
                    result[key] = float(np.mean(covered[mask]))

        return result
