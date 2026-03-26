"""평가 지표 모듈.

MAPE, MdAPE, R², Within-K% 등을 계산한다.
기획서 참조: 6.1
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
