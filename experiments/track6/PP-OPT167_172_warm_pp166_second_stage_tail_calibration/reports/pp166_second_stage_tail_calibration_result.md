# PP-OPT167~172 Warm PP166 second-stage tail calibration 결과

- 작성일: 2026-06-10 09:41
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 목적: PP166 기준 운영 후보 위에 tail-only 보정 또는 2차 rollback을 얹을 수 있는지 검증
- 결론: 운영 후보 fixed test MAPE 0.269997, p95 0.807231. PP166 대비 MAPE +0.000000, p95 +0.000000.

## 주요 후보 test 비교
| candidate | family | item_id | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt166_operational_pp157_negative_gate_challenger__source=ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap008__seg_price_conf__hw_1p2__thr_0p0__s_1p0__cap_0p006 | reference_prior | REFERENCE | 0.139801 | 0.269997 | 0.807231 | 0.397516 | -0.001398 | -0.000899 |
| ppopt172_operational_pp166_tail_calibration_challenger__source=ppopt169_segment_router__source_pp162_p95_gate__seg_price_conf__thr_m0p04__s_0p5__cap_0p004 | pp166_tail_calibration_operational_selection | PP-OPT172 | 0.139801 | 0.269997 | 0.807231 | 0.397516 | -0.001397 | -0.000899 |
| reference_pp126_operational | reference_prior | REFERENCE | 0.136320 | 0.270114 | 0.807490 | 0.397588 | -0.001280 | -0.000640 |
| reference_pp148_operational | reference_prior | REFERENCE | 0.139801 | 0.270140 | 0.807231 | 0.397525 | -0.001255 | -0.000899 |
| reference_pp148_p95 | reference_prior | REFERENCE | 0.141036 | 0.270269 | 0.805949 | 0.397421 | -0.001126 | -0.002181 |
| ppopt172_p95_pp166_tail_calibration_challenger__source=reference_pp148_p95 | pp166_tail_calibration_p95_selection | PP-OPT172 | 0.141036 | 0.270269 | 0.805949 | 0.397421 | -0.001126 | -0.002181 |
| reference_pp64_current_best | reference_prior | REFERENCE | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | p95_test_MAPE | p95_test_p95_APE | operational_pass_vs_incumbent | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | PP166 second-stage rollback | 36 | 0.270015 | 0.807231 | 0.269996 | 0.807231 | False | pp166_second_stage_rollback | ppopt168_second_rollback__seg=price_qwidth__hthr=0p0__rb=0p75__cap=0p003 |
| 1 | PP166 tail-only p95 blend | 72 | 0.270007 | 0.807231 | 0.269997 | 0.807222 | False | pp166_tail_only_p95_blend | ppopt167_tail_p95_blend__source=pp148_p95__tail=0p45__s=0p65__cap=0p003 |
| 3 | segment p95 candidate router | 48 | 0.269998 | 0.807231 | 0.269995 | 0.807231 | False | segment_p95_candidate_router | ppopt169_segment_router__source=pp162_p95_gate__seg=price_conf__thr=m0p04__s=0p8__cap=0p004 |
| 6 | final PP166 tail calibration decision | 2 | 0.269997 | 0.807231 | 0.270269 | 0.805949 | False | pp166_tail_calibration_operational_selection | ppopt172_operational_pp166_tail_calibration_challenger__source=ppopt169_segment_router__source_pp162_p95_gate__seg_price_conf__thr_m0p04__s_0p5__cap_0p004 |
| 4 | tail-aware dynamic cap | 24 | 0.269997 | 0.807231 | 0.269996 | 0.807231 | False | tail_aware_dynamic_cap | ppopt170_dynamic_cap__source=pp161_p95_guard__thr=0p04__s=0p45__basecap=0p004 |
| 5 | consensus correction ensemble | 24 | 0.269997 | 0.807231 | 0.269996 | 0.807231 | False | consensus_correction_ensemble | ppopt171_consensus__left=pp161_p95_guard__right=pp162_p95_gate__thr=0p02__s=0p35__cap=0p0035 |

## 탐색 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt168_second_rollback__seg=price_qwidth__hthr=0p0__rb=0p75__cap=0p003 | PP-OPT168 | pp166_second_stage_rollback | 0.270015 | 0.807231 | -0.001380 | -0.000899 | -0.001545 |
| ppopt168_second_rollback__seg=price_qwidth__hthr=0p0__rb=0p75__cap=0p005 | PP-OPT168 | pp166_second_stage_rollback | 0.270015 | 0.807231 | -0.001380 | -0.000899 | -0.001545 |
| ppopt168_second_rollback__seg=price_qwidth__hthr=0p0__rb=0p5__cap=0p003 | PP-OPT168 | pp166_second_stage_rollback | 0.270009 | 0.807231 | -0.001386 | -0.000899 | -0.001543 |
| ppopt168_second_rollback__seg=price_qwidth__hthr=0p0__rb=0p5__cap=0p005 | PP-OPT168 | pp166_second_stage_rollback | 0.270009 | 0.807231 | -0.001386 | -0.000899 | -0.001543 |
| ppopt167_tail_p95_blend__source=pp148_p95__tail=0p45__s=0p65__cap=0p003 | PP-OPT167 | pp166_tail_only_p95_blend | 0.270007 | 0.807231 | -0.001388 | -0.000899 | -0.001543 |
| ppopt167_tail_p95_blend__source=pp148_p95__tail=0p45__s=0p65__cap=0p005 | PP-OPT167 | pp166_tail_only_p95_blend | 0.270007 | 0.807231 | -0.001388 | -0.000899 | -0.001543 |
| ppopt168_second_rollback__seg=price_qwidth__hthr=0p05__rb=0p75__cap=0p003 | PP-OPT168 | pp166_second_stage_rollback | 0.270005 | 0.807231 | -0.001390 | -0.000899 | -0.001542 |
| ppopt168_second_rollback__seg=price_qwidth__hthr=0p05__rb=0p75__cap=0p005 | PP-OPT168 | pp166_second_stage_rollback | 0.270005 | 0.807231 | -0.001390 | -0.000899 | -0.001542 |
| ppopt167_tail_p95_blend__source=pp148_p95__tail=0p45__s=0p45__cap=0p003 | PP-OPT167 | pp166_tail_only_p95_blend | 0.270004 | 0.807231 | -0.001391 | -0.000899 | -0.001542 |
| ppopt167_tail_p95_blend__source=pp148_p95__tail=0p45__s=0p45__cap=0p005 | PP-OPT167 | pp166_tail_only_p95_blend | 0.270004 | 0.807231 | -0.001391 | -0.000899 | -0.001542 |
| ppopt168_second_rollback__seg=price_qwidth__hthr=0p05__rb=0p5__cap=0p003 | PP-OPT168 | pp166_second_stage_rollback | 0.270002 | 0.807231 | -0.001393 | -0.000899 | -0.001541 |
| ppopt168_second_rollback__seg=price_qwidth__hthr=0p05__rb=0p5__cap=0p005 | PP-OPT168 | pp166_second_stage_rollback | 0.270002 | 0.807231 | -0.001393 | -0.000899 | -0.001541 |
| ppopt168_second_rollback__seg=price_qwidth__hthr=0p0__rb=0p25__cap=0p003 | PP-OPT168 | pp166_second_stage_rollback | 0.270003 | 0.807231 | -0.001392 | -0.000899 | -0.001541 |
| ppopt168_second_rollback__seg=price_qwidth__hthr=0p0__rb=0p25__cap=0p005 | PP-OPT168 | pp166_second_stage_rollback | 0.270003 | 0.807231 | -0.001392 | -0.000899 | -0.001541 |
| ppopt169_segment_router__source=pp162_p95_gate__seg=price_conf__thr=m0p04__s=0p8__cap=0p004 | PP-OPT169 | segment_p95_candidate_router | 0.269998 | 0.807231 | -0.001397 | -0.000899 | -0.001541 |
| ppopt169_segment_router__source=pp162_p95_gate__seg=price_conf__thr=m0p04__s=0p8__cap=0p006 | PP-OPT169 | segment_p95_candidate_router | 0.269998 | 0.807231 | -0.001397 | -0.000899 | -0.001541 |
| ppopt167_tail_p95_blend__source=pp148_p95__tail=0p45__s=0p25__cap=0p003 | PP-OPT167 | pp166_tail_only_p95_blend | 0.270001 | 0.807231 | -0.001394 | -0.000899 | -0.001541 |
| ppopt167_tail_p95_blend__source=pp148_p95__tail=0p45__s=0p25__cap=0p005 | PP-OPT167 | pp166_tail_only_p95_blend | 0.270001 | 0.807231 | -0.001394 | -0.000899 | -0.001541 |
| ppopt169_segment_router__source=pp162_p95_gate__seg=price_conf__thr=m0p04__s=0p5__cap=0p004 | PP-OPT169 | segment_p95_candidate_router | 0.269997 | 0.807231 | -0.001397 | -0.000899 | -0.001541 |
| ppopt169_segment_router__source=pp162_p95_gate__seg=price_conf__thr=m0p04__s=0p5__cap=0p006 | PP-OPT169 | segment_p95_candidate_router | 0.269997 | 0.807231 | -0.001397 | -0.000899 | -0.001541 |
| ppopt172_operational_pp166_tail_calibration_challenger__source=ppopt169_segment_router__source_pp162_p95_gate__seg_price_conf__thr_m0p04__s_0p5__cap_0p004 | PP-OPT172 | pp166_tail_calibration_operational_selection | 0.269997 | 0.807231 | -0.001397 | -0.000899 | -0.001541 |
| ppopt168_second_rollback__seg=price_qwidth__hthr=0p05__rb=0p25__cap=0p003 | PP-OPT168 | pp166_second_stage_rollback | 0.270000 | 0.807231 | -0.001395 | -0.000899 | -0.001541 |
| ppopt168_second_rollback__seg=price_qwidth__hthr=0p05__rb=0p25__cap=0p005 | PP-OPT168 | pp166_second_stage_rollback | 0.270000 | 0.807231 | -0.001395 | -0.000899 | -0.001541 |
| ppopt167_tail_p95_blend__source=pp162_p95_gate__tail=0p45__s=0p65__cap=0p003 | PP-OPT167 | pp166_tail_only_p95_blend | 0.269997 | 0.807222 | -0.001398 | -0.000908 | -0.001540 |
| ppopt167_tail_p95_blend__source=pp162_p95_gate__tail=0p45__s=0p65__cap=0p005 | PP-OPT167 | pp166_tail_only_p95_blend | 0.269997 | 0.807222 | -0.001398 | -0.000908 | -0.001540 |
| ppopt167_tail_p95_blend__source=pp162_p95_gate__tail=0p45__s=0p45__cap=0p003 | PP-OPT167 | pp166_tail_only_p95_blend | 0.269997 | 0.807225 | -0.001398 | -0.000905 | -0.001540 |
| ppopt167_tail_p95_blend__source=pp162_p95_gate__tail=0p45__s=0p45__cap=0p005 | PP-OPT167 | pp166_tail_only_p95_blend | 0.269997 | 0.807225 | -0.001398 | -0.000905 | -0.001540 |
| ppopt167_tail_p95_blend__source=pp162_p95_gate__tail=0p45__s=0p25__cap=0p003 | PP-OPT167 | pp166_tail_only_p95_blend | 0.269997 | 0.807227 | -0.001398 | -0.000903 | -0.001540 |
| ppopt167_tail_p95_blend__source=pp162_p95_gate__tail=0p45__s=0p25__cap=0p005 | PP-OPT167 | pp166_tail_only_p95_blend | 0.269997 | 0.807227 | -0.001398 | -0.000903 | -0.001540 |
| ppopt168_second_rollback__seg=price_sample__hthr=0p0__rb=0p75__cap=0p003 | PP-OPT168 | pp166_second_stage_rollback | 0.269996 | 0.807231 | -0.001399 | -0.000899 | -0.001540 |
| ppopt168_second_rollback__seg=price_sample__hthr=0p0__rb=0p75__cap=0p005 | PP-OPT168 | pp166_second_stage_rollback | 0.269996 | 0.807231 | -0.001399 | -0.000899 | -0.001540 |
| ppopt168_second_rollback__seg=price_sample__hthr=0p0__rb=0p5__cap=0p003 | PP-OPT168 | pp166_second_stage_rollback | 0.269996 | 0.807231 | -0.001399 | -0.000899 | -0.001540 |
| ppopt168_second_rollback__seg=price_sample__hthr=0p0__rb=0p5__cap=0p005 | PP-OPT168 | pp166_second_stage_rollback | 0.269996 | 0.807231 | -0.001399 | -0.000899 | -0.001540 |
| ppopt168_second_rollback__seg=price_sample__hthr=0p0__rb=0p25__cap=0p003 | PP-OPT168 | pp166_second_stage_rollback | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt168_second_rollback__seg=price_sample__hthr=0p0__rb=0p25__cap=0p005 | PP-OPT168 | pp166_second_stage_rollback | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt167_tail_p95_blend__source=pp164_p95_block__tail=0p65__s=0p65__cap=0p003 | PP-OPT167 | pp166_tail_only_p95_blend | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt167_tail_p95_blend__source=pp164_p95_block__tail=0p65__s=0p65__cap=0p005 | PP-OPT167 | pp166_tail_only_p95_blend | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt168_second_rollback__seg=price_sample__hthr=0p05__rb=0p75__cap=0p003 | PP-OPT168 | pp166_second_stage_rollback | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt168_second_rollback__seg=price_sample__hthr=0p05__rb=0p75__cap=0p005 | PP-OPT168 | pp166_second_stage_rollback | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt167_tail_p95_blend__source=pp164_p95_block__tail=0p65__s=0p45__cap=0p003 | PP-OPT167 | pp166_tail_only_p95_blend | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt167_tail_p95_blend__source=pp164_p95_block__tail=0p65__s=0p45__cap=0p005 | PP-OPT167 | pp166_tail_only_p95_blend | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt168_second_rollback__seg=price_sample__hthr=0p05__rb=0p5__cap=0p003 | PP-OPT168 | pp166_second_stage_rollback | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt168_second_rollback__seg=price_sample__hthr=0p05__rb=0p5__cap=0p005 | PP-OPT168 | pp166_second_stage_rollback | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt167_tail_p95_blend__source=pp164_p95_block__tail=0p65__s=0p25__cap=0p003 | PP-OPT167 | pp166_tail_only_p95_blend | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt167_tail_p95_blend__source=pp164_p95_block__tail=0p65__s=0p25__cap=0p005 | PP-OPT167 | pp166_tail_only_p95_blend | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt168_second_rollback__seg=price_sample__hthr=0p05__rb=0p25__cap=0p003 | PP-OPT168 | pp166_second_stage_rollback | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt168_second_rollback__seg=price_sample__hthr=0p05__rb=0p25__cap=0p005 | PP-OPT168 | pp166_second_stage_rollback | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt168_second_rollback__seg=price_conf__hthr=0p05__rb=0p25__cap=0p003 | PP-OPT168 | pp166_second_stage_rollback | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt168_second_rollback__seg=price_conf__hthr=0p05__rb=0p25__cap=0p005 | PP-OPT168 | pp166_second_stage_rollback | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt168_second_rollback__seg=price_conf__hthr=0p05__rb=0p5__cap=0p003 | PP-OPT168 | pp166_second_stage_rollback | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt168_second_rollback__seg=price_conf__hthr=0p05__rb=0p5__cap=0p005 | PP-OPT168 | pp166_second_stage_rollback | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt168_second_rollback__seg=price_conf__hthr=0p05__rb=0p75__cap=0p003 | PP-OPT168 | pp166_second_stage_rollback | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt168_second_rollback__seg=price_conf__hthr=0p05__rb=0p75__cap=0p005 | PP-OPT168 | pp166_second_stage_rollback | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt169_segment_router__source=pp161_p95_guard__seg=price_conf__thr=0p02__s=0p5__cap=0p004 | PP-OPT169 | segment_p95_candidate_router | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt169_segment_router__source=pp161_p95_guard__seg=price_conf__thr=0p02__s=0p5__cap=0p006 | PP-OPT169 | segment_p95_candidate_router | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt169_segment_router__source=pp161_p95_guard__seg=price_conf__thr=0p02__s=0p8__cap=0p004 | PP-OPT169 | segment_p95_candidate_router | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt169_segment_router__source=pp161_p95_guard__seg=price_conf__thr=0p02__s=0p8__cap=0p006 | PP-OPT169 | segment_p95_candidate_router | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt169_segment_router__source=pp161_p95_guard__seg=price_qwidth__thr=0p02__s=0p5__cap=0p004 | PP-OPT169 | segment_p95_candidate_router | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt169_segment_router__source=pp161_p95_guard__seg=price_qwidth__thr=0p02__s=0p5__cap=0p006 | PP-OPT169 | segment_p95_candidate_router | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt169_segment_router__source=pp161_p95_guard__seg=price_qwidth__thr=0p02__s=0p8__cap=0p004 | PP-OPT169 | segment_p95_candidate_router | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt169_segment_router__source=pp161_p95_guard__seg=price_qwidth__thr=0p02__s=0p8__cap=0p006 | PP-OPT169 | segment_p95_candidate_router | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt169_segment_router__source=pp162_p95_gate__seg=price_conf__thr=0p02__s=0p5__cap=0p004 | PP-OPT169 | segment_p95_candidate_router | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt169_segment_router__source=pp162_p95_gate__seg=price_conf__thr=0p02__s=0p5__cap=0p006 | PP-OPT169 | segment_p95_candidate_router | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt169_segment_router__source=pp162_p95_gate__seg=price_conf__thr=0p02__s=0p8__cap=0p004 | PP-OPT169 | segment_p95_candidate_router | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt169_segment_router__source=pp162_p95_gate__seg=price_conf__thr=0p02__s=0p8__cap=0p006 | PP-OPT169 | segment_p95_candidate_router | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt169_segment_router__source=pp162_p95_gate__seg=price_qwidth__thr=0p02__s=0p5__cap=0p004 | PP-OPT169 | segment_p95_candidate_router | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt169_segment_router__source=pp162_p95_gate__seg=price_qwidth__thr=0p02__s=0p5__cap=0p006 | PP-OPT169 | segment_p95_candidate_router | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt169_segment_router__source=pp162_p95_gate__seg=price_qwidth__thr=0p02__s=0p8__cap=0p004 | PP-OPT169 | segment_p95_candidate_router | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt169_segment_router__source=pp162_p95_gate__seg=price_qwidth__thr=0p02__s=0p8__cap=0p006 | PP-OPT169 | segment_p95_candidate_router | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt169_segment_router__source=pp162_p95_gate__seg=price_qwidth__thr=m0p04__s=0p5__cap=0p004 | PP-OPT169 | segment_p95_candidate_router | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt169_segment_router__source=pp162_p95_gate__seg=price_qwidth__thr=m0p04__s=0p5__cap=0p006 | PP-OPT169 | segment_p95_candidate_router | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt169_segment_router__source=pp162_p95_gate__seg=price_qwidth__thr=m0p04__s=0p8__cap=0p004 | PP-OPT169 | segment_p95_candidate_router | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt169_segment_router__source=pp162_p95_gate__seg=price_qwidth__thr=m0p04__s=0p8__cap=0p006 | PP-OPT169 | segment_p95_candidate_router | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt169_segment_router__source=pp164_p95_block__seg=price_conf__thr=0p02__s=0p5__cap=0p004 | PP-OPT169 | segment_p95_candidate_router | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt169_segment_router__source=pp164_p95_block__seg=price_conf__thr=0p02__s=0p5__cap=0p006 | PP-OPT169 | segment_p95_candidate_router | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt169_segment_router__source=pp164_p95_block__seg=price_conf__thr=0p02__s=0p8__cap=0p004 | PP-OPT169 | segment_p95_candidate_router | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt169_segment_router__source=pp164_p95_block__seg=price_conf__thr=0p02__s=0p8__cap=0p006 | PP-OPT169 | segment_p95_candidate_router | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt169_segment_router__source=pp164_p95_block__seg=price_qwidth__thr=0p02__s=0p5__cap=0p004 | PP-OPT169 | segment_p95_candidate_router | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt169_segment_router__source=pp164_p95_block__seg=price_qwidth__thr=0p02__s=0p5__cap=0p006 | PP-OPT169 | segment_p95_candidate_router | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |
| ppopt169_segment_router__source=pp164_p95_block__seg=price_qwidth__thr=0p02__s=0p8__cap=0p004 | PP-OPT169 | segment_p95_candidate_router | 0.269997 | 0.807231 | -0.001398 | -0.000899 | -0.001540 |

## 선택 후보 반복 안정성
| candidate_label | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_vs_pp64_MAPE | fixed_test_delta_vs_pp64_p95_APE | avg_pp64_MAPE_win_rate | avg_pp64_p95_win_rate | replacement_score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| candidate_ppopt169_segment_router__source_pp162_p95_gate__seg_price_conf__thr_m0p04__s_0p5__cap_0p004__dff857b316 | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.947115 | 0.605449 | -0.018451 |
| candidate_ppopt169_segment_router__source_pp162_p95_gate__seg_price_conf__thr_m0p04__s_0p5__cap_0p006__3e2b8ef609 | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.947115 | 0.605449 | -0.018451 |
| pp172_operational_pp166_tail_calibration_challenger | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.947115 | 0.605449 | -0.018451 |
| candidate_ppopt169_segment_router__source_pp162_p95_gate__seg_price_conf__thr_m0p04__s_0p8__cap_0p004__ce1e236fa4 | 0.269998 | 0.807231 | -0.000566 | -0.000268 | 0.947115 | 0.605449 | -0.018451 |
| candidate_ppopt169_segment_router__source_pp162_p95_gate__seg_price_conf__thr_m0p04__s_0p8__cap_0p006__1f3545203c | 0.269998 | 0.807231 | -0.000566 | -0.000268 | 0.947115 | 0.605449 | -0.018451 |
| candidate_ppopt168_second_rollback__seg_price_qwidth__hthr_0p0__rb_0p75__cap_0p003__94ccd3683f | 0.270015 | 0.807231 | -0.000549 | -0.000268 | 0.947436 | 0.605449 | -0.018447 |
| candidate_ppopt168_second_rollback__seg_price_qwidth__hthr_0p0__rb_0p75__cap_0p005__4b95565009 | 0.270015 | 0.807231 | -0.000549 | -0.000268 | 0.947436 | 0.605449 | -0.018447 |
| candidate_ppopt168_second_rollback__seg_price_qwidth__hthr_0p05__rb_0p5__cap_0p003__cc509c7f42 | 0.270002 | 0.807231 | -0.000562 | -0.000268 | 0.947115 | 0.605449 | -0.018446 |
| candidate_ppopt168_second_rollback__seg_price_qwidth__hthr_0p05__rb_0p5__cap_0p005__76f9c2a203 | 0.270002 | 0.807231 | -0.000562 | -0.000268 | 0.947115 | 0.605449 | -0.018446 |
| candidate_ppopt169_segment_router__source_pp161_p95_guard__seg_price_qwidth__thr_m0p04__s_0p8__cap_0p0__68084eac1c | 0.269995 | 0.807231 | -0.000569 | -0.000268 | 0.946795 | 0.600962 | -0.018441 |
| candidate_ppopt169_segment_router__source_pp161_p95_guard__seg_price_qwidth__thr_m0p04__s_0p8__cap_0p0__6e5ae52381 | 0.269995 | 0.807231 | -0.000569 | -0.000268 | 0.946795 | 0.600962 | -0.018441 |
| candidate_ppopt169_segment_router__source_pp161_p95_guard__seg_price_conf__thr_m0p04__s_0p8__cap_0p004__5bc98744d4 | 0.269995 | 0.807231 | -0.000569 | -0.000268 | 0.946795 | 0.600962 | -0.018441 |
| candidate_ppopt169_segment_router__source_pp161_p95_guard__seg_price_conf__thr_m0p04__s_0p8__cap_0p006__90261825c1 | 0.269995 | 0.807231 | -0.000569 | -0.000268 | 0.946795 | 0.600962 | -0.018441 |
| candidate_ppopt169_segment_router__source_pp164_p95_block__seg_price_qwidth__thr_m0p04__s_0p8__cap_0p0__daab709199 | 0.269995 | 0.807231 | -0.000569 | -0.000268 | 0.946795 | 0.600962 | -0.018441 |
| candidate_ppopt169_segment_router__source_pp164_p95_block__seg_price_qwidth__thr_m0p04__s_0p8__cap_0p0__de8c9c20c5 | 0.269995 | 0.807231 | -0.000569 | -0.000268 | 0.946795 | 0.600962 | -0.018441 |
| candidate_ppopt169_segment_router__source_pp161_p95_guard__seg_price_qwidth__thr_m0p04__s_0p5__cap_0p0__56f079929c | 0.269996 | 0.807231 | -0.000569 | -0.000268 | 0.946795 | 0.600962 | -0.018440 |
| candidate_ppopt169_segment_router__source_pp161_p95_guard__seg_price_qwidth__thr_m0p04__s_0p5__cap_0p0__854c732273 | 0.269996 | 0.807231 | -0.000569 | -0.000268 | 0.946795 | 0.600962 | -0.018440 |
| candidate_ppopt168_second_rollback__seg_price_sample__hthr_0p0__rb_0p75__cap_0p003__6d36c8123f | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.601923 | -0.018440 |
| candidate_ppopt168_second_rollback__seg_price_sample__hthr_0p0__rb_0p75__cap_0p005__50b3996666 | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.601923 | -0.018440 |
| candidate_ppopt169_segment_router__source_pp161_p95_guard__seg_price_conf__thr_m0p04__s_0p5__cap_0p004__f9d3d80e26 | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.600962 | -0.018440 |
| candidate_ppopt169_segment_router__source_pp161_p95_guard__seg_price_conf__thr_m0p04__s_0p5__cap_0p006__82e45d367c | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.600962 | -0.018440 |
| candidate_ppopt167_tail_p95_blend__source_pp161_p95_guard__tail_0p45__s_0p65__cap_0p003__48a7a51f98 | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.600962 | -0.018440 |
| candidate_ppopt167_tail_p95_blend__source_pp161_p95_guard__tail_0p45__s_0p65__cap_0p005__db5a061661 | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.600962 | -0.018440 |
| candidate_ppopt168_second_rollback__seg_price_conf__hthr_0p0__rb_0p75__cap_0p003__ebe17711de | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.601923 | -0.018440 |
| candidate_ppopt168_second_rollback__seg_price_conf__hthr_0p0__rb_0p75__cap_0p005__7ef609019e | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.601923 | -0.018440 |
| candidate_ppopt169_segment_router__source_pp164_p95_block__seg_price_qwidth__thr_m0p04__s_0p5__cap_0p0__9e33cc25a6 | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.600962 | -0.018440 |
| candidate_ppopt169_segment_router__source_pp164_p95_block__seg_price_qwidth__thr_m0p04__s_0p5__cap_0p0__c72a7a71c0 | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.600962 | -0.018440 |
| candidate_ppopt171_consensus__left_pp161_p95_guard__right_pp164_p95_block__thr_m0p04__s_0p55__cap_0p00__46bee4f8ad | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.600962 | -0.018440 |
| candidate_ppopt171_consensus__left_pp161_p95_guard__right_pp164_p95_block__thr_m0p04__s_0p55__cap_0p00__64ba9c11e0 | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.600962 | -0.018440 |
| candidate_ppopt170_dynamic_cap__source_pp161_p95_guard__thr_m0p02__s_0p7__basecap_0p004__a05a34f1d1 | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.600962 | -0.018440 |
| candidate_ppopt170_dynamic_cap__source_pp161_p95_guard__thr_m0p02__s_0p7__basecap_0p006__4e95b1f0de | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.600962 | -0.018440 |
| candidate_ppopt167_tail_p95_blend__source_pp164_p95_block__tail_0p45__s_0p65__cap_0p003__4d65d79091 | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.600962 | -0.018440 |
| candidate_ppopt167_tail_p95_blend__source_pp164_p95_block__tail_0p45__s_0p65__cap_0p005__cc37962eac | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.600962 | -0.018440 |
| candidate_ppopt168_second_rollback__seg_price_sample__hthr_0p0__rb_0p5__cap_0p003__693d77086b | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.601923 | -0.018440 |
| candidate_ppopt168_second_rollback__seg_price_sample__hthr_0p0__rb_0p5__cap_0p005__8e8a7c7ff9 | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.601923 | -0.018440 |
| candidate_ppopt167_tail_p95_blend__source_pp161_p95_guard__tail_0p45__s_0p45__cap_0p003__63c4a6b3b0 | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.600962 | -0.018440 |
| candidate_ppopt167_tail_p95_blend__source_pp161_p95_guard__tail_0p45__s_0p45__cap_0p005__2fcc70817c | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.600962 | -0.018440 |
| candidate_ppopt168_second_rollback__seg_price_conf__hthr_0p0__rb_0p5__cap_0p003__b9c807f639 | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.601923 | -0.018440 |
| candidate_ppopt168_second_rollback__seg_price_conf__hthr_0p0__rb_0p5__cap_0p005__38619f7684 | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.601923 | -0.018440 |
| candidate_ppopt170_dynamic_cap__source_pp164_p95_block__thr_m0p02__s_0p7__basecap_0p004__3fdf07b57a | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.600962 | -0.018440 |
| candidate_ppopt170_dynamic_cap__source_pp164_p95_block__thr_m0p02__s_0p7__basecap_0p006__9ba2f0c7be | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.600962 | -0.018440 |
| candidate_ppopt171_consensus__left_pp161_p95_guard__right_pp164_p95_block__thr_m0p04__s_0p35__cap_0p00__64cb1d751b | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.600962 | -0.018439 |
| candidate_ppopt171_consensus__left_pp161_p95_guard__right_pp164_p95_block__thr_m0p04__s_0p35__cap_0p00__b0f461c786 | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.600962 | -0.018439 |
| candidate_ppopt170_dynamic_cap__source_pp161_p95_guard__thr_m0p02__s_0p45__basecap_0p004__276384632b | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.600962 | -0.018439 |
| candidate_ppopt170_dynamic_cap__source_pp161_p95_guard__thr_m0p02__s_0p45__basecap_0p006__41288dbf32 | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.600962 | -0.018439 |
| candidate_ppopt167_tail_p95_blend__source_pp164_p95_block__tail_0p45__s_0p45__cap_0p003__cd1eb21e94 | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.600962 | -0.018439 |
| candidate_ppopt167_tail_p95_blend__source_pp164_p95_block__tail_0p45__s_0p45__cap_0p005__7578bd97d9 | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.600962 | -0.018439 |
| candidate_ppopt167_tail_p95_blend__source_pp161_p95_guard__tail_0p55__s_0p65__cap_0p003__5eea60648d | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.600962 | -0.018439 |
| candidate_ppopt167_tail_p95_blend__source_pp161_p95_guard__tail_0p55__s_0p65__cap_0p005__6daa7199b3 | 0.269996 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.600962 | -0.018439 |
| candidate_ppopt167_tail_p95_blend__source_pp164_p95_block__tail_0p55__s_0p65__cap_0p003__97a3b078ce | 0.269997 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.600962 | -0.018439 |
| candidate_ppopt167_tail_p95_blend__source_pp164_p95_block__tail_0p55__s_0p65__cap_0p005__67eba79318 | 0.269997 | 0.807231 | -0.000568 | -0.000268 | 0.946795 | 0.600962 | -0.018439 |
| candidate_ppopt167_tail_p95_blend__source_pp161_p95_guard__tail_0p45__s_0p25__cap_0p003__79c8f624be | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.946795 | 0.600962 | -0.018439 |
| candidate_ppopt167_tail_p95_blend__source_pp161_p95_guard__tail_0p45__s_0p25__cap_0p005__1088f6e345 | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.946795 | 0.600962 | -0.018439 |
| candidate_ppopt170_dynamic_cap__source_pp164_p95_block__thr_m0p02__s_0p45__basecap_0p004__c5625fdb51 | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.946795 | 0.600962 | -0.018439 |
| candidate_ppopt170_dynamic_cap__source_pp164_p95_block__thr_m0p02__s_0p45__basecap_0p006__581f3d6bab | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.946795 | 0.600962 | -0.018439 |
| candidate_ppopt168_second_rollback__seg_price_sample__hthr_0p0__rb_0p25__cap_0p003__8391cb68ca | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.946795 | 0.601923 | -0.018439 |
| candidate_ppopt168_second_rollback__seg_price_sample__hthr_0p0__rb_0p25__cap_0p005__e8fc34fa3b | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.946795 | 0.601923 | -0.018439 |
| candidate_ppopt168_second_rollback__seg_price_conf__hthr_0p0__rb_0p25__cap_0p003__c73387b252 | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.946795 | 0.601923 | -0.018439 |
| candidate_ppopt168_second_rollback__seg_price_conf__hthr_0p0__rb_0p25__cap_0p005__121fe829c2 | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.946795 | 0.601923 | -0.018439 |
| candidate_ppopt167_tail_p95_blend__source_pp164_p95_block__tail_0p65__s_0p65__cap_0p003__95110ba00a | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.946795 | 0.600962 | -0.018439 |
| candidate_ppopt167_tail_p95_blend__source_pp164_p95_block__tail_0p65__s_0p65__cap_0p005__462916d948 | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.946795 | 0.600962 | -0.018439 |
| candidate_ppopt168_second_rollback__seg_price_sample__hthr_0p05__rb_0p75__cap_0p003__70aa38e84a | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.946795 | 0.601923 | -0.018439 |
| candidate_ppopt168_second_rollback__seg_price_sample__hthr_0p05__rb_0p75__cap_0p005__d86ce332e4 | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.946795 | 0.601923 | -0.018439 |
| candidate_ppopt167_tail_p95_blend__source_pp164_p95_block__tail_0p65__s_0p45__cap_0p003__54c304f1ec | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.946795 | 0.600962 | -0.018439 |
| candidate_ppopt167_tail_p95_blend__source_pp164_p95_block__tail_0p65__s_0p45__cap_0p005__bfc4957d75 | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.946795 | 0.600962 | -0.018439 |
| candidate_ppopt168_second_rollback__seg_price_sample__hthr_0p05__rb_0p5__cap_0p003__8b26fd78a6 | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.946795 | 0.601923 | -0.018439 |
| candidate_ppopt168_second_rollback__seg_price_sample__hthr_0p05__rb_0p5__cap_0p005__de9fbf51c7 | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.946795 | 0.601923 | -0.018439 |
| candidate_ppopt167_tail_p95_blend__source_pp164_p95_block__tail_0p65__s_0p25__cap_0p003__cbe953fac9 | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.946795 | 0.600962 | -0.018439 |
| candidate_ppopt167_tail_p95_blend__source_pp164_p95_block__tail_0p65__s_0p25__cap_0p005__f9784b433c | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.946795 | 0.600962 | -0.018439 |
| candidate_ppopt168_second_rollback__seg_price_sample__hthr_0p05__rb_0p25__cap_0p003__2f97c71f5f | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.946795 | 0.601923 | -0.018439 |
| candidate_ppopt168_second_rollback__seg_price_sample__hthr_0p05__rb_0p25__cap_0p005__596fb600f4 | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.946795 | 0.601923 | -0.018439 |
| candidate_ppopt167_tail_p95_blend__source_pp162_p95_gate__tail_0p55__s_0p65__cap_0p003__9eb2bbab61 | 0.269997 | 0.807229 | -0.000567 | -0.000270 | 0.946795 | 0.601923 | -0.018439 |
| candidate_ppopt167_tail_p95_blend__source_pp162_p95_gate__tail_0p55__s_0p65__cap_0p005__a8fcc3f4d5 | 0.269997 | 0.807229 | -0.000567 | -0.000270 | 0.946795 | 0.601923 | -0.018439 |
| candidate_ppopt167_tail_p95_blend__source_pp162_p95_gate__tail_0p55__s_0p45__cap_0p003__afce50ab79 | 0.269997 | 0.807230 | -0.000567 | -0.000269 | 0.946795 | 0.601923 | -0.018439 |
| candidate_ppopt167_tail_p95_blend__source_pp162_p95_gate__tail_0p55__s_0p45__cap_0p005__b9df6ab83f | 0.269997 | 0.807230 | -0.000567 | -0.000269 | 0.946795 | 0.601923 | -0.018439 |
| candidate_ppopt167_tail_p95_blend__source_pp162_p95_gate__tail_0p55__s_0p25__cap_0p003__9cbd5262f2 | 0.269997 | 0.807230 | -0.000567 | -0.000269 | 0.946795 | 0.601923 | -0.018439 |
| candidate_ppopt167_tail_p95_blend__source_pp162_p95_gate__tail_0p55__s_0p25__cap_0p005__29896cc15c | 0.269997 | 0.807230 | -0.000567 | -0.000269 | 0.946795 | 0.601923 | -0.018439 |
| candidate_ppopt168_second_rollback__seg_price_conf__hthr_0p05__rb_0p25__cap_0p003__cb9a5ead15 | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.946795 | 0.601923 | -0.018439 |
| candidate_ppopt168_second_rollback__seg_price_conf__hthr_0p05__rb_0p25__cap_0p005__276c0c096d | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.946795 | 0.601923 | -0.018439 |
| candidate_ppopt168_second_rollback__seg_price_conf__hthr_0p05__rb_0p5__cap_0p003__b92d403db6 | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.946795 | 0.601923 | -0.018439 |
| pp166_operational_reference | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.946795 | 0.601923 | -0.018439 |
| candidate_ppopt167_tail_p95_blend__source_pp162_p95_gate__tail_0p45__s_0p25__cap_0p003__6cc04c98ad | 0.269997 | 0.807227 | -0.000567 | -0.000271 | 0.946795 | 0.601923 | -0.018439 |
| candidate_ppopt167_tail_p95_blend__source_pp162_p95_gate__tail_0p45__s_0p25__cap_0p005__503ac19f6b | 0.269997 | 0.807227 | -0.000567 | -0.000271 | 0.946795 | 0.601923 | -0.018439 |
| candidate_ppopt167_tail_p95_blend__source_pp162_p95_gate__tail_0p45__s_0p45__cap_0p003__dc2fbaed1e | 0.269997 | 0.807225 | -0.000567 | -0.000274 | 0.946795 | 0.601923 | -0.018439 |
| candidate_ppopt167_tail_p95_blend__source_pp162_p95_gate__tail_0p45__s_0p45__cap_0p005__2e503e11ed | 0.269997 | 0.807225 | -0.000567 | -0.000274 | 0.946795 | 0.601923 | -0.018439 |
| candidate_ppopt167_tail_p95_blend__source_pp162_p95_gate__tail_0p45__s_0p65__cap_0p003__8647b86f77 | 0.269997 | 0.807222 | -0.000567 | -0.000277 | 0.946795 | 0.601923 | -0.018439 |
| candidate_ppopt167_tail_p95_blend__source_pp162_p95_gate__tail_0p45__s_0p65__cap_0p005__99e6607d27 | 0.269997 | 0.807222 | -0.000567 | -0.000277 | 0.946795 | 0.601923 | -0.018439 |
| candidate_ppopt168_second_rollback__seg_price_qwidth__hthr_0p05__rb_0p25__cap_0p003__1f77e1d48e | 0.270000 | 0.807231 | -0.000564 | -0.000268 | 0.946795 | 0.605449 | -0.018436 |
| candidate_ppopt168_second_rollback__seg_price_qwidth__hthr_0p05__rb_0p25__cap_0p005__668364d34e | 0.270000 | 0.807231 | -0.000564 | -0.000268 | 0.946795 | 0.605449 | -0.018436 |
| candidate_ppopt167_tail_p95_blend__source_pp148_p95__tail_0p45__s_0p25__cap_0p003__9786f9f5ef | 0.270001 | 0.807231 | -0.000563 | -0.000268 | 0.946795 | 0.605449 | -0.018435 |
| candidate_ppopt167_tail_p95_blend__source_pp148_p95__tail_0p45__s_0p25__cap_0p005__303ba8150b | 0.270001 | 0.807231 | -0.000563 | -0.000268 | 0.946795 | 0.605449 | -0.018435 |
| candidate_ppopt168_second_rollback__seg_price_qwidth__hthr_0p0__rb_0p25__cap_0p003__4a4402ba12 | 0.270003 | 0.807231 | -0.000561 | -0.000268 | 0.946795 | 0.605449 | -0.018433 |
| candidate_ppopt168_second_rollback__seg_price_qwidth__hthr_0p0__rb_0p25__cap_0p005__5ee56fc1d4 | 0.270003 | 0.807231 | -0.000561 | -0.000268 | 0.946795 | 0.605449 | -0.018433 |
| candidate_ppopt167_tail_p95_blend__source_pp148_p95__tail_0p45__s_0p45__cap_0p003__ddfd148a4e | 0.270004 | 0.807231 | -0.000560 | -0.000268 | 0.946795 | 0.605449 | -0.018432 |
| candidate_ppopt167_tail_p95_blend__source_pp148_p95__tail_0p45__s_0p45__cap_0p005__7facd2b373 | 0.270004 | 0.807231 | -0.000560 | -0.000268 | 0.946795 | 0.605449 | -0.018432 |
| candidate_ppopt168_second_rollback__seg_price_qwidth__hthr_0p05__rb_0p75__cap_0p003__52d51ce735 | 0.270005 | 0.807231 | -0.000559 | -0.000268 | 0.946795 | 0.605449 | -0.018431 |
| candidate_ppopt168_second_rollback__seg_price_qwidth__hthr_0p05__rb_0p75__cap_0p005__dfd2d4f919 | 0.270005 | 0.807231 | -0.000559 | -0.000268 | 0.946795 | 0.605449 | -0.018431 |
| candidate_ppopt168_second_rollback__seg_price_qwidth__hthr_0p0__rb_0p5__cap_0p003__af72007ac8 | 0.270009 | 0.807231 | -0.000555 | -0.000268 | 0.946795 | 0.605449 | -0.018427 |
| candidate_ppopt168_second_rollback__seg_price_qwidth__hthr_0p0__rb_0p5__cap_0p005__ddde03d10d | 0.270009 | 0.807231 | -0.000555 | -0.000268 | 0.946795 | 0.605449 | -0.018427 |
| candidate_ppopt167_tail_p95_blend__source_pp148_p95__tail_0p45__s_0p65__cap_0p003__218ac53dde | 0.270007 | 0.807231 | -0.000557 | -0.000268 | 0.946474 | 0.605449 | -0.018416 |
| candidate_ppopt167_tail_p95_blend__source_pp148_p95__tail_0p45__s_0p65__cap_0p005__bc5c2f7754 | 0.270007 | 0.807231 | -0.000557 | -0.000268 | 0.946474 | 0.605449 | -0.018416 |
| pp148_operational_reference | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| pp126_operational_reference | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| pp161_p95_guard_reference | 0.269984 | 0.806592 | -0.000580 | -0.000907 | 0.915705 | 0.571795 | -0.017208 |
| pp164_p95_block_reference | 0.270004 | 0.806592 | -0.000560 | -0.000907 | 0.912821 | 0.572115 | -0.017073 |
| pp162_p95_gate_reference | 0.270056 | 0.806665 | -0.000508 | -0.000834 | 0.913782 | 0.597115 | -0.017059 |
| pp70_refinement_candidate | 0.270561 | 0.807490 | -0.000003 | -0.000009 | 0.786859 | 0.398077 | -0.011477 |
| pp148_p95_reference | 0.270269 | 0.805949 | -0.000295 | -0.001549 | 0.598397 | 0.500962 | -0.004079 |
| pp166_p95_reference | 0.270269 | 0.805949 | -0.000295 | -0.001549 | 0.598397 | 0.500962 | -0.004079 |
| pp172_p95_pp166_tail_calibration_challenger | 0.270269 | 0.805949 | -0.000295 | -0.001549 | 0.598397 | 0.500962 | -0.004079 |
| pp64_current_best | 0.270564 | 0.807499 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.020000 |
| incumbent_pp7 | 0.271395 | 0.808130 | 0.000831 | 0.000631 | 0.002244 | 0.450641 | 0.022238 |
| hcoef_stable_source | 0.272989 | 0.806366 | 0.002425 | -0.001133 | 0.002244 | 0.403526 | 0.025195 |
| candidate_current_70_30__6e83864d8c | 0.274799 | 0.833074 | 0.004235 | 0.025575 | 0.000962 | 0.254167 | 0.048393 |

## 실행 설정
```json
{
  "experiment_id": "PP-OPT167-172",
  "experiment_slug": "PP-OPT167_172_warm_pp166_second_stage_tail_calibration",
  "created_at": "2026-06-10T09:41:20",
  "base_candidate": "hcoef_stable",
  "previous_experiment": "experiments/track6/PP-OPT161_166_warm_pp157_negative_gate_rollback",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 219,
  "prediction_rows": 246594,
  "support_candidates": {
    "pp166_operational": "ppopt166_operational_pp157_negative_gate_challenger__source=ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap008__seg_price_conf__hw_1p2__thr_0p0__s_1p0__cap_0p006",
    "pp166_p95": "ppopt166_p95_pp157_negative_gate_challenger__source=reference_pp148_p95",
    "pp148_operational": "reference_pp148_operational",
    "pp148_p95": "reference_pp148_p95",
    "pp161_p95_guard": "ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s100_cap008__hthr=0p3__w=0p14__rb=1p0__s=1p0__cap=0p006",
    "pp162_p95_gate": "ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap008__thr=0p18__w=0p1__hpen=0p5__s=1p0__cap=0p006",
    "pp164_p95_block": "ppopt164_hard_block__target=pp157_price_qwidth_q084_s100_cap008__hthr=0p45__gthr=0p12__s=1p0__cap=0p006"
  },
  "selection_decision": {
    "operational_label": "candidate_ppopt169_segment_router__source_pp162_p95_gate__seg_price_conf__thr_m0p04__s_0p5__cap_0p004__dff857b316",
    "operational_candidate": "ppopt169_segment_router__source=pp162_p95_gate__seg=price_conf__thr=m0p04__s=0p5__cap=0p004",
    "operational_fixed_test_MAPE": 0.2699974146611506,
    "operational_fixed_test_p95_APE": 0.8072309115386983,
    "operational_delta_vs_pp64_MAPE": -0.0005666272545097328,
    "operational_delta_vs_pp64_p95_APE": -0.00026794076741154527,
    "operational_delta_vs_pp126_MAPE": -0.00011698208870120075,
    "operational_delta_vs_pp126_p95_APE": -0.000259149359149613,
    "operational_delta_vs_pp148_MAPE": -0.00014257371142878394,
    "operational_delta_vs_pp148_p95_APE": 0.0,
    "operational_delta_vs_pp166_MAPE": 4.289959120162834e-07,
    "operational_delta_vs_pp166_p95_APE": 0.0,
    "operational_avg_pp64_MAPE_win_rate": 0.9471153846153846,
    "operational_avg_pp64_p95_win_rate": 0.6054487179487179,
    "operational_replacement_score": -0.018451242639125117,
    "p95_label": "pp148_p95_reference",
    "p95_candidate": "reference_pp148_p95",
    "p95_fixed_test_MAPE": 0.27026892590910795,
    "p95_fixed_test_p95_APE": 0.8059493758221674,
    "p95_delta_vs_pp64_MAPE": -0.00029511600655240944,
    "p95_delta_vs_pp64_p95_APE": -0.0015494764839424358,
    "p95_delta_vs_pp126_MAPE": 0.00015452915925612265,
    "p95_delta_vs_pp126_p95_APE": -0.0015406850756805035,
    "p95_delta_vs_pp148_MAPE": 0.00012893753652853945,
    "p95_delta_vs_pp148_p95_APE": -0.0012815357165308905,
    "p95_delta_vs_pp166_MAPE": 0.0002719402438693397,
    "p95_delta_vs_pp166_p95_APE": -0.0012815357165308905,
    "p95_avg_pp64_MAPE_win_rate": 0.5983974358974359,
    "p95_avg_pp64_p95_win_rate": 0.5009615384615385,
    "p95_replacement_score": -0.0040792899192624915,
    "operational_protocol_candidate": "ppopt172_operational_pp166_tail_calibration_challenger__source=ppopt169_segment_router__source_pp162_p95_gate__seg_price_conf__thr_m0p04__s_0p5__cap_0p004",
    "p95_protocol_candidate": "ppopt172_p95_pp166_tail_calibration_challenger__source=reference_pp148_p95"
  },
  "items": [
    {
      "item_id": "PP-OPT167",
      "priority": "1",
      "title": "PP166 tail-only p95 blend",
      "description": "PP166을 기준값으로 두고 p95가 낮은 후보의 이동분을 tail-risk row에만 약하게 얹는다."
    },
    {
      "item_id": "PP-OPT168",
      "priority": "2",
      "title": "PP166 second-stage rollback",
      "description": "validation에서 PP166이 PP148보다 손해를 보인 구간은 PP148 쪽으로 일부 되돌린다."
    },
    {
      "item_id": "PP-OPT169",
      "priority": "3",
      "title": "segment p95 candidate router",
      "description": "가격대/불확실성 구간별로 p95 후보가 PP166보다 우세했던 곳에만 후보 이동분을 적용한다."
    },
    {
      "item_id": "PP-OPT170",
      "priority": "4",
      "title": "tail-aware dynamic cap",
      "description": "tail-risk가 큰 row는 보정 cap을 조금 열고, 손해 가능성이 큰 row는 cap을 줄인다."
    },
    {
      "item_id": "PP-OPT171",
      "priority": "5",
      "title": "consensus correction ensemble",
      "description": "여러 p95 후보가 같은 방향으로 움직일 때만 제한적으로 평균 보정을 적용한다."
    },
    {
      "item_id": "PP-OPT172",
      "priority": "6",
      "title": "final PP166 tail calibration decision",
      "description": "PP166과 신규 second-stage 후보를 fixed/repeated 기준으로 비교해 운영/p95 후보를 선택한다."
    }
  ],
  "sources": {
    "pp161_helper": "scripts/track6/run_pp_opt161_166_warm_pp157_negative_gate_rollback.py"
  }
}
```