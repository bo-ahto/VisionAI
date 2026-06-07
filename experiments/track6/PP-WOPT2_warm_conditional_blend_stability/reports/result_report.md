# PP-WOPT2 Warm conditional fallback + PP-V8 blend stability

- 작성일: 2026-06-06 01:46
- 목적: PP-WOPT1의 조건별 결합 후보가 validation 선택에도 안정적인지 확인
- 반복 횟수: row/artist holdout 각 `200`회
- 선택 데이터: validation 일부
- 검증 데이터: 남은 validation holdout과 고정 test

## 1. 고정 test 상위 후보

| 후보 | 방식 | MdAPE | MAPE | p95_APE | 기준 대비 MdAPE | 기준 대비 MAPE | 기준 대비 p95 |
|---|---|---:|---:|---:|---:|---:|---:|
| `fixed_fallback_ppv8_wfallback_0.575` | fixed_weight_blend | 0.1348 | 0.2711 | 0.8362 | 0.0057 | 0.0037 | -0.0031 |
| `fixed_fallback_ppv8_wfallback_0.600` | fixed_weight_blend | 0.1362 | 0.2717 | 0.8329 | 0.0043 | 0.0031 | 0.0002 |
| `fixed_fallback_ppv8_wfallback_0.625` | fixed_weight_blend | 0.1374 | 0.2725 | 0.8378 | 0.0031 | 0.0023 | -0.0047 |
| `fixed_fallback_ppv8_wfallback_0.550` | fixed_weight_blend | 0.1376 | 0.2706 | 0.8414 | 0.0028 | 0.0042 | -0.0083 |
| `dyn_fallback_ppv8_n5_gap0.70_hard0.75_w0.65_0.550_0.40` | conditional_weight_blend | 0.1382 | 0.2695 | 0.8026 | 0.0023 | 0.0053 | 0.0305 |
| `dyn_fallback_ppv8_n5_gap0.70_hard1.00_w0.65_0.550_0.40` | conditional_weight_blend | 0.1382 | 0.2710 | 0.8066 | 0.0023 | 0.0038 | 0.0265 |
| `fixed_fallback_ppv8_wfallback_0.650` | fixed_weight_blend | 0.1382 | 0.2733 | 0.8432 | 0.0023 | 0.0015 | -0.0101 |
| `dyn_fallback_ppv8_n5_gap0.35_hard0.75_w0.65_0.550_0.40` | conditional_weight_blend | 0.1390 | 0.2695 | 0.8026 | 0.0015 | 0.0053 | 0.0305 |
| `dyn_fallback_ppv8_n5_gap0.50_hard0.75_w0.65_0.550_0.40` | conditional_weight_blend | 0.1390 | 0.2696 | 0.8026 | 0.0015 | 0.0052 | 0.0305 |
| `dyn_fallback_ppv8_n5_gap0.35_hard0.50_w0.65_0.550_0.40` | conditional_weight_blend | 0.1390 | 0.2702 | 0.8064 | 0.0015 | 0.0046 | 0.0267 |
| `dyn_fallback_ppv8_n5_gap0.50_hard0.50_w0.65_0.550_0.40` | conditional_weight_blend | 0.1390 | 0.2703 | 0.8064 | 0.0015 | 0.0045 | 0.0267 |
| `dyn_fallback_ppv8_n5_gap0.70_hard0.50_w0.65_0.550_0.40` | conditional_weight_blend | 0.1390 | 0.2703 | 0.8064 | 0.0015 | 0.0045 | 0.0267 |
| `dyn_fallback_ppv8_n5_gap0.35_hard1.00_w0.65_0.550_0.40` | conditional_weight_blend | 0.1390 | 0.2710 | 0.8066 | 0.0015 | 0.0038 | 0.0265 |
| `dyn_fallback_ppv8_n5_gap0.50_hard1.00_w0.65_0.550_0.40` | conditional_weight_blend | 0.1390 | 0.2711 | 0.8066 | 0.0015 | 0.0037 | 0.0265 |
| `fixed_fallback_ppv8_wfallback_0.525` | fixed_weight_blend | 0.1393 | 0.2701 | 0.8534 | 0.0011 | 0.0047 | -0.0203 |
| `fixed_fallback_ppv8_wfallback_0.700` | fixed_weight_blend | 0.1401 | 0.2751 | 0.8351 | 0.0004 | -0.0003 | -0.0020 |
| `fixed_fallback_ppv8_wfallback_0.500` | fixed_weight_blend | 0.1402 | 0.2699 | 0.8472 | 0.0003 | 0.0049 | -0.0141 |
| `fixed_fallback_ppv8_wfallback_0.675` | fixed_weight_blend | 0.1402 | 0.2742 | 0.8369 | 0.0002 | 0.0006 | -0.0038 |
| `blend_svcnum_ppv8_wsvc_0.70` | reference | 0.1405 | 0.2748 | 0.8331 | 0.0000 | 0.0000 | 0.0000 |
| `dyn_fallback_ppv8_n5_gap0.70_hard0.75_w0.70_0.575_0.45` | conditional_weight_blend | 0.1410 | 0.2708 | 0.8112 | -0.0005 | 0.0040 | 0.0218 |
| `dyn_fallback_ppv8_n5_gap0.70_hard1.00_w0.70_0.575_0.45` | conditional_weight_blend | 0.1410 | 0.2722 | 0.8112 | -0.0005 | 0.0026 | 0.0218 |
| `dyn_fallback_ppv8_n15_gap0.35_hard0.50_w0.70_0.575_0.45` | conditional_weight_blend | 0.1423 | 0.2708 | 0.8312 | -0.0018 | 0.0040 | 0.0019 |
| `dyn_fallback_ppv8_n15_gap0.35_hard0.75_w0.70_0.575_0.45` | conditional_weight_blend | 0.1423 | 0.2708 | 0.8312 | -0.0018 | 0.0040 | 0.0019 |
| `dyn_fallback_ppv8_n15_gap0.35_hard1.00_w0.70_0.575_0.45` | conditional_weight_blend | 0.1423 | 0.2708 | 0.8312 | -0.0018 | 0.0040 | 0.0019 |
| `dyn_fallback_ppv8_n15_gap0.50_hard0.50_w0.70_0.575_0.45` | conditional_weight_blend | 0.1423 | 0.2708 | 0.8312 | -0.0018 | 0.0040 | 0.0019 |

## 2. 선택 후 test 요약

| holdout 방식 | 선택 기준 | weight 중앙값 | MdAPE 평균 | MAPE 평균 | p95 평균 | MdAPE 개선확률 | MAPE 개선확률 | p95 개선확률 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| artist_holdout | all_metric_guarded | 0.750 | 0.1426 | 0.2767 | 0.8564 | 0.090 | 0.080 | 0.035 |
| artist_holdout | balanced_current | 0.750 | 0.1427 | 0.2767 | 0.8566 | 0.055 | 0.085 | 0.045 |
| artist_holdout | mape_current_mdape_guard | 0.725 | 0.1420 | 0.2761 | 0.8507 | 0.305 | 0.120 | 0.030 |
| artist_holdout | p95_current_mdape_guard | 0.750 | 0.1423 | 0.2765 | 0.8561 | 0.190 | 0.090 | 0.020 |
| row_holdout | all_metric_guarded | 0.750 | 0.1425 | 0.2766 | 0.8567 | 0.105 | 0.075 | 0.025 |
| row_holdout | balanced_current | 0.750 | 0.1426 | 0.2766 | 0.8563 | 0.080 | 0.085 | 0.045 |
| row_holdout | mape_current_mdape_guard | 0.725 | 0.1420 | 0.2762 | 0.8515 | 0.265 | 0.095 | 0.025 |
| row_holdout | p95_current_mdape_guard | 0.750 | 0.1424 | 0.2766 | 0.8573 | 0.180 | 0.090 | 0.035 |

## 3. 내부 holdout 요약

| holdout 방식 | 선택 기준 | MdAPE 평균 | MAPE 평균 | p95 평균 | MdAPE 개선확률 | MAPE 개선확률 | p95 개선확률 |
|---|---|---:|---:|---:|---:|---:|---:|
| artist_holdout | all_metric_guarded | 0.1257 | 0.2078 | 0.6347 | 0.630 | 0.510 | 0.765 |
| artist_holdout | balanced_current | 0.1254 | 0.2078 | 0.6353 | 0.640 | 0.505 | 0.755 |
| artist_holdout | mape_current_mdape_guard | 0.1261 | 0.2080 | 0.6366 | 0.595 | 0.465 | 0.760 |
| artist_holdout | p95_current_mdape_guard | 0.1254 | 0.2075 | 0.6346 | 0.670 | 0.515 | 0.760 |
| row_holdout | all_metric_guarded | 0.1267 | 0.2121 | 0.6405 | 0.670 | 0.505 | 0.745 |
| row_holdout | balanced_current | 0.1268 | 0.2122 | 0.6419 | 0.675 | 0.500 | 0.730 |
| row_holdout | mape_current_mdape_guard | 0.1270 | 0.2122 | 0.6422 | 0.675 | 0.460 | 0.760 |
| row_holdout | p95_current_mdape_guard | 0.1266 | 0.2120 | 0.6401 | 0.680 | 0.510 | 0.750 |

## 4. 선택 빈도 상위

| holdout 방식 | 선택 기준 | 후보 | 방식 | 선택 횟수 | 선택 비율 |
|---|---|---|---|---:|---:|
| artist_holdout | all_metric_guarded | `fixed_fallback_ppv8_wfallback_0.750` | fixed_weight_blend | 116 | 0.580 |
| artist_holdout | all_metric_guarded | `fixed_fallback_ppv8_wfallback_0.725` | fixed_weight_blend | 62 | 0.310 |
| artist_holdout | all_metric_guarded | `fixed_fallback_ppv8_wfallback_0.675` | fixed_weight_blend | 8 | 0.040 |
| artist_holdout | all_metric_guarded | `fixed_fallback_ppv8_wfallback_0.700` | fixed_weight_blend | 6 | 0.030 |
| artist_holdout | all_metric_guarded | `dyn_fallback_ppv8_n5_gap0.35_hard1.00_w0.65_0.550_0.40` | conditional_weight_blend | 2 | 0.010 |
| artist_holdout | balanced_current | `fixed_fallback_ppv8_wfallback_0.750` | fixed_weight_blend | 121 | 0.605 |
| artist_holdout | balanced_current | `fixed_fallback_ppv8_wfallback_0.725` | fixed_weight_blend | 60 | 0.300 |
| artist_holdout | balanced_current | `fixed_fallback_ppv8_wfallback_0.675` | fixed_weight_blend | 7 | 0.035 |
| artist_holdout | balanced_current | `dyn_fallback_ppv8_n5_gap0.50_hard1.00_w0.75_0.600_0.45` | conditional_weight_blend | 4 | 0.020 |
| artist_holdout | balanced_current | `dyn_fallback_ppv8_n5_gap0.35_hard1.00_w0.75_0.600_0.45` | conditional_weight_blend | 3 | 0.015 |
| artist_holdout | mape_current_mdape_guard | `fixed_fallback_ppv8_wfallback_0.750` | fixed_weight_blend | 81 | 0.405 |
| artist_holdout | mape_current_mdape_guard | `fixed_fallback_ppv8_wfallback_0.725` | fixed_weight_blend | 53 | 0.265 |
| artist_holdout | mape_current_mdape_guard | `fixed_fallback_ppv8_wfallback_0.700` | fixed_weight_blend | 42 | 0.210 |
| artist_holdout | mape_current_mdape_guard | `fixed_fallback_ppv8_wfallback_0.675` | fixed_weight_blend | 16 | 0.080 |
| artist_holdout | mape_current_mdape_guard | `dyn_fallback_ppv8_n5_gap0.35_hard1.00_w0.70_0.575_0.45` | conditional_weight_blend | 3 | 0.015 |
| artist_holdout | p95_current_mdape_guard | `fixed_fallback_ppv8_wfallback_0.750` | fixed_weight_blend | 121 | 0.605 |
| artist_holdout | p95_current_mdape_guard | `fixed_fallback_ppv8_wfallback_0.725` | fixed_weight_blend | 37 | 0.185 |
| artist_holdout | p95_current_mdape_guard | `fixed_fallback_ppv8_wfallback_0.700` | fixed_weight_blend | 24 | 0.120 |
| artist_holdout | p95_current_mdape_guard | `fixed_fallback_ppv8_wfallback_0.675` | fixed_weight_blend | 10 | 0.050 |
| artist_holdout | p95_current_mdape_guard | `dyn_fallback_ppv8_n5_gap0.50_hard1.00_w0.75_0.600_0.45` | conditional_weight_blend | 2 | 0.010 |
| row_holdout | all_metric_guarded | `fixed_fallback_ppv8_wfallback_0.750` | fixed_weight_blend | 118 | 0.590 |
| row_holdout | all_metric_guarded | `fixed_fallback_ppv8_wfallback_0.725` | fixed_weight_blend | 57 | 0.285 |
| row_holdout | all_metric_guarded | `fixed_fallback_ppv8_wfallback_0.700` | fixed_weight_blend | 10 | 0.050 |
| row_holdout | all_metric_guarded | `fixed_fallback_ppv8_wfallback_0.675` | fixed_weight_blend | 5 | 0.025 |
| row_holdout | all_metric_guarded | `fixed_fallback_ppv8_wfallback_0.650` | fixed_weight_blend | 4 | 0.020 |
| row_holdout | balanced_current | `fixed_fallback_ppv8_wfallback_0.750` | fixed_weight_blend | 120 | 0.600 |
| row_holdout | balanced_current | `fixed_fallback_ppv8_wfallback_0.725` | fixed_weight_blend | 57 | 0.285 |
| row_holdout | balanced_current | `fixed_fallback_ppv8_wfallback_0.700` | fixed_weight_blend | 6 | 0.030 |
| row_holdout | balanced_current | `dyn_fallback_ppv8_n5_gap0.35_hard1.00_w0.75_0.600_0.45` | conditional_weight_blend | 3 | 0.015 |
| row_holdout | balanced_current | `dyn_fallback_ppv8_n5_gap0.50_hard1.00_w0.75_0.600_0.45` | conditional_weight_blend | 3 | 0.015 |
| row_holdout | mape_current_mdape_guard | `fixed_fallback_ppv8_wfallback_0.750` | fixed_weight_blend | 83 | 0.415 |
| row_holdout | mape_current_mdape_guard | `fixed_fallback_ppv8_wfallback_0.725` | fixed_weight_blend | 62 | 0.310 |
| row_holdout | mape_current_mdape_guard | `fixed_fallback_ppv8_wfallback_0.700` | fixed_weight_blend | 36 | 0.180 |
| row_holdout | mape_current_mdape_guard | `fixed_fallback_ppv8_wfallback_0.675` | fixed_weight_blend | 11 | 0.055 |
| row_holdout | mape_current_mdape_guard | `dyn_fallback_ppv8_n5_gap0.35_hard1.00_w0.65_0.550_0.40` | conditional_weight_blend | 3 | 0.015 |
| row_holdout | p95_current_mdape_guard | `fixed_fallback_ppv8_wfallback_0.750` | fixed_weight_blend | 136 | 0.680 |
| row_holdout | p95_current_mdape_guard | `fixed_fallback_ppv8_wfallback_0.725` | fixed_weight_blend | 24 | 0.120 |
| row_holdout | p95_current_mdape_guard | `fixed_fallback_ppv8_wfallback_0.700` | fixed_weight_blend | 22 | 0.110 |
| row_holdout | p95_current_mdape_guard | `fixed_fallback_ppv8_wfallback_0.675` | fixed_weight_blend | 8 | 0.040 |
| row_holdout | p95_current_mdape_guard | `dyn_fallback_ppv8_n5_gap0.35_hard1.00_w0.65_0.550_0.40` | conditional_weight_blend | 3 | 0.015 |

## 5. 해석

- 고정 test에서 좋아 보이는 후보가 반복 선택 후 test 평균에서도 유지되는지 확인
- holdout/test 개선확률이 낮으면 test 단일 split 우연 가능성이 큼
- 조건별 결합 후보가 안정적이면 PP-SVC3 이후 후보로 승격
- 안정적이지 않으면 현재 Warm 1순위 유지
