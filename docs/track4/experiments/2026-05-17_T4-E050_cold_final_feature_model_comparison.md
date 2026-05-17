# T4-E050 Cold 최종 피처셋 모델 재비교

- 날짜: 2026-05-17
- 관련 가설: T4-H37
- 상태: 완료
- 목적: Cold 최종 full-size 피처셋에서도 기존 Quantile 후보가 적절한지 재확인

## 1. 실험 배경

- T4-E025에서는 Cold 모델군을 비교했지만, 당시 피처셋은 최종 full-size 피처셋이 아니었다.
- 이후 Cold 최종 후보는 `medium_category`, `width_cm`, `height_cm`, `log_area`, `aspect_ratio`, `has_depth`, `is_3d_candidate`로 정리되었다.
- 따라서 최종 피처셋 기준으로 모델군을 다시 비교했다.

## 2. 사용 데이터

- 학습 데이터: `data/track4_split/track4_train.csv`
- 검증 데이터: `data/track4_split/track4_val_cold.csv`
- 테스트 데이터: `data/track4_split/track4_test_cold.csv`

## 3. 사용 피처

- `medium_category`
- `width_cm`
- `height_cm`
- `log_area`
- `aspect_ratio`
- `has_depth`
- `is_3d_candidate`

## 4. 비교 모델

- `Quantile`
- `Huber`
- `Ridge`
- `HistGradientBoosting`
- `RandomForest`
- `LightGBM`
- `XGBoost`
- `CatBoost`

## 5. 실행 방법

- 실행 명령:
  - `python3 scripts/track4/run_t4_e050_cold_final_feature_model_comparison.py`

## 6. 결과

| 모델 | 유형 | val median APE | val p95 APE | test median APE | test p95 APE |
|---|---|---:|---:|---:|---:|
| Quantile | robust linear | 0.3349 | 1.3041 | 0.4199 | 2.7609 |
| HistGradientBoosting | tree | 0.3843 | 1.5485 | 0.4260 | 2.5872 |
| Huber | robust linear | 0.3425 | 1.2828 | 0.4290 | 2.8941 |
| RandomForest | tree | 0.4063 | 1.8954 | 0.4371 | 2.1781 |
| LightGBM | tree | 0.3887 | 1.6501 | 0.4424 | 2.7992 |
| XGBoost | tree | 0.3839 | 1.4441 | 0.4562 | 2.9688 |
| CatBoost | tree | 0.3947 | 1.5018 | 0.4591 | 2.9611 |
| Ridge | linear | 0.3961 | 1.6260 | 0.4741 | 3.3588 |

## 7. 해석

- test median APE 기준으로는 Quantile이 가장 좋다.
- 일부 트리 모델은 p95 APE가 Quantile보다 낮은 경우가 있지만, median APE가 더 나쁘다.
- Cold는 대표 오차와 큰 오차를 동시에 개선하는 후보가 아직 없다.
- 기존 Cold Quantile 최종 후보는 유지하는 것이 적절하다.

## 8. 결론

- Cold 최종 피처셋 기준 모델 재비교 누락은 보완되었다.
- Cold 최종 모델은 기존 `Quantile` 후보를 유지한다.
- Cold의 주요 한계는 모델 종류보다 입력 정보 부족과 위험 구간 분리에 있다.

## 9. 산출물

- 실행 스크립트: `scripts/track4/run_t4_e050_cold_final_feature_model_comparison.py`
- 결과 JSON: `data/track4/results/t4_e050_cold_final_feature_model_comparison_metrics.json`
- 예측 CSV: `data/track4/predictions/t4_e050_cold_final_feature_model_comparison_predictions.csv`
