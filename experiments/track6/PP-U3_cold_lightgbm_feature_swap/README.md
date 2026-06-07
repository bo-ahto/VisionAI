# PP-U3 Cold LightGBM 피처 교환/확장 비교

## 실험 계획

- 목적: 기존 실험에서 확인된 피처 영향도를 바탕으로 피처셋을 교환, 축소, 확장했을 때 성능이 어떻게 바뀌는지 확인한다.
- 대상: `cold` 데이터, `lightgbm` 모델.
- 통제 기준: 데이터 split, target(`ln_price_krw`), 모델 설정, 평가 지표는 고정하고 피처셋만 바꾼다.
- 선택 기준: validation에서 후보를 고르고 test는 선택된 후보의 재현성 확인으로만 사용한다.
- 기대 결과: 어떤 피처 조합이 모델 특성에 맞는지 확인하고, 후속 모델 조합/보정 실험의 입력 후보를 갱신한다.

## 후보 피처셋

| 후보 | 전략 | 피처 수 | 가설 |
|---|---|---:|---|
| `baseline_base_support_size` | LightGBM 기준 support-size 피처셋 | 12 | 현재 Cold LightGBM final artifact와 같은 피처셋 |
| `catboost_swap_medium_shape` | CatBoost 기준 medium-shape 피처셋 교환 | 12 | LightGBM에도 CatBoost형 재료+형태 조합을 넣으면 개선되는지 확인 |
| `support_shape_combo` | support-size + medium-shape 결합 | 14 | 두 Cold 모델의 강한 bucket을 함께 쓰면 상호 보완되는지 확인 |
| `generated_all_combo` | 전체 생성 bucket 확장 | 19 | size/shape/material/support 관련 생성 bucket을 모두 넣었을 때 과적합 없이 개선되는지 확인 |
| `raw_material_no_bucket` | 원본 크기+재료 중심 | 12 | bucket 없이 원본 피처만으로 모델이 충분히 구간을 학습하는지 확인 |
| `medium_size_combo` | medium-size 조합 | 13 | 재료와 크기 조합이 Cold 가격대를 더 잘 나누는지 확인 |
| `depth_shape_combo` | depth-shape 조합 | 11 | 크기+깊이+형태 조합만으로 2D/3D 및 형태 효과가 설명되는지 확인 |

## Validation 결과

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | baseline 대비 MdAPE |
|---|---:|---:|---:|---:|---:|
| `support_shape_combo` | 0.3834 | 0.7076 | 1.9472 | 0.6903 | -0.0017 |
| `baseline_base_support_size` | 0.3851 | 0.7169 | 2.0250 | 0.6901 | +0.0000 |
| `raw_material_no_bucket` | 0.3887 | 0.7107 | 1.9811 | 0.6932 | +0.0036 |
| `medium_size_combo` | 0.3898 | 0.7027 | 2.0291 | 0.6873 | +0.0047 |
| `generated_all_combo` | 0.3912 | 0.7074 | 1.9948 | 0.6925 | +0.0061 |
| `catboost_swap_medium_shape` | 0.3973 | 0.7065 | 1.9577 | 0.6887 | +0.0122 |
| `depth_shape_combo` | 0.4244 | 0.7405 | 2.0768 | 0.7068 | +0.0392 |

## Test 확인 결과

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | baseline 대비 MdAPE |
|---|---:|---:|---:|---:|---:|
| `medium_size_combo` | 0.4803 | 1.3722 | 4.6205 | 0.9592 | -0.0106 |
| `raw_material_no_bucket` | 0.4823 | 1.4005 | 4.7220 | 0.9657 | -0.0086 |
| `catboost_swap_medium_shape` | 0.4852 | 1.3962 | 4.6384 | 0.9642 | -0.0057 |
| `support_shape_combo` | 0.4871 | 1.3618 | 4.4949 | 0.9549 | -0.0038 |
| `generated_all_combo` | 0.4881 | 1.4304 | 4.8474 | 0.9718 | -0.0027 |
| `baseline_base_support_size` | 0.4909 | 1.4131 | 4.8212 | 0.9687 | +0.0000 |
| `depth_shape_combo` | 0.4953 | 1.4010 | 4.8614 | 0.9746 | +0.0045 |

## 코멘터리

- validation 기준 1위 후보는 `support_shape_combo`이고, 기준 후보 `baseline_base_support_size` 대비 MdAPE 변화는 `-0.0017`이다.
- test 기준 1위 후보는 `medium_size_combo`이고, 기준 후보 `baseline_base_support_size` 대비 MdAPE 변화는 `-0.0106`이다.
- validation과 test의 1위가 다르면 즉시 교체하지 않고, 후속 조합/보정 후보로만 둔다.
- 피처 교환 실험은 모델을 바꾸는 실험이 아니라, 같은 모델에서 어떤 입력 정보 구조가 더 맞는지 확인하는 사전 검증이다.
