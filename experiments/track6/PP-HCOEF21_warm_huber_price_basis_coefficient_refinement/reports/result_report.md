# PP-HCOEF21 Warm Huber 가변 기준가/계수 검증

- 작성일: 2026-06-08 03:39
- 목적: 고정 70:30 기준가를 표본 수/coverage/quantile 폭 기반 가변 기준가로 바꿀 수 있는지 검증.
- 현재 기준 후보: `hcoef_stable` = `hcoef2_size_reliability_cap005_s050`.
- 최소 비교 기준: `current_70_30` = SVC 70% + PP-V8 30%.
- 0604는 외부 stress test이며 후보 선택에는 사용하지 않음.

## 1. 실험 설계

- `current_70_30`이 실제로 `0.7 * svc_numeric_seed_mean + 0.3 * ppv8_service_proxy`인 것을 확인한 뒤 진행.
- 가변 기준가:
  - SVC 신뢰도가 높으면 SVC 비중을 높임.
  - 표본 수/coverage가 낮거나 quantile 폭이 크면 PP-V8 쪽으로 일부 이동.
  - 기존 HCOEF 안정 보정량(`hcoef_stable - current_70_30`)을 더하는 후보와, 안정 후보에서 작은 cap만큼 이동하는 후보를 분리.
- Huber residual:
  - `residual_log = actual_log - hcoef_stable`를 OOF로 학습.
  - cap과 strength로 이동폭을 제한.
  - fixed test/0604 residual은 보정값 생성에 사용하지 않음.

## 2. 후보 선택표

| candidate | method | decision | row_oof_MdAPE | row_oof_MAPE | row_oof_p95_APE | artist_oof_MdAPE | artist_oof_MAPE | artist_oof_p95_APE | test_MdAPE | test_MAPE | test_p95_APE | stress0604_MdAPE | stress0604_MAPE | stress0604_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef_stable | source | 현재 기준 후보 | 0.1260 | 0.2082 | 0.6479 | 0.1260 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9835 |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p02_s0p25 | residual_huber | OOF 개선 후보 | 0.1263 | 0.2077 | 0.6409 | 0.1261 | 0.2078 | 0.6409 | 0.1388 | 0.2727 | 0.8099 | 0.2696 | 0.3731 | 0.9834 |
| hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p02_s0p25 | residual_huber | OOF 개선 후보 | 0.1263 | 0.2077 | 0.6409 | 0.1261 | 0.2078 | 0.6409 | 0.1388 | 0.2727 | 0.8099 | 0.2696 | 0.3731 | 0.9834 |
| hcoef21_resid_ridge_adaptive_interactions_a1_cap0p02_s0p25 | residual_ridge | OOF 개선 후보 | 0.1263 | 0.2076 | 0.6409 | 0.1263 | 0.2079 | 0.6409 | 0.1388 | 0.2728 | 0.8097 | 0.2698 | 0.3730 | 0.9834 |
| hcoef21_resid_ridge_adaptive_interactions_a0p1_cap0p02_s0p25 | residual_ridge | OOF 개선 후보 | 0.1263 | 0.2077 | 0.6409 | 0.1263 | 0.2079 | 0.6409 | 0.1388 | 0.2728 | 0.8097 | 0.2698 | 0.3730 | 0.9834 |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p02_s0p25 | residual_huber | OOF 개선 후보 | 0.1263 | 0.2078 | 0.6409 | 0.1260 | 0.2079 | 0.6409 | 0.1389 | 0.2727 | 0.8100 | 0.2725 | 0.3733 | 0.9834 |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p02_s0p25 | residual_huber | OOF 개선 후보 | 0.1263 | 0.2078 | 0.6409 | 0.1261 | 0.2079 | 0.6409 | 0.1389 | 0.2727 | 0.8100 | 0.2725 | 0.3733 | 0.9834 |
| hcoef21_resid_ridge_adaptive_reliability_a0p1_cap0p02_s0p25 | residual_ridge | OOF 개선 후보 | 0.1263 | 0.2079 | 0.6409 | 0.1259 | 0.2079 | 0.6409 | 0.1389 | 0.2729 | 0.8100 | 0.2748 | 0.3733 | 0.9834 |
| hcoef21_resid_ridge_adaptive_reliability_a1_cap0p02_s0p25 | residual_ridge | OOF 개선 후보 | 0.1263 | 0.2079 | 0.6409 | 0.1259 | 0.2080 | 0.6409 | 0.1389 | 0.2729 | 0.8100 | 0.2758 | 0.3734 | 0.9834 |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p03_s0p25 | residual_huber | OOF 개선 후보 | 0.1286 | 0.2077 | 0.6445 | 0.1260 | 0.2077 | 0.6445 | 0.1400 | 0.2726 | 0.8139 | 0.2725 | 0.3728 | 0.9807 |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p03_s0p25 | residual_huber | OOF 개선 후보 | 0.1286 | 0.2077 | 0.6445 | 0.1261 | 0.2077 | 0.6445 | 0.1400 | 0.2726 | 0.8139 | 0.2725 | 0.3728 | 0.9807 |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p03_s0p25 | residual_huber | OOF 개선 후보 | 0.1279 | 0.2075 | 0.6445 | 0.1264 | 0.2076 | 0.6445 | 0.1402 | 0.2727 | 0.8139 | 0.2696 | 0.3725 | 0.9807 |
| hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p03_s0p25 | residual_huber | OOF 개선 후보 | 0.1279 | 0.2075 | 0.6445 | 0.1264 | 0.2076 | 0.6445 | 0.1402 | 0.2727 | 0.8139 | 0.2696 | 0.3725 | 0.9807 |
| hcoef21_resid_ridge_adaptive_reliability_a1_cap0p03_s0p25 | residual_ridge | OOF 개선 후보 | 0.1269 | 0.2078 | 0.6445 | 0.1264 | 0.2079 | 0.6445 | 0.1403 | 0.2730 | 0.8145 | 0.2758 | 0.3728 | 0.9807 |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p05_s0p25 | residual_huber | OOF 개선 후보 | 0.1266 | 0.2074 | 0.6451 | 0.1254 | 0.2076 | 0.6445 | 0.1404 | 0.2726 | 0.8230 | 0.2745 | 0.3720 | 0.9789 |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p05_s0p25 | residual_huber | OOF 개선 후보 | 0.1266 | 0.2074 | 0.6451 | 0.1254 | 0.2076 | 0.6445 | 0.1404 | 0.2726 | 0.8230 | 0.2745 | 0.3720 | 0.9789 |
| hcoef21_resid_ridge_adaptive_interactions_a1_cap0p03_s0p25 | residual_ridge | OOF 개선 후보 | 0.1288 | 0.2074 | 0.6445 | 0.1289 | 0.2077 | 0.6445 | 0.1405 | 0.2728 | 0.8137 | 0.2679 | 0.3724 | 0.9807 |
| hcoef21_resid_ridge_adaptive_interactions_a0p1_cap0p03_s0p25 | residual_ridge | OOF 개선 후보 | 0.1288 | 0.2074 | 0.6445 | 0.1288 | 0.2077 | 0.6445 | 0.1405 | 0.2728 | 0.8137 | 0.2679 | 0.3724 | 0.9807 |
| hcoef21_resid_ridge_adaptive_reliability_a0p1_cap0p03_s0p25 | residual_ridge | OOF 개선 후보 | 0.1281 | 0.2078 | 0.6445 | 0.1264 | 0.2079 | 0.6445 | 0.1408 | 0.2729 | 0.8145 | 0.2748 | 0.3728 | 0.9807 |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p02_s0p5 | residual_huber | OOF 개선 후보 | 0.1292 | 0.2075 | 0.6448 | 0.1274 | 0.2076 | 0.6451 | 0.1421 | 0.2725 | 0.8190 | 0.2727 | 0.3723 | 0.9790 |

## 3. Fixed Test 상위 후보

| candidate | method | n | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable | improve_count_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef_stable | source | 607 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0 |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p02_s0p25 | residual_huber | 607 | 0.1388 | 0.2727 | 0.8099 | 0.3987 | 0.0000 | -0.0003 | 0.0036 | 1 |
| hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p02_s0p25 | residual_huber | 607 | 0.1388 | 0.2727 | 0.8099 | 0.3987 | 0.0000 | -0.0003 | 0.0036 | 1 |
| hcoef21_resid_ridge_adaptive_interactions_a1_cap0p02_s0p25 | residual_ridge | 607 | 0.1388 | 0.2728 | 0.8097 | 0.3987 | 0.0000 | -0.0002 | 0.0033 | 1 |
| hcoef21_resid_ridge_adaptive_interactions_a0p1_cap0p02_s0p25 | residual_ridge | 607 | 0.1388 | 0.2728 | 0.8097 | 0.3987 | 0.0000 | -0.0002 | 0.0033 | 1 |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p02_s0p25 | residual_huber | 607 | 0.1389 | 0.2727 | 0.8100 | 0.3987 | 0.0001 | -0.0003 | 0.0036 | 1 |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p02_s0p25 | residual_huber | 607 | 0.1389 | 0.2727 | 0.8100 | 0.3987 | 0.0001 | -0.0003 | 0.0036 | 1 |
| hcoef21_resid_ridge_adaptive_reliability_a0p1_cap0p02_s0p25 | residual_ridge | 607 | 0.1389 | 0.2729 | 0.8100 | 0.3988 | 0.0001 | -0.0001 | 0.0036 | 1 |
| hcoef21_resid_ridge_adaptive_reliability_a1_cap0p02_s0p25 | residual_ridge | 607 | 0.1389 | 0.2729 | 0.8100 | 0.3988 | 0.0001 | -0.0000 | 0.0036 | 1 |
| hcoef21_stable_toward_balanced_cap003_s025 | source | 607 | 0.1389 | 0.2727 | 0.8128 | 0.3983 | 0.0001 | -0.0003 | 0.0065 | 1 |
| hcoef21_stable_toward_conservative_cap003_s025 | source | 607 | 0.1392 | 0.2728 | 0.8120 | 0.3984 | 0.0004 | -0.0002 | 0.0056 | 1 |
| hcoef21_stable_toward_guard_cap005_s025 | source | 607 | 0.1399 | 0.2723 | 0.8195 | 0.3977 | 0.0011 | -0.0007 | 0.0131 | 1 |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p03_s0p25 | residual_huber | 607 | 0.1400 | 0.2726 | 0.8139 | 0.3987 | 0.0012 | -0.0004 | 0.0075 | 1 |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p03_s0p25 | residual_huber | 607 | 0.1400 | 0.2726 | 0.8139 | 0.3987 | 0.0012 | -0.0004 | 0.0075 | 1 |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p03_s0p25 | residual_huber | 607 | 0.1402 | 0.2727 | 0.8139 | 0.3987 | 0.0014 | -0.0003 | 0.0075 | 1 |
| hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p03_s0p25 | residual_huber | 607 | 0.1402 | 0.2727 | 0.8139 | 0.3987 | 0.0014 | -0.0003 | 0.0075 | 1 |
| hcoef21_resid_ridge_adaptive_reliability_a1_cap0p03_s0p25 | residual_ridge | 607 | 0.1403 | 0.2730 | 0.8145 | 0.3988 | 0.0014 | -0.0000 | 0.0081 | 1 |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p05_s0p25 | residual_huber | 607 | 0.1404 | 0.2726 | 0.8230 | 0.3988 | 0.0015 | -0.0004 | 0.0166 | 1 |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p05_s0p25 | residual_huber | 607 | 0.1404 | 0.2726 | 0.8230 | 0.3988 | 0.0015 | -0.0004 | 0.0166 | 1 |
| hcoef21_resid_ridge_adaptive_interactions_a1_cap0p03_s0p25 | residual_ridge | 607 | 0.1405 | 0.2728 | 0.8137 | 0.3986 | 0.0017 | -0.0002 | 0.0073 | 1 |

## 4. Validation Row OOF 상위 후보

| candidate | method | n | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable | improve_count_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef21_direct_huber_adaptive_basis_stack_a0p001 | direct_huber | 519 | 0.1213 | 0.2087 | 0.6725 | 0.3206 | -0.0047 | 0.0005 | 0.0246 | 1 |
| hcoef21_direct_huber_adaptive_basis_stack_a0p01 | direct_huber | 519 | 0.1229 | 0.2085 | 0.6706 | 0.3204 | -0.0031 | 0.0003 | 0.0227 | 1 |
| hcoef21_adaptive_conservative_plus_stable_delta | source | 519 | 0.1251 | 0.2132 | 0.6702 | 0.3301 | -0.0009 | 0.0050 | 0.0222 | 1 |
| hcoef_stable | source | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0 |
| hcoef21_resid_ridge_adaptive_interactions_a1_cap0p03_s0p5 | residual_ridge | 519 | 0.1262 | 0.2067 | 0.6475 | 0.3229 | 0.0002 | -0.0015 | -0.0004 | 2 |
| hcoef21_resid_ridge_adaptive_interactions_a0p1_cap0p03_s0p5 | residual_ridge | 519 | 0.1262 | 0.2067 | 0.6475 | 0.3229 | 0.0002 | -0.0015 | -0.0004 | 2 |
| hcoef21_resid_ridge_adaptive_interactions_a1_cap0p02_s0p25 | residual_ridge | 519 | 0.1263 | 0.2076 | 0.6409 | 0.3244 | 0.0003 | -0.0006 | -0.0070 | 2 |
| hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p02_s0p25 | residual_huber | 519 | 0.1263 | 0.2077 | 0.6409 | 0.3244 | 0.0003 | -0.0006 | -0.0070 | 2 |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p02_s0p25 | residual_huber | 519 | 0.1263 | 0.2077 | 0.6409 | 0.3244 | 0.0003 | -0.0006 | -0.0070 | 2 |
| hcoef21_resid_ridge_adaptive_interactions_a0p1_cap0p02_s0p25 | residual_ridge | 519 | 0.1263 | 0.2077 | 0.6409 | 0.3244 | 0.0003 | -0.0006 | -0.0070 | 2 |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p02_s0p25 | residual_huber | 519 | 0.1263 | 0.2078 | 0.6409 | 0.3246 | 0.0003 | -0.0004 | -0.0070 | 2 |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p02_s0p25 | residual_huber | 519 | 0.1263 | 0.2078 | 0.6409 | 0.3246 | 0.0003 | -0.0004 | -0.0070 | 2 |
| hcoef21_resid_ridge_adaptive_reliability_a0p1_cap0p02_s0p25 | residual_ridge | 519 | 0.1263 | 0.2079 | 0.6409 | 0.3245 | 0.0003 | -0.0003 | -0.0070 | 2 |
| hcoef21_resid_ridge_adaptive_reliability_a1_cap0p02_s0p25 | residual_ridge | 519 | 0.1263 | 0.2079 | 0.6409 | 0.3246 | 0.0003 | -0.0003 | -0.0070 | 2 |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p05_s0p25 | residual_huber | 519 | 0.1266 | 0.2074 | 0.6451 | 0.3240 | 0.0006 | -0.0008 | -0.0028 | 2 |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p05_s0p25 | residual_huber | 519 | 0.1266 | 0.2074 | 0.6451 | 0.3240 | 0.0006 | -0.0008 | -0.0028 | 2 |
| hcoef21_resid_ridge_adaptive_reliability_a1_cap0p03_s0p25 | residual_ridge | 519 | 0.1269 | 0.2078 | 0.6445 | 0.3243 | 0.0009 | -0.0004 | -0.0034 | 2 |
| hcoef21_stable_toward_conservative_cap003_s025 | source | 519 | 0.1270 | 0.2085 | 0.6417 | 0.3254 | 0.0010 | 0.0003 | -0.0063 | 1 |
| svc_numeric_seed_mean | source | 519 | 0.1272 | 0.2176 | 0.6504 | 0.3367 | 0.0012 | 0.0094 | 0.0024 | 0 |
| hcoef21_resid_ridge_adaptive_reliability_a0p1_cap0p03_s0p5 | residual_ridge | 519 | 0.1273 | 0.2076 | 0.6475 | 0.3234 | 0.0013 | -0.0006 | -0.0004 | 2 |

## 5. Bootstrap / Repeated Split 요약

| source_scope | validation_scheme | candidate | method | n_bootstrap | mean_delta_MdAPE_vs_stable | mean_delta_MAPE_vs_stable | mean_delta_p95_APE_vs_stable | mean_delta_RMSE_log_vs_stable | MdAPE_improve_prob | MAPE_improve_prob | p95_improve_prob | all3_improve_prob | any2_improve_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation_oof_row | row_bootstrap | hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p05_s0p25 | residual_huber | 300 | -0.0004 | -0.0008 | 0.0004 | -0.0012 | 0.5600 | 0.9600 | 0.5433 | 0.3300 | 0.7467 |
| validation_oof_row | row_bootstrap | hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p03_s0p25 | residual_huber | 300 | -0.0000 | -0.0005 | -0.0001 | -0.0008 | 0.5467 | 0.9533 | 0.5933 | 0.3267 | 0.7833 |
| validation_oof_row | row_bootstrap | hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p03_s0p25 | residual_huber | 300 | -0.0000 | -0.0005 | -0.0001 | -0.0008 | 0.5467 | 0.9533 | 0.5933 | 0.3267 | 0.7833 |
| validation_oof_row | row_bootstrap | hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p05_s0p25 | residual_huber | 300 | -0.0004 | -0.0008 | 0.0004 | -0.0012 | 0.5567 | 0.9600 | 0.5433 | 0.3267 | 0.7467 |
| validation_oof_row | artist_bootstrap | hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p05_s0p5 | residual_huber | 300 | -0.0013 | -0.0018 | -0.0014 | -0.0028 | 0.6233 | 0.9733 | 0.5433 | 0.3233 | 0.8167 |
| validation_oof_row | artist_bootstrap | hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p05_s0p5 | residual_huber | 300 | -0.0013 | -0.0018 | -0.0014 | -0.0028 | 0.6233 | 0.9733 | 0.5433 | 0.3233 | 0.8167 |
| validation_oof_artist | row_bootstrap | hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p05_s0p5 | residual_huber | 300 | -0.0022 | -0.0016 | 0.0045 | -0.0026 | 0.7500 | 0.9467 | 0.4200 | 0.3133 | 0.8167 |
| validation_oof_artist | row_bootstrap | hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p05_s0p5 | residual_huber | 300 | -0.0022 | -0.0016 | 0.0045 | -0.0026 | 0.7500 | 0.9467 | 0.4200 | 0.3133 | 0.8167 |
| validation_oof_row | artist_bootstrap | hcoef21_resid_ridge_adaptive_interactions_a0p1_cap0p02_s0p25 | residual_ridge | 300 | -0.0004 | -0.0006 | 0.0007 | -0.0008 | 0.6100 | 0.9867 | 0.4800 | 0.3133 | 0.7667 |
| validation_oof_row | artist_bootstrap | hcoef21_resid_ridge_adaptive_interactions_a0p1_cap0p03_s0p25 | residual_ridge | 300 | -0.0005 | -0.0009 | 0.0008 | -0.0012 | 0.6233 | 0.9900 | 0.4900 | 0.3100 | 0.7967 |
| validation_oof_row | artist_bootstrap | hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p02_s0p25 | residual_huber | 300 | -0.0003 | -0.0004 | 0.0006 | -0.0006 | 0.6067 | 0.9733 | 0.5200 | 0.3067 | 0.8000 |
| validation_oof_row | artist_bootstrap | hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p02_s0p25 | residual_huber | 300 | -0.0003 | -0.0004 | 0.0006 | -0.0006 | 0.6000 | 0.9733 | 0.5200 | 0.3067 | 0.7933 |
| validation_oof_row | row_bootstrap | hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p05_s0p5 | residual_huber | 300 | -0.0006 | -0.0017 | -0.0020 | -0.0028 | 0.5800 | 0.9767 | 0.5133 | 0.3067 | 0.7733 |
| validation_oof_row | row_bootstrap | hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p05_s0p5 | residual_huber | 300 | -0.0006 | -0.0017 | -0.0020 | -0.0028 | 0.5800 | 0.9767 | 0.5133 | 0.3067 | 0.7733 |
| validation_oof_row | artist_bootstrap | hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p03_s0p25 | residual_huber | 300 | -0.0005 | -0.0006 | 0.0008 | -0.0008 | 0.5800 | 0.9733 | 0.5233 | 0.3033 | 0.7867 |
| validation_oof_row | artist_bootstrap | hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p03_s0p25 | residual_huber | 300 | -0.0005 | -0.0006 | 0.0008 | -0.0008 | 0.5800 | 0.9733 | 0.5233 | 0.3033 | 0.7867 |
| validation_oof_row | row_bootstrap | hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p02_s0p25 | residual_huber | 300 | 0.0000 | -0.0004 | -0.0001 | -0.0006 | 0.5167 | 0.9467 | 0.5833 | 0.3033 | 0.7667 |
| validation_oof_row | row_bootstrap | hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p02_s0p25 | residual_huber | 300 | 0.0000 | -0.0004 | -0.0001 | -0.0006 | 0.5167 | 0.9467 | 0.5833 | 0.3033 | 0.7667 |
| validation_oof_row | artist_bootstrap | hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p03_s0p25 | residual_huber | 300 | -0.0004 | -0.0008 | -0.0000 | -0.0010 | 0.5933 | 0.9900 | 0.5000 | 0.3000 | 0.7867 |
| validation_oof_row | artist_bootstrap | hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p03_s0p25 | residual_huber | 300 | -0.0004 | -0.0008 | -0.0000 | -0.0010 | 0.5933 | 0.9900 | 0.5000 | 0.3000 | 0.7867 |

## 6. 가변 기준가 비율 요약

| split | segment_col | segment_value | n | mean_reliability_score | mean_svc_weight_conservative | mean_svc_weight_balanced | mean_svc_weight_ppv8_guard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_ex50 | svc_coverage_tier | fallback_global | 18 | 0.4778 | 0.5989 | 0.5256 | 0.2589 |
| 0604_ex50 | svc_coverage_tier | high_n | 87 | 0.8448 | 0.7866 | 0.7515 | 0.5348 |
| 0604_ex50 | svc_coverage_tier | low_n | 569 | 0.2253 | 0.5800 | 0.5224 | 0.3293 |
| 0604_ex50 | svc_coverage_tier | medium_n | 155 | 0.6246 | 0.7324 | 0.7073 | 0.5171 |
| 0604_ex50 | svc_group_n_band | n_10_19 | 199 | 0.3973 | 0.6395 | 0.5946 | 0.3857 |
| 0604_ex50 | svc_group_n_band | n_20_49 | 90 | 0.6677 | 0.7518 | 0.7292 | 0.5581 |
| 0604_ex50 | svc_group_n_band | n_50_plus | 105 | 0.7819 | 0.7545 | 0.7128 | 0.4875 |
| 0604_ex50 | svc_group_n_band | n_5_9 | 435 | 0.1973 | 0.5715 | 0.5125 | 0.3231 |
| 0604_ex50 | qwidth_band | qwidth_extreme | 301 | 0.3019 | 0.5489 | 0.4640 | 0.2864 |
| 0604_ex50 | qwidth_band | qwidth_high | 185 | 0.3348 | 0.6534 | 0.6204 | 0.3815 |
| 0604_ex50 | qwidth_band | qwidth_low | 101 | 0.5051 | 0.7103 | 0.6857 | 0.4924 |
| 0604_ex50 | qwidth_band | qwidth_mid | 242 | 0.4267 | 0.6815 | 0.6531 | 0.4637 |
| test | svc_coverage_tier | high_n | 17 | 0.9911 | 0.8500 | 0.8500 | 0.8451 |
| test | svc_coverage_tier | low_n | 479 | 0.2446 | 0.5942 | 0.5418 | 0.3732 |
| test | svc_coverage_tier | medium_n | 111 | 0.6640 | 0.7616 | 0.7427 | 0.6539 |
| test | svc_group_n_band | n_10_19 | 162 | 0.4193 | 0.6517 | 0.6106 | 0.4832 |
| test | svc_group_n_band | n_20_49 | 62 | 0.7151 | 0.7916 | 0.7760 | 0.6885 |
| test | svc_group_n_band | n_50_plus | 17 | 0.9911 | 0.8500 | 0.8500 | 0.8451 |
| test | svc_group_n_band | n_5_9 | 366 | 0.2148 | 0.5860 | 0.5325 | 0.3563 |
| test | qwidth_band | qwidth_extreme | 145 | 0.1651 | 0.4995 | 0.4078 | 0.2626 |
| test | qwidth_band | qwidth_high | 97 | 0.2458 | 0.6248 | 0.5871 | 0.3974 |
| test | qwidth_band | qwidth_low | 169 | 0.5257 | 0.7164 | 0.6928 | 0.5782 |
| test | qwidth_band | qwidth_mid | 196 | 0.3627 | 0.6606 | 0.6288 | 0.4662 |
| validation | svc_coverage_tier | high_n | 5 | 0.9992 | 0.8500 | 0.8500 | 0.8496 |
| validation | svc_coverage_tier | low_n | 421 | 0.2689 | 0.6091 | 0.5617 | 0.4003 |
| validation | svc_coverage_tier | medium_n | 93 | 0.6466 | 0.7481 | 0.7236 | 0.6170 |
| validation | svc_group_n_band | n_10_19 | 160 | 0.4024 | 0.6501 | 0.6099 | 0.4692 |
| validation | svc_group_n_band | n_20_49 | 54 | 0.7039 | 0.7831 | 0.7639 | 0.6593 |
| validation | svc_group_n_band | n_50_plus | 5 | 0.9992 | 0.8500 | 0.8500 | 0.8496 |
| validation | svc_group_n_band | n_5_9 | 300 | 0.2365 | 0.5989 | 0.5498 | 0.3841 |
| validation | qwidth_band | qwidth_extreme | 104 | 0.1914 | 0.5074 | 0.4170 | 0.2768 |
| validation | qwidth_band | qwidth_high | 73 | 0.2452 | 0.6249 | 0.5872 | 0.3963 |
| validation | qwidth_band | qwidth_low | 171 | 0.4650 | 0.6973 | 0.6706 | 0.5461 |
| validation | qwidth_band | qwidth_mid | 171 | 0.3568 | 0.6585 | 0.6264 | 0.4623 |

## 7. 계수 해석

| candidate | method | feature | standardized_coefficient | raw_role | direction | interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| hcoef_stable | source | hcoef_stable | 1.0000 | source_prediction | positive | 현재 HCOEF 안정 후보 |
| current_70_30 | source | current_70_30 | 1.0000 | source_prediction | positive | 고정 70:30 기준 후보 |
| ppv8_service_proxy | source | ppv8_service_proxy | 1.0000 | source_prediction | positive | 오차 안정화 component |
| svc_numeric_seed_mean | source | svc_numeric_seed_mean | 1.0000 | source_prediction | positive | 유사 작품 기반 가격 피처 |
| l10_seq_full_generated_bucket | source | l10_seq_pred_log | 1.0000 | source_prediction | positive | PP-L10 순차 component |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p02_s0p25 | residual_huber | adaptive_basis_conservative_minus_stable | -0.1551 | residual_log | lowers prediction | 표본 수, coverage, quantile 폭으로 조정한 SVC:PP-V8 가변 기준가와 현재 안정 후보의 차이를 반영한다. |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p02_s0p25 | residual_huber | adaptive_basis_balanced_minus_stable | 0.0563 | residual_log | raises prediction | 표본 수, coverage, quantile 폭으로 조정한 SVC:PP-V8 가변 기준가와 현재 안정 후보의 차이를 반영한다. |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p02_s0p25 | residual_huber | adaptive_basis_ppv8_guard_minus_stable | 0.0685 | residual_log | raises prediction | 표본 수, coverage, quantile 폭으로 조정한 SVC:PP-V8 가변 기준가와 현재 안정 후보의 차이를 반영한다. |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p02_s0p25 | residual_huber | basis_reliability_score | 0.0029 | residual_log | raises prediction | 유사 표본 수와 coverage가 높고 quantile 폭이 좁을수록 기준가 신뢰도가 높다는 신호다. |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p02_s0p25 | residual_huber | basis_low_reliability | -0.0102 | residual_log | lowers prediction | 유사 기준가를 강하게 믿기 어려운 구간인지 나타내는 이진 신호다. |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p02_s0p25 | residual_huber | basis_high_reliability | 0.0005 | residual_log | raises prediction | 유사 기준가를 상대적으로 더 신뢰할 수 있는 구간인지 나타내는 이진 신호다. |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p02_s0p25 | residual_huber | basis_qwidth_extreme | 0.0077 | residual_log | raises prediction | 예측 범위가 넓어 점 예측 이동을 조심해야 하는 구간인지 나타낸다. |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p02_s0p25 | residual_huber | svc_group_n_log | -0.0193 | residual_log | lowers prediction | 유사 표본 수가 많을수록 기준가 신뢰도가 높다는 신호다. |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p02_s0p25 | residual_huber | coverage_numeric | 0.0056 | residual_log | raises prediction | 유사 표본 수 coverage tier를 숫자로 바꾼 신뢰도 피처다. |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p02_s0p25 | residual_huber | quantile_width | -0.0008 | residual_log | lowers prediction | 예측 범위가 넓은 샘플에서 residual 보정 방향이 달라지는지 확인한다. |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p02_s0p25 | residual_huber | pred_spread | -0.0000 | residual_log | lowers prediction | component 간 예측값 차이가 큰 샘플의 위험도를 나타낸다. |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p03_s0p25 | residual_huber | adaptive_basis_conservative_minus_stable | -0.1551 | residual_log | lowers prediction | 표본 수, coverage, quantile 폭으로 조정한 SVC:PP-V8 가변 기준가와 현재 안정 후보의 차이를 반영한다. |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p03_s0p25 | residual_huber | adaptive_basis_balanced_minus_stable | 0.0563 | residual_log | raises prediction | 표본 수, coverage, quantile 폭으로 조정한 SVC:PP-V8 가변 기준가와 현재 안정 후보의 차이를 반영한다. |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p03_s0p25 | residual_huber | adaptive_basis_ppv8_guard_minus_stable | 0.0685 | residual_log | raises prediction | 표본 수, coverage, quantile 폭으로 조정한 SVC:PP-V8 가변 기준가와 현재 안정 후보의 차이를 반영한다. |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p03_s0p25 | residual_huber | basis_reliability_score | 0.0029 | residual_log | raises prediction | 유사 표본 수와 coverage가 높고 quantile 폭이 좁을수록 기준가 신뢰도가 높다는 신호다. |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p03_s0p25 | residual_huber | basis_low_reliability | -0.0102 | residual_log | lowers prediction | 유사 기준가를 강하게 믿기 어려운 구간인지 나타내는 이진 신호다. |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p03_s0p25 | residual_huber | basis_high_reliability | 0.0005 | residual_log | raises prediction | 유사 기준가를 상대적으로 더 신뢰할 수 있는 구간인지 나타내는 이진 신호다. |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p03_s0p25 | residual_huber | basis_qwidth_extreme | 0.0077 | residual_log | raises prediction | 예측 범위가 넓어 점 예측 이동을 조심해야 하는 구간인지 나타낸다. |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p03_s0p25 | residual_huber | svc_group_n_log | -0.0193 | residual_log | lowers prediction | 유사 표본 수가 많을수록 기준가 신뢰도가 높다는 신호다. |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p03_s0p25 | residual_huber | coverage_numeric | 0.0056 | residual_log | raises prediction | 유사 표본 수 coverage tier를 숫자로 바꾼 신뢰도 피처다. |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p03_s0p25 | residual_huber | quantile_width | -0.0008 | residual_log | lowers prediction | 예측 범위가 넓은 샘플에서 residual 보정 방향이 달라지는지 확인한다. |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p03_s0p25 | residual_huber | pred_spread | -0.0000 | residual_log | lowers prediction | component 간 예측값 차이가 큰 샘플의 위험도를 나타낸다. |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p02_s0p25 | residual_huber | adaptive_basis_conservative_minus_stable | -0.1550 | residual_log | lowers prediction | 표본 수, coverage, quantile 폭으로 조정한 SVC:PP-V8 가변 기준가와 현재 안정 후보의 차이를 반영한다. |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p02_s0p25 | residual_huber | adaptive_basis_balanced_minus_stable | 0.0563 | residual_log | raises prediction | 표본 수, coverage, quantile 폭으로 조정한 SVC:PP-V8 가변 기준가와 현재 안정 후보의 차이를 반영한다. |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p02_s0p25 | residual_huber | adaptive_basis_ppv8_guard_minus_stable | 0.0685 | residual_log | raises prediction | 표본 수, coverage, quantile 폭으로 조정한 SVC:PP-V8 가변 기준가와 현재 안정 후보의 차이를 반영한다. |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p02_s0p25 | residual_huber | basis_reliability_score | 0.0030 | residual_log | raises prediction | 유사 표본 수와 coverage가 높고 quantile 폭이 좁을수록 기준가 신뢰도가 높다는 신호다. |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p02_s0p25 | residual_huber | basis_low_reliability | -0.0102 | residual_log | lowers prediction | 유사 기준가를 강하게 믿기 어려운 구간인지 나타내는 이진 신호다. |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p02_s0p25 | residual_huber | basis_high_reliability | 0.0005 | residual_log | raises prediction | 유사 기준가를 상대적으로 더 신뢰할 수 있는 구간인지 나타내는 이진 신호다. |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p02_s0p25 | residual_huber | basis_qwidth_extreme | 0.0077 | residual_log | raises prediction | 예측 범위가 넓어 점 예측 이동을 조심해야 하는 구간인지 나타낸다. |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p02_s0p25 | residual_huber | svc_group_n_log | -0.0193 | residual_log | lowers prediction | 유사 표본 수가 많을수록 기준가 신뢰도가 높다는 신호다. |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p02_s0p25 | residual_huber | coverage_numeric | 0.0056 | residual_log | raises prediction | 유사 표본 수 coverage tier를 숫자로 바꾼 신뢰도 피처다. |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p02_s0p25 | residual_huber | quantile_width | -0.0008 | residual_log | lowers prediction | 예측 범위가 넓은 샘플에서 residual 보정 방향이 달라지는지 확인한다. |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p02_s0p25 | residual_huber | pred_spread | -0.0000 | residual_log | lowers prediction | component 간 예측값 차이가 큰 샘플의 위험도를 나타낸다. |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p03_s0p25 | residual_huber | adaptive_basis_conservative_minus_stable | -0.1550 | residual_log | lowers prediction | 표본 수, coverage, quantile 폭으로 조정한 SVC:PP-V8 가변 기준가와 현재 안정 후보의 차이를 반영한다. |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p03_s0p25 | residual_huber | adaptive_basis_balanced_minus_stable | 0.0563 | residual_log | raises prediction | 표본 수, coverage, quantile 폭으로 조정한 SVC:PP-V8 가변 기준가와 현재 안정 후보의 차이를 반영한다. |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p03_s0p25 | residual_huber | adaptive_basis_ppv8_guard_minus_stable | 0.0685 | residual_log | raises prediction | 표본 수, coverage, quantile 폭으로 조정한 SVC:PP-V8 가변 기준가와 현재 안정 후보의 차이를 반영한다. |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p03_s0p25 | residual_huber | basis_reliability_score | 0.0030 | residual_log | raises prediction | 유사 표본 수와 coverage가 높고 quantile 폭이 좁을수록 기준가 신뢰도가 높다는 신호다. |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p03_s0p25 | residual_huber | basis_low_reliability | -0.0102 | residual_log | lowers prediction | 유사 기준가를 강하게 믿기 어려운 구간인지 나타내는 이진 신호다. |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p03_s0p25 | residual_huber | basis_high_reliability | 0.0005 | residual_log | raises prediction | 유사 기준가를 상대적으로 더 신뢰할 수 있는 구간인지 나타내는 이진 신호다. |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p03_s0p25 | residual_huber | basis_qwidth_extreme | 0.0077 | residual_log | raises prediction | 예측 범위가 넓어 점 예측 이동을 조심해야 하는 구간인지 나타낸다. |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p03_s0p25 | residual_huber | svc_group_n_log | -0.0193 | residual_log | lowers prediction | 유사 표본 수가 많을수록 기준가 신뢰도가 높다는 신호다. |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p03_s0p25 | residual_huber | coverage_numeric | 0.0056 | residual_log | raises prediction | 유사 표본 수 coverage tier를 숫자로 바꾼 신뢰도 피처다. |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p03_s0p25 | residual_huber | quantile_width | -0.0008 | residual_log | lowers prediction | 예측 범위가 넓은 샘플에서 residual 보정 방향이 달라지는지 확인한다. |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p03_s0p25 | residual_huber | pred_spread | -0.0000 | residual_log | lowers prediction | component 간 예측값 차이가 큰 샘플의 위험도를 나타낸다. |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p02_s0p25 | residual_huber | adaptive_basis_conservative_minus_stable | -0.0651 | residual_log | lowers prediction | 표본 수, coverage, quantile 폭으로 조정한 SVC:PP-V8 가변 기준가와 현재 안정 후보의 차이를 반영한다. |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p02_s0p25 | residual_huber | adaptive_basis_ppv8_guard_minus_stable | 0.0331 | residual_log | raises prediction | 표본 수, coverage, quantile 폭으로 조정한 SVC:PP-V8 가변 기준가와 현재 안정 후보의 차이를 반영한다. |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p02_s0p25 | residual_huber | svc_minus_stable_x_reliable | -0.0228 | residual_log | lowers prediction | 유사 기준가가 안정 후보와 다른 방향을 보일 때, 신뢰도가 높을수록 더 반영할지 확인한다. |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p02_s0p25 | residual_huber | ppv8_minus_stable_x_lowrel | -0.0119 | residual_log | lowers prediction | 유사 표본 신뢰도가 낮은 구간에서 오차 안정화 component 쪽으로 이동할지 확인한다. |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p02_s0p25 | residual_huber | current_minus_stable_x_qextreme | -0.0329 | residual_log | lowers prediction | quantile 폭이 큰 구간에서 기존 70:30 후보와 안정 후보의 차이를 조심스럽게 반영한다. |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p02_s0p25 | residual_huber | adaptive_conservative_gap_x_reliability | 0.0036 | residual_log | raises prediction | 표준화 계수 0.0036로 잔차 또는 로그 가격을 보조한다. |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p02_s0p25 | residual_huber | basis_reliability_score | -0.0082 | residual_log | lowers prediction | 유사 표본 수와 coverage가 높고 quantile 폭이 좁을수록 기준가 신뢰도가 높다는 신호다. |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p02_s0p25 | residual_huber | basis_low_reliability | -0.0084 | residual_log | lowers prediction | 유사 기준가를 강하게 믿기 어려운 구간인지 나타내는 이진 신호다. |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p02_s0p25 | residual_huber | basis_qwidth_extreme | 0.0052 | residual_log | raises prediction | 예측 범위가 넓어 점 예측 이동을 조심해야 하는 구간인지 나타낸다. |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p02_s0p25 | residual_huber | pred_spread | 0.0031 | residual_log | raises prediction | component 간 예측값 차이가 큰 샘플의 위험도를 나타낸다. |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p02_s0p25 | residual_huber | log_area_filled | -0.0027 | residual_log | lowers prediction | 표준화 계수 -0.0027로 잔차 또는 로그 가격을 보조한다. |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p03_s0p25 | residual_huber | adaptive_basis_conservative_minus_stable | -0.0651 | residual_log | lowers prediction | 표본 수, coverage, quantile 폭으로 조정한 SVC:PP-V8 가변 기준가와 현재 안정 후보의 차이를 반영한다. |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p03_s0p25 | residual_huber | adaptive_basis_ppv8_guard_minus_stable | 0.0331 | residual_log | raises prediction | 표본 수, coverage, quantile 폭으로 조정한 SVC:PP-V8 가변 기준가와 현재 안정 후보의 차이를 반영한다. |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p03_s0p25 | residual_huber | svc_minus_stable_x_reliable | -0.0228 | residual_log | lowers prediction | 유사 기준가가 안정 후보와 다른 방향을 보일 때, 신뢰도가 높을수록 더 반영할지 확인한다. |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p03_s0p25 | residual_huber | ppv8_minus_stable_x_lowrel | -0.0119 | residual_log | lowers prediction | 유사 표본 신뢰도가 낮은 구간에서 오차 안정화 component 쪽으로 이동할지 확인한다. |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p03_s0p25 | residual_huber | current_minus_stable_x_qextreme | -0.0329 | residual_log | lowers prediction | quantile 폭이 큰 구간에서 기존 70:30 후보와 안정 후보의 차이를 조심스럽게 반영한다. |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p03_s0p25 | residual_huber | adaptive_conservative_gap_x_reliability | 0.0036 | residual_log | raises prediction | 표준화 계수 0.0036로 잔차 또는 로그 가격을 보조한다. |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p03_s0p25 | residual_huber | basis_reliability_score | -0.0082 | residual_log | lowers prediction | 유사 표본 수와 coverage가 높고 quantile 폭이 좁을수록 기준가 신뢰도가 높다는 신호다. |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p03_s0p25 | residual_huber | basis_low_reliability | -0.0084 | residual_log | lowers prediction | 유사 기준가를 강하게 믿기 어려운 구간인지 나타내는 이진 신호다. |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p03_s0p25 | residual_huber | basis_qwidth_extreme | 0.0052 | residual_log | raises prediction | 예측 범위가 넓어 점 예측 이동을 조심해야 하는 구간인지 나타낸다. |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p03_s0p25 | residual_huber | pred_spread | 0.0031 | residual_log | raises prediction | component 간 예측값 차이가 큰 샘플의 위험도를 나타낸다. |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p03_s0p25 | residual_huber | log_area_filled | -0.0027 | residual_log | lowers prediction | 표준화 계수 -0.0027로 잔차 또는 로그 가격을 보조한다. |
| hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p02_s0p25 | residual_huber | adaptive_basis_conservative_minus_stable | -0.0651 | residual_log | lowers prediction | 표본 수, coverage, quantile 폭으로 조정한 SVC:PP-V8 가변 기준가와 현재 안정 후보의 차이를 반영한다. |
| hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p02_s0p25 | residual_huber | adaptive_basis_ppv8_guard_minus_stable | 0.0330 | residual_log | raises prediction | 표본 수, coverage, quantile 폭으로 조정한 SVC:PP-V8 가변 기준가와 현재 안정 후보의 차이를 반영한다. |
| hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p02_s0p25 | residual_huber | svc_minus_stable_x_reliable | -0.0229 | residual_log | lowers prediction | 유사 기준가가 안정 후보와 다른 방향을 보일 때, 신뢰도가 높을수록 더 반영할지 확인한다. |
| hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p02_s0p25 | residual_huber | ppv8_minus_stable_x_lowrel | -0.0119 | residual_log | lowers prediction | 유사 표본 신뢰도가 낮은 구간에서 오차 안정화 component 쪽으로 이동할지 확인한다. |
| hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p02_s0p25 | residual_huber | current_minus_stable_x_qextreme | -0.0329 | residual_log | lowers prediction | quantile 폭이 큰 구간에서 기존 70:30 후보와 안정 후보의 차이를 조심스럽게 반영한다. |
| hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p02_s0p25 | residual_huber | adaptive_conservative_gap_x_reliability | 0.0036 | residual_log | raises prediction | 표준화 계수 0.0036로 잔차 또는 로그 가격을 보조한다. |
| hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p02_s0p25 | residual_huber | basis_reliability_score | -0.0082 | residual_log | lowers prediction | 유사 표본 수와 coverage가 높고 quantile 폭이 좁을수록 기준가 신뢰도가 높다는 신호다. |
| hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p02_s0p25 | residual_huber | basis_low_reliability | -0.0084 | residual_log | lowers prediction | 유사 기준가를 강하게 믿기 어려운 구간인지 나타내는 이진 신호다. |
| hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p02_s0p25 | residual_huber | basis_qwidth_extreme | 0.0052 | residual_log | raises prediction | 예측 범위가 넓어 점 예측 이동을 조심해야 하는 구간인지 나타낸다. |

## 8. 잔차 구간 분석

| scope | split | candidate | segment_col | segment_value | n | MdAPE | MAPE | p95_APE | median_residual_log | mean_residual_log | mean_abs_move_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_stress | 0604_ex50 | svc_numeric_seed_mean | gap_band | gap_020_plus | 402 | 0.5239 | 0.6071 | 1.3189 | 0.3621 | 0.7716 | 0.2761 |
| 0604_stress | 0604_ex50 | l10_seq_full_generated_bucket | gap_band | gap_020_plus | 402 | 0.5130 | 0.5988 | 1.5918 | 0.1562 | 0.5032 | 0.5894 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_020_plus | 402 | 0.4302 | 0.5054 | 1.0000 | 0.2961 | 0.6185 | 0.0225 |
| 0604_stress | 0604_ex50 | hcoef_stable | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p02_s0p25 | gap_band | gap_020_plus | 402 | 0.4316 | 0.5035 | 0.9999 | 0.2749 | 0.6045 | 0.0046 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p02_s0p25 | gap_band | gap_020_plus | 402 | 0.4315 | 0.5035 | 0.9999 | 0.2749 | 0.6045 | 0.0046 |
| 0604_stress | 0604_ex50 | hcoef21_resid_ridge_adaptive_reliability_a1_cap0p02_s0p25 | gap_band | gap_020_plus | 402 | 0.4315 | 0.5032 | 0.9999 | 0.2749 | 0.6033 | 0.0047 |
| 0604_stress | 0604_ex50 | hcoef21_resid_ridge_adaptive_reliability_a0p1_cap0p02_s0p25 | gap_band | gap_020_plus | 402 | 0.4315 | 0.5032 | 0.9999 | 0.2749 | 0.6032 | 0.0047 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p02_s0p25 | gap_band | gap_020_plus | 402 | 0.4315 | 0.5030 | 0.9999 | 0.2772 | 0.6025 | 0.0048 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p02_s0p25 | gap_band | gap_020_plus | 402 | 0.4315 | 0.5030 | 0.9999 | 0.2772 | 0.6025 | 0.0048 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p03_s0p25 | gap_band | gap_020_plus | 402 | 0.4301 | 0.5029 | 0.9999 | 0.2729 | 0.6047 | 0.0067 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p03_s0p25 | gap_band | gap_020_plus | 402 | 0.4301 | 0.5029 | 0.9999 | 0.2729 | 0.6047 | 0.0067 |
| 0604_stress | 0604_ex50 | hcoef21_resid_ridge_adaptive_interactions_a1_cap0p02_s0p25 | gap_band | gap_020_plus | 402 | 0.4315 | 0.5028 | 0.9999 | 0.2776 | 0.6029 | 0.0049 |
| 0604_stress | 0604_ex50 | hcoef21_resid_ridge_adaptive_interactions_a0p1_cap0p02_s0p25 | gap_band | gap_020_plus | 402 | 0.4315 | 0.5028 | 0.9999 | 0.2776 | 0.6029 | 0.0049 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p03_s0p25 | gap_band | gap_020_plus | 402 | 0.4298 | 0.5023 | 0.9999 | 0.2757 | 0.6017 | 0.0069 |
| 0604_stress | 0604_ex50 | l10_seq_full_generated_bucket | gap_band | gap_010_020 | 128 | 0.3203 | 0.4882 | 2.1936 | -0.0384 | 0.0639 | 0.3592 |
| 0604_stress | 0604_ex50 | ppv8_service_proxy | gap_band | gap_020_plus | 402 | 0.3131 | 0.4234 | 1.1510 | 0.1623 | 0.2613 | 0.6194 |
| 0604_stress | 0604_ex50 | svc_numeric_seed_mean | gap_band | gap_010_020 | 128 | 0.2777 | 0.3693 | 0.9720 | -0.0734 | 0.0324 | 0.0620 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_010_020 | 128 | 0.2248 | 0.3419 | 0.8656 | -0.0556 | 0.0461 | 0.0217 |
| 0604_stress | 0604_ex50 | hcoef_stable | gap_band | gap_010_020 | 128 | 0.2255 | 0.3393 | 0.8728 | -0.0465 | 0.0399 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef21_resid_ridge_adaptive_reliability_a1_cap0p02_s0p25 | gap_band | gap_010_020 | 128 | 0.2194 | 0.3388 | 0.8762 | -0.0415 | 0.0390 | 0.0048 |
| 0604_stress | 0604_ex50 | hcoef21_resid_ridge_adaptive_reliability_a0p1_cap0p02_s0p25 | gap_band | gap_010_020 | 128 | 0.2194 | 0.3388 | 0.8763 | -0.0415 | 0.0389 | 0.0048 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p02_s0p25 | gap_band | gap_010_020 | 128 | 0.2194 | 0.3388 | 0.8757 | -0.0415 | 0.0390 | 0.0046 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p02_s0p25 | gap_band | gap_010_020 | 128 | 0.2194 | 0.3388 | 0.8757 | -0.0415 | 0.0390 | 0.0046 |
| 0604_stress | 0604_ex50 | hcoef21_resid_ridge_adaptive_interactions_a0p1_cap0p02_s0p25 | gap_band | gap_010_020 | 128 | 0.2194 | 0.3387 | 0.8765 | -0.0415 | 0.0391 | 0.0047 |
| 0604_stress | 0604_ex50 | hcoef21_resid_ridge_adaptive_interactions_a1_cap0p02_s0p25 | gap_band | gap_010_020 | 128 | 0.2194 | 0.3387 | 0.8765 | -0.0415 | 0.0392 | 0.0047 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p03_s0p25 | gap_band | gap_010_020 | 128 | 0.2170 | 0.3386 | 0.8772 | -0.0390 | 0.0386 | 0.0068 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p03_s0p25 | gap_band | gap_010_020 | 128 | 0.2170 | 0.3386 | 0.8772 | -0.0390 | 0.0386 | 0.0068 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p02_s0p25 | gap_band | gap_010_020 | 128 | 0.2194 | 0.3384 | 0.8757 | -0.0415 | 0.0390 | 0.0047 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p02_s0p25 | gap_band | gap_010_020 | 128 | 0.2194 | 0.3384 | 0.8757 | -0.0415 | 0.0390 | 0.0047 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p03_s0p25 | gap_band | gap_010_020 | 128 | 0.2164 | 0.3380 | 0.8772 | -0.0390 | 0.0386 | 0.0068 |
| 0604_stress | 0604_ex50 | ppv8_service_proxy | gap_band | gap_010_020 | 128 | 0.2540 | 0.3269 | 0.7844 | 0.0520 | 0.0782 | 0.1447 |
| 0604_stress | 0604_ex50 | l10_seq_full_generated_bucket | gap_band | gap_005_010 | 125 | 0.1883 | 0.3007 | 0.9169 | 0.0567 | 0.0972 | 0.1938 |
| 0604_stress | 0604_ex50 | ppv8_service_proxy | gap_band | gap_005_010 | 125 | 0.1764 | 0.2618 | 0.7685 | 0.0806 | 0.0930 | 0.0754 |
| 0604_stress | 0604_ex50 | svc_numeric_seed_mean | gap_band | gap_005_010 | 125 | 0.1613 | 0.2612 | 0.9572 | 0.0380 | 0.0895 | 0.0361 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_005_010 | 125 | 0.1531 | 0.2572 | 0.9461 | 0.0641 | 0.0905 | 0.0190 |
| 0604_stress | 0604_ex50 | hcoef_stable | gap_band | gap_005_010 | 125 | 0.1498 | 0.2514 | 0.9526 | 0.0403 | 0.0872 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef21_resid_ridge_adaptive_reliability_a0p1_cap0p02_s0p25 | gap_band | gap_005_010 | 125 | 0.1494 | 0.2508 | 0.9464 | 0.0353 | 0.0863 | 0.0047 |
| 0604_stress | 0604_ex50 | hcoef21_resid_ridge_adaptive_reliability_a1_cap0p02_s0p25 | gap_band | gap_005_010 | 125 | 0.1494 | 0.2508 | 0.9464 | 0.0353 | 0.0863 | 0.0047 |
| 0604_stress | 0604_ex50 | hcoef21_resid_ridge_adaptive_interactions_a1_cap0p02_s0p25 | gap_band | gap_005_010 | 125 | 0.1494 | 0.2506 | 0.9464 | 0.0353 | 0.0864 | 0.0045 |
| 0604_stress | 0604_ex50 | hcoef21_resid_ridge_adaptive_interactions_a0p1_cap0p02_s0p25 | gap_band | gap_005_010 | 125 | 0.1494 | 0.2506 | 0.9464 | 0.0353 | 0.0864 | 0.0045 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p02_s0p25 | gap_band | gap_005_010 | 125 | 0.1494 | 0.2506 | 0.9464 | 0.0353 | 0.0863 | 0.0044 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p02_s0p25 | gap_band | gap_005_010 | 125 | 0.1494 | 0.2506 | 0.9464 | 0.0353 | 0.0863 | 0.0044 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p02_s0p25 | gap_band | gap_005_010 | 125 | 0.1494 | 0.2504 | 0.9464 | 0.0353 | 0.0865 | 0.0044 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p02_s0p25 | gap_band | gap_005_010 | 125 | 0.1494 | 0.2504 | 0.9464 | 0.0353 | 0.0865 | 0.0044 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p03_s0p25 | gap_band | gap_005_010 | 125 | 0.1523 | 0.2502 | 0.9433 | 0.0328 | 0.0859 | 0.0062 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p03_s0p25 | gap_band | gap_005_010 | 125 | 0.1520 | 0.2499 | 0.9433 | 0.0328 | 0.0860 | 0.0062 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p03_s0p25 | gap_band | gap_005_010 | 125 | 0.1520 | 0.2499 | 0.9433 | 0.0328 | 0.0860 | 0.0062 |
| 0604_stress | 0604_ex50 | l10_seq_full_generated_bucket | gap_band | gap_000_003 | 119 | 0.1387 | 0.2330 | 0.7125 | -0.0071 | 0.0833 | 0.1325 |
| 0604_stress | 0604_ex50 | l10_seq_full_generated_bucket | gap_band | gap_003_005 | 55 | 0.1531 | 0.2296 | 0.5665 | -0.0167 | 0.1022 | 0.2173 |
| 0604_stress | 0604_ex50 | svc_numeric_seed_mean | gap_band | gap_000_003 | 119 | 0.1025 | 0.1967 | 0.5508 | 0.0404 | 0.0785 | 0.0222 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_000_003 | 119 | 0.1066 | 0.1953 | 0.5444 | 0.0401 | 0.0761 | 0.0164 |
| 0604_stress | 0604_ex50 | ppv8_service_proxy | gap_band | gap_000_003 | 119 | 0.1162 | 0.1942 | 0.5405 | 0.0395 | 0.0705 | 0.0125 |
| 0604_stress | 0604_ex50 | ppv8_service_proxy | gap_band | gap_003_005 | 55 | 0.1039 | 0.1925 | 0.4983 | 0.0427 | 0.0915 | 0.0397 |
| 0604_stress | 0604_ex50 | svc_numeric_seed_mean | gap_band | gap_003_005 | 55 | 0.1117 | 0.1922 | 0.5421 | 0.0171 | 0.0778 | 0.0356 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_003_005 | 55 | 0.0809 | 0.1908 | 0.5325 | 0.0305 | 0.0819 | 0.0227 |
| 0604_stress | 0604_ex50 | hcoef_stable | gap_band | gap_000_003 | 119 | 0.1053 | 0.1886 | 0.5300 | 0.0272 | 0.0704 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef21_resid_ridge_adaptive_reliability_a1_cap0p02_s0p25 | gap_band | gap_000_003 | 119 | 0.0998 | 0.1882 | 0.5276 | 0.0279 | 0.0699 | 0.0044 |
| 0604_stress | 0604_ex50 | hcoef21_resid_ridge_adaptive_reliability_a0p1_cap0p02_s0p25 | gap_band | gap_000_003 | 119 | 0.0998 | 0.1882 | 0.5276 | 0.0273 | 0.0699 | 0.0044 |
| 0604_stress | 0604_ex50 | hcoef21_resid_ridge_adaptive_interactions_a0p1_cap0p02_s0p25 | gap_band | gap_000_003 | 119 | 0.0998 | 0.1877 | 0.5276 | 0.0222 | 0.0687 | 0.0043 |
| 0604_stress | 0604_ex50 | hcoef21_resid_ridge_adaptive_interactions_a1_cap0p02_s0p25 | gap_band | gap_000_003 | 119 | 0.0998 | 0.1877 | 0.5276 | 0.0222 | 0.0687 | 0.0043 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p02_s0p25 | gap_band | gap_000_003 | 119 | 0.0998 | 0.1876 | 0.5276 | 0.0222 | 0.0694 | 0.0044 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p02_s0p25 | gap_band | gap_000_003 | 119 | 0.0998 | 0.1876 | 0.5276 | 0.0222 | 0.0694 | 0.0044 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p02_s0p25 | gap_band | gap_000_003 | 119 | 0.0998 | 0.1875 | 0.5276 | 0.0226 | 0.0693 | 0.0041 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p02_s0p25 | gap_band | gap_000_003 | 119 | 0.0998 | 0.1875 | 0.5276 | 0.0226 | 0.0693 | 0.0041 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p03_s0p25 | gap_band | gap_000_003 | 119 | 0.0970 | 0.1873 | 0.5264 | 0.0226 | 0.0688 | 0.0055 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p03_s0p25 | gap_band | gap_000_003 | 119 | 0.0970 | 0.1870 | 0.5264 | 0.0203 | 0.0689 | 0.0063 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p03_s0p25 | gap_band | gap_000_003 | 119 | 0.0970 | 0.1870 | 0.5264 | 0.0203 | 0.0689 | 0.0063 |
| 0604_stress | 0604_ex50 | hcoef_stable | gap_band | gap_003_005 | 55 | 0.0868 | 0.1845 | 0.5173 | 0.0125 | 0.0816 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef21_resid_ridge_adaptive_reliability_a1_cap0p02_s0p25 | gap_band | gap_003_005 | 55 | 0.0914 | 0.1836 | 0.5131 | 0.0075 | 0.0818 | 0.0048 |
| 0604_stress | 0604_ex50 | hcoef21_resid_ridge_adaptive_reliability_a0p1_cap0p02_s0p25 | gap_band | gap_003_005 | 55 | 0.0914 | 0.1836 | 0.5131 | 0.0075 | 0.0818 | 0.0048 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p02_s0p25 | gap_band | gap_003_005 | 55 | 0.0914 | 0.1835 | 0.5131 | 0.0075 | 0.0816 | 0.0048 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p02_s0p25 | gap_band | gap_003_005 | 55 | 0.0914 | 0.1835 | 0.5131 | 0.0075 | 0.0816 | 0.0048 |
| 0604_stress | 0604_ex50 | hcoef21_resid_ridge_adaptive_interactions_a1_cap0p02_s0p25 | gap_band | gap_003_005 | 55 | 0.0914 | 0.1835 | 0.5131 | 0.0075 | 0.0816 | 0.0049 |
| 0604_stress | 0604_ex50 | hcoef21_resid_ridge_adaptive_interactions_a0p1_cap0p02_s0p25 | gap_band | gap_003_005 | 55 | 0.0914 | 0.1835 | 0.5131 | 0.0075 | 0.0816 | 0.0049 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p02_s0p25 | gap_band | gap_003_005 | 55 | 0.0914 | 0.1835 | 0.5131 | 0.0075 | 0.0816 | 0.0049 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p02_s0p25 | gap_band | gap_003_005 | 55 | 0.0914 | 0.1835 | 0.5131 | 0.0075 | 0.0816 | 0.0049 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p03_s0p25 | gap_band | gap_003_005 | 55 | 0.0937 | 0.1829 | 0.5110 | 0.0050 | 0.0817 | 0.0073 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p03_s0p25 | gap_band | gap_003_005 | 55 | 0.0937 | 0.1829 | 0.5110 | 0.0050 | 0.0817 | 0.0073 |
| 0604_stress | 0604_ex50 | hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p03_s0p25 | gap_band | gap_003_005 | 55 | 0.0937 | 0.1829 | 0.5110 | 0.0050 | 0.0816 | 0.0071 |

## 9. 판단

- 운영 기본 후보는 현재 기준 후보보다 row OOF, artist OOF, fixed test에서 MdAPE/MAPE/p95가 모두 동등 또는 개선되어야 함.
- 가변 기준가 후보는 설명 가능성이 높지만, 큰 오차 p95가 안정 후보보다 커지면 운영 기본 후보로 채택하지 않음.
- Huber residual 후보는 MAPE 또는 p95 목적별 후보로는 남길 수 있지만, bootstrap gate를 통과하지 못하면 기본 후보로 승격하지 않음.
