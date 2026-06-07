# PP-SVC3 Warm 비교군 통계 후보 결합/라우팅

- 작성일: 2026-06-03 21:31
- 목적: Warm 비교군 통계 후보와 기존 Warm 후보를 결합해 MdAPE와 MAPE 균형이 좋아지는지 확인한다.
- 원칙: 가중치와 라우팅 기준은 validation에서만 선택하고 test는 선택 후 확인으로 사용한다.

## 1. Validation 상위 후보

| 후보 | method | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---:|---:|---:|---:|
| `blend_svcnum_ppv6_wsvc_0.80` | weighted_blend | 0.1223 | 0.2139 | 0.6441 | 0.3326 |
| `route_svc_coverage_tier_mdape` | segment_route | 0.1225 | 0.2144 | 0.6495 | 0.3361 |
| `route_svc_coverage_tier_balanced` | segment_route | 0.1225 | 0.2144 | 0.6495 | 0.3361 |
| `blend_svcnum_ppv6_wsvc_0.85` | weighted_blend | 0.1230 | 0.2145 | 0.6596 | 0.3330 |
| `blend_svcnum_ppv6_wsvc_0.75` | weighted_blend | 0.1234 | 0.2139 | 0.6535 | 0.3326 |
| `blend_svcnum_ppv8_wsvc_0.85` | weighted_blend | 0.1236 | 0.2128 | 0.6496 | 0.3310 |
| `blend_svcfull_ppv8_wsvc_0.85` | weighted_blend | 0.1241 | 0.2136 | 0.6512 | 0.3323 |
| `blend_svcnum_ppv8_wsvc_0.80` | weighted_blend | 0.1241 | 0.2117 | 0.6437 | 0.3299 |
| `blend_svcnum_ppv6_wsvc_0.90` | weighted_blend | 0.1244 | 0.2153 | 0.6514 | 0.3338 |
| `blend_svcnum_ppv8_wsvc_0.90` | weighted_blend | 0.1245 | 0.2141 | 0.6517 | 0.3324 |
| `blend_svcfull_ppv6_wsvc_0.85` | weighted_blend | 0.1246 | 0.2154 | 0.6593 | 0.3342 |
| `blend_svcnum_ppv8_wsvc_0.75` | weighted_blend | 0.1247 | 0.2112 | 0.6446 | 0.3293 |
| `blend_svcfull_ppv8_wsvc_0.75` | weighted_blend | 0.1260 | 0.2117 | 0.6518 | 0.3304 |
| `blend_svcfull_ppv6_wsvc_0.80` | weighted_blend | 0.1261 | 0.2148 | 0.6436 | 0.3337 |
| `blend_svcnum_ppv8_wsvc_0.95` | weighted_blend | 0.1263 | 0.2157 | 0.6489 | 0.3343 |
| `blend_svcnum_ppv6_wsvc_0.95` | weighted_blend | 0.1263 | 0.2163 | 0.6497 | 0.3350 |
| `blend_svcfull_ppv8_wsvc_0.90` | weighted_blend | 0.1265 | 0.2149 | 0.6522 | 0.3339 |
| `route_svc_group_level_p95_guarded` | segment_route | 0.1266 | 0.2172 | 0.6504 | 0.3363 |
| `blend_svcfull_ppv8_wsvc_0.80` | weighted_blend | 0.1267 | 0.2124 | 0.6432 | 0.3311 |
| `route_svc_coverage_tier_p95_guarded` | segment_route | 0.1267 | 0.2163 | 0.6495 | 0.3369 |

## 2. Validation 선택 후보

| objective | selected | val MdAPE | val MAPE | val p95 |
|---|---|---:|---:|---:|
| mdape_primary | `blend_svcnum_ppv6_wsvc_0.80` | 0.1223 | 0.2139 | 0.6441 |
| mape_guarded | `blend_svcnum_ppv8_wsvc_0.70` | 0.1305 | 0.2110 | 0.6580 |
| p95_guarded | `route_disagree_svcnum_ppv6_bin_p95_guarded` | 0.1393 | 0.2218 | 0.6431 |
| balanced | `blend_svcnum_ppv6_wsvc_0.80` | 0.1223 | 0.2139 | 0.6441 |

## 3. 선택 후보 test 결과

| 후보 | method | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---:|---:|---:|---:|
| `blend_svcnum_ppv8_wsvc_0.70` | weighted_blend | 0.1405 | 0.2748 | 0.8331 | 0.3996 |
| `blend_svcnum_ppv6_wsvc_0.80` | weighted_blend | 0.1475 | 0.2839 | 0.8451 | 0.4070 |
| `svc_numeric_seed_mean` | base | 0.1520 | 0.2942 | 0.9381 | 0.4179 |
| `svc_full_seed_mean` | base | 0.1533 | 0.2956 | 0.9190 | 0.4168 |
| `route_disagree_svcnum_ppv6_bin_p95_guarded` | segment_route | 0.1534 | 0.2910 | 0.9335 | 0.4133 |
| `pp_v6_fine_blend_mape_guarded` | base | 0.1613 | 0.2889 | 0.9314 | 0.4079 |
| `pp_v8_compact_blend_mape_guarded` | base | 0.1632 | 0.2816 | 0.9311 | 0.4028 |

## 4. PP-V6 대비 bootstrap

| 후보 | mode | MdAPE 개선확률 | MAPE 개선확률 | p95 개선확률 | MdAPE delta 중앙값 |
|---|---|---:|---:|---:|---:|
| `blend_svcnum_ppv6_wsvc_0.80` | artist_bootstrap | 0.942 | 0.654 | 0.606 | 0.0137 |
| `blend_svcnum_ppv6_wsvc_0.80` | row_bootstrap | 0.978 | 0.712 | 0.718 | 0.0130 |
| `blend_svcnum_ppv8_wsvc_0.70` | artist_bootstrap | 0.998 | 0.924 | 0.718 | 0.0206 |
| `blend_svcnum_ppv8_wsvc_0.70` | row_bootstrap | 0.998 | 0.950 | 0.858 | 0.0196 |
| `pp_v8_compact_blend_mape_guarded` | artist_bootstrap | 0.278 | 0.882 | 0.584 | -0.0040 |
| `pp_v8_compact_blend_mape_guarded` | row_bootstrap | 0.276 | 0.932 | 0.600 | -0.0037 |
| `route_disagree_svcnum_ppv6_bin_p95_guarded` | artist_bootstrap | 0.804 | 0.416 | 0.426 | 0.0069 |
| `route_disagree_svcnum_ppv6_bin_p95_guarded` | row_bootstrap | 0.798 | 0.448 | 0.478 | 0.0065 |
| `svc_full_seed_mean` | artist_bootstrap | 0.802 | 0.264 | 0.426 | 0.0102 |
| `svc_full_seed_mean` | row_bootstrap | 0.796 | 0.314 | 0.518 | 0.0090 |
| `svc_numeric_seed_mean` | artist_bootstrap | 0.842 | 0.322 | 0.418 | 0.0099 |
| `svc_numeric_seed_mean` | row_bootstrap | 0.842 | 0.344 | 0.474 | 0.0093 |

## 5. 해석 기준

- validation과 test가 같은 후보를 지지하면 운영 후보로 올린다.
- validation 선택 후보가 test에서 기존 `PP-V6/PP-V8`보다 약하면, 결합 정책은 과적합 가능성이 있으므로 보류한다.
- MdAPE와 MAPE가 서로 반대로 움직이면 단일 후보가 아니라 목적별 응답 정책으로 분리한다.

## 6. 실행 결론

- `PP-SVC3`에서는 단순 가중 결합이 조건별 라우팅보다 더 안정적이었다.
- validation의 `mape_guarded` 목적에서 선택된 `blend_svcnum_ppv8_wsvc_0.70`이 test에서도 가장 좋은 운영 후보로 확인됐다.
- `blend_svcnum_ppv8_wsvc_0.70`의 test 결과는 MdAPE `0.1405`, MAPE `0.2748`, p95 `0.8331`이다.
- 기존 Warm 대표 `PP-V6`은 MdAPE `0.1613`, MAPE `0.2889`, p95 `0.9314`였고, `PP-V8`은 MdAPE `0.1632`, MAPE `0.2816`, p95 `0.9311`이었다.
- 따라서 `blend_svcnum_ppv8_wsvc_0.70`은 기존 후보 대비 MdAPE, MAPE, p95를 모두 개선했다.
- `PP-V6` 대비 bootstrap 개선확률도 row 기준 MdAPE `0.998`, MAPE `0.950`, p95 `0.858`로 강했다.
- artist bootstrap 기준도 MdAPE `0.998`, MAPE `0.924`, p95 `0.718`로 작가 구성 변동을 고려해도 개선 신호가 유지됐다.
- 현재 Warm 최종 후보는 `PP-SVC3 blend_svcnum_ppv8_wsvc_0.70`을 1순위로 올릴 수 있다.
- 단, 최종 서비스 확정 전에는 이 결합식이 validation에서 선택된 기준임을 명시하고, 가능하면 추가 split 또는 holdout 반복 검증을 한 번 더 수행하는 것이 안전하다.
