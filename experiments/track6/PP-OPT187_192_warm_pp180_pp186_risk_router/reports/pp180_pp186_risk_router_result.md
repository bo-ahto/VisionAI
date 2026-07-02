# PP-OPT187~192 Warm PP180/PP186 risk router 결과

- 작성일: 2026-06-10 10:30
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 목적: PP180의 MAPE 장점과 PP186의 p95 안정성을 row별 라우팅으로 결합
- 결론: 운영 후보 fixed test MAPE 0.269914, p95 0.807326. PP180 대비 MAPE -0.000018, p95 +0.000000. p95 고정 후보 MAPE 0.269949, p95 0.807255.

## 주요 후보 test 비교
| candidate | family | item_id | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt192_operational_pp180_pp186_risk_router__source=ppopt189_segment_router__seg_price_gap__scorethr_0p02__mix_0p75__s_0p95__cap_0p0025 | pp180_pp186_risk_router_operational_selection | PP-OPT192 | 0.140975 | 0.269914 | 0.807326 | 0.397468 | -0.001481 | -0.000804 |
| ppopt180_operational_basis_generation_challenger__source=ppopt174_direct_basis__source_stack_huber_weighted__thr_0p08__s_0p3__cap_0p004 | reference_prior | REFERENCE | 0.140975 | 0.269933 | 0.807326 | 0.397475 | -0.001462 | -0.000804 |
| ppopt192_p95_guarded_pp180_pp186_risk_router__source=ppopt187_hard_risk_router__risk_uncertainty__mode_hard__thr_0p78__w_0p06__s_0p75 | pp180_pp186_risk_router_p95_guarded_selection | PP-OPT192 | 0.140094 | 0.269949 | 0.807255 | 0.397482 | -0.001446 | -0.000875 |
| ppopt186_operational_huber_basis_p95_guard__source=ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p04__s_0p42__cap_0p0045 | reference_prior | REFERENCE | 0.139801 | 0.269961 | 0.807231 | 0.397497 | -0.001434 | -0.000899 |
| ppopt172_operational_pp166_tail_calibration_challenger__source=ppopt169_segment_router__source_pp162_p95_gate__seg_price_conf__thr_m0p04__s_0p5__cap_0p004 | reference_prior | REFERENCE | 0.139801 | 0.269997 | 0.807231 | 0.397516 | -0.001397 | -0.000899 |
| reference_pp126_operational | reference_prior | REFERENCE | 0.136320 | 0.270114 | 0.807490 | 0.397588 | -0.001280 | -0.000640 |
| reference_pp148_operational | reference_prior | REFERENCE | 0.139801 | 0.270140 | 0.807231 | 0.397525 | -0.001255 | -0.000899 |
| reference_pp148_p95 | reference_prior | REFERENCE | 0.141036 | 0.270269 | 0.805949 | 0.397421 | -0.001126 | -0.002181 |
| ppopt192_p95_extreme_pp180_pp186_risk_router__source=reference_pp148_p95 | pp180_pp186_risk_router_p95_extreme_selection | PP-OPT192 | 0.141036 | 0.270269 | 0.805949 | 0.397421 | -0.001126 | -0.002181 |
| reference_pp64_current_best | reference_prior | REFERENCE | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | p95_test_MAPE | p95_test_p95_APE | operational_pass_vs_incumbent | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | hard risk router | 360 | 0.269954 | 0.807326 | 0.269955 | 0.807231 | False | pp180_pp186_hard_risk_router | ppopt187_hard_risk_router__risk=gap_heavy__mode=hard__thr=0p78__w=0p06__s=1p0 |
| 4 | prediction gap hazard rollback | 432 | 0.269954 | 0.807259 | 0.269951 | 0.807259 | False | pp180_pp186_gap_hazard_rollback | ppopt190_gap_hazard_rollback__risk=gap_heavy__gapthr=0p76__stable=0p25__s=0p7__cap=0p0025 |
| 6 | final PP180/PP186 router decision | 3 | 0.269949 | 0.807255 | 0.270269 | 0.805949 | False | pp180_pp186_risk_router_p95_guarded_selection | ppopt192_p95_guarded_pp180_pp186_risk_router__source=ppopt187_hard_risk_router__risk_uncertainty__mode_hard__thr_0p78__w_0p06__s_0p75 |
| 2 | soft risk blend | 768 | 0.269962 | 0.807259 | 0.269955 | 0.807259 | False | pp180_pp186_soft_risk_blend | ppopt188_soft_risk_blend__risk=gap_heavy__thr=0p46__w=0p16__s=0p7__cap=0p0025 |
| 5 | hybrid risk and segment router | 324 | 0.269934 | 0.807294 | 0.269934 | 0.807294 | False | pp180_pp186_hybrid_risk_segment_router | ppopt191_hybrid_router__risk=gap_heavy__thr=0p46__segshare=0p75__s=0p75__cap=0p0035 |
| 3 | segment outcome router | 576 | 0.269899 | 0.807323 | 0.269918 | 0.807320 | False | pp180_pp186_segment_outcome_router | ppopt189_segment_router__seg=price_conf__scorethr=0p12__mix=0p35__s=0p95__cap=0p006 |

## 탐색 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt187_hard_risk_router__risk=gap_heavy__mode=hard__thr=0p78__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269954 | 0.807326 | -0.001441 | -0.000804 | -0.001623 |
| ppopt187_hard_risk_router__risk=gap_heavy__mode=hard__thr=0p78__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269954 | 0.807326 | -0.001441 | -0.000804 | -0.001623 |
| ppopt187_hard_risk_router__risk=gap_heavy__mode=hard__thr=0p78__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269954 | 0.807326 | -0.001441 | -0.000804 | -0.001623 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=nearhard__thr=0p78__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269943 | 0.807295 | -0.001452 | -0.000835 | -0.001615 |
| ppopt187_hard_risk_router__risk=conservative__mode=hard__thr=0p78__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269953 | 0.807326 | -0.001442 | -0.000804 | -0.001614 |
| ppopt187_hard_risk_router__risk=conservative__mode=hard__thr=0p78__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269953 | 0.807326 | -0.001442 | -0.000804 | -0.001614 |
| ppopt187_hard_risk_router__risk=conservative__mode=hard__thr=0p78__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269953 | 0.807326 | -0.001442 | -0.000804 | -0.001614 |
| ppopt187_hard_risk_router__risk=tail__mode=hard__thr=0p78__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269932 | 0.807326 | -0.001463 | -0.000804 | -0.001613 |
| ppopt187_hard_risk_router__risk=tail__mode=hard__thr=0p78__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269932 | 0.807326 | -0.001463 | -0.000804 | -0.001613 |
| ppopt187_hard_risk_router__risk=tail__mode=hard__thr=0p78__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269932 | 0.807326 | -0.001463 | -0.000804 | -0.001613 |
| ppopt187_hard_risk_router__risk=gap_heavy__mode=nearhard__thr=0p72__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269973 | 0.807233 | -0.001422 | -0.000897 | -0.001613 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=hard__thr=0p78__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269955 | 0.807231 | -0.001440 | -0.000899 | -0.001609 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=hard__thr=0p78__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269955 | 0.807231 | -0.001440 | -0.000899 | -0.001609 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=hard__thr=0p78__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269955 | 0.807231 | -0.001440 | -0.000899 | -0.001609 |
| ppopt187_hard_risk_router__risk=tail__mode=nearhard__thr=0p72__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269961 | 0.807274 | -0.001434 | -0.000856 | -0.001607 |
| ppopt187_hard_risk_router__risk=conservative__mode=nearhard__thr=0p72__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269973 | 0.807243 | -0.001422 | -0.000887 | -0.001604 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=nearhard__thr=0p72__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269969 | 0.807250 | -0.001426 | -0.000880 | -0.001603 |
| ppopt187_hard_risk_router__risk=tail__mode=nearhard__thr=0p66__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269981 | 0.807238 | -0.001413 | -0.000892 | -0.001600 |
| ppopt187_hard_risk_router__risk=gap_heavy__mode=nearhard__thr=0p66__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269986 | 0.807231 | -0.001409 | -0.000899 | -0.001599 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=nearhard__thr=0p66__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269977 | 0.807243 | -0.001418 | -0.000887 | -0.001598 |
| ppopt187_hard_risk_router__risk=tail__mode=nearhard__thr=0p66__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269991 | 0.807231 | -0.001404 | -0.000899 | -0.001597 |
| ppopt187_hard_risk_router__risk=conservative__mode=nearhard__thr=0p66__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269987 | 0.807231 | -0.001408 | -0.000899 | -0.001596 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=nearhard__thr=0p72__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269981 | 0.807231 | -0.001414 | -0.000899 | -0.001596 |
| ppopt187_hard_risk_router__risk=tail__mode=nearhard__thr=0p6__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269985 | 0.807235 | -0.001410 | -0.000895 | -0.001596 |
| ppopt187_hard_risk_router__risk=tail__mode=hard__thr=0p72__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269987 | 0.807231 | -0.001408 | -0.000899 | -0.001595 |
| ppopt187_hard_risk_router__risk=tail__mode=hard__thr=0p72__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269987 | 0.807231 | -0.001408 | -0.000899 | -0.001595 |
| ppopt187_hard_risk_router__risk=tail__mode=hard__thr=0p72__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269987 | 0.807231 | -0.001408 | -0.000899 | -0.001595 |
| ppopt187_hard_risk_router__risk=conservative__mode=hard__thr=0p72__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269992 | 0.807231 | -0.001403 | -0.000899 | -0.001595 |
| ppopt187_hard_risk_router__risk=conservative__mode=hard__thr=0p72__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269992 | 0.807231 | -0.001403 | -0.000899 | -0.001595 |
| ppopt187_hard_risk_router__risk=conservative__mode=hard__thr=0p72__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269992 | 0.807231 | -0.001403 | -0.000899 | -0.001595 |
| ppopt187_hard_risk_router__risk=gap_heavy__mode=hard__thr=0p72__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269985 | 0.807231 | -0.001409 | -0.000899 | -0.001595 |
| ppopt187_hard_risk_router__risk=gap_heavy__mode=hard__thr=0p72__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269985 | 0.807231 | -0.001409 | -0.000899 | -0.001595 |
| ppopt187_hard_risk_router__risk=gap_heavy__mode=hard__thr=0p72__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269985 | 0.807231 | -0.001409 | -0.000899 | -0.001595 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=hard__thr=0p72__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269992 | 0.807231 | -0.001403 | -0.000899 | -0.001595 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=hard__thr=0p72__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269992 | 0.807231 | -0.001403 | -0.000899 | -0.001595 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=hard__thr=0p72__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269992 | 0.807231 | -0.001403 | -0.000899 | -0.001595 |
| ppopt187_hard_risk_router__risk=conservative__mode=nearhard__thr=0p66__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269991 | 0.807231 | -0.001404 | -0.000899 | -0.001594 |
| ppopt187_hard_risk_router__risk=conservative__mode=nearhard__thr=0p66__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269969 | 0.807259 | -0.001426 | -0.000871 | -0.001594 |
| ppopt187_hard_risk_router__risk=conservative__mode=nearhard__thr=0p72__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269956 | 0.807276 | -0.001439 | -0.000854 | -0.001594 |
| ppopt187_hard_risk_router__risk=conservative__mode=nearhard__thr=0p6__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269989 | 0.807231 | -0.001406 | -0.000899 | -0.001593 |
| ppopt187_hard_risk_router__risk=tail__mode=nearhard__thr=0p6__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269991 | 0.807231 | -0.001404 | -0.000899 | -0.001593 |
| ppopt187_hard_risk_router__risk=gap_heavy__mode=nearhard__thr=0p66__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269988 | 0.807231 | -0.001407 | -0.000899 | -0.001592 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=nearhard__thr=0p66__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269990 | 0.807231 | -0.001405 | -0.000899 | -0.001592 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=nearhard__thr=0p54__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269985 | 0.807231 | -0.001410 | -0.000899 | -0.001592 |
| ppopt187_hard_risk_router__risk=tail__mode=hard__thr=0p66__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269991 | 0.807231 | -0.001404 | -0.000899 | -0.001591 |
| ppopt187_hard_risk_router__risk=tail__mode=hard__thr=0p66__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269991 | 0.807231 | -0.001404 | -0.000899 | -0.001591 |
| ppopt187_hard_risk_router__risk=tail__mode=hard__thr=0p66__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269991 | 0.807231 | -0.001404 | -0.000899 | -0.001591 |
| ppopt187_hard_risk_router__risk=gap_heavy__mode=nearhard__thr=0p6__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269985 | 0.807231 | -0.001410 | -0.000899 | -0.001591 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=nearhard__thr=0p66__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269990 | 0.807231 | -0.001405 | -0.000899 | -0.001590 |
| ppopt187_hard_risk_router__risk=tail__mode=hard__thr=0p6__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269992 | 0.807231 | -0.001403 | -0.000899 | -0.001590 |
| ppopt187_hard_risk_router__risk=tail__mode=hard__thr=0p6__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269992 | 0.807231 | -0.001403 | -0.000899 | -0.001590 |
| ppopt187_hard_risk_router__risk=tail__mode=hard__thr=0p6__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269992 | 0.807231 | -0.001403 | -0.000899 | -0.001590 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=hard__thr=0p66__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269989 | 0.807231 | -0.001406 | -0.000899 | -0.001590 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=hard__thr=0p66__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269989 | 0.807231 | -0.001406 | -0.000899 | -0.001590 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=hard__thr=0p66__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269989 | 0.807231 | -0.001406 | -0.000899 | -0.001590 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=nearhard__thr=0p54__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269987 | 0.807231 | -0.001408 | -0.000899 | -0.001590 |
| ppopt187_hard_risk_router__risk=gap_heavy__mode=nearhard__thr=0p54__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269984 | 0.807231 | -0.001411 | -0.000899 | -0.001590 |
| ppopt187_hard_risk_router__risk=conservative__mode=nearhard__thr=0p6__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269991 | 0.807231 | -0.001404 | -0.000899 | -0.001589 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=nearhard__thr=0p6__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269989 | 0.807231 | -0.001406 | -0.000899 | -0.001589 |
| ppopt187_hard_risk_router__risk=tail__mode=nearhard__thr=0p54__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269992 | 0.807231 | -0.001403 | -0.000899 | -0.001589 |
| ppopt187_hard_risk_router__risk=tail__mode=nearhard__thr=0p6__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269990 | 0.807231 | -0.001405 | -0.000899 | -0.001589 |
| ppopt187_hard_risk_router__risk=conservative__mode=nearhard__thr=0p54__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269990 | 0.807231 | -0.001405 | -0.000899 | -0.001587 |
| ppopt187_hard_risk_router__risk=conservative__mode=hard__thr=0p66__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269990 | 0.807231 | -0.001405 | -0.000899 | -0.001587 |
| ppopt187_hard_risk_router__risk=conservative__mode=hard__thr=0p66__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269990 | 0.807231 | -0.001405 | -0.000899 | -0.001587 |
| ppopt187_hard_risk_router__risk=conservative__mode=hard__thr=0p66__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269990 | 0.807231 | -0.001405 | -0.000899 | -0.001587 |
| ppopt187_hard_risk_router__risk=conservative__mode=nearhard__thr=0p6__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269992 | 0.807231 | -0.001403 | -0.000899 | -0.001586 |
| ppopt187_hard_risk_router__risk=tail__mode=nearhard__thr=0p54__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269993 | 0.807231 | -0.001402 | -0.000899 | -0.001586 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=nearhard__thr=0p6__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269988 | 0.807231 | -0.001406 | -0.000899 | -0.001586 |
| ppopt187_hard_risk_router__risk=conservative__mode=nearhard__thr=0p54__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269991 | 0.807231 | -0.001404 | -0.000899 | -0.001585 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=nearhard__thr=0p6__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269988 | 0.807231 | -0.001407 | -0.000899 | -0.001584 |
| ppopt187_hard_risk_router__risk=conservative__mode=nearhard__thr=0p54__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269989 | 0.807231 | -0.001406 | -0.000899 | -0.001584 |
| ppopt187_hard_risk_router__risk=tail__mode=nearhard__thr=0p54__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269995 | 0.807231 | -0.001400 | -0.000899 | -0.001584 |
| ppopt187_hard_risk_router__risk=gap_heavy__mode=nearhard__thr=0p54__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269982 | 0.807231 | -0.001413 | -0.000899 | -0.001583 |
| ppopt187_hard_risk_router__risk=gap_heavy__mode=nearhard__thr=0p6__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269986 | 0.807231 | -0.001409 | -0.000899 | -0.001583 |
| ppopt187_hard_risk_router__risk=gap_heavy__mode=hard__thr=0p66__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269990 | 0.807231 | -0.001405 | -0.000899 | -0.001582 |
| ppopt187_hard_risk_router__risk=gap_heavy__mode=hard__thr=0p66__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269990 | 0.807231 | -0.001405 | -0.000899 | -0.001582 |
| ppopt187_hard_risk_router__risk=gap_heavy__mode=hard__thr=0p66__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269990 | 0.807231 | -0.001405 | -0.000899 | -0.001582 |
| ppopt187_hard_risk_router__risk=conservative__mode=hard__thr=0p6__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001581 |
| ppopt187_hard_risk_router__risk=conservative__mode=hard__thr=0p6__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001581 |
| ppopt187_hard_risk_router__risk=conservative__mode=hard__thr=0p6__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001581 |
| ppopt187_hard_risk_router__risk=gap_heavy__mode=nearhard__thr=0p6__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269984 | 0.807231 | -0.001411 | -0.000899 | -0.001578 |
| ppopt187_hard_risk_router__risk=tail__mode=nearhard__thr=0p66__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269964 | 0.807271 | -0.001430 | -0.000859 | -0.001574 |
| ppopt187_hard_risk_router__risk=gap_heavy__mode=hard__thr=0p54__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269976 | 0.807231 | -0.001419 | -0.000899 | -0.001571 |
| ppopt187_hard_risk_router__risk=gap_heavy__mode=hard__thr=0p54__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269976 | 0.807231 | -0.001419 | -0.000899 | -0.001571 |
| ppopt187_hard_risk_router__risk=gap_heavy__mode=hard__thr=0p54__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269976 | 0.807231 | -0.001419 | -0.000899 | -0.001571 |
| ppopt187_hard_risk_router__risk=gap_heavy__mode=nearhard__thr=0p66__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269969 | 0.807255 | -0.001426 | -0.000875 | -0.001567 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=hard__thr=0p54__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269976 | 0.807231 | -0.001419 | -0.000899 | -0.001565 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=hard__thr=0p54__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269976 | 0.807231 | -0.001419 | -0.000899 | -0.001565 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=hard__thr=0p54__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269976 | 0.807231 | -0.001419 | -0.000899 | -0.001565 |
| ppopt187_hard_risk_router__risk=tail__mode=nearhard__thr=0p72__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269948 | 0.807294 | -0.001446 | -0.000836 | -0.001560 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=nearhard__thr=0p54__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269984 | 0.807231 | -0.001411 | -0.000899 | -0.001555 |
| ppopt187_hard_risk_router__risk=gap_heavy__mode=nearhard__thr=0p72__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269957 | 0.807270 | -0.001438 | -0.000860 | -0.001552 |
| ppopt187_hard_risk_router__risk=gap_heavy__mode=nearhard__thr=0p54__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269980 | 0.807231 | -0.001415 | -0.000899 | -0.001551 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=hard__thr=0p6__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269990 | 0.807231 | -0.001405 | -0.000899 | -0.001550 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=hard__thr=0p6__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269990 | 0.807231 | -0.001405 | -0.000899 | -0.001550 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=hard__thr=0p6__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269990 | 0.807231 | -0.001405 | -0.000899 | -0.001550 |
| ppopt187_hard_risk_router__risk=gap_heavy__mode=hard__thr=0p78__w=0p06__s=0p75 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269948 | 0.807326 | -0.001446 | -0.000804 | -0.001547 |
| ppopt187_hard_risk_router__risk=gap_heavy__mode=hard__thr=0p78__w=0p16__s=0p75 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269948 | 0.807326 | -0.001446 | -0.000804 | -0.001547 |
| ppopt187_hard_risk_router__risk=gap_heavy__mode=hard__thr=0p78__w=0p1__s=0p75 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269948 | 0.807326 | -0.001446 | -0.000804 | -0.001547 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=nearhard__thr=0p72__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269953 | 0.807278 | -0.001442 | -0.000852 | -0.001546 |
| ppopt187_hard_risk_router__risk=gap_heavy__mode=hard__thr=0p54__w=0p06__s=0p75 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269965 | 0.807255 | -0.001430 | -0.000875 | -0.001546 |
| ppopt187_hard_risk_router__risk=gap_heavy__mode=hard__thr=0p54__w=0p16__s=0p75 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269965 | 0.807255 | -0.001430 | -0.000875 | -0.001546 |
| ppopt187_hard_risk_router__risk=gap_heavy__mode=hard__thr=0p54__w=0p1__s=0p75 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269965 | 0.807255 | -0.001430 | -0.000875 | -0.001546 |
| ppopt187_hard_risk_router__risk=conservative__mode=hard__thr=0p54__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269982 | 0.807231 | -0.001413 | -0.000899 | -0.001545 |
| ppopt187_hard_risk_router__risk=conservative__mode=hard__thr=0p54__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269982 | 0.807231 | -0.001413 | -0.000899 | -0.001545 |
| ppopt187_hard_risk_router__risk=conservative__mode=hard__thr=0p54__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269982 | 0.807231 | -0.001413 | -0.000899 | -0.001545 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=hard__thr=0p54__w=0p06__s=0p75 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269965 | 0.807255 | -0.001430 | -0.000875 | -0.001541 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=hard__thr=0p54__w=0p16__s=0p75 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269965 | 0.807255 | -0.001430 | -0.000875 | -0.001541 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=hard__thr=0p54__w=0p1__s=0p75 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269965 | 0.807255 | -0.001430 | -0.000875 | -0.001541 |
| ppopt187_hard_risk_router__risk=uncertainty__mode=nearhard__thr=0p78__w=0p06__s=0p75 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269940 | 0.807302 | -0.001455 | -0.000828 | -0.001541 |
| ppopt187_hard_risk_router__risk=conservative__mode=hard__thr=0p78__w=0p06__s=0p75 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269948 | 0.807326 | -0.001447 | -0.000804 | -0.001541 |
| ppopt187_hard_risk_router__risk=conservative__mode=hard__thr=0p78__w=0p16__s=0p75 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269948 | 0.807326 | -0.001447 | -0.000804 | -0.001541 |
| ppopt187_hard_risk_router__risk=conservative__mode=hard__thr=0p78__w=0p1__s=0p75 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269948 | 0.807326 | -0.001447 | -0.000804 | -0.001541 |
| ppopt187_hard_risk_router__risk=tail__mode=hard__thr=0p54__w=0p06__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269988 | 0.807231 | -0.001407 | -0.000899 | -0.001540 |
| ppopt187_hard_risk_router__risk=tail__mode=hard__thr=0p54__w=0p16__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269988 | 0.807231 | -0.001407 | -0.000899 | -0.001540 |
| ppopt187_hard_risk_router__risk=tail__mode=hard__thr=0p54__w=0p1__s=1p0 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269988 | 0.807231 | -0.001407 | -0.000899 | -0.001540 |
| ppopt187_hard_risk_router__risk=tail__mode=hard__thr=0p78__w=0p06__s=0p75 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269932 | 0.807326 | -0.001463 | -0.000804 | -0.001540 |
| ppopt187_hard_risk_router__risk=tail__mode=hard__thr=0p78__w=0p16__s=0p75 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269932 | 0.807326 | -0.001463 | -0.000804 | -0.001540 |
| ppopt187_hard_risk_router__risk=tail__mode=hard__thr=0p78__w=0p1__s=0p75 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269932 | 0.807326 | -0.001463 | -0.000804 | -0.001540 |
| ppopt187_hard_risk_router__risk=gap_heavy__mode=nearhard__thr=0p72__w=0p06__s=0p75 | PP-OPT187 | pp180_pp186_hard_risk_router | 0.269962 | 0.807256 | -0.001432 | -0.000874 | -0.001540 |

## 선택 후보 반복 안정성
| candidate_label | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_vs_pp64_MAPE | fixed_test_delta_vs_pp64_p95_APE | avg_pp64_MAPE_win_rate | avg_pp64_p95_win_rate | replacement_score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| candidate_ppopt189_segment_router__seg_price_gap__scorethr_0p02__mix_0p75__s_0p95__cap_0p0025__0b3e477775 | 0.269914 | 0.807326 | -0.000650 | -0.000173 | 0.953526 | 0.750962 | -0.018791 |
| candidate_ppopt189_segment_router__seg_price_gap__scorethr_0p02__mix_0p75__s_0p95__cap_0p004__da9d24b993 | 0.269914 | 0.807326 | -0.000650 | -0.000173 | 0.953526 | 0.750962 | -0.018791 |
| candidate_ppopt189_segment_router__seg_price_gap__scorethr_0p02__mix_0p75__s_0p95__cap_0p006__10a4bf115c | 0.269914 | 0.807326 | -0.000650 | -0.000173 | 0.953526 | 0.750962 | -0.018791 |
| pp192_operational_pp180_pp186_risk_router_challenger | 0.269914 | 0.807326 | -0.000650 | -0.000173 | 0.953526 | 0.750962 | -0.018791 |
| candidate_ppopt189_segment_router__seg_price_gap__scorethr_m0p08__mix_0p75__s_0p95__cap_0p0025__aea7273ed9 | 0.269915 | 0.807326 | -0.000650 | -0.000173 | 0.953526 | 0.750962 | -0.018791 |
| candidate_ppopt189_segment_router__seg_price_gap__scorethr_m0p08__mix_0p75__s_0p95__cap_0p004__f977f8eb4b | 0.269915 | 0.807326 | -0.000650 | -0.000173 | 0.953526 | 0.750962 | -0.018791 |
| candidate_ppopt189_segment_router__seg_price_gap__scorethr_m0p08__mix_0p75__s_0p95__cap_0p006__fdc3e647fc | 0.269915 | 0.807326 | -0.000650 | -0.000173 | 0.953526 | 0.750962 | -0.018791 |
| candidate_ppopt189_segment_router__seg_price_gap__scorethr_m0p18__mix_0p75__s_0p95__cap_0p0025__9fc8d1dea4 | 0.269915 | 0.807326 | -0.000650 | -0.000173 | 0.953526 | 0.750962 | -0.018791 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p02__mix_0p35__s_0p95__cap_0p0025__96f97bb645 | 0.269909 | 0.807326 | -0.000655 | -0.000173 | 0.952885 | 0.750962 | -0.018770 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p02__mix_0p55__s_0p95__cap_0p0025__20351d3c86 | 0.269909 | 0.807326 | -0.000655 | -0.000173 | 0.952885 | 0.750962 | -0.018770 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p02__mix_0p75__s_0p95__cap_0p0025__14534fbbc2 | 0.269909 | 0.807326 | -0.000655 | -0.000173 | 0.952885 | 0.750962 | -0.018770 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p08__mix_0p35__s_0p95__cap_0p0025__172719efe6 | 0.269909 | 0.807326 | -0.000655 | -0.000173 | 0.952885 | 0.750962 | -0.018770 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p08__mix_0p55__s_0p95__cap_0p0025__6d7ae6569d | 0.269909 | 0.807326 | -0.000655 | -0.000173 | 0.952885 | 0.750962 | -0.018770 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p08__mix_0p75__s_0p95__cap_0p0025__73913d537f | 0.269909 | 0.807326 | -0.000655 | -0.000173 | 0.952885 | 0.750962 | -0.018770 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p18__mix_0p35__s_0p95__cap_0p0025__c93eff3dfe | 0.269909 | 0.807326 | -0.000655 | -0.000173 | 0.952885 | 0.750962 | -0.018770 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p18__mix_0p55__s_0p95__cap_0p0025__afcdfc8634 | 0.269909 | 0.807326 | -0.000655 | -0.000173 | 0.952885 | 0.750962 | -0.018770 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p18__mix_0p75__s_0p95__cap_0p0025__af25daec9a | 0.269909 | 0.807326 | -0.000655 | -0.000173 | 0.952885 | 0.750962 | -0.018770 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p02__mix_0p35__s_0p75__cap_0p0025__345786adeb | 0.269910 | 0.807326 | -0.000654 | -0.000173 | 0.952885 | 0.750962 | -0.018770 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p02__mix_0p55__s_0p75__cap_0p0025__de56d70e7c | 0.269910 | 0.807326 | -0.000654 | -0.000173 | 0.952885 | 0.750962 | -0.018770 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p02__mix_0p75__s_0p75__cap_0p0025__bd859972fe | 0.269910 | 0.807326 | -0.000654 | -0.000173 | 0.952885 | 0.750962 | -0.018770 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p08__mix_0p35__s_0p75__cap_0p0025__26a542449d | 0.269910 | 0.807326 | -0.000654 | -0.000173 | 0.952885 | 0.750962 | -0.018770 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p08__mix_0p55__s_0p75__cap_0p0025__2407d17da0 | 0.269910 | 0.807326 | -0.000654 | -0.000173 | 0.952885 | 0.750962 | -0.018770 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p08__mix_0p75__s_0p75__cap_0p0025__b4220f6414 | 0.269910 | 0.807326 | -0.000654 | -0.000173 | 0.952885 | 0.750962 | -0.018770 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p18__mix_0p35__s_0p75__cap_0p0025__d2707fc5be | 0.269910 | 0.807326 | -0.000654 | -0.000173 | 0.952885 | 0.750962 | -0.018770 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p18__mix_0p55__s_0p75__cap_0p0025__05184e2d58 | 0.269910 | 0.807326 | -0.000654 | -0.000173 | 0.952885 | 0.750962 | -0.018770 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p18__mix_0p75__s_0p75__cap_0p0025__a6f171be1d | 0.269910 | 0.807326 | -0.000654 | -0.000173 | 0.952885 | 0.750962 | -0.018770 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p12__mix_0p35__s_0p95__cap_0p0025__1b6714a2a9 | 0.269911 | 0.807323 | -0.000653 | -0.000175 | 0.952885 | 0.750962 | -0.018769 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p12__mix_0p55__s_0p95__cap_0p0025__a91bb18eef | 0.269911 | 0.807323 | -0.000653 | -0.000175 | 0.952885 | 0.750962 | -0.018769 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p12__mix_0p75__s_0p95__cap_0p0025__b76e61a1f3 | 0.269911 | 0.807323 | -0.000653 | -0.000175 | 0.952885 | 0.750962 | -0.018769 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p12__mix_0p35__s_0p75__cap_0p0025__fae37d8e38 | 0.269911 | 0.807324 | -0.000653 | -0.000175 | 0.952885 | 0.750962 | -0.018769 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p12__mix_0p55__s_0p75__cap_0p0025__a730ebe39a | 0.269911 | 0.807324 | -0.000653 | -0.000175 | 0.952885 | 0.750962 | -0.018769 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p12__mix_0p75__s_0p75__cap_0p0025__741a7bf0a0 | 0.269911 | 0.807324 | -0.000653 | -0.000175 | 0.952885 | 0.750962 | -0.018769 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p02__mix_0p35__s_0p95__cap_0p004__32f7f7e4c1 | 0.269899 | 0.807326 | -0.000665 | -0.000173 | 0.952564 | 0.749679 | -0.018767 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p02__mix_0p55__s_0p95__cap_0p004__33f722d077 | 0.269899 | 0.807326 | -0.000665 | -0.000173 | 0.952564 | 0.749679 | -0.018767 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p02__mix_0p75__s_0p95__cap_0p004__b383bc94ca | 0.269899 | 0.807326 | -0.000665 | -0.000173 | 0.952564 | 0.749679 | -0.018767 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p08__mix_0p35__s_0p95__cap_0p004__29ce998c22 | 0.269899 | 0.807326 | -0.000665 | -0.000173 | 0.952564 | 0.749679 | -0.018767 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p08__mix_0p55__s_0p95__cap_0p004__eb881fb7d6 | 0.269899 | 0.807326 | -0.000665 | -0.000173 | 0.952564 | 0.749679 | -0.018767 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p08__mix_0p75__s_0p95__cap_0p004__2146143cc4 | 0.269899 | 0.807326 | -0.000665 | -0.000173 | 0.952564 | 0.749679 | -0.018767 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p18__mix_0p35__s_0p95__cap_0p004__ea2e4a4065 | 0.269899 | 0.807326 | -0.000665 | -0.000173 | 0.952564 | 0.749679 | -0.018767 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p18__mix_0p55__s_0p95__cap_0p004__e01b15d2d9 | 0.269899 | 0.807326 | -0.000665 | -0.000173 | 0.952564 | 0.749679 | -0.018767 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p18__mix_0p75__s_0p95__cap_0p004__9e9626b029 | 0.269899 | 0.807326 | -0.000665 | -0.000173 | 0.952564 | 0.749679 | -0.018767 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p02__mix_0p35__s_0p55__cap_0p0025__386885071f | 0.269912 | 0.807326 | -0.000652 | -0.000173 | 0.952885 | 0.750962 | -0.018767 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p02__mix_0p35__s_0p55__cap_0p004__4f14b8d8d4 | 0.269912 | 0.807326 | -0.000652 | -0.000173 | 0.952885 | 0.750962 | -0.018767 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p02__mix_0p35__s_0p55__cap_0p006__8b2b41e001 | 0.269912 | 0.807326 | -0.000652 | -0.000173 | 0.952885 | 0.750962 | -0.018767 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p02__mix_0p55__s_0p55__cap_0p0025__4997333933 | 0.269912 | 0.807326 | -0.000652 | -0.000173 | 0.952885 | 0.750962 | -0.018767 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p02__mix_0p55__s_0p55__cap_0p004__116851da2c | 0.269912 | 0.807326 | -0.000652 | -0.000173 | 0.952885 | 0.750962 | -0.018767 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p02__mix_0p55__s_0p55__cap_0p006__f8c59691bf | 0.269912 | 0.807326 | -0.000652 | -0.000173 | 0.952885 | 0.750962 | -0.018767 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p02__mix_0p75__s_0p55__cap_0p0025__1dcf940144 | 0.269912 | 0.807326 | -0.000652 | -0.000173 | 0.952885 | 0.750962 | -0.018767 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p02__mix_0p75__s_0p55__cap_0p004__216023d975 | 0.269912 | 0.807326 | -0.000652 | -0.000173 | 0.952885 | 0.750962 | -0.018767 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p02__mix_0p35__s_0p75__cap_0p004__065fa8d112 | 0.269905 | 0.807326 | -0.000659 | -0.000173 | 0.952564 | 0.750641 | -0.018762 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p02__mix_0p35__s_0p75__cap_0p006__1fe2ccf362 | 0.269905 | 0.807326 | -0.000659 | -0.000173 | 0.952564 | 0.750641 | -0.018762 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p02__mix_0p55__s_0p75__cap_0p004__00b1b2c2ed | 0.269905 | 0.807326 | -0.000659 | -0.000173 | 0.952564 | 0.750641 | -0.018762 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p02__mix_0p55__s_0p75__cap_0p006__e9c86b7e9b | 0.269905 | 0.807326 | -0.000659 | -0.000173 | 0.952564 | 0.750641 | -0.018762 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p02__mix_0p75__s_0p75__cap_0p004__2fd035ba0d | 0.269905 | 0.807326 | -0.000659 | -0.000173 | 0.952564 | 0.750641 | -0.018762 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p02__mix_0p75__s_0p75__cap_0p006__3bb8fe07b5 | 0.269905 | 0.807326 | -0.000659 | -0.000173 | 0.952564 | 0.750641 | -0.018762 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p08__mix_0p35__s_0p75__cap_0p004__c9fcd2f25e | 0.269905 | 0.807326 | -0.000659 | -0.000173 | 0.952564 | 0.750641 | -0.018762 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p08__mix_0p35__s_0p75__cap_0p006__b6a6dbe439 | 0.269905 | 0.807326 | -0.000659 | -0.000173 | 0.952564 | 0.750641 | -0.018762 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p08__mix_0p55__s_0p75__cap_0p004__8ea2003e67 | 0.269905 | 0.807326 | -0.000659 | -0.000173 | 0.952564 | 0.750641 | -0.018762 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p08__mix_0p55__s_0p75__cap_0p006__6b97135617 | 0.269905 | 0.807326 | -0.000659 | -0.000173 | 0.952564 | 0.750641 | -0.018762 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p08__mix_0p75__s_0p75__cap_0p004__e2b67c9de2 | 0.269905 | 0.807326 | -0.000659 | -0.000173 | 0.952564 | 0.750641 | -0.018762 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p08__mix_0p75__s_0p75__cap_0p006__fa9d640816 | 0.269905 | 0.807326 | -0.000659 | -0.000173 | 0.952564 | 0.750641 | -0.018762 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p18__mix_0p35__s_0p75__cap_0p004__961f941b08 | 0.269905 | 0.807326 | -0.000659 | -0.000173 | 0.952564 | 0.750641 | -0.018762 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p18__mix_0p35__s_0p75__cap_0p006__4806099866 | 0.269905 | 0.807326 | -0.000659 | -0.000173 | 0.952564 | 0.750641 | -0.018762 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p18__mix_0p55__s_0p75__cap_0p004__e4152939fa | 0.269905 | 0.807326 | -0.000659 | -0.000173 | 0.952564 | 0.750641 | -0.018762 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p18__mix_0p55__s_0p75__cap_0p006__2f6f1a6f35 | 0.269905 | 0.807326 | -0.000659 | -0.000173 | 0.952564 | 0.750641 | -0.018762 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p18__mix_0p75__s_0p75__cap_0p004__99937593cc | 0.269905 | 0.807326 | -0.000659 | -0.000173 | 0.952564 | 0.750641 | -0.018762 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p18__mix_0p75__s_0p75__cap_0p006__7d01e59159 | 0.269905 | 0.807326 | -0.000659 | -0.000173 | 0.952564 | 0.750641 | -0.018762 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p12__mix_0p35__s_0p75__cap_0p004__187e374baa | 0.269906 | 0.807324 | -0.000658 | -0.000175 | 0.952564 | 0.750641 | -0.018760 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p12__mix_0p35__s_0p75__cap_0p006__c869eb2922 | 0.269906 | 0.807324 | -0.000658 | -0.000175 | 0.952564 | 0.750641 | -0.018760 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p12__mix_0p55__s_0p75__cap_0p004__9c6e9c3673 | 0.269906 | 0.807324 | -0.000658 | -0.000175 | 0.952564 | 0.750641 | -0.018760 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p12__mix_0p55__s_0p75__cap_0p006__ef9119e58b | 0.269906 | 0.807324 | -0.000658 | -0.000175 | 0.952564 | 0.750641 | -0.018760 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p12__mix_0p75__s_0p75__cap_0p004__36f2b8d49f | 0.269906 | 0.807324 | -0.000658 | -0.000175 | 0.952564 | 0.750641 | -0.018760 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p12__mix_0p75__s_0p75__cap_0p006__e59814cb5a | 0.269906 | 0.807324 | -0.000658 | -0.000175 | 0.952564 | 0.750641 | -0.018760 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p02__mix_0p35__s_0p95__cap_0p006__5183e2f08b | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p02__mix_0p55__s_0p95__cap_0p006__45a9b62395 | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p02__mix_0p75__s_0p95__cap_0p006__bfc612e96d | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p08__mix_0p35__s_0p95__cap_0p006__d7f5e0b10b | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p08__mix_0p55__s_0p95__cap_0p006__13025a8404 | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p08__mix_0p75__s_0p95__cap_0p006__866ebb7f33 | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p18__mix_0p35__s_0p95__cap_0p006__19de26f53c | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p18__mix_0p55__s_0p95__cap_0p006__77d7f472bc | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_m0p18__mix_0p75__s_0p95__cap_0p006__0d247569ca | 0.269898 | 0.807326 | -0.000666 | -0.000173 | 0.952244 | 0.748718 | -0.018756 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p12__mix_0p35__s_0p95__cap_0p006__732dc29b40 | 0.269899 | 0.807323 | -0.000665 | -0.000175 | 0.952244 | 0.748718 | -0.018755 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p12__mix_0p55__s_0p95__cap_0p006__042d33284b | 0.269899 | 0.807323 | -0.000665 | -0.000175 | 0.952244 | 0.748718 | -0.018755 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p12__mix_0p75__s_0p95__cap_0p006__c07cfc7547 | 0.269899 | 0.807323 | -0.000665 | -0.000175 | 0.952244 | 0.748718 | -0.018755 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p12__mix_0p35__s_0p95__cap_0p004__3722d2f431 | 0.269900 | 0.807323 | -0.000664 | -0.000175 | 0.952244 | 0.749679 | -0.018753 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p12__mix_0p55__s_0p95__cap_0p004__8e6fe2d36a | 0.269900 | 0.807323 | -0.000664 | -0.000175 | 0.952244 | 0.749679 | -0.018753 |
| candidate_ppopt189_segment_router__seg_price_conf__scorethr_0p12__mix_0p75__s_0p95__cap_0p004__57f271b18c | 0.269900 | 0.807323 | -0.000664 | -0.000175 | 0.952244 | 0.749679 | -0.018753 |
| pp180_operational_reference | 0.269933 | 0.807326 | -0.000631 | -0.000173 | 0.952244 | 0.754487 | -0.018721 |
| candidate_ppopt187_hard_risk_router__risk_gap_heavy__mode_hard__thr_0p78__w_0p06__s_1p0__2500a89683 | 0.269954 | 0.807326 | -0.000610 | -0.000173 | 0.952564 | 0.743910 | -0.018712 |
| candidate_ppopt187_hard_risk_router__risk_gap_heavy__mode_hard__thr_0p78__w_0p16__s_1p0__d723904934 | 0.269954 | 0.807326 | -0.000610 | -0.000173 | 0.952564 | 0.743910 | -0.018712 |
| candidate_ppopt187_hard_risk_router__risk_gap_heavy__mode_hard__thr_0p78__w_0p1__s_1p0__92b0d7855e | 0.269954 | 0.807326 | -0.000610 | -0.000173 | 0.952564 | 0.743910 | -0.018712 |
| candidate_ppopt187_hard_risk_router__risk_tail__mode_hard__thr_0p78__w_0p06__s_1p0__70c8a37788 | 0.269932 | 0.807326 | -0.000632 | -0.000173 | 0.951923 | 0.739744 | -0.018709 |
| candidate_ppopt187_hard_risk_router__risk_tail__mode_hard__thr_0p78__w_0p16__s_1p0__e6b1a7537f | 0.269932 | 0.807326 | -0.000632 | -0.000173 | 0.951923 | 0.739744 | -0.018709 |
| candidate_ppopt187_hard_risk_router__risk_tail__mode_hard__thr_0p78__w_0p1__s_1p0__710e6a0e18 | 0.269932 | 0.807326 | -0.000632 | -0.000173 | 0.951923 | 0.739744 | -0.018709 |
| candidate_ppopt187_hard_risk_router__risk_uncertainty__mode_nearhard__thr_0p78__w_0p06__s_1p0__fb6b4226a2 | 0.269943 | 0.807295 | -0.000621 | -0.000204 | 0.951923 | 0.743910 | -0.018698 |
| candidate_ppopt187_hard_risk_router__risk_gap_heavy__mode_nearhard__thr_0p72__w_0p06__s_1p0__a91309d183 | 0.269973 | 0.807233 | -0.000591 | -0.000266 | 0.952244 | 0.744231 | -0.018681 |
| candidate_ppopt187_hard_risk_router__risk_conservative__mode_hard__thr_0p78__w_0p06__s_1p0__d9625672de | 0.269953 | 0.807326 | -0.000611 | -0.000173 | 0.951603 | 0.743910 | -0.018675 |
| candidate_ppopt187_hard_risk_router__risk_conservative__mode_hard__thr_0p78__w_0p16__s_1p0__5e19fbd42a | 0.269953 | 0.807326 | -0.000611 | -0.000173 | 0.951603 | 0.743910 | -0.018675 |
| candidate_ppopt187_hard_risk_router__risk_conservative__mode_hard__thr_0p78__w_0p1__s_1p0__0cb37578ef | 0.269953 | 0.807326 | -0.000611 | -0.000173 | 0.951603 | 0.743910 | -0.018675 |
| candidate_ppopt187_hard_risk_router__risk_uncertainty__mode_hard__thr_0p78__w_0p06__s_0p75__c244d965f9 | 0.269949 | 0.807255 | -0.000615 | -0.000244 | 0.950962 | 0.751603 | -0.018653 |
| candidate_ppopt187_hard_risk_router__risk_uncertainty__mode_hard__thr_0p78__w_0p16__s_0p75__e9313e1c35 | 0.269949 | 0.807255 | -0.000615 | -0.000244 | 0.950962 | 0.751603 | -0.018653 |
| candidate_ppopt187_hard_risk_router__risk_uncertainty__mode_hard__thr_0p78__w_0p1__s_0p75__d2fe1bc819 | 0.269949 | 0.807255 | -0.000615 | -0.000244 | 0.950962 | 0.751603 | -0.018653 |
| pp192_p95_guarded_pp180_pp186_risk_router_challenger | 0.269949 | 0.807255 | -0.000615 | -0.000244 | 0.950962 | 0.751603 | -0.018653 |
| candidate_ppopt187_hard_risk_router__risk_uncertainty__mode_hard__thr_0p78__w_0p06__s_1p0__1c9562cc2b | 0.269955 | 0.807231 | -0.000609 | -0.000268 | 0.950962 | 0.731731 | -0.018647 |
| candidate_ppopt187_hard_risk_router__risk_uncertainty__mode_hard__thr_0p78__w_0p16__s_1p0__09799f037f | 0.269955 | 0.807231 | -0.000609 | -0.000268 | 0.950962 | 0.731731 | -0.018647 |
| candidate_ppopt187_hard_risk_router__risk_uncertainty__mode_hard__thr_0p78__w_0p1__s_1p0__8cd5a773b2 | 0.269955 | 0.807231 | -0.000609 | -0.000268 | 0.950962 | 0.731731 | -0.018647 |
| candidate_ppopt187_hard_risk_router__risk_conservative__mode_nearhard__thr_0p72__w_0p1__s_1p0__dbb0d6dd65 | 0.269956 | 0.807276 | -0.000608 | -0.000223 | 0.950962 | 0.740064 | -0.018646 |
| candidate_ppopt187_hard_risk_router__risk_tail__mode_nearhard__thr_0p72__w_0p06__s_1p0__5dcc05f73f | 0.269961 | 0.807274 | -0.000603 | -0.000225 | 0.950641 | 0.736538 | -0.018629 |
| candidate_ppopt190_gap_hazard_rollback__risk_uncertainty__gapthr_0p76__stable_0p25__s_0p7__cap_0p0015__b7c4959a20 | 0.269951 | 0.807259 | -0.000613 | -0.000240 | 0.950000 | 0.745513 | -0.018613 |
| candidate_ppopt190_gap_hazard_rollback__risk_conservative__gapthr_0p76__stable_0p25__s_0p7__cap_0p0015__7ae22c9006 | 0.269951 | 0.807259 | -0.000613 | -0.000240 | 0.950000 | 0.745513 | -0.018613 |
| candidate_ppopt187_hard_risk_router__risk_tail__mode_nearhard__thr_0p66__w_0p16__s_1p0__4673e419bc | 0.269964 | 0.807271 | -0.000600 | -0.000228 | 0.950321 | 0.740064 | -0.018612 |
| candidate_ppopt190_gap_hazard_rollback__risk_uncertainty__gapthr_0p76__stable_0p25__s_0p7__cap_0p004__4bd6d9aace | 0.269953 | 0.807259 | -0.000611 | -0.000240 | 0.950000 | 0.744551 | -0.018611 |
| candidate_ppopt190_gap_hazard_rollback__risk_uncertainty__gapthr_0p76__stable_0p45__s_0p7__cap_0p004__a72ffa358c | 0.269953 | 0.807259 | -0.000611 | -0.000240 | 0.950000 | 0.744551 | -0.018611 |
| candidate_ppopt190_gap_hazard_rollback__risk_gap_heavy__gapthr_0p76__stable_0p25__s_0p7__cap_0p004__c47a00470a | 0.269953 | 0.807259 | -0.000611 | -0.000240 | 0.950000 | 0.744551 | -0.018611 |
| candidate_ppopt190_gap_hazard_rollback__risk_uncertainty__gapthr_0p52__stable_0p25__s_0p7__cap_0p004__ff2642cfbd | 0.269953 | 0.807259 | -0.000611 | -0.000240 | 0.950000 | 0.744551 | -0.018611 |
| candidate_ppopt190_gap_hazard_rollback__risk_uncertainty__gapthr_0p52__stable_0p45__s_0p7__cap_0p004__fc48494d86 | 0.269953 | 0.807259 | -0.000611 | -0.000240 | 0.950000 | 0.744551 | -0.018611 |
| candidate_ppopt190_gap_hazard_rollback__risk_uncertainty__gapthr_0p68__stable_0p25__s_0p7__cap_0p004__ccf6d5b489 | 0.269953 | 0.807259 | -0.000611 | -0.000240 | 0.950000 | 0.744551 | -0.018611 |
| candidate_ppopt190_gap_hazard_rollback__risk_uncertainty__gapthr_0p68__stable_0p45__s_0p7__cap_0p004__735bd8c93e | 0.269953 | 0.807259 | -0.000611 | -0.000240 | 0.950000 | 0.744551 | -0.018611 |
| candidate_ppopt190_gap_hazard_rollback__risk_uncertainty__gapthr_0p6__stable_0p25__s_0p7__cap_0p004__9c84702146 | 0.269953 | 0.807259 | -0.000611 | -0.000240 | 0.950000 | 0.744551 | -0.018611 |
| candidate_ppopt190_gap_hazard_rollback__risk_uncertainty__gapthr_0p6__stable_0p45__s_0p7__cap_0p004__4a17a2b190 | 0.269953 | 0.807259 | -0.000611 | -0.000240 | 0.950000 | 0.744551 | -0.018611 |
| candidate_ppopt190_gap_hazard_rollback__risk_conservative__gapthr_0p76__stable_0p25__s_0p7__cap_0p004__e38d1d9ab4 | 0.269954 | 0.807259 | -0.000611 | -0.000240 | 0.950000 | 0.744551 | -0.018611 |
| candidate_ppopt190_gap_hazard_rollback__risk_gap_heavy__gapthr_0p76__stable_0p45__s_0p7__cap_0p004__7255a4d83c | 0.269954 | 0.807259 | -0.000611 | -0.000240 | 0.950000 | 0.744551 | -0.018611 |
| candidate_ppopt190_gap_hazard_rollback__risk_conservative__gapthr_0p76__stable_0p45__s_0p7__cap_0p004__e7fa31448e | 0.269954 | 0.807259 | -0.000610 | -0.000240 | 0.950000 | 0.744551 | -0.018610 |
| candidate_ppopt190_gap_hazard_rollback__risk_gap_heavy__gapthr_0p52__stable_0p25__s_0p7__cap_0p004__01eb98089e | 0.269954 | 0.807259 | -0.000610 | -0.000240 | 0.950000 | 0.744551 | -0.018610 |
| candidate_ppopt190_gap_hazard_rollback__risk_gap_heavy__gapthr_0p52__stable_0p45__s_0p7__cap_0p004__1470dd096b | 0.269954 | 0.807259 | -0.000610 | -0.000240 | 0.950000 | 0.744551 | -0.018610 |
| candidate_ppopt190_gap_hazard_rollback__risk_gap_heavy__gapthr_0p68__stable_0p25__s_0p7__cap_0p004__07608b9edf | 0.269954 | 0.807259 | -0.000610 | -0.000240 | 0.950000 | 0.744551 | -0.018610 |
| candidate_ppopt190_gap_hazard_rollback__risk_gap_heavy__gapthr_0p68__stable_0p45__s_0p7__cap_0p004__5adac99d93 | 0.269954 | 0.807259 | -0.000610 | -0.000240 | 0.950000 | 0.744551 | -0.018610 |
| candidate_ppopt190_gap_hazard_rollback__risk_gap_heavy__gapthr_0p6__stable_0p25__s_0p7__cap_0p004__4a755ac615 | 0.269954 | 0.807259 | -0.000610 | -0.000240 | 0.950000 | 0.744551 | -0.018610 |
| candidate_ppopt190_gap_hazard_rollback__risk_gap_heavy__gapthr_0p6__stable_0p45__s_0p7__cap_0p004__8449b66e9b | 0.269954 | 0.807259 | -0.000610 | -0.000240 | 0.950000 | 0.744551 | -0.018610 |
| candidate_ppopt190_gap_hazard_rollback__risk_conservative__gapthr_0p52__stable_0p25__s_0p7__cap_0p004__6766dc03c2 | 0.269954 | 0.807259 | -0.000610 | -0.000240 | 0.950000 | 0.744551 | -0.018610 |
| candidate_ppopt190_gap_hazard_rollback__risk_conservative__gapthr_0p52__stable_0p45__s_0p7__cap_0p004__6e6bf6a4df | 0.269954 | 0.807259 | -0.000610 | -0.000240 | 0.950000 | 0.744551 | -0.018610 |
| candidate_ppopt190_gap_hazard_rollback__risk_conservative__gapthr_0p68__stable_0p25__s_0p7__cap_0p004__355319971a | 0.269954 | 0.807259 | -0.000610 | -0.000240 | 0.950000 | 0.744551 | -0.018610 |
| candidate_ppopt190_gap_hazard_rollback__risk_conservative__gapthr_0p68__stable_0p45__s_0p7__cap_0p004__9ecd9e4796 | 0.269954 | 0.807259 | -0.000610 | -0.000240 | 0.950000 | 0.744551 | -0.018610 |
| candidate_ppopt190_gap_hazard_rollback__risk_conservative__gapthr_0p6__stable_0p25__s_0p7__cap_0p004__d18ba7d23e | 0.269954 | 0.807259 | -0.000610 | -0.000240 | 0.950000 | 0.744551 | -0.018610 |
| candidate_ppopt190_gap_hazard_rollback__risk_conservative__gapthr_0p6__stable_0p45__s_0p7__cap_0p004__a6e424330d | 0.269954 | 0.807259 | -0.000610 | -0.000240 | 0.950000 | 0.744551 | -0.018610 |
| candidate_ppopt190_gap_hazard_rollback__risk_uncertainty__gapthr_0p76__stable_0p25__s_0p7__cap_0p0025__44607cb909 | 0.269954 | 0.807259 | -0.000610 | -0.000240 | 0.950000 | 0.744872 | -0.018610 |
| candidate_ppopt190_gap_hazard_rollback__risk_uncertainty__gapthr_0p76__stable_0p45__s_0p7__cap_0p0025__358aaaff10 | 0.269954 | 0.807259 | -0.000610 | -0.000240 | 0.950000 | 0.744872 | -0.018610 |
| candidate_ppopt190_gap_hazard_rollback__risk_conservative__gapthr_0p76__stable_0p25__s_0p7__cap_0p0025__92a2d70a0b | 0.269954 | 0.807259 | -0.000610 | -0.000240 | 0.950000 | 0.744872 | -0.018610 |
| candidate_ppopt190_gap_hazard_rollback__risk_uncertainty__gapthr_0p52__stable_0p25__s_0p7__cap_0p0025__e07866421b | 0.269954 | 0.807259 | -0.000610 | -0.000240 | 0.950000 | 0.744872 | -0.018610 |
| candidate_ppopt190_gap_hazard_rollback__risk_uncertainty__gapthr_0p52__stable_0p45__s_0p7__cap_0p0025__9c62ed3f18 | 0.269954 | 0.807259 | -0.000610 | -0.000240 | 0.950000 | 0.744872 | -0.018610 |
| candidate_ppopt190_gap_hazard_rollback__risk_uncertainty__gapthr_0p68__stable_0p25__s_0p7__cap_0p0025__0ad057bf9a | 0.269954 | 0.807259 | -0.000610 | -0.000240 | 0.950000 | 0.744872 | -0.018610 |
| candidate_ppopt190_gap_hazard_rollback__risk_uncertainty__gapthr_0p68__stable_0p45__s_0p7__cap_0p0025__07d0fa468d | 0.269954 | 0.807259 | -0.000610 | -0.000240 | 0.950000 | 0.744872 | -0.018610 |
| candidate_ppopt190_gap_hazard_rollback__risk_uncertainty__gapthr_0p6__stable_0p25__s_0p7__cap_0p0025__4c6ce56ca1 | 0.269954 | 0.807259 | -0.000610 | -0.000240 | 0.950000 | 0.744872 | -0.018610 |
| candidate_ppopt190_gap_hazard_rollback__risk_uncertainty__gapthr_0p6__stable_0p45__s_0p7__cap_0p0025__66e1f102da | 0.269954 | 0.807259 | -0.000610 | -0.000240 | 0.950000 | 0.744872 | -0.018610 |
| candidate_ppopt190_gap_hazard_rollback__risk_gap_heavy__gapthr_0p76__stable_0p25__s_0p7__cap_0p0025__86d1d1eec2 | 0.269954 | 0.807259 | -0.000610 | -0.000240 | 0.950000 | 0.744872 | -0.018610 |
| candidate_ppopt190_gap_hazard_rollback__risk_conservative__gapthr_0p76__stable_0p45__s_0p7__cap_0p0025__d51e978bf1 | 0.269954 | 0.807259 | -0.000610 | -0.000240 | 0.950000 | 0.744872 | -0.018610 |
| candidate_ppopt190_gap_hazard_rollback__risk_gap_heavy__gapthr_0p76__stable_0p45__s_0p7__cap_0p0025__6d700879fe | 0.269955 | 0.807259 | -0.000609 | -0.000240 | 0.950000 | 0.744872 | -0.018609 |
| candidate_ppopt190_gap_hazard_rollback__risk_conservative__gapthr_0p52__stable_0p25__s_0p7__cap_0p0025__dab3aaaf5e | 0.269955 | 0.807259 | -0.000609 | -0.000240 | 0.950000 | 0.744872 | -0.018609 |
| candidate_ppopt190_gap_hazard_rollback__risk_conservative__gapthr_0p52__stable_0p45__s_0p7__cap_0p0025__2c89adef1d | 0.269955 | 0.807259 | -0.000609 | -0.000240 | 0.950000 | 0.744872 | -0.018609 |
| candidate_ppopt190_gap_hazard_rollback__risk_conservative__gapthr_0p68__stable_0p25__s_0p7__cap_0p0025__a03eb73d71 | 0.269955 | 0.807259 | -0.000609 | -0.000240 | 0.950000 | 0.744872 | -0.018609 |
| candidate_ppopt190_gap_hazard_rollback__risk_conservative__gapthr_0p68__stable_0p45__s_0p7__cap_0p0025__e07ec6646e | 0.269955 | 0.807259 | -0.000609 | -0.000240 | 0.950000 | 0.744872 | -0.018609 |
| candidate_ppopt190_gap_hazard_rollback__risk_conservative__gapthr_0p6__stable_0p25__s_0p7__cap_0p0025__52c5adcd26 | 0.269955 | 0.807259 | -0.000609 | -0.000240 | 0.950000 | 0.744872 | -0.018609 |
| candidate_ppopt190_gap_hazard_rollback__risk_conservative__gapthr_0p6__stable_0p45__s_0p7__cap_0p0025__1bf342ebae | 0.269955 | 0.807259 | -0.000609 | -0.000240 | 0.950000 | 0.744872 | -0.018609 |
| candidate_ppopt190_gap_hazard_rollback__risk_gap_heavy__gapthr_0p52__stable_0p25__s_0p7__cap_0p0025__478723c879 | 0.269955 | 0.807259 | -0.000609 | -0.000240 | 0.950000 | 0.744872 | -0.018609 |
| candidate_ppopt190_gap_hazard_rollback__risk_gap_heavy__gapthr_0p52__stable_0p45__s_0p7__cap_0p0025__a3824bff38 | 0.269955 | 0.807259 | -0.000609 | -0.000240 | 0.950000 | 0.744872 | -0.018609 |
| candidate_ppopt190_gap_hazard_rollback__risk_gap_heavy__gapthr_0p68__stable_0p25__s_0p7__cap_0p0025__b3d9bedc56 | 0.269955 | 0.807259 | -0.000609 | -0.000240 | 0.950000 | 0.744872 | -0.018609 |
| candidate_ppopt190_gap_hazard_rollback__risk_gap_heavy__gapthr_0p68__stable_0p45__s_0p7__cap_0p0025__687f82b6f5 | 0.269955 | 0.807259 | -0.000609 | -0.000240 | 0.950000 | 0.744872 | -0.018609 |
| candidate_ppopt190_gap_hazard_rollback__risk_gap_heavy__gapthr_0p6__stable_0p25__s_0p7__cap_0p0025__6638262b44 | 0.269955 | 0.807259 | -0.000609 | -0.000240 | 0.950000 | 0.744872 | -0.018609 |
| candidate_ppopt190_gap_hazard_rollback__risk_gap_heavy__gapthr_0p6__stable_0p45__s_0p7__cap_0p0025__6ed3f79510 | 0.269955 | 0.807259 | -0.000609 | -0.000240 | 0.950000 | 0.744872 | -0.018609 |

## 실행 설정
```json
{
  "experiment_id": "PP-OPT187-192",
  "experiment_slug": "PP-OPT187_192_warm_pp180_pp186_risk_router",
  "created_at": "2026-06-10T10:29:21",
  "base_candidate": "hcoef_stable",
  "previous_experiment": "experiments/track6/PP-OPT181_186_warm_huber_basis_p95_guard_refinement",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 2480,
  "prediction_rows": 2792480,
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
    "pp186_p95": "ppopt186_p95_huber_basis_p95_guard__source=reference_pp148_p95"
  },
  "selection_decision": {
    "operational_label": "candidate_ppopt189_segment_router__seg_price_gap__scorethr_0p02__mix_0p75__s_0p95__cap_0p0025__0b3e477775",
    "operational_candidate": "ppopt189_segment_router__seg=price_gap__scorethr=0p02__mix=0p75__s=0p95__cap=0p0025",
    "operational_fixed_test_MAPE": 0.26991435414474985,
    "operational_fixed_test_p95_APE": 0.8073255046591389,
    "operational_delta_vs_pp64_MAPE": -0.000649687770910512,
    "operational_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "operational_delta_vs_pp126_MAPE": -0.0002000426051019799,
    "operational_delta_vs_pp126_p95_APE": -0.0001645562387090349,
    "operational_delta_vs_pp148_MAPE": -0.0002256342278295631,
    "operational_delta_vs_pp148_p95_APE": 9.45931204405781e-05,
    "operational_delta_vs_pp166_MAPE": -8.263152048876288e-05,
    "operational_delta_vs_pp166_p95_APE": 9.45931204405781e-05,
    "operational_delta_vs_pp172_MAPE": -8.306051640072365e-05,
    "operational_delta_vs_pp172_p95_APE": 9.45931204405781e-05,
    "operational_delta_vs_pp180_MAPE": -1.8272443038480635e-05,
    "operational_delta_vs_pp180_p95_APE": 0.0,
    "operational_delta_vs_pp186_MAPE": -4.6279721476749636e-05,
    "operational_delta_vs_pp186_p95_APE": 9.45931204405781e-05,
    "operational_avg_pp64_MAPE_win_rate": 0.953525641025641,
    "operational_avg_pp64_p95_win_rate": 0.7509615384615383,
    "operational_replacement_score": -0.018790713411936152,
    "p95_guarded_label": "candidate_ppopt187_hard_risk_router__risk_uncertainty__mode_hard__thr_0p78__w_0p06__s_0p75__c244d965f9",
    "p95_guarded_candidate": "ppopt187_hard_risk_router__risk=uncertainty__mode=hard__thr=0p78__w=0p06__s=0p75",
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
    "p95_extreme_avg_pp64_MAPE_win_rate": 0.5983974358974359,
    "p95_extreme_avg_pp64_p95_win_rate": 0.5009615384615385,
    "p95_extreme_replacement_score": -0.0040792899192624915,
    "operational_protocol_candidate": "ppopt192_operational_pp180_pp186_risk_router__source=ppopt189_segment_router__seg_price_gap__scorethr_0p02__mix_0p75__s_0p95__cap_0p0025",
    "p95_guarded_protocol_candidate": "ppopt192_p95_guarded_pp180_pp186_risk_router__source=ppopt187_hard_risk_router__risk_uncertainty__mode_hard__thr_0p78__w_0p06__s_0p75",
    "p95_extreme_protocol_candidate": "ppopt192_p95_extreme_pp180_pp186_risk_router__source=reference_pp148_p95"
  },
  "items": [
    {
      "item_id": "PP-OPT187",
      "priority": "1",
      "title": "hard risk router",
      "description": "위험 점수가 큰 row는 PP186으로, 나머지는 PP180으로 보내는 hard/near-hard 라우터."
    },
    {
      "item_id": "PP-OPT188",
      "priority": "2",
      "title": "soft risk blend",
      "description": "위험 점수를 연속 가중치로 바꿔 PP180에서 PP186 쪽으로 부드럽게 이동."
    },
    {
      "item_id": "PP-OPT189",
      "priority": "3",
      "title": "segment outcome router",
      "description": "validation 구간별로 PP180이 p95를 해치는 segment만 PP186으로 rollback."
    },
    {
      "item_id": "PP-OPT190",
      "priority": "4",
      "title": "prediction gap hazard rollback",
      "description": "PP180과 PP186의 예측 차이가 큰 row를 위험 row로 보고 제한 rollback."
    },
    {
      "item_id": "PP-OPT191",
      "priority": "5",
      "title": "hybrid risk and segment router",
      "description": "row 위험 점수와 validation segment p95 hazard를 함께 쓰는 하이브리드 라우터."
    },
    {
      "item_id": "PP-OPT192",
      "priority": "6",
      "title": "final PP180/PP186 router decision",
      "description": "PP180, PP186, 신규 라우터 후보를 fixed/repeated 기준으로 비교해 선택."
    }
  ],
  "router_formula": {
    "base": "PP180 operational log price",
    "safe_price": "PP186 p95-guard log price",
    "final": "PP180 log price + clip((PP186 log price - PP180 log price) * router_weight, row_cap)",
    "risk_inputs": [
      "quantile_width",
      "l10_price_range_ratio",
      "component_prediction_spread",
      "current_vs_stable_gap_abs",
      "abs(PP180 log price - PP186 log price)",
      "svc_group_n",
      "confidence_tier",
      "stable_price_band"
    ]
  }
}
```