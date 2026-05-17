# T5-E007 생성 조합 피처 검증

- 날짜: 2026-05-18
- 관련 가설: T5-H10
- 상태: 완료
- 목적: 재료·지지체·크기 조합 피처가 E006 full_size 후보보다 성능을 개선하는지 확인

## 1. 확인하려는 것

- 크기 구간 피처가 단순 연속형 크기 피처보다 도움이 되는가
- 재료와 크기를 묶은 조합 피처가 가격 설명력을 높이는가
- 지지체와 크기를 묶은 조합 피처가 오차를 줄이는가
- 대형/재료/3D rule flag가 큰 오차를 줄이는가

## 2. 사용 데이터

- 학습: `data/track5_split/track5_train.csv`
- Warm 검증: `data/track5_split/track5_val_warm.csv`
- Cold 검증: `data/track5_split/track5_val_cold.csv`
- test는 사용하지 않음

## 3. 기준 모델

- Warm:
  - `Ridge`
  - 기준 피처셋: `warm_full_size`
- Cold:
  - `QuantileRegressor`
  - 기준 피처셋: `cold_full_size`

## 4. 생성 피처

- `size_bucket`
- `medium_size_bucket`
- `support_size_bucket`
- `medium_support_bucket`
- `is_large_work`
- `is_very_large_work`
- `is_large_oil`
- `is_large_acrylic`
- `is_3d_large`

## 5. Warm 결과

| 피처셋 | median APE | p95 APE | Within-30 | Within-50 | 해석 |
|---|---:|---:|---:|---:|---|
| warm_full_size | 0.2326 | 0.8465 | 0.6290 | 0.8054 | 기준선 |
| warm_plus_size_bucket | 0.2389 | 0.8695 | 0.6199 | 0.8145 | median/p95 악화 |
| warm_plus_medium_size | 0.2284 | 0.8494 | 0.6244 | 0.8145 | median 개선, p95 소폭 악화 |
| warm_plus_support_size | 0.2320 | 0.8322 | 0.6380 | 0.8054 | p95 개선 |
| warm_plus_rule_flags | 0.2471 | 0.8169 | 0.6244 | 0.8190 | p95 최선, median 악화 |
| warm_all_combo | 0.2355 | 0.8126 | 0.6154 | 0.8145 | p95 최선권, median 악화 |

## 6. Cold 결과

| 피처셋 | median APE | p95 APE | Within-30 | Within-50 | 해석 |
|---|---:|---:|---:|---:|---|
| cold_full_size | 0.3432 | 1.8235 | 0.4538 | 0.6659 | 기준선 |
| cold_plus_size_bucket | 0.3523 | 1.8484 | 0.4390 | 0.6737 | median/p95 악화 |
| cold_plus_medium_size | 0.3520 | 1.8837 | 0.4429 | 0.6753 | median/p95 악화 |
| cold_plus_support_size | 0.3410 | 1.9163 | 0.4413 | 0.6831 | median 개선, p95 악화 |
| cold_plus_rule_flags | 0.3518 | 1.8123 | 0.4468 | 0.6761 | p95 개선, median 악화 |
| cold_all_combo | 0.3364 | 1.9122 | 0.4515 | 0.6761 | median 최선, p95 악화 |

## 7. 해석

- Warm:
  - median 기준으로는 `warm_plus_medium_size`가 근소하게 개선된다.
  - p95 기준으로는 `warm_all_combo` 또는 `warm_plus_rule_flags`가 개선된다.
  - median과 p95를 동시에 안정적으로 개선한 단일 후보는 없다.
- Cold:
  - median 기준으로는 `cold_all_combo`가 가장 좋다.
  - p95 기준으로는 `cold_plus_rule_flags`가 가장 좋다.
  - 단일 후보가 median과 p95를 동시에 개선하지 못했다.

## 8. 결론

- T5-H10은 부분 검증으로 둔다.
- 생성 조합 피처는 일부 개선 신호가 있지만 최종 채택하기에는 아직 불충분하다.
- Warm은 `warm_full_size`를 기준 후보로 유지하고, `warm_plus_medium_size`, `warm_all_combo`를 보조 후보로 둔다.
- Cold는 `cold_full_size`를 기준 후보로 유지하고, `cold_all_combo`, `cold_plus_rule_flags`를 보조 후보로 둔다.
- 다음 단계에서는 후보 피처 조합을 정리한 뒤 모델군 재비교로 넘어간다.

## 9. 산출물

- 실행 스크립트: `scripts/track5/run_t5_e007_combo_feature_validation.py`
- 결과 JSON: `data/track5/results/t5_e007_combo_feature_validation_metrics.json`
- 예측 결과: `data/track5/predictions/t5_e007_combo_feature_validation_predictions.csv`
