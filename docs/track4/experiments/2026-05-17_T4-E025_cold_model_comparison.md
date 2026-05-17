# T4-E025 Cold robust 모델 비교

- 실험 ID: `T4-E025`
- 연결 가설: `T4-H4`
- 날짜: 2026-05-17
- 상태: 완료

## 1. 실험 목적

- Cold 상황에서 어떤 모델군이 가장 안정적인지 확인함
- 작가 정보 없이 동일한 구조-only 피처만 사용함
- robust 선형 계열과 트리 계열을 같은 데이터와 같은 피처로 비교함

## 2. 확인하려는 질문

- Cold에서는 robust 선형 계열이 트리 모델보다 안정적인가
- median APE 기준 최선 모델은 무엇인가
- 큰 오차 위험을 보는 p95 APE 기준 최선 모델은 무엇인가

## 3. 사용 데이터

- 학습 데이터: `data/track4_split/track4_train.csv`
- Cold 평가 데이터: `data/track4_split/track4_val_cold.csv`
- Warm 평가 데이터: 사용하지 않음
- calibration 데이터: 사용하지 않음

| 구분 | rows | 작가 수 | 가격 중앙값 | 3D 후보 수 | support unknown 수 |
|---|---:|---:|---:|---:|---:|
| train | 28,905 | 1,834 | 3,091,200 | 485 | 2,321 |
| val_cold | 1,814 | 108 | 2,652,020 | 70 | 206 |

## 4. 사용 피처

- `medium_category`
- `support_category`
- `log_area`
- `aspect_ratio`
- `has_depth`
- `is_3d_candidate`

## 5. 제외한 피처

- 작가 정보
- 출처 정보
- 갤러리 정보
- URL / 이미지 정보
- 가격 정답 컬럼

## 6. 사용 모델

- baseline
- `dummy_median`
- 선형/robust 선형
- `ridge`
- `huber`
- `quantile_median`
- 트리 계열
- `hist_gradient_boosting`
- `random_forest`
- `lightgbm`
- `xgboost`
- `catboost`

## 7. 실행 명령

```bash
python3 scripts/track4/run_t4_e025_cold_model_comparison.py
```

## 8. 결과 파일

- 결과 JSON: `data/track4/results/t4_e025_cold_model_comparison_metrics.json`
- 예측 CSV: `data/track4/predictions/t4_e025_cold_model_comparison_predictions.csv`
- 실행 스크립트: `scripts/track4/run_t4_e025_cold_model_comparison.py`

## 9. 주요 결과

| 모델 | 모델군 | median APE | MAPE | RMSE(log) | Within-30% | Within-50% | p95 APE |
|---|---|---:|---:|---:|---:|---:|---:|
| quantile_median | robust_linear | 0.3486 | 0.4919 | 0.6725 | 0.4487 | 0.6307 | 1.2464 |
| huber | robust_linear | 0.3567 | 0.5013 | 0.6720 | 0.4454 | 0.6213 | 1.2373 |
| lightgbm | tree | 0.3748 | 0.6024 | 0.6801 | 0.4146 | 0.5998 | 1.6652 |
| hist_gradient_boosting | tree | 0.3835 | 0.5892 | 0.6763 | 0.4333 | 0.6036 | 1.6212 |
| xgboost | tree | 0.3860 | 0.5697 | 0.6661 | 0.4234 | 0.6058 | 1.4719 |
| catboost | tree | 0.3962 | 0.6005 | 0.6783 | 0.3931 | 0.5910 | 1.5359 |
| ridge | linear | 0.3962 | 0.5899 | 0.6968 | 0.3942 | 0.5783 | 1.5736 |
| random_forest | tree | 0.3983 | 0.6169 | 0.7147 | 0.3804 | 0.6042 | 1.7765 |
| dummy_median | baseline | 0.7424 | 1.3365 | 1.1582 | 0.1979 | 0.3280 | 4.1520 |

## 10. 해석

- median APE 기준 최선은 `quantile_median`임
- p95 APE 기준 최선은 `huber`임
- 두 모델 모두 robust 선형 계열임
- 트리 계열은 단순 중앙값보다 개선됐지만 robust 선형 계열보다 median APE와 p95 APE가 전반적으로 불리함
- 따라서 Cold에서는 현재 구조-only 피처 기준으로 복잡한 트리 모델보다 robust 선형 계열이 더 안정적임

## 11. 결론

- 채택 / 보류 / 중단: 부분 채택
- 판단:
- `T4-H4`는 validation 기준 지지됨
- Cold 기준 후보는 `quantile_median`과 `huber`를 함께 유지함
- 단일 대표 점수인 median APE 기준은 `quantile_median` 우선
- 큰 오차 위험인 p95 APE 기준은 `huber` 우선

## 12. 후속 작업

- `T4-E026`: support unknown 처리 ablation
- `T4-E027`: 2D/3D slice 및 depth 피처 실험
- `T4-H17`: Cold 저위험/고위험 구간 분리 실험
- `T4-H18`: 가격 범위 calibration 실험
