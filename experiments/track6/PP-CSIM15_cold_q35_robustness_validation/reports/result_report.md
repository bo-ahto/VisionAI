# Cold q35 후보 강건성 검증

- 작성일: 2026-06-18T16:45:30
- 목적: q35 후보가 기존 q45보다 운영 후보로 승격 가능한지 강건성까지 확인한다.
- 조건: `artist_key`, 같은 작가 가격 이력, `artist_key` lookup 후처리, `search_*`, 외부 live 검색 미사용.
- q35/q45 모두 같은 학습 데이터, 같은 피처, 같은 유사작품 k160 기준 통계를 사용하고 LightGBM Quantile alpha만 다르다.
- 부분 선택 정책은 실제 가격을 보지 않고 사용 단계에서 알 수 있는 예측가/유사작품 통계만 사용한다.

## 1. Test 성능: tail 기준 정렬
| candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | APE_gt_1 | APE_gt_2 | APE_gt_5 | APE_gt_10 | q35_selected_rate | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q35_global | test | 0.495018 | 0.971691 | 2.090436 | 0.943144 | 0.300742 | 0.502743 | 446 | 163 | 58 | 40 | 1.000000 | 전체 q35 후보 |
| q35_if_q45_above_refq25_0p2 | test | 0.491948 | 0.998513 | 2.212824 | 0.941382 | 0.302356 | 0.506938 | 452 | 169 | 59 | 40 | 0.821878 | q45가 유사작품 q25보다 0.20 log 이상 높으면 q35, 아니면 q45 |
| q35_if_pred_lt_300w | test | 0.487643 | 1.052516 | 2.390672 | 0.925884 | 0.322039 | 0.508874 | 535 | 196 | 61 | 43 | 0.454017 | q45 예측가가 300만원 미만이면 q35, 아니면 q45 |
| q45_current | test | 0.496699 | 1.086514 | 2.452153 | 0.909771 | 0.322039 | 0.503066 | 578 | 232 | 66 | 43 | 0.000000 | 기존 q45 후보 |

## 2. Validation 성능: tail 기준 정렬
| candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | APE_gt_1 | APE_gt_2 | APE_gt_5 | APE_gt_10 | q35_selected_rate | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q35_global | validation | 0.359201 | 0.475196 | 1.115400 | 0.673808 | 0.386851 | 0.677080 | 160 | 46 | 8 | 1 | 1.000000 | 전체 q35 후보 |
| q35_if_q45_above_refq25_0p2 | validation | 0.365821 | 0.491399 | 1.314477 | 0.671201 | 0.383218 | 0.677080 | 190 | 52 | 8 | 1 | 0.610243 | q45가 유사작품 q25보다 0.20 log 이상 높으면 q35, 아니면 q45 |
| q35_if_pred_lt_300w | validation | 0.357198 | 0.497871 | 1.309407 | 0.663564 | 0.401380 | 0.671994 | 206 | 56 | 8 | 2 | 0.615692 | q45 예측가가 300만원 미만이면 q35, 아니면 q45 |
| q45_current | validation | 0.365821 | 0.540571 | 1.471871 | 0.655823 | 0.367236 | 0.681075 | 262 | 73 | 18 | 4 | 0.000000 | 기존 q45 후보 |

## 3. Paired bootstrap
- delta는 `후보 - q45_current`다. 음수이면 후보가 q45보다 좋다.
| split | candidate_a | candidate_b | n | n_boot | delta_MdAPE_a_minus_b_mean | delta_MAPE_a_minus_b_mean | delta_p95_APE_a_minus_b_mean | delta_RMSE_log_a_minus_b_mean | p_delta_MdAPE_a_minus_b_lt_0 | p_delta_MAPE_a_minus_b_lt_0 | p_delta_p95_APE_a_minus_b_lt_0 | p_delta_RMSE_log_a_minus_b_lt_0 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | q35_global | q45_current | 2753 | 800 | -0.006573 | -0.065383 | -0.349335 | 0.018060 | 0.877500 | 1.000000 | 1.000000 | 0.000000 |
| validation | q35_if_pred_lt_300w | q45_current | 2753 | 800 | -0.008786 | -0.042608 | -0.154727 | 0.007841 | 0.965000 | 1.000000 | 1.000000 | 0.005000 |
| validation | q35_if_q45_above_refq25_0p2 | q45_current | 2753 | 800 | -0.000296 | -0.049288 | -0.169804 | 0.015371 | 0.482500 | 1.000000 | 1.000000 | 0.000000 |
| test | q35_global | q45_current | 3099 | 800 | -0.000808 | -0.115044 | -0.396110 | 0.033431 | 0.508750 | 1.000000 | 1.000000 | 0.000000 |
| test | q35_if_pred_lt_300w | q45_current | 3099 | 800 | -0.008295 | -0.034085 | -0.093555 | 0.016036 | 0.903750 | 1.000000 | 0.978750 | 0.000000 |
| test | q35_if_q45_above_refq25_0p2 | q45_current | 3099 | 800 | -0.004802 | -0.088141 | -0.320394 | 0.031674 | 0.696250 | 1.000000 | 1.000000 | 0.000000 |

## 4. Test 가격대별 진단
| candidate | split | segment | n | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 | APE_gt_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q35_global | test | 1m_3m | 866 | 0.449293 | 0.775798 | 2.215003 | 0.691915 | 51 | 6 | 2 |
| q35_if_pred_lt_300w | test | 1m_3m | 866 | 0.482106 | 0.898398 | 2.500168 | 0.746327 | 75 | 8 | 2 |
| q35_if_q45_above_refq25_0p2 | test | 1m_3m | 866 | 0.449980 | 0.788544 | 2.288245 | 0.693782 | 55 | 8 | 2 |
| q45_current | test | 1m_3m | 866 | 0.509186 | 0.915907 | 2.500168 | 0.726037 | 75 | 8 | 2 |
| q35_global | test | 3m_10m | 1057 | 0.464583 | 0.482630 | 0.895791 | 0.780519 | 7 | 2 | 0 |
| q35_if_pred_lt_300w | test | 3m_10m | 1057 | 0.480356 | 0.534136 | 1.222818 | 0.784025 | 15 | 2 | 1 |
| q35_if_q45_above_refq25_0p2 | test | 3m_10m | 1057 | 0.462416 | 0.480970 | 0.918948 | 0.770224 | 7 | 2 | 0 |
| q45_current | test | 3m_10m | 1057 | 0.429399 | 0.512366 | 1.222818 | 0.706357 | 15 | 2 | 1 |
| q35_global | test | gt_10m | 636 | 0.554615 | 0.547219 | 0.909412 | 1.253620 | 0 | 0 | 0 |
| q35_if_pred_lt_300w | test | gt_10m | 636 | 0.459469 | 0.479238 | 0.898497 | 1.111311 | 0 | 0 | 0 |
| q35_if_q45_above_refq25_0p2 | test | gt_10m | 636 | 0.542405 | 0.541280 | 0.908529 | 1.241055 | 0 | 0 | 0 |
| q45_current | test | gt_10m | 636 | 0.459469 | 0.478404 | 0.898497 | 1.100473 | 0 | 0 | 0 |
| q35_global | test | lt_1m | 540 | 0.695267 | 2.743070 | 20.911669 | 1.137395 | 105 | 50 | 38 |
| q35_if_pred_lt_300w | test | lt_1m | 540 | 0.695267 | 2.989546 | 24.822371 | 1.169905 | 106 | 51 | 40 |
| q35_if_q45_above_refq25_0p2 | test | lt_1m | 540 | 0.699765 | 2.886801 | 22.527743 | 1.156993 | 107 | 49 | 38 |
| q45_current | test | lt_1m | 540 | 0.880594 | 3.200176 | 24.822371 | 1.225420 | 142 | 56 | 40 |

## 5. Test 결측 스트레스
| candidate | stress_scenario | split | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 | APE_gt_10 | missing_fields |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q35_global | as_is | test | 0.495018 | 0.971691 | 2.090436 | 0.943144 | 163 | 58 | 40 |  |
| q45_current | as_is | test | 0.496699 | 1.086514 | 2.452153 | 0.909771 | 232 | 66 | 43 |  |
| q35_global | missing_all_core_numeric | test | 0.493722 | 0.913230 | 2.528718 | 0.931071 | 186 | 71 | 37 | artist_meta_birth_year,artist_meta_total_works,artist_meta_total_works_log,artist_meta_followers,artist_meta_followers_log,artist_meta_career_stage |
| q45_current | missing_all_core_numeric | test | 0.479119 | 1.014595 | 2.917513 | 0.889464 | 249 | 77 | 38 | artist_meta_birth_year,artist_meta_total_works,artist_meta_total_works_log,artist_meta_followers,artist_meta_followers_log,artist_meta_career_stage |
| q35_global | missing_birth_and_followers | test | 0.506584 | 0.973950 | 2.097062 | 0.942703 | 164 | 58 | 40 | artist_meta_birth_year,artist_meta_followers,artist_meta_followers_log |
| q45_current | missing_birth_and_followers | test | 0.496699 | 1.081960 | 2.476940 | 0.907828 | 229 | 66 | 43 | artist_meta_birth_year,artist_meta_followers,artist_meta_followers_log |
| q35_global | missing_birth_year | test | 0.506584 | 0.973950 | 2.097062 | 0.942703 | 164 | 58 | 40 | artist_meta_birth_year |
| q45_current | missing_birth_year | test | 0.496699 | 1.081960 | 2.476940 | 0.907828 | 229 | 66 | 43 | artist_meta_birth_year |
| q35_global | missing_career_stage | test | 0.493142 | 0.913380 | 2.528718 | 0.932156 | 185 | 71 | 37 | artist_meta_career_stage |
| q45_current | missing_career_stage | test | 0.479842 | 1.014965 | 2.917513 | 0.889890 | 249 | 76 | 38 | artist_meta_career_stage |
| q35_global | missing_followers | test | 0.495018 | 0.971691 | 2.090436 | 0.943144 | 163 | 58 | 40 | artist_meta_followers,artist_meta_followers_log |
| q45_current | missing_followers | test | 0.496699 | 1.086514 | 2.452153 | 0.909771 | 232 | 66 | 43 | artist_meta_followers,artist_meta_followers_log |
| q35_global | missing_total_works | test | 0.495018 | 0.971691 | 2.090436 | 0.943144 | 163 | 58 | 40 | artist_meta_total_works,artist_meta_total_works_log |
| q45_current | missing_total_works | test | 0.496699 | 1.086514 | 2.452153 | 0.909771 | 232 | 66 | 43 | artist_meta_total_works,artist_meta_total_works_log |

## 6. 결론

- `q35_global`은 q45 대비 MAPE, p95, APE > 5를 낮추는 방향이 test에서 확인된다.
- q35의 이점은 1백만원 미만 및 1백만~3백만원 구간의 과대예측 완화에서 주로 나온다.
- 1천만원 이상 고가 구간은 q45가 더 안정적인 편이므로, q35를 전면 적용할지는 고가 구간 손실과 tail 개선의 trade-off로 판단해야 한다.
- 부분 선택 정책은 q35 선택률을 낮출 수 있지만, 이번 검증에서는 full q35의 tail 개선을 일관되게 넘지는 못했다.