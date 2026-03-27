"""추론 latency 측정.

기획서 참조: 10장 전환 게이트 — 추론 latency < 100ms
"""
from __future__ import annotations

import time

import pandas as pd
from catboost import CatBoostRegressor

from visionai.price_engine.models.predictor import predict


def measure_latency(
    model: CatBoostRegressor,
    sample_row: pd.DataFrame,
    n_runs: int = 100,
) -> dict[str, float]:
    """단건 추론 latency를 측정한다.

    Args:
        model: CatBoost 모델.
        sample_row: 1행짜리 DataFrame.
        n_runs: 반복 횟수 (중앙값 산출).

    Returns:
        {"median_ms": float, "p95_ms": float, "max_ms": float, "pass": bool}
    """
    latencies: list[float] = []
    for _ in range(n_runs):
        start = time.perf_counter()
        _ = predict(model, sample_row, apply_low_price_cap=False)
        elapsed = (time.perf_counter() - start) * 1000
        latencies.append(elapsed)

    import numpy as np

    arr = np.array(latencies)
    median_ms = float(np.median(arr))
    p95_ms = float(np.percentile(arr, 95))
    max_ms = float(np.max(arr))

    return {
        "median_ms": round(median_ms, 2),
        "p95_ms": round(p95_ms, 2),
        "max_ms": round(max_ms, 2),
        "pass": p95_ms < 100.0,
    }
