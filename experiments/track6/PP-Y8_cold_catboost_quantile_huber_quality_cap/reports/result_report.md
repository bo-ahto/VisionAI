# PP-Y8 Cold CatBoost Quantile + Huber residual + 품질 cap

- 목적: Cold 가격 예측에서 피처 조합과 모델 순서 변경으로 추가 개선 가능성을 확인한다.
- 기준: 기존 Track6 split을 고정하고 validation에서 후보를 비교한 뒤 test 결과를 함께 기록한다.

## Test 결과 상위

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 정책 |
|---|---:|---:|---:|---:|---|
| `base_catq_gallery_search_quality` | 0.4834 | 1.1041 | 3.6239 | 0.8863 | `cold_catboost_quantile_huber_quality_cap_base` |
| `catq_gallery_search_quality_huber_oof_cap0.1_s0.5` | 0.4887 | 1.1054 | 3.6552 | 0.8854 | `cold_catboost_quantile_huber_quality_cap` |
| `catq_gallery_search_quality_huber_oof_cap0.35_s0.5` | 0.4895 | 1.1106 | 3.6567 | 0.8849 | `cold_catboost_quantile_huber_quality_cap` |
| `catq_gallery_search_quality_huber_oof_cap0.15_s0.5` | 0.4897 | 1.1066 | 3.6567 | 0.8852 | `cold_catboost_quantile_huber_quality_cap` |
| `catq_gallery_search_quality_huber_oof_cap0.25_s0.5` | 0.4897 | 1.1088 | 3.6567 | 0.8850 | `cold_catboost_quantile_huber_quality_cap` |
| `catq_gallery_search_quality_huber_oof_cap0.5_s0.5` | 0.4897 | 1.1119 | 3.6567 | 0.8848 | `cold_catboost_quantile_huber_quality_cap` |
| `catq_gallery_search_quality_huber_oof_cap0.1_s0.75` | 0.4926 | 1.1064 | 3.6701 | 0.8851 | `cold_catboost_quantile_huber_quality_cap` |
| `catq_gallery_search_quality_huber_oof_cap0.35_s0.75` | 0.4932 | 1.1151 | 3.6701 | 0.8849 | `cold_catboost_quantile_huber_quality_cap` |
| `catq_gallery_search_quality_huber_oof_cap0.5_s0.75` | 0.4932 | 1.1173 | 3.7455 | 0.8850 | `cold_catboost_quantile_huber_quality_cap` |
| `catq_gallery_search_quality_huber_oof_cap0.25_s0.75` | 0.4936 | 1.1121 | 3.6701 | 0.8848 | `cold_catboost_quantile_huber_quality_cap` |
| `catq_gallery_search_quality_huber_oof_cap0.15_s0.75` | 0.4940 | 1.1085 | 3.6701 | 0.8850 | `cold_catboost_quantile_huber_quality_cap` |
| `catq_gallery_search_quality_huber_oof_cap0.1_s1` | 0.4959 | 1.1077 | 3.6887 | 0.8849 | `cold_catboost_quantile_huber_quality_cap` |
| `catq_gallery_search_quality_huber_oof_cap0.15_s1` | 0.4961 | 1.1107 | 3.6887 | 0.8849 | `cold_catboost_quantile_huber_quality_cap` |
| `catq_gallery_search_quality_huber_oof_cap0.5_s1` | 0.4963 | 1.1237 | 3.8345 | 0.8857 | `cold_catboost_quantile_huber_quality_cap` |
| `catq_gallery_search_quality_huber_oof_cap0.25_s1` | 0.4963 | 1.1160 | 3.6919 | 0.8851 | `cold_catboost_quantile_huber_quality_cap` |
| `catq_gallery_search_quality_huber_oof_cap0.35_s1` | 0.4963 | 1.1204 | 3.7130 | 0.8854 | `cold_catboost_quantile_huber_quality_cap` |

## 설정/피처 맵

| experiment_id | candidate | base_model | base_loss | residual_model | feature_strategy | hypothesis | n_features | residual_train_source | features |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-Y8 | catq_gallery_search_quality | catboost | Quantile:alpha=0.5 | huber | CatBoost Quantile + 갤러리 + 검색 품질 | CatBoost 중앙 예측 뒤 LightGBM residual로 tail 구간 보정 | 56 | 3-fold OOF base prediction on train | width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, medium_support_bucket, is_extreme_aspect_ratio, size_bucket, shape_bucket, medium_size_bucket, support_size_bucket, medium_shape_bucket, is_large_2d, is_large_3d, artist_meta_birth_year, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_for_sale_ratio, artist_meta_career_stage, artist_meta_total_works_log, artist_meta_for_sale_works_log, artist_meta_followers_log, artist_meta_birth_year_missing, artist_meta_total_works_missing, artist_meta_for_sale_works_missing, artist_meta_followers_missing, artist_meta_career_stage_missing, artist_meta_is_p1_flag, artist_meta_has_international_flag, is_high_price_candidate_flag, artist_meta_source, artist_meta_nationality, artist_meta_nationality_ko, gallery_tier_raw_numeric, gallery_tier_raw_available_flag, gallery_tier_validated_score, gallery_tier_validated_available_flag, gallery_tier_any_available_flag, gallery_city_count, gallery_city_count_log, gallery_tier_raw_bucket, gallery_tier_validated, gallery_ref_type, gallery_audit_status, gallery_feature_source, search_quality_score, search_quality_grade, search_collected_flag, search_homonym_risk_grade, search_quality_x_log_area |
