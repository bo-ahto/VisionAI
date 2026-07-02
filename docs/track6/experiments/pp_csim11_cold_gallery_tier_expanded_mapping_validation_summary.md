# Cold 확장 갤러리 티어 매핑 검증

- 작성일: 2026-06-18T16:20:38
- 목적: 보유 원천 데이터의 갤러리명/원천 tier/티어 리스트 exact match를 합쳐 갤러리 티어 coverage를 확장했을 때 Cold 성능이 개선되는지 검증한다.
- 조건: `artist_key`, 같은 작가 가격 이력, `artist_key` lookup 후처리, `search_*`, 외부 live 검색 미사용.
- 구조: 유사작품 k160 + LightGBM Quantile q45 고정, 확장 갤러리 피처 추가 여부만 변경.
- 갤러리 사전: `data/art_gallery_tier_list_v3.xlsx - 전체 리스트.csv` / 89개 항목.

## 1. Test 결과: MdAPE 기준
| candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | APE_gt_1 | APE_gt_2 | APE_gt_5 | APE_gt_10 | n_features | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_current_meta | test | 0.471031 | 0.999148 | 2.569218 | 0.880774 | 0.310745 | 0.532430 | 501 | 233 | 74 | 37 | 45 | 현재 k160 q45 전체 user_meta_core_bucket 피처 참고 |
| artwork_gallery_context | test | 0.476178 | 1.113353 | 3.949693 | 0.917599 | 0.309777 | 0.522427 | 542 | 245 | 144 | 43 | 20 | artwork_only + 갤러리 티어/유형/감사 상태 |
| similarity_gallery_context | test | 0.477820 | 1.070466 | 3.624651 | 0.907476 | 0.307841 | 0.520813 | 515 | 249 | 95 | 41 | 31 | similarity_only + 갤러리 티어/유형/감사 상태 |
| enterable_gallery_context | test | 0.489231 | 1.083027 | 2.632958 | 0.907953 | 0.317844 | 0.507583 | 584 | 290 | 76 | 43 | 41 | enterable_only + 갤러리 티어/유형/감사 상태 |
| artwork_only | test | 0.490823 | 1.159634 | 3.677973 | 0.941292 | 0.300097 | 0.515973 | 543 | 241 | 137 | 51 | 12 | 작가 메타와 유사작품 통계를 모두 제거하고 작품 피처만 사용 |
| similarity_only | test | 0.493210 | 1.116201 | 3.748102 | 0.932119 | 0.302678 | 0.506615 | 520 | 246 | 136 | 49 | 23 | 작가 메타 없이 작품 피처 + 유사작품 k160 통계만 사용 |
| enterable_only | test | 0.496699 | 1.086514 | 2.452153 | 0.909771 | 0.322039 | 0.503066 | 578 | 232 | 66 | 43 | 33 | 운영 입력 가능성이 높은 작가 메타만 사용 |
| enterable_gallery_tier | test | 0.502329 | 1.081851 | 2.711593 | 0.912006 | 0.313004 | 0.497580 | 599 | 294 | 74 | 43 | 37 | enterable_only + 갤러리 티어 점수/가용 flag |

## 2. Test 결과: APE > 5 기준
| candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | APE_gt_1 | APE_gt_2 | APE_gt_5 | APE_gt_10 | n_features | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| enterable_only | test | 0.496699 | 1.086514 | 2.452153 | 0.909771 | 0.322039 | 0.503066 | 578 | 232 | 66 | 43 | 33 | 운영 입력 가능성이 높은 작가 메타만 사용 |
| full_current_meta | test | 0.471031 | 0.999148 | 2.569218 | 0.880774 | 0.310745 | 0.532430 | 501 | 233 | 74 | 37 | 45 | 현재 k160 q45 전체 user_meta_core_bucket 피처 참고 |
| enterable_gallery_tier | test | 0.502329 | 1.081851 | 2.711593 | 0.912006 | 0.313004 | 0.497580 | 599 | 294 | 74 | 43 | 37 | enterable_only + 갤러리 티어 점수/가용 flag |
| enterable_gallery_context | test | 0.489231 | 1.083027 | 2.632958 | 0.907953 | 0.317844 | 0.507583 | 584 | 290 | 76 | 43 | 41 | enterable_only + 갤러리 티어/유형/감사 상태 |
| similarity_gallery_context | test | 0.477820 | 1.070466 | 3.624651 | 0.907476 | 0.307841 | 0.520813 | 515 | 249 | 95 | 41 | 31 | similarity_only + 갤러리 티어/유형/감사 상태 |
| similarity_only | test | 0.493210 | 1.116201 | 3.748102 | 0.932119 | 0.302678 | 0.506615 | 520 | 246 | 136 | 49 | 23 | 작가 메타 없이 작품 피처 + 유사작품 k160 통계만 사용 |
| artwork_only | test | 0.490823 | 1.159634 | 3.677973 | 0.941292 | 0.300097 | 0.515973 | 543 | 241 | 137 | 51 | 12 | 작가 메타와 유사작품 통계를 모두 제거하고 작품 피처만 사용 |
| artwork_gallery_context | test | 0.476178 | 1.113353 | 3.949693 | 0.917599 | 0.309777 | 0.522427 | 542 | 245 | 144 | 43 | 20 | artwork_only + 갤러리 티어/유형/감사 상태 |

## 3. 갤러리 티어 커버리지
| split | n | gallery_tier_available_n | gallery_tier_available_rate | gallery_audit_ok_n | mapping_sources |
| --- | --- | --- | --- | --- | --- |
| train | 26914 | 16476 | 0.612172 | 16476 | {"source_raw_tier": 16285, "unmatched": 10438, "dictionary_exact": 172, "validated_audit": 19} |
| validation | 2753 | 1905 | 0.691972 | 1905 | {"source_raw_tier": 1902, "unmatched": 848, "dictionary_exact": 3} |
| test | 3099 | 1750 | 0.564698 | 1750 | {"source_raw_tier": 1702, "unmatched": 1349, "validated_audit": 32, "dictionary_exact": 16} |

## 4. 가격대별 진단
| candidate | split | segment | n | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| artwork_gallery_context | test | 1m_3m | 866 | 0.515381 | 0.835740 | 2.356631 | 0.701980 | 58 | 10 |
| artwork_only | test | 1m_3m | 866 | 0.494830 | 0.883420 | 2.445674 | 0.718732 | 66 | 8 |
| enterable_gallery_context | test | 1m_3m | 866 | 0.488515 | 0.894597 | 2.610320 | 0.717828 | 82 | 8 |
| enterable_gallery_tier | test | 1m_3m | 866 | 0.492113 | 0.903778 | 2.702496 | 0.727534 | 83 | 9 |
| enterable_only | test | 1m_3m | 866 | 0.509186 | 0.915907 | 2.500168 | 0.726037 | 75 | 8 |
| full_current_meta | test | 1m_3m | 866 | 0.482545 | 0.703997 | 2.010462 | 0.652357 | 45 | 6 |
| similarity_gallery_context | test | 1m_3m | 866 | 0.483696 | 0.757028 | 2.144424 | 0.676761 | 52 | 9 |
| similarity_only | test | 1m_3m | 866 | 0.479702 | 0.819370 | 2.291546 | 0.706104 | 62 | 10 |
| artwork_gallery_context | test | 3m_10m | 1057 | 0.405033 | 0.465949 | 1.017433 | 0.634790 | 15 | 3 |
| artwork_only | test | 3m_10m | 1057 | 0.435881 | 0.476031 | 1.014664 | 0.663038 | 10 | 3 |
| enterable_gallery_context | test | 3m_10m | 1057 | 0.427915 | 0.519292 | 1.227647 | 0.701942 | 16 | 2 |
| enterable_gallery_tier | test | 3m_10m | 1057 | 0.445381 | 0.526391 | 1.275728 | 0.706909 | 17 | 2 |
| enterable_only | test | 3m_10m | 1057 | 0.429399 | 0.512366 | 1.222818 | 0.706357 | 15 | 2 |
| full_current_meta | test | 3m_10m | 1057 | 0.421007 | 0.463703 | 0.940966 | 0.653641 | 12 | 2 |
| similarity_gallery_context | test | 3m_10m | 1057 | 0.399854 | 0.477828 | 1.124053 | 0.657273 | 15 | 2 |
| similarity_only | test | 3m_10m | 1057 | 0.434298 | 0.493292 | 1.073611 | 0.679429 | 19 | 4 |
| artwork_gallery_context | test | gt_10m | 636 | 0.498223 | 0.484684 | 0.909559 | 1.111201 | 0 | 0 |
| artwork_only | test | gt_10m | 636 | 0.515748 | 0.500802 | 0.915004 | 1.144631 | 0 | 0 |
| enterable_gallery_context | test | gt_10m | 636 | 0.454519 | 0.484675 | 0.907380 | 1.090815 | 1 | 0 |
| enterable_gallery_tier | test | gt_10m | 636 | 0.466337 | 0.489528 | 0.910587 | 1.095761 | 2 | 0 |
| enterable_only | test | gt_10m | 636 | 0.459469 | 0.478404 | 0.898497 | 1.100473 | 0 | 0 |
| full_current_meta | test | gt_10m | 636 | 0.483473 | 0.486703 | 0.899568 | 1.106711 | 0 | 0 |
| similarity_gallery_context | test | gt_10m | 636 | 0.504920 | 0.488755 | 0.907417 | 1.098623 | 0 | 0 |
| similarity_only | test | gt_10m | 636 | 0.513947 | 0.489653 | 0.905136 | 1.124066 | 0 | 0 |
| artwork_gallery_context | test | lt_1m | 540 | 1.081562 | 3.566230 | 25.416185 | 1.341185 | 172 | 131 |
| artwork_only | test | lt_1m | 540 | 0.968759 | 3.716647 | 24.430386 | 1.361169 | 165 | 126 |
| enterable_gallery_context | test | lt_1m | 540 | 0.940796 | 3.193395 | 24.212427 | 1.240480 | 191 | 66 |
| enterable_gallery_tier | test | lt_1m | 540 | 0.967410 | 3.152313 | 23.346004 | 1.237818 | 192 | 63 |
| enterable_only | test | lt_1m | 540 | 0.880594 | 3.200176 | 24.822371 | 1.225420 | 142 | 56 |
| full_current_meta | test | lt_1m | 540 | 0.815276 | 3.124113 | 26.272536 | 1.220932 | 176 | 66 |
| similarity_gallery_context | test | lt_1m | 540 | 0.915215 | 3.418290 | 24.291326 | 1.313159 | 182 | 84 |
| similarity_only | test | lt_1m | 540 | 0.871953 | 3.549452 | 23.458016 | 1.339736 | 165 | 122 |

## 5. 피처 세트 정의

- `enterable_only`: `width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket, artist_meta_birth_year, artist_meta_career_stage, artist_meta_birth_year_missing, artist_meta_career_stage_missing, artist_meta_nationality, artist_meta_nationality_ko, artist_birth_period_bucket, artist_career_stage_bucket, medium_birth_period_bucket, career_size_bucket, artwork_sim_k160_ref_n, artwork_sim_k160_ref_log_price_median, artwork_sim_k160_ref_log_price_q25, artwork_sim_k160_ref_log_price_q75, artwork_sim_k160_ref_log_price_iqr, artwork_sim_k160_ref_log_price_mean, artwork_sim_k160_ref_log_price_std, artwork_sim_k160_ref_area_price_median, artwork_sim_k160_ref_similarity_mean, artwork_sim_k160_ref_similarity_max, artwork_sim_k160_ref_similarity_min`
- `enterable_gallery_tier`: `width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket, artist_meta_birth_year, artist_meta_career_stage, artist_meta_birth_year_missing, artist_meta_career_stage_missing, artist_meta_nationality, artist_meta_nationality_ko, artist_birth_period_bucket, artist_career_stage_bucket, medium_birth_period_bucket, career_size_bucket, artwork_sim_k160_ref_n, artwork_sim_k160_ref_log_price_median, artwork_sim_k160_ref_log_price_q25, artwork_sim_k160_ref_log_price_q75, artwork_sim_k160_ref_log_price_iqr, artwork_sim_k160_ref_log_price_mean, artwork_sim_k160_ref_log_price_std, artwork_sim_k160_ref_area_price_median, artwork_sim_k160_ref_similarity_mean, artwork_sim_k160_ref_similarity_max, artwork_sim_k160_ref_similarity_min, user_gallery_tier_score, user_gallery_tier_available_flag, user_gallery_tier_missing_flag, user_gallery_tier_bucket`
- `enterable_gallery_context`: `width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket, artist_meta_birth_year, artist_meta_career_stage, artist_meta_birth_year_missing, artist_meta_career_stage_missing, artist_meta_nationality, artist_meta_nationality_ko, artist_birth_period_bucket, artist_career_stage_bucket, medium_birth_period_bucket, career_size_bucket, artwork_sim_k160_ref_n, artwork_sim_k160_ref_log_price_median, artwork_sim_k160_ref_log_price_q25, artwork_sim_k160_ref_log_price_q75, artwork_sim_k160_ref_log_price_iqr, artwork_sim_k160_ref_log_price_mean, artwork_sim_k160_ref_log_price_std, artwork_sim_k160_ref_area_price_median, artwork_sim_k160_ref_similarity_mean, artwork_sim_k160_ref_similarity_max, artwork_sim_k160_ref_similarity_min, user_gallery_tier_score, user_gallery_tier_available_flag, user_gallery_tier_missing_flag, user_gallery_tier_bucket, user_gallery_ref_type, user_gallery_audit_status, user_gallery_category, user_gallery_mapping_source`
- `similarity_only`: `width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket, artwork_sim_k160_ref_n, artwork_sim_k160_ref_log_price_median, artwork_sim_k160_ref_log_price_q25, artwork_sim_k160_ref_log_price_q75, artwork_sim_k160_ref_log_price_iqr, artwork_sim_k160_ref_log_price_mean, artwork_sim_k160_ref_log_price_std, artwork_sim_k160_ref_area_price_median, artwork_sim_k160_ref_similarity_mean, artwork_sim_k160_ref_similarity_max, artwork_sim_k160_ref_similarity_min`
- `similarity_gallery_context`: `width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket, artwork_sim_k160_ref_n, artwork_sim_k160_ref_log_price_median, artwork_sim_k160_ref_log_price_q25, artwork_sim_k160_ref_log_price_q75, artwork_sim_k160_ref_log_price_iqr, artwork_sim_k160_ref_log_price_mean, artwork_sim_k160_ref_log_price_std, artwork_sim_k160_ref_area_price_median, artwork_sim_k160_ref_similarity_mean, artwork_sim_k160_ref_similarity_max, artwork_sim_k160_ref_similarity_min, user_gallery_tier_score, user_gallery_tier_available_flag, user_gallery_tier_missing_flag, user_gallery_tier_bucket, user_gallery_ref_type, user_gallery_audit_status, user_gallery_category, user_gallery_mapping_source`
- `artwork_only`: `width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket`
- `artwork_gallery_context`: `width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket, user_gallery_tier_score, user_gallery_tier_available_flag, user_gallery_tier_missing_flag, user_gallery_tier_bucket, user_gallery_ref_type, user_gallery_audit_status, user_gallery_category, user_gallery_mapping_source`
- `full_current_meta`: `width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket, artist_meta_birth_year, artist_meta_total_works, artist_meta_followers, artist_meta_career_stage, artist_meta_total_works_log, artist_meta_followers_log, artist_meta_birth_year_missing, artist_meta_total_works_missing, artist_meta_followers_missing, artist_meta_career_stage_missing, artist_meta_is_p1_flag, artist_meta_has_international_flag, artist_meta_nationality, artist_meta_nationality_ko, artist_birth_period_bucket, artist_inventory_bucket, artist_followers_bucket, artist_career_stage_bucket, artist_meta_completeness_bucket, medium_birth_period_bucket, support_meta_completeness_bucket, career_size_bucket, artwork_sim_k160_ref_n, artwork_sim_k160_ref_log_price_median, artwork_sim_k160_ref_log_price_q25, artwork_sim_k160_ref_log_price_q75, artwork_sim_k160_ref_log_price_iqr, artwork_sim_k160_ref_log_price_mean, artwork_sim_k160_ref_log_price_std, artwork_sim_k160_ref_area_price_median, artwork_sim_k160_ref_similarity_mean, artwork_sim_k160_ref_similarity_max, artwork_sim_k160_ref_similarity_min`

## 6. 결론

- MdAPE 기준 최상위 후보는 `full_current_meta`이다.
- APE > 5 안정성 기준 최상위 후보는 `enterable_only`이다.
- raw source tier는 Saatchi/1차시장 원천 tier를 그대로 사용하므로, 운영 사전 기준으로 쓰려면 갤러리명 alias와 티어 정책 검수가 추가로 필요하다.
- 이번 실험은 갤러리 티어 coverage를 늘렸을 때의 가능성 검증이며, 최종 채택 전에는 매핑 사전 버전 고정과 사람이 검수한 alias 확장이 필요하다.