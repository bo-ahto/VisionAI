# PP-FPOL2 Warm 작가+작품 Huber residual 보정 실험

- 작성일: 2026-06-08 15:22
- 기준 후보: `blend_svcnum_ppv8_wsvc_0.70`
- 정책 grid: `experiments/track6/PP-FPOL1_warm_artist_artwork_feature_correction_policy/outputs/candidate_correction_grid.csv`
- validation: 작가 키 기준 5-fold OOF
- test: validation 전체 학습 후 고정 test 1회 적용
- 후보 수: 22

## 1. 기준 성능

| split | RMSE_log | MdAPE | MAPE | p95_APE | Within_30 | Within_50 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| validation | 0.3292 | 0.1305 | 0.2110 | 0.6580 | 0.7746 | 0.9075 |
| test | 0.3996 | 0.1405 | 0.2748 | 0.8331 | 0.7628 | 0.8781 |

## 2. 피처 세트별 test 최선

| feature_set | best_test_policy | best_test_delta_MdAPE | best_test_delta_MAPE | best_test_delta_p95_APE | best_test_candidate |
| --- | --- | --- | --- | --- | --- |
| artist_core | hard_clip | -0.0019 | -0.0002 | -0.0173 | huber_artist_core_hard_clip_small_global_eps1p05_cap0p03_s0p5 |
| artist_artwork_core_year_guard | soft_tanh_cap | -0.0004 | -0.0002 | 0.0005 | huber_artist_artwork_core_year_guard_soft_tanh_cap_medium_soft_eps1p35_cap0p06_s0p35 |
| artist_artwork_core | hard_clip | 0.0003 | 0.0001 | -0.0004 | huber_artist_artwork_core_hard_clip_medium_global_eps1p35_cap0p06_s0p25 |
| artwork_size_material_support | hard_clip | -0.0001 | 0.0003 | -0.0023 | huber_artwork_size_material_support_hard_clip_medium_global_eps1p35_cap0p06_s0p25 |
| artwork_size_shape | pred_bin_tail_guard | -0.0007 | 0.0008 | -0.0005 | huber_artwork_size_shape_pred_bin_tail_guard_mid_open_tail_guard_eps1p35_cap0p06_s0p35 |
| artist_core_activity_light | hard_clip | 0.0005 | 0.0008 | -0.0076 | huber_artist_core_activity_light_hard_clip_small_global_eps1p05_cap0p03_s0p5 |

## 3. test 3지표 모두 개선 후보

| candidate | feature_set | correction_policy | correction_cap | correction_strength | validation_delta_MdAPE | validation_delta_MAPE | validation_delta_p95_APE | test_MdAPE | test_MAPE | test_p95_APE | test_delta_MdAPE | test_delta_MAPE | test_delta_p95_APE | test_mean_abs_correction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| huber_artist_core_hard_clip_small_global_eps1p05_cap0p03_s0p5 | artist_core | hard_clip | 0.0300 | 0.5000 | -0.0038 | -0.0013 | -0.0094 | 0.1386 | 0.2746 | 0.8158 | -0.0019 | -0.0002 | -0.0173 | 0.0069 |
| huber_artist_artwork_core_year_guard_hard_clip_small_global_eps1p35_cap0p03_s0p5 | artist_artwork_core_year_guard | hard_clip | 0.0300 | 0.5000 | -0.0018 | -0.0003 | -0.0104 | 0.1404 | 0.2748 | 0.8327 | -0.0001 | -0.0000 | -0.0004 | 0.0126 |

## 4. validation 기준 상위 후보

| candidate | feature_set | correction_policy | correction_cap | correction_strength | validation_delta_MdAPE | validation_delta_MAPE | validation_delta_p95_APE | test_MdAPE | test_MAPE | test_p95_APE | test_delta_MdAPE | test_delta_MAPE | test_delta_p95_APE | test_mean_abs_correction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| huber_artist_core_hard_clip_small_global_eps1p05_cap0p03_s0p5 | artist_core | hard_clip | 0.0300 | 0.5000 | -0.0038 | -0.0013 | -0.0094 | 0.1386 | 0.2746 | 0.8158 | -0.0019 | -0.0002 | -0.0173 | 0.0069 |
| huber_artist_artwork_core_year_guard_pred_bin_tail_guard_wide_low_strength_eps1p35_cap0p08_s0p25 | artist_artwork_core_year_guard | pred_bin_tail_guard | 0.0800 | 0.2500 | -0.0031 | -0.0005 | -0.0113 | 0.1410 | 0.2746 | 0.8344 | 0.0005 | -0.0002 | 0.0014 | 0.0114 |
| huber_artist_core_activity_light_hard_clip_small_global_eps1p05_cap0p03_s0p5 | artist_core_activity_light | hard_clip | 0.0300 | 0.5000 | -0.0025 | -0.0011 | -0.0086 | 0.1410 | 0.2756 | 0.8255 | 0.0005 | 0.0008 | -0.0076 | 0.0094 |
| huber_artist_artwork_core_year_guard_hard_clip_medium_global_eps1p35_cap0p06_s0p25 | artist_artwork_core_year_guard | hard_clip | 0.0600 | 0.2500 | -0.0023 | -0.0005 | -0.0093 | 0.1410 | 0.2747 | 0.8339 | 0.0005 | -0.0001 | 0.0008 | 0.0106 |
| huber_artist_artwork_core_year_guard_pred_bin_tail_guard_mid_open_tail_guard_eps1p35_cap0p06_s0p35 | artist_artwork_core_year_guard | pred_bin_tail_guard | 0.0600 | 0.3500 | -0.0017 | -0.0004 | -0.0122 | 0.1418 | 0.2747 | 0.8338 | 0.0013 | -0.0001 | 0.0008 | 0.0132 |
| huber_artist_artwork_core_year_guard_hard_clip_small_global_eps1p35_cap0p03_s0p5 | artist_artwork_core_year_guard | hard_clip | 0.0300 | 0.5000 | -0.0018 | -0.0003 | -0.0104 | 0.1404 | 0.2748 | 0.8327 | -0.0001 | -0.0000 | -0.0004 | 0.0126 |
| huber_artist_artwork_core_year_guard_soft_tanh_cap_medium_soft_eps1p35_cap0p06_s0p35 | artist_artwork_core_year_guard | soft_tanh_cap | 0.0600 | 0.3500 | -0.0012 | -0.0006 | -0.0122 | 0.1401 | 0.2746 | 0.8336 | -0.0004 | -0.0002 | 0.0005 | 0.0137 |
| huber_artist_artwork_core_hard_clip_small_global_eps1p35_cap0p03_s0p5 | artist_artwork_core | hard_clip | 0.0300 | 0.5000 | -0.0018 | -0.0005 | -0.0094 | 0.1417 | 0.2753 | 0.8327 | 0.0012 | 0.0005 | -0.0004 | 0.0122 |
| huber_artist_artwork_core_pred_bin_tail_guard_wide_low_strength_eps1p35_cap0p08_s0p25 | artist_artwork_core | pred_bin_tail_guard | 0.0800 | 0.2500 | -0.0025 | -0.0007 | -0.0048 | 0.1412 | 0.2749 | 0.8332 | 0.0007 | 0.0001 | 0.0002 | 0.0107 |
| huber_artist_artwork_core_pred_bin_tail_guard_mid_open_tail_guard_eps1p35_cap0p06_s0p35 | artist_artwork_core | pred_bin_tail_guard | 0.0600 | 0.3500 | -0.0014 | -0.0005 | -0.0082 | 0.1418 | 0.2752 | 0.8334 | 0.0013 | 0.0004 | 0.0003 | 0.0125 |
| huber_artwork_size_shape_hard_clip_small_global_eps1p35_cap0p03_s0p5 | artwork_size_shape | hard_clip | 0.0300 | 0.5000 | -0.0034 | 0.0010 | 0.0004 | 0.1404 | 0.2757 | 0.8320 | -0.0001 | 0.0009 | -0.0011 | 0.0080 |
| huber_artist_artwork_core_soft_tanh_cap_medium_soft_eps1p35_cap0p06_s0p35 | artist_artwork_core | soft_tanh_cap | 0.0600 | 0.3500 | 0.0002 | -0.0007 | -0.0077 | 0.1409 | 0.2749 | 0.8335 | 0.0005 | 0.0001 | 0.0004 | 0.0129 |
| huber_artist_artwork_core_hard_clip_medium_global_eps1p35_cap0p06_s0p25 | artist_artwork_core | hard_clip | 0.0600 | 0.2500 | -0.0001 | -0.0006 | -0.0048 | 0.1407 | 0.2749 | 0.8327 | 0.0003 | 0.0001 | -0.0004 | 0.0100 |
| huber_artwork_size_shape_pred_bin_tail_guard_mid_open_tail_guard_eps1p35_cap0p06_s0p35 | artwork_size_shape | pred_bin_tail_guard | 0.0600 | 0.3500 | -0.0023 | 0.0010 | 0.0015 | 0.1398 | 0.2756 | 0.8326 | -0.0007 | 0.0008 | -0.0005 | 0.0065 |
| huber_artwork_size_shape_soft_tanh_cap_medium_soft_eps1p35_cap0p06_s0p35 | artwork_size_shape | soft_tanh_cap | 0.0600 | 0.3500 | -0.0022 | 0.0011 | 0.0015 | 0.1401 | 0.2757 | 0.8326 | -0.0004 | 0.0009 | -0.0004 | 0.0064 |

## 5. test 기준 상위 후보

| candidate | feature_set | correction_policy | correction_cap | correction_strength | validation_delta_MdAPE | validation_delta_MAPE | validation_delta_p95_APE | test_MdAPE | test_MAPE | test_p95_APE | test_delta_MdAPE | test_delta_MAPE | test_delta_p95_APE | test_mean_abs_correction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| huber_artist_core_hard_clip_small_global_eps1p05_cap0p03_s0p5 | artist_core | hard_clip | 0.0300 | 0.5000 | -0.0038 | -0.0013 | -0.0094 | 0.1386 | 0.2746 | 0.8158 | -0.0019 | -0.0002 | -0.0173 | 0.0069 |
| huber_artist_artwork_core_year_guard_soft_tanh_cap_medium_soft_eps1p35_cap0p06_s0p35 | artist_artwork_core_year_guard | soft_tanh_cap | 0.0600 | 0.3500 | -0.0012 | -0.0006 | -0.0122 | 0.1401 | 0.2746 | 0.8336 | -0.0004 | -0.0002 | 0.0005 | 0.0137 |
| huber_artwork_size_material_support_hard_clip_medium_global_eps1p35_cap0p06_s0p25 | artwork_size_material_support | hard_clip | 0.0600 | 0.2500 | 0.0006 | 0.0021 | 0.0077 | 0.1404 | 0.2751 | 0.8307 | -0.0001 | 0.0003 | -0.0023 | 0.0088 |
| huber_artist_core_activity_light_hard_clip_small_global_eps1p05_cap0p03_s0p5 | artist_core_activity_light | hard_clip | 0.0300 | 0.5000 | -0.0025 | -0.0011 | -0.0086 | 0.1410 | 0.2756 | 0.8255 | 0.0005 | 0.0008 | -0.0076 | 0.0094 |
| huber_artist_artwork_core_year_guard_hard_clip_small_global_eps1p35_cap0p03_s0p5 | artist_artwork_core_year_guard | hard_clip | 0.0300 | 0.5000 | -0.0018 | -0.0003 | -0.0104 | 0.1404 | 0.2748 | 0.8327 | -0.0001 | -0.0000 | -0.0004 | 0.0126 |
| huber_artwork_size_shape_pred_bin_tail_guard_mid_open_tail_guard_eps1p35_cap0p06_s0p35 | artwork_size_shape | pred_bin_tail_guard | 0.0600 | 0.3500 | -0.0023 | 0.0010 | 0.0015 | 0.1398 | 0.2756 | 0.8326 | -0.0007 | 0.0008 | -0.0005 | 0.0065 |
| huber_artwork_size_material_support_hard_clip_small_global_eps1p35_cap0p03_s0p5 | artwork_size_material_support | hard_clip | 0.0300 | 0.5000 | -0.0003 | 0.0026 | 0.0104 | 0.1404 | 0.2757 | 0.8299 | -0.0001 | 0.0009 | -0.0032 | 0.0116 |
| huber_artist_artwork_core_hard_clip_medium_global_eps1p35_cap0p06_s0p25 | artist_artwork_core | hard_clip | 0.0600 | 0.2500 | -0.0001 | -0.0006 | -0.0048 | 0.1407 | 0.2749 | 0.8327 | 0.0003 | 0.0001 | -0.0004 | 0.0100 |
| huber_artwork_size_shape_soft_tanh_cap_medium_soft_eps1p35_cap0p06_s0p35 | artwork_size_shape | soft_tanh_cap | 0.0600 | 0.3500 | -0.0022 | 0.0011 | 0.0015 | 0.1401 | 0.2757 | 0.8326 | -0.0004 | 0.0009 | -0.0004 | 0.0064 |
| huber_artist_artwork_core_year_guard_hard_clip_medium_global_eps1p35_cap0p06_s0p25 | artist_artwork_core_year_guard | hard_clip | 0.0600 | 0.2500 | -0.0023 | -0.0005 | -0.0093 | 0.1410 | 0.2747 | 0.8339 | 0.0005 | -0.0001 | 0.0008 | 0.0106 |
| huber_artwork_size_material_support_soft_tanh_cap_medium_soft_eps1p35_cap0p06_s0p35 | artwork_size_material_support | soft_tanh_cap | 0.0600 | 0.3500 | 0.0005 | 0.0029 | 0.0088 | 0.1413 | 0.2752 | 0.8298 | 0.0008 | 0.0004 | -0.0033 | 0.0112 |
| huber_artist_artwork_core_year_guard_pred_bin_tail_guard_wide_low_strength_eps1p35_cap0p08_s0p25 | artist_artwork_core_year_guard | pred_bin_tail_guard | 0.0800 | 0.2500 | -0.0031 | -0.0005 | -0.0113 | 0.1410 | 0.2746 | 0.8344 | 0.0005 | -0.0002 | 0.0014 | 0.0114 |
| huber_artwork_size_shape_hard_clip_small_global_eps1p35_cap0p03_s0p5 | artwork_size_shape | hard_clip | 0.0300 | 0.5000 | -0.0034 | 0.0010 | 0.0004 | 0.1404 | 0.2757 | 0.8320 | -0.0001 | 0.0009 | -0.0011 | 0.0080 |
| huber_artist_artwork_core_soft_tanh_cap_medium_soft_eps1p35_cap0p06_s0p35 | artist_artwork_core | soft_tanh_cap | 0.0600 | 0.3500 | 0.0002 | -0.0007 | -0.0077 | 0.1409 | 0.2749 | 0.8335 | 0.0005 | 0.0001 | 0.0004 | 0.0129 |
| huber_artwork_size_shape_hard_clip_medium_global_eps1p35_cap0p06_s0p25 | artwork_size_shape | hard_clip | 0.0600 | 0.2500 | -0.0005 | 0.0008 | 0.0021 | 0.1407 | 0.2754 | 0.8330 | 0.0002 | 0.0006 | -0.0001 | 0.0049 |

## 6. bootstrap 안정성

| sample_type | candidate | mean_delta_MdAPE | improvement_probability_MdAPE | mean_delta_MAPE | improvement_probability_MAPE | mean_delta_p95_APE | improvement_probability_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| artist_bootstrap | huber_artist_artwork_core_year_guard_soft_tanh_cap_medium_soft_eps1p35_cap0p06_s0p35 | -0.0010 | 0.5950 | -0.0002 | 0.6325 | -0.0072 | 0.7200 |
| artist_bootstrap | huber_artist_artwork_core_year_guard_pred_bin_tail_guard_wide_low_strength_eps1p35_cap0p08_s0p25 | -0.0010 | 0.5875 | -0.0002 | 0.6350 | -0.0052 | 0.7025 |
| artist_bootstrap | huber_artist_artwork_core_year_guard_hard_clip_medium_global_eps1p35_cap0p06_s0p25 | -0.0009 | 0.5850 | -0.0002 | 0.6525 | -0.0057 | 0.7100 |
| artist_bootstrap | huber_artist_core_hard_clip_small_global_eps1p05_cap0p03_s0p5 | 0.0002 | 0.4925 | -0.0002 | 0.6200 | -0.0028 | 0.7425 |
| artist_bootstrap | huber_artist_artwork_core_year_guard_pred_bin_tail_guard_mid_open_tail_guard_eps1p35_cap0p06_s0p35 | -0.0006 | 0.5350 | -0.0001 | 0.5850 | -0.0062 | 0.7125 |
| artist_bootstrap | huber_artist_artwork_core_year_guard_hard_clip_small_global_eps1p35_cap0p03_s0p5 | -0.0005 | 0.5525 | -0.0001 | 0.5650 | -0.0076 | 0.7375 |
| artist_bootstrap | huber_artwork_size_material_support_hard_clip_medium_global_eps1p35_cap0p06_s0p25 | -0.0001 | 0.4625 | 0.0003 | 0.3450 | -0.0002 | 0.5625 |
| artist_bootstrap | huber_artwork_size_material_support_soft_tanh_cap_medium_soft_eps1p35_cap0p06_s0p35 | 0.0002 | 0.4475 | 0.0004 | 0.3575 | 0.0000 | 0.5525 |
| artist_bootstrap | huber_artwork_size_material_support_pred_bin_tail_guard_mid_open_tail_guard_eps1p35_cap0p06_s0p35 | 0.0004 | 0.4475 | 0.0005 | 0.2825 | 0.0003 | 0.5525 |
| artist_bootstrap | huber_artwork_size_material_support_hard_clip_small_global_eps1p35_cap0p03_s0p5 | 0.0011 | 0.3950 | 0.0009 | 0.1375 | -0.0003 | 0.5550 |
| artist_bootstrap | huber_artist_core_activity_light_hard_clip_small_global_eps1p05_cap0p03_s0p5 | 0.0019 | 0.2450 | 0.0009 | 0.0975 | 0.0011 | 0.4150 |
| row_bootstrap | huber_artist_core_hard_clip_small_global_eps1p05_cap0p03_s0p5 | 0.0000 | 0.5425 | -0.0002 | 0.6400 | -0.0027 | 0.7200 |
| row_bootstrap | huber_artist_artwork_core_year_guard_pred_bin_tail_guard_wide_low_strength_eps1p35_cap0p08_s0p25 | -0.0010 | 0.6075 | -0.0001 | 0.6075 | -0.0038 | 0.6625 |
| row_bootstrap | huber_artist_artwork_core_year_guard_soft_tanh_cap_medium_soft_eps1p35_cap0p06_s0p35 | -0.0012 | 0.5900 | -0.0001 | 0.5925 | -0.0058 | 0.6750 |
| row_bootstrap | huber_artist_artwork_core_year_guard_hard_clip_medium_global_eps1p35_cap0p06_s0p25 | -0.0010 | 0.6225 | -0.0001 | 0.6025 | -0.0044 | 0.6725 |
| row_bootstrap | huber_artist_artwork_core_year_guard_pred_bin_tail_guard_mid_open_tail_guard_eps1p35_cap0p06_s0p35 | -0.0005 | 0.5225 | 0.0000 | 0.5700 | -0.0048 | 0.6825 |
| row_bootstrap | huber_artist_artwork_core_year_guard_hard_clip_small_global_eps1p35_cap0p03_s0p5 | -0.0005 | 0.5500 | 0.0000 | 0.5150 | -0.0066 | 0.7525 |
| row_bootstrap | huber_artwork_size_material_support_hard_clip_medium_global_eps1p35_cap0p06_s0p25 | -0.0004 | 0.5000 | 0.0004 | 0.2425 | -0.0009 | 0.5725 |
| row_bootstrap | huber_artwork_size_material_support_soft_tanh_cap_medium_soft_eps1p35_cap0p06_s0p35 | -0.0002 | 0.4650 | 0.0004 | 0.2575 | -0.0011 | 0.5775 |
| row_bootstrap | huber_artwork_size_material_support_pred_bin_tail_guard_mid_open_tail_guard_eps1p35_cap0p06_s0p35 | 0.0002 | 0.4725 | 0.0006 | 0.1825 | -0.0010 | 0.5675 |
| row_bootstrap | huber_artist_core_activity_light_hard_clip_small_global_eps1p05_cap0p03_s0p5 | 0.0018 | 0.2500 | 0.0009 | 0.0550 | 0.0015 | 0.3875 |
| row_bootstrap | huber_artwork_size_material_support_hard_clip_small_global_eps1p35_cap0p03_s0p5 | 0.0007 | 0.4200 | 0.0009 | 0.0575 | -0.0015 | 0.5625 |

## 7. 산출물

- `outputs/candidate_metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_set_summary.csv`
- `outputs/bootstrap_summary.csv`
- `outputs/bootstrap_samples.csv`
- `outputs/coefficients_top.csv`
- `outputs/experiment_manifest.json`