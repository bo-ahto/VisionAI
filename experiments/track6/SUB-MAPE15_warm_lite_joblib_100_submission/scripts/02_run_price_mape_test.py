#!/usr/bin/env python3
"""가격 예측 모델 100건 성능 시험 스크립트.

이 스크립트는 제출 패키지 안에 포함된 100건 시험 입력 데이터와 정답 데이터를 읽고,
패키지 내부 모델 파일로 예측을 수행한 뒤 MAPE 등 성능 지표를 계산한다.
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


# 제출 패키지 루트 폴더.
ROOT = Path(__file__).resolve().parents[1]

# 모델 예측 코드와 시험 데이터 위치.
PREDICTOR = ROOT / "model_bundle" / "predict" / "predict_warm_lite_unified_current_joblib_v0_1.py"
FEATURES = ROOT / "data" / "price_test_features_100.csv"
LABELS = ROOT / "data" / "price_test_labels_100.csv"
OUT = ROOT / "outputs" / "rerun_100"


def import_predictor() -> Any:
    """패키지 내부의 예측 모듈을 파일 경로로 직접 불러온다."""
    spec = importlib.util.spec_from_file_location("warm_joblib_predictor", PREDICTOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"predictor load failed: {PREDICTOR}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def safe_float(value: object, default: float = 0.0) -> float:
    """입력값을 float로 변환한다."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def metrics(frame: pd.DataFrame) -> dict[str, Any]:
    """예측 결과 DataFrame에서 성능 지표를 계산한다.

    APE = abs(예측가격 - 실제가격) / 실제가격
    MAPE = 100건 APE 평균
    """
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
    # 결과 파일을 저장할 폴더를 만든다.
    OUT.mkdir(parents=True, exist_ok=True)

    # 모델 예측 모듈과 모델 파일을 로드한다.
    predictor = import_predictor()
    store = predictor.load_store()
    artifacts = predictor.artifacts_from_store(store)
    models = store["models"]
    params = store["params"]

    # 시험 입력 데이터와 정답 데이터를 읽는다.
    features = pd.read_csv(FEATURES, low_memory=False)
    labels = pd.read_csv(LABELS, low_memory=False)
    labels_by_id = labels.set_index("_track6_row_id")

    rows: list[dict[str, Any]] = []
    for _, row in features.iterrows():
        # 모델이 요구하는 입력 형식으로 작품 정보를 구성한다.
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

        # artist_key 기준으로 가격 예측을 수행한다.
        pred = predictor.predict_by_artist_key(
            input_frame,
            str(row["artist_key"]),
            artifacts=artifacts,
            models=models,
            params=params,
        ).iloc[0]

        # 같은 _track6_row_id의 실제 가격 정답을 가져온다.
        label = labels_by_id.loc[int(row["_track6_row_id"])]
        pred_price = float(pred["warm_lite_unified_current_pred_price_krw"])
        actual_price = float(label["actual_price"])
        pred_log = float(pred["warm_lite_unified_current_pred_log"])
        actual_log = float(label["actual_log"])

        # 작품별 예측 결과와 APE를 저장한다.
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

    # 전체 100건 성능 요약을 만든다.
    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "features": str(FEATURES.relative_to(ROOT)),
        "labels": str(LABELS.relative_to(ROOT)),
        "model_bundle": "model_bundle",
        "metrics": metrics(out),
    }

    # 상세 예측 결과와 요약 지표를 파일로 저장한다.
    out.to_csv(OUT / "predictions.csv", index=False)
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
