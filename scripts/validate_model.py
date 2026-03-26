"""Sprint 1 검증 일괄 실행 스크립트.

Baseline 재현 + 재변환 편향 + Calibration + 세그먼트별 MAPE.
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    """Sprint 1 검증을 실행한다."""
    from visionai.price_engine.models.predictor import load_model, predict
    from visionai.price_engine.validation.bias_check import compute_bias_table
    from visionai.price_engine.validation.calibration import compute_calibration_table
    from visionai.price_engine.validation.confidence_grade import assign_confidence_grade
    from visionai.price_engine.validation.metrics import compute_metrics

    # 데이터 로드
    logger.info("Loading preprocessed features...")
    df = pd.read_parquet(ROOT / "data" / "preprocessed_features.parquet")

    # 모델 로드
    logger.info("Loading baseline model...")
    model = load_model(ROOT / "model_test_results" / "baseline_catboost_v1.cbm")

    # 0. Data manifest
    print(f"\n{'='*60}")
    print("0. Data Manifest")
    print(f"{'='*60}")
    print(f"  Total rows:    {len(df):,}")
    print(f"  Split 분포:    {df['split'].value_counts().to_dict()}")
    for atype in ["메이저", "프리미엄", "위클리"]:
        n = len(df[(df["split"] == "test") & (df["타입"] == atype)])
        print(f"  Test {atype}: {n}")
    baseline_ref = {"메이저": 1025, "프리미엄": 1273, "위클리": 4284, "전체": 6582}
    print(f"  Baseline 참조 N: {baseline_ref}")
    test_n = len(df[df["split"] == "test"])
    if test_n != baseline_ref["전체"]:
        print(f"  ⚠️ Test N 불일치: {test_n} vs {baseline_ref['전체']}")
        print(f"     → test set이 다르므로 MAPE 직접 비교는 부적절")

    # Test set만 사용
    test = df[df["split"] == "test"].copy()
    logger.info("Test set: %d rows", len(test))

    # 예측
    y_pred = predict(model, test)
    y_true = test["낙찰가"].astype(float).values

    # 1. 전체 MAPE
    overall = compute_metrics(y_true, y_pred)
    print(f"\n{'='*60}")
    print("1. Baseline 검증")
    print(f"{'='*60}")
    print(f"  MAPE:      {overall.mape}%")
    print(f"  MdAPE:     {overall.mdape}%")
    print(f"  R²:        {overall.r2}")
    print(f"  Within±20%: {overall.within_20pct}%")
    print(f"  Within±30%: {overall.within_30pct}%")
    print(f"  N:         {overall.n}")

    # 가중평균 정합성 체크
    type_mapes = {}
    type_ns = {}
    for atype in ["메이저", "프리미엄", "위클리"]:
        mask = test["타입"].values == atype
        if mask.sum() > 0:
            m = compute_metrics(y_true[mask], y_pred[mask])
            type_mapes[atype] = m.mape
            type_ns[atype] = m.n
    if type_ns:
        weighted_mape = sum(type_mapes[k] * type_ns[k] for k in type_ns) / sum(type_ns.values())
        print(f"  가중평균 MAPE: {weighted_mape:.2f}% (전체와 차이: {abs(overall.mape - weighted_mape):.2f}%p)")

    # 2. 타입별 MAPE
    print(f"\n{'='*60}")
    print("2. 타입별 성능")
    print(f"{'='*60}")
    for atype in ["메이저", "프리미엄", "위클리"]:
        mask = test["타입"].values == atype
        if mask.sum() == 0:
            continue
        m = compute_metrics(y_true[mask], y_pred[mask])
        print(f"  {atype:6s}: MAPE={m.mape:6.2f}%  MdAPE={m.mdape:5.2f}%  R²={m.r2:.4f}  ±20%={m.within_20pct}%  N={m.n}")

    # 3. 가격대별 MAPE
    print(f"\n{'='*60}")
    print("3. 가격대별 성능")
    print(f"{'='*60}")
    tiers = pd.cut(
        y_true,
        bins=[0, 1_000_000, 5_000_000, 30_000_000, 100_000_000, np.inf],
        labels=["<100만", "100만~500만", "500만~3000만", "3000만~1억", "1억+"],
    )
    for tier in ["<100만", "100만~500만", "500만~3000만", "3000만~1억", "1억+"]:
        mask = tiers == tier
        if mask.sum() == 0:
            continue
        m = compute_metrics(y_true[mask], y_pred[mask])
        print(f"  {tier:12s}: MAPE={m.mape:6.2f}%  ±20%={m.within_20pct}%  N={m.n}")

    # 4. 재변환 편향
    print(f"\n{'='*60}")
    print("4. 재변환 편향 검증")
    print(f"{'='*60}")
    bias = compute_bias_table(y_true, y_pred)
    for _, row in bias.iterrows():
        print(f"  {row['price_tier']:12s}: median(P̂/P)={row['median_ratio']:.4f}  → {row['verdict']}  (N={row['n']})")

    # 5. Calibration
    print(f"\n{'='*60}")
    print("5. Calibration 테이블")
    print(f"{'='*60}")
    grades = assign_confidence_grade(test, works_full=df)
    cal = compute_calibration_table(y_true, y_pred, grades)
    for _, row in cal.iterrows():
        print(f"  {row['grade']}등급: ±20%={row['within_20pct']:5.1f}%  ±30%={row['within_30pct']:5.1f}%  MAPE={row['mape']:6.2f}%  N={row['n']}")

    a_row = cal[cal["grade"] == "A"]
    if not a_row.empty:
        a_w20 = a_row.iloc[0]["within_20pct"]
        cal_ok = a_w20 >= 65.0
        print(f"\n  A등급 within-20%: {a_w20}% (게이트 기준: ≥65%)")
        print(f"  {'✅' if cal_ok else '❌'} Calibration: {'Pass' if cal_ok else 'Fail'}")

    print(f"\n{'='*60}")
    print("Sprint 1 검증 완료")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
