# PP-HCOEF34 Warm Huber 기준가 생성/계수 조정 실험

- 작성일: 2026-06-08 08:02
- 목적: 유사 작품 기반 가격 피처를 여러 방식으로 다시 만들고, Huber가 기준가와 신뢰도 피처의 계수를 안정적으로 학습하는지 확인.
- 기준 후보: `current_70_30` = 유사 작품 기반 가격 피처 70% + 오차 안정화 후보 30%.
- 안정 비교 후보: `hcoef_stable` = 기존 70:30 위에 작은 Huber 잔차 보정을 더한 현재 안정 후보.
- 선택 원칙: validation 반복 OOF로 후보를 먼저 고르고 fixed test/0604는 확인용으로만 사용.

## 1. 실행 결론

- 새 기준가 생성 방식은 기존 70:30 대비 개선 후보는 만들 수 있지만, 현재 hcoef_stable을 반복 검증과 fixed p95 기준에서 명확히 넘는 운영 후보는 아직 없음.
- HCOEF34는 기준가 자체를 바꾸는 broad screening 실험이므로, 좋은 후보가 있더라도 HCOEF35에서 반복 수를 늘려 재검증해야 함.

## 2. 생성한 기준가 방식

- `basis_artist_overall_m1`: 작가 전체 과거 거래 중앙값. 같은 작가의 전반적 가격 기준선.
- `basis_artist_size_m5`: 작가+크기 구간 중앙값. 크기별 가격 차이를 반영하되 표본 5개 미만은 global로 완화.
- `basis_artist_medium_support_m5`: 작가+재료/지지체 중앙값. 재료와 지지체에 따른 가격 차이를 반영.
- `basis_artist_size_medium_support_m5`: 작가+크기+재료/지지체 중앙값. 가장 세밀하지만 표본 부족 위험이 큼.
- `basis_fallback_m5/m10`: 세밀한 기준부터 찾고 표본이 부족하면 상위 기준으로 이동하는 fallback 기준가.
- `basis_shrink_k*`: 표본 수가 적을수록 작가 전체/전역 기준으로 부드럽게 당기는 shrink 기준가.

## 3. 기준가 fallback 분포

| split | n | fallback_global_pct | fallback_artist_pct | fallback_artist_size_pct | fallback_artist_medium_support_pct | fallback_artist_size_medium_support_pct | median_fallback_n | median_fallback_iqr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | 519 | 0.0000 | 13.8728 | 6.9364 | 40.0771 | 39.1137 | 8.0000 | 0.4463 |
| test | 607 | 0.0000 | 19.6046 | 6.9193 | 32.4547 | 41.0214 | 8.0000 | 0.4403 |
| 0604_ex50 | 829 | 12.3040 | 30.5187 | 25.6936 | 19.9035 | 11.5802 | 7.0000 | 0.6355 |

## 4. 기준 후보와 기준가 컴포넌트 고정 지표

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

## 5. 후보 선택 판단

| candidate | decision | method | test_MdAPE | test_MAPE | test_p95_APE | stress0604_MdAPE | stress0604_MAPE | stress0604_p95_APE | row_oof_ref_any2_improve_prob | artist_oof_ref_any2_improve_prob | row_oof_stable_any2_improve_prob | artist_oof_stable_any2_improve_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef34_resid_basis_resid_all_a0p001_cap0p005_s0p5 | 기존 70:30 대비 개선 후보 | residual_huber | 0.1373 | 0.2729 | 0.8074 | 0.2749 | 0.3746 | 0.9835 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef34_resid_basis_resid_all_a0p01_cap0p005_s0p5 | 기존 70:30 대비 개선 후보 | residual_huber | 0.1373 | 0.2729 | 0.8074 | 0.2749 | 0.3746 | 0.9835 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef34_resid_basis_resid_all_a0p01_cap0p01_s0p25 | 기존 70:30 대비 개선 후보 | residual_huber | 0.1373 | 0.2729 | 0.8074 | 0.2749 | 0.3746 | 0.9835 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef34_resid_basis_resid_all_a0p001_cap0p01_s0p25 | 기존 70:30 대비 개선 후보 | residual_huber | 0.1373 | 0.2729 | 0.8074 | 0.2749 | 0.3746 | 0.9835 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef34_resid_basis_resid_core_a0p01_cap0p005_s0p5 | 기존 70:30 대비 개선 후보 | residual_huber | 0.1373 | 0.2730 | 0.8081 | 0.2746 | 0.3746 | 0.9835 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef34_resid_basis_resid_core_a0p001_cap0p005_s0p5 | 기존 70:30 대비 개선 후보 | residual_huber | 0.1373 | 0.2730 | 0.8081 | 0.2746 | 0.3746 | 0.9835 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef34_resid_basis_resid_core_a0p001_cap0p01_s0p25 | 기존 70:30 대비 개선 후보 | residual_huber | 0.1373 | 0.2730 | 0.8081 | 0.2746 | 0.3746 | 0.9835 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef34_resid_basis_resid_core_a0p01_cap0p01_s0p25 | 기존 70:30 대비 개선 후보 | residual_huber | 0.1373 | 0.2730 | 0.8081 | 0.2746 | 0.3746 | 0.9835 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef34_resid_basis_resid_all_a0p01_cap0p02_s0p25 | 기존 70:30 대비 개선 후보 | residual_huber | 0.1375 | 0.2729 | 0.8094 | 0.2767 | 0.3749 | 0.9849 | 1.0000 | 1.0000 | 0.6667 | 0.6667 |
| hcoef34_resid_basis_resid_all_a0p001_cap0p02_s0p25 | 기존 70:30 대비 개선 후보 | residual_huber | 0.1375 | 0.2729 | 0.8094 | 0.2767 | 0.3749 | 0.9849 | 1.0000 | 1.0000 | 0.6667 | 0.6667 |
| hcoef34_resid_basis_resid_all_a0p001_cap0p005_s0p25 | 기존 70:30 대비 개선 후보 | residual_huber | 0.1377 | 0.2729 | 0.8069 | 0.2740 | 0.3745 | 0.9835 | 1.0000 | 1.0000 | 0.8333 | 1.0000 |
| hcoef34_resid_basis_resid_all_a0p01_cap0p005_s0p25 | 기존 70:30 대비 개선 후보 | residual_huber | 0.1377 | 0.2729 | 0.8069 | 0.2740 | 0.3745 | 0.9835 | 1.0000 | 1.0000 | 0.8333 | 1.0000 |

## 6. Fixed test 상위 후보

| candidate | method | MdAPE | MAPE | p95_APE | RMSE_log | improve_count_vs_reference | improve_count_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef34_resid_basis_resid_all_a0p001_cap0p005_s0p5 | residual_huber | 0.1373 | 0.2729 | 0.8074 | 0.3987 | 3 | 2 |
| hcoef34_resid_basis_resid_all_a0p01_cap0p005_s0p5 | residual_huber | 0.1373 | 0.2729 | 0.8074 | 0.3987 | 3 | 2 |
| hcoef34_resid_basis_resid_all_a0p01_cap0p01_s0p25 | residual_huber | 0.1373 | 0.2729 | 0.8074 | 0.3987 | 3 | 2 |
| hcoef34_resid_basis_resid_all_a0p001_cap0p01_s0p25 | residual_huber | 0.1373 | 0.2729 | 0.8074 | 0.3987 | 3 | 2 |
| hcoef34_resid_basis_resid_core_a0p01_cap0p005_s0p5 | residual_huber | 0.1373 | 0.2730 | 0.8081 | 0.3989 | 3 | 1 |
| hcoef34_resid_basis_resid_core_a0p001_cap0p005_s0p5 | residual_huber | 0.1373 | 0.2730 | 0.8081 | 0.3989 | 3 | 1 |
| hcoef34_resid_basis_resid_core_a0p001_cap0p01_s0p25 | residual_huber | 0.1373 | 0.2730 | 0.8081 | 0.3989 | 3 | 1 |
| hcoef34_resid_basis_resid_core_a0p01_cap0p01_s0p25 | residual_huber | 0.1373 | 0.2730 | 0.8081 | 0.3989 | 3 | 1 |
| hcoef34_resid_basis_resid_all_a0p01_cap0p02_s0p25 | residual_huber | 0.1375 | 0.2729 | 0.8094 | 0.3986 | 3 | 2 |
| hcoef34_resid_basis_resid_all_a0p001_cap0p02_s0p25 | residual_huber | 0.1375 | 0.2729 | 0.8094 | 0.3986 | 3 | 2 |
| hcoef34_resid_basis_resid_all_a0p001_cap0p005_s0p25 | residual_huber | 0.1377 | 0.2729 | 0.8069 | 0.3987 | 3 | 2 |
| hcoef34_resid_basis_resid_all_a0p01_cap0p005_s0p25 | residual_huber | 0.1377 | 0.2729 | 0.8069 | 0.3987 | 3 | 2 |
| hcoef34_resid_basis_resid_core_a0p01_cap0p005_s0p25 | residual_huber | 0.1377 | 0.2730 | 0.8072 | 0.3989 | 3 | 1 |
| hcoef34_resid_basis_resid_core_a0p001_cap0p005_s0p25 | residual_huber | 0.1377 | 0.2730 | 0.8072 | 0.3989 | 3 | 1 |
| hcoef34_resid_basis_resid_all_a0p01_cap0p01_s0p5 | residual_huber | 0.1378 | 0.2729 | 0.8094 | 0.3986 | 3 | 2 |

## 7. 반복 OOF 요약

| candidate | validation_scheme | n_repeats | mean_MdAPE | mean_MAPE | mean_p95_APE | mean_delta_MdAPE_vs_reference | mean_delta_MAPE_vs_reference | mean_delta_p95_APE_vs_reference | ref_any2_improve_prob | stable_any2_improve_prob | stable_all3_improve_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef34_resid_basis_resid_core_a0p001_cap0p005_s0p5 | artist_oof | 12 | 0.1244 | 0.2081 | 0.6440 | -0.0061 | -0.0029 | -0.0140 | 1.0000 | 1.0000 | 0.7500 |
| hcoef34_resid_basis_resid_core_a0p01_cap0p005_s0p5 | artist_oof | 12 | 0.1244 | 0.2081 | 0.6440 | -0.0061 | -0.0029 | -0.0140 | 1.0000 | 1.0000 | 0.7500 |
| hcoef34_resid_basis_resid_core_a0p001_cap0p005_s0p5 | row_oof | 12 | 0.1245 | 0.2081 | 0.6440 | -0.0061 | -0.0030 | -0.0140 | 1.0000 | 1.0000 | 1.0000 |
| hcoef34_resid_basis_resid_core_a0p001_cap0p01_s0p25 | row_oof | 12 | 0.1245 | 0.2081 | 0.6440 | -0.0061 | -0.0030 | -0.0140 | 1.0000 | 1.0000 | 1.0000 |
| hcoef34_resid_basis_resid_core_a0p01_cap0p005_s0p5 | row_oof | 12 | 0.1245 | 0.2081 | 0.6440 | -0.0061 | -0.0030 | -0.0140 | 1.0000 | 1.0000 | 1.0000 |
| hcoef34_resid_basis_resid_core_a0p01_cap0p01_s0p25 | row_oof | 12 | 0.1245 | 0.2081 | 0.6440 | -0.0061 | -0.0030 | -0.0140 | 1.0000 | 1.0000 | 1.0000 |
| hcoef34_resid_basis_resid_core_a0p01_cap0p01_s0p25 | artist_oof | 12 | 0.1245 | 0.2081 | 0.6440 | -0.0061 | -0.0029 | -0.0140 | 1.0000 | 1.0000 | 0.9167 |
| hcoef34_resid_basis_resid_core_a0p001_cap0p01_s0p25 | artist_oof | 12 | 0.1245 | 0.2081 | 0.6440 | -0.0061 | -0.0029 | -0.0140 | 1.0000 | 1.0000 | 0.9167 |
| hcoef34_resid_basis_resid_core_a0p001_cap0p005_s0p25 | row_oof | 12 | 0.1246 | 0.2081 | 0.6461 | -0.0059 | -0.0029 | -0.0120 | 1.0000 | 1.0000 | 1.0000 |
| hcoef34_resid_basis_resid_core_a0p01_cap0p005_s0p25 | row_oof | 12 | 0.1246 | 0.2081 | 0.6461 | -0.0059 | -0.0029 | -0.0120 | 1.0000 | 1.0000 | 1.0000 |
| hcoef34_resid_basis_resid_core_a0p001_cap0p005_s0p25 | artist_oof | 12 | 0.1246 | 0.2082 | 0.6461 | -0.0059 | -0.0029 | -0.0120 | 1.0000 | 1.0000 | 0.7500 |
| hcoef34_resid_basis_resid_core_a0p01_cap0p005_s0p25 | artist_oof | 12 | 0.1246 | 0.2082 | 0.6461 | -0.0059 | -0.0029 | -0.0120 | 1.0000 | 1.0000 | 0.7500 |
| hcoef34_resid_basis_resid_all_a0p001_cap0p005_s0p5 | artist_oof | 12 | 0.1248 | 0.2082 | 0.6442 | -0.0057 | -0.0028 | -0.0138 | 1.0000 | 1.0000 | 0.5000 |
| hcoef34_resid_basis_resid_all_a0p01_cap0p005_s0p5 | artist_oof | 12 | 0.1248 | 0.2082 | 0.6442 | -0.0057 | -0.0028 | -0.0138 | 1.0000 | 1.0000 | 0.5000 |
| hcoef34_resid_basis_resid_all_a0p01_cap0p01_s0p25 | artist_oof | 12 | 0.1248 | 0.2082 | 0.6442 | -0.0057 | -0.0028 | -0.0138 | 1.0000 | 1.0000 | 0.5000 |
| hcoef34_resid_basis_resid_all_a0p001_cap0p01_s0p25 | artist_oof | 12 | 0.1248 | 0.2082 | 0.6442 | -0.0057 | -0.0028 | -0.0138 | 1.0000 | 1.0000 | 0.5000 |
| hcoef34_resid_basis_resid_all_a0p001_cap0p01_s0p25 | row_oof | 12 | 0.1249 | 0.2082 | 0.6442 | -0.0056 | -0.0028 | -0.0138 | 1.0000 | 1.0000 | 0.4167 |
| hcoef34_resid_basis_resid_all_a0p01_cap0p01_s0p25 | row_oof | 12 | 0.1249 | 0.2082 | 0.6442 | -0.0056 | -0.0028 | -0.0138 | 1.0000 | 1.0000 | 0.4167 |
| hcoef34_resid_basis_resid_all_a0p001_cap0p005_s0p5 | row_oof | 12 | 0.1250 | 0.2082 | 0.6441 | -0.0056 | -0.0028 | -0.0140 | 1.0000 | 1.0000 | 0.4167 |
| hcoef34_resid_basis_resid_all_a0p01_cap0p005_s0p5 | row_oof | 12 | 0.1250 | 0.2082 | 0.6441 | -0.0056 | -0.0028 | -0.0140 | 1.0000 | 1.0000 | 0.4167 |
| hcoef34_resid_basis_resid_all_a0p01_cap0p005_s0p25 | row_oof | 12 | 0.1250 | 0.2082 | 0.6461 | -0.0056 | -0.0028 | -0.0120 | 1.0000 | 0.8333 | 0.5000 |
| hcoef34_resid_basis_resid_all_a0p001_cap0p005_s0p25 | row_oof | 12 | 0.1250 | 0.2082 | 0.6461 | -0.0056 | -0.0028 | -0.0120 | 1.0000 | 0.8333 | 0.5000 |
| hcoef34_resid_basis_resid_all_a0p01_cap0p005_s0p25 | artist_oof | 12 | 0.1251 | 0.2082 | 0.6462 | -0.0054 | -0.0028 | -0.0118 | 1.0000 | 1.0000 | 0.2500 |
| hcoef34_resid_basis_resid_all_a0p001_cap0p005_s0p25 | artist_oof | 12 | 0.1251 | 0.2082 | 0.6462 | -0.0054 | -0.0028 | -0.0118 | 1.0000 | 1.0000 | 0.2500 |
| hcoef34_resid_basis_resid_all_a0p01_cap0p02_s0p5 | row_oof | 12 | 0.1255 | 0.2083 | 0.6463 | -0.0051 | -0.0027 | -0.0117 | 1.0000 | 0.7500 | 0.1667 |
| hcoef34_resid_basis_resid_all_a0p001_cap0p02_s0p5 | row_oof | 12 | 0.1255 | 0.2083 | 0.6463 | -0.0051 | -0.0027 | -0.0117 | 1.0000 | 0.7500 | 0.1667 |
| hcoef34_resid_basis_resid_all_a0p001_cap0p02_s0p25 | row_oof | 12 | 0.1259 | 0.2082 | 0.6439 | -0.0047 | -0.0028 | -0.0141 | 1.0000 | 0.6667 | 0.3333 |
| hcoef34_resid_basis_resid_all_a0p01_cap0p02_s0p25 | row_oof | 12 | 0.1259 | 0.2082 | 0.6439 | -0.0047 | -0.0028 | -0.0141 | 1.0000 | 0.6667 | 0.3333 |
| hcoef34_resid_basis_resid_all_a0p001_cap0p01_s0p5 | artist_oof | 12 | 0.1259 | 0.2083 | 0.6433 | -0.0046 | -0.0027 | -0.0147 | 1.0000 | 0.7500 | 0.1667 |
| hcoef34_resid_basis_resid_all_a0p01_cap0p01_s0p5 | artist_oof | 12 | 0.1259 | 0.2083 | 0.6433 | -0.0046 | -0.0027 | -0.0147 | 1.0000 | 0.7500 | 0.1667 |

_상위 30개만 표시. 전체 114개._

## 8. Huber 계수 해석

- 계수는 표준화된 피처 기준. 절대 원화 단위 계수가 아니라 방향성과 상대 영향 비교용.
- 양수 계수: 해당 피처가 커질수록 예측 로그가격 또는 stable 잔차 보정값을 올리는 방향.
- 음수 계수: 해당 피처가 커질수록 예측 로그가격 또는 stable 잔차 보정값을 낮추는 방향.
- 기준가 피처 계수가 크고 신뢰도 피처가 함께 움직이면, Huber가 '어떤 기준가를 얼마나 믿을지'를 학습했다는 의미.
| candidate | kind | feature_set | target | feature | coefficient_on_scaled_feature | abs_coefficient | direction | alpha | cap | strength | clip_margin |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef34_meta_basis_trust_core_a0p001 | meta_huber | basis_trust_core | actual_log | hcoef_stable | 3.8093 | 3.8093 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 |  |  |  |
| hcoef34_meta_basis_trust_core_a0p001 | meta_huber | basis_trust_core | actual_log | current_70_30 | -2.4666 | 2.4666 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 |  |  |  |
| hcoef34_meta_basis_trust_core_a0p001 | meta_huber | basis_trust_core | actual_log | basis_shrink_k20 | -0.0824 | 0.0824 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 |  |  |  |
| hcoef34_meta_basis_trust_core_a0p001 | meta_huber | basis_trust_core | actual_log | basis_fallback_m5 | 0.0364 | 0.0364 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 |  |  |  |
| hcoef34_meta_basis_trust_core_a0p001 | meta_huber | basis_trust_core | actual_log | log_area | -0.0186 | 0.0186 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 |  |  |  |
| hcoef34_meta_basis_trust_core_a0p001 | meta_huber | basis_trust_core | actual_log | basis_fallback_m5_iqr | 0.0071 | 0.0071 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 |  |  |  |
| hcoef34_meta_basis_trust_core_a0p001 | meta_huber | basis_trust_core | actual_log | basis_fallback_m5_n_log | -0.0070 | 0.0070 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 |  |  |  |
| hcoef34_meta_basis_trust_core_a0p001_clip0p20 | meta_huber | basis_trust_core | actual_log | hcoef_stable | 3.8093 | 3.8093 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 |  |  | 0.2000 |
| hcoef34_meta_basis_trust_core_a0p001_clip0p20 | meta_huber | basis_trust_core | actual_log | current_70_30 | -2.4666 | 2.4666 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 |  |  | 0.2000 |
| hcoef34_meta_basis_trust_core_a0p001_clip0p20 | meta_huber | basis_trust_core | actual_log | basis_shrink_k20 | -0.0824 | 0.0824 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 |  |  | 0.2000 |
| hcoef34_meta_basis_trust_core_a0p001_clip0p20 | meta_huber | basis_trust_core | actual_log | basis_fallback_m5 | 0.0364 | 0.0364 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 |  |  | 0.2000 |
| hcoef34_meta_basis_trust_core_a0p001_clip0p20 | meta_huber | basis_trust_core | actual_log | log_area | -0.0186 | 0.0186 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 |  |  | 0.2000 |
| hcoef34_meta_basis_trust_core_a0p001_clip0p20 | meta_huber | basis_trust_core | actual_log | basis_fallback_m5_iqr | 0.0071 | 0.0071 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 |  |  | 0.2000 |
| hcoef34_meta_basis_trust_core_a0p001_clip0p20 | meta_huber | basis_trust_core | actual_log | basis_fallback_m5_n_log | -0.0070 | 0.0070 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 |  |  | 0.2000 |
| hcoef34_meta_basis_trust_core_a0p01 | meta_huber | basis_trust_core | actual_log | hcoef_stable | 3.6997 | 3.6997 | 예측 로그가격/보정값을 올리는 방향 | 0.0100 |  |  |  |
| hcoef34_meta_basis_trust_core_a0p01 | meta_huber | basis_trust_core | actual_log | current_70_30 | -2.3568 | 2.3568 | 예측 로그가격/보정값을 낮추는 방향 | 0.0100 |  |  |  |
| hcoef34_meta_basis_trust_core_a0p01 | meta_huber | basis_trust_core | actual_log | basis_shrink_k20 | -0.0809 | 0.0809 | 예측 로그가격/보정값을 낮추는 방향 | 0.0100 |  |  |  |
| hcoef34_meta_basis_trust_core_a0p01 | meta_huber | basis_trust_core | actual_log | basis_fallback_m5 | 0.0345 | 0.0345 | 예측 로그가격/보정값을 올리는 방향 | 0.0100 |  |  |  |
| hcoef34_meta_basis_trust_core_a0p01 | meta_huber | basis_trust_core | actual_log | log_area | -0.0185 | 0.0185 | 예측 로그가격/보정값을 낮추는 방향 | 0.0100 |  |  |  |
| hcoef34_meta_basis_trust_core_a0p01 | meta_huber | basis_trust_core | actual_log | basis_fallback_m5_n_log | -0.0072 | 0.0072 | 예측 로그가격/보정값을 낮추는 방향 | 0.0100 |  |  |  |
| hcoef34_meta_basis_trust_core_a0p01 | meta_huber | basis_trust_core | actual_log | basis_fallback_m5_iqr | 0.0070 | 0.0070 | 예측 로그가격/보정값을 올리는 방향 | 0.0100 |  |  |  |
| hcoef34_meta_basis_trust_core_a0p01_clip0p20 | meta_huber | basis_trust_core | actual_log | hcoef_stable | 3.6997 | 3.6997 | 예측 로그가격/보정값을 올리는 방향 | 0.0100 |  |  | 0.2000 |
| hcoef34_meta_basis_trust_core_a0p01_clip0p20 | meta_huber | basis_trust_core | actual_log | current_70_30 | -2.3568 | 2.3568 | 예측 로그가격/보정값을 낮추는 방향 | 0.0100 |  |  | 0.2000 |
| hcoef34_meta_basis_trust_core_a0p01_clip0p20 | meta_huber | basis_trust_core | actual_log | basis_shrink_k20 | -0.0809 | 0.0809 | 예측 로그가격/보정값을 낮추는 방향 | 0.0100 |  |  | 0.2000 |
| hcoef34_meta_basis_trust_core_a0p01_clip0p20 | meta_huber | basis_trust_core | actual_log | basis_fallback_m5 | 0.0345 | 0.0345 | 예측 로그가격/보정값을 올리는 방향 | 0.0100 |  |  | 0.2000 |
| hcoef34_meta_basis_trust_core_a0p01_clip0p20 | meta_huber | basis_trust_core | actual_log | log_area | -0.0185 | 0.0185 | 예측 로그가격/보정값을 낮추는 방향 | 0.0100 |  |  | 0.2000 |
| hcoef34_meta_basis_trust_core_a0p01_clip0p20 | meta_huber | basis_trust_core | actual_log | basis_fallback_m5_n_log | -0.0072 | 0.0072 | 예측 로그가격/보정값을 낮추는 방향 | 0.0100 |  |  | 0.2000 |
| hcoef34_meta_basis_trust_core_a0p01_clip0p20 | meta_huber | basis_trust_core | actual_log | basis_fallback_m5_iqr | 0.0070 | 0.0070 | 예측 로그가격/보정값을 올리는 방향 | 0.0100 |  |  | 0.2000 |
| hcoef34_meta_basis_generation_all_a0p001 | meta_huber | basis_generation_all | actual_log | hcoef_stable | 2.7890 | 2.7890 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 |  |  |  |
| hcoef34_meta_basis_generation_all_a0p001 | meta_huber | basis_generation_all | actual_log | current_70_30 | -1.5791 | 1.5791 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 |  |  |  |
| hcoef34_meta_basis_generation_all_a0p001 | meta_huber | basis_generation_all | actual_log | basis_shrink_k5 | 0.4344 | 0.4344 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 |  |  |  |
| hcoef34_meta_basis_generation_all_a0p001 | meta_huber | basis_generation_all | actual_log | basis_shrink_k20 | -0.2163 | 0.2163 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 |  |  |  |
| hcoef34_meta_basis_generation_all_a0p001 | meta_huber | basis_generation_all | actual_log | basis_fallback_m5 | -0.1066 | 0.1066 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 |  |  |  |
| hcoef34_meta_basis_generation_all_a0p001 | meta_huber | basis_generation_all | actual_log | basis_artist_size_medium_support_m5 | 0.0268 | 0.0268 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 |  |  |  |
| hcoef34_meta_basis_generation_all_a0p001 | meta_huber | basis_generation_all | actual_log | basis_artist_size_m5 | -0.0225 | 0.0225 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 |  |  |  |
| hcoef34_meta_basis_generation_all_a0p001 | meta_huber | basis_generation_all | actual_log | basis_artist_overall_m1 | -0.0225 | 0.0225 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 |  |  |  |
| hcoef34_meta_basis_generation_all_a0p001 | meta_huber | basis_generation_all | actual_log | basis_artist_medium_support_m5 | -0.0219 | 0.0219 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 |  |  |  |
| hcoef34_meta_basis_generation_all_a0p001 | meta_huber | basis_generation_all | actual_log | log_area | -0.0137 | 0.0137 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 |  |  |  |
| hcoef34_meta_basis_generation_all_a0p001 | meta_huber | basis_generation_all | actual_log | basis_fallback_m5_iqr | 0.0117 | 0.0117 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 |  |  |  |
| hcoef34_meta_basis_generation_all_a0p001 | meta_huber | basis_generation_all | actual_log | basis_component_spread | -0.0113 | 0.0113 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 |  |  |  |
| hcoef34_meta_basis_generation_all_a0p001 | meta_huber | basis_generation_all | actual_log | basis_fallback_m5_n_log | -0.0102 | 0.0102 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 |  |  |  |
| hcoef34_meta_basis_generation_all_a0p001_clip0p20 | meta_huber | basis_generation_all | actual_log | hcoef_stable | 2.7890 | 2.7890 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 |  |  | 0.2000 |
| hcoef34_meta_basis_generation_all_a0p001_clip0p20 | meta_huber | basis_generation_all | actual_log | current_70_30 | -1.5791 | 1.5791 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 |  |  | 0.2000 |
| hcoef34_meta_basis_generation_all_a0p001_clip0p20 | meta_huber | basis_generation_all | actual_log | basis_shrink_k5 | 0.4344 | 0.4344 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 |  |  | 0.2000 |
| hcoef34_meta_basis_generation_all_a0p001_clip0p20 | meta_huber | basis_generation_all | actual_log | basis_shrink_k20 | -0.2163 | 0.2163 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 |  |  | 0.2000 |
| hcoef34_meta_basis_generation_all_a0p001_clip0p20 | meta_huber | basis_generation_all | actual_log | basis_fallback_m5 | -0.1066 | 0.1066 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 |  |  | 0.2000 |
| hcoef34_meta_basis_generation_all_a0p001_clip0p20 | meta_huber | basis_generation_all | actual_log | basis_artist_size_medium_support_m5 | 0.0268 | 0.0268 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 |  |  | 0.2000 |
| hcoef34_meta_basis_generation_all_a0p001_clip0p20 | meta_huber | basis_generation_all | actual_log | basis_artist_size_m5 | -0.0225 | 0.0225 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 |  |  | 0.2000 |
| hcoef34_meta_basis_generation_all_a0p001_clip0p20 | meta_huber | basis_generation_all | actual_log | basis_artist_overall_m1 | -0.0225 | 0.0225 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 |  |  | 0.2000 |
| hcoef34_meta_basis_generation_all_a0p001_clip0p20 | meta_huber | basis_generation_all | actual_log | basis_artist_medium_support_m5 | -0.0219 | 0.0219 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 |  |  | 0.2000 |
| hcoef34_meta_basis_generation_all_a0p001_clip0p20 | meta_huber | basis_generation_all | actual_log | log_area | -0.0137 | 0.0137 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 |  |  | 0.2000 |
| hcoef34_meta_basis_generation_all_a0p001_clip0p20 | meta_huber | basis_generation_all | actual_log | basis_fallback_m5_iqr | 0.0117 | 0.0117 | 예측 로그가격/보정값을 올리는 방향 | 0.0010 |  |  | 0.2000 |
| hcoef34_meta_basis_generation_all_a0p001_clip0p20 | meta_huber | basis_generation_all | actual_log | basis_component_spread | -0.0113 | 0.0113 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 |  |  | 0.2000 |
| hcoef34_meta_basis_generation_all_a0p001_clip0p20 | meta_huber | basis_generation_all | actual_log | basis_fallback_m5_n_log | -0.0102 | 0.0102 | 예측 로그가격/보정값을 낮추는 방향 | 0.0010 |  |  | 0.2000 |
| hcoef34_meta_basis_generation_all_a0p01 | meta_huber | basis_generation_all | actual_log | hcoef_stable | 2.7064 | 2.7064 | 예측 로그가격/보정값을 올리는 방향 | 0.0100 |  |  |  |
| hcoef34_meta_basis_generation_all_a0p01 | meta_huber | basis_generation_all | actual_log | current_70_30 | -1.4972 | 1.4972 | 예측 로그가격/보정값을 낮추는 방향 | 0.0100 |  |  |  |
| hcoef34_meta_basis_generation_all_a0p01 | meta_huber | basis_generation_all | actual_log | basis_shrink_k5 | 0.4371 | 0.4371 | 예측 로그가격/보정값을 올리는 방향 | 0.0100 |  |  |  |
| hcoef34_meta_basis_generation_all_a0p01 | meta_huber | basis_generation_all | actual_log | basis_shrink_k20 | -0.2152 | 0.2152 | 예측 로그가격/보정값을 낮추는 방향 | 0.0100 |  |  |  |
| hcoef34_meta_basis_generation_all_a0p01 | meta_huber | basis_generation_all | actual_log | basis_fallback_m5 | -0.1089 | 0.1089 | 예측 로그가격/보정값을 낮추는 방향 | 0.0100 |  |  |  |
| hcoef34_meta_basis_generation_all_a0p01 | meta_huber | basis_generation_all | actual_log | basis_artist_size_medium_support_m5 | 0.0271 | 0.0271 | 예측 로그가격/보정값을 올리는 방향 | 0.0100 |  |  |  |

## 9. 잔차/큰 오차 요약

| split | candidate | n | median_residual_log | mean_residual_log | residual_std | ape_median | ape_mean | ape_p95 | ape_gt_100pct_n | over_2x_n | under_half_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | current_70_30 | 607 | -0.0006 | -0.0119 | 0.3998 | 0.1405 | 0.2748 | 0.8331 | 24 | 24 | 17 |
| test | hcoef_stable | 607 | -0.0039 | -0.0148 | 0.3989 | 0.1388 | 0.2730 | 0.8064 | 26 | 26 | 17 |
| test | basis_fallback_m5 | 607 | 0.0000 | 0.0198 | 0.7822 | 0.3115 | 0.7237 | 2.2963 | 79 | 79 | 78 |
| test | basis_shrink_k20 | 607 | -0.0290 | 0.0075 | 0.7806 | 0.4337 | 0.7124 | 2.3046 | 97 | 97 | 108 |
| 0604_ex50 | current_70_30 | 829 | 0.0782 | 0.3370 | 1.2685 | 0.2779 | 0.3774 | 0.9871 | 30 | 30 | 153 |
| 0604_ex50 | hcoef_stable | 829 | 0.0608 | 0.3278 | 1.2668 | 0.2731 | 0.3744 | 0.9835 | 26 | 26 | 152 |
| 0604_ex50 | basis_fallback_m5 | 829 | 0.0000 | 0.0789 | 1.0657 | 0.4108 | 0.9491 | 4.0140 | 135 | 137 | 166 |
| 0604_ex50 | basis_shrink_k20 | 829 | -0.0181 | 0.0155 | 1.1132 | 0.6129 | 1.0603 | 3.4046 | 195 | 195 | 189 |
| test | hcoef34_resid_basis_resid_core_a0p001_cap0p005_s0p5 | 607 | -0.0017 | -0.0150 | 0.3990 | 0.1373 | 0.2730 | 0.8081 | 26 | 26 | 17 |
| 0604_ex50 | hcoef34_resid_basis_resid_core_a0p001_cap0p005_s0p5 | 829 | 0.0583 | 0.3271 | 1.2671 | 0.2746 | 0.3746 | 0.9835 | 27 | 27 | 152 |
| test | hcoef34_resid_basis_resid_core_a0p001_cap0p01_s0p25 | 607 | -0.0017 | -0.0151 | 0.3989 | 0.1373 | 0.2730 | 0.8081 | 26 | 26 | 17 |
| 0604_ex50 | hcoef34_resid_basis_resid_core_a0p001_cap0p01_s0p25 | 829 | 0.0583 | 0.3272 | 1.2671 | 0.2746 | 0.3746 | 0.9835 | 27 | 27 | 152 |
| test | hcoef34_resid_basis_resid_core_a0p01_cap0p005_s0p5 | 607 | -0.0017 | -0.0150 | 0.3990 | 0.1373 | 0.2730 | 0.8081 | 26 | 26 | 17 |
| 0604_ex50 | hcoef34_resid_basis_resid_core_a0p01_cap0p005_s0p5 | 829 | 0.0583 | 0.3271 | 1.2671 | 0.2746 | 0.3746 | 0.9835 | 27 | 27 | 152 |
| test | hcoef34_resid_basis_resid_core_a0p01_cap0p01_s0p25 | 607 | -0.0017 | -0.0151 | 0.3989 | 0.1373 | 0.2730 | 0.8081 | 26 | 26 | 17 |
| 0604_ex50 | hcoef34_resid_basis_resid_core_a0p01_cap0p01_s0p25 | 829 | 0.0583 | 0.3272 | 1.2671 | 0.2746 | 0.3746 | 0.9835 | 27 | 27 | 152 |
| test | hcoef34_resid_basis_resid_all_a0p001_cap0p005_s0p25 | 607 | -0.0027 | -0.0149 | 0.3988 | 0.1377 | 0.2729 | 0.8069 | 26 | 26 | 17 |
| 0604_ex50 | hcoef34_resid_basis_resid_all_a0p001_cap0p005_s0p25 | 829 | 0.0621 | 0.3278 | 1.2669 | 0.2740 | 0.3745 | 0.9835 | 26 | 26 | 152 |
| test | hcoef34_resid_basis_resid_all_a0p001_cap0p005_s0p5 | 607 | -0.0030 | -0.0151 | 0.3987 | 0.1373 | 0.2729 | 0.8074 | 26 | 26 | 17 |
| 0604_ex50 | hcoef34_resid_basis_resid_all_a0p001_cap0p005_s0p5 | 829 | 0.0633 | 0.3279 | 1.2670 | 0.2749 | 0.3746 | 0.9835 | 27 | 27 | 152 |
| test | hcoef34_resid_basis_resid_all_a0p001_cap0p01_s0p25 | 607 | -0.0030 | -0.0151 | 0.3987 | 0.1373 | 0.2729 | 0.8074 | 26 | 26 | 17 |
| 0604_ex50 | hcoef34_resid_basis_resid_all_a0p001_cap0p01_s0p25 | 829 | 0.0633 | 0.3279 | 1.2670 | 0.2749 | 0.3746 | 0.9835 | 27 | 27 | 152 |
| test | hcoef34_resid_basis_resid_all_a0p001_cap0p02_s0p25 | 607 | -0.0034 | -0.0153 | 0.3986 | 0.1375 | 0.2729 | 0.8094 | 27 | 27 | 17 |
| 0604_ex50 | hcoef34_resid_basis_resid_all_a0p001_cap0p02_s0p25 | 829 | 0.0658 | 0.3280 | 1.2673 | 0.2767 | 0.3749 | 0.9849 | 27 | 27 | 153 |
| test | hcoef34_resid_basis_resid_all_a0p01_cap0p005_s0p25 | 607 | -0.0027 | -0.0149 | 0.3988 | 0.1377 | 0.2729 | 0.8069 | 26 | 26 | 17 |
| 0604_ex50 | hcoef34_resid_basis_resid_all_a0p01_cap0p005_s0p25 | 829 | 0.0621 | 0.3278 | 1.2669 | 0.2740 | 0.3745 | 0.9835 | 26 | 26 | 152 |
| test | hcoef34_resid_basis_resid_all_a0p01_cap0p005_s0p5 | 607 | -0.0030 | -0.0151 | 0.3987 | 0.1373 | 0.2729 | 0.8074 | 26 | 26 | 17 |
| 0604_ex50 | hcoef34_resid_basis_resid_all_a0p01_cap0p005_s0p5 | 829 | 0.0633 | 0.3279 | 1.2670 | 0.2749 | 0.3746 | 0.9835 | 27 | 27 | 152 |
| test | hcoef34_resid_basis_resid_all_a0p01_cap0p01_s0p25 | 607 | -0.0030 | -0.0151 | 0.3987 | 0.1373 | 0.2729 | 0.8074 | 26 | 26 | 17 |
| 0604_ex50 | hcoef34_resid_basis_resid_all_a0p01_cap0p01_s0p25 | 829 | 0.0633 | 0.3279 | 1.2670 | 0.2749 | 0.3746 | 0.9835 | 27 | 27 | 152 |
| test | hcoef34_resid_basis_resid_all_a0p01_cap0p02_s0p25 | 607 | -0.0034 | -0.0153 | 0.3986 | 0.1375 | 0.2729 | 0.8094 | 27 | 27 | 17 |
| 0604_ex50 | hcoef34_resid_basis_resid_all_a0p01_cap0p02_s0p25 | 829 | 0.0658 | 0.3280 | 1.2673 | 0.2767 | 0.3749 | 0.9849 | 27 | 27 | 153 |

## 10. 다음 보정 방향

- HCOEF34에서 안정 후보가 나오면 HCOEF35에서 반복 횟수를 늘려 row/artist/bootstrap 재검증.
- 안정 후보가 없으면 기준가 직접 반영보다 신뢰도별 routing 또는 가격 범위/신뢰도 정책으로 분리.
- fixed test만 좋은 후보는 채택하지 않고, validation OOF 기준으로 동일 방향이 반복되는지 먼저 확인.

## 11. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/residual_analysis.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `outputs/selected_candidates.csv`
- `outputs/basis_coverage.csv`
- `artifacts/experiment_config.json`