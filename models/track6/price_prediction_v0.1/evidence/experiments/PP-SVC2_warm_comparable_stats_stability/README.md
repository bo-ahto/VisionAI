# PP-SVC2 Warm 비교군 통계 피처 안정성 검증

- 작성일: 2026-06-03 21:20
- 목적: `PP-SVC1-W`의 비교군 통계 피처 개선이 fold seed와 후보 비교에서 안정적인지 확인한다.
- 방식: Warm Huber에 비교군 통계 피처를 넣고 OOF fold seed 10개로 반복 재학습했다.

## 1. Test 결과

| 후보 | source | seed | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---:|---:|---:|---:|---:|
| `svc_numeric_seed_202606032` | PP-SVC2_seed_repeat | 202606032 | 0.1475 | 0.2918 | 0.9546 | 0.4221 |
| `svc_full_seed_202606032` | PP-SVC2_seed_repeat | 202606032 | 0.1476 | 0.2929 | 0.9543 | 0.4225 |
| `svc_full_seed_202606038` | PP-SVC2_seed_repeat | 202606038 | 0.1508 | 0.3022 | 0.9198 | 0.4167 |
| `svc_numeric_seed_202606035` | PP-SVC2_seed_repeat | 202606035 | 0.1511 | 0.2950 | 0.9097 | 0.4164 |
| `svc_full_seed_202606037` | PP-SVC2_seed_repeat | 202606037 | 0.1515 | 0.2930 | 0.9176 | 0.4148 |
| `svc_numeric_seed_202606037` | PP-SVC2_seed_repeat | 202606037 | 0.1516 | 0.2919 | 0.9354 | 0.4165 |
| `svc_full_seed_202606035` | PP-SVC2_seed_repeat | 202606035 | 0.1517 | 0.2959 | 0.8954 | 0.4156 |
| `svc_full_seed_202606036` | PP-SVC2_seed_repeat | 202606036 | 0.1519 | 0.2900 | 0.9057 | 0.4119 |
| `svc_numeric_seed_mean` | seed_mean |  | 0.1520 | 0.2942 | 0.9381 | 0.4179 |
| `svc_numeric_seed_202606036` | PP-SVC2_seed_repeat | 202606036 | 0.1523 | 0.2896 | 0.9364 | 0.4135 |
| `svc_numeric_seed_202606039` | PP-SVC2_seed_repeat | 202606039 | 0.1523 | 0.2995 | 0.9450 | 0.4253 |
| `svc_numeric_seed_202606030` | PP-SVC2_seed_repeat | 202606030 | 0.1527 | 0.2934 | 0.9127 | 0.4131 |
| `svc_full_seed_202606039` | PP-SVC2_seed_repeat | 202606039 | 0.1527 | 0.3017 | 0.9313 | 0.4255 |
| `svc_full_seed_mean` | seed_mean |  | 0.1533 | 0.2956 | 0.9190 | 0.4168 |
| `svc_full_seed_202606034` | PP-SVC2_seed_repeat | 202606034 | 0.1535 | 0.3053 | 0.9106 | 0.4238 |
| `svc_numeric_seed_202606034` | PP-SVC2_seed_repeat | 202606034 | 0.1536 | 0.3034 | 0.9314 | 0.4264 |
| `svc_numeric_seed_202606038` | PP-SVC2_seed_repeat | 202606038 | 0.1538 | 0.3002 | 0.9227 | 0.4176 |
| `svc_full_seed_202606030` | PP-SVC2_seed_repeat | 202606030 | 0.1569 | 0.2964 | 0.9110 | 0.4129 |
| `svc_full_seed_202606031` | PP-SVC2_seed_repeat | 202606031 | 0.1570 | 0.2976 | 0.9247 | 0.4136 |
| `svc_numeric_seed_202606033` | PP-SVC2_seed_repeat | 202606033 | 0.1575 | 0.2920 | 0.9522 | 0.4223 |
| `svc_numeric_seed_202606031` | PP-SVC2_seed_repeat | 202606031 | 0.1582 | 0.2965 | 0.9294 | 0.4153 |
| `svc_full_seed_202606033` | PP-SVC2_seed_repeat | 202606033 | 0.1585 | 0.2920 | 0.9201 | 0.4211 |
| `pp_v6_fine_blend_mape_guarded` | PP-V6 |  | 0.1613 | 0.2889 | 0.9314 | 0.4079 |
| `pp_v8_compact_blend_mape_guarded` | PP-V8 |  | 0.1632 | 0.2816 | 0.9311 | 0.4028 |
| `baseline_huber` | PP-SVC2 |  | 0.2274 | 0.4952 | 2.0130 | 0.6081 |
| `direct_group_median` | service_prior |  | 0.3100 | 0.7193 | 2.2352 | 0.7632 |

## 2. Seed 안정성

| 후보 | seeds | MdAPE mean/std | MAPE mean/std | p95 mean/std |
|---|---:|---:|---:|---:|
| `svc_full` | 10 | 0.1532 / 0.0032 | 0.2967 / 0.0048 | 0.9190 / 0.0152 |
| `svc_numeric` | 10 | 0.1531 / 0.0029 | 0.2953 / 0.0042 | 0.9330 / 0.0144 |

## 3. PP-V6 대비 bootstrap

| 후보 | mode | MdAPE 개선확률 | MAPE 개선확률 | p95 개선확률 | MdAPE delta 중앙값 |
|---|---|---:|---:|---:|---:|
| `baseline_huber` | artist_bootstrap | 0.000 | 0.000 | 0.000 | -0.0672 |
| `baseline_huber` | row_bootstrap | 0.000 | 0.000 | 0.000 | -0.0661 |
| `direct_group_median` | artist_bootstrap | 0.000 | 0.000 | 0.000 | -0.1491 |
| `direct_group_median` | row_bootstrap | 0.000 | 0.000 | 0.000 | -0.1432 |
| `pp_v8_compact_blend_mape_guarded` | artist_bootstrap | 0.278 | 0.882 | 0.584 | -0.0040 |
| `pp_v8_compact_blend_mape_guarded` | row_bootstrap | 0.276 | 0.932 | 0.600 | -0.0037 |
| `svc_full_seed_mean` | artist_bootstrap | 0.802 | 0.264 | 0.426 | 0.0102 |
| `svc_full_seed_mean` | row_bootstrap | 0.796 | 0.314 | 0.518 | 0.0090 |
| `svc_numeric_seed_mean` | artist_bootstrap | 0.842 | 0.322 | 0.418 | 0.0099 |
| `svc_numeric_seed_mean` | row_bootstrap | 0.842 | 0.344 | 0.474 | 0.0093 |

## 4. Slice 결과

| 후보 | slice | value | n | MdAPE | MAPE | p95_APE |
|---|---|---|---:|---:|---:|---:|
| `svc_full_seed_mean` | svc_group_level | `artist` | 295 | 0.1947 | 0.3751 | 1.2630 |
| `svc_full_seed_mean` | svc_group_level | `artist_medium_support_size` | 247 | 0.0973 | 0.1724 | 0.5473 |
| `svc_full_seed_mean` | svc_group_level | `artist_size` | 65 | 0.2119 | 0.4028 | 1.3845 |
| `svc_full_seed_mean` | svc_coverage_tier | `high_n` | 17 | 0.1307 | 0.1580 | 0.3703 |
| `svc_full_seed_mean` | svc_coverage_tier | `low_n` | 479 | 0.1570 | 0.3230 | 1.1732 |
| `svc_full_seed_mean` | svc_coverage_tier | `medium_n` | 111 | 0.1316 | 0.1985 | 0.5555 |
| `svc_numeric_seed_mean` | svc_group_level | `artist` | 295 | 0.1927 | 0.3713 | 1.2509 |
| `svc_numeric_seed_mean` | svc_group_level | `artist_medium_support_size` | 247 | 0.0980 | 0.1718 | 0.5496 |
| `svc_numeric_seed_mean` | svc_group_level | `artist_size` | 65 | 0.2158 | 0.4096 | 1.3971 |
| `svc_numeric_seed_mean` | svc_coverage_tier | `high_n` | 17 | 0.1434 | 0.1590 | 0.3653 |
| `svc_numeric_seed_mean` | svc_coverage_tier | `low_n` | 479 | 0.1556 | 0.3215 | 1.1824 |
| `svc_numeric_seed_mean` | svc_coverage_tier | `medium_n` | 111 | 0.1332 | 0.1973 | 0.5518 |
| `baseline_huber` | svc_group_level | `artist` | 295 | 0.3145 | 0.5756 | 2.1687 |
| `baseline_huber` | svc_group_level | `artist_medium_support_size` | 247 | 0.1393 | 0.3457 | 1.6449 |
| `baseline_huber` | svc_group_level | `artist_size` | 65 | 0.3278 | 0.6983 | 2.9937 |
| `baseline_huber` | svc_coverage_tier | `high_n` | 17 | 0.1748 | 0.1870 | 0.3665 |
| `baseline_huber` | svc_coverage_tier | `low_n` | 479 | 0.2592 | 0.5709 | 2.3715 |
| `baseline_huber` | svc_coverage_tier | `medium_n` | 111 | 0.1445 | 0.2156 | 0.7090 |
| `direct_group_median` | svc_group_level | `artist` | 295 | 0.5286 | 1.2185 | 3.5792 |
| `direct_group_median` | svc_group_level | `artist_medium_support_size` | 247 | 0.0935 | 0.2141 | 0.7549 |
| `direct_group_median` | svc_group_level | `artist_size` | 65 | 0.2593 | 0.3739 | 1.1743 |
| `direct_group_median` | svc_coverage_tier | `high_n` | 17 | 0.2917 | 0.4831 | 1.3600 |
| `direct_group_median` | svc_coverage_tier | `low_n` | 479 | 0.3030 | 0.6696 | 1.9886 |
| `direct_group_median` | svc_coverage_tier | `medium_n` | 111 | 0.3457 | 0.9700 | 3.3333 |

## 5. 해석

- seed별 성능 편차가 작다면 비교군 통계 피처는 OOF fold 우연에 덜 민감하다고 본다.
- `svc_full_seed_mean`이 `PP-V6`보다 bootstrap 개선확률이 높으면 Warm 최종 후보 재검증 대상으로 올린다.
- 직접 비교군 중앙값 후보가 약하면, 개선 원인은 중앙값 직접 대체가 아니라 Huber가 비교군 통계를 설명 변수로 사용한 효과로 해석한다.

## 6. 실행 결론

- Warm 비교군 통계 피처의 MdAPE 개선은 seed 반복에서도 유지됐다.
- `svc_full` seed 평균 MdAPE는 `0.1532`, 표준편차는 `0.0032`로 fold 구성에 크게 흔들리지 않았다.
- `svc_numeric_seed_mean`은 test MdAPE `0.1520`, `svc_full_seed_mean`은 test MdAPE `0.1533`으로 기존 `PP-V6` MdAPE `0.1613`보다 낮았다.
- `PP-V6` 대비 MdAPE 개선확률은 `svc_numeric_seed_mean` row/artist bootstrap 모두 `0.842`, `svc_full_seed_mean`은 row `0.796`, artist `0.802`였다.
- 반면 MAPE는 `PP-V6` `0.2889`, `PP-V8` `0.2816`이 `svc_numeric/full` 평균 후보보다 더 좋았다.
- 따라서 Warm 최종 정책은 단일 후보 교체가 아니라 목적별 분리가 맞다.
- 대표 정확도(MdAPE)는 `svc_numeric/full` 비교군 통계 후보를 우선 검토하고, 평균오차(MAPE) 방어는 `PP-V6/PP-V8`을 유지하는 방향이 합리적이다.
- 다음 실험은 `svc_numeric/full`과 `PP-V6/PP-V8`의 조건별 라우팅 또는 가중 결합으로 MdAPE와 MAPE를 동시에 낮출 수 있는지 확인하는 것이 좋다.
