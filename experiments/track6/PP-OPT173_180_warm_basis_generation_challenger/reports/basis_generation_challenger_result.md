# PP-OPT173~180 Warm basis-generation challenger 결과

- 작성일: 2026-06-10 10:04
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 목적: PP172 위의 미세 보정 대신 기준 로그가격 생성 자체를 바꾸는 후보 검증
- 결론: 운영 후보 fixed test MAPE 0.269933, p95 0.807326. PP172 대비 MAPE -0.000065, p95 +0.000095.

## 주요 후보 test 비교
| candidate | family | item_id | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt180_operational_basis_generation_challenger__source=ppopt174_direct_basis__source_stack_huber_weighted__thr_0p08__s_0p3__cap_0p004 | basis_generation_operational_selection | PP-OPT180 | 0.140975 | 0.269933 | 0.807326 | 0.397475 | -0.001462 | -0.000804 |
| ppopt166_operational_pp157_negative_gate_challenger__source=ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap008__seg_price_conf__hw_1p2__thr_0p0__s_1p0__cap_0p006 | reference_prior | REFERENCE | 0.139801 | 0.269997 | 0.807231 | 0.397516 | -0.001398 | -0.000899 |
| ppopt172_operational_pp166_tail_calibration_challenger__source=ppopt169_segment_router__source_pp162_p95_gate__seg_price_conf__thr_m0p04__s_0p5__cap_0p004 | reference_prior | REFERENCE | 0.139801 | 0.269997 | 0.807231 | 0.397516 | -0.001397 | -0.000899 |
| reference_pp126_operational | reference_prior | REFERENCE | 0.136320 | 0.270114 | 0.807490 | 0.397588 | -0.001280 | -0.000640 |
| reference_pp148_operational | reference_prior | REFERENCE | 0.139801 | 0.270140 | 0.807231 | 0.397525 | -0.001255 | -0.000899 |
| reference_pp148_p95 | reference_prior | REFERENCE | 0.141036 | 0.270269 | 0.805949 | 0.397421 | -0.001126 | -0.002181 |
| ppopt180_p95_basis_generation_challenger__source=reference_pp148_p95 | basis_generation_p95_selection | PP-OPT180 | 0.141036 | 0.270269 | 0.805949 | 0.397421 | -0.001126 | -0.002181 |
| reference_pp64_current_best | reference_prior | REFERENCE | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | p95_test_MAPE | p95_test_p95_APE | operational_pass_vs_incumbent | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | segment residual basis | 90 | 0.270171 | 0.806965 | 0.270577 | 0.805925 | False | segment_residual_basis | ppopt173_segment_residual_basis__seg=price_sample__shrink=8p0__s=0p85__cap=0p004 |
| 2 | direct model basis routing | 126 | 0.269749 | 0.807649 | 0.269915 | 0.807231 | False | direct_model_basis_routing | ppopt174_direct_basis__source=stack_huber_weighted__thr=m0p04__s=0p45__cap=0p007 |
| 7 | basis micro calibration | 24 | 0.270684 | 0.806693 | 0.270711 | 0.806514 | False | basis_micro_calibration | ppopt179_micro_basis_calibration__thr=0p03__bs=0p12__ss=0p2__cap=0p005 |
| 6 | basis family router | 40 | 0.269775 | 0.807649 | 0.269958 | 0.807231 | False | basis_family_router | ppopt178_family_router__family=huber__thr=m0p02__s=0p35__cap=0p007 |
| 4 | model consensus basis | 36 | 0.269992 | 0.807231 | 0.269982 | 0.807231 | False | model_consensus_basis | ppopt176_consensus_basis__group=lgb_cat_xgb__thr=0p02__s=0p18__cap=0p0035 |
| 3 | quantile basis with uncertainty guard | 54 | 0.269996 | 0.807231 | 0.269994 | 0.807231 | False | quantile_basis_uncertainty_guard | ppopt175_quantile_basis__source=huber__maxw=0p75__s=0p2__cap=0p006 |
| 8 | final basis-generation decision | 2 | 0.269933 | 0.807326 | 0.270269 | 0.805949 | False | basis_generation_operational_selection | ppopt180_operational_basis_generation_challenger__source=ppopt174_direct_basis__source_stack_huber_weighted__thr_0p08__s_0p3__cap_0p004 |
| 5 | basis-to-PP172 correction | 18 | 0.266550 | 0.815707 | 0.266472 | 0.815707 | False | basis_to_pp172_correction | ppopt177_basis_to_pp172__basis=huber_weighted__corr=0p75__cap=0p01 |

## 탐색 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt173_segment_residual_basis__seg=price_sample__shrink=8p0__s=0p85__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270171 | 0.806965 | -0.001224 | -0.001165 | -0.002465 |
| ppopt173_segment_residual_basis__seg=price_sample__shrink=18p0__s=0p85__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270182 | 0.806965 | -0.001213 | -0.001165 | -0.002433 |
| ppopt173_segment_residual_basis__seg=price_sample__shrink=8p0__s=0p6__cap=0p007 | PP-OPT173 | segment_residual_basis | 0.270528 | 0.806764 | -0.000867 | -0.001366 | -0.002337 |
| ppopt173_segment_residual_basis__seg=price_sample__shrink=18p0__s=0p6__cap=0p007 | PP-OPT173 | segment_residual_basis | 0.270538 | 0.806764 | -0.000857 | -0.001366 | -0.002322 |
| ppopt173_segment_residual_basis__seg=price_sample__shrink=35p0__s=0p85__cap=0p007 | PP-OPT173 | segment_residual_basis | 0.270510 | 0.806764 | -0.000885 | -0.001366 | -0.002303 |
| ppopt173_segment_residual_basis__seg=price_sample__shrink=35p0__s=0p85__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270205 | 0.806965 | -0.001190 | -0.001165 | -0.002297 |
| ppopt173_segment_residual_basis__seg=price_sample__shrink=8p0__s=0p85__cap=0p007 | PP-OPT173 | segment_residual_basis | 0.270470 | 0.806764 | -0.000925 | -0.001366 | -0.002297 |
| ppopt173_segment_residual_basis__seg=price_sample__shrink=18p0__s=0p85__cap=0p007 | PP-OPT173 | segment_residual_basis | 0.270485 | 0.806764 | -0.000910 | -0.001366 | -0.002284 |
| ppopt173_segment_residual_basis__seg=price_sample__shrink=35p0__s=0p6__cap=0p007 | PP-OPT173 | segment_residual_basis | 0.270564 | 0.806764 | -0.000830 | -0.001366 | -0.002241 |
| ppopt173_segment_residual_basis__seg=price_sample__shrink=8p0__s=0p6__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270225 | 0.806965 | -0.001170 | -0.001165 | -0.002212 |
| ppopt173_segment_residual_basis__seg=price_sample__shrink=18p0__s=0p6__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270236 | 0.806965 | -0.001159 | -0.001165 | -0.002134 |
| ppopt173_segment_residual_basis__seg=price_sample__shrink=8p0__s=0p35__cap=0p007 | PP-OPT173 | segment_residual_basis | 0.270585 | 0.806764 | -0.000810 | -0.001366 | -0.002117 |
| ppopt173_segment_residual_basis__seg=price_sample__shrink=18p0__s=0p35__cap=0p007 | PP-OPT173 | segment_residual_basis | 0.270593 | 0.806764 | -0.000802 | -0.001366 | -0.002061 |
| ppopt173_segment_residual_basis__seg=price_sample__shrink=35p0__s=0p6__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270251 | 0.806965 | -0.001144 | -0.001165 | -0.002034 |
| ppopt173_segment_residual_basis__seg=price_conf__shrink=8p0__s=0p85__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270636 | 0.806486 | -0.000759 | -0.001644 | -0.002019 |
| ppopt173_segment_residual_basis__seg=price_conf__shrink=18p0__s=0p85__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270621 | 0.806486 | -0.000774 | -0.001644 | -0.002016 |
| ppopt173_segment_residual_basis__seg=price_conf__shrink=35p0__s=0p85__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270601 | 0.806486 | -0.000794 | -0.001644 | -0.002014 |
| ppopt173_segment_residual_basis__seg=price_conf__shrink=8p0__s=0p6__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270583 | 0.806486 | -0.000812 | -0.001644 | -0.001998 |
| ppopt173_segment_residual_basis__seg=price_sample__shrink=35p0__s=0p35__cap=0p007 | PP-OPT173 | segment_residual_basis | 0.270574 | 0.806764 | -0.000821 | -0.001366 | -0.001991 |
| ppopt173_segment_residual_basis__seg=price_conf__shrink=18p0__s=0p6__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270573 | 0.806486 | -0.000822 | -0.001644 | -0.001971 |
| ppopt173_segment_residual_basis__seg=price_conf__shrink=35p0__s=0p6__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270567 | 0.806486 | -0.000828 | -0.001644 | -0.001932 |
| ppopt173_segment_residual_basis__seg=price_qwidth__shrink=8p0__s=0p85__cap=0p007 | PP-OPT173 | segment_residual_basis | 0.271156 | 0.807689 | -0.000239 | -0.000441 | -0.001915 |
| ppopt173_segment_residual_basis__seg=price_sample__shrink=8p0__s=0p35__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270283 | 0.806965 | -0.001112 | -0.001165 | -0.001912 |
| ppopt174_direct_basis__source=stack_huber_weighted__thr=m0p04__s=0p45__cap=0p007 | PP-OPT174 | direct_model_basis_routing | 0.269749 | 0.807649 | -0.001646 | -0.000481 | -0.001902 |
| ppopt179_micro_basis_calibration__thr=0p03__bs=0p12__ss=0p2__cap=0p005 | PP-OPT179 | basis_micro_calibration | 0.270684 | 0.806693 | -0.000711 | -0.001437 | -0.001890 |
| ppopt179_micro_basis_calibration__thr=0p03__bs=0p2__ss=0p2__cap=0p005 | PP-OPT179 | basis_micro_calibration | 0.270684 | 0.806693 | -0.000711 | -0.001437 | -0.001890 |
| ppopt179_micro_basis_calibration__thr=0p06__bs=0p12__ss=0p2__cap=0p005 | PP-OPT179 | basis_micro_calibration | 0.270684 | 0.806693 | -0.000711 | -0.001437 | -0.001890 |
| ppopt179_micro_basis_calibration__thr=0p06__bs=0p2__ss=0p2__cap=0p005 | PP-OPT179 | basis_micro_calibration | 0.270684 | 0.806693 | -0.000711 | -0.001437 | -0.001890 |
| ppopt179_micro_basis_calibration__thr=0p0__bs=0p12__ss=0p2__cap=0p005 | PP-OPT179 | basis_micro_calibration | 0.270684 | 0.806693 | -0.000711 | -0.001437 | -0.001890 |
| ppopt179_micro_basis_calibration__thr=0p0__bs=0p2__ss=0p2__cap=0p005 | PP-OPT179 | basis_micro_calibration | 0.270684 | 0.806693 | -0.000711 | -0.001437 | -0.001890 |
| ppopt173_segment_residual_basis__seg=price_conf__shrink=8p0__s=0p35__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270533 | 0.806510 | -0.000862 | -0.001620 | -0.001882 |
| ppopt173_segment_residual_basis__seg=price_qwidth__shrink=18p0__s=0p85__cap=0p007 | PP-OPT173 | segment_residual_basis | 0.271167 | 0.807689 | -0.000228 | -0.000441 | -0.001880 |
| ppopt179_micro_basis_calibration__thr=0p03__bs=0p12__ss=0p2__cap=0p003 | PP-OPT179 | basis_micro_calibration | 0.270413 | 0.806813 | -0.000982 | -0.001317 | -0.001875 |
| ppopt179_micro_basis_calibration__thr=0p03__bs=0p2__ss=0p2__cap=0p003 | PP-OPT179 | basis_micro_calibration | 0.270413 | 0.806813 | -0.000982 | -0.001317 | -0.001875 |
| ppopt179_micro_basis_calibration__thr=0p06__bs=0p12__ss=0p2__cap=0p003 | PP-OPT179 | basis_micro_calibration | 0.270413 | 0.806813 | -0.000982 | -0.001317 | -0.001875 |
| ppopt179_micro_basis_calibration__thr=0p06__bs=0p2__ss=0p2__cap=0p003 | PP-OPT179 | basis_micro_calibration | 0.270413 | 0.806813 | -0.000982 | -0.001317 | -0.001875 |
| ppopt179_micro_basis_calibration__thr=0p0__bs=0p12__ss=0p2__cap=0p003 | PP-OPT179 | basis_micro_calibration | 0.270413 | 0.806813 | -0.000982 | -0.001317 | -0.001875 |
| ppopt179_micro_basis_calibration__thr=0p0__bs=0p2__ss=0p2__cap=0p003 | PP-OPT179 | basis_micro_calibration | 0.270413 | 0.806813 | -0.000982 | -0.001317 | -0.001875 |
| ppopt173_segment_residual_basis__seg=price_qwidth__shrink=8p0__s=0p6__cap=0p007 | PP-OPT173 | segment_residual_basis | 0.271170 | 0.807689 | -0.000224 | -0.000441 | -0.001869 |
| ppopt173_segment_residual_basis__seg=price_sample__shrink=18p0__s=0p35__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270289 | 0.806965 | -0.001106 | -0.001165 | -0.001866 |
| ppopt174_direct_basis__source=stack_huber_weighted__thr=m0p04__s=0p3__cap=0p007 | PP-OPT174 | direct_model_basis_routing | 0.269769 | 0.807649 | -0.001626 | -0.000481 | -0.001862 |
| ppopt173_segment_residual_basis__seg=price_qwidth__shrink=8p0__s=0p85__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270623 | 0.807494 | -0.000772 | -0.000636 | -0.001855 |
| ppopt178_family_router__family=huber__thr=m0p02__s=0p35__cap=0p007 | PP-OPT178 | basis_family_router | 0.269775 | 0.807649 | -0.001619 | -0.000481 | -0.001850 |
| ppopt173_segment_residual_basis__seg=price_conf__shrink=18p0__s=0p35__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270533 | 0.806550 | -0.000862 | -0.001580 | -0.001845 |
| ppopt173_segment_residual_basis__seg=price_qwidth__shrink=35p0__s=0p85__cap=0p007 | PP-OPT173 | segment_residual_basis | 0.271160 | 0.807689 | -0.000234 | -0.000441 | -0.001833 |
| ppopt173_segment_residual_basis__seg=price_sample__shrink=35p0__s=0p35__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270304 | 0.806965 | -0.001091 | -0.001165 | -0.001819 |
| ppopt173_segment_residual_basis__seg=price_qwidth__shrink=18p0__s=0p85__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270628 | 0.807494 | -0.000767 | -0.000636 | -0.001818 |
| ppopt174_direct_basis__source=stack_huber_weighted__thr=0p02__s=0p45__cap=0p007 | PP-OPT174 | direct_model_basis_routing | 0.269788 | 0.807649 | -0.001606 | -0.000481 | -0.001815 |
| ppopt173_segment_residual_basis__seg=price_qwidth__shrink=8p0__s=0p6__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270632 | 0.807494 | -0.000763 | -0.000636 | -0.001808 |
| ppopt173_segment_residual_basis__seg=price_qwidth__shrink=18p0__s=0p6__cap=0p007 | PP-OPT173 | segment_residual_basis | 0.271168 | 0.807689 | -0.000227 | -0.000441 | -0.001807 |
| ppopt173_segment_residual_basis__seg=price_conf__shrink=35p0__s=0p35__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270528 | 0.806605 | -0.000867 | -0.001525 | -0.001794 |
| ppopt173_segment_residual_basis__seg=price_qwidth__shrink=18p0__s=0p6__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270640 | 0.807494 | -0.000755 | -0.000636 | -0.001791 |
| ppopt173_segment_residual_basis__seg=price_qwidth__shrink=35p0__s=0p85__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270639 | 0.807494 | -0.000756 | -0.000636 | -0.001788 |
| ppopt179_micro_basis_calibration__thr=0p03__bs=0p12__ss=0p35__cap=0p003 | PP-OPT179 | basis_micro_calibration | 0.270441 | 0.806652 | -0.000954 | -0.001478 | -0.001767 |
| ppopt179_micro_basis_calibration__thr=0p03__bs=0p2__ss=0p35__cap=0p003 | PP-OPT179 | basis_micro_calibration | 0.270441 | 0.806652 | -0.000954 | -0.001478 | -0.001767 |
| ppopt179_micro_basis_calibration__thr=0p06__bs=0p12__ss=0p35__cap=0p003 | PP-OPT179 | basis_micro_calibration | 0.270441 | 0.806652 | -0.000954 | -0.001478 | -0.001767 |
| ppopt179_micro_basis_calibration__thr=0p06__bs=0p2__ss=0p35__cap=0p003 | PP-OPT179 | basis_micro_calibration | 0.270441 | 0.806652 | -0.000954 | -0.001478 | -0.001767 |
| ppopt179_micro_basis_calibration__thr=0p0__bs=0p12__ss=0p35__cap=0p003 | PP-OPT179 | basis_micro_calibration | 0.270441 | 0.806652 | -0.000954 | -0.001478 | -0.001767 |
| ppopt179_micro_basis_calibration__thr=0p0__bs=0p2__ss=0p35__cap=0p003 | PP-OPT179 | basis_micro_calibration | 0.270441 | 0.806652 | -0.000954 | -0.001478 | -0.001767 |
| ppopt173_segment_residual_basis__seg=price_qwidth__shrink=8p0__s=0p35__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270647 | 0.807494 | -0.000748 | -0.000636 | -0.001727 |
| ppopt173_segment_residual_basis__seg=price_medium__shrink=35p0__s=0p85__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270505 | 0.806486 | -0.000890 | -0.001644 | -0.001724 |
| ppopt173_segment_residual_basis__seg=price_medium__shrink=18p0__s=0p85__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270503 | 0.806486 | -0.000892 | -0.001644 | -0.001723 |
| ppopt173_segment_residual_basis__seg=price_medium__shrink=35p0__s=0p35__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270316 | 0.806486 | -0.001078 | -0.001644 | -0.001718 |
| ppopt173_segment_residual_basis__seg=price_medium__shrink=18p0__s=0p35__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270340 | 0.806486 | -0.001055 | -0.001644 | -0.001711 |
| ppopt173_segment_residual_basis__seg=price_medium__shrink=8p0__s=0p85__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270495 | 0.806486 | -0.000900 | -0.001644 | -0.001706 |
| ppopt173_segment_residual_basis__seg=price_qwidth__shrink=35p0__s=0p6__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270646 | 0.807494 | -0.000749 | -0.000636 | -0.001698 |
| ppopt173_segment_residual_basis__seg=price_medium__shrink=8p0__s=0p35__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270360 | 0.806486 | -0.001035 | -0.001644 | -0.001691 |
| ppopt173_segment_residual_basis__seg=price_medium__shrink=35p0__s=0p6__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270436 | 0.806486 | -0.000959 | -0.001644 | -0.001684 |
| ppopt173_segment_residual_basis__seg=price_medium__shrink=18p0__s=0p6__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270477 | 0.806486 | -0.000918 | -0.001644 | -0.001671 |
| ppopt173_segment_residual_basis__seg=price_medium__shrink=8p0__s=0p6__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270497 | 0.806486 | -0.000898 | -0.001644 | -0.001670 |
| ppopt179_micro_basis_calibration__thr=0p03__bs=0p12__ss=0p35__cap=0p005 | PP-OPT179 | basis_micro_calibration | 0.270711 | 0.806514 | -0.000684 | -0.001616 | -0.001654 |
| ppopt179_micro_basis_calibration__thr=0p03__bs=0p2__ss=0p35__cap=0p005 | PP-OPT179 | basis_micro_calibration | 0.270711 | 0.806514 | -0.000684 | -0.001616 | -0.001654 |
| ppopt179_micro_basis_calibration__thr=0p06__bs=0p12__ss=0p35__cap=0p005 | PP-OPT179 | basis_micro_calibration | 0.270711 | 0.806514 | -0.000684 | -0.001616 | -0.001654 |
| ppopt179_micro_basis_calibration__thr=0p06__bs=0p2__ss=0p35__cap=0p005 | PP-OPT179 | basis_micro_calibration | 0.270711 | 0.806514 | -0.000684 | -0.001616 | -0.001654 |
| ppopt179_micro_basis_calibration__thr=0p0__bs=0p12__ss=0p35__cap=0p005 | PP-OPT179 | basis_micro_calibration | 0.270711 | 0.806514 | -0.000684 | -0.001616 | -0.001654 |
| ppopt179_micro_basis_calibration__thr=0p0__bs=0p2__ss=0p35__cap=0p005 | PP-OPT179 | basis_micro_calibration | 0.270711 | 0.806514 | -0.000684 | -0.001616 | -0.001654 |
| ppopt174_direct_basis__source=direct_xgb_weighted__thr=m0p04__s=0p45__cap=0p007 | PP-OPT174 | direct_model_basis_routing | 0.269944 | 0.807231 | -0.001451 | -0.000899 | -0.001593 |
| ppopt173_segment_residual_basis__seg=price_qwidth__shrink=18p0__s=0p35__cap=0p004 | PP-OPT173 | segment_residual_basis | 0.270648 | 0.807494 | -0.000747 | -0.000636 | -0.001592 |
| ppopt174_direct_basis__source=direct_xgb_weighted__thr=m0p04__s=0p3__cap=0p007 | PP-OPT174 | direct_model_basis_routing | 0.269946 | 0.807231 | -0.001449 | -0.000899 | -0.001591 |
| ppopt174_direct_basis__source=direct_cat_plain__thr=m0p04__s=0p45__cap=0p004 | PP-OPT174 | direct_model_basis_routing | 0.269948 | 0.807231 | -0.001447 | -0.000899 | -0.001590 |
| ppopt174_direct_basis__source=direct_xgb_weighted__thr=0p02__s=0p45__cap=0p007 | PP-OPT174 | direct_model_basis_routing | 0.269947 | 0.807231 | -0.001448 | -0.000899 | -0.001590 |
| ppopt178_family_router__family=segment_price_medium__thr=m0p02__s=0p35__cap=0p004 | PP-OPT178 | basis_family_router | 0.270023 | 0.807231 | -0.001372 | -0.000899 | -0.001590 |
| ppopt174_direct_basis__source=direct_xgb_weighted__thr=m0p04__s=0p18__cap=0p007 | PP-OPT174 | direct_model_basis_routing | 0.269949 | 0.807231 | -0.001446 | -0.000899 | -0.001589 |
| ppopt174_direct_basis__source=direct_cat_plain__thr=m0p04__s=0p45__cap=0p007 | PP-OPT174 | direct_model_basis_routing | 0.269915 | 0.807231 | -0.001480 | -0.000899 | -0.001589 |
| ppopt174_direct_basis__source=direct_xgb_weighted__thr=m0p04__s=0p45__cap=0p004 | PP-OPT174 | direct_model_basis_routing | 0.269966 | 0.807231 | -0.001429 | -0.000899 | -0.001589 |
| ppopt174_direct_basis__source=direct_xgb_weighted__thr=0p02__s=0p3__cap=0p007 | PP-OPT174 | direct_model_basis_routing | 0.269952 | 0.807231 | -0.001443 | -0.000899 | -0.001589 |
| ppopt174_direct_basis__source=direct_cat_plain__thr=0p02__s=0p45__cap=0p004 | PP-OPT174 | direct_model_basis_routing | 0.269948 | 0.807231 | -0.001447 | -0.000899 | -0.001588 |
| ppopt174_direct_basis__source=direct_cat_plain__thr=0p02__s=0p45__cap=0p007 | PP-OPT174 | direct_model_basis_routing | 0.269916 | 0.807231 | -0.001479 | -0.000899 | -0.001587 |
| ppopt174_direct_basis__source=direct_xgb_weighted__thr=m0p04__s=0p3__cap=0p004 | PP-OPT174 | direct_model_basis_routing | 0.269966 | 0.807231 | -0.001429 | -0.000899 | -0.001587 |
| ppopt174_direct_basis__source=direct_xgb_weighted__thr=0p02__s=0p45__cap=0p004 | PP-OPT174 | direct_model_basis_routing | 0.269967 | 0.807231 | -0.001428 | -0.000899 | -0.001586 |

## 선택 후보 반복 안정성
| candidate_label | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_vs_pp64_MAPE | fixed_test_delta_vs_pp64_p95_APE | avg_pp64_MAPE_win_rate | avg_pp64_p95_win_rate | replacement_score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| candidate_ppopt174_direct_basis__source_stack_huber_weighted__thr_m0p04__s_0p45__cap_0p007__37b5ac6a25 | 0.269749 | 0.807649 | -0.000815 | 0.000150 | 0.970833 | 0.594872 | -0.019544 |
| candidate_ppopt174_direct_basis__source_stack_huber_weighted__thr_m0p04__s_0p3__cap_0p007__131f865394 | 0.269769 | 0.807649 | -0.000796 | 0.000150 | 0.966987 | 0.597436 | -0.019370 |
| candidate_ppopt178_family_router__family_huber__thr_m0p02__s_0p35__cap_0p007__8c59b451c6 | 0.269775 | 0.807649 | -0.000789 | 0.000150 | 0.966026 | 0.598397 | -0.019325 |
| candidate_ppopt174_direct_basis__source_stack_huber_weighted__thr_m0p04__s_0p45__cap_0p004__4e6873aae8 | 0.269850 | 0.807470 | -0.000714 | -0.000029 | 0.964744 | 0.749359 | -0.019304 |
| candidate_ppopt174_direct_basis__source_stack_huber_weighted__thr_0p02__s_0p45__cap_0p007__f8b3aa0097 | 0.269788 | 0.807649 | -0.000776 | 0.000150 | 0.965385 | 0.601282 | -0.019286 |
| candidate_ppopt178_family_router__family_huber__thr_m0p02__s_0p35__cap_0p004__490dac3b01 | 0.269853 | 0.807470 | -0.000711 | -0.000029 | 0.964103 | 0.749359 | -0.019275 |
| candidate_ppopt174_direct_basis__source_stack_huber_weighted__thr_m0p04__s_0p3__cap_0p004__17b3b05266 | 0.269852 | 0.807470 | -0.000712 | -0.000029 | 0.963782 | 0.748397 | -0.019264 |
| candidate_ppopt174_direct_basis__source_stack_huber_weighted__thr_0p02__s_0p45__cap_0p004__1e9385ab65 | 0.269858 | 0.807470 | -0.000706 | -0.000029 | 0.963462 | 0.752244 | -0.019245 |
| candidate_ppopt174_direct_basis__source_stack_huber_weighted__thr_m0p04__s_0p18__cap_0p004__830ea14c07 | 0.269863 | 0.807470 | -0.000701 | -0.000029 | 0.961859 | 0.748077 | -0.019175 |
| candidate_ppopt174_direct_basis__source_stack_huber_weighted__thr_m0p04__s_0p18__cap_0p007__429593ab48 | 0.269816 | 0.807649 | -0.000748 | 0.000150 | 0.962821 | 0.599038 | -0.019156 |
| candidate_ppopt178_family_router__family_huber__thr_m0p02__s_0p2__cap_0p007__0353e07356 | 0.269823 | 0.807649 | -0.000741 | 0.000150 | 0.962179 | 0.600321 | -0.019123 |
| candidate_ppopt178_family_router__family_huber__thr_m0p02__s_0p2__cap_0p004__0e4190afc9 | 0.269870 | 0.807470 | -0.000694 | -0.000029 | 0.960577 | 0.749359 | -0.019117 |
| candidate_ppopt174_direct_basis__source_stack_huber_weighted__thr_0p02__s_0p3__cap_0p004__28ff748d06 | 0.269870 | 0.807470 | -0.000694 | -0.000029 | 0.960577 | 0.751282 | -0.019117 |
| candidate_ppopt174_direct_basis__source_stack_huber_weighted__thr_0p02__s_0p3__cap_0p007__782eed460d | 0.269823 | 0.807649 | -0.000741 | 0.000150 | 0.961859 | 0.602244 | -0.019111 |
| candidate_ppopt178_family_router__family_huber__thr_0p04__s_0p35__cap_0p007__a4a25d8122 | 0.269841 | 0.807527 | -0.000723 | 0.000028 | 0.959936 | 0.603846 | -0.019100 |
| candidate_ppopt174_direct_basis__source_stack_huber_weighted__thr_0p02__s_0p18__cap_0p007__8280c6eced | 0.269846 | 0.807499 | -0.000718 | 0.000000 | 0.958654 | 0.610577 | -0.019064 |
| candidate_ppopt174_direct_basis__source_stack_huber_plain__thr_m0p04__s_0p18__cap_0p007__1a6ec3c1e5 | 0.269773 | 0.807756 | -0.000791 | 0.000257 | 0.959295 | 0.492628 | -0.018983 |
| candidate_ppopt178_family_router__family_huber__thr_0p04__s_0p35__cap_0p004__68917bab69 | 0.269893 | 0.807470 | -0.000672 | -0.000029 | 0.957692 | 0.751282 | -0.018979 |
| candidate_ppopt174_direct_basis__source_stack_huber_plain__thr_m0p04__s_0p3__cap_0p007__f172a48870 | 0.269683 | 0.808105 | -0.000881 | 0.000606 | 0.962821 | 0.489423 | -0.018970 |
| candidate_ppopt174_direct_basis__source_stack_huber_plain__thr_m0p04__s_0p45__cap_0p007__c97f15237c | 0.269671 | 0.808360 | -0.000893 | 0.000861 | 0.966987 | 0.472756 | -0.018970 |
| candidate_ppopt174_direct_basis__source_stack_huber_plain__thr_m0p04__s_0p18__cap_0p004__cfcd688f97 | 0.269806 | 0.807756 | -0.000758 | 0.000257 | 0.959295 | 0.492949 | -0.018950 |
| candidate_ppopt174_direct_basis__source_stack_huber_weighted__thr_0p02__s_0p18__cap_0p004__d1ff3118f1 | 0.269896 | 0.807470 | -0.000668 | -0.000029 | 0.957051 | 0.751282 | -0.018950 |
| candidate_ppopt174_direct_basis__source_stack_huber_plain__thr_m0p04__s_0p3__cap_0p004__0d22800115 | 0.269800 | 0.807896 | -0.000764 | 0.000397 | 0.960897 | 0.491346 | -0.018922 |
| candidate_ppopt174_direct_basis__source_stack_huber_plain__thr_m0p04__s_0p45__cap_0p004__57e071aa04 | 0.269802 | 0.807963 | -0.000762 | 0.000465 | 0.961859 | 0.491346 | -0.018911 |
| candidate_ppopt178_family_router__family_huber__thr_0p04__s_0p2__cap_0p007__fcf5de0c38 | 0.269882 | 0.807400 | -0.000682 | -0.000098 | 0.954167 | 0.751603 | -0.018849 |
| candidate_ppopt178_family_router__family_huber__thr_0p04__s_0p2__cap_0p004__593357a347 | 0.269908 | 0.807400 | -0.000656 | -0.000098 | 0.954167 | 0.751603 | -0.018823 |
| candidate_ppopt174_direct_basis__source_stack_huber_weighted__thr_0p08__s_0p45__cap_0p007__938efebded | 0.269901 | 0.807373 | -0.000663 | -0.000126 | 0.953526 | 0.754487 | -0.018805 |
| candidate_ppopt174_direct_basis__source_stack_huber_weighted__thr_0p08__s_0p45__cap_0p004__55fb6db0ff | 0.269913 | 0.807373 | -0.000651 | -0.000126 | 0.953526 | 0.754487 | -0.018792 |
| candidate_ppopt174_direct_basis__source_stack_huber_plain__thr_0p02__s_0p45__cap_0p004__e6e9d613b8 | 0.269877 | 0.807657 | -0.000687 | 0.000158 | 0.954167 | 0.491987 | -0.018743 |
| candidate_ppopt174_direct_basis__source_stack_huber_weighted__thr_0p08__s_0p3__cap_0p004__498cc8e0d8 | 0.269933 | 0.807326 | -0.000631 | -0.000173 | 0.952244 | 0.754487 | -0.018721 |
| candidate_ppopt174_direct_basis__source_stack_huber_weighted__thr_0p08__s_0p3__cap_0p007__cd148467a2 | 0.269933 | 0.807326 | -0.000631 | -0.000173 | 0.952244 | 0.754487 | -0.018721 |
| pp180_operational_basis_generation_challenger | 0.269933 | 0.807326 | -0.000631 | -0.000173 | 0.952244 | 0.754487 | -0.018721 |
| candidate_ppopt174_direct_basis__source_stack_huber_plain__thr_0p02__s_0p3__cap_0p007__4531783b40 | 0.269910 | 0.807515 | -0.000654 | 0.000016 | 0.951923 | 0.494551 | -0.018720 |
| candidate_ppopt174_direct_basis__source_stack_huber_plain__thr_0p02__s_0p45__cap_0p007__6b55b6fbec | 0.269872 | 0.807657 | -0.000693 | 0.000158 | 0.953205 | 0.491987 | -0.018710 |
| candidate_ppopt174_direct_basis__source_stack_huber_plain__thr_0p02__s_0p3__cap_0p004__f30e454583 | 0.269910 | 0.807515 | -0.000654 | 0.000016 | 0.950962 | 0.494551 | -0.018681 |
| candidate_ppopt174_direct_basis__source_stack_huber_plain__thr_0p02__s_0p18__cap_0p004__b7ae584d21 | 0.269942 | 0.807402 | -0.000622 | -0.000097 | 0.950321 | 0.577564 | -0.018635 |
| candidate_ppopt174_direct_basis__source_stack_huber_plain__thr_0p02__s_0p18__cap_0p007__314e1075f7 | 0.269942 | 0.807402 | -0.000622 | -0.000097 | 0.950321 | 0.577564 | -0.018635 |
| candidate_ppopt174_direct_basis__source_stack_huber_weighted__thr_0p08__s_0p18__cap_0p004__0eaa8c77fc | 0.269958 | 0.807288 | -0.000606 | -0.000211 | 0.950000 | 0.749038 | -0.018606 |
| candidate_ppopt174_direct_basis__source_stack_huber_weighted__thr_0p08__s_0p18__cap_0p007__2ee59a4db9 | 0.269958 | 0.807288 | -0.000606 | -0.000211 | 0.950000 | 0.749038 | -0.018606 |
| candidate_ppopt174_direct_basis__source_direct_cat_plain__thr_m0p04__s_0p45__cap_0p004__57fb4d2299 | 0.269948 | 0.807231 | -0.000616 | -0.000268 | 0.949679 | 0.600641 | -0.018603 |
| candidate_ppopt174_direct_basis__source_direct_cat_plain__thr_0p02__s_0p45__cap_0p004__ce729a123b | 0.269948 | 0.807231 | -0.000616 | -0.000268 | 0.949679 | 0.600641 | -0.018603 |
| candidate_ppopt174_direct_basis__source_direct_cat_plain__thr_m0p04__s_0p45__cap_0p007__4b0e084b17 | 0.269915 | 0.807231 | -0.000650 | -0.000268 | 0.948397 | 0.594872 | -0.018585 |
| candidate_ppopt174_direct_basis__source_direct_xgb_weighted__thr_m0p04__s_0p45__cap_0p004__beacb614f8 | 0.269966 | 0.807231 | -0.000598 | -0.000268 | 0.949679 | 0.600641 | -0.018585 |
| candidate_ppopt174_direct_basis__source_direct_xgb_weighted__thr_m0p04__s_0p3__cap_0p004__c705a2e798 | 0.269966 | 0.807231 | -0.000598 | -0.000268 | 0.949679 | 0.600641 | -0.018585 |
| candidate_ppopt174_direct_basis__source_direct_cat_plain__thr_0p02__s_0p45__cap_0p007__0b07973c32 | 0.269916 | 0.807231 | -0.000648 | -0.000268 | 0.948397 | 0.594872 | -0.018584 |
| candidate_ppopt174_direct_basis__source_direct_cat_plain__thr_m0p04__s_0p3__cap_0p007__fd19676e24 | 0.269920 | 0.807231 | -0.000644 | -0.000268 | 0.948397 | 0.594872 | -0.018580 |
| candidate_ppopt174_direct_basis__source_direct_cat_plain__thr_0p02__s_0p3__cap_0p007__964030e163 | 0.269923 | 0.807231 | -0.000641 | -0.000268 | 0.948397 | 0.594872 | -0.018577 |
| candidate_ppopt174_direct_basis__source_direct_cat_plain__thr_m0p04__s_0p3__cap_0p004__23f2ad3e96 | 0.269949 | 0.807231 | -0.000615 | -0.000268 | 0.949038 | 0.600641 | -0.018577 |
| candidate_ppopt174_direct_basis__source_direct_cat_plain__thr_0p02__s_0p3__cap_0p004__8e11f6193a | 0.269950 | 0.807231 | -0.000614 | -0.000268 | 0.949038 | 0.600641 | -0.018575 |
| candidate_ppopt174_direct_basis__source_direct_cat_plain__thr_0p08__s_0p45__cap_0p007__8d3c7d3d37 | 0.269925 | 0.807231 | -0.000639 | -0.000268 | 0.948397 | 0.594872 | -0.018575 |
| candidate_ppopt174_direct_basis__source_direct_xgb_weighted__thr_0p02__s_0p45__cap_0p004__77d155accd | 0.269967 | 0.807231 | -0.000597 | -0.000268 | 0.949359 | 0.600641 | -0.018571 |
| candidate_ppopt174_direct_basis__source_direct_xgb_weighted__thr_m0p04__s_0p18__cap_0p004__2dcc2d0719 | 0.269968 | 0.807231 | -0.000596 | -0.000268 | 0.949359 | 0.600641 | -0.018570 |
| candidate_ppopt174_direct_basis__source_direct_cat_plain__thr_m0p04__s_0p18__cap_0p007__035ec8d030 | 0.269930 | 0.807231 | -0.000635 | -0.000268 | 0.948397 | 0.594872 | -0.018570 |
| candidate_ppopt174_direct_basis__source_direct_xgb_weighted__thr_0p02__s_0p3__cap_0p004__fecd8bd1f3 | 0.269968 | 0.807231 | -0.000596 | -0.000268 | 0.949359 | 0.600641 | -0.018570 |
| candidate_ppopt174_direct_basis__source_direct_xgb_weighted__thr_m0p04__s_0p45__cap_0p007__ee28357c0a | 0.269944 | 0.807231 | -0.000620 | -0.000268 | 0.948718 | 0.594872 | -0.018569 |
| candidate_ppopt174_direct_basis__source_direct_xgb_weighted__thr_0p02__s_0p18__cap_0p004__af3e4aaa8a | 0.269971 | 0.807231 | -0.000593 | -0.000268 | 0.949359 | 0.600641 | -0.018568 |
| candidate_ppopt174_direct_basis__source_direct_xgb_weighted__thr_m0p04__s_0p3__cap_0p007__881bb125c1 | 0.269946 | 0.807231 | -0.000618 | -0.000268 | 0.948718 | 0.594872 | -0.018567 |
| candidate_ppopt174_direct_basis__source_direct_cat_plain__thr_0p08__s_0p3__cap_0p007__75cef57f27 | 0.269935 | 0.807231 | -0.000629 | -0.000268 | 0.948397 | 0.594872 | -0.018565 |
| candidate_ppopt174_direct_basis__source_direct_cat_plain__thr_0p02__s_0p18__cap_0p007__2ed7e32f79 | 0.269935 | 0.807231 | -0.000629 | -0.000268 | 0.948397 | 0.594872 | -0.018565 |
| candidate_ppopt174_direct_basis__source_direct_cat_plain__thr_0p08__s_0p45__cap_0p004__5093e5a5b4 | 0.269951 | 0.807231 | -0.000613 | -0.000268 | 0.948718 | 0.600641 | -0.018562 |
| candidate_ppopt174_direct_basis__source_direct_cat_plain__thr_m0p04__s_0p18__cap_0p004__f8a0b8f6fe | 0.269953 | 0.807231 | -0.000611 | -0.000268 | 0.948718 | 0.600641 | -0.018560 |
| candidate_ppopt174_direct_basis__source_direct_cat_plain__thr_0p08__s_0p3__cap_0p004__7c25ab4bf2 | 0.269954 | 0.807231 | -0.000610 | -0.000268 | 0.948718 | 0.600641 | -0.018558 |
| candidate_ppopt174_direct_basis__source_direct_cat_plain__thr_0p02__s_0p18__cap_0p004__aa012cb4cd | 0.269954 | 0.807231 | -0.000610 | -0.000268 | 0.948718 | 0.600641 | -0.018558 |
| candidate_ppopt174_direct_basis__source_direct_xgb_weighted__thr_0p02__s_0p45__cap_0p007__6bbb793478 | 0.269947 | 0.807231 | -0.000617 | -0.000268 | 0.948397 | 0.594872 | -0.018553 |
| candidate_ppopt174_direct_basis__source_direct_cat_plain__thr_0p08__s_0p18__cap_0p007__c01669bfdc | 0.269948 | 0.807231 | -0.000616 | -0.000268 | 0.948397 | 0.594872 | -0.018552 |
| candidate_ppopt174_direct_basis__source_direct_xgb_weighted__thr_m0p04__s_0p18__cap_0p007__ca0d444771 | 0.269949 | 0.807231 | -0.000615 | -0.000268 | 0.948397 | 0.594872 | -0.018551 |
| candidate_ppopt174_direct_basis__source_direct_xgb_weighted__thr_0p02__s_0p3__cap_0p007__bf5f33958f | 0.269952 | 0.807231 | -0.000612 | -0.000268 | 0.948397 | 0.594872 | -0.018548 |
| candidate_ppopt174_direct_basis__source_direct_cat_plain__thr_0p08__s_0p18__cap_0p004__3ac99a4651 | 0.269961 | 0.807231 | -0.000603 | -0.000268 | 0.948077 | 0.600641 | -0.018526 |
| candidate_ppopt174_direct_basis__source_direct_xgb_weighted__thr_0p02__s_0p18__cap_0p007__9aff69e26f | 0.269958 | 0.807231 | -0.000606 | -0.000268 | 0.947756 | 0.594872 | -0.018516 |
| candidate_ppopt174_direct_basis__source_direct_cat_weighted__thr_0p02__s_0p45__cap_0p004__5cd53953d0 | 0.269976 | 0.807231 | -0.000588 | -0.000268 | 0.948077 | 0.600641 | -0.018511 |
| candidate_ppopt178_family_router__family_direct_cat__thr_m0p02__s_0p35__cap_0p004__d316a9dcf4 | 0.269977 | 0.807231 | -0.000587 | -0.000268 | 0.948077 | 0.600641 | -0.018510 |
| candidate_ppopt178_family_router__family_segment_price_medium__thr_0p04__s_0p2__cap_0p004__8983f9771a | 0.270003 | 0.807231 | -0.000561 | -0.000268 | 0.948718 | 0.600641 | -0.018510 |
| candidate_ppopt178_family_router__family_segment_price_conf__thr_0p04__s_0p2__cap_0p004__d743334c76 | 0.270003 | 0.807231 | -0.000561 | -0.000268 | 0.948718 | 0.600641 | -0.018509 |
| candidate_ppopt178_family_router__family_segment_price_conf__thr_0p04__s_0p35__cap_0p004__7ba2d5ae64 | 0.270003 | 0.807231 | -0.000561 | -0.000268 | 0.948718 | 0.600641 | -0.018509 |
| candidate_ppopt178_family_router__family_segment_price_conf__thr_m0p02__s_0p2__cap_0p004__0c47ae6408 | 0.270003 | 0.807231 | -0.000561 | -0.000268 | 0.948718 | 0.600641 | -0.018509 |
| candidate_ppopt178_family_router__family_segment_price_conf__thr_m0p02__s_0p35__cap_0p004__3efcafe370 | 0.270003 | 0.807231 | -0.000561 | -0.000268 | 0.948718 | 0.600641 | -0.018509 |
| candidate_ppopt178_family_router__family_segment_price_medium__thr_0p04__s_0p35__cap_0p004__b34e195a2e | 0.270003 | 0.807231 | -0.000561 | -0.000268 | 0.948718 | 0.600641 | -0.018509 |
| candidate_ppopt174_direct_basis__source_direct_cat_weighted__thr_m0p04__s_0p3__cap_0p007__64c14bc065 | 0.269958 | 0.807231 | -0.000606 | -0.000268 | 0.947436 | 0.594872 | -0.018503 |
| candidate_ppopt178_family_router__family_direct_cat__thr_m0p02__s_0p35__cap_0p007__10ef32bb79 | 0.269959 | 0.807231 | -0.000605 | -0.000268 | 0.947436 | 0.594872 | -0.018503 |
| candidate_ppopt174_direct_basis__source_direct_cat_weighted__thr_m0p04__s_0p18__cap_0p004__cfdf27105c | 0.269975 | 0.807231 | -0.000589 | -0.000268 | 0.947756 | 0.600641 | -0.018499 |
| candidate_ppopt178_family_router__family_direct_cat__thr_m0p02__s_0p2__cap_0p004__a96742b81e | 0.269975 | 0.807231 | -0.000589 | -0.000268 | 0.947756 | 0.600641 | -0.018499 |
| candidate_ppopt174_direct_basis__source_direct_cat_weighted__thr_0p02__s_0p3__cap_0p004__962d4e861c | 0.269975 | 0.807231 | -0.000589 | -0.000268 | 0.947756 | 0.600641 | -0.018499 |
| candidate_ppopt178_family_router__family_segment_price_medium__thr_m0p02__s_0p2__cap_0p004__2d6bbe468c | 0.270014 | 0.807231 | -0.000550 | -0.000268 | 0.948718 | 0.599359 | -0.018498 |
| candidate_ppopt174_direct_basis__source_direct_cat_weighted__thr_m0p04__s_0p3__cap_0p004__f5933186ac | 0.269978 | 0.807231 | -0.000586 | -0.000268 | 0.947756 | 0.600641 | -0.018496 |
| candidate_ppopt178_family_router__family_segment_price_medium__thr_m0p02__s_0p35__cap_0p004__bf21a339ce | 0.270023 | 0.807231 | -0.000541 | -0.000268 | 0.948718 | 0.599038 | -0.018489 |
| candidate_ppopt176_consensus_basis__group_lgb_cat_xgb__thr_0p02__s_0p18__cap_0p0035__5e2e06dbaa | 0.269992 | 0.807231 | -0.000572 | -0.000268 | 0.947756 | 0.600962 | -0.018482 |
| candidate_ppopt174_direct_basis__source_direct_cat_weighted__thr_m0p04__s_0p45__cap_0p004__049d964e34 | 0.269981 | 0.807231 | -0.000583 | -0.000268 | 0.947436 | 0.600641 | -0.018481 |
| candidate_ppopt176_consensus_basis__group_lgb_cat_xgb__thr_0p02__s_0p32__cap_0p0035__6185b43dc5 | 0.269994 | 0.807231 | -0.000570 | -0.000268 | 0.947756 | 0.600962 | -0.018480 |
| candidate_ppopt176_consensus_basis__group_lgb_cat_xgb__thr_0p02__s_0p46__cap_0p0035__cc66c151fe | 0.269994 | 0.807231 | -0.000570 | -0.000268 | 0.947756 | 0.600962 | -0.018480 |
| candidate_ppopt176_consensus_basis__group_lgb_cat_xgb__thr_m0p04__s_0p18__cap_0p0035__1efe8b90db | 0.269994 | 0.807231 | -0.000570 | -0.000268 | 0.947756 | 0.600962 | -0.018480 |
| candidate_ppopt176_consensus_basis__group_lgb_cat_xgb__thr_m0p04__s_0p32__cap_0p0035__4ad652ff77 | 0.269994 | 0.807231 | -0.000570 | -0.000268 | 0.947756 | 0.600962 | -0.018480 |
| candidate_ppopt176_consensus_basis__group_lgb_cat_xgb__thr_m0p04__s_0p46__cap_0p0035__a47a5bc24f | 0.269994 | 0.807231 | -0.000570 | -0.000268 | 0.947756 | 0.600962 | -0.018480 |
| candidate_ppopt178_family_router__family_segment_price_medium__thr_m0p02__s_0p2__cap_0p007__7c619e6f37 | 0.270014 | 0.807231 | -0.000550 | -0.000268 | 0.948077 | 0.594551 | -0.018473 |
| candidate_ppopt174_direct_basis__source_direct_cat_weighted__thr_m0p04__s_0p18__cap_0p007__19e65d2df5 | 0.269959 | 0.807231 | -0.000605 | -0.000268 | 0.946474 | 0.594872 | -0.018464 |
| candidate_ppopt178_family_router__family_segment_price_medium__thr_0p04__s_0p35__cap_0p007__5b0381f12e | 0.270007 | 0.807231 | -0.000557 | -0.000268 | 0.947436 | 0.594872 | -0.018454 |
| candidate_ppopt178_family_router__family_segment_price_conf__thr_0p04__s_0p2__cap_0p007__c8612c730f | 0.270008 | 0.807231 | -0.000556 | -0.000268 | 0.947436 | 0.594872 | -0.018454 |
| candidate_ppopt178_family_router__family_segment_price_conf__thr_0p04__s_0p35__cap_0p007__b09d81800c | 0.270008 | 0.807231 | -0.000556 | -0.000268 | 0.947436 | 0.594872 | -0.018454 |
| candidate_ppopt178_family_router__family_segment_price_conf__thr_m0p02__s_0p2__cap_0p007__0396c60b30 | 0.270008 | 0.807231 | -0.000556 | -0.000268 | 0.947436 | 0.594872 | -0.018454 |
| candidate_ppopt178_family_router__family_segment_price_conf__thr_m0p02__s_0p35__cap_0p007__d11329a12c | 0.270008 | 0.807231 | -0.000556 | -0.000268 | 0.947436 | 0.594872 | -0.018454 |
| candidate_ppopt174_direct_basis__source_direct_cat_weighted__thr_0p02__s_0p3__cap_0p007__8440321c9d | 0.269958 | 0.807231 | -0.000606 | -0.000268 | 0.946154 | 0.594872 | -0.018452 |
| candidate_ppopt178_family_router__family_direct_cat__thr_m0p02__s_0p2__cap_0p007__dcd3262d87 | 0.269958 | 0.807231 | -0.000606 | -0.000268 | 0.946154 | 0.594872 | -0.018452 |
| pp172_operational_reference | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.947115 | 0.605449 | -0.018451 |
| candidate_ppopt174_direct_basis__source_direct_cat_weighted__thr_0p02__s_0p18__cap_0p007__e316e28d96 | 0.269957 | 0.807231 | -0.000607 | -0.000268 | 0.945833 | 0.594872 | -0.018440 |
| pp166_operational_reference | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.946795 | 0.601923 | -0.018439 |
| candidate_ppopt178_family_router__family_segment_price_medium__thr_m0p02__s_0p35__cap_0p007__3dbbf175ab | 0.270027 | 0.807231 | -0.000537 | -0.000268 | 0.947436 | 0.594231 | -0.018434 |
| candidate_ppopt173_segment_residual_basis__seg_price_sample__shrink_8p0__s_0p85__cap_0p004__ae6d6c79e9 | 0.270171 | 0.806965 | -0.000393 | -0.000534 | 0.940064 | 0.653526 | -0.017996 |
| candidate_ppopt173_segment_residual_basis__seg_price_sample__shrink_18p0__s_0p85__cap_0p004__843de385d7 | 0.270182 | 0.806965 | -0.000382 | -0.000534 | 0.938141 | 0.653526 | -0.017908 |
| candidate_ppopt173_segment_residual_basis__seg_price_sample__shrink_35p0__s_0p85__cap_0p004__d4fcb5b5da | 0.270205 | 0.806965 | -0.000359 | -0.000534 | 0.931090 | 0.653205 | -0.017603 |
| candidate_ppopt173_segment_residual_basis__seg_price_sample__shrink_8p0__s_0p6__cap_0p004__8373df9eda | 0.270225 | 0.806965 | -0.000339 | -0.000534 | 0.928205 | 0.653526 | -0.017467 |
| pp148_operational_reference | 0.270140 | 0.807231 | -0.000424 | -0.000268 | 0.925962 | 0.531090 | -0.017463 |
| candidate_ppopt173_segment_residual_basis__seg_price_sample__shrink_18p0__s_0p6__cap_0p004__3c87504a4f | 0.270236 | 0.806965 | -0.000328 | -0.000534 | 0.925962 | 0.653205 | -0.017367 |
| candidate_ppopt173_segment_residual_basis__seg_price_sample__shrink_35p0__s_0p6__cap_0p004__277a94d796 | 0.270251 | 0.806965 | -0.000313 | -0.000534 | 0.923077 | 0.653205 | -0.017236 |
| pp126_operational_reference | 0.270114 | 0.807490 | -0.000450 | -0.000009 | 0.919231 | 0.494231 | -0.017219 |
| candidate_ppopt173_segment_residual_basis__seg_price_sample__shrink_8p0__s_0p35__cap_0p004__98f5792101 | 0.270283 | 0.806965 | -0.000281 | -0.000534 | 0.916987 | 0.652564 | -0.016960 |
| candidate_ppopt173_segment_residual_basis__seg_price_sample__shrink_18p0__s_0p35__cap_0p004__effc612948 | 0.270289 | 0.806965 | -0.000275 | -0.000534 | 0.915064 | 0.652564 | -0.016878 |
| candidate_ppopt173_segment_residual_basis__seg_price_sample__shrink_35p0__s_0p35__cap_0p004__ab47958dd4 | 0.270304 | 0.806965 | -0.000260 | -0.000534 | 0.913141 | 0.652564 | -0.016786 |
| candidate_ppopt173_segment_residual_basis__seg_price_sample__shrink_8p0__s_0p85__cap_0p007__93016c9c94 | 0.270470 | 0.806764 | -0.000094 | -0.000735 | 0.822115 | 0.616026 | -0.012979 |
| candidate_ppopt173_segment_residual_basis__seg_price_sample__shrink_18p0__s_0p85__cap_0p007__0ddcf9c122 | 0.270485 | 0.806764 | -0.000079 | -0.000735 | 0.816346 | 0.615705 | -0.012733 |
| candidate_ppopt173_segment_residual_basis__seg_price_sample__shrink_35p0__s_0p85__cap_0p007__c2f2da14f4 | 0.270510 | 0.806764 | -0.000054 | -0.000735 | 0.804808 | 0.615385 | -0.012246 |
| candidate_ppopt173_segment_residual_basis__seg_price_sample__shrink_8p0__s_0p6__cap_0p007__bc52cde95c | 0.270528 | 0.806764 | -0.000036 | -0.000735 | 0.799359 | 0.614744 | -0.012011 |
| candidate_ppopt173_segment_residual_basis__seg_price_sample__shrink_18p0__s_0p6__cap_0p007__36682d94ef | 0.270538 | 0.806764 | -0.000026 | -0.000735 | 0.792628 | 0.614423 | -0.011731 |
| pp70_refinement_candidate | 0.270561 | 0.807490 | -0.000003 | -0.000009 | 0.786859 | 0.398077 | -0.011477 |
| candidate_ppopt173_segment_residual_basis__seg_price_medium__shrink_35p0__s_0p35__cap_0p004__7301f1ad88 | 0.270316 | 0.806486 | -0.000248 | -0.001013 | 0.778526 | 0.529487 | -0.011389 |
| candidate_ppopt179_micro_basis_calibration__thr_0p03__bs_0p12__ss_0p2__cap_0p003__0a17d41dd6 | 0.270413 | 0.806813 | -0.000151 | -0.000686 | 0.774038 | 0.607051 | -0.011112 |
| candidate_ppopt179_micro_basis_calibration__thr_0p03__bs_0p2__ss_0p2__cap_0p003__afdd3b9faa | 0.270413 | 0.806813 | -0.000151 | -0.000686 | 0.774038 | 0.607051 | -0.011112 |
| candidate_ppopt179_micro_basis_calibration__thr_0p06__bs_0p12__ss_0p2__cap_0p003__a5c1e9e508 | 0.270413 | 0.806813 | -0.000151 | -0.000686 | 0.774038 | 0.607051 | -0.011112 |
| candidate_ppopt179_micro_basis_calibration__thr_0p06__bs_0p2__ss_0p2__cap_0p003__ed0b079dbe | 0.270413 | 0.806813 | -0.000151 | -0.000686 | 0.774038 | 0.607051 | -0.011112 |
| candidate_ppopt179_micro_basis_calibration__thr_0p0__bs_0p12__ss_0p2__cap_0p003__a46e666b5a | 0.270413 | 0.806813 | -0.000151 | -0.000686 | 0.774038 | 0.607051 | -0.011112 |
| candidate_ppopt179_micro_basis_calibration__thr_0p0__bs_0p2__ss_0p2__cap_0p003__b734ac89aa | 0.270413 | 0.806813 | -0.000151 | -0.000686 | 0.774038 | 0.607051 | -0.011112 |
| candidate_ppopt173_segment_residual_basis__seg_price_medium__shrink_18p0__s_0p35__cap_0p004__1318c7b964 | 0.270340 | 0.806486 | -0.000224 | -0.001013 | 0.763782 | 0.527244 | -0.010775 |
| candidate_ppopt173_segment_residual_basis__seg_price_medium__shrink_8p0__s_0p35__cap_0p004__cdf95f6736 | 0.270360 | 0.806486 | -0.000204 | -0.001013 | 0.746474 | 0.526282 | -0.010063 |
| candidate_ppopt179_micro_basis_calibration__thr_0p03__bs_0p12__ss_0p35__cap_0p003__d1146bcfc6 | 0.270441 | 0.806652 | -0.000123 | -0.000847 | 0.734295 | 0.588782 | -0.009495 |
| candidate_ppopt179_micro_basis_calibration__thr_0p03__bs_0p2__ss_0p35__cap_0p003__5a6ad33774 | 0.270441 | 0.806652 | -0.000123 | -0.000847 | 0.734295 | 0.588782 | -0.009495 |
| candidate_ppopt179_micro_basis_calibration__thr_0p06__bs_0p12__ss_0p35__cap_0p003__e576ca3797 | 0.270441 | 0.806652 | -0.000123 | -0.000847 | 0.734295 | 0.588782 | -0.009495 |
| candidate_ppopt179_micro_basis_calibration__thr_0p06__bs_0p2__ss_0p35__cap_0p003__f2f922d519 | 0.270441 | 0.806652 | -0.000123 | -0.000847 | 0.734295 | 0.588782 | -0.009495 |
| candidate_ppopt179_micro_basis_calibration__thr_0p0__bs_0p12__ss_0p35__cap_0p003__6a3af3484c | 0.270441 | 0.806652 | -0.000123 | -0.000847 | 0.734295 | 0.588782 | -0.009495 |
| candidate_ppopt179_micro_basis_calibration__thr_0p0__bs_0p2__ss_0p35__cap_0p003__4d7af06fba | 0.270441 | 0.806652 | -0.000123 | -0.000847 | 0.734295 | 0.588782 | -0.009495 |
| candidate_ppopt173_segment_residual_basis__seg_price_medium__shrink_35p0__s_0p6__cap_0p004__e94f8869f7 | 0.270436 | 0.806486 | -0.000128 | -0.001013 | 0.708974 | 0.525962 | -0.008487 |
| candidate_ppopt173_segment_residual_basis__seg_price_sample__shrink_35p0__s_0p6__cap_0p007__2085298335 | 0.270564 | 0.806764 | 0.000000 | -0.000735 | 0.698397 | 0.614423 | -0.007936 |
| candidate_ppopt173_segment_residual_basis__seg_price_sample__shrink_8p0__s_0p35__cap_0p007__09592957f4 | 0.270585 | 0.806764 | 0.000020 | -0.000735 | 0.692949 | 0.612821 | -0.007697 |

## 실행 설정
```json
{
  "experiment_id": "PP-OPT173-180",
  "experiment_slug": "PP-OPT173_180_warm_basis_generation_challenger",
  "created_at": "2026-06-10T10:04:30",
  "base_candidate": "hcoef_stable",
  "previous_experiment": "experiments/track6/PP-OPT167_172_warm_pp166_second_stage_tail_calibration",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 402,
  "prediction_rows": 452652,
  "support_candidates": {
    "pp166_operational": "ppopt166_operational_pp157_negative_gate_challenger__source=ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap008__seg_price_conf__hw_1p2__thr_0p0__s_1p0__cap_0p006",
    "pp166_p95": "ppopt166_p95_pp157_negative_gate_challenger__source=reference_pp148_p95",
    "pp148_operational": "reference_pp148_operational",
    "pp148_p95": "reference_pp148_p95",
    "pp161_p95_guard": "ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s100_cap008__hthr=0p3__w=0p14__rb=1p0__s=1p0__cap=0p006",
    "pp162_p95_gate": "ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap008__thr=0p18__w=0p1__hpen=0p5__s=1p0__cap=0p006",
    "pp164_p95_block": "ppopt164_hard_block__target=pp157_price_qwidth_q084_s100_cap008__hthr=0p45__gthr=0p12__s=1p0__cap=0p006",
    "pp172_operational": "ppopt172_operational_pp166_tail_calibration_challenger__source=ppopt169_segment_router__source_pp162_p95_gate__seg_price_conf__thr_m0p04__s_0p5__cap_0p004",
    "pp172_p95": "ppopt172_p95_pp166_tail_calibration_challenger__source=reference_pp148_p95"
  },
  "selection_decision": {
    "operational_label": "candidate_ppopt174_direct_basis__source_stack_huber_weighted__thr_0p08__s_0p3__cap_0p004__498cc8e0d8",
    "operational_candidate": "ppopt174_direct_basis__source=stack_huber_weighted__thr=0p08__s=0p3__cap=0p004",
    "operational_fixed_test_MAPE": 0.26993262658778844,
    "operational_fixed_test_p95_APE": 0.807325504659139,
    "operational_delta_vs_pp64_MAPE": -0.0006314153278719203,
    "operational_delta_vs_pp64_p95_APE": -0.00017334764697085614,
    "operational_delta_vs_pp126_MAPE": -0.00018177016206338825,
    "operational_delta_vs_pp126_p95_APE": -0.00016455623870892389,
    "operational_delta_vs_pp148_MAPE": -0.00020736178479097145,
    "operational_delta_vs_pp148_p95_APE": 9.459312044068913e-05,
    "operational_delta_vs_pp166_MAPE": -6.435907745017122e-05,
    "operational_delta_vs_pp166_p95_APE": 9.459312044068913e-05,
    "operational_delta_vs_pp172_MAPE": -6.478807336213199e-05,
    "operational_delta_vs_pp172_p95_APE": 9.459312044068913e-05,
    "operational_avg_pp64_MAPE_win_rate": 0.9522435897435897,
    "operational_avg_pp64_p95_win_rate": 0.7544871794871795,
    "operational_replacement_score": -0.01872115891761551,
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
    "p95_delta_vs_pp172_MAPE": 0.0002715112479573789,
    "p95_delta_vs_pp172_p95_APE": -0.0012815357165308905,
    "p95_avg_pp64_MAPE_win_rate": 0.5983974358974359,
    "p95_avg_pp64_p95_win_rate": 0.5009615384615385,
    "p95_replacement_score": -0.0040792899192624915,
    "operational_protocol_candidate": "ppopt180_operational_basis_generation_challenger__source=ppopt174_direct_basis__source_stack_huber_weighted__thr_0p08__s_0p3__cap_0p004",
    "p95_protocol_candidate": "ppopt180_p95_basis_generation_challenger__source=reference_pp148_p95"
  },
  "items": [
    {
      "item_id": "PP-OPT173",
      "priority": "1",
      "title": "segment residual basis",
      "description": "validation OOF residual을 가격대/신뢰도/작품 메타 구간별로 집계해 새 기준 로그가격을 만든다."
    },
    {
      "item_id": "PP-OPT174",
      "priority": "2",
      "title": "direct model basis routing",
      "description": "LightGBM/CatBoost/XGBoost/Huber 직접 예측을 기준가 후보로 두고 구간별 우세 구간에서만 적용한다."
    },
    {
      "item_id": "PP-OPT175",
      "priority": "3",
      "title": "quantile basis with uncertainty guard",
      "description": "LightGBM quantile 기준가의 폭이 좁은 구간에서만 q50/huber 기준가 이동분을 적용한다."
    },
    {
      "item_id": "PP-OPT176",
      "priority": "4",
      "title": "model consensus basis",
      "description": "여러 direct basis가 같은 방향으로 움직일 때만 평균 기준가 이동을 허용한다."
    },
    {
      "item_id": "PP-OPT177",
      "priority": "5",
      "title": "basis-to-PP172 correction",
      "description": "새 기준가를 중심으로 두고 PP172를 안정 보정 후보로 되돌리는 구조를 검증한다."
    },
    {
      "item_id": "PP-OPT178",
      "priority": "6",
      "title": "basis family router",
      "description": "segment residual basis, direct basis, PP172 중 validation 구간 성과가 좋은 family를 라우팅한다."
    },
    {
      "item_id": "PP-OPT179",
      "priority": "7",
      "title": "basis micro calibration",
      "description": "상위 basis 후보의 threshold/cap 주변만 좁게 재검증한다."
    },
    {
      "item_id": "PP-OPT180",
      "priority": "8",
      "title": "final basis-generation decision",
      "description": "PP172와 새 basis-generation 후보를 fixed/repeated 기준으로 비교해 최종 판단한다."
    }
  ],
  "sources": {
    "pp167_helper": "scripts/track6/run_pp_opt167_172_warm_pp166_second_stage_tail_calibration.py",
    "direct_meta_detail": "experiments/track6/PP-OPT161_166_warm_pp157_negative_gate_rollback/artifacts/direct_meta_prediction_detail.csv"
  }
}
```