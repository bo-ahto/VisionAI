# PP-OPT59~64 Warm p95 guard 실험 결과

- 작성일: 2026-06-09 12:40
- 데이터 기준: 제출용 제외, Warm validation OOF 519건 + fixed test 607건
- 기준 후보: PP-OPT7 운영 후보
- 비교 후보: PP20, PP23, PP30, PP38, PP45, PP52, PP58
- 전체 후보 수: 1215
- 운영 대체 통과 후보 수: 1213

## 최종 선택 후보
- 선택 후보: `ppopt64_p95_guard_challenger__source=ppopt62_segment_threshold__helper_pp48_score__base_0p36__vh_0p08__lowconf_0p06__s_0p85`
- 원본 후보: `ppopt62_segment_threshold__helper=pp48_score__base=0p36__vh=0p08__lowconf=0p06__s=0p85`
- 판단: PP64 선택 후보는 PP58 대비 MAPE -0.000008, p95 -0.000312이다.
| eval_split | n | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | 607 | 0.137878 | 0.270564 | 0.807499 | 0.397991 | 0.782537 | 0.883031 | -0.000831 | -0.000631 |
| validation_oof | 519 | 0.122635 | 0.206281 | 0.637922 | 0.323780 | 0.782274 | 0.911368 | -0.000742 | 0.001327 |

## 주요 reference test 비교
| candidate | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- |
| ppopt64_p95_guard_challenger__source=ppopt62_segment_threshold__helper_pp48_score__base_0p36__vh_0p08__lowconf_0p06__s_0p85 | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |
| reference_pp58_challenger | 0.137878 | 0.270572 | 0.807811 | 0.397997 | -0.000823 | -0.000319 |
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
| 3 | rollback classifier probability calibration | 360 | 0.270640 | 0.807386 | -0.000755 | -0.000744 | 1.000000 | 0.504167 | True | True | calibrated_rollback_probability | ppopt61_calibrated_rollback__prob=geomean__helper=pp48_score__thr=0p08__width=0p34__s=0p9 |
| 2 | PP58 tail-risk guard | 128 | 0.270612 | 0.807848 | -0.000783 | -0.000282 | 1.000000 | 0.537500 | True | True | pp58_tail_risk_guard | ppopt60_tail_guard__helper=pp48_score__score=risk__thr=0p42__s=0p45 |
| 5 | MAPE 후보와 안정 후보 2단계 router | 192 | 0.270601 | 0.807644 | -0.000794 | -0.000486 | 1.000000 | 0.541667 | True | True | two_stage_mape_stability_router | ppopt63_two_stage_router__safe=pp48score_pp30__thr=0p36__max=0p4__sharp=0p75 |
| 4 | segment별 rollback threshold | 324 | 0.270591 | 0.807476 | -0.000804 | -0.000654 | 1.000000 | 0.512500 | True | True | segment_rollback_threshold | ppopt62_segment_threshold__helper=pp48_score__base=0p28__vh=0p0__lowconf=m0p06__s=0p85 |
| 1 | PP58 rollback threshold/strength fine grid | 200 | 0.270578 | 0.807432 | -0.000816 | -0.000698 | 1.000000 | 0.512500 | True | True | fine_classifier_rollback | ppopt59_fine_classifier__helper=pp48_score__thr=0p36__width=0p32__s=0p82 |
| 6 | 최종 p95 guard challenger 선택 | 1 | 0.270564 | 0.807499 | -0.000831 | -0.000631 | 1.000000 | 0.508333 | True | True | p95_guard_selection_protocol | ppopt64_p95_guard_challenger__source=ppopt62_segment_threshold__helper_pp48_score__base_0p36__vh_0p08__lowconf_0p06__s_0p85 |

## 운영 대체 통과 후보 상위
| item_id | candidate | family | test_MdAPE | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | incumbent_all3_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REFERENCE | reference_pp48_score | reference_prior | 0.136800 | 0.270816 | 0.807385 | -0.000579 | -0.000745 | 1.000000 | 0.900000 | 0.779167 | -0.002413 |
| REFERENCE | reference_pp38_best | reference_prior | 0.137053 | 0.270836 | 0.807102 | -0.000559 | -0.001028 | 1.000000 | 0.541667 | 0.479167 | -0.001713 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=geomean__helper=pp48_score__thr=0p08__width=0p34__s=0p9 | calibrated_rollback_probability | 0.136961 | 0.270640 | 0.807386 | -0.000755 | -0.000744 | 1.000000 | 0.504167 | 0.429167 | -0.001678 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=geomean__helper=pp48_score__thr=0p08__width=0p34__s=0p75 | calibrated_rollback_probability | 0.137114 | 0.270632 | 0.807432 | -0.000763 | -0.000698 | 1.000000 | 0.508333 | 0.437500 | -0.001638 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=geomean__helper=pp48_score__thr=0p08__width=0p46__s=0p9 | calibrated_rollback_probability | 0.137200 | 0.270623 | 0.807448 | -0.000772 | -0.000682 | 1.000000 | 0.508333 | 0.433333 | -0.001591 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=calibrated__helper=pp48_score__thr=0p08__width=0p34__s=0p9 | calibrated_rollback_probability | 0.137301 | 0.270626 | 0.807479 | -0.000769 | -0.000651 | 1.000000 | 0.512500 | 0.445833 | -0.001585 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=geomean__helper=pp48_score__thr=0p12__width=0p34__s=0p9 | calibrated_rollback_probability | 0.137261 | 0.270617 | 0.807403 | -0.000778 | -0.000727 | 1.000000 | 0.508333 | 0.429167 | -0.001583 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=geomean__helper=pp48_score__thr=0p08__width=0p34__s=0p55 | calibrated_rollback_probability | 0.137318 | 0.270623 | 0.807493 | -0.000772 | -0.000637 | 1.000000 | 0.508333 | 0.441667 | -0.001570 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=geomean__helper=pp48_score__thr=0p08__width=0p46__s=0p75 | calibrated_rollback_probability | 0.137313 | 0.270618 | 0.807484 | -0.000777 | -0.000646 | 1.000000 | 0.508333 | 0.441667 | -0.001567 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=calibrated__helper=pp48_score__thr=0p08__width=0p34__s=0p75 | calibrated_rollback_probability | 0.137397 | 0.270621 | 0.807509 | -0.000774 | -0.000621 | 1.000000 | 0.512500 | 0.450000 | -0.001557 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=geomean__helper=pp48_score__thr=0p08__width=0p58__s=0p9 | calibrated_rollback_probability | 0.137341 | 0.270617 | 0.807492 | -0.000778 | -0.000638 | 1.000000 | 0.508333 | 0.441667 | -0.001557 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=geomean__helper=pp48_mape__thr=0p08__width=0p34__s=0p9 | calibrated_rollback_probability | 0.137412 | 0.270591 | 0.807992 | -0.000803 | -0.000138 | 1.000000 | 0.504167 | 0.462500 | -0.001556 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=geomean__helper=pp48_score__thr=0p12__width=0p34__s=0p75 | calibrated_rollback_probability | 0.137364 | 0.270613 | 0.807446 | -0.000782 | -0.000684 | 1.000000 | 0.508333 | 0.433333 | -0.001550 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=geomean__helper=pp48_score__thr=0p12__width=0p46__s=0p9 | calibrated_rollback_probability | 0.137422 | 0.270610 | 0.807470 | -0.000785 | -0.000660 | 1.000000 | 0.508333 | 0.437500 | -0.001532 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=calibrated__helper=pp48_score__thr=0p08__width=0p46__s=0p9 | calibrated_rollback_probability | 0.137451 | 0.270618 | 0.807527 | -0.000776 | -0.000603 | 1.000000 | 0.512500 | 0.441667 | -0.001521 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=geomean__helper=pp48_mape__thr=0p08__width=0p34__s=0p75 | calibrated_rollback_probability | 0.137489 | 0.270592 | 0.807936 | -0.000803 | -0.000194 | 1.000000 | 0.500000 | 0.454167 | -0.001514 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=geomean__helper=pp48_score__thr=0p08__width=0p58__s=0p75 | calibrated_rollback_probability | 0.137430 | 0.270614 | 0.807520 | -0.000781 | -0.000610 | 1.000000 | 0.508333 | 0.433333 | -0.001508 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=geomean__helper=pp48_score__thr=0p08__width=0p46__s=0p55 | calibrated_rollback_probability | 0.137464 | 0.270613 | 0.807531 | -0.000782 | -0.000599 | 1.000000 | 0.512500 | 0.437500 | -0.001504 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=geomean__helper=pp48_score__thr=0p12__width=0p34__s=0p55 | calibrated_rollback_probability | 0.137501 | 0.270609 | 0.807503 | -0.000786 | -0.000627 | 1.000000 | 0.512500 | 0.437500 | -0.001503 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=geomean__helper=pp48_score__thr=0p12__width=0p46__s=0p75 | calibrated_rollback_probability | 0.137498 | 0.270608 | 0.807502 | -0.000787 | -0.000628 | 1.000000 | 0.512500 | 0.437500 | -0.001502 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=geomean__helper=pp48_mape__thr=0p12__width=0p34__s=0p9 | calibrated_rollback_probability | 0.137564 | 0.270586 | 0.807966 | -0.000809 | -0.000164 | 1.000000 | 0.500000 | 0.454167 | -0.001496 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=geomean__helper=pp48_score__thr=0p12__width=0p58__s=0p9 | calibrated_rollback_probability | 0.137516 | 0.270607 | 0.807509 | -0.000788 | -0.000621 | 1.000000 | 0.512500 | 0.437500 | -0.001495 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=geomean__helper=pp48_mape__thr=0p08__width=0p46__s=0p9 | calibrated_rollback_probability | 0.137533 | 0.270587 | 0.807915 | -0.000808 | -0.000215 | 1.000000 | 0.500000 | 0.454167 | -0.001495 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=calibrated__helper=pp48_score__thr=0p12__width=0p34__s=0p9 | calibrated_rollback_probability | 0.137600 | 0.270606 | 0.807508 | -0.000789 | -0.000622 | 1.000000 | 0.512500 | 0.441667 | -0.001487 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=geomean__helper=pp48_score__thr=0p08__width=0p34__s=0p35 | calibrated_rollback_probability | 0.137522 | 0.270613 | 0.807554 | -0.000782 | -0.000576 | 1.000000 | 0.508333 | 0.437500 | -0.001486 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=calibrated__helper=pp48_score__thr=0p08__width=0p46__s=0p75 | calibrated_rollback_probability | 0.137523 | 0.270615 | 0.807549 | -0.000780 | -0.000581 | 1.000000 | 0.508333 | 0.437500 | -0.001486 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=calibrated__helper=pp48_score__thr=0p08__width=0p34__s=0p55 | calibrated_rollback_probability | 0.137525 | 0.270615 | 0.807550 | -0.000780 | -0.000580 | 1.000000 | 0.508333 | 0.437500 | -0.001485 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=geomean__helper=pp48_mape__thr=0p08__width=0p34__s=0p55 | calibrated_rollback_probability | 0.137593 | 0.270593 | 0.807863 | -0.000801 | -0.000267 | 1.000000 | 0.504167 | 0.454167 | -0.001480 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=calibrated__helper=pp48_score__thr=0p08__width=0p58__s=0p9 | calibrated_rollback_probability | 0.137540 | 0.270614 | 0.807554 | -0.000781 | -0.000576 | 1.000000 | 0.508333 | 0.437500 | -0.001479 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=geomean__helper=pp48_mape__thr=0p12__width=0p34__s=0p75 | calibrated_rollback_probability | 0.137617 | 0.270588 | 0.807915 | -0.000807 | -0.000215 | 1.000000 | 0.500000 | 0.454167 | -0.001478 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=geomean__helper=pp48_mape__thr=0p08__width=0p46__s=0p75 | calibrated_rollback_probability | 0.137591 | 0.270588 | 0.807872 | -0.000806 | -0.000258 | 1.000000 | 0.504167 | 0.454167 | -0.001477 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=calibrated__helper=pp48_mape__thr=0p08__width=0p34__s=0p9 | calibrated_rollback_probability | 0.137584 | 0.270595 | 0.807874 | -0.000800 | -0.000256 | 1.000000 | 0.504167 | 0.450000 | -0.001476 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=geomean__helper=pp48_score__thr=0p08__width=0p58__s=0p55 | calibrated_rollback_probability | 0.137550 | 0.270609 | 0.807557 | -0.000785 | -0.000573 | 1.000000 | 0.508333 | 0.437500 | -0.001473 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=geomean__helper=pp48_mape__thr=0p08__width=0p58__s=0p9 | calibrated_rollback_probability | 0.137605 | 0.270589 | 0.807862 | -0.000806 | -0.000268 | 1.000000 | 0.504167 | 0.454167 | -0.001472 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=geomean__helper=pp48_score__thr=0p12__width=0p58__s=0p75 | calibrated_rollback_probability | 0.137577 | 0.270605 | 0.807534 | -0.000790 | -0.000596 | 1.000000 | 0.508333 | 0.433333 | -0.001463 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=geomean__helper=pp48_score__thr=0p12__width=0p46__s=0p55 | calibrated_rollback_probability | 0.137600 | 0.270605 | 0.807544 | -0.000790 | -0.000586 | 1.000000 | 0.508333 | 0.437500 | -0.001462 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=calibrated__helper=pp48_score__thr=0p08__width=0p58__s=0p75 | calibrated_rollback_probability | 0.137596 | 0.270612 | 0.807572 | -0.000783 | -0.000558 | 1.000000 | 0.508333 | 0.437500 | -0.001458 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=calibrated__helper=pp48_score__thr=0p12__width=0p34__s=0p75 | calibrated_rollback_probability | 0.137647 | 0.270605 | 0.807534 | -0.000790 | -0.000596 | 1.000000 | 0.508333 | 0.437500 | -0.001457 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=geomean__helper=pp48_mape__thr=0p12__width=0p46__s=0p9 | calibrated_rollback_probability | 0.137646 | 0.270587 | 0.807886 | -0.000807 | -0.000244 | 1.000000 | 0.504167 | 0.450000 | -0.001457 |
| PP-OPT61 | ppopt61_calibrated_rollback__prob=calibrated__helper=pp48_mape__thr=0p08__width=0p34__s=0p75 | calibrated_rollback_probability | 0.137633 | 0.270595 | 0.807838 | -0.000800 | -0.000292 | 1.000000 | 0.504167 | 0.445833 | -0.001451 |

## 전체 MAPE 상위 후보
| item_id | candidate | family | test_MdAPE | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | incumbent_all3_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-OPT62 | ppopt62_segment_threshold__helper=pp48_mape__base=0p36__vh=0p08__lowconf=0p06__s=0p85 | segment_rollback_threshold | 0.137878 | 0.270563 | 0.807834 | -0.000832 | -0.000296 | 1.000000 | 0.504167 | 0.420833 | -0.001332 |
| PP-OPT59 | ppopt59_fine_classifier__helper=pp48_mape__thr=0p44__width=0p32__s=0p9 | fine_classifier_rollback | 0.137878 | 0.270564 | 0.807860 | -0.000831 | -0.000270 | 1.000000 | 0.508333 | 0.420833 | -0.001321 |
| PP-OPT62 | ppopt62_segment_threshold__helper=pp48_score__base=0p36__vh=0p08__lowconf=0p06__s=0p85 | segment_rollback_threshold | 0.137878 | 0.270564 | 0.807499 | -0.000831 | -0.000631 | 1.000000 | 0.508333 | 0.412500 | -0.001324 |
| PP-OPT64 | ppopt64_p95_guard_challenger__source=ppopt62_segment_threshold__helper_pp48_score__base_0p36__vh_0p08__lowconf_0p06__s_0p85 | p95_guard_selection_protocol | 0.137878 | 0.270564 | 0.807499 | -0.000831 | -0.000631 | 1.000000 | 0.508333 | 0.412500 | -0.001324 |
| PP-OPT59 | ppopt59_fine_classifier__helper=pp48_mape__thr=0p4__width=0p32__s=0p9 | fine_classifier_rollback | 0.137878 | 0.270565 | 0.807901 | -0.000830 | -0.000229 | 1.000000 | 0.508333 | 0.420833 | -0.001332 |
| PP-OPT59 | ppopt59_fine_classifier__helper=pp48_mape__thr=0p48__width=0p32__s=0p9 | fine_classifier_rollback | 0.137878 | 0.270565 | 0.807818 | -0.000829 | -0.000312 | 1.000000 | 0.512500 | 0.420833 | -0.001310 |
| PP-OPT62 | ppopt62_segment_threshold__helper=pp48_mape__base=0p36__vh=0p08__lowconf=0p0__s=0p85 | segment_rollback_threshold | 0.137878 | 0.270565 | 0.807832 | -0.000829 | -0.000298 | 1.000000 | 0.504167 | 0.420833 | -0.001330 |
| PP-OPT62 | ppopt62_segment_threshold__helper=pp48_mape__base=0p36__vh=0p0__lowconf=0p06__s=0p85 | segment_rollback_threshold | 0.137878 | 0.270565 | 0.807834 | -0.000829 | -0.000296 | 1.000000 | 0.504167 | 0.416667 | -0.001325 |
| PP-OPT59 | ppopt59_fine_classifier__helper=pp48_mape__thr=0p36__width=0p4__s=0p9 | fine_classifier_rollback | 0.137878 | 0.270566 | 0.807886 | -0.000829 | -0.000244 | 1.000000 | 0.504167 | 0.420833 | -0.001331 |
| PP-OPT62 | ppopt62_segment_threshold__helper=pp48_score__base=0p36__vh=0p0__lowconf=0p06__s=0p85 | segment_rollback_threshold | 0.137878 | 0.270566 | 0.807499 | -0.000829 | -0.000631 | 1.000000 | 0.508333 | 0.408333 | -0.001322 |
| PP-OPT59 | ppopt59_fine_classifier__helper=pp48_mape__thr=0p4__width=0p4__s=0p9 | fine_classifier_rollback | 0.137878 | 0.270567 | 0.807853 | -0.000828 | -0.000277 | 1.000000 | 0.508333 | 0.416667 | -0.001317 |
| PP-OPT59 | ppopt59_fine_classifier__helper=pp48_mape__thr=0p44__width=0p32__s=0p82 | fine_classifier_rollback | 0.137878 | 0.270567 | 0.807842 | -0.000828 | -0.000288 | 1.000000 | 0.508333 | 0.420833 | -0.001321 |
| PP-OPT62 | ppopt62_segment_threshold__helper=pp48_score__base=0p36__vh=0p08__lowconf=0p0__s=0p85 | segment_rollback_threshold | 0.137878 | 0.270567 | 0.807510 | -0.000827 | -0.000620 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT59 | ppopt59_fine_classifier__helper=pp48_score__thr=0p44__width=0p32__s=0p9 | fine_classifier_rollback | 0.137878 | 0.270568 | 0.807472 | -0.000827 | -0.000658 | 1.000000 | 0.508333 | 0.408333 | -0.001304 |
| PP-OPT59 | ppopt59_fine_classifier__helper=pp48_mape__thr=0p4__width=0p32__s=0p82 | fine_classifier_rollback | 0.137878 | 0.270568 | 0.807880 | -0.000827 | -0.000250 | 1.000000 | 0.508333 | 0.416667 | -0.001323 |
| PP-OPT59 | ppopt59_fine_classifier__helper=pp48_mape__thr=0p52__width=0p32__s=0p9 | fine_classifier_rollback | 0.137878 | 0.270568 | 0.807776 | -0.000827 | -0.000354 | 1.000000 | 0.520833 | 0.420833 | -0.001301 |
| PP-OPT62 | ppopt62_segment_threshold__helper=pp48_mape__base=0p36__vh=0p0__lowconf=0p0__s=0p85 | segment_rollback_threshold | 0.137878 | 0.270568 | 0.807832 | -0.000827 | -0.000298 | 1.000000 | 0.504167 | 0.416667 | -0.001322 |
| PP-OPT62 | ppopt62_segment_threshold__helper=pp48_mape__base=0p36__vh=m0p08__lowconf=0p06__s=0p85 | segment_rollback_threshold | 0.137878 | 0.270568 | 0.807834 | -0.000827 | -0.000296 | 1.000000 | 0.504167 | 0.416667 | -0.001325 |
| PP-OPT59 | ppopt59_fine_classifier__helper=pp48_mape__thr=0p48__width=0p32__s=0p82 | fine_classifier_rollback | 0.137878 | 0.270568 | 0.807804 | -0.000827 | -0.000326 | 1.000000 | 0.512500 | 0.412500 | -0.001294 |
| PP-OPT59 | ppopt59_fine_classifier__helper=pp48_mape__thr=0p36__width=0p4__s=0p82 | fine_classifier_rollback | 0.137878 | 0.270568 | 0.807865 | -0.000826 | -0.000265 | 1.000000 | 0.504167 | 0.416667 | -0.001322 |
| PP-OPT62 | ppopt62_segment_threshold__helper=pp48_mape__base=0p36__vh=0p08__lowconf=m0p06__s=0p85 | segment_rollback_threshold | 0.137878 | 0.270568 | 0.807830 | -0.000826 | -0.000300 | 1.000000 | 0.504167 | 0.416667 | -0.001318 |
| PP-OPT59 | ppopt59_fine_classifier__helper=pp48_score__thr=0p4__width=0p32__s=0p9 | fine_classifier_rollback | 0.137878 | 0.270569 | 0.807441 | -0.000826 | -0.000689 | 1.000000 | 0.508333 | 0.412500 | -0.001334 |
| PP-OPT62 | ppopt62_segment_threshold__helper=pp48_score__base=0p44__vh=0p08__lowconf=0p06__s=0p85 | segment_rollback_threshold | 0.137878 | 0.270569 | 0.807551 | -0.000826 | -0.000579 | 1.000000 | 0.508333 | 0.408333 | -0.001291 |
| PP-OPT62 | ppopt62_segment_threshold__helper=pp48_score__base=0p36__vh=0p0__lowconf=0p0__s=0p85 | segment_rollback_threshold | 0.137878 | 0.270569 | 0.807510 | -0.000826 | -0.000620 | 1.000000 | 0.508333 | 0.408333 | -0.001322 |
| PP-OPT62 | ppopt62_segment_threshold__helper=pp48_mape__base=0p44__vh=0p08__lowconf=0p06__s=0p85 | segment_rollback_threshold | 0.137878 | 0.270569 | 0.807774 | -0.000825 | -0.000356 | 1.000000 | 0.508333 | 0.416667 | -0.001310 |
| PP-OPT59 | ppopt59_fine_classifier__helper=pp48_mape__thr=0p4__width=0p4__s=0p82 | fine_classifier_rollback | 0.137878 | 0.270570 | 0.807836 | -0.000825 | -0.000294 | 1.000000 | 0.508333 | 0.416667 | -0.001316 |
| PP-OPT59 | ppopt59_fine_classifier__helper=pp48_score__thr=0p4__width=0p4__s=0p9 | fine_classifier_rollback | 0.137878 | 0.270570 | 0.807485 | -0.000825 | -0.000645 | 1.000000 | 0.508333 | 0.404167 | -0.001304 |
| PP-OPT62 | ppopt62_segment_threshold__helper=pp48_score__base=0p36__vh=m0p08__lowconf=0p06__s=0p85 | segment_rollback_threshold | 0.137878 | 0.270570 | 0.807499 | -0.000825 | -0.000631 | 1.000000 | 0.512500 | 0.412500 | -0.001334 |
| PP-OPT59 | ppopt59_fine_classifier__helper=pp48_score__thr=0p48__width=0p32__s=0p9 | fine_classifier_rollback | 0.137878 | 0.270570 | 0.807508 | -0.000825 | -0.000622 | 1.000000 | 0.508333 | 0.408333 | -0.001288 |
| PP-OPT59 | ppopt59_fine_classifier__helper=pp48_mape__thr=0p44__width=0p32__s=0p74 | fine_classifier_rollback | 0.137878 | 0.270570 | 0.807825 | -0.000825 | -0.000305 | 1.000000 | 0.508333 | 0.420833 | -0.001321 |
| PP-OPT62 | ppopt62_segment_threshold__helper=pp48_mape__base=0p28__vh=0p08__lowconf=0p06__s=0p85 | segment_rollback_threshold | 0.137878 | 0.270570 | 0.807893 | -0.000825 | -0.000237 | 1.000000 | 0.504167 | 0.420833 | -0.001341 |
| PP-OPT59 | ppopt59_fine_classifier__helper=pp48_mape__thr=0p44__width=0p4__s=0p9 | fine_classifier_rollback | 0.137878 | 0.270570 | 0.807820 | -0.000825 | -0.000310 | 1.000000 | 0.508333 | 0.420833 | -0.001317 |
| PP-OPT62 | ppopt62_segment_threshold__helper=pp48_mape__base=0p44__vh=0p08__lowconf=0p0__s=0p85 | segment_rollback_threshold | 0.137878 | 0.270570 | 0.807773 | -0.000825 | -0.000357 | 1.000000 | 0.508333 | 0.416667 | -0.001308 |
| PP-OPT59 | ppopt59_fine_classifier__helper=pp48_score__thr=0p44__width=0p32__s=0p82 | fine_classifier_rollback | 0.137878 | 0.270570 | 0.807489 | -0.000825 | -0.000641 | 1.000000 | 0.508333 | 0.408333 | -0.001304 |
| PP-OPT62 | ppopt62_segment_threshold__helper=pp48_score__base=0p36__vh=0p08__lowconf=m0p06__s=0p85 | segment_rollback_threshold | 0.137878 | 0.270570 | 0.807520 | -0.000825 | -0.000610 | 1.000000 | 0.508333 | 0.408333 | -0.001317 |
| PP-OPT59 | ppopt59_fine_classifier__helper=pp48_mape__thr=0p36__width=0p48__s=0p9 | fine_classifier_rollback | 0.137878 | 0.270570 | 0.807848 | -0.000824 | -0.000282 | 1.000000 | 0.504167 | 0.416667 | -0.001318 |
| PP-OPT59 | ppopt59_fine_classifier__helper=pp48_mape__thr=0p36__width=0p32__s=0p9 | fine_classifier_rollback | 0.137878 | 0.270570 | 0.807942 | -0.000824 | -0.000188 | 1.000000 | 0.504167 | 0.420833 | -0.001341 |
| PP-OPT59 | ppopt59_fine_classifier__helper=pp48_mape__thr=0p52__width=0p32__s=0p82 | fine_classifier_rollback | 0.137878 | 0.270571 | 0.807765 | -0.000824 | -0.000365 | 1.000000 | 0.520833 | 0.420833 | -0.001303 |
| PP-OPT59 | ppopt59_fine_classifier__helper=pp48_mape__thr=0p4__width=0p32__s=0p74 | fine_classifier_rollback | 0.137878 | 0.270571 | 0.807858 | -0.000824 | -0.000272 | 1.000000 | 0.508333 | 0.416667 | -0.001322 |
| PP-OPT62 | ppopt62_segment_threshold__helper=pp48_score__base=0p44__vh=0p0__lowconf=0p06__s=0p85 | segment_rollback_threshold | 0.137878 | 0.270571 | 0.807551 | -0.000824 | -0.000579 | 1.000000 | 0.508333 | 0.408333 | -0.001293 |

## 해석
이번 배치는 PP58의 MAPE 이득을 유지하면서 p95를 회복하는 실험이다. 선택 후보가 PP58보다 MAPE를 거의 유지하고 p95를 낮추면 운영 후보로 더 균형적이다.

## 실행 설정
```json
{
  "experiment_id": "PP-OPT59-64",
  "experiment_slug": "PP-OPT59_64_warm_p95_guard_experiments",
  "created_at": "2026-06-09T12:40:13",
  "seed": 20260609,
  "base_candidate": "hcoef_stable",
  "incumbent_candidate": "incumbent_operational_pp_opt7",
  "previous_challenger": "previous_challenger_pp20",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 1216,
  "prediction_rows": 1369216,
  "items": [
    {
      "item_id": "PP-OPT59",
      "priority": "1",
      "title": "PP58 rollback threshold/strength fine grid",
      "description": "PP58 근처의 classifier rollback threshold, width, strength를 더 촘촘히 탐색한다."
    },
    {
      "item_id": "PP-OPT60",
      "priority": "2",
      "title": "PP58 tail-risk guard",
      "description": "tail risk가 높은 row에서 PP58을 PP52/PP48/PP20 쪽으로 되돌린다."
    },
    {
      "item_id": "PP-OPT61",
      "priority": "3",
      "title": "rollback classifier probability calibration",
      "description": "rollback 확률을 OOF bin calibration한 뒤 classifier rollback을 다시 적용한다."
    },
    {
      "item_id": "PP-OPT62",
      "priority": "4",
      "title": "segment별 rollback threshold",
      "description": "가격대/신뢰도/불확실성 구간별로 rollback threshold를 조정한다."
    },
    {
      "item_id": "PP-OPT63",
      "priority": "5",
      "title": "MAPE 후보와 안정 후보 2단계 router",
      "description": "먼저 PP52/PP58 계열을 고르고, tail 위험 row만 안정 후보로 override한다."
    },
    {
      "item_id": "PP-OPT64",
      "priority": "6",
      "title": "최종 p95 guard challenger 선택",
      "description": "PP58 대비 p95 회복과 MAPE 유지 조건을 함께 고려해 최종 후보를 선택한다."
    }
  ],
  "selected_references": {
    "pp20": "previous_challenger_pp20",
    "pp23": "reference_pp23",
    "pp30": "reference_pp30_best",
    "pp38": "reference_pp38_best",
    "pp45": "reference_pp45_challenger",
    "pp48_score": "reference_pp48_score",
    "pp52": "reference_pp52_challenger",
    "pp58": "ppopt58_rollback_router_challenger__source=ppopt54_classifier_rollback__helper_pp48_mape__thr_0p44__width_0p4__rel_none__s_0p85",
    "pp48_mape": "ppopt48_segment_micro__center=pp45__group=price_conf__shrink=160p0__guard=medium__s=0p32__cap=0p008"
  },
  "selection_decision": {
    "selected_source_candidate": "ppopt62_segment_threshold__helper=pp48_score__base=0p36__vh=0p08__lowconf=0p06__s=0p85",
    "selected_source_item_id": "PP-OPT62",
    "selected_source_family": "segment_rollback_threshold",
    "selection_reason": "prefer PP58 p95 recovery while preserving PP58 MAPE within 0.000015; fallback to PP52 MAPE improvement with p95 safe",
    "test_MdAPE": 0.13787846966744394,
    "test_MAPE": 0.2705640419156603,
    "test_p95_APE": 0.8074988523061101,
    "test_delta_vs_incumbent_MdAPE": 0.000985903768827734,
    "test_delta_vs_incumbent_MAPE": -0.000830846096406157,
    "test_delta_vs_incumbent_p95_APE": -0.0006311304073586266,
    "recommendation_score_vs_incumbent": -0.0013242489630431898,
    "protocol_candidate": "ppopt64_p95_guard_challenger__source=ppopt62_segment_threshold__helper_pp48_score__base_0p36__vh_0p08__lowconf_0p06__s_0p85"
  },
  "sources": {
    "pp_opt53_config": "PP-OPT53_58_warm_rollback_router_experiments",
    "pp_opt53_predictions": "experiments/track6/PP-OPT53_58_warm_rollback_router_experiments/outputs/candidate_predictions.csv",
    "pp_opt53_aggregate": "experiments/track6/PP-OPT53_58_warm_rollback_router_experiments/outputs/aggregate_candidate_stability.csv",
    "pp_opt53_rollback": "experiments/track6/PP-OPT53_58_warm_rollback_router_experiments/artifacts/rollback_probability_detail.csv",
    "pp_opt47_quantile": "experiments/track6/PP-OPT47_52_warm_residual_finetune_experiments/artifacts/quantile_residual_predictions.csv",
    "pp_opt53_helper": "scripts/track6/run_pp_opt53_58_warm_rollback_router_experiments.py"
  }
}
```