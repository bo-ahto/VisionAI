# PP-OPT47~52 Warm 잔차 fine-tune 실험 결과

- 작성일: 2026-06-09 12:22
- 데이터 기준: 제출용 제외, Warm validation OOF 519건 + fixed test 607건
- 기준 후보: PP-OPT7 운영 후보
- 비교 후보: PP20, PP23, PP30, PP38, PP41, PP45
- 전체 후보 수: 3835
- 운영 대체 통과 후보 수: 1960

## 최종 선택 후보
- 선택 후보: `ppopt52_finetune_challenger__source=ppopt49_quantile_consensus_micro__center_pp45__wlim_0p22__guard_medium__s_0p42__cap_0p01`
- 원본 후보: `ppopt49_quantile_consensus_micro__center=pp45__wlim=0p22__guard=medium__s=0p42__cap=0p01`
- 판단: PP52 선택 후보는 PP45 대비 MAPE -0.000083, p95 +0.000000이다.
| eval_split | n | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | 607 | 0.137878 | 0.270598 | 0.807660 | 0.397987 | 0.782537 | 0.883031 | -0.000797 | -0.000470 |
| validation_oof | 519 | 0.122430 | 0.206301 | 0.638550 | 0.323793 | 0.782274 | 0.911368 | -0.000722 | 0.001955 |

## 주요 reference test 비교
| candidate | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- |
| reference_pp44_safe | 0.139159 | 0.270585 | 0.808127 | 0.398016 | -0.000810 | -0.000003 |
| ppopt52_finetune_challenger__source=ppopt49_quantile_consensus_micro__center_pp45__wlim_0p22__guard_medium__s_0p42__cap_0p01 | 0.137878 | 0.270598 | 0.807660 | 0.397987 | -0.000797 | -0.000470 |
| reference_pp45_challenger | 0.137878 | 0.270682 | 0.807660 | 0.397988 | -0.000713 | -0.000470 |
| reference_pp23 | 0.137878 | 0.270707 | 0.807660 | 0.398002 | -0.000688 | -0.000470 |
| reference_pp43_score | 0.136814 | 0.270715 | 0.808138 | 0.398063 | -0.000680 | 0.000008 |
| reference_pp41_challenger | 0.137845 | 0.270724 | 0.807587 | 0.398003 | -0.000671 | -0.000543 |
| reference_pp46_safe | 0.136703 | 0.270792 | 0.807806 | 0.398180 | -0.000603 | -0.000324 |
| reference_pp38_best | 0.137053 | 0.270836 | 0.807102 | 0.398092 | -0.000559 | -0.001028 |
| reference_pp30_best | 0.137546 | 0.270872 | 0.806932 | 0.398014 | -0.000523 | -0.001198 |
| previous_challenger_pp20 | 0.136835 | 0.271182 | 0.806472 | 0.398134 | -0.000213 | -0.001658 |
| incumbent_operational_pp_opt7 | 0.136893 | 0.271395 | 0.808130 | 0.398341 | 0.000000 | 0.000000 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | stable_validation_pass_vs_incumbent | operational_pass_vs_incumbent | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | p95-safe segment median micro 보정 | 2304 | 0.270816 | 0.807385 | -0.000579 | -0.000745 | 1.000000 | 0.900000 | True | True | p95_safe_segment_micro | ppopt48_segment_micro__center=pp38__group=price_conf__shrink=110p0__guard=medium__s=0p32__cap=0p0045 |
| 5 | PP45와 보정 후보의 p95-aware micro blend | 225 | 0.270690 | 0.807804 | -0.000705 | -0.000326 | 1.000000 | 0.683333 | True | True | p95_aware_micro_blend | ppopt51_micro_blend__anchor=pp45__helper=pp43_score__mode=constant__w=0p3 |
| 4 | low-risk q50 residual 보정 | 384 | 0.270618 | 0.807660 | -0.000777 | -0.000470 | 1.000000 | 0.612500 | True | True | low_risk_q50_micro | ppopt50_lowrisk_q50__center=pp45__rel=0p75__width=mild__s=0p34__cap=0p008 |
| 3 | quantile consensus micro 보정 | 384 | 0.270637 | 0.807587 | -0.000758 | -0.000543 | 1.000000 | 0.504167 | True | True | quantile_consensus_micro | ppopt49_quantile_consensus_micro__center=pp41__wlim=0p22__guard=strict__s=0p42__cap=0p01 |
| 1 | PP45 very-high fallback 세밀화 | 525 | 0.270697 | 0.807587 | -0.000698 | -0.000543 | 1.000000 | 0.558333 | True | True | fallback_fine_grid | ppopt47_fallback_fine__base=pp41__fallback=pp30__mask=very_high_qwidth_soft__s=1p0 |
| 6 | 최종 fine-tune challenger 선택 | 1 | 0.270598 | 0.807660 | -0.000797 | -0.000470 | 1.000000 | 0.558333 | True | True | finetune_challenger_selection_protocol | ppopt52_finetune_challenger__source=ppopt49_quantile_consensus_micro__center_pp45__wlim_0p22__guard_medium__s_0p42__cap_0p01 |

## 운영 대체 통과 후보 상위
| item_id | candidate | family | test_MdAPE | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | incumbent_all3_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-OPT48 | ppopt48_segment_micro__center=pp38__group=price_conf__shrink=110p0__guard=medium__s=0p32__cap=0p0045 | p95_safe_segment_micro | 0.136800 | 0.270816 | 0.807385 | -0.000579 | -0.000745 | 1.000000 | 0.900000 | 0.779167 | -0.002413 |
| PP-OPT48 | ppopt48_segment_micro__center=pp38__group=price_conf__shrink=110p0__guard=medium__s=0p32__cap=0p006 | p95_safe_segment_micro | 0.136800 | 0.270801 | 0.807485 | -0.000593 | -0.000645 | 1.000000 | 0.900000 | 0.779167 | -0.002411 |
| PP-OPT48 | ppopt48_segment_micro__center=pp38__group=price_conf__shrink=70p0__guard=medium__s=0p25__cap=0p0045 | p95_safe_segment_micro | 0.136791 | 0.270820 | 0.807385 | -0.000575 | -0.000745 | 1.000000 | 0.912500 | 0.779167 | -0.002409 |
| PP-OPT48 | ppopt48_segment_micro__center=pp38__group=price_conf__shrink=70p0__guard=medium__s=0p25__cap=0p006 | p95_safe_segment_micro | 0.136791 | 0.270804 | 0.807485 | -0.000591 | -0.000645 | 1.000000 | 0.912500 | 0.779167 | -0.002407 |
| PP-OPT48 | ppopt48_segment_micro__center=pp38__group=price_conf__shrink=70p0__guard=medium__s=0p32__cap=0p006 | p95_safe_segment_micro | 0.137144 | 0.270814 | 0.807480 | -0.000580 | -0.000650 | 1.000000 | 0.933333 | 0.800000 | -0.002404 |
| PP-OPT48 | ppopt48_segment_micro__center=pp38__group=price_conf__shrink=70p0__guard=strict__s=0p32__cap=0p0045 | p95_safe_segment_micro | 0.137091 | 0.270822 | 0.807385 | -0.000573 | -0.000745 | 1.000000 | 0.925000 | 0.795833 | -0.002401 |
| PP-OPT48 | ppopt48_segment_micro__center=pp38__group=price_conf__shrink=110p0__guard=medium__s=0p32__cap=0p008 | p95_safe_segment_micro | 0.136800 | 0.270781 | 0.807557 | -0.000614 | -0.000573 | 1.000000 | 0.900000 | 0.775000 | -0.002399 |
| REFERENCE | reference_pp43_score | reference_prior | 0.136814 | 0.270715 | 0.808138 | -0.000680 | 0.000008 | 1.000000 | 0.925000 | 0.829167 | -0.002396 |
| PP-OPT48 | ppopt48_segment_micro__center=pp38__group=price_conf__shrink=70p0__guard=medium__s=0p32__cap=0p0045 | p95_safe_segment_micro | 0.137144 | 0.270833 | 0.807380 | -0.000562 | -0.000750 | 1.000000 | 0.929167 | 0.800000 | -0.002395 |
| PP-OPT48 | ppopt48_segment_micro__center=pp38__group=price_conf__shrink=70p0__guard=medium__s=0p25__cap=0p008 | p95_safe_segment_micro | 0.136791 | 0.270784 | 0.807539 | -0.000611 | -0.000591 | 1.000000 | 0.912500 | 0.775000 | -0.002394 |
| PP-OPT48 | ppopt48_segment_micro__center=pp38__group=price_conf__shrink=70p0__guard=medium__s=0p32__cap=0p008 | p95_safe_segment_micro | 0.137144 | 0.270796 | 0.807613 | -0.000599 | -0.000517 | 1.000000 | 0.933333 | 0.795833 | -0.002391 |
| REFERENCE | reference_pp46_safe | reference_prior | 0.136703 | 0.270792 | 0.807806 | -0.000603 | -0.000324 | 1.000000 | 0.900000 | 0.762500 | -0.002379 |
| PP-OPT48 | ppopt48_segment_micro__center=pp45__group=price_conf__shrink=70p0__guard=strict__s=0p25__cap=0p008 | p95_safe_segment_micro | 0.136175 | 0.270629 | 0.808055 | -0.000766 | -0.000075 | 1.000000 | 0.891667 | 0.829167 | -0.002375 |
| PP-OPT48 | ppopt48_segment_micro__center=pp45__group=price_conf__shrink=70p0__guard=medium__s=0p32__cap=0p006 | p95_safe_segment_micro | 0.136371 | 0.270666 | 0.808030 | -0.000729 | -0.000100 | 1.000000 | 0.895833 | 0.820833 | -0.002374 |
| PP-OPT48 | ppopt48_segment_micro__center=pp45__group=price_conf__shrink=110p0__guard=strict__s=0p32__cap=0p008 | p95_safe_segment_micro | 0.136162 | 0.270626 | 0.808071 | -0.000769 | -0.000059 | 1.000000 | 0.887500 | 0.825000 | -0.002374 |
| PP-OPT48 | ppopt48_segment_micro__center=pp45__group=price_conf__shrink=110p0__guard=medium__s=0p32__cap=0p008 | p95_safe_segment_micro | 0.136237 | 0.270632 | 0.808108 | -0.000763 | -0.000022 | 1.000000 | 0.891667 | 0.829167 | -0.002369 |
| PP-OPT48 | ppopt48_segment_micro__center=pp23__group=price_conf__shrink=70p0__guard=medium__s=0p32__cap=0p006 | p95_safe_segment_micro | 0.136371 | 0.270690 | 0.808030 | -0.000705 | -0.000100 | 1.000000 | 0.895833 | 0.825000 | -0.002368 |
| PP-OPT48 | ppopt48_segment_micro__center=pp45__group=price_conf__shrink=70p0__guard=strict__s=0p32__cap=0p008 | p95_safe_segment_micro | 0.136272 | 0.270637 | 0.808166 | -0.000758 | 0.000036 | 1.000000 | 0.895833 | 0.829167 | -0.002367 |
| PP-OPT48 | ppopt48_segment_micro__center=pp45__group=price_conf__shrink=70p0__guard=strict__s=0p32__cap=0p006 | p95_safe_segment_micro | 0.136272 | 0.270657 | 0.808036 | -0.000738 | -0.000094 | 1.000000 | 0.895833 | 0.816667 | -0.002366 |
| PP-OPT48 | ppopt48_segment_micro__center=pp41__group=price_conf__shrink=70p0__guard=medium__s=0p32__cap=0p008 | p95_safe_segment_micro | 0.136390 | 0.270685 | 0.808090 | -0.000710 | -0.000040 | 1.000000 | 0.895833 | 0.829167 | -0.002365 |
| PP-OPT48 | ppopt48_segment_micro__center=pp45__group=price_conf__shrink=70p0__guard=medium__s=0p25__cap=0p008 | p95_safe_segment_micro | 0.136253 | 0.270636 | 0.808090 | -0.000759 | -0.000040 | 1.000000 | 0.891667 | 0.829167 | -0.002364 |
| PP-OPT48 | ppopt48_segment_micro__center=pp45__group=price_conf__shrink=70p0__guard=medium__s=0p32__cap=0p0045 | p95_safe_segment_micro | 0.136371 | 0.270685 | 0.807931 | -0.000710 | -0.000199 | 1.000000 | 0.900000 | 0.820833 | -0.002363 |
| PP-OPT48 | ppopt48_segment_micro__center=pp41__group=price_conf__shrink=70p0__guard=medium__s=0p32__cap=0p006 | p95_safe_segment_micro | 0.136390 | 0.270706 | 0.807958 | -0.000689 | -0.000172 | 1.000000 | 0.895833 | 0.825000 | -0.002361 |
| PP-OPT48 | ppopt48_segment_micro__center=pp23__group=price_conf__shrink=70p0__guard=strict__s=0p32__cap=0p006 | p95_safe_segment_micro | 0.136272 | 0.270681 | 0.808036 | -0.000714 | -0.000094 | 1.000000 | 0.895833 | 0.820833 | -0.002360 |
| PP-OPT48 | ppopt48_segment_micro__center=pp41__group=price_conf__shrink=70p0__guard=strict__s=0p32__cap=0p008 | p95_safe_segment_micro | 0.136291 | 0.270676 | 0.808094 | -0.000719 | -0.000036 | 1.000000 | 0.895833 | 0.825000 | -0.002359 |
| PP-OPT48 | ppopt48_segment_micro__center=pp45__group=price_conf__shrink=110p0__guard=medium__s=0p32__cap=0p0045 | p95_safe_segment_micro | 0.136237 | 0.270667 | 0.807938 | -0.000728 | -0.000192 | 1.000000 | 0.891667 | 0.820833 | -0.002359 |
| PP-OPT48 | ppopt48_segment_micro__center=pp23__group=price_conf__shrink=70p0__guard=medium__s=0p32__cap=0p0045 | p95_safe_segment_micro | 0.136371 | 0.270709 | 0.807931 | -0.000686 | -0.000199 | 1.000000 | 0.900000 | 0.825000 | -0.002358 |
| PP-OPT48 | ppopt48_segment_micro__center=pp45__group=price_conf__shrink=70p0__guard=medium__s=0p32__cap=0p008 | p95_safe_segment_micro | 0.136371 | 0.270646 | 0.808162 | -0.000749 | 0.000032 | 1.000000 | 0.895833 | 0.825000 | -0.002357 |
| PP-OPT48 | ppopt48_segment_micro__center=pp45__group=price_conf__shrink=70p0__guard=strict__s=0p32__cap=0p0045 | p95_safe_segment_micro | 0.136272 | 0.270674 | 0.807937 | -0.000721 | -0.000193 | 1.000000 | 0.895833 | 0.816667 | -0.002357 |
| PP-OPT48 | ppopt48_segment_micro__center=pp45__group=price_conf__shrink=70p0__guard=medium__s=0p25__cap=0p0045 | p95_safe_segment_micro | 0.136253 | 0.270672 | 0.807937 | -0.000723 | -0.000193 | 1.000000 | 0.891667 | 0.820833 | -0.002355 |
| PP-OPT48 | ppopt48_segment_micro__center=pp23__group=price_conf__shrink=70p0__guard=strict__s=0p25__cap=0p008 | p95_safe_segment_micro | 0.136175 | 0.270653 | 0.808055 | -0.000742 | -0.000075 | 1.000000 | 0.883333 | 0.825000 | -0.002354 |
| PP-OPT48 | ppopt48_segment_micro__center=pp23__group=price_conf__shrink=110p0__guard=strict__s=0p32__cap=0p008 | p95_safe_segment_micro | 0.136162 | 0.270650 | 0.808071 | -0.000745 | -0.000059 | 1.000000 | 0.879167 | 0.820833 | -0.002352 |
| PP-OPT48 | ppopt48_segment_micro__center=pp41__group=price_conf__shrink=70p0__guard=medium__s=0p32__cap=0p0045 | p95_safe_segment_micro | 0.136390 | 0.270725 | 0.807859 | -0.000670 | -0.000271 | 1.000000 | 0.900000 | 0.825000 | -0.002351 |
| PP-OPT48 | ppopt48_segment_micro__center=pp23__group=price_conf__shrink=70p0__guard=strict__s=0p32__cap=0p0045 | p95_safe_segment_micro | 0.136272 | 0.270698 | 0.807937 | -0.000697 | -0.000193 | 1.000000 | 0.895833 | 0.820833 | -0.002351 |
| PP-OPT48 | ppopt48_segment_micro__center=pp23__group=price_conf__shrink=70p0__guard=medium__s=0p25__cap=0p008 | p95_safe_segment_micro | 0.136253 | 0.270660 | 0.808090 | -0.000735 | -0.000040 | 1.000000 | 0.891667 | 0.829167 | -0.002351 |
| PP-OPT48 | ppopt48_segment_micro__center=pp41__group=price_conf__shrink=110p0__guard=medium__s=0p32__cap=0p008 | p95_safe_segment_micro | 0.136256 | 0.270672 | 0.808036 | -0.000723 | -0.000094 | 1.000000 | 0.891667 | 0.829167 | -0.002349 |
| PP-OPT48 | ppopt48_segment_micro__center=pp23__group=price_conf__shrink=110p0__guard=medium__s=0p32__cap=0p008 | p95_safe_segment_micro | 0.136237 | 0.270657 | 0.808108 | -0.000738 | -0.000022 | 1.000000 | 0.883333 | 0.825000 | -0.002347 |
| PP-OPT48 | ppopt48_segment_micro__center=pp45__group=price_conf__shrink=70p0__guard=strict__s=0p25__cap=0p0045 | p95_safe_segment_micro | 0.136175 | 0.270663 | 0.807941 | -0.000732 | -0.000188 | 1.000000 | 0.891667 | 0.816667 | -0.002347 |
| PP-OPT48 | ppopt48_segment_micro__center=pp41__group=price_conf__shrink=70p0__guard=strict__s=0p32__cap=0p006 | p95_safe_segment_micro | 0.136291 | 0.270697 | 0.807964 | -0.000698 | -0.000166 | 1.000000 | 0.895833 | 0.816667 | -0.002345 |
| PP-OPT48 | ppopt48_segment_micro__center=pp41__group=price_conf__shrink=110p0__guard=strict__s=0p32__cap=0p008 | p95_safe_segment_micro | 0.136182 | 0.270666 | 0.807999 | -0.000729 | -0.000131 | 1.000000 | 0.883333 | 0.820833 | -0.002345 |

## 전체 MAPE 상위 후보
| item_id | candidate | family | test_MdAPE | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | incumbent_all3_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp23__rel=0p55__width=mild__s=0p34__cap=0p008 | low_risk_q50_micro | 0.138548 | 0.270319 | 0.807909 | -0.001076 | -0.000221 | 1.000000 | 0.412500 | 0.345833 | -0.000205 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp41__rel=0p55__width=mild__s=0p34__cap=0p008 | low_risk_q50_micro | 0.137280 | 0.270331 | 0.807849 | -0.001063 | -0.000281 | 1.000000 | 0.350000 | 0.283333 | -0.000266 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp23__rel=0p45__width=strict__s=0p34__cap=0p008 | low_risk_q50_micro | 0.138870 | 0.270338 | 0.808132 | -0.001057 | 0.000002 | 0.991667 | 0.395833 | 0.312500 | -0.000105 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp23__rel=0p45__width=mild__s=0p24__cap=0p008 | low_risk_q50_micro | 0.138817 | 0.270348 | 0.808102 | -0.001047 | -0.000028 | 0.995833 | 0.420833 | 0.329167 | -0.000206 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp23__rel=0p45__width=mild__s=0p34__cap=0p008 | low_risk_q50_micro | 0.139208 | 0.270352 | 0.808194 | -0.001042 | 0.000064 | 0.987500 | 0.354167 | 0.279167 | 0.000293 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp41__rel=0p45__width=strict__s=0p34__cap=0p008 | low_risk_q50_micro | 0.137002 | 0.270354 | 0.808082 | -0.001041 | -0.000048 | 1.000000 | 0.350000 | 0.270833 | -0.000254 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp41__rel=0p45__width=mild__s=0p24__cap=0p008 | low_risk_q50_micro | 0.137052 | 0.270356 | 0.808052 | -0.001039 | -0.000078 | 1.000000 | 0.383333 | 0.304167 | -0.000361 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp23__rel=0p55__width=strict__s=0p34__cap=0p008 | low_risk_q50_micro | 0.138377 | 0.270358 | 0.807848 | -0.001037 | -0.000282 | 1.000000 | 0.416667 | 0.366667 | -0.000479 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp41__rel=0p45__width=mild__s=0p34__cap=0p008 | low_risk_q50_micro | 0.136721 | 0.270359 | 0.808123 | -0.001036 | -0.000007 | 0.995833 | 0.345833 | 0.250000 | 0.000008 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp41__rel=0p55__width=strict__s=0p34__cap=0p008 | low_risk_q50_micro | 0.137421 | 0.270363 | 0.807784 | -0.001031 | -0.000346 | 1.000000 | 0.379167 | 0.329167 | -0.000548 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp23__rel=0p55__width=mild__s=0p24__cap=0p008 | low_risk_q50_micro | 0.138351 | 0.270372 | 0.807836 | -0.001023 | -0.000294 | 1.000000 | 0.416667 | 0.375000 | -0.000541 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp41__rel=0p55__width=mild__s=0p24__cap=0p008 | low_risk_q50_micro | 0.137446 | 0.270374 | 0.807772 | -0.001021 | -0.000358 | 1.000000 | 0.387500 | 0.345833 | -0.000618 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp45__rel=0p55__width=mild__s=0p34__cap=0p008 | low_risk_q50_micro | 0.137371 | 0.270374 | 0.807871 | -0.001021 | -0.000259 | 1.000000 | 0.445833 | 0.383333 | -0.000801 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp23__rel=0p45__width=strict__s=0p24__cap=0p008 | low_risk_q50_micro | 0.138578 | 0.270377 | 0.807993 | -0.001018 | -0.000137 | 1.000000 | 0.420833 | 0.354167 | -0.000461 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp41__rel=0p45__width=strict__s=0p24__cap=0p008 | low_risk_q50_micro | 0.137250 | 0.270387 | 0.807937 | -0.001007 | -0.000193 | 1.000000 | 0.383333 | 0.325000 | -0.000551 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp23__rel=0p45__width=mild__s=0p16__cap=0p008 | low_risk_q50_micro | 0.138505 | 0.270392 | 0.807955 | -0.001002 | -0.000175 | 1.000000 | 0.429167 | 0.375000 | -0.000568 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp41__rel=0p55__width=mild__s=0p34__cap=0p006 | low_risk_q50_micro | 0.137280 | 0.270397 | 0.807849 | -0.000998 | -0.000281 | 1.000000 | 0.354167 | 0.287500 | -0.000479 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp45__rel=0p45__width=mild__s=0p24__cap=0p008 | low_risk_q50_micro | 0.137166 | 0.270398 | 0.808034 | -0.000996 | -0.000096 | 1.000000 | 0.441667 | 0.354167 | -0.000823 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp45__rel=0p45__width=mild__s=0p34__cap=0p008 | low_risk_q50_micro | 0.136869 | 0.270399 | 0.808190 | -0.000996 | 0.000060 | 0.995833 | 0.437500 | 0.333333 | -0.000611 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp45__rel=0p45__width=strict__s=0p34__cap=0p008 | low_risk_q50_micro | 0.137134 | 0.270399 | 0.808063 | -0.000995 | -0.000067 | 1.000000 | 0.441667 | 0.350000 | -0.000793 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp41__rel=0p45__width=mild__s=0p16__cap=0p008 | low_risk_q50_micro | 0.137316 | 0.270403 | 0.807897 | -0.000992 | -0.000233 | 1.000000 | 0.383333 | 0.337500 | -0.000628 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp23__rel=0p55__width=mild__s=0p34__cap=0p006 | low_risk_q50_micro | 0.138548 | 0.270407 | 0.807909 | -0.000987 | -0.000221 | 1.000000 | 0.433333 | 0.366667 | -0.000460 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp45__rel=0p55__width=strict__s=0p34__cap=0p008 | low_risk_q50_micro | 0.137504 | 0.270410 | 0.807820 | -0.000985 | -0.000310 | 1.000000 | 0.466667 | 0.404167 | -0.000968 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp23__rel=0p55__width=strict__s=0p34__cap=0p006 | low_risk_q50_micro | 0.138377 | 0.270411 | 0.807848 | -0.000984 | -0.000282 | 1.000000 | 0.425000 | 0.375000 | -0.000625 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp23__rel=0p55__width=mild__s=0p24__cap=0p006 | low_risk_q50_micro | 0.138351 | 0.270412 | 0.807836 | -0.000983 | -0.000294 | 1.000000 | 0.433333 | 0.391667 | -0.000697 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp45__rel=0p55__width=mild__s=0p24__cap=0p008 | low_risk_q50_micro | 0.137520 | 0.270414 | 0.807809 | -0.000981 | -0.000321 | 1.000000 | 0.466667 | 0.404167 | -0.000986 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp41__rel=0p55__width=strict__s=0p34__cap=0p006 | low_risk_q50_micro | 0.137421 | 0.270417 | 0.807784 | -0.000978 | -0.000346 | 1.000000 | 0.387500 | 0.341667 | -0.000702 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp23__rel=0p55__width=strict__s=0p24__cap=0p008 | low_risk_q50_micro | 0.138230 | 0.270418 | 0.807793 | -0.000977 | -0.000337 | 1.000000 | 0.429167 | 0.391667 | -0.000823 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp41__rel=0p55__width=mild__s=0p24__cap=0p006 | low_risk_q50_micro | 0.137446 | 0.270421 | 0.807772 | -0.000974 | -0.000358 | 1.000000 | 0.395833 | 0.358333 | -0.000755 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp45__rel=0p55__width=mild__s=0p34__cap=0p006 | low_risk_q50_micro | 0.137371 | 0.270423 | 0.807871 | -0.000972 | -0.000259 | 1.000000 | 0.450000 | 0.391667 | -0.000960 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp45__rel=0p45__width=strict__s=0p24__cap=0p008 | low_risk_q50_micro | 0.137353 | 0.270424 | 0.807944 | -0.000971 | -0.000186 | 1.000000 | 0.441667 | 0.362500 | -0.000917 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp23__rel=0p45__width=mild__s=0p24__cap=0p006 | low_risk_q50_micro | 0.138817 | 0.270426 | 0.808061 | -0.000969 | -0.000069 | 1.000000 | 0.425000 | 0.333333 | -0.000338 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp23__rel=0p45__width=strict__s=0p24__cap=0p006 | low_risk_q50_micro | 0.138578 | 0.270428 | 0.807993 | -0.000967 | -0.000137 | 1.000000 | 0.429167 | 0.366667 | -0.000603 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp41__rel=0p55__width=strict__s=0p24__cap=0p008 | low_risk_q50_micro | 0.137546 | 0.270428 | 0.807726 | -0.000967 | -0.000404 | 1.000000 | 0.420833 | 0.375000 | -0.000866 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp23__rel=0p45__width=strict__s=0p34__cap=0p006 | low_risk_q50_micro | 0.138870 | 0.270432 | 0.808061 | -0.000963 | -0.000069 | 1.000000 | 0.400000 | 0.320833 | -0.000262 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp41__rel=0p45__width=strict__s=0p24__cap=0p006 | low_risk_q50_micro | 0.137250 | 0.270433 | 0.807937 | -0.000962 | -0.000193 | 1.000000 | 0.383333 | 0.333333 | -0.000696 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp23__rel=0p55__width=mild__s=0p16__cap=0p008 | low_risk_q50_micro | 0.138193 | 0.270435 | 0.807777 | -0.000960 | -0.000353 | 1.000000 | 0.445833 | 0.404167 | -0.000977 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp41__rel=0p45__width=mild__s=0p24__cap=0p006 | low_risk_q50_micro | 0.137052 | 0.270436 | 0.807989 | -0.000959 | -0.000141 | 1.000000 | 0.391667 | 0.316667 | -0.000523 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp45__rel=0p45__width=mild__s=0p16__cap=0p008 | low_risk_q50_micro | 0.137404 | 0.270437 | 0.807909 | -0.000958 | -0.000221 | 1.000000 | 0.445833 | 0.370833 | -0.000950 |
| PP-OPT50 | ppopt50_lowrisk_q50__center=pp41__rel=0p45__width=strict__s=0p34__cap=0p006 | low_risk_q50_micro | 0.137002 | 0.270438 | 0.807989 | -0.000957 | -0.000141 | 1.000000 | 0.383333 | 0.304167 | -0.000500 |

## 해석
이번 배치는 PP45 주변의 국소 탐색이다. PP45보다 개선 폭이 작거나 p95를 되돌리면 운영 후보 갱신보다 분석 후보로만 유지한다.

## 실행 설정
```json
{
  "experiment_id": "PP-OPT47-52",
  "experiment_slug": "PP-OPT47_52_warm_residual_finetune_experiments",
  "created_at": "2026-06-09T12:21:09",
  "seed": 20260609,
  "base_candidate": "hcoef_stable",
  "incumbent_candidate": "incumbent_operational_pp_opt7",
  "previous_challenger": "previous_challenger_pp20",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 3836,
  "prediction_rows": 4319336,
  "items": [
    {
      "item_id": "PP-OPT47",
      "priority": "1",
      "title": "PP45 very-high fallback 세밀화",
      "description": "PP45의 초고가 fallback 강도와 적용 마스크를 더 촘촘히 탐색한다."
    },
    {
      "item_id": "PP-OPT48",
      "priority": "2",
      "title": "p95-safe segment median micro 보정",
      "description": "구간 중앙 잔차 보정을 더 작은 cap과 강한 shrinkage로 제한한다."
    },
    {
      "item_id": "PP-OPT49",
      "priority": "3",
      "title": "quantile consensus micro 보정",
      "description": "q25/q50/q75가 같은 방향을 가리킬 때만 작은 잔차 보정을 적용한다."
    },
    {
      "item_id": "PP-OPT50",
      "priority": "4",
      "title": "low-risk q50 residual 보정",
      "description": "공격적인 q50 잔차 보정을 신뢰도 높은 row에만 축소 적용한다."
    },
    {
      "item_id": "PP-OPT51",
      "priority": "5",
      "title": "PP45와 보정 후보의 p95-aware micro blend",
      "description": "PP45를 중심으로 PP43/PP44/PP46 후보를 5~30% 범위에서만 혼합한다."
    },
    {
      "item_id": "PP-OPT52",
      "priority": "6",
      "title": "최종 fine-tune challenger 선택",
      "description": "PP45 대비 MAPE 개선과 p95 방어를 함께 만족하는 후보를 선택한다."
    }
  ],
  "selected_references": {
    "pp20": "previous_challenger_pp20",
    "pp23": "reference_pp23",
    "pp30": "reference_pp30_best",
    "pp36": "reference_pp36_challenger",
    "pp38": "reference_pp38_best",
    "pp41": "reference_pp41_challenger",
    "pp45": "ppopt45_high_price_fallback__base=pp23__fallback=pp30__mode=all_very_high__s=0p8",
    "pp43_score": "ppopt43_segment_median__center=pp23__group=price_conf__shrink=55p0__s=0p35__cap=0p008",
    "pp44_safe": "ppopt44_quantile_residual__center=pp38_score__src=q50_width__s=0p25__cap=0p02",
    "pp46_safe": "ppopt46_monotonic_cap__center=pp38_score__src=segment__s=0p25__cap=0p012"
  },
  "selection_decision": {
    "selected_source_candidate": "ppopt49_quantile_consensus_micro__center=pp45__wlim=0p22__guard=medium__s=0p42__cap=0p01",
    "selected_source_item_id": "PP-OPT49",
    "selected_source_family": "quantile_consensus_micro",
    "selection_reason": "prefer PP45 MAPE improvement with p95 not worse than PP7 and small p95 give-back versus PP45",
    "test_MdAPE": 0.13787846966744394,
    "test_MAPE": 0.2705982707897427,
    "test_p95_APE": 0.8076599439149326,
    "test_delta_vs_incumbent_MdAPE": 0.000985903768827734,
    "test_delta_vs_incumbent_MAPE": -0.00079661722232377,
    "test_delta_vs_incumbent_p95_APE": -0.00047003879853613206,
    "recommendation_score_vs_incumbent": -0.0013195993882742596,
    "protocol_candidate": "ppopt52_finetune_challenger__source=ppopt49_quantile_consensus_micro__center_pp45__wlim_0p22__guard_medium__s_0p42__cap_0p01"
  },
  "sources": {
    "pp_opt42_config": "PP-OPT42_46_warm_residual_correction_experiments",
    "pp_opt42_predictions": "experiments/track6/PP-OPT42_46_warm_residual_correction_experiments/outputs/candidate_predictions.csv",
    "pp_opt42_aggregate": "experiments/track6/PP-OPT42_46_warm_residual_correction_experiments/outputs/aggregate_candidate_stability.csv",
    "pp_opt42_helper": "scripts/track6/run_pp_opt42_46_warm_residual_correction_experiments.py"
  }
}
```