"""Reliability Model 실험.

규칙 기반 vs 데이터 기반 신뢰도 등급을 비교한다.
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    """Reliability 실험."""
    from visionai.price_engine.models.predictor import load_model
    from visionai.price_engine.models.segment_calibrator import fit_calibration, apply_calibration
    from visionai.price_engine.models.target_transform import predict_transform
    from visionai.price_engine.reliability.reliability_features import extract_reliability_features
    from visionai.price_engine.reliability.reliability_model import ReliabilityModel
    from visionai.price_engine.validation.calibration import compute_calibration_table
    from visionai.price_engine.validation.confidence_grade import assign_confidence_grade
    df = pd.read_parquet(ROOT / "data" / "preprocessed_features.parquet")
    model = load_model(ROOT / "model_test_results" / "target_transform_v1.cbm")

    valid = df[df["split"] == "valid"].copy()
    test = df[df["split"] == "test"].copy()

    # Calibration
    y_pred_v = predict_transform(model, valid)
    y_true_v = valid["낙찰가"].astype(float).values
    est_v = ((valid["추정가(최저)"].astype(float) + valid["추정가(최고)"].astype(float)) / 2).values
    factors = fit_calibration(y_true_v, y_pred_v, valid["타입"].values, est_v)

    y_pred_v_cal = apply_calibration(y_pred_v, valid["타입"].values, est_v, factors, blend_weight=0.0)
    y_pred_t_raw = predict_transform(model, test)
    est_t = ((test["추정가(최저)"].astype(float) + test["추정가(최고)"].astype(float)) / 2).values
    y_pred_t = apply_calibration(y_pred_t_raw, test["타입"].values, est_t, factors, blend_weight=0.0)
    y_true_t = test["낙찰가"].astype(float).values

    # === Reliability Model 학습 (validation set) ===
    meta_valid = extract_reliability_features(valid, works_full=df)
    reliability = ReliabilityModel(threshold=0.2)
    reliability.fit(meta_valid, y_true_v, y_pred_v_cal)

    # === Test set 평가 (holdout AUC/Brier) ===
    meta_test = extract_reliability_features(test, works_full=df)
    eval_result = reliability.evaluate(meta_test, y_true_t, y_pred_t)
    print(f"\nTest set AUC: {eval_result['auc']:.4f}, Brier: {eval_result['brier']:.4f}")

    reliability_grades = reliability.assign_grades(meta_test)

    # === 규칙 기반 등급 (기존) ===
    rule_grades = assign_confidence_grade(test, works_full=df)

    # === 비교 ===
    print(f"\n{'='*70}")
    print("Reliability Model vs 규칙 기반 등급 비교")
    print(f"{'='*70}")

    print(f"\n--- 규칙 기반 ---")
    cal_rule = compute_calibration_table(y_true_t, y_pred_t, rule_grades)
    for _, r in cal_rule.iterrows():
        print(f"  {r['grade']}등급: ±20%={r['within_20pct']:5.1f}%  MAPE={r['mape']:6.2f}%  N={r['n']}")

    print(f"\n--- Reliability Model ---")
    cal_rel = compute_calibration_table(y_true_t, y_pred_t, reliability_grades)
    for _, r in cal_rel.iterrows():
        print(f"  {r['grade']}등급: ±20%={r['within_20pct']:5.1f}%  MAPE={r['mape']:6.2f}%  N={r['n']}")

    # A등급 비교
    rule_a = cal_rule[cal_rule["grade"] == "A"]
    rel_a = cal_rel[cal_rel["grade"] == "A"]

    print(f"\n--- A등급 비교 ---")
    if not rule_a.empty:
        print(f"  규칙: ±20%={rule_a.iloc[0]['within_20pct']:.1f}%  N={rule_a.iloc[0]['n']}")
    if not rel_a.empty:
        print(f"  모델: ±20%={rel_a.iloc[0]['within_20pct']:.1f}%  N={rel_a.iloc[0]['n']}")

    # 등급 분포
    print(f"\n--- 등급 분포 ---")
    print(f"  규칙: {rule_grades.value_counts().sort_index().to_dict()}")
    print(f"  모델: {reliability_grades.value_counts().sort_index().to_dict()}")

    # Pr(APE ≤ 0.2) 분포
    proba = reliability.predict_proba(meta_test)
    print(f"\n--- Pr(APE ≤ 20%) 분포 ---")
    print(f"  mean={proba.mean():.3f}  median={np.median(proba):.3f}  min={proba.min():.3f}  max={proba.max():.3f}")


if __name__ == "__main__":
    main()
