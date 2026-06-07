# PP-WOPT1 Warm current top-candidate refinement

- 작성일: 2026-06-06 01:38
- 목적: 현재 Warm 1순위 후보 이후 개선 여지를 같은 기준으로 검증
- 기준 후보: `blend_svcnum_ppv8_wsvc_0.70`
- 기준 test MdAPE: `0.1405`
- 기준 test MAPE: `0.2748`
- 기준 test p95_APE: `0.8331`

## 1. 실험 축

- Huber + 작가 메타/작가 가격 기준선
- Huber + 신뢰도 보정 유사 작품 기반 가격 피처
- 유사 작품 기반 가격 피처와 PP-V8 오차 안정화 후보의 고정 비율 재탐색
- 표본 수와 후보 간 차이에 따른 조건별 결합 비율

## 2. Test 상위 후보

| 순위 | 후보 | 계열 | 방식 | MdAPE | MAPE | p95_APE | RMSE_log |
|---:|---|---|---|---:|---:|---:|---:|
| 1 | `blend_fallback_numeric_ppv8_wleft_0.575` | fixed_blend | fixed_weight_blend | 0.1348 | 0.2711 | 0.8362 | 0.3995 |
| 2 | `blend_fallback_numeric_ppv8_wleft_0.600` | fixed_blend | fixed_weight_blend | 0.1362 | 0.2717 | 0.8329 | 0.4003 |
| 3 | `blend_fallback_numeric_ppv8_wleft_0.625` | fixed_blend | fixed_weight_blend | 0.1374 | 0.2725 | 0.8378 | 0.4013 |
| 4 | `blend_fallback_numeric_ppv8_wleft_0.550` | fixed_blend | fixed_weight_blend | 0.1376 | 0.2706 | 0.8414 | 0.3987 |
| 5 | `dyn_fallback_ppv8_n5_iqr0.70_d0.75_w0.65_0.550_0.40` | conditional_blend | conditional_weight_blend | 0.1382 | 0.2695 | 0.8026 | 0.3989 |
| 6 | `dyn_fallback_ppv8_n5_iqr0.70_d1.00_w0.65_0.550_0.40` | conditional_blend | conditional_weight_blend | 0.1382 | 0.2710 | 0.8066 | 0.4004 |
| 7 | `blend_fallback_numeric_ppv8_wleft_0.650` | fixed_blend | fixed_weight_blend | 0.1382 | 0.2733 | 0.8432 | 0.4024 |
| 8 | `dyn_fallback_ppv8_n5_iqr0.35_d0.75_w0.65_0.550_0.40` | conditional_blend | conditional_weight_blend | 0.1390 | 0.2695 | 0.8026 | 0.3989 |
| 9 | `dyn_fallback_ppv8_n5_iqr0.50_d0.75_w0.65_0.550_0.40` | conditional_blend | conditional_weight_blend | 0.1390 | 0.2696 | 0.8026 | 0.3989 |
| 10 | `dyn_fallback_ppv8_n5_iqr0.35_d0.50_w0.65_0.550_0.40` | conditional_blend | conditional_weight_blend | 0.1390 | 0.2702 | 0.8064 | 0.3993 |
| 11 | `dyn_fallback_ppv8_n5_iqr0.50_d0.50_w0.65_0.550_0.40` | conditional_blend | conditional_weight_blend | 0.1390 | 0.2703 | 0.8064 | 0.3993 |
| 12 | `dyn_fallback_ppv8_n5_iqr0.70_d0.50_w0.65_0.550_0.40` | conditional_blend | conditional_weight_blend | 0.1390 | 0.2703 | 0.8064 | 0.3993 |
| 13 | `dyn_fallback_ppv8_n5_iqr0.35_d1.00_w0.65_0.550_0.40` | conditional_blend | conditional_weight_blend | 0.1390 | 0.2710 | 0.8066 | 0.4003 |
| 14 | `dyn_fallback_ppv8_n5_iqr0.50_d1.00_w0.65_0.550_0.40` | conditional_blend | conditional_weight_blend | 0.1390 | 0.2711 | 0.8066 | 0.4003 |
| 15 | `blend_fallback_numeric_ppv8_wleft_0.525` | fixed_blend | fixed_weight_blend | 0.1393 | 0.2701 | 0.8534 | 0.3979 |
| 16 | `blend_fallback_numeric_ppv8_wleft_0.700` | fixed_blend | fixed_weight_blend | 0.1401 | 0.2751 | 0.8351 | 0.4047 |
| 17 | `blend_fallback_numeric_ppv8_wleft_0.500` | fixed_blend | fixed_weight_blend | 0.1402 | 0.2699 | 0.8472 | 0.3973 |
| 18 | `blend_fallback_numeric_ppv8_wleft_0.675` | fixed_blend | fixed_weight_blend | 0.1402 | 0.2742 | 0.8369 | 0.4035 |
| 19 | `blend_svcnum_ppv8_wsvc_0.70` | reference | reference | 0.1405 | 0.2748 | 0.8331 | 0.3996 |
| 20 | `dyn_fallback_ppv8_n5_iqr0.70_d0.75_w0.70_0.575_0.45` | conditional_blend | conditional_weight_blend | 0.1410 | 0.2708 | 0.8112 | 0.4010 |
| 21 | `dyn_fallback_ppv8_n5_iqr0.70_d1.00_w0.70_0.575_0.45` | conditional_blend | conditional_weight_blend | 0.1410 | 0.2722 | 0.8112 | 0.4022 |
| 22 | `dyn_fallback_ppv8_n15_iqr0.35_d0.50_w0.70_0.575_0.45` | conditional_blend | conditional_weight_blend | 0.1423 | 0.2708 | 0.8312 | 0.3980 |
| 23 | `dyn_fallback_ppv8_n15_iqr0.35_d0.75_w0.70_0.575_0.45` | conditional_blend | conditional_weight_blend | 0.1423 | 0.2708 | 0.8312 | 0.3980 |
| 24 | `dyn_fallback_ppv8_n15_iqr0.35_d1.00_w0.70_0.575_0.45` | conditional_blend | conditional_weight_blend | 0.1423 | 0.2708 | 0.8312 | 0.3980 |
| 25 | `dyn_fallback_ppv8_n15_iqr0.50_d0.50_w0.70_0.575_0.45` | conditional_blend | conditional_weight_blend | 0.1423 | 0.2708 | 0.8312 | 0.3980 |

## 3. Validation 선택 후보와 Test 확인

| 선택 기준 | 선택 후보 | 계열 | val MdAPE | val MAPE | val p95 | test MdAPE | test MAPE | test p95 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| mdape_primary | `blend_fallback_numeric_ppv8_wleft_0.850` | fixed_blend | 0.1200 | 0.2123 | 0.6419 | 0.1425 | 0.2835 | 0.9259 |
| mape_current_mdape_guard | `blend_fallback_numeric_ppv8_wleft_0.725` | fixed_blend | 0.1264 | 0.2106 | 0.6408 | 0.1425 | 0.2762 | 0.8471 |
| balanced_current | `blend_fallback_numeric_ppv8_wleft_0.850` | fixed_blend | 0.1200 | 0.2123 | 0.6419 | 0.1425 | 0.2835 | 0.9259 |

## 4. Validation MAPE 상위 후보

| 후보 | 계열 | 방식 | MdAPE | MAPE | p95_APE |
|---|---|---|---:|---:|---:|
| `blend_fallback_numeric_ppv8_wleft_0.725` | fixed_blend | fixed_weight_blend | 0.1264 | 0.2106 | 0.6408 |
| `blend_fallback_numeric_ppv8_wleft_0.750` | fixed_blend | fixed_weight_blend | 0.1273 | 0.2107 | 0.6234 |
| `blend_fallback_numeric_ppv8_wleft_0.700` | fixed_blend | fixed_weight_blend | 0.1285 | 0.2107 | 0.6541 |
| `blend_fallback_numeric_ppv8_wleft_0.775` | fixed_blend | fixed_weight_blend | 0.1277 | 0.2108 | 0.6163 |
| `blend_fallback_numeric_ppv8_wleft_0.675` | fixed_blend | fixed_weight_blend | 0.1328 | 0.2109 | 0.6500 |
| `blend_svcnum_ppv8_wsvc_0.70` | reference | reference | 0.1305 | 0.2110 | 0.6580 |
| `blend_fallback_numeric_ppv8_wleft_0.800` | fixed_blend | fixed_weight_blend | 0.1249 | 0.2112 | 0.6252 |
| `blend_fallback_numeric_ppv8_wleft_0.650` | fixed_blend | fixed_weight_blend | 0.1367 | 0.2113 | 0.6445 |
| `blend_fallback_numeric_ppv8_wleft_0.825` | fixed_blend | fixed_weight_blend | 0.1238 | 0.2117 | 0.6363 |
| `blend_fallback_numeric_ppv8_wleft_0.625` | fixed_blend | fixed_weight_blend | 0.1365 | 0.2118 | 0.6460 |
| `blend_fallback_numeric_ppv8_wleft_0.850` | fixed_blend | fixed_weight_blend | 0.1200 | 0.2123 | 0.6419 |
| `blend_fallback_numeric_ppv8_wleft_0.600` | fixed_blend | fixed_weight_blend | 0.1362 | 0.2125 | 0.6613 |
| `blend_fallback_numeric_ppv8_wleft_0.875` | fixed_blend | fixed_weight_blend | 0.1205 | 0.2129 | 0.6342 |
| `blend_fallback_numeric_ppv8_wleft_0.575` | fixed_blend | fixed_weight_blend | 0.1340 | 0.2132 | 0.6688 |
| `blend_fallback_numeric_ppv8_wleft_0.900` | fixed_blend | fixed_weight_blend | 0.1200 | 0.2136 | 0.6424 |
| `blend_fallback_numeric_ppv8_wleft_0.550` | fixed_blend | fixed_weight_blend | 0.1372 | 0.2140 | 0.6760 |
| `dyn_fallback_ppv8_n5_iqr0.35_d1.00_w0.70_0.575_0.45` | conditional_blend | conditional_weight_blend | 0.1287 | 0.2143 | 0.6780 |
| `dyn_fallback_ppv8_n5_iqr0.35_d1.00_w0.75_0.600_0.45` | conditional_blend | conditional_weight_blend | 0.1273 | 0.2143 | 0.6780 |
| `dyn_fallback_ppv8_n5_iqr0.50_d1.00_w0.70_0.575_0.45` | conditional_blend | conditional_weight_blend | 0.1285 | 0.2145 | 0.6628 |
| `dyn_fallback_ppv8_n5_iqr0.70_d1.00_w0.70_0.575_0.45` | conditional_blend | conditional_weight_blend | 0.1287 | 0.2146 | 0.6628 |

## 5. 해석

- test 상위 후보만으로 바로 채택하지 않음
- validation에서 선택된 후보가 test에서도 기준 후보를 함께 개선하는지 우선 확인
- Huber 작가 메타 후보가 개선되면 모델 내부 피처 고도화 방향으로 승격
- 고정 또는 조건별 결합 후보가 개선되면 PP-SVC6처럼 반복 holdout 검증으로 승격
- MdAPE, MAPE, p95가 서로 엇갈리면 단일 점 예측 후보가 아니라 큰 오차 방어 보조 후보로 분리

## 6. 산출물

- `outputs/all_candidate_metrics.csv`
- `outputs/huber_candidate_predictions.csv`
- `outputs/blend_candidate_predictions.csv`
- `outputs/selected_validation_candidates.csv`
- `outputs/huber_coefficients_top.csv`
- `reports/result_report.md`
- `reports/result_report.html`
