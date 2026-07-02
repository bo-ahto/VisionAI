# PP-HCOEF7 Warm Huber 면적단가 기준가 직접 잔차 피처 실험

- 작성일: 2026-06-07 23:14
- 목적: HCOEF4에서 강한 계수로 확인된 면적단가 기준가와 기준가 신뢰도 피처를 HCOEF3 잔차 보정에 직접 추가.
- 기준 후보: `hcoef2_size_reliability_cap005_s050`.
- 방식: `current_70_30` 잔차를 Huber로 학습하고, 보정값은 cap/strength로 제한.
- 후보 선택: 반복 OOF 우선, fixed test는 최종 확인용.

## 1. 실행 결론

- 새 운영 기본 후보 채택 없음.
- 이 실험은 routing 조건을 사람이 직접 고정하는 대신 Huber 계수가 basis 신뢰도를 직접 조정하도록 한 점이 HCOEF6와 다름.

## 2. 후보 선택표

| candidate | row_all3_prob | artist_all3_prob | row_delta_MdAPE | row_delta_MAPE | row_delta_p95_APE | artist_delta_MdAPE | artist_delta_MAPE | artist_delta_p95_APE | test_delta_MdAPE | test_delta_MAPE | test_delta_p95_APE | ops0604_delta_MdAPE | ops0604_delta_MAPE | ops0604_delta_p95_APE | passes_repeat_gate | passes_fixed_guard | purpose |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.75 | 0.8333 | 0.5000 | -0.0032 | -0.0025 | -0.0017 | -0.0013 | -0.0023 | -0.0023 | 0.0054 | -0.0031 | 0.0311 | -0.0094 | -0.0086 | -0.0005 | False | False | repeat_mape_candidate |
| hcoef7_unit_area_reliability_alpha0.001_cap0.05_s0.75 | 0.8333 | 0.5000 | -0.0032 | -0.0025 | -0.0017 | -0.0013 | -0.0023 | -0.0023 | 0.0054 | -0.0031 | 0.0311 | -0.0094 | -0.0086 | -0.0005 | False | False | repeat_mape_candidate |
| hcoef7_risk_flags_alpha0.001_cap0.05_s0.50 | 0.6667 | 0.4167 | -0.0018 | -0.0014 | -0.0009 | -0.0025 | -0.0012 | 0.0007 | -0.0002 | -0.0011 | 0.0225 | -0.0063 | -0.0055 | 0.0031 | False | False | repeat_mape_candidate |
| hcoef7_risk_flags_alpha0.01_cap0.05_s0.50 | 0.6667 | 0.4167 | -0.0018 | -0.0014 | -0.0009 | -0.0025 | -0.0012 | 0.0007 | -0.0002 | -0.0011 | 0.0225 | -0.0063 | -0.0055 | 0.0031 | False | False | repeat_mape_candidate |
| hcoef7_shrunk_basis_gap_alpha0.001_cap0.05_s0.75 | 0.4167 | 0.5000 | -0.0017 | -0.0030 | -0.0002 | -0.0013 | -0.0026 | -0.0011 | 0.0039 | -0.0041 | 0.0263 | -0.0091 | -0.0091 | -0.0005 | False | False | repeat_mape_candidate |
| hcoef7_shrunk_basis_gap_alpha0.01_cap0.05_s0.75 | 0.4167 | 0.5000 | -0.0017 | -0.0030 | -0.0002 | -0.0013 | -0.0026 | -0.0011 | 0.0039 | -0.0041 | 0.0263 | -0.0091 | -0.0091 | -0.0005 | False | False | repeat_mape_candidate |
| hcoef7_risk_flags_alpha0.01_cap0.03_s0.75 | 0.2500 | 0.2500 | -0.0015 | -0.0010 | 0.0008 | -0.0020 | -0.0009 | 0.0013 | 0.0015 | -0.0008 | 0.0219 | -0.0058 | -0.0049 | 0.0031 | False | False | repeat_mape_candidate |
| hcoef7_risk_flags_alpha0.001_cap0.03_s0.75 | 0.2500 | 0.2500 | -0.0015 | -0.0010 | 0.0007 | -0.0020 | -0.0009 | 0.0013 | 0.0015 | -0.0008 | 0.0219 | -0.0058 | -0.0049 | 0.0031 | False | False | repeat_mape_candidate |
| hcoef7_risk_flags_alpha0.001_cap0.05_s0.75 | 0.3333 | 0.2500 | -0.0013 | -0.0023 | -0.0004 | -0.0020 | -0.0020 | -0.0001 | 0.0044 | -0.0019 | 0.0264 | -0.0099 | -0.0091 | -0.0005 | False | False | repeat_mape_candidate |
| hcoef7_risk_flags_alpha0.01_cap0.05_s0.75 | 0.3333 | 0.2500 | -0.0013 | -0.0023 | -0.0003 | -0.0020 | -0.0020 | -0.0001 | 0.0044 | -0.0019 | 0.0264 | -0.0098 | -0.0091 | -0.0005 | False | False | repeat_mape_candidate |
| hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.50 | 0.4167 | 0.5000 | -0.0007 | -0.0014 | -0.0013 | -0.0011 | -0.0014 | -0.0004 | -0.0001 | -0.0019 | 0.0195 | -0.0063 | -0.0052 | 0.0032 | False | False | repeat_mape_candidate |
| hcoef7_unit_area_reliability_alpha0.001_cap0.05_s0.50 | 0.4167 | 0.5000 | -0.0007 | -0.0014 | -0.0013 | -0.0011 | -0.0014 | -0.0004 | -0.0001 | -0.0019 | 0.0195 | -0.0063 | -0.0052 | 0.0032 | False | False | repeat_mape_candidate |
| hcoef7_unit_area_level_flags_alpha0.01_cap0.05_s0.75 | 0.3333 | 0.5000 | -0.0006 | -0.0022 | -0.0011 | 0.0001 | -0.0019 | -0.0022 | 0.0054 | -0.0031 | 0.0311 | -0.0091 | -0.0089 | -0.0005 | False | False | repeat_mape_candidate |
| hcoef7_unit_area_level_flags_alpha0.001_cap0.05_s0.75 | 0.4167 | 0.5000 | -0.0006 | -0.0022 | -0.0012 | 0.0001 | -0.0019 | -0.0022 | 0.0054 | -0.0031 | 0.0311 | -0.0091 | -0.0089 | -0.0005 | False | False | repeat_mape_candidate |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.75 | 0.4167 | 0.3333 | -0.0002 | -0.0009 | -0.0011 | 0.0000 | -0.0010 | 0.0005 | 0.0023 | -0.0017 | 0.0230 | -0.0031 | -0.0045 | 0.0032 | False | False | repeat_mape_candidate |
| hcoef7_unit_area_reliability_alpha0.001_cap0.03_s0.75 | 0.4167 | 0.3333 | -0.0002 | -0.0009 | -0.0012 | 0.0000 | -0.0010 | 0.0005 | 0.0023 | -0.0017 | 0.0229 | -0.0031 | -0.0045 | 0.0032 | False | False | repeat_mape_candidate |
| hcoef7_shrunk_basis_gap_alpha0.01_cap0.05_s0.50 | 0.1667 | 0.4167 | -0.0000 | -0.0017 | -0.0009 | -0.0010 | -0.0016 | -0.0005 | -0.0012 | -0.0026 | 0.0211 | -0.0063 | -0.0054 | 0.0028 | False | False | repeat_mape_candidate |
| hcoef2_size_reliability_cap005_s050 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | False | hold_or_reject |
| hcoef7_shrunk_basis_gap_alpha0.001_cap0.05_s0.50 | 0.1667 | 0.4167 | 0.0000 | -0.0017 | -0.0009 | -0.0010 | -0.0016 | -0.0005 | -0.0012 | -0.0026 | 0.0211 | -0.0063 | -0.0054 | 0.0028 | False | False | repeat_mape_candidate |
| hcoef7_unit_area_level_flags_alpha0.01_cap0.05_s0.50 | 0.2500 | 0.4167 | 0.0001 | -0.0012 | -0.0010 | -0.0005 | -0.0011 | -0.0002 | 0.0003 | -0.0019 | 0.0134 | -0.0063 | -0.0054 | 0.0032 | False | False | repeat_mape_candidate |
| hcoef7_unit_area_level_flags_alpha0.001_cap0.05_s0.50 | 0.2500 | 0.4167 | 0.0001 | -0.0012 | -0.0010 | -0.0005 | -0.0011 | -0.0002 | 0.0003 | -0.0019 | 0.0134 | -0.0063 | -0.0054 | 0.0032 | False | False | repeat_mape_candidate |
| hcoef7_shrunk_basis_gap_alpha0.001_cap0.03_s0.75 | 0.2500 | 0.3333 | 0.0005 | -0.0014 | -0.0007 | -0.0001 | -0.0012 | 0.0003 | -0.0007 | -0.0024 | 0.0216 | -0.0031 | -0.0049 | 0.0028 | False | False | repeat_mape_candidate |
| hcoef7_shrunk_basis_gap_alpha0.01_cap0.03_s0.75 | 0.2500 | 0.3333 | 0.0005 | -0.0014 | -0.0007 | -0.0001 | -0.0012 | 0.0003 | -0.0007 | -0.0024 | 0.0216 | -0.0031 | -0.0049 | 0.0028 | False | False | repeat_mape_candidate |
| hcoef7_unit_area_level_flags_alpha0.001_cap0.03_s0.75 | 0.0000 | 0.0833 | 0.0011 | -0.0007 | -0.0004 | 0.0008 | -0.0007 | -0.0001 | 0.0023 | -0.0018 | 0.0139 | -0.0031 | -0.0047 | 0.0032 | False | False | repeat_mape_candidate |

## 3. 반복 OOF 요약

| validation_scheme | candidate | mean_delta_MdAPE_vs_hcoef2 | mean_delta_MAPE_vs_hcoef2 | mean_delta_p95_APE_vs_hcoef2 | std_delta_MdAPE_vs_hcoef2 | MdAPE_improve_prob_vs_hcoef2 | MAPE_improve_prob_vs_hcoef2 | p95_improve_prob_vs_hcoef2 | all3_improve_prob_vs_hcoef2 | mean_improve_count_vs_hcoef2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| row_oof | hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.75 | -0.0032 | -0.0025 | -0.0017 | 0.0013 | 1.0000 | 1.0000 | 0.8333 | 0.8333 | 2.8333 |
| row_oof | hcoef7_unit_area_reliability_alpha0.001_cap0.05_s0.75 | -0.0032 | -0.0025 | -0.0017 | 0.0013 | 1.0000 | 1.0000 | 0.8333 | 0.8333 | 2.8333 |
| row_oof | hcoef7_risk_flags_alpha0.001_cap0.05_s0.50 | -0.0018 | -0.0014 | -0.0009 | 0.0013 | 0.9167 | 1.0000 | 0.7500 | 0.6667 | 2.6667 |
| row_oof | hcoef7_risk_flags_alpha0.01_cap0.05_s0.50 | -0.0018 | -0.0014 | -0.0009 | 0.0013 | 0.9167 | 1.0000 | 0.7500 | 0.6667 | 2.6667 |
| artist_oof | hcoef7_shrunk_basis_gap_alpha0.01_cap0.05_s0.75 | -0.0013 | -0.0026 | -0.0011 | 0.0018 | 0.7500 | 1.0000 | 0.5833 | 0.5000 | 2.3333 |
| artist_oof | hcoef7_shrunk_basis_gap_alpha0.001_cap0.05_s0.75 | -0.0013 | -0.0026 | -0.0011 | 0.0017 | 0.7500 | 1.0000 | 0.5833 | 0.5000 | 2.3333 |
| artist_oof | hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.75 | -0.0013 | -0.0023 | -0.0023 | 0.0019 | 0.8333 | 1.0000 | 0.5833 | 0.5000 | 2.4167 |
| artist_oof | hcoef7_unit_area_reliability_alpha0.001_cap0.05_s0.75 | -0.0013 | -0.0023 | -0.0023 | 0.0019 | 0.8333 | 1.0000 | 0.5833 | 0.5000 | 2.4167 |
| artist_oof | hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.50 | -0.0011 | -0.0014 | -0.0004 | 0.0013 | 0.7500 | 1.0000 | 0.5833 | 0.5000 | 2.3333 |
| artist_oof | hcoef7_unit_area_reliability_alpha0.001_cap0.05_s0.50 | -0.0011 | -0.0014 | -0.0004 | 0.0013 | 0.7500 | 1.0000 | 0.5833 | 0.5000 | 2.3333 |
| artist_oof | hcoef7_unit_area_level_flags_alpha0.001_cap0.05_s0.75 | 0.0001 | -0.0019 | -0.0022 | 0.0018 | 0.5833 | 1.0000 | 0.6667 | 0.5000 | 2.2500 |
| artist_oof | hcoef7_unit_area_level_flags_alpha0.01_cap0.05_s0.75 | 0.0001 | -0.0019 | -0.0022 | 0.0018 | 0.5833 | 1.0000 | 0.6667 | 0.5000 | 2.2500 |
| artist_oof | hcoef7_risk_flags_alpha0.01_cap0.05_s0.50 | -0.0025 | -0.0012 | 0.0007 | 0.0014 | 0.9167 | 1.0000 | 0.5000 | 0.4167 | 2.4167 |
| artist_oof | hcoef7_risk_flags_alpha0.001_cap0.05_s0.50 | -0.0025 | -0.0012 | 0.0007 | 0.0014 | 0.9167 | 1.0000 | 0.5000 | 0.4167 | 2.4167 |
| row_oof | hcoef7_shrunk_basis_gap_alpha0.001_cap0.05_s0.75 | -0.0017 | -0.0030 | -0.0002 | 0.0013 | 0.8333 | 1.0000 | 0.5000 | 0.4167 | 2.3333 |
| row_oof | hcoef7_shrunk_basis_gap_alpha0.01_cap0.05_s0.75 | -0.0017 | -0.0030 | -0.0002 | 0.0013 | 0.8333 | 1.0000 | 0.5000 | 0.4167 | 2.3333 |
| artist_oof | hcoef7_shrunk_basis_gap_alpha0.01_cap0.05_s0.50 | -0.0010 | -0.0016 | -0.0005 | 0.0017 | 0.5833 | 1.0000 | 0.5833 | 0.4167 | 2.1667 |
| artist_oof | hcoef7_shrunk_basis_gap_alpha0.001_cap0.05_s0.50 | -0.0010 | -0.0016 | -0.0005 | 0.0017 | 0.5833 | 1.0000 | 0.5833 | 0.4167 | 2.1667 |
| row_oof | hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.50 | -0.0007 | -0.0014 | -0.0013 | 0.0014 | 0.5833 | 1.0000 | 0.7500 | 0.4167 | 2.3333 |
| row_oof | hcoef7_unit_area_reliability_alpha0.001_cap0.05_s0.50 | -0.0007 | -0.0014 | -0.0013 | 0.0014 | 0.5833 | 1.0000 | 0.7500 | 0.4167 | 2.3333 |
| row_oof | hcoef7_unit_area_level_flags_alpha0.001_cap0.05_s0.75 | -0.0006 | -0.0022 | -0.0012 | 0.0024 | 0.6667 | 1.0000 | 0.5833 | 0.4167 | 2.2500 |
| artist_oof | hcoef7_unit_area_level_flags_alpha0.001_cap0.05_s0.50 | -0.0005 | -0.0011 | -0.0002 | 0.0021 | 0.6667 | 1.0000 | 0.6667 | 0.4167 | 2.3333 |
| artist_oof | hcoef7_unit_area_level_flags_alpha0.01_cap0.05_s0.50 | -0.0005 | -0.0011 | -0.0002 | 0.0021 | 0.6667 | 1.0000 | 0.6667 | 0.4167 | 2.3333 |
| row_oof | hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.75 | -0.0002 | -0.0009 | -0.0011 | 0.0015 | 0.5000 | 1.0000 | 0.6667 | 0.4167 | 2.1667 |
| row_oof | hcoef7_unit_area_reliability_alpha0.001_cap0.03_s0.75 | -0.0002 | -0.0009 | -0.0012 | 0.0015 | 0.5000 | 1.0000 | 0.6667 | 0.4167 | 2.1667 |
| row_oof | hcoef7_risk_flags_alpha0.001_cap0.05_s0.75 | -0.0013 | -0.0023 | -0.0004 | 0.0020 | 0.6667 | 1.0000 | 0.5000 | 0.3333 | 2.1667 |
| row_oof | hcoef7_risk_flags_alpha0.01_cap0.05_s0.75 | -0.0013 | -0.0023 | -0.0003 | 0.0020 | 0.6667 | 1.0000 | 0.5000 | 0.3333 | 2.1667 |
| row_oof | hcoef7_unit_area_level_flags_alpha0.01_cap0.05_s0.75 | -0.0006 | -0.0022 | -0.0011 | 0.0024 | 0.6667 | 1.0000 | 0.5000 | 0.3333 | 2.1667 |
| artist_oof | hcoef7_shrunk_basis_gap_alpha0.01_cap0.03_s0.75 | -0.0001 | -0.0012 | 0.0003 | 0.0016 | 0.5000 | 1.0000 | 0.4167 | 0.3333 | 1.9167 |
| artist_oof | hcoef7_shrunk_basis_gap_alpha0.001_cap0.03_s0.75 | -0.0001 | -0.0012 | 0.0003 | 0.0016 | 0.5000 | 1.0000 | 0.4167 | 0.3333 | 1.9167 |
| artist_oof | hcoef7_unit_area_reliability_alpha0.001_cap0.03_s0.75 | 0.0000 | -0.0010 | 0.0005 | 0.0017 | 0.5833 | 1.0000 | 0.4167 | 0.3333 | 2.0000 |
| artist_oof | hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.75 | 0.0000 | -0.0010 | 0.0005 | 0.0017 | 0.5833 | 1.0000 | 0.4167 | 0.3333 | 2.0000 |

## 4. Fixed test 상위 후보

| candidate | method | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_hcoef2 | delta_MAPE_vs_hcoef2 | delta_p95_APE_vs_hcoef2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef7_shrunk_basis_gap_alpha0.001_cap0.03_s0.50 | unit_area_basis_residual_huber | 0.1361 | 0.2718 | 0.8298 | 0.3975 | -0.0027 | -0.0011 | 0.0235 |
| hcoef7_shrunk_basis_gap_alpha0.01_cap0.03_s0.50 | unit_area_basis_residual_huber | 0.1361 | 0.2719 | 0.8298 | 0.3975 | -0.0027 | -0.0011 | 0.0235 |
| hcoef7_risk_flags_alpha0.001_cap0.03_s0.25 | unit_area_basis_residual_huber | 0.1374 | 0.2738 | 0.8293 | 0.3987 | -0.0014 | 0.0008 | 0.0229 |
| hcoef7_risk_flags_alpha0.01_cap0.03_s0.25 | unit_area_basis_residual_huber | 0.1374 | 0.2738 | 0.8293 | 0.3987 | -0.0014 | 0.0008 | 0.0229 |
| hcoef7_shrunk_basis_gap_alpha0.001_cap0.05_s0.50 | unit_area_basis_residual_huber | 0.1376 | 0.2704 | 0.8274 | 0.3965 | -0.0012 | -0.0026 | 0.0211 |
| hcoef7_shrunk_basis_gap_alpha0.01_cap0.05_s0.50 | unit_area_basis_residual_huber | 0.1376 | 0.2704 | 0.8274 | 0.3965 | -0.0012 | -0.0026 | 0.0211 |
| hcoef7_shrunk_basis_gap_alpha0.01_cap0.03_s0.25 | unit_area_basis_residual_huber | 0.1378 | 0.2732 | 0.8268 | 0.3985 | -0.0010 | 0.0002 | 0.0204 |
| hcoef7_shrunk_basis_gap_alpha0.001_cap0.03_s0.25 | unit_area_basis_residual_huber | 0.1378 | 0.2732 | 0.8268 | 0.3985 | -0.0010 | 0.0002 | 0.0204 |
| hcoef7_shrunk_basis_gap_alpha0.001_cap0.03_s0.75 | unit_area_basis_residual_huber | 0.1381 | 0.2706 | 0.8280 | 0.3966 | -0.0007 | -0.0024 | 0.0216 |
| hcoef7_shrunk_basis_gap_alpha0.01_cap0.03_s0.75 | unit_area_basis_residual_huber | 0.1381 | 0.2706 | 0.8280 | 0.3966 | -0.0007 | -0.0024 | 0.0216 |
| hcoef7_shrunk_basis_gap_alpha0.01_cap0.05_s0.25 | unit_area_basis_residual_huber | 0.1382 | 0.2725 | 0.8241 | 0.3979 | -0.0006 | -0.0005 | 0.0177 |
| hcoef7_shrunk_basis_gap_alpha0.001_cap0.05_s0.25 | unit_area_basis_residual_huber | 0.1382 | 0.2724 | 0.8241 | 0.3979 | -0.0006 | -0.0005 | 0.0177 |
| hcoef7_unit_area_reliability_alpha0.001_cap0.03_s0.25 | unit_area_basis_residual_huber | 0.1382 | 0.2735 | 0.8255 | 0.3987 | -0.0006 | 0.0005 | 0.0191 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.25 | unit_area_basis_residual_huber | 0.1382 | 0.2735 | 0.8255 | 0.3987 | -0.0006 | 0.0005 | 0.0191 |
| hcoef7_risk_flags_alpha0.001_cap0.05_s0.25 | unit_area_basis_residual_huber | 0.1385 | 0.2732 | 0.8283 | 0.3981 | -0.0003 | 0.0002 | 0.0219 |
| hcoef7_risk_flags_alpha0.01_cap0.05_s0.25 | unit_area_basis_residual_huber | 0.1385 | 0.2732 | 0.8283 | 0.3982 | -0.0003 | 0.0002 | 0.0219 |
| hcoef7_risk_flags_alpha0.001_cap0.05_s0.50 | unit_area_basis_residual_huber | 0.1386 | 0.2719 | 0.8288 | 0.3970 | -0.0002 | -0.0011 | 0.0225 |
| hcoef7_risk_flags_alpha0.01_cap0.05_s0.50 | unit_area_basis_residual_huber | 0.1386 | 0.2719 | 0.8288 | 0.3970 | -0.0002 | -0.0011 | 0.0225 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.50 | unit_area_basis_residual_huber | 0.1387 | 0.2711 | 0.8258 | 0.3969 | -0.0001 | -0.0019 | 0.0195 |
| hcoef7_unit_area_reliability_alpha0.001_cap0.05_s0.50 | unit_area_basis_residual_huber | 0.1387 | 0.2711 | 0.8258 | 0.3969 | -0.0001 | -0.0019 | 0.0195 |
| hcoef2_size_reliability_cap005_s050 | hcoef2_stable | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 |
| hcoef7_unit_area_level_flags_alpha0.001_cap0.03_s0.25 | unit_area_basis_residual_huber | 0.1388 | 0.2734 | 0.8242 | 0.3987 | 0.0000 | 0.0004 | 0.0179 |
| hcoef7_unit_area_level_flags_alpha0.01_cap0.03_s0.25 | unit_area_basis_residual_huber | 0.1388 | 0.2734 | 0.8242 | 0.3987 | 0.0000 | 0.0004 | 0.0179 |
| hcoef7_unit_area_level_flags_alpha0.01_cap0.05_s0.25 | unit_area_basis_residual_huber | 0.1390 | 0.2728 | 0.8188 | 0.3982 | 0.0002 | -0.0002 | 0.0124 |

## 5. 주요 계수

- 계수는 표준화된 피처 기준이다.
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
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.25 | huber_residual | residual_log | svc_fallback | -0.2914 | 0.2914 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.25 | huber_residual | residual_log | shrunk_svc_prior | 0.2391 | 0.2391 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.25 | huber_residual | residual_log | basis_unit_gap | 0.0866 | 0.0866 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.25 | huber_residual | residual_log | current_shrunk_huber_gap | 0.0751 | 0.0751 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.25 | huber_residual | residual_log | basis_shrunk_weight | -0.0523 | 0.0523 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.25 | huber_residual | residual_log | basis_relaxed_n_log | 0.0443 | 0.0443 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.25 | huber_residual | residual_log | log_area | 0.0366 | 0.0366 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.25 | huber_residual | residual_log | raw_shrunk_prior_gap | -0.0356 | 0.0356 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.25 | huber_residual | residual_log | basis_relaxed_unit_area_log | 0.0243 | 0.0243 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.25 | huber_residual | residual_log | shrunk_huber_refit | -0.0133 | 0.0133 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.25 | huber_residual | residual_log | svc_prior_iqr | 0.0103 | 0.0103 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.25 | huber_residual | residual_log | svc_group_n_log | -0.0100 | 0.0100 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.25 | huber_residual | residual_log | basis_relaxed_iqr | -0.0087 | 0.0087 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.25 | huber_residual | residual_log | current_ppv8_gap | -0.0075 | 0.0075 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.25 | huber_residual | residual_log | ppv8_defensive | 0.0058 | 0.0058 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.50 | huber_residual | residual_log | svc_fallback | -0.2914 | 0.2914 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.50 | huber_residual | residual_log | shrunk_svc_prior | 0.2391 | 0.2391 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.50 | huber_residual | residual_log | basis_unit_gap | 0.0866 | 0.0866 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.50 | huber_residual | residual_log | current_shrunk_huber_gap | 0.0751 | 0.0751 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.50 | huber_residual | residual_log | basis_shrunk_weight | -0.0523 | 0.0523 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.50 | huber_residual | residual_log | basis_relaxed_n_log | 0.0443 | 0.0443 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.50 | huber_residual | residual_log | log_area | 0.0366 | 0.0366 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.50 | huber_residual | residual_log | raw_shrunk_prior_gap | -0.0356 | 0.0356 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.50 | huber_residual | residual_log | basis_relaxed_unit_area_log | 0.0243 | 0.0243 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.50 | huber_residual | residual_log | shrunk_huber_refit | -0.0133 | 0.0133 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.50 | huber_residual | residual_log | svc_prior_iqr | 0.0103 | 0.0103 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.50 | huber_residual | residual_log | svc_group_n_log | -0.0100 | 0.0100 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.50 | huber_residual | residual_log | basis_relaxed_iqr | -0.0087 | 0.0087 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.50 | huber_residual | residual_log | current_ppv8_gap | -0.0075 | 0.0075 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.50 | huber_residual | residual_log | ppv8_defensive | 0.0058 | 0.0058 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.75 | huber_residual | residual_log | svc_fallback | -0.2914 | 0.2914 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.75 | huber_residual | residual_log | shrunk_svc_prior | 0.2391 | 0.2391 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.75 | huber_residual | residual_log | basis_unit_gap | 0.0866 | 0.0866 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.75 | huber_residual | residual_log | current_shrunk_huber_gap | 0.0751 | 0.0751 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.75 | huber_residual | residual_log | basis_shrunk_weight | -0.0523 | 0.0523 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.75 | huber_residual | residual_log | basis_relaxed_n_log | 0.0443 | 0.0443 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.75 | huber_residual | residual_log | log_area | 0.0366 | 0.0366 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.75 | huber_residual | residual_log | raw_shrunk_prior_gap | -0.0356 | 0.0356 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.75 | huber_residual | residual_log | basis_relaxed_unit_area_log | 0.0243 | 0.0243 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.75 | huber_residual | residual_log | shrunk_huber_refit | -0.0133 | 0.0133 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.75 | huber_residual | residual_log | svc_prior_iqr | 0.0103 | 0.0103 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.75 | huber_residual | residual_log | svc_group_n_log | -0.0100 | 0.0100 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.75 | huber_residual | residual_log | basis_relaxed_iqr | -0.0087 | 0.0087 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.75 | huber_residual | residual_log | current_ppv8_gap | -0.0075 | 0.0075 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.75 | huber_residual | residual_log | ppv8_defensive | 0.0058 | 0.0058 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.25 | huber_residual | residual_log | svc_fallback | -0.2914 | 0.2914 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.25 | huber_residual | residual_log | shrunk_svc_prior | 0.2391 | 0.2391 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.25 | huber_residual | residual_log | basis_unit_gap | 0.0866 | 0.0866 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.25 | huber_residual | residual_log | current_shrunk_huber_gap | 0.0751 | 0.0751 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.25 | huber_residual | residual_log | basis_shrunk_weight | -0.0523 | 0.0523 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.25 | huber_residual | residual_log | basis_relaxed_n_log | 0.0443 | 0.0443 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.25 | huber_residual | residual_log | log_area | 0.0366 | 0.0366 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.25 | huber_residual | residual_log | raw_shrunk_prior_gap | -0.0356 | 0.0356 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.25 | huber_residual | residual_log | basis_relaxed_unit_area_log | 0.0243 | 0.0243 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.25 | huber_residual | residual_log | shrunk_huber_refit | -0.0133 | 0.0133 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.25 | huber_residual | residual_log | svc_prior_iqr | 0.0103 | 0.0103 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.25 | huber_residual | residual_log | svc_group_n_log | -0.0100 | 0.0100 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.25 | huber_residual | residual_log | basis_relaxed_iqr | -0.0087 | 0.0087 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.25 | huber_residual | residual_log | current_ppv8_gap | -0.0075 | 0.0075 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.25 | huber_residual | residual_log | ppv8_defensive | 0.0058 | 0.0058 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.50 | huber_residual | residual_log | svc_fallback | -0.2914 | 0.2914 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.50 | huber_residual | residual_log | shrunk_svc_prior | 0.2391 | 0.2391 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.50 | huber_residual | residual_log | basis_unit_gap | 0.0866 | 0.0866 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.50 | huber_residual | residual_log | current_shrunk_huber_gap | 0.0751 | 0.0751 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.50 | huber_residual | residual_log | basis_shrunk_weight | -0.0523 | 0.0523 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.50 | huber_residual | residual_log | basis_relaxed_n_log | 0.0443 | 0.0443 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.50 | huber_residual | residual_log | log_area | 0.0366 | 0.0366 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.50 | huber_residual | residual_log | raw_shrunk_prior_gap | -0.0356 | 0.0356 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.50 | huber_residual | residual_log | basis_relaxed_unit_area_log | 0.0243 | 0.0243 | 0.0103 |
| hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.50 | huber_residual | residual_log | shrunk_huber_refit | -0.0133 | 0.0133 | 0.0103 |

## 6. 잔차/큰 오차 요약

| split | candidate | n | median_residual_log | mean_residual_log | residual_std | over_2x_n | under_half_n | ape_gt_100pct_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_ex50 | hcoef2_size_reliability_cap005_s050 | 829 | 0.0608 | 0.3278 | 1.2668 | 26 | 152 | 26 |
| 0604_ex50 | hcoef7_risk_flags_alpha0.001_cap0.03_s0.25 | 829 | 0.0707 | 0.3350 | 1.2670 | 30 | 154 | 30 |
| 0604_ex50 | hcoef7_risk_flags_alpha0.001_cap0.03_s0.50 | 829 | 0.0688 | 0.3329 | 1.2655 | 28 | 154 | 28 |
| 0604_ex50 | hcoef7_risk_flags_alpha0.001_cap0.03_s0.75 | 829 | 0.0633 | 0.3308 | 1.2640 | 28 | 152 | 28 |
| 0604_ex50 | hcoef7_risk_flags_alpha0.001_cap0.05_s0.25 | 829 | 0.0683 | 0.3336 | 1.2660 | 28 | 154 | 28 |
| 0604_ex50 | hcoef7_risk_flags_alpha0.001_cap0.05_s0.50 | 829 | 0.0608 | 0.3301 | 1.2635 | 27 | 152 | 27 |
| 0604_ex50 | hcoef7_risk_flags_alpha0.001_cap0.05_s0.75 | 829 | 0.0530 | 0.3267 | 1.2612 | 27 | 150 | 27 |
| 0604_ex50 | hcoef7_risk_flags_alpha0.01_cap0.03_s0.25 | 829 | 0.0707 | 0.3350 | 1.2670 | 30 | 154 | 30 |
| 0604_ex50 | hcoef7_risk_flags_alpha0.01_cap0.03_s0.50 | 829 | 0.0688 | 0.3329 | 1.2655 | 28 | 154 | 28 |
| 0604_ex50 | hcoef7_risk_flags_alpha0.01_cap0.03_s0.75 | 829 | 0.0633 | 0.3308 | 1.2640 | 28 | 152 | 28 |
| 0604_ex50 | hcoef7_risk_flags_alpha0.01_cap0.05_s0.25 | 829 | 0.0683 | 0.3336 | 1.2660 | 28 | 154 | 28 |
| 0604_ex50 | hcoef7_risk_flags_alpha0.01_cap0.05_s0.50 | 829 | 0.0608 | 0.3301 | 1.2635 | 27 | 152 | 27 |
| 0604_ex50 | hcoef7_risk_flags_alpha0.01_cap0.05_s0.75 | 829 | 0.0530 | 0.3267 | 1.2612 | 27 | 150 | 27 |
| 0604_ex50 | hcoef7_shrunk_basis_gap_alpha0.001_cap0.03_s0.25 | 829 | 0.0708 | 0.3351 | 1.2667 | 30 | 153 | 30 |
| 0604_ex50 | hcoef7_shrunk_basis_gap_alpha0.001_cap0.03_s0.50 | 829 | 0.0704 | 0.3331 | 1.2651 | 28 | 153 | 28 |
| 0604_ex50 | hcoef7_shrunk_basis_gap_alpha0.001_cap0.03_s0.75 | 829 | 0.0633 | 0.3311 | 1.2634 | 28 | 150 | 28 |
| 0604_ex50 | hcoef7_shrunk_basis_gap_alpha0.001_cap0.05_s0.25 | 829 | 0.0733 | 0.3337 | 1.2657 | 28 | 153 | 28 |
| 0604_ex50 | hcoef7_shrunk_basis_gap_alpha0.001_cap0.05_s0.50 | 829 | 0.0608 | 0.3303 | 1.2629 | 27 | 150 | 27 |
| 0604_ex50 | hcoef7_shrunk_basis_gap_alpha0.001_cap0.05_s0.75 | 829 | 0.0608 | 0.3269 | 1.2603 | 27 | 148 | 27 |
| 0604_ex50 | hcoef7_shrunk_basis_gap_alpha0.01_cap0.03_s0.25 | 829 | 0.0708 | 0.3351 | 1.2667 | 30 | 153 | 30 |
| 0604_ex50 | hcoef7_shrunk_basis_gap_alpha0.01_cap0.03_s0.50 | 829 | 0.0704 | 0.3331 | 1.2651 | 28 | 153 | 28 |
| 0604_ex50 | hcoef7_shrunk_basis_gap_alpha0.01_cap0.03_s0.75 | 829 | 0.0633 | 0.3311 | 1.2634 | 28 | 150 | 28 |
| 0604_ex50 | hcoef7_shrunk_basis_gap_alpha0.01_cap0.05_s0.25 | 829 | 0.0733 | 0.3337 | 1.2657 | 28 | 153 | 28 |
| 0604_ex50 | hcoef7_shrunk_basis_gap_alpha0.01_cap0.05_s0.50 | 829 | 0.0608 | 0.3303 | 1.2629 | 27 | 150 | 27 |
| 0604_ex50 | hcoef7_shrunk_basis_gap_alpha0.01_cap0.05_s0.75 | 829 | 0.0608 | 0.3269 | 1.2603 | 27 | 148 | 27 |
| 0604_ex50 | hcoef7_unit_area_level_flags_alpha0.001_cap0.03_s0.25 | 829 | 0.0708 | 0.3351 | 1.2669 | 30 | 153 | 30 |
| 0604_ex50 | hcoef7_unit_area_level_flags_alpha0.001_cap0.03_s0.50 | 829 | 0.0708 | 0.3331 | 1.2654 | 28 | 153 | 28 |
| 0604_ex50 | hcoef7_unit_area_level_flags_alpha0.001_cap0.03_s0.75 | 829 | 0.0633 | 0.3311 | 1.2640 | 28 | 149 | 28 |
| 0604_ex50 | hcoef7_unit_area_level_flags_alpha0.001_cap0.05_s0.25 | 829 | 0.0733 | 0.3337 | 1.2659 | 28 | 153 | 28 |
| 0604_ex50 | hcoef7_unit_area_level_flags_alpha0.001_cap0.05_s0.50 | 829 | 0.0610 | 0.3303 | 1.2635 | 27 | 149 | 27 |
| 0604_ex50 | hcoef7_unit_area_level_flags_alpha0.001_cap0.05_s0.75 | 829 | 0.0594 | 0.3269 | 1.2612 | 27 | 147 | 27 |
| 0604_ex50 | hcoef7_unit_area_level_flags_alpha0.01_cap0.03_s0.25 | 829 | 0.0708 | 0.3351 | 1.2669 | 30 | 153 | 30 |
| 0604_ex50 | hcoef7_unit_area_level_flags_alpha0.01_cap0.03_s0.50 | 829 | 0.0708 | 0.3331 | 1.2654 | 28 | 153 | 28 |
| 0604_ex50 | hcoef7_unit_area_level_flags_alpha0.01_cap0.03_s0.75 | 829 | 0.0633 | 0.3311 | 1.2640 | 28 | 149 | 28 |
| 0604_ex50 | hcoef7_unit_area_level_flags_alpha0.01_cap0.05_s0.25 | 829 | 0.0733 | 0.3337 | 1.2659 | 28 | 153 | 28 |
| 0604_ex50 | hcoef7_unit_area_level_flags_alpha0.01_cap0.05_s0.50 | 829 | 0.0610 | 0.3303 | 1.2635 | 27 | 149 | 27 |
| 0604_ex50 | hcoef7_unit_area_level_flags_alpha0.01_cap0.05_s0.75 | 829 | 0.0595 | 0.3269 | 1.2612 | 27 | 147 | 27 |
| 0604_ex50 | hcoef7_unit_area_reliability_alpha0.001_cap0.03_s0.25 | 829 | 0.0708 | 0.3350 | 1.2670 | 30 | 153 | 30 |
| 0604_ex50 | hcoef7_unit_area_reliability_alpha0.001_cap0.03_s0.50 | 829 | 0.0708 | 0.3329 | 1.2655 | 28 | 153 | 28 |
| 0604_ex50 | hcoef7_unit_area_reliability_alpha0.001_cap0.03_s0.75 | 829 | 0.0649 | 0.3308 | 1.2641 | 28 | 149 | 28 |
| 0604_ex50 | hcoef7_unit_area_reliability_alpha0.001_cap0.05_s0.25 | 829 | 0.0733 | 0.3336 | 1.2660 | 28 | 153 | 28 |
| 0604_ex50 | hcoef7_unit_area_reliability_alpha0.001_cap0.05_s0.50 | 829 | 0.0629 | 0.3301 | 1.2636 | 27 | 149 | 27 |
| 0604_ex50 | hcoef7_unit_area_reliability_alpha0.001_cap0.05_s0.75 | 829 | 0.0639 | 0.3266 | 1.2613 | 27 | 147 | 27 |
| 0604_ex50 | hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.25 | 829 | 0.0708 | 0.3350 | 1.2670 | 30 | 153 | 30 |
| 0604_ex50 | hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.50 | 829 | 0.0708 | 0.3329 | 1.2655 | 28 | 153 | 28 |
| 0604_ex50 | hcoef7_unit_area_reliability_alpha0.01_cap0.03_s0.75 | 829 | 0.0649 | 0.3308 | 1.2641 | 28 | 149 | 28 |
| 0604_ex50 | hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.25 | 829 | 0.0733 | 0.3336 | 1.2660 | 28 | 153 | 28 |
| 0604_ex50 | hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.50 | 829 | 0.0629 | 0.3301 | 1.2636 | 27 | 149 | 27 |
| 0604_ex50 | hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.75 | 829 | 0.0639 | 0.3266 | 1.2613 | 27 | 147 | 27 |
| test | hcoef2_size_reliability_cap005_s050 | 607 | -0.0039 | -0.0148 | 0.3989 | 26 | 17 | 26 |

## 7. 다음 보정 방향

- 반복 OOF와 fixed guard를 동시에 통과한 후보가 있으면 HCOEF8에서 반복 횟수를 늘려 재검증.
- 통과 후보가 없으면 segmented Huber 계수 또는 작가 메타 residual 피처와 결합하는 방향으로 이동.

## 8. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/residual_analysis.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `outputs/repeated_validation_metrics.csv`
- `outputs/selected_candidates.csv`
- `artifacts/experiment_config.json`