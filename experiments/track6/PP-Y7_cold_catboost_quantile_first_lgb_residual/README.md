# PP-Y7 Cold CatBoost Quantile 선행 + LightGBM residual

- 목적: Cold 가격 예측에서 피처 조합과 모델 순서 변경으로 추가 개선 가능성을 확인한다.
- 기준: 기존 Track6 split을 고정하고 validation에서 후보를 비교한 뒤 test 결과를 함께 기록한다.

## Test 결과 상위

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 정책 |
|---|---:|---:|---:|---:|---|
| `base_catq_gallery_search_quality` | 0.4834 | 1.1041 | 3.6239 | 0.8863 | `cold_catboost_quantile_first_lgb_residual_base` |
| `catq_gallery_search_quality_lightgbm_oof_cap0.35_s1` | 0.4853 | 1.1337 | 3.7702 | 0.8859 | `cold_catboost_quantile_first_lgb_residual` |
| `catq_gallery_search_quality_lightgbm_oof_cap0.25_s1` | 0.4853 | 1.1295 | 3.7702 | 0.8832 | `cold_catboost_quantile_first_lgb_residual` |
| `catq_gallery_search_quality_lightgbm_oof_cap0.15_s1` | 0.4857 | 1.1257 | 3.7384 | 0.8824 | `cold_catboost_quantile_first_lgb_residual` |
| `catq_gallery_search_quality_lightgbm_oof_cap0.1_s1` | 0.4863 | 1.1238 | 3.6828 | 0.8836 | `cold_catboost_quantile_first_lgb_residual` |
| `catq_gallery_search_quality_lightgbm_oof_cap0.5_s1` | 0.4863 | 1.1384 | 3.7702 | 0.8897 | `cold_catboost_quantile_first_lgb_residual` |
| `catq_gallery_search_quality_lightgbm_oof_cap0.25_s0.5` | 0.4877 | 1.1147 | 3.6339 | 0.8833 | `cold_catboost_quantile_first_lgb_residual` |
| `catq_gallery_search_quality_lightgbm_oof_cap0.5_s0.5` | 0.4877 | 1.1181 | 3.6505 | 0.8858 | `cold_catboost_quantile_first_lgb_residual` |
| `catq_gallery_search_quality_lightgbm_oof_cap0.15_s0.5` | 0.4879 | 1.1134 | 3.6339 | 0.8834 | `cold_catboost_quantile_first_lgb_residual` |
| `catq_gallery_search_quality_lightgbm_oof_cap0.35_s0.5` | 0.4879 | 1.1163 | 3.6339 | 0.8843 | `cold_catboost_quantile_first_lgb_residual` |
| `catq_gallery_search_quality_lightgbm_oof_cap0.35_s0.75` | 0.4881 | 1.1243 | 3.6909 | 0.8847 | `cold_catboost_quantile_first_lgb_residual` |
| `catq_gallery_search_quality_lightgbm_oof_cap0.1_s0.5` | 0.4886 | 1.1130 | 3.6339 | 0.8843 | `cold_catboost_quantile_first_lgb_residual` |
| `catq_gallery_search_quality_lightgbm_oof_cap0.5_s0.75` | 0.4886 | 1.1273 | 3.6909 | 0.8872 | `cold_catboost_quantile_first_lgb_residual` |
| `catq_gallery_search_quality_lightgbm_oof_cap0.25_s0.75` | 0.4888 | 1.1215 | 3.6765 | 0.8829 | `cold_catboost_quantile_first_lgb_residual` |
| `catq_gallery_search_quality_lightgbm_oof_cap0.15_s0.75` | 0.4890 | 1.1192 | 3.6647 | 0.8827 | `cold_catboost_quantile_first_lgb_residual` |
| `catq_gallery_search_quality_lightgbm_oof_cap0.1_s0.75` | 0.4895 | 1.1182 | 3.6647 | 0.8838 | `cold_catboost_quantile_first_lgb_residual` |

## 설정/피처 맵

| experiment_id | candidate | base_model | base_loss | residual_model | feature_strategy | hypothesis | n_features | residual_train_source | features |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-Y7 | catq_gallery_search_quality | catboost | Quantile:alpha=0.5 | lightgbm | CatBoost Quantile + 갤러리 + 검색 품질 | CatBoost 중앙 예측 뒤 LightGBM residual로 tail 구간 보정 | 56 | 3-fold OOF base prediction on train | width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, medium_support_bucket, is_extreme_aspect_ratio, size_bucket, shape_bucket, medium_size_bucket, support_size_bucket, medium_shape_bucket, is_large_2d, is_large_3d, artist_meta_birth_year, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_for_sale_ratio, artist_meta_career_stage, artist_meta_total_works_log, artist_meta_for_sale_works_log, artist_meta_followers_log, artist_meta_birth_year_missing, artist_meta_total_works_missing, artist_meta_for_sale_works_missing, artist_meta_followers_missing, artist_meta_career_stage_missing, artist_meta_is_p1_flag, artist_meta_has_international_flag, is_high_price_candidate_flag, artist_meta_source, artist_meta_nationality, artist_meta_nationality_ko, gallery_tier_raw_numeric, gallery_tier_raw_available_flag, gallery_tier_validated_score, gallery_tier_validated_available_flag, gallery_tier_any_available_flag, gallery_city_count, gallery_city_count_log, gallery_tier_raw_bucket, gallery_tier_validated, gallery_ref_type, gallery_audit_status, gallery_feature_source, search_quality_score, search_quality_grade, search_collected_flag, search_homonym_risk_grade, search_quality_x_log_area |
