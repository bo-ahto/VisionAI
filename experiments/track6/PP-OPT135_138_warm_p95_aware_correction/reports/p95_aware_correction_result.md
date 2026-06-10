# PP-OPT135~138 Warm p95-aware correction 결과

- 작성일: 2026-06-09 16:15
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 목적: PP127 low-MAPE 보정의 p95 악화를 막으면서 MAPE 개선 유지
- 결론: 운영 후보 fixed test MAPE 0.270114, p95 0.807490. PP126 대비 MAPE +0.000000, p95 +0.000000.
- 해석: PP127의 큰 MAPE 개선은 p95 tail row에서 과한 이동을 만든다. 이번 배치는 해당 tail-harm 확률을 직접 학습해 hard guard와 row별 budget으로 보정 강도를 줄였다.

## 주요 후보 test 비교
| candidate | family | item_id | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| reference_pp134_operational_recomputed | reference_prior | REFERENCE | 0.136320 | 0.270033 | 0.807490 | 0.397520 | -0.001362 | -0.000640 |
| reference_pp126_operational | reference_prior | REFERENCE | 0.136320 | 0.270114 | 0.807490 | 0.397588 | -0.001280 | -0.000640 |
| ppopt138_operational_p95_aware_correction_challenger__source=reference_pp126_operational | p95_aware_operational_selection | PP-OPT138 | 0.136320 | 0.270114 | 0.807490 | 0.397588 | -0.001280 | -0.000640 |
| reference_pp134_p95_recomputed | reference_prior | REFERENCE | 0.136320 | 0.270242 | 0.807488 | 0.397692 | -0.001153 | -0.000641 |
| reference_pp126_p95 | reference_prior | REFERENCE | 0.137871 | 0.270317 | 0.807465 | 0.397768 | -0.001078 | -0.000665 |
| ppopt138_p95_p95_aware_correction_challenger__source=reference_pp126_p95 | p95_aware_p95_selection | PP-OPT138 | 0.137871 | 0.270317 | 0.807465 | 0.397768 | -0.001078 | -0.000665 |
| reference_pp64_current_best | reference_prior | REFERENCE | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | p95_test_MAPE | p95_test_p95_APE | operational_pass_vs_incumbent | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4 | guarded correction router | 83 | 0.270114 | 0.807490 | 0.270317 | 0.807465 | True | p95_aware_operational_selection | ppopt138_operational_p95_aware_correction_challenger__source=reference_pp126_operational |
| 2 | tail-harm rollback classifier | 243 | 0.269579 | 0.809113 | 0.269513 | 0.809113 | False | tail_harm_rollback_classifier | ppopt136_tail_harm_rollback__thr=0p38__pre=0p7__rollback=1p0__floor=0p08__cap=0p014 |
| 1 | p95-aware hard guard on learned stack gain | 648 | 0.269972 | 0.809212 | 0.270125 | 0.809092 | False | p95_aware_hard_guard | ppopt135_hard_guard__target=stack_plain__tpen=0p55__hpen=0p55__thr=0p42__hard=0p56__cap=0p014__s=0p6 |
| 3 | row-level correction budget | 81 | 0.269616 | 0.809213 | 0.269627 | 0.809077 | False | row_level_correction_budget | ppopt137_row_budget__cap=0p018__rshrink=0p45__tshrink=0p95__s=0p45 |

## 탐색 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt138_operational_p95_aware_correction_challenger__source=reference_pp126_operational | PP-OPT138 | p95_aware_operational_selection | 0.270114 | 0.807490 | -0.001280 | -0.000640 | 0.987500 | 0.604167 | -0.002076 |
| ppopt138_guarded_router__stack=0p55__rollback=0p65__p95=0p06__cap=0p012 | PP-OPT138 | guarded_correction_router | 0.269716 | 0.808971 | -0.001679 | 0.000841 | 0.991667 | 0.558333 | -0.001860 |
| ppopt138_guarded_router__stack=0p55__rollback=0p65__p95=0p12__cap=0p012 | PP-OPT138 | guarded_correction_router | 0.269717 | 0.808971 | -0.001678 | 0.000841 | 0.991667 | 0.558333 | -0.001860 |
| ppopt138_guarded_router__stack=0p55__rollback=0p65__p95=0p2__cap=0p012 | PP-OPT138 | guarded_correction_router | 0.269718 | 0.808971 | -0.001677 | 0.000841 | 0.991667 | 0.558333 | -0.001860 |
| ppopt138_guarded_router__stack=0p55__rollback=0p5__p95=0p06__cap=0p012 | PP-OPT138 | guarded_correction_router | 0.269728 | 0.808971 | -0.001666 | 0.000841 | 0.991667 | 0.558333 | -0.001855 |
| ppopt138_guarded_router__stack=0p55__rollback=0p5__p95=0p12__cap=0p012 | PP-OPT138 | guarded_correction_router | 0.269729 | 0.808971 | -0.001666 | 0.000841 | 0.991667 | 0.558333 | -0.001855 |
| ppopt138_guarded_router__stack=0p55__rollback=0p5__p95=0p2__cap=0p012 | PP-OPT138 | guarded_correction_router | 0.269730 | 0.808971 | -0.001665 | 0.000841 | 0.991667 | 0.558333 | -0.001855 |
| ppopt138_guarded_router__stack=0p55__rollback=0p35__p95=0p06__cap=0p012 | PP-OPT138 | guarded_correction_router | 0.269741 | 0.808971 | -0.001654 | 0.000841 | 0.991667 | 0.558333 | -0.001850 |
| ppopt138_guarded_router__stack=0p55__rollback=0p35__p95=0p12__cap=0p012 | PP-OPT138 | guarded_correction_router | 0.269741 | 0.808971 | -0.001654 | 0.000841 | 0.991667 | 0.558333 | -0.001850 |
| ppopt138_guarded_router__stack=0p55__rollback=0p35__p95=0p2__cap=0p012 | PP-OPT138 | guarded_correction_router | 0.269742 | 0.808971 | -0.001653 | 0.000841 | 0.991667 | 0.558333 | -0.001850 |
| ppopt136_tail_harm_rollback__thr=0p38__pre=0p7__rollback=1p0__floor=0p08__cap=0p014 | PP-OPT136 | tail_harm_rollback_classifier | 0.269579 | 0.809113 | -0.001816 | 0.000983 | 0.991667 | 0.570833 | -0.001784 |
| ppopt136_tail_harm_rollback__thr=0p38__pre=0p7__rollback=1p0__floor=0p0__cap=0p014 | PP-OPT136 | tail_harm_rollback_classifier | 0.269579 | 0.809113 | -0.001816 | 0.000983 | 0.991667 | 0.570833 | -0.001784 |
| ppopt136_tail_harm_rollback__thr=0p38__pre=0p7__rollback=1p0__floor=0p16__cap=0p014 | PP-OPT136 | tail_harm_rollback_classifier | 0.269579 | 0.809113 | -0.001816 | 0.000983 | 0.991667 | 0.570833 | -0.001784 |
| ppopt136_tail_harm_rollback__thr=0p38__pre=0p55__rollback=0p7__floor=0p08__cap=0p014 | PP-OPT136 | tail_harm_rollback_classifier | 0.269586 | 0.809113 | -0.001809 | 0.000983 | 0.991667 | 0.541667 | -0.001757 |
| ppopt136_tail_harm_rollback__thr=0p38__pre=0p55__rollback=0p7__floor=0p0__cap=0p014 | PP-OPT136 | tail_harm_rollback_classifier | 0.269586 | 0.809113 | -0.001809 | 0.000983 | 0.991667 | 0.541667 | -0.001757 |
| ppopt136_tail_harm_rollback__thr=0p38__pre=0p55__rollback=0p7__floor=0p16__cap=0p014 | PP-OPT136 | tail_harm_rollback_classifier | 0.269586 | 0.809113 | -0.001809 | 0.000983 | 0.991667 | 0.541667 | -0.001757 |
| ppopt136_tail_harm_rollback__thr=0p38__pre=0p55__rollback=0p85__floor=0p08__cap=0p014 | PP-OPT136 | tail_harm_rollback_classifier | 0.269591 | 0.809113 | -0.001804 | 0.000983 | 0.991667 | 0.541667 | -0.001753 |
| ppopt136_tail_harm_rollback__thr=0p38__pre=0p55__rollback=0p85__floor=0p0__cap=0p014 | PP-OPT136 | tail_harm_rollback_classifier | 0.269591 | 0.809113 | -0.001804 | 0.000983 | 0.991667 | 0.541667 | -0.001753 |
| ppopt136_tail_harm_rollback__thr=0p38__pre=0p55__rollback=0p85__floor=0p16__cap=0p014 | PP-OPT136 | tail_harm_rollback_classifier | 0.269591 | 0.809113 | -0.001804 | 0.000983 | 0.991667 | 0.541667 | -0.001753 |
| ppopt136_tail_harm_rollback__thr=0p38__pre=0p55__rollback=1p0__floor=0p08__cap=0p014 | PP-OPT136 | tail_harm_rollback_classifier | 0.269597 | 0.809113 | -0.001797 | 0.000983 | 0.991667 | 0.541667 | -0.001749 |
| ppopt136_tail_harm_rollback__thr=0p38__pre=0p55__rollback=1p0__floor=0p0__cap=0p014 | PP-OPT136 | tail_harm_rollback_classifier | 0.269597 | 0.809113 | -0.001797 | 0.000983 | 0.991667 | 0.541667 | -0.001749 |
| ppopt136_tail_harm_rollback__thr=0p38__pre=0p55__rollback=1p0__floor=0p16__cap=0p014 | PP-OPT136 | tail_harm_rollback_classifier | 0.269597 | 0.809113 | -0.001797 | 0.000983 | 0.991667 | 0.541667 | -0.001749 |
| ppopt136_tail_harm_rollback__thr=0p38__pre=0p7__rollback=0p85__floor=0p08__cap=0p014 | PP-OPT136 | tail_harm_rollback_classifier | 0.269574 | 0.809113 | -0.001821 | 0.000983 | 0.991667 | 0.570833 | -0.001735 |
| ppopt136_tail_harm_rollback__thr=0p38__pre=0p7__rollback=0p85__floor=0p0__cap=0p014 | PP-OPT136 | tail_harm_rollback_classifier | 0.269574 | 0.809113 | -0.001821 | 0.000983 | 0.991667 | 0.570833 | -0.001735 |
| ppopt136_tail_harm_rollback__thr=0p38__pre=0p7__rollback=0p85__floor=0p16__cap=0p014 | PP-OPT136 | tail_harm_rollback_classifier | 0.269574 | 0.809113 | -0.001821 | 0.000983 | 0.991667 | 0.570833 | -0.001735 |
| ppopt135_hard_guard__target=stack_plain__tpen=0p55__hpen=0p55__thr=0p42__hard=0p56__cap=0p014__s=0p6 | PP-OPT135 | p95_aware_hard_guard | 0.269972 | 0.809212 | -0.001423 | 0.001082 | 0.995833 | 0.525000 | -0.001708 |
| ppopt135_hard_guard__target=stack_plain__tpen=0p55__hpen=0p55__thr=0p42__hard=0p66__cap=0p014__s=0p6 | PP-OPT135 | p95_aware_hard_guard | 0.269972 | 0.809212 | -0.001423 | 0.001082 | 0.995833 | 0.525000 | -0.001708 |
| ppopt135_hard_guard__target=stack_plain__tpen=0p55__hpen=0p55__thr=0p42__hard=0p46__cap=0p014__s=0p6 | PP-OPT135 | p95_aware_hard_guard | 0.269972 | 0.809212 | -0.001423 | 0.001082 | 0.995833 | 0.525000 | -0.001708 |
| ppopt135_hard_guard__target=stack_plain__tpen=0p55__hpen=0p55__thr=0p42__hard=0p56__cap=0p014__s=0p75 | PP-OPT135 | p95_aware_hard_guard | 0.269958 | 0.809212 | -0.001437 | 0.001082 | 0.991667 | 0.520833 | -0.001708 |
| ppopt135_hard_guard__target=stack_plain__tpen=0p55__hpen=0p55__thr=0p42__hard=0p66__cap=0p014__s=0p75 | PP-OPT135 | p95_aware_hard_guard | 0.269958 | 0.809212 | -0.001437 | 0.001082 | 0.991667 | 0.520833 | -0.001708 |
| ppopt135_hard_guard__target=stack_plain__tpen=0p55__hpen=0p55__thr=0p42__hard=0p46__cap=0p014__s=0p75 | PP-OPT135 | p95_aware_hard_guard | 0.269958 | 0.809212 | -0.001437 | 0.001082 | 0.991667 | 0.520833 | -0.001708 |
| ppopt135_hard_guard__target=stack_weighted__tpen=0p55__hpen=0p75__thr=0p42__hard=0p46__cap=0p014__s=0p6 | PP-OPT135 | p95_aware_hard_guard | 0.270190 | 0.809207 | -0.001204 | 0.001077 | 0.995833 | 0.512500 | -0.001702 |
| ppopt135_hard_guard__target=stack_weighted__tpen=0p55__hpen=0p75__thr=0p42__hard=0p56__cap=0p014__s=0p6 | PP-OPT135 | p95_aware_hard_guard | 0.270190 | 0.809207 | -0.001204 | 0.001077 | 0.995833 | 0.512500 | -0.001702 |
| ppopt135_hard_guard__target=stack_weighted__tpen=0p55__hpen=0p75__thr=0p42__hard=0p66__cap=0p014__s=0p6 | PP-OPT135 | p95_aware_hard_guard | 0.270190 | 0.809207 | -0.001204 | 0.001077 | 0.995833 | 0.512500 | -0.001702 |
| ppopt135_hard_guard__target=stack_plain__tpen=0p55__hpen=0p75__thr=0p36__hard=0p56__cap=0p014__s=0p6 | PP-OPT135 | p95_aware_hard_guard | 0.269787 | 0.809212 | -0.001608 | 0.001082 | 0.991667 | 0.537500 | -0.001700 |
| ppopt135_hard_guard__target=stack_plain__tpen=0p55__hpen=0p75__thr=0p36__hard=0p66__cap=0p014__s=0p6 | PP-OPT135 | p95_aware_hard_guard | 0.269787 | 0.809212 | -0.001608 | 0.001082 | 0.991667 | 0.537500 | -0.001700 |
| ppopt135_hard_guard__target=stack_plain__tpen=0p55__hpen=0p75__thr=0p36__hard=0p46__cap=0p014__s=0p6 | PP-OPT135 | p95_aware_hard_guard | 0.269787 | 0.809212 | -0.001608 | 0.001082 | 0.991667 | 0.537500 | -0.001700 |
| ppopt135_hard_guard__target=stack_plain__tpen=0p75__hpen=0p55__thr=0p36__hard=0p56__cap=0p014__s=0p75 | PP-OPT135 | p95_aware_hard_guard | 0.269852 | 0.809212 | -0.001543 | 0.001082 | 0.991667 | 0.562500 | -0.001693 |
| ppopt135_hard_guard__target=stack_plain__tpen=0p75__hpen=0p55__thr=0p36__hard=0p66__cap=0p014__s=0p75 | PP-OPT135 | p95_aware_hard_guard | 0.269852 | 0.809212 | -0.001543 | 0.001082 | 0.991667 | 0.562500 | -0.001693 |
| ppopt135_hard_guard__target=stack_plain__tpen=0p75__hpen=0p55__thr=0p36__hard=0p46__cap=0p014__s=0p75 | PP-OPT135 | p95_aware_hard_guard | 0.269853 | 0.809212 | -0.001542 | 0.001082 | 0.991667 | 0.562500 | -0.001693 |
| ppopt135_hard_guard__target=stack_plain__tpen=0p75__hpen=0p55__thr=0p36__hard=0p56__cap=0p014__s=0p6 | PP-OPT135 | p95_aware_hard_guard | 0.269888 | 0.809212 | -0.001507 | 0.001082 | 0.991667 | 0.550000 | -0.001691 |
| ppopt135_hard_guard__target=stack_plain__tpen=0p75__hpen=0p55__thr=0p36__hard=0p66__cap=0p014__s=0p6 | PP-OPT135 | p95_aware_hard_guard | 0.269888 | 0.809212 | -0.001507 | 0.001082 | 0.991667 | 0.550000 | -0.001691 |
| ppopt135_hard_guard__target=stack_plain__tpen=0p75__hpen=0p55__thr=0p36__hard=0p46__cap=0p014__s=0p6 | PP-OPT135 | p95_aware_hard_guard | 0.269889 | 0.809212 | -0.001506 | 0.001082 | 0.991667 | 0.550000 | -0.001691 |
| ppopt135_hard_guard__target=stack_weighted__tpen=0p55__hpen=0p75__thr=0p42__hard=0p46__cap=0p014__s=0p45 | PP-OPT135 | p95_aware_hard_guard | 0.270157 | 0.809207 | -0.001237 | 0.001077 | 0.995833 | 0.537500 | -0.001681 |
| ppopt135_hard_guard__target=stack_weighted__tpen=0p55__hpen=0p75__thr=0p42__hard=0p56__cap=0p014__s=0p45 | PP-OPT135 | p95_aware_hard_guard | 0.270157 | 0.809207 | -0.001237 | 0.001077 | 0.995833 | 0.537500 | -0.001681 |
| ppopt135_hard_guard__target=stack_weighted__tpen=0p55__hpen=0p75__thr=0p42__hard=0p66__cap=0p014__s=0p45 | PP-OPT135 | p95_aware_hard_guard | 0.270157 | 0.809207 | -0.001237 | 0.001077 | 0.995833 | 0.537500 | -0.001681 |
| ppopt136_tail_harm_rollback__thr=0p38__pre=0p7__rollback=0p7__floor=0p08__cap=0p014 | PP-OPT136 | tail_harm_rollback_classifier | 0.269568 | 0.809113 | -0.001827 | 0.000983 | 0.991667 | 0.570833 | -0.001672 |
| ppopt136_tail_harm_rollback__thr=0p38__pre=0p7__rollback=0p7__floor=0p0__cap=0p014 | PP-OPT136 | tail_harm_rollback_classifier | 0.269568 | 0.809113 | -0.001827 | 0.000983 | 0.991667 | 0.570833 | -0.001672 |
| ppopt136_tail_harm_rollback__thr=0p38__pre=0p7__rollback=0p7__floor=0p16__cap=0p014 | PP-OPT136 | tail_harm_rollback_classifier | 0.269568 | 0.809113 | -0.001827 | 0.000983 | 0.991667 | 0.570833 | -0.001672 |
| ppopt135_hard_guard__target=stack_weighted__tpen=0p55__hpen=0p55__thr=0p42__hard=0p46__cap=0p014__s=0p6 | PP-OPT135 | p95_aware_hard_guard | 0.270145 | 0.809207 | -0.001250 | 0.001077 | 0.995833 | 0.504167 | -0.001653 |
| ppopt135_hard_guard__target=stack_weighted__tpen=0p55__hpen=0p55__thr=0p42__hard=0p56__cap=0p014__s=0p6 | PP-OPT135 | p95_aware_hard_guard | 0.270145 | 0.809207 | -0.001250 | 0.001077 | 0.995833 | 0.504167 | -0.001653 |
| ppopt135_hard_guard__target=stack_weighted__tpen=0p55__hpen=0p55__thr=0p42__hard=0p66__cap=0p014__s=0p6 | PP-OPT135 | p95_aware_hard_guard | 0.270145 | 0.809207 | -0.001250 | 0.001077 | 0.995833 | 0.504167 | -0.001653 |
| ppopt138_p95_p95_aware_correction_challenger__source=reference_pp126_p95 | PP-OPT138 | p95_aware_p95_selection | 0.270317 | 0.807465 | -0.001078 | -0.000665 | 1.000000 | 0.591667 | -0.001653 |
| ppopt135_hard_guard__target=stack_plain__tpen=0p55__hpen=0p55__thr=0p36__hard=0p56__cap=0p014__s=0p45 | PP-OPT135 | p95_aware_hard_guard | 0.269726 | 0.809212 | -0.001669 | 0.001082 | 0.991667 | 0.537500 | -0.001651 |
| ppopt135_hard_guard__target=stack_plain__tpen=0p55__hpen=0p55__thr=0p36__hard=0p66__cap=0p014__s=0p45 | PP-OPT135 | p95_aware_hard_guard | 0.269726 | 0.809212 | -0.001669 | 0.001082 | 0.991667 | 0.537500 | -0.001651 |
| ppopt135_hard_guard__target=stack_plain__tpen=0p55__hpen=0p55__thr=0p36__hard=0p46__cap=0p014__s=0p45 | PP-OPT135 | p95_aware_hard_guard | 0.269728 | 0.809212 | -0.001667 | 0.001082 | 0.991667 | 0.537500 | -0.001651 |
| ppopt135_hard_guard__target=stack_weighted__tpen=0p55__hpen=0p55__thr=0p42__hard=0p46__cap=0p014__s=0p45 | PP-OPT135 | p95_aware_hard_guard | 0.270125 | 0.809207 | -0.001270 | 0.001077 | 0.995833 | 0.537500 | -0.001649 |
| ppopt135_hard_guard__target=stack_weighted__tpen=0p55__hpen=0p55__thr=0p42__hard=0p56__cap=0p014__s=0p45 | PP-OPT135 | p95_aware_hard_guard | 0.270125 | 0.809207 | -0.001270 | 0.001077 | 0.995833 | 0.537500 | -0.001649 |
| ppopt135_hard_guard__target=stack_weighted__tpen=0p55__hpen=0p55__thr=0p42__hard=0p66__cap=0p014__s=0p45 | PP-OPT135 | p95_aware_hard_guard | 0.270125 | 0.809207 | -0.001270 | 0.001077 | 0.995833 | 0.537500 | -0.001649 |
| ppopt135_hard_guard__target=stack_plain__tpen=0p55__hpen=0p75__thr=0p36__hard=0p56__cap=0p014__s=0p45 | PP-OPT135 | p95_aware_hard_guard | 0.269822 | 0.809212 | -0.001572 | 0.001082 | 0.991667 | 0.525000 | -0.001641 |

## 선택 후보 반복 안정성
| candidate_label | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_vs_pp64_MAPE | fixed_test_delta_vs_pp64_p95_APE | avg_delta_vs_pp64_MAPE | avg_delta_vs_pp64_p95_APE | avg_pp64_MAPE_win_rate | avg_pp64_p95_win_rate | replacement_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| candidate_ppopt136_tail_harm_rollback__thr_0p38__pre_0p85__rollback_0p7__floor_0p08__cap_0p014__ebd8ff4866 | 0.269545 | 0.809113 | -0.001019 | 0.001614 | -0.000931 | -0.002198 | 0.950000 | 0.438462 | -0.017889 |
| candidate_ppopt136_tail_harm_rollback__thr_0p38__pre_0p85__rollback_0p7__floor_0p0__cap_0p014__569df023d5 | 0.269545 | 0.809113 | -0.001019 | 0.001614 | -0.000931 | -0.002198 | 0.950000 | 0.438462 | -0.017889 |
| candidate_ppopt136_tail_harm_rollback__thr_0p38__pre_0p85__rollback_0p7__floor_0p16__cap_0p014__b2a9b0b38a | 0.269545 | 0.809113 | -0.001019 | 0.001614 | -0.000931 | -0.002198 | 0.950000 | 0.438462 | -0.017889 |
| candidate_ppopt136_tail_harm_rollback__thr_0p38__pre_0p85__rollback_0p85__floor_0p08__cap_0p014__2b72698faa | 0.269551 | 0.809113 | -0.001013 | 0.001614 | -0.000924 | -0.002182 | 0.948718 | 0.438462 | -0.017832 |
| candidate_ppopt136_tail_harm_rollback__thr_0p38__pre_0p85__rollback_0p85__floor_0p0__cap_0p014__a1a5f15ed0 | 0.269551 | 0.809113 | -0.001013 | 0.001614 | -0.000924 | -0.002182 | 0.948718 | 0.438462 | -0.017832 |
| candidate_ppopt136_tail_harm_rollback__thr_0p38__pre_0p85__rollback_0p85__floor_0p16__cap_0p014__13438b35ce | 0.269551 | 0.809113 | -0.001013 | 0.001614 | -0.000924 | -0.002182 | 0.948718 | 0.438462 | -0.017832 |
| candidate_ppopt136_tail_harm_rollback__thr_0p38__pre_0p85__rollback_1p0__floor_0p08__cap_0p014__4a2b0539f0 | 0.269557 | 0.809113 | -0.001007 | 0.001614 | -0.000917 | -0.002166 | 0.947436 | 0.438462 | -0.017774 |
| candidate_ppopt136_tail_harm_rollback__thr_0p38__pre_0p85__rollback_1p0__floor_0p0__cap_0p014__e0dcdc0834 | 0.269557 | 0.809113 | -0.001007 | 0.001614 | -0.000917 | -0.002166 | 0.947436 | 0.438462 | -0.017774 |
| candidate_ppopt136_tail_harm_rollback__thr_0p38__pre_0p85__rollback_1p0__floor_0p16__cap_0p014__cea3e936c6 | 0.269557 | 0.809113 | -0.001007 | 0.001614 | -0.000917 | -0.002166 | 0.947436 | 0.438462 | -0.017774 |
| candidate_ppopt136_tail_harm_rollback__thr_0p38__pre_0p7__rollback_0p7__floor_0p08__cap_0p014__0c997a2565 | 0.269568 | 0.809113 | -0.000996 | 0.001614 | -0.000895 | -0.002030 | 0.945833 | 0.435577 | -0.017700 |
| candidate_ppopt136_tail_harm_rollback__thr_0p38__pre_0p7__rollback_0p7__floor_0p0__cap_0p014__d30f327f79 | 0.269568 | 0.809113 | -0.000996 | 0.001614 | -0.000895 | -0.002030 | 0.945833 | 0.435577 | -0.017700 |
| candidate_ppopt136_tail_harm_rollback__thr_0p38__pre_0p7__rollback_0p7__floor_0p16__cap_0p014__f29ca8ada4 | 0.269568 | 0.809113 | -0.000996 | 0.001614 | -0.000895 | -0.002030 | 0.945833 | 0.435577 | -0.017700 |
| candidate_ppopt138_guarded_router__stack_0p3__rollback_0p35__p95_0p12__cap_0p026__44e1fad132 | 0.269828 | 0.808775 | -0.000736 | 0.001277 | -0.000733 | -0.001735 | 0.944231 | 0.434936 | -0.017612 |
| candidate_ppopt138_guarded_router__stack_0p3__rollback_0p35__p95_0p06__cap_0p026__19984e6d85 | 0.269827 | 0.808775 | -0.000737 | 0.001277 | -0.000733 | -0.001738 | 0.943910 | 0.434936 | -0.017600 |
| candidate_ppopt138_guarded_router__stack_0p3__rollback_0p5__p95_0p06__cap_0p026__53e569573d | 0.269815 | 0.808775 | -0.000749 | 0.001277 | -0.000742 | -0.001779 | 0.943590 | 0.434615 | -0.017599 |
| candidate_ppopt138_guarded_router__stack_0p3__rollback_0p5__p95_0p12__cap_0p026__2207215fb3 | 0.269816 | 0.808775 | -0.000748 | 0.001277 | -0.000742 | -0.001776 | 0.943590 | 0.434615 | -0.017598 |
| candidate_ppopt138_guarded_router__stack_0p3__rollback_0p5__p95_0p2__cap_0p026__5f1feb4982 | 0.269816 | 0.808775 | -0.000748 | 0.001277 | -0.000741 | -0.001770 | 0.943590 | 0.434615 | -0.017598 |
| candidate_ppopt138_guarded_router__stack_0p3__rollback_0p65__p95_0p06__cap_0p026__bae0747487 | 0.269803 | 0.808775 | -0.000761 | 0.001277 | -0.000751 | -0.001820 | 0.942949 | 0.434615 | -0.017586 |
| candidate_ppopt138_guarded_router__stack_0p3__rollback_0p65__p95_0p12__cap_0p026__c620c0aa56 | 0.269803 | 0.808775 | -0.000761 | 0.001277 | -0.000751 | -0.001816 | 0.942949 | 0.434615 | -0.017585 |
| candidate_ppopt138_guarded_router__stack_0p3__rollback_0p65__p95_0p2__cap_0p026__46e97e0a26 | 0.269804 | 0.808775 | -0.000760 | 0.001277 | -0.000750 | -0.001811 | 0.942949 | 0.434615 | -0.017584 |
| candidate_ppopt138_guarded_router__stack_0p3__rollback_0p35__p95_0p06__cap_0p018__86f95e99bf | 0.269827 | 0.808775 | -0.000737 | 0.001277 | -0.000726 | -0.001738 | 0.942308 | 0.434936 | -0.017536 |
| candidate_ppopt138_guarded_router__stack_0p3__rollback_0p35__p95_0p12__cap_0p018__e666f7b987 | 0.269828 | 0.808775 | -0.000736 | 0.001277 | -0.000725 | -0.001735 | 0.942308 | 0.434936 | -0.017535 |
| candidate_ppopt138_guarded_router__stack_0p3__rollback_0p5__p95_0p06__cap_0p018__1fab54c6fe | 0.269815 | 0.808775 | -0.000749 | 0.001277 | -0.000735 | -0.001779 | 0.941346 | 0.434615 | -0.017509 |
| candidate_ppopt138_guarded_router__stack_0p3__rollback_0p5__p95_0p12__cap_0p018__eb32b220d8 | 0.269816 | 0.808775 | -0.000748 | 0.001277 | -0.000734 | -0.001776 | 0.941346 | 0.434615 | -0.017509 |
| candidate_ppopt138_guarded_router__stack_0p3__rollback_0p65__p95_0p06__cap_0p018__fc67ee147b | 0.269803 | 0.808775 | -0.000761 | 0.001277 | -0.000744 | -0.001820 | 0.941026 | 0.434615 | -0.017509 |
| candidate_ppopt138_guarded_router__stack_0p3__rollback_0p65__p95_0p12__cap_0p018__70b042d477 | 0.269803 | 0.808775 | -0.000761 | 0.001277 | -0.000743 | -0.001816 | 0.941026 | 0.434615 | -0.017508 |
| candidate_ppopt138_guarded_router__stack_0p3__rollback_0p5__p95_0p2__cap_0p018__902fcce4ad | 0.269816 | 0.808775 | -0.000748 | 0.001277 | -0.000734 | -0.001770 | 0.941346 | 0.434615 | -0.017508 |
| candidate_ppopt138_guarded_router__stack_0p3__rollback_0p65__p95_0p2__cap_0p018__4811b6dbf2 | 0.269804 | 0.808775 | -0.000760 | 0.001277 | -0.000743 | -0.001811 | 0.941026 | 0.434615 | -0.017507 |
| candidate_ppopt138_guarded_router__stack_0p3__rollback_0p65__p95_0p06__cap_0p012__267d981158 | 0.269806 | 0.808775 | -0.000758 | 0.001277 | -0.000733 | -0.001789 | 0.939744 | 0.434295 | -0.017454 |
| candidate_ppopt138_guarded_router__stack_0p3__rollback_0p65__p95_0p12__cap_0p012__bc90fe4cee | 0.269807 | 0.808775 | -0.000757 | 0.001277 | -0.000733 | -0.001785 | 0.939744 | 0.434295 | -0.017453 |
| candidate_ppopt138_guarded_router__stack_0p3__rollback_0p65__p95_0p2__cap_0p012__82e436acd6 | 0.269808 | 0.808775 | -0.000757 | 0.001277 | -0.000732 | -0.001780 | 0.939744 | 0.434295 | -0.017453 |
| candidate_ppopt138_guarded_router__stack_0p3__rollback_0p5__p95_0p06__cap_0p012__002b63d4e9 | 0.269818 | 0.808775 | -0.000746 | 0.001277 | -0.000724 | -0.001748 | 0.939744 | 0.434295 | -0.017442 |
| candidate_ppopt138_guarded_router__stack_0p3__rollback_0p5__p95_0p12__cap_0p012__f51880370b | 0.269819 | 0.808775 | -0.000745 | 0.001277 | -0.000723 | -0.001745 | 0.939744 | 0.434295 | -0.017441 |
| candidate_ppopt138_guarded_router__stack_0p3__rollback_0p5__p95_0p2__cap_0p012__ac9a47a763 | 0.269820 | 0.808775 | -0.000744 | 0.001277 | -0.000723 | -0.001740 | 0.939744 | 0.434295 | -0.017441 |
| pp126_operational_reference | 0.270114 | 0.807490 | -0.000450 | -0.000009 | -0.000455 | -0.001725 | 0.919231 | 0.494231 | -0.017219 |
| pp138_operational_p95_aware_correction_challenger | 0.270114 | 0.807490 | -0.000450 | -0.000009 | -0.000455 | -0.001725 | 0.919231 | 0.494231 | -0.017219 |
| pp134_operational_recomputed_reference | 0.270033 | 0.807490 | -0.000531 | -0.000009 | -0.000509 | -0.001995 | 0.909936 | 0.496474 | -0.016928 |
| candidate_ppopt135_hard_guard__target_stack_plain__tpen_0p55__hpen_0p55__thr_0p42__hard_0p56__cap_0p02__b1a9b104b1 | 0.269964 | 0.810096 | -0.000600 | 0.002597 | -0.000728 | -0.000981 | 0.951282 | 0.391667 | -0.016833 |
| candidate_ppopt135_hard_guard__target_stack_plain__tpen_0p55__hpen_0p55__thr_0p42__hard_0p66__cap_0p02__be99d539a1 | 0.269964 | 0.810096 | -0.000600 | 0.002597 | -0.000728 | -0.000981 | 0.951282 | 0.391667 | -0.016833 |
| candidate_ppopt135_hard_guard__target_stack_plain__tpen_0p55__hpen_0p55__thr_0p42__hard_0p46__cap_0p02__cc4bf9cbef | 0.269964 | 0.810096 | -0.000600 | 0.002597 | -0.000728 | -0.000981 | 0.951282 | 0.391667 | -0.016833 |
| pp118_operational_reference | 0.270139 | 0.807490 | -0.000425 | -0.000009 | -0.000389 | -0.001654 | 0.909295 | 0.494551 | -0.016797 |
| candidate_ppopt135_hard_guard__target_stack_plain__tpen_0p55__hpen_0p55__thr_0p42__hard_0p56__cap_0p02__d9e29a66a3 | 0.269957 | 0.810186 | -0.000607 | 0.002687 | -0.000746 | -0.000455 | 0.948077 | 0.390064 | -0.016649 |
| candidate_ppopt135_hard_guard__target_stack_plain__tpen_0p55__hpen_0p55__thr_0p42__hard_0p66__cap_0p02__54dc14020e | 0.269957 | 0.810186 | -0.000607 | 0.002687 | -0.000746 | -0.000455 | 0.948077 | 0.390064 | -0.016649 |
| candidate_ppopt135_hard_guard__target_stack_plain__tpen_0p55__hpen_0p55__thr_0p42__hard_0p46__cap_0p02__1d248846a3 | 0.269957 | 0.810186 | -0.000607 | 0.002687 | -0.000746 | -0.000455 | 0.948077 | 0.390064 | -0.016649 |
| pp126_p95_reference | 0.270317 | 0.807465 | -0.000247 | -0.000034 | -0.000239 | -0.000998 | 0.909936 | 0.665705 | -0.016645 |
| pp138_p95_p95_aware_correction_challenger | 0.270317 | 0.807465 | -0.000247 | -0.000034 | -0.000239 | -0.000998 | 0.909936 | 0.665705 | -0.016645 |
| pp134_p95_recomputed_reference | 0.270242 | 0.807488 | -0.000322 | -0.000010 | -0.000335 | -0.001402 | 0.907051 | 0.492628 | -0.016604 |
| candidate_ppopt135_hard_guard__target_stack_weighted__tpen_0p55__hpen_0p75__thr_0p42__hard_0p46__cap_0__1996df63a7 | 0.270188 | 0.810178 | -0.000376 | 0.002679 | -0.000598 | -0.000308 | 0.947115 | 0.327885 | -0.016385 |
| candidate_ppopt135_hard_guard__target_stack_weighted__tpen_0p55__hpen_0p75__thr_0p42__hard_0p56__cap_0__56623af50c | 0.270188 | 0.810178 | -0.000376 | 0.002679 | -0.000598 | -0.000308 | 0.947115 | 0.327885 | -0.016385 |
| candidate_ppopt135_hard_guard__target_stack_weighted__tpen_0p55__hpen_0p75__thr_0p42__hard_0p66__cap_0__227f5c3391 | 0.270188 | 0.810178 | -0.000376 | 0.002679 | -0.000598 | -0.000308 | 0.947115 | 0.327885 | -0.016385 |
| candidate_ppopt135_hard_guard__target_stack_plain__tpen_0p55__hpen_0p55__thr_0p42__hard_0p56__cap_0p03__6907b69888 | 0.269951 | 0.810739 | -0.000614 | 0.003240 | -0.000763 | -0.000349 | 0.949038 | 0.390064 | -0.016307 |
| candidate_ppopt135_hard_guard__target_stack_plain__tpen_0p55__hpen_0p55__thr_0p42__hard_0p66__cap_0p03__c5ad669f1d | 0.269951 | 0.810739 | -0.000614 | 0.003240 | -0.000763 | -0.000349 | 0.949038 | 0.390064 | -0.016307 |
| candidate_ppopt135_hard_guard__target_stack_plain__tpen_0p55__hpen_0p55__thr_0p42__hard_0p46__cap_0p03__3e89b2cee0 | 0.269951 | 0.810739 | -0.000613 | 0.003240 | -0.000763 | -0.000349 | 0.949038 | 0.390064 | -0.016307 |
| pp81_stable_reference | 0.270559 | 0.807490 | -0.000005 | -0.000009 | -0.000004 | -0.000014 | 0.890705 | 0.410256 | -0.015633 |
| pp95_operational_reference | 0.270559 | 0.807490 | -0.000005 | -0.000009 | -0.000004 | -0.000014 | 0.890705 | 0.410256 | -0.015633 |
| pp70_refinement_candidate | 0.270561 | 0.807490 | -0.000003 | -0.000009 | -0.000001 | -0.000001 | 0.786859 | 0.398077 | -0.011477 |
| pp119_guarded_mape_reference | 0.269759 | 0.807513 | -0.000805 | 0.000014 | 0.000727 | 0.003451 | 0.502244 | 0.208974 | 0.000686 |
| pp119_aggressive_mape_reference | 0.269384 | 0.812525 | -0.001180 | 0.005026 | -0.000456 | -0.003399 | 0.537500 | 0.444231 | 0.000838 |
| pp82_p95_reference | 0.270651 | 0.806840 | 0.000087 | -0.000659 | 0.000082 | 0.000179 | 0.056090 | 0.603846 | 0.017948 |
| pp64_current_best | 0.270564 | 0.807499 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.020000 |
| incumbent_pp7 | 0.271395 | 0.808130 | 0.000831 | 0.000631 | 0.000748 | 0.001946 | 0.002244 | 0.450641 | 0.022238 |
| hcoef_stable_source | 0.272989 | 0.806366 | 0.002425 | -0.001133 | 0.002013 | 0.005297 | 0.002244 | 0.403526 | 0.025195 |

## 선택 후보 시나리오별 안정성
| candidate_label | eval_split | scenario | mean_delta_vs_pp64_MAPE | mean_delta_vs_pp64_p95_APE | pp64_MAPE_win_rate | pp64_p95_win_rate | pp64_all3_win_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pp126_operational_reference | test | artist_group_holdout | -0.000463 | 0.000003 | 1.000000 | 0.315385 | 0.265385 |
| pp126_operational_reference | test | confidence_stratified_rows | -0.000430 | 0.000022 | 1.000000 | 0.430769 | 0.342308 |
| pp126_operational_reference | test | full_split | -0.000450 | -0.000009 | 1.000000 | 1.000000 | 1.000000 |
| pp126_operational_reference | test | price_band_stratified_rows | -0.000432 | -0.000003 | 1.000000 | 0.376923 | 0.307692 |
| pp126_operational_reference | test | risk_focus_bootstrap | -0.001084 | -0.008342 | 0.992308 | 0.346154 | 0.030769 |
| pp126_operational_reference | test | row_bootstrap | -0.000462 | -0.000112 | 0.996154 | 0.315385 | 0.196154 |
| pp126_operational_reference | validation_oof | artist_group_holdout | -0.000371 | -0.003836 | 0.896154 | 0.576923 | 0.384615 |
| pp126_operational_reference | validation_oof | confidence_stratified_rows | -0.000384 | -0.002605 | 0.915385 | 0.526923 | 0.365385 |
| pp126_operational_reference | validation_oof | full_split | -0.000383 | -0.000025 | 1.000000 | 1.000000 | 0.000000 |
| pp126_operational_reference | validation_oof | price_band_stratified_rows | -0.000386 | -0.002142 | 0.911538 | 0.488462 | 0.292308 |
| pp126_operational_reference | validation_oof | risk_focus_bootstrap | -0.000227 | -0.001270 | 0.565385 | 0.138462 | 0.073077 |
| pp126_operational_reference | validation_oof | row_bootstrap | -0.000384 | -0.002389 | 0.753846 | 0.415385 | 0.219231 |
| pp134_operational_recomputed_reference | test | artist_group_holdout | -0.000547 | 0.000013 | 1.000000 | 0.315385 | 0.292308 |
| pp134_operational_recomputed_reference | test | confidence_stratified_rows | -0.000507 | 0.000032 | 1.000000 | 0.430769 | 0.361538 |
| pp134_operational_recomputed_reference | test | full_split | -0.000531 | -0.000009 | 1.000000 | 1.000000 | 1.000000 |
| pp134_operational_recomputed_reference | test | price_band_stratified_rows | -0.000510 | -0.000003 | 1.000000 | 0.376923 | 0.334615 |
| pp134_operational_recomputed_reference | test | risk_focus_bootstrap | -0.001282 | -0.010033 | 0.992308 | 0.346154 | 0.026923 |
| pp134_operational_recomputed_reference | test | row_bootstrap | -0.000546 | -0.000131 | 0.996154 | 0.315385 | 0.242308 |
| pp134_operational_recomputed_reference | validation_oof | artist_group_holdout | -0.000373 | -0.004296 | 0.857692 | 0.596154 | 0.350000 |
| pp134_operational_recomputed_reference | validation_oof | confidence_stratified_rows | -0.000391 | -0.002885 | 0.888462 | 0.526923 | 0.330769 |
| pp134_operational_recomputed_reference | validation_oof | full_split | -0.000387 | -0.000025 | 1.000000 | 1.000000 | 0.000000 |
| pp134_operational_recomputed_reference | validation_oof | price_band_stratified_rows | -0.000391 | -0.002430 | 0.876923 | 0.492308 | 0.265385 |
| pp134_operational_recomputed_reference | validation_oof | risk_focus_bootstrap | -0.000251 | -0.001500 | 0.565385 | 0.138462 | 0.069231 |
| pp134_operational_recomputed_reference | validation_oof | row_bootstrap | -0.000393 | -0.002678 | 0.742308 | 0.419231 | 0.215385 |
| pp138_operational_p95_aware_correction_challenger | test | artist_group_holdout | -0.000463 | 0.000003 | 1.000000 | 0.315385 | 0.265385 |
| pp138_operational_p95_aware_correction_challenger | test | confidence_stratified_rows | -0.000430 | 0.000022 | 1.000000 | 0.430769 | 0.342308 |
| pp138_operational_p95_aware_correction_challenger | test | full_split | -0.000450 | -0.000009 | 1.000000 | 1.000000 | 1.000000 |
| pp138_operational_p95_aware_correction_challenger | test | price_band_stratified_rows | -0.000432 | -0.000003 | 1.000000 | 0.376923 | 0.307692 |
| pp138_operational_p95_aware_correction_challenger | test | risk_focus_bootstrap | -0.001084 | -0.008342 | 0.992308 | 0.346154 | 0.030769 |
| pp138_operational_p95_aware_correction_challenger | test | row_bootstrap | -0.000462 | -0.000112 | 0.996154 | 0.315385 | 0.196154 |
| pp138_operational_p95_aware_correction_challenger | validation_oof | artist_group_holdout | -0.000371 | -0.003836 | 0.896154 | 0.576923 | 0.384615 |
| pp138_operational_p95_aware_correction_challenger | validation_oof | confidence_stratified_rows | -0.000384 | -0.002605 | 0.915385 | 0.526923 | 0.365385 |
| pp138_operational_p95_aware_correction_challenger | validation_oof | full_split | -0.000383 | -0.000025 | 1.000000 | 1.000000 | 0.000000 |
| pp138_operational_p95_aware_correction_challenger | validation_oof | price_band_stratified_rows | -0.000386 | -0.002142 | 0.911538 | 0.488462 | 0.292308 |
| pp138_operational_p95_aware_correction_challenger | validation_oof | risk_focus_bootstrap | -0.000227 | -0.001270 | 0.565385 | 0.138462 | 0.073077 |
| pp138_operational_p95_aware_correction_challenger | validation_oof | row_bootstrap | -0.000384 | -0.002389 | 0.753846 | 0.415385 | 0.219231 |
| pp138_p95_p95_aware_correction_challenger | test | artist_group_holdout | -0.000256 | 0.000085 | 1.000000 | 0.607692 | 0.438462 |
| pp138_p95_p95_aware_correction_challenger | test | confidence_stratified_rows | -0.000238 | 0.000089 | 1.000000 | 0.596154 | 0.346154 |
| pp138_p95_p95_aware_correction_challenger | test | full_split | -0.000247 | -0.000034 | 1.000000 | 1.000000 | 1.000000 |
| pp138_p95_p95_aware_correction_challenger | test | price_band_stratified_rows | -0.000241 | 0.000092 | 1.000000 | 0.553846 | 0.376923 |
| pp138_p95_p95_aware_correction_challenger | test | risk_focus_bootstrap | -0.000615 | -0.004214 | 0.996154 | 0.630769 | 0.238462 |
| pp138_p95_p95_aware_correction_challenger | test | row_bootstrap | -0.000256 | 0.000018 | 0.996154 | 0.473077 | 0.215385 |
| pp138_p95_p95_aware_correction_challenger | validation_oof | artist_group_holdout | -0.000190 | -0.002566 | 0.888462 | 0.738462 | 0.446154 |
| pp138_p95_p95_aware_correction_challenger | validation_oof | confidence_stratified_rows | -0.000197 | -0.001790 | 0.900000 | 0.742308 | 0.534615 |
| pp138_p95_p95_aware_correction_challenger | validation_oof | full_split | -0.000196 | -0.000025 | 1.000000 | 1.000000 | 1.000000 |
| pp138_p95_p95_aware_correction_challenger | validation_oof | price_band_stratified_rows | -0.000195 | -0.001328 | 0.888462 | 0.711538 | 0.461538 |
| pp138_p95_p95_aware_correction_challenger | validation_oof | risk_focus_bootstrap | -0.000033 | -0.000737 | 0.503846 | 0.365385 | 0.157692 |
| pp138_p95_p95_aware_correction_challenger | validation_oof | row_bootstrap | -0.000199 | -0.001571 | 0.746154 | 0.569231 | 0.257692 |

## 실행 설정
```json
{
  "experiment_id": "PP-OPT135-138",
  "experiment_slug": "PP-OPT135_138_warm_p95_aware_correction",
  "created_at": "2026-06-09T16:15:23",
  "seed": 20260609,
  "base_candidate": "hcoef_stable",
  "incumbent_candidate": "incumbent_operational_pp_opt7",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 1070,
  "prediction_rows": 1204820,
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
    "p95_label": "pp126_p95_reference",
    "p95_candidate": "reference_pp126_p95",
    "p95_fixed_test_MAPE": 0.2703165497281949,
    "p95_fixed_test_p95_APE": 0.8074645851983095,
    "p95_delta_vs_pp64_MAPE": -0.0002474921874654479,
    "p95_delta_vs_pp64_p95_APE": -3.4267107800300955e-05,
    "p95_delta_vs_pp126_MAPE": 0.0002021529783430842,
    "p95_delta_vs_pp126_p95_APE": -2.54756995383687e-05,
    "p95_avg_pp64_MAPE_win_rate": 0.9099358974358974,
    "p95_avg_pp64_p95_win_rate": 0.6657051282051282,
    "p95_replacement_score": -0.016644928084901346,
    "operational_protocol_candidate": "ppopt138_operational_p95_aware_correction_challenger__source=reference_pp126_operational",
    "p95_protocol_candidate": "ppopt138_p95_p95_aware_correction_challenger__source=reference_pp126_p95"
  },
  "items": [
    {
      "item_id": "PP-OPT135",
      "priority": "1",
      "title": "p95-aware hard guard on learned stack gain",
      "description": "PP127 low-MAPE stack_plain 보정에 p95 악화 확률 기반 hard guard를 적용한다."
    },
    {
      "item_id": "PP-OPT136",
      "priority": "2",
      "title": "tail-harm rollback classifier",
      "description": "stack_plain이 큰 오차 구간을 악화시킬 row를 별도 분류하고 해당 row의 보정 이동량을 되돌린다."
    },
    {
      "item_id": "PP-OPT137",
      "priority": "3",
      "title": "row-level correction budget",
      "description": "risk, quantile width, 가격대, tail-harm 확률에 따라 row별 최대 보정폭을 다르게 둔다."
    },
    {
      "item_id": "PP-OPT138",
      "priority": "4",
      "title": "guarded correction router",
      "description": "PP126, PP134 harm rollback, p95-aware stack, p95 router를 row별 확률과 cap 안에서 결합한다."
    }
  ],
  "sources": {
    "pp127_config": "experiments/track6/PP-OPT127_134_warm_learned_stack_correction/artifacts/run_config.json",
    "pp127_helper": "scripts/track6/run_pp_opt127_134_warm_learned_stack_correction.py"
  }
}
```