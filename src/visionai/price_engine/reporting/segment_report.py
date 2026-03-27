"""세그먼트별 MAPE 리포트 생성.

기획서 참조: 6.2
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from visionai.price_engine.validation.metrics import EvalMetrics, compute_metrics


def generate_segment_report(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    df: pd.DataFrame,
    grades: pd.Series | None = None,
) -> str:
    """타입별 + 가격대별 + grade별 MAPE 리포트를 생성한다.

    Returns:
        리포트 텍스트.
    """
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("세그먼트별 MAPE 리포트")
    lines.append("=" * 60)

    # 전체
    overall = compute_metrics(y_true, y_pred)
    lines.append(f"\n전체: MAPE={overall.mape}%  MdAPE={overall.mdape}%  ±20%={overall.within_20pct}%  N={overall.n}")

    # 타입별
    lines.append("\n--- 타입별 ---")
    for atype in ["메이저", "프리미엄", "위클리"]:
        mask = df["타입"].values == atype
        if mask.sum() == 0:
            continue
        m = compute_metrics(y_true[mask], y_pred[mask])
        lines.append(f"  {atype:6s}: MAPE={m.mape:6.2f}%  ±20%={m.within_20pct}%  N={m.n}")

    # 가격대별
    lines.append("\n--- 가격대별 ---")
    tiers = pd.cut(
        y_true,
        bins=[0, 1_000_000, 5_000_000, 30_000_000, 100_000_000, np.inf],
        labels=["<100만", "100만~500만", "500만~3000만", "3000만~1억", "1억+"],
    )
    for tier in ["<100만", "100만~500만", "500만~3000만", "3000만~1억", "1억+"]:
        mask = tiers == tier
        if mask.sum() == 0:
            continue
        m = compute_metrics(y_true[mask], y_pred[mask])
        lines.append(f"  {tier:12s}: MAPE={m.mape:6.2f}%  ±20%={m.within_20pct}%  N={m.n}")

    # grade별
    if grades is not None:
        lines.append("\n--- 신뢰도 등급별 ---")
        for g in ["A", "B", "C", "D"]:
            mask = grades.values == g
            if mask.sum() == 0:
                continue
            m = compute_metrics(y_true[mask], y_pred[mask])
            lines.append(f"  {g}등급: MAPE={m.mape:6.2f}%  ±20%={m.within_20pct}%  N={m.n}")

    return "\n".join(lines)
