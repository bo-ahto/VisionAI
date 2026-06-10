# PP-HCOEF36 Warm Huber 목적별 라우팅 실험

- 작성일: 2026-06-08 08:22
- 목적: HCOEF34/35의 MdAPE/MAPE 개선 후보를 모든 행에 적용하지 않고, 기준가 신뢰도가 높은 행에만 적용해 p95 악화를 막을 수 있는지 확인.
- 기준 후보: `current_70_30`.
- 안정 비교 후보: `hcoef_stable`.
- 선택 원칙: validation/OOF 기반 rule과 Huber 계수만 사용. fixed test/0604는 확인용.

## 1. 실행 결론

- `hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66`를 Warm 안정 재검증 후보로 분리. test MdAPE/MAPE/p95 0.1383/0.2729/0.8060.
- HCOEF35의 개선 신호는 전체 교체보다 라우팅/신뢰도 정책으로 다루는 것이 더 적합함.

## 2. 기준 후보 지표

| split | candidate | method | n | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_reference | delta_MAPE_vs_reference | delta_p95_APE_vs_reference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | current_70_30 | baseline_reference | 519 | 0.1305 | 0.2110 | 0.6580 | 0.3292 | 0.0000 | 0.0000 | 0.0000 |
| validation | hcoef_stable | baseline_stable | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | -0.0045 | -0.0028 | -0.0101 |
| test | current_70_30 | baseline_reference | 607 | 0.1405 | 0.2748 | 0.8331 | 0.3996 | 0.0000 | 0.0000 | 0.0000 |
| test | hcoef_stable | baseline_stable | 607 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | -0.0017 | -0.0018 | -0.0267 |
| 0604_ex50 | current_70_30 | baseline_reference | 829 | 0.2779 | 0.3774 | 0.9871 | 1.3117 | 0.0000 | 0.0000 | 0.0000 |
| 0604_ex50 | hcoef_stable | baseline_stable | 829 | 0.2731 | 0.3744 | 0.9835 | 1.3078 | -0.0049 | -0.0030 | -0.0036 |

## 3. 선택 후보 판단

| candidate | decision | base_improver | route_rule | route_coverage | test_MdAPE | test_MAPE | test_p95_APE | fixed_p95_margin_vs_stable | stress0604_MdAPE | stress0604_MAPE | stress0604_p95_APE | row_oof_ref_any2_improve_prob | artist_oof_ref_any2_improve_prob | row_oof_stable_any2_improve_prob | artist_oof_stable_any2_improve_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66 | Warm 안정 후보 재검증 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | spread_q66 | 0.6211 | 0.1383 | 0.2729 | 0.8060 | -0.0003 | 0.2734 | 0.3744 | 0.9835 | 1.0000 | 1.0000 | 0.9167 | 0.9167 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66 | Warm 안정 후보 재검증 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q66 | 0.6211 | 0.1383 | 0.2729 | 0.8060 | -0.0003 | 0.2734 | 0.3743 | 0.9835 | 1.0000 | 1.0000 | 0.9167 | 0.9167 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90 | Warm 안정 후보 재검증 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q66_area90 | 0.5865 | 0.1383 | 0.2729 | 0.8060 | -0.0003 | 0.2734 | 0.3743 | 0.9835 | 1.0000 | 1.0000 | 0.9167 | 0.9167 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__precise_level_spread_q75 | p95 방어형 70:30 개선 후보 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | precise_level_spread_q75 | 0.5453 | 0.1382 | 0.2729 | 0.8062 | -0.0002 | 0.2731 | 0.3744 | 0.9835 | 1.0000 | 1.0000 | 0.5000 | 0.3750 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__spread_q66 | p95 방어형 70:30 개선 후보 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | spread_q66 | 0.6211 | 0.1382 | 0.2729 | 0.8062 | -0.0002 | 0.2734 | 0.3744 | 0.9835 | 1.0000 | 1.0000 | 0.5000 | 0.4167 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q66 | p95 방어형 70:30 개선 후보 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | n_ge5_spread_q66 | 0.6211 | 0.1382 | 0.2729 | 0.8062 | -0.0002 | 0.2734 | 0.3743 | 0.9835 | 1.0000 | 1.0000 | 0.5000 | 0.4167 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__gap_q75 | p95 방어형 70:30 개선 후보 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | gap_q75 | 0.7628 | 0.1382 | 0.2729 | 0.8063 | -0.0001 | 0.2731 | 0.3745 | 0.9835 | 1.0000 | 1.0000 | 0.8750 | 0.9167 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q66_area90 | p95 방어형 70:30 개선 후보 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | n_ge5_spread_q66_area90 | 0.5865 | 0.1382 | 0.2729 | 0.8062 | -0.0002 | 0.2734 | 0.3743 | 0.9835 | 1.0000 | 1.0000 | 0.4167 | 0.5000 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__spread_q50 | p95 방어형 70:30 개선 후보 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | spread_q50 | 0.4399 | 0.1382 | 0.2730 | 0.8062 | -0.0002 | 0.2734 | 0.3744 | 0.9835 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__spread_q66 | p95 방어형 70:30 개선 후보 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | spread_q66 | 0.6211 | 0.1383 | 0.2729 | 0.8059 | -0.0005 | 0.2734 | 0.3745 | 0.9837 | 1.0000 | 1.0000 | 0.8333 | 0.8750 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q66 | p95 방어형 70:30 개선 후보 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | n_ge5_spread_q66 | 0.6211 | 0.1383 | 0.2729 | 0.8059 | -0.0005 | 0.2734 | 0.3743 | 0.9835 | 1.0000 | 1.0000 | 0.8333 | 0.8750 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__spread_q50 | p95 방어형 70:30 개선 후보 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | spread_q50 | 0.4399 | 0.1383 | 0.2729 | 0.8059 | -0.0005 | 0.2734 | 0.3746 | 0.9837 | 1.0000 | 1.0000 | 0.0417 | 0.0833 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q66_area90 | p95 방어형 70:30 개선 후보 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | n_ge5_spread_q66_area90 | 0.5865 | 0.1383 | 0.2729 | 0.8059 | -0.0005 | 0.2734 | 0.3743 | 0.9835 | 1.0000 | 1.0000 | 0.7917 | 0.8750 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q50 | p95 방어형 70:30 개선 후보 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | spread_q50 | 0.4399 | 0.1383 | 0.2729 | 0.8060 | -0.0003 | 0.2734 | 0.3745 | 0.9835 | 1.0000 | 1.0000 | 0.1250 | 0.1667 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__precise_level_spread_q75 | p95 방어형 70:30 개선 후보 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | precise_level_spread_q75 | 0.5453 | 0.1387 | 0.2728 | 0.8059 | -0.0005 | 0.2731 | 0.3744 | 0.9835 | 1.0000 | 1.0000 | 0.4583 | 0.7083 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__precise_level_spread_q75 | p95 방어형 70:30 개선 후보 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | precise_level_spread_q75 | 0.5453 | 0.1388 | 0.2728 | 0.8060 | -0.0003 | 0.2731 | 0.3744 | 0.9835 | 1.0000 | 1.0000 | 0.4583 | 0.3750 |
| hcoef36_route_core_oof_core_cap0p0075_s0p35__coarse_artist_gap_q66 | p95 방어형 70:30 개선 후보 | hcoef35_core_oof_basis_resid_core_a0p01_cap0p0075_s0p35 | coarse_artist_gap_q66 | 0.0906 | 0.1388 | 0.2730 | 0.8064 | 0.0000 | 0.2731 | 0.3744 | 0.9835 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef36_route_core_balanced_core_cap0p005_s0p5__coarse_artist_gap_q66 | p95 방어형 70:30 개선 후보 | hcoef35_core_balanced_basis_resid_core_a0p001_cap0p005_s0p5 | coarse_artist_gap_q66 | 0.0906 | 0.1388 | 0.2730 | 0.8064 | 0.0000 | 0.2731 | 0.3744 | 0.9835 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__coarse_artist_gap_q66 | p95 방어형 70:30 개선 후보 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | coarse_artist_gap_q66 | 0.0906 | 0.1388 | 0.2730 | 0.8064 | 0.0000 | 0.2731 | 0.3744 | 0.9835 | 1.0000 | 1.0000 | 0.6667 | 0.8333 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__coarse_artist_gap_q66 | p95 방어형 70:30 개선 후보 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | coarse_artist_gap_q66 | 0.0906 | 0.1388 | 0.2730 | 0.8064 | 0.0000 | 0.2731 | 0.3745 | 0.9835 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__coarse_artist_gap_q66 | p95 방어형 70:30 개선 후보 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | coarse_artist_gap_q66 | 0.0906 | 0.1388 | 0.2730 | 0.8064 | 0.0000 | 0.2731 | 0.3745 | 0.9835 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__all_rows | 기존 70:30 대비 개선 후보 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | all_rows | 1.0000 | 0.1365 | 0.2729 | 0.8078 | 0.0014 | 0.2756 | 0.3747 | 0.9837 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__n_ge5 | 기존 70:30 대비 개선 후보 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | n_ge5 | 1.0000 | 0.1365 | 0.2729 | 0.8078 | 0.0014 | 0.2756 | 0.3747 | 0.9837 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef36_route_core_oof_core_cap0p0075_s0p35__spread_q75 | 기존 70:30 대비 개선 후보 | hcoef35_core_oof_basis_resid_core_a0p01_cap0p0075_s0p35 | spread_q75 | 0.7133 | 0.1372 | 0.2730 | 0.8081 | 0.0018 | 0.2734 | 0.3745 | 0.9835 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef36_route_core_oof_core_cap0p0075_s0p35__all_rows | 기존 70:30 대비 개선 후보 | hcoef35_core_oof_basis_resid_core_a0p01_cap0p0075_s0p35 | all_rows | 1.0000 | 0.1372 | 0.2730 | 0.8081 | 0.0018 | 0.2747 | 0.3746 | 0.9835 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef36_route_core_oof_core_cap0p0075_s0p35__n_ge5 | 기존 70:30 대비 개선 후보 | hcoef35_core_oof_basis_resid_core_a0p01_cap0p0075_s0p35 | n_ge5 | 1.0000 | 0.1372 | 0.2730 | 0.8081 | 0.0018 | 0.2747 | 0.3746 | 0.9835 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__all_rows | 기존 70:30 대비 개선 후보 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | all_rows | 1.0000 | 0.1373 | 0.2729 | 0.8074 | 0.0010 | 0.2749 | 0.3746 | 0.9835 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5 | 기존 70:30 대비 개선 후보 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5 | 1.0000 | 0.1373 | 0.2729 | 0.8074 | 0.0010 | 0.2749 | 0.3746 | 0.9835 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef36_route_core_balanced_core_cap0p005_s0p5__spread_q75 | 기존 70:30 대비 개선 후보 | hcoef35_core_balanced_basis_resid_core_a0p001_cap0p005_s0p5 | spread_q75 | 0.7133 | 0.1373 | 0.2730 | 0.8081 | 0.0017 | 0.2734 | 0.3745 | 0.9835 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hcoef36_route_core_balanced_core_cap0p005_s0p5__all_rows | 기존 70:30 대비 개선 후보 | hcoef35_core_balanced_basis_resid_core_a0p001_cap0p005_s0p5 | all_rows | 1.0000 | 0.1373 | 0.2730 | 0.8081 | 0.0017 | 0.2746 | 0.3746 | 0.9835 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

_상위 30개만 표시. 전체 65개._

## 4. 라우팅 정책 요약

| candidate | decision | base_improver | route_rule | route_coverage | route_n | basis_component_spread_max | abs_fallback_stable_gap_max | log_area_min | log_area_max | test_MdAPE | test_MAPE | test_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66 | Warm 안정 후보 재검증 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | spread_q66 | 0.6211 | 377 | 1.0532 | nan | nan | nan | 0.1383 | 0.2729 | 0.8060 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66 | Warm 안정 후보 재검증 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q66 | 0.6211 | 377 | 1.0532 | nan | nan | nan | 0.1383 | 0.2729 | 0.8060 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90 | Warm 안정 후보 재검증 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q66_area90 | 0.5865 | 356 | 1.0532 | nan | 5.9339 | 9.9587 | 0.1383 | 0.2729 | 0.8060 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__precise_level_spread_q75 | p95 방어형 70:30 개선 후보 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | precise_level_spread_q75 | 0.5453 | 331 | 1.2319 | nan | nan | nan | 0.1382 | 0.2729 | 0.8062 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__spread_q66 | p95 방어형 70:30 개선 후보 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | spread_q66 | 0.6211 | 377 | 1.0532 | nan | nan | nan | 0.1382 | 0.2729 | 0.8062 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q66 | p95 방어형 70:30 개선 후보 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | n_ge5_spread_q66 | 0.6211 | 377 | 1.0532 | nan | nan | nan | 0.1382 | 0.2729 | 0.8062 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__gap_q75 | p95 방어형 70:30 개선 후보 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | gap_q75 | 0.7628 | 463 | nan | 0.6607 | nan | nan | 0.1382 | 0.2729 | 0.8063 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q66_area90 | p95 방어형 70:30 개선 후보 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | n_ge5_spread_q66_area90 | 0.5865 | 356 | 1.0532 | nan | 5.9339 | 9.9587 | 0.1382 | 0.2729 | 0.8062 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__spread_q50 | p95 방어형 70:30 개선 후보 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | spread_q50 | 0.4399 | 267 | 0.6969 | nan | nan | nan | 0.1382 | 0.2730 | 0.8062 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__spread_q66 | p95 방어형 70:30 개선 후보 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | spread_q66 | 0.6211 | 377 | 1.0532 | nan | nan | nan | 0.1383 | 0.2729 | 0.8059 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q66 | p95 방어형 70:30 개선 후보 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | n_ge5_spread_q66 | 0.6211 | 377 | 1.0532 | nan | nan | nan | 0.1383 | 0.2729 | 0.8059 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__spread_q50 | p95 방어형 70:30 개선 후보 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | spread_q50 | 0.4399 | 267 | 0.6969 | nan | nan | nan | 0.1383 | 0.2729 | 0.8059 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q66_area90 | p95 방어형 70:30 개선 후보 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | n_ge5_spread_q66_area90 | 0.5865 | 356 | 1.0532 | nan | 5.9339 | 9.9587 | 0.1383 | 0.2729 | 0.8059 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q50 | p95 방어형 70:30 개선 후보 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | spread_q50 | 0.4399 | 267 | 0.6969 | nan | nan | nan | 0.1383 | 0.2729 | 0.8060 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__precise_level_spread_q75 | p95 방어형 70:30 개선 후보 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | precise_level_spread_q75 | 0.5453 | 331 | 1.2319 | nan | nan | nan | 0.1387 | 0.2728 | 0.8059 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__precise_level_spread_q75 | p95 방어형 70:30 개선 후보 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | precise_level_spread_q75 | 0.5453 | 331 | 1.2319 | nan | nan | nan | 0.1388 | 0.2728 | 0.8060 |
| hcoef36_route_core_oof_core_cap0p0075_s0p35__coarse_artist_gap_q66 | p95 방어형 70:30 개선 후보 | hcoef35_core_oof_basis_resid_core_a0p01_cap0p0075_s0p35 | coarse_artist_gap_q66 | 0.0906 | 55 | nan | 0.4871 | nan | nan | 0.1388 | 0.2730 | 0.8064 |
| hcoef36_route_core_balanced_core_cap0p005_s0p5__coarse_artist_gap_q66 | p95 방어형 70:30 개선 후보 | hcoef35_core_balanced_basis_resid_core_a0p001_cap0p005_s0p5 | coarse_artist_gap_q66 | 0.0906 | 55 | nan | 0.4871 | nan | nan | 0.1388 | 0.2730 | 0.8064 |
| hcoef36_route_p95_near_all_cap0p0075_s0p2__coarse_artist_gap_q66 | p95 방어형 70:30 개선 후보 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | coarse_artist_gap_q66 | 0.0906 | 55 | nan | 0.4871 | nan | nan | 0.1388 | 0.2730 | 0.8064 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__coarse_artist_gap_q66 | p95 방어형 70:30 개선 후보 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | coarse_artist_gap_q66 | 0.0906 | 55 | nan | 0.4871 | nan | nan | 0.1388 | 0.2730 | 0.8064 |

## 5. 반복 OOF 요약

| candidate | validation_scheme | n_repeats | mean_MdAPE | mean_MAPE | mean_p95_APE | ref_any2_improve_prob | stable_any2_improve_prob | stable_all3_improve_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef36_route_core_oof_core_cap0p0075_s0p35__all_rows | row_oof | 24 | 0.1244 | 0.2081 | 0.6438 | 1.0000 | 1.0000 | 1.0000 |
| hcoef36_route_core_oof_core_cap0p0075_s0p35__n_ge5 | row_oof | 24 | 0.1244 | 0.2081 | 0.6438 | 1.0000 | 1.0000 | 1.0000 |
| hcoef36_route_core_oof_core_cap0p0075_s0p35__spread_q75 | row_oof | 24 | 0.1244 | 0.2082 | 0.6473 | 1.0000 | 1.0000 | 0.9583 |
| hcoef36_route_core_oof_core_cap0p0075_s0p35__all_rows | artist_oof | 24 | 0.1244 | 0.2081 | 0.6438 | 1.0000 | 1.0000 | 0.9167 |
| hcoef36_route_core_oof_core_cap0p0075_s0p35__n_ge5 | artist_oof | 24 | 0.1244 | 0.2081 | 0.6438 | 1.0000 | 1.0000 | 0.9167 |
| hcoef36_route_core_balanced_core_cap0p005_s0p5__all_rows | row_oof | 24 | 0.1244 | 0.2081 | 0.6440 | 1.0000 | 1.0000 | 1.0000 |
| hcoef36_route_core_balanced_core_cap0p005_s0p5__n_ge5 | row_oof | 24 | 0.1244 | 0.2081 | 0.6440 | 1.0000 | 1.0000 | 1.0000 |
| hcoef36_route_core_oof_core_cap0p0075_s0p35__spread_q50 | row_oof | 24 | 0.1244 | 0.2082 | 0.6479 | 1.0000 | 1.0000 | 0.0000 |
| hcoef36_route_core_balanced_core_cap0p005_s0p5__spread_q75 | row_oof | 24 | 0.1245 | 0.2082 | 0.6474 | 1.0000 | 1.0000 | 0.9583 |
| hcoef36_route_core_balanced_core_cap0p005_s0p5__all_rows | artist_oof | 24 | 0.1245 | 0.2081 | 0.6440 | 1.0000 | 1.0000 | 0.8333 |
| hcoef36_route_core_balanced_core_cap0p005_s0p5__n_ge5 | artist_oof | 24 | 0.1245 | 0.2081 | 0.6440 | 1.0000 | 1.0000 | 0.8333 |
| hcoef36_route_core_balanced_core_cap0p005_s0p5__spread_q50 | row_oof | 24 | 0.1245 | 0.2082 | 0.6479 | 1.0000 | 1.0000 | 0.0000 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__all_rows | row_oof | 24 | 0.1246 | 0.2082 | 0.6441 | 1.0000 | 1.0000 | 0.4583 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5 | row_oof | 24 | 0.1246 | 0.2082 | 0.6441 | 1.0000 | 1.0000 | 0.4583 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__all_rows | artist_oof | 24 | 0.1247 | 0.2082 | 0.6442 | 1.0000 | 1.0000 | 0.4167 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5 | artist_oof | 24 | 0.1247 | 0.2082 | 0.6442 | 1.0000 | 1.0000 | 0.4167 |
| hcoef36_route_core_oof_core_cap0p0075_s0p35__spread_q75 | artist_oof | 24 | 0.1248 | 0.2082 | 0.6473 | 1.0000 | 1.0000 | 0.7500 |
| hcoef36_route_core_balanced_core_cap0p005_s0p5__spread_q75 | artist_oof | 24 | 0.1249 | 0.2082 | 0.6474 | 1.0000 | 1.0000 | 0.7917 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__all_rows | artist_oof | 24 | 0.1250 | 0.2083 | 0.6443 | 1.0000 | 1.0000 | 0.3750 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__n_ge5 | artist_oof | 24 | 0.1250 | 0.2083 | 0.6443 | 1.0000 | 1.0000 | 0.3750 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__all_rows | row_oof | 24 | 0.1251 | 0.2082 | 0.6442 | 1.0000 | 1.0000 | 0.4583 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__n_ge5 | row_oof | 24 | 0.1251 | 0.2082 | 0.6442 | 1.0000 | 1.0000 | 0.4583 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__gap_q66 | artist_oof | 24 | 0.1253 | 0.2083 | 0.6449 | 1.0000 | 1.0000 | 0.2083 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__gap_q75 | artist_oof | 24 | 0.1253 | 0.2083 | 0.6449 | 1.0000 | 1.0000 | 0.1667 |
| hcoef36_route_best_mdape_all_cap0p01_s0p35__n_ge5_gap_q66 | artist_oof | 24 | 0.1253 | 0.2083 | 0.6449 | 1.0000 | 1.0000 | 0.2083 |
| hcoef36_route_core_oof_core_cap0p0075_s0p35__gap_q66 | row_oof | 24 | 0.1253 | 0.2081 | 0.6461 | 1.0000 | 1.0000 | 0.9167 |
| hcoef36_route_core_oof_core_cap0p0075_s0p35__gap_q75 | row_oof | 24 | 0.1253 | 0.2081 | 0.6459 | 1.0000 | 1.0000 | 0.9583 |
| hcoef36_route_core_oof_core_cap0p0075_s0p35__n_ge5_gap_q66 | row_oof | 24 | 0.1253 | 0.2081 | 0.6461 | 1.0000 | 1.0000 | 0.9167 |
| hcoef36_route_core_balanced_core_cap0p005_s0p5__gap_q66 | row_oof | 24 | 0.1253 | 0.2082 | 0.6463 | 1.0000 | 1.0000 | 0.9583 |
| hcoef36_route_core_balanced_core_cap0p005_s0p5__gap_q75 | row_oof | 24 | 0.1253 | 0.2081 | 0.6461 | 1.0000 | 1.0000 | 0.9583 |

_상위 30개만 표시. 전체 130개._

## 6. Huber 계수 해석

- 계수는 라우팅에 들어간 base improver의 Huber residual model 기준.
- 양수 계수는 stable 예측에 보정값을 더하는 방향, 음수 계수는 낮추는 방향.

| candidate | base_improver | route_rule | feature | coefficient_on_scaled_feature | direction |
| --- | --- | --- | --- | --- | --- |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__all_rows | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | all_rows | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__all_rows | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | all_rows | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__all_rows | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | all_rows | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__all_rows | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | all_rows | basis_component_spread | -0.0236 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__all_rows | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | all_rows | log_area | -0.0231 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__coarse_artist_gap_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | coarse_artist_gap_q66 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__coarse_artist_gap_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | coarse_artist_gap_q66 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__coarse_artist_gap_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | coarse_artist_gap_q66 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__coarse_artist_gap_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | coarse_artist_gap_q66 | basis_component_spread | -0.0236 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__coarse_artist_gap_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | coarse_artist_gap_q66 | log_area | -0.0231 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__gap_q50 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | gap_q50 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__gap_q50 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | gap_q50 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__gap_q50 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | gap_q50 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__gap_q50 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | gap_q50 | basis_component_spread | -0.0236 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__gap_q50 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | gap_q50 | log_area | -0.0231 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__gap_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | gap_q66 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__gap_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | gap_q66 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__gap_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | gap_q66 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__gap_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | gap_q66 | basis_component_spread | -0.0236 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__gap_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | gap_q66 | log_area | -0.0231 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__gap_q75 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | gap_q75 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__gap_q75 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | gap_q75 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__gap_q75 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | gap_q75 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__gap_q75 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | gap_q75 | basis_component_spread | -0.0236 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__gap_q75 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | gap_q75 | log_area | -0.0231 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5 | basis_component_spread | -0.0236 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5 | log_area | -0.0231 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_gap_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_gap_q66 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_gap_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_gap_q66 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_gap_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_gap_q66 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_gap_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_gap_q66 | basis_component_spread | -0.0236 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_gap_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_gap_q66 | log_area | -0.0231 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q66 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q66 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q66 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q66 | basis_component_spread | -0.0236 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q66 | log_area | -0.0231 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q66_area90 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q66_area90 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q66_area90 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q66_area90 | basis_component_spread | -0.0236 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q66_area90 | log_area | -0.0231 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__precise_level_spread_q75 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | precise_level_spread_q75 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__precise_level_spread_q75 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | precise_level_spread_q75 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__precise_level_spread_q75 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | precise_level_spread_q75 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__precise_level_spread_q75 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | precise_level_spread_q75 | basis_component_spread | -0.0236 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__precise_level_spread_q75 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | precise_level_spread_q75 | log_area | -0.0231 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q50 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | spread_q50 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q50 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | spread_q50 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q50 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | spread_q50 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q50 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | spread_q50 | basis_component_spread | -0.0236 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q50 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | spread_q50 | log_area | -0.0231 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | spread_q66 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | spread_q66 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | spread_q66 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | spread_q66 | basis_component_spread | -0.0236 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | spread_q66 | log_area | -0.0231 | 예측 로그가격/보정값을 낮추는 방향 |

_상위 60개만 표시. 전체 325개._

## 7. 잔차/큰 오차 요약

| split | candidate | n | median_residual_log | mean_residual_log | residual_std | ape_median | ape_mean | ape_p95 | ape_gt_100pct_n | over_2x_n | under_half_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | current_70_30 | 607 | -0.0006 | -0.0119 | 0.3998 | 0.1405 | 0.2748 | 0.8331 | 24 | 24 | 17 |
| test | hcoef_stable | 607 | -0.0039 | -0.0148 | 0.3989 | 0.1388 | 0.2730 | 0.8064 | 26 | 26 | 17 |
| 0604_ex50 | current_70_30 | 829 | 0.0782 | 0.3370 | 1.2685 | 0.2779 | 0.3774 | 0.9871 | 30 | 30 | 153 |
| 0604_ex50 | hcoef_stable | 829 | 0.0608 | 0.3278 | 1.2668 | 0.2731 | 0.3744 | 0.9835 | 26 | 26 | 152 |
| test | hcoef36_route_best_mdape_all_cap0p01_s0p35__spread_q50 | 607 | -0.0027 | -0.0152 | 0.3988 | 0.1383 | 0.2729 | 0.8059 | 26 | 26 | 17 |
| 0604_ex50 | hcoef36_route_best_mdape_all_cap0p01_s0p35__spread_q50 | 829 | 0.0608 | 0.3275 | 1.2669 | 0.2734 | 0.3746 | 0.9837 | 27 | 27 | 152 |
| test | hcoef36_route_best_mdape_all_cap0p01_s0p35__spread_q66 | 607 | -0.0030 | -0.0154 | 0.3987 | 0.1383 | 0.2729 | 0.8059 | 26 | 26 | 17 |
| 0604_ex50 | hcoef36_route_best_mdape_all_cap0p01_s0p35__spread_q66 | 829 | 0.0608 | 0.3276 | 1.2668 | 0.2734 | 0.3745 | 0.9837 | 27 | 27 | 152 |
| test | hcoef36_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q66 | 607 | -0.0030 | -0.0154 | 0.3987 | 0.1383 | 0.2729 | 0.8059 | 26 | 26 | 17 |
| 0604_ex50 | hcoef36_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q66 | 829 | 0.0608 | 0.3279 | 1.2668 | 0.2734 | 0.3743 | 0.9835 | 26 | 26 | 152 |
| test | hcoef36_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q66_area90 | 607 | -0.0030 | -0.0153 | 0.3987 | 0.1383 | 0.2729 | 0.8059 | 26 | 26 | 17 |
| 0604_ex50 | hcoef36_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q66_area90 | 829 | 0.0608 | 0.3278 | 1.2668 | 0.2734 | 0.3743 | 0.9835 | 26 | 26 | 152 |
| test | hcoef36_route_best_mdape_all_cap0p01_s0p35__precise_level_spread_q75 | 607 | -0.0030 | -0.0151 | 0.3986 | 0.1387 | 0.2728 | 0.8059 | 26 | 26 | 17 |
| 0604_ex50 | hcoef36_route_best_mdape_all_cap0p01_s0p35__precise_level_spread_q75 | 829 | 0.0608 | 0.3279 | 1.2668 | 0.2731 | 0.3744 | 0.9835 | 26 | 26 | 152 |
| test | hcoef36_route_p95_near_all_cap0p0075_s0p2__spread_q50 | 607 | -0.0024 | -0.0150 | 0.3988 | 0.1382 | 0.2730 | 0.8062 | 26 | 26 | 17 |
| 0604_ex50 | hcoef36_route_p95_near_all_cap0p0075_s0p2__spread_q50 | 829 | 0.0608 | 0.3277 | 1.2668 | 0.2734 | 0.3744 | 0.9835 | 26 | 26 | 152 |
| test | hcoef36_route_p95_near_all_cap0p0075_s0p2__spread_q66 | 607 | -0.0024 | -0.0150 | 0.3988 | 0.1382 | 0.2729 | 0.8062 | 26 | 26 | 17 |
| 0604_ex50 | hcoef36_route_p95_near_all_cap0p0075_s0p2__spread_q66 | 829 | 0.0608 | 0.3277 | 1.2668 | 0.2734 | 0.3744 | 0.9835 | 26 | 26 | 152 |
| test | hcoef36_route_p95_near_all_cap0p0075_s0p2__gap_q75 | 607 | -0.0039 | -0.0149 | 0.3988 | 0.1382 | 0.2729 | 0.8063 | 26 | 26 | 17 |
| 0604_ex50 | hcoef36_route_p95_near_all_cap0p0075_s0p2__gap_q75 | 829 | 0.0623 | 0.3277 | 1.2668 | 0.2731 | 0.3745 | 0.9835 | 26 | 26 | 152 |
| test | hcoef36_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q66 | 607 | -0.0024 | -0.0150 | 0.3988 | 0.1382 | 0.2729 | 0.8062 | 26 | 26 | 17 |
| 0604_ex50 | hcoef36_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q66 | 829 | 0.0608 | 0.3278 | 1.2668 | 0.2734 | 0.3743 | 0.9835 | 26 | 26 | 152 |
| test | hcoef36_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q66_area90 | 607 | -0.0024 | -0.0150 | 0.3988 | 0.1382 | 0.2729 | 0.8062 | 26 | 26 | 17 |
| 0604_ex50 | hcoef36_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q66_area90 | 829 | 0.0608 | 0.3278 | 1.2668 | 0.2734 | 0.3743 | 0.9835 | 26 | 26 | 152 |
| test | hcoef36_route_p95_near_all_cap0p0075_s0p2__precise_level_spread_q75 | 607 | -0.0024 | -0.0149 | 0.3988 | 0.1382 | 0.2729 | 0.8062 | 26 | 26 | 17 |
| 0604_ex50 | hcoef36_route_p95_near_all_cap0p0075_s0p2__precise_level_spread_q75 | 829 | 0.0608 | 0.3278 | 1.2668 | 0.2731 | 0.3744 | 0.9835 | 26 | 26 | 152 |
| test | hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q50 | 607 | -0.0017 | -0.0151 | 0.3988 | 0.1383 | 0.2729 | 0.8060 | 26 | 26 | 17 |
| 0604_ex50 | hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q50 | 829 | 0.0608 | 0.3276 | 1.2668 | 0.2734 | 0.3745 | 0.9835 | 27 | 27 | 152 |
| test | hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66 | 607 | -0.0030 | -0.0152 | 0.3988 | 0.1383 | 0.2729 | 0.8060 | 26 | 26 | 17 |
| 0604_ex50 | hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66 | 829 | 0.0608 | 0.3277 | 1.2668 | 0.2734 | 0.3744 | 0.9835 | 27 | 27 | 152 |
| test | hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66 | 607 | -0.0030 | -0.0152 | 0.3988 | 0.1383 | 0.2729 | 0.8060 | 26 | 26 | 17 |
| 0604_ex50 | hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66 | 829 | 0.0608 | 0.3278 | 1.2668 | 0.2734 | 0.3743 | 0.9835 | 26 | 26 | 152 |
| test | hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90 | 607 | -0.0030 | -0.0152 | 0.3988 | 0.1383 | 0.2729 | 0.8060 | 26 | 26 | 17 |
| 0604_ex50 | hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90 | 829 | 0.0608 | 0.3278 | 1.2668 | 0.2734 | 0.3743 | 0.9835 | 26 | 26 | 152 |

## 8. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/policy_map.csv`
- `outputs/residual_analysis.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `outputs/selected_candidates.csv`
- `artifacts/experiment_config.json`