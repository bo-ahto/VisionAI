# PP-HCOEF4 Warm 기준가 생성 방식 고도화 실험

- 작성일: 2026-06-07 22:41
- 목적: 유사 작품 기준가를 작가/크기/재료 조합과 표본 수 신뢰도로 완화해 Huber 계수 조정에 넣었을 때 현재 Warm 후보를 넘는지 확인.
- 기준 후보: `current_70_30` = 유사 작품 기반 가격 피처 70% + 오차 안정화 후보 30%.
- 현재 개선 후보 대조: `hcoef2_size_reliability_cap005_s050`.
- 선택 원칙: validation에서 후보를 고르고 fixed test/0604는 확인용으로만 사용.

## 1. 실행 결론

- 반복 검증 후보: `loose_huber_basis_core_alpha0.1`. fixed test MdAPE/MAPE/p95 `0.1346/0.2618/0.8916`.
- 기준 fixed test: MdAPE `0.1405`, MAPE `0.2748`, p95 `0.8331`, RMSE_log `0.3996`.
- fixed test만 좋은 후보는 채택하지 않고 HCOEF5 반복 검증 후보로만 분리.

## 2. Validation 상위 후보

| candidate | method | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- |
| loose_ridge_basis_core_alpha10 | ridge_basis_meta_validation | 0.1191 | 0.2101 | 0.6426 | 0.3219 |
| loose_ridge_basis_gap_reliability_alpha10 | ridge_basis_meta_validation | 0.1222 | 0.2119 | 0.6533 | 0.3212 |
| loose_huber_basis_core_alpha0.001 | huber_basis_meta_validation | 0.1223 | 0.2082 | 0.6418 | 0.3182 |
| loose_huber_basis_core_alpha0.01 | huber_basis_meta_validation | 0.1223 | 0.2081 | 0.6423 | 0.3182 |
| loose_huber_basis_core_alpha0.1 | huber_basis_meta_validation | 0.1224 | 0.2077 | 0.6441 | 0.3182 |
| loose_relaxed_unit_area_basis | basis_component | 0.1236 | 0.2692 | 0.6933 | 0.4013 |
| default_huber_basis_core_alpha0.1 | huber_basis_meta_validation | 0.1239 | 0.2125 | 0.6364 | 0.3184 |
| loose_huber_basis_gap_reliability_alpha0.01 | huber_basis_meta_validation | 0.1241 | 0.2094 | 0.6489 | 0.3186 |
| loose_huber_basis_gap_reliability_alpha0.001 | huber_basis_meta_validation | 0.1241 | 0.2094 | 0.6489 | 0.3186 |
| loose_huber_basis_gap_reliability_alpha0.1 | huber_basis_meta_validation | 0.1243 | 0.2093 | 0.6485 | 0.3186 |
| default_huber_basis_gap_reliability_alpha0.1 | huber_basis_meta_validation | 0.1253 | 0.2129 | 0.6282 | 0.3186 |
| default_huber_basis_gap_reliability_alpha0.01 | huber_basis_meta_validation | 0.1255 | 0.2132 | 0.6264 | 0.3187 |
| default_huber_basis_gap_reliability_alpha0.001 | huber_basis_meta_validation | 0.1255 | 0.2132 | 0.6264 | 0.3188 |
| default_ridge_basis_core_alpha10 | ridge_basis_meta_validation | 0.1255 | 0.2150 | 0.6618 | 0.3218 |
| default_huber_basis_core_alpha0.001 | huber_basis_meta_validation | 0.1255 | 0.2132 | 0.6264 | 0.3188 |
| default_huber_basis_core_alpha0.01 | huber_basis_meta_validation | 0.1256 | 0.2131 | 0.6266 | 0.3188 |

## 3. Validation 선택 후보의 test/0604 확인

| selection_objective | selected_candidate | method | val_MdAPE | val_MAPE | val_p95_APE | val_score | test_MdAPE | test_MAPE | test_p95_APE | ops0604_MdAPE | ops0604_MAPE | ops0604_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| balanced_score | loose_ridge_basis_core_alpha10 | ridge_basis_meta_validation | 0.1191 | 0.2101 | 0.6426 | 0.9577 | 0.1425 | 0.2639 | 0.9083 | 0.2114 | 0.3298 | 0.9362 |
| mape_guarded | loose_huber_basis_core_alpha0.1 | huber_basis_meta_validation | 0.1224 | 0.2077 | 0.6441 | 0.9642 | 0.1346 | 0.2618 | 0.8916 | 0.2304 | 0.3447 | 0.9514 |
| p95_guarded | strict_ridge_basis_level_signals_alpha1 | ridge_basis_meta_validation | 0.1350 | 0.2158 | 0.6190 | 1.0068 | 0.1598 | 0.2902 | 0.9260 | 0.2816 | 0.4017 | 1.1383 |

## 4. Fixed test 상위 후보

| candidate | method | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- |
| loose_relaxed_unit_area_basis | basis_component | 0.1192 | 0.3328 | 1.1731 | 0.4715 |
| loose_huber_basis_gap_reliability_alpha0.1 | huber_basis_meta_validation | 0.1346 | 0.2628 | 0.9110 | 0.3902 |
| loose_huber_basis_core_alpha0.1 | huber_basis_meta_validation | 0.1346 | 0.2618 | 0.8916 | 0.3899 |
| loose_huber_basis_core_alpha0.001 | huber_basis_meta_validation | 0.1347 | 0.2621 | 0.8958 | 0.3896 |
| loose_huber_basis_gap_reliability_alpha0.001 | huber_basis_meta_validation | 0.1347 | 0.2628 | 0.9126 | 0.3901 |
| loose_huber_basis_core_alpha0.01 | huber_basis_meta_validation | 0.1347 | 0.2620 | 0.8952 | 0.3896 |
| loose_huber_basis_gap_reliability_alpha0.01 | huber_basis_meta_validation | 0.1348 | 0.2628 | 0.9126 | 0.3902 |
| default_relaxed_unit_area_basis | basis_component | 0.1350 | 0.3463 | 1.3055 | 0.4785 |
| hcoef2_size_reliability_cap005_s050 | current_residual_huber_correction | 0.1388 | 0.2730 | 0.8064 | 0.3988 |
| default_huber_basis_gap_reliability_alpha0.01 | huber_basis_meta_validation | 0.1390 | 0.2655 | 0.9209 | 0.3908 |
| default_huber_basis_core_alpha0.01 | huber_basis_meta_validation | 0.1390 | 0.2654 | 0.9208 | 0.3908 |
| default_huber_basis_core_alpha0.001 | huber_basis_meta_validation | 0.1392 | 0.2655 | 0.9209 | 0.3908 |
| default_huber_basis_gap_reliability_alpha0.001 | huber_basis_meta_validation | 0.1392 | 0.2655 | 0.9210 | 0.3908 |
| loose_ridge_basis_gap_reliability_alpha10 | ridge_basis_meta_validation | 0.1399 | 0.2670 | 0.8704 | 0.3925 |
| current_70_30 | reference | 0.1405 | 0.2748 | 0.8331 | 0.3996 |
| loose_dynamic_svc_basis_wbasis_0.20 | reliability_weighted_basis_blend | 0.1408 | 0.2751 | 0.8162 | 0.4010 |

## 5. 기준 대비 2개 이상 지표 개선 후보

| candidate | method | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- |
| loose_huber_basis_gap_reliability_alpha0.1 | huber_basis_meta_validation | 0.1346 | 0.2628 | 0.9110 | 0.3902 |
| loose_huber_basis_core_alpha0.1 | huber_basis_meta_validation | 0.1346 | 0.2618 | 0.8916 | 0.3899 |
| loose_huber_basis_core_alpha0.001 | huber_basis_meta_validation | 0.1347 | 0.2621 | 0.8958 | 0.3896 |
| loose_huber_basis_gap_reliability_alpha0.001 | huber_basis_meta_validation | 0.1347 | 0.2628 | 0.9126 | 0.3901 |
| loose_huber_basis_core_alpha0.01 | huber_basis_meta_validation | 0.1347 | 0.2620 | 0.8952 | 0.3896 |
| loose_huber_basis_gap_reliability_alpha0.01 | huber_basis_meta_validation | 0.1348 | 0.2628 | 0.9126 | 0.3902 |
| hcoef2_size_reliability_cap005_s050 | current_residual_huber_correction | 0.1388 | 0.2730 | 0.8064 | 0.3988 |
| default_huber_basis_gap_reliability_alpha0.01 | huber_basis_meta_validation | 0.1390 | 0.2655 | 0.9209 | 0.3908 |
| default_huber_basis_core_alpha0.01 | huber_basis_meta_validation | 0.1390 | 0.2654 | 0.9208 | 0.3908 |
| default_huber_basis_core_alpha0.001 | huber_basis_meta_validation | 0.1392 | 0.2655 | 0.9209 | 0.3908 |
| default_huber_basis_gap_reliability_alpha0.001 | huber_basis_meta_validation | 0.1392 | 0.2655 | 0.9210 | 0.3908 |
| loose_ridge_basis_gap_reliability_alpha10 | ridge_basis_meta_validation | 0.1399 | 0.2670 | 0.8704 | 0.3925 |

## 6. 주요 계수

- 계수는 표준화된 피처 기준이다. 방향성과 상대 영향 비교용이다.
| candidate | model_type | target | feature | coefficient_on_scaled_feature | abs_coefficient | intercept |
| --- | --- | --- | --- | --- | --- | --- |
| loose_huber_basis_core_alpha0.001 | huber | actual_log | current_70_30 | 1.0246 | 1.0246 | 14.9914 |
| loose_huber_basis_core_alpha0.001 | huber | actual_log | basis_relaxed_unit_area_log | 0.4530 | 0.4530 | 14.9914 |
| loose_huber_basis_core_alpha0.001 | huber | actual_log | shrunk_huber_refit | -0.2622 | 0.2622 | 14.9914 |
| loose_huber_basis_core_alpha0.001 | huber | actual_log | svc_fallback | -0.2586 | 0.2586 | 14.9914 |
| loose_huber_basis_core_alpha0.001 | huber | actual_log | shrunk_svc_prior | 0.2272 | 0.2272 | 14.9914 |
| loose_huber_basis_core_alpha0.001 | huber | actual_log | ppv8_defensive | 0.1218 | 0.1218 | 14.9914 |
| loose_huber_basis_core_alpha0.001 | huber | actual_log | log_area | 0.0374 | 0.0374 | 14.9914 |
| loose_huber_basis_core_alpha0.001 | huber | actual_log | basis_relaxed_price_log | -0.0317 | 0.0317 | 14.9914 |
| loose_huber_basis_core_alpha0.001 | huber | actual_log | basis_relaxed_n_log | -0.0149 | 0.0149 | 14.9914 |
| loose_huber_basis_core_alpha0.001 | huber | actual_log | basis_relaxed_iqr | -0.0017 | 0.0017 | 14.9914 |
| loose_huber_basis_core_alpha0.001 | huber | actual_log | basis_relaxed_missing | 0.0000 | 0.0000 | 14.9914 |
| loose_huber_basis_core_alpha0.01 | huber | actual_log | current_70_30 | 1.0069 | 1.0069 | 14.9914 |
| loose_huber_basis_core_alpha0.01 | huber | actual_log | basis_relaxed_unit_area_log | 0.4536 | 0.4536 | 14.9914 |
| loose_huber_basis_core_alpha0.01 | huber | actual_log | shrunk_huber_refit | -0.2617 | 0.2617 | 14.9914 |
| loose_huber_basis_core_alpha0.01 | huber | actual_log | svc_fallback | -0.2475 | 0.2475 | 14.9914 |
| loose_huber_basis_core_alpha0.01 | huber | actual_log | shrunk_svc_prior | 0.2272 | 0.2272 | 14.9914 |
| loose_huber_basis_core_alpha0.01 | huber | actual_log | ppv8_defensive | 0.1273 | 0.1273 | 14.9914 |
| loose_huber_basis_core_alpha0.01 | huber | actual_log | log_area | 0.0374 | 0.0374 | 14.9914 |
| loose_huber_basis_core_alpha0.01 | huber | actual_log | basis_relaxed_price_log | -0.0316 | 0.0316 | 14.9914 |
| loose_huber_basis_core_alpha0.01 | huber | actual_log | basis_relaxed_n_log | -0.0149 | 0.0149 | 14.9914 |
| loose_huber_basis_core_alpha0.01 | huber | actual_log | basis_relaxed_iqr | -0.0017 | 0.0017 | 14.9914 |
| loose_huber_basis_core_alpha0.01 | huber | actual_log | basis_relaxed_missing | 0.0000 | 0.0000 | 14.9914 |
| loose_huber_basis_core_alpha0.1 | huber | actual_log | current_70_30 | 0.8625 | 0.8625 | 14.9912 |
| loose_huber_basis_core_alpha0.1 | huber | actual_log | basis_relaxed_unit_area_log | 0.4560 | 0.4560 | 14.9912 |
| loose_huber_basis_core_alpha0.1 | huber | actual_log | shrunk_huber_refit | -0.2590 | 0.2590 | 14.9912 |
| loose_huber_basis_core_alpha0.1 | huber | actual_log | shrunk_svc_prior | 0.2273 | 0.2273 | 14.9912 |
| loose_huber_basis_core_alpha0.1 | huber | actual_log | ppv8_defensive | 0.1711 | 0.1711 | 14.9912 |
| loose_huber_basis_core_alpha0.1 | huber | actual_log | svc_fallback | -0.1525 | 0.1525 | 14.9912 |
| loose_huber_basis_core_alpha0.1 | huber | actual_log | log_area | 0.0374 | 0.0374 | 14.9912 |
| loose_huber_basis_core_alpha0.1 | huber | actual_log | basis_relaxed_price_log | -0.0305 | 0.0305 | 14.9912 |
| loose_huber_basis_core_alpha0.1 | huber | actual_log | basis_relaxed_n_log | -0.0149 | 0.0149 | 14.9912 |
| loose_huber_basis_core_alpha0.1 | huber | actual_log | basis_relaxed_iqr | -0.0014 | 0.0014 | 14.9912 |
| loose_huber_basis_core_alpha0.1 | huber | actual_log | basis_relaxed_missing | 0.0000 | 0.0000 | 14.9912 |
| loose_ridge_basis_core_alpha0.1 | ridge | actual_log | current_70_30 | 1.2646 | 1.2646 | 15.0033 |
| loose_ridge_basis_core_alpha0.1 | ridge | actual_log | svc_fallback | -0.4331 | 0.4331 | 15.0033 |
| loose_ridge_basis_core_alpha0.1 | ridge | actual_log | basis_relaxed_unit_area_log | 0.4104 | 0.4104 | 15.0033 |
| loose_ridge_basis_core_alpha0.1 | ridge | actual_log | shrunk_huber_refit | -0.4091 | 0.4091 | 15.0033 |
| loose_ridge_basis_core_alpha0.1 | ridge | actual_log | shrunk_svc_prior | 0.3592 | 0.3592 | 15.0033 |
| loose_ridge_basis_core_alpha0.1 | ridge | actual_log | ppv8_defensive | 0.1444 | 0.1444 | 15.0033 |
| loose_ridge_basis_core_alpha0.1 | ridge | actual_log | basis_relaxed_price_log | -0.0994 | 0.0994 | 15.0033 |
| loose_ridge_basis_core_alpha0.1 | ridge | actual_log | log_area | 0.0744 | 0.0744 | 15.0033 |
| loose_ridge_basis_core_alpha0.1 | ridge | actual_log | basis_relaxed_n_log | -0.0236 | 0.0236 | 15.0033 |
| loose_ridge_basis_core_alpha0.1 | ridge | actual_log | basis_relaxed_iqr | -0.0083 | 0.0083 | 15.0033 |
| loose_ridge_basis_core_alpha0.1 | ridge | actual_log | basis_relaxed_missing | 0.0000 | 0.0000 | 15.0033 |
| loose_ridge_basis_core_alpha1 | ridge | actual_log | current_70_30 | 0.4632 | 0.4632 | 15.0033 |
| loose_ridge_basis_core_alpha1 | ridge | actual_log | basis_relaxed_unit_area_log | 0.4222 | 0.4222 | 15.0033 |
| loose_ridge_basis_core_alpha1 | ridge | actual_log | ppv8_defensive | 0.3653 | 0.3653 | 15.0033 |
| loose_ridge_basis_core_alpha1 | ridge | actual_log | shrunk_huber_refit | -0.3505 | 0.3505 | 15.0033 |
| loose_ridge_basis_core_alpha1 | ridge | actual_log | shrunk_svc_prior | 0.3261 | 0.3261 | 15.0033 |
| loose_ridge_basis_core_alpha1 | ridge | actual_log | svc_fallback | 0.1022 | 0.1022 | 15.0033 |
| loose_ridge_basis_core_alpha1 | ridge | actual_log | basis_relaxed_price_log | -0.0803 | 0.0803 | 15.0033 |
| loose_ridge_basis_core_alpha1 | ridge | actual_log | log_area | 0.0651 | 0.0651 | 15.0033 |
| loose_ridge_basis_core_alpha1 | ridge | actual_log | basis_relaxed_n_log | -0.0248 | 0.0248 | 15.0033 |
| loose_ridge_basis_core_alpha1 | ridge | actual_log | basis_relaxed_iqr | -0.0064 | 0.0064 | 15.0033 |
| loose_ridge_basis_core_alpha1 | ridge | actual_log | basis_relaxed_missing | 0.0000 | 0.0000 | 15.0033 |
| loose_ridge_basis_core_alpha10 | ridge | actual_log | basis_relaxed_unit_area_log | 0.4007 | 0.4007 | 15.0033 |
| loose_ridge_basis_core_alpha10 | ridge | actual_log | ppv8_defensive | 0.3213 | 0.3213 | 15.0033 |
| loose_ridge_basis_core_alpha10 | ridge | actual_log | current_70_30 | 0.2843 | 0.2843 | 15.0033 |
| loose_ridge_basis_core_alpha10 | ridge | actual_log | svc_fallback | 0.2277 | 0.2277 | 15.0033 |
| loose_ridge_basis_core_alpha10 | ridge | actual_log | shrunk_svc_prior | 0.1831 | 0.1831 | 15.0033 |

## 7. 기준가 coverage

| policy | split | level | rows | covered_rows | covered_share | median_n_when_covered |
| --- | --- | --- | --- | --- | --- | --- |
| loose | validation | artist_medium_support_size | 519 | 310 | 0.5973 | 6.0000 |
| loose | validation | artist_size | 519 | 370 | 0.7129 | 6.0000 |
| loose | validation | artist | 519 | 519 | 1.0000 | 12.0000 |
| loose | validation | medium_support_size | 519 | 479 | 0.9229 | 875.0000 |
| loose | validation | medium_category_support_size | 519 | 479 | 0.9229 | 875.0000 |
| loose | validation | medium_size | 519 | 504 | 0.9711 | 1600.0000 |
| loose | test | artist_medium_support_size | 607 | 354 | 0.5832 | 7.0000 |
| loose | test | artist_size | 607 | 433 | 0.7133 | 7.0000 |
| loose | test | artist | 607 | 607 | 1.0000 | 13.0000 |
| loose | test | medium_support_size | 607 | 576 | 0.9489 | 938.5000 |
| loose | test | medium_category_support_size | 607 | 576 | 0.9489 | 938.5000 |
| loose | test | medium_size | 607 | 593 | 0.9769 | 1606.0000 |
| loose | 0604_ex50 | artist_medium_support_size | 829 | 182 | 0.2195 | 4.5000 |
| loose | 0604_ex50 | artist_size | 829 | 494 | 0.5959 | 6.0000 |
| loose | 0604_ex50 | artist | 829 | 755 | 0.9107 | 12.0000 |
| loose | 0604_ex50 | medium_support_size | 829 | 452 | 0.5452 | 1277.0000 |
| loose | 0604_ex50 | medium_category_support_size | 829 | 452 | 0.5452 | 1277.0000 |
| loose | 0604_ex50 | medium_size | 829 | 582 | 0.7021 | 1402.0000 |
| default | validation | artist_medium_support_size | 519 | 202 | 0.3892 | 8.0000 |
| default | validation | artist_size | 519 | 267 | 0.5145 | 9.0000 |
| default | validation | artist | 519 | 519 | 1.0000 | 12.0000 |
| default | validation | medium_support_size | 519 | 469 | 0.9037 | 894.0000 |
| default | validation | medium_category_support_size | 519 | 469 | 0.9037 | 894.0000 |
| default | validation | medium_size | 519 | 502 | 0.9672 | 1600.0000 |
| default | test | artist_medium_support_size | 607 | 247 | 0.4069 | 8.0000 |
| default | test | artist_size | 607 | 312 | 0.5140 | 9.0000 |
| default | test | artist | 607 | 607 | 1.0000 | 13.0000 |
| default | test | medium_support_size | 607 | 552 | 0.9094 | 983.0000 |
| default | test | medium_category_support_size | 607 | 552 | 0.9094 | 983.0000 |
| default | test | medium_size | 607 | 589 | 0.9703 | 1606.0000 |
| default | 0604_ex50 | artist_medium_support_size | 829 | 91 | 0.1098 | 7.0000 |
| default | 0604_ex50 | artist_size | 829 | 315 | 0.3800 | 8.0000 |
| default | 0604_ex50 | artist | 829 | 727 | 0.8770 | 12.0000 |
| default | 0604_ex50 | medium_support_size | 829 | 429 | 0.5175 | 1277.0000 |
| default | 0604_ex50 | medium_category_support_size | 829 | 429 | 0.5175 | 1277.0000 |
| default | 0604_ex50 | medium_size | 829 | 576 | 0.6948 | 1402.0000 |

## 8. 잔차/큰 오차 요약

| split | candidate | median_residual_log | mean_residual_log | residual_std | over_2x_n | under_half_n | ape_gt_100pct_n |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_ex50 | current_70_30 | 0.0782 | 0.3370 | 1.2685 | 30 | 153 | 30 |
| 0604_ex50 | hcoef2_size_reliability_cap005_s050 | 0.0608 | 0.3278 | 1.2668 | 26 | 152 | 26 |
| 0604_ex50 | loose_huber_basis_core_alpha0.1 | -0.0142 | 0.1387 | 0.7986 | 26 | 89 | 26 |
| 0604_ex50 | loose_ridge_basis_core_alpha10 | 0.0138 | 0.1881 | 0.8220 | 20 | 104 | 20 |
| 0604_ex50 | strict_ridge_basis_level_signals_alpha1 | -0.0154 | 0.1391 | 1.0601 | 49 | 86 | 49 |
| test | current_70_30 | -0.0006 | -0.0119 | 0.3998 | 24 | 17 | 24 |
| test | hcoef2_size_reliability_cap005_s050 | -0.0039 | -0.0148 | 0.3989 | 26 | 17 | 26 |
| test | loose_huber_basis_core_alpha0.1 | -0.0012 | -0.0163 | 0.3899 | 25 | 14 | 25 |
| test | loose_ridge_basis_core_alpha10 | -0.0224 | -0.0266 | 0.3897 | 25 | 15 | 25 |
| test | strict_ridge_basis_level_signals_alpha1 | -0.0179 | -0.0270 | 0.4104 | 26 | 17 | 26 |
| validation | current_70_30 | 0.0027 | 0.0209 | 0.3289 | 9 | 11 | 9 |
| validation | hcoef2_size_reliability_cap005_s050 | 0.0021 | 0.0181 | 0.3250 | 9 | 10 | 9 |
| validation | loose_huber_basis_core_alpha0.1 | -0.0042 | 0.0108 | 0.3183 | 8 | 11 | 8 |
| validation | loose_ridge_basis_core_alpha10 | -0.0205 | -0.0007 | 0.3222 | 10 | 12 | 10 |
| validation | strict_ridge_basis_level_signals_alpha1 | -0.0122 | 0.0010 | 0.3197 | 7 | 10 | 7 |

## 9. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/residual_analysis.csv`
- `outputs/coverage_summary.csv`
- `outputs/selected_validation_candidates.csv`
- `artifacts/experiment_config.json`