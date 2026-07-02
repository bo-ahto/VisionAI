#!/usr/bin/env python3
"""Run the high-confidence Warm joblib submission test inside this package.

실행 위치와 무관하게 이 파일이 들어 있는 제출 패키지 폴더를 기준으로 동작한다.
"""
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


ROOT = Path(__file__).resolve().parents[1]
PREDICTOR = ROOT / "model_bundle" / "predict" / "predict_warm_lite_unified_current_joblib_v0_1.py"
FEATURES = ROOT / "data" / "warm_joblib_high_confidence_test_features.csv"
LABELS = ROOT / "data" / "warm_joblib_high_confidence_test_labels.csv"
OUT = ROOT / "outputs" / "rerun_high_confidence"


def import_predictor() -> Any:
    spec = importlib.util.spec_from_file_location("warm_joblib_predictor", PREDICTOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"predictor load failed: {PREDICTOR}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def safe_float(value: object, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def metrics(frame: pd.DataFrame) -> dict[str, Any]:
    ape = frame["APE"].to_numpy(dtype=float)
    log_error = frame["pred_log"].to_numpy(dtype=float) - frame["actual_log"].to_numpy(dtype=float)
    return {
        "n": int(len(frame)),
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean(np.square(log_error)))),
        "within_15pct": float(np.nanmean(ape <= 0.15)),
        "within_30pct": float(np.nanmean(ape <= 0.30)),
        "APE_gt_1": int(np.nansum(ape > 1.0)),
        "APE_gt_5": int(np.nansum(ape > 5.0)),
        "passes_research_goal_mape_le_15pct": bool(float(np.nanmean(ape)) <= 0.15),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    predictor = import_predictor()
    store = predictor.load_store()
    artifacts = predictor.artifacts_from_store(store)
    models = store["models"]
    params = store["params"]

    features = pd.read_csv(FEATURES, low_memory=False)
    labels = pd.read_csv(LABELS, low_memory=False)
    labels_by_id = labels.set_index("_track6_row_id")
    rows: list[dict[str, Any]] = []
    for _, row in features.iterrows():
        input_frame = pd.DataFrame(
            [
                {
                    "width_cm": safe_float(row["width_cm"]),
                    "height_cm": safe_float(row["height_cm"]),
                    "depth_cm": safe_float(row.get("depth_cm")),
                    "medium_category": str(row.get("medium_category") or "unknown"),
                    "support_category": str(row.get("support_category") or "unknown"),
                }
            ]
        )
        pred = predictor.predict_by_artist_key(
            input_frame,
            str(row["artist_key"]),
            artifacts=artifacts,
            models=models,
            params=params,
        ).iloc[0]
        label = labels_by_id.loc[int(row["_track6_row_id"])]
        pred_price = float(pred["warm_lite_unified_current_pred_price_krw"])
        actual_price = float(label["actual_price"])
        pred_log = float(pred["warm_lite_unified_current_pred_log"])
        actual_log = float(label["actual_log"])
        rows.append(
            {
                "_track6_row_id": int(row["_track6_row_id"]),
                "artist_key": str(row["artist_key"]),
                "actual_price": actual_price,
                "actual_log": actual_log,
                "pred_price": pred_price,
                "pred_log": pred_log,
                "APE": abs(pred_price - actual_price) / max(actual_price, 1.0),
                "artist_history_n": int(pred["artist_history_n"]),
                "lgbq_width": float(pred["lgbq_width"]),
                "current_residual_correction_log": float(pred["current_residual_correction_log"]),
                "runtime_source": str(pred["runtime_source"]),
            }
        )
    out = pd.DataFrame(rows)
    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "features": str(FEATURES.relative_to(ROOT)),
        "labels": str(LABELS.relative_to(ROOT)),
        "model_bundle": "model_bundle",
        "metrics": metrics(out),
    }
    out.to_csv(OUT / "predictions.csv", index=False)
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
