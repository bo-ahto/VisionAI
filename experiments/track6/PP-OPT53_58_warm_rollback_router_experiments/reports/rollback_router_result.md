# PP-OPT53~58 Warm rollback/router 실험 결과

- 작성일: 2026-06-09 12:32
- 데이터 기준: 제출용 제외, Warm validation OOF 519건 + fixed test 607건
- 기준 후보: PP-OPT7 운영 후보
- 비교 후보: PP20, PP23, PP30, PP38, PP45, PP52
- 전체 후보 수: 1511
- 운영 대체 통과 후보 수: 1509

## 최종 선택 후보
- 선택 후보: `ppopt58_rollback_router_challenger__source=ppopt54_classifier_rollback__helper_pp48_mape__thr_0p44__width_0p4__rel_none__s_0p85`
- 원본 후보: `ppopt54_classifier_rollback__helper=pp48_mape__thr=0p44__width=0p4__rel=none__s=0p85`
- 판단: PP58 선택 후보는 PP52 대비 MAPE -0.000027, p95 +0.000151이다.
| eval_split | n | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | 607 | 0.137878 | 0.270572 | 0.807811 | 0.397997 | 0.782537 | 0.883031 | -0.000823 | -0.000319 |
| validation_oof | 519 | 0.122635 | 0.206304 | 0.638224 | 0.323798 | 0.782274 | 0.911368 | -0.000719 | 0.001629 |

## 주요 reference test 비교
| candidate | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- |
| ppopt58_rollback_router_challenger__source=ppopt54_classifier_rollback__helper_pp48_mape__thr_0p44__width_0p4__rel_none__s_0p85 | 0.137878 | 0.270572 | 0.807811 | 0.397997 | -0.000823 | -0.000319 |
| reference_pp52_challenger | 0.137878 | 0.270598 | 0.807660 | 0.397987 | -0.000797 | -0.000470 |
| reference_pp45_challenger | 0.137878 | 0.270682 | 0.807660 | 0.397988 | -0.000713 | -0.000470 |
| reference_pp23 | 0.137878 | 0.270707 | 0.807660 | 0.398002 | -0.000688 | -0.000470 |
| reference_pp48_score | 0.136800 | 0.270816 | 0.807385 | 0.398121 | -0.000579 | -0.000745 |
| reference_pp38_best | 0.137053 | 0.270836 | 0.807102 | 0.398092 | -0.000559 | -0.001028 |
| reference_pp30_best | 0.137546 | 0.270872 | 0.806932 | 0.398014 | -0.000523 | -0.001198 |
| previous_challenger_pp20 | 0.136835 | 0.271182 | 0.806472 | 0.398134 | -0.000213 | -0.001658 |
| incumbent_operational_pp_opt7 | 0.136893 | 0.271395 | 0.808130 | 0.398341 | 0.000000 | 0.000000 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | stable_validation_pass_vs_incumbent | operational_pass_vs_incumbent | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | PP52 악화 확률 classifier rollback | 600 | 0.270652 | 0.807423 | -0.000743 | -0.000707 | 1.000000 | 0.570833 | True | True | classifier_rollback | ppopt54_classifier_rollback__helper=pp48_score__thr=0p08__width=0p4__rel=none__s=0p85 |
| 5 | MAPE 후보와 안정 후보의 row별 router | 192 | 0.270680 | 0.807408 | -0.000715 | -0.000722 | 1.000000 | 0.545833 | True | True | mape_stability_row_router | ppopt57_row_router__safe=pp48_pp30__thr=0p16__sharp=0p75__max=0p9 |
| 1 | PP52 위험도 기반 PP48/PP20 rollback | 240 | 0.270635 | 0.807572 | -0.000760 | -0.000558 | 1.000000 | 0.545833 | True | True | pp52_risk_rollback | ppopt53_risk_rollback__helper=pp48_safe__score=combined__thr=0p18__s=0p7 |
| 4 | segment별 quantile 보정 강도 | 108 | 0.270605 | 0.807587 | -0.000789 | -0.000543 | 1.000000 | 0.504167 | True | True | segment_quantile_strength | ppopt56_segment_strength__center=pp41__high=0p52__lowconf=0p75__cap=0p012 |
| 3 | quantile consensus dynamic cap | 360 | 0.270682 | 0.807587 | -0.000712 | -0.000543 | 1.000000 | 0.504167 | True | True | quantile_dynamic_cap | ppopt55_dynamic_cap__center=pp41__wlim=0p26__cap=0p012_0p008_0p004__guard=medium__s=0p55 |
| 6 | 최종 rollback-router challenger 선택 | 1 | 0.270572 | 0.807811 | -0.000823 | -0.000319 | 1.000000 | 0.508333 | True | True | rollback_router_selection_protocol | ppopt58_rollback_router_challenger__source=ppopt54_classifier_rollback__helper_pp48_mape__thr_0p44__width_0p4__rel_none__s_0p85 |

## 운영 대체 통과 후보 상위
| item_id | candidate | family | test_MdAPE | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | incumbent_all3_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REFERENCE | reference_pp48_score | reference_prior | 0.136800 | 0.270816 | 0.807385 | -0.000579 | -0.000745 | 1.000000 | 0.900000 | 0.779167 | -0.002413 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_score__thr=0p08__width=0p4__rel=none__s=0p85 | classifier_rollback | 0.136790 | 0.270652 | 0.807423 | -0.000743 | -0.000707 | 1.000000 | 0.570833 | 0.487500 | -0.001822 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_mape__thr=0p08__width=0p4__rel=none__s=0p85 | classifier_rollback | 0.137325 | 0.270598 | 0.807969 | -0.000797 | -0.000161 | 1.000000 | 0.616667 | 0.566667 | -0.001782 |
| REFERENCE | reference_pp38_best | reference_prior | 0.137053 | 0.270836 | 0.807102 | -0.000559 | -0.001028 | 1.000000 | 0.541667 | 0.479167 | -0.001713 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_score__thr=0p08__width=0p4__rel=none__s=0p65 | classifier_rollback | 0.137047 | 0.270639 | 0.807479 | -0.000756 | -0.000651 | 1.000000 | 0.508333 | 0.437500 | -0.001655 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_score__thr=0p08__width=0p55__rel=none__s=0p85 | classifier_rollback | 0.137087 | 0.270632 | 0.807404 | -0.000763 | -0.000726 | 1.000000 | 0.508333 | 0.437500 | -0.001648 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_score__thr=0p14__width=0p4__rel=none__s=0p85 | classifier_rollback | 0.137152 | 0.270633 | 0.807411 | -0.000762 | -0.000719 | 1.000000 | 0.508333 | 0.433333 | -0.001637 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_score__thr=0p08__width=0p4__rel=risk_only__s=0p85 | classifier_rollback | 0.137109 | 0.270634 | 0.807494 | -0.000761 | -0.000636 | 1.000000 | 0.508333 | 0.437500 | -0.001632 |
| PP-OPT57 | ppopt57_row_router__safe=pp48_pp30__thr=0p16__sharp=0p75__max=0p9 | mape_stability_row_router | 0.137243 | 0.270680 | 0.807408 | -0.000715 | -0.000722 | 1.000000 | 0.545833 | 0.466667 | -0.001579 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_score__thr=0p08__width=0p55__rel=none__s=0p65 | classifier_rollback | 0.137273 | 0.270624 | 0.807464 | -0.000771 | -0.000666 | 1.000000 | 0.508333 | 0.437500 | -0.001578 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_score__thr=0p08__width=0p7__rel=none__s=0p85 | classifier_rollback | 0.137257 | 0.270616 | 0.807459 | -0.000779 | -0.000671 | 1.000000 | 0.508333 | 0.437500 | -0.001577 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_score__thr=0p14__width=0p4__rel=none__s=0p65 | classifier_rollback | 0.137323 | 0.270624 | 0.807470 | -0.000771 | -0.000660 | 1.000000 | 0.508333 | 0.437500 | -0.001576 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_score__thr=0p14__width=0p55__rel=none__s=0p85 | classifier_rollback | 0.137350 | 0.270614 | 0.807429 | -0.000781 | -0.000701 | 1.000000 | 0.508333 | 0.437500 | -0.001561 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_score__thr=0p08__width=0p55__rel=risk_only__s=0p85 | classifier_rollback | 0.137319 | 0.270620 | 0.807479 | -0.000775 | -0.000651 | 1.000000 | 0.508333 | 0.437500 | -0.001561 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_score__thr=0p14__width=0p4__rel=risk_only__s=0p85 | classifier_rollback | 0.137365 | 0.270621 | 0.807485 | -0.000774 | -0.000645 | 1.000000 | 0.508333 | 0.437500 | -0.001560 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_score__thr=0p08__width=0p4__rel=risk_only__s=0p65 | classifier_rollback | 0.137290 | 0.270625 | 0.807533 | -0.000770 | -0.000597 | 1.000000 | 0.508333 | 0.429167 | -0.001550 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_score__thr=0p08__width=0p4__rel=none__s=0p45 | classifier_rollback | 0.137303 | 0.270626 | 0.807534 | -0.000769 | -0.000596 | 1.000000 | 0.508333 | 0.429167 | -0.001545 |
| PP-OPT57 | ppopt57_row_router__safe=pp48_pp30__thr=0p16__sharp=0p75__max=0p7 | mape_stability_row_router | 0.137385 | 0.270661 | 0.807464 | -0.000734 | -0.000666 | 1.000000 | 0.541667 | 0.462500 | -0.001534 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_mape__thr=0p14__width=0p4__rel=none__s=0p85 | classifier_rollback | 0.137509 | 0.270597 | 0.807971 | -0.000798 | -0.000159 | 1.000000 | 0.500000 | 0.458333 | -0.001522 |
| PP-OPT57 | ppopt57_row_router__safe=pp48_pp20__thr=0p16__sharp=0p75__max=0p9 | mape_stability_row_router | 0.137206 | 0.270736 | 0.807292 | -0.000659 | -0.000838 | 1.000000 | 0.545833 | 0.462500 | -0.001521 |
| PP-OPT53 | ppopt53_risk_rollback__helper=pp48_safe__score=combined__thr=0p18__s=0p7 | pp52_risk_rollback | 0.137517 | 0.270635 | 0.807572 | -0.000760 | -0.000558 | 1.000000 | 0.545833 | 0.462500 | -0.001518 |
| PP-OPT53 | ppopt53_risk_rollback__helper=pp48_score__score=combined__thr=0p18__s=0p7 | pp52_risk_rollback | 0.137517 | 0.270635 | 0.807572 | -0.000760 | -0.000558 | 1.000000 | 0.545833 | 0.462500 | -0.001518 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_mape__thr=0p08__width=0p4__rel=none__s=0p65 | classifier_rollback | 0.137455 | 0.270597 | 0.807897 | -0.000797 | -0.000233 | 1.000000 | 0.500000 | 0.454167 | -0.001517 |
| PP-OPT53 | ppopt53_risk_rollback__helper=pp48_safe__score=risk__thr=0p18__s=0p7 | pp52_risk_rollback | 0.137446 | 0.270670 | 0.807637 | -0.000725 | -0.000493 | 1.000000 | 0.562500 | 0.466667 | -0.001517 |
| PP-OPT53 | ppopt53_risk_rollback__helper=pp48_score__score=risk__thr=0p18__s=0p7 | pp52_risk_rollback | 0.137446 | 0.270670 | 0.807637 | -0.000725 | -0.000493 | 1.000000 | 0.562500 | 0.466667 | -0.001517 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_mape__thr=0p08__width=0p55__rel=none__s=0p85 | classifier_rollback | 0.137476 | 0.270591 | 0.807972 | -0.000804 | -0.000158 | 1.000000 | 0.500000 | 0.454167 | -0.001514 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_score__thr=0p14__width=0p55__rel=none__s=0p65 | classifier_rollback | 0.137474 | 0.270610 | 0.807484 | -0.000785 | -0.000646 | 1.000000 | 0.508333 | 0.437500 | -0.001512 |
| PP-OPT57 | ppopt57_row_router__safe=pp48_pp30__thr=0p16__sharp=1p0__max=0p9 | mape_stability_row_router | 0.137436 | 0.270662 | 0.807439 | -0.000733 | -0.000691 | 1.000000 | 0.541667 | 0.458333 | -0.001512 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_score__thr=0p08__width=0p7__rel=none__s=0p65 | classifier_rollback | 0.137403 | 0.270611 | 0.807506 | -0.000784 | -0.000624 | 1.000000 | 0.508333 | 0.429167 | -0.001507 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_mape__thr=0p08__width=0p4__rel=risk_only__s=0p85 | classifier_rollback | 0.137487 | 0.270596 | 0.807883 | -0.000799 | -0.000247 | 1.000000 | 0.500000 | 0.454167 | -0.001505 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_score__thr=0p08__width=0p55__rel=risk_only__s=0p65 | classifier_rollback | 0.137451 | 0.270615 | 0.807521 | -0.000780 | -0.000608 | 1.000000 | 0.512500 | 0.433333 | -0.001504 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_score__thr=0p08__width=0p7__rel=risk_only__s=0p85 | classifier_rollback | 0.137439 | 0.270609 | 0.807518 | -0.000786 | -0.000612 | 1.000000 | 0.512500 | 0.433333 | -0.001504 |
| PP-OPT57 | ppopt57_row_router__safe=pp48_pp30__thr=0p16__sharp=1p0__max=0p7 | mape_stability_row_router | 0.137534 | 0.270648 | 0.807488 | -0.000747 | -0.000642 | 1.000000 | 0.545833 | 0.466667 | -0.001503 |
| PP-OPT57 | ppopt57_row_router__safe=pp48_pp20__thr=0p16__sharp=0p75__max=0p7 | mape_stability_row_router | 0.137355 | 0.270705 | 0.807374 | -0.000690 | -0.000756 | 1.000000 | 0.545833 | 0.466667 | -0.001503 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_score__thr=0p14__width=0p7__rel=none__s=0p85 | classifier_rollback | 0.137463 | 0.270605 | 0.807479 | -0.000790 | -0.000651 | 1.000000 | 0.508333 | 0.433333 | -0.001501 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_score__thr=0p08__width=0p55__rel=none__s=0p45 | classifier_rollback | 0.137460 | 0.270615 | 0.807524 | -0.000779 | -0.000605 | 1.000000 | 0.508333 | 0.433333 | -0.001501 |
| PP-OPT53 | ppopt53_risk_rollback__helper=pp48_safe__score=risk__thr=0p18__s=0p5 | pp52_risk_rollback | 0.137570 | 0.270650 | 0.807644 | -0.000745 | -0.000486 | 1.000000 | 0.558333 | 0.470833 | -0.001495 |
| PP-OPT53 | ppopt53_risk_rollback__helper=pp48_score__score=risk__thr=0p18__s=0p5 | pp52_risk_rollback | 0.137570 | 0.270650 | 0.807644 | -0.000745 | -0.000486 | 1.000000 | 0.558333 | 0.470833 | -0.001495 |
| PP-OPT56 | ppopt56_segment_strength__center=pp41__high=0p52__lowconf=0p75__cap=0p012 | segment_quantile_strength | 0.137845 | 0.270605 | 0.807587 | -0.000789 | -0.000543 | 1.000000 | 0.504167 | 0.450000 | -0.001494 |
| PP-OPT53 | ppopt53_risk_rollback__helper=pp48_safe__score=combined__thr=0p18__s=0p5 | pp52_risk_rollback | 0.137620 | 0.270624 | 0.807597 | -0.000771 | -0.000533 | 1.000000 | 0.545833 | 0.466667 | -0.001494 |

## 전체 MAPE 상위 후보
| item_id | candidate | family | test_MdAPE | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | incumbent_all3_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_mape__thr=0p44__width=0p4__rel=none__s=0p85 | classifier_rollback | 0.137878 | 0.270572 | 0.807811 | -0.000823 | -0.000319 | 1.000000 | 0.508333 | 0.420833 | -0.001317 |
| PP-OPT58 | ppopt58_rollback_router_challenger__source=ppopt54_classifier_rollback__helper_pp48_mape__thr_0p44__width_0p4__rel_none__s_0p85 | rollback_router_selection_protocol | 0.137878 | 0.270572 | 0.807811 | -0.000823 | -0.000319 | 1.000000 | 0.508333 | 0.420833 | -0.001317 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_mape__thr=0p32__width=0p4__rel=none__s=0p85 | classifier_rollback | 0.137878 | 0.270574 | 0.807904 | -0.000821 | -0.000226 | 1.000000 | 0.504167 | 0.420833 | -0.001334 |
| PP-OPT56 | ppopt56_segment_strength__center=pp45__high=0p52__lowconf=0p75__cap=0p012 | segment_quantile_strength | 0.137878 | 0.270574 | 0.807660 | -0.000820 | -0.000470 | 1.000000 | 0.558333 | 0.420833 | -0.001314 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_score__thr=0p44__width=0p4__rel=none__s=0p85 | classifier_rollback | 0.137878 | 0.270574 | 0.807518 | -0.000820 | -0.000612 | 1.000000 | 0.508333 | 0.408333 | -0.001296 |
| PP-OPT56 | ppopt56_segment_strength__center=pp45__high=0p42__lowconf=0p75__cap=0p012 | segment_quantile_strength | 0.137878 | 0.270575 | 0.807660 | -0.000819 | -0.000470 | 1.000000 | 0.558333 | 0.420833 | -0.001316 |
| PP-OPT56 | ppopt56_segment_strength__center=pp45__high=0p34__lowconf=0p75__cap=0p012 | segment_quantile_strength | 0.137878 | 0.270577 | 0.807660 | -0.000818 | -0.000470 | 1.000000 | 0.558333 | 0.420833 | -0.001318 |
| PP-OPT56 | ppopt56_segment_strength__center=pp45__high=0p52__lowconf=0p55__cap=0p012 | segment_quantile_strength | 0.137878 | 0.270577 | 0.807660 | -0.000818 | -0.000470 | 1.000000 | 0.558333 | 0.420833 | -0.001305 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_mape__thr=0p32__width=0p55__rel=none__s=0p85 | classifier_rollback | 0.137878 | 0.270577 | 0.807837 | -0.000817 | -0.000293 | 1.000000 | 0.504167 | 0.416667 | -0.001317 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_mape__thr=0p44__width=0p4__rel=none__s=0p65 | classifier_rollback | 0.137878 | 0.270578 | 0.807776 | -0.000817 | -0.000354 | 1.000000 | 0.512500 | 0.412500 | -0.001301 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_mape__thr=0p44__width=0p55__rel=none__s=0p85 | classifier_rollback | 0.137878 | 0.270579 | 0.807770 | -0.000816 | -0.000360 | 1.000000 | 0.512500 | 0.412500 | -0.001301 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_mape__thr=0p32__width=0p4__rel=none__s=0p65 | classifier_rollback | 0.137878 | 0.270579 | 0.807847 | -0.000815 | -0.000283 | 1.000000 | 0.504167 | 0.416667 | -0.001322 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_mape__thr=0p44__width=0p4__rel=risk_only__s=0p85 | classifier_rollback | 0.137878 | 0.270580 | 0.807769 | -0.000815 | -0.000361 | 1.000000 | 0.512500 | 0.412500 | -0.001303 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_score__thr=0p44__width=0p4__rel=none__s=0p65 | classifier_rollback | 0.137878 | 0.270580 | 0.807551 | -0.000815 | -0.000579 | 1.000000 | 0.508333 | 0.408333 | -0.001296 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_mape__thr=0p22__width=0p55__rel=none__s=0p85 | classifier_rollback | 0.137788 | 0.270580 | 0.807893 | -0.000815 | -0.000236 | 1.000000 | 0.504167 | 0.437500 | -0.001386 |
| PP-OPT56 | ppopt56_segment_strength__center=pp45__high=0p42__lowconf=0p55__cap=0p012 | segment_quantile_strength | 0.137878 | 0.270580 | 0.807660 | -0.000815 | -0.000470 | 1.000000 | 0.558333 | 0.420833 | -0.001307 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_mape__thr=0p32__width=0p4__rel=risk_only__s=0p85 | classifier_rollback | 0.137878 | 0.270581 | 0.807836 | -0.000814 | -0.000294 | 1.000000 | 0.504167 | 0.416667 | -0.001321 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_score__thr=0p44__width=0p55__rel=none__s=0p85 | classifier_rollback | 0.137878 | 0.270581 | 0.807557 | -0.000814 | -0.000573 | 1.000000 | 0.512500 | 0.412500 | -0.001303 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_mape__thr=0p32__width=0p7__rel=none__s=0p85 | classifier_rollback | 0.137878 | 0.270582 | 0.807799 | -0.000813 | -0.000331 | 1.000000 | 0.504167 | 0.416667 | -0.001316 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_score__thr=0p44__width=0p4__rel=risk_only__s=0p85 | classifier_rollback | 0.137878 | 0.270582 | 0.807558 | -0.000813 | -0.000572 | 1.000000 | 0.512500 | 0.412500 | -0.001306 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_mape__thr=0p32__width=0p55__rel=none__s=0p65 | classifier_rollback | 0.137878 | 0.270582 | 0.807796 | -0.000813 | -0.000334 | 1.000000 | 0.504167 | 0.416667 | -0.001316 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_score__thr=0p32__width=0p4__rel=none__s=0p85 | classifier_rollback | 0.137878 | 0.270582 | 0.807448 | -0.000812 | -0.000682 | 1.000000 | 0.512500 | 0.412500 | -0.001344 |
| PP-OPT56 | ppopt56_segment_strength__center=pp23__high=0p52__lowconf=0p75__cap=0p012 | segment_quantile_strength | 0.137878 | 0.270583 | 0.807660 | -0.000812 | -0.000470 | 1.000000 | 0.504167 | 0.383333 | -0.001265 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_mape__thr=0p08__width=0p7__rel=none__s=0p85 | classifier_rollback | 0.137562 | 0.270583 | 0.807905 | -0.000812 | -0.000225 | 1.000000 | 0.500000 | 0.454167 | -0.001480 |
| PP-OPT53 | ppopt53_risk_rollback__helper=pp48_safe__score=rollback__thr=0p38__s=0p7 | pp52_risk_rollback | 0.137878 | 0.270583 | 0.807559 | -0.000812 | -0.000571 | 1.000000 | 0.508333 | 0.408333 | -0.001305 |
| PP-OPT53 | ppopt53_risk_rollback__helper=pp48_score__score=rollback__thr=0p38__s=0p7 | pp52_risk_rollback | 0.137878 | 0.270583 | 0.807559 | -0.000812 | -0.000571 | 1.000000 | 0.508333 | 0.408333 | -0.001305 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_mape__thr=0p44__width=0p7__rel=none__s=0p85 | classifier_rollback | 0.137878 | 0.270583 | 0.807746 | -0.000812 | -0.000384 | 1.000000 | 0.520833 | 0.420833 | -0.001318 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_mape__thr=0p32__width=0p55__rel=risk_only__s=0p85 | classifier_rollback | 0.137878 | 0.270583 | 0.807788 | -0.000811 | -0.000342 | 1.000000 | 0.504167 | 0.412500 | -0.001308 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_mape__thr=0p44__width=0p55__rel=none__s=0p65 | classifier_rollback | 0.137878 | 0.270584 | 0.807744 | -0.000811 | -0.000386 | 1.000000 | 0.520833 | 0.420833 | -0.001318 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_score__thr=0p32__width=0p55__rel=none__s=0p85 | classifier_rollback | 0.137878 | 0.270584 | 0.807506 | -0.000811 | -0.000624 | 1.000000 | 0.508333 | 0.408333 | -0.001317 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_mape__thr=0p14__width=0p7__rel=none__s=0p85 | classifier_rollback | 0.137667 | 0.270584 | 0.807879 | -0.000811 | -0.000251 | 1.000000 | 0.500000 | 0.445833 | -0.001434 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_mape__thr=0p22__width=0p7__rel=none__s=0p85 | classifier_rollback | 0.137807 | 0.270584 | 0.807843 | -0.000811 | -0.000286 | 1.000000 | 0.504167 | 0.429167 | -0.001360 |
| PP-OPT56 | ppopt56_segment_strength__center=pp23__high=0p42__lowconf=0p75__cap=0p012 | segment_quantile_strength | 0.137878 | 0.270584 | 0.807660 | -0.000811 | -0.000470 | 1.000000 | 0.504167 | 0.383333 | -0.001266 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_mape__thr=0p22__width=0p55__rel=none__s=0p65 | classifier_rollback | 0.137809 | 0.270584 | 0.807839 | -0.000811 | -0.000291 | 1.000000 | 0.504167 | 0.429167 | -0.001361 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_mape__thr=0p44__width=0p4__rel=risk_only__s=0p65 | classifier_rollback | 0.137878 | 0.270584 | 0.807744 | -0.000811 | -0.000386 | 1.000000 | 0.520833 | 0.420833 | -0.001320 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_mape__thr=0p44__width=0p4__rel=none__s=0p45 | classifier_rollback | 0.137878 | 0.270584 | 0.807740 | -0.000811 | -0.000390 | 1.000000 | 0.520833 | 0.420833 | -0.001318 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_mape__thr=0p44__width=0p55__rel=risk_only__s=0p85 | classifier_rollback | 0.137878 | 0.270585 | 0.807739 | -0.000810 | -0.000391 | 1.000000 | 0.520833 | 0.420833 | -0.001320 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_mape__thr=0p32__width=0p4__rel=risk_only__s=0p65 | classifier_rollback | 0.137878 | 0.270585 | 0.807794 | -0.000810 | -0.000336 | 1.000000 | 0.504167 | 0.412500 | -0.001311 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_score__thr=0p44__width=0p7__rel=none__s=0p85 | classifier_rollback | 0.137878 | 0.270585 | 0.807579 | -0.000810 | -0.000551 | 1.000000 | 0.512500 | 0.412500 | -0.001303 |
| PP-OPT54 | ppopt54_classifier_rollback__helper=pp48_mape__thr=0p22__width=0p55__rel=risk_only__s=0p85 | classifier_rollback | 0.137814 | 0.270585 | 0.807828 | -0.000810 | -0.000302 | 1.000000 | 0.504167 | 0.429167 | -0.001360 |

## 해석
이번 배치는 PP52의 quantile micro 보정을 유지하되, 위험 row에서는 안정 후보로 되돌리는 실험이다. PP52보다 MAPE가 더 좋아지지 않으면 안정성 강화 후보로만 본다.

## 실행 설정
```json
{
  "experiment_id": "PP-OPT53-58",
  "experiment_slug": "PP-OPT53_58_warm_rollback_router_experiments",
  "created_at": "2026-06-09T12:32:12",
  "seed": 20260609,
  "base_candidate": "hcoef_stable",
  "incumbent_candidate": "incumbent_operational_pp_opt7",
  "previous_challenger": "previous_challenger_pp20",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 1512,
  "prediction_rows": 1702512,
  "items": [
    {
      "item_id": "PP-OPT53",
      "priority": "1",
      "title": "PP52 위험도 기반 PP48/PP20 rollback",
      "description": "위험 row에서 PP52를 안정 후보로 부분 rollback한다."
    },
    {
      "item_id": "PP-OPT54",
      "priority": "2",
      "title": "PP52 악화 확률 classifier rollback",
      "description": "validation OOF에서 PP52가 PP45보다 나빠지는 row를 학습해 되돌린다."
    },
    {
      "item_id": "PP-OPT55",
      "priority": "3",
      "title": "quantile consensus dynamic cap",
      "description": "잔차 quantile 폭과 신뢰도에 따라 PP45 기반 보정 cap을 동적으로 조절한다."
    },
    {
      "item_id": "PP-OPT56",
      "priority": "4",
      "title": "segment별 quantile 보정 강도",
      "description": "가격대/신뢰도/불확실성 구간별로 quantile consensus 보정 강도를 다르게 적용한다."
    },
    {
      "item_id": "PP-OPT57",
      "priority": "5",
      "title": "MAPE 후보와 안정 후보의 row별 router",
      "description": "PP52, PP48, PP20, PP30 중 row별로 안전한 후보를 선택 또는 혼합한다."
    },
    {
      "item_id": "PP-OPT58",
      "priority": "6",
      "title": "최종 rollback-router challenger 선택",
      "description": "PP52 대비 개선과 p95 방어를 모두 고려해 최종 후보를 선택한다."
    }
  ],
  "selected_references": {
    "pp20": "previous_challenger_pp20",
    "pp23": "reference_pp23",
    "pp30": "reference_pp30_best",
    "pp38": "reference_pp38_best",
    "pp41": "reference_pp41_challenger",
    "pp45": "reference_pp45_challenger",
    "pp52": "ppopt52_finetune_challenger__source=ppopt49_quantile_consensus_micro__center_pp45__wlim_0p22__guard_medium__s_0p42__cap_0p01",
    "pp48_score": "ppopt48_segment_micro__center=pp38__group=price_conf__shrink=110p0__guard=medium__s=0p32__cap=0p0045",
    "pp48_mape": "ppopt48_segment_micro__center=pp45__group=price_conf__shrink=160p0__guard=medium__s=0p32__cap=0p008",
    "pp50_mape": "ppopt50_lowrisk_q50__center=pp23__rel=0p75__width=mild__s=0p34__cap=0p008",
    "pp49_alt": "ppopt49_quantile_consensus_micro__center=pp45__wlim=0p22__guard=medium__s=0p3__cap=0p01",
    "pp48_safe": "ppopt48_segment_micro__center=pp38__group=price_conf__shrink=110p0__guard=medium__s=0p32__cap=0p0045"
  },
  "selection_decision": {
    "selected_source_candidate": "ppopt54_classifier_rollback__helper=pp48_mape__thr=0p44__width=0p4__rel=none__s=0p85",
    "selected_source_item_id": "PP-OPT54",
    "selected_source_family": "classifier_rollback",
    "selection_reason": "prefer PP52 MAPE improvement with p95 not worse than PP7 and p95 give-back <= 0.00035 versus PP52",
    "test_MdAPE": 0.13787846966744394,
    "test_MAPE": 0.2705716656301805,
    "test_p95_APE": 0.8078112428963969,
    "test_delta_vs_incumbent_MdAPE": 0.000985903768827734,
    "test_delta_vs_incumbent_MAPE": -0.0008232223818859796,
    "test_delta_vs_incumbent_p95_APE": -0.0003187398170717559,
    "recommendation_score_vs_incumbent": -0.0013174240321455041,
    "protocol_candidate": "ppopt58_rollback_router_challenger__source=ppopt54_classifier_rollback__helper_pp48_mape__thr_0p44__width_0p4__rel_none__s_0p85"
  },
  "sources": {
    "pp_opt47_config": "PP-OPT47_52_warm_residual_finetune_experiments",
    "pp_opt47_predictions": "experiments/track6/PP-OPT47_52_warm_residual_finetune_experiments/outputs/candidate_predictions.csv",
    "pp_opt47_aggregate": "experiments/track6/PP-OPT47_52_warm_residual_finetune_experiments/outputs/aggregate_candidate_stability.csv",
    "pp_opt47_quantile": "experiments/track6/PP-OPT47_52_warm_residual_finetune_experiments/artifacts/quantile_residual_predictions.csv",
    "pp_opt47_helper": "scripts/track6/run_pp_opt47_52_warm_residual_finetune_experiments.py"
  }
}
```