"""Phase 2 실험 ③: auction_type별 분리 모델.

위클리/프리미엄/메이저 각각 별도 CatBoost를 학습하고 통합 모델과 비교한다.
기획서 참조: 4.2절 ③
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    """분리 모델 실험."""
    from visionai.price_engine.models.predictor import load_model
    from visionai.price_engine.models.segment_calibrator import fit_calibration, apply_calibration
    from visionai.price_engine.models.target_transform import predict_transform, train_transform_model
    from visionai.price_engine.validation.metrics import compute_metrics

    df = pd.read_parquet(ROOT / "data" / "preprocessed_features.parquet")
    train = df[df["split"] == "train"]
    valid = df[df["split"] == "valid"]
    test = df[df["split"] == "test"].copy()
    y_true = test["낙찰가"].astype(float).values

    # === 통합 모델 (기존 Champion) ===
    unified_model = load_model(ROOT / "model_test_results" / "target_transform_v1.cbm")
    y_pred_u_raw = predict_transform(unified_model, test)
    est_t = ((test["추정가(최저)"].astype(float) + test["추정가(최고)"].astype(float)) / 2).values

    y_pred_v = predict_transform(unified_model, valid)
    y_true_v = valid["낙찰가"].astype(float).values
    est_v = ((valid["추정가(최저)"].astype(float) + valid["추정가(최고)"].astype(float)) / 2).values
    factors = fit_calibration(y_true_v, y_pred_v, valid["타입"].values, est_v)
    y_pred_unified = apply_calibration(y_pred_u_raw, test["타입"].values, est_t, factors, blend_weight=0.0)

    # === 분리 모델 (타입별) ===
    y_pred_split = np.zeros(len(test))

    for atype in ["위클리", "프리미엄", "메이저"]:
        train_a = train[train["타입"] == atype]
        valid_a = valid[valid["타입"] == atype]
        test_a = test[test["타입"] == atype]

        if len(train_a) < 100 or len(valid_a) < 20:
            logging.warning("Skipping %s: insufficient data", atype)
            continue

        logging.info("Training %s model: train=%d, valid=%d", atype, len(train_a), len(valid_a))
        model_a = train_transform_model(
            train_a, valid_a, iterations=1500, early_stopping_rounds=150
        )

        y_pred_a = predict_transform(model_a, test_a)
        mask = test["타입"] == atype
        y_pred_split[mask.values] = y_pred_a

    # === 비교 ===
    m_unified = compute_metrics(y_true, y_pred_unified)
    m_split = compute_metrics(y_true, y_pred_split)

    print(f"\n{'='*70}")
    print("Phase 2 실험 ③: 분리 모델 vs 통합 모델")
    print(f"{'='*70}")
    print(f"{'모델':<20} {'MAPE':>8} {'MdAPE':>8} {'R²':>8} {'±20%':>8}")
    print("-" * 70)
    print(f"{'통합+Calibration':<20} {m_unified.mape:>7.2f}% {m_unified.mdape:>7.2f}% {m_unified.r2:>7.4f} {m_unified.within_20pct:>7.1f}%")
    print(f"{'분리 (타입별)':<20} {m_split.mape:>7.2f}% {m_split.mdape:>7.2f}% {m_split.r2:>7.4f} {m_split.within_20pct:>7.1f}%")

    delta = m_split.mape - m_unified.mape
    print(f"\nΔ MAPE: {delta:+.2f}%p {'(분리 개선)' if delta < 0 else '(통합 유지)'}")

    # 타입별 비교
    print(f"\n--- 타입별 ---")
    for atype in ["메이저", "프리미엄", "위클리"]:
        mask = test["타입"].values == atype
        mu = compute_metrics(y_true[mask], y_pred_unified[mask])
        ms = compute_metrics(y_true[mask], y_pred_split[mask])
        print(f"  {atype:6s}: 통합={mu.mape:6.2f}%  분리={ms.mape:6.2f}%  Δ={ms.mape-mu.mape:+.2f}%p")


if __name__ == "__main__":
    main()
