# PP-HCOEF26 Warm Huber low-risk 적용/p95 fallback 실험

- 작성일: 2026-06-08 05:28
- 목적: HCOEF25 MAPE 개선 후보를 전체에 적용하지 않고, 위험이 낮은 구간에만 제한 적용했을 때 p95를 방어할 수 있는지 검증.
- 현재 기준 후보: `hcoef_stable`.
- 최소 비교 기준: `current_70_30`.
- 선택 원칙: HCOEF25 source 후보는 validation OOF 기준으로 고르고, fixed test/0604 residual은 경계값 선택에 사용하지 않음.

## 1. 실행 결론

- 상위 후보: `hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1` (판단: MAPE 특화 후보, fixed test MdAPE/MAPE/p95 `0.1371/0.2727/0.8064`).
- 현재 기준 fixed test: MdAPE `0.1388`, MAPE `0.2730`, p95 `0.8064`, RMSE_log `0.3988`.
- 최소 비교 기준 fixed test: MdAPE `0.1405`, MAPE `0.2748`, p95 `0.8331`, RMSE_log `0.3996`.
- HCOEF26은 새 기준가를 test에 맞춰 만들지 않고, HCOEF25 후보 이동분을 사전에 정의한 안전 구간에만 적용한 실험임.

## 2. 사용한 HCOEF25 source 후보

| source_candidate |
| --- |
| hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 |
| hcoef25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5 |
| hcoef25_direct_huber_guarded_loose_a0p01_cap0p02_s0p5 |
| hcoef25_direct_huber_guarded_default_a0p01_cap0p03_s0p5 |
| hcoef25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5 |
| hcoef25_direct_huber_guarded_strict_a0p01_cap0p04_s0p5 |
| hcoef25_resid_huber_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25 |
| hcoef25_resid_huber_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25 |
| hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p03_s0p25 |
| hcoef25_resid_huber_strict_conservative_guard_core_a0p01_cap0p03_s0p25 |
| hcoef25_direct_huber_guarded_loose_a0p01_cap0p03_s0p5 |
| hcoef25_resid_huber_loose_conservative_guard_core_a0p001_cap0p03_s0p25 |
| hcoef25_resid_huber_loose_conservative_guard_core_a0p01_cap0p03_s0p25 |
| hcoef25_resid_huber_default_conservative_guard_core_a0p001_cap0p03_s0p25 |

## 3. 후보 선택표

| candidate | decision | row_oof_MdAPE | row_oof_MAPE | row_oof_p95_APE | artist_oof_MdAPE | artist_oof_MAPE | artist_oof_p95_APE | test_MdAPE | test_MAPE | test_p95_APE | stress0604_MdAPE | stress0604_MAPE | stress0604_p95_APE | bootstrap_all3_gate | fixed_test_p95_guard | stress0604_p95_guard |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef_stable | 현재 기준 후보 | 0.1260 | 0.2082 | 0.6479 | 0.1260 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6425 | 0.1260 | 0.2082 | 0.6416 | 0.1371 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6425 | 0.1260 | 0.2082 | 0.6416 | 0.1371 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6425 | 0.1260 | 0.2082 | 0.6416 | 0.1371 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_nocap_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6425 | 0.1260 | 0.2082 | 0.6416 | 0.1371 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6453 | 0.1260 | 0.2082 | 0.6453 | 0.1371 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6453 | 0.1260 | 0.2082 | 0.6453 | 0.1371 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6425 | 0.1260 | 0.2082 | 0.6416 | 0.1371 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6425 | 0.1260 | 0.2082 | 0.6416 | 0.1371 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6425 | 0.1260 | 0.2082 | 0.6416 | 0.1371 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6425 | 0.1260 | 0.2082 | 0.6416 | 0.1371 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6453 | 0.1260 | 0.2082 | 0.6453 | 0.1371 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6453 | 0.1260 | 0.2082 | 0.6453 | 0.1371 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6425 | 0.1260 | 0.2082 | 0.6416 | 0.1372 | 0.2726 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_nocap_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6425 | 0.1260 | 0.2082 | 0.6416 | 0.1372 | 0.2726 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6425 | 0.1260 | 0.2082 | 0.6416 | 0.1372 | 0.2726 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6425 | 0.1260 | 0.2082 | 0.6416 | 0.1372 | 0.2726 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6425 | 0.1260 | 0.2082 | 0.6416 | 0.1372 | 0.2726 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6425 | 0.1260 | 0.2082 | 0.6416 | 0.1372 | 0.2726 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6425 | 0.1260 | 0.2082 | 0.6416 | 0.1372 | 0.2726 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6425 | 0.1260 | 0.2082 | 0.6416 | 0.1372 | 0.2726 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6453 | 0.1260 | 0.2082 | 0.6453 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6453 | 0.1260 | 0.2082 | 0.6453 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6453 | 0.1260 | 0.2082 | 0.6453 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6453 | 0.1260 | 0.2082 | 0.6453 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p005_s0p75 | MAPE 특화 후보 | 0.1256 | 0.2082 | 0.6471 | 0.1256 | 0.2082 | 0.6471 | 0.1372 | 0.2728 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p005_s0p75 | MAPE 특화 후보 | 0.1256 | 0.2082 | 0.6471 | 0.1256 | 0.2082 | 0.6471 | 0.1372 | 0.2728 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p005_s0p75 | MAPE 특화 후보 | 0.1256 | 0.2082 | 0.6471 | 0.1256 | 0.2082 | 0.6471 | 0.1372 | 0.2728 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p005_s0p75 | MAPE 특화 후보 | 0.1256 | 0.2082 | 0.6471 | 0.1256 | 0.2082 | 0.6471 | 0.1372 | 0.2728 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0025_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6479 | 0.1260 | 0.2082 | 0.6479 | 0.1372 | 0.2728 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0025_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6479 | 0.1260 | 0.2082 | 0.6479 | 0.1372 | 0.2728 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0025_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6479 | 0.1260 | 0.2082 | 0.6479 | 0.1372 | 0.2728 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0025_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6479 | 0.1260 | 0.2082 | 0.6479 | 0.1372 | 0.2728 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0025_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6479 | 0.1260 | 0.2082 | 0.6479 | 0.1372 | 0.2729 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0025_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6479 | 0.1260 | 0.2082 | 0.6479 | 0.1372 | 0.2729 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_no_extreme_reliable_cap0p0025_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6479 | 0.1260 | 0.2082 | 0.6479 | 0.1372 | 0.2729 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_no_extreme_reliable_cap0p005_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6479 | 0.1260 | 0.2082 | 0.6479 | 0.1372 | 0.2729 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_no_extreme_reliable_cap0p0075_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6479 | 0.1260 | 0.2082 | 0.6479 | 0.1372 | 0.2729 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_no_extreme_reliable_nocap_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6479 | 0.1260 | 0.2082 | 0.6479 | 0.1372 | 0.2729 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | False | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_p95_defense_core_cap0p0025_s1 | MAPE 특화 후보 | 0.1260 | 0.2082 | 0.6479 | 0.1260 | 0.2082 | 0.6479 | 0.1372 | 0.2729 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | False | True | True |

## 4. Validation OOF 상위 후보

### Row OOF

| candidate | method | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable | mask_applied_share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p04_s0p5_confidence_medium_plus_nocap_s1 | gated_h25_candidate | 0.1235 | 0.2081 | 0.6479 | 0.3250 | -0.0025 | -0.0001 | 0.0000 | 0.2543 |
| hcoef26_h25_direct_huber_guarded_loose_a0p01_cap0p03_s0p5_confidence_medium_plus_nocap_s1 | gated_h25_candidate | 0.1235 | 0.2083 | 0.6479 | 0.3251 | -0.0024 | 0.0001 | 0.0000 | 0.2543 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_confidence_medium_plus_nocap_s1 | gated_h25_candidate | 0.1245 | 0.2081 | 0.6479 | 0.3250 | -0.0015 | -0.0001 | 0.0000 | 0.2543 |
| hcoef26_h25_direct_huber_guarded_default_a0p01_cap0p03_s0p5_confidence_medium_plus_nocap_s1 | gated_h25_candidate | 0.1245 | 0.2082 | 0.6479 | 0.3251 | -0.0015 | -0.0001 | 0.0000 | 0.2543 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_confidence_medium_plus_nocap_s0p75 | gated_h25_candidate | 0.1247 | 0.2081 | 0.6479 | 0.3250 | -0.0013 | -0.0001 | 0.0000 | 0.2543 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5_confidence_medium_plus_nocap_s1 | gated_h25_candidate | 0.1247 | 0.2081 | 0.6479 | 0.3251 | -0.0013 | -0.0001 | 0.0000 | 0.2543 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p04_s0p5_confidence_medium_plus_nocap_s0p75 | gated_h25_candidate | 0.1247 | 0.2081 | 0.6479 | 0.3250 | -0.0013 | -0.0001 | 0.0000 | 0.2543 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_confidence_medium_plus_nocap_s0p5 | gated_h25_candidate | 0.1247 | 0.2081 | 0.6479 | 0.3251 | -0.0013 | -0.0001 | 0.0000 | 0.2543 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p04_s0p5_confidence_medium_plus_nocap_s0p5 | gated_h25_candidate | 0.1247 | 0.2081 | 0.6479 | 0.3251 | -0.0013 | -0.0001 | 0.0000 | 0.2543 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5_confidence_medium_plus_nocap_s0p75 | gated_h25_candidate | 0.1247 | 0.2081 | 0.6479 | 0.3251 | -0.0013 | -0.0001 | 0.0000 | 0.2543 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_confidence_medium_plus_cap0p0075_s1 | gated_h25_candidate | 0.1247 | 0.2081 | 0.6479 | 0.3251 | -0.0013 | -0.0001 | 0.0000 | 0.2543 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5_confidence_medium_plus_cap0p0075_s1 | gated_h25_candidate | 0.1247 | 0.2081 | 0.6479 | 0.3251 | -0.0013 | -0.0001 | 0.0000 | 0.2543 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p04_s0p5_confidence_medium_plus_cap0p0075_s1 | gated_h25_candidate | 0.1247 | 0.2081 | 0.6479 | 0.3251 | -0.0013 | -0.0001 | 0.0000 | 0.2543 |
| hcoef26_h25_direct_huber_guarded_default_a0p01_cap0p03_s0p5_confidence_medium_plus_nocap_s0p75 | gated_h25_candidate | 0.1247 | 0.2081 | 0.6479 | 0.3251 | -0.0013 | -0.0001 | 0.0000 | 0.2543 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_nocap_s1 | gated_h25_candidate | 0.1247 | 0.2081 | 0.6471 | 0.3250 | -0.0013 | -0.0001 | -0.0008 | 0.2775 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_p95_defense_core_nocap_s1 | gated_h25_candidate | 0.1247 | 0.2081 | 0.6471 | 0.3250 | -0.0013 | -0.0001 | -0.0008 | 0.2775 |
| hcoef26_h25_direct_huber_guarded_default_a0p01_cap0p03_s0p5_confidence_medium_plus_cap0p0075_s1 | gated_h25_candidate | 0.1247 | 0.2082 | 0.6479 | 0.3251 | -0.0013 | -0.0000 | 0.0000 | 0.2543 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_qwidth_gap_safe_nocap_s1 | gated_h25_candidate | 0.1247 | 0.2082 | 0.6479 | 0.3250 | -0.0013 | -0.0000 | 0.0000 | 0.2062 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p04_s0p5_no_extreme_reliable_nocap_s1 | gated_h25_candidate | 0.1247 | 0.2082 | 0.6471 | 0.3250 | -0.0013 | 0.0000 | -0.0008 | 0.2775 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p04_s0p5_p95_defense_core_nocap_s1 | gated_h25_candidate | 0.1247 | 0.2082 | 0.6471 | 0.3250 | -0.0013 | 0.0000 | -0.0008 | 0.2775 |
| hcoef26_h25_direct_huber_guarded_loose_a0p01_cap0p02_s0p5_confidence_medium_plus_nocap_s0p75 | gated_h25_candidate | 0.1247 | 0.2082 | 0.6479 | 0.3251 | -0.0013 | 0.0000 | 0.0000 | 0.2543 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p04_s0p5_qwidth_gap_safe_nocap_s1 | gated_h25_candidate | 0.1247 | 0.2082 | 0.6479 | 0.3249 | -0.0013 | 0.0000 | 0.0000 | 0.2062 |
| hcoef26_h25_direct_huber_guarded_loose_a0p01_cap0p02_s0p5_confidence_medium_plus_cap0p0075_s1 | gated_h25_candidate | 0.1247 | 0.2083 | 0.6479 | 0.3251 | -0.0013 | 0.0000 | 0.0000 | 0.2543 |
| hcoef26_h25_direct_huber_guarded_loose_a0p01_cap0p03_s0p5_confidence_medium_plus_cap0p0075_s1 | gated_h25_candidate | 0.1247 | 0.2083 | 0.6479 | 0.3251 | -0.0013 | 0.0000 | 0.0000 | 0.2543 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_reliable_lowrisk_nocap_s1 | gated_h25_candidate | 0.1247 | 0.2083 | 0.6479 | 0.3251 | -0.0013 | 0.0001 | 0.0000 | 0.0867 |

### Artist OOF

| candidate | method | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable | mask_applied_share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef26_h25_direct_huber_guarded_default_a0p01_cap0p03_s0p5_confidence_medium_plus_nocap_s1 | gated_h25_candidate | 0.1245 | 0.2082 | 0.6479 | 0.3251 | -0.0015 | -0.0000 | 0.0000 | 0.2543 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_confidence_medium_plus_nocap_s1 | gated_h25_candidate | 0.1247 | 0.2080 | 0.6479 | 0.3250 | -0.0013 | -0.0002 | 0.0000 | 0.2543 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p04_s0p5_confidence_medium_plus_nocap_s1 | gated_h25_candidate | 0.1247 | 0.2080 | 0.6479 | 0.3250 | -0.0013 | -0.0002 | 0.0000 | 0.2543 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_confidence_medium_plus_cap0p0075_s1 | gated_h25_candidate | 0.1247 | 0.2081 | 0.6479 | 0.3251 | -0.0013 | -0.0001 | 0.0000 | 0.2543 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5_confidence_medium_plus_cap0p0075_s1 | gated_h25_candidate | 0.1247 | 0.2081 | 0.6479 | 0.3251 | -0.0013 | -0.0001 | 0.0000 | 0.2543 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p04_s0p5_confidence_medium_plus_cap0p0075_s1 | gated_h25_candidate | 0.1247 | 0.2081 | 0.6479 | 0.3251 | -0.0013 | -0.0001 | 0.0000 | 0.2543 |
| hcoef26_h25_direct_huber_guarded_default_a0p01_cap0p03_s0p5_confidence_medium_plus_cap0p0075_s1 | gated_h25_candidate | 0.1247 | 0.2082 | 0.6479 | 0.3251 | -0.0013 | -0.0001 | 0.0000 | 0.2543 |
| hcoef26_h25_direct_huber_guarded_default_a0p01_cap0p03_s0p5_qwidth_gap_safe_nocap_s1 | gated_h25_candidate | 0.1247 | 0.2082 | 0.6479 | 0.3249 | -0.0013 | -0.0000 | 0.0000 | 0.2062 |
| hcoef26_h25_direct_huber_guarded_default_a0p01_cap0p03_s0p5_confidence_medium_plus_nocap_s0p75 | gated_h25_candidate | 0.1250 | 0.2082 | 0.6479 | 0.3251 | -0.0010 | -0.0001 | 0.0000 | 0.2543 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p04_s0p5_qwidth_gap_safe_nocap_s1 | gated_h25_candidate | 0.1250 | 0.2080 | 0.6479 | 0.3248 | -0.0009 | -0.0002 | 0.0000 | 0.2062 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_qwidth_gap_safe_nocap_s1 | gated_h25_candidate | 0.1250 | 0.2080 | 0.6479 | 0.3248 | -0.0009 | -0.0002 | 0.0000 | 0.2062 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5_confidence_medium_plus_nocap_s1 | gated_h25_candidate | 0.1250 | 0.2080 | 0.6479 | 0.3251 | -0.0009 | -0.0002 | 0.0000 | 0.2543 |
| hcoef26_h25_direct_huber_guarded_default_a0p01_cap0p03_s0p5_no_extreme_reliable_nocap_s1 | gated_h25_candidate | 0.1253 | 0.2083 | 0.6398 | 0.3251 | -0.0007 | 0.0000 | -0.0081 | 0.2775 |
| hcoef26_h25_direct_huber_guarded_default_a0p01_cap0p03_s0p5_p95_defense_core_nocap_s1 | gated_h25_candidate | 0.1253 | 0.2083 | 0.6398 | 0.3251 | -0.0007 | 0.0000 | -0.0081 | 0.2775 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_nocap_s1 | gated_h25_candidate | 0.1253 | 0.2080 | 0.6397 | 0.3249 | -0.0007 | -0.0002 | -0.0083 | 0.2775 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_p95_defense_core_nocap_s1 | gated_h25_candidate | 0.1253 | 0.2080 | 0.6397 | 0.3249 | -0.0007 | -0.0002 | -0.0083 | 0.2775 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p04_s0p5_no_extreme_reliable_nocap_s1 | gated_h25_candidate | 0.1253 | 0.2081 | 0.6397 | 0.3249 | -0.0007 | -0.0001 | -0.0083 | 0.2775 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p04_s0p5_p95_defense_core_nocap_s1 | gated_h25_candidate | 0.1253 | 0.2081 | 0.6397 | 0.3249 | -0.0007 | -0.0001 | -0.0083 | 0.2775 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_confidence_medium_plus_nocap_s0p75 | gated_h25_candidate | 0.1253 | 0.2080 | 0.6479 | 0.3250 | -0.0006 | -0.0002 | 0.0000 | 0.2543 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p04_s0p5_confidence_medium_plus_nocap_s0p75 | gated_h25_candidate | 0.1253 | 0.2080 | 0.6479 | 0.3250 | -0.0006 | -0.0002 | 0.0000 | 0.2543 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5_qwidth_gap_safe_nocap_s1 | gated_h25_candidate | 0.1253 | 0.2080 | 0.6479 | 0.3250 | -0.0006 | -0.0002 | 0.0000 | 0.2062 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p04_s0p5_confidence_medium_plus_nocap_s0p5 | gated_h25_candidate | 0.1253 | 0.2080 | 0.6479 | 0.3250 | -0.0006 | -0.0002 | 0.0000 | 0.2543 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5_no_extreme_reliable_nocap_s1 | gated_h25_candidate | 0.1253 | 0.2080 | 0.6397 | 0.3250 | -0.0006 | -0.0002 | -0.0083 | 0.2775 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5_p95_defense_core_nocap_s1 | gated_h25_candidate | 0.1253 | 0.2080 | 0.6397 | 0.3250 | -0.0006 | -0.0002 | -0.0083 | 0.2775 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_confidence_medium_plus_nocap_s0p5 | gated_h25_candidate | 0.1253 | 0.2081 | 0.6479 | 0.3251 | -0.0006 | -0.0002 | 0.0000 | 0.2543 |

## 5. Fixed Test 상위 후보

| candidate | method | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable | mask_applied_share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gated_h25_candidate | 0.1371 | 0.2727 | 0.8064 | 0.3987 | -0.0017 | -0.0003 | 0.0000 | 0.3031 |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gated_h25_candidate | 0.1371 | 0.2727 | 0.8064 | 0.3987 | -0.0017 | -0.0003 | 0.0000 | 0.3031 |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_nocap_s1 | gated_h25_candidate | 0.1371 | 0.2727 | 0.8064 | 0.3987 | -0.0017 | -0.0003 | 0.0000 | 0.3031 |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gated_h25_candidate | 0.1371 | 0.2727 | 0.8064 | 0.3987 | -0.0017 | -0.0003 | 0.0000 | 0.3031 |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | gated_h25_candidate | 0.1371 | 0.2727 | 0.8064 | 0.3987 | -0.0017 | -0.0003 | 0.0000 | 0.3031 |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | gated_h25_candidate | 0.1371 | 0.2727 | 0.8064 | 0.3987 | -0.0017 | -0.0003 | 0.0000 | 0.3031 |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gated_h25_candidate | 0.1371 | 0.2727 | 0.8064 | 0.3987 | -0.0017 | -0.0003 | 0.0000 | 0.3031 |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gated_h25_candidate | 0.1371 | 0.2727 | 0.8064 | 0.3987 | -0.0017 | -0.0003 | 0.0000 | 0.3031 |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | gated_h25_candidate | 0.1371 | 0.2727 | 0.8064 | 0.3987 | -0.0017 | -0.0003 | 0.0000 | 0.3031 |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gated_h25_candidate | 0.1371 | 0.2727 | 0.8064 | 0.3987 | -0.0017 | -0.0003 | 0.0000 | 0.3031 |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | gated_h25_candidate | 0.1371 | 0.2727 | 0.8064 | 0.3987 | -0.0017 | -0.0003 | 0.0000 | 0.3031 |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | gated_h25_candidate | 0.1371 | 0.2727 | 0.8064 | 0.3987 | -0.0017 | -0.0003 | 0.0000 | 0.3031 |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gated_h25_candidate | 0.1372 | 0.2726 | 0.8064 | 0.3987 | -0.0016 | -0.0004 | 0.0000 | 0.3031 |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_nocap_s1 | gated_h25_candidate | 0.1372 | 0.2726 | 0.8064 | 0.3987 | -0.0016 | -0.0004 | 0.0000 | 0.3031 |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gated_h25_candidate | 0.1372 | 0.2726 | 0.8064 | 0.3987 | -0.0016 | -0.0004 | 0.0000 | 0.3031 |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gated_h25_candidate | 0.1372 | 0.2726 | 0.8064 | 0.3987 | -0.0016 | -0.0004 | 0.0000 | 0.3031 |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gated_h25_candidate | 0.1372 | 0.2726 | 0.8064 | 0.3987 | -0.0016 | -0.0004 | 0.0000 | 0.3031 |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gated_h25_candidate | 0.1372 | 0.2726 | 0.8064 | 0.3987 | -0.0016 | -0.0004 | 0.0000 | 0.3031 |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | gated_h25_candidate | 0.1372 | 0.2726 | 0.8064 | 0.3987 | -0.0016 | -0.0004 | 0.0000 | 0.3031 |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gated_h25_candidate | 0.1372 | 0.2726 | 0.8064 | 0.3987 | -0.0016 | -0.0004 | 0.0000 | 0.3031 |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | gated_h25_candidate | 0.1372 | 0.2727 | 0.8064 | 0.3987 | -0.0016 | -0.0003 | 0.0000 | 0.3031 |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | gated_h25_candidate | 0.1372 | 0.2727 | 0.8064 | 0.3987 | -0.0016 | -0.0003 | 0.0000 | 0.3031 |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | gated_h25_candidate | 0.1372 | 0.2727 | 0.8064 | 0.3987 | -0.0016 | -0.0003 | 0.0000 | 0.3031 |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | gated_h25_candidate | 0.1372 | 0.2727 | 0.8064 | 0.3987 | -0.0016 | -0.0003 | 0.0000 | 0.3031 |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p005_s0p75 | gated_h25_candidate | 0.1372 | 0.2728 | 0.8064 | 0.3988 | -0.0016 | -0.0002 | 0.0000 | 0.3031 |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p005_s0p75 | gated_h25_candidate | 0.1372 | 0.2728 | 0.8064 | 0.3988 | -0.0016 | -0.0002 | 0.0000 | 0.3031 |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p005_s0p75 | gated_h25_candidate | 0.1372 | 0.2728 | 0.8064 | 0.3988 | -0.0016 | -0.0002 | 0.0000 | 0.3031 |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p005_s0p75 | gated_h25_candidate | 0.1372 | 0.2728 | 0.8064 | 0.3988 | -0.0016 | -0.0002 | 0.0000 | 0.3031 |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0025_s1 | gated_h25_candidate | 0.1372 | 0.2728 | 0.8064 | 0.3988 | -0.0016 | -0.0001 | 0.0000 | 0.3031 |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0025_s1 | gated_h25_candidate | 0.1372 | 0.2728 | 0.8064 | 0.3988 | -0.0016 | -0.0001 | 0.0000 | 0.3031 |

## 6. 0604 Stress Test 상위 후보

| candidate | method | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable | mask_applied_share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppv8_service_proxy | source | 0.2298 | 0.3359 | 0.9273 | 0.7124 | -0.0433 | -0.0385 | -0.0561 | 1.0000 |
| hcoef_stable | source | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| hcoef26_h25_direct_huber_guarded_default_a0p01_cap0p03_s0p5_reliable_lowrisk_cap0p0025_s0p25 | gated_h25_candidate | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | 0.0374 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_reliable_lowrisk_cap0p0025_s0p25 | gated_h25_candidate | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | 0.0374 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5_reliable_lowrisk_cap0p0025_s0p25 | gated_h25_candidate | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | 0.0374 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p04_s0p5_reliable_lowrisk_cap0p0025_s0p25 | gated_h25_candidate | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | 0.0374 |
| hcoef26_h25_direct_huber_guarded_loose_a0p01_cap0p02_s0p5_reliable_lowrisk_cap0p0025_s0p25 | gated_h25_candidate | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | 0.0374 |
| hcoef26_h25_direct_huber_guarded_loose_a0p01_cap0p03_s0p5_reliable_lowrisk_cap0p0025_s0p25 | gated_h25_candidate | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | 0.0374 |
| hcoef26_h25_direct_huber_guarded_default_a0p01_cap0p03_s0p5_reliable_lowrisk_cap0p0025_s0p5 | gated_h25_candidate | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | 0.0374 |
| hcoef26_h25_direct_huber_guarded_default_a0p01_cap0p03_s0p5_reliable_lowrisk_cap0p005_s0p25 | gated_h25_candidate | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | 0.0374 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_reliable_lowrisk_cap0p0025_s0p5 | gated_h25_candidate | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | 0.0374 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5_reliable_lowrisk_cap0p0025_s0p5 | gated_h25_candidate | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | 0.0374 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p04_s0p5_reliable_lowrisk_cap0p0025_s0p5 | gated_h25_candidate | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | 0.0374 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_reliable_lowrisk_cap0p005_s0p25 | gated_h25_candidate | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | 0.0374 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5_reliable_lowrisk_cap0p005_s0p25 | gated_h25_candidate | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | 0.0374 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p04_s0p5_reliable_lowrisk_cap0p005_s0p25 | gated_h25_candidate | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | 0.0374 |
| hcoef26_h25_direct_huber_guarded_loose_a0p01_cap0p02_s0p5_reliable_lowrisk_cap0p005_s0p25 | gated_h25_candidate | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | 0.0374 |
| hcoef26_h25_direct_huber_guarded_loose_a0p01_cap0p03_s0p5_reliable_lowrisk_cap0p005_s0p25 | gated_h25_candidate | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | 0.0374 |
| hcoef26_h25_direct_huber_guarded_loose_a0p01_cap0p02_s0p5_reliable_lowrisk_cap0p0025_s0p5 | gated_h25_candidate | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | 0.0374 |
| hcoef26_h25_direct_huber_guarded_loose_a0p01_cap0p03_s0p5_reliable_lowrisk_cap0p0025_s0p5 | gated_h25_candidate | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | 0.0374 |
| hcoef26_h25_direct_huber_guarded_default_a0p01_cap0p03_s0p5_reliable_lowrisk_cap0p0025_s0p75 | gated_h25_candidate | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | 0.0374 |
| hcoef26_h25_rh_loose_conservative_guard_core_a0p001_cap0p03_s0p25_reliable_lowrisk_cap0p0025_s0p25 | gated_h25_candidate | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | 0.0374 |
| hcoef26_h25_rh_loose_conservative_guard_core_a0p01_cap0p03_s0p25_reliable_lowrisk_cap0p0025_s0p25 | gated_h25_candidate | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | 0.0374 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_reliable_lowrisk_cap0p0025_s0p75 | gated_h25_candidate | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | 0.0374 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5_reliable_lowrisk_cap0p0025_s0p75 | gated_h25_candidate | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | 0.0374 |

## 7. 적용 구간 coverage

| scope | mask_name | rows | covered_rows | covered_share |
| --- | --- | --- | --- | --- |
| 0604_stress | hard_risk_fallback | 829 | 265 | 0.3197 |
| 0604_stress | lowrisk_only | 829 | 57 | 0.0688 |
| 0604_stress | reliable_lowrisk | 829 | 31 | 0.0374 |
| 0604_stress | no_extreme_reliable | 829 | 128 | 0.1544 |
| 0604_stress | confidence_medium_plus | 829 | 128 | 0.1544 |
| 0604_stress | qwidth_gap_safe | 829 | 86 | 0.1037 |
| 0604_stress | p95_defense_core | 829 | 128 | 0.1544 |
| fixed_confirmation | hard_risk_fallback | 607 | 371 | 0.6112 |
| fixed_confirmation | lowrisk_only | 607 | 75 | 0.1236 |
| fixed_confirmation | reliable_lowrisk | 607 | 62 | 0.1021 |
| fixed_confirmation | no_extreme_reliable | 607 | 184 | 0.3031 |
| fixed_confirmation | confidence_medium_plus | 607 | 165 | 0.2718 |
| fixed_confirmation | qwidth_gap_safe | 607 | 127 | 0.2092 |
| fixed_confirmation | p95_defense_core | 607 | 184 | 0.3031 |
| validation_oof_artist | hard_risk_fallback | 519 | 328 | 0.6320 |
| validation_oof_artist | lowrisk_only | 519 | 50 | 0.0963 |
| validation_oof_artist | reliable_lowrisk | 519 | 45 | 0.0867 |
| validation_oof_artist | no_extreme_reliable | 519 | 144 | 0.2775 |
| validation_oof_artist | confidence_medium_plus | 519 | 132 | 0.2543 |
| validation_oof_artist | qwidth_gap_safe | 519 | 107 | 0.2062 |
| validation_oof_artist | p95_defense_core | 519 | 144 | 0.2775 |
| validation_oof_row | hard_risk_fallback | 519 | 328 | 0.6320 |
| validation_oof_row | lowrisk_only | 519 | 50 | 0.0963 |
| validation_oof_row | reliable_lowrisk | 519 | 45 | 0.0867 |
| validation_oof_row | no_extreme_reliable | 519 | 144 | 0.2775 |
| validation_oof_row | confidence_medium_plus | 519 | 132 | 0.2543 |
| validation_oof_row | qwidth_gap_safe | 519 | 107 | 0.2062 |
| validation_oof_row | p95_defense_core | 519 | 144 | 0.2775 |

## 8. 계수/정책 해석

- `source_candidate`: HCOEF25에서 가져온 평균오차 개선 후보.
- `mask_*`: 해당 후보를 실제로 적용할 수 있는 구간. 조건을 만족하지 않으면 `hcoef_stable`로 fallback.
- `strength`: HCOEF25 후보 이동분을 얼마나 반영할지 정한 가중치.
- `cap`: 한 작품에서 허용하는 최대 로그 이동폭. cap이 작을수록 p95 방어에 유리하지만 개선폭은 작아짐.

| candidate | method | feature | coefficient_or_weight | cap | mask_name | direction | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef_stable | source | hcoef_stable | 1.0000 |  | all | source prediction move applied where mask=1 | 현재 HCOEF 안정 후보 |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25 | 1.0000 |  | no_extreme_reliable | source prediction move applied where mask=1 | 극단 위험 구간을 제외하고 표본 수 10개 이상인 구간에만 적용 |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gated_h25_candidate | mask_no_extreme_reliable | 1.0000 |  | no_extreme_reliable | enables_or_blocks_candidate_move | 이 조건을 만족한 행에만 HCOEF25 후보와 hcoef_stable의 차이를 적용한다. |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25 | 1.0000 | 0.0075 | no_extreme_reliable | source prediction move applied where mask=1 | 극단 위험 구간을 제외하고 표본 수 10개 이상인 구간에만 적용 |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gated_h25_candidate | mask_no_extreme_reliable | 1.0000 |  | no_extreme_reliable | enables_or_blocks_candidate_move | 이 조건을 만족한 행에만 HCOEF25 후보와 hcoef_stable의 차이를 적용한다. |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25 | 1.0000 | 0.0075 | p95_defense_core | source prediction move applied where mask=1 | p95 방어용 핵심 안전 구간에만 적용 |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gated_h25_candidate | mask_p95_defense_core | 1.0000 |  | p95_defense_core | enables_or_blocks_candidate_move | 이 조건을 만족한 행에만 HCOEF25 후보와 hcoef_stable의 차이를 적용한다. |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25 | 1.0000 |  | no_extreme_reliable | source prediction move applied where mask=1 | 극단 위험 구간을 제외하고 표본 수 10개 이상인 구간에만 적용 |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gated_h25_candidate | mask_no_extreme_reliable | 1.0000 |  | no_extreme_reliable | enables_or_blocks_candidate_move | 이 조건을 만족한 행에만 HCOEF25 후보와 hcoef_stable의 차이를 적용한다. |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25 | 1.0000 | 0.0075 | no_extreme_reliable | source prediction move applied where mask=1 | 극단 위험 구간을 제외하고 표본 수 10개 이상인 구간에만 적용 |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gated_h25_candidate | mask_no_extreme_reliable | 1.0000 |  | no_extreme_reliable | enables_or_blocks_candidate_move | 이 조건을 만족한 행에만 HCOEF25 후보와 hcoef_stable의 차이를 적용한다. |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_nocap_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25 | 1.0000 |  | p95_defense_core | source prediction move applied where mask=1 | p95 방어용 핵심 안전 구간에만 적용 |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_nocap_s1 | gated_h25_candidate | mask_p95_defense_core | 1.0000 |  | p95_defense_core | enables_or_blocks_candidate_move | 이 조건을 만족한 행에만 HCOEF25 후보와 hcoef_stable의 차이를 적용한다. |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25 | 1.0000 | 0.0075 | p95_defense_core | source prediction move applied where mask=1 | p95 방어용 핵심 안전 구간에만 적용 |
| hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gated_h25_candidate | mask_p95_defense_core | 1.0000 |  | p95_defense_core | enables_or_blocks_candidate_move | 이 조건을 만족한 행에만 HCOEF25 후보와 hcoef_stable의 차이를 적용한다. |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p03_s0p25 | 1.0000 |  | no_extreme_reliable | source prediction move applied where mask=1 | 극단 위험 구간을 제외하고 표본 수 10개 이상인 구간에만 적용 |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gated_h25_candidate | mask_no_extreme_reliable | 1.0000 |  | no_extreme_reliable | enables_or_blocks_candidate_move | 이 조건을 만족한 행에만 HCOEF25 후보와 hcoef_stable의 차이를 적용한다. |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p03_s0p25 | 1.0000 | 0.0050 | no_extreme_reliable | source prediction move applied where mask=1 | 극단 위험 구간을 제외하고 표본 수 10개 이상인 구간에만 적용 |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | gated_h25_candidate | mask_no_extreme_reliable | 1.0000 |  | no_extreme_reliable | enables_or_blocks_candidate_move | 이 조건을 만족한 행에만 HCOEF25 후보와 hcoef_stable의 차이를 적용한다. |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p03_s0p25 | 1.0000 | 0.0075 | no_extreme_reliable | source prediction move applied where mask=1 | 극단 위험 구간을 제외하고 표본 수 10개 이상인 구간에만 적용 |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gated_h25_candidate | mask_no_extreme_reliable | 1.0000 |  | no_extreme_reliable | enables_or_blocks_candidate_move | 이 조건을 만족한 행에만 HCOEF25 후보와 hcoef_stable의 차이를 적용한다. |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p03_s0p25 | 1.0000 |  | p95_defense_core | source prediction move applied where mask=1 | p95 방어용 핵심 안전 구간에만 적용 |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | gated_h25_candidate | mask_p95_defense_core | 1.0000 |  | p95_defense_core | enables_or_blocks_candidate_move | 이 조건을 만족한 행에만 HCOEF25 후보와 hcoef_stable의 차이를 적용한다. |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p03_s0p25 | 1.0000 | 0.0050 | p95_defense_core | source prediction move applied where mask=1 | p95 방어용 핵심 안전 구간에만 적용 |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | gated_h25_candidate | mask_p95_defense_core | 1.0000 |  | p95_defense_core | enables_or_blocks_candidate_move | 이 조건을 만족한 행에만 HCOEF25 후보와 hcoef_stable의 차이를 적용한다. |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p03_s0p25 | 1.0000 | 0.0075 | p95_defense_core | source prediction move applied where mask=1 | p95 방어용 핵심 안전 구간에만 적용 |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gated_h25_candidate | mask_p95_defense_core | 1.0000 |  | p95_defense_core | enables_or_blocks_candidate_move | 이 조건을 만족한 행에만 HCOEF25 후보와 hcoef_stable의 차이를 적용한다. |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_conservative_guard_core_a0p01_cap0p03_s0p25 | 1.0000 |  | no_extreme_reliable | source prediction move applied where mask=1 | 극단 위험 구간을 제외하고 표본 수 10개 이상인 구간에만 적용 |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gated_h25_candidate | mask_no_extreme_reliable | 1.0000 |  | no_extreme_reliable | enables_or_blocks_candidate_move | 이 조건을 만족한 행에만 HCOEF25 후보와 hcoef_stable의 차이를 적용한다. |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_conservative_guard_core_a0p01_cap0p03_s0p25 | 1.0000 | 0.0050 | no_extreme_reliable | source prediction move applied where mask=1 | 극단 위험 구간을 제외하고 표본 수 10개 이상인 구간에만 적용 |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | gated_h25_candidate | mask_no_extreme_reliable | 1.0000 |  | no_extreme_reliable | enables_or_blocks_candidate_move | 이 조건을 만족한 행에만 HCOEF25 후보와 hcoef_stable의 차이를 적용한다. |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_conservative_guard_core_a0p01_cap0p03_s0p25 | 1.0000 | 0.0075 | no_extreme_reliable | source prediction move applied where mask=1 | 극단 위험 구간을 제외하고 표본 수 10개 이상인 구간에만 적용 |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gated_h25_candidate | mask_no_extreme_reliable | 1.0000 |  | no_extreme_reliable | enables_or_blocks_candidate_move | 이 조건을 만족한 행에만 HCOEF25 후보와 hcoef_stable의 차이를 적용한다. |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_nocap_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_conservative_guard_core_a0p01_cap0p03_s0p25 | 1.0000 |  | p95_defense_core | source prediction move applied where mask=1 | p95 방어용 핵심 안전 구간에만 적용 |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_nocap_s1 | gated_h25_candidate | mask_p95_defense_core | 1.0000 |  | p95_defense_core | enables_or_blocks_candidate_move | 이 조건을 만족한 행에만 HCOEF25 후보와 hcoef_stable의 차이를 적용한다. |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_conservative_guard_core_a0p01_cap0p03_s0p25 | 1.0000 | 0.0050 | p95_defense_core | source prediction move applied where mask=1 | p95 방어용 핵심 안전 구간에만 적용 |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | gated_h25_candidate | mask_p95_defense_core | 1.0000 |  | p95_defense_core | enables_or_blocks_candidate_move | 이 조건을 만족한 행에만 HCOEF25 후보와 hcoef_stable의 차이를 적용한다. |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_conservative_guard_core_a0p01_cap0p03_s0p25 | 1.0000 | 0.0075 | p95_defense_core | source prediction move applied where mask=1 | p95 방어용 핵심 안전 구간에만 적용 |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gated_h25_candidate | mask_p95_defense_core | 1.0000 |  | p95_defense_core | enables_or_blocks_candidate_move | 이 조건을 만족한 행에만 HCOEF25 후보와 hcoef_stable의 차이를 적용한다. |

## 9. 잔차/큰 오차 구간

| scope | split | candidate | segment_col | segment_value | n | MdAPE | MAPE | p95_APE | median_residual_log | mean_residual_log | mean_abs_move_log | over_50pct_error_rate | over_100pct_error_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_stress | 0604_ex50 | svc_numeric_seed_mean | gap_band | gap_020_plus | 402 | 0.5239 | 0.6071 | 1.3189 | 0.3621 | 0.7716 | 0.2761 | 0.5199 | 0.0622 |
| 0604_stress | 0604_ex50 | l10_seq_full_generated_bucket | gap_band | gap_020_plus | 402 | 0.5130 | 0.5988 | 1.5918 | 0.1562 | 0.5032 | 0.5894 | 0.5124 | 0.1169 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_020_plus | 402 | 0.4302 | 0.5054 | 1.0000 | 0.2961 | 0.6185 | 0.0225 | 0.4328 | 0.0448 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_nocap_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_nocap_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef_stable | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | l10_seq_full_generated_bucket | gap_band | gap_010_020 | 128 | 0.3203 | 0.4882 | 2.1936 | -0.0384 | 0.0639 | 0.3592 | 0.3359 | 0.0703 |
| 0604_stress | 0604_ex50 | ppv8_service_proxy | gap_band | gap_020_plus | 402 | 0.3131 | 0.4234 | 1.1510 | 0.1623 | 0.2613 | 0.6194 | 0.2910 | 0.0622 |
| 0604_stress | 0604_ex50 | svc_numeric_seed_mean | gap_band | gap_010_020 | 128 | 0.2777 | 0.3693 | 0.9720 | -0.0734 | 0.0324 | 0.0620 | 0.2891 | 0.0469 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_010_020 | 128 | 0.2248 | 0.3419 | 0.8656 | -0.0556 | 0.0461 | 0.0217 | 0.3125 | 0.0391 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_010_020 | 128 | 0.2210 | 0.3397 | 0.8728 | -0.0540 | 0.0394 | 0.0010 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gap_band | gap_010_020 | 128 | 0.2210 | 0.3397 | 0.8728 | -0.0540 | 0.0394 | 0.0010 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gap_band | gap_010_020 | 128 | 0.2210 | 0.3397 | 0.8728 | -0.0540 | 0.0394 | 0.0010 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | gap_band | gap_010_020 | 128 | 0.2210 | 0.3397 | 0.8728 | -0.0540 | 0.0394 | 0.0010 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_010_020 | 128 | 0.2210 | 0.3397 | 0.8728 | -0.0540 | 0.0394 | 0.0010 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gap_band | gap_010_020 | 128 | 0.2210 | 0.3397 | 0.8728 | -0.0540 | 0.0394 | 0.0010 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gap_band | gap_010_020 | 128 | 0.2210 | 0.3397 | 0.8728 | -0.0540 | 0.0394 | 0.0010 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_nocap_s1 | gap_band | gap_010_020 | 128 | 0.2210 | 0.3397 | 0.8728 | -0.0540 | 0.0394 | 0.0010 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_010_020 | 128 | 0.2210 | 0.3396 | 0.8728 | -0.0540 | 0.0394 | 0.0009 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gap_band | gap_010_020 | 128 | 0.2210 | 0.3396 | 0.8728 | -0.0540 | 0.0394 | 0.0009 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gap_band | gap_010_020 | 128 | 0.2210 | 0.3396 | 0.8728 | -0.0540 | 0.0394 | 0.0009 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_010_020 | 128 | 0.2210 | 0.3396 | 0.8728 | -0.0540 | 0.0394 | 0.0009 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gap_band | gap_010_020 | 128 | 0.2210 | 0.3396 | 0.8728 | -0.0540 | 0.0394 | 0.0009 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gap_band | gap_010_020 | 128 | 0.2210 | 0.3396 | 0.8728 | -0.0540 | 0.0394 | 0.0009 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_nocap_s1 | gap_band | gap_010_020 | 128 | 0.2210 | 0.3396 | 0.8728 | -0.0540 | 0.0394 | 0.0009 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | gap_band | gap_010_020 | 128 | 0.2225 | 0.3396 | 0.8728 | -0.0515 | 0.0395 | 0.0007 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | gap_band | gap_010_020 | 128 | 0.2225 | 0.3396 | 0.8728 | -0.0515 | 0.0395 | 0.0007 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | gap_band | gap_010_020 | 128 | 0.2225 | 0.3396 | 0.8728 | -0.0515 | 0.0395 | 0.0007 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | gap_band | gap_010_020 | 128 | 0.2225 | 0.3396 | 0.8728 | -0.0515 | 0.0395 | 0.0007 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef_stable | gap_band | gap_010_020 | 128 | 0.2255 | 0.3393 | 0.8728 | -0.0465 | 0.0399 | 0.0000 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | ppv8_service_proxy | gap_band | gap_010_020 | 128 | 0.2540 | 0.3269 | 0.7844 | 0.0520 | 0.0782 | 0.1447 | 0.2656 | 0.0156 |
| 0604_stress | 0604_ex50 | l10_seq_full_generated_bucket | gap_band | gap_005_010 | 125 | 0.1883 | 0.3007 | 0.9169 | 0.0567 | 0.0972 | 0.1938 | 0.1680 | 0.0400 |
| 0604_stress | 0604_ex50 | ppv8_service_proxy | gap_band | gap_005_010 | 125 | 0.1764 | 0.2618 | 0.7685 | 0.0806 | 0.0930 | 0.0754 | 0.0880 | 0.0240 |
| 0604_stress | 0604_ex50 | svc_numeric_seed_mean | gap_band | gap_005_010 | 125 | 0.1613 | 0.2612 | 0.9572 | 0.0380 | 0.0895 | 0.0361 | 0.0960 | 0.0480 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_005_010 | 125 | 0.1531 | 0.2572 | 0.9461 | 0.0641 | 0.0905 | 0.0190 | 0.0880 | 0.0480 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_005_010 | 125 | 0.1498 | 0.2517 | 0.9526 | 0.0403 | 0.0877 | 0.0012 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gap_band | gap_005_010 | 125 | 0.1498 | 0.2517 | 0.9526 | 0.0403 | 0.0877 | 0.0012 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gap_band | gap_005_010 | 125 | 0.1498 | 0.2517 | 0.9526 | 0.0403 | 0.0877 | 0.0012 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_nocap_s1 | gap_band | gap_005_010 | 125 | 0.1498 | 0.2517 | 0.9526 | 0.0403 | 0.0877 | 0.0012 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_005_010 | 125 | 0.1498 | 0.2517 | 0.9526 | 0.0403 | 0.0877 | 0.0012 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gap_band | gap_005_010 | 125 | 0.1498 | 0.2517 | 0.9526 | 0.0403 | 0.0877 | 0.0012 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gap_band | gap_005_010 | 125 | 0.1498 | 0.2517 | 0.9526 | 0.0403 | 0.0877 | 0.0012 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_005_010 | 125 | 0.1492 | 0.2517 | 0.9526 | 0.0403 | 0.0876 | 0.0012 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gap_band | gap_005_010 | 125 | 0.1492 | 0.2517 | 0.9526 | 0.0403 | 0.0876 | 0.0012 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gap_band | gap_005_010 | 125 | 0.1492 | 0.2517 | 0.9526 | 0.0403 | 0.0876 | 0.0012 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_nocap_s1 | gap_band | gap_005_010 | 125 | 0.1492 | 0.2517 | 0.9526 | 0.0403 | 0.0876 | 0.0012 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_005_010 | 125 | 0.1492 | 0.2517 | 0.9526 | 0.0403 | 0.0876 | 0.0012 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gap_band | gap_005_010 | 125 | 0.1492 | 0.2517 | 0.9526 | 0.0403 | 0.0876 | 0.0012 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gap_band | gap_005_010 | 125 | 0.1492 | 0.2517 | 0.9526 | 0.0403 | 0.0876 | 0.0012 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | gap_band | gap_005_010 | 125 | 0.1492 | 0.2517 | 0.9526 | 0.0403 | 0.0876 | 0.0012 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | gap_band | gap_005_010 | 125 | 0.1498 | 0.2516 | 0.9526 | 0.0403 | 0.0875 | 0.0010 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | gap_band | gap_005_010 | 125 | 0.1498 | 0.2516 | 0.9526 | 0.0403 | 0.0875 | 0.0010 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | gap_band | gap_005_010 | 125 | 0.1498 | 0.2516 | 0.9526 | 0.0403 | 0.0875 | 0.0010 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | gap_band | gap_005_010 | 125 | 0.1498 | 0.2516 | 0.9526 | 0.0403 | 0.0875 | 0.0010 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef_stable | gap_band | gap_005_010 | 125 | 0.1498 | 0.2514 | 0.9526 | 0.0403 | 0.0872 | 0.0000 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | l10_seq_full_generated_bucket | gap_band | gap_000_003 | 119 | 0.1387 | 0.2330 | 0.7125 | -0.0071 | 0.0833 | 0.1325 | 0.0924 | 0.0084 |
| 0604_stress | 0604_ex50 | l10_seq_full_generated_bucket | gap_band | gap_003_005 | 55 | 0.1531 | 0.2296 | 0.5665 | -0.0167 | 0.1022 | 0.2173 | 0.1636 | 0.0182 |
| 0604_stress | 0604_ex50 | svc_numeric_seed_mean | gap_band | gap_000_003 | 119 | 0.1025 | 0.1967 | 0.5508 | 0.0404 | 0.0785 | 0.0222 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_000_003 | 119 | 0.1066 | 0.1953 | 0.5444 | 0.0401 | 0.0761 | 0.0164 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | ppv8_service_proxy | gap_band | gap_000_003 | 119 | 0.1162 | 0.1942 | 0.5405 | 0.0395 | 0.0705 | 0.0125 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | ppv8_service_proxy | gap_band | gap_003_005 | 55 | 0.1039 | 0.1925 | 0.4983 | 0.0427 | 0.0915 | 0.0397 | 0.0545 | 0.0000 |
| 0604_stress | 0604_ex50 | svc_numeric_seed_mean | gap_band | gap_003_005 | 55 | 0.1117 | 0.1922 | 0.5421 | 0.0171 | 0.0778 | 0.0356 | 0.0727 | 0.0000 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_003_005 | 55 | 0.0809 | 0.1908 | 0.5325 | 0.0305 | 0.0819 | 0.0227 | 0.0545 | 0.0000 |

## 10. Bootstrap 요약

| source_scope | validation_scheme | candidate | method | n_bootstrap | mean_delta_MdAPE_vs_stable | mean_delta_MAPE_vs_stable | mean_delta_p95_APE_vs_stable | mean_delta_RMSE_log_vs_stable | MdAPE_improve_prob | MAPE_improve_prob | p95_improve_prob | all3_improve_prob | any2_improve_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation_oof_row | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5_no_extreme_reliable_nocap_s1 | gated_h25_candidate | 300 | -0.0014 | -0.0001 | -0.0001 | -0.0001 | 0.6733 | 0.6467 | 0.3433 | 0.1600 | 0.5833 |
| validation_oof_row | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5_p95_defense_core_nocap_s1 | gated_h25_candidate | 300 | -0.0014 | -0.0001 | -0.0001 | -0.0001 | 0.6733 | 0.6467 | 0.3433 | 0.1600 | 0.5833 |
| validation_oof_row | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_nocap_s1 | gated_h25_candidate | 300 | -0.0015 | -0.0001 | -0.0001 | -0.0002 | 0.6567 | 0.5967 | 0.3867 | 0.1600 | 0.5700 |
| validation_oof_row | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_p95_defense_core_nocap_s1 | gated_h25_candidate | 300 | -0.0015 | -0.0001 | -0.0001 | -0.0002 | 0.6567 | 0.5967 | 0.3867 | 0.1600 | 0.5700 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_cap0p0075_s0p5 | gated_h25_candidate | 300 | -0.0003 | -0.0001 | 0.0001 | -0.0001 | 0.5000 | 0.8100 | 0.3433 | 0.1533 | 0.5567 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_p95_defense_core_cap0p0075_s0p5 | gated_h25_candidate | 300 | -0.0003 | -0.0001 | 0.0001 | -0.0001 | 0.5000 | 0.8100 | 0.3433 | 0.1533 | 0.5567 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5_no_extreme_reliable_cap0p0075_s0p5 | gated_h25_candidate | 300 | -0.0003 | -0.0001 | 0.0001 | -0.0001 | 0.5000 | 0.8100 | 0.3433 | 0.1533 | 0.5567 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5_p95_defense_core_cap0p0075_s0p5 | gated_h25_candidate | 300 | -0.0003 | -0.0001 | 0.0001 | -0.0001 | 0.5000 | 0.8100 | 0.3433 | 0.1533 | 0.5567 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p04_s0p5_no_extreme_reliable_cap0p0075_s0p5 | gated_h25_candidate | 300 | -0.0003 | -0.0001 | 0.0001 | -0.0001 | 0.5000 | 0.8100 | 0.3433 | 0.1533 | 0.5567 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p04_s0p5_p95_defense_core_cap0p0075_s0p5 | gated_h25_candidate | 300 | -0.0003 | -0.0001 | 0.0001 | -0.0001 | 0.5000 | 0.8100 | 0.3433 | 0.1533 | 0.5567 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_cap0p005_s0p75 | gated_h25_candidate | 300 | -0.0003 | -0.0001 | 0.0001 | -0.0001 | 0.4967 | 0.7900 | 0.3433 | 0.1533 | 0.5467 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_p95_defense_core_cap0p005_s0p75 | gated_h25_candidate | 300 | -0.0003 | -0.0001 | 0.0001 | -0.0001 | 0.4967 | 0.7900 | 0.3433 | 0.1533 | 0.5467 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5_no_extreme_reliable_cap0p005_s0p75 | gated_h25_candidate | 300 | -0.0003 | -0.0001 | 0.0001 | -0.0001 | 0.4967 | 0.7900 | 0.3433 | 0.1533 | 0.5467 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5_p95_defense_core_cap0p005_s0p75 | gated_h25_candidate | 300 | -0.0003 | -0.0001 | 0.0001 | -0.0001 | 0.4967 | 0.7900 | 0.3433 | 0.1533 | 0.5467 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p04_s0p5_no_extreme_reliable_cap0p005_s0p75 | gated_h25_candidate | 300 | -0.0003 | -0.0001 | 0.0001 | -0.0001 | 0.4967 | 0.7900 | 0.3433 | 0.1533 | 0.5467 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p04_s0p5_p95_defense_core_cap0p005_s0p75 | gated_h25_candidate | 300 | -0.0003 | -0.0001 | 0.0001 | -0.0001 | 0.4967 | 0.7900 | 0.3433 | 0.1533 | 0.5467 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_nocap_s1 | gated_h25_candidate | 300 | -0.0010 | -0.0002 | 0.0004 | -0.0002 | 0.5800 | 0.7167 | 0.3700 | 0.1500 | 0.5833 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_p95_defense_core_nocap_s1 | gated_h25_candidate | 300 | -0.0010 | -0.0002 | 0.0004 | -0.0002 | 0.5800 | 0.7167 | 0.3700 | 0.1500 | 0.5833 |
| validation_oof_row | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_nocap_s0p75 | gated_h25_candidate | 300 | -0.0012 | -0.0001 | 0.0000 | -0.0002 | 0.6300 | 0.6567 | 0.3233 | 0.1500 | 0.5700 |
| validation_oof_row | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_p95_defense_core_nocap_s0p75 | gated_h25_candidate | 300 | -0.0012 | -0.0001 | 0.0000 | -0.0002 | 0.6300 | 0.6567 | 0.3233 | 0.1500 | 0.5700 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_nocap_s0p5 | gated_h25_candidate | 300 | -0.0005 | -0.0001 | 0.0003 | -0.0001 | 0.4833 | 0.7867 | 0.3433 | 0.1500 | 0.5300 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_p95_defense_core_nocap_s0p5 | gated_h25_candidate | 300 | -0.0005 | -0.0001 | 0.0003 | -0.0001 | 0.4833 | 0.7867 | 0.3433 | 0.1500 | 0.5300 |
| validation_oof_row | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p04_s0p5_no_extreme_reliable_nocap_s1 | gated_h25_candidate | 300 | -0.0013 | -0.0000 | 0.0000 | -0.0002 | 0.6533 | 0.5133 | 0.3867 | 0.1500 | 0.5200 |
| validation_oof_row | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p04_s0p5_p95_defense_core_nocap_s1 | gated_h25_candidate | 300 | -0.0013 | -0.0000 | 0.0000 | -0.0002 | 0.6533 | 0.5133 | 0.3867 | 0.1500 | 0.5200 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5_no_extreme_reliable_nocap_s0p5 | gated_h25_candidate | 300 | -0.0004 | -0.0001 | 0.0002 | -0.0001 | 0.4733 | 0.8100 | 0.3433 | 0.1467 | 0.5433 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5_p95_defense_core_nocap_s0p5 | gated_h25_candidate | 300 | -0.0004 | -0.0001 | 0.0002 | -0.0001 | 0.4733 | 0.8100 | 0.3433 | 0.1467 | 0.5433 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_nocap_s0p75 | gated_h25_candidate | 300 | -0.0007 | -0.0002 | 0.0004 | -0.0002 | 0.5033 | 0.7567 | 0.3667 | 0.1433 | 0.5567 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_p95_defense_core_nocap_s0p75 | gated_h25_candidate | 300 | -0.0007 | -0.0002 | 0.0004 | -0.0002 | 0.5033 | 0.7567 | 0.3667 | 0.1433 | 0.5567 |
| validation_oof_row | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_cap0p0075_s1 | gated_h25_candidate | 300 | -0.0011 | -0.0001 | -0.0001 | -0.0001 | 0.5833 | 0.6500 | 0.3433 | 0.1433 | 0.5400 |
| validation_oof_row | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_p95_defense_core_cap0p0075_s1 | gated_h25_candidate | 300 | -0.0011 | -0.0001 | -0.0001 | -0.0001 | 0.5833 | 0.6500 | 0.3433 | 0.1433 | 0.5400 |
| validation_oof_row | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5_no_extreme_reliable_cap0p0075_s1 | gated_h25_candidate | 300 | -0.0011 | -0.0001 | -0.0001 | -0.0001 | 0.5833 | 0.6500 | 0.3433 | 0.1433 | 0.5400 |
| validation_oof_row | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5_p95_defense_core_cap0p0075_s1 | gated_h25_candidate | 300 | -0.0011 | -0.0001 | -0.0001 | -0.0001 | 0.5833 | 0.6500 | 0.3433 | 0.1433 | 0.5400 |
| validation_oof_row | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p04_s0p5_no_extreme_reliable_cap0p0075_s1 | gated_h25_candidate | 300 | -0.0011 | -0.0001 | -0.0001 | -0.0001 | 0.5833 | 0.6500 | 0.3433 | 0.1433 | 0.5400 |
| validation_oof_row | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p04_s0p5_p95_defense_core_cap0p0075_s1 | gated_h25_candidate | 300 | -0.0011 | -0.0001 | -0.0001 | -0.0001 | 0.5833 | 0.6500 | 0.3433 | 0.1433 | 0.5400 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_cap0p005_s1 | gated_h25_candidate | 300 | -0.0004 | -0.0001 | 0.0002 | -0.0001 | 0.4767 | 0.7767 | 0.3433 | 0.1433 | 0.5233 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_p95_defense_core_cap0p005_s1 | gated_h25_candidate | 300 | -0.0004 | -0.0001 | 0.0002 | -0.0001 | 0.4767 | 0.7767 | 0.3433 | 0.1433 | 0.5233 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5_no_extreme_reliable_cap0p005_s1 | gated_h25_candidate | 300 | -0.0004 | -0.0001 | 0.0002 | -0.0001 | 0.4767 | 0.7767 | 0.3433 | 0.1433 | 0.5233 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5_p95_defense_core_cap0p005_s1 | gated_h25_candidate | 300 | -0.0004 | -0.0001 | 0.0002 | -0.0001 | 0.4767 | 0.7767 | 0.3433 | 0.1433 | 0.5233 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p04_s0p5_no_extreme_reliable_cap0p005_s1 | gated_h25_candidate | 300 | -0.0004 | -0.0001 | 0.0002 | -0.0001 | 0.4767 | 0.7767 | 0.3433 | 0.1433 | 0.5233 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p04_s0p5_p95_defense_core_cap0p005_s1 | gated_h25_candidate | 300 | -0.0004 | -0.0001 | 0.0002 | -0.0001 | 0.4767 | 0.7767 | 0.3433 | 0.1433 | 0.5233 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5_no_extreme_reliable_nocap_s1 | gated_h25_candidate | 300 | -0.0008 | -0.0001 | 0.0002 | -0.0001 | 0.5567 | 0.7467 | 0.3433 | 0.1400 | 0.5700 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5_p95_defense_core_nocap_s1 | gated_h25_candidate | 300 | -0.0008 | -0.0001 | 0.0002 | -0.0001 | 0.5567 | 0.7467 | 0.3433 | 0.1400 | 0.5700 |
| validation_oof_artist | artist_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_nocap_s0p75 | gated_h25_candidate | 300 | -0.0007 | -0.0002 | 0.0006 | -0.0002 | 0.5233 | 0.8200 | 0.3133 | 0.1333 | 0.5800 |
| validation_oof_artist | artist_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_p95_defense_core_nocap_s0p75 | gated_h25_candidate | 300 | -0.0007 | -0.0002 | 0.0006 | -0.0002 | 0.5233 | 0.8200 | 0.3133 | 0.1333 | 0.5800 |
| validation_oof_artist | artist_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_nocap_s1 | gated_h25_candidate | 300 | -0.0010 | -0.0002 | 0.0006 | -0.0002 | 0.5500 | 0.7867 | 0.3167 | 0.1333 | 0.5767 |
| validation_oof_artist | artist_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_p95_defense_core_nocap_s1 | gated_h25_candidate | 300 | -0.0010 | -0.0002 | 0.0006 | -0.0002 | 0.5500 | 0.7867 | 0.3167 | 0.1333 | 0.5767 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_cap0p0075_s1 | gated_h25_candidate | 300 | -0.0007 | -0.0001 | 0.0002 | -0.0001 | 0.4900 | 0.7700 | 0.3433 | 0.1333 | 0.5333 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_p95_defense_core_cap0p0075_s1 | gated_h25_candidate | 300 | -0.0007 | -0.0001 | 0.0002 | -0.0001 | 0.4900 | 0.7700 | 0.3433 | 0.1333 | 0.5333 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5_no_extreme_reliable_cap0p0075_s1 | gated_h25_candidate | 300 | -0.0007 | -0.0001 | 0.0002 | -0.0001 | 0.4900 | 0.7700 | 0.3433 | 0.1333 | 0.5333 |
| validation_oof_artist | row_bootstrap | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5_p95_defense_core_cap0p0075_s1 | gated_h25_candidate | 300 | -0.0007 | -0.0001 | 0.0002 | -0.0001 | 0.4900 | 0.7700 | 0.3433 | 0.1333 | 0.5333 |

## 11. 적용 정책 상세

| scope | candidate | source_candidate | mask_name | method | strength | cap | applied_rows | rows | applied_share | mean_abs_move_log | purpose |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation_oof_row | hcoef_stable | hcoef_stable | all | source | 1.0000 |  | 519 | 519 | 1.0000 | 0.0000 | 현재 HCOEF 안정 후보 |
| validation_oof_row | current_70_30 | current_70_30 | all | source | 1.0000 |  | 519 | 519 | 1.0000 | 0.0181 | 서비스 v0.1 70:30 기준 후보 |
| validation_oof_row | ppv8_service_proxy | ppv8_service_proxy | all | source | 1.0000 |  | 519 | 519 | 1.0000 | 0.1132 | PP-V8/service component proxy |
| validation_oof_row | svc_numeric_seed_mean | svc_numeric_seed_mean | all | source | 1.0000 |  | 519 | 519 | 1.0000 | 0.0504 | 유사 작품 기반 가격 피처 |
| validation_oof_row | l10_seq_full_generated_bucket | l10_seq_full_generated_bucket | all | source | 1.0000 |  | 519 | 519 | 1.0000 | 0.1690 | PP-L10 순차 component |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_lowrisk_only_nocap_s0p25 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | lowrisk_only | gated_h25_candidate | 0.2500 |  | 50 | 519 | 0.0963 | 0.0001 | 위험 신호가 없고 유사 표본 수가 10개 이상인 구간에만 HCOEF25 이동 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_lowrisk_only_cap0p0025_s0p25 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | lowrisk_only | gated_h25_candidate | 0.2500 | 0.0025 | 50 | 519 | 0.0963 | 0.0001 | 위험 신호가 없고 유사 표본 수가 10개 이상인 구간에만 HCOEF25 이동 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_lowrisk_only_cap0p005_s0p25 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | lowrisk_only | gated_h25_candidate | 0.2500 | 0.0050 | 50 | 519 | 0.0963 | 0.0001 | 위험 신호가 없고 유사 표본 수가 10개 이상인 구간에만 HCOEF25 이동 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_lowrisk_only_cap0p0075_s0p25 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | lowrisk_only | gated_h25_candidate | 0.2500 | 0.0075 | 50 | 519 | 0.0963 | 0.0001 | 위험 신호가 없고 유사 표본 수가 10개 이상인 구간에만 HCOEF25 이동 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_lowrisk_only_nocap_s0p5 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | lowrisk_only | gated_h25_candidate | 0.5000 |  | 50 | 519 | 0.0963 | 0.0001 | 위험 신호가 없고 유사 표본 수가 10개 이상인 구간에만 HCOEF25 이동 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_lowrisk_only_cap0p0025_s0p5 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | lowrisk_only | gated_h25_candidate | 0.5000 | 0.0025 | 50 | 519 | 0.0963 | 0.0001 | 위험 신호가 없고 유사 표본 수가 10개 이상인 구간에만 HCOEF25 이동 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_lowrisk_only_cap0p005_s0p5 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | lowrisk_only | gated_h25_candidate | 0.5000 | 0.0050 | 50 | 519 | 0.0963 | 0.0001 | 위험 신호가 없고 유사 표본 수가 10개 이상인 구간에만 HCOEF25 이동 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_lowrisk_only_cap0p0075_s0p5 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | lowrisk_only | gated_h25_candidate | 0.5000 | 0.0075 | 50 | 519 | 0.0963 | 0.0001 | 위험 신호가 없고 유사 표본 수가 10개 이상인 구간에만 HCOEF25 이동 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_lowrisk_only_nocap_s0p75 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | lowrisk_only | gated_h25_candidate | 0.7500 |  | 50 | 519 | 0.0963 | 0.0002 | 위험 신호가 없고 유사 표본 수가 10개 이상인 구간에만 HCOEF25 이동 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_lowrisk_only_cap0p0025_s0p75 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | lowrisk_only | gated_h25_candidate | 0.7500 | 0.0025 | 50 | 519 | 0.0963 | 0.0002 | 위험 신호가 없고 유사 표본 수가 10개 이상인 구간에만 HCOEF25 이동 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_lowrisk_only_cap0p005_s0p75 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | lowrisk_only | gated_h25_candidate | 0.7500 | 0.0050 | 50 | 519 | 0.0963 | 0.0002 | 위험 신호가 없고 유사 표본 수가 10개 이상인 구간에만 HCOEF25 이동 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_lowrisk_only_cap0p0075_s0p75 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | lowrisk_only | gated_h25_candidate | 0.7500 | 0.0075 | 50 | 519 | 0.0963 | 0.0002 | 위험 신호가 없고 유사 표본 수가 10개 이상인 구간에만 HCOEF25 이동 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_lowrisk_only_nocap_s1 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | lowrisk_only | gated_h25_candidate | 1.0000 |  | 50 | 519 | 0.0963 | 0.0002 | 위험 신호가 없고 유사 표본 수가 10개 이상인 구간에만 HCOEF25 이동 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_lowrisk_only_cap0p0025_s1 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | lowrisk_only | gated_h25_candidate | 1.0000 | 0.0025 | 50 | 519 | 0.0963 | 0.0002 | 위험 신호가 없고 유사 표본 수가 10개 이상인 구간에만 HCOEF25 이동 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_lowrisk_only_cap0p005_s1 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | lowrisk_only | gated_h25_candidate | 1.0000 | 0.0050 | 50 | 519 | 0.0963 | 0.0002 | 위험 신호가 없고 유사 표본 수가 10개 이상인 구간에만 HCOEF25 이동 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_lowrisk_only_cap0p0075_s1 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | lowrisk_only | gated_h25_candidate | 1.0000 | 0.0075 | 50 | 519 | 0.0963 | 0.0002 | 위험 신호가 없고 유사 표본 수가 10개 이상인 구간에만 HCOEF25 이동 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_reliable_lowrisk_nocap_s0p25 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | reliable_lowrisk | gated_h25_candidate | 0.2500 |  | 45 | 519 | 0.0867 | 0.0001 | 표본 수 20개 이상, 낮은/중간 quantile 폭, 낮은 spread 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_reliable_lowrisk_cap0p0025_s0p25 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | reliable_lowrisk | gated_h25_candidate | 0.2500 | 0.0025 | 45 | 519 | 0.0867 | 0.0001 | 표본 수 20개 이상, 낮은/중간 quantile 폭, 낮은 spread 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_reliable_lowrisk_cap0p005_s0p25 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | reliable_lowrisk | gated_h25_candidate | 0.2500 | 0.0050 | 45 | 519 | 0.0867 | 0.0001 | 표본 수 20개 이상, 낮은/중간 quantile 폭, 낮은 spread 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_reliable_lowrisk_cap0p0075_s0p25 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | reliable_lowrisk | gated_h25_candidate | 0.2500 | 0.0075 | 45 | 519 | 0.0867 | 0.0001 | 표본 수 20개 이상, 낮은/중간 quantile 폭, 낮은 spread 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_reliable_lowrisk_nocap_s0p5 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | reliable_lowrisk | gated_h25_candidate | 0.5000 |  | 45 | 519 | 0.0867 | 0.0001 | 표본 수 20개 이상, 낮은/중간 quantile 폭, 낮은 spread 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_reliable_lowrisk_cap0p0025_s0p5 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | reliable_lowrisk | gated_h25_candidate | 0.5000 | 0.0025 | 45 | 519 | 0.0867 | 0.0001 | 표본 수 20개 이상, 낮은/중간 quantile 폭, 낮은 spread 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_reliable_lowrisk_cap0p005_s0p5 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | reliable_lowrisk | gated_h25_candidate | 0.5000 | 0.0050 | 45 | 519 | 0.0867 | 0.0001 | 표본 수 20개 이상, 낮은/중간 quantile 폭, 낮은 spread 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_reliable_lowrisk_cap0p0075_s0p5 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | reliable_lowrisk | gated_h25_candidate | 0.5000 | 0.0075 | 45 | 519 | 0.0867 | 0.0001 | 표본 수 20개 이상, 낮은/중간 quantile 폭, 낮은 spread 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_reliable_lowrisk_nocap_s0p75 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | reliable_lowrisk | gated_h25_candidate | 0.7500 |  | 45 | 519 | 0.0867 | 0.0001 | 표본 수 20개 이상, 낮은/중간 quantile 폭, 낮은 spread 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_reliable_lowrisk_cap0p0025_s0p75 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | reliable_lowrisk | gated_h25_candidate | 0.7500 | 0.0025 | 45 | 519 | 0.0867 | 0.0001 | 표본 수 20개 이상, 낮은/중간 quantile 폭, 낮은 spread 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_reliable_lowrisk_cap0p005_s0p75 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | reliable_lowrisk | gated_h25_candidate | 0.7500 | 0.0050 | 45 | 519 | 0.0867 | 0.0001 | 표본 수 20개 이상, 낮은/중간 quantile 폭, 낮은 spread 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_reliable_lowrisk_cap0p0075_s0p75 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | reliable_lowrisk | gated_h25_candidate | 0.7500 | 0.0075 | 45 | 519 | 0.0867 | 0.0001 | 표본 수 20개 이상, 낮은/중간 quantile 폭, 낮은 spread 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_reliable_lowrisk_nocap_s1 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | reliable_lowrisk | gated_h25_candidate | 1.0000 |  | 45 | 519 | 0.0867 | 0.0002 | 표본 수 20개 이상, 낮은/중간 quantile 폭, 낮은 spread 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_reliable_lowrisk_cap0p0025_s1 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | reliable_lowrisk | gated_h25_candidate | 1.0000 | 0.0025 | 45 | 519 | 0.0867 | 0.0002 | 표본 수 20개 이상, 낮은/중간 quantile 폭, 낮은 spread 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_reliable_lowrisk_cap0p005_s1 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | reliable_lowrisk | gated_h25_candidate | 1.0000 | 0.0050 | 45 | 519 | 0.0867 | 0.0002 | 표본 수 20개 이상, 낮은/중간 quantile 폭, 낮은 spread 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_reliable_lowrisk_cap0p0075_s1 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | reliable_lowrisk | gated_h25_candidate | 1.0000 | 0.0075 | 45 | 519 | 0.0867 | 0.0002 | 표본 수 20개 이상, 낮은/중간 quantile 폭, 낮은 spread 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_no_extreme_reliable_nocap_s0p25 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | no_extreme_reliable | gated_h25_candidate | 0.2500 |  | 144 | 519 | 0.2775 | 0.0002 | 극단 위험 구간을 제외하고 표본 수 10개 이상인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_no_extreme_reliable_cap0p0025_s0p25 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | no_extreme_reliable | gated_h25_candidate | 0.2500 | 0.0025 | 144 | 519 | 0.2775 | 0.0002 | 극단 위험 구간을 제외하고 표본 수 10개 이상인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_no_extreme_reliable_cap0p005_s0p25 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | no_extreme_reliable | gated_h25_candidate | 0.2500 | 0.0050 | 144 | 519 | 0.2775 | 0.0002 | 극단 위험 구간을 제외하고 표본 수 10개 이상인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_no_extreme_reliable_cap0p0075_s0p25 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | no_extreme_reliable | gated_h25_candidate | 0.2500 | 0.0075 | 144 | 519 | 0.2775 | 0.0002 | 극단 위험 구간을 제외하고 표본 수 10개 이상인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_no_extreme_reliable_nocap_s0p5 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | no_extreme_reliable | gated_h25_candidate | 0.5000 |  | 144 | 519 | 0.2775 | 0.0003 | 극단 위험 구간을 제외하고 표본 수 10개 이상인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_no_extreme_reliable_cap0p0025_s0p5 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | no_extreme_reliable | gated_h25_candidate | 0.5000 | 0.0025 | 144 | 519 | 0.2775 | 0.0003 | 극단 위험 구간을 제외하고 표본 수 10개 이상인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_no_extreme_reliable_cap0p005_s0p5 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | no_extreme_reliable | gated_h25_candidate | 0.5000 | 0.0050 | 144 | 519 | 0.2775 | 0.0003 | 극단 위험 구간을 제외하고 표본 수 10개 이상인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_no_extreme_reliable_cap0p0075_s0p5 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | no_extreme_reliable | gated_h25_candidate | 0.5000 | 0.0075 | 144 | 519 | 0.2775 | 0.0003 | 극단 위험 구간을 제외하고 표본 수 10개 이상인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_no_extreme_reliable_nocap_s0p75 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | no_extreme_reliable | gated_h25_candidate | 0.7500 |  | 144 | 519 | 0.2775 | 0.0005 | 극단 위험 구간을 제외하고 표본 수 10개 이상인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_no_extreme_reliable_cap0p0025_s0p75 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | no_extreme_reliable | gated_h25_candidate | 0.7500 | 0.0025 | 144 | 519 | 0.2775 | 0.0005 | 극단 위험 구간을 제외하고 표본 수 10개 이상인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_no_extreme_reliable_cap0p005_s0p75 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | no_extreme_reliable | gated_h25_candidate | 0.7500 | 0.0050 | 144 | 519 | 0.2775 | 0.0005 | 극단 위험 구간을 제외하고 표본 수 10개 이상인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_no_extreme_reliable_cap0p0075_s0p75 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | no_extreme_reliable | gated_h25_candidate | 0.7500 | 0.0075 | 144 | 519 | 0.2775 | 0.0005 | 극단 위험 구간을 제외하고 표본 수 10개 이상인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_no_extreme_reliable_nocap_s1 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | no_extreme_reliable | gated_h25_candidate | 1.0000 |  | 144 | 519 | 0.2775 | 0.0006 | 극단 위험 구간을 제외하고 표본 수 10개 이상인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_no_extreme_reliable_cap0p0025_s1 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | no_extreme_reliable | gated_h25_candidate | 1.0000 | 0.0025 | 144 | 519 | 0.2775 | 0.0006 | 극단 위험 구간을 제외하고 표본 수 10개 이상인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_no_extreme_reliable_cap0p005_s1 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | no_extreme_reliable | gated_h25_candidate | 1.0000 | 0.0050 | 144 | 519 | 0.2775 | 0.0006 | 극단 위험 구간을 제외하고 표본 수 10개 이상인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_no_extreme_reliable_cap0p0075_s1 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | no_extreme_reliable | gated_h25_candidate | 1.0000 | 0.0075 | 144 | 519 | 0.2775 | 0.0006 | 극단 위험 구간을 제외하고 표본 수 10개 이상인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_confidence_medium_plus_nocap_s0p25 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | confidence_medium_plus | gated_h25_candidate | 0.2500 |  | 132 | 519 | 0.2543 | 0.0001 | 운영 신뢰도 medium 이상 또는 누락이지만 hard risk가 아닌 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_confidence_medium_plus_cap0p0025_s0p25 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | confidence_medium_plus | gated_h25_candidate | 0.2500 | 0.0025 | 132 | 519 | 0.2543 | 0.0001 | 운영 신뢰도 medium 이상 또는 누락이지만 hard risk가 아닌 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_confidence_medium_plus_cap0p005_s0p25 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | confidence_medium_plus | gated_h25_candidate | 0.2500 | 0.0050 | 132 | 519 | 0.2543 | 0.0001 | 운영 신뢰도 medium 이상 또는 누락이지만 hard risk가 아닌 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_confidence_medium_plus_cap0p0075_s0p25 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | confidence_medium_plus | gated_h25_candidate | 0.2500 | 0.0075 | 132 | 519 | 0.2543 | 0.0001 | 운영 신뢰도 medium 이상 또는 누락이지만 hard risk가 아닌 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_confidence_medium_plus_nocap_s0p5 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | confidence_medium_plus | gated_h25_candidate | 0.5000 |  | 132 | 519 | 0.2543 | 0.0003 | 운영 신뢰도 medium 이상 또는 누락이지만 hard risk가 아닌 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_confidence_medium_plus_cap0p0025_s0p5 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | confidence_medium_plus | gated_h25_candidate | 0.5000 | 0.0025 | 132 | 519 | 0.2543 | 0.0003 | 운영 신뢰도 medium 이상 또는 누락이지만 hard risk가 아닌 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_confidence_medium_plus_cap0p005_s0p5 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | confidence_medium_plus | gated_h25_candidate | 0.5000 | 0.0050 | 132 | 519 | 0.2543 | 0.0003 | 운영 신뢰도 medium 이상 또는 누락이지만 hard risk가 아닌 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_confidence_medium_plus_cap0p0075_s0p5 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | confidence_medium_plus | gated_h25_candidate | 0.5000 | 0.0075 | 132 | 519 | 0.2543 | 0.0003 | 운영 신뢰도 medium 이상 또는 누락이지만 hard risk가 아닌 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_confidence_medium_plus_nocap_s0p75 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | confidence_medium_plus | gated_h25_candidate | 0.7500 |  | 132 | 519 | 0.2543 | 0.0004 | 운영 신뢰도 medium 이상 또는 누락이지만 hard risk가 아닌 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_confidence_medium_plus_cap0p0025_s0p75 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | confidence_medium_plus | gated_h25_candidate | 0.7500 | 0.0025 | 132 | 519 | 0.2543 | 0.0004 | 운영 신뢰도 medium 이상 또는 누락이지만 hard risk가 아닌 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_confidence_medium_plus_cap0p005_s0p75 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | confidence_medium_plus | gated_h25_candidate | 0.7500 | 0.0050 | 132 | 519 | 0.2543 | 0.0004 | 운영 신뢰도 medium 이상 또는 누락이지만 hard risk가 아닌 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_confidence_medium_plus_cap0p0075_s0p75 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | confidence_medium_plus | gated_h25_candidate | 0.7500 | 0.0075 | 132 | 519 | 0.2543 | 0.0004 | 운영 신뢰도 medium 이상 또는 누락이지만 hard risk가 아닌 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_confidence_medium_plus_nocap_s1 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | confidence_medium_plus | gated_h25_candidate | 1.0000 |  | 132 | 519 | 0.2543 | 0.0006 | 운영 신뢰도 medium 이상 또는 누락이지만 hard risk가 아닌 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_confidence_medium_plus_cap0p0025_s1 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | confidence_medium_plus | gated_h25_candidate | 1.0000 | 0.0025 | 132 | 519 | 0.2543 | 0.0006 | 운영 신뢰도 medium 이상 또는 누락이지만 hard risk가 아닌 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_confidence_medium_plus_cap0p005_s1 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | confidence_medium_plus | gated_h25_candidate | 1.0000 | 0.0050 | 132 | 519 | 0.2543 | 0.0006 | 운영 신뢰도 medium 이상 또는 누락이지만 hard risk가 아닌 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_confidence_medium_plus_cap0p0075_s1 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | confidence_medium_plus | gated_h25_candidate | 1.0000 | 0.0075 | 132 | 519 | 0.2543 | 0.0006 | 운영 신뢰도 medium 이상 또는 누락이지만 hard risk가 아닌 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_qwidth_gap_safe_nocap_s0p25 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | qwidth_gap_safe | gated_h25_candidate | 0.2500 |  | 107 | 519 | 0.2062 | 0.0001 | quantile 폭과 후보 간 gap이 모두 안정적인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_qwidth_gap_safe_cap0p0025_s0p25 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | qwidth_gap_safe | gated_h25_candidate | 0.2500 | 0.0025 | 107 | 519 | 0.2062 | 0.0001 | quantile 폭과 후보 간 gap이 모두 안정적인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_qwidth_gap_safe_cap0p005_s0p25 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | qwidth_gap_safe | gated_h25_candidate | 0.2500 | 0.0050 | 107 | 519 | 0.2062 | 0.0001 | quantile 폭과 후보 간 gap이 모두 안정적인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_qwidth_gap_safe_cap0p0075_s0p25 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | qwidth_gap_safe | gated_h25_candidate | 0.2500 | 0.0075 | 107 | 519 | 0.2062 | 0.0001 | quantile 폭과 후보 간 gap이 모두 안정적인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_qwidth_gap_safe_nocap_s0p5 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | qwidth_gap_safe | gated_h25_candidate | 0.5000 |  | 107 | 519 | 0.2062 | 0.0002 | quantile 폭과 후보 간 gap이 모두 안정적인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_qwidth_gap_safe_cap0p0025_s0p5 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | qwidth_gap_safe | gated_h25_candidate | 0.5000 | 0.0025 | 107 | 519 | 0.2062 | 0.0002 | quantile 폭과 후보 간 gap이 모두 안정적인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_qwidth_gap_safe_cap0p005_s0p5 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | qwidth_gap_safe | gated_h25_candidate | 0.5000 | 0.0050 | 107 | 519 | 0.2062 | 0.0002 | quantile 폭과 후보 간 gap이 모두 안정적인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_qwidth_gap_safe_cap0p0075_s0p5 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | qwidth_gap_safe | gated_h25_candidate | 0.5000 | 0.0075 | 107 | 519 | 0.2062 | 0.0002 | quantile 폭과 후보 간 gap이 모두 안정적인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_qwidth_gap_safe_nocap_s0p75 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | qwidth_gap_safe | gated_h25_candidate | 0.7500 |  | 107 | 519 | 0.2062 | 0.0003 | quantile 폭과 후보 간 gap이 모두 안정적인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_qwidth_gap_safe_cap0p0025_s0p75 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | qwidth_gap_safe | gated_h25_candidate | 0.7500 | 0.0025 | 107 | 519 | 0.2062 | 0.0003 | quantile 폭과 후보 간 gap이 모두 안정적인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_qwidth_gap_safe_cap0p005_s0p75 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | qwidth_gap_safe | gated_h25_candidate | 0.7500 | 0.0050 | 107 | 519 | 0.2062 | 0.0003 | quantile 폭과 후보 간 gap이 모두 안정적인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_qwidth_gap_safe_cap0p0075_s0p75 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | qwidth_gap_safe | gated_h25_candidate | 0.7500 | 0.0075 | 107 | 519 | 0.2062 | 0.0003 | quantile 폭과 후보 간 gap이 모두 안정적인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_qwidth_gap_safe_nocap_s1 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | qwidth_gap_safe | gated_h25_candidate | 1.0000 |  | 107 | 519 | 0.2062 | 0.0005 | quantile 폭과 후보 간 gap이 모두 안정적인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_qwidth_gap_safe_cap0p0025_s1 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | qwidth_gap_safe | gated_h25_candidate | 1.0000 | 0.0025 | 107 | 519 | 0.2062 | 0.0005 | quantile 폭과 후보 간 gap이 모두 안정적인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_qwidth_gap_safe_cap0p005_s1 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | qwidth_gap_safe | gated_h25_candidate | 1.0000 | 0.0050 | 107 | 519 | 0.2062 | 0.0005 | quantile 폭과 후보 간 gap이 모두 안정적인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_qwidth_gap_safe_cap0p0075_s1 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | qwidth_gap_safe | gated_h25_candidate | 1.0000 | 0.0075 | 107 | 519 | 0.2062 | 0.0005 | quantile 폭과 후보 간 gap이 모두 안정적인 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_p95_defense_core_nocap_s0p25 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | p95_defense_core | gated_h25_candidate | 0.2500 |  | 144 | 519 | 0.2775 | 0.0002 | p95 방어용 핵심 안전 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_p95_defense_core_cap0p0025_s0p25 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | p95_defense_core | gated_h25_candidate | 0.2500 | 0.0025 | 144 | 519 | 0.2775 | 0.0002 | p95 방어용 핵심 안전 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_p95_defense_core_cap0p005_s0p25 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | p95_defense_core | gated_h25_candidate | 0.2500 | 0.0050 | 144 | 519 | 0.2775 | 0.0002 | p95 방어용 핵심 안전 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_p95_defense_core_cap0p0075_s0p25 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | p95_defense_core | gated_h25_candidate | 0.2500 | 0.0075 | 144 | 519 | 0.2775 | 0.0002 | p95 방어용 핵심 안전 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_p95_defense_core_nocap_s0p5 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | p95_defense_core | gated_h25_candidate | 0.5000 |  | 144 | 519 | 0.2775 | 0.0003 | p95 방어용 핵심 안전 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_p95_defense_core_cap0p0025_s0p5 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | p95_defense_core | gated_h25_candidate | 0.5000 | 0.0025 | 144 | 519 | 0.2775 | 0.0003 | p95 방어용 핵심 안전 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_p95_defense_core_cap0p005_s0p5 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | p95_defense_core | gated_h25_candidate | 0.5000 | 0.0050 | 144 | 519 | 0.2775 | 0.0003 | p95 방어용 핵심 안전 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_p95_defense_core_cap0p0075_s0p5 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | p95_defense_core | gated_h25_candidate | 0.5000 | 0.0075 | 144 | 519 | 0.2775 | 0.0003 | p95 방어용 핵심 안전 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_p95_defense_core_nocap_s0p75 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | p95_defense_core | gated_h25_candidate | 0.7500 |  | 144 | 519 | 0.2775 | 0.0005 | p95 방어용 핵심 안전 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_p95_defense_core_cap0p0025_s0p75 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | p95_defense_core | gated_h25_candidate | 0.7500 | 0.0025 | 144 | 519 | 0.2775 | 0.0005 | p95 방어용 핵심 안전 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_p95_defense_core_cap0p005_s0p75 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | p95_defense_core | gated_h25_candidate | 0.7500 | 0.0050 | 144 | 519 | 0.2775 | 0.0005 | p95 방어용 핵심 안전 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_p95_defense_core_cap0p0075_s0p75 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | p95_defense_core | gated_h25_candidate | 0.7500 | 0.0075 | 144 | 519 | 0.2775 | 0.0005 | p95 방어용 핵심 안전 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_p95_defense_core_nocap_s1 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | p95_defense_core | gated_h25_candidate | 1.0000 |  | 144 | 519 | 0.2775 | 0.0006 | p95 방어용 핵심 안전 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_p95_defense_core_cap0p0025_s1 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | p95_defense_core | gated_h25_candidate | 1.0000 | 0.0025 | 144 | 519 | 0.2775 | 0.0006 | p95 방어용 핵심 안전 구간에만 적용 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p01_s0p25_p95_defense_core_cap0p005_s1 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | p95_defense_core | gated_h25_candidate | 1.0000 | 0.0050 | 144 | 519 | 0.2775 | 0.0006 | p95 방어용 핵심 안전 구간에만 적용 |

## 12. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/policy_map.csv`
- `outputs/mask_coverage_summary.csv`
- `outputs/residual_analysis.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `outputs/selected_candidates.csv`
- `artifacts/experiment_config.json`