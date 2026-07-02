# PP-HCOEF18 Warm quantile-risk guarded refinement

- 작성일: 2026-06-08 02:27
- 목적: HCOEF 안정 후보를 기본값으로 유지하면서 quantile width 위험도에 따라 보정폭 축소 또는 PP-V8 제한 이동이 가능한지 검증
- 기준 후보: `hcoef2_size_reliability_cap005_s050`
- 선택 기준: validation과 bootstrap 우선, fixed test와 0604는 확인용
- 금지 기준: test/0604 residual을 보고 threshold, weight, cap을 만들지 않음

## 1. validation에서 고정한 quantile width 경계

| qwidth_q33 | qwidth_q50 | qwidth_q66 | qwidth_q80 | pred_spread_q66 | pred_spread_q80 |
| --- | --- | --- | --- | --- | --- |
| 1.2116 | 1.3780 | 1.5114 | 1.7065 | 0.1661 | 0.2397 |

## 2. 실행 결론

- PP-L10 quantile width는 validation/test/0604에 공통으로 붙일 수 있었음.
- 이 실험은 quantile width를 가격 예측값 자체로 쓰기보다 HCOEF 보정폭을 줄이는 risk gate로 사용함.
- low quantile width 구간에서는 PP-V8 방향 제한 이동 후보를 비교함.
- high quantile width 또는 모델 간 spread가 큰 구간에서는 HCOEF 잔차 보정폭을 `current_70_30` 방향으로 줄이는 후보를 비교함.
- 후보 채택은 validation/OOF성 bootstrap gate와 fixed test p95 guard를 동시에 봄.

## 3. validation 상위 후보

| candidate | method | n | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable | policy_apply_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef18_qrisk_shrink_current_qwidth_q80_cap0p03_w0p75 | quantile_guard | 519 | 0.1253 | 0.2095 | 0.6481 | 0.3271 | -0.0006 | 0.0013 | 0.0002 | 0.2004 |
| hcoef18_qrisk_shrink_current_qwidth_q80_cap0p05_w0p75 | quantile_guard | 519 | 0.1253 | 0.2095 | 0.6481 | 0.3271 | -0.0006 | 0.0013 | 0.0002 | 0.2004 |
| hcoef18_qrisk_shrink_current_qwidth_q66_cap0p03_w0p75 | quantile_guard | 519 | 0.1257 | 0.2095 | 0.6502 | 0.3271 | -0.0003 | 0.0013 | 0.0022 | 0.3410 |
| hcoef18_qrisk_shrink_current_qwidth_q66_cap0p05_w0p75 | quantile_guard | 519 | 0.1257 | 0.2095 | 0.6502 | 0.3271 | -0.0003 | 0.0013 | 0.0022 | 0.3410 |
| hcoef_stable | baseline | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p05_w0p10 | quantile_guard | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0.2486 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p02_w0p25 | quantile_guard | 519 | 0.1260 | 0.2083 | 0.6479 | 0.3253 | 0.0000 | 0.0001 | 0.0000 | 0.2486 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p05_w0p10 | quantile_guard | 519 | 0.1260 | 0.2083 | 0.6479 | 0.3252 | 0.0000 | 0.0001 | 0.0000 | 0.1830 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p03_w0p25 | quantile_guard | 519 | 0.1260 | 0.2083 | 0.6479 | 0.3253 | 0.0000 | 0.0001 | 0.0000 | 0.2486 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p05_w0p25 | quantile_guard | 519 | 0.1260 | 0.2083 | 0.6479 | 0.3253 | 0.0000 | 0.0001 | 0.0000 | 0.2486 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p15_cap0p05_w0p10 | quantile_guard | 519 | 0.1260 | 0.2083 | 0.6479 | 0.3252 | 0.0000 | 0.0001 | 0.0000 | 0.4355 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p15_cap0p05_w0p10 | quantile_guard | 519 | 0.1260 | 0.2083 | 0.6479 | 0.3252 | 0.0000 | 0.0001 | 0.0000 | 0.3006 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p10_cap0p05_w0p10 | quantile_guard | 519 | 0.1260 | 0.2083 | 0.6479 | 0.3252 | 0.0000 | 0.0001 | 0.0000 | 0.2601 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p10_cap0p05_w0p10 | quantile_guard | 519 | 0.1260 | 0.2083 | 0.6479 | 0.3252 | 0.0000 | 0.0001 | 0.0000 | 0.3699 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p15_cap0p02_w0p25 | quantile_guard | 519 | 0.1260 | 0.2084 | 0.6479 | 0.3252 | 0.0000 | 0.0001 | 0.0000 | 0.4355 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p02_w0p25 | quantile_guard | 519 | 0.1260 | 0.2084 | 0.6479 | 0.3253 | 0.0000 | 0.0002 | 0.0000 | 0.1830 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p10_cap0p02_w0p25 | quantile_guard | 519 | 0.1260 | 0.2084 | 0.6479 | 0.3252 | 0.0000 | 0.0002 | 0.0000 | 0.3699 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p02_w0p50 | quantile_guard | 519 | 0.1260 | 0.2084 | 0.6482 | 0.3254 | 0.0000 | 0.0002 | 0.0003 | 0.2486 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p15_cap0p02_w0p25 | quantile_guard | 519 | 0.1260 | 0.2084 | 0.6479 | 0.3253 | 0.0000 | 0.0002 | 0.0000 | 0.3006 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p03_w0p25 | quantile_guard | 519 | 0.1260 | 0.2084 | 0.6479 | 0.3253 | 0.0000 | 0.0002 | 0.0000 | 0.1830 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p10_cap0p02_w0p25 | quantile_guard | 519 | 0.1260 | 0.2084 | 0.6479 | 0.3253 | 0.0000 | 0.0002 | 0.0000 | 0.2601 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p15_cap0p03_w0p25 | quantile_guard | 519 | 0.1260 | 0.2084 | 0.6484 | 0.3252 | 0.0000 | 0.0002 | 0.0004 | 0.4355 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p05_w0p25 | quantile_guard | 519 | 0.1260 | 0.2084 | 0.6479 | 0.3253 | 0.0000 | 0.0002 | 0.0000 | 0.1830 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p15_cap0p03_w0p25 | quantile_guard | 519 | 0.1260 | 0.2084 | 0.6479 | 0.3253 | 0.0000 | 0.0002 | 0.0000 | 0.3006 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p10_cap0p03_w0p25 | quantile_guard | 519 | 0.1260 | 0.2085 | 0.6484 | 0.3252 | 0.0000 | 0.0003 | 0.0004 | 0.3699 |

_Only first 25 of 101 rows shown._

## 4. fixed test 상위 후보

| candidate | method | n | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable | policy_apply_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p03_w0p50 | quantile_guard | 607 | 0.1361 | 0.2731 | 0.8064 | 0.3987 | -0.0027 | 0.0001 | 0.0000 | 0.1845 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p05_w0p50 | quantile_guard | 607 | 0.1361 | 0.2732 | 0.8064 | 0.3987 | -0.0027 | 0.0002 | 0.0000 | 0.1845 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p02_w0p50 | quantile_guard | 607 | 0.1383 | 0.2731 | 0.8064 | 0.3988 | -0.0005 | 0.0001 | 0.0000 | 0.1153 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p03_w0p50 | quantile_guard | 607 | 0.1383 | 0.2731 | 0.8064 | 0.3988 | -0.0005 | 0.0001 | 0.0000 | 0.1153 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p05_w0p50 | quantile_guard | 607 | 0.1383 | 0.2732 | 0.8064 | 0.3988 | -0.0005 | 0.0002 | 0.0000 | 0.1153 |
| hcoef18_qrisk_shrink_current_qwidth_q66_cap0p03_w0p25 | quantile_guard | 607 | 0.1384 | 0.2733 | 0.8097 | 0.3989 | -0.0004 | 0.0003 | 0.0034 | 0.3987 |
| hcoef18_qrisk_shrink_current_qwidth_q66_cap0p05_w0p25 | quantile_guard | 607 | 0.1384 | 0.2733 | 0.8097 | 0.3989 | -0.0004 | 0.0003 | 0.0034 | 0.3987 |
| hcoef18_qrisk_shrink_current_spread_qwidth_q66_cap0p03_w0p25 | quantile_guard | 607 | 0.1384 | 0.2734 | 0.8097 | 0.3989 | -0.0004 | 0.0004 | 0.0034 | 0.4992 |
| hcoef18_qrisk_shrink_current_spread_qwidth_q66_cap0p05_w0p25 | quantile_guard | 607 | 0.1384 | 0.2734 | 0.8097 | 0.3989 | -0.0004 | 0.0004 | 0.0034 | 0.4992 |
| hcoef18_qrisk_shrink_current_qwidth_q66_cap0p02_w0p50 | quantile_guard | 607 | 0.1384 | 0.2736 | 0.8154 | 0.3989 | -0.0004 | 0.0006 | 0.0090 | 0.3987 |
| hcoef18_qrisk_shrink_current_spread_qwidth_q66_cap0p02_w0p50 | quantile_guard | 607 | 0.1384 | 0.2737 | 0.8160 | 0.3989 | -0.0004 | 0.0007 | 0.0096 | 0.4992 |
| hcoef18_qrisk_shrink_current_qwidth_q66_cap0p03_w0p50 | quantile_guard | 607 | 0.1384 | 0.2737 | 0.8162 | 0.3989 | -0.0004 | 0.0007 | 0.0098 | 0.3987 |
| hcoef18_qrisk_shrink_current_qwidth_q66_cap0p05_w0p50 | quantile_guard | 607 | 0.1384 | 0.2737 | 0.8162 | 0.3989 | -0.0004 | 0.0007 | 0.0098 | 0.3987 |
| hcoef18_qrisk_shrink_current_spread_qwidth_q80_cap0p02_w0p75 | quantile_guard | 607 | 0.1384 | 0.2738 | 0.8236 | 0.3990 | -0.0004 | 0.0008 | 0.0172 | 0.3904 |
| hcoef18_qrisk_shrink_current_spread_qwidth_q66_cap0p03_w0p50 | quantile_guard | 607 | 0.1384 | 0.2739 | 0.8169 | 0.3990 | -0.0004 | 0.0009 | 0.0106 | 0.4992 |
| hcoef18_qrisk_shrink_current_spread_qwidth_q66_cap0p05_w0p50 | quantile_guard | 607 | 0.1384 | 0.2739 | 0.8169 | 0.3990 | -0.0004 | 0.0009 | 0.0106 | 0.4992 |
| hcoef18_qrisk_shrink_current_qwidth_q66_cap0p02_w0p75 | quantile_guard | 607 | 0.1384 | 0.2739 | 0.8215 | 0.3989 | -0.0004 | 0.0009 | 0.0151 | 0.3987 |
| hcoef18_qrisk_shrink_current_spread_qwidth_q66_cap0p02_w0p75 | quantile_guard | 607 | 0.1384 | 0.2740 | 0.8236 | 0.3990 | -0.0004 | 0.0010 | 0.0172 | 0.4992 |
| hcoef18_qrisk_shrink_current_spread_qwidth_q80_cap0p03_w0p25 | quantile_guard | 607 | 0.1387 | 0.2733 | 0.8101 | 0.3989 | -0.0001 | 0.0003 | 0.0037 | 0.3904 |
| hcoef18_qrisk_shrink_current_spread_qwidth_q80_cap0p05_w0p25 | quantile_guard | 607 | 0.1387 | 0.2733 | 0.8101 | 0.3989 | -0.0001 | 0.0003 | 0.0037 | 0.3904 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p02_w0p10 | quantile_guard | 607 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | -0.0000 | 0.0000 | 0.1153 |
| hcoef_stable | baseline | 607 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p03_w0p10 | quantile_guard | 607 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0.1153 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p05_w0p10 | quantile_guard | 607 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0.1153 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p02_w0p50 | quantile_guard | 607 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0.1845 |

_Only first 25 of 101 rows shown._

## 5. 0604 stress test 상위 후보

| candidate | method | n | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable | policy_apply_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppv8_service_proxy | component | 829 | 0.2298 | 0.3359 | 0.9273 | 0.7124 | -0.0433 | -0.0385 | -0.0561 | 1.0000 |
| hcoef18_qrisk_shrink_current_spread_qwidth_q80_cap0p03_w0p50 | quantile_guard | 829 | 0.2715 | 0.3748 | 0.9866 | 1.3095 | -0.0016 | 0.0005 | 0.0031 | 0.6333 |
| hcoef18_qrisk_shrink_current_spread_qwidth_q80_cap0p05_w0p50 | quantile_guard | 829 | 0.2715 | 0.3748 | 0.9866 | 1.3095 | -0.0016 | 0.0005 | 0.0031 | 0.6333 |
| hcoef18_qrisk_adaptive_shrink0p03_ppv80p02 | quantile_guard | 829 | 0.2715 | 0.3749 | 0.9866 | 1.3095 | -0.0016 | 0.0005 | 0.0031 | 0.6936 |
| hcoef18_qrisk_adaptive_shrink0p05_ppv80p02 | quantile_guard | 829 | 0.2715 | 0.3749 | 0.9866 | 1.3095 | -0.0016 | 0.0005 | 0.0031 | 0.6936 |
| hcoef18_qrisk_adaptive_shrink0p03_ppv80p03 | quantile_guard | 829 | 0.2715 | 0.3749 | 0.9866 | 1.3095 | -0.0016 | 0.0005 | 0.0031 | 0.6936 |
| hcoef18_qrisk_adaptive_shrink0p05_ppv80p03 | quantile_guard | 829 | 0.2715 | 0.3749 | 0.9866 | 1.3095 | -0.0016 | 0.0005 | 0.0031 | 0.6936 |
| hcoef18_qrisk_shrink_current_spread_qwidth_q66_cap0p03_w0p50 | quantile_guard | 829 | 0.2715 | 0.3751 | 0.9869 | 1.3096 | -0.0016 | 0.0007 | 0.0034 | 0.7334 |
| hcoef18_qrisk_shrink_current_spread_qwidth_q66_cap0p05_w0p50 | quantile_guard | 829 | 0.2715 | 0.3751 | 0.9869 | 1.3096 | -0.0016 | 0.0007 | 0.0034 | 0.7334 |
| hcoef18_qrisk_shrink_current_spread_qwidth_q80_cap0p02_w0p50 | quantile_guard | 829 | 0.2727 | 0.3747 | 0.9866 | 1.3092 | -0.0003 | 0.0003 | 0.0031 | 0.6333 |
| hcoef18_qrisk_adaptive_shrink0p02_ppv80p02 | quantile_guard | 829 | 0.2727 | 0.3747 | 0.9866 | 1.3092 | -0.0003 | 0.0004 | 0.0031 | 0.6936 |
| hcoef18_qrisk_adaptive_shrink0p02_ppv80p03 | quantile_guard | 829 | 0.2727 | 0.3748 | 0.9866 | 1.3092 | -0.0003 | 0.0004 | 0.0031 | 0.6936 |
| hcoef18_qrisk_shrink_current_qwidth_q80_cap0p02_w0p50 | quantile_guard | 829 | 0.2727 | 0.3749 | 0.9834 | 1.3089 | -0.0003 | 0.0005 | -0.0001 | 0.3631 |
| hcoef18_qrisk_shrink_current_spread_qwidth_q66_cap0p02_w0p50 | quantile_guard | 829 | 0.2727 | 0.3749 | 0.9869 | 1.3092 | -0.0003 | 0.0005 | 0.0034 | 0.7334 |
| hcoef18_qrisk_shrink_current_qwidth_q66_cap0p02_w0p50 | quantile_guard | 829 | 0.2727 | 0.3753 | 0.9869 | 1.3091 | -0.0003 | 0.0009 | 0.0034 | 0.5862 |
| hcoef18_qrisk_shrink_current_spread_qwidth_q80_cap0p03_w0p25 | quantile_guard | 829 | 0.2730 | 0.3746 | 0.9859 | 1.3086 | -0.0000 | 0.0002 | 0.0024 | 0.6333 |
| hcoef18_qrisk_shrink_current_spread_qwidth_q80_cap0p05_w0p25 | quantile_guard | 829 | 0.2730 | 0.3746 | 0.9859 | 1.3086 | -0.0000 | 0.0002 | 0.0024 | 0.6333 |
| hcoef18_qrisk_shrink_current_qwidth_q80_cap0p03_w0p25 | quantile_guard | 829 | 0.2730 | 0.3747 | 0.9834 | 1.3085 | -0.0000 | 0.0003 | -0.0001 | 0.3631 |
| hcoef18_qrisk_shrink_current_qwidth_q80_cap0p05_w0p25 | quantile_guard | 829 | 0.2730 | 0.3747 | 0.9834 | 1.3085 | -0.0000 | 0.0003 | -0.0001 | 0.3631 |
| hcoef18_qrisk_shrink_current_spread_qwidth_q66_cap0p03_w0p25 | quantile_guard | 829 | 0.2730 | 0.3747 | 0.9859 | 1.3087 | -0.0000 | 0.0003 | 0.0024 | 0.7334 |
| hcoef18_qrisk_shrink_current_spread_qwidth_q66_cap0p05_w0p25 | quantile_guard | 829 | 0.2730 | 0.3747 | 0.9859 | 1.3087 | -0.0000 | 0.0003 | 0.0024 | 0.7334 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p02_w0p50 | quantile_guard | 829 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0410 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p03_w0p50 | quantile_guard | 829 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0410 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p02_w0p25 | quantile_guard | 829 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0410 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p03_w0p25 | quantile_guard | 829 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0410 |

_Only first 25 of 101 rows shown._

## 6. 후보 선택표

| candidate | method | validation_MdAPE | validation_MAPE | validation_p95_APE | validation_RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable | policy_apply_rate | test_MdAPE | test_MAPE | test_p95_APE | test_RMSE_log | test_delta_MdAPE_vs_stable | test_delta_MAPE_vs_stable | test_delta_p95_APE_vs_stable | stress0604_MdAPE | stress0604_MAPE | stress0604_p95_APE | validation_artist_bootstrap_all3_improve_prob | validation_row_bootstrap_all3_improve_prob | validation_artist_bootstrap_any2_improve_prob | validation_row_bootstrap_any2_improve_prob | validation_pass_2of3 | fixed_test_p95_guard | stress0604_p95_guard | fixed_test_2of3 | bootstrap_gate | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef18_qrisk_shrink_current_qwidth_q80_cap0p03_w0p75 | quantile_guard | 0.1253 | 0.2095 | 0.6481 | 0.3271 | -0.0006 | 0.0013 | 0.0002 | 0.2004 | 0.1389 | 0.2737 | 0.8237 | 0.3988 | 0.0001 | 0.0007 | 0.0174 | 0.2731 | 0.3754 | 0.9833 | 0.0000 | 0.0000 | 0.0000 | 0.0033 | False | False | True | False | False | 보류 |
| hcoef18_qrisk_shrink_current_qwidth_q80_cap0p05_w0p75 | quantile_guard | 0.1253 | 0.2095 | 0.6481 | 0.3271 | -0.0006 | 0.0013 | 0.0002 | 0.2004 | 0.1389 | 0.2737 | 0.8237 | 0.3988 | 0.0001 | 0.0007 | 0.0174 | 0.2731 | 0.3754 | 0.9833 | 0.0000 | 0.0000 | 0.0000 | 0.0033 | False | False | True | False | False | 보류 |
| hcoef18_qrisk_shrink_current_qwidth_q66_cap0p03_w0p75 | quantile_guard | 0.1257 | 0.2095 | 0.6502 | 0.3271 | -0.0003 | 0.0013 | 0.0022 | 0.3410 | 0.1388 | 0.2741 | 0.8226 | 0.3990 | 0.0000 | 0.0011 | 0.0163 | 0.2791 | 0.3763 | 0.9870 | 0.0000 | 0.0000 | 0.0300 | 0.0333 | False | False | False | False | False | 보류 |
| hcoef18_qrisk_shrink_current_qwidth_q66_cap0p05_w0p75 | quantile_guard | 0.1257 | 0.2095 | 0.6502 | 0.3271 | -0.0003 | 0.0013 | 0.0022 | 0.3410 | 0.1388 | 0.2741 | 0.8226 | 0.3990 | 0.0000 | 0.0011 | 0.0163 | 0.2791 | 0.3763 | 0.9870 | 0.0000 | 0.0000 | 0.0300 | 0.0333 | False | False | False | False | False | 보류 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p02_w0p50 | quantile_guard | 0.1260 | 0.2085 | 0.6482 | 0.3254 | 0.0000 | 0.0003 | 0.0003 | 0.1830 | 0.1383 | 0.2731 | 0.8064 | 0.3988 | -0.0005 | 0.0001 | 0.0000 | 0.2731 | 0.3743 | 0.9835 | 0.0000 | 0.0000 | 0.0633 | 0.0567 | False | True | True | True | False | 보류 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p03_w0p50 | quantile_guard | 0.1260 | 0.2086 | 0.6484 | 0.3254 | 0.0000 | 0.0004 | 0.0004 | 0.1830 | 0.1383 | 0.2731 | 0.8064 | 0.3988 | -0.0005 | 0.0001 | 0.0000 | 0.2731 | 0.3743 | 0.9835 | 0.0067 | 0.0000 | 0.0733 | 0.0433 | False | True | True | True | False | 보류 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p05_w0p50 | quantile_guard | 0.1260 | 0.2087 | 0.6484 | 0.3254 | 0.0000 | 0.0005 | 0.0004 | 0.1830 | 0.1383 | 0.2732 | 0.8064 | 0.3988 | -0.0005 | 0.0002 | 0.0000 | 0.2731 | 0.3743 | 0.9835 | 0.0067 | 0.0000 | 0.0767 | 0.0500 | False | True | True | True | False | 보류 |
| hcoef_stable | baseline | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0.2731 | 0.3744 | 0.9835 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | True | True | True | False | 보류 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p05_w0p10 | quantile_guard | 0.1260 | 0.2083 | 0.6479 | 0.3252 | 0.0000 | 0.0001 | 0.0000 | 0.1830 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0.2731 | 0.3744 | 0.9835 | 0.0033 | 0.0000 | 0.0533 | 0.0533 | False | True | True | True | False | 보류 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p02_w0p25 | quantile_guard | 0.1260 | 0.2084 | 0.6479 | 0.3253 | 0.0000 | 0.0002 | 0.0000 | 0.1830 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0.2731 | 0.3743 | 0.9835 | 0.0000 | 0.0000 | 0.0500 | 0.0433 | False | True | True | True | False | 보류 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p02_w0p50 | quantile_guard | 0.1260 | 0.2084 | 0.6482 | 0.3254 | 0.0000 | 0.0002 | 0.0003 | 0.2486 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0.2734 | 0.3746 | 0.9835 | 0.0100 | 0.0100 | 0.1800 | 0.1133 | False | True | True | True | False | 보류 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p03_w0p25 | quantile_guard | 0.1260 | 0.2084 | 0.6479 | 0.3253 | 0.0000 | 0.0002 | 0.0000 | 0.1830 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0.2731 | 0.3743 | 0.9835 | 0.0033 | 0.0000 | 0.0667 | 0.0533 | False | True | True | True | False | 보류 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p05_w0p25 | quantile_guard | 0.1260 | 0.2084 | 0.6479 | 0.3253 | 0.0000 | 0.0002 | 0.0000 | 0.1830 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0001 | 0.0000 | 0.2731 | 0.3743 | 0.9835 | 0.0033 | 0.0000 | 0.0867 | 0.0733 | False | True | True | True | False | 보류 |
| hcoef18_qrisk_shrink_current_qwidth_q80_cap0p03_w0p25 | quantile_guard | 0.1260 | 0.2086 | 0.6481 | 0.3258 | 0.0000 | 0.0004 | 0.0001 | 0.2004 | 0.1388 | 0.2732 | 0.8101 | 0.3988 | 0.0000 | 0.0002 | 0.0037 | 0.2730 | 0.3747 | 0.9834 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | False | True | False | False | 보류 |
| hcoef18_qrisk_shrink_current_qwidth_q80_cap0p05_w0p25 | quantile_guard | 0.1260 | 0.2086 | 0.6481 | 0.3258 | 0.0000 | 0.0004 | 0.0001 | 0.2004 | 0.1388 | 0.2732 | 0.8101 | 0.3988 | 0.0000 | 0.0002 | 0.0037 | 0.2730 | 0.3747 | 0.9834 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | False | True | False | False | 보류 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p05_w0p10 | quantile_guard | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0.2486 | 0.1389 | 0.2730 | 0.8064 | 0.3988 | 0.0001 | -0.0000 | 0.0000 | 0.2731 | 0.3744 | 0.9835 | 0.0067 | 0.0167 | 0.1433 | 0.1333 | False | True | True | True | False | 보류 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p02_w0p25 | quantile_guard | 0.1260 | 0.2083 | 0.6479 | 0.3253 | 0.0000 | 0.0001 | 0.0000 | 0.2486 | 0.1389 | 0.2730 | 0.8064 | 0.3988 | 0.0001 | -0.0000 | 0.0000 | 0.2734 | 0.3745 | 0.9835 | 0.0067 | 0.0133 | 0.1867 | 0.1100 | False | True | True | True | False | 보류 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p03_w0p25 | quantile_guard | 0.1260 | 0.2083 | 0.6479 | 0.3253 | 0.0000 | 0.0001 | 0.0000 | 0.2486 | 0.1389 | 0.2730 | 0.8064 | 0.3988 | 0.0001 | 0.0000 | 0.0000 | 0.2734 | 0.3745 | 0.9835 | 0.0067 | 0.0100 | 0.1833 | 0.1300 | False | True | True | False | False | 보류 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p05_w0p25 | quantile_guard | 0.1260 | 0.2083 | 0.6479 | 0.3253 | 0.0000 | 0.0001 | 0.0000 | 0.2486 | 0.1389 | 0.2730 | 0.8064 | 0.3988 | 0.0001 | 0.0000 | 0.0000 | 0.2734 | 0.3745 | 0.9835 | 0.0067 | 0.0100 | 0.2033 | 0.1533 | False | True | True | False | False | 보류 |
| hcoef18_qrisk_shrink_current_qwidth_q80_cap0p02_w0p25 | quantile_guard | 0.1260 | 0.2085 | 0.6481 | 0.3257 | 0.0000 | 0.0003 | 0.0001 | 0.2004 | 0.1389 | 0.2731 | 0.8096 | 0.3988 | 0.0001 | 0.0001 | 0.0033 | 0.2731 | 0.3746 | 0.9834 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | False | True | False | False | 보류 |
| hcoef18_qrisk_shrink_current_qwidth_q80_cap0p02_w0p50 | quantile_guard | 0.1260 | 0.2089 | 0.6481 | 0.3262 | 0.0000 | 0.0007 | 0.0002 | 0.2004 | 0.1389 | 0.2733 | 0.8160 | 0.3988 | 0.0001 | 0.0003 | 0.0096 | 0.2727 | 0.3749 | 0.9834 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | False | True | False | False | 보류 |
| hcoef18_qrisk_shrink_current_qwidth_q80_cap0p03_w0p50 | quantile_guard | 0.1260 | 0.2090 | 0.6481 | 0.3264 | 0.0000 | 0.0008 | 0.0002 | 0.2004 | 0.1389 | 0.2734 | 0.8169 | 0.3988 | 0.0001 | 0.0004 | 0.0105 | 0.2731 | 0.3750 | 0.9834 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | False | True | False | False | 보류 |
| hcoef18_qrisk_shrink_current_qwidth_q80_cap0p05_w0p50 | quantile_guard | 0.1260 | 0.2090 | 0.6481 | 0.3264 | 0.0000 | 0.0008 | 0.0002 | 0.2004 | 0.1389 | 0.2734 | 0.8169 | 0.3988 | 0.0001 | 0.0004 | 0.0105 | 0.2731 | 0.3750 | 0.9834 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | False | True | False | False | 보류 |
| hcoef18_qrisk_shrink_current_qwidth_q80_cap0p02_w0p75 | quantile_guard | 0.1260 | 0.2092 | 0.6481 | 0.3267 | 0.0000 | 0.0010 | 0.0002 | 0.2004 | 0.1389 | 0.2735 | 0.8224 | 0.3988 | 0.0001 | 0.0005 | 0.0160 | 0.2731 | 0.3752 | 0.9833 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | False | False | True | False | False | 보류 |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p15_cap0p02_w0p25 | quantile_guard | 0.1260 | 0.2084 | 0.6479 | 0.3253 | 0.0000 | 0.0002 | 0.0000 | 0.3006 | 0.1391 | 0.2729 | 0.8064 | 0.3987 | 0.0003 | -0.0001 | 0.0000 | 0.2731 | 0.3744 | 0.9835 | 0.0000 | 0.0000 | 0.0467 | 0.0400 | False | True | True | True | False | 보류 |

## 7. bootstrap 요약

| split | validation_scheme | candidate | method | n_bootstrap | mean_delta_MdAPE_vs_stable | mean_delta_MAPE_vs_stable | mean_delta_p95_APE_vs_stable | mean_delta_RMSE_log_vs_stable | MdAPE_improve_prob | MAPE_improve_prob | p95_improve_prob | all3_improve_prob | any2_improve_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | artist_bootstrap | hcoef18_qrisk_shrink_current_qwidth_q80_cap0p02_w0p25 | quantile_guard | 300 | 0.0001 | 0.0001 | -0.0004 | -0.0000 | 0.3100 | 0.1667 | 0.3767 | 0.0400 | 0.1667 |
| test | artist_bootstrap | hcoef18_qrisk_shrink_current_qwidth_q80_cap0p03_w0p25 | quantile_guard | 300 | 0.0000 | 0.0002 | -0.0006 | -0.0000 | 0.3300 | 0.1267 | 0.3767 | 0.0400 | 0.1567 |
| test | artist_bootstrap | hcoef18_qrisk_shrink_current_qwidth_q80_cap0p05_w0p25 | quantile_guard | 300 | 0.0000 | 0.0002 | -0.0006 | -0.0000 | 0.3300 | 0.1267 | 0.3767 | 0.0400 | 0.1567 |
| test | artist_bootstrap | hcoef18_qrisk_shrink_current_qwidth_q80_cap0p02_w0p75 | quantile_guard | 300 | 0.0002 | 0.0005 | -0.0013 | -0.0001 | 0.3867 | 0.1200 | 0.4167 | 0.0367 | 0.2033 |
| test | artist_bootstrap | hcoef18_qrisk_shrink_current_qwidth_q80_cap0p02_w0p50 | quantile_guard | 300 | 0.0001 | 0.0003 | -0.0009 | -0.0001 | 0.3633 | 0.1233 | 0.3767 | 0.0300 | 0.1800 |
| test | artist_bootstrap | current_70_30 | baseline | 300 | -0.0003 | 0.0017 | -0.0056 | 0.0007 | 0.5100 | 0.0467 | 0.5733 | 0.0267 | 0.2933 |
| test | artist_bootstrap | hcoef18_qrisk_shrink_current_qwidth_q80_cap0p03_w0p50 | quantile_guard | 300 | 0.0001 | 0.0004 | -0.0013 | -0.0000 | 0.3967 | 0.1067 | 0.3767 | 0.0267 | 0.1900 |
| test | artist_bootstrap | hcoef18_qrisk_shrink_current_qwidth_q80_cap0p03_w0p75 | quantile_guard | 300 | 0.0002 | 0.0007 | -0.0020 | -0.0000 | 0.3767 | 0.0967 | 0.4167 | 0.0267 | 0.1900 |
| test | artist_bootstrap | hcoef18_qrisk_shrink_current_qwidth_q80_cap0p05_w0p50 | quantile_guard | 300 | 0.0001 | 0.0004 | -0.0013 | -0.0000 | 0.3967 | 0.1067 | 0.3767 | 0.0267 | 0.1900 |
| test | artist_bootstrap | hcoef18_qrisk_shrink_current_qwidth_q80_cap0p05_w0p75 | quantile_guard | 300 | 0.0002 | 0.0007 | -0.0020 | -0.0000 | 0.3767 | 0.0967 | 0.4167 | 0.0267 | 0.1900 |
| test | artist_bootstrap | hcoef18_qrisk_shrink_current_qwidth_q66_cap0p03_w0p75 | quantile_guard | 300 | -0.0006 | 0.0011 | -0.0011 | 0.0001 | 0.5533 | 0.0367 | 0.4767 | 0.0233 | 0.2633 |
| test | artist_bootstrap | hcoef18_qrisk_shrink_current_qwidth_q66_cap0p05_w0p75 | quantile_guard | 300 | -0.0006 | 0.0011 | -0.0011 | 0.0001 | 0.5533 | 0.0367 | 0.4767 | 0.0233 | 0.2633 |
| test | artist_bootstrap | hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p15_cap0p02_w0p25 | quantile_guard | 300 | -0.0002 | -0.0001 | -0.0004 | -0.0001 | 0.3667 | 0.7833 | 0.0600 | 0.0233 | 0.3433 |
| test | artist_bootstrap | hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p02_w0p25 | quantile_guard | 300 | -0.0003 | 0.0000 | -0.0000 | -0.0000 | 0.3267 | 0.4933 | 0.0167 | 0.0100 | 0.1733 |
| test | artist_bootstrap | hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p02_w0p50 | quantile_guard | 300 | -0.0008 | 0.0000 | -0.0001 | -0.0001 | 0.5800 | 0.4267 | 0.0167 | 0.0100 | 0.2600 |
| test | artist_bootstrap | ppv8_service_proxy | component | 300 | 0.0239 | 0.0085 | 0.0487 | 0.0038 | 0.0100 | 0.2100 | 0.3200 | 0.0067 | 0.1367 |
| test | artist_bootstrap | hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p03_w0p25 | quantile_guard | 300 | -0.0005 | 0.0000 | -0.0000 | -0.0000 | 0.4267 | 0.4200 | 0.0167 | 0.0067 | 0.1867 |
| test | artist_bootstrap | hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p05_w0p10 | quantile_guard | 300 | -0.0002 | 0.0000 | -0.0000 | -0.0000 | 0.2833 | 0.5000 | 0.0167 | 0.0067 | 0.1467 |
| test | artist_bootstrap | hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p05_w0p25 | quantile_guard | 300 | -0.0006 | 0.0000 | -0.0000 | -0.0000 | 0.4833 | 0.3567 | 0.0167 | 0.0067 | 0.1867 |
| test | artist_bootstrap | hcoef_stable | baseline | 300 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| test | artist_bootstrap | l10_seq_full_generated_bucket | component | 300 | 0.0327 | 0.0529 | 0.1122 | 0.0401 | 0.0100 | 0.0000 | 0.1733 | 0.0000 | 0.0067 |
| test | artist_bootstrap | hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p02_w0p25 | quantile_guard | 300 | -0.0003 | 0.0000 | 0.0000 | -0.0000 | 0.2467 | 0.3833 | 0.0000 | 0.0000 | 0.1167 |
| test | artist_bootstrap | hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p02_w0p50 | quantile_guard | 300 | -0.0005 | 0.0001 | 0.0000 | -0.0000 | 0.4200 | 0.3167 | 0.0000 | 0.0000 | 0.1533 |
| test | artist_bootstrap | hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p03_w0p25 | quantile_guard | 300 | -0.0003 | 0.0000 | 0.0000 | -0.0000 | 0.3100 | 0.3267 | 0.0000 | 0.0000 | 0.1200 |
| test | artist_bootstrap | hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p03_w0p50 | quantile_guard | 300 | -0.0004 | 0.0001 | 0.0000 | -0.0000 | 0.3633 | 0.1933 | 0.0000 | 0.0000 | 0.0800 |
| test | artist_bootstrap | hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p05_w0p10 | quantile_guard | 300 | -0.0002 | 0.0000 | 0.0000 | -0.0000 | 0.2267 | 0.4267 | 0.0000 | 0.0000 | 0.1067 |
| test | artist_bootstrap | hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p05_w0p25 | quantile_guard | 300 | -0.0004 | 0.0001 | 0.0000 | -0.0000 | 0.3467 | 0.2867 | 0.0000 | 0.0000 | 0.1133 |
| test | artist_bootstrap | hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p05_w0p50 | quantile_guard | 300 | -0.0003 | 0.0002 | 0.0000 | -0.0000 | 0.3200 | 0.1233 | 0.0000 | 0.0000 | 0.0533 |
| test | row_bootstrap | hcoef18_qrisk_shrink_current_qwidth_q80_cap0p02_w0p25 | quantile_guard | 300 | 0.0000 | 0.0002 | -0.0010 | -0.0000 | 0.2267 | 0.1133 | 0.4733 | 0.0133 | 0.1667 |
| test | row_bootstrap | hcoef18_qrisk_shrink_current_qwidth_q80_cap0p02_w0p50 | quantile_guard | 300 | 0.0000 | 0.0003 | -0.0021 | -0.0000 | 0.3133 | 0.0933 | 0.4867 | 0.0133 | 0.1967 |
| test | row_bootstrap | hcoef18_qrisk_shrink_current_qwidth_q66_cap0p03_w0p75 | quantile_guard | 300 | -0.0007 | 0.0011 | -0.0029 | 0.0002 | 0.5367 | 0.0200 | 0.6000 | 0.0100 | 0.3333 |
| test | row_bootstrap | hcoef18_qrisk_shrink_current_qwidth_q66_cap0p05_w0p75 | quantile_guard | 300 | -0.0007 | 0.0011 | -0.0029 | 0.0002 | 0.5367 | 0.0200 | 0.6000 | 0.0100 | 0.3333 |
| test | row_bootstrap | current_70_30 | baseline | 300 | -0.0004 | 0.0018 | -0.0063 | 0.0008 | 0.5433 | 0.0300 | 0.5967 | 0.0067 | 0.3400 |
| test | row_bootstrap | hcoef18_qrisk_shrink_current_qwidth_q80_cap0p02_w0p75 | quantile_guard | 300 | 0.0001 | 0.0005 | -0.0031 | -0.0000 | 0.3267 | 0.0833 | 0.5267 | 0.0067 | 0.2167 |
| test | row_bootstrap | hcoef18_qrisk_shrink_current_qwidth_q80_cap0p03_w0p25 | quantile_guard | 300 | -0.0000 | 0.0002 | -0.0013 | -0.0000 | 0.2700 | 0.0800 | 0.4733 | 0.0067 | 0.1800 |
| test | row_bootstrap | hcoef18_qrisk_shrink_current_qwidth_q80_cap0p05_w0p25 | quantile_guard | 300 | -0.0000 | 0.0002 | -0.0013 | -0.0000 | 0.2700 | 0.0800 | 0.4733 | 0.0067 | 0.1800 |
| test | row_bootstrap | hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p02_w0p25 | quantile_guard | 300 | -0.0003 | -0.0000 | -0.0001 | -0.0000 | 0.3467 | 0.5567 | 0.0133 | 0.0067 | 0.1900 |
| test | row_bootstrap | hcoef18_qrisk_shrink_current_qwidth_q80_cap0p03_w0p50 | quantile_guard | 300 | 0.0000 | 0.0004 | -0.0027 | -0.0000 | 0.3367 | 0.0667 | 0.4867 | 0.0033 | 0.2000 |
| test | row_bootstrap | hcoef18_qrisk_shrink_current_qwidth_q80_cap0p03_w0p75 | quantile_guard | 300 | 0.0001 | 0.0007 | -0.0041 | 0.0000 | 0.3500 | 0.0633 | 0.5267 | 0.0033 | 0.2233 |
| test | row_bootstrap | hcoef18_qrisk_shrink_current_qwidth_q80_cap0p05_w0p50 | quantile_guard | 300 | 0.0000 | 0.0004 | -0.0027 | -0.0000 | 0.3367 | 0.0667 | 0.4867 | 0.0033 | 0.2000 |
| test | row_bootstrap | hcoef18_qrisk_shrink_current_qwidth_q80_cap0p05_w0p75 | quantile_guard | 300 | 0.0001 | 0.0007 | -0.0041 | 0.0000 | 0.3500 | 0.0633 | 0.5267 | 0.0033 | 0.2233 |
| test | row_bootstrap | hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p02_w0p50 | quantile_guard | 300 | -0.0006 | 0.0000 | -0.0001 | -0.0001 | 0.5333 | 0.4767 | 0.0133 | 0.0033 | 0.2767 |
| test | row_bootstrap | hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p03_w0p25 | quantile_guard | 300 | -0.0005 | 0.0000 | -0.0001 | -0.0001 | 0.4233 | 0.4967 | 0.0133 | 0.0033 | 0.2200 |
| test | row_bootstrap | hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p05_w0p10 | quantile_guard | 300 | -0.0003 | -0.0000 | -0.0000 | -0.0000 | 0.2733 | 0.5633 | 0.0133 | 0.0033 | 0.1600 |
| test | row_bootstrap | hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p05_w0p25 | quantile_guard | 300 | -0.0006 | 0.0000 | -0.0001 | -0.0000 | 0.4700 | 0.4300 | 0.0133 | 0.0033 | 0.2200 |

_Only first 45 of 112 rows shown._

## 8. quantile width 구간별 후보 성능

| split | qwidth_band | candidate | n | quantile_width_median | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | over_2x_n | under_half_n | threshold_q33 | threshold_q66 | threshold_q80 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_ex50 | qwidth_extreme | ppv8_service_proxy | 301 | 1.9384 | 0.3604 | 0.4111 | 0.9854 | 0.8969 | 0.4585 | 0.7243 | 14 | 57 | 1.2116 | 1.5114 | 1.7065 |
| 0604_ex50 | qwidth_extreme | current_70_30 | 301 | 1.9384 | 0.3750 | 0.4420 | 0.9959 | 1.9726 | 0.4086 | 0.6279 | 7 | 100 | 1.2116 | 1.5114 | 1.7065 |
| 0604_ex50 | qwidth_extreme | hcoef_stable | 301 | 1.9384 | 0.3786 | 0.4380 | 0.9960 | 1.9673 | 0.4053 | 0.6279 | 7 | 100 | 1.2116 | 1.5114 | 1.7065 |
| 0604_ex50 | qwidth_extreme | l10_seq_full_generated_bucket | 301 | 1.9384 | 0.5018 | 0.5526 | 1.2600 | 1.4811 | 0.3223 | 0.4983 | 29 | 92 | 1.2116 | 1.5114 | 1.7065 |
| 0604_ex50 | qwidth_high | ppv8_service_proxy | 185 | 1.5937 | 0.2210 | 0.3675 | 1.0427 | 0.8217 | 0.6270 | 0.7784 | 11 | 17 | 1.2116 | 1.5114 | 1.7065 |
| 0604_ex50 | qwidth_high | hcoef_stable | 185 | 1.5937 | 0.2364 | 0.3758 | 0.9867 | 0.9911 | 0.5514 | 0.7297 | 6 | 27 | 1.2116 | 1.5114 | 1.7065 |
| 0604_ex50 | qwidth_high | current_70_30 | 185 | 1.5937 | 0.2549 | 0.3810 | 0.9966 | 0.9949 | 0.5514 | 0.7514 | 9 | 28 | 1.2116 | 1.5114 | 1.7065 |
| 0604_ex50 | qwidth_high | l10_seq_full_generated_bucket | 185 | 1.5937 | 0.3017 | 0.4513 | 1.3316 | 0.9602 | 0.4757 | 0.6486 | 15 | 41 | 1.2116 | 1.5114 | 1.7065 |
| 0604_ex50 | qwidth_low | l10_seq_full_generated_bucket | 101 | 1.1090 | 0.1428 | 0.2512 | 0.7638 | 0.5901 | 0.7030 | 0.8614 | 1 | 7 | 1.2116 | 1.5114 | 1.7065 |
| 0604_ex50 | qwidth_low | ppv8_service_proxy | 101 | 1.1090 | 0.1754 | 0.2114 | 0.5782 | 0.4165 | 0.7921 | 0.9109 | 0 | 4 | 1.2116 | 1.5114 | 1.7065 |
| 0604_ex50 | qwidth_low | hcoef_stable | 101 | 1.1090 | 0.1774 | 0.2683 | 0.8046 | 0.4146 | 0.6634 | 0.8218 | 2 | 3 | 1.2116 | 1.5114 | 1.7065 |
| 0604_ex50 | qwidth_low | current_70_30 | 101 | 1.1090 | 0.1977 | 0.2707 | 0.7769 | 0.4180 | 0.6733 | 0.8218 | 2 | 3 | 1.2116 | 1.5114 | 1.7065 |
| 0604_ex50 | qwidth_mid | ppv8_service_proxy | 242 | 1.3787 | 0.1797 | 0.2702 | 0.7637 | 0.3868 | 0.6736 | 0.8306 | 6 | 11 | 1.2116 | 1.5114 | 1.7065 |
| 0604_ex50 | qwidth_mid | hcoef_stable | 242 | 1.3787 | 0.2381 | 0.3384 | 0.8841 | 0.4712 | 0.5661 | 0.7521 | 11 | 22 | 1.2116 | 1.5114 | 1.7065 |
| 0604_ex50 | qwidth_mid | current_70_30 | 242 | 1.3787 | 0.2432 | 0.3387 | 0.8870 | 0.4745 | 0.5950 | 0.7479 | 12 | 22 | 1.2116 | 1.5114 | 1.7065 |
| 0604_ex50 | qwidth_mid | l10_seq_full_generated_bucket | 242 | 1.3787 | 0.2653 | 0.4377 | 1.8768 | 0.6415 | 0.5620 | 0.7521 | 18 | 30 | 1.2116 | 1.5114 | 1.7065 |
| test | qwidth_extreme | hcoef_stable | 145 | 1.9481 | 0.2037 | 0.4181 | 1.9368 | 0.5436 | 0.6690 | 0.8069 | 13 | 7 | 1.2116 | 1.5114 | 1.7065 |
| test | qwidth_extreme | current_70_30 | 145 | 1.9481 | 0.2043 | 0.4220 | 1.8921 | 0.5436 | 0.6621 | 0.7931 | 12 | 7 | 1.2116 | 1.5114 | 1.7065 |
| test | qwidth_extreme | ppv8_service_proxy | 145 | 1.9481 | 0.2385 | 0.4260 | 1.6051 | 0.5331 | 0.6138 | 0.7586 | 15 | 6 | 1.2116 | 1.5114 | 1.7065 |
| test | qwidth_extreme | l10_seq_full_generated_bucket | 145 | 1.9481 | 0.3265 | 0.5300 | 1.8852 | 0.6074 | 0.4690 | 0.6621 | 18 | 7 | 1.2116 | 1.5114 | 1.7065 |
| test | qwidth_high | current_70_30 | 97 | 1.5885 | 0.1523 | 0.3014 | 0.7766 | 0.4826 | 0.7423 | 0.8660 | 3 | 3 | 1.2116 | 1.5114 | 1.7065 |
| test | qwidth_high | hcoef_stable | 97 | 1.5885 | 0.1601 | 0.2972 | 0.7645 | 0.4812 | 0.7526 | 0.8660 | 3 | 3 | 1.2116 | 1.5114 | 1.7065 |
| test | qwidth_high | l10_seq_full_generated_bucket | 97 | 1.5885 | 0.1973 | 0.4079 | 0.9953 | 0.5429 | 0.6289 | 0.7938 | 5 | 3 | 1.2116 | 1.5114 | 1.7065 |
| test | qwidth_high | ppv8_service_proxy | 97 | 1.5885 | 0.2073 | 0.3504 | 1.1238 | 0.5128 | 0.6495 | 0.8041 | 6 | 5 | 1.2116 | 1.5114 | 1.7065 |
| test | qwidth_low | l10_seq_full_generated_bucket | 169 | 1.0551 | 0.1081 | 0.1742 | 0.5101 | 0.2285 | 0.8166 | 0.9408 | 1 | 0 | 1.2116 | 1.5114 | 1.7065 |
| test | qwidth_low | current_70_30 | 169 | 1.0551 | 0.1085 | 0.1786 | 0.4870 | 0.2408 | 0.8698 | 0.9527 | 4 | 0 | 1.2116 | 1.5114 | 1.7065 |
| test | qwidth_low | hcoef_stable | 169 | 1.0551 | 0.1137 | 0.1779 | 0.4859 | 0.2401 | 0.8817 | 0.9467 | 5 | 0 | 1.2116 | 1.5114 | 1.7065 |
| test | qwidth_low | ppv8_service_proxy | 169 | 1.0551 | 0.1195 | 0.1707 | 0.4298 | 0.2278 | 0.8402 | 0.9704 | 4 | 0 | 1.2116 | 1.5114 | 1.7065 |
| test | qwidth_mid | current_70_30 | 196 | 1.3811 | 0.1156 | 0.2357 | 0.6786 | 0.3327 | 0.7551 | 0.8827 | 5 | 7 | 1.2116 | 1.5114 | 1.7065 |
| test | qwidth_mid | hcoef_stable | 196 | 1.3811 | 0.1205 | 0.2356 | 0.6876 | 0.3312 | 0.7704 | 0.8878 | 5 | 7 | 1.2116 | 1.5114 | 1.7065 |
| test | qwidth_mid | ppv8_service_proxy | 196 | 1.3811 | 0.1424 | 0.2364 | 0.6482 | 0.3427 | 0.7806 | 0.8673 | 3 | 10 | 1.2116 | 1.5114 | 1.7065 |
| test | qwidth_mid | l10_seq_full_generated_bucket | 196 | 1.3811 | 0.1506 | 0.2670 | 0.6624 | 0.3671 | 0.7041 | 0.8724 | 6 | 9 | 1.2116 | 1.5114 | 1.7065 |
| validation | qwidth_extreme | hcoef_stable | 104 | 1.9554 | 0.1666 | 0.2956 | 0.9546 | 0.4921 | 0.7212 | 0.8654 | 5 | 4 | 1.2116 | 1.5114 | 1.7065 |
| validation | qwidth_extreme | current_70_30 | 104 | 1.9554 | 0.1804 | 0.3040 | 0.9961 | 0.5004 | 0.7212 | 0.8558 | 5 | 5 | 1.2116 | 1.5114 | 1.7065 |
| validation | qwidth_extreme | ppv8_service_proxy | 104 | 1.9554 | 0.2582 | 0.4344 | 1.1598 | 0.5940 | 0.5577 | 0.7404 | 8 | 9 | 1.2116 | 1.5114 | 1.7065 |
| validation | qwidth_extreme | l10_seq_full_generated_bucket | 104 | 1.9554 | 0.2954 | 0.4849 | 1.1928 | 0.6447 | 0.5192 | 0.6731 | 8 | 10 | 1.2116 | 1.5114 | 1.7065 |
| validation | qwidth_high | hcoef_stable | 73 | 1.6037 | 0.1008 | 0.1972 | 0.6811 | 0.2642 | 0.7945 | 0.9041 | 2 | 0 | 1.2116 | 1.5114 | 1.7065 |
| validation | qwidth_high | current_70_30 | 73 | 1.6037 | 0.1047 | 0.1980 | 0.6883 | 0.2652 | 0.8082 | 0.8904 | 2 | 0 | 1.2116 | 1.5114 | 1.7065 |
| validation | qwidth_high | ppv8_service_proxy | 73 | 1.6037 | 0.1410 | 0.2452 | 0.6908 | 0.3034 | 0.6712 | 0.9041 | 1 | 0 | 1.2116 | 1.5114 | 1.7065 |
| validation | qwidth_high | l10_seq_full_generated_bucket | 73 | 1.6037 | 0.1887 | 0.2761 | 0.7961 | 0.3370 | 0.7397 | 0.8356 | 2 | 1 | 1.2116 | 1.5114 | 1.7065 |
| validation | qwidth_low | ppv8_service_proxy | 171 | 1.0858 | 0.1034 | 0.1738 | 0.6142 | 0.2791 | 0.8480 | 0.9181 | 2 | 6 | 1.2116 | 1.5114 | 1.7065 |
| validation | qwidth_low | hcoef_stable | 171 | 1.0858 | 0.1120 | 0.1675 | 0.5638 | 0.2712 | 0.8246 | 0.9240 | 1 | 6 | 1.2116 | 1.5114 | 1.7065 |
| validation | qwidth_low | current_70_30 | 171 | 1.0858 | 0.1162 | 0.1691 | 0.5569 | 0.2761 | 0.8187 | 0.9240 | 1 | 6 | 1.2116 | 1.5114 | 1.7065 |
| validation | qwidth_low | l10_seq_full_generated_bucket | 171 | 1.0858 | 0.1298 | 0.2112 | 0.6426 | 0.3022 | 0.7895 | 0.8947 | 5 | 6 | 1.2116 | 1.5114 | 1.7065 |
| validation | qwidth_mid | hcoef_stable | 171 | 1.3738 | 0.1280 | 0.2004 | 0.5709 | 0.2652 | 0.7602 | 0.9298 | 1 | 0 | 1.2116 | 1.5114 | 1.7065 |
| validation | qwidth_mid | current_70_30 | 171 | 1.3738 | 0.1308 | 0.2019 | 0.5524 | 0.2654 | 0.7485 | 0.9298 | 1 | 0 | 1.2116 | 1.5114 | 1.7065 |
| validation | qwidth_mid | l10_seq_full_generated_bucket | 171 | 1.3738 | 0.1655 | 0.2808 | 0.7393 | 0.3475 | 0.6667 | 0.8538 | 3 | 2 | 1.2116 | 1.5114 | 1.7065 |
| validation | qwidth_mid | ppv8_service_proxy | 171 | 1.3738 | 0.1726 | 0.2294 | 0.5169 | 0.2973 | 0.7193 | 0.9415 | 4 | 1 | 1.2116 | 1.5114 | 1.7065 |

## 9. 구간별 오차 요약

| split | candidate | segment_col | segment_value | n | MdAPE | MAPE | p95_APE | median_residual_log | policy_apply_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_ex50 | l10_seq_full_generated_bucket | gap_band | gap_020_plus | 402 | 0.5130 | 0.5988 | 1.5918 | 0.1562 | 1.0000 |
| 0604_ex50 | hcoef18_qrisk_shrink_current_qwidth_q66_cap0p03_w0p75 | gap_band | gap_020_plus | 402 | 0.4323 | 0.5067 | 0.9999 | 0.2886 | 0.7189 |
| 0604_ex50 | hcoef18_qrisk_shrink_current_qwidth_q66_cap0p05_w0p75 | gap_band | gap_020_plus | 402 | 0.4323 | 0.5067 | 0.9999 | 0.2886 | 0.7189 |
| 0604_ex50 | hcoef18_qrisk_shrink_current_qwidth_q80_cap0p03_w0p75 | gap_band | gap_020_plus | 402 | 0.4323 | 0.5058 | 0.9999 | 0.2864 | 0.4726 |
| 0604_ex50 | hcoef18_qrisk_shrink_current_qwidth_q80_cap0p05_w0p75 | gap_band | gap_020_plus | 402 | 0.4323 | 0.5058 | 0.9999 | 0.2864 | 0.4726 |
| 0604_ex50 | current_70_30 | gap_band | gap_020_plus | 402 | 0.4302 | 0.5054 | 1.0000 | 0.2961 | 1.0000 |
| 0604_ex50 | hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p05_w0p10 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.0000 |
| 0604_ex50 | hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p02_w0p25 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.0000 |
| 0604_ex50 | hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p05_w0p10 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.0000 |
| 0604_ex50 | hcoef_stable | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 1.0000 |
| 0604_ex50 | l10_seq_full_generated_bucket | gap_band | gap_010_020 | 128 | 0.3203 | 0.4882 | 2.1936 | -0.0384 | 1.0000 |
| 0604_ex50 | ppv8_service_proxy | gap_band | gap_020_plus | 402 | 0.3131 | 0.4234 | 1.1510 | 0.1623 | 1.0000 |
| 0604_ex50 | current_70_30 | gap_band | gap_010_020 | 128 | 0.2248 | 0.3419 | 0.8656 | -0.0556 | 1.0000 |
| 0604_ex50 | hcoef18_qrisk_shrink_current_qwidth_q66_cap0p03_w0p75 | gap_band | gap_010_020 | 128 | 0.2269 | 0.3419 | 0.8728 | -0.0465 | 0.5781 |
| 0604_ex50 | hcoef18_qrisk_shrink_current_qwidth_q66_cap0p05_w0p75 | gap_band | gap_010_020 | 128 | 0.2269 | 0.3419 | 0.8728 | -0.0465 | 0.5781 |
| 0604_ex50 | hcoef18_qrisk_shrink_current_qwidth_q80_cap0p03_w0p75 | gap_band | gap_010_020 | 128 | 0.2269 | 0.3409 | 0.8728 | -0.0465 | 0.3750 |
| 0604_ex50 | hcoef18_qrisk_shrink_current_qwidth_q80_cap0p05_w0p75 | gap_band | gap_010_020 | 128 | 0.2269 | 0.3409 | 0.8728 | -0.0465 | 0.3750 |
| 0604_ex50 | hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p05_w0p10 | gap_band | gap_010_020 | 128 | 0.2255 | 0.3393 | 0.8728 | -0.0465 | 0.0000 |
| 0604_ex50 | hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p02_w0p25 | gap_band | gap_010_020 | 128 | 0.2255 | 0.3393 | 0.8728 | -0.0465 | 0.0000 |
| 0604_ex50 | hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p05_w0p10 | gap_band | gap_010_020 | 128 | 0.2255 | 0.3393 | 0.8728 | -0.0465 | 0.0000 |
| 0604_ex50 | hcoef_stable | gap_band | gap_010_020 | 128 | 0.2255 | 0.3393 | 0.8728 | -0.0465 | 1.0000 |
| 0604_ex50 | ppv8_service_proxy | gap_band | gap_010_020 | 128 | 0.2540 | 0.3269 | 0.7844 | 0.0520 | 1.0000 |
| 0604_ex50 | l10_seq_full_generated_bucket | gap_band | gap_005_010 | 125 | 0.1883 | 0.3007 | 0.9169 | 0.0567 | 1.0000 |
| 0604_ex50 | ppv8_service_proxy | gap_band | gap_005_010 | 125 | 0.1764 | 0.2618 | 0.7685 | 0.0806 | 1.0000 |
| 0604_ex50 | current_70_30 | gap_band | gap_005_010 | 125 | 0.1531 | 0.2572 | 0.9461 | 0.0641 | 1.0000 |
| 0604_ex50 | hcoef18_qrisk_shrink_current_qwidth_q66_cap0p03_w0p75 | gap_band | gap_005_010 | 125 | 0.1478 | 0.2529 | 0.9549 | 0.0531 | 0.4320 |
| 0604_ex50 | hcoef18_qrisk_shrink_current_qwidth_q66_cap0p05_w0p75 | gap_band | gap_005_010 | 125 | 0.1478 | 0.2529 | 0.9549 | 0.0531 | 0.4320 |
| 0604_ex50 | hcoef18_qrisk_shrink_current_qwidth_q80_cap0p03_w0p75 | gap_band | gap_005_010 | 125 | 0.1498 | 0.2529 | 0.9526 | 0.0499 | 0.2880 |
| 0604_ex50 | hcoef18_qrisk_shrink_current_qwidth_q80_cap0p05_w0p75 | gap_band | gap_005_010 | 125 | 0.1498 | 0.2529 | 0.9526 | 0.0499 | 0.2880 |
| 0604_ex50 | hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p05_w0p10 | gap_band | gap_005_010 | 125 | 0.1498 | 0.2514 | 0.9526 | 0.0403 | 0.0000 |
| 0604_ex50 | hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p02_w0p25 | gap_band | gap_005_010 | 125 | 0.1498 | 0.2514 | 0.9526 | 0.0403 | 0.0000 |
| 0604_ex50 | hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p05_w0p10 | gap_band | gap_005_010 | 125 | 0.1498 | 0.2514 | 0.9526 | 0.0403 | 0.0000 |
| 0604_ex50 | hcoef_stable | gap_band | gap_005_010 | 125 | 0.1498 | 0.2514 | 0.9526 | 0.0403 | 1.0000 |
| 0604_ex50 | l10_seq_full_generated_bucket | gap_band | gap_000_003 | 119 | 0.1387 | 0.2330 | 0.7125 | -0.0071 | 1.0000 |
| 0604_ex50 | l10_seq_full_generated_bucket | gap_band | gap_003_005 | 55 | 0.1531 | 0.2296 | 0.5665 | -0.0167 | 1.0000 |
| 0604_ex50 | current_70_30 | gap_band | gap_000_003 | 119 | 0.1066 | 0.1953 | 0.5444 | 0.0401 | 1.0000 |
| 0604_ex50 | ppv8_service_proxy | gap_band | gap_000_003 | 119 | 0.1162 | 0.1942 | 0.5405 | 0.0395 | 1.0000 |
| 0604_ex50 | ppv8_service_proxy | gap_band | gap_003_005 | 55 | 0.1039 | 0.1925 | 0.4983 | 0.0427 | 1.0000 |
| 0604_ex50 | hcoef18_qrisk_shrink_current_qwidth_q66_cap0p03_w0p75 | gap_band | gap_000_003 | 119 | 0.1049 | 0.1908 | 0.5379 | 0.0272 | 0.4202 |
| 0604_ex50 | hcoef18_qrisk_shrink_current_qwidth_q66_cap0p05_w0p75 | gap_band | gap_000_003 | 119 | 0.1049 | 0.1908 | 0.5379 | 0.0272 | 0.4202 |
| 0604_ex50 | current_70_30 | gap_band | gap_003_005 | 55 | 0.0809 | 0.1908 | 0.5325 | 0.0305 | 1.0000 |
| 0604_ex50 | hcoef18_qrisk_shrink_current_qwidth_q80_cap0p03_w0p75 | gap_band | gap_000_003 | 119 | 0.0996 | 0.1894 | 0.5300 | 0.0272 | 0.1345 |
| 0604_ex50 | hcoef18_qrisk_shrink_current_qwidth_q80_cap0p05_w0p75 | gap_band | gap_000_003 | 119 | 0.0996 | 0.1894 | 0.5300 | 0.0272 | 0.1345 |
| 0604_ex50 | hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p02_w0p25 | gap_band | gap_000_003 | 119 | 0.1059 | 0.1889 | 0.5300 | 0.0303 | 0.4286 |
| 0604_ex50 | hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p05_w0p10 | gap_band | gap_000_003 | 119 | 0.1056 | 0.1887 | 0.5300 | 0.0284 | 0.4286 |
| 0604_ex50 | hcoef_stable | gap_band | gap_000_003 | 119 | 0.1053 | 0.1886 | 0.5300 | 0.0272 | 1.0000 |
| 0604_ex50 | hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p05_w0p10 | gap_band | gap_000_003 | 119 | 0.1053 | 0.1885 | 0.5300 | 0.0272 | 0.2101 |
| 0604_ex50 | hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p02_w0p25 | gap_band | gap_003_005 | 55 | 0.0914 | 0.1856 | 0.5197 | 0.0175 | 0.4545 |
| 0604_ex50 | hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p05_w0p10 | gap_band | gap_003_005 | 55 | 0.0903 | 0.1853 | 0.5196 | 0.0155 | 0.4545 |
| 0604_ex50 | hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p05_w0p10 | gap_band | gap_003_005 | 55 | 0.0880 | 0.1845 | 0.5173 | 0.0125 | 0.1636 |
| 0604_ex50 | hcoef_stable | gap_band | gap_003_005 | 55 | 0.0868 | 0.1845 | 0.5173 | 0.0125 | 1.0000 |
| 0604_ex50 | hcoef18_qrisk_shrink_current_qwidth_q66_cap0p03_w0p75 | gap_band | gap_003_005 | 55 | 0.0868 | 0.1843 | 0.5240 | 0.0125 | 0.3455 |
| 0604_ex50 | hcoef18_qrisk_shrink_current_qwidth_q66_cap0p05_w0p75 | gap_band | gap_003_005 | 55 | 0.0868 | 0.1843 | 0.5240 | 0.0125 | 0.3455 |
| 0604_ex50 | hcoef18_qrisk_shrink_current_qwidth_q80_cap0p03_w0p75 | gap_band | gap_003_005 | 55 | 0.0868 | 0.1834 | 0.5240 | 0.0125 | 0.2000 |
| 0604_ex50 | hcoef18_qrisk_shrink_current_qwidth_q80_cap0p05_w0p75 | gap_band | gap_003_005 | 55 | 0.0868 | 0.1834 | 0.5240 | 0.0125 | 0.2000 |
| 0604_ex50 | l10_seq_full_generated_bucket | ppv8_direction | ppv8_higher | 439 | 0.4403 | 0.5640 | 1.5932 | 0.0698 | 1.0000 |
| 0604_ex50 | hcoef18_qrisk_shrink_current_qwidth_q66_cap0p03_w0p75 | ppv8_direction | ppv8_lower | 390 | 0.2490 | 0.3852 | 1.0348 | -0.0128 | 0.4436 |
| 0604_ex50 | hcoef18_qrisk_shrink_current_qwidth_q66_cap0p05_w0p75 | ppv8_direction | ppv8_lower | 390 | 0.2490 | 0.3852 | 1.0348 | -0.0128 | 0.4436 |
| 0604_ex50 | hcoef18_qrisk_shrink_current_qwidth_q80_cap0p03_w0p75 | ppv8_direction | ppv8_lower | 390 | 0.2490 | 0.3850 | 1.0310 | -0.0116 | 0.2615 |
| 0604_ex50 | hcoef18_qrisk_shrink_current_qwidth_q80_cap0p05_w0p75 | ppv8_direction | ppv8_lower | 390 | 0.2490 | 0.3850 | 1.0310 | -0.0116 | 0.2615 |

## 10. 정책/계수 해석

| candidate | method | policy_type | source_col | qwidth_threshold_name | qwidth_threshold | spread_threshold | gap | cap | weight | shrink_cap | ppv8_cap | description |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef_stable | baseline | baseline | hcoef_stable |  |  |  |  |  |  |  |  | HCOEF 안정 후보 |
| current_70_30 | baseline | baseline | current_70_30 |  |  |  |  |  |  |  |  | 기존 70:30 기준 |
| ppv8_service_proxy | component | component | ppv8_service_proxy |  |  |  |  |  |  |  |  | PP-V8/service proxy |
| svc_numeric_seed_mean | component | component | svc_numeric_seed_mean |  |  |  |  |  |  |  |  | 유사 작품 기반 가격 피처 |
| l10_seq_full_generated_bucket | component | component | l10_seq_pred_log |  |  |  |  |  |  |  |  | PP-L10 Quantile->Huber->CatBoost 순차 구조 예측값 |
| hcoef18_qrisk_shrink_current_qwidth_q66_cap0p02_w0p25 | quantile_guard | high_qwidth_shrink_current |  | qwidth_q66 | 1.5114 |  |  | 0.0200 | 0.2500 |  |  | quantile_width가 validation qwidth_q66 이상이면 HCOEF 보정폭을 current_70_30 방향으로 cap 0.02, weight 0.25만큼 축소. |
| hcoef18_qrisk_shrink_current_spread_qwidth_q66_cap0p02_w0p25 | quantile_guard | high_qwidth_or_spread_shrink_current |  | qwidth_q66 | 1.5114 | 0.2397 |  | 0.0200 | 0.2500 |  |  | quantile_width가 qwidth_q66 이상이거나 후보 간 spread가 높으면 HCOEF 보정폭을 current_70_30 방향으로 제한 축소. |
| hcoef18_qrisk_shrink_current_qwidth_q66_cap0p02_w0p50 | quantile_guard | high_qwidth_shrink_current |  | qwidth_q66 | 1.5114 |  |  | 0.0200 | 0.5000 |  |  | quantile_width가 validation qwidth_q66 이상이면 HCOEF 보정폭을 current_70_30 방향으로 cap 0.02, weight 0.5만큼 축소. |
| hcoef18_qrisk_shrink_current_spread_qwidth_q66_cap0p02_w0p50 | quantile_guard | high_qwidth_or_spread_shrink_current |  | qwidth_q66 | 1.5114 | 0.2397 |  | 0.0200 | 0.5000 |  |  | quantile_width가 qwidth_q66 이상이거나 후보 간 spread가 높으면 HCOEF 보정폭을 current_70_30 방향으로 제한 축소. |
| hcoef18_qrisk_shrink_current_qwidth_q66_cap0p02_w0p75 | quantile_guard | high_qwidth_shrink_current |  | qwidth_q66 | 1.5114 |  |  | 0.0200 | 0.7500 |  |  | quantile_width가 validation qwidth_q66 이상이면 HCOEF 보정폭을 current_70_30 방향으로 cap 0.02, weight 0.75만큼 축소. |
| hcoef18_qrisk_shrink_current_spread_qwidth_q66_cap0p02_w0p75 | quantile_guard | high_qwidth_or_spread_shrink_current |  | qwidth_q66 | 1.5114 | 0.2397 |  | 0.0200 | 0.7500 |  |  | quantile_width가 qwidth_q66 이상이거나 후보 간 spread가 높으면 HCOEF 보정폭을 current_70_30 방향으로 제한 축소. |
| hcoef18_qrisk_shrink_current_qwidth_q66_cap0p03_w0p25 | quantile_guard | high_qwidth_shrink_current |  | qwidth_q66 | 1.5114 |  |  | 0.0300 | 0.2500 |  |  | quantile_width가 validation qwidth_q66 이상이면 HCOEF 보정폭을 current_70_30 방향으로 cap 0.03, weight 0.25만큼 축소. |
| hcoef18_qrisk_shrink_current_spread_qwidth_q66_cap0p03_w0p25 | quantile_guard | high_qwidth_or_spread_shrink_current |  | qwidth_q66 | 1.5114 | 0.2397 |  | 0.0300 | 0.2500 |  |  | quantile_width가 qwidth_q66 이상이거나 후보 간 spread가 높으면 HCOEF 보정폭을 current_70_30 방향으로 제한 축소. |
| hcoef18_qrisk_shrink_current_qwidth_q66_cap0p03_w0p50 | quantile_guard | high_qwidth_shrink_current |  | qwidth_q66 | 1.5114 |  |  | 0.0300 | 0.5000 |  |  | quantile_width가 validation qwidth_q66 이상이면 HCOEF 보정폭을 current_70_30 방향으로 cap 0.03, weight 0.5만큼 축소. |
| hcoef18_qrisk_shrink_current_spread_qwidth_q66_cap0p03_w0p50 | quantile_guard | high_qwidth_or_spread_shrink_current |  | qwidth_q66 | 1.5114 | 0.2397 |  | 0.0300 | 0.5000 |  |  | quantile_width가 qwidth_q66 이상이거나 후보 간 spread가 높으면 HCOEF 보정폭을 current_70_30 방향으로 제한 축소. |
| hcoef18_qrisk_shrink_current_qwidth_q66_cap0p03_w0p75 | quantile_guard | high_qwidth_shrink_current |  | qwidth_q66 | 1.5114 |  |  | 0.0300 | 0.7500 |  |  | quantile_width가 validation qwidth_q66 이상이면 HCOEF 보정폭을 current_70_30 방향으로 cap 0.03, weight 0.75만큼 축소. |
| hcoef18_qrisk_shrink_current_spread_qwidth_q66_cap0p03_w0p75 | quantile_guard | high_qwidth_or_spread_shrink_current |  | qwidth_q66 | 1.5114 | 0.2397 |  | 0.0300 | 0.7500 |  |  | quantile_width가 qwidth_q66 이상이거나 후보 간 spread가 높으면 HCOEF 보정폭을 current_70_30 방향으로 제한 축소. |
| hcoef18_qrisk_shrink_current_qwidth_q66_cap0p05_w0p25 | quantile_guard | high_qwidth_shrink_current |  | qwidth_q66 | 1.5114 |  |  | 0.0500 | 0.2500 |  |  | quantile_width가 validation qwidth_q66 이상이면 HCOEF 보정폭을 current_70_30 방향으로 cap 0.05, weight 0.25만큼 축소. |
| hcoef18_qrisk_shrink_current_spread_qwidth_q66_cap0p05_w0p25 | quantile_guard | high_qwidth_or_spread_shrink_current |  | qwidth_q66 | 1.5114 | 0.2397 |  | 0.0500 | 0.2500 |  |  | quantile_width가 qwidth_q66 이상이거나 후보 간 spread가 높으면 HCOEF 보정폭을 current_70_30 방향으로 제한 축소. |
| hcoef18_qrisk_shrink_current_qwidth_q66_cap0p05_w0p50 | quantile_guard | high_qwidth_shrink_current |  | qwidth_q66 | 1.5114 |  |  | 0.0500 | 0.5000 |  |  | quantile_width가 validation qwidth_q66 이상이면 HCOEF 보정폭을 current_70_30 방향으로 cap 0.05, weight 0.5만큼 축소. |
| hcoef18_qrisk_shrink_current_spread_qwidth_q66_cap0p05_w0p50 | quantile_guard | high_qwidth_or_spread_shrink_current |  | qwidth_q66 | 1.5114 | 0.2397 |  | 0.0500 | 0.5000 |  |  | quantile_width가 qwidth_q66 이상이거나 후보 간 spread가 높으면 HCOEF 보정폭을 current_70_30 방향으로 제한 축소. |
| hcoef18_qrisk_shrink_current_qwidth_q66_cap0p05_w0p75 | quantile_guard | high_qwidth_shrink_current |  | qwidth_q66 | 1.5114 |  |  | 0.0500 | 0.7500 |  |  | quantile_width가 validation qwidth_q66 이상이면 HCOEF 보정폭을 current_70_30 방향으로 cap 0.05, weight 0.75만큼 축소. |
| hcoef18_qrisk_shrink_current_spread_qwidth_q66_cap0p05_w0p75 | quantile_guard | high_qwidth_or_spread_shrink_current |  | qwidth_q66 | 1.5114 | 0.2397 |  | 0.0500 | 0.7500 |  |  | quantile_width가 qwidth_q66 이상이거나 후보 간 spread가 높으면 HCOEF 보정폭을 current_70_30 방향으로 제한 축소. |
| hcoef18_qrisk_shrink_current_qwidth_q80_cap0p02_w0p25 | quantile_guard | high_qwidth_shrink_current |  | qwidth_q80 | 1.7065 |  |  | 0.0200 | 0.2500 |  |  | quantile_width가 validation qwidth_q80 이상이면 HCOEF 보정폭을 current_70_30 방향으로 cap 0.02, weight 0.25만큼 축소. |
| hcoef18_qrisk_shrink_current_spread_qwidth_q80_cap0p02_w0p25 | quantile_guard | high_qwidth_or_spread_shrink_current |  | qwidth_q80 | 1.7065 | 0.2397 |  | 0.0200 | 0.2500 |  |  | quantile_width가 qwidth_q80 이상이거나 후보 간 spread가 높으면 HCOEF 보정폭을 current_70_30 방향으로 제한 축소. |
| hcoef18_qrisk_shrink_current_qwidth_q80_cap0p02_w0p50 | quantile_guard | high_qwidth_shrink_current |  | qwidth_q80 | 1.7065 |  |  | 0.0200 | 0.5000 |  |  | quantile_width가 validation qwidth_q80 이상이면 HCOEF 보정폭을 current_70_30 방향으로 cap 0.02, weight 0.5만큼 축소. |
| hcoef18_qrisk_shrink_current_spread_qwidth_q80_cap0p02_w0p50 | quantile_guard | high_qwidth_or_spread_shrink_current |  | qwidth_q80 | 1.7065 | 0.2397 |  | 0.0200 | 0.5000 |  |  | quantile_width가 qwidth_q80 이상이거나 후보 간 spread가 높으면 HCOEF 보정폭을 current_70_30 방향으로 제한 축소. |
| hcoef18_qrisk_shrink_current_qwidth_q80_cap0p02_w0p75 | quantile_guard | high_qwidth_shrink_current |  | qwidth_q80 | 1.7065 |  |  | 0.0200 | 0.7500 |  |  | quantile_width가 validation qwidth_q80 이상이면 HCOEF 보정폭을 current_70_30 방향으로 cap 0.02, weight 0.75만큼 축소. |
| hcoef18_qrisk_shrink_current_spread_qwidth_q80_cap0p02_w0p75 | quantile_guard | high_qwidth_or_spread_shrink_current |  | qwidth_q80 | 1.7065 | 0.2397 |  | 0.0200 | 0.7500 |  |  | quantile_width가 qwidth_q80 이상이거나 후보 간 spread가 높으면 HCOEF 보정폭을 current_70_30 방향으로 제한 축소. |
| hcoef18_qrisk_shrink_current_qwidth_q80_cap0p03_w0p25 | quantile_guard | high_qwidth_shrink_current |  | qwidth_q80 | 1.7065 |  |  | 0.0300 | 0.2500 |  |  | quantile_width가 validation qwidth_q80 이상이면 HCOEF 보정폭을 current_70_30 방향으로 cap 0.03, weight 0.25만큼 축소. |
| hcoef18_qrisk_shrink_current_spread_qwidth_q80_cap0p03_w0p25 | quantile_guard | high_qwidth_or_spread_shrink_current |  | qwidth_q80 | 1.7065 | 0.2397 |  | 0.0300 | 0.2500 |  |  | quantile_width가 qwidth_q80 이상이거나 후보 간 spread가 높으면 HCOEF 보정폭을 current_70_30 방향으로 제한 축소. |
| hcoef18_qrisk_shrink_current_qwidth_q80_cap0p03_w0p50 | quantile_guard | high_qwidth_shrink_current |  | qwidth_q80 | 1.7065 |  |  | 0.0300 | 0.5000 |  |  | quantile_width가 validation qwidth_q80 이상이면 HCOEF 보정폭을 current_70_30 방향으로 cap 0.03, weight 0.5만큼 축소. |
| hcoef18_qrisk_shrink_current_spread_qwidth_q80_cap0p03_w0p50 | quantile_guard | high_qwidth_or_spread_shrink_current |  | qwidth_q80 | 1.7065 | 0.2397 |  | 0.0300 | 0.5000 |  |  | quantile_width가 qwidth_q80 이상이거나 후보 간 spread가 높으면 HCOEF 보정폭을 current_70_30 방향으로 제한 축소. |
| hcoef18_qrisk_shrink_current_qwidth_q80_cap0p03_w0p75 | quantile_guard | high_qwidth_shrink_current |  | qwidth_q80 | 1.7065 |  |  | 0.0300 | 0.7500 |  |  | quantile_width가 validation qwidth_q80 이상이면 HCOEF 보정폭을 current_70_30 방향으로 cap 0.03, weight 0.75만큼 축소. |
| hcoef18_qrisk_shrink_current_spread_qwidth_q80_cap0p03_w0p75 | quantile_guard | high_qwidth_or_spread_shrink_current |  | qwidth_q80 | 1.7065 | 0.2397 |  | 0.0300 | 0.7500 |  |  | quantile_width가 qwidth_q80 이상이거나 후보 간 spread가 높으면 HCOEF 보정폭을 current_70_30 방향으로 제한 축소. |
| hcoef18_qrisk_shrink_current_qwidth_q80_cap0p05_w0p25 | quantile_guard | high_qwidth_shrink_current |  | qwidth_q80 | 1.7065 |  |  | 0.0500 | 0.2500 |  |  | quantile_width가 validation qwidth_q80 이상이면 HCOEF 보정폭을 current_70_30 방향으로 cap 0.05, weight 0.25만큼 축소. |
| hcoef18_qrisk_shrink_current_spread_qwidth_q80_cap0p05_w0p25 | quantile_guard | high_qwidth_or_spread_shrink_current |  | qwidth_q80 | 1.7065 | 0.2397 |  | 0.0500 | 0.2500 |  |  | quantile_width가 qwidth_q80 이상이거나 후보 간 spread가 높으면 HCOEF 보정폭을 current_70_30 방향으로 제한 축소. |
| hcoef18_qrisk_shrink_current_qwidth_q80_cap0p05_w0p50 | quantile_guard | high_qwidth_shrink_current |  | qwidth_q80 | 1.7065 |  |  | 0.0500 | 0.5000 |  |  | quantile_width가 validation qwidth_q80 이상이면 HCOEF 보정폭을 current_70_30 방향으로 cap 0.05, weight 0.5만큼 축소. |
| hcoef18_qrisk_shrink_current_spread_qwidth_q80_cap0p05_w0p50 | quantile_guard | high_qwidth_or_spread_shrink_current |  | qwidth_q80 | 1.7065 | 0.2397 |  | 0.0500 | 0.5000 |  |  | quantile_width가 qwidth_q80 이상이거나 후보 간 spread가 높으면 HCOEF 보정폭을 current_70_30 방향으로 제한 축소. |
| hcoef18_qrisk_shrink_current_qwidth_q80_cap0p05_w0p75 | quantile_guard | high_qwidth_shrink_current |  | qwidth_q80 | 1.7065 |  |  | 0.0500 | 0.7500 |  |  | quantile_width가 validation qwidth_q80 이상이면 HCOEF 보정폭을 current_70_30 방향으로 cap 0.05, weight 0.75만큼 축소. |
| hcoef18_qrisk_shrink_current_spread_qwidth_q80_cap0p05_w0p75 | quantile_guard | high_qwidth_or_spread_shrink_current |  | qwidth_q80 | 1.7065 | 0.2397 |  | 0.0500 | 0.7500 |  |  | quantile_width가 qwidth_q80 이상이거나 후보 간 spread가 높으면 HCOEF 보정폭을 current_70_30 방향으로 제한 축소. |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p02_w0p10 | quantile_guard | low_qwidth_ppv8_move |  | qwidth_q33 | 1.2116 |  | 0.0500 | 0.0200 | 0.1000 |  |  | quantile_width가 validation qwidth_q33 이하이고 PP-V8 gap이 0.05 이하일 때만 PP-V8 방향으로 제한 이동. |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p02_w0p25 | quantile_guard | low_qwidth_ppv8_move |  | qwidth_q33 | 1.2116 |  | 0.0500 | 0.0200 | 0.2500 |  |  | quantile_width가 validation qwidth_q33 이하이고 PP-V8 gap이 0.05 이하일 때만 PP-V8 방향으로 제한 이동. |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p02_w0p50 | quantile_guard | low_qwidth_ppv8_move |  | qwidth_q33 | 1.2116 |  | 0.0500 | 0.0200 | 0.5000 |  |  | quantile_width가 validation qwidth_q33 이하이고 PP-V8 gap이 0.05 이하일 때만 PP-V8 방향으로 제한 이동. |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p03_w0p10 | quantile_guard | low_qwidth_ppv8_move |  | qwidth_q33 | 1.2116 |  | 0.0500 | 0.0300 | 0.1000 |  |  | quantile_width가 validation qwidth_q33 이하이고 PP-V8 gap이 0.05 이하일 때만 PP-V8 방향으로 제한 이동. |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p03_w0p25 | quantile_guard | low_qwidth_ppv8_move |  | qwidth_q33 | 1.2116 |  | 0.0500 | 0.0300 | 0.2500 |  |  | quantile_width가 validation qwidth_q33 이하이고 PP-V8 gap이 0.05 이하일 때만 PP-V8 방향으로 제한 이동. |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p03_w0p50 | quantile_guard | low_qwidth_ppv8_move |  | qwidth_q33 | 1.2116 |  | 0.0500 | 0.0300 | 0.5000 |  |  | quantile_width가 validation qwidth_q33 이하이고 PP-V8 gap이 0.05 이하일 때만 PP-V8 방향으로 제한 이동. |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p05_w0p10 | quantile_guard | low_qwidth_ppv8_move |  | qwidth_q33 | 1.2116 |  | 0.0500 | 0.0500 | 0.1000 |  |  | quantile_width가 validation qwidth_q33 이하이고 PP-V8 gap이 0.05 이하일 때만 PP-V8 방향으로 제한 이동. |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p05_w0p25 | quantile_guard | low_qwidth_ppv8_move |  | qwidth_q33 | 1.2116 |  | 0.0500 | 0.0500 | 0.2500 |  |  | quantile_width가 validation qwidth_q33 이하이고 PP-V8 gap이 0.05 이하일 때만 PP-V8 방향으로 제한 이동. |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p05_cap0p05_w0p50 | quantile_guard | low_qwidth_ppv8_move |  | qwidth_q33 | 1.2116 |  | 0.0500 | 0.0500 | 0.5000 |  |  | quantile_width가 validation qwidth_q33 이하이고 PP-V8 gap이 0.05 이하일 때만 PP-V8 방향으로 제한 이동. |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p10_cap0p02_w0p10 | quantile_guard | low_qwidth_ppv8_move |  | qwidth_q33 | 1.2116 |  | 0.1000 | 0.0200 | 0.1000 |  |  | quantile_width가 validation qwidth_q33 이하이고 PP-V8 gap이 0.1 이하일 때만 PP-V8 방향으로 제한 이동. |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p10_cap0p02_w0p25 | quantile_guard | low_qwidth_ppv8_move |  | qwidth_q33 | 1.2116 |  | 0.1000 | 0.0200 | 0.2500 |  |  | quantile_width가 validation qwidth_q33 이하이고 PP-V8 gap이 0.1 이하일 때만 PP-V8 방향으로 제한 이동. |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p10_cap0p02_w0p50 | quantile_guard | low_qwidth_ppv8_move |  | qwidth_q33 | 1.2116 |  | 0.1000 | 0.0200 | 0.5000 |  |  | quantile_width가 validation qwidth_q33 이하이고 PP-V8 gap이 0.1 이하일 때만 PP-V8 방향으로 제한 이동. |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p10_cap0p03_w0p10 | quantile_guard | low_qwidth_ppv8_move |  | qwidth_q33 | 1.2116 |  | 0.1000 | 0.0300 | 0.1000 |  |  | quantile_width가 validation qwidth_q33 이하이고 PP-V8 gap이 0.1 이하일 때만 PP-V8 방향으로 제한 이동. |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p10_cap0p03_w0p25 | quantile_guard | low_qwidth_ppv8_move |  | qwidth_q33 | 1.2116 |  | 0.1000 | 0.0300 | 0.2500 |  |  | quantile_width가 validation qwidth_q33 이하이고 PP-V8 gap이 0.1 이하일 때만 PP-V8 방향으로 제한 이동. |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p10_cap0p03_w0p50 | quantile_guard | low_qwidth_ppv8_move |  | qwidth_q33 | 1.2116 |  | 0.1000 | 0.0300 | 0.5000 |  |  | quantile_width가 validation qwidth_q33 이하이고 PP-V8 gap이 0.1 이하일 때만 PP-V8 방향으로 제한 이동. |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p10_cap0p05_w0p10 | quantile_guard | low_qwidth_ppv8_move |  | qwidth_q33 | 1.2116 |  | 0.1000 | 0.0500 | 0.1000 |  |  | quantile_width가 validation qwidth_q33 이하이고 PP-V8 gap이 0.1 이하일 때만 PP-V8 방향으로 제한 이동. |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p10_cap0p05_w0p25 | quantile_guard | low_qwidth_ppv8_move |  | qwidth_q33 | 1.2116 |  | 0.1000 | 0.0500 | 0.2500 |  |  | quantile_width가 validation qwidth_q33 이하이고 PP-V8 gap이 0.1 이하일 때만 PP-V8 방향으로 제한 이동. |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p10_cap0p05_w0p50 | quantile_guard | low_qwidth_ppv8_move |  | qwidth_q33 | 1.2116 |  | 0.1000 | 0.0500 | 0.5000 |  |  | quantile_width가 validation qwidth_q33 이하이고 PP-V8 gap이 0.1 이하일 때만 PP-V8 방향으로 제한 이동. |
| hcoef18_qrisk_lowq_ppv8_qwidth_q33_gap0p15_cap0p02_w0p10 | quantile_guard | low_qwidth_ppv8_move |  | qwidth_q33 | 1.2116 |  | 0.1500 | 0.0200 | 0.1000 |  |  | quantile_width가 validation qwidth_q33 이하이고 PP-V8 gap이 0.15 이하일 때만 PP-V8 방향으로 제한 이동. |

## 11. 해석

- `quantile_width`는 q90 로그 예측과 q10 로그 예측의 차이로, 값이 클수록 모델이 가격 범위를 넓게 본다는 뜻임.
- Huber는 기본적으로 로그 가격을 선형 결합으로 예측하므로, HCOEF 보정폭이 위험 구간에서 과하게 작동하면 `current_70_30` 방향으로 줄이는 정책이 해석 가능함.
- low quantile width는 quantile 모델이 상대적으로 좁은 가격 범위를 본 구간이므로, PP-V8 이동을 허용해도 되는지 확인하는 gate로 사용함.
- high quantile width 또는 모델 간 spread가 큰 구간은 예측 불확실성이 큰 구간이므로, 점 예측을 공격적으로 움직이기보다 보정폭 축소 또는 신뢰도/범위 정책 후보로 보는 것이 맞음.

## 12. 산출물

- `artifacts/experiment_config.json`
- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/policy_map.csv`
- `outputs/residual_analysis.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `outputs/quantile_feature_audit.csv`
- `outputs/error_segment_summary.csv`
- `outputs/selected_candidates.csv`