# PP-HCOEF22 Warm Huber 목적별 라우팅/신뢰도 정책 검증

- 작성일: 2026-06-08 04:14
- 목적: HCOEF20~21의 MAPE/p95 후보를 validation OOF 기준 구간 라우팅으로 제한 적용할 수 있는지 검증.
- 현재 기준 후보: `hcoef_stable` = `hcoef2_size_reliability_cap005_s050`.
- 최소 비교 기준: `current_70_30` = SVC 70% + PP-V8 30%.
- fixed test와 0604 residual은 정책 선택에 사용하지 않음.

## 1. 실험 설계

- 후보 풀은 HCOEF20~21의 validation/OOF 개선 신호가 있는 후보만 사용.
- 구간 선택은 validation row OOF와 artist OOF가 동시에 개선되는 경우에만 허용.
- 라우팅 축:
  - `qwidth_band`
  - `svc_coverage_tier`
  - `svc_group_n_band`
  - `gap_band`
  - `pred_spread_band`
  - `qwidth_band + svc_coverage_tier`
  - `gap_band + qwidth_band`
- 후보 유형:
  - `mape_guard`: MAPE 개선을 우선하되 MdAPE/p95 악화가 작은 구간에만 적용.
  - `p95_guard`: 큰 오차 방어를 우선하되 MdAPE/MAPE 악화가 작은 구간에만 적용.
  - `any2_guard`: MdAPE/MAPE/p95 중 2개 이상 개선되는 구간에만 적용.

## 2. 후보 풀 요약

| candidate | source_experiment | decision | row_oof_MdAPE | row_oof_MAPE | row_oof_p95_APE | artist_oof_MdAPE | artist_oof_MAPE | artist_oof_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p05_s0p5 | PP-HCOEF21 | OOF 개선 후보 | 0.1284 | 0.2065 | 0.6407 | 0.1237 | 0.2066 | 0.6461 |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p05_s0p5 | PP-HCOEF21 | OOF 개선 후보 | 0.1284 | 0.2065 | 0.6407 | 0.1237 | 0.2066 | 0.6462 |
| hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p02_s0p25 | PP-HCOEF21 | OOF 개선 후보 | 0.1263 | 0.2077 | 0.6409 | 0.1261 | 0.2078 | 0.6409 |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p02_s0p25 | PP-HCOEF21 | OOF 개선 후보 | 0.1263 | 0.2077 | 0.6409 | 0.1261 | 0.2078 | 0.6409 |
| hcoef21_resid_ridge_adaptive_interactions_a1_cap0p02_s0p25 | PP-HCOEF21 | OOF 개선 후보 | 0.1263 | 0.2076 | 0.6409 | 0.1263 | 0.2079 | 0.6409 |
| hcoef21_resid_ridge_adaptive_interactions_a0p1_cap0p02_s0p25 | PP-HCOEF21 | OOF 개선 후보 | 0.1263 | 0.2077 | 0.6409 | 0.1263 | 0.2079 | 0.6409 |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p02_s0p25 | PP-HCOEF21 | OOF 개선 후보 | 0.1263 | 0.2078 | 0.6409 | 0.1260 | 0.2079 | 0.6409 |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p02_s0p25 | PP-HCOEF21 | OOF 개선 후보 | 0.1263 | 0.2078 | 0.6409 | 0.1261 | 0.2079 | 0.6409 |
| hcoef21_resid_ridge_adaptive_reliability_a0p1_cap0p02_s0p25 | PP-HCOEF21 | OOF 개선 후보 | 0.1263 | 0.2079 | 0.6409 | 0.1259 | 0.2079 | 0.6409 |
| hcoef21_resid_ridge_adaptive_reliability_a1_cap0p02_s0p25 | PP-HCOEF21 | OOF 개선 후보 | 0.1263 | 0.2079 | 0.6409 | 0.1259 | 0.2080 | 0.6409 |
| hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p03_s0p5 | PP-HCOEF21 | OOF 개선 후보 | 0.1281 | 0.2069 | 0.6439 | 0.1262 | 0.2072 | 0.6459 |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p03_s0p5 | PP-HCOEF21 | OOF 개선 후보 | 0.1281 | 0.2069 | 0.6439 | 0.1262 | 0.2072 | 0.6459 |
| hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p05_s0p25 | PP-HCOEF21 | OOF 개선 후보 | 0.1279 | 0.2071 | 0.6446 | 0.1261 | 0.2073 | 0.6443 |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p05_s0p25 | PP-HCOEF21 | OOF 개선 후보 | 0.1279 | 0.2071 | 0.6446 | 0.1261 | 0.2073 | 0.6443 |
| current_70_30 | PP-HCOEF21 | 최소 비교 기준 | 0.1305 | 0.2110 | 0.6580 | 0.1305 | 0.2110 | 0.6580 |
| hcoef_stable | PP-HCOEF21 | 현재 기준 후보 | 0.1260 | 0.2082 | 0.6479 | 0.1260 | 0.2082 | 0.6479 |
| ppv8_service_proxy | PP-HCOEF21 | component 대조군 | 0.1544 | 0.2544 | 0.8084 | 0.1544 | 0.2544 | 0.8084 |
| svc_numeric_seed_mean | PP-HCOEF21 | component 대조군 | 0.1272 | 0.2176 | 0.6504 | 0.1272 | 0.2176 | 0.6504 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p03_s0p5 | PP-HCOEF20 | OOF 개선 후보 | 0.1269 | 0.2077 | 0.6410 | 0.1256 | 0.2073 | 0.6432 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p03_s0p5 | PP-HCOEF20 | OOF 개선 후보 | 0.1269 | 0.2077 | 0.6410 | 0.1256 | 0.2073 | 0.6432 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p25 | PP-HCOEF20 | OOF 개선 후보 | 0.1263 | 0.2079 | 0.6408 | 0.1259 | 0.2078 | 0.6404 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p25 | PP-HCOEF20 | OOF 개선 후보 | 0.1263 | 0.2079 | 0.6408 | 0.1259 | 0.2078 | 0.6404 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p03_s0p25 | PP-HCOEF20 | OOF 개선 후보 | 0.1286 | 0.2078 | 0.6445 | 0.1264 | 0.2076 | 0.6385 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p03_s0p25 | PP-HCOEF20 | OOF 개선 후보 | 0.1286 | 0.2078 | 0.6445 | 0.1264 | 0.2076 | 0.6385 |

## 3. 라우팅 후보 선택표

| policy_family | segment_col | segment_value | chosen_candidate | n_row | n_artist | mean_delta_MdAPE | mean_delta_MAPE | mean_delta_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mape_guard | gap_band | gap_003_005 | hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p05_s0p5 | 55 | 55 | 0.0014 | -0.0033 | -0.0195 |
| mape_guard | gap_band | gap_005_010 | hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p5 | 117 | 117 | 0.0012 | -0.0015 | -0.0089 |
| mape_guard | gap_band | gap_010_020 | hcoef21_resid_ridge_adaptive_interactions_a0p1_cap0p02_s0p25 | 134 | 134 | -0.0039 | -0.0008 | -0.0020 |
| mape_guard | gap_band | gap_020_plus | hcoef21_resid_ridge_adaptive_reliability_a0p1_cap0p02_s0p25 | 76 | 76 | -0.0014 | -0.0011 | 0.0004 |
| mape_guard | gap_band+qwidth_band | gap_000_003 \| qwidth_low | hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p5 | 70 | 70 | 0.0016 | -0.0005 | 0.0058 |
| mape_guard | gap_band+qwidth_band | gap_000_003 \| qwidth_mid | ppv8_service_proxy | 44 | 44 | -0.0101 | -0.0020 | 0.0056 |
| mape_guard | gap_band+qwidth_band | gap_005_010 \| qwidth_extreme | hcoef21_resid_ridge_adaptive_reliability_a0p1_cap0p02_s0p25 | 21 | 21 | -0.0046 | -0.0018 | -0.0059 |
| mape_guard | gap_band+qwidth_band | gap_005_010 \| qwidth_low | hcoef20_resid_huber_component_gaps_a0p01_cap0p03_s0p5 | 40 | 40 | -0.0050 | -0.0010 | -0.0048 |
| mape_guard | gap_band+qwidth_band | gap_005_010 \| qwidth_mid | hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p25 | 41 | 41 | 0.0032 | -0.0012 | -0.0019 |
| mape_guard | gap_band+qwidth_band | gap_010_020 \| qwidth_high | hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p03_s0p5 | 24 | 24 | -0.0125 | -0.0030 | 0.0059 |
| mape_guard | gap_band+qwidth_band | gap_010_020 \| qwidth_low | hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p02_s0p25 | 29 | 29 | 0.0024 | -0.0011 | -0.0024 |
| mape_guard | gap_band+qwidth_band | gap_010_020 \| qwidth_mid | hcoef20_resid_ridge_component_gaps_qwidth_a1_cap0p02_s0p25 | 44 | 44 | -0.0002 | -0.0007 | 0.0080 |
| mape_guard | gap_band+qwidth_band | gap_020_plus \| qwidth_extreme | hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p03_s0p5 | 24 | 24 | -0.0101 | -0.0035 | -0.0022 |
| mape_guard | gap_band+qwidth_band | gap_020_plus \| qwidth_mid | hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p05_s0p5 | 28 | 28 | 0.0036 | -0.0026 | -0.0309 |
| mape_guard | pred_spread_band | spread_extreme | hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p05_s0p5 | 104 | 104 | -0.0001 | -0.0039 | 0.0043 |
| mape_guard | pred_spread_band | spread_low_mid | hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p05_s0p5 | 342 | 342 | 0.0004 | -0.0017 | -0.0013 |
| mape_guard | qwidth_band | qwidth_extreme | hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p05_s0p5 | 104 | 104 | -0.0078 | -0.0076 | -0.0465 |
| mape_guard | qwidth_band | qwidth_high | hcoef20_resid_huber_component_gaps_a0p001_cap0p05_s0p5 | 73 | 73 | -0.0024 | -0.0008 | -0.0117 |
| mape_guard | qwidth_band | qwidth_low | hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p05_s0p25 | 171 | 171 | -0.0034 | -0.0006 | 0.0066 |
| mape_guard | qwidth_band+svc_coverage_tier | qwidth_extreme \| low_n | hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p05_s0p5 | 91 | 91 | -0.0088 | -0.0063 | -0.0481 |
| mape_guard | qwidth_band+svc_coverage_tier | qwidth_high \| low_n | hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p25 | 63 | 63 | -0.0051 | -0.0006 | 0.0072 |
| mape_guard | qwidth_band+svc_coverage_tier | qwidth_low \| medium_n | ppv8_service_proxy | 41 | 41 | -0.0069 | -0.0018 | -0.1227 |
| mape_guard | qwidth_band+svc_coverage_tier | qwidth_mid \| medium_n | ppv8_service_proxy | 29 | 29 | -0.0533 | -0.0204 | -0.0020 |
| mape_guard | svc_coverage_tier | low_n | hcoef20_resid_huber_component_gaps_a0p01_cap0p05_s0p5 | 421 | 421 | -0.0027 | -0.0005 | -0.0018 |
| mape_guard | svc_coverage_tier | medium_n | hcoef20_resid_ridge_component_gaps_qwidth_a1_cap0p02_s0p25 | 93 | 93 | -0.0015 | -0.0008 | -0.0013 |
| mape_guard | svc_group_n_band | n_10_19 | hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p05_s0p5 | 160 | 160 | 0.0040 | -0.0035 | -0.0479 |
| mape_guard | svc_group_n_band | n_20_49 | hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p05_s0p5 | 54 | 54 | 0.0008 | -0.0041 | -0.0018 |
| p95_guard | gap_band | gap_003_005 | hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p05_s0p5 | 55 | 55 | 0.0014 | -0.0033 | -0.0195 |
| p95_guard | gap_band | gap_005_010 | hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p5 | 117 | 117 | 0.0012 | -0.0015 | -0.0089 |
| p95_guard | gap_band | gap_010_020 | current_70_30 | 134 | 134 | 0.0042 | 0.0030 | -0.0108 |
| p95_guard | gap_band+qwidth_band | gap_000_003 \| qwidth_low | svc_numeric_seed_mean | 70 | 70 | 0.0022 | 0.0014 | -0.0639 |
| p95_guard | gap_band+qwidth_band | gap_005_010 \| qwidth_extreme | hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p05_s0p25 | 21 | 21 | 0.0051 | -0.0018 | -0.0148 |
| p95_guard | gap_band+qwidth_band | gap_005_010 \| qwidth_low | hcoef20_resid_huber_component_gaps_a0p001_cap0p05_s0p5 | 40 | 40 | -0.0068 | -0.0007 | -0.0048 |
| p95_guard | gap_band+qwidth_band | gap_010_020 \| qwidth_extreme | hcoef20_resid_huber_component_gaps_a0p001_cap0p05_s0p5 | 37 | 37 | 0.0057 | -0.0038 | -0.0164 |
| p95_guard | gap_band+qwidth_band | gap_010_020 \| qwidth_low | hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p03_s0p5 | 29 | 29 | 0.0045 | -0.0007 | -0.0123 |
| p95_guard | gap_band+qwidth_band | gap_010_020 \| qwidth_mid | current_70_30 | 44 | 44 | 0.0044 | 0.0002 | -0.0256 |
| p95_guard | gap_band+qwidth_band | gap_020_plus \| qwidth_mid | hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p05_s0p5 | 28 | 28 | 0.0036 | -0.0026 | -0.0309 |
| p95_guard | pred_spread_band | spread_high | current_70_30 | 73 | 73 | -0.0041 | 0.0005 | -0.0204 |
| p95_guard | pred_spread_band | spread_low_mid | current_70_30 | 342 | 342 | -0.0102 | 0.0028 | -0.0133 |
| p95_guard | qwidth_band | qwidth_extreme | hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p05_s0p5 | 104 | 104 | -0.0078 | -0.0076 | -0.0465 |

## 4. 후보 판단 요약

| candidate | decision | row_oof_MdAPE | row_oof_MAPE | row_oof_p95_APE | artist_oof_MdAPE | artist_oof_MAPE | artist_oof_p95_APE | test_MdAPE | test_MAPE | test_p95_APE | stress0604_MdAPE | stress0604_MAPE | stress0604_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef_stable | 현재 기준 후보 | 0.1260 | 0.2082 | 0.6479 | 0.1260 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9835 |
| hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25 | OOF 개선 후보 | 0.1263 | 0.2081 | 0.6409 | 0.1263 | 0.2080 | 0.6408 | 0.1388 | 0.2727 | 0.8089 | 0.2765 | 0.3736 | 0.9835 |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p25 | OOF 개선 후보 | 0.1263 | 0.2081 | 0.6409 | 0.1263 | 0.2080 | 0.6408 | 0.1388 | 0.2727 | 0.8089 | 0.2765 | 0.3736 | 0.9835 |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p02_s0p25 | OOF 개선 후보 | 0.1263 | 0.2077 | 0.6409 | 0.1261 | 0.2078 | 0.6409 | 0.1388 | 0.2727 | 0.8099 | 0.2696 | 0.3731 | 0.9834 |
| hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p02_s0p25 | OOF 개선 후보 | 0.1263 | 0.2077 | 0.6409 | 0.1261 | 0.2078 | 0.6409 | 0.1388 | 0.2727 | 0.8099 | 0.2696 | 0.3731 | 0.9834 |
| hcoef21_resid_ridge_adaptive_interactions_a1_cap0p02_s0p25 | OOF 개선 후보 | 0.1263 | 0.2076 | 0.6409 | 0.1263 | 0.2079 | 0.6409 | 0.1388 | 0.2728 | 0.8097 | 0.2698 | 0.3730 | 0.9834 |
| hcoef21_resid_ridge_adaptive_interactions_a0p1_cap0p02_s0p25 | OOF 개선 후보 | 0.1263 | 0.2077 | 0.6409 | 0.1263 | 0.2079 | 0.6409 | 0.1388 | 0.2728 | 0.8097 | 0.2698 | 0.3730 | 0.9834 |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p02_s0p25 | OOF 개선 후보 | 0.1263 | 0.2078 | 0.6409 | 0.1260 | 0.2079 | 0.6409 | 0.1389 | 0.2727 | 0.8100 | 0.2725 | 0.3733 | 0.9834 |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p02_s0p25 | OOF 개선 후보 | 0.1263 | 0.2078 | 0.6409 | 0.1261 | 0.2079 | 0.6409 | 0.1389 | 0.2727 | 0.8100 | 0.2725 | 0.3733 | 0.9834 |
| hcoef21_resid_ridge_adaptive_reliability_a0p1_cap0p02_s0p25 | OOF 개선 후보 | 0.1263 | 0.2079 | 0.6409 | 0.1259 | 0.2079 | 0.6409 | 0.1389 | 0.2729 | 0.8100 | 0.2748 | 0.3733 | 0.9834 |
| hcoef21_resid_ridge_adaptive_reliability_a1_cap0p02_s0p25 | OOF 개선 후보 | 0.1263 | 0.2079 | 0.6409 | 0.1259 | 0.2080 | 0.6409 | 0.1389 | 0.2729 | 0.8100 | 0.2758 | 0.3734 | 0.9834 |
| hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p25 | OOF 개선 후보 | 0.1263 | 0.2080 | 0.6409 | 0.1263 | 0.2079 | 0.6418 | 0.1394 | 0.2729 | 0.8095 | 0.2765 | 0.3736 | 0.9835 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p25 | OOF 개선 후보 | 0.1263 | 0.2079 | 0.6408 | 0.1259 | 0.2078 | 0.6404 | 0.1394 | 0.2729 | 0.8091 | 0.2694 | 0.3740 | 0.9835 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p25 | OOF 개선 후보 | 0.1263 | 0.2079 | 0.6408 | 0.1259 | 0.2078 | 0.6404 | 0.1394 | 0.2729 | 0.8091 | 0.2694 | 0.3740 | 0.9835 |
| hcoef20_resid_ridge_component_gaps_qwidth_a1_cap0p02_s0p25 | OOF 개선 후보 | 0.1263 | 0.2080 | 0.6409 | 0.1263 | 0.2079 | 0.6416 | 0.1394 | 0.2729 | 0.8095 | 0.2765 | 0.3736 | 0.9835 |
| hcoef22_route_any2_guard | OOF 개선 후보 | 0.1263 | 0.2070 | 0.6398 | 0.1258 | 0.2067 | 0.6398 | 0.1408 | 0.2732 | 0.8100 | 0.2748 | 0.3719 | 0.9790 |
| hcoef22_route_p95_guard | OOF 개선 후보 | 0.1290 | 0.2076 | 0.6394 | 0.1277 | 0.2074 | 0.6397 | 0.1412 | 0.2734 | 0.8161 | 0.2724 | 0.3712 | 0.9836 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p03_s0p25 | OOF 개선 후보 | 0.1286 | 0.2078 | 0.6445 | 0.1264 | 0.2076 | 0.6385 | 0.1422 | 0.2727 | 0.8096 | 0.2696 | 0.3737 | 0.9808 |

## 5. 가격 범위/신뢰도 정책

| scope | split | hcoef22_confidence_tier | n | range_coverage_qwidth | median_quantile_width | stable_MdAPE | stable_MAPE | stable_p95_APE | over_50pct_error_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_stress | 0604_ex50 | high | 26 | 0.6538 | 1.0159 | 0.2234 | 0.3580 | 1.0017 | 0.3462 |
| 0604_stress | 0604_ex50 | low | 235 | 0.7532 | 2.0603 | 0.3969 | 0.4350 | 0.9963 | 0.3745 |
| 0604_stress | 0604_ex50 | medium | 148 | 0.8311 | 1.3454 | 0.2374 | 0.3431 | 1.0134 | 0.2365 |
| 0604_stress | 0604_ex50 | watch | 420 | 0.8810 | 1.5555 | 0.2373 | 0.3524 | 0.9554 | 0.2571 |
| fixed_confirmation | test | high | 44 | 0.9091 | 0.9172 | 0.1148 | 0.1772 | 0.4927 | 0.0682 |
| fixed_confirmation | test | low | 107 | 0.9159 | 1.9998 | 0.1963 | 0.4076 | 1.7126 | 0.2243 |
| fixed_confirmation | test | medium | 127 | 0.9764 | 1.2633 | 0.1118 | 0.1978 | 0.5178 | 0.0551 |
| fixed_confirmation | test | watch | 329 | 0.9271 | 1.4637 | 0.1448 | 0.2710 | 0.8055 | 0.1155 |
| validation_oof_artist | validation | high | 34 | 1.0000 | 0.9788 | 0.0692 | 0.1104 | 0.3019 | 0.0000 |
| validation_oof_artist | validation | low | 78 | 0.9615 | 2.0603 | 0.1824 | 0.3312 | 1.0754 | 0.1410 |
| validation_oof_artist | validation | medium | 119 | 0.9580 | 1.2373 | 0.1194 | 0.1991 | 0.6188 | 0.0924 |
| validation_oof_artist | validation | watch | 288 | 0.9514 | 1.3920 | 0.1149 | 0.1902 | 0.6021 | 0.0833 |
| validation_oof_row | validation | high | 34 | 1.0000 | 0.9788 | 0.0692 | 0.1104 | 0.3019 | 0.0000 |
| validation_oof_row | validation | low | 78 | 0.9615 | 2.0603 | 0.1824 | 0.3312 | 1.0754 | 0.1410 |
| validation_oof_row | validation | medium | 119 | 0.9580 | 1.2373 | 0.1194 | 0.1991 | 0.6188 | 0.0924 |
| validation_oof_row | validation | watch | 288 | 0.9514 | 1.3920 | 0.1149 | 0.1902 | 0.6021 | 0.0833 |

## 6. Bootstrap / 반복 검증 요약

| candidate | source_scope | validation_scheme | all3_improve_prob | any2_improve_prob | mean_delta_MdAPE_vs_stable | mean_delta_MAPE_vs_stable | mean_delta_p95_APE_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef22_route_mape_guard | validation_oof_artist | row_bootstrap | 0.3733 | 0.8833 | -0.0027 | -0.0015 | 0.0003 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p03_s0p25 | validation_oof_artist | row_bootstrap | 0.4300 | 0.8667 | -0.0009 | -0.0006 | -0.0008 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p03_s0p25 | validation_oof_artist | row_bootstrap | 0.4300 | 0.8667 | -0.0009 | -0.0006 | -0.0008 |
| hcoef22_route_mape_guard | validation_oof_row | artist_bootstrap | 0.3733 | 0.8667 | -0.0022 | -0.0015 | -0.0034 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p03_s0p5 | validation_oof_artist | row_bootstrap | 0.4267 | 0.8500 | -0.0019 | -0.0010 | -0.0009 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p03_s0p5 | validation_oof_artist | row_bootstrap | 0.4267 | 0.8500 | -0.0019 | -0.0010 | -0.0009 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p25 | validation_oof_artist | row_bootstrap | 0.4133 | 0.8500 | -0.0008 | -0.0004 | -0.0005 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p25 | validation_oof_artist | row_bootstrap | 0.4133 | 0.8500 | -0.0008 | -0.0004 | -0.0005 |
| hcoef22_route_mape_guard | validation_oof_artist | artist_bootstrap | 0.3300 | 0.8467 | -0.0028 | -0.0014 | 0.0018 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p25 | validation_oof_row | artist_bootstrap | 0.3900 | 0.8400 | -0.0008 | -0.0003 | -0.0010 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p25 | validation_oof_row | artist_bootstrap | 0.3900 | 0.8400 | -0.0008 | -0.0003 | -0.0010 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p25 | validation_oof_artist | artist_bootstrap | 0.3133 | 0.8367 | -0.0007 | -0.0004 | 0.0003 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p25 | validation_oof_artist | artist_bootstrap | 0.3133 | 0.8367 | -0.0007 | -0.0004 | 0.0003 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p5 | validation_oof_artist | row_bootstrap | 0.3733 | 0.8333 | -0.0012 | -0.0008 | -0.0006 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p5 | validation_oof_artist | row_bootstrap | 0.3733 | 0.8333 | -0.0012 | -0.0008 | -0.0006 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p03_s0p25 | validation_oof_artist | artist_bootstrap | 0.3533 | 0.8333 | -0.0009 | -0.0005 | 0.0002 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p03_s0p25 | validation_oof_artist | artist_bootstrap | 0.3533 | 0.8333 | -0.0009 | -0.0005 | 0.0002 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p03_s0p25 | validation_oof_row | row_bootstrap | 0.4133 | 0.8267 | -0.0004 | -0.0004 | -0.0021 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p03_s0p25 | validation_oof_row | row_bootstrap | 0.4133 | 0.8267 | -0.0004 | -0.0004 | -0.0021 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p05_s0p25 | validation_oof_artist | row_bootstrap | 0.4100 | 0.8267 | -0.0010 | -0.0006 | -0.0019 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p05_s0p25 | validation_oof_artist | row_bootstrap | 0.4100 | 0.8267 | -0.0010 | -0.0006 | -0.0019 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p05_s0p5 | validation_oof_artist | row_bootstrap | 0.3833 | 0.8267 | -0.0026 | -0.0009 | -0.0025 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p05_s0p5 | validation_oof_artist | row_bootstrap | 0.3833 | 0.8267 | -0.0026 | -0.0009 | -0.0025 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p05_s0p25 | validation_oof_artist | artist_bootstrap | 0.3900 | 0.8200 | -0.0012 | -0.0006 | -0.0008 |

## 7. 해석

- HCOEF22는 새 계수를 test에 맞춘 실험이 아니라, validation에서 이미 확인된 후보를 특정 구간에만 제한 적용하는 실험임.
- 라우팅 후보가 `hcoef_stable` 대비 fixed test p95 `0.8064`를 넘기면 운영 기본 후보로 채택하지 않음.
- MAPE가 낮아져도 MdAPE 또는 p95가 악화되면 목적별 후보로만 유지함.
- quantile width와 표본 수는 점 예측 이동보다 가격 범위/신뢰도 표시 정책으로 쓰는 편이 더 안전한지 함께 확인함.

## 8. 판단

- 운영 기본 후보: `hcoef_stable` 유지 여부를 후보 선택표 기준으로 판단.
- MAPE 특화 후보: MAPE 개선이 있으나 p95 guard를 통과하지 못하면 별도 후보로만 유지.
- 신뢰도/범위 정책: point prediction과 분리해서 서비스 표시 정책으로 검토.

## 9. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/segment_policy_selection.csv`
- `outputs/policy_map.csv`
- `outputs/feature_coefficients.csv`
- `outputs/residual_analysis.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `outputs/range_confidence_policy.csv`
- `reports/result_report.md`
- `reports/result_report.html`
