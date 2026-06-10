#!/usr/bin/env python3
"""Cold prediction v0.5 (operational, search-free) — 이종 blend 예측기.

PP-CBOOST1~3에서 검증된 이종 계열 blend를 동결: LGB Quantile 5-seed 평균(B)
0.7 + 선형 Huber·비작가 그룹통계 6구성 앙상블(C) 0.3. raw-input 실행 가능.

목적별 후보(p95 방어 우선): 동결 v0.2 defense 대비 test MdAPE -0.003,
MAPE 동등(+0.002), p95 -11.5%(4.122→3.649). MdAPE 반복 비악화 확률은
0.12~0.28로 낮아 all-metric 후보가 아님(PP-CBOOST3) — 채택은 2026-06-10
사용자 결정(큰 오차 회피 우선).
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

BUNDLE = Path(__file__).resolve().parents[1]
FEATURES = ["width_cm", "height_cm", "depth_cm", "area_cm2", "log_area", "aspect_ratio",
            "has_depth", "is_3d_candidate", "medium_category", "support_category",
            "size_bucket", "support_size_bucket"]
REQUIRED = FEATURES + ["medium_support_bucket"]
QUANTILES = ["q10", "q40", "q50", "q90"]
GRP_COLS = ["grp_log_price_median", "grp_log_price_q25", "grp_log_price_q75",
            "grp_log_price_iqr", "grp_unit_area_median", "grp_unit_area_iqr",
            "grp_n_log", "grp_match_level"]


def load_params() -> dict:
    return json.loads((BUNDLE / "config" / "blend_params_v0_5.json").read_text(encoding="utf-8"))


def load_models() -> dict:
    p = load_params()
    return {"lgb": {q: [joblib.load(BUNDLE / "models" / f"lgbq_{q}_seed{i}.joblib")
                        for i in range(p["n_seeds"])] for q in QUANTILES},
            "huber": [joblib.load(BUNDLE / "models" / f"huber_c{i}.joblib")
                      for i in range(p["n_huber"])]}


def assign_group_stats(frame: pd.DataFrame, params: dict) -> pd.DataFrame:
    out = frame.copy()
    for c in GRP_COLS:
        out[c] = np.nan
    un = pd.Series(True, index=out.index)
    for level, lad in enumerate(params["ladder"], start=1):
        if not un.any():
            break
        table = lad["table"]
        keys = lad["keys"]
        kv = out.loc[un, keys].astype(str).agg("|".join, axis=1)
        hit = kv.map(lambda k: k in table)
        idx = kv.index[hit]
        if len(idx):
            vals = pd.DataFrame([table[k] for k in kv[hit]], index=idx)
            for c in vals.columns:
                out.loc[idx, c] = vals[c].to_numpy()
            out.loc[idx, "grp_match_level"] = float(level)
            un.loc[idx] = False
    if un.any():
        for c, v in params["global_fallback"].items():
            out.loc[un, c] = v
        out.loc[un, "grp_match_level"] = float(len(params["ladder"]) + 1)
    out["grp_price_proxy"] = out["grp_unit_area_median"] + out["log_area"].clip(lower=0)
    return out


def predict(frame: pd.DataFrame, models: dict | None = None, params: dict | None = None) -> pd.DataFrame:
    params = params or load_params()
    models = models or load_models()
    missing = [c for c in REQUIRED if c not in frame.columns]
    if missing:
        raise ValueError(f"required columns missing: {missing}")

    q = {k: np.mean([np.asarray(m.predict(frame[FEATURES]), dtype=float)
                     for m in models["lgb"][k]], axis=0) for k in QUANTILES}
    fs = assign_group_stats(frame, params)
    c_cols = params["huber_num_cols"]
    c_pred = np.mean([np.asarray(h.predict(fs[cols + params["huber_cat_cols"]]), dtype=float)
                      for h, cols in zip(models["huber"], c_cols)], axis=0)

    w = float(params["blend_w"])
    rep = q["q50"] + w * (c_pred - q["q50"])
    g = params["guard"]
    width = q["q90"] - q["q10"]
    mask = (width >= float(g["width_q67"])) & ((rep - q["q40"]) >= float(g["gap_q50"])) & (q["q40"] < rep)
    defense = rep.copy()
    defense[mask] = 0.5 * rep[mask] + 0.5 * q["q40"][mask]

    out = frame.copy()
    for k in QUANTILES:
        out[f"{k}_pred_log"] = q[k]
    out["c_linear_pred_log"] = c_pred
    out["qwidth_log"] = width
    out["representative_pred_log"] = rep
    out["defense_pred_log"] = defense
    out["defense_pred_price_krw"] = np.clip(np.exp(defense), 1_000.0, None)
    out["range_low_price_krw"] = np.clip(np.exp(q["q10"]), 1_000.0, None)
    out["range_high_price_krw"] = np.clip(np.exp(q["q90"]), 1_000.0, None)
    return out
