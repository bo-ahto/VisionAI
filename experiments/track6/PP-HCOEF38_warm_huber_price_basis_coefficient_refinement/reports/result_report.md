# PP-HCOEF38 Warm Huber stricter low-risk routing 실험

- 작성일: 2026-06-08 09:33
- 목적: HCOEF37에서 any2 안정성은 확인됐지만 all3가 약했던 low-risk routing 후보를 더 엄격한 구간에만 적용해 all3 안정성이 올라가는지 확인.
- 기준 후보: `current_70_30`.
- 운영 비교 후보: `hcoef_stable`.
- 반복 수: row OOF `60`회, artist OOF `60`회.
- 선택 원칙: 라우팅 경계는 validation/OOF 기반 quantile과 표본 수 조건만 사용. fixed test/0604 residual은 사용하지 않음.

## 1. 실행 결론

- 최상위 후보: `hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q66_area80`.
- 판단: 기존 70:30 대비 p95 방어 후보.
- fixed test MdAPE/MAPE/p95: `0.138803/0.272806/0.806366`.
- hcoef_stable 대비 fixed delta MdAPE/MAPE/p95: `0.000000/-0.000183/0.000000`.
- row/artist min stable any2/all3: `0.7167/0.2167`.
- HCOEF38은 더 많은 피처를 넣는 실험이 아니라 적용 구간을 더 보수적으로 줄이는 실험이다.

## 2. fixed test / 0604 확인 지표

| split | candidate | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable | route_rule | route_coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | current_70_30 | 0.1305 | 0.2110 | 0.6580 | 0.3292 | 0.0045 | 0.0028 | 0.0101 | nan | nan |
| validation | hcoef_stable | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | nan | nan |
| test | current_70_30 | 0.1405 | 0.2748 | 0.8331 | 0.3996 | 0.0017 | 0.0018 | 0.0267 | nan | nan |
| test | hcoef_stable | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | nan | nan |
| 0604_ex50 | current_70_30 | 0.2779 | 0.3774 | 0.9871 | 1.3117 | 0.0049 | 0.0030 | 0.0036 | nan | nan |
| 0604_ex50 | hcoef_stable | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | nan | nan |
| validation | hcoef38_route_basis_balanced_all_cap0p005_s0p5__spread_q50 | 0.1259 | 0.2082 | 0.6479 | 0.3251 | -0.0001 | -0.0000 | 0.0000 | spread_q50 | 0.5010 |
| test | hcoef38_route_basis_balanced_all_cap0p005_s0p5__spread_q50 | 0.1383 | 0.2729 | 0.8060 | 0.3988 | -0.0005 | -0.0000 | -0.0003 | spread_q50 | 0.4399 |
| 0604_ex50 | hcoef38_route_basis_balanced_all_cap0p005_s0p5__spread_q50 | 0.2734 | 0.3745 | 0.9835 | 1.3078 | 0.0003 | 0.0001 | 0.0000 | spread_q50 | 0.2750 |
| validation | hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50 | 0.1259 | 0.2082 | 0.6479 | 0.3251 | -0.0001 | -0.0000 | 0.0000 | n_ge5_spread_q50 | 0.5010 |
| test | hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50 | 0.1383 | 0.2729 | 0.8060 | 0.3988 | -0.0005 | -0.0000 | -0.0003 | n_ge5_spread_q50 | 0.4399 |
| 0604_ex50 | hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50 | 0.2734 | 0.3744 | 0.9835 | 1.3078 | 0.0003 | 0.0000 | 0.0000 | n_ge5_spread_q50 | 0.2280 |
| validation | hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50_area80 | 0.1259 | 0.2082 | 0.6479 | 0.3251 | -0.0001 | -0.0000 | 0.0000 | n_ge5_spread_q50_area80 | 0.4509 |
| test | hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50_area80 | 0.1383 | 0.2730 | 0.8064 | 0.3988 | -0.0005 | 0.0000 | 0.0000 | n_ge5_spread_q50_area80 | 0.3773 |
| 0604_ex50 | hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50_area80 | 0.2734 | 0.3744 | 0.9835 | 1.3078 | 0.0003 | 0.0000 | 0.0000 | n_ge5_spread_q50_area80 | 0.1846 |
| validation | hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge10_spread_q66_area80 | 0.1260 | 0.2081 | 0.6474 | 0.3252 | 0.0000 | -0.0001 | -0.0006 | n_ge10_spread_q66_area80 | 0.2331 |
| test | hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge10_spread_q66_area80 | 0.1388 | 0.2729 | 0.8064 | 0.3988 | 0.0000 | -0.0001 | 0.0000 | n_ge10_spread_q66_area80 | 0.2306 |
| 0604_ex50 | hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge10_spread_q66_area80 | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | n_ge10_spread_q66_area80 | 0.1363 |
| validation | hcoef38_route_best_mdape_all_cap0p01_s0p35__spread_q50 | 0.1253 | 0.2082 | 0.6479 | 0.3250 | -0.0007 | 0.0000 | 0.0000 | spread_q50 | 0.5010 |
| test | hcoef38_route_best_mdape_all_cap0p01_s0p35__spread_q50 | 0.1383 | 0.2729 | 0.8059 | 0.3988 | -0.0005 | -0.0001 | -0.0005 | spread_q50 | 0.4399 |
| 0604_ex50 | hcoef38_route_best_mdape_all_cap0p01_s0p35__spread_q50 | 0.2734 | 0.3746 | 0.9837 | 1.3078 | 0.0003 | 0.0002 | 0.0003 | spread_q50 | 0.2750 |
| validation | hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q50 | 0.1253 | 0.2082 | 0.6479 | 0.3250 | -0.0007 | 0.0000 | 0.0000 | n_ge5_spread_q50 | 0.5010 |
| test | hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q50 | 0.1383 | 0.2729 | 0.8059 | 0.3988 | -0.0005 | -0.0001 | -0.0005 | n_ge5_spread_q50 | 0.4399 |
| 0604_ex50 | hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q50 | 0.2734 | 0.3744 | 0.9835 | 1.3078 | 0.0003 | 0.0001 | 0.0000 | n_ge5_spread_q50 | 0.2280 |
| validation | hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q50 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | -0.0000 | 0.0000 | n_ge10_spread_q50 | 0.2100 |
| test | hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q50 | 0.1388 | 0.2728 | 0.8064 | 0.3988 | 0.0000 | -0.0002 | 0.0000 | n_ge10_spread_q50 | 0.2026 |
| 0604_ex50 | hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q50 | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | n_ge10_spread_q50 | 0.0989 |
| validation | hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q50_area80 | 0.1253 | 0.2082 | 0.6479 | 0.3251 | -0.0007 | -0.0000 | 0.0000 | n_ge5_spread_q50_area80 | 0.4509 |
| test | hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q50_area80 | 0.1383 | 0.2730 | 0.8064 | 0.3988 | -0.0005 | 0.0000 | 0.0000 | n_ge5_spread_q50_area80 | 0.3773 |
| 0604_ex50 | hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q50_area80 | 0.2734 | 0.3744 | 0.9835 | 1.3078 | 0.0003 | 0.0000 | 0.0000 | n_ge5_spread_q50_area80 | 0.1846 |
| validation | hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q66_area80 | 0.1260 | 0.2081 | 0.6471 | 0.3252 | 0.0000 | -0.0001 | -0.0009 | n_ge10_spread_q66_area80 | 0.2331 |
| test | hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q66_area80 | 0.1388 | 0.2728 | 0.8064 | 0.3988 | 0.0000 | -0.0002 | 0.0000 | n_ge10_spread_q66_area80 | 0.2306 |
| 0604_ex50 | hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q66_area80 | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0001 | 0.0000 | n_ge10_spread_q66_area80 | 0.1363 |
| validation | hcoef38_route_p95_near_all_cap0p0075_s0p2__spread_q50 | 0.1260 | 0.2082 | 0.6479 | 0.3251 | 0.0000 | -0.0000 | 0.0000 | spread_q50 | 0.5010 |
| test | hcoef38_route_p95_near_all_cap0p0075_s0p2__spread_q50 | 0.1382 | 0.2730 | 0.8062 | 0.3988 | -0.0006 | -0.0000 | -0.0002 | spread_q50 | 0.4399 |
| 0604_ex50 | hcoef38_route_p95_near_all_cap0p0075_s0p2__spread_q50 | 0.2734 | 0.3744 | 0.9835 | 1.3078 | 0.0003 | 0.0001 | 0.0000 | spread_q50 | 0.2750 |
| validation | hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q50_area80 | 0.1260 | 0.2082 | 0.6479 | 0.3251 | 0.0000 | -0.0000 | 0.0000 | n_ge5_spread_q50_area80 | 0.4509 |
| test | hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q50_area80 | 0.1382 | 0.2730 | 0.8064 | 0.3988 | -0.0006 | -0.0000 | 0.0000 | n_ge5_spread_q50_area80 | 0.3773 |
| 0604_ex50 | hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q50_area80 | 0.2734 | 0.3744 | 0.9835 | 1.3078 | 0.0003 | 0.0000 | 0.0000 | n_ge5_spread_q50_area80 | 0.1846 |
| validation | hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge10_spread_q66_area80 | 0.1260 | 0.2082 | 0.6477 | 0.3252 | 0.0000 | -0.0001 | -0.0002 | n_ge10_spread_q66_area80 | 0.2331 |
| test | hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge10_spread_q66_area80 | 0.1388 | 0.2729 | 0.8064 | 0.3988 | 0.0000 | -0.0001 | 0.0000 | n_ge10_spread_q66_area80 | 0.2306 |
| 0604_ex50 | hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge10_spread_q66_area80 | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | n_ge10_spread_q66_area80 | 0.1363 |

## 3. 후보 판단

| candidate | extended_repeat_decision | base_improver | route_rule | route_coverage | test_MdAPE | test_MAPE | test_p95_APE | stress0604_MdAPE | stress0604_MAPE | stress0604_p95_APE | min_stable_any2_improve_prob | min_stable_all3_improve_prob | fixed_p95_margin_vs_stable | stress0604_p95_margin_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q66_area80 | 기존 70:30 대비 p95 방어 후보 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | n_ge10_spread_q66_area80 | 0.2306 | 0.1388 | 0.2728 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | 0.7167 | 0.2167 | 0.0000 | -0.0000 |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge10_spread_q66_area80 | 기존 70:30 대비 p95 방어 후보 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge10_spread_q66_area80 | 0.2306 | 0.1388 | 0.2729 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | 0.6333 | 0.0000 | 0.0000 | -0.0000 |
| hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge10_spread_q66_area80 | 기존 70:30 대비 p95 방어 후보 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | n_ge10_spread_q66_area80 | 0.2306 | 0.1388 | 0.2729 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | 0.6167 | 0.0000 | 0.0000 | -0.0000 |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50_area80 | 기존 70:30 대비 p95 방어 후보 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q50_area80 | 0.3773 | 0.1383 | 0.2730 | 0.8064 | 0.2734 | 0.3744 | 0.9835 | 0.2333 | 0.0000 | 0.0000 | -0.0000 |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q50_area80 | 기존 70:30 대비 p95 방어 후보 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | n_ge5_spread_q50_area80 | 0.3773 | 0.1383 | 0.2730 | 0.8064 | 0.2734 | 0.3744 | 0.9835 | 0.1833 | 0.0000 | 0.0000 | -0.0000 |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__spread_q50 | 기존 70:30 대비 p95 방어 후보 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | spread_q50 | 0.4399 | 0.1383 | 0.2729 | 0.8060 | 0.2734 | 0.3745 | 0.9835 | 0.1500 | 0.0000 | -0.0003 | -0.0000 |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50 | 기존 70:30 대비 p95 방어 후보 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q50 | 0.4399 | 0.1383 | 0.2729 | 0.8060 | 0.2734 | 0.3744 | 0.9835 | 0.1500 | 0.0000 | -0.0003 | -0.0000 |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q50 | 기존 70:30 대비 p95 방어 후보 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | n_ge10_spread_q50 | 0.2026 | 0.1388 | 0.2728 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | 0.1167 | 0.0000 | 0.0000 | -0.0000 |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__spread_q50 | 기존 70:30 대비 p95 방어 후보 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | spread_q50 | 0.4399 | 0.1383 | 0.2729 | 0.8059 | 0.2734 | 0.3746 | 0.9837 | 0.0833 | 0.0000 | -0.0005 | 0.0003 |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q50 | 기존 70:30 대비 p95 방어 후보 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | n_ge5_spread_q50 | 0.4399 | 0.1383 | 0.2729 | 0.8059 | 0.2734 | 0.3744 | 0.9835 | 0.0833 | 0.0000 | -0.0005 | -0.0000 |
| hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q50_area80 | 기존 70:30 대비 p95 방어 후보 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | n_ge5_spread_q50_area80 | 0.3773 | 0.1382 | 0.2730 | 0.8064 | 0.2734 | 0.3744 | 0.9835 | 0.0500 | 0.0000 | 0.0000 | -0.0000 |
| hcoef38_route_p95_near_all_cap0p0075_s0p2__spread_q50 | 기존 70:30 대비 p95 방어 후보 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | spread_q50 | 0.4399 | 0.1382 | 0.2730 | 0.8062 | 0.2734 | 0.3744 | 0.9835 | 0.0333 | 0.0000 | -0.0002 | -0.0000 |
| hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q50 | 기존 70:30 대비 p95 방어 후보 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | n_ge5_spread_q50 | 0.4399 | 0.1382 | 0.2730 | 0.8062 | 0.2734 | 0.3744 | 0.9835 | 0.0333 | 0.0000 | -0.0002 | -0.0000 |
| hcoef38_route_p95_near_all_cap0p0075_s0p2__precise_level_spread_q50 | 기존 70:30 대비 p95 방어 후보 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | precise_level_spread_q50 | 0.3575 | 0.1383 | 0.2729 | 0.8062 | 0.2731 | 0.3744 | 0.9835 | 0.0000 | 0.0000 | -0.0002 | -0.0000 |
| hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q50_gap_q50 | 기존 70:30 대비 p95 방어 후보 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | n_ge5_spread_q50_gap_q50 | 0.2537 | 0.1383 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | 0.0000 | 0.0000 | 0.0000 | -0.0000 |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q50_gap_q50 | 기존 70:30 대비 p95 방어 후보 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | n_ge5_spread_q50_gap_q50 | 0.2537 | 0.1383 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.0000 | 0.0000 | 0.0000 | -0.0000 |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50_gap_q50 | 기존 70:30 대비 p95 방어 후보 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q50_gap_q50 | 0.2537 | 0.1383 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.0000 | 0.0000 | 0.0000 | -0.0000 |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__precise_level_spread_q66_gap_q50 | 기존 70:30 대비 p95 방어 후보 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | precise_level_spread_q66_gap_q50 | 0.3081 | 0.1384 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | 0.0000 | 0.0000 | 0.0000 | -0.0000 |
| hcoef38_route_p95_near_all_cap0p0075_s0p2__precise_level_spread_q66_gap_q50 | 기존 70:30 대비 p95 방어 후보 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | precise_level_spread_q66_gap_q50 | 0.3081 | 0.1384 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | 0.0000 | 0.0000 | 0.0000 | -0.0000 |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__precise_level_spread_q66_gap_q50 | 기존 70:30 대비 p95 방어 후보 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | precise_level_spread_q66_gap_q50 | 0.3081 | 0.1384 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | 0.0000 | 0.0000 | 0.0000 | -0.0000 |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__precise_level_spread_q50 | 기존 70:30 대비 p95 방어 후보 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | precise_level_spread_q50 | 0.3575 | 0.1387 | 0.2728 | 0.8059 | 0.2731 | 0.3744 | 0.9835 | 0.0000 | 0.0000 | -0.0005 | -0.0000 |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__precise_level_spread_q50 | 기존 70:30 대비 p95 방어 후보 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | precise_level_spread_q50 | 0.3575 | 0.1387 | 0.2729 | 0.8060 | 0.2731 | 0.3744 | 0.9835 | 0.0000 | 0.0000 | -0.0003 | -0.0000 |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge10_spread_q50 | 기존 70:30 대비 p95 방어 후보 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge10_spread_q50 | 0.2026 | 0.1388 | 0.2729 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | 0.0000 | 0.0000 | 0.0000 | -0.0000 |
| hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge10_spread_q50 | 기존 70:30 대비 p95 방어 후보 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | n_ge10_spread_q50 | 0.2026 | 0.1388 | 0.2729 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | 0.0000 | 0.0000 | 0.0000 | -0.0000 |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q50_gap_q50 | 기존 70:30 대비 p95 방어 후보 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | n_ge10_spread_q50_gap_q50 | 0.1318 | 0.1388 | 0.2729 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | 0.0000 | 0.0000 | 0.0000 | -0.0000 |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge10_spread_q50_gap_q50 | 기존 70:30 대비 p95 방어 후보 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge10_spread_q50_gap_q50 | 0.1318 | 0.1388 | 0.2729 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | 0.0000 | 0.0000 | 0.0000 | -0.0000 |
| hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge10_spread_q50_gap_q50 | 기존 70:30 대비 p95 방어 후보 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | n_ge10_spread_q50_gap_q50 | 0.1318 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | 0.0000 | 0.0000 | 0.0000 | -0.0000 |

## 4. 반복 OOF 요약

| validation_scheme | candidate | n_repeats | mean_MdAPE | mean_MAPE | mean_p95_APE | mean_delta_MdAPE_vs_stable | mean_delta_MAPE_vs_stable | mean_delta_p95_APE_vs_stable | stable_any2_improve_prob | stable_all3_improve_prob | stable_p95_improve_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| row_oof | hcoef38_route_basis_balanced_all_cap0p005_s0p5__spread_q50 | 60 | 0.1257 | 0.2083 | 0.6479 | -0.0003 | 0.0000 | 0.0000 | 0.1500 | 0.0000 | 0.0000 |
| row_oof | hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50 | 60 | 0.1257 | 0.2083 | 0.6479 | -0.0003 | 0.0000 | 0.0000 | 0.1500 | 0.0000 | 0.0000 |
| row_oof | hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50_area80 | 60 | 0.1257 | 0.2082 | 0.6479 | -0.0003 | 0.0000 | 0.0000 | 0.2333 | 0.0000 | 0.0000 |
| row_oof | hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge10_spread_q66_area80 | 60 | 0.1260 | 0.2082 | 0.6474 | 0.0000 | -0.0000 | -0.0005 | 0.8167 | 0.0000 | 0.9500 |
| row_oof | hcoef38_route_best_mdape_all_cap0p01_s0p35__spread_q50 | 60 | 0.1253 | 0.2083 | 0.6479 | -0.0007 | 0.0001 | 0.0000 | 0.0833 | 0.0000 | 0.0000 |
| row_oof | hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q50 | 60 | 0.1253 | 0.2083 | 0.6479 | -0.0007 | 0.0001 | 0.0000 | 0.0833 | 0.0000 | 0.0000 |
| row_oof | hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q50 | 60 | 0.1260 | 0.2082 | 0.6479 | -0.0000 | 0.0000 | 0.0000 | 0.1833 | 0.0000 | 0.0000 |
| row_oof | hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q50_area80 | 60 | 0.1253 | 0.2083 | 0.6479 | -0.0007 | 0.0000 | 0.0000 | 0.1833 | 0.0000 | 0.0000 |
| row_oof | hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q66_area80 | 60 | 0.1260 | 0.2082 | 0.6472 | 0.0000 | -0.0000 | -0.0007 | 0.9000 | 0.2333 | 0.9500 |
| row_oof | hcoef38_route_p95_near_all_cap0p0075_s0p2__spread_q50 | 60 | 0.1259 | 0.2082 | 0.6479 | -0.0001 | 0.0000 | 0.0000 | 0.0333 | 0.0000 | 0.0000 |
| row_oof | hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q50_area80 | 60 | 0.1259 | 0.2082 | 0.6479 | -0.0001 | 0.0000 | 0.0000 | 0.0500 | 0.0000 | 0.0000 |
| row_oof | hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge10_spread_q66_area80 | 60 | 0.1260 | 0.2082 | 0.6477 | 0.0000 | -0.0000 | -0.0002 | 0.8500 | 0.0000 | 0.9500 |
| artist_oof | hcoef38_route_basis_balanced_all_cap0p005_s0p5__spread_q50 | 60 | 0.1257 | 0.2083 | 0.6479 | -0.0003 | 0.0000 | 0.0000 | 0.1500 | 0.0000 | 0.0000 |
| artist_oof | hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50 | 60 | 0.1257 | 0.2083 | 0.6479 | -0.0003 | 0.0000 | 0.0000 | 0.1500 | 0.0000 | 0.0000 |
| artist_oof | hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50_area80 | 60 | 0.1257 | 0.2082 | 0.6479 | -0.0003 | 0.0000 | 0.0000 | 0.3333 | 0.0000 | 0.0000 |
| artist_oof | hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge10_spread_q66_area80 | 60 | 0.1260 | 0.2082 | 0.6475 | 0.0000 | -0.0000 | -0.0005 | 0.6333 | 0.0000 | 0.9000 |
| artist_oof | hcoef38_route_best_mdape_all_cap0p01_s0p35__spread_q50 | 60 | 0.1253 | 0.2083 | 0.6479 | -0.0007 | 0.0001 | 0.0000 | 0.1167 | 0.0000 | 0.0000 |
| artist_oof | hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q50 | 60 | 0.1253 | 0.2083 | 0.6479 | -0.0007 | 0.0001 | 0.0000 | 0.1167 | 0.0000 | 0.0000 |
| artist_oof | hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q50 | 60 | 0.1259 | 0.2082 | 0.6479 | -0.0000 | 0.0000 | 0.0000 | 0.1167 | 0.0000 | 0.0000 |
| artist_oof | hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q50_area80 | 60 | 0.1253 | 0.2082 | 0.6479 | -0.0007 | 0.0000 | 0.0000 | 0.3000 | 0.0000 | 0.0000 |
| artist_oof | hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q66_area80 | 60 | 0.1260 | 0.2082 | 0.6472 | -0.0000 | -0.0000 | -0.0007 | 0.7167 | 0.2167 | 0.9000 |
| artist_oof | hcoef38_route_p95_near_all_cap0p0075_s0p2__spread_q50 | 60 | 0.1259 | 0.2082 | 0.6479 | -0.0001 | 0.0000 | 0.0000 | 0.0333 | 0.0000 | 0.0000 |
| artist_oof | hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q50_area80 | 60 | 0.1259 | 0.2082 | 0.6479 | -0.0001 | 0.0000 | 0.0000 | 0.0833 | 0.0000 | 0.0000 |
| artist_oof | hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge10_spread_q66_area80 | 60 | 0.1260 | 0.2082 | 0.6477 | 0.0000 | -0.0000 | -0.0002 | 0.6167 | 0.0000 | 0.9000 |

## 5. 라우팅 정책

| candidate | split | route_rule | route_coverage | route_n | basis_component_spread_max | abs_fallback_stable_gap_max | log_area_min | log_area_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__spread_q50 | validation | spread_q50 | 0.5010 | 260 | 0.6969 | nan | nan | nan |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__spread_q50 | test | spread_q50 | 0.4399 | 267 | 0.6969 | nan | nan | nan |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__spread_q50 | 0604_ex50 | spread_q50 | 0.2750 | 228 | 0.6969 | nan | nan | nan |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50 | validation | n_ge5_spread_q50 | 0.5010 | 260 | 0.6969 | nan | nan | nan |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50 | test | n_ge5_spread_q50 | 0.4399 | 267 | 0.6969 | nan | nan | nan |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50 | 0604_ex50 | n_ge5_spread_q50 | 0.2280 | 189 | 0.6969 | nan | nan | nan |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50_area80 | validation | n_ge5_spread_q50_area80 | 0.4509 | 234 | 0.6969 | nan | 6.5574 | 9.8384 |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50_area80 | test | n_ge5_spread_q50_area80 | 0.3773 | 229 | 0.6969 | nan | 6.5574 | 9.8384 |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50_area80 | 0604_ex50 | n_ge5_spread_q50_area80 | 0.1846 | 153 | 0.6969 | nan | 6.5574 | 9.8384 |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge10_spread_q66_area80 | validation | n_ge10_spread_q66_area80 | 0.2331 | 121 | 1.0532 | nan | 6.5574 | 9.8384 |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge10_spread_q66_area80 | test | n_ge10_spread_q66_area80 | 0.2306 | 140 | 1.0532 | nan | 6.5574 | 9.8384 |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge10_spread_q66_area80 | 0604_ex50 | n_ge10_spread_q66_area80 | 0.1363 | 113 | 1.0532 | nan | 6.5574 | 9.8384 |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__spread_q50 | validation | spread_q50 | 0.5010 | 260 | 0.6969 | nan | nan | nan |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__spread_q50 | test | spread_q50 | 0.4399 | 267 | 0.6969 | nan | nan | nan |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__spread_q50 | 0604_ex50 | spread_q50 | 0.2750 | 228 | 0.6969 | nan | nan | nan |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q50 | validation | n_ge5_spread_q50 | 0.5010 | 260 | 0.6969 | nan | nan | nan |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q50 | test | n_ge5_spread_q50 | 0.4399 | 267 | 0.6969 | nan | nan | nan |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q50 | 0604_ex50 | n_ge5_spread_q50 | 0.2280 | 189 | 0.6969 | nan | nan | nan |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q50 | validation | n_ge10_spread_q50 | 0.2100 | 109 | 0.6969 | nan | nan | nan |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q50 | test | n_ge10_spread_q50 | 0.2026 | 123 | 0.6969 | nan | nan | nan |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q50 | 0604_ex50 | n_ge10_spread_q50 | 0.0989 | 82 | 0.6969 | nan | nan | nan |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q50_area80 | validation | n_ge5_spread_q50_area80 | 0.4509 | 234 | 0.6969 | nan | 6.5574 | 9.8384 |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q50_area80 | test | n_ge5_spread_q50_area80 | 0.3773 | 229 | 0.6969 | nan | 6.5574 | 9.8384 |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q50_area80 | 0604_ex50 | n_ge5_spread_q50_area80 | 0.1846 | 153 | 0.6969 | nan | 6.5574 | 9.8384 |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q66_area80 | validation | n_ge10_spread_q66_area80 | 0.2331 | 121 | 1.0532 | nan | 6.5574 | 9.8384 |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q66_area80 | test | n_ge10_spread_q66_area80 | 0.2306 | 140 | 1.0532 | nan | 6.5574 | 9.8384 |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q66_area80 | 0604_ex50 | n_ge10_spread_q66_area80 | 0.1363 | 113 | 1.0532 | nan | 6.5574 | 9.8384 |
| hcoef38_route_p95_near_all_cap0p0075_s0p2__spread_q50 | validation | spread_q50 | 0.5010 | 260 | 0.6969 | nan | nan | nan |
| hcoef38_route_p95_near_all_cap0p0075_s0p2__spread_q50 | test | spread_q50 | 0.4399 | 267 | 0.6969 | nan | nan | nan |
| hcoef38_route_p95_near_all_cap0p0075_s0p2__spread_q50 | 0604_ex50 | spread_q50 | 0.2750 | 228 | 0.6969 | nan | nan | nan |
| hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q50_area80 | validation | n_ge5_spread_q50_area80 | 0.4509 | 234 | 0.6969 | nan | 6.5574 | 9.8384 |
| hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q50_area80 | test | n_ge5_spread_q50_area80 | 0.3773 | 229 | 0.6969 | nan | 6.5574 | 9.8384 |
| hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q50_area80 | 0604_ex50 | n_ge5_spread_q50_area80 | 0.1846 | 153 | 0.6969 | nan | 6.5574 | 9.8384 |
| hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge10_spread_q66_area80 | validation | n_ge10_spread_q66_area80 | 0.2331 | 121 | 1.0532 | nan | 6.5574 | 9.8384 |
| hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge10_spread_q66_area80 | test | n_ge10_spread_q66_area80 | 0.2306 | 140 | 1.0532 | nan | 6.5574 | 9.8384 |
| hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge10_spread_q66_area80 | 0604_ex50 | n_ge10_spread_q66_area80 | 0.1363 | 113 | 1.0532 | nan | 6.5574 | 9.8384 |

## 6. Huber 계수 해석

- 계수는 HCOEF35 base improver의 residual Huber 모델 기준이다.
- 양수 계수는 stable 예측에 보정값을 더하는 방향이다.
- 음수 계수는 stable 예측에서 보정값을 빼는 방향이다.

| candidate | base_improver | route_rule | feature | coefficient_on_scaled_feature | direction |
| --- | --- | --- | --- | --- | --- |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__spread_q50 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | spread_q50 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50_area80 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q50_area80 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge10_spread_q66_area80 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | n_ge10_spread_q66_area80 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q50_area80 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | n_ge5_spread_q50_area80 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef38_route_p95_near_all_cap0p0075_s0p2__spread_q50 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | spread_q50 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge10_spread_q66_area80 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge10_spread_q66_area80 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q50 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q66_area80 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | n_ge10_spread_q66_area80 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q50_area80 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | n_ge5_spread_q50_area80 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q50 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | n_ge5_spread_q50 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__spread_q50 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | spread_q50 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q50 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | n_ge10_spread_q50 | basis_artist_overall_m1_gap | -0.0389 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__spread_q50 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | spread_q50 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef38_route_p95_near_all_cap0p0075_s0p2__spread_q50 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | spread_q50 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q50 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50_area80 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q50_area80 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q50_area80 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | n_ge5_spread_q50_area80 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge10_spread_q66_area80 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge10_spread_q66_area80 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge10_spread_q66_area80 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | n_ge10_spread_q66_area80 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q66_area80 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | n_ge10_spread_q66_area80 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q50_area80 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | n_ge5_spread_q50_area80 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q50 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | n_ge10_spread_q50 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q50 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | n_ge5_spread_q50 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__spread_q50 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | spread_q50 | basis_artist_medium_support_m5_gap | -0.0257 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge10_spread_q66_area80 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | n_ge10_spread_q66_area80 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef38_route_p95_near_all_cap0p0075_s0p2__spread_q50 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | spread_q50 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge10_spread_q66_area80 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge10_spread_q66_area80 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__spread_q50 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | spread_q50 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q50 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q50_area80 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | n_ge5_spread_q50_area80 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50_area80 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q50_area80 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q66_area80 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | n_ge10_spread_q66_area80 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q50_area80 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | n_ge5_spread_q50_area80 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q50 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | n_ge10_spread_q50 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q50 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | n_ge5_spread_q50 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef38_route_best_mdape_all_cap0p01_s0p35__spread_q50 | hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35 | spread_q50 | shrink20_stable_gap | 0.0255 | 예측 로그가격/보정값을 올리는 방향 |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50_area80 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q50_area80 | basis_component_spread | -0.0236 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | n_ge5_spread_q50 | basis_component_spread | -0.0236 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef38_route_p95_near_all_cap0p0075_s0p2__spread_q50 | hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2 | spread_q50 | basis_component_spread | -0.0236 | 예측 로그가격/보정값을 낮추는 방향 |
| hcoef38_route_basis_balanced_all_cap0p005_s0p5__spread_q50 | hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5 | spread_q50 | basis_component_spread | -0.0236 | 예측 로그가격/보정값을 낮추는 방향 |

_상위 40개만 표시. 전체 120개._

## 7. 잔차와 큰 오차 확인

| split | candidate | n | median_residual_log | mean_residual_log | residual_std | ape_median | ape_mean | ape_p95 | ape_gt_100pct_n | over_2x_n | under_half_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | current_70_30 | 607 | -0.0006 | -0.0119 | 0.3998 | 0.1405 | 0.2748 | 0.8331 | 24 | 24 | 17 |
| test | hcoef_stable | 607 | -0.0039 | -0.0148 | 0.3989 | 0.1388 | 0.2730 | 0.8064 | 26 | 26 | 17 |
| 0604_ex50 | current_70_30 | 829 | 0.0782 | 0.3370 | 1.2685 | 0.2779 | 0.3774 | 0.9871 | 30 | 30 | 153 |
| 0604_ex50 | hcoef_stable | 829 | 0.0608 | 0.3278 | 1.2668 | 0.2731 | 0.3744 | 0.9835 | 26 | 26 | 152 |
| test | hcoef38_route_basis_balanced_all_cap0p005_s0p5__spread_q50 | 607 | -0.0017 | -0.0151 | 0.3988 | 0.1383 | 0.2729 | 0.8060 | 26 | 26 | 17 |
| 0604_ex50 | hcoef38_route_basis_balanced_all_cap0p005_s0p5__spread_q50 | 829 | 0.0608 | 0.3276 | 1.2668 | 0.2734 | 0.3745 | 0.9835 | 27 | 27 | 152 |
| test | hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50 | 607 | -0.0017 | -0.0151 | 0.3988 | 0.1383 | 0.2729 | 0.8060 | 26 | 26 | 17 |
| 0604_ex50 | hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50 | 829 | 0.0608 | 0.3277 | 1.2668 | 0.2734 | 0.3744 | 0.9835 | 26 | 26 | 152 |
| test | hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50_area80 | 607 | -0.0017 | -0.0150 | 0.3989 | 0.1383 | 0.2730 | 0.8064 | 26 | 26 | 17 |
| 0604_ex50 | hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q50_area80 | 829 | 0.0608 | 0.3277 | 1.2668 | 0.2734 | 0.3744 | 0.9835 | 26 | 26 | 152 |
| test | hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge10_spread_q66_area80 | 607 | -0.0017 | -0.0146 | 0.3988 | 0.1388 | 0.2729 | 0.8064 | 26 | 26 | 17 |
| 0604_ex50 | hcoef38_route_basis_balanced_all_cap0p005_s0p5__n_ge10_spread_q66_area80 | 829 | 0.0608 | 0.3279 | 1.2668 | 0.2731 | 0.3744 | 0.9835 | 26 | 26 | 152 |
| test | hcoef38_route_best_mdape_all_cap0p01_s0p35__spread_q50 | 607 | -0.0027 | -0.0152 | 0.3988 | 0.1383 | 0.2729 | 0.8059 | 26 | 26 | 17 |
| 0604_ex50 | hcoef38_route_best_mdape_all_cap0p01_s0p35__spread_q50 | 829 | 0.0608 | 0.3275 | 1.2669 | 0.2734 | 0.3746 | 0.9837 | 27 | 27 | 152 |
| test | hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q50 | 607 | -0.0027 | -0.0152 | 0.3988 | 0.1383 | 0.2729 | 0.8059 | 26 | 26 | 17 |
| 0604_ex50 | hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q50 | 829 | 0.0608 | 0.3277 | 1.2668 | 0.2734 | 0.3744 | 0.9835 | 26 | 26 | 152 |
| test | hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q50 | 607 | -0.0027 | -0.0147 | 0.3988 | 0.1388 | 0.2728 | 0.8064 | 26 | 26 | 17 |
| 0604_ex50 | hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q50 | 829 | 0.0608 | 0.3279 | 1.2668 | 0.2731 | 0.3744 | 0.9835 | 26 | 26 | 152 |
| test | hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q50_area80 | 607 | -0.0027 | -0.0151 | 0.3989 | 0.1383 | 0.2730 | 0.8064 | 26 | 26 | 17 |
| 0604_ex50 | hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q50_area80 | 829 | 0.0608 | 0.3277 | 1.2668 | 0.2734 | 0.3744 | 0.9835 | 26 | 26 | 152 |
| test | hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q66_area80 | 607 | -0.0027 | -0.0146 | 0.3988 | 0.1388 | 0.2728 | 0.8064 | 26 | 26 | 17 |
| 0604_ex50 | hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q66_area80 | 829 | 0.0608 | 0.3280 | 1.2668 | 0.2731 | 0.3744 | 0.9835 | 26 | 26 | 152 |
| test | hcoef38_route_p95_near_all_cap0p0075_s0p2__spread_q50 | 607 | -0.0024 | -0.0150 | 0.3988 | 0.1382 | 0.2730 | 0.8062 | 26 | 26 | 17 |
| 0604_ex50 | hcoef38_route_p95_near_all_cap0p0075_s0p2__spread_q50 | 829 | 0.0608 | 0.3277 | 1.2668 | 0.2734 | 0.3744 | 0.9835 | 26 | 26 | 152 |
| test | hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q50 | 607 | -0.0024 | -0.0150 | 0.3988 | 0.1382 | 0.2730 | 0.8062 | 26 | 26 | 17 |
| 0604_ex50 | hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q50 | 829 | 0.0608 | 0.3278 | 1.2668 | 0.2734 | 0.3744 | 0.9835 | 26 | 26 | 152 |
| test | hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q50_gap_q50 | 607 | -0.0039 | -0.0149 | 0.3989 | 0.1383 | 0.2730 | 0.8064 | 26 | 26 | 17 |
| 0604_ex50 | hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q50_gap_q50 | 829 | 0.0608 | 0.3278 | 1.2668 | 0.2731 | 0.3744 | 0.9835 | 26 | 26 | 152 |
| test | hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q50_area80 | 607 | -0.0024 | -0.0149 | 0.3989 | 0.1382 | 0.2730 | 0.8064 | 26 | 26 | 17 |
| 0604_ex50 | hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q50_area80 | 829 | 0.0608 | 0.3278 | 1.2668 | 0.2734 | 0.3744 | 0.9835 | 26 | 26 | 152 |
| test | hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge10_spread_q66_area80 | 607 | -0.0024 | -0.0147 | 0.3989 | 0.1388 | 0.2729 | 0.8064 | 26 | 26 | 17 |
| 0604_ex50 | hcoef38_route_p95_near_all_cap0p0075_s0p2__n_ge10_spread_q66_area80 | 829 | 0.0608 | 0.3279 | 1.2668 | 0.2731 | 0.3744 | 0.9835 | 26 | 26 | 152 |
| test | hcoef38_route_p95_near_all_cap0p0075_s0p2__precise_level_spread_q50 | 607 | -0.0024 | -0.0149 | 0.3988 | 0.1383 | 0.2729 | 0.8062 | 26 | 26 | 17 |
| 0604_ex50 | hcoef38_route_p95_near_all_cap0p0075_s0p2__precise_level_spread_q50 | 829 | 0.0608 | 0.3278 | 1.2668 | 0.2731 | 0.3744 | 0.9835 | 26 | 26 | 152 |

## 8. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/policy_map.csv`
- `outputs/residual_analysis.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `outputs/repeated_validation_summary.csv`
- `outputs/selected_candidates.csv`
- `artifacts/experiment_config.json`