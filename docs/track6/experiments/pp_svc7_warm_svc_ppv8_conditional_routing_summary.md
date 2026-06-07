# PP-SVC7 Warm 70:30 vs 운영 pp_v8 조건부 라우팅 + 0604 동시 검증

- 작성일: 2026-06-07 17:01
- weight grid: [0.0, 0.3, 0.5, 0.7] (0.0=pp_v8, 0.70=70:30), validation 전역 best w = 0.7
- disagreement 경계(validation |svc-ppv8| q33/q66): 0.0573 / 0.1661
- 라우팅 규칙은 고정 validation에서만 선택, 고정 test와 0604는 확인용

## 1. 실행 결론

- 어떤 라우터도 고정 test(70:30)와 0604(pp_v8)를 동시에 만족하지 못함 → 70:30 vs pp_v8 차이는 라우팅 불가한 영역(distribution shift) 차이로 결론
- 고정 test 목표(70:30): MdAPE 0.1405 / 0604 목표(pp_v8): MdAPE 0.2298

## 2. 후보 × 영역 MdAPE

| candidate | validation | test | 0604 |
| --- | --- | --- | --- |
| blend_0.70 | 0.1305 | 0.1405 | 0.2779 |
| pp_v8 | 0.1544 | 0.1632 | 0.2298 |
| router_disagree_bin | 0.1305 | 0.1413 | 0.2779 |
| router_svc_coverage_tier | 0.1287 | 0.1398 | 0.2797 |
| router_svc_group_level | 0.1271 | 0.1426 | 0.2682 |

## 3. 라우터 영역 통합 판정

| router | test_MdAPE | test_target(blend) | test_ok | ops_MdAPE | ops_target(pp_v8) | ops_ok | reconciles_both |
| --- | --- | --- | --- | --- | --- | --- | --- |
| router_svc_coverage_tier | 0.1398 | 0.1405 | True | 0.2797 | 0.2298 | False | False |
| router_svc_group_level | 0.1426 | 0.1405 | True | 0.2682 | 0.2298 | False | False |
| router_disagree_bin | 0.1413 | 0.1405 | True | 0.2779 | 0.2298 | False | False |

## 4. 전역 weight tradeoff (영역별 MdAPE)

| w_svc | validation | test | 0604 |
| --- | --- | --- | --- |
| 0.0000 | 0.1544 | 0.1632 | 0.2298 |
| 0.1000 | 0.1493 | 0.1626 | 0.2358 |
| 0.2000 | 0.1470 | 0.1593 | 0.2385 |
| 0.3000 | 0.1451 | 0.1534 | 0.2425 |
| 0.4000 | 0.1393 | 0.1450 | 0.2500 |
| 0.5000 | 0.1345 | 0.1413 | 0.2510 |
| 0.6000 | 0.1389 | 0.1395 | 0.2618 |
| 0.7000 | 0.1305 | 0.1405 | 0.2779 |
| 0.8000 | 0.1241 | 0.1455 | 0.2919 |
| 0.9000 | 0.1245 | 0.1505 | 0.3024 |
| 1.0000 | 0.1272 | 0.1520 | 0.3072 |

## 5. svc_coverage_tier 라우터: 선택 weight와 0604 segment 비교

| svc_coverage_tier | n | selected_w | router_MdAPE | ppv8_MdAPE |
| --- | --- | --- | --- | --- |
| fallback_global | 18 | 0.7000 | 0.6453 | 0.6931 |
| high_n | 87 | 0.7000 | 0.4544 | 0.3435 |
| low_n | 569 | 0.7000 | 0.2537 | 0.2328 |
| medium_n | 155 | 0.5000 | 0.2355 | 0.1784 |

## 6. 산출물

- `outputs/region_candidate_metrics.csv`, `outputs/global_weight_sweep.csv`
- `outputs/router_segment_weight_map.csv`, `outputs/router_0604_segment_breakdown.csv`, `outputs/router_verdict.csv`
- `artifacts/run_config.json`