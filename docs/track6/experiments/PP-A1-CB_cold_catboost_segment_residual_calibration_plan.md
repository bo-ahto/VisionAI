# PP-A1-CB Cold CatBoost 전체/세그먼트 예측 오차 보정 실험 계획서

- 작성일: `2026-05-29`
- 실험 ID: `PP-A1-CB`
- 실험명: Cold CatBoost 전체 residual 보정 및 segment 확장 검증
- 대상 모델: `Cold CatBoost`
- 대상 피처셋: `base_medium_shape`
- 실험 목적: Cold CatBoost 모델의 예측값이 전체 또는 특정 세그먼트에서 반복적으로 높거나 낮게 치우치는지 확인하고, CatBoost 모델 특성에 맞는 residual 보정값을 validation 데이터에서 산출해 test 데이터에 고정 적용한다.

## 1. 실험 배경

- 본 실험은 후처리 실험군 `PP-A1`의 Cold CatBoost 세부 실험으로 진행한다.
- `PP-A1`은 모델 예측값이 전체적으로 과대 또는 과소 예측되는지 확인하는 실험이다.
- Cold 모델은 CatBoost와 LightGBM을 별도 실험으로 분리한다.
- CatBoost는 대칭 트리 구조를 사용하는 gradient boosting 모델이다.
- CatBoost는 범주형 피처와 세그먼트별 상호작용을 트리 분기 안에서 반영한다.
- 따라서 Warm Huber처럼 전체 residual 하나만 더하는 방식보다, CatBoost가 나누는 세그먼트 단위의 residual 보정이 더 적합하다.
- 본 실험에서는 전체 median residual 보정을 기준선으로 확인한다.
- 본 실험에서는 CatBoost 특성상 전체 보정만으로 부족한 경우 segment/leaf 보정을 함께 검증한다.
- 따라서 PP-A1-CB는 PP-A1의 전체 보정 실험이면서, CatBoost 전용 segment 확장 검증을 포함한다.

## 2. 이전 실험에서 확인된 근거

- `T6-E005`에서 Cold CatBoost와 Cold LightGBM의 피처 조합을 비교했다.
- `T6-E006`에서 Cold CatBoost 기준 후보를 `catboost_cold__base_medium_shape`로 선정했다.
- `T6-E007`에서 동일 후보를 테스트 데이터에 적용해 기준 성능을 확인했다.
- `T6-PP residual calibration`에서 validation residual 기반 보정을 사전 실행했다.
- 사전 실행 결과, CatBoost 전체 median residual 보정은 p95_APE를 낮췄지만 MdAPE를 악화시켰다.
- 사전 실행 결과, CatBoost `medium_category_median_residual` 보정은 MdAPE가 baseline보다 나빠져 현재 기준에서는 보류 판단이다.
- 따라서 PP-A1-CB는 단순 전체 보정 채택이 아니라, CatBoost 특성에 맞는 segment/leaf 보정이 실제로 안정적인지 확인하기 위한 실험이다.
- 현재 사전 실행 결과는 전체 보정과 단순 운영 피처 기반 segment 보정만 확인한 결과다.
- 본 실험의 추가 확인 대상은 CatBoost 구조에 더 가까운 leaf pattern 또는 `medium_shape_bucket` 기반 보정이다.
- 따라서 본 실험은 기존 결과의 단순 반복이 아니라, CatBoost에 맞는 보정 단위를 재정의하는 실험이다.

## 3. 기준 피처셋 정의

- Cold CatBoost 기준 피처셋은 `base_medium_shape`로 고정한다.
- `base_medium_shape`는 작품 기본 피처에 형태 구간과 재료-형태 조합 피처를 추가한 피처셋이다.
- 본 실험의 실제 입력 피처는 아래와 같이 고정한다.

| 구분 | 사용 피처 |
|---|---|
| 기본 수치 피처 | `width_cm`, `height_cm`, `depth_cm`, `area_cm2`, `log_area`, `aspect_ratio` |
| 기본 범주 피처 | `has_depth`, `is_3d_candidate`, `medium_category`, `support_category` |
| 형태/재료 조합 피처 | `shape_bucket`, `medium_shape_bucket` |

- 해당 피처셋은 후처리 전용 신규 피처셋이 아니다.
- 해당 피처셋은 기존 Cold CatBoost 후보 선정 단계에서 CatBoost 기준 최저 MdAPE를 기록한 피처셋이다.
- `T6-E006`에서 해당 조합을 Cold CatBoost 기준 후보로 선택했다.
- PP-A1-CB에서는 위 피처 구성을 고정한다.
- PP-A1-CB에서는 피처 변경 없이 보정값 적용 여부와 보정 단위만 비교한다.

## 4. 실험에서 기대하는 값

- 기대 산출값은 Cold CatBoost의 예측 치우침을 나타내는 로그 스케일 residual 보정값이다.
- 전체 보정 후보는 `catboost_global_correction`으로 정의한다.
- 세그먼트 보정 후보는 `catboost_segment_correction`으로 정의한다.
- `catboost_segment_correction > 0`이면 해당 세그먼트에서 CatBoost가 validation 기준 과소 예측한 것으로 해석한다.
- `catboost_segment_correction < 0`이면 해당 세그먼트에서 CatBoost가 validation 기준 과대 예측한 것으로 해석한다.
- 보정 후 기대 방향은 MdAPE 개선이다.
- 보정 후 p95_APE와 RMSE_log는 악화되지 않아야 한다.
- 추가 기대값은 segment coverage, fallback rate, 악화 세그먼트 수다.
- CatBoost segment 보정은 전체 성능뿐 아니라 보정 적용 범위와 과보정 여부를 함께 확인해야 한다.

## 5. 피처 및 실험 조건 통제

- 본 실험은 후처리 효과만 확인한다.
- 피처셋은 반드시 고정한다.
- Cold CatBoost 입력 피처는 `base_medium_shape`로 고정한다.
- 피처 추가는 수행하지 않는다.
- 피처 제거는 수행하지 않는다.
- 피처 조합 변경은 수행하지 않는다.
- train / validation / test split은 기존 Track6 고정 split을 사용한다.
- CatBoost 모델 학습 설정은 기존 후보 선정 당시 설정을 유지한다.
- 실험 중 변경되는 값은 예측 후 적용하는 보정값뿐이다.

```text
고정: Cold 대상 데이터
고정: train / validation / test split
고정: CatBoost 모델
고정: base_medium_shape 피처셋
고정: 모델 학습 설정
변경: pred_log에 segment residual correction을 더하는지 여부
```

## 6. 모델 입력 전처리 기준

- 수치 피처는 숫자형으로 변환한다.
- 수치 피처 결측값은 CatBoost 입력 전 `0.0`으로 대체한다.
- 범주 피처는 문자열로 변환한다.
- 범주 피처 결측값은 `__MISSING__`으로 대체한다.
- CatBoost 모델 설정은 기존 Cold 후보 선정 당시와 동일하게 유지한다.

```text
CatBoostRegressor(
  loss_function="RMSE",
  iterations=500,
  learning_rate=0.04,
  depth=6,
  l2_leaf_reg=6.0,
  random_seed=20260518
)
```

- 이 전처리와 모델 설정을 고정해야 보정 전후 성능 차이를 후처리 효과로 해석할 수 있다.

## 7. 표준 보정식과 본 실험 적용식

- 본 실험은 회귀 모델에서 일반적으로 사용하는 residual bias correction 방식을 적용한다.
- 표준식은 아래와 같다.

```text
residual = actual - prediction
correction = median(residual)
corrected_prediction = prediction + correction
```

- `median(residual)`은 residual을 작은 값부터 큰 값까지 정렬했을 때 가운데에 있는 값, 즉 중앙값이다.
- 평균도 대표값으로 사용할 수 있지만, 가격 데이터는 큰 오차에 흔들릴 수 있으므로 본 실험에서는 중앙값을 우선 사용한다.
- 본 실험의 타깃은 가격 원값이 아니라 `log(price)`다.
- 따라서 표준식을 로그 스케일에 맞게 변환한다.

```text
residual_log = actual_log - pred_log
correction_log = median(residual_log)
corrected_pred_log = pred_log + correction_log
corrected_pred_price = exp(corrected_pred_log)
```

- CatBoost 실험에서는 전체 보정과 세그먼트 보정을 모두 확인한다.
- 전체 보정은 validation 전체 residual 중앙값을 사용한다.

```text
catboost_global_correction = median(actual_log - pred_log)
corrected_pred_log = pred_log + catboost_global_correction
corrected_pred_price = exp(corrected_pred_log)
```

- 세그먼트 보정은 validation에서 같은 세그먼트에 속한 residual 중앙값을 사용한다.

```text
segment_key = selected_segment(feature_values or leaf_pattern)
catboost_segment_correction[segment_key] = median(actual_log - pred_log | segment_key)
corrected_pred_log = pred_log + alpha * catboost_segment_correction[segment_key]
corrected_pred_price = exp(corrected_pred_log)
```

- 기본 비교에서는 `alpha = 1.0`을 사용한다.
- 과보정 방지를 위해 보정 강도 `alpha` 후보를 함께 비교한다.

```text
alpha 후보 = {0.25, 0.5, 0.75, 1.0}
```

- CatBoost는 대칭 트리 구조를 사용하므로, 가능하면 leaf pattern 기반 보정을 우선 검토한다.
- leaf pattern을 안정적으로 운영에 저장/적용하기 어렵거나 표본 수가 부족하면, 운영 피처 기반 세그먼트로 대체한다.
- 본 실험에서 우선 확인할 운영 세그먼트는 `medium_category`, `shape_bucket`, `medium_shape_bucket`이다.
- median residual을 사용하는 이유는 Cold 데이터에 극단 가격과 희소 조합이 존재할 수 있기 때문이다.
- mean residual은 일부 극단값에 의해 보정값이 과하게 흔들릴 수 있다.
- CatBoost segment residual 보정에는 median residual이 더 안정적이다.

## 8. 세그먼트 보정 후보

- 1순위 후보: `leaf_pattern_median_residual`
- 2순위 후보: `medium_shape_bucket_median_residual`
- 3순위 후보: `shape_bucket_median_residual`
- 4순위 후보: `medium_category_median_residual`
- 비교 기준 후보: `overall_median_residual`

| 후보 | 설명 | 사용 목적 |
|---|---|---|
| `leaf_pattern_median_residual` | CatBoost leaf 조합별 residual 중앙값 | CatBoost 모델 구조에 가장 직접적으로 맞춘 보정 |
| `medium_shape_bucket_median_residual` | 재료-형태 조합별 residual 중앙값 | CatBoost 기준 피처셋의 핵심 조합 효과 확인 |
| `shape_bucket_median_residual` | 형태 구간별 residual 중앙값 | 형태별 반복 오차 확인 |
| `medium_category_median_residual` | 재료 범주별 residual 중앙값 | 재료별 반복 오차 확인 |
| `overall_median_residual` | 전체 residual 중앙값 | 세그먼트 보정 대비 기준선 |

## 9. leaf pattern 적용 조건

- `leaf_pattern_median_residual`은 CatBoost 모델 구조에 가장 직접적으로 맞춘 보정 후보다.
- 다만 leaf pattern은 조합 수가 많고 희소해질 수 있으므로 별도 적용 조건이 필요하다.
- leaf pattern 보정은 아래 조건을 만족할 때만 후보로 유지한다.

| 조건 | 기준 |
|---|---|
| 최소 표본 수 | leaf pattern별 validation 표본 수가 설정 기준 이상이어야 함 |
| validation coverage | validation에서 보정 가능한 leaf pattern 샘플 비율이 기준 이상이어야 함 |
| fallback 예상 비율 | validation 기준 fallback 적용 비율이 기준 이하이어야 함 |
| 개선 분포 | validation 개선이 소수 leaf pattern에만 집중되지 않아야 함 |
| 운영 재현성 | 동일 모델과 동일 전처리에서 leaf pattern을 재현할 수 있어야 함 |

- leaf pattern 보정이 위 조건을 만족하지 못하면 운영 피처 기반 세그먼트 보정으로 대체한다.
- leaf pattern 저장과 재현이 불안정하면 최종 운영 후보로 채택하지 않는다.
- test의 unseen leaf pattern 비율은 사후 진단 지표로만 사용한다.
- test의 unseen leaf pattern 비율을 보고 leaf 보정 후보를 새로 선택하거나 fallback 기준을 바꾸지 않는다.

## 10. 최소 표본 수, 보정 강도, fallback 기준

- 세그먼트별 보정값은 validation 표본 수가 충분할 때만 적용한다.
- 최소 표본 수 후보는 `n >= 30`, `n >= 50`, `n >= 100`으로 비교한다.
- 표본 수가 기준보다 작으면 해당 세그먼트 보정값을 적용하지 않는다.
- 표본 수가 작을수록 보정 강도를 낮춘다.

| validation 표본 수 | 허용 alpha 후보 | 판단 |
|---:|---|---|
| `n >= 100` | `0.5`, `0.75`, `1.0` | 충분한 표본이므로 강한 보정 후보 허용 |
| `50 <= n < 100` | `0.25`, `0.5` | 중간 표본이므로 보수적 보정 우선 |
| `30 <= n < 50` | `0.25` | 과보정 위험이 높으므로 약한 보정만 허용 |
| `n < 30` | 적용 안 함 | fallback 적용 |

- 표본 수 부족 시 fallback은 아래 순서로 적용한다.

```text
leaf_pattern
-> medium_shape_bucket
-> shape_bucket 또는 medium_category
-> overall_median_residual
-> no_correction
```

- fallback 기준은 validation에서 확정한다.
- test 성능을 보고 fallback 순서를 바꾸지 않는다.
- fallback 비율이 지나치게 높으면 해당 보정 후보는 운영 적용성이 낮은 것으로 판단한다.
- segment 보정 후보의 기본 수치 기준은 아래와 같이 둔다.

| 지표 | 기본 기준 | 해석 |
|---|---:|---|
| `segment_coverage` | `>= 0.70` | 전체 샘플의 70% 이상에 보정 규칙이 직접 적용되어야 함 |
| `fallback_rate` | `<= 0.30` | fallback 적용 비율이 30%를 넘으면 운영 적용성이 낮음 |
| `unseen_segment_rate` | `<= 0.20` | test 사후 진단에서 미등록 세그먼트가 20% 이하이면 안정적 |
| `worsened_segment_count` | `<= improved_segment_count` | 악화 세그먼트 수가 개선 세그먼트 수보다 많으면 보류 |

- 위 수치 기준은 validation에서 후보를 선택하기 위한 기본 기준이다.
- `unseen_segment_rate`는 test 사후 진단용이며, test 결과를 보고 보정 규칙을 변경하지 않는다.

## 11. 실험 절차

- 1단계: `base_medium_shape`로 학습된 Cold CatBoost 모델의 validation 예측값을 생성한다.
- 2단계: validation에서 `actual_log - pred_log`를 계산해 `residual_log`를 생성한다.
- 3단계: validation 전체 residual 중앙값을 계산해 `catboost_global_correction`으로 저장한다.
- 4단계: validation 세그먼트별 residual 중앙값을 계산해 `catboost_segment_correction`으로 저장한다.
- 5단계: validation에서 leaf pattern 보정 후보의 coverage, fallback 예상 비율, 세그먼트별 개선/악화 수를 계산한다.
- 6단계: validation 기준으로 segment 후보, 최소 표본 수, alpha, fallback 순서를 확정한다.
- 7단계: test 원본 예측값 `pred_log`에 validation에서 확정한 `alpha * segment correction`을 더해 `corrected_pred_log`를 생성한다.
- 8단계: test 샘플의 `segment_key`가 validation에서 최소 표본 수 기준을 충족한 보정 규칙에 존재하면 해당 보정값을 적용한다.
- 9단계: test 샘플의 `segment_key`가 validation 규칙에 없거나 validation 표본 수 기준을 충족하지 못한 경우 fallback을 적용한다.
- 10단계: `corrected_pred_log`를 가격 원 단위로 변환해 `corrected_pred_price`를 생성한다.
- 11단계: 보정 전 `pred_log` 기준 성능과 보정 후 `corrected_pred_log` 기준 성능을 비교한다.
- 12단계: test에서는 사후 진단용으로 unseen rate, fallback rate, 세그먼트별 개선/악화 수를 확인한다.

## 12. 데이터 누수 방지 기준

- 보정값은 validation 데이터에서만 계산한다.
- test 데이터의 실제값은 보정값 계산에 사용하지 않는다.
- test 데이터는 보정식과 fallback 기준 고정 후 최종 확인 용도로만 사용한다.
- test 성능을 보고 세그먼트 기준, 최소 표본 수, fallback 순서를 재조정하지 않는다.
- test 성능을 보고 alpha 후보를 새로 추가하지 않는다.
- leaf pattern 후보도 validation 기준으로만 생성하고 test에서는 고정 적용한다.
- segment 후보, 최소 표본 수, alpha, fallback 순서는 모두 validation에서 확정한다.
- test에서는 확정된 규칙의 성능과 적용 안정성만 확인한다.

## 13. 평가 지표

- 주 지표: `MdAPE`
- 보조 지표: `p95_APE`, `RMSE_log`, `Within_30`, `Within_50`
- `MdAPE`는 일반적인 예측 오차의 중앙 수준을 확인하기 위해 사용한다.
- `p95_APE`는 큰 오차 위험이 악화되는지 확인하기 위해 사용한다.
- `RMSE_log`는 로그 스케일의 전체 오차가 악화되는지 확인하기 위해 사용한다.
- Cold CatBoost는 큰 오차 위험이 상대적으로 크므로 p95_APE 악화 여부를 반드시 같이 판단한다.
- 세그먼트 보정 전용 지표를 추가로 확인한다.

| 지표 | 기준 역할 | 정의 | 목적 |
|---|---|---|---|
| `segment_coverage` | validation 후보 선택 | 보정 적용 샘플 수 / 전체 샘플 수 | 보정 규칙이 충분히 적용되는지 확인 |
| `fallback_rate` | validation 후보 선택 | fallback 적용 샘플 수 / 전체 샘플 수 | 세그먼트 규칙의 운영 적용성 확인 |
| `improved_segment_count` | validation 후보 선택 | 보정 후 MdAPE가 개선된 세그먼트 수 | 개선 범위 확인 |
| `worsened_segment_count` | validation 후보 선택 | 보정 후 MdAPE가 악화된 세그먼트 수 | 과보정 위험 확인 |
| `unseen_segment_rate` | test 사후 진단 | test에서 validation에 없던 세그먼트 비율 | 운영 재현성 확인 |

- 전체 성능이 개선되어도 `worsened_segment_count`가 과도하면 최종 채택하지 않는다.
- `fallback_rate`가 높으면 해당 보정 방식은 운영 적용성이 낮은 후보로 분류한다.
- validation 후보 선택 기준은 `segment_coverage >= 0.70`, `fallback_rate <= 0.30`, `worsened_segment_count <= improved_segment_count`로 둔다.
- `unseen_segment_rate <= 0.20`은 test 사후 진단 기준으로만 사용한다.

## 14. 성공 및 보류 기준

- 채택 조건은 아래 채택 항목을 모두 만족하는 경우로 본다.

- 채택: 보정 후 MdAPE가 개선되고 p95_APE가 악화되지 않는 경우.
- 채택: RMSE_log가 기존 수준을 유지하는 경우.
- 채택: validation 기준 `segment_coverage >= 0.70`인 경우.
- 채택: validation 기준 `fallback_rate <= 0.30`인 경우.
- 채택: validation 기준 `worsened_segment_count <= improved_segment_count`인 경우.
- 보류: MdAPE가 개선되더라도 p95_APE가 크게 악화되는 경우.
- 보류: p95_APE는 개선되지만 MdAPE가 뚜렷하게 악화되는 경우.
- 보류: 전체 지표는 개선되지만 악화 세그먼트 수가 많은 경우.
- 보류: validation 기준 fallback_rate가 높은 경우.
- 사후 점검: test unseen_segment_rate가 높으면 운영 적용 위험으로 표시하되, test 결과를 보고 보정 규칙을 변경하지 않는다.
- 중단: MdAPE와 p95_APE가 모두 baseline 대비 악화되는 경우.
- 후보 유지: 전체 성능 개선은 작더라도 특정 고위험 세그먼트의 p95_APE가 안정적으로 개선되는 경우.
- 미적용: 모든 alpha와 segment 후보에서 baseline 대비 안정적인 개선이 없는 경우.

## 15. 현재 실행 결과 참고

- 결과 출처: `T6-PP residual calibration` 사전 실행 결과
- 실행 스크립트: `scripts/track6/run_t6_pp_residual_calibration.py`
- 결과 파일: `data/track6/results/t6_pp_residual_calibration_metrics.csv`
- 보정 규칙 파일: `data/track6/results/t6_pp_residual_calibration_rules.csv`
- 기준 모델: `catboost_cold`
- 기준 피처셋: `base_medium_shape`
- 비교 방식: test baseline `pred_log`와 validation residual 보정 후 `corrected_pred_log` 비교

- 기준 성능은 Cold CatBoost `catboost_cold__base_medium_shape`의 test baseline 결과다.
- 보정 후 성능은 validation에서 계산한 residual 보정값을 test 예측값에 고정 적용한 결과다.
- 현재 사전 실행 결과에는 leaf pattern 보정은 포함되지 않았다.
- 현재 사전 실행 결과는 운영 피처 기반 residual 보정의 1차 참고값으로 본다.

| 구분 | method | MdAPE | p95_APE | RMSE_log |
|---|---|---:|---:|---:|
| 보정 전 | `baseline` | `0.4839` | `4.7974` | `0.9642` |
| 보정 후 | `overall_median_residual` | `0.4953` | `3.9490` | `0.9556` |
| 보정 후 | `medium_category_median_residual` | `0.4880` | `4.7974` | `0.9535` |
| 보정 후 | `support_category_median_residual` | `0.5317` | `5.1977` | `0.9871` |

- `overall_median_residual`은 p95_APE를 개선했지만 MdAPE를 악화시켰다.
- `medium_category_median_residual`은 RMSE_log를 개선했지만 MdAPE가 baseline보다 악화됐다.
- `support_category_median_residual`은 MdAPE와 p95_APE가 모두 악화됐다.
- 현재 사전 결과만 보면 CatBoost segment 보정은 즉시 채택보다 보류에 가깝다.
- 단, CatBoost 구조에 더 직접적인 `leaf_pattern_median_residual`은 아직 확인되지 않았으므로 본 계획에서 추가 검증한다.
- 현재 실행 결과는 `alpha = 1.0`에 가까운 보정 기준이다.
- 최종 적용 전에는 alpha별 성능, coverage, fallback rate를 추가 확인한다.

## 16. 해석 시 주의점

- 본 결과는 `base_medium_shape`를 사용한 현재 Cold CatBoost 설정에 한정된다.
- 피처셋을 변경하면 CatBoost 분기와 residual 분포가 달라진다.
- 피처셋 변경 시 segment correction은 재계산해야 한다.
- 전체 median residual 보정이 p95_APE를 낮추더라도 MdAPE를 악화시키면 최종 채택하지 않는다.
- CatBoost leaf 기반 보정은 모델 구조와 가장 잘 맞지만, 운영 적용을 위해 leaf pattern 저장과 재현 가능성이 확인되어야 한다.
- 세그먼트 표본 수가 부족한 경우 보정값을 무리하게 적용하면 과보정 위험이 커진다.
- CatBoost와 LightGBM은 모두 트리 기반 모델이지만 보정 방식은 동일하게 두지 않는다.
- CatBoost는 대칭 트리 구조를 가지므로 leaf pattern 또는 안정적인 세그먼트 단위 residual을 우선 검토한다.
- LightGBM은 leaf-wise 방식으로 비대칭 분기하므로 PP-A1-LGBM에서는 pred_log bin 또는 linear calibration을 우선 검토한다.

## 17. 실패 시 판단 기준

- PP-A1-CB가 채택 기준을 충족하지 못하면 CatBoost에는 PP-A1 보정을 적용하지 않는다.
- 이 경우 Cold CatBoost baseline 예측을 유지한다.
- CatBoost 보정이 실패하더라도 특정 조건에서 CatBoost가 LightGBM보다 유리하면 PP-E 조건별 모델 선택 후보로 넘긴다.
- p95_APE만 개선되고 MdAPE가 악화되는 경우, 정확도 보정으로는 보류하고 위험 방어용 후보로만 별도 표시한다.
- leaf pattern 보정이 운영 재현성 조건을 만족하지 못하면 최종 운영 후보에서 제외한다.

## 18. 결론

- PP-A1-CB는 Cold CatBoost의 전체 또는 세그먼트 residual bias를 validation 기반 median correction으로 보정하는 실험이다.
- 보정값은 validation 데이터에서만 계산한다.
- test 데이터에는 고정된 보정값과 fallback 기준만 적용한다.
- 피처셋과 모델을 고정하므로, 보정 전후 성능 차이는 후처리 효과로 해석할 수 있다.
- 현재 사전 실행 결과에서는 단순 세그먼트 보정이 명확한 채택 기준을 충족하지 못했다.
- 따라서 PP-A1-CB의 핵심은 CatBoost 구조에 맞는 leaf/segment 보정이 실제로 MdAPE와 p95_APE를 동시에 안정화하는지 확인하는 것이다.
- 다음 단계에서는 `leaf_pattern_median_residual`, `medium_shape_bucket_median_residual`, 최소 표본 수 기준, alpha 보정 강도를 포함해 CatBoost 전용 보정 후보를 재검증한다.
