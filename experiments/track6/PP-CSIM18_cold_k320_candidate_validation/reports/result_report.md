# Cold k320 후보 집중 검증

- 작성일: 2026-06-18T17:01:40
- 목적: k320 계열이 q35 k160 기준선을 대체할 수 있는지 집중 검증한다.
- 조건: `artist_key`, 같은 작가 가격 이력, lookup 후처리, `search_*`, 외부 live 검색 미사용.

## 1. Test 성능
| candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | APE_gt_1 | APE_gt_2 | APE_gt_5 | APE_gt_10 | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q35_k320_combined | test | 0.513510 | 0.926227 | 2.224042 | 0.932185 | 0.306551 | 0.484027 | 434 | 209 | 54 | 40 | 비가중+거리 가중 유사작품 k320 통계 + q35 |
| q35_k320_unweighted | test | 0.508301 | 0.946180 | 2.190874 | 0.934777 | 0.295257 | 0.492417 | 451 | 209 | 59 | 40 | 비가중 유사작품 k320 통계 + q35 |
| q35_k160_unweighted | test | 0.495018 | 0.971691 | 2.090436 | 0.943144 | 0.300742 | 0.502743 | 446 | 163 | 58 | 40 | 비가중 유사작품 k160 통계 + q35 |

## 2. Validation 성능
| candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | APE_gt_1 | APE_gt_2 | APE_gt_5 | APE_gt_10 | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q35_k320_unweighted | validation | 0.373800 | 0.472872 | 1.069764 | 0.674193 | 0.386124 | 0.670904 | 159 | 47 | 8 | 1 | 비가중 유사작품 k320 통계 + q35 |
| q35_k160_unweighted | validation | 0.359201 | 0.475196 | 1.115400 | 0.673808 | 0.386851 | 0.677080 | 160 | 46 | 8 | 1 | 비가중 유사작품 k160 통계 + q35 |
| q35_k320_combined | validation | 0.377500 | 0.477518 | 1.084326 | 0.679118 | 0.394479 | 0.672721 | 156 | 47 | 8 | 1 | 비가중+거리 가중 유사작품 k320 통계 + q35 |

## 3. Paired bootstrap vs q35_k160_unweighted
- delta는 `후보 - q35_k160_unweighted`다. 음수이면 후보가 기준선보다 좋다.
| split | candidate_a | candidate_b | n | n_boot | delta_MdAPE_a_minus_b_mean | delta_MAPE_a_minus_b_mean | delta_p95_APE_a_minus_b_mean | delta_RMSE_log_a_minus_b_mean | p_delta_MAPE_a_minus_b_lt_0 | p_delta_p95_APE_a_minus_b_lt_0 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | q35_k320_unweighted | q35_k160_unweighted | 2753 | 800 | 0.016420 | -0.002298 | -0.035028 | 0.000510 | 0.816250 | 0.871250 |
| validation | q35_k320_combined | q35_k160_unweighted | 2753 | 800 | 0.016401 | 0.002390 | -0.024364 | 0.005360 | 0.157500 | 0.766250 |
| test | q35_k320_unweighted | q35_k160_unweighted | 3099 | 800 | 0.010549 | -0.025169 | 0.122055 | -0.008322 | 0.987500 | 0.147500 |
| test | q35_k320_combined | q35_k160_unweighted | 3099 | 800 | 0.016315 | -0.044886 | 0.133802 | -0.010861 | 1.000000 | 0.178750 |

## 4. Test 가격대별 진단
| candidate | split | segment | n | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 | APE_gt_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q35_k160_unweighted | test | 1m_3m | 866 | 0.449293 | 0.775798 | 2.215003 | 0.691915 | 51 | 6 | 2 |
| q35_k320_combined | test | 1m_3m | 866 | 0.464200 | 0.744423 | 2.174374 | 0.679807 | 54 | 3 | 2 |
| q35_k320_unweighted | test | 1m_3m | 866 | 0.472683 | 0.767563 | 2.164435 | 0.685893 | 53 | 5 | 2 |
| q35_k160_unweighted | test | 3m_10m | 1057 | 0.464583 | 0.482630 | 0.895791 | 0.780519 | 7 | 2 | 0 |
| q35_k320_combined | test | 3m_10m | 1057 | 0.463550 | 0.479942 | 0.899843 | 0.768103 | 7 | 2 | 0 |
| q35_k320_unweighted | test | 3m_10m | 1057 | 0.451867 | 0.480441 | 0.910621 | 0.761953 | 7 | 2 | 0 |
| q35_k160_unweighted | test | gt_10m | 636 | 0.554615 | 0.547219 | 0.909412 | 1.253620 | 0 | 0 | 0 |
| q35_k320_combined | test | gt_10m | 636 | 0.541008 | 0.553264 | 0.907861 | 1.248786 | 0 | 0 | 0 |
| q35_k320_unweighted | test | gt_10m | 636 | 0.545868 | 0.551558 | 0.911108 | 1.249160 | 0 | 0 | 0 |
| q35_k160_unweighted | test | lt_1m | 540 | 0.695267 | 2.743070 | 20.911669 | 1.137395 | 105 | 50 | 38 |
| q35_k320_combined | test | lt_1m | 540 | 0.718872 | 2.530614 | 19.417337 | 1.119933 | 148 | 49 | 38 |
| q35_k320_unweighted | test | lt_1m | 540 | 0.759716 | 2.609048 | 20.308285 | 1.134024 | 149 | 52 | 38 |

## 5. Test 결측 스트레스
| candidate | stress_scenario | split | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 | APE_gt_10 | missing_fields |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q35_k160_unweighted | as_is | test | 0.495018 | 0.971691 | 2.090436 | 0.943144 | 163 | 58 | 40 |  |
| q35_k320_combined | as_is | test | 0.513510 | 0.926227 | 2.224042 | 0.932185 | 209 | 54 | 40 |  |
| q35_k320_unweighted | as_is | test | 0.508301 | 0.946180 | 2.190874 | 0.934777 | 209 | 59 | 40 |  |
| q35_k160_unweighted | missing_all_core_numeric | test | 0.493722 | 0.913230 | 2.528718 | 0.931071 | 186 | 71 | 37 | artist_meta_birth_year,artist_meta_total_works,artist_meta_total_works_log,artist_meta_followers,artist_meta_followers_log,artist_meta_career_stage |
| q35_k320_combined | missing_all_core_numeric | test | 0.498081 | 0.900627 | 2.457310 | 0.924687 | 177 | 68 | 36 | artist_meta_birth_year,artist_meta_total_works,artist_meta_total_works_log,artist_meta_followers,artist_meta_followers_log,artist_meta_career_stage |
| q35_k320_unweighted | missing_all_core_numeric | test | 0.490453 | 0.906007 | 2.486230 | 0.923398 | 180 | 71 | 37 | artist_meta_birth_year,artist_meta_total_works,artist_meta_total_works_log,artist_meta_followers,artist_meta_followers_log,artist_meta_career_stage |
| q35_k160_unweighted | missing_birth_and_followers | test | 0.506584 | 0.973950 | 2.097062 | 0.942703 | 164 | 58 | 40 | artist_meta_birth_year,artist_meta_followers,artist_meta_followers_log |
| q35_k320_combined | missing_birth_and_followers | test | 0.513955 | 0.924460 | 2.224042 | 0.931052 | 209 | 54 | 40 | artist_meta_birth_year,artist_meta_followers,artist_meta_followers_log |
| q35_k320_unweighted | missing_birth_and_followers | test | 0.508301 | 0.941924 | 2.190874 | 0.933248 | 209 | 58 | 40 | artist_meta_birth_year,artist_meta_followers,artist_meta_followers_log |
| q35_k160_unweighted | missing_birth_year | test | 0.506584 | 0.973950 | 2.097062 | 0.942703 | 164 | 58 | 40 | artist_meta_birth_year |
| q35_k320_combined | missing_birth_year | test | 0.513955 | 0.924460 | 2.224042 | 0.931052 | 209 | 54 | 40 | artist_meta_birth_year |
| q35_k320_unweighted | missing_birth_year | test | 0.508301 | 0.941924 | 2.190874 | 0.933248 | 209 | 58 | 40 | artist_meta_birth_year |
| q35_k160_unweighted | missing_career_stage | test | 0.493142 | 0.913380 | 2.528718 | 0.932156 | 185 | 71 | 37 | artist_meta_career_stage |
| q35_k320_combined | missing_career_stage | test | 0.500515 | 0.902550 | 2.460385 | 0.925737 | 177 | 68 | 36 | artist_meta_career_stage |
| q35_k320_unweighted | missing_career_stage | test | 0.491456 | 0.907998 | 2.486230 | 0.924255 | 180 | 72 | 37 | artist_meta_career_stage |
| q35_k160_unweighted | missing_followers | test | 0.495018 | 0.971691 | 2.090436 | 0.943144 | 163 | 58 | 40 | artist_meta_followers,artist_meta_followers_log |
| q35_k320_combined | missing_followers | test | 0.513510 | 0.926227 | 2.224042 | 0.932185 | 209 | 54 | 40 | artist_meta_followers,artist_meta_followers_log |
| q35_k320_unweighted | missing_followers | test | 0.508301 | 0.946180 | 2.190874 | 0.934777 | 209 | 59 | 40 | artist_meta_followers,artist_meta_followers_log |
| q35_k160_unweighted | missing_total_works | test | 0.495018 | 0.971691 | 2.090436 | 0.943144 | 163 | 58 | 40 | artist_meta_total_works,artist_meta_total_works_log |
| q35_k320_combined | missing_total_works | test | 0.513510 | 0.926227 | 2.224042 | 0.932185 | 209 | 54 | 40 | artist_meta_total_works,artist_meta_total_works_log |
| q35_k320_unweighted | missing_total_works | test | 0.508301 | 0.946180 | 2.190874 | 0.934777 | 209 | 59 | 40 | artist_meta_total_works,artist_meta_total_works_log |

## 6. 예측 이동량
| candidate | split | n | mean_log_shift_vs_baseline | median_log_shift_vs_baseline | p05_log_shift_vs_baseline | p95_log_shift_vs_baseline | share_lower_than_baseline |
| --- | --- | --- | --- | --- | --- | --- | --- |
| q35_k160_unweighted | validation | 2753 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| q35_k320_combined | validation | 2753 | -0.001521 | 0.006329 | -0.136924 | 0.161917 | 0.482020 |
| q35_k320_unweighted | validation | 2753 | -0.006800 | -0.008803 | -0.173007 | 0.176822 | 0.538685 |
| q35_k160_unweighted | test | 3099 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| q35_k320_combined | test | 3099 | 0.007254 | 0.002288 | -0.174111 | 0.198938 | 0.487254 |
| q35_k320_unweighted | test | 3099 | 0.011636 | 0.009076 | -0.176131 | 0.211377 | 0.459503 |