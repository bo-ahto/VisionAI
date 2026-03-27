"""Model-B 세그먼트별 Duan smearing + 추정가 범위 ratio 보정.

Calib set에서 파라미터 산출. Adaptive quantile bin (5-quantile).
기획서 3.3절 참조.
"""
from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger(__name__)

_N_BINS = 5
_MIN_BIN_SIZE = 30


class EstimateCalibrator:
    """세그먼트별 Duan smearing + 추정가 범위 ratio 보정.

    Adaptive quantile bin: S1(<Q20)~S5(>=Q80).
    각 bin에서:
    - smearing_factor = mean(exp(residual))
    - ratio_low = median(est_low_actual / est_mid_actual)
    - ratio_high = median(est_high_actual / est_mid_actual)
    """

    def __init__(self) -> None:
        self.boundaries: np.ndarray | None = None
        self.smearing_factors: dict[int, float] = {}
        self.ratios_low: dict[int, float] = {}
        self.ratios_high: dict[int, float] = {}
        self._fitted: bool = False

    def fit(
        self,
        y_pred_calib: np.ndarray,
        y_actual_calib: np.ndarray,
        est_low_actual: np.ndarray,
        est_mid_actual: np.ndarray,
        est_high_actual: np.ndarray,
    ) -> dict[str, object]:
        """Calib set에서 세그먼트별 파라미터 산출.

        Args:
            y_pred_calib: Model-B raw 예측 ln(est_mid), shape (n,).
            y_actual_calib: 실제 ln(추정가 중앙), shape (n,).
            est_low_actual: 실제 추정가(최저), shape (n,).
            est_mid_actual: 실제 추정가(중앙), shape (n,).
            est_high_actual: 실제 추정가(최고), shape (n,).

        Returns:
            dict with boundaries, smearing_factors, ratios.
        """
        n = len(y_pred_calib)
        if n == 0:
            logger.warning("Empty calib set. Calibrator not fitted.")
            self._fitted = False
            self.boundaries = None
            self.smearing_factors = {}
            self.ratios_low = {}
            self.ratios_high = {}
            return {}

        # Adaptive quantile bin 경계: 실제 추정가 분포 기준 (기획서 3.3절)
        # y_pred가 아닌 y_actual(실제 추정가)의 분위수로 경계 설정
        quantiles = np.linspace(1 / _N_BINS, 1 - 1 / _N_BINS, _N_BINS - 1)
        self.boundaries = np.quantile(y_actual_calib, quantiles)
        # 예측값을 실제 추정가 기준 경계에 매핑
        segments = np.digitize(y_pred_calib, self.boundaries)

        residuals = y_actual_calib - y_pred_calib

        for seg in range(_N_BINS):
            mask = segments == seg
            seg_count = int(mask.sum())

            if seg_count < _MIN_BIN_SIZE:
                # 반복 병합: 인접 bin을 추가하여 min_size 도달까지
                expand = 1
                while seg_count < _MIN_BIN_SIZE and expand < _N_BINS:
                    if seg - expand >= 0:
                        mask = mask | (segments == seg - expand)
                    if seg + expand < _N_BINS:
                        mask = mask | (segments == seg + expand)
                    seg_count = int(mask.sum())
                    expand += 1

            if seg_count == 0:
                self.smearing_factors[seg] = 1.0
                self.ratios_low[seg] = 0.8
                self.ratios_high[seg] = 1.2
                continue

            # Smearing factor: E[exp(e)]
            seg_resid = residuals[mask]
            self.smearing_factors[seg] = float(np.mean(np.exp(seg_resid)))

            # Ratio: median(est_low/est_mid), median(est_high/est_mid)
            seg_mid = est_mid_actual[mask]
            valid_mid = seg_mid > 0

            if valid_mid.sum() > 0:
                self.ratios_low[seg] = float(
                    np.median(est_low_actual[mask][valid_mid] / seg_mid[valid_mid])
                )
                self.ratios_high[seg] = float(
                    np.median(est_high_actual[mask][valid_mid] / seg_mid[valid_mid])
                )
            else:
                self.ratios_low[seg] = 0.8
                self.ratios_high[seg] = 1.2

        self._fitted = True

        logger.info(
            "EstimateCalibrator fit: %d segments, smearing=%s",
            _N_BINS,
            {k: round(v, 4) for k, v in self.smearing_factors.items()},
        )

        return {
            "boundaries": self.boundaries.tolist(),
            "smearing_factors": dict(self.smearing_factors),
            "ratios_low": dict(self.ratios_low),
            "ratios_high": dict(self.ratios_high),
        }

    def transform(self, y_pred_raw: np.ndarray) -> dict[str, np.ndarray]:
        """Raw 예측에 세그먼트별 smearing + ratio 적용.

        Args:
            y_pred_raw: Model-B raw 예측 ln(est_mid), shape (n,).

        Returns:
            dict with 'est_low', 'est_mid', 'est_high' (원화, 라운딩 전).
        """
        if not self._fitted:
            msg = "Calibrator not fitted. Call fit() first."
            raise RuntimeError(msg)

        if self.boundaries is not None:
            segments = np.digitize(y_pred_raw, self.boundaries)
        else:
            segments = np.zeros(len(y_pred_raw), dtype=int)

        est_mid = np.zeros(len(y_pred_raw))
        est_low = np.zeros(len(y_pred_raw))
        est_high = np.zeros(len(y_pred_raw))

        for seg in range(_N_BINS):
            mask = segments == seg
            if not mask.any():
                continue
            sf = self.smearing_factors.get(seg, 1.0)
            rl = self.ratios_low.get(seg, 0.8)
            rh = self.ratios_high.get(seg, 1.2)

            est_mid[mask] = np.exp(y_pred_raw[mask]) * sf
            est_low[mask] = est_mid[mask] * rl
            est_high[mask] = est_mid[mask] * rh

        return {"est_low": est_low, "est_mid": est_mid, "est_high": est_high}

    def validate_stability(
        self,
        y_pred_calib: np.ndarray,
        y_actual_calib: np.ndarray,
        n_bootstrap: int = 100,
    ) -> dict[int, tuple[float, float]]:
        """세그먼트별 smearing factor의 bootstrap 95% CI."""
        if self.boundaries is None:
            return {}

        segments = np.digitize(y_pred_calib, self.boundaries)
        residuals = y_actual_calib - y_pred_calib
        result: dict[int, tuple[float, float]] = {}

        rng = np.random.default_rng(42)
        for seg in range(_N_BINS):
            mask = segments == seg
            seg_resid = residuals[mask]
            if len(seg_resid) < 5:
                result[seg] = (float("nan"), float("nan"))
                continue
            bootstrap_means = []
            for _ in range(n_bootstrap):
                sample = rng.choice(seg_resid, size=len(seg_resid), replace=True)
                bootstrap_means.append(float(np.mean(np.exp(sample))))
            ci_low = float(np.percentile(bootstrap_means, 2.5))
            ci_high = float(np.percentile(bootstrap_means, 97.5))
            result[seg] = (ci_low, ci_high)

        return result
