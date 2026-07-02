# Cold 유사 이웃 잔차 보정 규칙 라우터

- 작성일: 2026-06-22T15:50:51
- 목적: CSIM24 유사 이웃 잔차 보정을 전체 적용하지 않고, 추론 시점 신호가 맞는 row에만 적용한다.
- 라우터 입력: 기본 예측가, 보정 후보 예측가, 보정 로그값의 크기/방향.
- 금지: 실제 가격, `artist_key`, 같은 작가 가격 이력, 검색/lookup 후처리.

## 1. Validation 선택 후보
| candidate | source_candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 | APE_gt_10 | selected_rate | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | resid_artist_meta_k40_s1p0_cap0p18 | validation | 0.405434 | 0.563535 | 1.648824 | 0.807140 | 77 | 8 | 1 | 0.556505 | 하향 보정 0.05 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | resid_artist_meta_k40_s1p0_cap0p25 | validation | 0.405266 | 0.564256 | 1.648824 | 0.807453 | 77 | 7 | 1 | 0.556505 | 하향 보정 0.05 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | resid_artist_meta_k40_s1p0_cap0p18 | validation | 0.405582 | 0.564505 | 1.648824 | 0.811121 | 77 | 8 | 1 | 0.643883 | 하향 보정 0.03 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | resid_artist_meta_k40_s1p0_cap0p25 | validation | 0.405492 | 0.565225 | 1.648824 | 0.811433 | 77 | 7 | 1 | 0.643883 | 하향 보정 0.03 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s1p0_cap0p18__route_base_lt_neg_800w_abs0p0 | resid_artist_meta_k40_s1p0_cap0p18 | validation | 0.405266 | 0.569096 | 1.675375 | 0.810338 | 82 | 8 | 1 | 0.574369 | 기본 예측가 800만원 미만이고 하향 보정 절대값 0.00 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s1p0_cap0p1__route_neg_corr_ge_0p05 | resid_artist_meta_k40_s1p0_cap0p1 | validation | 0.406234 | 0.569325 | 1.671233 | 0.807847 | 77 | 8 | 1 | 0.556505 | 하향 보정 0.05 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s1p0_cap0p18__route_base_lt_neg_800w_abs0p05 | resid_artist_meta_k40_s1p0_cap0p18 | validation | 0.404400 | 0.569463 | 1.675375 | 0.806778 | 82 | 8 | 1 | 0.448932 | 기본 예측가 800만원 미만이고 하향 보정 절대값 0.05 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s1p0_cap0p25__route_base_lt_neg_800w_abs0p0 | resid_artist_meta_k40_s1p0_cap0p25 | validation | 0.404411 | 0.569835 | 1.675375 | 0.810641 | 82 | 7 | 1 | 0.574369 | 기본 예측가 800만원 미만이고 하향 보정 절대값 0.00 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s1p0_cap0p25__route_base_lt_neg_800w_abs0p05 | resid_artist_meta_k40_s1p0_cap0p25 | validation | 0.403316 | 0.570202 | 1.675375 | 0.807083 | 82 | 7 | 1 | 0.448932 | 기본 예측가 800만원 미만이고 하향 보정 절대값 0.05 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s1p0_cap0p1__route_neg_corr_ge_0p03 | resid_artist_meta_k40_s1p0_cap0p1 | validation | 0.407902 | 0.570295 | 1.668550 | 0.811824 | 77 | 8 | 1 | 0.643883 | 하향 보정 0.03 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s1p0_cap0p18__route_base_lt_neg_800w_abs0p03 | resid_artist_meta_k40_s1p0_cap0p18 | validation | 0.404476 | 0.570414 | 1.675375 | 0.810740 | 82 | 8 | 1 | 0.535534 | 기본 예측가 800만원 미만이고 하향 보정 절대값 0.03 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s1p0_cap0p25__route_base_lt_neg_800w_abs0p03 | resid_artist_meta_k40_s1p0_cap0p25 | validation | 0.403786 | 0.571153 | 1.675375 | 0.811043 | 82 | 7 | 1 | 0.535534 | 기본 예측가 800만원 미만이고 하향 보정 절대값 0.03 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k160_s1p0_cap0p18__route_neg_corr_ge_0p03 | resid_artist_meta_k160_s1p0_cap0p18 | validation | 0.403893 | 0.571412 | 1.676127 | 0.807598 | 79 | 9 | 1 | 0.568544 | 하향 보정 0.03 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s0p75_cap0p18__route_neg_corr_ge_0p03 | resid_artist_meta_k40_s0p75_cap0p18 | validation | 0.408393 | 0.571767 | 1.680541 | 0.807144 | 84 | 8 | 1 | 0.558058 | 하향 보정 0.03 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k160_s1p0_cap0p18__route_neg_corr_ge_0p05 | resid_artist_meta_k160_s1p0_cap0p18 | validation | 0.404400 | 0.571846 | 1.677894 | 0.807405 | 79 | 9 | 1 | 0.552621 | 하향 보정 0.05 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k160_s1p0_cap0p25__route_neg_corr_ge_0p03 | resid_artist_meta_k160_s1p0_cap0p25 | validation | 0.403786 | 0.572302 | 1.676127 | 0.807723 | 79 | 9 | 1 | 0.568544 | 하향 보정 0.03 log 이상이면 보정 후보 적용 |

## 2. Validation 선택 후보의 Test 결과
| candidate | source_candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 | APE_gt_10 | selected_rate | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | resid_artist_meta_k40_s1p0_cap0p25 | test | 0.472314 | 0.706767 | 2.161091 | 0.806398 | 184 | 30 | 7 | 0.581333 | 하향 보정 0.03 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | resid_artist_meta_k40_s1p0_cap0p25 | test | 0.475254 | 0.707336 | 2.161091 | 0.805736 | 184 | 30 | 7 | 0.557667 | 하향 보정 0.05 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | resid_artist_meta_k40_s1p0_cap0p18 | test | 0.469877 | 0.708626 | 2.169832 | 0.804789 | 186 | 30 | 7 | 0.581333 | 하향 보정 0.03 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | resid_artist_meta_k40_s1p0_cap0p18 | test | 0.472052 | 0.709195 | 2.169832 | 0.804126 | 186 | 30 | 7 | 0.557667 | 하향 보정 0.05 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s1p0_cap0p1__route_neg_corr_ge_0p05 | resid_artist_meta_k40_s1p0_cap0p1 | test | 0.474671 | 0.713238 | 2.201186 | 0.802392 | 189 | 30 | 7 | 0.557667 | 하향 보정 0.05 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s1p0_cap0p25__route_base_lt_neg_800w_abs0p0 | resid_artist_meta_k40_s1p0_cap0p25 | test | 0.477169 | 0.713501 | 2.190069 | 0.805480 | 195 | 31 | 8 | 0.484333 | 기본 예측가 800만원 미만이고 하향 보정 절대값 0.00 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s1p0_cap0p18__route_base_lt_neg_800w_abs0p0 | resid_artist_meta_k40_s1p0_cap0p18 | test | 0.477169 | 0.715388 | 2.230026 | 0.804311 | 197 | 31 | 8 | 0.484333 | 기본 예측가 800만원 미만이고 하향 보정 절대값 0.00 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s1p0_cap0p18__route_base_lt_neg_800w_abs0p05 | resid_artist_meta_k40_s1p0_cap0p18 | test | 0.477320 | 0.715965 | 2.230026 | 0.803597 | 197 | 31 | 8 | 0.436667 | 기본 예측가 800만원 미만이고 하향 보정 절대값 0.05 log 이상이면 보정 후보 적용 |
| base | base_similarity_k160_q50 | test | 0.481850 | 0.746296 | 2.398009 | 0.802895 | 212 | 35 | 8 | 0.000000 | 항상 base similarity k160 |

## 3. Test 상위 후보 참고
| candidate | source_candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 | APE_gt_10 | selected_rate | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | resid_artist_meta_k40_s1p0_cap0p25 | test | 0.472314 | 0.706767 | 2.161091 | 0.806398 | 184 | 30 | 7 | 0.581333 | 하향 보정 0.03 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | resid_artist_meta_k40_s1p0_cap0p25 | test | 0.475254 | 0.707336 | 2.161091 | 0.805736 | 184 | 30 | 7 | 0.557667 | 하향 보정 0.05 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | resid_artist_meta_k40_s1p0_cap0p18 | test | 0.469877 | 0.708626 | 2.169832 | 0.804789 | 186 | 30 | 7 | 0.581333 | 하향 보정 0.03 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | resid_artist_meta_k40_s1p0_cap0p18 | test | 0.472052 | 0.709195 | 2.169832 | 0.804126 | 186 | 30 | 7 | 0.557667 | 하향 보정 0.05 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s1p0_cap0p1__route_neg_corr_ge_0p03 | resid_artist_meta_k40_s1p0_cap0p1 | test | 0.472203 | 0.712669 | 2.201186 | 0.803057 | 189 | 30 | 7 | 0.581333 | 하향 보정 0.03 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s1p0_cap0p1__route_neg_corr_ge_0p05 | resid_artist_meta_k40_s1p0_cap0p1 | test | 0.474671 | 0.713238 | 2.201186 | 0.802392 | 189 | 30 | 7 | 0.557667 | 하향 보정 0.05 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s1p0_cap0p25__route_base_lt_neg_800w_abs0p0 | resid_artist_meta_k40_s1p0_cap0p25 | test | 0.477169 | 0.713501 | 2.190069 | 0.805480 | 195 | 31 | 8 | 0.484333 | 기본 예측가 800만원 미만이고 하향 보정 절대값 0.00 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s1p0_cap0p25__route_base_lt_neg_800w_abs0p03 | resid_artist_meta_k40_s1p0_cap0p25 | test | 0.477139 | 0.713636 | 2.190069 | 0.805443 | 195 | 31 | 8 | 0.457333 | 기본 예측가 800만원 미만이고 하향 보정 절대값 0.03 log 이상이면 보정 후보 적용 |
| resid_artwork_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | resid_artwork_artist_meta_k40_s1p0_cap0p25 | test | 0.478812 | 0.713848 | 2.161091 | 0.809905 | 187 | 30 | 6 | 0.395000 | 하향 보정 0.03 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s1p0_cap0p25__route_base_lt_neg_800w_abs0p05 | resid_artist_meta_k40_s1p0_cap0p25 | test | 0.477320 | 0.714078 | 2.190069 | 0.804768 | 195 | 31 | 8 | 0.436667 | 기본 예측가 800만원 미만이고 하향 보정 절대값 0.05 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s0p75_cap0p25__route_neg_corr_ge_0p03 | resid_artist_meta_k40_s0p75_cap0p25 | test | 0.474795 | 0.714808 | 2.175553 | 0.805887 | 193 | 30 | 7 | 0.568333 | 하향 보정 0.03 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s1p0_cap0p18__route_base_lt_neg_800w_abs0p0 | resid_artist_meta_k40_s1p0_cap0p18 | test | 0.477169 | 0.715388 | 2.230026 | 0.804311 | 197 | 31 | 8 | 0.484333 | 기본 예측가 800만원 미만이고 하향 보정 절대값 0.00 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s1p0_cap0p18__route_base_lt_neg_800w_abs0p03 | resid_artist_meta_k40_s1p0_cap0p18 | test | 0.476763 | 0.715523 | 2.230026 | 0.804274 | 197 | 31 | 8 | 0.457333 | 기본 예측가 800만원 미만이고 하향 보정 절대값 0.03 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s1p0_cap0p18__route_base_lt_neg_800w_abs0p05 | resid_artist_meta_k40_s1p0_cap0p18 | test | 0.477320 | 0.715965 | 2.230026 | 0.803597 | 197 | 31 | 8 | 0.436667 | 기본 예측가 800만원 미만이고 하향 보정 절대값 0.05 log 이상이면 보정 후보 적용 |
| resid_artwork_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | resid_artwork_artist_meta_k40_s1p0_cap0p25 | test | 0.482551 | 0.716012 | 2.175553 | 0.809748 | 189 | 30 | 6 | 0.326000 | 하향 보정 0.05 log 이상이면 보정 후보 적용 |
| resid_artist_meta_k40_s0p75_cap0p18__route_neg_corr_ge_0p03 | resid_artist_meta_k40_s0p75_cap0p18 | test | 0.473367 | 0.716168 | 2.229543 | 0.804707 | 193 | 30 | 7 | 0.568333 | 하향 보정 0.03 log 이상이면 보정 후보 적용 |

## 4. Paired bootstrap vs base
| split | candidate_a | candidate_b | n | n_boot | delta_MdAPE_a_minus_b_mean | delta_MAPE_a_minus_b_mean | delta_p95_APE_a_minus_b_mean | p_delta_MdAPE_a_minus_b_lt_0 | p_delta_MAPE_a_minus_b_lt_0 | p_delta_p95_APE_a_minus_b_lt_0 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | base | 2575 | 800 | -0.019731 | -0.043172 | -0.164226 | 1.000000 | 1.000000 | 1.000000 |
| validation | resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | base | 2575 | 800 | -0.020120 | -0.042448 | -0.167187 | 1.000000 | 1.000000 | 1.000000 |
| validation | resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | base | 2575 | 800 | -0.019092 | -0.042204 | -0.165997 | 1.000000 | 1.000000 | 1.000000 |
| validation | resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | base | 2575 | 800 | -0.019447 | -0.041479 | -0.168958 | 0.998750 | 1.000000 | 1.000000 |
| validation | resid_artist_meta_k40_s1p0_cap0p18__route_base_lt_neg_800w_abs0p0 | base | 2575 | 800 | -0.019719 | -0.037630 | -0.140681 | 1.000000 | 1.000000 | 1.000000 |
| validation | resid_artist_meta_k40_s1p0_cap0p1__route_neg_corr_ge_0p05 | base | 2575 | 800 | -0.018981 | -0.037397 | -0.142126 | 1.000000 | 1.000000 | 1.000000 |
| validation | resid_artist_meta_k40_s1p0_cap0p18__route_base_lt_neg_800w_abs0p05 | base | 2575 | 800 | -0.020505 | -0.037261 | -0.129433 | 1.000000 | 1.000000 | 1.000000 |
| validation | resid_artist_meta_k40_s1p0_cap0p25__route_base_lt_neg_800w_abs0p0 | base | 2575 | 800 | -0.020523 | -0.036892 | -0.140774 | 1.000000 | 1.000000 | 1.000000 |
| test | resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | base | 3000 | 800 | -0.007451 | -0.037050 | -0.182347 | 0.966250 | 1.000000 | 1.000000 |
| test | resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | base | 3000 | 800 | -0.006241 | -0.038918 | -0.206259 | 0.936250 | 1.000000 | 1.000000 |
| test | resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | base | 3000 | 800 | -0.008848 | -0.037624 | -0.182347 | 0.983750 | 1.000000 | 1.000000 |
| test | resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | base | 3000 | 800 | -0.007573 | -0.039491 | -0.206259 | 0.965000 | 1.000000 | 1.000000 |
| test | resid_artist_meta_k40_s1p0_cap0p18__route_base_lt_neg_800w_abs0p0 | base | 3000 | 800 | -0.004137 | -0.030833 | -0.141375 | 0.885000 | 1.000000 | 0.998750 |
| test | resid_artist_meta_k40_s1p0_cap0p1__route_neg_corr_ge_0p05 | base | 3000 | 800 | -0.005818 | -0.032992 | -0.163195 | 0.943750 | 1.000000 | 1.000000 |
| test | resid_artist_meta_k40_s1p0_cap0p18__route_base_lt_neg_800w_abs0p05 | base | 3000 | 800 | -0.003278 | -0.030253 | -0.141265 | 0.836250 | 1.000000 | 0.998750 |
| test | resid_artist_meta_k40_s1p0_cap0p25__route_base_lt_neg_800w_abs0p0 | base | 3000 | 800 | -0.003029 | -0.032730 | -0.171149 | 0.808750 | 1.000000 | 0.998750 |

## 5. 가격대별 진단
| candidate | split | segment | n | selected_rate | MdAPE | MAPE | p95_APE | APE_gt_2 | APE_gt_5 | APE_gt_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base | test | 1m_3m | 948 | 0.000000 | 0.414611 | 0.727543 | 2.301306 | 64 | 11 | 3 |
| base | test | 3m_10m | 980 | 0.000000 | 0.420003 | 0.519689 | 1.447841 | 30 | 2 | 0 |
| base | test | gt_10m | 496 | 0.000000 | 0.495163 | 0.494618 | 0.909020 | 0 | 0 | 0 |
| base | test | lt_1m | 576 | 0.000000 | 0.841231 | 1.379428 | 3.928765 | 118 | 22 | 5 |
| resid_artist_meta_k40_s1p0_cap0p18__route_base_lt_neg_800w_abs0p0 | test | 1m_3m | 948 | 0.561181 | 0.420074 | 0.690521 | 2.169172 | 56 | 11 | 3 |
| resid_artist_meta_k40_s1p0_cap0p18__route_base_lt_neg_800w_abs0p0 | test | 3m_10m | 980 | 0.439796 | 0.431433 | 0.521145 | 1.447841 | 30 | 2 | 0 |
| resid_artist_meta_k40_s1p0_cap0p18__route_base_lt_neg_800w_abs0p0 | test | gt_10m | 496 | 0.258065 | 0.512898 | 0.499997 | 0.917744 | 0 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p18__route_base_lt_neg_800w_abs0p0 | test | lt_1m | 576 | 0.628472 | 0.739975 | 1.272274 | 3.745833 | 111 | 18 | 5 |
| resid_artist_meta_k40_s1p0_cap0p18__route_base_lt_neg_800w_abs0p05 | test | 1m_3m | 948 | 0.505274 | 0.420074 | 0.691496 | 2.169172 | 56 | 11 | 3 |
| resid_artist_meta_k40_s1p0_cap0p18__route_base_lt_neg_800w_abs0p05 | test | 3m_10m | 980 | 0.385714 | 0.431619 | 0.521178 | 1.447841 | 30 | 2 | 0 |
| resid_artist_meta_k40_s1p0_cap0p18__route_base_lt_neg_800w_abs0p05 | test | gt_10m | 496 | 0.221774 | 0.512898 | 0.499779 | 0.917744 | 0 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p18__route_base_lt_neg_800w_abs0p05 | test | lt_1m | 576 | 0.595486 | 0.739975 | 1.273805 | 3.745833 | 111 | 18 | 5 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | test | 1m_3m | 948 | 0.541139 | 0.420074 | 0.685461 | 2.102299 | 55 | 10 | 2 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | test | 3m_10m | 980 | 0.559184 | 0.420240 | 0.502822 | 1.293536 | 20 | 2 | 0 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | test | gt_10m | 496 | 0.677419 | 0.512837 | 0.503988 | 0.917744 | 0 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | test | lt_1m | 576 | 0.602431 | 0.739975 | 1.273118 | 3.745833 | 111 | 18 | 5 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | test | 1m_3m | 948 | 0.517932 | 0.420074 | 0.686250 | 2.102299 | 55 | 10 | 2 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | test | 3m_10m | 980 | 0.533673 | 0.421034 | 0.503468 | 1.293536 | 20 | 2 | 0 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | test | gt_10m | 496 | 0.637097 | 0.512837 | 0.503849 | 0.917744 | 0 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | test | lt_1m | 576 | 0.595486 | 0.739975 | 1.273805 | 3.745833 | 111 | 18 | 5 |
| resid_artist_meta_k40_s1p0_cap0p1__route_neg_corr_ge_0p05 | test | 1m_3m | 948 | 0.517932 | 0.429298 | 0.691986 | 2.102299 | 55 | 10 | 2 |
| resid_artist_meta_k40_s1p0_cap0p1__route_neg_corr_ge_0p05 | test | 3m_10m | 980 | 0.533673 | 0.423106 | 0.503389 | 1.293536 | 21 | 2 | 0 |
| resid_artist_meta_k40_s1p0_cap0p1__route_neg_corr_ge_0p05 | test | gt_10m | 496 | 0.637097 | 0.511603 | 0.502254 | 0.911096 | 0 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p1__route_neg_corr_ge_0p05 | test | lt_1m | 576 | 0.595486 | 0.741010 | 1.286930 | 3.852615 | 113 | 18 | 5 |
| resid_artist_meta_k40_s1p0_cap0p25__route_base_lt_neg_800w_abs0p0 | test | 1m_3m | 948 | 0.561181 | 0.420074 | 0.688768 | 2.102299 | 56 | 11 | 3 |
| resid_artist_meta_k40_s1p0_cap0p25__route_base_lt_neg_800w_abs0p0 | test | 3m_10m | 980 | 0.439796 | 0.430485 | 0.521808 | 1.447841 | 30 | 2 | 0 |
| resid_artist_meta_k40_s1p0_cap0p25__route_base_lt_neg_800w_abs0p0 | test | gt_10m | 496 | 0.258065 | 0.512898 | 0.500296 | 0.922408 | 0 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p25__route_base_lt_neg_800w_abs0p0 | test | lt_1m | 576 | 0.628472 | 0.739975 | 1.263943 | 3.745833 | 109 | 18 | 5 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | test | 1m_3m | 948 | 0.541139 | 0.420074 | 0.683591 | 2.100471 | 55 | 10 | 2 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | test | 3m_10m | 980 | 0.559184 | 0.419859 | 0.503403 | 1.293536 | 20 | 2 | 0 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | test | gt_10m | 496 | 0.677419 | 0.512837 | 0.504848 | 0.922408 | 0 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | test | lt_1m | 576 | 0.602431 | 0.739975 | 1.264787 | 3.745833 | 109 | 18 | 5 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | test | 1m_3m | 948 | 0.517932 | 0.420074 | 0.684379 | 2.100471 | 55 | 10 | 2 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | test | 3m_10m | 980 | 0.533673 | 0.420240 | 0.504049 | 1.293536 | 20 | 2 | 0 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | test | gt_10m | 496 | 0.637097 | 0.512837 | 0.504710 | 0.922408 | 0 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | test | lt_1m | 576 | 0.595486 | 0.739975 | 1.265474 | 3.745833 | 109 | 18 | 5 |
| base | validation | 1m_3m | 837 | 0.000000 | 0.357073 | 0.581180 | 1.839279 | 34 | 2 | 0 |
| base | validation | 3m_10m | 744 | 0.000000 | 0.328934 | 0.438459 | 1.212460 | 10 | 0 | 0 |
| base | validation | gt_10m | 571 | 0.000000 | 0.558205 | 0.520800 | 0.934409 | 0 | 0 | 0 |
| base | validation | lt_1m | 423 | 0.000000 | 0.804773 | 1.069342 | 3.093418 | 53 | 8 | 1 |
| resid_artist_meta_k40_s1p0_cap0p18__route_base_lt_neg_800w_abs0p0 | validation | 1m_3m | 837 | 0.695341 | 0.324682 | 0.531412 | 1.716496 | 29 | 2 | 0 |
| resid_artist_meta_k40_s1p0_cap0p18__route_base_lt_neg_800w_abs0p0 | validation | 3m_10m | 744 | 0.404570 | 0.327666 | 0.438609 | 1.212460 | 10 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p18__route_base_lt_neg_800w_abs0p0 | validation | gt_10m | 571 | 0.457093 | 0.570687 | 0.526751 | 0.936182 | 0 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p18__route_base_lt_neg_800w_abs0p0 | validation | lt_1m | 423 | 0.791962 | 0.599405 | 0.930329 | 2.868305 | 43 | 6 | 1 |
| resid_artist_meta_k40_s1p0_cap0p18__route_base_lt_neg_800w_abs0p05 | validation | 1m_3m | 837 | 0.596177 | 0.323713 | 0.535320 | 1.770272 | 29 | 2 | 0 |
| resid_artist_meta_k40_s1p0_cap0p18__route_base_lt_neg_800w_abs0p05 | validation | 3m_10m | 744 | 0.323925 | 0.327666 | 0.437757 | 1.212460 | 10 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p18__route_base_lt_neg_800w_abs0p05 | validation | gt_10m | 571 | 0.150613 | 0.561976 | 0.523247 | 0.936182 | 0 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p18__route_base_lt_neg_800w_abs0p05 | validation | lt_1m | 423 | 0.780142 | 0.599405 | 0.931058 | 2.868305 | 43 | 6 | 1 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | validation | 1m_3m | 837 | 0.603345 | 0.323713 | 0.533013 | 1.725541 | 28 | 2 | 0 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | validation | 3m_10m | 744 | 0.537634 | 0.327666 | 0.420470 | 1.090563 | 6 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | validation | gt_10m | 571 | 0.739054 | 0.571693 | 0.527001 | 0.925313 | 0 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | validation | lt_1m | 423 | 0.782506 | 0.599405 | 0.930780 | 2.868305 | 43 | 6 | 1 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | validation | 1m_3m | 837 | 0.602151 | 0.323713 | 0.532979 | 1.725541 | 28 | 2 | 0 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | validation | 3m_10m | 744 | 0.473118 | 0.327666 | 0.419744 | 1.090563 | 6 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | validation | gt_10m | 571 | 0.432574 | 0.567045 | 0.523421 | 0.925313 | 0 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | validation | lt_1m | 423 | 0.780142 | 0.599405 | 0.931058 | 2.868305 | 43 | 6 | 1 |
| resid_artist_meta_k40_s1p0_cap0p1__route_neg_corr_ge_0p05 | validation | 1m_3m | 837 | 0.602151 | 0.325231 | 0.538017 | 1.769925 | 28 | 2 | 0 |
| resid_artist_meta_k40_s1p0_cap0p1__route_neg_corr_ge_0p05 | validation | 3m_10m | 744 | 0.473118 | 0.327666 | 0.420521 | 1.090563 | 6 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p1__route_neg_corr_ge_0p05 | validation | gt_10m | 571 | 0.432574 | 0.561082 | 0.522568 | 0.925313 | 0 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p1__route_neg_corr_ge_0p05 | validation | lt_1m | 423 | 0.780142 | 0.646757 | 0.956117 | 2.868305 | 43 | 6 | 1 |
| resid_artist_meta_k40_s1p0_cap0p25__route_base_lt_neg_800w_abs0p0 | validation | 1m_3m | 837 | 0.695341 | 0.323713 | 0.532314 | 1.716496 | 29 | 1 | 0 |
| resid_artist_meta_k40_s1p0_cap0p25__route_base_lt_neg_800w_abs0p0 | validation | 3m_10m | 744 | 0.404570 | 0.327666 | 0.439260 | 1.212460 | 10 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p25__route_base_lt_neg_800w_abs0p0 | validation | gt_10m | 571 | 0.457093 | 0.570687 | 0.526766 | 0.936182 | 0 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p25__route_base_lt_neg_800w_abs0p0 | validation | lt_1m | 423 | 0.791962 | 0.599405 | 0.931880 | 2.868305 | 43 | 6 | 1 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | validation | 1m_3m | 837 | 0.603345 | 0.319069 | 0.533703 | 1.725541 | 28 | 1 | 0 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | validation | 3m_10m | 744 | 0.537634 | 0.327666 | 0.421063 | 1.090563 | 6 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | validation | gt_10m | 571 | 0.739054 | 0.571693 | 0.527318 | 0.925313 | 0 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | validation | lt_1m | 423 | 0.782506 | 0.599405 | 0.932331 | 2.868305 | 43 | 6 | 1 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | validation | 1m_3m | 837 | 0.602151 | 0.319069 | 0.533669 | 1.725541 | 28 | 1 | 0 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | validation | 3m_10m | 744 | 0.473118 | 0.327666 | 0.420336 | 1.090563 | 6 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | validation | gt_10m | 571 | 0.432574 | 0.567045 | 0.523738 | 0.925313 | 0 | 0 | 0 |
| resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | validation | lt_1m | 423 | 0.780142 | 0.599405 | 0.932609 | 2.868305 | 43 | 6 | 1 |