# PP-OPT161~166 Warm PP157 negative-gate rollback 결과

- 작성일: 2026-06-10 09:26
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 목적: PP157의 MAPE 개선 신호를 유지하면서 PP148 대비 손해 row를 rollback
- 결론: 운영 후보 fixed test MAPE 0.269997, p95 0.807231. PP126 대비 MAPE -0.000117, p95 -0.000259. PP148 대비 MAPE -0.000143, p95 +0.000000.

## 주요 후보 test 비교
| candidate | family | item_id | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| reference_pp157_price_qwidth_q084_s100_cap008 | reference_prior | REFERENCE | 0.136320 | 0.269983 | 0.806851 | 0.397567 | -0.001412 | -0.001279 |
| ppopt166_operational_pp157_negative_gate_challenger__source=ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap008__seg_price_conf__hw_1p2__thr_0p0__s_1p0__cap_0p006 | pp157_negative_gate_operational_selection | PP-OPT166 | 0.139801 | 0.269997 | 0.807231 | 0.397516 | -0.001398 | -0.000899 |
| reference_pp126_operational | reference_prior | REFERENCE | 0.136320 | 0.270114 | 0.807490 | 0.397588 | -0.001280 | -0.000640 |
| reference_pp148_operational | reference_prior | REFERENCE | 0.139801 | 0.270140 | 0.807231 | 0.397525 | -0.001255 | -0.000899 |
| ppopt166_p95_pp157_negative_gate_challenger__source=reference_pp148_p95 | pp157_negative_gate_p95_selection | PP-OPT166 | 0.141036 | 0.270269 | 0.805949 | 0.397421 | -0.001126 | -0.002181 |
| reference_pp64_current_best | reference_prior | REFERENCE | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | p95_test_MAPE | p95_test_p95_APE | operational_pass_vs_incumbent | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | PP157 gain-harm gated adoption | 72 | 0.270098 | 0.806877 | 0.270056 | 0.806665 | True | pp157_gain_harm_gated_adoption | ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s090_cap005__thr=0p18__w=0p1__hpen=0p5__s=1p0__cap=0p006 |
| 1 | PP157 harm-probability rollback | 72 | 0.270020 | 0.806949 | 0.269984 | 0.806592 | False | pp157_harm_probability_rollback | ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s090_cap005__hthr=0p3__w=0p14__rb=0p55__s=1p0__cap=0p006 |
| 5 | PP148 and negative-gated PP157 ensemble | 48 | 0.270121 | 0.807057 | 0.270099 | 0.806952 | False | pp148_negative_gated_pp157_ensemble | ppopt165_pp148_pp157_ensemble__target=pp157_price_qwidth_q084_s090_cap005__thr=0p18__p157=0p5__hpen=0p55__cap=0p005 |
| 3 | segment outcome rollback | 96 | 0.270035 | 0.807231 | 0.269988 | 0.807231 | False | segment_outcome_pp157_rollback | ppopt163_segment_outcome__target=pp157_price_qwidth_q084_s090_cap005__seg=price_qwidth__hw=1p2__thr=0p0__s=1p0__cap=0p006 |
| 6 | final PP157 negative-gate decision | 2 | 0.269997 | 0.807231 | 0.270269 | 0.805949 | False | pp157_negative_gate_operational_selection | ppopt166_operational_pp157_negative_gate_challenger__source=ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap008__seg_price_conf__hw_1p2__thr_0p0__s_1p0__cap_0p006 |
| 4 | hard negative classifier block | 48 | 0.270052 | 0.806892 | 0.270004 | 0.806592 | False | hard_negative_classifier_block | ppopt164_hard_block__target=pp157_price_qwidth_q084_s090_cap005__hthr=0p45__gthr=0p12__s=0p85__cap=0p006 |

## 탐색 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s090_cap005__thr=0p18__w=0p1__hpen=0p5__s=1p0__cap=0p006 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270098 | 0.806877 | -0.001297 | -0.001253 | -0.001949 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s090_cap005__thr=0p18__w=0p1__hpen=0p5__s=1p0__cap=0p008 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270098 | 0.806877 | -0.001297 | -0.001253 | -0.001949 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap0065__thr=0p18__w=0p1__hpen=0p5__s=0p85__cap=0p006 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270084 | 0.806840 | -0.001311 | -0.001290 | -0.001863 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap0065__thr=0p18__w=0p1__hpen=0p5__s=0p85__cap=0p008 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270084 | 0.806840 | -0.001311 | -0.001290 | -0.001863 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s090_cap005__thr=0p18__w=0p1__hpen=0p5__s=0p85__cap=0p006 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270104 | 0.806930 | -0.001290 | -0.001200 | -0.001859 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s090_cap005__thr=0p18__w=0p1__hpen=0p5__s=0p85__cap=0p008 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270104 | 0.806930 | -0.001290 | -0.001200 | -0.001859 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap0065__thr=0p18__w=0p1__hpen=0p5__s=1p0__cap=0p006 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270074 | 0.806771 | -0.001321 | -0.001359 | -0.001855 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap0065__thr=0p18__w=0p1__hpen=0p5__s=1p0__cap=0p008 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270074 | 0.806771 | -0.001321 | -0.001359 | -0.001853 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap008__thr=0p18__w=0p1__hpen=0p5__s=0p85__cap=0p006 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270067 | 0.806750 | -0.001328 | -0.001380 | -0.001820 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap008__thr=0p18__w=0p1__hpen=0p5__s=0p85__cap=0p008 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270067 | 0.806750 | -0.001328 | -0.001380 | -0.001817 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap0065__thr=0p18__w=0p1__hpen=0p75__s=1p0__cap=0p006 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270075 | 0.806801 | -0.001319 | -0.001329 | -0.001809 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap0065__thr=0p18__w=0p1__hpen=0p75__s=1p0__cap=0p008 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270075 | 0.806801 | -0.001319 | -0.001329 | -0.001809 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s090_cap005__thr=0p18__w=0p1__hpen=0p75__s=1p0__cap=0p006 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270098 | 0.806900 | -0.001297 | -0.001230 | -0.001806 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s090_cap005__thr=0p18__w=0p1__hpen=0p75__s=1p0__cap=0p008 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270098 | 0.806900 | -0.001297 | -0.001230 | -0.001806 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s090_cap005__hthr=0p3__w=0p14__rb=0p55__s=1p0__cap=0p006 | PP-OPT161 | pp157_harm_probability_rollback | 0.270020 | 0.806949 | -0.001375 | -0.001181 | -0.001758 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s090_cap005__hthr=0p3__w=0p14__rb=0p55__s=1p0__cap=0p008 | PP-OPT161 | pp157_harm_probability_rollback | 0.270019 | 0.806949 | -0.001376 | -0.001181 | -0.001756 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s090_cap005__hthr=0p4__w=0p14__rb=0p55__s=1p0__cap=0p006 | PP-OPT161 | pp157_harm_probability_rollback | 0.270014 | 0.806960 | -0.001380 | -0.001170 | -0.001754 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s090_cap005__hthr=0p4__w=0p14__rb=0p55__s=1p0__cap=0p008 | PP-OPT161 | pp157_harm_probability_rollback | 0.270013 | 0.806960 | -0.001382 | -0.001170 | -0.001750 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s090_cap005__thr=0p18__w=0p1__hpen=0p75__s=0p85__cap=0p006 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270105 | 0.806950 | -0.001290 | -0.001180 | -0.001744 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s090_cap005__thr=0p18__w=0p1__hpen=0p75__s=0p85__cap=0p008 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270105 | 0.806950 | -0.001290 | -0.001180 | -0.001744 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap008__thr=0p18__w=0p1__hpen=0p75__s=0p85__cap=0p006 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270069 | 0.806781 | -0.001326 | -0.001349 | -0.001744 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap008__thr=0p18__w=0p1__hpen=0p75__s=0p85__cap=0p008 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270069 | 0.806781 | -0.001326 | -0.001349 | -0.001742 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap0065__thr=0p18__w=0p1__hpen=0p75__s=0p85__cap=0p006 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270085 | 0.806865 | -0.001310 | -0.001265 | -0.001740 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap0065__thr=0p18__w=0p1__hpen=0p75__s=0p85__cap=0p008 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270085 | 0.806865 | -0.001310 | -0.001265 | -0.001740 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s100_cap0065__hthr=0p3__w=0p14__rb=0p55__s=1p0__cap=0p006 | PP-OPT161 | pp157_harm_probability_rollback | 0.269999 | 0.806829 | -0.001396 | -0.001301 | -0.001733 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s100_cap0065__hthr=0p4__w=0p14__rb=0p55__s=1p0__cap=0p006 | PP-OPT161 | pp157_harm_probability_rollback | 0.269991 | 0.806840 | -0.001404 | -0.001290 | -0.001733 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s100_cap0065__hthr=0p4__w=0p14__rb=0p55__s=1p0__cap=0p008 | PP-OPT161 | pp157_harm_probability_rollback | 0.269990 | 0.806840 | -0.001405 | -0.001290 | -0.001722 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s100_cap0065__hthr=0p3__w=0p14__rb=0p55__s=1p0__cap=0p008 | PP-OPT161 | pp157_harm_probability_rollback | 0.269999 | 0.806829 | -0.001396 | -0.001301 | -0.001718 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s090_cap005__hthr=0p3__w=0p14__rb=0p55__s=0p85__cap=0p006 | PP-OPT161 | pp157_harm_probability_rollback | 0.270036 | 0.806991 | -0.001359 | -0.001139 | -0.001713 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s090_cap005__hthr=0p3__w=0p14__rb=0p55__s=0p85__cap=0p008 | PP-OPT161 | pp157_harm_probability_rollback | 0.270036 | 0.806991 | -0.001359 | -0.001139 | -0.001713 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s090_cap005__hthr=0p4__w=0p14__rb=0p55__s=0p85__cap=0p006 | PP-OPT161 | pp157_harm_probability_rollback | 0.270031 | 0.807001 | -0.001364 | -0.001129 | -0.001708 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s090_cap005__hthr=0p4__w=0p14__rb=0p55__s=0p85__cap=0p008 | PP-OPT161 | pp157_harm_probability_rollback | 0.270031 | 0.807001 | -0.001364 | -0.001129 | -0.001708 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap008__thr=0p18__w=0p1__hpen=0p75__s=1p0__cap=0p006 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270058 | 0.806701 | -0.001337 | -0.001429 | -0.001697 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap008__thr=0p18__w=0p1__hpen=0p75__s=1p0__cap=0p008 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270058 | 0.806701 | -0.001337 | -0.001429 | -0.001689 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s100_cap0065__hthr=0p3__w=0p14__rb=0p55__s=0p85__cap=0p006 | PP-OPT161 | pp157_harm_probability_rollback | 0.270019 | 0.806889 | -0.001376 | -0.001241 | -0.001683 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s100_cap0065__hthr=0p3__w=0p14__rb=0p55__s=0p85__cap=0p008 | PP-OPT161 | pp157_harm_probability_rollback | 0.270019 | 0.806889 | -0.001376 | -0.001241 | -0.001682 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s100_cap0065__hthr=0p4__w=0p14__rb=0p55__s=0p85__cap=0p006 | PP-OPT161 | pp157_harm_probability_rollback | 0.270012 | 0.806899 | -0.001383 | -0.001231 | -0.001680 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s100_cap0065__hthr=0p4__w=0p14__rb=0p55__s=0p85__cap=0p008 | PP-OPT161 | pp157_harm_probability_rollback | 0.270012 | 0.806899 | -0.001383 | -0.001231 | -0.001678 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap008__thr=0p18__w=0p1__hpen=0p5__s=1p0__cap=0p006 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270056 | 0.806665 | -0.001339 | -0.001465 | -0.001672 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap008__thr=0p18__w=0p1__hpen=0p5__s=1p0__cap=0p008 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270056 | 0.806665 | -0.001339 | -0.001465 | -0.001661 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s100_cap008__hthr=0p4__w=0p14__rb=0p55__s=0p85__cap=0p006 | PP-OPT161 | pp157_harm_probability_rollback | 0.269995 | 0.806797 | -0.001399 | -0.001333 | -0.001655 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s100_cap008__hthr=0p3__w=0p14__rb=0p55__s=0p85__cap=0p006 | PP-OPT161 | pp157_harm_probability_rollback | 0.270003 | 0.806787 | -0.001391 | -0.001343 | -0.001654 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s100_cap008__hthr=0p3__w=0p14__rb=0p55__s=0p85__cap=0p008 | PP-OPT161 | pp157_harm_probability_rollback | 0.270005 | 0.806787 | -0.001390 | -0.001343 | -0.001644 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s100_cap008__hthr=0p4__w=0p14__rb=0p55__s=0p85__cap=0p008 | PP-OPT161 | pp157_harm_probability_rollback | 0.269997 | 0.806797 | -0.001398 | -0.001333 | -0.001641 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s090_cap005__thr=0p24__w=0p1__hpen=0p5__s=1p0__cap=0p006 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270110 | 0.806877 | -0.001285 | -0.001253 | -0.001640 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s090_cap005__thr=0p24__w=0p1__hpen=0p5__s=1p0__cap=0p008 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270110 | 0.806877 | -0.001285 | -0.001253 | -0.001640 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap0065__thr=0p24__w=0p1__hpen=0p5__s=1p0__cap=0p006 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270089 | 0.806771 | -0.001306 | -0.001359 | -0.001628 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap0065__thr=0p24__w=0p1__hpen=0p5__s=1p0__cap=0p008 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270089 | 0.806771 | -0.001306 | -0.001359 | -0.001628 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap008__thr=0p24__w=0p1__hpen=0p5__s=1p0__cap=0p008 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270073 | 0.806665 | -0.001322 | -0.001465 | -0.001622 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap008__thr=0p24__w=0p1__hpen=0p5__s=1p0__cap=0p006 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270073 | 0.806665 | -0.001322 | -0.001465 | -0.001622 |
| ppopt165_pp148_pp157_ensemble__target=pp157_price_qwidth_q084_s090_cap005__thr=0p18__p157=0p5__hpen=0p55__cap=0p005 | PP-OPT165 | pp148_negative_gated_pp157_ensemble | 0.270121 | 0.807057 | -0.001274 | -0.001073 | -0.001610 |
| ppopt165_pp148_pp157_ensemble__target=pp157_price_qwidth_q084_s090_cap005__thr=0p18__p157=0p5__hpen=0p55__cap=0p007 | PP-OPT165 | pp148_negative_gated_pp157_ensemble | 0.270121 | 0.807057 | -0.001274 | -0.001073 | -0.001610 |
| ppopt165_pp148_pp157_ensemble__target=pp157_price_qwidth_q084_s100_cap0065__thr=0p18__p157=0p5__hpen=0p55__cap=0p005 | PP-OPT165 | pp148_negative_gated_pp157_ensemble | 0.270109 | 0.807004 | -0.001285 | -0.001126 | -0.001608 |
| ppopt165_pp148_pp157_ensemble__target=pp157_price_qwidth_q084_s100_cap0065__thr=0p18__p157=0p5__hpen=0p55__cap=0p007 | PP-OPT165 | pp148_negative_gated_pp157_ensemble | 0.270109 | 0.807004 | -0.001285 | -0.001126 | -0.001608 |
| ppopt165_pp148_pp157_ensemble__target=pp157_price_qwidth_q084_s100_cap008__thr=0p18__p157=0p5__hpen=0p55__cap=0p005 | PP-OPT165 | pp148_negative_gated_pp157_ensemble | 0.270099 | 0.806952 | -0.001296 | -0.001178 | -0.001604 |
| ppopt165_pp148_pp157_ensemble__target=pp157_price_qwidth_q084_s100_cap008__thr=0p18__p157=0p5__hpen=0p55__cap=0p007 | PP-OPT165 | pp148_negative_gated_pp157_ensemble | 0.270099 | 0.806952 | -0.001296 | -0.001178 | -0.001604 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s090_cap005__hthr=0p3__w=0p14__rb=0p75__s=1p0__cap=0p006 | PP-OPT161 | pp157_harm_probability_rollback | 0.270020 | 0.806897 | -0.001375 | -0.001233 | -0.001600 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s090_cap005__hthr=0p3__w=0p14__rb=0p75__s=1p0__cap=0p008 | PP-OPT161 | pp157_harm_probability_rollback | 0.270018 | 0.806897 | -0.001377 | -0.001233 | -0.001599 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s090_cap005__hthr=0p4__w=0p14__rb=0p75__s=1p0__cap=0p006 | PP-OPT161 | pp157_harm_probability_rollback | 0.270012 | 0.806912 | -0.001383 | -0.001218 | -0.001595 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s100_cap008__hthr=0p4__w=0p14__rb=0p55__s=1p0__cap=0p006 | PP-OPT161 | pp157_harm_probability_rollback | 0.269973 | 0.806720 | -0.001422 | -0.001410 | -0.001595 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s090_cap005__thr=0p24__w=0p1__hpen=0p5__s=0p85__cap=0p006 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270115 | 0.806930 | -0.001280 | -0.001200 | -0.001595 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s090_cap005__thr=0p24__w=0p1__hpen=0p5__s=0p85__cap=0p008 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270115 | 0.806930 | -0.001280 | -0.001200 | -0.001595 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap0065__thr=0p24__w=0p1__hpen=0p5__s=0p85__cap=0p006 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270097 | 0.806840 | -0.001298 | -0.001290 | -0.001592 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap0065__thr=0p24__w=0p1__hpen=0p5__s=0p85__cap=0p008 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270097 | 0.806840 | -0.001298 | -0.001290 | -0.001592 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s090_cap005__hthr=0p4__w=0p14__rb=0p75__s=1p0__cap=0p008 | PP-OPT161 | pp157_harm_probability_rollback | 0.270010 | 0.806912 | -0.001385 | -0.001218 | -0.001590 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap008__thr=0p24__w=0p1__hpen=0p5__s=0p85__cap=0p006 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270081 | 0.806750 | -0.001314 | -0.001380 | -0.001589 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap008__thr=0p24__w=0p1__hpen=0p5__s=0p85__cap=0p008 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270081 | 0.806750 | -0.001314 | -0.001380 | -0.001587 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s090_cap005__thr=0p24__w=0p1__hpen=0p75__s=1p0__cap=0p006 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270111 | 0.806900 | -0.001284 | -0.001230 | -0.001580 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s090_cap005__thr=0p24__w=0p1__hpen=0p75__s=1p0__cap=0p008 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270111 | 0.806900 | -0.001284 | -0.001230 | -0.001580 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s100_cap008__hthr=0p3__w=0p14__rb=0p55__s=1p0__cap=0p006 | PP-OPT161 | pp157_harm_probability_rollback | 0.269981 | 0.806708 | -0.001414 | -0.001422 | -0.001580 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s090_cap005__hthr=0p3__w=0p14__rb=0p75__s=0p85__cap=0p006 | PP-OPT161 | pp157_harm_probability_rollback | 0.270036 | 0.806947 | -0.001359 | -0.001183 | -0.001580 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s090_cap005__hthr=0p3__w=0p14__rb=0p75__s=0p85__cap=0p008 | PP-OPT161 | pp157_harm_probability_rollback | 0.270036 | 0.806947 | -0.001359 | -0.001183 | -0.001580 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s090_cap005__hthr=0p4__w=0p14__rb=0p75__s=0p85__cap=0p006 | PP-OPT161 | pp157_harm_probability_rollback | 0.270029 | 0.806960 | -0.001366 | -0.001170 | -0.001573 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s100_cap0065__hthr=0p4__w=0p14__rb=0p75__s=1p0__cap=0p006 | PP-OPT161 | pp157_harm_probability_rollback | 0.269988 | 0.806792 | -0.001407 | -0.001338 | -0.001572 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s090_cap005__hthr=0p4__w=0p14__rb=0p75__s=0p85__cap=0p008 | PP-OPT161 | pp157_harm_probability_rollback | 0.270029 | 0.806960 | -0.001366 | -0.001170 | -0.001572 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap008__thr=0p24__w=0p1__hpen=0p75__s=1p0__cap=0p006 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270074 | 0.806701 | -0.001321 | -0.001429 | -0.001569 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap0065__thr=0p24__w=0p1__hpen=0p75__s=1p0__cap=0p006 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270090 | 0.806801 | -0.001304 | -0.001329 | -0.001569 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap0065__thr=0p24__w=0p1__hpen=0p75__s=1p0__cap=0p008 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270090 | 0.806801 | -0.001304 | -0.001329 | -0.001568 |
| ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s100_cap0065__hthr=0p3__w=0p14__rb=0p75__s=1p0__cap=0p006 | PP-OPT161 | pp157_harm_probability_rollback | 0.269999 | 0.806777 | -0.001396 | -0.001353 | -0.001565 |
| ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap008__thr=0p24__w=0p1__hpen=0p75__s=1p0__cap=0p008 | PP-OPT162 | pp157_gain_harm_gated_adoption | 0.270074 | 0.806701 | -0.001321 | -0.001429 | -0.001563 |

## 선택 후보 반복 안정성
| candidate_label | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_vs_pp64_MAPE | fixed_test_delta_vs_pp64_p95_APE | avg_pp64_MAPE_win_rate | avg_pp64_p95_win_rate | replacement_score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap008__seg_price_conf__hw_1p2__a8818b3400 | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.946795 | 0.601923 | -0.018439 |
| pp166_operational_pp157_negative_gate_challenger | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.946795 | 0.601923 | -0.018439 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap008__seg_price_conf__hw_1p2__3237aa96a1 | 0.270002 | 0.807231 | -0.000562 | -0.000268 | 0.945513 | 0.601923 | -0.018383 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap0065__seg_price_conf__hw_1p__3761c8b98a | 0.270016 | 0.807231 | -0.000548 | -0.000268 | 0.944551 | 0.600321 | -0.018330 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap0065__seg_price_conf__hw_1p__d93721a591 | 0.270016 | 0.807231 | -0.000548 | -0.000268 | 0.944551 | 0.600321 | -0.018330 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap0065__seg_price_conf__hw_1p__2c2227f818 | 0.270018 | 0.807231 | -0.000546 | -0.000268 | 0.944551 | 0.600321 | -0.018329 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap0065__seg_price_conf__hw_1p__9c2510ddb1 | 0.270018 | 0.807231 | -0.000546 | -0.000268 | 0.944551 | 0.600321 | -0.018329 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap008__seg_price_conf__hw_1p6__c9cd8ee338 | 0.269988 | 0.807231 | -0.000576 | -0.000268 | 0.943590 | 0.601923 | -0.018320 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s090_cap005__seg_price_conf__hw_1p2__e38431190a | 0.270038 | 0.807231 | -0.000526 | -0.000268 | 0.943910 | 0.598397 | -0.018282 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s090_cap005__seg_price_conf__hw_1p6__b73615228d | 0.270038 | 0.807231 | -0.000526 | -0.000268 | 0.943910 | 0.598397 | -0.018282 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap008__seg_price_conf__hw_1p2__da56129574 | 0.270017 | 0.807231 | -0.000547 | -0.000268 | 0.943269 | 0.602885 | -0.018277 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s090_cap005__seg_price_conf__hw_1p2__25c77c8236 | 0.270041 | 0.807231 | -0.000523 | -0.000268 | 0.943590 | 0.598397 | -0.018267 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s090_cap005__seg_price_conf__hw_1p6__48cef852ab | 0.270041 | 0.807231 | -0.000523 | -0.000268 | 0.943590 | 0.598397 | -0.018267 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap008__seg_price_qwidth__hw_1__461d682363 | 0.269991 | 0.807231 | -0.000573 | -0.000268 | 0.941987 | 0.595833 | -0.018252 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap008__seg_price_qwidth__hw_1__a5553df501 | 0.269991 | 0.807231 | -0.000573 | -0.000268 | 0.941987 | 0.595833 | -0.018252 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap008__seg_price_qwidth__hw_1__c7738ae888 | 0.269991 | 0.807231 | -0.000573 | -0.000268 | 0.941987 | 0.595833 | -0.018252 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap008__seg_price_qwidth__hw_1__f9f3f4b75b | 0.269991 | 0.807231 | -0.000573 | -0.000268 | 0.941987 | 0.595833 | -0.018252 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap008__seg_price_qwidth__hw_1__536e7b3f06 | 0.269992 | 0.807231 | -0.000572 | -0.000268 | 0.941667 | 0.595833 | -0.018238 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap008__seg_price_qwidth__hw_1__67c0de8f3c | 0.269992 | 0.807231 | -0.000572 | -0.000268 | 0.941667 | 0.595833 | -0.018238 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap008__seg_price_qwidth__hw_1__7b68e6a2c0 | 0.269992 | 0.807231 | -0.000572 | -0.000268 | 0.941667 | 0.595833 | -0.018238 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap008__seg_price_qwidth__hw_1__d8de1ac8de | 0.269992 | 0.807231 | -0.000572 | -0.000268 | 0.941667 | 0.595833 | -0.018238 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap008__seg_price_conf__hw_1p6__d0e7b05076 | 0.269993 | 0.807231 | -0.000571 | -0.000268 | 0.941346 | 0.601923 | -0.018225 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap0065__seg_price_qwidth__hw___2ccfd3caa5 | 0.270011 | 0.807231 | -0.000553 | -0.000268 | 0.941346 | 0.594231 | -0.018207 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap0065__seg_price_qwidth__hw___69a687818e | 0.270011 | 0.807231 | -0.000553 | -0.000268 | 0.941346 | 0.594231 | -0.018207 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap0065__seg_price_qwidth__hw___ddb7fe2356 | 0.270011 | 0.807231 | -0.000553 | -0.000268 | 0.941346 | 0.594231 | -0.018207 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap0065__seg_price_qwidth__hw___ffcaee3e8c | 0.270013 | 0.807231 | -0.000551 | -0.000268 | 0.941346 | 0.594231 | -0.018205 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap0065__seg_price_qwidth__hw___22332d7902 | 0.270013 | 0.807231 | -0.000551 | -0.000268 | 0.941346 | 0.594231 | -0.018205 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap0065__seg_price_qwidth__hw___7d9579aeb1 | 0.270013 | 0.807231 | -0.000551 | -0.000268 | 0.941346 | 0.594231 | -0.018205 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap0065__seg_price_qwidth__hw___e592497d51 | 0.270013 | 0.807231 | -0.000551 | -0.000268 | 0.941346 | 0.594231 | -0.018205 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap0065__seg_price_qwidth__hw___5097066c4c | 0.270014 | 0.807231 | -0.000550 | -0.000268 | 0.941346 | 0.594231 | -0.018204 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s090_cap005__seg_price_qwidth__hw_1__12a9d0c0c0 | 0.270035 | 0.807231 | -0.000530 | -0.000268 | 0.941667 | 0.592308 | -0.018196 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s090_cap005__seg_price_qwidth__hw_1__e7ec4e6d8a | 0.270032 | 0.807231 | -0.000532 | -0.000268 | 0.941346 | 0.592308 | -0.018186 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap0065__seg_price_qwidth__hw___8fa7470628 | 0.270031 | 0.807231 | -0.000533 | -0.000268 | 0.940385 | 0.592949 | -0.018149 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap0065__seg_price_qwidth__hw___346e5a9271 | 0.270031 | 0.807231 | -0.000533 | -0.000268 | 0.940385 | 0.592949 | -0.018148 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s090_cap005__seg_price_qwidth__hw_1__ddced3346e | 0.270048 | 0.807231 | -0.000517 | -0.000268 | 0.940385 | 0.588782 | -0.018132 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s090_cap005__seg_price_qwidth__hw_1__eb7b80ceb0 | 0.270048 | 0.807231 | -0.000516 | -0.000268 | 0.940385 | 0.588782 | -0.018132 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s090_cap005__seg_price_qwidth__hw_1__1383159ebb | 0.270031 | 0.807231 | -0.000533 | -0.000268 | 0.939423 | 0.592308 | -0.018110 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s090_cap005__seg_price_qwidth__hw_1__885bcb4f35 | 0.270031 | 0.807231 | -0.000533 | -0.000268 | 0.939423 | 0.592308 | -0.018110 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s090_cap005__seg_price_qwidth__hw_1__da066cdd9e | 0.270031 | 0.807231 | -0.000533 | -0.000268 | 0.939423 | 0.592308 | -0.018110 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s090_cap005__seg_price_qwidth__hw_1__6b94ce0ed0 | 0.270034 | 0.807231 | -0.000530 | -0.000268 | 0.939423 | 0.592308 | -0.018107 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s090_cap005__seg_price_qwidth__hw_1__b06f92b929 | 0.270034 | 0.807231 | -0.000530 | -0.000268 | 0.939423 | 0.592308 | -0.018107 |
| candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s090_cap005__seg_price_qwidth__hw_1__e5a64b2054 | 0.270034 | 0.807231 | -0.000530 | -0.000268 | 0.939423 | 0.592308 | -0.018107 |
| candidate_ppopt162_gain_harm_adopt__target_pp157_price_qwidth_q084_s100_cap008__thr_0p3__w_0p1__hpen_0__cbde3ae225 | 0.270105 | 0.806701 | -0.000459 | -0.000798 | 0.926923 | 0.586538 | -0.017536 |
| candidate_ppopt162_gain_harm_adopt__target_pp157_price_qwidth_q084_s100_cap008__thr_0p3__w_0p1__hpen_0__8387ef7b18 | 0.270106 | 0.806665 | -0.000458 | -0.000834 | 0.926603 | 0.586538 | -0.017522 |
| candidate_ppopt162_gain_harm_adopt__target_pp157_price_qwidth_q084_s100_cap008__thr_0p3__w_0p1__hpen_0__20253212f2 | 0.270105 | 0.806701 | -0.000459 | -0.000798 | 0.926282 | 0.586538 | -0.017510 |
| candidate_ppopt162_gain_harm_adopt__target_pp157_price_qwidth_q084_s100_cap008__thr_0p3__w_0p1__hpen_0__39ce9c7b12 | 0.270106 | 0.806665 | -0.000458 | -0.000834 | 0.926282 | 0.586538 | -0.017509 |
| pp148_operational_reference | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| candidate_ppopt162_gain_harm_adopt__target_pp157_price_qwidth_q084_s100_cap008__thr_0p24__w_0p1__hpen___b053bf032a | 0.270073 | 0.806665 | -0.000491 | -0.000834 | 0.923718 | 0.595833 | -0.017440 |
| candidate_ppopt162_gain_harm_adopt__target_pp157_price_qwidth_q084_s100_cap008__thr_0p24__w_0p1__hpen___11530db250 | 0.270074 | 0.806701 | -0.000490 | -0.000798 | 0.923718 | 0.595833 | -0.017438 |
| candidate_ppopt162_gain_harm_adopt__target_pp157_price_qwidth_q084_s100_cap008__thr_0p24__w_0p1__hpen___42e50e97b1 | 0.270073 | 0.806665 | -0.000491 | -0.000834 | 0.922115 | 0.595833 | -0.017376 |
| candidate_ppopt162_gain_harm_adopt__target_pp157_price_qwidth_q084_s100_cap008__thr_0p24__w_0p1__hpen___0bd744324b | 0.270074 | 0.806701 | -0.000490 | -0.000798 | 0.921795 | 0.595833 | -0.017362 |
| candidate_ppopt161_harm_rollback__target_pp157_price_qwidth_q084_s100_cap0065__hthr_0p4__w_0p14__rb_1p__1c82d9a8be | 0.269985 | 0.806733 | -0.000579 | -0.000766 | 0.917628 | 0.579808 | -0.017285 |
| candidate_ppopt162_gain_harm_adopt__target_pp157_price_qwidth_q084_s090_cap005__thr_0p18__w_0p1__hpen___b0b9db6fed | 0.270105 | 0.806950 | -0.000460 | -0.000549 | 0.920192 | 0.591667 | -0.017267 |
| candidate_ppopt162_gain_harm_adopt__target_pp157_price_qwidth_q084_s090_cap005__thr_0p18__w_0p1__hpen___eef4cf2eab | 0.270105 | 0.806950 | -0.000460 | -0.000549 | 0.920192 | 0.591667 | -0.017267 |
| candidate_ppopt162_gain_harm_adopt__target_pp157_price_qwidth_q084_s090_cap005__thr_0p18__w_0p1__hpen___79b0aefcf9 | 0.270104 | 0.806930 | -0.000460 | -0.000568 | 0.919551 | 0.591667 | -0.017242 |
| candidate_ppopt162_gain_harm_adopt__target_pp157_price_qwidth_q084_s090_cap005__thr_0p18__w_0p1__hpen___cdd4194252 | 0.270104 | 0.806930 | -0.000460 | -0.000568 | 0.919551 | 0.591667 | -0.017242 |
| candidate_ppopt164_hard_block__target_pp157_price_qwidth_q084_s100_cap008__hthr_0p35__gthr_0p12__s_1p0__0febb45240 | 0.270007 | 0.806592 | -0.000557 | -0.000907 | 0.916987 | 0.570833 | -0.017237 |
| candidate_ppopt161_harm_rollback__target_pp157_price_qwidth_q084_s090_cap005__hthr_0p4__w_0p14__rb_0p5__56f41c10a6 | 0.270031 | 0.807001 | -0.000533 | -0.000498 | 0.917308 | 0.590705 | -0.017225 |
| pp126_operational_reference | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt161_harm_rollback__target_pp157_price_qwidth_q084_s100_cap008__hthr_0p4__w_0p14__rb_1p0__2b18b2ee3e | 0.269966 | 0.806612 | -0.000598 | -0.000886 | 0.915385 | 0.581090 | -0.017213 |
| candidate_ppopt161_harm_rollback__target_pp157_price_qwidth_q084_s100_cap008__hthr_0p3__w_0p14__rb_1p0__0a2b8ed9eb | 0.269984 | 0.806592 | -0.000580 | -0.000907 | 0.915705 | 0.571795 | -0.017208 |
| candidate_ppopt161_harm_rollback__target_pp157_price_qwidth_q084_s100_cap0065__hthr_0p4__w_0p14__rb_1p__43ad9d2707 | 0.269984 | 0.806733 | -0.000580 | -0.000766 | 0.915705 | 0.579808 | -0.017208 |
| candidate_ppopt161_harm_rollback__target_pp157_price_qwidth_q084_s090_cap005__hthr_0p3__w_0p14__rb_0p5__2d0fe03904 | 0.270036 | 0.806991 | -0.000528 | -0.000508 | 0.916987 | 0.590385 | -0.017207 |
| candidate_ppopt161_harm_rollback__target_pp157_price_qwidth_q084_s090_cap005__hthr_0p3__w_0p14__rb_0p5__da3b4f8d83 | 0.270036 | 0.806991 | -0.000528 | -0.000508 | 0.916987 | 0.590385 | -0.017207 |
| candidate_ppopt161_harm_rollback__target_pp157_price_qwidth_q084_s090_cap005__hthr_0p4__w_0p14__rb_0p5__195fdaf4cd | 0.270031 | 0.807001 | -0.000533 | -0.000498 | 0.916667 | 0.590705 | -0.017200 |
| candidate_ppopt162_gain_harm_adopt__target_pp157_price_qwidth_q084_s100_cap0065__thr_0p18__w_0p1__hpen__a146d67e58 | 0.270085 | 0.806865 | -0.000479 | -0.000633 | 0.917949 | 0.595833 | -0.017197 |
| candidate_ppopt162_gain_harm_adopt__target_pp157_price_qwidth_q084_s100_cap0065__thr_0p18__w_0p1__hpen__afecffd8fc | 0.270085 | 0.806865 | -0.000479 | -0.000633 | 0.917949 | 0.595833 | -0.017197 |
| candidate_ppopt162_gain_harm_adopt__target_pp157_price_qwidth_q084_s090_cap005__thr_0p18__w_0p1__hpen___2a0c43a5d7 | 0.270098 | 0.806900 | -0.000466 | -0.000599 | 0.918269 | 0.595192 | -0.017197 |
| candidate_ppopt162_gain_harm_adopt__target_pp157_price_qwidth_q084_s090_cap005__thr_0p18__w_0p1__hpen___36944ee686 | 0.270098 | 0.806900 | -0.000466 | -0.000599 | 0.918269 | 0.595192 | -0.017197 |
| candidate_ppopt164_hard_block__target_pp157_price_qwidth_q084_s100_cap008__hthr_0p35__gthr_0p12__s_0p8__2b25540eec | 0.270027 | 0.806688 | -0.000537 | -0.000811 | 0.916026 | 0.585256 | -0.017178 |
| candidate_ppopt161_harm_rollback__target_pp157_price_qwidth_q084_s100_cap008__hthr_0p3__w_0p14__rb_1p0__8633bb04af | 0.270006 | 0.806688 | -0.000558 | -0.000811 | 0.915385 | 0.584936 | -0.017174 |
| candidate_ppopt161_harm_rollback__target_pp157_price_qwidth_q084_s090_cap005__hthr_0p3__w_0p14__rb_0p5__1bf04338ed | 0.270019 | 0.806949 | -0.000545 | -0.000550 | 0.915385 | 0.576282 | -0.017160 |
| candidate_ppopt161_harm_rollback__target_pp157_price_qwidth_q084_s090_cap005__hthr_0p3__w_0p14__rb_0p5__572c368086 | 0.270020 | 0.806949 | -0.000544 | -0.000550 | 0.915385 | 0.576282 | -0.017159 |
| candidate_ppopt161_harm_rollback__target_pp157_price_qwidth_q084_s090_cap005__hthr_0p4__w_0p14__rb_0p5__cb41a52750 | 0.270014 | 0.806960 | -0.000550 | -0.000539 | 0.915064 | 0.576282 | -0.017152 |
| candidate_ppopt161_harm_rollback__target_pp157_price_qwidth_q084_s090_cap005__hthr_0p4__w_0p14__rb_0p5__5feb45eeef | 0.270013 | 0.806960 | -0.000551 | -0.000539 | 0.914744 | 0.576282 | -0.017141 |
| candidate_ppopt162_gain_harm_adopt__target_pp157_price_qwidth_q084_s100_cap008__thr_0p18__w_0p1__hpen___04c2354ebc | 0.270069 | 0.806781 | -0.000495 | -0.000718 | 0.916026 | 0.595833 | -0.017136 |
| candidate_ppopt162_gain_harm_adopt__target_pp157_price_qwidth_q084_s100_cap008__thr_0p18__w_0p1__hpen___ca3a0b5ba8 | 0.270069 | 0.806781 | -0.000495 | -0.000718 | 0.916026 | 0.595833 | -0.017136 |
| candidate_ppopt162_gain_harm_adopt__target_pp157_price_qwidth_q084_s100_cap0065__thr_0p18__w_0p1__hpen__48919422fb | 0.270084 | 0.806840 | -0.000480 | -0.000659 | 0.916346 | 0.595833 | -0.017134 |
| candidate_ppopt162_gain_harm_adopt__target_pp157_price_qwidth_q084_s100_cap0065__thr_0p18__w_0p1__hpen__c85ea8f42f | 0.270084 | 0.806840 | -0.000480 | -0.000659 | 0.916346 | 0.595833 | -0.017134 |
| candidate_ppopt162_gain_harm_adopt__target_pp157_price_qwidth_q084_s090_cap005__thr_0p18__w_0p1__hpen___3e18ebdee8 | 0.270098 | 0.806877 | -0.000466 | -0.000621 | 0.916667 | 0.595513 | -0.017133 |
| candidate_ppopt162_gain_harm_adopt__target_pp157_price_qwidth_q084_s090_cap005__thr_0p18__w_0p1__hpen___571f69e3ee | 0.270098 | 0.806877 | -0.000466 | -0.000621 | 0.916667 | 0.595513 | -0.017133 |
| candidate_ppopt162_gain_harm_adopt__target_pp157_price_qwidth_q084_s100_cap0065__thr_0p18__w_0p1__hpen__763db7036c | 0.270075 | 0.806801 | -0.000489 | -0.000698 | 0.916026 | 0.595833 | -0.017130 |
| candidate_ppopt162_gain_harm_adopt__target_pp157_price_qwidth_q084_s100_cap0065__thr_0p18__w_0p1__hpen__e4df6c0c33 | 0.270075 | 0.806801 | -0.000489 | -0.000698 | 0.916026 | 0.595833 | -0.017130 |
| candidate_ppopt161_harm_rollback__target_pp157_price_qwidth_q084_s100_cap008__hthr_0p4__w_0p14__rb_1p0__4ad87687cb | 0.269990 | 0.806705 | -0.000574 | -0.000793 | 0.913462 | 0.595833 | -0.017113 |
| candidate_ppopt162_gain_harm_adopt__target_pp157_price_qwidth_q084_s100_cap008__thr_0p18__w_0p1__hpen___97db21a686 | 0.270058 | 0.806701 | -0.000506 | -0.000798 | 0.915064 | 0.596795 | -0.017109 |
| candidate_ppopt161_harm_rollback__target_pp157_price_qwidth_q084_s100_cap0065__hthr_0p3__w_0p14__rb_0p__97816b7864 | 0.269999 | 0.806777 | -0.000565 | -0.000722 | 0.913462 | 0.579808 | -0.017104 |
| candidate_ppopt161_harm_rollback__target_pp157_price_qwidth_q084_s100_cap0065__hthr_0p3__w_0p14__rb_0p__d61fc1d214 | 0.269999 | 0.806777 | -0.000565 | -0.000722 | 0.913462 | 0.579808 | -0.017103 |
| candidate_ppopt161_harm_rollback__target_pp157_price_qwidth_q084_s100_cap0065__hthr_0p4__w_0p14__rb_0p__e658568be1 | 0.269988 | 0.806792 | -0.000576 | -0.000707 | 0.913141 | 0.579808 | -0.017102 |
| candidate_ppopt164_hard_block__target_pp157_price_qwidth_q084_s100_cap008__hthr_0p35__gthr_0p2__s_1p0___4b427f6d32 | 0.270040 | 0.806592 | -0.000524 | -0.000907 | 0.914423 | 0.591346 | -0.017101 |
| candidate_ppopt161_harm_rollback__target_pp157_price_qwidth_q084_s100_cap008__hthr_0p3__w_0p14__rb_1p0__49b732eff8 | 0.270007 | 0.806688 | -0.000557 | -0.000811 | 0.913462 | 0.584936 | -0.017095 |
| candidate_ppopt162_gain_harm_adopt__target_pp157_price_qwidth_q084_s100_cap0065__thr_0p18__w_0p1__hpen__ae0cc57100 | 0.270074 | 0.806771 | -0.000490 | -0.000728 | 0.915064 | 0.595833 | -0.017093 |
| candidate_ppopt162_gain_harm_adopt__target_pp157_price_qwidth_q084_s100_cap008__thr_0p18__w_0p1__hpen___293032f6f3 | 0.270067 | 0.806750 | -0.000497 | -0.000749 | 0.914423 | 0.596795 | -0.017074 |
| candidate_ppopt164_hard_block__target_pp157_price_qwidth_q084_s100_cap008__hthr_0p35__gthr_0p2__s_0p85__41f41ddcb1 | 0.270054 | 0.806688 | -0.000510 | -0.000811 | 0.914103 | 0.589744 | -0.017074 |
| candidate_ppopt164_hard_block__target_pp157_price_qwidth_q084_s100_cap008__hthr_0p45__gthr_0p12__s_1p0__0a11ddcb4c | 0.270004 | 0.806592 | -0.000560 | -0.000907 | 0.912821 | 0.572115 | -0.017073 |
| candidate_ppopt162_gain_harm_adopt__target_pp157_price_qwidth_q084_s100_cap0065__thr_0p18__w_0p1__hpen__7b9cfff91a | 0.270074 | 0.806771 | -0.000490 | -0.000728 | 0.914423 | 0.595833 | -0.017067 |
| candidate_ppopt164_hard_block__target_pp157_price_qwidth_q084_s100_cap008__hthr_0p35__gthr_0p12__s_0p8__5617bdf4f9 | 0.270029 | 0.806688 | -0.000535 | -0.000811 | 0.913141 | 0.585256 | -0.017060 |
| candidate_ppopt162_gain_harm_adopt__target_pp157_price_qwidth_q084_s100_cap008__thr_0p18__w_0p1__hpen___e973e83120 | 0.270056 | 0.806665 | -0.000508 | -0.000834 | 0.913782 | 0.597115 | -0.017059 |
| candidate_ppopt162_gain_harm_adopt__target_pp157_price_qwidth_q084_s100_cap008__thr_0p18__w_0p1__hpen___8f3a8d8381 | 0.270067 | 0.806750 | -0.000497 | -0.000749 | 0.913782 | 0.596795 | -0.017048 |
| candidate_ppopt164_hard_block__target_pp157_price_qwidth_q084_s100_cap008__hthr_0p45__gthr_0p2__s_1p0___f1df6399a7 | 0.270048 | 0.806592 | -0.000516 | -0.000907 | 0.913141 | 0.592628 | -0.017042 |
| candidate_ppopt164_hard_block__target_pp157_price_qwidth_q084_s100_cap008__hthr_0p35__gthr_0p2__s_0p85__79a44bc090 | 0.270056 | 0.806688 | -0.000508 | -0.000811 | 0.913141 | 0.589744 | -0.017034 |

## 실행 설정
```json
{
  "experiment_id": "PP-OPT161-166",
  "experiment_slug": "PP-OPT161_166_warm_pp157_negative_gate_rollback",
  "created_at": "2026-06-10T09:26:19",
  "seed": 20260609,
  "base_candidate": "hcoef_stable",
  "incumbent_candidate": "incumbent_operational_pp_opt7",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 357,
  "prediction_rows": 401982,
  "pp157_configs": [
    {
      "name": "price_qwidth_q084_s100_cap008",
      "seg": "price_qwidth",
      "cols": [
        "stable_price_band_code",
        "qwidth_band"
      ],
      "q": 0.84,
      "strength": 1.0,
      "cap": 0.008
    },
    {
      "name": "price_qwidth_q084_s100_cap0065",
      "seg": "price_qwidth",
      "cols": [
        "stable_price_band_code",
        "qwidth_band"
      ],
      "q": 0.84,
      "strength": 1.0,
      "cap": 0.0065
    },
    {
      "name": "price_qwidth_q084_s090_cap005",
      "seg": "price_qwidth",
      "cols": [
        "stable_price_band_code",
        "qwidth_band"
      ],
      "q": 0.84,
      "strength": 0.9,
      "cap": 0.005
    }
  ],
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
    "operational_label": "candidate_ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap008__seg_price_conf__hw_1p2__a8818b3400",
    "operational_candidate": "ppopt163_segment_outcome__target=pp157_price_qwidth_q084_s100_cap008__seg=price_conf__hw=1p2__thr=0p0__s=1p0__cap=0p006",
    "operational_fixed_test_MAPE": 0.2699969856652386,
    "operational_fixed_test_p95_APE": 0.8072309115386983,
    "operational_delta_vs_pp64_MAPE": -0.0005670562504217491,
    "operational_delta_vs_pp64_p95_APE": -0.00026794076741154527,
    "operational_delta_vs_pp126_MAPE": -0.00011741108461321703,
    "operational_delta_vs_pp126_p95_APE": -0.000259149359149613,
    "operational_delta_vs_pp148_MAPE": -0.00014300270734085574,
    "operational_delta_vs_pp148_p95_APE": 0.0,
    "operational_avg_pp64_MAPE_win_rate": 0.9467948717948719,
    "operational_avg_pp64_p95_win_rate": 0.6019230769230769,
    "operational_replacement_score": -0.018438851122216625,
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
    "operational_protocol_candidate": "ppopt166_operational_pp157_negative_gate_challenger__source=ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap008__seg_price_conf__hw_1p2__thr_0p0__s_1p0__cap_0p006",
    "p95_protocol_candidate": "ppopt166_p95_pp157_negative_gate_challenger__source=reference_pp148_p95"
  },
  "items": [
    {
      "item_id": "PP-OPT161",
      "priority": "1",
      "title": "PP157 harm-probability rollback",
      "description": "PP157이 PP148보다 나빠질 확률이 높은 row를 PP148 쪽으로 되돌린다."
    },
    {
      "item_id": "PP-OPT162",
      "priority": "2",
      "title": "PP157 gain-harm gated adoption",
      "description": "PP157 gain 확률과 harm 확률을 동시에 써서 PP148에서 PP157로 이동할 row만 선택한다."
    },
    {
      "item_id": "PP-OPT163",
      "priority": "3",
      "title": "segment outcome rollback",
      "description": "validation에서 PP157 손해율이 높은 가격대/불확실성 구간은 PP157 적용을 제한한다."
    },
    {
      "item_id": "PP-OPT164",
      "priority": "4",
      "title": "hard negative classifier block",
      "description": "negative classifier가 위험하다고 본 row는 PP157 이동을 완전히 차단한다."
    },
    {
      "item_id": "PP-OPT165",
      "priority": "5",
      "title": "PP148 and negative-gated PP157 ensemble",
      "description": "PP148의 안정성을 유지하면서 PP157의 MAPE 개선분만 작은 비율로 섞는다."
    },
    {
      "item_id": "PP-OPT166",
      "priority": "6",
      "title": "final PP157 negative-gate decision",
      "description": "PP148/PP157 negative-gate 후보를 fixed/repeated 기준으로 비교한다."
    }
  ],
  "sources": {
    "pp155_helper": "scripts/track6/run_pp_opt155_160_warm_strict_huber_gate.py"
  }
}
```