"""Calibration 검증 — grade별 coverage 테이블.

기획서 참조: 5.2 필수 검증 테이블
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def compute_calibration_table(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    grades: pd.Series,
) -> pd.DataFrame:
    """grade별 ±20%, ±30% coverage를 계산한다.

    Returns:
        DataFrame with columns: grade, n, within_20pct, within_30pct, mape, mdape.
    """
    ape = np.abs(y_true - y_pred) / y_true

    rows = []
    for g in ["A", "B", "C", "D"]:
        mask = grades.values == g
        if mask.sum() == 0:
            continue
        a = ape[mask]
        rows.append({
            "grade": g,
            "n": int(mask.sum()),
            "within_20pct": round(float(np.mean(a < 0.20) * 100), 1),
            "within_30pct": round(float(np.mean(a < 0.30) * 100), 1),
            "mape": round(float(np.mean(a) * 100), 2),
            "mdape": round(float(np.median(a) * 100), 2),
        })

    return pd.DataFrame(rows)
