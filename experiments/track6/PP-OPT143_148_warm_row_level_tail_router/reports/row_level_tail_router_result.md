# PP-OPT143~148 Warm row-level tail router 결과

- 작성일: 2026-06-09 16:38
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 목적: PP126을 기본값으로 유지하면서 p95 위험 row만 direct-meta/보정 후보로 부분 전환
- 결론: 운영 후보 fixed test MAPE 0.270140, p95 0.807231. PP126 대비 MAPE +0.000026, p95 -0.000259. p95 후보 fixed test MAPE 0.270269, p95 0.805949.

## 주요 후보 test 비교
| candidate | family | item_id | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| reference_pp134_operational_recomputed | reference_prior | REFERENCE | 0.136320 | 0.270033 | 0.807490 | 0.397520 | -0.001362 | -0.000640 |
| reference_pp126_operational | reference_prior | REFERENCE | 0.136320 | 0.270114 | 0.807490 | 0.397588 | -0.001280 | -0.000640 |
| ppopt148_operational_row_level_tail_router_challenger__source=ppopt146_hard_switch__target_direct_lgb_l2_s0p18_cap0p01__thr_0p42__tail_0p0__s_0p65__cap_0p01 | row_level_tail_router_operational_selection | PP-OPT148 | 0.139801 | 0.270140 | 0.807231 | 0.397525 | -0.001255 | -0.000899 |
| reference_pp134_p95_recomputed | reference_prior | REFERENCE | 0.136320 | 0.270242 | 0.807488 | 0.397692 | -0.001153 | -0.000641 |
| ppopt148_p95_row_level_tail_router_challenger__source=ppopt144_learned_adopt__target_direct_lgb_l2_s0p18_cap0p01__thr_0p24__w_0p08__hpen_0p2__s_1p0__cap_0p014 | row_level_tail_router_p95_selection | PP-OPT148 | 0.141036 | 0.270269 | 0.805949 | 0.397421 | -0.001126 | -0.002181 |
| reference_pp126_p95 | reference_prior | REFERENCE | 0.137871 | 0.270317 | 0.807465 | 0.397768 | -0.001078 | -0.000665 |
| reference_pp64_current_best | reference_prior | REFERENCE | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | p95_test_MAPE | p95_test_p95_APE | operational_pass_vs_incumbent | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | operation-tail dual router | 108 | 0.270064 | 0.807475 | 0.270060 | 0.807451 | True | operation_tail_dual_router | ppopt147_operation_tail_dual__mid=0p65__tail=0p25__hpen=0p25__cap=0p006 |
| 2 | learned adoption probability router | 1620 | 0.270118 | 0.807347 | 0.270269 | 0.805949 | True | learned_adoption_probability_router | ppopt144_learned_adopt__target=direct_lgb_l2_s0p18_cap0p01__thr=0p4__w=0p22__hpen=0p7__s=0p45__cap=0p006 |
| 4 | hard-switch quantile router | 216 | 0.270108 | 0.807490 | 0.270109 | 0.807091 | True | hard_switch_quantile_router | ppopt146_hard_switch__target=direct_lgb_q50_s0p18_cap0p01__thr=0p42__tail=0p4__s=0p65__cap=0p007 |
| 1 | tail-risk row-only direct-meta router | 432 | 0.270115 | 0.807490 | 0.270039 | 0.807091 | True | tail_risk_row_only_direct_meta_router | ppopt143_tail_risk_router__target=pp134_p95_recomputed__thr=0p52__w=0p24__s=0p35__cap=0p006 |
| 3 | direction-consensus guarded router | 324 | 0.270102 | 0.807490 | 0.270195 | 0.806186 | True | direction_consensus_guarded_router | ppopt145_direction_consensus__target=direct_lgb_q50_s0p18_cap0p01__minc=0p67__thr=0p32__s=0p45__cap=0p006 |
| 6 | final row-level tail-router decision | 2 | 0.270140 | 0.807231 | 0.270269 | 0.805949 | False | row_level_tail_router_operational_selection | ppopt148_operational_row_level_tail_router_challenger__source=ppopt146_hard_switch__target_direct_lgb_l2_s0p18_cap0p01__thr_0p42__tail_0p0__s_0p65__cap_0p01 |

## 탐색 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt147_operation_tail_dual__mid=0p65__tail=0p25__hpen=0p25__cap=0p006 | PP-OPT147 | operation_tail_dual_router | 0.270064 | 0.807475 | -0.001331 | -0.000655 | -0.002085 |
| ppopt147_operation_tail_dual__mid=0p65__tail=0p25__hpen=0p25__cap=0p01 | PP-OPT147 | operation_tail_dual_router | 0.270064 | 0.807475 | -0.001331 | -0.000655 | -0.002085 |
| ppopt147_operation_tail_dual__mid=0p65__tail=0p25__hpen=0p25__cap=0p014 | PP-OPT147 | operation_tail_dual_router | 0.270064 | 0.807475 | -0.001331 | -0.000655 | -0.002085 |
| ppopt147_operation_tail_dual__mid=0p65__tail=0p25__hpen=0p25__cap=0p018 | PP-OPT147 | operation_tail_dual_router | 0.270064 | 0.807475 | -0.001331 | -0.000655 | -0.002085 |
| ppopt147_operation_tail_dual__mid=0p65__tail=0p25__hpen=0p45__cap=0p006 | PP-OPT147 | operation_tail_dual_router | 0.270064 | 0.807475 | -0.001331 | -0.000655 | -0.002085 |
| ppopt147_operation_tail_dual__mid=0p65__tail=0p25__hpen=0p45__cap=0p01 | PP-OPT147 | operation_tail_dual_router | 0.270064 | 0.807475 | -0.001331 | -0.000655 | -0.002085 |
| ppopt147_operation_tail_dual__mid=0p65__tail=0p25__hpen=0p45__cap=0p014 | PP-OPT147 | operation_tail_dual_router | 0.270064 | 0.807475 | -0.001331 | -0.000655 | -0.002085 |
| ppopt147_operation_tail_dual__mid=0p65__tail=0p25__hpen=0p45__cap=0p018 | PP-OPT147 | operation_tail_dual_router | 0.270064 | 0.807475 | -0.001331 | -0.000655 | -0.002085 |
| ppopt147_operation_tail_dual__mid=0p65__tail=0p25__hpen=0p65__cap=0p006 | PP-OPT147 | operation_tail_dual_router | 0.270064 | 0.807475 | -0.001331 | -0.000655 | -0.002085 |
| ppopt147_operation_tail_dual__mid=0p65__tail=0p25__hpen=0p65__cap=0p01 | PP-OPT147 | operation_tail_dual_router | 0.270064 | 0.807475 | -0.001331 | -0.000655 | -0.002085 |
| ppopt147_operation_tail_dual__mid=0p65__tail=0p25__hpen=0p65__cap=0p014 | PP-OPT147 | operation_tail_dual_router | 0.270064 | 0.807475 | -0.001331 | -0.000655 | -0.002085 |
| ppopt147_operation_tail_dual__mid=0p65__tail=0p25__hpen=0p65__cap=0p018 | PP-OPT147 | operation_tail_dual_router | 0.270064 | 0.807475 | -0.001331 | -0.000655 | -0.002085 |
| ppopt147_operation_tail_dual__mid=0p65__tail=0p45__hpen=0p25__cap=0p006 | PP-OPT147 | operation_tail_dual_router | 0.270062 | 0.807463 | -0.001333 | -0.000667 | -0.002084 |
| ppopt147_operation_tail_dual__mid=0p65__tail=0p45__hpen=0p25__cap=0p01 | PP-OPT147 | operation_tail_dual_router | 0.270062 | 0.807463 | -0.001333 | -0.000667 | -0.002084 |
| ppopt147_operation_tail_dual__mid=0p65__tail=0p45__hpen=0p25__cap=0p014 | PP-OPT147 | operation_tail_dual_router | 0.270062 | 0.807463 | -0.001333 | -0.000667 | -0.002084 |
| ppopt147_operation_tail_dual__mid=0p65__tail=0p45__hpen=0p25__cap=0p018 | PP-OPT147 | operation_tail_dual_router | 0.270062 | 0.807463 | -0.001333 | -0.000667 | -0.002084 |
| ppopt147_operation_tail_dual__mid=0p65__tail=0p45__hpen=0p45__cap=0p006 | PP-OPT147 | operation_tail_dual_router | 0.270062 | 0.807463 | -0.001333 | -0.000667 | -0.002084 |
| ppopt147_operation_tail_dual__mid=0p65__tail=0p45__hpen=0p45__cap=0p01 | PP-OPT147 | operation_tail_dual_router | 0.270062 | 0.807463 | -0.001333 | -0.000667 | -0.002084 |
| ppopt147_operation_tail_dual__mid=0p65__tail=0p45__hpen=0p45__cap=0p014 | PP-OPT147 | operation_tail_dual_router | 0.270062 | 0.807463 | -0.001333 | -0.000667 | -0.002084 |
| ppopt147_operation_tail_dual__mid=0p65__tail=0p45__hpen=0p45__cap=0p018 | PP-OPT147 | operation_tail_dual_router | 0.270062 | 0.807463 | -0.001333 | -0.000667 | -0.002084 |
| ppopt147_operation_tail_dual__mid=0p65__tail=0p45__hpen=0p65__cap=0p006 | PP-OPT147 | operation_tail_dual_router | 0.270062 | 0.807463 | -0.001333 | -0.000667 | -0.002084 |
| ppopt147_operation_tail_dual__mid=0p65__tail=0p45__hpen=0p65__cap=0p01 | PP-OPT147 | operation_tail_dual_router | 0.270062 | 0.807463 | -0.001333 | -0.000667 | -0.002084 |
| ppopt147_operation_tail_dual__mid=0p65__tail=0p45__hpen=0p65__cap=0p014 | PP-OPT147 | operation_tail_dual_router | 0.270062 | 0.807463 | -0.001333 | -0.000667 | -0.002084 |
| ppopt147_operation_tail_dual__mid=0p65__tail=0p45__hpen=0p65__cap=0p018 | PP-OPT147 | operation_tail_dual_router | 0.270062 | 0.807463 | -0.001333 | -0.000667 | -0.002084 |
| ppopt144_learned_adopt__target=direct_lgb_l2_s0p18_cap0p01__thr=0p4__w=0p22__hpen=0p7__s=0p45__cap=0p006 | PP-OPT144 | learned_adoption_probability_router | 0.270118 | 0.807347 | -0.001277 | -0.000783 | -0.002082 |
| ppopt144_learned_adopt__target=direct_lgb_l2_s0p18_cap0p01__thr=0p4__w=0p22__hpen=0p7__s=0p45__cap=0p01 | PP-OPT144 | learned_adoption_probability_router | 0.270118 | 0.807347 | -0.001277 | -0.000783 | -0.002082 |
| ppopt144_learned_adopt__target=direct_lgb_l2_s0p18_cap0p01__thr=0p4__w=0p22__hpen=0p7__s=0p45__cap=0p014 | PP-OPT144 | learned_adoption_probability_router | 0.270118 | 0.807347 | -0.001277 | -0.000783 | -0.002082 |
| ppopt144_learned_adopt__target=direct_lgb_l2_s0p18_cap0p01__thr=0p4__w=0p22__hpen=0p45__s=0p45__cap=0p006 | PP-OPT144 | learned_adoption_probability_router | 0.270118 | 0.807345 | -0.001277 | -0.000785 | -0.002082 |
| ppopt144_learned_adopt__target=direct_lgb_l2_s0p18_cap0p01__thr=0p4__w=0p22__hpen=0p45__s=0p45__cap=0p01 | PP-OPT144 | learned_adoption_probability_router | 0.270118 | 0.807345 | -0.001277 | -0.000785 | -0.002082 |
| ppopt144_learned_adopt__target=direct_lgb_l2_s0p18_cap0p01__thr=0p4__w=0p22__hpen=0p45__s=0p45__cap=0p014 | PP-OPT144 | learned_adoption_probability_router | 0.270118 | 0.807345 | -0.001277 | -0.000785 | -0.002082 |
| ppopt144_learned_adopt__target=direct_lgb_l2_s0p18_cap0p01__thr=0p4__w=0p22__hpen=0p2__s=0p45__cap=0p006 | PP-OPT144 | learned_adoption_probability_router | 0.270118 | 0.807342 | -0.001277 | -0.000788 | -0.002082 |
| ppopt144_learned_adopt__target=direct_lgb_l2_s0p18_cap0p01__thr=0p4__w=0p22__hpen=0p2__s=0p45__cap=0p01 | PP-OPT144 | learned_adoption_probability_router | 0.270118 | 0.807342 | -0.001277 | -0.000788 | -0.002082 |
| ppopt144_learned_adopt__target=direct_lgb_l2_s0p18_cap0p01__thr=0p4__w=0p22__hpen=0p2__s=0p45__cap=0p014 | PP-OPT144 | learned_adoption_probability_router | 0.270118 | 0.807342 | -0.001277 | -0.000788 | -0.002082 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p25__hpen=0p25__cap=0p006 | PP-OPT147 | operation_tail_dual_router | 0.270079 | 0.807475 | -0.001316 | -0.000655 | -0.002082 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p25__hpen=0p25__cap=0p01 | PP-OPT147 | operation_tail_dual_router | 0.270079 | 0.807475 | -0.001316 | -0.000655 | -0.002082 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p25__hpen=0p25__cap=0p014 | PP-OPT147 | operation_tail_dual_router | 0.270079 | 0.807475 | -0.001316 | -0.000655 | -0.002082 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p25__hpen=0p25__cap=0p018 | PP-OPT147 | operation_tail_dual_router | 0.270079 | 0.807475 | -0.001316 | -0.000655 | -0.002082 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p25__hpen=0p45__cap=0p006 | PP-OPT147 | operation_tail_dual_router | 0.270079 | 0.807475 | -0.001316 | -0.000655 | -0.002082 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p25__hpen=0p45__cap=0p01 | PP-OPT147 | operation_tail_dual_router | 0.270079 | 0.807475 | -0.001316 | -0.000655 | -0.002082 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p25__hpen=0p45__cap=0p014 | PP-OPT147 | operation_tail_dual_router | 0.270079 | 0.807475 | -0.001316 | -0.000655 | -0.002082 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p25__hpen=0p45__cap=0p018 | PP-OPT147 | operation_tail_dual_router | 0.270079 | 0.807475 | -0.001316 | -0.000655 | -0.002082 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p25__hpen=0p65__cap=0p006 | PP-OPT147 | operation_tail_dual_router | 0.270079 | 0.807475 | -0.001316 | -0.000655 | -0.002082 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p25__hpen=0p65__cap=0p01 | PP-OPT147 | operation_tail_dual_router | 0.270079 | 0.807475 | -0.001316 | -0.000655 | -0.002082 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p25__hpen=0p65__cap=0p014 | PP-OPT147 | operation_tail_dual_router | 0.270079 | 0.807475 | -0.001316 | -0.000655 | -0.002082 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p25__hpen=0p65__cap=0p018 | PP-OPT147 | operation_tail_dual_router | 0.270079 | 0.807475 | -0.001316 | -0.000655 | -0.002082 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p45__hpen=0p25__cap=0p006 | PP-OPT147 | operation_tail_dual_router | 0.270077 | 0.807463 | -0.001318 | -0.000667 | -0.002082 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p45__hpen=0p25__cap=0p01 | PP-OPT147 | operation_tail_dual_router | 0.270077 | 0.807463 | -0.001318 | -0.000667 | -0.002082 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p45__hpen=0p25__cap=0p014 | PP-OPT147 | operation_tail_dual_router | 0.270077 | 0.807463 | -0.001318 | -0.000667 | -0.002082 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p45__hpen=0p25__cap=0p018 | PP-OPT147 | operation_tail_dual_router | 0.270077 | 0.807463 | -0.001318 | -0.000667 | -0.002082 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p45__hpen=0p45__cap=0p006 | PP-OPT147 | operation_tail_dual_router | 0.270077 | 0.807463 | -0.001318 | -0.000667 | -0.002082 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p45__hpen=0p45__cap=0p01 | PP-OPT147 | operation_tail_dual_router | 0.270077 | 0.807463 | -0.001318 | -0.000667 | -0.002082 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p45__hpen=0p45__cap=0p014 | PP-OPT147 | operation_tail_dual_router | 0.270077 | 0.807463 | -0.001318 | -0.000667 | -0.002082 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p45__hpen=0p45__cap=0p018 | PP-OPT147 | operation_tail_dual_router | 0.270077 | 0.807463 | -0.001318 | -0.000667 | -0.002082 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p45__hpen=0p65__cap=0p006 | PP-OPT147 | operation_tail_dual_router | 0.270077 | 0.807463 | -0.001318 | -0.000667 | -0.002082 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p45__hpen=0p65__cap=0p01 | PP-OPT147 | operation_tail_dual_router | 0.270077 | 0.807463 | -0.001318 | -0.000667 | -0.002082 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p45__hpen=0p65__cap=0p014 | PP-OPT147 | operation_tail_dual_router | 0.270077 | 0.807463 | -0.001318 | -0.000667 | -0.002082 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p45__hpen=0p65__cap=0p018 | PP-OPT147 | operation_tail_dual_router | 0.270077 | 0.807463 | -0.001318 | -0.000667 | -0.002082 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p65__hpen=0p25__cap=0p006 | PP-OPT147 | operation_tail_dual_router | 0.270075 | 0.807451 | -0.001320 | -0.000679 | -0.002081 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p65__hpen=0p25__cap=0p01 | PP-OPT147 | operation_tail_dual_router | 0.270075 | 0.807451 | -0.001320 | -0.000679 | -0.002081 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p65__hpen=0p25__cap=0p014 | PP-OPT147 | operation_tail_dual_router | 0.270075 | 0.807451 | -0.001320 | -0.000679 | -0.002081 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p65__hpen=0p25__cap=0p018 | PP-OPT147 | operation_tail_dual_router | 0.270075 | 0.807451 | -0.001320 | -0.000679 | -0.002081 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p65__hpen=0p45__cap=0p006 | PP-OPT147 | operation_tail_dual_router | 0.270075 | 0.807451 | -0.001320 | -0.000679 | -0.002081 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p65__hpen=0p45__cap=0p01 | PP-OPT147 | operation_tail_dual_router | 0.270075 | 0.807451 | -0.001320 | -0.000679 | -0.002081 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p65__hpen=0p45__cap=0p014 | PP-OPT147 | operation_tail_dual_router | 0.270075 | 0.807451 | -0.001320 | -0.000679 | -0.002081 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p65__hpen=0p45__cap=0p018 | PP-OPT147 | operation_tail_dual_router | 0.270075 | 0.807451 | -0.001320 | -0.000679 | -0.002081 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p65__hpen=0p65__cap=0p006 | PP-OPT147 | operation_tail_dual_router | 0.270075 | 0.807451 | -0.001320 | -0.000679 | -0.002081 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p65__hpen=0p65__cap=0p01 | PP-OPT147 | operation_tail_dual_router | 0.270075 | 0.807451 | -0.001320 | -0.000679 | -0.002081 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p65__hpen=0p65__cap=0p014 | PP-OPT147 | operation_tail_dual_router | 0.270075 | 0.807451 | -0.001320 | -0.000679 | -0.002081 |
| ppopt147_operation_tail_dual__mid=0p45__tail=0p65__hpen=0p65__cap=0p018 | PP-OPT147 | operation_tail_dual_router | 0.270075 | 0.807451 | -0.001320 | -0.000679 | -0.002081 |
| ppopt147_operation_tail_dual__mid=0p25__tail=0p25__hpen=0p25__cap=0p006 | PP-OPT147 | operation_tail_dual_router | 0.270094 | 0.807475 | -0.001301 | -0.000655 | -0.002079 |
| ppopt147_operation_tail_dual__mid=0p25__tail=0p25__hpen=0p25__cap=0p01 | PP-OPT147 | operation_tail_dual_router | 0.270094 | 0.807475 | -0.001301 | -0.000655 | -0.002079 |
| ppopt147_operation_tail_dual__mid=0p25__tail=0p25__hpen=0p25__cap=0p014 | PP-OPT147 | operation_tail_dual_router | 0.270094 | 0.807475 | -0.001301 | -0.000655 | -0.002079 |
| ppopt147_operation_tail_dual__mid=0p25__tail=0p25__hpen=0p25__cap=0p018 | PP-OPT147 | operation_tail_dual_router | 0.270094 | 0.807475 | -0.001301 | -0.000655 | -0.002079 |
| ppopt147_operation_tail_dual__mid=0p25__tail=0p25__hpen=0p45__cap=0p006 | PP-OPT147 | operation_tail_dual_router | 0.270094 | 0.807475 | -0.001301 | -0.000655 | -0.002079 |
| ppopt147_operation_tail_dual__mid=0p25__tail=0p25__hpen=0p45__cap=0p01 | PP-OPT147 | operation_tail_dual_router | 0.270094 | 0.807475 | -0.001301 | -0.000655 | -0.002079 |
| ppopt147_operation_tail_dual__mid=0p25__tail=0p25__hpen=0p45__cap=0p014 | PP-OPT147 | operation_tail_dual_router | 0.270094 | 0.807475 | -0.001301 | -0.000655 | -0.002079 |
| ppopt147_operation_tail_dual__mid=0p25__tail=0p25__hpen=0p45__cap=0p018 | PP-OPT147 | operation_tail_dual_router | 0.270094 | 0.807475 | -0.001301 | -0.000655 | -0.002079 |
| ppopt147_operation_tail_dual__mid=0p25__tail=0p25__hpen=0p65__cap=0p006 | PP-OPT147 | operation_tail_dual_router | 0.270094 | 0.807475 | -0.001301 | -0.000655 | -0.002079 |
| ppopt147_operation_tail_dual__mid=0p25__tail=0p25__hpen=0p65__cap=0p01 | PP-OPT147 | operation_tail_dual_router | 0.270094 | 0.807475 | -0.001301 | -0.000655 | -0.002079 |
| ppopt147_operation_tail_dual__mid=0p25__tail=0p25__hpen=0p65__cap=0p014 | PP-OPT147 | operation_tail_dual_router | 0.270094 | 0.807475 | -0.001301 | -0.000655 | -0.002079 |

## 선택 후보 반복 안정성
| candidate_label | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_vs_pp64_MAPE | fixed_test_delta_vs_pp64_p95_APE | avg_pp64_MAPE_win_rate | avg_pp64_p95_win_rate | replacement_score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| candidate_ppopt146_hard_switch__target_direct_lgb_l2_s0p18_cap0p01__thr_0p42__tail_0p0__s_0p65__cap_0p__49f1fee265 | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| candidate_ppopt146_hard_switch__target_direct_lgb_l2_s0p18_cap0p01__thr_0p42__tail_0p0__s_0p65__cap_0p__6914aff5e7 | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| pp148_operational_row_level_tail_router_challenger | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| candidate_ppopt146_hard_switch__target_direct_lgb_l2_s0p18_cap0p01__thr_0p42__tail_0p0__s_1p0__cap_0p0__b868885de9 | 0.270139 | 0.807091 | -0.000425 | -0.000408 | 0.924038 | 0.531090 | -0.017387 |
| candidate_ppopt146_hard_switch__target_direct_lgb_l2_s0p18_cap0p01__thr_0p42__tail_0p0__s_1p0__cap_0p0__71886081d2 | 0.270161 | 0.807091 | -0.000403 | -0.000408 | 0.922436 | 0.528205 | -0.017300 |
| pp126_operational_reference | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt147_operation_tail_dual__mid_0p65__tail_0p25__hpen_0p25__cap_0p006__24244a9c84 | 0.270064 | 0.807475 | -0.000500 | -0.000024 | 0.916667 | 0.529167 | -0.017167 |
| candidate_ppopt147_operation_tail_dual__mid_0p65__tail_0p25__hpen_0p25__cap_0p014__676dce4efd | 0.270064 | 0.807475 | -0.000500 | -0.000024 | 0.916667 | 0.529167 | -0.017167 |
| candidate_ppopt147_operation_tail_dual__mid_0p65__tail_0p25__hpen_0p25__cap_0p018__f84d625008 | 0.270064 | 0.807475 | -0.000500 | -0.000024 | 0.916667 | 0.529167 | -0.017167 |
| candidate_ppopt147_operation_tail_dual__mid_0p65__tail_0p25__hpen_0p25__cap_0p01__08ec88b047 | 0.270064 | 0.807475 | -0.000500 | -0.000024 | 0.916667 | 0.529167 | -0.017167 |
| candidate_ppopt147_operation_tail_dual__mid_0p65__tail_0p25__hpen_0p45__cap_0p006__28542f2ba6 | 0.270064 | 0.807475 | -0.000500 | -0.000024 | 0.916667 | 0.529167 | -0.017167 |
| candidate_ppopt147_operation_tail_dual__mid_0p65__tail_0p25__hpen_0p45__cap_0p014__5f6fb4f192 | 0.270064 | 0.807475 | -0.000500 | -0.000024 | 0.916667 | 0.529167 | -0.017167 |
| candidate_ppopt147_operation_tail_dual__mid_0p65__tail_0p25__hpen_0p45__cap_0p018__ec527b2f15 | 0.270064 | 0.807475 | -0.000500 | -0.000024 | 0.916667 | 0.529167 | -0.017167 |
| candidate_ppopt147_operation_tail_dual__mid_0p65__tail_0p25__hpen_0p45__cap_0p01__cd40a9f6a9 | 0.270064 | 0.807475 | -0.000500 | -0.000024 | 0.916667 | 0.529167 | -0.017167 |
| candidate_ppopt147_operation_tail_dual__mid_0p65__tail_0p25__hpen_0p65__cap_0p006__5f8b952537 | 0.270064 | 0.807475 | -0.000500 | -0.000024 | 0.916667 | 0.529167 | -0.017167 |
| candidate_ppopt147_operation_tail_dual__mid_0p65__tail_0p25__hpen_0p65__cap_0p014__02e443f394 | 0.270064 | 0.807475 | -0.000500 | -0.000024 | 0.916667 | 0.529167 | -0.017167 |
| candidate_ppopt147_operation_tail_dual__mid_0p65__tail_0p25__hpen_0p65__cap_0p018__ddef4a9eb4 | 0.270064 | 0.807475 | -0.000500 | -0.000024 | 0.916667 | 0.529167 | -0.017167 |
| candidate_ppopt147_operation_tail_dual__mid_0p65__tail_0p25__hpen_0p65__cap_0p01__12816d9536 | 0.270064 | 0.807475 | -0.000500 | -0.000024 | 0.916667 | 0.529167 | -0.017167 |
| candidate_ppopt147_operation_tail_dual__mid_0p65__tail_0p45__hpen_0p25__cap_0p006__dd18337ec3 | 0.270062 | 0.807463 | -0.000502 | -0.000036 | 0.916346 | 0.528846 | -0.017156 |
| candidate_ppopt147_operation_tail_dual__mid_0p65__tail_0p45__hpen_0p25__cap_0p014__c1b91e5265 | 0.270062 | 0.807463 | -0.000502 | -0.000036 | 0.916346 | 0.528846 | -0.017156 |
| candidate_ppopt147_operation_tail_dual__mid_0p65__tail_0p45__hpen_0p25__cap_0p018__aee2a866c0 | 0.270062 | 0.807463 | -0.000502 | -0.000036 | 0.916346 | 0.528846 | -0.017156 |
| candidate_ppopt147_operation_tail_dual__mid_0p65__tail_0p45__hpen_0p25__cap_0p01__cfdb8ae3e2 | 0.270062 | 0.807463 | -0.000502 | -0.000036 | 0.916346 | 0.528846 | -0.017156 |
| candidate_ppopt147_operation_tail_dual__mid_0p65__tail_0p45__hpen_0p45__cap_0p006__9cd5b21b98 | 0.270062 | 0.807463 | -0.000502 | -0.000036 | 0.916346 | 0.528846 | -0.017156 |
| candidate_ppopt147_operation_tail_dual__mid_0p65__tail_0p45__hpen_0p45__cap_0p014__1d2548ca01 | 0.270062 | 0.807463 | -0.000502 | -0.000036 | 0.916346 | 0.528846 | -0.017156 |
| candidate_ppopt147_operation_tail_dual__mid_0p65__tail_0p45__hpen_0p45__cap_0p018__0ee92ed21a | 0.270062 | 0.807463 | -0.000502 | -0.000036 | 0.916346 | 0.528846 | -0.017156 |
| candidate_ppopt147_operation_tail_dual__mid_0p65__tail_0p45__hpen_0p45__cap_0p01__867c7f26ae | 0.270062 | 0.807463 | -0.000502 | -0.000036 | 0.916346 | 0.528846 | -0.017156 |
| candidate_ppopt147_operation_tail_dual__mid_0p65__tail_0p45__hpen_0p65__cap_0p006__59b2c36f1c | 0.270062 | 0.807463 | -0.000502 | -0.000036 | 0.916346 | 0.528846 | -0.017156 |
| candidate_ppopt147_operation_tail_dual__mid_0p65__tail_0p45__hpen_0p65__cap_0p014__d339c97ff7 | 0.270062 | 0.807463 | -0.000502 | -0.000036 | 0.916346 | 0.528846 | -0.017156 |
| candidate_ppopt147_operation_tail_dual__mid_0p65__tail_0p45__hpen_0p65__cap_0p018__295c735e37 | 0.270062 | 0.807463 | -0.000502 | -0.000036 | 0.916346 | 0.528846 | -0.017156 |
| candidate_ppopt147_operation_tail_dual__mid_0p65__tail_0p45__hpen_0p65__cap_0p01__41ab1d23f7 | 0.270062 | 0.807463 | -0.000502 | -0.000036 | 0.916346 | 0.528846 | -0.017156 |
| pp134_operational_recomputed_reference | 0.270033 | 0.807490 | -0.000531 | -0.000009 | 0.909936 | 0.496474 | -0.016928 |
| candidate_ppopt144_learned_adopt__target_direct_lgb_huber_s0p18_cap0p01__thr_0p32__w_0p14__hpen_0p2__s__973f19cf51 | 0.269912 | 0.807028 | -0.000652 | -0.000471 | 0.903846 | 0.647756 | -0.016806 |
| pp118_operational_reference | 0.270139 | 0.807490 | -0.000425 | -0.000009 | 0.909295 | 0.494551 | -0.016797 |
| candidate_ppopt144_learned_adopt__target_direct_lgb_huber_s0p18_cap0p01__thr_0p32__w_0p14__hpen_0p45____5e5c70b535 | 0.269911 | 0.807028 | -0.000653 | -0.000471 | 0.903526 | 0.647756 | -0.016794 |
| candidate_ppopt144_learned_adopt__target_direct_lgb_huber_s0p18_cap0p01__thr_0p32__w_0p14__hpen_0p7__s__4a1c835585 | 0.269910 | 0.807028 | -0.000654 | -0.000471 | 0.902244 | 0.647756 | -0.016743 |
| candidate_ppopt144_learned_adopt__target_direct_lgb_huber_s0p18_cap0p01__thr_0p32__w_0p08__hpen_0p7__s__1960e5811d | 0.269917 | 0.806719 | -0.000647 | -0.000780 | 0.900962 | 0.628526 | -0.016686 |
| candidate_ppopt144_learned_adopt__target_direct_lgb_huber_s0p18_cap0p01__thr_0p32__w_0p08__hpen_0p7__s__dec707db1a | 0.269917 | 0.806719 | -0.000647 | -0.000780 | 0.900962 | 0.628526 | -0.016686 |
| pp126_p95_reference | 0.270317 | 0.807465 | -0.000247 | -0.000034 | 0.909936 | 0.665705 | -0.016645 |
| candidate_ppopt143_tail_risk_router__target_direct_lgb_l2_s0p18_cap0p01__thr_0p28__w_0p1__s_0p35__cap___5c31bb01b5 | 0.270125 | 0.807351 | -0.000439 | -0.000148 | 0.904167 | 0.708333 | -0.016606 |
| candidate_ppopt143_tail_risk_router__target_direct_lgb_l2_s0p18_cap0p01__thr_0p28__w_0p1__s_0p35__cap___61be25cae0 | 0.270125 | 0.807351 | -0.000439 | -0.000148 | 0.904167 | 0.708333 | -0.016606 |
| candidate_ppopt143_tail_risk_router__target_direct_lgb_l2_s0p18_cap0p01__thr_0p28__w_0p1__s_0p35__cap___dc5a8b0aae | 0.270125 | 0.807351 | -0.000439 | -0.000148 | 0.904167 | 0.708333 | -0.016606 |
| pp134_p95_recomputed_reference | 0.270242 | 0.807488 | -0.000322 | -0.000010 | 0.907051 | 0.492628 | -0.016604 |
| candidate_ppopt144_learned_adopt__target_direct_lgb_huber_s0p18_cap0p01__thr_0p32__w_0p08__hpen_0p45____3584727bb3 | 0.269918 | 0.806721 | -0.000646 | -0.000778 | 0.898397 | 0.628526 | -0.016581 |
| candidate_ppopt144_learned_adopt__target_direct_lgb_huber_s0p18_cap0p01__thr_0p32__w_0p08__hpen_0p45____394798fa0b | 0.269918 | 0.806721 | -0.000646 | -0.000778 | 0.898397 | 0.628526 | -0.016581 |
| candidate_ppopt143_tail_risk_router__target_direct_lgb_l2_s0p18_cap0p01__thr_0p28__w_0p24__s_0p75__cap__7b5ac7abb7 | 0.270092 | 0.807251 | -0.000472 | -0.000248 | 0.902244 | 0.703205 | -0.016561 |
| candidate_ppopt143_tail_risk_router__target_direct_lgb_l2_s0p18_cap0p01__thr_0p28__w_0p24__s_0p75__cap__d41e053c89 | 0.270092 | 0.807251 | -0.000472 | -0.000248 | 0.902244 | 0.703205 | -0.016561 |
| candidate_ppopt143_tail_risk_router__target_direct_lgb_l2_s0p18_cap0p01__thr_0p28__w_0p24__s_0p75__cap__e4f3c4dde8 | 0.270092 | 0.807251 | -0.000472 | -0.000248 | 0.902244 | 0.703205 | -0.016561 |
| candidate_ppopt144_learned_adopt__target_direct_lgb_huber_s0p18_cap0p01__thr_0p32__w_0p08__hpen_0p2__s__3a4c46f22a | 0.269921 | 0.806724 | -0.000643 | -0.000775 | 0.897436 | 0.628526 | -0.016541 |
| candidate_ppopt144_learned_adopt__target_direct_lgb_huber_s0p18_cap0p01__thr_0p32__w_0p08__hpen_0p2__s__686b7f5f44 | 0.269921 | 0.806724 | -0.000643 | -0.000775 | 0.897436 | 0.628526 | -0.016541 |
| candidate_ppopt143_tail_risk_router__target_direct_lgb_l2_s0p18_cap0p01__thr_0p28__w_0p16__s_0p55__cap__1b32128ea4 | 0.270108 | 0.807271 | -0.000456 | -0.000228 | 0.900000 | 0.704167 | -0.016456 |
| candidate_ppopt143_tail_risk_router__target_direct_lgb_l2_s0p18_cap0p01__thr_0p28__w_0p16__s_0p55__cap__2b2ea1dc2a | 0.270108 | 0.807271 | -0.000456 | -0.000228 | 0.900000 | 0.704167 | -0.016456 |
| candidate_ppopt143_tail_risk_router__target_direct_lgb_l2_s0p18_cap0p01__thr_0p28__w_0p16__s_0p55__cap__85d6d3aba9 | 0.270108 | 0.807271 | -0.000456 | -0.000228 | 0.900000 | 0.704167 | -0.016456 |
| candidate_ppopt143_tail_risk_router__target_direct_lgb_l2_s0p18_cap0p01__thr_0p28__w_0p24__s_1p0__cap___c79530f4b4 | 0.270089 | 0.807171 | -0.000475 | -0.000328 | 0.896474 | 0.702885 | -0.016334 |
| candidate_ppopt144_learned_adopt__target_direct_lgb_huber_s0p18_cap0p01__thr_0p32__w_0p14__hpen_0p45____9f3340a5fe | 0.269931 | 0.806837 | -0.000633 | -0.000661 | 0.888782 | 0.647756 | -0.016185 |
| candidate_ppopt144_learned_adopt__target_direct_lgb_huber_s0p18_cap0p01__thr_0p32__w_0p14__hpen_0p2__s__645a22d646 | 0.269929 | 0.806839 | -0.000635 | -0.000659 | 0.886538 | 0.647756 | -0.016096 |
| candidate_ppopt144_learned_adopt__target_direct_lgb_huber_s0p18_cap0p01__thr_0p32__w_0p14__hpen_0p2__s__717b398074 | 0.269929 | 0.806839 | -0.000635 | -0.000659 | 0.886538 | 0.647756 | -0.016096 |
| candidate_ppopt143_tail_risk_router__target_direct_lgb_l2_s0p18_cap0p01__thr_0p28__w_0p1__s_0p55__cap___2e9277142e | 0.270131 | 0.807271 | -0.000433 | -0.000228 | 0.890705 | 0.703205 | -0.016061 |
| candidate_ppopt143_tail_risk_router__target_direct_lgb_l2_s0p18_cap0p01__thr_0p28__w_0p1__s_0p55__cap___76a2a5a34d | 0.270131 | 0.807271 | -0.000433 | -0.000228 | 0.890705 | 0.703205 | -0.016061 |
| candidate_ppopt143_tail_risk_router__target_direct_lgb_l2_s0p18_cap0p01__thr_0p28__w_0p1__s_0p55__cap___d1ef42b695 | 0.270131 | 0.807271 | -0.000433 | -0.000228 | 0.890705 | 0.703205 | -0.016061 |
| candidate_ppopt144_learned_adopt__target_direct_lgb_huber_s0p18_cap0p01__thr_0p32__w_0p14__hpen_0p7__s__186185a71c | 0.269903 | 0.806719 | -0.000661 | -0.000780 | 0.877885 | 0.647436 | -0.015777 |
| candidate_ppopt144_learned_adopt__target_direct_lgb_huber_s0p18_cap0p01__thr_0p32__w_0p14__hpen_0p7__s__33d9b1621b | 0.269903 | 0.806719 | -0.000661 | -0.000780 | 0.877885 | 0.647436 | -0.015777 |
| candidate_ppopt144_learned_adopt__target_direct_lgb_huber_s0p18_cap0p01__thr_0p32__w_0p14__hpen_0p45____ecb1832b30 | 0.269901 | 0.806721 | -0.000663 | -0.000778 | 0.876603 | 0.647436 | -0.015727 |
| candidate_ppopt144_learned_adopt__target_direct_lgb_huber_s0p18_cap0p01__thr_0p32__w_0p14__hpen_0p45____ef54cbe840 | 0.269901 | 0.806721 | -0.000663 | -0.000778 | 0.876603 | 0.647436 | -0.015727 |
| candidate_ppopt144_learned_adopt__target_direct_lgb_huber_s0p18_cap0p01__thr_0p32__w_0p14__hpen_0p2__s__29e3cad03c | 0.269899 | 0.806724 | -0.000665 | -0.000775 | 0.874359 | 0.647436 | -0.015639 |
| candidate_ppopt144_learned_adopt__target_direct_lgb_huber_s0p18_cap0p01__thr_0p32__w_0p14__hpen_0p2__s__fee1ba9e41 | 0.269899 | 0.806724 | -0.000665 | -0.000775 | 0.874359 | 0.647436 | -0.015639 |
| pp81_stable_reference | 0.270559 | 0.807490 | -0.000005 | -0.000009 | 0.890705 | 0.410256 | -0.015633 |
| pp95_operational_reference | 0.270559 | 0.807490 | -0.000005 | -0.000009 | 0.890705 | 0.410256 | -0.015633 |
| candidate_ppopt143_tail_risk_router__target_direct_lgb_l2_s0p18_cap0p01__thr_0p28__w_0p1__s_0p75__cap___ef3fc137e9 | 0.270129 | 0.807191 | -0.000435 | -0.000308 | 0.876603 | 0.704167 | -0.015500 |
| candidate_ppopt143_tail_risk_router__target_direct_lgb_l2_s0p18_cap0p01__thr_0p28__w_0p1__s_0p75__cap___5e51667c12 | 0.270140 | 0.807191 | -0.000424 | -0.000308 | 0.875962 | 0.701603 | -0.015463 |
| candidate_ppopt143_tail_risk_router__target_direct_lgb_l2_s0p18_cap0p01__thr_0p28__w_0p1__s_0p75__cap___de822654ce | 0.270140 | 0.807191 | -0.000424 | -0.000308 | 0.875962 | 0.701603 | -0.015463 |
| candidate_ppopt143_tail_risk_router__target_direct_lgb_l2_s0p18_cap0p01__thr_0p28__w_0p1__s_1p0__cap_0__ccd3d86eb0 | 0.270127 | 0.807158 | -0.000437 | -0.000341 | 0.874679 | 0.706410 | -0.015424 |
| candidate_ppopt143_tail_risk_router__target_direct_lgb_l2_s0p18_cap0p01__thr_0p28__w_0p1__s_1p0__cap_0__a193b12bd5 | 0.270153 | 0.807091 | -0.000411 | -0.000408 | 0.856090 | 0.703846 | -0.014655 |
| candidate_ppopt143_tail_risk_router__target_direct_lgb_l2_s0p18_cap0p01__thr_0p28__w_0p1__s_1p0__cap_0__04cb5b731c | 0.270154 | 0.807091 | -0.000410 | -0.000408 | 0.856090 | 0.703846 | -0.014654 |
| candidate_ppopt144_learned_adopt__target_direct_lgb_huber_s0p18_cap0p01__thr_0p4__w_0p08__hpen_0p7__s___42a7155499 | 0.269917 | 0.806719 | -0.000647 | -0.000780 | 0.841667 | 0.587500 | -0.014314 |
| candidate_ppopt144_learned_adopt__target_direct_lgb_huber_s0p18_cap0p01__thr_0p4__w_0p08__hpen_0p7__s___f31404d0e9 | 0.269917 | 0.806719 | -0.000647 | -0.000780 | 0.841667 | 0.587500 | -0.014314 |
| candidate_ppopt144_learned_adopt__target_direct_lgb_huber_s0p18_cap0p01__thr_0p4__w_0p08__hpen_0p45__s__110bc9bb8b | 0.269913 | 0.806721 | -0.000651 | -0.000778 | 0.840064 | 0.587500 | -0.014254 |
| candidate_ppopt144_learned_adopt__target_direct_lgb_huber_s0p18_cap0p01__thr_0p4__w_0p08__hpen_0p45__s__5d47f00897 | 0.269913 | 0.806721 | -0.000651 | -0.000778 | 0.840064 | 0.587500 | -0.014254 |
| candidate_ppopt144_learned_adopt__target_direct_lgb_huber_s0p18_cap0p01__thr_0p4__w_0p08__hpen_0p2__s___9f30cb105c | 0.269909 | 0.806724 | -0.000655 | -0.000775 | 0.837500 | 0.585897 | -0.014155 |
| candidate_ppopt144_learned_adopt__target_direct_lgb_huber_s0p18_cap0p01__thr_0p4__w_0p08__hpen_0p2__s___e8ebf91669 | 0.269909 | 0.806724 | -0.000655 | -0.000775 | 0.837500 | 0.585897 | -0.014155 |
| pp70_refinement_candidate | 0.270561 | 0.807490 | -0.000003 | -0.000009 | 0.786859 | 0.398077 | -0.011477 |

## 실행 설정
```json
{
  "experiment_id": "PP-OPT143-148",
  "experiment_slug": "PP-OPT143_148_warm_row_level_tail_router",
  "created_at": "2026-06-09T16:38:04",
  "seed": 20260609,
  "base_candidate": "hcoef_stable",
  "incumbent_candidate": "incumbent_operational_pp_opt7",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 2717,
  "prediction_rows": 3059342,
  "selected_references": {
    "pp64": "reference_pp64_current_best",
    "pp70": "reference_pp70_refinement",
    "pp81": "reference_pp81_best",
    "pp82_op": "reference_pp82_operational",
    "pp82_p95": "reference_pp82_p95",
    "pp95_op": "reference_pp95_operational",
    "pp95_p95": "reference_pp95_p95",
    "pp102_op": "reference_pp102_operational",
    "pp110_op": "ppopt110_operational_guarded_pp102_challenger__source=ppopt104_margin_gate__gain_gain_any__hpen_1p05__rpen_0p0__thr_0p14__s_1p0",
    "pp110_p95": "ppopt110_p95_guarded_pp102_challenger__source=ppopt108_tail_hybrid__target_pp82_p95__opthr_0p02__tailthr_0p08__tails_0p4",
    "pp118_op": "ppopt118_operational_next_dimension_challenger__source=ppopt116_hybrid_stack_router__target_huber_stack_weighted__thr_0p12__s_0p75",
    "pp118_p95": "ppopt118_p95_next_dimension_challenger__source=ppopt111_meta_router__set_tail_mix__thr_0p22__s_1p0",
    "pp111_p95_source": "ppopt111_meta_router__set=tail_mix__thr=0p22__s=1p0",
    "pp126_op": "ppopt126_operational_stack_gate_challenger__source=ppopt119_fine_gate__safe_pp81__policy_less_harm__thr_0p1__width_0p16__s_0p75",
    "pp126_p95": "ppopt126_p95_stack_gate_challenger__source=ppopt124_p95_limited__target_pp82_p95__thr_0p08__mpen_0p2__s_0p4",
    "pp119_operational_source": "ppopt119_fine_gate__safe=pp81__policy=less_harm__thr=0p1__width=0p16__s=0p75",
    "pp119_p95_source": "ppopt124_p95_limited__target=pp82_p95__thr=0p08__mpen=0p2__s=0p4",
    "pp119_guarded_mape": "ppopt124_p95_limited__target=xgb_direct__thr=0p32__mpen=0p2__s=0p4",
    "pp119_aggressive_mape": "ppopt123_aggressive_rollback__target=huber_weighted__safe=pp118_op__cap=0p055__rollback=0p25__floor=0p0",
    "pp119_stable_best": "ppopt119_fine_gate__safe=pp81__policy=less_harm__thr=0p1__width=0p16__s=0p75"
  },
  "selected_pp119_sources": {
    "pp126_op": "ppopt126_operational_stack_gate_challenger__source=ppopt119_fine_gate__safe_pp81__policy_less_harm__thr_0p1__width_0p16__s_0p75",
    "pp126_p95": "ppopt126_p95_stack_gate_challenger__source=ppopt124_p95_limited__target_pp82_p95__thr_0p08__mpen_0p2__s_0p4",
    "pp119_operational_source": "ppopt119_fine_gate__safe=pp81__policy=less_harm__thr=0p1__width=0p16__s=0p75",
    "pp119_p95_source": "ppopt124_p95_limited__target=pp82_p95__thr=0p08__mpen=0p2__s=0p4",
    "pp119_guarded_mape": "ppopt124_p95_limited__target=xgb_direct__thr=0p32__mpen=0p2__s=0p4",
    "pp119_aggressive_mape": "ppopt123_aggressive_rollback__target=huber_weighted__safe=pp118_op__cap=0p055__rollback=0p25__floor=0p0",
    "pp119_stable_best": "ppopt119_fine_gate__safe=pp81__policy=less_harm__thr=0p1__width=0p16__s=0p75"
  },
  "recomputed_reference_notes": {
    "pp134_op_recomputed": "PP134 운영 후보 재계산: learned harm rollback",
    "pp134_p95_recomputed": "PP134 p95 후보 재계산: p95 tail router"
  },
  "selection_decision": {
    "operational_label": "candidate_ppopt146_hard_switch__target_direct_lgb_l2_s0p18_cap0p01__thr_0p42__tail_0p0__s_0p65__cap_0p__49f1fee265",
    "operational_candidate": "ppopt146_hard_switch__target=direct_lgb_l2_s0p18_cap0p01__thr=0p42__tail=0p0__s=0p65__cap=0p01",
    "operational_fixed_test_MAPE": 0.27013998837257946,
    "operational_fixed_test_p95_APE": 0.8072309115386983,
    "operational_delta_vs_pp64_MAPE": -0.0004240535430808934,
    "operational_delta_vs_pp64_p95_APE": -0.00026794076741154527,
    "operational_delta_vs_pp126_MAPE": 2.5591622727638708e-05,
    "operational_delta_vs_pp126_p95_APE": -0.000259149359149613,
    "operational_avg_pp64_MAPE_win_rate": 0.9259615384615385,
    "operational_avg_pp64_p95_win_rate": 0.5310897435897436,
    "operational_replacement_score": -0.017462515081542434,
    "p95_label": "candidate_ppopt144_learned_adopt__target_direct_lgb_l2_s0p18_cap0p01__thr_0p24__w_0p08__hpen_0p2__s_1p__43151e1066",
    "p95_candidate": "ppopt144_learned_adopt__target=direct_lgb_l2_s0p18_cap0p01__thr=0p24__w=0p08__hpen=0p2__s=1p0__cap=0p014",
    "p95_fixed_test_MAPE": 0.27026892590910795,
    "p95_fixed_test_p95_APE": 0.8059493758221674,
    "p95_delta_vs_pp64_MAPE": -0.00029511600655240944,
    "p95_delta_vs_pp64_p95_APE": -0.0015494764839424358,
    "p95_delta_vs_pp126_MAPE": 0.00015452915925612265,
    "p95_delta_vs_pp126_p95_APE": -0.0015406850756805035,
    "p95_avg_pp64_MAPE_win_rate": 0.5983974358974359,
    "p95_avg_pp64_p95_win_rate": 0.5009615384615385,
    "p95_replacement_score": -0.004079289919262468,
    "operational_protocol_candidate": "ppopt148_operational_row_level_tail_router_challenger__source=ppopt146_hard_switch__target_direct_lgb_l2_s0p18_cap0p01__thr_0p42__tail_0p0__s_0p65__cap_0p01",
    "p95_protocol_candidate": "ppopt148_p95_row_level_tail_router_challenger__source=ppopt144_learned_adopt__target_direct_lgb_l2_s0p18_cap0p01__thr_0p24__w_0p08__hpen_0p2__s_1p0__cap_0p014"
  },
  "items": [
    {
      "item_id": "PP-OPT143",
      "priority": "1",
      "title": "tail-risk row-only direct-meta router",
      "description": "PP126을 기본값으로 두고 p95 위험 점수가 높은 row에서만 direct-meta p95 후보로 이동한다."
    },
    {
      "item_id": "PP-OPT144",
      "priority": "2",
      "title": "learned adoption probability router",
      "description": "validation OOF에서 direct-meta 후보가 PP126보다 좋아진 row를 학습해 적용 확률로 사용한다."
    },
    {
      "item_id": "PP-OPT145",
      "priority": "3",
      "title": "direction-consensus guarded router",
      "description": "direct-meta, quantile median, p95 후보의 이동 방향이 동의할 때만 보정을 적용한다."
    },
    {
      "item_id": "PP-OPT146",
      "priority": "4",
      "title": "hard-switch quantile router",
      "description": "적용 확률 상위 row에만 아주 작은 hard switch를 허용하고 나머지는 PP126으로 유지한다."
    },
    {
      "item_id": "PP-OPT147",
      "priority": "5",
      "title": "operation-tail dual router",
      "description": "중간 위험 구간은 PP134 운영 보정, 큰 tail 위험 구간은 direct-meta p95 보정을 섞는다."
    },
    {
      "item_id": "PP-OPT148",
      "priority": "6",
      "title": "final row-level tail-router decision",
      "description": "PP126/PP134/PP139와 row-level router 후보를 같은 fixed/repeated 기준으로 비교한다."
    }
  ],
  "sources": {
    "pp135_helper": "scripts/track6/run_pp_opt135_138_warm_p95_aware_correction.py",
    "pp139_helper": "scripts/track6/run_pp_opt139_142_warm_direct_meta_stack.py"
  }
}
```