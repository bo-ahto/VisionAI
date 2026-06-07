# Track6 모델별 피처 영향도, 조합 근거, 후처리 튜닝 보고서

- 작성일: 2026-05-31
- 목적: 상사 보고용으로 Warm Huber, Cold CatBoost, Cold LightGBM이 가격을 예측하는 방식과 피처 영향도 해석, 피처 조합 선정 근거, 후처리 튜닝 계획을 한 문서로 정리한다.
- 사용 산출물: 최종 artifact 해석 감사 결과, T6-E005 피처 조합 ablation, T6-E007 test confirmation, T6-E008 risk slice, T6-PP residual calibration.

## 1. 결론 요약

- Warm Huber는 선형 예측식이므로 피처별 영향이 계수와 실제 contribution으로 직접 설명된다. 최종적으로 `size + medium_support + artist_key` 조합이 타당하다.
- Cold CatBoost는 대칭 트리 구조이므로 단일 중요도보다 `SHAP + interaction + leaf segment`를 함께 봐야 한다. 최종적으로 `size + depth_3d + medium/shape` 조합이 타당하다.
- Cold LightGBM은 leaf-wise 트리 구조이므로 평균 중요도보다 `permutation 영향 + tail slice`가 중요하다. 최종적으로 `area/size + support_size_bucket + pred_log bin` 중심의 tail 안정화가 필요하다.
- 후처리는 Warm은 즉시 채택 후보가 있고, Cold CatBoost는 단순 보정 보류, Cold LightGBM은 tail 안정화 후보로 보는 것이 맞다.

## 2. 최종 모델과 기준 성능

최종 artifact 구성은 아래와 같다.

```text
Warm Huber: base_existing_combo + artist_key
Cold CatBoost: base_medium_shape
Cold LightGBM: base_support_size
```

### 최종 artifact test 성능

| split | rows | MdAPE | MAPE | p90_APE | p95_APE | Within_30 | Within_50 | RMSE_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train+validation(final artifact fit data) | 27433.0000 | 0.1677 | 0.3699 | 0.7248 | 1.0345 | 0.6917 | 0.8281 | 0.5367 |
| test_warm | 607.0000 | 0.2241 | 0.4951 | 1.1073 | 2.0209 | 0.5931 | 0.7265 | 0.6093 |

| model | feature_set | rows | MdAPE | MAPE | p90_APE | p95_APE | Within_30 | Within_50 | RMSE_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cold_catboost | base_medium_shape | 3099.0000 | 0.4843 | 1.4262 | 2.3033 | 4.4183 | 0.3024 | 0.5182 | 0.9549 |
| cold_lightgbm | base_support_size | 3099.0000 | 0.4797 | 1.3651 | 2.1286 | 5.0569 | 0.3027 | 0.5195 | 0.9551 |

### validation에서 조합을 고른 근거

| split | model | feature_set | median_ape | p95_ape | within_30 | within_50 | rmse_log |
| --- | --- | --- | --- | --- | --- | --- | --- |
| val_cold | lightgbm_cold | base_support_size | 0.3848 | 2.0207 | 0.3603 | 0.5979 | 0.6873 |
| val_cold | lightgbm_cold | base_existing_combo | 0.3861 | 1.9909 | 0.3560 | 0.5975 | 0.6912 |
| val_cold | lightgbm_cold | all_operational_combos | 0.3910 | 2.0164 | 0.3454 | 0.6055 | 0.6925 |
| val_cold | lightgbm_cold | base | 0.3911 | 2.0401 | 0.3767 | 0.5975 | 0.6910 |
| val_cold | lightgbm_cold | base_large_flags | 0.3938 | 1.9783 | 0.3698 | 0.5946 | 0.6916 |
| val_cold | lightgbm_cold | base_size_shape | 0.3939 | 1.9831 | 0.3992 | 0.5972 | 0.6886 |
| val_cold | lightgbm_cold | base_medium_size | 0.3952 | 2.0032 | 0.3905 | 0.6062 | 0.6867 |
| val_cold | lightgbm_cold | base_medium_shape | 0.3973 | 2.0014 | 0.3861 | 0.5957 | 0.6891 |
| val_cold | catboost_cold | base_medium_shape | 0.4251 | 2.4420 | 0.3364 | 0.5547 | 0.7133 |
| val_cold | catboost_cold | base_existing_combo | 0.4266 | 2.3177 | 0.3444 | 0.5561 | 0.7100 |
| val_cold | catboost_cold | base_support_size | 0.4282 | 2.3586 | 0.3385 | 0.5601 | 0.7099 |
| val_cold | catboost_cold | base_medium_size | 0.4287 | 2.2506 | 0.3447 | 0.5598 | 0.7071 |

### test 확인 결과

| split | model | feature_set | validation_median_ape | validation_p95_ape | median_ape | p95_ape | rmse_log |
| --- | --- | --- | --- | --- | --- | --- | --- |
| test_warm | huber_warm_artist | base_existing_combo | 0.2126 | 1.3194 | 0.2274 | 2.0130 | 0.6081 |
| test_cold | catboost_cold | base_medium_shape | 0.4251 | 2.4420 | 0.4839 | 4.7974 | 0.9642 |
| test_cold | lightgbm_cold | base_support_size | 0.3848 | 2.0207 | 0.4859 | 4.7612 | 0.9705 |
| test_cold | lightgbm_cold | base_large_flags | 0.3938 | 1.9783 | 0.4921 | 4.7924 | 0.9686 |

## 3. Warm Huber: 가격 예측 공식과 피처 영향 해석

### 예측 공식

Warm Huber는 로그 가격을 먼저 예측한 뒤 원 가격으로 환산한다.

```text
z_num = StandardScaler(x_num)
z_cat = OneHotEncoder(x_cat)
pred_log_price = intercept + sum_j(beta_j * z_j)
pred_price = exp(pred_log_price)
```

HuberRegressor의 핵심은 학습 손실 함수다. 일반 선형 회귀는 큰 오차를 계속 제곱으로 강하게 따라가지만, Huber는 기준을 넘는 큰 오차를 선형 손실로 바꿔 이상치 영향력을 줄인다.

```text
r_i = y_i - (intercept + x_i * beta)
u_i = r_i / sigma

loss(u_i) =
  0.5 * u_i^2                         if |u_i| <= epsilon
  epsilon * |u_i| - 0.5 * epsilon^2    if |u_i| > epsilon

objective = sum_i loss(u_i) + alpha * ||beta||^2
```

따라서 Warm Huber에서 피처 영향은 다음 순서로 해석했다.

- 계수 `beta_j`: 해당 피처가 로그 가격을 올리는지/내리는지 확인
- 원 단위 환산 계수: 표준화된 숫자형 피처를 실제 cm, 면적 단위로 바꿔 확인
- 실제 contribution: `beta_j * z_j`가 test 데이터에서 평균적으로 얼마나 예측값을 움직였는지 확인
- 범주형 피처: one-hot 원계수 대신 centered contribution으로 해석

### 피처 그룹 영향도

| feature_group | encoded_feature_count | mean_abs_centered_contribution_sum | top_features | top_up_features | top_down_features | rank |
| --- | --- | --- | --- | --- | --- | --- |
| size | 4 | 1.2222 | num__log_area / num__height_cm / num__width_cm / num__area_cm2 | num__log_area / num__height_cm / num__width_cm | num__area_cm2 | 1 |
| medium_support | 58 | 0.5625 | cat__medium_support_bucket_mixed_media__canvas / cat__medium_support_bucket_mixed_media__unknown / cat__medium_support_bucket_acrylic__canvas / cat__medium_support_bucket_oil__linen / cat__medium_support_bucket_oil__canvas | cat__medium_support_bucket_acrylic__canvas / cat__medium_support_bucket_oil__linen / cat__medium_support_bucket_oil__canvas / cat__medium_support_bucket_mixed_media__paper / cat__medium_support_bucket_acrylic__linen | cat__medium_support_bucket_mixed_media__canvas / cat__medium_support_bucket_mixed_media__unknown / cat__medium_support_bucket_painting_material__unknown / cat__medium_support_bucket_textile__unknown / cat__medium_support_bucket_painting_material__paper | 2 |
| support | 9 | 0.5121 | cat__support_category_paper / cat__support_category_canvas / cat__support_category_unknown / cat__support_category_linen / cat__support_category_fabric | cat__support_category_canvas / cat__support_category_unknown / cat__support_category_metal / cat__support_category_glass | cat__support_category_paper / cat__support_category_linen / cat__support_category_fabric / cat__support_category_panel / cat__support_category_wood | 3 |
| medium | 18 | 0.4920 | cat__medium_category_mixed_media / cat__medium_category_acrylic / cat__medium_category_oil / cat__medium_category_painting_material / cat__medium_category_textile | cat__medium_category_mixed_media / cat__medium_category_painting_material / cat__medium_category_textile / cat__medium_category_ink / cat__medium_category_charcoal | cat__medium_category_acrylic / cat__medium_category_oil / cat__medium_category_other / cat__medium_category_print / cat__medium_category_sculpture_material | 4 |
| artist | 648 | 0.4353 | cat__artist_key_infrequent_sklearn / cat__artist_key_sang oktabu kim / cat__artist_key_sheean kim / cat__artist_key_young sung kim / cat__artist_key_ham sup 함섭 | cat__artist_key_sang oktabu kim / cat__artist_key_sheean kim / cat__artist_key_young sung kim / cat__artist_key_ham sup 함섭 / cat__artist_key_yoo suntai | cat__artist_key_infrequent_sklearn / cat__artist_key_jeremy yong / cat__artist_key_hyungjun suh / cat__artist_key_ro un lee / cat__artist_key_chang beom son | 5 |
| depth_3d | 5 | 0.0320 | cat__is_3d_candidate_True / cat__is_3d_candidate_False / cat__has_depth_False / cat__has_depth_True / num__depth_cm | cat__is_3d_candidate_True / cat__has_depth_False | cat__is_3d_candidate_False / cat__has_depth_True / num__depth_cm | 6 |
| shape | 2 | 0.0067 | num__aspect_ratio / cat__is_extreme_aspect_ratio_False | - | num__aspect_ratio | 7 |

### 상위 피처 contribution

| encoded_feature | raw_feature | feature_group | coef | original_unit_coef | active_rate | mean_abs_centered_contribution | mean_centered_contribution | centered_direction | rank_by_centered_abs_contribution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| num__log_area | log_area | size | 0.4787 | 0.4029 | 0.0318 | 0.4096 | 0.0152 | 예측가격 상승 방향 | 1 |
| num__height_cm | height_cm | size | 0.3906 | 0.0086 | 0.0632 | 0.3015 | 0.0247 | 예측가격 상승 방향 | 2 |
| num__width_cm | width_cm | size | 0.3961 | 0.0088 | 0.0331 | 0.2991 | 0.0131 | 예측가격 상승 방향 | 3 |
| num__area_cm2 | area_cm2 | size | -0.3882 | -0.0000 | 0.0382 | 0.2120 | -0.0148 | 예측가격 하락 방향 | 4 |
| cat__medium_category_mixed_media | medium_category | medium | 0.3387 | - | 0.3970 | 0.1719 | 0.1719 | 예측가격 상승 방향 | 5 |
| cat__support_category_paper | support_category | support | -0.1455 | - | 0.1697 | 0.1431 | -0.1431 | 예측가격 하락 방향 | 6 |
| cat__medium_category_acrylic | medium_category | medium | -0.6108 | - | 0.2488 | 0.1285 | -0.1285 | 예측가격 하락 방향 | 7 |
| cat__support_category_canvas | support_category | support | 0.9098 | - | 0.5832 | 0.1236 | 0.1236 | 예측가격 상승 방향 | 8 |
| cat__support_category_unknown | support_category | support | 1.7725 | - | 0.1104 | 0.1186 | 0.1186 | 예측가격 상승 방향 | 9 |
| cat__medium_support_bucket_mixed_media__canvas | medium_support_bucket | medium_support | -0.4980 | - | 0.1466 | 0.1012 | -0.1012 | 예측가격 하락 방향 | 10 |
| cat__medium_category_oil | medium_category | medium | -0.5050 | - | 0.2438 | 0.1001 | -0.1001 | 예측가격 하락 방향 | 11 |
| cat__support_category_linen | support_category | support | -0.7973 | - | 0.0478 | 0.0714 | -0.0714 | 예측가격 하락 방향 | 12 |

### Warm 피처 조합을 이렇게 판단한 이유

- `size` 그룹이 mean_abs_centered_contribution_sum 1위다. 즉, 실제 test 예측값을 가장 많이 움직인 축은 작품 크기다.
- `medium_support`와 `support`가 그 다음 설명 축이다. 같은 크기라도 재료와 지지체 조합에 따라 가격대가 달라진다는 뜻이다.
- Warm은 기존 작가가 있는 조건이므로 `artist_key`가 과거 작가 가격대 정보를 반영한다.
- 그래서 Warm 조합은 `size + medium_support + artist_key`가 가장 설명 가능하고, 선형 모델의 특성과도 맞다.

### Huber 안정성 확인

| split | rows | epsilon | scale | outlier_threshold_log | outlier_count | outlier_rate | median_abs_residual_log | p95_abs_residual_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train+validation | 27433.0000 | 1.3500 | 0.1710 | 0.2308 | 10858.0000 | 0.3958 | 0.1684 | 1.0984 |
| test_warm | 607.0000 | 1.3500 | 0.1710 | 0.2308 | 297.0000 | 0.4893 | 0.2214 | 1.3645 |

| epsilon | split | rows | MdAPE | MAPE | p90_APE | p95_APE | Within_30 | Within_50 | RMSE_log | outlier_rate | n_iter | scale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1.1000 | val_warm | 519.0000 | 0.2079 | 0.4090 | 0.9165 | 1.2920 | 0.5934 | 0.7437 | 0.6497 | 0.7803 | 3000.0000 | 0.0510 |
| 1.1000 | test_warm_locked | 607.0000 | 0.2254 | 0.4923 | 1.1065 | 2.0415 | 0.5815 | 0.7282 | 0.6070 | 0.8320 | 3000.0000 | 0.0510 |
| 1.3500 | val_warm | 519.0000 | 0.2126 | 0.4167 | 0.9195 | 1.3194 | 0.5954 | 0.7322 | 0.6446 | 0.4798 | 2512.0000 | 0.1740 |
| 1.3500 | test_warm_locked | 607.0000 | 0.2274 | 0.4952 | 1.1021 | 2.0130 | 0.5898 | 0.7232 | 0.6081 | 0.4827 | 2512.0000 | 0.1740 |
| 1.5000 | val_warm | 519.0000 | 0.2190 | 0.4192 | 0.9246 | 1.3315 | 0.5973 | 0.7360 | 0.6429 | 0.3931 | 2872.0000 | 0.2240 |
| 1.5000 | test_warm_locked | 607.0000 | 0.2316 | 0.4964 | 1.1269 | 2.0225 | 0.5914 | 0.7232 | 0.6084 | 0.3888 | 2872.0000 | 0.2240 |
| 1.7500 | val_warm | 519.0000 | 0.2261 | 0.4221 | 0.9063 | 1.3511 | 0.5857 | 0.7322 | 0.6402 | 0.2543 | 2438.0000 | 0.2857 |
| 1.7500 | test_warm_locked | 607.0000 | 0.2347 | 0.4989 | 1.1359 | 2.0691 | 0.5832 | 0.7199 | 0.6081 | 0.2883 | 2438.0000 | 0.2857 |
| 2.0000 | val_warm | 519.0000 | 0.2203 | 0.4247 | 0.8970 | 1.3620 | 0.5819 | 0.7322 | 0.6373 | 0.1696 | 2129.0000 | 0.3294 |
| 2.0000 | test_warm_locked | 607.0000 | 0.2396 | 0.5029 | 1.1220 | 2.1153 | 0.5799 | 0.7117 | 0.6081 | 0.2224 | 2129.0000 | 0.3294 |

### Warm Huber 피처별 근본 해석

아래 표는 “수치가 높다/낮다”를 넘어, 왜 해당 피처가 Warm Huber 구조 안에서 그렇게 작동했는지를 정리한 것이다.

| 피처/구간 | 관측 결과 | 모델 특성 기반 원인 | 높게 나온 이유 | 낮게/반대로 나온 이유 | 조합/보정 의미 |
| --- | --- | --- | --- | --- | --- |
| size: log_area, width_cm, height_cm, area_cm2 | Warm Huber에서 contribution 1위 그룹 | Huber는 선형 모델이라 각 크기 피처가 로그가격에 더해지는 독립 항으로 작동한다. 크기는 대부분 작품에서 관측되는 연속형 변수이고 결측/희소성이 낮아, 학습 과정에서 안정적인 공통 가격 축으로 선택되기 쉽다. | Warm 조건에서도 작가 이력만으로 가격을 설명할 수 없고, 같은 작가라도 작품 크기에 따라 가격대가 달라진다. 따라서 모델은 크기를 '작가 가격대 안에서 가격을 조정하는 기본 물리량'으로 크게 사용한다. | area_cm2는 log_area, width_cm, height_cm과 정보가 겹친다. 선형 모델은 중복 피처가 함께 있을 때 한 피처는 상승 방향, 다른 피처는 과대 상승을 눌러주는 보정 방향으로 배치할 수 있다. 따라서 area_cm2의 음의 계수는 면적이 가격을 낮춘다는 뜻이 아니라 중복 크기 정보 사이의 균형 조정이다. | 개별 크기 피처 하나를 보정 기준으로 쓰기보다 size 그룹 또는 size_bucket 기준으로 반복 편향을 확인해야 한다. |
| medium_support_bucket | Warm Huber에서 contribution 2위 그룹 | one-hot 범주형 피처는 해당 조합에 속하는 작품에만 일정한 로그가격 보정값을 더한다. Huber는 극단 가격 사례의 영향은 줄이지만, 반복적으로 나타나는 재료-지지체 조합의 평균 가격 차이는 계수로 남긴다. | 재료와 지지체는 작품의 물리적 완성도, 시장 분류, 구매자가 기대하는 가격 범위를 동시에 반영한다. 단일 medium 또는 support보다 조합 피처가 더 구체적인 작품 유형을 나타내기 때문에 영향이 크게 나타났다. | 희소 조합은 min_frequency 처리로 infrequent 그룹에 묶이거나 active_rate가 낮아 평균 contribution이 제한된다. 즉, 특정 조합의 계수가 커도 표본이 적으면 전체 영향도는 낮게 보인다. | 보정은 medium 단독보다 medium_support 조합을 우선 보되, 표본 수가 부족하면 support 또는 medium 단위로 fallback해야 한다. |
| artist_key | Warm에서만 사용되는 주요 설명 축 | Warm은 같은 작가가 학습 데이터에 존재하는 조건이다. one-hot artist_key는 해당 작가의 과거 가격대가 선형식의 절편 보정처럼 작동하게 만든다. | 미술품 가격은 작품 물성뿐 아니라 작가의 기존 시장 가격대에 크게 의존한다. Warm에서는 이 정보가 직접 주어지므로 모델이 가격 기준선을 잡는 데 사용한다. | 저빈도 작가는 infrequent 그룹으로 묶이고, Huber 손실은 극단 고가/저가 작가 사례에 과도하게 맞추지 않는다. 그래서 일부 작가 효과는 의도적으로 완화된다. | low_artist_history 또는 infrequent artist 그룹은 별도 신뢰도 표시와 residual 점검이 필요하다. |
| depth_3d / shape | Warm에서는 size, medium/support보다 낮은 영향 | 선형 Huber는 피처 간 복잡한 상호작용을 직접 만들지 않는다. 깊이나 형태가 가격에 영향을 주더라도 재료/크기와 결합되어야 의미가 커지는 경우, 선형 단독 항에서는 낮게 보일 수 있다. | - | Warm에서는 이미 artist_key와 medium_support가 많은 가격 차이를 흡수한다. 따라서 depth나 shape가 단독으로 추가 설명하는 잔여 정보가 상대적으로 작다. | 선형 Warm에서는 낮게 보여도 Cold 트리 모델에서는 depth와 size/medium interaction이 크게 나타난다. 즉, 낮은 영향은 피처가 무의미해서가 아니라 Warm Huber 구조 안에서 단독 선형 효과가 작다는 뜻이다. |

## 4. Cold CatBoost: 트리 예측 과정과 피처 조합 해석

### 예측 방식

CatBoost는 여러 개의 대칭 트리를 더해 로그 가격을 예측한다.

```text
pred_log_price = base_score + sum_t(leaf_value_t(x))
pred_price = exp(pred_log_price)
```

대칭 트리는 같은 depth의 모든 노드가 동일한 split 조건을 공유한다. 따라서 CatBoost에서는 “피처 하나가 가격을 올린다”보다 “어떤 피처 조합이 같은 경로에서 반복적으로 가격 구간을 나누는가”가 더 중요하다.

### 구조 확인

| model | tree_count | mean_leaf_count_per_tree | median_leaf_count_per_tree | inferred_depth | leaf_pattern_50_unique_count | top_10_leaf_pattern_coverage | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cold_catboost | 500 | 63.3520 | 64.0000 | 6.0000 | 1488 | 0.0768 | CatBoost 대칭 트리 구조상 같은 depth에서 동일 split 조건을 반복 적용하므로, 단독 중요도보다 interaction과 leaf segment 잔차를 함께 해석한다. |

### SHAP 기준 상위 피처

| feature | mean_abs_shap | mean_shap | feature_group | direction | rank |
| --- | --- | --- | --- | --- | --- |
| width_cm | 0.2629 | 0.0499 | size | 평균적으로 예측가격 상승 | 1 |
| area_cm2 | 0.2217 | 0.0709 | size | 평균적으로 예측가격 상승 | 2 |
| log_area | 0.1974 | 0.0452 | size | 평균적으로 예측가격 상승 | 3 |
| height_cm | 0.1266 | 0.0217 | size | 평균적으로 예측가격 상승 | 4 |
| depth_cm | 0.0940 | 0.0114 | depth_3d | 평균적으로 예측가격 상승 | 5 |
| support_category | 0.0661 | 0.0196 | support | 평균적으로 예측가격 상승 | 6 |
| medium_category | 0.0413 | 0.0153 | medium | 평균적으로 예측가격 상승 | 7 |
| aspect_ratio | 0.0353 | -0.0073 | shape | 평균적으로 예측가격 하락 | 8 |

### interaction 기준 상위 조합

| feature_1 | feature_2 | feature_group_1 | feature_group_2 | interaction_score | rank |
| --- | --- | --- | --- | --- | --- |
| width_cm | depth_cm | size | depth_3d | 5.5493 | 1 |
| height_cm | depth_cm | size | depth_3d | 5.2242 | 2 |
| depth_cm | aspect_ratio | depth_3d | shape | 5.1604 | 3 |
| depth_cm | medium_category | depth_3d | medium | 4.8243 | 4 |
| depth_cm | area_cm2 | depth_3d | size | 4.6171 | 5 |
| height_cm | medium_category | size | medium | 4.4176 | 6 |
| depth_cm | log_area | depth_3d | size | 4.3858 | 7 |
| depth_cm | support_category | depth_3d | support | 3.7983 | 8 |

### CatBoost 조합을 이렇게 판단한 이유

- SHAP 상위가 `width_cm`, `area_cm2`, `log_area`, `height_cm`로 모두 size 계열이다. Cold에서는 작가 이력이 없으므로 작품 물리 크기가 가격대를 먼저 나눈다.
- interaction 1위와 2위가 `width_cm x depth_cm`, `height_cm x depth_cm`이다. 이는 CatBoost가 size와 depth를 조합 조건으로 사용한다는 뜻이다.
- `depth_cm x medium_category`도 상위권이다. 입체성의 가격 의미가 재료에 따라 달라진다.
- 그래서 CatBoost 조합은 `size + depth_3d + medium/shape`가 모델 구조와 맞다.

### leaf segment 진단

| rows | median_residual_log | MdAPE | p95_APE | coverage_rate |
| --- | --- | --- | --- | --- |
| 42 | -2.2712 | 8.6912 | 8.8514 | 0.0136 |
| 31 | -1.1093 | 2.0323 | 2.7061 | 0.0100 |
| 27 | -3.4697 | 31.1256 | 31.5357 | 0.0087 |
| 24 | -0.1173 | 0.5429 | 0.8672 | 0.0077 |
| 22 | 0.0114 | 0.1812 | 0.5262 | 0.0071 |
| 20 | -0.4611 | 0.6752 | 1.7020 | 0.0065 |
| 18 | -1.6898 | 4.4183 | 4.4183 | 0.0058 |
| 18 | -0.0056 | 0.1456 | 1.2850 | 0.0058 |
| 18 | -0.1644 | 0.3998 | 0.8362 | 0.0058 |
| 18 | 0.2549 | 0.2250 | 0.7783 | 0.0058 |
| 17 | -0.1778 | 0.1946 | 0.1996 | 0.0055 |
| 16 | -3.4506 | 30.5207 | 31.9465 | 0.0052 |

### Cold CatBoost 피처별 근본 해석

아래 표는 CatBoost의 대칭 트리 구조와 ordered categorical 처리 특성에 맞춰 피처 영향의 원인을 설명한 것이다.

| 피처/구간 | 관측 결과 | 모델 특성 기반 원인 | 높게 나온 이유 | 낮게/반대로 나온 이유 | 조합/보정 의미 |
| --- | --- | --- | --- | --- | --- |
| size: width_cm, area_cm2, log_area, height_cm | CatBoost SHAP 상위 1~4위 | Cold에는 artist_key가 없으므로 모델은 모든 작품에 공통으로 존재하는 물리량을 먼저 사용한다. CatBoost의 대칭 트리는 같은 depth에서 동일 split을 반복 적용하므로, 많은 샘플을 안정적으로 나눌 수 있는 크기 피처가 상단 분기 조건이 되기 쉽다. | 처음 보는 작가의 가격 기준선을 직접 알 수 없기 때문에, 크기가 가격대의 대체 기준선 역할을 한다. 크기 피처는 결측이 적고 연속적이라 트리가 가격 구간을 나누기 좋은 신호다. | CatBoost는 크기 피처들을 독립 항으로 더하는 것이 아니라 분기 조건으로 사용한다. width_cm이 높다는 것은 단독 가격 프리미엄이 아니라, 특정 크기 구간으로 들어가는 경로가 예측값을 바꾼다는 뜻이다. | size 구간별 잔차를 보되, CatBoost에서는 size 단독보다 size와 depth/medium 조합 segment를 우선한다. |
| depth_cm | SHAP 5위, interaction 상위 대부분에 포함 | 대칭 트리는 한 번 선택한 split 조건을 전체 depth에 반복 적용하기 때문에, depth가 size/medium/shape와 함께 구간을 나누면 여러 트리에서 반복적으로 영향이 커질 수 있다. | Cold 데이터에서 depth는 단순 치수가 아니라 2D/3D 성격, 오브제성, 설치/조각 가능성을 대신 나타낸다. 작가 정보가 없는 상황에서는 작품 유형을 구분하는 강한 단서가 된다. | 깊이가 크면 항상 비싼 것이 아니라, 어떤 크기와 재료에서 깊이가 있는지가 중요하다. 그래서 interaction은 높지만 단독 방향성은 조합에 따라 달라진다. | CatBoost 보정은 depth 관련 leaf segment를 확인하고, 표본이 적으면 medium_shape_bucket 또는 size/depth slice로 fallback한다. |
| width_cm x depth_cm, height_cm x depth_cm | interaction 1위, 2위 | CatBoost interaction은 두 피처가 같은 트리 경로에서 예측값 변화를 함께 만든다는 뜻이다. 대칭 트리 구조에서는 반복 split 조합이 강한 segment 효과를 만든다. | 넓거나 높은 작품에 깊이까지 있으면 일반 평면 작품과 다른 시장 분류가 된다. 모델은 이를 단순 대형 작품이 아니라 '큰 입체/오브제 가능성'으로 분리한다. | - | width나 depth 각각의 값보다 두 조건이 동시에 만족될 때 가격 경로가 달라진다. 따라서 피처 영향도 보고에서 이 조합을 별도 설명해야 한다. |
| medium_category / support_category | SHAP 중위권, depth/size와 interaction | CatBoost는 범주형 변수를 target statistics와 ordered boosting 방식으로 처리해 범주별 평균 가격 정보를 누수 위험을 줄이며 학습한다. 다만 범주 단독보다 다른 split과 결합될 때 영향이 커진다. | - | - | CatBoost 보정은 medium 단독보다 medium_shape_bucket 또는 depth-medium segment 기준이 더 적합하다. |

## 5. Cold LightGBM: 트리 예측 과정과 피처 조합 해석

### 예측 방식

LightGBM도 여러 트리를 더해 로그 가격을 예측한다.

```text
pred_log_price = base_score + learning_rate * sum_t(leaf_value_t(x))
pred_price = exp(pred_log_price)
```

LightGBM은 leaf-wise 방식으로 손실을 크게 줄일 수 있는 leaf를 우선 확장한다. 그래서 평균 성능은 좋아질 수 있지만 일부 좁은 구간에서 오차가 크게 튀는 tail risk가 생길 수 있다.

### permutation 기준 피처 영향

| feature | feature_group | MdAPE_delta | p95_APE_delta | RMSE_log_delta |
| --- | --- | --- | --- | --- |
| area_cm2 | size | 0.2542 | 7.5139 | 0.4264 |
| width_cm | size | 0.0584 | 0.7783 | 0.0837 |
| log_area | size | 0.0237 | 0.1799 | 0.0146 |
| support_size_bucket | size | 0.0216 | -0.1286 | -0.0002 |
| depth_cm | depth_3d | 0.0198 | -0.3702 | 0.0041 |
| height_cm | size | 0.0193 | 0.2537 | 0.0311 |
| support_category | support | 0.0133 | 0.1694 | 0.0088 |
| has_depth | depth_3d | 0.0113 | -0.1717 | 0.0245 |

### tail 위험 구간

| slice_feature | slice_value | rows | MdAPE | p95_APE | mean_APE |
| --- | --- | --- | --- | --- | --- |
| support_size_bucket | canvas__q5 | 538 | 0.4893 | 26.4323 | 2.4873 |
| medium_category | acrylic | 965 | 0.4049 | 10.5052 | 2.2039 |
| size_bucket | q3 | 593 | 0.6105 | 10.5052 | 2.0602 |
| support_size_bucket | canvas__q3 | 398 | 0.5595 | 10.5052 | 2.5701 |
| support_category | canvas | 1849 | 0.4718 | 9.1233 | 1.6917 |
| size_bucket | q5 | 837 | 0.4681 | 7.1108 | 1.8589 |
| is_3d_candidate | False | 3057 | 0.4773 | 5.1707 | 1.3667 |
| support_size_bucket | paper__q2 | 158 | 0.3823 | 4.9249 | 1.4659 |

### leaf-wise 위험 확인

| tree_idx | used_leaf_count | max_leaf_rows | max_leaf_row_rate | worst_leaf_MdAPE | worst_leaf_rows |
| --- | --- | --- | --- | --- | --- |
| summary | 29.3257 | 1838.0000 | 0.5931 | 5.1568 | 3.0000 |
| 70 | 29.0000 | 598.0000 | 0.1930 | 45.7743 | 1.0000 |
| 69 | 28.0000 | 1168.0000 | 0.3769 | 45.7743 | 1.0000 |
| 62 | 27.0000 | 1140.0000 | 0.3679 | 45.7743 | 1.0000 |
| 56 | 26.0000 | 1142.0000 | 0.3685 | 45.7743 | 1.0000 |
| 119 | 30.0000 | 947.0000 | 0.3056 | 45.4669 | 2.0000 |
| 164 | 31.0000 | 1257.0000 | 0.4056 | 45.4669 | 2.0000 |
| 33 | 30.0000 | 680.0000 | 0.2194 | 45.4669 | 2.0000 |
| 34 | 29.0000 | 756.0000 | 0.2439 | 45.4669 | 2.0000 |
| 36 | 30.0000 | 607.0000 | 0.1959 | 45.4669 | 2.0000 |
| 172 | 30.0000 | 1013.0000 | 0.3269 | 45.4669 | 2.0000 |
| 40 | 30.0000 | 715.0000 | 0.2307 | 45.4669 | 2.0000 |

### LightGBM 조합을 이렇게 판단한 이유

- `area_cm2`를 섞었을 때 MdAPE_delta가 +0.2542, p95_APE_delta가 +7.5139로 가장 크다. 즉, LightGBM은 면적 의존도가 매우 높다.
- `support_size_bucket=canvas__q5`의 p95_APE가 26.43으로 가장 높다. 대형 캔버스 구간은 점예측보다 위험도 표시와 tail 안정화가 중요하다.
- leaf-wise 구조상 leaf 자체를 운영 보정 기준으로 쓰기에는 복잡하므로, 사람이 이해 가능한 `size_bucket`, `support_size_bucket`, `pred_log bin`으로 내려와 보정하는 것이 맞다.

### Cold LightGBM 피처별 근본 해석

아래 표는 LightGBM의 leaf-wise 성장 방식 때문에 어떤 피처가 크게 작동하고 어떤 구간에서 tail risk가 생기는지를 설명한 것이다.

| 피처/구간 | 관측 결과 | 모델 특성 기반 원인 | 높게 나온 이유 | 낮게/반대로 나온 이유 | 조합/보정 의미 |
| --- | --- | --- | --- | --- | --- |
| area_cm2 | permutation 영향 최대 | LightGBM은 leaf-wise 방식으로 손실 감소가 큰 leaf를 우선 확장한다. area_cm2는 연속형이고 가격대 분리에 강하므로, 특정 면적 기준 split이 반복적으로 깊은 leaf를 만들기 쉽다. | Cold에는 작가 기준선이 없고, 면적은 가격대 구분력이 강하다. permutation에서 area_cm2를 섞으면 기존 leaf 경로가 크게 무너져 MdAPE와 p95가 동시에 악화된다. | leaf-wise 구조는 강한 피처를 좁은 구간까지 깊게 파고들 수 있다. 따라서 area_cm2 의존도가 높다는 것은 평균 성능에는 유리하지만 큰 작품 구간 tail risk를 키울 수 있다. | area 단독 보정보다 size_bucket, pred_log bin, support_size_bucket으로 과민 구간을 안정화한다. |
| width_cm, height_cm, log_area | split/permutation 상위권 | LightGBM은 여러 크기 표현 중 손실을 가장 많이 줄이는 split을 선택한다. 서로 비슷한 정보를 가진 크기 피처들이 여러 경로에서 번갈아 사용될 수 있다. | 같은 면적이라도 가로형/세로형/정방형 여부에 따라 가격 분포가 달라질 수 있어, 모델은 면적 외 크기 표현도 활용한다. | 크기 피처끼리 상관이 높기 때문에 하나를 permutation해도 다른 크기 피처가 일부 대체한다. 그래서 area_cm2만 압도적으로 높고 나머지는 중간 수준으로 나타난다. | 크기 피처를 개별 보정하지 말고 크기 bucket과 형태 bucket의 결합으로 tail을 확인한다. |
| support_size_bucket: canvas__q5 | tail slice p95_APE 최상위 | LightGBM의 leaf-wise 성장은 특정 구간의 평균 손실을 줄이는 데 집중한다. 하지만 대형 캔버스처럼 가격 분산이 큰 구간은 같은 leaf 안에서도 실제 가격 편차가 커져 p95가 튈 수 있다. | 대형 캔버스는 고가 가능성이 있지만 모든 대형 캔버스가 고가인 것은 아니다. 작가 정보가 없는 Cold 조건에서는 이 분산을 충분히 설명하지 못해 큰 오차가 발생한다. | 해당 구간의 MdAPE는 전체와 비슷해도 p95가 매우 높다. 즉 일반 사례는 맞추지만 일부 고위험 사례에서 크게 틀리는 구조다. | 가격 범위/신뢰도 표시, p95 안정화, 상한/하한 완충 보정의 우선 대상이다. |
| medium_category: acrylic | tail slice p95 상위 | 범주형이 ordinal encoding된 뒤 트리에 들어가면, LightGBM은 범주 자체보다 해당 범주가 놓인 split 경로의 손실 감소를 기준으로 사용한다. acrylic은 표본이 많고 내부 가격 분산도 커 tail risk가 나타난다. | 아크릴은 작품 수가 많아 모델이 자주 만나는 범주지만, 같은 아크릴 안에서도 크기/지지체/작가 부재에 따라 가격 편차가 크다. 그래서 단순 medium 정보만으로는 충분하지 않다. | acrylic 전체를 일괄 보정하면 정상 구간까지 흔들 수 있다. 문제는 acrylic 전체가 아니라 acrylic 중 특정 size/support 조합일 가능성이 높다. | medium 단독보다 medium x size 또는 support_size_bucket과 함께 tail 보정을 설계한다. |

## 6. 지금까지 실험을 통해 조합을 찾은 과정

- 1단계: T6-E005에서 여러 feature_set을 validation 기준으로 비교했다.
- 2단계: T6-E006에서 Warm, Cold CatBoost, Cold LightGBM 후보를 선택했다.
- 3단계: T6-E007에서 선택 후보를 locked test로 확인했다.
- 4단계: 최종 artifact를 만든 뒤, 기존 해석 스크립트와 피처셋이 불일치하는 문제를 확인했다.
- 5단계: 최종 artifact 기준으로 Warm 계수/contribution, CatBoost SHAP/interaction, LightGBM permutation/tail slice를 재산출했다.
- 6단계: 단순 성능표가 아니라 모델 구조에 맞는 영향도 지표로 조합 이유를 다시 설명했다.

## 7. 후처리 튜닝 결과와 계획

### 기존 residual calibration 결과

| scope | baseline_MdAPE | best_MdAPE_method | best_MdAPE | baseline_p95_APE | best_p95_method | best_p95_APE | decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| warm | 0.2274 | pred_bin_median_residual | 0.2211 | 2.0130 | size_bucket_median_residual | 1.9736 | 채택 후보: 전체/예측구간 편향 보정이 MdAPE를 개선한다. |
| cold_catboost | 0.4839 | medium_category_median_residual | 0.4880 | 4.7974 | overall_median_residual | 3.9490 | 보류: 단순 median 보정은 MdAPE를 악화시켜 leaf/segment fallback 재실험이 필요하다. |
| cold_lightgbm | 0.4859 | size_bucket_median_residual | 0.4873 | 4.7612 | medium_category_median_residual | 4.2199 | 조건부 후보: MdAPE 악화 여부를 제한하면서 tail 안정화 위주로 검증한다. |

### 모델별 후처리 방향

| 모델 | 현재 판단 | 보정 방식 | 이유 | 적용 조건 |
| --- | --- | --- | --- | --- |
| Warm Huber | 채택 후보 | overall median residual 또는 pred_bin median residual | 선형 모델이라 전체 편향과 예측값 구간별 편향을 로그 공간에서 더하는 방식이 자연스럽고 MdAPE가 개선됐다. | validation/CV에서 보정값을 고정한 뒤 test/운영에서 재확인 |
| Cold CatBoost | 보류 후 재실험 | leaf/segment residual + fallback | 단순 median 보정은 MdAPE를 악화시켰다. CatBoost 구조상 대칭 트리 leaf와 interaction segment를 이용한 보정이 더 적합하다. | leaf coverage가 낮으면 medium_shape_bucket, shape/medium, overall 순서로 fallback |
| Cold LightGBM | 조건부 후보 | pred_log bin + size/support bucket tail 안정화 | 평균 예측보다 p95 tail risk가 문제이며, support_size_bucket과 area/size 의존도가 크다. | MdAPE 악화를 제한하고 p95 개선을 우선 목표로 검증 |

### risk slice 근거

| model | slice | n | median_ape | p95_ape | within_30 | q80_range_multiplier | risk_flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| catboost_cold__base_medium_shape | extreme_shape | 50 | 0.7044 | 3.2608 | 0.2400 | 3.4540 | True |
| catboost_cold__base_medium_shape | 3d | 42 | 0.7009 | 3.0203 | 0.1429 | 3.8374 | True |
| catboost_cold__base_medium_shape | unbalanced_shape | 350 | 0.5710 | 2.4540 | 0.2400 | 2.6905 | True |
| catboost_cold__base_medium_shape | large_q5 | 834 | 0.4560 | 7.6190 | 0.3609 | 3.1948 | True |
| catboost_cold__base_medium_shape | all | 3099 | 0.4839 | 4.7974 | 0.2956 | 2.8394 | False |
| catboost_cold__base_medium_shape | 2d | 3057 | 0.4796 | 4.7974 | 0.2977 | 2.8049 | False |
| catboost_cold__base_medium_shape | small_q1 | 474 | 0.4600 | 1.9718 | 0.3523 | 2.6458 | False |
| huber_warm_artist__base_existing_combo | low_artist_history | 88 | 0.4886 | 2.0306 | 0.3182 | 2.5496 | True |
| huber_warm_artist__base_existing_combo | small_q1 | 133 | 0.3239 | 1.7441 | 0.4737 | 2.4651 | True |
| huber_warm_artist__base_existing_combo | unbalanced_shape | 65 | 0.2751 | 3.5301 | 0.5231 | 2.7667 | True |
| huber_warm_artist__base_existing_combo | extreme_shape | 12 | 0.6052 | 4.4556 | 0.2500 | 3.8402 | False |
| huber_warm_artist__base_existing_combo | 3d | 12 | 0.4792 | 3.4389 | 0.1667 | 2.9730 | False |
| huber_warm_artist__base_existing_combo | all | 607 | 0.2274 | 2.0130 | 0.5898 | 2.0942 | False |
| huber_warm_artist__base_existing_combo | 2d | 595 | 0.2250 | 1.9551 | 0.5983 | 2.0763 | False |

## 8. 보고서 완성 기준과 추가 검증 계획

- 보고서 작성에 필요한 핵심 근거는 확보했다. 최종 artifact 기준 성능, 피처 영향도, 모델 구조별 해석 지표, 1차 residual calibration 결과가 모두 존재한다.
- Warm Huber: 현재 보정 후보가 이미 개선을 보였으므로 `PP-A1-W`는 실행 후보로 볼 수 있다. 단, 운영 적용 전 보정값은 validation 또는 cross-validation에서 고정해야 한다.
- Cold CatBoost: 단순 residual 보정은 보류다. 보고 결론은 “CatBoost는 단순 보정 적용이 아니라 leaf/segment fallback 보정으로 별도 실험해야 한다”가 맞다.
- Cold LightGBM: 단순 median 보정보다 tail 안정화 실험이 필요하다. 특히 `support_size_bucket`, `size_bucket`, `pred_log bin` 기준으로 p95 개선과 MdAPE 악화 제한을 같이 봐야 한다.
- 공통: 후처리 실험은 test 잔차로 보정값을 만들면 안 된다. 보정값은 validation 또는 OOF에서 만들고 locked test는 최종 확인에만 사용해야 한다.

## 9. 보고용 최종 메시지

- Warm Huber는 가격을 선형식으로 계산하기 때문에 피처별 계수와 contribution으로 영향도를 직접 설명할 수 있다.
- Cold CatBoost와 Cold LightGBM은 모두 트리형 모델이지만 예측 방식이 다르므로 같은 방식으로 해석하면 안 된다.
- CatBoost는 대칭 트리 구조라 피처 조합과 interaction을 중심으로 설명해야 한다.
- LightGBM은 leaf-wise 구조라 평균 중요도보다 tail 위험 구간을 중심으로 설명해야 한다.
- 후처리는 모델 구조에 맞춰 다르게 가야 한다. Warm은 로그 잔차 보정, CatBoost는 segment fallback, LightGBM은 tail 안정화가 맞다.
