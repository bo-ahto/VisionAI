#!/usr/bin/env python3
"""Verify reproducibility for the best Cold research baseline.

The best fixed-test Cold baseline is the v0.3 guard+search path:
PP-Y18 representative prediction -> qwidth/gap guard -> per-artist search delta.

This script intentionally rebuilds the evaluation frame from the upstream
prediction artifacts, applies the shipped v0.3 post-processor, and compares the
result with the recorded PP-COLD-DEFENSE1 metrics.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "models" / "track6" / "cold_prediction_v0.3"
REPRO_DIR = BUNDLE / "reproduction"

Y18_PATH = REPO / "experiments" / "track6" / "PP-Y18_cold_y16_top_candidate_stability" / "outputs" / "predictions.csv"
Y2_PATH = REPO / "experiments" / "track6" / "PP-Y2_cold_lgbq_search_external_combo" / "outputs" / "predictions.csv"
QR1_PATH = REPO / "experiments" / "track6" / "PP-QR1_cold_quantile_regression_alpha_grid" / "outputs" / "predictions.csv"
H28_PATH = REPO / "experiments" / "track6" / "PP-H20_H26_search_feature_expansion" / "outputs" / "candidate_predictions.csv"
DEFENSE1_METRICS_PATH = (
    REPO
    / "experiments"
    / "track6"
    / "PP-COLD-DEFENSE1_cold_guard_search_layer_combination"
    / "outputs"
    / "test_metrics.csv"
)

Y18_CANDIDATE = "stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min30_cap0.25"
Y2_QWIDTH_CANDIDATE = "lgbq_search_all_external_interaction"
CAT_Q40_CANDIDATE = "catboost_quantile_q40"
LGB_Q40_CANDIDATE = "lightgbm_quantile_q40"
SEARCH_SOURCE = "h23_gallery_museum_median_cap0.2"
TOL = 1e-9


def load_postprocessor():
    path = BUNDLE / "predict" / "apply_cold_postprocess_v0_3.py"
    spec = importlib.util.spec_from_file_location("apply_cold_postprocess_v0_3", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def metric_triplet(actual_price: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pred_price = np.clip(np.exp(np.asarray(pred_log, dtype=float)), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
    }


def read_candidate(path: Path, candidate: str, pred_col: str) -> pd.DataFrame:
    raw = pd.read_csv(path, low_memory=False)
    part = raw[raw["candidate"].eq(candidate)].copy()
    if part.empty:
        raise ValueError(f"missing candidate {candidate} in {path}")
    return part[["split", "_track6_row_id", "pred_log"]].rename(columns={"pred_log": pred_col})


def build_frame() -> pd.DataFrame:
    y18_raw = pd.read_csv(Y18_PATH, low_memory=False)
    y18 = y18_raw[y18_raw["candidate"].eq(Y18_CANDIDATE)].copy()
    if y18.empty:
        raise ValueError(f"missing candidate {Y18_CANDIDATE} in {Y18_PATH}")
    frame = y18[
        [
            "split",
            "_track6_row_id",
            "actual_log",
            "actual_price",
            "quantile_width_log",
            "price_range_ratio",
            "artist_key",
            "pred_log",
        ]
    ].rename(columns={"pred_log": "y18_qwidth_pred_log"})

    if frame["quantile_width_log"].isna().all():
        y2_raw = pd.read_csv(Y2_PATH, low_memory=False)
        y2 = y2_raw[y2_raw["candidate"].eq(Y2_QWIDTH_CANDIDATE)].copy()
        if y2.empty:
            raise ValueError(f"missing candidate {Y2_QWIDTH_CANDIDATE} in {Y2_PATH}")
        y2 = y2[["split", "_track6_row_id", "quantile_width_log", "price_range_ratio"]].rename(
            columns={
                "quantile_width_log": "y2_quantile_width_log",
                "price_range_ratio": "y2_price_range_ratio",
            }
        )
        frame = frame.merge(y2, on=["split", "_track6_row_id"], how="left")
        frame["quantile_width_log"] = frame["quantile_width_log"].fillna(frame["y2_quantile_width_log"])
        frame["price_range_ratio"] = frame["price_range_ratio"].fillna(frame["y2_price_range_ratio"])
        frame = frame.drop(columns=["y2_quantile_width_log", "y2_price_range_ratio"])

    if frame["quantile_width_log"].isna().any() and frame["price_range_ratio"].notna().any():
        frame["quantile_width_log"] = frame["quantile_width_log"].fillna(
            np.log(frame["price_range_ratio"].clip(lower=1.0))
        )
    if frame["price_range_ratio"].isna().any() and frame["quantile_width_log"].notna().any():
        frame["price_range_ratio"] = frame["price_range_ratio"].fillna(
            np.exp(frame["quantile_width_log"].clip(lower=0.0, upper=8.0))
        )

    frame = frame.merge(read_candidate(QR1_PATH, CAT_Q40_CANDIDATE, "cat_q40_pred_log"), on=["split", "_track6_row_id"], how="inner")
    frame = frame.merge(read_candidate(QR1_PATH, LGB_Q40_CANDIDATE, "lgb_q40_pred_log"), on=["split", "_track6_row_id"], how="inner")

    h28 = pd.read_csv(H28_PATH, low_memory=False)
    h28_source_col = f"{SEARCH_SOURCE}__pred_log"
    required = ["split", "_track6_row_id", "pred_log", h28_source_col]
    missing = [c for c in required if c not in h28.columns]
    if missing:
        raise ValueError(f"{H28_PATH} missing columns: {missing}")
    h28 = h28[required].rename(columns={"pred_log": "search_shared_base_pred_log", h28_source_col: "search_source_pred_log"})

    frame = frame.merge(h28, on=["split", "_track6_row_id"], how="inner")
    frame["search_delta_from_source"] = frame["search_source_pred_log"] - frame["search_shared_base_pred_log"]
    return frame.sort_values(["split", "_track6_row_id"]).reset_index(drop=True)


def validation_thresholds(frame: pd.DataFrame) -> dict[str, float]:
    val = frame[frame["split"].eq("validation")]
    if val.empty:
        raise ValueError("validation split is empty")
    gap_for_threshold = val["y18_qwidth_pred_log"].to_numpy(dtype=float) - val["cat_q40_pred_log"].to_numpy(dtype=float)
    return {
        "qwidth_q67": float(val["quantile_width_log"].quantile(0.67)),
        "gap_q50": float(np.quantile(gap_for_threshold, 0.50)),
    }


def independent_guard(frame: pd.DataFrame, params: dict[str, Any]) -> np.ndarray:
    y18 = frame["y18_qwidth_pred_log"].to_numpy(dtype=float)
    lgb_q40 = frame["lgb_q40_pred_log"].to_numpy(dtype=float)
    qwidth = frame["quantile_width_log"].to_numpy(dtype=float)
    guard = params["guard"]
    qwidth_q67 = float(guard["qwidth_q67"])
    gap_q50 = float(guard["gap_q50"])
    weight = float(guard["weight"])
    mask = (qwidth >= qwidth_q67) & ((y18 - lgb_q40) >= gap_q50) & (lgb_q40 < y18)
    out = y18.copy()
    out[mask] = (1.0 - weight) * y18[mask] + weight * lgb_q40[mask]
    return out


def max_abs_metric_diff(left: dict[str, float], right: dict[str, float]) -> float:
    return float(max(abs(left[k] - right[k]) for k in ["MdAPE", "MAPE", "p95_APE"]))


def main() -> None:
    REPRO_DIR.mkdir(parents=True, exist_ok=True)

    frame = build_frame()
    test = frame[frame["split"].eq("test")].copy()
    if test.empty:
        raise ValueError("test split is empty")

    params = json.loads((BUNDLE / "config" / "cold_postprocess_params_v0_3.json").read_text(encoding="utf-8"))
    lookup_raw = json.loads((BUNDLE / "config" / "search_delta_lookup_v0_3.json").read_text(encoding="utf-8"))
    lookup = {str(k): float(v) for k, v in lookup_raw["artist_delta"].items()}

    pp = load_postprocessor()
    shipped = pp.apply(test, params=params, lookup=lookup)

    guard = independent_guard(test, params)
    lookup_delta = test["artist_key"].astype(str).map(lookup).fillna(0.0).to_numpy(dtype=float)
    independent_defense_lookup = guard + lookup_delta
    independent_defense_source = guard + test["search_delta_from_source"].to_numpy(dtype=float)

    actual_price = test["actual_price"].to_numpy(dtype=float)
    shipped_rep = shipped["cold_representative_pred_log"].to_numpy(dtype=float)
    shipped_def = shipped["cold_defense_pred_log"].to_numpy(dtype=float)

    reproduced_metrics = {
        "y18_base": metric_triplet(actual_price, shipped_rep),
        "guard": metric_triplet(actual_price, guard),
        "guard_search_gm": metric_triplet(actual_price, shipped_def),
    }

    recorded_raw = pd.read_csv(DEFENSE1_METRICS_PATH).set_index("candidate")
    recorded_metrics = {
        "y18_base": {
            "MdAPE": float(recorded_raw.loc["y18_base", "test_MdAPE"]),
            "MAPE": float(recorded_raw.loc["y18_base", "test_MAPE"]),
            "p95_APE": float(recorded_raw.loc["y18_base", "test_p95_APE"]),
        },
        "guard": {
            "MdAPE": float(recorded_raw.loc["guard", "test_MdAPE"]),
            "MAPE": float(recorded_raw.loc["guard", "test_MAPE"]),
            "p95_APE": float(recorded_raw.loc["guard", "test_p95_APE"]),
        },
        "guard_search_gm": {
            "MdAPE": float(recorded_raw.loc["guard_search_gm", "test_MdAPE"]),
            "MAPE": float(recorded_raw.loc["guard_search_gm", "test_MAPE"]),
            "p95_APE": float(recorded_raw.loc["guard_search_gm", "test_p95_APE"]),
        },
    }

    threshold_recalc = validation_thresholds(frame)
    threshold_diff = {
        key: abs(float(params["guard"][key]) - value)
        for key, value in threshold_recalc.items()
    }
    metric_diff = {
        name: max_abs_metric_diff(reproduced_metrics[name], recorded_metrics[name])
        for name in reproduced_metrics
    }

    source_delta_diff = np.abs(lookup_delta - test["search_delta_from_source"].to_numpy(dtype=float))
    result = {
        "model_name": "검색 피처 포함 연구 기준 예측가격",
        "internal_id": "COLD_BASE_RESEARCH_V1 / v0.3 guard+search / guard_search_gm",
        "upstream_files": {
            "pp_y18_predictions": str(Y18_PATH.relative_to(REPO)),
            "qr1_quantile_predictions": str(QR1_PATH.relative_to(REPO)),
            "h28_search_predictions": str(H28_PATH.relative_to(REPO)),
            "recorded_defense_metrics": str(DEFENSE1_METRICS_PATH.relative_to(REPO)),
        },
        "test_rows": int(len(test)),
        "validation_rows": int(frame["split"].eq("validation").sum()),
        "search_lookup_artists": int(len(lookup)),
        "test_search_coverage": float(shipped["search_covered"].mean()),
        "guard_params_from_bundle": params["guard"],
        "guard_params_recalculated_from_validation": threshold_recalc,
        "max_threshold_abs_diff": float(max(threshold_diff.values())),
        "max_postprocessor_vs_independent_lookup_log_diff": float(np.max(np.abs(shipped_def - independent_defense_lookup))),
        "max_lookup_delta_vs_source_delta_log_diff_on_test": float(np.max(source_delta_diff)),
        "max_metric_abs_diff_vs_recorded": float(max(metric_diff.values())),
        "metric_abs_diff_vs_recorded": metric_diff,
        "checks": {
            "thresholds_reproduced": bool(max(threshold_diff.values()) <= TOL),
            "postprocessor_matches_independent_formula": bool(np.max(np.abs(shipped_def - independent_defense_lookup)) <= TOL),
            "frozen_lookup_matches_h28_source_delta_on_test": bool(np.max(source_delta_diff) <= TOL),
            "recorded_metrics_reproduced": bool(max(metric_diff.values()) <= TOL),
            "all_passed": bool(
                max(threshold_diff.values()) <= TOL
                and np.max(np.abs(shipped_def - independent_defense_lookup)) <= TOL
                and np.max(source_delta_diff) <= TOL
                and max(metric_diff.values()) <= TOL
            ),
        },
    }

    metrics_rows: list[dict[str, Any]] = []
    for name, metrics in reproduced_metrics.items():
        row = {"candidate": name}
        row.update({f"reproduced_{k}": v for k, v in metrics.items()})
        row.update({f"recorded_{k}": v for k, v in recorded_metrics[name].items()})
        row["max_abs_diff"] = metric_diff[name]
        metrics_rows.append(row)
    metrics_df = pd.DataFrame(metrics_rows)

    json_path = REPRO_DIR / "best_research_reproducibility_check.json"
    csv_path = REPRO_DIR / "best_research_reproducibility_metrics.csv"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    metrics_df.to_csv(csv_path, index=False)

    print("[COLD-BEST-REPRO] all_passed:", result["checks"]["all_passed"])
    print("[COLD-BEST-REPRO] test rows:", result["test_rows"])
    print("[COLD-BEST-REPRO] search coverage:", f"{result['test_search_coverage']:.6f}")
    print("[COLD-BEST-REPRO] max threshold diff:", f"{result['max_threshold_abs_diff']:.3e}")
    print("[COLD-BEST-REPRO] max postprocessor diff:", f"{result['max_postprocessor_vs_independent_lookup_log_diff']:.3e}")
    print("[COLD-BEST-REPRO] max source delta diff:", f"{result['max_lookup_delta_vs_source_delta_log_diff_on_test']:.3e}")
    print("[COLD-BEST-REPRO] max metric diff:", f"{result['max_metric_abs_diff_vs_recorded']:.3e}")
    print(metrics_df.to_string(index=False))
    print("[COLD-BEST-REPRO] wrote:", json_path.relative_to(REPO))
    print("[COLD-BEST-REPRO] wrote:", csv_path.relative_to(REPO))


if __name__ == "__main__":
    main()
