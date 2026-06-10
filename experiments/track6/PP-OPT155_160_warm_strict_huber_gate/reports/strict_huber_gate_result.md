# PP-OPT155~160 Warm strict Huber gate 결과

- 작성일: 2026-06-09 17:03
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 목적: PP149의 낮은 MAPE 신호를 더 엄격한 적용 gate로 안정화
- 결론: 운영 후보 fixed test MAPE 0.270140, p95 0.807231. PP126 대비 MAPE +0.000026, p95 -0.000259. PP148 대비 MAPE +0.000000, p95 +0.000000.

## 주요 후보 test 비교
| candidate | family | item_id | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| reference_pp126_operational | reference_prior | REFERENCE | 0.136320 | 0.270114 | 0.807490 | 0.397588 | -0.001280 | -0.000640 |
| reference_pp148_operational | reference_prior | REFERENCE | 0.139801 | 0.270140 | 0.807231 | 0.397525 | -0.001255 | -0.000899 |
| ppopt160_operational_strict_huber_gate_challenger__source=reference_pp148_operational | strict_huber_gate_operational_selection | PP-OPT160 | 0.139801 | 0.270140 | 0.807231 | 0.397525 | -0.001255 | -0.000899 |
| reference_pp148_p95 | reference_prior | REFERENCE | 0.141036 | 0.270269 | 0.805949 | 0.397421 | -0.001126 | -0.002181 |
| ppopt160_p95_strict_huber_gate_challenger__source=reference_pp148_p95 | strict_huber_gate_p95_selection | PP-OPT160 | 0.141036 | 0.270269 | 0.805949 | 0.397421 | -0.001126 | -0.002181 |
| reference_pp64_current_best | reference_prior | REFERENCE | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | p95_test_MAPE | p95_test_p95_APE | operational_pass_vs_incumbent | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | strict stable-gain Huber gate | 720 | 0.270114 | 0.807490 | 0.270094 | 0.806582 | True | strict_stable_gain_huber_gate | ppopt155_strict_huber__thr=0p42__w=0p05__dmin=0p67__s=0p5__cap=0p003 |
| 4 | tail-safe strict Huber gate | 192 | 0.270114 | 0.807490 | 0.270114 | 0.807490 | True | tail_safe_strict_huber_gate | ppopt158_tail_safe_huber__thr=0p4__w=0p06__s=0p45__cap=0p0035 |
| 3 | segment quantile strict Huber gate | 192 | 0.270049 | 0.807211 | 0.269983 | 0.806851 | True | segment_quantile_strict_huber_gate | ppopt157_segment_quantile__seg=price_qwidth__q=0p84__s=1p0__cap=0p0035 |
| 5 | PP148 and strict Huber ensemble | 576 | 0.270132 | 0.807309 | 0.270103 | 0.806926 | False | pp148_strict_huber_ensemble | ppopt159_pp148_strict_ensemble__thr=0p4__w=0p14__p148=0p7__hs=0p15__cap=0p005 |
| 6 | final strict Huber gate decision | 2 | 0.270140 | 0.807231 | 0.270269 | 0.805949 | False | strict_huber_gate_operational_selection | ppopt160_operational_strict_huber_gate_challenger__source=reference_pp148_operational |
| 2 | PP148 plus strict Huber micro-gate | 240 | 0.270140 | 0.807231 | 0.270133 | 0.806865 | False | pp148_plus_strict_huber_micro_gate | ppopt156_pp148_strict_micro__thr=0p44__w=0p12__s=0p15__cap=0p0015 |

## 탐색 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt155_strict_huber__thr=0p42__w=0p05__dmin=0p67__s=0p5__cap=0p003 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p05__dmin=0p67__s=0p5__cap=0p0045 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p05__dmin=0p67__s=0p5__cap=0p006 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p05__dmin=0p67__s=0p5__cap=0p0075 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p05__dmin=0p67__s=0p7__cap=0p003 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p05__dmin=0p67__s=0p7__cap=0p0045 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p05__dmin=0p67__s=0p7__cap=0p006 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p05__dmin=0p67__s=0p7__cap=0p0075 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p05__dmin=0p67__s=0p9__cap=0p003 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p05__dmin=0p67__s=0p9__cap=0p0045 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p05__dmin=0p67__s=0p9__cap=0p006 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p05__dmin=0p67__s=0p9__cap=0p0075 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p05__dmin=0p67__s=1p0__cap=0p003 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p05__dmin=0p67__s=1p0__cap=0p0045 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p05__dmin=0p67__s=1p0__cap=0p006 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p05__dmin=0p67__s=1p0__cap=0p0075 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p08__dmin=0p67__s=0p5__cap=0p003 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p08__dmin=0p67__s=0p5__cap=0p0045 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p08__dmin=0p67__s=0p5__cap=0p006 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p08__dmin=0p67__s=0p5__cap=0p0075 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p08__dmin=0p67__s=0p7__cap=0p003 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p08__dmin=0p67__s=0p7__cap=0p0045 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p08__dmin=0p67__s=0p7__cap=0p006 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p08__dmin=0p67__s=0p7__cap=0p0075 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p08__dmin=0p67__s=0p9__cap=0p003 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p08__dmin=0p67__s=0p9__cap=0p0045 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p08__dmin=0p67__s=0p9__cap=0p006 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p08__dmin=0p67__s=0p9__cap=0p0075 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p08__dmin=0p67__s=1p0__cap=0p003 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p08__dmin=0p67__s=1p0__cap=0p0045 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p08__dmin=0p67__s=1p0__cap=0p006 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p08__dmin=0p67__s=1p0__cap=0p0075 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p12__dmin=0p67__s=0p5__cap=0p003 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p12__dmin=0p67__s=0p5__cap=0p0045 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p12__dmin=0p67__s=0p5__cap=0p006 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p12__dmin=0p67__s=0p5__cap=0p0075 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p12__dmin=0p67__s=0p7__cap=0p003 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p12__dmin=0p67__s=0p7__cap=0p0045 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p12__dmin=0p67__s=0p7__cap=0p006 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p12__dmin=0p67__s=0p7__cap=0p0075 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p12__dmin=0p67__s=0p9__cap=0p003 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p12__dmin=0p67__s=0p9__cap=0p0045 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p12__dmin=0p67__s=0p9__cap=0p006 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p12__dmin=0p67__s=0p9__cap=0p0075 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p12__dmin=0p67__s=1p0__cap=0p003 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p12__dmin=0p67__s=1p0__cap=0p0045 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p12__dmin=0p67__s=1p0__cap=0p006 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt155_strict_huber__thr=0p42__w=0p12__dmin=0p67__s=1p0__cap=0p0075 | PP-OPT155 | strict_stable_gain_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p06__s=0p45__cap=0p0035 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p06__s=0p45__cap=0p005 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p06__s=0p45__cap=0p0065 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p06__s=0p45__cap=0p008 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p06__s=0p65__cap=0p0035 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p06__s=0p65__cap=0p005 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p06__s=0p65__cap=0p0065 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p06__s=0p65__cap=0p008 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p06__s=0p85__cap=0p0035 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p06__s=0p85__cap=0p005 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p06__s=0p85__cap=0p0065 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p06__s=0p85__cap=0p008 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p06__s=1p0__cap=0p0035 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p06__s=1p0__cap=0p005 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p06__s=1p0__cap=0p0065 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p06__s=1p0__cap=0p008 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p16__s=0p45__cap=0p0035 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p16__s=0p45__cap=0p005 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p16__s=0p45__cap=0p0065 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p16__s=0p45__cap=0p008 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p16__s=0p65__cap=0p0035 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p16__s=0p65__cap=0p005 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p16__s=0p65__cap=0p0065 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p16__s=0p65__cap=0p008 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p16__s=0p85__cap=0p0035 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p16__s=0p85__cap=0p005 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p16__s=0p85__cap=0p0065 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p16__s=0p85__cap=0p008 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p16__s=1p0__cap=0p0035 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p16__s=1p0__cap=0p005 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p16__s=1p0__cap=0p0065 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |
| ppopt158_tail_safe_huber__thr=0p4__w=0p16__s=1p0__cap=0p008 | PP-OPT158 | tail_safe_strict_huber_gate | 0.270114 | 0.807490 | -0.001280 | -0.000640 | -0.002076 |

## 선택 후보 반복 안정성
| candidate_label | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_vs_pp64_MAPE | fixed_test_delta_vs_pp64_p95_APE | avg_pp64_MAPE_win_rate | avg_pp64_p95_win_rate | replacement_score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| candidate_ppopt156_pp148_strict_micro__thr_0p44__w_0p05__s_0p15__cap_0p0015__41c9a3a6e3 | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| candidate_ppopt156_pp148_strict_micro__thr_0p44__w_0p05__s_0p15__cap_0p0025__505b36f3ba | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| candidate_ppopt156_pp148_strict_micro__thr_0p44__w_0p05__s_0p15__cap_0p0035__06ae59bb48 | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| candidate_ppopt156_pp148_strict_micro__thr_0p44__w_0p05__s_0p15__cap_0p005__11a0235346 | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| candidate_ppopt156_pp148_strict_micro__thr_0p44__w_0p08__s_0p15__cap_0p0015__46797b8a92 | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| candidate_ppopt156_pp148_strict_micro__thr_0p44__w_0p08__s_0p15__cap_0p0025__1e9e47ee1b | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| candidate_ppopt156_pp148_strict_micro__thr_0p44__w_0p08__s_0p15__cap_0p0035__20a9487bd9 | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| candidate_ppopt156_pp148_strict_micro__thr_0p44__w_0p08__s_0p15__cap_0p005__5644ade78e | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| candidate_ppopt156_pp148_strict_micro__thr_0p44__w_0p12__s_0p15__cap_0p0015__b8480d8b93 | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| candidate_ppopt156_pp148_strict_micro__thr_0p44__w_0p12__s_0p15__cap_0p0025__dae0c26346 | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| candidate_ppopt156_pp148_strict_micro__thr_0p44__w_0p12__s_0p15__cap_0p0035__8e165ea0ff | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| candidate_ppopt156_pp148_strict_micro__thr_0p44__w_0p12__s_0p15__cap_0p005__725ebde46a | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| candidate_ppopt156_pp148_strict_micro__thr_0p4__w_0p05__s_0p15__cap_0p0015__fe4cc80e19 | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| candidate_ppopt156_pp148_strict_micro__thr_0p4__w_0p05__s_0p15__cap_0p0025__ef5399a40c | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| candidate_ppopt156_pp148_strict_micro__thr_0p4__w_0p05__s_0p15__cap_0p0035__d7ee4ac3d5 | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| candidate_ppopt156_pp148_strict_micro__thr_0p4__w_0p05__s_0p15__cap_0p005__b53b57e1c7 | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| candidate_ppopt156_pp148_strict_micro__thr_0p4__w_0p08__s_0p15__cap_0p0015__fa4c964d69 | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| candidate_ppopt156_pp148_strict_micro__thr_0p4__w_0p08__s_0p15__cap_0p0025__36b5bd3c52 | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| candidate_ppopt156_pp148_strict_micro__thr_0p4__w_0p08__s_0p15__cap_0p0035__7f7e913efc | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| candidate_ppopt156_pp148_strict_micro__thr_0p4__w_0p08__s_0p15__cap_0p005__ffd6f77d6a | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| candidate_ppopt156_pp148_strict_micro__thr_0p4__w_0p12__s_0p15__cap_0p0015__4554753fd5 | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| candidate_ppopt156_pp148_strict_micro__thr_0p4__w_0p12__s_0p15__cap_0p0025__5cbdf89ef2 | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| candidate_ppopt156_pp148_strict_micro__thr_0p4__w_0p12__s_0p15__cap_0p0035__6fb2e620eb | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| candidate_ppopt156_pp148_strict_micro__thr_0p4__w_0p12__s_0p15__cap_0p005__35e841e23f | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| pp148_operational_reference | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| pp160_operational_strict_huber_gate_challenger | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| candidate_ppopt156_pp148_strict_micro__thr_0p44__w_0p05__s_0p25__cap_0p0015__6a4a080bd4 | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925641 | 0.531090 | -0.017450 |
| candidate_ppopt156_pp148_strict_micro__thr_0p44__w_0p08__s_0p25__cap_0p0015__bea124a9de | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925641 | 0.531090 | -0.017450 |
| candidate_ppopt156_pp148_strict_micro__thr_0p44__w_0p12__s_0p25__cap_0p0015__a936072a0d | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925641 | 0.531090 | -0.017450 |
| candidate_ppopt156_pp148_strict_micro__thr_0p44__w_0p12__s_0p25__cap_0p0025__8773b1d874 | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925641 | 0.531090 | -0.017450 |
| candidate_ppopt156_pp148_strict_micro__thr_0p44__w_0p12__s_0p25__cap_0p0035__74dd4697a1 | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925641 | 0.531090 | -0.017450 |
| candidate_ppopt156_pp148_strict_micro__thr_0p44__w_0p12__s_0p25__cap_0p005__2971cf8e40 | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925641 | 0.531090 | -0.017450 |
| candidate_ppopt156_pp148_strict_micro__thr_0p44__w_0p12__s_0p35__cap_0p0015__affee6d041 | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925641 | 0.531090 | -0.017450 |
| candidate_ppopt156_pp148_strict_micro__thr_0p44__w_0p12__s_0p5__cap_0p0015__bc219ca16e | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925641 | 0.531090 | -0.017450 |
| candidate_ppopt159_pp148_strict_ensemble__thr_0p4__w_0p06__p148_1p0__hs_0p15__cap_0p007__eb83b01d4b | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925321 | 0.531090 | -0.017437 |
| candidate_ppopt159_pp148_strict_ensemble__thr_0p4__w_0p14__p148_1p0__hs_0p15__cap_0p007__fecfc1bb98 | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925321 | 0.531090 | -0.017437 |
| candidate_ppopt159_pp148_strict_ensemble__thr_0p4__w_0p1__p148_1p0__hs_0p15__cap_0p007__e18ec1f664 | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925321 | 0.531090 | -0.017437 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p05__dmin_0p67__s_0p5__cap_0p003__10f42507be | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p05__dmin_0p67__s_0p5__cap_0p0045__d496f9bf64 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p05__dmin_0p67__s_0p5__cap_0p006__f8c4d8ab81 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p05__dmin_0p67__s_0p5__cap_0p0075__c7e9bdb0a0 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p05__dmin_0p67__s_0p7__cap_0p003__4f31423a1c | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p05__dmin_0p67__s_0p7__cap_0p0045__c17ece48e4 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p05__dmin_0p67__s_0p7__cap_0p006__2d49fe7029 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p05__dmin_0p67__s_0p7__cap_0p0075__65217b053c | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p05__dmin_0p67__s_0p9__cap_0p003__5fbc751497 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p05__dmin_0p67__s_0p9__cap_0p0045__4dad945ff9 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p05__dmin_0p67__s_0p9__cap_0p006__535b9c8634 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p05__dmin_0p67__s_0p9__cap_0p0075__63eb567641 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p05__dmin_0p67__s_1p0__cap_0p003__1bd226e537 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p05__dmin_0p67__s_1p0__cap_0p0045__26f7427c6c | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p05__dmin_0p67__s_1p0__cap_0p006__5ccd9997a0 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p05__dmin_0p67__s_1p0__cap_0p0075__2589baf45a | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p08__dmin_0p67__s_0p5__cap_0p003__4620d4a8d4 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p08__dmin_0p67__s_0p5__cap_0p0045__789f9bfc61 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p08__dmin_0p67__s_0p5__cap_0p006__b804068d6d | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p08__dmin_0p67__s_0p5__cap_0p0075__8c913361a3 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p08__dmin_0p67__s_0p7__cap_0p003__b10943fb86 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p08__dmin_0p67__s_0p7__cap_0p0045__afe953dc36 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p08__dmin_0p67__s_0p7__cap_0p006__0125b8ff2a | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p08__dmin_0p67__s_0p7__cap_0p0075__7c254908a5 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p08__dmin_0p67__s_0p9__cap_0p003__7dfaf3bcf6 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p08__dmin_0p67__s_0p9__cap_0p0045__bc19ed5672 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p08__dmin_0p67__s_0p9__cap_0p006__2858f8b086 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p08__dmin_0p67__s_0p9__cap_0p0075__44446afe16 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p08__dmin_0p67__s_1p0__cap_0p003__3154ebc952 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p08__dmin_0p67__s_1p0__cap_0p0045__87fd20be48 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p08__dmin_0p67__s_1p0__cap_0p006__7cfc14aad2 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p08__dmin_0p67__s_1p0__cap_0p0075__25aa3cf878 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p12__dmin_0p67__s_0p5__cap_0p003__085766e972 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p12__dmin_0p67__s_0p5__cap_0p0045__7095432872 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p12__dmin_0p67__s_0p5__cap_0p006__7e76cc2943 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt155_strict_huber__thr_0p42__w_0p12__dmin_0p67__s_0p5__cap_0p0075__90770188b3 | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| pp126_operational_reference | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| pp134_operational_recomputed_reference | 0.270033 | 0.807490 | -0.000531 | -0.000009 | 0.909936 | 0.496474 | -0.016928 |
| pp118_operational_reference | 0.270139 | 0.807490 | -0.000425 | -0.000009 | 0.909295 | 0.494551 | -0.016797 |
| pp126_p95_reference | 0.270317 | 0.807465 | -0.000247 | -0.000034 | 0.909936 | 0.665705 | -0.016645 |
| candidate_ppopt157_segment_quantile__seg_price_qwidth__q_0p84__s_1p0__cap_0p005__00a7261d48 | 0.270021 | 0.807091 | -0.000543 | -0.000408 | 0.901603 | 0.559936 | -0.016607 |
| pp134_p95_recomputed_reference | 0.270242 | 0.807488 | -0.000322 | -0.000010 | 0.907051 | 0.492628 | -0.016604 |
| candidate_ppopt157_segment_quantile__seg_price_qwidth__q_0p9__s_1p0__cap_0p0065__9b4c26f3a0 | 0.270033 | 0.807490 | -0.000531 | -0.000009 | 0.901603 | 0.536538 | -0.016595 |
| candidate_ppopt157_segment_quantile__seg_price_qwidth__q_0p84__s_0p9__cap_0p005__9f821915fe | 0.270021 | 0.807091 | -0.000543 | -0.000408 | 0.901282 | 0.559936 | -0.016594 |
| candidate_ppopt157_segment_quantile__seg_price_qwidth__q_0p84__s_0p7__cap_0p005__72341442f5 | 0.270025 | 0.807091 | -0.000539 | -0.000408 | 0.900321 | 0.559936 | -0.016552 |
| candidate_ppopt157_segment_quantile__seg_price_qwidth__q_0p84__s_0p5__cap_0p0065__5aa0fd6c21 | 0.270026 | 0.806971 | -0.000538 | -0.000528 | 0.899359 | 0.561218 | -0.016513 |
| candidate_ppopt157_segment_quantile__seg_price_qwidth__q_0p84__s_0p5__cap_0p008__eff2c90625 | 0.270026 | 0.806911 | -0.000538 | -0.000588 | 0.899359 | 0.561538 | -0.016512 |
| candidate_ppopt157_segment_quantile__seg_price_qwidth__q_0p7__s_0p9__cap_0p005__e4d337109a | 0.270023 | 0.807270 | -0.000541 | -0.000229 | 0.897756 | 0.558013 | -0.016451 |
| candidate_ppopt157_segment_quantile__seg_price_qwidth__q_0p7__s_1p0__cap_0p005__3fc3691761 | 0.270020 | 0.807270 | -0.000544 | -0.000229 | 0.897436 | 0.558013 | -0.016441 |
| candidate_ppopt157_segment_quantile__seg_price_qwidth__q_0p7__s_0p7__cap_0p005__89f65309ed | 0.270031 | 0.807270 | -0.000533 | -0.000229 | 0.896795 | 0.558013 | -0.016405 |
| candidate_ppopt157_segment_quantile__seg_price_conf__q_0p7__s_1p0__cap_0p005__c70de87719 | 0.270034 | 0.807270 | -0.000530 | -0.000229 | 0.896795 | 0.631731 | -0.016402 |
| candidate_ppopt157_segment_quantile__seg_price_qwidth__q_0p9__s_0p9__cap_0p008__4c192790e9 | 0.270034 | 0.807490 | -0.000530 | -0.000009 | 0.896474 | 0.536538 | -0.016389 |
| candidate_ppopt157_segment_quantile__seg_price_qwidth__q_0p9__s_1p0__cap_0p008__0d90474f62 | 0.270026 | 0.807490 | -0.000538 | -0.000009 | 0.896154 | 0.536538 | -0.016385 |
| candidate_ppopt157_segment_quantile__seg_price_qwidth__q_0p84__s_1p0__cap_0p0065__8e7f64e0b5 | 0.269998 | 0.806971 | -0.000566 | -0.000528 | 0.894551 | 0.561218 | -0.016348 |
| candidate_ppopt157_segment_quantile__seg_price_conf__q_0p9__s_0p7__cap_0p008__151bd67a27 | 0.270083 | 0.806851 | -0.000481 | -0.000648 | 0.896474 | 0.537179 | -0.016340 |
| candidate_ppopt157_segment_quantile__seg_price_conf__q_0p78__s_1p0__cap_0p005__133101056d | 0.270027 | 0.807091 | -0.000537 | -0.000408 | 0.894872 | 0.569231 | -0.016332 |
| candidate_ppopt157_segment_quantile__seg_price_qwidth__q_0p84__s_0p7__cap_0p0065__7854f5497e | 0.270009 | 0.806971 | -0.000555 | -0.000528 | 0.894231 | 0.561218 | -0.016324 |
| candidate_ppopt157_segment_quantile__seg_price_conf__q_0p78__s_0p9__cap_0p005__d3fcd96b7e | 0.270028 | 0.807091 | -0.000536 | -0.000408 | 0.894551 | 0.569231 | -0.016318 |
| candidate_ppopt157_segment_quantile__seg_price_qwidth__q_0p84__s_0p9__cap_0p0065__e18f8b1ba7 | 0.270000 | 0.806971 | -0.000564 | -0.000528 | 0.893590 | 0.561218 | -0.016307 |
| candidate_ppopt157_segment_quantile__seg_price_conf__q_0p78__s_0p7__cap_0p005__6b7b870b67 | 0.270033 | 0.807091 | -0.000531 | -0.000408 | 0.893590 | 0.569231 | -0.016275 |
| candidate_ppopt157_segment_quantile__seg_price_qwidth__q_0p84__s_0p7__cap_0p008__ad294e16cb | 0.270004 | 0.806851 | -0.000560 | -0.000648 | 0.891346 | 0.562500 | -0.016214 |
| candidate_ppopt155_strict_huber__thr_0p26__w_0p08__dmin_0p34__s_0p9__cap_0p006__9b36d793b3 | 0.270135 | 0.806817 | -0.000429 | -0.000682 | 0.893269 | 0.515705 | -0.016160 |
| candidate_ppopt155_strict_huber__thr_0p26__w_0p08__dmin_0p34__s_1p0__cap_0p006__3cc08caaa2 | 0.270135 | 0.806764 | -0.000429 | -0.000735 | 0.891987 | 0.515705 | -0.016108 |

## 실행 설정
```json
{
  "experiment_id": "PP-OPT155-160",
  "experiment_slug": "PP-OPT155_160_warm_strict_huber_gate",
  "created_at": "2026-06-09T17:02:51",
  "seed": 20260609,
  "base_candidate": "hcoef_stable",
  "incumbent_candidate": "incumbent_operational_pp_opt7",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 1939,
  "prediction_rows": 2183314,
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
    "operational_protocol_candidate": "ppopt160_operational_strict_huber_gate_challenger__source=reference_pp148_operational",
    "p95_protocol_candidate": "ppopt160_p95_strict_huber_gate_challenger__source=reference_pp148_p95"
  },
  "items": [
    {
      "item_id": "PP-OPT155",
      "priority": "1",
      "title": "strict stable-gain Huber gate",
      "description": "Huber 후보가 안정적으로 이길 확률이 높은 row만 작은 cap으로 보정한다."
    },
    {
      "item_id": "PP-OPT156",
      "priority": "2",
      "title": "PP148 plus strict Huber micro-gate",
      "description": "PP148 운영 후보 위에 stable-gain 확률이 높은 row만 미세 Huber 보정을 더한다."
    },
    {
      "item_id": "PP-OPT157",
      "priority": "3",
      "title": "segment quantile strict Huber gate",
      "description": "가격대/신뢰도 구간별 validation score 상위 row에만 Huber 보정을 적용한다."
    },
    {
      "item_id": "PP-OPT158",
      "priority": "4",
      "title": "tail-safe strict Huber gate",
      "description": "p95 위험 방어를 우선해 tail harm, quantile width가 높은 row의 Huber 이동량을 줄인다."
    },
    {
      "item_id": "PP-OPT159",
      "priority": "5",
      "title": "PP148 and strict Huber ensemble",
      "description": "PP148의 안정성과 strict Huber의 MAPE 개선 신호를 작은 비율로 결합한다."
    },
    {
      "item_id": "PP-OPT160",
      "priority": "6",
      "title": "final strict Huber gate decision",
      "description": "PP126/PP148와 strict Huber 후보를 fixed/repeated 기준으로 비교한다."
    }
  ],
  "sources": {
    "pp149_helper": "scripts/track6/run_pp_opt149_154_warm_huber_adoption_stabilization.py"
  }
}
```