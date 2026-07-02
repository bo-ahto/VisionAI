# PP-OPT199~204 Warm PP192/PP198 winner router 결과

- 작성일: 2026-06-10 10:50
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 목적: PP198이 PP192보다 이기는 row만 선택해 MAPE 개선과 repeated stability를 동시에 확보
- 결론: 운영 후보 fixed test MAPE 0.269894, p95 0.807326. PP192 대비 MAPE -0.000021, replacement score -0.018824. MAPE 후보 MAPE 0.269894, p95 0.807326.

## 주요 후보 test 비교
| candidate | family | item_id | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt204_operational_pp192_pp198_winner_router__source=ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_1p0__basecap_0p006__shrink_0p8 | pp192_pp198_winner_router_operational_selection | PP-OPT204 | 0.140975 | 0.269894 | 0.807326 | 0.397456 | -0.001501 | -0.000804 |
| ppopt204_mape_challenger_pp192_pp198_winner_router__source=ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_1p0__basecap_0p006__shrink_0p8 | pp192_pp198_winner_router_mape_selection | PP-OPT204 | 0.140975 | 0.269894 | 0.807326 | 0.397456 | -0.001501 | -0.000804 |
| ppopt198_operational_segment_router_refinement__source=ppopt194_price_conf_refine__scorethr_0p02__mix_0p25__s_1p05__cap_0p006 | reference_prior | REFERENCE | 0.140975 | 0.269894 | 0.807326 | 0.397455 | -0.001501 | -0.000804 |
| ppopt192_operational_pp180_pp186_risk_router__source=ppopt189_segment_router__seg_price_gap__scorethr_0p02__mix_0p75__s_0p95__cap_0p0025 | reference_prior | REFERENCE | 0.140975 | 0.269914 | 0.807326 | 0.397468 | -0.001481 | -0.000804 |
| ppopt180_operational_basis_generation_challenger__source=ppopt174_direct_basis__source_stack_huber_weighted__thr_0p08__s_0p3__cap_0p004 | reference_prior | REFERENCE | 0.140975 | 0.269933 | 0.807326 | 0.397475 | -0.001462 | -0.000804 |
| ppopt204_p95_guarded_pp192_pp198_winner_router__source=ppopt192_p95_guarded_pp180_pp186_risk_router__source_ppopt187_hard_risk_router__risk_uncertainty__mode_hard__thr_0p78__w | pp192_pp198_winner_router_p95_guarded_selection | PP-OPT204 | 0.140094 | 0.269949 | 0.807255 | 0.397482 | -0.001446 | -0.000875 |
| ppopt186_operational_huber_basis_p95_guard__source=ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p04__s_0p42__cap_0p0045 | reference_prior | REFERENCE | 0.139801 | 0.269961 | 0.807231 | 0.397497 | -0.001434 | -0.000899 |
| ppopt172_operational_pp166_tail_calibration_challenger__source=ppopt169_segment_router__source_pp162_p95_gate__seg_price_conf__thr_m0p04__s_0p5__cap_0p004 | reference_prior | REFERENCE | 0.139801 | 0.269997 | 0.807231 | 0.397516 | -0.001397 | -0.000899 |
| reference_pp126_operational | reference_prior | REFERENCE | 0.136320 | 0.270114 | 0.807490 | 0.397588 | -0.001280 | -0.000640 |
| reference_pp148_operational | reference_prior | REFERENCE | 0.139801 | 0.270140 | 0.807231 | 0.397525 | -0.001255 | -0.000899 |
| reference_pp148_p95 | reference_prior | REFERENCE | 0.141036 | 0.270269 | 0.805949 | 0.397421 | -0.001126 | -0.002181 |
| ppopt204_p95_extreme_pp192_pp198_winner_router__source=reference_pp148_p95 | pp192_pp198_winner_router_p95_extreme_selection | PP-OPT204 | 0.141036 | 0.270269 | 0.805949 | 0.397421 | -0.001126 | -0.002181 |
| reference_pp64_current_best | reference_prior | REFERENCE | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | p95_test_MAPE | p95_test_p95_APE | operational_pass_vs_incumbent | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | final PP192/PP198 winner-router decision | 4 | 0.269949 | 0.807255 | 0.270269 | 0.805949 | False | pp192_pp198_winner_router_p95_guarded_selection | ppopt204_p95_guarded_pp192_pp198_winner_router__source=ppopt192_p95_guarded_pp180_pp186_risk_router__source_ppopt187_hard_risk_router__risk_uncertainty__mode_hard__thr_0p78__w |
| 3 | p95 guarded winner router | 144 | 0.269894 | 0.807326 | 0.269894 | 0.807326 | False | pp192_pp198_p95_guarded_winner_router | ppopt201_p95_guarded_winner__seg=price_conf__thr=0p08__s=1p0__basecap=0p006__shrink=0p8 |
| 2 | row risk winner router | 144 | 0.269901 | 0.807326 | 0.269896 | 0.807326 | False | pp192_pp198_row_risk_winner_router | ppopt200_row_risk_winner__riskthr=0p4__segshare=0p45__s=0p9__cap=0p004 |
| 1 | segment winner router | 400 | 0.269895 | 0.807326 | 0.269894 | 0.807326 | False | pp192_pp198_segment_winner_router | ppopt199_segment_winner__seg=price_conf__thr=0p08__s=1p1__cap=0p0025 |
| 5 | small global blend plus winner gate | 48 | 0.269896 | 0.807326 | 0.269895 | 0.807326 | False | pp192_pp198_global_blend_plus_gate | ppopt203_global_plus_gate__global=0p24__gated=0p7__cap=0p0025 |
| 4 | consensus winner router | 64 | 0.269903 | 0.807326 | 0.269900 | 0.807326 | False | pp192_pp198_consensus_winner_router | ppopt202_consensus_winner__mode=conf70__s=0p85__cap=0p0015 |

## 탐색 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt204_p95_guarded_pp192_pp198_winner_router__source=ppopt192_p95_guarded_pp180_pp186_risk_router__source_ppopt187_hard_risk_router__risk_uncertainty__mode_hard__thr_0p78__w | PP-OPT204 | pp192_pp198_winner_router_p95_guarded_selection | 0.269949 | 0.807255 | -0.001446 | -0.000875 | -0.001537 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p08__s=1p0__basecap=0p006__shrink=0p8 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001379 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p0__s=1p0__basecap=0p006__shrink=0p8 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001379 |
| ppopt204_mape_challenger_pp192_pp198_winner_router__source=ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_1p0__basecap_0p006__shrink_0p8 | PP-OPT204 | pp192_pp198_winner_router_mape_selection | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001379 |
| ppopt204_operational_pp192_pp198_winner_router__source=ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_1p0__basecap_0p006__shrink_0p8 | PP-OPT204 | pp192_pp198_winner_router_operational_selection | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001379 |
| ppopt200_row_risk_winner__riskthr=0p4__segshare=0p45__s=0p9__cap=0p004 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269901 | 0.807326 | -0.001494 | -0.000804 | -0.001379 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p08__s=1p0__basecap=0p004__shrink=0p8 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269894 | 0.807326 | -0.001500 | -0.000804 | -0.001379 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p0__s=1p0__basecap=0p004__shrink=0p8 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269894 | 0.807326 | -0.001500 | -0.000804 | -0.001379 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p08__s=1p0__basecap=0p004__shrink=0p55 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001378 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p0__s=1p0__basecap=0p004__shrink=0p55 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001378 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p08__s=1p0__basecap=0p006__shrink=0p55 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001378 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p0__s=1p0__basecap=0p006__shrink=0p55 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001378 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p08__s=1p0__basecap=0p004__shrink=0p3 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001378 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p0__s=1p0__basecap=0p004__shrink=0p3 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001378 |
| ppopt199_segment_winner__seg=price_conf__thr=0p08__s=1p1__cap=0p0025 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269895 | 0.807326 | -0.001500 | -0.000804 | -0.001377 |
| ppopt199_segment_winner__seg=price_conf__thr=0p0__s=1p1__cap=0p0025 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269895 | 0.807326 | -0.001500 | -0.000804 | -0.001377 |
| ppopt199_segment_winner__seg=price_conf__thr=0p16__s=1p1__cap=0p0025 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269895 | 0.807326 | -0.001500 | -0.000804 | -0.001377 |
| ppopt199_segment_winner__seg=price_conf__thr=m0p08__s=1p1__cap=0p0025 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269895 | 0.807326 | -0.001500 | -0.000804 | -0.001377 |
| ppopt199_segment_winner__seg=price_conf__thr=m0p18__s=1p1__cap=0p0025 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269895 | 0.807326 | -0.001500 | -0.000804 | -0.001377 |
| ppopt199_segment_winner__seg=price_conf__thr=0p08__s=1p1__cap=0p004 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001377 |
| ppopt199_segment_winner__seg=price_conf__thr=0p0__s=1p1__cap=0p004 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001377 |
| ppopt199_segment_winner__seg=price_conf__thr=0p16__s=1p1__cap=0p004 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001377 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p08__s=1p0__basecap=0p0025__shrink=0p8 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269900 | 0.807326 | -0.001495 | -0.000804 | -0.001377 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p0__s=1p0__basecap=0p0025__shrink=0p8 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269900 | 0.807326 | -0.001495 | -0.000804 | -0.001377 |
| ppopt199_segment_winner__seg=price_conf__thr=0p08__s=1p1__cap=0p006 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001377 |
| ppopt199_segment_winner__seg=price_conf__thr=0p0__s=1p1__cap=0p006 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001377 |
| ppopt199_segment_winner__seg=price_conf__thr=0p16__s=1p1__cap=0p006 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001377 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p08__s=1p0__basecap=0p006__shrink=0p3 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001377 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p0__s=1p0__basecap=0p006__shrink=0p3 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001377 |
| ppopt199_segment_winner__seg=price_conf__thr=m0p08__s=1p1__cap=0p004 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001377 |
| ppopt199_segment_winner__seg=price_conf__thr=m0p08__s=1p1__cap=0p006 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001377 |
| ppopt199_segment_winner__seg=price_conf__thr=m0p18__s=1p1__cap=0p004 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001377 |
| ppopt199_segment_winner__seg=price_conf__thr=m0p18__s=1p1__cap=0p006 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001377 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p08__s=0p85__basecap=0p0025__shrink=0p8 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269901 | 0.807326 | -0.001494 | -0.000804 | -0.001377 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p0__s=0p85__basecap=0p0025__shrink=0p8 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269901 | 0.807326 | -0.001494 | -0.000804 | -0.001377 |
| ppopt200_row_risk_winner__riskthr=0p48__segshare=0p45__s=0p7__cap=0p004 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269902 | 0.807326 | -0.001493 | -0.000804 | -0.001376 |
| ppopt200_row_risk_winner__riskthr=0p4__segshare=0p45__s=0p9__cap=0p0025 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269903 | 0.807326 | -0.001492 | -0.000804 | -0.001376 |
| ppopt200_row_risk_winner__riskthr=0p48__segshare=0p65__s=0p7__cap=0p004 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269901 | 0.807326 | -0.001494 | -0.000804 | -0.001376 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p08__s=1p0__basecap=0p0025__shrink=0p3 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269895 | 0.807326 | -0.001499 | -0.000804 | -0.001376 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p0__s=1p0__basecap=0p0025__shrink=0p3 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269895 | 0.807326 | -0.001499 | -0.000804 | -0.001376 |
| ppopt199_segment_winner__seg=price_conf__thr=0p08__s=0p95__cap=0p0025 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269896 | 0.807326 | -0.001499 | -0.000804 | -0.001376 |
| ppopt199_segment_winner__seg=price_conf__thr=0p0__s=0p95__cap=0p0025 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269896 | 0.807326 | -0.001499 | -0.000804 | -0.001376 |
| ppopt199_segment_winner__seg=price_conf__thr=0p16__s=0p95__cap=0p0025 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269896 | 0.807326 | -0.001499 | -0.000804 | -0.001376 |
| ppopt199_segment_winner__seg=price_conf__thr=m0p08__s=0p95__cap=0p0025 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269896 | 0.807326 | -0.001499 | -0.000804 | -0.001375 |
| ppopt199_segment_winner__seg=price_conf__thr=m0p18__s=0p95__cap=0p0025 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269896 | 0.807326 | -0.001499 | -0.000804 | -0.001375 |
| ppopt199_segment_winner__seg=price_conf__thr=0p08__s=0p95__cap=0p004 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269895 | 0.807326 | -0.001500 | -0.000804 | -0.001375 |
| ppopt199_segment_winner__seg=price_conf__thr=0p0__s=0p95__cap=0p004 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269895 | 0.807326 | -0.001500 | -0.000804 | -0.001375 |
| ppopt199_segment_winner__seg=price_conf__thr=0p16__s=0p95__cap=0p004 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269895 | 0.807326 | -0.001500 | -0.000804 | -0.001375 |
| ppopt200_row_risk_winner__riskthr=0p56__segshare=0p45__s=0p9__cap=0p004 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269897 | 0.807326 | -0.001498 | -0.000804 | -0.001375 |
| ppopt199_segment_winner__seg=price_conf__thr=0p08__s=0p95__cap=0p006 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269895 | 0.807326 | -0.001500 | -0.000804 | -0.001375 |
| ppopt199_segment_winner__seg=price_conf__thr=0p0__s=0p95__cap=0p006 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269895 | 0.807326 | -0.001500 | -0.000804 | -0.001375 |
| ppopt199_segment_winner__seg=price_conf__thr=0p16__s=0p95__cap=0p006 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269895 | 0.807326 | -0.001500 | -0.000804 | -0.001375 |
| ppopt199_segment_winner__seg=price_conf__thr=m0p08__s=0p95__cap=0p004 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269895 | 0.807326 | -0.001500 | -0.000804 | -0.001375 |
| ppopt199_segment_winner__seg=price_conf__thr=m0p08__s=0p95__cap=0p006 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269895 | 0.807326 | -0.001500 | -0.000804 | -0.001375 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p08__s=0p65__basecap=0p0025__shrink=0p8 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269902 | 0.807326 | -0.001493 | -0.000804 | -0.001375 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p0__s=0p65__basecap=0p0025__shrink=0p8 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269902 | 0.807326 | -0.001493 | -0.000804 | -0.001375 |
| ppopt199_segment_winner__seg=price_conf__thr=m0p18__s=0p95__cap=0p004 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269895 | 0.807326 | -0.001500 | -0.000804 | -0.001375 |
| ppopt199_segment_winner__seg=price_conf__thr=m0p18__s=0p95__cap=0p006 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269895 | 0.807326 | -0.001500 | -0.000804 | -0.001375 |
| ppopt200_row_risk_winner__riskthr=0p48__segshare=0p45__s=0p7__cap=0p0025 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269903 | 0.807326 | -0.001492 | -0.000804 | -0.001375 |
| ppopt200_row_risk_winner__riskthr=0p48__segshare=0p65__s=0p7__cap=0p0025 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269902 | 0.807326 | -0.001493 | -0.000804 | -0.001375 |
| ppopt203_global_plus_gate__global=0p24__gated=0p7__cap=0p0025 | PP-OPT203 | pp192_pp198_global_blend_plus_gate | 0.269896 | 0.807326 | -0.001499 | -0.000804 | -0.001375 |
| ppopt203_global_plus_gate__global=0p24__gated=0p7__cap=0p004 | PP-OPT203 | pp192_pp198_global_blend_plus_gate | 0.269895 | 0.807326 | -0.001500 | -0.000804 | -0.001375 |
| ppopt200_row_risk_winner__riskthr=0p56__segshare=0p65__s=0p9__cap=0p004 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269897 | 0.807326 | -0.001498 | -0.000804 | -0.001375 |
| ppopt200_row_risk_winner__riskthr=0p4__segshare=0p65__s=0p7__cap=0p004 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269903 | 0.807326 | -0.001492 | -0.000804 | -0.001374 |
| ppopt200_row_risk_winner__riskthr=0p48__segshare=0p65__s=0p7__cap=0p0015 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269902 | 0.807326 | -0.001493 | -0.000804 | -0.001374 |
| ppopt200_row_risk_winner__riskthr=0p48__segshare=0p45__s=0p9__cap=0p004 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269899 | 0.807326 | -0.001496 | -0.000804 | -0.001374 |
| ppopt200_row_risk_winner__riskthr=0p56__segshare=0p85__s=0p9__cap=0p004 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269896 | 0.807326 | -0.001499 | -0.000804 | -0.001374 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p08__s=0p85__basecap=0p006__shrink=0p8 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269897 | 0.807326 | -0.001498 | -0.000804 | -0.001374 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p0__s=0p85__basecap=0p006__shrink=0p8 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269897 | 0.807326 | -0.001498 | -0.000804 | -0.001374 |
| ppopt200_row_risk_winner__riskthr=0p48__segshare=0p65__s=0p9__cap=0p004 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001374 |
| ppopt200_row_risk_winner__riskthr=0p64__segshare=0p45__s=0p9__cap=0p004 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269896 | 0.807326 | -0.001499 | -0.000804 | -0.001374 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p08__s=0p85__basecap=0p004__shrink=0p8 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269897 | 0.807326 | -0.001498 | -0.000804 | -0.001374 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p0__s=0p85__basecap=0p004__shrink=0p8 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269897 | 0.807326 | -0.001498 | -0.000804 | -0.001374 |
| ppopt200_row_risk_winner__riskthr=0p64__segshare=0p65__s=0p9__cap=0p004 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269896 | 0.807326 | -0.001499 | -0.000804 | -0.001374 |
| ppopt200_row_risk_winner__riskthr=0p48__segshare=0p85__s=0p9__cap=0p004 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269897 | 0.807326 | -0.001498 | -0.000804 | -0.001374 |
| ppopt200_row_risk_winner__riskthr=0p64__segshare=0p85__s=0p9__cap=0p0025 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269896 | 0.807326 | -0.001498 | -0.000804 | -0.001374 |
| ppopt200_row_risk_winner__riskthr=0p64__segshare=0p85__s=0p9__cap=0p004 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269896 | 0.807326 | -0.001499 | -0.000804 | -0.001374 |
| ppopt200_row_risk_winner__riskthr=0p56__segshare=0p85__s=0p9__cap=0p0025 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269897 | 0.807326 | -0.001498 | -0.000804 | -0.001374 |
| ppopt200_row_risk_winner__riskthr=0p64__segshare=0p65__s=0p9__cap=0p0025 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269896 | 0.807326 | -0.001498 | -0.000804 | -0.001374 |
| ppopt200_row_risk_winner__riskthr=0p64__segshare=0p45__s=0p9__cap=0p0025 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269896 | 0.807326 | -0.001498 | -0.000804 | -0.001374 |
| ppopt200_row_risk_winner__riskthr=0p4__segshare=0p45__s=0p9__cap=0p0015 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269903 | 0.807326 | -0.001492 | -0.000804 | -0.001374 |
| ppopt200_row_risk_winner__riskthr=0p56__segshare=0p65__s=0p9__cap=0p0025 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269897 | 0.807326 | -0.001498 | -0.000804 | -0.001374 |
| ppopt200_row_risk_winner__riskthr=0p56__segshare=0p45__s=0p9__cap=0p0025 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001374 |
| ppopt200_row_risk_winner__riskthr=0p48__segshare=0p45__s=0p7__cap=0p0015 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269903 | 0.807326 | -0.001492 | -0.000804 | -0.001374 |
| ppopt200_row_risk_winner__riskthr=0p4__segshare=0p45__s=0p7__cap=0p004 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269904 | 0.807326 | -0.001491 | -0.000804 | -0.001373 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p08__s=0p85__basecap=0p004__shrink=0p55 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269897 | 0.807326 | -0.001498 | -0.000804 | -0.001373 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p0__s=0p85__basecap=0p004__shrink=0p55 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269897 | 0.807326 | -0.001498 | -0.000804 | -0.001373 |
| ppopt200_row_risk_winner__riskthr=0p4__segshare=0p65__s=0p7__cap=0p0025 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269903 | 0.807326 | -0.001492 | -0.000804 | -0.001373 |
| ppopt203_global_plus_gate__global=0p18__gated=0p7__cap=0p0025 | PP-OPT203 | pp192_pp198_global_blend_plus_gate | 0.269897 | 0.807326 | -0.001498 | -0.000804 | -0.001373 |
| ppopt200_row_risk_winner__riskthr=0p48__segshare=0p85__s=0p9__cap=0p0025 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269897 | 0.807326 | -0.001498 | -0.000804 | -0.001373 |
| ppopt203_global_plus_gate__global=0p18__gated=0p7__cap=0p004 | PP-OPT203 | pp192_pp198_global_blend_plus_gate | 0.269896 | 0.807326 | -0.001499 | -0.000804 | -0.001373 |
| ppopt200_row_risk_winner__riskthr=0p4__segshare=0p85__s=0p9__cap=0p004 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269897 | 0.807326 | -0.001497 | -0.000804 | -0.001373 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p08__s=0p85__basecap=0p004__shrink=0p3 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269897 | 0.807326 | -0.001498 | -0.000804 | -0.001373 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p0__s=0p85__basecap=0p004__shrink=0p3 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269897 | 0.807326 | -0.001498 | -0.000804 | -0.001373 |
| ppopt202_consensus_winner__mode=conf70__s=0p85__cap=0p0015 | PP-OPT202 | pp192_pp198_consensus_winner_router | 0.269903 | 0.807326 | -0.001492 | -0.000804 | -0.001373 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p08__s=0p85__basecap=0p0025__shrink=0p3 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269897 | 0.807326 | -0.001497 | -0.000804 | -0.001373 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p0__s=0p85__basecap=0p0025__shrink=0p3 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269897 | 0.807326 | -0.001497 | -0.000804 | -0.001373 |
| ppopt202_consensus_winner__mode=conf70__s=0p85__cap=0p0025 | PP-OPT202 | pp192_pp198_consensus_winner_router | 0.269902 | 0.807326 | -0.001493 | -0.000804 | -0.001373 |
| ppopt202_consensus_winner__mode=conf70__s=0p85__cap=0p004 | PP-OPT202 | pp192_pp198_consensus_winner_router | 0.269902 | 0.807326 | -0.001493 | -0.000804 | -0.001373 |
| ppopt202_consensus_winner__mode=conf70__s=0p85__cap=0p006 | PP-OPT202 | pp192_pp198_consensus_winner_router | 0.269902 | 0.807326 | -0.001493 | -0.000804 | -0.001373 |
| ppopt203_global_plus_gate__global=0p24__gated=0p35__cap=0p0015 | PP-OPT203 | pp192_pp198_global_blend_plus_gate | 0.269903 | 0.807326 | -0.001492 | -0.000804 | -0.001373 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p08__s=1p0__basecap=0p0025__shrink=0p55 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269897 | 0.807326 | -0.001498 | -0.000804 | -0.001373 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p0__s=1p0__basecap=0p0025__shrink=0p55 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269897 | 0.807326 | -0.001498 | -0.000804 | -0.001373 |
| ppopt200_row_risk_winner__riskthr=0p4__segshare=0p45__s=0p7__cap=0p0025 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269905 | 0.807326 | -0.001490 | -0.000804 | -0.001373 |
| ppopt203_global_plus_gate__global=0p24__gated=0p35__cap=0p0025 | PP-OPT203 | pp192_pp198_global_blend_plus_gate | 0.269902 | 0.807326 | -0.001493 | -0.000804 | -0.001373 |
| ppopt203_global_plus_gate__global=0p24__gated=0p35__cap=0p004 | PP-OPT203 | pp192_pp198_global_blend_plus_gate | 0.269902 | 0.807326 | -0.001493 | -0.000804 | -0.001373 |
| ppopt203_global_plus_gate__global=0p08__gated=0p5__cap=0p0015 | PP-OPT203 | pp192_pp198_global_blend_plus_gate | 0.269903 | 0.807326 | -0.001492 | -0.000804 | -0.001372 |
| ppopt200_row_risk_winner__riskthr=0p4__segshare=0p65__s=0p7__cap=0p0015 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269904 | 0.807326 | -0.001491 | -0.000804 | -0.001372 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p08__s=0p85__basecap=0p006__shrink=0p3 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269897 | 0.807326 | -0.001498 | -0.000804 | -0.001372 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p08__s=0p85__basecap=0p006__shrink=0p55 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269897 | 0.807326 | -0.001498 | -0.000804 | -0.001372 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p0__s=0p85__basecap=0p006__shrink=0p3 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269897 | 0.807326 | -0.001498 | -0.000804 | -0.001372 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p0__s=0p85__basecap=0p006__shrink=0p55 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269897 | 0.807326 | -0.001498 | -0.000804 | -0.001372 |
| ppopt203_global_plus_gate__global=0p08__gated=0p5__cap=0p0025 | PP-OPT203 | pp192_pp198_global_blend_plus_gate | 0.269903 | 0.807326 | -0.001492 | -0.000804 | -0.001372 |
| ppopt203_global_plus_gate__global=0p08__gated=0p5__cap=0p004 | PP-OPT203 | pp192_pp198_global_blend_plus_gate | 0.269902 | 0.807326 | -0.001492 | -0.000804 | -0.001372 |
| ppopt200_row_risk_winner__riskthr=0p48__segshare=0p65__s=0p9__cap=0p0025 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269899 | 0.807326 | -0.001496 | -0.000804 | -0.001372 |
| ppopt200_row_risk_winner__riskthr=0p4__segshare=0p85__s=0p9__cap=0p0025 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001372 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p08__s=0p85__basecap=0p0025__shrink=0p55 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001372 |
| ppopt201_p95_guarded_winner__seg=price_conf__thr=0p0__s=0p85__basecap=0p0025__shrink=0p55 | PP-OPT201 | pp192_pp198_p95_guarded_winner_router | 0.269898 | 0.807326 | -0.001497 | -0.000804 | -0.001372 |
| ppopt200_row_risk_winner__riskthr=0p4__segshare=0p65__s=0p9__cap=0p004 | PP-OPT200 | pp192_pp198_row_risk_winner_router | 0.269899 | 0.807326 | -0.001496 | -0.000804 | -0.001372 |
| ppopt199_segment_winner__seg=price_conf__thr=0p08__s=0p55__cap=0p0015 | PP-OPT199 | pp192_pp198_segment_winner_router | 0.269903 | 0.807326 | -0.001491 | -0.000804 | -0.001371 |

## 선택 후보 반복 안정성
| candidate_label | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_vs_pp64_MAPE | fixed_test_delta_vs_pp64_p95_APE | avg_pp64_MAPE_win_rate | avg_pp64_p95_win_rate | replacement_score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_1p0__basecap_0p006__shrink_0p8__a3697a8167 | 0.269894 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018824 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p0__s_1p0__basecap_0p006__shrink_0p8__e8315af17a | 0.269894 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018824 |
| pp204_mape_pp192_pp198_winner_router_challenger | 0.269894 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018824 |
| pp204_operational_pp192_pp198_winner_router_challenger | 0.269894 | 0.807326 | -0.000671 | -0.000173 | 0.953846 | 0.747756 | -0.018824 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_1p0__basecap_0p004__shrink_0p3__1db8a7483e | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.953846 | 0.747756 | -0.018824 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p0__s_1p0__basecap_0p004__shrink_0p3__61141cebc2 | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.953846 | 0.747756 | -0.018824 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_1p0__basecap_0p004__shrink_0p55__032e87eab4 | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.953846 | 0.747756 | -0.018824 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p0__s_1p0__basecap_0p004__shrink_0p55__4ef9e9292c | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.953846 | 0.747756 | -0.018824 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_1p0__basecap_0p004__shrink_0p8__ed66df40ce | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.953526 | 0.747756 | -0.018811 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p0__s_1p0__basecap_0p004__shrink_0p8__0de8e476ce | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.953526 | 0.747756 | -0.018811 |
| candidate_ppopt199_segment_winner__seg_price_conf__thr_0p08__s_1p1__cap_0p0025__5e5dd8e54b | 0.269895 | 0.807326 | -0.000669 | -0.000173 | 0.953526 | 0.747756 | -0.018810 |
| candidate_ppopt199_segment_winner__seg_price_conf__thr_0p0__s_1p1__cap_0p0025__5d0807546f | 0.269895 | 0.807326 | -0.000669 | -0.000173 | 0.953526 | 0.747756 | -0.018810 |
| candidate_ppopt199_segment_winner__seg_price_conf__thr_0p16__s_1p1__cap_0p0025__8998fa92b3 | 0.269895 | 0.807326 | -0.000669 | -0.000173 | 0.953526 | 0.747756 | -0.018810 |
| candidate_ppopt199_segment_winner__seg_price_conf__thr_m0p08__s_1p1__cap_0p0025__b69352b389 | 0.269895 | 0.807326 | -0.000669 | -0.000173 | 0.953526 | 0.747756 | -0.018810 |
| candidate_ppopt199_segment_winner__seg_price_conf__thr_m0p18__s_1p1__cap_0p0025__4f559ba4d9 | 0.269895 | 0.807326 | -0.000669 | -0.000173 | 0.953526 | 0.747756 | -0.018810 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_0p85__basecap_0p006__shrink_0p8__f9ef1cbe77 | 0.269897 | 0.807326 | -0.000667 | -0.000173 | 0.953526 | 0.747756 | -0.018808 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p0__s_0p85__basecap_0p006__shrink_0p8__b8501f4d96 | 0.269897 | 0.807326 | -0.000667 | -0.000173 | 0.953526 | 0.747756 | -0.018808 |
| candidate_ppopt200_row_risk_winner__riskthr_0p56__segshare_0p45__s_0p9__cap_0p004__613894067c | 0.269897 | 0.807326 | -0.000667 | -0.000173 | 0.953526 | 0.749359 | -0.018808 |
| candidate_ppopt200_row_risk_winner__riskthr_0p48__segshare_0p65__s_0p9__cap_0p004__37e1895152 | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.953526 | 0.749679 | -0.018807 |
| candidate_ppopt200_row_risk_winner__riskthr_0p4__segshare_0p45__s_0p7__cap_0p004__6a659025d7 | 0.269904 | 0.807326 | -0.000660 | -0.000173 | 0.953526 | 0.750641 | -0.018801 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_1p0__basecap_0p006__shrink_0p55__59f16ad531 | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.953205 | 0.747756 | -0.018799 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p0__s_1p0__basecap_0p006__shrink_0p55__b5c4c40571 | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.953205 | 0.747756 | -0.018799 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_1p0__basecap_0p0025__shrink_0p3__f24a080876 | 0.269895 | 0.807326 | -0.000669 | -0.000173 | 0.953205 | 0.747756 | -0.018797 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p0__s_1p0__basecap_0p0025__shrink_0p3__317c03e460 | 0.269895 | 0.807326 | -0.000669 | -0.000173 | 0.953205 | 0.747756 | -0.018797 |
| candidate_ppopt199_segment_winner__seg_price_conf__thr_0p08__s_0p95__cap_0p0025__b870a5ae5b | 0.269896 | 0.807326 | -0.000669 | -0.000173 | 0.953205 | 0.747756 | -0.018797 |
| candidate_ppopt199_segment_winner__seg_price_conf__thr_0p0__s_0p95__cap_0p0025__88702722f0 | 0.269896 | 0.807326 | -0.000669 | -0.000173 | 0.953205 | 0.747756 | -0.018797 |
| candidate_ppopt199_segment_winner__seg_price_conf__thr_0p16__s_0p95__cap_0p0025__78b2cd8102 | 0.269896 | 0.807326 | -0.000669 | -0.000173 | 0.953205 | 0.747756 | -0.018797 |
| candidate_ppopt199_segment_winner__seg_price_conf__thr_m0p08__s_0p95__cap_0p0025__f752a2d2fa | 0.269896 | 0.807326 | -0.000669 | -0.000173 | 0.953205 | 0.747756 | -0.018797 |
| candidate_ppopt199_segment_winner__seg_price_conf__thr_m0p18__s_0p95__cap_0p0025__50b7cc5c60 | 0.269896 | 0.807326 | -0.000668 | -0.000173 | 0.953205 | 0.747756 | -0.018797 |
| candidate_ppopt203_global_plus_gate__global_0p24__gated_0p7__cap_0p0025__7b8cc8aa25 | 0.269896 | 0.807326 | -0.000668 | -0.000173 | 0.953205 | 0.747756 | -0.018797 |
| candidate_ppopt200_row_risk_winner__riskthr_0p64__segshare_0p85__s_0p9__cap_0p0025__3aec189e2f | 0.269896 | 0.807326 | -0.000668 | -0.000173 | 0.953205 | 0.747756 | -0.018796 |
| candidate_ppopt200_row_risk_winner__riskthr_0p64__segshare_0p65__s_0p9__cap_0p0025__02411a83c6 | 0.269896 | 0.807326 | -0.000668 | -0.000173 | 0.953205 | 0.747756 | -0.018796 |
| candidate_ppopt200_row_risk_winner__riskthr_0p64__segshare_0p45__s_0p9__cap_0p0025__6e18b3a78a | 0.269896 | 0.807326 | -0.000668 | -0.000173 | 0.953205 | 0.747756 | -0.018796 |
| candidate_ppopt200_row_risk_winner__riskthr_0p48__segshare_0p85__s_0p9__cap_0p004__ae38d9591d | 0.269897 | 0.807326 | -0.000667 | -0.000173 | 0.953205 | 0.748718 | -0.018796 |
| candidate_ppopt200_row_risk_winner__riskthr_0p56__segshare_0p65__s_0p9__cap_0p004__efdaaf05a8 | 0.269897 | 0.807326 | -0.000667 | -0.000173 | 0.953205 | 0.748718 | -0.018796 |
| candidate_ppopt200_row_risk_winner__riskthr_0p56__segshare_0p85__s_0p9__cap_0p0025__39f568304a | 0.269897 | 0.807326 | -0.000667 | -0.000173 | 0.953205 | 0.747756 | -0.018795 |
| candidate_ppopt203_global_plus_gate__global_0p18__gated_0p7__cap_0p0025__d18882197c | 0.269897 | 0.807326 | -0.000667 | -0.000173 | 0.953205 | 0.747756 | -0.018795 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_0p85__basecap_0p004__shrink_0p3__3558dc3589 | 0.269897 | 0.807326 | -0.000667 | -0.000173 | 0.953205 | 0.747756 | -0.018795 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p0__s_0p85__basecap_0p004__shrink_0p3__11fbcd4b1f | 0.269897 | 0.807326 | -0.000667 | -0.000173 | 0.953205 | 0.747756 | -0.018795 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_0p85__basecap_0p004__shrink_0p55__25952c247d | 0.269897 | 0.807326 | -0.000667 | -0.000173 | 0.953205 | 0.747756 | -0.018795 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p0__s_0p85__basecap_0p004__shrink_0p55__e7aea03d02 | 0.269897 | 0.807326 | -0.000667 | -0.000173 | 0.953205 | 0.747756 | -0.018795 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_0p85__basecap_0p004__shrink_0p8__26b5a60c87 | 0.269897 | 0.807326 | -0.000667 | -0.000173 | 0.953205 | 0.747756 | -0.018795 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p0__s_0p85__basecap_0p004__shrink_0p8__c02b107f56 | 0.269897 | 0.807326 | -0.000667 | -0.000173 | 0.953205 | 0.747756 | -0.018795 |
| candidate_ppopt200_row_risk_winner__riskthr_0p56__segshare_0p65__s_0p9__cap_0p0025__9a439a92c6 | 0.269897 | 0.807326 | -0.000667 | -0.000173 | 0.953205 | 0.748718 | -0.018795 |
| candidate_ppopt200_row_risk_winner__riskthr_0p48__segshare_0p85__s_0p9__cap_0p0025__567c72a651 | 0.269897 | 0.807326 | -0.000667 | -0.000173 | 0.953205 | 0.748718 | -0.018795 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_1p0__basecap_0p0025__shrink_0p55__5eba0cd643 | 0.269897 | 0.807326 | -0.000667 | -0.000173 | 0.953205 | 0.749679 | -0.018795 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p0__s_1p0__basecap_0p0025__shrink_0p55__a1ccd12022 | 0.269897 | 0.807326 | -0.000667 | -0.000173 | 0.953205 | 0.749679 | -0.018795 |
| candidate_ppopt200_row_risk_winner__riskthr_0p4__segshare_0p85__s_0p9__cap_0p004__f7d0ba31f2 | 0.269897 | 0.807326 | -0.000667 | -0.000173 | 0.953205 | 0.749679 | -0.018795 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_0p85__basecap_0p0025__shrink_0p3__838d79464f | 0.269897 | 0.807326 | -0.000667 | -0.000173 | 0.953205 | 0.747756 | -0.018795 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p0__s_0p85__basecap_0p0025__shrink_0p3__afe1a811d6 | 0.269897 | 0.807326 | -0.000667 | -0.000173 | 0.953205 | 0.747756 | -0.018795 |
| candidate_ppopt200_row_risk_winner__riskthr_0p56__segshare_0p45__s_0p9__cap_0p0025__ef90edfe64 | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.953205 | 0.749359 | -0.018795 |
| candidate_ppopt203_global_plus_gate__global_0p12__gated_0p7__cap_0p0025__0356ec8fac | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.953205 | 0.748718 | -0.018794 |
| candidate_ppopt200_row_risk_winner__riskthr_0p4__segshare_0p85__s_0p9__cap_0p0025__37b4ce8ca8 | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.953205 | 0.749679 | -0.018794 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_0p85__basecap_0p0025__shrink_0p55__da51a07bfe | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.953205 | 0.749679 | -0.018794 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p0__s_0p85__basecap_0p0025__shrink_0p55__c123cbe2d0 | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.953205 | 0.749679 | -0.018794 |
| candidate_ppopt200_row_risk_winner__riskthr_0p48__segshare_0p65__s_0p9__cap_0p0025__8d75b69265 | 0.269899 | 0.807326 | -0.000666 | -0.000173 | 0.953205 | 0.749679 | -0.018794 |
| candidate_ppopt200_row_risk_winner__riskthr_0p48__segshare_0p45__s_0p9__cap_0p004__9de30c4f54 | 0.269899 | 0.807326 | -0.000665 | -0.000173 | 0.953205 | 0.749679 | -0.018794 |
| pp192_operational_reference | 0.269914 | 0.807326 | -0.000650 | -0.000173 | 0.953526 | 0.750962 | -0.018791 |
| candidate_ppopt199_segment_winner__seg_price_conf__thr_0p08__s_1p1__cap_0p006__8882ce0c58 | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018786 |
| candidate_ppopt199_segment_winner__seg_price_conf__thr_0p0__s_1p1__cap_0p006__4d93fdedfc | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018786 |
| candidate_ppopt199_segment_winner__seg_price_conf__thr_0p16__s_1p1__cap_0p006__5271c0b095 | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018786 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_1p0__basecap_0p006__shrink_0p3__d5c1650c4d | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018786 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p0__s_1p0__basecap_0p006__shrink_0p3__3c578fa10d | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018786 |
| candidate_ppopt199_segment_winner__seg_price_conf__thr_m0p08__s_1p1__cap_0p006__e4e1c63dce | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018786 |
| candidate_ppopt199_segment_winner__seg_price_conf__thr_m0p18__s_1p1__cap_0p006__1956851241 | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018786 |
| pp198_operational_reference | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt199_segment_winner__seg_price_conf__thr_0p08__s_1p1__cap_0p004__4691d0a91c | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt199_segment_winner__seg_price_conf__thr_0p0__s_1p1__cap_0p004__b1005cefcc | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt199_segment_winner__seg_price_conf__thr_0p16__s_1p1__cap_0p004__d063e19a5d | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt199_segment_winner__seg_price_conf__thr_m0p08__s_1p1__cap_0p004__ef4076359d | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt199_segment_winner__seg_price_conf__thr_m0p18__s_1p1__cap_0p004__bd3f2a4848 | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt200_row_risk_winner__riskthr_0p64__segshare_0p65__s_0p9__cap_0p004__3b6cca9aed | 0.269896 | 0.807326 | -0.000668 | -0.000173 | 0.952885 | 0.747756 | -0.018783 |
| candidate_ppopt200_row_risk_winner__riskthr_0p64__segshare_0p45__s_0p9__cap_0p004__71f8058ec0 | 0.269896 | 0.807326 | -0.000668 | -0.000173 | 0.952885 | 0.747756 | -0.018783 |
| candidate_ppopt200_row_risk_winner__riskthr_0p56__segshare_0p85__s_0p9__cap_0p004__50082cd6ac | 0.269896 | 0.807326 | -0.000668 | -0.000173 | 0.952885 | 0.747756 | -0.018783 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_0p85__basecap_0p006__shrink_0p3__8c0e9cf1ea | 0.269897 | 0.807326 | -0.000667 | -0.000173 | 0.952885 | 0.747756 | -0.018782 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_0p85__basecap_0p006__shrink_0p55__3963534549 | 0.269897 | 0.807326 | -0.000667 | -0.000173 | 0.952885 | 0.747756 | -0.018782 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p0__s_0p85__basecap_0p006__shrink_0p3__282649b1ef | 0.269897 | 0.807326 | -0.000667 | -0.000173 | 0.952885 | 0.747756 | -0.018782 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p0__s_0p85__basecap_0p006__shrink_0p55__b287b59a38 | 0.269897 | 0.807326 | -0.000667 | -0.000173 | 0.952885 | 0.747756 | -0.018782 |
| candidate_ppopt203_global_plus_gate__global_0p08__gated_0p7__cap_0p004__f86f1236ba | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952885 | 0.749679 | -0.018781 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_1p0__basecap_0p0025__shrink_0p8__651efd45c9 | 0.269900 | 0.807326 | -0.000664 | -0.000173 | 0.952885 | 0.749679 | -0.018779 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p0__s_1p0__basecap_0p0025__shrink_0p8__145de72a2a | 0.269900 | 0.807326 | -0.000664 | -0.000173 | 0.952885 | 0.749679 | -0.018779 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_0p85__basecap_0p0025__shrink_0p8__d41c9feb9d | 0.269901 | 0.807326 | -0.000663 | -0.000173 | 0.952885 | 0.749679 | -0.018779 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p0__s_0p85__basecap_0p0025__shrink_0p8__112efd4214 | 0.269901 | 0.807326 | -0.000663 | -0.000173 | 0.952885 | 0.749679 | -0.018779 |
| candidate_ppopt200_row_risk_winner__riskthr_0p4__segshare_0p45__s_0p9__cap_0p004__f775b0818e | 0.269901 | 0.807326 | -0.000663 | -0.000173 | 0.952885 | 0.750000 | -0.018778 |
| candidate_ppopt200_row_risk_winner__riskthr_0p48__segshare_0p65__s_0p7__cap_0p004__3e4a91a6a2 | 0.269901 | 0.807326 | -0.000663 | -0.000173 | 0.952885 | 0.749679 | -0.018778 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_0p65__basecap_0p0025__shrink_0p8__c36d589c7d | 0.269902 | 0.807326 | -0.000662 | -0.000173 | 0.952885 | 0.749679 | -0.018778 |
| candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p0__s_0p65__basecap_0p0025__shrink_0p8__cdb2d90e97 | 0.269902 | 0.807326 | -0.000662 | -0.000173 | 0.952885 | 0.749679 | -0.018778 |
| candidate_ppopt200_row_risk_winner__riskthr_0p48__segshare_0p65__s_0p7__cap_0p0025__19b93e0d41 | 0.269902 | 0.807326 | -0.000662 | -0.000173 | 0.952885 | 0.749679 | -0.018778 |
| candidate_ppopt200_row_risk_winner__riskthr_0p48__segshare_0p45__s_0p7__cap_0p004__11e26659b7 | 0.269902 | 0.807326 | -0.000662 | -0.000173 | 0.952885 | 0.750000 | -0.018777 |
| candidate_ppopt200_row_risk_winner__riskthr_0p48__segshare_0p65__s_0p7__cap_0p0015__61155e9318 | 0.269902 | 0.807326 | -0.000662 | -0.000173 | 0.952885 | 0.749679 | -0.018777 |
| candidate_ppopt200_row_risk_winner__riskthr_0p4__segshare_0p65__s_0p7__cap_0p004__be27f85999 | 0.269903 | 0.807326 | -0.000661 | -0.000173 | 0.952885 | 0.750000 | -0.018777 |
| candidate_ppopt200_row_risk_winner__riskthr_0p48__segshare_0p45__s_0p7__cap_0p0025__8add4afd36 | 0.269903 | 0.807326 | -0.000661 | -0.000173 | 0.952885 | 0.750000 | -0.018777 |
| candidate_ppopt200_row_risk_winner__riskthr_0p4__segshare_0p45__s_0p9__cap_0p0025__cdd140a3c2 | 0.269903 | 0.807326 | -0.000661 | -0.000173 | 0.952885 | 0.750000 | -0.018777 |
| candidate_ppopt200_row_risk_winner__riskthr_0p48__segshare_0p45__s_0p7__cap_0p0015__62a8d11545 | 0.269903 | 0.807326 | -0.000661 | -0.000173 | 0.952885 | 0.750000 | -0.018776 |
| candidate_ppopt200_row_risk_winner__riskthr_0p4__segshare_0p65__s_0p7__cap_0p0025__248d8e9c15 | 0.269903 | 0.807326 | -0.000661 | -0.000173 | 0.952885 | 0.750000 | -0.018776 |
| candidate_ppopt200_row_risk_winner__riskthr_0p4__segshare_0p45__s_0p9__cap_0p0015__473e609215 | 0.269903 | 0.807326 | -0.000661 | -0.000173 | 0.952885 | 0.750000 | -0.018776 |
| candidate_ppopt199_segment_winner__seg_price_conf__thr_0p08__s_0p95__cap_0p006__b9b57ebfa8 | 0.269895 | 0.807326 | -0.000669 | -0.000173 | 0.952564 | 0.747756 | -0.018772 |
| candidate_ppopt199_segment_winner__seg_price_conf__thr_0p0__s_0p95__cap_0p006__ac1f3f085a | 0.269895 | 0.807326 | -0.000669 | -0.000173 | 0.952564 | 0.747756 | -0.018772 |
| candidate_ppopt199_segment_winner__seg_price_conf__thr_0p16__s_0p95__cap_0p006__61280f7130 | 0.269895 | 0.807326 | -0.000669 | -0.000173 | 0.952564 | 0.747756 | -0.018772 |
| candidate_ppopt199_segment_winner__seg_price_conf__thr_m0p08__s_0p95__cap_0p006__0b0edbd4d5 | 0.269895 | 0.807326 | -0.000669 | -0.000173 | 0.952564 | 0.747756 | -0.018772 |
| candidate_ppopt199_segment_winner__seg_price_conf__thr_m0p18__s_0p95__cap_0p006__84550f02fc | 0.269895 | 0.807326 | -0.000669 | -0.000173 | 0.952564 | 0.747756 | -0.018772 |
| candidate_ppopt199_segment_winner__seg_price_conf__thr_0p08__s_0p95__cap_0p004__0b83068761 | 0.269895 | 0.807326 | -0.000669 | -0.000173 | 0.952564 | 0.747756 | -0.018772 |
| candidate_ppopt199_segment_winner__seg_price_conf__thr_0p0__s_0p95__cap_0p004__9db3803988 | 0.269895 | 0.807326 | -0.000669 | -0.000173 | 0.952564 | 0.747756 | -0.018772 |
| candidate_ppopt199_segment_winner__seg_price_conf__thr_0p16__s_0p95__cap_0p004__67cd30985c | 0.269895 | 0.807326 | -0.000669 | -0.000173 | 0.952564 | 0.747756 | -0.018772 |
| candidate_ppopt199_segment_winner__seg_price_conf__thr_m0p08__s_0p95__cap_0p004__7f639e1c22 | 0.269895 | 0.807326 | -0.000669 | -0.000173 | 0.952564 | 0.747756 | -0.018772 |
| candidate_ppopt199_segment_winner__seg_price_conf__thr_m0p18__s_0p95__cap_0p004__68b2a65348 | 0.269895 | 0.807326 | -0.000669 | -0.000173 | 0.952564 | 0.747756 | -0.018772 |
| candidate_ppopt203_global_plus_gate__global_0p24__gated_0p7__cap_0p004__cd79a0a2ac | 0.269895 | 0.807326 | -0.000669 | -0.000173 | 0.952564 | 0.747756 | -0.018771 |
| candidate_ppopt200_row_risk_winner__riskthr_0p64__segshare_0p85__s_0p9__cap_0p004__502168175a | 0.269896 | 0.807326 | -0.000668 | -0.000173 | 0.952564 | 0.747756 | -0.018771 |
| candidate_ppopt203_global_plus_gate__global_0p18__gated_0p7__cap_0p004__63836be505 | 0.269896 | 0.807326 | -0.000668 | -0.000173 | 0.952564 | 0.747756 | -0.018770 |
| candidate_ppopt203_global_plus_gate__global_0p12__gated_0p7__cap_0p004__71424ea579 | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952564 | 0.748718 | -0.018769 |
| pp180_operational_reference | 0.269933 | 0.807326 | -0.000631 | -0.000173 | 0.952244 | 0.754487 | -0.018721 |
| pp192_p95_guarded_reference | 0.269949 | 0.807255 | -0.000615 | -0.000244 | 0.950962 | 0.751603 | -0.018653 |
| pp198_p95_guarded_reference | 0.269949 | 0.807255 | -0.000615 | -0.000244 | 0.950962 | 0.751603 | -0.018653 |
| pp204_p95_guarded_pp192_pp198_winner_router_challenger | 0.269949 | 0.807255 | -0.000615 | -0.000244 | 0.950962 | 0.751603 | -0.018653 |
| pp186_operational_reference | 0.269961 | 0.807231 | -0.000603 | -0.000268 | 0.949359 | 0.598718 | -0.018578 |
| pp172_operational_reference | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.947115 | 0.605449 | -0.018451 |
| pp166_operational_reference | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.946795 | 0.601923 | -0.018439 |
| pp148_operational_reference | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| pp126_operational_reference | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| pp70_refinement_candidate | 0.270561 | 0.807490 | -0.000003 | -0.000009 | 0.786859 | 0.398077 | -0.011477 |
| pp148_p95_reference | 0.270269 | 0.805949 | -0.000295 | -0.001549 | 0.598397 | 0.500962 | -0.004079 |
| pp166_p95_reference | 0.270269 | 0.805949 | -0.000295 | -0.001549 | 0.598397 | 0.500962 | -0.004079 |
| pp172_p95_reference | 0.270269 | 0.805949 | -0.000295 | -0.001549 | 0.598397 | 0.500962 | -0.004079 |
| pp180_p95_reference | 0.270269 | 0.805949 | -0.000295 | -0.001549 | 0.598397 | 0.500962 | -0.004079 |
| pp186_p95_reference | 0.270269 | 0.805949 | -0.000295 | -0.001549 | 0.598397 | 0.500962 | -0.004079 |
| pp192_p95_extreme_reference | 0.270269 | 0.805949 | -0.000295 | -0.001549 | 0.598397 | 0.500962 | -0.004079 |
| pp198_p95_extreme_reference | 0.270269 | 0.805949 | -0.000295 | -0.001549 | 0.598397 | 0.500962 | -0.004079 |
| pp204_p95_extreme_pp192_pp198_winner_router_challenger | 0.270269 | 0.805949 | -0.000295 | -0.001549 | 0.598397 | 0.500962 | -0.004079 |
| pp64_current_best | 0.270564 | 0.807499 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.020000 |
| incumbent_pp7 | 0.271395 | 0.808130 | 0.000831 | 0.000631 | 0.002244 | 0.450641 | 0.022238 |
| hcoef_stable_source | 0.272989 | 0.806366 | 0.002425 | -0.001133 | 0.002244 | 0.403526 | 0.025195 |
| current_70_30 | 0.274799 | 0.833074 | 0.004235 | 0.025575 | 0.000962 | 0.254167 | 0.048393 |

## 실행 설정
```json
{
  "experiment_id": "PP-OPT199-204",
  "experiment_slug": "PP-OPT199_204_warm_pp192_pp198_winner_router",
  "created_at": "2026-06-10T10:50:28",
  "base_candidate": "hcoef_stable",
  "previous_experiment": "experiments/track6/PP-OPT193_198_warm_segment_outcome_router_refinement",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 826,
  "prediction_rows": 930076,
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
    "pp198_p95_extreme": "ppopt198_p95_extreme_segment_router_refinement__source=reference_pp148_p95"
  },
  "selection_decision": {
    "operational_label": "candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_1p0__basecap_0p006__shrink_0p8__a3697a8167",
    "operational_candidate": "ppopt201_p95_guarded_winner__seg=price_conf__thr=0p08__s=1p0__basecap=0p006__shrink=0p8",
    "operational_fixed_test_MAPE": 0.26989352127116634,
    "operational_fixed_test_p95_APE": 0.8073255046591389,
    "operational_delta_vs_pp64_MAPE": -0.0006705206444940215,
    "operational_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "operational_delta_vs_pp126_MAPE": -0.0002208754786854894,
    "operational_delta_vs_pp126_p95_APE": -0.0001645562387090349,
    "operational_delta_vs_pp148_MAPE": -0.0002464671014130726,
    "operational_delta_vs_pp148_p95_APE": 9.45931204405781e-05,
    "operational_delta_vs_pp166_MAPE": -0.00010346439407227237,
    "operational_delta_vs_pp166_p95_APE": 9.45931204405781e-05,
    "operational_delta_vs_pp172_MAPE": -0.00010389338998423314,
    "operational_delta_vs_pp172_p95_APE": 9.45931204405781e-05,
    "operational_delta_vs_pp180_MAPE": -3.910531662199013e-05,
    "operational_delta_vs_pp180_p95_APE": 0.0,
    "operational_delta_vs_pp186_MAPE": -6.711259506025913e-05,
    "operational_delta_vs_pp186_p95_APE": 9.45931204405781e-05,
    "operational_delta_vs_pp192_MAPE": -2.083287358345398e-05,
    "operational_delta_vs_pp192_p95_APE": 0.0,
    "operational_delta_vs_pp198_MAPE": -4.877470538011686e-07,
    "operational_delta_vs_pp198_p95_APE": 0.0,
    "operational_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "operational_avg_pp64_p95_win_rate": 0.7477564102564102,
    "operational_replacement_score": -0.018824366798340177,
    "mape_challenger_label": "candidate_ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_1p0__basecap_0p006__shrink_0p8__a3697a8167",
    "mape_challenger_candidate": "ppopt201_p95_guarded_winner__seg=price_conf__thr=0p08__s=1p0__basecap=0p006__shrink=0p8",
    "mape_challenger_fixed_test_MAPE": 0.26989352127116634,
    "mape_challenger_fixed_test_p95_APE": 0.8073255046591389,
    "mape_challenger_delta_vs_pp64_MAPE": -0.0006705206444940215,
    "mape_challenger_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "mape_challenger_delta_vs_pp126_MAPE": -0.0002208754786854894,
    "mape_challenger_delta_vs_pp126_p95_APE": -0.0001645562387090349,
    "mape_challenger_delta_vs_pp148_MAPE": -0.0002464671014130726,
    "mape_challenger_delta_vs_pp148_p95_APE": 9.45931204405781e-05,
    "mape_challenger_delta_vs_pp166_MAPE": -0.00010346439407227237,
    "mape_challenger_delta_vs_pp166_p95_APE": 9.45931204405781e-05,
    "mape_challenger_delta_vs_pp172_MAPE": -0.00010389338998423314,
    "mape_challenger_delta_vs_pp172_p95_APE": 9.45931204405781e-05,
    "mape_challenger_delta_vs_pp180_MAPE": -3.910531662199013e-05,
    "mape_challenger_delta_vs_pp180_p95_APE": 0.0,
    "mape_challenger_delta_vs_pp186_MAPE": -6.711259506025913e-05,
    "mape_challenger_delta_vs_pp186_p95_APE": 9.45931204405781e-05,
    "mape_challenger_delta_vs_pp192_MAPE": -2.083287358345398e-05,
    "mape_challenger_delta_vs_pp192_p95_APE": 0.0,
    "mape_challenger_delta_vs_pp198_MAPE": -4.877470538011686e-07,
    "mape_challenger_delta_vs_pp198_p95_APE": 0.0,
    "mape_challenger_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "mape_challenger_avg_pp64_p95_win_rate": 0.7477564102564102,
    "mape_challenger_replacement_score": -0.018824366798340177,
    "p95_guarded_label": "pp192_p95_guarded_reference",
    "p95_guarded_candidate": "ppopt192_p95_guarded_pp180_pp186_risk_router__source=ppopt187_hard_risk_router__risk_uncertainty__mode_hard__thr_0p78__w_0p06__s_0p75",
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
    "p95_guarded_delta_vs_pp180_MAPE": 1.6574554299320088e-05,
    "p95_guarded_delta_vs_pp180_p95_APE": -7.093082770415204e-05,
    "p95_guarded_delta_vs_pp186_MAPE": -1.1432724138948913e-05,
    "p95_guarded_delta_vs_pp186_p95_APE": 2.366229273642606e-05,
    "p95_guarded_delta_vs_pp192_MAPE": 3.4846997337856234e-05,
    "p95_guarded_delta_vs_pp192_p95_APE": -7.093082770415204e-05,
    "p95_guarded_delta_vs_pp198_MAPE": 5.5192123867509046e-05,
    "p95_guarded_delta_vs_pp198_p95_APE": -7.093082770415204e-05,
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
    "p95_extreme_delta_vs_pp180_MAPE": 0.0003362993213196219,
    "p95_extreme_delta_vs_pp180_p95_APE": -0.0013761288369714686,
    "p95_extreme_delta_vs_pp186_MAPE": 0.0003082920428813529,
    "p95_extreme_delta_vs_pp186_p95_APE": -0.0012815357165308905,
    "p95_extreme_delta_vs_pp192_MAPE": 0.00035457176435815807,
    "p95_extreme_delta_vs_pp192_p95_APE": -0.0013761288369714686,
    "p95_extreme_delta_vs_pp198_MAPE": 0.0003749168908878109,
    "p95_extreme_delta_vs_pp198_p95_APE": -0.0013761288369714686,
    "p95_extreme_avg_pp64_MAPE_win_rate": 0.5983974358974359,
    "p95_extreme_avg_pp64_p95_win_rate": 0.5009615384615385,
    "p95_extreme_replacement_score": -0.0040792899192624915,
    "operational_protocol_candidate": "ppopt204_operational_pp192_pp198_winner_router__source=ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_1p0__basecap_0p006__shrink_0p8",
    "mape_challenger_protocol_candidate": "ppopt204_mape_challenger_pp192_pp198_winner_router__source=ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_1p0__basecap_0p006__shrink_0p8",
    "p95_guarded_protocol_candidate": "ppopt204_p95_guarded_pp192_pp198_winner_router__source=ppopt192_p95_guarded_pp180_pp186_risk_router__source_ppopt187_hard_risk_router__risk_uncertainty__mode_hard__thr_0p78__w",
    "p95_extreme_protocol_candidate": "ppopt204_p95_extreme_pp192_pp198_winner_router__source=reference_pp148_p95"
  },
  "items": [
    {
      "item_id": "PP-OPT199",
      "priority": "1",
      "title": "segment winner router",
      "description": "validation에서 PP198이 PP192보다 이긴 segment만 PP198 쪽으로 이동."
    },
    {
      "item_id": "PP-OPT200",
      "priority": "2",
      "title": "row risk winner router",
      "description": "PP192/PP198 gap, 불확실성, segment win score를 같이 써서 row 단위로 이동."
    },
    {
      "item_id": "PP-OPT201",
      "priority": "3",
      "title": "p95 guarded winner router",
      "description": "PP198 이동을 허용하되 segment p95 손상이 있는 구간은 동적으로 cap 축소."
    },
    {
      "item_id": "PP-OPT202",
      "priority": "4",
      "title": "consensus winner router",
      "description": "price-confidence와 price-gap segment가 동시에 PP198 우위를 보일 때만 이동."
    },
    {
      "item_id": "PP-OPT203",
      "priority": "5",
      "title": "small global blend plus winner gate",
      "description": "PP198을 아주 약하게 전역 반영하고 winner gate 구간에서만 추가 이동."
    },
    {
      "item_id": "PP-OPT204",
      "priority": "6",
      "title": "final PP192/PP198 winner-router decision",
      "description": "PP192, PP198, 신규 winner-router 후보를 fixed/repeated 기준으로 비교해 선택."
    }
  ],
  "router_formula": {
    "base": "PP192 operational log price",
    "mape_candidate": "PP198 MAPE challenger log price",
    "final": "PP192 log price + clip((PP198 log price - PP192 log price) * winner_weight, row_cap)",
    "winner_inputs": [
      "validation segment PP198-vs-PP192 APE gain",
      "validation segment PP198-vs-PP192 p95 delta",
      "row uncertainty risk",
      "abs(PP198 log price - PP192 log price)"
    ]
  }
}
```