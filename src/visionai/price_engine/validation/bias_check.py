"""재변환 편향 검증.

기획서 참조: 2.2 재변환 편향, 10장 Sprint 1
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def compute_bias_table(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> pd.DataFrame:
    """가격대별 median(P̂/P_actual)을 산출한다.

    기획서 판단 기준:
      0.95~1.05 → 보정 불필요
      0.85~0.95 → smearing correction 실험
      < 0.85    → smearing correction 필수
      > 1.05    → 과대추정 조사

    Returns:
        DataFrame with: price_tier, n, median_ratio, verdict.
    """
    ratio = y_pred / y_true

    tiers = pd.cut(
        y_true,
        bins=[0, 1_000_000, 5_000_000, 30_000_000, 100_000_000, np.inf],
        labels=["<100만", "100만~500만", "500만~3000만", "3000만~1억", "1억+"],
    )

    rows = []
    for tier_name in ["<100만", "100만~500만", "500만~3000만", "3000만~1억", "1억+"]:
        mask = tiers == tier_name
        if mask.sum() == 0:
            continue
        med = float(np.median(ratio[mask]))
        if med >= 1.05:
            verdict = "과대추정 조사"
        elif med >= 0.95:
            verdict = "정상"
        elif med >= 0.85:
            verdict = "smearing 실험"
        else:
            verdict = "smearing 필수"

        rows.append({
            "price_tier": tier_name,
            "n": int(mask.sum()),
            "median_ratio": round(med, 4),
            "verdict": verdict,
        })

    return pd.DataFrame(rows)
