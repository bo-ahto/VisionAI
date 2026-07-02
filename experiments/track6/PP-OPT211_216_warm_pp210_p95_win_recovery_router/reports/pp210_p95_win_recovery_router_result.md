# PP-OPT211~216 Warm PP210 p95-win recovery router 결과

- 작성일: 2026-06-10 11:12
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 목적: PP210의 MAPE 이득을 유지하면서 repeated p95 win rate를 PP204 수준으로 회복 가능한지 확인
- 결론: 운영 후보 fixed test MAPE 0.269891, p95 0.807326. PP210 대비 MAPE +0.000000, p95 win rate +0.000000. p95 recovery 후보 p95 win rate 0.749679.

## 주요 후보 test 비교
| candidate | family | item_id | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt216_mape_challenger_pp210_p95_recovery__source=ppopt210_mape_challenger_pp204_local_refinement__source_ppopt205_local_price_conf__thr_0p04__width_0p22__s_1p16__basecap | pp210_p95_recovery_mape_selection | PP-OPT216 | 0.140975 | 0.269890 | 0.807326 | 0.397454 | -0.001505 | -0.000804 |
| ppopt210_operational_pp204_local_refinement__source=ppopt205_local_price_conf__thr_0p04__width_0p22__s_1p16__basecap_0p0055__shrink_0p9 | reference_prior | REFERENCE | 0.140975 | 0.269891 | 0.807326 | 0.397456 | -0.001504 | -0.000804 |
| ppopt216_operational_pp210_p95_recovery__source=ppopt211_segment_recovery__seg_price_conf__thr_0p08__s_0p25__cap_0p0005 | pp210_p95_recovery_operational_selection | PP-OPT216 | 0.140975 | 0.269891 | 0.807326 | 0.397456 | -0.001504 | -0.000804 |
| ppopt204_operational_pp192_pp198_winner_router__source=ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_1p0__basecap_0p006__shrink_0p8 | reference_prior | REFERENCE | 0.140975 | 0.269894 | 0.807326 | 0.397456 | -0.001501 | -0.000804 |
| ppopt198_operational_segment_router_refinement__source=ppopt194_price_conf_refine__scorethr_0p02__mix_0p25__s_1p05__cap_0p006 | reference_prior | REFERENCE | 0.140975 | 0.269894 | 0.807326 | 0.397455 | -0.001501 | -0.000804 |
| ppopt216_p95_recovery_pp210_p95_recovery__source=ppopt215_p95_aware_rebuild__thr_0p02__p95thr_m0p0001__s_1p16__basecap_0p005__shrink_1p2 | pp210_p95_recovery_p95_win_selection | PP-OPT216 | 0.140975 | 0.269898 | 0.807326 | 0.397460 | -0.001497 | -0.000804 |
| ppopt192_operational_pp180_pp186_risk_router__source=ppopt189_segment_router__seg_price_gap__scorethr_0p02__mix_0p75__s_0p95__cap_0p0025 | reference_prior | REFERENCE | 0.140975 | 0.269914 | 0.807326 | 0.397468 | -0.001481 | -0.000804 |
| ppopt180_operational_basis_generation_challenger__source=ppopt174_direct_basis__source_stack_huber_weighted__thr_0p08__s_0p3__cap_0p004 | reference_prior | REFERENCE | 0.140975 | 0.269933 | 0.807326 | 0.397475 | -0.001462 | -0.000804 |
| ppopt216_p95_guarded_pp210_p95_recovery__source=ppopt210_p95_guarded_pp204_local_refinement__source_ppopt204_p95_guarded_pp192_pp198_winner_router__source_ppopt192_p95_ | pp210_p95_recovery_p95_guarded_selection | PP-OPT216 | 0.140094 | 0.269949 | 0.807255 | 0.397482 | -0.001446 | -0.000875 |
| ppopt186_operational_huber_basis_p95_guard__source=ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p04__s_0p42__cap_0p0045 | reference_prior | REFERENCE | 0.139801 | 0.269961 | 0.807231 | 0.397497 | -0.001434 | -0.000899 |
| ppopt172_operational_pp166_tail_calibration_challenger__source=ppopt169_segment_router__source_pp162_p95_gate__seg_price_conf__thr_m0p04__s_0p5__cap_0p004 | reference_prior | REFERENCE | 0.139801 | 0.269997 | 0.807231 | 0.397516 | -0.001397 | -0.000899 |
| reference_pp126_operational | reference_prior | REFERENCE | 0.136320 | 0.270114 | 0.807490 | 0.397588 | -0.001280 | -0.000640 |
| reference_pp148_operational | reference_prior | REFERENCE | 0.139801 | 0.270140 | 0.807231 | 0.397525 | -0.001255 | -0.000899 |
| reference_pp148_p95 | reference_prior | REFERENCE | 0.141036 | 0.270269 | 0.805949 | 0.397421 | -0.001126 | -0.002181 |
| ppopt216_p95_extreme_pp210_p95_recovery__source=reference_pp148_p95 | pp210_p95_recovery_p95_extreme_selection | PP-OPT216 | 0.141036 | 0.270269 | 0.805949 | 0.397421 | -0.001126 | -0.002181 |
| reference_pp64_current_best | reference_prior | REFERENCE | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | p95_test_MAPE | p95_test_p95_APE | operational_pass_vs_incumbent | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | final PP210 p95 recovery decision | 5 | 0.269949 | 0.807255 | 0.270269 | 0.805949 | False | pp210_p95_recovery_p95_guarded_selection | ppopt216_p95_guarded_pp210_p95_recovery__source=ppopt210_p95_guarded_pp204_local_refinement__source_ppopt204_p95_guarded_pp192_pp198_winner_router__source_ppopt192_p95_ |
| 5 | p95-aware PP210 rebuild | 324 | 0.269898 | 0.807326 | 0.269891 | 0.807326 | False | pp210_p95_aware_rebuild | ppopt215_p95_aware_rebuild__thr=0p02__p95thr=m0p0001__s=1p16__basecap=0p005__shrink=1p2 |
| 4 | PP204/PP192 mixed fallback | 108 | 0.269891 | 0.807326 | 0.269891 | 0.807326 | False | pp210_mixed_fallback_recovery | ppopt214_mixed_fallback__pp192share=0p65__riskshare=0p25__s=0p25__cap=0p0005 |
| 2 | row-risk p95 recovery rollback | 144 | 0.269892 | 0.807326 | 0.269891 | 0.807326 | False | pp210_row_risk_p95_recovery | ppopt212_row_risk_recovery__riskthr=0p45__segshare=0p65__s=0p7__cap=0p0005 |
| 3 | tail-risk only fallback | 162 | 0.269892 | 0.807326 | 0.269891 | 0.807326 | False | pp210_tail_only_fallback | ppopt213_tail_only_fallback__to=pp204__riskthr=0p55__gapshare=0p25__s=0p4__cap=0p0004 |
| 1 | segment p95 recovery rollback | 256 | 0.269891 | 0.807326 | 0.269891 | 0.807326 | False | pp210_segment_p95_recovery | ppopt211_segment_recovery__seg=price_conf__thr=0p08__s=0p25__cap=0p0005 |

## 탐색 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt216_p95_guarded_pp210_p95_recovery__source=ppopt210_p95_guarded_pp204_local_refinement__source_ppopt204_p95_guarded_pp192_pp198_winner_router__source_ppopt192_p95_ | PP-OPT216 | pp210_p95_recovery_p95_guarded_selection | 0.269949 | 0.807255 | -0.001446 | -0.000875 | -0.001537 |
| ppopt215_p95_aware_rebuild__thr=0p02__p95thr=m0p0001__s=1p16__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p02__p95thr=m2em05__s=1p16__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p02__p95thr=m6em05__s=1p16__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p04__p95thr=m0p0001__s=1p16__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p04__p95thr=m2em05__s=1p16__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p04__p95thr=m6em05__s=1p16__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p08__p95thr=m0p0001__s=1p16__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p08__p95thr=m2em05__s=1p16__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p08__p95thr=m6em05__s=1p16__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p12__p95thr=m0p0001__s=1p16__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p12__p95thr=m2em05__s=1p16__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p12__p95thr=m6em05__s=1p16__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt216_p95_recovery_pp210_p95_recovery__source=ppopt215_p95_aware_rebuild__thr_0p02__p95thr_m0p0001__s_1p16__basecap_0p005__shrink_1p2 | PP-OPT216 | pp210_p95_recovery_p95_win_selection | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p02__p95thr=m0p0001__s=1p08__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p02__p95thr=m2em05__s=1p08__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p02__p95thr=m6em05__s=1p08__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p04__p95thr=m0p0001__s=1p08__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p04__p95thr=m2em05__s=1p08__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p04__p95thr=m6em05__s=1p08__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p08__p95thr=m0p0001__s=1p08__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p08__p95thr=m2em05__s=1p08__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p08__p95thr=m6em05__s=1p08__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p12__p95thr=m0p0001__s=1p08__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p12__p95thr=m2em05__s=1p08__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p12__p95thr=m6em05__s=1p08__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p02__p95thr=m0p0001__s=1p0__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p02__p95thr=m2em05__s=1p0__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p02__p95thr=m6em05__s=1p0__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p04__p95thr=m0p0001__s=1p0__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p04__p95thr=m2em05__s=1p0__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p04__p95thr=m6em05__s=1p0__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p08__p95thr=m0p0001__s=1p0__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p08__p95thr=m2em05__s=1p0__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p08__p95thr=m6em05__s=1p0__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p12__p95thr=m0p0001__s=1p0__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p12__p95thr=m2em05__s=1p0__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt215_p95_aware_rebuild__thr=0p12__p95thr=m6em05__s=1p0__basecap=0p005__shrink=1p2 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001385 |
| ppopt214_mixed_fallback__pp192share=0p65__riskshare=0p25__s=0p25__cap=0p0005 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p65__riskshare=0p25__s=0p25__cap=0p0008 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p65__riskshare=0p25__s=0p25__cap=0p0012 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p45__riskshare=0p25__s=0p4__cap=0p0005 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p45__riskshare=0p25__s=0p4__cap=0p0008 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p45__riskshare=0p25__s=0p4__cap=0p0012 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p65__riskshare=0p25__s=0p4__cap=0p0005 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269891 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p65__riskshare=0p25__s=0p4__cap=0p0008 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269891 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p65__riskshare=0p25__s=0p4__cap=0p0012 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269891 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p45__riskshare=0p45__s=0p25__cap=0p0005 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p45__riskshare=0p45__s=0p25__cap=0p0008 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p45__riskshare=0p45__s=0p25__cap=0p0012 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p65__riskshare=0p45__s=0p25__cap=0p0005 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269891 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p65__riskshare=0p45__s=0p25__cap=0p0008 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269891 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p65__riskshare=0p45__s=0p25__cap=0p0012 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269891 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p25__riskshare=0p25__s=0p55__cap=0p0005 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p25__riskshare=0p25__s=0p55__cap=0p0008 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p25__riskshare=0p25__s=0p55__cap=0p0012 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p45__riskshare=0p25__s=0p55__cap=0p0005 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269891 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p45__riskshare=0p25__s=0p55__cap=0p0008 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269891 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p45__riskshare=0p25__s=0p55__cap=0p0012 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269891 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p65__riskshare=0p25__s=0p55__cap=0p0005 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p65__riskshare=0p25__s=0p55__cap=0p0008 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p65__riskshare=0p25__s=0p55__cap=0p0012 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p25__riskshare=0p65__s=0p25__cap=0p0005 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p25__riskshare=0p65__s=0p25__cap=0p0008 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p25__riskshare=0p65__s=0p25__cap=0p0012 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p45__riskshare=0p65__s=0p25__cap=0p0005 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269891 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p45__riskshare=0p65__s=0p25__cap=0p0008 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269891 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p45__riskshare=0p65__s=0p25__cap=0p0012 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269891 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p25__riskshare=0p45__s=0p4__cap=0p0005 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p25__riskshare=0p45__s=0p4__cap=0p0008 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p25__riskshare=0p45__s=0p4__cap=0p0012 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p65__riskshare=0p65__s=0p25__cap=0p0005 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p65__riskshare=0p65__s=0p25__cap=0p0008 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p65__riskshare=0p65__s=0p25__cap=0p0012 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p45__riskshare=0p45__s=0p4__cap=0p0005 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p45__riskshare=0p45__s=0p4__cap=0p0008 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p45__riskshare=0p45__s=0p4__cap=0p0012 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p65__riskshare=0p45__s=0p4__cap=0p0005 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p65__riskshare=0p45__s=0p4__cap=0p0008 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p65__riskshare=0p45__s=0p4__cap=0p0012 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p25__riskshare=0p45__s=0p55__cap=0p0005 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p25__riskshare=0p45__s=0p55__cap=0p0008 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p25__riskshare=0p45__s=0p55__cap=0p0012 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p25__riskshare=0p65__s=0p4__cap=0p0005 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p25__riskshare=0p65__s=0p4__cap=0p0008 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p25__riskshare=0p65__s=0p4__cap=0p0012 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p45__riskshare=0p45__s=0p55__cap=0p0005 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p45__riskshare=0p45__s=0p55__cap=0p0008 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p45__riskshare=0p45__s=0p55__cap=0p0012 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p45__riskshare=0p65__s=0p4__cap=0p0005 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p45__riskshare=0p65__s=0p4__cap=0p0008 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p45__riskshare=0p65__s=0p4__cap=0p0012 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p65__riskshare=0p45__s=0p55__cap=0p0005 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p65__riskshare=0p45__s=0p55__cap=0p0008 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p65__riskshare=0p45__s=0p55__cap=0p0012 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt215_p95_aware_rebuild__thr=0p02__p95thr=m0p0001__s=1p16__basecap=0p005__shrink=0p9 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt215_p95_aware_rebuild__thr=0p02__p95thr=m2em05__s=1p16__basecap=0p005__shrink=0p9 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt215_p95_aware_rebuild__thr=0p02__p95thr=m6em05__s=1p16__basecap=0p005__shrink=0p9 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt215_p95_aware_rebuild__thr=0p04__p95thr=m0p0001__s=1p16__basecap=0p005__shrink=0p9 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt215_p95_aware_rebuild__thr=0p04__p95thr=m2em05__s=1p16__basecap=0p005__shrink=0p9 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt215_p95_aware_rebuild__thr=0p04__p95thr=m6em05__s=1p16__basecap=0p005__shrink=0p9 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt215_p95_aware_rebuild__thr=0p08__p95thr=m0p0001__s=1p16__basecap=0p005__shrink=0p9 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt215_p95_aware_rebuild__thr=0p08__p95thr=m2em05__s=1p16__basecap=0p005__shrink=0p9 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt215_p95_aware_rebuild__thr=0p08__p95thr=m6em05__s=1p16__basecap=0p005__shrink=0p9 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt215_p95_aware_rebuild__thr=0p12__p95thr=m0p0001__s=1p16__basecap=0p005__shrink=0p9 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt215_p95_aware_rebuild__thr=0p12__p95thr=m2em05__s=1p16__basecap=0p005__shrink=0p9 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt215_p95_aware_rebuild__thr=0p12__p95thr=m6em05__s=1p16__basecap=0p005__shrink=0p9 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p65__riskshare=0p65__s=0p4__cap=0p0005 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p65__riskshare=0p65__s=0p4__cap=0p0008 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p65__riskshare=0p65__s=0p4__cap=0p0012 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p25__riskshare=0p65__s=0p55__cap=0p0005 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p25__riskshare=0p65__s=0p55__cap=0p0008 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p25__riskshare=0p65__s=0p55__cap=0p0012 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p45__riskshare=0p65__s=0p55__cap=0p0005 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p45__riskshare=0p65__s=0p55__cap=0p0008 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p45__riskshare=0p65__s=0p55__cap=0p0012 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p65__riskshare=0p65__s=0p55__cap=0p0005 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001502 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p65__riskshare=0p65__s=0p55__cap=0p0008 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001502 | -0.000804 | -0.001384 |
| ppopt214_mixed_fallback__pp192share=0p65__riskshare=0p65__s=0p55__cap=0p0012 | PP-OPT214 | pp210_mixed_fallback_recovery | 0.269892 | 0.807326 | -0.001502 | -0.000804 | -0.001384 |
| ppopt212_row_risk_recovery__riskthr=0p45__segshare=0p65__s=0p7__cap=0p0005 | PP-OPT212 | pp210_row_risk_p95_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt212_row_risk_recovery__riskthr=0p45__segshare=0p65__s=0p7__cap=0p0008 | PP-OPT212 | pp210_row_risk_p95_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt212_row_risk_recovery__riskthr=0p45__segshare=0p65__s=0p7__cap=0p0012 | PP-OPT212 | pp210_row_risk_p95_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt212_row_risk_recovery__riskthr=0p45__segshare=0p65__s=0p7__cap=0p0018 | PP-OPT212 | pp210_row_risk_p95_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt213_tail_only_fallback__to=pp204__riskthr=0p55__gapshare=0p25__s=0p4__cap=0p0004 | PP-OPT213 | pp210_tail_only_fallback | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001383 |
| ppopt213_tail_only_fallback__to=pp204__riskthr=0p55__gapshare=0p25__s=0p4__cap=0p0007 | PP-OPT213 | pp210_tail_only_fallback | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001383 |
| ppopt213_tail_only_fallback__to=pp204__riskthr=0p55__gapshare=0p25__s=0p4__cap=0p001 | PP-OPT213 | pp210_tail_only_fallback | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001383 |
| ppopt212_row_risk_recovery__riskthr=0p45__segshare=0p45__s=0p5__cap=0p0005 | PP-OPT212 | pp210_row_risk_p95_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001383 |
| ppopt212_row_risk_recovery__riskthr=0p45__segshare=0p45__s=0p5__cap=0p0008 | PP-OPT212 | pp210_row_risk_p95_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001383 |
| ppopt212_row_risk_recovery__riskthr=0p45__segshare=0p45__s=0p5__cap=0p0012 | PP-OPT212 | pp210_row_risk_p95_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001383 |
| ppopt212_row_risk_recovery__riskthr=0p45__segshare=0p45__s=0p5__cap=0p0018 | PP-OPT212 | pp210_row_risk_p95_recovery | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001383 |
| ppopt213_tail_only_fallback__to=pp204__riskthr=0p55__gapshare=0p65__s=0p28__cap=0p0004 | PP-OPT213 | pp210_tail_only_fallback | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001383 |
| ppopt213_tail_only_fallback__to=pp204__riskthr=0p55__gapshare=0p65__s=0p28__cap=0p0007 | PP-OPT213 | pp210_tail_only_fallback | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001383 |
| ppopt213_tail_only_fallback__to=pp204__riskthr=0p55__gapshare=0p65__s=0p28__cap=0p001 | PP-OPT213 | pp210_tail_only_fallback | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001383 |
| ppopt215_p95_aware_rebuild__thr=0p02__p95thr=m0p0001__s=1p16__basecap=0p0055__shrink=1p05 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269892 | 0.807326 | -0.001502 | -0.000804 | -0.001383 |
| ppopt215_p95_aware_rebuild__thr=0p02__p95thr=m2em05__s=1p16__basecap=0p0055__shrink=1p05 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269892 | 0.807326 | -0.001502 | -0.000804 | -0.001383 |
| ppopt215_p95_aware_rebuild__thr=0p02__p95thr=m6em05__s=1p16__basecap=0p0055__shrink=1p05 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269892 | 0.807326 | -0.001502 | -0.000804 | -0.001383 |
| ppopt215_p95_aware_rebuild__thr=0p04__p95thr=m0p0001__s=1p16__basecap=0p0055__shrink=1p05 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269892 | 0.807326 | -0.001502 | -0.000804 | -0.001383 |
| ppopt215_p95_aware_rebuild__thr=0p04__p95thr=m2em05__s=1p16__basecap=0p0055__shrink=1p05 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269892 | 0.807326 | -0.001502 | -0.000804 | -0.001383 |
| ppopt215_p95_aware_rebuild__thr=0p04__p95thr=m6em05__s=1p16__basecap=0p0055__shrink=1p05 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269892 | 0.807326 | -0.001502 | -0.000804 | -0.001383 |
| ppopt215_p95_aware_rebuild__thr=0p08__p95thr=m0p0001__s=1p16__basecap=0p0055__shrink=1p05 | PP-OPT215 | pp210_p95_aware_rebuild | 0.269892 | 0.807326 | -0.001502 | -0.000804 | -0.001383 |

## 선택 후보 반복 안정성
| candidate_label | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_vs_pp64_MAPE | fixed_test_delta_vs_pp64_p95_APE | avg_pp64_MAPE_win_rate | avg_pp64_p95_win_rate | replacement_score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p08__s_0p25__cap_0p0005__a4aa293138 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p08__s_0p25__cap_0p0008__ab7fa9a0ef | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p08__s_0p25__cap_0p0012__68e8f0c160 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p08__s_0p25__cap_0p0018__d58469f5dc | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p08__s_0p4__cap_0p0005__b9aaed9125 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p08__s_0p4__cap_0p0008__907f402d2b | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p08__s_0p4__cap_0p0012__c9ea05b31e | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p08__s_0p4__cap_0p0018__49765bd50b | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p08__s_0p55__cap_0p0005__3c42415347 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p08__s_0p55__cap_0p0008__35759d5e27 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p08__s_0p55__cap_0p0012__c7829aa570 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p08__s_0p55__cap_0p0018__9abcebc76e | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p08__s_0p75__cap_0p0005__d39b599e4e | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p08__s_0p75__cap_0p0008__c63aca9293 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p08__s_0p75__cap_0p0012__7a408d7bf9 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p08__s_0p75__cap_0p0018__df2b690028 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p0__s_0p25__cap_0p0005__7ed7ce174a | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p0__s_0p25__cap_0p0008__428f02b1ed | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p0__s_0p25__cap_0p0012__2b2908d542 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p0__s_0p25__cap_0p0018__7280e6ff4b | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p0__s_0p4__cap_0p0005__95420f0c9f | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p0__s_0p4__cap_0p0008__b035a31025 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p0__s_0p4__cap_0p0012__6da984a9da | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p0__s_0p4__cap_0p0018__6e7ccf047f | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p0__s_0p55__cap_0p0005__11900909ca | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p0__s_0p55__cap_0p0008__325074e3f6 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p0__s_0p55__cap_0p0012__b875e48153 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p0__s_0p55__cap_0p0018__28460dabc7 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p0__s_0p75__cap_0p0005__04572bf6fc | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p0__s_0p75__cap_0p0008__b1441a4b0c | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p0__s_0p75__cap_0p0012__0e2e926e8c | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p0__s_0p75__cap_0p0018__73e381c8af | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p16__s_0p25__cap_0p0005__4ad11e8928 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p16__s_0p25__cap_0p0008__cf2e1eac9d | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p16__s_0p25__cap_0p0012__a8c2616ff2 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p16__s_0p25__cap_0p0018__9291473b61 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p16__s_0p4__cap_0p0005__02fb4fc57c | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p16__s_0p4__cap_0p0008__0bd2fc0a4b | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p16__s_0p4__cap_0p0012__7e9e5cc9e5 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p16__s_0p4__cap_0p0018__7e49a5fddf | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p16__s_0p55__cap_0p0005__b5e01e074b | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p16__s_0p55__cap_0p0008__4144c96bfd | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p16__s_0p55__cap_0p0012__084d808163 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p16__s_0p55__cap_0p0018__afe45647b8 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p16__s_0p75__cap_0p0005__e8d5686a52 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p16__s_0p75__cap_0p0008__876dcc6548 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p16__s_0p75__cap_0p0012__9e7c07f019 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p16__s_0p75__cap_0p0018__6438a60c0a | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_m0p1__s_0p25__cap_0p0005__ec2520c052 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_m0p1__s_0p25__cap_0p0008__3197a191ed | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_m0p1__s_0p25__cap_0p0012__8ce22984ee | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_m0p1__s_0p25__cap_0p0018__31d5776a83 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_m0p1__s_0p4__cap_0p0005__18704bfa12 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_m0p1__s_0p4__cap_0p0008__b6c75c4844 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_m0p1__s_0p4__cap_0p0012__7af299342f | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_m0p1__s_0p4__cap_0p0018__389fb2a48a | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_m0p1__s_0p55__cap_0p0005__dd60c69f33 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_m0p1__s_0p55__cap_0p0008__9d9f862e7e | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_m0p1__s_0p55__cap_0p0012__77d22133a2 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_m0p1__s_0p55__cap_0p0018__a6b1676969 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_m0p1__s_0p75__cap_0p0005__d4b548f322 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_m0p1__s_0p75__cap_0p0008__6699984a66 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_m0p1__s_0p75__cap_0p0012__613ff3757e | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf__thr_m0p1__s_0p75__cap_0p0018__eb65eb79bf | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p08__s_0p25__cap_0p0005__a038db1c91 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p08__s_0p25__cap_0p0008__2afeee2ff2 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p08__s_0p25__cap_0p0012__654589b19c | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p08__s_0p25__cap_0p0018__4f07ae4eb1 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p08__s_0p4__cap_0p0005__89f5be7723 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p08__s_0p4__cap_0p0008__9fcbee4b4a | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p08__s_0p4__cap_0p0012__1ba55882e2 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p08__s_0p4__cap_0p0018__fcee23579c | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p08__s_0p55__cap_0p0005__66523ec12a | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p08__s_0p55__cap_0p0008__17d0bd65ba | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p08__s_0p55__cap_0p0012__282f36b28c | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p08__s_0p55__cap_0p0018__0da4829a1d | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p08__s_0p75__cap_0p0005__ff215e27a4 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p08__s_0p75__cap_0p0008__c341d82c66 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p08__s_0p75__cap_0p0012__52aec37021 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p08__s_0p75__cap_0p0018__6210859106 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p0__s_0p25__cap_0p0005__36b7629f53 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p0__s_0p25__cap_0p0008__cfbf6378bf | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p0__s_0p25__cap_0p0012__008d5c6362 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p0__s_0p25__cap_0p0018__51696cea7a | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p0__s_0p4__cap_0p0005__f439aca644 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p0__s_0p4__cap_0p0008__78370d1e9d | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p0__s_0p4__cap_0p0012__1cb45a40ab | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p0__s_0p4__cap_0p0018__fc3b5810de | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p0__s_0p55__cap_0p0005__1855798110 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p0__s_0p55__cap_0p0008__fac2e4adb4 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p0__s_0p55__cap_0p0012__f6c28eab6f | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p0__s_0p55__cap_0p0018__e5899f6c62 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p0__s_0p75__cap_0p0005__d5e1b95b37 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p0__s_0p75__cap_0p0008__b2113079dd | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p0__s_0p75__cap_0p0012__07136b37d7 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p0__s_0p75__cap_0p0018__09efacd84a | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p16__s_0p25__cap_0p0005__3a48afe5cd | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p16__s_0p25__cap_0p0008__5b077f0396 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p16__s_0p25__cap_0p0012__0e34266486 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p16__s_0p25__cap_0p0018__38485c323e | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p16__s_0p4__cap_0p0005__52c351cd4c | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p16__s_0p4__cap_0p0008__f302b128cd | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p16__s_0p4__cap_0p0012__c12cc24f20 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p16__s_0p4__cap_0p0018__dfebe7edae | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p16__s_0p55__cap_0p0005__6814dda649 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p16__s_0p55__cap_0p0008__3ee7e22036 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p16__s_0p55__cap_0p0012__fa68ec6751 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p16__s_0p55__cap_0p0018__771f0c3ba9 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt211_segment_recovery__seg_price_conf_gap__thr_0p16__s_0p75__cap_0p0005__7c5db3fdaf | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| pp210_operational_reference | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| pp216_operational_pp210_p95_recovery_challenger | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt214_mixed_fallback__pp192share_0p65__riskshare_0p25__s_0p25__cap_0p0005__af5ee70468 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt214_mixed_fallback__pp192share_0p65__riskshare_0p25__s_0p25__cap_0p0008__62e2f2560d | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt214_mixed_fallback__pp192share_0p65__riskshare_0p25__s_0p25__cap_0p0012__fe2b5d8e2b | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt214_mixed_fallback__pp192share_0p25__riskshare_0p25__s_0p55__cap_0p0005__f49da30cb8 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt214_mixed_fallback__pp192share_0p25__riskshare_0p25__s_0p55__cap_0p0008__13ee978314 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt214_mixed_fallback__pp192share_0p25__riskshare_0p25__s_0p55__cap_0p0012__794eafab66 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt214_mixed_fallback__pp192share_0p45__riskshare_0p25__s_0p4__cap_0p0005__f67700e940 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt214_mixed_fallback__pp192share_0p45__riskshare_0p25__s_0p4__cap_0p0008__bb98dc21d0 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt214_mixed_fallback__pp192share_0p45__riskshare_0p25__s_0p4__cap_0p0012__65bcc3de5a | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt214_mixed_fallback__pp192share_0p25__riskshare_0p65__s_0p25__cap_0p0005__2ee77bc417 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt214_mixed_fallback__pp192share_0p25__riskshare_0p65__s_0p25__cap_0p0008__74a4b06678 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt214_mixed_fallback__pp192share_0p25__riskshare_0p65__s_0p25__cap_0p0012__747f22431c | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt214_mixed_fallback__pp192share_0p45__riskshare_0p45__s_0p25__cap_0p0005__df8a2e3652 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt214_mixed_fallback__pp192share_0p45__riskshare_0p45__s_0p25__cap_0p0008__24a4267d97 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt214_mixed_fallback__pp192share_0p45__riskshare_0p45__s_0p25__cap_0p0012__38c8722c8d | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt215_p95_aware_rebuild__thr_0p02__p95thr_m0p0001__s_1p16__basecap_0p005__shrink_0p9__06eb4a43a0 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt215_p95_aware_rebuild__thr_0p02__p95thr_m2em05__s_1p16__basecap_0p005__shrink_0p9__ceb1d2d640 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt215_p95_aware_rebuild__thr_0p02__p95thr_m6em05__s_1p16__basecap_0p005__shrink_0p9__000631c17e | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt215_p95_aware_rebuild__thr_0p04__p95thr_m0p0001__s_1p16__basecap_0p005__shrink_0p9__13f83b5c9a | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt215_p95_aware_rebuild__thr_0p04__p95thr_m2em05__s_1p16__basecap_0p005__shrink_0p9__c778a92c65 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt215_p95_aware_rebuild__thr_0p04__p95thr_m6em05__s_1p16__basecap_0p005__shrink_0p9__868f152c25 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt215_p95_aware_rebuild__thr_0p08__p95thr_m0p0001__s_1p16__basecap_0p005__shrink_0p9__cea4b21f5b | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt215_p95_aware_rebuild__thr_0p08__p95thr_m2em05__s_1p16__basecap_0p005__shrink_0p9__39b1839e42 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt215_p95_aware_rebuild__thr_0p08__p95thr_m6em05__s_1p16__basecap_0p005__shrink_0p9__8fb308268c | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt215_p95_aware_rebuild__thr_0p12__p95thr_m0p0001__s_1p16__basecap_0p005__shrink_0p9__3b03e5dcf4 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt215_p95_aware_rebuild__thr_0p12__p95thr_m2em05__s_1p16__basecap_0p005__shrink_0p9__1f976d8f35 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt215_p95_aware_rebuild__thr_0p12__p95thr_m6em05__s_1p16__basecap_0p005__shrink_0p9__cb0434b3a8 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018827 |
| candidate_ppopt214_mixed_fallback__pp192share_0p25__riskshare_0p45__s_0p4__cap_0p0005__d44c45b1f9 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt214_mixed_fallback__pp192share_0p25__riskshare_0p45__s_0p4__cap_0p0008__d413c5655a | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt214_mixed_fallback__pp192share_0p25__riskshare_0p45__s_0p4__cap_0p0012__6609e8754f | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt214_mixed_fallback__pp192share_0p65__riskshare_0p25__s_0p4__cap_0p0005__6573950b11 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p65__riskshare_0p25__s_0p4__cap_0p0008__c1fd74fc13 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p65__riskshare_0p25__s_0p4__cap_0p0012__5cc4835cbf | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p45__riskshare_0p25__s_0p55__cap_0p0005__a7b9152e59 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p45__riskshare_0p25__s_0p55__cap_0p0008__94d78682fc | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p45__riskshare_0p25__s_0p55__cap_0p0012__8ece17b52d | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p65__riskshare_0p45__s_0p25__cap_0p0005__37805bda57 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p65__riskshare_0p45__s_0p25__cap_0p0008__8ca09cb964 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p65__riskshare_0p45__s_0p25__cap_0p0012__adcfa0972b | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p45__riskshare_0p65__s_0p25__cap_0p0005__ff51b9f82d | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p45__riskshare_0p65__s_0p25__cap_0p0008__7db73f243b | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p45__riskshare_0p65__s_0p25__cap_0p0012__bfef6d3064 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p25__riskshare_0p45__s_0p55__cap_0p0005__6912ca1b3c | 0.269892 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p25__riskshare_0p45__s_0p55__cap_0p0008__cd69f2585e | 0.269892 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p25__riskshare_0p45__s_0p55__cap_0p0012__e49e2205f4 | 0.269892 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p25__riskshare_0p65__s_0p4__cap_0p0005__e7eacfd4f2 | 0.269892 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p25__riskshare_0p65__s_0p4__cap_0p0008__849e6b2e8d | 0.269892 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p25__riskshare_0p65__s_0p4__cap_0p0012__94971422d5 | 0.269892 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p45__riskshare_0p45__s_0p4__cap_0p0005__ded5ddee6a | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p45__riskshare_0p45__s_0p4__cap_0p0008__bf253ed8b0 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p45__riskshare_0p45__s_0p4__cap_0p0012__88dfda53bc | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p65__riskshare_0p25__s_0p55__cap_0p0005__66d84f258a | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p65__riskshare_0p25__s_0p55__cap_0p0008__f8612f1836 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p65__riskshare_0p25__s_0p55__cap_0p0012__307eba8121 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p65__riskshare_0p65__s_0p25__cap_0p0005__49c291e48d | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p65__riskshare_0p65__s_0p25__cap_0p0008__37054509f3 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p65__riskshare_0p65__s_0p25__cap_0p0012__f7c69855bd | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p65__riskshare_0p45__s_0p4__cap_0p0005__429b84d100 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p65__riskshare_0p45__s_0p4__cap_0p0008__b548a4a5c5 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p65__riskshare_0p45__s_0p4__cap_0p0012__ea2f89318e | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p25__riskshare_0p65__s_0p55__cap_0p0005__49fdff1427 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p45__riskshare_0p45__s_0p55__cap_0p0005__eb414e2dd3 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p45__riskshare_0p45__s_0p55__cap_0p0008__e5fd6a6af8 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p45__riskshare_0p45__s_0p55__cap_0p0012__cf252606a7 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p45__riskshare_0p65__s_0p4__cap_0p0005__60b218ab0b | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p45__riskshare_0p65__s_0p4__cap_0p0008__cda6aabdf8 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p45__riskshare_0p65__s_0p4__cap_0p0012__4398f33e88 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p65__riskshare_0p45__s_0p55__cap_0p0005__7cff855f04 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt214_mixed_fallback__pp192share_0p65__riskshare_0p45__s_0p55__cap_0p0008__0ec19eb657 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |

## 실행 설정
```json
{
  "experiment_id": "PP-OPT211-216",
  "experiment_slug": "PP-OPT211_216_warm_pp210_p95_win_recovery_router",
  "created_at": "2026-06-10T11:12:30",
  "base_candidate": "hcoef_stable",
  "previous_experiment": "experiments/track6/PP-OPT205_210_warm_pp204_local_winner_router_refinement",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 1029,
  "prediction_rows": 1158654,
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
    "pp210_p95_extreme": "ppopt210_p95_extreme_pp204_local_refinement__source=reference_pp148_p95"
  },
  "selection_decision": {
    "operational_label": "candidate_ppopt211_segment_recovery__seg_price_conf__thr_0p08__s_0p25__cap_0p0005__a4aa293138",
    "operational_candidate": "ppopt211_segment_recovery__seg=price_conf__thr=0p08__s=0p25__cap=0p0005",
    "operational_fixed_test_MAPE": 0.2698910008301743,
    "operational_fixed_test_p95_APE": 0.8073255046591389,
    "operational_delta_vs_pp64_MAPE": -0.000673041085486048,
    "operational_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "operational_delta_vs_pp126_MAPE": -0.00022339591967751593,
    "operational_delta_vs_pp126_p95_APE": -0.0001645562387090349,
    "operational_delta_vs_pp148_MAPE": -0.0002489875424050991,
    "operational_delta_vs_pp148_p95_APE": 9.45931204405781e-05,
    "operational_delta_vs_pp166_MAPE": -0.0001059848350642989,
    "operational_delta_vs_pp166_p95_APE": 9.45931204405781e-05,
    "operational_delta_vs_pp172_MAPE": -0.00010641383097625967,
    "operational_delta_vs_pp172_p95_APE": 9.45931204405781e-05,
    "operational_delta_vs_pp186_MAPE": -6.963303605228566e-05,
    "operational_delta_vs_pp186_p95_APE": 9.45931204405781e-05,
    "operational_delta_vs_pp192_MAPE": -2.335331457548051e-05,
    "operational_delta_vs_pp192_p95_APE": 0.0,
    "operational_delta_vs_pp198_MAPE": -3.0081880458276977e-06,
    "operational_delta_vs_pp198_p95_APE": 0.0,
    "operational_delta_vs_pp204_MAPE": -2.520440992026529e-06,
    "operational_delta_vs_pp204_p95_APE": 0.0,
    "operational_delta_vs_pp210_MAPE": 0.0,
    "operational_delta_vs_pp210_p95_APE": 0.0,
    "operational_delta_vs_pp204_p95_win_rate": -0.0006410256410256387,
    "operational_delta_vs_pp210_p95_win_rate": 0.0,
    "operational_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "operational_avg_pp64_p95_win_rate": 0.7471153846153845,
    "operational_replacement_score": -0.018826887239332204,
    "p95_recovery_label": "candidate_ppopt215_p95_aware_rebuild__thr_0p02__p95thr_m0p0001__s_1p16__basecap_0p005__shrink_1p2__fa1c81b71a",
    "p95_recovery_candidate": "ppopt215_p95_aware_rebuild__thr=0p02__p95thr=m0p0001__s=1p16__basecap=0p005__shrink=1p2",
    "p95_recovery_fixed_test_MAPE": 0.2698976418819697,
    "p95_recovery_fixed_test_p95_APE": 0.8073255046591389,
    "p95_recovery_delta_vs_pp64_MAPE": -0.0006664000336906728,
    "p95_recovery_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "p95_recovery_delta_vs_pp126_MAPE": -0.0002167548678821407,
    "p95_recovery_delta_vs_pp126_p95_APE": -0.0001645562387090349,
    "p95_recovery_delta_vs_pp148_MAPE": -0.0002423464906097239,
    "p95_recovery_delta_vs_pp148_p95_APE": 9.45931204405781e-05,
    "p95_recovery_delta_vs_pp166_MAPE": -9.934378326892368e-05,
    "p95_recovery_delta_vs_pp166_p95_APE": 9.45931204405781e-05,
    "p95_recovery_delta_vs_pp172_MAPE": -9.977277918088445e-05,
    "p95_recovery_delta_vs_pp172_p95_APE": 9.45931204405781e-05,
    "p95_recovery_delta_vs_pp186_MAPE": -6.299198425691044e-05,
    "p95_recovery_delta_vs_pp186_p95_APE": 9.45931204405781e-05,
    "p95_recovery_delta_vs_pp192_MAPE": -1.671226278010529e-05,
    "p95_recovery_delta_vs_pp192_p95_APE": 0.0,
    "p95_recovery_delta_vs_pp198_MAPE": 3.6328637495475213e-06,
    "p95_recovery_delta_vs_pp198_p95_APE": 0.0,
    "p95_recovery_delta_vs_pp204_MAPE": 4.12061080334869e-06,
    "p95_recovery_delta_vs_pp204_p95_APE": 0.0,
    "p95_recovery_delta_vs_pp210_MAPE": 6.641051795375219e-06,
    "p95_recovery_delta_vs_pp210_p95_APE": 0.0,
    "p95_recovery_delta_vs_pp204_p95_win_rate": 0.0019230769230769162,
    "p95_recovery_delta_vs_pp210_p95_win_rate": 0.002564102564102555,
    "p95_recovery_avg_pp64_MAPE_win_rate": 0.9528846153846153,
    "p95_recovery_avg_pp64_p95_win_rate": 0.7496794871794871,
    "p95_recovery_replacement_score": -0.018781784649075286,
    "mape_challenger_label": "pp210_mape_reference",
    "mape_challenger_candidate": "ppopt210_mape_challenger_pp204_local_refinement__source=ppopt205_local_price_conf__thr_0p04__width_0p22__s_1p16__basecap_0p0065__shrink_0p65",
    "mape_challenger_fixed_test_MAPE": 0.2698902927490762,
    "mape_challenger_fixed_test_p95_APE": 0.8073255046591389,
    "mape_challenger_delta_vs_pp64_MAPE": -0.0006737491665841366,
    "mape_challenger_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "mape_challenger_delta_vs_pp126_MAPE": -0.00022410400077560455,
    "mape_challenger_delta_vs_pp126_p95_APE": -0.0001645562387090349,
    "mape_challenger_delta_vs_pp148_MAPE": -0.00024969562350318775,
    "mape_challenger_delta_vs_pp148_p95_APE": 9.45931204405781e-05,
    "mape_challenger_delta_vs_pp166_MAPE": -0.00010669291616238752,
    "mape_challenger_delta_vs_pp166_p95_APE": 9.45931204405781e-05,
    "mape_challenger_delta_vs_pp172_MAPE": -0.00010712191207434829,
    "mape_challenger_delta_vs_pp172_p95_APE": 9.45931204405781e-05,
    "mape_challenger_delta_vs_pp186_MAPE": -7.034111715037428e-05,
    "mape_challenger_delta_vs_pp186_p95_APE": 9.45931204405781e-05,
    "mape_challenger_delta_vs_pp192_MAPE": -2.406139567356913e-05,
    "mape_challenger_delta_vs_pp192_p95_APE": 0.0,
    "mape_challenger_delta_vs_pp198_MAPE": -3.7162691439163176e-06,
    "mape_challenger_delta_vs_pp198_p95_APE": 0.0,
    "mape_challenger_delta_vs_pp204_MAPE": -3.228522090115149e-06,
    "mape_challenger_delta_vs_pp204_p95_APE": 0.0,
    "mape_challenger_delta_vs_pp210_MAPE": -7.080810980886199e-07,
    "mape_challenger_delta_vs_pp210_p95_APE": 0.0,
    "mape_challenger_delta_vs_pp204_p95_win_rate": -0.0006410256410256387,
    "mape_challenger_delta_vs_pp210_p95_win_rate": 0.0,
    "mape_challenger_avg_pp64_MAPE_win_rate": 0.9528846153846153,
    "mape_challenger_avg_pp64_p95_win_rate": 0.7471153846153845,
    "mape_challenger_replacement_score": -0.01878913378196875,
    "p95_guarded_label": "pp210_p95_guarded_reference",
    "p95_guarded_candidate": "ppopt210_p95_guarded_pp204_local_refinement__source=ppopt204_p95_guarded_pp192_pp198_winner_router__source_ppopt192_p95_guarded_pp180_pp186_risk_router__source_ppopt187_har",
    "p95_guarded_fixed_test_MAPE": 0.26994920114208765,
    "p95_guarded_fixed_test_p95_APE": 0.8072545738314347,
    "p95_guarded_delta_vs_pp64_MAPE": -0.0006148407735727113,
    "p95_guarded_delta_vs_pp64_p95_APE": -0.0002442784746751192,
    "p95_guarded_delta_vs_pp126_MAPE": -0.0001651956077641792,
    "p95_guarded_delta_vs_pp126_p95_APE": -0.00023548706641318695,
    "p95_guarded_delta_vs_pp148_MAPE": -0.00019078723049176238,
    "p95_guarded_delta_vs_pp148_p95_APE": 2.366229273642606e-05,
    "p95_guarded_delta_vs_pp166_MAPE": -4.7784523150962155e-05,
    "p95_guarded_delta_vs_pp166_p95_APE": 2.366229273642606e-05,
    "p95_guarded_delta_vs_pp172_MAPE": -4.821351906292293e-05,
    "p95_guarded_delta_vs_pp172_p95_APE": 2.366229273642606e-05,
    "p95_guarded_delta_vs_pp186_MAPE": -1.1432724138948913e-05,
    "p95_guarded_delta_vs_pp186_p95_APE": 2.366229273642606e-05,
    "p95_guarded_delta_vs_pp192_MAPE": 3.4846997337856234e-05,
    "p95_guarded_delta_vs_pp192_p95_APE": -7.093082770415204e-05,
    "p95_guarded_delta_vs_pp198_MAPE": 5.5192123867509046e-05,
    "p95_guarded_delta_vs_pp198_p95_APE": -7.093082770415204e-05,
    "p95_guarded_delta_vs_pp204_MAPE": 5.5679870921310215e-05,
    "p95_guarded_delta_vs_pp204_p95_APE": -7.093082770415204e-05,
    "p95_guarded_delta_vs_pp210_MAPE": 5.8200311913336744e-05,
    "p95_guarded_delta_vs_pp210_p95_APE": -7.093082770415204e-05,
    "p95_guarded_delta_vs_pp204_p95_win_rate": 0.0038461538461540545,
    "p95_guarded_delta_vs_pp210_p95_win_rate": 0.004487179487179693,
    "p95_guarded_avg_pp64_MAPE_win_rate": 0.9509615384615384,
    "p95_guarded_avg_pp64_p95_win_rate": 0.7516025641025642,
    "p95_guarded_replacement_score": -0.01865330231203425,
    "p95_extreme_label": "pp148_p95_reference",
    "p95_extreme_candidate": "reference_pp148_p95",
    "p95_extreme_fixed_test_MAPE": 0.27026892590910795,
    "p95_extreme_fixed_test_p95_APE": 0.8059493758221674,
    "p95_extreme_delta_vs_pp64_MAPE": -0.00029511600655240944,
    "p95_extreme_delta_vs_pp64_p95_APE": -0.0015494764839424358,
    "p95_extreme_delta_vs_pp126_MAPE": 0.00015452915925612265,
    "p95_extreme_delta_vs_pp126_p95_APE": -0.0015406850756805035,
    "p95_extreme_delta_vs_pp148_MAPE": 0.00012893753652853945,
    "p95_extreme_delta_vs_pp148_p95_APE": -0.0012815357165308905,
    "p95_extreme_delta_vs_pp166_MAPE": 0.0002719402438693397,
    "p95_extreme_delta_vs_pp166_p95_APE": -0.0012815357165308905,
    "p95_extreme_delta_vs_pp172_MAPE": 0.0002715112479573789,
    "p95_extreme_delta_vs_pp172_p95_APE": -0.0012815357165308905,
    "p95_extreme_delta_vs_pp186_MAPE": 0.0003082920428813529,
    "p95_extreme_delta_vs_pp186_p95_APE": -0.0012815357165308905,
    "p95_extreme_delta_vs_pp192_MAPE": 0.00035457176435815807,
    "p95_extreme_delta_vs_pp192_p95_APE": -0.0013761288369714686,
    "p95_extreme_delta_vs_pp198_MAPE": 0.0003749168908878109,
    "p95_extreme_delta_vs_pp198_p95_APE": -0.0013761288369714686,
    "p95_extreme_delta_vs_pp204_MAPE": 0.00037540463794161205,
    "p95_extreme_delta_vs_pp204_p95_APE": -0.0013761288369714686,
    "p95_extreme_delta_vs_pp210_MAPE": 0.0003779250789336386,
    "p95_extreme_delta_vs_pp210_p95_APE": -0.0013761288369714686,
    "p95_extreme_delta_vs_pp204_p95_win_rate": -0.2467948717948717,
    "p95_extreme_delta_vs_pp210_p95_win_rate": -0.24615384615384606,
    "p95_extreme_avg_pp64_MAPE_win_rate": 0.5983974358974359,
    "p95_extreme_avg_pp64_p95_win_rate": 0.5009615384615385,
    "p95_extreme_replacement_score": -0.0040792899192624915,
    "operational_protocol_candidate": "ppopt216_operational_pp210_p95_recovery__source=ppopt211_segment_recovery__seg_price_conf__thr_0p08__s_0p25__cap_0p0005",
    "p95_recovery_protocol_candidate": "ppopt216_p95_recovery_pp210_p95_recovery__source=ppopt215_p95_aware_rebuild__thr_0p02__p95thr_m0p0001__s_1p16__basecap_0p005__shrink_1p2",
    "mape_challenger_protocol_candidate": "ppopt216_mape_challenger_pp210_p95_recovery__source=ppopt210_mape_challenger_pp204_local_refinement__source_ppopt205_local_price_conf__thr_0p04__width_0p22__s_1p16__basecap",
    "p95_guarded_protocol_candidate": "ppopt216_p95_guarded_pp210_p95_recovery__source=ppopt210_p95_guarded_pp204_local_refinement__source_ppopt204_p95_guarded_pp192_pp198_winner_router__source_ppopt192_p95_",
    "p95_extreme_protocol_candidate": "ppopt216_p95_extreme_pp210_p95_recovery__source=reference_pp148_p95"
  },
  "items": [
    {
      "item_id": "PP-OPT211",
      "priority": "1",
      "title": "segment p95 recovery rollback",
      "description": "validation segment에서 PP210이 PP204보다 상단 오차를 키우는 구간만 PP204로 부분 rollback."
    },
    {
      "item_id": "PP-OPT212",
      "priority": "2",
      "title": "row-risk p95 recovery rollback",
      "description": "row 위험도, 예측 gap, p95 harm score를 결합해 위험 row만 PP204로 되돌림."
    },
    {
      "item_id": "PP-OPT213",
      "priority": "3",
      "title": "tail-risk only fallback",
      "description": "quantile 폭, 가격 범위, 모델 spread가 큰 row에만 아주 작은 fallback 이동 적용."
    },
    {
      "item_id": "PP-OPT214",
      "priority": "4",
      "title": "PP204/PP192 mixed fallback",
      "description": "fallback을 PP204 단일이 아니라 PP204와 PP192 사이로 두어 p95 회복과 MAPE 손상을 균형화."
    },
    {
      "item_id": "PP-OPT215",
      "priority": "5",
      "title": "p95-aware PP210 rebuild",
      "description": "PP210의 winner router를 다시 만들되 p95 harm guard와 row cap을 더 보수적으로 적용."
    },
    {
      "item_id": "PP-OPT216",
      "priority": "6",
      "title": "final PP210 p95 recovery decision",
      "description": "PP210, PP204, 신규 recovery 후보를 fixed/repeated 기준으로 비교해 선택."
    }
  ],
  "router_formula": {
    "base": "PP210 operational log price",
    "fallback": "PP204 operational log price, PP192 operational log price, or mixed fallback",
    "recovery_final": "PP210 log price + clip((fallback log price - PP210 log price) * rollback_weight, row_cap)",
    "rebuild_final": "PP192 log price + clip((PP198 log price - PP192 log price) * p95_aware_winner_weight, row_cap)",
    "recovery_inputs": [
      "validation segment PP210-vs-PP204 p95 gain",
      "validation segment PP210-vs-PP204 APE gain",
      "row tail risk",
      "abs(PP210 log price - PP204 log price)",
      "quantile_width",
      "component_prediction_spread"
    ]
  }
}
```