# PP-OPT139~142 Warm direct meta-stack 결과

- 작성일: 2026-06-09 16:24
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 목적: 사후 보정이 아니라 direct meta-stack/quantile meta 기준가로 큰 개선 가능성 확인
- 결론: 운영 후보 fixed test MAPE 0.270114, p95 0.807490. PP126 대비 MAPE +0.000000, p95 +0.000000.

## 주요 후보 test 비교
| candidate | family | item_id | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| reference_pp134_operational_recomputed | reference_prior | REFERENCE | 0.136320 | 0.270033 | 0.807490 | 0.397520 | -0.001362 | -0.000640 |
| reference_pp126_operational | reference_prior | REFERENCE | 0.136320 | 0.270114 | 0.807490 | 0.397588 | -0.001280 | -0.000640 |
| ppopt142_operational_direct_meta_stack_challenger__source=reference_pp126_operational | direct_meta_stack_operational_selection | PP-OPT142 | 0.136320 | 0.270114 | 0.807490 | 0.397588 | -0.001280 | -0.000640 |
| reference_pp126_p95 | reference_prior | REFERENCE | 0.137871 | 0.270317 | 0.807465 | 0.397768 | -0.001078 | -0.000665 |
| reference_pp64_current_best | reference_prior | REFERENCE | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |
| ppopt142_p95_direct_meta_stack_challenger__source=ppopt139_direct_meta__target_lgb_l2__s_0p18__cap_0p01 | direct_meta_stack_p95_selection | PP-OPT142 | 0.139554 | 0.270699 | 0.805930 | 0.397266 | -0.000696 | -0.002200 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | p95_test_MAPE | p95_test_p95_APE | operational_pass_vs_incumbent | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4 | final direct meta-stack decision | 2 | 0.270114 | 0.807490 | 0.270699 | 0.805930 | True | direct_meta_stack_operational_selection | ppopt142_operational_direct_meta_stack_challenger__source=reference_pp126_operational |
| 2 | quantile meta basis with uncertainty cap | 48 | 0.270189 | 0.807613 | 0.270189 | 0.807613 | False | quantile_meta_basis_uncertainty_cap | ppopt140_quantile_meta__wpen=0p85__s=0p16__cap=0p01 |
| 3 | two-head direct meta with tail guard | 108 | 0.270382 | 0.806762 | 0.271372 | 0.805582 | False | two_head_direct_meta_tail_guard | ppopt141_two_head_meta__target=lgb_huber__rthr=0p45__s=0p38__cap=0p01 |
| 1 | direct LightGBM meta-stack basis | 80 | 0.270715 | 0.805930 | 0.271223 | 0.804988 | False | direct_lgbm_meta_stack_basis | ppopt139_direct_meta__target=lgb_l2__s=0p28__cap=0p01 |

## 탐색 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt142_operational_direct_meta_stack_challenger__source=reference_pp126_operational | PP-OPT142 | direct_meta_stack_operational_selection | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt140_quantile_meta__wpen=0p85__s=0p16__cap=0p01 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270189 | 0.807613 | -0.001206 | -0.000517 | -0.001845 |
| ppopt140_quantile_meta__wpen=0p85__s=0p24__cap=0p01 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270218 | 0.807675 | -0.001177 | -0.000455 | -0.001761 |
| ppopt140_quantile_meta__wpen=0p85__s=0p46__cap=0p01 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270267 | 0.807844 | -0.001127 | -0.000286 | -0.001741 |
| ppopt140_quantile_meta__wpen=0p85__s=0p16__cap=0p016 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270231 | 0.807613 | -0.001164 | -0.000517 | -0.001730 |
| ppopt140_quantile_meta__wpen=0p85__s=0p34__cap=0p01 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270252 | 0.807752 | -0.001142 | -0.000378 | -0.001725 |
| ppopt140_quantile_meta__wpen=0p85__s=0p24__cap=0p016 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270247 | 0.807675 | -0.001148 | -0.000455 | -0.001665 |
| ppopt140_quantile_meta__wpen=0p65__s=0p16__cap=0p01 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270287 | 0.808190 | -0.001108 | 0.000060 | -0.001649 |
| ppopt140_quantile_meta__wpen=0p85__s=0p16__cap=0p024 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270250 | 0.807613 | -0.001145 | -0.000517 | -0.001617 |
| ppopt140_quantile_meta__wpen=0p45__s=0p16__cap=0p01 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270317 | 0.808249 | -0.001078 | 0.000119 | -0.001596 |
| ppopt140_quantile_meta__wpen=0p85__s=0p16__cap=0p034 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270268 | 0.807613 | -0.001127 | -0.000517 | -0.001586 |
| ppopt140_quantile_meta__wpen=0p65__s=0p24__cap=0p01 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270304 | 0.808249 | -0.001091 | 0.000119 | -0.001562 |
| ppopt140_quantile_meta__wpen=0p45__s=0p24__cap=0p01 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270345 | 0.808249 | -0.001050 | 0.000119 | -0.001501 |
| ppopt140_quantile_meta__wpen=0p65__s=0p34__cap=0p01 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270326 | 0.808249 | -0.001069 | 0.000119 | -0.001462 |
| ppopt140_quantile_meta__wpen=0p45__s=0p46__cap=0p01 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270348 | 0.808249 | -0.001047 | 0.000119 | -0.001410 |
| ppopt140_quantile_meta__wpen=0p85__s=0p34__cap=0p016 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270287 | 0.807752 | -0.001108 | -0.000378 | -0.001407 |
| ppopt140_quantile_meta__wpen=0p65__s=0p46__cap=0p01 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270344 | 0.808249 | -0.001051 | 0.000119 | -0.001402 |
| ppopt140_quantile_meta__wpen=0p45__s=0p34__cap=0p01 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270359 | 0.808249 | -0.001036 | 0.000119 | -0.001389 |
| ppopt140_quantile_meta__wpen=0p85__s=0p24__cap=0p024 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270303 | 0.807675 | -0.001092 | -0.000455 | -0.001325 |
| ppopt140_quantile_meta__wpen=0p85__s=0p46__cap=0p016 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270334 | 0.807844 | -0.001061 | -0.000286 | -0.001268 |
| ppopt140_quantile_meta__wpen=0p65__s=0p16__cap=0p016 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270395 | 0.808213 | -0.001000 | 0.000083 | -0.001226 |
| ppopt141_two_head_meta__target=lgb_huber__rthr=0p45__s=0p38__cap=0p01 | PP-OPT141 | two_head_direct_meta_tail_guard | 0.270382 | 0.806762 | -0.001013 | -0.001368 | -0.001088 |
| ppopt140_quantile_meta__wpen=0p85__s=0p34__cap=0p024 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270331 | 0.807752 | -0.001064 | -0.000378 | -0.000995 |
| ppopt140_quantile_meta__wpen=0p85__s=0p24__cap=0p034 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270330 | 0.807675 | -0.001064 | -0.000455 | -0.000941 |
| ppopt141_two_head_meta__target=lgb_huber__rthr=0p45__s=0p5__cap=0p01 | PP-OPT141 | two_head_direct_meta_tail_guard | 0.270413 | 0.806762 | -0.000981 | -0.001368 | -0.000859 |
| ppopt141_two_head_meta__target=lgb_huber__rthr=0p45__s=0p26__cap=0p01 | PP-OPT141 | two_head_direct_meta_tail_guard | 0.270419 | 0.806762 | -0.000976 | -0.001368 | -0.000759 |
| ppopt140_quantile_meta__wpen=0p65__s=0p24__cap=0p016 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270414 | 0.808559 | -0.000981 | 0.000429 | -0.000690 |
| ppopt140_quantile_meta__wpen=0p45__s=0p16__cap=0p016 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270424 | 0.808680 | -0.000971 | 0.000550 | -0.000606 |
| ppopt141_two_head_meta__target=lgb_huber__rthr=0p45__s=0p16__cap=0p01 | PP-OPT141 | two_head_direct_meta_tail_guard | 0.270420 | 0.806736 | -0.000975 | -0.001394 | -0.000419 |
| ppopt140_quantile_meta__wpen=0p85__s=0p46__cap=0p024 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270370 | 0.807844 | -0.001025 | -0.000286 | -0.000413 |
| ppopt141_two_head_meta__target=lgb_huber__rthr=0p65__s=0p5__cap=0p01 | PP-OPT141 | two_head_direct_meta_tail_guard | 0.270475 | 0.806762 | -0.000919 | -0.001368 | -0.000381 |
| ppopt140_quantile_meta__wpen=0p85__s=0p34__cap=0p034 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270399 | 0.807752 | -0.000996 | -0.000378 | -0.000351 |
| ppopt141_two_head_meta__target=lgb_huber__rthr=0p65__s=0p16__cap=0p01 | PP-OPT141 | two_head_direct_meta_tail_guard | 0.270482 | 0.806736 | -0.000913 | -0.001394 | -0.000342 |
| ppopt141_two_head_meta__target=lgb_huber__rthr=0p55__s=0p5__cap=0p01 | PP-OPT141 | two_head_direct_meta_tail_guard | 0.270431 | 0.806762 | -0.000964 | -0.001368 | -0.000333 |
| ppopt141_two_head_meta__target=lgb_huber__rthr=0p55__s=0p16__cap=0p01 | PP-OPT141 | two_head_direct_meta_tail_guard | 0.270437 | 0.806736 | -0.000958 | -0.001394 | -0.000294 |
| ppopt141_two_head_meta__target=lgb_huber__rthr=0p65__s=0p38__cap=0p01 | PP-OPT141 | two_head_direct_meta_tail_guard | 0.270444 | 0.806762 | -0.000951 | -0.001368 | -0.000292 |
| ppopt141_two_head_meta__target=lgb_huber__rthr=0p55__s=0p38__cap=0p01 | PP-OPT141 | two_head_direct_meta_tail_guard | 0.270400 | 0.806762 | -0.000995 | -0.001368 | -0.000252 |
| ppopt140_quantile_meta__wpen=0p65__s=0p34__cap=0p016 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270441 | 0.808702 | -0.000954 | 0.000572 | -0.000218 |
| ppopt141_two_head_meta__target=lgb_huber__rthr=0p65__s=0p26__cap=0p01 | PP-OPT141 | two_head_direct_meta_tail_guard | 0.270481 | 0.806762 | -0.000914 | -0.001368 | -0.000210 |
| ppopt140_quantile_meta__wpen=0p45__s=0p24__cap=0p016 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270464 | 0.808702 | -0.000931 | 0.000572 | -0.000199 |
| ppopt141_two_head_meta__target=lgb_huber__rthr=0p55__s=0p26__cap=0p01 | PP-OPT141 | two_head_direct_meta_tail_guard | 0.270436 | 0.806762 | -0.000959 | -0.001368 | -0.000153 |
| ppopt139_direct_meta__target=lgb_l2__s=0p28__cap=0p01 | PP-OPT139 | direct_lgbm_meta_stack_basis | 0.270715 | 0.805930 | -0.000680 | -0.002200 | -0.000088 |
| ppopt140_quantile_meta__wpen=0p65__s=0p16__cap=0p024 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270460 | 0.808213 | -0.000935 | 0.000083 | -0.000059 |
| ppopt139_direct_meta__target=lgb_l2__s=0p18__cap=0p01 | PP-OPT139 | direct_lgbm_meta_stack_basis | 0.270699 | 0.805930 | -0.000696 | -0.002200 | -0.000039 |
| ppopt142_p95_direct_meta_stack_challenger__source=ppopt139_direct_meta__target_lgb_l2__s_0p18__cap_0p01 | PP-OPT142 | direct_meta_stack_p95_selection | 0.270699 | 0.805930 | -0.000696 | -0.002200 | -0.000039 |
| ppopt139_direct_meta__target=lgb_l2__s=0p4__cap=0p01 | PP-OPT139 | direct_lgbm_meta_stack_basis | 0.270718 | 0.805930 | -0.000677 | -0.002200 | 0.000037 |
| ppopt139_direct_meta__target=lgb_huber__s=0p1__cap=0p01 | PP-OPT139 | direct_lgbm_meta_stack_basis | 0.270467 | 0.806992 | -0.000928 | -0.001138 | 0.000043 |
| ppopt139_direct_meta__target=lgb_l2__s=0p1__cap=0p01 | PP-OPT139 | direct_lgbm_meta_stack_basis | 0.270566 | 0.806315 | -0.000829 | -0.001815 | 0.000061 |
| ppopt139_direct_meta__target=lgb_l2__s=0p55__cap=0p01 | PP-OPT139 | direct_lgbm_meta_stack_basis | 0.270709 | 0.805930 | -0.000686 | -0.002200 | 0.000078 |
| ppopt139_direct_meta__target=lgb_huber__s=0p55__cap=0p01 | PP-OPT139 | direct_lgbm_meta_stack_basis | 0.270572 | 0.806726 | -0.000823 | -0.001404 | 0.000200 |
| ppopt140_quantile_meta__wpen=0p65__s=0p16__cap=0p034 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270456 | 0.808213 | -0.000939 | 0.000083 | 0.000205 |
| ppopt139_direct_meta__target=lgb_huber__s=0p4__cap=0p01 | PP-OPT139 | direct_lgbm_meta_stack_basis | 0.270536 | 0.806726 | -0.000859 | -0.001404 | 0.000211 |
| ppopt139_direct_meta__target=lgb_q50__s=0p1__cap=0p01 | PP-OPT139 | direct_lgbm_meta_stack_basis | 0.270482 | 0.809025 | -0.000913 | 0.000895 | 0.000234 |
| ppopt140_quantile_meta__wpen=0p45__s=0p34__cap=0p016 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270509 | 0.808702 | -0.000886 | 0.000572 | 0.000282 |
| ppopt140_quantile_meta__wpen=0p65__s=0p46__cap=0p016 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270468 | 0.808702 | -0.000927 | 0.000572 | 0.000286 |
| ppopt139_direct_meta__target=lgb_huber__s=0p28__cap=0p01 | PP-OPT139 | direct_lgbm_meta_stack_basis | 0.270536 | 0.806726 | -0.000859 | -0.001404 | 0.000306 |
| ppopt139_direct_meta__target=lgb_huber__s=0p18__cap=0p01 | PP-OPT139 | direct_lgbm_meta_stack_basis | 0.270569 | 0.806726 | -0.000826 | -0.001404 | 0.000337 |
| ppopt141_two_head_meta__target=lgb_q50__rthr=0p45__s=0p16__cap=0p01 | PP-OPT141 | two_head_direct_meta_tail_guard | 0.270525 | 0.808952 | -0.000869 | 0.000822 | 0.000344 |
| ppopt140_quantile_meta__wpen=0p85__s=0p46__cap=0p034 | PP-OPT140 | quantile_meta_basis_uncertainty_cap | 0.270434 | 0.807844 | -0.000961 | -0.000286 | 0.000359 |
| ppopt141_two_head_meta__target=lgb_q50__rthr=0p65__s=0p16__cap=0p01 | PP-OPT141 | two_head_direct_meta_tail_guard | 0.270538 | 0.808998 | -0.000857 | 0.000868 | 0.000428 |

## 선택 후보 반복 안정성
| candidate_label | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_vs_pp64_MAPE | fixed_test_delta_vs_pp64_p95_APE | avg_pp64_MAPE_win_rate | avg_pp64_p95_win_rate | replacement_score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pp126_operational_reference | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| pp142_operational_direct_meta_stack_challenger | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| pp134_operational_recomputed_reference | 0.270033 | 0.807490 | -0.000531 | -0.000009 | 0.909936 | 0.496474 | -0.016928 |
| pp118_operational_reference | 0.270139 | 0.807490 | -0.000425 | -0.000009 | 0.909295 | 0.494551 | -0.016797 |
| pp126_p95_reference | 0.270317 | 0.807465 | -0.000247 | -0.000034 | 0.909936 | 0.665705 | -0.016645 |
| pp134_p95_recomputed_reference | 0.270242 | 0.807488 | -0.000322 | -0.000010 | 0.907051 | 0.492628 | -0.016604 |
| pp81_stable_reference | 0.270559 | 0.807490 | -0.000005 | -0.000009 | 0.890705 | 0.410256 | -0.015633 |
| pp95_operational_reference | 0.270559 | 0.807490 | -0.000005 | -0.000009 | 0.890705 | 0.410256 | -0.015633 |
| candidate_ppopt140_quantile_meta__wpen_0p85__s_0p16__cap_0p01__73b1e3c6f1 | 0.270189 | 0.807613 | -0.000375 | 0.000114 | 0.882372 | 0.368910 | -0.015590 |
| candidate_ppopt140_quantile_meta__wpen_0p85__s_0p24__cap_0p01__f5dd74a181 | 0.270218 | 0.807675 | -0.000346 | 0.000176 | 0.866667 | 0.352885 | -0.014889 |
| candidate_ppopt140_quantile_meta__wpen_0p85__s_0p34__cap_0p01__3f65adb714 | 0.270252 | 0.807752 | -0.000312 | 0.000253 | 0.852564 | 0.354167 | -0.014237 |
| candidate_ppopt140_quantile_meta__wpen_0p85__s_0p16__cap_0p016__0e9eecde43 | 0.270231 | 0.807613 | -0.000333 | 0.000114 | 0.844231 | 0.368590 | -0.014021 |
| candidate_ppopt140_quantile_meta__wpen_0p85__s_0p46__cap_0p01__d8a4601078 | 0.270267 | 0.807844 | -0.000297 | 0.000345 | 0.845192 | 0.366987 | -0.013863 |
| candidate_ppopt140_quantile_meta__wpen_0p85__s_0p24__cap_0p016__fa4272e122 | 0.270247 | 0.807675 | -0.000317 | 0.000176 | 0.835256 | 0.352564 | -0.013542 |
| candidate_ppopt140_quantile_meta__wpen_0p65__s_0p16__cap_0p01__96b97e19e4 | 0.270287 | 0.808190 | -0.000277 | 0.000691 | 0.815705 | 0.380769 | -0.012421 |
| candidate_ppopt140_quantile_meta__wpen_0p85__s_0p16__cap_0p024__2eccec3479 | 0.270250 | 0.807613 | -0.000314 | 0.000114 | 0.803526 | 0.367628 | -0.012304 |
| candidate_ppopt140_quantile_meta__wpen_0p85__s_0p34__cap_0p016__f82758c16a | 0.270287 | 0.807752 | -0.000277 | 0.000253 | 0.799359 | 0.351282 | -0.011929 |
| candidate_ppopt140_quantile_meta__wpen_0p65__s_0p24__cap_0p01__721d936615 | 0.270304 | 0.808249 | -0.000260 | 0.000750 | 0.800962 | 0.362821 | -0.011733 |
| candidate_ppopt140_quantile_meta__wpen_0p85__s_0p16__cap_0p034__f8e4e8ff97 | 0.270268 | 0.807613 | -0.000296 | 0.000114 | 0.786538 | 0.367628 | -0.011607 |
| candidate_ppopt140_quantile_meta__wpen_0p45__s_0p16__cap_0p01__84971dc9b1 | 0.270317 | 0.808249 | -0.000247 | 0.000750 | 0.797756 | 0.367628 | -0.011602 |
| pp70_refinement_candidate | 0.270561 | 0.807490 | -0.000003 | -0.000009 | 0.786859 | 0.398077 | -0.011477 |
| candidate_ppopt140_quantile_meta__wpen_0p65__s_0p34__cap_0p01__2d0dbcebae | 0.270326 | 0.808249 | -0.000238 | 0.000750 | 0.775321 | 0.362179 | -0.010629 |
| candidate_ppopt140_quantile_meta__wpen_0p45__s_0p24__cap_0p01__9708284450 | 0.270345 | 0.808249 | -0.000219 | 0.000750 | 0.774679 | 0.366667 | -0.010586 |
| candidate_ppopt140_quantile_meta__wpen_0p65__s_0p46__cap_0p01__32d2edf1d3 | 0.270344 | 0.808249 | -0.000220 | 0.000750 | 0.768910 | 0.362821 | -0.010324 |
| candidate_ppopt140_quantile_meta__wpen_0p85__s_0p46__cap_0p016__9ff5fe9e71 | 0.270334 | 0.807844 | -0.000230 | 0.000345 | 0.762500 | 0.345833 | -0.010283 |
| candidate_ppopt140_quantile_meta__wpen_0p45__s_0p46__cap_0p01__662b38bb36 | 0.270348 | 0.808249 | -0.000216 | 0.000750 | 0.767949 | 0.367628 | -0.010272 |
| candidate_ppopt140_quantile_meta__wpen_0p45__s_0p34__cap_0p01__a5a36667ff | 0.270359 | 0.808249 | -0.000205 | 0.000750 | 0.762179 | 0.365064 | -0.010041 |
| candidate_ppopt141_two_head_meta__target_lgb_huber__rthr_0p45__s_0p16__cap_0p01__1ca3de23c3 | 0.270420 | 0.806736 | -0.000144 | -0.000763 | 0.725321 | 0.522115 | -0.009157 |
| candidate_ppopt141_two_head_meta__target_lgb_huber__rthr_0p45__s_0p38__cap_0p01__e30f2bb755 | 0.270382 | 0.806762 | -0.000182 | -0.000737 | 0.721154 | 0.521474 | -0.009028 |
| candidate_ppopt141_two_head_meta__target_lgb_huber__rthr_0p45__s_0p26__cap_0p01__79efc1cb72 | 0.270419 | 0.806762 | -0.000145 | -0.000737 | 0.707372 | 0.518910 | -0.008440 |
| candidate_ppopt141_two_head_meta__target_lgb_huber__rthr_0p45__s_0p5__cap_0p01__71ce680301 | 0.270413 | 0.806762 | -0.000151 | -0.000737 | 0.704487 | 0.520833 | -0.008330 |
| candidate_ppopt141_two_head_meta__target_lgb_huber__rthr_0p55__s_0p16__cap_0p01__57f2d5b0ae | 0.270437 | 0.806736 | -0.000127 | -0.000763 | 0.681090 | 0.504487 | -0.007287 |
| candidate_ppopt140_quantile_meta__wpen_0p85__s_0p24__cap_0p024__b218fc3f46 | 0.270303 | 0.807675 | -0.000261 | 0.000176 | 0.675962 | 0.351282 | -0.007011 |
| candidate_ppopt141_two_head_meta__target_lgb_huber__rthr_0p65__s_0p38__cap_0p01__86608d0efe | 0.270444 | 0.806762 | -0.000120 | -0.000737 | 0.671474 | 0.510577 | -0.006979 |
| candidate_ppopt141_two_head_meta__target_lgb_huber__rthr_0p65__s_0p16__cap_0p01__91a6c09f06 | 0.270482 | 0.806736 | -0.000082 | -0.000763 | 0.672756 | 0.511538 | -0.006938 |
| candidate_ppopt139_direct_meta__target_lgb_huber__s_0p1__cap_0p01__62b22abf9c | 0.270467 | 0.806992 | -0.000097 | -0.000507 | 0.667949 | 0.508013 | -0.006653 |
| candidate_ppopt141_two_head_meta__target_lgb_huber__rthr_0p65__s_0p26__cap_0p01__ce91b88e77 | 0.270481 | 0.806762 | -0.000083 | -0.000737 | 0.658333 | 0.509295 | -0.006416 |
| candidate_ppopt140_quantile_meta__wpen_0p85__s_0p34__cap_0p024__4959956665 | 0.270331 | 0.807752 | -0.000233 | 0.000253 | 0.653526 | 0.350000 | -0.005943 |
| candidate_ppopt140_quantile_meta__wpen_0p85__s_0p24__cap_0p034__8e526235d9 | 0.270330 | 0.807675 | -0.000234 | 0.000176 | 0.620833 | 0.343590 | -0.004695 |
| candidate_ppopt140_quantile_meta__wpen_0p85__s_0p46__cap_0p024__a3d092b25b | 0.270370 | 0.807844 | -0.000194 | 0.000345 | 0.624038 | 0.341987 | -0.004547 |
| candidate_ppopt140_quantile_meta__wpen_0p65__s_0p16__cap_0p016__0cbdb1a9f4 | 0.270395 | 0.808213 | -0.000169 | 0.000714 | 0.626603 | 0.371154 | -0.004508 |
| candidate_ppopt141_two_head_meta__target_lgb_huber__rthr_0p55__s_0p38__cap_0p01__3565ae7434 | 0.270400 | 0.806762 | -0.000165 | -0.000737 | 0.595192 | 0.503846 | -0.003972 |
| candidate_ppopt141_two_head_meta__target_lgb_huber__rthr_0p55__s_0p26__cap_0p01__8ccf2c567e | 0.270436 | 0.806762 | -0.000128 | -0.000737 | 0.583654 | 0.501923 | -0.003446 |
| candidate_ppopt141_two_head_meta__target_lgb_huber__rthr_0p55__s_0p5__cap_0p01__4b9a465dc6 | 0.270431 | 0.806762 | -0.000133 | -0.000737 | 0.576923 | 0.503526 | -0.003210 |
| candidate_ppopt141_two_head_meta__target_lgb_huber__rthr_0p65__s_0p5__cap_0p01__e85b35357c | 0.270475 | 0.806762 | -0.000089 | -0.000737 | 0.565385 | 0.510256 | -0.002704 |
| candidate_ppopt139_direct_meta__target_lgb_huber__s_0p28__cap_0p01__b89cf15a01 | 0.270536 | 0.806726 | -0.000028 | -0.000773 | 0.527244 | 0.508974 | -0.001086 |
| candidate_ppopt139_direct_meta__target_lgb_huber__s_0p4__cap_0p01__e0e9bc3523 | 0.270536 | 0.806726 | -0.000028 | -0.000773 | 0.524359 | 0.510577 | -0.001002 |
| pp119_guarded_mape_reference | 0.269759 | 0.807513 | -0.000805 | 0.000014 | 0.502244 | 0.208974 | 0.000686 |
| pp119_aggressive_mape_reference | 0.269384 | 0.812525 | -0.001180 | 0.005026 | 0.537500 | 0.444231 | 0.000838 |
| candidate_ppopt139_direct_meta__target_lgb_huber__s_0p18__cap_0p01__997aeb2566 | 0.270569 | 0.806726 | 0.000005 | -0.000773 | 0.437821 | 0.509295 | 0.002605 |
| candidate_ppopt139_direct_meta__target_lgb_huber__s_0p55__cap_0p01__b5a9adc612 | 0.270572 | 0.806726 | 0.000008 | -0.000773 | 0.428526 | 0.510256 | 0.002867 |
| candidate_ppopt141_two_head_meta__target_lgb_huber__rthr_0p45__s_0p16__cap_0p016__b8fb08d58e | 0.270575 | 0.806736 | 0.000011 | -0.000763 | 0.392628 | 0.500000 | 0.004548 |
| candidate_ppopt139_direct_meta__target_lgb_huber__s_0p1__cap_0p016__b8c5f11197 | 0.270572 | 0.806992 | 0.000008 | -0.000507 | 0.359295 | 0.475000 | 0.006289 |
| candidate_ppopt141_two_head_meta__target_lgb_huber__rthr_0p55__s_0p16__cap_0p016__1e0d31fa21 | 0.270603 | 0.806736 | 0.000039 | -0.000763 | 0.348718 | 0.483333 | 0.006624 |
| candidate_ppopt139_direct_meta__target_lgb_l2__s_0p1__cap_0p01__9dc753c5f9 | 0.270566 | 0.806315 | 0.000002 | -0.001184 | 0.325321 | 0.560577 | 0.007039 |
| candidate_ppopt141_two_head_meta__target_lgb_huber__rthr_0p45__s_0p38__cap_0p016__4c7dc85469 | 0.270772 | 0.806316 | 0.000208 | -0.001183 | 0.331410 | 0.489744 | 0.007069 |
| candidate_ppopt141_two_head_meta__target_lgb_huber__rthr_0p45__s_0p26__cap_0p016__bf8e97b46b | 0.270766 | 0.806259 | 0.000202 | -0.001240 | 0.331410 | 0.492628 | 0.007107 |
| candidate_ppopt141_two_head_meta__target_lgb_huber__rthr_0p55__s_0p26__cap_0p016__4803bd9cd0 | 0.270803 | 0.806259 | 0.000239 | -0.001240 | 0.290385 | 0.476923 | 0.009105 |
| candidate_ppopt141_two_head_meta__target_lgb_huber__rthr_0p65__s_0p26__cap_0p016__b9d7071eea | 0.270875 | 0.806259 | 0.000311 | -0.001240 | 0.287500 | 0.486218 | 0.009250 |
| candidate_ppopt139_direct_meta__target_lgb_l2__s_0p18__cap_0p01__0ba65557b2 | 0.270699 | 0.805930 | 0.000135 | -0.001569 | 0.249038 | 0.555128 | 0.010282 |
| pp142_p95_direct_meta_stack_challenger | 0.270699 | 0.805930 | 0.000135 | -0.001569 | 0.249038 | 0.555128 | 0.010282 |
| candidate_ppopt139_direct_meta__target_lgb_l2__s_0p28__cap_0p01__b97f46338a | 0.270715 | 0.805930 | 0.000151 | -0.001569 | 0.244231 | 0.536218 | 0.010498 |
| candidate_ppopt139_direct_meta__target_lgb_l2__s_0p55__cap_0p01__dafed46416 | 0.270709 | 0.805930 | 0.000145 | -0.001569 | 0.237821 | 0.521795 | 0.010765 |
| candidate_ppopt139_direct_meta__target_lgb_l2__s_0p1__cap_0p016__de03269227 | 0.270679 | 0.806164 | 0.000115 | -0.001334 | 0.244551 | 0.507372 | 0.010825 |
| candidate_ppopt139_direct_meta__target_lgb_l2__s_0p4__cap_0p01__f1410962bc | 0.270718 | 0.805930 | 0.000154 | -0.001569 | 0.235897 | 0.526923 | 0.010848 |
| candidate_ppopt139_direct_meta__target_lgb_huber__s_0p55__cap_0p016__6a9ecd6ec2 | 0.270952 | 0.806261 | 0.000388 | -0.001238 | 0.247436 | 0.484295 | 0.010864 |
| candidate_ppopt139_direct_meta__target_lgb_huber__s_0p4__cap_0p016__1bce0e4fcf | 0.270999 | 0.806261 | 0.000435 | -0.001238 | 0.241667 | 0.478846 | 0.011277 |
| candidate_ppopt139_direct_meta__target_lgb_huber__s_0p28__cap_0p016__5ba7a9544f | 0.271025 | 0.806261 | 0.000461 | -0.001238 | 0.239744 | 0.475962 | 0.011483 |
| candidate_ppopt141_two_head_meta__target_lgb_huber__rthr_0p45__s_0p26__cap_0p024__1b310b75be | 0.271109 | 0.806259 | 0.000545 | -0.001240 | 0.203205 | 0.455449 | 0.013238 |
| candidate_ppopt141_two_head_meta__target_lgb_huber__rthr_0p45__s_0p5__cap_0p024__b1c372a550 | 0.271372 | 0.805582 | 0.000808 | -0.001917 | 0.189423 | 0.459615 | 0.013973 |
| candidate_ppopt141_two_head_meta__target_lgb_huber__rthr_0p45__s_0p38__cap_0p024__9340a35682 | 0.271345 | 0.805682 | 0.000781 | -0.001817 | 0.187500 | 0.457372 | 0.014061 |
| candidate_ppopt139_direct_meta__target_lgb_l2__s_0p18__cap_0p016__53986d3ef0 | 0.271050 | 0.805450 | 0.000486 | -0.002049 | 0.143269 | 0.507692 | 0.015065 |
| candidate_ppopt141_two_head_meta__target_lgb_huber__rthr_0p55__s_0p26__cap_0p024__63fb01f1a9 | 0.271164 | 0.806259 | 0.000600 | -0.001240 | 0.169231 | 0.436859 | 0.015149 |
| candidate_ppopt141_two_head_meta__target_lgb_huber__rthr_0p65__s_0p26__cap_0p024__379cac28e6 | 0.271272 | 0.806259 | 0.000708 | -0.001240 | 0.168590 | 0.446154 | 0.015208 |
| candidate_ppopt139_direct_meta__target_lgb_l2__s_0p4__cap_0p016__21b338e527 | 0.271245 | 0.804988 | 0.000681 | -0.002511 | 0.126603 | 0.510256 | 0.016008 |
| candidate_ppopt139_direct_meta__target_lgb_l2__s_0p28__cap_0p016__67ce7fda4c | 0.271223 | 0.804988 | 0.000658 | -0.002511 | 0.124359 | 0.516987 | 0.016062 |
| candidate_ppopt139_direct_meta__target_lgb_l2__s_0p55__cap_0p016__621a94750e | 0.271262 | 0.804988 | 0.000698 | -0.002511 | 0.124038 | 0.508333 | 0.016149 |
| candidate_ppopt139_direct_meta__target_lgb_l2__s_0p1__cap_0p026__70ef28d7dc | 0.271041 | 0.806164 | 0.000477 | -0.001334 | 0.128526 | 0.480128 | 0.016771 |
| pp82_p95_reference | 0.270651 | 0.806840 | 0.000087 | -0.000659 | 0.056090 | 0.603846 | 0.017948 |
| pp64_current_best | 0.270564 | 0.807499 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.020000 |

## 실행 설정
```json
{
  "experiment_id": "PP-OPT139-142",
  "experiment_slug": "PP-OPT139_142_warm_direct_meta_stack",
  "created_at": "2026-06-09T16:24:33",
  "seed": 20260609,
  "base_candidate": "hcoef_stable",
  "incumbent_candidate": "incumbent_operational_pp_opt7",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 253,
  "prediction_rows": 284878,
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
    "operational_label": "pp126_operational_reference",
    "operational_candidate": "reference_pp126_operational",
    "operational_fixed_test_MAPE": 0.2701143967498518,
    "operational_fixed_test_p95_APE": 0.8074900608978479,
    "operational_delta_vs_pp64_MAPE": -0.0004496451658085321,
    "operational_delta_vs_pp64_p95_APE": -8.791408261932254e-06,
    "operational_delta_vs_pp126_MAPE": 0.0,
    "operational_delta_vs_pp126_p95_APE": 0.0,
    "operational_avg_pp64_MAPE_win_rate": 0.9192307692307692,
    "operational_avg_pp64_p95_win_rate": 0.49423076923076925,
    "operational_replacement_score": -0.0172188759350393,
    "p95_label": "candidate_ppopt139_direct_meta__target_lgb_l2__s_0p18__cap_0p01__0ba65557b2",
    "p95_candidate": "ppopt139_direct_meta__target=lgb_l2__s=0p18__cap=0p01",
    "p95_fixed_test_MAPE": 0.27069888269437203,
    "p95_fixed_test_p95_APE": 0.8059299362274386,
    "p95_delta_vs_pp64_MAPE": 0.00013484077871167566,
    "p95_delta_vs_pp64_p95_APE": -0.0015689160786712675,
    "p95_delta_vs_pp126_MAPE": 0.0005844859445202077,
    "p95_delta_vs_pp126_p95_APE": -0.0015601246704093352,
    "p95_avg_pp64_MAPE_win_rate": 0.24903846153846154,
    "p95_avg_pp64_p95_win_rate": 0.555128205128205,
    "p95_replacement_score": 0.010281910477642871,
    "operational_protocol_candidate": "ppopt142_operational_direct_meta_stack_challenger__source=reference_pp126_operational",
    "p95_protocol_candidate": "ppopt142_p95_direct_meta_stack_challenger__source=ppopt139_direct_meta__target_lgb_l2__s_0p18__cap_0p01"
  },
  "items": [
    {
      "item_id": "PP-OPT139",
      "priority": "1",
      "title": "direct LightGBM meta-stack basis",
      "description": "기존 Warm 후보, direct model, stack model 예측값을 입력으로 validation OOF에서 로그가격을 직접 예측한다."
    },
    {
      "item_id": "PP-OPT140",
      "priority": "2",
      "title": "quantile meta basis with uncertainty cap",
      "description": "q25/q50/q75 meta 예측의 폭을 불확실성으로 보고 폭이 큰 row의 이동량을 줄인다."
    },
    {
      "item_id": "PP-OPT141",
      "priority": "3",
      "title": "two-head direct meta with tail guard",
      "description": "direct meta 예측과 p95/tail-harm 확률을 함께 사용해 큰 이동은 위험 구간에서 축소한다."
    },
    {
      "item_id": "PP-OPT142",
      "priority": "4",
      "title": "final direct meta-stack decision",
      "description": "PP126/PP134와 direct meta 후보를 같은 fixed/repeated 기준으로 비교하고 최종 판단한다."
    }
  ],
  "sources": {
    "pp135_helper": "scripts/track6/run_pp_opt135_138_warm_p95_aware_correction.py"
  }
}
```