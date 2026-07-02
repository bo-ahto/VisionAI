#!/usr/bin/env python3
"""Verify the unified Warm-lite route_gap_q50 bundle against PP-ROUTE-CF9."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_wlite_q3_quantile_residual_correction_validation as q3  # noqa: E402
from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402


REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "models" / "track6" / "warm_lite_unified_route_gap_q50_v0.1_candidate"
PREDICTOR = BUNDLE / "predict" / "predict_warm_lite_unified_route_gap_q50_v0_1.py"
CF9 = REPO / "experiments" / "track6" / "PP-ROUTE-CF9_conditional_cf7_router"
OUT = REPO / "experiments" / "track6" / "PP-ROUTE-CF10_unified_route_gap_q50_bundle_parity"


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def import_predictor():
    spec = importlib.util.spec_from_file_location("wlite_unified_route_gap", PREDICTOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"predictor load failed: {PREDICTOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ensure_dirs() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)


def load_frames() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    needed = unique(
        artifact_features()["warm"]
        + q3.cb3.NUM_BASE
        + q3.CAT_COLS
        + ["medium_support_bucket", "ln_price_krw", "log_area", "price_krw", "_track6_row_id", "artist_key"]
    )
    needed = [col for col in needed if col != "grp_price_proxy"]
    train, val, test = load_scope("warm", needed)
    keep = unique([c for c in needed if c in train.columns] + ["ln_price_krw", "log_area", "price_krw"])
    return (
        train[keep].reset_index(drop=True),
        val[keep].sort_values("_track6_row_id").reset_index(drop=True),
        test[keep].sort_values("_track6_row_id").reset_index(drop=True),
    )


def predict_split(
    predictor: Any,
    frame: pd.DataFrame,
    train: pd.DataFrame,
    models: dict[int, dict[str, Any]],
    params: dict[str, Any],
    split: str,
) -> pd.DataFrame:
    parts = []
    train_by_artist = {str(k): g.copy() for k, g in train.groupby(train["artist_key"].astype(str), sort=False)}
    for artist, group in frame.groupby(frame["artist_key"].astype(str), sort=False):
        history = train_by_artist.get(str(artist))
        if history is None or history.empty:
            raise RuntimeError(f"missing history for artist {artist}")
        pred = predictor.predict(group.copy(), history, models=models, params=params)
        out = group[["_track6_row_id", "artist_key", "ln_price_krw", "price_krw"]].copy()
        out = out.rename(columns={"ln_price_krw": "actual_log", "price_krw": "actual_price"})
        out["split"] = split
        out["pred_log"] = pred["warm_lite_unified_route_gap_q50_pred_log"].to_numpy(dtype=float)
        out["current_pred_log"] = pred["current_pred_log"].to_numpy(dtype=float)
        out["cf7_pred_log"] = pred["cf7_pred_log"].to_numpy(dtype=float)
        out["route_to_cf7"] = pred["route_to_cf7"].to_numpy(dtype=bool)
        out["full_lean_gap_abs_log"] = pred["full_lean_gap_abs_log"].to_numpy(dtype=float)
        parts.append(out)
    return pd.concat(parts, ignore_index=True).sort_values("_track6_row_id").reset_index(drop=True)


def reference_predictions() -> pd.DataFrame:
    raw = pd.read_csv(CF9 / "outputs" / "test_router_candidate_predictions.csv", low_memory=False)
    val = pd.read_csv(CF9 / "outputs" / "validation_router_candidate_predictions.csv", low_memory=False)
    ref = pd.concat([val, raw], ignore_index=True)
    ref = ref[ref["candidate"].eq("route_gap_q50")].copy()
    return ref[["_track6_row_id", "split", "pred_log", "route_to_cf7"]].rename(
        columns={"pred_log": "reference_pred_log", "route_to_cf7": "reference_route_to_cf7"}
    )


def metrics(actual_price: np.ndarray, actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    actual_price = np.asarray(actual_price, dtype=float)
    actual_log = np.asarray(actual_log, dtype=float)
    pred_log = np.asarray(pred_log, dtype=float)
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "n": int(len(ape)),
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean((pred_log - actual_log) ** 2))),
    }


def main() -> None:
    ensure_dirs()
    predictor = import_predictor()
    params = predictor.load_params()
    models = predictor.load_models()
    train, val, test = load_frames()
    pred = pd.concat(
        [
            predict_split(predictor, val, train, models, params, "validation"),
            predict_split(predictor, test, train, models, params, "test"),
        ],
        ignore_index=True,
    )
    ref = reference_predictions()
    merged = pred.merge(ref, on=["_track6_row_id", "split"], how="inner", validate="one_to_one")
    merged["abs_log_diff"] = np.abs(merged["pred_log"] - merged["reference_pred_log"])
    merged["route_match"] = merged["route_to_cf7"].astype(bool) == merged["reference_route_to_cf7"].astype(bool)

    by_split = []
    for split, group in merged.groupby("split", sort=True):
        row = {"split": split}
        row.update(metrics(group["actual_price"].to_numpy(), group["actual_log"].to_numpy(), group["pred_log"].to_numpy()))
        row["max_abs_log_diff"] = float(group["abs_log_diff"].max())
        row["mean_abs_log_diff"] = float(group["abs_log_diff"].mean())
        row["n_route_mismatch"] = int((~group["route_match"]).sum())
        by_split.append(row)

    summary = {
        "experiment_id": "PP-ROUTE-CF10",
        "check": "warm_lite_unified_route_gap_q50_bundle_replay_parity_vs_PP_ROUTE_CF9",
        "bundle": str(BUNDLE.relative_to(REPO)),
        "n_reference": int(len(ref)),
        "n_replayed": int(len(pred)),
        "n_merged": int(len(merged)),
        "max_abs_log_diff": float(merged["abs_log_diff"].max()),
        "mean_abs_log_diff": float(merged["abs_log_diff"].mean()),
        "n_route_mismatch": int((~merged["route_match"]).sum()),
        "passed": bool(
            len(merged) == len(ref)
            and len(merged) == len(pred)
            and float(merged["abs_log_diff"].max()) <= 1e-10
            and int((~merged["route_match"]).sum()) == 0
        ),
        "by_split": by_split,
    }

    merged.to_csv(OUT / "outputs" / "bundle_parity_rows.csv", index=False)
    pd.DataFrame(by_split).to_csv(OUT / "outputs" / "bundle_parity_metrics_by_split.csv", index=False)
    (OUT / "artifacts" / "bundle_parity_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    report = "\n".join(
        [
            "# PP-ROUTE-CF10 Unified route_gap_q50 bundle parity",
            "",
            "```json",
            json.dumps(summary, ensure_ascii=False, indent=2),
            "```",
            "",
        ]
    )
    (OUT / "reports" / "result_report.md").write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
