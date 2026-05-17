# T4-E026 support unknown 처리 ablation

- 실험 ID: `T4-E026`
- 연결 가설: `T4-H6`, `T4-H14`
- 날짜: 2026-05-17
- 상태: 완료

## 1. 실험 목적

- Track 4에서 `support_category`를 모델 피처로 유지할지 확인함
- support unknown을 단순 결측으로 볼지, 위험 신호로 볼지 확인함
- Warm과 Cold에서 support 피처 정책을 같이 가져가도 되는지 확인함

## 2. 확인하려는 질문

- support 정보를 빼면 성능이 좋아지는가
- support category를 그대로 쓰는 것이 좋은가
- support unknown 여부만 flag로 쓰는 것이 좋은가
- `medium_support_bucket`처럼 재료와 지지체를 조합하면 좋아지는가
- support unknown 작품은 실제로 오차가 더 큰가

## 3. 사용 데이터

- 학습 데이터: `data/track4_split/track4_train.csv`
- Warm 평가 데이터: `data/track4_split/track4_val_warm.csv`
- Cold 평가 데이터: `data/track4_split/track4_val_cold.csv`

| 구분 | rows | 작가 수 | support unknown 수 | support unknown 비율 |
|---|---:|---:|---:|---:|
| train | 28,905 | 1,834 | 2,321 | 0.0803 |
| val_warm | 67 | 67 | 7 | 0.1045 |
| val_cold | 1,814 | 108 | 206 | 0.1136 |

## 4. 사용 모델

- Warm 모델
- `Ridge`
- 구조 피처 + `artist_key` + 작가 이력 피처 사용
- 이유: `T4-E024`에서 Warm 작가 key 포함 모델이 가장 좋았기 때문
- Cold 모델
- `QuantileRegressor`
- 작가 피처 제외
- 이유: `T4-E025`에서 Cold median APE 기준 가장 좋았기 때문

## 5. 비교한 피처 조합

- `no_support`
- support 정보를 모두 제외
- `support_category`
- support_category를 범주형으로 사용
- `support_unknown_flag`
- support가 unknown인지 여부만 사용
- `medium_support_bucket`
- 재료와 지지체 조합 사용
- `support_category_plus_unknown_flag`
- support_category와 unknown flag를 함께 사용

## 6. 실행 명령

```bash
python3 scripts/track4/run_t4_e026_support_unknown_ablation.py
```

## 7. 결과 파일

- 결과 JSON: `data/track4/results/t4_e026_support_unknown_ablation_metrics.json`
- 예측 CSV: `data/track4/predictions/t4_e026_support_unknown_ablation_predictions.csv`
- 실행 스크립트: `scripts/track4/run_t4_e026_support_unknown_ablation.py`

## 8. 주요 결과

| 피처 조합 | Warm median APE | Warm p95 APE | Cold median APE | Cold p95 APE | 해석 |
|---|---:|---:|---:|---:|---|
| no_support | 0.2885 | 1.7671 | 0.3410 | 1.3120 | Cold median 기준 최선 |
| support_category | 0.2697 | 1.6488 | 0.3486 | 1.2464 | Warm 기준 최선 |
| support_unknown_flag | 0.2827 | 1.7351 | 0.3507 | 1.2301 | Cold p95 기준 최선 |
| medium_support_bucket | 0.2926 | 1.5995 | 0.3624 | 1.2601 | Warm p95는 낮지만 median 악화 |
| support_category_plus_unknown_flag | 0.2698 | 1.6488 | 0.3476 | 1.2475 | support_category와 거의 유사 |

## 9. Cold support known / unknown slice

| 피처 조합 | support known median APE | support unknown median APE | support unknown rows | 해석 |
|---|---:|---:|---:|---|
| no_support | 0.3201 | 0.5559 | 206 | unknown 구간 오차가 큼 |
| support_category | 0.3241 | 0.5895 | 206 | unknown 구간 오차가 더 큼 |
| support_unknown_flag | 0.3232 | 0.5770 | 206 | unknown flag만으로 큰 개선은 없음 |
| medium_support_bucket | 0.3308 | 0.5618 | 206 | 조합 피처도 개선 제한적 |
| support_category_plus_unknown_flag | 0.3232 | 0.5887 | 206 | support_category와 유사 |

## 10. 해석

- Warm에서는 `support_category`를 유지하는 것이 가장 좋음
- Cold에서는 `no_support`가 median APE 기준 가장 좋음
- Cold p95 APE 기준으로는 `support_unknown_flag`가 가장 좋지만 median APE는 악화됨
- `medium_support_bucket`은 Warm/Cold median APE를 모두 개선하지 못함
- Cold에서 support unknown 작품은 known 작품보다 median APE가 뚜렷하게 높음
- 따라서 support unknown은 성능 개선 피처라기보다 신뢰도/위험 구간 판단용 피처로 보는 것이 적절함

## 11. 결론

- 채택 / 보류 / 중단: 부분 채택
- 판단:
- `T4-H6`: support 피처는 Warm/Cold에 동일하게 적용하면 안 됨
- `T4-H14`: support unknown은 오차가 큰 구간을 설명하는 위험 신호로 유지할 가치가 있음
- 운영 후보:
- Warm: `support_category` 유지
- Cold: 기본 예측 모델에서는 support 제외 우선 검토
- Cold 신뢰도 정책: `is_support_unknown`을 위험 flag 후보로 유지

## 12. 후속 작업

- `T4-H17`: support unknown을 Cold 위험 구간 분리 기준에 포함
- `T4-H24`: 입력 정보 부족 시 가격 범위/경고 정책에 반영
- `T4-H28`: 재료와 크기 조합 피처는 별도 실험에서 재검토
