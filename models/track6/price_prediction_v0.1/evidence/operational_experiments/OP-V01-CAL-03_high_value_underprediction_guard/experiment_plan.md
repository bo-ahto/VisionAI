# OP-V01-CAL-03 고가 작품 과소 예측 방어

## 1. 목적

- v0.1 Warm 기준 후보가 고가 작품을 지나치게 낮게 예측하는 문제를 줄일 수 있는지 확인한다.
- 0604 신규 라벨은 보정값 학습에 사용하지 않는다.
- 기존 validation split에서 상향 보정값을 만들고 기존 test split에서만 평가한다.

## 2. 기준 모델

- 기준 후보: `PP-V8 compact_blend_mape_guarded`
- 기준 예측값: `pred_log`, `pred_price`
- 원본 예측 파일: `models/track6/price_prediction_v0.1/evidence/experiments/PP-V8_warm_deployment_simplification/outputs/predictions.csv`

## 3. 보정 방식

- validation에서 `actual_log - pred_log`를 계산한다.
- 과소 예측 방어 목적이므로 음수 보정값은 사용하지 않는다.
- 즉, 예측을 더 낮추는 보정은 하지 않고, 필요한 구간만 제한적으로 올린다.
- 고가 후보 플래그가 희소하므로 예측 가격 상위 구간, 큰 면적, 작가 표본 수를 함께 본다.

## 4. 채택 기준

- test under 1/3x 건수가 줄어야 한다.
- p95_APE가 개선되어야 한다.
- MdAPE와 MAPE가 크게 악화되면 점가격 보정으로 채택하지 않는다.
- 점가격 개선은 약하지만 범위 포함률 개선 가능성이 있으면 가격 범위/신뢰도 보정 후보로 둔다.

