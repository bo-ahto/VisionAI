# T5-E012 Cold 위험 구간 분석

- 날짜: 2026-05-18
- 관련 가설: T5-H15
- 목적: Cold 단일 예측값을 그대로 사용할 수 있는 구간과 주의가 필요한 구간을 나눌 수 있는지 확인

## 1. 실험 배경

- T5-E010에서 Cold 최종 후보는 유지됐지만 test median APE `0.3918`, p95 APE `2.0152`로 오차 폭이 큼
- Cold는 처음 보는 작가이므로 Warm보다 가격 예측의 불확실성이 큼
- 서비스 적용 전 어떤 조건에서 신뢰도 경고가 필요한지 확인해야 함

## 2. 사용 데이터

- 평가: `data/track5_split/track5_test_cold.csv`
- 예측값: `data/track5/predictions/t5_e010_final_candidate_test_predictions.csv`
- 결과: `data/track5/results/t5_e012_cold_risk_slice_analysis_metrics.json`

## 3. 실험 방법

- Cold 1순위 후보인 QuantileRegressor + full_size 예측 결과를 사용함
- 아래 조건별로 오차를 비교함
  - 대형 작품 여부
  - 초대형 작품 여부
  - 3D 여부
  - 재료 unknown 여부
  - 지지체 unknown 여부
  - 위 조건을 합친 risk score
- 판단 기준
  - 특정 구간의 median APE 또는 p95 APE가 전체보다 높으면 위험 구간 후보로 봄
  - 표본 수가 너무 적으면 확정이 아니라 후속 검증 대상으로 둠

## 4. 전체 결과

| 구분 | rows | median APE | p95 APE | Within-30 | Within-50 |
|---|---:|---:|---:|---:|---:|
| Cold 전체 | 2896 | 0.3918 | 2.0152 | 0.3930 | 0.5746 |

## 5. 주요 구간 결과

| 구간 | rows | median APE | p95 APE | 해석 |
|---|---:|---:|---:|---|
| support known | 2679 | 0.3795 | 1.8762 | 전체보다 안정적 |
| support unknown | 217 | 0.5272 | 4.4609 | 강한 위험 신호 |
| medium known | 2861 | 0.3871 | 1.9147 | 전체보다 안정적 |
| medium unknown | 35 | 0.8762 | 2.7011 | 위험 신호지만 표본 적음 |
| very large 아님 | 2328 | 0.4003 | 1.9177 | 전체와 유사 |
| very large | 568 | 0.3704 | 2.4292 | median은 낮지만 큰 오차 위험 증가 |
| 3D 아님 | 660 | 0.4181 | 2.3084 | 3D보다 오히려 p95 높음 |
| 3D | 2236 | 0.3776 | 1.8933 | 단독 위험 조건으로 보기 어려움 |

## 6. 해석

- 가장 강한 위험 신호는 `support_unknown`임
  - median APE `0.5272`
  - p95 APE `4.4609`
- `medium_unknown`도 위험 신호가 있으나 rows `35`로 표본이 작음
- 대형/3D 여부만으로는 위험 구간이 명확하게 갈리지 않음
- 초대형 작품은 median은 나쁘지 않지만 p95가 커서 큰 오차 가능성은 있음

## 7. 결론

- Cold는 단일 가격만 제공하기보다 신뢰도 구간을 함께 관리해야 함
- 우선 경고 후보
  - 지지체 정보가 없는 작품
  - 재료 정보가 없는 작품
  - 초대형 작품
- 다음 단계에서는 위 조건을 사용해 가격 범위 폭과 커버리지를 검증해야 함
