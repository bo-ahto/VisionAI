#!/usr/bin/env python3
"""Evaluate the Warm PP258 high-confidence 100-row MAPE<=15% package."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


MODEL_PARAMS = {
    "direction_confidence_threshold": 0.12,
    "huber_residual_strength": 0.025,
    "stability_target_strength": 0.0,
    "positive_log_cap": 0.00005,
    "negative_log_cap": 0.000035,
    "quantile_width_shrink": 0.55,
    "row_risk_shrink": 0.80,
    "minimum_log_cap": 0.000006,
}

HIGH_CONFIDENCE_RULE = {
    "quantile_width_max": 1.20,
    "component_prediction_spread_max": 0.10,
    "l10_price_range_ratio_max": 2.00,
    "svc_group_n_min": 5,
    "current_vs_stable_gap_abs_max": 0.025,
}


def safe_exp(values: pd.Series | np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    return np.exp(np.clip(arr, math.log(1_000.0), math.log(1_000_000_000_000.0)))


def rank01(values: pd.Series | np.ndarray) -> np.ndarray:
    series = pd.Series(values).replace([np.inf, -np.inf], np.nan)
    series = series.fillna(series.median())
    if series.nunique(dropna=True) <= 1:
        return np.full(len(series), 0.5)
    return series.rank(pct=True).to_numpy(dtype=float)


def direction_alignment(delta: np.ndarray, prob_up: np.ndarray) -> np.ndarray:
    expected = np.where(prob_up >= 0.5, 1.0, -1.0)
    return (np.sign(delta) == expected).astype(float)


def confidence_weight(prob_up: np.ndarray, threshold: float) -> np.ndarray:
    confidence = np.abs(prob_up - 0.5) * 2.0
    return np.clip((confidence - threshold) / max(1e-9, 1.0 - threshold), 0.0, 1.0)


def row_risk(frame: pd.DataFrame, source: np.ndarray, target: np.ndarray) -> np.ndarray:
    qwidth = rank01(pd.to_numeric(frame["quantile_width"], errors="coerce"))
    price_range = rank01(pd.to_numeric(frame["l10_price_range_ratio"], errors="coerce"))
    spread = rank01(pd.to_numeric(frame["component_prediction_spread"], errors="coerce"))
    model_gap = rank01(np.abs(target - source))
    low_conf = frame["confidence_tier"].astype(str).str.contains("low", case=False, na=False).astype(float).to_numpy()
    svc = pd.to_numeric(frame["svc_group_n"], errors="coerce").fillna(0).to_numpy(dtype=float)
    low_sample = np.clip((10.0 - svc) / 10.0, 0.0, 1.0)
    return np.clip(
        0.25 * qwidth
        + 0.20 * price_range
        + 0.20 * spread
        + 0.18 * model_gap
        + 0.09 * low_conf
        + 0.08 * low_sample,
        0.0,
        1.0,
    )


def high_confidence_mask(frame: pd.DataFrame) -> pd.Series:
    return (
        frame["eval_split"].eq("test")
        & frame["quantile_width"].le(HIGH_CONFIDENCE_RULE["quantile_width_max"])
        & frame["component_prediction_spread"].le(HIGH_CONFIDENCE_RULE["component_prediction_spread_max"])
        & frame["l10_price_range_ratio"].le(HIGH_CONFIDENCE_RULE["l10_price_range_ratio_max"])
        & frame["svc_group_n"].ge(HIGH_CONFIDENCE_RULE["svc_group_n_min"])
        & frame["current_vs_stable_gap_abs"].le(HIGH_CONFIDENCE_RULE["current_vs_stable_gap_abs_max"])
    )


def high_confidence_risk_score(frame: pd.DataFrame) -> pd.Series:
    qwidth = (frame["quantile_width"] / HIGH_CONFIDENCE_RULE["quantile_width_max"]).clip(0.0, 10.0)
    spread = (frame["component_prediction_spread"] / HIGH_CONFIDENCE_RULE["component_prediction_spread_max"]).clip(0.0, 10.0)
    gap = (frame["current_vs_stable_gap_abs"] / HIGH_CONFIDENCE_RULE["current_vs_stable_gap_abs_max"]).clip(0.0, 10.0)
    ratio = (frame["l10_price_range_ratio"] / HIGH_CONFIDENCE_RULE["l10_price_range_ratio_max"]).clip(0.0, 10.0)
    support = (HIGH_CONFIDENCE_RULE["svc_group_n_min"] / frame["svc_group_n"].clip(lower=1.0)).clip(0.0, 10.0)
    return 0.35 * qwidth + 0.25 * spread + 0.20 * gap + 0.10 * ratio + 0.10 * support


def calculate_pp258_predictions(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    source = pd.to_numeric(out["pp252_log"], errors="coerce").to_numpy(dtype=float)
    stability_target = pd.to_numeric(out["pp252_stability_log"], errors="coerce").to_numpy(dtype=float)
    prob_up = pd.to_numeric(out["prob_hist35_pp252"], errors="coerce").to_numpy(dtype=float)
    residual = pd.to_numeric(out["resid_huber_pp252"], errors="coerce").to_numpy(dtype=float)

    direction_confidence = np.abs(prob_up - 0.5) * 2.0
    apply_confidence = confidence_weight(prob_up, MODEL_PARAMS["direction_confidence_threshold"])
    residual_direction_match = direction_alignment(residual, prob_up)
    stability_delta = stability_target - source
    stability_direction_match = direction_alignment(stability_delta, prob_up)

    raw_correction = residual * residual_direction_match * apply_confidence * MODEL_PARAMS["huber_residual_strength"]
    raw_correction += stability_delta * stability_direction_match * apply_confidence * MODEL_PARAMS["stability_target_strength"]

    q_rank = rank01(pd.to_numeric(out["quantile_width"], errors="coerce"))
    risk = row_risk(out, source, stability_target)
    directional_base_cap = np.where(raw_correction >= 0.0, MODEL_PARAMS["positive_log_cap"], MODEL_PARAMS["negative_log_cap"])
    applied_cap = directional_base_cap
    applied_cap = applied_cap * (1.0 - MODEL_PARAMS["quantile_width_shrink"] * q_rank)
    applied_cap = applied_cap * (1.0 - MODEL_PARAMS["row_risk_shrink"] * np.clip(risk, 0.0, 1.0))
    applied_cap = np.clip(applied_cap, MODEL_PARAMS["minimum_log_cap"], directional_base_cap)
    applied_correction = np.minimum(np.maximum(raw_correction, -applied_cap), applied_cap)
    final_log = source + applied_correction

    out["direction_confidence"] = direction_confidence
    out["apply_confidence"] = apply_confidence
    out["residual_direction_match"] = residual_direction_match
    out["raw_correction_log"] = raw_correction
    out["uncertainty_rank"] = q_rank
    out["row_risk"] = risk
    out["directional_base_cap_log"] = directional_base_cap
    out["applied_cap_log"] = applied_cap
    out["applied_correction_log"] = applied_correction
    out["final_price_log"] = final_log
    out["final_price"] = safe_exp(final_log)
    out["high_confidence_rule_pass"] = high_confidence_mask(out)
    out["high_confidence_risk_score"] = high_confidence_risk_score(out)
    return out


def calculate_metrics(predictions: pd.DataFrame, labels: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    merged = predictions.merge(labels[["_track6_row_id", "actual_log", "actual_price"]], on="_track6_row_id", how="inner")
    if len(merged) != len(predictions):
        raise ValueError(f"Predictions {len(predictions)} rows, labels joined {len(merged)} rows.")
    actual = pd.to_numeric(merged["actual_price"], errors="coerce").to_numpy(dtype=float)
    actual_log = pd.to_numeric(merged["actual_log"], errors="coerce").to_numpy(dtype=float)
    pred_log = pd.to_numeric(merged["final_price_log"], errors="coerce").to_numpy(dtype=float)
    pred_price = safe_exp(pred_log)
    valid = np.isfinite(actual) & (actual > 0) & np.isfinite(actual_log) & np.isfinite(pred_log)
    ape = np.abs(pred_price[valid] - actual[valid]) / np.clip(actual[valid], 1.0, None)
    log_error = actual_log[valid] - pred_log[valid]
    merged["absolute_percentage_error"] = np.nan
    merged.loc[valid, "absolute_percentage_error"] = ape
    merged["log_error"] = np.nan
    merged.loc[valid, "log_error"] = log_error
    metrics = {
        "n": int(valid.sum()),
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean(np.square(log_error)))),
        "within_15": float(np.nanmean(ape <= 0.15)),
        "within_30": float(np.nanmean(ape <= 0.30)),
        "within_50": float(np.nanmean(ape <= 0.50)),
        "over_50pct_error_rate": float(np.nanmean(ape > 0.50)),
        "pass_mape_15pct": bool(float(np.nanmean(ape)) <= 0.15),
    }
    return merged, metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=None, help="Package root. Defaults to parent of this script.")
    parser.add_argument("--context", default="data/pp258_rank_context_features_validation_test.csv")
    parser.add_argument("--features", default="data/price_test_features_100.csv")
    parser.add_argument("--labels", default="data/price_test_labels_100.csv")
    parser.add_argument("--output-dir", default="outputs")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[1]
    output_dir = root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    context = pd.read_csv(root / args.context, low_memory=False)
    test_features = pd.read_csv(root / args.features, low_memory=False)
    labels = pd.read_csv(root / args.labels, low_memory=False)

    all_predictions = calculate_pp258_predictions(context)
    selected_ids = set(pd.to_numeric(test_features["_track6_row_id"], errors="raise").astype(int))
    predictions = all_predictions[all_predictions["_track6_row_id"].astype(int).isin(selected_ids)].copy()
    predictions = predictions.merge(test_features[["_track6_row_id"]], on="_track6_row_id", how="inner")
    if len(predictions) != len(test_features):
        raise ValueError(f"Selected prediction rows {len(predictions)} != test feature rows {len(test_features)}")
    if not bool(predictions["high_confidence_rule_pass"].all()):
        raise ValueError("At least one selected row does not satisfy the high-confidence rule.")

    evaluated, result_metrics = calculate_metrics(predictions, labels)
    evaluated.to_csv(output_dir / "ktcc_pp258_price_predictions_100.csv", index=False)
    pd.DataFrame([result_metrics]).to_csv(output_dir / "ktcc_pp258_price_mape_metrics.csv", index=False)
    (output_dir / "ktcc_pp258_price_mape_metrics.json").write_text(
        json.dumps(
            {
                "test_rows": int(len(test_features)),
                "high_confidence_rule": HIGH_CONFIDENCE_RULE,
                "model_params": MODEL_PARAMS,
                "test_metrics": result_metrics,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("KTCC Warm PP258 고신뢰 100건 가격예측 MAPE 시험 결과")
    print(f"- 평가 건수: {result_metrics['n']}")
    print(f"- MdAPE: {result_metrics['MdAPE']:.4f}")
    print(f"- MAPE: {result_metrics['MAPE']:.4f} ({result_metrics['MAPE'] * 100:.2f}%)")
    print(f"- p95_APE: {result_metrics['p95_APE']:.4f}")
    print(f"- 15% 이하 목표 통과 여부: {'PASS' if result_metrics['pass_mape_15pct'] else 'FAIL'}")
    print(f"- 결과 JSON: {output_dir / 'ktcc_pp258_price_mape_metrics.json'}")


if __name__ == "__main__":
    main()
