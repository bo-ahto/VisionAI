# PP-OPT37~41 Warm 후속 개선 실험 결과

- 작성일: 2026-06-09 12:01
- 데이터 기준: 제출용 제외, Warm validation OOF 519건 + fixed test 607건
- 기준 후보: PP-OPT7 운영 후보
- 비교 후보: PP20, PP23, PP30, PP31, PP36
- 전체 후보 수: 441
- 운영 대체 통과 후보 수: 362

## 최종 선택 후보
- 선택 후보: `ppopt41_followup_challenger__source=ppopt40_p95_penalty_stack__pen_0p75__p20_0p0__p23_0p9__p30_0p1__p31_0p0__p36_0p0`
- 원본 후보: `ppopt40_p95_penalty_stack__pen=0p75__p20=0p0__p23=0p9__p30=0p1__p31=0p0__p36=0p0`
- 원본 실험: `PP-OPT40` / `p95_penalty_limited_stacking`
- 판단: PP41 선택 후보는 PP36 대비 MAPE -0.000024, p95 +0.000063이다.
| eval_split | n | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | delta_vs_incumbent_MdAPE | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | 607 | 0.137845 | 0.270724 | 0.807587 | 0.398003 | 0.784185 | 0.883031 | 0.000953 | -0.000671 | -0.000543 |
| validation_oof | 519 | 0.122425 | 0.206404 | 0.638541 | 0.323788 | 0.782274 | 0.911368 | -0.003498 | -0.000620 | 0.001946 |

## 주요 reference test 비교
| candidate | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- |
| reference_pp23 | 0.137878 | 0.270707 | 0.807660 | 0.398002 | -0.000688 | -0.000470 |
| reference_pp31_best | 0.137878 | 0.270748 | 0.807524 | 0.398008 | -0.000647 | -0.000606 |
| reference_pp36_challenger | 0.137878 | 0.270748 | 0.807524 | 0.398008 | -0.000647 | -0.000606 |
| reference_pp30_best | 0.137546 | 0.270872 | 0.806932 | 0.398014 | -0.000523 | -0.001198 |
| previous_challenger_pp20 | 0.136835 | 0.271182 | 0.806472 | 0.398134 | -0.000213 | -0.001658 |
| incumbent_operational_pp_opt7 | 0.136893 | 0.271395 | 0.808130 | 0.398341 | 0.000000 | 0.000000 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | stable_validation_pass_vs_incumbent | operational_pass_vs_incumbent | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | PP35 segment router 안정화 | 135 | 0.270836 | 0.807102 | -0.000559 | -0.001028 | 1.000000 | 0.541667 | True | True | stabilized_segment_router | ppopt38_router_shrink__router=pp35_guarded__anchor=pp30_score__max=0p8__floor=0p3 |
| 4 | p95 패널티 목적함수 기반 제한 stacking | 36 | 0.270822 | 0.807150 | -0.000573 | -0.000979 | 1.000000 | 0.558333 | True | True | p95_penalty_limited_stacking | ppopt40_p95_penalty_stack__pen=0p75__p20=0p0__p23=0p30000000000000004__p30=0p7000000000000001__p31=0p0__p36=0p0 |
| 3 | selector 확률 보정 후 재블렌드 | 108 | 0.270851 | 0.807059 | -0.000544 | -0.001071 | 1.000000 | 0.554167 | True | True | calibrated_selector_reblend | ppopt39_calibrated_selector__prob=raw_calibrated_geomean__thr=0p1__width=0p45__sharp=1p25 |
| 1 | PP30 selector 후 PP31 tail guard 순차 적용 | 153 | 0.270870 | 0.806952 | -0.000524 | -0.001178 | 1.000000 | 0.554167 | True | True | selector_then_tail_guard | ppopt37_selector_pp31_blend__selector=pp30_score__s=0p1 |
| 5 | 최종 follow-up challenger 선택 | 1 | 0.270724 | 0.807587 | -0.000671 | -0.000543 | 1.000000 | 0.504167 | True | True | followup_challenger_selection_protocol | ppopt41_followup_challenger__source=ppopt40_p95_penalty_stack__pen_0p75__p20_0p0__p23_0p9__p30_0p1__p31_0p0__p36_0p0 |

## 운영 대체 통과 후보 상위
| item_id | candidate | family | test_MdAPE | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | incumbent_all3_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp30_score__max=0p8__floor=0p3 | stabilized_segment_router | 0.137053 | 0.270836 | 0.807102 | -0.000559 | -0.001028 | 1.000000 | 0.541667 | 0.479167 | -0.001713 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp36__max=0p8__floor=0p3 | stabilized_segment_router | 0.137187 | 0.270795 | 0.807356 | -0.000600 | -0.000774 | 1.000000 | 0.541667 | 0.483333 | -0.001709 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp30_score__max=0p8__floor=0p15 | stabilized_segment_router | 0.137089 | 0.270837 | 0.807079 | -0.000558 | -0.001051 | 1.000000 | 0.545833 | 0.479167 | -0.001687 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp36__max=0p8__floor=0p0 | stabilized_segment_router | 0.137287 | 0.270788 | 0.807368 | -0.000607 | -0.000762 | 1.000000 | 0.554167 | 0.500000 | -0.001686 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp36__max=0p8__floor=0p15 | stabilized_segment_router | 0.137237 | 0.270791 | 0.807362 | -0.000603 | -0.000768 | 1.000000 | 0.541667 | 0.483333 | -0.001681 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp36__max=0p65__floor=0p3 | stabilized_segment_router | 0.137317 | 0.270785 | 0.807387 | -0.000610 | -0.000743 | 1.000000 | 0.550000 | 0.500000 | -0.001672 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp30_score__max=0p8__floor=0p0 | stabilized_segment_router | 0.137125 | 0.270838 | 0.807057 | -0.000557 | -0.001073 | 1.000000 | 0.545833 | 0.479167 | -0.001662 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp30_score__max=0p65__floor=0p3 | stabilized_segment_router | 0.137146 | 0.270840 | 0.807070 | -0.000555 | -0.001060 | 1.000000 | 0.541667 | 0.483333 | -0.001658 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp36__max=0p65__floor=0p15 | stabilized_segment_router | 0.137358 | 0.270782 | 0.807392 | -0.000613 | -0.000738 | 1.000000 | 0.550000 | 0.495833 | -0.001641 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp30_score__max=0p65__floor=0p15 | stabilized_segment_router | 0.137175 | 0.270841 | 0.807052 | -0.000554 | -0.001078 | 1.000000 | 0.541667 | 0.483333 | -0.001636 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp36__max=0p65__floor=0p0 | stabilized_segment_router | 0.137398 | 0.270780 | 0.807397 | -0.000615 | -0.000733 | 1.000000 | 0.550000 | 0.504167 | -0.001635 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp30_score__max=0p5__floor=0p3 | stabilized_segment_router | 0.137238 | 0.270845 | 0.807038 | -0.000550 | -0.001092 | 1.000000 | 0.550000 | 0.500000 | -0.001625 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp30_score__max=0p65__floor=0p0 | stabilized_segment_router | 0.137204 | 0.270841 | 0.807033 | -0.000553 | -0.001097 | 1.000000 | 0.545833 | 0.487500 | -0.001623 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp30_score__max=0p5__floor=0p15 | stabilized_segment_router | 0.137261 | 0.270845 | 0.807024 | -0.000550 | -0.001106 | 1.000000 | 0.550000 | 0.500000 | -0.001609 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp36__max=0p5__floor=0p3 | stabilized_segment_router | 0.137446 | 0.270775 | 0.807419 | -0.000620 | -0.000711 | 1.000000 | 0.554167 | 0.500000 | -0.001602 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp30_score__max=0p5__floor=0p0 | stabilized_segment_router | 0.137283 | 0.270846 | 0.807010 | -0.000549 | -0.001120 | 1.000000 | 0.554167 | 0.504167 | -0.001600 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp36__max=0p5__floor=0p15 | stabilized_segment_router | 0.137478 | 0.270773 | 0.807423 | -0.000622 | -0.000707 | 1.000000 | 0.554167 | 0.504167 | -0.001593 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp30_score__max=0p35__floor=0p3 | stabilized_segment_router | 0.137331 | 0.270851 | 0.807006 | -0.000544 | -0.001124 | 1.000000 | 0.554167 | 0.512500 | -0.001584 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp36__max=0p5__floor=0p0 | stabilized_segment_router | 0.137509 | 0.270771 | 0.807427 | -0.000624 | -0.000703 | 1.000000 | 0.554167 | 0.504167 | -0.001575 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp30_score__max=0p35__floor=0p15 | stabilized_segment_router | 0.137346 | 0.270852 | 0.806996 | -0.000543 | -0.001134 | 1.000000 | 0.554167 | 0.512500 | -0.001573 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp30_score__max=0p35__floor=0p0 | stabilized_segment_router | 0.137362 | 0.270852 | 0.806986 | -0.000543 | -0.001144 | 1.000000 | 0.554167 | 0.512500 | -0.001561 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp20__max=0p8__floor=0p3 | stabilized_segment_router | 0.136767 | 0.270960 | 0.806898 | -0.000435 | -0.001232 | 1.000000 | 0.520833 | 0.441667 | -0.001558 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp36__max=0p35__floor=0p3 | stabilized_segment_router | 0.137576 | 0.270766 | 0.807450 | -0.000629 | -0.000680 | 1.000000 | 0.550000 | 0.512500 | -0.001557 |
| PP-OPT38 | ppopt38_router_stable_only__router=pp35_guarded__anchor=pp30_score__thr=0p56 | stabilized_segment_router | 0.137366 | 0.270832 | 0.806936 | -0.000563 | -0.001194 | 1.000000 | 0.558333 | 0.508333 | -0.001555 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp36__max=0p35__floor=0p15 | stabilized_segment_router | 0.137598 | 0.270765 | 0.807453 | -0.000630 | -0.000677 | 1.000000 | 0.550000 | 0.512500 | -0.001545 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp20__max=0p8__floor=0p15 | stabilized_segment_router | 0.136772 | 0.270976 | 0.806851 | -0.000419 | -0.001279 | 1.000000 | 0.520833 | 0.441667 | -0.001535 |
| PP-OPT38 | ppopt38_router_stable_only__router=pp35_guarded__anchor=pp36__thr=0p56 | stabilized_segment_router | 0.137625 | 0.270758 | 0.807489 | -0.000637 | -0.000641 | 1.000000 | 0.558333 | 0.512500 | -0.001533 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp36__max=0p35__floor=0p0 | stabilized_segment_router | 0.137620 | 0.270764 | 0.807456 | -0.000631 | -0.000674 | 1.000000 | 0.541667 | 0.504167 | -0.001516 |
| PP-OPT38 | ppopt38_router_stable_only__router=pp35_guarded__anchor=pp30_score__thr=0p64 | stabilized_segment_router | 0.137546 | 0.270842 | 0.806932 | -0.000553 | -0.001198 | 1.000000 | 0.562500 | 0.520833 | -0.001500 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp20__max=0p8__floor=0p0 | stabilized_segment_router | 0.136777 | 0.270991 | 0.806804 | -0.000404 | -0.001326 | 1.000000 | 0.520833 | 0.433333 | -0.001495 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp20__max=0p65__floor=0p3 | stabilized_segment_router | 0.136780 | 0.270999 | 0.806818 | -0.000396 | -0.001312 | 1.000000 | 0.520833 | 0.429167 | -0.001464 |
| PP-OPT40 | ppopt40_p95_penalty_stack__pen=0p75__p20=0p0__p23=0p30000000000000004__p30=0p7000000000000001__p31=0p0__p36=0p0 | p95_penalty_limited_stacking | 0.137646 | 0.270822 | 0.807150 | -0.000573 | -0.000979 | 1.000000 | 0.558333 | 0.529167 | -0.001458 |
| PP-OPT40 | ppopt40_p95_penalty_stack__pen=0p75__p20=0p0__p23=0p1__p30=0p7000000000000001__p31=0p2__p36=0p0 | p95_penalty_limited_stacking | 0.137646 | 0.270830 | 0.807123 | -0.000565 | -0.001007 | 1.000000 | 0.558333 | 0.529167 | -0.001454 |
| PP-OPT40 | ppopt40_p95_penalty_stack__pen=0p75__p20=0p0__p23=0p2__p30=0p8__p31=0p0__p36=0p0 | p95_penalty_limited_stacking | 0.137613 | 0.270839 | 0.807078 | -0.000556 | -0.001052 | 1.000000 | 0.550000 | 0.525000 | -0.001451 |
| PP-OPT40 | ppopt40_p95_penalty_stack__pen=0p75__p20=0p0__p23=0p1__p30=0p8__p31=0p1__p36=0p0 | p95_penalty_limited_stacking | 0.137613 | 0.270843 | 0.807064 | -0.000552 | -0.001066 | 1.000000 | 0.550000 | 0.525000 | -0.001449 |
| PP-OPT40 | ppopt40_p95_penalty_stack__pen=0p75__p20=0p0__p23=0p1__p30=0p8__p31=0p0__p36=0p09999999999999998 | p95_penalty_limited_stacking | 0.137613 | 0.270843 | 0.807064 | -0.000552 | -0.001066 | 1.000000 | 0.550000 | 0.525000 | -0.001449 |
| PP-OPT40 | ppopt40_p95_penalty_stack__pen=0p75__p20=0p0__p23=0p0__p30=0p8__p31=0p2__p36=0p0 | p95_penalty_limited_stacking | 0.137613 | 0.270847 | 0.807050 | -0.000548 | -0.001080 | 1.000000 | 0.550000 | 0.525000 | -0.001448 |
| PP-OPT40 | ppopt40_p95_penalty_stack__pen=0p75__p20=0p0__p23=0p4__p30=0p6000000000000001__p31=0p0__p36=0p0 | p95_penalty_limited_stacking | 0.137679 | 0.270805 | 0.807223 | -0.000589 | -0.000907 | 1.000000 | 0.558333 | 0.525000 | -0.001447 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp20__max=0p65__floor=0p15 | stabilized_segment_router | 0.136784 | 0.271012 | 0.806780 | -0.000383 | -0.001350 | 1.000000 | 0.525000 | 0.429167 | -0.001444 |
| PP-OPT38 | ppopt38_router_stable_only__router=pp35_p95__anchor=pp30_score__thr=0p64 | stabilized_segment_router | 0.137546 | 0.270857 | 0.806932 | -0.000538 | -0.001198 | 1.000000 | 0.558333 | 0.508333 | -0.001444 |

## 전체 MAPE 상위 후보
| item_id | candidate | family | test_MdAPE | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | incumbent_all3_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REFERENCE | reference_pp35_best_mape | reference_prior | 0.138000 | 0.270374 | 0.807277 | -0.001021 | -0.000853 | 1.000000 | 0.508333 | 0.416667 | -0.001358 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_mape__anchor=pp36__max=0p8__floor=0p3 | stabilized_segment_router | 0.138472 | 0.270540 | 0.807356 | -0.000855 | -0.000774 | 1.000000 | 0.508333 | 0.445833 | -0.001227 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_mape__anchor=pp36__max=0p8__floor=0p15 | stabilized_segment_router | 0.138429 | 0.270560 | 0.807362 | -0.000835 | -0.000768 | 1.000000 | 0.508333 | 0.450000 | -0.001237 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_mape__anchor=pp36__max=0p65__floor=0p3 | stabilized_segment_router | 0.138361 | 0.270577 | 0.807387 | -0.000818 | -0.000743 | 1.000000 | 0.508333 | 0.445833 | -0.001233 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_mape__anchor=pp36__max=0p8__floor=0p0 | stabilized_segment_router | 0.138386 | 0.270579 | 0.807368 | -0.000815 | -0.000762 | 1.000000 | 0.508333 | 0.454167 | -0.001248 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_mape__anchor=pp30_score__max=0p8__floor=0p3 | stabilized_segment_router | 0.138338 | 0.270580 | 0.807102 | -0.000815 | -0.001028 | 1.000000 | 0.516667 | 0.462500 | -0.001275 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_mape__anchor=pp36__max=0p65__floor=0p15 | stabilized_segment_router | 0.138326 | 0.270593 | 0.807392 | -0.000802 | -0.000738 | 1.000000 | 0.508333 | 0.450000 | -0.001243 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_mape__anchor=pp30_score__max=0p8__floor=0p15 | stabilized_segment_router | 0.138281 | 0.270604 | 0.807079 | -0.000791 | -0.001051 | 1.000000 | 0.516667 | 0.462500 | -0.001279 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_mape__anchor=pp36__max=0p65__floor=0p0 | stabilized_segment_router | 0.138291 | 0.270609 | 0.807397 | -0.000785 | -0.000733 | 1.000000 | 0.512500 | 0.458333 | -0.001262 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_mape__anchor=pp36__max=0p5__floor=0p3 | stabilized_segment_router | 0.138249 | 0.270615 | 0.807419 | -0.000780 | -0.000711 | 1.000000 | 0.512500 | 0.454167 | -0.001256 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_mape__anchor=pp36__max=0p5__floor=0p15 | stabilized_segment_router | 0.138222 | 0.270627 | 0.807423 | -0.000768 | -0.000707 | 1.000000 | 0.512500 | 0.458333 | -0.001266 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_mape__anchor=pp30_score__max=0p8__floor=0p0 | stabilized_segment_router | 0.138223 | 0.270628 | 0.807057 | -0.000767 | -0.001073 | 1.000000 | 0.516667 | 0.462500 | -0.001282 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_mape__anchor=pp30_score__max=0p65__floor=0p3 | stabilized_segment_router | 0.138190 | 0.270631 | 0.807070 | -0.000764 | -0.001060 | 1.000000 | 0.512500 | 0.462500 | -0.001285 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_mape__anchor=pp36__max=0p5__floor=0p0 | stabilized_segment_router | 0.138196 | 0.270639 | 0.807427 | -0.000756 | -0.000703 | 1.000000 | 0.512500 | 0.458333 | -0.001267 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_mape__anchor=pp30_score__max=0p65__floor=0p15 | stabilized_segment_router | 0.138143 | 0.270650 | 0.807052 | -0.000745 | -0.001078 | 1.000000 | 0.520833 | 0.462500 | -0.001288 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_mape__anchor=pp36__max=0p35__floor=0p3 | stabilized_segment_router | 0.138138 | 0.270652 | 0.807450 | -0.000742 | -0.000680 | 1.000000 | 0.512500 | 0.458333 | -0.001271 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_mape__anchor=pp36__max=0p35__floor=0p15 | stabilized_segment_router | 0.138119 | 0.270661 | 0.807453 | -0.000734 | -0.000677 | 1.000000 | 0.508333 | 0.458333 | -0.001272 |
| PP-OPT38 | ppopt38_router_stable_only__router=pp35_mape__anchor=pp36__thr=0p48 | stabilized_segment_router | 0.138316 | 0.270663 | 0.807364 | -0.000732 | -0.000766 | 1.000000 | 0.508333 | 0.454167 | -0.001248 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_mape__anchor=pp30_score__max=0p65__floor=0p0 | stabilized_segment_router | 0.138096 | 0.270670 | 0.807033 | -0.000725 | -0.001097 | 1.000000 | 0.520833 | 0.462500 | -0.001291 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_mape__anchor=pp36__max=0p35__floor=0p0 | stabilized_segment_router | 0.138100 | 0.270670 | 0.807456 | -0.000725 | -0.000674 | 1.000000 | 0.508333 | 0.458333 | -0.001273 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_mape__anchor=pp30_score__max=0p5__floor=0p3 | stabilized_segment_router | 0.138041 | 0.270683 | 0.807038 | -0.000712 | -0.001092 | 1.000000 | 0.525000 | 0.466667 | -0.001304 |
| PP-OPT38 | ppopt38_router_stable_only__router=pp35_mape__anchor=pp36__thr=0p56 | stabilized_segment_router | 0.138096 | 0.270697 | 0.807489 | -0.000698 | -0.000641 | 1.000000 | 0.508333 | 0.454167 | -0.001265 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_mape__anchor=pp30_score__max=0p5__floor=0p15 | stabilized_segment_router | 0.138005 | 0.270698 | 0.807024 | -0.000697 | -0.001106 | 1.000000 | 0.533333 | 0.475000 | -0.001323 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_mape__anchor=pp20__max=0p8__floor=0p3 | stabilized_segment_router | 0.138052 | 0.270700 | 0.806898 | -0.000695 | -0.001232 | 1.000000 | 0.516667 | 0.437500 | -0.001184 |
| REFERENCE | reference_pp23 | reference_prior | 0.137878 | 0.270707 | 0.807660 | -0.000688 | -0.000470 | 1.000000 | 0.504167 | 0.400000 | -0.001185 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_mape__anchor=pp30_score__max=0p5__floor=0p0 | stabilized_segment_router | 0.137969 | 0.270713 | 0.807010 | -0.000682 | -0.001120 | 1.000000 | 0.537500 | 0.479167 | -0.001334 |
| PP-OPT38 | ppopt38_router_stable_only__router=pp35_mape__anchor=pp30_score__thr=0p48 | stabilized_segment_router | 0.138131 | 0.270714 | 0.806952 | -0.000681 | -0.001178 | 1.000000 | 0.495833 | 0.445833 | -0.001247 |
| PP-OPT40 | ppopt40_p95_penalty_stack__pen=0p75__p20=0p0__p23=0p9__p30=0p1__p31=0p0__p36=0p0 | p95_penalty_limited_stacking | 0.137845 | 0.270724 | 0.807587 | -0.000671 | -0.000543 | 1.000000 | 0.504167 | 0.462500 | -0.001312 |
| PP-OPT41 | ppopt41_followup_challenger__source=ppopt40_p95_penalty_stack__pen_0p75__p20_0p0__p23_0p9__p30_0p1__p31_0p0__p36_0p0 | followup_challenger_selection_protocol | 0.137845 | 0.270724 | 0.807587 | -0.000671 | -0.000543 | 1.000000 | 0.504167 | 0.462500 | -0.001312 |
| PP-OPT38 | ppopt38_router_stable_only__router=pp35_mape__anchor=pp36__thr=0p64 | stabilized_segment_router | 0.137878 | 0.270732 | 0.807524 | -0.000663 | -0.000606 | 1.000000 | 0.508333 | 0.441667 | -0.001270 |

## MAPE와 p95 동시 개선 후보
| item_id | candidate | family | test_MdAPE | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | incumbent_all3_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp30_score__max=0p8__floor=0p3 | stabilized_segment_router | 0.137053 | 0.270836 | 0.807102 | -0.000559 | -0.001028 | 1.000000 | 0.541667 | 0.479167 | -0.001713 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp36__max=0p8__floor=0p3 | stabilized_segment_router | 0.137187 | 0.270795 | 0.807356 | -0.000600 | -0.000774 | 1.000000 | 0.541667 | 0.483333 | -0.001709 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp30_score__max=0p8__floor=0p15 | stabilized_segment_router | 0.137089 | 0.270837 | 0.807079 | -0.000558 | -0.001051 | 1.000000 | 0.545833 | 0.479167 | -0.001687 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp36__max=0p8__floor=0p0 | stabilized_segment_router | 0.137287 | 0.270788 | 0.807368 | -0.000607 | -0.000762 | 1.000000 | 0.554167 | 0.500000 | -0.001686 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp36__max=0p8__floor=0p15 | stabilized_segment_router | 0.137237 | 0.270791 | 0.807362 | -0.000603 | -0.000768 | 1.000000 | 0.541667 | 0.483333 | -0.001681 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp36__max=0p65__floor=0p3 | stabilized_segment_router | 0.137317 | 0.270785 | 0.807387 | -0.000610 | -0.000743 | 1.000000 | 0.550000 | 0.500000 | -0.001672 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp30_score__max=0p8__floor=0p0 | stabilized_segment_router | 0.137125 | 0.270838 | 0.807057 | -0.000557 | -0.001073 | 1.000000 | 0.545833 | 0.479167 | -0.001662 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp30_score__max=0p65__floor=0p3 | stabilized_segment_router | 0.137146 | 0.270840 | 0.807070 | -0.000555 | -0.001060 | 1.000000 | 0.541667 | 0.483333 | -0.001658 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp36__max=0p65__floor=0p15 | stabilized_segment_router | 0.137358 | 0.270782 | 0.807392 | -0.000613 | -0.000738 | 1.000000 | 0.550000 | 0.495833 | -0.001641 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp30_score__max=0p65__floor=0p15 | stabilized_segment_router | 0.137175 | 0.270841 | 0.807052 | -0.000554 | -0.001078 | 1.000000 | 0.541667 | 0.483333 | -0.001636 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp36__max=0p65__floor=0p0 | stabilized_segment_router | 0.137398 | 0.270780 | 0.807397 | -0.000615 | -0.000733 | 1.000000 | 0.550000 | 0.504167 | -0.001635 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp30_score__max=0p5__floor=0p3 | stabilized_segment_router | 0.137238 | 0.270845 | 0.807038 | -0.000550 | -0.001092 | 1.000000 | 0.550000 | 0.500000 | -0.001625 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp30_score__max=0p65__floor=0p0 | stabilized_segment_router | 0.137204 | 0.270841 | 0.807033 | -0.000553 | -0.001097 | 1.000000 | 0.545833 | 0.487500 | -0.001623 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp30_score__max=0p5__floor=0p15 | stabilized_segment_router | 0.137261 | 0.270845 | 0.807024 | -0.000550 | -0.001106 | 1.000000 | 0.550000 | 0.500000 | -0.001609 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp36__max=0p5__floor=0p3 | stabilized_segment_router | 0.137446 | 0.270775 | 0.807419 | -0.000620 | -0.000711 | 1.000000 | 0.554167 | 0.500000 | -0.001602 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp30_score__max=0p5__floor=0p0 | stabilized_segment_router | 0.137283 | 0.270846 | 0.807010 | -0.000549 | -0.001120 | 1.000000 | 0.554167 | 0.504167 | -0.001600 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp36__max=0p5__floor=0p15 | stabilized_segment_router | 0.137478 | 0.270773 | 0.807423 | -0.000622 | -0.000707 | 1.000000 | 0.554167 | 0.504167 | -0.001593 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp30_score__max=0p35__floor=0p3 | stabilized_segment_router | 0.137331 | 0.270851 | 0.807006 | -0.000544 | -0.001124 | 1.000000 | 0.554167 | 0.512500 | -0.001584 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp36__max=0p5__floor=0p0 | stabilized_segment_router | 0.137509 | 0.270771 | 0.807427 | -0.000624 | -0.000703 | 1.000000 | 0.554167 | 0.504167 | -0.001575 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp30_score__max=0p35__floor=0p15 | stabilized_segment_router | 0.137346 | 0.270852 | 0.806996 | -0.000543 | -0.001134 | 1.000000 | 0.554167 | 0.512500 | -0.001573 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp30_score__max=0p35__floor=0p0 | stabilized_segment_router | 0.137362 | 0.270852 | 0.806986 | -0.000543 | -0.001144 | 1.000000 | 0.554167 | 0.512500 | -0.001561 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp20__max=0p8__floor=0p3 | stabilized_segment_router | 0.136767 | 0.270960 | 0.806898 | -0.000435 | -0.001232 | 1.000000 | 0.520833 | 0.441667 | -0.001558 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp36__max=0p35__floor=0p3 | stabilized_segment_router | 0.137576 | 0.270766 | 0.807450 | -0.000629 | -0.000680 | 1.000000 | 0.550000 | 0.512500 | -0.001557 |
| PP-OPT38 | ppopt38_router_stable_only__router=pp35_guarded__anchor=pp30_score__thr=0p56 | stabilized_segment_router | 0.137366 | 0.270832 | 0.806936 | -0.000563 | -0.001194 | 1.000000 | 0.558333 | 0.508333 | -0.001555 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp36__max=0p35__floor=0p15 | stabilized_segment_router | 0.137598 | 0.270765 | 0.807453 | -0.000630 | -0.000677 | 1.000000 | 0.550000 | 0.512500 | -0.001545 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp20__max=0p8__floor=0p15 | stabilized_segment_router | 0.136772 | 0.270976 | 0.806851 | -0.000419 | -0.001279 | 1.000000 | 0.520833 | 0.441667 | -0.001535 |
| PP-OPT38 | ppopt38_router_stable_only__router=pp35_guarded__anchor=pp36__thr=0p56 | stabilized_segment_router | 0.137625 | 0.270758 | 0.807489 | -0.000637 | -0.000641 | 1.000000 | 0.558333 | 0.512500 | -0.001533 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp36__max=0p35__floor=0p0 | stabilized_segment_router | 0.137620 | 0.270764 | 0.807456 | -0.000631 | -0.000674 | 1.000000 | 0.541667 | 0.504167 | -0.001516 |
| PP-OPT38 | ppopt38_router_stable_only__router=pp35_guarded__anchor=pp30_score__thr=0p64 | stabilized_segment_router | 0.137546 | 0.270842 | 0.806932 | -0.000553 | -0.001198 | 1.000000 | 0.562500 | 0.520833 | -0.001500 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp20__max=0p8__floor=0p0 | stabilized_segment_router | 0.136777 | 0.270991 | 0.806804 | -0.000404 | -0.001326 | 1.000000 | 0.520833 | 0.433333 | -0.001495 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp20__max=0p65__floor=0p3 | stabilized_segment_router | 0.136780 | 0.270999 | 0.806818 | -0.000396 | -0.001312 | 1.000000 | 0.520833 | 0.429167 | -0.001464 |
| PP-OPT40 | ppopt40_p95_penalty_stack__pen=0p75__p20=0p0__p23=0p30000000000000004__p30=0p7000000000000001__p31=0p0__p36=0p0 | p95_penalty_limited_stacking | 0.137646 | 0.270822 | 0.807150 | -0.000573 | -0.000979 | 1.000000 | 0.558333 | 0.529167 | -0.001458 |
| PP-OPT40 | ppopt40_p95_penalty_stack__pen=0p75__p20=0p0__p23=0p1__p30=0p7000000000000001__p31=0p2__p36=0p0 | p95_penalty_limited_stacking | 0.137646 | 0.270830 | 0.807123 | -0.000565 | -0.001007 | 1.000000 | 0.558333 | 0.529167 | -0.001454 |
| PP-OPT40 | ppopt40_p95_penalty_stack__pen=0p75__p20=0p0__p23=0p2__p30=0p8__p31=0p0__p36=0p0 | p95_penalty_limited_stacking | 0.137613 | 0.270839 | 0.807078 | -0.000556 | -0.001052 | 1.000000 | 0.550000 | 0.525000 | -0.001451 |
| PP-OPT40 | ppopt40_p95_penalty_stack__pen=0p75__p20=0p0__p23=0p1__p30=0p8__p31=0p1__p36=0p0 | p95_penalty_limited_stacking | 0.137613 | 0.270843 | 0.807064 | -0.000552 | -0.001066 | 1.000000 | 0.550000 | 0.525000 | -0.001449 |
| PP-OPT40 | ppopt40_p95_penalty_stack__pen=0p75__p20=0p0__p23=0p1__p30=0p8__p31=0p0__p36=0p09999999999999998 | p95_penalty_limited_stacking | 0.137613 | 0.270843 | 0.807064 | -0.000552 | -0.001066 | 1.000000 | 0.550000 | 0.525000 | -0.001449 |
| PP-OPT40 | ppopt40_p95_penalty_stack__pen=0p75__p20=0p0__p23=0p0__p30=0p8__p31=0p2__p36=0p0 | p95_penalty_limited_stacking | 0.137613 | 0.270847 | 0.807050 | -0.000548 | -0.001080 | 1.000000 | 0.550000 | 0.525000 | -0.001448 |
| PP-OPT40 | ppopt40_p95_penalty_stack__pen=0p75__p20=0p0__p23=0p4__p30=0p6000000000000001__p31=0p0__p36=0p0 | p95_penalty_limited_stacking | 0.137679 | 0.270805 | 0.807223 | -0.000589 | -0.000907 | 1.000000 | 0.558333 | 0.525000 | -0.001447 |
| PP-OPT38 | ppopt38_router_shrink__router=pp35_guarded__anchor=pp20__max=0p65__floor=0p15 | stabilized_segment_router | 0.136784 | 0.271012 | 0.806780 | -0.000383 | -0.001350 | 1.000000 | 0.525000 | 0.429167 | -0.001444 |
| PP-OPT38 | ppopt38_router_stable_only__router=pp35_p95__anchor=pp30_score__thr=0p64 | stabilized_segment_router | 0.137546 | 0.270857 | 0.806932 | -0.000538 | -0.001198 | 1.000000 | 0.558333 | 0.508333 | -0.001444 |

## 해석
PP30 계열의 row별 선택은 여전히 안정적인 개선 신호가 가장 강하다. PP35 router는 MAPE 잠재력은 크지만 shrinkage를 걸어도 반복 검증 안정성 관리가 핵심이다.
후속 운영 판단은 PP20 p95 안정성, PP23/PP36 MAPE 개선, PP41의 균형 개선을 함께 비교해야 한다.

## 실행 설정
```json
{
  "experiment_id": "PP-OPT37-41",
  "experiment_slug": "PP-OPT37_41_warm_followup_refinement_experiments",
  "created_at": "2026-06-09T12:01:25",
  "seed": 20260609,
  "base_candidate": "hcoef_stable",
  "incumbent_candidate": "incumbent_operational_pp_opt7",
  "previous_challenger": "previous_challenger_pp20",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 442,
  "prediction_rows": 497692,
  "items": [
    {
      "item_id": "PP-OPT37",
      "priority": "1",
      "title": "PP30 selector 후 PP31 tail guard 순차 적용",
      "description": "row별 PP20/PP23 선택값에 tail 위험 구간 보정을 약하게 얹는다."
    },
    {
      "item_id": "PP-OPT38",
      "priority": "2",
      "title": "PP35 segment router 안정화",
      "description": "MAPE 개선 신호가 컸던 segment router를 표본/위험도 기반 shrinkage로 안정화한다."
    },
    {
      "item_id": "PP-OPT39",
      "priority": "3",
      "title": "selector 확률 보정 후 재블렌드",
      "description": "LightGBM selector 확률을 validation OOF에서 bin calibration한 뒤 PP20/PP23 가중치를 다시 계산한다."
    },
    {
      "item_id": "PP-OPT40",
      "priority": "4",
      "title": "p95 패널티 목적함수 기반 제한 stacking",
      "description": "validation OOF에서 MAPE와 p95 패널티를 함께 최소화하는 제한 가중 조합을 고른다."
    },
    {
      "item_id": "PP-OPT41",
      "priority": "5",
      "title": "최종 follow-up challenger 선택",
      "description": "PP20/PP36 대비 MAPE 개선과 p95 손실 한도를 함께 보며 최종 후보를 고른다."
    }
  ],
  "selected_components": {
    "pp20": "ppopt20_protocol_selected__source=ppopt19_segment_tuning__profile_low_support_tail__artist_cat_artist_mean__as_0p25__ts_0p55",
    "pp23": "ppopt23_monotonic_gate__src=pp15_best_mape__thr=0p16__s=0p85",
    "pp23_mape": "ppopt23_monotonic_gate__src=opt8_cat_price_band__thr=0p16__s=0p85",
    "pp27_tail": "ppopt27_micro_residual__center=pp19_best_score__s=0p5__cap=0p01",
    "pp15_mape": "ppopt15_absorb_pp12__base=pp9_best_mape__p12s=0p34__p9s=1p05__cap=0p026",
    "pp21_mape": "ppopt21_uplift_gate__src=opt8_artist_mape__model=lgbm__thr=0p18__s=0p95",
    "pp19_stable": "ppopt19_segment_tuning__profile=price_tail_high__artist=artist__as=0p35__ts=0p75",
    "pp14_stable": "ppopt14_gate_grid__artist=artist_stable__sthr=0p12__tthr=0p25__as=0p2__ts=0p75__cap=0p024",
    "pp24_conformal": "ppopt24_conformal_gate__src=pp19_best_score__s=0p95__cap=0p018"
  },
  "prior_candidates": {
    "pp30_score": "ppopt30_row_selector__model=select_pp23_lgbm__thr=0p18__sharp=1p0",
    "pp30_p95": "ppopt30_row_selector__model=select_pp23_cat__thr=0p28__sharp=0p75",
    "pp31_mape": "ppopt31_pp23_tail_guard__thr=0p3__s=0p25__cap=0p01",
    "pp36": "ppopt36_final_challenger__source=ppopt31_pp23_tail_guard__thr_0p3__s_0p25__cap_0p01",
    "pp35_mape": "ppopt35_segment_router__group=price__obj=mape",
    "pp35_guarded": "ppopt35_segment_router__group=spread_price__obj=guarded",
    "pp35_p95": "ppopt35_segment_router__group=price__obj=guarded"
  },
  "thresholds": {
    "p85": 0.38339160296436176,
    "p90": 0.4636774710873784,
    "p95": 0.6365947866362616
  },
  "selection_decision": {
    "selected_source_candidate": "ppopt40_p95_penalty_stack__pen=0p75__p20=0p0__p23=0p9__p30=0p1__p31=0p0__p36=0p0",
    "protocol_candidate": "ppopt41_followup_challenger__source=ppopt40_p95_penalty_stack__pen_0p75__p20_0p0__p23_0p9__p30_0p1__p31_0p0__p36_0p0",
    "selected_source_item_id": "PP-OPT40",
    "selected_source_family": "p95_penalty_limited_stacking",
    "selection_reason": "operational pass first, then PP36 improvement with tight p95 give-back; fallback to PP20 improvement rule",
    "test_MdAPE": 0.13784524368141932,
    "test_MAPE": 0.2707235616573717,
    "test_p95_APE": 0.807587276131646,
    "test_delta_vs_incumbent_MdAPE": 0.000952677782803113,
    "test_delta_vs_incumbent_MAPE": -0.0006713263546947457,
    "test_delta_vs_incumbent_p95_APE": -0.0005427065818226495,
    "recommendation_score_vs_incumbent": -0.001312146382352406
  },
  "sources": {
    "pp_opt29_config": "PP-OPT29_36_warm_final_hybrid_selection_experiments",
    "pp_opt29_predictions": "experiments/track6/PP-OPT29_36_warm_final_hybrid_selection_experiments/outputs/candidate_predictions.csv",
    "pp_opt29_aggregate": "experiments/track6/PP-OPT29_36_warm_final_hybrid_selection_experiments/outputs/aggregate_candidate_stability.csv",
    "pp_opt29_helper": "scripts/track6/run_pp_opt29_36_warm_final_hybrid_selection_experiments.py"
  }
}
```