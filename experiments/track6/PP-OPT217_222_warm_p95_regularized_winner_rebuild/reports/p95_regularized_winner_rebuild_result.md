# PP-OPT217~222 Warm p95-regularized winner rebuild 결과

- 작성일: 2026-06-10 11:22
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 목적: PP216 p95-recovery의 p95 win-rate 회복 신호를 유지하면서 MAPE 손상 축소
- 결론: 운영 후보 MAPE 0.269889, p95 win rate 0.747115. 균형 후보 MAPE 0.269890, p95 win rate 0.747756. PP216 p95-recovery 대비 균형 후보 MAPE -0.000008.

## 주요 후보 test 비교
| candidate | family | item_id | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt222_mape_challenger_p95_regularized_rebuild__source=ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p24__basecap_0p006__shrink_0p9 | p95_regularized_rebuild_mape_selection | PP-OPT222 | 0.140975 | 0.269889 | 0.807326 | 0.397455 | -0.001506 | -0.000804 |
| ppopt222_operational_p95_regularized_rebuild__source=ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p24__basecap_0p0056__shrink_0p9 | p95_regularized_rebuild_operational_selection | PP-OPT222 | 0.140975 | 0.269889 | 0.807326 | 0.397455 | -0.001505 | -0.000804 |
| ppopt222_balanced_p95_regularized_rebuild__source=ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p24__basecap_0p0052__shrink_0p9 | p95_regularized_rebuild_balanced_selection | PP-OPT222 | 0.140975 | 0.269890 | 0.807326 | 0.397456 | -0.001505 | -0.000804 |
| ppopt210_operational_pp204_local_refinement__source=ppopt205_local_price_conf__thr_0p04__width_0p22__s_1p16__basecap_0p0055__shrink_0p9 | reference_prior | REFERENCE | 0.140975 | 0.269891 | 0.807326 | 0.397456 | -0.001504 | -0.000804 |
| ppopt204_operational_pp192_pp198_winner_router__source=ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_1p0__basecap_0p006__shrink_0p8 | reference_prior | REFERENCE | 0.140975 | 0.269894 | 0.807326 | 0.397456 | -0.001501 | -0.000804 |
| ppopt198_operational_segment_router_refinement__source=ppopt194_price_conf_refine__scorethr_0p02__mix_0p25__s_1p05__cap_0p006 | reference_prior | REFERENCE | 0.140975 | 0.269894 | 0.807326 | 0.397455 | -0.001501 | -0.000804 |
| ppopt216_p95_recovery_pp210_p95_recovery__source=ppopt215_p95_aware_rebuild__thr_0p02__p95thr_m0p0001__s_1p16__basecap_0p005__shrink_1p2 | reference_prior | REFERENCE | 0.140975 | 0.269898 | 0.807326 | 0.397460 | -0.001497 | -0.000804 |
| ppopt222_p95_recovery_p95_regularized_rebuild__source=ppopt216_p95_recovery_pp210_p95_recovery__source_ppopt215_p95_aware_rebuild__thr_0p02__p95thr_m0p0001__s_1p16__basecap_0 | p95_regularized_rebuild_p95_recovery_selection | PP-OPT222 | 0.140975 | 0.269898 | 0.807326 | 0.397460 | -0.001497 | -0.000804 |
| ppopt192_operational_pp180_pp186_risk_router__source=ppopt189_segment_router__seg_price_gap__scorethr_0p02__mix_0p75__s_0p95__cap_0p0025 | reference_prior | REFERENCE | 0.140975 | 0.269914 | 0.807326 | 0.397468 | -0.001481 | -0.000804 |
| ppopt180_operational_basis_generation_challenger__source=ppopt174_direct_basis__source_stack_huber_weighted__thr_0p08__s_0p3__cap_0p004 | reference_prior | REFERENCE | 0.140975 | 0.269933 | 0.807326 | 0.397475 | -0.001462 | -0.000804 |
| ppopt222_p95_guarded_p95_regularized_rebuild__source=ppopt210_p95_guarded_pp204_local_refinement__source_ppopt204_p95_guarded_pp192_pp198_winner_router__source_ppopt192_p95_ | p95_regularized_rebuild_p95_guarded_selection | PP-OPT222 | 0.140094 | 0.269949 | 0.807255 | 0.397482 | -0.001446 | -0.000875 |
| reference_pp126_operational | reference_prior | REFERENCE | 0.136320 | 0.270114 | 0.807490 | 0.397588 | -0.001280 | -0.000640 |
| reference_pp148_operational | reference_prior | REFERENCE | 0.139801 | 0.270140 | 0.807231 | 0.397525 | -0.001255 | -0.000899 |
| reference_pp148_p95 | reference_prior | REFERENCE | 0.141036 | 0.270269 | 0.805949 | 0.397421 | -0.001126 | -0.002181 |
| ppopt222_p95_extreme_p95_regularized_rebuild__source=reference_pp148_p95 | p95_regularized_rebuild_p95_extreme_selection | PP-OPT222 | 0.141036 | 0.270269 | 0.805949 | 0.397421 | -0.001126 | -0.002181 |
| reference_pp64_current_best | reference_prior | REFERENCE | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | p95_test_MAPE | p95_test_p95_APE | operational_pass_vs_incumbent | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | final p95-regularized rebuild decision | 6 | 0.269949 | 0.807255 | 0.270269 | 0.805949 | False | p95_regularized_rebuild_p95_guarded_selection | ppopt222_p95_guarded_p95_regularized_rebuild__source=ppopt210_p95_guarded_pp204_local_refinement__source_ppopt204_p95_guarded_pp192_pp198_winner_router__source_ppopt192_p95_ |
| 1 | p95-regularized winner rebuild local search | 1152 | 0.269891 | 0.807326 | 0.269889 | 0.807326 | False | p95_regularized_winner_rebuild | ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m0p00014__p95width=0p00012__s=1p24__basecap=0p006__shrink=1p05 |
| 3 | global plus gated p95 recovery blend | 48 | 0.269891 | 0.807326 | 0.269891 | 0.807326 | False | global_plus_gated_p95_recovery_blend | ppopt219_global_plus_recovery__global=0p05__gated=0p18__cap=0p0004 |
| 2 | PP210 to p95-recovery gated route | 144 | 0.269891 | 0.807326 | 0.269891 | 0.807326 | False | pp210_to_p95_recovery_route | ppopt218_route_to_recovery__seg=price_qwidth__thr=m0p05__s=0p55__cap=0p0004 |
| 4 | three-way PP210/PP204/recovery route | 36 | 0.269891 | 0.807326 | 0.269891 | 0.807326 | False | three_way_pp210_pp204_recovery_route | ppopt220_three_way_route__recshare=0p3__s=0p18__cap=0p0004 |

## 탐색 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt222_p95_guarded_p95_regularized_rebuild__source=ppopt210_p95_guarded_pp204_local_refinement__source_ppopt204_p95_guarded_pp192_pp198_winner_router__source_ppopt192_p95_ | PP-OPT222 | p95_regularized_rebuild_p95_guarded_selection | 0.269949 | 0.807255 | -0.001446 | -0.000875 | -0.001537 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m0p00014__p95width=0p00012__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m0p00014__p95width=8em05__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m0p0001__p95width=0p00012__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m0p0001__p95width=8em05__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m2em05__p95width=0p00012__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m2em05__p95width=8em05__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m6em05__p95width=0p00012__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m6em05__p95width=8em05__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m0p00014__p95width=0p00012__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m0p00014__p95width=8em05__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m0p0001__p95width=0p00012__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m0p0001__p95width=8em05__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m2em05__p95width=0p00012__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m2em05__p95width=8em05__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m6em05__p95width=0p00012__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m6em05__p95width=8em05__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m0p00014__p95width=0p00012__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m0p00014__p95width=8em05__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m0p0001__p95width=0p00012__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m0p0001__p95width=8em05__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m2em05__p95width=0p00012__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m2em05__p95width=8em05__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m6em05__p95width=0p00012__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m6em05__p95width=8em05__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m0p00014__p95width=0p00012__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m0p00014__p95width=8em05__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m0p0001__p95width=0p00012__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m0p0001__p95width=8em05__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m2em05__p95width=0p00012__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m2em05__p95width=8em05__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m6em05__p95width=0p00012__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m6em05__p95width=8em05__s=1p24__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m0p00014__p95width=0p00012__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m0p00014__p95width=8em05__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m0p0001__p95width=0p00012__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m0p0001__p95width=8em05__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m2em05__p95width=0p00012__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m2em05__p95width=8em05__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m6em05__p95width=0p00012__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m6em05__p95width=8em05__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m0p00014__p95width=0p00012__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m0p00014__p95width=8em05__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m0p0001__p95width=0p00012__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m0p0001__p95width=8em05__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m2em05__p95width=0p00012__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m2em05__p95width=8em05__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m6em05__p95width=0p00012__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m6em05__p95width=8em05__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m0p00014__p95width=0p00012__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m0p00014__p95width=8em05__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m0p0001__p95width=0p00012__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m0p0001__p95width=8em05__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m2em05__p95width=0p00012__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m2em05__p95width=8em05__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m6em05__p95width=0p00012__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m6em05__p95width=8em05__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m0p00014__p95width=0p00012__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m0p00014__p95width=8em05__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m0p0001__p95width=0p00012__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m0p0001__p95width=8em05__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m2em05__p95width=0p00012__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m2em05__p95width=8em05__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m6em05__p95width=0p00012__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m6em05__p95width=8em05__s=1p24__basecap=0p0052__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt222_balanced_p95_regularized_rebuild__source=ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p24__basecap_0p0052__shrink_0p9 | PP-OPT222 | p95_regularized_rebuild_balanced_selection | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001386 |
| ppopt222_p95_recovery_p95_regularized_rebuild__source=ppopt216_p95_recovery_pp210_p95_recovery__source_ppopt215_p95_aware_rebuild__thr_0p02__p95thr_m0p0001__s_1p16__basecap_0 | PP-OPT222 | p95_regularized_rebuild_p95_recovery_selection | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m0p00014__p95width=0p00012__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m0p00014__p95width=8em05__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m0p0001__p95width=0p00012__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m0p0001__p95width=8em05__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m2em05__p95width=0p00012__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m2em05__p95width=8em05__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m6em05__p95width=0p00012__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m6em05__p95width=8em05__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m0p00014__p95width=0p00012__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m0p00014__p95width=8em05__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m0p0001__p95width=0p00012__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m0p0001__p95width=8em05__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m2em05__p95width=0p00012__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m2em05__p95width=8em05__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m6em05__p95width=0p00012__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m6em05__p95width=8em05__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m0p00014__p95width=0p00012__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m0p00014__p95width=8em05__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m0p0001__p95width=0p00012__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m0p0001__p95width=8em05__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m2em05__p95width=0p00012__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m2em05__p95width=8em05__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m6em05__p95width=0p00012__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m6em05__p95width=8em05__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m0p00014__p95width=0p00012__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m0p00014__p95width=8em05__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m0p0001__p95width=0p00012__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m0p0001__p95width=8em05__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m2em05__p95width=0p00012__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m2em05__p95width=8em05__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m6em05__p95width=0p00012__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m6em05__p95width=8em05__s=1p16__basecap=0p006__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m0p00014__p95width=0p00012__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m0p00014__p95width=8em05__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m0p0001__p95width=0p00012__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m0p0001__p95width=8em05__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m2em05__p95width=0p00012__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m2em05__p95width=8em05__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m6em05__p95width=0p00012__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m6em05__p95width=8em05__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m0p00014__p95width=0p00012__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m0p00014__p95width=8em05__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m0p0001__p95width=0p00012__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m0p0001__p95width=8em05__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m2em05__p95width=0p00012__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m2em05__p95width=8em05__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m6em05__p95width=0p00012__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m6em05__p95width=8em05__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m0p00014__p95width=0p00012__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m0p00014__p95width=8em05__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m0p0001__p95width=0p00012__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m0p0001__p95width=8em05__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m2em05__p95width=0p00012__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m2em05__p95width=8em05__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m6em05__p95width=0p00012__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m6em05__p95width=8em05__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m0p00014__p95width=0p00012__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m0p00014__p95width=8em05__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m0p0001__p95width=0p00012__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m0p0001__p95width=8em05__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m2em05__p95width=0p00012__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m2em05__p95width=8em05__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m6em05__p95width=0p00012__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m6em05__p95width=8em05__s=1p24__basecap=0p0056__shrink=1p05 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001385 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m0p00014__p95width=0p00012__s=1p24__basecap=0p0048__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m0p00014__p95width=8em05__s=1p24__basecap=0p0048__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m0p0001__p95width=0p00012__s=1p24__basecap=0p0048__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m0p0001__p95width=8em05__s=1p24__basecap=0p0048__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m2em05__p95width=0p00012__s=1p24__basecap=0p0048__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m2em05__p95width=8em05__s=1p24__basecap=0p0048__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m6em05__p95width=0p00012__s=1p24__basecap=0p0048__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m6em05__p95width=8em05__s=1p24__basecap=0p0048__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m0p00014__p95width=0p00012__s=1p24__basecap=0p0048__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m0p00014__p95width=8em05__s=1p24__basecap=0p0048__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m0p0001__p95width=0p00012__s=1p24__basecap=0p0048__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m0p0001__p95width=8em05__s=1p24__basecap=0p0048__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m2em05__p95width=0p00012__s=1p24__basecap=0p0048__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m2em05__p95width=8em05__s=1p24__basecap=0p0048__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m6em05__p95width=0p00012__s=1p24__basecap=0p0048__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt217_p95_regularized_rebuild__thr=0p04__p95thr=m6em05__p95width=8em05__s=1p24__basecap=0p0048__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m0p00014__p95width=0p00012__s=1p24__basecap=0p0048__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m0p00014__p95width=8em05__s=1p24__basecap=0p0048__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m0p0001__p95width=0p00012__s=1p24__basecap=0p0048__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m0p0001__p95width=8em05__s=1p24__basecap=0p0048__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m2em05__p95width=0p00012__s=1p24__basecap=0p0048__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m2em05__p95width=8em05__s=1p24__basecap=0p0048__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m6em05__p95width=0p00012__s=1p24__basecap=0p0048__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt217_p95_regularized_rebuild__thr=0p08__p95thr=m6em05__p95width=8em05__s=1p24__basecap=0p0048__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m0p00014__p95width=0p00012__s=1p24__basecap=0p0048__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m0p00014__p95width=8em05__s=1p24__basecap=0p0048__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m0p0001__p95width=0p00012__s=1p24__basecap=0p0048__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m0p0001__p95width=8em05__s=1p24__basecap=0p0048__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt217_p95_regularized_rebuild__thr=0p0__p95thr=m2em05__p95width=0p00012__s=1p24__basecap=0p0048__shrink=0p9 | PP-OPT217 | p95_regularized_winner_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |

## 선택 후보 반복 안정성
| candidate_label | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_vs_pp64_MAPE | fixed_test_delta_vs_pp64_p95_APE | avg_pp64_MAPE_win_rate | avg_pp64_p95_win_rate | replacement_score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p24__basec__74bdd5eaba | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_8em05__s_1p24__basecap__1b228d5252 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p0001__p95width_0p00012__s_1p24__baseca__336a9bdf21 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p0001__p95width_8em05__s_1p24__basecap___989dd13f49 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m2em05__p95width_0p00012__s_1p24__basecap__7c04f9ee79 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m2em05__p95width_8em05__s_1p24__basecap_0__c6f06a099d | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m6em05__p95width_0p00012__s_1p24__basecap__67d37b4d35 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m6em05__p95width_8em05__s_1p24__basecap_0__39d4ecfcbe | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m0p00014__p95width_0p00012__s_1p24__basec__f4397ce5ec | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m0p00014__p95width_8em05__s_1p24__basecap__51628cb10f | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m0p0001__p95width_0p00012__s_1p24__baseca__cbd9227506 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m0p0001__p95width_8em05__s_1p24__basecap___97d2fec936 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m2em05__p95width_0p00012__s_1p24__basecap__f5ebf4e0e8 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m2em05__p95width_8em05__s_1p24__basecap_0__43f3bdfd7b | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m6em05__p95width_0p00012__s_1p24__basecap__fa9dd3b825 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m6em05__p95width_8em05__s_1p24__basecap_0__595db963e4 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m0p00014__p95width_0p00012__s_1p24__basec__21821d813e | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m0p00014__p95width_8em05__s_1p24__basecap__5b39111624 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m0p0001__p95width_0p00012__s_1p24__baseca__e8232aaa1b | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m0p0001__p95width_8em05__s_1p24__basecap___6a98affd09 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m2em05__p95width_0p00012__s_1p24__basecap__413c7f27a3 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m2em05__p95width_8em05__s_1p24__basecap_0__9d528669bd | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m6em05__p95width_0p00012__s_1p24__basecap__ec5018595c | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m6em05__p95width_8em05__s_1p24__basecap_0__f955af629a | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m0p00014__p95width_0p00012__s_1p24__baseca__81254aeaea | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m0p00014__p95width_8em05__s_1p24__basecap___c345663ecf | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m0p0001__p95width_0p00012__s_1p24__basecap__843d8168d2 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m0p0001__p95width_8em05__s_1p24__basecap_0__dcefc43a8d | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m2em05__p95width_0p00012__s_1p24__basecap___812ead1729 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m2em05__p95width_8em05__s_1p24__basecap_0p__5b1bc7bf62 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m6em05__p95width_0p00012__s_1p24__basecap___907b80fd6f | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m6em05__p95width_8em05__s_1p24__basecap_0p__8d76f7b611 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| pp222_operational_p95_regularized_rebuild_challenger | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p24__basec__54bfbf5146 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_8em05__s_1p24__basecap__625e015f73 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p0001__p95width_0p00012__s_1p24__baseca__53ad28ed2a | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p0001__p95width_8em05__s_1p24__basecap___40d9b6f377 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m2em05__p95width_0p00012__s_1p24__basecap__73661087f7 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m2em05__p95width_8em05__s_1p24__basecap_0__54f13eb7ad | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m6em05__p95width_0p00012__s_1p24__basecap__9cdb6297e2 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m6em05__p95width_8em05__s_1p24__basecap_0__91bc24536d | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m0p00014__p95width_0p00012__s_1p24__basec__ee2501a0a2 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m0p00014__p95width_8em05__s_1p24__basecap__822d949384 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m0p0001__p95width_0p00012__s_1p24__baseca__8e6f1ffa9c | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m0p0001__p95width_8em05__s_1p24__basecap___ae60abcb74 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m2em05__p95width_0p00012__s_1p24__basecap__342655f339 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m2em05__p95width_8em05__s_1p24__basecap_0__a2dcfd644d | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m6em05__p95width_0p00012__s_1p24__basecap__4e726493d9 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m6em05__p95width_8em05__s_1p24__basecap_0__6ceeb7dc8b | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m0p00014__p95width_0p00012__s_1p24__basec__cc96a45197 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m0p00014__p95width_8em05__s_1p24__basecap__61e51c9272 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m0p0001__p95width_0p00012__s_1p24__baseca__a3750a797d | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m0p0001__p95width_8em05__s_1p24__basecap___e2efa617a5 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m2em05__p95width_0p00012__s_1p24__basecap__30ee36a5ec | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m2em05__p95width_8em05__s_1p24__basecap_0__adf8a2e438 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m6em05__p95width_0p00012__s_1p24__basecap__fa485d0c13 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m6em05__p95width_8em05__s_1p24__basecap_0__c5095bfe84 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m0p00014__p95width_0p00012__s_1p24__baseca__1f6950d0f1 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m0p00014__p95width_8em05__s_1p24__basecap___faa976fd7f | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m0p0001__p95width_0p00012__s_1p24__basecap__53217716f6 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m0p0001__p95width_8em05__s_1p24__basecap_0__dce4b6a850 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m2em05__p95width_0p00012__s_1p24__basecap___a02753c510 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m2em05__p95width_8em05__s_1p24__basecap_0p__36aa8c694d | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m6em05__p95width_0p00012__s_1p24__basecap___90f399e0b5 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m6em05__p95width_8em05__s_1p24__basecap_0p__46e39b3a3b | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| pp222_balanced_p95_regularized_rebuild_challenger | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p24__basec__cd66f3fa59 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_8em05__s_1p24__basecap__f5330112d5 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p0001__p95width_0p00012__s_1p24__baseca__66754bf7b8 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p0001__p95width_8em05__s_1p24__basecap___2cf1d309ba | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m2em05__p95width_0p00012__s_1p24__basecap__c4d8958f34 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m2em05__p95width_8em05__s_1p24__basecap_0__1ae3c90678 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m6em05__p95width_0p00012__s_1p24__basecap__b423548611 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m6em05__p95width_8em05__s_1p24__basecap_0__f070a1d501 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m0p00014__p95width_0p00012__s_1p24__basec__0537302ed2 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m0p00014__p95width_8em05__s_1p24__basecap__5e9f0ba0d2 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m0p0001__p95width_0p00012__s_1p24__baseca__e65f619c9b | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m0p0001__p95width_8em05__s_1p24__basecap___14befe6adc | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m2em05__p95width_0p00012__s_1p24__basecap__ff717e3875 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m2em05__p95width_8em05__s_1p24__basecap_0__3b5c020749 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m6em05__p95width_0p00012__s_1p24__basecap__9578b1265a | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m6em05__p95width_8em05__s_1p24__basecap_0__d15811cd09 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m0p00014__p95width_0p00012__s_1p24__basec__a8b3b79d8f | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m0p00014__p95width_8em05__s_1p24__basecap__7d3c195120 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m0p0001__p95width_0p00012__s_1p24__baseca__5f8763c23d | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m0p0001__p95width_8em05__s_1p24__basecap___935f184dff | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m2em05__p95width_0p00012__s_1p24__basecap__eda4211760 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m2em05__p95width_8em05__s_1p24__basecap_0__84ffcfdbcf | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m6em05__p95width_0p00012__s_1p24__basecap__3c0c8e8c18 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m6em05__p95width_8em05__s_1p24__basecap_0__5c7ff050ae | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m0p00014__p95width_0p00012__s_1p24__baseca__bab9c04bca | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m0p00014__p95width_8em05__s_1p24__basecap___714aa0e543 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m0p0001__p95width_0p00012__s_1p24__basecap__f7d2339319 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m0p0001__p95width_8em05__s_1p24__basecap_0__0154586b50 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m2em05__p95width_0p00012__s_1p24__basecap___4dea39df67 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m2em05__p95width_8em05__s_1p24__basecap_0p__2f14b388fb | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m6em05__p95width_0p00012__s_1p24__basecap___0f60817abc | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m6em05__p95width_8em05__s_1p24__basecap_0p__26151259e9 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| pp210_operational_reference | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p24__basec__d83c5ab17b | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_8em05__s_1p24__basecap__62a085a9da | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p0001__p95width_0p00012__s_1p24__baseca__6b20b7ac3e | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p0001__p95width_8em05__s_1p24__basecap___bbd578f67a | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m2em05__p95width_0p00012__s_1p24__basecap__1cb9e18315 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m2em05__p95width_8em05__s_1p24__basecap_0__9708b972bb | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m6em05__p95width_0p00012__s_1p24__basecap__278232bc94 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m6em05__p95width_8em05__s_1p24__basecap_0__dce93a33de | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m0p00014__p95width_0p00012__s_1p24__basec__498147b69e | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m0p00014__p95width_8em05__s_1p24__basecap__bcc182fa88 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m0p0001__p95width_0p00012__s_1p24__baseca__d7cfc81fe9 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p16__basec__e00afdfe8b | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_8em05__s_1p16__basecap__e1c48ee1d7 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p0001__p95width_0p00012__s_1p16__baseca__2ba0c9b092 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p0001__p95width_8em05__s_1p16__basecap___a93a9d42c2 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m2em05__p95width_0p00012__s_1p16__basecap__00164e1849 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m2em05__p95width_8em05__s_1p16__basecap_0__51f47535d3 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m6em05__p95width_0p00012__s_1p16__basecap__c75a37f895 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m6em05__p95width_8em05__s_1p16__basecap_0__f8012adda7 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m0p00014__p95width_0p00012__s_1p16__basec__47d750e1f8 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m0p00014__p95width_8em05__s_1p16__basecap__bbc6bf7870 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m0p0001__p95width_0p00012__s_1p16__baseca__ef75779c0c | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m0p0001__p95width_8em05__s_1p16__basecap___f97630bf7c | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m2em05__p95width_0p00012__s_1p16__basecap__5dee17e994 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m2em05__p95width_8em05__s_1p16__basecap_0__922df8b66a | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m6em05__p95width_0p00012__s_1p16__basecap__d585bcfcdd | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m6em05__p95width_8em05__s_1p16__basecap_0__0c5a91c671 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m0p00014__p95width_0p00012__s_1p16__basec__351c35298b | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m0p00014__p95width_8em05__s_1p16__basecap__39cf6daeee | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m0p0001__p95width_0p00012__s_1p16__baseca__bdae480b58 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m0p0001__p95width_8em05__s_1p16__basecap___d809b007e6 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m2em05__p95width_0p00012__s_1p16__basecap__62eb535048 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m2em05__p95width_8em05__s_1p16__basecap_0__5912f602d2 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m6em05__p95width_0p00012__s_1p16__basecap__96375e2a8c | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m6em05__p95width_8em05__s_1p16__basecap_0__f602afe45f | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m0p00014__p95width_0p00012__s_1p16__baseca__783b5ad34e | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m0p00014__p95width_8em05__s_1p16__basecap___4700878cec | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m0p0001__p95width_0p00012__s_1p16__basecap__faa16d11ea | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m0p0001__p95width_8em05__s_1p16__basecap_0__7f6b955cde | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m2em05__p95width_0p00012__s_1p16__basecap___37d7ac489d | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m2em05__p95width_8em05__s_1p16__basecap_0p__1f48b66901 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m6em05__p95width_0p00012__s_1p16__basecap___d5f3c155a0 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m6em05__p95width_8em05__s_1p16__basecap_0p__198925d0e9 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p24__basec__ded187c2af | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_8em05__s_1p24__basecap__d320d94e7c | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p0001__p95width_0p00012__s_1p24__baseca__5d500375ba | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p0001__p95width_8em05__s_1p24__basecap___72fc0d0ea5 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m2em05__p95width_0p00012__s_1p24__basecap__32525a8c4b | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m2em05__p95width_8em05__s_1p24__basecap_0__66dc2aad3d | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m6em05__p95width_0p00012__s_1p24__basecap__d407cdc72e | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m6em05__p95width_8em05__s_1p24__basecap_0__dafc5ae482 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m0p00014__p95width_0p00012__s_1p24__basec__bcd8ea9aa6 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m0p00014__p95width_8em05__s_1p24__basecap__d8cff144eb | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m0p0001__p95width_0p00012__s_1p24__baseca__888b4ef26b | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m0p0001__p95width_8em05__s_1p24__basecap___a5e8c93c79 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m2em05__p95width_0p00012__s_1p24__basecap__701f4fe46e | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m2em05__p95width_8em05__s_1p24__basecap_0__b565b4dbcc | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m6em05__p95width_0p00012__s_1p24__basecap__51ab5bb971 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p04__p95thr_m6em05__p95width_8em05__s_1p24__basecap_0__c48e6cf463 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m0p00014__p95width_0p00012__s_1p24__basec__1cf9a0a5ce | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m0p00014__p95width_8em05__s_1p24__basecap__ccc760bd65 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m0p0001__p95width_0p00012__s_1p24__baseca__0cfb7aafb9 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m0p0001__p95width_8em05__s_1p24__basecap___2aa9013bb5 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m2em05__p95width_0p00012__s_1p24__basecap__b8cfd9bf5e | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m2em05__p95width_8em05__s_1p24__basecap_0__6fc9bbb5eb | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m6em05__p95width_0p00012__s_1p24__basecap__b0ea5c3bb8 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p08__p95thr_m6em05__p95width_8em05__s_1p24__basecap_0__a64c410dc7 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m0p00014__p95width_0p00012__s_1p24__baseca__f992eb3e7c | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m0p00014__p95width_8em05__s_1p24__basecap___1bf5d4b66c | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m0p0001__p95width_0p00012__s_1p24__basecap__f9694e2de7 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m0p0001__p95width_8em05__s_1p24__basecap_0__5e77b64220 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m2em05__p95width_0p00012__s_1p24__basecap___6b7035edb2 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m2em05__p95width_8em05__s_1p24__basecap_0p__b2fac2a0ad | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m6em05__p95width_0p00012__s_1p24__basecap___46825ad223 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p0__p95thr_m6em05__p95width_8em05__s_1p24__basecap_0p__ebfe32ffe3 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| pp204_operational_reference | 0.269894 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018824 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p24__basec__43963d52eb | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953526 | 0.747115 | -0.018816 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_8em05__s_1p24__basecap__bebffb670c | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953526 | 0.747115 | -0.018816 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p0001__p95width_0p00012__s_1p24__baseca__0e467cb945 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953526 | 0.747115 | -0.018816 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p0001__p95width_8em05__s_1p24__basecap___1760d082e5 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953526 | 0.747115 | -0.018816 |
| candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m2em05__p95width_0p00012__s_1p24__basecap__738131b22e | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953526 | 0.747115 | -0.018816 |

## 실행 설정
```json
{
  "experiment_id": "PP-OPT217-222",
  "experiment_slug": "PP-OPT217_222_warm_p95_regularized_winner_rebuild",
  "created_at": "2026-06-10T11:22:20",
  "base_candidate": "hcoef_stable",
  "previous_experiment": "experiments/track6/PP-OPT211_216_warm_pp210_p95_win_recovery_router",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 1421,
  "prediction_rows": 1600046,
  "support_candidates": {
    "pp166_operational": "ppopt166_operational_pp157_negative_gate_challenger__source=ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap008__seg_price_conf__hw_1p2__thr_0p0__s_1p0__cap_0p006",
    "pp166_p95": "ppopt166_p95_pp157_negative_gate_challenger__source=reference_pp148_p95",
    "pp148_operational": "reference_pp148_operational",
    "pp148_p95": "reference_pp148_p95",
    "pp161_p95_guard": "ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s100_cap008__hthr=0p3__w=0p14__rb=1p0__s=1p0__cap=0p006",
    "pp162_p95_gate": "ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap008__thr=0p18__w=0p1__hpen=0p5__s=1p0__cap=0p006",
    "pp164_p95_block": "ppopt164_hard_block__target=pp157_price_qwidth_q084_s100_cap008__hthr=0p45__gthr=0p12__s=1p0__cap=0p006",
    "pp172_operational": "ppopt172_operational_pp166_tail_calibration_challenger__source=ppopt169_segment_router__source_pp162_p95_gate__seg_price_conf__thr_m0p04__s_0p5__cap_0p004",
    "pp172_p95": "ppopt172_p95_pp166_tail_calibration_challenger__source=reference_pp148_p95",
    "pp180_operational": "ppopt180_operational_basis_generation_challenger__source=ppopt174_direct_basis__source_stack_huber_weighted__thr_0p08__s_0p3__cap_0p004",
    "pp180_p95": "ppopt180_p95_basis_generation_challenger__source=reference_pp148_p95",
    "pp186_operational": "ppopt186_operational_huber_basis_p95_guard__source=ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p04__s_0p42__cap_0p0045",
    "pp186_strict": "ppopt186_strict_guarded_huber_basis_p95_guard__source=ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p04__s_0p42__cap_0p0045",
    "pp186_p95": "ppopt186_p95_huber_basis_p95_guard__source=reference_pp148_p95",
    "pp192_operational": "ppopt192_operational_pp180_pp186_risk_router__source=ppopt189_segment_router__seg_price_gap__scorethr_0p02__mix_0p75__s_0p95__cap_0p0025",
    "pp192_p95_guarded": "ppopt192_p95_guarded_pp180_pp186_risk_router__source=ppopt187_hard_risk_router__risk_uncertainty__mode_hard__thr_0p78__w_0p06__s_0p75",
    "pp192_p95_extreme": "ppopt192_p95_extreme_pp180_pp186_risk_router__source=reference_pp148_p95",
    "pp198_operational": "ppopt198_operational_segment_router_refinement__source=ppopt194_price_conf_refine__scorethr_0p02__mix_0p25__s_1p05__cap_0p006",
    "pp198_p95_guarded": "ppopt198_p95_guarded_segment_router_refinement__source=ppopt192_p95_guarded_pp180_pp186_risk_router__source_ppopt187_hard_risk_router__risk_uncertainty__mode_hard__thr_0p78__w",
    "pp198_p95_extreme": "ppopt198_p95_extreme_segment_router_refinement__source=reference_pp148_p95",
    "pp204_operational": "ppopt204_operational_pp192_pp198_winner_router__source=ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_1p0__basecap_0p006__shrink_0p8",
    "pp204_mape": "ppopt204_mape_challenger_pp192_pp198_winner_router__source=ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_1p0__basecap_0p006__shrink_0p8",
    "pp204_p95_guarded": "ppopt204_p95_guarded_pp192_pp198_winner_router__source=ppopt192_p95_guarded_pp180_pp186_risk_router__source_ppopt187_hard_risk_router__risk_uncertainty__mode_hard__thr_0p78__w",
    "pp204_p95_extreme": "ppopt204_p95_extreme_pp192_pp198_winner_router__source=reference_pp148_p95",
    "pp210_operational": "ppopt210_operational_pp204_local_refinement__source=ppopt205_local_price_conf__thr_0p04__width_0p22__s_1p16__basecap_0p0055__shrink_0p9",
    "pp210_mape": "ppopt210_mape_challenger_pp204_local_refinement__source=ppopt205_local_price_conf__thr_0p04__width_0p22__s_1p16__basecap_0p0065__shrink_0p65",
    "pp210_p95_guarded": "ppopt210_p95_guarded_pp204_local_refinement__source=ppopt204_p95_guarded_pp192_pp198_winner_router__source_ppopt192_p95_guarded_pp180_pp186_risk_router__source_ppopt187_har",
    "pp210_p95_extreme": "ppopt210_p95_extreme_pp204_local_refinement__source=reference_pp148_p95",
    "pp216_operational": "ppopt216_operational_pp210_p95_recovery__source=ppopt211_segment_recovery__seg_price_conf__thr_0p08__s_0p25__cap_0p0005",
    "pp216_p95_recovery": "ppopt216_p95_recovery_pp210_p95_recovery__source=ppopt215_p95_aware_rebuild__thr_0p02__p95thr_m0p0001__s_1p16__basecap_0p005__shrink_1p2",
    "pp216_mape": "ppopt216_mape_challenger_pp210_p95_recovery__source=ppopt210_mape_challenger_pp204_local_refinement__source_ppopt205_local_price_conf__thr_0p04__width_0p22__s_1p16__basecap",
    "pp216_p95_guarded": "ppopt216_p95_guarded_pp210_p95_recovery__source=ppopt210_p95_guarded_pp204_local_refinement__source_ppopt204_p95_guarded_pp192_pp198_winner_router__source_ppopt192_p95_",
    "pp216_p95_extreme": "ppopt216_p95_extreme_pp210_p95_recovery__source=reference_pp148_p95"
  },
  "selection_decision": {
    "operational_label": "candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p24__basec__74bdd5eaba",
    "operational_candidate": "ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m0p00014__p95width=0p00012__s=1p24__basecap=0p0056__shrink=0p9",
    "operational_fixed_test_MAPE": 0.26988949770443443,
    "operational_fixed_test_p95_APE": 0.8073255046591389,
    "operational_delta_vs_pp64_MAPE": -0.0006745442112259248,
    "operational_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "operational_delta_vs_pp204_MAPE": -4.023566731903294e-06,
    "operational_delta_vs_pp204_p95_APE": 0.0,
    "operational_delta_vs_pp210_MAPE": -1.503125739876765e-06,
    "operational_delta_vs_pp210_p95_APE": 0.0,
    "operational_delta_vs_pp216_recovery_MAPE": -8.144177535251984e-06,
    "operational_delta_vs_pp216_recovery_p95_win_rate": -0.002564102564102555,
    "operational_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "operational_avg_pp64_p95_win_rate": 0.7471153846153845,
    "operational_replacement_score": -0.01882839036507208,
    "balanced_label": "candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p24__basec__54bfbf5146",
    "balanced_candidate": "ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m0p00014__p95width=0p00012__s=1p24__basecap=0p0052__shrink=0p9",
    "balanced_fixed_test_MAPE": 0.26988999773577327,
    "balanced_fixed_test_p95_APE": 0.8073255046591389,
    "balanced_delta_vs_pp64_MAPE": -0.00067404417988709,
    "balanced_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "balanced_delta_vs_pp204_MAPE": -3.5235353930684887e-06,
    "balanced_delta_vs_pp204_p95_APE": 0.0,
    "balanced_delta_vs_pp210_MAPE": -1.0030944010419596e-06,
    "balanced_delta_vs_pp210_p95_APE": 0.0,
    "balanced_delta_vs_pp216_recovery_MAPE": -7.644146196417179e-06,
    "balanced_delta_vs_pp216_recovery_p95_win_rate": -0.0019230769230769162,
    "balanced_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "balanced_avg_pp64_p95_win_rate": 0.7477564102564102,
    "balanced_replacement_score": -0.018827890333733246,
    "p95_recovery_label": "pp216_p95_recovery_reference",
    "p95_recovery_candidate": "ppopt216_p95_recovery_pp210_p95_recovery__source=ppopt215_p95_aware_rebuild__thr_0p02__p95thr_m0p0001__s_1p16__basecap_0p005__shrink_1p2",
    "p95_recovery_fixed_test_MAPE": 0.2698976418819697,
    "p95_recovery_fixed_test_p95_APE": 0.8073255046591389,
    "p95_recovery_delta_vs_pp64_MAPE": -0.0006664000336906728,
    "p95_recovery_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "p95_recovery_delta_vs_pp204_MAPE": 4.12061080334869e-06,
    "p95_recovery_delta_vs_pp204_p95_APE": 0.0,
    "p95_recovery_delta_vs_pp210_MAPE": 6.641051795375219e-06,
    "p95_recovery_delta_vs_pp210_p95_APE": 0.0,
    "p95_recovery_delta_vs_pp216_recovery_MAPE": 0.0,
    "p95_recovery_delta_vs_pp216_recovery_p95_win_rate": 0.0,
    "p95_recovery_avg_pp64_MAPE_win_rate": 0.9528846153846153,
    "p95_recovery_avg_pp64_p95_win_rate": 0.7496794871794871,
    "p95_recovery_replacement_score": -0.018781784649075286,
    "mape_challenger_label": "candidate_ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p24__basec__43963d52eb",
    "mape_challenger_candidate": "ppopt217_p95_regularized_rebuild__thr=0p02__p95thr=m0p00014__p95width=0p00012__s=1p24__basecap=0p006__shrink=0p9",
    "mape_challenger_fixed_test_MAPE": 0.26988937611067,
    "mape_challenger_fixed_test_p95_APE": 0.8073255046591389,
    "mape_challenger_delta_vs_pp64_MAPE": -0.0006746658049903709,
    "mape_challenger_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "mape_challenger_delta_vs_pp204_MAPE": -4.145160496349387e-06,
    "mape_challenger_delta_vs_pp204_p95_APE": 0.0,
    "mape_challenger_delta_vs_pp210_MAPE": -1.624719504322858e-06,
    "mape_challenger_delta_vs_pp210_p95_APE": 0.0,
    "mape_challenger_delta_vs_pp216_recovery_MAPE": -8.265771299698077e-06,
    "mape_challenger_delta_vs_pp216_recovery_p95_win_rate": -0.002564102564102555,
    "mape_challenger_avg_pp64_MAPE_win_rate": 0.953525641025641,
    "mape_challenger_avg_pp64_p95_win_rate": 0.7471153846153845,
    "mape_challenger_replacement_score": -0.01881569144601601,
    "p95_guarded_label": "pp210_p95_guarded_reference",
    "p95_guarded_candidate": "ppopt210_p95_guarded_pp204_local_refinement__source=ppopt204_p95_guarded_pp192_pp198_winner_router__source_ppopt192_p95_guarded_pp180_pp186_risk_router__source_ppopt187_har",
    "p95_guarded_fixed_test_MAPE": 0.26994920114208765,
    "p95_guarded_fixed_test_p95_APE": 0.8072545738314347,
    "p95_guarded_delta_vs_pp64_MAPE": -0.0006148407735727113,
    "p95_guarded_delta_vs_pp64_p95_APE": -0.0002442784746751192,
    "p95_guarded_delta_vs_pp204_MAPE": 5.5679870921310215e-05,
    "p95_guarded_delta_vs_pp204_p95_APE": -7.093082770415204e-05,
    "p95_guarded_delta_vs_pp210_MAPE": 5.8200311913336744e-05,
    "p95_guarded_delta_vs_pp210_p95_APE": -7.093082770415204e-05,
    "p95_guarded_delta_vs_pp216_recovery_MAPE": 5.1559260117961525e-05,
    "p95_guarded_delta_vs_pp216_recovery_p95_win_rate": 0.0019230769230771383,
    "p95_guarded_avg_pp64_MAPE_win_rate": 0.9509615384615384,
    "p95_guarded_avg_pp64_p95_win_rate": 0.7516025641025642,
    "p95_guarded_replacement_score": -0.01865330231203425,
    "p95_extreme_label": "pp148_p95_reference",
    "p95_extreme_candidate": "reference_pp148_p95",
    "p95_extreme_fixed_test_MAPE": 0.27026892590910795,
    "p95_extreme_fixed_test_p95_APE": 0.8059493758221674,
    "p95_extreme_delta_vs_pp64_MAPE": -0.00029511600655240944,
    "p95_extreme_delta_vs_pp64_p95_APE": -0.0015494764839424358,
    "p95_extreme_delta_vs_pp204_MAPE": 0.00037540463794161205,
    "p95_extreme_delta_vs_pp204_p95_APE": -0.0013761288369714686,
    "p95_extreme_delta_vs_pp210_MAPE": 0.0003779250789336386,
    "p95_extreme_delta_vs_pp210_p95_APE": -0.0013761288369714686,
    "p95_extreme_delta_vs_pp216_recovery_MAPE": 0.00037128402713826336,
    "p95_extreme_delta_vs_pp216_recovery_p95_win_rate": -0.2487179487179486,
    "p95_extreme_avg_pp64_MAPE_win_rate": 0.5983974358974359,
    "p95_extreme_avg_pp64_p95_win_rate": 0.5009615384615385,
    "p95_extreme_replacement_score": -0.0040792899192624915,
    "operational_protocol_candidate": "ppopt222_operational_p95_regularized_rebuild__source=ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p24__basecap_0p0056__shrink_0p9",
    "balanced_protocol_candidate": "ppopt222_balanced_p95_regularized_rebuild__source=ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p24__basecap_0p0052__shrink_0p9",
    "p95_recovery_protocol_candidate": "ppopt222_p95_recovery_p95_regularized_rebuild__source=ppopt216_p95_recovery_pp210_p95_recovery__source_ppopt215_p95_aware_rebuild__thr_0p02__p95thr_m0p0001__s_1p16__basecap_0",
    "mape_challenger_protocol_candidate": "ppopt222_mape_challenger_p95_regularized_rebuild__source=ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p24__basecap_0p006__shrink_0p9",
    "p95_guarded_protocol_candidate": "ppopt222_p95_guarded_p95_regularized_rebuild__source=ppopt210_p95_guarded_pp204_local_refinement__source_ppopt204_p95_guarded_pp192_pp198_winner_router__source_ppopt192_p95_",
    "p95_extreme_protocol_candidate": "ppopt222_p95_extreme_p95_regularized_rebuild__source=reference_pp148_p95"
  },
  "items": [
    {
      "item_id": "PP-OPT217",
      "priority": "1",
      "title": "p95-regularized winner rebuild local search",
      "description": "PP216 p95-recovery rebuild 주변의 p95 guard, strength, cap, shrink를 재탐색."
    },
    {
      "item_id": "PP-OPT218",
      "priority": "2",
      "title": "PP210 to p95-recovery gated route",
      "description": "PP210에서 PP216 p95-recovery 후보 쪽으로 p95 이득이 있는 row만 제한 이동."
    },
    {
      "item_id": "PP-OPT219",
      "priority": "3",
      "title": "global plus gated p95 recovery blend",
      "description": "PP210에 p95-recovery 후보를 아주 약하게 전역 반영하고 p95 이득 구간만 추가 이동."
    },
    {
      "item_id": "PP-OPT220",
      "priority": "4",
      "title": "three-way PP210/PP204/recovery route",
      "description": "PP210, PP204, p95-recovery 후보를 p95 win-rate와 MAPE 손상 기준으로 라우팅."
    },
    {
      "item_id": "PP-OPT221",
      "priority": "5",
      "title": "p95-regularized candidate score selection",
      "description": "MAPE와 p95 win-rate를 동시에 반영한 score로 후보를 재정렬."
    },
    {
      "item_id": "PP-OPT222",
      "priority": "6",
      "title": "final p95-regularized rebuild decision",
      "description": "PP210, PP216 p95-recovery, 신규 후보를 fixed/repeated 기준으로 비교해 선택."
    }
  ],
  "router_formula": {
    "rebuild_base": "PP192 operational log price",
    "rebuild_target": "PP198 operational log price",
    "rebuild_final": "PP192 log price + clip((PP198 log price - PP192 log price) * p95_regularized_weight, row_cap)",
    "recovery_route_base": "PP210 operational log price",
    "recovery_target": "PP216 p95-recovery log price",
    "recovery_final": "PP210 log price + clip((PP216 recovery log price - PP210 log price) * recovery_gate, row_cap)",
    "selection_goal": "Keep PP210-level MAPE while recovering repeated p95 win-rate toward PP216 p95-recovery."
  }
}
```