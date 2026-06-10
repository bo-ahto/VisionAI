# PP-HCOEF9 Warm Huber 위험도 기반 기준가 결합 실험

- 작성일: 2026-06-07 23:37
- 목적: HCOEF4 loose 기준가 Huber의 MdAPE/MAPE 개선 신호를 HCOEF3 안정 후보 위에 제한적으로 반영.
- 핵심 가설: 유사 작품 기준가의 표본 수가 충분하고 분산이 낮으며 HCOEF3과 HCOEF4 예측 차이가 과도하지 않을 때만 HCOEF4 쪽으로 이동하면 p95 악화 없이 중앙/평균 오차를 줄일 수 있다.
- 기준 후보: `hcoef2_size_reliability_cap005_s050`.
- 반복 설정: row OOF 20회, artist OOF 20회, 각 5 folds.
- 후보 선택: 반복 OOF 우선, fixed test/0604는 확인용.

## 1. 실행 결론

- 새 운영 기본 후보 채택 없음.
- p95_APE를 함께 낮추지 못한 후보는 기본 후보로 채택하지 않는다.

## 2. 후보 선택표

| candidate | row_all3_prob | artist_all3_prob | row_delta_MdAPE | row_delta_MAPE | row_delta_p95_APE | artist_delta_MdAPE | artist_delta_MAPE | artist_delta_p95_APE | test_delta_MdAPE | test_delta_MAPE | test_delta_p95_APE | ops0604_delta_MdAPE | ops0604_delta_MAPE | ops0604_delta_p95_APE | passes_repeat_gate | passes_fixed_guard | purpose |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef9_loose_basis_core_huber_alpha0p1_model_agreement_only | 0.5000 | 0.3500 | -0.0060 | -0.0042 | 0.0007 | -0.0057 | -0.0039 | 0.0050 | -0.0032 | -0.0060 | 0.0244 | -0.0173 | -0.0138 | -0.0404 | False | False | hold_or_reject |
| loose_basis_core_huber_alpha0p1 | 0.6500 | 0.6500 | -0.0059 | -0.0031 | -0.0067 | -0.0062 | -0.0009 | -0.0094 | -0.0042 | -0.0112 | 0.0853 | -0.0427 | -0.0296 | -0.0321 | False | False | hold_or_reject |
| hcoef9_loose_basis_core_huber_alpha0p01_model_agreement_only | 0.5500 | 0.3500 | -0.0059 | -0.0040 | 0.0012 | -0.0056 | -0.0037 | 0.0060 | -0.0030 | -0.0061 | 0.0241 | -0.0173 | -0.0138 | -0.0403 | False | False | hold_or_reject |
| loose_basis_gap_huber_alpha0p1 | 0.8000 | 0.5000 | -0.0056 | -0.0022 | -0.0089 | -0.0056 | 0.0007 | -0.0099 | -0.0042 | -0.0102 | 0.1046 | -0.0393 | -0.0314 | -0.0094 | False | False | hold_or_reject |
| hcoef9_loose_basis_gap_huber_alpha0p1_model_agreement_only | 0.5000 | 0.6000 | -0.0056 | -0.0034 | 0.0008 | -0.0052 | -0.0030 | 0.0005 | 0.0002 | -0.0056 | 0.0246 | -0.0188 | -0.0134 | -0.0042 | False | False | hold_or_reject |
| loose_basis_core_huber_alpha0p01 | 0.7000 | 0.6500 | -0.0056 | -0.0029 | -0.0047 | -0.0062 | -0.0005 | -0.0081 | -0.0041 | -0.0110 | 0.0888 | -0.0439 | -0.0291 | -0.0293 | False | False | hold_or_reject |
| hcoef9_loose_basis_core_huber_alpha0p1_broad_low_mid_guarded | 0.3500 | 0.3500 | -0.0036 | -0.0006 | 0.0012 | -0.0031 | -0.0005 | 0.0014 | 0.0030 | -0.0012 | 0.0003 | -0.0069 | -0.0037 | -0.0000 | False | False | repeat_mape_candidate |
| hcoef9_loose_basis_core_huber_alpha0p1_low_strong_mid_light_high_stable | 0.5500 | 0.2500 | -0.0033 | -0.0002 | -0.0028 | -0.0030 | -0.0000 | -0.0009 | 0.0022 | -0.0012 | 0.0023 | -0.0107 | -0.0030 | -0.0045 | False | False | repeat_mape_candidate |
| hcoef9_loose_basis_core_huber_alpha0p01_broad_low_mid_guarded | 0.3500 | 0.3000 | -0.0033 | -0.0005 | 0.0015 | -0.0028 | -0.0004 | 0.0016 | 0.0031 | -0.0012 | 0.0002 | -0.0069 | -0.0036 | -0.0000 | False | False | repeat_mape_candidate |
| hcoef9_loose_basis_core_huber_alpha0p01_low_strong_mid_light_high_stable | 0.5500 | 0.2000 | -0.0033 | -0.0001 | -0.0017 | -0.0030 | 0.0001 | -0.0006 | 0.0022 | -0.0012 | 0.0022 | -0.0107 | -0.0030 | -0.0045 | False | False | hold_or_reject |
| hcoef9_loose_basis_gap_huber_alpha0p1_broad_low_mid_guarded | 0.2500 | 0.3000 | -0.0031 | -0.0004 | 0.0018 | -0.0031 | -0.0003 | 0.0016 | 0.0024 | -0.0012 | 0.0008 | -0.0069 | -0.0036 | -0.0000 | False | False | repeat_mape_candidate |
| hcoef9_loose_basis_gap_huber_alpha0p1_low_strong_mid_light_high_stable | 0.2500 | 0.2000 | -0.0031 | 0.0000 | -0.0016 | -0.0031 | 0.0001 | -0.0006 | 0.0021 | -0.0012 | 0.0032 | -0.0094 | -0.0031 | -0.0045 | False | False | hold_or_reject |
| hcoef9_loose_basis_core_huber_alpha0p1_low_medium_mid_tiny_high_stable | 0.1000 | 0.1000 | -0.0020 | -0.0004 | 0.0010 | -0.0019 | -0.0003 | 0.0017 | 0.0022 | -0.0006 | 0.0013 | -0.0040 | -0.0015 | 0.0000 | False | False | repeat_mape_candidate |
| hcoef9_loose_basis_core_huber_alpha0p01_low_medium_mid_tiny_high_stable | 0.1000 | 0.1000 | -0.0019 | -0.0003 | 0.0013 | -0.0019 | -0.0002 | 0.0019 | 0.0022 | -0.0005 | 0.0012 | -0.0040 | -0.0015 | 0.0000 | False | False | repeat_mape_candidate |
| hcoef9_loose_basis_gap_huber_alpha0p1_low_medium_mid_tiny_high_stable | 0.1000 | 0.1000 | -0.0019 | -0.0002 | 0.0014 | -0.0019 | -0.0002 | 0.0019 | 0.0022 | -0.0006 | 0.0015 | -0.0040 | -0.0015 | 0.0000 | False | False | repeat_mape_candidate |
| hcoef2_size_reliability_cap005_s050 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | False | hold_or_reject |
| hcoef9_loose_basis_gap_huber_alpha0p1_low_only_basis_high_stable | 0.0000 | 0.0000 | 0.0001 | 0.0005 | 0.0031 | 0.0004 | 0.0006 | 0.0038 | 0.0007 | 0.0002 | 0.0000 | 0.0000 | -0.0001 | 0.0000 | False | False | hold_or_reject |
| hcoef9_loose_basis_core_huber_alpha0p1_low_only_basis_high_stable | 0.0000 | 0.0000 | 0.0002 | 0.0004 | 0.0024 | 0.0005 | 0.0005 | 0.0036 | 0.0007 | 0.0002 | 0.0000 | 0.0000 | -0.0000 | 0.0000 | False | False | hold_or_reject |
| hcoef9_loose_basis_core_huber_alpha0p01_sample_count_only | 0.2000 | 0.0000 | 0.0002 | -0.0008 | -0.0018 | 0.0005 | -0.0008 | -0.0018 | 0.0033 | -0.0005 | 0.0000 | -0.0030 | -0.0025 | -0.0003 | False | False | repeat_mape_candidate |
| hcoef9_loose_basis_core_huber_alpha0p01_low_only_basis_high_stable | 0.0000 | 0.0000 | 0.0003 | 0.0005 | 0.0031 | 0.0007 | 0.0006 | 0.0037 | 0.0007 | 0.0002 | 0.0000 | 0.0000 | -0.0000 | 0.0000 | False | False | hold_or_reject |
| hcoef9_loose_basis_gap_huber_alpha0p1_sample_count_only | 0.1000 | 0.0000 | 0.0003 | -0.0008 | -0.0018 | 0.0004 | -0.0008 | -0.0018 | 0.0022 | -0.0006 | 0.0000 | -0.0062 | -0.0027 | -0.0003 | False | False | repeat_mape_candidate |
| hcoef9_loose_basis_core_huber_alpha0p1_sample_count_only | 0.1000 | 0.0000 | 0.0003 | -0.0009 | -0.0018 | 0.0005 | -0.0008 | -0.0018 | 0.0033 | -0.0005 | 0.0000 | -0.0030 | -0.0025 | -0.0003 | False | False | repeat_mape_candidate |

## 3. 반복 OOF 요약

| validation_scheme | candidate | mean_delta_MdAPE_vs_hcoef2 | mean_delta_MAPE_vs_hcoef2 | mean_delta_p95_APE_vs_hcoef2 | std_delta_MdAPE_vs_hcoef2 | MdAPE_improve_prob_vs_hcoef2 | MAPE_improve_prob_vs_hcoef2 | p95_improve_prob_vs_hcoef2 | all3_improve_prob_vs_hcoef2 | mean_improve_count_vs_hcoef2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| row_oof | loose_basis_gap_huber_alpha0p1 | -0.0056 | -0.0022 | -0.0089 | 0.0032 | 1.0000 | 0.9500 | 0.8500 | 0.8000 | 2.8000 |
| row_oof | loose_basis_core_huber_alpha0p01 | -0.0056 | -0.0029 | -0.0047 | 0.0030 | 1.0000 | 0.9500 | 0.7000 | 0.7000 | 2.6500 |
| artist_oof | loose_basis_core_huber_alpha0p01 | -0.0062 | -0.0005 | -0.0081 | 0.0043 | 0.9000 | 0.7500 | 0.8500 | 0.6500 | 2.5000 |
| artist_oof | loose_basis_core_huber_alpha0p1 | -0.0062 | -0.0009 | -0.0094 | 0.0044 | 0.9000 | 0.8000 | 0.8500 | 0.6500 | 2.5500 |
| row_oof | loose_basis_core_huber_alpha0p1 | -0.0059 | -0.0031 | -0.0067 | 0.0030 | 0.9500 | 0.9500 | 0.7000 | 0.6500 | 2.6000 |
| artist_oof | hcoef9_loose_basis_gap_huber_alpha0p1_model_agreement_only | -0.0052 | -0.0030 | 0.0005 | 0.0032 | 1.0000 | 1.0000 | 0.6000 | 0.6000 | 2.6000 |
| row_oof | hcoef9_loose_basis_core_huber_alpha0p01_model_agreement_only | -0.0059 | -0.0040 | 0.0012 | 0.0022 | 1.0000 | 1.0000 | 0.5500 | 0.5500 | 2.5500 |
| row_oof | hcoef9_loose_basis_core_huber_alpha0p1_low_strong_mid_light_high_stable | -0.0033 | -0.0002 | -0.0028 | 0.0008 | 1.0000 | 0.8000 | 0.7000 | 0.5500 | 2.5000 |
| row_oof | hcoef9_loose_basis_core_huber_alpha0p01_low_strong_mid_light_high_stable | -0.0033 | -0.0001 | -0.0017 | 0.0009 | 1.0000 | 0.7000 | 0.7000 | 0.5500 | 2.4000 |
| row_oof | hcoef9_loose_basis_core_huber_alpha0p1_model_agreement_only | -0.0060 | -0.0042 | 0.0007 | 0.0023 | 1.0000 | 1.0000 | 0.5000 | 0.5000 | 2.5000 |
| row_oof | hcoef9_loose_basis_gap_huber_alpha0p1_model_agreement_only | -0.0056 | -0.0034 | 0.0008 | 0.0025 | 1.0000 | 1.0000 | 0.5000 | 0.5000 | 2.5000 |
| artist_oof | loose_basis_gap_huber_alpha0p1 | -0.0056 | 0.0007 | -0.0099 | 0.0045 | 0.8500 | 0.5500 | 0.8500 | 0.5000 | 2.2500 |
| artist_oof | hcoef9_loose_basis_core_huber_alpha0p1_model_agreement_only | -0.0057 | -0.0039 | 0.0050 | 0.0032 | 1.0000 | 1.0000 | 0.3500 | 0.3500 | 2.3500 |
| artist_oof | hcoef9_loose_basis_core_huber_alpha0p01_model_agreement_only | -0.0056 | -0.0037 | 0.0060 | 0.0030 | 0.9500 | 1.0000 | 0.3500 | 0.3500 | 2.3000 |
| row_oof | hcoef9_loose_basis_core_huber_alpha0p1_broad_low_mid_guarded | -0.0036 | -0.0006 | 0.0012 | 0.0011 | 1.0000 | 1.0000 | 0.3500 | 0.3500 | 2.3500 |
| row_oof | hcoef9_loose_basis_core_huber_alpha0p01_broad_low_mid_guarded | -0.0033 | -0.0005 | 0.0015 | 0.0012 | 1.0000 | 1.0000 | 0.3500 | 0.3500 | 2.3500 |
| artist_oof | hcoef9_loose_basis_core_huber_alpha0p1_broad_low_mid_guarded | -0.0031 | -0.0005 | 0.0014 | 0.0017 | 0.9500 | 1.0000 | 0.3500 | 0.3500 | 2.3000 |
| artist_oof | hcoef9_loose_basis_gap_huber_alpha0p1_broad_low_mid_guarded | -0.0031 | -0.0003 | 0.0016 | 0.0016 | 0.9500 | 0.9000 | 0.3000 | 0.3000 | 2.1500 |
| artist_oof | hcoef9_loose_basis_core_huber_alpha0p01_broad_low_mid_guarded | -0.0028 | -0.0004 | 0.0016 | 0.0018 | 0.9000 | 0.9500 | 0.3000 | 0.3000 | 2.1500 |
| row_oof | hcoef9_loose_basis_gap_huber_alpha0p1_broad_low_mid_guarded | -0.0031 | -0.0004 | 0.0018 | 0.0009 | 1.0000 | 0.9500 | 0.3000 | 0.2500 | 2.2500 |
| row_oof | hcoef9_loose_basis_gap_huber_alpha0p1_low_strong_mid_light_high_stable | -0.0031 | 0.0000 | -0.0016 | 0.0008 | 1.0000 | 0.3500 | 0.6000 | 0.2500 | 1.9500 |
| artist_oof | hcoef9_loose_basis_core_huber_alpha0p1_low_strong_mid_light_high_stable | -0.0030 | -0.0000 | -0.0009 | 0.0014 | 0.9000 | 0.5000 | 0.4500 | 0.2500 | 1.8500 |
| artist_oof | hcoef9_loose_basis_gap_huber_alpha0p1_low_strong_mid_light_high_stable | -0.0031 | 0.0001 | -0.0006 | 0.0015 | 0.9500 | 0.4000 | 0.4000 | 0.2000 | 1.7500 |
| artist_oof | hcoef9_loose_basis_core_huber_alpha0p01_low_strong_mid_light_high_stable | -0.0030 | 0.0001 | -0.0006 | 0.0014 | 0.9000 | 0.4000 | 0.4000 | 0.2000 | 1.7000 |
| row_oof | hcoef9_loose_basis_core_huber_alpha0p01_sample_count_only | 0.0002 | -0.0008 | -0.0018 | 0.0007 | 0.2500 | 1.0000 | 0.6500 | 0.2000 | 1.9000 |
| row_oof | hcoef9_loose_basis_core_huber_alpha0p1_low_medium_mid_tiny_high_stable | -0.0020 | -0.0004 | 0.0010 | 0.0008 | 1.0000 | 1.0000 | 0.1000 | 0.1000 | 2.1000 |
| artist_oof | hcoef9_loose_basis_gap_huber_alpha0p1_low_medium_mid_tiny_high_stable | -0.0019 | -0.0002 | 0.0019 | 0.0010 | 0.9000 | 0.8000 | 0.1000 | 0.1000 | 1.8000 |
| row_oof | hcoef9_loose_basis_core_huber_alpha0p01_low_medium_mid_tiny_high_stable | -0.0019 | -0.0003 | 0.0013 | 0.0007 | 1.0000 | 1.0000 | 0.1000 | 0.1000 | 2.1000 |
| artist_oof | hcoef9_loose_basis_core_huber_alpha0p1_low_medium_mid_tiny_high_stable | -0.0019 | -0.0003 | 0.0017 | 0.0009 | 0.9000 | 0.9500 | 0.2000 | 0.1000 | 2.0500 |
| artist_oof | hcoef9_loose_basis_core_huber_alpha0p01_low_medium_mid_tiny_high_stable | -0.0019 | -0.0002 | 0.0019 | 0.0009 | 0.9000 | 0.8500 | 0.1500 | 0.1000 | 1.9000 |
| row_oof | hcoef9_loose_basis_gap_huber_alpha0p1_low_medium_mid_tiny_high_stable | -0.0019 | -0.0002 | 0.0014 | 0.0007 | 1.0000 | 0.9500 | 0.1500 | 0.1000 | 2.1000 |
| row_oof | hcoef9_loose_basis_gap_huber_alpha0p1_sample_count_only | 0.0003 | -0.0008 | -0.0018 | 0.0006 | 0.1500 | 1.0000 | 0.6500 | 0.1000 | 1.8000 |
| row_oof | hcoef9_loose_basis_core_huber_alpha0p1_sample_count_only | 0.0003 | -0.0009 | -0.0018 | 0.0006 | 0.1500 | 1.0000 | 0.6500 | 0.1000 | 1.8000 |
| artist_oof | hcoef2_size_reliability_cap005_s050 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| row_oof | hcoef2_size_reliability_cap005_s050 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| row_oof | hcoef9_loose_basis_gap_huber_alpha0p1_low_only_basis_high_stable | 0.0001 | 0.0005 | 0.0031 | 0.0008 | 0.3000 | 0.0000 | 0.0000 | 0.0000 | 0.3000 |

## 4. Fixed test 상위 후보

| candidate | method | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_hcoef2 | delta_MAPE_vs_hcoef2 | delta_p95_APE_vs_hcoef2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| loose_basis_gap_huber_alpha0p1 | loose_basis_huber_full | 0.1346 | 0.2628 | 0.9110 | 0.3902 | -0.0042 | -0.0102 | 0.1046 |
| loose_basis_core_huber_alpha0p1 | loose_basis_huber_full | 0.1346 | 0.2618 | 0.8916 | 0.3899 | -0.0042 | -0.0112 | 0.0853 |
| loose_basis_core_huber_alpha0p01 | loose_basis_huber_full | 0.1347 | 0.2620 | 0.8952 | 0.3896 | -0.0041 | -0.0110 | 0.0888 |
| hcoef9_loose_basis_core_huber_alpha0p1_model_agreement_only | risk_gated_basis_blend | 0.1356 | 0.2670 | 0.8308 | 0.3948 | -0.0032 | -0.0060 | 0.0244 |
| hcoef9_loose_basis_core_huber_alpha0p01_model_agreement_only | risk_gated_basis_blend | 0.1358 | 0.2669 | 0.8304 | 0.3945 | -0.0030 | -0.0061 | 0.0241 |
| hcoef2_size_reliability_cap005_s050 | hcoef3_stable_anchor | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 |
| hcoef9_loose_basis_gap_huber_alpha0p1_model_agreement_only | risk_gated_basis_blend | 0.1390 | 0.2674 | 0.8310 | 0.3947 | 0.0002 | -0.0056 | 0.0246 |
| hcoef9_loose_basis_gap_huber_alpha0p1_low_only_basis_high_stable | risk_gated_basis_blend | 0.1395 | 0.2732 | 0.8064 | 0.3980 | 0.0007 | 0.0002 | 0.0000 |
| hcoef9_loose_basis_core_huber_alpha0p01_low_only_basis_high_stable | risk_gated_basis_blend | 0.1395 | 0.2732 | 0.8064 | 0.3980 | 0.0007 | 0.0002 | 0.0000 |
| hcoef9_loose_basis_core_huber_alpha0p1_low_only_basis_high_stable | risk_gated_basis_blend | 0.1395 | 0.2732 | 0.8064 | 0.3980 | 0.0007 | 0.0002 | 0.0000 |
| hcoef9_loose_basis_gap_huber_alpha0p1_low_strong_mid_light_high_stable | risk_gated_basis_blend | 0.1409 | 0.2718 | 0.8096 | 0.3972 | 0.0021 | -0.0012 | 0.0032 |
| hcoef9_loose_basis_core_huber_alpha0p1_low_strong_mid_light_high_stable | risk_gated_basis_blend | 0.1410 | 0.2717 | 0.8087 | 0.3973 | 0.0022 | -0.0012 | 0.0023 |
| hcoef9_loose_basis_core_huber_alpha0p01_low_strong_mid_light_high_stable | risk_gated_basis_blend | 0.1410 | 0.2718 | 0.8086 | 0.3973 | 0.0022 | -0.0012 | 0.0022 |
| hcoef9_loose_basis_gap_huber_alpha0p1_low_medium_mid_tiny_high_stable | risk_gated_basis_blend | 0.1410 | 0.2724 | 0.8079 | 0.3980 | 0.0022 | -0.0006 | 0.0015 |
| hcoef9_loose_basis_core_huber_alpha0p1_low_medium_mid_tiny_high_stable | risk_gated_basis_blend | 0.1410 | 0.2724 | 0.8076 | 0.3980 | 0.0022 | -0.0006 | 0.0013 |
| hcoef9_loose_basis_core_huber_alpha0p01_low_medium_mid_tiny_high_stable | risk_gated_basis_blend | 0.1410 | 0.2724 | 0.8076 | 0.3980 | 0.0022 | -0.0005 | 0.0012 |
| hcoef9_loose_basis_gap_huber_alpha0p1_sample_count_only | risk_gated_basis_blend | 0.1410 | 0.2724 | 0.8064 | 0.3987 | 0.0022 | -0.0006 | 0.0000 |
| hcoef9_loose_basis_gap_huber_alpha0p1_broad_low_mid_guarded | risk_gated_basis_blend | 0.1412 | 0.2718 | 0.8071 | 0.3974 | 0.0024 | -0.0012 | 0.0008 |
| hcoef9_loose_basis_core_huber_alpha0p1_broad_low_mid_guarded | risk_gated_basis_blend | 0.1418 | 0.2718 | 0.8066 | 0.3974 | 0.0030 | -0.0012 | 0.0003 |
| hcoef9_loose_basis_core_huber_alpha0p01_broad_low_mid_guarded | risk_gated_basis_blend | 0.1419 | 0.2718 | 0.8066 | 0.3974 | 0.0031 | -0.0012 | 0.0002 |
| hcoef9_loose_basis_core_huber_alpha0p1_sample_count_only | risk_gated_basis_blend | 0.1421 | 0.2725 | 0.8064 | 0.3988 | 0.0033 | -0.0005 | 0.0000 |
| hcoef9_loose_basis_core_huber_alpha0p01_sample_count_only | risk_gated_basis_blend | 0.1421 | 0.2725 | 0.8064 | 0.3987 | 0.0033 | -0.0005 | 0.0000 |

## 5. 위험도 구간 적용 비율

| candidate | low_share_mean | mid_share_mean | high_share_mean |
| --- | --- | --- | --- |
| hcoef9_loose_basis_core_huber_alpha0p1_model_agreement_only | 0.9107 | 0.0339 | 0.0553 |
| hcoef9_loose_basis_core_huber_alpha0p01_model_agreement_only | 0.9103 | 0.0343 | 0.0553 |
| hcoef9_loose_basis_gap_huber_alpha0p1_model_agreement_only | 0.9050 | 0.0417 | 0.0533 |
| hcoef9_loose_basis_gap_huber_alpha0p1_broad_low_mid_guarded | 0.2436 | 0.4375 | 0.3189 |
| hcoef9_loose_basis_core_huber_alpha0p01_broad_low_mid_guarded | 0.2436 | 0.4367 | 0.3197 |
| hcoef9_loose_basis_core_huber_alpha0p1_broad_low_mid_guarded | 0.2436 | 0.4367 | 0.3197 |
| hcoef9_loose_basis_gap_huber_alpha0p1_low_medium_mid_tiny_high_stable | 0.1717 | 0.3613 | 0.4670 |
| hcoef9_loose_basis_gap_huber_alpha0p1_low_strong_mid_light_high_stable | 0.1717 | 0.3613 | 0.4670 |
| hcoef9_loose_basis_core_huber_alpha0p01_low_medium_mid_tiny_high_stable | 0.1717 | 0.3609 | 0.4674 |
| hcoef9_loose_basis_core_huber_alpha0p01_low_strong_mid_light_high_stable | 0.1717 | 0.3609 | 0.4674 |
| hcoef9_loose_basis_core_huber_alpha0p1_low_medium_mid_tiny_high_stable | 0.1717 | 0.3609 | 0.4674 |
| hcoef9_loose_basis_core_huber_alpha0p1_low_strong_mid_light_high_stable | 0.1717 | 0.3609 | 0.4674 |
| hcoef9_loose_basis_core_huber_alpha0p01_sample_count_only | 0.1595 | 0.3388 | 0.5017 |
| hcoef9_loose_basis_core_huber_alpha0p1_sample_count_only | 0.1595 | 0.3388 | 0.5017 |
| hcoef9_loose_basis_gap_huber_alpha0p1_sample_count_only | 0.1595 | 0.3388 | 0.5017 |
| hcoef9_loose_basis_core_huber_alpha0p01_low_only_basis_high_stable | 0.1570 | 0.0000 | 0.8430 |
| hcoef9_loose_basis_core_huber_alpha0p1_low_only_basis_high_stable | 0.1570 | 0.0000 | 0.8430 |
| hcoef9_loose_basis_gap_huber_alpha0p1_low_only_basis_high_stable | 0.1570 | 0.0000 | 0.8430 |

## 6. 주요 계수

- 계수는 표준화된 피처 기준이다. 방향성과 상대 영향 비교용이다.
| candidate | model_type | target | feature | coefficient_on_scaled_feature | abs_coefficient | intercept |
| --- | --- | --- | --- | --- | --- | --- |
| loose_basis_core_huber_alpha0p01 | huber | actual_log | current_70_30 | 1.0069 | 1.0069 | 14.9914 |
| loose_basis_core_huber_alpha0p1 | huber | actual_log | current_70_30 | 0.8625 | 0.8625 | 14.9912 |
| hcoef2_size_reliability_cap005_s050 | huber_residual | residual_log | svc_fallback | -0.4718 | 0.4718 | 0.0101 |
| loose_basis_core_huber_alpha0p1 | huber | actual_log | basis_relaxed_unit_area_log | 0.4560 | 0.4560 | 14.9912 |
| loose_basis_core_huber_alpha0p01 | huber | actual_log | basis_relaxed_unit_area_log | 0.4536 | 0.4536 | 14.9914 |
| loose_basis_gap_huber_alpha0p1 | huber | actual_log | basis_relaxed_unit_area_log | 0.4497 | 0.4497 | 14.9917 |
| loose_basis_gap_huber_alpha0p1 | huber | actual_log | current_70_30 | 0.3770 | 0.3770 | 14.9917 |
| loose_basis_gap_huber_alpha0p1 | huber | actual_log | basis_relaxed_vs_current_gap | -0.3052 | 0.3052 | 14.9917 |
| loose_basis_gap_huber_alpha0p1 | huber | actual_log | shrunk_huber_refit | -0.2654 | 0.2654 | 14.9917 |
| loose_basis_core_huber_alpha0p01 | huber | actual_log | shrunk_huber_refit | -0.2617 | 0.2617 | 14.9914 |
| loose_basis_core_huber_alpha0p1 | huber | actual_log | shrunk_huber_refit | -0.2590 | 0.2590 | 14.9912 |
| loose_basis_core_huber_alpha0p01 | huber | actual_log | svc_fallback | -0.2475 | 0.2475 | 14.9914 |
| loose_basis_gap_huber_alpha0p1 | huber | actual_log | shrunk_svc_prior | 0.2276 | 0.2276 | 14.9917 |
| loose_basis_core_huber_alpha0p1 | huber | actual_log | shrunk_svc_prior | 0.2273 | 0.2273 | 14.9912 |
| loose_basis_core_huber_alpha0p01 | huber | actual_log | shrunk_svc_prior | 0.2272 | 0.2272 | 14.9914 |
| loose_basis_gap_huber_alpha0p1 | huber | actual_log | basis_relaxed_price_log | 0.2265 | 0.2265 | 14.9917 |
| hcoef2_size_reliability_cap005_s050 | huber_residual | residual_log | shrunk_svc_prior | 0.2221 | 0.2221 | 0.0101 |
| loose_basis_gap_huber_alpha0p1 | huber | actual_log | basis_relaxed_vs_svc_gap | 0.1805 | 0.1805 | 14.9917 |
| loose_basis_core_huber_alpha0p1 | huber | actual_log | ppv8_defensive | 0.1711 | 0.1711 | 14.9912 |
| loose_basis_core_huber_alpha0p1 | huber | actual_log | svc_fallback | -0.1525 | 0.1525 | 14.9912 |
| loose_basis_gap_huber_alpha0p1 | huber | actual_log | svc_fallback | 0.1350 | 0.1350 | 14.9917 |
| hcoef2_size_reliability_cap005_s050 | huber_residual | residual_log | current_shrunk_huber_gap | 0.1308 | 0.1308 | 0.0101 |
| loose_basis_gap_huber_alpha0p1 | huber | actual_log | ppv8_defensive | 0.1298 | 0.1298 | 14.9917 |
| loose_basis_core_huber_alpha0p01 | huber | actual_log | ppv8_defensive | 0.1273 | 0.1273 | 14.9914 |
| hcoef2_size_reliability_cap005_s050 | huber_residual | residual_log | ppv8_defensive | 0.1081 | 0.1081 | 0.0101 |
| hcoef2_size_reliability_cap005_s050 | huber_residual | residual_log | shrunk_huber_refit | 0.0877 | 0.0877 | 0.0101 |
| hcoef2_size_reliability_cap005_s050 | huber_residual | residual_log | raw_shrunk_prior_gap | -0.0580 | 0.0580 | 0.0101 |
| hcoef2_size_reliability_cap005_s050 | huber_residual | residual_log | log_area | 0.0570 | 0.0570 | 0.0101 |
| hcoef2_size_reliability_cap005_s050 | huber_residual | residual_log | current_ppv8_gap | 0.0491 | 0.0491 | 0.0101 |
| loose_basis_core_huber_alpha0p01 | huber | actual_log | log_area | 0.0374 | 0.0374 | 14.9914 |
| loose_basis_core_huber_alpha0p1 | huber | actual_log | log_area | 0.0374 | 0.0374 | 14.9912 |
| loose_basis_gap_huber_alpha0p1 | huber | actual_log | log_area | 0.0364 | 0.0364 | 14.9917 |
| loose_basis_core_huber_alpha0p01 | huber | actual_log | basis_relaxed_price_log | -0.0316 | 0.0316 | 14.9914 |
| loose_basis_core_huber_alpha0p1 | huber | actual_log | basis_relaxed_price_log | -0.0305 | 0.0305 | 14.9912 |
| loose_basis_core_huber_alpha0p1 | huber | actual_log | basis_relaxed_n_log | -0.0149 | 0.0149 | 14.9912 |
| loose_basis_core_huber_alpha0p01 | huber | actual_log | basis_relaxed_n_log | -0.0149 | 0.0149 | 14.9914 |
| loose_basis_gap_huber_alpha0p1 | huber | actual_log | svc_group_n_log | -0.0124 | 0.0124 | 14.9917 |
| hcoef2_size_reliability_cap005_s050 | huber_residual | residual_log | svc_group_n_log | -0.0121 | 0.0121 | 0.0101 |
| loose_basis_gap_huber_alpha0p1 | huber | actual_log | basis_relaxed_iqr | -0.0104 | 0.0104 | 14.9917 |
| loose_basis_gap_huber_alpha0p1 | huber | actual_log | svc_prior_iqr | 0.0096 | 0.0096 | 14.9917 |

## 7. 잔차/큰 오차 요약

| split | candidate | n | median_residual_log | mean_residual_log | residual_std | over_2x_n | under_half_n | ape_gt_100pct_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_ex50 | hcoef2_size_reliability_cap005_s050 | 829 | 0.0608 | 0.3278 | 1.2668 | 26 | 152 | 26 |
| 0604_ex50 | hcoef9_loose_basis_core_huber_alpha0p01_broad_low_mid_guarded | 829 | 0.0645 | 0.3281 | 1.2662 | 26 | 152 | 26 |
| 0604_ex50 | hcoef9_loose_basis_core_huber_alpha0p01_low_medium_mid_tiny_high_stable | 829 | 0.0617 | 0.3279 | 1.2665 | 26 | 152 | 26 |
| 0604_ex50 | hcoef9_loose_basis_core_huber_alpha0p01_low_only_basis_high_stable | 829 | 0.0655 | 0.3269 | 1.2669 | 26 | 152 | 26 |
| 0604_ex50 | hcoef9_loose_basis_core_huber_alpha0p01_low_strong_mid_light_high_stable | 829 | 0.0662 | 0.3277 | 1.2664 | 25 | 152 | 25 |
| 0604_ex50 | hcoef9_loose_basis_core_huber_alpha0p01_model_agreement_only | 829 | 0.0632 | 0.3319 | 1.2640 | 21 | 146 | 21 |
| 0604_ex50 | hcoef9_loose_basis_core_huber_alpha0p01_sample_count_only | 829 | 0.0617 | 0.3287 | 1.2655 | 26 | 148 | 26 |
| 0604_ex50 | hcoef9_loose_basis_core_huber_alpha0p1_broad_low_mid_guarded | 829 | 0.0645 | 0.3281 | 1.2662 | 26 | 152 | 26 |
| 0604_ex50 | hcoef9_loose_basis_core_huber_alpha0p1_low_medium_mid_tiny_high_stable | 829 | 0.0619 | 0.3279 | 1.2665 | 26 | 152 | 26 |
| 0604_ex50 | hcoef9_loose_basis_core_huber_alpha0p1_low_only_basis_high_stable | 829 | 0.0655 | 0.3269 | 1.2669 | 26 | 152 | 26 |
| 0604_ex50 | hcoef9_loose_basis_core_huber_alpha0p1_low_strong_mid_light_high_stable | 829 | 0.0662 | 0.3277 | 1.2664 | 25 | 152 | 25 |
| 0604_ex50 | hcoef9_loose_basis_core_huber_alpha0p1_model_agreement_only | 829 | 0.0629 | 0.3318 | 1.2640 | 21 | 146 | 21 |
| 0604_ex50 | hcoef9_loose_basis_core_huber_alpha0p1_sample_count_only | 829 | 0.0619 | 0.3287 | 1.2655 | 26 | 148 | 26 |
| 0604_ex50 | hcoef9_loose_basis_gap_huber_alpha0p1_broad_low_mid_guarded | 829 | 0.0645 | 0.3284 | 1.2662 | 26 | 151 | 26 |
| 0604_ex50 | hcoef9_loose_basis_gap_huber_alpha0p1_low_medium_mid_tiny_high_stable | 829 | 0.0653 | 0.3281 | 1.2666 | 26 | 151 | 26 |
| 0604_ex50 | hcoef9_loose_basis_gap_huber_alpha0p1_low_only_basis_high_stable | 829 | 0.0641 | 0.3270 | 1.2670 | 26 | 151 | 26 |
| 0604_ex50 | hcoef9_loose_basis_gap_huber_alpha0p1_low_strong_mid_light_high_stable | 829 | 0.0655 | 0.3280 | 1.2665 | 25 | 151 | 25 |
| 0604_ex50 | hcoef9_loose_basis_gap_huber_alpha0p1_model_agreement_only | 829 | 0.0622 | 0.3327 | 1.2640 | 23 | 145 | 23 |
| 0604_ex50 | hcoef9_loose_basis_gap_huber_alpha0p1_sample_count_only | 829 | 0.0661 | 0.3293 | 1.2655 | 26 | 148 | 26 |
| 0604_ex50 | loose_basis_core_huber_alpha0p01 | 829 | -0.0144 | 0.1390 | 0.8012 | 26 | 88 | 26 |
| 0604_ex50 | loose_basis_core_huber_alpha0p1 | 829 | -0.0142 | 0.1387 | 0.7986 | 26 | 89 | 26 |
| 0604_ex50 | loose_basis_gap_huber_alpha0p1 | 829 | -0.0043 | 0.1504 | 0.8072 | 26 | 90 | 26 |
| test | hcoef2_size_reliability_cap005_s050 | 607 | -0.0039 | -0.0148 | 0.3989 | 26 | 17 | 26 |
| test | hcoef9_loose_basis_core_huber_alpha0p01_broad_low_mid_guarded | 607 | -0.0012 | -0.0137 | 0.3975 | 26 | 17 | 26 |
| test | hcoef9_loose_basis_core_huber_alpha0p01_low_medium_mid_tiny_high_stable | 607 | -0.0004 | -0.0137 | 0.3981 | 26 | 17 | 26 |
| test | hcoef9_loose_basis_core_huber_alpha0p01_low_only_basis_high_stable | 607 | -0.0005 | -0.0138 | 0.3981 | 26 | 17 | 26 |
| test | hcoef9_loose_basis_core_huber_alpha0p01_low_strong_mid_light_high_stable | 607 | -0.0039 | -0.0129 | 0.3974 | 26 | 17 | 26 |
| test | hcoef9_loose_basis_core_huber_alpha0p01_model_agreement_only | 607 | -0.0044 | -0.0155 | 0.3945 | 26 | 17 | 26 |
| test | hcoef9_loose_basis_core_huber_alpha0p01_sample_count_only | 607 | -0.0005 | -0.0137 | 0.3988 | 27 | 17 | 27 |
| test | hcoef9_loose_basis_core_huber_alpha0p1_broad_low_mid_guarded | 607 | -0.0009 | -0.0136 | 0.3975 | 26 | 17 | 26 |
| test | hcoef9_loose_basis_core_huber_alpha0p1_low_medium_mid_tiny_high_stable | 607 | -0.0004 | -0.0137 | 0.3981 | 26 | 17 | 26 |
| test | hcoef9_loose_basis_core_huber_alpha0p1_low_only_basis_high_stable | 607 | -0.0005 | -0.0137 | 0.3981 | 26 | 17 | 26 |
| test | hcoef9_loose_basis_core_huber_alpha0p1_low_strong_mid_light_high_stable | 607 | -0.0039 | -0.0129 | 0.3974 | 26 | 17 | 26 |
| test | hcoef9_loose_basis_core_huber_alpha0p1_model_agreement_only | 607 | -0.0039 | -0.0154 | 0.3948 | 26 | 17 | 26 |
| test | hcoef9_loose_basis_core_huber_alpha0p1_sample_count_only | 607 | -0.0005 | -0.0137 | 0.3989 | 27 | 17 | 27 |
| test | hcoef9_loose_basis_gap_huber_alpha0p1_broad_low_mid_guarded | 607 | -0.0021 | -0.0137 | 0.3974 | 26 | 17 | 26 |

## 8. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/residual_analysis.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `outputs/selected_candidates.csv`
- `outputs/risk_segment_summary.csv`
- `artifacts/experiment_config.json`