# Cold 사용자 입력 가능 작가 메타 피처 감사

- 작성일: 2026-06-18T15:57:26
- 목적: Cold 후보에서 운영 입력이 애매한 작가 메타를 제거해도 성능이 유지되는지 검증한다.
- 조건: `artist_key`, 같은 작가 가격 이력, `artist_key` lookup 후처리, `search_*`, 외부 live 검색 미사용.
- 구조: 유사작품 k160 + LightGBM Quantile q45 고정, 피처 세트만 변경.

## 1. Test 결과: MdAPE 기준
| candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | APE_gt_1 | APE_gt_2 | APE_gt_5 | APE_gt_10 | n_features | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_current_meta | test | 0.471031 | 0.999148 | 2.569218 | 0.880774 | 0.310745 | 0.532430 | 501 | 233 | 74 | 37 | 45 | 현재 k160 q45 전체 user_meta_core_bucket 피처 |
| no_followers | test | 0.486967 | 1.090848 | 2.544941 | 0.901743 | 0.321394 | 0.514359 | 550 | 242 | 73 | 38 | 41 | followers 계열 제거 |
| no_total_works | test | 0.487655 | 1.065456 | 2.489286 | 0.905415 | 0.318490 | 0.513391 | 561 | 252 | 68 | 43 | 41 | total works 계열 제거 |
| artwork_only | test | 0.490823 | 1.159634 | 3.677973 | 0.941292 | 0.300097 | 0.515973 | 543 | 241 | 137 | 51 | 12 | 작가 메타와 유사작품 통계를 모두 제거하고 작품 피처만 사용 |
| no_followers_total | test | 0.492291 | 1.077927 | 2.601124 | 0.910014 | 0.322685 | 0.506938 | 617 | 269 | 67 | 43 | 37 | followers + total works 제거 |
| similarity_only | test | 0.493210 | 1.116201 | 3.748102 | 0.932119 | 0.302678 | 0.506615 | 520 | 246 | 136 | 49 | 23 | 작품 피처 + 유사작품 k160 통계만 사용 |
| enterable_only | test | 0.496699 | 1.086514 | 2.452153 | 0.909771 | 0.322039 | 0.503066 | 578 | 232 | 66 | 43 | 33 | 운영 입력 가능성이 높은 메타만 사용 |
| no_optional_all | test | 0.496699 | 1.086514 | 2.452153 | 0.909771 | 0.322039 | 0.503066 | 578 | 232 | 66 | 43 | 33 | followers/total works/P1/international/completeness 제거 |

## 2. Test 결과: APE > 5 기준
| candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | APE_gt_1 | APE_gt_2 | APE_gt_5 | APE_gt_10 | n_features | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| enterable_only | test | 0.496699 | 1.086514 | 2.452153 | 0.909771 | 0.322039 | 0.503066 | 578 | 232 | 66 | 43 | 33 | 운영 입력 가능성이 높은 메타만 사용 |
| no_optional_all | test | 0.496699 | 1.086514 | 2.452153 | 0.909771 | 0.322039 | 0.503066 | 578 | 232 | 66 | 43 | 33 | followers/total works/P1/international/completeness 제거 |
| no_followers_total | test | 0.492291 | 1.077927 | 2.601124 | 0.910014 | 0.322685 | 0.506938 | 617 | 269 | 67 | 43 | 37 | followers + total works 제거 |
| no_total_works | test | 0.487655 | 1.065456 | 2.489286 | 0.905415 | 0.318490 | 0.513391 | 561 | 252 | 68 | 43 | 41 | total works 계열 제거 |
| no_followers | test | 0.486967 | 1.090848 | 2.544941 | 0.901743 | 0.321394 | 0.514359 | 550 | 242 | 73 | 38 | 41 | followers 계열 제거 |
| full_current_meta | test | 0.471031 | 0.999148 | 2.569218 | 0.880774 | 0.310745 | 0.532430 | 501 | 233 | 74 | 37 | 45 | 현재 k160 q45 전체 user_meta_core_bucket 피처 |
| similarity_only | test | 0.493210 | 1.116201 | 3.748102 | 0.932119 | 0.302678 | 0.506615 | 520 | 246 | 136 | 49 | 23 | 작품 피처 + 유사작품 k160 통계만 사용 |
| artwork_only | test | 0.490823 | 1.159634 | 3.677973 | 0.941292 | 0.300097 | 0.515973 | 543 | 241 | 137 | 51 | 12 | 작가 메타와 유사작품 통계를 모두 제거하고 작품 피처만 사용 |

## 3. 가격대별 진단
| candidate | split | segment | n | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| artwork_only | test | 1m_3m | 866 | 0.494830 | 0.883420 | 2.445674 | 0.718732 | 66 | 8 |
| enterable_only | test | 1m_3m | 866 | 0.509186 | 0.915907 | 2.500168 | 0.726037 | 75 | 8 |
| full_current_meta | test | 1m_3m | 866 | 0.482545 | 0.703997 | 2.010462 | 0.652357 | 45 | 6 |
| no_followers | test | 1m_3m | 866 | 0.517954 | 0.762865 | 2.225027 | 0.694681 | 57 | 6 |
| no_followers_total | test | 1m_3m | 866 | 0.480142 | 0.894416 | 2.624364 | 0.719584 | 78 | 8 |
| no_optional_all | test | 1m_3m | 866 | 0.509186 | 0.915907 | 2.500168 | 0.726037 | 75 | 8 |
| no_total_works | test | 1m_3m | 866 | 0.471915 | 0.831955 | 2.416503 | 0.688817 | 67 | 8 |
| similarity_only | test | 1m_3m | 866 | 0.479702 | 0.819370 | 2.291546 | 0.706104 | 62 | 10 |
| artwork_only | test | 3m_10m | 1057 | 0.435881 | 0.476031 | 1.014664 | 0.663038 | 10 | 3 |
| enterable_only | test | 3m_10m | 1057 | 0.429399 | 0.512366 | 1.222818 | 0.706357 | 15 | 2 |
| full_current_meta | test | 3m_10m | 1057 | 0.421007 | 0.463703 | 0.940966 | 0.653641 | 12 | 2 |
| no_followers | test | 3m_10m | 1057 | 0.435956 | 0.481779 | 1.062620 | 0.668808 | 12 | 2 |
| no_followers_total | test | 3m_10m | 1057 | 0.442560 | 0.524579 | 1.262738 | 0.706436 | 15 | 2 |
| no_optional_all | test | 3m_10m | 1057 | 0.429399 | 0.512366 | 1.222818 | 0.706357 | 15 | 2 |
| no_total_works | test | 3m_10m | 1057 | 0.428368 | 0.505656 | 1.211696 | 0.704569 | 14 | 3 |
| similarity_only | test | 3m_10m | 1057 | 0.434298 | 0.493292 | 1.073611 | 0.679429 | 19 | 4 |
| artwork_only | test | gt_10m | 636 | 0.515748 | 0.500802 | 0.915004 | 1.144631 | 0 | 0 |
| enterable_only | test | gt_10m | 636 | 0.459469 | 0.478404 | 0.898497 | 1.100473 | 0 | 0 |
| full_current_meta | test | gt_10m | 636 | 0.483473 | 0.486703 | 0.899568 | 1.106711 | 0 | 0 |
| no_followers | test | gt_10m | 636 | 0.470615 | 0.479358 | 0.895960 | 1.102339 | 0 | 0 |
| no_followers_total | test | gt_10m | 636 | 0.467371 | 0.481329 | 0.898204 | 1.102551 | 0 | 0 |
| no_optional_all | test | gt_10m | 636 | 0.459469 | 0.478404 | 0.898497 | 1.100473 | 0 | 0 |
| no_total_works | test | gt_10m | 636 | 0.479206 | 0.491045 | 0.895222 | 1.112273 | 0 | 0 |
| similarity_only | test | gt_10m | 636 | 0.513947 | 0.489653 | 0.905136 | 1.124066 | 0 | 0 |
| artwork_only | test | lt_1m | 540 | 0.968759 | 3.716647 | 24.430386 | 1.361169 | 165 | 126 |
| enterable_only | test | lt_1m | 540 | 0.880594 | 3.200176 | 24.822371 | 1.225420 | 142 | 56 |
| full_current_meta | test | lt_1m | 540 | 0.815276 | 3.124113 | 26.272536 | 1.220932 | 176 | 66 |
| no_followers | test | lt_1m | 540 | 0.956788 | 3.529233 | 31.578214 | 1.259314 | 173 | 65 |
| no_followers_total | test | lt_1m | 540 | 1.028789 | 3.158010 | 23.098506 | 1.230263 | 176 | 57 |
| no_optional_all | test | lt_1m | 540 | 0.880594 | 3.200176 | 24.822371 | 1.225420 | 142 | 56 |
| no_total_works | test | lt_1m | 540 | 0.922575 | 3.212205 | 25.972222 | 1.230820 | 171 | 57 |
| similarity_only | test | lt_1m | 540 | 0.871953 | 3.549452 | 23.458016 | 1.339736 | 165 | 122 |

## 4. 피처 세트 정의

- `full_current_meta`: `width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket, artist_meta_birth_year, artist_meta_total_works, artist_meta_followers, artist_meta_career_stage, artist_meta_total_works_log, artist_meta_followers_log, artist_meta_birth_year_missing, artist_meta_total_works_missing, artist_meta_followers_missing, artist_meta_career_stage_missing, artist_meta_is_p1_flag, artist_meta_has_international_flag, artist_meta_nationality, artist_meta_nationality_ko, artist_birth_period_bucket, artist_inventory_bucket, artist_followers_bucket, artist_career_stage_bucket, artist_meta_completeness_bucket, medium_birth_period_bucket, support_meta_completeness_bucket, career_size_bucket, artwork_sim_k160_ref_n, artwork_sim_k160_ref_log_price_median, artwork_sim_k160_ref_log_price_q25, artwork_sim_k160_ref_log_price_q75, artwork_sim_k160_ref_log_price_iqr, artwork_sim_k160_ref_log_price_mean, artwork_sim_k160_ref_log_price_std, artwork_sim_k160_ref_area_price_median, artwork_sim_k160_ref_similarity_mean, artwork_sim_k160_ref_similarity_max, artwork_sim_k160_ref_similarity_min`
- `enterable_only`: `width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket, artist_meta_birth_year, artist_meta_career_stage, artist_meta_birth_year_missing, artist_meta_career_stage_missing, artist_meta_nationality, artist_meta_nationality_ko, artist_birth_period_bucket, artist_career_stage_bucket, medium_birth_period_bucket, career_size_bucket, artwork_sim_k160_ref_n, artwork_sim_k160_ref_log_price_median, artwork_sim_k160_ref_log_price_q25, artwork_sim_k160_ref_log_price_q75, artwork_sim_k160_ref_log_price_iqr, artwork_sim_k160_ref_log_price_mean, artwork_sim_k160_ref_log_price_std, artwork_sim_k160_ref_area_price_median, artwork_sim_k160_ref_similarity_mean, artwork_sim_k160_ref_similarity_max, artwork_sim_k160_ref_similarity_min`
- `similarity_only`: `width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket, artwork_sim_k160_ref_n, artwork_sim_k160_ref_log_price_median, artwork_sim_k160_ref_log_price_q25, artwork_sim_k160_ref_log_price_q75, artwork_sim_k160_ref_log_price_iqr, artwork_sim_k160_ref_log_price_mean, artwork_sim_k160_ref_log_price_std, artwork_sim_k160_ref_area_price_median, artwork_sim_k160_ref_similarity_mean, artwork_sim_k160_ref_similarity_max, artwork_sim_k160_ref_similarity_min`
- `artwork_only`: `width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket`

## 5. 결론

- MdAPE 기준 최상위 후보는 `full_current_meta`이다.
- APE > 5 안정성 기준 최상위 후보는 `enterable_only`이다.
- `artwork_only`는 작가 메타를 아예 쓰지 않는 하한선 비교다. 중앙 오차는 크게 무너지지 않지만, APE > 5가 크게 늘어 저가/불확실 구간 방어에는 부족하다.
- `similarity_only`는 작가 메타 없이 유사작품 통계만 추가한 비교다. 이 실험에서는 유사작품 통계만으로는 tail 안정성이 개선되지 않았다.
- `enterable_only`는 사용자가 비교적 입력하기 쉬운 작가 메타만 남긴 후보이며, full 메타 대비 중앙 오차는 손해가 있지만 p95와 APE > 5가 가장 안정적이다.
- 입력하기 애매한 피처를 제거했을 때의 손실과 tail 변화를 기준으로 기본 학습 피처를 정한다.