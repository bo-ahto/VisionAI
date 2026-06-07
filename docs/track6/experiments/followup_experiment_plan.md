# Track6 후속 실험 계획

- 목적: Warm / Cold 최종 후보 모델을 실제 서비스에 적용하기 전, 모델별 피처 영향도 검증, 후처리, 가격 범위, 신뢰도, 추가 작가 정보 효과를 순서대로 검증한다.
- 기준 문서:
  - `final_model_decision_and_enhancement_plan.md`
  - `junior_presentation_onboarding_guide.md`
  - `executive_model_interpretation_deep_dive_presentation.md`
  - `pre_postprocessing_feature_influence_gap_analysis.md`
  - `huber_quantile_catboost_mape_optimization_plan.md`
- 기준 데이터: Track6 고정 split
- 현재 기준 모델:
  - Warm: `Huber`
  - Cold 1순위: `CatBoost`
  - Cold 보조/비교: `LightGBM`
- 현재 기준 피처:
  - Warm Huber: `base_existing_combo`
    - `width_cm`, `height_cm`, `depth_cm`, `area_cm2`, `log_area`, `aspect_ratio`, `has_depth`, `is_3d_candidate`, `medium_category`, `support_category`, `medium_support_bucket`, `is_extreme_aspect_ratio`, `artist_key`
  - Cold CatBoost: `base_medium_shape`
    - `width_cm`, `height_cm`, `depth_cm`, `area_cm2`, `log_area`, `aspect_ratio`, `has_depth`, `is_3d_candidate`, `medium_category`, `support_category`, `shape_bucket`, `medium_shape_bucket`
  - Cold LightGBM: `base_support_size`
    - `width_cm`, `height_cm`, `depth_cm`, `area_cm2`, `log_area`, `aspect_ratio`, `has_depth`, `is_3d_candidate`, `medium_category`, `support_category`, `size_bucket`, `support_size_bucket`

## 1. 후속 실험을 하는 이유

- Warm은 최종 artifact 기준 Test MdAPE가 약 `22.4%` 수준으로 Cold보다 안정적이다.
- Cold는 CatBoost/LightGBM 모두 Test MdAPE가 약 `48%` 수준으로 Warm보다 훨씬 어렵다.
- 특히 Cold는 p95_APE가 커서 큰 오차가 발생하는 작품이 존재한다.
- 따라서 모델만 고르는 것으로 끝내면 안 된다.
- 예측 가격을 서비스에서 어떻게 보여줄지, 어떤 경우에 신뢰도를 낮출지, 어떤 외부 정보를 더 수집해야 할지 추가 검증이 필요하다.

## 2. 공통 실험 원칙

- Warm / Cold 결과는 합치지 않고 따로 판단한다.
- validation 결과로 보정 기준과 신뢰도 기준을 정한다.
- test는 최종 확인용으로만 사용한다.
- 가격 label은 학습 target과 평가 지표 계산에만 사용한다.
- 출처 자체는 모델 입력 피처로 사용하지 않는다.
- 운영에서 입력할 수 없거나 내부 DB로 자동 생성할 수 없는 피처는 최종 후보에서 제외한다.
- 모든 후속 실험은 실험 폴더, 설정 파일, 사용 데이터, 결과 CSV, HTML 리포트를 남긴다.

## 3. PRE-PP 모델별 피처 영향도 검증

### 목적

- 후처리 기준으로 사용할 피처/구간이 실제로 모델 성능에 필요한지 확인한다.
- 후처리 전에 `왜 이 피처 조합을 기준으로 보정하는가`를 설명할 수 있게 만든다.
- 모델 내부 해석과 성능 기여 검증을 분리한다.

```text
모델 내부 해석: SHAP, interaction, coefficient, permutation
성능 기여 검증: one-drop 또는 group-drop ablation
```

### 필요성

- 기존 실험은 후보 피처셋 비교와 모델 내부 해석 중심이다.
- 최종 모델 기준으로 특정 피처 그룹을 제거했을 때 성능이 어떻게 변하는지는 충분히 확인되지 않았다.
- CatBoost와 LightGBM은 피처 조합을 자동으로 학습하므로, 후처리 segment를 정하기 전에 group-drop 검증이 필요하다.

### 우선 실험

| 순서 | 실험 ID | 대상 모델 | 제거 그룹 | 목적 |
|---:|---|---|---|---|
| 1 | `CB-AB-02` | Cold CatBoost | `depth_cm`, `has_depth`, `is_3d_candidate` | CatBoost의 size x depth 경로가 실제 성능에 필요한지 확인 |
| 2 | `CB-AB-05` | Cold CatBoost | `medium_shape_bucket` | medium/shape 조합이 최종 CatBoost 피처셋에 필요한지 확인 |
| 3 | `LGB-AB-03` | Cold LightGBM | `support_size_bucket` | support x size 조합이 tail 안정화에 기여하는지 확인 |
| 4 | `LGB-AB-02` | Cold LightGBM | `size_bucket` | LightGBM의 size bucket 의존도와 p95 위험을 확인 |
| 5 | `W-AB-04` | Warm Huber | `medium_category`, `support_category`, `medium_support_bucket` | Warm 재료/지지체 보정 기준의 필요성 확인 |
| 6 | `W-AB-02` | Warm Huber | `width_cm`, `height_cm`, `area_cm2`, `log_area` | Warm size 그룹 기여도 확인 |

### 판단 기준

- 제거 후 MdAPE가 악화되면 해당 피처 그룹은 일반 예측 정확도에 필요하다.
- 제거 후 p95_APE가 악화되면 해당 피처 그룹은 큰 오차 방어 또는 tail risk 관리에 필요하다.
- 제거해도 성능이 유지되면 후처리 기준 우선순위를 낮춘다.
- 제거 후 성능이 좋아지면 해당 피처 그룹은 과분화 또는 노이즈 가능성이 있으므로 최종 피처셋을 재검토한다.

### 결과 활용

- CatBoost 후처리 segment를 `depth/3D`, `medium_shape`, `leaf/segment` 중 어디에 둘지 결정한다.
- LightGBM tail 안정화 기준을 `size_bucket`, `support_size_bucket`, `pred_bin` 중 어디에 둘지 결정한다.
- Warm Huber 보정이 전체 residual 보정으로 충분한지, 재료/지지체/크기 구간 보정까지 필요한지 결정한다.

## 4. PRE-MODEL Warm/Cold CatBoost 적합성 검증

### 목적

- Warm과 Cold 모두에서 CatBoost의 대칭 트리 구조가 가격 예측에 더 적합한지 확인한다.
- 특히 Warm에서는 작가별 작품 크기 구간과 작가 x 크기 x 재료/형태 조합을 CatBoost가 더 잘 학습하는지 검증한다.
- Cold에서는 기존 CatBoost 후보를 유지하되, 조건별 조합 학습이 실제 성능 개선으로 이어지는지 재확인한다.

### 실험 가설

```text
CatBoost는 대칭 트리 구조를 사용한다.
같은 깊이의 노드들이 같은 split 조건을 반복 적용하기 때문에,
작가, 크기, 재료, 형태 같은 조건 조합을 안정적으로 나눌 수 있다.

따라서 Warm에서는 작가별 작품 크기 구간을 더 잘 나눌 수 있고,
Cold에서는 작가 기준선이 없는 대신 작품 자체 조건 조합을 더 잘 나눌 수 있다.
```

쉽게 말하면 다음과 같다.

```text
Huber는 작가 효과와 크기 효과를 더해서 예측한다.
CatBoost는 "어떤 작가인가, 그 작가의 작품이 어느 크기 구간인가, 재료와 형태가 무엇인가"를 조건 조합으로 나눠 예측한다.
```

### 우선 실험

| 순서 | 실험 ID | 대상 | 비교 기준 | 목적 |
|---:|---|---|---|---|
| 1 | `W-CB-01` | Warm CatBoost `base_existing_combo` | Warm Huber `base_existing_combo` | 같은 피처셋에서 모델 구조만 바꿨을 때 개선되는지 확인 |
| 2 | `W-CB-02` | Warm CatBoost `artist_key + size` 계열 | Warm Huber 보조 후보 | 작가별 크기 구간을 CatBoost가 더 잘 나누는지 확인 |
| 3 | `W-CB-03` | Warm CatBoost `artist_key + size + material/support` | Warm Huber 기준 후보 | 작가 x 크기 x 재료/지지체 조합 효과 확인 |
| 4 | `C-CB-01` | Cold CatBoost `base_medium_shape` 재검증 | Cold LightGBM `base_support_size` | Cold CatBoost가 대표 오차 또는 p95에서 여전히 유효한지 확인 |
| 5 | `C-CB-02` | Cold CatBoost 조건별 segment 진단 | Cold CatBoost 전체 모델 | size, depth/3D, medium_shape 구간별 반복 오차 확인 |

### 판단 기준

- validation MdAPE가 개선되면 대표 정확도 개선 후보로 본다.
- p95_APE가 개선되면 큰 오차 방어 후보로 본다.
- OOF와 validation 방향이 다르면 과적합 가능성을 의심한다.
- test만 좋아지고 validation이 나쁘면 기준 모델로 바로 채택하지 않는다.
- 작가 수나 segment 표본이 부족한 구간에서만 개선되면 운영 후보가 아니라 추가 분석 후보로 둔다.

### 결과 활용

- Warm CatBoost가 Huber보다 안정적으로 좋으면 Warm 기준 모델 후보를 재검토한다.
- Warm CatBoost가 일부 구간에서만 좋으면 모델 교체보다 구간별 보정 또는 모델 선택 정책으로 연결한다.
- Cold CatBoost가 특정 segment에서 반복 오차를 보이면 leaf/segment residual 보정 설계에 반영한다.

## 5. PRE-SPLIT-CB Warm/Cold CatBoost 구분 학습 보정 실험

### 목적

- Warm과 Cold 모두에서 CatBoost를 조건별로 구분 학습했을 때 보정값이 더 작고 안정적으로 나오는지 확인한다.
- 전체 모델 하나로 예측한 뒤 보정하는 방식과, 조건별 CatBoost 모델을 따로 학습한 뒤 보정하는 방식을 비교한다.
- 최종 목적은 모델 자체 성능 개선뿐 아니라, 후처리에 필요한 보정값이 더 명확하고 작아지는지 확인하는 것이다.

### 실험 가설

```text
전체 CatBoost 모델 하나는 서로 다른 가격 구조를 가진 작품군을 한 모델 안에서 함께 학습한다.
반면 조건별로 CatBoost를 나누어 학습하면 각 모델의 시작 기준값, 트리 분기, leaf 값이 해당 구간에 맞춰진다.

따라서 구분 학습 CatBoost는 전체 모델보다 구간별 residual이 작아질 수 있고,
후처리에서 필요한 보정값도 더 안정적으로 계산될 수 있다.
```

쉽게 말하면 다음과 같다.

```text
전체 CatBoost:
모든 Warm 또는 Cold 작품을 한 모델이 한꺼번에 학습

구분 학습 CatBoost:
작가 학습량, 작품 크기, 2D/3D, 재료/형태 조건별로 나누어
각 구간에 맞는 CatBoost를 따로 학습
```

### 우선 실험

| 순서 | 실험 ID | 대상 | 구분 학습 기준 | 비교 기준 | 목적 |
|---:|---|---|---|---|---|
| 1 | `SPLIT-WCB-01` | Warm CatBoost | size_bucket | Warm CatBoost 전체 모델 | 작가가 있는 Warm에서도 크기 구간별 CatBoost가 더 안정적인지 확인 |
| 2 | `SPLIT-WCB-02` | Warm CatBoost | artist_works_bucket | Warm CatBoost 전체 모델 | 작가 학습량이 많은/적은 구간별 가격 구조 차이 확인 |
| 3 | `SPLIT-WCB-03` | Warm CatBoost | artist_size_segment | Warm CatBoost 전체 모델 | 작가별 크기 구간을 따로 학습하면 보정값이 줄어드는지 확인 |
| 4 | `SPLIT-CB-01` | Cold CatBoost | size_bucket | Cold CatBoost 전체 모델 | Cold 크기 구간별 기준 가격대 차이 확인 |
| 5 | `SPLIT-CB-02` | Cold CatBoost | depth_3d_segment | Cold CatBoost 전체 모델 | 2D/3D 후보를 따로 학습하면 큰 오차가 줄어드는지 확인 |
| 6 | `SPLIT-CB-03` | Cold CatBoost | medium_shape_bucket | Cold CatBoost 전체 모델 | 재료/형태 조합별 가격 구조 차이 확인 |

### 예측값과 보정값 산출 방식

각 실험은 같은 순서로 진행한다.

```text
1. train을 구분 기준별로 나눈다.
2. 각 구간별 CatBoost 모델을 따로 학습한다.
3. validation도 같은 기준으로 나눈다.
4. 각 validation 샘플은 자기 구간에 맞는 CatBoost 모델로 pred_log를 생성한다.
5. residual_log = actual_log - pred_log를 계산한다.
6. 구간별 median(residual_log)를 보정값으로 계산한다.
7. 구분 학습 전/후의 보정값 크기와 성능을 비교한다.
```

### 비교할 결과

| 비교 항목 | 확인 목적 |
|---|---|
| 전체 CatBoost 보정 전 성능 | 기존 기준 모델의 원 성능 |
| 전체 CatBoost + segment 보정 성능 | 모델은 하나로 두고 보정만 상세화했을 때 효과 |
| 구분 학습 CatBoost 보정 전 성능 | 조건별 모델 학습 자체가 성능을 개선하는지 |
| 구분 학습 CatBoost + segment 보정 성능 | 조건별 모델과 조건별 보정을 함께 썼을 때 효과 |
| median_residual_log 절대값 | 구분 학습 후 필요한 보정값이 줄어드는지 |
| segment별 rows | 구간별 모델을 학습할 만큼 데이터가 충분한지 |

### 안전장치

- 구분 학습 모델은 segment train rows가 충분한 경우에만 학습한다.
- 기본 기준은 `train rows >= 300`, `validation rows >= 50`으로 둔다.
- 기준보다 작으면 해당 구간은 전체 CatBoost 모델로 fallback한다.
- validation만 좋아지고 test에서 나빠지면 구분 학습은 보류한다.
- 보정값이 너무 크면 모델이 구간을 제대로 학습하지 못한 것으로 보고 위험 구간으로 표시한다.

### 판단 기준

- 구분 학습 CatBoost가 전체 CatBoost보다 validation MdAPE 또는 p95_APE를 개선하면 후보로 둔다.
- 성능 개선이 작더라도 median_residual_log 절대값이 줄면 보정 안정성 후보로 둔다.
- 특정 구간에서만 개선되면 전체 모델 교체가 아니라 모델 선택 또는 구간별 보정 정책으로 연결한다.
- 표본 수가 부족한 구간은 모델 분리 대상이 아니라 correction map 또는 fallback 보정 대상으로 둔다.

### 결과 활용

- Warm에서 CatBoost 구분 학습이 유효하면 Huber 유지 여부를 재검토한다.
- Warm에서 특정 작가/크기 구간만 유효하면 전체 모델 교체 대신 조건별 모델 선택 정책으로 연결한다.
- Cold에서 구분 학습이 유효하면 Cold CatBoost segment 보정의 기준을 더 세분화한다.
- 구분 학습이 유효하지 않으면 전체 CatBoost 모델 + 상세 correction map 방식으로 후처리를 유지한다.

## 6. PRE-CAL 상세 보정값 산출 실험

### 목적

- 전체 보정값 하나만 보는 것이 아니라, 모델별/구간별로 반복 오차가 있는지 확인한다.
- 각 구간의 로그 residual 중앙값을 보정값으로 산출해, 후처리에서 실제로 사용할 수 있는 correction map을 만든다.
- 가격 범위, 신뢰도, 모델 라우팅 실험 전에 어떤 구간이 높게/낮게 치우치는지 먼저 파악한다.

### 기본 계산식

```text
pred_log = model.predict(features)
residual_log = actual_log - pred_log
segment_correction = median(residual_log in same segment)
corrected_pred_log = pred_log + segment_correction
corrected_pred_price = exp(corrected_pred_log)
```

여기서 `median(residual_log in same segment)`는 같은 구간에 속한 validation 샘플들의 residual_log 중앙값이다.

### 우선 실험

| 순서 | 실험 ID | 대상 모델 | segment 기준 | 목적 |
|---:|---|---|---|---|
| 1 | `CAL-W-01` | Warm Huber | overall, pred_bin, size_bucket | 전체/예측가/크기 구간별 보정값 산출 |
| 2 | `CAL-W-02` | Warm Huber | artist_works_bucket, artist_size_segment | 작가 학습량과 작가별 크기 구간 보정 가능성 확인 |
| 3 | `CAL-WCB-01` | Warm CatBoost 후보 | pred_bin, size_bucket, artist_size_segment, leaf_segment | Warm CatBoost가 잡은 작가/크기 조건 조합의 반복 오차 확인 |
| 4 | `CAL-SPLIT-WCB-01` | Warm 구분 학습 CatBoost | split_segment, artist_size_segment, leaf_segment | 구분 학습 후에도 남는 보정값 확인 |
| 5 | `CAL-CB-01` | Cold CatBoost | leaf_segment, medium_shape_bucket, shape_bucket, overall | CatBoost 대칭 트리 segment 기반 보정값 산출 |
| 6 | `CAL-SPLIT-CB-01` | Cold 구분 학습 CatBoost | split_segment, leaf_segment, medium_shape_bucket | 구분 학습 후에도 남는 보정값 확인 |
| 7 | `CAL-LGB-01` | Cold LightGBM | pred_bin, size_bucket, support_size_bucket, tail_risk_segment | LightGBM tail 구간 보정값 산출 |

### 산출물

각 실험은 correction map을 남긴다.

| 컬럼 | 의미 |
|---|---|
| `model_name` | 보정 대상 모델 |
| `segment_type` | 보정 구간 종류 |
| `segment_value` | 실제 구간값 |
| `rows` | 해당 구간 validation 샘플 수 |
| `median_residual_log` | 해당 구간 보정값 |
| `correction_applied_rate` | 보정 적용 가능 비율 |
| `MdAPE_before` | 보정 전 대표 오차 |
| `MdAPE_after` | 보정 후 대표 오차 |
| `p95_APE_before` | 보정 전 큰 오차 |
| `p95_APE_after` | 보정 후 큰 오차 |
| `RMSE_log_before` | 보정 전 로그 오차 |
| `RMSE_log_after` | 보정 후 로그 오차 |

### 안전장치

- segment별 validation 샘플 수가 너무 적으면 해당 보정값은 사용하지 않는다.
- 기본 기준은 `rows >= 50`으로 둔다.
- `rows < 50`이면 상위 fallback 보정값을 사용한다.
- 보정값이 너무 크면 과보정 위험이 있으므로 cap을 적용한다.

```text
correction_capped = clip(segment_correction, -0.30, +0.30)
```

### fallback 구조

| 모델 | fallback 순서 |
|---|---|
| Warm Huber | size_bucket -> pred_bin -> overall |
| Warm CatBoost | artist_size_segment -> size_bucket -> pred_bin -> overall |
| Cold CatBoost | leaf_segment -> medium_shape_bucket -> shape_bucket -> overall |
| Cold LightGBM | support_size_bucket -> size_bucket -> pred_bin -> overall |

### 판단 기준

- validation에서 보정값을 계산하고 test에는 같은 보정값을 그대로 적용한다.
- validation과 test에서 MdAPE 또는 p95_APE 개선 방향이 같으면 후보로 둔다.
- validation만 좋아지고 test가 나빠지면 과적합 가능성으로 보류한다.
- MdAPE가 소폭 나빠져도 p95_APE가 크게 개선되면 신뢰도/가격 범위 실험과 연결한다.

### 결과 활용

- 실제 후처리 실험에서 어떤 segment 보정부터 적용할지 결정한다.
- 가격 범위 실험에서 구간별 범위 폭을 다르게 줄 수 있는지 판단한다.
- 신뢰도 실험에서 보정값이 크거나 불안정한 구간을 낮은 신뢰도 후보로 사용한다.

## 7. PP-J 모델별 커스텀 보정 실험

### 목적

- Huber, CatBoost, LightGBM은 가격을 예측하는 구조가 다르다.
- 따라서 모든 모델에 같은 보정 방식을 적용하면 `왜 이 보정이 이 모델에 맞는지` 설명하기 어렵다.
- PRE-CAL에서 만든 보정값 지도를 바탕으로 모델 구조에 맞는 커스텀 보정을 검증한다.

### 실험 가설

```text
Warm Huber는 선형 모델이므로 피처별 계수와 기여도 구간을 기준으로 보정하는 것이 자연스럽다.
CatBoost는 대칭 트리 구조이므로 leaf와 조건 조합 구간을 기준으로 보정하는 것이 자연스럽다.
LightGBM은 leaf-wise 방식으로 세밀한 구간을 만들기 쉬우므로 고가/큰 오차 tail 구간을 별도로 보정하는 것이 자연스럽다.
```

쉽게 말하면 다음과 같다.

```text
Huber 보정:
어떤 피처가 예측 가격을 얼마나 올리고 내렸는지 보고, 그 기여가 큰 구간을 보정한다.

CatBoost 보정:
모델이 나눈 조건 조합, 즉 leaf 또는 작가 x 크기 x 재료 구간에서 반복 오차를 찾는다.

LightGBM 보정:
세밀하게 나뉜 고가/극단 구간에서 크게 틀리는 패턴을 줄인다.
```

### 우선 실험

| 순서 | 실험 ID | 대상 모델 | 보정 기준 | 목적 |
|---:|---|---|---|---|
| 1 | `PP-J1` | Warm Huber | 큰 오차 구간, pred_bin, size_bucket | Huber가 낮은 영향력으로 처리한 큰 오차 구간을 보정 |
| 2 | `PP-J2` | Warm Huber | size/medium/artist 계수 기여도 구간 | 선형 모델의 피처별 기여도와 residual을 직접 연결 |
| 3 | `PP-J3` | Warm CatBoost 후보 | leaf_segment, artist_size_segment | Warm CatBoost가 나눈 작가 x 크기 조건 조합의 반복 오차 보정 |
| 4 | `PP-J4` | Cold CatBoost | leaf_segment, medium_shape_bucket, shape_bucket | CatBoost leaf 표본 수와 반복 오차를 이용한 보정/fallback 검증 |
| 5 | `PP-J5` | Cold CatBoost | depth_3d_segment, size_bucket, medium_shape_bucket | 2D/3D와 크기 조합에서 발생하는 큰 오차 보정 |
| 6 | `PP-J6` | Cold LightGBM | high pred_bin, small leaf risk, support_size_bucket | LightGBM의 고가/작은 leaf 위험 구간 보정 |

### 판단 기준

- PRE-CAL에서 표본 수가 충분한 구간만 보정 후보로 사용한다.
- 기본 기준은 validation rows `>= 50`이다.
- 구간 표본이 부족하면 상위 구간 보정값으로 fallback한다.
- 보정값은 validation에서만 계산하고 test에는 그대로 적용한다.
- MdAPE가 개선되거나 p95_APE가 줄어야 한다.
- MdAPE가 소폭 나빠지더라도 p95_APE가 명확히 줄면 가격 범위/신뢰도 실험과 연결한다.
- 보정값이 너무 크면 cap을 적용하고, 해당 구간은 낮은 신뢰도 후보로 표시한다.

### 결과 활용

- Warm Huber는 전체 중앙값 보정만으로 충분한지, 계수 기여도 기반 보정이 필요한지 결정한다.
- Warm CatBoost가 유효하면 leaf/artist-size 보정을 통해 Huber 대체 또는 조건부 적용 가능성을 본다.
- Cold CatBoost는 leaf/medium-shape fallback 구조를 확정한다.
- Cold LightGBM은 고가/tail 위험 방어용 보조 모델 또는 보정 후보로 남길지 결정한다.

## 8. E1 Warm 가격 범위 보정 실험

### 목적

- Warm 예측 가격 주변에 어느 정도의 가격 범위를 붙이면 적절한지 확인한다.
- 단일 예측 가격만 보여줘도 되는지, 참고 범위를 함께 보여줘야 하는지 판단한다.

### 사용 모델

- Warm 1차 후보: `Huber`

### 사용 피처

- `width_cm`
- `height_cm`
- `depth_cm`
- `area_cm2`
- `log_area`
- `aspect_ratio`
- `has_depth`
- `is_3d_candidate`
- `medium_category`
- `support_category`
- `medium_support_bucket`
- `is_extreme_aspect_ratio`
- `artist_key`

### 실험 방법

- Warm validation 데이터에서 예측값을 생성한다.
- 실제 가격과 예측 가격의 오차 분포를 계산한다.
- coverage 기준을 여러 개로 비교한다.
  - 70% coverage
  - 80% coverage
  - 90% coverage
- 각 coverage에서 필요한 가격 범위 폭을 계산한다.

### 확인 지표

- coverage
- interval width
- MdAPE
- p95_APE
- Within_30

### 판단 기준

- 목표 coverage에 실제 coverage가 가까우면 범위 보정 후보로 둔다.
- 가격 범위가 지나치게 넓으면 서비스 표현 방식 재검토가 필요하다.
- MdAPE가 기존 후보 대비 악화되지 않아야 한다.

### 결과 활용

- Warm 서비스 화면에서 `예측가 + 참고 범위` 제공 여부를 결정한다.
- Warm 가격 범위의 기본 폭을 정한다.

## 9. E2 Cold 가격 범위 보정 실험

### 목적

- Cold 예측값을 단일 가격으로 보여도 되는지 확인한다.
- Cold에 반드시 가격 범위와 낮은 신뢰도 문구를 붙여야 하는지 판단한다.

### 사용 모델

- Cold 1차 후보: `CatBoost`
- Cold 보조 후보: `LightGBM`

### 사용 피처

- CatBoost: `base_medium_shape`
  - `width_cm`, `height_cm`, `depth_cm`, `area_cm2`, `log_area`, `aspect_ratio`, `has_depth`, `is_3d_candidate`, `medium_category`, `support_category`, `shape_bucket`, `medium_shape_bucket`
- LightGBM: `base_support_size`
  - `width_cm`, `height_cm`, `depth_cm`, `area_cm2`, `log_area`, `aspect_ratio`, `has_depth`, `is_3d_candidate`, `medium_category`, `support_category`, `size_bucket`, `support_size_bucket`

### 실험 방법

- Cold validation 데이터에서 예측값을 생성한다.
- 실제 가격과 예측 가격의 오차 분포를 계산한다.
- Cold 전체와 주요 slice별 가격 범위를 따로 계산한다.
- coverage 기준을 여러 개로 비교한다.
  - 70% coverage
  - 80% coverage
  - 90% coverage

### 확인 지표

- coverage
- interval width
- MdAPE
- p95_APE
- Within_30
- slice별 coverage

### 판단 기준

- 80% coverage 기준 범위가 실무적으로 감당 가능한지 확인한다.
- 특정 구간에서 범위가 과도하게 넓으면 고위험 구간으로 분리한다.
- Cold 전체 범위가 너무 넓으면 단일 가격 중심 서비스는 보류한다.

### 결과 활용

- Cold 예측 결과를 `단일 가격`, `가격 범위`, `참고용 추정` 중 어떤 형태로 보여줄지 결정한다.

## 10. E3 Cold 신뢰도 라우팅 실험

### 목적

- Cold 작품을 저위험 / 고위험 구간으로 나눌 수 있는지 확인한다.
- Cold 전체에 같은 안내 문구를 쓰지 않고, 조건별로 신뢰도 표현을 다르게 하기 위함이다.

### 후보 기준

- 작가 메타 정보 보유량
- 활동량/인지도 정보 존재 여부
- 작품 크기 극단값 여부
- NANT 재료/지지체 분류 성공 여부
- CatBoost depth/medium_shape ablation 결과
- LightGBM size/support_size ablation 결과
- 예측 가격대별 반복 오차 여부

### 실험 방법

- Cold validation 또는 test 결과를 기준별 slice로 나눈다.
- slice별 성능을 비교한다.
- 저위험 후보와 고위험 후보를 분리한다.

### 확인 지표

- slice별 MdAPE
- slice별 p95_APE
- slice별 Within_30
- slice별 sample 수

### 판단 기준

- 특정 slice의 p95_APE가 전체보다 크게 높으면 고위험 구간으로 본다.
- 특정 slice의 MdAPE가 전체보다 낮고 sample 수가 충분하면 저위험 구간으로 본다.
- sample 수가 너무 적으면 결론이 아니라 관찰 결과로만 남긴다.

### 결과 활용

- Cold 결과에 `신뢰도 높음 / 보통 / 낮음`을 붙이는 기준을 만든다.
- 고위험 Cold 작품에는 더 넓은 가격 범위 또는 주의 문구를 붙인다.

## 11. E4 외부 작가 DB 보강 후 재실험

### 목적

- 외부 작가 정보가 Cold 성능을 실제로 개선하는지 확인한다.
- 추가 수집이 필요한 작가 DB 항목의 우선순위를 정한다.

### 우선 수집 항목

- 개인전 수
- 단체전 수
- 아트페어 참여 수
- 주요 기관 전시 여부
- 수상 이력
- 레지던시 이력
- 언론/검색량
- 갤러리 소속 여부
- 전속 여부

### 실험 방법

- 기존 Cold 1차 후보에 외부 작가 메타 피처를 추가한다.
- 기존 후보와 동일 split에서 비교한다.
- 결측이 많은 변수는 원값과 결측 여부 flag를 함께 둔다.
- 메타가 있는 작품만 골라 학습하거나 평가하지 않는다.

### 확인 지표

- MdAPE
- p95_APE
- Within_30
- 결측 있음 / 없음 slice 성능
- 수집 가능률

### 판단 기준

- 성능 개선이 있고 운영에서 자동 생성 가능한 변수만 채택 후보로 둔다.
- 결측이 많고 성능 개선이 작으면 보류한다.
- 출처 의존성이 강하면 별도 검증 후 채택한다.

### 결과 활용

- 작가 DB 수집 우선순위를 정한다.
- Cold 모델의 다음 버전 피처 후보를 정한다.

## 12. E5 Warm 저이력 작가 fallback 실험

### 목적

- 학습 데이터에 작가가 있어도 작품 수가 적으면 Warm 모델보다 Cold 방식이 더 안정적인지 확인한다.
- “작가가 train에 있으면 무조건 Warm”이라는 기준이 충분한지 검증한다.

### 비교 대상

- Warm 방식:
  - `Huber`
  - Warm 1차 후보 피처
- Cold 방식:
  - `CatBoost`
  - Cold 1차 후보 피처

### 실험 방법

- Warm test를 `artist_works_count_train` 기준으로 구간화한다.
- 예시 구간:
  - 5~9개
  - 10~29개
  - 30개 이상
- 각 구간에서 Warm 방식과 Cold 방식의 성능을 비교한다.

### 확인 지표

- 구간별 MdAPE
- 구간별 p95_APE
- 구간별 Within_30
- 구간별 sample 수

### 판단 기준

- 저이력 구간에서 Warm p95_APE가 크면 fallback 후보로 둔다.
- 특정 작품 수 이하에서 Cold 방식이 더 안정적이면 라우팅 기준으로 사용한다.
- sample 수가 부족한 구간은 확정하지 않고 추가 데이터 필요로 표시한다.

### 결과 활용

- Warm / Cold 라우팅 기준을 단순 작가 존재 여부에서 작가 학습 작품 수까지 확장할지 결정한다.

## 13. 권장 진행 순서

| 순서 | 실험 | 이유 |
|---:|---|---|
| 1 | PRE-PP 모델별 group-drop ablation | 후처리 기준으로 쓸 피처/구간이 실제로 필요한지 먼저 확인 |
| 2 | PRE-MODEL Warm/Cold CatBoost 적합성 검증 | 보정 전에 기준 모델을 바꿀 가치가 있는지 확인 |
| 3 | PRE-SPLIT-CB Warm/Cold CatBoost 구분 학습 보정 | 구분 학습이 보정값을 줄이는지 확인 |
| 4 | PRE-CAL 상세 보정값 산출 | 모델별/구간별 correction map을 먼저 만든다 |
| 5 | PP-J 모델별 커스텀 보정 | PRE-CAL 결과를 모델 구조별 보정 방식으로 검증 |
| 6 | PP-L Huber/Quantile/CatBoost MAPE 최적화 | MdAPE를 유지하면서 MAPE와 p95_APE를 줄이는 순차 학습 후보를 검증 |
| 7 | E1 Warm 가격 범위 보정 | Warm은 서비스 가능성이 높으므로 표현 방식을 정함 |
| 8 | E2 Cold 가격 범위 보정 | Cold 단일 가격 제공 가능성을 판단함 |
| 9 | E3 Cold 신뢰도 라우팅 | PRE-PP/PRE-CAL/PP-J/PP-L 결과를 반영해 Cold 고위험 구간을 분리 |
| 10 | E5 Warm 저이력 fallback | Warm 라우팅 기준을 보완함 |
| 11 | E4 외부 작가 DB 보강 후 재실험 | 추가 수집이 필요하므로 후순위로 진행함 |

## 14. 산출물 기준

- 각 실험은 아래 파일을 남긴다.
  - `experiment_config.json`
  - `prompts/used_prompt.md`
  - `data/`
  - `outputs/metrics.csv`
  - `outputs/predictions.csv`
  - `outputs/result_sheet.html`
  - `README.md`

- 종합 문서에는 아래 내용을 반영한다.
  - 후속 실험별 결론
  - Warm / Cold 모델 유지 여부
  - 가격 범위 정책
  - 신뢰도 정책
  - 추가 수집 필요 항목
