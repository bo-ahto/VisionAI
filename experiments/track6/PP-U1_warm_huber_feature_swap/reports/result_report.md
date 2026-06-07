# PP-U1 Warm Huber 피처 교환/축소/확장 비교

## 실험 계획

- 목적: 기존 실험에서 확인된 피처 영향도를 바탕으로 피처셋을 교환, 축소, 확장했을 때 성능이 어떻게 바뀌는지 확인한다.
- 대상: `warm` 데이터, `huber` 모델.
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
| `artist_size_depth` | 0.2093 | 0.4439 | 1.3632 | 0.6654 | -0.0032 |
| `baseline_base_existing_combo` | 0.2126 | 0.4167 | 1.3194 | 0.6446 | +0.0000 |
| `artist_size_only` | 0.2155 | 0.4549 | 1.4478 | 0.6692 | +0.0029 |
| `artist_size_aspect` | 0.2159 | 0.4556 | 1.4631 | 0.6691 | +0.0033 |
| `full_plus_generated_buckets` | 0.2193 | 0.4131 | 1.2415 | 0.6493 | +0.0067 |
| `artist_size_generated_buckets` | 0.2203 | 0.4421 | 1.3380 | 0.6510 | +0.0077 |
| `artist_size_works` | 0.2215 | 0.4438 | 1.3963 | 0.6724 | +0.0089 |
| `artist_size_material` | 0.2240 | 0.4210 | 1.4065 | 0.6438 | +0.0115 |

## Test 확인 결과

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | baseline 대비 MdAPE |
|---|---:|---:|---:|---:|---:|
| `full_plus_generated_buckets` | 0.2131 | 0.4814 | 1.8591 | 0.6072 | -0.0143 |
| `artist_size_generated_buckets` | 0.2190 | 0.5014 | 2.0341 | 0.6120 | -0.0084 |
| `artist_size_works` | 0.2218 | 0.4892 | 1.9108 | 0.6233 | -0.0056 |
| `artist_size_only` | 0.2247 | 0.5050 | 1.9728 | 0.6234 | -0.0027 |
| `artist_size_material` | 0.2247 | 0.4981 | 2.0119 | 0.6106 | -0.0027 |
| `artist_size_aspect` | 0.2259 | 0.5041 | 1.9756 | 0.6230 | -0.0015 |
| `baseline_base_existing_combo` | 0.2274 | 0.4952 | 2.0130 | 0.6081 | +0.0000 |
| `artist_size_depth` | 0.2275 | 0.5011 | 1.9227 | 0.6159 | +0.0001 |

## 코멘터리

- validation 기준 1위 후보는 `artist_size_depth`이고, 기준 후보 `baseline_base_existing_combo` 대비 MdAPE 변화는 `-0.0032`이다.
- test 기준 1위 후보는 `full_plus_generated_buckets`이고, 기준 후보 `baseline_base_existing_combo` 대비 MdAPE 변화는 `-0.0143`이다.
- validation과 test의 1위가 다르면 즉시 교체하지 않고, 후속 조합/보정 후보로만 둔다.
- 피처 교환 실험은 모델을 바꾸는 실험이 아니라, 같은 모델에서 어떤 입력 정보 구조가 더 맞는지 확인하는 사전 검증이다.
