# PP-WMIN3 Warm min1 70:30 기준가와 HCOEF 안정 보정 재검증

- 작성일: 2026-06-12 20:35
- 목적: WMIN2의 min1 SVC/70:30 개선이 HCOEF 안정 보정 단계에서도 유지되는지 확인한다.
- selection 기준: validation row/artist OOF. fixed test는 최종 확인용.
- partial 모드: min1 `current_70_30`과 `svc_fallback`만 교체하고 기존 raw/shrunk SVC prior는 유지한다.
- svc_proxy 모드: raw/shrunk SVC prior도 min1 SVC로 치환해 전체 SVC 교체에 가까운 proxy를 본다.

## 1. 결론 요약

- validation artist OOF 최상위: `wmin2_svc_numeric_seed_mean_min1` `0.0948/0.1856/0.6060`.
- 재학습 HCOEF 최상위: `wmin3_min1_hcoef_refit_partial` artist OOF 평균 `0.1026/0.1795/0.5733`.
- min1 70:30 자체가 기존 HCOEF 안정 후보보다 강해지는지와, 그 위에 기존 HCOEF 잔차 보정을 다시 얹을 가치가 있는지를 분리해 판단한다.

## 2. Repeated Validation Summary

| variant_mode | validation_scheme | candidate | MdAPE_mean | MAPE_mean | p95_APE_mean | old_stable_MdAPE_win_rate | old_stable_MAPE_win_rate | old_stable_p95_win_rate | new_basis_MdAPE_win_rate | new_basis_MAPE_win_rate | new_basis_p95_win_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| partial | artist_oof | wmin2_svc_numeric_seed_mean_min1 | 0.0948 | 0.1856 | 0.6060 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| svc_proxy | artist_oof | wmin2_svc_numeric_seed_mean_min1 | 0.0948 | 0.1856 | 0.6060 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| partial | artist_oof | wmin3_min1_hcoef_refit_partial | 0.1026 | 0.1795 | 0.5733 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| svc_proxy | artist_oof | wmin3_min1_hcoef_refit_svc_proxy | 0.1029 | 0.1796 | 0.5746 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| partial | artist_oof | wmin3_min1_hcoef_delta_transplant | 0.1059 | 0.1801 | 0.5827 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| svc_proxy | artist_oof | wmin3_min1_hcoef_delta_transplant | 0.1059 | 0.1801 | 0.5827 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| partial | artist_oof | wmin3_min1_70_30_basis | 0.1075 | 0.1806 | 0.5819 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| svc_proxy | artist_oof | wmin3_min1_70_30_basis | 0.1075 | 0.1806 | 0.5819 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| partial | artist_oof | old_hcoef_stable_min5 | 0.1260 | 0.2082 | 0.6479 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| svc_proxy | artist_oof | old_hcoef_stable_min5 | 0.1260 | 0.2082 | 0.6479 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| partial | artist_oof | old_current_70_30_min5 | 0.1305 | 0.2110 | 0.6580 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| svc_proxy | artist_oof | old_current_70_30_min5 | 0.1305 | 0.2110 | 0.6580 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| partial | row_oof | wmin2_svc_numeric_seed_mean_min1 | 0.0948 | 0.1856 | 0.6060 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| svc_proxy | row_oof | wmin2_svc_numeric_seed_mean_min1 | 0.0948 | 0.1856 | 0.6060 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| partial | row_oof | wmin3_min1_hcoef_refit_partial | 0.1021 | 0.1794 | 0.5727 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| svc_proxy | row_oof | wmin3_min1_hcoef_refit_svc_proxy | 0.1024 | 0.1794 | 0.5748 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| partial | row_oof | wmin3_min1_hcoef_delta_transplant | 0.1059 | 0.1801 | 0.5827 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| svc_proxy | row_oof | wmin3_min1_hcoef_delta_transplant | 0.1059 | 0.1801 | 0.5827 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| partial | row_oof | wmin3_min1_70_30_basis | 0.1075 | 0.1806 | 0.5819 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| svc_proxy | row_oof | wmin3_min1_70_30_basis | 0.1075 | 0.1806 | 0.5819 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| partial | row_oof | old_hcoef_stable_min5 | 0.1260 | 0.2082 | 0.6479 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| svc_proxy | row_oof | old_hcoef_stable_min5 | 0.1260 | 0.2082 | 0.6479 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| partial | row_oof | old_current_70_30_min5 | 0.1305 | 0.2110 | 0.6580 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| svc_proxy | row_oof | old_current_70_30_min5 | 0.1305 | 0.2110 | 0.6580 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## 3. Fixed Confirmation

| variant_mode | split | candidate | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_old_stable | delta_MAPE_vs_old_stable | delta_p95_APE_vs_old_stable | delta_MdAPE_vs_new_basis | delta_MAPE_vs_new_basis | delta_p95_APE_vs_new_basis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| partial | validation | old_current_70_30_min5 | 0.1305 | 0.2110 | 0.6580 | 0.3292 | 0.0045 | 0.0028 | 0.0101 | 0.0230 | 0.0305 | 0.0762 |
| partial | validation | old_hcoef_stable_min5 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0.0185 | 0.0276 | 0.0661 |
| partial | validation | wmin2_svc_numeric_seed_mean_min1 | 0.0948 | 0.1856 | 0.6060 | 0.3142 | -0.0312 | -0.0226 | -0.0419 | -0.0127 | 0.0051 | 0.0242 |
| partial | validation | wmin3_min1_70_30_basis | 0.1075 | 0.1806 | 0.5819 | 0.2996 | -0.0185 | -0.0276 | -0.0661 | 0.0000 | 0.0000 | 0.0000 |
| partial | validation | wmin3_min1_hcoef_delta_transplant | 0.1059 | 0.1801 | 0.5827 | 0.2972 | -0.0201 | -0.0281 | -0.0652 | -0.0016 | -0.0004 | 0.0009 |
| partial | validation | wmin3_min1_hcoef_refit_partial | 0.1016 | 0.1784 | 0.5713 | 0.2973 | -0.0244 | -0.0298 | -0.0767 | -0.0059 | -0.0022 | -0.0106 |
| partial | test | old_current_70_30_min5 | 0.1405 | 0.2748 | 0.8331 | 0.3996 | 0.0017 | 0.0018 | 0.0267 | 0.0322 | 0.0351 | 0.0505 |
| partial | test | old_hcoef_stable_min5 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0.0305 | 0.0333 | 0.0237 |
| partial | test | wmin2_svc_numeric_seed_mean_min1 | 0.1116 | 0.2537 | 0.8032 | 0.3924 | -0.0272 | -0.0193 | -0.0031 | 0.0033 | 0.0140 | 0.0206 |
| partial | test | wmin3_min1_70_30_basis | 0.1083 | 0.2397 | 0.7826 | 0.3765 | -0.0305 | -0.0333 | -0.0237 | 0.0000 | 0.0000 | 0.0000 |
| partial | test | wmin3_min1_hcoef_delta_transplant | 0.1107 | 0.2395 | 0.7787 | 0.3772 | -0.0282 | -0.0334 | -0.0276 | 0.0023 | -0.0001 | -0.0039 |
| partial | test | wmin3_min1_hcoef_refit_partial | 0.1066 | 0.2393 | 0.7792 | 0.3769 | -0.0322 | -0.0337 | -0.0272 | -0.0017 | -0.0004 | -0.0034 |
| svc_proxy | validation | old_current_70_30_min5 | 0.1305 | 0.2110 | 0.6580 | 0.3292 | 0.0045 | 0.0028 | 0.0101 | 0.0230 | 0.0305 | 0.0762 |
| svc_proxy | validation | old_hcoef_stable_min5 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0.0185 | 0.0276 | 0.0661 |
| svc_proxy | validation | wmin2_svc_numeric_seed_mean_min1 | 0.0948 | 0.1856 | 0.6060 | 0.3142 | -0.0312 | -0.0226 | -0.0419 | -0.0127 | 0.0051 | 0.0242 |
| svc_proxy | validation | wmin3_min1_70_30_basis | 0.1075 | 0.1806 | 0.5819 | 0.2996 | -0.0185 | -0.0276 | -0.0661 | 0.0000 | 0.0000 | 0.0000 |
| svc_proxy | validation | wmin3_min1_hcoef_delta_transplant | 0.1059 | 0.1801 | 0.5827 | 0.2972 | -0.0201 | -0.0281 | -0.0652 | -0.0016 | -0.0004 | 0.0009 |
| svc_proxy | validation | wmin3_min1_hcoef_refit_svc_proxy | 0.1008 | 0.1787 | 0.5765 | 0.2975 | -0.0252 | -0.0295 | -0.0715 | -0.0067 | -0.0019 | -0.0054 |
| svc_proxy | test | old_current_70_30_min5 | 0.1405 | 0.2748 | 0.8331 | 0.3996 | 0.0017 | 0.0018 | 0.0267 | 0.0322 | 0.0351 | 0.0505 |
| svc_proxy | test | old_hcoef_stable_min5 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0.0305 | 0.0333 | 0.0237 |
| svc_proxy | test | wmin2_svc_numeric_seed_mean_min1 | 0.1116 | 0.2537 | 0.8032 | 0.3924 | -0.0272 | -0.0193 | -0.0031 | 0.0033 | 0.0140 | 0.0206 |
| svc_proxy | test | wmin3_min1_70_30_basis | 0.1083 | 0.2397 | 0.7826 | 0.3765 | -0.0305 | -0.0333 | -0.0237 | 0.0000 | 0.0000 | 0.0000 |
| svc_proxy | test | wmin3_min1_hcoef_delta_transplant | 0.1107 | 0.2395 | 0.7787 | 0.3772 | -0.0282 | -0.0334 | -0.0276 | 0.0023 | -0.0001 | -0.0039 |
| svc_proxy | test | wmin3_min1_hcoef_refit_svc_proxy | 0.1095 | 0.2393 | 0.7809 | 0.3767 | -0.0293 | -0.0337 | -0.0255 | 0.0012 | -0.0004 | -0.0017 |

## 4. HCOEF Refit Coefficients

| candidate | source_candidate | feature | coefficient_on_scaled_feature | abs_coefficient | alpha | cap | strength | experiment_id | variant_mode |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | current_shrunk_huber_gap | 0.0500 | 0.0500 | 0.0100 | 0.0500 | 0.5000 | PP-WMIN3 | partial |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | log_area | 0.0223 | 0.0223 | 0.0100 | 0.0500 | 0.5000 | PP-WMIN3 | partial |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | shrunk_huber_refit | -0.0222 | 0.0222 | 0.0100 | 0.0500 | 0.5000 | PP-WMIN3 | partial |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | shrunk_svc_prior | 0.0193 | 0.0193 | 0.0100 | 0.0500 | 0.5000 | PP-WMIN3 | partial |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | svc_group_n_log | -0.0151 | 0.0151 | 0.0100 | 0.0500 | 0.5000 | PP-WMIN3 | partial |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | current_ppv8_gap | 0.0129 | 0.0129 | 0.0100 | 0.0500 | 0.5000 | PP-WMIN3 | partial |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | ppv8_defensive | -0.0109 | 0.0109 | 0.0100 | 0.0500 | 0.5000 | PP-WMIN3 | partial |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | raw_shrunk_prior_gap | 0.0100 | 0.0100 | 0.0100 | 0.0500 | 0.5000 | PP-WMIN3 | partial |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | svc_fallback | -0.0074 | 0.0074 | 0.0100 | 0.0500 | 0.5000 | PP-WMIN3 | partial |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | svc_prior_iqr | 0.0047 | 0.0047 | 0.0100 | 0.0500 | 0.5000 | PP-WMIN3 | partial |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | current_shrunk_huber_gap | 0.0462 | 0.0462 | 0.0100 | 0.0500 | 0.5000 | PP-WMIN3 | svc_proxy |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | svc_group_n_log | -0.0157 | 0.0157 | 0.0100 | 0.0500 | 0.5000 | PP-WMIN3 | svc_proxy |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | current_ppv8_gap | 0.0140 | 0.0140 | 0.0100 | 0.0500 | 0.5000 | PP-WMIN3 | svc_proxy |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | log_area | 0.0126 | 0.0126 | 0.0100 | 0.0500 | 0.5000 | PP-WMIN3 | svc_proxy |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | shrunk_huber_refit | -0.0121 | 0.0121 | 0.0100 | 0.0500 | 0.5000 | PP-WMIN3 | svc_proxy |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | svc_prior_iqr | 0.0050 | 0.0050 | 0.0100 | 0.0500 | 0.5000 | PP-WMIN3 | svc_proxy |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | ppv8_defensive | -0.0023 | 0.0023 | 0.0100 | 0.0500 | 0.5000 | PP-WMIN3 | svc_proxy |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | svc_fallback | 0.0011 | 0.0011 | 0.0100 | 0.0500 | 0.5000 | PP-WMIN3 | svc_proxy |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | shrunk_svc_prior | 0.0011 | 0.0011 | 0.0100 | 0.0500 | 0.5000 | PP-WMIN3 | svc_proxy |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | raw_shrunk_prior_gap | 0.0000 | 0.0000 | 0.0100 | 0.0500 | 0.5000 | PP-WMIN3 | svc_proxy |

## 5. 다음 판단

- refit 후보가 min1 70:30보다 validation OOF에서 안정적으로 좋아지면 PP-WMIN4 decision layer 재학습 대상에 포함한다.
- refit 후보가 min1 70:30보다 약하면 WMIN4는 min1 70:30 또는 min1 SVC 기반 PP258 decision 재학습 중심으로 진행한다.
