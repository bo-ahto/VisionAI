# Cold 유사도 missing 피처 제거 검증

- 작성일: 2026-06-22T15:58:17
- 목적: 유사 이웃 선택에서 missing 여부 피처를 제거했을 때 성능 변화를 확인한다.
- 모델 입력 피처는 기존 user_meta_core_bucket을 유지하고, 유사도 피처에서만 missing flag를 제거했다.
- 제거 피처: `artist_meta_birth_year_missing`, `artist_meta_total_works_missing`, `artist_meta_followers_missing`, `artist_meta_career_stage_missing`

## 1. 라우터 후보 성능
| candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 | APE_gt_10 | selected_rate | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| resid_artist_meta_no_missing_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | test | 0.480796 | 0.700283 | 2.161220 | 0.814631 | 190 | 32 | 7 | 0.562000 | 하향 보정 0.03 log 이상이면 보정 후보 적용 |
| resid_artist_meta_no_missing_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | test | 0.483119 | 0.700790 | 2.161220 | 0.814709 | 190 | 32 | 8 | 0.530333 | 하향 보정 0.05 log 이상이면 보정 후보 적용 |
| resid_artist_meta_no_missing_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | test | 0.480796 | 0.702100 | 2.189605 | 0.812940 | 190 | 32 | 7 | 0.562000 | 하향 보정 0.03 log 이상이면 보정 후보 적용 |
| resid_artist_meta_no_missing_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | test | 0.483119 | 0.702607 | 2.189605 | 0.813018 | 190 | 32 | 8 | 0.530333 | 하향 보정 0.05 log 이상이면 보정 후보 적용 |
| resid_artist_meta_no_missing_k80_s1p0_cap0p25__route_neg_corr_ge_0p03 | test | 0.486776 | 0.708611 | 2.189605 | 0.814123 | 191 | 32 | 8 | 0.546333 | 하향 보정 0.03 log 이상이면 보정 후보 적용 |
| resid_artist_meta_no_missing_k80_s1p0_cap0p25__route_neg_corr_ge_0p05 | test | 0.486468 | 0.709794 | 2.189605 | 0.814214 | 191 | 32 | 8 | 0.501333 | 하향 보정 0.05 log 이상이면 보정 후보 적용 |
| resid_artist_meta_no_missing_k80_s1p0_cap0p18__route_neg_corr_ge_0p03 | test | 0.486468 | 0.710186 | 2.194383 | 0.814077 | 191 | 32 | 8 | 0.546333 | 하향 보정 0.03 log 이상이면 보정 후보 적용 |
| resid_artist_meta_no_missing_k80_s1p0_cap0p18__route_neg_corr_ge_0p05 | test | 0.486161 | 0.711369 | 2.194383 | 0.814168 | 191 | 32 | 8 | 0.501333 | 하향 보정 0.05 log 이상이면 보정 후보 적용 |
| base | test | 0.481850 | 0.746296 | 2.398009 | 0.802895 | 212 | 35 | 8 | 0.000000 | 항상 base similarity k160 |
| resid_artist_meta_no_missing_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | validation | 0.397448 | 0.551661 | 1.535785 | 0.809555 | 75 | 9 | 1 | 0.554951 | 하향 보정 0.03 log 이상이면 보정 후보 적용 |
| resid_artist_meta_no_missing_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | validation | 0.397612 | 0.551784 | 1.535785 | 0.808562 | 75 | 9 | 1 | 0.544854 | 하향 보정 0.05 log 이상이면 보정 후보 적용 |
| resid_artist_meta_no_missing_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | validation | 0.396381 | 0.552381 | 1.533461 | 0.809870 | 75 | 8 | 1 | 0.554951 | 하향 보정 0.03 log 이상이면 보정 후보 적용 |
| resid_artist_meta_no_missing_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | validation | 0.397061 | 0.552504 | 1.533461 | 0.808878 | 75 | 8 | 1 | 0.544854 | 하향 보정 0.05 log 이상이면 보정 후보 적용 |
| resid_artist_meta_no_missing_k80_s1p0_cap0p18__route_neg_corr_ge_0p05 | validation | 0.398763 | 0.553441 | 1.573982 | 0.805866 | 72 | 9 | 1 | 0.527379 | 하향 보정 0.05 log 이상이면 보정 후보 적용 |
| resid_artist_meta_no_missing_k80_s1p0_cap0p25__route_neg_corr_ge_0p05 | validation | 0.398543 | 0.554010 | 1.558001 | 0.806156 | 72 | 8 | 1 | 0.527379 | 하향 보정 0.05 log 이상이면 보정 후보 적용 |
| resid_artist_meta_no_missing_k80_s1p0_cap0p18__route_neg_corr_ge_0p03 | validation | 0.398656 | 0.554133 | 1.573982 | 0.809821 | 72 | 9 | 1 | 0.621359 | 하향 보정 0.03 log 이상이면 보정 후보 적용 |
| resid_artist_meta_no_missing_k80_s1p0_cap0p25__route_neg_corr_ge_0p03 | validation | 0.398342 | 0.554702 | 1.558001 | 0.810110 | 72 | 8 | 1 | 0.621359 | 하향 보정 0.03 log 이상이면 보정 후보 적용 |
| base | validation | 0.424537 | 0.606746 | 1.808312 | 0.809976 | 97 | 10 | 1 | 0.000000 | 항상 base similarity k160 |

## 2. 원천 잔차 후보 성능
| candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 | APE_gt_10 | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| resid_artist_meta_no_missing_k80_s1p0_cap0p18 | test | 0.504395 | 0.734259 | 2.298326 | 0.817385 | 201 | 31 | 8 | artist_meta_no_missing top_k=80 residual median, correction=clip(1.00*median, +/-0.18) |
| resid_artist_meta_no_missing_k80_s1p0_cap0p1 | test | 0.499682 | 0.734336 | 2.315395 | 0.814214 | 201 | 32 | 8 | artist_meta_no_missing top_k=80 residual median, correction=clip(1.00*median, +/-0.10) |
| resid_artist_meta_no_missing_k80_s1p0_cap0p25 | test | 0.504400 | 0.734505 | 2.288989 | 0.817977 | 202 | 31 | 8 | artist_meta_no_missing top_k=80 residual median, correction=clip(1.00*median, +/-0.25) |
| resid_artist_meta_no_missing_k40_s0p75_cap0p1 | test | 0.484226 | 0.734950 | 2.359538 | 0.811551 | 205 | 33 | 8 | artist_meta_no_missing top_k=40 residual median, correction=clip(0.75*median, +/-0.10) |
| resid_artist_meta_no_missing_k80_s0p75_cap0p1 | test | 0.494254 | 0.735079 | 2.335752 | 0.812133 | 199 | 33 | 8 | artist_meta_no_missing top_k=80 residual median, correction=clip(0.75*median, +/-0.10) |
| resid_artist_meta_no_missing_k40_s1p0_cap0p1 | test | 0.487229 | 0.735200 | 2.334706 | 0.813047 | 208 | 32 | 8 | artist_meta_no_missing top_k=40 residual median, correction=clip(1.00*median, +/-0.10) |
| resid_artist_meta_no_missing_k80_s0p75_cap0p25 | test | 0.493228 | 0.735355 | 2.320431 | 0.813065 | 197 | 33 | 8 | artist_meta_no_missing top_k=80 residual median, correction=clip(0.75*median, +/-0.25) |
| resid_artist_meta_no_missing_k80_s0p75_cap0p18 | test | 0.493025 | 0.735679 | 2.330201 | 0.812813 | 196 | 33 | 8 | artist_meta_no_missing top_k=80 residual median, correction=clip(0.75*median, +/-0.18) |
| resid_artist_meta_no_missing_k40_s1p0_cap0p18 | test | 0.492068 | 0.736962 | 2.308478 | 0.818473 | 211 | 31 | 8 | artist_meta_no_missing top_k=40 residual median, correction=clip(1.00*median, +/-0.18) |
| resid_artist_meta_no_missing_k320_s1p0_cap0p1 | test | 0.481566 | 0.737266 | 2.319658 | 0.807441 | 205 | 33 | 7 | artist_meta_no_missing top_k=320 residual median, correction=clip(1.00*median, +/-0.10) |
| resid_artist_meta_no_missing_k320_s1p0_cap0p18 | test | 0.481566 | 0.737549 | 2.319658 | 0.807794 | 205 | 33 | 7 | artist_meta_no_missing top_k=320 residual median, correction=clip(1.00*median, +/-0.18) |
| resid_artist_meta_no_missing_k320_s1p0_cap0p25 | test | 0.481566 | 0.737549 | 2.319658 | 0.807794 | 205 | 33 | 7 | artist_meta_no_missing top_k=320 residual median, correction=clip(1.00*median, +/-0.25) |
| resid_artist_meta_no_missing_k80_s0p5_cap0p25 | test | 0.494881 | 0.737760 | 2.326901 | 0.808712 | 206 | 33 | 8 | artist_meta_no_missing top_k=80 residual median, correction=clip(0.50*median, +/-0.25) |
| resid_artist_meta_no_missing_k80_s0p5_cap0p18 | test | 0.494881 | 0.737766 | 2.326901 | 0.808711 | 206 | 33 | 8 | artist_meta_no_missing top_k=80 residual median, correction=clip(0.50*median, +/-0.18) |
| resid_artist_meta_no_missing_k80_s0p5_cap0p1 | test | 0.495712 | 0.738186 | 2.326901 | 0.808528 | 206 | 33 | 8 | artist_meta_no_missing top_k=80 residual median, correction=clip(0.50*median, +/-0.10) |
| resid_artist_meta_no_missing_k40_s0p75_cap0p18 | test | 0.486004 | 0.738539 | 2.330482 | 0.814394 | 207 | 33 | 8 | artist_meta_no_missing top_k=40 residual median, correction=clip(0.75*median, +/-0.18) |
| resid_artist_meta_no_missing_k80_s1p0_cap0p05 | test | 0.491785 | 0.738574 | 2.323684 | 0.807034 | 203 | 32 | 8 | artist_meta_no_missing top_k=80 residual median, correction=clip(1.00*median, +/-0.05) |
| resid_artist_meta_no_missing_k320_s0p75_cap0p05 | test | 0.478542 | 0.738655 | 2.347724 | 0.805720 | 206 | 33 | 7 | artist_meta_no_missing top_k=320 residual median, correction=clip(0.75*median, +/-0.05) |
| resid_artist_meta_no_missing_k80_s0p5_cap0p05 | test | 0.492778 | 0.738964 | 2.326901 | 0.807521 | 204 | 33 | 8 | artist_meta_no_missing top_k=80 residual median, correction=clip(0.50*median, +/-0.05) |
| resid_artist_meta_no_missing_k40_s0p5_cap0p1 | test | 0.483069 | 0.738978 | 2.386139 | 0.808772 | 212 | 33 | 7 | artist_meta_no_missing top_k=40 residual median, correction=clip(0.50*median, +/-0.10) |
| resid_artist_meta_no_missing_k40_s0p5_cap0p05 | test | 0.482778 | 0.739124 | 2.339701 | 0.806813 | 207 | 33 | 7 | artist_meta_no_missing top_k=40 residual median, correction=clip(0.50*median, +/-0.05) |
| resid_artist_meta_no_missing_k320_s0p75_cap0p1 | test | 0.480006 | 0.739227 | 2.337383 | 0.806248 | 206 | 33 | 7 | artist_meta_no_missing top_k=320 residual median, correction=clip(0.75*median, +/-0.10) |
| resid_artist_meta_no_missing_k80_s0p75_cap0p05 | test | 0.492193 | 0.739228 | 2.333769 | 0.807562 | 203 | 33 | 8 | artist_meta_no_missing top_k=80 residual median, correction=clip(0.75*median, +/-0.05) |
| resid_artist_meta_no_missing_k320_s0p75_cap0p18 | test | 0.480006 | 0.739256 | 2.337383 | 0.806258 | 206 | 33 | 7 | artist_meta_no_missing top_k=320 residual median, correction=clip(0.75*median, +/-0.18) |
| resid_artist_meta_no_missing_k320_s0p75_cap0p25 | test | 0.480006 | 0.739256 | 2.337383 | 0.806258 | 206 | 33 | 7 | artist_meta_no_missing top_k=320 residual median, correction=clip(0.75*median, +/-0.25) |
| resid_artist_meta_no_missing_k320_s1p0_cap0p05 | test | 0.479063 | 0.739262 | 2.353330 | 0.806029 | 205 | 33 | 7 | artist_meta_no_missing top_k=320 residual median, correction=clip(1.00*median, +/-0.05) |
| resid_artist_meta_no_missing_k40_s0p75_cap0p05 | test | 0.484787 | 0.739692 | 2.341696 | 0.807192 | 207 | 33 | 8 | artist_meta_no_missing top_k=40 residual median, correction=clip(0.75*median, +/-0.05) |
| resid_artist_meta_no_missing_k40_s1p0_cap0p05 | test | 0.484302 | 0.739857 | 2.338171 | 0.807126 | 207 | 32 | 8 | artist_meta_no_missing top_k=40 residual median, correction=clip(1.00*median, +/-0.05) |
| resid_artist_meta_no_missing_k40_s1p0_cap0p25 | test | 0.495497 | 0.739894 | 2.296211 | 0.821159 | 213 | 32 | 8 | artist_meta_no_missing top_k=40 residual median, correction=clip(1.00*median, +/-0.25) |
| resid_artist_meta_no_missing_k40_s0p75_cap0p25 | test | 0.490889 | 0.739902 | 2.320134 | 0.816600 | 209 | 33 | 8 | artist_meta_no_missing top_k=40 residual median, correction=clip(0.75*median, +/-0.25) |
| resid_artist_meta_no_missing_k40_s0p5_cap0p18 | test | 0.483740 | 0.740262 | 2.384835 | 0.810820 | 214 | 33 | 7 | artist_meta_no_missing top_k=40 residual median, correction=clip(0.50*median, +/-0.18) |
| resid_artist_meta_no_missing_k160_s0p75_cap0p05 | test | 0.482633 | 0.740733 | 2.333668 | 0.807169 | 208 | 33 | 8 | artist_meta_no_missing top_k=160 residual median, correction=clip(0.75*median, +/-0.05) |
| resid_artist_meta_no_missing_k320_s0p5_cap0p05 | test | 0.482496 | 0.741126 | 2.374288 | 0.804768 | 209 | 33 | 7 | artist_meta_no_missing top_k=320 residual median, correction=clip(0.50*median, +/-0.05) |
| resid_artist_meta_no_missing_k320_s0p5_cap0p1 | test | 0.482496 | 0.741255 | 2.374288 | 0.804929 | 209 | 33 | 7 | artist_meta_no_missing top_k=320 residual median, correction=clip(0.50*median, +/-0.10) |
| resid_artist_meta_no_missing_k320_s0p5_cap0p18 | test | 0.482496 | 0.741255 | 2.374288 | 0.804929 | 209 | 33 | 7 | artist_meta_no_missing top_k=320 residual median, correction=clip(0.50*median, +/-0.18) |
| resid_artist_meta_no_missing_k320_s0p5_cap0p25 | test | 0.482496 | 0.741255 | 2.374288 | 0.804929 | 209 | 33 | 7 | artist_meta_no_missing top_k=320 residual median, correction=clip(0.50*median, +/-0.25) |
| resid_artist_meta_no_missing_k80_s0p25_cap0p1 | test | 0.489630 | 0.741316 | 2.336589 | 0.805315 | 210 | 33 | 8 | artist_meta_no_missing top_k=80 residual median, correction=clip(0.25*median, +/-0.10) |
| resid_artist_meta_no_missing_k80_s0p25_cap0p18 | test | 0.489630 | 0.741316 | 2.336589 | 0.805315 | 210 | 33 | 8 | artist_meta_no_missing top_k=80 residual median, correction=clip(0.25*median, +/-0.18) |
| resid_artist_meta_no_missing_k80_s0p25_cap0p25 | test | 0.489630 | 0.741316 | 2.336589 | 0.805315 | 210 | 33 | 8 | artist_meta_no_missing top_k=80 residual median, correction=clip(0.25*median, +/-0.25) |
| resid_artist_meta_no_missing_k160_s1p0_cap0p1 | test | 0.487747 | 0.741411 | 2.314846 | 0.810220 | 210 | 33 | 8 | artist_meta_no_missing top_k=160 residual median, correction=clip(1.00*median, +/-0.10) |

## 3. Paired bootstrap vs base
| split | candidate_a | candidate_b | n | n_boot | delta_MdAPE_a_minus_b_mean | delta_MAPE_a_minus_b_mean | delta_p95_APE_a_minus_b_mean | p_delta_MdAPE_a_minus_b_lt_0 | p_delta_MAPE_a_minus_b_lt_0 | p_delta_p95_APE_a_minus_b_lt_0 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | resid_artist_meta_no_missing_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | base | 2575 | 800 | -0.029545 | -0.054994 | -0.235358 | 1.000000 | 1.000000 | 1.000000 |
| validation | resid_artist_meta_no_missing_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | base | 2575 | 800 | -0.029251 | -0.054870 | -0.234641 | 1.000000 | 1.000000 | 1.000000 |
| validation | resid_artist_meta_no_missing_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | base | 2575 | 800 | -0.030468 | -0.054272 | -0.240751 | 1.000000 | 1.000000 | 1.000000 |
| validation | resid_artist_meta_no_missing_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | base | 2575 | 800 | -0.030160 | -0.054148 | -0.240034 | 1.000000 | 1.000000 | 1.000000 |
| validation | resid_artist_meta_no_missing_k80_s1p0_cap0p18__route_neg_corr_ge_0p03 | base | 2575 | 800 | -0.027473 | -0.052526 | -0.222491 | 1.000000 | 1.000000 | 1.000000 |
| validation | resid_artist_meta_no_missing_k80_s1p0_cap0p18__route_neg_corr_ge_0p05 | base | 2575 | 800 | -0.027105 | -0.053217 | -0.222121 | 1.000000 | 1.000000 | 1.000000 |
| validation | resid_artist_meta_no_missing_k80_s1p0_cap0p25__route_neg_corr_ge_0p03 | base | 2575 | 800 | -0.028254 | -0.051956 | -0.226858 | 1.000000 | 1.000000 | 1.000000 |
| validation | resid_artist_meta_no_missing_k80_s1p0_cap0p25__route_neg_corr_ge_0p05 | base | 2575 | 800 | -0.027830 | -0.052647 | -0.226488 | 1.000000 | 1.000000 | 1.000000 |
| test | resid_artist_meta_no_missing_k40_s1p0_cap0p18__route_neg_corr_ge_0p03 | base | 3000 | 800 | 0.000597 | -0.044180 | -0.188569 | 0.462500 | 1.000000 | 1.000000 |
| test | resid_artist_meta_no_missing_k40_s1p0_cap0p18__route_neg_corr_ge_0p05 | base | 3000 | 800 | 0.001540 | -0.043662 | -0.188569 | 0.376250 | 1.000000 | 1.000000 |
| test | resid_artist_meta_no_missing_k40_s1p0_cap0p25__route_neg_corr_ge_0p03 | base | 3000 | 800 | 0.001034 | -0.046003 | -0.202776 | 0.430000 | 1.000000 | 1.000000 |
| test | resid_artist_meta_no_missing_k40_s1p0_cap0p25__route_neg_corr_ge_0p05 | base | 3000 | 800 | 0.001995 | -0.045485 | -0.202776 | 0.338750 | 1.000000 | 1.000000 |
| test | resid_artist_meta_no_missing_k80_s1p0_cap0p18__route_neg_corr_ge_0p03 | base | 3000 | 800 | 0.006474 | -0.036046 | -0.167301 | 0.077500 | 1.000000 | 1.000000 |
| test | resid_artist_meta_no_missing_k80_s1p0_cap0p18__route_neg_corr_ge_0p05 | base | 3000 | 800 | 0.006071 | -0.034858 | -0.166989 | 0.095000 | 1.000000 | 1.000000 |
| test | resid_artist_meta_no_missing_k80_s1p0_cap0p25__route_neg_corr_ge_0p03 | base | 3000 | 800 | 0.006793 | -0.037632 | -0.182315 | 0.070000 | 1.000000 | 1.000000 |
| test | resid_artist_meta_no_missing_k80_s1p0_cap0p25__route_neg_corr_ge_0p05 | base | 3000 | 800 | 0.006392 | -0.036444 | -0.182020 | 0.086250 | 1.000000 | 1.000000 |

## 4. 해석

- 이 실험은 전체 작가 메타에서 missing 정보를 제거한 것이 아니라, 유사도 계산에서만 제거한 것이다.
- 성능이 좋아지면 missing 여부가 실제 작가 유사성보다 데이터 수집 상태를 기준으로 이웃을 묶고 있었을 가능성이 있다.
- 성능이 나빠지면 missing 여부 자체가 입력 품질/작가 프로필 밀도를 나타내는 유효 신호였을 가능성이 있다.