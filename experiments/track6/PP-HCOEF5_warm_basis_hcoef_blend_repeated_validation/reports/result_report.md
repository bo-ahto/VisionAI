# PP-HCOEF5 Warm 기준가-HCOEF 안정 결합 반복 검증

- 작성일: 2026-06-07 22:45
- 목적: HCOEF4의 loose 기준가 Huber 후보를 HCOEF3 안정 후보 위에 제한적으로 결합해 p95 악화 없이 MdAPE/MAPE를 개선할 수 있는지 확인.
- 기준 후보: `hcoef2_size_reliability_cap005_s050`.
- 검증 방식: validation row OOF 12회, artist OOF 12회, 각 5 folds. fixed test/0604는 확인용.

## 1. 실행 결론

- 반복 OOF 신호는 있으나 fixed guard 미통과: `loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.03_s0.25`
- fixed test만 좋은 후보는 채택하지 않고 반복 OOF와 p95 guard를 함께 본다.

## 2. 반복 OOF 요약

| validation_scheme | candidate | mean_delta_MdAPE_vs_hcoef2 | mean_delta_MAPE_vs_hcoef2 | mean_delta_p95_APE_vs_hcoef2 | std_delta_MdAPE_vs_hcoef2 | MdAPE_improve_prob_vs_hcoef2 | MAPE_improve_prob_vs_hcoef2 | p95_improve_prob_vs_hcoef2 | all3_improve_prob_vs_hcoef2 | mean_improve_count_vs_hcoef2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| row_oof | loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.03_s0.25 | -0.0021 | -0.0012 | -0.0046 | 0.0011 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 3.0000 |
| row_oof | loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.03_s0.25 | -0.0019 | -0.0010 | -0.0047 | 0.0010 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 3.0000 |
| row_oof | loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.03_s0.25 | -0.0019 | -0.0011 | -0.0048 | 0.0011 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 3.0000 |
| row_oof | loose_basis_core_huber_alpha0p1 | -0.0063 | -0.0029 | -0.0139 | 0.0022 | 1.0000 | 1.0000 | 0.9167 | 0.9167 | 2.9167 |
| row_oof | loose_basis_core_huber_alpha0p01 | -0.0060 | -0.0027 | -0.0117 | 0.0026 | 1.0000 | 1.0000 | 0.9167 | 0.9167 | 2.9167 |
| row_oof | loose_basis_gap_huber_alpha0p1 | -0.0057 | -0.0021 | -0.0154 | 0.0030 | 1.0000 | 1.0000 | 0.9167 | 0.9167 | 2.9167 |
| artist_oof | loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.03_s0.25 | -0.0015 | -0.0009 | -0.0037 | 0.0010 | 1.0000 | 1.0000 | 0.9167 | 0.9167 | 2.9167 |
| row_oof | loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.08_s0.50 | -0.0056 | -0.0034 | -0.0039 | 0.0019 | 1.0000 | 1.0000 | 0.8333 | 0.8333 | 2.8333 |
| artist_oof | loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.03_s0.25 | -0.0018 | -0.0011 | -0.0037 | 0.0010 | 1.0000 | 1.0000 | 0.8333 | 0.8333 | 2.8333 |
| artist_oof | loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.03_s0.25 | -0.0017 | -0.0011 | -0.0038 | 0.0010 | 1.0000 | 1.0000 | 0.8333 | 0.8333 | 2.8333 |
| row_oof | loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.08_s0.75 | -0.0070 | -0.0047 | -0.0042 | 0.0025 | 1.0000 | 1.0000 | 0.7500 | 0.7500 | 2.7500 |
| row_oof | loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.08_s0.75 | -0.0066 | -0.0045 | -0.0034 | 0.0026 | 1.0000 | 1.0000 | 0.7500 | 0.7500 | 2.7500 |
| artist_oof | loose_basis_core_huber_alpha0p01 | -0.0059 | -0.0007 | -0.0120 | 0.0028 | 0.9167 | 0.8333 | 0.8333 | 0.7500 | 2.5833 |
| artist_oof | loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.08_s0.75 | -0.0056 | -0.0032 | -0.0056 | 0.0026 | 1.0000 | 1.0000 | 0.7500 | 0.7500 | 2.7500 |
| row_oof | loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.08_s0.50 | -0.0056 | -0.0038 | -0.0037 | 0.0015 | 1.0000 | 1.0000 | 0.7500 | 0.7500 | 2.7500 |
| row_oof | loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.03_s0.50 | -0.0043 | -0.0022 | -0.0026 | 0.0012 | 1.0000 | 1.0000 | 0.7500 | 0.7500 | 2.7500 |
| artist_oof | loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.03_s0.50 | -0.0042 | -0.0020 | -0.0037 | 0.0020 | 1.0000 | 1.0000 | 0.7500 | 0.7500 | 2.7500 |
| artist_oof | loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.03_s0.50 | -0.0041 | -0.0020 | -0.0038 | 0.0021 | 1.0000 | 1.0000 | 0.7500 | 0.7500 | 2.7500 |
| row_oof | loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.03_s0.50 | -0.0040 | -0.0021 | -0.0030 | 0.0016 | 1.0000 | 1.0000 | 0.7500 | 0.7500 | 2.7500 |
| row_oof | loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.03_s0.50 | -0.0039 | -0.0019 | -0.0027 | 0.0015 | 1.0000 | 1.0000 | 0.7500 | 0.7500 | 2.7500 |
| artist_oof | loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.03_s0.50 | -0.0035 | -0.0016 | -0.0036 | 0.0026 | 1.0000 | 1.0000 | 0.7500 | 0.7500 | 2.7500 |
| row_oof | loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.05_s0.25 | -0.0033 | -0.0017 | -0.0024 | 0.0011 | 1.0000 | 1.0000 | 0.7500 | 0.7500 | 2.7500 |
| row_oof | loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.05_s0.25 | -0.0032 | -0.0016 | -0.0023 | 0.0014 | 1.0000 | 1.0000 | 0.7500 | 0.7500 | 2.7500 |
| row_oof | loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.08_s0.75 | -0.0068 | -0.0040 | -0.0019 | 0.0027 | 1.0000 | 1.0000 | 0.6667 | 0.6667 | 2.6667 |
| artist_oof | loose_basis_core_huber_alpha0p1 | -0.0057 | -0.0010 | -0.0128 | 0.0037 | 0.8333 | 0.8333 | 0.8333 | 0.6667 | 2.5000 |
| row_oof | loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.08_s0.50 | -0.0055 | -0.0037 | -0.0039 | 0.0016 | 1.0000 | 1.0000 | 0.6667 | 0.6667 | 2.6667 |
| artist_oof | loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.08_s0.50 | -0.0052 | -0.0029 | -0.0002 | 0.0018 | 1.0000 | 1.0000 | 0.6667 | 0.6667 | 2.6667 |
| artist_oof | loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.08_s0.25 | -0.0046 | -0.0022 | -0.0009 | 0.0018 | 1.0000 | 1.0000 | 0.6667 | 0.6667 | 2.6667 |

## 3. 후보 선택표

| candidate | row_all3_prob | artist_all3_prob | row_delta_MdAPE | artist_delta_MdAPE | test_delta_MdAPE | test_delta_MAPE | test_delta_p95_APE | ops0604_delta_MdAPE | ops0604_delta_MAPE | ops0604_delta_p95_APE | passes_repeat_gate | passes_fixed_guard |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.03_s0.25 | 1.0000 | 0.9167 | -0.0019 | -0.0015 | 0.0012 | -0.0013 | 0.0009 | -0.0051 | -0.0028 | -0.0028 | True | False |
| loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.05_s0.75 | 0.5000 | 0.3333 | -0.0056 | -0.0059 | -0.0004 | -0.0049 | 0.0060 | -0.0110 | -0.0126 | -0.0262 | False | True |
| loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.05_s0.75 | 0.5000 | 0.4167 | -0.0058 | -0.0063 | -0.0001 | -0.0049 | 0.0066 | -0.0110 | -0.0126 | -0.0262 | False | True |
| loose_basis_gap_huber_alpha0p1 | 0.9167 | 0.5833 | -0.0057 | -0.0052 | -0.0042 | -0.0102 | 0.1046 | -0.0393 | -0.0314 | -0.0094 | False | False |
| loose_basis_core_huber_alpha0p1 | 0.9167 | 0.6667 | -0.0063 | -0.0057 | -0.0042 | -0.0112 | 0.0853 | -0.0427 | -0.0296 | -0.0321 | False | False |
| loose_basis_core_huber_alpha0p01 | 0.9167 | 0.7500 | -0.0060 | -0.0059 | -0.0041 | -0.0110 | 0.0888 | -0.0439 | -0.0291 | -0.0293 | False | False |
| loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.08_s0.75 | 0.7500 | 0.5000 | -0.0070 | -0.0065 | -0.0032 | -0.0065 | 0.0244 | -0.0189 | -0.0184 | -0.0404 | False | False |
| loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.08_s0.75 | 0.7500 | 0.5000 | -0.0066 | -0.0062 | -0.0030 | -0.0065 | 0.0241 | -0.0189 | -0.0184 | -0.0403 | False | False |
| hcoef2_size_reliability_cap005_s050 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | False |
| loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.08_s0.75 | 0.6667 | 0.7500 | -0.0068 | -0.0056 | 0.0002 | -0.0062 | 0.0246 | -0.0192 | -0.0188 | -0.0396 | False | False |
| loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.08_s1.00 | 0.5000 | 0.3333 | -0.0055 | -0.0064 | 0.0004 | -0.0078 | 0.0323 | -0.0306 | -0.0223 | -0.0440 | False | False |
| loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.08_s1.00 | 0.4167 | 0.2500 | -0.0059 | -0.0065 | 0.0004 | -0.0077 | 0.0325 | -0.0306 | -0.0223 | -0.0440 | False | False |
| loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.03_s1.00 | 0.3333 | 0.4167 | -0.0060 | -0.0058 | 0.0006 | -0.0041 | 0.0103 | -0.0098 | -0.0102 | -0.0147 | False | False |
| loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.03_s1.00 | 0.3333 | 0.3333 | -0.0063 | -0.0061 | 0.0007 | -0.0041 | 0.0111 | -0.0096 | -0.0102 | -0.0148 | False | False |
| loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.03_s0.75 | 0.5000 | 0.4167 | -0.0055 | -0.0060 | 0.0007 | -0.0033 | 0.0075 | -0.0131 | -0.0079 | -0.0045 | False | False |
| loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.08_s0.25 | 0.6667 | 0.5833 | -0.0035 | -0.0032 | 0.0012 | -0.0025 | 0.0003 | -0.0115 | -0.0069 | -0.0045 | False | False |
| loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.03_s0.75 | 0.5000 | 0.4167 | -0.0052 | -0.0059 | 0.0013 | -0.0033 | 0.0069 | -0.0132 | -0.0079 | -0.0045 | False | False |
| loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.05_s0.25 | 0.7500 | 0.5833 | -0.0032 | -0.0025 | 0.0014 | -0.0019 | 0.0006 | -0.0088 | -0.0045 | -0.0045 | False | False |
| loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.03_s0.25 | 1.0000 | 0.8333 | -0.0019 | -0.0017 | 0.0014 | -0.0013 | 0.0005 | -0.0037 | -0.0028 | -0.0028 | False | False |
| loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.03_s0.25 | 1.0000 | 0.8333 | -0.0021 | -0.0018 | 0.0014 | -0.0013 | 0.0006 | -0.0037 | -0.0028 | -0.0028 | False | False |

## 4. Fixed test 상위 후보

| candidate | method | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_hcoef2 | delta_MAPE_vs_hcoef2 | delta_p95_APE_vs_hcoef2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| loose_basis_gap_huber_alpha0p1 | basis_huber_full_validation | 0.1346 | 0.2628 | 0.9110 | 0.3902 | -0.0042 | -0.0102 | 0.1046 |
| loose_basis_core_huber_alpha0p1 | basis_huber_full_validation | 0.1346 | 0.2618 | 0.8916 | 0.3899 | -0.0042 | -0.0112 | 0.0853 |
| loose_basis_core_huber_alpha0p01 | basis_huber_full_validation | 0.1347 | 0.2620 | 0.8952 | 0.3896 | -0.0041 | -0.0110 | 0.0888 |
| loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.08_s0.75 | basis_on_hcoef2_capped_blend | 0.1356 | 0.2665 | 0.8308 | 0.3941 | -0.0032 | -0.0065 | 0.0244 |
| loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.08_s0.75 | basis_on_hcoef2_capped_blend | 0.1358 | 0.2665 | 0.8304 | 0.3939 | -0.0030 | -0.0065 | 0.0241 |
| loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.05_s0.75 | basis_on_hcoef2_capped_blend | 0.1384 | 0.2681 | 0.8124 | 0.3951 | -0.0004 | -0.0049 | 0.0060 |
| loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.05_s0.75 | basis_on_hcoef2_capped_blend | 0.1387 | 0.2681 | 0.8130 | 0.3951 | -0.0001 | -0.0049 | 0.0066 |
| hcoef2_size_reliability_cap005_s050 | current_stable_hcoef2 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 |
| loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.08_s0.75 | basis_on_hcoef2_capped_blend | 0.1390 | 0.2668 | 0.8310 | 0.3940 | 0.0002 | -0.0062 | 0.0246 |
| loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.08_s1.00 | basis_on_hcoef2_capped_blend | 0.1392 | 0.2652 | 0.8386 | 0.3930 | 0.0004 | -0.0078 | 0.0323 |
| loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.08_s1.00 | basis_on_hcoef2_capped_blend | 0.1392 | 0.2653 | 0.8389 | 0.3934 | 0.0004 | -0.0077 | 0.0325 |
| loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.03_s1.00 | basis_on_hcoef2_capped_blend | 0.1394 | 0.2689 | 0.8167 | 0.3958 | 0.0006 | -0.0041 | 0.0103 |
| loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.03_s1.00 | basis_on_hcoef2_capped_blend | 0.1395 | 0.2689 | 0.8175 | 0.3957 | 0.0007 | -0.0041 | 0.0111 |
| loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.03_s0.75 | basis_on_hcoef2_capped_blend | 0.1395 | 0.2696 | 0.8139 | 0.3964 | 0.0007 | -0.0033 | 0.0075 |
| loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.08_s0.25 | basis_on_hcoef2_capped_blend | 0.1400 | 0.2704 | 0.8067 | 0.3968 | 0.0012 | -0.0025 | 0.0003 |
| loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.03_s0.25 | basis_on_hcoef2_capped_blend | 0.1400 | 0.2717 | 0.8073 | 0.3979 | 0.0012 | -0.0013 | 0.0009 |
| loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.03_s0.75 | basis_on_hcoef2_capped_blend | 0.1401 | 0.2696 | 0.8133 | 0.3964 | 0.0013 | -0.0033 | 0.0069 |
| loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.05_s0.25 | basis_on_hcoef2_capped_blend | 0.1402 | 0.2711 | 0.8070 | 0.3974 | 0.0014 | -0.0019 | 0.0006 |
| loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.03_s0.25 | basis_on_hcoef2_capped_blend | 0.1403 | 0.2717 | 0.8069 | 0.3979 | 0.0014 | -0.0013 | 0.0005 |
| loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.03_s0.25 | basis_on_hcoef2_capped_blend | 0.1403 | 0.2717 | 0.8070 | 0.3979 | 0.0014 | -0.0013 | 0.0006 |

## 5. 주요 계수

- 계수는 표준화된 피처 기준이다. basis-Huber 후보의 방향성 해석용이다.
| candidate | model_type | target | feature | coefficient_on_scaled_feature | abs_coefficient | intercept |
| --- | --- | --- | --- | --- | --- | --- |
| loose_basis_core_huber_alpha0p1 | huber | actual_log | current_70_30 | 0.8625 | 0.8625 | 14.9912 |
| loose_basis_core_huber_alpha0p1 | huber | actual_log | basis_relaxed_unit_area_log | 0.4560 | 0.4560 | 14.9912 |
| loose_basis_core_huber_alpha0p1 | huber | actual_log | shrunk_huber_refit | -0.2590 | 0.2590 | 14.9912 |
| loose_basis_core_huber_alpha0p1 | huber | actual_log | shrunk_svc_prior | 0.2273 | 0.2273 | 14.9912 |
| loose_basis_core_huber_alpha0p1 | huber | actual_log | ppv8_defensive | 0.1711 | 0.1711 | 14.9912 |
| loose_basis_core_huber_alpha0p1 | huber | actual_log | svc_fallback | -0.1525 | 0.1525 | 14.9912 |
| loose_basis_core_huber_alpha0p1 | huber | actual_log | log_area | 0.0374 | 0.0374 | 14.9912 |
| loose_basis_core_huber_alpha0p1 | huber | actual_log | basis_relaxed_price_log | -0.0305 | 0.0305 | 14.9912 |
| loose_basis_core_huber_alpha0p1 | huber | actual_log | basis_relaxed_n_log | -0.0149 | 0.0149 | 14.9912 |
| loose_basis_core_huber_alpha0p1 | huber | actual_log | basis_relaxed_iqr | -0.0014 | 0.0014 | 14.9912 |
| loose_basis_core_huber_alpha0p1 | huber | actual_log | basis_relaxed_missing | 0.0000 | 0.0000 | 14.9912 |
| loose_basis_core_huber_alpha0p01 | huber | actual_log | current_70_30 | 1.0069 | 1.0069 | 14.9914 |
| loose_basis_core_huber_alpha0p01 | huber | actual_log | basis_relaxed_unit_area_log | 0.4536 | 0.4536 | 14.9914 |
| loose_basis_core_huber_alpha0p01 | huber | actual_log | shrunk_huber_refit | -0.2617 | 0.2617 | 14.9914 |
| loose_basis_core_huber_alpha0p01 | huber | actual_log | svc_fallback | -0.2475 | 0.2475 | 14.9914 |
| loose_basis_core_huber_alpha0p01 | huber | actual_log | shrunk_svc_prior | 0.2272 | 0.2272 | 14.9914 |
| loose_basis_core_huber_alpha0p01 | huber | actual_log | ppv8_defensive | 0.1273 | 0.1273 | 14.9914 |
| loose_basis_core_huber_alpha0p01 | huber | actual_log | log_area | 0.0374 | 0.0374 | 14.9914 |
| loose_basis_core_huber_alpha0p01 | huber | actual_log | basis_relaxed_price_log | -0.0316 | 0.0316 | 14.9914 |
| loose_basis_core_huber_alpha0p01 | huber | actual_log | basis_relaxed_n_log | -0.0149 | 0.0149 | 14.9914 |
| loose_basis_core_huber_alpha0p01 | huber | actual_log | basis_relaxed_iqr | -0.0017 | 0.0017 | 14.9914 |
| loose_basis_core_huber_alpha0p01 | huber | actual_log | basis_relaxed_missing | 0.0000 | 0.0000 | 14.9914 |
| loose_basis_gap_huber_alpha0p1 | huber | actual_log | basis_relaxed_unit_area_log | 0.4497 | 0.4497 | 14.9917 |
| loose_basis_gap_huber_alpha0p1 | huber | actual_log | current_70_30 | 0.3770 | 0.3770 | 14.9917 |
| loose_basis_gap_huber_alpha0p1 | huber | actual_log | basis_relaxed_vs_current_gap | -0.3052 | 0.3052 | 14.9917 |
| loose_basis_gap_huber_alpha0p1 | huber | actual_log | shrunk_huber_refit | -0.2654 | 0.2654 | 14.9917 |
| loose_basis_gap_huber_alpha0p1 | huber | actual_log | shrunk_svc_prior | 0.2276 | 0.2276 | 14.9917 |
| loose_basis_gap_huber_alpha0p1 | huber | actual_log | basis_relaxed_price_log | 0.2265 | 0.2265 | 14.9917 |
| loose_basis_gap_huber_alpha0p1 | huber | actual_log | basis_relaxed_vs_svc_gap | 0.1805 | 0.1805 | 14.9917 |
| loose_basis_gap_huber_alpha0p1 | huber | actual_log | svc_fallback | 0.1350 | 0.1350 | 14.9917 |
| loose_basis_gap_huber_alpha0p1 | huber | actual_log | ppv8_defensive | 0.1298 | 0.1298 | 14.9917 |
| loose_basis_gap_huber_alpha0p1 | huber | actual_log | log_area | 0.0364 | 0.0364 | 14.9917 |
| loose_basis_gap_huber_alpha0p1 | huber | actual_log | svc_group_n_log | -0.0124 | 0.0124 | 14.9917 |
| loose_basis_gap_huber_alpha0p1 | huber | actual_log | basis_relaxed_iqr | -0.0104 | 0.0104 | 14.9917 |
| loose_basis_gap_huber_alpha0p1 | huber | actual_log | svc_prior_iqr | 0.0096 | 0.0096 | 14.9917 |
| loose_basis_gap_huber_alpha0p1 | huber | actual_log | basis_relaxed_n_log | -0.0045 | 0.0045 | 14.9917 |

## 6. 잔차/큰 오차 요약

| split | candidate | median_residual_log | mean_residual_log | residual_std | over_2x_n | under_half_n | ape_gt_100pct_n |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_ex50 | hcoef2_size_reliability_cap005_s050 | 0.0608 | 0.3278 | 1.2668 | 26 | 152 | 26 |
| 0604_ex50 | loose_basis_core_huber_alpha0p01 | -0.0144 | 0.1390 | 0.8012 | 26 | 88 | 26 |
| 0604_ex50 | loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.03_s0.25 | 0.0580 | 0.3269 | 1.2653 | 26 | 151 | 26 |
| 0604_ex50 | loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.03_s0.50 | 0.0614 | 0.3260 | 1.2639 | 24 | 151 | 24 |
| 0604_ex50 | loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.03_s0.75 | 0.0608 | 0.3251 | 1.2625 | 22 | 150 | 22 |
| 0604_ex50 | loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.03_s1.00 | 0.0569 | 0.3242 | 1.2611 | 22 | 144 | 22 |
| 0604_ex50 | loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.05_s0.25 | 0.0584 | 0.3262 | 1.2644 | 26 | 151 | 26 |
| 0604_ex50 | loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.05_s0.50 | 0.0614 | 0.3246 | 1.2620 | 22 | 149 | 22 |
| 0604_ex50 | loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.05_s0.75 | 0.0616 | 0.3230 | 1.2598 | 22 | 143 | 22 |
| 0604_ex50 | loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.05_s1.00 | 0.0624 | 0.3214 | 1.2577 | 21 | 139 | 21 |
| 0604_ex50 | loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.08_s0.25 | 0.0564 | 0.3252 | 1.2630 | 22 | 150 | 22 |
| 0604_ex50 | loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.08_s0.50 | 0.0598 | 0.3226 | 1.2594 | 22 | 143 | 22 |
| 0604_ex50 | loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.08_s0.75 | 0.0595 | 0.3200 | 1.2561 | 21 | 137 | 21 |
| 0604_ex50 | loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.08_s1.00 | 0.0566 | 0.3174 | 1.2529 | 21 | 136 | 21 |
| 0604_ex50 | loose_basis_core_huber_alpha0p1 | -0.0142 | 0.1387 | 0.7986 | 26 | 89 | 26 |
| 0604_ex50 | loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.03_s0.25 | 0.0580 | 0.3269 | 1.2653 | 26 | 151 | 26 |
| 0604_ex50 | loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.03_s0.50 | 0.0614 | 0.3260 | 1.2639 | 24 | 151 | 24 |
| 0604_ex50 | loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.03_s0.75 | 0.0608 | 0.3251 | 1.2624 | 22 | 150 | 22 |
| 0604_ex50 | loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.03_s1.00 | 0.0568 | 0.3242 | 1.2611 | 22 | 144 | 22 |
| 0604_ex50 | loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.05_s0.25 | 0.0584 | 0.3262 | 1.2643 | 26 | 151 | 26 |
| 0604_ex50 | loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.05_s0.50 | 0.0615 | 0.3246 | 1.2620 | 22 | 149 | 22 |
| 0604_ex50 | loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.05_s0.75 | 0.0616 | 0.3230 | 1.2597 | 22 | 143 | 22 |
| 0604_ex50 | loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.05_s1.00 | 0.0624 | 0.3214 | 1.2576 | 21 | 139 | 21 |
| 0604_ex50 | loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.08_s0.25 | 0.0565 | 0.3252 | 1.2630 | 22 | 150 | 22 |
| 0604_ex50 | loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.08_s0.50 | 0.0598 | 0.3226 | 1.2594 | 22 | 143 | 22 |
| 0604_ex50 | loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.08_s0.75 | 0.0595 | 0.3200 | 1.2560 | 21 | 137 | 21 |
| 0604_ex50 | loose_basis_core_huber_alpha0p1_on_hcoef2_cap0.08_s1.00 | 0.0556 | 0.3174 | 1.2529 | 21 | 136 | 21 |
| 0604_ex50 | loose_basis_gap_huber_alpha0p1 | -0.0043 | 0.1504 | 0.8072 | 26 | 90 | 26 |
| 0604_ex50 | loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.03_s0.25 | 0.0580 | 0.3271 | 1.2653 | 26 | 151 | 26 |
| 0604_ex50 | loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.03_s0.50 | 0.0612 | 0.3264 | 1.2639 | 24 | 150 | 24 |
| 0604_ex50 | loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.03_s0.75 | 0.0597 | 0.3257 | 1.2625 | 22 | 149 | 22 |
| 0604_ex50 | loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.03_s1.00 | 0.0568 | 0.3250 | 1.2611 | 22 | 144 | 22 |
| 0604_ex50 | loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.05_s0.25 | 0.0584 | 0.3266 | 1.2643 | 26 | 151 | 26 |
| 0604_ex50 | loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.05_s0.50 | 0.0585 | 0.3255 | 1.2620 | 22 | 148 | 22 |
| 0604_ex50 | loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.05_s0.75 | 0.0596 | 0.3243 | 1.2598 | 22 | 142 | 22 |
| 0604_ex50 | loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.05_s1.00 | 0.0617 | 0.3232 | 1.2576 | 21 | 139 | 21 |
| 0604_ex50 | loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.08_s0.25 | 0.0564 | 0.3257 | 1.2629 | 22 | 150 | 22 |
| 0604_ex50 | loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.08_s0.50 | 0.0585 | 0.3237 | 1.2593 | 22 | 142 | 22 |
| 0604_ex50 | loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.08_s0.75 | 0.0590 | 0.3216 | 1.2559 | 21 | 136 | 21 |
| 0604_ex50 | loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.08_s1.00 | 0.0587 | 0.3196 | 1.2527 | 21 | 136 | 21 |

## 7. 산출물

- `outputs/repeated_validation_metrics.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `outputs/fixed_confirmation_metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/residual_analysis.csv`
- `outputs/selected_candidates.csv`
- `artifacts/experiment_config.json`