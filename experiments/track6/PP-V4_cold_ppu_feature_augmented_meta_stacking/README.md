# PP-V4 Cold PP-U 피처 후보 추가 cross-fitted meta stacking

- 목적: 종합 보고서에서 남은 후속 후보를 기존 조합 구조에 넣어 추가 개선 여부를 확인한다.
- 선택 기준: validation에서 조합/정책을 정하고 test에서 재현성을 확인한다.

## Test 결과 상위

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `cold` | `component_s1_mdape` | `meta_component` | 0.4744 | 1.2095 | 3.4731 | 0.9301 |
| `cold` | `component_s1_p95` | `meta_component` | 0.4765 | 1.2067 | 3.2824 | 0.9386 |
| `cold` | `component_s4_huber` | `meta_component` | 0.4765 | 1.2079 | 3.2827 | 0.9409 |
| `cold` | `huber_component_range_clipped` | `feature_augmented_meta_stacking` | 0.4771 | 1.2207 | 3.6200 | 0.9457 |
| `cold` | `huber_raw` | `feature_augmented_meta_stacking` | 0.4793 | 1.2087 | 4.3888 | 0.9501 |
| `cold` | `component_r4_huber_meta` | `meta_component` | 0.4796 | 1.2148 | 3.4131 | 0.9436 |
| `cold` | `ridge_1_component_range_clipped` | `feature_augmented_meta_stacking` | 0.4796 | 1.2233 | 3.7024 | 0.9438 |
| `cold` | `component_u3_medium_size` | `meta_component` | 0.4803 | 1.3722 | 4.6205 | 0.9592 |
| `cold` | `ridge_10_component_range_clipped` | `feature_augmented_meta_stacking` | 0.4805 | 1.2200 | 3.6742 | 0.9429 |
| `cold` | `ridge_1_raw` | `feature_augmented_meta_stacking` | 0.4806 | 1.2141 | 4.2576 | 0.9445 |
| `cold` | `component_q2_mape_blend` | `meta_component` | 0.4811 | 1.1797 | 3.7925 | 0.9236 |
| `cold` | `ridge_10_raw` | `feature_augmented_meta_stacking` | 0.4823 | 1.2110 | 4.1502 | 0.9432 |
| `cold` | `component_u4_support_size_catboost` | `meta_component` | 0.4835 | 1.4657 | 4.4439 | 0.9640 |
| `cold` | `component_u3_support_shape` | `meta_component` | 0.4871 | 1.3618 | 4.4949 | 0.9549 |
| `cold` | `component_baseline_lgb` | `meta_component` | 0.4909 | 1.4131 | 4.8212 | 0.9687 |

## 선택/가중치 맵

| experiment_id | meta_model | clip_mode | validation_cv_RMSE_log | validation_cv_MdAPE | validation_cv_MAPE | validation_cv_p95_APE | validation_cv_Within_30 | validation_cv_Within_50 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-V4 | ridge_1 | raw | 0.630329 | 0.346536 | 0.545446 | 1.57912 | 0.422448 | 0.662187 |
| PP-V4 | ridge_1 | component_range_clipped | 0.629779 | 0.349927 | 0.549256 | 1.5784 | 0.420632 | 0.660734 |
| PP-V4 | ridge_10 | raw | 0.630864 | 0.344841 | 0.546308 | 1.57878 | 0.419542 | 0.660734 |
| PP-V4 | ridge_10 | component_range_clipped | 0.630392 | 0.349027 | 0.549462 | 1.58146 | 0.417363 | 0.658918 |
| PP-V4 | huber | raw | 0.631403 | 0.346686 | 0.536291 | 1.51013 | 0.434072 | 0.669452 |
| PP-V4 | huber | component_range_clipped | 0.630319 | 0.352335 | 0.544065 | 1.54379 | 0.430076 | 0.667272 |
