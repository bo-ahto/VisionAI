# PP-HCOEF8 Warm Huber segmented 보정 실험

- 작성일: 2026-06-07 23:24
- 목적: HCOEF7의 면적단가/기준가 신뢰도 잔차 피처 개선 신호를 유지하되, p95 위험 구간에는 약한 보정 또는 무보정을 적용.
- 기준 후보: `hcoef2_size_reliability_cap005_s050`.
- 방식: Huber raw residual을 학습한 뒤 low/mid/high basis-risk 구간별 cap/strength를 다르게 적용.
- 후보 선택: 반복 OOF 우선, fixed test는 최종 확인용.

## 1. 실행 결론

- 새 운영 기본 후보 채택 없음.

## 2. 후보 선택표

| candidate | row_all3_prob | artist_all3_prob | row_delta_MdAPE | row_delta_MAPE | row_delta_p95_APE | artist_delta_MdAPE | artist_delta_MAPE | artist_delta_p95_APE | test_delta_MdAPE | test_delta_MAPE | test_delta_p95_APE | ops0604_delta_MdAPE | ops0604_delta_MAPE | ops0604_delta_p95_APE | passes_repeat_gate | passes_fixed_guard | purpose |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef2_size_reliability_cap005_s050 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | False | hold_or_reject |
| hcoef8_unit_area_reliability_alpha0.01_low_medium_mid_light_high_none | 0.0000 | 0.0000 | 0.0019 | 0.0018 | 0.0101 | 0.0010 | 0.0015 | 0.0108 | 0.0017 | 0.0015 | 0.0288 | 0.0039 | 0.0021 | 0.0036 | False | False | hold_or_reject |
| hcoef8_unit_area_reliability_alpha0.001_low_medium_mid_light_high_none | 0.0000 | 0.0000 | 0.0019 | 0.0018 | 0.0101 | 0.0010 | 0.0015 | 0.0108 | 0.0017 | 0.0015 | 0.0288 | 0.0039 | 0.0021 | 0.0036 | False | False | hold_or_reject |
| hcoef8_risk_flags_alpha0.001_low_medium_mid_light_high_none | 0.0000 | 0.0000 | 0.0020 | 0.0019 | 0.0103 | 0.0010 | 0.0017 | 0.0103 | 0.0010 | 0.0023 | 0.0294 | 0.0039 | 0.0026 | 0.0036 | False | False | hold_or_reject |
| hcoef8_risk_flags_alpha0.01_low_medium_mid_light_high_none | 0.0000 | 0.0000 | 0.0020 | 0.0019 | 0.0103 | 0.0010 | 0.0017 | 0.0103 | 0.0010 | 0.0023 | 0.0294 | 0.0039 | 0.0026 | 0.0036 | False | False | hold_or_reject |
| hcoef8_shrunk_basis_gap_alpha0.001_low_medium_mid_light_high_none | 0.0000 | 0.0000 | 0.0021 | 0.0017 | 0.0107 | 0.0010 | 0.0014 | 0.0109 | 0.0024 | 0.0015 | 0.0294 | 0.0039 | 0.0020 | 0.0036 | False | False | hold_or_reject |
| hcoef8_shrunk_basis_gap_alpha0.01_low_medium_mid_light_high_none | 0.0000 | 0.0000 | 0.0021 | 0.0017 | 0.0107 | 0.0010 | 0.0014 | 0.0109 | 0.0024 | 0.0015 | 0.0294 | 0.0039 | 0.0020 | 0.0036 | False | False | hold_or_reject |
| hcoef8_risk_flags_alpha0.01_all_tiny_low_priority | 0.0000 | 0.0000 | 0.0023 | 0.0017 | 0.0113 | 0.0014 | 0.0014 | 0.0107 | 0.0015 | 0.0019 | 0.0276 | 0.0042 | 0.0023 | 0.0036 | False | False | hold_or_reject |
| hcoef8_risk_flags_alpha0.001_all_tiny_low_priority | 0.0000 | 0.0000 | 0.0023 | 0.0017 | 0.0113 | 0.0014 | 0.0014 | 0.0107 | 0.0015 | 0.0019 | 0.0276 | 0.0042 | 0.0023 | 0.0036 | False | False | hold_or_reject |
| hcoef8_unit_area_reliability_alpha0.001_low_strong_mid_light_high_none | 0.0000 | 0.0000 | 0.0026 | 0.0019 | 0.0099 | 0.0026 | 0.0016 | 0.0111 | 0.0048 | 0.0016 | 0.0288 | 0.0027 | 0.0018 | 0.0036 | False | False | hold_or_reject |
| hcoef8_unit_area_reliability_alpha0.01_low_strong_mid_light_high_none | 0.0000 | 0.0000 | 0.0026 | 0.0019 | 0.0099 | 0.0026 | 0.0016 | 0.0111 | 0.0048 | 0.0016 | 0.0288 | 0.0027 | 0.0018 | 0.0036 | False | False | hold_or_reject |
| hcoef8_unit_area_reliability_alpha0.01_all_tiny_low_priority | 0.0000 | 0.0000 | 0.0026 | 0.0016 | 0.0115 | 0.0017 | 0.0013 | 0.0117 | 0.0015 | 0.0014 | 0.0271 | 0.0042 | 0.0021 | 0.0036 | False | False | hold_or_reject |
| hcoef8_unit_area_reliability_alpha0.001_all_tiny_low_priority | 0.0000 | 0.0000 | 0.0026 | 0.0016 | 0.0115 | 0.0017 | 0.0013 | 0.0117 | 0.0015 | 0.0014 | 0.0271 | 0.0042 | 0.0021 | 0.0036 | False | False | hold_or_reject |
| hcoef8_shrunk_basis_gap_alpha0.001_all_tiny_low_priority | 0.0000 | 0.0000 | 0.0028 | 0.0015 | 0.0119 | 0.0016 | 0.0012 | 0.0117 | 0.0007 | 0.0014 | 0.0276 | 0.0042 | 0.0020 | 0.0036 | False | False | hold_or_reject |
| hcoef8_shrunk_basis_gap_alpha0.01_all_tiny_low_priority | 0.0000 | 0.0000 | 0.0028 | 0.0015 | 0.0119 | 0.0016 | 0.0012 | 0.0117 | 0.0007 | 0.0014 | 0.0276 | 0.0042 | 0.0020 | 0.0036 | False | False | hold_or_reject |
| hcoef8_unit_area_reliability_alpha0.01_low_mid_balanced_high_none | 0.0000 | 0.0000 | 0.0030 | 0.0018 | 0.0101 | 0.0025 | 0.0014 | 0.0116 | 0.0029 | 0.0010 | 0.0308 | -0.0003 | 0.0009 | 0.0036 | False | False | hold_or_reject |
| hcoef8_unit_area_reliability_alpha0.001_low_mid_balanced_high_none | 0.0000 | 0.0000 | 0.0030 | 0.0018 | 0.0101 | 0.0025 | 0.0014 | 0.0116 | 0.0029 | 0.0010 | 0.0308 | -0.0003 | 0.0009 | 0.0036 | False | False | hold_or_reject |
| hcoef8_risk_flags_alpha0.01_low_mid_balanced_high_none | 0.0000 | 0.0000 | 0.0031 | 0.0018 | 0.0103 | 0.0022 | 0.0017 | 0.0108 | 0.0029 | 0.0019 | 0.0346 | -0.0003 | 0.0012 | 0.0036 | False | False | hold_or_reject |
| hcoef8_risk_flags_alpha0.001_low_mid_balanced_high_none | 0.0000 | 0.0000 | 0.0031 | 0.0018 | 0.0103 | 0.0022 | 0.0017 | 0.0107 | 0.0029 | 0.0019 | 0.0346 | -0.0003 | 0.0012 | 0.0036 | False | False | hold_or_reject |
| hcoef8_shrunk_basis_gap_alpha0.01_low_strong_mid_light_high_none | 0.0000 | 0.0000 | 0.0031 | 0.0018 | 0.0109 | 0.0023 | 0.0014 | 0.0112 | 0.0059 | 0.0016 | 0.0297 | 0.0027 | 0.0017 | 0.0036 | False | False | hold_or_reject |
| hcoef8_shrunk_basis_gap_alpha0.001_low_strong_mid_light_high_none | 0.0000 | 0.0000 | 0.0031 | 0.0018 | 0.0108 | 0.0023 | 0.0015 | 0.0112 | 0.0059 | 0.0016 | 0.0297 | 0.0027 | 0.0017 | 0.0036 | False | False | hold_or_reject |
| hcoef8_risk_flags_alpha0.01_low_strong_mid_light_high_none | 0.0000 | 0.0000 | 0.0031 | 0.0021 | 0.0100 | 0.0024 | 0.0019 | 0.0105 | 0.0048 | 0.0026 | 0.0308 | 0.0027 | 0.0023 | 0.0036 | False | False | hold_or_reject |
| hcoef8_risk_flags_alpha0.001_low_strong_mid_light_high_none | 0.0000 | 0.0000 | 0.0031 | 0.0021 | 0.0100 | 0.0024 | 0.0019 | 0.0105 | 0.0048 | 0.0026 | 0.0308 | 0.0027 | 0.0023 | 0.0036 | False | False | hold_or_reject |
| hcoef8_unit_area_reliability_alpha0.001_artist_low_only_strong | 0.0000 | 0.0000 | 0.0031 | 0.0020 | 0.0111 | 0.0026 | 0.0017 | 0.0108 | 0.0053 | 0.0020 | 0.0267 | 0.0049 | 0.0025 | 0.0036 | False | False | hold_or_reject |

## 3. 반복 OOF 요약

| validation_scheme | candidate | mean_delta_MdAPE_vs_hcoef2 | mean_delta_MAPE_vs_hcoef2 | mean_delta_p95_APE_vs_hcoef2 | std_delta_MdAPE_vs_hcoef2 | MdAPE_improve_prob_vs_hcoef2 | MAPE_improve_prob_vs_hcoef2 | p95_improve_prob_vs_hcoef2 | all3_improve_prob_vs_hcoef2 | mean_improve_count_vs_hcoef2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| artist_oof | hcoef2_size_reliability_cap005_s050 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| row_oof | hcoef2_size_reliability_cap005_s050 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| artist_oof | hcoef8_shrunk_basis_gap_alpha0.01_low_medium_mid_light_high_none | 0.0010 | 0.0014 | 0.0109 | 0.0014 | 0.3333 | 0.0000 | 0.0000 | 0.0000 | 0.3333 |
| artist_oof | hcoef8_shrunk_basis_gap_alpha0.001_low_medium_mid_light_high_none | 0.0010 | 0.0014 | 0.0109 | 0.0014 | 0.3333 | 0.0000 | 0.0000 | 0.0000 | 0.3333 |
| artist_oof | hcoef8_unit_area_reliability_alpha0.01_low_medium_mid_light_high_none | 0.0010 | 0.0015 | 0.0108 | 0.0014 | 0.2500 | 0.0000 | 0.0000 | 0.0000 | 0.2500 |
| artist_oof | hcoef8_unit_area_reliability_alpha0.001_low_medium_mid_light_high_none | 0.0010 | 0.0015 | 0.0108 | 0.0014 | 0.2500 | 0.0000 | 0.0000 | 0.0000 | 0.2500 |
| artist_oof | hcoef8_risk_flags_alpha0.01_low_medium_mid_light_high_none | 0.0010 | 0.0017 | 0.0103 | 0.0014 | 0.2500 | 0.0000 | 0.0000 | 0.0000 | 0.2500 |
| artist_oof | hcoef8_risk_flags_alpha0.001_low_medium_mid_light_high_none | 0.0010 | 0.0017 | 0.0103 | 0.0014 | 0.2500 | 0.0000 | 0.0000 | 0.0000 | 0.2500 |
| artist_oof | hcoef8_risk_flags_alpha0.01_all_tiny_low_priority | 0.0014 | 0.0014 | 0.0107 | 0.0016 | 0.1667 | 0.0000 | 0.0000 | 0.0000 | 0.1667 |
| artist_oof | hcoef8_risk_flags_alpha0.001_all_tiny_low_priority | 0.0014 | 0.0014 | 0.0107 | 0.0016 | 0.1667 | 0.0000 | 0.0000 | 0.0000 | 0.1667 |
| artist_oof | hcoef8_shrunk_basis_gap_alpha0.001_all_tiny_low_priority | 0.0016 | 0.0012 | 0.0117 | 0.0015 | 0.0833 | 0.0000 | 0.0000 | 0.0000 | 0.0833 |
| artist_oof | hcoef8_shrunk_basis_gap_alpha0.01_all_tiny_low_priority | 0.0016 | 0.0012 | 0.0117 | 0.0015 | 0.0833 | 0.0000 | 0.0000 | 0.0000 | 0.0833 |
| artist_oof | hcoef8_unit_area_reliability_alpha0.01_all_tiny_low_priority | 0.0017 | 0.0013 | 0.0117 | 0.0014 | 0.0833 | 0.0000 | 0.0000 | 0.0000 | 0.0833 |
| artist_oof | hcoef8_unit_area_reliability_alpha0.001_all_tiny_low_priority | 0.0017 | 0.0013 | 0.0117 | 0.0014 | 0.0833 | 0.0000 | 0.0000 | 0.0000 | 0.0833 |
| row_oof | hcoef8_unit_area_reliability_alpha0.01_low_medium_mid_light_high_none | 0.0019 | 0.0018 | 0.0101 | 0.0011 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| row_oof | hcoef8_unit_area_reliability_alpha0.001_low_medium_mid_light_high_none | 0.0019 | 0.0018 | 0.0101 | 0.0011 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| row_oof | hcoef8_risk_flags_alpha0.01_low_medium_mid_light_high_none | 0.0020 | 0.0019 | 0.0103 | 0.0011 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| row_oof | hcoef8_risk_flags_alpha0.001_low_medium_mid_light_high_none | 0.0020 | 0.0019 | 0.0103 | 0.0011 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| row_oof | hcoef8_shrunk_basis_gap_alpha0.01_low_medium_mid_light_high_none | 0.0021 | 0.0017 | 0.0107 | 0.0012 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| row_oof | hcoef8_shrunk_basis_gap_alpha0.001_low_medium_mid_light_high_none | 0.0021 | 0.0017 | 0.0107 | 0.0012 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| artist_oof | hcoef8_shrunk_basis_gap_alpha0.001_low_mid_balanced_high_none | 0.0022 | 0.0012 | 0.0116 | 0.0013 | 0.0833 | 0.0000 | 0.0000 | 0.0000 | 0.0833 |
| artist_oof | hcoef8_shrunk_basis_gap_alpha0.01_low_mid_balanced_high_none | 0.0022 | 0.0012 | 0.0116 | 0.0013 | 0.0833 | 0.0000 | 0.0000 | 0.0000 | 0.0833 |
| artist_oof | hcoef8_risk_flags_alpha0.01_low_mid_balanced_high_none | 0.0022 | 0.0017 | 0.0108 | 0.0015 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| artist_oof | hcoef8_risk_flags_alpha0.001_low_mid_balanced_high_none | 0.0022 | 0.0017 | 0.0107 | 0.0015 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| artist_oof | hcoef8_shrunk_basis_gap_alpha0.001_artist_low_only_strong | 0.0022 | 0.0017 | 0.0108 | 0.0015 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| artist_oof | hcoef8_shrunk_basis_gap_alpha0.01_artist_low_only_strong | 0.0022 | 0.0017 | 0.0108 | 0.0015 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| artist_oof | hcoef8_risk_flags_alpha0.01_artist_low_only_strong | 0.0022 | 0.0020 | 0.0108 | 0.0011 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| artist_oof | hcoef8_risk_flags_alpha0.001_artist_low_only_strong | 0.0023 | 0.0020 | 0.0108 | 0.0011 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| artist_oof | hcoef8_shrunk_basis_gap_alpha0.001_low_only_medium | 0.0023 | 0.0016 | 0.0108 | 0.0017 | 0.0833 | 0.0000 | 0.0000 | 0.0000 | 0.0833 |
| artist_oof | hcoef8_shrunk_basis_gap_alpha0.01_low_only_medium | 0.0023 | 0.0016 | 0.0108 | 0.0017 | 0.0833 | 0.0000 | 0.0000 | 0.0000 | 0.0833 |
| row_oof | hcoef8_risk_flags_alpha0.01_all_tiny_low_priority | 0.0023 | 0.0017 | 0.0113 | 0.0014 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| row_oof | hcoef8_risk_flags_alpha0.001_all_tiny_low_priority | 0.0023 | 0.0017 | 0.0113 | 0.0014 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## 4. Fixed test 상위 후보

| candidate | method | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_hcoef2 | delta_MAPE_vs_hcoef2 | delta_p95_APE_vs_hcoef2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef2_size_reliability_cap005_s050 | hcoef2_stable | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 |
| hcoef8_shrunk_basis_gap_alpha0.01_all_tiny_low_priority | segmented_unit_area_residual_huber | 0.1395 | 0.2744 | 0.8340 | 0.3992 | 0.0007 | 0.0014 | 0.0276 |
| hcoef8_shrunk_basis_gap_alpha0.001_all_tiny_low_priority | segmented_unit_area_residual_huber | 0.1395 | 0.2744 | 0.8340 | 0.3992 | 0.0007 | 0.0014 | 0.0276 |
| hcoef8_unit_area_reliability_alpha0.01_low_only_medium | segmented_unit_area_residual_huber | 0.1398 | 0.2748 | 0.8331 | 0.3994 | 0.0010 | 0.0019 | 0.0267 |
| hcoef8_unit_area_reliability_alpha0.001_low_only_medium | segmented_unit_area_residual_huber | 0.1398 | 0.2748 | 0.8331 | 0.3994 | 0.0010 | 0.0019 | 0.0267 |
| hcoef8_risk_flags_alpha0.001_low_medium_mid_light_high_none | segmented_unit_area_residual_huber | 0.1398 | 0.2753 | 0.8358 | 0.3995 | 0.0010 | 0.0023 | 0.0294 |
| hcoef8_risk_flags_alpha0.01_low_medium_mid_light_high_none | segmented_unit_area_residual_huber | 0.1398 | 0.2753 | 0.8358 | 0.3995 | 0.0010 | 0.0023 | 0.0294 |
| hcoef8_unit_area_reliability_alpha0.01_all_tiny_low_priority | segmented_unit_area_residual_huber | 0.1403 | 0.2744 | 0.8334 | 0.3992 | 0.0015 | 0.0014 | 0.0271 |
| hcoef8_unit_area_reliability_alpha0.001_all_tiny_low_priority | segmented_unit_area_residual_huber | 0.1403 | 0.2744 | 0.8334 | 0.3992 | 0.0015 | 0.0014 | 0.0271 |
| hcoef8_risk_flags_alpha0.001_all_tiny_low_priority | segmented_unit_area_residual_huber | 0.1403 | 0.2749 | 0.8340 | 0.3994 | 0.0015 | 0.0019 | 0.0276 |
| hcoef8_risk_flags_alpha0.01_all_tiny_low_priority | segmented_unit_area_residual_huber | 0.1403 | 0.2749 | 0.8340 | 0.3994 | 0.0015 | 0.0019 | 0.0276 |
| hcoef8_unit_area_reliability_alpha0.01_low_medium_mid_light_high_none | segmented_unit_area_residual_huber | 0.1405 | 0.2745 | 0.8351 | 0.3992 | 0.0017 | 0.0015 | 0.0288 |
| hcoef8_unit_area_reliability_alpha0.001_low_medium_mid_light_high_none | segmented_unit_area_residual_huber | 0.1405 | 0.2745 | 0.8351 | 0.3992 | 0.0017 | 0.0015 | 0.0288 |
| hcoef8_shrunk_basis_gap_alpha0.01_low_medium_mid_light_high_none | segmented_unit_area_residual_huber | 0.1412 | 0.2745 | 0.8358 | 0.3992 | 0.0024 | 0.0015 | 0.0294 |
| hcoef8_shrunk_basis_gap_alpha0.001_low_medium_mid_light_high_none | segmented_unit_area_residual_huber | 0.1412 | 0.2745 | 0.8358 | 0.3992 | 0.0024 | 0.0015 | 0.0294 |
| hcoef8_shrunk_basis_gap_alpha0.001_low_mid_balanced_high_none | segmented_unit_area_residual_huber | 0.1415 | 0.2739 | 0.8392 | 0.3987 | 0.0027 | 0.0009 | 0.0328 |
| hcoef8_shrunk_basis_gap_alpha0.01_low_mid_balanced_high_none | segmented_unit_area_residual_huber | 0.1415 | 0.2739 | 0.8392 | 0.3987 | 0.0027 | 0.0009 | 0.0328 |
| hcoef8_risk_flags_alpha0.01_low_only_medium | segmented_unit_area_residual_huber | 0.1415 | 0.2755 | 0.8331 | 0.3997 | 0.0027 | 0.0025 | 0.0267 |
| hcoef8_risk_flags_alpha0.001_low_only_medium | segmented_unit_area_residual_huber | 0.1415 | 0.2755 | 0.8331 | 0.3997 | 0.0027 | 0.0025 | 0.0267 |
| hcoef8_unit_area_reliability_alpha0.001_low_mid_balanced_high_none | segmented_unit_area_residual_huber | 0.1417 | 0.2740 | 0.8372 | 0.3988 | 0.0029 | 0.0010 | 0.0308 |
| hcoef8_unit_area_reliability_alpha0.01_low_mid_balanced_high_none | segmented_unit_area_residual_huber | 0.1417 | 0.2740 | 0.8372 | 0.3988 | 0.0029 | 0.0010 | 0.0308 |
| hcoef8_risk_flags_alpha0.001_low_mid_balanced_high_none | segmented_unit_area_residual_huber | 0.1417 | 0.2749 | 0.8410 | 0.3991 | 0.0029 | 0.0019 | 0.0346 |
| hcoef8_risk_flags_alpha0.01_low_mid_balanced_high_none | segmented_unit_area_residual_huber | 0.1417 | 0.2749 | 0.8410 | 0.3991 | 0.0029 | 0.0019 | 0.0346 |
| hcoef8_shrunk_basis_gap_alpha0.01_low_only_medium | segmented_unit_area_residual_huber | 0.1422 | 0.2749 | 0.8331 | 0.3994 | 0.0034 | 0.0019 | 0.0267 |

## 5. Segment 적용 비율

| candidate | low_share_mean | mid_share_mean | high_share_mean |
| --- | --- | --- | --- |
| hcoef8_risk_flags_alpha0.001_all_tiny_low_priority | 0.1662 | 0.3742 | 0.4596 |
| hcoef8_risk_flags_alpha0.001_artist_low_only_strong | 0.1582 | 0.3822 | 0.4596 |
| hcoef8_risk_flags_alpha0.001_low_medium_mid_light_high_none | 0.1662 | 0.3742 | 0.4596 |
| hcoef8_risk_flags_alpha0.001_low_mid_balanced_high_none | 0.1662 | 0.3742 | 0.4596 |
| hcoef8_risk_flags_alpha0.001_low_only_medium | 0.1662 | 0.3742 | 0.4596 |
| hcoef8_risk_flags_alpha0.001_low_strong_mid_light_high_none | 0.1662 | 0.3742 | 0.4596 |
| hcoef8_risk_flags_alpha0.01_all_tiny_low_priority | 0.1662 | 0.3742 | 0.4596 |
| hcoef8_risk_flags_alpha0.01_artist_low_only_strong | 0.1582 | 0.3822 | 0.4596 |
| hcoef8_risk_flags_alpha0.01_low_medium_mid_light_high_none | 0.1662 | 0.3742 | 0.4596 |
| hcoef8_risk_flags_alpha0.01_low_mid_balanced_high_none | 0.1662 | 0.3742 | 0.4596 |
| hcoef8_risk_flags_alpha0.01_low_only_medium | 0.1662 | 0.3742 | 0.4596 |
| hcoef8_risk_flags_alpha0.01_low_strong_mid_light_high_none | 0.1662 | 0.3742 | 0.4596 |
| hcoef8_shrunk_basis_gap_alpha0.001_all_tiny_low_priority | 0.1662 | 0.3742 | 0.4596 |
| hcoef8_shrunk_basis_gap_alpha0.001_artist_low_only_strong | 0.1582 | 0.3822 | 0.4596 |
| hcoef8_shrunk_basis_gap_alpha0.001_low_medium_mid_light_high_none | 0.1662 | 0.3742 | 0.4596 |
| hcoef8_shrunk_basis_gap_alpha0.001_low_mid_balanced_high_none | 0.1662 | 0.3742 | 0.4596 |
| hcoef8_shrunk_basis_gap_alpha0.001_low_only_medium | 0.1662 | 0.3742 | 0.4596 |
| hcoef8_shrunk_basis_gap_alpha0.001_low_strong_mid_light_high_none | 0.1662 | 0.3742 | 0.4596 |
| hcoef8_shrunk_basis_gap_alpha0.01_all_tiny_low_priority | 0.1662 | 0.3742 | 0.4596 |
| hcoef8_shrunk_basis_gap_alpha0.01_artist_low_only_strong | 0.1582 | 0.3822 | 0.4596 |
| hcoef8_shrunk_basis_gap_alpha0.01_low_medium_mid_light_high_none | 0.1662 | 0.3742 | 0.4596 |
| hcoef8_shrunk_basis_gap_alpha0.01_low_mid_balanced_high_none | 0.1662 | 0.3742 | 0.4596 |
| hcoef8_shrunk_basis_gap_alpha0.01_low_only_medium | 0.1662 | 0.3742 | 0.4596 |
| hcoef8_shrunk_basis_gap_alpha0.01_low_strong_mid_light_high_none | 0.1662 | 0.3742 | 0.4596 |

## 6. 주요 계수

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
| hcoef8_unit_area_reliability_alpha0.01 | huber_residual_raw | residual_log | svc_fallback | -0.2914 | 0.2914 | 0.0103 |
| hcoef8_unit_area_reliability_alpha0.01 | huber_residual_raw | residual_log | shrunk_svc_prior | 0.2391 | 0.2391 | 0.0103 |
| hcoef8_unit_area_reliability_alpha0.01 | huber_residual_raw | residual_log | basis_unit_gap | 0.0866 | 0.0866 | 0.0103 |
| hcoef8_unit_area_reliability_alpha0.01 | huber_residual_raw | residual_log | current_shrunk_huber_gap | 0.0751 | 0.0751 | 0.0103 |
| hcoef8_unit_area_reliability_alpha0.01 | huber_residual_raw | residual_log | basis_shrunk_weight | -0.0523 | 0.0523 | 0.0103 |
| hcoef8_unit_area_reliability_alpha0.01 | huber_residual_raw | residual_log | basis_relaxed_n_log | 0.0443 | 0.0443 | 0.0103 |
| hcoef8_unit_area_reliability_alpha0.01 | huber_residual_raw | residual_log | log_area | 0.0366 | 0.0366 | 0.0103 |
| hcoef8_unit_area_reliability_alpha0.01 | huber_residual_raw | residual_log | raw_shrunk_prior_gap | -0.0356 | 0.0356 | 0.0103 |
| hcoef8_unit_area_reliability_alpha0.01 | huber_residual_raw | residual_log | basis_relaxed_unit_area_log | 0.0243 | 0.0243 | 0.0103 |
| hcoef8_unit_area_reliability_alpha0.01 | huber_residual_raw | residual_log | shrunk_huber_refit | -0.0133 | 0.0133 | 0.0103 |
| hcoef8_unit_area_reliability_alpha0.01 | huber_residual_raw | residual_log | svc_prior_iqr | 0.0103 | 0.0103 | 0.0103 |
| hcoef8_unit_area_reliability_alpha0.01 | huber_residual_raw | residual_log | svc_group_n_log | -0.0100 | 0.0100 | 0.0103 |
| hcoef8_unit_area_reliability_alpha0.01 | huber_residual_raw | residual_log | basis_relaxed_iqr | -0.0087 | 0.0087 | 0.0103 |
| hcoef8_unit_area_reliability_alpha0.01 | huber_residual_raw | residual_log | current_ppv8_gap | -0.0075 | 0.0075 | 0.0103 |
| hcoef8_unit_area_reliability_alpha0.01 | huber_residual_raw | residual_log | ppv8_defensive | 0.0058 | 0.0058 | 0.0103 |
| hcoef8_unit_area_reliability_alpha0.001 | huber_residual_raw | residual_log | svc_fallback | -0.2931 | 0.2931 | 0.0103 |
| hcoef8_unit_area_reliability_alpha0.001 | huber_residual_raw | residual_log | shrunk_svc_prior | 0.2392 | 0.2392 | 0.0103 |
| hcoef8_unit_area_reliability_alpha0.001 | huber_residual_raw | residual_log | basis_unit_gap | 0.0865 | 0.0865 | 0.0103 |
| hcoef8_unit_area_reliability_alpha0.001 | huber_residual_raw | residual_log | current_shrunk_huber_gap | 0.0753 | 0.0753 | 0.0103 |
| hcoef8_unit_area_reliability_alpha0.001 | huber_residual_raw | residual_log | basis_shrunk_weight | -0.0523 | 0.0523 | 0.0103 |
| hcoef8_unit_area_reliability_alpha0.001 | huber_residual_raw | residual_log | basis_relaxed_n_log | 0.0443 | 0.0443 | 0.0103 |
| hcoef8_unit_area_reliability_alpha0.001 | huber_residual_raw | residual_log | log_area | 0.0366 | 0.0366 | 0.0103 |
| hcoef8_unit_area_reliability_alpha0.001 | huber_residual_raw | residual_log | raw_shrunk_prior_gap | -0.0356 | 0.0356 | 0.0103 |
| hcoef8_unit_area_reliability_alpha0.001 | huber_residual_raw | residual_log | basis_relaxed_unit_area_log | 0.0248 | 0.0248 | 0.0103 |
| hcoef8_unit_area_reliability_alpha0.001 | huber_residual_raw | residual_log | shrunk_huber_refit | -0.0127 | 0.0127 | 0.0103 |
| hcoef8_unit_area_reliability_alpha0.001 | huber_residual_raw | residual_log | svc_prior_iqr | 0.0103 | 0.0103 | 0.0103 |
| hcoef8_unit_area_reliability_alpha0.001 | huber_residual_raw | residual_log | svc_group_n_log | -0.0100 | 0.0100 | 0.0103 |
| hcoef8_unit_area_reliability_alpha0.001 | huber_residual_raw | residual_log | basis_relaxed_iqr | -0.0087 | 0.0087 | 0.0103 |
| hcoef8_unit_area_reliability_alpha0.001 | huber_residual_raw | residual_log | current_ppv8_gap | -0.0073 | 0.0073 | 0.0103 |
| hcoef8_unit_area_reliability_alpha0.001 | huber_residual_raw | residual_log | ppv8_defensive | 0.0064 | 0.0064 | 0.0103 |
| hcoef8_shrunk_basis_gap_alpha0.01 | huber_residual_raw | residual_log | shrunk_svc_prior | 0.3381 | 0.3381 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.01 | huber_residual_raw | residual_log | svc_fallback | -0.3280 | 0.3280 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.01 | huber_residual_raw | residual_log | basis_unit_gap | 0.0864 | 0.0864 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.01 | huber_residual_raw | residual_log | current_shrunk_huber_gap | 0.0792 | 0.0792 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.01 | huber_residual_raw | residual_log | basis_shrunk_weight | -0.0518 | 0.0518 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.01 | huber_residual_raw | residual_log | basis_relaxed_n_log | 0.0438 | 0.0438 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.01 | huber_residual_raw | residual_log | basis_shrunk_vs_current_gap | -0.0356 | 0.0356 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.01 | huber_residual_raw | residual_log | log_area | 0.0341 | 0.0341 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.01 | huber_residual_raw | residual_log | basis_shrunk_price_log | -0.0321 | 0.0321 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.01 | huber_residual_raw | residual_log | shrunk_huber_refit | -0.0304 | 0.0304 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.01 | huber_residual_raw | residual_log | raw_shrunk_prior_gap | -0.0163 | 0.0163 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.01 | huber_residual_raw | residual_log | svc_prior_iqr | 0.0117 | 0.0117 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.01 | huber_residual_raw | residual_log | basis_relaxed_unit_area_log | 0.0102 | 0.0102 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.01 | huber_residual_raw | residual_log | svc_group_n_log | -0.0100 | 0.0100 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.01 | huber_residual_raw | residual_log | ppv8_defensive | -0.0095 | 0.0095 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.01 | huber_residual_raw | residual_log | basis_relaxed_iqr | -0.0091 | 0.0091 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.01 | huber_residual_raw | residual_log | current_ppv8_gap | -0.0086 | 0.0086 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.001 | huber_residual_raw | residual_log | shrunk_svc_prior | 0.3383 | 0.3383 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.001 | huber_residual_raw | residual_log | svc_fallback | -0.3306 | 0.3306 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.001 | huber_residual_raw | residual_log | basis_unit_gap | 0.0863 | 0.0863 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.001 | huber_residual_raw | residual_log | current_shrunk_huber_gap | 0.0794 | 0.0794 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.001 | huber_residual_raw | residual_log | basis_shrunk_weight | -0.0520 | 0.0520 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.001 | huber_residual_raw | residual_log | basis_relaxed_n_log | 0.0441 | 0.0441 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.001 | huber_residual_raw | residual_log | basis_shrunk_vs_current_gap | -0.0360 | 0.0360 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.001 | huber_residual_raw | residual_log | log_area | 0.0341 | 0.0341 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.001 | huber_residual_raw | residual_log | basis_shrunk_price_log | -0.0316 | 0.0316 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.001 | huber_residual_raw | residual_log | shrunk_huber_refit | -0.0298 | 0.0298 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.001 | huber_residual_raw | residual_log | raw_shrunk_prior_gap | -0.0162 | 0.0162 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.001 | huber_residual_raw | residual_log | svc_prior_iqr | 0.0117 | 0.0117 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.001 | huber_residual_raw | residual_log | basis_relaxed_unit_area_log | 0.0108 | 0.0108 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.001 | huber_residual_raw | residual_log | svc_group_n_log | -0.0100 | 0.0100 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.001 | huber_residual_raw | residual_log | basis_relaxed_iqr | -0.0091 | 0.0091 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.001 | huber_residual_raw | residual_log | ppv8_defensive | -0.0089 | 0.0089 | 0.0100 |
| hcoef8_shrunk_basis_gap_alpha0.001 | huber_residual_raw | residual_log | current_ppv8_gap | -0.0084 | 0.0084 | 0.0100 |
| hcoef8_risk_flags_alpha0.01 | huber_residual_raw | residual_log | svc_fallback | -0.5343 | 0.5343 | 0.0117 |
| hcoef8_risk_flags_alpha0.01 | huber_residual_raw | residual_log | shrunk_svc_prior | 0.2425 | 0.2425 | 0.0117 |
| hcoef8_risk_flags_alpha0.01 | huber_residual_raw | residual_log | current_shrunk_huber_gap | 0.1031 | 0.1031 | 0.0117 |
| hcoef8_risk_flags_alpha0.01 | huber_residual_raw | residual_log | basis_relaxed_unit_area_log | 0.0973 | 0.0973 | 0.0117 |
| hcoef8_risk_flags_alpha0.01 | huber_residual_raw | residual_log | ppv8_defensive | 0.0891 | 0.0891 | 0.0117 |
| hcoef8_risk_flags_alpha0.01 | huber_residual_raw | residual_log | shrunk_huber_refit | 0.0706 | 0.0706 | 0.0117 |

## 7. 잔차/큰 오차 요약

| split | candidate | n | median_residual_log | mean_residual_log | residual_std | over_2x_n | under_half_n | ape_gt_100pct_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_ex50 | hcoef2_size_reliability_cap005_s050 | 829 | 0.0608 | 0.3278 | 1.2668 | 26 | 152 | 26 |
| 0604_ex50 | hcoef8_risk_flags_alpha0.001_all_tiny_low_priority | 829 | 0.0742 | 0.3356 | 1.2684 | 30 | 154 | 30 |
| 0604_ex50 | hcoef8_risk_flags_alpha0.001_artist_low_only_strong | 829 | 0.0782 | 0.3357 | 1.2688 | 30 | 154 | 30 |
| 0604_ex50 | hcoef8_risk_flags_alpha0.001_low_medium_mid_light_high_none | 829 | 0.0732 | 0.3352 | 1.2686 | 30 | 154 | 30 |
| 0604_ex50 | hcoef8_risk_flags_alpha0.001_low_mid_balanced_high_none | 829 | 0.0646 | 0.3339 | 1.2685 | 30 | 154 | 30 |
| 0604_ex50 | hcoef8_risk_flags_alpha0.001_low_only_medium | 829 | 0.0782 | 0.3357 | 1.2686 | 30 | 154 | 30 |
| 0604_ex50 | hcoef8_risk_flags_alpha0.001_low_strong_mid_light_high_none | 829 | 0.0707 | 0.3341 | 1.2687 | 30 | 154 | 30 |
| 0604_ex50 | hcoef8_risk_flags_alpha0.01_all_tiny_low_priority | 829 | 0.0742 | 0.3356 | 1.2684 | 30 | 154 | 30 |
| 0604_ex50 | hcoef8_risk_flags_alpha0.01_artist_low_only_strong | 829 | 0.0782 | 0.3357 | 1.2688 | 30 | 154 | 30 |
| 0604_ex50 | hcoef8_risk_flags_alpha0.01_low_medium_mid_light_high_none | 829 | 0.0732 | 0.3352 | 1.2686 | 30 | 154 | 30 |
| 0604_ex50 | hcoef8_risk_flags_alpha0.01_low_mid_balanced_high_none | 829 | 0.0646 | 0.3339 | 1.2685 | 30 | 154 | 30 |
| 0604_ex50 | hcoef8_risk_flags_alpha0.01_low_only_medium | 829 | 0.0782 | 0.3357 | 1.2686 | 30 | 154 | 30 |
| 0604_ex50 | hcoef8_risk_flags_alpha0.01_low_strong_mid_light_high_none | 829 | 0.0707 | 0.3341 | 1.2687 | 30 | 154 | 30 |
| 0604_ex50 | hcoef8_shrunk_basis_gap_alpha0.001_all_tiny_low_priority | 829 | 0.0742 | 0.3360 | 1.2682 | 30 | 153 | 30 |
| 0604_ex50 | hcoef8_shrunk_basis_gap_alpha0.001_artist_low_only_strong | 829 | 0.0782 | 0.3364 | 1.2685 | 30 | 153 | 30 |
| 0604_ex50 | hcoef8_shrunk_basis_gap_alpha0.001_low_medium_mid_light_high_none | 829 | 0.0732 | 0.3358 | 1.2684 | 30 | 153 | 30 |
| 0604_ex50 | hcoef8_shrunk_basis_gap_alpha0.001_low_mid_balanced_high_none | 829 | 0.0639 | 0.3345 | 1.2683 | 30 | 153 | 30 |
| 0604_ex50 | hcoef8_shrunk_basis_gap_alpha0.001_low_only_medium | 829 | 0.0782 | 0.3361 | 1.2685 | 30 | 153 | 30 |
| 0604_ex50 | hcoef8_shrunk_basis_gap_alpha0.001_low_strong_mid_light_high_none | 829 | 0.0707 | 0.3349 | 1.2684 | 30 | 153 | 30 |
| 0604_ex50 | hcoef8_shrunk_basis_gap_alpha0.01_all_tiny_low_priority | 829 | 0.0742 | 0.3360 | 1.2682 | 30 | 153 | 30 |
| 0604_ex50 | hcoef8_shrunk_basis_gap_alpha0.01_artist_low_only_strong | 829 | 0.0782 | 0.3364 | 1.2685 | 30 | 153 | 30 |
| 0604_ex50 | hcoef8_shrunk_basis_gap_alpha0.01_low_medium_mid_light_high_none | 829 | 0.0732 | 0.3358 | 1.2684 | 30 | 153 | 30 |
| 0604_ex50 | hcoef8_shrunk_basis_gap_alpha0.01_low_mid_balanced_high_none | 829 | 0.0639 | 0.3345 | 1.2683 | 30 | 153 | 30 |
| 0604_ex50 | hcoef8_shrunk_basis_gap_alpha0.01_low_only_medium | 829 | 0.0782 | 0.3362 | 1.2685 | 30 | 153 | 30 |
| 0604_ex50 | hcoef8_shrunk_basis_gap_alpha0.01_low_strong_mid_light_high_none | 829 | 0.0707 | 0.3349 | 1.2684 | 30 | 153 | 30 |
| 0604_ex50 | hcoef8_unit_area_reliability_alpha0.001_all_tiny_low_priority | 829 | 0.0742 | 0.3359 | 1.2683 | 30 | 153 | 30 |
| 0604_ex50 | hcoef8_unit_area_reliability_alpha0.001_artist_low_only_strong | 829 | 0.0782 | 0.3362 | 1.2685 | 30 | 153 | 30 |
| 0604_ex50 | hcoef8_unit_area_reliability_alpha0.001_low_medium_mid_light_high_none | 829 | 0.0732 | 0.3356 | 1.2685 | 30 | 153 | 30 |
| 0604_ex50 | hcoef8_unit_area_reliability_alpha0.001_low_mid_balanced_high_none | 829 | 0.0646 | 0.3344 | 1.2684 | 30 | 153 | 30 |
| 0604_ex50 | hcoef8_unit_area_reliability_alpha0.001_low_only_medium | 829 | 0.0782 | 0.3360 | 1.2685 | 30 | 153 | 30 |
| 0604_ex50 | hcoef8_unit_area_reliability_alpha0.001_low_strong_mid_light_high_none | 829 | 0.0707 | 0.3347 | 1.2685 | 30 | 153 | 30 |
| 0604_ex50 | hcoef8_unit_area_reliability_alpha0.01_all_tiny_low_priority | 829 | 0.0742 | 0.3359 | 1.2683 | 30 | 153 | 30 |
| 0604_ex50 | hcoef8_unit_area_reliability_alpha0.01_artist_low_only_strong | 829 | 0.0782 | 0.3362 | 1.2685 | 30 | 153 | 30 |
| 0604_ex50 | hcoef8_unit_area_reliability_alpha0.01_low_medium_mid_light_high_none | 829 | 0.0732 | 0.3356 | 1.2685 | 30 | 153 | 30 |
| 0604_ex50 | hcoef8_unit_area_reliability_alpha0.01_low_mid_balanced_high_none | 829 | 0.0646 | 0.3344 | 1.2684 | 30 | 153 | 30 |
| 0604_ex50 | hcoef8_unit_area_reliability_alpha0.01_low_only_medium | 829 | 0.0782 | 0.3360 | 1.2685 | 30 | 153 | 30 |
| 0604_ex50 | hcoef8_unit_area_reliability_alpha0.01_low_strong_mid_light_high_none | 829 | 0.0707 | 0.3347 | 1.2685 | 30 | 153 | 30 |
| test | hcoef2_size_reliability_cap005_s050 | 607 | -0.0039 | -0.0148 | 0.3989 | 26 | 17 | 26 |
| test | hcoef8_risk_flags_alpha0.001_all_tiny_low_priority | 607 | -0.0025 | -0.0118 | 0.3996 | 24 | 17 | 24 |
| test | hcoef8_risk_flags_alpha0.001_artist_low_only_strong | 607 | -0.0006 | -0.0107 | 0.4000 | 24 | 18 | 24 |
| test | hcoef8_risk_flags_alpha0.001_low_medium_mid_light_high_none | 607 | -0.0027 | -0.0116 | 0.3997 | 24 | 17 | 24 |
| test | hcoef8_risk_flags_alpha0.001_low_mid_balanced_high_none | 607 | -0.0070 | -0.0123 | 0.3992 | 24 | 17 | 24 |
| test | hcoef8_risk_flags_alpha0.001_low_only_medium | 607 | -0.0001 | -0.0111 | 0.3999 | 24 | 17 | 24 |
| test | hcoef8_risk_flags_alpha0.001_low_strong_mid_light_high_none | 607 | -0.0045 | -0.0113 | 0.3996 | 24 | 18 | 24 |
| test | hcoef8_risk_flags_alpha0.01_all_tiny_low_priority | 607 | -0.0025 | -0.0118 | 0.3996 | 24 | 17 | 24 |
| test | hcoef8_risk_flags_alpha0.01_artist_low_only_strong | 607 | -0.0006 | -0.0107 | 0.4000 | 24 | 18 | 24 |
| test | hcoef8_risk_flags_alpha0.01_low_medium_mid_light_high_none | 607 | -0.0027 | -0.0116 | 0.3997 | 24 | 17 | 24 |
| test | hcoef8_risk_flags_alpha0.01_low_mid_balanced_high_none | 607 | -0.0070 | -0.0123 | 0.3992 | 24 | 17 | 24 |
| test | hcoef8_risk_flags_alpha0.01_low_only_medium | 607 | -0.0001 | -0.0111 | 0.3999 | 24 | 17 | 24 |
| test | hcoef8_risk_flags_alpha0.01_low_strong_mid_light_high_none | 607 | -0.0045 | -0.0113 | 0.3996 | 24 | 18 | 24 |

## 8. 다음 보정 방향

- segmented cap/strength가 p95 guard를 통과하면 반복 횟수를 늘려 재검증.
- 통과 후보가 없으면 면적단가 피처는 MAPE 목적 후보로만 유지하고, p95 방어는 별도 quantile/risk 모델과 결합.

## 9. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/residual_analysis.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `outputs/repeated_validation_metrics.csv`
- `outputs/segment_policy_summary.csv`
- `outputs/selected_candidates.csv`
- `artifacts/experiment_config.json`