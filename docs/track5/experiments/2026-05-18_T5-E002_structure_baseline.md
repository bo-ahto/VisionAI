# T5-E002 구조-only baseline

- 날짜: 2026-05-18
- 관련 가설: T5-H2
- 상태: 완료
- 목적: Track5 새 split에서 작가 정보 없이 작품 구조 정보만으로 기본 예측이 가능한지 확인

## 1. 확인하려는 것

- 구조 피처만으로 단순 중앙값 baseline보다 나은 성능이 나오는가
- Warm / Cold를 분리해서 봤을 때 기본 예측 가능성이 있는가
- 다음 단계에서 기준 모델로 삼을 수 있는 후보가 있는가

## 2. 사용 데이터

- 학습: `data/track5_split/track5_train.csv`
- Warm 검증: `data/track5_split/track5_val_warm.csv`
- Cold 검증: `data/track5_split/track5_val_cold.csv`
- test는 사용하지 않음

## 3. 사용 피처

- `medium_category`
- `support_category`
- `log_area`
- `aspect_ratio`
- `has_depth`
- `is_3d_candidate`

## 4. 비교 모델

- `dummy_median`
- `ridge`
- `huber`

## 5. 결과

| 모델 | Warm median APE | Warm p95 APE | Cold median APE | Cold p95 APE |
|---|---:|---:|---:|---:|
| dummy_median | 0.7506 | 6.7895 | 0.6973 | 4.7813 |
| ridge | 0.4707 | 3.3077 | 0.4115 | 2.1254 |
| huber | 0.4662 | 2.9250 | 0.3718 | 1.8598 |

## 6. 해석

- 구조-only 피처만 사용해도 단순 중앙값보다 Warm / Cold 모두 개선됐다.
- Warm은 작가 정보가 없으면 median APE가 `0.4662` 수준이라 한계가 크다.
- Cold는 구조-only Huber가 median APE `0.3718`로 기본 기준선 역할을 할 수 있다.
- Huber는 Warm / Cold 모두에서 p95 APE가 Ridge보다 낮아 기준 모델 후보로 적합하다.

## 7. 결론

- T5-H2는 검증 완료로 본다.
- 구조-only baseline 기준 모델은 `HuberRegressor`로 둔다.
- 다음 단계에서는 Warm에서 작가 피처를 추가했을 때 개선되는지 확인한다.

## 8. 산출물

- 실행 스크립트: `scripts/track5/run_t5_e002_structure_baseline.py`
- 결과 JSON: `data/track5/results/t5_e002_structure_baseline_metrics.json`
- 예측 결과: `data/track5/predictions/t5_e002_structure_baseline_predictions.csv`
