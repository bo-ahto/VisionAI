# PP-HCOEF20 Warm Huber 기준가/계수 재탐색

- 작성일: 2026-06-08 03:19
- 목적: HCOEF 안정 후보를 기본값으로 두고, 운영 component/신뢰도/gap 피처만 사용해 저차원 Huber 계수 보정 후보를 검증.
- 기준 후보: `hcoef_stable` = `hcoef2_size_reliability_cap005_s050`.
- 최소 비교 기준: `current_70_30`.
- 0604는 외부 stress test이며 후보 선택에는 사용하지 않음.

## 1. Validation에서 고정한 위험도 경계

| qwidth_q33 | qwidth_q66 | qwidth_q80 | pred_spread_q66 | pred_spread_q80 |
| --- | --- | --- | --- | --- |
| 1.2116 | 1.5114 | 1.7065 | 0.2611 | 0.3789 |

## 2. 실행 결론

- 점 예측 후보는 validation row OOF, validation artist OOF, bootstrap을 우선해 판단.
- fixed test와 0604가 좋아도 OOF/bootstrap이 약하면 운영 후보로 승격하지 않음.
- quantile width는 점 예측을 직접 움직이기보다 가격 범위와 신뢰도 표시 정책으로 별도 분리.
- Huber 계수는 기준가/component 간 gap, 표본 수 신뢰도, quantile width를 표준화한 뒤 residual_log를 작게 보정하는 방식으로 학습.

## 3. 후보 선택표

| candidate | method | decision | row_oof_MdAPE | row_oof_MAPE | row_oof_p95_APE | artist_oof_MdAPE | artist_oof_MAPE | artist_oof_p95_APE | test_MdAPE | test_MAPE | test_p95_APE | stress0604_MdAPE | stress0604_MAPE | stress0604_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef_stable | source | 현재 기준 후보 | 0.1260 | 0.2082 | 0.6479 | 0.1260 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9835 |
| hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25 | residual_huber | OOF 개선 후보 | 0.1263 | 0.2081 | 0.6409 | 0.1263 | 0.2080 | 0.6408 | 0.1388 | 0.2727 | 0.8089 | 0.2765 | 0.3736 | 0.9835 |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p25 | residual_huber | OOF 개선 후보 | 0.1263 | 0.2081 | 0.6409 | 0.1263 | 0.2080 | 0.6408 | 0.1388 | 0.2727 | 0.8089 | 0.2765 | 0.3736 | 0.9835 |
| hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p25 | residual_ridge | OOF 개선 후보 | 0.1263 | 0.2080 | 0.6409 | 0.1263 | 0.2079 | 0.6418 | 0.1394 | 0.2729 | 0.8095 | 0.2765 | 0.3736 | 0.9835 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p25 | residual_huber | OOF 개선 후보 | 0.1263 | 0.2079 | 0.6408 | 0.1259 | 0.2078 | 0.6404 | 0.1394 | 0.2729 | 0.8091 | 0.2694 | 0.3740 | 0.9835 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p25 | residual_huber | OOF 개선 후보 | 0.1263 | 0.2079 | 0.6408 | 0.1259 | 0.2078 | 0.6404 | 0.1394 | 0.2729 | 0.8091 | 0.2694 | 0.3740 | 0.9835 |
| hcoef20_resid_ridge_component_gaps_qwidth_a1_cap0p02_s0p25 | residual_ridge | OOF 개선 후보 | 0.1263 | 0.2080 | 0.6409 | 0.1263 | 0.2079 | 0.6416 | 0.1394 | 0.2729 | 0.8095 | 0.2765 | 0.3736 | 0.9835 |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p03_s0p25 | residual_huber | OOF 개선 후보 | 0.1291 | 0.2080 | 0.6445 | 0.1288 | 0.2080 | 0.6410 | 0.1416 | 0.2725 | 0.8089 | 0.2755 | 0.3732 | 0.9808 |
| hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p03_s0p25 | residual_huber | OOF 개선 후보 | 0.1291 | 0.2080 | 0.6445 | 0.1288 | 0.2080 | 0.6410 | 0.1416 | 0.2725 | 0.8089 | 0.2755 | 0.3732 | 0.9808 |
| hcoef20_resid_ridge_component_gaps_qwidth_a1_cap0p03_s0p25 | residual_ridge | OOF 개선 후보 | 0.1288 | 0.2079 | 0.6445 | 0.1291 | 0.2079 | 0.6445 | 0.1417 | 0.2729 | 0.8137 | 0.2755 | 0.3732 | 0.9808 |
| hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p03_s0p25 | residual_ridge | OOF 개선 후보 | 0.1288 | 0.2079 | 0.6445 | 0.1291 | 0.2079 | 0.6445 | 0.1417 | 0.2729 | 0.8137 | 0.2755 | 0.3732 | 0.9808 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p03_s0p25 | residual_huber | OOF 개선 후보 | 0.1286 | 0.2078 | 0.6445 | 0.1264 | 0.2076 | 0.6385 | 0.1422 | 0.2727 | 0.8096 | 0.2696 | 0.3737 | 0.9808 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p03_s0p25 | residual_huber | OOF 개선 후보 | 0.1286 | 0.2078 | 0.6445 | 0.1264 | 0.2076 | 0.6385 | 0.1422 | 0.2727 | 0.8096 | 0.2696 | 0.3737 | 0.9808 |
| hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p05_s0p25 | residual_huber | OOF 개선 후보 | 0.1295 | 0.2078 | 0.6448 | 0.1287 | 0.2078 | 0.6386 | 0.1433 | 0.2723 | 0.8089 | 0.2710 | 0.3725 | 0.9793 |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p05_s0p25 | residual_huber | OOF 개선 후보 | 0.1295 | 0.2078 | 0.6448 | 0.1287 | 0.2078 | 0.6386 | 0.1433 | 0.2723 | 0.8089 | 0.2710 | 0.3725 | 0.9793 |
| hcoef20_resid_ridge_component_gaps_qwidth_a1_cap0p03_s0p5 | residual_ridge | OOF 개선 후보 | 0.1273 | 0.2079 | 0.6440 | 0.1281 | 0.2077 | 0.6443 | 0.1433 | 0.2731 | 0.8273 | 0.2707 | 0.3722 | 0.9793 |
| hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p03_s0p5 | residual_ridge | OOF 개선 후보 | 0.1273 | 0.2079 | 0.6439 | 0.1281 | 0.2078 | 0.6443 | 0.1433 | 0.2732 | 0.8273 | 0.2707 | 0.3722 | 0.9793 |
| hcoef20_resid_ridge_component_gaps_qwidth_a1_cap0p02_s0p5 | residual_ridge | OOF 개선 후보 | 0.1288 | 0.2079 | 0.6451 | 0.1292 | 0.2078 | 0.6451 | 0.1433 | 0.2730 | 0.8182 | 0.2735 | 0.3728 | 0.9792 |
| hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p5 | residual_ridge | OOF 개선 후보 | 0.1288 | 0.2079 | 0.6451 | 0.1292 | 0.2078 | 0.6451 | 0.1433 | 0.2730 | 0.8182 | 0.2735 | 0.3728 | 0.9792 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p05_s0p25 | residual_huber | OOF 개선 후보 | 0.1286 | 0.2077 | 0.6454 | 0.1259 | 0.2076 | 0.6385 | 0.1443 | 0.2724 | 0.8100 | 0.2696 | 0.3732 | 0.9792 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p05_s0p25 | residual_huber | OOF 개선 후보 | 0.1286 | 0.2077 | 0.6454 | 0.1259 | 0.2076 | 0.6385 | 0.1443 | 0.2724 | 0.8100 | 0.2696 | 0.3732 | 0.9792 |
| hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p03_s0p5 | residual_huber | OOF 개선 후보 | 0.1285 | 0.2080 | 0.6431 | 0.1285 | 0.2079 | 0.6397 | 0.1444 | 0.2723 | 0.8144 | 0.2707 | 0.3722 | 0.9793 |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p03_s0p5 | residual_huber | OOF 개선 후보 | 0.1285 | 0.2080 | 0.6431 | 0.1285 | 0.2079 | 0.6397 | 0.1444 | 0.2723 | 0.8144 | 0.2707 | 0.3722 | 0.9793 |
| hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p5 | residual_huber | OOF 개선 후보 | 0.1292 | 0.2080 | 0.6447 | 0.1288 | 0.2079 | 0.6376 | 0.1445 | 0.2725 | 0.8144 | 0.2735 | 0.3728 | 0.9792 |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p5 | residual_huber | OOF 개선 후보 | 0.1292 | 0.2080 | 0.6447 | 0.1288 | 0.2079 | 0.6376 | 0.1445 | 0.2725 | 0.8144 | 0.2735 | 0.3728 | 0.9792 |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p05_s0p5 | residual_huber | OOF 개선 후보 | 0.1298 | 0.2079 | 0.6456 | 0.1270 | 0.2078 | 0.6427 | 0.1448 | 0.2722 | 0.8144 | 0.2761 | 0.3711 | 0.9760 |
| hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p05_s0p5 | residual_huber | OOF 개선 후보 | 0.1298 | 0.2079 | 0.6456 | 0.1270 | 0.2078 | 0.6427 | 0.1448 | 0.2722 | 0.8144 | 0.2761 | 0.3711 | 0.9760 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p5 | residual_huber | OOF 개선 후보 | 0.1274 | 0.2078 | 0.6410 | 0.1267 | 0.2075 | 0.6432 | 0.1451 | 0.2729 | 0.8150 | 0.2727 | 0.3736 | 0.9792 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p5 | residual_huber | OOF 개선 후보 | 0.1274 | 0.2078 | 0.6410 | 0.1267 | 0.2075 | 0.6432 | 0.1451 | 0.2729 | 0.8150 | 0.2727 | 0.3736 | 0.9792 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p05_s0p5 | residual_huber | OOF 개선 후보 | 0.1240 | 0.2077 | 0.6450 | 0.1240 | 0.2074 | 0.6432 | 0.1456 | 0.2724 | 0.8164 | 0.2706 | 0.3722 | 0.9794 |

## 4. Fixed Test 상위 후보

| candidate | method | n | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable | improve_count_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef20_resid_ridge_qwidth_reliability_a0p1_cap0p02_s0p5 | residual_ridge | 607 | 0.1367 | 0.2740 | 0.8156 | 0.3987 | -0.0021 | 0.0010 | 0.0092 | 1 |
| hcoef20_resid_ridge_qwidth_reliability_a1_cap0p02_s0p5 | residual_ridge | 607 | 0.1369 | 0.2740 | 0.8155 | 0.3987 | -0.0019 | 0.0010 | 0.0091 | 1 |
| hcoef20_resid_huber_qwidth_reliability_a0p001_cap0p05_s0p25 | residual_huber | 607 | 0.1369 | 0.2725 | 0.8093 | 0.3983 | -0.0019 | -0.0005 | 0.0029 | 2 |
| hcoef20_resid_huber_qwidth_reliability_a0p001_cap0p03_s0p25 | residual_huber | 607 | 0.1369 | 0.2726 | 0.8093 | 0.3985 | -0.0019 | -0.0004 | 0.0029 | 2 |
| hcoef20_resid_huber_qwidth_reliability_a0p01_cap0p05_s0p25 | residual_huber | 607 | 0.1369 | 0.2725 | 0.8093 | 0.3983 | -0.0019 | -0.0005 | 0.0029 | 2 |
| hcoef20_resid_huber_qwidth_reliability_a0p01_cap0p03_s0p25 | residual_huber | 607 | 0.1369 | 0.2726 | 0.8093 | 0.3985 | -0.0019 | -0.0004 | 0.0029 | 2 |
| hcoef20_resid_ridge_qwidth_reliability_a1_cap0p03_s0p25 | residual_ridge | 607 | 0.1372 | 0.2736 | 0.8121 | 0.3987 | -0.0016 | 0.0006 | 0.0058 | 1 |
| hcoef20_resid_huber_qwidth_reliability_a0p001_cap0p02_s0p5 | residual_huber | 607 | 0.1372 | 0.2725 | 0.8152 | 0.3984 | -0.0016 | -0.0005 | 0.0088 | 2 |
| hcoef20_resid_huber_qwidth_reliability_a0p01_cap0p02_s0p5 | residual_huber | 607 | 0.1372 | 0.2725 | 0.8152 | 0.3984 | -0.0016 | -0.0005 | 0.0088 | 2 |
| hcoef20_resid_ridge_qwidth_reliability_a0p1_cap0p03_s0p25 | residual_ridge | 607 | 0.1373 | 0.2736 | 0.8121 | 0.3987 | -0.0015 | 0.0006 | 0.0058 | 1 |
| hcoef20_resid_ridge_qwidth_reliability_a1_cap0p02_s0p25 | residual_ridge | 607 | 0.1377 | 0.2734 | 0.8091 | 0.3987 | -0.0011 | 0.0005 | 0.0028 | 1 |
| hcoef20_resid_huber_qwidth_reliability_a0p01_cap0p02_s0p25 | residual_huber | 607 | 0.1378 | 0.2727 | 0.8091 | 0.3986 | -0.0010 | -0.0003 | 0.0028 | 2 |
| hcoef20_resid_huber_qwidth_reliability_a0p001_cap0p02_s0p25 | residual_huber | 607 | 0.1378 | 0.2727 | 0.8091 | 0.3986 | -0.0010 | -0.0003 | 0.0028 | 2 |
| hcoef20_resid_ridge_qwidth_reliability_a0p1_cap0p02_s0p25 | residual_ridge | 607 | 0.1378 | 0.2734 | 0.8091 | 0.3987 | -0.0010 | 0.0005 | 0.0028 | 1 |
| hcoef20_resid_ridge_qwidth_reliability_a1_cap0p03_s0p5 | residual_ridge | 607 | 0.1381 | 0.2744 | 0.8219 | 0.3987 | -0.0007 | 0.0014 | 0.0155 | 1 |
| hcoef20_resid_ridge_qwidth_reliability_a0p1_cap0p03_s0p5 | residual_ridge | 607 | 0.1381 | 0.2744 | 0.8220 | 0.3987 | -0.0007 | 0.0014 | 0.0156 | 1 |
| hcoef20_resid_huber_qwidth_reliability_a0p01_cap0p03_s0p5 | residual_huber | 607 | 0.1384 | 0.2724 | 0.8156 | 0.3982 | -0.0004 | -0.0006 | 0.0092 | 2 |
| hcoef20_resid_huber_qwidth_reliability_a0p001_cap0p03_s0p5 | residual_huber | 607 | 0.1384 | 0.2724 | 0.8156 | 0.3982 | -0.0004 | -0.0006 | 0.0092 | 2 |
| hcoef_stable | source | 607 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0 |
| hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25 | residual_huber | 607 | 0.1388 | 0.2727 | 0.8089 | 0.3986 | 0.0000 | -0.0003 | 0.0026 | 1 |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p25 | residual_huber | 607 | 0.1388 | 0.2727 | 0.8089 | 0.3986 | 0.0000 | -0.0003 | 0.0026 | 1 |
| hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p25 | residual_ridge | 607 | 0.1394 | 0.2729 | 0.8095 | 0.3986 | 0.0006 | -0.0001 | 0.0031 | 1 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p25 | residual_huber | 607 | 0.1394 | 0.2729 | 0.8091 | 0.3988 | 0.0006 | -0.0001 | 0.0027 | 1 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p25 | residual_huber | 607 | 0.1394 | 0.2729 | 0.8091 | 0.3988 | 0.0006 | -0.0001 | 0.0027 | 1 |
| hcoef20_resid_ridge_component_gaps_qwidth_a1_cap0p02_s0p25 | residual_ridge | 607 | 0.1394 | 0.2729 | 0.8095 | 0.3986 | 0.0006 | -0.0001 | 0.0031 | 1 |

_Only first 25 of 61 rows shown._

## 5. Validation Row OOF 상위 후보

| candidate | method | n | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable | improve_count_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef20_direct_huber_component_stack_a0p01 | direct_huber | 519 | 0.1226 | 0.2091 | 0.6409 | 0.3228 | -0.0034 | 0.0009 | -0.0070 | 2 |
| hcoef20_direct_huber_component_stack_a0p001 | direct_huber | 519 | 0.1226 | 0.2092 | 0.6413 | 0.3227 | -0.0033 | 0.0009 | -0.0066 | 2 |
| hcoef20_direct_ridge_component_stack_a0p1 | direct_ridge | 519 | 0.1232 | 0.2150 | 0.6813 | 0.3254 | -0.0028 | 0.0068 | 0.0333 | 1 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p05_s0p5 | residual_huber | 519 | 0.1240 | 0.2077 | 0.6450 | 0.3235 | -0.0020 | -0.0005 | -0.0030 | 3 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p05_s0p5 | residual_huber | 519 | 0.1240 | 0.2077 | 0.6450 | 0.3235 | -0.0020 | -0.0005 | -0.0030 | 3 |
| hcoef_stable | source | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p25 | residual_huber | 519 | 0.1263 | 0.2079 | 0.6408 | 0.3246 | 0.0003 | -0.0003 | -0.0072 | 2 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p25 | residual_huber | 519 | 0.1263 | 0.2079 | 0.6408 | 0.3246 | 0.0003 | -0.0003 | -0.0072 | 2 |
| hcoef20_resid_ridge_component_gaps_qwidth_a1_cap0p02_s0p25 | residual_ridge | 519 | 0.1263 | 0.2080 | 0.6409 | 0.3245 | 0.0003 | -0.0002 | -0.0070 | 2 |
| hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p25 | residual_ridge | 519 | 0.1263 | 0.2080 | 0.6409 | 0.3245 | 0.0003 | -0.0002 | -0.0070 | 2 |
| hcoef20_resid_huber_qwidth_reliability_a0p001_cap0p02_s0p25 | residual_huber | 519 | 0.1263 | 0.2080 | 0.6470 | 0.3247 | 0.0003 | -0.0002 | -0.0010 | 2 |
| hcoef20_resid_huber_qwidth_reliability_a0p01_cap0p02_s0p25 | residual_huber | 519 | 0.1263 | 0.2080 | 0.6470 | 0.3247 | 0.0003 | -0.0002 | -0.0010 | 2 |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p25 | residual_huber | 519 | 0.1263 | 0.2081 | 0.6409 | 0.3247 | 0.0003 | -0.0001 | -0.0070 | 2 |
| hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25 | residual_huber | 519 | 0.1263 | 0.2081 | 0.6409 | 0.3247 | 0.0003 | -0.0001 | -0.0070 | 2 |
| hcoef20_resid_ridge_qwidth_reliability_a1_cap0p02_s0p25 | residual_ridge | 519 | 0.1263 | 0.2084 | 0.6474 | 0.3247 | 0.0003 | 0.0001 | -0.0005 | 1 |
| hcoef20_resid_ridge_qwidth_reliability_a0p1_cap0p02_s0p25 | residual_ridge | 519 | 0.1263 | 0.2084 | 0.6474 | 0.3247 | 0.0003 | 0.0001 | -0.0005 | 1 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p03_s0p5 | residual_huber | 519 | 0.1269 | 0.2077 | 0.6410 | 0.3237 | 0.0009 | -0.0005 | -0.0070 | 2 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p03_s0p5 | residual_huber | 519 | 0.1269 | 0.2077 | 0.6410 | 0.3237 | 0.0009 | -0.0005 | -0.0070 | 2 |
| svc_numeric_seed_mean | source | 519 | 0.1272 | 0.2176 | 0.6504 | 0.3367 | 0.0012 | 0.0094 | 0.0024 | 0 |
| hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p03_s0p5 | residual_ridge | 519 | 0.1273 | 0.2079 | 0.6439 | 0.3233 | 0.0013 | -0.0003 | -0.0041 | 2 |
| hcoef20_resid_ridge_component_gaps_qwidth_a1_cap0p03_s0p5 | residual_ridge | 519 | 0.1273 | 0.2079 | 0.6440 | 0.3233 | 0.0013 | -0.0003 | -0.0040 | 2 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p5 | residual_huber | 519 | 0.1274 | 0.2078 | 0.6410 | 0.3240 | 0.0014 | -0.0004 | -0.0070 | 2 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p5 | residual_huber | 519 | 0.1274 | 0.2078 | 0.6410 | 0.3240 | 0.0014 | -0.0004 | -0.0070 | 2 |
| hcoef20_resid_huber_qwidth_reliability_a0p01_cap0p05_s0p25 | residual_huber | 519 | 0.1282 | 0.2080 | 0.6467 | 0.3245 | 0.0022 | -0.0002 | -0.0012 | 2 |
| hcoef20_resid_huber_qwidth_reliability_a0p001_cap0p05_s0p25 | residual_huber | 519 | 0.1282 | 0.2080 | 0.6467 | 0.3245 | 0.0022 | -0.0002 | -0.0012 | 2 |

_Only first 25 of 61 rows shown._

## 6. Validation Artist OOF 상위 후보

| candidate | method | n | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable | improve_count_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p05_s0p5 | residual_huber | 519 | 0.1240 | 0.2074 | 0.6432 | 0.3237 | -0.0020 | -0.0008 | -0.0048 | 3 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p05_s0p5 | residual_huber | 519 | 0.1240 | 0.2074 | 0.6432 | 0.3237 | -0.0020 | -0.0008 | -0.0048 | 3 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p03_s0p5 | residual_huber | 519 | 0.1256 | 0.2073 | 0.6432 | 0.3237 | -0.0004 | -0.0009 | -0.0048 | 3 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p03_s0p5 | residual_huber | 519 | 0.1256 | 0.2073 | 0.6432 | 0.3237 | -0.0004 | -0.0009 | -0.0048 | 3 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p25 | residual_huber | 519 | 0.1259 | 0.2078 | 0.6404 | 0.3246 | -0.0001 | -0.0004 | -0.0076 | 3 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p25 | residual_huber | 519 | 0.1259 | 0.2078 | 0.6404 | 0.3246 | -0.0001 | -0.0004 | -0.0076 | 3 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p05_s0p25 | residual_huber | 519 | 0.1259 | 0.2076 | 0.6385 | 0.3243 | -0.0001 | -0.0006 | -0.0094 | 3 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p05_s0p25 | residual_huber | 519 | 0.1259 | 0.2076 | 0.6385 | 0.3243 | -0.0001 | -0.0006 | -0.0094 | 3 |
| hcoef_stable | source | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 0 |
| hcoef20_resid_ridge_component_gaps_qwidth_a1_cap0p02_s0p25 | residual_ridge | 519 | 0.1263 | 0.2079 | 0.6416 | 0.3245 | 0.0003 | -0.0003 | -0.0064 | 2 |
| hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p25 | residual_ridge | 519 | 0.1263 | 0.2079 | 0.6418 | 0.3245 | 0.0003 | -0.0003 | -0.0061 | 2 |
| hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25 | residual_huber | 519 | 0.1263 | 0.2080 | 0.6408 | 0.3247 | 0.0003 | -0.0002 | -0.0072 | 2 |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p25 | residual_huber | 519 | 0.1263 | 0.2080 | 0.6408 | 0.3247 | 0.0003 | -0.0002 | -0.0072 | 2 |
| hcoef20_resid_ridge_qwidth_reliability_a0p1_cap0p02_s0p25 | residual_ridge | 519 | 0.1263 | 0.2082 | 0.6474 | 0.3248 | 0.0003 | 0.0000 | -0.0005 | 1 |
| hcoef20_resid_ridge_qwidth_reliability_a1_cap0p02_s0p25 | residual_ridge | 519 | 0.1263 | 0.2082 | 0.6474 | 0.3248 | 0.0003 | 0.0000 | -0.0005 | 1 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p03_s0p25 | residual_huber | 519 | 0.1264 | 0.2076 | 0.6385 | 0.3244 | 0.0004 | -0.0006 | -0.0094 | 2 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p03_s0p25 | residual_huber | 519 | 0.1264 | 0.2076 | 0.6385 | 0.3244 | 0.0004 | -0.0006 | -0.0094 | 2 |
| hcoef20_direct_ridge_component_stack_a0p1 | direct_ridge | 519 | 0.1265 | 0.2157 | 0.6827 | 0.3289 | 0.0005 | 0.0075 | 0.0347 | 0 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p5 | residual_huber | 519 | 0.1267 | 0.2075 | 0.6432 | 0.3241 | 0.0007 | -0.0007 | -0.0048 | 2 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p5 | residual_huber | 519 | 0.1267 | 0.2075 | 0.6432 | 0.3241 | 0.0007 | -0.0007 | -0.0048 | 2 |
| hcoef20_resid_huber_qwidth_reliability_a0p001_cap0p02_s0p25 | residual_huber | 519 | 0.1270 | 0.2083 | 0.6466 | 0.3249 | 0.0010 | 0.0001 | -0.0014 | 1 |
| hcoef20_resid_huber_qwidth_reliability_a0p01_cap0p02_s0p25 | residual_huber | 519 | 0.1270 | 0.2083 | 0.6466 | 0.3249 | 0.0010 | 0.0001 | -0.0014 | 1 |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p05_s0p5 | residual_huber | 519 | 0.1270 | 0.2078 | 0.6427 | 0.3233 | 0.0011 | -0.0004 | -0.0052 | 2 |
| hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p05_s0p5 | residual_huber | 519 | 0.1270 | 0.2078 | 0.6427 | 0.3233 | 0.0011 | -0.0004 | -0.0052 | 2 |
| hcoef20_resid_huber_qwidth_reliability_a0p01_cap0p05_s0p5 | residual_huber | 519 | 0.1272 | 0.2085 | 0.6409 | 0.3245 | 0.0012 | 0.0003 | -0.0070 | 1 |

_Only first 25 of 61 rows shown._

## 7. 0604 Stress Test 상위 후보

| candidate | method | n | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable | improve_count_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppv8_service_proxy | source | 829 | 0.2298 | 0.3359 | 0.9273 | 0.7124 | -0.0433 | -0.0385 | -0.0561 | 3 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p25 | residual_huber | 829 | 0.2694 | 0.3740 | 0.9835 | 1.3080 | -0.0036 | -0.0004 | 0.0001 | 2 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p25 | residual_huber | 829 | 0.2694 | 0.3740 | 0.9835 | 1.3080 | -0.0036 | -0.0004 | 0.0001 | 2 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p05_s0p25 | residual_huber | 829 | 0.2696 | 0.3732 | 0.9792 | 1.3083 | -0.0035 | -0.0012 | -0.0043 | 3 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p03_s0p25 | residual_huber | 829 | 0.2696 | 0.3737 | 0.9808 | 1.3081 | -0.0035 | -0.0007 | -0.0026 | 3 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p05_s0p25 | residual_huber | 829 | 0.2696 | 0.3732 | 0.9792 | 1.3083 | -0.0035 | -0.0012 | -0.0043 | 3 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p03_s0p25 | residual_huber | 829 | 0.2696 | 0.3737 | 0.9808 | 1.3081 | -0.0035 | -0.0007 | -0.0026 | 3 |
| hcoef20_direct_ridge_component_stack_a0p1 | direct_ridge | 829 | 0.2698 | 0.3732 | 0.9419 | 1.3481 | -0.0032 | -0.0011 | -0.0416 | 3 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p05_s0p5 | residual_huber | 829 | 0.2706 | 0.3722 | 0.9794 | 1.3090 | -0.0024 | -0.0021 | -0.0040 | 3 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p05_s0p5 | residual_huber | 829 | 0.2706 | 0.3722 | 0.9794 | 1.3090 | -0.0024 | -0.0021 | -0.0040 | 3 |
| hcoef20_resid_huber_qwidth_reliability_a0p001_cap0p03_s0p5 | residual_huber | 829 | 0.2707 | 0.3722 | 0.9793 | 1.3116 | -0.0024 | -0.0021 | -0.0041 | 3 |
| hcoef20_resid_huber_qwidth_reliability_a0p01_cap0p03_s0p5 | residual_huber | 829 | 0.2707 | 0.3722 | 0.9793 | 1.3116 | -0.0024 | -0.0021 | -0.0041 | 3 |
| hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p03_s0p5 | residual_huber | 829 | 0.2707 | 0.3722 | 0.9793 | 1.3116 | -0.0024 | -0.0021 | -0.0041 | 3 |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p03_s0p5 | residual_huber | 829 | 0.2707 | 0.3722 | 0.9793 | 1.3116 | -0.0024 | -0.0021 | -0.0041 | 3 |
| hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p03_s0p5 | residual_ridge | 829 | 0.2707 | 0.3722 | 0.9793 | 1.3116 | -0.0024 | -0.0021 | -0.0041 | 3 |
| hcoef20_resid_ridge_component_gaps_qwidth_a1_cap0p03_s0p5 | residual_ridge | 829 | 0.2707 | 0.3722 | 0.9793 | 1.3116 | -0.0024 | -0.0021 | -0.0041 | 3 |
| hcoef20_resid_ridge_qwidth_reliability_a0p1_cap0p03_s0p5 | residual_ridge | 829 | 0.2707 | 0.3722 | 0.9793 | 1.3116 | -0.0024 | -0.0021 | -0.0041 | 3 |
| hcoef20_resid_ridge_qwidth_reliability_a1_cap0p03_s0p5 | residual_ridge | 829 | 0.2707 | 0.3722 | 0.9793 | 1.3116 | -0.0024 | -0.0021 | -0.0041 | 3 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p03_s0p5 | residual_huber | 829 | 0.2707 | 0.3731 | 0.9793 | 1.3085 | -0.0023 | -0.0013 | -0.0041 | 3 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p03_s0p5 | residual_huber | 829 | 0.2707 | 0.3731 | 0.9793 | 1.3085 | -0.0023 | -0.0013 | -0.0041 | 3 |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p05_s0p25 | residual_huber | 829 | 0.2710 | 0.3725 | 0.9793 | 1.3110 | -0.0020 | -0.0019 | -0.0042 | 3 |
| hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p05_s0p25 | residual_huber | 829 | 0.2710 | 0.3725 | 0.9793 | 1.3110 | -0.0020 | -0.0019 | -0.0042 | 3 |
| hcoef20_resid_huber_qwidth_reliability_a0p001_cap0p05_s0p25 | residual_huber | 829 | 0.2710 | 0.3725 | 0.9793 | 1.3110 | -0.0020 | -0.0019 | -0.0042 | 3 |
| hcoef20_resid_huber_qwidth_reliability_a0p01_cap0p05_s0p25 | residual_huber | 829 | 0.2710 | 0.3725 | 0.9793 | 1.3110 | -0.0020 | -0.0019 | -0.0042 | 3 |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p5 | residual_huber | 829 | 0.2727 | 0.3736 | 0.9792 | 1.3082 | -0.0003 | -0.0008 | -0.0042 | 3 |

_Only first 25 of 61 rows shown._

## 8. Bootstrap 요약

| source_scope | validation_scheme | candidate | method | n_bootstrap | mean_delta_MdAPE_vs_stable | mean_delta_MAPE_vs_stable | mean_delta_p95_APE_vs_stable | mean_delta_RMSE_log_vs_stable | MdAPE_improve_prob | MAPE_improve_prob | p95_improve_prob | all3_improve_prob | any2_improve_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation_oof_artist | artist_bootstrap | hcoef20_resid_huber_component_gaps_a0p001_cap0p05_s0p25 | residual_huber | 300 | -0.0012 | -0.0006 | -0.0008 | -0.0008 | 0.6767 | 0.9033 | 0.6067 | 0.3900 | 0.8200 |
| validation_oof_artist | artist_bootstrap | hcoef20_resid_huber_component_gaps_a0p01_cap0p05_s0p25 | residual_huber | 300 | -0.0012 | -0.0006 | -0.0008 | -0.0008 | 0.6767 | 0.9033 | 0.6067 | 0.3900 | 0.8200 |
| validation_oof_artist | artist_bootstrap | hcoef20_resid_huber_component_gaps_a0p001_cap0p03_s0p25 | residual_huber | 300 | -0.0009 | -0.0005 | 0.0002 | -0.0008 | 0.6667 | 0.9500 | 0.5567 | 0.3533 | 0.8333 |
| validation_oof_artist | artist_bootstrap | hcoef20_resid_huber_component_gaps_a0p01_cap0p03_s0p25 | residual_huber | 300 | -0.0009 | -0.0005 | 0.0002 | -0.0008 | 0.6667 | 0.9500 | 0.5567 | 0.3533 | 0.8333 |
| validation_oof_artist | artist_bootstrap | hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p5 | residual_huber | 300 | -0.0015 | -0.0007 | 0.0005 | -0.0011 | 0.6833 | 0.9400 | 0.5300 | 0.3467 | 0.8167 |
| validation_oof_artist | artist_bootstrap | hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p5 | residual_huber | 300 | -0.0015 | -0.0007 | 0.0005 | -0.0011 | 0.6833 | 0.9400 | 0.5300 | 0.3467 | 0.8167 |
| validation_oof_artist | artist_bootstrap | hcoef20_resid_huber_component_gaps_a0p01_cap0p05_s0p5 | residual_huber | 300 | -0.0027 | -0.0008 | -0.0006 | -0.0014 | 0.7433 | 0.8100 | 0.5300 | 0.3267 | 0.7900 |
| validation_oof_artist | artist_bootstrap | hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p25 | residual_huber | 300 | -0.0007 | -0.0004 | 0.0003 | -0.0006 | 0.6267 | 0.9533 | 0.5567 | 0.3133 | 0.8367 |
| validation_oof_artist | artist_bootstrap | hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p25 | residual_huber | 300 | -0.0007 | -0.0004 | 0.0003 | -0.0006 | 0.6267 | 0.9533 | 0.5567 | 0.3133 | 0.8367 |
| validation_oof_artist | artist_bootstrap | hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p5 | residual_huber | 300 | 0.0002 | -0.0003 | 0.0009 | -0.0009 | 0.5033 | 0.7333 | 0.5100 | 0.2167 | 0.6200 |
| validation_oof_artist | artist_bootstrap | hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p5 | residual_huber | 300 | 0.0002 | -0.0003 | 0.0009 | -0.0009 | 0.5033 | 0.7333 | 0.5100 | 0.2167 | 0.6200 |
| validation_oof_artist | artist_bootstrap | hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p25 | residual_ridge | 300 | -0.0002 | -0.0003 | 0.0015 | -0.0007 | 0.5100 | 0.8600 | 0.4667 | 0.2067 | 0.6900 |
| validation_oof_artist | artist_bootstrap | hcoef20_resid_ridge_component_gaps_qwidth_a1_cap0p02_s0p25 | residual_ridge | 300 | -0.0002 | -0.0003 | 0.0015 | -0.0007 | 0.5100 | 0.8600 | 0.4667 | 0.2067 | 0.6900 |
| validation_oof_artist | artist_bootstrap | hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25 | residual_huber | 300 | 0.0000 | -0.0002 | 0.0005 | -0.0005 | 0.5000 | 0.7933 | 0.5333 | 0.2000 | 0.6667 |
| validation_oof_artist | artist_bootstrap | hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p05_s0p25 | residual_huber | 300 | 0.0005 | -0.0003 | 0.0001 | -0.0010 | 0.4767 | 0.7667 | 0.5233 | 0.2000 | 0.6300 |
| validation_oof_artist | artist_bootstrap | hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p25 | residual_huber | 300 | 0.0000 | -0.0002 | 0.0005 | -0.0005 | 0.5000 | 0.7933 | 0.5333 | 0.2000 | 0.6667 |
| validation_oof_artist | artist_bootstrap | hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p05_s0p25 | residual_huber | 300 | 0.0005 | -0.0003 | 0.0001 | -0.0010 | 0.4767 | 0.7667 | 0.5233 | 0.2000 | 0.6300 |
| validation_oof_artist | artist_bootstrap | hcoef20_resid_ridge_component_gaps_qwidth_a1_cap0p03_s0p25 | residual_ridge | 300 | -0.0001 | -0.0003 | 0.0024 | -0.0009 | 0.5433 | 0.8100 | 0.4467 | 0.1933 | 0.6800 |
| validation_oof_artist | artist_bootstrap | hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p03_s0p25 | residual_ridge | 300 | -0.0001 | -0.0003 | 0.0024 | -0.0009 | 0.5467 | 0.8067 | 0.4467 | 0.1900 | 0.6833 |
| validation_oof_artist | artist_bootstrap | hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p5 | residual_ridge | 300 | -0.0003 | -0.0004 | 0.0030 | -0.0012 | 0.5400 | 0.8200 | 0.3967 | 0.1867 | 0.6367 |
| validation_oof_artist | artist_bootstrap | hcoef20_resid_ridge_component_gaps_qwidth_a1_cap0p02_s0p5 | residual_ridge | 300 | -0.0003 | -0.0004 | 0.0029 | -0.0012 | 0.5300 | 0.8367 | 0.3967 | 0.1833 | 0.6433 |
| validation_oof_artist | artist_bootstrap | hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p03_s0p25 | residual_huber | 300 | 0.0003 | -0.0002 | 0.0005 | -0.0007 | 0.4733 | 0.7133 | 0.5200 | 0.1800 | 0.5967 |
| validation_oof_artist | artist_bootstrap | hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p03_s0p25 | residual_huber | 300 | 0.0003 | -0.0002 | 0.0005 | -0.0007 | 0.4733 | 0.7133 | 0.5200 | 0.1800 | 0.5967 |
| validation_oof_artist | artist_bootstrap | hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p03_s0p5 | residual_huber | 300 | 0.0007 | -0.0002 | 0.0015 | -0.0012 | 0.4867 | 0.6533 | 0.4600 | 0.1533 | 0.5600 |
| validation_oof_artist | artist_bootstrap | hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p03_s0p5 | residual_huber | 300 | 0.0007 | -0.0002 | 0.0015 | -0.0012 | 0.4867 | 0.6533 | 0.4600 | 0.1533 | 0.5600 |
| validation_oof_artist | artist_bootstrap | hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p03_s0p5 | residual_ridge | 300 | -0.0005 | -0.0004 | 0.0054 | -0.0017 | 0.5700 | 0.7300 | 0.3300 | 0.1500 | 0.5733 |
| validation_oof_artist | artist_bootstrap | hcoef20_resid_ridge_component_gaps_qwidth_a1_cap0p03_s0p5 | residual_ridge | 300 | -0.0005 | -0.0004 | 0.0053 | -0.0017 | 0.5633 | 0.7400 | 0.3333 | 0.1467 | 0.5767 |
| validation_oof_artist | artist_bootstrap | hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p05_s0p5 | residual_huber | 300 | 0.0006 | -0.0004 | 0.0026 | -0.0017 | 0.4500 | 0.6567 | 0.4433 | 0.1333 | 0.5500 |
| validation_oof_artist | artist_bootstrap | hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p05_s0p5 | residual_huber | 300 | 0.0006 | -0.0004 | 0.0026 | -0.0017 | 0.4500 | 0.6567 | 0.4433 | 0.1333 | 0.5500 |
| validation_oof_artist | artist_bootstrap | current_70_30 | source | 300 | 0.0026 | 0.0028 | 0.0029 | 0.0039 | 0.2933 | 0.0067 | 0.4000 | 0.0033 | 0.1200 |
| validation_oof_artist | artist_bootstrap | hcoef_stable | source | 300 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| validation_oof_artist | row_bootstrap | hcoef20_resid_huber_component_gaps_a0p001_cap0p03_s0p25 | residual_huber | 300 | -0.0009 | -0.0006 | -0.0008 | -0.0008 | 0.6667 | 0.9733 | 0.6500 | 0.4300 | 0.8667 |
| validation_oof_artist | row_bootstrap | hcoef20_resid_huber_component_gaps_a0p01_cap0p03_s0p25 | residual_huber | 300 | -0.0009 | -0.0006 | -0.0008 | -0.0008 | 0.6667 | 0.9733 | 0.6500 | 0.4300 | 0.8667 |
| validation_oof_artist | row_bootstrap | hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p25 | residual_huber | 300 | -0.0008 | -0.0004 | -0.0005 | -0.0006 | 0.6567 | 0.9700 | 0.6300 | 0.4133 | 0.8500 |
| validation_oof_artist | row_bootstrap | hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p25 | residual_huber | 300 | -0.0008 | -0.0004 | -0.0005 | -0.0006 | 0.6567 | 0.9700 | 0.6300 | 0.4133 | 0.8500 |
| validation_oof_artist | row_bootstrap | hcoef20_resid_huber_component_gaps_a0p001_cap0p05_s0p25 | residual_huber | 300 | -0.0010 | -0.0006 | -0.0019 | -0.0009 | 0.6267 | 0.9367 | 0.6667 | 0.4100 | 0.8267 |
| validation_oof_artist | row_bootstrap | hcoef20_resid_huber_component_gaps_a0p01_cap0p05_s0p25 | residual_huber | 300 | -0.0010 | -0.0006 | -0.0019 | -0.0009 | 0.6267 | 0.9367 | 0.6667 | 0.4100 | 0.8267 |
| validation_oof_artist | row_bootstrap | hcoef20_resid_huber_component_gaps_a0p01_cap0p05_s0p5 | residual_huber | 300 | -0.0026 | -0.0009 | -0.0025 | -0.0016 | 0.7433 | 0.8667 | 0.5700 | 0.3833 | 0.8267 |
| validation_oof_artist | row_bootstrap | hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p5 | residual_huber | 300 | -0.0012 | -0.0008 | -0.0006 | -0.0011 | 0.6367 | 0.9567 | 0.6067 | 0.3733 | 0.8333 |
| validation_oof_artist | row_bootstrap | hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p5 | residual_huber | 300 | -0.0012 | -0.0008 | -0.0006 | -0.0011 | 0.6367 | 0.9567 | 0.6067 | 0.3733 | 0.8333 |
| validation_oof_artist | row_bootstrap | hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25 | residual_huber | 300 | 0.0002 | -0.0002 | -0.0004 | -0.0005 | 0.4800 | 0.8267 | 0.5867 | 0.2633 | 0.6800 |
| validation_oof_artist | row_bootstrap | hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p25 | residual_huber | 300 | 0.0002 | -0.0002 | -0.0004 | -0.0005 | 0.4800 | 0.8267 | 0.5867 | 0.2633 | 0.6800 |
| validation_oof_artist | row_bootstrap | hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p03_s0p25 | residual_huber | 300 | 0.0004 | -0.0002 | -0.0004 | -0.0007 | 0.4667 | 0.7767 | 0.5900 | 0.2400 | 0.6567 |
| validation_oof_artist | row_bootstrap | hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p03_s0p25 | residual_huber | 300 | 0.0004 | -0.0002 | -0.0004 | -0.0007 | 0.4667 | 0.7767 | 0.5900 | 0.2400 | 0.6567 |
| validation_oof_artist | row_bootstrap | hcoef20_resid_ridge_component_gaps_qwidth_a1_cap0p02_s0p25 | residual_ridge | 300 | 0.0001 | -0.0003 | 0.0008 | -0.0007 | 0.4967 | 0.8933 | 0.5100 | 0.2367 | 0.7000 |
| validation_oof_artist | row_bootstrap | hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p25 | residual_ridge | 300 | 0.0001 | -0.0003 | 0.0008 | -0.0007 | 0.4967 | 0.8867 | 0.5100 | 0.2333 | 0.7000 |
| validation_oof_artist | row_bootstrap | hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p05_s0p25 | residual_huber | 300 | 0.0007 | -0.0004 | -0.0012 | -0.0011 | 0.4033 | 0.8267 | 0.6033 | 0.2200 | 0.6567 |
| validation_oof_artist | row_bootstrap | hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p05_s0p25 | residual_huber | 300 | 0.0007 | -0.0004 | -0.0012 | -0.0011 | 0.4033 | 0.8267 | 0.6033 | 0.2200 | 0.6567 |
| validation_oof_artist | row_bootstrap | hcoef20_resid_ridge_component_gaps_qwidth_a1_cap0p02_s0p5 | residual_ridge | 300 | 0.0001 | -0.0004 | 0.0022 | -0.0013 | 0.4633 | 0.8567 | 0.4600 | 0.2200 | 0.6133 |
| validation_oof_artist | row_bootstrap | hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p5 | residual_huber | 300 | 0.0004 | -0.0003 | -0.0001 | -0.0010 | 0.4367 | 0.7867 | 0.5867 | 0.2167 | 0.6567 |
| validation_oof_artist | row_bootstrap | hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p05_s0p5 | residual_huber | 300 | 0.0007 | -0.0005 | -0.0005 | -0.0019 | 0.4433 | 0.7167 | 0.5133 | 0.2167 | 0.5767 |
| validation_oof_artist | row_bootstrap | hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p5 | residual_huber | 300 | 0.0004 | -0.0003 | -0.0001 | -0.0010 | 0.4367 | 0.7867 | 0.5867 | 0.2167 | 0.6567 |
| validation_oof_artist | row_bootstrap | hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p05_s0p5 | residual_huber | 300 | 0.0007 | -0.0005 | -0.0005 | -0.0019 | 0.4433 | 0.7167 | 0.5133 | 0.2167 | 0.5767 |
| validation_oof_artist | row_bootstrap | hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p5 | residual_ridge | 300 | 0.0001 | -0.0004 | 0.0022 | -0.0013 | 0.4700 | 0.8467 | 0.4600 | 0.2167 | 0.6200 |
| validation_oof_artist | row_bootstrap | hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p03_s0p5 | residual_huber | 300 | 0.0010 | -0.0003 | 0.0000 | -0.0013 | 0.4533 | 0.7067 | 0.5500 | 0.2133 | 0.5967 |
| validation_oof_artist | row_bootstrap | hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p03_s0p5 | residual_huber | 300 | 0.0010 | -0.0003 | 0.0000 | -0.0013 | 0.4533 | 0.7067 | 0.5500 | 0.2133 | 0.5967 |
| validation_oof_artist | row_bootstrap | hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p03_s0p25 | residual_ridge | 300 | 0.0003 | -0.0003 | 0.0015 | -0.0010 | 0.4733 | 0.8400 | 0.5000 | 0.2000 | 0.6667 |
| validation_oof_artist | row_bootstrap | hcoef20_resid_ridge_component_gaps_qwidth_a1_cap0p03_s0p25 | residual_ridge | 300 | 0.0003 | -0.0003 | 0.0015 | -0.0010 | 0.4733 | 0.8433 | 0.5000 | 0.2000 | 0.6700 |
| validation_oof_artist | row_bootstrap | hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p03_s0p5 | residual_ridge | 300 | 0.0001 | -0.0005 | 0.0040 | -0.0018 | 0.4867 | 0.7833 | 0.3933 | 0.1933 | 0.5567 |
| validation_oof_artist | row_bootstrap | hcoef20_resid_ridge_component_gaps_qwidth_a1_cap0p03_s0p5 | residual_ridge | 300 | 0.0001 | -0.0005 | 0.0040 | -0.0018 | 0.4700 | 0.7900 | 0.3933 | 0.1867 | 0.5500 |

_Only first 60 of 124 rows shown._

## 9. 가격 범위/신뢰도 정책

| split | range_confidence_tier | n | q10_q90_coverage | median_quantile_width | median_price_range_ratio | stable_MdAPE | stable_MAPE | stable_p95_APE | over_50pct_error_rate | policy_rule |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | high | 34 | 0.9118 | 0.9788 | 1.1226 | 0.0692 | 0.1104 | 0.3019 | 0.0000 | high: qwidth<=validation q33 and svc_group_n>=20; medium: qwidth<=validation q66 and svc_group_n>=10; else low |
| validation | low | 366 | 0.8197 | 1.5000 | 1.7834 | 0.1292 | 0.2203 | 0.6496 | 0.0956 | high: qwidth<=validation q33 and svc_group_n>=20; medium: qwidth<=validation q66 and svc_group_n>=10; else low |
| validation | medium | 119 | 0.8487 | 1.2373 | 1.4581 | 0.1194 | 0.1991 | 0.6188 | 0.0924 | high: qwidth<=validation q33 and svc_group_n>=20; medium: qwidth<=validation q66 and svc_group_n>=10; else low |
| test | high | 44 | 0.8636 | 0.9172 | 0.9804 | 0.1148 | 0.1772 | 0.4927 | 0.0682 | high: qwidth<=validation q33 and svc_group_n>=20; medium: qwidth<=validation q66 and svc_group_n>=10; else low |
| test | low | 436 | 0.7982 | 1.5499 | 1.8837 | 0.1573 | 0.3045 | 1.0320 | 0.1422 | high: qwidth<=validation q33 and svc_group_n>=20; medium: qwidth<=validation q66 and svc_group_n>=10; else low |
| test | medium | 127 | 0.6929 | 1.2633 | 1.4602 | 0.1118 | 0.1978 | 0.5178 | 0.0551 | high: qwidth<=validation q33 and svc_group_n>=20; medium: qwidth<=validation q66 and svc_group_n>=10; else low |
| 0604_ex50 | high | 26 | 0.6538 | 1.0159 | 2.7618 | 0.2234 | 0.3580 | 1.0017 | 0.3462 | high: qwidth<=validation q33 and svc_group_n>=20; medium: qwidth<=validation q66 and svc_group_n>=10; else low |
| 0604_ex50 | low | 655 | 0.8321 | 1.6766 | 5.3471 | 0.3032 | 0.3821 | 0.9788 | 0.2992 | high: qwidth<=validation q33 and svc_group_n>=20; medium: qwidth<=validation q66 and svc_group_n>=10; else low |
| 0604_ex50 | medium | 148 | 0.9054 | 1.3454 | 3.8397 | 0.2374 | 0.3431 | 1.0134 | 0.2365 | high: qwidth<=validation q33 and svc_group_n>=20; medium: qwidth<=validation q66 and svc_group_n>=10; else low |

## 10. 주요 계수 해석

| candidate | method | feature | standardized_coefficient | raw_role | direction | interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| current_70_30 | source | current_70_30 | 1.0000 | source_prediction | positive | 서비스 v0.1 70:30 기준 후보 |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p25 | residual_huber | ppv8_minus_stable | -0.0013 | residual_log | lowers prediction | PP-V8 component와 HCOEF 안정 후보의 차이를 제한적으로 반영한다. |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p25 | residual_huber | pred_spread | -0.0090 | residual_log | lowers prediction | component 간 예측값 차이가 큰 샘플의 위험도를 나타낸다. |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p25 | residual_huber | svc_minus_stable | -0.0107 | residual_log | lowers prediction | 유사 작품 기반 가격 피처와 안정 후보의 차이를 작게 반영한다. |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p25 | residual_huber | l10_minus_stable | -0.0124 | residual_log | lowers prediction | PP-L10 순차 component가 안정 후보와 다른 방향을 보조 신호로 쓴다. |
| hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p25 | residual_huber | current_minus_stable | -0.0313 | residual_log | lowers prediction | 70:30 기준 후보가 HCOEF 안정 후보보다 높거나 낮은 방향을 잔차 보정에 반영한다. |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p25 | residual_huber | ppv8_minus_stable | -0.0013 | residual_log | lowers prediction | PP-V8 component와 HCOEF 안정 후보의 차이를 제한적으로 반영한다. |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p25 | residual_huber | pred_spread | -0.0090 | residual_log | lowers prediction | component 간 예측값 차이가 큰 샘플의 위험도를 나타낸다. |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p25 | residual_huber | svc_minus_stable | -0.0107 | residual_log | lowers prediction | 유사 작품 기반 가격 피처와 안정 후보의 차이를 작게 반영한다. |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p25 | residual_huber | l10_minus_stable | -0.0124 | residual_log | lowers prediction | PP-L10 순차 component가 안정 후보와 다른 방향을 보조 신호로 쓴다. |
| hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p25 | residual_huber | current_minus_stable | -0.0313 | residual_log | lowers prediction | 70:30 기준 후보가 HCOEF 안정 후보보다 높거나 낮은 방향을 잔차 보정에 반영한다. |
| hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25 | residual_huber | quantile_width | 0.0369 | residual_log | raises prediction | 예측 범위가 넓은 샘플에서 residual 보정 방향이 달라지는지 확인한다. |
| hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25 | residual_huber | coverage_numeric | 0.0016 | residual_log | raises prediction | 유사 표본 수 coverage tier를 숫자로 바꾼 신뢰도 피처다. |
| hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25 | residual_huber | ppv8_minus_stable | -0.0023 | residual_log | lowers prediction | PP-V8 component와 HCOEF 안정 후보의 차이를 제한적으로 반영한다. |
| hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25 | residual_huber | log_area_filled | -0.0061 | residual_log | lowers prediction | 표준화 계수 -0.0061로 잔차 또는 로그 가격을 보조한다. |
| hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25 | residual_huber | svc_group_n_log | -0.0084 | residual_log | lowers prediction | 유사 표본 수가 많을수록 기준가 신뢰도가 높다는 신호다. |
| hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25 | residual_huber | svc_minus_stable | -0.0091 | residual_log | lowers prediction | 유사 작품 기반 가격 피처와 안정 후보의 차이를 작게 반영한다. |
| hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25 | residual_huber | l10_minus_stable | -0.0103 | residual_log | lowers prediction | PP-L10 순차 component가 안정 후보와 다른 방향을 보조 신호로 쓴다. |
| hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25 | residual_huber | pred_spread | -0.0123 | residual_log | lowers prediction | component 간 예측값 차이가 큰 샘플의 위험도를 나타낸다. |
| hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25 | residual_huber | current_minus_stable | -0.0297 | residual_log | lowers prediction | 70:30 기준 후보가 HCOEF 안정 후보보다 높거나 낮은 방향을 잔차 보정에 반영한다. |
| hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25 | residual_huber | l10_price_range_ratio | -0.0439 | residual_log | lowers prediction | 가격 범위가 넓을수록 불확실성이 크다는 신호로 해석한다. |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p25 | residual_huber | quantile_width | 0.0369 | residual_log | raises prediction | 예측 범위가 넓은 샘플에서 residual 보정 방향이 달라지는지 확인한다. |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p25 | residual_huber | coverage_numeric | 0.0016 | residual_log | raises prediction | 유사 표본 수 coverage tier를 숫자로 바꾼 신뢰도 피처다. |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p25 | residual_huber | ppv8_minus_stable | -0.0023 | residual_log | lowers prediction | PP-V8 component와 HCOEF 안정 후보의 차이를 제한적으로 반영한다. |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p25 | residual_huber | log_area_filled | -0.0061 | residual_log | lowers prediction | 표준화 계수 -0.0061로 잔차 또는 로그 가격을 보조한다. |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p25 | residual_huber | svc_group_n_log | -0.0084 | residual_log | lowers prediction | 유사 표본 수가 많을수록 기준가 신뢰도가 높다는 신호다. |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p25 | residual_huber | svc_minus_stable | -0.0091 | residual_log | lowers prediction | 유사 작품 기반 가격 피처와 안정 후보의 차이를 작게 반영한다. |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p25 | residual_huber | l10_minus_stable | -0.0103 | residual_log | lowers prediction | PP-L10 순차 component가 안정 후보와 다른 방향을 보조 신호로 쓴다. |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p25 | residual_huber | pred_spread | -0.0123 | residual_log | lowers prediction | component 간 예측값 차이가 큰 샘플의 위험도를 나타낸다. |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p25 | residual_huber | current_minus_stable | -0.0297 | residual_log | lowers prediction | 70:30 기준 후보가 HCOEF 안정 후보보다 높거나 낮은 방향을 잔차 보정에 반영한다. |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p25 | residual_huber | l10_price_range_ratio | -0.0438 | residual_log | lowers prediction | 가격 범위가 넓을수록 불확실성이 크다는 신호로 해석한다. |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p03_s0p25 | residual_huber | quantile_width | 0.0369 | residual_log | raises prediction | 예측 범위가 넓은 샘플에서 residual 보정 방향이 달라지는지 확인한다. |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p03_s0p25 | residual_huber | coverage_numeric | 0.0016 | residual_log | raises prediction | 유사 표본 수 coverage tier를 숫자로 바꾼 신뢰도 피처다. |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p03_s0p25 | residual_huber | ppv8_minus_stable | -0.0023 | residual_log | lowers prediction | PP-V8 component와 HCOEF 안정 후보의 차이를 제한적으로 반영한다. |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p03_s0p25 | residual_huber | log_area_filled | -0.0061 | residual_log | lowers prediction | 표준화 계수 -0.0061로 잔차 또는 로그 가격을 보조한다. |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p03_s0p25 | residual_huber | svc_group_n_log | -0.0084 | residual_log | lowers prediction | 유사 표본 수가 많을수록 기준가 신뢰도가 높다는 신호다. |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p03_s0p25 | residual_huber | svc_minus_stable | -0.0091 | residual_log | lowers prediction | 유사 작품 기반 가격 피처와 안정 후보의 차이를 작게 반영한다. |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p03_s0p25 | residual_huber | l10_minus_stable | -0.0103 | residual_log | lowers prediction | PP-L10 순차 component가 안정 후보와 다른 방향을 보조 신호로 쓴다. |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p03_s0p25 | residual_huber | pred_spread | -0.0123 | residual_log | lowers prediction | component 간 예측값 차이가 큰 샘플의 위험도를 나타낸다. |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p03_s0p25 | residual_huber | current_minus_stable | -0.0297 | residual_log | lowers prediction | 70:30 기준 후보가 HCOEF 안정 후보보다 높거나 낮은 방향을 잔차 보정에 반영한다. |
| hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p03_s0p25 | residual_huber | l10_price_range_ratio | -0.0438 | residual_log | lowers prediction | 가격 범위가 넓을수록 불확실성이 크다는 신호로 해석한다. |
| hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p25 | residual_ridge | quantile_width | 0.1173 | residual_log | raises prediction | 예측 범위가 넓은 샘플에서 residual 보정 방향이 달라지는지 확인한다. |
| hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p25 | residual_ridge | coverage_numeric | 0.0032 | residual_log | raises prediction | 유사 표본 수 coverage tier를 숫자로 바꾼 신뢰도 피처다. |
| hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p25 | residual_ridge | log_area_filled | -0.0008 | residual_log | lowers prediction | 표준화 계수 -0.0008로 잔차 또는 로그 가격을 보조한다. |
| hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p25 | residual_ridge | l10_minus_stable | -0.0037 | residual_log | lowers prediction | PP-L10 순차 component가 안정 후보와 다른 방향을 보조 신호로 쓴다. |
| hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p25 | residual_ridge | ppv8_minus_stable | -0.0048 | residual_log | lowers prediction | PP-V8 component와 HCOEF 안정 후보의 차이를 제한적으로 반영한다. |
| hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p25 | residual_ridge | pred_spread | -0.0086 | residual_log | lowers prediction | component 간 예측값 차이가 큰 샘플의 위험도를 나타낸다. |
| hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p25 | residual_ridge | svc_minus_stable | -0.0127 | residual_log | lowers prediction | 유사 작품 기반 가격 피처와 안정 후보의 차이를 작게 반영한다. |
| hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p25 | residual_ridge | svc_group_n_log | -0.0155 | residual_log | lowers prediction | 유사 표본 수가 많을수록 기준가 신뢰도가 높다는 신호다. |
| hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p25 | residual_ridge | current_minus_stable | -0.0455 | residual_log | lowers prediction | 70:30 기준 후보가 HCOEF 안정 후보보다 높거나 낮은 방향을 잔차 보정에 반영한다. |
| hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p25 | residual_ridge | l10_price_range_ratio | -0.1313 | residual_log | lowers prediction | 가격 범위가 넓을수록 불확실성이 크다는 신호로 해석한다. |
| hcoef20_resid_ridge_component_gaps_qwidth_a1_cap0p02_s0p25 | residual_ridge | quantile_width | 0.1141 | residual_log | raises prediction | 예측 범위가 넓은 샘플에서 residual 보정 방향이 달라지는지 확인한다. |
| hcoef20_resid_ridge_component_gaps_qwidth_a1_cap0p02_s0p25 | residual_ridge | coverage_numeric | 0.0030 | residual_log | raises prediction | 유사 표본 수 coverage tier를 숫자로 바꾼 신뢰도 피처다. |
| hcoef20_resid_ridge_component_gaps_qwidth_a1_cap0p02_s0p25 | residual_ridge | log_area_filled | -0.0007 | residual_log | lowers prediction | 표준화 계수 -0.0007로 잔차 또는 로그 가격을 보조한다. |
| hcoef20_resid_ridge_component_gaps_qwidth_a1_cap0p02_s0p25 | residual_ridge | l10_minus_stable | -0.0037 | residual_log | lowers prediction | PP-L10 순차 component가 안정 후보와 다른 방향을 보조 신호로 쓴다. |
| hcoef20_resid_ridge_component_gaps_qwidth_a1_cap0p02_s0p25 | residual_ridge | ppv8_minus_stable | -0.0047 | residual_log | lowers prediction | PP-V8 component와 HCOEF 안정 후보의 차이를 제한적으로 반영한다. |
| hcoef20_resid_ridge_component_gaps_qwidth_a1_cap0p02_s0p25 | residual_ridge | pred_spread | -0.0085 | residual_log | lowers prediction | component 간 예측값 차이가 큰 샘플의 위험도를 나타낸다. |
| hcoef20_resid_ridge_component_gaps_qwidth_a1_cap0p02_s0p25 | residual_ridge | svc_minus_stable | -0.0127 | residual_log | lowers prediction | 유사 작품 기반 가격 피처와 안정 후보의 차이를 작게 반영한다. |
| hcoef20_resid_ridge_component_gaps_qwidth_a1_cap0p02_s0p25 | residual_ridge | svc_group_n_log | -0.0156 | residual_log | lowers prediction | 유사 표본 수가 많을수록 기준가 신뢰도가 높다는 신호다. |
| hcoef20_resid_ridge_component_gaps_qwidth_a1_cap0p02_s0p25 | residual_ridge | current_minus_stable | -0.0454 | residual_log | lowers prediction | 70:30 기준 후보가 HCOEF 안정 후보보다 높거나 낮은 방향을 잔차 보정에 반영한다. |
| hcoef20_resid_ridge_component_gaps_qwidth_a1_cap0p02_s0p25 | residual_ridge | l10_price_range_ratio | -0.1281 | residual_log | lowers prediction | 가격 범위가 넓을수록 불확실성이 크다는 신호로 해석한다. |
| hcoef_stable | source | hcoef_stable | 1.0000 | source_prediction | positive | 현재 HCOEF 안정 후보 |

## 11. 구간별 잔차 요약

| scope | split | candidate | segment_col | segment_value | n | MdAPE | MAPE | p95_APE | median_residual_log | mean_residual_log | mean_abs_move_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_020_plus | 402 | 0.4302 | 0.5054 | 1.0000 | 0.2961 | 0.6185 | 0.0225 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p25 | gap_band | gap_020_plus | 402 | 0.4372 | 0.5048 | 0.9999 | 0.2780 | 0.6031 | 0.0045 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p25 | gap_band | gap_020_plus | 402 | 0.4372 | 0.5048 | 0.9999 | 0.2780 | 0.6031 | 0.0045 |
| 0604_stress | 0604_ex50 | hcoef_stable | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25 | gap_band | gap_020_plus | 402 | 0.4337 | 0.5038 | 0.9999 | 0.2849 | 0.6092 | 0.0050 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p25 | gap_band | gap_020_plus | 402 | 0.4337 | 0.5038 | 0.9999 | 0.2849 | 0.6092 | 0.0050 |
| 0604_stress | 0604_ex50 | hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p25 | gap_band | gap_020_plus | 402 | 0.4337 | 0.5038 | 0.9999 | 0.2849 | 0.6092 | 0.0050 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_010_020 | 128 | 0.2248 | 0.3419 | 0.8656 | -0.0556 | 0.0461 | 0.0217 |
| 0604_stress | 0604_ex50 | hcoef_stable | gap_band | gap_010_020 | 128 | 0.2255 | 0.3393 | 0.8728 | -0.0465 | 0.0399 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p25 | gap_band | gap_010_020 | 128 | 0.2214 | 0.3383 | 0.8757 | -0.0415 | 0.0397 | 0.0047 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p25 | gap_band | gap_010_020 | 128 | 0.2214 | 0.3383 | 0.8757 | -0.0415 | 0.0397 | 0.0047 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25 | gap_band | gap_010_020 | 128 | 0.2194 | 0.3369 | 0.8700 | -0.0415 | 0.0449 | 0.0050 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p25 | gap_band | gap_010_020 | 128 | 0.2194 | 0.3369 | 0.8700 | -0.0415 | 0.0449 | 0.0050 |
| 0604_stress | 0604_ex50 | hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p25 | gap_band | gap_010_020 | 128 | 0.2194 | 0.3369 | 0.8700 | -0.0415 | 0.0449 | 0.0050 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_005_010 | 125 | 0.1531 | 0.2572 | 0.9461 | 0.0641 | 0.0905 | 0.0190 |
| 0604_stress | 0604_ex50 | hcoef_stable | gap_band | gap_005_010 | 125 | 0.1498 | 0.2514 | 0.9526 | 0.0403 | 0.0872 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25 | gap_band | gap_005_010 | 125 | 0.1540 | 0.2513 | 0.9428 | 0.0453 | 0.0922 | 0.0050 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p25 | gap_band | gap_005_010 | 125 | 0.1540 | 0.2513 | 0.9428 | 0.0453 | 0.0922 | 0.0050 |
| 0604_stress | 0604_ex50 | hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p25 | gap_band | gap_005_010 | 125 | 0.1540 | 0.2513 | 0.9428 | 0.0453 | 0.0922 | 0.0050 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p25 | gap_band | gap_005_010 | 125 | 0.1508 | 0.2506 | 0.9464 | 0.0353 | 0.0866 | 0.0045 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p25 | gap_band | gap_005_010 | 125 | 0.1508 | 0.2506 | 0.9464 | 0.0353 | 0.0866 | 0.0045 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_000_003 | 119 | 0.1066 | 0.1953 | 0.5444 | 0.0401 | 0.0761 | 0.0164 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_003_005 | 55 | 0.0809 | 0.1908 | 0.5325 | 0.0305 | 0.0819 | 0.0227 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25 | gap_band | gap_000_003 | 119 | 0.0998 | 0.1888 | 0.5323 | 0.0322 | 0.0754 | 0.0050 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p25 | gap_band | gap_000_003 | 119 | 0.0998 | 0.1888 | 0.5323 | 0.0322 | 0.0754 | 0.0050 |
| 0604_stress | 0604_ex50 | hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p25 | gap_band | gap_000_003 | 119 | 0.0998 | 0.1888 | 0.5323 | 0.0322 | 0.0754 | 0.0050 |
| 0604_stress | 0604_ex50 | hcoef_stable | gap_band | gap_000_003 | 119 | 0.1053 | 0.1886 | 0.5300 | 0.0272 | 0.0704 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p25 | gap_band | gap_000_003 | 119 | 0.0998 | 0.1877 | 0.5276 | 0.0231 | 0.0689 | 0.0039 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p25 | gap_band | gap_000_003 | 119 | 0.0998 | 0.1877 | 0.5276 | 0.0231 | 0.0689 | 0.0039 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25 | gap_band | gap_003_005 | 55 | 0.0914 | 0.1848 | 0.5167 | 0.0175 | 0.0866 | 0.0050 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p25 | gap_band | gap_003_005 | 55 | 0.0914 | 0.1848 | 0.5167 | 0.0175 | 0.0866 | 0.0050 |
| 0604_stress | 0604_ex50 | hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p25 | gap_band | gap_003_005 | 55 | 0.0914 | 0.1848 | 0.5167 | 0.0175 | 0.0866 | 0.0050 |
| 0604_stress | 0604_ex50 | hcoef_stable | gap_band | gap_003_005 | 55 | 0.0868 | 0.1845 | 0.5173 | 0.0125 | 0.0816 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p25 | gap_band | gap_003_005 | 55 | 0.0914 | 0.1839 | 0.5131 | 0.0075 | 0.0821 | 0.0046 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p25 | gap_band | gap_003_005 | 55 | 0.0914 | 0.1839 | 0.5131 | 0.0075 | 0.0821 | 0.0046 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p25 | medium_support_bucket | other__metal | 6 | 0.6474 | 1.2678 | 3.3788 | -0.4555 | 0.3050 | 0.0042 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p25 | medium_support_bucket | other__metal | 6 | 0.6474 | 1.2678 | 3.3788 | -0.4555 | 0.3050 | 0.0042 |
| 0604_stress | 0604_ex50 | hcoef_stable | medium_support_bucket | other__metal | 6 | 0.6507 | 1.2662 | 3.3787 | -0.4505 | 0.3042 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25 | medium_support_bucket | other__metal | 6 | 0.6474 | 1.2583 | 3.3594 | -0.4455 | 0.3092 | 0.0050 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p25 | medium_support_bucket | other__metal | 6 | 0.6474 | 1.2583 | 3.3594 | -0.4455 | 0.3092 | 0.0050 |
| 0604_stress | 0604_ex50 | hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p25 | medium_support_bucket | other__metal | 6 | 0.6474 | 1.2583 | 3.3594 | -0.4455 | 0.3092 | 0.0050 |
| 0604_stress | 0604_ex50 | current_70_30 | medium_support_bucket | other__metal | 6 | 0.6672 | 1.2374 | 3.2827 | -0.4255 | 0.3042 | 0.0250 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p25 | medium_support_bucket | pencil__paper | 14 | 0.2258 | 0.7074 | 2.2846 | -0.1225 | -0.0553 | 0.0044 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p25 | medium_support_bucket | pencil__paper | 14 | 0.2258 | 0.7074 | 2.2846 | -0.1225 | -0.0553 | 0.0044 |
| 0604_stress | 0604_ex50 | hcoef_stable | medium_support_bucket | pencil__paper | 14 | 0.2246 | 0.7067 | 2.2775 | -0.1225 | -0.0538 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25 | medium_support_bucket | pencil__paper | 14 | 0.2258 | 0.7018 | 2.2611 | -0.1175 | -0.0488 | 0.0050 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p25 | medium_support_bucket | pencil__paper | 14 | 0.2258 | 0.7018 | 2.2611 | -0.1175 | -0.0488 | 0.0050 |
| 0604_stress | 0604_ex50 | hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p25 | medium_support_bucket | pencil__paper | 14 | 0.2258 | 0.7018 | 2.2611 | -0.1175 | -0.0488 | 0.0050 |
| 0604_stress | 0604_ex50 | current_70_30 | medium_support_bucket | pencil__paper | 14 | 0.2449 | 0.6988 | 2.2144 | -0.1246 | -0.0452 | 0.0217 |
| 0604_stress | 0604_ex50 | current_70_30 | medium_support_bucket | mixed__other | 15 | 0.6284 | 0.6781 | 0.9871 | 0.9898 | 1.6229 | 0.0250 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25 | medium_support_bucket | mixed__other | 15 | 0.6208 | 0.6716 | 0.9868 | 0.9698 | 1.6029 | 0.0050 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p25 | medium_support_bucket | mixed__other | 15 | 0.6208 | 0.6716 | 0.9868 | 0.9698 | 1.6029 | 0.0050 |
| 0604_stress | 0604_ex50 | hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p25 | medium_support_bucket | mixed__other | 15 | 0.6208 | 0.6716 | 0.9868 | 0.9698 | 1.6029 | 0.0050 |
| 0604_stress | 0604_ex50 | hcoef_stable | medium_support_bucket | mixed__other | 15 | 0.6189 | 0.6699 | 0.9867 | 0.9648 | 1.5979 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p25 | medium_support_bucket | mixed__other | 15 | 0.6170 | 0.6683 | 0.9868 | 0.9598 | 1.5949 | 0.0050 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p25 | medium_support_bucket | mixed__other | 15 | 0.6170 | 0.6683 | 0.9868 | 0.9598 | 1.5949 | 0.0050 |
| 0604_stress | 0604_ex50 | current_70_30 | medium_support_bucket | other__other | 68 | 0.5979 | 0.5914 | 0.9225 | 0.8978 | 1.1106 | 0.0250 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25 | medium_support_bucket | other__other | 68 | 0.5898 | 0.5842 | 0.9209 | 0.8778 | 1.0921 | 0.0050 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p25 | medium_support_bucket | other__other | 68 | 0.5898 | 0.5842 | 0.9209 | 0.8778 | 1.0921 | 0.0050 |
| 0604_stress | 0604_ex50 | hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p25 | medium_support_bucket | other__other | 68 | 0.5898 | 0.5842 | 0.9209 | 0.8778 | 1.0921 | 0.0050 |
| 0604_stress | 0604_ex50 | hcoef_stable | medium_support_bucket | other__other | 68 | 0.5877 | 0.5823 | 0.9205 | 0.8728 | 1.0871 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p25 | medium_support_bucket | other__other | 68 | 0.5857 | 0.5805 | 0.9201 | 0.8678 | 1.0827 | 0.0049 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p25 | medium_support_bucket | other__other | 68 | 0.5857 | 0.5805 | 0.9201 | 0.8678 | 1.0827 | 0.0049 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p25 | medium_support_bucket | pigment__canvas | 16 | 0.6120 | 0.5407 | 0.7845 | 0.0866 | 0.3950 | 0.0045 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p25 | medium_support_bucket | pigment__canvas | 16 | 0.6120 | 0.5407 | 0.7845 | 0.0866 | 0.3950 | 0.0045 |
| 0604_stress | 0604_ex50 | hcoef_stable | medium_support_bucket | pigment__canvas | 16 | 0.6090 | 0.5384 | 0.7844 | 0.0916 | 0.3993 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25 | medium_support_bucket | pigment__canvas | 16 | 0.6059 | 0.5364 | 0.7854 | 0.0966 | 0.4043 | 0.0050 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p25 | medium_support_bucket | pigment__canvas | 16 | 0.6059 | 0.5364 | 0.7854 | 0.0966 | 0.4043 | 0.0050 |
| 0604_stress | 0604_ex50 | hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p25 | medium_support_bucket | pigment__canvas | 16 | 0.6059 | 0.5364 | 0.7854 | 0.0966 | 0.4043 | 0.0050 |
| 0604_stress | 0604_ex50 | current_70_30 | medium_support_bucket | other__paper | 60 | 0.3444 | 0.5347 | 1.0443 | 0.0954 | 0.2938 | 0.0223 |
| 0604_stress | 0604_ex50 | hcoef_stable | medium_support_bucket | other__paper | 60 | 0.3532 | 0.5342 | 1.0399 | 0.0956 | 0.2863 | 0.0000 |
| 0604_stress | 0604_ex50 | current_70_30 | medium_support_bucket | acrylic__other | 9 | 0.5130 | 0.5340 | 0.7855 | 0.7194 | 0.8650 | 0.0250 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_a0p01_cap0p02_s0p25 | medium_support_bucket | other__paper | 60 | 0.3514 | 0.5338 | 1.0392 | 0.0917 | 0.2866 | 0.0047 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_a0p001_cap0p02_s0p25 | medium_support_bucket | other__paper | 60 | 0.3514 | 0.5338 | 1.0392 | 0.0917 | 0.2866 | 0.0047 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25 | medium_support_bucket | other__paper | 60 | 0.3514 | 0.5322 | 1.0392 | 0.1006 | 0.2913 | 0.0050 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p25 | medium_support_bucket | other__paper | 60 | 0.3514 | 0.5322 | 1.0392 | 0.1006 | 0.2913 | 0.0050 |
| 0604_stress | 0604_ex50 | hcoef20_resid_ridge_component_gaps_qwidth_a0p1_cap0p02_s0p25 | medium_support_bucket | other__paper | 60 | 0.3514 | 0.5322 | 1.0392 | 0.1006 | 0.2913 | 0.0050 |
| 0604_stress | 0604_ex50 | current_70_30 | medium_support_bucket | pigment__canvas | 16 | 0.5742 | 0.5282 | 0.7897 | 0.1166 | 0.4243 | 0.0250 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25 | medium_support_bucket | acrylic__other | 9 | 0.5031 | 0.5246 | 0.7812 | 0.6994 | 0.8450 | 0.0050 |
| 0604_stress | 0604_ex50 | hcoef20_resid_huber_component_gaps_qwidth_a0p01_cap0p02_s0p25 | medium_support_bucket | acrylic__other | 9 | 0.5031 | 0.5246 | 0.7812 | 0.6994 | 0.8450 | 0.0050 |

## 12. 판단

- 운영 기본 후보가 되려면 HCOEF 안정 후보 대비 row OOF, artist OOF, fixed test에서 MdAPE/MAPE/p95가 모두 동등 또는 개선되어야 함.
- MAPE 특화 후보와 p95 방어 후보는 운영 기본 후보와 분리해 목적별 후보로만 관리.
- quantile width는 점 예측 이동 기준으로 바로 쓰지 않고, 가격 범위/신뢰도 표시 정책으로 따로 관리하는 것이 현재 실험 원칙에 맞음.

## 13. 산출물

- `artifacts/experiment_config.json`
- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/policy_map.csv`
- `outputs/residual_analysis.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `outputs/range_confidence_policy.csv`
- `outputs/selected_candidates.csv`