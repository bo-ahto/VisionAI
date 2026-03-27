"""Shadow Mode — 예측 기록기.

실 경매 입력을 받아 예측만 기록하고, 결과 확정 후 retrospective scoring에 사용한다.
사용자에게 예측값을 노출하지 않고, 모델 품질 추적 목적으로만 사용.

기획서 참조: 9장 #10, 개발 계획서 Sprint 3
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor

from visionai.price_engine.models.segment_calibrator import (
    CalibrationFactors,
    apply_calibration,
)
from visionai.price_engine.models.target_transform import predict_transform

logger = logging.getLogger(__name__)

SHADOW_DIR = Path("data/shadow_logs")


def record_prediction(
    model: CatBoostRegressor,
    input_row: pd.DataFrame,
    factors: CalibrationFactors,
    output_dir: Path | None = None,
) -> dict:
    """단건 예측을 기록한다.

    Args:
        model: Target Transform CatBoost 모델.
        input_row: 1행짜리 피처 DataFrame.
        factors: Calibration 보정 계수.
        output_dir: 기록 디렉토리. None이면 SHADOW_DIR.

    Returns:
        기록된 예측 레코드 dict.
    """
    if output_dir is None:
        output_dir = SHADOW_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # 예측
    y_pred_raw = predict_transform(model, input_row)
    est_mid = (
        input_row["추정가(최저)"].astype(float).values
        + input_row["추정가(최고)"].astype(float).values
    ) / 2
    y_pred_cal = apply_calibration(
        y_pred_raw,
        input_row["타입"].values,
        est_mid,
        factors,
        blend_weight=0.0,
    )

    record = {
        "timestamp": datetime.now().isoformat(),
        "model_version": "target_transform_v1+calibration",
        "input": {
            "작가": str(input_row["artist_clean"].iloc[0]) if "artist_clean" in input_row.columns else "",
            "타입": str(input_row["타입"].iloc[0]),
            "회차": int(input_row["회차"].iloc[0]),
            "Lot": int(input_row["Lot"].iloc[0]),
            "추정가_최저": int(input_row["추정가(최저)"].iloc[0]),
            "추정가_최고": int(input_row["추정가(최고)"].iloc[0]),
        },
        "prediction": {
            "predicted_raw": int(y_pred_raw[0]),
            "predicted_calibrated": int(y_pred_cal[0]),
            "estimate_mid": int(est_mid[0]),
        },
        "actual": None,  # 경매 결과 확정 후 채움
        "scored": False,
    }

    # JSONL 기록
    log_file = output_dir / f"shadow_{datetime.now().strftime('%Y%m%d')}.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    logger.info(
        "Shadow recorded: %s Lot%d → ₩%s (raw ₩%s)",
        record["input"]["타입"],
        record["input"]["Lot"],
        f"{record['prediction']['predicted_calibrated']:,}",
        f"{record['prediction']['predicted_raw']:,}",
    )

    return record


def batch_record(
    model: CatBoostRegressor,
    df: pd.DataFrame,
    factors: CalibrationFactors,
    output_dir: Path | None = None,
) -> int:
    """다건 예측을 일괄 기록한다.

    Returns:
        기록된 건수.
    """
    count = 0
    for idx in df.index:
        row = df.loc[[idx]]
        record_prediction(model, row, factors, output_dir)
        count += 1

    logger.info("Batch recorded: %d predictions", count)
    return count
