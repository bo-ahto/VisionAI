# PP-WMIN2 Warm 작가 ladder 최소 표본 1건 운영형 SVC 검증

- 작성일: 2026-06-12 20:24
- 목적: Warm SVC의 작가 포함 비교군 ladder 최소 표본을 5건에서 1건으로 낮췄을 때 운영형 70:30 기준가까지 개선되는지 확인한다.
- 변경점: `artist_key`가 포함된 ladder(`artist_medium_support_size`, `artist_size`, `artist`)의 `min_n`만 1로 변경한다.
- 유지점: 기본 Warm 피처, Huber 학습 방식, SVC numeric 피처, PP-V8 참조 후보, 70:30 결합식은 기존 PP-SVC2/PP-SVC3와 동일하게 둔다.
- 검증 원칙: validation과 train OOF audit로 판단하고, fixed test는 최종 확인용으로만 기록한다.

## 1. Validation 판단

| 비교 | 변화량(기존-후보, 양수면 개선) |
|---|---:|
| SVC 단독 `current_svc_numeric_seed_mean_min5` → `wmin2_svc_numeric_seed_mean_min1` | MdAPE +0.0324, MAPE +0.0320, p95 +0.0444 |
| 70:30 `current_70_30_min5_svc_ppv8` → `wmin2_70_30_min1_svc_ppv8` | MdAPE +0.0230, MAPE +0.0305, p95 +0.0762 |

## 2. Fixed Test 확인

| 비교 | 변화량(기존-후보, 양수면 개선) |
|---|---:|
| SVC 단독 `current_svc_numeric_seed_mean_min5` → `wmin2_svc_numeric_seed_mean_min1` | MdAPE +0.0404, MAPE +0.0405, p95 +0.1349 |
| 70:30 `current_70_30_min5_svc_ppv8` → `wmin2_70_30_min1_svc_ppv8` | MdAPE +0.0322, MAPE +0.0351, p95 +0.0505 |

## 3. 전체 지표

| split | 후보 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---:|---:|---:|---:|
| test | `wmin2_70_30_min1_svc_ppv8` | 0.1083 | 0.2397 | 0.7826 | 0.3765 |
| test | `wmin2_svc_numeric_seed_mean_min1` | 0.1116 | 0.2537 | 0.8032 | 0.3924 |
| test | `current_70_30_min5_svc_ppv8` | 0.1405 | 0.2748 | 0.8331 | 0.3996 |
| test | `current_svc_numeric_seed_mean_min5` | 0.1520 | 0.2942 | 0.9381 | 0.4179 |
| test | `pp_v8_compact_blend_mape_guarded` | 0.1632 | 0.2816 | 0.9311 | 0.4028 |
| validation | `wmin2_svc_numeric_seed_mean_min1` | 0.0948 | 0.1856 | 0.6060 | 0.3142 |
| validation | `wmin2_70_30_min1_svc_ppv8` | 0.1075 | 0.1806 | 0.5819 | 0.2996 |
| validation | `current_svc_numeric_seed_mean_min5` | 0.1272 | 0.2176 | 0.6504 | 0.3367 |
| validation | `current_70_30_min5_svc_ppv8` | 0.1305 | 0.2110 | 0.6580 | 0.3292 |
| validation | `pp_v8_compact_blend_mape_guarded` | 0.1544 | 0.2544 | 0.8084 | 0.3721 |

## 4. Validation bootstrap

| baseline | 후보 | mode | MdAPE 개선확률 | MAPE 개선확률 | p95 개선확률 | MdAPE delta 중앙값 |
|---|---|---|---:|---:|---:|---:|
| `current_70_30_min5_svc_ppv8` | `wmin2_70_30_min1_svc_ppv8` | artist_bootstrap | 0.998 | 1.000 | 0.968 | 0.0230 |
| `current_70_30_min5_svc_ppv8` | `wmin2_70_30_min1_svc_ppv8` | row_bootstrap | 0.996 | 1.000 | 0.966 | 0.0223 |
| `current_svc_numeric_seed_mean_min5` | `wmin2_svc_numeric_seed_mean_min1` | artist_bootstrap | 1.000 | 1.000 | 0.864 | 0.0320 |
| `current_svc_numeric_seed_mean_min5` | `wmin2_svc_numeric_seed_mean_min1` | row_bootstrap | 1.000 | 0.996 | 0.864 | 0.0315 |

## 5. 누수 방어 audit

- source/holdout row id 중복 합계: `0`
- train 피처는 5-fold cross-fit으로 생성되므로 holdout row의 가격은 해당 row의 비교군 통계 계산에 들어가지 않는다.
- fold 제외 후 작가 포함 ladder의 source count가 0이면 다음 ladder로 fallback한다.

| artist ladder level | fold 제외 후 source 0건 fallback 필요 row 합계 |
|---|---:|
| `artist` | 3496 |
| `artist_medium_support_size` | 32842 |
| `artist_size` | 18422 |

## 6. Coverage

| split | column | value | rows | share | median group N |
|---|---|---|---:|---:|---:|
| train_oof_seed0 | svc_group_level | `artist` | 1497 | 0.056 | 4.0 |
| train_oof_seed0 | svc_group_level | `artist_medium_support_size` | 23645 | 0.879 | 8.0 |
| train_oof_seed0 | svc_group_level | `artist_size` | 1397 | 0.052 | 3.0 |
| train_oof_seed0 | svc_group_level | `global` | 19 | 0.001 | 21531.0 |
| train_oof_seed0 | svc_group_level | `medium_size` | 38 | 0.001 | 684.0 |
| train_oof_seed0 | svc_group_level | `medium_support_size` | 318 | 0.012 | 771.5 |
| train_oof_seed0 | svc_coverage_tier | `fallback_global` | 19 | 0.001 | 21531.0 |
| train_oof_seed0 | svc_coverage_tier | `high_n` | 2815 | 0.105 | 75.0 |
| train_oof_seed0 | svc_coverage_tier | `low_n` | 18163 | 0.675 | 4.0 |
| train_oof_seed0 | svc_coverage_tier | `medium_n` | 5917 | 0.220 | 24.0 |
| validation | svc_group_level | `artist` | 30 | 0.058 | 7.0 |
| validation | svc_group_level | `artist_medium_support_size` | 450 | 0.867 | 4.0 |
| validation | svc_group_level | `artist_size` | 39 | 0.075 | 2.0 |
| validation | svc_coverage_tier | `high_n` | 4 | 0.008 | 54.0 |
| validation | svc_coverage_tier | `low_n` | 470 | 0.906 | 4.0 |
| validation | svc_coverage_tier | `medium_n` | 45 | 0.087 | 21.0 |
| test | svc_group_level | `artist` | 59 | 0.097 | 6.0 |
| test | svc_group_level | `artist_medium_support_size` | 497 | 0.819 | 4.0 |
| test | svc_group_level | `artist_size` | 51 | 0.084 | 2.0 |
| test | svc_coverage_tier | `high_n` | 9 | 0.015 | 80.0 |
| test | svc_coverage_tier | `low_n` | 542 | 0.893 | 4.0 |
| test | svc_coverage_tier | `medium_n` | 56 | 0.092 | 24.0 |

## 7. 다음 판단

- validation에서 SVC 단독과 70:30 모두 개선되고 bootstrap 개선확률이 높으면 PP-WMIN3에서 기존 보정 stack과 결합해 확인한다.
- SVC 단독은 개선되지만 70:30에서 사라지면 PP-V8과의 결합 비율 또는 보정 stack에서 신호가 희석되는지 분해한다.
- validation에서 불안정하면 fixed test 개선이 있어도 채택하지 않고 slice별 원인을 분해한다.
