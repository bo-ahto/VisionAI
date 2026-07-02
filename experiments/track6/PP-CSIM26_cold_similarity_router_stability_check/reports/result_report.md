# Cold 유사 이웃 잔차 라우터 안정성 재검증

- 작성일: 2026-06-22T15:51:16
- 목적: CSIM25에서 남은 k40/k80 규칙 후보의 split 안정성과 bootstrap 우세 여부를 재검증한다.
- 추가 학습 없음. CSIM24 예측값과 CSIM25 라우팅 규칙만 재사용한다.
- 금지: 실제 가격을 라우터 입력으로 쓰지 않음, `artist_key`/동일 작가 가격 이력/검색 lookup 미사용.

## 1. 후보별 성능
| candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 | APE_gt_10 | selected_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | test | 0.472314 | 0.706767 | 2.161091 | 0.806398 | 184 | 30 | 7 | 0.581333 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | test | 0.475254 | 0.707336 | 2.161091 | 0.805736 | 184 | 30 | 7 | 0.557667 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | test | 0.469877 | 0.708626 | 2.169832 | 0.804789 | 186 | 30 | 7 | 0.581333 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | test | 0.472052 | 0.709195 | 2.169832 | 0.804126 | 186 | 30 | 7 | 0.557667 |
| resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p03 | test | 0.484487 | 0.732605 | 2.264398 | 0.806765 | 204 | 32 | 8 | 0.174333 |
| resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p05 | test | 0.484487 | 0.733582 | 2.264398 | 0.806729 | 204 | 32 | 8 | 0.128333 |
| resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p03 | test | 0.483910 | 0.734169 | 2.288508 | 0.806809 | 204 | 32 | 8 | 0.174333 |
| resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p05 | test | 0.483910 | 0.735146 | 2.288508 | 0.806772 | 204 | 32 | 8 | 0.128333 |
| base | test | 0.481850 | 0.746296 | 2.398009 | 0.802895 | 212 | 35 | 8 | 0.000000 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | validation | 0.405434 | 0.563535 | 1.648824 | 0.807140 | 77 | 8 | 1 | 0.556505 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | validation | 0.405266 | 0.564256 | 1.648824 | 0.807453 | 77 | 7 | 1 | 0.556505 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | validation | 0.405582 | 0.564505 | 1.648824 | 0.811121 | 77 | 8 | 1 | 0.643883 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | validation | 0.405492 | 0.565225 | 1.648824 | 0.811433 | 77 | 7 | 1 | 0.643883 |
| resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p03 | validation | 0.409345 | 0.586161 | 1.739339 | 0.806684 | 90 | 10 | 1 | 0.236893 |
| resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p05 | validation | 0.409345 | 0.586375 | 1.739339 | 0.806569 | 91 | 10 | 1 | 0.227573 |
| resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p03 | validation | 0.409345 | 0.586703 | 1.739339 | 0.806988 | 90 | 9 | 1 | 0.236893 |
| resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p05 | validation | 0.409345 | 0.586917 | 1.739339 | 0.806873 | 91 | 9 | 1 | 0.227573 |
| base | validation | 0.424537 | 0.606746 | 1.808312 | 0.809976 | 97 | 10 | 1 | 0.000000 |

## 2. 지표별 순위
| candidate | split | rank_sum | MdAPE_rank | MAPE_rank | p95_APE_rank | APE_gt_5_rank |
| --- | --- | --- | --- | --- | --- | --- |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | test | 6.000000 | 3.000000 | 1.000000 | 1.000000 | 1.000000 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | test | 8.000000 | 1.000000 | 3.000000 | 3.000000 | 1.000000 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | test | 8.000000 | 4.000000 | 2.000000 | 1.000000 | 1.000000 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | test | 10.000000 | 2.000000 | 4.000000 | 3.000000 | 1.000000 |
| resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p03 | test | 23.000000 | 8.000000 | 5.000000 | 5.000000 | 5.000000 |
| resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p05 | test | 24.000000 | 8.000000 | 6.000000 | 5.000000 | 5.000000 |
| resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p03 | test | 25.000000 | 6.000000 | 7.000000 | 7.000000 | 5.000000 |
| resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p05 | test | 26.000000 | 6.000000 | 8.000000 | 7.000000 | 5.000000 |
| base | test | 32.000000 | 5.000000 | 9.000000 | 9.000000 | 9.000000 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | validation | 5.000000 | 1.000000 | 2.000000 | 1.000000 | 1.000000 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | validation | 7.000000 | 2.000000 | 1.000000 | 1.000000 | 3.000000 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | validation | 9.000000 | 3.000000 | 4.000000 | 1.000000 | 1.000000 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | validation | 11.000000 | 4.000000 | 3.000000 | 1.000000 | 3.000000 |
| resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p03 | validation | 22.000000 | 5.000000 | 5.000000 | 5.000000 | 7.000000 |
| resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p03 | validation | 22.000000 | 5.000000 | 7.000000 | 5.000000 | 5.000000 |
| resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p05 | validation | 23.000000 | 5.000000 | 6.000000 | 5.000000 | 7.000000 |
| resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p05 | validation | 23.000000 | 5.000000 | 8.000000 | 5.000000 | 5.000000 |
| base | validation | 34.000000 | 9.000000 | 9.000000 | 9.000000 | 7.000000 |

## 3. Paired bootstrap
| comparison | split | candidate_a | candidate_b | n | n_boot | delta_MdAPE_a_minus_b_mean | delta_MAPE_a_minus_b_mean | delta_p95_APE_a_minus_b_mean | p_delta_MdAPE_a_minus_b_lt_0 | p_delta_MAPE_a_minus_b_lt_0 | p_delta_p95_APE_a_minus_b_lt_0 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| candidate_vs_base | validation | resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | base | 2575 | 800 | -0.019092 | -0.042204 | -0.165997 | 1.000000 | 1.000000 | 1.000000 |
| candidate_vs_base | validation | resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | base | 2575 | 800 | -0.019731 | -0.043172 | -0.164226 | 1.000000 | 1.000000 | 1.000000 |
| candidate_vs_base | validation | resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | base | 2575 | 800 | -0.019447 | -0.041479 | -0.168958 | 0.998750 | 1.000000 | 1.000000 |
| candidate_vs_base | validation | resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | base | 2575 | 800 | -0.020120 | -0.042448 | -0.167187 | 1.000000 | 1.000000 | 1.000000 |
| candidate_vs_base | validation | resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p03 | base | 2575 | 800 | -0.015766 | -0.020549 | -0.055043 | 1.000000 | 1.000000 | 1.000000 |
| candidate_vs_base | validation | resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p05 | base | 2575 | 800 | -0.015565 | -0.020333 | -0.055043 | 1.000000 | 1.000000 | 1.000000 |
| candidate_vs_base | validation | resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p03 | base | 2575 | 800 | -0.016367 | -0.020011 | -0.055169 | 1.000000 | 1.000000 | 1.000000 |
| candidate_vs_base | validation | resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p05 | base | 2575 | 800 | -0.016146 | -0.019795 | -0.055169 | 1.000000 | 1.000000 | 1.000000 |
| k40_vs_k80 | validation | resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p03 | 2575 | 800 | -0.003326 | -0.021654 | -0.110954 | 0.738750 | 1.000000 | 1.000000 |
| k40_vs_k80 | validation | resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p03 | 2575 | 800 | -0.003080 | -0.021468 | -0.113789 | 0.737500 | 1.000000 | 1.000000 |
| k40_vs_k80 | validation | resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p05 | 2575 | 800 | -0.004165 | -0.022839 | -0.109183 | 0.812500 | 1.000000 | 1.000000 |
| k40_vs_k80 | validation | resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p05 | 2575 | 800 | -0.003974 | -0.022652 | -0.112018 | 0.825000 | 1.000000 | 1.000000 |
| candidate_vs_base | test | resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | base | 3000 | 800 | -0.008848 | -0.037624 | -0.182347 | 0.983750 | 1.000000 | 1.000000 |
| candidate_vs_base | test | resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | base | 3000 | 800 | -0.007451 | -0.037050 | -0.182347 | 0.966250 | 1.000000 | 1.000000 |
| candidate_vs_base | test | resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | base | 3000 | 800 | -0.007573 | -0.039491 | -0.206259 | 0.965000 | 1.000000 | 1.000000 |
| candidate_vs_base | test | resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | base | 3000 | 800 | -0.006241 | -0.038918 | -0.206259 | 0.936250 | 1.000000 | 1.000000 |
| candidate_vs_base | test | resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p03 | base | 3000 | 800 | 0.002547 | -0.012093 | -0.088785 | 0.092500 | 1.000000 | 0.991250 |
| candidate_vs_base | test | resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p05 | base | 3000 | 800 | 0.002357 | -0.011124 | -0.088785 | 0.111250 | 1.000000 | 0.991250 |
| candidate_vs_base | test | resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p03 | base | 3000 | 800 | 0.003281 | -0.013664 | -0.109822 | 0.076250 | 1.000000 | 0.998750 |
| candidate_vs_base | test | resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p05 | base | 3000 | 800 | 0.003121 | -0.012695 | -0.109822 | 0.091250 | 1.000000 | 0.998750 |
| k40_vs_k80 | test | resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p03 | 3000 | 800 | -0.011395 | -0.025530 | -0.093563 | 0.996250 | 1.000000 | 0.998750 |
| k40_vs_k80 | test | resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p03 | 3000 | 800 | -0.010854 | -0.025827 | -0.096437 | 0.990000 | 1.000000 | 0.997500 |
| k40_vs_k80 | test | resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p05 | 3000 | 800 | -0.009808 | -0.025926 | -0.093563 | 0.983750 | 1.000000 | 0.998750 |
| k40_vs_k80 | test | resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p05 | 3000 | 800 | -0.009362 | -0.026223 | -0.096437 | 0.971250 | 1.000000 | 0.997500 |

## 4. 가격대별 진단
| candidate | split | segment | n | selected_rate | MdAPE | MAPE | p95_APE | APE_gt_2 | APE_gt_5 | APE_gt_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base | test | 1m_3m | 948 | 0.000000 | 0.414611 | 0.727543 | 2.301306 | 64 | 11 | 3 |
| base | test | 3m_10m | 980 | 0.000000 | 0.420003 | 0.519689 | 1.447841 | 30 | 2 | 0 |
| base | test | gt_10m | 496 | 0.000000 | 0.495163 | 0.494618 | 0.909020 | 0 | 0 | 0 |
| base | test | lt_1m | 576 | 0.000000 | 0.841231 | 1.379428 | 3.928765 | 118 | 22 | 5 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | test | 1m_3m | 948 | 0.541139 | 0.420074 | 0.685461 | 2.102299 | 55 | 10 | 2 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | test | 3m_10m | 980 | 0.559184 | 0.420240 | 0.502822 | 1.293536 | 20 | 2 | 0 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | test | gt_10m | 496 | 0.677419 | 0.512837 | 0.503988 | 0.917744 | 0 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | test | lt_1m | 576 | 0.602431 | 0.739975 | 1.273118 | 3.745833 | 111 | 18 | 5 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | test | 1m_3m | 948 | 0.517932 | 0.420074 | 0.686250 | 2.102299 | 55 | 10 | 2 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | test | 3m_10m | 980 | 0.533673 | 0.421034 | 0.503468 | 1.293536 | 20 | 2 | 0 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | test | gt_10m | 496 | 0.637097 | 0.512837 | 0.503849 | 0.917744 | 0 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | test | lt_1m | 576 | 0.595486 | 0.739975 | 1.273805 | 3.745833 | 111 | 18 | 5 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | test | 1m_3m | 948 | 0.541139 | 0.420074 | 0.683591 | 2.100471 | 55 | 10 | 2 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | test | 3m_10m | 980 | 0.559184 | 0.419859 | 0.503403 | 1.293536 | 20 | 2 | 0 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | test | gt_10m | 496 | 0.677419 | 0.512837 | 0.504848 | 0.922408 | 0 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | test | lt_1m | 576 | 0.602431 | 0.739975 | 1.264787 | 3.745833 | 109 | 18 | 5 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | test | 1m_3m | 948 | 0.517932 | 0.420074 | 0.684379 | 2.100471 | 55 | 10 | 2 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | test | 3m_10m | 980 | 0.533673 | 0.420240 | 0.504049 | 1.293536 | 20 | 2 | 0 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | test | gt_10m | 496 | 0.637097 | 0.512837 | 0.504710 | 0.922408 | 0 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | test | lt_1m | 576 | 0.595486 | 0.739975 | 1.265474 | 3.745833 | 109 | 18 | 5 |
| resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p03 | test | 1m_3m | 948 | 0.203586 | 0.418459 | 0.713999 | 2.264174 | 61 | 11 | 3 |
| resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p03 | test | 3m_10m | 980 | 0.129592 | 0.426163 | 0.520380 | 1.420724 | 30 | 2 | 0 |
| resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p03 | test | gt_10m | 496 | 0.177419 | 0.501835 | 0.499064 | 0.917664 | 0 | 0 | 0 |
| resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p03 | test | lt_1m | 576 | 0.199653 | 0.841231 | 1.333553 | 3.840359 | 113 | 19 | 5 |
| resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p05 | test | 1m_3m | 948 | 0.126582 | 0.418459 | 0.715178 | 2.264174 | 61 | 11 | 3 |
| resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p05 | test | 3m_10m | 980 | 0.090816 | 0.426163 | 0.520876 | 1.420724 | 30 | 2 | 0 |
| resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p05 | test | gt_10m | 496 | 0.147177 | 0.501835 | 0.498263 | 0.917664 | 0 | 0 | 0 |
| resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p05 | test | lt_1m | 576 | 0.178819 | 0.841231 | 1.336548 | 3.840359 | 113 | 19 | 5 |
| resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p03 | test | 1m_3m | 948 | 0.203586 | 0.419229 | 0.712011 | 2.264174 | 61 | 11 | 3 |
| resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p03 | test | 3m_10m | 980 | 0.129592 | 0.426163 | 0.520688 | 1.420724 | 30 | 2 | 0 |
| resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p03 | test | gt_10m | 496 | 0.177419 | 0.501835 | 0.499353 | 0.917664 | 0 | 0 | 0 |
| resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p03 | test | lt_1m | 576 | 0.199653 | 0.841231 | 1.327908 | 3.840359 | 113 | 19 | 5 |
| resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p05 | test | 1m_3m | 948 | 0.126582 | 0.419229 | 0.713190 | 2.264174 | 61 | 11 | 3 |
| resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p05 | test | 3m_10m | 980 | 0.090816 | 0.426163 | 0.521184 | 1.420724 | 30 | 2 | 0 |
| resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p05 | test | gt_10m | 496 | 0.147177 | 0.501835 | 0.498552 | 0.917664 | 0 | 0 | 0 |
| resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p05 | test | lt_1m | 576 | 0.178819 | 0.841231 | 1.330904 | 3.840359 | 113 | 19 | 5 |
| base | validation | 1m_3m | 837 | 0.000000 | 0.357073 | 0.581180 | 1.839279 | 34 | 2 | 0 |
| base | validation | 3m_10m | 744 | 0.000000 | 0.328934 | 0.438459 | 1.212460 | 10 | 0 | 0 |
| base | validation | gt_10m | 571 | 0.000000 | 0.558205 | 0.520800 | 0.934409 | 0 | 0 | 0 |
| base | validation | lt_1m | 423 | 0.000000 | 0.804773 | 1.069342 | 3.093418 | 53 | 8 | 1 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | validation | 1m_3m | 837 | 0.603345 | 0.323713 | 0.533013 | 1.725541 | 28 | 2 | 0 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | validation | 3m_10m | 744 | 0.537634 | 0.327666 | 0.420470 | 1.090563 | 6 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | validation | gt_10m | 571 | 0.739054 | 0.571693 | 0.527001 | 0.925313 | 0 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | validation | lt_1m | 423 | 0.782506 | 0.599405 | 0.930780 | 2.868305 | 43 | 6 | 1 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | validation | 1m_3m | 837 | 0.602151 | 0.323713 | 0.532979 | 1.725541 | 28 | 2 | 0 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | validation | 3m_10m | 744 | 0.473118 | 0.327666 | 0.419744 | 1.090563 | 6 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | validation | gt_10m | 571 | 0.432574 | 0.567045 | 0.523421 | 0.925313 | 0 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | validation | lt_1m | 423 | 0.780142 | 0.599405 | 0.931058 | 2.868305 | 43 | 6 | 1 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | validation | 1m_3m | 837 | 0.603345 | 0.319069 | 0.533703 | 1.725541 | 28 | 1 | 0 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | validation | 3m_10m | 744 | 0.537634 | 0.327666 | 0.421063 | 1.090563 | 6 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | validation | gt_10m | 571 | 0.739054 | 0.571693 | 0.527318 | 0.925313 | 0 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | validation | lt_1m | 423 | 0.782506 | 0.599405 | 0.932331 | 2.868305 | 43 | 6 | 1 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | validation | 1m_3m | 837 | 0.602151 | 0.319069 | 0.533669 | 1.725541 | 28 | 1 | 0 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | validation | 3m_10m | 744 | 0.473118 | 0.327666 | 0.420336 | 1.090563 | 6 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | validation | gt_10m | 571 | 0.432574 | 0.567045 | 0.523738 | 0.925313 | 0 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | validation | lt_1m | 423 | 0.780142 | 0.599405 | 0.932609 | 2.868305 | 43 | 6 | 1 |
| resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p03 | validation | 1m_3m | 837 | 0.268817 | 0.339026 | 0.553848 | 1.784207 | 31 | 2 | 0 |
| resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p03 | validation | 3m_10m | 744 | 0.172043 | 0.328300 | 0.433699 | 1.208684 | 10 | 0 | 0 |
| resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p03 | validation | gt_10m | 571 | 0.099825 | 0.567045 | 0.522831 | 0.934409 | 0 | 0 | 0 |
| resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p03 | validation | lt_1m | 423 | 0.472813 | 0.671875 | 1.003745 | 3.093418 | 49 | 8 | 1 |
| resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p05 | validation | 1m_3m | 837 | 0.264038 | 0.339026 | 0.554119 | 1.784207 | 31 | 2 | 0 |
| resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p05 | validation | 3m_10m | 744 | 0.161290 | 0.327666 | 0.433601 | 1.208684 | 10 | 0 | 0 |
| resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p05 | validation | gt_10m | 571 | 0.085814 | 0.567045 | 0.522722 | 0.934409 | 0 | 0 | 0 |
| resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p05 | validation | lt_1m | 423 | 0.463357 | 0.671875 | 1.004836 | 3.093418 | 50 | 8 | 1 |
| resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p03 | validation | 1m_3m | 837 | 0.268817 | 0.331706 | 0.554482 | 1.784207 | 31 | 1 | 0 |
| resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p03 | validation | 3m_10m | 744 | 0.172043 | 0.328300 | 0.433843 | 1.208684 | 10 | 0 | 0 |
| resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p03 | validation | gt_10m | 571 | 0.099825 | 0.567045 | 0.523179 | 0.934409 | 0 | 0 | 0 |
| resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p03 | validation | lt_1m | 423 | 0.472813 | 0.671875 | 1.005069 | 3.093418 | 49 | 8 | 1 |
| resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p05 | validation | 1m_3m | 837 | 0.264038 | 0.331706 | 0.554752 | 1.784207 | 31 | 1 | 0 |
| resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p05 | validation | 3m_10m | 744 | 0.161290 | 0.327666 | 0.433744 | 1.208684 | 10 | 0 | 0 |
| resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p05 | validation | gt_10m | 571 | 0.085814 | 0.567045 | 0.523070 | 0.934409 | 0 | 0 | 0 |
| resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p05 | validation | lt_1m | 423 | 0.463357 | 0.671875 | 1.006160 | 3.093418 | 50 | 8 | 1 |