# H81-H86 Cold Tail Risk 완화 실험

- 실험 ID: `H81_H86_cold_tail_risk_mitigation`
- 날짜: 2026-05-15
- 목적: Cold에서 큰 오차가 나는 tail risk를 후처리 정책으로 줄일 수 있는지 확인
- 기준 데이터:
- `data/release_split/track3_train.csv`
- `data/release_split/track3_test_cold.csv`
- 결과 파일:
- `data/track3_h81_h86_cold_tail_risk_mitigation_results.json`

## 1. 실험 배경

- Cold는 median APE는 `0.2786`으로 대표 오차는 관리 가능해 보임
- 하지만 p95 APE가 `1.4860`으로 큼
- 즉 일부 작품은 예측가 대비 100% 이상 크게 벗어나는 경우가 있음
- 가격 범위가 넓어지는 이유도 이 tail risk 때문임

## 2. 확인한 가설

| 가설 | 질문 |
|---|---|
| H81 | 예측값을 train 가격 범위 안으로 clipping하면 tail risk가 줄어드는가 |
| H82 | high-risk 작품의 예측값을 전체 중앙값 쪽으로 shrink하면 큰 오차가 줄어드는가 |
| H83 | high-risk 작품의 예측값을 재료/호수 그룹 중앙값 쪽으로 shrink하면 큰 오차가 줄어드는가 |
| H84 | high-risk 작품에만 예측값 상하한 cap을 적용하면 큰 오차가 줄어드는가 |
| H85 | tail risk는 모델 보정보다 신뢰도 경고로 관리하는 것이 더 적절한가 |
| H86 | p95 개선과 median APE 손실을 함께 보는 채택 기준이 필요하다 |

## 3. 실험 방법

- H32 Cold 조건부 fallback을 기준 모델로 사용
- train 내부에서 Cold calibration set을 만듦
- calibration set에서 후보 정책을 먼저 선택함
- release Cold test에는 선택된 정책만 검증함
- test 결과를 보고 정책을 고르지 않음

## 4. 기준 성능

| 항목 | 값 |
|---|---:|
| median APE | 0.2786 |
| p90 APE | 0.9337 |
| p95 APE | 1.4860 |
| p99 APE | 3.6093 |
| within-30% | 0.5203 |
| q80 가격 배수 | x2.00 |
| q90 가격 배수 | x2.91 |

## 5. 주요 후보 결과

| 정책 | median APE | p95 APE | p95 변화 | p99 APE | q80 가격 배수 | 해석 |
|---|---:|---:|---:|---:|---:|---|
| high-risk 전체 중앙값 shrink 0.40 | 0.2828 | 1.2442 | -0.2418 | 3.4972 | x2.13 | p95 개선 크지만 q80 폭 증가 |
| 복합 high-risk 중앙값 shrink 0.40 | 0.2828 | 1.2226 | -0.2634 | 3.4972 | x2.13 | p95 최대 개선, median 소폭 악화 |
| high-risk 중앙값 shrink 0.30 | 0.2759 | 1.2997 | -0.1863 | 3.4972 | x2.08 | median도 소폭 개선, q80 폭 증가 |
| high-risk 재료 중앙값 shrink 0.30 | 0.2739 | 1.2961 | -0.1899 | 3.4972 | x2.08 | 가장 균형적인 후보 |
| high-risk 중앙값 shrink 0.20 | 0.2706 | 1.3130 | -0.1730 | 3.4972 | x2.03 | median 개선, p95 개선, 폭 소폭 증가 |

## 6. 해석

- tail risk는 줄일 수 있음
- p95 APE는 `1.4860 -> 1.2226~1.3130` 수준으로 개선됨
- median APE는 거의 유지되거나 일부 후보에서는 소폭 개선됨
- 하지만 q80 가격 배수는 `x2.00 -> x2.02~x2.13`으로 줄지 않음
- 즉 “극단적으로 크게 틀리는 사례”는 완화되지만, 80% 가격 범위 폭 자체를 줄이는 데는 실패함
- 이 보정은 가격 범위를 좁히는 용도보다 high-risk 작품의 과도한 예측값을 눌러 tail을 줄이는 용도에 가까움

## 7. 결론

- H81: 미채택
- 단순 clipping은 최종 후보로 강하지 않음

- H82: 부분 채택
- high-risk 중앙값 shrink는 p95 tail risk를 줄이는 효과가 있음
- 단, 가격 범위 폭 축소 효과는 없음

- H83: 부분 채택
- 재료 그룹 중앙값 shrink는 median과 p95를 함께 개선하는 균형 후보임
- 다만 운영 전 추가 검증 필요

- H84: 미채택
- high-risk cap은 shrink보다 강한 후보로 보이지 않음

- H85: 채택
- Cold tail risk는 모델 보정만으로 해결하기 어렵고 신뢰도 경고와 함께 관리해야 함

- H86: 채택
- p95 개선만으로 채택하지 않고 median APE, q80 가격 범위, within-30%를 함께 봐야 함

## 8. 현재 판단

- Cold tail risk 완화용 후보는 있음
- 가장 현실적인 후보는 `high-risk 재료 중앙값 shrink 0.30`
- test 기준:
- median APE `0.2786 -> 0.2739`
- p95 APE `1.4860 -> 1.2961`
- q80 가격 배수 `x2.00 -> x2.08`
- 따라서 성능은 좋아지지만 가격 범위 폭은 줄지 않음
- 운영 후보로 바로 확정하지 말고 “tail-risk 보정 후보”로 보류하는 것이 적절함
