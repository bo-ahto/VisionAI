# T4-E039 가격 범위와 신뢰도 정책 보완

- 날짜: 2026-05-17
- 연결 가설: T4-H11, T4-H24, T4-H29
- 목적: 최종 후보 모델에 가격 범위와 신뢰도 그룹을 붙였을 때 test에서 실제로 쓸 수 있는지 확인
- 사용 데이터:
- `data/track4_split/track4_train.csv`
- `data/track4_split/track4_val_warm.csv`
- `data/track4_split/track4_test_warm.csv`
- `data/track4_split/track4_val_cold.csv`
- `data/track4_split/track4_test_cold.csv`

## 가설

- 단일 가격만 제시하는 것보다 가격 범위와 신뢰도 등급을 함께 주는 방식이 더 안전하다.
- 입력 정보가 부족하거나 위험 조건이면 단일 가격 대신 범위/경고 출력이 더 적절하다.

## 실험 방법

- validation 예측 오차로 가격 범위를 정함
- test에서는 validation에서 정한 범위를 그대로 적용함
- test 정답값을 이용해 범위를 다시 맞추지 않음
- 목표 coverage 후보:
- 70%
- 80%
- 90%
- 신뢰도 그룹:
- Warm: 작가 train 작품 수 기준 `low_history`, `mid_history`, `high_history`
- Cold: 3D, support unknown, 대형, 극단 비율 기준 `low_risk`, `mid_risk`, `high_risk`

## 사용 후보

- Warm 성능 후보: `warm_performance_artist_price_stats`
- Warm 운영 보수 후보: `warm_operational_artist_count`
- Cold median 후보: `cold_full_size`
- Cold tail 비교 후보: `cold_area_only`

## 결과

| 후보 | 정책 | test coverage | 범위 폭 중앙값 | 범위 폭 p90 | 해석 |
|---|---|---:|---:|---:|---|
| warm_performance_artist_price_stats | q80 | 0.8540 | x3.77 | x3.77 | coverage는 충분, 범위 폭은 다소 넓음 |
| warm_performance_artist_price_stats | q90 | 0.9197 | x5.14 | x5.14 | 안정적이나 범위가 넓음 |
| warm_operational_artist_count | q80 | 0.8102 | x4.66 | x4.66 | 운영 보수 후보도 coverage는 충족 |
| cold_full_size | q80 | 0.6729 | x3.53 | x7.59 | 80% 목표 미달 |
| cold_full_size | q90 | 0.7955 | x5.54 | x16.26 | 80%에 근접하지만 폭이 큼 |
| cold_area_only | q80 | 0.6900 | x3.62 | x7.04 | 80% 목표 미달 |
| cold_area_only | q90 | 0.7876 | x5.20 | x23.04 | 80%에 근접하지만 폭이 큼 |

## 신뢰도 그룹별 해석

- Warm
- `low_history`는 q80에서도 coverage가 낮음
- `warm_performance_artist_price_stats` q80 기준 low_history coverage `0.6757`
- 작가 이력이 적은 Warm은 낮은 신뢰도 경고 후보임

- Cold
- `low_risk`도 q80 coverage가 낮음
- `cold_full_size` q80 기준 low_risk coverage `0.6581`
- q90으로 올리면 전체 coverage는 `0.7955`까지 올라가지만 범위 폭 중앙값이 x5.54로 커짐
- `high_risk`는 coverage를 맞추려면 범위 폭이 극단적으로 커짐
- `cold_full_size` q80 기준 high_risk 범위 폭 중앙값 x39.86

## 결론

- Warm
- 가격 범위 정책은 부분적으로 사용 가능함
- 다만 low_history 작가는 신뢰도 경고가 필요함

- Cold
- 전체 Cold에 단일 범위 정책을 적용하기는 어려움
- 80% coverage를 목표로 하면 coverage가 부족함
- 90% 정책은 coverage에 가까워지지만 범위 폭이 너무 큼
- Cold는 저위험 구간 한정 서비스 가능성 또는 별도 tail risk 완화 가설이 필요함

## 상태 판단

- T4-H11: 부분 검증 유지
- Warm에는 적용 가능성이 있으나 Cold 전체에는 부족함
- T4-H24: 부분 검증 유지
- 위험 구간 경고 필요성은 확인됐지만 정책 기준은 더 세분화해야 함
- T4-H29: 부분 검증 유지
- 신뢰도 그룹별 차이는 확인됐지만 Cold low_risk도 아직 충분하지 않음

## 추가 세부 가설

- T4-H31: Cold는 전체가 아니라 low_risk 구간에 한정해야 가격 범위가 실용적일 것이다
- T4-H32: Warm low_history 작가는 별도 경고 또는 더 넓은 범위가 필요할 것이다

## 실행 명령

```bash
python3 scripts/track4/run_t4_e039_interval_policy.py
```
