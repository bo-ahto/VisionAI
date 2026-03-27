"""평가 지표 모듈.

MAPE, MdAPE, R², Within-K% 등을 계산한다.
Phase 3 추가: Pinball Loss, Interval Score, Coverage Rate, Range Width, Estimate MAPE/Bias.
기획서 참조: 6.1, Phase 3 기획서 5.1
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt


@dataclass
class EvalMetrics:
    """평가 결과."""

    mape: float
    mdape: float
    rmse: float
    mae: float
    r2: float
    within_20pct: float
    within_30pct: float
    n: int


def compute_metrics(
    y_true: npt.NDArray[np.floating],
    y_pred: npt.NDArray[np.floating],
) -> EvalMetrics:
    """원래 스케일(원 단위)의 실제값/예측값으로 평가 지표를 계산한다.

    Args:
        y_true: 실제 낙찰가 (원).
        y_pred: 예측 낙찰가 (원).

    Returns:
        EvalMetrics with MAPE, MdAPE, RMSE, MAE, R², Within-20/30%.
    """
    mask = y_true > 0
    yt = y_true[mask]
    yp = y_pred[mask]
    n = len(yt)

    if n == 0:
        return EvalMetrics(
            mape=float("nan"), mdape=float("nan"), rmse=float("nan"),
            mae=float("nan"), r2=float("nan"),
            within_20pct=float("nan"), within_30pct=float("nan"), n=0,
        )

    ape = np.abs(yt - yp) / yt

    mape = float(np.mean(ape) * 100)
    mdape = float(np.median(ape) * 100)
    rmse = float(np.sqrt(np.mean((yt - yp) ** 2)))
    mae = float(np.mean(np.abs(yt - yp)))

    ss_res = np.sum((yt - yp) ** 2)
    ss_tot = np.sum((yt - np.mean(yt)) ** 2)
    r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else float("nan")

    within_20 = float(np.mean(ape < 0.20) * 100)
    within_30 = float(np.mean(ape < 0.30) * 100)

    return EvalMetrics(
        mape=round(mape, 2),
        mdape=round(mdape, 2),
        rmse=round(rmse, 0),
        mae=round(mae, 0),
        r2=round(r2, 4),
        within_20pct=round(within_20, 1),
        within_30pct=round(within_30, 1),
        n=n,
    )


# ─── Phase 3: Quantile / Interval 지표 ───


def compute_pinball_loss(
    y_true: npt.NDArray[np.floating],
    q_pred: npt.NDArray[np.floating],
    tau: float,
) -> float:
    """Pinball (quantile) loss for a single quantile.

    rho_tau(u) = tau*|u| if u >= 0, (1-tau)*|u| if u < 0.
    y_true, q_pred are on log scale.

    Returns:
        Mean pinball loss (lower is better).
    """
    if len(y_true) == 0 or len(q_pred) == 0:
        return float("nan")
    residual = y_true - q_pred
    loss = np.where(residual >= 0, tau * residual, (tau - 1) * residual)
    return float(np.mean(loss))


def compute_pinball_loss_total(
    y_true: npt.NDArray[np.floating],
    q_preds: npt.NDArray[np.floating],
    taus: tuple[float, ...] = (0.25, 0.50, 0.75),
) -> float:
    """Sum of pinball losses across multiple quantiles.

    Args:
        y_true: shape (n,), log scale.
        q_preds: shape (n, len(taus)), log scale.
        taus: quantile levels.
    """
    total = 0.0
    for i, tau in enumerate(taus):
        total += compute_pinball_loss(y_true, q_preds[:, i], tau)
    return total


def compute_interval_score(
    y_true: npt.NDArray[np.floating],
    q_low: npt.NDArray[np.floating],
    q_high: npt.NDArray[np.floating],
    alpha: float = 0.5,
) -> float:
    """Interval Score (Gneiting & Raftery, 2007).

    IS = (q_high - q_low) + (2/alpha)(q_low - y)^+ + (2/alpha)(y - q_high)^+
    """
    if len(y_true) == 0 or len(q_low) == 0 or len(q_high) == 0:
        return float("nan")
    width = q_high - q_low
    undershoot = np.maximum(q_low - y_true, 0)
    overshoot = np.maximum(y_true - q_high, 0)
    score = width + (2.0 / alpha) * undershoot + (2.0 / alpha) * overshoot
    return float(np.mean(score))


def compute_coverage_rate(
    y_true: npt.NDArray[np.floating],
    q_low: npt.NDArray[np.floating],
    q_high: npt.NDArray[np.floating],
) -> float:
    """실제값이 [q_low, q_high] 구간 내에 있는 비율."""
    if len(y_true) == 0 or len(q_low) == 0 or len(q_high) == 0:
        return float("nan")
    covered = (y_true >= q_low) & (y_true <= q_high)
    return float(np.mean(covered))


def compute_range_width(
    q_low: npt.NDArray[np.floating],
    q_mid: npt.NDArray[np.floating],
    q_high: npt.NDArray[np.floating],
) -> float:
    """(q_high - q_low) / q_mid 의 중앙값. 원래 스케일 (원화).

    Returns:
        Median range width ratio.
    """
    mask = q_mid > 0
    ratios = (q_high[mask] - q_low[mask]) / q_mid[mask]
    return float(np.median(ratios)) if len(ratios) > 0 else float("nan")


def compute_estimate_mape(
    generated_mid: npt.NDArray[np.floating],
    actual_mid: npt.NDArray[np.floating],
) -> float:
    """생성 추정가 중앙 vs 실제 추정가 중앙 MAPE (%).

    Returns:
        MAPE in percent.
    """
    mask = actual_mid > 0
    ape = np.abs(generated_mid[mask] - actual_mid[mask]) / actual_mid[mask]
    return float(np.mean(ape) * 100) if len(ape) > 0 else float("nan")


def compute_estimate_bias(
    generated_mid: npt.NDArray[np.floating],
    actual_mid: npt.NDArray[np.floating],
) -> float:
    """median(생성 / 실제) — 1.0이면 편향 없음.

    Returns:
        Median ratio.
    """
    mask = actual_mid > 0
    ratios = generated_mid[mask] / actual_mid[mask]
    return float(np.median(ratios)) if len(ratios) > 0 else float("nan")
