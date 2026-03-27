"""Prediction Interval Backtest.

Phase 1 고정 margin의 grade별 실제 coverage를 측정한다.
기획서 참조: 5.3, 9장 #4
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# Phase 1 고정 margin (기획서 5.3)
GRADE_MARGINS: dict[str, float] = {
    "A": 0.20,
    "B": 0.30,
    "C": 0.50,
    "D": 0.70,
}


def compute_interval_coverage(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    grades: pd.Series,
) -> pd.DataFrame:
    """grade별 고정 margin 구간의 실제 coverage를 계산한다.

    Returns:
        DataFrame: grade, margin, n, coverage_pct
    """
    rows = []
    for g, margin in GRADE_MARGINS.items():
        mask = grades.values == g
        if mask.sum() == 0:
            continue

        yt = y_true[mask]
        yp = y_pred[mask]

        lower = yp * (1 - margin)
        upper = yp * (1 + margin)
        inside = (yt >= lower) & (yt <= upper)
        coverage = float(np.mean(inside) * 100)

        rows.append({
            "grade": g,
            "margin": f"±{int(margin*100)}%",
            "n": int(mask.sum()),
            "coverage_pct": round(coverage, 1),
        })

    return pd.DataFrame(rows)
