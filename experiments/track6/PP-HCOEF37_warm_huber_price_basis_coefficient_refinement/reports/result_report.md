# PP-HCOEF37 Warm Huber 확장 반복 검증 실험

- 작성일: 2026-06-08 09:07
- 목적: HCOEF36 상위 라우팅 후보가 fixed test에서만 우연히 좋아진 것인지, row/artist 반복 검증에서도 유지되는지 확인.
- 기준 후보: `current_70_30`.
- 운영 비교 후보: `hcoef_stable`.
- 반복 수: row OOF `60`회, artist OOF `60`회.
- 선택 원칙: HCOEF36에서 이미 정의된 후보와 라우팅 경계만 사용. fixed test/0604 residual로 새 경계를 만들지 않음.

## 1. 실행 결론

- 최상위 후보: `hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90`.
- 판단: Warm 안정 반복 검증 후보.
- fixed test MdAPE/MAPE/p95: `0.138290/0.272937/0.806031`.
- hcoef_stable 대비 fixed delta MdAPE/MAPE/p95: `-0.000513/-0.000052/-0.000335`.
- row/artist min stable any2/all3: `0.9333/0.4333`.
- HCOEF37은 새 피처 탐색 실험이 아니라 HCOEF36 후보의 안정성 재검증 실험이다.

## 2. fixed test / 0604 확인 지표

| split | candidate | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable | route_rule | route_coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | current_70_30 | 0.1305 | 0.2110 | 0.6580 | 0.3292 | 0.0045 | 0.0028 | 0.0101 | nan | nan |
| validation | hcoef_stable | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | nan | nan |
| test | current_70_30 | 0.1405 | 0.2748 | 0.8331 | 0.3996 | 0.0017 | 0.0018 | 0.0267 | nan | nan |
| test | hcoef_stable | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | nan | nan |
| 0604_ex50 | current_70_30 | 0.2779 | 0.3774 | 0.9871 | 1.3117 | 0.0049 | 0.0030 | 0.0036 | nan | nan |
| 0604_ex50 | hcoef_stable | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | nan | nan |
| validation | hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66 | 0.1259 | 0.2081 | 0.6474 | 0.3250 | -0.0001 | -0.0001 | -0.0006 | spread_q66 | 0.6590 |
| test | hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66 | 0.1383 | 0.2729 | 0.8060 | 0.3987 | -0.0005 | -0.0001 | -0.0003 | spread_q66 | 0.6211 |
| 0604_ex50 | hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66 | 0.2734 | 0.3744 | 0.9835 | 1.3078 | 0.0003 | 0.0001 | 0.0000 | spread_q66 | 0.4813 |
| validation | hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66 | 0.1259 | 0.2081 | 0.6474 | 0.3250 | -0.0001 | -0.0001 | -0.0006 | n_ge5_spread_q66 | 0.6590 |
| test | hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66 | 0.1383 | 0.2729 | 0.8060 | 0.3987 | -0.0005 | -0.0001 | -0.0003 | n_ge5_spread_q66 | 0.6211 |
| 0604_ex50 | hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66 | 0.2734 | 0.3743 | 0.9835 | 1.3078 | 0.0003 | -0.0000 | 0.0000 | n_ge5_spread_q66 | 0.4150 |
| validation | hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90 | 0.1259 | 0.2081 | 0.6474 | 0.3250 | -0.0001 | -0.0001 | -0.0006 | n_ge5_spread_q66_area90 | 0.6262 |
| test | hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90 | 0.1383 | 0.2729 | 0.8060 | 0.3987 | -0.0005 | -0.0001 | -0.0003 | n_ge5_spread_q66_area90 | 0.5865 |
| 0604_ex50 | hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90 | 0.2734 | 0.3743 | 0.9835 | 1.3078 | 0.0003 | -0.0000 | 0.0000 | n_ge5_spread_q66_area90 | 0.3872 |
| validation | hcoef36_route_p95_near_all_cap0p0075_s0p2__precise_level_spread_q75 | 0.1260 | 0.2082 | 0.6477 | 0.3251 | 0.0000 | -0.0000 | -0.0002 | precise_level_spread_q75 | 0.6262 |
| test | hcoef36_route_p95_near_all_cap0p0075_s0p2__precise_level_spread_q75 | 0.1382 | 0.2729 | 0.8062 | 0.3987 | -0.0006 | -0.0001 | -0.0002 | precise_level_spread_q75 | 0.5453 |
| 0604_ex50 | hcoef36_route_p95_near_all_cap0p0075_s0p2__precise_level_spread_q75 | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | precise_level_spread_q75 | 0.2123 |
| validation | hcoef36_route_p95_near_all_cap0p0075_s0p2__gap_q75 | 0.1253 | 0.2081 | 0.6476 | 0.3250 | -0.0006 | -0.0001 | -0.0004 | gap_q75 | 0.7495 |
| test | hcoef36_route_p95_near_all_cap0p0075_s0p2__gap_q75 | 0.1382 | 0.2729 | 0.8063 | 0.3988 | -0.0006 | -0.0000 | -0.0001 | gap_q75 | 0.7628 |
| 0604_ex50 | hcoef36_route_p95_near_all_cap0p0075_s0p2__gap_q75 | 0.2731 | 0.3745 | 0.9835 | 1.3077 | 0.0000 | 0.0001 | 0.0000 | gap_q75 | 0.6200 |
| validation | hcoef36_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q66 | 0.1260 | 0.2082 | 0.6477 | 0.3251 | 0.0000 | -0.0000 | -0.0002 | n_ge5_spread_q66 | 0.6590 |
| test | hcoef36_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q66 | 0.1382 | 0.2729 | 0.8062 | 0.3988 | -0.0006 | -0.0000 | -0.0002 | n_ge5_spread_q66 | 0.6211 |
| 0604_ex50 | hcoef36_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q66 | 0.2734 | 0.3743 | 0.9835 | 1.3078 | 0.0003 | -0.0000 | 0.0000 | n_ge5_spread_q66 | 0.4150 |
| validation | hcoef36_route_best_mdape_all_cap0p01_s0p35__spread_q66 | 0.1253 | 0.2081 | 0.6471 | 0.3249 | -0.0007 | -0.0001 | -0.0009 | spread_q66 | 0.6590 |
| test | hcoef36_route_best_mdape_all_cap0p01_s0p35__spread_q66 | 0.1383 | 0.2729 | 0.8059 | 0.3987 | -0.0005 | -0.0001 | -0.0005 | spread_q66 | 0.6211 |
| 0604_ex50 | hcoef36_route_best_mdape_all_cap0p01_s0p35__spread_q66 | 0.2734 | 0.3745 | 0.9837 | 1.3078 | 0.0003 | 0.0001 | 0.0003 | spread_q66 | 0.4813 |
| validation | hcoef36_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q66 | 0.1253 | 0.2081 | 0.6471 | 0.3249 | -0.0007 | -0.0001 | -0.0009 | n_ge5_spread_q66 | 0.6590 |
| test | hcoef36_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q66 | 0.1383 | 0.2729 | 0.8059 | 0.3987 | -0.0005 | -0.0001 | -0.0005 | n_ge5_spread_q66 | 0.6211 |
| 0604_ex50 | hcoef36_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q66 | 0.2734 | 0.3743 | 0.9835 | 1.3078 | 0.0003 | -0.0000 | 0.0000 | n_ge5_spread_q66 | 0.4150 |

## 3. 후보 판단

| candidate | extended_repeat_decision | base_improver | route_rule | route_coverage | test_MdAPE | test_MAPE | test_p95_APE | stress0604_MdAPE | stress0604_MAPE | stress0604_p95_APE | min_stable_any2_improve_prob | min_stable_all3_improve_prob | fixed_p95_margin_vs_stable | stress0604_p95_margin_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90 | Warm 안정 반복 검증 후보 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q66_area90 | 0.5865 | 0.1383 | 0.2729 | 0.8060 | 0.2734 | 0.3743 | 0.9835 | 0.9333 | 0.4333 | -0.0003 | -0.0000 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66 | Warm 안정 반복 검증 후보 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | spread_q66 | 0.6211 | 0.1383 | 0.2729 | 0.8060 | 0.2734 | 0.3744 | 0.9835 | 0.9333 | 0.4000 | -0.0003 | -0.0000 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66 | Warm 안정 반복 검증 후보 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q66 | 0.6211 | 0.1383 | 0.2729 | 0.8060 | 0.2734 | 0.3743 | 0.9835 | 0.9333 | 0.4000 | -0.0003 | -0.0000 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__spread_q66 | Warm 안정 반복 검증 후보 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | spread_q66 | 0.6211 | 0.1383 | 0.2729 | 0.8059 | 0.2734 | 0.3745 | 0.9837 | 0.9000 | 0.3167 | -0.0005 | 0.0003 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q66 | Warm 안정 반복 검증 후보 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | n_ge5_spread_q66 | 0.6211 | 0.1383 | 0.2729 | 0.8059 | 0.2734 | 0.3743 | 0.9835 | 0.9000 | 0.3167 | -0.0005 | -0.0000 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__gap_q75 | 기존 70:30 대비 p95 방어 후보 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | gap_q75 | 0.7628 | 0.1382 | 0.2729 | 0.8063 | 0.2731 | 0.3745 | 0.9835 | 0.8500 | 0.2833 | -0.0001 | -0.0000 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q66 | 기존 70:30 대비 p95 방어 후보 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | n_ge5_spread_q66 | 0.6211 | 0.1382 | 0.2729 | 0.8062 | 0.2734 | 0.3743 | 0.9835 | 0.4500 | 0.0667 | -0.0002 | -0.0000 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__precise_level_spread_q75 | 기존 70:30 대비 p95 방어 후보 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | precise_level_spread_q75 | 0.5453 | 0.1382 | 0.2729 | 0.8062 | 0.2731 | 0.3744 | 0.9835 | 0.4667 | 0.0500 | -0.0002 | -0.0000 |

## 4. 반복 OOF 요약

| validation_scheme | candidate | n_repeats | mean_MdAPE | mean_MAPE | mean_p95_APE | mean_delta_MdAPE_vs_stable | mean_delta_MAPE_vs_stable | mean_delta_p95_APE_vs_stable | stable_any2_improve_prob | stable_all3_improve_prob | stable_p95_improve_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| row_oof | hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66 | 60 | 0.1258 | 0.2082 | 0.6474 | -0.0002 | -0.0000 | -0.0005 | 0.9667 | 0.5667 | 0.9500 |
| row_oof | hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66 | 60 | 0.1258 | 0.2082 | 0.6474 | -0.0002 | -0.0000 | -0.0005 | 0.9667 | 0.5667 | 0.9500 |
| row_oof | hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90 | 60 | 0.1258 | 0.2082 | 0.6474 | -0.0002 | -0.0000 | -0.0005 | 0.9667 | 0.5333 | 0.9500 |
| row_oof | hcoef36_route_p95_near_all_cap0p0075_s0p2__gap_q75 | 60 | 0.1254 | 0.2082 | 0.6476 | -0.0006 | 0.0000 | -0.0004 | 0.9500 | 0.3167 | 0.9667 |
| artist_oof | hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90 | 60 | 0.1257 | 0.2082 | 0.6475 | -0.0003 | 0.0000 | -0.0005 | 0.9333 | 0.4333 | 0.9000 |
| artist_oof | hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66 | 60 | 0.1257 | 0.2082 | 0.6475 | -0.0003 | 0.0000 | -0.0005 | 0.9333 | 0.4000 | 0.9000 |
| artist_oof | hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66 | 60 | 0.1257 | 0.2082 | 0.6475 | -0.0003 | 0.0000 | -0.0005 | 0.9333 | 0.4000 | 0.9000 |
| artist_oof | hcoef36_route_best_mdape_all_cap0p01_s0p35__spread_q66 | 60 | 0.1253 | 0.2082 | 0.6472 | -0.0007 | 0.0000 | -0.0007 | 0.9167 | 0.3167 | 0.9000 |
| artist_oof | hcoef36_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q66 | 60 | 0.1253 | 0.2082 | 0.6472 | -0.0007 | 0.0000 | -0.0007 | 0.9167 | 0.3167 | 0.9000 |
| row_oof | hcoef36_route_best_mdape_all_cap0p01_s0p35__spread_q66 | 60 | 0.1253 | 0.2082 | 0.6472 | -0.0007 | -0.0000 | -0.0007 | 0.9000 | 0.5000 | 0.9500 |
| row_oof | hcoef36_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q66 | 60 | 0.1253 | 0.2082 | 0.6472 | -0.0007 | -0.0000 | -0.0007 | 0.9000 | 0.5000 | 0.9500 |
| artist_oof | hcoef36_route_p95_near_all_cap0p0075_s0p2__gap_q75 | 60 | 0.1256 | 0.2082 | 0.6476 | -0.0004 | 0.0000 | -0.0003 | 0.8500 | 0.2833 | 1.0000 |
| row_oof | hcoef36_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q66 | 60 | 0.1259 | 0.2082 | 0.6477 | -0.0001 | -0.0000 | -0.0002 | 0.6500 | 0.0833 | 0.9500 |
| row_oof | hcoef36_route_p95_near_all_cap0p0075_s0p2__precise_level_spread_q75 | 60 | 0.1259 | 0.2082 | 0.6477 | -0.0001 | 0.0000 | -0.0002 | 0.5833 | 0.0500 | 0.9500 |
| artist_oof | hcoef36_route_p95_near_all_cap0p0075_s0p2__precise_level_spread_q75 | 60 | 0.1259 | 0.2082 | 0.6477 | -0.0001 | 0.0000 | -0.0002 | 0.4667 | 0.0667 | 0.9000 |
| artist_oof | hcoef36_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q66 | 60 | 0.1259 | 0.2082 | 0.6477 | -0.0001 | 0.0000 | -0.0002 | 0.4500 | 0.0667 | 0.9000 |

## 5. 라우팅 정책

| candidate | split | route_rule | route_coverage | route_n | basis_component_spread_max | abs_fallback_stable_gap_max | log_area_min | log_area_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66 | validation | spread_q66 | 0.6590 | 342 | 1.0532 | nan | nan | nan |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66 | test | spread_q66 | 0.6211 | 377 | 1.0532 | nan | nan | nan |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66 | 0604_ex50 | spread_q66 | 0.4813 | 399 | 1.0532 | nan | nan | nan |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66 | validation | n_ge5_spread_q66 | 0.6590 | 342 | 1.0532 | nan | nan | nan |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66 | test | n_ge5_spread_q66 | 0.6211 | 377 | 1.0532 | nan | nan | nan |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66 | 0604_ex50 | n_ge5_spread_q66 | 0.4150 | 344 | 1.0532 | nan | nan | nan |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90 | validation | n_ge5_spread_q66_area90 | 0.6262 | 325 | 1.0532 | nan | 5.9339 | 9.9587 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90 | test | n_ge5_spread_q66_area90 | 0.5865 | 356 | 1.0532 | nan | 5.9339 | 9.9587 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90 | 0604_ex50 | n_ge5_spread_q66_area90 | 0.3872 | 321 | 1.0532 | nan | 5.9339 | 9.9587 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__precise_level_spread_q75 | validation | precise_level_spread_q75 | 0.6262 | 325 | 1.2319 | nan | nan | nan |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__precise_level_spread_q75 | test | precise_level_spread_q75 | 0.5453 | 331 | 1.2319 | nan | nan | nan |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__precise_level_spread_q75 | 0604_ex50 | precise_level_spread_q75 | 0.2123 | 176 | 1.2319 | nan | nan | nan |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__gap_q75 | validation | gap_q75 | 0.7495 | 389 | nan | 0.6607 | nan | nan |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__gap_q75 | test | gap_q75 | 0.7628 | 463 | nan | 0.6607 | nan | nan |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__gap_q75 | 0604_ex50 | gap_q75 | 0.6200 | 514 | nan | 0.6607 | nan | nan |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q66 | validation | n_ge5_spread_q66 | 0.6590 | 342 | 1.0532 | nan | nan | nan |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q66 | test | n_ge5_spread_q66 | 0.6211 | 377 | 1.0532 | nan | nan | nan |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q66 | 0604_ex50 | n_ge5_spread_q66 | 0.4150 | 344 | 1.0532 | nan | nan | nan |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__spread_q66 | validation | spread_q66 | 0.6590 | 342 | 1.0532 | nan | nan | nan |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__spread_q66 | test | spread_q66 | 0.6211 | 377 | 1.0532 | nan | nan | nan |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__spread_q66 | 0604_ex50 | spread_q66 | 0.4813 | 399 | 1.0532 | nan | nan | nan |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q66 | validation | n_ge5_spread_q66 | 0.6590 | 342 | 1.0532 | nan | nan | nan |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q66 | test | n_ge5_spread_q66 | 0.6211 | 377 | 1.0532 | nan | nan | nan |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q66 | 0604_ex50 | n_ge5_spread_q66 | 0.4150 | 344 | 1.0532 | nan | nan | nan |

## 6. Huber 계수 해석

- 계수는 HCOEF35 base improver의 residual Huber 모델 기준이다.
- 양수 계수는 stable 예측에 보정값을 더하는 방향이다.
- 음수 계수는 stable 예측에서 보정값을 빼는 방향이다.

| candidate | base_improver | route_rule | feature | coefficient_on_scaled_feature | direction |
| --- | --- | --- | --- | --- | --- |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | spread_q66 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q66 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q66 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | n_ge5_spread_q66 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__precise_level_spread_q75 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | precise_level_spread_q75 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q66_area90 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__gap_q75 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | gap_q75 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__spread_q66 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | spread_q66 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q66 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | n_ge5_spread_q66 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q66 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | n_ge5_spread_q66 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__precise_level_spread_q75 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | precise_level_spread_q75 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q66_area90 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q66 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__gap_q75 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | gap_q75 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | spread_q66 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q66 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | n_ge5_spread_q66 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__spread_q66 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | spread_q66 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | spread_q66 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q66 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__gap_q75 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | gap_q75 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q66_area90 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__precise_level_spread_q75 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | precise_level_spread_q75 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q66 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | n_ge5_spread_q66 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q66 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | n_ge5_spread_q66 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__spread_q66 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | spread_q66 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__precise_level_spread_q75 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | precise_level_spread_q75 | basis_component_spread | -0.0236 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q66 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | n_ge5_spread_q66 | basis_component_spread | -0.0236 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | spread_q66 | basis_component_spread | -0.0236 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__gap_q75 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | gap_q75 | basis_component_spread | -0.0236 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q66_area90 | basis_component_spread | -0.0236 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q66 | basis_component_spread | -0.0236 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__spread_q66 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | spread_q66 | basis_component_spread | -0.0236 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q66 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | n_ge5_spread_q66 | basis_component_spread | -0.0236 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q66 | log_area | -0.0231 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q66_area90 | log_area | -0.0231 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | spread_q66 | log_area | -0.0231 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__precise_level_spread_q75 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | precise_level_spread_q75 | log_area | -0.0231 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__gap_q75 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | gap_q75 | log_area | -0.0231 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q66 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | n_ge5_spread_q66 | log_area | -0.0231 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q66 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | n_ge5_spread_q66 | log_area | -0.0231 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__spread_q66 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | spread_q66 | log_area | -0.0231 | 예측 로그가격/보정값을 낮추는 방향 |

_상위 40개만 표시. 전체 80개._

## 7. 잔차와 큰 오차 확인

| split | candidate | n | median_residual_log | mean_residual_log | residual_std | ape_median | ape_mean | ape_p95 | ape_gt_100pct_n | over_2x_n | under_half_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | current_70_30 | 607 | -0.0006 | -0.0119 | 0.3998 | 0.1405 | 0.2748 | 0.8331 | 24 | 24 | 17 |
| test | hcoef_stable | 607 | -0.0039 | -0.0148 | 0.3989 | 0.1388 | 0.2730 | 0.8064 | 26 | 26 | 17 |
| 0604_ex50 | current_70_30 | 829 | 0.0782 | 0.3370 | 1.2685 | 0.2779 | 0.3774 | 0.9871 | 30 | 30 | 153 |
| 0604_ex50 | hcoef_stable | 829 | 0.0608 | 0.3278 | 1.2668 | 0.2731 | 0.3744 | 0.9835 | 26 | 26 | 152 |
| test | hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66 | 607 | -0.0030 | -0.0152 | 0.3988 | 0.1383 | 0.2729 | 0.8060 | 26 | 26 | 17 |
| 0604_ex50 | hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66 | 829 | 0.0608 | 0.3277 | 1.2668 | 0.2734 | 0.3744 | 0.9835 | 27 | 27 | 152 |
| test | hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66 | 607 | -0.0030 | -0.0152 | 0.3988 | 0.1383 | 0.2729 | 0.8060 | 26 | 26 | 17 |
| 0604_ex50 | hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66 | 829 | 0.0608 | 0.3278 | 1.2668 | 0.2734 | 0.3743 | 0.9835 | 26 | 26 | 152 |
| test | hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90 | 607 | -0.0030 | -0.0152 | 0.3988 | 0.1383 | 0.2729 | 0.8060 | 26 | 26 | 17 |
| 0604_ex50 | hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90 | 829 | 0.0608 | 0.3278 | 1.2668 | 0.2734 | 0.3743 | 0.9835 | 26 | 26 | 152 |
| test | hcoef36_route_p95_near_all_cap0p0075_s0p2__precise_level_spread_q75 | 607 | -0.0024 | -0.0149 | 0.3988 | 0.1382 | 0.2729 | 0.8062 | 26 | 26 | 17 |
| 0604_ex50 | hcoef36_route_p95_near_all_cap0p0075_s0p2__precise_level_spread_q75 | 829 | 0.0608 | 0.3278 | 1.2668 | 0.2731 | 0.3744 | 0.9835 | 26 | 26 | 152 |
| test | hcoef36_route_p95_near_all_cap0p0075_s0p2__gap_q75 | 607 | -0.0039 | -0.0149 | 0.3988 | 0.1382 | 0.2729 | 0.8063 | 26 | 26 | 17 |
| 0604_ex50 | hcoef36_route_p95_near_all_cap0p0075_s0p2__gap_q75 | 829 | 0.0623 | 0.3277 | 1.2668 | 0.2731 | 0.3745 | 0.9835 | 26 | 26 | 152 |
| test | hcoef36_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q66 | 607 | -0.0024 | -0.0150 | 0.3988 | 0.1382 | 0.2729 | 0.8062 | 26 | 26 | 17 |
| 0604_ex50 | hcoef36_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q66 | 829 | 0.0608 | 0.3278 | 1.2668 | 0.2734 | 0.3743 | 0.9835 | 26 | 26 | 152 |
| test | hcoef36_route_best_mdape_all_cap0p01_s0p35__spread_q66 | 607 | -0.0030 | -0.0154 | 0.3987 | 0.1383 | 0.2729 | 0.8059 | 26 | 26 | 17 |
| 0604_ex50 | hcoef36_route_best_mdape_all_cap0p01_s0p35__spread_q66 | 829 | 0.0608 | 0.3276 | 1.2668 | 0.2734 | 0.3745 | 0.9837 | 27 | 27 | 152 |
| test | hcoef36_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q66 | 607 | -0.0030 | -0.0154 | 0.3987 | 0.1383 | 0.2729 | 0.8059 | 26 | 26 | 17 |
| 0604_ex50 | hcoef36_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q66 | 829 | 0.0608 | 0.3279 | 1.2668 | 0.2734 | 0.3743 | 0.9835 | 26 | 26 | 152 |

## 8. 판단 기준

- 운영 후보: min stable all3 `0.95` 이상, fixed/0604 p95 방어, fixed test 3지표 모두 동등 또는 개선.
- 강한 반복 검증 후보: min stable all3 `0.90` 이상, fixed/0604 p95 방어.
- Warm 안정 반복 검증 후보: min stable any2 `0.90` 이상, fixed/0604 p95 방어.
- 기존 70:30 대비 p95 방어 후보: current_70_30 대비는 충분히 좋지만 hcoef_stable 반복 검증이 약한 후보.

## 9. 산출물

- `artifacts/experiment_config.json`
- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/policy_map.csv`
- `outputs/residual_analysis.csv`
- `outputs/repeated_iteration_metrics.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `outputs/selected_candidates.csv`