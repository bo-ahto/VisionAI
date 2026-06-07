# PP-HCOEF1 Warm Huber 기준가/계수 고도화 실험

- 작성일: 2026-06-07 22:14
- 목적: Warm Huber에서 기준가 생성 방식과 피처별 계수 조정으로 기존 70:30 후보를 넘을 수 있는지 확인.
- 기준 후보: `current_70_30` = 유사 작품 기반 가격 피처 70% + 오차 안정화 후보 30%.
- 선택 원칙: validation 내부 교차검증 또는 validation 지표로 후보를 고르고, fixed test와 0604는 확인용으로 사용.

## 1. 실행 결론

- validation 선택 후보가 fixed test에서 2개 이상 지표 개선 조건을 만족하지 못해 기본 후보 유지
- 현재 기준 test: MdAPE `0.1405`, MAPE `0.2748`, p95 `0.8331`, RMSE_log `0.3996`.
- test만 좋은 후보는 채택하지 않고 bootstrap 및 추가 split 재검증 대상으로만 분리.

## 2. Validation 상위 후보

| candidate | method | MdAPE | MAPE | p95_APE | RMSE_log | score | beats_ref_metric_count |
| --- | --- | --- | --- | --- | --- | --- | --- |
| residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.12_s0.75 | current_residual_huber_correction | 0.1200 | 0.2075 | 0.6535 | 0.3214 | 0.9600 | 3 |
| residual_huber_resid_basis_size_reliability_alpha0.001_cap0.12_s0.75 | current_residual_huber_correction | 0.1200 | 0.2075 | 0.6535 | 0.3214 | 0.9601 | 3 |
| residual_huber_resid_basis_size_reliability_alpha0.01_cap0.12_s0.75 | current_residual_huber_correction | 0.1200 | 0.2075 | 0.6537 | 0.3214 | 0.9602 | 3 |
| residual_huber_resid_basis_gap_alpha0.01_cap0.08_s1.00 | current_residual_huber_correction | 0.1193 | 0.2086 | 0.6602 | 0.3237 | 0.9624 | 2 |
| residual_huber_resid_basis_gap_alpha0.001_cap0.08_s1.00 | current_residual_huber_correction | 0.1194 | 0.2086 | 0.6602 | 0.3237 | 0.9628 | 2 |
| residual_huber_resid_basis_gap_alpha0.0001_cap0.08_s1.00 | current_residual_huber_correction | 0.1195 | 0.2086 | 0.6602 | 0.3237 | 0.9628 | 2 |
| residual_huber_resid_basis_gap_alpha0.01_cap0.12_s0.75 | current_residual_huber_correction | 0.1209 | 0.2087 | 0.6516 | 0.3235 | 0.9643 | 3 |
| residual_huber_resid_basis_gap_alpha0.001_cap0.12_s0.75 | current_residual_huber_correction | 0.1209 | 0.2087 | 0.6516 | 0.3235 | 0.9644 | 3 |
| residual_huber_resid_basis_gap_alpha0.0001_cap0.12_s0.75 | current_residual_huber_correction | 0.1209 | 0.2087 | 0.6516 | 0.3235 | 0.9644 | 3 |
| blend_ppv8_svc_shrunk_0.1_0.9_0.0 | basis_weight_simplex_grid | 0.1200 | 0.2136 | 0.6424 | 0.3354 | 0.9661 | 2 |
| residual_huber_resid_basis_gap_alpha0.01_cap0.08_s0.75 | current_residual_huber_correction | 0.1226 | 0.2083 | 0.6480 | 0.3243 | 0.9674 | 3 |
| residual_huber_resid_basis_gap_alpha0.001_cap0.08_s0.75 | current_residual_huber_correction | 0.1226 | 0.2083 | 0.6480 | 0.3243 | 0.9674 | 3 |

## 3. Validation 선택 후보의 test/0604 확인

| selection_objective | selected_candidate | method | val_MdAPE | val_MAPE | val_p95_APE | val_score | test_MdAPE | test_MAPE | test_p95_APE | ops0604_MdAPE | ops0604_MAPE | ops0604_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| balanced_score | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.12_s0.75 | current_residual_huber_correction | 0.1200 | 0.2075 | 0.6535 | 0.9600 | 0.1437 | 0.2718 | 0.8469 | 0.2677 | 0.3711 | 0.9718 |
| mdape_primary | residual_huber_resid_basis_gap_alpha0.01_cap0.08_s1.00 | current_residual_huber_correction | 0.1193 | 0.2086 | 0.6602 | 0.9624 | 0.1511 | 0.2763 | 0.8830 | 0.2713 | 0.3740 | 0.9595 |
| mape_guarded | meta_huber_basis_reliability_alpha0.01 | meta_huber_crossfit_validation | 0.1247 | 0.2067 | 0.6593 | 0.9754 | 0.1426 | 0.2726 | 0.9232 | 0.2756 | 0.3872 | 1.0752 |
| p95_guarded | blend_ppv8_svc_shrunk_0.2_0.8_0.0 | basis_weight_simplex_grid | 0.1249 | 0.2112 | 0.6252 | 0.9706 | 0.1430 | 0.2802 | 0.9075 | 0.2919 | 0.3942 | 0.9946 |

## 4. Fixed test 상위 후보

| candidate | method | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- |
| residual_huber_resid_basis_gap_alpha0.01_cap0.12_s0.50 | current_residual_huber_correction | 0.1359 | 0.2736 | 0.8565 | 0.3987 |
| residual_huber_resid_basis_gap_alpha0.001_cap0.12_s0.50 | current_residual_huber_correction | 0.1359 | 0.2736 | 0.8565 | 0.3987 |
| residual_huber_resid_basis_gap_alpha0.0001_cap0.12_s0.50 | current_residual_huber_correction | 0.1359 | 0.2736 | 0.8565 | 0.3987 |
| blend_ppv8_svc_shrunk_0.4_0.6_0.0 | basis_weight_simplex_grid | 0.1362 | 0.2717 | 0.8329 | 0.4003 |
| residual_huber_resid_basis_size_reliability_alpha0.01_cap0.03_s0.25 | current_residual_huber_correction | 0.1374 | 0.2741 | 0.8210 | 0.3993 |
| residual_huber_resid_basis_size_reliability_alpha0.001_cap0.03_s0.25 | current_residual_huber_correction | 0.1374 | 0.2741 | 0.8210 | 0.3993 |
| residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.03_s0.25 | current_residual_huber_correction | 0.1374 | 0.2741 | 0.8210 | 0.3993 |
| blend_current_shrunk_huber_wcurrent_0.95 | current_shrunk_huber_weight_grid | 0.1377 | 0.2749 | 0.8471 | 0.3988 |
| residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.12_s0.25 | current_residual_huber_correction | 0.1378 | 0.2728 | 0.8169 | 0.3982 |
| residual_huber_resid_basis_size_reliability_alpha0.001_cap0.12_s0.25 | current_residual_huber_correction | 0.1378 | 0.2728 | 0.8169 | 0.3982 |
| residual_huber_resid_basis_size_reliability_alpha0.01_cap0.12_s0.25 | current_residual_huber_correction | 0.1378 | 0.2728 | 0.8169 | 0.3982 |
| residual_huber_resid_basis_gap_alpha0.01_cap0.03_s0.25 | current_residual_huber_correction | 0.1382 | 0.2745 | 0.8307 | 0.3996 |

## 5. 기준 후보 대비 2개 이상 지표 개선 후보

| candidate | method | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- |
| residual_huber_resid_basis_gap_alpha0.01_cap0.12_s0.50 | current_residual_huber_correction | 0.1359 | 0.2736 | 0.8565 | 0.3987 |
| residual_huber_resid_basis_gap_alpha0.001_cap0.12_s0.50 | current_residual_huber_correction | 0.1359 | 0.2736 | 0.8565 | 0.3987 |
| residual_huber_resid_basis_gap_alpha0.0001_cap0.12_s0.50 | current_residual_huber_correction | 0.1359 | 0.2736 | 0.8565 | 0.3987 |
| blend_ppv8_svc_shrunk_0.4_0.6_0.0 | basis_weight_simplex_grid | 0.1362 | 0.2717 | 0.8329 | 0.4003 |
| residual_huber_resid_basis_size_reliability_alpha0.01_cap0.03_s0.25 | current_residual_huber_correction | 0.1374 | 0.2741 | 0.8210 | 0.3993 |
| residual_huber_resid_basis_size_reliability_alpha0.001_cap0.03_s0.25 | current_residual_huber_correction | 0.1374 | 0.2741 | 0.8210 | 0.3993 |
| residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.03_s0.25 | current_residual_huber_correction | 0.1374 | 0.2741 | 0.8210 | 0.3993 |
| residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.12_s0.25 | current_residual_huber_correction | 0.1378 | 0.2728 | 0.8169 | 0.3982 |
| residual_huber_resid_basis_size_reliability_alpha0.001_cap0.12_s0.25 | current_residual_huber_correction | 0.1378 | 0.2728 | 0.8169 | 0.3982 |
| residual_huber_resid_basis_size_reliability_alpha0.01_cap0.12_s0.25 | current_residual_huber_correction | 0.1378 | 0.2728 | 0.8169 | 0.3982 |
| residual_huber_resid_basis_gap_alpha0.01_cap0.03_s0.25 | current_residual_huber_correction | 0.1382 | 0.2745 | 0.8307 | 0.3996 |
| residual_huber_resid_basis_gap_alpha0.001_cap0.03_s0.25 | current_residual_huber_correction | 0.1382 | 0.2745 | 0.8307 | 0.3996 |
| residual_huber_resid_basis_gap_alpha0.0001_cap0.03_s0.25 | current_residual_huber_correction | 0.1382 | 0.2745 | 0.8307 | 0.3996 |
| residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.12_s0.50 | current_residual_huber_correction | 0.1388 | 0.2718 | 0.8191 | 0.3976 |
| residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.05_s0.50 | current_residual_huber_correction | 0.1388 | 0.2730 | 0.8064 | 0.3988 |
| residual_huber_resid_basis_size_reliability_alpha0.001_cap0.12_s0.50 | current_residual_huber_correction | 0.1388 | 0.2718 | 0.8191 | 0.3976 |
| residual_huber_resid_basis_size_reliability_alpha0.001_cap0.05_s0.50 | current_residual_huber_correction | 0.1388 | 0.2730 | 0.8064 | 0.3988 |
| residual_huber_resid_basis_size_reliability_alpha0.01_cap0.12_s0.50 | current_residual_huber_correction | 0.1388 | 0.2718 | 0.8191 | 0.3976 |
| residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | current_residual_huber_correction | 0.1388 | 0.2730 | 0.8064 | 0.3988 |
| residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.25 | current_residual_huber_correction | 0.1390 | 0.2737 | 0.8169 | 0.3991 |

## 6. Bootstrap 안정성 요약

| sample_type | candidate | mean_delta_MdAPE | mean_delta_MAPE | mean_delta_p95_APE | MdAPE_improve_prob | MAPE_improve_prob | p95_improve_prob |
| --- | --- | --- | --- | --- | --- | --- | --- |
| artist_bootstrap | blend_ppv8_svc_shrunk_0.4_0.6_0.0 | -0.0021 | -0.0031 | -0.0036 | 0.6367 | 0.8033 | 0.4600 |
| artist_bootstrap | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.03_s0.25 | -0.0012 | -0.0007 | 0.0002 | 0.6200 | 0.9567 | 0.4833 |
| artist_bootstrap | residual_huber_resid_basis_size_reliability_alpha0.001_cap0.03_s0.25 | -0.0012 | -0.0007 | 0.0002 | 0.6200 | 0.9533 | 0.4833 |
| artist_bootstrap | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.03_s0.25 | -0.0012 | -0.0007 | 0.0002 | 0.6200 | 0.9533 | 0.4833 |
| artist_bootstrap | residual_huber_resid_basis_gap_alpha0.01_cap0.12_s0.50 | -0.0010 | -0.0013 | 0.0331 | 0.5733 | 0.7567 | 0.1700 |
| artist_bootstrap | residual_huber_resid_basis_gap_alpha0.001_cap0.12_s0.50 | -0.0010 | -0.0012 | 0.0331 | 0.5700 | 0.7567 | 0.1700 |
| artist_bootstrap | residual_huber_resid_basis_gap_alpha0.0001_cap0.12_s0.50 | -0.0010 | -0.0012 | 0.0331 | 0.5700 | 0.7567 | 0.1700 |
| artist_bootstrap | blend_current_shrunk_huber_wcurrent_0.95 | -0.0007 | 0.0001 | -0.0018 | 0.5867 | 0.5033 | 0.4633 |
| artist_bootstrap | current_70_30 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| artist_bootstrap | meta_huber_basis_reliability_alpha0.01 | 0.0028 | -0.0023 | 0.0651 | 0.4067 | 0.6700 | 0.1733 |
| artist_bootstrap | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.12_s0.75 | 0.0029 | -0.0030 | 0.0328 | 0.3600 | 0.8533 | 0.2767 |
| artist_bootstrap | blend_ppv8_svc_shrunk_0.2_0.8_0.0 | 0.0036 | 0.0055 | 0.0537 | 0.1433 | 0.1100 | 0.1400 |
| artist_bootstrap | residual_huber_resid_basis_gap_alpha0.01_cap0.08_s1.00 | 0.0068 | 0.0013 | 0.0529 | 0.1467 | 0.3067 | 0.1267 |
| row_bootstrap | blend_ppv8_svc_shrunk_0.4_0.6_0.0 | -0.0025 | -0.0032 | -0.0065 | 0.6733 | 0.8500 | 0.5100 |
| row_bootstrap | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.03_s0.25 | -0.0013 | -0.0006 | 0.0000 | 0.6500 | 0.9800 | 0.4600 |
| row_bootstrap | residual_huber_resid_basis_size_reliability_alpha0.001_cap0.03_s0.25 | -0.0013 | -0.0006 | 0.0000 | 0.6500 | 0.9800 | 0.4600 |
| row_bootstrap | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.03_s0.25 | -0.0013 | -0.0006 | 0.0000 | 0.6500 | 0.9800 | 0.4600 |
| row_bootstrap | residual_huber_resid_basis_gap_alpha0.01_cap0.12_s0.50 | -0.0013 | -0.0009 | 0.0327 | 0.5767 | 0.7067 | 0.1400 |
| row_bootstrap | residual_huber_resid_basis_gap_alpha0.001_cap0.12_s0.50 | -0.0013 | -0.0009 | 0.0327 | 0.5767 | 0.7067 | 0.1400 |
| row_bootstrap | residual_huber_resid_basis_gap_alpha0.0001_cap0.12_s0.50 | -0.0013 | -0.0008 | 0.0327 | 0.5767 | 0.7067 | 0.1400 |
| row_bootstrap | blend_current_shrunk_huber_wcurrent_0.95 | -0.0006 | 0.0001 | -0.0042 | 0.5367 | 0.4367 | 0.4967 |
| row_bootstrap | current_70_30 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| row_bootstrap | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.12_s0.75 | 0.0035 | -0.0025 | 0.0307 | 0.2900 | 0.8833 | 0.2467 |
| row_bootstrap | meta_huber_basis_reliability_alpha0.01 | 0.0037 | -0.0015 | 0.0684 | 0.3567 | 0.6633 | 0.1200 |

## 7. 주요 Huber/Ridge 계수

- 계수는 표준화된 피처 기준이다. 절대 가격 단위의 직접 계수는 아니며, 방향성과 상대적 영향 확인용이다.
| candidate | model_type | target | feature | coefficient_on_scaled_feature | abs_coefficient | intercept |
| --- | --- | --- | --- | --- | --- | --- |
| meta_huber_basis3_alpha0.0001 | huber | actual_log | svc_fallback | 1.0535 | 1.0535 | 14.9862 |
| meta_huber_basis3_alpha0.0001 | huber | actual_log | ppv8_defensive | 0.4178 | 0.4178 | 14.9862 |
| meta_huber_basis3_alpha0.0001 | huber | actual_log | shrunk_huber_refit | -0.1827 | 0.1827 | 14.9862 |
| meta_huber_basis3_alpha0.001 | huber | actual_log | svc_fallback | 1.0534 | 1.0534 | 14.9862 |
| meta_huber_basis3_alpha0.001 | huber | actual_log | ppv8_defensive | 0.4178 | 0.4178 | 14.9862 |
| meta_huber_basis3_alpha0.001 | huber | actual_log | shrunk_huber_refit | -0.1827 | 0.1827 | 14.9862 |
| meta_huber_basis3_alpha0.01 | huber | actual_log | svc_fallback | 1.0533 | 1.0533 | 14.9862 |
| meta_huber_basis3_alpha0.01 | huber | actual_log | ppv8_defensive | 0.4179 | 0.4179 | 14.9862 |
| meta_huber_basis3_alpha0.01 | huber | actual_log | shrunk_huber_refit | -0.1826 | 0.1826 | 14.9862 |
| meta_ridge_basis3_alpha0.1 | ridge | actual_log | svc_fallback | 0.9959 | 0.9959 | 15.0033 |
| meta_ridge_basis3_alpha0.1 | ridge | actual_log | ppv8_defensive | 0.5096 | 0.5096 | 15.0033 |
| meta_ridge_basis3_alpha0.1 | ridge | actual_log | shrunk_huber_refit | -0.2243 | 0.2243 | 15.0033 |
| meta_ridge_basis3_alpha1 | ridge | actual_log | svc_fallback | 0.9599 | 0.9599 | 15.0033 |
| meta_ridge_basis3_alpha1 | ridge | actual_log | ppv8_defensive | 0.5150 | 0.5150 | 15.0033 |
| meta_ridge_basis3_alpha1 | ridge | actual_log | shrunk_huber_refit | -0.1943 | 0.1943 | 15.0033 |
| meta_ridge_basis3_alpha10 | ridge | actual_log | svc_fallback | 0.7570 | 0.7570 | 15.0033 |
| meta_ridge_basis3_alpha10 | ridge | actual_log | ppv8_defensive | 0.5168 | 0.5168 | 15.0033 |
| meta_ridge_basis3_alpha10 | ridge | actual_log | shrunk_huber_refit | 0.0002 | 0.0002 | 15.0033 |
| meta_huber_basis5_alpha0.0001 | huber | actual_log | current_70_30 | 1.8460 | 1.8460 | 14.9909 |
| meta_huber_basis5_alpha0.0001 | huber | actual_log | shrunk_huber_refit | -0.2642 | 0.2642 | 14.9909 |
| meta_huber_basis5_alpha0.0001 | huber | actual_log | svc_fallback | -0.2272 | 0.2272 | 14.9909 |
| meta_huber_basis5_alpha0.0001 | huber | actual_log | ppv8_defensive | -0.1439 | 0.1439 | 14.9909 |
| meta_huber_basis5_alpha0.0001 | huber | actual_log | shrunk_svc_prior | 0.0707 | 0.0707 | 14.9909 |
| meta_huber_basis5_alpha0.001 | huber | actual_log | current_70_30 | 1.8424 | 1.8424 | 14.9909 |
| meta_huber_basis5_alpha0.001 | huber | actual_log | shrunk_huber_refit | -0.2641 | 0.2641 | 14.9909 |
| meta_huber_basis5_alpha0.001 | huber | actual_log | svc_fallback | -0.2247 | 0.2247 | 14.9909 |
| meta_huber_basis5_alpha0.001 | huber | actual_log | ppv8_defensive | -0.1429 | 0.1429 | 14.9909 |
| meta_huber_basis5_alpha0.001 | huber | actual_log | shrunk_svc_prior | 0.0707 | 0.0707 | 14.9909 |
| meta_huber_basis5_alpha0.01 | huber | actual_log | current_70_30 | 1.8083 | 1.8083 | 14.9908 |
| meta_huber_basis5_alpha0.01 | huber | actual_log | shrunk_huber_refit | -0.2635 | 0.2635 | 14.9908 |
| meta_huber_basis5_alpha0.01 | huber | actual_log | svc_fallback | -0.2015 | 0.2015 | 14.9908 |
| meta_huber_basis5_alpha0.01 | huber | actual_log | ppv8_defensive | -0.1326 | 0.1326 | 14.9908 |
| meta_huber_basis5_alpha0.01 | huber | actual_log | shrunk_svc_prior | 0.0709 | 0.0709 | 14.9908 |
| meta_ridge_basis5_alpha0.1 | ridge | actual_log | current_70_30 | 1.6506 | 1.6506 | 15.0033 |
| meta_ridge_basis5_alpha0.1 | ridge | actual_log | shrunk_huber_refit | -0.3062 | 0.3062 | 15.0033 |
| meta_ridge_basis5_alpha0.1 | ridge | actual_log | svc_fallback | -0.1428 | 0.1428 | 15.0033 |
| meta_ridge_basis5_alpha0.1 | ridge | actual_log | shrunk_svc_prior | 0.0675 | 0.0675 | 15.0033 |
| meta_ridge_basis5_alpha0.1 | ridge | actual_log | ppv8_defensive | 0.0086 | 0.0086 | 15.0033 |
| meta_ridge_basis5_alpha1 | ridge | actual_log | current_70_30 | 0.7366 | 0.7366 | 15.0033 |
| meta_ridge_basis5_alpha1 | ridge | actual_log | svc_fallback | 0.4629 | 0.4629 | 15.0033 |

## 8. 잔차/큰 오차 요약

| split | candidate | median_residual_log | mean_residual_log | residual_std | over_2x_n | under_half_n | ape_gt_100pct_n |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_ex50 | blend_ppv8_svc_shrunk_0.2_0.8_0.0 | 0.0824 | 0.3611 | 1.3895 | 31 | 159 | 31 |
| 0604_ex50 | current_70_30 | 0.0782 | 0.3370 | 1.2685 | 30 | 153 | 30 |
| 0604_ex50 | meta_huber_basis_reliability_alpha0.01 | -0.0178 | 0.1585 | 1.1601 | 46 | 88 | 46 |
| 0604_ex50 | residual_huber_resid_basis_gap_alpha0.01_cap0.08_s1.00 | 0.0484 | 0.3071 | 1.2646 | 23 | 137 | 23 |
| 0604_ex50 | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.12_s0.75 | 0.0457 | 0.3037 | 1.2625 | 22 | 137 | 22 |
| test | blend_ppv8_svc_shrunk_0.2_0.8_0.0 | -0.0011 | -0.0131 | 0.4106 | 28 | 17 | 28 |
| test | current_70_30 | -0.0006 | -0.0119 | 0.3998 | 24 | 17 | 24 |
| test | meta_huber_basis_reliability_alpha0.01 | -0.0047 | -0.0218 | 0.3973 | 28 | 16 | 28 |
| test | residual_huber_resid_basis_gap_alpha0.01_cap0.08_s1.00 | -0.0136 | -0.0211 | 0.4002 | 27 | 17 | 27 |
| test | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.12_s0.75 | -0.0064 | -0.0188 | 0.3975 | 27 | 17 | 27 |

## 9. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/residual_analysis.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `outputs/bootstrap_samples.csv`
- `artifacts/experiment_config.json`