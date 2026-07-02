#!/usr/bin/env python3
"""Reproduce the selected Warm PP258 fixed-test predictions from packaged CSV files."""
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

    raw_correction = (
        residual
        * residual_direction_match
        * apply_confidence
        * MODEL_PARAMS["huber_residual_strength"]
    )
    raw_correction += (
        stability_delta
        * stability_direction_match
        * apply_confidence
        * MODEL_PARAMS["stability_target_strength"]
    )

    q_rank = rank01(pd.to_numeric(out["quantile_width"], errors="coerce"))
    risk = row_risk(out, source, stability_target)
    directional_base_cap = np.where(
        raw_correction >= 0.0,
        MODEL_PARAMS["positive_log_cap"],
        MODEL_PARAMS["negative_log_cap"],
    )
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
    if {"actual_price", "actual_log"}.issubset(out.columns):
        actual = pd.to_numeric(out["actual_price"], errors="coerce").to_numpy(dtype=float)
        out["absolute_percentage_error"] = np.abs(out["final_price"].to_numpy(dtype=float) - actual) / np.clip(actual, 1.0, None)
        out["log_error"] = pd.to_numeric(out["actual_log"], errors="coerce").to_numpy(dtype=float) - final_log
    return out


def metrics(frame: pd.DataFrame) -> dict[str, Any]:
    valid = (
        pd.to_numeric(frame["actual_price"], errors="coerce").gt(0)
        & pd.to_numeric(frame["actual_log"], errors="coerce").notna()
        & pd.to_numeric(frame["final_price_log"], errors="coerce").notna()
    )
    subset = frame.loc[valid].copy()
    ape = pd.to_numeric(subset["absolute_percentage_error"], errors="coerce").to_numpy(dtype=float)
    log_error = pd.to_numeric(subset["log_error"], errors="coerce").to_numpy(dtype=float)
    return {
        "n": int(valid.sum()),
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean(np.square(log_error)))),
        "within_15": float(np.nanmean(ape <= 0.15)),
        "within_30": float(np.nanmean(ape <= 0.30)),
        "within_50": float(np.nanmean(ape <= 0.50)),
        "over_50pct_error_rate": float(np.nanmean(ape > 0.50)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=None, help="Package root. Defaults to parent of this script.")
    parser.add_argument("--input", default="data/pp258_model_input_validation_test.csv")
    parser.add_argument("--split", default="test", choices=["test", "validation_oof", "all"])
    parser.add_argument("--output-dir", default="outputs")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[1]
    output_dir = root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    frame = pd.read_csv(root / args.input, low_memory=False)
    predictions = calculate_pp258_predictions(frame)
    if args.split == "all":
        evaluated = predictions
    else:
        evaluated = predictions[predictions["eval_split"].eq(args.split)].copy()
    result_metrics = metrics(evaluated)

    evaluated.to_csv(output_dir / f"pp258_{args.split}_predictions.csv", index=False)
    pd.DataFrame([result_metrics]).to_csv(output_dir / f"pp258_{args.split}_metrics.csv", index=False)
    (output_dir / f"pp258_{args.split}_metrics.json").write_text(
        json.dumps(
            {
                "split": args.split,
                "model_params": MODEL_PARAMS,
                "metrics": result_metrics,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("Warm PP258 최종 운영 모델 재현 결과")
    print(f"- split: {args.split}")
    print(f"- rows: {result_metrics['n']}")
    print(f"- MdAPE: {result_metrics['MdAPE']:.6f}")
    print(f"- MAPE: {result_metrics['MAPE']:.6f}")
    print(f"- p95_APE: {result_metrics['p95_APE']:.6f}")
    print(f"- RMSE_log: {result_metrics['RMSE_log']:.6f}")
    print(f"- output: {output_dir}")


if __name__ == "__main__":
    main()
