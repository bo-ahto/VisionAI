"""OOF v2 엔진 학습 — 생성 추정가 기반 낙찰가 예측 모델.

Phase 3 Model-B로 OOF 추정가 생성 → Phase 1-2 구조로 재학습.

Usage:
    PYTHONPATH=src python3 scripts/train_v2_engine.py
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "k-auction-works-20260325.csv"
OUTPUT_DIR = ROOT / "model_test_results"


def main() -> None:
    # ─── 1. Hedonic Features 빌드 ───
    logger.info("=== Step 1: Hedonic Features 빌드 ===")
    from visionai.price_engine.estimate_generator.hedonic_features import (
        build_hedonic_features,
    )

    df = build_hedonic_features(DATA_PATH)
    logger.info("Features built: %d rows", len(df))

    # ─── 2. OOF 추정가 생성 ───
    logger.info("=== Step 2: OOF 추정가 생성 (Expanding Window) ===")
    from visionai.price_engine.models.target_transform_v2 import PriceEngineV2

    v2 = PriceEngineV2(iterations=2000, depth=8, learning_rate=0.05)

    # OOF는 전체 데이터에서 생성 (train+calib+valid, test 제외)
    non_test = df[df["split"] != "test"].copy()
    logger.info("OOF source: %d rows (test excluded)", len(non_test))

    oof_estimates = v2.generate_oof_estimates(
        non_test, n_folds=5, session_col="회차", target_col="ln_estimate_mid_target"
    )

    oof_valid = oof_estimates["est_mid_oof"].notna().sum()
    logger.info("OOF estimates generated: %d / %d rows", oof_valid, len(non_test))

    # ─── 3. v2 모델 학습 ───
    logger.info("=== Step 3: v2 모델 학습 ===")
    train = non_test[non_test["split"] == "train"]
    valid = non_test[non_test["split"] == "valid"]

    train_oof = oof_estimates.loc[train.index]
    valid_oof = oof_estimates.loc[valid.index]

    v2.fit(
        train_df=train,
        oof_estimates=train_oof,
        valid_df=valid,
        valid_oof=valid_oof,
    )

    # ─── 4. 모델 저장 ───
    model_path = OUTPUT_DIR / "price_engine_v2.cbm"
    v2._model.save_model(str(model_path))
    logger.info("v2 model saved to %s", model_path)

    # ─── 5. Validation 평가 ───
    logger.info("=== Step 4: Validation 평가 ===")
    valid_has_oof = valid_oof["est_mid_oof"].notna()
    if valid_has_oof.sum() > 0:
        valid_v2 = valid.loc[valid_has_oof]
        oof_v2 = valid_oof.loc[valid_has_oof]

        est_mid = oof_v2["est_mid_oof"].values
        est_low = oof_v2["est_low_oof"].values
        est_high = oof_v2["est_high_oof"].values

        y_pred = v2.predict(valid_v2, est_mid=est_mid, est_low=est_low, est_high=est_high)
        y_true = pd.to_numeric(valid_v2["낙찰가"], errors="coerce").values

        valid_mask = np.isfinite(y_true) & np.isfinite(y_pred) & (y_true > 0)
        y_true_f = y_true[valid_mask]
        y_pred_f = y_pred[valid_mask]

        # MdAPE
        ape = np.abs(y_pred_f - y_true_f) / y_true_f
        mdape = float(np.median(ape) * 100)
        mape = float(np.mean(ape) * 100)

        # R²
        ss_res = np.sum((y_true_f - y_pred_f) ** 2)
        ss_tot = np.sum((y_true_f - np.mean(y_true_f)) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        # ±20% 이내 비율
        within_20 = float(np.mean(ape <= 0.20) * 100)

        logger.info("=" * 60)
        logger.info("v2 Validation 결과 (n=%d)", len(y_true_f))
        logger.info("MdAPE: %.2f%%", mdape)
        logger.info("MAPE: %.2f%%", mape)
        logger.info("R²: %.4f", r2)
        logger.info("±20%% 이내: %.1f%%", within_20)
        logger.info("=" * 60)
    else:
        logger.warning("No valid OOF estimates for validation set.")


if __name__ == "__main__":
    main()
