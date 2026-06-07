# PP-V2 Warm PP-U 피처 후보 추가 meta stacking

- 목적: 종합 보고서에서 남은 후속 후보를 기존 조합 구조에 넣어 추가 개선 여부를 확인한다.
- 선택 기준: validation에서 조합/정책을 정하고 test에서 재현성을 확인한다.

## Test 결과 상위

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `warm` | `huber_component_range_clipped` | `feature_augmented_meta_stacking` | 0.1680 | 0.2873 | 0.9287 | 0.4102 |
| `warm` | `ridge_1_component_range_clipped` | `feature_augmented_meta_stacking` | 0.1694 | 0.2955 | 0.9867 | 0.4164 |
| `warm` | `component_r5_p95` | `meta_component` | 0.1707 | 0.3278 | 1.1107 | 0.4381 |
| `warm` | `component_r5_mape` | `meta_component` | 0.1713 | 0.3271 | 1.1069 | 0.4382 |
| `warm` | `ridge_10_component_range_clipped` | `feature_augmented_meta_stacking` | 0.1716 | 0.2955 | 1.0322 | 0.4154 |
| `warm` | `huber_raw` | `feature_augmented_meta_stacking` | 0.1744 | 0.2945 | 0.9287 | 0.4157 |
| `warm` | `ridge_10_raw` | `feature_augmented_meta_stacking` | 0.1757 | 0.3072 | 1.0512 | 0.4242 |
| `warm` | `component_d4_blend` | `meta_component` | 0.1760 | 0.3293 | 1.1248 | 0.4387 |
| `warm` | `ridge_1_raw` | `feature_augmented_meta_stacking` | 0.1773 | 0.3079 | 1.0685 | 0.4257 |
| `warm` | `component_l8_seq` | `meta_component` | 0.1777 | 0.3383 | 1.1047 | 0.4479 |
| `warm` | `component_e1_history` | `meta_component` | 0.1856 | 0.3579 | 1.3398 | 0.4838 |
| `warm` | `component_l9_seq` | `meta_component` | 0.1898 | 0.3636 | 1.0841 | 0.4622 |
| `warm` | `component_k3_similar` | `meta_component` | 0.2042 | 0.3499 | 1.2149 | 0.5102 |
| `warm` | `component_u1_full_generated` | `meta_component` | 0.2131 | 0.4814 | 1.8591 | 0.6072 |
| `warm` | `component_u1_artist_size_works` | `meta_component` | 0.2218 | 0.4892 | 1.9108 | 0.6233 |
| `warm` | `component_huber` | `meta_component` | 0.2274 | 0.4952 | 2.0130 | 0.6081 |

## 선택/가중치 맵

| experiment_id | meta_model | clip_mode | validation_cv_RMSE_log | validation_cv_MdAPE | validation_cv_MAPE | validation_cv_p95_APE | validation_cv_Within_30 | validation_cv_Within_50 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-V2 | ridge_1 | raw | 0.379298 | 0.163482 | 0.271546 | 0.867745 | 0.699422 | 0.884393 |
| PP-V2 | ridge_1 | component_range_clipped | 0.3773 | 0.157339 | 0.262413 | 0.815684 | 0.707129 | 0.884393 |
| PP-V2 | ridge_10 | raw | 0.377943 | 0.162082 | 0.269859 | 0.874916 | 0.707129 | 0.878613 |
| PP-V2 | ridge_10 | component_range_clipped | 0.376729 | 0.157387 | 0.261849 | 0.815378 | 0.716763 | 0.878613 |
| PP-V2 | huber | raw | 0.377611 | 0.162865 | 0.264744 | 0.837207 | 0.709056 | 0.888247 |
| PP-V2 | huber | component_range_clipped | 0.378699 | 0.160273 | 0.261253 | 0.814728 | 0.712909 | 0.888247 |
