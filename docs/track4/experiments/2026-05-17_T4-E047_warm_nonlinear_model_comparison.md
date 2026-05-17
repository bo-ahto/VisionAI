# T4-E047 Warm 비선형 모델 비교

- 날짜: 2026-05-17
- 관련 가설: T4-H36
- 상태: 완료
- 목적: Warm 최종 피처 조합에서 Ridge만 사용한 것이 적절했는지 확인

## 1. 실험 배경

- 기존 Warm 최종 후보는 `Ridge`였다.
- 하지만 Warm에서 비선형 모델을 같은 최종 피처셋으로 비교한 실험이 빠져 있었다.
- 따라서 피처 조합은 고정하고 모델만 바꿔 비교했다.

## 2. 확인하려는 것

- Warm 최종 피처셋에서 비선형 모델이 Ridge보다 성능이 좋은가
- median APE가 좋아지더라도 p95 APE가 나빠지지 않는가
- seed를 바꿔도 결과가 크게 흔들리지 않는가

## 3. 사용 데이터

- 학습 데이터: `data/track4_split/track4_train.csv`
- 검증 데이터: `data/track4_split/track4_val_warm.csv`
- 테스트 데이터: `data/track4_split/track4_test_warm.csv`
- target: `ln_price_krw`
- 해석 가격: `price_krw`

## 4. 사용 피처

- `artist_key`
- `medium_category`
- `support_category`
- `artist_works_log`
- `artist_works_count_train`
- `artist_train_median_log_price`
- `artist_train_mean_log_price`
- `artist_train_iqr_log_price`
- `log_area`
- `aspect_ratio`

## 5. 비교 모델

- `Ridge`
- `HistGradientBoosting`
- `RandomForest`
- `LightGBM`
- `XGBoost`
- `CatBoost`

## 6. 실행 방법

- seed 3개로 반복 실행:
  - `42`
  - `2026`
  - `777`
- 실행 명령:
  - `python3 scripts/track4/run_t4_e047_warm_nonlinear_model_comparison.py`

## 7. 결과 요약

| 모델 | val median APE 평균 | val p95 APE 평균 | test median APE 평균 | test p95 APE 평균 | test median APE 표준편차 |
|---|---:|---:|---:|---:|---:|
| RandomForest | 0.1847 | 0.9084 | 0.2003 | 0.9131 | 0.0049 |
| Ridge | 0.2326 | 1.0538 | 0.2201 | 1.1118 | 0.0000 |
| HistGradientBoosting | 0.2988 | 0.9801 | 0.2417 | 0.9712 | 0.0124 |
| LightGBM | 0.2896 | 0.9816 | 0.2545 | 0.9791 | 0.0047 |
| CatBoost | 0.2465 | 1.1139 | 0.2597 | 1.0285 | 0.0034 |
| XGBoost | 0.2618 | 1.0192 | 0.2846 | 1.0220 | 0.0010 |

## 8. 해석

- RandomForest가 test median APE와 p95 APE 모두에서 Ridge보다 좋았다.
- Ridge test median APE는 `0.2201`이고 RandomForest는 `0.2003`이다.
- Ridge test p95 APE는 `1.1118`이고 RandomForest는 `0.9131`이다.
- 따라서 Warm 최종 후보는 Ridge에서 RandomForest로 교체 검토가 필요하다.
- LightGBM, XGBoost, CatBoost는 이번 피처셋과 설정에서는 Ridge보다 median APE가 불리했다.

## 9. 결론

- Warm 비선형 비교 누락은 보완되었다.
- 현재 결과 기준 Warm 최종 모델 1순위 후보는 `RandomForest`다.
- 단, 최종 artifact 교체 전에는 manifest 검사와 artifact dry-run을 한 번 더 진행해야 한다.

## 10. 산출물

- 실행 스크립트: `scripts/track4/run_t4_e047_warm_nonlinear_model_comparison.py`
- 결과 JSON: `data/track4/results/t4_e047_warm_nonlinear_model_comparison_metrics.json`
- 예측 CSV: `data/track4/predictions/t4_e047_warm_nonlinear_model_comparison_predictions.csv`
