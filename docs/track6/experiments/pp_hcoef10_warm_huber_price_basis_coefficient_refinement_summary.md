# PP-HCOEF10 Warm Huber 원인 구간 기반 약한 보정 실험

- 작성일: 2026-06-07 23:55
- 목적: HCOEF3 안정 후보의 남은 큰 오차가 특정 가격대, 기준가 신뢰도, 크기, 재료/지지체 구간에서 반복되는지 확인하고 해당 구간에만 작은 잔차 보정을 적용.
- 기준 후보: `hcoef2_size_reliability_cap005_s050`.
- 방식: validation 내부 train fold에서 segment별 residual_log 중앙값을 만들고, cap/strength로 제한해 holdout fold에 적용.
- 반복 설정: row OOF 20회, artist OOF 20회, 각 5 folds.
- 후보 선택: 반복 OOF 우선, fixed test/0604는 확인용.

## 1. 실행 결론

- 새 운영 기본 후보 채택 없음.
- p95_APE와 반복 안정성을 동시에 통과하지 못하면 기본 후보로 채택하지 않는다.

## 2. 후보 선택표

| candidate | row_all3_prob | artist_all3_prob | row_delta_MdAPE | row_delta_MAPE | row_delta_p95_APE | artist_delta_MdAPE | artist_delta_MAPE | artist_delta_p95_APE | test_delta_MdAPE | test_delta_MAPE | test_delta_p95_APE | ops0604_delta_MdAPE | ops0604_delta_MAPE | ops0604_delta_p95_APE | passes_repeat_gate | passes_fixed_guard | purpose |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef10_pred_reliability_cap0.02_s0.25 | 0.0000 | 0.1000 | 0.0001 | 0.0002 | 0.0035 | 0.0005 | 0.0002 | 0.0020 | -0.0005 | -0.0001 | -0.0002 | -0.0033 | -0.0001 | 0.0000 | False | True | hold_or_reject |
| hcoef10_pred_reliability_cap0.03_s0.25 | 0.0000 | 0.0000 | 0.0001 | 0.0003 | 0.0042 | 0.0004 | 0.0003 | 0.0033 | -0.0005 | -0.0001 | -0.0002 | -0.0051 | -0.0003 | 0.0001 | False | True | hold_or_reject |
| hcoef10_basis_gap_sign_cap0.03_s0.25 | 0.2500 | 0.2000 | -0.0004 | -0.0000 | -0.0029 | -0.0007 | 0.0000 | 0.0001 | 0.0006 | 0.0004 | 0.0051 | 0.0020 | 0.0003 | 0.0021 | False | False | hold_or_reject |
| hcoef10_basis_gap_sign_cap0.02_s0.25 | 0.1000 | 0.1000 | -0.0005 | 0.0001 | -0.0023 | -0.0005 | 0.0001 | -0.0005 | 0.0000 | 0.0004 | 0.0028 | 0.0020 | 0.0003 | 0.0006 | False | False | hold_or_reject |
| hcoef10_basis_gap_sign_cap0.05_s0.25 | 0.2500 | 0.2000 | -0.0003 | -0.0001 | -0.0022 | -0.0005 | -0.0000 | 0.0009 | 0.0009 | 0.0003 | 0.0051 | -0.0004 | 0.0001 | 0.0021 | False | False | repeat_mape_candidate |
| hcoef10_basis_level_cap0.03_s0.50 | 0.0000 | 0.0500 | 0.0003 | 0.0003 | -0.0012 | 0.0007 | 0.0003 | -0.0009 | -0.0002 | -0.0005 | 0.0014 | -0.0008 | -0.0004 | -0.0008 | False | False | hold_or_reject |
| hcoef10_basis_level_cap0.05_s0.50 | 0.0000 | 0.0500 | 0.0003 | 0.0003 | -0.0011 | 0.0007 | 0.0004 | -0.0010 | -0.0002 | -0.0005 | 0.0014 | -0.0008 | -0.0004 | -0.0008 | False | False | hold_or_reject |
| hcoef10_basis_level_cap0.02_s0.50 | 0.0000 | 0.0500 | 0.0004 | 0.0003 | -0.0009 | 0.0007 | 0.0003 | -0.0006 | -0.0002 | -0.0005 | 0.0014 | -0.0008 | -0.0004 | -0.0008 | False | False | hold_or_reject |
| hcoef10_basis_gap_sign_cap0.02_s0.50 | 0.0000 | 0.0500 | 0.0001 | 0.0001 | -0.0008 | -0.0001 | 0.0002 | 0.0015 | 0.0016 | 0.0008 | 0.0108 | -0.0005 | 0.0006 | 0.0034 | False | False | hold_or_reject |
| hcoef10_basis_level_cap0.05_s0.25 | 0.0000 | 0.1000 | 0.0000 | 0.0002 | -0.0001 | 0.0004 | 0.0002 | -0.0007 | 0.0002 | -0.0003 | 0.0007 | -0.0001 | -0.0002 | 0.0000 | False | False | hold_or_reject |
| hcoef10_basis_level_cap0.03_s0.25 | 0.0000 | 0.1000 | 0.0000 | 0.0001 | -0.0001 | 0.0004 | 0.0002 | -0.0004 | 0.0002 | -0.0003 | 0.0007 | -0.0001 | -0.0002 | 0.0000 | False | False | hold_or_reject |
| hcoef2_size_reliability_cap005_s050 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | False | hold_or_reject |
| hcoef10_basis_level_cap0.02_s0.25 | 0.0000 | 0.0500 | 0.0000 | 0.0001 | 0.0000 | 0.0003 | 0.0002 | -0.0002 | 0.0002 | -0.0003 | 0.0007 | -0.0001 | -0.0002 | 0.0000 | False | False | hold_or_reject |
| hcoef10_basis_gap_sign_cap0.03_s0.50 | 0.0500 | 0.0000 | 0.0001 | 0.0001 | 0.0008 | 0.0001 | 0.0001 | 0.0028 | 0.0002 | 0.0009 | 0.0157 | -0.0024 | 0.0007 | 0.0034 | False | False | hold_or_reject |
| hcoef10_pred_bin_cap0.05_s0.25 | 0.0500 | 0.1000 | -0.0007 | 0.0001 | 0.0009 | -0.0011 | 0.0002 | -0.0006 | -0.0001 | 0.0001 | 0.0002 | 0.0002 | -0.0004 | 0.0001 | False | False | hold_or_reject |
| hcoef10_pred_bin_cap0.02_s0.25 | 0.0000 | 0.0500 | 0.0001 | 0.0001 | 0.0012 | -0.0005 | 0.0001 | -0.0009 | -0.0005 | 0.0002 | 0.0002 | 0.0002 | -0.0001 | 0.0000 | False | False | hold_or_reject |
| hcoef10_pred_bin_cap0.03_s0.25 | 0.1000 | 0.1000 | -0.0004 | 0.0001 | 0.0013 | -0.0010 | 0.0002 | -0.0010 | -0.0005 | 0.0002 | 0.0002 | 0.0002 | -0.0002 | 0.0001 | False | False | hold_or_reject |
| hcoef10_size_reliability_cap0.02_s0.25 | 0.0500 | 0.0500 | 0.0012 | -0.0002 | 0.0014 | 0.0012 | -0.0001 | 0.0013 | 0.0022 | 0.0007 | 0.0036 | -0.0017 | 0.0001 | 0.0001 | False | False | repeat_mape_candidate |
| hcoef10_size_reliability_cap0.03_s0.25 | 0.0500 | 0.0000 | 0.0010 | -0.0002 | 0.0021 | 0.0020 | -0.0001 | 0.0016 | 0.0040 | 0.0010 | 0.0077 | -0.0017 | 0.0001 | 0.0001 | False | False | repeat_mape_candidate |
| hcoef10_pred_bin_cap0.02_s0.50 | 0.0500 | 0.0000 | -0.0012 | 0.0003 | 0.0024 | -0.0009 | 0.0004 | -0.0013 | -0.0001 | 0.0004 | 0.0006 | 0.0006 | -0.0003 | 0.0001 | False | False | hold_or_reject |
| hcoef10_basis_reliability_cap0.02_s0.25 | 0.0000 | 0.0500 | 0.0010 | -0.0000 | 0.0027 | 0.0012 | -0.0000 | -0.0012 | 0.0024 | 0.0007 | 0.0034 | -0.0025 | 0.0003 | 0.0004 | False | False | repeat_mape_candidate |
| hcoef10_pred_bin_cap0.03_s0.50 | 0.0000 | 0.0000 | -0.0013 | 0.0004 | 0.0030 | -0.0007 | 0.0005 | -0.0004 | -0.0001 | 0.0006 | 0.0006 | -0.0006 | -0.0004 | 0.0001 | False | False | hold_or_reject |
| hcoef10_size_reliability_cap0.02_s0.50 | 0.0500 | 0.0000 | 0.0014 | -0.0003 | 0.0031 | 0.0021 | -0.0001 | 0.0025 | 0.0036 | 0.0014 | 0.0127 | -0.0037 | 0.0002 | 0.0002 | False | False | hold_or_reject |
| hcoef10_medium_support_cap0.02_s0.25 | 0.0000 | 0.0000 | 0.0006 | 0.0003 | 0.0031 | 0.0006 | 0.0003 | 0.0033 | 0.0022 | 0.0007 | -0.0004 | -0.0004 | 0.0006 | 0.0015 | False | False | hold_or_reject |

## 3. 반복 OOF 요약

| validation_scheme | candidate | mean_delta_MdAPE_vs_hcoef2 | mean_delta_MAPE_vs_hcoef2 | mean_delta_p95_APE_vs_hcoef2 | std_delta_MdAPE_vs_hcoef2 | MdAPE_improve_prob_vs_hcoef2 | MAPE_improve_prob_vs_hcoef2 | p95_improve_prob_vs_hcoef2 | all3_improve_prob_vs_hcoef2 | mean_improve_count_vs_hcoef2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| row_oof | hcoef10_basis_gap_sign_cap0.03_s0.25 | -0.0004 | -0.0000 | -0.0029 | 0.0008 | 0.6500 | 0.6500 | 0.6000 | 0.2500 | 1.9000 |
| row_oof | hcoef10_basis_gap_sign_cap0.05_s0.25 | -0.0003 | -0.0001 | -0.0022 | 0.0010 | 0.6500 | 0.7000 | 0.5500 | 0.2500 | 1.9000 |
| artist_oof | hcoef10_basis_gap_sign_cap0.03_s0.25 | -0.0007 | 0.0000 | 0.0001 | 0.0013 | 0.7500 | 0.4500 | 0.6000 | 0.2000 | 1.8000 |
| artist_oof | hcoef10_basis_gap_sign_cap0.05_s0.25 | -0.0005 | -0.0000 | 0.0009 | 0.0012 | 0.8000 | 0.5500 | 0.6000 | 0.2000 | 1.9500 |
| artist_oof | hcoef10_pred_bin_cap0.05_s0.25 | -0.0011 | 0.0002 | -0.0006 | 0.0020 | 0.7500 | 0.2500 | 0.5500 | 0.1000 | 1.5500 |
| artist_oof | hcoef10_pred_bin_cap0.03_s0.25 | -0.0010 | 0.0002 | -0.0010 | 0.0018 | 0.7500 | 0.1500 | 0.6000 | 0.1000 | 1.5000 |
| row_oof | hcoef10_basis_gap_sign_cap0.02_s0.25 | -0.0005 | 0.0001 | -0.0023 | 0.0006 | 0.8000 | 0.3000 | 0.6500 | 0.1000 | 1.7500 |
| artist_oof | hcoef10_basis_gap_sign_cap0.02_s0.25 | -0.0005 | 0.0001 | -0.0005 | 0.0012 | 0.7500 | 0.1500 | 0.6500 | 0.1000 | 1.5500 |
| row_oof | hcoef10_pred_bin_cap0.03_s0.25 | -0.0004 | 0.0001 | 0.0013 | 0.0017 | 0.7000 | 0.2500 | 0.3000 | 0.1000 | 1.2500 |
| artist_oof | hcoef10_basis_level_cap0.03_s0.25 | 0.0004 | 0.0002 | -0.0004 | 0.0011 | 0.4500 | 0.1000 | 0.6000 | 0.1000 | 1.1500 |
| artist_oof | hcoef10_basis_level_cap0.05_s0.25 | 0.0004 | 0.0002 | -0.0007 | 0.0012 | 0.4500 | 0.1000 | 0.6000 | 0.1000 | 1.1500 |
| artist_oof | hcoef10_pred_reliability_cap0.02_s0.25 | 0.0005 | 0.0002 | 0.0020 | 0.0017 | 0.4500 | 0.2000 | 0.3500 | 0.1000 | 1.0000 |
| row_oof | hcoef10_size_reliability_cap0.03_s0.50 | 0.0011 | -0.0002 | 0.0060 | 0.0019 | 0.2500 | 0.8000 | 0.3000 | 0.1000 | 1.3500 |
| row_oof | hcoef10_basis_reliability_cap0.02_s0.50 | 0.0011 | 0.0000 | 0.0058 | 0.0015 | 0.2000 | 0.5000 | 0.2500 | 0.1000 | 0.9500 |
| artist_oof | hcoef10_basis_reliability_cap0.05_s0.50 | 0.0012 | 0.0001 | 0.0065 | 0.0018 | 0.2500 | 0.5000 | 0.3000 | 0.1000 | 1.0500 |
| artist_oof | hcoef10_basis_reliability_cap0.03_s0.50 | 0.0012 | 0.0000 | 0.0031 | 0.0019 | 0.2000 | 0.5000 | 0.3500 | 0.1000 | 1.0500 |
| artist_oof | hcoef10_basis_reliability_cap0.02_s0.50 | 0.0015 | 0.0000 | 0.0008 | 0.0022 | 0.3000 | 0.4500 | 0.4000 | 0.1000 | 1.1500 |
| row_oof | hcoef10_basis_reliability_cap0.05_s0.50 | 0.0018 | 0.0001 | 0.0126 | 0.0017 | 0.1500 | 0.5000 | 0.2500 | 0.1000 | 0.9000 |
| row_oof | hcoef10_pred_bin_cap0.05_s0.50 | -0.0019 | 0.0004 | 0.0043 | 0.0020 | 0.8500 | 0.2500 | 0.2000 | 0.0500 | 1.3000 |
| row_oof | hcoef10_pred_bin_cap0.02_s0.50 | -0.0012 | 0.0003 | 0.0024 | 0.0024 | 0.5500 | 0.2500 | 0.3500 | 0.0500 | 1.1500 |
| row_oof | hcoef10_pred_bin_cap0.05_s0.25 | -0.0007 | 0.0001 | 0.0009 | 0.0022 | 0.6500 | 0.4000 | 0.3000 | 0.0500 | 1.3500 |
| artist_oof | hcoef10_pred_bin_cap0.02_s0.25 | -0.0005 | 0.0001 | -0.0009 | 0.0014 | 0.6500 | 0.2000 | 0.6000 | 0.0500 | 1.4500 |
| artist_oof | hcoef10_basis_gap_sign_cap0.05_s0.50 | -0.0002 | 0.0001 | 0.0043 | 0.0015 | 0.5500 | 0.3500 | 0.4000 | 0.0500 | 1.3000 |
| artist_oof | hcoef10_basis_gap_sign_cap0.02_s0.50 | -0.0001 | 0.0002 | 0.0015 | 0.0016 | 0.4500 | 0.0500 | 0.6000 | 0.0500 | 1.1000 |
| row_oof | hcoef10_basis_gap_sign_cap0.05_s0.50 | -0.0001 | 0.0000 | 0.0047 | 0.0012 | 0.5500 | 0.6000 | 0.3000 | 0.0500 | 1.4500 |
| row_oof | hcoef10_basis_gap_sign_cap0.03_s0.50 | 0.0001 | 0.0001 | 0.0008 | 0.0013 | 0.4500 | 0.6000 | 0.4000 | 0.0500 | 1.4500 |
| artist_oof | hcoef10_basis_level_cap0.02_s0.25 | 0.0003 | 0.0002 | -0.0002 | 0.0010 | 0.4500 | 0.0500 | 0.6000 | 0.0500 | 1.1000 |
| row_oof | hcoef10_size_reliability_cap0.05_s0.50 | 0.0006 | 0.0002 | 0.0070 | 0.0029 | 0.3500 | 0.3000 | 0.3000 | 0.0500 | 0.9500 |
| artist_oof | hcoef10_basis_level_cap0.05_s0.50 | 0.0007 | 0.0004 | -0.0010 | 0.0015 | 0.3500 | 0.0500 | 0.6000 | 0.0500 | 1.0000 |
| artist_oof | hcoef10_basis_level_cap0.03_s0.50 | 0.0007 | 0.0003 | -0.0009 | 0.0015 | 0.3500 | 0.0500 | 0.6000 | 0.0500 | 1.0000 |
| artist_oof | hcoef10_basis_level_cap0.02_s0.50 | 0.0007 | 0.0003 | -0.0006 | 0.0015 | 0.3000 | 0.0500 | 0.6000 | 0.0500 | 0.9500 |
| row_oof | hcoef10_size_reliability_cap0.03_s0.25 | 0.0010 | -0.0002 | 0.0021 | 0.0012 | 0.2000 | 0.8500 | 0.3000 | 0.0500 | 1.3500 |
| row_oof | hcoef10_basis_reliability_cap0.03_s0.25 | 0.0011 | -0.0001 | 0.0040 | 0.0011 | 0.1000 | 0.6500 | 0.2000 | 0.0500 | 0.9500 |
| row_oof | hcoef10_basis_reliability_cap0.05_s0.25 | 0.0011 | -0.0000 | 0.0068 | 0.0013 | 0.1000 | 0.5500 | 0.2500 | 0.0500 | 0.9000 |
| row_oof | hcoef10_size_reliability_cap0.02_s0.25 | 0.0012 | -0.0002 | 0.0014 | 0.0013 | 0.1500 | 0.8500 | 0.4000 | 0.0500 | 1.4000 |
| artist_oof | hcoef10_basis_reliability_cap0.02_s0.25 | 0.0012 | -0.0000 | -0.0012 | 0.0011 | 0.1000 | 0.6000 | 0.7500 | 0.0500 | 1.4500 |
| artist_oof | hcoef10_size_reliability_cap0.03_s0.50 | 0.0012 | 0.0001 | 0.0044 | 0.0019 | 0.2000 | 0.5000 | 0.2500 | 0.0500 | 0.9500 |
| artist_oof | hcoef10_size_reliability_cap0.02_s0.25 | 0.0012 | -0.0001 | 0.0013 | 0.0010 | 0.1500 | 0.6500 | 0.3500 | 0.0500 | 1.1500 |
| artist_oof | hcoef10_basis_reliability_cap0.05_s0.25 | 0.0013 | -0.0001 | 0.0020 | 0.0013 | 0.1500 | 0.6000 | 0.3500 | 0.0500 | 1.1000 |
| row_oof | hcoef10_size_reliability_cap0.02_s0.50 | 0.0014 | -0.0003 | 0.0031 | 0.0015 | 0.1500 | 0.8000 | 0.2500 | 0.0500 | 1.2000 |

## 4. Fixed test p95 상위 후보

| candidate | method | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_hcoef2 | delta_MAPE_vs_hcoef2 | delta_p95_APE_vs_hcoef2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef10_medium_size_cap0.05_s0.50 | cause_segment_median_residual | 0.1441 | 0.2755 | 0.8035 | 0.4001 | 0.0053 | 0.0025 | -0.0028 |
| hcoef10_medium_support_cap0.05_s0.50 | cause_segment_median_residual | 0.1436 | 0.2749 | 0.8049 | 0.3997 | 0.0048 | 0.0019 | -0.0015 |
| hcoef10_medium_support_cap0.03_s0.50 | cause_segment_median_residual | 0.1435 | 0.2749 | 0.8049 | 0.3997 | 0.0047 | 0.0019 | -0.0015 |
| hcoef10_medium_size_cap0.03_s0.50 | cause_segment_median_residual | 0.1445 | 0.2750 | 0.8049 | 0.3997 | 0.0057 | 0.0020 | -0.0015 |
| hcoef10_medium_size_cap0.05_s0.25 | cause_segment_median_residual | 0.1411 | 0.2741 | 0.8050 | 0.3994 | 0.0022 | 0.0012 | -0.0014 |
| hcoef10_medium_support_cap0.02_s0.50 | cause_segment_median_residual | 0.1433 | 0.2743 | 0.8056 | 0.3993 | 0.0045 | 0.0014 | -0.0008 |
| hcoef10_medium_size_cap0.02_s0.50 | cause_segment_median_residual | 0.1438 | 0.2745 | 0.8056 | 0.3994 | 0.0050 | 0.0015 | -0.0008 |
| hcoef10_medium_support_cap0.05_s0.25 | cause_segment_median_residual | 0.1411 | 0.2739 | 0.8056 | 0.3992 | 0.0022 | 0.0009 | -0.0007 |
| hcoef10_medium_support_cap0.03_s0.25 | cause_segment_median_residual | 0.1411 | 0.2739 | 0.8056 | 0.3992 | 0.0022 | 0.0009 | -0.0007 |
| hcoef10_medium_size_cap0.03_s0.25 | cause_segment_median_residual | 0.1417 | 0.2739 | 0.8056 | 0.3993 | 0.0029 | 0.0009 | -0.0007 |
| hcoef10_medium_support_cap0.02_s0.25 | cause_segment_median_residual | 0.1411 | 0.2736 | 0.8060 | 0.3991 | 0.0022 | 0.0007 | -0.0004 |
| hcoef10_medium_size_cap0.02_s0.25 | cause_segment_median_residual | 0.1417 | 0.2737 | 0.8060 | 0.3991 | 0.0029 | 0.0007 | -0.0004 |
| hcoef10_pred_reliability_cap0.02_s0.25 | cause_segment_median_residual | 0.1383 | 0.2729 | 0.8062 | 0.3987 | -0.0005 | -0.0001 | -0.0002 |
| hcoef10_pred_reliability_cap0.03_s0.25 | cause_segment_median_residual | 0.1383 | 0.2729 | 0.8062 | 0.3987 | -0.0005 | -0.0001 | -0.0002 |
| hcoef10_pred_reliability_cap0.05_s0.25 | cause_segment_median_residual | 0.1387 | 0.2732 | 0.8062 | 0.3987 | -0.0001 | 0.0002 | -0.0002 |
| hcoef10_pred_reliability_cap0.02_s0.50 | cause_segment_median_residual | 0.1404 | 0.2729 | 0.8062 | 0.3986 | 0.0016 | -0.0001 | -0.0001 |
| hcoef10_pred_reliability_cap0.03_s0.50 | cause_segment_median_residual | 0.1420 | 0.2731 | 0.8062 | 0.3986 | 0.0032 | 0.0001 | -0.0001 |
| hcoef10_pred_reliability_cap0.05_s0.50 | cause_segment_median_residual | 0.1420 | 0.2740 | 0.8062 | 0.3988 | 0.0032 | 0.0010 | -0.0001 |
| hcoef2_size_reliability_cap005_s050 | hcoef3_stable_anchor | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 |
| hcoef10_pred_bin_cap0.02_s0.25 | cause_segment_median_residual | 0.1383 | 0.2732 | 0.8066 | 0.3990 | -0.0005 | 0.0002 | 0.0002 |
| hcoef10_pred_bin_cap0.03_s0.25 | cause_segment_median_residual | 0.1383 | 0.2732 | 0.8066 | 0.3991 | -0.0005 | 0.0002 | 0.0002 |
| hcoef10_pred_bin_cap0.05_s0.25 | cause_segment_median_residual | 0.1387 | 0.2731 | 0.8066 | 0.3991 | -0.0001 | 0.0001 | 0.0002 |
| hcoef10_pred_bin_cap0.02_s0.50 | cause_segment_median_residual | 0.1387 | 0.2734 | 0.8070 | 0.3992 | -0.0001 | 0.0004 | 0.0006 |
| hcoef10_pred_bin_cap0.05_s0.50 | cause_segment_median_residual | 0.1387 | 0.2735 | 0.8070 | 0.3995 | -0.0001 | 0.0005 | 0.0006 |
| hcoef10_pred_bin_cap0.03_s0.50 | cause_segment_median_residual | 0.1387 | 0.2736 | 0.8070 | 0.3994 | -0.0001 | 0.0006 | 0.0006 |
| hcoef10_basis_level_cap0.02_s0.25 | cause_segment_median_residual | 0.1390 | 0.2727 | 0.8071 | 0.3988 | 0.0002 | -0.0003 | 0.0007 |
| hcoef10_basis_level_cap0.03_s0.25 | cause_segment_median_residual | 0.1390 | 0.2727 | 0.8071 | 0.3988 | 0.0002 | -0.0003 | 0.0007 |
| hcoef10_basis_level_cap0.05_s0.25 | cause_segment_median_residual | 0.1390 | 0.2727 | 0.8071 | 0.3988 | 0.0002 | -0.0003 | 0.0007 |

## 5. 보정 적용 규모

| split | candidate | mean_abs_correction_log | max_abs_correction_log | overall_fallback_share | median_matched_n |
| --- | --- | --- | --- | --- | --- |
| 0604_ex50 | hcoef10_size_reliability_cap0.05_s0.50 | 0.0150 | 0.0250 | 0.0157 | 40.0000 |
| 0604_ex50 | hcoef10_pred_reliability_cap0.05_s0.50 | 0.0140 | 0.0250 | 0.0000 | 24.0000 |
| 0604_ex50 | hcoef10_size_reliability_cap0.03_s0.50 | 0.0111 | 0.0150 | 0.0157 | 40.0000 |
| 0604_ex50 | hcoef10_pred_reliability_cap0.03_s0.50 | 0.0106 | 0.0150 | 0.0000 | 24.0000 |
| 0604_ex50 | hcoef10_basis_reliability_cap0.05_s0.50 | 0.0097 | 0.0250 | 0.0000 | 128.0000 |
| 0604_ex50 | hcoef10_basis_reliability_cap0.03_s0.50 | 0.0095 | 0.0150 | 0.0000 | 128.0000 |
| 0604_ex50 | hcoef10_pred_bin_cap0.05_s0.50 | 0.0093 | 0.0250 | 0.0000 | 52.0000 |
| 0604_ex50 | hcoef10_basis_gap_sign_cap0.05_s0.50 | 0.0085 | 0.0223 | 0.0000 | 121.0000 |
| 0604_ex50 | hcoef10_basis_reliability_cap0.02_s0.50 | 0.0084 | 0.0100 | 0.0000 | 128.0000 |
| 0604_ex50 | hcoef10_size_reliability_cap0.02_s0.50 | 0.0082 | 0.0100 | 0.0157 | 40.0000 |
| 0604_ex50 | hcoef10_pred_reliability_cap0.02_s0.50 | 0.0079 | 0.0100 | 0.0000 | 24.0000 |
| 0604_ex50 | hcoef10_pred_bin_cap0.03_s0.50 | 0.0078 | 0.0150 | 0.0000 | 52.0000 |
| 0604_ex50 | hcoef10_size_reliability_cap0.05_s0.25 | 0.0075 | 0.0125 | 0.0157 | 40.0000 |
| 0604_ex50 | hcoef10_basis_gap_sign_cap0.03_s0.50 | 0.0074 | 0.0150 | 0.0000 | 121.0000 |
| 0604_ex50 | hcoef10_pred_reliability_cap0.05_s0.25 | 0.0070 | 0.0125 | 0.0000 | 24.0000 |
| 0604_ex50 | hcoef10_medium_size_cap0.05_s0.50 | 0.0069 | 0.0250 | 0.5850 | 0.0000 |
| 0604_ex50 | hcoef10_pred_bin_cap0.02_s0.50 | 0.0061 | 0.0100 | 0.0000 | 52.0000 |
| 0604_ex50 | hcoef10_basis_gap_sign_cap0.02_s0.50 | 0.0060 | 0.0100 | 0.0000 | 121.0000 |
| 0604_ex50 | hcoef10_medium_size_cap0.03_s0.50 | 0.0058 | 0.0150 | 0.5850 | 0.0000 |
| 0604_ex50 | hcoef10_size_reliability_cap0.03_s0.25 | 0.0056 | 0.0075 | 0.0157 | 40.0000 |
| 0604_ex50 | hcoef10_pred_reliability_cap0.03_s0.25 | 0.0053 | 0.0075 | 0.0000 | 24.0000 |
| 0604_ex50 | hcoef10_medium_support_cap0.05_s0.50 | 0.0053 | 0.0152 | 0.5850 | 0.0000 |
| 0604_ex50 | hcoef10_medium_support_cap0.03_s0.50 | 0.0053 | 0.0150 | 0.5850 | 0.0000 |
| 0604_ex50 | hcoef10_basis_reliability_cap0.05_s0.25 | 0.0049 | 0.0125 | 0.0000 | 128.0000 |
| 0604_ex50 | hcoef10_basis_reliability_cap0.03_s0.25 | 0.0047 | 0.0075 | 0.0000 | 128.0000 |
| 0604_ex50 | hcoef10_pred_bin_cap0.05_s0.25 | 0.0046 | 0.0125 | 0.0000 | 52.0000 |
| 0604_ex50 | hcoef10_medium_size_cap0.02_s0.50 | 0.0043 | 0.0100 | 0.5850 | 0.0000 |
| 0604_ex50 | hcoef10_basis_gap_sign_cap0.05_s0.25 | 0.0043 | 0.0112 | 0.0000 | 121.0000 |

## 6. 구간별 보정값 예시

| candidate | segment_keys | matched_level | matched_key | matched_n | raw_median_residual_log | limited_correction_log | cap | strength | min_n | purpose |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef10_basis_gap_sign_cap0.02_s0.25 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign | basis_flat | 286 | 0.0031 | 0.0008 | 0.0200 | 0.2500 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.02_s0.25 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign | basis_pos | 121 | -0.0145 | -0.0036 | 0.0200 | 0.2500 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.02_s0.25 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign | basis_neg | 112 | 0.0138 | 0.0034 | 0.0200 | 0.2500 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.02_s0.25 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign+ppv8_gap_sign | basis_flat|ppv8_flat | 268 | 0.0051 | 0.0013 | 0.0200 | 0.2500 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.02_s0.25 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign+ppv8_gap_sign | basis_pos|ppv8_flat | 102 | -0.0447 | -0.0050 | 0.0200 | 0.2500 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.02_s0.25 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign+ppv8_gap_sign | basis_neg|ppv8_flat | 97 | 0.0277 | 0.0050 | 0.0200 | 0.2500 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.02_s0.25 | basis_gap_sign+ppv8_gap_sign | overall | overall | 519 | 0.0021 | 0.0005 | 0.0200 | 0.2500 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.02_s0.50 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign | basis_flat | 286 | 0.0031 | 0.0015 | 0.0200 | 0.5000 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.02_s0.50 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign | basis_pos | 121 | -0.0145 | -0.0072 | 0.0200 | 0.5000 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.02_s0.50 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign | basis_neg | 112 | 0.0138 | 0.0069 | 0.0200 | 0.5000 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.02_s0.50 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign+ppv8_gap_sign | basis_flat|ppv8_flat | 268 | 0.0051 | 0.0025 | 0.0200 | 0.5000 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.02_s0.50 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign+ppv8_gap_sign | basis_pos|ppv8_flat | 102 | -0.0447 | -0.0100 | 0.0200 | 0.5000 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.02_s0.50 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign+ppv8_gap_sign | basis_neg|ppv8_flat | 97 | 0.0277 | 0.0100 | 0.0200 | 0.5000 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.02_s0.50 | basis_gap_sign+ppv8_gap_sign | overall | overall | 519 | 0.0021 | 0.0011 | 0.0200 | 0.5000 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.03_s0.25 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign | basis_flat | 286 | 0.0031 | 0.0008 | 0.0300 | 0.2500 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.03_s0.25 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign | basis_pos | 121 | -0.0145 | -0.0036 | 0.0300 | 0.2500 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.03_s0.25 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign | basis_neg | 112 | 0.0138 | 0.0034 | 0.0300 | 0.2500 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.03_s0.25 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign+ppv8_gap_sign | basis_flat|ppv8_flat | 268 | 0.0051 | 0.0013 | 0.0300 | 0.2500 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.03_s0.25 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign+ppv8_gap_sign | basis_pos|ppv8_flat | 102 | -0.0447 | -0.0075 | 0.0300 | 0.2500 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.03_s0.25 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign+ppv8_gap_sign | basis_neg|ppv8_flat | 97 | 0.0277 | 0.0069 | 0.0300 | 0.2500 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.03_s0.25 | basis_gap_sign+ppv8_gap_sign | overall | overall | 519 | 0.0021 | 0.0005 | 0.0300 | 0.2500 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.03_s0.50 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign | basis_flat | 286 | 0.0031 | 0.0015 | 0.0300 | 0.5000 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.03_s0.50 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign | basis_pos | 121 | -0.0145 | -0.0072 | 0.0300 | 0.5000 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.03_s0.50 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign | basis_neg | 112 | 0.0138 | 0.0069 | 0.0300 | 0.5000 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.03_s0.50 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign+ppv8_gap_sign | basis_flat|ppv8_flat | 268 | 0.0051 | 0.0025 | 0.0300 | 0.5000 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.03_s0.50 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign+ppv8_gap_sign | basis_pos|ppv8_flat | 102 | -0.0447 | -0.0150 | 0.0300 | 0.5000 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.03_s0.50 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign+ppv8_gap_sign | basis_neg|ppv8_flat | 97 | 0.0277 | 0.0138 | 0.0300 | 0.5000 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.03_s0.50 | basis_gap_sign+ppv8_gap_sign | overall | overall | 519 | 0.0021 | 0.0011 | 0.0300 | 0.5000 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.05_s0.25 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign | basis_flat | 286 | 0.0031 | 0.0008 | 0.0500 | 0.2500 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.05_s0.25 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign | basis_pos | 121 | -0.0145 | -0.0036 | 0.0500 | 0.2500 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.05_s0.25 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign | basis_neg | 112 | 0.0138 | 0.0034 | 0.0500 | 0.2500 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.05_s0.25 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign+ppv8_gap_sign | basis_flat|ppv8_flat | 268 | 0.0051 | 0.0013 | 0.0500 | 0.2500 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.05_s0.25 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign+ppv8_gap_sign | basis_pos|ppv8_flat | 102 | -0.0447 | -0.0112 | 0.0500 | 0.2500 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.05_s0.25 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign+ppv8_gap_sign | basis_neg|ppv8_flat | 97 | 0.0277 | 0.0069 | 0.0500 | 0.2500 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.05_s0.25 | basis_gap_sign+ppv8_gap_sign | overall | overall | 519 | 0.0021 | 0.0005 | 0.0500 | 0.2500 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.05_s0.50 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign | basis_flat | 286 | 0.0031 | 0.0015 | 0.0500 | 0.5000 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.05_s0.50 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign | basis_pos | 121 | -0.0145 | -0.0072 | 0.0500 | 0.5000 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.05_s0.50 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign | basis_neg | 112 | 0.0138 | 0.0069 | 0.0500 | 0.5000 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.05_s0.50 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign+ppv8_gap_sign | basis_flat|ppv8_flat | 268 | 0.0051 | 0.0025 | 0.0500 | 0.5000 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.05_s0.50 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign+ppv8_gap_sign | basis_pos|ppv8_flat | 102 | -0.0447 | -0.0223 | 0.0500 | 0.5000 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.05_s0.50 | basis_gap_sign+ppv8_gap_sign | basis_gap_sign+ppv8_gap_sign | basis_neg|ppv8_flat | 97 | 0.0277 | 0.0138 | 0.0500 | 0.5000 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_gap_sign_cap0.05_s0.50 | basis_gap_sign+ppv8_gap_sign | overall | overall | 519 | 0.0021 | 0.0011 | 0.0500 | 0.5000 | 15 | 기준가와 기존 후보 간 방향 차이에 따른 편향 보정 |
| hcoef10_basis_level_cap0.02_s0.25 | basis_level_simple | basis_level_simple | artist_detail | 370 | 0.0023 | 0.0006 | 0.0200 | 0.2500 | 20 | 작가 기반/시장 기반 fallback level별 편향 보정 |
| hcoef10_basis_level_cap0.02_s0.25 | basis_level_simple | basis_level_simple | artist_overall | 149 | -0.0119 | -0.0030 | 0.0200 | 0.2500 | 20 | 작가 기반/시장 기반 fallback level별 편향 보정 |
| hcoef10_basis_level_cap0.02_s0.25 | basis_level_simple | overall | overall | 519 | 0.0021 | 0.0005 | 0.0200 | 0.2500 | 20 | 작가 기반/시장 기반 fallback level별 편향 보정 |
| hcoef10_basis_level_cap0.02_s0.50 | basis_level_simple | basis_level_simple | artist_detail | 370 | 0.0023 | 0.0012 | 0.0200 | 0.5000 | 20 | 작가 기반/시장 기반 fallback level별 편향 보정 |
| hcoef10_basis_level_cap0.02_s0.50 | basis_level_simple | basis_level_simple | artist_overall | 149 | -0.0119 | -0.0059 | 0.0200 | 0.5000 | 20 | 작가 기반/시장 기반 fallback level별 편향 보정 |
| hcoef10_basis_level_cap0.02_s0.50 | basis_level_simple | overall | overall | 519 | 0.0021 | 0.0011 | 0.0200 | 0.5000 | 20 | 작가 기반/시장 기반 fallback level별 편향 보정 |
| hcoef10_basis_level_cap0.03_s0.25 | basis_level_simple | basis_level_simple | artist_detail | 370 | 0.0023 | 0.0006 | 0.0300 | 0.2500 | 20 | 작가 기반/시장 기반 fallback level별 편향 보정 |
| hcoef10_basis_level_cap0.03_s0.25 | basis_level_simple | basis_level_simple | artist_overall | 149 | -0.0119 | -0.0030 | 0.0300 | 0.2500 | 20 | 작가 기반/시장 기반 fallback level별 편향 보정 |

## 7. 잔차/큰 오차 요약

| split | candidate | n | median_residual_log | mean_residual_log | residual_std | over_2x_n | under_half_n | ape_gt_100pct_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_ex50 | hcoef10_basis_gap_sign_cap0.02_s0.25 | 829 | 0.0600 | 0.3278 | 1.2675 | 27 | 152 | 27 |
| 0604_ex50 | hcoef10_basis_gap_sign_cap0.02_s0.50 | 829 | 0.0593 | 0.3277 | 1.2683 | 27 | 154 | 27 |
| 0604_ex50 | hcoef10_basis_gap_sign_cap0.03_s0.25 | 829 | 0.0600 | 0.3279 | 1.2676 | 27 | 152 | 27 |
| 0604_ex50 | hcoef10_basis_gap_sign_cap0.03_s0.50 | 829 | 0.0593 | 0.3280 | 1.2683 | 27 | 154 | 27 |
| 0604_ex50 | hcoef10_basis_gap_sign_cap0.05_s0.25 | 829 | 0.0600 | 0.3285 | 1.2675 | 27 | 152 | 27 |
| 0604_ex50 | hcoef10_basis_gap_sign_cap0.05_s0.50 | 829 | 0.0593 | 0.3291 | 1.2682 | 27 | 154 | 27 |
| 0604_ex50 | hcoef10_basis_level_cap0.02_s0.25 | 829 | 0.0602 | 0.3283 | 1.2667 | 26 | 152 | 26 |
| 0604_ex50 | hcoef10_basis_level_cap0.02_s0.50 | 829 | 0.0596 | 0.3289 | 1.2667 | 26 | 154 | 26 |
| 0604_ex50 | hcoef10_basis_level_cap0.03_s0.25 | 829 | 0.0602 | 0.3283 | 1.2667 | 26 | 152 | 26 |
| 0604_ex50 | hcoef10_basis_level_cap0.03_s0.50 | 829 | 0.0596 | 0.3289 | 1.2667 | 26 | 154 | 26 |
| 0604_ex50 | hcoef10_basis_level_cap0.05_s0.25 | 829 | 0.0602 | 0.3283 | 1.2667 | 26 | 152 | 26 |
| 0604_ex50 | hcoef10_basis_level_cap0.05_s0.50 | 829 | 0.0596 | 0.3289 | 1.2667 | 26 | 154 | 26 |
| 0604_ex50 | hcoef10_basis_reliability_cap0.02_s0.25 | 829 | 0.0574 | 0.3266 | 1.2668 | 27 | 151 | 27 |
| 0604_ex50 | hcoef10_basis_reliability_cap0.02_s0.50 | 829 | 0.0586 | 0.3254 | 1.2668 | 27 | 151 | 27 |
| 0604_ex50 | hcoef10_basis_reliability_cap0.03_s0.25 | 829 | 0.0587 | 0.3271 | 1.2668 | 27 | 151 | 27 |
| 0604_ex50 | hcoef10_basis_reliability_cap0.03_s0.50 | 829 | 0.0612 | 0.3265 | 1.2668 | 27 | 151 | 27 |
| 0604_ex50 | hcoef10_basis_reliability_cap0.05_s0.25 | 829 | 0.0587 | 0.3273 | 1.2668 | 27 | 151 | 27 |
| 0604_ex50 | hcoef10_basis_reliability_cap0.05_s0.50 | 829 | 0.0613 | 0.3267 | 1.2668 | 27 | 151 | 27 |
| 0604_ex50 | hcoef10_medium_size_cap0.02_s0.25 | 829 | 0.0603 | 0.3261 | 1.2671 | 27 | 152 | 27 |
| 0604_ex50 | hcoef10_medium_size_cap0.02_s0.50 | 829 | 0.0598 | 0.3244 | 1.2674 | 27 | 152 | 27 |
| 0604_ex50 | hcoef10_medium_size_cap0.03_s0.25 | 829 | 0.0603 | 0.3255 | 1.2672 | 27 | 152 | 27 |
| 0604_ex50 | hcoef10_medium_size_cap0.03_s0.50 | 829 | 0.0598 | 0.3232 | 1.2677 | 30 | 152 | 30 |
| 0604_ex50 | hcoef10_medium_size_cap0.05_s0.25 | 829 | 0.0603 | 0.3249 | 1.2673 | 27 | 152 | 27 |
| 0604_ex50 | hcoef10_medium_size_cap0.05_s0.50 | 829 | 0.0598 | 0.3221 | 1.2678 | 30 | 152 | 30 |
| 0604_ex50 | hcoef10_medium_support_cap0.02_s0.25 | 829 | 0.0603 | 0.3258 | 1.2671 | 27 | 152 | 27 |
| 0604_ex50 | hcoef10_medium_support_cap0.02_s0.50 | 829 | 0.0598 | 0.3238 | 1.2675 | 27 | 152 | 27 |
| 0604_ex50 | hcoef10_medium_support_cap0.03_s0.25 | 829 | 0.0603 | 0.3252 | 1.2673 | 27 | 152 | 27 |
| 0604_ex50 | hcoef10_medium_support_cap0.03_s0.50 | 829 | 0.0598 | 0.3226 | 1.2677 | 30 | 152 | 30 |
| 0604_ex50 | hcoef10_medium_support_cap0.05_s0.25 | 829 | 0.0603 | 0.3251 | 1.2673 | 27 | 152 | 27 |
| 0604_ex50 | hcoef10_medium_support_cap0.05_s0.50 | 829 | 0.0598 | 0.3225 | 1.2678 | 30 | 152 | 30 |
| 0604_ex50 | hcoef10_pred_bin_cap0.02_s0.25 | 829 | 0.0610 | 0.3282 | 1.2668 | 26 | 152 | 26 |
| 0604_ex50 | hcoef10_pred_bin_cap0.02_s0.50 | 829 | 0.0613 | 0.3286 | 1.2668 | 26 | 153 | 26 |
| 0604_ex50 | hcoef10_pred_bin_cap0.03_s0.25 | 829 | 0.0610 | 0.3285 | 1.2668 | 26 | 153 | 26 |
| 0604_ex50 | hcoef10_pred_bin_cap0.03_s0.50 | 829 | 0.0614 | 0.3292 | 1.2668 | 26 | 153 | 26 |
| 0604_ex50 | hcoef10_pred_bin_cap0.05_s0.25 | 829 | 0.0610 | 0.3292 | 1.2666 | 26 | 153 | 26 |
| 0604_ex50 | hcoef10_pred_bin_cap0.05_s0.50 | 829 | 0.0633 | 0.3305 | 1.2665 | 26 | 153 | 26 |

## 8. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/residual_analysis.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `outputs/selected_candidates.csv`
- `outputs/segment_application_summary.csv`
- `artifacts/experiment_config.json`