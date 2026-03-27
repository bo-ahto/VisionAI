"""추정가 생성 엔진 통합 파이프라인.

Model-A(Quantile) + Model-B(Estimate) + Calibration + Rounding 통합.
4개 시나리오: A(독립 가치평가), B(추정가 검증), C(기존 엔진 연동), D(사전 가치평가).

기획서 3.5절, 개발기획서 Sprint 3 참조.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from visionai.price_engine.estimate_generator.cold_start import (
    assign_confidence_grade,
)
from visionai.price_engine.estimate_generator.estimate_calibrator import (
    EstimateCalibrator,
)
from visionai.price_engine.estimate_generator.estimate_model import (
    EstimateRegressorModel,
)
from visionai.price_engine.estimate_generator.market_rounder import round_to_market_unit
from visionai.price_engine.estimate_generator.quantile_calibrator import (
    QuantileCalibrator,
)
from visionai.price_engine.estimate_generator.quantile_model import (
    HedonicQuantileModel,
)
from visionai.price_engine.estimate_generator.selection_bias import (
    adjust_for_selection_bias,
)

logger = logging.getLogger(__name__)


class EstimateGenerator:
    """추정가 생성 엔진 통합 파이프라인."""

    def __init__(
        self,
        model_a: HedonicQuantileModel,
        model_b: EstimateRegressorModel,
        quantile_calibrator: QuantileCalibrator,
        estimate_calibrator: EstimateCalibrator,
        price_engine_v2: object | None = None,
    ) -> None:
        self.model_a = model_a
        self.model_b = model_b
        self.q_cal = quantile_calibrator
        self.e_cal = estimate_calibrator
        self.price_engine_v2 = price_engine_v2

    def generate(
        self,
        df: pd.DataFrame,
        artist_total_sold: int = 0,
        is_new_artist: bool = False,
        cold_start_tier: int = 0,
        artist_unsold_rate: float | None = None,
        group_unsold_rate: float | None = None,
        works_hist: pd.DataFrame | None = None,
        cutoff: int | None = None,
        medium_category: str | None = None,
        auction_type: str | None = None,
    ) -> dict:
        """전체 생성 파이프라인.

        Returns:
            dict with price_range, estimate, confidence_grade, metadata.
        """
        # === group_unsold_rate 자동 계산 (works_hist 제공 시) ===
        if works_hist is not None and cutoff is not None and group_unsold_rate is None:
            from visionai.price_engine.features.hedonic_stats import (
                compute_group_unsold_rate,
            )
            # medium_category/auction_type을 df에서 자동 추출 (미전달 시)
            if medium_category is None and "medium_category" in df.columns:
                medium_category = str(df["medium_category"].iloc[0])
            if auction_type is None and "타입" in df.columns:
                auction_type = str(df["타입"].iloc[0])

            if medium_category and auction_type:
                gur_df = compute_group_unsold_rate(
                    works_hist, cutoff, auction_type=auction_type
                )
                if not gur_df.empty:
                    key = (medium_category, auction_type)
                    if key in gur_df.index:
                        group_unsold_rate = float(
                            gur_df.loc[key, "group_unsold_rate"]
                        )

        # === Model-A: 낙찰가 구간 (연속값, 라운딩 없음) ===
        raw_q = self.model_a.predict_raw(df)
        calibrated_q = self.q_cal.transform(raw_q)
        price_low = np.exp(calibrated_q[:, 0])
        price_mid = np.exp(calibrated_q[:, 1])
        price_high = np.exp(calibrated_q[:, 2])

        # === Model-B: 추정가 재현 (라운딩 적용) ===
        raw_b = self.model_b.predict_raw(df)
        est_result = self.e_cal.transform(raw_b)
        est_low = np.array([round_to_market_unit(v) for v in est_result["est_low"]])
        est_mid = np.array([round_to_market_unit(v) for v in est_result["est_mid"]])
        est_high = np.array([round_to_market_unit(v) for v in est_result["est_high"]])

        # === 신뢰도 등급 ===
        grade = assign_confidence_grade(
            artist_total_sold=artist_total_sold,
            is_new_artist=is_new_artist,
            cold_start_tier=cold_start_tier,
            artist_unsold_rate=artist_unsold_rate,
            group_unsold_rate=group_unsold_rate,
        )

        # === Selection bias 보정 ===
        sb_applied = False
        expansion_factor = 1.0
        if len(price_low) == 1:
            adj_low, adj_mid, adj_high, adj_grade = adjust_for_selection_bias(
                float(price_low[0]), float(price_mid[0]), float(price_high[0]),
                artist_unsold_rate, group_unsold_rate, grade,
            )
            if adj_grade != grade:
                sb_applied = True
                expansion_factor = 1.3
                grade = adj_grade
            price_low = np.array([adj_low])
            price_mid = np.array([adj_mid])
            price_high = np.array([adj_high])

        return {
            "price_range": {
                "low": price_low,
                "mid": price_mid,
                "high": price_high,
            },
            "estimate": {
                "low": est_low,
                "mid": est_mid,
                "high": est_high,
            },
            "confidence_grade": grade,
            "cold_start_tier": cold_start_tier,
            "metadata": {
                "group_unsold_rate": group_unsold_rate,
                "artist_unsold_rate": artist_unsold_rate,
                "selection_bias_applied": sb_applied,
                "interval_expansion_factor": expansion_factor,
            },
        }

    def predict_with_v2(self, df: pd.DataFrame) -> dict:
        """시나리오 C: Model-B → 생성 추정가 → v2 엔진 → 낙찰가 예측.

        price_engine_v2가 설정되어 있어야 함.
        """
        if self.price_engine_v2 is None:
            msg = "price_engine_v2 not set. Pass it in __init__."
            raise RuntimeError(msg)

        # Model-B로 추정가 생성
        raw_b = self.model_b.predict_raw(df)
        est_result = self.e_cal.transform(raw_b)
        est_mid = np.array([round_to_market_unit(v) for v in est_result["est_mid"]])
        est_low = np.array([round_to_market_unit(v) for v in est_result["est_low"]])
        est_high = np.array([round_to_market_unit(v) for v in est_result["est_high"]])

        # v2 엔진으로 낙찰가 예측
        predicted_price = self.price_engine_v2.predict(
            df, est_mid=est_mid, est_low=est_low, est_high=est_high,
        )

        return {
            "predicted_price": predicted_price,
            "estimate_used": {
                "low": est_low,
                "mid": est_mid,
                "high": est_high,
            },
        }

    def validate_estimate(
        self,
        df: pd.DataFrame,
        kauction_low: int,
        kauction_high: int,
        auction_type: str = "프리미엄",
    ) -> dict:
        """시나리오 B: AI 추정가 vs K-Auction 추정가 비교.

        세그먼트별 차등 경고 기준:
        - 메이저 + 고가(>3000만): 괴리율 > 20%
        - 프리미엄: 괴리율 > 30%
        - 위클리 + 저가(<500만): 괴리율 > 40%
        """
        raw_b = self.model_b.predict_raw(df)
        est_result = self.e_cal.transform(raw_b)
        ai_mid = float(est_result["est_mid"][0]) if len(est_result["est_mid"]) > 0 else 0

        kauction_mid = (kauction_low + kauction_high) / 2
        if kauction_mid <= 0:
            return {"divergence_rate": float("nan"), "warning": False, "message": ""}

        divergence = abs(ai_mid - kauction_mid) / kauction_mid

        # 차등 경고 기준
        if auction_type == "메이저" and kauction_mid > 30_000_000:
            threshold = 0.20
        elif auction_type == "위클리" and kauction_mid < 5_000_000:
            threshold = 0.40
        else:
            threshold = 0.30

        warning = divergence > threshold

        return {
            "ai_estimate_mid": round_to_market_unit(ai_mid),
            "kauction_mid": int(kauction_mid),
            "divergence_rate": round(divergence * 100, 1),
            "threshold_pct": round(threshold * 100, 0),
            "warning": warning,
            "message": "추정가 재검토 권고" if warning else "",
        }
