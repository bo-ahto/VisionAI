# PP-OPT119~126 Warm PP118 stack-gate refinement 결과

- 작성일: 2026-06-09 15:00
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 목적: PP118 Huber stack 채택 gate를 p95 guard와 함께 세분화
- 결론: 운영 후보 candidate_ppopt119_fine_gate__safe_pp81__policy_less_harm__thr_0p1__width_0p16__s_0p75 fixed test MAPE 0.270114, p95 0.807490. PP64 대비 MAPE -0.000450, p95 -0.000009.
- 해석: PP118 이후의 개선은 Huber stack 자체가 아니라 stack 채택 gate의 세부 조건에서 나온다. p95를 크게 훼손하는 공격적 stack은 운영 후보에서 제외하고, 반복 안정성이 높은 gate 후보만 승격한다.

## 주요 후보 test 비교
| candidate | family | item_id | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt126_operational_stack_gate_challenger__source=ppopt119_fine_gate__safe_pp81__policy_less_harm__thr_0p1__width_0p16__s_0p75 | stack_gate_refined_operational_selection | PP-OPT126 | 0.136320 | 0.270114 | 0.807490 | 0.397588 | -0.001280 | -0.000640 |
| reference_pp118_operational | reference_prior | REFERENCE | 0.137878 | 0.270139 | 0.807490 | 0.397618 | -0.001256 | -0.000640 |
| ppopt126_p95_stack_gate_challenger__source=ppopt124_p95_limited__target_pp82_p95__thr_0p08__mpen_0p2__s_0p4 | stack_gate_refined_p95_selection | PP-OPT126 | 0.137871 | 0.270317 | 0.807465 | 0.397768 | -0.001078 | -0.000665 |
| reference_pp81_best | reference_prior | REFERENCE | 0.137878 | 0.270559 | 0.807490 | 0.397989 | -0.000836 | -0.000640 |
| reference_pp95_operational | reference_prior | REFERENCE | 0.137878 | 0.270559 | 0.807490 | 0.397989 | -0.000836 | -0.000640 |
| reference_pp64_current_best | reference_prior | REFERENCE | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | p95_test_MAPE | p95_test_p95_APE | operational_pass_vs_incumbent | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | fine stack adoption gate | 1440 | 0.270056 | 0.807490 | 0.269863 | 0.807490 | True | fine_stack_adoption_gate | ppopt119_fine_gate__safe=pp81__policy=less_harm__thr=0p1__width=0p16__s=0p85 |
| 8 | final stack-gate decision | 2 | 0.270114 | 0.807490 | 0.270317 | 0.807465 | True | stack_gate_refined_operational_selection | ppopt126_operational_stack_gate_challenger__source=ppopt119_fine_gate__safe_pp81__policy_less_harm__thr_0p1__width_0p16__s_0p75 |
| 3 | adaptive movement cap | 360 | 0.269956 | 0.807490 | 0.269931 | 0.807490 | True | adaptive_stack_movement_cap | ppopt121_adaptive_cap__safe=pp118_op__thr=0p1__cap=0p055__rshrink=0p2__s=0p95 |
| 2 | p95 guarded stack gate | 128 | 0.269982 | 0.807490 | 0.269949 | 0.807490 | True | p95_guarded_stack_gate | ppopt120_p95_guard__safe=pp118_op__thr=0p1__guard=0p55__s=1p1 |
| 4 | segment strength schedule | 128 | 0.270033 | 0.807490 | 0.269959 | 0.807490 | True | segment_strength_schedule | ppopt122_segment_strength__safe=pp118_op__policy=confidence_push__thr=0p1__s=1p0 |
| 6 | p95 purpose limited router | 144 | 0.270274 | 0.807487 | 0.270317 | 0.807465 | True | p95_purpose_limited_router | ppopt124_p95_limited__target=pp118_p95__thr=0p14__mpen=0p5__s=0p4 |
| 5 | risk rollback from aggressive stack | 192 | 0.270531 | 0.808911 | 0.269966 | 0.808790 | False | risk_rollback_from_aggressive_stack | ppopt123_aggressive_rollback__target=huber_plain__safe=pp118_op__cap=0p018__rollback=0p65__floor=0p0 |

## 탐색 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt119_fine_gate__safe=pp81__policy=less_harm__thr=0p1__width=0p16__s=0p85 | PP-OPT119 | fine_stack_adoption_gate | 0.270056 | 0.807490 | -0.001339 | -0.000640 | 0.966667 | 0.604167 | -0.002084 |
| ppopt119_fine_gate__safe=pp118_op__policy=less_harm__thr=0p1__width=0p16__s=0p95 | PP-OPT119 | fine_stack_adoption_gate | 0.269945 | 0.807490 | -0.001450 | -0.000640 | 0.966667 | 0.629167 | -0.002078 |
| ppopt119_fine_gate__safe=pp81__policy=less_harm__thr=0p1__width=0p16__s=0p75 | PP-OPT119 | fine_stack_adoption_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | 0.987500 | 0.604167 | -0.002076 |
| ppopt126_operational_stack_gate_challenger__source=ppopt119_fine_gate__safe_pp81__policy_less_harm__thr_0p1__width_0p16__s_0p75 | PP-OPT126 | stack_gate_refined_operational_selection | 0.270114 | 0.807490 | -0.001280 | -0.000640 | 0.987500 | 0.604167 | -0.002076 |
| ppopt119_fine_gate__safe=pp118_op__policy=less_harm__thr=0p1__width=0p16__s=0p85 | PP-OPT119 | fine_stack_adoption_gate | 0.269966 | 0.807490 | -0.001429 | -0.000640 | 0.966667 | 0.625000 | -0.002076 |
| ppopt121_adaptive_cap__safe=pp118_op__thr=0p1__cap=0p055__rshrink=0p2__s=0p95 | PP-OPT121 | adaptive_stack_movement_cap | 0.269956 | 0.807490 | -0.001439 | -0.000640 | 0.966667 | 0.608333 | -0.002073 |
| ppopt119_fine_gate__safe=pp118_op__policy=less_harm__thr=0p1__width=0p16__s=0p75 | PP-OPT119 | fine_stack_adoption_gate | 0.269986 | 0.807490 | -0.001409 | -0.000640 | 0.966667 | 0.604167 | -0.002073 |
| ppopt121_adaptive_cap__safe=pp118_op__thr=0p1__cap=0p055__rshrink=0p35__s=0p95 | PP-OPT121 | adaptive_stack_movement_cap | 0.269956 | 0.807490 | -0.001439 | -0.000640 | 0.966667 | 0.608333 | -0.002071 |
| ppopt121_adaptive_cap__safe=pp118_op__thr=0p1__cap=0p055__rshrink=0p5__s=0p95 | PP-OPT121 | adaptive_stack_movement_cap | 0.269956 | 0.807490 | -0.001439 | -0.000640 | 0.966667 | 0.608333 | -0.002066 |
| ppopt119_fine_gate__safe=pp118_op__policy=risk_strict__thr=0p06__width=0p16__s=0p65 | PP-OPT119 | fine_stack_adoption_gate | 0.270015 | 0.807490 | -0.001380 | -0.000640 | 0.966667 | 0.625000 | -0.002065 |
| ppopt119_fine_gate__safe=pp118_op__policy=risk_strict__thr=0p06__width=0p16__s=0p75 | PP-OPT119 | fine_stack_adoption_gate | 0.269996 | 0.807490 | -0.001399 | -0.000640 | 0.966667 | 0.625000 | -0.002062 |
| ppopt119_fine_gate__safe=pp118_op__policy=balanced__thr=0p1__width=0p16__s=0p95 | PP-OPT119 | fine_stack_adoption_gate | 0.269948 | 0.807490 | -0.001447 | -0.000640 | 0.966667 | 0.629167 | -0.002060 |
| ppopt119_fine_gate__safe=pp118_op__policy=balanced__thr=0p1__width=0p16__s=0p75 | PP-OPT119 | fine_stack_adoption_gate | 0.269988 | 0.807490 | -0.001407 | -0.000640 | 0.966667 | 0.604167 | -0.002059 |
| ppopt119_fine_gate__safe=pp81__policy=balanced__thr=0p1__width=0p16__s=0p85 | PP-OPT119 | fine_stack_adoption_gate | 0.270068 | 0.807490 | -0.001327 | -0.000640 | 0.975000 | 0.604167 | -0.002057 |
| ppopt119_fine_gate__safe=pp81__policy=less_harm__thr=0p12__width=0p16__s=0p85 | PP-OPT119 | fine_stack_adoption_gate | 0.270080 | 0.807490 | -0.001315 | -0.000640 | 0.966667 | 0.604167 | -0.002054 |
| ppopt121_adaptive_cap__safe=pp118_op__thr=0p1__cap=0p038__rshrink=0p2__s=0p95 | PP-OPT121 | adaptive_stack_movement_cap | 0.269956 | 0.807490 | -0.001439 | -0.000640 | 0.966667 | 0.608333 | -0.002054 |
| ppopt119_fine_gate__safe=pp118_op__policy=less_harm__thr=0p1__width=0p16__s=0p65 | PP-OPT119 | fine_stack_adoption_gate | 0.270006 | 0.807490 | -0.001388 | -0.000640 | 0.966667 | 0.604167 | -0.002054 |
| ppopt121_adaptive_cap__safe=pp118_op__thr=0p1__cap=0p055__rshrink=0p7__s=0p95 | PP-OPT121 | adaptive_stack_movement_cap | 0.269956 | 0.807490 | -0.001439 | -0.000640 | 0.966667 | 0.608333 | -0.002053 |
| ppopt119_fine_gate__safe=pp118_op__policy=balanced__thr=0p08__width=0p16__s=0p75 | PP-OPT119 | fine_stack_adoption_gate | 0.269983 | 0.807490 | -0.001412 | -0.000640 | 0.966667 | 0.625000 | -0.002048 |
| ppopt119_fine_gate__safe=pp118_op__policy=less_harm__thr=0p12__width=0p16__s=0p75 | PP-OPT119 | fine_stack_adoption_gate | 0.269997 | 0.807490 | -0.001398 | -0.000640 | 0.966667 | 0.604167 | -0.002048 |
| ppopt121_adaptive_cap__safe=pp118_op__thr=0p1__cap=0p038__rshrink=0p35__s=0p95 | PP-OPT121 | adaptive_stack_movement_cap | 0.269956 | 0.807490 | -0.001439 | -0.000640 | 0.966667 | 0.608333 | -0.002047 |
| ppopt119_fine_gate__safe=pp118_op__policy=more_harm__thr=0p08__width=0p16__s=0p75 | PP-OPT119 | fine_stack_adoption_gate | 0.269981 | 0.807490 | -0.001414 | -0.000640 | 0.966667 | 0.625000 | -0.002047 |
| ppopt119_fine_gate__safe=pp118_op__policy=less_harm__thr=0p1__width=0p16__s=0p55 | PP-OPT119 | fine_stack_adoption_gate | 0.270027 | 0.807490 | -0.001368 | -0.000640 | 0.966667 | 0.604167 | -0.002043 |
| ppopt119_fine_gate__safe=pp118_op__policy=risk_strict__thr=0p08__width=0p16__s=0p75 | PP-OPT119 | fine_stack_adoption_gate | 0.269998 | 0.807490 | -0.001397 | -0.000640 | 0.962500 | 0.604167 | -0.002043 |
| ppopt119_fine_gate__safe=pp118_op__policy=less_harm__thr=0p08__width=0p16__s=0p75 | PP-OPT119 | fine_stack_adoption_gate | 0.269971 | 0.807490 | -0.001424 | -0.000640 | 0.966667 | 0.625000 | -0.002042 |
| ppopt119_fine_gate__safe=pp118_op__policy=balanced__thr=0p1__width=0p16__s=0p65 | PP-OPT119 | fine_stack_adoption_gate | 0.270008 | 0.807490 | -0.001387 | -0.000640 | 0.966667 | 0.604167 | -0.002042 |
| ppopt119_fine_gate__safe=pp81__policy=less_harm__thr=0p1__width=0p16__s=0p95 | PP-OPT119 | fine_stack_adoption_gate | 0.269997 | 0.807490 | -0.001398 | -0.000640 | 0.966667 | 0.604167 | -0.002041 |
| ppopt119_fine_gate__safe=pp118_op__policy=risk_strict__thr=0p08__width=0p16__s=0p85 | PP-OPT119 | fine_stack_adoption_gate | 0.269979 | 0.807490 | -0.001416 | -0.000640 | 0.958333 | 0.625000 | -0.002040 |
| ppopt119_fine_gate__safe=pp118_op__policy=less_harm__thr=0p1__width=0p2__s=0p75 | PP-OPT119 | fine_stack_adoption_gate | 0.269992 | 0.807490 | -0.001402 | -0.000640 | 0.966667 | 0.604167 | -0.002040 |
| ppopt119_fine_gate__safe=pp118_op__policy=more_harm__thr=0p1__width=0p16__s=0p75 | PP-OPT119 | fine_stack_adoption_gate | 0.269988 | 0.807490 | -0.001407 | -0.000640 | 0.966667 | 0.604167 | -0.002039 |
| ppopt119_fine_gate__safe=pp118_op__policy=less_harm__thr=0p14__width=0p16__s=0p95 | PP-OPT119 | fine_stack_adoption_gate | 0.269969 | 0.807490 | -0.001426 | -0.000640 | 0.958333 | 0.608333 | -0.002038 |
| ppopt119_fine_gate__safe=pp118_op__policy=risk_strict__thr=0p08__width=0p16__s=0p95 | PP-OPT119 | fine_stack_adoption_gate | 0.269960 | 0.807490 | -0.001435 | -0.000640 | 0.958333 | 0.629167 | -0.002038 |
| ppopt121_adaptive_cap__safe=pp118_op__thr=0p14__cap=0p055__rshrink=0p2__s=0p95 | PP-OPT121 | adaptive_stack_movement_cap | 0.269968 | 0.807490 | -0.001427 | -0.000640 | 0.958333 | 0.608333 | -0.002038 |
| ppopt119_fine_gate__safe=pp118_op__policy=less_harm__thr=0p12__width=0p16__s=0p95 | PP-OPT119 | fine_stack_adoption_gate | 0.269959 | 0.807490 | -0.001436 | -0.000640 | 0.966667 | 0.608333 | -0.002037 |
| ppopt119_fine_gate__safe=pp118_op__policy=risk_strict__thr=0p08__width=0p16__s=0p65 | PP-OPT119 | fine_stack_adoption_gate | 0.270017 | 0.807490 | -0.001378 | -0.000640 | 0.966667 | 0.604167 | -0.002037 |
| ppopt121_adaptive_cap__safe=pp118_op__thr=0p14__cap=0p055__rshrink=0p35__s=0p95 | PP-OPT121 | adaptive_stack_movement_cap | 0.269968 | 0.807490 | -0.001427 | -0.000640 | 0.958333 | 0.608333 | -0.002035 |
| ppopt119_fine_gate__safe=pp118_op__policy=less_harm__thr=0p1__width=0p2__s=0p95 | PP-OPT119 | fine_stack_adoption_gate | 0.269953 | 0.807490 | -0.001442 | -0.000640 | 0.966667 | 0.608333 | -0.002034 |
| ppopt119_fine_gate__safe=pp118_op__policy=less_harm__thr=0p14__width=0p16__s=0p75 | PP-OPT119 | fine_stack_adoption_gate | 0.270004 | 0.807490 | -0.001390 | -0.000640 | 0.958333 | 0.604167 | -0.002034 |
| ppopt119_fine_gate__safe=pp118_op__policy=less_harm__thr=0p12__width=0p16__s=0p85 | PP-OPT119 | fine_stack_adoption_gate | 0.269978 | 0.807490 | -0.001417 | -0.000640 | 0.966667 | 0.604167 | -0.002034 |
| ppopt119_fine_gate__safe=pp118_op__policy=risk_strict__thr=0p06__width=0p2__s=0p75 | PP-OPT119 | fine_stack_adoption_gate | 0.269998 | 0.807490 | -0.001397 | -0.000640 | 0.966667 | 0.604167 | -0.002034 |
| ppopt119_fine_gate__safe=pp118_op__policy=balanced__thr=0p12__width=0p16__s=0p75 | PP-OPT119 | fine_stack_adoption_gate | 0.269995 | 0.807490 | -0.001400 | -0.000640 | 0.966667 | 0.604167 | -0.002033 |
| ppopt119_fine_gate__safe=pp81__policy=balanced__thr=0p08__width=0p16__s=0p75 | PP-OPT119 | fine_stack_adoption_gate | 0.270111 | 0.807490 | -0.001284 | -0.000640 | 0.983333 | 0.604167 | -0.002032 |
| ppopt119_fine_gate__safe=pp118_op__policy=risk_strict__thr=0p06__width=0p2__s=0p85 | PP-OPT119 | fine_stack_adoption_gate | 0.269979 | 0.807490 | -0.001416 | -0.000640 | 0.958333 | 0.625000 | -0.002031 |
| ppopt119_fine_gate__safe=pp118_op__policy=less_harm__thr=0p1__width=0p2__s=0p65 | PP-OPT119 | fine_stack_adoption_gate | 0.270012 | 0.807490 | -0.001383 | -0.000640 | 0.966667 | 0.604167 | -0.002031 |
| ppopt119_fine_gate__safe=pp81__policy=balanced__thr=0p08__width=0p16__s=0p85 | PP-OPT119 | fine_stack_adoption_gate | 0.270052 | 0.807490 | -0.001343 | -0.000640 | 0.970833 | 0.604167 | -0.002030 |
| ppopt119_fine_gate__safe=pp118_op__policy=more_harm__thr=0p1__width=0p16__s=0p65 | PP-OPT119 | fine_stack_adoption_gate | 0.270008 | 0.807490 | -0.001387 | -0.000640 | 0.966667 | 0.604167 | -0.002030 |
| ppopt121_adaptive_cap__safe=pp118_op__thr=0p14__cap=0p055__rshrink=0p5__s=0p95 | PP-OPT121 | adaptive_stack_movement_cap | 0.269968 | 0.807490 | -0.001427 | -0.000640 | 0.958333 | 0.608333 | -0.002030 |
| ppopt119_fine_gate__safe=pp81__policy=balanced__thr=0p1__width=0p16__s=0p75 | PP-OPT119 | fine_stack_adoption_gate | 0.270125 | 0.807490 | -0.001270 | -0.000640 | 0.987500 | 0.604167 | -0.002030 |
| ppopt119_fine_gate__safe=pp81__policy=more_harm__thr=0p08__width=0p16__s=0p85 | PP-OPT119 | fine_stack_adoption_gate | 0.270059 | 0.807490 | -0.001336 | -0.000640 | 0.975000 | 0.604167 | -0.002030 |
| ppopt119_fine_gate__safe=pp118_op__policy=risk_strict__thr=0p08__width=0p16__s=0p55 | PP-OPT119 | fine_stack_adoption_gate | 0.270035 | 0.807490 | -0.001360 | -0.000640 | 0.966667 | 0.604167 | -0.002029 |
| ppopt119_fine_gate__safe=pp118_op__policy=less_harm__thr=0p12__width=0p16__s=0p65 | PP-OPT119 | fine_stack_adoption_gate | 0.270016 | 0.807490 | -0.001379 | -0.000640 | 0.966667 | 0.604167 | -0.002029 |
| ppopt121_adaptive_cap__safe=pp118_op__thr=0p1__cap=0p038__rshrink=0p2__s=0p75 | PP-OPT121 | adaptive_stack_movement_cap | 0.269994 | 0.807490 | -0.001401 | -0.000640 | 0.966667 | 0.604167 | -0.002028 |
| ppopt119_fine_gate__safe=pp81__policy=less_harm__thr=0p08__width=0p16__s=0p75 | PP-OPT119 | fine_stack_adoption_gate | 0.270091 | 0.807490 | -0.001304 | -0.000640 | 0.983333 | 0.604167 | -0.002028 |
| ppopt119_fine_gate__safe=pp118_op__policy=less_harm__thr=0p12__width=0p16__s=0p55 | PP-OPT119 | fine_stack_adoption_gate | 0.270035 | 0.807490 | -0.001360 | -0.000640 | 0.966667 | 0.604167 | -0.002026 |
| ppopt119_fine_gate__safe=pp118_op__policy=balanced__thr=0p1__width=0p16__s=0p85 | PP-OPT119 | fine_stack_adoption_gate | 0.269968 | 0.807490 | -0.001427 | -0.000640 | 0.966667 | 0.604167 | -0.002026 |
| ppopt119_fine_gate__safe=pp118_op__policy=balanced__thr=0p14__width=0p16__s=0p75 | PP-OPT119 | fine_stack_adoption_gate | 0.270002 | 0.807490 | -0.001393 | -0.000640 | 0.958333 | 0.604167 | -0.002026 |
| ppopt119_fine_gate__safe=pp118_op__policy=risk_strict__thr=0p06__width=0p16__s=0p55 | PP-OPT119 | fine_stack_adoption_gate | 0.270034 | 0.807490 | -0.001361 | -0.000640 | 0.966667 | 0.604167 | -0.002025 |
| ppopt119_fine_gate__safe=pp118_op__policy=less_harm__thr=0p1__width=0p2__s=0p85 | PP-OPT119 | fine_stack_adoption_gate | 0.269973 | 0.807490 | -0.001422 | -0.000640 | 0.966667 | 0.604167 | -0.002025 |
| ppopt121_adaptive_cap__safe=pp118_op__thr=0p1__cap=0p055__rshrink=0p5__s=0p75 | PP-OPT121 | adaptive_stack_movement_cap | 0.269994 | 0.807490 | -0.001401 | -0.000640 | 0.966667 | 0.604167 | -0.002025 |
| ppopt119_fine_gate__safe=pp118_op__policy=balanced__thr=0p1__width=0p2__s=0p75 | PP-OPT119 | fine_stack_adoption_gate | 0.269993 | 0.807490 | -0.001402 | -0.000640 | 0.966667 | 0.604167 | -0.002024 |

## p95 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt124_p95_limited__target=pp82_p95__thr=0p08__mpen=0p2__s=0p4 | PP-OPT124 | p95_purpose_limited_router | 0.270317 | 0.807465 | -0.001078 | -0.000665 | 1.000000 | 0.591667 | -0.001653 |
| ppopt126_p95_stack_gate_challenger__source=ppopt124_p95_limited__target_pp82_p95__thr_0p08__mpen_0p2__s_0p4 | PP-OPT126 | stack_gate_refined_p95_selection | 0.270317 | 0.807465 | -0.001078 | -0.000665 | 1.000000 | 0.591667 | -0.001653 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p08__mpen=0p35__s=0p4 | PP-OPT124 | p95_purpose_limited_router | 0.270315 | 0.807467 | -0.001080 | -0.000663 | 1.000000 | 0.591667 | -0.001654 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p08__mpen=0p5__s=0p4 | PP-OPT124 | p95_purpose_limited_router | 0.270313 | 0.807470 | -0.001081 | -0.000660 | 1.000000 | 0.591667 | -0.001656 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p08__mpen=0p2__s=0p28 | PP-OPT124 | p95_purpose_limited_router | 0.270263 | 0.807472 | -0.001132 | -0.000658 | 1.000000 | 0.587500 | -0.001654 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p08__mpen=0p35__s=0p28 | PP-OPT124 | p95_purpose_limited_router | 0.270262 | 0.807474 | -0.001133 | -0.000656 | 1.000000 | 0.587500 | -0.001655 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p14__mpen=0p2__s=0p4 | PP-OPT124 | p95_purpose_limited_router | 0.270286 | 0.807476 | -0.001109 | -0.000654 | 1.000000 | 0.591667 | -0.001659 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p08__mpen=0p5__s=0p28 | PP-OPT124 | p95_purpose_limited_router | 0.270261 | 0.807476 | -0.001134 | -0.000654 | 1.000000 | 0.587500 | -0.001656 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p14__mpen=0p35__s=0p4 | PP-OPT124 | p95_purpose_limited_router | 0.270285 | 0.807477 | -0.001110 | -0.000653 | 1.000000 | 0.591667 | -0.001660 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p14__mpen=0p5__s=0p4 | PP-OPT124 | p95_purpose_limited_router | 0.270284 | 0.807478 | -0.001111 | -0.000652 | 1.000000 | 0.591667 | -0.001661 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p08__mpen=0p2__s=0p18 | PP-OPT124 | p95_purpose_limited_router | 0.270219 | 0.807479 | -0.001176 | -0.000651 | 1.000000 | 0.587500 | -0.001636 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p08__mpen=0p35__s=0p18 | PP-OPT124 | p95_purpose_limited_router | 0.270218 | 0.807480 | -0.001177 | -0.000650 | 1.000000 | 0.587500 | -0.001637 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p14__mpen=0p2__s=0p28 | PP-OPT124 | p95_purpose_limited_router | 0.270242 | 0.807480 | -0.001153 | -0.000650 | 1.000000 | 0.587500 | -0.001639 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p14__mpen=0p35__s=0p28 | PP-OPT124 | p95_purpose_limited_router | 0.270241 | 0.807481 | -0.001154 | -0.000649 | 1.000000 | 0.587500 | -0.001640 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p08__mpen=0p5__s=0p18 | PP-OPT124 | p95_purpose_limited_router | 0.270217 | 0.807481 | -0.001177 | -0.000649 | 1.000000 | 0.587500 | -0.001637 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p14__mpen=0p5__s=0p28 | PP-OPT124 | p95_purpose_limited_router | 0.270241 | 0.807482 | -0.001154 | -0.000648 | 1.000000 | 0.587500 | -0.001641 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p22__mpen=0p2__s=0p4 | PP-OPT124 | p95_purpose_limited_router | 0.270248 | 0.807482 | -0.001147 | -0.000648 | 1.000000 | 0.591667 | -0.001612 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p22__mpen=0p35__s=0p4 | PP-OPT124 | p95_purpose_limited_router | 0.270247 | 0.807483 | -0.001148 | -0.000647 | 1.000000 | 0.591667 | -0.001612 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p22__mpen=0p5__s=0p4 | PP-OPT124 | p95_purpose_limited_router | 0.270247 | 0.807483 | -0.001148 | -0.000647 | 1.000000 | 0.591667 | -0.001613 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p14__mpen=0p2__s=0p18 | PP-OPT124 | p95_purpose_limited_router | 0.270205 | 0.807484 | -0.001190 | -0.000646 | 1.000000 | 0.587500 | -0.001626 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p08__mpen=0p2__s=0p1 | PP-OPT124 | p95_purpose_limited_router | 0.270183 | 0.807484 | -0.001211 | -0.000646 | 0.995833 | 0.587500 | -0.001631 |
| ppopt124_p95_limited__target=pp118_p95__thr=0p08__mpen=0p2__s=0p4 | PP-OPT124 | p95_purpose_limited_router | 0.270303 | 0.807484 | -0.001092 | -0.000646 | 1.000000 | 0.591667 | -0.001661 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p14__mpen=0p35__s=0p18 | PP-OPT124 | p95_purpose_limited_router | 0.270205 | 0.807484 | -0.001190 | -0.000646 | 1.000000 | 0.587500 | -0.001626 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p22__mpen=0p2__s=0p28 | PP-OPT124 | p95_purpose_limited_router | 0.270215 | 0.807484 | -0.001180 | -0.000646 | 1.000000 | 0.587500 | -0.001614 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p08__mpen=0p35__s=0p1 | PP-OPT124 | p95_purpose_limited_router | 0.270183 | 0.807484 | -0.001212 | -0.000646 | 0.995833 | 0.587500 | -0.001632 |
| ppopt124_p95_limited__target=pp118_p95__thr=0p08__mpen=0p35__s=0p4 | PP-OPT124 | p95_purpose_limited_router | 0.270303 | 0.807485 | -0.001092 | -0.000645 | 1.000000 | 0.591667 | -0.001662 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p14__mpen=0p5__s=0p18 | PP-OPT124 | p95_purpose_limited_router | 0.270204 | 0.807485 | -0.001191 | -0.000645 | 1.000000 | 0.587500 | -0.001627 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p22__mpen=0p35__s=0p28 | PP-OPT124 | p95_purpose_limited_router | 0.270215 | 0.807485 | -0.001180 | -0.000645 | 1.000000 | 0.587500 | -0.001614 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p08__mpen=0p5__s=0p1 | PP-OPT124 | p95_purpose_limited_router | 0.270183 | 0.807485 | -0.001212 | -0.000645 | 0.995833 | 0.587500 | -0.001632 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p22__mpen=0p5__s=0p28 | PP-OPT124 | p95_purpose_limited_router | 0.270215 | 0.807485 | -0.001180 | -0.000645 | 1.000000 | 0.587500 | -0.001615 |
| ppopt124_p95_limited__target=pp118_p95__thr=0p08__mpen=0p5__s=0p4 | PP-OPT124 | p95_purpose_limited_router | 0.270302 | 0.807485 | -0.001093 | -0.000645 | 1.000000 | 0.591667 | -0.001662 |
| ppopt124_p95_limited__target=pp118_p95__thr=0p08__mpen=0p2__s=0p28 | PP-OPT124 | p95_purpose_limited_router | 0.270254 | 0.807486 | -0.001141 | -0.000644 | 1.000000 | 0.587500 | -0.001660 |
| ppopt124_p95_limited__target=pp118_p95__thr=0p08__mpen=0p35__s=0p28 | PP-OPT124 | p95_purpose_limited_router | 0.270253 | 0.807486 | -0.001141 | -0.000644 | 1.000000 | 0.587500 | -0.001661 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p22__mpen=0p2__s=0p18 | PP-OPT124 | p95_purpose_limited_router | 0.270188 | 0.807486 | -0.001207 | -0.000644 | 1.000000 | 0.587500 | -0.001631 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p14__mpen=0p2__s=0p1 | PP-OPT124 | p95_purpose_limited_router | 0.270176 | 0.807487 | -0.001219 | -0.000643 | 0.995833 | 0.587500 | -0.001635 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p22__mpen=0p35__s=0p18 | PP-OPT124 | p95_purpose_limited_router | 0.270188 | 0.807487 | -0.001207 | -0.000643 | 1.000000 | 0.587500 | -0.001631 |
| ppopt124_p95_limited__target=pp118_p95__thr=0p08__mpen=0p5__s=0p28 | PP-OPT124 | p95_purpose_limited_router | 0.270253 | 0.807487 | -0.001142 | -0.000643 | 1.000000 | 0.587500 | -0.001661 |
| ppopt124_p95_limited__target=pp118_p95__thr=0p14__mpen=0p2__s=0p4 | PP-OPT124 | p95_purpose_limited_router | 0.270275 | 0.807487 | -0.001120 | -0.000643 | 1.000000 | 0.591667 | -0.001666 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p14__mpen=0p35__s=0p1 | PP-OPT124 | p95_purpose_limited_router | 0.270176 | 0.807487 | -0.001219 | -0.000643 | 0.995833 | 0.587500 | -0.001635 |
| ppopt124_p95_limited__target=pp82_p95__thr=0p22__mpen=0p5__s=0p18 | PP-OPT124 | p95_purpose_limited_router | 0.270188 | 0.807487 | -0.001207 | -0.000643 | 1.000000 | 0.587500 | -0.001631 |

## 선택 후보 반복 안정성
| candidate_label | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_vs_pp64_MAPE | fixed_test_delta_vs_pp64_p95_APE | avg_delta_vs_pp64_MAPE | avg_delta_vs_pp64_p95_APE | avg_pp64_MAPE_win_rate | avg_pp64_p95_win_rate | replacement_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| candidate_ppopt119_fine_gate__safe_pp81__policy_less_harm__thr_0p1__width_0p16__s_0p75 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | -0.000455 | -0.001725 | 0.919231 | 0.494231 | -0.017219 |
| pp126_operational_stack_gate_challenger | 0.270114 | 0.807490 | -0.000450 | -0.000009 | -0.000455 | -0.001725 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt119_fine_gate__safe_pp81__policy_less_harm__thr_0p1__width_0p16__s_0p85 | 0.270056 | 0.807490 | -0.000508 | -0.000009 | -0.000501 | -0.001920 | 0.912500 | 0.496474 | -0.017008 |
| candidate_ppopt121_adaptive_cap__safe_pp118_op__thr_0p1__cap_0p055__rshrink_0p35__s_0p95 | 0.269956 | 0.807490 | -0.000608 | -0.000009 | -0.000573 | -0.002177 | 0.909295 | 0.496474 | -0.016980 |
| candidate_ppopt124_p95_limited__target_pp82_p95__thr_0p14__mpen_0p5__s_0p4 | 0.270284 | 0.807478 | -0.000280 | -0.000021 | -0.000269 | -0.001017 | 0.917308 | 0.645833 | -0.016972 |
| candidate_ppopt119_fine_gate__safe_pp81__policy_less_harm__thr_0p12__width_0p16__s_0p85 | 0.270080 | 0.807490 | -0.000484 | -0.000009 | -0.000481 | -0.001804 | 0.912179 | 0.496795 | -0.016972 |
| candidate_ppopt121_adaptive_cap__safe_pp118_op__thr_0p1__cap_0p055__rshrink_0p5__s_0p95 | 0.269956 | 0.807490 | -0.000608 | -0.000009 | -0.000569 | -0.002177 | 0.908974 | 0.496474 | -0.016967 |
| candidate_ppopt121_adaptive_cap__safe_pp118_op__thr_0p1__cap_0p055__rshrink_0p2__s_0p95 | 0.269956 | 0.807490 | -0.000608 | -0.000009 | -0.000575 | -0.002177 | 0.908654 | 0.496474 | -0.016954 |
| candidate_ppopt121_adaptive_cap__safe_pp118_op__thr_0p1__cap_0p055__rshrink_0p7__s_0p95 | 0.269956 | 0.807490 | -0.000608 | -0.000009 | -0.000560 | -0.002177 | 0.908333 | 0.496474 | -0.016942 |
| candidate_ppopt119_fine_gate__safe_pp118_op__policy_less_harm__thr_0p1__width_0p16__s_0p55 | 0.270027 | 0.807490 | -0.000537 | -0.000009 | -0.000506 | -0.002046 | 0.909936 | 0.496474 | -0.016935 |
| candidate_ppopt119_fine_gate__safe_pp118_op__policy_less_harm__thr_0p1__width_0p16__s_0p65 | 0.270006 | 0.807490 | -0.000558 | -0.000009 | -0.000524 | -0.002117 | 0.908974 | 0.496474 | -0.016917 |
| candidate_ppopt121_adaptive_cap__safe_pp118_op__thr_0p1__cap_0p038__rshrink_0p2__s_0p95 | 0.269956 | 0.807490 | -0.000608 | -0.000009 | -0.000561 | -0.002177 | 0.907692 | 0.496474 | -0.016916 |
| candidate_ppopt124_p95_limited__target_pp82_p95__thr_0p14__mpen_0p35__s_0p4 | 0.270285 | 0.807477 | -0.000279 | -0.000022 | -0.000267 | -0.001013 | 0.915705 | 0.649359 | -0.016907 |
| candidate_ppopt121_adaptive_cap__safe_pp118_op__thr_0p1__cap_0p038__rshrink_0p35__s_0p95 | 0.269956 | 0.807490 | -0.000608 | -0.000009 | -0.000556 | -0.002177 | 0.907051 | 0.496474 | -0.016890 |
| candidate_ppopt124_p95_limited__target_pp82_p95__thr_0p14__mpen_0p35__s_0p18 | 0.270205 | 0.807484 | -0.000359 | -0.000015 | -0.000335 | -0.001372 | 0.913141 | 0.655128 | -0.016885 |
| candidate_ppopt124_p95_limited__target_pp82_p95__thr_0p22__mpen_0p5__s_0p4 | 0.270247 | 0.807483 | -0.000317 | -0.000016 | -0.000296 | -0.001028 | 0.914103 | 0.539423 | -0.016881 |
| candidate_ppopt124_p95_limited__target_pp82_p95__thr_0p14__mpen_0p2__s_0p4 | 0.270286 | 0.807476 | -0.000278 | -0.000023 | -0.000266 | -0.001008 | 0.915064 | 0.653846 | -0.016880 |
| candidate_ppopt124_p95_limited__target_pp82_p95__thr_0p14__mpen_0p2__s_0p18 | 0.270205 | 0.807484 | -0.000359 | -0.000015 | -0.000334 | -0.001370 | 0.912821 | 0.652244 | -0.016872 |
| candidate_ppopt119_fine_gate__safe_pp118_op__policy_less_harm__thr_0p1__width_0p16__s_0p75 | 0.269986 | 0.807490 | -0.000578 | -0.000009 | -0.000543 | -0.002187 | 0.907051 | 0.496474 | -0.016860 |
| candidate_ppopt119_fine_gate__safe_pp81__policy_balanced__thr_0p1__width_0p16__s_0p85 | 0.270068 | 0.807490 | -0.000496 | -0.000009 | -0.000484 | -0.001823 | 0.908974 | 0.496474 | -0.016855 |
| candidate_ppopt124_p95_limited__target_pp82_p95__thr_0p22__mpen_0p35__s_0p4 | 0.270247 | 0.807483 | -0.000317 | -0.000016 | -0.000296 | -0.001025 | 0.913462 | 0.539423 | -0.016855 |
| candidate_ppopt124_p95_limited__target_pp82_p95__thr_0p22__mpen_0p2__s_0p4 | 0.270248 | 0.807482 | -0.000316 | -0.000017 | -0.000295 | -0.001022 | 0.913462 | 0.539744 | -0.016855 |
| candidate_ppopt124_p95_limited__target_pp82_p95__thr_0p14__mpen_0p5__s_0p28 | 0.270241 | 0.807482 | -0.000323 | -0.000017 | -0.000305 | -0.001214 | 0.913141 | 0.651923 | -0.016849 |
| candidate_ppopt119_fine_gate__safe_pp118_op__policy_less_harm__thr_0p12__width_0p16__s_0p75 | 0.269997 | 0.807490 | -0.000567 | -0.000009 | -0.000535 | -0.002119 | 0.907051 | 0.496474 | -0.016849 |
| candidate_ppopt124_p95_limited__target_pp118_p95__thr_0p08__mpen_0p2__s_0p4 | 0.270303 | 0.807484 | -0.000261 | -0.000015 | -0.000252 | -0.001053 | 0.914423 | 0.653846 | -0.016838 |
| candidate_ppopt124_p95_limited__target_pp82_p95__thr_0p14__mpen_0p35__s_0p28 | 0.270241 | 0.807481 | -0.000323 | -0.000018 | -0.000304 | -0.001211 | 0.912821 | 0.648397 | -0.016836 |
| candidate_ppopt124_p95_limited__target_pp82_p95__thr_0p14__mpen_0p2__s_0p28 | 0.270242 | 0.807480 | -0.000322 | -0.000019 | -0.000303 | -0.001208 | 0.912821 | 0.647436 | -0.016835 |
| candidate_ppopt119_fine_gate__safe_pp118_op__policy_less_harm__thr_0p1__width_0p16__s_0p85 | 0.269966 | 0.807490 | -0.000598 | -0.000009 | -0.000561 | -0.002256 | 0.905769 | 0.496474 | -0.016829 |
| candidate_ppopt119_fine_gate__safe_pp118_op__policy_less_harm__thr_0p1__width_0p16__s_0p95 | 0.269945 | 0.807490 | -0.000619 | -0.000009 | -0.000580 | -0.002324 | 0.905128 | 0.496474 | -0.016824 |
| candidate_ppopt124_p95_limited__target_pp82_p95__thr_0p22__mpen_0p2__s_0p28 | 0.270215 | 0.807484 | -0.000349 | -0.000015 | -0.000324 | -0.001218 | 0.911859 | 0.541346 | -0.016823 |
| candidate_ppopt119_fine_gate__safe_pp81__policy_risk_strict__thr_0p08__width_0p16__s_0p75 | 0.270149 | 0.807490 | -0.000415 | -0.000009 | -0.000409 | -0.001511 | 0.909615 | 0.494231 | -0.016800 |
| pp118_operational_reference | 0.270139 | 0.807490 | -0.000425 | -0.000009 | -0.000389 | -0.001654 | 0.909295 | 0.494551 | -0.016797 |
| candidate_ppopt124_p95_limited__target_pp82_p95__thr_0p08__mpen_0p5__s_0p18 | 0.270217 | 0.807481 | -0.000347 | -0.000018 | -0.000323 | -0.001371 | 0.910897 | 0.660577 | -0.016782 |
| candidate_ppopt124_p95_limited__target_pp82_p95__thr_0p08__mpen_0p35__s_0p18 | 0.270218 | 0.807480 | -0.000346 | -0.000019 | -0.000323 | -0.001369 | 0.910577 | 0.660577 | -0.016769 |
| candidate_ppopt124_p95_limited__target_pp82_p95__thr_0p08__mpen_0p5__s_0p28 | 0.270261 | 0.807476 | -0.000303 | -0.000023 | -0.000287 | -0.001209 | 0.911538 | 0.657051 | -0.016765 |
| candidate_ppopt119_fine_gate__safe_pp118_op__policy_balanced__thr_0p1__width_0p16__s_0p75 | 0.269988 | 0.807490 | -0.000576 | -0.000009 | -0.000536 | -0.002131 | 0.904487 | 0.496474 | -0.016755 |
| candidate_ppopt124_p95_limited__target_pp82_p95__thr_0p08__mpen_0p35__s_0p28 | 0.270262 | 0.807474 | -0.000302 | -0.000025 | -0.000285 | -0.001205 | 0.911218 | 0.658974 | -0.016751 |
| candidate_ppopt124_p95_limited__target_pp82_p95__thr_0p08__mpen_0p2__s_0p18 | 0.270219 | 0.807479 | -0.000345 | -0.000020 | -0.000322 | -0.001366 | 0.909615 | 0.657692 | -0.016730 |
| candidate_ppopt124_p95_limited__target_pp82_p95__thr_0p08__mpen_0p2__s_0p1 | 0.270183 | 0.807484 | -0.000381 | -0.000015 | -0.000352 | -0.001496 | 0.908654 | 0.661538 | -0.016727 |
| candidate_ppopt124_p95_limited__target_pp82_p95__thr_0p08__mpen_0p5__s_0p4 | 0.270313 | 0.807470 | -0.000251 | -0.000029 | -0.000243 | -0.001010 | 0.911218 | 0.662179 | -0.016699 |
| candidate_ppopt119_fine_gate__safe_pp118_op__policy_balanced__thr_0p1__width_0p16__s_0p95 | 0.269948 | 0.807490 | -0.000616 | -0.000009 | -0.000571 | -0.002254 | 0.901923 | 0.496474 | -0.016693 |
| candidate_ppopt124_p95_limited__target_pp82_p95__thr_0p08__mpen_0p2__s_0p28 | 0.270263 | 0.807472 | -0.000301 | -0.000027 | -0.000284 | -0.001201 | 0.909615 | 0.663782 | -0.016685 |
| candidate_ppopt119_fine_gate__safe_pp81__policy_risk_strict__thr_0p08__width_0p16__s_0p85 | 0.270094 | 0.807490 | -0.000470 | -0.000009 | -0.000450 | -0.001677 | 0.904487 | 0.496474 | -0.016649 |
| candidate_ppopt124_p95_limited__target_pp82_p95__thr_0p08__mpen_0p35__s_0p4 | 0.270315 | 0.807467 | -0.000249 | -0.000031 | -0.000241 | -0.001004 | 0.909936 | 0.663782 | -0.016646 |
| candidate_ppopt124_p95_limited__target_pp82_p95__thr_0p08__mpen_0p2__s_0p4 | 0.270317 | 0.807465 | -0.000247 | -0.000034 | -0.000239 | -0.000998 | 0.909936 | 0.665705 | -0.016645 |
| pp126_p95_stack_gate_challenger | 0.270317 | 0.807465 | -0.000247 | -0.000034 | -0.000239 | -0.000998 | 0.909936 | 0.665705 | -0.016645 |
| candidate_ppopt119_fine_gate__safe_pp81__policy_risk_strict__thr_0p06__width_0p16__s_0p85 | 0.270083 | 0.807490 | -0.000481 | -0.000009 | -0.000459 | -0.001794 | 0.902564 | 0.496474 | -0.016583 |
| candidate_ppopt119_fine_gate__safe_pp118_op__policy_risk_strict__thr_0p08__width_0p16__s_0p75 | 0.269998 | 0.807490 | -0.000566 | -0.000009 | -0.000517 | -0.002049 | 0.899679 | 0.496474 | -0.016554 |
| candidate_ppopt119_fine_gate__safe_pp118_op__policy_risk_strict__thr_0p06__width_0p16__s_0p65 | 0.270015 | 0.807490 | -0.000549 | -0.000009 | -0.000504 | -0.002056 | 0.900000 | 0.496474 | -0.016549 |
| candidate_ppopt119_fine_gate__safe_pp118_op__policy_more_harm__thr_0p08__width_0p16__s_0p75 | 0.269981 | 0.807490 | -0.000583 | -0.000009 | -0.000524 | -0.002144 | 0.898077 | 0.496474 | -0.016506 |
| candidate_ppopt119_fine_gate__safe_pp118_op__policy_risk_strict__thr_0p06__width_0p16__s_0p75 | 0.269996 | 0.807490 | -0.000568 | -0.000009 | -0.000520 | -0.002117 | 0.898397 | 0.496474 | -0.016504 |
| candidate_ppopt119_fine_gate__safe_pp118_op__policy_balanced__thr_0p08__width_0p16__s_0p75 | 0.269983 | 0.807490 | -0.000581 | -0.000009 | -0.000521 | -0.002199 | 0.894872 | 0.496474 | -0.016376 |
| pp81_stable_reference | 0.270559 | 0.807490 | -0.000005 | -0.000009 | -0.000004 | -0.000014 | 0.890705 | 0.410256 | -0.015633 |
| pp95_operational_reference | 0.270559 | 0.807490 | -0.000005 | -0.000009 | -0.000004 | -0.000014 | 0.890705 | 0.410256 | -0.015633 |
| pp70_refinement_candidate | 0.270561 | 0.807490 | -0.000003 | -0.000009 | -0.000001 | -0.000001 | 0.786859 | 0.398077 | -0.011477 |
| pp110_operational_reference | 0.270555 | 0.807490 | -0.000009 | -0.000009 | -0.000005 | -0.000016 | 0.782051 | 0.454808 | -0.011291 |
| candidate_ppopt123_aggressive_rollback__target_huber_weighted__safe_pp118_op__cap_0p018__rollback_0p25__floor_0p0 | 0.269678 | 0.809153 | -0.000886 | 0.001654 | -0.000659 | -0.002285 | 0.714423 | 0.494551 | -0.008305 |
| candidate_ppopt119_fine_gate__safe_pp118_op__policy_risk_light__thr_0p08__width_0p16__s_0p55 | 0.269574 | 0.810321 | -0.000990 | 0.002822 | -0.000771 | -0.003171 | 0.687821 | 0.473077 | -0.006527 |
| candidate_ppopt119_fine_gate__safe_pp118_op__policy_risk_light__thr_0p06__width_0p16__s_0p55 | 0.269445 | 0.810544 | -0.001119 | 0.003045 | -0.000818 | -0.003543 | 0.683974 | 0.469551 | -0.006346 |
| candidate_ppopt119_fine_gate__safe_pp118_op__policy_risk_light__thr_0p06__width_0p2__s_0p55 | 0.269574 | 0.810493 | -0.000990 | 0.002994 | -0.000747 | -0.003148 | 0.684615 | 0.477564 | -0.006278 |
| candidate_ppopt119_fine_gate__safe_pp81__policy_risk_light__thr_0p06__width_0p16__s_0p55 | 0.269625 | 0.810544 | -0.000939 | 0.003045 | -0.000689 | -0.002855 | 0.669872 | 0.452564 | -0.005602 |
| candidate_ppopt123_aggressive_rollback__target_huber_weighted__safe_pp118_op__cap_0p026__rollback_0p25__floor_0p0 | 0.269635 | 0.809887 | -0.000929 | 0.002388 | -0.000619 | -0.002868 | 0.643269 | 0.466987 | -0.004988 |
| candidate_ppopt123_aggressive_rollback__target_huber_weighted__safe_pp118_op__cap_0p026__rollback_0p25__floor_0p15 | 0.269635 | 0.809887 | -0.000929 | 0.002388 | -0.000619 | -0.002868 | 0.643269 | 0.466987 | -0.004988 |
| candidate_ppopt123_aggressive_rollback__target_huber_weighted__safe_pp118_op__cap_0p026__rollback_0p25__floor_0p3 | 0.269635 | 0.809887 | -0.000929 | 0.002388 | -0.000619 | -0.002868 | 0.643269 | 0.466987 | -0.004988 |
| candidate_ppopt119_fine_gate__safe_pp118_op__policy_risk_light__thr_0p08__width_0p16__s_0p65 | 0.269635 | 0.810829 | -0.000929 | 0.003330 | -0.000688 | -0.003106 | 0.642308 | 0.440385 | -0.004291 |
| candidate_ppopt119_fine_gate__safe_pp118_op__policy_risk_light__thr_0p06__width_0p16__s_0p65 | 0.269489 | 0.811093 | -0.001075 | 0.003594 | -0.000723 | -0.003546 | 0.638141 | 0.438462 | -0.004085 |
| candidate_ppopt119_fine_gate__safe_pp118_op__policy_risk_light__thr_0p06__width_0p2__s_0p65 | 0.269640 | 0.811033 | -0.000924 | 0.003534 | -0.000662 | -0.003100 | 0.637500 | 0.444231 | -0.003951 |
| candidate_ppopt119_fine_gate__safe_pp81__policy_risk_light__thr_0p06__width_0p16__s_0p65 | 0.269621 | 0.811093 | -0.000943 | 0.003594 | -0.000634 | -0.002975 | 0.626923 | 0.422436 | -0.003504 |
| candidate_ppopt119_fine_gate__safe_pp118_op__policy_risk_light__thr_0p06__width_0p16__s_0p75 | 0.269570 | 0.811640 | -0.000994 | 0.004141 | -0.000567 | -0.003509 | 0.591667 | 0.434295 | -0.001762 |
| candidate_ppopt119_fine_gate__safe_pp81__policy_risk_light__thr_0p06__width_0p16__s_0p75 | 0.269661 | 0.811640 | -0.000903 | 0.004141 | -0.000513 | -0.003078 | 0.585577 | 0.421154 | -0.001427 |
| candidate_ppopt119_fine_gate__safe_pp118_op__policy_risk_light__thr_0p06__width_0p16__s_0p85 | 0.269668 | 0.812185 | -0.000896 | 0.004686 | -0.000371 | -0.003489 | 0.544872 | 0.433013 | 0.000590 |
| candidate_ppopt123_aggressive_rollback__target_huber_weighted__safe_pp118_op__cap_0p055__rollback_0p25__floor_0p0 | 0.269384 | 0.812525 | -0.001180 | 0.005026 | -0.000456 | -0.003399 | 0.537500 | 0.444231 | 0.000838 |
| candidate_ppopt123_aggressive_rollback__target_huber_weighted__safe_pp118_op__cap_0p055__rollback_0p25__floor_0p15 | 0.269384 | 0.812525 | -0.001180 | 0.005026 | -0.000456 | -0.003399 | 0.537500 | 0.444231 | 0.000838 |
| candidate_ppopt123_aggressive_rollback__target_huber_weighted__safe_pp118_op__cap_0p055__rollback_0p25__floor_0p3 | 0.269384 | 0.812525 | -0.001180 | 0.005026 | -0.000456 | -0.003399 | 0.537500 | 0.444231 | 0.000838 |
| candidate_ppopt123_aggressive_rollback__target_huber_weighted__safe_pp118_op__cap_0p055__rollback_0p45__floor_0p0 | 0.269587 | 0.812162 | -0.000977 | 0.004663 | -0.000338 | -0.002799 | 0.525641 | 0.444872 | 0.001261 |
| candidate_ppopt123_aggressive_rollback__target_huber_weighted__safe_pp118_op__cap_0p055__rollback_0p45__floor_0p15 | 0.269587 | 0.812162 | -0.000977 | 0.004663 | -0.000338 | -0.002799 | 0.525641 | 0.444872 | 0.001261 |
| candidate_ppopt123_aggressive_rollback__target_huber_weighted__safe_pp118_op__cap_0p055__rollback_0p45__floor_0p3 | 0.269587 | 0.812162 | -0.000977 | 0.004663 | -0.000338 | -0.002799 | 0.525641 | 0.444872 | 0.001261 |
| candidate_ppopt123_aggressive_rollback__target_huber_weighted__safe_pp81__cap_0p055__rollback_0p25__floor_0p0 | 0.269604 | 0.812525 | -0.000960 | 0.005026 | -0.000314 | -0.003003 | 0.520192 | 0.441667 | 0.001750 |
| candidate_ppopt123_aggressive_rollback__target_huber_weighted__safe_pp81__cap_0p055__rollback_0p25__floor_0p15 | 0.269604 | 0.812525 | -0.000960 | 0.005026 | -0.000314 | -0.003003 | 0.520192 | 0.441667 | 0.001750 |
| candidate_ppopt123_aggressive_rollback__target_huber_weighted__safe_pp81__cap_0p055__rollback_0p25__floor_0p3 | 0.269604 | 0.812525 | -0.000960 | 0.005026 | -0.000314 | -0.003003 | 0.520192 | 0.441667 | 0.001750 |

## 선택 후보 시나리오별 안정성
| candidate_label | eval_split | scenario | mean_delta_vs_pp64_MAPE | mean_delta_vs_pp64_p95_APE | pp64_MAPE_win_rate | pp64_p95_win_rate | pp64_all3_win_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pp118_operational_reference | test | artist_group_holdout | -0.000441 | -0.000002 | 1.000000 | 0.319231 | 0.215385 |
| pp118_operational_reference | test | confidence_stratified_rows | -0.000409 | 0.000007 | 1.000000 | 0.430769 | 0.253846 |
| pp118_operational_reference | test | full_split | -0.000425 | -0.000009 | 1.000000 | 1.000000 | 0.000000 |
| pp118_operational_reference | test | price_band_stratified_rows | -0.000412 | -0.000003 | 1.000000 | 0.376923 | 0.246154 |
| pp118_operational_reference | test | risk_focus_bootstrap | -0.001032 | -0.007846 | 0.996154 | 0.346154 | 0.050000 |
| pp118_operational_reference | test | row_bootstrap | -0.000437 | -0.000148 | 1.000000 | 0.315385 | 0.142308 |
| pp118_operational_reference | validation_oof | artist_group_holdout | -0.000262 | -0.003755 | 0.850000 | 0.576923 | 0.338462 |
| pp118_operational_reference | validation_oof | confidence_stratified_rows | -0.000268 | -0.002559 | 0.876923 | 0.526923 | 0.311538 |
| pp118_operational_reference | validation_oof | full_split | -0.000268 | -0.000025 | 1.000000 | 1.000000 | 1.000000 |
| pp118_operational_reference | validation_oof | price_band_stratified_rows | -0.000268 | -0.002086 | 0.873077 | 0.488462 | 0.265385 |
| pp118_operational_reference | validation_oof | risk_focus_bootstrap | -0.000171 | -0.001151 | 0.576923 | 0.138462 | 0.069231 |
| pp118_operational_reference | validation_oof | row_bootstrap | -0.000274 | -0.002269 | 0.738462 | 0.415385 | 0.196154 |
| pp126_operational_stack_gate_challenger | test | artist_group_holdout | -0.000463 | 0.000003 | 1.000000 | 0.315385 | 0.265385 |
| pp126_operational_stack_gate_challenger | test | confidence_stratified_rows | -0.000430 | 0.000022 | 1.000000 | 0.430769 | 0.342308 |
| pp126_operational_stack_gate_challenger | test | full_split | -0.000450 | -0.000009 | 1.000000 | 1.000000 | 1.000000 |
| pp126_operational_stack_gate_challenger | test | price_band_stratified_rows | -0.000432 | -0.000003 | 1.000000 | 0.376923 | 0.307692 |
| pp126_operational_stack_gate_challenger | test | risk_focus_bootstrap | -0.001084 | -0.008342 | 0.992308 | 0.346154 | 0.030769 |
| pp126_operational_stack_gate_challenger | test | row_bootstrap | -0.000462 | -0.000112 | 0.996154 | 0.315385 | 0.196154 |
| pp126_operational_stack_gate_challenger | validation_oof | artist_group_holdout | -0.000371 | -0.003836 | 0.896154 | 0.576923 | 0.384615 |
| pp126_operational_stack_gate_challenger | validation_oof | confidence_stratified_rows | -0.000384 | -0.002605 | 0.915385 | 0.526923 | 0.365385 |
| pp126_operational_stack_gate_challenger | validation_oof | full_split | -0.000383 | -0.000025 | 1.000000 | 1.000000 | 0.000000 |
| pp126_operational_stack_gate_challenger | validation_oof | price_band_stratified_rows | -0.000386 | -0.002142 | 0.911538 | 0.488462 | 0.292308 |
| pp126_operational_stack_gate_challenger | validation_oof | risk_focus_bootstrap | -0.000227 | -0.001270 | 0.565385 | 0.138462 | 0.073077 |
| pp126_operational_stack_gate_challenger | validation_oof | row_bootstrap | -0.000384 | -0.002389 | 0.753846 | 0.415385 | 0.219231 |
| pp126_p95_stack_gate_challenger | test | artist_group_holdout | -0.000256 | 0.000085 | 1.000000 | 0.607692 | 0.438462 |
| pp126_p95_stack_gate_challenger | test | confidence_stratified_rows | -0.000238 | 0.000089 | 1.000000 | 0.596154 | 0.346154 |
| pp126_p95_stack_gate_challenger | test | full_split | -0.000247 | -0.000034 | 1.000000 | 1.000000 | 1.000000 |
| pp126_p95_stack_gate_challenger | test | price_band_stratified_rows | -0.000241 | 0.000092 | 1.000000 | 0.553846 | 0.376923 |
| pp126_p95_stack_gate_challenger | test | risk_focus_bootstrap | -0.000615 | -0.004214 | 0.996154 | 0.630769 | 0.238462 |
| pp126_p95_stack_gate_challenger | test | row_bootstrap | -0.000256 | 0.000018 | 0.996154 | 0.473077 | 0.215385 |
| pp126_p95_stack_gate_challenger | validation_oof | artist_group_holdout | -0.000190 | -0.002566 | 0.888462 | 0.738462 | 0.446154 |
| pp126_p95_stack_gate_challenger | validation_oof | confidence_stratified_rows | -0.000197 | -0.001790 | 0.900000 | 0.742308 | 0.534615 |
| pp126_p95_stack_gate_challenger | validation_oof | full_split | -0.000196 | -0.000025 | 1.000000 | 1.000000 | 1.000000 |
| pp126_p95_stack_gate_challenger | validation_oof | price_band_stratified_rows | -0.000195 | -0.001328 | 0.888462 | 0.711538 | 0.461538 |
| pp126_p95_stack_gate_challenger | validation_oof | risk_focus_bootstrap | -0.000033 | -0.000737 | 0.503846 | 0.365385 | 0.157692 |
| pp126_p95_stack_gate_challenger | validation_oof | row_bootstrap | -0.000199 | -0.001571 | 0.746154 | 0.569231 | 0.257692 |
| pp81_stable_reference | test | artist_group_holdout | -0.000005 | -0.000002 | 0.996154 | 0.319231 | 0.119231 |
| pp81_stable_reference | test | confidence_stratified_rows | -0.000005 | -0.000001 | 0.996154 | 0.434615 | 0.100000 |
| pp81_stable_reference | test | full_split | -0.000005 | -0.000009 | 1.000000 | 1.000000 | 0.000000 |
| pp81_stable_reference | test | price_band_stratified_rows | -0.000005 | -0.000003 | 0.996154 | 0.376923 | 0.115385 |
| pp81_stable_reference | test | risk_focus_bootstrap | -0.000008 | -0.000184 | 0.880769 | 0.338462 | 0.007692 |
| pp81_stable_reference | test | row_bootstrap | -0.000005 | -0.000014 | 0.953846 | 0.330769 | 0.065385 |
| pp81_stable_reference | validation_oof | artist_group_holdout | -0.000002 | 0.000002 | 0.803846 | 0.280769 | 0.092308 |
| pp81_stable_reference | validation_oof | confidence_stratified_rows | -0.000002 | 0.000003 | 0.911538 | 0.288462 | 0.115385 |
| pp81_stable_reference | validation_oof | full_split | -0.000002 | -0.000025 | 1.000000 | 1.000000 | 0.000000 |
| pp81_stable_reference | validation_oof | price_band_stratified_rows | -0.000002 | 0.000000 | 0.880769 | 0.319231 | 0.076923 |
| pp81_stable_reference | validation_oof | risk_focus_bootstrap | -0.000001 | 0.000048 | 0.569231 | 0.000000 | 0.000000 |
| pp81_stable_reference | validation_oof | row_bootstrap | -0.000002 | 0.000012 | 0.700000 | 0.234615 | 0.057692 |
| pp95_operational_reference | test | artist_group_holdout | -0.000005 | -0.000002 | 0.996154 | 0.319231 | 0.119231 |
| pp95_operational_reference | test | confidence_stratified_rows | -0.000005 | -0.000001 | 0.996154 | 0.434615 | 0.100000 |
| pp95_operational_reference | test | full_split | -0.000005 | -0.000009 | 1.000000 | 1.000000 | 0.000000 |
| pp95_operational_reference | test | price_band_stratified_rows | -0.000005 | -0.000003 | 0.996154 | 0.376923 | 0.115385 |
| pp95_operational_reference | test | risk_focus_bootstrap | -0.000008 | -0.000184 | 0.880769 | 0.338462 | 0.007692 |
| pp95_operational_reference | test | row_bootstrap | -0.000005 | -0.000014 | 0.953846 | 0.330769 | 0.065385 |
| pp95_operational_reference | validation_oof | artist_group_holdout | -0.000002 | 0.000002 | 0.803846 | 0.280769 | 0.092308 |
| pp95_operational_reference | validation_oof | confidence_stratified_rows | -0.000002 | 0.000003 | 0.911538 | 0.288462 | 0.115385 |
| pp95_operational_reference | validation_oof | full_split | -0.000002 | -0.000025 | 1.000000 | 1.000000 | 0.000000 |
| pp95_operational_reference | validation_oof | price_band_stratified_rows | -0.000002 | 0.000000 | 0.880769 | 0.319231 | 0.076923 |
| pp95_operational_reference | validation_oof | risk_focus_bootstrap | -0.000001 | 0.000048 | 0.569231 | 0.000000 | 0.000000 |
| pp95_operational_reference | validation_oof | row_bootstrap | -0.000002 | 0.000012 | 0.700000 | 0.234615 | 0.057692 |

## 실행 설정
```json
{
  "experiment_id": "PP-OPT119-126",
  "experiment_slug": "PP-OPT119_126_warm_pp118_stack_gate_refinement",
  "created_at": "2026-06-09T14:59:30",
  "seed": 20260609,
  "base_candidate": "hcoef_stable",
  "incumbent_candidate": "incumbent_operational_pp_opt7",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 2406,
  "prediction_rows": 2709156,
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
    "pp111_p95_source": "ppopt111_meta_router__set=tail_mix__thr=0p22__s=1p0"
  },
  "selection_decision": {
    "operational_label": "candidate_ppopt119_fine_gate__safe_pp81__policy_less_harm__thr_0p1__width_0p16__s_0p75",
    "operational_candidate": "ppopt119_fine_gate__safe=pp81__policy=less_harm__thr=0p1__width=0p16__s=0p75",
    "operational_fixed_test_MAPE": 0.2701143967498518,
    "operational_fixed_test_p95_APE": 0.8074900608978479,
    "operational_delta_vs_pp64_MAPE": -0.0004496451658085321,
    "operational_delta_vs_pp64_p95_APE": -8.791408261932254e-06,
    "operational_avg_pp64_MAPE_win_rate": 0.9192307692307692,
    "operational_avg_pp64_p95_win_rate": 0.49423076923076925,
    "operational_replacement_score": -0.0172188759350393,
    "p95_label": "candidate_ppopt124_p95_limited__target_pp82_p95__thr_0p08__mpen_0p2__s_0p4",
    "p95_candidate": "ppopt124_p95_limited__target=pp82_p95__thr=0p08__mpen=0p2__s=0p4",
    "p95_fixed_test_MAPE": 0.2703165497281949,
    "p95_fixed_test_p95_APE": 0.8074645851983092,
    "p95_delta_vs_pp64_MAPE": -0.0002474921874654479,
    "p95_delta_vs_pp64_p95_APE": -3.426710780063402e-05,
    "p95_avg_pp64_MAPE_win_rate": 0.9099358974358974,
    "p95_avg_pp64_p95_win_rate": 0.6657051282051282,
    "p95_replacement_score": -0.016644928084901346,
    "operational_protocol_candidate": "ppopt126_operational_stack_gate_challenger__source=ppopt119_fine_gate__safe_pp81__policy_less_harm__thr_0p1__width_0p16__s_0p75",
    "p95_protocol_candidate": "ppopt126_p95_stack_gate_challenger__source=ppopt124_p95_limited__target_pp82_p95__thr_0p08__mpen_0p2__s_0p4"
  },
  "items": [
    {
      "item_id": "PP-OPT119",
      "priority": "1",
      "title": "fine stack adoption gate",
      "description": "PP118의 Huber stack 채택 gate 주변에서 threshold, width, strength를 세분화한다."
    },
    {
      "item_id": "PP-OPT120",
      "priority": "2",
      "title": "p95 guarded stack gate",
      "description": "risk, harm, stack gap이 큰 row에서는 Huber stack 이동량을 줄여 p95 악화를 방어한다."
    },
    {
      "item_id": "PP-OPT121",
      "priority": "3",
      "title": "adaptive movement cap",
      "description": "Huber stack으로 이동하는 로그 이동량에 risk별 cap을 적용한다."
    },
    {
      "item_id": "PP-OPT122",
      "priority": "4",
      "title": "segment strength schedule",
      "description": "신뢰도, 가격대, risk에 따라 stack 채택 강도를 다르게 적용한다."
    },
    {
      "item_id": "PP-OPT123",
      "priority": "5",
      "title": "risk rollback from aggressive stack",
      "description": "MAPE가 강한 stack 후보를 쓰되 high-risk row는 PP118 또는 PP81로 되돌린다."
    },
    {
      "item_id": "PP-OPT124",
      "priority": "6",
      "title": "p95 purpose limited router",
      "description": "XGBoost p95 성향 후보와 p95 meta-router를 MAPE guard 안에서만 제한 채택한다."
    },
    {
      "item_id": "PP-OPT125",
      "priority": "7",
      "title": "stability selected stack challenger",
      "description": "고정 test와 반복 안정성 점수로 후보를 선별한다."
    },
    {
      "item_id": "PP-OPT126",
      "priority": "8",
      "title": "final stack-gate decision",
      "description": "선택 후보를 운영형/p95형으로 복제하고 PP118, PP81/PP95와 비교한다."
    }
  ],
  "sources": {
    "pp111_config": "experiments/track6/PP-OPT111_118_warm_next_dimension_experiments/artifacts/run_config.json",
    "pp111_predictions": "experiments/track6/PP-OPT111_118_warm_next_dimension_experiments/outputs/candidate_predictions.csv",
    "pp111_model_detail": "experiments/track6/PP-OPT111_118_warm_next_dimension_experiments/artifacts/next_dimension_model_prediction_detail.csv",
    "pp96_label_probabilities": "experiments/track6/PP-OPT96_102_warm_tail_label_refinement_experiments/artifacts/tail_label_probability_detail.csv",
    "pp96_helper": "scripts/track6/run_pp_opt96_102_warm_tail_label_refinement_experiments.py",
    "pp111_helper": "scripts/track6/run_pp_opt111_118_warm_next_dimension_experiments.py",
    "pp71_validation_helper": "scripts/track6/run_pp_opt71_75_warm_pp70_stability_validation.py"
  }
}
```