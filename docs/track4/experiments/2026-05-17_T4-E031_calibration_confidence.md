# T4-E031 가격 범위와 신뢰도 calibration

- 실험 ID: `T4-E031`
- 연결 가설: `T4-H18`, `T4-H29`
- 날짜: 2026-05-17
- 상태: 완료

## 1. 실험 목적

- validation에서 정한 가격 범위가 test에서도 유지되는지 확인함
- 단일 가격 예측만으로 부족한 구간을 신뢰도 그룹으로 구분할 수 있는지 확인함
- Warm과 Cold의 가격 범위 폭과 coverage를 분리해서 판단함

## 2. 확인하려는 질문

- validation 오차로 만든 80% 가격 범위가 test에서도 80% 안팎을 유지하는가
- Warm과 Cold의 가격 범위 폭이 얼마나 다른가
- 신뢰도 그룹별로 coverage와 범위 폭 차이가 나는가

## 3. 사용 데이터

- 학습 데이터: `data/track4_split/track4_train.csv`
- calibration 데이터:
- `data/track4_split/track4_val_warm.csv`
- `data/track4_split/track4_val_cold.csv`
- 최종 확인 데이터:
- `data/track4_split/track4_test_warm.csv`
- `data/track4_split/track4_test_cold.csv`

## 4. 사용 모델

- Warm 모델
- `Ridge`
- 구조 피처 + `support_category` + `artist_key` + 작가 이력 피처
- Cold 모델
- `QuantileRegressor`
- `medium_category`, `log_area`, `aspect_ratio`

## 5. 신뢰도 그룹

- Warm
- `low_history`: 작가 학습 작품 수 5건 미만
- `mid_history`: 작가 학습 작품 수 5건 이상 20건 미만
- `high_history`: 작가 학습 작품 수 20건 이상
- Cold
- `low`: 위험 flag 0개
- `medium`: 위험 flag 1개
- `high`: 위험 flag 2개 이상

## 6. 가격 범위 계산 방식

- validation에서 절대 로그 오차의 80% 분위값을 계산함
- `abs_log_error_q80 = quantile(|실제 로그가격 - 예측 로그가격|, 0.80)`
- 예측 가격 범위
- 하한: `exp(예측 로그가격 - abs_log_error_q80)`
- 상한: `exp(예측 로그가격 + abs_log_error_q80)`
- coverage
- 실제 가격이 위 범위 안에 들어온 비율

## 7. 실행 명령

```bash
python3 scripts/track4/run_t4_e031_calibration_confidence.py
```

## 8. 결과 파일

- 결과 JSON: `data/track4/results/t4_e031_calibration_confidence_metrics.json`
- 예측 CSV: `data/track4/predictions/t4_e031_calibration_confidence_predictions.csv`
- 실행 스크립트: `scripts/track4/run_t4_e031_calibration_confidence.py`

## 9. 단일 가격 예측 결과

| 구분 | rows | median APE | p95 APE | Within-30% | Within-50% |
|---|---:|---:|---:|---:|---:|
| val_warm | 67 | 0.2597 | 1.5644 | 0.5522 | 0.6567 |
| test_warm | 137 | 0.2810 | 2.5504 | 0.5401 | 0.6861 |
| val_cold | 1,814 | 0.3642 | 1.1421 | 0.4305 | 0.6389 |
| test_cold | 3,277 | 0.4363 | 2.8482 | 0.3604 | 0.5648 |

## 10. validation에서 학습한 가격 범위

| 구분 | abs_log_error_q80 | 반폭 배수 | 전체 범위 배수 |
|---|---:|---:|---:|
| Warm 전체 | 0.7081 | x2.03 | x4.12 |
| Cold 전체 | 0.7049 | x2.02 | x4.10 |

## 11. test 가격 범위 결과

| 구분 | rows | coverage | 평균 전체 범위 배수 | 중앙 전체 범위 배수 |
|---|---:|---:|---:|---:|
| Warm 전체 | 137 | 0.8102 | x4.39 | x4.66 |
| Cold 전체 | 3,277 | 0.6900 | x5.82 | x3.60 |

## 12. Warm 신뢰도 그룹별 test 결과

| 그룹 | rows | coverage | 중앙 전체 범위 배수 | 해석 |
|---|---:|---:|---:|---|
| high_history | 30 | 0.9667 | x4.12 | 범위가 보수적 |
| mid_history | 70 | 0.8571 | x4.66 | 목표보다 약간 높음 |
| low_history | 37 | 0.5946 | x4.12 | 범위가 부족함 |

## 13. Cold 신뢰도 그룹별 test 결과

| 그룹 | rows | coverage | 중앙 전체 범위 배수 | 해석 |
|---|---:|---:|---:|---|
| low | 2,734 | 0.6792 | x3.60 | 목표 80%에 미달 |
| medium | 481 | 0.7380 | x6.97 | 목표 80%에 미달 |
| high | 62 | 0.7903 | x94.88 | coverage는 근접하지만 폭이 너무 넓음 |

## 14. 해석

- Warm 전체는 test coverage `0.8102`로 목표 80%에 근접함
- Warm low_history는 coverage `0.5946`으로 범위가 부족함
- Cold 전체는 coverage `0.6900`으로 목표 80%에 크게 미달함
- Cold high 그룹은 coverage `0.7903`이지만 중앙 전체 범위 배수가 `x94.88`로 서비스 출력에 부적절함
- 따라서 Cold는 단순 validation q80 방식만으로는 안정적인 가격 범위를 만들기 어려움

## 15. 결론

- 채택 / 보류 / 중단: 부분 채택
- 판단:
- `T4-H18`: validation 기반 calibration은 Warm에는 대체로 유효하지만 Cold에는 부족함
- `T4-H29`: 신뢰도 그룹은 오차와 범위 폭 차이를 설명하는 데 유효함
- 운영 후보:
- Warm은 가격 범위 표시 후보로 유지
- Warm low_history는 별도 넓은 범위 또는 낮은 신뢰도 표시 필요
- Cold는 단일 가격과 일반 범위만으로는 부족함
- Cold high risk는 가격 범위가 과도하게 넓어 서비스 정책 재설계 필요

## 16. 후속 작업

- Cold 가격 범위는 더 보수적인 calibration 또는 예측 보류 정책 검토
- Warm low_history 전용 calibration 검토
- Cold high risk는 “참고 범위” 또는 “예측 신뢰 낮음” 정책으로 분리 검토
