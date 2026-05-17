# T5-E016 Cold 결측 flag 피처 실험

- 날짜: 2026-05-18
- 관련 가설: T5-H19
- 목적: 재료/지지체 unknown 여부를 모델 피처로 넣으면 Cold 성능이 개선되는지 확인

## 실험 방법

- 기준 모델: QuantileRegressor
- 평가 데이터: `track5_val_cold.csv`
- 기준 피처: Cold full_size
- 추가 피처
  - `medium_unknown`
  - `support_unknown`
  - `missing_info_count`

## 결과

| 설정 | median APE | p95 APE | Within-30 | Within-50 |
|---|---:|---:|---:|---:|
| cold base | 0.3432 | 1.8235 | 0.4538 | 0.6659 |
| cold missing flags | 0.3437 | 1.8242 | 0.4538 | 0.6667 |

## 해석

- 결측 flag를 단순히 피처에 추가해도 성능 개선은 없음
- unknown 정보는 모델 입력보다 서비스 경고 조건으로 쓰는 쪽이 더 적합해 보임

## 결론

- 단순 missing flag 피처는 미채택
- 위험 경고 정책에는 계속 활용 가능
