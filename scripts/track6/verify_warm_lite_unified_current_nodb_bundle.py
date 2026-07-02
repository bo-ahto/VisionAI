#!/usr/bin/env python3
"""Verify no-DB Warm-lite unified current bundle on fixed Warm test rows."""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "models" / "track6" / "warm_lite_unified_current_nodb_v0.1_candidate"
PREDICTOR = BUNDLE / "predict" / "predict_warm_lite_unified_current_nodb_v0_1.py"
TEST_CSV = (
    REPO
    / "models"
    / "track6"
    / "price_prediction_v0.1"
    / "data"
    / "training"
    / "track6_split"
    / "track6_test_warm.csv"
)
OUT = REPO / "experiments" / "track6" / "PP-WLITE-NODB_bundle_fixed_test_verification"


def import_predictor() -> Any:
    spec = importlib.util.spec_from_file_location("warm_lite_unified_current_nodb", PREDICTOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"predictor load failed: {PREDICTOR}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def metrics(frame: pd.DataFrame) -> dict[str, Any]:
    actual_price = frame["actual_price"].to_numpy(dtype=float)
    actual_log = frame["actual_log"].to_numpy(dtype=float)
    pred_log = frame["pred_log"].to_numpy(dtype=float)
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "n": int(len(frame)),
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean((pred_log - actual_log) ** 2))),
        "APE_gt_1": int(np.sum(ape > 1.0)),
        "APE_gt_5": int(np.sum(ape > 5.0)),
    }


def safe_depth(value: object) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return number if math.isfinite(number) else 0.0


def main() -> None:
    for sub in ["outputs", "artifacts", "reports"]:
        (OUT / sub).mkdir(parents=True, exist_ok=True)

    predictor = import_predictor()
    params = predictor.load_params()
    models = predictor.load_models()
    artifacts = predictor.load_artifacts()

    test = pd.read_csv(TEST_CSV, low_memory=False).sort_values("_track6_row_id").reset_index(drop=True)
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for idx, row in test.iterrows():
        frame = pd.DataFrame(
            [
                {
                    "width_cm": float(row["width_cm"]),
                    "height_cm": float(row["height_cm"]),
                    "depth_cm": safe_depth(row.get("depth_cm")),
                    "medium_category": str(row.get("medium_category") or "unknown"),
                    "support_category": str(row.get("support_category") or "unknown"),
                }
            ]
        )
        try:
            pred = predictor.predict_by_artist_key(
                frame,
                str(row["artist_key"]),
                artifacts=artifacts,
                models=models,
                params=params,
            ).iloc[0]
            rows.append(
                {
                    "_track6_row_id": int(row["_track6_row_id"]),
                    "artist_key": str(row["artist_key"]),
                    "actual_price": float(row["price_krw"]),
                    "actual_log": float(row["ln_price_krw"]),
                    "pred_log": float(pred["warm_lite_unified_current_pred_log"]),
                    "pred_price": float(pred["warm_lite_unified_current_pred_price_krw"]),
                    "lgbq_full_q50": float(pred["lgbq_full_q50"]),
                    "lgbq_lean_q50": float(pred["lgbq_lean_q50"]),
                    "lgbq_full_lean_avg": float(pred["lgbq_full_lean_avg"]),
                    "lgb_huber_residual_log": float(pred["lgb_huber_residual_log"]),
                    "artist_history_n": int(pred["artist_history_n"]),
                    "runtime_source": str(pred["runtime_source"]),
                }
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(
                {
                    "idx": int(idx),
                    "_track6_row_id": int(row["_track6_row_id"]),
                    "artist_key": str(row["artist_key"]),
                    "error": repr(exc),
                }
            )

    pred_df = pd.DataFrame(rows)
    err_df = pd.DataFrame(errors)
    if not pred_df.empty:
        pred_df["APE"] = (
            np.abs(pred_df["pred_price"].to_numpy(dtype=float) - pred_df["actual_price"].to_numpy(dtype=float))
            / np.clip(pred_df["actual_price"].to_numpy(dtype=float), 1.0, None)
        )
        pred_df["abs_log_error"] = np.abs(pred_df["pred_log"] - pred_df["actual_log"])

    summary = {
        "experiment_id": "PP-WLITE-NODB",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "bundle": str(BUNDLE.relative_to(REPO)),
        "db_used": False,
        "fixed_replay_feature_store_used": False,
        "test_csv_used_only_as_input_and_label": str(TEST_CSV.relative_to(REPO)),
        "input_rows": int(len(test)),
        "predicted_rows": int(len(pred_df)),
        "error_rows": int(len(err_df)),
        "metrics": metrics(pred_df) if not pred_df.empty else {},
        "artifact_rows": {
            "artist_registry": int(len(artifacts["registry"])),
            "artist_aliases": int(len(artifacts["aliases"])),
            "artist_train_history": int(len(artifacts["history"])),
        },
    }

    pred_df.to_csv(OUT / "outputs" / "nodb_predictions.csv", index=False)
    err_df.to_csv(OUT / "outputs" / "nodb_errors.csv", index=False)
    (OUT / "artifacts" / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    report = "\n".join(
        [
            "# PP-WLITE-NODB bundle verification",
            "",
            "## Summary",
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
