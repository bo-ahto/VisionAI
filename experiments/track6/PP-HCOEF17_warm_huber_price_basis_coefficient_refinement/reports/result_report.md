# PP-HCOEF17 Warm guarded PP-V8 movement

- 작성일: 2026-06-08 02:06
- 목적: HCOEF 안정 후보를 기본으로 유지하면서 PP-V8/service component를 신뢰 가능한 구간에만 제한 반영할 수 있는지 검증
- 기준 후보: `hcoef2_size_reliability_cap005_s050`
- 선택 기준: validation 우선, fixed test와 0604는 확인용
- 금지 기준: test/0604 residual을 보고 threshold, weight, cap을 만들지 않음

## 1. 실행 결론

- PP-V8 전체 반영은 HCOEF16에서 fixed test/artist OOF 기준 미통과였음.
- HCOEF17은 PP-V8과 HCOEF 안정 후보의 예측 차이가 작거나 비교군 신뢰도가 높은 구간에서만 제한 이동하는 후보를 비교함.
- 새 후보는 validation에서 먼저 판단하고, fixed test p95 guard와 bootstrap으로 재검증함.
- 0604에서 PP-V8이 HCOEF 안정 후보보다 APE가 낮은 비율: `0.5223`

## 2. validation 상위 후보

| candidate | method | n | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable | policy_apply_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef17_guard_agree_gap0p15_cap0p05_w0p5 | guarded_move | 519 | 0.1253 | 0.2095 | 0.6542 | 0.3258 | -0.0006 | 0.0013 | 0.0063 | 0.7592 |
| hcoef17_guard_cov1_n10_gap0p05_cap0p05_w0p25 | guarded_move | 519 | 0.1260 | 0.2081 | 0.6479 | 0.3251 | 0.0000 | -0.0001 | 0.0000 | 0.0944 |
| hcoef17_guard_cov1_n10_gap0p05_cap0p03_w0p25 | guarded_move | 519 | 0.1260 | 0.2081 | 0.6479 | 0.3251 | 0.0000 | -0.0001 | 0.0000 | 0.0944 |
| hcoef17_guard_cov1_n20_gap0p15_cap0p05_w0p25 | guarded_move | 519 | 0.1260 | 0.2081 | 0.6479 | 0.3252 | 0.0000 | -0.0001 | 0.0000 | 0.1002 |
| hcoef17_guard_cov1_n20_gap0p15_cap0p03_w0p25 | guarded_move | 519 | 0.1260 | 0.2081 | 0.6479 | 0.3252 | 0.0000 | -0.0001 | 0.0000 | 0.1002 |
| hcoef17_guard_cov1_n10_gap0p05_cap0p05_w0p1 | guarded_move | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | -0.0001 | 0.0000 | 0.0944 |
| hcoef17_guard_cov1_n20_gap0p05_cap0p05_w0p25 | guarded_move | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | -0.0000 | 0.0000 | 0.0674 |
| hcoef17_guard_cov1_n10_gap0p05_cap0p03_w0p1 | guarded_move | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | -0.0000 | 0.0000 | 0.0944 |
| hcoef17_guard_cov1_n20_gap0p15_cap0p05_w0p1 | guarded_move | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | -0.0000 | 0.0000 | 0.1002 |
| hcoef17_guard_cov1_n20_gap0p05_cap0p03_w0p25 | guarded_move | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | -0.0000 | 0.0000 | 0.0674 |
| hcoef17_guard_cov1_n20_gap0p15_cap0p03_w0p1 | guarded_move | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | -0.0000 | 0.0000 | 0.1002 |
| hcoef17_guard_cov1_n20_gap0p05_cap0p05_w0p1 | guarded_move | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | -0.0000 | 0.0000 | 0.0674 |
| hcoef17_guard_cov1_n20_gap0p05_cap0p03_w0p1 | guarded_move | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | -0.0000 | 0.0000 | 0.0674 |
| hcoef17_guard_agree_gap0p05_cap0p05_w0p1 | guarded_move | 519 | 0.1260 | 0.2082 | 0.6481 | 0.3253 | 0.0000 | -0.0000 | 0.0001 | 0.3699 |
| hcoef17_adaptive_tiered_conservative | guarded_move | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | -0.0000 | 0.0000 | 0.0963 |
| hcoef_stable | baseline | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| hcoef17_guard_agree_gap0p05_cap0p05_w0p25 | guarded_move | 519 | 0.1260 | 0.2082 | 0.6481 | 0.3254 | 0.0000 | 0.0000 | 0.0002 | 0.3699 |
| hcoef17_guard_cov1_n20_gap0p1_cap0p03_w0p1 | guarded_move | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0.0886 |
| hcoef17_guard_cov1_n20_gap0p1_cap0p03_w0p25 | guarded_move | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0.0886 |
| hcoef17_guard_cov1_n20_gap0p1_cap0p05_w0p1 | guarded_move | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0.0886 |
| hcoef17_guard_cov2_n10_gap0p05_cap0p03_w0p1 | guarded_move | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0.0077 |
| hcoef17_guard_cov2_n20_gap0p05_cap0p03_w0p1 | guarded_move | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0.0077 |
| hcoef17_guard_agree_gap0p05_cap0p02_w0p25 | guarded_move | 519 | 0.1260 | 0.2082 | 0.6481 | 0.3253 | 0.0000 | 0.0000 | 0.0002 | 0.3699 |
| hcoef17_guard_cov2_n10_gap0p05_cap0p05_w0p1 | guarded_move | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0.0077 |
| hcoef17_guard_cov2_n20_gap0p05_cap0p05_w0p1 | guarded_move | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0.0077 |

_Only first 25 of 100 rows shown._

## 3. fixed test 상위 후보

| candidate | method | n | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable | policy_apply_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef17_guard_agree_gap0p05_cap0p03_w0p5 | guarded_move | 607 | 0.1374 | 0.2735 | 0.8064 | 0.3991 | -0.0014 | 0.0005 | 0.0000 | 0.3377 |
| hcoef17_guard_agree_gap0p05_cap0p05_w0p5 | guarded_move | 607 | 0.1374 | 0.2736 | 0.8064 | 0.3991 | -0.0014 | 0.0007 | 0.0000 | 0.3377 |
| hcoef17_guard_cov2_n10_gap0p15_cap0p05_w0p25 | guarded_move | 607 | 0.1384 | 0.2729 | 0.8064 | 0.3988 | -0.0004 | -0.0001 | 0.0000 | 0.0214 |
| hcoef17_guard_cov2_n20_gap0p15_cap0p05_w0p25 | guarded_move | 607 | 0.1384 | 0.2729 | 0.8064 | 0.3988 | -0.0004 | -0.0001 | 0.0000 | 0.0214 |
| hcoef17_guard_cov2_n10_gap0p1_cap0p05_w0p25 | guarded_move | 607 | 0.1384 | 0.2729 | 0.8064 | 0.3988 | -0.0004 | -0.0001 | 0.0000 | 0.0198 |
| hcoef17_guard_cov2_n20_gap0p1_cap0p05_w0p25 | guarded_move | 607 | 0.1384 | 0.2729 | 0.8064 | 0.3988 | -0.0004 | -0.0001 | 0.0000 | 0.0198 |
| hcoef17_guard_cov2_n10_gap0p15_cap0p03_w0p25 | guarded_move | 607 | 0.1384 | 0.2729 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0214 |
| hcoef17_guard_cov2_n20_gap0p15_cap0p03_w0p25 | guarded_move | 607 | 0.1384 | 0.2729 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0214 |
| hcoef17_guard_cov2_n10_gap0p1_cap0p03_w0p25 | guarded_move | 607 | 0.1384 | 0.2729 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0198 |
| hcoef17_guard_cov2_n20_gap0p1_cap0p03_w0p25 | guarded_move | 607 | 0.1384 | 0.2729 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0198 |
| hcoef17_guard_cov2_n10_gap0p15_cap0p05_w0p1 | guarded_move | 607 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0214 |
| hcoef17_guard_cov2_n20_gap0p15_cap0p05_w0p1 | guarded_move | 607 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0214 |
| hcoef17_guard_cov2_n10_gap0p05_cap0p05_w0p25 | guarded_move | 607 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0099 |
| hcoef17_guard_cov2_n20_gap0p05_cap0p05_w0p25 | guarded_move | 607 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0099 |
| hcoef17_guard_cov2_n10_gap0p1_cap0p05_w0p1 | guarded_move | 607 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0198 |
| hcoef17_guard_cov2_n20_gap0p1_cap0p05_w0p1 | guarded_move | 607 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0198 |
| hcoef17_guard_cov2_n10_gap0p05_cap0p03_w0p25 | guarded_move | 607 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0099 |
| hcoef17_guard_cov2_n20_gap0p05_cap0p03_w0p25 | guarded_move | 607 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0099 |
| hcoef17_guard_cov2_n10_gap0p15_cap0p03_w0p1 | guarded_move | 607 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0214 |
| hcoef17_guard_cov2_n20_gap0p15_cap0p03_w0p1 | guarded_move | 607 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0214 |
| hcoef17_guard_cov2_n10_gap0p1_cap0p03_w0p1 | guarded_move | 607 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0198 |
| hcoef17_guard_cov2_n20_gap0p1_cap0p03_w0p1 | guarded_move | 607 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0198 |
| hcoef17_guard_cov2_n10_gap0p05_cap0p05_w0p1 | guarded_move | 607 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0099 |
| hcoef17_guard_cov2_n20_gap0p05_cap0p05_w0p1 | guarded_move | 607 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0099 |
| hcoef17_guard_cov2_n10_gap0p05_cap0p03_w0p1 | guarded_move | 607 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0099 |

_Only first 25 of 100 rows shown._

## 4. 0604 stress test 상위 후보

| candidate | method | n | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable | policy_apply_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppv8_service_proxy | component | 829 | 0.2298 | 0.3359 | 0.9273 | 0.7124 | -0.0433 | -0.0385 | -0.0561 | 1.0000 |
| hcoef17_guard_cov2_n10_gap0p15_cap0p05_w0p25 | guarded_move | 829 | 0.2731 | 0.3739 | 0.9790 | 1.3077 | 0.0000 | -0.0004 | -0.0045 | 0.0338 |
| hcoef17_guard_cov2_n20_gap0p15_cap0p05_w0p25 | guarded_move | 829 | 0.2731 | 0.3739 | 0.9790 | 1.3077 | 0.0000 | -0.0004 | -0.0045 | 0.0338 |
| hcoef17_adaptive_tiered_mape_guard | guarded_move | 829 | 0.2731 | 0.3740 | 0.9790 | 1.3077 | 0.0000 | -0.0004 | -0.0045 | 0.1170 |
| hcoef17_guard_cov1_n20_gap0p15_cap0p05_w0p25 | guarded_move | 829 | 0.2731 | 0.3740 | 0.9790 | 1.3077 | 0.0000 | -0.0004 | -0.0045 | 0.0989 |
| hcoef17_guard_cov2_n10_gap0p15_cap0p03_w0p25 | guarded_move | 829 | 0.2731 | 0.3741 | 0.9808 | 1.3077 | 0.0000 | -0.0003 | -0.0027 | 0.0338 |
| hcoef17_guard_cov2_n20_gap0p15_cap0p03_w0p25 | guarded_move | 829 | 0.2731 | 0.3741 | 0.9808 | 1.3077 | 0.0000 | -0.0003 | -0.0027 | 0.0338 |
| hcoef17_guard_cov1_n20_gap0p15_cap0p03_w0p25 | guarded_move | 829 | 0.2731 | 0.3742 | 0.9808 | 1.3078 | 0.0000 | -0.0002 | -0.0027 | 0.0989 |
| hcoef17_guard_cov2_n10_gap0p15_cap0p05_w0p1 | guarded_move | 829 | 0.2731 | 0.3742 | 0.9835 | 1.3077 | 0.0000 | -0.0002 | 0.0000 | 0.0338 |
| hcoef17_guard_cov2_n20_gap0p15_cap0p05_w0p1 | guarded_move | 829 | 0.2731 | 0.3742 | 0.9835 | 1.3077 | 0.0000 | -0.0002 | 0.0000 | 0.0338 |
| hcoef17_guard_cov1_n20_gap0p15_cap0p05_w0p1 | guarded_move | 829 | 0.2731 | 0.3742 | 0.9835 | 1.3078 | 0.0000 | -0.0001 | 0.0000 | 0.0989 |
| hcoef17_guard_cov2_n10_gap0p1_cap0p05_w0p25 | guarded_move | 829 | 0.2731 | 0.3742 | 0.9790 | 1.3077 | 0.0000 | -0.0001 | -0.0045 | 0.0145 |
| hcoef17_guard_cov2_n20_gap0p1_cap0p05_w0p25 | guarded_move | 829 | 0.2731 | 0.3742 | 0.9790 | 1.3077 | 0.0000 | -0.0001 | -0.0045 | 0.0145 |
| hcoef17_guard_cov2_n10_gap0p15_cap0p03_w0p1 | guarded_move | 829 | 0.2731 | 0.3743 | 0.9835 | 1.3077 | 0.0000 | -0.0001 | 0.0000 | 0.0338 |
| hcoef17_guard_cov2_n20_gap0p15_cap0p03_w0p1 | guarded_move | 829 | 0.2731 | 0.3743 | 0.9835 | 1.3077 | 0.0000 | -0.0001 | 0.0000 | 0.0338 |
| hcoef17_guard_cov1_n10_gap0p15_cap0p05_w0p1 | guarded_move | 829 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0001 | 0.0000 | 0.1315 |
| hcoef17_guard_cov2_n10_gap0p1_cap0p03_w0p25 | guarded_move | 829 | 0.2731 | 0.3743 | 0.9808 | 1.3077 | 0.0000 | -0.0001 | -0.0027 | 0.0145 |
| hcoef17_guard_cov2_n20_gap0p1_cap0p03_w0p25 | guarded_move | 829 | 0.2731 | 0.3743 | 0.9808 | 1.3077 | 0.0000 | -0.0001 | -0.0027 | 0.0145 |
| hcoef17_guard_cov1_n10_gap0p15_cap0p03_w0p25 | guarded_move | 829 | 0.2731 | 0.3743 | 0.9808 | 1.3078 | 0.0000 | -0.0001 | -0.0027 | 0.1315 |
| hcoef17_guard_cov1_n20_gap0p1_cap0p05_w0p25 | guarded_move | 829 | 0.2731 | 0.3743 | 0.9790 | 1.3077 | 0.0000 | -0.0001 | -0.0045 | 0.0700 |
| hcoef17_guard_cov1_n20_gap0p15_cap0p03_w0p1 | guarded_move | 829 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0001 | 0.0000 | 0.0989 |
| hcoef17_guard_cov2_n10_gap0p1_cap0p05_w0p1 | guarded_move | 829 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0001 | 0.0000 | 0.0145 |
| hcoef17_guard_cov2_n20_gap0p1_cap0p05_w0p1 | guarded_move | 829 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0001 | 0.0000 | 0.0145 |
| hcoef17_guard_agree_gap0p2_cap0p05_w0p1 | guarded_move | 829 | 0.2731 | 0.3743 | 0.9835 | 1.3077 | 0.0000 | -0.0001 | 0.0000 | 0.5151 |
| hcoef17_adaptive_tiered_conservative | guarded_move | 829 | 0.2731 | 0.3743 | 0.9808 | 1.3077 | 0.0000 | -0.0000 | -0.0027 | 0.0724 |

_Only first 25 of 100 rows shown._

## 5. 후보 선택표

| candidate | method | validation_MdAPE | validation_MAPE | validation_p95_APE | validation_RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable | policy_apply_rate | test_MdAPE | test_MAPE | test_p95_APE | test_RMSE_log | test_delta_MdAPE_vs_stable | test_delta_MAPE_vs_stable | test_delta_p95_APE_vs_stable | validation_artist_bootstrap_all3_improve_prob | validation_row_bootstrap_all3_improve_prob | validation_artist_bootstrap_any2_improve_prob | validation_row_bootstrap_any2_improve_prob | validation_pass_2of3 | fixed_test_p95_guard | fixed_test_2of3 | bootstrap_gate | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef17_guard_agree_gap0p15_cap0p05_w0p5 | guarded_move | 0.1253 | 0.2095 | 0.6542 | 0.3258 | -0.0006 | 0.0013 | 0.0063 | 0.7592 | 0.1408 | 0.2726 | 0.8097 | 0.3977 | 0.0020 | -0.0004 | 0.0033 | 0.0100 | 0.0067 | 0.1500 | 0.1433 | False | False | False | False | 보류 |
| hcoef17_guard_cov2_n10_gap0p05_cap0p03_w0p1 | guarded_move | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0.0077 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | True | True | False | 보류 |
| hcoef17_guard_cov2_n20_gap0p05_cap0p03_w0p1 | guarded_move | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0.0077 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | True | True | False | 보류 |
| hcoef17_guard_cov2_n10_gap0p05_cap0p05_w0p1 | guarded_move | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0.0077 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | True | True | False | 보류 |
| hcoef17_guard_cov2_n20_gap0p05_cap0p05_w0p1 | guarded_move | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0.0077 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | True | True | False | 보류 |
| hcoef17_guard_cov2_n10_gap0p1_cap0p03_w0p1 | guarded_move | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0.0096 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | True | True | False | 보류 |
| hcoef17_guard_cov2_n10_gap0p15_cap0p03_w0p1 | guarded_move | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0.0096 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | True | True | False | 보류 |
| hcoef17_guard_cov2_n20_gap0p1_cap0p03_w0p1 | guarded_move | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0.0096 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | True | True | False | 보류 |
| hcoef17_guard_cov2_n20_gap0p15_cap0p03_w0p1 | guarded_move | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0.0096 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | True | True | False | 보류 |
| hcoef17_guard_cov2_n10_gap0p1_cap0p05_w0p1 | guarded_move | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0.0096 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | True | True | False | 보류 |
| hcoef17_guard_cov2_n10_gap0p15_cap0p05_w0p1 | guarded_move | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0.0096 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | True | True | False | 보류 |
| hcoef17_guard_cov2_n20_gap0p1_cap0p05_w0p1 | guarded_move | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0.0096 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | True | True | False | 보류 |
| hcoef17_guard_cov2_n20_gap0p15_cap0p05_w0p1 | guarded_move | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0.0096 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | True | True | False | 보류 |
| hcoef17_guard_cov2_n10_gap0p05_cap0p03_w0p25 | guarded_move | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0.0077 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | True | True | False | 보류 |
| hcoef17_guard_cov2_n20_gap0p05_cap0p03_w0p25 | guarded_move | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0.0077 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | True | True | False | 보류 |
| hcoef17_guard_cov2_n10_gap0p05_cap0p05_w0p25 | guarded_move | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0.0077 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | True | True | False | 보류 |
| hcoef17_guard_cov2_n20_gap0p05_cap0p05_w0p25 | guarded_move | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0.0077 | 0.1384 | 0.2730 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | True | True | False | 보류 |
| hcoef17_guard_cov2_n10_gap0p1_cap0p03_w0p25 | guarded_move | 0.1260 | 0.2083 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0.0096 | 0.1384 | 0.2729 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | True | True | False | 보류 |
| hcoef17_guard_cov2_n10_gap0p15_cap0p03_w0p25 | guarded_move | 0.1260 | 0.2083 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0.0096 | 0.1384 | 0.2729 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | True | True | False | 보류 |
| hcoef17_guard_cov2_n20_gap0p1_cap0p03_w0p25 | guarded_move | 0.1260 | 0.2083 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0.0096 | 0.1384 | 0.2729 | 0.8064 | 0.3988 | -0.0004 | -0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | True | True | False | 보류 |

## 6. bootstrap 요약

| split | validation_scheme | candidate | method | n_bootstrap | mean_delta_MdAPE_vs_stable | mean_delta_MAPE_vs_stable | mean_delta_p95_APE_vs_stable | mean_delta_RMSE_log_vs_stable | MdAPE_improve_prob | MAPE_improve_prob | p95_improve_prob | all3_improve_prob | any2_improve_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | artist_bootstrap | hcoef17_guard_agree_gap0p15_cap0p05_w0p5 | guarded_move | 300 | 0.0011 | -0.0004 | 0.0004 | -0.0012 | 0.3800 | 0.6600 | 0.3533 | 0.1067 | 0.4567 |
| test | artist_bootstrap | current_70_30 | baseline | 300 | -0.0003 | 0.0017 | -0.0056 | 0.0007 | 0.5100 | 0.0467 | 0.5733 | 0.0267 | 0.2933 |
| test | artist_bootstrap | ppv8_service_proxy | component | 300 | 0.0239 | 0.0085 | 0.0487 | 0.0038 | 0.0100 | 0.2100 | 0.3200 | 0.0067 | 0.1367 |
| test | artist_bootstrap | hcoef_stable | baseline | 300 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| test | artist_bootstrap | hcoef17_guard_cov2_n10_gap0p05_cap0p03_w0p1 | guarded_move | 300 | -0.0001 | -0.0000 | 0.0000 | -0.0000 | 0.1600 | 0.9233 | 0.0000 | 0.0000 | 0.1567 |
| test | artist_bootstrap | hcoef17_guard_cov2_n10_gap0p05_cap0p03_w0p25 | guarded_move | 300 | -0.0003 | -0.0000 | 0.0000 | -0.0000 | 0.2733 | 0.8967 | 0.0000 | 0.0000 | 0.2700 |
| test | artist_bootstrap | hcoef17_guard_cov2_n10_gap0p05_cap0p05_w0p1 | guarded_move | 300 | -0.0002 | -0.0000 | 0.0000 | -0.0000 | 0.1833 | 0.9333 | 0.0000 | 0.0000 | 0.1800 |
| test | artist_bootstrap | hcoef17_guard_cov2_n10_gap0p05_cap0p05_w0p25 | guarded_move | 300 | -0.0003 | -0.0000 | 0.0000 | -0.0000 | 0.3300 | 0.9067 | 0.0000 | 0.0000 | 0.3267 |
| test | artist_bootstrap | hcoef17_guard_cov2_n10_gap0p1_cap0p03_w0p1 | guarded_move | 300 | -0.0002 | -0.0000 | 0.0000 | -0.0000 | 0.2000 | 0.9233 | 0.0000 | 0.0000 | 0.1933 |
| test | artist_bootstrap | hcoef17_guard_cov2_n10_gap0p1_cap0p03_w0p25 | guarded_move | 300 | -0.0003 | -0.0000 | 0.0000 | -0.0000 | 0.3467 | 0.9200 | 0.0000 | 0.0000 | 0.3367 |
| test | artist_bootstrap | hcoef17_guard_cov2_n10_gap0p1_cap0p05_w0p1 | guarded_move | 300 | -0.0002 | -0.0000 | 0.0000 | -0.0000 | 0.2500 | 0.9033 | 0.0000 | 0.0000 | 0.2400 |
| test | artist_bootstrap | hcoef17_guard_cov2_n10_gap0p15_cap0p03_w0p1 | guarded_move | 300 | -0.0002 | -0.0000 | 0.0000 | -0.0000 | 0.2000 | 0.9400 | 0.0000 | 0.0000 | 0.1967 |
| test | artist_bootstrap | hcoef17_guard_cov2_n10_gap0p15_cap0p03_w0p25 | guarded_move | 300 | -0.0003 | -0.0000 | 0.0000 | -0.0000 | 0.3467 | 0.9367 | 0.0000 | 0.0000 | 0.3400 |
| test | artist_bootstrap | hcoef17_guard_cov2_n10_gap0p15_cap0p05_w0p1 | guarded_move | 300 | -0.0002 | -0.0000 | 0.0000 | -0.0000 | 0.2500 | 0.9333 | 0.0000 | 0.0000 | 0.2433 |
| test | artist_bootstrap | hcoef17_guard_cov2_n20_gap0p05_cap0p03_w0p1 | guarded_move | 300 | -0.0001 | -0.0000 | 0.0000 | -0.0000 | 0.1600 | 0.9233 | 0.0000 | 0.0000 | 0.1567 |
| test | artist_bootstrap | hcoef17_guard_cov2_n20_gap0p05_cap0p03_w0p25 | guarded_move | 300 | -0.0003 | -0.0000 | 0.0000 | -0.0000 | 0.2733 | 0.8967 | 0.0000 | 0.0000 | 0.2700 |
| test | artist_bootstrap | hcoef17_guard_cov2_n20_gap0p05_cap0p05_w0p1 | guarded_move | 300 | -0.0002 | -0.0000 | 0.0000 | -0.0000 | 0.1833 | 0.9333 | 0.0000 | 0.0000 | 0.1800 |
| test | artist_bootstrap | hcoef17_guard_cov2_n20_gap0p05_cap0p05_w0p25 | guarded_move | 300 | -0.0003 | -0.0000 | 0.0000 | -0.0000 | 0.3300 | 0.9067 | 0.0000 | 0.0000 | 0.3267 |
| test | artist_bootstrap | hcoef17_guard_cov2_n20_gap0p1_cap0p03_w0p1 | guarded_move | 300 | -0.0002 | -0.0000 | 0.0000 | -0.0000 | 0.2000 | 0.9233 | 0.0000 | 0.0000 | 0.1933 |
| test | artist_bootstrap | hcoef17_guard_cov2_n20_gap0p1_cap0p03_w0p25 | guarded_move | 300 | -0.0003 | -0.0000 | 0.0000 | -0.0000 | 0.3467 | 0.9200 | 0.0000 | 0.0000 | 0.3367 |
| test | artist_bootstrap | hcoef17_guard_cov2_n20_gap0p1_cap0p05_w0p1 | guarded_move | 300 | -0.0002 | -0.0000 | 0.0000 | -0.0000 | 0.2500 | 0.9033 | 0.0000 | 0.0000 | 0.2400 |
| test | artist_bootstrap | hcoef17_guard_cov2_n20_gap0p15_cap0p03_w0p1 | guarded_move | 300 | -0.0002 | -0.0000 | 0.0000 | -0.0000 | 0.2000 | 0.9400 | 0.0000 | 0.0000 | 0.1967 |
| test | artist_bootstrap | hcoef17_guard_cov2_n20_gap0p15_cap0p05_w0p1 | guarded_move | 300 | -0.0002 | -0.0000 | 0.0000 | -0.0000 | 0.2500 | 0.9333 | 0.0000 | 0.0000 | 0.2433 |
| test | row_bootstrap | hcoef17_guard_agree_gap0p15_cap0p05_w0p5 | guarded_move | 300 | 0.0011 | -0.0003 | 0.0010 | -0.0011 | 0.3833 | 0.6700 | 0.3133 | 0.0733 | 0.4500 |
| test | row_bootstrap | current_70_30 | baseline | 300 | -0.0004 | 0.0018 | -0.0063 | 0.0008 | 0.5433 | 0.0300 | 0.5967 | 0.0067 | 0.3400 |
| test | row_bootstrap | hcoef_stable | baseline | 300 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| test | row_bootstrap | ppv8_service_proxy | component | 300 | 0.0240 | 0.0087 | 0.0553 | 0.0042 | 0.0067 | 0.1500 | 0.2633 | 0.0000 | 0.1000 |
| test | row_bootstrap | hcoef17_guard_cov2_n10_gap0p05_cap0p03_w0p1 | guarded_move | 300 | -0.0001 | -0.0000 | 0.0000 | -0.0000 | 0.1600 | 0.8833 | 0.0000 | 0.0000 | 0.1600 |
| test | row_bootstrap | hcoef17_guard_cov2_n10_gap0p05_cap0p03_w0p25 | guarded_move | 300 | -0.0003 | -0.0000 | 0.0000 | -0.0000 | 0.2633 | 0.8467 | 0.0000 | 0.0000 | 0.2600 |
| test | row_bootstrap | hcoef17_guard_cov2_n10_gap0p05_cap0p05_w0p1 | guarded_move | 300 | -0.0002 | -0.0000 | 0.0000 | -0.0000 | 0.1933 | 0.8867 | 0.0000 | 0.0000 | 0.1933 |
| test | row_bootstrap | hcoef17_guard_cov2_n10_gap0p05_cap0p05_w0p25 | guarded_move | 300 | -0.0003 | -0.0000 | 0.0000 | -0.0000 | 0.2967 | 0.8567 | 0.0000 | 0.0000 | 0.2933 |
| test | row_bootstrap | hcoef17_guard_cov2_n10_gap0p1_cap0p03_w0p1 | guarded_move | 300 | -0.0002 | -0.0000 | 0.0000 | -0.0000 | 0.1967 | 0.8900 | 0.0000 | 0.0000 | 0.1833 |
| test | row_bootstrap | hcoef17_guard_cov2_n10_gap0p1_cap0p03_w0p25 | guarded_move | 300 | -0.0004 | -0.0000 | 0.0000 | -0.0000 | 0.3167 | 0.8667 | 0.0000 | 0.0000 | 0.2900 |
| test | row_bootstrap | hcoef17_guard_cov2_n10_gap0p1_cap0p05_w0p1 | guarded_move | 300 | -0.0003 | -0.0000 | 0.0000 | -0.0000 | 0.2433 | 0.8667 | 0.0000 | 0.0000 | 0.2267 |
| test | row_bootstrap | hcoef17_guard_cov2_n10_gap0p15_cap0p03_w0p1 | guarded_move | 300 | -0.0002 | -0.0000 | 0.0000 | -0.0000 | 0.1967 | 0.9267 | 0.0000 | 0.0000 | 0.1867 |
| test | row_bootstrap | hcoef17_guard_cov2_n10_gap0p15_cap0p03_w0p25 | guarded_move | 300 | -0.0004 | -0.0000 | 0.0000 | -0.0000 | 0.3167 | 0.9167 | 0.0000 | 0.0000 | 0.3033 |
| test | row_bootstrap | hcoef17_guard_cov2_n10_gap0p15_cap0p05_w0p1 | guarded_move | 300 | -0.0003 | -0.0000 | 0.0000 | -0.0000 | 0.2433 | 0.9133 | 0.0000 | 0.0000 | 0.2300 |
| test | row_bootstrap | hcoef17_guard_cov2_n20_gap0p05_cap0p03_w0p1 | guarded_move | 300 | -0.0001 | -0.0000 | 0.0000 | -0.0000 | 0.1600 | 0.8833 | 0.0000 | 0.0000 | 0.1600 |
| test | row_bootstrap | hcoef17_guard_cov2_n20_gap0p05_cap0p03_w0p25 | guarded_move | 300 | -0.0003 | -0.0000 | 0.0000 | -0.0000 | 0.2633 | 0.8467 | 0.0000 | 0.0000 | 0.2600 |
| test | row_bootstrap | hcoef17_guard_cov2_n20_gap0p05_cap0p05_w0p1 | guarded_move | 300 | -0.0002 | -0.0000 | 0.0000 | -0.0000 | 0.1933 | 0.8867 | 0.0000 | 0.0000 | 0.1933 |

_Only first 40 of 92 rows shown._

## 7. 0604 PP-V8/HCOEF 승패 구간

| svc_coverage_tier | gap_band | winner | n |
| --- | --- | --- | --- |
| fallback_global | gap_020_plus | hcoef_better_or_tie | 7 |
| fallback_global | gap_020_plus | ppv8_better | 11 |
| high_n | gap_000_003 | hcoef_better_or_tie | 4 |
| high_n | gap_000_003 | ppv8_better | 1 |
| high_n | gap_003_005 | hcoef_better_or_tie | 1 |
| high_n | gap_003_005 | ppv8_better | 2 |
| high_n | gap_005_010 | ppv8_better | 4 |
| high_n | gap_010_020 | hcoef_better_or_tie | 7 |
| high_n | gap_010_020 | ppv8_better | 18 |
| high_n | gap_020_plus | hcoef_better_or_tie | 8 |
| high_n | gap_020_plus | ppv8_better | 42 |
| low_n | gap_000_003 | hcoef_better_or_tie | 44 |
| low_n | gap_000_003 | ppv8_better | 34 |
| low_n | gap_003_005 | hcoef_better_or_tie | 26 |
| low_n | gap_003_005 | ppv8_better | 14 |
| low_n | gap_005_010 | hcoef_better_or_tie | 61 |
| low_n | gap_005_010 | ppv8_better | 39 |
| low_n | gap_010_020 | hcoef_better_or_tie | 43 |
| low_n | gap_010_020 | ppv8_better | 43 |
| low_n | gap_020_plus | hcoef_better_or_tie | 114 |
| low_n | gap_020_plus | ppv8_better | 151 |
| medium_n | gap_000_003 | hcoef_better_or_tie | 28 |
| medium_n | gap_000_003 | ppv8_better | 8 |
| medium_n | gap_003_005 | hcoef_better_or_tie | 8 |
| medium_n | gap_003_005 | ppv8_better | 4 |
| medium_n | gap_005_010 | hcoef_better_or_tie | 14 |
| medium_n | gap_005_010 | ppv8_better | 7 |
| medium_n | gap_010_020 | hcoef_better_or_tie | 12 |
| medium_n | gap_010_020 | ppv8_better | 5 |
| medium_n | gap_020_plus | hcoef_better_or_tie | 19 |
| medium_n | gap_020_plus | ppv8_better | 50 |

## 8. 구간별 오차 요약

| split | candidate | segment_col | segment_value | n | MdAPE | MAPE | p95_APE | median_residual_log | policy_apply_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_ex50 | current_70_30 | gap_band | gap_020_plus | 402 | 0.4302 | 0.5054 | 1.0000 | 0.2961 | 1.0000 |
| 0604_ex50 | hcoef17_guard_agree_gap0p15_cap0p05_w0p5 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.0000 |
| 0604_ex50 | hcoef17_guard_cov1_n10_gap0p05_cap0p03_w0p1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.0000 |
| 0604_ex50 | hcoef17_guard_cov1_n10_gap0p05_cap0p03_w0p25 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.0000 |
| 0604_ex50 | hcoef17_guard_cov1_n10_gap0p05_cap0p05_w0p1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.0000 |
| 0604_ex50 | hcoef17_guard_cov1_n10_gap0p05_cap0p05_w0p25 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.0000 |
| 0604_ex50 | hcoef17_guard_cov1_n20_gap0p05_cap0p05_w0p25 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.0000 |
| 0604_ex50 | hcoef17_guard_cov1_n20_gap0p15_cap0p03_w0p25 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.0000 |
| 0604_ex50 | hcoef17_guard_cov1_n20_gap0p15_cap0p05_w0p25 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.0000 |
| 0604_ex50 | hcoef_stable | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 1.0000 |
| 0604_ex50 | ppv8_service_proxy | gap_band | gap_020_plus | 402 | 0.3131 | 0.4234 | 1.1510 | 0.1623 | 1.0000 |
| 0604_ex50 | current_70_30 | gap_band | gap_010_020 | 128 | 0.2248 | 0.3419 | 0.8656 | -0.0556 | 1.0000 |
| 0604_ex50 | hcoef17_guard_cov1_n10_gap0p05_cap0p03_w0p1 | gap_band | gap_010_020 | 128 | 0.2255 | 0.3393 | 0.8728 | -0.0465 | 0.0000 |
| 0604_ex50 | hcoef17_guard_cov1_n10_gap0p05_cap0p03_w0p25 | gap_band | gap_010_020 | 128 | 0.2255 | 0.3393 | 0.8728 | -0.0465 | 0.0000 |
| 0604_ex50 | hcoef17_guard_cov1_n10_gap0p05_cap0p05_w0p1 | gap_band | gap_010_020 | 128 | 0.2255 | 0.3393 | 0.8728 | -0.0465 | 0.0000 |
| 0604_ex50 | hcoef17_guard_cov1_n10_gap0p05_cap0p05_w0p25 | gap_band | gap_010_020 | 128 | 0.2255 | 0.3393 | 0.8728 | -0.0465 | 0.0000 |
| 0604_ex50 | hcoef17_guard_cov1_n20_gap0p05_cap0p05_w0p25 | gap_band | gap_010_020 | 128 | 0.2255 | 0.3393 | 0.8728 | -0.0465 | 0.0000 |
| 0604_ex50 | hcoef_stable | gap_band | gap_010_020 | 128 | 0.2255 | 0.3393 | 0.8728 | -0.0465 | 1.0000 |
| 0604_ex50 | hcoef17_guard_cov1_n20_gap0p15_cap0p03_w0p25 | gap_band | gap_010_020 | 128 | 0.2255 | 0.3383 | 0.8728 | -0.0390 | 0.1875 |
| 0604_ex50 | hcoef17_guard_cov1_n20_gap0p15_cap0p05_w0p25 | gap_band | gap_010_020 | 128 | 0.2255 | 0.3376 | 0.8728 | -0.0340 | 0.1875 |
| 0604_ex50 | hcoef17_guard_agree_gap0p15_cap0p05_w0p5 | gap_band | gap_010_020 | 128 | 0.2213 | 0.3370 | 0.8729 | -0.0215 | 0.5781 |
| 0604_ex50 | ppv8_service_proxy | gap_band | gap_010_020 | 128 | 0.2540 | 0.3269 | 0.7844 | 0.0520 | 1.0000 |
| 0604_ex50 | ppv8_service_proxy | gap_band | gap_005_010 | 125 | 0.1764 | 0.2618 | 0.7685 | 0.0806 | 1.0000 |
| 0604_ex50 | current_70_30 | gap_band | gap_005_010 | 125 | 0.1531 | 0.2572 | 0.9461 | 0.0641 | 1.0000 |
| 0604_ex50 | hcoef17_guard_agree_gap0p15_cap0p05_w0p5 | gap_band | gap_005_010 | 125 | 0.1528 | 0.2547 | 0.9044 | 0.0520 | 1.0000 |
| 0604_ex50 | hcoef17_guard_cov1_n10_gap0p05_cap0p03_w0p1 | gap_band | gap_005_010 | 125 | 0.1498 | 0.2514 | 0.9526 | 0.0403 | 0.0000 |
| 0604_ex50 | hcoef17_guard_cov1_n10_gap0p05_cap0p03_w0p25 | gap_band | gap_005_010 | 125 | 0.1498 | 0.2514 | 0.9526 | 0.0403 | 0.0000 |
| 0604_ex50 | hcoef17_guard_cov1_n10_gap0p05_cap0p05_w0p1 | gap_band | gap_005_010 | 125 | 0.1498 | 0.2514 | 0.9526 | 0.0403 | 0.0000 |
| 0604_ex50 | hcoef17_guard_cov1_n10_gap0p05_cap0p05_w0p25 | gap_band | gap_005_010 | 125 | 0.1498 | 0.2514 | 0.9526 | 0.0403 | 0.0000 |
| 0604_ex50 | hcoef17_guard_cov1_n20_gap0p05_cap0p05_w0p25 | gap_band | gap_005_010 | 125 | 0.1498 | 0.2514 | 0.9526 | 0.0403 | 0.0000 |
| 0604_ex50 | hcoef_stable | gap_band | gap_005_010 | 125 | 0.1498 | 0.2514 | 0.9526 | 0.0403 | 1.0000 |
| 0604_ex50 | hcoef17_guard_cov1_n20_gap0p15_cap0p03_w0p25 | gap_band | gap_005_010 | 125 | 0.1436 | 0.2510 | 0.9406 | 0.0403 | 0.1520 |
| 0604_ex50 | hcoef17_guard_cov1_n20_gap0p15_cap0p05_w0p25 | gap_band | gap_005_010 | 125 | 0.1436 | 0.2506 | 0.9327 | 0.0403 | 0.1520 |
| 0604_ex50 | current_70_30 | gap_band | gap_000_003 | 119 | 0.1066 | 0.1953 | 0.5444 | 0.0401 | 1.0000 |
| 0604_ex50 | ppv8_service_proxy | gap_band | gap_000_003 | 119 | 0.1162 | 0.1942 | 0.5405 | 0.0395 | 1.0000 |
| 0604_ex50 | ppv8_service_proxy | gap_band | gap_003_005 | 55 | 0.1039 | 0.1925 | 0.4983 | 0.0427 | 1.0000 |
| 0604_ex50 | hcoef17_guard_agree_gap0p15_cap0p05_w0p5 | gap_band | gap_000_003 | 119 | 0.1079 | 0.1912 | 0.5353 | 0.0333 | 1.0000 |
| 0604_ex50 | current_70_30 | gap_band | gap_003_005 | 55 | 0.0809 | 0.1908 | 0.5325 | 0.0305 | 1.0000 |
| 0604_ex50 | hcoef17_guard_cov1_n10_gap0p05_cap0p03_w0p25 | gap_band | gap_000_003 | 119 | 0.1059 | 0.1893 | 0.5300 | 0.0303 | 0.3445 |
| 0604_ex50 | hcoef17_guard_cov1_n10_gap0p05_cap0p05_w0p25 | gap_band | gap_000_003 | 119 | 0.1059 | 0.1893 | 0.5300 | 0.0303 | 0.3445 |

## 9. 정책/계수 해석

| candidate | method | policy_type | gap | cap | weight | coverage_min | n_min | source_col | description |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef_stable | baseline | baseline |  |  |  |  |  | hcoef_stable | HCOEF 안정 후보 |
| current_70_30 | baseline | baseline |  |  |  |  |  | current_70_30 | 기존 70:30 기준 |
| ppv8_service_proxy | component | component |  |  |  |  |  | ppv8_service_proxy | PP-V8/service proxy |
| svc_numeric_seed_mean | component | component |  |  |  |  |  | svc_numeric_seed_mean | 유사 작품 기반 가격 피처 |
| hcoef17_guard_agree_gap0p03_cap0p02_w0p1 | guarded_move | agreement_only | 0.0300 | 0.0200 | 0.1000 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.03 이하일 때만 cap 0.02, weight 0.1로 이동. |
| hcoef17_guard_agree_gap0p03_cap0p02_w0p25 | guarded_move | agreement_only | 0.0300 | 0.0200 | 0.2500 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.03 이하일 때만 cap 0.02, weight 0.25로 이동. |
| hcoef17_guard_agree_gap0p03_cap0p02_w0p5 | guarded_move | agreement_only | 0.0300 | 0.0200 | 0.5000 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.03 이하일 때만 cap 0.02, weight 0.5로 이동. |
| hcoef17_guard_agree_gap0p03_cap0p03_w0p1 | guarded_move | agreement_only | 0.0300 | 0.0300 | 0.1000 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.03 이하일 때만 cap 0.03, weight 0.1로 이동. |
| hcoef17_guard_agree_gap0p03_cap0p03_w0p25 | guarded_move | agreement_only | 0.0300 | 0.0300 | 0.2500 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.03 이하일 때만 cap 0.03, weight 0.25로 이동. |
| hcoef17_guard_agree_gap0p03_cap0p03_w0p5 | guarded_move | agreement_only | 0.0300 | 0.0300 | 0.5000 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.03 이하일 때만 cap 0.03, weight 0.5로 이동. |
| hcoef17_guard_agree_gap0p03_cap0p05_w0p1 | guarded_move | agreement_only | 0.0300 | 0.0500 | 0.1000 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.03 이하일 때만 cap 0.05, weight 0.1로 이동. |
| hcoef17_guard_agree_gap0p03_cap0p05_w0p25 | guarded_move | agreement_only | 0.0300 | 0.0500 | 0.2500 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.03 이하일 때만 cap 0.05, weight 0.25로 이동. |
| hcoef17_guard_agree_gap0p03_cap0p05_w0p5 | guarded_move | agreement_only | 0.0300 | 0.0500 | 0.5000 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.03 이하일 때만 cap 0.05, weight 0.5로 이동. |
| hcoef17_guard_agree_gap0p05_cap0p02_w0p1 | guarded_move | agreement_only | 0.0500 | 0.0200 | 0.1000 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.05 이하일 때만 cap 0.02, weight 0.1로 이동. |
| hcoef17_guard_agree_gap0p05_cap0p02_w0p25 | guarded_move | agreement_only | 0.0500 | 0.0200 | 0.2500 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.05 이하일 때만 cap 0.02, weight 0.25로 이동. |
| hcoef17_guard_agree_gap0p05_cap0p02_w0p5 | guarded_move | agreement_only | 0.0500 | 0.0200 | 0.5000 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.05 이하일 때만 cap 0.02, weight 0.5로 이동. |
| hcoef17_guard_agree_gap0p05_cap0p03_w0p1 | guarded_move | agreement_only | 0.0500 | 0.0300 | 0.1000 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.05 이하일 때만 cap 0.03, weight 0.1로 이동. |
| hcoef17_guard_agree_gap0p05_cap0p03_w0p25 | guarded_move | agreement_only | 0.0500 | 0.0300 | 0.2500 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.05 이하일 때만 cap 0.03, weight 0.25로 이동. |
| hcoef17_guard_agree_gap0p05_cap0p03_w0p5 | guarded_move | agreement_only | 0.0500 | 0.0300 | 0.5000 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.05 이하일 때만 cap 0.03, weight 0.5로 이동. |
| hcoef17_guard_agree_gap0p05_cap0p05_w0p1 | guarded_move | agreement_only | 0.0500 | 0.0500 | 0.1000 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.05 이하일 때만 cap 0.05, weight 0.1로 이동. |
| hcoef17_guard_agree_gap0p05_cap0p05_w0p25 | guarded_move | agreement_only | 0.0500 | 0.0500 | 0.2500 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.05 이하일 때만 cap 0.05, weight 0.25로 이동. |
| hcoef17_guard_agree_gap0p05_cap0p05_w0p5 | guarded_move | agreement_only | 0.0500 | 0.0500 | 0.5000 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.05 이하일 때만 cap 0.05, weight 0.5로 이동. |
| hcoef17_guard_agree_gap0p1_cap0p02_w0p1 | guarded_move | agreement_only | 0.1000 | 0.0200 | 0.1000 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.1 이하일 때만 cap 0.02, weight 0.1로 이동. |
| hcoef17_guard_agree_gap0p1_cap0p02_w0p25 | guarded_move | agreement_only | 0.1000 | 0.0200 | 0.2500 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.1 이하일 때만 cap 0.02, weight 0.25로 이동. |
| hcoef17_guard_agree_gap0p1_cap0p02_w0p5 | guarded_move | agreement_only | 0.1000 | 0.0200 | 0.5000 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.1 이하일 때만 cap 0.02, weight 0.5로 이동. |
| hcoef17_guard_agree_gap0p1_cap0p03_w0p1 | guarded_move | agreement_only | 0.1000 | 0.0300 | 0.1000 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.1 이하일 때만 cap 0.03, weight 0.1로 이동. |
| hcoef17_guard_agree_gap0p1_cap0p03_w0p25 | guarded_move | agreement_only | 0.1000 | 0.0300 | 0.2500 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.1 이하일 때만 cap 0.03, weight 0.25로 이동. |
| hcoef17_guard_agree_gap0p1_cap0p03_w0p5 | guarded_move | agreement_only | 0.1000 | 0.0300 | 0.5000 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.1 이하일 때만 cap 0.03, weight 0.5로 이동. |
| hcoef17_guard_agree_gap0p1_cap0p05_w0p1 | guarded_move | agreement_only | 0.1000 | 0.0500 | 0.1000 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.1 이하일 때만 cap 0.05, weight 0.1로 이동. |
| hcoef17_guard_agree_gap0p1_cap0p05_w0p25 | guarded_move | agreement_only | 0.1000 | 0.0500 | 0.2500 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.1 이하일 때만 cap 0.05, weight 0.25로 이동. |
| hcoef17_guard_agree_gap0p1_cap0p05_w0p5 | guarded_move | agreement_only | 0.1000 | 0.0500 | 0.5000 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.1 이하일 때만 cap 0.05, weight 0.5로 이동. |
| hcoef17_guard_agree_gap0p15_cap0p02_w0p1 | guarded_move | agreement_only | 0.1500 | 0.0200 | 0.1000 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.15 이하일 때만 cap 0.02, weight 0.1로 이동. |
| hcoef17_guard_agree_gap0p15_cap0p02_w0p25 | guarded_move | agreement_only | 0.1500 | 0.0200 | 0.2500 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.15 이하일 때만 cap 0.02, weight 0.25로 이동. |
| hcoef17_guard_agree_gap0p15_cap0p02_w0p5 | guarded_move | agreement_only | 0.1500 | 0.0200 | 0.5000 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.15 이하일 때만 cap 0.02, weight 0.5로 이동. |
| hcoef17_guard_agree_gap0p15_cap0p03_w0p1 | guarded_move | agreement_only | 0.1500 | 0.0300 | 0.1000 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.15 이하일 때만 cap 0.03, weight 0.1로 이동. |
| hcoef17_guard_agree_gap0p15_cap0p03_w0p25 | guarded_move | agreement_only | 0.1500 | 0.0300 | 0.2500 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.15 이하일 때만 cap 0.03, weight 0.25로 이동. |
| hcoef17_guard_agree_gap0p15_cap0p03_w0p5 | guarded_move | agreement_only | 0.1500 | 0.0300 | 0.5000 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.15 이하일 때만 cap 0.03, weight 0.5로 이동. |
| hcoef17_guard_agree_gap0p15_cap0p05_w0p1 | guarded_move | agreement_only | 0.1500 | 0.0500 | 0.1000 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.15 이하일 때만 cap 0.05, weight 0.1로 이동. |
| hcoef17_guard_agree_gap0p15_cap0p05_w0p25 | guarded_move | agreement_only | 0.1500 | 0.0500 | 0.2500 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.15 이하일 때만 cap 0.05, weight 0.25로 이동. |
| hcoef17_guard_agree_gap0p15_cap0p05_w0p5 | guarded_move | agreement_only | 0.1500 | 0.0500 | 0.5000 | 0.0000 | 0.0000 |  | PP-V8과 HCOEF 안정 후보 차이가 0.15 이하일 때만 cap 0.05, weight 0.5로 이동. |

## 10. 해석

- `ppv8_minus_stable`는 PP-V8 예측값과 HCOEF 안정 후보의 로그 가격 차이임.
- 정책 후보는 이 차이를 그대로 쓰지 않고 `cap`으로 자른 뒤 `weight`만큼만 반영함.
- `abs_ppv8_stable_gap`은 두 모델이 얼마나 다르게 보는지를 의미함. 차이가 큰 구간에서는 PP-V8을 신뢰하지 않고 HCOEF 안정 후보를 유지함.
- `svc_coverage_tier`와 `svc_group_n`은 유사 작품 기반 가격 피처의 신뢰도를 나타냄. 표본이 많고 coverage가 높을 때만 PP-V8 이동을 허용하는 후보를 별도 비교함.
- 이 실험에서 운영 후보가 나오지 않으면, PP-V8은 점 예측 교체보다 신뢰도/가격 범위/risk guard에 쓰는 것이 더 타당함.

## 11. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/policy_map.csv`
- `outputs/residual_analysis.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `outputs/service_feature_gap_audit.csv`
- `outputs/error_segment_summary.csv`
- `outputs/selected_candidates.csv`