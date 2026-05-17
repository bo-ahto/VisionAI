# T4-E041 Warm 저이력 작가 가격 범위 검증

- 날짜: 2026-05-17
- 연결 가설: T4-H3, T4-H32
- 목적: Warm에서도 train 작품 수가 적은 작가는 별도 경고나 더 넓은 가격 범위가 필요한지 확인
- 사용 데이터:
- `data/track4_split/track4_train.csv`
- `data/track4_split/track4_val_warm.csv`
- `data/track4_split/track4_test_warm.csv`

## 가설

- Warm 전체 성능이 좋아도 `low_history` 작가는 일반 Warm 작가보다 오차가 클 수 있다.
- `low_history` 작가는 단일 가격 또는 q80 범위만으로는 부족하고, 경고와 더 넓은 범위가 필요할 수 있다.

## 실험 방법

- `track4_train.csv`로 Warm 후보 모델을 다시 학습함
- `track4_val_warm.csv`에서 가격 범위 기준을 정함
- `track4_test_warm.csv`에서 history 구간별 coverage와 범위 폭을 확인함
- test 정답값으로 가격 범위를 다시 맞추지 않음
- 비교 후보:
- `warm_performance_artist_price_stats`: 작가 key, 작품 수, train 기준 작가 가격 통계 포함
- `warm_operational_artist_count`: 작가 key, 작품 수만 포함한 보수 후보

## history 구간 정의

- `low_history`: train 기준 작가 작품 수 5개 미만
- `mid_history`: train 기준 작가 작품 수 5개 이상 20개 미만
- `high_history`: train 기준 작가 작품 수 20개 이상

## 판단 기준

- 일반 범위 후보:
- q80 coverage가 `0.80` 이상
- q80 범위 폭 중앙값이 x`4.0` 이하
- 저이력 경고 + 넓은 범위 후보:
- `low_history` q90 coverage가 `0.80` 이상
- `low_history` q90 범위 폭 중앙값이 x`5.5` 이하

## 결과

| 후보 | 구간 | rows | median APE | p95 APE | q80 coverage | q80 범위 폭 | q90 coverage | q90 범위 폭 | 판정 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| warm_performance_artist_price_stats | low_history | 37 | 0.3581 | 1.6149 | 0.6757 | x2.74 | 0.8378 | x4.76 | 경고 + 넓은 범위 후보 |
| warm_performance_artist_price_stats | mid_history | 70 | 0.2068 | 0.9422 | 0.9143 | x3.77 | 0.9429 | x5.14 | 일반 범위 후보 |
| warm_performance_artist_price_stats | high_history | 30 | 0.1889 | 0.8449 | 0.9333 | x2.74 | 0.9667 | x4.76 | 일반 범위 후보 |
| warm_operational_artist_count | low_history | 37 | 0.5438 | 2.9875 | 0.5946 | x4.12 | 0.7027 | x6.57 | 보류 |
| warm_operational_artist_count | mid_history | 70 | 0.2661 | 1.3473 | 0.8571 | x4.66 | 0.9286 | x7.05 | 추가 검증 필요 |
| warm_operational_artist_count | high_history | 30 | 0.1872 | 0.7925 | 0.9667 | x4.12 | 0.9667 | x6.57 | 추가 검증 필요 |

## 해석

- Warm 전체 최고 후보는 `warm_performance_artist_price_stats`임
- test median APE:
- `warm_performance_artist_price_stats`: `0.2201`
- `warm_operational_artist_count`: `0.2810`
- `low_history`는 성능 후보에서도 median APE `0.3581`, p95 APE `1.6149`로 다른 history 구간보다 불안정함
- `low_history` q80 coverage는 `0.6757`로 부족함
- q90으로 넓히면 coverage가 `0.8378`까지 올라가고, 범위 폭은 x`4.76`임
- 따라서 `low_history`는 “일반 Warm”으로 표시하기보다 경고와 넓은 범위를 함께 주는 정책이 적절함
- 작가 가격 통계를 뺀 운영 보수 후보는 `low_history` 성능이 크게 악화되어 Warm 최종 후보로 부적합함

## 결론

- T4-H32는 검증 완료로 변경함
- Warm `low_history`는 별도 경고 또는 더 넓은 가격 범위가 필요함
- T4-H3는 부분 검증 유지함
- 작가 가격 통계 피처는 성능상 유리하지만, 운영에서 “예측 시점 이전 거래 데이터로만 만들 수 있는지”를 최종 dry-run에서 확인해야 함
- Warm 최종 후보는 현재 기준 `warm_performance_artist_price_stats` 유지가 타당함

## 실행 명령

```bash
python3 scripts/track4/run_t4_e041_warm_low_history_policy.py
```

## 산출물

- 결과 JSON: `data/track4/results/t4_e041_warm_low_history_policy_metrics.json`
- 예측 로그: `data/track4/predictions/t4_e041_warm_low_history_policy_predictions.csv`
