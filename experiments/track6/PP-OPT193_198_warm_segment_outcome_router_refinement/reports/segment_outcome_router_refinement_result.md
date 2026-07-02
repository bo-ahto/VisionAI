# PP-OPT193~198 Warm segment outcome router refinement 결과

- 작성일: 2026-06-10 10:40
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 목적: PP192 segment outcome router 주변 파라미터를 좁게 재탐색
- 결론: 운영 후보 fixed test MAPE 0.269894, p95 0.807326. PP192 대비 MAPE -0.000020, p95 +0.000000. p95 후보 MAPE 0.269949, p95 0.807255.

## 주요 후보 test 비교
| candidate | family | item_id | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt198_operational_segment_router_refinement__source=ppopt194_price_conf_refine__scorethr_0p02__mix_0p25__s_1p05__cap_0p006 | segment_router_refinement_operational_selection | PP-OPT198 | 0.140975 | 0.269894 | 0.807326 | 0.397455 | -0.001501 | -0.000804 |
| ppopt192_operational_pp180_pp186_risk_router__source=ppopt189_segment_router__seg_price_gap__scorethr_0p02__mix_0p75__s_0p95__cap_0p0025 | reference_prior | REFERENCE | 0.140975 | 0.269914 | 0.807326 | 0.397468 | -0.001481 | -0.000804 |
| ppopt180_operational_basis_generation_challenger__source=ppopt174_direct_basis__source_stack_huber_weighted__thr_0p08__s_0p3__cap_0p004 | reference_prior | REFERENCE | 0.140975 | 0.269933 | 0.807326 | 0.397475 | -0.001462 | -0.000804 |
| ppopt192_p95_guarded_pp180_pp186_risk_router__source=ppopt187_hard_risk_router__risk_uncertainty__mode_hard__thr_0p78__w_0p06__s_0p75 | reference_prior | REFERENCE | 0.140094 | 0.269949 | 0.807255 | 0.397482 | -0.001446 | -0.000875 |
| ppopt198_p95_guarded_segment_router_refinement__source=ppopt192_p95_guarded_pp180_pp186_risk_router__source_ppopt187_hard_risk_router__risk_uncertainty__mode_hard__thr_0p78__w | segment_router_refinement_p95_guarded_selection | PP-OPT198 | 0.140094 | 0.269949 | 0.807255 | 0.397482 | -0.001446 | -0.000875 |
| ppopt186_operational_huber_basis_p95_guard__source=ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p04__s_0p42__cap_0p0045 | reference_prior | REFERENCE | 0.139801 | 0.269961 | 0.807231 | 0.397497 | -0.001434 | -0.000899 |
| ppopt172_operational_pp166_tail_calibration_challenger__source=ppopt169_segment_router__source_pp162_p95_gate__seg_price_conf__thr_m0p04__s_0p5__cap_0p004 | reference_prior | REFERENCE | 0.139801 | 0.269997 | 0.807231 | 0.397516 | -0.001397 | -0.000899 |
| reference_pp126_operational | reference_prior | REFERENCE | 0.136320 | 0.270114 | 0.807490 | 0.397588 | -0.001280 | -0.000640 |
| reference_pp148_operational | reference_prior | REFERENCE | 0.139801 | 0.270140 | 0.807231 | 0.397525 | -0.001255 | -0.000899 |
| reference_pp148_p95 | reference_prior | REFERENCE | 0.141036 | 0.270269 | 0.805949 | 0.397421 | -0.001126 | -0.002181 |
| ppopt198_p95_extreme_segment_router_refinement__source=reference_pp148_p95 | segment_router_refinement_p95_extreme_selection | PP-OPT198 | 0.141036 | 0.270269 | 0.805949 | 0.397421 | -0.001126 | -0.002181 |
| reference_pp64_current_best | reference_prior | REFERENCE | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | p95_test_MAPE | p95_test_p95_APE | operational_pass_vs_incumbent | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | final segment router decision | 3 | 0.269949 | 0.807255 | 0.270269 | 0.805949 | False | segment_router_refinement_p95_guarded_selection | ppopt198_p95_guarded_segment_router_refinement__source=ppopt192_p95_guarded_pp180_pp186_risk_router__source_ppopt187_hard_risk_router__risk_uncertainty__mode_hard__thr_0p78__w |
| 2 | price-confidence segment router refinement | 288 | 0.269898 | 0.807320 | 0.269898 | 0.807320 | False | segment_price_conf_refinement | ppopt194_price_conf_refine__scorethr=0p16__mix=0p25__s=1p05__cap=0p006 |
| 4 | p95-constrained dynamic cap router | 108 | 0.269896 | 0.807323 | 0.269896 | 0.807323 | False | segment_dynamic_cap_router | ppopt196_dynamic_cap__seg=price_conf__scorethr=0p12__mix=0p35__s=1p05__basecap=0p006__shrink=0p3 |
| 1 | price-gap segment router refinement | 240 | 0.269914 | 0.807319 | 0.269914 | 0.807319 | False | segment_price_gap_refinement | ppopt193_price_gap_refine__scorethr=0p12__mix=0p85__s=1p05__cap=0p0035 |
| 3 | price-gap and confidence combined router | 108 | 0.269904 | 0.807324 | 0.269901 | 0.807324 | False | segment_gap_conf_combined_router | ppopt195_gap_conf_combined__gapthr=0p02__confthr=0p12__gapshare=0p3__s=0p95__cap=0p004 |
| 5 | segment consensus router | 36 | 0.269904 | 0.807324 | 0.269901 | 0.807324 | False | segment_consensus_router | ppopt197_consensus__mode=mean__s=1p05__cap=0p004 |

## 탐색 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt198_p95_guarded_segment_router_refinement__source=ppopt192_p95_guarded_pp180_pp186_risk_router__source_ppopt187_hard_risk_router__risk_uncertainty__mode_hard__thr_0p78__w | PP-OPT198 | segment_router_refinement_p95_guarded_selection | 0.269949 | 0.807255 | -0.001446 | -0.000875 | -0.001537 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p25__s=1p05__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269898 | 0.807320 | -0.001497 | -0.000810 | -0.001392 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p25__s=1p05__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269898 | 0.807320 | -0.001497 | -0.000810 | -0.001392 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p35__s=1p05__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269898 | 0.807320 | -0.001497 | -0.000810 | -0.001392 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p35__s=1p05__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269898 | 0.807320 | -0.001497 | -0.000810 | -0.001392 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p45__s=1p05__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269898 | 0.807320 | -0.001497 | -0.000810 | -0.001392 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p45__s=1p05__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269898 | 0.807320 | -0.001497 | -0.000810 | -0.001392 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p55__s=1p05__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269898 | 0.807320 | -0.001497 | -0.000810 | -0.001392 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p55__s=1p05__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269898 | 0.807320 | -0.001497 | -0.000810 | -0.001392 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p25__s=0p95__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269901 | 0.807321 | -0.001494 | -0.000809 | -0.001384 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p25__s=0p95__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269901 | 0.807321 | -0.001494 | -0.000809 | -0.001384 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p35__s=0p95__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269901 | 0.807321 | -0.001494 | -0.000809 | -0.001384 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p35__s=0p95__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269901 | 0.807321 | -0.001494 | -0.000809 | -0.001384 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p45__s=0p95__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269901 | 0.807321 | -0.001494 | -0.000809 | -0.001384 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p45__s=0p95__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269901 | 0.807321 | -0.001494 | -0.000809 | -0.001384 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p55__s=0p95__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269901 | 0.807321 | -0.001494 | -0.000809 | -0.001384 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p55__s=0p95__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269901 | 0.807321 | -0.001494 | -0.000809 | -0.001384 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p25__s=1p05__cap=0p004 | PP-OPT194 | segment_price_conf_refinement | 0.269902 | 0.807320 | -0.001493 | -0.000810 | -0.001384 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p35__s=1p05__cap=0p004 | PP-OPT194 | segment_price_conf_refinement | 0.269902 | 0.807320 | -0.001493 | -0.000810 | -0.001384 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p45__s=1p05__cap=0p004 | PP-OPT194 | segment_price_conf_refinement | 0.269902 | 0.807320 | -0.001493 | -0.000810 | -0.001384 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p55__s=1p05__cap=0p004 | PP-OPT194 | segment_price_conf_refinement | 0.269902 | 0.807320 | -0.001493 | -0.000810 | -0.001384 |
| ppopt194_price_conf_refine__scorethr=0p12__mix=0p25__s=1p05__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269896 | 0.807323 | -0.001499 | -0.000807 | -0.001383 |
| ppopt194_price_conf_refine__scorethr=0p12__mix=0p25__s=1p05__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269896 | 0.807323 | -0.001499 | -0.000807 | -0.001383 |
| ppopt194_price_conf_refine__scorethr=0p12__mix=0p35__s=1p05__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269896 | 0.807323 | -0.001499 | -0.000807 | -0.001383 |
| ppopt194_price_conf_refine__scorethr=0p12__mix=0p35__s=1p05__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269896 | 0.807323 | -0.001499 | -0.000807 | -0.001383 |
| ppopt194_price_conf_refine__scorethr=0p12__mix=0p45__s=1p05__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269896 | 0.807323 | -0.001499 | -0.000807 | -0.001383 |
| ppopt194_price_conf_refine__scorethr=0p12__mix=0p45__s=1p05__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269896 | 0.807323 | -0.001499 | -0.000807 | -0.001383 |
| ppopt194_price_conf_refine__scorethr=0p12__mix=0p55__s=1p05__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269896 | 0.807323 | -0.001499 | -0.000807 | -0.001383 |
| ppopt194_price_conf_refine__scorethr=0p12__mix=0p55__s=1p05__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269896 | 0.807323 | -0.001499 | -0.000807 | -0.001383 |
| ppopt196_dynamic_cap__seg=price_conf__scorethr=0p12__mix=0p35__s=1p05__basecap=0p006__shrink=0p3 | PP-OPT196 | segment_dynamic_cap_router | 0.269896 | 0.807323 | -0.001499 | -0.000807 | -0.001383 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p25__s=0p95__cap=0p004 | PP-OPT194 | segment_price_conf_refinement | 0.269903 | 0.807321 | -0.001492 | -0.000809 | -0.001381 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p35__s=0p95__cap=0p004 | PP-OPT194 | segment_price_conf_refinement | 0.269903 | 0.807321 | -0.001492 | -0.000809 | -0.001381 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p45__s=0p95__cap=0p004 | PP-OPT194 | segment_price_conf_refinement | 0.269903 | 0.807321 | -0.001492 | -0.000809 | -0.001381 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p55__s=0p95__cap=0p004 | PP-OPT194 | segment_price_conf_refinement | 0.269903 | 0.807321 | -0.001492 | -0.000809 | -0.001381 |
| ppopt196_dynamic_cap__seg=price_conf__scorethr=0p12__mix=0p35__s=1p05__basecap=0p006__shrink=0p55 | PP-OPT196 | segment_dynamic_cap_router | 0.269898 | 0.807323 | -0.001497 | -0.000807 | -0.001380 |
| ppopt196_dynamic_cap__seg=price_conf__scorethr=0p12__mix=0p35__s=1p05__basecap=0p006__shrink=0p8 | PP-OPT196 | segment_dynamic_cap_router | 0.269903 | 0.807323 | -0.001492 | -0.000807 | -0.001380 |
| ppopt196_dynamic_cap__seg=price_conf__scorethr=0p12__mix=0p35__s=0p95__basecap=0p006__shrink=0p8 | PP-OPT196 | segment_dynamic_cap_router | 0.269903 | 0.807323 | -0.001492 | -0.000806 | -0.001378 |
| ppopt193_price_gap_refine__scorethr=0p12__mix=0p85__s=1p05__cap=0p0035 | PP-OPT193 | segment_price_gap_refinement | 0.269914 | 0.807319 | -0.001480 | -0.000811 | -0.001378 |
| ppopt193_price_gap_refine__scorethr=0p12__mix=0p85__s=1p05__cap=0p005 | PP-OPT193 | segment_price_gap_refinement | 0.269914 | 0.807319 | -0.001480 | -0.000811 | -0.001378 |
| ppopt193_price_gap_refine__scorethr=0p12__mix=0p8__s=1p05__cap=0p0035 | PP-OPT193 | segment_price_gap_refinement | 0.269915 | 0.807319 | -0.001480 | -0.000811 | -0.001377 |
| ppopt193_price_gap_refine__scorethr=0p12__mix=0p8__s=1p05__cap=0p005 | PP-OPT193 | segment_price_gap_refinement | 0.269915 | 0.807319 | -0.001480 | -0.000811 | -0.001377 |
| ppopt196_dynamic_cap__seg=price_conf__scorethr=0p12__mix=0p35__s=0p85__basecap=0p006__shrink=0p8 | PP-OPT196 | segment_dynamic_cap_router | 0.269904 | 0.807324 | -0.001491 | -0.000806 | -0.001377 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p25__s=0p85__cap=0p004 | PP-OPT194 | segment_price_conf_refinement | 0.269904 | 0.807321 | -0.001490 | -0.000809 | -0.001377 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p25__s=0p85__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269904 | 0.807321 | -0.001490 | -0.000809 | -0.001377 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p25__s=0p85__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269904 | 0.807321 | -0.001490 | -0.000809 | -0.001377 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p35__s=0p85__cap=0p004 | PP-OPT194 | segment_price_conf_refinement | 0.269904 | 0.807321 | -0.001490 | -0.000809 | -0.001377 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p35__s=0p85__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269904 | 0.807321 | -0.001490 | -0.000809 | -0.001377 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p35__s=0p85__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269904 | 0.807321 | -0.001490 | -0.000809 | -0.001377 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p45__s=0p85__cap=0p004 | PP-OPT194 | segment_price_conf_refinement | 0.269904 | 0.807321 | -0.001490 | -0.000809 | -0.001377 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p45__s=0p85__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269904 | 0.807321 | -0.001490 | -0.000809 | -0.001377 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p45__s=0p85__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269904 | 0.807321 | -0.001490 | -0.000809 | -0.001377 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p55__s=0p85__cap=0p004 | PP-OPT194 | segment_price_conf_refinement | 0.269904 | 0.807321 | -0.001490 | -0.000809 | -0.001377 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p55__s=0p85__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269904 | 0.807321 | -0.001490 | -0.000809 | -0.001377 |
| ppopt194_price_conf_refine__scorethr=0p16__mix=0p55__s=0p85__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269904 | 0.807321 | -0.001490 | -0.000809 | -0.001377 |
| ppopt194_price_conf_refine__scorethr=0p02__mix=0p25__s=1p05__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p02__mix=0p25__s=1p05__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p02__mix=0p35__s=1p05__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p02__mix=0p35__s=1p05__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p02__mix=0p45__s=1p05__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p02__mix=0p45__s=1p05__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p02__mix=0p55__s=1p05__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p02__mix=0p55__s=1p05__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p08__mix=0p25__s=1p05__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p08__mix=0p25__s=1p05__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p08__mix=0p35__s=1p05__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p08__mix=0p35__s=1p05__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p08__mix=0p45__s=1p05__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p08__mix=0p45__s=1p05__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p08__mix=0p55__s=1p05__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p08__mix=0p55__s=1p05__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p0__mix=0p25__s=1p05__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p0__mix=0p25__s=1p05__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p0__mix=0p35__s=1p05__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p0__mix=0p35__s=1p05__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p0__mix=0p45__s=1p05__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p0__mix=0p45__s=1p05__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p0__mix=0p55__s=1p05__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p0__mix=0p55__s=1p05__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=m0p08__mix=0p25__s=1p05__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=m0p08__mix=0p25__s=1p05__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=m0p08__mix=0p35__s=1p05__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=m0p08__mix=0p35__s=1p05__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=m0p08__mix=0p45__s=1p05__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=m0p08__mix=0p45__s=1p05__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=m0p08__mix=0p55__s=1p05__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=m0p08__mix=0p55__s=1p05__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt196_dynamic_cap__seg=price_conf__scorethr=0p02__mix=0p35__s=1p05__basecap=0p006__shrink=0p3 | PP-OPT196 | segment_dynamic_cap_router | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt198_operational_segment_router_refinement__source=ppopt194_price_conf_refine__scorethr_0p02__mix_0p25__s_1p05__cap_0p006 | PP-OPT198 | segment_router_refinement_operational_selection | 0.269894 | 0.807326 | -0.001501 | -0.000804 | -0.001376 |
| ppopt196_dynamic_cap__seg=price_conf__scorethr=0p12__mix=0p35__s=0p95__basecap=0p006__shrink=0p55 | PP-OPT196 | segment_dynamic_cap_router | 0.269899 | 0.807323 | -0.001495 | -0.000806 | -0.001376 |
| ppopt196_dynamic_cap__seg=price_conf__scorethr=0p12__mix=0p35__s=1p05__basecap=0p004__shrink=0p3 | PP-OPT196 | segment_dynamic_cap_router | 0.269903 | 0.807323 | -0.001492 | -0.000807 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p12__mix=0p25__s=0p95__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269899 | 0.807323 | -0.001496 | -0.000806 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p12__mix=0p25__s=0p95__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269899 | 0.807323 | -0.001496 | -0.000806 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p12__mix=0p35__s=0p95__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269899 | 0.807323 | -0.001496 | -0.000806 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p12__mix=0p35__s=0p95__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269899 | 0.807323 | -0.001496 | -0.000806 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p12__mix=0p45__s=0p95__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269899 | 0.807323 | -0.001496 | -0.000806 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p12__mix=0p45__s=0p95__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269899 | 0.807323 | -0.001496 | -0.000806 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p12__mix=0p55__s=0p95__cap=0p006 | PP-OPT194 | segment_price_conf_refinement | 0.269899 | 0.807323 | -0.001496 | -0.000806 | -0.001376 |
| ppopt194_price_conf_refine__scorethr=0p12__mix=0p55__s=0p95__cap=0p008 | PP-OPT194 | segment_price_conf_refinement | 0.269899 | 0.807323 | -0.001496 | -0.000806 | -0.001376 |
| ppopt196_dynamic_cap__seg=price_conf__scorethr=0p12__mix=0p35__s=0p95__basecap=0p006__shrink=0p3 | PP-OPT196 | segment_dynamic_cap_router | 0.269899 | 0.807323 | -0.001496 | -0.000806 | -0.001376 |
| ppopt195_gap_conf_combined__gapthr=0p02__confthr=0p12__gapshare=0p3__s=0p95__cap=0p004 | PP-OPT195 | segment_gap_conf_combined_router | 0.269904 | 0.807324 | -0.001491 | -0.000806 | -0.001375 |
| ppopt195_gap_conf_combined__gapthr=0p02__confthr=0p12__gapshare=0p3__s=0p95__cap=0p006 | PP-OPT195 | segment_gap_conf_combined_router | 0.269904 | 0.807324 | -0.001491 | -0.000806 | -0.001375 |
| ppopt195_gap_conf_combined__gapthr=m0p08__confthr=0p12__gapshare=0p3__s=0p95__cap=0p004 | PP-OPT195 | segment_gap_conf_combined_router | 0.269904 | 0.807324 | -0.001491 | -0.000806 | -0.001375 |
| ppopt195_gap_conf_combined__gapthr=m0p08__confthr=0p12__gapshare=0p3__s=0p95__cap=0p006 | PP-OPT195 | segment_gap_conf_combined_router | 0.269904 | 0.807324 | -0.001491 | -0.000806 | -0.001375 |
| ppopt193_price_gap_refine__scorethr=0p12__mix=0p75__s=1p05__cap=0p0035 | PP-OPT193 | segment_price_gap_refinement | 0.269916 | 0.807319 | -0.001479 | -0.000811 | -0.001375 |
| ppopt193_price_gap_refine__scorethr=0p12__mix=0p75__s=1p05__cap=0p005 | PP-OPT193 | segment_price_gap_refinement | 0.269916 | 0.807319 | -0.001479 | -0.000811 | -0.001375 |
| ppopt196_dynamic_cap__seg=price_conf__scorethr=0p12__mix=0p35__s=0p95__basecap=0p004__shrink=0p3 | PP-OPT196 | segment_dynamic_cap_router | 0.269904 | 0.807323 | -0.001491 | -0.000806 | -0.001375 |
| ppopt194_price_conf_refine__scorethr=0p12__mix=0p25__s=1p05__cap=0p004 | PP-OPT194 | segment_price_conf_refinement | 0.269899 | 0.807323 | -0.001496 | -0.000807 | -0.001375 |
| ppopt194_price_conf_refine__scorethr=0p12__mix=0p35__s=1p05__cap=0p004 | PP-OPT194 | segment_price_conf_refinement | 0.269899 | 0.807323 | -0.001496 | -0.000807 | -0.001375 |
| ppopt194_price_conf_refine__scorethr=0p12__mix=0p45__s=1p05__cap=0p004 | PP-OPT194 | segment_price_conf_refinement | 0.269899 | 0.807323 | -0.001496 | -0.000807 | -0.001375 |
| ppopt194_price_conf_refine__scorethr=0p12__mix=0p55__s=1p05__cap=0p004 | PP-OPT194 | segment_price_conf_refinement | 0.269899 | 0.807323 | -0.001496 | -0.000807 | -0.001375 |
| ppopt195_gap_conf_combined__gapthr=0p02__confthr=0p12__gapshare=0p5__s=1p05__cap=0p004 | PP-OPT195 | segment_gap_conf_combined_router | 0.269904 | 0.807324 | -0.001491 | -0.000806 | -0.001375 |
| ppopt195_gap_conf_combined__gapthr=0p02__confthr=0p12__gapshare=0p5__s=1p05__cap=0p006 | PP-OPT195 | segment_gap_conf_combined_router | 0.269904 | 0.807324 | -0.001491 | -0.000806 | -0.001375 |
| ppopt197_consensus__mode=mean__s=1p05__cap=0p004 | PP-OPT197 | segment_consensus_router | 0.269904 | 0.807324 | -0.001491 | -0.000806 | -0.001375 |
| ppopt197_consensus__mode=mean__s=1p05__cap=0p006 | PP-OPT197 | segment_consensus_router | 0.269904 | 0.807324 | -0.001491 | -0.000806 | -0.001375 |
| ppopt195_gap_conf_combined__gapthr=m0p08__confthr=0p12__gapshare=0p5__s=1p05__cap=0p004 | PP-OPT195 | segment_gap_conf_combined_router | 0.269904 | 0.807324 | -0.001491 | -0.000806 | -0.001374 |
| ppopt195_gap_conf_combined__gapthr=m0p08__confthr=0p12__gapshare=0p5__s=1p05__cap=0p006 | PP-OPT195 | segment_gap_conf_combined_router | 0.269904 | 0.807324 | -0.001491 | -0.000806 | -0.001374 |
| ppopt196_dynamic_cap__seg=price_conf__scorethr=0p02__mix=0p35__s=1p05__basecap=0p006__shrink=0p55 | PP-OPT196 | segment_dynamic_cap_router | 0.269896 | 0.807326 | -0.001499 | -0.000804 | -0.001374 |
| ppopt196_dynamic_cap__seg=price_conf__scorethr=0p02__mix=0p35__s=1p05__basecap=0p006__shrink=0p8 | PP-OPT196 | segment_dynamic_cap_router | 0.269901 | 0.807326 | -0.001494 | -0.000804 | -0.001374 |
| ppopt193_price_gap_refine__scorethr=0p12__mix=0p85__s=1p05__cap=0p0025 | PP-OPT193 | segment_price_gap_refinement | 0.269917 | 0.807319 | -0.001478 | -0.000811 | -0.001374 |
| ppopt193_price_gap_refine__scorethr=0p12__mix=0p7__s=1p05__cap=0p0035 | PP-OPT193 | segment_price_gap_refinement | 0.269917 | 0.807319 | -0.001478 | -0.000811 | -0.001374 |

## 선택 후보 반복 안정성
| candidate_label | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_vs_pp64_MAPE | fixed_test_delta_vs_pp64_p95_APE | avg_pp64_MAPE_win_rate | avg_pp64_p95_win_rate | replacement_score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pp192_operational_reference | 0.269914 | 0.807326 | -0.000650 | -0.000173 | 0.953526 | 0.750962 | -0.018791 |
| candidate_ppopt194_price_conf_refine__scorethr_0p02__mix_0p25__s_1p05__cap_0p006__0f1df6f477 | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_0p02__mix_0p25__s_1p05__cap_0p008__49c318def7 | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_0p02__mix_0p35__s_1p05__cap_0p006__10544b218c | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_0p02__mix_0p35__s_1p05__cap_0p008__59f0b162e1 | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_0p02__mix_0p45__s_1p05__cap_0p006__fa1f3e5bf7 | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_0p02__mix_0p45__s_1p05__cap_0p008__1d7d8c7687 | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_0p02__mix_0p55__s_1p05__cap_0p006__19feb37426 | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_0p02__mix_0p55__s_1p05__cap_0p008__a1ffe050a6 | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_0p08__mix_0p25__s_1p05__cap_0p006__9a71888eab | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_0p08__mix_0p25__s_1p05__cap_0p008__a8ea9f8d2b | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_0p08__mix_0p35__s_1p05__cap_0p006__3fff87f895 | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_0p08__mix_0p35__s_1p05__cap_0p008__efec414c9c | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_0p08__mix_0p45__s_1p05__cap_0p006__7519394787 | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_0p08__mix_0p45__s_1p05__cap_0p008__b424201b5d | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_0p08__mix_0p55__s_1p05__cap_0p006__0f5ad2a186 | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_0p08__mix_0p55__s_1p05__cap_0p008__c862e44e93 | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_0p0__mix_0p25__s_1p05__cap_0p006__74fa4c217f | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_0p0__mix_0p25__s_1p05__cap_0p008__5306cccc55 | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_0p0__mix_0p35__s_1p05__cap_0p006__8af2a22cbc | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_0p0__mix_0p35__s_1p05__cap_0p008__269d15e6c1 | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_0p0__mix_0p45__s_1p05__cap_0p006__89cb14ed2c | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_0p0__mix_0p45__s_1p05__cap_0p008__93cc47a833 | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_0p0__mix_0p55__s_1p05__cap_0p006__ca8bfbe302 | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_0p0__mix_0p55__s_1p05__cap_0p008__4b834a912d | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_m0p08__mix_0p25__s_1p05__cap_0p006__02bd7f9637 | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_m0p08__mix_0p25__s_1p05__cap_0p008__aa0a9f77fa | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_m0p08__mix_0p35__s_1p05__cap_0p006__2f0957ce3c | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_m0p08__mix_0p35__s_1p05__cap_0p008__12c8fa2208 | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_m0p08__mix_0p45__s_1p05__cap_0p006__0acffa98e9 | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_m0p08__mix_0p45__s_1p05__cap_0p008__21f22f3397 | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_m0p08__mix_0p55__s_1p05__cap_0p006__98abcd0494 | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_m0p08__mix_0p55__s_1p05__cap_0p008__8a9714832b | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt196_dynamic_cap__seg_price_conf__scorethr_0p02__mix_0p35__s_1p05__basecap_0p006__shrink__b204e30cbc | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| pp198_operational_segment_router_refinement_challenger | 0.269894 | 0.807326 | -0.000670 | -0.000173 | 0.952885 | 0.747756 | -0.018785 |
| candidate_ppopt194_price_conf_refine__scorethr_0p12__mix_0p25__s_1p05__cap_0p006__46d5935bf5 | 0.269896 | 0.807323 | -0.000669 | -0.000176 | 0.952885 | 0.747756 | -0.018784 |
| candidate_ppopt194_price_conf_refine__scorethr_0p12__mix_0p25__s_1p05__cap_0p008__9c29360579 | 0.269896 | 0.807323 | -0.000669 | -0.000176 | 0.952885 | 0.747756 | -0.018784 |
| candidate_ppopt194_price_conf_refine__scorethr_0p12__mix_0p35__s_1p05__cap_0p006__851fa74d03 | 0.269896 | 0.807323 | -0.000669 | -0.000176 | 0.952885 | 0.747756 | -0.018784 |
| candidate_ppopt194_price_conf_refine__scorethr_0p12__mix_0p35__s_1p05__cap_0p008__1eca966fd0 | 0.269896 | 0.807323 | -0.000669 | -0.000176 | 0.952885 | 0.747756 | -0.018784 |
| candidate_ppopt194_price_conf_refine__scorethr_0p12__mix_0p45__s_1p05__cap_0p006__0178c4d9eb | 0.269896 | 0.807323 | -0.000669 | -0.000176 | 0.952885 | 0.747756 | -0.018784 |
| candidate_ppopt194_price_conf_refine__scorethr_0p12__mix_0p45__s_1p05__cap_0p008__327b7cc187 | 0.269896 | 0.807323 | -0.000669 | -0.000176 | 0.952885 | 0.747756 | -0.018784 |
| candidate_ppopt194_price_conf_refine__scorethr_0p12__mix_0p55__s_1p05__cap_0p006__23754b4caa | 0.269896 | 0.807323 | -0.000669 | -0.000176 | 0.952885 | 0.747756 | -0.018784 |
| candidate_ppopt194_price_conf_refine__scorethr_0p12__mix_0p55__s_1p05__cap_0p008__39f6d2bb2b | 0.269896 | 0.807323 | -0.000669 | -0.000176 | 0.952885 | 0.747756 | -0.018784 |
| candidate_ppopt196_dynamic_cap__seg_price_conf__scorethr_0p12__mix_0p35__s_1p05__basecap_0p006__shrink__a4e12e07a8 | 0.269896 | 0.807323 | -0.000669 | -0.000176 | 0.952885 | 0.747756 | -0.018784 |
| candidate_ppopt196_dynamic_cap__seg_price_conf__scorethr_0p02__mix_0p35__s_1p05__basecap_0p006__shrink__b1573a4020 | 0.269896 | 0.807326 | -0.000668 | -0.000173 | 0.952885 | 0.749359 | -0.018783 |
| candidate_ppopt196_dynamic_cap__seg_price_conf__scorethr_0p02__mix_0p35__s_1p05__basecap_0p006__shrink__78c483bebf | 0.269901 | 0.807326 | -0.000663 | -0.000173 | 0.952885 | 0.750641 | -0.018778 |
| candidate_ppopt196_dynamic_cap__seg_price_conf__scorethr_0p02__mix_0p35__s_0p95__basecap_0p006__shrink__83fa5f92e0 | 0.269902 | 0.807326 | -0.000662 | -0.000173 | 0.952885 | 0.750641 | -0.018778 |
| candidate_ppopt195_gap_conf_combined__gapthr_0p02__confthr_0p02__gapshare_0p3__s_0p95__cap_0p004__a8a8145211 | 0.269903 | 0.807326 | -0.000661 | -0.000173 | 0.952885 | 0.749679 | -0.018777 |
| candidate_ppopt195_gap_conf_combined__gapthr_0p02__confthr_0p02__gapshare_0p3__s_0p95__cap_0p006__a393b6ecd1 | 0.269903 | 0.807326 | -0.000661 | -0.000173 | 0.952885 | 0.749679 | -0.018777 |
| candidate_ppopt195_gap_conf_combined__gapthr_m0p08__confthr_0p02__gapshare_0p3__s_0p95__cap_0p004__b25dcf604e | 0.269903 | 0.807326 | -0.000661 | -0.000173 | 0.952885 | 0.749679 | -0.018777 |
| candidate_ppopt195_gap_conf_combined__gapthr_m0p08__confthr_0p02__gapshare_0p3__s_0p95__cap_0p006__b95f48b6fc | 0.269903 | 0.807326 | -0.000661 | -0.000173 | 0.952885 | 0.749679 | -0.018777 |
| candidate_ppopt196_dynamic_cap__seg_price_conf__scorethr_0p12__mix_0p35__s_1p05__basecap_0p006__shrink__d1f34cb492 | 0.269903 | 0.807323 | -0.000661 | -0.000176 | 0.952885 | 0.750641 | -0.018777 |
| candidate_ppopt196_dynamic_cap__seg_price_conf__scorethr_0p02__mix_0p35__s_0p85__basecap_0p006__shrink__3a0c263a88 | 0.269903 | 0.807326 | -0.000661 | -0.000173 | 0.952885 | 0.750641 | -0.018776 |
| candidate_ppopt196_dynamic_cap__seg_price_conf__scorethr_0p12__mix_0p35__s_0p95__basecap_0p006__shrink__10cc6ccd41 | 0.269903 | 0.807323 | -0.000661 | -0.000175 | 0.952885 | 0.750641 | -0.018776 |
| candidate_ppopt195_gap_conf_combined__gapthr_0p02__confthr_0p02__gapshare_0p5__s_1p05__cap_0p004__5294f78467 | 0.269903 | 0.807326 | -0.000661 | -0.000173 | 0.952885 | 0.749679 | -0.018776 |
| candidate_ppopt195_gap_conf_combined__gapthr_0p02__confthr_0p02__gapshare_0p5__s_1p05__cap_0p006__5716b586b7 | 0.269903 | 0.807326 | -0.000661 | -0.000173 | 0.952885 | 0.749679 | -0.018776 |
| candidate_ppopt195_gap_conf_combined__gapthr_m0p08__confthr_0p02__gapshare_0p5__s_1p05__cap_0p004__6ba9077a6d | 0.269903 | 0.807326 | -0.000661 | -0.000173 | 0.952885 | 0.749679 | -0.018776 |
| candidate_ppopt195_gap_conf_combined__gapthr_m0p08__confthr_0p02__gapshare_0p5__s_1p05__cap_0p006__0b9db51e4c | 0.269903 | 0.807326 | -0.000661 | -0.000173 | 0.952885 | 0.749679 | -0.018776 |
| candidate_ppopt195_gap_conf_combined__gapthr_0p02__confthr_0p12__gapshare_0p5__s_1p05__cap_0p004__a8fe8f7417 | 0.269904 | 0.807324 | -0.000660 | -0.000174 | 0.952885 | 0.749679 | -0.018775 |
| candidate_ppopt195_gap_conf_combined__gapthr_0p02__confthr_0p12__gapshare_0p5__s_1p05__cap_0p006__cb2a745725 | 0.269904 | 0.807324 | -0.000660 | -0.000174 | 0.952885 | 0.749679 | -0.018775 |
| candidate_ppopt197_consensus__mode_mean__s_1p05__cap_0p004__59560789b2 | 0.269904 | 0.807324 | -0.000660 | -0.000174 | 0.952885 | 0.749679 | -0.018775 |
| candidate_ppopt197_consensus__mode_mean__s_1p05__cap_0p006__3f4da4b75b | 0.269904 | 0.807324 | -0.000660 | -0.000174 | 0.952885 | 0.749679 | -0.018775 |
| candidate_ppopt196_dynamic_cap__seg_price_conf__scorethr_0p12__mix_0p35__s_1p05__basecap_0p006__shrink__edacf85e38 | 0.269898 | 0.807323 | -0.000666 | -0.000176 | 0.952564 | 0.749359 | -0.018769 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p25__s_1p05__cap_0p006__868b04597d | 0.269898 | 0.807320 | -0.000666 | -0.000179 | 0.952564 | 0.747756 | -0.018769 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p25__s_1p05__cap_0p008__3d21cd5ba1 | 0.269898 | 0.807320 | -0.000666 | -0.000179 | 0.952564 | 0.747756 | -0.018769 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p35__s_1p05__cap_0p006__fa8a244649 | 0.269898 | 0.807320 | -0.000666 | -0.000179 | 0.952564 | 0.747756 | -0.018769 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p35__s_1p05__cap_0p008__73cdf79028 | 0.269898 | 0.807320 | -0.000666 | -0.000179 | 0.952564 | 0.747756 | -0.018769 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p45__s_1p05__cap_0p006__2699319ead | 0.269898 | 0.807320 | -0.000666 | -0.000179 | 0.952564 | 0.747756 | -0.018769 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p45__s_1p05__cap_0p008__5bdf5ace57 | 0.269898 | 0.807320 | -0.000666 | -0.000179 | 0.952564 | 0.747756 | -0.018769 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p55__s_1p05__cap_0p006__b194d4be5f | 0.269898 | 0.807320 | -0.000666 | -0.000179 | 0.952564 | 0.747756 | -0.018769 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p55__s_1p05__cap_0p008__0e84d5a805 | 0.269898 | 0.807320 | -0.000666 | -0.000179 | 0.952564 | 0.747756 | -0.018769 |
| candidate_ppopt194_price_conf_refine__scorethr_0p02__mix_0p25__s_1p05__cap_0p004__445660f9bc | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952564 | 0.749679 | -0.018769 |
| candidate_ppopt194_price_conf_refine__scorethr_0p02__mix_0p35__s_1p05__cap_0p004__a25c6f03f6 | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952564 | 0.749679 | -0.018769 |
| candidate_ppopt194_price_conf_refine__scorethr_0p02__mix_0p45__s_1p05__cap_0p004__0422001c3f | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952564 | 0.749679 | -0.018769 |
| candidate_ppopt194_price_conf_refine__scorethr_0p02__mix_0p55__s_1p05__cap_0p004__82b1faf335 | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952564 | 0.749679 | -0.018769 |
| candidate_ppopt193_price_gap_refine__scorethr_0p12__mix_0p8__s_1p05__cap_0p0035__84b3aa445f | 0.269915 | 0.807319 | -0.000649 | -0.000179 | 0.952885 | 0.750962 | -0.018764 |
| candidate_ppopt193_price_gap_refine__scorethr_0p12__mix_0p8__s_1p05__cap_0p005__a61239d1c6 | 0.269915 | 0.807319 | -0.000649 | -0.000179 | 0.952885 | 0.750962 | -0.018764 |
| candidate_ppopt196_dynamic_cap__seg_price_conf__scorethr_0p12__mix_0p35__s_1p05__basecap_0p004__shrink__2bd23586d9 | 0.269903 | 0.807323 | -0.000661 | -0.000176 | 0.952564 | 0.750641 | -0.018763 |
| candidate_ppopt196_dynamic_cap__seg_price_conf__scorethr_0p12__mix_0p35__s_0p85__basecap_0p006__shrink__5815c055a1 | 0.269904 | 0.807324 | -0.000660 | -0.000175 | 0.952564 | 0.750641 | -0.018762 |
| candidate_ppopt194_price_conf_refine__scorethr_0p02__mix_0p25__s_0p95__cap_0p006__6de16fd5dc | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_0p02__mix_0p25__s_0p95__cap_0p008__0f1b9104f7 | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_0p02__mix_0p35__s_0p95__cap_0p006__623c7e15a0 | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_0p02__mix_0p35__s_0p95__cap_0p008__a8f3ad5a62 | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_0p02__mix_0p45__s_0p95__cap_0p006__29f92f655e | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_0p02__mix_0p45__s_0p95__cap_0p008__7cb805cc9c | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_0p02__mix_0p55__s_0p95__cap_0p006__ae29caa4a0 | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_0p02__mix_0p55__s_0p95__cap_0p008__80224bb38b | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_0p08__mix_0p25__s_0p95__cap_0p006__74607a1c56 | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_0p08__mix_0p25__s_0p95__cap_0p008__bc682ed999 | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_0p08__mix_0p35__s_0p95__cap_0p006__b424b3acaa | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_0p08__mix_0p35__s_0p95__cap_0p008__a96625f3de | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_0p08__mix_0p45__s_0p95__cap_0p006__761d87a5d6 | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_0p08__mix_0p45__s_0p95__cap_0p008__8d76c2fe24 | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_0p08__mix_0p55__s_0p95__cap_0p006__ab3c1ea81f | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_0p08__mix_0p55__s_0p95__cap_0p008__19be6110f2 | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_0p0__mix_0p25__s_0p95__cap_0p006__e278df24ea | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_0p0__mix_0p25__s_0p95__cap_0p008__ea3e3980b1 | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_0p0__mix_0p35__s_0p95__cap_0p006__509fd5a7b6 | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_0p0__mix_0p35__s_0p95__cap_0p008__9523de6a0d | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_0p0__mix_0p45__s_0p95__cap_0p006__69b49ec888 | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_0p0__mix_0p45__s_0p95__cap_0p008__dd16f0be7c | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_0p0__mix_0p55__s_0p95__cap_0p006__832a870a8d | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_0p0__mix_0p55__s_0p95__cap_0p008__b1687f7d56 | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_m0p08__mix_0p25__s_0p95__cap_0p006__20ef368f9f | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_m0p08__mix_0p25__s_0p95__cap_0p008__d4aa284da7 | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_m0p08__mix_0p35__s_0p95__cap_0p006__aa3f2d8b0a | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_m0p08__mix_0p35__s_0p95__cap_0p008__2a0de054c5 | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_m0p08__mix_0p45__s_0p95__cap_0p006__e941889f21 | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_m0p08__mix_0p45__s_0p95__cap_0p008__49058b082a | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_m0p08__mix_0p55__s_0p95__cap_0p006__ac9948f5f4 | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt194_price_conf_refine__scorethr_m0p08__mix_0p55__s_0p95__cap_0p008__2b66c6ac01 | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt196_dynamic_cap__seg_price_conf__scorethr_0p02__mix_0p35__s_0p95__basecap_0p006__shrink__c89d464b96 | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt196_dynamic_cap__seg_price_conf__scorethr_0p12__mix_0p35__s_0p95__basecap_0p006__shrink__18f479148d | 0.269899 | 0.807323 | -0.000665 | -0.000175 | 0.952244 | 0.749359 | -0.018754 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p25__s_0p85__cap_0p004__8b8b9671fe | 0.269904 | 0.807321 | -0.000660 | -0.000178 | 0.952244 | 0.749679 | -0.018749 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p25__s_0p85__cap_0p006__0777ba0ab0 | 0.269904 | 0.807321 | -0.000660 | -0.000178 | 0.952244 | 0.749679 | -0.018749 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p25__s_0p85__cap_0p008__d0ae5c8076 | 0.269904 | 0.807321 | -0.000660 | -0.000178 | 0.952244 | 0.749679 | -0.018749 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p35__s_0p85__cap_0p004__9975ff5f09 | 0.269904 | 0.807321 | -0.000660 | -0.000178 | 0.952244 | 0.749679 | -0.018749 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p35__s_0p85__cap_0p006__a4d5410d30 | 0.269904 | 0.807321 | -0.000660 | -0.000178 | 0.952244 | 0.749679 | -0.018749 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p35__s_0p85__cap_0p008__ef7c8b7794 | 0.269904 | 0.807321 | -0.000660 | -0.000178 | 0.952244 | 0.749679 | -0.018749 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p45__s_0p85__cap_0p004__97491789be | 0.269904 | 0.807321 | -0.000660 | -0.000178 | 0.952244 | 0.749679 | -0.018749 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p45__s_0p85__cap_0p006__b21e6a7075 | 0.269904 | 0.807321 | -0.000660 | -0.000178 | 0.952244 | 0.749679 | -0.018749 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p45__s_0p85__cap_0p008__82440112e8 | 0.269904 | 0.807321 | -0.000660 | -0.000178 | 0.952244 | 0.749679 | -0.018749 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p55__s_0p85__cap_0p004__64ba3c98ec | 0.269904 | 0.807321 | -0.000660 | -0.000178 | 0.952244 | 0.749679 | -0.018749 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p55__s_0p85__cap_0p006__7445d58f5a | 0.269904 | 0.807321 | -0.000660 | -0.000178 | 0.952244 | 0.749679 | -0.018749 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p55__s_0p85__cap_0p008__68164d122b | 0.269904 | 0.807321 | -0.000660 | -0.000178 | 0.952244 | 0.749679 | -0.018749 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p25__s_0p95__cap_0p006__09ecfafe25 | 0.269901 | 0.807321 | -0.000663 | -0.000178 | 0.951923 | 0.748718 | -0.018740 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p25__s_0p95__cap_0p008__2ea034d02c | 0.269901 | 0.807321 | -0.000663 | -0.000178 | 0.951923 | 0.748718 | -0.018740 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p35__s_0p95__cap_0p006__f4a3b6193f | 0.269901 | 0.807321 | -0.000663 | -0.000178 | 0.951923 | 0.748718 | -0.018740 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p35__s_0p95__cap_0p008__5faf3b7031 | 0.269901 | 0.807321 | -0.000663 | -0.000178 | 0.951923 | 0.748718 | -0.018740 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p45__s_0p95__cap_0p006__dc9407817b | 0.269901 | 0.807321 | -0.000663 | -0.000178 | 0.951923 | 0.748718 | -0.018740 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p45__s_0p95__cap_0p008__9c54406126 | 0.269901 | 0.807321 | -0.000663 | -0.000178 | 0.951923 | 0.748718 | -0.018740 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p55__s_0p95__cap_0p006__f87305be61 | 0.269901 | 0.807321 | -0.000663 | -0.000178 | 0.951923 | 0.748718 | -0.018740 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p55__s_0p95__cap_0p008__27aff380b3 | 0.269901 | 0.807321 | -0.000663 | -0.000178 | 0.951923 | 0.748718 | -0.018740 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p25__s_1p05__cap_0p004__5318f83f9d | 0.269902 | 0.807320 | -0.000662 | -0.000179 | 0.951923 | 0.749679 | -0.018739 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p35__s_1p05__cap_0p004__cb3264df02 | 0.269902 | 0.807320 | -0.000662 | -0.000179 | 0.951923 | 0.749679 | -0.018739 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p45__s_1p05__cap_0p004__667e641ad4 | 0.269902 | 0.807320 | -0.000662 | -0.000179 | 0.951923 | 0.749679 | -0.018739 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p55__s_1p05__cap_0p004__4a73cb4c31 | 0.269902 | 0.807320 | -0.000662 | -0.000179 | 0.951923 | 0.749679 | -0.018739 |
| candidate_ppopt193_price_gap_refine__scorethr_0p12__mix_0p85__s_1p05__cap_0p0035__f868c848ec | 0.269914 | 0.807319 | -0.000650 | -0.000179 | 0.952244 | 0.750962 | -0.018739 |
| candidate_ppopt193_price_gap_refine__scorethr_0p12__mix_0p85__s_1p05__cap_0p005__20a5f0c926 | 0.269914 | 0.807319 | -0.000650 | -0.000179 | 0.952244 | 0.750962 | -0.018739 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p25__s_0p95__cap_0p004__4717c814ae | 0.269903 | 0.807321 | -0.000662 | -0.000178 | 0.951923 | 0.749679 | -0.018738 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p35__s_0p95__cap_0p004__2c7c547c07 | 0.269903 | 0.807321 | -0.000662 | -0.000178 | 0.951923 | 0.749679 | -0.018738 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p45__s_0p95__cap_0p004__1ce1704438 | 0.269903 | 0.807321 | -0.000662 | -0.000178 | 0.951923 | 0.749679 | -0.018738 |
| candidate_ppopt194_price_conf_refine__scorethr_0p16__mix_0p55__s_0p95__cap_0p004__0463410c1d | 0.269903 | 0.807321 | -0.000662 | -0.000178 | 0.951923 | 0.749679 | -0.018738 |
| pp180_operational_reference | 0.269933 | 0.807326 | -0.000631 | -0.000173 | 0.952244 | 0.754487 | -0.018721 |
| pp192_p95_guarded_reference | 0.269949 | 0.807255 | -0.000615 | -0.000244 | 0.950962 | 0.751603 | -0.018653 |
| pp198_p95_guarded_segment_router_refinement_challenger | 0.269949 | 0.807255 | -0.000615 | -0.000244 | 0.950962 | 0.751603 | -0.018653 |
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
| pp198_p95_extreme_segment_router_refinement_challenger | 0.270269 | 0.805949 | -0.000295 | -0.001549 | 0.598397 | 0.500962 | -0.004079 |
| pp64_current_best | 0.270564 | 0.807499 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.020000 |

## 실행 설정
```json
{
  "experiment_id": "PP-OPT193-198",
  "experiment_slug": "PP-OPT193_198_warm_segment_outcome_router_refinement",
  "created_at": "2026-06-10T10:40:30",
  "base_candidate": "hcoef_stable",
  "previous_experiment": "experiments/track6/PP-OPT187_192_warm_pp180_pp186_risk_router",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 802,
  "prediction_rows": 903052,
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
    "pp192_p95_extreme": "ppopt192_p95_extreme_pp180_pp186_risk_router__source=reference_pp148_p95"
  },
  "selection_decision": {
    "operational_label": "candidate_ppopt194_price_conf_refine__scorethr_0p02__mix_0p25__s_1p05__cap_0p006__0f1df6f477",
    "operational_candidate": "ppopt194_price_conf_refine__scorethr=0p02__mix=0p25__s=1p05__cap=0p006",
    "operational_fixed_test_MAPE": 0.26989400901822014,
    "operational_fixed_test_p95_APE": 0.8073255046591389,
    "operational_delta_vs_pp64_MAPE": -0.0006700328974402203,
    "operational_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "operational_delta_vs_pp126_MAPE": -0.00022038773163168823,
    "operational_delta_vs_pp126_p95_APE": -0.0001645562387090349,
    "operational_delta_vs_pp148_MAPE": -0.00024597935435927143,
    "operational_delta_vs_pp148_p95_APE": 9.45931204405781e-05,
    "operational_delta_vs_pp166_MAPE": -0.0001029766470184712,
    "operational_delta_vs_pp166_p95_APE": 9.45931204405781e-05,
    "operational_delta_vs_pp172_MAPE": -0.00010340564293043197,
    "operational_delta_vs_pp172_p95_APE": 9.45931204405781e-05,
    "operational_delta_vs_pp180_MAPE": -3.861756956818896e-05,
    "operational_delta_vs_pp180_p95_APE": 0.0,
    "operational_delta_vs_pp186_MAPE": -6.662484800645796e-05,
    "operational_delta_vs_pp186_p95_APE": 9.45931204405781e-05,
    "operational_delta_vs_pp192_MAPE": -2.0345126529708324e-05,
    "operational_delta_vs_pp192_p95_APE": 0.0,
    "operational_avg_pp64_MAPE_win_rate": 0.9528846153846153,
    "operational_avg_pp64_p95_win_rate": 0.7477564102564102,
    "operational_replacement_score": -0.018785417512824833,
    "p95_guarded_label": "pp192_p95_guarded_reference",
    "p95_guarded_candidate": "ppopt192_p95_guarded_pp180_pp186_risk_router__source=ppopt187_hard_risk_router__risk_uncertainty__mode_hard__thr_0p78__w_0p06__s_0p75",
    "p95_guarded_fixed_test_MAPE": 0.26994920114208765,
    "p95_guarded_fixed_test_p95_APE": 0.8072545738314348,
    "p95_guarded_delta_vs_pp64_MAPE": -0.0006148407735727113,
    "p95_guarded_delta_vs_pp64_p95_APE": -0.0002442784746750082,
    "p95_guarded_delta_vs_pp126_MAPE": -0.0001651956077641792,
    "p95_guarded_delta_vs_pp126_p95_APE": -0.00023548706641307593,
    "p95_guarded_delta_vs_pp148_MAPE": -0.00019078723049176238,
    "p95_guarded_delta_vs_pp148_p95_APE": 2.3662292736537083e-05,
    "p95_guarded_delta_vs_pp166_MAPE": -4.7784523150962155e-05,
    "p95_guarded_delta_vs_pp166_p95_APE": 2.3662292736537083e-05,
    "p95_guarded_delta_vs_pp172_MAPE": -4.821351906292293e-05,
    "p95_guarded_delta_vs_pp172_p95_APE": 2.3662292736537083e-05,
    "p95_guarded_delta_vs_pp180_MAPE": 1.6574554299320088e-05,
    "p95_guarded_delta_vs_pp180_p95_APE": -7.093082770404102e-05,
    "p95_guarded_delta_vs_pp186_MAPE": -1.1432724138948913e-05,
    "p95_guarded_delta_vs_pp186_p95_APE": 2.3662292736537083e-05,
    "p95_guarded_delta_vs_pp192_MAPE": 3.484699733780072e-05,
    "p95_guarded_delta_vs_pp192_p95_APE": -7.093082770404102e-05,
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
    "p95_extreme_delta_vs_pp192_MAPE": 0.00035457176435810256,
    "p95_extreme_delta_vs_pp192_p95_APE": -0.0013761288369714686,
    "p95_extreme_avg_pp64_MAPE_win_rate": 0.5983974358974359,
    "p95_extreme_avg_pp64_p95_win_rate": 0.5009615384615385,
    "p95_extreme_replacement_score": -0.0040792899192624915,
    "operational_protocol_candidate": "ppopt198_operational_segment_router_refinement__source=ppopt194_price_conf_refine__scorethr_0p02__mix_0p25__s_1p05__cap_0p006",
    "p95_guarded_protocol_candidate": "ppopt198_p95_guarded_segment_router_refinement__source=ppopt192_p95_guarded_pp180_pp186_risk_router__source_ppopt187_hard_risk_router__risk_uncertainty__mode_hard__thr_0p78__w",
    "p95_extreme_protocol_candidate": "ppopt198_p95_extreme_segment_router_refinement__source=reference_pp148_p95"
  },
  "items": [
    {
      "item_id": "PP-OPT193",
      "priority": "1",
      "title": "price-gap segment router refinement",
      "description": "PP192가 선택한 stable price band x medium/support 구간 라우터 주변 파라미터를 좁게 재탐색."
    },
    {
      "item_id": "PP-OPT194",
      "priority": "2",
      "title": "price-confidence segment router refinement",
      "description": "test MAPE가 가장 낮았던 stable price band x confidence tier 라우터 주변을 안정성 기준으로 재검증."
    },
    {
      "item_id": "PP-OPT195",
      "priority": "3",
      "title": "price-gap and confidence combined router",
      "description": "price-gap hazard와 price-confidence hazard를 가중 결합해 단일 segment 편향을 줄인다."
    },
    {
      "item_id": "PP-OPT196",
      "priority": "4",
      "title": "p95-constrained dynamic cap router",
      "description": "segment p95 hazard가 큰 구간은 cap을 줄이고 안정 구간만 더 크게 이동한다."
    },
    {
      "item_id": "PP-OPT197",
      "priority": "5",
      "title": "segment consensus router",
      "description": "price-gap과 confidence segment가 동시에 위험하다고 보는 row만 PP186 쪽으로 되돌린다."
    },
    {
      "item_id": "PP-OPT198",
      "priority": "6",
      "title": "final segment router decision",
      "description": "PP192와 신규 세분화 후보를 fixed/repeated 기준으로 비교해 운영 후보를 선택한다."
    }
  ],
  "router_formula": {
    "base": "PP192 uses PP180 operational log price as base",
    "safe_price": "PP186 p95-guard log price",
    "final": "PP180 log price + clip((PP186 log price - PP180 log price) * segment_weight * strength, row_cap)",
    "segments": [
      "stable_price_band x medium_support_bucket",
      "stable_price_band x confidence_tier",
      "combined segment weights"
    ]
  }
}
```