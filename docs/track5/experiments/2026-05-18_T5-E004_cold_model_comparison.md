# T5-E004 Cold 모델군 비교

- 날짜: 2026-05-18
- 관련 가설: T5-H4
- 상태: 완료
- 목적: Cold 상황에서 robust 선형 계열이 복잡한 트리 모델보다 안정적인지 확인

## 1. 확인하려는 것

- 신규 작가 상황에서 어떤 모델군이 가장 안정적인가
- 구조-only 피처 기준으로 Quantile / Huber / Ridge / 트리 모델 중 무엇이 유리한가
- Cold 기준 모델을 무엇으로 둘지 결정할 수 있는가

## 2. 사용 데이터

- 학습: `data/track5_split/track5_train.csv`
- 검증: `data/track5_split/track5_val_cold.csv`
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
- `quantile_median`
- `hist_gradient_boosting`
- `random_forest`
- `lightgbm`
- `xgboost`
- `catboost`

## 5. 결과

| 모델 | 계열 | Cold median APE | Cold p95 APE | Within-30 | Within-50 |
|---|---|---:|---:|---:|---:|
| dummy_median | baseline | 0.6973 | 4.7813 | 0.2081 | 0.3662 |
| ridge | linear | 0.4115 | 2.1254 | 0.3662 | 0.5900 |
| huber | robust_linear | 0.3718 | 1.8598 | 0.4233 | 0.6401 |
| quantile_median | robust_linear | 0.3564 | 1.8218 | 0.4358 | 0.6448 |
| hist_gradient_boosting | tree | 0.3973 | 2.5671 | 0.3936 | 0.5994 |
| random_forest | tree | 0.3645 | 2.4594 | 0.4257 | 0.6291 |
| lightgbm | tree | 0.3917 | 2.9007 | 0.3991 | 0.6095 |
| xgboost | tree | 0.3849 | 2.5097 | 0.3850 | 0.5884 |
| catboost | tree | 0.4334 | 2.2184 | 0.3897 | 0.5751 |

## 6. 해석

- median APE 기준 최선은 `quantile_median`이다.
- p95 APE 기준도 `quantile_median`이 가장 낮다.
- 트리 모델은 일부 median APE가 근접하지만 p95 APE가 더 높아 큰 오차 위험이 크다.
- Cold는 현재 피처셋 기준으로 robust 선형 계열이 더 안정적이다.

## 7. 결론

- T5-H4는 validation 기준 검증 완료로 본다.
- Cold 기준 모델 후보는 `QuantileRegressor`로 둔다.
- 다음 단계에서는 기준 모델을 고정하고 피처 추가/제거/생성 실험으로 넘어간다.

## 8. 산출물

- 실행 스크립트: `scripts/track5/run_t5_e004_cold_model_comparison.py`
- 결과 JSON: `data/track5/results/t5_e004_cold_model_comparison_metrics.json`
- 예측 결과: `data/track5/predictions/t5_e004_cold_model_comparison_predictions.csv`
