# PP-OPT127~134 Warm learned stack-correction 결과

- 작성일: 2026-06-09 15:45
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 목적: PP126 이후 보정 적용 여부/강도를 LightGBM learned gate로 세분화
- 결론: 운영 learned 후보 fixed test MAPE 0.270033, p95 0.807490. PP64 대비 MAPE -0.000531, p95 -0.000009; PP126 대비 MAPE -0.000081, p95 +0.000000.
- 해석: 이번 실험은 보정 모델 자체를 바꾸기보다, PP126 위에서 보정을 적용할 row와 강도를 학습했다. LightGBM gain/harm/direction 신호가 PP126보다 추가 개선을 만들면 운영 후보로 볼 수 있고, 그렇지 않으면 PP126의 수동 gate가 아직 더 안정적인 기준이라는 뜻이다.

## 주요 후보 test 비교
| candidate | family | item_id | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| reference_pp119_guarded_mape | reference_prior | REFERENCE | 0.137878 | 0.269759 | 0.807513 | 0.396632 | -0.001636 | -0.000617 |
| ppopt134_operational_learned_stack_correction_challenger__source=ppopt128_harm_rollback__thr_0p12__pre_0p55__guard_0p35__floor_0p0__cap_0p018 | learned_stack_correction_operational_selection | PP-OPT134 | 0.136320 | 0.270033 | 0.807490 | 0.397520 | -0.001362 | -0.000640 |
| reference_pp126_operational | reference_prior | REFERENCE | 0.136320 | 0.270114 | 0.807490 | 0.397588 | -0.001280 | -0.000640 |
| ppopt134_p95_learned_stack_correction_challenger__source=ppopt130_p95_tail_router__target_pp82_p95__thr_0p3__width_0p18__s_0p55__cap_0p008 | learned_stack_correction_p95_selection | PP-OPT134 | 0.136320 | 0.270242 | 0.807488 | 0.397692 | -0.001153 | -0.000641 |
| reference_pp126_p95 | reference_prior | REFERENCE | 0.137871 | 0.270317 | 0.807465 | 0.397768 | -0.001078 | -0.000665 |
| reference_pp64_current_best | reference_prior | REFERENCE | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | p95_test_MAPE | p95_test_p95_APE | operational_pass_vs_incumbent | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | segment adaptive learned threshold | 486 | 0.269978 | 0.808105 | 0.270052 | 0.807766 | True | segment_adaptive_learned_threshold | ppopt131_segment_threshold__base=0p5__rslope=0p22__segpen=0p12__width=0p18__s=0p85__cap=0p045 |
| 2 | learned harm rollback | 576 | 0.269992 | 0.807490 | 0.269940 | 0.807490 | True | learned_harm_rollback | ppopt128_harm_rollback__thr=0p1__pre=0p85__guard=0p35__floor=0p0__cap=0p018 |
| 8 | final learned correction decision | 2 | 0.270033 | 0.807490 | 0.270242 | 0.807488 | True | learned_stack_correction_operational_selection | ppopt134_operational_learned_stack_correction_challenger__source=ppopt128_harm_rollback__thr_0p12__pre_0p55__guard_0p35__floor_0p0__cap_0p018 |
| 4 | learned p95 tail router | 360 | 0.270118 | 0.807490 | 0.270242 | 0.807488 | True | learned_p95_tail_router | ppopt130_p95_tail_router__target=pp126_p95__thr=0p54__width=0p26__s=0p4__cap=0p008 |
| 7 | aggressive correction with learned guard | 512 | 0.270010 | 0.807490 | 0.269955 | 0.807490 | True | aggressive_correction_with_learned_guard | ppopt133_aggressive_guard__thr=0p28__width=0p18__guard=0p45__cap=0p03__s=0p5 |
| 1 | learned stack gain gate | 2304 | 0.270129 | 0.807942 | 0.269941 | 0.807490 | True | learned_stack_gain_gate | ppopt127_learned_gain_gate__safe=pp126_op__target=stack_huber_plain__hpen=0p65__rpen=0p45__thr=0p56__width=0p26__cap=0p014__s=0p45 |
| 3 | learned residual direction correction | 96 | 0.270280 | 0.808400 | 0.270171 | 0.808306 | False | learned_residual_direction_correction | ppopt129_residual_direction__resid=residual_l1__s=0p45__cap=0p006__rshrink=0p6 |
| 6 | learned correction ensemble | 243 | 0.269829 | 0.809224 | 0.269870 | 0.809137 | False | learned_correction_ensemble | ppopt132_correction_ensemble__sw=0p8__pw=0p1__rw=0p15__cap=0p014__shrink=0p65 |

## 탐색 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt131_segment_threshold__base=0p5__rslope=0p22__segpen=0p12__width=0p18__s=0p85__cap=0p045 | PP-OPT131 | segment_adaptive_learned_threshold | 0.269978 | 0.808105 | -0.001417 | -0.000025 | 1.000000 | 0.604167 | -0.002282 |
| ppopt131_segment_threshold__base=0p5__rslope=0p22__segpen=0p12__width=0p18__s=0p85__cap=0p03 | PP-OPT131 | segment_adaptive_learned_threshold | 0.269978 | 0.808105 | -0.001417 | -0.000025 | 1.000000 | 0.604167 | -0.002266 |
| ppopt131_segment_threshold__base=0p5__rslope=0p22__segpen=0p12__width=0p18__s=0p7__cap=0p045 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270002 | 0.807997 | -0.001393 | -0.000133 | 0.995833 | 0.604167 | -0.002253 |
| ppopt131_segment_threshold__base=0p5__rslope=0p22__segpen=0p12__width=0p18__s=0p7__cap=0p03 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270002 | 0.807997 | -0.001393 | -0.000133 | 0.995833 | 0.604167 | -0.002251 |
| ppopt131_segment_threshold__base=0p5__rslope=0p22__segpen=0p12__width=0p26__s=0p85__cap=0p03 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270019 | 0.807916 | -0.001376 | -0.000214 | 0.995833 | 0.604167 | -0.002238 |
| ppopt131_segment_threshold__base=0p5__rslope=0p22__segpen=0p12__width=0p26__s=0p85__cap=0p045 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270019 | 0.807916 | -0.001376 | -0.000214 | 0.995833 | 0.604167 | -0.002238 |
| ppopt131_segment_threshold__base=0p5__rslope=0p22__segpen=0p12__width=0p18__s=0p85__cap=0p018 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270036 | 0.808105 | -0.001359 | -0.000025 | 0.995833 | 0.604167 | -0.002212 |
| ppopt131_segment_threshold__base=0p5__rslope=0p22__segpen=0p12__width=0p18__s=0p55__cap=0p03 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270026 | 0.807889 | -0.001369 | -0.000241 | 0.991667 | 0.604167 | -0.002211 |
| ppopt131_segment_threshold__base=0p5__rslope=0p22__segpen=0p12__width=0p18__s=0p55__cap=0p045 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270026 | 0.807889 | -0.001369 | -0.000241 | 0.991667 | 0.604167 | -0.002211 |
| ppopt131_segment_threshold__base=0p5__rslope=0p22__segpen=0p12__width=0p18__s=0p7__cap=0p018 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270032 | 0.807997 | -0.001363 | -0.000133 | 0.991667 | 0.604167 | -0.002208 |
| ppopt131_segment_threshold__base=0p5__rslope=0p22__segpen=0p12__width=0p26__s=0p7__cap=0p03 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270035 | 0.807841 | -0.001359 | -0.000289 | 0.991667 | 0.604167 | -0.002204 |
| ppopt131_segment_threshold__base=0p5__rslope=0p22__segpen=0p12__width=0p26__s=0p7__cap=0p045 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270035 | 0.807841 | -0.001359 | -0.000289 | 0.991667 | 0.604167 | -0.002204 |
| ppopt131_segment_threshold__base=0p5__rslope=0p14__segpen=0p12__width=0p26__s=0p7__cap=0p03 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270013 | 0.808102 | -0.001382 | -0.000028 | 0.987500 | 0.604167 | -0.002200 |
| ppopt131_segment_threshold__base=0p5__rslope=0p14__segpen=0p12__width=0p26__s=0p7__cap=0p045 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270013 | 0.808102 | -0.001382 | -0.000028 | 0.987500 | 0.604167 | -0.002200 |
| ppopt131_segment_threshold__base=0p5__rslope=0p22__segpen=0p12__width=0p26__s=0p85__cap=0p018 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270029 | 0.807916 | -0.001365 | -0.000214 | 0.991667 | 0.604167 | -0.002199 |
| ppopt131_segment_threshold__base=0p5__rslope=0p22__segpen=0p12__width=0p18__s=0p55__cap=0p018 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270031 | 0.807889 | -0.001364 | -0.000241 | 0.991667 | 0.604167 | -0.002196 |
| ppopt131_segment_threshold__base=0p5__rslope=0p22__segpen=0p12__width=0p26__s=0p7__cap=0p018 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270035 | 0.807841 | -0.001359 | -0.000289 | 0.987500 | 0.604167 | -0.002184 |
| ppopt131_segment_threshold__base=0p5__rslope=0p22__segpen=0p08__width=0p26__s=0p55__cap=0p03 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270049 | 0.808200 | -0.001346 | 0.000070 | 0.995833 | 0.600000 | -0.002184 |
| ppopt131_segment_threshold__base=0p5__rslope=0p22__segpen=0p08__width=0p26__s=0p55__cap=0p045 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270049 | 0.808200 | -0.001346 | 0.000070 | 0.995833 | 0.600000 | -0.002184 |
| ppopt131_segment_threshold__base=0p5__rslope=0p14__segpen=0p12__width=0p26__s=0p7__cap=0p018 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270020 | 0.808102 | -0.001375 | -0.000028 | 0.987500 | 0.604167 | -0.002183 |
| ppopt131_segment_threshold__base=0p5__rslope=0p14__segpen=0p12__width=0p26__s=0p85__cap=0p03 | PP-OPT131 | segment_adaptive_learned_threshold | 0.269991 | 0.808233 | -0.001403 | 0.000103 | 0.995833 | 0.604167 | -0.002181 |
| ppopt131_segment_threshold__base=0p5__rslope=0p14__segpen=0p12__width=0p26__s=0p85__cap=0p045 | PP-OPT131 | segment_adaptive_learned_threshold | 0.269991 | 0.808233 | -0.001403 | 0.000103 | 0.995833 | 0.604167 | -0.002181 |
| ppopt131_segment_threshold__base=0p5__rslope=0p14__segpen=0p12__width=0p18__s=0p55__cap=0p03 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270001 | 0.808184 | -0.001394 | 0.000054 | 0.987500 | 0.604167 | -0.002174 |
| ppopt131_segment_threshold__base=0p5__rslope=0p14__segpen=0p12__width=0p18__s=0p55__cap=0p045 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270001 | 0.808184 | -0.001394 | 0.000054 | 0.987500 | 0.604167 | -0.002174 |
| ppopt131_segment_threshold__base=0p5__rslope=0p14__segpen=0p12__width=0p26__s=0p55__cap=0p03 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270035 | 0.807971 | -0.001360 | -0.000159 | 0.987500 | 0.604167 | -0.002173 |
| ppopt131_segment_threshold__base=0p5__rslope=0p14__segpen=0p12__width=0p26__s=0p55__cap=0p045 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270035 | 0.807971 | -0.001360 | -0.000159 | 0.987500 | 0.604167 | -0.002173 |
| ppopt131_segment_threshold__base=0p5__rslope=0p08__segpen=0p12__width=0p26__s=0p55__cap=0p03 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270020 | 0.808125 | -0.001375 | -0.000005 | 0.987500 | 0.604167 | -0.002173 |
| ppopt131_segment_threshold__base=0p5__rslope=0p08__segpen=0p12__width=0p26__s=0p55__cap=0p045 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270020 | 0.808125 | -0.001375 | -0.000005 | 0.987500 | 0.604167 | -0.002173 |
| ppopt131_segment_threshold__base=0p5__rslope=0p14__segpen=0p12__width=0p26__s=0p55__cap=0p018 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270035 | 0.807971 | -0.001360 | -0.000159 | 0.987500 | 0.604167 | -0.002173 |
| ppopt131_segment_threshold__base=0p5__rslope=0p08__segpen=0p12__width=0p26__s=0p55__cap=0p018 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270020 | 0.808125 | -0.001375 | -0.000005 | 0.987500 | 0.604167 | -0.002171 |
| ppopt131_segment_threshold__base=0p5__rslope=0p22__segpen=0p12__width=0p26__s=0p55__cap=0p018 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270052 | 0.807766 | -0.001343 | -0.000364 | 0.987500 | 0.604167 | -0.002170 |
| ppopt131_segment_threshold__base=0p5__rslope=0p22__segpen=0p12__width=0p26__s=0p55__cap=0p03 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270052 | 0.807766 | -0.001343 | -0.000364 | 0.987500 | 0.604167 | -0.002170 |
| ppopt131_segment_threshold__base=0p5__rslope=0p22__segpen=0p12__width=0p26__s=0p55__cap=0p045 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270052 | 0.807766 | -0.001343 | -0.000364 | 0.987500 | 0.604167 | -0.002170 |
| ppopt127_learned_gain_gate__safe=pp126_op__target=stack_huber_weighted__hpen=0p65__rpen=0p45__thr=0p56__width=0p26__cap=0p022__s=0p45 | PP-OPT127 | learned_stack_gain_gate | 0.270099 | 0.808150 | -0.001296 | 0.000020 | 0.987500 | 0.600000 | -0.002169 |
| ppopt127_learned_gain_gate__safe=pp126_op__target=stack_huber_weighted__hpen=0p65__rpen=0p45__thr=0p56__width=0p26__cap=0p034__s=0p45 | PP-OPT127 | learned_stack_gain_gate | 0.270099 | 0.808150 | -0.001296 | 0.000020 | 0.987500 | 0.600000 | -0.002169 |
| ppopt127_learned_gain_gate__safe=pp126_op__target=stack_huber_weighted__hpen=0p65__rpen=0p45__thr=0p56__width=0p26__cap=0p05__s=0p45 | PP-OPT127 | learned_stack_gain_gate | 0.270099 | 0.808150 | -0.001296 | 0.000020 | 0.987500 | 0.600000 | -0.002169 |
| ppopt131_segment_threshold__base=0p5__rslope=0p22__segpen=0p08__width=0p26__s=0p55__cap=0p018 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270049 | 0.808200 | -0.001346 | 0.000070 | 0.991667 | 0.600000 | -0.002167 |
| ppopt127_learned_gain_gate__safe=pp126_op__target=stack_huber_weighted__hpen=0p65__rpen=0p45__thr=0p56__width=0p26__cap=0p014__s=0p45 | PP-OPT127 | learned_stack_gain_gate | 0.270099 | 0.808150 | -0.001296 | 0.000020 | 0.987500 | 0.600000 | -0.002165 |
| ppopt131_segment_threshold__base=0p5__rslope=0p14__segpen=0p12__width=0p18__s=0p55__cap=0p018 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270020 | 0.808184 | -0.001375 | 0.000054 | 0.987500 | 0.604167 | -0.002156 |
| ppopt131_segment_threshold__base=0p5__rslope=0p14__segpen=0p12__width=0p26__s=0p85__cap=0p018 | PP-OPT131 | segment_adaptive_learned_threshold | 0.270020 | 0.808233 | -0.001375 | 0.000103 | 0.987500 | 0.604167 | -0.002131 |
| ppopt131_segment_threshold__base=0p5__rslope=0p14__segpen=0p12__width=0p18__s=0p7__cap=0p045 | PP-OPT131 | segment_adaptive_learned_threshold | 0.269970 | 0.808373 | -0.001425 | 0.000243 | 1.000000 | 0.600000 | -0.002100 |
| ppopt128_harm_rollback__thr=0p1__pre=0p85__guard=0p35__floor=0p0__cap=0p018 | PP-OPT128 | learned_harm_rollback | 0.269992 | 0.807490 | -0.001403 | -0.000640 | 0.966667 | 0.625000 | -0.002097 |
| ppopt128_harm_rollback__thr=0p1__pre=0p85__guard=0p35__floor=0p12__cap=0p018 | PP-OPT128 | learned_harm_rollback | 0.269992 | 0.807490 | -0.001403 | -0.000640 | 0.966667 | 0.625000 | -0.002097 |
| ppopt128_harm_rollback__thr=0p1__pre=0p85__guard=0p35__floor=0p25__cap=0p018 | PP-OPT128 | learned_harm_rollback | 0.269992 | 0.807490 | -0.001403 | -0.000640 | 0.966667 | 0.625000 | -0.002097 |
| ppopt131_segment_threshold__base=0p5__rslope=0p14__segpen=0p12__width=0p18__s=0p7__cap=0p03 | PP-OPT131 | segment_adaptive_learned_threshold | 0.269970 | 0.808373 | -0.001425 | 0.000243 | 0.995833 | 0.600000 | -0.002094 |
| ppopt127_learned_gain_gate__safe=pp126_op__target=stack_huber_weighted__hpen=0p65__rpen=0p45__thr=0p56__width=0p26__cap=0p022__s=0p6 | PP-OPT127 | learned_stack_gain_gate | 0.270094 | 0.808369 | -0.001301 | 0.000239 | 0.995833 | 0.600000 | -0.002092 |
| ppopt127_learned_gain_gate__safe=pp126_op__target=stack_huber_weighted__hpen=0p65__rpen=0p45__thr=0p56__width=0p26__cap=0p034__s=0p6 | PP-OPT127 | learned_stack_gain_gate | 0.270094 | 0.808369 | -0.001301 | 0.000239 | 0.995833 | 0.600000 | -0.002092 |
| ppopt127_learned_gain_gate__safe=pp126_op__target=stack_huber_weighted__hpen=0p65__rpen=0p45__thr=0p56__width=0p26__cap=0p05__s=0p6 | PP-OPT127 | learned_stack_gain_gate | 0.270094 | 0.808369 | -0.001301 | 0.000239 | 0.995833 | 0.600000 | -0.002092 |
| ppopt131_segment_threshold__base=0p5__rslope=0p08__segpen=0p12__width=0p26__s=0p7__cap=0p03 | PP-OPT131 | segment_adaptive_learned_threshold | 0.269995 | 0.808297 | -0.001400 | 0.000167 | 0.987500 | 0.600000 | -0.002091 |
| ppopt131_segment_threshold__base=0p5__rslope=0p08__segpen=0p12__width=0p26__s=0p7__cap=0p045 | PP-OPT131 | segment_adaptive_learned_threshold | 0.269995 | 0.808297 | -0.001400 | 0.000167 | 0.987500 | 0.600000 | -0.002091 |
| ppopt128_harm_rollback__thr=0p12__pre=0p55__guard=0p5__floor=0p0__cap=0p03 | PP-OPT128 | learned_harm_rollback | 0.270037 | 0.807490 | -0.001357 | -0.000640 | 0.966667 | 0.604167 | -0.002089 |
| ppopt128_harm_rollback__thr=0p12__pre=0p55__guard=0p5__floor=0p0__cap=0p045 | PP-OPT128 | learned_harm_rollback | 0.270037 | 0.807490 | -0.001357 | -0.000640 | 0.966667 | 0.604167 | -0.002089 |
| ppopt128_harm_rollback__thr=0p12__pre=0p55__guard=0p5__floor=0p12__cap=0p03 | PP-OPT128 | learned_harm_rollback | 0.270037 | 0.807490 | -0.001357 | -0.000640 | 0.966667 | 0.604167 | -0.002089 |
| ppopt128_harm_rollback__thr=0p12__pre=0p55__guard=0p5__floor=0p12__cap=0p045 | PP-OPT128 | learned_harm_rollback | 0.270037 | 0.807490 | -0.001357 | -0.000640 | 0.966667 | 0.604167 | -0.002089 |
| ppopt128_harm_rollback__thr=0p12__pre=0p55__guard=0p5__floor=0p25__cap=0p03 | PP-OPT128 | learned_harm_rollback | 0.270037 | 0.807490 | -0.001357 | -0.000640 | 0.966667 | 0.604167 | -0.002089 |
| ppopt128_harm_rollback__thr=0p12__pre=0p55__guard=0p5__floor=0p25__cap=0p045 | PP-OPT128 | learned_harm_rollback | 0.270037 | 0.807490 | -0.001357 | -0.000640 | 0.966667 | 0.604167 | -0.002089 |
| ppopt128_harm_rollback__thr=0p1__pre=0p85__guard=0p35__floor=0p0__cap=0p03 | PP-OPT128 | learned_harm_rollback | 0.269978 | 0.807490 | -0.001417 | -0.000640 | 0.966667 | 0.625000 | -0.002089 |
| ppopt128_harm_rollback__thr=0p1__pre=0p85__guard=0p35__floor=0p12__cap=0p03 | PP-OPT128 | learned_harm_rollback | 0.269978 | 0.807490 | -0.001417 | -0.000640 | 0.966667 | 0.625000 | -0.002089 |
| ppopt128_harm_rollback__thr=0p1__pre=0p85__guard=0p35__floor=0p25__cap=0p03 | PP-OPT128 | learned_harm_rollback | 0.269978 | 0.807490 | -0.001417 | -0.000640 | 0.966667 | 0.625000 | -0.002089 |
| ppopt128_harm_rollback__thr=0p12__pre=0p55__guard=0p35__floor=0p0__cap=0p018 | PP-OPT128 | learned_harm_rollback | 0.270033 | 0.807490 | -0.001362 | -0.000640 | 0.966667 | 0.604167 | -0.002087 |

## p95 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt130_p95_tail_router__target=pp82_p95__thr=0p3__width=0p18__s=0p55__cap=0p008 | PP-OPT130 | learned_p95_tail_router | 0.270242 | 0.807488 | -0.001153 | -0.000641 | 0.983333 | 0.600000 | -0.001970 |
| ppopt134_p95_learned_stack_correction_challenger__source=ppopt130_p95_tail_router__target_pp82_p95__thr_0p3__width_0p18__s_0p55__cap_0p008 | PP-OPT134 | learned_stack_correction_p95_selection | 0.270242 | 0.807488 | -0.001153 | -0.000641 | 0.983333 | 0.600000 | -0.001970 |
| ppopt130_p95_tail_router__target=pp82_p95__thr=0p3__width=0p18__s=0p55__cap=0p014 | PP-OPT130 | learned_p95_tail_router | 0.270272 | 0.807488 | -0.001123 | -0.000641 | 0.979167 | 0.595833 | -0.001883 |
| ppopt130_p95_tail_router__target=pp82_p95__thr=0p3__width=0p18__s=0p55__cap=0p022 | PP-OPT130 | learned_p95_tail_router | 0.270311 | 0.807488 | -0.001084 | -0.000641 | 0.979167 | 0.575000 | -0.001787 |
| ppopt130_p95_tail_router__target=pp82_p95__thr=0p3__width=0p18__s=0p4__cap=0p008 | PP-OPT130 | learned_p95_tail_router | 0.270228 | 0.807489 | -0.001167 | -0.000641 | 0.983333 | 0.595833 | -0.001944 |
| ppopt130_p95_tail_router__target=pp82_p95__thr=0p3__width=0p18__s=0p4__cap=0p014 | PP-OPT130 | learned_p95_tail_router | 0.270250 | 0.807489 | -0.001145 | -0.000641 | 0.979167 | 0.595833 | -0.001893 |
| ppopt130_p95_tail_router__target=pp82_p95__thr=0p3__width=0p18__s=0p4__cap=0p022 | PP-OPT130 | learned_p95_tail_router | 0.270272 | 0.807489 | -0.001123 | -0.000641 | 0.979167 | 0.595833 | -0.001839 |
| ppopt130_p95_tail_router__target=pp82_p95__thr=0p3__width=0p26__s=0p55__cap=0p008 | PP-OPT130 | learned_p95_tail_router | 0.270234 | 0.807489 | -0.001161 | -0.000641 | 0.983333 | 0.600000 | -0.001958 |
| ppopt130_p95_tail_router__target=pp82_p95__thr=0p3__width=0p26__s=0p55__cap=0p014 | PP-OPT130 | learned_p95_tail_router | 0.270260 | 0.807489 | -0.001135 | -0.000641 | 0.979167 | 0.595833 | -0.001881 |
| ppopt130_p95_tail_router__target=pp82_p95__thr=0p3__width=0p26__s=0p55__cap=0p022 | PP-OPT130 | learned_p95_tail_router | 0.270281 | 0.807489 | -0.001114 | -0.000641 | 0.975000 | 0.575000 | -0.001779 |
| ppopt130_p95_tail_router__target=pp82_p95__thr=0p3__width=0p18__s=0p28__cap=0p008 | PP-OPT130 | learned_p95_tail_router | 0.270211 | 0.807489 | -0.001184 | -0.000641 | 0.983333 | 0.591667 | -0.001934 |
| ppopt130_p95_tail_router__target=pp82_p95__thr=0p3__width=0p18__s=0p28__cap=0p014 | PP-OPT130 | learned_p95_tail_router | 0.270221 | 0.807489 | -0.001174 | -0.000641 | 0.983333 | 0.591667 | -0.001895 |
| ppopt130_p95_tail_router__target=pp82_p95__thr=0p3__width=0p18__s=0p28__cap=0p022 | PP-OPT130 | learned_p95_tail_router | 0.270228 | 0.807489 | -0.001167 | -0.000641 | 0.979167 | 0.591667 | -0.001854 |
| ppopt130_p95_tail_router__target=pp82_p95__thr=0p3__width=0p26__s=0p4__cap=0p008 | PP-OPT130 | learned_p95_tail_router | 0.270221 | 0.807489 | -0.001174 | -0.000641 | 0.983333 | 0.595833 | -0.001944 |
| ppopt130_p95_tail_router__target=pp82_p95__thr=0p3__width=0p26__s=0p4__cap=0p014 | PP-OPT130 | learned_p95_tail_router | 0.270231 | 0.807489 | -0.001164 | -0.000641 | 0.979167 | 0.595833 | -0.001891 |
| ppopt130_p95_tail_router__target=pp82_p95__thr=0p3__width=0p26__s=0p4__cap=0p022 | PP-OPT130 | learned_p95_tail_router | 0.270244 | 0.807489 | -0.001151 | -0.000641 | 0.975000 | 0.595833 | -0.001838 |
| ppopt130_p95_tail_router__target=pp82_p95__thr=0p3__width=0p26__s=0p28__cap=0p008 | PP-OPT130 | learned_p95_tail_router | 0.270199 | 0.807490 | -0.001196 | -0.000640 | 0.983333 | 0.591667 | -0.001948 |
| ppopt130_p95_tail_router__target=pp82_p95__thr=0p3__width=0p26__s=0p28__cap=0p014 | PP-OPT130 | learned_p95_tail_router | 0.270204 | 0.807490 | -0.001191 | -0.000640 | 0.983333 | 0.591667 | -0.001906 |
| ppopt130_p95_tail_router__target=pp82_p95__thr=0p3__width=0p26__s=0p28__cap=0p022 | PP-OPT130 | learned_p95_tail_router | 0.270209 | 0.807490 | -0.001186 | -0.000640 | 0.979167 | 0.591667 | -0.001873 |
| ppopt130_p95_tail_router__target=pp126_p95__thr=0p3__width=0p18__s=0p55__cap=0p008 | PP-OPT130 | learned_p95_tail_router | 0.270199 | 0.807490 | -0.001196 | -0.000640 | 0.983333 | 0.591667 | -0.001940 |
| ppopt130_p95_tail_router__target=pp126_p95__thr=0p3__width=0p18__s=0p55__cap=0p014 | PP-OPT130 | learned_p95_tail_router | 0.270209 | 0.807490 | -0.001186 | -0.000640 | 0.983333 | 0.591667 | -0.001904 |
| ppopt130_p95_tail_router__target=pp126_p95__thr=0p3__width=0p18__s=0p55__cap=0p022 | PP-OPT130 | learned_p95_tail_router | 0.270220 | 0.807490 | -0.001174 | -0.000640 | 0.975000 | 0.591667 | -0.001855 |
| ppopt130_p95_tail_router__target=pp82_p95__thr=0p3__width=0p18__s=0p18__cap=0p008 | PP-OPT130 | learned_p95_tail_router | 0.270186 | 0.807490 | -0.001209 | -0.000640 | 0.983333 | 0.591667 | -0.001956 |
| ppopt130_p95_tail_router__target=pp82_p95__thr=0p3__width=0p18__s=0p18__cap=0p014 | PP-OPT130 | learned_p95_tail_router | 0.270188 | 0.807490 | -0.001207 | -0.000640 | 0.983333 | 0.591667 | -0.001920 |
| ppopt130_p95_tail_router__target=pp82_p95__thr=0p3__width=0p18__s=0p18__cap=0p022 | PP-OPT130 | learned_p95_tail_router | 0.270191 | 0.807490 | -0.001204 | -0.000640 | 0.983333 | 0.591667 | -0.001896 |
| ppopt130_p95_tail_router__target=pp126_p95__thr=0p3__width=0p18__s=0p4__cap=0p008 | PP-OPT130 | learned_p95_tail_router | 0.270185 | 0.807490 | -0.001210 | -0.000640 | 0.983333 | 0.591667 | -0.001971 |
| ppopt130_p95_tail_router__target=pp126_p95__thr=0p3__width=0p18__s=0p4__cap=0p022 | PP-OPT130 | learned_p95_tail_router | 0.270190 | 0.807490 | -0.001205 | -0.000640 | 0.979167 | 0.591667 | -0.001901 |
| ppopt130_p95_tail_router__target=pp126_p95__thr=0p3__width=0p18__s=0p4__cap=0p014 | PP-OPT130 | learned_p95_tail_router | 0.270191 | 0.807490 | -0.001204 | -0.000640 | 0.983333 | 0.591667 | -0.001933 |
| ppopt130_p95_tail_router__target=pp126_p95__thr=0p3__width=0p26__s=0p55__cap=0p008 | PP-OPT130 | learned_p95_tail_router | 0.270188 | 0.807490 | -0.001207 | -0.000640 | 0.983333 | 0.591667 | -0.001961 |
| ppopt130_p95_tail_router__target=pp126_p95__thr=0p3__width=0p26__s=0p55__cap=0p014 | PP-OPT130 | learned_p95_tail_router | 0.270195 | 0.807490 | -0.001200 | -0.000640 | 0.983333 | 0.591667 | -0.001926 |
| ppopt130_p95_tail_router__target=pp126_p95__thr=0p3__width=0p26__s=0p55__cap=0p022 | PP-OPT130 | learned_p95_tail_router | 0.270197 | 0.807490 | -0.001198 | -0.000640 | 0.975000 | 0.591667 | -0.001884 |
| ppopt130_p95_tail_router__target=pp118_p95__thr=0p3__width=0p18__s=0p55__cap=0p008 | PP-OPT130 | learned_p95_tail_router | 0.270237 | 0.807490 | -0.001157 | -0.000640 | 0.983333 | 0.600000 | -0.001971 |
| ppopt130_p95_tail_router__target=pp118_p95__thr=0p3__width=0p18__s=0p55__cap=0p014 | PP-OPT130 | learned_p95_tail_router | 0.270267 | 0.807490 | -0.001128 | -0.000640 | 0.979167 | 0.595833 | -0.001884 |
| ppopt130_p95_tail_router__target=pp118_p95__thr=0p3__width=0p18__s=0p55__cap=0p022 | PP-OPT130 | learned_p95_tail_router | 0.270299 | 0.807490 | -0.001096 | -0.000640 | 0.975000 | 0.575000 | -0.001782 |
| ppopt130_p95_tail_router__target=pp82_p95__thr=0p3__width=0p26__s=0p18__cap=0p008 | PP-OPT130 | learned_p95_tail_router | 0.270174 | 0.807490 | -0.001221 | -0.000640 | 0.983333 | 0.591667 | -0.001976 |
| ppopt130_p95_tail_router__target=pp82_p95__thr=0p3__width=0p26__s=0p18__cap=0p014 | PP-OPT130 | learned_p95_tail_router | 0.270175 | 0.807490 | -0.001220 | -0.000640 | 0.983333 | 0.591667 | -0.001944 |
| ppopt130_p95_tail_router__target=pp82_p95__thr=0p3__width=0p26__s=0p18__cap=0p022 | PP-OPT130 | learned_p95_tail_router | 0.270175 | 0.807490 | -0.001220 | -0.000640 | 0.979167 | 0.591667 | -0.001925 |
| ppopt130_p95_tail_router__target=pp82_p95__thr=0p3__width=0p18__s=0p1__cap=0p008 | PP-OPT130 | learned_p95_tail_router | 0.270157 | 0.807490 | -0.001238 | -0.000640 | 0.987500 | 0.591667 | -0.001990 |
| ppopt130_p95_tail_router__target=pp82_p95__thr=0p3__width=0p18__s=0p1__cap=0p014 | PP-OPT130 | learned_p95_tail_router | 0.270157 | 0.807490 | -0.001238 | -0.000640 | 0.987500 | 0.591667 | -0.001966 |
| ppopt130_p95_tail_router__target=pp82_p95__thr=0p3__width=0p18__s=0p1__cap=0p022 | PP-OPT130 | learned_p95_tail_router | 0.270157 | 0.807490 | -0.001238 | -0.000640 | 0.987500 | 0.591667 | -0.001956 |

## 선택 후보 반복 안정성
| candidate_label | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_vs_pp64_MAPE | fixed_test_delta_vs_pp64_p95_APE | avg_delta_vs_pp64_MAPE | avg_delta_vs_pp64_p95_APE | avg_pp64_MAPE_win_rate | avg_pp64_p95_win_rate | replacement_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p5__rpen_0p35__th__265c153f6b | 0.269650 | 0.809142 | -0.000914 | 0.001643 | -0.000958 | -0.002538 | 0.967308 | 0.466346 | -0.018456 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p65__rpen_0p45__t__9a35bedbf2 | 0.269497 | 0.809142 | -0.001067 | 0.001643 | -0.001016 | -0.003001 | 0.961859 | 0.496795 | -0.018392 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p5__rpen_0p35__th__d3b67a0f7a | 0.269653 | 0.809142 | -0.000911 | 0.001643 | -0.000938 | -0.002546 | 0.965385 | 0.467949 | -0.018376 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p65__rpen_0p45__t__33b0626253 | 0.269507 | 0.809142 | -0.001057 | 0.001643 | -0.000999 | -0.002896 | 0.960897 | 0.495192 | -0.018343 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p65__rpen_0p45__t__ccb9255a27 | 0.269519 | 0.809142 | -0.001045 | 0.001643 | -0.000988 | -0.002799 | 0.960577 | 0.494551 | -0.018318 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p65__rpen_0p45__t__aec4758b10 | 0.269519 | 0.809142 | -0.001045 | 0.001643 | -0.000981 | -0.002771 | 0.959936 | 0.494231 | -0.018292 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p65__rpen_0p45__t__a6279f3d7f | 0.269533 | 0.809142 | -0.001031 | 0.001643 | -0.000974 | -0.002733 | 0.959295 | 0.494551 | -0.018253 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p5__rpen_0p35__th__154d4386e7 | 0.269659 | 0.809142 | -0.000905 | 0.001643 | -0.000917 | -0.002548 | 0.962179 | 0.471154 | -0.018242 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p5__rpen_0p35__th__df2a41c1d5 | 0.269660 | 0.809142 | -0.000904 | 0.001643 | -0.000911 | -0.002541 | 0.960897 | 0.472115 | -0.018190 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p65__rpen_0p45__t__a17f7b1de0 | 0.269554 | 0.809142 | -0.001010 | 0.001643 | -0.000937 | -0.002688 | 0.955769 | 0.495833 | -0.018090 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p5__rpen_0p35__th__778e245639 | 0.269680 | 0.809142 | -0.000884 | 0.001643 | -0.000882 | -0.002477 | 0.958013 | 0.472115 | -0.018054 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p5__rpen_0p35__th__49b0e31314 | 0.269690 | 0.809142 | -0.000874 | 0.001643 | -0.000851 | -0.002404 | 0.955128 | 0.472436 | -0.017929 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p35__rpen_0p25__t__0325b3a26f | 0.269301 | 0.810077 | -0.001263 | 0.002578 | -0.001189 | -0.002704 | 0.958974 | 0.433654 | -0.017818 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p65__rpen_0p45__t__ff648d30cf | 0.269303 | 0.810077 | -0.001261 | 0.002578 | -0.001169 | -0.003065 | 0.958013 | 0.494872 | -0.017777 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p5__rpen_0p35__th__74fb85be4a | 0.269482 | 0.810077 | -0.001082 | 0.002578 | -0.001086 | -0.002858 | 0.961218 | 0.466026 | -0.017726 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p65__rpen_0p45__t__fd3e17460d | 0.269319 | 0.810077 | -0.001246 | 0.002578 | -0.001133 | -0.003053 | 0.956731 | 0.497756 | -0.017710 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p65__rpen_0p45__t__0f64f2dda9 | 0.269336 | 0.810077 | -0.001228 | 0.002578 | -0.001117 | -0.003060 | 0.956410 | 0.498397 | -0.017680 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p35__rpen_0p25__t__de1ffba6bb | 0.268735 | 0.810180 | -0.001829 | 0.002682 | -0.001417 | -0.003110 | 0.942308 | 0.447115 | -0.017644 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p5__rpen_0p35__th__d31d705d08 | 0.269500 | 0.810077 | -0.001064 | 0.002578 | -0.001040 | -0.002742 | 0.959295 | 0.467308 | -0.017631 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p65__rpen_0p45__t__50b29fb827 | 0.269315 | 0.810077 | -0.001249 | 0.002578 | -0.001094 | -0.003031 | 0.953846 | 0.499038 | -0.017598 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p5__rpen_0p35__th__1cb865f21e | 0.268797 | 0.810301 | -0.001767 | 0.002802 | -0.001419 | -0.003391 | 0.944231 | 0.454808 | -0.017575 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p65__rpen_0p45__t__aacc6afbf0 | 0.269357 | 0.810077 | -0.001207 | 0.002578 | -0.001070 | -0.002922 | 0.952244 | 0.498077 | -0.017492 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p5__rpen_0p35__th__27d2b9ab7d | 0.269559 | 0.810077 | -0.001005 | 0.002578 | -0.000977 | -0.002560 | 0.955769 | 0.470192 | -0.017431 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p5__rpen_0p35__th__f934696405 | 0.269556 | 0.810077 | -0.001008 | 0.002578 | -0.000960 | -0.002514 | 0.955449 | 0.471154 | -0.017422 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p5__rpen_0p35__th__c863029a6c | 0.269596 | 0.809604 | -0.000968 | 0.002105 | -0.000906 | -0.002342 | 0.948077 | 0.470513 | -0.017418 |
| pp126_operational_reference | 0.270114 | 0.807490 | -0.000450 | -0.000009 | -0.000455 | -0.001725 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p5__rpen_0p35__th__9b178385a1 | 0.269619 | 0.810077 | -0.000945 | 0.002578 | -0.000909 | -0.002371 | 0.950962 | 0.470833 | -0.017179 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p35__rpen_0p25__t__e960a5491d | 0.268744 | 0.810669 | -0.001820 | 0.003171 | -0.001430 | -0.003126 | 0.936218 | 0.450321 | -0.017050 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p35__rpen_0p25__t__6fe1e22cff | 0.269727 | 0.810077 | -0.000837 | 0.002578 | -0.000865 | -0.002268 | 0.948077 | 0.450000 | -0.016956 |
| candidate_ppopt128_harm_rollback__thr_0p12__pre_0p55__guard_0p35__floor_0p0__cap_0p018__dab6f04fcb | 0.270033 | 0.807490 | -0.000531 | -0.000009 | -0.000509 | -0.001995 | 0.909936 | 0.496474 | -0.016928 |
| candidate_ppopt128_harm_rollback__thr_0p12__pre_0p55__guard_0p35__floor_0p12__cap_0p018__d23d047a6b | 0.270033 | 0.807490 | -0.000531 | -0.000009 | -0.000509 | -0.001995 | 0.909936 | 0.496474 | -0.016928 |
| candidate_ppopt128_harm_rollback__thr_0p12__pre_0p55__guard_0p35__floor_0p25__cap_0p018__fa78a0a316 | 0.270033 | 0.807490 | -0.000531 | -0.000009 | -0.000509 | -0.001995 | 0.909936 | 0.496474 | -0.016928 |
| pp134_operational_learned_stack_correction_challenger | 0.270033 | 0.807490 | -0.000531 | -0.000009 | -0.000509 | -0.001995 | 0.909936 | 0.496474 | -0.016928 |
| candidate_ppopt128_harm_rollback__thr_0p12__pre_0p55__guard_0p5__floor_0p0__cap_0p03__cae9ed0d3c | 0.270037 | 0.807490 | -0.000527 | -0.000009 | -0.000508 | -0.001978 | 0.909936 | 0.496474 | -0.016924 |
| candidate_ppopt128_harm_rollback__thr_0p12__pre_0p55__guard_0p5__floor_0p0__cap_0p045__ac1958a54c | 0.270037 | 0.807490 | -0.000527 | -0.000009 | -0.000508 | -0.001978 | 0.909936 | 0.496474 | -0.016924 |
| candidate_ppopt128_harm_rollback__thr_0p12__pre_0p55__guard_0p5__floor_0p12__cap_0p03__2d85c87bca | 0.270037 | 0.807490 | -0.000527 | -0.000009 | -0.000508 | -0.001978 | 0.909936 | 0.496474 | -0.016924 |
| candidate_ppopt128_harm_rollback__thr_0p12__pre_0p55__guard_0p5__floor_0p12__cap_0p045__032d7a127a | 0.270037 | 0.807490 | -0.000527 | -0.000009 | -0.000508 | -0.001978 | 0.909936 | 0.496474 | -0.016924 |
| candidate_ppopt128_harm_rollback__thr_0p12__pre_0p55__guard_0p5__floor_0p25__cap_0p03__f0dcab16f0 | 0.270037 | 0.807490 | -0.000527 | -0.000009 | -0.000508 | -0.001978 | 0.909936 | 0.496474 | -0.016924 |
| candidate_ppopt128_harm_rollback__thr_0p12__pre_0p55__guard_0p5__floor_0p25__cap_0p045__039de181da | 0.270037 | 0.807490 | -0.000527 | -0.000009 | -0.000508 | -0.001978 | 0.909936 | 0.496474 | -0.016924 |
| candidate_ppopt128_harm_rollback__thr_0p12__pre_0p7__guard_0p35__floor_0p0__cap_0p018__9fa88d60be | 0.270016 | 0.807490 | -0.000548 | -0.000009 | -0.000521 | -0.002070 | 0.908333 | 0.496474 | -0.016882 |
| candidate_ppopt128_harm_rollback__thr_0p12__pre_0p7__guard_0p35__floor_0p12__cap_0p018__35796ca1bb | 0.270016 | 0.807490 | -0.000548 | -0.000009 | -0.000521 | -0.002070 | 0.908333 | 0.496474 | -0.016882 |
| candidate_ppopt128_harm_rollback__thr_0p12__pre_0p7__guard_0p35__floor_0p25__cap_0p018__d841a0a66a | 0.270016 | 0.807490 | -0.000548 | -0.000009 | -0.000521 | -0.002070 | 0.908333 | 0.496474 | -0.016882 |
| candidate_ppopt128_harm_rollback__thr_0p1__pre_0p55__guard_0p5__floor_0p0__cap_0p03__97bcd80763 | 0.270031 | 0.807490 | -0.000533 | -0.000009 | -0.000510 | -0.002010 | 0.908654 | 0.496474 | -0.016880 |
| candidate_ppopt128_harm_rollback__thr_0p1__pre_0p55__guard_0p5__floor_0p0__cap_0p045__5f4c2cec8f | 0.270031 | 0.807490 | -0.000533 | -0.000009 | -0.000510 | -0.002010 | 0.908654 | 0.496474 | -0.016880 |
| candidate_ppopt128_harm_rollback__thr_0p1__pre_0p55__guard_0p5__floor_0p12__cap_0p03__33f74633f2 | 0.270031 | 0.807490 | -0.000533 | -0.000009 | -0.000510 | -0.002010 | 0.908654 | 0.496474 | -0.016880 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p35__rpen_0p25__t__7f80624d3e | 0.268800 | 0.810994 | -0.001764 | 0.003495 | -0.001433 | -0.003147 | 0.938782 | 0.431090 | -0.016869 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p5__rpen_0p35__th__05f7554354 | 0.268620 | 0.810994 | -0.001944 | 0.003495 | -0.001517 | -0.003494 | 0.933654 | 0.453846 | -0.016844 |
| pp118_operational_reference | 0.270139 | 0.807490 | -0.000425 | -0.000009 | -0.000389 | -0.001654 | 0.909295 | 0.494551 | -0.016797 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p35__rpen_0p25__t__826d05b9d9 | 0.269753 | 0.810077 | -0.000811 | 0.002578 | -0.000820 | -0.002166 | 0.944231 | 0.450321 | -0.016776 |
| candidate_ppopt130_p95_tail_router__target_pp126_p95__thr_0p3__width_0p18__s_0p4__cap_0p008__b28526365e | 0.270185 | 0.807490 | -0.000379 | -0.000009 | -0.000373 | -0.001512 | 0.908974 | 0.492308 | -0.016738 |
| candidate_ppopt130_p95_tail_router__target_pp82_p95__thr_0p3__width_0p18__s_0p18__cap_0p008__a16f279423 | 0.270186 | 0.807490 | -0.000379 | -0.000009 | -0.000373 | -0.001499 | 0.908013 | 0.491987 | -0.016699 |
| candidate_ppopt130_p95_tail_router__target_pp82_p95__thr_0p3__width_0p26__s_0p55__cap_0p008__8844678333 | 0.270234 | 0.807489 | -0.000330 | -0.000010 | -0.000342 | -0.001432 | 0.908974 | 0.492308 | -0.016689 |
| candidate_ppopt130_p95_tail_router__target_pp82_p95__thr_0p3__width_0p18__s_0p18__cap_0p014__2a49bc1196 | 0.270188 | 0.807490 | -0.000377 | -0.000009 | -0.000364 | -0.001499 | 0.907692 | 0.491987 | -0.016684 |
| candidate_ppopt128_harm_rollback__thr_0p1__pre_0p85__guard_0p35__floor_0p0__cap_0p018__aa76ac677f | 0.269992 | 0.807490 | -0.000572 | -0.000009 | -0.000526 | -0.002194 | 0.902564 | 0.496474 | -0.016675 |
| candidate_ppopt128_harm_rollback__thr_0p1__pre_0p85__guard_0p35__floor_0p12__cap_0p018__d09a0a59f0 | 0.269992 | 0.807490 | -0.000572 | -0.000009 | -0.000526 | -0.002194 | 0.902564 | 0.496474 | -0.016675 |
| candidate_ppopt128_harm_rollback__thr_0p1__pre_0p85__guard_0p35__floor_0p25__cap_0p018__29ec4128ce | 0.269992 | 0.807490 | -0.000572 | -0.000009 | -0.000526 | -0.002194 | 0.902564 | 0.496474 | -0.016675 |
| candidate_ppopt128_harm_rollback__thr_0p1__pre_0p85__guard_0p35__floor_0p0__cap_0p03__cf458fa79f | 0.269978 | 0.807490 | -0.000586 | -0.000009 | -0.000540 | -0.002193 | 0.901603 | 0.496474 | -0.016650 |
| candidate_ppopt128_harm_rollback__thr_0p1__pre_0p85__guard_0p35__floor_0p12__cap_0p03__b088705dde | 0.269978 | 0.807490 | -0.000586 | -0.000009 | -0.000540 | -0.002193 | 0.901603 | 0.496474 | -0.016650 |
| candidate_ppopt128_harm_rollback__thr_0p1__pre_0p85__guard_0p35__floor_0p25__cap_0p03__b6291f5585 | 0.269978 | 0.807490 | -0.000586 | -0.000009 | -0.000540 | -0.002193 | 0.901603 | 0.496474 | -0.016650 |
| candidate_ppopt130_p95_tail_router__target_pp82_p95__thr_0p3__width_0p26__s_0p28__cap_0p008__e8b95012bb | 0.270199 | 0.807490 | -0.000365 | -0.000009 | -0.000361 | -0.001470 | 0.907051 | 0.491987 | -0.016647 |
| candidate_ppopt128_harm_rollback__thr_0p1__pre_1p0__guard_0p65__floor_0p0__cap_0p045__32b02010b8 | 0.269970 | 0.807490 | -0.000594 | -0.000009 | -0.000546 | -0.002204 | 0.901282 | 0.496474 | -0.016645 |
| candidate_ppopt128_harm_rollback__thr_0p1__pre_1p0__guard_0p65__floor_0p12__cap_0p045__ed8889d42b | 0.269970 | 0.807490 | -0.000594 | -0.000009 | -0.000546 | -0.002204 | 0.901282 | 0.496474 | -0.016645 |
| candidate_ppopt128_harm_rollback__thr_0p1__pre_1p0__guard_0p65__floor_0p25__cap_0p045__145528825a | 0.269970 | 0.807490 | -0.000594 | -0.000009 | -0.000546 | -0.002204 | 0.901282 | 0.496474 | -0.016645 |
| pp126_p95_reference | 0.270317 | 0.807465 | -0.000247 | -0.000034 | -0.000239 | -0.000998 | 0.909936 | 0.665705 | -0.016645 |
| candidate_ppopt130_p95_tail_router__target_pp126_p95__thr_0p3__width_0p18__s_0p4__cap_0p014__a46bce97de | 0.270191 | 0.807490 | -0.000373 | -0.000009 | -0.000361 | -0.001512 | 0.906410 | 0.492308 | -0.016629 |
| candidate_ppopt130_p95_tail_router__target_pp82_p95__thr_0p3__width_0p18__s_0p28__cap_0p008__4ad7f572ab | 0.270211 | 0.807489 | -0.000353 | -0.000010 | -0.000351 | -0.001438 | 0.906410 | 0.491987 | -0.016609 |
| candidate_ppopt130_p95_tail_router__target_pp82_p95__thr_0p3__width_0p18__s_0p55__cap_0p008__998c339d7c | 0.270242 | 0.807488 | -0.000322 | -0.000010 | -0.000335 | -0.001402 | 0.907051 | 0.492628 | -0.016604 |
| pp134_p95_learned_stack_correction_challenger | 0.270242 | 0.807488 | -0.000322 | -0.000010 | -0.000335 | -0.001402 | 0.907051 | 0.492628 | -0.016604 |
| candidate_ppopt130_p95_tail_router__target_pp126_p95__thr_0p3__width_0p18__s_0p55__cap_0p008__38f988f5d4 | 0.270199 | 0.807490 | -0.000365 | -0.000009 | -0.000357 | -0.001439 | 0.905769 | 0.491987 | -0.016596 |
| candidate_ppopt130_p95_tail_router__target_pp82_p95__thr_0p3__width_0p26__s_0p4__cap_0p008__47544ad1b1 | 0.270221 | 0.807489 | -0.000343 | -0.000010 | -0.000346 | -0.001444 | 0.905769 | 0.492308 | -0.016574 |
| candidate_ppopt130_p95_tail_router__target_pp82_p95__thr_0p3__width_0p18__s_0p4__cap_0p008__03e3e137a0 | 0.270228 | 0.807489 | -0.000336 | -0.000010 | -0.000338 | -0.001422 | 0.905769 | 0.492308 | -0.016567 |
| candidate_ppopt128_harm_rollback__thr_0p1__pre_1p0__guard_0p5__floor_0p0__cap_0p018__ffbfe689ff | 0.269982 | 0.807490 | -0.000582 | -0.000009 | -0.000527 | -0.002221 | 0.899359 | 0.496474 | -0.016556 |
| candidate_ppopt128_harm_rollback__thr_0p1__pre_1p0__guard_0p5__floor_0p12__cap_0p018__6f161691f5 | 0.269982 | 0.807490 | -0.000582 | -0.000009 | -0.000527 | -0.002221 | 0.899359 | 0.496474 | -0.016556 |
| candidate_ppopt128_harm_rollback__thr_0p1__pre_1p0__guard_0p5__floor_0p25__cap_0p018__1e02f91e8b | 0.269982 | 0.807490 | -0.000582 | -0.000009 | -0.000527 | -0.002221 | 0.899359 | 0.496474 | -0.016556 |
| candidate_ppopt130_p95_tail_router__target_pp82_p95__thr_0p3__width_0p18__s_0p18__cap_0p022__fd9b4d10fb | 0.270191 | 0.807490 | -0.000373 | -0.000009 | -0.000352 | -0.001499 | 0.904487 | 0.491987 | -0.016552 |
| candidate_ppopt127_learned_gain_gate__safe_pp126_op__target_stack_huber_plain__hpen_0p65__rpen_0p45__t__205a387d26 | 0.269039 | 0.811466 | -0.001525 | 0.003967 | -0.001278 | -0.003197 | 0.944551 | 0.504487 | -0.016530 |
| candidate_ppopt130_p95_tail_router__target_pp82_p95__thr_0p3__width_0p26__s_0p28__cap_0p014__41ac710fe1 | 0.270204 | 0.807490 | -0.000360 | -0.000009 | -0.000345 | -0.001426 | 0.904167 | 0.491346 | -0.016527 |
| candidate_ppopt130_p95_tail_router__target_pp126_p95__thr_0p3__width_0p18__s_0p55__cap_0p014__c030858442 | 0.270209 | 0.807490 | -0.000355 | -0.000009 | -0.000344 | -0.001429 | 0.904167 | 0.491346 | -0.016522 |
| candidate_ppopt130_p95_tail_router__target_pp82_p95__thr_0p3__width_0p18__s_0p28__cap_0p014__6887f401a9 | 0.270221 | 0.807489 | -0.000343 | -0.000010 | -0.000334 | -0.001368 | 0.904167 | 0.491346 | -0.016509 |
| candidate_ppopt130_p95_tail_router__target_pp126_p95__thr_0p3__width_0p18__s_0p4__cap_0p022__8f35eebc90 | 0.270190 | 0.807490 | -0.000374 | -0.000009 | -0.000351 | -0.001512 | 0.901282 | 0.492308 | -0.016425 |

## 선택 후보 시나리오별 안정성
| candidate_label | eval_split | scenario | mean_delta_vs_pp64_MAPE | mean_delta_vs_pp64_p95_APE | pp64_MAPE_win_rate | pp64_p95_win_rate | pp64_all3_win_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pp126_operational_reference | test | artist_group_holdout | -0.000463 | 0.000003 | 1.000000 | 0.315385 | 0.265385 |
| pp126_operational_reference | test | confidence_stratified_rows | -0.000430 | 0.000022 | 1.000000 | 0.430769 | 0.342308 |
| pp126_operational_reference | test | full_split | -0.000450 | -0.000009 | 1.000000 | 1.000000 | 1.000000 |
| pp126_operational_reference | test | price_band_stratified_rows | -0.000432 | -0.000003 | 1.000000 | 0.376923 | 0.307692 |
| pp126_operational_reference | test | risk_focus_bootstrap | -0.001084 | -0.008342 | 0.992308 | 0.346154 | 0.030769 |
| pp126_operational_reference | test | row_bootstrap | -0.000462 | -0.000112 | 0.996154 | 0.315385 | 0.196154 |
| pp126_operational_reference | validation_oof | artist_group_holdout | -0.000371 | -0.003836 | 0.896154 | 0.576923 | 0.384615 |
| pp126_operational_reference | validation_oof | confidence_stratified_rows | -0.000384 | -0.002605 | 0.915385 | 0.526923 | 0.365385 |
| pp126_operational_reference | validation_oof | full_split | -0.000383 | -0.000025 | 1.000000 | 1.000000 | 0.000000 |
| pp126_operational_reference | validation_oof | price_band_stratified_rows | -0.000386 | -0.002142 | 0.911538 | 0.488462 | 0.292308 |
| pp126_operational_reference | validation_oof | risk_focus_bootstrap | -0.000227 | -0.001270 | 0.565385 | 0.138462 | 0.073077 |
| pp126_operational_reference | validation_oof | row_bootstrap | -0.000384 | -0.002389 | 0.753846 | 0.415385 | 0.219231 |
| pp126_p95_reference | test | artist_group_holdout | -0.000256 | 0.000085 | 1.000000 | 0.607692 | 0.438462 |
| pp126_p95_reference | test | confidence_stratified_rows | -0.000238 | 0.000089 | 1.000000 | 0.596154 | 0.346154 |
| pp126_p95_reference | test | full_split | -0.000247 | -0.000034 | 1.000000 | 1.000000 | 1.000000 |
| pp126_p95_reference | test | price_band_stratified_rows | -0.000241 | 0.000092 | 1.000000 | 0.553846 | 0.376923 |
| pp126_p95_reference | test | risk_focus_bootstrap | -0.000615 | -0.004214 | 0.996154 | 0.630769 | 0.238462 |
| pp126_p95_reference | test | row_bootstrap | -0.000256 | 0.000018 | 0.996154 | 0.473077 | 0.215385 |
| pp126_p95_reference | validation_oof | artist_group_holdout | -0.000190 | -0.002566 | 0.888462 | 0.738462 | 0.446154 |
| pp126_p95_reference | validation_oof | confidence_stratified_rows | -0.000197 | -0.001790 | 0.900000 | 0.742308 | 0.534615 |
| pp126_p95_reference | validation_oof | full_split | -0.000196 | -0.000025 | 1.000000 | 1.000000 | 1.000000 |
| pp126_p95_reference | validation_oof | price_band_stratified_rows | -0.000195 | -0.001328 | 0.888462 | 0.711538 | 0.461538 |
| pp126_p95_reference | validation_oof | risk_focus_bootstrap | -0.000033 | -0.000737 | 0.503846 | 0.365385 | 0.157692 |
| pp126_p95_reference | validation_oof | row_bootstrap | -0.000199 | -0.001571 | 0.746154 | 0.569231 | 0.257692 |
| pp134_operational_learned_stack_correction_challenger | test | artist_group_holdout | -0.000547 | 0.000013 | 1.000000 | 0.315385 | 0.292308 |
| pp134_operational_learned_stack_correction_challenger | test | confidence_stratified_rows | -0.000507 | 0.000032 | 1.000000 | 0.430769 | 0.361538 |
| pp134_operational_learned_stack_correction_challenger | test | full_split | -0.000531 | -0.000009 | 1.000000 | 1.000000 | 1.000000 |
| pp134_operational_learned_stack_correction_challenger | test | price_band_stratified_rows | -0.000510 | -0.000003 | 1.000000 | 0.376923 | 0.334615 |
| pp134_operational_learned_stack_correction_challenger | test | risk_focus_bootstrap | -0.001282 | -0.010033 | 0.992308 | 0.346154 | 0.026923 |
| pp134_operational_learned_stack_correction_challenger | test | row_bootstrap | -0.000546 | -0.000131 | 0.996154 | 0.315385 | 0.242308 |
| pp134_operational_learned_stack_correction_challenger | validation_oof | artist_group_holdout | -0.000373 | -0.004296 | 0.857692 | 0.596154 | 0.350000 |
| pp134_operational_learned_stack_correction_challenger | validation_oof | confidence_stratified_rows | -0.000391 | -0.002885 | 0.888462 | 0.526923 | 0.330769 |
| pp134_operational_learned_stack_correction_challenger | validation_oof | full_split | -0.000387 | -0.000025 | 1.000000 | 1.000000 | 0.000000 |
| pp134_operational_learned_stack_correction_challenger | validation_oof | price_band_stratified_rows | -0.000391 | -0.002430 | 0.876923 | 0.492308 | 0.265385 |
| pp134_operational_learned_stack_correction_challenger | validation_oof | risk_focus_bootstrap | -0.000251 | -0.001500 | 0.565385 | 0.138462 | 0.069231 |
| pp134_operational_learned_stack_correction_challenger | validation_oof | row_bootstrap | -0.000393 | -0.002678 | 0.742308 | 0.419231 | 0.215385 |
| pp134_p95_learned_stack_correction_challenger | test | artist_group_holdout | -0.000333 | -0.000002 | 1.000000 | 0.319231 | 0.242308 |
| pp134_p95_learned_stack_correction_challenger | test | confidence_stratified_rows | -0.000306 | 0.000016 | 1.000000 | 0.430769 | 0.323077 |
| pp134_p95_learned_stack_correction_challenger | test | full_split | -0.000322 | -0.000010 | 1.000000 | 1.000000 | 1.000000 |
| pp134_p95_learned_stack_correction_challenger | test | price_band_stratified_rows | -0.000308 | -0.000003 | 1.000000 | 0.376923 | 0.296154 |
| pp134_p95_learned_stack_correction_challenger | test | risk_focus_bootstrap | -0.000803 | -0.006460 | 0.976923 | 0.346154 | 0.038462 |
| pp134_p95_learned_stack_correction_challenger | test | row_bootstrap | -0.000333 | -0.000080 | 0.980769 | 0.315385 | 0.180769 |
| pp134_p95_learned_stack_correction_challenger | validation_oof | artist_group_holdout | -0.000293 | -0.003306 | 0.869231 | 0.576923 | 0.369231 |
| pp134_p95_learned_stack_correction_challenger | validation_oof | confidence_stratified_rows | -0.000308 | -0.002273 | 0.896154 | 0.519231 | 0.353846 |
| pp134_p95_learned_stack_correction_challenger | validation_oof | full_split | -0.000305 | -0.000025 | 1.000000 | 1.000000 | 1.000000 |
| pp134_p95_learned_stack_correction_challenger | validation_oof | price_band_stratified_rows | -0.000311 | -0.001798 | 0.888462 | 0.488462 | 0.296154 |
| pp134_p95_learned_stack_correction_challenger | validation_oof | risk_focus_bootstrap | -0.000095 | -0.000880 | 0.534615 | 0.138462 | 0.065385 |
| pp134_p95_learned_stack_correction_challenger | validation_oof | row_bootstrap | -0.000300 | -0.002006 | 0.738462 | 0.400000 | 0.211538 |

## 실행 설정
```json
{
  "experiment_id": "PP-OPT127-134",
  "experiment_slug": "PP-OPT127_134_warm_learned_stack_correction",
  "created_at": "2026-06-09T15:44:27",
  "seed": 20260609,
  "base_candidate": "hcoef_stable",
  "incumbent_candidate": "incumbent_operational_pp_opt7",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 4595,
  "prediction_rows": 5173970,
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
  "selection_decision": {
    "operational_label": "candidate_ppopt128_harm_rollback__thr_0p12__pre_0p55__guard_0p35__floor_0p0__cap_0p018__dab6f04fcb",
    "operational_candidate": "ppopt128_harm_rollback__thr=0p12__pre=0p55__guard=0p35__floor=0p0__cap=0p018",
    "operational_fixed_test_MAPE": 0.27003336455913124,
    "operational_fixed_test_p95_APE": 0.8074900608978479,
    "operational_delta_vs_pp64_MAPE": -0.000530677356529119,
    "operational_delta_vs_pp64_p95_APE": -8.791408261932254e-06,
    "operational_delta_vs_pp126_MAPE": -8.103219072058687e-05,
    "operational_delta_vs_pp126_p95_APE": 0.0,
    "operational_avg_pp64_MAPE_win_rate": 0.9099358974358974,
    "operational_avg_pp64_p95_win_rate": 0.496474358974359,
    "operational_replacement_score": -0.016928113253965017,
    "p95_label": "candidate_ppopt130_p95_tail_router__target_pp82_p95__thr_0p3__width_0p18__s_0p55__cap_0p008__998c339d7c",
    "p95_candidate": "ppopt130_p95_tail_router__target=pp82_p95__thr=0p3__width=0p18__s=0p55__cap=0p008",
    "p95_fixed_test_MAPE": 0.27024227034813875,
    "p95_fixed_test_p95_APE": 0.8074884989871484,
    "p95_delta_vs_pp64_MAPE": -0.0003217715675216115,
    "p95_delta_vs_pp64_p95_APE": -1.0353318961486835e-05,
    "p95_delta_vs_pp126_MAPE": 0.00012787359828692058,
    "p95_delta_vs_pp126_p95_APE": -1.5619106995545806e-06,
    "p95_avg_pp64_MAPE_win_rate": 0.907051282051282,
    "p95_avg_pp64_p95_win_rate": 0.49262820512820515,
    "p95_replacement_score": -0.016603822849572895,
    "operational_protocol_candidate": "ppopt134_operational_learned_stack_correction_challenger__source=ppopt128_harm_rollback__thr_0p12__pre_0p55__guard_0p35__floor_0p0__cap_0p018",
    "p95_protocol_candidate": "ppopt134_p95_learned_stack_correction_challenger__source=ppopt130_p95_tail_router__target_pp82_p95__thr_0p3__width_0p18__s_0p55__cap_0p008"
  },
  "items": [
    {
      "item_id": "PP-OPT127",
      "priority": "1",
      "title": "learned stack gain gate",
      "description": "LightGBM이 Huber stack 보정이 이길 가능성을 학습하고, 가능성이 높은 row에만 stack 이동을 적용한다."
    },
    {
      "item_id": "PP-OPT128",
      "priority": "2",
      "title": "learned harm rollback",
      "description": "보정 적용 시 오차가 커질 가능성을 별도 학습하고, 위험 row에서는 보정 이동량을 줄인다."
    },
    {
      "item_id": "PP-OPT129",
      "priority": "3",
      "title": "learned residual direction correction",
      "description": "PP126 운영 후보의 잔차 방향과 크기를 학습해 작은 추가 로그 보정으로 과대/과소 방향을 보정한다."
    },
    {
      "item_id": "PP-OPT130",
      "priority": "4",
      "title": "learned p95 tail router",
      "description": "p95 방어 후보가 이길 가능성이 높은 row에서만 PP126 p95 후보 또는 기존 p95 후보로 부분 이동한다."
    },
    {
      "item_id": "PP-OPT131",
      "priority": "5",
      "title": "segment adaptive learned threshold",
      "description": "학습된 gain score에 가격대, 신뢰도, risk별 threshold를 더해 보정 적용 구간을 세분화한다."
    },
    {
      "item_id": "PP-OPT132",
      "priority": "6",
      "title": "learned correction ensemble",
      "description": "stack gate, p95 router, residual direction 보정을 cap 안에서 가중 평균한다."
    },
    {
      "item_id": "PP-OPT133",
      "priority": "7",
      "title": "aggressive correction with learned guard",
      "description": "MAPE는 낮지만 p95가 흔들린 공격적 후보를 학습형 harm guard로 제한 채택한다."
    },
    {
      "item_id": "PP-OPT134",
      "priority": "8",
      "title": "final learned correction decision",
      "description": "고정 test와 반복 안정성 점수를 함께 보고 운영형/p95형 learned correction 후보를 결정한다."
    }
  ],
  "sources": {
    "pp119_config": "experiments/track6/PP-OPT119_126_warm_pp118_stack_gate_refinement/artifacts/run_config.json",
    "pp119_predictions": "experiments/track6/PP-OPT119_126_warm_pp118_stack_gate_refinement/outputs/candidate_predictions.csv",
    "pp119_metrics": "experiments/track6/PP-OPT119_126_warm_pp118_stack_gate_refinement/outputs/candidate_metrics.csv",
    "pp119_stability_aggregate": "experiments/track6/PP-OPT119_126_warm_pp118_stack_gate_refinement/outputs/selected_stability_candidate_aggregate.csv",
    "pp119_helper": "scripts/track6/run_pp_opt119_126_warm_pp118_stack_gate_refinement.py"
  }
}
```