# Cold 유사 이웃 잔차 보정 검증

- 작성일: 2026-06-22T15:50:02
- 목적: 작가별 `search_delta_lookup[artist_key]` 대신, 유사 작품/유사 작가 메타 이웃의 out-of-fold 잔차로 마지막 보정을 할 수 있는지 검증한다.
- 조건: `artist_key`, 같은 작가 가격 이력, `artist_key` lookup 후처리, `search_*`, 외부 live 검색 미사용.
- 보정값 생성: train OOF residual만 reference로 사용. validation/test 실제 가격은 보정값 생성에 사용하지 않는다.

## 1. Validation 선택 후보
| candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 | APE_gt_10 | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| resid_artist_meta_k160_s1p0_cap0p18 | validation | 0.406839 | 0.577443 | 1.681279 | 0.809474 | 79 | 10 | 1 | artist_meta top_k=160 residual median, correction=clip(1.00*median, +/-0.18) |
| resid_artist_meta_k160_s1p0_cap0p25 | validation | 0.406396 | 0.578328 | 1.681279 | 0.809592 | 79 | 10 | 1 | artist_meta top_k=160 residual median, correction=clip(1.00*median, +/-0.25) |
| resid_artist_meta_k160_s1p0_cap0p1 | validation | 0.408328 | 0.579940 | 1.683768 | 0.809696 | 79 | 10 | 1 | artist_meta top_k=160 residual median, correction=clip(1.00*median, +/-0.10) |
| resid_artist_meta_k160_s0p75_cap0p18 | validation | 0.410675 | 0.582891 | 1.715611 | 0.808959 | 85 | 10 | 1 | artist_meta top_k=160 residual median, correction=clip(0.75*median, +/-0.18) |
| resid_artist_meta_k160_s0p75_cap0p25 | validation | 0.410420 | 0.584130 | 1.715611 | 0.809187 | 85 | 10 | 1 | artist_meta top_k=160 residual median, correction=clip(0.75*median, +/-0.25) |
| resid_artist_meta_k40_s1p0_cap0p1 | validation | 0.428532 | 0.584320 | 1.676580 | 0.813600 | 83 | 8 | 1 | artist_meta top_k=40 residual median, correction=clip(1.00*median, +/-0.10) |
| resid_artist_meta_k160_s0p75_cap0p1 | validation | 0.411694 | 0.584405 | 1.721143 | 0.809208 | 85 | 10 | 1 | artist_meta top_k=160 residual median, correction=clip(0.75*median, +/-0.10) |
| resid_artist_meta_k160_s1p0_cap0p05 | validation | 0.413712 | 0.585301 | 1.697037 | 0.810349 | 80 | 10 | 1 | artist_meta top_k=160 residual median, correction=clip(1.00*median, +/-0.05) |
| resid_artist_meta_k40_s1p0_cap0p05 | validation | 0.420457 | 0.587321 | 1.697037 | 0.812602 | 81 | 8 | 1 | artist_meta top_k=40 residual median, correction=clip(1.00*median, +/-0.05) |
| resid_artist_meta_k40_s1p0_cap0p18 | validation | 0.447648 | 0.588130 | 1.679392 | 0.815254 | 83 | 8 | 1 | artist_meta top_k=40 residual median, correction=clip(1.00*median, +/-0.18) |
| resid_artist_meta_k160_s0p75_cap0p05 | validation | 0.414254 | 0.588224 | 1.724315 | 0.809765 | 85 | 10 | 1 | artist_meta top_k=160 residual median, correction=clip(0.75*median, +/-0.05) |
| resid_artist_meta_k160_s0p5_cap0p18 | validation | 0.418594 | 0.589256 | 1.742379 | 0.808832 | 89 | 9 | 1 | artist_meta top_k=160 residual median, correction=clip(0.50*median, +/-0.18) |

## 2. Validation 선택 후보의 Test 결과
| candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 | APE_gt_10 | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| resid_artist_meta_k40_s1p0_cap0p1 | test | 0.479003 | 0.732797 | 2.350753 | 0.804109 | 200 | 30 | 7 | artist_meta top_k=40 residual median, correction=clip(1.00*median, +/-0.10) |
| resid_artist_meta_k160_s1p0_cap0p1 | test | 0.489143 | 0.744371 | 2.326036 | 0.808516 | 207 | 33 | 8 | artist_meta top_k=160 residual median, correction=clip(1.00*median, +/-0.10) |
| resid_artist_meta_k160_s0p75_cap0p18 | test | 0.487779 | 0.745813 | 2.342803 | 0.807354 | 208 | 33 | 8 | artist_meta top_k=160 residual median, correction=clip(0.75*median, +/-0.18) |
| resid_artist_meta_k160_s1p0_cap0p18 | test | 0.491927 | 0.746061 | 2.325709 | 0.809237 | 208 | 33 | 8 | artist_meta top_k=160 residual median, correction=clip(1.00*median, +/-0.18) |
| resid_artist_meta_k160_s0p75_cap0p25 | test | 0.487779 | 0.746069 | 2.342803 | 0.807440 | 208 | 33 | 8 | artist_meta top_k=160 residual median, correction=clip(0.75*median, +/-0.25) |
| base_similarity_k160_q50 | test | 0.481850 | 0.746296 | 2.398009 | 0.802895 | 212 | 35 | 8 | user_meta + artwork similarity k160 q50 |
| resid_artist_meta_k160_s1p0_cap0p25 | test | 0.492494 | 0.746921 | 2.325709 | 0.809538 | 208 | 33 | 8 | artist_meta top_k=160 residual median, correction=clip(1.00*median, +/-0.25) |

## 3. Test 상위 후보 참고
| candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 | APE_gt_10 | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| resid_artist_meta_k40_s1p0_cap0p1 | test | 0.479003 | 0.732797 | 2.350753 | 0.804109 | 200 | 30 | 7 | artist_meta top_k=40 residual median, correction=clip(1.00*median, +/-0.10) |
| resid_artist_meta_k40_s1p0_cap0p05 | test | 0.481746 | 0.733425 | 2.323164 | 0.803706 | 200 | 30 | 7 | artist_meta top_k=40 residual median, correction=clip(1.00*median, +/-0.05) |
| resid_artist_meta_k40_s0p75_cap0p05 | test | 0.481939 | 0.734651 | 2.323164 | 0.803086 | 201 | 30 | 7 | artist_meta top_k=40 residual median, correction=clip(0.75*median, +/-0.05) |
| resid_artist_meta_k40_s0p75_cap0p1 | test | 0.476805 | 0.737167 | 2.392815 | 0.804118 | 206 | 30 | 7 | artist_meta top_k=40 residual median, correction=clip(0.75*median, +/-0.10) |
| resid_artist_meta_k320_s1p0_cap0p05 | test | 0.479063 | 0.738267 | 2.358539 | 0.805943 | 205 | 33 | 7 | artist_meta top_k=320 residual median, correction=clip(1.00*median, +/-0.05) |
| resid_artist_meta_k40_s0p5_cap0p05 | test | 0.481077 | 0.738314 | 2.323164 | 0.802710 | 208 | 32 | 7 | artist_meta top_k=40 residual median, correction=clip(0.50*median, +/-0.05) |
| resid_artist_meta_k320_s1p0_cap0p1 | test | 0.479850 | 0.739092 | 2.343352 | 0.806862 | 205 | 33 | 7 | artist_meta top_k=320 residual median, correction=clip(1.00*median, +/-0.10) |
| resid_artist_meta_k320_s1p0_cap0p18 | test | 0.479850 | 0.739255 | 2.357916 | 0.807068 | 205 | 33 | 7 | artist_meta top_k=320 residual median, correction=clip(1.00*median, +/-0.18) |
| resid_artist_meta_k320_s1p0_cap0p25 | test | 0.479850 | 0.739255 | 2.357916 | 0.807068 | 205 | 33 | 7 | artist_meta top_k=320 residual median, correction=clip(1.00*median, +/-0.25) |
| resid_artist_meta_k320_s0p75_cap0p05 | test | 0.478101 | 0.739956 | 2.361226 | 0.805279 | 206 | 33 | 7 | artist_meta top_k=320 residual median, correction=clip(0.75*median, +/-0.05) |
| resid_artist_meta_k40_s1p0_cap0p18 | test | 0.483924 | 0.740064 | 2.350344 | 0.807953 | 203 | 30 | 7 | artist_meta top_k=40 residual median, correction=clip(1.00*median, +/-0.18) |
| resid_artist_meta_k320_s0p75_cap0p18 | test | 0.479418 | 0.740598 | 2.361191 | 0.805775 | 206 | 33 | 7 | artist_meta top_k=320 residual median, correction=clip(0.75*median, +/-0.18) |
| resid_artist_meta_k320_s0p75_cap0p25 | test | 0.479418 | 0.740598 | 2.361191 | 0.805775 | 206 | 33 | 7 | artist_meta top_k=320 residual median, correction=clip(0.75*median, +/-0.25) |
| resid_artist_meta_k320_s0p75_cap0p1 | test | 0.479418 | 0.740598 | 2.361191 | 0.805782 | 206 | 33 | 7 | artist_meta top_k=320 residual median, correction=clip(0.75*median, +/-0.10) |
| resid_artist_meta_k160_s1p0_cap0p05 | test | 0.485908 | 0.740856 | 2.315907 | 0.807106 | 206 | 33 | 8 | artist_meta top_k=160 residual median, correction=clip(1.00*median, +/-0.05) |
| resid_artist_meta_k40_s0p5_cap0p1 | test | 0.478741 | 0.741310 | 2.403089 | 0.804195 | 213 | 32 | 7 | artist_meta top_k=40 residual median, correction=clip(0.50*median, +/-0.10) |

## 4. Paired bootstrap vs base
| split | candidate_a | candidate_b | n | n_boot | delta_MdAPE_a_minus_b_mean | delta_MAPE_a_minus_b_mean | delta_p95_APE_a_minus_b_mean | p_delta_MdAPE_a_minus_b_lt_0 | p_delta_MAPE_a_minus_b_lt_0 | p_delta_p95_APE_a_minus_b_lt_0 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | resid_artist_meta_k160_s1p0_cap0p18 | base_similarity_k160_q50 | 2575 | 800 | -0.018124 | -0.029274 | -0.128098 | 1.000000 | 1.000000 | 1.000000 |
| validation | resid_artist_meta_k160_s1p0_cap0p25 | base_similarity_k160_q50 | 2575 | 800 | -0.019164 | -0.028391 | -0.129064 | 1.000000 | 1.000000 | 1.000000 |
| validation | resid_artist_meta_k160_s1p0_cap0p1 | base_similarity_k160_q50 | 2575 | 800 | -0.016578 | -0.026780 | -0.123982 | 0.998750 | 1.000000 | 1.000000 |
| validation | resid_artist_meta_k160_s0p75_cap0p18 | base_similarity_k160_q50 | 2575 | 800 | -0.015477 | -0.023825 | -0.098414 | 0.998750 | 1.000000 | 1.000000 |
| validation | resid_artist_meta_k160_s0p75_cap0p25 | base_similarity_k160_q50 | 2575 | 800 | -0.016146 | -0.022588 | -0.098652 | 0.998750 | 1.000000 | 1.000000 |
| validation | resid_artist_meta_k40_s1p0_cap0p1 | base_similarity_k160_q50 | 2575 | 800 | 0.003238 | -0.022467 | -0.126693 | 0.321250 | 1.000000 | 1.000000 |
| test | resid_artist_meta_k160_s1p0_cap0p18 | base_similarity_k160_q50 | 3000 | 800 | 0.009273 | -0.000195 | -0.040858 | 0.033750 | 0.540000 | 0.805000 |
| test | resid_artist_meta_k160_s1p0_cap0p25 | base_similarity_k160_q50 | 3000 | 800 | 0.010535 | 0.000671 | -0.041610 | 0.020000 | 0.381250 | 0.813750 |
| test | resid_artist_meta_k160_s1p0_cap0p1 | base_similarity_k160_q50 | 3000 | 800 | 0.008370 | -0.001897 | -0.042413 | 0.042500 | 0.850000 | 0.810000 |
| test | resid_artist_meta_k160_s0p75_cap0p18 | base_similarity_k160_q50 | 3000 | 800 | 0.006681 | -0.000449 | -0.027831 | 0.047500 | 0.611250 | 0.781250 |
| test | resid_artist_meta_k160_s0p75_cap0p25 | base_similarity_k160_q50 | 3000 | 800 | 0.006823 | -0.000191 | -0.027831 | 0.037500 | 0.542500 | 0.781250 |
| test | resid_artist_meta_k40_s1p0_cap0p1 | base_similarity_k160_q50 | 3000 | 800 | -0.000538 | -0.013447 | -0.038024 | 0.547500 | 1.000000 | 0.782500 |

## 5. 가격대별 진단
| candidate | split | segment | n | mean_correction_log | MdAPE | MAPE | p95_APE | APE_gt_2 | APE_gt_5 | APE_gt_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base_similarity_k160_q50 | test | 1m_3m | 948 | nan | 0.414611 | 0.727543 | 2.301306 | 64 | 11 | 3 |
| base_similarity_k160_q50 | test | 3m_10m | 980 | nan | 0.420003 | 0.519689 | 1.447841 | 30 | 2 | 0 |
| base_similarity_k160_q50 | test | gt_10m | 496 | nan | 0.495163 | 0.494618 | 0.909020 | 0 | 0 | 0 |
| base_similarity_k160_q50 | test | lt_1m | 576 | nan | 0.841231 | 1.379428 | 3.928765 | 118 | 22 | 5 |
| resid_artist_meta_k160_s0p75_cap0p18 | test | 1m_3m | 948 | -0.003851 | 0.434378 | 0.728711 | 2.267666 | 67 | 10 | 3 |
| resid_artist_meta_k160_s0p75_cap0p18 | test | 3m_10m | 980 | -0.007857 | 0.421131 | 0.516428 | 1.383479 | 25 | 2 | 0 |
| resid_artist_meta_k160_s0p75_cap0p18 | test | gt_10m | 496 | -0.017161 | 0.494641 | 0.498703 | 0.912177 | 0 | 0 | 0 |
| resid_artist_meta_k160_s0p75_cap0p18 | test | lt_1m | 576 | -0.001559 | 0.792414 | 1.377020 | 3.961061 | 116 | 21 | 5 |
| resid_artist_meta_k160_s0p75_cap0p25 | test | 1m_3m | 948 | -0.003612 | 0.434510 | 0.728838 | 2.267666 | 67 | 10 | 3 |
| resid_artist_meta_k160_s0p75_cap0p25 | test | 3m_10m | 980 | -0.007375 | 0.421131 | 0.517077 | 1.383479 | 25 | 2 | 0 |
| resid_artist_meta_k160_s0p75_cap0p25 | test | gt_10m | 496 | -0.017161 | 0.494641 | 0.498703 | 0.912177 | 0 | 0 | 0 |
| resid_artist_meta_k160_s0p75_cap0p25 | test | lt_1m | 576 | -0.001549 | 0.792414 | 1.377044 | 3.961061 | 116 | 21 | 5 |
| resid_artist_meta_k160_s1p0_cap0p1 | test | 1m_3m | 948 | -0.007365 | 0.433848 | 0.727785 | 2.235589 | 68 | 10 | 3 |
| resid_artist_meta_k160_s1p0_cap0p1 | test | 3m_10m | 980 | -0.013877 | 0.421669 | 0.512062 | 1.362403 | 23 | 2 | 0 |
| resid_artist_meta_k160_s1p0_cap0p1 | test | gt_10m | 496 | -0.022967 | 0.496804 | 0.499859 | 0.913439 | 0 | 0 | 0 |
| resid_artist_meta_k160_s1p0_cap0p1 | test | lt_1m | 576 | -0.002722 | 0.770024 | 1.377467 | 4.020769 | 116 | 21 | 5 |
| resid_artist_meta_k160_s1p0_cap0p18 | test | 1m_3m | 948 | -0.005932 | 0.435893 | 0.729804 | 2.238772 | 68 | 10 | 3 |
| resid_artist_meta_k160_s1p0_cap0p18 | test | 3m_10m | 980 | -0.011872 | 0.422674 | 0.514572 | 1.362403 | 23 | 2 | 0 |
| resid_artist_meta_k160_s1p0_cap0p18 | test | gt_10m | 496 | -0.022913 | 0.496804 | 0.500129 | 0.913439 | 0 | 0 | 0 |
| resid_artist_meta_k160_s1p0_cap0p18 | test | lt_1m | 576 | -0.002082 | 0.770024 | 1.378447 | 3.961826 | 117 | 21 | 5 |
| resid_artist_meta_k160_s1p0_cap0p25 | test | 1m_3m | 948 | -0.005019 | 0.438059 | 0.730149 | 2.238772 | 68 | 10 | 3 |
| resid_artist_meta_k160_s1p0_cap0p25 | test | 3m_10m | 980 | -0.010241 | 0.423618 | 0.516979 | 1.362403 | 23 | 2 | 0 |
| resid_artist_meta_k160_s1p0_cap0p25 | test | gt_10m | 496 | -0.022881 | 0.496804 | 0.500123 | 0.913439 | 0 | 0 | 0 |
| resid_artist_meta_k160_s1p0_cap0p25 | test | lt_1m | 576 | -0.002066 | 0.770024 | 1.378268 | 3.961826 | 117 | 21 | 5 |
| resid_artist_meta_k40_s1p0_cap0p1 | test | 1m_3m | 948 | -0.009617 | 0.441577 | 0.723523 | 2.298972 | 62 | 10 | 2 |
| resid_artist_meta_k40_s1p0_cap0p1 | test | 3m_10m | 980 | -0.010675 | 0.423498 | 0.511957 | 1.320076 | 23 | 2 | 0 |
| resid_artist_meta_k40_s1p0_cap0p1 | test | gt_10m | 496 | -0.020895 | 0.500346 | 0.498067 | 0.914410 | 0 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p1 | test | lt_1m | 576 | -0.018203 | 0.758941 | 1.325926 | 4.063225 | 115 | 18 | 5 |
| base_similarity_k160_q50 | validation | 1m_3m | 837 | nan | 0.357073 | 0.581180 | 1.839279 | 34 | 2 | 0 |
| base_similarity_k160_q50 | validation | 3m_10m | 744 | nan | 0.328934 | 0.438459 | 1.212460 | 10 | 0 | 0 |
| base_similarity_k160_q50 | validation | gt_10m | 571 | nan | 0.558205 | 0.520800 | 0.934409 | 0 | 0 | 0 |
| base_similarity_k160_q50 | validation | lt_1m | 423 | nan | 0.804773 | 1.069342 | 3.093418 | 53 | 8 | 1 |
| resid_artist_meta_k160_s0p75_cap0p18 | validation | 1m_3m | 837 | -0.035340 | 0.330333 | 0.550433 | 1.804098 | 29 | 2 | 0 |
| resid_artist_meta_k160_s0p75_cap0p18 | validation | 3m_10m | 744 | -0.022555 | 0.335324 | 0.428837 | 1.166803 | 9 | 0 | 0 |
| resid_artist_meta_k160_s0p75_cap0p18 | validation | gt_10m | 571 | -0.016831 | 0.561510 | 0.522172 | 0.935407 | 0 | 0 | 0 |
| resid_artist_meta_k160_s0p75_cap0p18 | validation | lt_1m | 423 | -0.052003 | 0.714807 | 1.000038 | 2.948307 | 47 | 8 | 1 |
| resid_artist_meta_k160_s0p75_cap0p25 | validation | 1m_3m | 837 | -0.040228 | 0.331402 | 0.552418 | 1.804098 | 29 | 2 | 0 |
| resid_artist_meta_k160_s0p75_cap0p25 | validation | 3m_10m | 744 | -0.023242 | 0.335324 | 0.429333 | 1.166803 | 9 | 0 | 0 |
| resid_artist_meta_k160_s0p75_cap0p25 | validation | gt_10m | 571 | -0.016831 | 0.561510 | 0.522172 | 0.935407 | 0 | 0 | 0 |
| resid_artist_meta_k160_s0p75_cap0p25 | validation | lt_1m | 423 | -0.056802 | 0.714807 | 1.002784 | 2.948307 | 47 | 8 | 1 |
| resid_artist_meta_k160_s1p0_cap0p1 | validation | 1m_3m | 837 | -0.034324 | 0.334184 | 0.550227 | 1.796521 | 29 | 2 | 0 |
| resid_artist_meta_k160_s1p0_cap0p1 | validation | 3m_10m | 744 | -0.026671 | 0.335415 | 0.426215 | 1.127760 | 6 | 0 | 0 |
| resid_artist_meta_k160_s1p0_cap0p1 | validation | gt_10m | 571 | -0.021698 | 0.564245 | 0.523208 | 0.936078 | 0 | 0 | 0 |
| resid_artist_meta_k160_s1p0_cap0p1 | validation | lt_1m | 423 | -0.056147 | 0.685697 | 0.985700 | 2.906493 | 44 | 8 | 1 |
| resid_artist_meta_k160_s1p0_cap0p18 | validation | 1m_3m | 837 | -0.042401 | 0.333244 | 0.545011 | 1.796521 | 29 | 2 | 0 |
| resid_artist_meta_k160_s1p0_cap0p18 | validation | 3m_10m | 744 | -0.029409 | 0.329504 | 0.426290 | 1.127760 | 6 | 0 | 0 |
| resid_artist_meta_k160_s1p0_cap0p18 | validation | gt_10m | 571 | -0.022510 | 0.568450 | 0.523189 | 0.936078 | 0 | 0 | 0 |
| resid_artist_meta_k160_s1p0_cap0p18 | validation | lt_1m | 423 | -0.064889 | 0.685697 | 0.980715 | 2.906493 | 44 | 8 | 1 |
| resid_artist_meta_k160_s1p0_cap0p25 | validation | 1m_3m | 837 | -0.047884 | 0.326710 | 0.546156 | 1.796521 | 29 | 2 | 0 |
| resid_artist_meta_k160_s1p0_cap0p25 | validation | 3m_10m | 744 | -0.030180 | 0.329504 | 0.426648 | 1.127760 | 6 | 0 | 0 |
| resid_artist_meta_k160_s1p0_cap0p25 | validation | gt_10m | 571 | -0.022442 | 0.568450 | 0.523133 | 0.936078 | 0 | 0 | 0 |
| resid_artist_meta_k160_s1p0_cap0p25 | validation | lt_1m | 423 | -0.070023 | 0.685697 | 0.983279 | 2.906493 | 44 | 8 | 1 |
| resid_artist_meta_k40_s1p0_cap0p1 | validation | 1m_3m | 837 | -0.027607 | 0.332618 | 0.550715 | 1.733404 | 30 | 2 | 0 |
| resid_artist_meta_k40_s1p0_cap0p1 | validation | 3m_10m | 744 | -0.005072 | 0.377510 | 0.445978 | 1.090789 | 6 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p1 | validation | gt_10m | 571 | -0.026538 | 0.561805 | 0.523811 | 0.924379 | 0 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p1 | validation | lt_1m | 423 | -0.047331 | 0.646757 | 0.975823 | 2.868305 | 47 | 6 | 1 |