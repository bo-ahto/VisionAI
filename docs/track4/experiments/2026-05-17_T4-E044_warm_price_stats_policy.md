# T4-E044 Warm 과거 가격 통계 피처 정책 검증

- 날짜: 2026-05-17
- 연결 가설: T4-H34
- 목적: Warm 과거 가격 통계 피처를 운영 피처로 조건부 허용할 근거가 있는지 확인
- 사용 데이터:
- `data/track4_split/track4_train.csv`
- `data/track4_split/track4_test_warm.csv`

## 가설

- Warm 성능 최고 후보는 작가별 과거 가격 통계 피처를 사용함
- 이 피처가 예측 시점 이전 데이터로만 계산된다면 누수가 아니라 운영 가능한 과거 이력 피처로 볼 수 있음
- 성능 개선 폭이 충분히 크면 조건부 허용을 검토할 가치가 있음

## 조건부 허용 기준

- 예측 시점 이전 학습/거래 데이터만 사용해 계산함
- 예측 대상 작품의 정답 가격은 절대 포함하지 않음
- 운영 데이터 파이프라인에서 같은 계산을 재현할 수 있어야 함
- 위 조건을 만족하지 못하면 가격 통계 피처는 금지함

## 실험 방법

- Warm 배포 가능 보수 후보와 가격 통계 추가 후보를 비교함
- 모든 후보는 `track4_train.csv`로 학습함
- 평가는 `track4_test_warm.csv`에서 수행함
- 가격 통계는 train 기준 작가별 `ln_price_krw` 통계로만 계산함
- test 정답 가격은 통계 계산에 사용하지 않음

## 비교 후보

- `deployable_count_only`
- 현재 manifest 통과 보수 후보
- 작가 key, 작가 작품 수, 재료/지지체/크기 정보 사용
- `stats_median_only`
- 작가 train 중앙 가격 추가
- `stats_median_iqr`
- 작가 train 중앙 가격과 변동 폭 추가
- `stats_mean_only`
- 작가 train 평균 가격 추가
- `stats_all`
- 작가 train 중앙/평균/변동 폭 전체 추가

## 결과

| 후보 | median APE | p95 APE | within-30 | within-50 | 현재 manifest | 조건부 허용 manifest |
|---|---:|---:|---:|---:|---|---|
| deployable_count_only | 0.2810 | 2.5504 | 0.5401 | 0.6861 | 통과 | 통과 |
| stats_median_only | 0.2467 | 1.2057 | 0.6131 | 0.8029 | 차단 | 통과 |
| stats_median_iqr | 0.2463 | 1.2040 | 0.6131 | 0.8029 | 차단 | 통과 |
| stats_mean_only | 0.2282 | 1.0820 | 0.6204 | 0.8248 | 차단 | 통과 |
| stats_all | 0.2201 | 1.1118 | 0.6131 | 0.8321 | 차단 | 통과 |

## 개선 폭

| 후보 | median APE 개선 | median APE 상대 개선 | p95 APE 개선 | p95 APE 상대 개선 |
|---|---:|---:|---:|---:|
| stats_median_only | 0.0343 | 12.21% | 1.3447 | 52.72% |
| stats_median_iqr | 0.0347 | 12.36% | 1.3464 | 52.79% |
| stats_mean_only | 0.0528 | 18.80% | 1.4684 | 57.58% |
| stats_all | 0.0610 | 21.69% | 1.4385 | 56.41% |

## history 구간별 결과

| 후보 | 구간 | rows | median APE | p95 APE | within-50 |
|---|---|---:|---:|---:|---:|
| deployable_count_only | low_history | 37 | 0.5438 | 2.9875 | 0.4324 |
| stats_all | low_history | 37 | 0.3581 | 1.6149 | 0.7027 |
| deployable_count_only | mid_history | 70 | 0.2661 | 1.3473 | 0.7286 |
| stats_all | mid_history | 70 | 0.2068 | 0.9422 | 0.8714 |
| deployable_count_only | high_history | 30 | 0.1872 | 0.7925 | 0.9000 |
| stats_all | high_history | 30 | 0.1889 | 0.8449 | 0.9000 |

## 해석

- 가격 통계 피처는 Warm 전체 성능을 크게 개선함
- 가장 좋은 후보는 `stats_all`임
- median APE는 `0.2810`에서 `0.2201`로 개선됨
- p95 APE는 `2.5504`에서 `1.1118`로 개선됨
- `low_history`에서도 median APE가 `0.5438`에서 `0.3581`로 개선됨
- `high_history`에서는 큰 개선이 없지만 악화 폭도 제한적임
- 현재 manifest는 `price` 패턴을 금지하므로 이 피처를 자동 통과시키지 않음
- 조건부 허용 규칙을 적용하면 해당 피처셋은 통과함

## 결론

- T4-H34는 검증 완료로 변경함
- 과거 가격 통계 피처는 조건부 허용을 권장함
- 조건은 “예측 시점 이전 데이터만 사용”임
- 이 조건을 코드와 manifest에 명확히 반영해야 함
- 최종 Warm 후보는 성능 기준으로 `stats_all`을 우선 검토함
- 단, 운영 DB에서 작가별 과거 가격 통계를 안정적으로 만들 수 없다면 `deployable_count_only`를 보수 후보로 유지함

## 후속 작업

- `feature_manifest.json`에 조건부 허용 피처 목록을 분리해서 추가
- 최종 dry-run에서 `stats_all` 후보가 조건부 허용 manifest를 통과하도록 수정
- 최종 운영 후보를 다시 생성

## 실행 명령

```bash
python3 scripts/track4/run_t4_e044_warm_price_stats_policy.py
```

## 산출물

- 결과 JSON: `data/track4/results/t4_e044_warm_price_stats_policy_metrics.json`
