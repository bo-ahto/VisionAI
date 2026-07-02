# PP-OPT229~234 Warm PP228 p95-win recovery without MAPE loss 결과

- 작성일: 2026-06-10 11:53
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 목적: PP228 균형 후보를 기준으로 공격형 이동과 p95 회복 이동을 row별로 제한 적용
- 결론: 운영 후보 MAPE 0.269889, p95 win rate 0.747756. PP228 균형 대비 MAPE 변화 -0.000000005, p95 win rate 변화 +0.000000.

## 주요 후보 test 비교
| candidate | family | item_id | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt228_mape_challenger_pp222_narrow_balance__source=ppopt224_risk_shaped_cap__curve_1p25__s_1p26__basecap_0p0054__shrink_0p86 | reference_prior | REFERENCE | 0.140975 | 0.269889 | 0.807326 | 0.397455 | -0.001506 | -0.000804 |
| ppopt228_operational_pp222_narrow_balance__source=ppopt224_risk_shaped_cap__curve_1p25__s_1p26__basecap_0p0052__shrink_0p94 | reference_prior | REFERENCE | 0.140975 | 0.269889 | 0.807326 | 0.397455 | -0.001506 | -0.000804 |
| ppopt234_operational_pp228_p95_recovery__source=ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve_1p25 | pp228_p95_recovery_operational_selection | PP-OPT234 | 0.140975 | 0.269889 | 0.807326 | 0.397456 | -0.001505 | -0.000804 |
| ppopt234_balanced_pp228_p95_recovery__source=ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve_1p25 | pp228_p95_recovery_balanced_selection | PP-OPT234 | 0.140975 | 0.269889 | 0.807326 | 0.397456 | -0.001505 | -0.000804 |
| ppopt234_mape_challenger_pp228_p95_recovery__source=ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve_1p25 | pp228_p95_recovery_mape_selection | PP-OPT234 | 0.140975 | 0.269889 | 0.807326 | 0.397456 | -0.001505 | -0.000804 |
| ppopt234_p95_recovery_pp228_p95_recovery__source=ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve_1p25 | pp228_p95_recovery_p95_win_selection | PP-OPT234 | 0.140975 | 0.269889 | 0.807326 | 0.397456 | -0.001505 | -0.000804 |
| ppopt228_balanced_pp222_narrow_balance__source=ppopt223_neighborhood__thr_0p015__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00545__shrink_0p92 | reference_prior | REFERENCE | 0.140975 | 0.269890 | 0.807326 | 0.397456 | -0.001505 | -0.000804 |
| ppopt228_p95_guarded_pp222_narrow_balance__source=ppopt222_p95_guarded_p95_regularized_rebuild__source_ppopt210_p95_guarded_pp204_local_refinement__source_ppopt204_p95_gu | reference_prior | REFERENCE | 0.140094 | 0.269949 | 0.807255 | 0.397482 | -0.001446 | -0.000875 |
| ppopt234_p95_guarded_pp228_p95_recovery__source=ppopt228_p95_guarded_pp222_narrow_balance__source_ppopt222_p95_guarded_p95_regularized_rebuild__source_ppopt210_p95_guar | pp228_p95_recovery_p95_guarded_selection | PP-OPT234 | 0.140094 | 0.269949 | 0.807255 | 0.397482 | -0.001446 | -0.000875 |
| reference_pp64_current_best | reference_prior | REFERENCE | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | p95_test_MAPE | p95_test_p95_APE | operational_pass_vs_incumbent | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PP228 balanced to aggressive gated lift | 432 | 0.269889 | 0.807326 | 0.269889 | 0.807326 | False | pp228_aggressive_gated_lift | ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00018__shrink=0p55__curve=0p75 |
| 6 | final PP228 p95 recovery decision | 6 | 0.269889 | 0.807326 | 0.270269 | 0.805949 | False | pp228_p95_recovery_balanced_selection | ppopt234_balanced_pp228_p95_recovery__source=ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve_1p25 |
| 4 | aggressive lift plus p95 recovery offset | 162 | 0.269889 | 0.807326 | 0.269889 | 0.807326 | False | pp228_aggressive_plus_p95_recovery_offset | ppopt232_dual_offset__target=guarded__as=0p5__rs=0p08__acap=0p00012__rcap=0p00012 |
| 2 | PP228 balanced to MAPE challenger tiny lift | 60 | 0.269890 | 0.807326 | 0.269890 | 0.807326 | False | pp228_mape_tiny_lift | ppopt230_mape_tiny_lift__s=0p12__basecap=0p00014__shrink=0p75 |
| 3 | p95 recovery support | 120 | 0.269890 | 0.807326 | 0.269890 | 0.807326 | False | pp228_p95_recovery_support | ppopt231_p95_recovery_support__target=guarded__s=0p08__basecap=0p00014__shrink=0p5 |
| 5 | row-level conservative router | 36 | 0.269890 | 0.807326 | 0.269890 | 0.807326 | False | pp228_row_level_conservative_router | ppopt233_conservative_router__athr=0p2__gthr=0p18__cap=0p0001 |

## 탐색 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt234_p95_guarded_pp228_p95_recovery__source=ppopt228_p95_guarded_pp222_narrow_balance__source_ppopt222_p95_guarded_p95_regularized_rebuild__source_ppopt210_p95_guar | PP-OPT234 | pp228_p95_recovery_p95_guarded_selection | 0.269949 | 0.807255 | -0.001446 | -0.000875 | -0.001537 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00018__shrink=0p55__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00018__shrink=0p55__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00018__shrink=0p55__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00018__shrink=0p75__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00018__shrink=0p75__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00018__shrink=0p75__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00018__shrink=0p9__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00018__shrink=0p9__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00018__shrink=0p9__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00028__shrink=0p55__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00028__shrink=0p55__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00028__shrink=0p55__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00028__shrink=0p75__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00028__shrink=0p75__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00028__shrink=0p75__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00028__shrink=0p9__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00028__shrink=0p9__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00028__shrink=0p9__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00042__shrink=0p55__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00042__shrink=0p55__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00042__shrink=0p55__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00042__shrink=0p75__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00042__shrink=0p75__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00042__shrink=0p75__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00042__shrink=0p9__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00042__shrink=0p9__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00042__shrink=0p9__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p0006__shrink=0p55__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p0006__shrink=0p55__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p0006__shrink=0p55__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p0006__shrink=0p75__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p0006__shrink=0p75__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p0006__shrink=0p75__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p0006__shrink=0p9__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p0006__shrink=0p9__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p0006__shrink=0p9__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt234_balanced_pp228_p95_recovery__source=ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve_1p25 | PP-OPT234 | pp228_p95_recovery_balanced_selection | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt234_mape_challenger_pp228_p95_recovery__source=ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve_1p25 | PP-OPT234 | pp228_p95_recovery_mape_selection | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt234_operational_pp228_p95_recovery__source=ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve_1p25 | PP-OPT234 | pp228_p95_recovery_operational_selection | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt234_p95_recovery_pp228_p95_recovery__source=ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve_1p25 | PP-OPT234 | pp228_p95_recovery_p95_win_selection | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p00018__shrink=0p55__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p00018__shrink=0p55__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p00018__shrink=0p55__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p00018__shrink=0p75__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p00018__shrink=0p75__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p00018__shrink=0p75__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p00018__shrink=0p9__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p00018__shrink=0p9__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p00018__shrink=0p9__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p00028__shrink=0p55__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p00028__shrink=0p55__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p00028__shrink=0p55__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p00028__shrink=0p75__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p00028__shrink=0p75__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p00028__shrink=0p75__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p00028__shrink=0p9__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p00028__shrink=0p9__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p00028__shrink=0p9__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p00042__shrink=0p55__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p00042__shrink=0p55__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p00042__shrink=0p55__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p00042__shrink=0p75__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p00042__shrink=0p75__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p00042__shrink=0p75__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p00042__shrink=0p9__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p00042__shrink=0p9__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p00042__shrink=0p9__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p0006__shrink=0p55__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p0006__shrink=0p55__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p0006__shrink=0p55__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p0006__shrink=0p75__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p0006__shrink=0p75__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p0006__shrink=0p75__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p0006__shrink=0p9__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p0006__shrink=0p9__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p6__basecap=0p0006__shrink=0p9__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=guarded__as=0p5__rs=0p08__acap=0p00012__rcap=0p00012 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=guarded__as=0p5__rs=0p08__acap=0p00012__rcap=0p0002 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=guarded__as=0p5__rs=0p08__acap=0p00012__rcap=6em05 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=guarded__as=0p5__rs=0p08__acap=0p00022__rcap=0p00012 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=guarded__as=0p5__rs=0p08__acap=0p00022__rcap=0p0002 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=guarded__as=0p5__rs=0p08__acap=0p00022__rcap=6em05 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=guarded__as=0p5__rs=0p08__acap=0p00034__rcap=0p00012 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=guarded__as=0p5__rs=0p08__acap=0p00034__rcap=0p0002 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=guarded__as=0p5__rs=0p08__acap=0p00034__rcap=6em05 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=guarded__as=0p5__rs=0p16__acap=0p00012__rcap=0p00012 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=guarded__as=0p5__rs=0p16__acap=0p00012__rcap=0p0002 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=guarded__as=0p5__rs=0p16__acap=0p00012__rcap=6em05 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=guarded__as=0p5__rs=0p16__acap=0p00022__rcap=0p00012 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=guarded__as=0p5__rs=0p16__acap=0p00022__rcap=0p0002 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=guarded__as=0p5__rs=0p16__acap=0p00022__rcap=6em05 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=guarded__as=0p5__rs=0p16__acap=0p00034__rcap=0p00012 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=guarded__as=0p5__rs=0p16__acap=0p00034__rcap=0p0002 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=guarded__as=0p5__rs=0p16__acap=0p00034__rcap=6em05 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=guarded__as=0p5__rs=0p28__acap=0p00012__rcap=0p00012 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=guarded__as=0p5__rs=0p28__acap=0p00012__rcap=0p0002 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=guarded__as=0p5__rs=0p28__acap=0p00012__rcap=6em05 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=guarded__as=0p5__rs=0p28__acap=0p00022__rcap=0p00012 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=guarded__as=0p5__rs=0p28__acap=0p00022__rcap=0p0002 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=guarded__as=0p5__rs=0p28__acap=0p00022__rcap=6em05 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=guarded__as=0p5__rs=0p28__acap=0p00034__rcap=0p00012 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=guarded__as=0p5__rs=0p28__acap=0p00034__rcap=0p0002 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=guarded__as=0p5__rs=0p28__acap=0p00034__rcap=6em05 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=recovery__as=0p5__rs=0p08__acap=0p00012__rcap=0p00012 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=recovery__as=0p5__rs=0p08__acap=0p00012__rcap=0p0002 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=recovery__as=0p5__rs=0p08__acap=0p00012__rcap=6em05 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=recovery__as=0p5__rs=0p08__acap=0p00022__rcap=0p00012 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=recovery__as=0p5__rs=0p08__acap=0p00022__rcap=0p0002 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=recovery__as=0p5__rs=0p08__acap=0p00022__rcap=6em05 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=recovery__as=0p5__rs=0p08__acap=0p00034__rcap=0p00012 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=recovery__as=0p5__rs=0p08__acap=0p00034__rcap=0p0002 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=recovery__as=0p5__rs=0p08__acap=0p00034__rcap=6em05 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=recovery__as=0p5__rs=0p16__acap=0p00012__rcap=0p00012 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=recovery__as=0p5__rs=0p16__acap=0p00012__rcap=0p0002 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=recovery__as=0p5__rs=0p16__acap=0p00012__rcap=6em05 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=recovery__as=0p5__rs=0p16__acap=0p00022__rcap=0p00012 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=recovery__as=0p5__rs=0p16__acap=0p00022__rcap=0p0002 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=recovery__as=0p5__rs=0p16__acap=0p00022__rcap=6em05 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=recovery__as=0p5__rs=0p16__acap=0p00034__rcap=0p00012 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=recovery__as=0p5__rs=0p16__acap=0p00034__rcap=0p0002 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=recovery__as=0p5__rs=0p16__acap=0p00034__rcap=6em05 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=recovery__as=0p5__rs=0p28__acap=0p00012__rcap=0p00012 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=recovery__as=0p5__rs=0p28__acap=0p00012__rcap=0p0002 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=recovery__as=0p5__rs=0p28__acap=0p00012__rcap=6em05 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=recovery__as=0p5__rs=0p28__acap=0p00022__rcap=0p00012 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=recovery__as=0p5__rs=0p28__acap=0p00022__rcap=0p0002 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=recovery__as=0p5__rs=0p28__acap=0p00022__rcap=6em05 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=recovery__as=0p5__rs=0p28__acap=0p00034__rcap=0p00012 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=recovery__as=0p5__rs=0p28__acap=0p00034__rcap=0p0002 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt232_dual_offset__target=recovery__as=0p5__rs=0p28__acap=0p00034__rcap=6em05 | PP-OPT232 | pp228_aggressive_plus_p95_recovery_offset | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p45__basecap=0p00018__shrink=0p55__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p45__basecap=0p00018__shrink=0p55__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p45__basecap=0p00018__shrink=0p55__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p45__basecap=0p00018__shrink=0p75__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p45__basecap=0p00018__shrink=0p75__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p45__basecap=0p00018__shrink=0p75__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p45__basecap=0p00018__shrink=0p9__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p45__basecap=0p00018__shrink=0p9__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p45__basecap=0p00018__shrink=0p9__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p45__basecap=0p00028__shrink=0p55__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p45__basecap=0p00028__shrink=0p55__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p45__basecap=0p00028__shrink=0p55__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p45__basecap=0p00028__shrink=0p75__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p45__basecap=0p00028__shrink=0p75__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p45__basecap=0p00028__shrink=0p75__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p45__basecap=0p00028__shrink=0p9__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p45__basecap=0p00028__shrink=0p9__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p45__basecap=0p00028__shrink=0p9__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p45__basecap=0p00042__shrink=0p55__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p45__basecap=0p00042__shrink=0p55__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p45__basecap=0p00042__shrink=0p55__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p45__basecap=0p00042__shrink=0p75__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p45__basecap=0p00042__shrink=0p75__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p45__basecap=0p00042__shrink=0p75__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p45__basecap=0p00042__shrink=0p9__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p45__basecap=0p00042__shrink=0p9__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p45__basecap=0p00042__shrink=0p9__curve=1p25 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p45__basecap=0p0006__shrink=0p55__curve=0p75 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt229_aggressive_gated_lift__seg=price_conf__s=0p45__basecap=0p0006__shrink=0p55__curve=1p0 | PP-OPT229 | pp228_aggressive_gated_lift | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |

## 선택 후보 반복 안정성
| candidate_label | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_vs_pp64_MAPE | fixed_test_delta_vs_pp64_p95_APE | avg_pp64_MAPE_win_rate | avg_pp64_p95_win_rate | replacement_score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pp228_operational_reference | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018842 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve___49fa782c9b | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve___87a7c7f0b2 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve___f950555308 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p75__curve___3f1af44ad5 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p75__curve___cffead939c | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p75__curve___e598feee39 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p9__curve_0__72fd9f9f00 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p9__curve_1__d7df3c6011 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p9__curve_1__f7b4d1d4a2 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00028__shrink_0p55__curve___15cd2c70ef | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00028__shrink_0p55__curve___bb14f00f6c | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00028__shrink_0p55__curve___df4bc9f2d6 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00028__shrink_0p75__curve___049527dfc5 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00028__shrink_0p75__curve___a1f2e73f9d | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00028__shrink_0p75__curve___b3ed9db272 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00028__shrink_0p9__curve_0__f0959ac2ed | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00028__shrink_0p9__curve_1__09008f21f8 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00028__shrink_0p9__curve_1__99706d8228 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00042__shrink_0p55__curve___5b5db39947 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00042__shrink_0p55__curve___8a46ede954 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00042__shrink_0p55__curve___e896eaf4f3 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00042__shrink_0p75__curve___5665b06c3d | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00042__shrink_0p75__curve___5c65c79bfa | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00042__shrink_0p75__curve___a7fd2e15c6 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00042__shrink_0p9__curve_0__78f4337672 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00042__shrink_0p9__curve_1__18354f0462 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00042__shrink_0p9__curve_1__d2a75c51f8 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p0006__shrink_0p55__curve_0__3655b779c8 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p0006__shrink_0p55__curve_1__409e2742a7 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p0006__shrink_0p55__curve_1__98f4e73ff1 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p0006__shrink_0p75__curve_0__52314b1c3e | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p0006__shrink_0p75__curve_1__88d70ed493 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p0006__shrink_0p75__curve_1__9c806cb4eb | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p0006__shrink_0p9__curve_0p__0824c58952 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p0006__shrink_0p9__curve_1p__37959200d1 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p0006__shrink_0p9__curve_1p__c55b7b156c | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| pp234_balanced_pp228_p95_recovery_candidate | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| pp234_mape_pp228_p95_recovery_candidate | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| pp234_operational_pp228_p95_recovery_candidate | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| pp234_p95_recovery_pp228_p95_recovery_candidate | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| pp222_aggressive_reference | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p00018__shrink_0p55__curve_0__782b93eafc | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p00018__shrink_0p55__curve_1__23b47c8079 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p00018__shrink_0p55__curve_1__d1bd87c28e | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p00018__shrink_0p75__curve_0__6d72b039a4 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p00018__shrink_0p75__curve_1__5047e926ea | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p00018__shrink_0p75__curve_1__f2fa7d076c | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p00018__shrink_0p9__curve_0p__cd3c8d49da | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p00018__shrink_0p9__curve_1p__99c6c353e8 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p00018__shrink_0p9__curve_1p__9c9fd3d44d | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p00028__shrink_0p55__curve_0__a2e04914c1 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p00028__shrink_0p55__curve_1__27a93367f5 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p00028__shrink_0p55__curve_1__46235c197a | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p00028__shrink_0p75__curve_0__ff8b78c32c | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p00028__shrink_0p75__curve_1__580b4b83f9 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p00028__shrink_0p75__curve_1__ea7431115d | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p00028__shrink_0p9__curve_0p__704a76a0bc | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p00028__shrink_0p9__curve_1p__239fb05565 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p00028__shrink_0p9__curve_1p__2f940bc96e | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p00042__shrink_0p55__curve_0__2f3cde12bf | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p00042__shrink_0p55__curve_1__f81f0e11de | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p00042__shrink_0p55__curve_1__ffa5ac533b | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p00042__shrink_0p75__curve_0__db6dc6dac7 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p00042__shrink_0p75__curve_1__ab68d27d49 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p00042__shrink_0p75__curve_1__d9d396c8cc | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p00042__shrink_0p9__curve_0p__7f200a8487 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p00042__shrink_0p9__curve_1p__46ef654310 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p00042__shrink_0p9__curve_1p__d6c51abfcf | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p0006__shrink_0p55__curve_0p__1d2bdc5d5b | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p0006__shrink_0p55__curve_1p__aa4158970f | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p0006__shrink_0p55__curve_1p__af1b871f76 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p0006__shrink_0p75__curve_0p__0b2cf1fac9 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p0006__shrink_0p75__curve_1p__39253b05f8 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p0006__shrink_0p75__curve_1p__46f19299d0 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p0006__shrink_0p9__curve_0p7__3dd6540c7e | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p0006__shrink_0p9__curve_1p0__2f958ccb27 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p6__basecap_0p0006__shrink_0p9__curve_1p2__39cbf9f687 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_guarded__as_0p5__rs_0p08__acap_0p00012__rcap_0p00012__09b28a387d | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_guarded__as_0p5__rs_0p08__acap_0p00012__rcap_0p0002__612c19ab01 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_guarded__as_0p5__rs_0p08__acap_0p00012__rcap_6em05__69ec230b8d | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_guarded__as_0p5__rs_0p08__acap_0p00022__rcap_0p00012__fd8ee0bbb4 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_guarded__as_0p5__rs_0p08__acap_0p00022__rcap_0p0002__ae842eb531 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_guarded__as_0p5__rs_0p08__acap_0p00022__rcap_6em05__fb49763941 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_guarded__as_0p5__rs_0p08__acap_0p00034__rcap_0p00012__ead4b7ce85 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_guarded__as_0p5__rs_0p08__acap_0p00034__rcap_0p0002__28cb15fe6b | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_guarded__as_0p5__rs_0p08__acap_0p00034__rcap_6em05__cfb6b0c2eb | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_guarded__as_0p5__rs_0p16__acap_0p00012__rcap_0p00012__072518f09e | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_guarded__as_0p5__rs_0p16__acap_0p00012__rcap_0p0002__f5a81c9ed3 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_guarded__as_0p5__rs_0p16__acap_0p00012__rcap_6em05__3eff0051d7 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_guarded__as_0p5__rs_0p16__acap_0p00022__rcap_0p00012__5d6cebc567 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_guarded__as_0p5__rs_0p16__acap_0p00022__rcap_0p0002__cb3fbb4169 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_guarded__as_0p5__rs_0p16__acap_0p00022__rcap_6em05__330ebb70c0 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_guarded__as_0p5__rs_0p16__acap_0p00034__rcap_0p00012__962ffd8300 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_guarded__as_0p5__rs_0p16__acap_0p00034__rcap_0p0002__cb193aba85 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_guarded__as_0p5__rs_0p16__acap_0p00034__rcap_6em05__986a26965c | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_guarded__as_0p5__rs_0p28__acap_0p00012__rcap_0p00012__72f3cabf72 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_guarded__as_0p5__rs_0p28__acap_0p00012__rcap_0p0002__5ac9db9be4 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_guarded__as_0p5__rs_0p28__acap_0p00012__rcap_6em05__55679b6240 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_guarded__as_0p5__rs_0p28__acap_0p00022__rcap_0p00012__373be92dcd | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_guarded__as_0p5__rs_0p28__acap_0p00022__rcap_0p0002__d9267ade04 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_guarded__as_0p5__rs_0p28__acap_0p00022__rcap_6em05__d5ba1f2ee3 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_guarded__as_0p5__rs_0p28__acap_0p00034__rcap_0p00012__8e329dd49a | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_guarded__as_0p5__rs_0p28__acap_0p00034__rcap_0p0002__299c0db1c2 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_guarded__as_0p5__rs_0p28__acap_0p00034__rcap_6em05__1d4c0dc2b0 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_recovery__as_0p5__rs_0p08__acap_0p00012__rcap_0p00012__25a9b5c05f | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_recovery__as_0p5__rs_0p08__acap_0p00012__rcap_0p0002__b43b71df22 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_recovery__as_0p5__rs_0p08__acap_0p00012__rcap_6em05__961ce354e5 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_recovery__as_0p5__rs_0p08__acap_0p00022__rcap_0p00012__cc868cf879 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_recovery__as_0p5__rs_0p08__acap_0p00022__rcap_0p0002__53273305fa | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_recovery__as_0p5__rs_0p08__acap_0p00022__rcap_6em05__12b1b4f899 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_recovery__as_0p5__rs_0p08__acap_0p00034__rcap_0p00012__0bcfef2efe | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_recovery__as_0p5__rs_0p08__acap_0p00034__rcap_0p0002__c69284c46d | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_recovery__as_0p5__rs_0p08__acap_0p00034__rcap_6em05__3a2c04be74 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_recovery__as_0p5__rs_0p16__acap_0p00012__rcap_0p00012__edb7aa8974 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_recovery__as_0p5__rs_0p16__acap_0p00012__rcap_0p0002__d5c9a3b096 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_recovery__as_0p5__rs_0p16__acap_0p00012__rcap_6em05__6294de344b | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_recovery__as_0p5__rs_0p16__acap_0p00022__rcap_0p00012__9be3e0472d | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_recovery__as_0p5__rs_0p16__acap_0p00022__rcap_0p0002__7c1e7aefa5 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_recovery__as_0p5__rs_0p16__acap_0p00022__rcap_6em05__b49368917e | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_recovery__as_0p5__rs_0p16__acap_0p00034__rcap_0p00012__21fb552368 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_recovery__as_0p5__rs_0p16__acap_0p00034__rcap_0p0002__f25f6fe93b | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_recovery__as_0p5__rs_0p16__acap_0p00034__rcap_6em05__0ba2b2f755 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_recovery__as_0p5__rs_0p28__acap_0p00012__rcap_0p00012__b6ed1d50c0 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_recovery__as_0p5__rs_0p28__acap_0p00012__rcap_0p0002__a65a301c91 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_recovery__as_0p5__rs_0p28__acap_0p00012__rcap_6em05__fa05e6851d | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_recovery__as_0p5__rs_0p28__acap_0p00022__rcap_0p00012__7d33dd1867 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_recovery__as_0p5__rs_0p28__acap_0p00022__rcap_0p0002__0c90b33b40 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_recovery__as_0p5__rs_0p28__acap_0p00022__rcap_6em05__ffc697df95 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_recovery__as_0p5__rs_0p28__acap_0p00034__rcap_0p00012__849c0a0334 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_recovery__as_0p5__rs_0p28__acap_0p00034__rcap_0p0002__d5aaca2ef0 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt232_dual_offset__target_recovery__as_0p5__rs_0p28__acap_0p00034__rcap_6em05__c735eb66fd | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p45__basecap_0p00018__shrink_0p55__curve___035048ac1f | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p45__basecap_0p00018__shrink_0p55__curve___f3b0b932fd | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p45__basecap_0p00018__shrink_0p55__curve___f79e28b7cd | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p45__basecap_0p00018__shrink_0p75__curve___4ccc3de136 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p45__basecap_0p00018__shrink_0p75__curve___885f3c8f32 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p45__basecap_0p00018__shrink_0p75__curve___d7d0be1829 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p45__basecap_0p00018__shrink_0p9__curve_0__2be6ae1664 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p45__basecap_0p00018__shrink_0p9__curve_1__6c03c7327d | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p45__basecap_0p00018__shrink_0p9__curve_1__b63375fd4c | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p45__basecap_0p00028__shrink_0p55__curve___0026f78429 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p45__basecap_0p00028__shrink_0p55__curve___ad0a3e6ce9 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p45__basecap_0p00028__shrink_0p55__curve___d70dadd92f | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p45__basecap_0p00028__shrink_0p75__curve___3f03b0e0e7 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p45__basecap_0p00028__shrink_0p75__curve___77bb3aa95a | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p45__basecap_0p00028__shrink_0p75__curve___83df0d3bdd | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p45__basecap_0p00028__shrink_0p9__curve_0__fb431597d5 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p45__basecap_0p00028__shrink_0p9__curve_1__9303071e3e | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p45__basecap_0p00028__shrink_0p9__curve_1__d6c7f7adaa | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p45__basecap_0p00042__shrink_0p55__curve___0621bb53ef | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p45__basecap_0p00042__shrink_0p55__curve___d13367d025 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p45__basecap_0p00042__shrink_0p55__curve___dd08bb364c | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p45__basecap_0p00042__shrink_0p75__curve___44aceafa64 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p45__basecap_0p00042__shrink_0p75__curve___4bb396048f | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p45__basecap_0p00042__shrink_0p75__curve___f1cf0dd0d8 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p45__basecap_0p00042__shrink_0p9__curve_0__0654d0fd70 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p45__basecap_0p00042__shrink_0p9__curve_1__0d6a95edf0 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p45__basecap_0p00042__shrink_0p9__curve_1__27f571e6e0 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p45__basecap_0p0006__shrink_0p55__curve_0__5aabf23206 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p45__basecap_0p0006__shrink_0p55__curve_1__021c3484ff | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p45__basecap_0p0006__shrink_0p55__curve_1__c16dc111b6 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| pp228_balanced_reference | 0.269890 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| pp222_balanced_reference | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| pp210_operational_reference | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| pp204_operational_reference | 0.269894 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018824 |
| pp228_mape_reference | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953526 | 0.747115 | -0.018816 |
| pp192_operational_reference | 0.269914 | 0.807326 | -0.000650 | -0.000173 | 0.953526 | 0.750962 | -0.018791 |
| pp216_p95_recovery_reference | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952885 | 0.749679 | -0.018782 |
| pp222_p95_guarded_reference | 0.269949 | 0.807255 | -0.000615 | -0.000244 | 0.950962 | 0.751603 | -0.018653 |
| pp228_p95_guarded_reference | 0.269949 | 0.807255 | -0.000615 | -0.000244 | 0.950962 | 0.751603 | -0.018653 |
| pp234_p95_guarded_pp228_p95_recovery_candidate | 0.269949 | 0.807255 | -0.000615 | -0.000244 | 0.950962 | 0.751603 | -0.018653 |
| pp148_operational_reference | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| pp126_operational_reference | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| pp70_refinement_candidate | 0.270561 | 0.807490 | -0.000003 | -0.000009 | 0.786859 | 0.398077 | -0.011477 |
| pp148_p95_reference | 0.270269 | 0.805949 | -0.000295 | -0.001549 | 0.598397 | 0.500962 | -0.004079 |
| pp228_p95_extreme_reference | 0.270269 | 0.805949 | -0.000295 | -0.001549 | 0.598397 | 0.500962 | -0.004079 |
| pp234_p95_extreme_pp228_p95_recovery_candidate | 0.270269 | 0.805949 | -0.000295 | -0.001549 | 0.598397 | 0.500962 | -0.004079 |
| pp64_current_best | 0.270564 | 0.807499 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.020000 |
| incumbent_pp7 | 0.271395 | 0.808130 | 0.000831 | 0.000631 | 0.002244 | 0.450641 | 0.022238 |

## 실행 설정
```json
{
  "experiment_id": "PP-OPT229-234",
  "experiment_slug": "PP-OPT229_234_warm_pp228_p95_recovery_without_mape_loss",
  "created_at": "2026-06-10T11:52:48",
  "previous_experiment": "experiments/track6/PP-OPT223_228_warm_pp222_narrow_balance_refinement",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 839,
  "prediction_rows": 944714,
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
  "prior_decision": {
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
  "selection_decision": {
    "operational_label": "candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve___49fa782c9b",
    "operational_candidate": "ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00018__shrink=0p55__curve=1p25",
    "operational_fixed_test_MAPE": 0.2698894975680414,
    "operational_fixed_test_p95_APE": 0.8073255046591389,
    "operational_delta_vs_pp64_MAPE": -0.0006745443476189328,
    "operational_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "operational_delta_vs_pp228_balanced_MAPE": -5.257381030521202e-09,
    "operational_delta_vs_pp228_balanced_p95_win_rate": 0.0,
    "operational_delta_vs_pp228_operational_MAPE": 3.8978966737657217e-07,
    "operational_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "operational_avg_pp64_p95_win_rate": 0.7477564102564102,
    "operational_replacement_score": -0.01882839050146509,
    "balanced_label": "candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve___49fa782c9b",
    "balanced_candidate": "ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00018__shrink=0p55__curve=1p25",
    "balanced_fixed_test_MAPE": 0.2698894975680414,
    "balanced_fixed_test_p95_APE": 0.8073255046591389,
    "balanced_delta_vs_pp64_MAPE": -0.0006745443476189328,
    "balanced_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "balanced_delta_vs_pp228_balanced_MAPE": -5.257381030521202e-09,
    "balanced_delta_vs_pp228_balanced_p95_win_rate": 0.0,
    "balanced_delta_vs_pp228_operational_MAPE": 3.8978966737657217e-07,
    "balanced_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "balanced_avg_pp64_p95_win_rate": 0.7477564102564102,
    "balanced_replacement_score": -0.01882839050146509,
    "mape_challenger_label": "candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve___49fa782c9b",
    "mape_challenger_candidate": "ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00018__shrink=0p55__curve=1p25",
    "mape_challenger_fixed_test_MAPE": 0.2698894975680414,
    "mape_challenger_fixed_test_p95_APE": 0.8073255046591389,
    "mape_challenger_delta_vs_pp64_MAPE": -0.0006745443476189328,
    "mape_challenger_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "mape_challenger_delta_vs_pp228_balanced_MAPE": -5.257381030521202e-09,
    "mape_challenger_delta_vs_pp228_balanced_p95_win_rate": 0.0,
    "mape_challenger_delta_vs_pp228_operational_MAPE": 3.8978966737657217e-07,
    "mape_challenger_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "mape_challenger_avg_pp64_p95_win_rate": 0.7477564102564102,
    "mape_challenger_replacement_score": -0.01882839050146509,
    "p95_recovery_label": "candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve___49fa782c9b",
    "p95_recovery_candidate": "ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00018__shrink=0p55__curve=1p25",
    "p95_recovery_fixed_test_MAPE": 0.2698894975680414,
    "p95_recovery_fixed_test_p95_APE": 0.8073255046591389,
    "p95_recovery_delta_vs_pp64_MAPE": -0.0006745443476189328,
    "p95_recovery_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "p95_recovery_delta_vs_pp228_balanced_MAPE": -5.257381030521202e-09,
    "p95_recovery_delta_vs_pp228_balanced_p95_win_rate": 0.0,
    "p95_recovery_delta_vs_pp228_operational_MAPE": 3.8978966737657217e-07,
    "p95_recovery_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "p95_recovery_avg_pp64_p95_win_rate": 0.7477564102564102,
    "p95_recovery_replacement_score": -0.01882839050146509,
    "p95_guarded_label": "pp228_p95_guarded_reference",
    "p95_guarded_candidate": "ppopt228_p95_guarded_pp222_narrow_balance__source=ppopt222_p95_guarded_p95_regularized_rebuild__source_ppopt210_p95_guarded_pp204_local_refinement__source_ppopt204_p95_gu",
    "p95_guarded_fixed_test_MAPE": 0.26994920114208765,
    "p95_guarded_fixed_test_p95_APE": 0.8072545738314347,
    "p95_guarded_delta_vs_pp64_MAPE": -0.0006148407735727113,
    "p95_guarded_delta_vs_pp64_p95_APE": -0.0002442784746751192,
    "p95_guarded_delta_vs_pp228_balanced_MAPE": 5.969831666519099e-05,
    "p95_guarded_delta_vs_pp228_balanced_p95_win_rate": 0.0038461538461540545,
    "p95_guarded_delta_vs_pp228_operational_MAPE": 6.009336371359808e-05,
    "p95_guarded_avg_pp64_MAPE_win_rate": 0.9509615384615384,
    "p95_guarded_avg_pp64_p95_win_rate": 0.7516025641025642,
    "p95_guarded_replacement_score": -0.01865330231203425,
    "p95_extreme_label": "pp228_p95_extreme_reference",
    "p95_extreme_candidate": "ppopt228_p95_extreme_pp222_narrow_balance__source=reference_pp148_p95",
    "p95_extreme_fixed_test_MAPE": 0.27026892590910795,
    "p95_extreme_fixed_test_p95_APE": 0.8059493758221674,
    "p95_extreme_delta_vs_pp64_MAPE": -0.00029511600655240944,
    "p95_extreme_delta_vs_pp64_p95_APE": -0.0015494764839424358,
    "p95_extreme_delta_vs_pp228_balanced_MAPE": 0.0003794230836854928,
    "p95_extreme_delta_vs_pp228_balanced_p95_win_rate": -0.2467948717948717,
    "p95_extreme_delta_vs_pp228_operational_MAPE": 0.0003798181307338999,
    "p95_extreme_avg_pp64_MAPE_win_rate": 0.5983974358974359,
    "p95_extreme_avg_pp64_p95_win_rate": 0.5009615384615385,
    "p95_extreme_replacement_score": -0.0040792899192624915,
    "operational_protocol_candidate": "ppopt234_operational_pp228_p95_recovery__source=ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve_1p25",
    "balanced_protocol_candidate": "ppopt234_balanced_pp228_p95_recovery__source=ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve_1p25",
    "mape_challenger_protocol_candidate": "ppopt234_mape_challenger_pp228_p95_recovery__source=ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve_1p25",
    "p95_recovery_protocol_candidate": "ppopt234_p95_recovery_pp228_p95_recovery__source=ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve_1p25",
    "p95_guarded_protocol_candidate": "ppopt234_p95_guarded_pp228_p95_recovery__source=ppopt228_p95_guarded_pp222_narrow_balance__source_ppopt222_p95_guarded_p95_regularized_rebuild__source_ppopt210_p95_guar",
    "p95_extreme_protocol_candidate": "ppopt234_p95_extreme_pp228_p95_recovery__source=ppopt228_p95_extreme_pp222_narrow_balance__source_reference_pp148_p95"
  },
  "items": [
    {
      "item_id": "PP-OPT229",
      "priority": "1",
      "title": "PP228 balanced to aggressive gated lift",
      "description": "PP228 균형 후보에서 공격형 후보로 이동하되, validation 구간 신호와 row risk cap으로 제한."
    },
    {
      "item_id": "PP-OPT230",
      "priority": "2",
      "title": "PP228 balanced to MAPE challenger tiny lift",
      "description": "MAPE 최저 후보 방향의 이동을 더 작은 cap으로만 허용."
    },
    {
      "item_id": "PP-OPT231",
      "priority": "3",
      "title": "p95 recovery support",
      "description": "PP216 p95-recovery와 PP222 p95-guarded 후보 쪽 이동을 p95 회복 신호가 있는 row에만 적용."
    },
    {
      "item_id": "PP-OPT232",
      "priority": "4",
      "title": "aggressive lift plus p95 recovery offset",
      "description": "공격형 이동 후 p95 회복 이동을 같이 넣어 MAPE 개선과 p95 win rate 회복의 균형을 탐색."
    },
    {
      "item_id": "PP-OPT233",
      "priority": "5",
      "title": "row-level conservative router",
      "description": "row별로 균형, 공격형, p95 회복 후보 중 이동 방향을 선택."
    },
    {
      "item_id": "PP-OPT234",
      "priority": "6",
      "title": "final PP228 p95 recovery decision",
      "description": "PP228 균형 후보 대비 MAPE 손상 없이 p95 win rate 또는 replacement score가 개선되는지 최종 선택."
    }
  ],
  "router_formula": {
    "base": "PP228 balanced log price",
    "aggressive_move": "clip((PP228 operational log price - PP228 balanced log price) * aggressive_weight, aggressive_cap)",
    "mape_move": "clip((PP228 MAPE challenger log price - PP228 balanced log price) * mape_weight, mape_cap)",
    "p95_recovery_move": "clip((p95 recovery log price - PP228 balanced log price) * recovery_weight, recovery_cap)",
    "dual_final": "PP228 balanced log price + aggressive_move + p95_recovery_move",
    "selection_goal": "Keep PP228 balanced p95 win-rate and avoid fixed-test MAPE loss while improving replacement score."
  }
}
```