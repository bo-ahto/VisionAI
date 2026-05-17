# T4-E040 Cold 저위험 구간 가격 범위 검증

- 날짜: 2026-05-17
- 연결 가설: T4-H31
- 목적: Cold 전체가 아니라 `low_risk` 구간에 한정하면 가격 범위를 서비스에 쓸 수 있는지 확인
- 사용 데이터:
- `data/track4_split/track4_train.csv`
- `data/track4_split/track4_val_cold.csv`
- `data/track4_split/track4_test_cold.csv`

## 가설

- Cold 전체를 한 번에 서비스 대상으로 보면 범위 폭이 너무 넓다.
- Cold를 위험 구간별로 나누면 `low_risk` 구간은 제한적으로 가격 범위를 제공할 수 있을 것이다.

## 실험 방법

- `track4_train.csv`로 Cold 후보 모델을 다시 학습함
- `track4_val_cold.csv`에서 예측 오차를 계산해 가격 범위 기준을 정함
- `track4_test_cold.csv`에는 validation에서 정한 기준만 적용함
- test 정답값으로 범위를 다시 맞추지 않음
- Cold 후보는 기존 최종 후보와 동일하게 사용함
- `cold_full_size`: `medium_category`, `width_cm`, `height_cm`, `log_area`, `aspect_ratio`, `has_depth`, `is_3d_candidate`
- `cold_area_only`: `medium_category`, `log_area`

## 위험 구간 정의

- 위험 flag:
- 3D 후보
- 지지체 unknown
- train 기준 상위 10% 대형 작품
- 극단 가로세로비
- `low_risk`: 위험 flag 0개
- `mid_risk`: 위험 flag 1개
- `high_risk`: 위험 flag 2개 이상

## 판단 기준

- 단일 가격 + 범위 후보:
- q80 coverage가 `0.80` 이상
- q80 범위 폭 중앙값이 x`4.0` 이하
- 제한적 가격 범위 후보:
- `low_risk`에서 q90 coverage가 `0.78` 이상
- q90 범위 폭 중앙값이 x`6.0` 이하
- 보류:
- 범위 폭이 x`10.0`을 넘거나 coverage가 부족한 경우

## 결과

| 후보 | 구간 | rows | median APE | p95 APE | q80 coverage | q80 범위 폭 | q90 coverage | q90 범위 폭 | 판정 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| cold_full_size | low_risk | 2738 | 0.4077 | 2.6384 | 0.6581 | x3.53 | 0.7834 | x5.54 | 제한적 가격 범위 후보 |
| cold_full_size | mid_risk | 488 | 0.4274 | 4.1932 | 0.7336 | x7.59 | 0.8463 | x16.26 | 보류 |
| cold_full_size | high_risk | 51 | 0.5672 | 4.2456 | 0.8824 | x39.86 | 0.9608 | x69.58 | 보류 |
| cold_area_only | low_risk | 2738 | 0.4360 | 2.9177 | 0.6793 | x3.62 | 0.7754 | x5.20 | 추가 검증 필요 |
| cold_area_only | mid_risk | 488 | 0.4173 | 4.1662 | 0.7254 | x7.04 | 0.8381 | x23.04 | 보류 |
| cold_area_only | high_risk | 51 | 0.8085 | 3.6164 | 0.9216 | x102.95 | 0.9608 | x308.11 | 보류 |

## 해석

- `cold_full_size`의 `low_risk`만 제한적 가격 범위 후보로 남음
- 다만 q80 기준 coverage는 `0.6581`이라 단일 가격을 신뢰하기에는 부족함
- q90 기준으로 올리면 coverage는 `0.7834`까지 올라가지만, 가격 범위 폭이 x`5.54`임
- 예를 들어 예측가 100만 원이면 대략 넓은 범위를 함께 제시해야 하는 수준임
- `mid_risk`는 q90 coverage가 더 높지만 범위 폭이 x`16.26`이라 설명력이 낮음
- `high_risk`는 coverage를 맞추려면 범위 폭이 x`69.58` 이상이라 서비스 출력 후보로 보기 어려움
- `cold_area_only`는 `low_risk` q90 coverage가 `0.7754`로 기준 `0.78`에 미달함

## 결론

- T4-H31은 부분 검증으로 둠
- Cold 전체는 서비스용 단일 가격 후보가 아님
- Cold `low_risk`는 `cold_full_size` + q90 범위 정책에 한해 제한적 후보로 볼 수 있음
- Cold `mid_risk`, `high_risk`는 가격 범위가 너무 넓어 경고 또는 보류 정책이 필요함
- 다음 단계에서는 Cold 범위 폭을 줄이기 위한 세부 가설이 필요함

## 실행 명령

```bash
python3 scripts/track4/run_t4_e040_cold_low_risk_policy.py
```

## 산출물

- 결과 JSON: `data/track4/results/t4_e040_cold_low_risk_policy_metrics.json`
- 예측 로그: `data/track4/predictions/t4_e040_cold_low_risk_policy_predictions.csv`
