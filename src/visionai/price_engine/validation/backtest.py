"""워크포워드 백테스트 러너.

여러 cutoff 시점에서 반복 평가하여 MAPE 안정성을 확인한다.
기획서 참조: 9장 #1
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor

from visionai.price_engine.models.predictor import predict
from visionai.price_engine.validation.metrics import EvalMetrics, compute_metrics

logger = logging.getLogger(__name__)


def run_walkforward_backtest(
    model: CatBoostRegressor,
    df: pd.DataFrame,
    cutoffs: list[int] | None = None,
    session_col: str = "회차",
    price_col: str = "낙찰가",
) -> pd.DataFrame:
    """여러 cutoff 시점에서 MAPE를 측정한다.

    Args:
        model: 학습된 CatBoost 모델.
        df: 전체 데이터 (피처 + 타겟).
        cutoffs: 테스트 시작 회차 리스트. None이면 기본 [350, 380, 410, 440].

    Returns:
        DataFrame: cutoff, mape, mdape, n
    """
    if cutoffs is None:
        cutoffs = [350, 380, 410, 440]

    rows = []
    for cutoff in cutoffs:
        test_mask = df[session_col] >= cutoff
        test = df[test_mask]

        if len(test) < 10:
            logger.warning("Cutoff %d: only %d rows, skipping", cutoff, len(test))
            continue

        y_pred = predict(model, test, apply_low_price_cap=False)
        y_true = test[price_col].astype(float).values
        m = compute_metrics(y_true, y_pred)

        rows.append({
            "cutoff": cutoff,
            "mape": m.mape,
            "mdape": m.mdape,
            "within_20pct": m.within_20pct,
            "n": m.n,
        })
        logger.info("Cutoff %d: MAPE=%.2f%% N=%d", cutoff, m.mape, m.n)

    result = pd.DataFrame(rows)

    if len(result) >= 2:
        mape_std = result["mape"].std()
        logger.info("MAPE std across cutoffs: %.2f%%p (stable if < 3%%p)", mape_std)

    return result
