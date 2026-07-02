# Cold 갤러리 티어 피처 검증

- 작성일: 2026-06-18T16:16:05
- 목적: 사용자가 팝업으로 선택 가능한 소속 갤러리 정보를 갤러리 티어/유형 피처로 넣었을 때 Cold 성능이 개선되는지 검증한다.
- 조건: `artist_key`, 같은 작가 가격 이력, `artist_key` lookup 후처리, `search_*`, 외부 live 검색 미사용.
- 구조: 유사작품 k160 + LightGBM Quantile q45 고정, 갤러리 피처 추가 여부만 변경.
- 갤러리 사전: `data/art_gallery_tier_list_v3.xlsx - 전체 리스트.csv` / 89개 항목.

## 1. Test 결과: MdAPE 기준
| candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | APE_gt_1 | APE_gt_2 | APE_gt_5 | APE_gt_10 | n_features | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_current_meta | test | 0.471031 | 0.999148 | 2.569218 | 0.880774 | 0.310745 | 0.532430 | 501 | 233 | 74 | 37 | 45 | 현재 k160 q45 전체 user_meta_core_bucket 피처 참고 |
| artwork_gallery_context | test | 0.482013 | 1.115537 | 3.723222 | 0.925707 | 0.298483 | 0.518232 | 548 | 258 | 142 | 45 | 19 | artwork_only + 갤러리 티어/유형/감사 상태 |
| similarity_gallery_context | test | 0.483320 | 1.108546 | 3.531052 | 0.925596 | 0.314940 | 0.519200 | 499 | 251 | 128 | 48 | 30 | similarity_only + 갤러리 티어/유형/감사 상태 |
| artwork_only | test | 0.490823 | 1.159634 | 3.677973 | 0.941292 | 0.300097 | 0.515973 | 543 | 241 | 137 | 51 | 12 | 작가 메타와 유사작품 통계를 모두 제거하고 작품 피처만 사용 |
| similarity_only | test | 0.493210 | 1.116201 | 3.748102 | 0.932119 | 0.302678 | 0.506615 | 520 | 246 | 136 | 49 | 23 | 작가 메타 없이 작품 피처 + 유사작품 k160 통계만 사용 |
| enterable_only | test | 0.496699 | 1.086514 | 2.452153 | 0.909771 | 0.322039 | 0.503066 | 578 | 232 | 66 | 43 | 33 | 운영 입력 가능성이 높은 작가 메타만 사용 |
| enterable_gallery_tier | test | 0.496699 | 1.086514 | 2.452153 | 0.909771 | 0.322039 | 0.503066 | 578 | 232 | 66 | 43 | 37 | enterable_only + 갤러리 티어 점수/가용 flag |
| enterable_gallery_context | test | 0.497623 | 1.083618 | 2.551042 | 0.903068 | 0.319781 | 0.500807 | 582 | 283 | 65 | 43 | 40 | enterable_only + 갤러리 티어/유형/감사 상태 |

## 2. Test 결과: APE > 5 기준
| candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | APE_gt_1 | APE_gt_2 | APE_gt_5 | APE_gt_10 | n_features | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| enterable_gallery_context | test | 0.497623 | 1.083618 | 2.551042 | 0.903068 | 0.319781 | 0.500807 | 582 | 283 | 65 | 43 | 40 | enterable_only + 갤러리 티어/유형/감사 상태 |
| enterable_only | test | 0.496699 | 1.086514 | 2.452153 | 0.909771 | 0.322039 | 0.503066 | 578 | 232 | 66 | 43 | 33 | 운영 입력 가능성이 높은 작가 메타만 사용 |
| enterable_gallery_tier | test | 0.496699 | 1.086514 | 2.452153 | 0.909771 | 0.322039 | 0.503066 | 578 | 232 | 66 | 43 | 37 | enterable_only + 갤러리 티어 점수/가용 flag |
| full_current_meta | test | 0.471031 | 0.999148 | 2.569218 | 0.880774 | 0.310745 | 0.532430 | 501 | 233 | 74 | 37 | 45 | 현재 k160 q45 전체 user_meta_core_bucket 피처 참고 |
| similarity_gallery_context | test | 0.483320 | 1.108546 | 3.531052 | 0.925596 | 0.314940 | 0.519200 | 499 | 251 | 128 | 48 | 30 | similarity_only + 갤러리 티어/유형/감사 상태 |
| similarity_only | test | 0.493210 | 1.116201 | 3.748102 | 0.932119 | 0.302678 | 0.506615 | 520 | 246 | 136 | 49 | 23 | 작가 메타 없이 작품 피처 + 유사작품 k160 통계만 사용 |
| artwork_only | test | 0.490823 | 1.159634 | 3.677973 | 0.941292 | 0.300097 | 0.515973 | 543 | 241 | 137 | 51 | 12 | 작가 메타와 유사작품 통계를 모두 제거하고 작품 피처만 사용 |
| artwork_gallery_context | test | 0.482013 | 1.115537 | 3.723222 | 0.925707 | 0.298483 | 0.518232 | 548 | 258 | 142 | 45 | 19 | artwork_only + 갤러리 티어/유형/감사 상태 |

## 3. 갤러리 티어 커버리지
| split | n | gallery_tier_available_n | gallery_tier_available_rate | gallery_audit_ok_n |
| --- | --- | --- | --- | --- |
| train | 26914 | 19 | 0.000706 | 19 |
| validation | 2753 | 0 | 0.000000 | 0 |
| test | 3099 | 32 | 0.010326 | 32 |

## 4. 가격대별 진단
| candidate | split | segment | n | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| artwork_gallery_context | test | 1m_3m | 866 | 0.482363 | 0.851313 | 2.435278 | 0.710157 | 71 | 10 |
| artwork_only | test | 1m_3m | 866 | 0.494830 | 0.883420 | 2.445674 | 0.718732 | 66 | 8 |
| enterable_gallery_context | test | 1m_3m | 866 | 0.516718 | 0.884619 | 2.558418 | 0.715482 | 76 | 8 |
| enterable_gallery_tier | test | 1m_3m | 866 | 0.509186 | 0.915907 | 2.500168 | 0.726037 | 75 | 8 |
| enterable_only | test | 1m_3m | 866 | 0.509186 | 0.915907 | 2.500168 | 0.726037 | 75 | 8 |
| full_current_meta | test | 1m_3m | 866 | 0.482545 | 0.703997 | 2.010462 | 0.652357 | 45 | 6 |
| similarity_gallery_context | test | 1m_3m | 866 | 0.469647 | 0.802346 | 2.192613 | 0.689897 | 51 | 9 |
| similarity_only | test | 1m_3m | 866 | 0.479702 | 0.819370 | 2.291546 | 0.706104 | 62 | 10 |
| artwork_gallery_context | test | 3m_10m | 1057 | 0.420107 | 0.473451 | 0.996712 | 0.649918 | 14 | 3 |
| artwork_only | test | 3m_10m | 1057 | 0.435881 | 0.476031 | 1.014664 | 0.663038 | 10 | 3 |
| enterable_gallery_context | test | 3m_10m | 1057 | 0.440253 | 0.524386 | 1.238012 | 0.700466 | 17 | 2 |
| enterable_gallery_tier | test | 3m_10m | 1057 | 0.429399 | 0.512366 | 1.222818 | 0.706357 | 15 | 2 |
| enterable_only | test | 3m_10m | 1057 | 0.429399 | 0.512366 | 1.222818 | 0.706357 | 15 | 2 |
| full_current_meta | test | 3m_10m | 1057 | 0.421007 | 0.463703 | 0.940966 | 0.653641 | 12 | 2 |
| similarity_gallery_context | test | 3m_10m | 1057 | 0.426558 | 0.477854 | 1.119017 | 0.677252 | 14 | 2 |
| similarity_only | test | 3m_10m | 1057 | 0.434298 | 0.493292 | 1.073611 | 0.679429 | 19 | 4 |
| artwork_gallery_context | test | gt_10m | 636 | 0.500279 | 0.492584 | 0.908799 | 1.126483 | 0 | 0 |
| artwork_only | test | gt_10m | 636 | 0.515748 | 0.500802 | 0.915004 | 1.144631 | 0 | 0 |
| enterable_gallery_context | test | gt_10m | 636 | 0.446133 | 0.472029 | 0.891137 | 1.086875 | 0 | 0 |
| enterable_gallery_tier | test | gt_10m | 636 | 0.459469 | 0.478404 | 0.898497 | 1.100473 | 0 | 0 |
| enterable_only | test | gt_10m | 636 | 0.459469 | 0.478404 | 0.898497 | 1.100473 | 0 | 0 |
| full_current_meta | test | gt_10m | 636 | 0.483473 | 0.486703 | 0.899568 | 1.106711 | 0 | 0 |
| similarity_gallery_context | test | gt_10m | 636 | 0.505712 | 0.487045 | 0.908364 | 1.115321 | 0 | 0 |
| similarity_only | test | gt_10m | 636 | 0.513947 | 0.489653 | 0.905136 | 1.124066 | 0 | 0 |
| artwork_gallery_context | test | lt_1m | 540 | 0.978692 | 3.529799 | 24.528159 | 1.337052 | 173 | 129 |
| artwork_only | test | lt_1m | 540 | 0.968759 | 3.716647 | 24.430386 | 1.361169 | 165 | 126 |
| enterable_gallery_context | test | lt_1m | 540 | 0.908219 | 3.217718 | 24.940437 | 1.227832 | 190 | 55 |
| enterable_gallery_tier | test | lt_1m | 540 | 0.880594 | 3.200176 | 24.822371 | 1.225420 | 142 | 56 |
| enterable_only | test | lt_1m | 540 | 0.880594 | 3.200176 | 24.822371 | 1.225420 | 142 | 56 |
| full_current_meta | test | lt_1m | 540 | 0.815276 | 3.124113 | 26.272536 | 1.220932 | 176 | 66 |
| similarity_gallery_context | test | lt_1m | 540 | 0.827264 | 3.566112 | 24.416230 | 1.338090 | 186 | 117 |
| similarity_only | test | lt_1m | 540 | 0.871953 | 3.549452 | 23.458016 | 1.339736 | 165 | 122 |

## 5. 피처 세트 정의

- `enterable_only`: `width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket, artist_meta_birth_year, artist_meta_career_stage, artist_meta_birth_year_missing, artist_meta_career_stage_missing, artist_meta_nationality, artist_meta_nationality_ko, artist_birth_period_bucket, artist_career_stage_bucket, medium_birth_period_bucket, career_size_bucket, artwork_sim_k160_ref_n, artwork_sim_k160_ref_log_price_median, artwork_sim_k160_ref_log_price_q25, artwork_sim_k160_ref_log_price_q75, artwork_sim_k160_ref_log_price_iqr, artwork_sim_k160_ref_log_price_mean, artwork_sim_k160_ref_log_price_std, artwork_sim_k160_ref_area_price_median, artwork_sim_k160_ref_similarity_mean, artwork_sim_k160_ref_similarity_max, artwork_sim_k160_ref_similarity_min`
- `enterable_gallery_tier`: `width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket, artist_meta_birth_year, artist_meta_career_stage, artist_meta_birth_year_missing, artist_meta_career_stage_missing, artist_meta_nationality, artist_meta_nationality_ko, artist_birth_period_bucket, artist_career_stage_bucket, medium_birth_period_bucket, career_size_bucket, artwork_sim_k160_ref_n, artwork_sim_k160_ref_log_price_median, artwork_sim_k160_ref_log_price_q25, artwork_sim_k160_ref_log_price_q75, artwork_sim_k160_ref_log_price_iqr, artwork_sim_k160_ref_log_price_mean, artwork_sim_k160_ref_log_price_std, artwork_sim_k160_ref_area_price_median, artwork_sim_k160_ref_similarity_mean, artwork_sim_k160_ref_similarity_max, artwork_sim_k160_ref_similarity_min, user_gallery_tier_score, user_gallery_tier_available_flag, user_gallery_tier_missing_flag, user_gallery_tier_bucket`
- `enterable_gallery_context`: `width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket, artist_meta_birth_year, artist_meta_career_stage, artist_meta_birth_year_missing, artist_meta_career_stage_missing, artist_meta_nationality, artist_meta_nationality_ko, artist_birth_period_bucket, artist_career_stage_bucket, medium_birth_period_bucket, career_size_bucket, artwork_sim_k160_ref_n, artwork_sim_k160_ref_log_price_median, artwork_sim_k160_ref_log_price_q25, artwork_sim_k160_ref_log_price_q75, artwork_sim_k160_ref_log_price_iqr, artwork_sim_k160_ref_log_price_mean, artwork_sim_k160_ref_log_price_std, artwork_sim_k160_ref_area_price_median, artwork_sim_k160_ref_similarity_mean, artwork_sim_k160_ref_similarity_max, artwork_sim_k160_ref_similarity_min, user_gallery_tier_score, user_gallery_tier_available_flag, user_gallery_tier_missing_flag, user_gallery_tier_bucket, user_gallery_ref_type, user_gallery_audit_status, user_gallery_category`
- `similarity_only`: `width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket, artwork_sim_k160_ref_n, artwork_sim_k160_ref_log_price_median, artwork_sim_k160_ref_log_price_q25, artwork_sim_k160_ref_log_price_q75, artwork_sim_k160_ref_log_price_iqr, artwork_sim_k160_ref_log_price_mean, artwork_sim_k160_ref_log_price_std, artwork_sim_k160_ref_area_price_median, artwork_sim_k160_ref_similarity_mean, artwork_sim_k160_ref_similarity_max, artwork_sim_k160_ref_similarity_min`
- `similarity_gallery_context`: `width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket, artwork_sim_k160_ref_n, artwork_sim_k160_ref_log_price_median, artwork_sim_k160_ref_log_price_q25, artwork_sim_k160_ref_log_price_q75, artwork_sim_k160_ref_log_price_iqr, artwork_sim_k160_ref_log_price_mean, artwork_sim_k160_ref_log_price_std, artwork_sim_k160_ref_area_price_median, artwork_sim_k160_ref_similarity_mean, artwork_sim_k160_ref_similarity_max, artwork_sim_k160_ref_similarity_min, user_gallery_tier_score, user_gallery_tier_available_flag, user_gallery_tier_missing_flag, user_gallery_tier_bucket, user_gallery_ref_type, user_gallery_audit_status, user_gallery_category`
- `artwork_only`: `width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket`
- `artwork_gallery_context`: `width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket, user_gallery_tier_score, user_gallery_tier_available_flag, user_gallery_tier_missing_flag, user_gallery_tier_bucket, user_gallery_ref_type, user_gallery_audit_status, user_gallery_category`
- `full_current_meta`: `width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket, artist_meta_birth_year, artist_meta_total_works, artist_meta_followers, artist_meta_career_stage, artist_meta_total_works_log, artist_meta_followers_log, artist_meta_birth_year_missing, artist_meta_total_works_missing, artist_meta_followers_missing, artist_meta_career_stage_missing, artist_meta_is_p1_flag, artist_meta_has_international_flag, artist_meta_nationality, artist_meta_nationality_ko, artist_birth_period_bucket, artist_inventory_bucket, artist_followers_bucket, artist_career_stage_bucket, artist_meta_completeness_bucket, medium_birth_period_bucket, support_meta_completeness_bucket, career_size_bucket, artwork_sim_k160_ref_n, artwork_sim_k160_ref_log_price_median, artwork_sim_k160_ref_log_price_q25, artwork_sim_k160_ref_log_price_q75, artwork_sim_k160_ref_log_price_iqr, artwork_sim_k160_ref_log_price_mean, artwork_sim_k160_ref_log_price_std, artwork_sim_k160_ref_area_price_median, artwork_sim_k160_ref_similarity_mean, artwork_sim_k160_ref_similarity_max, artwork_sim_k160_ref_similarity_min`

## 6. 결론

- MdAPE 기준 최상위 후보는 `full_current_meta`이다.
- APE > 5 안정성 기준 최상위 후보는 `enterable_gallery_context`이다.
- 현재 Track4 갤러리 감사 기준의 validated coverage가 낮으므로, 이번 결과는 보수적으로 해석해야 한다.
- 팝업 선택형 UI로 갤러리 매핑 coverage가 올라가면 효과가 달라질 수 있어, 운영 사전 coverage 확장 후 같은 실험을 재실행해야 한다.