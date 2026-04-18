"""Conformalized Quantile Regression (CQR).

Romano et al. (2019) 기반.
exchangeability 가정 하 calibration split에서 coverage ≥ 1-alpha 보장.
시계열 환경: split-by-time 또는 weighted conformal로 별도 검증 필수.

Phase 5 Sprint 3 기획서 참조.
"""
from __future__ import annotations

import logging
import pickle
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


class ConformalQuantileCalibrator:
    """CQR — 적응적 prediction interval.

    Base quantile model의 q_low/q_high 출력에 conformity score Q를 가감하여
    coverage ≥ 1-alpha를 보장하는 prediction interval 생성.
    """

    def __init__(self, alpha: float = 0.45) -> None:
        """Args:
            alpha: 목표 miscoverage rate. coverage = 1 - alpha.
        """
        self.alpha = alpha
        self._Q: float | None = None
        self._fitted: bool = False

    def fit(
        self,
        y_calib: np.ndarray,
        q_pred_calib: np.ndarray,
    ) -> float:
        """Calib set에서 conformity score Q 산출.

        Args:
            y_calib: 실제 ln(낙찰가), shape (n,).
            q_pred_calib: quantile 예측, shape (n, 3) = [q25, q50, q75].

        Returns:
            Q: conformity score quantile.
        """
        q_low = q_pred_calib[:, 0]
        q_high = q_pred_calib[:, 2]

        # Conformity scores: max(q_low - y, y - q_high)
        scores = np.maximum(q_low - y_calib, y_calib - q_high)

        # (1-alpha)(1 + 1/n)-quantile
        n = len(scores)
        quantile_level = (1 - self.alpha) * (1 + 1 / n)
        quantile_level = min(quantile_level, 1.0)

        # method="higher"로 order statistic 기반 상위 양자 선택
        # → finite-sample coverage ≥ 1-alpha 보장 (Romano et al., 2019)
        self._Q = float(np.quantile(scores, quantile_level, method="higher"))
        self._fitted = True

        logger.info(
            "CQR fit: n=%d, alpha=%.2f, Q=%.4f",
            n, self.alpha, self._Q,
        )
        return self._Q

    def predict(self, q_pred: np.ndarray) -> np.ndarray:
        """CQR prediction interval 생성.

        C(X) = [q_low - Q, q50, q_high + Q]

        Args:
            q_pred: shape (n, 3) = [q25, q50, q75] (log scale).

        Returns:
            shape (n, 3): [calibrated_low, q50, calibrated_high].
        """
        if not self._fitted or self._Q is None:
            msg = "CQR not fitted. Call fit() first."
            raise RuntimeError(msg)

        out = q_pred.copy()
        out[:, 0] = q_pred[:, 0] - self._Q
        out[:, 2] = q_pred[:, 2] + self._Q

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
        """검증 세트에서 CQR coverage + slice별 검증."""
        calibrated = self.predict(q_pred_valid)
        covered = (y_valid >= calibrated[:, 0]) & (y_valid <= calibrated[:, 2])

        result: dict[str, float] = {
            "coverage_overall": float(np.mean(covered)),
            "n": float(len(y_valid)),
            "interval_width_median": float(
                np.median(calibrated[:, 2] - calibrated[:, 0])
            ),
        }

        if auction_types is not None:
            for atype in np.unique(auction_types):
                mask = auction_types == atype
                if mask.sum() > 0:
                    result[f"coverage_{atype}"] = float(np.mean(covered[mask]))

        return result

    def validate_temporal_coverage(
        self,
        y_windows: list[np.ndarray],
        q_windows: list[np.ndarray],
    ) -> dict[str, float]:
        """최근 3개 시간 윈도우에서 coverage 검증.

        Returns:
            dict with: window_N_coverage (N=0,1,2), all_pass (bool).
        """
        result: dict[str, float] = {}
        all_pass = True
        target_coverage = 1 - self.alpha

        for i, (y_w, q_w) in enumerate(zip(y_windows, q_windows, strict=False)):
            cal = self.predict(q_w)
            covered = (y_w >= cal[:, 0]) & (y_w <= cal[:, 2])
            cov = float(np.mean(covered))
            result[f"window_{i}_coverage"] = cov
            if cov < target_coverage - 0.05:  # 5%p 마진
                all_pass = False

        result["all_pass"] = float(all_pass)
        return result

    def save(self, path: str) -> None:
        """CQR 파라미터 저장."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(
                {"alpha": self.alpha, "Q": self._Q, "_fitted": self._fitted},
                f,
            )
        logger.info("CQR saved to %s", path)

    def load(self, path: str) -> None:
        """CQR 파라미터 로드."""
        with open(path, "rb") as f:
            state = pickle.load(f)
        self.alpha = state["alpha"]
        self._Q = state["Q"]
        self._fitted = state["_fitted"]
        logger.info("CQR loaded from %s", path)
