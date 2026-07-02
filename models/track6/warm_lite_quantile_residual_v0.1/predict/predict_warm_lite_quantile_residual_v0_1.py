#!/usr/bin/env python3
"""Warm-lite Quantile residual v0.1 predictor.

This bundle is for the official v0.1 API Warm-lite route:
artist match >= 0.80 and same-artist price history count 1~4.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


warnings.filterwarnings("ignore", message="X does not have valid feature names")

BUNDLE = Path(__file__).resolve().parents[1]
GRP_COLS = [
    "grp_log_price_median",
    "grp_log_price_q25",
    "grp_log_price_q75",
    "grp_log_price_iqr",
    "grp_unit_area_median",
    "grp_unit_area_iqr",
    "grp_n_log",
    "grp_match_level",
]
ARTIST_LADDER = [["medium_support_bucket", "size_bucket"], ["size_bucket"], []]
REQUIRED = [
    "width_cm",
    "height_cm",
    "depth_cm",
    "area_cm2",
    "log_area",
    "aspect_ratio",
    "has_depth",
    "is_3d_candidate",
    "medium_category",
    "support_category",
    "size_bucket",
    "medium_support_bucket",
]


def load_params() -> dict[str, Any]:
    path = BUNDLE / "config" / "warm_lite_quantile_residual_params_v0_1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_models() -> dict[str, Any]:
    return {
        "full_q10": joblib.load(BUNDLE / "models" / "lgbq_full_q10.joblib"),
        "full_q50": joblib.load(BUNDLE / "models" / "lgbq_full_q50.joblib"),
        "full_q90": joblib.load(BUNDLE / "models" / "lgbq_full_q90.joblib"),
        "lean_q50": joblib.load(BUNDLE / "models" / "lgbq_lean_q50.joblib"),
        "lightgbm_residual": joblib.load(BUNDLE / "models" / "lightgbm_huber_residual.joblib"),
    }


def _stats_from(rows: pd.DataFrame, level: float) -> dict[str, float]:
    lp = rows["ln_price_krw"].astype(float)
    unit = lp - rows["log_area"].astype(float).clip(lower=0)
    return {
        "grp_log_price_median": float(lp.median()),
        "grp_log_price_q25": float(lp.quantile(0.25)),
        "grp_log_price_q75": float(lp.quantile(0.75)),
        "grp_log_price_iqr": float(lp.quantile(0.75) - lp.quantile(0.25)),
        "grp_unit_area_median": float(unit.median()),
        "grp_unit_area_iqr": float(unit.quantile(0.75) - unit.quantile(0.25)),
        "grp_n_log": float(np.log1p(len(rows))),
        "grp_match_level": level,
    }


def assign_stats(frame: pd.DataFrame, artist_history: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
    out = frame.copy()
    for col in GRP_COLS:
        out[col] = np.nan

    for idx in out.index:
        hit = None
        for level, keys in enumerate(ARTIST_LADDER, start=1):
            sub = artist_history
            for key in keys:
                sub = sub[sub[key].astype(str) == str(out.at[idx, key])]
            if len(sub) >= 1:
                hit = _stats_from(sub, float(level))
                break
        if hit:
            for col, value in hit.items():
                out.at[idx, col] = value

    unresolved = out["grp_match_level"].isna()
    if unresolved.any():
        for level, ladder in enumerate(params["ladder"], start=len(ARTIST_LADDER) + 1):
            still = out["grp_match_level"].isna()
            if not still.any():
                break
            keys = ladder["keys"]
            kv = out.loc[still, keys].astype(str).agg("|".join, axis=1)
            hitmask = kv.map(lambda value: value in ladder["table"])
            idx = kv.index[hitmask]
            for col in GRP_COLS[:-1]:
                out.loc[idx, col] = [ladder["table"][key].get(col) for key in kv[hitmask]]
            out.loc[idx, "grp_match_level"] = float(level)

        still = out["grp_match_level"].isna()
        for col, value in params["global_fallback"].items():
            out.loc[still, col] = value
        out.loc[still, "grp_match_level"] = float(len(ARTIST_LADDER) + len(params["ladder"]) + 1)

    out["grp_price_proxy"] = out["grp_unit_area_median"] + out["log_area"].clip(lower=0)
    return out


def _predict_quantiles(models: dict[str, Any], frame: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
    out = pd.DataFrame(index=frame.index)
    full_cols = params["full_num_cols"] + params["cat_cols"]
    lean_cols = params["lean_num_cols"] + params["cat_cols"]
    out["lgbq_full_q10"] = np.asarray(models["full_q10"].predict(frame[full_cols]), dtype=float)
    out["lgbq_full_q50"] = np.asarray(models["full_q50"].predict(frame[full_cols]), dtype=float)
    out["lgbq_full_q90"] = np.asarray(models["full_q90"].predict(frame[full_cols]), dtype=float)
    out["lgbq_lean_q50"] = np.asarray(models["lean_q50"].predict(frame[lean_cols]), dtype=float)
    out["lgbq_full_lean_avg"] = 0.50 * out["lgbq_full_q50"] + 0.50 * out["lgbq_lean_q50"]
    out["lgbq_width"] = np.maximum(out["lgbq_full_q90"] - out["lgbq_full_q10"], 0.0)
    return out


def _residual_feature_frame(frame: pd.DataFrame, qpred: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
    out = frame.copy()
    for col in params["q_cols"]:
        out[col] = qpred[col].to_numpy(dtype=float)
    for col in params["residual_cat_cols"]:
        out[col] = out[col].astype(str).fillna("__MISSING__")
    return out[params["residual_num_cols"] + params["residual_cat_cols"]]


def predict(
    frame: pd.DataFrame,
    artist_history: pd.DataFrame,
    models: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> pd.DataFrame:
    params = params or load_params()
    models = models or load_models()
    missing = [col for col in REQUIRED if col not in frame.columns]
    if missing:
        raise ValueError(f"required columns missing: {missing}")
    history_n = len(artist_history)
    if not 1 <= history_n <= 4:
        raise ValueError(f"Warm-lite는 작가 이력 1~4건 전용 (got {history_n})")

    fs = assign_stats(frame, artist_history, params)
    qpred = _predict_quantiles(models, fs, params)
    residual_x = _residual_feature_frame(fs, qpred, params)
    residual = np.asarray(models["lightgbm_residual"].predict(residual_x), dtype=float)
    raw_correction = float(params["residual_strength"]) * residual
    applied_correction = np.clip(
        raw_correction,
        -float(params["residual_cap_log"]),
        float(params["residual_cap_log"]),
    )
    pred_log = qpred["lgbq_full_lean_avg"].to_numpy(dtype=float) + applied_correction

    out = frame.copy()
    out["warm_lite_pred_log"] = pred_log
    out["warm_lite_pred_price_krw"] = np.clip(np.exp(pred_log), 1_000.0, None)
    out["lgbq_full_q10"] = qpred["lgbq_full_q10"].to_numpy(dtype=float)
    out["lgbq_full_q50"] = qpred["lgbq_full_q50"].to_numpy(dtype=float)
    out["lgbq_full_q90"] = qpred["lgbq_full_q90"].to_numpy(dtype=float)
    out["lgbq_lean_q50"] = qpred["lgbq_lean_q50"].to_numpy(dtype=float)
    out["lgbq_full_lean_avg"] = qpred["lgbq_full_lean_avg"].to_numpy(dtype=float)
    out["lgbq_width"] = qpred["lgbq_width"].to_numpy(dtype=float)
    out["lgb_huber_residual"] = residual
    out["raw_residual_correction_log"] = raw_correction
    out["applied_residual_correction_log"] = applied_correction
    out["artist_history_n"] = history_n
    out["confidence_grade"] = "warm_lite_low" if history_n == 1 else "warm_lite_standard"
    out["display_policy"] = (
        "wide_range_with_review_flag" if history_n == 1 else "point_estimate_with_standard_range"
    )
    return out
