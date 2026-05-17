# T5-E017 Cold support_unknown fallback 실험

- 날짜: 2026-05-18
- 관련 가설: T5-H20
- 목적: 지지체 정보가 없는 Cold 작품을 별도 모델로 보완할 수 있는지 확인

## 실험 방법

- 기준 모델: QuantileRegressor
- fallback 조건: `support_unknown == 1`
- support_unknown train 표본만으로 별도 모델을 학습
- validation에서 support_unknown 작품은 fallback 예측으로 교체

## 결과

| 구분 | median APE | p95 APE |
|---|---:|---:|
| Cold base 전체 | 0.3432 | 1.8235 |
| fallback 전체 | 0.3401 | 1.8235 |
| fallback support_known | 0.3252 | 1.6555 |
| fallback support_unknown | 0.5585 | 8.2886 |

## 해석

- 전체 median은 소폭 개선됨
- 하지만 support_unknown 구간의 p95가 매우 커서 위험 구간 자체는 해결되지 않음
- fallback 모델이 해당 구간을 안정화한다고 보기 어려움

## 결론

- support_unknown fallback은 보류
- support_unknown은 모델 분기보다 신뢰도 경고/추가 정보 요청 조건으로 쓰는 것이 적합
