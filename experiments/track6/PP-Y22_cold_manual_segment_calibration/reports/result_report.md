# PP-Y22 Cold 수동 구간 보정 실험

## 1. 목적

- 자동 분위수 구간 보정 대신 사람이 해석 가능한 수동 구간 보정이 Cold 성능을 더 안정적으로 개선하는지 확인
- 구간 기준을 validation 분포가 아니라 운영 설명이 가능한 가격대/불확실성 배수/검색 품질/외부 정보 상태로 고정
- validation 내부 OOF로 보정 정책을 선택하고 test에는 선택된 보정 정책을 1회 적용

## 2. 실험 기준

- 1차 예측값: `lgbq_search_all_external_interaction`
- 기준 모델: Cold LightGBM Quantile + 검색/전시/갤러리 상호작용 피처
- 보정식: `corrected_pred_log = pred_log + clip(segment_median_residual, -cap, cap) * strength`
- residual 정의: `actual_log - pred_log`
- 수동 구간:
  - 예측 가격대: 50만원 미만, 50만-100만원, 100만-300만원, 300만-1000만원, 1000만-3000만원, 3000만-1억원, 1억원 이상
  - 예측 불확실성 배수: 1.5배 이하, 1.5-2.5배, 2.5-4배, 4-7배, 7배 초과
  - 검색 품질: 검색 양호, 검색 낮음, 검색 없음
  - 외부 정보: 갤러리/전시 정보 충분, 일부, 부족

## 3. 기존 자동 구간 후보 참고

| candidate | split | policy | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| stability_lgbq_search_all_external_interaction_external_x_qwidth_oof_min30_cap0.25 | test | y16_candidate_stability | 0.4239 | 1.0003 | 3.3553 | 0.8557 | 0.3411 | 0.5799 |
| stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min30_cap0.25 | test | y16_candidate_stability | 0.4247 | 0.9910 | 3.3053 | 0.8575 | 0.3462 | 0.5779 |
| component_pp_y2_baseline | test | stability_component | 0.4421 | 1.0484 | 3.3537 | 0.8567 | 0.3249 | 0.5602 |
| stability_lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.35 | test | y16_candidate_stability | 0.4438 | 1.1083 | 2.8025 | 0.8905 | 0.3504 | 0.5624 |
| stability_lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.35 | validation | y16_candidate_stability | 0.3501 | 0.5358 | 1.4493 | 0.6266 | 0.4341 | 0.6727 |
| stability_lgbq_search_all_external_interaction_external_x_qwidth_oof_min30_cap0.25 | validation | y16_candidate_stability | 0.3648 | 0.5548 | 1.4282 | 0.6383 | 0.4057 | 0.6346 |
| stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min30_cap0.25 | validation | y16_candidate_stability | 0.3656 | 0.5460 | 1.4000 | 0.6388 | 0.3977 | 0.6469 |
| component_pp_y2_baseline | validation | stability_component | 0.4129 | 0.5887 | 1.5042 | 0.6556 | 0.3360 | 0.5983 |

## 4. Validation OOF 선택 후보

| selector | candidate | segment_name | min_rows | cap | strength | fallback | validation_oof_MdAPE | validation_oof_MAPE | validation_oof_p95_APE | test_MdAPE | test_MAPE | test_p95_APE | test_RMSE_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation_oof_best_mdape | manual_qwidth_manual_min30_cap0.35_s1_zero | qwidth_manual | 30.0000 | 0.3500 | 1.0000 | zero | 0.3527 | 0.5410 | 1.4062 | 0.4338 | 1.0155 | 2.8025 | 0.8580 |
| validation_oof_best_mape | manual_pred_x_qwidth_manual_min30_cap0.35_s1_zero | pred_x_qwidth_manual | 30.0000 | 0.3500 | 1.0000 | zero | 0.3790 | 0.5272 | 1.3858 | 0.4388 | 1.1139 | 2.6028 | 0.8836 |
| validation_oof_best_p95 | manual_qwidth_manual_min30_cap0.35_s0.75_zero | qwidth_manual | 30.0000 | 0.3500 | 0.7500 | zero | 0.3554 | 0.5456 | 1.3331 | 0.4322 | 1.0179 | 3.0869 | 0.8534 |
| validation_oof_balanced_rank | manual_qwidth_manual_min30_cap0.35_s0.75_zero | qwidth_manual | 30.0000 | 0.3500 | 0.7500 | zero | 0.3554 | 0.5456 | 1.3331 | 0.4322 | 1.0179 | 3.0869 | 0.8534 |

## 5. Validation OOF 상위 후보

| experiment_id | candidate | scope | split | policy | n | RMSE_log | MdAPE | MAPE | p95_APE | Within_30 | Within_50 | over_3x_n | under_1_3x_n | segment_name | segment_columns | min_rows | cap | strength | fallback | global_correction | eligible_segments | total_segments |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-Y22 | manual_qwidth_manual_min30_cap0.35_s1_zero | cold | validation_oof | manual_segment_residual_calibration | 2753 | 0.6296 | 0.3527 | 0.5410 | 1.4062 | 0.4326 | 0.6731 | 71 | 114 | qwidth_manual | qwidth_manual | 30.0000 | 0.3500 | 1.0000 | zero | 0.0184 | 5.0000 | 5.0000 |
| PP-Y22 | manual_qwidth_manual_min100_cap0.35_s1_zero | cold | validation_oof | manual_segment_residual_calibration | 2753 | 0.6296 | 0.3527 | 0.5410 | 1.4062 | 0.4326 | 0.6731 | 71 | 114 | qwidth_manual | qwidth_manual | 100.0000 | 0.3500 | 1.0000 | zero | 0.0184 | 5.0000 | 5.0000 |
| PP-Y22 | manual_qwidth_manual_min30_cap0.35_s0.75_zero | cold | validation_oof | manual_segment_residual_calibration | 2753 | 0.6280 | 0.3554 | 0.5456 | 1.3331 | 0.4203 | 0.6582 | 75 | 108 | qwidth_manual | qwidth_manual | 30.0000 | 0.3500 | 0.7500 | zero | 0.0184 | 5.0000 | 5.0000 |
| PP-Y22 | manual_qwidth_manual_min100_cap0.35_s0.75_zero | cold | validation_oof | manual_segment_residual_calibration | 2753 | 0.6280 | 0.3554 | 0.5456 | 1.3331 | 0.4203 | 0.6582 | 75 | 108 | qwidth_manual | qwidth_manual | 100.0000 | 0.3500 | 0.7500 | zero | 0.0184 | 5.0000 | 5.0000 |
| PP-Y22 | manual_qwidth_manual_min30_cap0.25_s1_zero | cold | validation_oof | manual_segment_residual_calibration | 2753 | 0.6298 | 0.3568 | 0.5441 | 1.3383 | 0.4119 | 0.6578 | 71 | 113 | qwidth_manual | qwidth_manual | 30.0000 | 0.2500 | 1.0000 | zero | 0.0184 | 5.0000 | 5.0000 |
| PP-Y22 | manual_qwidth_manual_min100_cap0.25_s1_zero | cold | validation_oof | manual_segment_residual_calibration | 2753 | 0.6298 | 0.3568 | 0.5441 | 1.3383 | 0.4119 | 0.6578 | 71 | 113 | qwidth_manual | qwidth_manual | 100.0000 | 0.2500 | 1.0000 | zero | 0.0184 | 5.0000 | 5.0000 |
| PP-Y22 | manual_external_x_qwidth_manual_min30_cap0.35_s1_zero | cold | validation_oof | manual_segment_residual_calibration | 2753 | 0.6352 | 0.3642 | 0.5652 | 1.4472 | 0.4112 | 0.6302 | 81 | 114 | external_x_qwidth_manual | external_info_manual__qwidth_simple_manual | 30.0000 | 0.3500 | 1.0000 | zero | 0.0184 | 4.0000 | 5.0000 |
| PP-Y22 | manual_external_x_qwidth_manual_min100_cap0.35_s1_zero | cold | validation_oof | manual_segment_residual_calibration | 2753 | 0.6352 | 0.3642 | 0.5652 | 1.4472 | 0.4112 | 0.6302 | 81 | 114 | external_x_qwidth_manual | external_info_manual__qwidth_simple_manual | 100.0000 | 0.3500 | 1.0000 | zero | 0.0184 | 4.0000 | 5.0000 |
| PP-Y22 | manual_qwidth_manual_min30_cap0.25_s0.75_zero | cold | validation_oof | manual_segment_residual_calibration | 2753 | 0.6306 | 0.3655 | 0.5501 | 1.3363 | 0.4043 | 0.6527 | 75 | 105 | qwidth_manual | qwidth_manual | 30.0000 | 0.2500 | 0.7500 | zero | 0.0184 | 5.0000 | 5.0000 |
| PP-Y22 | manual_qwidth_manual_min100_cap0.25_s0.75_zero | cold | validation_oof | manual_segment_residual_calibration | 2753 | 0.6306 | 0.3655 | 0.5501 | 1.3363 | 0.4043 | 0.6527 | 75 | 105 | qwidth_manual | qwidth_manual | 100.0000 | 0.2500 | 0.7500 | zero | 0.0184 | 5.0000 | 5.0000 |
| PP-Y22 | manual_search_x_qwidth_manual_min100_cap0.35_s1_zero | cold | validation_oof | manual_segment_residual_calibration | 2753 | 0.6273 | 0.3674 | 0.5738 | 1.4967 | 0.3996 | 0.6451 | 91 | 85 | search_x_qwidth_manual | search_quality_manual__qwidth_simple_manual | 100.0000 | 0.3500 | 1.0000 | zero | 0.0184 | 4.0000 | 5.0000 |
| PP-Y22 | manual_search_x_qwidth_manual_min30_cap0.35_s1_zero | cold | validation_oof | manual_segment_residual_calibration | 2753 | 0.6264 | 0.3679 | 0.5743 | 1.4967 | 0.4003 | 0.6440 | 92 | 85 | search_x_qwidth_manual | search_quality_manual__qwidth_simple_manual | 30.0000 | 0.3500 | 1.0000 | zero | 0.0184 | 5.0000 | 5.0000 |
| PP-Y22 | manual_qwidth_manual_min30_cap0.15_s1_zero | cold | validation_oof | manual_segment_residual_calibration | 2753 | 0.6333 | 0.3706 | 0.5639 | 1.3808 | 0.4007 | 0.6389 | 76 | 100 | qwidth_manual | qwidth_manual | 30.0000 | 0.1500 | 1.0000 | zero | 0.0184 | 5.0000 | 5.0000 |
| PP-Y22 | manual_qwidth_manual_min100_cap0.15_s1_zero | cold | validation_oof | manual_segment_residual_calibration | 2753 | 0.6333 | 0.3706 | 0.5639 | 1.3808 | 0.4007 | 0.6389 | 76 | 100 | qwidth_manual | qwidth_manual | 100.0000 | 0.1500 | 1.0000 | zero | 0.0184 | 5.0000 | 5.0000 |
| PP-Y22 | manual_pred_x_qwidth_manual_min30_cap0.35_s0.75_zero | cold | validation_oof | manual_segment_residual_calibration | 2753 | 0.6249 | 0.3739 | 0.5330 | 1.3593 | 0.4014 | 0.6408 | 73 | 115 | pred_x_qwidth_manual | pred_price_manual__qwidth_simple_manual | 30.0000 | 0.3500 | 0.7500 | zero | 0.0184 | 12.0000 | 15.0000 |
| PP-Y22 | manual_external_x_qwidth_manual_min30_cap0.35_s0.75_zero | cold | validation_oof | manual_segment_residual_calibration | 2753 | 0.6308 | 0.3754 | 0.5616 | 1.3687 | 0.3919 | 0.6339 | 75 | 108 | external_x_qwidth_manual | external_info_manual__qwidth_simple_manual | 30.0000 | 0.3500 | 0.7500 | zero | 0.0184 | 4.0000 | 5.0000 |
| PP-Y22 | manual_external_x_qwidth_manual_min100_cap0.35_s0.75_zero | cold | validation_oof | manual_segment_residual_calibration | 2753 | 0.6308 | 0.3754 | 0.5616 | 1.3687 | 0.3919 | 0.6339 | 75 | 108 | external_x_qwidth_manual | external_info_manual__qwidth_simple_manual | 100.0000 | 0.3500 | 0.7500 | zero | 0.0184 | 4.0000 | 5.0000 |
| PP-Y22 | manual_search_x_qwidth_manual_min100_cap0.35_s0.75_zero | cold | validation_oof | manual_segment_residual_calibration | 2753 | 0.6259 | 0.3756 | 0.5692 | 1.4529 | 0.3839 | 0.6415 | 85 | 86 | search_x_qwidth_manual | search_quality_manual__qwidth_simple_manual | 100.0000 | 0.3500 | 0.7500 | zero | 0.0184 | 4.0000 | 5.0000 |
| PP-Y22 | manual_search_x_qwidth_manual_min30_cap0.35_s0.75_zero | cold | validation_oof | manual_segment_residual_calibration | 2753 | 0.6252 | 0.3757 | 0.5695 | 1.4529 | 0.3839 | 0.6404 | 86 | 86 | search_x_qwidth_manual | search_quality_manual__qwidth_simple_manual | 30.0000 | 0.3500 | 0.7500 | zero | 0.0184 | 5.0000 | 5.0000 |
| PP-Y22 | manual_qwidth_simple_manual_min30_cap0.35_s1_zero | cold | validation_oof | manual_segment_residual_calibration | 2753 | 0.6341 | 0.3783 | 0.5672 | 1.4601 | 0.3970 | 0.6291 | 80 | 110 | qwidth_simple_manual | qwidth_simple_manual | 30.0000 | 0.3500 | 1.0000 | zero | 0.0184 | 3.0000 | 3.0000 |

## 6. Test 상위 후보

| experiment_id | candidate | scope | split | policy | n | RMSE_log | MdAPE | MAPE | p95_APE | Within_30 | Within_50 | over_3x_n | under_1_3x_n | segment_name | segment_columns | min_rows | cap | strength | fallback | global_correction | eligible_segments | total_segments |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-Y22 | manual_qwidth_simple_manual_min30_cap0.25_s0.75_zero | cold | test | manual_segment_residual_calibration | 3099 | 0.8648 | 0.4233 | 1.1076 | 3.2064 | 0.3572 | 0.5860 | 258 | 246 | qwidth_simple_manual | qwidth_simple_manual | 30.0000 | 0.2500 | 0.7500 | zero | 0.0184 | 3.0000 | 3.0000 |
| PP-Y22 | manual_qwidth_simple_manual_min100_cap0.25_s0.75_zero | cold | test | manual_segment_residual_calibration | 3099 | 0.8648 | 0.4233 | 1.1076 | 3.2064 | 0.3572 | 0.5860 | 258 | 246 | qwidth_simple_manual | qwidth_simple_manual | 100.0000 | 0.2500 | 0.7500 | zero | 0.0184 | 3.0000 | 3.0000 |
| PP-Y22 | manual_search_x_qwidth_manual_min100_cap0.15_s0.75_zero | cold | test | manual_segment_residual_calibration | 3099 | 0.8557 | 0.4250 | 1.0889 | 3.5175 | 0.3395 | 0.5737 | 252 | 224 | search_x_qwidth_manual | search_quality_manual__qwidth_simple_manual | 100.0000 | 0.1500 | 0.7500 | zero | 0.0184 | 4.0000 | 5.0000 |
| PP-Y22 | manual_qwidth_simple_manual_min30_cap0.35_s0.75_zero | cold | test | manual_segment_residual_calibration | 3099 | 0.8666 | 0.4251 | 1.1122 | 3.1575 | 0.3588 | 0.5828 | 258 | 249 | qwidth_simple_manual | qwidth_simple_manual | 30.0000 | 0.3500 | 0.7500 | zero | 0.0184 | 3.0000 | 3.0000 |
| PP-Y22 | manual_qwidth_simple_manual_min100_cap0.35_s0.75_zero | cold | test | manual_segment_residual_calibration | 3099 | 0.8666 | 0.4251 | 1.1122 | 3.1575 | 0.3588 | 0.5828 | 258 | 249 | qwidth_simple_manual | qwidth_simple_manual | 100.0000 | 0.3500 | 0.7500 | zero | 0.0184 | 3.0000 | 3.0000 |
| PP-Y22 | manual_search_x_qwidth_manual_min100_cap0.25_s0.75_zero | cold | test | manual_segment_residual_calibration | 3099 | 0.8600 | 0.4255 | 1.1206 | 3.2064 | 0.3498 | 0.5744 | 264 | 219 | search_x_qwidth_manual | search_quality_manual__qwidth_simple_manual | 100.0000 | 0.2500 | 0.7500 | zero | 0.0184 | 4.0000 | 5.0000 |
| PP-Y22 | manual_qwidth_simple_manual_min30_cap0.15_s0.75_zero | cold | test | manual_segment_residual_calibration | 3099 | 0.8565 | 0.4264 | 1.0851 | 3.5175 | 0.3385 | 0.5773 | 248 | 230 | qwidth_simple_manual | qwidth_simple_manual | 30.0000 | 0.1500 | 0.7500 | zero | 0.0184 | 3.0000 | 3.0000 |
| PP-Y22 | manual_qwidth_simple_manual_min100_cap0.15_s0.75_zero | cold | test | manual_segment_residual_calibration | 3099 | 0.8565 | 0.4264 | 1.0851 | 3.5175 | 0.3385 | 0.5773 | 248 | 230 | qwidth_simple_manual | qwidth_simple_manual | 100.0000 | 0.1500 | 0.7500 | zero | 0.0184 | 3.0000 | 3.0000 |
| PP-Y22 | manual_search_x_qwidth_manual_min100_cap0.15_s1_zero | cold | test | manual_segment_residual_calibration | 3099 | 0.8579 | 0.4267 | 1.1072 | 3.3672 | 0.3459 | 0.5666 | 268 | 221 | search_x_qwidth_manual | search_quality_manual__qwidth_simple_manual | 100.0000 | 0.1500 | 1.0000 | zero | 0.0184 | 4.0000 | 5.0000 |
| PP-Y22 | manual_pred_x_qwidth_manual_min100_cap0.25_s0.75_zero | cold | test | manual_segment_residual_calibration | 3099 | 0.8610 | 0.4271 | 1.0491 | 3.1917 | 0.3572 | 0.5779 | 257 | 251 | pred_x_qwidth_manual | pred_price_manual__qwidth_simple_manual | 100.0000 | 0.2500 | 0.7500 | zero | 0.0184 | 10.0000 | 15.0000 |
| PP-Y22 | manual_qwidth_manual_min30_cap0.15_s0.75_zero | cold | test | manual_segment_residual_calibration | 3099 | 0.8521 | 0.4274 | 1.0407 | 3.5175 | 0.3308 | 0.5795 | 241 | 233 | qwidth_manual | qwidth_manual | 30.0000 | 0.1500 | 0.7500 | zero | 0.0184 | 5.0000 | 5.0000 |
| PP-Y22 | manual_qwidth_manual_min100_cap0.15_s0.75_zero | cold | test | manual_segment_residual_calibration | 3099 | 0.8521 | 0.4274 | 1.0407 | 3.5175 | 0.3308 | 0.5795 | 241 | 233 | qwidth_manual | qwidth_manual | 100.0000 | 0.1500 | 0.7500 | zero | 0.0184 | 5.0000 | 5.0000 |
| PP-Y22 | manual_pred_x_qwidth_manual_min30_cap0.25_s0.75_zero | cold | test | manual_segment_residual_calibration | 3099 | 0.8655 | 0.4275 | 1.0832 | 3.1917 | 0.3601 | 0.5779 | 257 | 251 | pred_x_qwidth_manual | pred_price_manual__qwidth_simple_manual | 30.0000 | 0.2500 | 0.7500 | zero | 0.0184 | 12.0000 | 15.0000 |
| PP-Y22 | manual_search_x_qwidth_manual_min100_cap0.25_s1_zero | cold | test | manual_segment_residual_calibration | 3099 | 0.8661 | 0.4279 | 1.1557 | 2.9516 | 0.3443 | 0.5641 | 281 | 228 | search_x_qwidth_manual | search_quality_manual__qwidth_simple_manual | 100.0000 | 0.2500 | 1.0000 | zero | 0.0184 | 4.0000 | 5.0000 |
| PP-Y22 | manual_pred_x_qwidth_manual_min100_cap0.15_s0.75_zero | cold | test | manual_segment_residual_calibration | 3099 | 0.8575 | 0.4280 | 1.0434 | 3.5023 | 0.3401 | 0.5744 | 237 | 248 | pred_x_qwidth_manual | pred_price_manual__qwidth_simple_manual | 100.0000 | 0.1500 | 0.7500 | zero | 0.0184 | 10.0000 | 15.0000 |
| PP-Y22 | manual_search_x_qwidth_manual_min30_cap0.15_s0.75_zero | cold | test | manual_segment_residual_calibration | 3099 | 0.8567 | 0.4287 | 1.0916 | 3.5175 | 0.3379 | 0.5708 | 252 | 224 | search_x_qwidth_manual | search_quality_manual__qwidth_simple_manual | 30.0000 | 0.1500 | 0.7500 | zero | 0.0184 | 5.0000 | 5.0000 |
| PP-Y22 | manual_search_x_qwidth_manual_min30_cap0.25_s0.75_zero | cold | test | manual_segment_residual_calibration | 3099 | 0.8609 | 0.4287 | 1.1233 | 3.2064 | 0.3482 | 0.5715 | 264 | 219 | search_x_qwidth_manual | search_quality_manual__qwidth_simple_manual | 30.0000 | 0.2500 | 0.7500 | zero | 0.0184 | 5.0000 | 5.0000 |
| PP-Y22 | manual_pred_x_qwidth_manual_min100_cap0.25_s1_zero | cold | test | manual_segment_residual_calibration | 3099 | 0.8681 | 0.4287 | 1.0587 | 2.9516 | 0.3556 | 0.5712 | 274 | 271 | pred_x_qwidth_manual | pred_price_manual__qwidth_simple_manual | 100.0000 | 0.2500 | 1.0000 | zero | 0.0184 | 10.0000 | 15.0000 |
| PP-Y22 | manual_pred_x_qwidth_manual_min30_cap0.15_s0.75_zero | cold | test | manual_segment_residual_calibration | 3099 | 0.8614 | 0.4290 | 1.0728 | 3.5023 | 0.3424 | 0.5747 | 237 | 248 | pred_x_qwidth_manual | pred_price_manual__qwidth_simple_manual | 30.0000 | 0.1500 | 0.7500 | zero | 0.0184 | 12.0000 | 15.0000 |
| PP-Y22 | manual_search_x_qwidth_manual_min30_cap0.15_s1_zero | cold | test | manual_segment_residual_calibration | 3099 | 0.8592 | 0.4296 | 1.1110 | 3.3672 | 0.3449 | 0.5637 | 268 | 221 | search_x_qwidth_manual | search_quality_manual__qwidth_simple_manual | 30.0000 | 0.1500 | 1.0000 | zero | 0.0184 | 5.0000 | 5.0000 |

## 7. 실행 결론

- 기준선 test MdAPE `0.4421`, MAPE `1.0484`, p95_APE `3.3537`.
- validation OOF로 선택된 수동 구간 후보 중 test 기준 최상위는 `manual_qwidth_manual_min30_cap0.35_s0.75_zero`.
- 해당 후보 test MdAPE `0.4322`, MAPE `1.0179`, p95_APE `3.0869`.
- 자동 구간 후보 `qwidth_bin_oof_min30_cap0.25`의 test MdAPE는 `0.4247`, MAPE는 `0.9910`, p95_APE는 `3.3053`.
- 결론: 수동 구간 후보는 기준선보다 MdAPE, MAPE, p95를 개선했지만 자동 qwidth 후보보다 MdAPE/MAPE가 낮지는 않았다.
- 따라서 수동 구간 보정은 v0.1 Cold 기본 보정 정책으로 바로 채택하지 않는다.
- 단, 수동 구간은 p95_APE를 낮추는 후보가 있어 큰 오차 방어 또는 수동 검수 우선순위 정책에는 활용 가치가 있다.
- test-only 상위 후보 `manual_qwidth_simple_manual_min30_cap0.25_s0.75_zero`는 test MdAPE `0.4233`으로 자동 qwidth 후보보다 낮았지만, validation OOF 선택 후보가 아니고 MAPE가 `1.1076`으로 악화되어 채택하지 않는다.
- 후속 실험은 수동 구간을 단독 보정보다 “자동 qwidth 후보 + p95 위험 구간만 수동 cap 보정” 형태로 제한 적용하는 방향이 적절하다.

## 8. 산출물

- metrics: `outputs/metrics.csv`
- predictions: `outputs/predictions.csv`
- correction map: `outputs/policy_map.csv`
- selection summary: `outputs/selection_summary.csv`
