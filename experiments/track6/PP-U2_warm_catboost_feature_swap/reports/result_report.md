# PP-U2 Warm CatBoost 피처 교환/축소/확장 비교

## 실험 계획

- 목적: 기존 실험에서 확인된 피처 영향도를 바탕으로 피처셋을 교환, 축소, 확장했을 때 성능이 어떻게 바뀌는지 확인한다.
- 대상: `warm` 데이터, `catboost` 모델.
- 통제 기준: 데이터 split, target(`ln_price_krw`), 모델 설정, 평가 지표는 고정하고 피처셋만 바꾼다.
- 선택 기준: validation에서 후보를 고르고 test는 선택된 후보의 재현성 확인으로만 사용한다.
- 기대 결과: 어떤 피처 조합이 모델 특성에 맞는지 확인하고, 후속 모델 조합/보정 실험의 입력 후보를 갱신한다.

## 후보 피처셋

| 후보 | 전략 | 피처 수 | 가설 |
|---|---|---:|---|
| `baseline_base_existing_combo` | 기준 피처셋 | 13 | 현재 Warm Huber final artifact와 같은 피처셋 |
| `artist_size_only` | 작가+크기 핵심축만 유지 | 5 | 기존 group-drop에서 핵심으로 확인된 작가와 크기만 남겼을 때 노이즈가 줄어드는지 확인 |
| `artist_size_aspect` | 작가+크기+형태 | 7 | 형태/aspect가 Warm에서 약한 보조 신호인지 재확인 |
| `artist_size_depth` | 작가+크기+깊이/입체 | 8 | depth/3D가 Warm에서는 독립 설명력이 약했는지 재확인 |
| `artist_size_material` | 작가+크기+재료/지지체 | 8 | 재료/지지체 조합이 Warm에서 노이즈인지 보조 신호인지 확인 |
| `artist_size_works` | 작가+크기+작가 학습량 | 6 | artist_works_log가 p95 안정성 보조 피처로 작동하는지 확인 |
| `artist_size_generated_buckets` | 작가+크기+생성 bucket | 9 | size/shape/support bucket을 쓰면 선형 Huber가 구간 효과를 더 잘 반영하는지 확인 |
| `full_plus_generated_buckets` | 기준 피처셋+생성 bucket | 20 | 기준 피처셋에 생성 bucket을 추가해 구간 정보를 더 넣는 것이 도움이 되는지 확인 |

## Validation 결과

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | baseline 대비 MdAPE |
|---|---:|---:|---:|---:|---:|
| `artist_size_only` | 0.2778 | 0.4109 | 1.3366 | 0.5540 | -0.0134 |
| `artist_size_works` | 0.2782 | 0.4053 | 1.2457 | 0.5592 | -0.0130 |
| `artist_size_aspect` | 0.2798 | 0.4062 | 1.2635 | 0.5532 | -0.0114 |
| `artist_size_depth` | 0.2813 | 0.4003 | 1.2407 | 0.5515 | -0.0099 |
| `baseline_base_existing_combo` | 0.2912 | 0.4063 | 1.2508 | 0.5530 | +0.0000 |
| `artist_size_generated_buckets` | 0.2942 | 0.4097 | 1.1955 | 0.5478 | +0.0030 |
| `full_plus_generated_buckets` | 0.2980 | 0.3982 | 1.0657 | 0.5464 | +0.0068 |
| `artist_size_material` | 0.3093 | 0.4263 | 1.2850 | 0.5634 | +0.0181 |

## Test 확인 결과

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | baseline 대비 MdAPE |
|---|---:|---:|---:|---:|---:|
| `artist_size_generated_buckets` | 0.3125 | 0.4952 | 1.5624 | 0.6373 | -0.0134 |
| `baseline_base_existing_combo` | 0.3259 | 0.4975 | 1.6086 | 0.6358 | +0.0000 |
| `full_plus_generated_buckets` | 0.3328 | 0.4772 | 1.4793 | 0.6248 | +0.0069 |
| `artist_size_depth` | 0.3372 | 0.4920 | 1.5565 | 0.6360 | +0.0113 |
| `artist_size_material` | 0.3373 | 0.5123 | 1.7290 | 0.6435 | +0.0114 |
| `artist_size_only` | 0.3467 | 0.5087 | 1.6310 | 0.6390 | +0.0208 |
| `artist_size_works` | 0.3523 | 0.4904 | 1.4616 | 0.6254 | +0.0264 |
| `artist_size_aspect` | 0.3599 | 0.5001 | 1.5861 | 0.6409 | +0.0340 |

## 코멘터리

- validation 기준 1위 후보는 `artist_size_only`이고, 기준 후보 `baseline_base_existing_combo` 대비 MdAPE 변화는 `-0.0134`이다.
- test 기준 1위 후보는 `artist_size_generated_buckets`이고, 기준 후보 `baseline_base_existing_combo` 대비 MdAPE 변화는 `-0.0134`이다.
- validation과 test의 1위가 다르면 즉시 교체하지 않고, 후속 조합/보정 후보로만 둔다.
- 피처 교환 실험은 모델을 바꾸는 실험이 아니라, 같은 모델에서 어떤 입력 정보 구조가 더 맞는지 확인하는 사전 검증이다.
