# PP-U5 Warm Huber 재료/지지체 중복 분리 검증

## 실험 계획

- 목적: Warm Huber에서 `medium_category`, `support_category`, `medium_support_bucket`을 함께 쓰는 현재 구조가 필요한지, 아니면 원본 피처와 조합 피처가 중복되는지 확인한다.
- 대상: `warm` 데이터, `huber` 모델.
- 통제 기준: 데이터 split, target(`ln_price_krw`), Huber 모델 설정, 평가 지표는 고정하고 재료/지지체 관련 피처만 바꾼다.
- 선택 기준: validation에서 후보를 고르고 test는 선택된 후보의 재현성 확인으로만 사용한다.
- 기대 결과: 재료/지지체 피처를 원본 중심으로 설명할지, 조합 bucket 중심으로 설명할지, 세 피처 동시 사용을 유지할지 판단한다.

## 후보 피처셋

| 후보 | 전략 | 피처 수 | 가설 |
|---|---|---:|---|
| `baseline_all_three` | 현재 기준 구조 | 13 | 현재 Warm Huber 기준 피처셋처럼 원본 재료, 원본 지지체, 조합 피처를 모두 사용 |
| `raw_medium_support_only` | 원본 재료/지지체만 사용 | 12 | 조합 피처 없이 원본 재료와 지지체만으로 충분한지 확인 |
| `combo_bucket_only` | 조합 피처만 사용 | 11 | 재료와 지지체를 각각 쓰지 않고 조합 bucket 하나로 설명 가능한지 확인 |
| `medium_only` | 재료만 사용 | 11 | 재료 대분류만으로 보조 신호가 충분한지 확인 |
| `support_only` | 지지체만 사용 | 11 | 지지체 대분류만으로 보조 신호가 충분한지 확인 |
| `no_material_support` | 재료/지지체 제거 | 10 | 재료/지지체 정보 자체가 Warm Huber에서 필요한지 재확인 |

## Validation 결과

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | baseline 대비 MdAPE |
|---|---:|---:|---:|---:|---:|
| `combo_bucket_only` | 0.2121 | 0.4350 | 1.3815 | 0.6532 | -0.0005 |
| `baseline_all_three` | 0.2126 | 0.4167 | 1.3194 | 0.6446 | +0.0000 |
| `medium_only` | 0.2147 | 0.4448 | 1.3669 | 0.6584 | +0.0021 |
| `support_only` | 0.2154 | 0.4345 | 1.3015 | 0.6562 | +0.0028 |
| `no_material_support` | 0.2170 | 0.4450 | 1.3546 | 0.6651 | +0.0044 |
| `raw_medium_support_only` | 0.2181 | 0.4351 | 1.3357 | 0.6520 | +0.0055 |

## Test 확인 결과

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | baseline 대비 MdAPE |
|---|---:|---:|---:|---:|---:|
| `support_only` | 0.2165 | 0.4944 | 2.0386 | 0.6078 | -0.0109 |
| `raw_medium_support_only` | 0.2165 | 0.4955 | 2.0382 | 0.6097 | -0.0109 |
| `medium_only` | 0.2252 | 0.4958 | 1.9790 | 0.6148 | -0.0022 |
| `no_material_support` | 0.2253 | 0.4987 | 1.9928 | 0.6148 | -0.0021 |
| `combo_bucket_only` | 0.2273 | 0.4931 | 2.0145 | 0.6054 | -0.0001 |
| `baseline_all_three` | 0.2274 | 0.4952 | 2.0130 | 0.6081 | +0.0000 |

## 코멘터리

- validation 기준 1위 후보는 `combo_bucket_only`이고, 기준 후보 `baseline_all_three` 대비 MdAPE 변화는 `-0.0005`이다.
- test 기준 1위 후보는 `support_only`이고, 기준 후보 `baseline_all_three` 대비 MdAPE 변화는 `-0.0109`이다.
- validation과 test의 1위가 다르면 즉시 교체하지 않고, 후속 조합/보정 후보로만 둔다.
- `combo_bucket_only`는 validation MdAPE가 가장 낮지만 MAPE, p95_APE, RMSE_log는 현재 기준 구조보다 악화됐다.
- `support_only`와 `raw_medium_support_only`는 test MdAPE가 가장 낮지만 validation에서는 현재 기준 구조보다 나빠졌다.
- `no_material_support`는 validation MdAPE가 `0.2170`으로 악화되어 재료/지지체 그룹 자체는 유지할 근거가 있다.
- 현재 기준 구조는 validation에서 MdAPE 2위이면서 MAPE, p95_APE, RMSE_log가 가장 안정적이다.
- 결론: 세 피처 동시 사용이 압도적으로 우세하다고 보기는 어렵지만, 현재 기준 구조를 바로 단순화할 만큼 일관된 개선도 확인되지 않았다. 따라서 Warm Huber 기준 피처셋은 현 구조를 유지하고, 조합 피처 단독 또는 지지체 단독 구조는 후속 안정성 검증 후보로만 둔다.
