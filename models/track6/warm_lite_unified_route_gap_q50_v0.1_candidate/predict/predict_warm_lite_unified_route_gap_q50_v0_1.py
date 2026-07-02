#!/usr/bin/env python3
"""Unified Warm-lite route_gap_q50 official 0.1v predictor.

This predictor is the default official 0.1v Warm route policy for trusted
same-artist price history count >= 1.  It reproduces the PP-ROUTE-CF9 rule:
keep the unified Warm-lite prediction by default, and switch to the stronger
CF7 residual correction when the full/lean q50 disagreement is at least the
validation q50 gap threshold.
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
    path = BUNDLE / "config" / "warm_lite_unified_route_gap_q50_params_v0_1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_models() -> dict[int, dict[str, Any]]:
    params = load_params()
    out: dict[int, dict[str, Any]] = {}
    for seed in params["seeds"]:
        seed_dir = BUNDLE / "models" / f"seed_{seed}"
        out[int(seed)] = {
            "full_q10": joblib.load(seed_dir / "lgbq_full_q10.joblib"),
            "full_q50": joblib.load(seed_dir / "lgbq_full_q50.joblib"),
            "full_q90": joblib.load(seed_dir / "lgbq_full_q90.joblib"),
            "lean_q50": joblib.load(seed_dir / "lgbq_lean_q50.joblib"),
            "lightgbm_residual": joblib.load(seed_dir / "lightgbm_huber_residual.joblib"),
        }
    return out


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
        for level, ladder in enumerate(params["fallback_ladder"], start=len(ARTIST_LADDER) + 1):
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
        out.loc[still, "grp_match_level"] = float(len(ARTIST_LADDER) + len(params["fallback_ladder"]) + 1)

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


def _predict_one_seed(
    seed_models: dict[str, Any],
    feature_frame: pd.DataFrame,
    params: dict[str, Any],
) -> pd.DataFrame:
    qpred = _predict_quantiles(seed_models, feature_frame, params)
    residual_x = _residual_feature_frame(feature_frame, qpred, params)
    residual = np.asarray(seed_models["lightgbm_residual"].predict(residual_x), dtype=float)
    current_correction = np.clip(
        float(params["current_residual_strength"]) * residual,
        -float(params["current_residual_cap_log"]),
        float(params["current_residual_cap_log"]),
    )
    out = qpred.copy()
    out["lgb_huber_residual_log"] = residual
    out["current_residual_correction_log"] = current_correction
    out["current_pred_log"] = out["lgbq_full_lean_avg"].to_numpy(dtype=float) + current_correction
    out["full_lean_gap_abs_log"] = np.abs(
        out["lgbq_full_q50"].to_numpy(dtype=float) - out["lgbq_lean_q50"].to_numpy(dtype=float)
    )
    return out


def predict(
    frame: pd.DataFrame,
    artist_history: pd.DataFrame,
    models: dict[int, dict[str, Any]] | None = None,
    params: dict[str, Any] | None = None,
) -> pd.DataFrame:
    params = params or load_params()
    models = models or load_models()
    missing = [col for col in REQUIRED if col not in frame.columns]
    if missing:
        raise ValueError(f"required columns missing: {missing}")
    history_n = len(artist_history)
    if history_n < 1:
        raise ValueError(f"Unified Warm-lite는 작가 이력 1건 이상 전용 (got {history_n})")

    fs = assign_stats(frame, artist_history, params)
    seed_parts = []
    for seed in params["seeds"]:
        seed_parts.append(_predict_one_seed(models[int(seed)], fs, params))

    mean = pd.concat(seed_parts, keys=params["seeds"], names=["seed", "row"])
    mean = mean.groupby(level="row").mean(numeric_only=True).sort_index()
    routed_correction = np.clip(
        float(params["routed_residual_strength"]) * mean["lgb_huber_residual_log"].to_numpy(dtype=float),
        -float(params["routed_residual_cap_log"]),
        float(params["routed_residual_cap_log"]),
    )
    cf7_pred_log = mean["lgbq_full_lean_avg"].to_numpy(dtype=float) + routed_correction
    route_to_cf7 = mean["full_lean_gap_abs_log"].to_numpy(dtype=float) >= float(params["route_gap_threshold"])
    pred_log = mean["current_pred_log"].to_numpy(dtype=float).copy()
    pred_log[route_to_cf7] = cf7_pred_log[route_to_cf7]

    out = frame.copy()
    out["warm_lite_unified_route_gap_q50_pred_log"] = pred_log
    out["warm_lite_unified_route_gap_q50_pred_price_krw"] = np.clip(np.exp(pred_log), 1_000.0, None)
    out["current_pred_log"] = mean["current_pred_log"].to_numpy(dtype=float)
    out["cf7_pred_log"] = cf7_pred_log
    out["route_to_cf7"] = route_to_cf7
    out["route_gap_threshold"] = float(params["route_gap_threshold"])
    out["full_lean_gap_abs_log"] = mean["full_lean_gap_abs_log"].to_numpy(dtype=float)
    out["lgbq_full_q10"] = mean["lgbq_full_q10"].to_numpy(dtype=float)
    out["lgbq_full_q50"] = mean["lgbq_full_q50"].to_numpy(dtype=float)
    out["lgbq_full_q90"] = mean["lgbq_full_q90"].to_numpy(dtype=float)
    out["lgbq_lean_q50"] = mean["lgbq_lean_q50"].to_numpy(dtype=float)
    out["lgbq_full_lean_avg"] = mean["lgbq_full_lean_avg"].to_numpy(dtype=float)
    out["lgbq_width"] = mean["lgbq_width"].to_numpy(dtype=float)
    out["lgb_huber_residual_log"] = mean["lgb_huber_residual_log"].to_numpy(dtype=float)
    out["artist_history_n"] = history_n
    out["confidence_grade"] = "warm_lite_unified_low" if history_n == 1 else "warm_lite_unified_standard"
    return out
