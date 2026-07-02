#!/usr/bin/env python3
"""Cold k80 운영 모델 단일/배치 추론 predictor.

resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p05

runtime_store.joblib 하나(base q50 model + train 참조풀 + OOF 잔차 + params)만 읽는다.
DB/CSV/외부검색/artist_key 가격이력 미사용(strict cold).

피처 엔지니어링/유사도 계산은 track6 실험 함수를 재사용한다(parity 보장). 플랫폼 서빙 시에는
이 헬퍼들을 vendor한다. 입력은 track6 split과 같은 원천 컬럼을 가진 DataFrame이다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

BUNDLE = Path(__file__).resolve().parents[1]
STORE_PATH = BUNDLE / "artifacts" / "runtime_store.joblib"


def load_store() -> dict[str, Any]:
    return joblib.load(STORE_PATH)


def predict(input_frame: pd.DataFrame, store: dict[str, Any] | None = None) -> pd.DataFrame:
    """입력 작품 DataFrame -> Cold k80 routed 예측가(원/로그)."""
    import run_pp_csim24_cold_similarity_residual_correction as exp  # noqa: E402
    from run_pp_csim1_cold_similarity_reference import (  # noqa: E402
        ARTIST_SIM_FEATURES,
        ARTWORK_SIM_FEATURES,
    )

    store = store or load_store()
    p = store["params"]
    train_ref = store["train_ref"]
    base_features = store["base_features"]

    # 입력 피처 엔지니어링 (split 로더와 동일 경로) + base artwork-sim 참조 통계
    eng = exp.engineer_artist_meta(input_frame.copy())
    eng, _ = exp.add_generated_buckets(eng)
    _, _, target_sim, _ = exp.compute_reference_stats(
        train_ref, train_ref.iloc[:1].copy(), eng, ARTWORK_SIM_FEATURES,
        prefix=f"artwork_sim_k{p['base_top_k']}", top_k=p["base_top_k"],
    )
    base_pred = exp.predict_q_model(store["base_model"], train_ref, target_sim, base_features)
    stats = exp.residual_neighbor_stat(
        train_ref, target_sim, ARTIST_SIM_FEATURES, store["train_residual"],
        top_k=p["k"], prefix=f"artist_meta_k{p['k']}",
    )
    median = stats[f"artist_meta_k{p['k']}_resid_median"].to_numpy(dtype=float)
    correction = np.clip(p["strength"] * median, -p["cap"], p["cap"])
    routed = np.where(correction <= -p["route_neg_corr_ge"], correction, 0.0)
    pred_log = base_pred + routed

    out = input_frame.copy()
    out["pred_log"] = pred_log
    out["pred_price_krw"] = np.exp(pred_log)
    out["correction_log"] = routed
    out["route"] = "cold"
    return out
