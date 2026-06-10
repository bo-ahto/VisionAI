# PP-OPT76~82 Warm tail routing 실험 결과

- 작성일: 2026-06-09 13:51
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 목적: 정상 row는 PP64/PP70을 유지하고 tail 위험 row만 PP20/PP30/PP48 안정 후보로 이동
- 전체 후보 수: 4227
- 운영 대체 통과 후보 수: 4225
- 판단: 운영형 후보는 PP64 대비 MAPE -0.000007, p95 -0.000049. p95 목적형 후보는 PP64 대비 MAPE +0.000087, p95 -0.000659.

## 선택 후보
- 운영형: `ppopt82_operational_tail_routing_challenger__source=ppopt80_hard_tail__anchor_pp70__helper_pp20__score_p95_prob__thr_0p62__width_0p24__s_1p0`
- p95 목적형: `ppopt82_p95_tail_routing_challenger__source=ppopt77_clf_tail__anchor_pp70__helper_pp20__prob_tail85_only__thr_0p26__width_0p18__s_0p64`
| candidate | eval_split | n | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt82_operational_tail_routing_challenger__source=ppopt80_hard_tail__anchor_pp70__helper_pp20__score_p95_prob__thr_0p62__width_0p24__s_1p0 | test | 607 | 0.137878 | 0.270557 | 0.807450 | 0.397982 | 0.782537 | 0.883031 | -0.000838 | -0.000680 |
| ppopt82_operational_tail_routing_challenger__source=ppopt80_hard_tail__anchor_pp70__helper_pp20__score_p95_prob__thr_0p62__width_0p24__s_1p0 | validation_oof | 519 | 0.122635 | 0.206316 | 0.637897 | 0.323832 | 0.782274 | 0.911368 | -0.000707 | 0.001302 |
| ppopt82_p95_tail_routing_challenger__source=ppopt77_clf_tail__anchor_pp70__helper_pp20__prob_tail85_only__thr_0p26__width_0p18__s_0p64 | test | 607 | 0.137634 | 0.270651 | 0.806840 | 0.397982 | 0.782537 | 0.883031 | -0.000744 | -0.001290 |
| ppopt82_p95_tail_routing_challenger__source=ppopt77_clf_tail__anchor_pp70__helper_pp20__prob_tail85_only__thr_0p26__width_0p18__s_0p64 | validation_oof | 519 | 0.122780 | 0.206340 | 0.637897 | 0.323887 | 0.782274 | 0.911368 | -0.000683 | 0.001302 |

## 주요 reference test 비교
| candidate | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- |
| ppopt82_operational_tail_routing_challenger__source=ppopt80_hard_tail__anchor_pp70__helper_pp20__score_p95_prob__thr_0p62__width_0p24__s_1p0 | 0.137878 | 0.270557 | 0.807450 | 0.397982 | -0.000838 | -0.000680 |
| reference_pp70_refinement | 0.137878 | 0.270561 | 0.807490 | 0.397991 | -0.000834 | -0.000640 |
| reference_pp64_current_best | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |
| reference_pp58_challenger | 0.137878 | 0.270572 | 0.807811 | 0.397997 | -0.000823 | -0.000319 |
| reference_pp52_challenger | 0.137878 | 0.270598 | 0.807660 | 0.397987 | -0.000797 | -0.000470 |
| ppopt82_p95_tail_routing_challenger__source=ppopt77_clf_tail__anchor_pp70__helper_pp20__prob_tail85_only__thr_0p26__width_0p18__s_0p64 | 0.137634 | 0.270651 | 0.806840 | 0.397982 | -0.000744 | -0.001290 |
| reference_pp48_score | 0.136800 | 0.270816 | 0.807385 | 0.398121 | -0.000579 | -0.000745 |
| reference_pp30_best | 0.137546 | 0.270872 | 0.806932 | 0.398014 | -0.000523 | -0.001198 |
| previous_challenger_pp20 | 0.136835 | 0.271182 | 0.806472 | 0.398134 | -0.000213 | -0.001658 |
| incumbent_operational_pp_opt7 | 0.136893 | 0.271395 | 0.808130 | 0.398341 | 0.000000 | 0.000000 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | operational_pass_vs_incumbent | p95_best_test_MAPE | p95_best_test_p95_APE | best_family | best_candidate | p95_best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | validation-trained tail classifier routing | 1800 | 0.270720 | 0.807423 | True | 0.270651 | 0.806840 | classifier_tail_routing | ppopt77_clf_tail__anchor=pp70__helper=pp48__prob=tail85_only__thr=0p1__width=0p18__s=0p64 | ppopt77_clf_tail__anchor=pp70__helper=pp20__prob=tail85_only__thr=0p26__width=0p18__s=0p64 |
| 3 | helper-specific better-probability routing | 288 | 0.270585 | 0.807385 | True | 0.270701 | 0.807133 | helper_specific_probability_routing | ppopt78_helper_prob__anchor=pp70__helper=pp48_bias__thr=0p2__width=0p34__s=0p52 | ppopt78_helper_prob__anchor=pp70__helper=p95_bias__thr=0p12__width=0p2__s=0p52 |
| 7 | 최종 tail-routing challenger 선택 | 2 | 0.270651 | 0.806840 | True | 0.270651 | 0.806840 | tail_routing_p95_selection | ppopt82_p95_tail_routing_challenger__source=ppopt77_clf_tail__anchor_pp70__helper_pp20__prob_tail85_only__thr_0p26__width_0p18__s_0p64 | ppopt82_p95_tail_routing_challenger__source=ppopt77_clf_tail__anchor_pp70__helper_pp20__prob_tail85_only__thr_0p26__width_0p18__s_0p64 |
| 1 | deterministic tail-risk score routing | 1200 | 0.270573 | 0.807490 | True | 0.270615 | 0.807443 | deterministic_tail_score_routing | ppopt76_det_tail__anchor=pp70__helper=pp48__score=p95__thr=0p82__width=0p18__s=0p58 | ppopt76_det_tail__anchor=pp70__helper=pp20__score=risk__thr=0p5__width=0p18__s=0p58 |
| 6 | tail routing ensemble | 288 | 0.270559 | 0.807490 | True | 0.270559 | 0.807490 | tail_routing_ensemble | ppopt81_tail_ensemble__anchor=pp70__helper=pp48_p95_mix__thr=0p48__width=0p22__s=0p56 | ppopt81_tail_ensemble__anchor=pp70__helper=pp48_p95_mix__thr=0p48__width=0p22__s=0p56 |
| 4 | quantile-direction aligned tail routing | 256 | 0.270561 | 0.807490 | True | 0.270561 | 0.807490 | quantile_direction_tail_routing | ppopt79_qdir_tail__anchor=pp70__helper=p95_weighted__score=risk__thr=0p72__s=0p12 | ppopt79_qdir_tail__anchor=pp70__helper=p95_weighted__score=risk__thr=0p72__s=0p12 |
| 5 | p95-first hard tail fallback | 384 | 0.270561 | 0.807490 | True | 0.270557 | 0.807422 | p95_first_hard_tail_fallback | ppopt80_hard_tail__anchor=pp70__helper=p95_weighted__score=risk_prob__thr=0p7__width=0p14__s=1p0 | ppopt80_hard_tail__anchor=pp70__helper=pp20__score=p95_prob__thr=0p62__width=0p14__s=1p0 |

## 운영 통과 후보 상위
| item_id | candidate | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REFERENCE | reference_pp48_score | reference_prior | 0.270816 | 0.807385 | -0.000579 | -0.000745 | 1.000000 | 0.900000 | -0.002413 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp48__prob=tail85_only__thr=0p1__width=0p18__s=0p64 | classifier_tail_routing | 0.270720 | 0.807423 | -0.000675 | -0.000707 | 1.000000 | 0.587500 | -0.001859 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=pp48__prob=tail85_only__thr=0p1__width=0p18__s=0p64 | classifier_tail_routing | 0.270722 | 0.807426 | -0.000673 | -0.000704 | 1.000000 | 0.587500 | -0.001859 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp48__prob=tail85_only__thr=0p1__width=0p32__s=0p64 | classifier_tail_routing | 0.270702 | 0.807423 | -0.000693 | -0.000707 | 1.000000 | 0.537500 | -0.001788 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=pp48__prob=tail85_only__thr=0p1__width=0p32__s=0p64 | classifier_tail_routing | 0.270704 | 0.807426 | -0.000691 | -0.000704 | 1.000000 | 0.537500 | -0.001788 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=pp48__prob=tail85_only__thr=0p18__width=0p18__s=0p64 | classifier_tail_routing | 0.270703 | 0.807426 | -0.000692 | -0.000704 | 1.000000 | 0.537500 | -0.001779 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp48__prob=tail85_only__thr=0p18__width=0p18__s=0p64 | classifier_tail_routing | 0.270700 | 0.807423 | -0.000694 | -0.000707 | 1.000000 | 0.537500 | -0.001779 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp48__prob=tail85_only__thr=0p1__width=0p18__s=0p46 | classifier_tail_routing | 0.270675 | 0.807442 | -0.000720 | -0.000688 | 1.000000 | 0.529167 | -0.001732 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=pp48__prob=tail85_only__thr=0p1__width=0p18__s=0p46 | classifier_tail_routing | 0.270677 | 0.807447 | -0.000718 | -0.000683 | 1.000000 | 0.529167 | -0.001732 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp48__prob=tail85_only__thr=0p1__width=0p46__s=0p64 | classifier_tail_routing | 0.270671 | 0.807454 | -0.000724 | -0.000676 | 1.000000 | 0.525000 | -0.001725 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=pp48__prob=tail85_only__thr=0p1__width=0p46__s=0p64 | classifier_tail_routing | 0.270674 | 0.807459 | -0.000721 | -0.000671 | 1.000000 | 0.525000 | -0.001725 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp48__prob=tail85_only__thr=0p18__width=0p18__s=0p46 | classifier_tail_routing | 0.270661 | 0.807442 | -0.000734 | -0.000688 | 1.000000 | 0.525000 | -0.001721 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=pp48__prob=tail85_only__thr=0p18__width=0p18__s=0p46 | classifier_tail_routing | 0.270663 | 0.807447 | -0.000731 | -0.000683 | 1.000000 | 0.525000 | -0.001721 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp48__prob=tail85_only__thr=0p1__width=0p32__s=0p46 | classifier_tail_routing | 0.270662 | 0.807442 | -0.000733 | -0.000688 | 1.000000 | 0.525000 | -0.001716 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=pp48__prob=tail85_only__thr=0p1__width=0p32__s=0p46 | classifier_tail_routing | 0.270664 | 0.807447 | -0.000731 | -0.000683 | 1.000000 | 0.525000 | -0.001716 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp48__prob=tail85_only__thr=0p18__width=0p32__s=0p64 | classifier_tail_routing | 0.270672 | 0.807445 | -0.000722 | -0.000685 | 1.000000 | 0.529167 | -0.001712 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=pp48__prob=tail85_only__thr=0p18__width=0p32__s=0p64 | classifier_tail_routing | 0.270675 | 0.807449 | -0.000720 | -0.000681 | 1.000000 | 0.529167 | -0.001712 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp48__prob=tail85_only__thr=0p26__width=0p18__s=0p64 | classifier_tail_routing | 0.270676 | 0.807423 | -0.000719 | -0.000707 | 1.000000 | 0.533333 | -0.001694 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=pp48__prob=tail85_only__thr=0p26__width=0p18__s=0p64 | classifier_tail_routing | 0.270679 | 0.807426 | -0.000716 | -0.000704 | 1.000000 | 0.533333 | -0.001694 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp48__prob=tail85_only__thr=0p18__width=0p46__s=0p64 | classifier_tail_routing | 0.270640 | 0.807475 | -0.000755 | -0.000655 | 1.000000 | 0.545833 | -0.001663 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=pp48__prob=tail85_only__thr=0p18__width=0p46__s=0p64 | classifier_tail_routing | 0.270643 | 0.807480 | -0.000752 | -0.000650 | 1.000000 | 0.545833 | -0.001663 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp48__prob=tail85_only__thr=0p1__width=0p18__s=0p3 | classifier_tail_routing | 0.270635 | 0.807459 | -0.000760 | -0.000671 | 1.000000 | 0.512500 | -0.001657 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=pp48__prob=tail85_only__thr=0p1__width=0p18__s=0p3 | classifier_tail_routing | 0.270638 | 0.807465 | -0.000757 | -0.000665 | 1.000000 | 0.512500 | -0.001657 |
| PP-OPT78 | ppopt78_helper_prob__anchor=pp70__helper=pp48_bias__thr=0p2__width=0p34__s=0p52 | helper_specific_probability_routing | 0.270585 | 0.807385 | -0.000810 | -0.000745 | 1.000000 | 0.508333 | -0.001622 |
| PP-OPT78 | ppopt78_helper_prob__anchor=pp64__helper=pp48_bias__thr=0p2__width=0p34__s=0p52 | helper_specific_probability_routing | 0.270587 | 0.807392 | -0.000808 | -0.000738 | 1.000000 | 0.508333 | -0.001622 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=pp48__prob=tail85_only__thr=0p26__width=0p32__s=0p64 | classifier_tail_routing | 0.270641 | 0.807481 | -0.000753 | -0.000649 | 1.000000 | 0.545833 | -0.001618 |
| PP-OPT78 | ppopt78_helper_prob__anchor=pp70__helper=pp48_bias__thr=0p2__width=0p2__s=0p52 | helper_specific_probability_routing | 0.270597 | 0.807312 | -0.000798 | -0.000818 | 1.000000 | 0.508333 | -0.001614 |
| PP-OPT78 | ppopt78_helper_prob__anchor=pp64__helper=pp48_bias__thr=0p2__width=0p2__s=0p52 | helper_specific_probability_routing | 0.270599 | 0.807317 | -0.000796 | -0.000812 | 1.000000 | 0.508333 | -0.001614 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=p95_weighted__prob=tail85_only__thr=0p1__width=0p18__s=0p64 | classifier_tail_routing | 0.270749 | 0.807074 | -0.000646 | -0.001056 | 1.000000 | 0.541667 | -0.001613 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=p95_weighted__prob=tail85_only__thr=0p1__width=0p18__s=0p64 | classifier_tail_routing | 0.270750 | 0.807077 | -0.000645 | -0.001053 | 1.000000 | 0.541667 | -0.001613 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp48__prob=tail85_only__thr=0p1__width=0p46__s=0p46 | classifier_tail_routing | 0.270640 | 0.807464 | -0.000755 | -0.000666 | 1.000000 | 0.512500 | -0.001611 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=pp48__prob=tail85_only__thr=0p1__width=0p46__s=0p46 | classifier_tail_routing | 0.270643 | 0.807470 | -0.000752 | -0.000660 | 1.000000 | 0.512500 | -0.001611 |
| PP-OPT78 | ppopt78_helper_prob__anchor=pp70__helper=pp48_bias__thr=0p12__width=0p2__s=0p52 | helper_specific_probability_routing | 0.270631 | 0.807281 | -0.000764 | -0.000849 | 1.000000 | 0.516667 | -0.001602 |
| PP-OPT78 | ppopt78_helper_prob__anchor=pp64__helper=pp48_bias__thr=0p12__width=0p2__s=0p52 | helper_specific_probability_routing | 0.270633 | 0.807286 | -0.000762 | -0.000844 | 1.000000 | 0.516667 | -0.001602 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp48__prob=tail85_only__thr=0p18__width=0p18__s=0p3 | classifier_tail_routing | 0.270626 | 0.807459 | -0.000769 | -0.000671 | 1.000000 | 0.512500 | -0.001601 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=pp48__prob=tail85_only__thr=0p18__width=0p18__s=0p3 | classifier_tail_routing | 0.270629 | 0.807465 | -0.000766 | -0.000665 | 1.000000 | 0.512500 | -0.001601 |
| PP-OPT78 | ppopt78_helper_prob__anchor=pp70__helper=pp48_bias__thr=0p12__width=0p34__s=0p52 | helper_specific_probability_routing | 0.270605 | 0.807336 | -0.000790 | -0.000794 | 1.000000 | 0.508333 | -0.001600 |
| PP-OPT78 | ppopt78_helper_prob__anchor=pp64__helper=pp48_bias__thr=0p12__width=0p34__s=0p52 | helper_specific_probability_routing | 0.270608 | 0.807343 | -0.000787 | -0.000787 | 1.000000 | 0.508333 | -0.001600 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp48__prob=tail85_only__thr=0p18__width=0p32__s=0p46 | classifier_tail_routing | 0.270641 | 0.807458 | -0.000754 | -0.000672 | 1.000000 | 0.516667 | -0.001599 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=pp48__prob=tail85_only__thr=0p18__width=0p32__s=0p46 | classifier_tail_routing | 0.270644 | 0.807463 | -0.000751 | -0.000667 | 1.000000 | 0.516667 | -0.001599 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp48__prob=tail85_only__thr=0p1__width=0p32__s=0p3 | classifier_tail_routing | 0.270627 | 0.807459 | -0.000768 | -0.000671 | 1.000000 | 0.512500 | -0.001592 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=pp48__prob=tail85_only__thr=0p1__width=0p32__s=0p3 | classifier_tail_routing | 0.270629 | 0.807465 | -0.000766 | -0.000665 | 1.000000 | 0.512500 | -0.001592 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=stable_median__prob=tail85_only__thr=0p1__width=0p18__s=0p64 | classifier_tail_routing | 0.270742 | 0.807133 | -0.000652 | -0.000997 | 1.000000 | 0.554167 | -0.001589 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=stable_median__prob=tail85_only__thr=0p1__width=0p18__s=0p64 | classifier_tail_routing | 0.270744 | 0.807136 | -0.000651 | -0.000994 | 1.000000 | 0.554167 | -0.001589 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=p95_weighted__prob=tail85_only__thr=0p18__width=0p18__s=0p64 | classifier_tail_routing | 0.270702 | 0.807077 | -0.000692 | -0.001053 | 1.000000 | 0.541667 | -0.001586 |

## p95 상위 후보
| item_id | candidate | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REFERENCE | previous_challenger_pp20 | reference_prior | 0.271182 | 0.806472 | -0.000213 | -0.001658 | 1.000000 | 0.554167 | -0.000883 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp20__prob=tail85_only__thr=0p26__width=0p18__s=0p64 | classifier_tail_routing | 0.270651 | 0.806840 | -0.000744 | -0.001290 | 1.000000 | 0.550000 | -0.001412 |
| PP-OPT82 | ppopt82_p95_tail_routing_challenger__source=ppopt77_clf_tail__anchor_pp70__helper_pp20__prob_tail85_only__thr_0p26__width_0p18__s_0p64 | tail_routing_p95_selection | 0.270651 | 0.806840 | -0.000744 | -0.001290 | 1.000000 | 0.550000 | -0.001412 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp20__prob=tail85_only__thr=0p18__width=0p18__s=0p64 | classifier_tail_routing | 0.270729 | 0.806840 | -0.000666 | -0.001290 | 1.000000 | 0.550000 | -0.001488 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp20__prob=tail85_only__thr=0p1__width=0p32__s=0p64 | classifier_tail_routing | 0.270736 | 0.806840 | -0.000659 | -0.001290 | 1.000000 | 0.554167 | -0.001479 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp20__prob=tail85_only__thr=0p1__width=0p18__s=0p64 | classifier_tail_routing | 0.270805 | 0.806840 | -0.000590 | -0.001290 | 1.000000 | 0.554167 | -0.001470 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=pp20__prob=tail85_only__thr=0p26__width=0p18__s=0p64 | classifier_tail_routing | 0.270654 | 0.806843 | -0.000741 | -0.001287 | 1.000000 | 0.550000 | -0.001412 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=pp20__prob=tail85_only__thr=0p18__width=0p18__s=0p64 | classifier_tail_routing | 0.270731 | 0.806843 | -0.000664 | -0.001287 | 1.000000 | 0.550000 | -0.001488 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=pp20__prob=tail85_only__thr=0p1__width=0p32__s=0p64 | classifier_tail_routing | 0.270738 | 0.806843 | -0.000657 | -0.001287 | 1.000000 | 0.554167 | -0.001479 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=pp20__prob=tail85_only__thr=0p1__width=0p18__s=0p64 | classifier_tail_routing | 0.270807 | 0.806843 | -0.000588 | -0.001287 | 1.000000 | 0.554167 | -0.001470 |
| REFERENCE | reference_pp30_best | reference_prior | 0.270872 | 0.806932 | -0.000523 | -0.001198 | 1.000000 | 0.550000 | -0.001396 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp20__prob=tail85_only__thr=0p18__width=0p32__s=0p64 | classifier_tail_routing | 0.270675 | 0.806950 | -0.000720 | -0.001180 | 1.000000 | 0.550000 | -0.001442 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=pp20__prob=tail85_only__thr=0p18__width=0p32__s=0p64 | classifier_tail_routing | 0.270678 | 0.806954 | -0.000717 | -0.001176 | 1.000000 | 0.550000 | -0.001442 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp20__prob=tail85_only__thr=0p1__width=0p46__s=0p64 | classifier_tail_routing | 0.270695 | 0.806994 | -0.000700 | -0.001136 | 1.000000 | 0.545833 | -0.001434 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=pp20__prob=tail85_only__thr=0p1__width=0p46__s=0p64 | classifier_tail_routing | 0.270697 | 0.806998 | -0.000698 | -0.001132 | 1.000000 | 0.545833 | -0.001434 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp20__prob=tail85_only__thr=0p26__width=0p18__s=0p46 | classifier_tail_routing | 0.270626 | 0.807023 | -0.000769 | -0.001107 | 1.000000 | 0.512500 | -0.001336 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp20__prob=tail85_only__thr=0p18__width=0p18__s=0p46 | classifier_tail_routing | 0.270681 | 0.807023 | -0.000714 | -0.001107 | 1.000000 | 0.512500 | -0.001403 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp20__prob=tail85_only__thr=0p1__width=0p32__s=0p46 | classifier_tail_routing | 0.270686 | 0.807023 | -0.000708 | -0.001107 | 1.000000 | 0.516667 | -0.001398 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp20__prob=tail85_only__thr=0p1__width=0p18__s=0p46 | classifier_tail_routing | 0.270736 | 0.807023 | -0.000658 | -0.001107 | 1.000000 | 0.516667 | -0.001407 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=pp20__prob=tail85_only__thr=0p26__width=0p18__s=0p46 | classifier_tail_routing | 0.270628 | 0.807028 | -0.000766 | -0.001102 | 1.000000 | 0.512500 | -0.001336 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=pp20__prob=tail85_only__thr=0p18__width=0p18__s=0p46 | classifier_tail_routing | 0.270684 | 0.807028 | -0.000711 | -0.001102 | 1.000000 | 0.512500 | -0.001403 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=pp20__prob=tail85_only__thr=0p1__width=0p32__s=0p46 | classifier_tail_routing | 0.270689 | 0.807028 | -0.000706 | -0.001102 | 1.000000 | 0.516667 | -0.001398 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=pp20__prob=tail85_only__thr=0p1__width=0p18__s=0p46 | classifier_tail_routing | 0.270738 | 0.807028 | -0.000657 | -0.001102 | 1.000000 | 0.516667 | -0.001407 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=p95_weighted__prob=tail85_only__thr=0p26__width=0p18__s=0p64 | classifier_tail_routing | 0.270650 | 0.807074 | -0.000745 | -0.001056 | 1.000000 | 0.541667 | -0.001504 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=p95_weighted__prob=tail85_only__thr=0p18__width=0p18__s=0p64 | classifier_tail_routing | 0.270700 | 0.807074 | -0.000695 | -0.001056 | 1.000000 | 0.541667 | -0.001586 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=p95_weighted__prob=tail85_only__thr=0p1__width=0p32__s=0p64 | classifier_tail_routing | 0.270704 | 0.807074 | -0.000690 | -0.001056 | 1.000000 | 0.541667 | -0.001574 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=p95_weighted__prob=tail85_only__thr=0p1__width=0p18__s=0p64 | classifier_tail_routing | 0.270749 | 0.807074 | -0.000646 | -0.001056 | 1.000000 | 0.541667 | -0.001613 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=p95_weighted__prob=tail85_only__thr=0p26__width=0p18__s=0p64 | classifier_tail_routing | 0.270652 | 0.807077 | -0.000743 | -0.001053 | 1.000000 | 0.541667 | -0.001503 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=p95_weighted__prob=tail85_only__thr=0p18__width=0p18__s=0p64 | classifier_tail_routing | 0.270702 | 0.807077 | -0.000692 | -0.001053 | 1.000000 | 0.541667 | -0.001586 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=p95_weighted__prob=tail85_only__thr=0p1__width=0p32__s=0p64 | classifier_tail_routing | 0.270706 | 0.807077 | -0.000688 | -0.001053 | 1.000000 | 0.541667 | -0.001574 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=p95_weighted__prob=tail85_only__thr=0p1__width=0p18__s=0p64 | classifier_tail_routing | 0.270750 | 0.807077 | -0.000645 | -0.001053 | 1.000000 | 0.541667 | -0.001613 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp20__prob=tail85_only__thr=0p18__width=0p46__s=0p64 | classifier_tail_routing | 0.270645 | 0.807098 | -0.000750 | -0.001032 | 1.000000 | 0.512500 | -0.001349 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp20__prob=tail85_only__thr=0p26__width=0p32__s=0p64 | classifier_tail_routing | 0.270627 | 0.807099 | -0.000768 | -0.001031 | 1.000000 | 0.545833 | -0.001371 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp20__prob=tail85_only__thr=0p18__width=0p32__s=0p46 | classifier_tail_routing | 0.270643 | 0.807102 | -0.000752 | -0.001028 | 1.000000 | 0.512500 | -0.001367 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=pp20__prob=tail85_only__thr=0p18__width=0p46__s=0p64 | classifier_tail_routing | 0.270647 | 0.807103 | -0.000747 | -0.001027 | 1.000000 | 0.541667 | -0.001407 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=pp20__prob=tail85_only__thr=0p26__width=0p32__s=0p64 | classifier_tail_routing | 0.270630 | 0.807104 | -0.000765 | -0.001026 | 1.000000 | 0.545833 | -0.001370 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=pp20__prob=tail85_only__thr=0p18__width=0p32__s=0p46 | classifier_tail_routing | 0.270645 | 0.807107 | -0.000749 | -0.001023 | 1.000000 | 0.512500 | -0.001367 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=stable_median__prob=tail85_only__thr=0p26__width=0p18__s=0p64 | classifier_tail_routing | 0.270668 | 0.807133 | -0.000726 | -0.000997 | 1.000000 | 0.545833 | -0.001448 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=stable_median__prob=tail85_only__thr=0p1__width=0p32__s=0p64 | classifier_tail_routing | 0.270710 | 0.807133 | -0.000685 | -0.000997 | 1.000000 | 0.554167 | -0.001547 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=stable_median__prob=tail85_only__thr=0p18__width=0p18__s=0p64 | classifier_tail_routing | 0.270711 | 0.807133 | -0.000684 | -0.000997 | 1.000000 | 0.545833 | -0.001539 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=stable_median__prob=tail85_only__thr=0p1__width=0p18__s=0p64 | classifier_tail_routing | 0.270742 | 0.807133 | -0.000652 | -0.000997 | 1.000000 | 0.554167 | -0.001589 |
| PP-OPT78 | ppopt78_helper_prob__anchor=pp70__helper=p95_bias__thr=0p12__width=0p2__s=0p52 | helper_specific_probability_routing | 0.270701 | 0.807133 | -0.000693 | -0.000997 | 1.000000 | 0.508333 | -0.001422 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp20__prob=tail85_only__thr=0p1__width=0p46__s=0p46 | classifier_tail_routing | 0.270657 | 0.807134 | -0.000738 | -0.000996 | 1.000000 | 0.512500 | -0.001370 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=stable_median__prob=tail85_only__thr=0p26__width=0p18__s=0p64 | classifier_tail_routing | 0.270671 | 0.807136 | -0.000724 | -0.000994 | 1.000000 | 0.545833 | -0.001447 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp64__helper=stable_median__prob=tail85_only__thr=0p1__width=0p32__s=0p64 | classifier_tail_routing | 0.270712 | 0.807136 | -0.000683 | -0.000994 | 1.000000 | 0.554167 | -0.001547 |

## MAPE 상위 후보
| item_id | candidate | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-OPT80 | ppopt80_hard_tail__anchor=pp70__helper=pp20__score=p95_prob__thr=0p62__width=0p24__s=1p0 | p95_first_hard_tail_fallback | 0.270557 | 0.807450 | -0.000838 | -0.000680 | 1.000000 | 0.508333 | -0.001289 |
| PP-OPT82 | ppopt82_operational_tail_routing_challenger__source=ppopt80_hard_tail__anchor_pp70__helper_pp20__score_p95_prob__thr_0p62__width_0p24__s_1p0 | tail_routing_operational_selection | 0.270557 | 0.807450 | -0.000838 | -0.000680 | 1.000000 | 0.508333 | -0.001289 |
| PP-OPT80 | ppopt80_hard_tail__anchor=pp70__helper=pp20__score=p95_prob__thr=0p62__width=0p14__s=1p0 | p95_first_hard_tail_fallback | 0.270557 | 0.807422 | -0.000838 | -0.000708 | 1.000000 | 0.508333 | -0.001280 |
| PP-OPT80 | ppopt80_hard_tail__anchor=pp70__helper=pp20__score=p95_prob__thr=0p62__width=0p24__s=0p88 | p95_first_hard_tail_fallback | 0.270557 | 0.807455 | -0.000838 | -0.000675 | 1.000000 | 0.508333 | -0.001293 |
| PP-OPT80 | ppopt80_hard_tail__anchor=pp70__helper=pp20__score=p95_prob__thr=0p62__width=0p14__s=0p88 | p95_first_hard_tail_fallback | 0.270557 | 0.807430 | -0.000837 | -0.000700 | 1.000000 | 0.508333 | -0.001285 |
| PP-OPT80 | ppopt80_hard_tail__anchor=pp70__helper=pp20__score=p95_prob__thr=0p62__width=0p24__s=0p72 | p95_first_hard_tail_fallback | 0.270558 | 0.807461 | -0.000837 | -0.000669 | 1.000000 | 0.508333 | -0.001299 |
| PP-OPT80 | ppopt80_hard_tail__anchor=pp70__helper=pp20__score=p95_prob__thr=0p62__width=0p14__s=0p72 | p95_first_hard_tail_fallback | 0.270558 | 0.807441 | -0.000837 | -0.000689 | 1.000000 | 0.508333 | -0.001292 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp48__prob=stable_better_tail85__thr=0p1__width=0p18__s=0p64 | classifier_tail_routing | 0.270558 | 0.807495 | -0.000837 | -0.000635 | 1.000000 | 0.537500 | -0.001391 |
| PP-OPT80 | ppopt80_hard_tail__anchor=pp70__helper=pp20__score=p95_prob__thr=0p62__width=0p24__s=0p55 | p95_first_hard_tail_fallback | 0.270559 | 0.807468 | -0.000836 | -0.000662 | 1.000000 | 0.508333 | -0.001305 |
| PP-OPT80 | ppopt80_hard_tail__anchor=pp70__helper=pp20__score=p95_prob__thr=0p78__width=0p14__s=1p0 | p95_first_hard_tail_fallback | 0.270559 | 0.807490 | -0.000836 | -0.000640 | 1.000000 | 0.508333 | -0.001314 |
| PP-OPT80 | ppopt80_hard_tail__anchor=pp70__helper=pp20__score=p95_prob__thr=0p62__width=0p14__s=0p55 | p95_first_hard_tail_fallback | 0.270559 | 0.807453 | -0.000836 | -0.000677 | 1.000000 | 0.508333 | -0.001300 |
| PP-OPT80 | ppopt80_hard_tail__anchor=pp70__helper=pp20__score=p95_prob__thr=0p78__width=0p14__s=0p88 | p95_first_hard_tail_fallback | 0.270559 | 0.807490 | -0.000836 | -0.000640 | 1.000000 | 0.508333 | -0.001315 |
| PP-OPT81 | ppopt81_tail_ensemble__anchor=pp70__helper=pp48_p95_mix__thr=0p48__width=0p22__s=0p56 | tail_routing_ensemble | 0.270559 | 0.807490 | -0.000836 | -0.000640 | 1.000000 | 0.508333 | -0.001326 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp48__prob=stable_better_tail85__thr=0p1__width=0p18__s=0p46 | classifier_tail_routing | 0.270559 | 0.807493 | -0.000836 | -0.000637 | 1.000000 | 0.508333 | -0.001330 |
| PP-OPT80 | ppopt80_hard_tail__anchor=pp70__helper=pp20__score=p95_prob__thr=0p78__width=0p14__s=0p72 | p95_first_hard_tail_fallback | 0.270559 | 0.807490 | -0.000836 | -0.000640 | 1.000000 | 0.508333 | -0.001317 |
| PP-OPT81 | ppopt81_tail_ensemble__anchor=pp70__helper=prob_weighted__thr=0p48__width=0p22__s=0p56 | tail_routing_ensemble | 0.270559 | 0.807490 | -0.000836 | -0.000640 | 1.000000 | 0.508333 | -0.001325 |
| PP-OPT81 | ppopt81_tail_ensemble__anchor=pp70__helper=pp48_p95_mix__thr=0p48__width=0p22__s=0p4 | tail_routing_ensemble | 0.270559 | 0.807490 | -0.000835 | -0.000640 | 1.000000 | 0.508333 | -0.001326 |
| PP-OPT80 | ppopt80_hard_tail__anchor=pp70__helper=pp20__score=p95_prob__thr=0p78__width=0p24__s=1p0 | p95_first_hard_tail_fallback | 0.270560 | 0.807490 | -0.000835 | -0.000640 | 1.000000 | 0.508333 | -0.001319 |
| PP-OPT81 | ppopt81_tail_ensemble__anchor=pp70__helper=pp48_p95_mix__thr=0p48__width=0p34__s=0p56 | tail_routing_ensemble | 0.270560 | 0.807490 | -0.000835 | -0.000640 | 1.000000 | 0.508333 | -0.001326 |
| PP-OPT81 | ppopt81_tail_ensemble__anchor=pp70__helper=pp48_p95_mix__thr=0p58__width=0p22__s=0p56 | tail_routing_ensemble | 0.270560 | 0.807490 | -0.000835 | -0.000640 | 1.000000 | 0.508333 | -0.001325 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp48__prob=stable_better_tail85__thr=0p1__width=0p18__s=0p3 | classifier_tail_routing | 0.270560 | 0.807492 | -0.000835 | -0.000638 | 1.000000 | 0.508333 | -0.001328 |
| PP-OPT80 | ppopt80_hard_tail__anchor=pp70__helper=pp20__score=p95_prob__thr=0p78__width=0p14__s=0p55 | p95_first_hard_tail_fallback | 0.270560 | 0.807490 | -0.000835 | -0.000640 | 1.000000 | 0.508333 | -0.001319 |
| PP-OPT80 | ppopt80_hard_tail__anchor=pp64__helper=pp20__score=p95_prob__thr=0p62__width=0p24__s=1p0 | p95_first_hard_tail_fallback | 0.270560 | 0.807458 | -0.000835 | -0.000672 | 1.000000 | 0.508333 | -0.001288 |
| PP-OPT80 | ppopt80_hard_tail__anchor=pp70__helper=pp20__score=p95_prob__thr=0p78__width=0p24__s=0p88 | p95_first_hard_tail_fallback | 0.270560 | 0.807490 | -0.000835 | -0.000640 | 1.000000 | 0.508333 | -0.001319 |
| PP-OPT81 | ppopt81_tail_ensemble__anchor=pp70__helper=prob_weighted__thr=0p48__width=0p22__s=0p4 | tail_routing_ensemble | 0.270560 | 0.807490 | -0.000835 | -0.000640 | 1.000000 | 0.508333 | -0.001325 |
| PP-OPT81 | ppopt81_tail_ensemble__anchor=pp70__helper=prob_weighted__thr=0p38__width=0p34__s=0p56 | tail_routing_ensemble | 0.270560 | 0.807490 | -0.000835 | -0.000640 | 1.000000 | 0.508333 | -0.001323 |
| PP-OPT80 | ppopt80_hard_tail__anchor=pp70__helper=p95_weighted__score=p95_prob__thr=0p78__width=0p14__s=1p0 | p95_first_hard_tail_fallback | 0.270560 | 0.807490 | -0.000835 | -0.000640 | 1.000000 | 0.508333 | -0.001320 |
| PP-OPT81 | ppopt81_tail_ensemble__anchor=pp70__helper=prob_weighted__thr=0p48__width=0p34__s=0p56 | tail_routing_ensemble | 0.270560 | 0.807490 | -0.000835 | -0.000640 | 1.000000 | 0.508333 | -0.001325 |
| PP-OPT81 | ppopt81_tail_ensemble__anchor=pp70__helper=prob_p95_mix__thr=0p48__width=0p22__s=0p56 | tail_routing_ensemble | 0.270560 | 0.807490 | -0.000835 | -0.000640 | 1.000000 | 0.508333 | -0.001325 |
| PP-OPT80 | ppopt80_hard_tail__anchor=pp70__helper=pp20__score=p95_prob__thr=0p78__width=0p24__s=0p72 | p95_first_hard_tail_fallback | 0.270560 | 0.807490 | -0.000835 | -0.000640 | 1.000000 | 0.508333 | -0.001320 |
| PP-OPT81 | ppopt81_tail_ensemble__anchor=pp70__helper=pp48_p95_mix__thr=0p48__width=0p46__s=0p56 | tail_routing_ensemble | 0.270560 | 0.807490 | -0.000835 | -0.000640 | 1.000000 | 0.508333 | -0.001325 |
| PP-OPT81 | ppopt81_tail_ensemble__anchor=pp70__helper=pp48_p95_mix__thr=0p48__width=0p34__s=0p4 | tail_routing_ensemble | 0.270560 | 0.807490 | -0.000835 | -0.000640 | 1.000000 | 0.508333 | -0.001325 |
| PP-OPT81 | ppopt81_tail_ensemble__anchor=pp70__helper=pp48_p95_mix__thr=0p58__width=0p22__s=0p4 | tail_routing_ensemble | 0.270560 | 0.807490 | -0.000835 | -0.000640 | 1.000000 | 0.508333 | -0.001325 |
| PP-OPT81 | ppopt81_tail_ensemble__anchor=pp70__helper=pp48_p95_mix__thr=0p48__width=0p22__s=0p26 | tail_routing_ensemble | 0.270560 | 0.807490 | -0.000835 | -0.000640 | 1.000000 | 0.508333 | -0.001325 |
| PP-OPT80 | ppopt80_hard_tail__anchor=pp70__helper=p95_weighted__score=p95_prob__thr=0p78__width=0p14__s=0p88 | p95_first_hard_tail_fallback | 0.270560 | 0.807490 | -0.000835 | -0.000640 | 1.000000 | 0.508333 | -0.001321 |
| PP-OPT81 | ppopt81_tail_ensemble__anchor=pp70__helper=prob_weighted__thr=0p58__width=0p22__s=0p56 | tail_routing_ensemble | 0.270560 | 0.807490 | -0.000835 | -0.000640 | 1.000000 | 0.508333 | -0.001325 |
| PP-OPT80 | ppopt80_hard_tail__anchor=pp64__helper=pp20__score=p95_prob__thr=0p62__width=0p14__s=1p0 | p95_first_hard_tail_fallback | 0.270560 | 0.807429 | -0.000835 | -0.000701 | 1.000000 | 0.508333 | -0.001279 |
| PP-OPT81 | ppopt81_tail_ensemble__anchor=pp70__helper=prob_weighted__thr=0p38__width=0p22__s=0p56 | tail_routing_ensemble | 0.270560 | 0.807491 | -0.000835 | -0.000639 | 1.000000 | 0.508333 | -0.001321 |
| PP-OPT81 | ppopt81_tail_ensemble__anchor=pp70__helper=pp48_p95_mix__thr=0p58__width=0p34__s=0p56 | tail_routing_ensemble | 0.270560 | 0.807490 | -0.000835 | -0.000640 | 1.000000 | 0.508333 | -0.001325 |
| PP-OPT76 | ppopt76_det_tail__anchor=pp70__helper=pp20__score=risk__thr=0p74__width=0p18__s=0p58 | deterministic_tail_score_routing | 0.270560 | 0.807490 | -0.000835 | -0.000640 | 1.000000 | 0.508333 | -0.001324 |
| PP-OPT81 | ppopt81_tail_ensemble__anchor=pp70__helper=prob_weighted__thr=0p38__width=0p46__s=0p56 | tail_routing_ensemble | 0.270560 | 0.807490 | -0.000835 | -0.000640 | 1.000000 | 0.508333 | -0.001323 |
| PP-OPT77 | ppopt77_clf_tail__anchor=pp70__helper=pp48__prob=stable_better_tail85__thr=0p1__width=0p18__s=0p18 | classifier_tail_routing | 0.270560 | 0.807491 | -0.000835 | -0.000639 | 1.000000 | 0.508333 | -0.001327 |
| PP-OPT80 | ppopt80_hard_tail__anchor=pp64__helper=pp20__score=p95_prob__thr=0p62__width=0p24__s=0p88 | p95_first_hard_tail_fallback | 0.270560 | 0.807463 | -0.000835 | -0.000667 | 1.000000 | 0.508333 | -0.001293 |
| PP-OPT81 | ppopt81_tail_ensemble__anchor=pp70__helper=prob_weighted__thr=0p38__width=0p34__s=0p4 | tail_routing_ensemble | 0.270560 | 0.807490 | -0.000835 | -0.000640 | 1.000000 | 0.508333 | -0.001323 |
| PP-OPT81 | ppopt81_tail_ensemble__anchor=pp70__helper=prob_weighted__thr=0p48__width=0p46__s=0p56 | tail_routing_ensemble | 0.270560 | 0.807490 | -0.000835 | -0.000640 | 1.000000 | 0.508333 | -0.001325 |

## 해석
- p95를 크게 낮추는 후보는 PP20/PP48로 강하게 이동할수록 나오지만, MAPE와 MdAPE 손실이 빠르게 커진다.
- 운영형으로는 PP64 대비 p95 개선이 의미 있게 나오면서 MAPE 손실이 제한적인 후보만 비교해야 한다.
- p95 목적형 후보는 운영 기본값이 아니라 tail 안정성 우선 옵션으로 해석한다.

## 실행 설정
```json
{
  "experiment_id": "PP-OPT76-82",
  "experiment_slug": "PP-OPT76_82_warm_tail_routing_experiments",
  "created_at": "2026-06-09T13:50:07",
  "seed": 20260609,
  "base_candidate": "hcoef_stable",
  "incumbent_candidate": "incumbent_operational_pp_opt7",
  "previous_challenger": "previous_challenger_pp20",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 4228,
  "prediction_rows": 4760728,
  "selected_references": {
    "pp20": "previous_challenger_pp20",
    "pp30": "reference_pp30_best",
    "pp45": "reference_pp45_challenger",
    "pp48": "reference_pp48_score",
    "pp52": "reference_pp52_challenger",
    "pp58": "reference_pp58_challenger",
    "pp64": "reference_pp64_current_best",
    "pp70": "ppopt70_pp64_refinement_challenger__source=ppopt68_shrinkage__global_1p04__risk_0p7__vh_0p82__lowconf_0p78"
  },
  "selection_decision": {
    "reference_pp64_test_MAPE": 0.27056404191566036,
    "reference_pp64_test_p95_APE": 0.8074988523061098,
    "reference_pp70_test_MAPE": 0.2705609753769763,
    "reference_pp70_test_p95_APE": 0.8074900608978479,
    "operational_source_candidate": "ppopt80_hard_tail__anchor=pp70__helper=pp20__score=p95_prob__thr=0p62__width=0p24__s=1p0",
    "operational_source_item_id": "PP-OPT80",
    "operational_source_family": "p95_first_hard_tail_fallback",
    "operational_test_MAPE": 0.2705565870369285,
    "operational_test_p95_APE": 0.807450308348755,
    "operational_delta_vs_pp64_MAPE": -7.454878731882886e-06,
    "operational_delta_vs_pp64_p95_APE": -4.8543957354874046e-05,
    "p95_source_candidate": "ppopt77_clf_tail__anchor=pp70__helper=pp20__prob=tail85_only__thr=0p26__width=0p18__s=0p64",
    "p95_source_item_id": "PP-OPT77",
    "p95_source_family": "classifier_tail_routing",
    "p95_test_MAPE": 0.2706512801714569,
    "p95_test_p95_APE": 0.8068395739408173,
    "p95_delta_vs_pp64_MAPE": 8.72382557965401e-05,
    "p95_delta_vs_pp64_p95_APE": -0.0006592783652925593,
    "selection_reason": "operational candidate prioritizes p95 improvement within small MAPE loss; p95 candidate allows slightly more MAPE for tail reduction",
    "operational_protocol_candidate": "ppopt82_operational_tail_routing_challenger__source=ppopt80_hard_tail__anchor_pp70__helper_pp20__score_p95_prob__thr_0p62__width_0p24__s_1p0",
    "p95_protocol_candidate": "ppopt82_p95_tail_routing_challenger__source=ppopt77_clf_tail__anchor_pp70__helper_pp20__prob_tail85_only__thr_0p26__width_0p18__s_0p64"
  },
  "items": [
    {
      "item_id": "PP-OPT76",
      "priority": "1",
      "title": "deterministic tail-risk score routing",
      "description": "퀀타일 폭, 모델 간 spread, 저신뢰, 고가 구간으로 tail 위험도를 만들고 위험 row만 안정 후보로 이동한다."
    },
    {
      "item_id": "PP-OPT77",
      "priority": "2",
      "title": "validation-trained tail classifier routing",
      "description": "validation OOF에서 안정 후보가 PP64보다 좋아지는 tail row를 학습해 routing 확률로 사용한다."
    },
    {
      "item_id": "PP-OPT78",
      "priority": "3",
      "title": "helper-specific better-probability routing",
      "description": "PP20, PP30, PP48이 각각 PP64보다 나아지는 확률을 따로 학습해 helper를 가중 평균한다."
    },
    {
      "item_id": "PP-OPT79",
      "priority": "4",
      "title": "quantile-direction aligned tail routing",
      "description": "잔차 quantile 방향과 안정 후보 이동 방향이 맞는 row에서만 tail routing을 허용한다."
    },
    {
      "item_id": "PP-OPT80",
      "priority": "5",
      "title": "p95-first hard tail fallback",
      "description": "p95를 직접 낮추기 위해 매우 높은 위험 row에서 더 강한 fallback을 적용한다."
    },
    {
      "item_id": "PP-OPT81",
      "priority": "6",
      "title": "tail routing ensemble",
      "description": "deterministic risk, classifier probability, helper-specific probability를 함께 써서 routing 강도를 정한다."
    },
    {
      "item_id": "PP-OPT82",
      "priority": "7",
      "title": "최종 tail-routing challenger 선택",
      "description": "운영형 후보와 p95 목적형 후보를 분리해 최종 판단한다."
    }
  ],
  "sources": {
    "pp65_config": "experiments/track6/PP-OPT65_70_warm_pp64_refinement_experiments/artifacts/run_config.json",
    "pp65_predictions": "experiments/track6/PP-OPT65_70_warm_pp64_refinement_experiments/outputs/candidate_predictions.csv",
    "pp47_quantile": "experiments/track6/PP-OPT47_52_warm_residual_finetune_experiments/artifacts/quantile_residual_predictions.csv",
    "pp65_helper": "scripts/track6/run_pp_opt65_70_warm_pp64_refinement_experiments.py"
  }
}
```