# PP-V3 Cold PP-U 피처 후보 추가 fine blend

- 목적: 종합 보고서에서 남은 후속 후보를 기존 조합 구조에 넣어 추가 개선 여부를 확인한다.
- 선택 기준: validation에서 조합/정책을 정하고 test에서 재현성을 확인한다.

## Test 결과 상위

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `cold` | `component_s1_mdape` | `fine_blend_component` | 0.4744 | 1.2095 | 3.4731 | 0.9301 |
| `cold` | `component_s1_p95` | `fine_blend_component` | 0.4765 | 1.2067 | 3.2824 | 0.9386 |
| `cold` | `component_s4_huber` | `fine_blend_component` | 0.4765 | 1.2079 | 3.2827 | 0.9409 |
| `cold` | `fine_blend_p95_guarded` | `feature_augmented_fine_blend` | 0.4771 | 1.2073 | 3.4092 | 0.9396 |
| `cold` | `component_r4_huber_meta` | `fine_blend_component` | 0.4796 | 1.2148 | 3.4131 | 0.9436 |
| `cold` | `fine_blend_mape_guarded` | `feature_augmented_fine_blend` | 0.4796 | 1.2148 | 3.4131 | 0.9436 |
| `cold` | `component_u3_medium_size` | `fine_blend_component` | 0.4803 | 1.3722 | 4.6205 | 0.9592 |
| `cold` | `component_q2_mape_blend` | `fine_blend_component` | 0.4811 | 1.1797 | 3.7925 | 0.9236 |
| `cold` | `fine_blend_mdape` | `feature_augmented_fine_blend` | 0.4815 | 1.2186 | 3.3734 | 0.9386 |
| `cold` | `component_u4_support_size_catboost` | `fine_blend_component` | 0.4835 | 1.4657 | 4.4439 | 0.9640 |
| `cold` | `component_u3_support_shape` | `fine_blend_component` | 0.4871 | 1.3618 | 4.4949 | 0.9549 |
| `cold` | `component_baseline_lgb` | `fine_blend_component` | 0.4909 | 1.4131 | 4.8212 | 0.9687 |

## 선택/가중치 맵

| experiment_id | objective | step | mdape_guard | weight_baseline_lgb | weight_q2_mape_blend | weight_r4_huber_meta | weight_s1_mdape | weight_s1_p95 | weight_s4_huber | weight_u3_medium_size | weight_u3_support_shape | weight_u4_support_size_catboost | validation_RMSE_log | validation_MdAPE | validation_MAPE | validation_p95_APE | validation_Within_30 | validation_Within_50 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-V3 | mdape | 0.1 | 1.08 | 0 | 0 | 0.6 | 0.1 | 0.2 | 0 | 0 | 0.1 | 0 | 0.638044 | 0.346108 | 0.557021 | 1.55513 | 0.410098 | 0.643661 |
| PP-V3 | mape_guarded | 0.1 | 1.08 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.637386 | 0.354967 | 0.541622 | 1.52918 | 0.429713 | 0.667635 |
| PP-V3 | p95_guarded | 0.1 | 1.08 | 0 | 0.1 | 0.7 | 0 | 0 | 0.2 | 0 | 0 | 0 | 0.637146 | 0.360209 | 0.546665 | 1.52284 | 0.421722 | 0.652742 |
