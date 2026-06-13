# PP-WMIN9B Warm-lite 경계 비교 및 라우팅 정책 감사

- 작성일: 2026-06-13 10:16
- 데이터 기준: PP-WCUT4 실존 저이력 leave-one-out + PP-WMIN8 fixed test artifact
- 0604: 사용하지 않음
- 결론: 1~4건은 Warm-lite, 5건 이상은 WMIN8 조건부 라우팅으로 분리하는 경계가 현재 검증 결과와 일치한다. 저이력 행에 WMIN8을 강제 적용하는 비교는 운영 라우팅 조건을 깨기 때문에 채택 근거로 사용하지 않는다.

## 1. 라우팅 경계 판단
| history_count | route | status | evidence |
| --- | --- | --- | --- |
| 0 | Cold | keep | 동일 작가 이력이 없으면 Warm 계열의 작가 이력 통계가 계산되지 않음 |
| 1~4 | Warm-lite | validated | 실존 저이력 leave-one-out n=1947, Warm-lite MAPE 0.2866 vs Cold 0.9946, bootstrap gate {'p_MdAPE': 1.0, 'p_MAPE': 1.0, 'p_p95': 1.0, 'gate_pass': True} |
| 5+ | Warm WMIN8 | validated | fixed test n=607, MdAPE/MAPE/p95 0.1043/0.2358/0.7394; WMIN8 conditional route가 WMIN4와 PP258을 모두 개선 |

## 2. 저이력 1~4건 Warm-lite 검증
| route | n | artist_count | warm_lite_MdAPE | warm_lite_MAPE | warm_lite_p95_APE | cold_MdAPE | cold_MAPE | cold_p95_APE | delta_MAPE_vs_cold | delta_p95_APE_vs_cold |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Warm-lite 1~4 history | 1947 | 649 | 0.109227 | 0.286566 | 0.876470 | 0.542931 | 0.994585 | 2.535820 | -0.708019 | -1.659350 |

## 3. 이력 수별 Warm-lite 검증
| history_k | n | warm_lite_MdAPE | warm_lite_MAPE | warm_lite_p95_APE | cold_MdAPE | cold_MAPE | cold_p95_APE | delta_MAPE_vs_cold | delta_p95_APE_vs_cold |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 621 | 0.120677 | 0.341476 | 0.955881 | 0.560817 | 0.846008 | 2.236897 | -0.504532 | -1.281016 |
| 2 | 489 | 0.118375 | 0.270704 | 0.877912 | 0.569159 | 1.382894 | 3.222387 | -1.112190 | -2.344475 |
| 3 | 324 | 0.105981 | 0.254102 | 0.714172 | 0.507388 | 0.883915 | 2.727458 | -0.629812 | -2.013287 |
| 4 | 513 | 0.092263 | 0.255719 | 0.788372 | 0.512221 | 0.874196 | 3.084911 | -0.618477 | -2.296539 |

## 4. Warm 5건 이상 WMIN8 검증
| route | candidate_label | n | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- | --- |
| Warm WMIN8 5+ history | min1_route_w850_risk_q50_altlower_gap005 | 607 | 0.104326 | 0.235814 | 0.739416 | 0.377190 |
| min1_base_before_router | min1_huber_refit_partial | 607 | 0.106598 | 0.239302 | 0.779196 | 0.376884 |
| previous_operational_reference | current_pp258_operational_reference | 607 | 0.140976 | 0.269888 | 0.807325 | 0.397454 |

## 5. 검증 상태
| check | status | detail |
| --- | --- | --- |
| warm_lite_low_history_evidence | pass | PP-WCUT4 real low-history leave-one-out gate pass |
| wmin8_5plus_evidence | pass | PP-WMIN8 fixed test confirmation and packaged artifact available |
| direct_same_row_wmin8_vs_warm_lite_low_history | not_adopted | WMIN8 is a 5+ same-artist-history route. Forcing it onto 1~4 history rows would break the production route invariant, so the same-row comparison is not used as an operating decision. |
| warm_lite_artifact | pass | models/track6/warm_lite_v0.1/config/warm_lite_policy_v0_1.json |
| wmin8_exact_raw_adapter | pass | api_fixed_test_parity_pass=True, blocking_items=[] |
| official_service_route_boundary | pass | official v0.1 route boundary: 0 history -> Cold, 1~4 -> Warm-lite, 5+ -> WMIN8 Warm |

## 6. 실행 설정
```json
{
  "experiment_id": "PP-WMIN9B",
  "experiment_slug": "PP-WMIN9B_warm_lite_boundary_comparison",
  "created_at": "2026-06-13T10:16:49",
  "selection_policy": "no new candidate selection; routing boundary and adapter-gap audit only",
  "source_experiments": {
    "low_history": "experiments/track6/PP-WCUT4_real_low_history_validation",
    "warm_5plus": "experiments/track6/PP-WMIN8_warm_min1_weight_router",
    "warm_5plus_artifact": "models/track6/warm_wmin8_operational_candidate"
  },
  "direct_same_row_low_history_wmin8_comparison": "not_adopted_because_wmin8_is_5plus_history_route",
  "prohibitions": [
    "0604 not used"
  ]
}
```
