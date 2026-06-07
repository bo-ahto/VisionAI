# PP-Y6 Cold LightGBM Quantile 선행 + CatBoost residual

- 목적: Cold 가격 예측에서 피처 조합과 모델 순서 변경으로 추가 개선 가능성을 확인한다.
- 기준: 기존 Track6 split을 고정하고 validation에서 후보를 비교한 뒤 test 결과를 함께 기록한다.

## Test 결과 상위

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 정책 |
|---|---:|---:|---:|---:|---|
| `lgbq_search_external_interaction_catboost_oof_cap0.15_s1` | 0.4327 | 1.0514 | 3.8486 | 0.8555 | `cold_lgbq_first_catboost_residual` |
| `lgbq_search_external_interaction_catboost_oof_cap0.25_s1` | 0.4328 | 1.0527 | 3.8486 | 0.8557 | `cold_lgbq_first_catboost_residual` |
| `lgbq_search_external_interaction_catboost_oof_cap0.35_s1` | 0.4328 | 1.0534 | 3.8486 | 0.8559 | `cold_lgbq_first_catboost_residual` |
| `lgbq_search_external_interaction_catboost_oof_cap0.5_s1` | 0.4328 | 1.0535 | 3.8486 | 0.8559 | `cold_lgbq_first_catboost_residual` |
| `lgbq_search_external_interaction_catboost_oof_cap0.1_s1` | 0.4331 | 1.0502 | 3.8116 | 0.8554 | `cold_lgbq_first_catboost_residual` |
| `lgbq_search_external_interaction_catboost_oof_cap0.15_s0.75` | 0.4354 | 1.0503 | 3.8266 | 0.8555 | `cold_lgbq_first_catboost_residual` |
| `lgbq_search_external_interaction_catboost_oof_cap0.1_s0.75` | 0.4357 | 1.0495 | 3.6928 | 0.8556 | `cold_lgbq_first_catboost_residual` |
| `lgbq_search_external_interaction_catboost_oof_cap0.25_s0.75` | 0.4357 | 1.0511 | 3.8266 | 0.8556 | `cold_lgbq_first_catboost_residual` |
| `lgbq_search_external_interaction_catboost_oof_cap0.35_s0.75` | 0.4362 | 1.0516 | 3.8266 | 0.8557 | `cold_lgbq_first_catboost_residual` |
| `lgbq_search_external_interaction_catboost_oof_cap0.5_s0.75` | 0.4362 | 1.0517 | 3.8266 | 0.8557 | `cold_lgbq_first_catboost_residual` |
| `lgbq_search_external_interaction_catboost_oof_cap0.15_s0.5` | 0.4364 | 1.0494 | 3.6635 | 0.8557 | `cold_lgbq_first_catboost_residual` |
| `lgbq_search_external_interaction_catboost_oof_cap0.1_s0.5` | 0.4370 | 1.0490 | 3.5770 | 0.8558 | `cold_lgbq_first_catboost_residual` |
| `lgbq_search_external_interaction_catboost_oof_cap0.25_s0.5` | 0.4374 | 1.0499 | 3.6635 | 0.8557 | `cold_lgbq_first_catboost_residual` |
| `lgbq_search_external_interaction_catboost_oof_cap0.35_s0.5` | 0.4374 | 1.0502 | 3.6635 | 0.8558 | `cold_lgbq_first_catboost_residual` |
| `lgbq_search_external_interaction_catboost_oof_cap0.5_s0.5` | 0.4374 | 1.0503 | 3.6635 | 0.8558 | `cold_lgbq_first_catboost_residual` |
| `base_lgbq_search_external_interaction` | 0.4421 | 1.0484 | 3.3537 | 0.8567 | `cold_lgbq_first_catboost_residual_base` |

## 설정/피처 맵

| experiment_id | candidate | base_model | base_loss | residual_model | feature_strategy | hypothesis | n_features | residual_train_source | features |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-Y6 | lgbq_search_external_interaction | lightgbm | quantile | catboost | LightGBM Quantile + 검색 전체 + 전시/갤러리 상호작용 | LightGBM 중앙 예측 뒤 CatBoost residual로 범주형 잔차 조합 보정 | 87 | 3-fold OOF base prediction on train | width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket, artist_meta_birth_year, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_for_sale_ratio, artist_meta_career_stage, artist_meta_total_works_log, artist_meta_for_sale_works_log, artist_meta_followers_log, artist_meta_birth_year_missing, artist_meta_total_works_missing, artist_meta_for_sale_works_missing, artist_meta_followers_missing, artist_meta_career_stage_missing, artist_meta_is_p1_flag, artist_meta_has_international_flag, is_high_price_candidate_flag, artist_meta_source, artist_meta_nationality, artist_meta_nationality_ko, search_result_count, search_source_count, search_art_context_count, search_exhibition_context_count, search_gallery_context_count, search_award_institution_context_count, search_social_context_count, search_market_context_count, search_homonym_context_count, search_art_match_ratio, search_exhibition_ratio, search_source_ratio, search_quality_score, search_result_count_log, search_art_context_count_log, search_exhibition_context_count_log, search_source_count_log, search_collected_flag, search_success_flag, search_quality_x_log_area, search_art_match_x_followers_log, search_exhibition_x_career_stage, search_quality_grade, search_size_quality_bucket, search_homonym_risk_grade, artist_exhibition_solo_count, artist_exhibition_group_count, artist_exhibition_fair_count, artist_exhibition_total_count, artist_exhibition_available_count, artist_exhibition_solo_count_missing, artist_exhibition_group_count_missing, artist_exhibition_fair_count_missing, artist_exhibition_solo_count_log, artist_exhibition_group_count_log, artist_exhibition_fair_count_log, artist_exhibition_total_count_log, gallery_tier_raw_numeric, gallery_tier_raw_available_flag, gallery_tier_validated_score, gallery_tier_validated_available_flag, gallery_tier_any_available_flag, gallery_city_count, gallery_city_count_log, gallery_tier_raw_bucket, gallery_tier_validated, gallery_ref_type, gallery_audit_status, gallery_feature_source, exhibition_total_x_log_area, exhibition_total_x_followers_log, gallery_validated_x_followers_log, gallery_tier_x_exhibition_total_log, exhibition_size_bucket, gallery_exhibition_bucket |
