# T5-E019 Warm OOF extended 최종 설정 재검증

- 날짜: 2026-05-18
- 관련 가설: T5-H22
- 목적: Warm OOF extended 후보가 Huber `max_iter=3000` 설정에서도 성능이 유지되는지 확인

## 실험 방법

- 학습 데이터: `track5_train.csv`
- 평가 데이터: `track5_val_warm.csv`, `track5_test_warm.csv`
- 모델: HuberRegressor
- 설정: `max_iter=3000`
- 피처
  - Warm full_size 피처
  - OOF 방식 작가 가격 통계
  - 확장 작가 통계(q10/q25/q75/q90, min/max/std/span, count bucket)

## 결과

| split | median APE | p95 APE | Within-30 | Within-50 |
|---|---:|---:|---:|---:|
| val_warm | 0.1615 | 0.7368 | 0.6923 | 0.8778 |
| test_warm | 0.1570 | 0.8471 | 0.6947 | 0.8611 |

## 해석

- test 기준으로는 기존 Warm full_size와 비슷하거나 약간 좋은 구간이 있음
- validation 기준에서는 기존 Warm full_size보다 median과 p95가 나빠짐
- `max_iter=3000`에서도 수렴 경고가 남아 기술적 안정성 근거가 약함

## 결론

- Warm 최종 1순위 후보는 기존 `HuberRegressor + warm_full_size` 유지
- OOF extended는 최종 후보 교체가 아니라 보조 연구 후보로 보류
- 이유
  - validation 성능이 더 약함
  - 피처 수가 늘어남
  - 수렴 경고가 남음
