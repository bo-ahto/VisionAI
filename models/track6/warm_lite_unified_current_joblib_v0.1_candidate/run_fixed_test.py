#!/usr/bin/env python3
"""모델 폴더 안의 fixed Warm test CSV로 joblib-only Warm 모델을 검증한다.

실행 위치와 무관하게 이 파일이 있는 번들 폴더를 기준으로 동작한다.

필요한 파일:
- predict/predict_warm_lite_unified_current_joblib_v0_1.py
- artifacts/runtime_store.joblib
- test_data/track6_test_warm.csv

출력 파일:
- test_outputs/fixed_test/joblib_predictions.csv
- test_outputs/fixed_test/joblib_errors.csv
- test_outputs/fixed_test/summary.json

주의:
- test_data/track6_test_warm.csv는 평가 입력과 정답 라벨 확인용이다.
- 예측 런타임의 작가 매칭/작가 이력/모델 로딩은 runtime_store.joblib만 사용한다.
- DB, 작가 이력 CSV, fixed_replay_feature_store.csv는 사용하지 않는다.
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


BUNDLE = Path(__file__).resolve().parent
PREDICTOR = BUNDLE / "predict" / "predict_warm_lite_unified_current_joblib_v0_1.py"
TEST_CSV = BUNDLE / "test_data" / "track6_test_warm.csv"
OUT = BUNDLE / "test_outputs" / "fixed_test"


def import_predictor() -> Any:
    spec = importlib.util.spec_from_file_location("warm_lite_unified_current_joblib", PREDICTOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"predictor load failed: {PREDICTOR}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def safe_depth(value: object) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return number if math.isfinite(number) else 0.0


def metric_summary(frame: pd.DataFrame) -> dict[str, Any]:
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


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    predictor = import_predictor()

    # runtime_store.joblib을 한 번만 읽어서 모델, 파라미터, 작가 registry,
    # alias, 학습 이력을 모두 가져온다. 이 단계에서도 DB/CSV lookup은 없다.
    store = predictor.load_store()
    params = store["params"]
    models = store["models"]
    artifacts = predictor.artifacts_from_store(store)

    test = pd.read_csv(TEST_CSV, low_memory=False).sort_values("_track6_row_id").reset_index(drop=True)
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for idx, row in test.iterrows():
        input_frame = pd.DataFrame(
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
            # fixed test CSV에는 이미 평가 대상의 artist_key가 있으므로,
            # 작가명 재검색 없이 해당 키의 학습 이력으로 예측한다.
            pred = predictor.predict_by_artist_key(
                input_frame,
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
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "bundle": str(BUNDLE),
        "runtime_store": "artifacts/runtime_store.joblib",
        "test_csv": "test_data/track6_test_warm.csv",
        "db_used": False,
        "csv_lookup_history_used": False,
        "fixed_replay_feature_store_used": False,
        "input_rows": int(len(test)),
        "predicted_rows": int(len(pred_df)),
        "error_rows": int(len(err_df)),
        "metrics": metric_summary(pred_df) if not pred_df.empty else {},
        "artifact_rows": {
            "artist_registry": int(len(artifacts["registry"])),
            "artist_aliases": int(len(artifacts["aliases"])),
            "artist_train_history": int(len(artifacts["history"])),
        },
    }

    pred_df.to_csv(OUT / "joblib_predictions.csv", index=False)
    err_df.to_csv(OUT / "joblib_errors.csv", index=False)
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
