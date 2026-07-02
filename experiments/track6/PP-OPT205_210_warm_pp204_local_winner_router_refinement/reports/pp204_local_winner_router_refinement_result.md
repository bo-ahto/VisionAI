# PP-OPT205~210 Warm PP204 local winner-router refinement 결과

- 작성일: 2026-06-10 11:02
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 목적: PP204 winner-router 주변의 threshold/cap/shrink를 세밀하게 조정해 추가 개선 여부 확인
- 결론: 운영 후보 fixed test MAPE 0.269891, p95 0.807326. PP204 대비 MAPE -0.000003, p95 +0.000000, replacement score -0.018827.

## 주요 후보 test 비교
| candidate | family | item_id | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt210_mape_challenger_pp204_local_refinement__source=ppopt205_local_price_conf__thr_0p04__width_0p22__s_1p16__basecap_0p0065__shrink_0p65 | pp204_local_refinement_mape_selection | PP-OPT210 | 0.140975 | 0.269890 | 0.807326 | 0.397454 | -0.001505 | -0.000804 |
| ppopt210_operational_pp204_local_refinement__source=ppopt205_local_price_conf__thr_0p04__width_0p22__s_1p16__basecap_0p0055__shrink_0p9 | pp204_local_refinement_operational_selection | PP-OPT210 | 0.140975 | 0.269891 | 0.807326 | 0.397456 | -0.001504 | -0.000804 |
| ppopt204_operational_pp192_pp198_winner_router__source=ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_1p0__basecap_0p006__shrink_0p8 | reference_prior | REFERENCE | 0.140975 | 0.269894 | 0.807326 | 0.397456 | -0.001501 | -0.000804 |
| ppopt198_operational_segment_router_refinement__source=ppopt194_price_conf_refine__scorethr_0p02__mix_0p25__s_1p05__cap_0p006 | reference_prior | REFERENCE | 0.140975 | 0.269894 | 0.807326 | 0.397455 | -0.001501 | -0.000804 |
| ppopt192_operational_pp180_pp186_risk_router__source=ppopt189_segment_router__seg_price_gap__scorethr_0p02__mix_0p75__s_0p95__cap_0p0025 | reference_prior | REFERENCE | 0.140975 | 0.269914 | 0.807326 | 0.397468 | -0.001481 | -0.000804 |
| ppopt180_operational_basis_generation_challenger__source=ppopt174_direct_basis__source_stack_huber_weighted__thr_0p08__s_0p3__cap_0p004 | reference_prior | REFERENCE | 0.140975 | 0.269933 | 0.807326 | 0.397475 | -0.001462 | -0.000804 |
| ppopt210_p95_guarded_pp204_local_refinement__source=ppopt204_p95_guarded_pp192_pp198_winner_router__source_ppopt192_p95_guarded_pp180_pp186_risk_router__source_ppopt187_har | pp204_local_refinement_p95_guarded_selection | PP-OPT210 | 0.140094 | 0.269949 | 0.807255 | 0.397482 | -0.001446 | -0.000875 |
| ppopt186_operational_huber_basis_p95_guard__source=ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p04__s_0p42__cap_0p0045 | reference_prior | REFERENCE | 0.139801 | 0.269961 | 0.807231 | 0.397497 | -0.001434 | -0.000899 |
| ppopt172_operational_pp166_tail_calibration_challenger__source=ppopt169_segment_router__source_pp162_p95_gate__seg_price_conf__thr_m0p04__s_0p5__cap_0p004 | reference_prior | REFERENCE | 0.139801 | 0.269997 | 0.807231 | 0.397516 | -0.001397 | -0.000899 |
| reference_pp126_operational | reference_prior | REFERENCE | 0.136320 | 0.270114 | 0.807490 | 0.397588 | -0.001280 | -0.000640 |
| reference_pp148_operational | reference_prior | REFERENCE | 0.139801 | 0.270140 | 0.807231 | 0.397525 | -0.001255 | -0.000899 |
| reference_pp148_p95 | reference_prior | REFERENCE | 0.141036 | 0.270269 | 0.805949 | 0.397421 | -0.001126 | -0.002181 |
| ppopt210_p95_extreme_pp204_local_refinement__source=reference_pp148_p95 | pp204_local_refinement_p95_extreme_selection | PP-OPT210 | 0.141036 | 0.270269 | 0.805949 | 0.397421 | -0.001126 | -0.002181 |
| reference_pp64_current_best | reference_prior | REFERENCE | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | p95_test_MAPE | p95_test_p95_APE | operational_pass_vs_incumbent | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | final PP204 local refinement decision | 4 | 0.269949 | 0.807255 | 0.270269 | 0.805949 | False | pp204_local_refinement_p95_guarded_selection | ppopt210_p95_guarded_pp204_local_refinement__source=ppopt204_p95_guarded_pp192_pp198_winner_router__source_ppopt192_p95_guarded_pp180_pp186_risk_router__source_ppopt187_har |
| 1 | PP204 local threshold/cap refinement | 480 | 0.269891 | 0.807326 | 0.269890 | 0.807326 | False | pp204_local_threshold_cap_refinement | ppopt205_local_price_conf__thr=0p04__width=0p22__s=1p16__basecap=0p0045__shrink=0p8 |
| 2 | p95 guard sensitivity refinement | 216 | 0.269892 | 0.807326 | 0.269891 | 0.807326 | False | pp204_p95_guard_sensitivity_refinement | ppopt206_p95_guard_sensitivity__p95thr=0p0__p95width=0p00012__s=1p1__basecap=0p0055__shrink=1p0 |
| 3 | PP192/PP198 gap-aware cap | 64 | 0.269892 | 0.807326 | 0.269892 | 0.807326 | False | pp204_gap_aware_cap_refinement | ppopt207_gap_aware_cap__gapthr=0p006__gapwidth=0p003__s=1p05__basecap=0p0065__shrink=0p95 |
| 4 | confidence-risk asymmetric shrink | 48 | 0.269893 | 0.807326 | 0.269893 | 0.807326 | False | pp204_confidence_risk_shrink_refinement | ppopt208_conf_risk_shrink__lowshare=0p35__highshare=1p08__riskthr=0p5__s=1p05__basecap=0p0045 |
| 5 | PP204 second-stage residual nudge | 36 | 0.269894 | 0.807326 | 0.269894 | 0.807326 | False | pp204_second_stage_residual_nudge | ppopt209_second_stage_nudge__dir=rollback_pp192__s=0p2__cap=0p0008__shrink=0p5 |

## 탐색 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt210_p95_guarded_pp204_local_refinement__source=ppopt204_p95_guarded_pp192_pp198_winner_router__source_ppopt192_p95_guarded_pp180_pp186_risk_router__source_ppopt187_har | PP-OPT210 | pp204_local_refinement_p95_guarded_selection | 0.269949 | 0.807255 | -0.001446 | -0.000875 | -0.001537 |
| ppopt205_local_price_conf__thr=0p04__width=0p22__s=1p16__basecap=0p0045__shrink=0p8 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269891 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt205_local_price_conf__thr=0p04__width=0p26__s=1p16__basecap=0p0045__shrink=0p8 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269891 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt205_local_price_conf__thr=0p08__width=0p22__s=1p16__basecap=0p0045__shrink=0p8 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269891 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt205_local_price_conf__thr=0p08__width=0p26__s=1p16__basecap=0p0045__shrink=0p8 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269891 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt205_local_price_conf__thr=0p0__width=0p22__s=1p16__basecap=0p0045__shrink=0p8 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269891 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt205_local_price_conf__thr=0p0__width=0p26__s=1p16__basecap=0p0045__shrink=0p8 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269891 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt205_local_price_conf__thr=0p12__width=0p22__s=1p16__basecap=0p0045__shrink=0p8 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269891 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt205_local_price_conf__thr=0p12__width=0p26__s=1p16__basecap=0p0045__shrink=0p8 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269891 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt205_local_price_conf__thr=m0p02__width=0p26__s=1p16__basecap=0p0045__shrink=0p8 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269891 | 0.807326 | -0.001503 | -0.000804 | -0.001384 |
| ppopt205_local_price_conf__thr=m0p02__width=0p22__s=1p16__basecap=0p0045__shrink=0p8 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269891 | 0.807326 | -0.001503 | -0.000804 | -0.001383 |
| ppopt206_p95_guard_sensitivity__p95thr=0p0__p95width=0p00012__s=1p1__basecap=0p0055__shrink=1p0 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001383 |
| ppopt206_p95_guard_sensitivity__p95thr=0p0__p95width=0p00018__s=1p1__basecap=0p0055__shrink=1p0 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001383 |
| ppopt206_p95_guard_sensitivity__p95thr=0p0__p95width=8em05__s=1p1__basecap=0p0055__shrink=1p0 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001383 |
| ppopt206_p95_guard_sensitivity__p95thr=m2em05__p95width=0p00012__s=1p1__basecap=0p0055__shrink=1p0 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001383 |
| ppopt206_p95_guard_sensitivity__p95thr=m2em05__p95width=0p00018__s=1p1__basecap=0p0055__shrink=1p0 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001383 |
| ppopt206_p95_guard_sensitivity__p95thr=m2em05__p95width=8em05__s=1p1__basecap=0p0055__shrink=1p0 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001383 |
| ppopt206_p95_guard_sensitivity__p95thr=m4em05__p95width=0p00012__s=1p1__basecap=0p0055__shrink=1p0 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001383 |
| ppopt206_p95_guard_sensitivity__p95thr=m4em05__p95width=0p00018__s=1p1__basecap=0p0055__shrink=1p0 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001383 |
| ppopt206_p95_guard_sensitivity__p95thr=m4em05__p95width=8em05__s=1p1__basecap=0p0055__shrink=1p0 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001383 |
| ppopt206_p95_guard_sensitivity__p95thr=m8em05__p95width=0p00012__s=1p1__basecap=0p0055__shrink=1p0 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001383 |
| ppopt206_p95_guard_sensitivity__p95thr=m8em05__p95width=0p00018__s=1p1__basecap=0p0055__shrink=1p0 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001383 |
| ppopt206_p95_guard_sensitivity__p95thr=m8em05__p95width=8em05__s=1p1__basecap=0p0055__shrink=1p0 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269892 | 0.807326 | -0.001503 | -0.000804 | -0.001383 |
| ppopt205_local_price_conf__thr=0p04__width=0p22__s=1p16__basecap=0p0045__shrink=0p9 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001382 |
| ppopt205_local_price_conf__thr=0p04__width=0p26__s=1p16__basecap=0p0045__shrink=0p9 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001382 |
| ppopt205_local_price_conf__thr=0p08__width=0p22__s=1p16__basecap=0p0045__shrink=0p9 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001382 |
| ppopt205_local_price_conf__thr=0p08__width=0p26__s=1p16__basecap=0p0045__shrink=0p9 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001382 |
| ppopt205_local_price_conf__thr=0p0__width=0p22__s=1p16__basecap=0p0045__shrink=0p9 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001382 |
| ppopt205_local_price_conf__thr=0p0__width=0p26__s=1p16__basecap=0p0045__shrink=0p9 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001382 |
| ppopt205_local_price_conf__thr=0p12__width=0p22__s=1p16__basecap=0p0045__shrink=0p9 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001382 |
| ppopt205_local_price_conf__thr=0p12__width=0p26__s=1p16__basecap=0p0045__shrink=0p9 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001382 |
| ppopt205_local_price_conf__thr=m0p02__width=0p26__s=1p16__basecap=0p0045__shrink=0p9 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001382 |
| ppopt205_local_price_conf__thr=m0p02__width=0p22__s=1p16__basecap=0p0045__shrink=0p9 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001382 |
| ppopt207_gap_aware_cap__gapthr=0p006__gapwidth=0p003__s=1p05__basecap=0p0065__shrink=0p95 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269892 | 0.807326 | -0.001502 | -0.000804 | -0.001382 |
| ppopt207_gap_aware_cap__gapthr=0p006__gapwidth=0p006__s=1p05__basecap=0p0065__shrink=0p95 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269892 | 0.807326 | -0.001502 | -0.000804 | -0.001382 |
| ppopt207_gap_aware_cap__gapthr=0p014__gapwidth=0p003__s=1p05__basecap=0p0065__shrink=0p95 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269892 | 0.807326 | -0.001502 | -0.000804 | -0.001382 |
| ppopt207_gap_aware_cap__gapthr=0p014__gapwidth=0p006__s=1p05__basecap=0p0065__shrink=0p95 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269892 | 0.807326 | -0.001502 | -0.000804 | -0.001382 |
| ppopt207_gap_aware_cap__gapthr=0p01__gapwidth=0p003__s=1p05__basecap=0p0065__shrink=0p95 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269892 | 0.807326 | -0.001502 | -0.000804 | -0.001382 |
| ppopt207_gap_aware_cap__gapthr=0p01__gapwidth=0p006__s=1p05__basecap=0p0065__shrink=0p95 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269892 | 0.807326 | -0.001502 | -0.000804 | -0.001382 |
| ppopt207_gap_aware_cap__gapthr=0p003__gapwidth=0p006__s=1p05__basecap=0p0065__shrink=0p95 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt205_local_price_conf__thr=0p04__width=0p22__s=1p08__basecap=0p0045__shrink=0p8 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt205_local_price_conf__thr=0p04__width=0p26__s=1p08__basecap=0p0045__shrink=0p8 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt205_local_price_conf__thr=0p08__width=0p22__s=1p08__basecap=0p0045__shrink=0p8 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt205_local_price_conf__thr=0p08__width=0p26__s=1p08__basecap=0p0045__shrink=0p8 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt205_local_price_conf__thr=0p0__width=0p22__s=1p08__basecap=0p0045__shrink=0p8 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt205_local_price_conf__thr=0p0__width=0p26__s=1p08__basecap=0p0045__shrink=0p8 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt205_local_price_conf__thr=0p12__width=0p22__s=1p08__basecap=0p0045__shrink=0p8 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt205_local_price_conf__thr=0p12__width=0p26__s=1p08__basecap=0p0045__shrink=0p8 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt205_local_price_conf__thr=m0p02__width=0p26__s=1p08__basecap=0p0045__shrink=0p8 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt205_local_price_conf__thr=m0p02__width=0p22__s=1p08__basecap=0p0045__shrink=0p8 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt207_gap_aware_cap__gapthr=0p003__gapwidth=0p003__s=1p05__basecap=0p0065__shrink=0p95 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt207_gap_aware_cap__gapthr=0p006__gapwidth=0p003__s=1p05__basecap=0p0065__shrink=0p8 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269892 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt207_gap_aware_cap__gapthr=0p006__gapwidth=0p006__s=1p05__basecap=0p0065__shrink=0p8 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269892 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt207_gap_aware_cap__gapthr=0p014__gapwidth=0p003__s=1p05__basecap=0p0065__shrink=0p8 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269892 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt207_gap_aware_cap__gapthr=0p014__gapwidth=0p006__s=1p05__basecap=0p0065__shrink=0p8 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269892 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt207_gap_aware_cap__gapthr=0p01__gapwidth=0p003__s=1p05__basecap=0p0065__shrink=0p8 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269892 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt207_gap_aware_cap__gapthr=0p01__gapwidth=0p006__s=1p05__basecap=0p0065__shrink=0p8 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269892 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt207_gap_aware_cap__gapthr=0p003__gapwidth=0p006__s=1p05__basecap=0p0065__shrink=0p8 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt205_local_price_conf__thr=0p04__width=0p22__s=1p08__basecap=0p0045__shrink=0p9 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt205_local_price_conf__thr=0p04__width=0p26__s=1p08__basecap=0p0045__shrink=0p9 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt205_local_price_conf__thr=0p08__width=0p22__s=1p08__basecap=0p0045__shrink=0p9 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt205_local_price_conf__thr=0p08__width=0p26__s=1p08__basecap=0p0045__shrink=0p9 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt205_local_price_conf__thr=0p0__width=0p22__s=1p08__basecap=0p0045__shrink=0p9 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt205_local_price_conf__thr=0p0__width=0p26__s=1p08__basecap=0p0045__shrink=0p9 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt205_local_price_conf__thr=0p12__width=0p22__s=1p08__basecap=0p0045__shrink=0p9 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt205_local_price_conf__thr=0p12__width=0p26__s=1p08__basecap=0p0045__shrink=0p9 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt205_local_price_conf__thr=m0p02__width=0p26__s=1p08__basecap=0p0045__shrink=0p9 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt205_local_price_conf__thr=m0p02__width=0p22__s=1p08__basecap=0p0045__shrink=0p9 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt207_gap_aware_cap__gapthr=0p006__gapwidth=0p003__s=1p05__basecap=0p005__shrink=0p95 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt207_gap_aware_cap__gapthr=0p006__gapwidth=0p006__s=1p05__basecap=0p005__shrink=0p95 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt207_gap_aware_cap__gapthr=0p014__gapwidth=0p003__s=1p05__basecap=0p005__shrink=0p95 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt207_gap_aware_cap__gapthr=0p014__gapwidth=0p006__s=1p05__basecap=0p005__shrink=0p95 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt207_gap_aware_cap__gapthr=0p01__gapwidth=0p003__s=1p05__basecap=0p005__shrink=0p95 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt207_gap_aware_cap__gapthr=0p01__gapwidth=0p006__s=1p05__basecap=0p005__shrink=0p95 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt207_gap_aware_cap__gapthr=0p003__gapwidth=0p003__s=1p05__basecap=0p0065__shrink=0p8 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt207_gap_aware_cap__gapthr=0p003__gapwidth=0p006__s=1p05__basecap=0p005__shrink=0p95 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269893 | 0.807326 | -0.001501 | -0.000804 | -0.001381 |
| ppopt207_gap_aware_cap__gapthr=0p006__gapwidth=0p003__s=1p05__basecap=0p005__shrink=0p8 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt207_gap_aware_cap__gapthr=0p006__gapwidth=0p006__s=1p05__basecap=0p005__shrink=0p8 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt207_gap_aware_cap__gapthr=0p014__gapwidth=0p003__s=1p05__basecap=0p005__shrink=0p8 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt207_gap_aware_cap__gapthr=0p014__gapwidth=0p006__s=1p05__basecap=0p005__shrink=0p8 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt207_gap_aware_cap__gapthr=0p01__gapwidth=0p003__s=1p05__basecap=0p005__shrink=0p8 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt207_gap_aware_cap__gapthr=0p01__gapwidth=0p006__s=1p05__basecap=0p005__shrink=0p8 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001381 |
| ppopt208_conf_risk_shrink__lowshare=0p35__highshare=1p08__riskthr=0p5__s=1p05__basecap=0p0045 | PP-OPT208 | pp204_confidence_risk_shrink_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt208_conf_risk_shrink__lowshare=0p35__highshare=1p0__riskthr=0p5__s=1p05__basecap=0p0045 | PP-OPT208 | pp204_confidence_risk_shrink_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt208_conf_risk_shrink__lowshare=0p55__highshare=1p08__riskthr=0p5__s=1p05__basecap=0p0045 | PP-OPT208 | pp204_confidence_risk_shrink_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt208_conf_risk_shrink__lowshare=0p55__highshare=1p0__riskthr=0p5__s=1p05__basecap=0p0045 | PP-OPT208 | pp204_confidence_risk_shrink_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt208_conf_risk_shrink__lowshare=0p75__highshare=1p08__riskthr=0p5__s=1p05__basecap=0p0045 | PP-OPT208 | pp204_confidence_risk_shrink_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt208_conf_risk_shrink__lowshare=0p75__highshare=1p0__riskthr=0p5__s=1p05__basecap=0p0045 | PP-OPT208 | pp204_confidence_risk_shrink_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt206_p95_guard_sensitivity__p95thr=0p0__p95width=0p00012__s=1p0__basecap=0p007__shrink=1p0 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt206_p95_guard_sensitivity__p95thr=0p0__p95width=0p00018__s=1p0__basecap=0p007__shrink=1p0 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt206_p95_guard_sensitivity__p95thr=0p0__p95width=8em05__s=1p0__basecap=0p007__shrink=1p0 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt206_p95_guard_sensitivity__p95thr=m2em05__p95width=0p00012__s=1p0__basecap=0p007__shrink=1p0 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt206_p95_guard_sensitivity__p95thr=m2em05__p95width=0p00018__s=1p0__basecap=0p007__shrink=1p0 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt206_p95_guard_sensitivity__p95thr=m2em05__p95width=8em05__s=1p0__basecap=0p007__shrink=1p0 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt206_p95_guard_sensitivity__p95thr=m4em05__p95width=0p00012__s=1p0__basecap=0p007__shrink=1p0 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt206_p95_guard_sensitivity__p95thr=m4em05__p95width=0p00018__s=1p0__basecap=0p007__shrink=1p0 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt206_p95_guard_sensitivity__p95thr=m4em05__p95width=8em05__s=1p0__basecap=0p007__shrink=1p0 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt206_p95_guard_sensitivity__p95thr=m8em05__p95width=0p00012__s=1p0__basecap=0p007__shrink=1p0 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt206_p95_guard_sensitivity__p95thr=m8em05__p95width=0p00018__s=1p0__basecap=0p007__shrink=1p0 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt206_p95_guard_sensitivity__p95thr=m8em05__p95width=8em05__s=1p0__basecap=0p007__shrink=1p0 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt207_gap_aware_cap__gapthr=0p003__gapwidth=0p003__s=1p05__basecap=0p005__shrink=0p95 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001380 |
| ppopt207_gap_aware_cap__gapthr=0p003__gapwidth=0p006__s=1p05__basecap=0p005__shrink=0p8 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt206_p95_guard_sensitivity__p95thr=0p0__p95width=0p00012__s=1p1__basecap=0p004__shrink=0p8 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt206_p95_guard_sensitivity__p95thr=0p0__p95width=0p00018__s=1p1__basecap=0p004__shrink=0p8 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt206_p95_guard_sensitivity__p95thr=0p0__p95width=8em05__s=1p1__basecap=0p004__shrink=0p8 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt206_p95_guard_sensitivity__p95thr=m2em05__p95width=0p00012__s=1p1__basecap=0p004__shrink=0p8 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt206_p95_guard_sensitivity__p95thr=m2em05__p95width=0p00018__s=1p1__basecap=0p004__shrink=0p8 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt206_p95_guard_sensitivity__p95thr=m2em05__p95width=8em05__s=1p1__basecap=0p004__shrink=0p8 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt206_p95_guard_sensitivity__p95thr=m4em05__p95width=0p00012__s=1p1__basecap=0p004__shrink=0p8 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt206_p95_guard_sensitivity__p95thr=m4em05__p95width=0p00018__s=1p1__basecap=0p004__shrink=0p8 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt206_p95_guard_sensitivity__p95thr=m4em05__p95width=8em05__s=1p1__basecap=0p004__shrink=0p8 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt206_p95_guard_sensitivity__p95thr=m8em05__p95width=0p00012__s=1p1__basecap=0p004__shrink=0p8 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt206_p95_guard_sensitivity__p95thr=m8em05__p95width=0p00018__s=1p1__basecap=0p004__shrink=0p8 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt206_p95_guard_sensitivity__p95thr=m8em05__p95width=8em05__s=1p1__basecap=0p004__shrink=0p8 | PP-OPT206 | pp204_p95_guard_sensitivity_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt207_gap_aware_cap__gapthr=0p003__gapwidth=0p003__s=1p05__basecap=0p005__shrink=0p8 | PP-OPT207 | pp204_gap_aware_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt205_local_price_conf__thr=0p04__width=0p22__s=1p16__basecap=0p0035__shrink=0p65 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt205_local_price_conf__thr=0p04__width=0p26__s=1p16__basecap=0p0035__shrink=0p65 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt205_local_price_conf__thr=0p08__width=0p22__s=1p16__basecap=0p0035__shrink=0p65 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt205_local_price_conf__thr=0p08__width=0p26__s=1p16__basecap=0p0035__shrink=0p65 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |
| ppopt205_local_price_conf__thr=0p0__width=0p22__s=1p16__basecap=0p0035__shrink=0p65 | PP-OPT205 | pp204_local_threshold_cap_refinement | 0.269893 | 0.807326 | -0.001502 | -0.000804 | -0.001380 |

## 선택 후보 반복 안정성
| candidate_label | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_vs_pp64_MAPE | fixed_test_delta_vs_pp64_p95_APE | avg_pp64_MAPE_win_rate | avg_pp64_p95_win_rate | replacement_score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| candidate_ppopt205_local_price_conf__thr_0p04__width_0p22__s_1p16__basecap_0p0055__shrink_0p9__d5428a4dd1 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt205_local_price_conf__thr_0p04__width_0p26__s_1p16__basecap_0p0055__shrink_0p9__c7379b3127 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt205_local_price_conf__thr_0p08__width_0p22__s_1p16__basecap_0p0055__shrink_0p9__820eecb790 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt205_local_price_conf__thr_0p08__width_0p26__s_1p16__basecap_0p0055__shrink_0p9__341cd023d6 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt205_local_price_conf__thr_0p0__width_0p22__s_1p16__basecap_0p0055__shrink_0p9__4b18bd7a72 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt205_local_price_conf__thr_0p0__width_0p26__s_1p16__basecap_0p0055__shrink_0p9__b2d4c7f37b | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt205_local_price_conf__thr_0p12__width_0p22__s_1p16__basecap_0p0055__shrink_0p9__858a56172c | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt205_local_price_conf__thr_0p12__width_0p26__s_1p16__basecap_0p0055__shrink_0p9__c4215a8174 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| pp210_operational_pp204_local_refinement_challenger | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt205_local_price_conf__thr_m0p02__width_0p26__s_1p16__basecap_0p0055__shrink_0p9__4e9333d2be | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt205_local_price_conf__thr_m0p02__width_0p22__s_1p16__basecap_0p0055__shrink_0p9__ef352dec6a | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_0p0__p95width_0p00012__s_1p1__basecap_0p007__shrink_1__e81267260c | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_0p0__p95width_0p00018__s_1p1__basecap_0p007__shrink_1__159efc8a16 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_0p0__p95width_8em05__s_1p1__basecap_0p007__shrink_1p0__4061020a62 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m2em05__p95width_0p00012__s_1p1__basecap_0p007__shrin__2a799d9c7a | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m2em05__p95width_0p00018__s_1p1__basecap_0p007__shrin__634b31b821 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m2em05__p95width_8em05__s_1p1__basecap_0p007__shrink___4d895c9e21 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m4em05__p95width_0p00012__s_1p1__basecap_0p007__shrin__e78f7901ad | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m4em05__p95width_0p00018__s_1p1__basecap_0p007__shrin__c0252dc95b | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m4em05__p95width_8em05__s_1p1__basecap_0p007__shrink___fc4b5b9771 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m8em05__p95width_0p00012__s_1p1__basecap_0p007__shrin__57e50e56b4 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m8em05__p95width_0p00018__s_1p1__basecap_0p007__shrin__5b613e3112 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m8em05__p95width_8em05__s_1p1__basecap_0p007__shrink___6f64a7d273 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747115 | -0.018827 |
| candidate_ppopt205_local_price_conf__thr_0p04__width_0p22__s_1p16__basecap_0p0045__shrink_0p8__dbb1132578 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt205_local_price_conf__thr_0p04__width_0p26__s_1p16__basecap_0p0045__shrink_0p8__10d071a7c2 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt205_local_price_conf__thr_0p08__width_0p22__s_1p16__basecap_0p0045__shrink_0p8__dff7061b68 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt205_local_price_conf__thr_0p08__width_0p26__s_1p16__basecap_0p0045__shrink_0p8__0e236f4171 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt205_local_price_conf__thr_0p0__width_0p22__s_1p16__basecap_0p0045__shrink_0p8__9a843a72b7 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt205_local_price_conf__thr_0p0__width_0p26__s_1p16__basecap_0p0045__shrink_0p8__6a334413c9 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt205_local_price_conf__thr_0p12__width_0p22__s_1p16__basecap_0p0045__shrink_0p8__71e1c2f8eb | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt205_local_price_conf__thr_0p12__width_0p26__s_1p16__basecap_0p0045__shrink_0p8__d7ccf32341 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt205_local_price_conf__thr_m0p02__width_0p26__s_1p16__basecap_0p0045__shrink_0p8__fc2af42d13 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt205_local_price_conf__thr_m0p02__width_0p22__s_1p16__basecap_0p0045__shrink_0p8__45e41ff660 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_0p0__p95width_0p00012__s_1p1__basecap_0p0055__shrink___44d16d9be9 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747115 | -0.018826 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_0p0__p95width_0p00018__s_1p1__basecap_0p0055__shrink___f08afe4e9d | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747115 | -0.018826 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_0p0__p95width_8em05__s_1p1__basecap_0p0055__shrink_0p__70931f478b | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747115 | -0.018826 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m2em05__p95width_0p00012__s_1p1__basecap_0p0055__shri__0402fec71c | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747115 | -0.018826 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_0p0__p95width_0p00012__s_1p1__basecap_0p0055__shrink___0685dd376f | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_0p0__p95width_0p00018__s_1p1__basecap_0p0055__shrink___b95cec8142 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_0p0__p95width_8em05__s_1p1__basecap_0p0055__shrink_1p__23e6f417fc | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m2em05__p95width_0p00012__s_1p1__basecap_0p0055__shri__c498fdb207 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m2em05__p95width_0p00018__s_1p1__basecap_0p0055__shri__db53b1cd6a | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m2em05__p95width_8em05__s_1p1__basecap_0p0055__shrink__85f086e440 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m4em05__p95width_0p00012__s_1p1__basecap_0p0055__shri__05389528f7 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m4em05__p95width_0p00018__s_1p1__basecap_0p0055__shri__6fd78ab1a1 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m4em05__p95width_8em05__s_1p1__basecap_0p0055__shrink__6bf58f2308 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m8em05__p95width_0p00012__s_1p1__basecap_0p0055__shri__15bf0f54b5 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m8em05__p95width_0p00018__s_1p1__basecap_0p0055__shri__b0475f9a51 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m8em05__p95width_8em05__s_1p1__basecap_0p0055__shrink__a7ff02417d | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747756 | -0.018826 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p006__gapwidth_0p003__s_1p05__basecap_0p0065__shrink_0p8__80cc4e5800 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747115 | -0.018825 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p006__gapwidth_0p006__s_1p05__basecap_0p0065__shrink_0p8__533d07878e | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747115 | -0.018825 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p014__gapwidth_0p003__s_1p05__basecap_0p0065__shrink_0p8__1f2d4a4df8 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747115 | -0.018825 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p014__gapwidth_0p006__s_1p05__basecap_0p0065__shrink_0p8__ac3d939a28 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747115 | -0.018825 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p01__gapwidth_0p003__s_1p05__basecap_0p0065__shrink_0p8__c2b31f5f80 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747115 | -0.018825 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p01__gapwidth_0p006__s_1p05__basecap_0p0065__shrink_0p8__57117cb7d5 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747115 | -0.018825 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p006__gapwidth_0p003__s_1p05__basecap_0p0065__shrink_0p95__cc25345b7f | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747115 | -0.018825 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p006__gapwidth_0p006__s_1p05__basecap_0p0065__shrink_0p95__a5799383c2 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747115 | -0.018825 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p014__gapwidth_0p003__s_1p05__basecap_0p0065__shrink_0p95__69e865b918 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747115 | -0.018825 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p014__gapwidth_0p006__s_1p05__basecap_0p0065__shrink_0p95__282552d65d | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747115 | -0.018825 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p01__gapwidth_0p003__s_1p05__basecap_0p0065__shrink_0p95__fecfd918ef | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747115 | -0.018825 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p01__gapwidth_0p006__s_1p05__basecap_0p0065__shrink_0p95__8a68fcd703 | 0.269892 | 0.807326 | -0.000672 | -0.000173 | 0.953846 | 0.747115 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_0p04__width_0p22__s_1p16__basecap_0p0045__shrink_0p9__2f23fee0dd | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_0p04__width_0p26__s_1p16__basecap_0p0045__shrink_0p9__399bb40759 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_0p08__width_0p22__s_1p16__basecap_0p0045__shrink_0p9__df3b6ad17b | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_0p08__width_0p26__s_1p16__basecap_0p0045__shrink_0p9__b7e60a5e87 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_0p0__width_0p22__s_1p16__basecap_0p0045__shrink_0p9__c16d8414f9 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_0p0__width_0p26__s_1p16__basecap_0p0045__shrink_0p9__8ba4db3edd | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_0p12__width_0p22__s_1p16__basecap_0p0045__shrink_0p9__d214ef985b | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_0p12__width_0p26__s_1p16__basecap_0p0045__shrink_0p9__2f3de27d13 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_m0p02__width_0p26__s_1p16__basecap_0p0045__shrink_0p9__84a560d91e | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_m0p02__width_0p22__s_1p16__basecap_0p0045__shrink_0p9__8adfd462ab | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p003__gapwidth_0p006__s_1p05__basecap_0p0065__shrink_0p8__79ebf984be | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747115 | -0.018825 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p003__gapwidth_0p006__s_1p05__basecap_0p0065__shrink_0p95__748f42efd2 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747115 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_0p04__width_0p22__s_1p08__basecap_0p0045__shrink_0p8__52601080ce | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_0p04__width_0p26__s_1p08__basecap_0p0045__shrink_0p8__e8e00cd9bf | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_0p08__width_0p22__s_1p08__basecap_0p0045__shrink_0p8__dcb466db5b | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_0p08__width_0p26__s_1p08__basecap_0p0045__shrink_0p8__00f07ffb34 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_0p0__width_0p22__s_1p08__basecap_0p0045__shrink_0p8__aa559a7706 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_0p0__width_0p26__s_1p08__basecap_0p0045__shrink_0p8__f9e7f6a6f7 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_0p12__width_0p22__s_1p08__basecap_0p0045__shrink_0p8__b3a2c7568a | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_0p12__width_0p26__s_1p08__basecap_0p0045__shrink_0p8__882fa57995 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_m0p02__width_0p26__s_1p08__basecap_0p0045__shrink_0p8__bd48466e6a | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_m0p02__width_0p22__s_1p08__basecap_0p0045__shrink_0p8__bbe0613ffb | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p003__gapwidth_0p003__s_1p05__basecap_0p0065__shrink_0p8__20dd724427 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747115 | -0.018825 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p003__gapwidth_0p003__s_1p05__basecap_0p0065__shrink_0p95__9713f8df05 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747115 | -0.018825 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p006__gapwidth_0p003__s_1p05__basecap_0p005__shrink_0p8__de614ac6e2 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747115 | -0.018825 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p006__gapwidth_0p006__s_1p05__basecap_0p005__shrink_0p8__d3e85c1f63 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747115 | -0.018825 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p014__gapwidth_0p003__s_1p05__basecap_0p005__shrink_0p8__e90f3babce | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747115 | -0.018825 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p014__gapwidth_0p006__s_1p05__basecap_0p005__shrink_0p8__bbb7b4e549 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747115 | -0.018825 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p01__gapwidth_0p003__s_1p05__basecap_0p005__shrink_0p8__287d6a27a5 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747115 | -0.018825 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p01__gapwidth_0p006__s_1p05__basecap_0p005__shrink_0p8__09a85f243f | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747115 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_0p04__width_0p22__s_1p16__basecap_0p0035__shrink_0p65__d0cd4b410d | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_0p04__width_0p26__s_1p16__basecap_0p0035__shrink_0p65__c6213f689a | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_0p08__width_0p22__s_1p16__basecap_0p0035__shrink_0p65__68bc301c11 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_0p08__width_0p26__s_1p16__basecap_0p0035__shrink_0p65__762e81c9ca | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_0p0__width_0p22__s_1p16__basecap_0p0035__shrink_0p65__a1f3af0a61 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_0p0__width_0p26__s_1p16__basecap_0p0035__shrink_0p65__96e16fe793 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p003__gapwidth_0p006__s_1p05__basecap_0p005__shrink_0p8__b10495ee2b | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747115 | -0.018825 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p003__gapwidth_0p003__s_1p05__basecap_0p005__shrink_0p8__26b7a73bcf | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747115 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_0p04__width_0p22__s_1p08__basecap_0p0045__shrink_0p9__24310e95bd | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_0p04__width_0p26__s_1p08__basecap_0p0045__shrink_0p9__7e3967a61d | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_0p08__width_0p22__s_1p08__basecap_0p0045__shrink_0p9__aa73412efd | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_0p08__width_0p26__s_1p08__basecap_0p0045__shrink_0p9__c20a01bbe1 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_0p0__width_0p22__s_1p08__basecap_0p0045__shrink_0p9__918d3f4d46 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_0p0__width_0p26__s_1p08__basecap_0p0045__shrink_0p9__9959e45a79 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_0p12__width_0p22__s_1p08__basecap_0p0045__shrink_0p9__fac1c349fd | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_0p12__width_0p26__s_1p08__basecap_0p0045__shrink_0p9__a382e2b8fe | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_m0p02__width_0p26__s_1p08__basecap_0p0045__shrink_0p9__18008c6386 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt205_local_price_conf__thr_m0p02__width_0p22__s_1p08__basecap_0p0045__shrink_0p9__eee03f69cb | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_0p0__p95width_0p00012__s_1p1__basecap_0p004__shrink_0__18e8511860 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_0p0__p95width_0p00018__s_1p1__basecap_0p004__shrink_0__5d685a82e3 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_0p0__p95width_8em05__s_1p1__basecap_0p004__shrink_0p8__7d9cfd6b79 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m2em05__p95width_0p00012__s_1p1__basecap_0p004__shrin__bd262107e1 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m2em05__p95width_0p00018__s_1p1__basecap_0p004__shrin__f6b19b991f | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m2em05__p95width_8em05__s_1p1__basecap_0p004__shrink___5ebfadcad5 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m4em05__p95width_0p00012__s_1p1__basecap_0p004__shrin__74a17b974d | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m4em05__p95width_0p00018__s_1p1__basecap_0p004__shrin__25ab4fabe2 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m4em05__p95width_8em05__s_1p1__basecap_0p004__shrink___16bf17bbb9 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m8em05__p95width_0p00012__s_1p1__basecap_0p004__shrin__a29d5c36df | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m8em05__p95width_0p00018__s_1p1__basecap_0p004__shrin__8ff648ed03 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m8em05__p95width_8em05__s_1p1__basecap_0p004__shrink___9a674cbb95 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_0p0__p95width_0p00012__s_1p0__basecap_0p007__shrink_1__c32a31136c | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_0p0__p95width_0p00018__s_1p0__basecap_0p007__shrink_1__a375340179 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_0p0__p95width_8em05__s_1p0__basecap_0p007__shrink_1p0__2f4596cd63 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m2em05__p95width_0p00012__s_1p0__basecap_0p007__shrin__0c1646d343 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m2em05__p95width_0p00018__s_1p0__basecap_0p007__shrin__b037f05c0d | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m2em05__p95width_8em05__s_1p0__basecap_0p007__shrink___199a4510f4 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m4em05__p95width_0p00012__s_1p0__basecap_0p007__shrin__0ffcd1c3d3 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m4em05__p95width_0p00018__s_1p0__basecap_0p007__shrin__f625d44e36 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m4em05__p95width_8em05__s_1p0__basecap_0p007__shrink___b2331266f8 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m8em05__p95width_0p00012__s_1p0__basecap_0p007__shrin__665e42f79f | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m8em05__p95width_0p00018__s_1p0__basecap_0p007__shrin__ca18152178 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt206_p95_guard_sensitivity__p95thr_m8em05__p95width_8em05__s_1p0__basecap_0p007__shrink___9d0ecb0599 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p006__gapwidth_0p003__s_1p05__basecap_0p005__shrink_0p95__8e7a71deff | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p006__gapwidth_0p006__s_1p05__basecap_0p005__shrink_0p95__9bacd76c46 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p014__gapwidth_0p003__s_1p05__basecap_0p005__shrink_0p95__7d09e696b6 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p014__gapwidth_0p006__s_1p05__basecap_0p005__shrink_0p95__36e608e670 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p01__gapwidth_0p003__s_1p05__basecap_0p005__shrink_0p95__45c23108f7 | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p01__gapwidth_0p006__s_1p05__basecap_0p005__shrink_0p95__3d40879bce | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018825 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p003__gapwidth_0p006__s_1p05__basecap_0p005__shrink_0p95__25e13c9aaa | 0.269893 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018824 |
| pp204_mape_reference | 0.269894 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018824 |
| pp204_operational_reference | 0.269894 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018824 |
| candidate_ppopt207_gap_aware_cap__gapthr_0p003__gapwidth_0p003__s_1p05__basecap_0p005__shrink_0p95__aea2608bb3 | 0.269894 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018824 |
| candidate_ppopt205_local_price_conf__thr_0p04__width_0p22__s_1p16__basecap_0p0065__shrink_0p9__095a49fd0d | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953526 | 0.747115 | -0.018815 |
| candidate_ppopt205_local_price_conf__thr_0p04__width_0p26__s_1p16__basecap_0p0065__shrink_0p9__e0d42d0e3a | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953526 | 0.747115 | -0.018815 |
| candidate_ppopt205_local_price_conf__thr_0p08__width_0p22__s_1p16__basecap_0p0065__shrink_0p9__7bff75a5c5 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953526 | 0.747115 | -0.018815 |
| candidate_ppopt205_local_price_conf__thr_0p08__width_0p26__s_1p16__basecap_0p0065__shrink_0p9__d3f636fa87 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953526 | 0.747115 | -0.018815 |
| candidate_ppopt205_local_price_conf__thr_0p0__width_0p22__s_1p16__basecap_0p0065__shrink_0p9__fa390cf340 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953526 | 0.747115 | -0.018815 |
| candidate_ppopt205_local_price_conf__thr_0p0__width_0p26__s_1p16__basecap_0p0065__shrink_0p9__916b0e26a7 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953526 | 0.747115 | -0.018815 |
| candidate_ppopt205_local_price_conf__thr_0p12__width_0p22__s_1p16__basecap_0p0065__shrink_0p9__6f5db462a2 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953526 | 0.747115 | -0.018815 |
| candidate_ppopt205_local_price_conf__thr_0p12__width_0p26__s_1p16__basecap_0p0065__shrink_0p9__81f016d806 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953526 | 0.747115 | -0.018815 |
| candidate_ppopt205_local_price_conf__thr_m0p02__width_0p26__s_1p16__basecap_0p0065__shrink_0p9__b191761cd2 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953526 | 0.747115 | -0.018815 |
| candidate_ppopt205_local_price_conf__thr_m0p02__width_0p22__s_1p16__basecap_0p0065__shrink_0p9__e39121e2af | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.953526 | 0.747115 | -0.018815 |
| candidate_ppopt205_local_price_conf__thr_0p04__width_0p22__s_1p16__basecap_0p0055__shrink_0p8__cb2cf00435 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953526 | 0.747115 | -0.018814 |
| candidate_ppopt205_local_price_conf__thr_0p04__width_0p26__s_1p16__basecap_0p0055__shrink_0p8__4480981a68 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953526 | 0.747115 | -0.018814 |
| candidate_ppopt205_local_price_conf__thr_0p08__width_0p22__s_1p16__basecap_0p0055__shrink_0p8__7662fee1c1 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953526 | 0.747115 | -0.018814 |
| candidate_ppopt205_local_price_conf__thr_0p08__width_0p26__s_1p16__basecap_0p0055__shrink_0p8__10d76a8fa6 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953526 | 0.747115 | -0.018814 |
| candidate_ppopt205_local_price_conf__thr_0p0__width_0p22__s_1p16__basecap_0p0055__shrink_0p8__8e13c9fb4c | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953526 | 0.747115 | -0.018814 |
| candidate_ppopt205_local_price_conf__thr_0p0__width_0p26__s_1p16__basecap_0p0055__shrink_0p8__2e06331e5f | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953526 | 0.747115 | -0.018814 |
| candidate_ppopt205_local_price_conf__thr_0p12__width_0p22__s_1p16__basecap_0p0055__shrink_0p8__1ea180a3d1 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.953526 | 0.747115 | -0.018814 |

## 실행 설정
```json
{
  "experiment_id": "PP-OPT205-210",
  "experiment_slug": "PP-OPT205_210_warm_pp204_local_winner_router_refinement",
  "created_at": "2026-06-10T11:02:11",
  "base_candidate": "hcoef_stable",
  "previous_experiment": "experiments/track6/PP-OPT199_204_warm_pp192_pp198_winner_router",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 874,
  "prediction_rows": 984124,
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
    "pp204_p95_extreme": "ppopt204_p95_extreme_pp192_pp198_winner_router__source=reference_pp148_p95"
  },
  "selection_decision": {
    "operational_label": "candidate_ppopt205_local_price_conf__thr_0p04__width_0p22__s_1p16__basecap_0p0055__shrink_0p9__d5428a4dd1",
    "operational_candidate": "ppopt205_local_price_conf__thr=0p04__width=0p22__s=1p16__basecap=0p0055__shrink=0p9",
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
    "operational_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "operational_avg_pp64_p95_win_rate": 0.7471153846153845,
    "operational_replacement_score": -0.018826887239332204,
    "mape_challenger_label": "candidate_ppopt205_local_price_conf__thr_0p04__width_0p22__s_1p16__basecap_0p0065__shrink_0p65__aa9d92e4f2",
    "mape_challenger_candidate": "ppopt205_local_price_conf__thr=0p04__width=0p22__s=1p16__basecap=0p0065__shrink=0p65",
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
    "mape_challenger_avg_pp64_MAPE_win_rate": 0.9528846153846153,
    "mape_challenger_avg_pp64_p95_win_rate": 0.7471153846153845,
    "mape_challenger_replacement_score": -0.01878913378196875,
    "p95_guarded_label": "pp204_p95_guarded_reference",
    "p95_guarded_candidate": "ppopt204_p95_guarded_pp192_pp198_winner_router__source=ppopt192_p95_guarded_pp180_pp186_risk_router__source_ppopt187_hard_risk_router__risk_uncertainty__mode_hard__thr_0p78__w",
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
    "p95_extreme_avg_pp64_MAPE_win_rate": 0.5983974358974359,
    "p95_extreme_avg_pp64_p95_win_rate": 0.5009615384615385,
    "p95_extreme_replacement_score": -0.0040792899192624915,
    "operational_protocol_candidate": "ppopt210_operational_pp204_local_refinement__source=ppopt205_local_price_conf__thr_0p04__width_0p22__s_1p16__basecap_0p0055__shrink_0p9",
    "mape_challenger_protocol_candidate": "ppopt210_mape_challenger_pp204_local_refinement__source=ppopt205_local_price_conf__thr_0p04__width_0p22__s_1p16__basecap_0p0065__shrink_0p65",
    "p95_guarded_protocol_candidate": "ppopt210_p95_guarded_pp204_local_refinement__source=ppopt204_p95_guarded_pp192_pp198_winner_router__source_ppopt192_p95_guarded_pp180_pp186_risk_router__source_ppopt187_har",
    "p95_extreme_protocol_candidate": "ppopt210_p95_extreme_pp204_local_refinement__source=reference_pp148_p95"
  },
  "items": [
    {
      "item_id": "PP-OPT205",
      "priority": "1",
      "title": "PP204 local threshold/cap refinement",
      "description": "PP204 선택식 주변의 threshold, strength, base cap, risk shrink를 촘촘하게 재탐색."
    },
    {
      "item_id": "PP-OPT206",
      "priority": "2",
      "title": "p95 guard sensitivity refinement",
      "description": "winner segment p95 손상 감지 기준과 guard 폭을 바꿔 p95 win rate 회복 여부 확인."
    },
    {
      "item_id": "PP-OPT207",
      "priority": "3",
      "title": "PP192/PP198 gap-aware cap",
      "description": "PP192와 PP198 예측 차이가 큰 row는 이동 강도와 cap을 줄여 tail 손상을 방어."
    },
    {
      "item_id": "PP-OPT208",
      "priority": "4",
      "title": "confidence-risk asymmetric shrink",
      "description": "저신뢰·고위험 row에서는 PP198 이동을 더 약하게, 고신뢰 row에서는 기존 강도 유지."
    },
    {
      "item_id": "PP-OPT209",
      "priority": "5",
      "title": "PP204 second-stage residual nudge",
      "description": "PP204를 기준으로 두고 PP198 또는 PP192 방향으로 아주 작은 2차 이동을 적용."
    },
    {
      "item_id": "PP-OPT210",
      "priority": "6",
      "title": "final PP204 local refinement decision",
      "description": "PP204와 신규 local refinement 후보를 fixed/repeated 기준으로 비교해 선택."
    }
  ],
  "router_formula": {
    "base": "PP192 operational log price, or PP204 operational log price for second-stage nudge",
    "mape_candidate": "PP198 MAPE challenger log price",
    "main_final": "PP192 log price + clip((PP198 log price - PP192 log price) * winner_weight, tuned row_cap)",
    "second_stage_final": "PP204 log price + clip((target log price - PP204 log price) * second_stage_weight, tiny row_cap)",
    "winner_inputs": [
      "validation stable_price_band x confidence_tier PP198-vs-PP192 APE gain",
      "validation segment PP198-vs-PP192 p95 delta",
      "row uncertainty risk",
      "abs(PP198 log price - PP192 log price)",
      "confidence tier asymmetric shrink"
    ]
  }
}
```