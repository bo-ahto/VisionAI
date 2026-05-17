# T5-E010 최종 후보 test 확인

- 날짜: 2026-05-18
- 관련 가설: T5-H13
- 목적: validation에서 고정한 Warm / Cold 최종 후보가 test에서도 유지되는지 확인
- 원칙: test 결과를 본 뒤 새 후보를 추가하지 않음

## 1. 실험 배경

- T5-E009에서 test 전에 최종 확인 후보를 고정함
- Warm 후보
  - 1순위: HuberRegressor + `warm_full_size`
  - 보조: HuberRegressor + `warm_all_combo`
- Cold 후보
  - 1순위: QuantileRegressor + `cold_full_size`
  - 보조: QuantileRegressor + `cold_all_combo`
- 이 실험은 위 후보만 test split에 적용해 최종 확인함

## 2. 사용 데이터

- 학습: `data/track5_split/track5_train.csv`
- Warm test: `data/track5_split/track5_test_warm.csv`
- Cold test: `data/track5_split/track5_test_cold.csv`
- 결과: `data/track5/results/t5_e010_final_candidate_test_metrics.json`
- 예측값: `data/track5/predictions/t5_e010_final_candidate_test_predictions.csv`

## 3. 사용 모델과 피처

- Warm 1순위 후보
  - 모델: HuberRegressor
  - 피처: 작가 key, 작가 학습 이력, train 기준 작가 가격 통계, 재료, 지지체, 크기, 3D 여부
- Warm 보조 후보
  - 모델: HuberRegressor
  - 피처: Warm 1순위 후보 + 크기/재료/지지체 조합 피처
- Cold 1순위 후보
  - 모델: QuantileRegressor
  - 피처: 재료, 지지체, 크기, 3D 여부
- Cold 보조 후보
  - 모델: QuantileRegressor
  - 피처: Cold 1순위 후보 + 크기/재료/지지체 조합 피처

## 4. 결과

| 후보 | 데이터 | median APE | p95 APE | MAPE | RMSE(log) | Within-30 | Within-50 |
|---|---|---:|---:|---:|---:|---:|---:|
| Warm 1순위: Huber + full_size | test_warm | 0.1585 | 0.8738 | 0.3737 | 0.4226 | 0.6908 | 0.8552 |
| Warm 보조: Huber + all_combo | test_warm | 0.1566 | 0.8474 | 0.3859 | 0.4329 | 0.6928 | 0.8474 |
| Cold 1순위: Quantile + full_size | test_cold | 0.3918 | 2.0152 | 1.1221 | 0.7520 | 0.3930 | 0.5746 |
| Cold 보조: Quantile + all_combo | test_cold | 0.4221 | 2.0214 | 0.7242 | 0.7361 | 0.3940 | 0.5832 |

## 5. 해석

- Warm
  - validation에서 선정한 Huber 계열 후보가 test에서도 유지됨
  - `all_combo`는 median APE와 p95 APE가 약간 더 낮지만 MAPE와 Within-50은 `full_size`보다 약함
  - 차이가 크지 않으므로 운영 후보는 단순한 `full_size`를 1순위로 두고, `all_combo`는 보조 후보로 유지하는 것이 안전함
- Cold
  - `full_size`는 `all_combo`보다 median APE가 낮아 1순위 후보로 유지됨
  - 다만 test 기준 median APE `0.3918`, p95 APE `2.0152`로 오차 폭이 큼
  - Cold는 단일 가격만 제공하기에는 위험 구간 식별과 가격 범위 정책이 필요함
- 주의
  - HuberRegressor에서 수렴 경고가 발생함
  - 다음 단계에서 스케일링 또는 반복 횟수 증가 재검증을 별도 실험으로 확인할 필요가 있음

## 6. 결론

- Warm 최종 후보
  - 1순위: HuberRegressor + `warm_full_size`
  - 보조: HuberRegressor + `warm_all_combo`
- Cold 최종 후보
  - 1순위: QuantileRegressor + `cold_full_size`
  - 보조: QuantileRegressor + `cold_all_combo`
- Track5는 순서도 기준으로 `후보 피처 기반 최종 모델 비교`까지 완료됨
- 다음 단계는 `필요하면 피처 조정` 또는 `가격 범위/신뢰도 정책 검증`으로 진행

## 7. 다음 작업

- T5-E011: Warm Huber 수렴 경고 재검증
- T5-E012: Cold 위험 구간 분리와 가격 범위 정책 검증
- T5-E013: 최종 운영 후보 artifact 생성 전 재현성 점검
