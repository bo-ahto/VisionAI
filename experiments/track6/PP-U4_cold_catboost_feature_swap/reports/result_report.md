# PP-U4 Cold CatBoost 피처 교환/확장 비교

## 실험 계획

- 목적: 기존 실험에서 확인된 피처 영향도를 바탕으로 피처셋을 교환, 축소, 확장했을 때 성능이 어떻게 바뀌는지 확인한다.
- 대상: `cold` 데이터, `catboost` 모델.
- 통제 기준: 데이터 split, target(`ln_price_krw`), 모델 설정, 평가 지표는 고정하고 피처셋만 바꾼다.
- 선택 기준: validation에서 후보를 고르고 test는 선택된 후보의 재현성 확인으로만 사용한다.
- 기대 결과: 어떤 피처 조합이 모델 특성에 맞는지 확인하고, 후속 모델 조합/보정 실험의 입력 후보를 갱신한다.

## 후보 피처셋

| 후보 | 전략 | 피처 수 | 가설 |
|---|---|---:|---|
| `baseline_base_medium_shape` | CatBoost 기준 medium-shape 피처셋 | 12 | 현재 Cold CatBoost final artifact와 같은 피처셋 |
| `lightgbm_swap_support_size` | LightGBM 기준 support-size 피처셋 교환 | 12 | CatBoost에도 LightGBM형 support-size 구간을 넣으면 개선되는지 확인 |
| `support_shape_combo` | support-size + medium-shape 결합 | 14 | CatBoost 대칭 트리가 두 bucket 조합을 함께 나눌 수 있는지 확인 |
| `generated_all_combo` | 전체 생성 bucket 확장 | 19 | 생성 bucket을 모두 넣었을 때 CatBoost가 유효한 조합만 고르는지 확인 |
| `raw_material_no_bucket` | 원본 크기+재료 중심 | 12 | 명시 bucket 없이 CatBoost split만으로 조합을 찾는지 확인 |
| `medium_size_combo` | medium-size 조합 | 13 | 재료와 크기 조합이 medium-shape보다 나은지 확인 |
| `depth_shape_combo` | depth-shape 조합 | 11 | CatBoost에서 depth/shape interaction만 강조했을 때 tail이 줄어드는지 확인 |

## Validation 결과

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | baseline 대비 MdAPE |
|---|---:|---:|---:|---:|---:|
| `baseline_base_medium_shape` | 0.4194 | 0.7332 | 2.2053 | 0.7037 | +0.0000 |
| `raw_material_no_bucket` | 0.4222 | 0.7331 | 2.3514 | 0.7046 | +0.0028 |
| `support_shape_combo` | 0.4230 | 0.7349 | 2.2437 | 0.7072 | +0.0036 |
| `medium_size_combo` | 0.4253 | 0.7496 | 2.3852 | 0.7131 | +0.0060 |
| `lightgbm_swap_support_size` | 0.4260 | 0.7507 | 2.3555 | 0.7139 | +0.0066 |
| `generated_all_combo` | 0.4292 | 0.7385 | 2.1762 | 0.7084 | +0.0098 |
| `depth_shape_combo` | 0.4460 | 0.7665 | 2.5934 | 0.7221 | +0.0267 |

## Test 확인 결과

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | baseline 대비 MdAPE |
|---|---:|---:|---:|---:|---:|
| `lightgbm_swap_support_size` | 0.4835 | 1.4657 | 4.4439 | 0.9640 | -0.0032 |
| `support_shape_combo` | 0.4848 | 1.5606 | 4.4354 | 0.9808 | -0.0019 |
| `baseline_base_medium_shape` | 0.4867 | 1.4803 | 4.6329 | 0.9681 | +0.0000 |
| `medium_size_combo` | 0.4894 | 1.4731 | 4.5768 | 0.9659 | +0.0027 |
| `generated_all_combo` | 0.4923 | 1.5108 | 4.5280 | 0.9770 | +0.0056 |
| `raw_material_no_bucket` | 0.4936 | 1.4930 | 4.3014 | 0.9743 | +0.0069 |
| `depth_shape_combo` | 0.4984 | 1.4392 | 4.5495 | 0.9688 | +0.0117 |

## 코멘터리

- validation 기준 1위 후보는 `baseline_base_medium_shape`이고, 기준 후보 `baseline_base_medium_shape` 대비 MdAPE 변화는 `+0.0000`이다.
- test 기준 1위 후보는 `lightgbm_swap_support_size`이고, 기준 후보 `baseline_base_medium_shape` 대비 MdAPE 변화는 `-0.0032`이다.
- validation과 test의 1위가 다르면 즉시 교체하지 않고, 후속 조합/보정 후보로만 둔다.
- 피처 교환 실험은 모델을 바꾸는 실험이 아니라, 같은 모델에서 어떤 입력 정보 구조가 더 맞는지 확인하는 사전 검증이다.
