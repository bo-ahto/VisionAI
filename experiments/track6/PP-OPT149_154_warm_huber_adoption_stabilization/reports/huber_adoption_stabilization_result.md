# PP-OPT149~154 Warm Huber adoption stabilization 결과

- 작성일: 2026-06-09 16:51
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 목적: PP143~148에서 발견된 direct LightGBM Huber 보정의 MAPE 개선 신호를 안정화
- 결론: 운영 후보 fixed test MAPE 0.270140, p95 0.807231. PP126 대비 MAPE +0.000026, p95 -0.000259. PP148 대비 MAPE +0.000000, p95 +0.000000.

## 주요 후보 test 비교
| candidate | family | item_id | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| reference_pp126_operational | reference_prior | REFERENCE | 0.136320 | 0.270114 | 0.807490 | 0.397588 | -0.001280 | -0.000640 |
| reference_pp148_operational | reference_prior | REFERENCE | 0.139801 | 0.270140 | 0.807231 | 0.397525 | -0.001255 | -0.000899 |
| ppopt154_operational_huber_adoption_stabilization_challenger__source=reference_pp148_operational | huber_adoption_stabilized_operational_selection | PP-OPT154 | 0.139801 | 0.270140 | 0.807231 | 0.397525 | -0.001255 | -0.000899 |
| reference_pp148_p95 | reference_prior | REFERENCE | 0.141036 | 0.270269 | 0.805949 | 0.397421 | -0.001126 | -0.002181 |
| ppopt154_p95_huber_adoption_stabilization_challenger__source=reference_pp148_p95 | huber_adoption_stabilized_p95_selection | PP-OPT154 | 0.141036 | 0.270269 | 0.805949 | 0.397421 | -0.001126 | -0.002181 |
| reference_pp64_current_best | reference_prior | REFERENCE | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | p95_test_MAPE | p95_test_p95_APE | operational_pass_vs_incumbent | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | huber adoption with l2 hard-switch consensus | 1152 | 0.270114 | 0.807490 | 0.269953 | 0.806345 | True | huber_adoption_l2_hardswitch_consensus | ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p28__w=0p08__s=0p65__cap=0p004 |
| 1 | huber adoption small-cap stabilization | 1200 | 0.270037 | 0.807223 | 0.269811 | 0.806782 | True | huber_adoption_small_cap_stabilization | ppopt149_huber_small_cap__thr=0p32__w=0p06__hpen=0p2__s=1p0__cap=0p0035 |
| 4 | uncertainty rollback for huber adoption | 384 | 0.269989 | 0.807242 | 0.269875 | 0.806822 | True | huber_adoption_uncertainty_rollback | ppopt152_uncertainty_rollback__thr=0p32__w=0p14__rb=0p8__s=0p85__cap=0p004 |
| 3 | PP148 plus huber micro correction | 384 | 0.270089 | 0.807008 | 0.269968 | 0.806783 | False | pp148_plus_huber_micro_correction | ppopt151_pp148_micro_huber__shift=0__thr=0p32__w=0p08__s=0p7__cap=0p003 |
| 5 | PP148 and huber stability ensemble | 512 | 0.270043 | 0.806927 | 0.269943 | 0.806734 | False | pp148_huber_stability_ensemble | ppopt153_pp148_huber_ensemble__thr=0p3__w=0p08__p148=0p7__hs=0p5__cap=0p006 |
| 6 | final huber adoption stabilization decision | 2 | 0.270140 | 0.807231 | 0.270269 | 0.805949 | False | huber_adoption_stabilized_operational_selection | ppopt154_operational_huber_adoption_stabilization_challenger__source=reference_pp148_operational |

## 탐색 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p28__w=0p08__s=0p65__cap=0p004 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p28__w=0p08__s=0p65__cap=0p006 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p28__w=0p08__s=0p65__cap=0p008 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p28__w=0p08__s=0p65__cap=0p01 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p28__w=0p08__s=0p85__cap=0p004 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p28__w=0p08__s=0p85__cap=0p006 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p28__w=0p08__s=0p85__cap=0p008 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p28__w=0p08__s=0p85__cap=0p01 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p28__w=0p08__s=1p0__cap=0p004 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p28__w=0p08__s=1p0__cap=0p006 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p28__w=0p08__s=1p0__cap=0p008 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p28__w=0p08__s=1p0__cap=0p01 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p28__w=0p14__s=0p65__cap=0p004 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p28__w=0p14__s=0p65__cap=0p006 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p28__w=0p14__s=0p65__cap=0p008 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p28__w=0p14__s=0p65__cap=0p01 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p28__w=0p14__s=0p85__cap=0p004 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p28__w=0p14__s=0p85__cap=0p006 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p28__w=0p14__s=0p85__cap=0p008 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p28__w=0p14__s=0p85__cap=0p01 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p28__w=0p14__s=1p0__cap=0p004 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p28__w=0p14__s=1p0__cap=0p006 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p28__w=0p14__s=1p0__cap=0p008 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p28__w=0p14__s=1p0__cap=0p01 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p32__w=0p08__s=0p65__cap=0p004 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p32__w=0p08__s=0p65__cap=0p006 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p32__w=0p08__s=0p65__cap=0p008 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p32__w=0p08__s=0p65__cap=0p01 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p32__w=0p08__s=0p85__cap=0p004 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p32__w=0p08__s=0p85__cap=0p006 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p32__w=0p08__s=0p85__cap=0p008 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p32__w=0p08__s=0p85__cap=0p01 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p32__w=0p08__s=1p0__cap=0p004 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p32__w=0p08__s=1p0__cap=0p006 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p32__w=0p08__s=1p0__cap=0p008 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p32__w=0p08__s=1p0__cap=0p01 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p32__w=0p14__s=0p65__cap=0p004 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p32__w=0p14__s=0p65__cap=0p006 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p32__w=0p14__s=0p65__cap=0p008 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p32__w=0p14__s=0p65__cap=0p01 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p32__w=0p14__s=0p85__cap=0p004 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p32__w=0p14__s=0p85__cap=0p006 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p32__w=0p14__s=0p85__cap=0p008 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p32__w=0p14__s=0p85__cap=0p01 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p32__w=0p14__s=1p0__cap=0p004 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p32__w=0p14__s=1p0__cap=0p006 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p32__w=0p14__s=1p0__cap=0p008 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p32__w=0p14__s=1p0__cap=0p01 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p36__w=0p08__s=0p65__cap=0p004 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p36__w=0p08__s=0p65__cap=0p006 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p36__w=0p08__s=0p65__cap=0p008 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p36__w=0p08__s=0p65__cap=0p01 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p36__w=0p08__s=0p85__cap=0p004 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p36__w=0p08__s=0p85__cap=0p006 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p36__w=0p08__s=0p85__cap=0p008 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p36__w=0p08__s=0p85__cap=0p01 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p36__w=0p08__s=1p0__cap=0p004 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p36__w=0p08__s=1p0__cap=0p006 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p36__w=0p08__s=1p0__cap=0p008 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p36__w=0p08__s=1p0__cap=0p01 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p36__w=0p14__s=0p65__cap=0p004 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p36__w=0p14__s=0p65__cap=0p006 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p36__w=0p14__s=0p65__cap=0p008 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p36__w=0p14__s=0p65__cap=0p01 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p36__w=0p14__s=0p85__cap=0p004 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p36__w=0p14__s=0p85__cap=0p006 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p36__w=0p14__s=0p85__cap=0p008 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p36__w=0p14__s=0p85__cap=0p01 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p36__w=0p14__s=1p0__cap=0p004 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p36__w=0p14__s=1p0__cap=0p006 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p36__w=0p14__s=1p0__cap=0p008 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p36__w=0p14__s=1p0__cap=0p01 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p4__w=0p08__s=0p65__cap=0p004 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p4__w=0p08__s=0p65__cap=0p006 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p4__w=0p08__s=0p65__cap=0p008 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p4__w=0p08__s=0p65__cap=0p01 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p4__w=0p08__s=0p85__cap=0p004 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p4__w=0p08__s=0p85__cap=0p006 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p4__w=0p08__s=0p85__cap=0p008 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt150_l2_huber_consensus__l2thr=0p58__minc=0p34__thr=0p4__w=0p08__s=0p85__cap=0p01 | PP-OPT150 | huber_adoption_l2_hardswitch_consensus | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |

## 선택 후보 반복 안정성
| candidate_label | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_vs_pp64_MAPE | fixed_test_delta_vs_pp64_p95_APE | avg_pp64_MAPE_win_rate | avg_pp64_p95_win_rate | replacement_score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pp148_operational_reference | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| pp154_operational_huber_adoption_stabilization_challenger | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p4__w_0p2__s_0p25__cap_0p002__c70a1b7335 | 0.270148 | 0.807340 | -0.000416 | -0.000159 | 0.923397 | 0.531090 | -0.017352 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p4__w_0p2__s_0p25__cap_0p003__2882adb742 | 0.270148 | 0.807340 | -0.000416 | -0.000159 | 0.923397 | 0.531090 | -0.017352 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p4__w_0p2__s_0p25__cap_0p0045__96b52500e0 | 0.270148 | 0.807340 | -0.000416 | -0.000159 | 0.923397 | 0.531090 | -0.017352 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p4__w_0p2__s_0p25__cap_0p006__c58f383c22 | 0.270148 | 0.807340 | -0.000416 | -0.000159 | 0.923397 | 0.531090 | -0.017352 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p28__w_0p08__s_0p25__cap_0p002__a579e25aa0 | 0.270158 | 0.807345 | -0.000406 | -0.000154 | 0.923397 | 0.573718 | -0.017342 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p28__w_0p08__s_0p25__cap_0p003__e65e59b399 | 0.270160 | 0.807383 | -0.000404 | -0.000115 | 0.923397 | 0.573718 | -0.017340 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p28__w_0p08__s_0p25__cap_0p0045__8b31ea3e19 | 0.270160 | 0.807383 | -0.000404 | -0.000115 | 0.923397 | 0.573718 | -0.017340 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p28__w_0p08__s_0p25__cap_0p006__fbed8d3a48 | 0.270160 | 0.807383 | -0.000404 | -0.000115 | 0.923397 | 0.573718 | -0.017340 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p28__w_0p14__s_0p25__cap_0p003__d8c1772b70 | 0.270160 | 0.807383 | -0.000404 | -0.000115 | 0.923397 | 0.573718 | -0.017339 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p28__w_0p14__s_0p25__cap_0p0045__0e9e3abac6 | 0.270160 | 0.807383 | -0.000404 | -0.000115 | 0.923397 | 0.573718 | -0.017339 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p28__w_0p14__s_0p25__cap_0p006__ab06853be1 | 0.270160 | 0.807383 | -0.000404 | -0.000115 | 0.923397 | 0.573718 | -0.017339 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p28__w_0p14__s_0p25__cap_0p002__50c098e935 | 0.270158 | 0.807345 | -0.000406 | -0.000154 | 0.923077 | 0.573718 | -0.017329 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p36__w_0p2__s_0p25__cap_0p002__cd64b1d185 | 0.270151 | 0.807345 | -0.000413 | -0.000154 | 0.922756 | 0.531090 | -0.017323 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p36__w_0p2__s_0p25__cap_0p003__3755a73a84 | 0.270152 | 0.807370 | -0.000412 | -0.000129 | 0.922756 | 0.531090 | -0.017322 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p36__w_0p2__s_0p25__cap_0p0045__691e74f27f | 0.270152 | 0.807370 | -0.000412 | -0.000129 | 0.922756 | 0.531090 | -0.017322 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p28__w_0p2__s_0p25__cap_0p003__615fe229be | 0.270157 | 0.807383 | -0.000407 | -0.000115 | 0.922756 | 0.531410 | -0.017317 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p28__w_0p2__s_0p25__cap_0p0045__fa5f266aab | 0.270157 | 0.807383 | -0.000407 | -0.000115 | 0.922756 | 0.531410 | -0.017317 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p28__w_0p2__s_0p25__cap_0p006__97bb94a4e9 | 0.270157 | 0.807383 | -0.000407 | -0.000115 | 0.922756 | 0.531410 | -0.017317 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p32__w_0p08__s_0p25__cap_0p002__52c4d7e375 | 0.270160 | 0.807345 | -0.000404 | -0.000154 | 0.922756 | 0.573397 | -0.017314 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p32__w_0p08__s_0p25__cap_0p003__754751295a | 0.270162 | 0.807383 | -0.000402 | -0.000115 | 0.922756 | 0.573397 | -0.017312 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p32__w_0p08__s_0p25__cap_0p0045__cc4df9628f | 0.270162 | 0.807383 | -0.000402 | -0.000115 | 0.922756 | 0.573397 | -0.017312 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p32__w_0p08__s_0p25__cap_0p006__82ff3d67c8 | 0.270162 | 0.807383 | -0.000402 | -0.000115 | 0.922756 | 0.573397 | -0.017312 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p4__w_0p14__s_0p25__cap_0p002__8af0f3ac7b | 0.270150 | 0.807345 | -0.000414 | -0.000154 | 0.922436 | 0.531090 | -0.017311 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p28__w_0p2__s_0p25__cap_0p002__ada6769035 | 0.270155 | 0.807345 | -0.000409 | -0.000154 | 0.922436 | 0.531410 | -0.017306 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p28__w_0p08__s_0p7__cap_0p002__7842ed3a83 | 0.270173 | 0.807345 | -0.000391 | -0.000154 | 0.921154 | 0.573718 | -0.017237 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p28__w_0p08__s_0p4__cap_0p002__08883361e2 | 0.270168 | 0.807345 | -0.000396 | -0.000154 | 0.920833 | 0.573718 | -0.017229 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p28__w_0p08__s_0p65__cap_0p004__4f6022be62 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p28__w_0p08__s_0p65__cap_0p006__e069e5878b | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p28__w_0p08__s_0p65__cap_0p008__d2abb37eb9 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p28__w_0p08__s_0p65__cap_0p01__25ee869c33 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p28__w_0p08__s_0p85__cap_0p004__1eabc52349 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p28__w_0p08__s_0p85__cap_0p006__0ac441b739 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p28__w_0p08__s_0p85__cap_0p008__b816f83605 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p28__w_0p08__s_0p85__cap_0p01__c60080f1b8 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p28__w_0p08__s_1p0__cap_0p004__11607da5c5 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p28__w_0p08__s_1p0__cap_0p006__b503d0032a | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p28__w_0p08__s_1p0__cap_0p008__53152aaec6 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p28__w_0p08__s_1p0__cap_0p01__6cec2a4516 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p28__w_0p14__s_0p65__cap_0p004__adb834f860 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p28__w_0p14__s_0p65__cap_0p006__118fed4955 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p28__w_0p14__s_0p65__cap_0p008__5700759350 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p28__w_0p14__s_0p65__cap_0p01__c4b4c90b2c | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p28__w_0p14__s_0p85__cap_0p004__28b11e3cc0 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p28__w_0p14__s_0p85__cap_0p006__46d4962272 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p28__w_0p14__s_0p85__cap_0p008__01bdc1288a | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p28__w_0p14__s_0p85__cap_0p01__23564ca799 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p28__w_0p14__s_1p0__cap_0p004__70086a36cd | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p28__w_0p14__s_1p0__cap_0p006__33380501e1 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p28__w_0p14__s_1p0__cap_0p008__b5d673ef17 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p28__w_0p14__s_1p0__cap_0p01__dea79f6ee6 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p32__w_0p08__s_0p65__cap_0p004__55c52ad268 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p32__w_0p08__s_0p65__cap_0p006__4a30230d92 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p32__w_0p08__s_0p65__cap_0p008__d7ccf5a150 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p32__w_0p08__s_0p65__cap_0p01__d2fa0dd2fb | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p32__w_0p08__s_0p85__cap_0p004__528390e67b | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p32__w_0p08__s_0p85__cap_0p006__e8a661211b | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p32__w_0p08__s_0p85__cap_0p008__06cb18830c | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p58__minc_0p34__thr_0p32__w_0p08__s_0p85__cap_0p01__556200b745 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| pp126_operational_reference | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p28__w_0p08__s_0p55__cap_0p002__8e1ddbeff3 | 0.270173 | 0.807345 | -0.000391 | -0.000154 | 0.919872 | 0.573718 | -0.017186 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p28__w_0p08__s_0p4__cap_0p003__014fffbeb9 | 0.270169 | 0.807401 | -0.000395 | -0.000098 | 0.919231 | 0.573718 | -0.017165 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p28__w_0p08__s_0p55__cap_0p003__d76a70290d | 0.270180 | 0.807401 | -0.000384 | -0.000098 | 0.918590 | 0.573718 | -0.017128 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p28__w_0p14__s_0p7__cap_0p002__df02e10103 | 0.270174 | 0.807345 | -0.000390 | -0.000154 | 0.918269 | 0.573718 | -0.017121 |
| candidate_ppopt151_pp148_micro_huber__shift_1__thr_0p28__w_0p08__s_0p7__cap_0p003__8ba4fae3e6 | 0.270187 | 0.807401 | -0.000378 | -0.000098 | 0.916987 | 0.573718 | -0.017057 |
| pp134_operational_recomputed_reference | 0.270033 | 0.807490 | -0.000531 | -0.000009 | 0.909936 | 0.496474 | -0.016928 |
| pp118_operational_reference | 0.270139 | 0.807490 | -0.000425 | -0.000009 | 0.909295 | 0.494551 | -0.016797 |
| candidate_ppopt149_huber_small_cap__thr_0p36__w_0p06__hpen_0p45__s_1p0__cap_0p0055__0ca71aa1bd | 0.269851 | 0.807069 | -0.000713 | -0.000429 | 0.899038 | 0.600641 | -0.016674 |
| candidate_ppopt149_huber_small_cap__thr_0p36__w_0p06__hpen_0p2__s_1p0__cap_0p0055__371c2dda67 | 0.269852 | 0.807069 | -0.000712 | -0.000429 | 0.898718 | 0.600641 | -0.016661 |
| candidate_ppopt149_huber_small_cap__thr_0p36__w_0p06__hpen_0p7__s_1p0__cap_0p0055__5eed8e14b3 | 0.269850 | 0.807069 | -0.000714 | -0.000429 | 0.898397 | 0.600000 | -0.016650 |
| pp126_p95_reference | 0.270317 | 0.807465 | -0.000247 | -0.000034 | 0.909936 | 0.665705 | -0.016645 |
| candidate_ppopt149_huber_small_cap__thr_0p36__w_0p06__hpen_0p9__s_1p0__cap_0p0055__32f9a54c06 | 0.269849 | 0.807069 | -0.000715 | -0.000429 | 0.897756 | 0.600000 | -0.016625 |
| pp134_p95_recomputed_reference | 0.270242 | 0.807488 | -0.000322 | -0.000010 | 0.907051 | 0.492628 | -0.016604 |
| candidate_ppopt149_huber_small_cap__thr_0p36__w_0p06__hpen_0p45__s_0p8__cap_0p0055__71b37d1b96 | 0.269870 | 0.807061 | -0.000694 | -0.000438 | 0.894551 | 0.600000 | -0.016476 |
| candidate_ppopt149_huber_small_cap__thr_0p36__w_0p08__hpen_0p2__s_1p0__cap_0p0055__466a14ea63 | 0.269856 | 0.807069 | -0.000708 | -0.000429 | 0.893590 | 0.600000 | -0.016451 |
| candidate_ppopt149_huber_small_cap__thr_0p36__w_0p08__hpen_0p45__s_1p0__cap_0p0055__6cd0f8a525 | 0.269858 | 0.807069 | -0.000706 | -0.000429 | 0.892308 | 0.600000 | -0.016398 |
| candidate_ppopt149_huber_small_cap__thr_0p36__w_0p08__hpen_0p7__s_1p0__cap_0p0055__ea93791839 | 0.269860 | 0.807069 | -0.000704 | -0.000429 | 0.891026 | 0.600000 | -0.016345 |
| candidate_ppopt149_huber_small_cap__thr_0p36__w_0p08__hpen_0p9__s_1p0__cap_0p0055__120e76503d | 0.269862 | 0.807069 | -0.000702 | -0.000429 | 0.890064 | 0.600321 | -0.016304 |
| candidate_ppopt149_huber_small_cap__thr_0p36__w_0p06__hpen_0p2__s_1p0__cap_0p0065__d00ddb5d31 | 0.269823 | 0.806992 | -0.000741 | -0.000506 | 0.888782 | 0.600321 | -0.016292 |
| candidate_ppopt149_huber_small_cap__thr_0p36__w_0p06__hpen_0p45__s_1p0__cap_0p0065__bd7503cf6e | 0.269822 | 0.806992 | -0.000742 | -0.000506 | 0.887500 | 0.600321 | -0.016242 |
| candidate_ppopt149_huber_small_cap__thr_0p36__w_0p06__hpen_0p7__s_1p0__cap_0p0065__c3d04677f6 | 0.269823 | 0.806991 | -0.000741 | -0.000508 | 0.884936 | 0.599679 | -0.016139 |
| candidate_ppopt149_huber_small_cap__thr_0p36__w_0p06__hpen_0p9__s_1p0__cap_0p0065__8791815238 | 0.269826 | 0.806982 | -0.000738 | -0.000517 | 0.884615 | 0.599679 | -0.016122 |
| candidate_ppopt149_huber_small_cap__thr_0p36__w_0p06__hpen_0p9__s_0p8__cap_0p0065__dc65427577 | 0.269869 | 0.806911 | -0.000695 | -0.000588 | 0.884295 | 0.604167 | -0.016067 |
| candidate_ppopt149_huber_small_cap__thr_0p36__w_0p06__hpen_0p7__s_0p8__cap_0p008__ba2f8c53e5 | 0.269870 | 0.806874 | -0.000694 | -0.000625 | 0.881731 | 0.600000 | -0.015963 |
| candidate_ppopt149_huber_small_cap__thr_0p36__w_0p06__hpen_0p7__s_0p8__cap_0p0065__01342fc0af | 0.269865 | 0.806918 | -0.000699 | -0.000580 | 0.881090 | 0.600000 | -0.015942 |
| candidate_ppopt149_huber_small_cap__thr_0p36__w_0p06__hpen_0p2__s_0p8__cap_0p0065__42f87d12c8 | 0.269855 | 0.806936 | -0.000709 | -0.000562 | 0.880449 | 0.600000 | -0.015927 |
| candidate_ppopt149_huber_small_cap__thr_0p36__w_0p06__hpen_0p45__s_0p8__cap_0p0065__65d8ba2598 | 0.269861 | 0.806927 | -0.000704 | -0.000571 | 0.879808 | 0.600000 | -0.015896 |
| candidate_ppopt149_huber_small_cap__thr_0p36__w_0p06__hpen_0p45__s_0p8__cap_0p008__22eb00ab58 | 0.269866 | 0.806876 | -0.000698 | -0.000623 | 0.878526 | 0.600000 | -0.015839 |
| candidate_ppopt149_huber_small_cap__thr_0p36__w_0p08__hpen_0p2__s_1p0__cap_0p0065__01a9bc7b2b | 0.269839 | 0.806992 | -0.000725 | -0.000506 | 0.877564 | 0.599679 | -0.015828 |
| candidate_ppopt149_huber_small_cap__thr_0p36__w_0p08__hpen_0p45__s_1p0__cap_0p0065__d3e07e6b02 | 0.269841 | 0.806992 | -0.000723 | -0.000506 | 0.875962 | 0.599679 | -0.015761 |
| candidate_ppopt149_huber_small_cap__thr_0p36__w_0p06__hpen_0p2__s_0p8__cap_0p008__ed50959886 | 0.269862 | 0.806878 | -0.000702 | -0.000621 | 0.875962 | 0.600000 | -0.015740 |
| candidate_ppopt149_huber_small_cap__thr_0p36__w_0p08__hpen_0p7__s_1p0__cap_0p0065__6244fe3686 | 0.269845 | 0.806991 | -0.000720 | -0.000508 | 0.873718 | 0.599679 | -0.015668 |
| candidate_ppopt149_huber_small_cap__thr_0p36__w_0p08__hpen_0p9__s_1p0__cap_0p0065__9e241f8db4 | 0.269848 | 0.806982 | -0.000716 | -0.000517 | 0.873718 | 0.600000 | -0.015665 |
| pp81_stable_reference | 0.270559 | 0.807490 | -0.000005 | -0.000009 | 0.890705 | 0.410256 | -0.015633 |
| pp95_operational_reference | 0.270559 | 0.807490 | -0.000005 | -0.000009 | 0.890705 | 0.410256 | -0.015633 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p36__minc_0p34__thr_0p36__w_0p14__s_0p85__cap_0p01__d4d8e81dc4 | 0.269987 | 0.806570 | -0.000577 | -0.000929 | 0.870833 | 0.538462 | -0.015411 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p36__minc_0p34__thr_0p36__w_0p14__s_0p85__cap_0p008__b0936ebf0c | 0.269987 | 0.806570 | -0.000577 | -0.000929 | 0.870513 | 0.538462 | -0.015398 |
| candidate_ppopt149_huber_small_cap__thr_0p36__w_0p06__hpen_0p9__s_1p0__cap_0p008__c66ce9dd92 | 0.269811 | 0.806782 | -0.000753 | -0.000717 | 0.866026 | 0.599679 | -0.015394 |
| candidate_ppopt150_l2_huber_consensus__l2thr_0p36__minc_0p34__thr_0p4__w_0p08__s_0p85__cap_0p01__f9f4b73879 | 0.269996 | 0.806517 | -0.000568 | -0.000981 | 0.868910 | 0.544551 | -0.015324 |

## 실행 설정
```json
{
  "experiment_id": "PP-OPT149-154",
  "experiment_slug": "PP-OPT149_154_warm_huber_adoption_stabilization",
  "created_at": "2026-06-09T16:50:07",
  "seed": 20260609,
  "base_candidate": "hcoef_stable",
  "incumbent_candidate": "incumbent_operational_pp_opt7",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 3651,
  "prediction_rows": 4111026,
  "selected_references": {
    "pp64": "reference_pp64_current_best",
    "pp70": "reference_pp70_refinement",
    "pp81": "reference_pp81_best",
    "pp82_op": "reference_pp82_operational",
    "pp82_p95": "reference_pp82_p95",
    "pp95_op": "reference_pp95_operational",
    "pp95_p95": "reference_pp95_p95",
    "pp102_op": "reference_pp102_operational",
    "pp110_op": "ppopt110_operational_guarded_pp102_challenger__source=ppopt104_margin_gate__gain_gain_any__hpen_1p05__rpen_0p0__thr_0p14__s_1p0",
    "pp110_p95": "ppopt110_p95_guarded_pp102_challenger__source=ppopt108_tail_hybrid__target_pp82_p95__opthr_0p02__tailthr_0p08__tails_0p4",
    "pp118_op": "ppopt118_operational_next_dimension_challenger__source=ppopt116_hybrid_stack_router__target_huber_stack_weighted__thr_0p12__s_0p75",
    "pp118_p95": "ppopt118_p95_next_dimension_challenger__source=ppopt111_meta_router__set_tail_mix__thr_0p22__s_1p0",
    "pp111_p95_source": "ppopt111_meta_router__set=tail_mix__thr=0p22__s=1p0",
    "pp126_op": "ppopt126_operational_stack_gate_challenger__source=ppopt119_fine_gate__safe_pp81__policy_less_harm__thr_0p1__width_0p16__s_0p75",
    "pp126_p95": "ppopt126_p95_stack_gate_challenger__source=ppopt124_p95_limited__target_pp82_p95__thr_0p08__mpen_0p2__s_0p4",
    "pp119_operational_source": "ppopt119_fine_gate__safe=pp81__policy=less_harm__thr=0p1__width=0p16__s=0p75",
    "pp119_p95_source": "ppopt124_p95_limited__target=pp82_p95__thr=0p08__mpen=0p2__s=0p4",
    "pp119_guarded_mape": "ppopt124_p95_limited__target=xgb_direct__thr=0p32__mpen=0p2__s=0p4",
    "pp119_aggressive_mape": "ppopt123_aggressive_rollback__target=huber_weighted__safe=pp118_op__cap=0p055__rollback=0p25__floor=0p0",
    "pp119_stable_best": "ppopt119_fine_gate__safe=pp81__policy=less_harm__thr=0p1__width=0p16__s=0p75"
  },
  "selected_pp119_sources": {
    "pp126_op": "ppopt126_operational_stack_gate_challenger__source=ppopt119_fine_gate__safe_pp81__policy_less_harm__thr_0p1__width_0p16__s_0p75",
    "pp126_p95": "ppopt126_p95_stack_gate_challenger__source=ppopt124_p95_limited__target_pp82_p95__thr_0p08__mpen_0p2__s_0p4",
    "pp119_operational_source": "ppopt119_fine_gate__safe=pp81__policy=less_harm__thr=0p1__width=0p16__s=0p75",
    "pp119_p95_source": "ppopt124_p95_limited__target=pp82_p95__thr=0p08__mpen=0p2__s=0p4",
    "pp119_guarded_mape": "ppopt124_p95_limited__target=xgb_direct__thr=0p32__mpen=0p2__s=0p4",
    "pp119_aggressive_mape": "ppopt123_aggressive_rollback__target=huber_weighted__safe=pp118_op__cap=0p055__rollback=0p25__floor=0p0",
    "pp119_stable_best": "ppopt119_fine_gate__safe=pp81__policy=less_harm__thr=0p1__width=0p16__s=0p75"
  },
  "recomputed_reference_notes": {
    "pp134_op_recomputed": "PP134 운영 후보 재계산: learned harm rollback",
    "pp134_p95_recomputed": "PP134 p95 후보 재계산: p95 tail router"
  },
  "selection_decision": {
    "operational_label": "pp148_operational_reference",
    "operational_candidate": "reference_pp148_operational",
    "operational_fixed_test_MAPE": 0.27013998837257946,
    "operational_fixed_test_p95_APE": 0.8072309115386983,
    "operational_delta_vs_pp64_MAPE": -0.0004240535430808934,
    "operational_delta_vs_pp64_p95_APE": -0.00026794076741154527,
    "operational_delta_vs_pp126_MAPE": 2.5591622727638708e-05,
    "operational_delta_vs_pp126_p95_APE": -0.000259149359149613,
    "operational_delta_vs_pp148_MAPE": 0.0,
    "operational_delta_vs_pp148_p95_APE": 0.0,
    "operational_avg_pp64_MAPE_win_rate": 0.9259615384615385,
    "operational_avg_pp64_p95_win_rate": 0.5310897435897436,
    "operational_replacement_score": -0.017462515081542434,
    "p95_label": "pp148_p95_reference",
    "p95_candidate": "reference_pp148_p95",
    "p95_fixed_test_MAPE": 0.27026892590910795,
    "p95_fixed_test_p95_APE": 0.8059493758221674,
    "p95_delta_vs_pp64_MAPE": -0.00029511600655240944,
    "p95_delta_vs_pp64_p95_APE": -0.0015494764839424358,
    "p95_delta_vs_pp126_MAPE": 0.00015452915925612265,
    "p95_delta_vs_pp126_p95_APE": -0.0015406850756805035,
    "p95_delta_vs_pp148_MAPE": 0.0,
    "p95_delta_vs_pp148_p95_APE": 0.0,
    "p95_avg_pp64_MAPE_win_rate": 0.5983974358974359,
    "p95_avg_pp64_p95_win_rate": 0.5009615384615385,
    "p95_replacement_score": -0.004079289919262468,
    "operational_protocol_candidate": "ppopt154_operational_huber_adoption_stabilization_challenger__source=reference_pp148_operational",
    "p95_protocol_candidate": "ppopt154_p95_huber_adoption_stabilization_challenger__source=reference_pp148_p95"
  },
  "items": [
    {
      "item_id": "PP-OPT149",
      "priority": "1",
      "title": "huber adoption small-cap stabilization",
      "description": "direct LightGBM Huber 후보의 낮은 MAPE 신호를 유지하되 작은 cap과 높은 적용 확률로 안정화한다."
    },
    {
      "item_id": "PP-OPT150",
      "priority": "2",
      "title": "huber adoption with l2 hard-switch consensus",
      "description": "PP148 hard-switch가 허용한 row 중 Huber 보정 방향도 동의하는 경우만 추가 이동한다."
    },
    {
      "item_id": "PP-OPT151",
      "priority": "3",
      "title": "PP148 plus huber micro correction",
      "description": "PP148 운영 후보를 기준으로 Huber adoption 보정을 아주 작은 2차 이동량으로만 더한다."
    },
    {
      "item_id": "PP-OPT152",
      "priority": "4",
      "title": "uncertainty rollback for huber adoption",
      "description": "meta quantile 폭, tail harm, Huber harm 확률이 클수록 Huber 보정을 PP126 쪽으로 되돌린다."
    },
    {
      "item_id": "PP-OPT153",
      "priority": "5",
      "title": "PP148 and huber stability ensemble",
      "description": "PP148 운영 후보와 안정화 Huber 후보를 작은 가중 평균으로 결합한다."
    },
    {
      "item_id": "PP-OPT154",
      "priority": "6",
      "title": "final huber adoption stabilization decision",
      "description": "PP126/PP148와 안정화 Huber 후보를 fixed/repeated 기준으로 비교한다."
    }
  ],
  "sources": {
    "pp143_helper": "scripts/track6/run_pp_opt143_148_warm_row_level_tail_router.py"
  }
}
```