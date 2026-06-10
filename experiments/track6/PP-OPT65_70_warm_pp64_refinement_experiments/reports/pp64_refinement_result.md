# PP-OPT65~70 Warm PP64 refinement 실험 결과

- 작성일: 2026-06-09 12:52
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 고정 기준 후보: PP64
- 전체 후보 수: 4722
- 운영 대체 통과 후보 수: 4670

## 최종 선택 후보
- 선택 후보: `ppopt70_pp64_refinement_challenger__source=ppopt68_shrinkage__global_1p04__risk_0p7__vh_0p82__lowconf_0p78`
- 원본 후보: `ppopt68_shrinkage__global=1p04__risk=0p7__vh=0p82__lowconf=0p78`
- 판단: PP70 선택 후보는 PP64 대비 MAPE -0.000003, p95 -0.000009이다.
| eval_split | n | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | 607 | 0.137878 | 0.270561 | 0.807490 | 0.397991 | 0.782537 | 0.883031 | -0.000834 | -0.000640 |
| validation_oof | 519 | 0.122635 | 0.206280 | 0.637897 | 0.323781 | 0.782274 | 0.911368 | -0.000743 | 0.001302 |

## 주요 reference test 비교
| candidate | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- |
| ppopt70_pp64_refinement_challenger__source=ppopt68_shrinkage__global_1p04__risk_0p7__vh_0p82__lowconf_0p78 | 0.137878 | 0.270561 | 0.807490 | 0.397991 | -0.000834 | -0.000640 |
| reference_pp64_current_best | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |
| reference_pp58_challenger | 0.137878 | 0.270572 | 0.807811 | 0.397997 | -0.000823 | -0.000319 |
| reference_pp52_challenger | 0.137878 | 0.270598 | 0.807660 | 0.397987 | -0.000797 | -0.000470 |
| reference_pp48_score | 0.136800 | 0.270816 | 0.807385 | 0.398121 | -0.000579 | -0.000745 |
| previous_challenger_pp20 | 0.136835 | 0.271182 | 0.806472 | 0.398134 | -0.000213 | -0.001658 |
| incumbent_operational_pp_opt7 | 0.136893 | 0.271395 | 0.808130 | 0.398341 | 0.000000 | 0.000000 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | stable_validation_pass_vs_incumbent | operational_pass_vs_incumbent | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | PP64 tail-only fallback guard | 600 | 0.270577 | 0.807512 | -0.000818 | -0.000618 | 1.000000 | 0.508333 | True | True | pp64_tail_only_fallback_guard | ppopt66_tail_guard__helper=pp48_score__score=combined__thr=0p66__width=0p22__s=0p44 |
| 4 | PP64 correction shrinkage by risk segment | 192 | 0.270562 | 0.807491 | -0.000833 | -0.000639 | 1.000000 | 0.508333 | True | True | pp64_risk_segment_shrinkage | ppopt68_shrinkage__global=1p04__risk=0p7__vh=0p82__lowconf=1p0 |
| 6 | 최종 PP64 refinement challenger 선택 | 1 | 0.270561 | 0.807490 | -0.000834 | -0.000640 | 1.000000 | 0.508333 | True | True | pp64_refinement_selection_protocol | ppopt70_pp64_refinement_challenger__source=ppopt68_shrinkage__global_1p04__risk_0p7__vh_0p82__lowconf_0p78 |
| 5 | PP64 stability dynamic blend | 120 | 0.270571 | 0.807509 | -0.000824 | -0.000621 | 1.000000 | 0.508333 | True | True | pp64_stability_dynamic_blend | ppopt69_dynamic_blend__low=pp52__high=pp48_score__lows=0p0__highs=0p32 |
| 1 | PP64 segment threshold local fine grid | 3750 | 0.270586 | 0.807613 | -0.000809 | -0.000517 | 1.000000 | 0.520833 | True | True | pp64_local_threshold_grid | ppopt65_local_threshold__helper=pp48_score__base=0p4__vh=0p04__lowconf=0p02__width=0p48__s=0p76 |
| 3 | quantile consensus micro correction on PP64 | 50 | 0.270561 | 0.807499 | -0.000834 | -0.000631 | 1.000000 | 0.508333 | True | False | pp64_quantile_consensus_micro | ppopt67_quantile_micro__guard=risk_discount__s=0p07__cap=0p003 |

## 운영 대체 통과 후보 상위
| item_id | candidate | family | test_MdAPE | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | incumbent_all3_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REFERENCE | reference_pp48_score | reference_prior | 0.136800 | 0.270816 | 0.807385 | -0.000579 | -0.000745 | 1.000000 | 0.900000 | 0.779167 | -0.002413 |
| REFERENCE | reference_pp30_best | reference_prior | 0.137546 | 0.270872 | 0.806932 | -0.000523 | -0.001198 | 1.000000 | 0.550000 | 0.495833 | -0.001396 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp48_score__score=combined__thr=0p66__width=0p22__s=0p44 | pp64_tail_only_fallback_guard | 0.137878 | 0.270577 | 0.807512 | -0.000818 | -0.000618 | 1.000000 | 0.508333 | 0.412500 | -0.001327 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp48_score__score=combined__thr=0p66__width=0p22__s=0p32 | pp64_tail_only_fallback_guard | 0.137878 | 0.270574 | 0.807509 | -0.000821 | -0.000621 | 1.000000 | 0.508333 | 0.412500 | -0.001327 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp48_score__score=combined__thr=0p6__width=0p42__s=0p32 | pp64_tail_only_fallback_guard | 0.137878 | 0.270573 | 0.807508 | -0.000822 | -0.000622 | 1.000000 | 0.508333 | 0.412500 | -0.001327 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp48_score__score=combined__thr=0p66__width=0p32__s=0p44 | pp64_tail_only_fallback_guard | 0.137878 | 0.270573 | 0.807508 | -0.000822 | -0.000622 | 1.000000 | 0.508333 | 0.412500 | -0.001327 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp48_score__score=combined__thr=0p6__width=0p32__s=0p22 | pp64_tail_only_fallback_guard | 0.137878 | 0.270572 | 0.807507 | -0.000823 | -0.000623 | 1.000000 | 0.508333 | 0.412500 | -0.001326 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp48_score__score=combined__thr=0p6__width=0p22__s=0p14 | pp64_tail_only_fallback_guard | 0.137878 | 0.270571 | 0.807506 | -0.000824 | -0.000624 | 1.000000 | 0.508333 | 0.412500 | -0.001326 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp48_score__score=combined__thr=0p66__width=0p42__s=0p44 | pp64_tail_only_fallback_guard | 0.137878 | 0.270571 | 0.807506 | -0.000824 | -0.000624 | 1.000000 | 0.508333 | 0.412500 | -0.001326 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp48_score__score=combined__thr=0p66__width=0p22__s=0p22 | pp64_tail_only_fallback_guard | 0.137878 | 0.270571 | 0.807506 | -0.000824 | -0.000624 | 1.000000 | 0.508333 | 0.412500 | -0.001326 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp48_score__score=combined__thr=0p66__width=0p32__s=0p32 | pp64_tail_only_fallback_guard | 0.137878 | 0.270571 | 0.807506 | -0.000824 | -0.000624 | 1.000000 | 0.508333 | 0.412500 | -0.001326 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp48_score__score=combined__thr=0p6__width=0p42__s=0p22 | pp64_tail_only_fallback_guard | 0.137878 | 0.270570 | 0.807505 | -0.000825 | -0.000625 | 1.000000 | 0.508333 | 0.412500 | -0.001326 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp48_score__score=combined__thr=0p6__width=0p32__s=0p14 | pp64_tail_only_fallback_guard | 0.137878 | 0.270569 | 0.807504 | -0.000826 | -0.000626 | 1.000000 | 0.508333 | 0.412500 | -0.001326 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp48score_pp20__score=combined__thr=0p6__width=0p22__s=0p22 | pp64_tail_only_fallback_guard | 0.137878 | 0.270575 | 0.807506 | -0.000820 | -0.000624 | 1.000000 | 0.508333 | 0.412500 | -0.001326 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp48score_pp20__score=combined__thr=0p6__width=0p42__s=0p44 | pp64_tail_only_fallback_guard | 0.137878 | 0.270575 | 0.807506 | -0.000819 | -0.000624 | 1.000000 | 0.508333 | 0.412500 | -0.001326 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp48_score__score=combined__thr=0p66__width=0p42__s=0p32 | pp64_tail_only_fallback_guard | 0.137878 | 0.270569 | 0.807504 | -0.000826 | -0.000626 | 1.000000 | 0.508333 | 0.412500 | -0.001326 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp48score_pp20__score=combined__thr=0p6__width=0p32__s=0p32 | pp64_tail_only_fallback_guard | 0.137878 | 0.270575 | 0.807506 | -0.000820 | -0.000624 | 1.000000 | 0.508333 | 0.412500 | -0.001326 |
| PP-OPT68 | ppopt68_shrinkage__global=1p04__risk=0p7__vh=0p82__lowconf=1p0 | pp64_risk_segment_shrinkage | 0.137878 | 0.270562 | 0.807491 | -0.000833 | -0.000639 | 1.000000 | 0.508333 | 0.412500 | -0.001326 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp48_score__score=combined__thr=0p54__width=0p42__s=0p14 | pp64_tail_only_fallback_guard | 0.137878 | 0.270569 | 0.807504 | -0.000826 | -0.000626 | 1.000000 | 0.508333 | 0.412500 | -0.001326 |
| PP-OPT68 | ppopt68_shrinkage__global=1p04__risk=0p7__vh=0p94__lowconf=1p0 | pp64_risk_segment_shrinkage | 0.137878 | 0.270562 | 0.807491 | -0.000833 | -0.000639 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp48score_pp20__score=combined__thr=0p66__width=0p22__s=0p44 | pp64_tail_only_fallback_guard | 0.137878 | 0.270577 | 0.807507 | -0.000818 | -0.000623 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT68 | ppopt68_shrinkage__global=1p04__risk=0p7__vh=1p0__lowconf=1p0 | pp64_risk_segment_shrinkage | 0.137878 | 0.270563 | 0.807491 | -0.000832 | -0.000639 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp48_score__score=combined__thr=0p66__width=0p32__s=0p22 | pp64_tail_only_fallback_guard | 0.137878 | 0.270569 | 0.807503 | -0.000826 | -0.000626 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp48_score__score=combined__thr=0p54__width=0p22__s=0p08 | pp64_tail_only_fallback_guard | 0.137878 | 0.270570 | 0.807505 | -0.000825 | -0.000625 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT68 | ppopt68_shrinkage__global=1p04__risk=0p7__vh=1p08__lowconf=1p0 | pp64_risk_segment_shrinkage | 0.137878 | 0.270563 | 0.807491 | -0.000832 | -0.000639 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp48_score__score=combined__thr=0p72__width=0p22__s=0p44 | pp64_tail_only_fallback_guard | 0.137878 | 0.270569 | 0.807503 | -0.000826 | -0.000627 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp48_score__score=combined__thr=0p6__width=0p22__s=0p08 | pp64_tail_only_fallback_guard | 0.137878 | 0.270568 | 0.807503 | -0.000827 | -0.000627 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT68 | ppopt68_shrinkage__global=1p04__risk=0p82__vh=0p82__lowconf=1p0 | pp64_risk_segment_shrinkage | 0.137878 | 0.270562 | 0.807492 | -0.000833 | -0.000638 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp48_score__score=combined__thr=0p66__width=0p22__s=0p14 | pp64_tail_only_fallback_guard | 0.137878 | 0.270568 | 0.807503 | -0.000827 | -0.000627 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp48_score__score=risk__thr=0p66__width=0p22__s=0p44 | pp64_tail_only_fallback_guard | 0.137878 | 0.270567 | 0.807508 | -0.000827 | -0.000622 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT68 | ppopt68_shrinkage__global=1p04__risk=0p82__vh=0p94__lowconf=1p0 | pp64_risk_segment_shrinkage | 0.137878 | 0.270562 | 0.807492 | -0.000833 | -0.000638 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT68 | ppopt68_shrinkage__global=1p04__risk=0p82__vh=1p0__lowconf=1p0 | pp64_risk_segment_shrinkage | 0.137878 | 0.270563 | 0.807492 | -0.000832 | -0.000638 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp48_score__score=combined__thr=0p6__width=0p42__s=0p14 | pp64_tail_only_fallback_guard | 0.137878 | 0.270568 | 0.807503 | -0.000827 | -0.000627 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT68 | ppopt68_shrinkage__global=1p04__risk=0p82__vh=1p08__lowconf=1p0 | pp64_risk_segment_shrinkage | 0.137878 | 0.270563 | 0.807492 | -0.000832 | -0.000638 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp48score_pp20__score=combined__thr=0p6__width=0p42__s=0p32 | pp64_tail_only_fallback_guard | 0.137878 | 0.270572 | 0.807504 | -0.000823 | -0.000626 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT68 | ppopt68_shrinkage__global=1p04__risk=0p94__vh=0p82__lowconf=1p0 | pp64_risk_segment_shrinkage | 0.137878 | 0.270562 | 0.807492 | -0.000833 | -0.000638 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT68 | ppopt68_shrinkage__global=1p04__risk=0p7__vh=0p82__lowconf=0p9 | pp64_risk_segment_shrinkage | 0.137878 | 0.270561 | 0.807491 | -0.000834 | -0.000639 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp48_score__score=combined__thr=0p54__width=0p32__s=0p08 | pp64_tail_only_fallback_guard | 0.137878 | 0.270568 | 0.807503 | -0.000827 | -0.000627 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp48score_pp20__score=combined__thr=0p66__width=0p22__s=0p32 | pp64_tail_only_fallback_guard | 0.137878 | 0.270573 | 0.807505 | -0.000822 | -0.000625 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT68 | ppopt68_shrinkage__global=1p04__risk=0p94__vh=0p94__lowconf=1p0 | pp64_risk_segment_shrinkage | 0.137878 | 0.270562 | 0.807492 | -0.000833 | -0.000638 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT68 | ppopt68_shrinkage__global=1p04__risk=0p94__vh=1p0__lowconf=1p0 | pp64_risk_segment_shrinkage | 0.137878 | 0.270563 | 0.807492 | -0.000832 | -0.000638 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp48_score__score=combined__thr=0p66__width=0p42__s=0p22 | pp64_tail_only_fallback_guard | 0.137878 | 0.270568 | 0.807502 | -0.000827 | -0.000628 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT68 | ppopt68_shrinkage__global=1p04__risk=0p7__vh=0p94__lowconf=0p9 | pp64_risk_segment_shrinkage | 0.137878 | 0.270562 | 0.807491 | -0.000833 | -0.000639 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp48_score__score=combined__thr=0p72__width=0p22__s=0p32 | pp64_tail_only_fallback_guard | 0.137878 | 0.270567 | 0.807502 | -0.000828 | -0.000628 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT68 | ppopt68_shrinkage__global=1p04__risk=1p0__vh=0p82__lowconf=1p0 | pp64_risk_segment_shrinkage | 0.137878 | 0.270562 | 0.807492 | -0.000833 | -0.000638 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |

## 전체 MAPE 상위 후보
| item_id | candidate | family | test_MdAPE | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | incumbent_all3_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-OPT67 | ppopt67_quantile_micro__guard=risk_discount__s=0p1__cap=0p014 | pp64_quantile_consensus_micro | 0.139573 | 0.270518 | 0.807499 | -0.000877 | -0.000631 | 1.000000 | 0.508333 | 0.391667 | -0.000954 |
| PP-OPT67 | ppopt67_quantile_micro__guard=risk_discount__s=0p07__cap=0p014 | pp64_quantile_consensus_micro | 0.141080 | 0.270530 | 0.807499 | -0.000864 | -0.000631 | 1.000000 | 0.508333 | 0.395833 | -0.000557 |
| PP-OPT67 | ppopt67_quantile_micro__guard=risk_discount__s=0p07__cap=0p01 | pp64_quantile_consensus_micro | 0.141080 | 0.270531 | 0.807499 | -0.000864 | -0.000631 | 1.000000 | 0.508333 | 0.395833 | -0.000557 |
| PP-OPT67 | ppopt67_quantile_micro__guard=reliability__s=0p1__cap=0p014 | pp64_quantile_consensus_micro | 0.140332 | 0.270533 | 0.807499 | -0.000862 | -0.000631 | 1.000000 | 0.508333 | 0.375000 | -0.000751 |
| PP-OPT67 | ppopt67_quantile_micro__guard=risk_discount__s=0p14__cap=0p014 | pp64_quantile_consensus_micro | 0.140444 | 0.270534 | 0.807499 | -0.000861 | -0.000631 | 1.000000 | 0.508333 | 0.375000 | -0.000740 |
| PP-OPT67 | ppopt67_quantile_micro__guard=reliability__s=0p07__cap=0p014 | pp64_quantile_consensus_micro | 0.141001 | 0.270534 | 0.807499 | -0.000861 | -0.000631 | 1.000000 | 0.508333 | 0.391667 | -0.000583 |
| PP-OPT67 | ppopt67_quantile_micro__guard=reliability__s=0p07__cap=0p01 | pp64_quantile_consensus_micro | 0.141001 | 0.270541 | 0.807499 | -0.000854 | -0.000631 | 1.000000 | 0.508333 | 0.391667 | -0.000583 |
| PP-OPT67 | ppopt67_quantile_micro__guard=risk_discount__s=0p1__cap=0p01 | pp64_quantile_consensus_micro | 0.139573 | 0.270541 | 0.807499 | -0.000853 | -0.000631 | 1.000000 | 0.508333 | 0.391667 | -0.000954 |
| PP-OPT67 | ppopt67_quantile_micro__guard=risk_discount__s=0p14__cap=0p01 | pp64_quantile_consensus_micro | 0.140444 | 0.270542 | 0.807499 | -0.000853 | -0.000631 | 1.000000 | 0.508333 | 0.375000 | -0.000731 |
| PP-OPT67 | ppopt67_quantile_micro__guard=risk_discount__s=0p04__cap=0p007 | pp64_quantile_consensus_micro | 0.140246 | 0.270545 | 0.807499 | -0.000850 | -0.000631 | 1.000000 | 0.508333 | 0.408333 | -0.000762 |
| PP-OPT67 | ppopt67_quantile_micro__guard=risk_discount__s=0p04__cap=0p01 | pp64_quantile_consensus_micro | 0.140246 | 0.270545 | 0.807499 | -0.000850 | -0.000631 | 1.000000 | 0.508333 | 0.408333 | -0.000762 |
| PP-OPT67 | ppopt67_quantile_micro__guard=risk_discount__s=0p04__cap=0p014 | pp64_quantile_consensus_micro | 0.140246 | 0.270545 | 0.807499 | -0.000850 | -0.000631 | 1.000000 | 0.508333 | 0.408333 | -0.000762 |
| PP-OPT67 | ppopt67_quantile_micro__guard=risk_discount__s=0p18__cap=0p014 | pp64_quantile_consensus_micro | 0.141167 | 0.270545 | 0.807499 | -0.000850 | -0.000631 | 1.000000 | 0.508333 | 0.375000 | -0.000594 |
| PP-OPT67 | ppopt67_quantile_micro__guard=risk_discount__s=0p04__cap=0p005 | pp64_quantile_consensus_micro | 0.140246 | 0.270547 | 0.807499 | -0.000848 | -0.000631 | 1.000000 | 0.508333 | 0.408333 | -0.000762 |
| PP-OPT67 | ppopt67_quantile_micro__guard=reliability__s=0p04__cap=0p007 | pp64_quantile_consensus_micro | 0.141167 | 0.270547 | 0.807499 | -0.000848 | -0.000631 | 1.000000 | 0.508333 | 0.400000 | -0.000523 |
| PP-OPT67 | ppopt67_quantile_micro__guard=reliability__s=0p04__cap=0p01 | pp64_quantile_consensus_micro | 0.141167 | 0.270547 | 0.807499 | -0.000848 | -0.000631 | 1.000000 | 0.508333 | 0.400000 | -0.000523 |
| PP-OPT67 | ppopt67_quantile_micro__guard=reliability__s=0p04__cap=0p014 | pp64_quantile_consensus_micro | 0.141167 | 0.270547 | 0.807499 | -0.000848 | -0.000631 | 1.000000 | 0.508333 | 0.400000 | -0.000523 |
| PP-OPT67 | ppopt67_quantile_micro__guard=risk_discount__s=0p1__cap=0p007 | pp64_quantile_consensus_micro | 0.139573 | 0.270548 | 0.807499 | -0.000847 | -0.000631 | 1.000000 | 0.508333 | 0.391667 | -0.000946 |
| PP-OPT67 | ppopt67_quantile_micro__guard=risk_discount__s=0p07__cap=0p007 | pp64_quantile_consensus_micro | 0.141080 | 0.270548 | 0.807499 | -0.000847 | -0.000631 | 1.000000 | 0.508333 | 0.395833 | -0.000557 |
| PP-OPT67 | ppopt67_quantile_micro__guard=risk_discount__s=0p18__cap=0p01 | pp64_quantile_consensus_micro | 0.141167 | 0.270549 | 0.807499 | -0.000846 | -0.000631 | 1.000000 | 0.508333 | 0.375000 | -0.000565 |
| PP-OPT67 | ppopt67_quantile_micro__guard=risk_discount__s=0p07__cap=0p005 | pp64_quantile_consensus_micro | 0.140648 | 0.270552 | 0.807499 | -0.000843 | -0.000631 | 1.000000 | 0.508333 | 0.395833 | -0.000660 |
| PP-OPT67 | ppopt67_quantile_micro__guard=risk_discount__s=0p14__cap=0p007 | pp64_quantile_consensus_micro | 0.140444 | 0.270554 | 0.807499 | -0.000841 | -0.000631 | 1.000000 | 0.508333 | 0.391667 | -0.000745 |
| PP-OPT67 | ppopt67_quantile_micro__guard=reliability__s=0p04__cap=0p005 | pp64_quantile_consensus_micro | 0.140648 | 0.270555 | 0.807499 | -0.000840 | -0.000631 | 1.000000 | 0.508333 | 0.400000 | -0.000653 |
| PP-OPT67 | ppopt67_quantile_micro__guard=risk_discount__s=0p1__cap=0p005 | pp64_quantile_consensus_micro | 0.140297 | 0.270557 | 0.807499 | -0.000838 | -0.000631 | 1.000000 | 0.508333 | 0.391667 | -0.000752 |
| PP-OPT67 | ppopt67_quantile_micro__guard=risk_discount__s=0p04__cap=0p003 | pp64_quantile_consensus_micro | 0.138928 | 0.270557 | 0.807499 | -0.000838 | -0.000631 | 1.000000 | 0.508333 | 0.408333 | -0.001090 |
| PP-OPT67 | ppopt67_quantile_micro__guard=risk_discount__s=0p18__cap=0p007 | pp64_quantile_consensus_micro | 0.140463 | 0.270558 | 0.807499 | -0.000837 | -0.000631 | 1.000000 | 0.508333 | 0.391667 | -0.000741 |
| PP-OPT67 | ppopt67_quantile_micro__guard=reliability__s=0p1__cap=0p01 | pp64_quantile_consensus_micro | 0.140332 | 0.270559 | 0.807499 | -0.000836 | -0.000631 | 1.000000 | 0.508333 | 0.375000 | -0.000742 |
| PP-OPT67 | ppopt67_quantile_micro__guard=reliability__s=0p14__cap=0p014 | pp64_quantile_consensus_micro | 0.141167 | 0.270560 | 0.807499 | -0.000835 | -0.000631 | 1.000000 | 0.508333 | 0.370833 | -0.000567 |
| PP-OPT67 | ppopt67_quantile_micro__guard=reliability__s=0p07__cap=0p007 | pp64_quantile_consensus_micro | 0.141001 | 0.270560 | 0.807499 | -0.000835 | -0.000631 | 1.000000 | 0.508333 | 0.391667 | -0.000576 |
| PP-OPT67 | ppopt67_quantile_micro__guard=risk_discount__s=0p07__cap=0p003 | pp64_quantile_consensus_micro | 0.138928 | 0.270561 | 0.807499 | -0.000834 | -0.000631 | 1.000000 | 0.508333 | 0.408333 | -0.001098 |
| PP-OPT68 | ppopt68_shrinkage__global=1p04__risk=0p7__vh=0p82__lowconf=0p78 | pp64_risk_segment_shrinkage | 0.137878 | 0.270561 | 0.807490 | -0.000834 | -0.000640 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT70 | ppopt70_pp64_refinement_challenger__source=ppopt68_shrinkage__global_1p04__risk_0p7__vh_0p82__lowconf_0p78 | pp64_refinement_selection_protocol | 0.137878 | 0.270561 | 0.807490 | -0.000834 | -0.000640 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT68 | ppopt68_shrinkage__global=1p04__risk=0p82__vh=0p82__lowconf=0p78 | pp64_risk_segment_shrinkage | 0.137878 | 0.270561 | 0.807490 | -0.000834 | -0.000640 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT68 | ppopt68_shrinkage__global=1p04__risk=0p94__vh=0p82__lowconf=0p78 | pp64_risk_segment_shrinkage | 0.137878 | 0.270561 | 0.807491 | -0.000834 | -0.000639 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT68 | ppopt68_shrinkage__global=1p04__risk=1p0__vh=0p82__lowconf=0p78 | pp64_risk_segment_shrinkage | 0.137878 | 0.270561 | 0.807491 | -0.000834 | -0.000639 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT68 | ppopt68_shrinkage__global=1p04__risk=0p7__vh=0p82__lowconf=0p9 | pp64_risk_segment_shrinkage | 0.137878 | 0.270561 | 0.807491 | -0.000834 | -0.000639 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT68 | ppopt68_shrinkage__global=1p04__risk=0p82__vh=0p82__lowconf=0p9 | pp64_risk_segment_shrinkage | 0.137878 | 0.270561 | 0.807491 | -0.000833 | -0.000639 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT67 | ppopt67_quantile_micro__guard=risk_discount__s=0p14__cap=0p005 | pp64_quantile_consensus_micro | 0.140297 | 0.270561 | 0.807499 | -0.000833 | -0.000631 | 1.000000 | 0.508333 | 0.391667 | -0.000751 |
| PP-OPT68 | ppopt68_shrinkage__global=1p04__risk=0p94__vh=0p82__lowconf=0p9 | pp64_risk_segment_shrinkage | 0.137878 | 0.270561 | 0.807492 | -0.000833 | -0.000638 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT68 | ppopt68_shrinkage__global=1p04__risk=1p0__vh=0p82__lowconf=0p9 | pp64_risk_segment_shrinkage | 0.137878 | 0.270561 | 0.807492 | -0.000833 | -0.000638 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT68 | ppopt68_shrinkage__global=1p04__risk=0p7__vh=0p94__lowconf=0p78 | pp64_risk_segment_shrinkage | 0.137878 | 0.270562 | 0.807490 | -0.000833 | -0.000640 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT68 | ppopt68_shrinkage__global=1p04__risk=0p82__vh=0p94__lowconf=0p78 | pp64_risk_segment_shrinkage | 0.137878 | 0.270562 | 0.807490 | -0.000833 | -0.000640 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT68 | ppopt68_shrinkage__global=1p04__risk=0p7__vh=0p82__lowconf=1p0 | pp64_risk_segment_shrinkage | 0.137878 | 0.270562 | 0.807491 | -0.000833 | -0.000639 | 1.000000 | 0.508333 | 0.412500 | -0.001326 |
| PP-OPT68 | ppopt68_shrinkage__global=1p04__risk=0p94__vh=0p94__lowconf=0p78 | pp64_risk_segment_shrinkage | 0.137878 | 0.270562 | 0.807491 | -0.000833 | -0.000639 | 1.000000 | 0.508333 | 0.412500 | -0.001325 |
| PP-OPT68 | ppopt68_shrinkage__global=1p04__risk=1p0__vh=0p94__lowconf=0p78 | pp64_risk_segment_shrinkage | 0.137878 | 0.270562 | 0.807491 | -0.000833 | -0.000639 | 1.000000 | 0.508333 | 0.412500 | -0.001324 |

## 전체 p95 상위 후보
| item_id | candidate | family | test_MdAPE | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | incumbent_all3_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REFERENCE | previous_challenger_pp20 | reference_prior | 0.136835 | 0.271182 | 0.806472 | -0.000213 | -0.001658 | 1.000000 | 0.554167 | 0.316667 | -0.000883 |
| REFERENCE | reference_pp30_best | reference_prior | 0.137546 | 0.270872 | 0.806932 | -0.000523 | -0.001198 | 1.000000 | 0.550000 | 0.495833 | -0.001396 |
| REFERENCE | reference_pp48_score | reference_prior | 0.136800 | 0.270816 | 0.807385 | -0.000579 | -0.000745 | 1.000000 | 0.900000 | 0.779167 | -0.002413 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp20__score=combined__thr=0p54__width=0p22__s=0p44 | pp64_tail_only_fallback_guard | 0.137878 | 0.270592 | 0.807464 | -0.000802 | -0.000666 | 1.000000 | 0.508333 | 0.412500 | -0.001309 |
| PP-OPT65 | ppopt65_local_threshold__helper=pp48score_pp20__base=0p32__vh=0p12__lowconf=0p1__width=0p36__s=0p92 | pp64_local_threshold_grid | 0.137878 | 0.270584 | 0.807464 | -0.000811 | -0.000666 | 1.000000 | 0.508333 | 0.408333 | -0.001284 |
| PP-OPT65 | ppopt65_local_threshold__helper=pp48score_pp20__base=0p32__vh=0p1__lowconf=0p1__width=0p36__s=0p92 | pp64_local_threshold_grid | 0.137878 | 0.270584 | 0.807464 | -0.000811 | -0.000666 | 1.000000 | 0.508333 | 0.408333 | -0.001285 |
| PP-OPT65 | ppopt65_local_threshold__helper=pp48score_pp20__base=0p32__vh=0p12__lowconf=0p08__width=0p36__s=0p92 | pp64_local_threshold_grid | 0.137878 | 0.270584 | 0.807464 | -0.000811 | -0.000666 | 1.000000 | 0.508333 | 0.408333 | -0.001284 |
| PP-OPT65 | ppopt65_local_threshold__helper=pp48score_pp20__base=0p32__vh=0p08__lowconf=0p1__width=0p36__s=0p92 | pp64_local_threshold_grid | 0.137878 | 0.270585 | 0.807464 | -0.000810 | -0.000666 | 1.000000 | 0.508333 | 0.408333 | -0.001285 |
| PP-OPT65 | ppopt65_local_threshold__helper=pp48score_pp20__base=0p32__vh=0p1__lowconf=0p08__width=0p36__s=0p92 | pp64_local_threshold_grid | 0.137878 | 0.270585 | 0.807464 | -0.000810 | -0.000666 | 1.000000 | 0.508333 | 0.408333 | -0.001284 |
| PP-OPT65 | ppopt65_local_threshold__helper=pp48score_pp20__base=0p32__vh=0p12__lowconf=0p06__width=0p36__s=0p92 | pp64_local_threshold_grid | 0.137878 | 0.270585 | 0.807464 | -0.000810 | -0.000666 | 1.000000 | 0.508333 | 0.408333 | -0.001283 |
| PP-OPT65 | ppopt65_local_threshold__helper=pp48score_pp20__base=0p32__vh=0p08__lowconf=0p08__width=0p36__s=0p92 | pp64_local_threshold_grid | 0.137878 | 0.270586 | 0.807464 | -0.000809 | -0.000666 | 1.000000 | 0.508333 | 0.408333 | -0.001285 |
| PP-OPT65 | ppopt65_local_threshold__helper=pp48score_pp20__base=0p32__vh=0p06__lowconf=0p1__width=0p36__s=0p92 | pp64_local_threshold_grid | 0.137878 | 0.270586 | 0.807464 | -0.000809 | -0.000666 | 1.000000 | 0.508333 | 0.408333 | -0.001285 |
| PP-OPT65 | ppopt65_local_threshold__helper=pp48score_pp20__base=0p32__vh=0p1__lowconf=0p06__width=0p36__s=0p92 | pp64_local_threshold_grid | 0.137878 | 0.270586 | 0.807464 | -0.000809 | -0.000666 | 1.000000 | 0.508333 | 0.408333 | -0.001284 |
| PP-OPT65 | ppopt65_local_threshold__helper=pp48score_pp20__base=0p32__vh=0p06__lowconf=0p08__width=0p36__s=0p92 | pp64_local_threshold_grid | 0.137878 | 0.270586 | 0.807464 | -0.000808 | -0.000666 | 1.000000 | 0.508333 | 0.408333 | -0.001285 |
| PP-OPT65 | ppopt65_local_threshold__helper=pp48score_pp20__base=0p32__vh=0p04__lowconf=0p1__width=0p36__s=0p92 | pp64_local_threshold_grid | 0.137878 | 0.270586 | 0.807464 | -0.000808 | -0.000666 | 1.000000 | 0.508333 | 0.408333 | -0.001286 |
| PP-OPT65 | ppopt65_local_threshold__helper=pp48score_pp20__base=0p32__vh=0p08__lowconf=0p06__width=0p36__s=0p92 | pp64_local_threshold_grid | 0.137878 | 0.270587 | 0.807464 | -0.000808 | -0.000666 | 1.000000 | 0.508333 | 0.408333 | -0.001284 |
| PP-OPT65 | ppopt65_local_threshold__helper=pp48score_pp20__base=0p32__vh=0p04__lowconf=0p08__width=0p36__s=0p92 | pp64_local_threshold_grid | 0.137878 | 0.270587 | 0.807464 | -0.000808 | -0.000666 | 1.000000 | 0.508333 | 0.408333 | -0.001286 |
| PP-OPT65 | ppopt65_local_threshold__helper=pp48score_pp20__base=0p32__vh=0p06__lowconf=0p06__width=0p36__s=0p92 | pp64_local_threshold_grid | 0.137878 | 0.270587 | 0.807464 | -0.000808 | -0.000666 | 1.000000 | 0.508333 | 0.408333 | -0.001285 |
| PP-OPT65 | ppopt65_local_threshold__helper=pp48score_pp20__base=0p32__vh=0p04__lowconf=0p06__width=0p36__s=0p92 | pp64_local_threshold_grid | 0.137878 | 0.270588 | 0.807464 | -0.000807 | -0.000666 | 1.000000 | 0.508333 | 0.408333 | -0.001285 |
| PP-OPT65 | ppopt65_local_threshold__helper=pp48score_pp20__base=0p32__vh=0p12__lowconf=0p04__width=0p36__s=0p92 | pp64_local_threshold_grid | 0.137878 | 0.270586 | 0.807466 | -0.000809 | -0.000664 | 1.000000 | 0.508333 | 0.408333 | -0.001283 |
| PP-OPT65 | ppopt65_local_threshold__helper=pp48score_pp20__base=0p32__vh=0p1__lowconf=0p04__width=0p36__s=0p92 | pp64_local_threshold_grid | 0.137878 | 0.270587 | 0.807466 | -0.000808 | -0.000664 | 1.000000 | 0.508333 | 0.408333 | -0.001283 |
| PP-OPT65 | ppopt65_local_threshold__helper=pp48score_pp20__base=0p32__vh=0p08__lowconf=0p04__width=0p36__s=0p92 | pp64_local_threshold_grid | 0.137878 | 0.270588 | 0.807466 | -0.000807 | -0.000664 | 1.000000 | 0.508333 | 0.408333 | -0.001284 |
| PP-OPT65 | ppopt65_local_threshold__helper=pp48score_pp20__base=0p32__vh=0p06__lowconf=0p04__width=0p36__s=0p92 | pp64_local_threshold_grid | 0.137878 | 0.270588 | 0.807466 | -0.000807 | -0.000664 | 1.000000 | 0.508333 | 0.408333 | -0.001284 |
| PP-OPT65 | ppopt65_local_threshold__helper=pp48score_pp20__base=0p32__vh=0p04__lowconf=0p04__width=0p36__s=0p92 | pp64_local_threshold_grid | 0.137878 | 0.270589 | 0.807466 | -0.000806 | -0.000664 | 1.000000 | 0.508333 | 0.408333 | -0.001285 |
| PP-OPT66 | ppopt66_tail_guard__helper=pp20__score=risk__thr=0p54__width=0p22__s=0p44 | pp64_tail_only_fallback_guard | 0.137878 | 0.270592 | 0.807468 | -0.000803 | -0.000662 | 1.000000 | 0.508333 | 0.412500 | -0.001315 |
| PP-OPT65 | ppopt65_local_threshold__helper=pp48score_pp20__base=0p32__vh=0p12__lowconf=0p02__width=0p36__s=0p92 | pp64_local_threshold_grid | 0.137878 | 0.270588 | 0.807470 | -0.000807 | -0.000660 | 1.000000 | 0.508333 | 0.408333 | -0.001282 |
| PP-OPT65 | ppopt65_local_threshold__helper=pp48score_pp20__base=0p32__vh=0p1__lowconf=0p02__width=0p36__s=0p92 | pp64_local_threshold_grid | 0.137878 | 0.270588 | 0.807470 | -0.000807 | -0.000660 | 1.000000 | 0.508333 | 0.408333 | -0.001282 |
| PP-OPT65 | ppopt65_local_threshold__helper=pp48score_pp20__base=0p32__vh=0p08__lowconf=0p02__width=0p36__s=0p92 | pp64_local_threshold_grid | 0.137878 | 0.270589 | 0.807470 | -0.000806 | -0.000660 | 1.000000 | 0.508333 | 0.408333 | -0.001283 |
| PP-OPT65 | ppopt65_local_threshold__helper=pp48score_pp20__base=0p32__vh=0p06__lowconf=0p02__width=0p36__s=0p92 | pp64_local_threshold_grid | 0.137878 | 0.270590 | 0.807470 | -0.000805 | -0.000660 | 1.000000 | 0.508333 | 0.408333 | -0.001283 |
| PP-OPT65 | ppopt65_local_threshold__helper=pp48score_pp20__base=0p32__vh=0p04__lowconf=0p02__width=0p36__s=0p92 | pp64_local_threshold_grid | 0.137878 | 0.270590 | 0.807470 | -0.000805 | -0.000660 | 1.000000 | 0.508333 | 0.408333 | -0.001285 |
| PP-OPT65 | ppopt65_local_threshold__helper=pp48score_pp20__base=0p32__vh=0p12__lowconf=0p1__width=0p36__s=0p88 | pp64_local_threshold_grid | 0.137878 | 0.270584 | 0.807472 | -0.000811 | -0.000657 | 1.000000 | 0.508333 | 0.408333 | -0.001285 |
| PP-OPT65 | ppopt65_local_threshold__helper=pp48score_pp20__base=0p32__vh=0p1__lowconf=0p1__width=0p36__s=0p88 | pp64_local_threshold_grid | 0.137878 | 0.270585 | 0.807472 | -0.000810 | -0.000657 | 1.000000 | 0.508333 | 0.408333 | -0.001285 |
| PP-OPT65 | ppopt65_local_threshold__helper=pp48score_pp20__base=0p32__vh=0p12__lowconf=0p08__width=0p36__s=0p88 | pp64_local_threshold_grid | 0.137878 | 0.270585 | 0.807472 | -0.000810 | -0.000657 | 1.000000 | 0.508333 | 0.408333 | -0.001284 |
| PP-OPT65 | ppopt65_local_threshold__helper=pp48score_pp20__base=0p32__vh=0p08__lowconf=0p1__width=0p36__s=0p88 | pp64_local_threshold_grid | 0.137878 | 0.270586 | 0.807472 | -0.000809 | -0.000657 | 1.000000 | 0.508333 | 0.408333 | -0.001285 |
| PP-OPT65 | ppopt65_local_threshold__helper=pp48score_pp20__base=0p32__vh=0p1__lowconf=0p08__width=0p36__s=0p88 | pp64_local_threshold_grid | 0.137878 | 0.270586 | 0.807472 | -0.000809 | -0.000657 | 1.000000 | 0.508333 | 0.408333 | -0.001285 |

## 해석
- PP65는 PP64와 같은 구조에서 threshold만 좁게 움직여, 기존 PP64가 우연한 단일 조합인지 확인한다.
- PP66은 tail row만 안정 후보로 후퇴시켜 p95 개선 가능성을 본다.
- PP67은 quantile 잔차 방향이 명확한 경우에만 작은 보정값을 더해 MAPE 개선 가능성을 확인한다.
- PP68은 PP64 보정량이 과한 구간이 있는지 확인하기 위한 shrinkage 실험이다.
- PP69는 위험도에 따라 PP64를 MAPE 후보와 안정 후보 사이에서 동적으로 섞는 실험이다.

## 실행 설정
```json
{
  "experiment_id": "PP-OPT65-70",
  "experiment_slug": "PP-OPT65_70_warm_pp64_refinement_experiments",
  "created_at": "2026-06-09T12:51:03",
  "seed": 20260609,
  "base_candidate": "hcoef_stable",
  "incumbent_candidate": "incumbent_operational_pp_opt7",
  "previous_challenger": "previous_challenger_pp20",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 4723,
  "prediction_rows": 5318098,
  "items": [
    {
      "item_id": "PP-OPT65",
      "priority": "1",
      "title": "PP64 segment threshold local fine grid",
      "description": "PP64의 핵심 구조를 유지하고 rollback threshold, width, strength만 좁은 범위에서 다시 탐색한다."
    },
    {
      "item_id": "PP-OPT66",
      "priority": "2",
      "title": "PP64 tail-only fallback guard",
      "description": "tail 위험이 높은 row에서만 PP64를 PP48/PP20 등 안정 후보 쪽으로 약하게 되돌린다."
    },
    {
      "item_id": "PP-OPT67",
      "priority": "3",
      "title": "quantile consensus micro correction on PP64",
      "description": "잔차 quantile 방향이 일치할 때만 PP64 위에 아주 작은 보정을 더한다."
    },
    {
      "item_id": "PP-OPT68",
      "priority": "4",
      "title": "PP64 correction shrinkage by risk segment",
      "description": "PP52에서 PP64로 이동한 rollback 보정량을 위험 구간별로 줄이거나 유지한다."
    },
    {
      "item_id": "PP-OPT69",
      "priority": "5",
      "title": "PP64 stability dynamic blend",
      "description": "위험이 낮은 row는 PP64/PP52 쪽, 위험이 높은 row는 PP48/PP20 쪽으로 동적 혼합한다."
    },
    {
      "item_id": "PP-OPT70",
      "priority": "6",
      "title": "최종 PP64 refinement challenger 선택",
      "description": "PP64 대비 MAPE와 p95의 균형을 기준으로 최종 후보를 선택한다."
    }
  ],
  "selected_references": {
    "pp20": "previous_challenger_pp20",
    "pp30": "reference_pp30_best",
    "pp45": "reference_pp45_challenger",
    "pp48_score": "reference_pp48_score",
    "pp52": "reference_pp52_challenger",
    "pp58": "reference_pp58_challenger",
    "pp64": "ppopt64_p95_guard_challenger__source=ppopt62_segment_threshold__helper_pp48_score__base_0p36__vh_0p08__lowconf_0p06__s_0p85"
  },
  "selection_decision": {
    "selected_source_candidate": "ppopt68_shrinkage__global=1p04__risk=0p7__vh=0p82__lowconf=0p78",
    "selected_source_item_id": "PP-OPT68",
    "selected_source_family": "pp64_risk_segment_shrinkage",
    "selection_reason": "prefer MAPE not worse than PP64 with p95 neutral; fallback to p95 improvement within 0.00003 MAPE loss",
    "reference_pp64_test_MAPE": 0.27056404191566036,
    "reference_pp64_test_p95_APE": 0.8074988523061098,
    "delta_vs_pp64_MAPE": -3.0665386839823228e-06,
    "delta_vs_pp64_p95_APE": -8.791408261932254e-06,
    "test_MdAPE": 0.13787846966744394,
    "test_MAPE": 0.2705609753769764,
    "test_p95_APE": 0.8074900608978479,
    "test_delta_vs_incumbent_MAPE": -0.0008339126350900838,
    "test_delta_vs_incumbent_p95_APE": -0.0006399218156207809,
    "recommendation_score_vs_incumbent": -0.0013248233276436719,
    "protocol_candidate": "ppopt70_pp64_refinement_challenger__source=ppopt68_shrinkage__global_1p04__risk_0p7__vh_0p82__lowconf_0p78"
  },
  "sources": {
    "pp_opt59_config": "experiments/track6/PP-OPT59_64_warm_p95_guard_experiments/artifacts/run_config.json",
    "pp_opt59_predictions": "experiments/track6/PP-OPT59_64_warm_p95_guard_experiments/outputs/candidate_predictions.csv",
    "pp_opt59_rollback_calibration": "experiments/track6/PP-OPT59_64_warm_p95_guard_experiments/artifacts/rollback_probability_calibration.csv",
    "pp_opt47_quantile": "experiments/track6/PP-OPT47_52_warm_residual_finetune_experiments/artifacts/quantile_residual_predictions.csv",
    "pp_opt59_helper": "scripts/track6/run_pp_opt59_64_warm_p95_guard_experiments.py"
  }
}
```