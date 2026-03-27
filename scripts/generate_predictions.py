"""작가별/호수별 예측 JSON 생성 스크립트.

기획서 7.2, 개발 계획서 Sprint 1.5
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent

# 호수 → cm 매핑 (F형 기준)
HO_TO_CM: dict[str, tuple[float, float]] = {
    "10호": (53.0, 45.5),
    "20호": (72.7, 60.6),
    "30호": (90.9, 72.7),
    "50호": (116.8, 90.9),
    "100호": (162.1, 130.3),
}


def main() -> None:
    """정적 predictions.json을 생성한다."""
    from visionai.price_engine.models.predictor import load_model, predict
    from visionai.price_engine.validation.confidence_grade import assign_confidence_grade
    from visionai.price_engine.validation.metrics import compute_metrics

    # 데이터 + 모델 로드
    df = pd.read_parquet(ROOT / "data" / "preprocessed_features.parquet")
    model = load_model(ROOT / "model_test_results" / "baseline_catboost_v1.cbm")

    # 전체 예측 (train+valid+test)
    y_pred = predict(model, df)
    y_true = df["낙찰가"].astype(float).values
    grades = assign_confidence_grade(df, works_full=df)

    # 작가별 집계
    df["predicted_price"] = y_pred
    df["confidence_grade"] = grades.values

    # 충분한 데이터가 있는 작가만 (sold >= 3)
    artist_counts = df.groupby("artist_clean").size()
    valid_artists = artist_counts[artist_counts >= 3].index

    artists_data: dict[str, dict] = {}
    for artist in valid_artists:
        adf = df[df["artist_clean"] == artist]
        if artist in ("__UNKNOWN__", "__NEW_ARTIST__"):
            continue

        # 작가 기본 정보
        avg_price = int(adf["낙찰가"].mean())
        total_works = len(adf)

        # 호수별 예측 (추정가 중앙값 기반 근사)
        predictions_by_size: dict[str, dict] = {}
        for ho_name, (w, h) in HO_TO_CM.items():
            # 해당 작가의 비슷한 크기 작품 찾기 (면적 ±50%)
            target_area = w * h
            area = adf["surface_area"].fillna(0)
            size_mask = (area > target_area * 0.5) & (area < target_area * 1.5)
            similar = adf[size_mask]

            if len(similar) < 2:
                continue

            pred_median = int(np.median(similar["predicted_price"]))
            pred_low = int(np.percentile(similar["predicted_price"], 20))
            pred_high = int(np.percentile(similar["predicted_price"], 80))

            # 신뢰도: 해당 slice에서 가장 많은 grade
            grade_mode = similar["confidence_grade"].mode()
            confidence = grade_mode.iloc[0] if len(grade_mode) > 0 else "D"

            is_recommended = confidence in ("A", "B") and len(similar) >= 5
            option_b_blocked = confidence == "D" or len(similar) < 3

            predictions_by_size[ho_name] = {
                "predicted_price": pred_median,
                "price_range": [pred_low, pred_high],
                "confidence": confidence,
                "basis_count": len(similar),
                "prediction_method": "historical_aggregate",
                "is_recommended": is_recommended,
                "option_b_blocked": option_b_blocked,
            }

        if not predictions_by_size:
            continue

        # 작가 tier
        if avg_price >= 100_000_000:
            tier = "최상"
        elif avg_price >= 30_000_000:
            tier = "상위"
        elif avg_price >= 5_000_000:
            tier = "중상"
        elif avg_price >= 1_000_000:
            tier = "중하"
        else:
            tier = "하위"

        artists_data[artist] = {
            "artist_tier": tier,
            "total_works": total_works,
            "avg_price": avg_price,
            "predictions_by_size": predictions_by_size,
        }

    # 전체 메트릭
    test_mask = df["split"] == "test"
    test_metrics = compute_metrics(y_true[test_mask], y_pred[test_mask])

    output = {
        "generated_at": pd.Timestamp.now().isoformat(),
        "model_version": "catboost_baseline_v1",
        "model_metrics": {
            "overall_mape": test_metrics.mape,
            "overall_mdape": test_metrics.mdape,
        },
        "artists": artists_data,
        "confidence_guide": {
            "A": "예측 오차 ±20% 이내 기대 (고가 구간, 거래 풍부)",
            "B": "예측 오차 ±30% 이내 기대",
            "C": "참고용 (거래 이력 희소)",
            "D": "근사 추정 (데이터 부족, 추정가 범위만 참고)",
        },
        "low_price_warning": "100만 원 미만 작품은 과대추정 경향이 있어 추정가 최고값으로 캡 처리됨",
    }

    # 저장
    out_path = ROOT / "frontend" / "data" / "predictions.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    logger.info("Generated predictions.json: %d artists", len(artists_data))
    logger.info("Output: %s", out_path)

    # 요약
    print(f"\n{'='*50}")
    print("predictions.json 생성 완료")
    print(f"{'='*50}")
    print(f"  작가 수: {len(artists_data)}")
    print(f"  호수별 예측 있는 작가: {sum(1 for a in artists_data.values() if a['predictions_by_size'])}")
    tier_counts = pd.Series([a["artist_tier"] for a in artists_data.values()]).value_counts()
    print(f"  Tier 분포: {tier_counts.to_dict()}")


if __name__ == "__main__":
    main()
