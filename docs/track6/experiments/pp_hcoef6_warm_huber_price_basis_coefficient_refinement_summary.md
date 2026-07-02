# PP-HCOEF6 Warm Huber 조건부 기준가 routing 실험

- 작성일: 2026-06-07 23:03
- 목적: HCOEF4 basis-Huber 후보의 MdAPE/MAPE 장점을 살리되, p95_APE 악화를 막기 위해 신뢰도가 높은 구간에만 제한 적용.
- 기준 후보: `hcoef2_size_reliability_cap005_s050`.
- 방식: 기본 예측은 HCOEF3 안정 후보를 유지하고, 표본 수/IQR/gap/기준가 level/완화 weight 조건을 만족한 샘플에만 basis-Huber 차이를 cap/strength로 제한해 반영.
- 후보 선택: 반복 OOF 우선, fixed test는 최종 확인용.

## 1. 실행 결론

- 새 운영 기본 후보 채택 없음.
- 조건부 routing은 일부 MAPE/MdAPE 개선 신호를 만들었는지 확인하되, 운영 후보는 p95 guard와 반복 OOF를 동시에 통과해야 함.

## 2. 후보 선택표

| candidate | row_all3_prob | artist_all3_prob | row_delta_MdAPE | row_delta_MAPE | row_delta_p95_APE | artist_delta_MdAPE | artist_delta_MAPE | artist_delta_p95_APE | test_delta_MdAPE | test_delta_MAPE | test_delta_p95_APE | ops0604_delta_MdAPE | ops0604_delta_MAPE | ops0604_delta_p95_APE | passes_repeat_gate | passes_fixed_guard | purpose |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| loose_basis_core_huber_alpha0p01__route_broad_lowrisk_n30_iqr065_gap050_cap003_s075 | 0.0000 | 0.0000 | 0.0000 | -0.0002 | 0.0000 | 0.0000 | -0.0002 | 0.0000 | -0.0004 | -0.0002 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | True | repeat_mape_candidate |
| loose_basis_core_huber_alpha0p1__route_broad_lowrisk_n30_iqr065_gap050_cap003_s075 | 0.0000 | 0.0000 | 0.0000 | -0.0002 | 0.0000 | 0.0000 | -0.0002 | 0.0000 | -0.0004 | -0.0002 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | True | repeat_mape_candidate |
| loose_basis_gap_huber_alpha0p1__route_broad_lowrisk_n30_iqr065_gap050_cap003_s075 | 0.0000 | 0.0000 | 0.0000 | -0.0002 | 0.0000 | 0.0000 | -0.0002 | 0.0000 | -0.0004 | -0.0002 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | True | repeat_mape_candidate |
| loose_basis_core_huber_alpha0p1 | 0.9167 | 0.6667 | -0.0065 | -0.0032 | -0.0140 | -0.0056 | -0.0010 | -0.0127 | -0.0042 | -0.0112 | 0.0853 | -0.0427 | -0.0296 | -0.0321 | False | False | repeat_mape_candidate |
| loose_basis_core_huber_alpha0p01 | 0.9167 | 0.7500 | -0.0061 | -0.0030 | -0.0117 | -0.0058 | -0.0007 | -0.0111 | -0.0041 | -0.0110 | 0.0888 | -0.0439 | -0.0291 | -0.0293 | False | False | repeat_mape_candidate |
| loose_basis_gap_huber_alpha0p1 | 0.9167 | 0.6667 | -0.0061 | -0.0024 | -0.0160 | -0.0053 | 0.0004 | -0.0120 | -0.0042 | -0.0102 | 0.1046 | -0.0393 | -0.0314 | -0.0094 | False | False | fixed_confirmation_candidate |
| loose_basis_core_huber_alpha0p1__route_detail_or_artist_n3_iqr080_gap060_cap003_s050 | 0.5000 | 0.5000 | -0.0042 | -0.0013 | -0.0006 | -0.0033 | -0.0012 | -0.0003 | 0.0026 | -0.0019 | 0.0000 | -0.0052 | -0.0034 | 0.0000 | False | False | repeat_mape_candidate |
| loose_basis_core_huber_alpha0p01__route_detail_or_artist_n3_iqr080_gap060_cap003_s050 | 0.5000 | 0.5000 | -0.0040 | -0.0012 | -0.0011 | -0.0031 | -0.0011 | -0.0004 | 0.0031 | -0.0019 | 0.0000 | -0.0052 | -0.0034 | 0.0000 | False | False | repeat_mape_candidate |
| loose_basis_gap_huber_alpha0p1__route_detail_or_artist_n3_iqr080_gap060_cap003_s050 | 0.5833 | 0.5000 | -0.0036 | -0.0010 | -0.0010 | -0.0029 | -0.0008 | -0.0003 | 0.0024 | -0.0018 | 0.0000 | -0.0052 | -0.0032 | 0.0000 | False | False | repeat_mape_candidate |
| loose_basis_core_huber_alpha0p1__route_artist_reliable_n5_iqr090_gap080_cap005_s050 | 0.1667 | 0.1667 | -0.0034 | -0.0004 | 0.0012 | -0.0036 | -0.0002 | 0.0018 | 0.0026 | -0.0019 | 0.0000 | -0.0129 | -0.0030 | 0.0000 | False | False | repeat_mape_candidate |
| loose_basis_core_huber_alpha0p01__route_artist_reliable_n5_iqr090_gap080_cap005_s050 | 0.1667 | 0.2500 | -0.0033 | -0.0003 | 0.0013 | -0.0035 | -0.0002 | 0.0022 | 0.0033 | -0.0018 | 0.0000 | -0.0129 | -0.0030 | 0.0000 | False | False | repeat_mape_candidate |
| loose_basis_gap_huber_alpha0p1__route_artist_reliable_n5_iqr090_gap080_cap005_s050 | 0.1667 | 0.1667 | -0.0033 | -0.0002 | 0.0013 | -0.0034 | 0.0000 | 0.0028 | 0.0044 | -0.0018 | 0.0000 | -0.0129 | -0.0030 | 0.0000 | False | False | hold_or_reject |
| loose_basis_core_huber_alpha0p01__route_coverage_high_n8_iqr100_gap100_cap003_s025 | 0.0000 | 0.0000 | -0.0003 | -0.0002 | 0.0000 | 0.0001 | -0.0001 | 0.0000 | 0.0014 | -0.0002 | 0.0000 | 0.0000 | -0.0006 | 0.0000 | False | False | repeat_mape_candidate |
| loose_basis_core_huber_alpha0p1__route_coverage_high_n8_iqr100_gap100_cap003_s025 | 0.0000 | 0.0000 | -0.0003 | -0.0002 | 0.0000 | 0.0001 | -0.0002 | 0.0000 | 0.0014 | -0.0002 | 0.0000 | 0.0000 | -0.0006 | 0.0000 | False | False | repeat_mape_candidate |
| loose_basis_gap_huber_alpha0p1__route_coverage_high_n8_iqr100_gap100_cap003_s025 | 0.0000 | 0.0000 | -0.0003 | -0.0001 | 0.0000 | 0.0000 | -0.0001 | 0.0000 | 0.0014 | -0.0002 | 0.0000 | 0.0000 | -0.0006 | 0.0000 | False | False | repeat_mape_candidate |
| loose_basis_gap_huber_alpha0p1__route_broad_reliable_n20_iqr080_gap080_cap005_s050 | 0.0000 | 0.0000 | -0.0000 | -0.0001 | 0.0000 | 0.0008 | -0.0001 | 0.0000 | 0.0003 | 0.0001 | 0.0000 | 0.0000 | -0.0005 | 0.0000 | False | False | repeat_mape_candidate |
| hcoef2_size_reliability_cap005_s050 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | False | hold_or_reject |
| loose_basis_core_huber_alpha0p1__route_broad_reliable_n20_iqr080_gap080_cap005_s050 | 0.0000 | 0.0000 | 0.0001 | -0.0001 | 0.0000 | 0.0008 | -0.0001 | 0.0000 | 0.0001 | 0.0001 | 0.0000 | 0.0000 | -0.0005 | 0.0000 | False | False | repeat_mape_candidate |
| loose_basis_core_huber_alpha0p01__route_broad_reliable_n20_iqr080_gap080_cap005_s050 | 0.0000 | 0.0000 | 0.0002 | -0.0001 | 0.0000 | 0.0008 | -0.0001 | 0.0000 | 0.0001 | 0.0001 | 0.0000 | 0.0000 | -0.0005 | 0.0000 | False | False | repeat_mape_candidate |
| loose_basis_core_huber_alpha0p1__route_artist_strict_n10_iqr075_gap065_cap005_s075 | 0.0000 | 0.0000 | 0.0004 | 0.0001 | 0.0014 | 0.0009 | 0.0002 | 0.0026 | 0.0007 | 0.0001 | 0.0000 | -0.0002 | -0.0004 | 0.0000 | False | False | hold_or_reject |
| loose_basis_gap_huber_alpha0p1__route_artist_strict_n10_iqr075_gap065_cap005_s075 | 0.0000 | 0.0000 | 0.0005 | 0.0002 | 0.0017 | 0.0008 | 0.0002 | 0.0027 | 0.0007 | 0.0000 | 0.0000 | -0.0002 | -0.0004 | 0.0000 | False | False | hold_or_reject |
| loose_basis_core_huber_alpha0p01__route_artist_strict_n10_iqr075_gap065_cap005_s075 | 0.0000 | 0.0000 | 0.0005 | 0.0002 | 0.0017 | 0.0009 | 0.0002 | 0.0027 | 0.0007 | 0.0001 | 0.0000 | -0.0002 | -0.0004 | 0.0000 | False | False | hold_or_reject |

## 3. 반복 OOF 요약

| validation_scheme | candidate | mean_delta_MdAPE_vs_hcoef2 | mean_delta_MAPE_vs_hcoef2 | mean_delta_p95_APE_vs_hcoef2 | std_delta_MdAPE_vs_hcoef2 | MdAPE_improve_prob_vs_hcoef2 | MAPE_improve_prob_vs_hcoef2 | p95_improve_prob_vs_hcoef2 | all3_improve_prob_vs_hcoef2 | mean_improve_count_vs_hcoef2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| row_oof | loose_basis_core_huber_alpha0p1 | -0.0065 | -0.0032 | -0.0140 | 0.0024 | 1.0000 | 1.0000 | 0.9167 | 0.9167 | 2.9167 |
| row_oof | loose_basis_core_huber_alpha0p01 | -0.0061 | -0.0030 | -0.0117 | 0.0026 | 1.0000 | 1.0000 | 0.9167 | 0.9167 | 2.9167 |
| row_oof | loose_basis_gap_huber_alpha0p1 | -0.0061 | -0.0024 | -0.0160 | 0.0031 | 1.0000 | 1.0000 | 0.9167 | 0.9167 | 2.9167 |
| artist_oof | loose_basis_core_huber_alpha0p01 | -0.0058 | -0.0007 | -0.0111 | 0.0028 | 0.9167 | 0.8333 | 0.8333 | 0.7500 | 2.5833 |
| artist_oof | loose_basis_core_huber_alpha0p1 | -0.0056 | -0.0010 | -0.0127 | 0.0036 | 0.8333 | 0.8333 | 0.8333 | 0.6667 | 2.5000 |
| artist_oof | loose_basis_gap_huber_alpha0p1 | -0.0053 | 0.0004 | -0.0120 | 0.0040 | 0.8333 | 0.7500 | 0.8333 | 0.6667 | 2.4167 |
| row_oof | loose_basis_gap_huber_alpha0p1__route_detail_or_artist_n3_iqr080_gap060_cap003_s050 | -0.0036 | -0.0010 | -0.0010 | 0.0014 | 1.0000 | 1.0000 | 0.5833 | 0.5833 | 2.5833 |
| row_oof | loose_basis_core_huber_alpha0p1__route_detail_or_artist_n3_iqr080_gap060_cap003_s050 | -0.0042 | -0.0013 | -0.0006 | 0.0011 | 1.0000 | 1.0000 | 0.5000 | 0.5000 | 2.5000 |
| row_oof | loose_basis_core_huber_alpha0p01__route_detail_or_artist_n3_iqr080_gap060_cap003_s050 | -0.0040 | -0.0012 | -0.0011 | 0.0015 | 1.0000 | 1.0000 | 0.5000 | 0.5000 | 2.5000 |
| artist_oof | loose_basis_core_huber_alpha0p1__route_detail_or_artist_n3_iqr080_gap060_cap003_s050 | -0.0033 | -0.0012 | -0.0003 | 0.0018 | 1.0000 | 1.0000 | 0.5000 | 0.5000 | 2.5000 |
| artist_oof | loose_basis_core_huber_alpha0p01__route_detail_or_artist_n3_iqr080_gap060_cap003_s050 | -0.0031 | -0.0011 | -0.0004 | 0.0019 | 1.0000 | 1.0000 | 0.5000 | 0.5000 | 2.5000 |
| artist_oof | loose_basis_gap_huber_alpha0p1__route_detail_or_artist_n3_iqr080_gap060_cap003_s050 | -0.0029 | -0.0008 | -0.0003 | 0.0022 | 1.0000 | 1.0000 | 0.5000 | 0.5000 | 2.5000 |
| artist_oof | loose_basis_core_huber_alpha0p01__route_artist_reliable_n5_iqr090_gap080_cap005_s050 | -0.0035 | -0.0002 | 0.0022 | 0.0009 | 1.0000 | 0.6667 | 0.2500 | 0.2500 | 1.9167 |
| artist_oof | loose_basis_core_huber_alpha0p1__route_artist_reliable_n5_iqr090_gap080_cap005_s050 | -0.0036 | -0.0002 | 0.0018 | 0.0009 | 1.0000 | 0.6667 | 0.1667 | 0.1667 | 1.8333 |
| row_oof | loose_basis_core_huber_alpha0p1__route_artist_reliable_n5_iqr090_gap080_cap005_s050 | -0.0034 | -0.0004 | 0.0012 | 0.0009 | 1.0000 | 1.0000 | 0.1667 | 0.1667 | 2.1667 |
| artist_oof | loose_basis_gap_huber_alpha0p1__route_artist_reliable_n5_iqr090_gap080_cap005_s050 | -0.0034 | 0.0000 | 0.0028 | 0.0009 | 1.0000 | 0.5833 | 0.1667 | 0.1667 | 1.7500 |
| row_oof | loose_basis_core_huber_alpha0p01__route_artist_reliable_n5_iqr090_gap080_cap005_s050 | -0.0033 | -0.0003 | 0.0013 | 0.0009 | 1.0000 | 1.0000 | 0.1667 | 0.1667 | 2.1667 |
| row_oof | loose_basis_gap_huber_alpha0p1__route_artist_reliable_n5_iqr090_gap080_cap005_s050 | -0.0033 | -0.0002 | 0.0013 | 0.0010 | 1.0000 | 0.9167 | 0.1667 | 0.1667 | 2.0833 |
| row_oof | loose_basis_core_huber_alpha0p1__route_coverage_high_n8_iqr100_gap100_cap003_s025 | -0.0003 | -0.0002 | 0.0000 | 0.0006 | 0.5000 | 1.0000 | 0.0000 | 0.0000 | 1.5000 |
| row_oof | loose_basis_core_huber_alpha0p01__route_coverage_high_n8_iqr100_gap100_cap003_s025 | -0.0003 | -0.0002 | 0.0000 | 0.0006 | 0.5000 | 1.0000 | 0.0000 | 0.0000 | 1.5000 |
| row_oof | loose_basis_gap_huber_alpha0p1__route_coverage_high_n8_iqr100_gap100_cap003_s025 | -0.0003 | -0.0001 | 0.0000 | 0.0006 | 0.5000 | 1.0000 | 0.0000 | 0.0000 | 1.5000 |
| row_oof | loose_basis_gap_huber_alpha0p1__route_broad_reliable_n20_iqr080_gap080_cap005_s050 | -0.0000 | -0.0001 | 0.0000 | 0.0005 | 0.0833 | 1.0000 | 0.0000 | 0.0000 | 1.0833 |
| row_oof | loose_basis_gap_huber_alpha0p1__route_broad_lowrisk_n30_iqr065_gap050_cap003_s075 | 0.0000 | -0.0002 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 1.0000 |
| row_oof | loose_basis_core_huber_alpha0p1__route_broad_lowrisk_n30_iqr065_gap050_cap003_s075 | 0.0000 | -0.0002 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 1.0000 |
| row_oof | loose_basis_core_huber_alpha0p01__route_broad_lowrisk_n30_iqr065_gap050_cap003_s075 | 0.0000 | -0.0002 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 1.0000 |
| artist_oof | loose_basis_gap_huber_alpha0p1__route_broad_lowrisk_n30_iqr065_gap050_cap003_s075 | 0.0000 | -0.0002 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 1.0000 |
| artist_oof | loose_basis_core_huber_alpha0p1__route_broad_lowrisk_n30_iqr065_gap050_cap003_s075 | 0.0000 | -0.0002 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 1.0000 |
| artist_oof | loose_basis_core_huber_alpha0p01__route_broad_lowrisk_n30_iqr065_gap050_cap003_s075 | 0.0000 | -0.0002 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 1.0000 |
| artist_oof | hcoef2_size_reliability_cap005_s050 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| row_oof | hcoef2_size_reliability_cap005_s050 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| artist_oof | loose_basis_gap_huber_alpha0p1__route_coverage_high_n8_iqr100_gap100_cap003_s025 | 0.0000 | -0.0001 | 0.0000 | 0.0011 | 0.4167 | 0.9167 | 0.0000 | 0.0000 | 1.3333 |
| artist_oof | loose_basis_core_huber_alpha0p1__route_coverage_high_n8_iqr100_gap100_cap003_s025 | 0.0001 | -0.0002 | 0.0000 | 0.0011 | 0.3333 | 1.0000 | 0.0000 | 0.0000 | 1.3333 |

## 4. Fixed test 상위 후보

| candidate | method | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_hcoef2 | delta_MAPE_vs_hcoef2 | delta_p95_APE_vs_hcoef2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| loose_basis_gap_huber_alpha0p1 | basis_huber_full | 0.1346 | 0.2628 | 0.9110 | 0.3902 | -0.0042 | -0.0102 | 0.1046 |
| loose_basis_core_huber_alpha0p1 | basis_huber_full | 0.1346 | 0.2618 | 0.8916 | 0.3899 | -0.0042 | -0.0112 | 0.0853 |
| loose_basis_core_huber_alpha0p01 | basis_huber_full | 0.1347 | 0.2620 | 0.8952 | 0.3896 | -0.0041 | -0.0110 | 0.0888 |
| loose_basis_gap_huber_alpha0p1__route_broad_lowrisk_n30_iqr065_gap050_cap003_s075 | conditional_basis_on_hcoef2 | 0.1384 | 0.2728 | 0.8064 | 0.3988 | -0.0004 | -0.0002 | 0.0000 |
| loose_basis_core_huber_alpha0p1__route_broad_lowrisk_n30_iqr065_gap050_cap003_s075 | conditional_basis_on_hcoef2 | 0.1384 | 0.2728 | 0.8064 | 0.3988 | -0.0004 | -0.0002 | 0.0000 |
| loose_basis_core_huber_alpha0p01__route_broad_lowrisk_n30_iqr065_gap050_cap003_s075 | conditional_basis_on_hcoef2 | 0.1384 | 0.2728 | 0.8064 | 0.3988 | -0.0004 | -0.0002 | 0.0000 |
| hcoef2_size_reliability_cap005_s050 | hcoef2_stable | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 |
| loose_basis_core_huber_alpha0p01__route_broad_reliable_n20_iqr080_gap080_cap005_s050 | conditional_basis_on_hcoef2 | 0.1389 | 0.2731 | 0.8064 | 0.3990 | 0.0001 | 0.0001 | 0.0000 |
| loose_basis_core_huber_alpha0p1__route_broad_reliable_n20_iqr080_gap080_cap005_s050 | conditional_basis_on_hcoef2 | 0.1389 | 0.2731 | 0.8064 | 0.3990 | 0.0001 | 0.0001 | 0.0000 |
| loose_basis_gap_huber_alpha0p1__route_broad_reliable_n20_iqr080_gap080_cap005_s050 | conditional_basis_on_hcoef2 | 0.1391 | 0.2731 | 0.8064 | 0.3990 | 0.0003 | 0.0001 | 0.0000 |
| loose_basis_gap_huber_alpha0p1__route_artist_strict_n10_iqr075_gap065_cap005_s075 | conditional_basis_on_hcoef2 | 0.1395 | 0.2730 | 0.8064 | 0.3984 | 0.0007 | 0.0000 | 0.0000 |
| loose_basis_core_huber_alpha0p01__route_artist_strict_n10_iqr075_gap065_cap005_s075 | conditional_basis_on_hcoef2 | 0.1395 | 0.2731 | 0.8064 | 0.3984 | 0.0007 | 0.0001 | 0.0000 |
| loose_basis_core_huber_alpha0p1__route_artist_strict_n10_iqr075_gap065_cap005_s075 | conditional_basis_on_hcoef2 | 0.1395 | 0.2731 | 0.8064 | 0.3984 | 0.0007 | 0.0001 | 0.0000 |
| loose_basis_core_huber_alpha0p1__route_coverage_high_n8_iqr100_gap100_cap003_s025 | conditional_basis_on_hcoef2 | 0.1403 | 0.2728 | 0.8064 | 0.3987 | 0.0014 | -0.0002 | 0.0000 |
| loose_basis_core_huber_alpha0p01__route_coverage_high_n8_iqr100_gap100_cap003_s025 | conditional_basis_on_hcoef2 | 0.1403 | 0.2728 | 0.8064 | 0.3987 | 0.0014 | -0.0002 | 0.0000 |
| loose_basis_gap_huber_alpha0p1__route_coverage_high_n8_iqr100_gap100_cap003_s025 | conditional_basis_on_hcoef2 | 0.1403 | 0.2728 | 0.8064 | 0.3987 | 0.0014 | -0.0002 | 0.0000 |
| loose_basis_gap_huber_alpha0p1__route_detail_or_artist_n3_iqr080_gap060_cap003_s050 | conditional_basis_on_hcoef2 | 0.1412 | 0.2712 | 0.8064 | 0.3976 | 0.0024 | -0.0018 | 0.0000 |
| loose_basis_core_huber_alpha0p1__route_detail_or_artist_n3_iqr080_gap060_cap003_s050 | conditional_basis_on_hcoef2 | 0.1414 | 0.2711 | 0.8064 | 0.3976 | 0.0026 | -0.0019 | 0.0000 |
| loose_basis_core_huber_alpha0p1__route_artist_reliable_n5_iqr090_gap080_cap005_s050 | conditional_basis_on_hcoef2 | 0.1414 | 0.2711 | 0.8064 | 0.3975 | 0.0026 | -0.0019 | 0.0000 |
| loose_basis_core_huber_alpha0p01__route_detail_or_artist_n3_iqr080_gap060_cap003_s050 | conditional_basis_on_hcoef2 | 0.1419 | 0.2711 | 0.8064 | 0.3976 | 0.0031 | -0.0019 | 0.0000 |
| loose_basis_core_huber_alpha0p01__route_artist_reliable_n5_iqr090_gap080_cap005_s050 | conditional_basis_on_hcoef2 | 0.1421 | 0.2711 | 0.8064 | 0.3975 | 0.0033 | -0.0018 | 0.0000 |
| loose_basis_gap_huber_alpha0p1__route_artist_reliable_n5_iqr090_gap080_cap005_s050 | conditional_basis_on_hcoef2 | 0.1432 | 0.2712 | 0.8064 | 0.3975 | 0.0044 | -0.0018 | 0.0000 |

## 5. Routing 적용 범위

| candidate | validation_routed_share | mean_routed_share | max_routed_share |
| --- | --- | --- | --- |
| loose_basis_core_huber_alpha0p01__route_artist_reliable_n5_iqr090_gap080_cap005_s050 | 0.5453 | 0.5028 | 0.5700 |
| loose_basis_core_huber_alpha0p01__route_artist_strict_n10_iqr075_gap065_cap005_s075 | 0.1753 | 0.1596 | 0.2010 |
| loose_basis_core_huber_alpha0p01__route_broad_lowrisk_n30_iqr065_gap050_cap003_s075 | 0.0212 | 0.0200 | 0.0362 |
| loose_basis_core_huber_alpha0p01__route_broad_reliable_n20_iqr080_gap080_cap005_s050 | 0.0597 | 0.0698 | 0.0774 |
| loose_basis_core_huber_alpha0p01__route_coverage_high_n8_iqr100_gap100_cap003_s025 | 0.2813 | 0.2723 | 0.3064 |
| loose_basis_core_huber_alpha0p01__route_detail_or_artist_n3_iqr080_gap060_cap003_s050 | 0.7225 | 0.6591 | 0.7225 |
| loose_basis_core_huber_alpha0p1__route_artist_reliable_n5_iqr090_gap080_cap005_s050 | 0.5453 | 0.5028 | 0.5700 |
| loose_basis_core_huber_alpha0p1__route_artist_strict_n10_iqr075_gap065_cap005_s075 | 0.1753 | 0.1596 | 0.2010 |
| loose_basis_core_huber_alpha0p1__route_broad_lowrisk_n30_iqr065_gap050_cap003_s075 | 0.0212 | 0.0200 | 0.0362 |
| loose_basis_core_huber_alpha0p1__route_broad_reliable_n20_iqr080_gap080_cap005_s050 | 0.0597 | 0.0698 | 0.0774 |
| loose_basis_core_huber_alpha0p1__route_coverage_high_n8_iqr100_gap100_cap003_s025 | 0.2813 | 0.2723 | 0.3064 |
| loose_basis_core_huber_alpha0p1__route_detail_or_artist_n3_iqr080_gap060_cap003_s050 | 0.7225 | 0.6591 | 0.7225 |
| loose_basis_gap_huber_alpha0p1__route_artist_reliable_n5_iqr090_gap080_cap005_s050 | 0.5453 | 0.5028 | 0.5700 |
| loose_basis_gap_huber_alpha0p1__route_artist_strict_n10_iqr075_gap065_cap005_s075 | 0.1753 | 0.1596 | 0.2010 |
| loose_basis_gap_huber_alpha0p1__route_broad_lowrisk_n30_iqr065_gap050_cap003_s075 | 0.0212 | 0.0200 | 0.0362 |
| loose_basis_gap_huber_alpha0p1__route_broad_reliable_n20_iqr080_gap080_cap005_s050 | 0.0597 | 0.0698 | 0.0774 |
| loose_basis_gap_huber_alpha0p1__route_coverage_high_n8_iqr100_gap100_cap003_s025 | 0.2813 | 0.2723 | 0.3064 |
| loose_basis_gap_huber_alpha0p1__route_detail_or_artist_n3_iqr080_gap060_cap003_s050 | 0.7225 | 0.6591 | 0.7225 |

## 6. 주요 계수

- HCOEF3 안정 후보와 basis-Huber 모델의 표준화 계수.
| candidate | model_type | target | feature | coefficient_on_scaled_feature | abs_coefficient | intercept |
| --- | --- | --- | --- | --- | --- | --- |
| hcoef2_size_reliability_cap005_s050 | huber_residual | residual_log | svc_fallback | -0.4718 | 0.4718 | 0.0101 |
| hcoef2_size_reliability_cap005_s050 | huber_residual | residual_log | shrunk_svc_prior | 0.2221 | 0.2221 | 0.0101 |
| hcoef2_size_reliability_cap005_s050 | huber_residual | residual_log | current_shrunk_huber_gap | 0.1308 | 0.1308 | 0.0101 |
| hcoef2_size_reliability_cap005_s050 | huber_residual | residual_log | ppv8_defensive | 0.1081 | 0.1081 | 0.0101 |
| hcoef2_size_reliability_cap005_s050 | huber_residual | residual_log | shrunk_huber_refit | 0.0877 | 0.0877 | 0.0101 |
| hcoef2_size_reliability_cap005_s050 | huber_residual | residual_log | raw_shrunk_prior_gap | -0.0580 | 0.0580 | 0.0101 |
| hcoef2_size_reliability_cap005_s050 | huber_residual | residual_log | log_area | 0.0570 | 0.0570 | 0.0101 |
| hcoef2_size_reliability_cap005_s050 | huber_residual | residual_log | current_ppv8_gap | 0.0491 | 0.0491 | 0.0101 |
| hcoef2_size_reliability_cap005_s050 | huber_residual | residual_log | svc_group_n_log | -0.0121 | 0.0121 | 0.0101 |
| hcoef2_size_reliability_cap005_s050 | huber_residual | residual_log | svc_prior_iqr | 0.0008 | 0.0008 | 0.0101 |
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

## 7. 잔차/큰 오차 요약

| split | candidate | n | median_residual_log | mean_residual_log | residual_std | over_2x_n | under_half_n | ape_gt_100pct_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_ex50 | hcoef2_size_reliability_cap005_s050 | 829 | 0.0608 | 0.3278 | 1.2668 | 26 | 152 | 26 |
| 0604_ex50 | loose_basis_core_huber_alpha0p01 | 829 | -0.0144 | 0.1390 | 0.8012 | 26 | 88 | 26 |
| 0604_ex50 | loose_basis_core_huber_alpha0p01__route_artist_reliable_n5_iqr090_gap080_cap005_s050 | 829 | 0.0617 | 0.3262 | 1.2663 | 26 | 152 | 26 |
| 0604_ex50 | loose_basis_core_huber_alpha0p01__route_artist_strict_n10_iqr075_gap065_cap005_s075 | 829 | 0.0647 | 0.3274 | 1.2666 | 26 | 152 | 26 |
| 0604_ex50 | loose_basis_core_huber_alpha0p01__route_broad_lowrisk_n30_iqr065_gap050_cap003_s075 | 829 | 0.0608 | 0.3278 | 1.2668 | 26 | 152 | 26 |
| 0604_ex50 | loose_basis_core_huber_alpha0p01__route_broad_reliable_n20_iqr080_gap080_cap005_s050 | 829 | 0.0617 | 0.3283 | 1.2665 | 26 | 152 | 26 |
| 0604_ex50 | loose_basis_core_huber_alpha0p01__route_coverage_high_n8_iqr100_gap100_cap003_s025 | 829 | 0.0608 | 0.3281 | 1.2666 | 26 | 152 | 26 |
| 0604_ex50 | loose_basis_core_huber_alpha0p01__route_detail_or_artist_n3_iqr080_gap060_cap003_s050 | 829 | 0.0617 | 0.3268 | 1.2660 | 24 | 152 | 24 |
| 0604_ex50 | loose_basis_core_huber_alpha0p1 | 829 | -0.0142 | 0.1387 | 0.7986 | 26 | 89 | 26 |
| 0604_ex50 | loose_basis_core_huber_alpha0p1__route_artist_reliable_n5_iqr090_gap080_cap005_s050 | 829 | 0.0619 | 0.3263 | 1.2663 | 26 | 152 | 26 |
| 0604_ex50 | loose_basis_core_huber_alpha0p1__route_artist_strict_n10_iqr075_gap065_cap005_s075 | 829 | 0.0648 | 0.3274 | 1.2666 | 26 | 152 | 26 |
| 0604_ex50 | loose_basis_core_huber_alpha0p1__route_broad_lowrisk_n30_iqr065_gap050_cap003_s075 | 829 | 0.0608 | 0.3278 | 1.2668 | 26 | 152 | 26 |
| 0604_ex50 | loose_basis_core_huber_alpha0p1__route_broad_reliable_n20_iqr080_gap080_cap005_s050 | 829 | 0.0619 | 0.3283 | 1.2665 | 26 | 152 | 26 |
| 0604_ex50 | loose_basis_core_huber_alpha0p1__route_coverage_high_n8_iqr100_gap100_cap003_s025 | 829 | 0.0608 | 0.3281 | 1.2666 | 26 | 152 | 26 |
| 0604_ex50 | loose_basis_core_huber_alpha0p1__route_detail_or_artist_n3_iqr080_gap060_cap003_s050 | 829 | 0.0619 | 0.3268 | 1.2660 | 24 | 152 | 24 |
| 0604_ex50 | loose_basis_gap_huber_alpha0p1 | 829 | -0.0043 | 0.1504 | 0.8072 | 26 | 90 | 26 |
| 0604_ex50 | loose_basis_gap_huber_alpha0p1__route_artist_reliable_n5_iqr090_gap080_cap005_s050 | 829 | 0.0641 | 0.3260 | 1.2664 | 26 | 151 | 26 |
| 0604_ex50 | loose_basis_gap_huber_alpha0p1__route_artist_strict_n10_iqr075_gap065_cap005_s075 | 829 | 0.0631 | 0.3275 | 1.2666 | 26 | 151 | 26 |
| 0604_ex50 | loose_basis_gap_huber_alpha0p1__route_broad_lowrisk_n30_iqr065_gap050_cap003_s075 | 829 | 0.0608 | 0.3278 | 1.2668 | 26 | 152 | 26 |
| 0604_ex50 | loose_basis_gap_huber_alpha0p1__route_broad_reliable_n20_iqr080_gap080_cap005_s050 | 829 | 0.0641 | 0.3287 | 1.2665 | 26 | 152 | 26 |
| 0604_ex50 | loose_basis_gap_huber_alpha0p1__route_coverage_high_n8_iqr100_gap100_cap003_s025 | 829 | 0.0608 | 0.3281 | 1.2667 | 26 | 152 | 26 |
| 0604_ex50 | loose_basis_gap_huber_alpha0p1__route_detail_or_artist_n3_iqr080_gap060_cap003_s050 | 829 | 0.0612 | 0.3268 | 1.2660 | 24 | 151 | 24 |
| test | hcoef2_size_reliability_cap005_s050 | 607 | -0.0039 | -0.0148 | 0.3989 | 26 | 17 | 26 |
| test | loose_basis_core_huber_alpha0p01 | 607 | -0.0015 | -0.0165 | 0.3896 | 25 | 14 | 25 |
| test | loose_basis_core_huber_alpha0p01__route_artist_reliable_n5_iqr090_gap080_cap005_s050 | 607 | -0.0011 | -0.0132 | 0.3976 | 26 | 17 | 26 |
| test | loose_basis_core_huber_alpha0p01__route_artist_strict_n10_iqr075_gap065_cap005_s075 | 607 | -0.0005 | -0.0137 | 0.3985 | 26 | 17 | 26 |
| test | loose_basis_core_huber_alpha0p01__route_broad_lowrisk_n30_iqr065_gap050_cap003_s075 | 607 | -0.0039 | -0.0143 | 0.3988 | 26 | 17 | 26 |
| test | loose_basis_core_huber_alpha0p01__route_broad_reliable_n20_iqr080_gap080_cap005_s050 | 607 | -0.0008 | -0.0143 | 0.3991 | 26 | 17 | 26 |
| test | loose_basis_core_huber_alpha0p01__route_coverage_high_n8_iqr100_gap100_cap003_s025 | 607 | -0.0009 | -0.0145 | 0.3987 | 26 | 17 | 26 |
| test | loose_basis_core_huber_alpha0p01__route_detail_or_artist_n3_iqr080_gap060_cap003_s050 | 607 | -0.0025 | -0.0143 | 0.3977 | 26 | 17 | 26 |
| test | loose_basis_core_huber_alpha0p1 | 607 | -0.0012 | -0.0163 | 0.3899 | 25 | 14 | 25 |
| test | loose_basis_core_huber_alpha0p1__route_artist_reliable_n5_iqr090_gap080_cap005_s050 | 607 | -0.0008 | -0.0131 | 0.3976 | 26 | 17 | 26 |
| test | loose_basis_core_huber_alpha0p1__route_artist_strict_n10_iqr075_gap065_cap005_s075 | 607 | -0.0005 | -0.0137 | 0.3985 | 26 | 17 | 26 |
| test | loose_basis_core_huber_alpha0p1__route_broad_lowrisk_n30_iqr065_gap050_cap003_s075 | 607 | -0.0039 | -0.0143 | 0.3988 | 26 | 17 | 26 |
| test | loose_basis_core_huber_alpha0p1__route_broad_reliable_n20_iqr080_gap080_cap005_s050 | 607 | -0.0006 | -0.0143 | 0.3991 | 26 | 17 | 26 |
| test | loose_basis_core_huber_alpha0p1__route_coverage_high_n8_iqr100_gap100_cap003_s025 | 607 | -0.0009 | -0.0145 | 0.3987 | 26 | 17 | 26 |
| test | loose_basis_core_huber_alpha0p1__route_detail_or_artist_n3_iqr080_gap060_cap003_s050 | 607 | -0.0009 | -0.0142 | 0.3977 | 26 | 17 | 26 |
| test | loose_basis_gap_huber_alpha0p1 | 607 | -0.0046 | -0.0166 | 0.3902 | 25 | 14 | 25 |
| test | loose_basis_gap_huber_alpha0p1__route_artist_reliable_n5_iqr090_gap080_cap005_s050 | 607 | -0.0026 | -0.0135 | 0.3976 | 26 | 17 | 26 |
| test | loose_basis_gap_huber_alpha0p1__route_artist_strict_n10_iqr075_gap065_cap005_s075 | 607 | -0.0005 | -0.0135 | 0.3985 | 26 | 17 | 26 |
| test | loose_basis_gap_huber_alpha0p1__route_broad_lowrisk_n30_iqr065_gap050_cap003_s075 | 607 | -0.0028 | -0.0142 | 0.3988 | 26 | 17 | 26 |
| test | loose_basis_gap_huber_alpha0p1__route_broad_reliable_n20_iqr080_gap080_cap005_s050 | 607 | -0.0005 | -0.0141 | 0.3990 | 26 | 17 | 26 |
| test | loose_basis_gap_huber_alpha0p1__route_coverage_high_n8_iqr100_gap100_cap003_s025 | 607 | -0.0009 | -0.0145 | 0.3987 | 26 | 17 | 26 |
| test | loose_basis_gap_huber_alpha0p1__route_detail_or_artist_n3_iqr080_gap060_cap003_s050 | 607 | -0.0026 | -0.0143 | 0.3977 | 26 | 17 | 26 |
| validation | hcoef2_size_reliability_cap005_s050 | 519 | 0.0021 | 0.0181 | 0.3250 | 9 | 10 | 9 |
| validation | loose_basis_core_huber_alpha0p01 | 519 | -0.0042 | 0.0119 | 0.3088 | 7 | 11 | 7 |
| validation | loose_basis_core_huber_alpha0p01__route_artist_reliable_n5_iqr090_gap080_cap005_s050 | 519 | 0.0020 | 0.0189 | 0.3243 | 9 | 10 | 9 |
| validation | loose_basis_core_huber_alpha0p01__route_artist_strict_n10_iqr075_gap065_cap005_s075 | 519 | 0.0052 | 0.0199 | 0.3253 | 9 | 10 | 9 |
| validation | loose_basis_core_huber_alpha0p01__route_broad_lowrisk_n30_iqr065_gap050_cap003_s075 | 519 | 0.0021 | 0.0185 | 0.3250 | 9 | 10 | 9 |
| validation | loose_basis_core_huber_alpha0p01__route_broad_reliable_n20_iqr080_gap080_cap005_s050 | 519 | 0.0036 | 0.0187 | 0.3250 | 9 | 10 | 9 |

## 8. 다음 보정 방향

- 조건부 routing 후보가 p95 guard를 통과하지 못하면, basis-Huber를 전체 모델로 쓰기보다 원인 분석용 피처로 유지.
- routing 조건이 너무 좁아 개선폭이 작으면, `basis_relaxed_unit_area_log`를 HCOEF3 residual 피처로 직접 넣는 저차원 Huber 실험으로 이동.
- 특정 기준가 level에서만 좋아지는 경우, 크기/표본 수/재료 구간별 segmented Huber 계수 실험으로 이동.

## 9. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/residual_analysis.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `outputs/repeated_validation_metrics.csv`
- `outputs/routing_rules.csv`
- `outputs/selected_candidates.csv`
- `artifacts/experiment_config.json`