# PP-OPT223~228 Warm PP222 narrow balance refinement 결과

- 작성일: 2026-06-10 11:34
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 목적: PP222 균형 후보와 공격형 후보 사이의 좁은 cap/strength/shrink 탐색
- 결론: 운영 후보 MAPE 0.269889, p95 win rate 0.747115. 균형 후보 MAPE 0.269890, p95 win rate 0.747756.

## 주요 후보 test 비교
| candidate | family | item_id | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt228_mape_challenger_pp222_narrow_balance__source=ppopt224_risk_shaped_cap__curve_1p25__s_1p26__basecap_0p0054__shrink_0p86 | pp222_narrow_balance_mape_selection | PP-OPT228 | 0.140975 | 0.269889 | 0.807326 | 0.397455 | -0.001506 | -0.000804 |
| ppopt228_operational_pp222_narrow_balance__source=ppopt224_risk_shaped_cap__curve_1p25__s_1p26__basecap_0p0052__shrink_0p94 | pp222_narrow_balance_operational_selection | PP-OPT228 | 0.140975 | 0.269889 | 0.807326 | 0.397455 | -0.001506 | -0.000804 |
| ppopt222_operational_p95_regularized_rebuild__source=ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p24__basecap_0p0056__shrink_0p9 | reference_prior | REFERENCE | 0.140975 | 0.269889 | 0.807326 | 0.397455 | -0.001505 | -0.000804 |
| ppopt228_balanced_pp222_narrow_balance__source=ppopt223_neighborhood__thr_0p015__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00545__shrink_0p92 | pp222_narrow_balance_balanced_selection | PP-OPT228 | 0.140975 | 0.269890 | 0.807326 | 0.397456 | -0.001505 | -0.000804 |
| ppopt222_balanced_p95_regularized_rebuild__source=ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p24__basecap_0p0052__shrink_0p9 | reference_prior | REFERENCE | 0.140975 | 0.269890 | 0.807326 | 0.397456 | -0.001505 | -0.000804 |
| ppopt210_operational_pp204_local_refinement__source=ppopt205_local_price_conf__thr_0p04__width_0p22__s_1p16__basecap_0p0055__shrink_0p9 | reference_prior | REFERENCE | 0.140975 | 0.269891 | 0.807326 | 0.397456 | -0.001504 | -0.000804 |
| ppopt204_operational_pp192_pp198_winner_router__source=ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_1p0__basecap_0p006__shrink_0p8 | reference_prior | REFERENCE | 0.140975 | 0.269894 | 0.807326 | 0.397456 | -0.001501 | -0.000804 |
| ppopt216_p95_recovery_pp210_p95_recovery__source=ppopt215_p95_aware_rebuild__thr_0p02__p95thr_m0p0001__s_1p16__basecap_0p005__shrink_1p2 | reference_prior | REFERENCE | 0.140975 | 0.269898 | 0.807326 | 0.397460 | -0.001497 | -0.000804 |
| ppopt192_operational_pp180_pp186_risk_router__source=ppopt189_segment_router__seg_price_gap__scorethr_0p02__mix_0p75__s_0p95__cap_0p0025 | reference_prior | REFERENCE | 0.140975 | 0.269914 | 0.807326 | 0.397468 | -0.001481 | -0.000804 |
| ppopt228_p95_guarded_pp222_narrow_balance__source=ppopt222_p95_guarded_p95_regularized_rebuild__source_ppopt210_p95_guarded_pp204_local_refinement__source_ppopt204_p95_gu | pp222_narrow_balance_p95_guarded_selection | PP-OPT228 | 0.140094 | 0.269949 | 0.807255 | 0.397482 | -0.001446 | -0.000875 |
| reference_pp126_operational | reference_prior | REFERENCE | 0.136320 | 0.270114 | 0.807490 | 0.397588 | -0.001280 | -0.000640 |
| reference_pp148_operational | reference_prior | REFERENCE | 0.139801 | 0.270140 | 0.807231 | 0.397525 | -0.001255 | -0.000899 |
| reference_pp148_p95 | reference_prior | REFERENCE | 0.141036 | 0.270269 | 0.805949 | 0.397421 | -0.001126 | -0.002181 |
| ppopt228_p95_extreme_pp222_narrow_balance__source=reference_pp148_p95 | pp222_narrow_balance_p95_extreme_selection | PP-OPT228 | 0.141036 | 0.270269 | 0.805949 | 0.397421 | -0.001126 | -0.002181 |
| reference_pp64_current_best | reference_prior | REFERENCE | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | p95_test_MAPE | p95_test_p95_APE | operational_pass_vs_incumbent | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | final PP222 narrow balance decision | 5 | 0.269949 | 0.807255 | 0.270269 | 0.805949 | False | pp222_narrow_balance_p95_guarded_selection | ppopt228_p95_guarded_pp222_narrow_balance__source=ppopt222_p95_guarded_p95_regularized_rebuild__source_ppopt210_p95_guarded_pp204_local_refinement__source_ppopt204_p95_gu |
| 2 | risk-shaped cap refinement | 81 | 0.269889 | 0.807326 | 0.269889 | 0.807326 | False | pp222_risk_shaped_cap_refinement | ppopt224_risk_shaped_cap__curve=1p0__s=1p26__basecap=0p0054__shrink=0p9 |
| 1 | PP222 balanced neighborhood search | 864 | 0.269890 | 0.807326 | 0.269889 | 0.807326 | False | pp222_balanced_neighborhood_search | ppopt223_neighborhood__thr=0p015__p95thr=m0p00012__p95width=0p00012__s=1p26__basecap=0p00545__shrink=0p92 |
| 3 | balanced-to-aggressive micro blend | 20 | 0.269890 | 0.807326 | 0.269890 | 0.807326 | False | pp222_balanced_to_aggressive_micro_blend | ppopt225_balanced_to_aggressive__share=0p5__cap=0p00025 |
| 4 | balanced-to-recovery p95 support blend | 12 | 0.269890 | 0.807326 | 0.269890 | 0.807326 | False | pp222_balanced_to_recovery_support | ppopt226_recovery_support__s=0p18__cap=0p00025 |

## 탐색 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt228_p95_guarded_pp222_narrow_balance__source=ppopt222_p95_guarded_p95_regularized_rebuild__source_ppopt210_p95_guarded_pp204_local_refinement__source_ppopt204_p95_gu | PP-OPT228 | pp222_narrow_balance_p95_guarded_selection | 0.269949 | 0.807255 | -0.001446 | -0.000875 | -0.001537 |
| ppopt224_risk_shaped_cap__curve=1p0__s=1p26__basecap=0p0054__shrink=0p9 | PP-OPT224 | pp222_risk_shaped_cap_refinement | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00012__p95width=0p00012__s=1p26__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00012__p95width=0p0001__s=1p26__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00014__p95width=0p00012__s=1p26__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00014__p95width=0p0001__s=1p26__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00016__p95width=0p00012__s=1p26__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00016__p95width=0p0001__s=1p26__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00012__p95width=0p00012__s=1p26__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00012__p95width=0p0001__s=1p26__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00014__p95width=0p00012__s=1p26__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00014__p95width=0p0001__s=1p26__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00016__p95width=0p00012__s=1p26__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00016__p95width=0p0001__s=1p26__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00012__p95width=0p00012__s=1p26__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00012__p95width=0p0001__s=1p26__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00014__p95width=0p00012__s=1p26__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00014__p95width=0p0001__s=1p26__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00016__p95width=0p00012__s=1p26__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00016__p95width=0p0001__s=1p26__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt228_balanced_pp222_narrow_balance__source=ppopt223_neighborhood__thr_0p015__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00545__shrink_0p92 | PP-OPT228 | pp222_narrow_balance_balanced_selection | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00012__p95width=0p00012__s=1p26__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00012__p95width=0p0001__s=1p26__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00014__p95width=0p00012__s=1p26__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00014__p95width=0p0001__s=1p26__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00016__p95width=0p00012__s=1p26__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00016__p95width=0p0001__s=1p26__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00012__p95width=0p00012__s=1p26__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00012__p95width=0p0001__s=1p26__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00014__p95width=0p00012__s=1p26__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00014__p95width=0p0001__s=1p26__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00016__p95width=0p00012__s=1p26__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00016__p95width=0p0001__s=1p26__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00012__p95width=0p00012__s=1p26__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00012__p95width=0p0001__s=1p26__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00014__p95width=0p00012__s=1p26__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00014__p95width=0p0001__s=1p26__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00016__p95width=0p00012__s=1p26__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00016__p95width=0p0001__s=1p26__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00012__p95width=0p00012__s=1p26__basecap=0p00525__shrink=0p88 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00012__p95width=0p0001__s=1p26__basecap=0p00525__shrink=0p88 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00014__p95width=0p00012__s=1p26__basecap=0p00525__shrink=0p88 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00014__p95width=0p0001__s=1p26__basecap=0p00525__shrink=0p88 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00016__p95width=0p00012__s=1p26__basecap=0p00525__shrink=0p88 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00016__p95width=0p0001__s=1p26__basecap=0p00525__shrink=0p88 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00012__p95width=0p00012__s=1p26__basecap=0p00525__shrink=0p88 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00012__p95width=0p0001__s=1p26__basecap=0p00525__shrink=0p88 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00014__p95width=0p00012__s=1p26__basecap=0p00525__shrink=0p88 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00014__p95width=0p0001__s=1p26__basecap=0p00525__shrink=0p88 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00016__p95width=0p00012__s=1p26__basecap=0p00525__shrink=0p88 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00016__p95width=0p0001__s=1p26__basecap=0p00525__shrink=0p88 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00012__p95width=0p00012__s=1p26__basecap=0p00525__shrink=0p88 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00012__p95width=0p0001__s=1p26__basecap=0p00525__shrink=0p88 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00014__p95width=0p00012__s=1p26__basecap=0p00525__shrink=0p88 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00014__p95width=0p0001__s=1p26__basecap=0p00525__shrink=0p88 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00016__p95width=0p00012__s=1p26__basecap=0p00525__shrink=0p88 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00016__p95width=0p0001__s=1p26__basecap=0p00525__shrink=0p88 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt224_risk_shaped_cap__curve=1p0__s=1p26__basecap=0p0053__shrink=0p9 | PP-OPT224 | pp222_risk_shaped_cap_refinement | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00012__p95width=0p00012__s=1p26__basecap=0p00545__shrink=0p94 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00012__p95width=0p0001__s=1p26__basecap=0p00545__shrink=0p94 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00014__p95width=0p00012__s=1p26__basecap=0p00545__shrink=0p94 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00014__p95width=0p0001__s=1p26__basecap=0p00545__shrink=0p94 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00016__p95width=0p00012__s=1p26__basecap=0p00545__shrink=0p94 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00016__p95width=0p0001__s=1p26__basecap=0p00545__shrink=0p94 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00012__p95width=0p00012__s=1p26__basecap=0p00545__shrink=0p94 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00012__p95width=0p0001__s=1p26__basecap=0p00545__shrink=0p94 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00014__p95width=0p00012__s=1p26__basecap=0p00545__shrink=0p94 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00014__p95width=0p0001__s=1p26__basecap=0p00545__shrink=0p94 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00016__p95width=0p00012__s=1p26__basecap=0p00545__shrink=0p94 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00016__p95width=0p0001__s=1p26__basecap=0p00545__shrink=0p94 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00012__p95width=0p00012__s=1p26__basecap=0p00545__shrink=0p94 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00012__p95width=0p0001__s=1p26__basecap=0p00545__shrink=0p94 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00014__p95width=0p00012__s=1p26__basecap=0p00545__shrink=0p94 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00014__p95width=0p0001__s=1p26__basecap=0p00545__shrink=0p94 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00016__p95width=0p00012__s=1p26__basecap=0p00545__shrink=0p94 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00016__p95width=0p0001__s=1p26__basecap=0p00545__shrink=0p94 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00012__p95width=0p00012__s=1p26__basecap=0p00535__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00012__p95width=0p0001__s=1p26__basecap=0p00535__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00014__p95width=0p00012__s=1p26__basecap=0p00535__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00014__p95width=0p0001__s=1p26__basecap=0p00535__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00016__p95width=0p00012__s=1p26__basecap=0p00535__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00016__p95width=0p0001__s=1p26__basecap=0p00535__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00012__p95width=0p00012__s=1p26__basecap=0p00535__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00012__p95width=0p0001__s=1p26__basecap=0p00535__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00014__p95width=0p00012__s=1p26__basecap=0p00535__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00014__p95width=0p0001__s=1p26__basecap=0p00535__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00016__p95width=0p00012__s=1p26__basecap=0p00535__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00016__p95width=0p0001__s=1p26__basecap=0p00535__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00012__p95width=0p00012__s=1p26__basecap=0p00535__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00012__p95width=0p0001__s=1p26__basecap=0p00535__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00014__p95width=0p00012__s=1p26__basecap=0p00535__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00014__p95width=0p0001__s=1p26__basecap=0p00535__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00016__p95width=0p00012__s=1p26__basecap=0p00535__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00016__p95width=0p0001__s=1p26__basecap=0p00535__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00012__p95width=0p00012__s=1p24__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00012__p95width=0p0001__s=1p24__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00014__p95width=0p00012__s=1p24__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00014__p95width=0p0001__s=1p24__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00016__p95width=0p00012__s=1p24__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00016__p95width=0p0001__s=1p24__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00012__p95width=0p00012__s=1p24__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00012__p95width=0p0001__s=1p24__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00014__p95width=0p00012__s=1p24__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00014__p95width=0p0001__s=1p24__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00016__p95width=0p00012__s=1p24__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00016__p95width=0p0001__s=1p24__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00012__p95width=0p00012__s=1p24__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00012__p95width=0p0001__s=1p24__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00014__p95width=0p00012__s=1p24__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00014__p95width=0p0001__s=1p24__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00016__p95width=0p00012__s=1p24__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00016__p95width=0p0001__s=1p24__basecap=0p00545__shrink=0p92 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt224_risk_shaped_cap__curve=1p0__s=1p24__basecap=0p0054__shrink=0p9 | PP-OPT224 | pp222_risk_shaped_cap_refinement | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00012__p95width=0p00012__s=1p26__basecap=0p00525__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00012__p95width=0p0001__s=1p26__basecap=0p00525__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00014__p95width=0p00012__s=1p26__basecap=0p00525__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00014__p95width=0p0001__s=1p26__basecap=0p00525__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00016__p95width=0p00012__s=1p26__basecap=0p00525__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00016__p95width=0p0001__s=1p26__basecap=0p00525__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00012__p95width=0p00012__s=1p26__basecap=0p00525__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00012__p95width=0p0001__s=1p26__basecap=0p00525__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00014__p95width=0p00012__s=1p26__basecap=0p00525__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00014__p95width=0p0001__s=1p26__basecap=0p00525__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00016__p95width=0p00012__s=1p26__basecap=0p00525__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00016__p95width=0p0001__s=1p26__basecap=0p00525__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00012__p95width=0p00012__s=1p26__basecap=0p00525__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00012__p95width=0p0001__s=1p26__basecap=0p00525__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00014__p95width=0p00012__s=1p26__basecap=0p00525__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00014__p95width=0p0001__s=1p26__basecap=0p00525__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00016__p95width=0p00012__s=1p26__basecap=0p00525__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00016__p95width=0p0001__s=1p26__basecap=0p00525__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00012__p95width=0p00012__s=1p24__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00012__p95width=0p0001__s=1p24__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00014__p95width=0p00012__s=1p24__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00014__p95width=0p0001__s=1p24__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00016__p95width=0p00012__s=1p24__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00016__p95width=0p0001__s=1p24__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00012__p95width=0p00012__s=1p24__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00012__p95width=0p0001__s=1p24__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00014__p95width=0p00012__s=1p24__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00014__p95width=0p0001__s=1p24__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00016__p95width=0p00012__s=1p24__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00016__p95width=0p0001__s=1p24__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00012__p95width=0p00012__s=1p24__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00012__p95width=0p0001__s=1p24__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00014__p95width=0p00012__s=1p24__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00014__p95width=0p0001__s=1p24__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00016__p95width=0p00012__s=1p24__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p02__p95thr=m0p00016__p95width=0p0001__s=1p24__basecap=0p00535__shrink=0p9 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00012__p95width=0p00012__s=1p26__basecap=0p00515__shrink=0p88 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00012__p95width=0p0001__s=1p26__basecap=0p00515__shrink=0p88 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00014__p95width=0p00012__s=1p26__basecap=0p00515__shrink=0p88 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00014__p95width=0p0001__s=1p26__basecap=0p00515__shrink=0p88 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00016__p95width=0p00012__s=1p26__basecap=0p00515__shrink=0p88 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p015__p95thr=m0p00016__p95width=0p0001__s=1p26__basecap=0p00515__shrink=0p88 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00012__p95width=0p00012__s=1p26__basecap=0p00515__shrink=0p88 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00012__p95width=0p0001__s=1p26__basecap=0p00515__shrink=0p88 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00014__p95width=0p00012__s=1p26__basecap=0p00515__shrink=0p88 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00014__p95width=0p0001__s=1p26__basecap=0p00515__shrink=0p88 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt223_neighborhood__thr=0p025__p95thr=m0p00016__p95width=0p00012__s=1p26__basecap=0p00515__shrink=0p88 | PP-OPT223 | pp222_balanced_neighborhood_search | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |

## 선택 후보 반복 안정성
| candidate_label | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_vs_pp64_MAPE | fixed_test_delta_vs_pp64_p95_APE | avg_pp64_MAPE_win_rate | avg_pp64_p95_win_rate | replacement_score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| candidate_ppopt224_risk_shaped_cap__curve_1p25__s_1p26__basecap_0p0052__shrink_0p94__f45db05a1a | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018842 |
| pp228_operational_pp222_narrow_balance_challenger | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018842 |
| candidate_ppopt224_risk_shaped_cap__curve_1p25__s_1p26__basecap_0p0054__shrink_0p94__cc16453224 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt224_risk_shaped_cap__curve_1p25__s_1p26__basecap_0p0053__shrink_0p94__d621247e2d | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt224_risk_shaped_cap__curve_1p25__s_1p26__basecap_0p0054__shrink_0p9__52861e83d4 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt224_risk_shaped_cap__curve_1p25__s_1p26__basecap_0p0053__shrink_0p9__948ef0c4b1 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt224_risk_shaped_cap__curve_1p25__s_1p26__basecap_0p0052__shrink_0p9__e7ed28161a | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt224_risk_shaped_cap__curve_1p0__s_1p26__basecap_0p0054__shrink_0p86__bf60ef5e52 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00545__764aa24a7e | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00012__p95width_0p0001__s_1p26__basecap_0p00545___40bde4fa49 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00014__p95width_0p00012__s_1p26__basecap_0p00545__d99ab429d0 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00014__p95width_0p0001__s_1p26__basecap_0p00545___80c8d6e32f | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00016__p95width_0p00012__s_1p26__basecap_0p00545__e8cc52b964 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00016__p95width_0p0001__s_1p26__basecap_0p00545___72ca7d2417 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00545__f3001f4608 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00012__p95width_0p0001__s_1p26__basecap_0p00545___9e0412a253 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00014__p95width_0p00012__s_1p26__basecap_0p00545__cf46ec8e51 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00014__p95width_0p0001__s_1p26__basecap_0p00545___e79543a4ec | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00016__p95width_0p00012__s_1p26__basecap_0p00545__e19d4f7ac8 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00016__p95width_0p0001__s_1p26__basecap_0p00545___50b76b76c2 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00545___0bc3a51309 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00012__p95width_0p0001__s_1p26__basecap_0p00545____4617b591f3 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p26__basecap_0p00545___02c4ef2292 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00014__p95width_0p0001__s_1p26__basecap_0p00545____af31955554 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00016__p95width_0p00012__s_1p26__basecap_0p00545___09a5298c4c | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00016__p95width_0p0001__s_1p26__basecap_0p00545____a1c3d4dba6 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt224_risk_shaped_cap__curve_1p0__s_1p26__basecap_0p0053__shrink_0p86__626ca177cb | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00535__558e590bb3 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00012__p95width_0p0001__s_1p26__basecap_0p00535___cbbab6c8c3 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00014__p95width_0p00012__s_1p26__basecap_0p00535__6496457a87 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00014__p95width_0p0001__s_1p26__basecap_0p00535___6c9402013b | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00016__p95width_0p00012__s_1p26__basecap_0p00535__50e45d8675 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00016__p95width_0p0001__s_1p26__basecap_0p00535___96436413d0 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00535__97e305a4d3 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00012__p95width_0p0001__s_1p26__basecap_0p00535___acb770ee3d | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00014__p95width_0p00012__s_1p26__basecap_0p00535__d33efaf8cc | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00014__p95width_0p0001__s_1p26__basecap_0p00535___fae052656b | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00016__p95width_0p00012__s_1p26__basecap_0p00535__fdfd6147a1 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00016__p95width_0p0001__s_1p26__basecap_0p00535___46992e3ad2 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00535___020c430077 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00012__p95width_0p0001__s_1p26__basecap_0p00535____168b9af753 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p26__basecap_0p00535___f107ecf619 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00014__p95width_0p0001__s_1p26__basecap_0p00535____0269b02050 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00016__p95width_0p00012__s_1p26__basecap_0p00535___11ddeb8dda | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00016__p95width_0p0001__s_1p26__basecap_0p00535____77ee40dfea | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00545__0c00171839 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00012__p95width_0p0001__s_1p26__basecap_0p00545___bcaad082e9 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00014__p95width_0p00012__s_1p26__basecap_0p00545__1d41587e19 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00014__p95width_0p0001__s_1p26__basecap_0p00545___a594845c6d | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00016__p95width_0p00012__s_1p26__basecap_0p00545__e5b04b577b | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00016__p95width_0p0001__s_1p26__basecap_0p00545___704ee428ec | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00545__3ccdc9e63d | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00012__p95width_0p0001__s_1p26__basecap_0p00545___1585c926b9 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00014__p95width_0p00012__s_1p26__basecap_0p00545__7cfb44e03c | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00014__p95width_0p0001__s_1p26__basecap_0p00545___ba2fcb136d | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00016__p95width_0p00012__s_1p26__basecap_0p00545__8dd2df0df5 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00016__p95width_0p0001__s_1p26__basecap_0p00545___16939f4306 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00545___47b5221af8 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00012__p95width_0p0001__s_1p26__basecap_0p00545____f40821b54d | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p26__basecap_0p00545___b4c7ac87bc | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00014__p95width_0p0001__s_1p26__basecap_0p00545____cd056a2650 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00016__p95width_0p00012__s_1p26__basecap_0p00545___1cbac8d6bd | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00016__p95width_0p0001__s_1p26__basecap_0p00545____92478f79d3 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt224_risk_shaped_cap__curve_1p0__s_1p26__basecap_0p0054__shrink_0p9__bf67609194 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt224_risk_shaped_cap__curve_1p0__s_1p26__basecap_0p0052__shrink_0p86__ef21f64a4a | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt224_risk_shaped_cap__curve_1p25__s_1p24__basecap_0p0052__shrink_0p94__79ea4d239f | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00525__7a3e3e7894 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00012__p95width_0p0001__s_1p26__basecap_0p00525___48aa5f081f | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00014__p95width_0p00012__s_1p26__basecap_0p00525__4b407d1233 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00014__p95width_0p0001__s_1p26__basecap_0p00525___d7845da12d | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00016__p95width_0p00012__s_1p26__basecap_0p00525__584685e449 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00016__p95width_0p0001__s_1p26__basecap_0p00525___558e5cfc94 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00525__49f7a893d5 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00012__p95width_0p0001__s_1p26__basecap_0p00525___a0265fb19e | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00014__p95width_0p00012__s_1p26__basecap_0p00525__f7b8ef76f9 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00014__p95width_0p0001__s_1p26__basecap_0p00525___6a091830d8 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00016__p95width_0p00012__s_1p26__basecap_0p00525__7c517c4ab6 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00016__p95width_0p0001__s_1p26__basecap_0p00525___c9f7ffae58 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00525___a601bfe0ee | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00012__p95width_0p0001__s_1p26__basecap_0p00525____172af554f0 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p26__basecap_0p00525___dccf3a43b2 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00014__p95width_0p0001__s_1p26__basecap_0p00525____f7635ff8c7 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00016__p95width_0p00012__s_1p26__basecap_0p00525___f6604e4bff | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00016__p95width_0p0001__s_1p26__basecap_0p00525____a373810eba | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00535__45d9a1b205 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00012__p95width_0p0001__s_1p26__basecap_0p00535___8d427ef7d4 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00014__p95width_0p00012__s_1p26__basecap_0p00535__a5d4c577a4 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00014__p95width_0p0001__s_1p26__basecap_0p00535___5e99c025f2 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00016__p95width_0p00012__s_1p26__basecap_0p00535__46e1615976 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00016__p95width_0p0001__s_1p26__basecap_0p00535___f10623d1c0 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00535__d9dce6adc2 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00012__p95width_0p0001__s_1p26__basecap_0p00535___d74aab94f2 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00014__p95width_0p00012__s_1p26__basecap_0p00535__91f791510c | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00014__p95width_0p0001__s_1p26__basecap_0p00535___77150156c7 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00016__p95width_0p00012__s_1p26__basecap_0p00535__a77c018f39 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00016__p95width_0p0001__s_1p26__basecap_0p00535___c13ecd0e65 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00535___a219c12b88 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00012__p95width_0p0001__s_1p26__basecap_0p00535____496649996e | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p26__basecap_0p00535___a27740d0cb | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00014__p95width_0p0001__s_1p26__basecap_0p00535____3912c64e59 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00016__p95width_0p00012__s_1p26__basecap_0p00535___4c19086ec9 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00016__p95width_0p0001__s_1p26__basecap_0p00535____07af3af234 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| pp222_aggressive_reference | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00545__545ef9d07f | 0.269890 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00012__p95width_0p0001__s_1p26__basecap_0p00545___f9380f0f42 | 0.269890 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00014__p95width_0p00012__s_1p26__basecap_0p00545__e316992deb | 0.269890 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00014__p95width_0p0001__s_1p26__basecap_0p00545___55fec46e35 | 0.269890 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00016__p95width_0p00012__s_1p26__basecap_0p00545__c76979b41d | 0.269890 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00016__p95width_0p0001__s_1p26__basecap_0p00545___2d10e53ec7 | 0.269890 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00545__214de636c9 | 0.269890 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00012__p95width_0p0001__s_1p26__basecap_0p00545___a5e12e9e1f | 0.269890 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00014__p95width_0p00012__s_1p26__basecap_0p00545__f0a03b4d0b | 0.269890 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00014__p95width_0p0001__s_1p26__basecap_0p00545___433ac12f0d | 0.269890 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00016__p95width_0p00012__s_1p26__basecap_0p00545__c90792b556 | 0.269890 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00016__p95width_0p0001__s_1p26__basecap_0p00545___b98078e0e0 | 0.269890 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00545___351dacbd8f | 0.269890 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00012__p95width_0p0001__s_1p26__basecap_0p00545____2deaa72b32 | 0.269890 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p26__basecap_0p00545___d4eb361cb2 | 0.269890 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00014__p95width_0p0001__s_1p26__basecap_0p00545____1f008a80b0 | 0.269890 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00016__p95width_0p00012__s_1p26__basecap_0p00545___35d2281d3b | 0.269890 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00016__p95width_0p0001__s_1p26__basecap_0p00545____c93ef26103 | 0.269890 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| pp228_balanced_pp222_narrow_balance_challenger | 0.269890 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt224_risk_shaped_cap__curve_1p0__s_1p26__basecap_0p0053__shrink_0p9__7a6ae67645 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00525__a7aa4f19a4 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00012__p95width_0p0001__s_1p26__basecap_0p00525___d3c8532899 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00014__p95width_0p00012__s_1p26__basecap_0p00525__b85c21f6d2 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00014__p95width_0p0001__s_1p26__basecap_0p00525___7e156a4bf4 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00016__p95width_0p00012__s_1p26__basecap_0p00525__30ed2aa822 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00016__p95width_0p0001__s_1p26__basecap_0p00525___bb5129d597 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00525__5d68fddbb4 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00012__p95width_0p0001__s_1p26__basecap_0p00525___a5c6255314 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00014__p95width_0p00012__s_1p26__basecap_0p00525__c272898a2d | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00014__p95width_0p0001__s_1p26__basecap_0p00525___c058e81a92 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00016__p95width_0p00012__s_1p26__basecap_0p00525__5d8d0df701 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00016__p95width_0p0001__s_1p26__basecap_0p00525___ea0351eb2c | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00525___680a1ce5fc | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00012__p95width_0p0001__s_1p26__basecap_0p00525____c635736a42 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p26__basecap_0p00525___28a9bc50bd | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00014__p95width_0p0001__s_1p26__basecap_0p00525____a245493d75 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00016__p95width_0p00012__s_1p26__basecap_0p00525___ae006a74f3 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00016__p95width_0p0001__s_1p26__basecap_0p00525____169db55496 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00535__19219f8700 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00012__p95width_0p0001__s_1p26__basecap_0p00535___c3ca987d8b | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00014__p95width_0p00012__s_1p26__basecap_0p00535__a61065612f | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00014__p95width_0p0001__s_1p26__basecap_0p00535___0b0429b059 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00016__p95width_0p00012__s_1p26__basecap_0p00535__047750ac9f | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00016__p95width_0p0001__s_1p26__basecap_0p00535___f5a92c1541 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00535__978adf4117 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00012__p95width_0p0001__s_1p26__basecap_0p00535___d5014bf9bb | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00014__p95width_0p00012__s_1p26__basecap_0p00535__5d3ed0d71f | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00014__p95width_0p0001__s_1p26__basecap_0p00535___3e650372f3 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00016__p95width_0p00012__s_1p26__basecap_0p00535__66f8e2c15a | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00016__p95width_0p0001__s_1p26__basecap_0p00535___4ec51982b4 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00535___cde23f1573 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00012__p95width_0p0001__s_1p26__basecap_0p00535____16aafa2122 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p26__basecap_0p00535___0cdb45f4c7 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00014__p95width_0p0001__s_1p26__basecap_0p00535____daedef4c7d | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00016__p95width_0p00012__s_1p26__basecap_0p00535___daf08a7bba | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00016__p95width_0p0001__s_1p26__basecap_0p00535____d39dc084c3 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00545__0f6a665d16 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00012__p95width_0p0001__s_1p26__basecap_0p00545___30ffab2791 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00014__p95width_0p00012__s_1p26__basecap_0p00545__1c902abb16 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00014__p95width_0p0001__s_1p26__basecap_0p00545___78a6f5d36b | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00016__p95width_0p00012__s_1p26__basecap_0p00545__34364908ed | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00016__p95width_0p0001__s_1p26__basecap_0p00545___9502bf99a5 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00545__e61e3cc591 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00012__p95width_0p0001__s_1p26__basecap_0p00545___080713672e | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00014__p95width_0p00012__s_1p26__basecap_0p00545__e49b6b72bb | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00014__p95width_0p0001__s_1p26__basecap_0p00545___c597117dae | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00016__p95width_0p00012__s_1p26__basecap_0p00545__a53a81be27 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p025__p95thr_m0p00016__p95width_0p0001__s_1p26__basecap_0p00545___94bffe6279 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00545___c1848a9b1f | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00012__p95width_0p0001__s_1p26__basecap_0p00545____349e81959c | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p26__basecap_0p00545___56c8bf06eb | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00014__p95width_0p0001__s_1p26__basecap_0p00545____25abc7b2d9 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00016__p95width_0p00012__s_1p26__basecap_0p00545___b736e2ed5b | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p02__p95thr_m0p00016__p95width_0p0001__s_1p26__basecap_0p00545____00cd5f2ed9 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt224_risk_shaped_cap__curve_1p0__s_1p24__basecap_0p0054__shrink_0p9__df6097fcbd | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00012__p95width_0p00012__s_1p24__basecap_0p00535__b2990a0913 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00012__p95width_0p0001__s_1p24__basecap_0p00535___0f03898431 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |

## 실행 설정
```json
{
  "experiment_id": "PP-OPT223-228",
  "experiment_slug": "PP-OPT223_228_warm_pp222_narrow_balance_refinement",
  "created_at": "2026-06-10T11:34:04",
  "base_candidate": "hcoef_stable",
  "previous_experiment": "experiments/track6/PP-OPT217_222_warm_p95_regularized_winner_rebuild",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 1006,
  "prediction_rows": 1132756,
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
    "pp216_p95_extreme": "ppopt216_p95_extreme_pp210_p95_recovery__source=reference_pp148_p95",
    "pp222_operational": "ppopt222_operational_p95_regularized_rebuild__source=ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p24__basecap_0p0056__shrink_0p9",
    "pp222_balanced": "ppopt222_balanced_p95_regularized_rebuild__source=ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p24__basecap_0p0052__shrink_0p9",
    "pp222_p95_recovery": "ppopt222_p95_recovery_p95_regularized_rebuild__source=ppopt216_p95_recovery_pp210_p95_recovery__source_ppopt215_p95_aware_rebuild__thr_0p02__p95thr_m0p0001__s_1p16__basecap_0",
    "pp222_mape": "ppopt222_mape_challenger_p95_regularized_rebuild__source=ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p24__basecap_0p006__shrink_0p9",
    "pp222_p95_guarded": "ppopt222_p95_guarded_p95_regularized_rebuild__source=ppopt210_p95_guarded_pp204_local_refinement__source_ppopt204_p95_guarded_pp192_pp198_winner_router__source_ppopt192_p95_",
    "pp222_p95_extreme": "ppopt222_p95_extreme_p95_regularized_rebuild__source=reference_pp148_p95"
  },
  "selection_decision": {
    "operational_label": "candidate_ppopt224_risk_shaped_cap__curve_1p25__s_1p26__basecap_0p0052__shrink_0p94__f45db05a1a",
    "operational_candidate": "ppopt224_risk_shaped_cap__curve=1p25__s=1p26__basecap=0p0052__shrink=0p94",
    "operational_fixed_test_MAPE": 0.26988910777837405,
    "operational_fixed_test_p95_APE": 0.8073255046591389,
    "operational_delta_vs_pp64_MAPE": -0.0006749341372863094,
    "operational_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "operational_delta_vs_pp222_balanced_MAPE": -8.899573992748877e-07,
    "operational_delta_vs_pp222_balanced_p95_win_rate": -0.0006410256410256387,
    "operational_delta_vs_pp222_aggressive_MAPE": -3.8992606044008227e-07,
    "operational_avg_pp64_MAPE_win_rate": 0.9541666666666666,
    "operational_avg_pp64_p95_win_rate": 0.7471153846153845,
    "operational_replacement_score": -0.018841600803952974,
    "balanced_label": "candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00545__545ef9d07f",
    "balanced_candidate": "ppopt223_neighborhood__thr=0p015__p95thr=m0p00012__p95width=0p00012__s=1p26__basecap=0p00545__shrink=0p92",
    "balanced_fixed_test_MAPE": 0.26988950282542246,
    "balanced_fixed_test_p95_APE": 0.8073255046591389,
    "balanced_delta_vs_pp64_MAPE": -0.0006745390902379023,
    "balanced_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "balanced_delta_vs_pp222_balanced_MAPE": -4.949103508677943e-07,
    "balanced_delta_vs_pp222_balanced_p95_win_rate": 0.0,
    "balanced_delta_vs_pp222_aggressive_MAPE": 5.120987967011104e-09,
    "balanced_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "balanced_avg_pp64_p95_win_rate": 0.7477564102564102,
    "balanced_replacement_score": -0.018828385244084058,
    "mape_challenger_label": "candidate_ppopt224_risk_shaped_cap__curve_1p25__s_1p26__basecap_0p0054__shrink_0p86__69ab40e036",
    "mape_challenger_candidate": "ppopt224_risk_shaped_cap__curve=1p25__s=1p26__basecap=0p0054__shrink=0p86",
    "mape_challenger_fixed_test_MAPE": 0.26988883720393,
    "mape_challenger_fixed_test_p95_APE": 0.8073255046591389,
    "mape_challenger_delta_vs_pp64_MAPE": -0.0006752047117303817,
    "mape_challenger_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "mape_challenger_delta_vs_pp222_balanced_MAPE": -1.16053184334719e-06,
    "mape_challenger_delta_vs_pp222_balanced_p95_win_rate": -0.0006410256410256387,
    "mape_challenger_delta_vs_pp222_aggressive_MAPE": -6.605005045123846e-07,
    "mape_challenger_avg_pp64_MAPE_win_rate": 0.953525641025641,
    "mape_challenger_avg_pp64_p95_win_rate": 0.7471153846153845,
    "mape_challenger_replacement_score": -0.018816230352756022,
    "p95_guarded_label": "pp222_p95_guarded_reference",
    "p95_guarded_candidate": "ppopt222_p95_guarded_p95_regularized_rebuild__source=ppopt210_p95_guarded_pp204_local_refinement__source_ppopt204_p95_guarded_pp192_pp198_winner_router__source_ppopt192_p95_",
    "p95_guarded_fixed_test_MAPE": 0.26994920114208765,
    "p95_guarded_fixed_test_p95_APE": 0.8072545738314347,
    "p95_guarded_delta_vs_pp64_MAPE": -0.0006148407735727113,
    "p95_guarded_delta_vs_pp64_p95_APE": -0.0002442784746751192,
    "p95_guarded_delta_vs_pp222_balanced_MAPE": 5.920340631432319e-05,
    "p95_guarded_delta_vs_pp222_balanced_p95_win_rate": 0.0038461538461540545,
    "p95_guarded_delta_vs_pp222_aggressive_MAPE": 5.9703437653158e-05,
    "p95_guarded_avg_pp64_MAPE_win_rate": 0.9509615384615384,
    "p95_guarded_avg_pp64_p95_win_rate": 0.7516025641025642,
    "p95_guarded_replacement_score": -0.01865330231203425,
    "p95_extreme_label": "pp148_p95_reference",
    "p95_extreme_candidate": "reference_pp148_p95",
    "p95_extreme_fixed_test_MAPE": 0.27026892590910795,
    "p95_extreme_fixed_test_p95_APE": 0.8059493758221674,
    "p95_extreme_delta_vs_pp64_MAPE": -0.00029511600655240944,
    "p95_extreme_delta_vs_pp64_p95_APE": -0.0015494764839424358,
    "p95_extreme_delta_vs_pp222_balanced_MAPE": 0.00037892817333462503,
    "p95_extreme_delta_vs_pp222_balanced_p95_win_rate": -0.2467948717948717,
    "p95_extreme_delta_vs_pp222_aggressive_MAPE": 0.00037942820467345983,
    "p95_extreme_avg_pp64_MAPE_win_rate": 0.5983974358974359,
    "p95_extreme_avg_pp64_p95_win_rate": 0.5009615384615385,
    "p95_extreme_replacement_score": -0.0040792899192624915,
    "operational_protocol_candidate": "ppopt228_operational_pp222_narrow_balance__source=ppopt224_risk_shaped_cap__curve_1p25__s_1p26__basecap_0p0052__shrink_0p94",
    "balanced_protocol_candidate": "ppopt228_balanced_pp222_narrow_balance__source=ppopt223_neighborhood__thr_0p015__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00545__shrink_0p92",
    "mape_challenger_protocol_candidate": "ppopt228_mape_challenger_pp222_narrow_balance__source=ppopt224_risk_shaped_cap__curve_1p25__s_1p26__basecap_0p0054__shrink_0p86",
    "p95_guarded_protocol_candidate": "ppopt228_p95_guarded_pp222_narrow_balance__source=ppopt222_p95_guarded_p95_regularized_rebuild__source_ppopt210_p95_guarded_pp204_local_refinement__source_ppopt204_p95_gu",
    "p95_extreme_protocol_candidate": "ppopt228_p95_extreme_pp222_narrow_balance__source=reference_pp148_p95"
  },
  "items": [
    {
      "item_id": "PP-OPT223",
      "priority": "1",
      "title": "PP222 balanced neighborhood search",
      "description": "PP222 균형 후보 주변의 threshold, p95 guard, strength, cap, shrink를 좁게 재탐색."
    },
    {
      "item_id": "PP-OPT224",
      "priority": "2",
      "title": "risk-shaped cap refinement",
      "description": "동일 weight에서 row risk별 cap 곡선을 조정해 p95 win rate를 유지하며 MAPE를 낮춤."
    },
    {
      "item_id": "PP-OPT225",
      "priority": "3",
      "title": "balanced-to-aggressive micro blend",
      "description": "PP222 균형 후보에서 공격형 MAPE 후보로 아주 작게 이동."
    },
    {
      "item_id": "PP-OPT226",
      "priority": "4",
      "title": "balanced-to-recovery p95 support blend",
      "description": "p95 win rate 회복 신호가 있는 row만 PP216 p95-recovery 후보 쪽으로 미세 이동."
    },
    {
      "item_id": "PP-OPT227",
      "priority": "5",
      "title": "candidate score selection",
      "description": "MAPE, replacement, p95 win rate 하한을 같이 적용해 후보를 재선택."
    },
    {
      "item_id": "PP-OPT228",
      "priority": "6",
      "title": "final PP222 narrow balance decision",
      "description": "PP222 균형/공격형 후보와 신규 후보를 fixed/repeated 기준으로 비교해 선택."
    }
  ],
  "router_formula": {
    "base": "PP192 operational log price",
    "target": "PP198 operational log price",
    "main_final": "PP192 log price + clip((PP198 log price - PP192 log price) * p95_regularized_weight, row_cap)",
    "micro_blend": "PP222 balanced log price + clip((target log price - PP222 balanced log price) * share, row_cap)",
    "selection_goal": "Keep PP222 balanced p95 win-rate while moving MAPE toward PP222 aggressive."
  }
}
```