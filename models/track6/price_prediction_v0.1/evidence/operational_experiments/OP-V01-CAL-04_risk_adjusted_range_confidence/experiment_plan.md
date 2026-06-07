# OP-V01-CAL-04 위험도 기반 가격 범위/신뢰도 보정

## 1. 목적

- v0.1 점가격은 유지한 상태에서, 실제 가격이 표시 범위 안에 들어오는 비율을 높일 수 있는지 확인한다.
- CAL-02/CAL-03에서 점가격 보정은 채택 보류였으므로, 가격 범위와 신뢰도 표시를 먼저 보정한다.
- 기존 validation split에서 위험 그룹별 범위 확장 배율을 정하고, 기존 test split에서만 평가한다.

## 2. 기준 모델

- 기준 후보: `PP-V8 compact_blend_mape_guarded`
- 기준 점가격: `pred_log`, `pred_price`
- 기준 범위: `routing_width`를 점가격 중심 로그 범위로 해석
- 원본 예측 파일: `models/track6/price_prediction_v0.1/evidence/experiments/PP-V8_warm_deployment_simplification/outputs/predictions.csv`

## 3. 보정 방식

- 점가격은 변경하지 않는다.
- 기준 범위는 `pred_log ± routing_width / 2`로 만든다.
- 위험 그룹별로 validation에서 필요한 범위 확장 배율을 찾는다.
- 선택 가능한 배율은 `1.00, 1.25, 1.50, 1.75, 2.00, 2.50, 3.00`이다.
- 각 위험 그룹에서 validation 범위 포함률이 목표치 이상이 되는 가장 작은 배율을 선택한다.

## 4. 위험 그룹

| 그룹 | 의미 |
| --- | --- |
| explicit_high_price_flag | 기존 데이터에서 고가 후보로 표시된 작품 |
| high_value_range_risk | 예측 가격 상위 구간이며 대형 또는 표본 부족인 작품 |
| wide_uncertainty | 기존 모델의 예측 범위 폭이 넓은 작품 |
| low_sample | 작가 학습 표본 수가 적은 작품 |
| small_low_price_risk | 저가/소형 과대 예측 가능성이 있는 작품 |
| regular | 위 조건에 해당하지 않는 일반 작품 |

## 5. 채택 기준

- test 범위 포함률이 기준선보다 개선되어야 한다.
- 범위 폭이 과도하게 넓어지면 제외한다.
- 점가격 지표는 그대로 유지되므로, 통과 후보는 신뢰도와 범위 표시 정책 후보로만 관리한다.
- v0.1 운영 기본값에는 바로 반영하지 않고, 별도 API/프론트 테스트로 표시 품질을 확인한 뒤 반영 여부를 결정한다.
