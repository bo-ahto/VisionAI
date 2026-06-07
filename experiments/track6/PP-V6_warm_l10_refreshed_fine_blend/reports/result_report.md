# PP-V6 Warm PP-L10 반영 fine blend

- 목적: 종합 보고서에서 남은 후속 후보를 기존 조합 구조에 넣어 추가 개선 여부를 확인한다.
- 선택 기준: validation에서 조합/정책을 정하고 test에서 재현성을 확인한다.

## Test 결과 상위

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `warm` | `fine_blend_mape_guarded` | `feature_augmented_fine_blend` | 0.1613 | 0.2889 | 0.9314 | 0.4079 |
| `warm` | `fine_blend_mdape` | `feature_augmented_fine_blend` | 0.1655 | 0.3215 | 1.1349 | 0.4381 |
| `warm` | `fine_blend_p95_guarded` | `feature_augmented_fine_blend` | 0.1670 | 0.2924 | 0.9496 | 0.4107 |
| `warm` | `component_r5_p95` | `fine_blend_component` | 0.1707 | 0.3278 | 1.1107 | 0.4381 |
| `warm` | `component_l10_meta_external_search_seq` | `fine_blend_component` | 0.1708 | 0.3363 | 1.1432 | 0.4507 |
| `warm` | `component_r5_mape` | `fine_blend_component` | 0.1713 | 0.3271 | 1.1069 | 0.4382 |
| `warm` | `component_l10_generated_bucket_seq` | `fine_blend_component` | 0.1743 | 0.3265 | 0.9818 | 0.4396 |
| `warm` | `component_d4_blend` | `fine_blend_component` | 0.1760 | 0.3293 | 1.1248 | 0.4387 |
| `warm` | `component_l8_seq` | `fine_blend_component` | 0.1777 | 0.3383 | 1.1047 | 0.4479 |
| `warm` | `component_e1_history` | `fine_blend_component` | 0.1856 | 0.3579 | 1.3398 | 0.4838 |
| `warm` | `component_l9_seq` | `fine_blend_component` | 0.1898 | 0.3636 | 1.0841 | 0.4622 |
| `warm` | `component_k3_similar` | `fine_blend_component` | 0.2042 | 0.3499 | 1.2149 | 0.5102 |
| `warm` | `component_u1_full_generated` | `fine_blend_component` | 0.2131 | 0.4814 | 1.8591 | 0.6072 |
| `warm` | `component_u1_artist_size_works` | `fine_blend_component` | 0.2218 | 0.4892 | 1.9108 | 0.6233 |
| `warm` | `component_huber` | `fine_blend_component` | 0.2274 | 0.4952 | 2.0130 | 0.6081 |

## 선택/가중치 맵

| experiment_id | objective | step | mdape_guard | weight_huber | weight_l8_seq | weight_l9_seq | weight_d4_blend | weight_r5_p95 | weight_r5_mape | weight_e1_history | weight_k3_similar | weight_u1_full_generated | weight_u1_artist_size_works | weight_l10_meta_external_search_seq | weight_l10_generated_bucket_seq | validation_RMSE_log | validation_MdAPE | validation_MAPE | validation_p95_APE | validation_Within_30 | validation_Within_50 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-V6 | mdape | 0.1 | 1.08 | 0.1 | 0 | 0.2 | 0 | 0 | 0 | 0.5 | 0 | 0 | 0 | 0.1 | 0.1 | 0.411719 | 0.139763 | 0.271302 | 0.842522 | 0.71869 | 0.874759 |
| PP-V6 | mape_guarded | 0.1 | 1.08 | 0 | 0 | 0.1 | 0 | 0 | 0 | 0.3 | 0.2 | 0 | 0 | 0.2 | 0.2 | 0.382326 | 0.152997 | 0.256586 | 0.793506 | 0.743738 | 0.874759 |
| PP-V6 | p95_guarded | 0.1 | 1.08 | 0 | 0 | 0 | 0 | 0 | 0 | 0.1 | 0.3 | 0 | 0 | 0.6 | 0 | 0.38331 | 0.162331 | 0.262903 | 0.721043 | 0.741811 | 0.874759 |
