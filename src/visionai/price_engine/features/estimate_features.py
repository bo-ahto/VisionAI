"""추정가 파생 피처 생성.

기획서 참조: 3.2.3 추정가 파생 피처
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def build_estimate_features(df: pd.DataFrame) -> pd.DataFrame:
    """추정가 최저/최고로부터 파생 피처를 생성한다.

    Args:
        df: '추정가(최저)', '추정가(최고)' 컬럼을 포함하는 DataFrame.

    Returns:
        estimate_mid, estimate_range, estimate_ratio, ln_estimate_mid 컬럼이
        추가된 DataFrame (원본 수정 없이 복사본 반환).
    """
    out = df.copy()
    low = out["추정가(최저)"].astype(float)
    high = out["추정가(최고)"].astype(float)

    out["estimate_mid"] = (low + high) / 2
    out["estimate_range"] = high - low

    # 0 나누기 방지: low=0이면 NaN
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = high / low
        ratio[low == 0] = np.nan
    out["estimate_ratio"] = ratio

    # log 변환: estimate_mid=0이면 NaN
    mid = out["estimate_mid"]
    ln_mid = np.where(mid > 0, np.log(mid), np.nan)
    out["ln_estimate_mid"] = ln_mid

    return out
