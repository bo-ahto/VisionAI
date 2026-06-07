# PP-X5 전시/갤러리 피처 목적별 정책 비교

- 목적: 갤러리 티어와 개인전/전시 활동 피처를 현재 최신 Cold 후보 구조에서 재검증한다.
- 기준: 기존 Track6 split은 바꾸지 않고 `_track6_row_id` 기준으로 외부 피처만 추가한다.

## Test 결과 상위

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 정책 |
|---|---:|---:|---:|---:|---|
| `component_x2_mdape` | 0.4490 | 1.1102 | 3.9976 | 0.8768 | `external_feature_policy_comparison` |
| `component_w2_mdape` | 0.4497 | 1.1111 | 4.1587 | 0.8817 | `external_feature_policy_comparison` |
| `component_x3_mape` | 0.4682 | 1.0669 | 3.6635 | 0.8850 | `external_feature_policy_comparison` |
| `component_x4_p95` | 0.4683 | 1.0665 | 3.7091 | 0.8962 | `external_feature_policy_comparison` |
| `component_w4_p95` | 0.4766 | 1.0847 | 3.0322 | 0.8907 | `external_feature_policy_comparison` |
| `component_x3_p95` | 0.4766 | 1.0847 | 3.0322 | 0.8907 | `external_feature_policy_comparison` |
| `component_x4_mape` | 0.4855 | 1.1288 | 3.6780 | 0.9385 | `external_feature_policy_comparison` |

## 설정/피처 맵

| experiment_id | label | folder | candidate |
| --- | --- | --- | --- |
| PP-X5 | w2_mdape | PP-W2_cold_catboost_artist_meta_feature_expansion | generated_all_meta_all |
| PP-X5 | w4_p95 | PP-W4_cold_lightgbm_quantile_artist_meta_catboost_residual | base_lightgbm_quantile_meta_all |
| PP-X5 | x2_mdape | PP-X2_cold_catboost_exhibition_gallery_revalidation | catboost_gallery |
| PP-X5 | x3_mape | PP-X3_cold_lightgbm_quantile_exhibition_gallery_revalidation | lightgbm_quantile_gallery |
| PP-X5 | x3_p95 | PP-X3_cold_lightgbm_quantile_exhibition_gallery_revalidation | baseline_lightgbm_quantile_ppw4_meta_all |
| PP-X5 | x4_mape | PP-X4_cold_lightgbm_external_huber_residual | lightgbm_quantile_exhibition_gallery_interaction_huber_residual_cap0.5_s1 |
| PP-X5 | x4_p95 | PP-X4_cold_lightgbm_external_huber_residual | lightgbm_quantile_exhibition_gallery_interaction_huber_residual_cap0.25_s0.75 |
