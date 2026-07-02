# Cold 갤러리/작가 프로필 유사 그룹핑 검증

- 작성일: 2026-06-22T15:32:24
- 목적: Cold에서 갤러리/전시/작가 프로필 문맥을 가격군 그룹핑에 사용할 수 있는지 검증한다.
- 엄격 조건: `artist_key`, 동일 작가 가격 이력, artist_key lookup, `search_*`, 외부 live 검색 미사용.
- 기준: LightGBM Quantile q50, 유사 이웃 기준가격 통계 k80.

## 1. Test 결과
| candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 | APE_gt_10 | n_model_features | n_similarity_features | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base_artwork_similarity_k80 | test | 0.473266 | 1.084235 | 3.198446 | 0.881226 | 277 | 79 | 39 | 37 | 12 | 작품+기본 작가 메타, 유사 이웃은 작품 조건만 사용 |
| direct_gallery_profile_k80 | test | 0.459030 | 1.095882 | 3.322819 | 0.879997 | 299 | 81 | 39 | 63 | 12 | 갤러리/전시 문맥을 모델 입력에 직접 추가 |
| similarity_gallery_profile_k80 | test | 0.524108 | 1.220084 | 3.337424 | 0.937043 | 298 | 86 | 50 | 37 | 56 | 갤러리/전시 문맥은 유사 이웃 선택에만 사용 |
| direct_and_similarity_gallery_profile_k80 | test | 0.516516 | 1.221468 | 3.379139 | 0.935294 | 282 | 85 | 48 | 63 | 56 | 갤러리/전시 문맥을 모델 입력과 유사 이웃 선택에 모두 사용 |

## 2. Validation 결과
| candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 | APE_gt_10 | n_model_features | n_similarity_features | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base_artwork_similarity_k80 | validation | 0.375690 | 0.556960 | 1.536828 | 0.665134 | 86 | 23 | 4 | 37 | 12 | 작품+기본 작가 메타, 유사 이웃은 작품 조건만 사용 |
| direct_gallery_profile_k80 | validation | 0.415704 | 0.615427 | 1.771437 | 0.677429 | 101 | 25 | 4 | 63 | 12 | 갤러리/전시 문맥을 모델 입력에 직접 추가 |
| similarity_gallery_profile_k80 | validation | 0.481720 | 0.844461 | 3.076680 | 0.789850 | 277 | 34 | 9 | 37 | 56 | 갤러리/전시 문맥은 유사 이웃 선택에만 사용 |
| direct_and_similarity_gallery_profile_k80 | validation | 0.473339 | 0.891382 | 3.244529 | 0.803685 | 315 | 65 | 12 | 63 | 56 | 갤러리/전시 문맥을 모델 입력과 유사 이웃 선택에 모두 사용 |

## 3. 갤러리/전시 피처 커버리지
| split | n | gallery_any_n | gallery_any_rate | gallery_validated_n | gallery_validated_rate | exhibition_available_n | exhibition_available_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| train | 26914 | 16304 | 0.605781 | 19 | 0.000706 | 16284 | 0.605038 |
| validation | 2753 | 1902 | 0.690883 | 0 | 0.000000 | 1902 | 0.690883 |
| test | 3099 | 1734 | 0.559535 | 32 | 0.010326 | 1693 | 0.546305 |

## 4. 가격대별 Test 진단
| candidate | split | segment | n | MdAPE | MAPE | p95_APE | APE_gt_2 | APE_gt_5 | APE_gt_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base_artwork_similarity_k80 | test | 1m_3m | 866 | 0.509475 | 0.780011 | 2.163101 | 63 | 6 | 0 |
| base_artwork_similarity_k80 | test | 3m_10m | 1057 | 0.383693 | 0.478722 | 1.097567 | 22 | 4 | 0 |
| base_artwork_similarity_k80 | test | gt_10m | 636 | 0.476171 | 0.473754 | 0.904765 | 0 | 0 | 0 |
| base_artwork_similarity_k80 | test | lt_1m | 540 | 0.932203 | 3.476366 | 28.137774 | 192 | 69 | 39 |
| direct_and_similarity_gallery_profile_k80 | test | 1m_3m | 866 | 0.594807 | 0.822800 | 2.175546 | 57 | 7 | 0 |
| direct_and_similarity_gallery_profile_k80 | test | 3m_10m | 1057 | 0.439894 | 0.525749 | 1.123256 | 26 | 4 | 1 |
| direct_and_similarity_gallery_profile_k80 | test | gt_10m | 636 | 0.499082 | 0.497342 | 0.916119 | 2 | 0 | 0 |
| direct_and_similarity_gallery_profile_k80 | test | lt_1m | 540 | 1.159415 | 4.075482 | 30.441979 | 197 | 74 | 47 |
| direct_gallery_profile_k80 | test | 1m_3m | 866 | 0.522818 | 0.799580 | 2.458534 | 74 | 6 | 0 |
| direct_gallery_profile_k80 | test | 3m_10m | 1057 | 0.380105 | 0.486410 | 1.221370 | 24 | 3 | 0 |
| direct_gallery_profile_k80 | test | gt_10m | 636 | 0.436255 | 0.460736 | 0.895682 | 0 | 0 | 0 |
| direct_gallery_profile_k80 | test | lt_1m | 540 | 1.036569 | 3.512110 | 26.590978 | 201 | 72 | 39 |
| similarity_gallery_profile_k80 | test | 1m_3m | 866 | 0.565369 | 0.845040 | 2.339382 | 72 | 7 | 0 |
| similarity_gallery_profile_k80 | test | 3m_10m | 1057 | 0.456796 | 0.550248 | 1.217824 | 26 | 4 | 1 |
| similarity_gallery_profile_k80 | test | gt_10m | 636 | 0.494506 | 0.500451 | 0.918757 | 1 | 0 | 0 |
| similarity_gallery_profile_k80 | test | lt_1m | 540 | 1.062988 | 3.980256 | 30.968465 | 199 | 75 | 49 |

## 5. 후보 정의
### base_artwork_similarity_k80
- 정책: 작품+기본 작가 메타, 유사 이웃은 작품 조건만 사용
- 모델 입력 피처: `width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket, artist_meta_birth_year, artist_meta_total_works, artist_meta_followers, artist_meta_career_stage, artist_meta_total_works_log, artist_meta_followers_log, artist_meta_birth_year_missing, artist_meta_total_works_missing, artist_meta_followers_missing, artist_meta_career_stage_missing, artist_meta_is_p1_flag, artist_meta_has_international_flag, artist_meta_nationality, artist_meta_nationality_ko, base_artwork_similarity_k80_ref_k80_ref_n, base_artwork_similarity_k80_ref_k80_ref_log_price_median, base_artwork_similarity_k80_ref_k80_ref_log_price_q25, base_artwork_similarity_k80_ref_k80_ref_log_price_q75, base_artwork_similarity_k80_ref_k80_ref_log_price_iqr, base_artwork_similarity_k80_ref_k80_ref_log_price_mean, base_artwork_similarity_k80_ref_k80_ref_log_price_std, base_artwork_similarity_k80_ref_k80_ref_area_price_median, base_artwork_similarity_k80_ref_k80_ref_similarity_mean, base_artwork_similarity_k80_ref_k80_ref_similarity_max, base_artwork_similarity_k80_ref_k80_ref_similarity_min`
- 유사 이웃 선택 피처: `width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket`

### direct_gallery_profile_k80
- 정책: 갤러리/전시 문맥을 모델 입력에 직접 추가
- 모델 입력 피처: `width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket, artist_meta_birth_year, artist_meta_total_works, artist_meta_followers, artist_meta_career_stage, artist_meta_total_works_log, artist_meta_followers_log, artist_meta_birth_year_missing, artist_meta_total_works_missing, artist_meta_followers_missing, artist_meta_career_stage_missing, artist_meta_is_p1_flag, artist_meta_has_international_flag, artist_meta_nationality, artist_meta_nationality_ko, artist_exhibition_solo_count_log, artist_exhibition_group_count_log, artist_exhibition_fair_count_log, artist_exhibition_total_count_log, artist_exhibition_available_count, gallery_tier_raw_numeric, gallery_tier_raw_available_flag, gallery_tier_validated_score, gallery_tier_validated_available_flag, gallery_tier_any_available_flag, gallery_city_count_log, gallery_tier_raw_bucket, gallery_tier_validated, gallery_ref_type, gallery_audit_status, gallery_feature_source, gallery_tier_x_exhibition_total_log, exhibition_size_bucket, gallery_exhibition_bucket, profile_exhibition_bucket, profile_gallery_tier_bucket, profile_gallery_source_bucket, profile_gallery_exhibition_bucket, profile_career_gallery_bucket, profile_medium_gallery_bucket, profile_size_exhibition_bucket, direct_gallery_profile_k80_ref_k80_ref_n, direct_gallery_profile_k80_ref_k80_ref_log_price_median, direct_gallery_profile_k80_ref_k80_ref_log_price_q25, direct_gallery_profile_k80_ref_k80_ref_log_price_q75, direct_gallery_profile_k80_ref_k80_ref_log_price_iqr, direct_gallery_profile_k80_ref_k80_ref_log_price_mean, direct_gallery_profile_k80_ref_k80_ref_log_price_std, direct_gallery_profile_k80_ref_k80_ref_area_price_median, direct_gallery_profile_k80_ref_k80_ref_similarity_mean, direct_gallery_profile_k80_ref_k80_ref_similarity_max, direct_gallery_profile_k80_ref_k80_ref_similarity_min`
- 유사 이웃 선택 피처: `width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket`

### similarity_gallery_profile_k80
- 정책: 갤러리/전시 문맥은 유사 이웃 선택에만 사용
- 모델 입력 피처: `width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket, artist_meta_birth_year, artist_meta_total_works, artist_meta_followers, artist_meta_career_stage, artist_meta_total_works_log, artist_meta_followers_log, artist_meta_birth_year_missing, artist_meta_total_works_missing, artist_meta_followers_missing, artist_meta_career_stage_missing, artist_meta_is_p1_flag, artist_meta_has_international_flag, artist_meta_nationality, artist_meta_nationality_ko, similarity_gallery_profile_k80_ref_k80_ref_n, similarity_gallery_profile_k80_ref_k80_ref_log_price_median, similarity_gallery_profile_k80_ref_k80_ref_log_price_q25, similarity_gallery_profile_k80_ref_k80_ref_log_price_q75, similarity_gallery_profile_k80_ref_k80_ref_log_price_iqr, similarity_gallery_profile_k80_ref_k80_ref_log_price_mean, similarity_gallery_profile_k80_ref_k80_ref_log_price_std, similarity_gallery_profile_k80_ref_k80_ref_area_price_median, similarity_gallery_profile_k80_ref_k80_ref_similarity_mean, similarity_gallery_profile_k80_ref_k80_ref_similarity_max, similarity_gallery_profile_k80_ref_k80_ref_similarity_min`
- 유사 이웃 선택 피처: `width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket, artist_meta_birth_year, artist_meta_total_works, artist_meta_followers, artist_meta_career_stage, artist_meta_total_works_log, artist_meta_followers_log, artist_meta_birth_year_missing, artist_meta_total_works_missing, artist_meta_followers_missing, artist_meta_career_stage_missing, artist_meta_is_p1_flag, artist_meta_has_international_flag, artist_meta_nationality, artist_meta_nationality_ko, artist_birth_period_bucket, artist_career_stage_bucket, artist_inventory_bucket, artist_followers_bucket, artist_exhibition_solo_count_log, artist_exhibition_group_count_log, artist_exhibition_fair_count_log, artist_exhibition_total_count_log, artist_exhibition_available_count, gallery_tier_raw_numeric, gallery_tier_raw_available_flag, gallery_tier_validated_score, gallery_tier_validated_available_flag, gallery_tier_any_available_flag, gallery_city_count_log, gallery_tier_raw_bucket, gallery_tier_validated, gallery_ref_type, gallery_audit_status, gallery_feature_source, gallery_tier_x_exhibition_total_log, exhibition_size_bucket, gallery_exhibition_bucket, profile_exhibition_bucket, profile_gallery_tier_bucket, profile_gallery_source_bucket, profile_gallery_exhibition_bucket, profile_career_gallery_bucket, profile_medium_gallery_bucket, profile_size_exhibition_bucket`

### direct_and_similarity_gallery_profile_k80
- 정책: 갤러리/전시 문맥을 모델 입력과 유사 이웃 선택에 모두 사용
- 모델 입력 피처: `width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket, artist_meta_birth_year, artist_meta_total_works, artist_meta_followers, artist_meta_career_stage, artist_meta_total_works_log, artist_meta_followers_log, artist_meta_birth_year_missing, artist_meta_total_works_missing, artist_meta_followers_missing, artist_meta_career_stage_missing, artist_meta_is_p1_flag, artist_meta_has_international_flag, artist_meta_nationality, artist_meta_nationality_ko, artist_exhibition_solo_count_log, artist_exhibition_group_count_log, artist_exhibition_fair_count_log, artist_exhibition_total_count_log, artist_exhibition_available_count, gallery_tier_raw_numeric, gallery_tier_raw_available_flag, gallery_tier_validated_score, gallery_tier_validated_available_flag, gallery_tier_any_available_flag, gallery_city_count_log, gallery_tier_raw_bucket, gallery_tier_validated, gallery_ref_type, gallery_audit_status, gallery_feature_source, gallery_tier_x_exhibition_total_log, exhibition_size_bucket, gallery_exhibition_bucket, profile_exhibition_bucket, profile_gallery_tier_bucket, profile_gallery_source_bucket, profile_gallery_exhibition_bucket, profile_career_gallery_bucket, profile_medium_gallery_bucket, profile_size_exhibition_bucket, direct_and_similarity_gallery_profile_k80_ref_k80_ref_n, direct_and_similarity_gallery_profile_k80_ref_k80_ref_log_price_median, direct_and_similarity_gallery_profile_k80_ref_k80_ref_log_price_q25, direct_and_similarity_gallery_profile_k80_ref_k80_ref_log_price_q75, direct_and_similarity_gallery_profile_k80_ref_k80_ref_log_price_iqr, direct_and_similarity_gallery_profile_k80_ref_k80_ref_log_price_mean, direct_and_similarity_gallery_profile_k80_ref_k80_ref_log_price_std, direct_and_similarity_gallery_profile_k80_ref_k80_ref_area_price_median, direct_and_similarity_gallery_profile_k80_ref_k80_ref_similarity_mean, direct_and_similarity_gallery_profile_k80_ref_k80_ref_similarity_max, direct_and_similarity_gallery_profile_k80_ref_k80_ref_similarity_min`
- 유사 이웃 선택 피처: `width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket, artist_meta_birth_year, artist_meta_total_works, artist_meta_followers, artist_meta_career_stage, artist_meta_total_works_log, artist_meta_followers_log, artist_meta_birth_year_missing, artist_meta_total_works_missing, artist_meta_followers_missing, artist_meta_career_stage_missing, artist_meta_is_p1_flag, artist_meta_has_international_flag, artist_meta_nationality, artist_meta_nationality_ko, artist_birth_period_bucket, artist_career_stage_bucket, artist_inventory_bucket, artist_followers_bucket, artist_exhibition_solo_count_log, artist_exhibition_group_count_log, artist_exhibition_fair_count_log, artist_exhibition_total_count_log, artist_exhibition_available_count, gallery_tier_raw_numeric, gallery_tier_raw_available_flag, gallery_tier_validated_score, gallery_tier_validated_available_flag, gallery_tier_any_available_flag, gallery_city_count_log, gallery_tier_raw_bucket, gallery_tier_validated, gallery_ref_type, gallery_audit_status, gallery_feature_source, gallery_tier_x_exhibition_total_log, exhibition_size_bucket, gallery_exhibition_bucket, profile_exhibition_bucket, profile_gallery_tier_bucket, profile_gallery_source_bucket, profile_gallery_exhibition_bucket, profile_career_gallery_bucket, profile_medium_gallery_bucket, profile_size_exhibition_bucket`

## 6. 해석

- 갤러리/전시 문맥이 좋아 보이더라도 raw source tier 비중이 높으면 운영 채택 전에 입력 방식과 tier 사전 버전을 고정해야 한다.
- `gallery_validated_rate`가 낮으면 검증된 갤러리 티어만으로는 효과를 기대하기 어렵고, 사용자 선택형 갤러리 입력 또는 운영 검수 사전이 필요하다.
- 이번 실험에서 우세 후보는 Cold 운영 후보로 바로 승격하기보다, 동일 split 재현성과 APE > 5 tail risk를 함께 보고 후속 freezing 대상으로 삼는다.