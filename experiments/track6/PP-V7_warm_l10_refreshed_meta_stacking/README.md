# PP-V7 Warm PP-L10 반영 meta stacking

- 목적: 종합 보고서에서 남은 후속 후보를 기존 조합 구조에 넣어 추가 개선 여부를 확인한다.
- 선택 기준: validation에서 조합/정책을 정하고 test에서 재현성을 확인한다.

## Test 결과 상위

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `warm` | `component_r5_p95` | `meta_component` | 0.1707 | 0.3278 | 1.1107 | 0.4381 |
| `warm` | `component_l10_meta_external_search_seq` | `meta_component` | 0.1708 | 0.3363 | 1.1432 | 0.4507 |
| `warm` | `huber_component_range_clipped` | `feature_augmented_meta_stacking` | 0.1712 | 0.2803 | 0.8990 | 0.4053 |
| `warm` | `component_r5_mape` | `meta_component` | 0.1713 | 0.3271 | 1.1069 | 0.4382 |
| `warm` | `ridge_10_component_range_clipped` | `feature_augmented_meta_stacking` | 0.1730 | 0.2894 | 0.9121 | 0.4113 |
| `warm` | `huber_raw` | `feature_augmented_meta_stacking` | 0.1735 | 0.2845 | 0.8990 | 0.4093 |
| `warm` | `ridge_1_component_range_clipped` | `feature_augmented_meta_stacking` | 0.1741 | 0.2895 | 0.9130 | 0.4109 |
| `warm` | `component_l10_generated_bucket_seq` | `meta_component` | 0.1743 | 0.3265 | 0.9818 | 0.4396 |
| `warm` | `component_d4_blend` | `meta_component` | 0.1760 | 0.3293 | 1.1248 | 0.4387 |
| `warm` | `component_l8_seq` | `meta_component` | 0.1777 | 0.3383 | 1.1047 | 0.4479 |
| `warm` | `ridge_10_raw` | `feature_augmented_meta_stacking` | 0.1787 | 0.3010 | 0.9402 | 0.4215 |
| `warm` | `ridge_1_raw` | `feature_augmented_meta_stacking` | 0.1838 | 0.3016 | 0.9399 | 0.4217 |
| `warm` | `component_e1_history` | `meta_component` | 0.1856 | 0.3579 | 1.3398 | 0.4838 |
| `warm` | `component_l9_seq` | `meta_component` | 0.1898 | 0.3636 | 1.0841 | 0.4622 |
| `warm` | `component_k3_similar` | `meta_component` | 0.2042 | 0.3499 | 1.2149 | 0.5102 |
| `warm` | `component_u1_full_generated` | `meta_component` | 0.2131 | 0.4814 | 1.8591 | 0.6072 |
| `warm` | `component_u1_artist_size_works` | `meta_component` | 0.2218 | 0.4892 | 1.9108 | 0.6233 |
| `warm` | `component_huber` | `meta_component` | 0.2274 | 0.4952 | 2.0130 | 0.6081 |

## 선택/가중치 맵

| experiment_id | meta_model | clip_mode | validation_cv_RMSE_log | validation_cv_MdAPE | validation_cv_MAPE | validation_cv_p95_APE | validation_cv_Within_30 | validation_cv_Within_50 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-V7 | ridge_1 | raw | 0.368386 | 0.166524 | 0.263044 | 0.815984 | 0.714836 | 0.88632 |
| PP-V7 | ridge_1 | component_range_clipped | 0.363724 | 0.16288 | 0.256578 | 0.785763 | 0.71869 | 0.88632 |
| PP-V7 | ridge_10 | raw | 0.36665 | 0.166916 | 0.261569 | 0.826569 | 0.726397 | 0.88632 |
| PP-V7 | ridge_10 | component_range_clipped | 0.362837 | 0.161566 | 0.255823 | 0.776955 | 0.726397 | 0.88632 |
| PP-V7 | huber | raw | 0.366302 | 0.160859 | 0.249697 | 0.809391 | 0.734104 | 0.8921 |
| PP-V7 | huber | component_range_clipped | 0.36539 | 0.160644 | 0.248597 | 0.788746 | 0.734104 | 0.8921 |
