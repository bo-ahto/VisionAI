"""Phase 2 실험 ②: 타깃 변환 — log(price/estimate_mid).

Baseline vs 타깃 변환을 동일 test set에서 비교한다.
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    """타깃 변환 실험을 실행한다."""
    from visionai.price_engine.models.predictor import load_model, predict
    from visionai.price_engine.models.target_transform import (
        predict_transform,
        train_transform_model,
    )
    from visionai.price_engine.validation.bias_check import compute_bias_table
    from visionai.price_engine.validation.calibration import compute_calibration_table
    from visionai.price_engine.validation.confidence_grade import assign_confidence_grade
    from visionai.price_engine.validation.metrics import compute_metrics

    # 데이터 로드
    df = pd.read_parquet(ROOT / "data" / "preprocessed_features.parquet")
    train = df[df["split"] == "train"]
    valid = df[df["split"] == "valid"]
    test = df[df["split"] == "test"].copy()

    y_true = test["낙찰가"].astype(float).values

    # === Baseline (기존 ln(price) 모델) ===
    baseline = load_model(ROOT / "model_test_results" / "baseline_catboost_v1.cbm")
    y_pred_base = predict(baseline, test)
    m_base = compute_metrics(y_true, y_pred_base)

    # === 타깃 변환 모델 학습 ===
    transform_model = train_transform_model(train, valid)
    y_pred_transform = predict_transform(transform_model, test)
    m_transform = compute_metrics(y_true, y_pred_transform)

    # === 비교 ===
    print(f"\n{'='*70}")
    print("Phase 2 실험 ②: 타깃 변환 — log(price/estimate_mid)")
    print(f"{'='*70}")

    print(f"\n{'모델':<20} {'MAPE':>8} {'MdAPE':>8} {'R²':>8} {'±20%':>8} {'±30%':>8}")
    print("-" * 70)
    print(f"{'Baseline (ln P)':<20} {m_base.mape:>7.2f}% {m_base.mdape:>7.2f}% {m_base.r2:>7.4f} {m_base.within_20pct:>7.1f}% {m_base.within_30pct:>7.1f}%")
    print(f"{'Transform (ln P/E)':<20} {m_transform.mape:>7.2f}% {m_transform.mdape:>7.2f}% {m_transform.r2:>7.4f} {m_transform.within_20pct:>7.1f}% {m_transform.within_30pct:>7.1f}%")

    delta_mape = m_transform.mape - m_base.mape
    print(f"\nΔ MAPE: {delta_mape:+.2f}%p {'(개선)' if delta_mape < 0 else '(악화)'}")

    # === 타입별 비교 ===
    print(f"\n--- 타입별 ---")
    for atype in ["메이저", "프리미엄", "위클리"]:
        mask = test["타입"].values == atype
        if mask.sum() == 0:
            continue
        mb = compute_metrics(y_true[mask], y_pred_base[mask])
        mt = compute_metrics(y_true[mask], y_pred_transform[mask])
        delta = mt.mape - mb.mape
        print(f"  {atype:6s}: Base={mb.mape:6.2f}% → Transform={mt.mape:6.2f}% (Δ{delta:+.2f}%p)")

    # === 재변환 편향 비교 ===
    print(f"\n--- 재변환 편향 ---")
    bias_base = compute_bias_table(y_true, y_pred_base)
    bias_transform = compute_bias_table(y_true, y_pred_transform)

    print(f"{'가격대':<12} {'Base ratio':>12} {'Transform ratio':>16}")
    for _, rb in bias_base.iterrows():
        rt = bias_transform[bias_transform["price_tier"] == rb["price_tier"]]
        tr = rt.iloc[0]["median_ratio"] if len(rt) > 0 else float("nan")
        print(f"  {rb['price_tier']:<12} {rb['median_ratio']:>11.4f} {tr:>15.4f}")

    # === Calibration 비교 ===
    print(f"\n--- Calibration ---")
    grades = assign_confidence_grade(test, works_full=df)

    cal_base = compute_calibration_table(y_true, y_pred_base, grades)
    cal_transform = compute_calibration_table(y_true, y_pred_transform, grades)

    for g in ["A", "B", "C", "D"]:
        rb = cal_base[cal_base["grade"] == g]
        rt = cal_transform[cal_transform["grade"] == g]
        if rb.empty:
            continue
        b20 = rb.iloc[0]["within_20pct"]
        t20 = rt.iloc[0]["within_20pct"] if not rt.empty else 0
        print(f"  {g}등급 within-20%: Base={b20:.1f}% → Transform={t20:.1f}%")

    # === 게이트 달성 체크 ===
    print(f"\n--- 게이트 달성 체크 ---")

    # MAPE 타입별
    major_mask = test["타입"].values == "메이저"
    premium_mask = test["타입"].values == "프리미엄"
    m_major = compute_metrics(y_true[major_mask], y_pred_transform[major_mask])
    m_premium = compute_metrics(y_true[premium_mask], y_pred_transform[premium_mask])
    mape_ok = m_transform.mape < 38 and m_major.mape < 19 and m_premium.mape < 30
    print(f"  MAPE < 38% + 타입별: {'✅' if mape_ok else '❌'} (전체={m_transform.mape:.2f}%, 메이저={m_major.mape:.2f}%, 프리미엄={m_premium.mape:.2f}%)")

    # A등급
    a_row = cal_transform[cal_transform["grade"] == "A"]
    a_w20 = a_row.iloc[0]["within_20pct"] if not a_row.empty else 0
    cal_ok = a_w20 >= 65
    print(f"  A등급 within-20% ≥ 65%: {'✅' if cal_ok else '❌'} ({a_w20:.1f}%)")

    # 재변환 편향
    bias_ok = all(r["median_ratio"] >= 0.95 for _, r in bias_transform.iterrows())
    worst = bias_transform.loc[bias_transform["median_ratio"].idxmin()]
    print(f"  재변환 편향 ≥ 0.95: {'✅' if bias_ok else '❌'} (worst={worst['price_tier']} {worst['median_ratio']:.4f})")

    # 모델 저장
    save_path = ROOT / "model_test_results" / "target_transform_v1.cbm"
    transform_model.save_model(str(save_path))
    print(f"\n모델 저장: {save_path}")


if __name__ == "__main__":
    main()
