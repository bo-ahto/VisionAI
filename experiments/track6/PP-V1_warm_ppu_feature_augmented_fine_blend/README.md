# PP-V1 Warm PP-U 피처 후보 추가 fine blend

- 목적: 종합 보고서에서 남은 후속 후보를 기존 조합 구조에 넣어 추가 개선 여부를 확인한다.
- 선택 기준: validation에서 조합/정책을 정하고 test에서 재현성을 확인한다.

## Test 결과 상위

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `warm` | `fine_blend_mape_guarded` | `feature_augmented_fine_blend` | 0.1621 | 0.3044 | 1.0335 | 0.4220 |
| `warm` | `fine_blend_mdape` | `feature_augmented_fine_blend` | 0.1668 | 0.3067 | 0.9580 | 0.4241 |
| `warm` | `fine_blend_p95_guarded` | `feature_augmented_fine_blend` | 0.1695 | 0.3168 | 1.0674 | 0.4399 |
| `warm` | `component_r5_p95` | `fine_blend_component` | 0.1707 | 0.3278 | 1.1107 | 0.4381 |
| `warm` | `component_r5_mape` | `fine_blend_component` | 0.1713 | 0.3271 | 1.1069 | 0.4382 |
| `warm` | `component_d4_blend` | `fine_blend_component` | 0.1760 | 0.3293 | 1.1248 | 0.4387 |
| `warm` | `component_l8_seq` | `fine_blend_component` | 0.1777 | 0.3383 | 1.1047 | 0.4479 |
| `warm` | `component_e1_history` | `fine_blend_component` | 0.1856 | 0.3579 | 1.3398 | 0.4838 |
| `warm` | `component_l9_seq` | `fine_blend_component` | 0.1898 | 0.3636 | 1.0841 | 0.4622 |
| `warm` | `component_k3_similar` | `fine_blend_component` | 0.2042 | 0.3499 | 1.2149 | 0.5102 |
| `warm` | `component_u1_full_generated` | `fine_blend_component` | 0.2131 | 0.4814 | 1.8591 | 0.6072 |
| `warm` | `component_u1_artist_size_works` | `fine_blend_component` | 0.2218 | 0.4892 | 1.9108 | 0.6233 |
| `warm` | `component_huber` | `fine_blend_component` | 0.2274 | 0.4952 | 2.0130 | 0.6081 |

## 선택/가중치 맵

| experiment_id | objective | step | mdape_guard | weight_huber | weight_l8_seq | weight_l9_seq | weight_d4_blend | weight_r5_p95 | weight_r5_mape | weight_e1_history | weight_k3_similar | weight_u1_full_generated | weight_u1_artist_size_works | validation_RMSE_log | validation_MdAPE | validation_MAPE | validation_p95_APE | validation_Within_30 | validation_Within_50 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-V1 | mdape | 0.1 | 1.08 | 0 | 0 | 0.2 | 0 | 0 | 0.1 | 0.5 | 0.2 | 0 | 0 | 0.399277 | 0.149528 | 0.268022 | 0.815347 | 0.73025 | 0.868979 |
| PP-V1 | mape_guarded | 0.1 | 1.08 | 0 | 0.2 | 0.1 | 0 | 0 | 0 | 0.5 | 0.2 | 0 | 0 | 0.391965 | 0.153965 | 0.265989 | 0.804721 | 0.720617 | 0.878613 |
| PP-V1 | p95_guarded | 0.1 | 1.08 | 0 | 0 | 0 | 0 | 0 | 0.1 | 0.7 | 0.2 | 0 | 0 | 0.395339 | 0.154797 | 0.271071 | 0.786373 | 0.722543 | 0.868979 |
