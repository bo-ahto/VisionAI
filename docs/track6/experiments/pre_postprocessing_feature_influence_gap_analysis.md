# 후처리 전 모델별 피처 영향도 검증 Gap 정리

- 작성일: 2026-06-01
- 목적: 후처리 실험 전에 모델별 피처 영향도 검증이 충분히 되었는지 확인하고, 아직 진행되지 않은 실험을 구분한다.
- 결론: 후처리 전에 추가 검증이 필요하다. 특히 최종 모델 기준의 `one-drop` 또는 `group-drop` ablation이 부족하다.

---

## 1. 왜 후처리 전에 확인해야 하는가

- 후처리는 모델이 반복적으로 높게 또는 낮게 예측하는 구간을 보정하는 작업이다.
- 보정 구간은 보통 피처 또는 피처 조합을 기준으로 만든다.
- 따라서 어떤 피처가 실제로 모델 성능에 필요한지 확인하지 않고 보정부터 진행하면, 중요하지 않은 피처를 기준으로 보정 구간을 만들 위험이 있다.
- 특히 CatBoost와 LightGBM은 트리 구조상 피처 조합을 자동으로 학습하므로, 단순 중요도만 보고 후처리 기준을 정하면 설명력이 약하다.
- 후처리 전에 최소한 다음 두 가지를 분리해서 확인해야 한다.

```text
모델 내부 해석: 이미 학습된 모델 안에서 어떤 피처가 예측값을 움직였는가?
성능 기여 검증: 해당 피처 또는 피처 그룹을 빼고 다시 학습해도 성능이 유지되는가?
```

---

## 2. 현재 최종 모델과 피처셋

| 영역 | 최종 모델 | 최종 피처셋 | 주요 피처 |
| --- | --- | --- | --- |
| Warm | HuberRegressor | `base_existing_combo` | width, height, depth, area, log_area, aspect_ratio, medium/support, artist_key |
| Cold CatBoost | CatBoostRegressor | `base_medium_shape` | size, depth/3D, medium/support, shape_bucket, medium_shape_bucket |
| Cold LightGBM | LGBMRegressor | `base_support_size` | size, depth/3D, medium/support, size_bucket, support_size_bucket |

---

## 3. 이미 진행된 실험

| 실험 | 상태 | 확인한 내용 | 한계 |
| --- | --- | --- | --- |
| T6-E003 Warm 작가 피처 ablation | 완료 | Warm에서 `artist_key`가 구조 피처 대비 성능을 크게 개선하는지 확인 | 최종 피처셋의 크기/재료/깊이/형태 그룹별 제거 실험은 아님 |
| T6-E005 피처 조합 ablation | 완료 | `base`, `base_existing_combo`, `base_medium_shape`, `base_support_size` 등 후보 조합 비교 | 최종 모델에서 특정 피처 그룹 하나를 제거하는 one-drop/group-drop 실험은 아님 |
| T6-E006 validation 후보 선정 | 완료 | Warm Huber, Cold CatBoost, Cold LightGBM의 최종 후보 피처셋 선정 | 후보 선정 결과이며 피처별 성능 기여 검증은 아님 |
| T6-E007 test confirmation | 완료 | 선택 후보의 test 성능 확인 | test 확인 결과이며 피처 제거 실험은 아님 |
| FINAL interpretability | 완료 | Warm 계수, Cold CatBoost SHAP/interaction, LightGBM permutation 등 해석 산출 | 모델 내부 해석 중심이며 제거 시 성능 변화는 직접 확인하지 않음 |
| CM1 Cold 상위 피처 조합별 모델군 비교 | 완료 | Cold 후보 피처 조합에서 CatBoost 성능이 좋은 조합 확인 | 최종 artifact의 `base_medium_shape` 기준 one-drop 실험은 아님 |
| T6-E022 Warm 피처 제거 ablation | 예정 | Warm 후보 피처 one-drop 계획 | 실행 결과 없음 |
| T6-E023 Cold 피처 제거 ablation | 예정 | Cold 후보 피처 one-drop 계획 | 실행 결과 없음. CatBoost 최종 피처셋 기준도 아님 |

---

## 4. 현재 실험 조합으로 알 수 있는 것과 없는 것

### 알 수 있는 것

- Warm에서는 `artist_key`가 중요한 기준선 역할을 한다.
- 후보 피처셋 중 Warm은 `base_existing_combo`, Cold CatBoost는 `base_medium_shape`, Cold LightGBM은 `base_support_size`가 선택됐다.
- CatBoost에서는 크기, 깊이/3D, medium/shape 조합이 예측 경로에 중요하게 나타난다.
- LightGBM에서는 size 계열과 support/size bucket이 성능과 tail risk에 중요하게 나타난다.
- 1차 해석 리포트로 모델 내부에서 어떤 피처가 예측값을 움직였는지는 확인했다.

### 아직 알기 어려운 것

- 최종 Warm Huber에서 `size group`을 빼면 성능이 얼마나 나빠지는가.
- 최종 Warm Huber에서 `medium/support group`을 빼도 성능이 유지되는가.
- 최종 Cold CatBoost에서 `shape_bucket`, `medium_shape_bucket`이 실제 성능 개선에 기여했는가.
- 최종 Cold CatBoost에서 `depth/3D group`을 제거하면 SHAP/interaction 해석과 일치하게 성능이 악화되는가.
- 최종 Cold LightGBM에서 `size_bucket`, `support_size_bucket`이 tail risk를 줄이는 데 실제로 기여했는가.
- 피처 중요도는 높지만 제거해도 성능이 유지되는 대체 가능 피처가 있는가.
- 피처 중요도는 낮지만 특정 tail 구간 안정화에 필요한 보조 피처가 있는가.

---

## 5. 후처리 전 필요한 추가 실험

### 5.1 Warm Huber group-drop ablation

목적:

- 선형 Huber에서 피처 그룹별 성능 기여를 확인한다.
- 계수/기여도 해석과 실제 제거 실험 결과가 일치하는지 확인한다.
- Warm 보정 기준을 `overall`, `pred_bin`, `size`, `medium/support`, `artist` 중 어디에 둘지 판단한다.

기준 모델:

```text
Warm Huber final = base_existing_combo
```

권장 실험:

| 실험 ID | 제거 그룹 | 제거 피처 | 기대 확인 |
| --- | --- | --- | --- |
| W-AB-01 | artist group | artist_key | Warm에서 작가 기준선이 여전히 필수인지 재확인 |
| W-AB-02 | size group | width_cm, height_cm, area_cm2, log_area | 크기 피처가 대표 오차와 p95에 얼마나 기여하는지 확인 |
| W-AB-03 | depth/3D group | depth_cm, has_depth, is_3d_candidate | 깊이/입체 정보가 Huber에서 실제 성능 기여가 있는지 확인 |
| W-AB-04 | medium/support group | medium_category, support_category, medium_support_bucket | 재료/지지체 보정 기준이 필요한지 확인 |
| W-AB-05 | shape/aspect group | aspect_ratio, is_extreme_aspect_ratio | 형태 피처가 독립적으로 필요한지 확인 |

판단 기준:

- 제거 후 MdAPE가 악화되면 해당 그룹은 성능 기여가 있다.
- 제거 후 p95가 악화되면 해당 그룹은 tail risk 관리에 필요하다.
- 제거해도 성능이 유지되면 후처리 기준으로 우선순위를 낮춘다.

---

### 5.2 Cold CatBoost group-drop ablation

목적:

- CatBoost의 SHAP/interaction 해석이 실제 성능 기여와 일치하는지 확인한다.
- `base_medium_shape`에서 어떤 피처 조합이 반드시 필요한지 구분한다.
- CatBoost 후처리 segment를 `size`, `depth`, `medium/shape`, `leaf/segment` 중 어디에 둘지 판단한다.

기준 모델:

```text
Cold CatBoost final = base_medium_shape
```

권장 실험:

| 실험 ID | 제거 그룹 | 제거 피처 | 기대 확인 |
| --- | --- | --- | --- |
| CB-AB-01 | size group | width_cm, height_cm, area_cm2, log_area | Cold에서 크기가 기본 가격대 역할을 하는지 검증 |
| CB-AB-02 | depth/3D group | depth_cm, has_depth, is_3d_candidate | size x depth interaction이 실제 성능에 필요한지 검증 |
| CB-AB-03 | medium/support base group | medium_category, support_category | 재료/지지체가 단독 기준으로 필요한지 확인 |
| CB-AB-04 | shape bucket group | shape_bucket | shape_bucket이 경로 분리에 기여하는지 확인 |
| CB-AB-05 | medium_shape group | medium_shape_bucket | medium x shape 조합이 CatBoost 성능에 기여하는지 확인 |
| CB-AB-06 | aspect group | aspect_ratio | 형태 비율 정보가 shape_bucket 없이도 필요한지 확인 |

판단 기준:

- SHAP/interaction 상위 피처를 제거했을 때 MdAPE 또는 p95가 악화되면 해석 신뢰도가 높아진다.
- SHAP은 높지만 제거해도 성능이 유지되면 대체 피처가 있다는 뜻이다.
- 제거 후 MdAPE는 유지되지만 p95가 악화되면 해당 피처는 일반 정확도보다 tail 안정성에 기여한다.

주의:

- CatBoost에서 제거 실험 결과는 피처 하나의 순수 독립 효과가 아니다.
- 피처를 빼면 트리 구조가 다시 학습되므로, 결과는 “해당 피처 그룹을 포함한 조합의 성능 기여”로 해석해야 한다.

---

### 5.3 Cold LightGBM group-drop ablation

목적:

- LightGBM이 size bucket과 support_size bucket에 얼마나 의존하는지 확인한다.
- leaf-wise 구조에서 tail risk를 만드는 피처와 줄이는 피처를 구분한다.
- LightGBM 후처리 기준을 `pred_bin`, `size_bucket`, `support_size_bucket`, `material/support` 중 어디에 둘지 판단한다.

기준 모델:

```text
Cold LightGBM final = base_support_size
```

권장 실험:

| 실험 ID | 제거 그룹 | 제거 피처 | 기대 확인 |
| --- | --- | --- | --- |
| LGB-AB-01 | size raw group | width_cm, height_cm, area_cm2, log_area | 원 크기 피처 의존도 확인 |
| LGB-AB-02 | size bucket group | size_bucket | 가격대 분할용 크기 bucket이 성능에 필요한지 확인 |
| LGB-AB-03 | support_size group | support_size_bucket | 지지체 x 크기 조합이 tail 안정화에 기여하는지 확인 |
| LGB-AB-04 | depth/3D group | depth_cm, has_depth, is_3d_candidate | 특정 입체 구간에서 leaf-wise 과분화가 생기는지 확인 |
| LGB-AB-05 | medium/support base group | medium_category, support_category | 재료/지지체 기본 정보의 성능 기여 확인 |
| LGB-AB-06 | aspect group | aspect_ratio | 형태 비율이 size bucket을 대체하거나 보완하는지 확인 |

판단 기준:

- 제거 후 MdAPE가 악화되면 일반 예측 정확도에 필요하다.
- 제거 후 p95만 악화되면 tail 안정화에 필요하다.
- 제거 후 p95가 좋아지면 해당 피처가 일부 구간에서 과분화를 만들 가능성이 있다.

---

## 6. 우선순위

| 우선순위 | 실험 | 이유 |
| --- | --- | --- |
| 1 | CB-AB-02 depth/3D 제거 | CatBoost 해석에서 size x depth interaction이 핵심이므로 검증 가치가 가장 큼 |
| 2 | CB-AB-05 medium_shape 제거 | CatBoost 최종 피처셋 이름 자체가 `base_medium_shape`이므로 조합 기여 확인 필요 |
| 3 | LGB-AB-03 support_size 제거 | LightGBM 최종 피처셋의 핵심 bucket이며 tail 안정화와 직접 연결 |
| 4 | LGB-AB-02 size_bucket 제거 | LightGBM의 size 의존도와 p95 위험을 구분하는 데 필요 |
| 5 | W-AB-04 medium/support 제거 | Warm 후처리에서 재료/지지체 보정 기준을 둘지 판단 가능 |
| 6 | W-AB-02 size 제거 | Huber 계수 해석에서 크기 그룹 기여 확인 |

---

## 7. 후처리와 연결하는 기준

| ablation 결과 | 후처리 판단 |
| --- | --- |
| 제거 시 MdAPE와 p95 모두 악화 | 해당 피처 그룹은 유지하고 보정 segment 후보로 사용 |
| 제거 시 MdAPE만 악화 | 일반 정확도에 중요하므로 모델 피처로 유지하되 후처리 우선순위는 중간 |
| 제거 시 p95만 악화 | tail risk 방어용 보정 segment 후보로 우선 검토 |
| 제거해도 성능 유지 | 후처리 기준으로 쓰는 우선순위를 낮춤 |
| 제거 시 성능 개선 | 해당 피처가 과분화/노이즈일 수 있으므로 피처셋 재검토 |

---

## 8. 최종 판단

- 지금까지의 실험은 후보 피처셋을 고르고 모델을 선택하기에는 충분하다.
- 하지만 후처리 기준을 설득력 있게 정하기에는 최종 모델 기준의 제거 실험이 부족하다.
- 따라서 후처리 본실험 전에 최소한 핵심 그룹만 대상으로 `group-drop ablation`을 먼저 수행하는 것이 맞다.
- 특히 Cold CatBoost와 Cold LightGBM은 트리 구조가 다르기 때문에 같은 피처라도 제거 실험 결과와 후처리 연결 방식이 달라야 한다.
- 이 실험을 통해 “왜 이 피처 조합을 기준으로 보정하는가”를 설명할 수 있어야 후처리 계획의 설득력이 높아진다.
