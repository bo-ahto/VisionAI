# T5-E008 후보 피처 기반 모델군 재비교

- 날짜: 2026-05-18
- 관련 가설: T5-H11
- 상태: 완료
- 목적: 후보 피처셋이 정해진 뒤 Warm / Cold 각각에서 모델군을 다시 비교해 최종 후보를 좁힘

## 1. 확인하려는 것

- Warm 기준 모델 Ridge보다 더 나은 모델이 있는가
- Cold 기준 모델 Quantile보다 더 나은 모델이 있는가
- 조합 피처 후보가 모델군을 바꿨을 때도 유효한가

## 2. 사용 데이터

- 학습: `data/track5_split/track5_train.csv`
- Warm 검증: `data/track5_split/track5_val_warm.csv`
- Cold 검증: `data/track5_split/track5_val_cold.csv`
- test는 사용하지 않음

## 3. 후보 피처셋

- Warm:
  - `warm_full_size`
  - `warm_all_combo`
- Cold:
  - `cold_full_size`
  - `cold_all_combo`

## 4. 비교 모델

- `ridge`
- `huber`
- `quantile_median`
- `hist_gradient_boosting`
- `random_forest`
- `lightgbm`

## 5. Warm 결과 요약

| 피처셋 | 최선 모델 | median APE | p95 APE | Within-30 | Within-50 |
|---|---|---:|---:|---:|---:|
| warm_full_size | huber | 0.1506 | 0.6999 | 0.7014 | 0.8914 |
| warm_all_combo | huber | 0.1564 | 0.6634 | 0.7330 | 0.9005 |

## 6. Cold 결과 요약

| 피처셋 | 최선 모델 | median APE | p95 APE | Within-30 | Within-50 |
|---|---|---:|---:|---:|---:|
| cold_full_size | quantile_median | 0.3432 | 1.8235 | 0.4538 | 0.6659 |
| cold_all_combo | quantile_median | 0.3364 | 1.9122 | 0.4515 | 0.6761 |

## 7. 해석

- Warm:
  - Ridge보다 Huber가 크게 개선됐다.
  - median APE 기준은 `warm_full_size + huber`가 최선이다.
  - p95 / Within 기준은 `warm_all_combo + huber`가 조금 더 좋다.
  - 둘 다 후보로 유지하되, 최종 test에서는 두 후보를 함께 확인해야 한다.
- Cold:
  - QuantileRegressor가 여전히 가장 균형이 좋다.
  - `cold_all_combo`는 median APE를 낮추지만 p95 APE를 악화시킨다.
  - 최종 후보는 `cold_full_size + quantile_median`을 우선으로 둔다.

## 8. 결론

- T5-H11은 validation 기준 검증 완료로 본다.
- Warm 최종 후보:
  - 1순위: `warm_full_size + Huber`
  - 보조 후보: `warm_all_combo + Huber`
- Cold 최종 후보:
  - 1순위: `cold_full_size + QuantileRegressor`
  - 보조 후보: `cold_all_combo + QuantileRegressor`
- 다음 단계는 test를 열기 전, 후보 피처/모델 조합을 최종 확인 목록으로 고정하는 것이다.

## 9. 산출물

- 실행 스크립트: `scripts/track5/run_t5_e008_candidate_model_comparison.py`
- 결과 JSON: `data/track5/results/t5_e008_candidate_model_comparison_metrics.json`
- 예측 결과: `data/track5/predictions/t5_e008_candidate_model_comparison_predictions.csv`
