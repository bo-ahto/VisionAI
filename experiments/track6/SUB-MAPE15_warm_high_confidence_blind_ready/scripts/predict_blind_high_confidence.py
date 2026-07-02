#!/usr/bin/env python3
"""Predict prices for a frozen blind high-confidence Warm benchmark.

The model and high-confidence rule are loaded from the already frozen
SUB-MAPE15 submission package. This script does not train or tune anything.
It only engineers the same feature columns, applies the fixed eligibility rule,
selects the blind evaluation subset, and writes predictions.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[4]
SUBMISSION_DIR = REPO / "experiments" / "track6" / "SUB-MAPE15_warm_high_confidence_100_submission"
MODEL_CONFIG_PATH = SUBMISSION_DIR / "artifacts" / "model_config.json"
SPLIT_MANIFEST_PATH = SUBMISSION_DIR / "artifacts" / "split_manifest.json"

BASE_CANDIDATE = "hcoef_stable"
REQUIRED_COMPONENT_COLUMNS = [
    "hcoef_stable",
    "current_70_30",
    "ppv8_service_proxy",
    "svc_numeric_seed_mean",
    "l10_seq_pred_log",
    "quantile_width",
    "l10_price_range_ratio",
    "svc_group_n",
    "log_area",
]
OPTIONAL_METADATA_COLUMNS = [
    "split",
    "_track6_row_id",
    "external_artwork_id",
    "artist_key",
    "artist_name_ko",
    "artist_name_en",
    "title",
    "medium_support_bucket",
    "svc_group_level",
    "svc_coverage_tier",
    "service_confidence_tier",
]


def safe_exp(values: pd.Series | np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    return np.exp(np.clip(arr, math.log(1_000.0), math.log(1_000_000_000_000.0)))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_input_columns(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    aliases = {
        "stable_warm_price_log": "hcoef_stable",
        "base_price_log": "hcoef_stable",
        "defensive_blend_price_log": "ppv8_service_proxy",
        "similar_artwork_price_log": "svc_numeric_seed_mean",
        "warm_feature_price_log": "l10_seq_pred_log",
    }
    for source, target in aliases.items():
        if source in out.columns and target not in out.columns:
            out[target] = out[source]
    return out


def add_engineered_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = normalize_input_columns(frame)
    missing = [col for col in REQUIRED_COMPONENT_COLUMNS if col not in out.columns]
    if missing:
        raise ValueError(f"Missing required blind input columns: {missing}")

    for col in REQUIRED_COMPONENT_COLUMNS:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    component_cols = [
        "hcoef_stable",
        "current_70_30",
        "ppv8_service_proxy",
        "svc_numeric_seed_mean",
        "l10_seq_pred_log",
    ]
    out["component_prediction_spread"] = out[component_cols].std(axis=1)
    out["current_vs_stable_gap_abs"] = (out["current_70_30"] - out["hcoef_stable"]).abs()
    out["svc_group_n_log"] = np.log1p(out["svc_group_n"].fillna(0.0))
    out["current_minus_stable_log"] = out["current_70_30"] - out["hcoef_stable"]
    out["ppv8_minus_stable_log"] = out["ppv8_service_proxy"] - out["hcoef_stable"]
    out["svc_minus_stable_log"] = out["svc_numeric_seed_mean"] - out["hcoef_stable"]
    out["l10_minus_stable_log"] = out["l10_seq_pred_log"] - out["hcoef_stable"]
    out["stable_warm_price_log"] = out["hcoef_stable"]
    out["stable_warm_price"] = safe_exp(out["stable_warm_price_log"])
    return out


def high_confidence_mask(frame: pd.DataFrame, rule: dict[str, float]) -> pd.Series:
    return (
        frame["quantile_width"].le(rule["quantile_width_max"])
        & frame["component_prediction_spread"].le(rule["component_prediction_spread_max"])
        & frame["l10_price_range_ratio"].le(rule["l10_price_range_ratio_max"])
        & frame["svc_group_n"].ge(rule["svc_group_n_min"])
        & frame["current_vs_stable_gap_abs"].le(rule["current_vs_stable_gap_abs_max"])
    )


def high_confidence_risk_score(frame: pd.DataFrame, rule: dict[str, float]) -> pd.Series:
    qwidth = (frame["quantile_width"] / rule["quantile_width_max"]).clip(0.0, 10.0)
    spread = (frame["component_prediction_spread"] / rule["component_prediction_spread_max"]).clip(0.0, 10.0)
    gap = (frame["current_vs_stable_gap_abs"] / rule["current_vs_stable_gap_abs_max"]).clip(0.0, 10.0)
    ratio = (frame["l10_price_range_ratio"] / rule["l10_price_range_ratio_max"]).clip(0.0, 10.0)
    support = (rule["svc_group_n_min"] / frame["svc_group_n"].clip(lower=1.0)).clip(0.0, 10.0)
    return 0.35 * qwidth + 0.25 * spread + 0.20 * gap + 0.10 * ratio + 0.10 * support


def select_blind_subset(frame: pd.DataFrame, required_n: int, allow_fewer: bool) -> pd.DataFrame:
    eligible = frame[frame["blind_high_confidence_eligible"]].copy()
    eligible = eligible.sort_values(["high_confidence_risk_score", "_stable_sort_key"]).reset_index(drop=True)
    if len(eligible) < required_n and not allow_fewer:
        raise ValueError(
            f"Only {len(eligible)} high-confidence rows are eligible, but {required_n} are required. "
            "Provide a larger blind candidate pool or rerun with --allow-fewer for diagnostics only."
        )
    return eligible.head(required_n if len(eligible) >= required_n else len(eligible)).copy()


def predict(frame: pd.DataFrame, model: Any, feature_columns: list[str], cap: float) -> pd.DataFrame:
    out = frame.copy()
    adjustment = np.clip(model.predict(out[feature_columns]), -cap, cap)
    out["residual_adjustment_log"] = adjustment
    out["final_price_log"] = out["stable_warm_price_log"] + adjustment
    out["final_price"] = safe_exp(out["final_price_log"])
    return out


def output_columns(frame: pd.DataFrame, feature_columns: list[str]) -> list[str]:
    metadata = [col for col in OPTIONAL_METADATA_COLUMNS if col in frame.columns]
    core = [
        "blind_high_confidence_eligible",
        "blind_selected_for_evaluation",
        "high_confidence_risk_score",
        "stable_warm_price_log",
        "stable_warm_price",
        "residual_adjustment_log",
        "final_price_log",
        "final_price",
    ]
    diagnostics = [
        "hcoef_stable",
        "current_70_30",
        "ppv8_service_proxy",
        "svc_numeric_seed_mean",
        "l10_seq_pred_log",
    ]
    cols = metadata + core + feature_columns + diagnostics
    return [col for col in dict.fromkeys(cols) if col in frame.columns]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Blind candidate pool CSV with component prediction columns.")
    parser.add_argument("--output", required=True, help="Prediction CSV path.")
    parser.add_argument("--required-n", type=int, default=100, help="Number of high-confidence rows to select.")
    parser.add_argument("--allow-fewer", action="store_true", help="Allow fewer than required-n for diagnostic runs.")
    args = parser.parse_args()

    model_config = load_json(MODEL_CONFIG_PATH)
    split_manifest = load_json(SPLIT_MANIFEST_PATH)
    rule = split_manifest["selection_rule"]
    model = joblib.load(REPO / model_config["model_path"])
    feature_columns = model_config["feature_columns"]
    cap = float(model_config["residual_adjustment_cap_log"])

    frame = pd.read_csv(args.input, low_memory=False)
    frame = add_engineered_features(frame)
    if "_track6_row_id" in frame.columns:
        frame["_stable_sort_key"] = frame["_track6_row_id"].astype(str)
    elif "external_artwork_id" in frame.columns:
        frame["_stable_sort_key"] = frame["external_artwork_id"].astype(str)
    else:
        frame["_stable_sort_key"] = np.arange(len(frame)).astype(str)

    frame["blind_high_confidence_eligible"] = high_confidence_mask(frame, rule)
    frame["high_confidence_risk_score"] = high_confidence_risk_score(frame, rule)
    selected = select_blind_subset(frame, args.required_n, args.allow_fewer)
    selected["blind_selected_for_evaluation"] = True
    predictions = predict(selected, model, feature_columns, cap)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    predictions[output_columns(predictions, feature_columns)].to_csv(output_path, index=False)

    summary = {
        "input": args.input,
        "output": args.output,
        "input_rows": int(len(frame)),
        "eligible_rows": int(frame["blind_high_confidence_eligible"].sum()),
        "selected_rows": int(len(predictions)),
        "required_n": args.required_n,
        "allow_fewer": args.allow_fewer,
        "model_path": model_config["model_path"],
        "selection_rule": rule,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
