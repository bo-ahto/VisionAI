# PP-HCOEF14 Warm Huber 위험 구간 shrinkage/routing OOF 실험

- 작성일: 2026-06-08 01:01
- 목적: HCOEF13에서 확인한 위험 구간에 한정해 보정 축소, 70:30 기준 routing, 작은 segment residual 보정을 검증.
- 기준 후보: `hcoef2_size_reliability_cap005_s050`.
- 비교 기준: `current_70_30`.
- 반복 설정: row OOF 20회, artist OOF 20회, 각 5 folds.
- 후보 선택: 반복 OOF 우선. fixed test/0604는 확인용.

## 1. 실행 결론

- 판단: 새 운영 후보 채택 없음.
- 현재 결과에서 반복 OOF gate와 fixed p95 guard를 동시에 통과하지 못하면 기본 후보로 채택하지 않는다.

## 2. 후보 선택표

| candidate | method | candidate_status | passes_repeat_gate | passes_fixed_guard | all3_improve_prob_vs_stable_row_oof | all3_improve_prob_vs_stable_artist_oof | test_MdAPE | test_MAPE | test_p95_APE | test_delta_MdAPE_vs_stable | test_delta_MAPE_vs_stable | test_delta_p95_APE_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef14_seg_iqr_cap002_s025 | segment_residual | fixed 확인용 보류 | False | True | 0.1500 | 0.2500 | 0.1388 | 0.2729 | 0.8062 | 0.0000 | -0.0001 | -0.0001 |
| hcoef14_seg_core_risk_cap002_s025 | segment_residual | fixed 확인용 보류 | False | True | 0.0000 | 0.0000 | 0.1389 | 0.2729 | 0.8057 | 0.0001 | -0.0001 | -0.0007 |
| hcoef14_seg_core_risk_cap003_s025 | segment_residual | fixed 확인용 보류 | False | True | 0.0000 | 0.0000 | 0.1389 | 0.2728 | 0.8055 | 0.0001 | -0.0002 | -0.0009 |
| hcoef14_shrink_iqr_mid_high_keep075 | shrink_hcoef | fixed 확인용 보류 | False | True | 0.0000 | 0.0000 | 0.1387 | 0.2730 | 0.8055 | -0.0001 | 0.0000 | -0.0008 |
| hcoef14_shrink_iqr_mid_high_keep050 | shrink_hcoef | fixed 확인용 보류 | False | True | 0.0000 | 0.0000 | 0.1384 | 0.2731 | 0.8047 | -0.0004 | 0.0001 | -0.0017 |
| hcoef14_seg_n1019_cap002_s050 | segment_residual | 보류 | False | False | 0.0000 | 0.0000 | 0.1404 | 0.2726 | 0.8068 | 0.0016 | -0.0004 | 0.0004 |
| hcoef14_seg_n1019_cap002_s025 | segment_residual | 보류 | False | False | 0.0000 | 0.0000 | 0.1389 | 0.2728 | 0.8065 | 0.0001 | -0.0002 | 0.0001 |
| hcoef14_seg_size_basis_cap002_s025 | segment_residual | 보류 | False | False | 0.0000 | 0.0000 | 0.1389 | 0.2731 | 0.8065 | 0.0001 | 0.0001 | 0.0001 |
| hcoef14_route_core_gap_ref_w025 | route_reference | 보류 | False | False | 0.0000 | 0.0000 | 0.1389 | 0.2731 | 0.8101 | 0.0001 | 0.0001 | 0.0037 |
| hcoef14_route_basis_disagree_ref_w025 | route_reference | 보류 | False | False | 0.0000 | 0.0000 | 0.1389 | 0.2730 | 0.8075 | 0.0001 | 0.0000 | 0.0011 |
| hcoef14_route_core_gap_ref_w050 | route_reference | 보류 | False | False | 0.0000 | 0.0000 | 0.1395 | 0.2731 | 0.8169 | 0.0007 | 0.0002 | 0.0106 |
| hcoef14_seg_gap_cap002_s025 | segment_residual | 보류 | False | False | 0.0000 | 0.0000 | 0.1388 | 0.2731 | 0.8094 | 0.0000 | 0.0001 | 0.0030 |
| hcoef14_route_basis_disagree_ref_w050 | route_reference | 보류 | False | False | 0.0000 | 0.0000 | 0.1395 | 0.2731 | 0.8087 | 0.0007 | 0.0001 | 0.0024 |
| hcoef14_shrink_n1019_keep075 | shrink_hcoef | 보류 | False | False | 0.0000 | 0.0000 | 0.1389 | 0.2731 | 0.8064 | 0.0001 | 0.0001 | 0.0000 |
| hcoef14_route_ppv8_pos_ref_w050 | route_reference | 보류 | False | False | 0.0000 | 0.0000 | 0.1388 | 0.2730 | 0.8169 | 0.0000 | -0.0000 | 0.0105 |
| hcoef14_route_ppv8_pos_ref_w025 | route_reference | 보류 | False | False | 0.0000 | 0.0000 | 0.1388 | 0.2730 | 0.8101 | 0.0000 | -0.0000 | 0.0037 |
| hcoef14_seg_pred_basis_cap002_s025 | segment_residual | 보류 | False | False | 0.0000 | 0.0000 | 0.1388 | 0.2729 | 0.8064 | 0.0000 | -0.0001 | 0.0000 |
| hcoef14_shrink_n1019_keep050 | shrink_hcoef | 보류 | False | False | 0.0000 | 0.0000 | 0.1395 | 0.2732 | 0.8064 | 0.0007 | 0.0002 | 0.0000 |
| hcoef14_shrink_core_risk_keep075 | shrink_hcoef | 보류 | False | False | 0.0000 | 0.0000 | 0.1387 | 0.2730 | 0.8097 | -0.0001 | 0.0000 | 0.0034 |
| hcoef14_route_artist_overall_ref_w025 | route_reference | fixed 확인용 보류 | False | False | 0.0000 | 0.0000 | 0.1387 | 0.2729 | 0.8066 | -0.0001 | -0.0000 | 0.0003 |

## 3. 반복 OOF 요약

| validation_scheme | candidate | method | mean_delta_MdAPE_vs_stable | mean_delta_MAPE_vs_stable | mean_delta_p95_APE_vs_stable | MdAPE_improve_prob_vs_stable | MAPE_improve_prob_vs_stable | p95_improve_prob_vs_stable | all3_improve_prob_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| artist_oof | hcoef14_seg_iqr_cap002_s025 | segment_residual | -0.0004 | -0.0003 | -0.0010 | 0.5500 | 1.0000 | 0.5000 | 0.2500 |
| artist_oof | hcoef14_route_basis_disagree_ref_w025 | route_reference | -0.0005 | 0.0000 | 0.0000 | 0.5000 | 0.3000 | 0.0000 | 0.0000 |
| artist_oof | hcoef14_route_core_gap_ref_w025 | route_reference | -0.0005 | -0.0000 | 0.0000 | 0.5000 | 0.8000 | 0.0000 | 0.0000 |
| artist_oof | hcoef14_route_ppv8_pos_ref_w025 | route_reference | 0.0000 | -0.0001 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 |
| artist_oof | hcoef14_route_ppv8_pos_ref_w050 | route_reference | 0.0000 | -0.0002 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 |
| artist_oof | hcoef14_seg_gap_cap002_s025 | segment_residual | -0.0003 | -0.0002 | 0.0000 | 0.5000 | 1.0000 | 0.0000 | 0.0000 |
| artist_oof | hcoef14_seg_n1019_cap002_s025 | segment_residual | -0.0003 | -0.0004 | 0.0000 | 0.4500 | 1.0000 | 0.0000 | 0.0000 |
| artist_oof | hcoef14_seg_n1019_cap002_s050 | segment_residual | -0.0009 | -0.0008 | 0.0000 | 0.8000 | 1.0000 | 0.0000 | 0.0000 |
| artist_oof | hcoef14_seg_pred_basis_cap002_s025 | segment_residual | 0.0002 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.0000 | 0.0000 |
| artist_oof | hcoef14_seg_size_basis_cap002_s025 | segment_residual | -0.0001 | -0.0004 | 0.0000 | 0.4500 | 1.0000 | 0.0000 | 0.0000 |
| artist_oof | hcoef14_shrink_n1019_keep050 | shrink_hcoef | -0.0001 | 0.0002 | 0.0000 | 0.4500 | 0.0000 | 0.0000 | 0.0000 |
| artist_oof | hcoef14_shrink_n1019_keep075 | shrink_hcoef | -0.0003 | 0.0001 | 0.0000 | 0.4500 | 0.0000 | 0.0000 | 0.0000 |
| artist_oof | hcoef2_size_reliability_cap005_s050 | stable_oof_anchor | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| artist_oof | hcoef14_route_basis_disagree_ref_w050 | route_reference | -0.0008 | 0.0000 | 0.0002 | 0.8000 | 0.2500 | 0.0000 | 0.0000 |
| artist_oof | hcoef14_route_core_gap_ref_w050 | route_reference | -0.0008 | -0.0001 | 0.0002 | 0.8000 | 0.7500 | 0.0000 | 0.0000 |
| artist_oof | hcoef14_seg_core_risk_cap002_s025 | segment_residual | 0.0006 | -0.0001 | 0.0004 | 0.2000 | 0.9500 | 0.2000 | 0.0000 |
| artist_oof | hcoef14_seg_core_risk_cap003_s025 | segment_residual | 0.0007 | -0.0002 | 0.0011 | 0.1500 | 0.9500 | 0.2000 | 0.0000 |
| artist_oof | hcoef14_shrink_iqr_mid_high_keep075 | shrink_hcoef | 0.0002 | 0.0002 | 0.0035 | 0.0500 | 0.0000 | 0.0000 | 0.0000 |
| artist_oof | hcoef14_route_artist_overall_ref_w025 | route_reference | 0.0010 | 0.0003 | 0.0037 | 0.0500 | 0.0000 | 0.0000 | 0.0000 |
| artist_oof | hcoef14_shrink_core_risk_keep075 | shrink_hcoef | 0.0005 | 0.0002 | 0.0037 | 0.1000 | 0.0000 | 0.0000 | 0.0000 |
| artist_oof | hcoef14_shrink_iqr_mid_high_keep050 | shrink_hcoef | 0.0002 | 0.0003 | 0.0057 | 0.1000 | 0.0000 | 0.0000 | 0.0000 |
| artist_oof | hcoef14_route_artist_overall_ref_w050 | route_reference | 0.0006 | 0.0006 | 0.0058 | 0.2500 | 0.0000 | 0.0000 | 0.0000 |
| artist_oof | hcoef14_shrink_core_risk_keep050 | shrink_hcoef | 0.0004 | 0.0004 | 0.0058 | 0.2500 | 0.0000 | 0.0000 | 0.0000 |
| row_oof | hcoef14_seg_iqr_cap002_s025 | segment_residual | -0.0003 | -0.0002 | 0.0020 | 0.5000 | 1.0000 | 0.1500 | 0.1500 |
| row_oof | hcoef14_route_basis_disagree_ref_w025 | route_reference | -0.0006 | 0.0000 | 0.0000 | 0.7000 | 0.2500 | 0.0000 | 0.0000 |
| row_oof | hcoef14_route_core_gap_ref_w025 | route_reference | -0.0006 | -0.0000 | 0.0000 | 0.6500 | 0.8000 | 0.0000 | 0.0000 |
| row_oof | hcoef14_route_ppv8_pos_ref_w025 | route_reference | 0.0000 | -0.0001 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 |
| row_oof | hcoef14_route_ppv8_pos_ref_w050 | route_reference | 0.0000 | -0.0003 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 |
| row_oof | hcoef14_seg_gap_cap002_s025 | segment_residual | -0.0002 | -0.0002 | 0.0000 | 0.4000 | 1.0000 | 0.0000 | 0.0000 |
| row_oof | hcoef14_seg_n1019_cap002_s025 | segment_residual | -0.0004 | -0.0004 | 0.0000 | 0.6000 | 1.0000 | 0.0000 | 0.0000 |
| row_oof | hcoef14_seg_n1019_cap002_s050 | segment_residual | -0.0009 | -0.0008 | 0.0000 | 0.8500 | 1.0000 | 0.0000 | 0.0000 |
| row_oof | hcoef14_seg_pred_basis_cap002_s025 | segment_residual | 0.0001 | -0.0000 | 0.0000 | 0.0000 | 0.5500 | 0.0000 | 0.0000 |
| row_oof | hcoef14_seg_size_basis_cap002_s025 | segment_residual | -0.0004 | -0.0004 | 0.0000 | 0.6000 | 1.0000 | 0.0000 | 0.0000 |
| row_oof | hcoef14_shrink_n1019_keep050 | shrink_hcoef | 0.0002 | 0.0002 | 0.0000 | 0.3000 | 0.0000 | 0.0000 | 0.0000 |
| row_oof | hcoef14_shrink_n1019_keep075 | shrink_hcoef | -0.0004 | 0.0001 | 0.0000 | 0.6000 | 0.0000 | 0.0000 | 0.0000 |
| row_oof | hcoef2_size_reliability_cap005_s050 | stable_oof_anchor | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| row_oof | hcoef14_route_basis_disagree_ref_w050 | route_reference | -0.0009 | 0.0000 | 0.0006 | 0.8500 | 0.2500 | 0.0000 | 0.0000 |
| row_oof | hcoef14_route_core_gap_ref_w050 | route_reference | -0.0008 | -0.0001 | 0.0006 | 0.8000 | 0.7500 | 0.0000 | 0.0000 |
| row_oof | hcoef14_seg_core_risk_cap002_s025 | segment_residual | 0.0003 | -0.0001 | 0.0042 | 0.1500 | 0.9500 | 0.0000 | 0.0000 |
| row_oof | hcoef14_seg_core_risk_cap003_s025 | segment_residual | 0.0006 | -0.0002 | 0.0050 | 0.1500 | 0.9500 | 0.0000 | 0.0000 |
| row_oof | hcoef14_shrink_iqr_mid_high_keep075 | shrink_hcoef | 0.0002 | 0.0002 | 0.0052 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| row_oof | hcoef14_route_artist_overall_ref_w025 | route_reference | 0.0008 | 0.0003 | 0.0053 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| row_oof | hcoef14_shrink_core_risk_keep075 | shrink_hcoef | 0.0003 | 0.0002 | 0.0053 | 0.3000 | 0.0000 | 0.0000 | 0.0000 |
| row_oof | hcoef14_route_artist_overall_ref_w050 | route_reference | 0.0006 | 0.0007 | 0.0077 | 0.1500 | 0.0000 | 0.0000 | 0.0000 |
| row_oof | hcoef14_shrink_core_risk_keep050 | shrink_hcoef | 0.0006 | 0.0004 | 0.0077 | 0.2000 | 0.0000 | 0.0000 | 0.0000 |
| row_oof | hcoef14_shrink_iqr_mid_high_keep050 | shrink_hcoef | 0.0004 | 0.0004 | 0.0078 | 0.0500 | 0.0000 | 0.0000 | 0.0000 |

## 4. Fixed test p95 상위 후보

| candidate | method | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable | improve_count_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef14_shrink_iqr_mid_high_keep050 | shrink_hcoef | 0.1384 | 0.2731 | 0.8047 | 0.3986 | -0.0004 | 0.0001 | -0.0017 | 2 |
| hcoef14_seg_core_risk_cap003_s025 | segment_residual | 0.1389 | 0.2728 | 0.8055 | 0.3986 | 0.0001 | -0.0002 | -0.0009 | 2 |
| hcoef14_shrink_iqr_mid_high_keep075 | shrink_hcoef | 0.1387 | 0.2730 | 0.8055 | 0.3987 | -0.0001 | 0.0000 | -0.0008 | 2 |
| hcoef14_seg_core_risk_cap002_s025 | segment_residual | 0.1389 | 0.2729 | 0.8057 | 0.3987 | 0.0001 | -0.0001 | -0.0007 | 2 |
| hcoef14_seg_iqr_cap002_s025 | segment_residual | 0.1388 | 0.2729 | 0.8062 | 0.3987 | 0.0000 | -0.0001 | -0.0001 | 2 |
| hcoef14_seg_pred_basis_cap002_s025 | segment_residual | 0.1388 | 0.2729 | 0.8064 | 0.3988 | 0.0000 | -0.0001 | 0.0000 | 1 |
| hcoef2_size_reliability_cap005_s050 | stable_huber_residual | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0 |
| hcoef14_shrink_n1019_keep075 | shrink_hcoef | 0.1389 | 0.2731 | 0.8064 | 0.3988 | 0.0001 | 0.0001 | 0.0000 | 0 |
| hcoef14_shrink_n1019_keep050 | shrink_hcoef | 0.1395 | 0.2732 | 0.8064 | 0.3989 | 0.0007 | 0.0002 | 0.0000 | 0 |
| hcoef14_seg_n1019_cap002_s025 | segment_residual | 0.1389 | 0.2728 | 0.8065 | 0.3988 | 0.0001 | -0.0002 | 0.0001 | 1 |
| hcoef14_seg_size_basis_cap002_s025 | segment_residual | 0.1389 | 0.2731 | 0.8065 | 0.3989 | 0.0001 | 0.0001 | 0.0001 | 0 |
| hcoef14_route_artist_overall_ref_w025 | route_reference | 0.1387 | 0.2729 | 0.8066 | 0.3987 | -0.0001 | -0.0000 | 0.0003 | 2 |
| hcoef14_seg_n1019_cap002_s050 | segment_residual | 0.1404 | 0.2726 | 0.8068 | 0.3987 | 0.0016 | -0.0004 | 0.0004 | 1 |
| hcoef14_route_basis_disagree_ref_w025 | route_reference | 0.1389 | 0.2730 | 0.8075 | 0.3989 | 0.0001 | 0.0000 | 0.0011 | 0 |
| hcoef14_route_artist_overall_ref_w050 | route_reference | 0.1388 | 0.2729 | 0.8080 | 0.3986 | 0.0000 | -0.0001 | 0.0017 | 1 |
| hcoef14_route_basis_disagree_ref_w050 | route_reference | 0.1395 | 0.2731 | 0.8087 | 0.3990 | 0.0007 | 0.0001 | 0.0024 | 0 |
| hcoef14_seg_gap_cap002_s025 | segment_residual | 0.1388 | 0.2731 | 0.8094 | 0.3989 | 0.0000 | 0.0001 | 0.0030 | 0 |
| hcoef14_shrink_core_risk_keep075 | shrink_hcoef | 0.1387 | 0.2730 | 0.8097 | 0.3987 | -0.0001 | 0.0000 | 0.0034 | 1 |
| hcoef14_route_ppv8_pos_ref_w025 | route_reference | 0.1388 | 0.2730 | 0.8101 | 0.3988 | 0.0000 | -0.0000 | 0.0037 | 1 |
| hcoef14_route_core_gap_ref_w025 | route_reference | 0.1389 | 0.2731 | 0.8101 | 0.3989 | 0.0001 | 0.0001 | 0.0037 | 0 |
| hcoef14_route_ppv8_pos_ref_w050 | route_reference | 0.1388 | 0.2730 | 0.8169 | 0.3988 | 0.0000 | -0.0000 | 0.0105 | 1 |
| hcoef14_shrink_core_risk_keep050 | shrink_hcoef | 0.1388 | 0.2731 | 0.8169 | 0.3987 | 0.0000 | 0.0001 | 0.0106 | 0 |
| hcoef14_route_core_gap_ref_w050 | route_reference | 0.1395 | 0.2731 | 0.8169 | 0.3990 | 0.0007 | 0.0002 | 0.0106 | 0 |
| current_70_30 | reference_70_30 | 0.1405 | 0.2748 | 0.8331 | 0.3996 | 0.0017 | 0.0018 | 0.0267 | 0 |

## 5. 보정 적용 규모

| candidate | method | risk_mask | split | applications | map_rows | mean_correction_log | max_abs_correction_log |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef14_route_artist_overall_ref_w025 | route_reference | artist_overall | 0604_ex50 | 261 | 1 | nan | nan |
| hcoef14_route_artist_overall_ref_w025 | route_reference | artist_overall | test | 174 | 1 | nan | nan |
| hcoef14_route_artist_overall_ref_w025 | route_reference | artist_overall | validation | 149 | 1 | nan | nan |
| hcoef14_route_artist_overall_ref_w025 | route_reference | artist_overall | validation_oof | 5960 | 200 | nan | nan |
| hcoef14_route_artist_overall_ref_w050 | route_reference | artist_overall | 0604_ex50 | 261 | 1 | nan | nan |
| hcoef14_route_artist_overall_ref_w050 | route_reference | artist_overall | test | 174 | 1 | nan | nan |
| hcoef14_route_artist_overall_ref_w050 | route_reference | artist_overall | validation | 149 | 1 | nan | nan |
| hcoef14_route_artist_overall_ref_w050 | route_reference | artist_overall | validation_oof | 5960 | 200 | nan | nan |
| hcoef14_route_basis_disagree_ref_w025 | route_reference | basis_disagreement | 0604_ex50 | 167 | 1 | nan | nan |
| hcoef14_route_basis_disagree_ref_w025 | route_reference | basis_disagreement | test | 101 | 1 | nan | nan |
| hcoef14_route_basis_disagree_ref_w025 | route_reference | basis_disagreement | validation | 92 | 1 | nan | nan |
| hcoef14_route_basis_disagree_ref_w025 | route_reference | basis_disagreement | validation_oof | 3680 | 200 | nan | nan |
| hcoef14_route_basis_disagree_ref_w050 | route_reference | basis_disagreement | 0604_ex50 | 167 | 1 | nan | nan |
| hcoef14_route_basis_disagree_ref_w050 | route_reference | basis_disagreement | test | 101 | 1 | nan | nan |
| hcoef14_route_basis_disagree_ref_w050 | route_reference | basis_disagreement | validation | 92 | 1 | nan | nan |
| hcoef14_route_basis_disagree_ref_w050 | route_reference | basis_disagreement | validation_oof | 3680 | 200 | nan | nan |
| hcoef14_route_core_gap_ref_w025 | route_reference | core_gap_risk | 0604_ex50 | 252 | 1 | nan | nan |
| hcoef14_route_core_gap_ref_w025 | route_reference | core_gap_risk | test | 124 | 1 | nan | nan |
| hcoef14_route_core_gap_ref_w025 | route_reference | core_gap_risk | validation | 110 | 1 | nan | nan |
| hcoef14_route_core_gap_ref_w025 | route_reference | core_gap_risk | validation_oof | 4400 | 200 | nan | nan |
| hcoef14_route_core_gap_ref_w050 | route_reference | core_gap_risk | 0604_ex50 | 252 | 1 | nan | nan |
| hcoef14_route_core_gap_ref_w050 | route_reference | core_gap_risk | test | 124 | 1 | nan | nan |
| hcoef14_route_core_gap_ref_w050 | route_reference | core_gap_risk | validation | 110 | 1 | nan | nan |
| hcoef14_route_core_gap_ref_w050 | route_reference | core_gap_risk | validation_oof | 4400 | 200 | nan | nan |
| hcoef14_route_ppv8_pos_ref_w025 | route_reference | ppv8_pos | 0604_ex50 | 107 | 1 | nan | nan |
| hcoef14_route_ppv8_pos_ref_w025 | route_reference | ppv8_pos | test | 39 | 1 | nan | nan |
| hcoef14_route_ppv8_pos_ref_w025 | route_reference | ppv8_pos | validation | 24 | 1 | nan | nan |
| hcoef14_route_ppv8_pos_ref_w025 | route_reference | ppv8_pos | validation_oof | 960 | 200 | nan | nan |
| hcoef14_route_ppv8_pos_ref_w050 | route_reference | ppv8_pos | 0604_ex50 | 107 | 1 | nan | nan |
| hcoef14_route_ppv8_pos_ref_w050 | route_reference | ppv8_pos | test | 39 | 1 | nan | nan |
| hcoef14_route_ppv8_pos_ref_w050 | route_reference | ppv8_pos | validation | 24 | 1 | nan | nan |
| hcoef14_route_ppv8_pos_ref_w050 | route_reference | ppv8_pos | validation_oof | 960 | 200 | nan | nan |
| hcoef14_seg_core_risk_cap002_s025 | segment_residual | core_risk | 0604_ex50 | 371 | 3 | 0.0006 | 0.0050 |
| hcoef14_seg_core_risk_cap002_s025 | segment_residual | core_risk | test | 230 | 3 | 0.0006 | 0.0050 |
| hcoef14_seg_core_risk_cap002_s025 | segment_residual | core_risk | validation | 201 | 3 | 0.0006 | 0.0050 |
| hcoef14_seg_core_risk_cap002_s025 | segment_residual | core_risk | validation_oof | 8016 | 600 | 0.0002 | 0.0050 |
| hcoef14_seg_core_risk_cap003_s025 | segment_residual | core_risk | 0604_ex50 | 371 | 3 | 0.0003 | 0.0075 |
| hcoef14_seg_core_risk_cap003_s025 | segment_residual | core_risk | test | 230 | 3 | 0.0003 | 0.0075 |
| hcoef14_seg_core_risk_cap003_s025 | segment_residual | core_risk | validation | 201 | 3 | 0.0003 | 0.0075 |
| hcoef14_seg_core_risk_cap003_s025 | segment_residual | core_risk | validation_oof | 8016 | 600 | 0.0000 | 0.0075 |

## 6. Huber 계수/정책 해석

- 기존 Huber 잔차 보정 계수와 HCOEF14 정책 파라미터를 함께 기록한다.
- route 후보는 위험 구간에서 현재 후보를 70:30 기준으로 일부 되돌리는 방식이다.
- shrink 후보는 위험 구간에서 Huber 잔차 보정폭만 줄이는 방식이다.
- segment residual 후보는 validation train fold에서 같은 위험 구간의 residual 중앙값만 아주 작게 반영한다.
| candidate | method | feature | coefficient_on_scaled_feature | abs_coefficient | direction | route_weight | keep_weight | cap | strength | min_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef2_size_reliability_cap005_s050 | stable_huber_residual | ppv8_defensive | 0.1081 | 0.1081 | 가격 보정값을 올리는 방향 | nan | nan | nan | nan | nan |
| hcoef2_size_reliability_cap005_s050 | stable_huber_residual | svc_fallback | -0.4718 | 0.4718 | 가격 보정값을 낮추는 방향 | nan | nan | nan | nan | nan |
| hcoef2_size_reliability_cap005_s050 | stable_huber_residual | shrunk_huber_refit | 0.0877 | 0.0877 | 가격 보정값을 올리는 방향 | nan | nan | nan | nan | nan |
| hcoef2_size_reliability_cap005_s050 | stable_huber_residual | shrunk_svc_prior | 0.2221 | 0.2221 | 가격 보정값을 올리는 방향 | nan | nan | nan | nan | nan |
| hcoef2_size_reliability_cap005_s050 | stable_huber_residual | log_area | 0.0570 | 0.0570 | 가격 보정값을 올리는 방향 | nan | nan | nan | nan | nan |
| hcoef2_size_reliability_cap005_s050 | stable_huber_residual | svc_group_n_log | -0.0121 | 0.0121 | 가격 보정값을 낮추는 방향 | nan | nan | nan | nan | nan |
| hcoef2_size_reliability_cap005_s050 | stable_huber_residual | svc_prior_iqr | 0.0008 | 0.0008 | 가격 보정값을 올리는 방향 | nan | nan | nan | nan | nan |
| hcoef2_size_reliability_cap005_s050 | stable_huber_residual | current_ppv8_gap | 0.0491 | 0.0491 | 가격 보정값을 올리는 방향 | nan | nan | nan | nan | nan |
| hcoef2_size_reliability_cap005_s050 | stable_huber_residual | current_shrunk_huber_gap | 0.1308 | 0.1308 | 가격 보정값을 올리는 방향 | nan | nan | nan | nan | nan |
| hcoef2_size_reliability_cap005_s050 | stable_huber_residual | raw_shrunk_prior_gap | -0.0580 | 0.0580 | 가격 보정값을 낮추는 방향 | nan | nan | nan | nan | nan |
| hcoef14_route_ppv8_pos_ref_w025 | route_reference | ppv8_pos | nan | nan | ppv8 gap 양수 구간을 70:30 기준으로 일부 되돌림 | 0.2500 | 1.0000 | 0.0200 | 0.2500 | 20.0000 |
| hcoef14_route_ppv8_pos_ref_w050 | route_reference | ppv8_pos | nan | nan | ppv8 gap 양수 구간을 70:30 기준으로 절반 되돌림 | 0.5000 | 1.0000 | 0.0200 | 0.2500 | 20.0000 |
| hcoef14_route_basis_disagree_ref_w025 | route_reference | basis_disagreement | nan | nan | 기준가와 현재 후보 불일치 구간 보수 routing | 0.2500 | 1.0000 | 0.0200 | 0.2500 | 20.0000 |
| hcoef14_route_basis_disagree_ref_w050 | route_reference | basis_disagreement | nan | nan | 기준가와 현재 후보 불일치 구간 강한 보수 routing | 0.5000 | 1.0000 | 0.0200 | 0.2500 | 20.0000 |
| hcoef14_route_artist_overall_ref_w025 | route_reference | artist_overall | nan | nan | 작가 전체 fallback 구간 일부 보수 routing | 0.2500 | 1.0000 | 0.0200 | 0.2500 | 20.0000 |
| hcoef14_route_artist_overall_ref_w050 | route_reference | artist_overall | nan | nan | 작가 전체 fallback 구간 절반 보수 routing | 0.5000 | 1.0000 | 0.0200 | 0.2500 | 20.0000 |
| hcoef14_route_core_gap_ref_w025 | route_reference | core_gap_risk | nan | nan | 후보 gap 위험 구간 보수 routing | 0.2500 | 1.0000 | 0.0200 | 0.2500 | 20.0000 |
| hcoef14_route_core_gap_ref_w050 | route_reference | core_gap_risk | nan | nan | 후보 gap 위험 구간 강한 보수 routing | 0.5000 | 1.0000 | 0.0200 | 0.2500 | 20.0000 |
| hcoef14_shrink_n1019_keep050 | shrink_hcoef | n_10_19 | nan | nan | 표본 수 10~19 구간 Huber 잔차 보정 절반 축소 | 0.0000 | 0.5000 | 0.0200 | 0.2500 | 20.0000 |
| hcoef14_shrink_n1019_keep075 | shrink_hcoef | n_10_19 | nan | nan | 표본 수 10~19 구간 Huber 잔차 보정 약한 축소 | 0.0000 | 0.7500 | 0.0200 | 0.2500 | 20.0000 |
| hcoef14_shrink_iqr_mid_high_keep050 | shrink_hcoef | iqr_mid_high | nan | nan | IQR 중간/높음 구간 Huber 잔차 보정 절반 축소 | 0.0000 | 0.5000 | 0.0200 | 0.2500 | 20.0000 |
| hcoef14_shrink_iqr_mid_high_keep075 | shrink_hcoef | iqr_mid_high | nan | nan | IQR 중간/높음 구간 Huber 잔차 보정 약한 축소 | 0.0000 | 0.7500 | 0.0200 | 0.2500 | 20.0000 |
| hcoef14_shrink_core_risk_keep050 | shrink_hcoef | core_risk | nan | nan | HCOEF13 핵심 위험 구간 Huber 잔차 보정 절반 축소 | 0.0000 | 0.5000 | 0.0200 | 0.2500 | 20.0000 |
| hcoef14_shrink_core_risk_keep075 | shrink_hcoef | core_risk | nan | nan | HCOEF13 핵심 위험 구간 Huber 잔차 보정 약한 축소 | 0.0000 | 0.7500 | 0.0200 | 0.2500 | 20.0000 |
| hcoef14_seg_n1019_cap002_s025 | segment_residual | basis_n_bucket | nan | nan | 표본 수 10~19 구간 segment median residual 보정 | 0.0000 | 1.0000 | 0.0200 | 0.2500 | 20.0000 |
| hcoef14_seg_n1019_cap002_s050 | segment_residual | basis_n_bucket | nan | nan | 표본 수 10~19 구간 segment median residual 보정 강화 | 0.0000 | 1.0000 | 0.0200 | 0.5000 | 20.0000 |
| hcoef14_seg_iqr_cap002_s025 | segment_residual | basis_iqr_bucket | nan | nan | IQR 위험 구간 segment median residual 보정 | 0.0000 | 1.0000 | 0.0200 | 0.2500 | 20.0000 |
| hcoef14_seg_gap_cap002_s025 | segment_residual | ppv8_gap_sign+basis_gap_sign | nan | nan | 후보 gap 구간 segment median residual 보정 | 0.0000 | 1.0000 | 0.0200 | 0.2500 | 15.0000 |
| hcoef14_seg_pred_basis_cap002_s025 | segment_residual | pred_bin+basis_n_bucket | nan | nan | 예측 가격대 x 표본 수 구간 residual 보정 | 0.0000 | 1.0000 | 0.0200 | 0.2500 | 12.0000 |
| hcoef14_seg_size_basis_cap002_s025 | segment_residual | size_bin+basis_n_bucket | nan | nan | 크기 x 표본 수 구간 residual 보정 | 0.0000 | 1.0000 | 0.0200 | 0.2500 | 12.0000 |
| hcoef14_seg_core_risk_cap002_s025 | segment_residual | risk_cause | nan | nan | HCOEF13 핵심 위험 cause별 residual 보정 | 0.0000 | 1.0000 | 0.0200 | 0.2500 | 20.0000 |
| hcoef14_seg_core_risk_cap003_s025 | segment_residual | risk_cause | nan | nan | HCOEF13 핵심 위험 cause별 residual 보정 cap 확대 | 0.0000 | 1.0000 | 0.0300 | 0.2500 | 20.0000 |

## 7. 잔차/큰 오차 요약

| split | candidate | n | median_residual_log | mean_residual_log | residual_std | ape_median | ape_mean | ape_p95 | ape_gt_50pct_n | ape_gt_100pct_n | over_2x_n | under_half_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_ex50 | current_70_30 | 829 | 0.0782 | 0.3370 | 1.2677 | 0.2779 | 0.3774 | 0.9871 | 237 | 30 | 30 | 153 |
| 0604_ex50 | hcoef14_route_artist_overall_ref_w025 | 829 | 0.0608 | 0.3286 | 1.2662 | 0.2730 | 0.3745 | 0.9849 | 242 | 27 | 27 | 154 |
| 0604_ex50 | hcoef14_route_artist_overall_ref_w050 | 829 | 0.0608 | 0.3295 | 1.2663 | 0.2695 | 0.3747 | 0.9869 | 242 | 27 | 27 | 154 |
| 0604_ex50 | hcoef14_route_basis_disagree_ref_w025 | 829 | 0.0608 | 0.3285 | 1.2662 | 0.2774 | 0.3746 | 0.9835 | 239 | 26 | 26 | 152 |
| 0604_ex50 | hcoef14_route_basis_disagree_ref_w050 | 829 | 0.0608 | 0.3292 | 1.2664 | 0.2745 | 0.3749 | 0.9835 | 239 | 26 | 26 | 152 |
| 0604_ex50 | hcoef14_route_core_gap_ref_w025 | 829 | 0.0608 | 0.3286 | 1.2660 | 0.2774 | 0.3746 | 0.9859 | 239 | 26 | 26 | 152 |
| 0604_ex50 | hcoef14_route_core_gap_ref_w050 | 829 | 0.0608 | 0.3293 | 1.2661 | 0.2745 | 0.3748 | 0.9866 | 239 | 26 | 26 | 152 |
| 0604_ex50 | hcoef14_route_ppv8_pos_ref_w025 | 829 | 0.0608 | 0.3279 | 1.2659 | 0.2734 | 0.3743 | 0.9859 | 240 | 26 | 26 | 152 |
| 0604_ex50 | hcoef14_route_ppv8_pos_ref_w050 | 829 | 0.0608 | 0.3280 | 1.2657 | 0.2734 | 0.3742 | 0.9865 | 240 | 26 | 26 | 152 |
| 0604_ex50 | hcoef14_seg_core_risk_cap002_s025 | 829 | 0.0608 | 0.3278 | 1.2661 | 0.2767 | 0.3743 | 0.9834 | 239 | 26 | 26 | 152 |
| 0604_ex50 | hcoef14_seg_core_risk_cap003_s025 | 829 | 0.0608 | 0.3281 | 1.2661 | 0.2783 | 0.3742 | 0.9834 | 239 | 26 | 26 | 152 |
| 0604_ex50 | hcoef14_seg_gap_cap002_s025 | 829 | 0.0608 | 0.3278 | 1.2660 | 0.2731 | 0.3742 | 0.9835 | 240 | 26 | 26 | 152 |
| 0604_ex50 | hcoef14_seg_iqr_cap002_s025 | 829 | 0.0608 | 0.3281 | 1.2659 | 0.2731 | 0.3741 | 0.9834 | 240 | 26 | 26 | 152 |
| 0604_ex50 | hcoef14_seg_n1019_cap002_s025 | 829 | 0.0608 | 0.3286 | 1.2660 | 0.2731 | 0.3742 | 0.9835 | 240 | 26 | 26 | 153 |
| 0604_ex50 | hcoef14_seg_n1019_cap002_s050 | 829 | 0.0608 | 0.3293 | 1.2660 | 0.2731 | 0.3741 | 0.9835 | 241 | 26 | 26 | 154 |
| 0604_ex50 | hcoef14_seg_pred_basis_cap002_s025 | 829 | 0.0608 | 0.3280 | 1.2660 | 0.2731 | 0.3743 | 0.9835 | 240 | 26 | 26 | 152 |
| 0604_ex50 | hcoef14_seg_size_basis_cap002_s025 | 829 | 0.0608 | 0.3283 | 1.2660 | 0.2731 | 0.3743 | 0.9835 | 240 | 26 | 26 | 153 |
| 0604_ex50 | hcoef14_shrink_core_risk_keep050 | 829 | 0.0608 | 0.3308 | 1.2661 | 0.2744 | 0.3751 | 0.9869 | 241 | 27 | 27 | 154 |
| 0604_ex50 | hcoef14_shrink_core_risk_keep075 | 829 | 0.0608 | 0.3293 | 1.2661 | 0.2730 | 0.3747 | 0.9859 | 241 | 27 | 27 | 154 |
| 0604_ex50 | hcoef14_shrink_iqr_mid_high_keep050 | 829 | 0.0608 | 0.3286 | 1.2661 | 0.2734 | 0.3748 | 0.9833 | 242 | 26 | 26 | 154 |
| 0604_ex50 | hcoef14_shrink_iqr_mid_high_keep075 | 829 | 0.0608 | 0.3282 | 1.2661 | 0.2731 | 0.3745 | 0.9834 | 242 | 26 | 26 | 154 |
| 0604_ex50 | hcoef14_shrink_n1019_keep050 | 829 | 0.0608 | 0.3290 | 1.2661 | 0.2728 | 0.3746 | 0.9834 | 241 | 26 | 26 | 154 |
| 0604_ex50 | hcoef14_shrink_n1019_keep075 | 829 | 0.0608 | 0.3284 | 1.2661 | 0.2731 | 0.3745 | 0.9834 | 241 | 26 | 26 | 154 |
| 0604_ex50 | hcoef2_size_reliability_cap005_s050 | 829 | 0.0608 | 0.3278 | 1.2660 | 0.2731 | 0.3744 | 0.9835 | 240 | 26 | 26 | 152 |
| test | current_70_30 | 607 | -0.0006 | -0.0119 | 0.3994 | 0.1405 | 0.2748 | 0.8331 | 74 | 24 | 24 | 17 |
| test | hcoef14_route_artist_overall_ref_w025 | 607 | -0.0005 | -0.0144 | 0.3985 | 0.1387 | 0.2729 | 0.8066 | 73 | 26 | 26 | 17 |
| test | hcoef14_route_artist_overall_ref_w050 | 607 | -0.0003 | -0.0140 | 0.3984 | 0.1388 | 0.2729 | 0.8080 | 73 | 26 | 26 | 17 |
| test | hcoef14_route_basis_disagree_ref_w025 | 607 | -0.0005 | -0.0145 | 0.3986 | 0.1389 | 0.2730 | 0.8075 | 72 | 26 | 26 | 17 |
| test | hcoef14_route_basis_disagree_ref_w050 | 607 | -0.0005 | -0.0142 | 0.3987 | 0.1395 | 0.2731 | 0.8087 | 72 | 26 | 26 | 17 |
| test | hcoef14_route_core_gap_ref_w025 | 607 | -0.0005 | -0.0144 | 0.3987 | 0.1389 | 0.2731 | 0.8101 | 72 | 26 | 26 | 17 |
| test | hcoef14_route_core_gap_ref_w050 | 607 | -0.0005 | -0.0140 | 0.3988 | 0.1395 | 0.2731 | 0.8169 | 72 | 26 | 26 | 17 |
| test | hcoef14_route_ppv8_pos_ref_w025 | 607 | -0.0039 | -0.0146 | 0.3986 | 0.1388 | 0.2730 | 0.8101 | 72 | 26 | 26 | 17 |
| test | hcoef14_route_ppv8_pos_ref_w050 | 607 | -0.0039 | -0.0143 | 0.3986 | 0.1388 | 0.2730 | 0.8169 | 72 | 26 | 26 | 17 |
| test | hcoef14_seg_core_risk_cap002_s025 | 607 | -0.0005 | -0.0146 | 0.3984 | 0.1389 | 0.2729 | 0.8057 | 72 | 26 | 26 | 17 |
| test | hcoef14_seg_core_risk_cap003_s025 | 607 | -0.0005 | -0.0144 | 0.3984 | 0.1389 | 0.2728 | 0.8055 | 72 | 26 | 26 | 17 |
| test | hcoef14_seg_gap_cap002_s025 | 607 | -0.0039 | -0.0148 | 0.3986 | 0.1388 | 0.2731 | 0.8094 | 72 | 26 | 26 | 17 |
| test | hcoef14_seg_iqr_cap002_s025 | 607 | -0.0041 | -0.0146 | 0.3984 | 0.1388 | 0.2729 | 0.8062 | 72 | 26 | 26 | 17 |
| test | hcoef14_seg_n1019_cap002_s025 | 607 | -0.0015 | -0.0139 | 0.3985 | 0.1389 | 0.2728 | 0.8065 | 72 | 26 | 26 | 17 |
| test | hcoef14_seg_n1019_cap002_s050 | 607 | 0.0008 | -0.0129 | 0.3985 | 0.1404 | 0.2726 | 0.8068 | 72 | 26 | 26 | 17 |
| test | hcoef14_seg_pred_basis_cap002_s025 | 607 | -0.0039 | -0.0147 | 0.3985 | 0.1388 | 0.2729 | 0.8064 | 72 | 26 | 26 | 17 |
| test | hcoef14_seg_size_basis_cap002_s025 | 607 | -0.0015 | -0.0141 | 0.3987 | 0.1389 | 0.2731 | 0.8065 | 72 | 26 | 26 | 17 |
| test | hcoef14_shrink_core_risk_keep050 | 607 | -0.0003 | -0.0138 | 0.3984 | 0.1388 | 0.2731 | 0.8169 | 73 | 26 | 26 | 17 |

## 8. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/residual_analysis.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `outputs/selected_candidates.csv`
- `outputs/segment_application_summary.csv`
- `artifacts/experiment_config.json`