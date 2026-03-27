"""Phase 2 실험 ④: Two-Step (분류→조건부 회귀).

Step 1: 추정가 이상 낙찰 여부 이진 분류
Step 2: 상향/하향 그룹별 회귀
기획서 참조: 4.2절 ④, Kim & Kim (2024)
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier, CatBoostRegressor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    """Two-Step 실험."""
    from visionai.price_engine.models.predictor import (
        BASELINE_FEATURES,
        CAT_FEATURE_INDICES,
        prepare_features,
        load_model,
    )
    from visionai.price_engine.models.segment_calibrator import fit_calibration, apply_calibration
    from visionai.price_engine.models.target_transform import predict_transform
    from visionai.price_engine.validation.metrics import compute_metrics

    df = pd.read_parquet(ROOT / "data" / "preprocessed_features.parquet")
    train = df[df["split"] == "train"].copy()
    valid = df[df["split"] == "valid"].copy()
    test = df[df["split"] == "test"].copy()
    y_true = test["낙찰가"].astype(float).values

    # === 통합 모델 (Champion) ===
    unified_model = load_model(ROOT / "model_test_results" / "target_transform_v1.cbm")
    y_pred_u_raw = predict_transform(unified_model, test)
    est_t = ((test["추정가(최저)"].astype(float) + test["추정가(최고)"].astype(float)) / 2).values

    y_pred_v = predict_transform(unified_model, valid)
    y_true_v = valid["낙찰가"].astype(float).values
    est_v = ((valid["추정가(최저)"].astype(float) + valid["추정가(최고)"].astype(float)) / 2).values
    factors = fit_calibration(y_true_v, y_pred_v, valid["타입"].values, est_v)
    y_pred_unified = apply_calibration(y_pred_u_raw, test["타입"].values, est_t, factors, blend_weight=0.0)

    # === Two-Step ===

    # Step 1: 분류 — 추정가 중앙값 이상 낙찰?
    train["estimate_mid"] = (train["추정가(최저)"].astype(float) + train["추정가(최고)"].astype(float)) / 2
    valid["estimate_mid_v"] = (valid["추정가(최저)"].astype(float) + valid["추정가(최고)"].astype(float)) / 2
    test["estimate_mid_t"] = est_t

    train_label = (train["낙찰가"].astype(float) >= train["estimate_mid"]).astype(int)
    valid_label = (valid["낙찰가"].astype(float) >= valid["estimate_mid_v"]).astype(int)

    X_train = prepare_features(train)
    X_valid = prepare_features(valid)
    X_test = prepare_features(test)

    logging.info("Step 1: Classification (premium vs discount)")
    logging.info("  Train positive rate: %.1f%%", train_label.mean() * 100)

    clf = CatBoostClassifier(
        iterations=1000,
        depth=6,
        learning_rate=0.05,
        cat_features=CAT_FEATURE_INDICES,
        random_seed=42,
        verbose=0,
        early_stopping_rounds=100,
    )
    clf.fit(X_train, train_label, eval_set=(X_valid, valid_label), use_best_model=True)

    test_class = clf.predict(X_test).flatten()
    premium_mask = test_class == 1
    discount_mask = test_class == 0

    logging.info("  Test premium: %d (%.1f%%)", premium_mask.sum(), premium_mask.mean() * 100)

    # Step 2: 조건부 회귀 — 각 그룹별 타깃 변환 모델
    y_pred_twostep = np.zeros(len(test))

    for label, mask_name, train_mask_fn in [
        (1, "premium", lambda df: df["낙찰가"].astype(float) >= df["estimate_mid"]),
        (0, "discount", lambda df: df["낙찰가"].astype(float) < df["estimate_mid"]),
    ]:
        train_sub = train[train_mask_fn(train)]
        valid_sub = valid[
            (valid["낙찰가"].astype(float) >= valid["estimate_mid_v"]) if label == 1
            else (valid["낙찰가"].astype(float) < valid["estimate_mid_v"])
        ]

        if len(train_sub) < 100:
            logging.warning("Skipping %s: insufficient data", mask_name)
            continue

        # 타깃 변환 학습
        from visionai.price_engine.models.target_transform import train_transform_model, predict_transform as pt

        logging.info("Step 2: %s regression (train=%d, valid=%d)", mask_name, len(train_sub), len(valid_sub))
        reg = train_transform_model(train_sub, valid_sub, iterations=1000, early_stopping_rounds=100)

        test_mask = premium_mask if label == 1 else discount_mask
        if test_mask.sum() > 0:
            test_sub = test[test_mask]
            y_pred_sub = pt(reg, test_sub)
            y_pred_twostep[test_mask] = y_pred_sub

    # === 비교 ===
    m_unified = compute_metrics(y_true, y_pred_unified)
    m_twostep = compute_metrics(y_true, y_pred_twostep)

    print(f"\n{'='*70}")
    print("Phase 2 실험 ④: Two-Step vs 통합 모델")
    print(f"{'='*70}")
    print(f"{'모델':<20} {'MAPE':>8} {'MdAPE':>8} {'R²':>8} {'±20%':>8}")
    print("-" * 70)
    print(f"{'통합+Calibration':<20} {m_unified.mape:>7.2f}% {m_unified.mdape:>7.2f}% {m_unified.r2:>7.4f} {m_unified.within_20pct:>7.1f}%")
    print(f"{'Two-Step':<20} {m_twostep.mape:>7.2f}% {m_twostep.mdape:>7.2f}% {m_twostep.r2:>7.4f} {m_twostep.within_20pct:>7.1f}%")

    delta = m_twostep.mape - m_unified.mape
    print(f"\nΔ MAPE: {delta:+.2f}%p {'(Two-Step 개선)' if delta < 0 else '(통합 유지)'}")

    # 타입별
    print(f"\n--- 타입별 ---")
    for atype in ["메이저", "프리미엄", "위클리"]:
        mask = test["타입"].values == atype
        mu = compute_metrics(y_true[mask], y_pred_unified[mask])
        mt = compute_metrics(y_true[mask], y_pred_twostep[mask])
        print(f"  {atype:6s}: 통합={mu.mape:6.2f}%  Two-Step={mt.mape:6.2f}%  Δ={mt.mape-mu.mape:+.2f}%p")


if __name__ == "__main__":
    main()
