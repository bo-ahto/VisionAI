"""드리프트 모니터링 — PSI, KS, rolling MAPE.

기획서 참조: 8.3절
입력 분포 변화(PSI/KS), 성능 변화(rolling MAPE), calibration 변화를 감지한다.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

logger = logging.getLogger(__name__)


@dataclass
class DriftResult:
    """드리프트 검사 결과."""

    feature: str
    psi: float
    ks_statistic: float
    ks_pvalue: float
    alert: bool


def compute_psi(
    reference: np.ndarray,
    current: np.ndarray,
    n_bins: int = 10,
) -> float:
    """Population Stability Index를 계산한다.

    PSI > 0.2 → 유의미한 분포 변화 (경고)
    PSI > 0.25 → 심각한 변화 (재학습 트리거)
    """
    ref = reference[~np.isnan(reference)]
    cur = current[~np.isnan(current)]

    if len(ref) < 10 or len(cur) < 10:
        return 0.0

    # 공통 빈 경계
    bins = np.percentile(ref, np.linspace(0, 100, n_bins + 1))
    bins[0] = -np.inf
    bins[-1] = np.inf

    ref_counts = np.histogram(ref, bins=bins)[0] / len(ref)
    cur_counts = np.histogram(cur, bins=bins)[0] / len(cur)

    # 0 방지
    ref_counts = np.maximum(ref_counts, 1e-6)
    cur_counts = np.maximum(cur_counts, 1e-6)

    psi = float(np.sum((cur_counts - ref_counts) * np.log(cur_counts / ref_counts)))
    return round(psi, 4)


def compute_ks(
    reference: np.ndarray,
    current: np.ndarray,
) -> tuple[float, float]:
    """Kolmogorov-Smirnov test를 수행한다.

    Returns:
        (ks_statistic, p_value)
    """
    ref = reference[~np.isnan(reference)]
    cur = current[~np.isnan(current)]

    if len(ref) < 10 or len(cur) < 10:
        return 0.0, 1.0

    stat, pvalue = scipy_stats.ks_2samp(ref, cur)
    return round(float(stat), 4), round(float(pvalue), 4)


def check_feature_drift(
    reference_df: pd.DataFrame,
    current_df: pd.DataFrame,
    features: list[str] | None = None,
    psi_threshold: float = 0.2,
) -> list[DriftResult]:
    """피처별 드리프트를 검사한다.

    Args:
        reference_df: 기준 데이터 (train 또는 이전 기간).
        current_df: 현재 데이터 (최신 경매).
        features: 검사할 피처 목록. None이면 수치형 전체.
        psi_threshold: PSI 경고 임계치.

    Returns:
        피처별 DriftResult 리스트.
    """
    if features is None:
        features = ["ln_estimate_mid", "surface_area", "artist_avg_price", "estimate_ratio"]

    results = []
    for feat in features:
        if feat not in reference_df.columns or feat not in current_df.columns:
            continue

        ref = reference_df[feat].astype(float).values
        cur = current_df[feat].astype(float).values

        psi = compute_psi(ref, cur)
        ks_stat, ks_pval = compute_ks(ref, cur)
        alert = psi > psi_threshold

        result = DriftResult(
            feature=feat,
            psi=psi,
            ks_statistic=ks_stat,
            ks_pvalue=ks_pval,
            alert=alert,
        )
        results.append(result)

        if alert:
            logger.warning("DRIFT ALERT [%s]: PSI=%.4f (>%.2f)", feat, psi, psi_threshold)
        else:
            logger.info("Drift OK [%s]: PSI=%.4f", feat, psi)

    return results


def compute_rolling_mape(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    timestamps: np.ndarray,
    window_size: int = 4,
) -> pd.DataFrame:
    """시간축 기반 rolling MAPE를 계산한다.

    Args:
        timestamps: 회차 또는 날짜 배열 (정렬 기준).
        window_size: 윈도우 크기 (회차 단위).

    Returns:
        DataFrame: period, mape, n
    """
    df = pd.DataFrame({
        "y_true": y_true,
        "y_pred": y_pred,
        "period": timestamps,
    })
    df = df.sort_values("period")

    unique_periods = sorted(df["period"].unique())
    rows = []

    for i in range(len(unique_periods) - window_size + 1):
        window_periods = unique_periods[i:i + window_size]
        mask = df["period"].isin(window_periods)
        subset = df[mask]

        yt = subset["y_true"].values
        yp = subset["y_pred"].values
        valid = yt > 0
        if valid.sum() == 0:
            continue

        ape = np.abs(yt[valid] - yp[valid]) / yt[valid]
        mape = float(np.mean(ape) * 100)

        rows.append({
            "period_start": window_periods[0],
            "period_end": window_periods[-1],
            "mape": round(mape, 2),
            "n": int(valid.sum()),
        })

    return pd.DataFrame(rows)
