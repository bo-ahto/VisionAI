"""D등급 / Cold Start slice 리포트.

기획서 참조: 5.2 D등급 필수 검증 4항목
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from visionai.price_engine.validation.metrics import compute_metrics


def generate_cold_start_report(
    df: pd.DataFrame,
    y_pred: np.ndarray,
    grades: pd.Series,
) -> str:
    """D등급 slice 분석 리포트를 생성한다.

    Returns:
        리포트 텍스트.
    """
    y_true = df["낙찰가"].astype(float).values
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("D등급 / Cold Start Slice 리포트")
    lines.append("=" * 60)

    # 1. D등급 전체
    d_mask = grades.values == "D"
    if d_mask.sum() > 0:
        m = compute_metrics(y_true[d_mask], y_pred[d_mask])
        lines.append(f"\n1. D등급 전체: N={m.n}")
        lines.append(f"   MAPE={m.mape}%  MdAPE={m.mdape}%  ±20%={m.within_20pct}%")
    else:
        lines.append("\n1. D등급 없음")

    # 2. D등급 내 세부 분류
    lines.append("\n2. D등급 세부 분류:")
    for subgroup, label in [
        ("__UNKNOWN__", "작자미상"),
        ("__NEW_ARTIST__", "신규 작가"),
    ]:
        mask = d_mask & (df["artist_clean"].values == subgroup)
        if mask.sum() > 0:
            m = compute_metrics(y_true[mask], y_pred[mask])
            lines.append(f"   {label} ({subgroup}): N={m.n}  MAPE={m.mape}%  ±20%={m.within_20pct}%")

    # 기타 D등급 (이름이 있지만 sold=0)
    other_d = d_mask & ~df["artist_clean"].isin(["__UNKNOWN__", "__NEW_ARTIST__"])
    if other_d.sum() > 0:
        m = compute_metrics(y_true[other_d.values], y_pred[other_d.values])
        lines.append(f"   기타 D등급: N={m.n}  MAPE={m.mape}%  ±20%={m.within_20pct}%")

    # 3. C등급 희소 작가 (1~5건)
    lines.append("\n3. C등급 희소 작가 (sold 1~5):")
    c_mask = grades.values == "C"
    if c_mask.sum() > 0:
        m = compute_metrics(y_true[c_mask], y_pred[c_mask])
        lines.append(f"   N={m.n}  MAPE={m.mape}%  MdAPE={m.mdape}%  ±20%={m.within_20pct}%")

    # 4. UX 결정 권고
    lines.append("\n4. UX 결정 권고:")
    if d_mask.sum() > 0:
        d_metrics = compute_metrics(y_true[d_mask], y_pred[d_mask])
        if d_metrics.mdape > 100:
            lines.append("   → MdAPE > 100%: Option B 권장 (예측 불가 표시)")
        elif d_metrics.within_20pct < 5:
            lines.append("   → within-20% < 5%: Option B 권장 (예측 불가 표시)")
        else:
            lines.append("   → Option A 가능 (넓은 범위 + 참고용)")

    return "\n".join(lines)
