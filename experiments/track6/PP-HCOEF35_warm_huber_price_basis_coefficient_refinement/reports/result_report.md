# PP-HCOEF35 Warm Huber 기준가 잔차 p95 방어 재검증

- 작성일: 2026-06-08 08:09
- 목적: HCOEF34에서 확인된 basis residual Huber 후보의 p95 악화를 막기 위해 cap/strength를 더 작게 탐색.
- 기준 후보: `current_70_30`.
- 안정 비교 후보: `hcoef_stable`.
- 선택 원칙: validation 반복 OOF 우선, fixed test/0604 확인용.

## 1. 실행 결론

- cap/strength를 촘촘하게 낮춰도 hcoef_stable의 fixed p95를 넘기면서 반복 OOF까지 통과하는 후보는 아직 없음.
- HCOEF35는 HCOEF34의 same-feature refinement이므로, 좋은 후보가 있더라도 HCOEF36에서 반복 수 확대 또는 bootstrap 확인 필요.

## 2. 기준 후보 지표

| split | candidate | method | n | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_reference | delta_MAPE_vs_reference | delta_p95_APE_vs_reference | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | current_70_30 | baseline_reference | 519 | 0.1305 | 0.2110 | 0.6580 | 0.3292 | 0.0000 | 0.0000 | 0.0000 | 0.0045 | 0.0028 | 0.0101 |
| validation | hcoef_stable | baseline_stable | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | -0.0045 | -0.0028 | -0.0101 | 0.0000 | 0.0000 | 0.0000 |
| validation | basis_fallback_m5 | basis_component | 519 | 0.2982 | 0.6888 | 3.1786 | 0.7889 | 0.1677 | 0.4777 | 2.5205 | 0.1723 | 0.4806 | 2.5306 |
| validation | basis_shrink_k20 | basis_component | 519 | 0.4400 | 0.7101 | 2.4859 | 0.7813 | 0.3094 | 0.4991 | 1.8278 | 0.3140 | 0.5019 | 1.8379 |
| test | current_70_30 | baseline_reference | 607 | 0.1405 | 0.2748 | 0.8331 | 0.3996 | 0.0000 | 0.0000 | 0.0000 | 0.0017 | 0.0018 | 0.0267 |
| test | hcoef_stable | baseline_stable | 607 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | -0.0017 | -0.0018 | -0.0267 | 0.0000 | 0.0000 | 0.0000 |
| test | basis_fallback_m5 | basis_component | 607 | 0.3115 | 0.7237 | 2.2963 | 0.7818 | 0.1710 | 0.4489 | 1.4632 | 0.1727 | 0.4507 | 1.4899 |
| test | basis_shrink_k20 | basis_component | 607 | 0.4337 | 0.7124 | 2.3046 | 0.7800 | 0.2932 | 0.4376 | 1.4715 | 0.2949 | 0.4394 | 1.4982 |
| 0604_ex50 | current_70_30 | baseline_reference | 829 | 0.2779 | 0.3774 | 0.9871 | 1.3117 | 0.0000 | 0.0000 | 0.0000 | 0.0049 | 0.0030 | 0.0036 |
| 0604_ex50 | hcoef_stable | baseline_stable | 829 | 0.2731 | 0.3744 | 0.9835 | 1.3078 | -0.0049 | -0.0030 | -0.0036 | 0.0000 | 0.0000 | 0.0000 |
| 0604_ex50 | basis_fallback_m5 | basis_component | 829 | 0.4108 | 0.9491 | 4.0140 | 1.0680 | 0.1329 | 0.5717 | 3.0269 | 0.1377 | 0.5747 | 3.0305 |
| 0604_ex50 | basis_shrink_k20 | basis_component | 829 | 0.6129 | 1.0603 | 3.4046 | 1.1127 | 0.3349 | 0.6829 | 2.4175 | 0.3398 | 0.6859 | 2.4211 |

## 3. 후보 선택 판단

| candidate | decision | method | test_MdAPE | test_MAPE | test_p95_APE | fixed_mdape_margin_vs_stable | fixed_mape_margin_vs_stable | fixed_p95_margin_vs_stable | stress0604_MdAPE | stress0604_MAPE | stress0604_p95_APE | row_oof_ref_any2_improve_prob | artist_oof_ref_any2_improve_prob | row_oof_stable_any2_improve_prob | artist_oof_stable_any2_improve_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef35_resid_basis_resid_all_a0p01_cap0p01_s0p35 | 기존 70:30 대비 개선 후보 | residual_huber | 0.1365 | 0.2729 | 0.8078 | -0.0023 | -0.0001 | 0.0014 | 0.2756 | 0.3747 | 0.9837 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p01_s0p35 | 기존 70:30 대비 개선 후보 | residual_huber | 0.1365 | 0.2729 | 0.8078 | -0.0023 | -0.0001 | 0.0014 | 0.2756 | 0.3747 | 0.9837 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p0075_s0p5 | 기존 70:30 대비 개선 후보 | residual_huber | 0.1367 | 0.2729 | 0.8079 | -0.0021 | -0.0001 | 0.0015 | 0.2758 | 0.3747 | 0.9839 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef35_resid_basis_resid_all_a0p01_cap0p0075_s0p5 | 기존 70:30 대비 개선 후보 | residual_huber | 0.1367 | 0.2729 | 0.8079 | -0.0021 | -0.0001 | 0.0015 | 0.2758 | 0.3747 | 0.9839 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p0075_s0p35 | 기존 70:30 대비 개선 후보 | residual_huber | 0.1372 | 0.2729 | 0.8074 | -0.0016 | -0.0001 | 0.0011 | 0.2750 | 0.3746 | 0.9835 | 1.0000 | 1.0000 | 0.9583 | 1.0000 |
| hcoef35_resid_basis_resid_all_a0p01_cap0p0075_s0p35 | 기존 70:30 대비 개선 후보 | residual_huber | 0.1372 | 0.2729 | 0.8074 | -0.0016 | -0.0001 | 0.0011 | 0.2750 | 0.3746 | 0.9835 | 1.0000 | 1.0000 | 0.9583 | 1.0000 |
| hcoef35_resid_basis_resid_core_a0p01_cap0p0075_s0p35 | 기존 70:30 대비 개선 후보 | residual_huber | 0.1372 | 0.2730 | 0.8081 | -0.0016 | 0.0000 | 0.0018 | 0.2747 | 0.3746 | 0.9835 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef35_resid_basis_resid_core_a0p001_cap0p0075_s0p35 | 기존 70:30 대비 개선 후보 | residual_huber | 0.1372 | 0.2730 | 0.8081 | -0.0016 | 0.0000 | 0.0018 | 0.2747 | 0.3746 | 0.9835 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p005_s0p5 | 기존 70:30 대비 개선 후보 | residual_huber | 0.1373 | 0.2729 | 0.8074 | -0.0015 | -0.0001 | 0.0010 | 0.2749 | 0.3746 | 0.9835 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef35_resid_basis_resid_all_a0p01_cap0p005_s0p5 | 기존 70:30 대비 개선 후보 | residual_huber | 0.1373 | 0.2729 | 0.8074 | -0.0015 | -0.0001 | 0.0010 | 0.2749 | 0.3746 | 0.9835 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef35_resid_basis_resid_all_a0p01_cap0p01_s0p25 | 기존 70:30 대비 개선 후보 | residual_huber | 0.1373 | 0.2729 | 0.8074 | -0.0015 | -0.0001 | 0.0010 | 0.2749 | 0.3746 | 0.9835 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p01_s0p25 | 기존 70:30 대비 개선 후보 | residual_huber | 0.1373 | 0.2729 | 0.8074 | -0.0015 | -0.0001 | 0.0010 | 0.2749 | 0.3746 | 0.9835 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef35_resid_basis_resid_core_a0p01_cap0p005_s0p5 | 기존 70:30 대비 개선 후보 | residual_huber | 0.1373 | 0.2730 | 0.8081 | -0.0015 | 0.0000 | 0.0017 | 0.2746 | 0.3746 | 0.9835 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef35_resid_basis_resid_core_a0p001_cap0p005_s0p5 | 기존 70:30 대비 개선 후보 | residual_huber | 0.1373 | 0.2730 | 0.8081 | -0.0015 | 0.0000 | 0.0017 | 0.2746 | 0.3746 | 0.9835 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef35_resid_basis_resid_core_a0p001_cap0p01_s0p25 | 기존 70:30 대비 개선 후보 | residual_huber | 0.1373 | 0.2730 | 0.8081 | -0.0015 | 0.0000 | 0.0017 | 0.2746 | 0.3745 | 0.9835 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

## 4. Fixed test 상위 후보

| candidate | method | MdAPE | MAPE | p95_APE | RMSE_log | improve_count_vs_reference | improve_count_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef35_resid_basis_resid_all_a0p01_cap0p01_s0p35 | residual_huber | 0.1365 | 0.2729 | 0.8078 | 0.3986 | 3 | 2 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p01_s0p35 | residual_huber | 0.1365 | 0.2729 | 0.8078 | 0.3986 | 3 | 2 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p0075_s0p5 | residual_huber | 0.1367 | 0.2729 | 0.8079 | 0.3986 | 3 | 2 |
| hcoef35_resid_basis_resid_all_a0p01_cap0p0075_s0p5 | residual_huber | 0.1367 | 0.2729 | 0.8079 | 0.3986 | 3 | 2 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p0075_s0p35 | residual_huber | 0.1372 | 0.2729 | 0.8074 | 0.3987 | 3 | 2 |
| hcoef35_resid_basis_resid_all_a0p01_cap0p0075_s0p35 | residual_huber | 0.1372 | 0.2729 | 0.8074 | 0.3987 | 3 | 2 |
| hcoef35_resid_basis_resid_core_a0p01_cap0p0075_s0p35 | residual_huber | 0.1372 | 0.2730 | 0.8081 | 0.3989 | 3 | 1 |
| hcoef35_resid_basis_resid_core_a0p001_cap0p0075_s0p35 | residual_huber | 0.1372 | 0.2730 | 0.8081 | 0.3989 | 3 | 1 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p005_s0p5 | residual_huber | 0.1373 | 0.2729 | 0.8074 | 0.3987 | 3 | 2 |
| hcoef35_resid_basis_resid_all_a0p01_cap0p005_s0p5 | residual_huber | 0.1373 | 0.2729 | 0.8074 | 0.3987 | 3 | 2 |
| hcoef35_resid_basis_resid_all_a0p01_cap0p01_s0p25 | residual_huber | 0.1373 | 0.2729 | 0.8074 | 0.3987 | 3 | 2 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p01_s0p25 | residual_huber | 0.1373 | 0.2729 | 0.8074 | 0.3987 | 3 | 2 |
| hcoef35_resid_basis_resid_core_a0p01_cap0p005_s0p5 | residual_huber | 0.1373 | 0.2730 | 0.8081 | 0.3989 | 3 | 1 |
| hcoef35_resid_basis_resid_core_a0p001_cap0p005_s0p5 | residual_huber | 0.1373 | 0.2730 | 0.8081 | 0.3989 | 3 | 1 |
| hcoef35_resid_basis_resid_core_a0p001_cap0p01_s0p25 | residual_huber | 0.1373 | 0.2730 | 0.8081 | 0.3989 | 3 | 1 |
| hcoef35_resid_basis_resid_core_a0p01_cap0p01_s0p25 | residual_huber | 0.1373 | 0.2730 | 0.8081 | 0.3989 | 3 | 1 |
| hcoef35_resid_basis_resid_all_a0p01_cap0p01_s0p2 | residual_huber | 0.1375 | 0.2729 | 0.8072 | 0.3987 | 3 | 2 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p01_s0p2 | residual_huber | 0.1375 | 0.2729 | 0.8072 | 0.3987 | 3 | 2 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p0075_s0p2 | residual_huber | 0.1375 | 0.2729 | 0.8070 | 0.3987 | 3 | 2 |
| hcoef35_resid_basis_resid_all_a0p01_cap0p0075_s0p2 | residual_huber | 0.1375 | 0.2729 | 0.8070 | 0.3987 | 3 | 2 |

## 5. 반복 OOF 요약

| candidate | validation_scheme | n_repeats | mean_MdAPE | mean_MAPE | mean_p95_APE | mean_delta_MdAPE_vs_reference | mean_delta_MAPE_vs_reference | mean_delta_p95_APE_vs_reference | ref_any2_improve_prob | stable_any2_improve_prob | stable_all3_improve_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef35_resid_basis_resid_core_a0p01_cap0p0075_s0p35 | row_oof | 24 | 0.1244 | 0.2081 | 0.6438 | -0.0062 | -0.0030 | -0.0142 | 1.0000 | 1.0000 | 1.0000 |
| hcoef35_resid_basis_resid_core_a0p001_cap0p0075_s0p35 | row_oof | 24 | 0.1244 | 0.2081 | 0.6438 | -0.0062 | -0.0030 | -0.0142 | 1.0000 | 1.0000 | 1.0000 |
| hcoef35_resid_basis_resid_all_a0p01_cap0p01_s0p2 | row_oof | 24 | 0.1244 | 0.2082 | 0.6450 | -0.0062 | -0.0028 | -0.0130 | 1.0000 | 0.9167 | 0.5000 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p01_s0p2 | row_oof | 24 | 0.1244 | 0.2082 | 0.6450 | -0.0062 | -0.0028 | -0.0130 | 1.0000 | 0.9167 | 0.5000 |
| hcoef35_resid_basis_resid_core_a0p01_cap0p0075_s0p35 | artist_oof | 24 | 0.1244 | 0.2081 | 0.6438 | -0.0061 | -0.0029 | -0.0142 | 1.0000 | 1.0000 | 0.9167 |
| hcoef35_resid_basis_resid_core_a0p001_cap0p0075_s0p35 | artist_oof | 24 | 0.1244 | 0.2081 | 0.6438 | -0.0061 | -0.0029 | -0.0142 | 1.0000 | 1.0000 | 0.9167 |
| hcoef35_resid_basis_resid_core_a0p01_cap0p005_s0p5 | row_oof | 24 | 0.1244 | 0.2081 | 0.6440 | -0.0061 | -0.0030 | -0.0140 | 1.0000 | 1.0000 | 1.0000 |
| hcoef35_resid_basis_resid_core_a0p001_cap0p005_s0p5 | row_oof | 24 | 0.1244 | 0.2081 | 0.6440 | -0.0061 | -0.0030 | -0.0140 | 1.0000 | 1.0000 | 1.0000 |
| hcoef35_resid_basis_resid_all_a0p01_cap0p0075_s0p25 | row_oof | 24 | 0.1244 | 0.2082 | 0.6452 | -0.0061 | -0.0028 | -0.0129 | 1.0000 | 0.9167 | 0.5417 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p0075_s0p25 | row_oof | 24 | 0.1244 | 0.2082 | 0.6452 | -0.0061 | -0.0028 | -0.0129 | 1.0000 | 0.9167 | 0.5417 |
| hcoef35_resid_basis_resid_all_a0p01_cap0p01_s0p2 | artist_oof | 24 | 0.1244 | 0.2082 | 0.6450 | -0.0061 | -0.0028 | -0.0130 | 1.0000 | 0.9583 | 0.3333 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p01_s0p2 | artist_oof | 24 | 0.1244 | 0.2082 | 0.6450 | -0.0061 | -0.0028 | -0.0130 | 1.0000 | 0.9583 | 0.3333 |
| hcoef35_resid_basis_resid_core_a0p01_cap0p005_s0p5 | artist_oof | 24 | 0.1245 | 0.2081 | 0.6440 | -0.0060 | -0.0029 | -0.0140 | 1.0000 | 1.0000 | 0.8333 |
| hcoef35_resid_basis_resid_core_a0p001_cap0p005_s0p5 | artist_oof | 24 | 0.1245 | 0.2081 | 0.6440 | -0.0060 | -0.0029 | -0.0140 | 1.0000 | 1.0000 | 0.8333 |
| hcoef35_resid_basis_resid_core_a0p001_cap0p01_s0p25 | row_oof | 24 | 0.1245 | 0.2081 | 0.6440 | -0.0060 | -0.0030 | -0.0140 | 1.0000 | 1.0000 | 1.0000 |
| hcoef35_resid_basis_resid_core_a0p01_cap0p01_s0p25 | row_oof | 24 | 0.1245 | 0.2081 | 0.6440 | -0.0060 | -0.0030 | -0.0140 | 1.0000 | 1.0000 | 1.0000 |
| hcoef35_resid_basis_resid_all_a0p01_cap0p005_s0p35 | row_oof | 24 | 0.1245 | 0.2082 | 0.6453 | -0.0060 | -0.0028 | -0.0127 | 1.0000 | 0.9167 | 0.5833 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p005_s0p35 | row_oof | 24 | 0.1245 | 0.2082 | 0.6453 | -0.0060 | -0.0028 | -0.0127 | 1.0000 | 0.9167 | 0.5833 |
| hcoef35_resid_basis_resid_all_a0p01_cap0p0075_s0p25 | artist_oof | 24 | 0.1245 | 0.2082 | 0.6452 | -0.0060 | -0.0028 | -0.0128 | 1.0000 | 0.9167 | 0.3333 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p0075_s0p25 | artist_oof | 24 | 0.1245 | 0.2082 | 0.6452 | -0.0060 | -0.0028 | -0.0128 | 1.0000 | 0.9167 | 0.3333 |
| hcoef35_resid_basis_resid_all_a0p01_cap0p0035_s0p5 | row_oof | 24 | 0.1245 | 0.2082 | 0.6453 | -0.0060 | -0.0028 | -0.0127 | 1.0000 | 0.9167 | 0.5000 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p0035_s0p5 | row_oof | 24 | 0.1245 | 0.2082 | 0.6453 | -0.0060 | -0.0028 | -0.0127 | 1.0000 | 0.9167 | 0.5000 |
| hcoef35_resid_basis_resid_core_a0p01_cap0p01_s0p25 | artist_oof | 24 | 0.1245 | 0.2081 | 0.6440 | -0.0060 | -0.0029 | -0.0140 | 1.0000 | 1.0000 | 0.9167 |
| hcoef35_resid_basis_resid_core_a0p001_cap0p01_s0p25 | artist_oof | 24 | 0.1245 | 0.2081 | 0.6440 | -0.0060 | -0.0029 | -0.0140 | 1.0000 | 1.0000 | 0.9167 |
| hcoef35_resid_basis_resid_all_a0p01_cap0p01_s0p25 | artist_oof | 24 | 0.1246 | 0.2082 | 0.6442 | -0.0059 | -0.0028 | -0.0138 | 1.0000 | 1.0000 | 0.4167 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p01_s0p25 | artist_oof | 24 | 0.1246 | 0.2082 | 0.6442 | -0.0059 | -0.0028 | -0.0138 | 1.0000 | 1.0000 | 0.4167 |
| hcoef35_resid_basis_resid_core_a0p001_cap0p0025_s0p5 | row_oof | 24 | 0.1246 | 0.2081 | 0.6461 | -0.0059 | -0.0029 | -0.0120 | 1.0000 | 1.0000 | 1.0000 |
| hcoef35_resid_basis_resid_core_a0p01_cap0p0025_s0p5 | row_oof | 24 | 0.1246 | 0.2081 | 0.6461 | -0.0059 | -0.0029 | -0.0120 | 1.0000 | 1.0000 | 1.0000 |
| hcoef35_resid_basis_resid_core_a0p001_cap0p005_s0p25 | row_oof | 24 | 0.1246 | 0.2081 | 0.6461 | -0.0059 | -0.0029 | -0.0120 | 1.0000 | 1.0000 | 1.0000 |
| hcoef35_resid_basis_resid_core_a0p01_cap0p005_s0p25 | row_oof | 24 | 0.1246 | 0.2081 | 0.6461 | -0.0059 | -0.0029 | -0.0120 | 1.0000 | 1.0000 | 1.0000 |

_상위 30개만 표시. 전체 288개._

## 6. 계수 해석

- 계수는 표준화된 피처 기준. 방향성과 상대 영향 비교용.
| candidate | kind | feature_set | target | feature | coefficient_on_scaled_feature | abs_coefficient | direction | alpha | cap | strength | clip_margin | experiment_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p1 | residual_huber | basis_resid_all | stable_residual_log | basis_artist_overall_m1_gap | -0.0389 | 0.0389 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.1000 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p1 | residual_huber | basis_resid_all | stable_residual_log | basis_artist_medium_support_m5_gap | -0.0257 | 0.0257 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.1000 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p1 | residual_huber | basis_resid_all | stable_residual_log | shrink20_stable_gap | 0.0255 | 0.0255 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 | 0.0010 | 0.1000 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p1 | residual_huber | basis_resid_all | stable_residual_log | basis_component_spread | -0.0236 | 0.0236 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.1000 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p1 | residual_huber | basis_resid_all | stable_residual_log | log_area | -0.0231 | 0.0231 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.1000 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p1 | residual_huber | basis_resid_all | stable_residual_log | basis_artist_size_m5_gap | -0.0188 | 0.0188 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.1000 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p1 | residual_huber | basis_resid_all | stable_residual_log | basis_artist_size_medium_support_m5_gap | -0.0187 | 0.0187 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.1000 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p1 | residual_huber | basis_resid_all | stable_residual_log | basis_fallback_m5_n_log | -0.0175 | 0.0175 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.1000 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p1 | residual_huber | basis_resid_all | stable_residual_log | fallback_stable_gap | 0.0118 | 0.0118 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 | 0.0010 | 0.1000 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p1 | residual_huber | basis_resid_all | stable_residual_log | basis_fallback_m5_iqr | 0.0095 | 0.0095 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 | 0.0010 | 0.1000 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p15 | residual_huber | basis_resid_all | stable_residual_log | basis_artist_overall_m1_gap | -0.0389 | 0.0389 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.1500 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p15 | residual_huber | basis_resid_all | stable_residual_log | basis_artist_medium_support_m5_gap | -0.0257 | 0.0257 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.1500 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p15 | residual_huber | basis_resid_all | stable_residual_log | shrink20_stable_gap | 0.0255 | 0.0255 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 | 0.0010 | 0.1500 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p15 | residual_huber | basis_resid_all | stable_residual_log | basis_component_spread | -0.0236 | 0.0236 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.1500 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p15 | residual_huber | basis_resid_all | stable_residual_log | log_area | -0.0231 | 0.0231 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.1500 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p15 | residual_huber | basis_resid_all | stable_residual_log | basis_artist_size_m5_gap | -0.0188 | 0.0188 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.1500 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p15 | residual_huber | basis_resid_all | stable_residual_log | basis_artist_size_medium_support_m5_gap | -0.0187 | 0.0187 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.1500 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p15 | residual_huber | basis_resid_all | stable_residual_log | basis_fallback_m5_n_log | -0.0175 | 0.0175 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.1500 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p15 | residual_huber | basis_resid_all | stable_residual_log | fallback_stable_gap | 0.0118 | 0.0118 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 | 0.0010 | 0.1500 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p15 | residual_huber | basis_resid_all | stable_residual_log | basis_fallback_m5_iqr | 0.0095 | 0.0095 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 | 0.0010 | 0.1500 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p2 | residual_huber | basis_resid_all | stable_residual_log | basis_artist_overall_m1_gap | -0.0389 | 0.0389 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.2000 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p2 | residual_huber | basis_resid_all | stable_residual_log | basis_artist_medium_support_m5_gap | -0.0257 | 0.0257 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.2000 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p2 | residual_huber | basis_resid_all | stable_residual_log | shrink20_stable_gap | 0.0255 | 0.0255 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 | 0.0010 | 0.2000 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p2 | residual_huber | basis_resid_all | stable_residual_log | basis_component_spread | -0.0236 | 0.0236 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.2000 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p2 | residual_huber | basis_resid_all | stable_residual_log | log_area | -0.0231 | 0.0231 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.2000 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p2 | residual_huber | basis_resid_all | stable_residual_log | basis_artist_size_m5_gap | -0.0188 | 0.0188 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.2000 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p2 | residual_huber | basis_resid_all | stable_residual_log | basis_artist_size_medium_support_m5_gap | -0.0187 | 0.0187 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.2000 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p2 | residual_huber | basis_resid_all | stable_residual_log | basis_fallback_m5_n_log | -0.0175 | 0.0175 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.2000 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p2 | residual_huber | basis_resid_all | stable_residual_log | fallback_stable_gap | 0.0118 | 0.0118 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 | 0.0010 | 0.2000 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p2 | residual_huber | basis_resid_all | stable_residual_log | basis_fallback_m5_iqr | 0.0095 | 0.0095 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 | 0.0010 | 0.2000 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p25 | residual_huber | basis_resid_all | stable_residual_log | basis_artist_overall_m1_gap | -0.0389 | 0.0389 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.2500 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p25 | residual_huber | basis_resid_all | stable_residual_log | basis_artist_medium_support_m5_gap | -0.0257 | 0.0257 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.2500 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p25 | residual_huber | basis_resid_all | stable_residual_log | shrink20_stable_gap | 0.0255 | 0.0255 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 | 0.0010 | 0.2500 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p25 | residual_huber | basis_resid_all | stable_residual_log | basis_component_spread | -0.0236 | 0.0236 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.2500 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p25 | residual_huber | basis_resid_all | stable_residual_log | log_area | -0.0231 | 0.0231 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.2500 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p25 | residual_huber | basis_resid_all | stable_residual_log | basis_artist_size_m5_gap | -0.0188 | 0.0188 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.2500 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p25 | residual_huber | basis_resid_all | stable_residual_log | basis_artist_size_medium_support_m5_gap | -0.0187 | 0.0187 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.2500 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p25 | residual_huber | basis_resid_all | stable_residual_log | basis_fallback_m5_n_log | -0.0175 | 0.0175 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.2500 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p25 | residual_huber | basis_resid_all | stable_residual_log | fallback_stable_gap | 0.0118 | 0.0118 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 | 0.0010 | 0.2500 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p25 | residual_huber | basis_resid_all | stable_residual_log | basis_fallback_m5_iqr | 0.0095 | 0.0095 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 | 0.0010 | 0.2500 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p35 | residual_huber | basis_resid_all | stable_residual_log | basis_artist_overall_m1_gap | -0.0389 | 0.0389 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.3500 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p35 | residual_huber | basis_resid_all | stable_residual_log | basis_artist_medium_support_m5_gap | -0.0257 | 0.0257 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.3500 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p35 | residual_huber | basis_resid_all | stable_residual_log | shrink20_stable_gap | 0.0255 | 0.0255 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 | 0.0010 | 0.3500 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p35 | residual_huber | basis_resid_all | stable_residual_log | basis_component_spread | -0.0236 | 0.0236 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.3500 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p35 | residual_huber | basis_resid_all | stable_residual_log | log_area | -0.0231 | 0.0231 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.3500 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p35 | residual_huber | basis_resid_all | stable_residual_log | basis_artist_size_m5_gap | -0.0188 | 0.0188 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.3500 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p35 | residual_huber | basis_resid_all | stable_residual_log | basis_artist_size_medium_support_m5_gap | -0.0187 | 0.0187 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.3500 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p35 | residual_huber | basis_resid_all | stable_residual_log | basis_fallback_m5_n_log | -0.0175 | 0.0175 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.3500 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p35 | residual_huber | basis_resid_all | stable_residual_log | fallback_stable_gap | 0.0118 | 0.0118 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 | 0.0010 | 0.3500 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p35 | residual_huber | basis_resid_all | stable_residual_log | basis_fallback_m5_iqr | 0.0095 | 0.0095 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 | 0.0010 | 0.3500 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p5 | residual_huber | basis_resid_all | stable_residual_log | basis_artist_overall_m1_gap | -0.0389 | 0.0389 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.5000 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p5 | residual_huber | basis_resid_all | stable_residual_log | basis_artist_medium_support_m5_gap | -0.0257 | 0.0257 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.5000 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p5 | residual_huber | basis_resid_all | stable_residual_log | shrink20_stable_gap | 0.0255 | 0.0255 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 | 0.0010 | 0.5000 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p5 | residual_huber | basis_resid_all | stable_residual_log | basis_component_spread | -0.0236 | 0.0236 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.5000 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p5 | residual_huber | basis_resid_all | stable_residual_log | log_area | -0.0231 | 0.0231 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.5000 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p5 | residual_huber | basis_resid_all | stable_residual_log | basis_artist_size_m5_gap | -0.0188 | 0.0188 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.5000 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p5 | residual_huber | basis_resid_all | stable_residual_log | basis_artist_size_medium_support_m5_gap | -0.0187 | 0.0187 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.5000 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p5 | residual_huber | basis_resid_all | stable_residual_log | basis_fallback_m5_n_log | -0.0175 | 0.0175 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 | 0.0010 | 0.5000 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p5 | residual_huber | basis_resid_all | stable_residual_log | fallback_stable_gap | 0.0118 | 0.0118 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 | 0.0010 | 0.5000 |  | PP-HCOEF35 |
| hcoef35_resid_basis_resid_all_a0p001_cap0p001_s0p5 | residual_huber | basis_resid_all | stable_residual_log | basis_fallback_m5_iqr | 0.0095 | 0.0095 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 | 0.0010 | 0.5000 |  | PP-HCOEF35 |

## 7. 잔차/큰 오차 요약

| split | candidate | n | median_residual_log | mean_residual_log | residual_std | ape_median | ape_mean | ape_p95 | ape_gt_100pct_n | over_2x_n | under_half_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | current_70_30 | 607 | -0.0006 | -0.0120 | 0.3998 | 0.1405 | 0.2748 | 0.8331 | 24 | 24 | 17 |
| test | hcoef_stable | 607 | -0.0039 | -0.0148 | 0.3989 | 0.1388 | 0.2730 | 0.8064 | 26 | 26 | 17 |
| test | basis_fallback_m5 | 607 | 0.0000 | 0.0198 | 0.7822 | 0.3115 | 0.7237 | 2.2963 | 79 | 79 | 78 |
| test | basis_shrink_k20 | 607 | -0.0290 | 0.0075 | 0.7806 | 0.4337 | 0.7124 | 2.3046 | 97 | 97 | 108 |
| 0604_ex50 | current_70_30 | 829 | 0.0782 | 0.3371 | 1.2685 | 0.2779 | 0.3774 | 0.9871 | 30 | 30 | 153 |
| 0604_ex50 | hcoef_stable | 829 | 0.0608 | 0.3278 | 1.2668 | 0.2731 | 0.3744 | 0.9835 | 26 | 26 | 152 |
| 0604_ex50 | basis_fallback_m5 | 829 | 0.0000 | 0.0789 | 1.0657 | 0.4108 | 0.9491 | 4.0140 | 135 | 137 | 166 |
| 0604_ex50 | basis_shrink_k20 | 829 | -0.0181 | 0.0155 | 1.1133 | 0.6129 | 1.0603 | 3.4046 | 195 | 195 | 189 |
| test | hcoef35_resid_basis_resid_all_a0p001_cap0p005_s0p5 | 607 | -0.0030 | -0.0151 | 0.3987 | 0.1373 | 0.2729 | 0.8074 | 26 | 26 | 17 |
| 0604_ex50 | hcoef35_resid_basis_resid_all_a0p001_cap0p005_s0p5 | 829 | 0.0633 | 0.3279 | 1.2670 | 0.2749 | 0.3746 | 0.9835 | 27 | 27 | 152 |
| test | hcoef35_resid_basis_resid_all_a0p001_cap0p0075_s0p35 | 607 | -0.0032 | -0.0151 | 0.3987 | 0.1372 | 0.2729 | 0.8074 | 26 | 26 | 17 |
| 0604_ex50 | hcoef35_resid_basis_resid_all_a0p001_cap0p0075_s0p35 | 829 | 0.0634 | 0.3279 | 1.2670 | 0.2750 | 0.3746 | 0.9835 | 27 | 27 | 152 |
| test | hcoef35_resid_basis_resid_all_a0p001_cap0p0075_s0p5 | 607 | -0.0029 | -0.0152 | 0.3987 | 0.1367 | 0.2729 | 0.8079 | 26 | 26 | 17 |
| 0604_ex50 | hcoef35_resid_basis_resid_all_a0p001_cap0p0075_s0p5 | 829 | 0.0646 | 0.3279 | 1.2671 | 0.2758 | 0.3747 | 0.9839 | 27 | 27 | 152 |
| test | hcoef35_resid_basis_resid_all_a0p001_cap0p01_s0p25 | 607 | -0.0030 | -0.0151 | 0.3987 | 0.1373 | 0.2729 | 0.8074 | 26 | 26 | 17 |
| 0604_ex50 | hcoef35_resid_basis_resid_all_a0p001_cap0p01_s0p25 | 829 | 0.0633 | 0.3279 | 1.2670 | 0.2749 | 0.3746 | 0.9835 | 27 | 27 | 152 |
| test | hcoef35_resid_basis_resid_all_a0p001_cap0p01_s0p35 | 607 | -0.0030 | -0.0152 | 0.3987 | 0.1365 | 0.2729 | 0.8078 | 26 | 26 | 17 |
| 0604_ex50 | hcoef35_resid_basis_resid_all_a0p001_cap0p01_s0p35 | 829 | 0.0643 | 0.3279 | 1.2671 | 0.2756 | 0.3747 | 0.9837 | 27 | 27 | 152 |
| test | hcoef35_resid_basis_resid_all_a0p01_cap0p005_s0p5 | 607 | -0.0030 | -0.0151 | 0.3987 | 0.1373 | 0.2729 | 0.8074 | 26 | 26 | 17 |
| 0604_ex50 | hcoef35_resid_basis_resid_all_a0p01_cap0p005_s0p5 | 829 | 0.0633 | 0.3279 | 1.2670 | 0.2749 | 0.3746 | 0.9835 | 27 | 27 | 152 |
| test | hcoef35_resid_basis_resid_all_a0p01_cap0p0075_s0p35 | 607 | -0.0032 | -0.0151 | 0.3987 | 0.1372 | 0.2729 | 0.8074 | 26 | 26 | 17 |
| 0604_ex50 | hcoef35_resid_basis_resid_all_a0p01_cap0p0075_s0p35 | 829 | 0.0634 | 0.3279 | 1.2670 | 0.2750 | 0.3746 | 0.9835 | 27 | 27 | 152 |
| test | hcoef35_resid_basis_resid_all_a0p01_cap0p0075_s0p5 | 607 | -0.0029 | -0.0152 | 0.3987 | 0.1367 | 0.2729 | 0.8079 | 26 | 26 | 17 |
| 0604_ex50 | hcoef35_resid_basis_resid_all_a0p01_cap0p0075_s0p5 | 829 | 0.0646 | 0.3279 | 1.2671 | 0.2758 | 0.3747 | 0.9839 | 27 | 27 | 152 |
| test | hcoef35_resid_basis_resid_all_a0p01_cap0p01_s0p25 | 607 | -0.0030 | -0.0151 | 0.3987 | 0.1373 | 0.2729 | 0.8074 | 26 | 26 | 17 |
| 0604_ex50 | hcoef35_resid_basis_resid_all_a0p01_cap0p01_s0p25 | 829 | 0.0633 | 0.3279 | 1.2670 | 0.2749 | 0.3746 | 0.9835 | 27 | 27 | 152 |
| test | hcoef35_resid_basis_resid_all_a0p01_cap0p01_s0p35 | 607 | -0.0030 | -0.0152 | 0.3987 | 0.1365 | 0.2729 | 0.8078 | 26 | 26 | 17 |
| 0604_ex50 | hcoef35_resid_basis_resid_all_a0p01_cap0p01_s0p35 | 829 | 0.0643 | 0.3279 | 1.2671 | 0.2756 | 0.3747 | 0.9837 | 27 | 27 | 152 |
| test | hcoef35_resid_basis_resid_core_a0p001_cap0p005_s0p5 | 607 | -0.0017 | -0.0150 | 0.3990 | 0.1373 | 0.2730 | 0.8081 | 26 | 26 | 17 |
| 0604_ex50 | hcoef35_resid_basis_resid_core_a0p001_cap0p005_s0p5 | 829 | 0.0583 | 0.3271 | 1.2671 | 0.2746 | 0.3746 | 0.9835 | 27 | 27 | 152 |
| test | hcoef35_resid_basis_resid_core_a0p001_cap0p0075_s0p35 | 607 | -0.0018 | -0.0151 | 0.3990 | 0.1372 | 0.2730 | 0.8081 | 26 | 26 | 17 |
| 0604_ex50 | hcoef35_resid_basis_resid_core_a0p001_cap0p0075_s0p35 | 829 | 0.0582 | 0.3271 | 1.2671 | 0.2747 | 0.3746 | 0.9835 | 27 | 27 | 152 |
| test | hcoef35_resid_basis_resid_core_a0p001_cap0p01_s0p25 | 607 | -0.0017 | -0.0151 | 0.3989 | 0.1373 | 0.2730 | 0.8081 | 26 | 26 | 17 |
| 0604_ex50 | hcoef35_resid_basis_resid_core_a0p001_cap0p01_s0p25 | 829 | 0.0583 | 0.3272 | 1.2671 | 0.2746 | 0.3745 | 0.9835 | 27 | 27 | 152 |
| test | hcoef35_resid_basis_resid_core_a0p01_cap0p005_s0p5 | 607 | -0.0017 | -0.0150 | 0.3990 | 0.1373 | 0.2730 | 0.8081 | 26 | 26 | 17 |
| 0604_ex50 | hcoef35_resid_basis_resid_core_a0p01_cap0p005_s0p5 | 829 | 0.0583 | 0.3271 | 1.2671 | 0.2746 | 0.3746 | 0.9835 | 27 | 27 | 152 |
| test | hcoef35_resid_basis_resid_core_a0p01_cap0p0075_s0p35 | 607 | -0.0018 | -0.0151 | 0.3990 | 0.1372 | 0.2730 | 0.8081 | 26 | 26 | 17 |
| 0604_ex50 | hcoef35_resid_basis_resid_core_a0p01_cap0p0075_s0p35 | 829 | 0.0582 | 0.3271 | 1.2671 | 0.2747 | 0.3746 | 0.9835 | 27 | 27 | 152 |

## 8. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/residual_analysis.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `outputs/selected_candidates.csv`
- `artifacts/experiment_config.json`