#!/usr/bin/env python3
"""Warm-lite v0.1 — 이력 1~4건 고신뢰 매칭 작가용 경량 Warm 예측기.

PP-WCUT1/2로 검증, PP-WMATCH1이 전제(매칭 정확도 ~85%+) 제공. 2026-06-12 채택.

- 적용 조건(라우팅): 작가매칭신뢰도 >= 0.90 AND 사용 가능 가격 이력 1~4건
- 구조: 작가 사다리(min 1) 통계는 호출자가 주는 작가 이력으로 실시간 계산,
  미매칭 시 동결된 비작가 사다리 테이블 fallback → 선형 Huber 6구성 앙상블
- k=1 차등 정책: confidence_grade = "warm_lite_low" (넓은 범위 표시 + 검수
  플래그 권장). k>=2 = "warm_lite_standard"
- 입력: frame(작품 피처) + artist_history(해당 작가의 알려진 작품들:
  ln_price_krw, log_area, medium_support_bucket, size_bucket, medium_category,
  support_category 포함)
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

BUNDLE = Path(__file__).resolve().parents[1]
GRP_COLS = ["grp_log_price_median", "grp_log_price_q25", "grp_log_price_q75",
            "grp_log_price_iqr", "grp_unit_area_median", "grp_unit_area_iqr",
            "grp_n_log", "grp_match_level"]
ARTIST_LADDER = [["medium_support_bucket", "size_bucket"], ["size_bucket"], []]  # artist 내 키
REQUIRED = ["width_cm", "height_cm", "depth_cm", "area_cm2", "log_area", "aspect_ratio",
            "has_depth", "is_3d_candidate", "medium_category", "support_category",
            "size_bucket", "medium_support_bucket"]


def load_params() -> dict:
    return json.loads((BUNDLE / "config" / "warm_lite_params_v0_1.json").read_text(encoding="utf-8"))


def load_models() -> list:
    p = load_params()
    return [joblib.load(BUNDLE / "models" / f"huber_c{i}.joblib") for i in range(p["n_huber"])]


def _stats_from(rows: pd.DataFrame, level: float) -> dict:
    lp = rows["ln_price_krw"].astype(float)
    unit = lp - rows["log_area"].astype(float).clip(lower=0)
    return {"grp_log_price_median": float(lp.median()),
            "grp_log_price_q25": float(lp.quantile(0.25)),
            "grp_log_price_q75": float(lp.quantile(0.75)),
            "grp_log_price_iqr": float(lp.quantile(0.75) - lp.quantile(0.25)),
            "grp_unit_area_median": float(unit.median()),
            "grp_unit_area_iqr": float(unit.quantile(0.75) - unit.quantile(0.25)),
            "grp_n_log": float(np.log1p(len(rows))), "grp_match_level": level}


def assign_stats(frame: pd.DataFrame, artist_history: pd.DataFrame, params: dict) -> pd.DataFrame:
    out = frame.copy()
    for c in GRP_COLS:
        out[c] = np.nan
    # 작가 사다리 (min 1): 이력 내 동일 버킷 → 동일 크기 → 작가 전체
    for i in out.index:
        hit = None
        for li, keys in enumerate(ARTIST_LADDER, start=1):
            sub = artist_history
            for kcol in keys:
                sub = sub[sub[kcol].astype(str) == str(out.at[i, kcol])]
            if len(sub) >= 1:
                hit = _stats_from(sub, float(li))
                break
        if hit:
            for c, v in hit.items():
                out.at[i, c] = v
    # 비작가 동결 사다리 fallback
    un = out["grp_match_level"].isna()
    if un.any():
        for li, lad in enumerate(params["ladder"], start=len(ARTIST_LADDER) + 1):
            still = out["grp_match_level"].isna()
            if not still.any():
                break
            kv = out.loc[still, lad["keys"]].astype(str).agg("|".join, axis=1)
            hitmask = kv.map(lambda k: k in lad["table"])
            idx = kv.index[hitmask]
            for c in GRP_COLS[:-1]:
                out.loc[idx, c] = [lad["table"][k].get(c) for k in kv[hitmask]]
            out.loc[idx, "grp_match_level"] = float(li)
        still = out["grp_match_level"].isna()
        for c, v in params["global_fallback"].items():
            out.loc[still, c] = v
        out.loc[still, "grp_match_level"] = float(len(ARTIST_LADDER) + len(params["ladder"]) + 1)
    out["grp_price_proxy"] = out["grp_unit_area_median"] + out["log_area"].clip(lower=0)
    return out


def predict(frame: pd.DataFrame, artist_history: pd.DataFrame,
            models: list | None = None, params: dict | None = None) -> pd.DataFrame:
    params = params or load_params()
    models = models or load_models()
    missing = [c for c in REQUIRED if c not in frame.columns]
    if missing:
        raise ValueError(f"required columns missing: {missing}")
    k = len(artist_history)
    if not 1 <= k <= 4:
        raise ValueError(f"Warm-lite는 작가 이력 1~4건 전용 (got {k}) — 5건 이상은 Warm, 0건은 Cold")

    fs = assign_stats(frame, artist_history, params)
    preds = np.mean([np.asarray(m.predict(fs[cols + params["huber_cat_cols"]]), dtype=float)
                     for m, cols in zip(models, params["huber_num_cols"])], axis=0)
    out = frame.copy()
    out["warm_lite_pred_log"] = preds
    out["warm_lite_pred_price_krw"] = np.clip(np.exp(preds), 1_000.0, None)
    out["artist_history_n"] = k
    out["confidence_grade"] = "warm_lite_low" if k == 1 else "warm_lite_standard"
    out["display_policy"] = ("wide_range_with_review_flag" if k == 1
                             else "point_estimate_with_standard_range")
    return out
