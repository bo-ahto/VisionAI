# PP-OPT96~102 Warm tail label refinement 실험 결과

- 작성일: 2026-06-09 14:14
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 목적: tail risk 자체가 아니라 fallback helper가 실제로 더 좋은 row를 학습
- 결론: PP102 운영형은 PP64/PP70 교체 후보로 승격 가능. 운영형 fixed test는 PP64 대비 MAPE -0.000009, p95 -0.000009.

## 주요 후보 test 비교
| candidate | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- |
| ppopt102_operational_label_refined_tail_challenger__source=ppopt96_best_gain__helper_prob_weighted_tail80__prob_best_gain_tail75__thr_0p32__width_0p18__s_0p46 | 0.137878 | 0.270555 | 0.807490 | 0.397983 | -0.000840 | -0.000640 |
| reference_pp82_operational | 0.137878 | 0.270557 | 0.807450 | 0.397982 | -0.000838 | -0.000680 |
| reference_pp81_best | 0.137878 | 0.270559 | 0.807490 | 0.397989 | -0.000836 | -0.000640 |
| reference_pp95_operational | 0.137878 | 0.270559 | 0.807490 | 0.397989 | -0.000836 | -0.000640 |
| reference_pp70_refinement | 0.137878 | 0.270561 | 0.807490 | 0.397991 | -0.000834 | -0.000640 |
| reference_pp64_current_best | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |
| ppopt102_p95_label_refined_tail_challenger__source=ppopt96_best_gain__helper_pp20__prob_best_gain_any__thr_0p08__width_0p18__s_0p64 | 0.137211 | 0.270927 | 0.806859 | 0.398056 | -0.000468 | -0.001271 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | p95_test_MAPE | p95_test_p95_APE | operational_pass_vs_incumbent | best_family | best_candidate | p95_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | best-helper gain label routing | 1200 | 0.270654 | 0.807084 | 0.270927 | 0.806859 | True | best_helper_gain_label_routing | ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p32__width=0p18__s=0p64 | ppopt96_best_gain__helper=pp20__prob=best_gain_any__thr=0p08__width=0p18__s=0p64 |
| 3 | gain minus harm guarded routing | 576 | 0.270562 | 0.807505 | 0.270585 | 0.807482 | True | gain_minus_harm_guarded_routing | ppopt98_gain_harm__helper=prob_weighted_tail80__gain=best_gain_tail85__hpen=0p9__thr=0p05__s=0p42 | ppopt98_gain_harm__helper=p95_weighted__gain=best_gain_tail85__hpen=0p35__thr=0p05__s=0p58 |
| 4 | tail quantile label routing | 240 | 0.270615 | 0.807450 | 0.270638 | 0.807433 | True | tail_quantile_label_routing | ppopt99_tail_quantile__prob=best_gain_tail85__thr=0p04__width=0p24__s=0p72 | ppopt99_tail_quantile__prob=best_gain_tail85__thr=0p04__width=0p14__s=0p72 |
| 7 | final label-refined tail challenger | 2 | 0.270555 | 0.807490 | 0.270927 | 0.806859 | True | label_refined_operational_selection | ppopt102_operational_label_refined_tail_challenger__source=ppopt96_best_gain__helper_prob_weighted_tail80__prob_best_gain_tail75__thr_0p32__width_0p18__s_0p46 | ppopt102_p95_label_refined_tail_challenger__source=ppopt96_best_gain__helper_pp20__prob_best_gain_any__thr_0p08__width_0p18__s_0p64 |
| 6 | existing candidate selector with refined labels | 288 | 0.270566 | 0.807490 | 0.270568 | 0.807482 | True | existing_candidate_label_selector | ppopt101_selector__safe=pp81__target=p95mode__thr=0p34__hpen=0p9__s=0p42 | ppopt101_selector__safe=pp81__target=p95mode__thr=0p08__hpen=0p45__s=0p42 |
| 2 | helper-specific gain label routing | 240 | 0.270563 | 0.807490 | 0.270560 | 0.807490 | True | helper_specific_gain_label_routing | ppopt97_helper_specific__helper=tail70_weighted__thr=0p3__width=0p16__s=0p52 | ppopt97_helper_specific__helper=tail80_weighted__thr=0p12__width=0p16__s=0p52 |
| 5 | direction and gain aligned routing | 96 | 0.270557 | 0.807490 | 0.270569 | 0.807483 | True | direction_and_gain_aligned_routing | ppopt100_direction_gain__helper=pp20__prob=pp20_gain_tail80__thr=0p1__s=0p66 | ppopt100_direction_gain__helper=pp20__prob=best_gain_tail80__thr=0p04__s=0p66 |

## 운영 통과 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| reference_pp48_score | REFERENCE | reference_prior | 0.270816 | 0.807385 | -0.000579 | -0.000745 | 1.000000 | 0.900000 | -0.002413 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p32__width=0p18__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270654 | 0.807084 | -0.000740 | -0.001046 | 1.000000 | 0.533333 | -0.001617 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p22__width=0p3__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270681 | 0.807084 | -0.000713 | -0.001046 | 1.000000 | 0.533333 | -0.001610 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p08__width=0p44__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270721 | 0.807095 | -0.000674 | -0.001035 | 1.000000 | 0.537500 | -0.001604 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p14__width=0p44__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270687 | 0.807090 | -0.000708 | -0.001040 | 1.000000 | 0.537500 | -0.001603 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p08__width=0p44__s=0p46 | PP-OPT96 | best_helper_gain_label_routing | 0.270676 | 0.807206 | -0.000719 | -0.000924 | 1.000000 | 0.537500 | -0.001596 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p22__width=0p18__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270720 | 0.807084 | -0.000675 | -0.001046 | 1.000000 | 0.533333 | -0.001592 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p08__width=0p3__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270764 | 0.807100 | -0.000631 | -0.001030 | 1.000000 | 0.537500 | -0.001590 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p22__width=0p18__s=0p46 | PP-OPT96 | best_helper_gain_label_routing | 0.270675 | 0.807199 | -0.000720 | -0.000931 | 1.000000 | 0.533333 | -0.001588 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p08__width=0p18__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270798 | 0.807111 | -0.000597 | -0.001019 | 1.000000 | 0.541667 | -0.001588 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p14__width=0p3__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270726 | 0.807092 | -0.000668 | -0.001038 | 1.000000 | 0.537500 | -0.001588 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p08__width=0p3__s=0p46 | PP-OPT96 | best_helper_gain_label_routing | 0.270707 | 0.807210 | -0.000688 | -0.000920 | 1.000000 | 0.537500 | -0.001587 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p14__width=0p18__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270765 | 0.807097 | -0.000630 | -0.001033 | 1.000000 | 0.541667 | -0.001587 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p08__width=0p18__s=0p46 | PP-OPT96 | best_helper_gain_label_routing | 0.270731 | 0.807218 | -0.000664 | -0.000912 | 1.000000 | 0.537500 | -0.001585 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p14__width=0p3__s=0p46 | PP-OPT96 | best_helper_gain_label_routing | 0.270680 | 0.807204 | -0.000715 | -0.000926 | 1.000000 | 0.537500 | -0.001583 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p32__width=0p3__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270623 | 0.807095 | -0.000772 | -0.001035 | 1.000000 | 0.504167 | -0.001578 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p14__width=0p18__s=0p46 | PP-OPT96 | best_helper_gain_label_routing | 0.270707 | 0.807208 | -0.000688 | -0.000922 | 1.000000 | 0.537500 | -0.001576 |
| ppopt96_best_gain__helper=balanced_stable__prob=best_gain_any__thr=0p08__width=0p3__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270755 | 0.807133 | -0.000640 | -0.000997 | 1.000000 | 0.537500 | -0.001572 |
| ppopt96_best_gain__helper=balanced_stable__prob=best_gain_any__thr=0p08__width=0p18__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270786 | 0.807132 | -0.000609 | -0.000998 | 1.000000 | 0.537500 | -0.001564 |
| ppopt96_best_gain__helper=balanced_stable__prob=best_gain_any__thr=0p22__width=0p18__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270715 | 0.807136 | -0.000680 | -0.000994 | 1.000000 | 0.533333 | -0.001563 |
| ppopt96_best_gain__helper=balanced_stable__prob=best_gain_any__thr=0p14__width=0p18__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270758 | 0.807134 | -0.000637 | -0.000996 | 1.000000 | 0.537500 | -0.001562 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p22__width=0p44__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270645 | 0.807128 | -0.000749 | -0.001002 | 1.000000 | 0.504167 | -0.001562 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p44__width=0p18__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270592 | 0.807101 | -0.000803 | -0.001028 | 1.000000 | 0.508333 | -0.001553 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p32__width=0p3__s=0p46 | PP-OPT96 | best_helper_gain_label_routing | 0.270605 | 0.807206 | -0.000790 | -0.000924 | 1.000000 | 0.508333 | -0.001551 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p32__width=0p18__s=0p46 | PP-OPT96 | best_helper_gain_label_routing | 0.270628 | 0.807199 | -0.000767 | -0.000931 | 1.000000 | 0.504167 | -0.001548 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p22__width=0p3__s=0p46 | PP-OPT96 | best_helper_gain_label_routing | 0.270647 | 0.807199 | -0.000747 | -0.000931 | 1.000000 | 0.504167 | -0.001542 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p32__width=0p44__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270605 | 0.807221 | -0.000790 | -0.000909 | 1.000000 | 0.508333 | -0.001542 |
| ppopt96_best_gain__helper=balanced_stable__prob=best_gain_any__thr=0p32__width=0p18__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270650 | 0.807136 | -0.000744 | -0.000994 | 1.000000 | 0.504167 | -0.001528 |
| ppopt96_best_gain__helper=balanced_stable__prob=best_gain_any__thr=0p14__width=0p44__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270682 | 0.807135 | -0.000713 | -0.000995 | 1.000000 | 0.504167 | -0.001527 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p14__width=0p44__s=0p46 | PP-OPT96 | best_helper_gain_label_routing | 0.270651 | 0.807202 | -0.000744 | -0.000928 | 1.000000 | 0.504167 | -0.001527 |
| ppopt96_best_gain__helper=balanced_stable__prob=best_gain_any__thr=0p08__width=0p44__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270714 | 0.807134 | -0.000681 | -0.000996 | 1.000000 | 0.508333 | -0.001526 |
| ppopt96_best_gain__helper=balanced_stable__prob=best_gain_any__thr=0p32__width=0p3__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270621 | 0.807145 | -0.000774 | -0.000985 | 1.000000 | 0.508333 | -0.001525 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p22__width=0p44__s=0p46 | PP-OPT96 | best_helper_gain_label_routing | 0.270622 | 0.807230 | -0.000773 | -0.000900 | 1.000000 | 0.508333 | -0.001524 |
| ppopt96_best_gain__helper=balanced_stable__prob=best_gain_any__thr=0p22__width=0p3__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270677 | 0.807136 | -0.000718 | -0.000994 | 1.000000 | 0.504167 | -0.001523 |
| ppopt96_best_gain__helper=p95_weighted__prob=best_gain_any__thr=0p08__width=0p3__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270779 | 0.807084 | -0.000615 | -0.001046 | 1.000000 | 0.537500 | -0.001518 |
| ppopt96_best_gain__helper=p95_weighted__prob=best_gain_any__thr=0p22__width=0p18__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270738 | 0.807090 | -0.000657 | -0.001040 | 1.000000 | 0.533333 | -0.001511 |
| ppopt96_best_gain__helper=balanced_stable__prob=best_gain_any__thr=0p14__width=0p3__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270721 | 0.807135 | -0.000674 | -0.000995 | 1.000000 | 0.508333 | -0.001509 |
| ppopt96_best_gain__helper=p95_weighted__prob=best_gain_any__thr=0p14__width=0p18__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270784 | 0.807085 | -0.000611 | -0.001045 | 1.000000 | 0.537500 | -0.001508 |
| ppopt96_best_gain__helper=balanced_stable__prob=best_gain_any__thr=0p22__width=0p44__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270643 | 0.807174 | -0.000752 | -0.000956 | 1.000000 | 0.508333 | -0.001505 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p32__width=0p18__s=0p3 | PP-OPT96 | best_helper_gain_label_routing | 0.270605 | 0.807300 | -0.000790 | -0.000830 | 1.000000 | 0.508333 | -0.001502 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p32__width=0p44__s=0p46 | PP-OPT96 | best_helper_gain_label_routing | 0.270593 | 0.807296 | -0.000802 | -0.000834 | 1.000000 | 0.508333 | -0.001502 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p44__width=0p18__s=0p46 | PP-OPT96 | best_helper_gain_label_routing | 0.270583 | 0.807211 | -0.000812 | -0.000919 | 1.000000 | 0.508333 | -0.001501 |
| ppopt96_best_gain__helper=p95_weighted__prob=best_gain_any__thr=0p08__width=0p18__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270811 | 0.807080 | -0.000584 | -0.001050 | 1.000000 | 0.537500 | -0.001500 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p32__width=0p3__s=0p3 | PP-OPT96 | best_helper_gain_label_routing | 0.270590 | 0.807305 | -0.000805 | -0.000825 | 1.000000 | 0.508333 | -0.001499 |
| ppopt96_best_gain__helper=p95_weighted__prob=best_gain_any__thr=0p14__width=0p44__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270699 | 0.807088 | -0.000696 | -0.001042 | 1.000000 | 0.508333 | -0.001490 |
| ppopt96_best_gain__helper=balanced_stable__prob=best_gain_any__thr=0p32__width=0p3__s=0p46 | PP-OPT96 | best_helper_gain_label_routing | 0.270604 | 0.807242 | -0.000791 | -0.000888 | 1.000000 | 0.508333 | -0.001490 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p22__width=0p3__s=0p3 | PP-OPT96 | best_helper_gain_label_routing | 0.270617 | 0.807300 | -0.000778 | -0.000830 | 1.000000 | 0.508333 | -0.001490 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p08__width=0p3__s=0p3 | PP-OPT96 | best_helper_gain_label_routing | 0.270656 | 0.807307 | -0.000739 | -0.000822 | 1.000000 | 0.512500 | -0.001489 |
| ppopt96_best_gain__helper=p95_weighted__prob=best_gain_any__thr=0p32__width=0p3__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270630 | 0.807100 | -0.000765 | -0.001030 | 1.000000 | 0.508333 | -0.001489 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p08__width=0p18__s=0p3 | PP-OPT96 | best_helper_gain_label_routing | 0.270672 | 0.807312 | -0.000723 | -0.000818 | 1.000000 | 0.512500 | -0.001488 |

## p95 상위 후보
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| previous_challenger_pp20 | REFERENCE | reference_prior | 0.271182 | 0.806472 | -0.000213 | -0.001658 | 1.000000 | 0.554167 | -0.000883 |
| reference_pp82_p95 | REFERENCE | reference_prior | 0.270651 | 0.806840 | -0.000744 | -0.001290 | 1.000000 | 0.550000 | -0.001412 |
| reference_pp95_p95 | REFERENCE | reference_prior | 0.270651 | 0.806840 | -0.000744 | -0.001290 | 1.000000 | 0.550000 | -0.001412 |
| ppopt102_p95_label_refined_tail_challenger__source=ppopt96_best_gain__helper_pp20__prob_best_gain_any__thr_0p08__width_0p18__s_0p64 | PP-OPT102 | label_refined_p95_selection | 0.270927 | 0.806859 | -0.000468 | -0.001271 | 1.000000 | 0.554167 | -0.001234 |
| ppopt96_best_gain__helper=pp20__prob=best_gain_any__thr=0p08__width=0p18__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270927 | 0.806859 | -0.000468 | -0.001271 | 1.000000 | 0.554167 | -0.001234 |
| ppopt96_best_gain__helper=pp20__prob=best_gain_any__thr=0p08__width=0p3__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270890 | 0.806873 | -0.000504 | -0.001257 | 1.000000 | 0.554167 | -0.001285 |
| ppopt96_best_gain__helper=pp20__prob=best_gain_any__thr=0p14__width=0p18__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270901 | 0.806877 | -0.000494 | -0.001253 | 1.000000 | 0.545833 | -0.001214 |
| ppopt96_best_gain__helper=pp20__prob=best_gain_any__thr=0p08__width=0p44__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270824 | 0.806880 | -0.000571 | -0.001250 | 1.000000 | 0.508333 | -0.001247 |
| ppopt96_best_gain__helper=pp20__prob=best_gain_any__thr=0p14__width=0p3__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270841 | 0.806884 | -0.000554 | -0.001246 | 1.000000 | 0.537500 | -0.001234 |
| ppopt96_best_gain__helper=pp20__prob=best_gain_any__thr=0p14__width=0p44__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270775 | 0.806887 | -0.000619 | -0.001243 | 1.000000 | 0.504167 | -0.001224 |
| ppopt96_best_gain__helper=pp20__prob=best_gain_any__thr=0p32__width=0p18__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270726 | 0.806894 | -0.000669 | -0.001236 | 1.000000 | 0.508333 | -0.001261 |
| ppopt96_best_gain__helper=pp20__prob=best_gain_any__thr=0p22__width=0p3__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270773 | 0.806894 | -0.000622 | -0.001236 | 1.000000 | 0.508333 | -0.001234 |
| ppopt96_best_gain__helper=pp20__prob=best_gain_any__thr=0p22__width=0p18__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270839 | 0.806894 | -0.000556 | -0.001236 | 1.000000 | 0.541667 | -0.001244 |
| ppopt96_best_gain__helper=pp20__prob=best_gain_any__thr=0p32__width=0p3__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270672 | 0.806909 | -0.000723 | -0.001221 | 1.000000 | 0.508333 | -0.001286 |
| ppopt96_best_gain__helper=pp20__prob=best_gain_any__thr=0p44__width=0p18__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270621 | 0.806919 | -0.000774 | -0.001211 | 1.000000 | 0.508333 | -0.001334 |
| ppopt96_best_gain__helper=pp20__prob=best_gain_any__thr=0p22__width=0p44__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270711 | 0.806958 | -0.000684 | -0.001171 | 1.000000 | 0.508333 | -0.001266 |
| ppopt96_best_gain__helper=pp20__prob=best_gain_any__thr=0p08__width=0p18__s=0p46 | PP-OPT96 | best_helper_gain_label_routing | 0.270823 | 0.807037 | -0.000571 | -0.001093 | 1.000000 | 0.516667 | -0.001276 |
| ppopt96_best_gain__helper=pp20__prob=best_gain_any__thr=0p08__width=0p3__s=0p46 | PP-OPT96 | best_helper_gain_label_routing | 0.270798 | 0.807047 | -0.000597 | -0.001083 | 1.000000 | 0.512500 | -0.001274 |
| ppopt96_best_gain__helper=pp20__prob=best_gain_any__thr=0p14__width=0p18__s=0p46 | PP-OPT96 | best_helper_gain_label_routing | 0.270805 | 0.807050 | -0.000590 | -0.001080 | 1.000000 | 0.512500 | -0.001238 |
| ppopt96_best_gain__helper=pp20__prob=best_gain_any__thr=0p08__width=0p44__s=0p46 | PP-OPT96 | best_helper_gain_label_routing | 0.270750 | 0.807052 | -0.000645 | -0.001078 | 1.000000 | 0.508333 | -0.001301 |
| ppopt96_best_gain__helper=pp20__prob=best_gain_any__thr=0p14__width=0p3__s=0p46 | PP-OPT96 | best_helper_gain_label_routing | 0.270762 | 0.807055 | -0.000633 | -0.001075 | 1.000000 | 0.508333 | -0.001244 |
| ppopt96_best_gain__helper=pp20__prob=best_gain_any__thr=0p14__width=0p44__s=0p46 | PP-OPT96 | best_helper_gain_label_routing | 0.270715 | 0.807057 | -0.000680 | -0.001073 | 1.000000 | 0.508333 | -0.001271 |
| ppopt96_best_gain__helper=pp20__prob=best_gain_any__thr=0p32__width=0p18__s=0p46 | PP-OPT96 | best_helper_gain_label_routing | 0.270679 | 0.807062 | -0.000716 | -0.001068 | 1.000000 | 0.504167 | -0.001296 |
| ppopt96_best_gain__helper=pp20__prob=best_gain_any__thr=0p22__width=0p3__s=0p46 | PP-OPT96 | best_helper_gain_label_routing | 0.270713 | 0.807062 | -0.000682 | -0.001068 | 1.000000 | 0.508333 | -0.001283 |
| ppopt96_best_gain__helper=pp20__prob=best_gain_any__thr=0p22__width=0p18__s=0p46 | PP-OPT96 | best_helper_gain_label_routing | 0.270760 | 0.807062 | -0.000634 | -0.001068 | 1.000000 | 0.508333 | -0.001248 |
| ppopt96_best_gain__helper=pp20__prob=best_gain_any__thr=0p32__width=0p3__s=0p46 | PP-OPT96 | best_helper_gain_label_routing | 0.270641 | 0.807073 | -0.000754 | -0.001057 | 1.000000 | 0.504167 | -0.001309 |
| ppopt96_best_gain__helper=p95_weighted__prob=best_gain_any__thr=0p08__width=0p18__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270811 | 0.807080 | -0.000584 | -0.001050 | 1.000000 | 0.537500 | -0.001500 |
| ppopt96_best_gain__helper=pp20__prob=best_gain_any__thr=0p44__width=0p18__s=0p46 | PP-OPT96 | best_helper_gain_label_routing | 0.270604 | 0.807080 | -0.000791 | -0.001050 | 1.000000 | 0.508333 | -0.001360 |
| ppopt96_best_gain__helper=p95_weighted__prob=best_gain_any__thr=0p08__width=0p3__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270779 | 0.807084 | -0.000615 | -0.001046 | 1.000000 | 0.537500 | -0.001518 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p32__width=0p18__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270654 | 0.807084 | -0.000740 | -0.001046 | 1.000000 | 0.533333 | -0.001617 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p22__width=0p3__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270681 | 0.807084 | -0.000713 | -0.001046 | 1.000000 | 0.533333 | -0.001610 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p22__width=0p18__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270720 | 0.807084 | -0.000675 | -0.001046 | 1.000000 | 0.533333 | -0.001592 |
| ppopt96_best_gain__helper=p95_weighted__prob=best_gain_any__thr=0p14__width=0p18__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270784 | 0.807085 | -0.000611 | -0.001045 | 1.000000 | 0.537500 | -0.001508 |
| ppopt96_best_gain__helper=p95_weighted__prob=best_gain_any__thr=0p08__width=0p44__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270734 | 0.807086 | -0.000661 | -0.001044 | 1.000000 | 0.504167 | -0.001477 |
| ppopt96_best_gain__helper=p95_weighted__prob=best_gain_any__thr=0p14__width=0p3__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270743 | 0.807087 | -0.000652 | -0.001043 | 1.000000 | 0.504167 | -0.001458 |
| ppopt96_best_gain__helper=p95_weighted__prob=best_gain_any__thr=0p14__width=0p44__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270699 | 0.807088 | -0.000696 | -0.001042 | 1.000000 | 0.508333 | -0.001490 |
| ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_any__thr=0p14__width=0p44__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270687 | 0.807090 | -0.000708 | -0.001040 | 1.000000 | 0.537500 | -0.001603 |
| ppopt96_best_gain__helper=p95_weighted__prob=best_gain_any__thr=0p32__width=0p18__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270665 | 0.807090 | -0.000730 | -0.001040 | 1.000000 | 0.504167 | -0.001484 |
| ppopt96_best_gain__helper=p95_weighted__prob=best_gain_any__thr=0p22__width=0p3__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270695 | 0.807090 | -0.000700 | -0.001040 | 1.000000 | 0.504167 | -0.001477 |
| ppopt96_best_gain__helper=p95_weighted__prob=best_gain_any__thr=0p22__width=0p18__s=0p64 | PP-OPT96 | best_helper_gain_label_routing | 0.270738 | 0.807090 | -0.000657 | -0.001040 | 1.000000 | 0.533333 | -0.001511 |

## 반복 안정성 검증
| candidate_label | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_vs_pp64_MAPE | fixed_test_delta_vs_pp64_p95_APE | avg_delta_vs_pp64_MAPE | avg_delta_vs_pp64_p95_APE | avg_pp64_MAPE_win_rate | avg_pp64_p95_win_rate | avg_pp64_all3_win_rate | replacement_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pp81_stable_reference | 0.270559 | 0.807490 | -0.000005 | -0.000009 | -0.000004 | -0.000014 | 0.890705 | 0.410256 | 0.062500 | -0.015633 |
| pp95_operational_reference | 0.270559 | 0.807490 | -0.000005 | -0.000009 | -0.000004 | -0.000014 | 0.890705 | 0.410256 | 0.062500 | -0.015633 |
| pp70_refinement_candidate | 0.270561 | 0.807490 | -0.000003 | -0.000009 | -0.000001 | -0.000001 | 0.786859 | 0.398077 | 0.054167 | -0.011477 |
| pp102_operational_label_refined | 0.270555 | 0.807490 | -0.000009 | -0.000009 | -0.000004 | -0.000017 | 0.614423 | 0.454808 | 0.049359 | -0.004586 |
| pp82_operational_reference | 0.270557 | 0.807450 | -0.000007 | -0.000049 | 0.000018 | 0.000050 | 0.362179 | 0.477244 | 0.037179 | 0.005532 |
| pp82_p95_reference | 0.270651 | 0.806840 | 0.000087 | -0.000659 | 0.000082 | 0.000179 | 0.056090 | 0.603846 | 0.009615 | 0.017948 |
| pp95_p95_reference | 0.270651 | 0.806840 | 0.000087 | -0.000659 | 0.000083 | 0.000178 | 0.055128 | 0.603846 | 0.009615 | 0.017986 |
| pp64_current_best | 0.270564 | 0.807499 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.020000 |
| pp102_p95_label_refined | 0.270927 | 0.806859 | 0.000363 | -0.000640 | 0.000324 | 0.000610 | 0.003846 | 0.461218 | 0.001282 | 0.020584 |
| incumbent_pp7 | 0.271395 | 0.808130 | 0.000831 | 0.000631 | 0.000748 | 0.001946 | 0.002244 | 0.450641 | 0.000641 | 0.022238 |
| hcoef_stable_source | 0.272989 | 0.806366 | 0.002425 | -0.001133 | 0.002013 | 0.005297 | 0.002244 | 0.403526 | 0.000641 | 0.025195 |

## 신규 후보 시나리오별 안정성
| candidate_label | eval_split | scenario | mean_delta_vs_pp64_MAPE | mean_delta_vs_pp64_p95_APE | pp64_MAPE_win_rate | pp64_p95_win_rate | pp64_all3_win_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pp102_operational_label_refined | test | artist_group_holdout | -0.000009 | -0.000004 | 0.973077 | 0.326923 | 0.126923 |
| pp102_operational_label_refined | test | confidence_stratified_rows | -0.000009 | -0.000003 | 0.976923 | 0.442308 | 0.111538 |
| pp102_operational_label_refined | test | full_split | -0.000009 | -0.000009 | 1.000000 | 1.000000 | 0.000000 |
| pp102_operational_label_refined | test | price_band_stratified_rows | -0.000009 | -0.000003 | 0.984615 | 0.376923 | 0.115385 |
| pp102_operational_label_refined | test | risk_focus_bootstrap | -0.000025 | -0.000044 | 0.969231 | 0.223077 | 0.019231 |
| pp102_operational_label_refined | test | row_bootstrap | -0.000009 | -0.000018 | 0.900000 | 0.350000 | 0.069231 |
| pp102_operational_label_refined | validation_oof | artist_group_holdout | 0.000003 | -0.000043 | 0.250000 | 0.480769 | 0.030769 |
| pp102_operational_label_refined | validation_oof | confidence_stratified_rows | 0.000003 | -0.000021 | 0.319231 | 0.384615 | 0.034615 |
| pp102_operational_label_refined | validation_oof | full_split | 0.000003 | -0.000025 | 0.000000 | 1.000000 | 0.000000 |
| pp102_operational_label_refined | validation_oof | price_band_stratified_rows | 0.000002 | -0.000034 | 0.315385 | 0.446154 | 0.046154 |
| pp102_operational_label_refined | validation_oof | risk_focus_bootstrap | 0.000010 | 0.000031 | 0.311538 | 0.046154 | 0.000000 |
| pp102_operational_label_refined | validation_oof | row_bootstrap | 0.000003 | -0.000027 | 0.373077 | 0.380769 | 0.038462 |
| pp102_p95_label_refined | test | artist_group_holdout | 0.000366 | 0.000973 | 0.000000 | 0.492308 | 0.000000 |
| pp102_p95_label_refined | test | confidence_stratified_rows | 0.000362 | 0.000645 | 0.000000 | 0.538462 | 0.000000 |
| pp102_p95_label_refined | test | full_split | 0.000363 | -0.000640 | 0.000000 | 1.000000 | 0.000000 |
| pp102_p95_label_refined | test | price_band_stratified_rows | 0.000362 | 0.000839 | 0.000000 | 0.484615 | 0.000000 |
| pp102_p95_label_refined | test | risk_focus_bootstrap | 0.000220 | 0.001660 | 0.038462 | 0.384615 | 0.011538 |
| pp102_p95_label_refined | test | row_bootstrap | 0.000356 | 0.001574 | 0.007692 | 0.407692 | 0.003846 |
| pp102_p95_label_refined | validation_oof | artist_group_holdout | 0.000318 | 0.000581 | 0.000000 | 0.480769 | 0.000000 |
| pp102_p95_label_refined | validation_oof | confidence_stratified_rows | 0.000320 | 0.000373 | 0.000000 | 0.438462 | 0.000000 |
| pp102_p95_label_refined | validation_oof | full_split | 0.000316 | 0.000279 | 0.000000 | 0.000000 | 0.000000 |
| pp102_p95_label_refined | validation_oof | price_band_stratified_rows | 0.000316 | 0.000391 | 0.000000 | 0.446154 | 0.000000 |
| pp102_p95_label_refined | validation_oof | risk_focus_bootstrap | 0.000268 | 0.000004 | 0.000000 | 0.392308 | 0.000000 |
| pp102_p95_label_refined | validation_oof | row_bootstrap | 0.000325 | 0.000644 | 0.000000 | 0.469231 | 0.000000 |

## 실행 설정
```json
{
  "experiment_id": "PP-OPT96-102",
  "experiment_slug": "PP-OPT96_102_warm_tail_label_refinement_experiments",
  "created_at": "2026-06-09T14:13:21",
  "seed": 20260609,
  "base_candidate": "hcoef_stable",
  "incumbent_candidate": "incumbent_operational_pp_opt7",
  "previous_challenger": "previous_challenger_pp20",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 2654,
  "prediction_rows": 2988404,
  "selected_references": {
    "pp20": "previous_challenger_pp20",
    "pp30": "reference_pp30_best",
    "pp48": "reference_pp48_score",
    "pp64": "reference_pp64_current_best",
    "pp70": "reference_pp70_refinement",
    "pp82_op": "ppopt82_operational_tail_routing_challenger__source=ppopt80_hard_tail__anchor_pp70__helper_pp20__score_p95_prob__thr_0p62__width_0p24__s_1p0",
    "pp82_p95": "ppopt82_p95_tail_routing_challenger__source=ppopt77_clf_tail__anchor_pp70__helper_pp20__prob_tail85_only__thr_0p26__width_0p18__s_0p64",
    "pp81": "ppopt81_tail_ensemble__anchor=pp70__helper=pp48_p95_mix__thr=0p48__width=0p22__s=0p56",
    "pp95_op": "ppopt95_operational_guarded_tail_challenger__source=ppopt93_pp81_tail_boost__target_pp82op__score_risk_prob__thr_0p76__width_0p18__s_0p1",
    "pp95_p95": "ppopt95_p95_guarded_tail_challenger__source=ppopt94_p95_guard__target_pp82op__score_risk_focus__thr_0p7__width_0p32__s_0p2"
  },
  "stability_labels": {
    "hcoef_stable_source": "hcoef_stable",
    "incumbent_pp7": "incumbent_operational_pp_opt7",
    "pp64_current_best": "reference_pp64_current_best",
    "pp70_refinement_candidate": "reference_pp70_refinement",
    "pp81_stable_reference": "reference_pp81_best",
    "pp82_operational_reference": "reference_pp82_operational",
    "pp82_p95_reference": "reference_pp82_p95",
    "pp95_operational_reference": "reference_pp95_operational",
    "pp95_p95_reference": "reference_pp95_p95",
    "pp102_operational_label_refined": "ppopt102_operational_label_refined_tail_challenger__source=ppopt96_best_gain__helper_prob_weighted_tail80__prob_best_gain_tail75__thr_0p32__width_0p18__s_0p46",
    "pp102_p95_label_refined": "ppopt102_p95_label_refined_tail_challenger__source=ppopt96_best_gain__helper_pp20__prob_best_gain_any__thr_0p08__width_0p18__s_0p64"
  },
  "selection_decision": {
    "reference_pp64_test_MAPE": 0.27056404191566036,
    "reference_pp64_test_p95_APE": 0.8074988523061098,
    "reference_pp70_test_MAPE": 0.2705609753769763,
    "reference_pp70_test_p95_APE": 0.8074900608978479,
    "operational_source_candidate": "ppopt96_best_gain__helper=prob_weighted_tail80__prob=best_gain_tail75__thr=0p32__width=0p18__s=0p46",
    "operational_source_item_id": "PP-OPT96",
    "operational_source_family": "best_helper_gain_label_routing",
    "operational_test_MAPE": 0.2705549313821523,
    "operational_test_p95_APE": 0.8074900608978479,
    "operational_delta_vs_pp64_MAPE": -9.110533508049912e-06,
    "operational_delta_vs_pp64_p95_APE": -8.791408261932254e-06,
    "p95_source_candidate": "ppopt96_best_gain__helper=pp20__prob=best_gain_any__thr=0p08__width=0p18__s=0p64",
    "p95_source_item_id": "PP-OPT96",
    "p95_source_family": "best_helper_gain_label_routing",
    "p95_test_MAPE": 0.2709265515851524,
    "p95_test_p95_APE": 0.8068590248527615,
    "p95_delta_vs_pp64_MAPE": 0.00036250966949202823,
    "p95_delta_vs_pp64_p95_APE": -0.0006398274533483406,
    "selection_reason": "select operational candidate only if MAPE and p95 are not worse than PP64; keep p95-focused candidate separately",
    "operational_protocol_candidate": "ppopt102_operational_label_refined_tail_challenger__source=ppopt96_best_gain__helper_prob_weighted_tail80__prob_best_gain_tail75__thr_0p32__width_0p18__s_0p46",
    "p95_protocol_candidate": "ppopt102_p95_label_refined_tail_challenger__source=ppopt96_best_gain__helper_pp20__prob_best_gain_any__thr_0p08__width_0p18__s_0p64"
  },
  "stability_decision": {
    "operational_verdict": "PP102 운영형은 PP64/PP70 교체 후보로 승격 가능",
    "p95_verdict": "PP102 p95형은 tail 안정성 우선 옵션으로 유지",
    "pp102_operational_fixed_test_MAPE": 0.2705549313821523,
    "pp102_operational_fixed_test_p95_APE": 0.8074900608978479,
    "pp102_operational_delta_vs_pp64_MAPE": -9.110533508049912e-06,
    "pp102_operational_delta_vs_pp64_p95_APE": -8.791408261932254e-06,
    "pp102_operational_avg_pp64_MAPE_win_rate": 0.6144230769230768,
    "pp102_operational_avg_pp64_p95_win_rate": 0.4548076923076923,
    "pp102_operational_avg_pp64_all3_win_rate": 0.04935897435897436,
    "pp102_p95_fixed_test_MAPE": 0.2709265515851524,
    "pp102_p95_fixed_test_p95_APE": 0.8068590248527615,
    "pp102_p95_delta_vs_pp64_MAPE": 0.00036250966949202823,
    "pp102_p95_delta_vs_pp64_p95_APE": -0.0006398274533483406,
    "pp102_p95_avg_pp64_MAPE_win_rate": 0.0038461538461538464,
    "pp102_p95_avg_pp64_p95_win_rate": 0.4612179487179487
  },
  "items": [
    {
      "item_id": "PP-OPT96",
      "priority": "1",
      "title": "best-helper gain label routing",
      "description": "best stable helper가 PP70보다 실제로 좋아지는 validation row를 학습해 routing한다."
    },
    {
      "item_id": "PP-OPT97",
      "priority": "2",
      "title": "helper-specific gain label routing",
      "description": "PP20/PP48/혼합 helper별 개선 확률을 따로 학습해 fallback helper를 가중한다."
    },
    {
      "item_id": "PP-OPT98",
      "priority": "3",
      "title": "gain minus harm guarded routing",
      "description": "개선 확률과 손상 확률을 같이 학습해, 손상 위험이 높으면 fallback을 줄인다."
    },
    {
      "item_id": "PP-OPT99",
      "priority": "4",
      "title": "tail quantile label routing",
      "description": "tail 분위수별로 label을 분리해 p95 영역에서만 fallback을 허용한다."
    },
    {
      "item_id": "PP-OPT100",
      "priority": "5",
      "title": "direction and gain aligned routing",
      "description": "잔차 quantile 방향과 helper 이동 방향이 맞고 개선 확률이 있을 때만 routing한다."
    },
    {
      "item_id": "PP-OPT101",
      "priority": "6",
      "title": "existing candidate selector with refined labels",
      "description": "PP70, PP81, PP82, PP95 후보 중 label 기반으로 row별 선택/혼합한다."
    },
    {
      "item_id": "PP-OPT102",
      "priority": "7",
      "title": "final label-refined tail challenger",
      "description": "운영형과 p95 목적형 후보를 분리해 최종 선택하고 안정성을 검증한다."
    }
  ],
  "sources": {
    "pp76_config": "experiments/track6/PP-OPT76_82_warm_tail_routing_experiments/artifacts/run_config.json",
    "pp76_predictions": "experiments/track6/PP-OPT76_82_warm_tail_routing_experiments/outputs/candidate_predictions.csv",
    "pp89_config": "experiments/track6/PP-OPT89_95_warm_tail_guarded_stability_experiments/artifacts/run_config.json",
    "pp89_predictions": "experiments/track6/PP-OPT89_95_warm_tail_guarded_stability_experiments/outputs/candidate_predictions.csv",
    "pp47_quantile": "experiments/track6/PP-OPT47_52_warm_residual_finetune_experiments/artifacts/quantile_residual_predictions.csv",
    "pp76_helper": "scripts/track6/run_pp_opt76_82_warm_tail_routing_experiments.py",
    "pp71_validation_helper": "scripts/track6/run_pp_opt71_75_warm_pp70_stability_validation.py"
  }
}
```