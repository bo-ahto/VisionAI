# T5-E006 기준 모델 기반 피처 ablation

- 날짜: 2026-05-18
- 관련 가설: T5-H9
- 상태: 완료
- 목적: 기준 Warm/Cold 모델에서 크기, 지지체, 3D 관련 피처를 추가·제거했을 때 성능이 개선되는지 확인

## 1. 확인하려는 것

- Warm과 Cold에서 같은 피처 조합이 같은 효과를 내는가
- `support_category`는 유지할 가치가 있는가
- `width_cm`, `height_cm`, 3D flag를 추가하면 성능이 개선되는가
- `aspect_ratio`는 필수 피처인가

## 2. 사용 데이터

- 학습: `data/track5_split/track5_train.csv`
- Warm 검증: `data/track5_split/track5_val_warm.csv`
- Cold 검증: `data/track5_split/track5_val_cold.csv`
- test는 사용하지 않음

## 3. 기준 모델

- Warm:
  - `Ridge`
  - 작가 key + 작가 이력 + train 기준 작가 가격 통계 포함
- Cold:
  - `QuantileRegressor`
  - 작가 피처 제외

## 4. Warm 결과

| 피처셋 | median APE | p95 APE | Within-30 | Within-50 | 해석 |
|---|---:|---:|---:|---:|---|
| warm_baseline | 0.2333 | 0.9060 | 0.6063 | 0.7873 | 기준선 |
| warm_no_support | 0.2303 | 0.9093 | 0.6471 | 0.7964 | median과 Within 개선, p95 소폭 악화 |
| warm_full_size | 0.2326 | 0.8465 | 0.6290 | 0.8054 | p95와 Within-50 최선 |
| warm_area_only | 0.2298 | 0.9198 | 0.6154 | 0.8009 | median 최선, p95 악화 |

## 5. Cold 결과

| 피처셋 | median APE | p95 APE | Within-30 | Within-50 | 해석 |
|---|---:|---:|---:|---:|---|
| cold_baseline | 0.3564 | 1.8218 | 0.4358 | 0.6448 | 기준선 |
| cold_no_support | 0.3489 | 1.9276 | 0.4429 | 0.6549 | median 개선, p95 악화 |
| cold_full_size | 0.3432 | 1.8235 | 0.4538 | 0.6659 | median/Within 개선, p95 거의 유지 |
| cold_area_only | 0.3731 | 1.8185 | 0.4092 | 0.6440 | p95는 근소 개선, median 악화 |
| cold_no_3d_flags | 0.3741 | 1.7908 | 0.4155 | 0.6463 | p95 최선, median 악화 |

## 6. 해석

- Warm:
  - median만 보면 `warm_area_only`가 가장 낮다.
  - p95와 Within-50까지 보면 `warm_full_size`가 더 안정적이다.
  - 최종 후보는 `warm_full_size`를 우선 후보로 두고, `warm_no_support`는 보조 후보로 남긴다.
- Cold:
  - `cold_full_size`가 median APE와 Within 지표를 개선하면서 p95를 거의 유지했다.
  - `cold_no_3d_flags`는 p95는 낮지만 median이 악화되어 전체 후보로는 약하다.
  - Cold 후보 피처셋은 `cold_full_size`를 우선 후보로 둔다.

## 7. 결론

- T5-H9는 부분 검증으로 둔다.
- Warm과 Cold에서 피처 효과가 다르므로 피처셋을 분리 관리해야 한다.
- 다음 단계에서는 생성 조합 피처를 추가해 `warm_full_size`, `cold_full_size` 기준보다 개선되는지 확인한다.

## 8. 산출물

- 실행 스크립트: `scripts/track5/run_t5_e006_feature_ablation.py`
- 결과 JSON: `data/track5/results/t5_e006_feature_ablation_metrics.json`
- 예측 결과: `data/track5/predictions/t5_e006_feature_ablation_predictions.csv`
