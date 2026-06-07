# OP-V01-CAL-02 저가/소형 작품 과대 예측 방어

## 1. 목적

- v0.1 Warm 기준 후보에서 실제보다 3배 이상 높게 예측하는 과대 예측을 줄일 수 있는지 확인한다.
- 0604 신규 라벨은 보정값 학습에 사용하지 않는다.
- 기존 validation split에서 보정값을 만들고 기존 test split에서만 평가한다.

## 2. 기준 모델

- 기준 후보: `PP-V8 compact_blend_mape_guarded`
- 기준 예측값: `pred_log`, `pred_price`
- 원본 예측 파일: `models/track6/price_prediction_v0.1/evidence/experiments/PP-V8_warm_deployment_simplification/outputs/predictions.csv`
- 피처 파일:
  - `models/track6/price_prediction_v0.1/data/training/track6_split/track6_val_warm.csv`
  - `models/track6/price_prediction_v0.1/data/training/track6_split/track6_test_warm.csv`

## 3. 보정 방식

- validation에서 `actual_log - pred_log`를 계산한다.
- 과대 예측 방어 목적이므로 양수 보정값은 사용하지 않는다.
- 즉, 예측을 더 올리는 보정은 하지 않고, 필요한 구간만 제한적으로 낮춘다.
- 보정값은 구간별 residual median을 사용한다.
- 보정값은 과도한 하향을 막기 위해 cap을 둔다.

## 4. 실험 후보

| 후보 | 방식 |
| --- | --- |
| baseline | 기존 v0.1 Warm 기준 후보 |
| global_negative_cap20 | validation 전체 중앙 오차가 음수일 때만 최대 20% 로그 하향 |
| pred_bin_negative_cap20 | 예측 가격 5분위 구간별 하향 보정 |
| area_bin_negative_cap20 | 작품 면적 구간별 하향 보정 |
| pred_area_negative_min20_cap20 | 예측 가격 구간과 면적 구간 조합별 하향 보정 |
| pred_area_sample_negative_min15_cap15 | 예측 가격, 면적, 작가 학습 표본 수 조합별 하향 보정 |

## 5. 채택 기준

- test MAPE가 개선되어야 한다.
- over 3x 건수가 줄어야 한다.
- MdAPE와 p95_APE가 악화되면 점가격 보정으로 채택하지 않는다.
- 성능 개선이 작거나 불안정하면 가격 범위/신뢰도 보정 후보로만 둔다.

