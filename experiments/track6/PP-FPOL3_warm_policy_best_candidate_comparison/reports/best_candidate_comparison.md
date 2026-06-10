# PP-FPOL3 Warm 최상위 후보 비교

- 작성일: 2026-06-08 15:30
- 비교 대상: PP-FPOL2, PP-AMW10, PP-AMW8, PP-WHUBER7, PP-WCOEF
- 기준 test: 607건 Warm 고정 test
- 기준 후보: `blend_svcnum_ppv8_wsvc_0.70`

## 1. 목적별 최상위 후보

| objective | source | candidate | feature_set | test_MdAPE | test_MAPE | test_p95_APE | test_delta_MdAPE | test_delta_MAPE | test_delta_p95_APE | test_balanced_delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MdAPE 최저 | PP-WHUBER7 | PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p001_predbin_mid_open_tail_guard_cap0p06_s0p35 | pred_size_material_svc_artist | 0.1328 | 0.2743 | 0.8447 | -0.0077 | -0.0005 | 0.0116 | -0.0058 |
| MAPE 최저 | PP-WHUBER7 | PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08 | pred_size_material_svc_artist | 0.1368 | 0.2729 | 0.8152 | -0.0037 | -0.0019 | -0.0179 | -0.0092 |
| p95 최저 | PP-WHUBER7 | PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08 | pred_size_svc | 0.1396 | 0.2733 | 0.8016 | -0.0009 | -0.0015 | -0.0314 | -0.0087 |
| 세 지표 균형 최저 | PP-WHUBER7 | PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_predbin_mid_open_tail_guard_cap0p06_s0p35 | pred_size_svc | 0.1361 | 0.2740 | 0.8062 | -0.0044 | -0.0008 | -0.0269 | -0.0105 |
| 세 지표 모두 개선 중 균형 최저 | PP-WHUBER7 | PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_predbin_mid_open_tail_guard_cap0p06_s0p35 | pred_size_svc | 0.1361 | 0.2740 | 0.8062 | -0.0044 | -0.0008 | -0.0269 | -0.0105 |
| 이번 정책 실험 최선 | PP-FPOL2 | huber_artist_core_hard_clip_small_global_eps1p05_cap0p03_s0p5 | artist_core | 0.1386 | 0.2746 | 0.8158 | -0.0019 | -0.0002 | -0.0173 | -0.0055 |

## 2. 주요 후보 직접 비교

| source | candidate | feature_set | test_MdAPE | test_MAPE | test_p95_APE | test_delta_MdAPE | test_delta_MAPE | test_delta_p95_APE | test_balanced_delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-WHUBER7 | PP-WHUBER7_pred_size_svc_eps1.05_alpha0p01_dir_under_guard_cap0p08 | pred_size_svc | 0.1396 | 0.2733 | 0.8018 | -0.0009 | -0.0015 | -0.0312 | -0.0087 |
| PP-WHUBER7 | PP-WHUBER7_pred_size_material_svc_artist_eps1.35_alpha0p01_predbin_mid_open_tail_guard_cap0p08_s0p25 | pred_size_material_svc_artist | 0.1334 | 0.2745 | 0.8288 | -0.0071 | -0.0003 | -0.0043 | -0.0082 |
| PP-WCOEF | PP-WCOEF5_resid_pred_size_svc_alpha0p001_cap0p08_s0p25 | current_pred_log, ppv8_pred_log, fallback_pred_log, current_ppv8_gap_abs, current_fallback_gap_abs, pred_log_bin, width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, medium_support_bucket, is_extreme_aspect_ratio, size_bin, log_area_x_size_small, log_area_x_size_mid_low, log_area_x_size_mid_high, log_area_x_size_large, aspect_ratio_x_size_small, aspect_ratio_x_size_mid_low, aspect_ratio_x_size_mid_high, aspect_ratio_x_size_large, svc_group_log_price_median, svc_group_log_price_q25, svc_group_log_price_q75, svc_group_log_price_iqr, svc_group_log_unit_area_median, svc_group_log_unit_area_iqr, svc_group_n_log, svc_group_level, svc_coverage_tier, svc_reliability_bin, svc_price_x_rel_high, svc_price_x_rel_mid, svc_price_x_rel_low, svc_unit_area_x_rel_high, svc_unit_area_x_rel_mid, svc_unit_area_x_rel_low, svc_n_log_x_rel_high, svc_iqr_x_rel_low, svc_missing_flag | 0.1395 | 0.2741 | 0.8073 | -0.0009 | -0.0007 | -0.0258 | -0.0068 |
| PP-AMW10 | huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5 | birth_generation | 0.1386 | 0.2742 | 0.8129 | -0.0019 | -0.0006 | -0.0202 | -0.0066 |
| PP-WHUBER7 | PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p001_predbin_mid_open_tail_guard_cap0p06_s0p35 | pred_size_material_svc_artist | 0.1328 | 0.2743 | 0.8447 | -0.0077 | -0.0005 | 0.0116 | -0.0058 |
| PP-WCOEF | PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p01_cap0p08_s0p25 | current_pred_log, ppv8_pred_log, fallback_pred_log, current_ppv8_gap_abs, current_fallback_gap_abs, pred_log_bin, width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, medium_support_bucket, is_extreme_aspect_ratio, size_bin, medium_size_bin, support_size_bin, medium_support_size_bin, svc_group_log_price_median, svc_group_log_price_q25, svc_group_log_price_q75, svc_group_log_price_iqr, svc_group_log_unit_area_median, svc_group_log_unit_area_iqr, svc_group_n_log, svc_group_level, svc_coverage_tier, svc_reliability_bin, svc_price_x_rel_high, svc_price_x_rel_mid, svc_price_x_rel_low, svc_unit_area_x_rel_high, svc_unit_area_x_rel_mid, svc_unit_area_x_rel_low, svc_n_log_x_rel_high, svc_iqr_x_rel_low, svc_missing_flag, artist_prior_log_price_k5, artist_prior_log_price_k15, artist_prior_log_price_k30, artist_prior_log_unit_area_k15, artist_prior_n_log, artist_prior_iqr, artist_works_log, artist_works_count_train, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_for_sale_ratio, artist_meta_career_age, artist_meta_birth_year, artist_meta_source, artist_meta_nationality, artist_meta_nationality_ko, artist_meta_career_stage, artist_meta_is_p1, artist_meta_has_international, artist_works_bin, artist_meta_total_works_bin, artist_prior_price_x_works_low, artist_prior_price_x_works_mid, artist_prior_price_x_works_high, artist_prior_unit_area_x_works_high | 0.1353 | 0.2751 | 0.8291 | -0.0052 | 0.0003 | -0.0040 | -0.0057 |
| PP-FPOL2 | huber_artist_core_hard_clip_small_global_eps1p05_cap0p03_s0p5 | artist_core | 0.1386 | 0.2746 | 0.8158 | -0.0019 | -0.0002 | -0.0173 | -0.0055 |
| REFERENCE | blend_svcnum_ppv8_wsvc_0.70 | base_warm_blend | 0.1405 | 0.2748 | 0.8331 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## 3. 판단

- MdAPE만 최우선이면 PP-WHUBER7의 `pred_size_material_svc_artist` 후보가 가장 낮다. 다만 일부 후보는 p95가 악화된다.
- MAPE와 p95까지 같이 보면 PP-WHUBER7의 `pred_size_svc ... dir_under_guard_cap0p08` 후보가 가장 강하다.
- PP-FPOL2 최선 후보는 기존 안정 후보인 작가 생년+세대 계열과 거의 같은 방향이며, 전체 최상위는 아니다.
- 작품 피처 전체 통합 보정은 PP-WHUBER7의 SVC/가격대 guard 방식으로 쓸 때 더 강했고, PP-FPOL2처럼 일반 작가+작품 피처를 한 번에 넣으면 개선 폭이 줄었다.