#!/usr/bin/env python3
"""No-DB Warm-lite unified current predictor.

This runtime does not read SQLite and does not read fixed replay feature store.
It reads only files inside this bundle:

- config/warm_lite_unified_route_gap_q50_params_v0_1.json
- models/seed_*/LightGBM joblib files
- artifacts/artist_registry.csv
- artifacts/artist_aliases.csv
- artifacts/artist_train_history.csv

The model formula is the official 0.1v current candidate:

    seed_mean(qavg + clip(0.50 * LightGBMHuberResidual, -0.10, +0.10))
"""

from __future__ import annotations

import json
import math
import re
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


warnings.filterwarnings("ignore", message="X does not have valid feature names")

BUNDLE = Path(__file__).resolve().parents[1]


def find_repo_root(start: Path) -> Path:
    for current in [start, *start.parents]:
        if (current / "src" / "visionai").exists() and (current / "scripts" / "track6").exists():
            return current
    raise RuntimeError(f"VisionAI repo root not found from {start}")


REPO = find_repo_root(BUNDLE)
TRACK6_SCRIPT_DIR = REPO / "scripts" / "track6"
if str(TRACK6_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(TRACK6_SCRIPT_DIR))

import extract_price_prediction_v0_1_features as feature_ops  # noqa: E402

FEATURE_GENERATION = feature_ops.load_artifact_feature_generation(REPO / "models" / "track6" / "price_prediction_v0.1")

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
REQUIRED_INPUT = [
    "width_cm",
    "height_cm",
    "depth_cm",
    "medium_category",
    "support_category",
]
REQUIRED_MODEL = [
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


@dataclass(frozen=True)
class ArtistResolution:
    artist_key: str | None
    match_score: float
    match_basis: str
    homonym_risk: float
    price_history_count: int
    review_required: bool


def normalize_name(value: object) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[()\\[\\]{}.,'\"`~!@#$%^&*_+=:;|/?<>-]", "", text)
    return text


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


def load_artifacts() -> dict[str, pd.DataFrame]:
    registry = pd.read_csv(BUNDLE / "artifacts" / "artist_registry.csv", low_memory=False)
    aliases = pd.read_csv(BUNDLE / "artifacts" / "artist_aliases.csv", low_memory=False)
    history = pd.read_csv(BUNDLE / "artifacts" / "artist_train_history.csv", low_memory=False)

    for frame in [registry, aliases, history]:
        if "artist_key" in frame.columns:
            frame["artist_key"] = frame["artist_key"].astype(str)
    aliases["alias_normalized"] = aliases["alias_normalized"].fillna("").astype(str)
    registry["name_ko_norm"] = registry["name_ko"].map(normalize_name)
    registry["name_en_norm"] = registry["name_en"].map(normalize_name)
    history["ln_price_krw"] = pd.to_numeric(history["log_price_krw"], errors="coerce")
    missing_log = history["ln_price_krw"].isna()
    if missing_log.any():
        history.loc[missing_log, "ln_price_krw"] = np.log(
            pd.to_numeric(history.loc[missing_log, "price_krw"], errors="coerce")
        )
    history["depth_cm"] = pd.to_numeric(history["depth_cm"], errors="coerce").fillna(0.0)
    history = add_runtime_features(history)
    return {"registry": registry, "aliases": aliases, "history": history}


def add_runtime_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["width_cm"] = pd.to_numeric(out["width_cm"], errors="coerce")
    out["height_cm"] = pd.to_numeric(out["height_cm"], errors="coerce")
    out["depth_cm"] = pd.to_numeric(out.get("depth_cm", 0.0), errors="coerce").fillna(0.0)
    out["area_cm2"] = pd.to_numeric(out.get("area_cm2"), errors="coerce")
    missing_area = out["area_cm2"].isna() | (out["area_cm2"] <= 0)
    out.loc[missing_area, "area_cm2"] = out.loc[missing_area, "width_cm"] * out.loc[missing_area, "height_cm"]
    out["log_area"] = np.log(out["area_cm2"].clip(lower=1.0))
    min_side = np.minimum(out["width_cm"], out["height_cm"])
    max_side = np.maximum(out["width_cm"], out["height_cm"])
    out["aspect_ratio"] = np.where(min_side > 0, max_side / min_side, np.nan)
    out["has_depth"] = out["depth_cm"] > 0
    if "is_3d_candidate" not in out.columns:
        out["is_3d_candidate"] = out["has_depth"]
    out["medium_category"] = out["medium_category"].fillna("unknown").astype(str)
    out["support_category"] = out["support_category"].fillna("unknown").astype(str)
    out["medium_support_bucket"] = out["medium_category"] + "__" + out["support_category"]
    return feature_ops.add_bucket_features(out, FEATURE_GENERATION, "cold")


def build_feature_frame(input_frame: pd.DataFrame) -> pd.DataFrame:
    missing = [col for col in REQUIRED_INPUT if col not in input_frame.columns]
    if missing:
        raise ValueError(f"required input columns missing: {missing}")
    return add_runtime_features(input_frame)[REQUIRED_MODEL].copy()


def resolve_artist(
    artist_name: str | None = None,
    artist_key: str | None = None,
    artifacts: dict[str, pd.DataFrame] | None = None,
) -> ArtistResolution:
    artifacts = artifacts or load_artifacts()
    registry = artifacts["registry"]
    aliases = artifacts["aliases"]
    history = artifacts["history"]

    if artist_key:
        key = str(artist_key)
        hit = registry[registry["artist_key"].eq(key)]
        count = int((history["artist_key"].astype(str) == key).sum())
        if not hit.empty and count >= 1:
            row = hit.iloc[0]
            return ArtistResolution(
                artist_key=key,
                match_score=1.0,
                match_basis="direct_key",
                homonym_risk=float(row.get("is_homonym") or 0),
                price_history_count=count,
                review_required=False,
            )

    norm = normalize_name(artist_name)
    if not norm:
        return ArtistResolution(None, 0.0, "missing_name", 1.0, 0, True)

    alias_hits = aliases[aliases["alias_normalized"].eq(norm)].copy()
    if not alias_hits.empty:
        alias_hits["confidence"] = pd.to_numeric(alias_hits["confidence"], errors="coerce").fillna(1.0)
        grouped = alias_hits.groupby("artist_key", as_index=False)["confidence"].max()
        grouped = grouped.sort_values(["confidence", "artist_key"], ascending=[False, True])
        key = str(grouped.iloc[0]["artist_key"])
        count = int((history["artist_key"].astype(str) == key).sum())
        review = len(grouped) > 1
        return ArtistResolution(
            artist_key=key if count >= 1 else None,
            match_score=float(grouped.iloc[0]["confidence"]),
            match_basis="alias",
            homonym_risk=1.0 if review else 0.0,
            price_history_count=count,
            review_required=review or count < 1,
        )

    name_hit = registry[(registry["name_ko_norm"].eq(norm)) | (registry["name_en_norm"].eq(norm))].copy()
    if not name_hit.empty:
        name_hit = name_hit.sort_values(["valid_price_count", "artist_key"], ascending=[False, True])
        key = str(name_hit.iloc[0]["artist_key"])
        count = int((history["artist_key"].astype(str) == key).sum())
        review = len(name_hit) > 1
        return ArtistResolution(
            artist_key=key if count >= 1 else None,
            match_score=1.0,
            match_basis="registry_name",
            homonym_risk=1.0 if review else 0.0,
            price_history_count=count,
            review_required=review or count < 1,
        )

    return ArtistResolution(None, 0.0, "not_found", 1.0, 0, True)


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


def _predict_one_seed(seed_models: dict[str, Any], feature_frame: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
    qpred = _predict_quantiles(seed_models, feature_frame, params)
    residual_x = _residual_feature_frame(feature_frame, qpred, params)
    residual = np.asarray(seed_models["lightgbm_residual"].predict(residual_x), dtype=float)
    correction = np.clip(
        float(params["current_residual_strength"]) * residual,
        -float(params["current_residual_cap_log"]),
        float(params["current_residual_cap_log"]),
    )
    out = qpred.copy()
    out["lgb_huber_residual_log"] = residual
    out["current_residual_correction_log"] = correction
    out["current_pred_log"] = out["lgbq_full_lean_avg"].to_numpy(dtype=float) + correction
    return out


def predict_by_artist_key(
    input_frame: pd.DataFrame,
    artist_key: str,
    *,
    artifacts: dict[str, pd.DataFrame] | None = None,
    models: dict[int, dict[str, Any]] | None = None,
    params: dict[str, Any] | None = None,
) -> pd.DataFrame:
    params = params or load_params()
    models = models or load_models()
    artifacts = artifacts or load_artifacts()
    history = artifacts["history"]
    artist_history = history[history["artist_key"].astype(str).eq(str(artist_key))].copy()
    if artist_history.empty:
        raise ValueError(f"artist train history not found: {artist_key}")

    frame = build_feature_frame(input_frame)
    fs = assign_stats(frame, artist_history, params)
    seed_parts = [_predict_one_seed(models[int(seed)], fs, params) for seed in params["seeds"]]
    mean = pd.concat(seed_parts, keys=params["seeds"], names=["seed", "row"])
    mean = mean.groupby(level="row").mean(numeric_only=True).sort_index()

    out = input_frame.copy()
    out["artist_key"] = str(artist_key)
    out["warm_lite_unified_current_pred_log"] = mean["current_pred_log"].to_numpy(dtype=float)
    out["warm_lite_unified_current_pred_price_krw"] = np.clip(
        np.exp(out["warm_lite_unified_current_pred_log"].to_numpy(dtype=float)),
        1_000.0,
        None,
    )
    out["lgbq_full_q10"] = mean["lgbq_full_q10"].to_numpy(dtype=float)
    out["lgbq_full_q50"] = mean["lgbq_full_q50"].to_numpy(dtype=float)
    out["lgbq_full_q90"] = mean["lgbq_full_q90"].to_numpy(dtype=float)
    out["lgbq_lean_q50"] = mean["lgbq_lean_q50"].to_numpy(dtype=float)
    out["lgbq_full_lean_avg"] = mean["lgbq_full_lean_avg"].to_numpy(dtype=float)
    out["lgbq_width"] = mean["lgbq_width"].to_numpy(dtype=float)
    out["lgb_huber_residual_log"] = mean["lgb_huber_residual_log"].to_numpy(dtype=float)
    out["current_residual_correction_log"] = mean["current_residual_correction_log"].to_numpy(dtype=float)
    out["artist_history_n"] = int(len(artist_history))
    out["runtime_source"] = "frozen_csv_no_db"
    return out


def predict(
    input_frame: pd.DataFrame,
    *,
    artist_name: str | None = None,
    artist_key: str | None = None,
    artifacts: dict[str, pd.DataFrame] | None = None,
    models: dict[int, dict[str, Any]] | None = None,
    params: dict[str, Any] | None = None,
) -> pd.DataFrame:
    artifacts = artifacts or load_artifacts()
    resolved = resolve_artist(artist_name=artist_name, artist_key=artist_key, artifacts=artifacts)
    if resolved.artist_key is None or resolved.review_required:
        raise ValueError(f"artist not resolved for warm prediction: {resolved}")
    out = predict_by_artist_key(
        input_frame,
        resolved.artist_key,
        artifacts=artifacts,
        models=models,
        params=params,
    )
    out["artist_match_score"] = resolved.match_score
    out["artist_match_basis"] = resolved.match_basis
    out["artist_homonym_risk"] = resolved.homonym_risk
    return out
