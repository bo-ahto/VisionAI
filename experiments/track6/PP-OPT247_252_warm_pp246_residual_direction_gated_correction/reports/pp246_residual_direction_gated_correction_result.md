# PP-OPT247~252 Warm PP246 residual-direction gated correction 결과

- 작성일: 2026-06-10 13:14
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 목적: PP246 기준에서 잔차 방향 gate와 비대칭 quantile cap을 적용해 보정 여부를 더 정교하게 선택
- 결론: 균형 후보 MAPE 0.269889, PP246 대비 MAPE 변화 -0.000000759. p95-recovery 후보 p95 win rate 0.789423.

## 주요 후보 test 비교
| candidate | family | item_id | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt252_balanced_pp246_gated_correction__source=ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_huber_1p15__rs_0p05__ps_0p04__cap_0p0001 | pp246_gated_balanced_selection | PP-OPT252 | 0.140975 | 0.269889 | 0.807324 | 0.397454 | -0.001506 | -0.000805 |
| ppopt252_mape_challenger_pp246_gated_correction__source=ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_huber_1p15__rs_0p05__ps_0p04__cap_0p0001 | pp246_gated_mape_selection | PP-OPT252 | 0.140975 | 0.269889 | 0.807324 | 0.397454 | -0.001506 | -0.000805 |
| ppopt246_operational_pp234_p95_constrained__source=ppopt240_mape_challenger_pp234_learned_router__source_ppopt236_segment_winner__seg_price_conf__minn_15__gain_0p0__cap_0p | reference_prior | REFERENCE | 0.140975 | 0.269889 | 0.807326 | 0.397455 | -0.001506 | -0.000804 |
| ppopt246_balanced_pp234_p95_constrained__source=ppopt241_p95_support__src_s3__seg_price_conf__s_0p22__cap_0p0001__shrink_0p5 | reference_prior | REFERENCE | 0.140975 | 0.269889 | 0.807326 | 0.397456 | -0.001505 | -0.000804 |
| ppopt252_operational_pp246_gated_correction__source=ppopt250_segment_direction_router__seg_price_conf_qwidth__minn_8__gain_0p0__s_0p35__cap_3em05 | pp246_gated_operational_selection | PP-OPT252 | 0.140975 | 0.269890 | 0.807326 | 0.397456 | -0.001505 | -0.000804 |
| ppopt246_p95_recovery_pp234_p95_constrained__source=ppopt243_linear_residual__model_huber_1p15__s_0p22__cap_3em05__shrink_0p5 | reference_prior | REFERENCE | 0.140990 | 0.269890 | 0.807321 | 0.397455 | -0.001505 | -0.000809 |
| ppopt252_p95_recovery_pp246_gated_correction__source=ppopt249_direction_residual__prob_hist35_seed17__resid_huber_1p15__thr_0p1__s_0p14__up_8em05__down_4em05 | pp246_gated_p95_recovery_selection | PP-OPT252 | 0.140975 | 0.269891 | 0.807321 | 0.397455 | -0.001504 | -0.000809 |
| ppopt246_p95_guarded_pp234_p95_constrained__source=ppopt234_p95_guarded_pp228_p95_recovery__source_ppopt228_p95_guarded_pp222_narrow_balance__source_ppopt222_p95_guarded_p | reference_prior | REFERENCE | 0.140094 | 0.269949 | 0.807255 | 0.397482 | -0.001446 | -0.000875 |
| ppopt252_p95_guarded_pp246_gated_correction__source=ppopt246_p95_guarded_pp234_p95_constrained__source_ppopt234_p95_guarded_pp228_p95_recovery__source_ppopt228_p95_guarded_ | pp246_gated_p95_guarded_selection | PP-OPT252 | 0.140094 | 0.269949 | 0.807255 | 0.397482 | -0.001446 | -0.000875 |
| reference_pp64_current_best | reference_prior | REFERENCE | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | p95_test_MAPE | p95_test_p95_APE | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | direction residual plus p95 support ensemble | 288 | 0.269889 | 0.807324 | 0.269890 | 0.807319 | pp246_direction_residual_p95_support_ensemble | ppopt251_residual_support_ensemble__prob=hist35_seed17__resid=huber_1p15__rs=0p05__ps=0p04__cap=0p0001 |
| 6 | final PP246 gated correction decision | 6 | 0.269889 | 0.807324 | 0.270269 | 0.805949 | pp246_gated_balanced_selection | ppopt252_balanced_pp246_gated_correction__source=ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_huber_1p15__rs_0p05__ps_0p04__cap_0p0001 |
| 3 | direction-gated residual correction | 200 | 0.269889 | 0.807321 | 0.269889 | 0.807319 | pp246_direction_gated_residual | ppopt249_direction_residual__prob=hist70_seed29__resid=hist_gbr_60__thr=0p22__s=0p14__up=8em05__down=4em05 |
| 1 | residual direction probability gate | 576 | 0.269889 | 0.807326 | 0.269890 | 0.807323 | pp246_residual_direction_gate | ppopt247_direction_gate__prob=hist70_seed29__target=operational__thr=0p24__s=0p55__cap=0p0001__shrink=0p6 |
| 4 | segment residual-direction router | 96 | 0.269890 | 0.807326 | 0.269892 | 0.807317 | pp246_segment_residual_direction_router | ppopt250_segment_direction_router__seg=price_conf__minn=15__gain=2em05__s=0p35__cap=3em05 |
| 2 | asymmetric quantile residual cap | 168 | 0.269892 | 0.807324 | 0.269897 | 0.807316 | pp246_asymmetric_quantile_residual_cap | ppopt248_asym_quantile_cap__resid=huber_1p15__s=0p14__up=4em05__down=2em05__qshrink=0p55 |

## 탐색 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt252_p95_guarded_pp246_gated_correction__source=ppopt246_p95_guarded_pp234_p95_constrained__source_ppopt234_p95_guarded_pp228_p95_recovery__source_ppopt228_p95_guarded_ | PP-OPT252 | pp246_gated_p95_guarded_selection | 0.269949 | 0.807255 | -0.001446 | -0.000875 | -0.001537 |
| ppopt248_asym_quantile_cap__resid=ridge_2p0__s=0p04__up=6em05__down=6em05__qshrink=0p3 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269893 | 0.807320 | -0.001501 | -0.000810 | -0.001418 |
| ppopt248_asym_quantile_cap__resid=ridge_2p0__s=0p08__up=6em05__down=6em05__qshrink=0p3 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269893 | 0.807320 | -0.001502 | -0.000810 | -0.001418 |
| ppopt248_asym_quantile_cap__resid=ridge_2p0__s=0p14__up=6em05__down=6em05__qshrink=0p3 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269893 | 0.807320 | -0.001502 | -0.000810 | -0.001418 |
| ppopt248_asym_quantile_cap__resid=huber_1p70__s=0p14__up=6em05__down=6em05__qshrink=0p3 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269893 | 0.807320 | -0.001502 | -0.000810 | -0.001417 |
| ppopt249_direction_residual__prob=log_c1p4_seed41__resid=ridge_2p0__thr=0p1__s=0p08__up=8em05__down=4em05 | PP-OPT249 | pp246_direction_gated_residual | 0.269892 | 0.807324 | -0.001503 | -0.000806 | -0.001416 |
| ppopt249_direction_residual__prob=log_c1p4_seed41__resid=ridge_2p0__thr=0p1__s=0p14__up=8em05__down=4em05 | PP-OPT249 | pp246_direction_gated_residual | 0.269892 | 0.807324 | -0.001503 | -0.000806 | -0.001416 |
| ppopt249_direction_residual__prob=log_c1p4_seed41__resid=ridge_6p0__thr=0p1__s=0p08__up=8em05__down=4em05 | PP-OPT249 | pp246_direction_gated_residual | 0.269892 | 0.807324 | -0.001503 | -0.000806 | -0.001416 |
| ppopt248_asym_quantile_cap__resid=ridge_6p0__s=0p04__up=6em05__down=6em05__qshrink=0p3 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269894 | 0.807320 | -0.001501 | -0.000810 | -0.001416 |
| ppopt248_asym_quantile_cap__resid=ridge_2p0__s=0p04__up=6em05__down=6em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269893 | 0.807321 | -0.001502 | -0.000809 | -0.001416 |
| ppopt249_direction_residual__prob=log_c1p4_seed41__resid=ridge_6p0__thr=0p1__s=0p14__up=8em05__down=4em05 | PP-OPT249 | pp246_direction_gated_residual | 0.269891 | 0.807324 | -0.001503 | -0.000806 | -0.001416 |
| ppopt248_asym_quantile_cap__resid=ridge_6p0__s=0p08__up=6em05__down=6em05__qshrink=0p3 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269894 | 0.807320 | -0.001501 | -0.000810 | -0.001416 |
| ppopt248_asym_quantile_cap__resid=ridge_2p0__s=0p08__up=6em05__down=6em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269893 | 0.807321 | -0.001502 | -0.000809 | -0.001416 |
| ppopt248_asym_quantile_cap__resid=ridge_2p0__s=0p14__up=6em05__down=6em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269893 | 0.807321 | -0.001502 | -0.000809 | -0.001416 |
| ppopt248_asym_quantile_cap__resid=ridge_6p0__s=0p14__up=6em05__down=6em05__qshrink=0p3 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269894 | 0.807320 | -0.001501 | -0.000810 | -0.001416 |
| ppopt248_asym_quantile_cap__resid=huber_1p70__s=0p14__up=6em05__down=6em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269893 | 0.807321 | -0.001502 | -0.000809 | -0.001416 |
| ppopt248_asym_quantile_cap__resid=ridge_2p0__s=0p04__up=6em05__down=3em05__qshrink=0p3 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269894 | 0.807320 | -0.001500 | -0.000810 | -0.001416 |
| ppopt248_asym_quantile_cap__resid=ridge_2p0__s=0p08__up=6em05__down=3em05__qshrink=0p3 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269894 | 0.807320 | -0.001500 | -0.000810 | -0.001416 |
| ppopt248_asym_quantile_cap__resid=ridge_2p0__s=0p14__up=6em05__down=3em05__qshrink=0p3 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269894 | 0.807320 | -0.001500 | -0.000810 | -0.001416 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=ridge_2p0__rs=0p09__ps=0p14__cap=6em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001504 | -0.000805 | -0.001416 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=ridge_2p0__rs=0p09__ps=0p08__cap=6em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001504 | -0.000805 | -0.001416 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=ridge_2p0__rs=0p09__ps=0p04__cap=6em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001504 | -0.000805 | -0.001416 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=ridge_2p0__rs=0p05__ps=0p14__cap=6em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269891 | 0.807325 | -0.001504 | -0.000805 | -0.001415 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=ridge_2p0__rs=0p05__ps=0p08__cap=6em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269891 | 0.807325 | -0.001504 | -0.000805 | -0.001415 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=ridge_2p0__rs=0p05__ps=0p04__cap=6em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269891 | 0.807325 | -0.001504 | -0.000805 | -0.001415 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=ridge_6p0__rs=0p05__ps=0p08__cap=6em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001504 | -0.000805 | -0.001415 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=ridge_6p0__rs=0p05__ps=0p14__cap=6em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001504 | -0.000805 | -0.001415 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=ridge_6p0__rs=0p05__ps=0p04__cap=6em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001504 | -0.000805 | -0.001415 |
| ppopt249_direction_residual__prob=log_c0p2_seed17__resid=ridge_6p0__thr=0p1__s=0p08__up=8em05__down=4em05 | PP-OPT249 | pp246_direction_gated_residual | 0.269890 | 0.807324 | -0.001504 | -0.000806 | -0.001415 |
| ppopt249_direction_residual__prob=log_c0p2_seed17__resid=ridge_2p0__thr=0p1__s=0p14__up=8em05__down=4em05 | PP-OPT249 | pp246_direction_gated_residual | 0.269890 | 0.807324 | -0.001504 | -0.000806 | -0.001415 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=ridge_6p0__rs=0p09__ps=0p08__cap=6em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001415 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=ridge_6p0__rs=0p09__ps=0p14__cap=6em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001415 |
| ppopt249_direction_residual__prob=log_c0p2_seed17__resid=ridge_2p0__thr=0p1__s=0p08__up=8em05__down=4em05 | PP-OPT249 | pp246_direction_gated_residual | 0.269890 | 0.807324 | -0.001504 | -0.000806 | -0.001415 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=ridge_6p0__rs=0p09__ps=0p04__cap=6em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001415 |
| ppopt249_direction_residual__prob=log_c0p2_seed17__resid=ridge_6p0__thr=0p1__s=0p14__up=8em05__down=4em05 | PP-OPT249 | pp246_direction_gated_residual | 0.269890 | 0.807324 | -0.001504 | -0.000806 | -0.001415 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=huber_1p70__rs=0p09__ps=0p14__cap=6em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001415 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=huber_1p70__rs=0p05__ps=0p14__cap=6em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001504 | -0.000805 | -0.001415 |
| ppopt248_asym_quantile_cap__resid=huber_1p70__s=0p08__up=6em05__down=6em05__qshrink=0p3 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269893 | 0.807320 | -0.001502 | -0.000810 | -0.001415 |
| ppopt248_asym_quantile_cap__resid=huber_1p70__s=0p08__up=6em05__down=6em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269893 | 0.807321 | -0.001502 | -0.000809 | -0.001415 |
| ppopt248_asym_quantile_cap__resid=huber_1p70__s=0p14__up=6em05__down=3em05__qshrink=0p3 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269894 | 0.807320 | -0.001501 | -0.000810 | -0.001415 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=huber_1p15__rs=0p09__ps=0p14__cap=6em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001414 |
| ppopt248_asym_quantile_cap__resid=ridge_2p0__s=0p04__up=4em05__down=2em05__qshrink=0p3 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269893 | 0.807322 | -0.001502 | -0.000808 | -0.001414 |
| ppopt248_asym_quantile_cap__resid=ridge_2p0__s=0p08__up=4em05__down=2em05__qshrink=0p3 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269893 | 0.807322 | -0.001502 | -0.000808 | -0.001414 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=huber_1p15__rs=0p05__ps=0p14__cap=6em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001414 |
| ppopt248_asym_quantile_cap__resid=ridge_6p0__s=0p04__up=6em05__down=6em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269893 | 0.807321 | -0.001502 | -0.000809 | -0.001414 |
| ppopt248_asym_quantile_cap__resid=ridge_2p0__s=0p14__up=4em05__down=2em05__qshrink=0p3 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269893 | 0.807322 | -0.001502 | -0.000808 | -0.001414 |
| ppopt248_asym_quantile_cap__resid=ridge_6p0__s=0p08__up=6em05__down=6em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269893 | 0.807321 | -0.001502 | -0.000809 | -0.001414 |
| ppopt248_asym_quantile_cap__resid=huber_1p70__s=0p14__up=4em05__down=2em05__qshrink=0p3 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269893 | 0.807322 | -0.001502 | -0.000808 | -0.001414 |
| ppopt248_asym_quantile_cap__resid=ridge_6p0__s=0p04__up=6em05__down=3em05__qshrink=0p3 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269895 | 0.807320 | -0.001500 | -0.000810 | -0.001414 |
| ppopt248_asym_quantile_cap__resid=ridge_6p0__s=0p14__up=6em05__down=6em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269893 | 0.807321 | -0.001502 | -0.000809 | -0.001414 |
| ppopt248_asym_quantile_cap__resid=ridge_6p0__s=0p08__up=6em05__down=3em05__qshrink=0p3 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269895 | 0.807320 | -0.001500 | -0.000810 | -0.001414 |
| ppopt248_asym_quantile_cap__resid=ridge_6p0__s=0p14__up=6em05__down=3em05__qshrink=0p3 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269895 | 0.807320 | -0.001500 | -0.000810 | -0.001414 |
| ppopt248_asym_quantile_cap__resid=ridge_2p0__s=0p04__up=6em05__down=3em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269894 | 0.807321 | -0.001501 | -0.000809 | -0.001414 |
| ppopt248_asym_quantile_cap__resid=huber_1p70__s=0p14__up=0p0001__down=5em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269896 | 0.807318 | -0.001499 | -0.000812 | -0.001414 |
| ppopt248_asym_quantile_cap__resid=ridge_2p0__s=0p08__up=6em05__down=3em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269894 | 0.807321 | -0.001501 | -0.000809 | -0.001414 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=huber_1p70__rs=0p09__ps=0p08__cap=6em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001414 |
| ppopt248_asym_quantile_cap__resid=ridge_2p0__s=0p14__up=6em05__down=3em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269894 | 0.807321 | -0.001501 | -0.000809 | -0.001414 |
| ppopt249_direction_residual__prob=log_c1p4_seed41__resid=ridge_2p0__thr=0p1__s=0p14__up=4em05__down=2em05 | PP-OPT249 | pp246_direction_gated_residual | 0.269890 | 0.807325 | -0.001504 | -0.000805 | -0.001414 |
| ppopt249_direction_residual__prob=log_c1p4_seed41__resid=ridge_2p0__thr=0p1__s=0p08__up=4em05__down=2em05 | PP-OPT249 | pp246_direction_gated_residual | 0.269891 | 0.807325 | -0.001504 | -0.000805 | -0.001414 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=huber_1p70__rs=0p05__ps=0p08__cap=6em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001504 | -0.000805 | -0.001414 |
| ppopt248_asym_quantile_cap__resid=huber_1p70__s=0p14__up=6em05__down=3em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269894 | 0.807321 | -0.001501 | -0.000809 | -0.001414 |
| ppopt250_segment_direction_router__seg=price_conf_qwidth__minn=8__gain=0p0__s=0p7__cap=0p00012 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001414 |
| ppopt250_segment_direction_router__seg=price_conf_qwidth__minn=8__gain=0p0__s=0p35__cap=0p00012 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001414 |
| ppopt249_direction_residual__prob=log_c1p4_seed41__resid=ridge_6p0__thr=0p1__s=0p14__up=4em05__down=2em05 | PP-OPT249 | pp246_direction_gated_residual | 0.269890 | 0.807325 | -0.001504 | -0.000805 | -0.001414 |
| ppopt249_direction_residual__prob=log_c1p4_seed41__resid=ridge_6p0__thr=0p1__s=0p08__up=4em05__down=2em05 | PP-OPT249 | pp246_direction_gated_residual | 0.269890 | 0.807325 | -0.001504 | -0.000805 | -0.001414 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=huber_1p70__rs=0p05__ps=0p14__cap=3em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001414 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=huber_1p70__rs=0p09__ps=0p14__cap=3em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001414 |
| ppopt248_asym_quantile_cap__resid=huber_1p70__s=0p04__up=6em05__down=6em05__qshrink=0p3 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269893 | 0.807320 | -0.001502 | -0.000810 | -0.001414 |
| ppopt248_asym_quantile_cap__resid=ridge_6p0__s=0p04__up=0p0001__down=5em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269897 | 0.807318 | -0.001498 | -0.000812 | -0.001414 |
| ppopt250_segment_direction_router__seg=price_qwidth__minn=8__gain=0p0__s=0p7__cap=0p00012 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001414 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=huber_1p70__rs=0p09__ps=0p08__cap=3em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001414 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=ridge_2p0__rs=0p09__ps=0p08__cap=3em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001414 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=ridge_2p0__rs=0p09__ps=0p14__cap=3em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001414 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=ridge_2p0__rs=0p09__ps=0p04__cap=3em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001414 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=ridge_2p0__rs=0p05__ps=0p08__cap=3em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001414 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=ridge_2p0__rs=0p05__ps=0p14__cap=3em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001414 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=ridge_2p0__rs=0p05__ps=0p04__cap=3em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001414 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=huber_1p15__rs=0p09__ps=0p14__cap=3em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001414 |
| ppopt248_asym_quantile_cap__resid=ridge_6p0__s=0p08__up=0p0001__down=5em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269897 | 0.807318 | -0.001498 | -0.000812 | -0.001414 |
| ppopt250_segment_direction_router__seg=price_qwidth__minn=8__gain=0p0__s=0p35__cap=0p00012 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001414 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=huber_1p15__rs=0p05__ps=0p14__cap=3em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001414 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=huber_1p70__rs=0p05__ps=0p08__cap=3em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001414 |
| ppopt248_asym_quantile_cap__resid=ridge_6p0__s=0p14__up=0p0001__down=5em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269897 | 0.807318 | -0.001498 | -0.000812 | -0.001414 |
| ppopt248_asym_quantile_cap__resid=huber_1p70__s=0p04__up=6em05__down=6em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269893 | 0.807321 | -0.001502 | -0.000809 | -0.001414 |
| ppopt250_segment_direction_router__seg=price_conf_qwidth__minn=15__gain=0p0__s=0p7__cap=0p00012 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001414 |
| ppopt250_segment_direction_router__seg=price_conf_qwidth__minn=15__gain=0p0__s=0p35__cap=0p00012 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001414 |
| ppopt249_direction_residual__prob=log_c0p2_seed17__resid=ridge_2p0__thr=0p1__s=0p14__up=4em05__down=2em05 | PP-OPT249 | pp246_direction_gated_residual | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001414 |
| ppopt249_direction_residual__prob=log_c0p2_seed17__resid=ridge_2p0__thr=0p1__s=0p08__up=4em05__down=2em05 | PP-OPT249 | pp246_direction_gated_residual | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001414 |
| ppopt249_direction_residual__prob=log_c0p2_seed17__resid=ridge_6p0__thr=0p1__s=0p14__up=4em05__down=2em05 | PP-OPT249 | pp246_direction_gated_residual | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001414 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=ridge_6p0__rs=0p05__ps=0p04__cap=3em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001414 |
| ppopt249_direction_residual__prob=log_c0p2_seed17__resid=ridge_6p0__thr=0p1__s=0p08__up=4em05__down=2em05 | PP-OPT249 | pp246_direction_gated_residual | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001414 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=ridge_6p0__rs=0p05__ps=0p08__cap=3em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001414 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=ridge_6p0__rs=0p05__ps=0p14__cap=3em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001414 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=ridge_6p0__rs=0p09__ps=0p04__cap=3em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001414 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=ridge_6p0__rs=0p09__ps=0p08__cap=3em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001414 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=ridge_6p0__rs=0p09__ps=0p14__cap=3em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001414 |
| ppopt248_asym_quantile_cap__resid=ridge_6p0__s=0p04__up=4em05__down=2em05__qshrink=0p3 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269893 | 0.807322 | -0.001502 | -0.000808 | -0.001414 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=huber_1p70__rs=0p09__ps=0p04__cap=6em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001414 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=huber_1p15__rs=0p09__ps=0p08__cap=6em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001414 |
| ppopt248_asym_quantile_cap__resid=ridge_6p0__s=0p08__up=4em05__down=2em05__qshrink=0p3 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269893 | 0.807322 | -0.001502 | -0.000808 | -0.001414 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=huber_1p15__rs=0p05__ps=0p08__cap=6em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001414 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=huber_1p70__rs=0p05__ps=0p04__cap=6em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001504 | -0.000805 | -0.001414 |
| ppopt248_asym_quantile_cap__resid=ridge_2p0__s=0p04__up=4em05__down=2em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269892 | 0.807323 | -0.001503 | -0.000807 | -0.001414 |
| ppopt248_asym_quantile_cap__resid=ridge_2p0__s=0p08__up=4em05__down=2em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269892 | 0.807323 | -0.001503 | -0.000807 | -0.001413 |
| ppopt248_asym_quantile_cap__resid=ridge_6p0__s=0p14__up=4em05__down=2em05__qshrink=0p3 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269893 | 0.807322 | -0.001502 | -0.000808 | -0.001413 |
| ppopt248_asym_quantile_cap__resid=huber_1p70__s=0p08__up=4em05__down=2em05__qshrink=0p3 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269893 | 0.807322 | -0.001502 | -0.000808 | -0.001413 |
| ppopt248_asym_quantile_cap__resid=ridge_2p0__s=0p14__up=4em05__down=2em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269892 | 0.807323 | -0.001503 | -0.000807 | -0.001413 |
| ppopt248_asym_quantile_cap__resid=huber_1p70__s=0p14__up=4em05__down=2em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269892 | 0.807323 | -0.001503 | -0.000807 | -0.001413 |
| ppopt248_asym_quantile_cap__resid=huber_1p70__s=0p08__up=4em05__down=2em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269892 | 0.807323 | -0.001503 | -0.000807 | -0.001413 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=huber_1p15__rs=0p09__ps=0p08__cap=3em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001413 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=huber_1p15__rs=0p05__ps=0p08__cap=3em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001413 |
| ppopt250_segment_direction_router__seg=price_qwidth__minn=15__gain=0p0__s=0p7__cap=0p00012 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001413 |
| ppopt250_segment_direction_router__seg=price_qwidth__minn=15__gain=0p0__s=0p35__cap=0p00012 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269891 | 0.807326 | -0.001504 | -0.000804 | -0.001413 |
| ppopt250_segment_direction_router__seg=price_conf_qwidth__minn=8__gain=0p0__s=0p7__cap=7em05 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001413 |
| ppopt250_segment_direction_router__seg=price_conf_qwidth__minn=8__gain=0p0__s=0p35__cap=7em05 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001413 |
| ppopt248_asym_quantile_cap__resid=huber_1p70__s=0p08__up=6em05__down=3em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269894 | 0.807321 | -0.001501 | -0.000809 | -0.001413 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=huber_1p70__rs=0p09__ps=0p04__cap=3em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001413 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=huber_1p70__rs=0p05__ps=0p04__cap=3em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001413 |
| ppopt248_asym_quantile_cap__resid=huber_1p70__s=0p08__up=6em05__down=3em05__qshrink=0p3 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269894 | 0.807320 | -0.001501 | -0.000810 | -0.001413 |
| ppopt250_segment_direction_router__seg=price_qwidth__minn=8__gain=0p0__s=0p7__cap=7em05 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001413 |
| ppopt248_asym_quantile_cap__resid=ridge_6p0__s=0p04__up=6em05__down=3em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269894 | 0.807321 | -0.001501 | -0.000809 | -0.001413 |
| ppopt250_segment_direction_router__seg=price_qwidth__minn=8__gain=0p0__s=0p35__cap=7em05 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001413 |
| ppopt248_asym_quantile_cap__resid=ridge_6p0__s=0p08__up=6em05__down=3em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269894 | 0.807321 | -0.001501 | -0.000809 | -0.001413 |
| ppopt248_asym_quantile_cap__resid=ridge_6p0__s=0p14__up=6em05__down=3em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269894 | 0.807321 | -0.001501 | -0.000809 | -0.001413 |
| ppopt250_segment_direction_router__seg=price_conf_qwidth__minn=15__gain=0p0__s=0p7__cap=7em05 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001413 |
| ppopt250_segment_direction_router__seg=price_conf_qwidth__minn=15__gain=0p0__s=0p35__cap=7em05 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001413 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=huber_1p15__rs=0p09__ps=0p04__cap=6em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001413 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=huber_1p15__rs=0p05__ps=0p04__cap=6em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001413 |
| ppopt250_segment_direction_router__seg=price_conf__minn=15__gain=0p0__s=0p7__cap=0p00012 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269891 | 0.807325 | -0.001504 | -0.000805 | -0.001413 |
| ppopt250_segment_direction_router__seg=price_conf__minn=8__gain=0p0__s=0p7__cap=0p00012 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269891 | 0.807325 | -0.001504 | -0.000805 | -0.001413 |
| ppopt250_segment_direction_router__seg=price_conf__minn=15__gain=0p0__s=0p35__cap=0p00012 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269891 | 0.807325 | -0.001504 | -0.000804 | -0.001413 |
| ppopt250_segment_direction_router__seg=price_conf__minn=8__gain=0p0__s=0p35__cap=0p00012 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269891 | 0.807325 | -0.001504 | -0.000804 | -0.001413 |
| ppopt250_segment_direction_router__seg=price_qwidth__minn=15__gain=0p0__s=0p7__cap=7em05 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001413 |
| ppopt250_segment_direction_router__seg=price_qwidth__minn=15__gain=0p0__s=0p35__cap=7em05 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001413 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=huber_1p15__rs=0p09__ps=0p04__cap=3em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001413 |
| ppopt251_residual_support_ensemble__prob=log_c1p4_seed41__resid=huber_1p15__rs=0p05__ps=0p04__cap=3em05 | PP-OPT251 | pp246_direction_residual_p95_support_ensemble | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001413 |
| ppopt248_asym_quantile_cap__resid=ridge_6p0__s=0p04__up=4em05__down=2em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269892 | 0.807323 | -0.001502 | -0.000807 | -0.001413 |
| ppopt248_asym_quantile_cap__resid=ridge_6p0__s=0p08__up=4em05__down=2em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269892 | 0.807323 | -0.001502 | -0.000807 | -0.001413 |
| ppopt248_asym_quantile_cap__resid=ridge_6p0__s=0p14__up=4em05__down=2em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269892 | 0.807323 | -0.001502 | -0.000807 | -0.001413 |
| ppopt249_direction_residual__prob=log_c1p4_seed41__resid=huber_1p70__thr=0p22__s=0p14__up=8em05__down=4em05 | PP-OPT249 | pp246_direction_gated_residual | 0.269890 | 0.807324 | -0.001505 | -0.000806 | -0.001413 |
| ppopt249_direction_residual__prob=log_c1p4_seed41__resid=huber_1p70__thr=0p22__s=0p08__up=8em05__down=4em05 | PP-OPT249 | pp246_direction_gated_residual | 0.269890 | 0.807324 | -0.001505 | -0.000806 | -0.001413 |
| ppopt250_segment_direction_router__seg=price_conf_qwidth__minn=8__gain=0p0__s=0p7__cap=3em05 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001413 |
| ppopt250_segment_direction_router__seg=price_conf_qwidth__minn=8__gain=0p0__s=0p35__cap=3em05 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001413 |
| ppopt252_operational_pp246_gated_correction__source=ppopt250_segment_direction_router__seg_price_conf_qwidth__minn_8__gain_0p0__s_0p35__cap_3em05 | PP-OPT252 | pp246_gated_operational_selection | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001413 |
| ppopt250_segment_direction_router__seg=price_qwidth__minn=8__gain=0p0__s=0p7__cap=3em05 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001413 |
| ppopt248_asym_quantile_cap__resid=huber_1p70__s=0p08__up=0p0001__down=5em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269896 | 0.807318 | -0.001499 | -0.000812 | -0.001413 |
| ppopt250_segment_direction_router__seg=price_conf__minn=15__gain=0p0__s=0p7__cap=7em05 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001413 |
| ppopt250_segment_direction_router__seg=price_conf__minn=8__gain=0p0__s=0p7__cap=7em05 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001413 |
| ppopt250_segment_direction_router__seg=price_conf__minn=15__gain=0p0__s=0p35__cap=7em05 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269890 | 0.807325 | -0.001505 | -0.000804 | -0.001413 |
| ppopt250_segment_direction_router__seg=price_conf__minn=8__gain=0p0__s=0p35__cap=7em05 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269890 | 0.807325 | -0.001505 | -0.000804 | -0.001413 |
| ppopt250_segment_direction_router__seg=price_qwidth__minn=8__gain=0p0__s=0p35__cap=3em05 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001413 |
| ppopt248_asym_quantile_cap__resid=huber_1p70__s=0p04__up=4em05__down=2em05__qshrink=0p55 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269892 | 0.807323 | -0.001503 | -0.000807 | -0.001412 |
| ppopt250_segment_direction_router__seg=price_conf_qwidth__minn=15__gain=0p0__s=0p7__cap=3em05 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001412 |
| ppopt250_segment_direction_router__seg=price_conf_qwidth__minn=15__gain=0p0__s=0p35__cap=3em05 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001412 |
| ppopt248_asym_quantile_cap__resid=huber_1p70__s=0p04__up=4em05__down=2em05__qshrink=0p3 | PP-OPT248 | pp246_asymmetric_quantile_residual_cap | 0.269893 | 0.807322 | -0.001502 | -0.000808 | -0.001412 |
| ppopt250_segment_direction_router__seg=price_qwidth__minn=15__gain=0p0__s=0p7__cap=3em05 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001412 |
| ppopt250_segment_direction_router__seg=price_qwidth__minn=15__gain=0p0__s=0p35__cap=3em05 | PP-OPT250 | pp246_segment_residual_direction_router | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001412 |
| ppopt249_direction_residual__prob=log_c1p4_seed41__resid=huber_1p70__thr=0p22__s=0p08__up=4em05__down=2em05 | PP-OPT249 | pp246_direction_gated_residual | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001412 |
| ppopt249_direction_residual__prob=log_c1p4_seed41__resid=huber_1p70__thr=0p22__s=0p14__up=4em05__down=2em05 | PP-OPT249 | pp246_direction_gated_residual | 0.269890 | 0.807325 | -0.001505 | -0.000805 | -0.001412 |
| ppopt249_direction_residual__prob=log_c1p4_seed41__resid=huber_1p70__thr=0p1__s=0p14__up=4em05__down=2em05 | PP-OPT249 | pp246_direction_gated_residual | 0.269890 | 0.807325 | -0.001504 | -0.000805 | -0.001412 |

## 선택 후보 반복 안정성
| candidate_label | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_vs_pp64_MAPE | fixed_test_delta_vs_pp64_p95_APE | avg_pp64_MAPE_win_rate | avg_pp64_p95_win_rate | replacement_score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pp228_operational_reference | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018842 |
| pp240_operational_reference | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018842 |
| pp246_mape_reference | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018842 |
| pp246_operational_reference | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018842 |
| candidate_ppopt250_segment_direction_router__seg_price_conf_qwidth__minn_8__gain_0p0__s_0p35__cap_3em0__8fa3e0236b | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.954167 | 0.816667 | -0.018841 |
| pp252_operational_pp246_gated_candidate | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.954167 | 0.816667 | -0.018841 |
| candidate_ppopt250_segment_direction_router__seg_price_conf_qwidth__minn_8__gain_0p0__s_0p7__cap_3em05__b562f142ab | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.954167 | 0.816667 | -0.018841 |
| candidate_ppopt250_segment_direction_router__seg_price_conf_qwidth__minn_15__gain_0p0__s_0p35__cap_3em__c25487a3fe | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.954167 | 0.817308 | -0.018841 |
| candidate_ppopt250_segment_direction_router__seg_price_conf_qwidth__minn_15__gain_0p0__s_0p7__cap_3em0__5c42d0126a | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.954167 | 0.817308 | -0.018841 |
| candidate_ppopt250_segment_direction_router__seg_price_qwidth__minn_8__gain_0p0__s_0p35__cap_3em05__e03d549bd8 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.954167 | 0.789103 | -0.018841 |
| candidate_ppopt250_segment_direction_router__seg_price_qwidth__minn_8__gain_0p0__s_0p7__cap_3em05__b7468bb1c7 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.954167 | 0.789103 | -0.018841 |
| candidate_ppopt250_segment_direction_router__seg_price_qwidth__minn_15__gain_0p0__s_0p35__cap_3em05__3782e4ecd4 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.954167 | 0.789744 | -0.018841 |
| candidate_ppopt250_segment_direction_router__seg_price_qwidth__minn_15__gain_0p0__s_0p7__cap_3em05__cadd1512d2 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.954167 | 0.789744 | -0.018841 |
| candidate_ppopt250_segment_direction_router__seg_price_conf__minn_15__gain_0p0__s_0p35__cap_7em05__e3dda49ff1 | 0.269890 | 0.807325 | -0.000674 | -0.000173 | 0.954167 | 0.816667 | -0.018841 |
| candidate_ppopt250_segment_direction_router__seg_price_conf__minn_8__gain_0p0__s_0p35__cap_7em05__4b00f6a51d | 0.269890 | 0.807325 | -0.000674 | -0.000173 | 0.954167 | 0.816667 | -0.018841 |
| candidate_ppopt250_segment_direction_router__seg_price_conf__minn_15__gain_0p0__s_0p7__cap_7em05__a89c397688 | 0.269890 | 0.807325 | -0.000674 | -0.000173 | 0.954167 | 0.816667 | -0.018841 |
| candidate_ppopt250_segment_direction_router__seg_price_conf__minn_8__gain_0p0__s_0p7__cap_7em05__eafa8232f7 | 0.269890 | 0.807325 | -0.000674 | -0.000173 | 0.954167 | 0.816667 | -0.018841 |
| candidate_ppopt250_segment_direction_router__seg_price_conf_qwidth__minn_8__gain_0p0__s_0p35__cap_7em0__f4588f7beb | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.954167 | 0.814744 | -0.018841 |
| candidate_ppopt250_segment_direction_router__seg_price_conf_qwidth__minn_8__gain_0p0__s_0p7__cap_7em05__119ffcfc08 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.954167 | 0.814744 | -0.018841 |
| candidate_ppopt250_segment_direction_router__seg_price_conf_qwidth__minn_15__gain_0p0__s_0p35__cap_7em__7ce7063cef | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.954167 | 0.815385 | -0.018841 |
| candidate_ppopt250_segment_direction_router__seg_price_conf_qwidth__minn_15__gain_0p0__s_0p7__cap_7em0__6224cb9685 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.954167 | 0.815385 | -0.018841 |
| candidate_ppopt250_segment_direction_router__seg_price_qwidth__minn_8__gain_0p0__s_0p35__cap_7em05__6da74860e3 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.954167 | 0.787179 | -0.018841 |
| candidate_ppopt250_segment_direction_router__seg_price_qwidth__minn_8__gain_0p0__s_0p7__cap_7em05__46f7cd0dac | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.954167 | 0.787179 | -0.018840 |
| candidate_ppopt250_segment_direction_router__seg_price_qwidth__minn_15__gain_0p0__s_0p35__cap_7em05__8e60de9122 | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.954167 | 0.787821 | -0.018840 |
| candidate_ppopt250_segment_direction_router__seg_price_qwidth__minn_15__gain_0p0__s_0p7__cap_7em05__c550cef59b | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.954167 | 0.787821 | -0.018840 |
| pp246_p95_recovery_reference | 0.269890 | 0.807321 | -0.000674 | -0.000178 | 0.954167 | 0.814103 | -0.018840 |
| candidate_ppopt249_direction_residual__prob_log_c1p4_seed41__resid_huber_1p70__thr_0p22__s_0p08__up_8e__230f6d814c | 0.269890 | 0.807324 | -0.000674 | -0.000175 | 0.954167 | 0.749679 | -0.018840 |
| candidate_ppopt249_direction_residual__prob_log_c1p4_seed41__resid_huber_1p70__thr_0p22__s_0p14__up_8e__920813a8ec | 0.269890 | 0.807324 | -0.000674 | -0.000175 | 0.954167 | 0.749679 | -0.018840 |
| candidate_ppopt251_residual_support_ensemble__prob_log_c1p4_seed41__resid_huber_1p70__rs_0p09__ps_0p14__40eaffe703 | 0.269890 | 0.807325 | -0.000674 | -0.000174 | 0.954167 | 0.815705 | -0.018840 |
| candidate_ppopt251_residual_support_ensemble__prob_log_c1p4_seed41__resid_huber_1p70__rs_0p09__ps_0p08__6b027d5fd6 | 0.269890 | 0.807325 | -0.000674 | -0.000174 | 0.954167 | 0.815705 | -0.018840 |
| candidate_ppopt251_residual_support_ensemble__prob_log_c1p4_seed41__resid_huber_1p70__rs_0p09__ps_0p04__d8755b2f6d | 0.269890 | 0.807325 | -0.000674 | -0.000174 | 0.954167 | 0.815705 | -0.018840 |
| candidate_ppopt251_residual_support_ensemble__prob_log_c1p4_seed41__resid_huber_1p70__rs_0p05__ps_0p14__09a1672394 | 0.269890 | 0.807325 | -0.000674 | -0.000174 | 0.954167 | 0.815705 | -0.018840 |
| candidate_ppopt251_residual_support_ensemble__prob_log_c1p4_seed41__resid_huber_1p70__rs_0p05__ps_0p08__09e2e87c0d | 0.269890 | 0.807325 | -0.000674 | -0.000174 | 0.954167 | 0.815705 | -0.018840 |
| candidate_ppopt251_residual_support_ensemble__prob_log_c1p4_seed41__resid_huber_1p70__rs_0p05__ps_0p04__08df810412 | 0.269890 | 0.807325 | -0.000674 | -0.000174 | 0.954167 | 0.815705 | -0.018840 |
| candidate_ppopt250_segment_direction_router__seg_price_conf__minn_15__gain_0p0__s_0p7__cap_0p00012__3d9e3ff406 | 0.269891 | 0.807325 | -0.000673 | -0.000173 | 0.954167 | 0.827564 | -0.018840 |
| candidate_ppopt250_segment_direction_router__seg_price_conf__minn_8__gain_0p0__s_0p7__cap_0p00012__3adb4a08ea | 0.269891 | 0.807325 | -0.000673 | -0.000173 | 0.954167 | 0.827564 | -0.018840 |
| candidate_ppopt250_segment_direction_router__seg_price_conf__minn_15__gain_0p0__s_0p35__cap_0p00012__61a86f64f3 | 0.269891 | 0.807325 | -0.000673 | -0.000173 | 0.954167 | 0.827564 | -0.018840 |
| candidate_ppopt250_segment_direction_router__seg_price_conf__minn_8__gain_0p0__s_0p35__cap_0p00012__eee858c6fa | 0.269891 | 0.807325 | -0.000673 | -0.000173 | 0.954167 | 0.827564 | -0.018840 |
| candidate_ppopt250_segment_direction_router__seg_price_conf_qwidth__minn_8__gain_0p0__s_0p35__cap_0p00__bb4e256c91 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.954167 | 0.825641 | -0.018840 |
| candidate_ppopt250_segment_direction_router__seg_price_conf_qwidth__minn_8__gain_0p0__s_0p7__cap_0p000__d6f00d117b | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.954167 | 0.825641 | -0.018840 |
| candidate_ppopt250_segment_direction_router__seg_price_conf_qwidth__minn_15__gain_0p0__s_0p35__cap_0p0__4b3352a473 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.954167 | 0.826282 | -0.018840 |
| candidate_ppopt250_segment_direction_router__seg_price_conf_qwidth__minn_15__gain_0p0__s_0p7__cap_0p00__2b78544102 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.954167 | 0.826282 | -0.018840 |
| candidate_ppopt250_segment_direction_router__seg_price_qwidth__minn_8__gain_0p0__s_0p35__cap_0p00012__fac21d835d | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.954167 | 0.798077 | -0.018840 |
| candidate_ppopt250_segment_direction_router__seg_price_qwidth__minn_8__gain_0p0__s_0p7__cap_0p00012__949dfe0a6f | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.954167 | 0.798077 | -0.018840 |
| candidate_ppopt250_segment_direction_router__seg_price_qwidth__minn_15__gain_0p0__s_0p35__cap_0p00012__a81a1b3240 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.954167 | 0.798718 | -0.018840 |
| candidate_ppopt250_segment_direction_router__seg_price_qwidth__minn_15__gain_0p0__s_0p7__cap_0p00012__19f7d17691 | 0.269891 | 0.807326 | -0.000673 | -0.000173 | 0.954167 | 0.798718 | -0.018840 |
| candidate_ppopt248_asym_quantile_cap__resid_huber_1p70__s_0p04__up_6em05__down_6em05__qshrink_0p55__507e467263 | 0.269893 | 0.807321 | -0.000671 | -0.000178 | 0.954167 | 0.670833 | -0.018838 |
| candidate_ppopt248_asym_quantile_cap__resid_huber_1p70__s_0p08__up_6em05__down_6em05__qshrink_0p55__75af64bab2 | 0.269893 | 0.807321 | -0.000671 | -0.000178 | 0.954167 | 0.670833 | -0.018838 |
| candidate_ppopt248_asym_quantile_cap__resid_huber_1p70__s_0p14__up_6em05__down_6em05__qshrink_0p55__dd6b43f523 | 0.269893 | 0.807321 | -0.000671 | -0.000178 | 0.954167 | 0.670833 | -0.018838 |
| candidate_ppopt248_asym_quantile_cap__resid_huber_1p70__s_0p04__up_6em05__down_6em05__qshrink_0p3__081401d966 | 0.269893 | 0.807320 | -0.000671 | -0.000179 | 0.954167 | 0.668590 | -0.018838 |
| candidate_ppopt248_asym_quantile_cap__resid_huber_1p70__s_0p14__up_6em05__down_6em05__qshrink_0p3__2fe618ca42 | 0.269893 | 0.807320 | -0.000671 | -0.000179 | 0.954167 | 0.668590 | -0.018838 |
| candidate_ppopt248_asym_quantile_cap__resid_huber_1p70__s_0p08__up_6em05__down_6em05__qshrink_0p3__75ac7d4d9c | 0.269893 | 0.807320 | -0.000671 | -0.000179 | 0.954167 | 0.668590 | -0.018838 |
| candidate_ppopt248_asym_quantile_cap__resid_ridge_2p0__s_0p14__up_6em05__down_6em05__qshrink_0p3__65ca692aaa | 0.269893 | 0.807320 | -0.000671 | -0.000179 | 0.954167 | 0.669231 | -0.018837 |
| candidate_ppopt248_asym_quantile_cap__resid_ridge_2p0__s_0p08__up_6em05__down_6em05__qshrink_0p3__aa9680b473 | 0.269893 | 0.807320 | -0.000671 | -0.000179 | 0.954167 | 0.669231 | -0.018837 |
| candidate_ppopt248_asym_quantile_cap__resid_ridge_2p0__s_0p04__up_6em05__down_6em05__qshrink_0p3__727cd52d0f | 0.269893 | 0.807320 | -0.000671 | -0.000179 | 0.954167 | 0.669231 | -0.018837 |
| candidate_ppopt248_asym_quantile_cap__resid_hist_gbr_60__s_0p04__up_6em05__down_6em05__qshrink_0p3__fe47436953 | 0.269894 | 0.807323 | -0.000670 | -0.000176 | 0.954167 | 0.671154 | -0.018837 |
| candidate_ppopt248_asym_quantile_cap__resid_hist_gbr_60__s_0p08__up_6em05__down_6em05__qshrink_0p3__3245a3fed2 | 0.269894 | 0.807323 | -0.000670 | -0.000176 | 0.954167 | 0.671154 | -0.018837 |
| candidate_ppopt248_asym_quantile_cap__resid_hist_gbr_60__s_0p14__up_6em05__down_6em05__qshrink_0p3__0025a252d5 | 0.269894 | 0.807323 | -0.000670 | -0.000176 | 0.954167 | 0.671154 | -0.018837 |
| candidate_ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_huber_1p15__rs_0p05__ps_0p04____dda3fdcffe | 0.269889 | 0.807324 | -0.000675 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| pp252_balanced_pp246_gated_candidate | 0.269889 | 0.807324 | -0.000675 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| pp252_mape_pp246_gated_candidate | 0.269889 | 0.807324 | -0.000675 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_huber_1p15__rs_0p05__ps_0p08____c1eb7eb4c4 | 0.269889 | 0.807324 | -0.000675 | -0.000175 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_huber_1p15__rs_0p05__ps_0p14____f1cb3d5f66 | 0.269889 | 0.807324 | -0.000675 | -0.000175 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_huber_1p15__rs_0p09__ps_0p04____6e2b1ce291 | 0.269889 | 0.807324 | -0.000675 | -0.000175 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_huber_1p15__rs_0p09__ps_0p08____c7ff504d40 | 0.269889 | 0.807324 | -0.000675 | -0.000175 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_huber_1p15__rs_0p09__ps_0p14____59dbe4f6f6 | 0.269889 | 0.807323 | -0.000675 | -0.000175 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_huber_1p15__rs_0p05__ps_0p04____8a565b9602 | 0.269889 | 0.807324 | -0.000675 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_huber_1p15__rs_0p05__ps_0p08____9e087ea17a | 0.269889 | 0.807324 | -0.000675 | -0.000175 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_huber_1p15__rs_0p05__ps_0p14____288c610d56 | 0.269889 | 0.807324 | -0.000675 | -0.000175 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_huber_1p15__rs_0p09__ps_0p04____673ca75710 | 0.269889 | 0.807324 | -0.000675 | -0.000175 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_huber_1p15__rs_0p09__ps_0p08____192e8c7b57 | 0.269889 | 0.807324 | -0.000675 | -0.000175 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_huber_1p15__rs_0p09__ps_0p14____8b17016bd5 | 0.269889 | 0.807324 | -0.000675 | -0.000175 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt249_direction_residual__prob_hist70_seed29__resid_hist_gbr_60__thr_0p22__s_0p14__up_8em__ae320bec03 | 0.269889 | 0.807321 | -0.000675 | -0.000178 | 0.953846 | 0.745513 | -0.018829 |
| candidate_ppopt249_direction_residual__prob_hist70_seed29__resid_hist_gbr_60__thr_0p22__s_0p08__up_8em__139767faa9 | 0.269889 | 0.807321 | -0.000675 | -0.000178 | 0.953846 | 0.745513 | -0.018829 |
| candidate_ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_huber_1p70__rs_0p05__ps_0p08____8beec28274 | 0.269889 | 0.807323 | -0.000675 | -0.000176 | 0.953846 | 0.658013 | -0.018829 |
| candidate_ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_huber_1p70__rs_0p05__ps_0p14____06d2a51033 | 0.269889 | 0.807323 | -0.000675 | -0.000176 | 0.953846 | 0.658013 | -0.018829 |
| candidate_ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_huber_1p70__rs_0p05__ps_0p04____32dec0cb14 | 0.269889 | 0.807323 | -0.000675 | -0.000176 | 0.953846 | 0.658013 | -0.018829 |
| candidate_ppopt249_direction_residual__prob_hist70_seed29__resid_huber_1p15__thr_0p22__s_0p08__up_8em0__e447f65209 | 0.269889 | 0.807322 | -0.000675 | -0.000176 | 0.953846 | 0.779808 | -0.018829 |
| candidate_ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_huber_1p15__rs_0p05__ps_0p04____cc842530fc | 0.269889 | 0.807325 | -0.000675 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_huber_1p15__rs_0p05__ps_0p08____c6d39b3122 | 0.269889 | 0.807325 | -0.000675 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_huber_1p15__rs_0p05__ps_0p14____bf82a34f29 | 0.269889 | 0.807325 | -0.000675 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt249_direction_residual__prob_hist70_seed29__resid_ridge_2p0__thr_0p22__s_0p08__up_8em05__4b8a63cfcc | 0.269889 | 0.807319 | -0.000675 | -0.000179 | 0.953846 | 0.744872 | -0.018829 |
| candidate_ppopt249_direction_residual__prob_hist70_seed29__resid_ridge_2p0__thr_0p22__s_0p14__up_8em05__59feffba86 | 0.269889 | 0.807319 | -0.000675 | -0.000179 | 0.953846 | 0.744872 | -0.018829 |
| candidate_ppopt249_direction_residual__prob_hist70_seed29__resid_hist_gbr_60__thr_0p22__s_0p08__up_4em__e0d6dd6d4d | 0.269889 | 0.807323 | -0.000675 | -0.000176 | 0.953846 | 0.747436 | -0.018829 |
| candidate_ppopt249_direction_residual__prob_hist70_seed29__resid_hist_gbr_60__thr_0p22__s_0p14__up_4em__7ad313fe48 | 0.269889 | 0.807323 | -0.000675 | -0.000176 | 0.953846 | 0.747436 | -0.018829 |
| candidate_ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_huber_1p15__rs_0p09__ps_0p04____8a5be2d0e6 | 0.269889 | 0.807324 | -0.000675 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_huber_1p15__rs_0p09__ps_0p08____32b14b8ad4 | 0.269889 | 0.807324 | -0.000675 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_huber_1p15__rs_0p09__ps_0p14____ecd0986757 | 0.269889 | 0.807324 | -0.000675 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_operational__thr_0p24__s_0p55__cap_0p000__6035894d75 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_operational__thr_0p24__s_0p55__cap_0p000__aa58c1e6d0 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_operational__thr_0p24__s_0p55__cap_6em05__903b0d1f38 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_operational__thr_0p12__s_0p55__cap_0p000__a494cf95c3 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_operational__thr_0p12__s_0p55__cap_0p000__f4a9ade072 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_operational__thr_0p24__s_0p55__cap_6em05__38944cf290 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt249_direction_residual__prob_hist70_seed29__resid_ridge_6p0__thr_0p22__s_0p08__up_8em05__0fcf45e617 | 0.269889 | 0.807319 | -0.000675 | -0.000179 | 0.953846 | 0.745513 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_p95_recovery__thr_0p12__s_0p55__cap_0p00__263e74ac9c | 0.269889 | 0.807325 | -0.000675 | -0.000174 | 0.953846 | 0.780128 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_p95_recovery__thr_0p12__s_0p55__cap_0p00__b361495556 | 0.269889 | 0.807325 | -0.000675 | -0.000174 | 0.953846 | 0.780128 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_p95_recovery__thr_0p12__s_0p55__cap_2em0__0bd43c24fa | 0.269889 | 0.807325 | -0.000675 | -0.000174 | 0.953846 | 0.780128 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_p95_recovery__thr_0p12__s_0p55__cap_2em0__81eca61317 | 0.269889 | 0.807325 | -0.000675 | -0.000174 | 0.953846 | 0.780128 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_p95_recovery__thr_0p12__s_0p55__cap_6em0__51093d1202 | 0.269889 | 0.807325 | -0.000675 | -0.000174 | 0.953846 | 0.780128 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_p95_recovery__thr_0p12__s_0p55__cap_6em0__c4ffb3dfe6 | 0.269889 | 0.807325 | -0.000675 | -0.000174 | 0.953846 | 0.780128 | -0.018828 |
| candidate_ppopt249_direction_residual__prob_hist70_seed29__resid_ridge_2p0__thr_0p22__s_0p08__up_4em05__6eb7d2a50b | 0.269889 | 0.807322 | -0.000675 | -0.000176 | 0.953846 | 0.746795 | -0.018828 |
| candidate_ppopt249_direction_residual__prob_hist70_seed29__resid_ridge_6p0__thr_0p22__s_0p14__up_8em05__9f1d4b3e52 | 0.269889 | 0.807319 | -0.000675 | -0.000179 | 0.953846 | 0.745513 | -0.018828 |
| candidate_ppopt249_direction_residual__prob_hist70_seed29__resid_ridge_2p0__thr_0p22__s_0p14__up_4em05__e5d4eed00f | 0.269889 | 0.807322 | -0.000675 | -0.000176 | 0.953846 | 0.746795 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_operational__thr_0p12__s_0p55__cap_6em05__1c2fa34069 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt249_direction_residual__prob_hist70_seed29__resid_ridge_6p0__thr_0p22__s_0p14__up_4em05__eade627f8a | 0.269889 | 0.807322 | -0.000675 | -0.000176 | 0.953846 | 0.747436 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_p95_recovery__thr_0p24__s_0p55__cap_0p00__4ce6e4bec4 | 0.269889 | 0.807325 | -0.000675 | -0.000173 | 0.953846 | 0.780449 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_p95_recovery__thr_0p24__s_0p55__cap_0p00__d4bfbd74b8 | 0.269889 | 0.807325 | -0.000675 | -0.000173 | 0.953846 | 0.780449 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_p95_recovery__thr_0p24__s_0p55__cap_2em0__9d1a0b92ef | 0.269889 | 0.807325 | -0.000675 | -0.000173 | 0.953846 | 0.780449 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_p95_recovery__thr_0p24__s_0p55__cap_2em0__e5fbeebca2 | 0.269889 | 0.807325 | -0.000675 | -0.000173 | 0.953846 | 0.780449 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_p95_recovery__thr_0p24__s_0p55__cap_6em0__7cd208abe3 | 0.269889 | 0.807325 | -0.000675 | -0.000173 | 0.953846 | 0.780449 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_p95_recovery__thr_0p24__s_0p55__cap_6em0__8a5e7280dc | 0.269889 | 0.807325 | -0.000675 | -0.000173 | 0.953846 | 0.780449 | -0.018828 |
| candidate_ppopt249_direction_residual__prob_hist70_seed29__resid_huber_1p15__thr_0p22__s_0p14__up_8em0__0728bda9e9 | 0.269889 | 0.807321 | -0.000675 | -0.000178 | 0.953846 | 0.779808 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist35_seed17__target_p95_recovery__thr_0p12__s_0p55__cap_0p00__5935f0ff52 | 0.269889 | 0.807325 | -0.000675 | -0.000174 | 0.953846 | 0.784615 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist35_seed17__target_p95_recovery__thr_0p12__s_0p55__cap_0p00__e6c30e690d | 0.269889 | 0.807325 | -0.000675 | -0.000174 | 0.953846 | 0.784615 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist35_seed17__target_p95_recovery__thr_0p12__s_0p55__cap_2em0__23a41ed951 | 0.269889 | 0.807325 | -0.000675 | -0.000174 | 0.953846 | 0.784615 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist35_seed17__target_p95_recovery__thr_0p12__s_0p55__cap_2em0__653876abe1 | 0.269889 | 0.807325 | -0.000675 | -0.000174 | 0.953846 | 0.784615 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist35_seed17__target_p95_recovery__thr_0p12__s_0p55__cap_6em0__0b9fc69182 | 0.269889 | 0.807325 | -0.000675 | -0.000174 | 0.953846 | 0.784615 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist35_seed17__target_p95_recovery__thr_0p12__s_0p55__cap_6em0__38f7c2e8ba | 0.269889 | 0.807325 | -0.000675 | -0.000174 | 0.953846 | 0.784615 | -0.018828 |
| candidate_ppopt249_direction_residual__prob_hist70_seed29__resid_ridge_6p0__thr_0p22__s_0p08__up_4em05__0105d69763 | 0.269889 | 0.807322 | -0.000675 | -0.000176 | 0.953846 | 0.747436 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist35_seed17__target_operational__thr_0p24__s_0p55__cap_0p000__425dc93942 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist35_seed17__target_operational__thr_0p24__s_0p55__cap_0p000__c551e50a8f | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist35_seed17__target_operational__thr_0p24__s_0p55__cap_6em05__afc6fd233d | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist35_seed17__target_operational__thr_0p24__s_0p55__cap_6em05__bf0829e508 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_operational__thr_0p12__s_0p55__cap_6em05__4d38907144 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_ridge_6p0__rs_0p05__ps_0p04__c__4f19e41c40 | 0.269889 | 0.807321 | -0.000675 | -0.000178 | 0.953846 | 0.658333 | -0.018828 |
| candidate_ppopt249_direction_residual__prob_hist35_seed17__resid_huber_1p15__thr_0p22__s_0p08__up_8em0__4d58a31e92 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.780449 | -0.018828 |
| candidate_ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_ridge_6p0__rs_0p05__ps_0p08__c__83777f6501 | 0.269889 | 0.807321 | -0.000675 | -0.000178 | 0.953846 | 0.658333 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist35_seed17__target_operational__thr_0p12__s_0p55__cap_0p000__0eae052666 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist35_seed17__target_operational__thr_0p12__s_0p55__cap_0p000__67a5d9122b | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist35_seed17__target_operational__thr_0p12__s_0p55__cap_6em05__097a910283 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_operational__thr_0p24__s_0p25__cap_0p000__2dd140ac32 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_operational__thr_0p24__s_0p25__cap_0p000__abf04f9f04 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_operational__thr_0p24__s_0p25__cap_6em05__38f51e575d | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_operational__thr_0p24__s_0p25__cap_6em05__3af2aa61d9 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist35_seed17__target_operational__thr_0p12__s_0p55__cap_6em05__138fd3fe2f | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_lgbm80_seed29__target_operational__thr_0p12__s_0p55__cap_0p000__1f22c2e55a | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_lgbm80_seed29__target_operational__thr_0p12__s_0p55__cap_0p000__b854bd09dd | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_lgbm80_seed29__target_operational__thr_0p12__s_0p55__cap_6em05__115af8466f | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_lgbm80_seed29__target_operational__thr_0p12__s_0p55__cap_6em05__8b90eb8e86 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_lgbm80_seed29__target_p95_recovery__thr_0p12__s_0p55__cap_0p00__2b7b576b78 | 0.269889 | 0.807325 | -0.000675 | -0.000173 | 0.953846 | 0.780128 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_lgbm80_seed29__target_p95_recovery__thr_0p12__s_0p55__cap_0p00__7b7d581148 | 0.269889 | 0.807325 | -0.000675 | -0.000173 | 0.953846 | 0.780128 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_lgbm80_seed29__target_p95_recovery__thr_0p12__s_0p55__cap_2em0__076e8ada6d | 0.269889 | 0.807325 | -0.000675 | -0.000173 | 0.953846 | 0.780128 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_lgbm80_seed29__target_p95_recovery__thr_0p12__s_0p55__cap_2em0__22f29f6024 | 0.269889 | 0.807325 | -0.000675 | -0.000173 | 0.953846 | 0.780128 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_lgbm80_seed29__target_p95_recovery__thr_0p12__s_0p55__cap_6em0__96e7a584b1 | 0.269889 | 0.807325 | -0.000675 | -0.000173 | 0.953846 | 0.780128 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_lgbm80_seed29__target_p95_recovery__thr_0p12__s_0p55__cap_6em0__b23405b0aa | 0.269889 | 0.807325 | -0.000675 | -0.000173 | 0.953846 | 0.780128 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_operational__thr_0p12__s_0p25__cap_0p000__6d94cbad23 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_operational__thr_0p12__s_0p25__cap_0p000__880749b802 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_operational__thr_0p12__s_0p25__cap_6em05__fa379f3a98 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_operational__thr_0p12__s_0p25__cap_6em05__fc2b917139 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt249_direction_residual__prob_hist70_seed29__resid_huber_1p15__thr_0p22__s_0p08__up_4em0__cc90c05ecc | 0.269889 | 0.807323 | -0.000675 | -0.000176 | 0.953846 | 0.779808 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_p95_recovery__thr_0p12__s_0p25__cap_0p00__763ed208c6 | 0.269889 | 0.807325 | -0.000675 | -0.000174 | 0.953846 | 0.780769 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_p95_recovery__thr_0p12__s_0p25__cap_0p00__b1da32e0fa | 0.269889 | 0.807325 | -0.000675 | -0.000174 | 0.953846 | 0.780769 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_p95_recovery__thr_0p12__s_0p25__cap_2em0__362e182207 | 0.269889 | 0.807325 | -0.000675 | -0.000174 | 0.953846 | 0.780769 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_p95_recovery__thr_0p12__s_0p25__cap_2em0__fa5c38d352 | 0.269889 | 0.807325 | -0.000675 | -0.000174 | 0.953846 | 0.780769 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_p95_recovery__thr_0p12__s_0p25__cap_6em0__1eb1f790cc | 0.269889 | 0.807325 | -0.000675 | -0.000174 | 0.953846 | 0.780769 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_p95_recovery__thr_0p12__s_0p25__cap_6em0__45937ee87e | 0.269889 | 0.807325 | -0.000675 | -0.000174 | 0.953846 | 0.780769 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_operational__thr_0p24__s_0p25__cap_2em05__2448f71a73 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt249_direction_residual__prob_hist70_seed29__resid_huber_1p15__thr_0p22__s_0p14__up_4em0__28af065587 | 0.269889 | 0.807323 | -0.000675 | -0.000176 | 0.953846 | 0.779808 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_lgbm80_seed29__target_p95_recovery__thr_0p24__s_0p55__cap_0p00__4071d4d1eb | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_lgbm80_seed29__target_p95_recovery__thr_0p24__s_0p55__cap_0p00__8c6ef2ffd3 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_lgbm80_seed29__target_p95_recovery__thr_0p24__s_0p55__cap_2em0__0a3ec00069 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_lgbm80_seed29__target_p95_recovery__thr_0p24__s_0p55__cap_2em0__eaa723531e | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_lgbm80_seed29__target_p95_recovery__thr_0p24__s_0p55__cap_6em0__3cc13e7872 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_lgbm80_seed29__target_p95_recovery__thr_0p24__s_0p55__cap_6em0__8efebd2903 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_p95_recovery__thr_0p24__s_0p25__cap_0p00__96d5fef5bb | 0.269889 | 0.807325 | -0.000675 | -0.000173 | 0.953846 | 0.781090 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_p95_recovery__thr_0p24__s_0p25__cap_0p00__a6caaf707b | 0.269889 | 0.807325 | -0.000675 | -0.000173 | 0.953846 | 0.781090 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_p95_recovery__thr_0p24__s_0p25__cap_2em0__202dcf9570 | 0.269889 | 0.807325 | -0.000675 | -0.000173 | 0.953846 | 0.781090 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_p95_recovery__thr_0p24__s_0p25__cap_2em0__661b0dd5a7 | 0.269889 | 0.807325 | -0.000675 | -0.000173 | 0.953846 | 0.781090 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_p95_recovery__thr_0p24__s_0p25__cap_6em0__891b3afdbd | 0.269889 | 0.807325 | -0.000675 | -0.000173 | 0.953846 | 0.781090 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_p95_recovery__thr_0p24__s_0p25__cap_6em0__ab0ed4e913 | 0.269889 | 0.807325 | -0.000675 | -0.000173 | 0.953846 | 0.781090 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_log_c0p2_seed17__target_operational__thr_0p24__s_0p55__cap_0p0__0794d46dfa | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist70_seed29__target_operational__thr_0p24__s_0p25__cap_2em05__1126cca5ed | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_lgbm80_seed29__target_operational__thr_0p24__s_0p55__cap_0p000__42af808160 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_lgbm80_seed29__target_operational__thr_0p24__s_0p55__cap_0p000__bb85552d82 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_lgbm80_seed29__target_operational__thr_0p24__s_0p55__cap_6em05__85518e2f61 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_lgbm80_seed29__target_operational__thr_0p24__s_0p55__cap_6em05__8eba103678 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist35_seed17__target_operational__thr_0p24__s_0p55__cap_2em05__95475701d4 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_lgbm80_seed29__target_operational__thr_0p12__s_0p55__cap_2em05__d690b0e215 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018828 |
| candidate_ppopt247_direction_gate__prob_hist35_seed17__target_p95_recovery__thr_0p12__s_0p25__cap_0p00__1125b99ea4 | 0.269889 | 0.807325 | -0.000675 | -0.000173 | 0.953846 | 0.784615 | -0.018828 |

## 실행 설정
```json
{
  "experiment_id": "PP-OPT247-252",
  "experiment_slug": "PP-OPT247_252_warm_pp246_residual_direction_gated_correction",
  "created_at": "2026-06-10T13:13:53",
  "previous_experiment": "experiments/track6/PP-OPT241_246_warm_pp234_p95_constrained_support_and_basis_regeneration",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 1360,
  "prediction_rows": 1531360,
  "previous_decision": {
    "operational_label": "pp240_mape_reference",
    "operational_candidate": "ppopt240_mape_challenger_pp234_learned_router__source=ppopt236_segment_winner__seg_price_conf__minn_15__gain_0p0__cap_0p00045__shrink_0p5",
    "operational_fixed_test_MAPE": 0.26988910777837405,
    "operational_fixed_test_p95_APE": 0.8073255046591389,
    "operational_delta_vs_pp64_MAPE": -0.0006749341372863094,
    "operational_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "operational_delta_vs_pp234_MAPE": -3.8978966737657217e-07,
    "operational_delta_vs_pp234_p95_win_rate": -0.0006410256410256387,
    "operational_delta_vs_pp240_operational_MAPE": 0.0,
    "operational_avg_pp64_MAPE_win_rate": 0.9541666666666666,
    "operational_avg_pp64_p95_win_rate": 0.7471153846153845,
    "operational_replacement_score": -0.018841600803952974,
    "balanced_label": "candidate_ppopt241_p95_support__src_s3__seg_price_conf__s_0p22__cap_0p0001__shrink_0p5__24d5cb2201",
    "balanced_candidate": "ppopt241_p95_support__src=s3__seg=price_conf__s=0p22__cap=0p0001__shrink=0p5",
    "balanced_fixed_test_MAPE": 0.26988949026577663,
    "balanced_fixed_test_p95_APE": 0.8073255046591389,
    "balanced_delta_vs_pp64_MAPE": -0.0006745516498837256,
    "balanced_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "balanced_delta_vs_pp234_MAPE": -7.302264792841129e-09,
    "balanced_delta_vs_pp234_p95_win_rate": 0.0,
    "balanced_delta_vs_pp240_operational_MAPE": 3.8248740258373104e-07,
    "balanced_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "balanced_avg_pp64_p95_win_rate": 0.7477564102564102,
    "balanced_replacement_score": -0.01882839780372988,
    "mape_challenger_label": "pp240_mape_reference",
    "mape_challenger_candidate": "ppopt240_mape_challenger_pp234_learned_router__source=ppopt236_segment_winner__seg_price_conf__minn_15__gain_0p0__cap_0p00045__shrink_0p5",
    "mape_challenger_fixed_test_MAPE": 0.26988910777837405,
    "mape_challenger_fixed_test_p95_APE": 0.8073255046591389,
    "mape_challenger_delta_vs_pp64_MAPE": -0.0006749341372863094,
    "mape_challenger_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "mape_challenger_delta_vs_pp234_MAPE": -3.8978966737657217e-07,
    "mape_challenger_delta_vs_pp234_p95_win_rate": -0.0006410256410256387,
    "mape_challenger_delta_vs_pp240_operational_MAPE": 0.0,
    "mape_challenger_avg_pp64_MAPE_win_rate": 0.9541666666666666,
    "mape_challenger_avg_pp64_p95_win_rate": 0.7471153846153845,
    "mape_challenger_replacement_score": -0.018841600803952974,
    "p95_recovery_label": "candidate_ppopt243_linear_residual__model_huber_1p15__s_0p22__cap_3em05__shrink_0p5__ddb3a8ef18",
    "p95_recovery_candidate": "ppopt243_linear_residual__model=huber_1p15__s=0p22__cap=3em05__shrink=0p5",
    "p95_recovery_fixed_test_MAPE": 0.2698902774922426,
    "p95_recovery_fixed_test_p95_APE": 0.8073212838975509,
    "p95_recovery_delta_vs_pp64_MAPE": -0.0006737644234177664,
    "p95_recovery_delta_vs_pp64_p95_APE": -0.00017756840855898126,
    "p95_recovery_delta_vs_pp234_MAPE": 7.799242011663488e-07,
    "p95_recovery_delta_vs_pp234_p95_win_rate": 0.06634615384615405,
    "p95_recovery_delta_vs_pp240_operational_MAPE": 1.169713868542921e-06,
    "p95_recovery_avg_pp64_MAPE_win_rate": 0.9541666666666666,
    "p95_recovery_avg_pp64_p95_win_rate": 0.8141025641025642,
    "p95_recovery_replacement_score": -0.01884043109008443,
    "p95_guarded_label": "pp234_p95_guarded_reference",
    "p95_guarded_candidate": "ppopt234_p95_guarded_pp228_p95_recovery__source=ppopt228_p95_guarded_pp222_narrow_balance__source_ppopt222_p95_guarded_p95_regularized_rebuild__source_ppopt210_p95_guar",
    "p95_guarded_fixed_test_MAPE": 0.26994920114208765,
    "p95_guarded_fixed_test_p95_APE": 0.8072545738314347,
    "p95_guarded_delta_vs_pp64_MAPE": -0.0006148407735727113,
    "p95_guarded_delta_vs_pp64_p95_APE": -0.0002442784746751192,
    "p95_guarded_delta_vs_pp234_MAPE": 5.970357404622151e-05,
    "p95_guarded_delta_vs_pp234_p95_win_rate": 0.0038461538461540545,
    "p95_guarded_delta_vs_pp240_operational_MAPE": 6.009336371359808e-05,
    "p95_guarded_avg_pp64_MAPE_win_rate": 0.9509615384615384,
    "p95_guarded_avg_pp64_p95_win_rate": 0.7516025641025642,
    "p95_guarded_replacement_score": -0.01865330231203425,
    "p95_extreme_label": "pp240_p95_extreme_reference",
    "p95_extreme_candidate": "ppopt240_p95_extreme_pp234_learned_router__source=ppopt234_p95_extreme_pp228_p95_recovery__source_ppopt228_p95_extreme_pp222_narrow_balance__source_reference_pp148_p95",
    "p95_extreme_fixed_test_MAPE": 0.27026892590910795,
    "p95_extreme_fixed_test_p95_APE": 0.8059493758221674,
    "p95_extreme_delta_vs_pp64_MAPE": -0.00029511600655240944,
    "p95_extreme_delta_vs_pp64_p95_APE": -0.0015494764839424358,
    "p95_extreme_delta_vs_pp234_MAPE": 0.00037942834106652334,
    "p95_extreme_delta_vs_pp234_p95_win_rate": -0.2467948717948717,
    "p95_extreme_delta_vs_pp240_operational_MAPE": 0.0003798181307338999,
    "p95_extreme_avg_pp64_MAPE_win_rate": 0.5983974358974359,
    "p95_extreme_avg_pp64_p95_win_rate": 0.5009615384615385,
    "p95_extreme_replacement_score": -0.0040792899192624915,
    "operational_protocol_candidate": "ppopt246_operational_pp234_p95_constrained__source=ppopt240_mape_challenger_pp234_learned_router__source_ppopt236_segment_winner__seg_price_conf__minn_15__gain_0p0__cap_0p",
    "balanced_protocol_candidate": "ppopt246_balanced_pp234_p95_constrained__source=ppopt241_p95_support__src_s3__seg_price_conf__s_0p22__cap_0p0001__shrink_0p5",
    "mape_challenger_protocol_candidate": "ppopt246_mape_challenger_pp234_p95_constrained__source=ppopt240_mape_challenger_pp234_learned_router__source_ppopt236_segment_winner__seg_price_conf__minn_15__gain_0p0__cap_0p",
    "p95_recovery_protocol_candidate": "ppopt246_p95_recovery_pp234_p95_constrained__source=ppopt243_linear_residual__model_huber_1p15__s_0p22__cap_3em05__shrink_0p5",
    "p95_guarded_protocol_candidate": "ppopt246_p95_guarded_pp234_p95_constrained__source=ppopt234_p95_guarded_pp228_p95_recovery__source_ppopt228_p95_guarded_pp222_narrow_balance__source_ppopt222_p95_guarded_p",
    "p95_extreme_protocol_candidate": "ppopt246_p95_extreme_pp234_p95_constrained__source=ppopt240_p95_extreme_pp234_learned_router__source_ppopt234_p95_extreme_pp228_p95_recovery__source_ppopt228_p95_extreme_p"
  },
  "pp234_decision": {
    "operational_label": "candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve___49fa782c9b",
    "operational_candidate": "ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00018__shrink=0p55__curve=1p25",
    "operational_fixed_test_MAPE": 0.2698894975680414,
    "operational_fixed_test_p95_APE": 0.8073255046591389,
    "operational_delta_vs_pp64_MAPE": -0.0006745443476189328,
    "operational_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "operational_delta_vs_pp228_balanced_MAPE": -5.257381030521202e-09,
    "operational_delta_vs_pp228_balanced_p95_win_rate": 0.0,
    "operational_delta_vs_pp228_operational_MAPE": 3.8978966737657217e-07,
    "operational_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "operational_avg_pp64_p95_win_rate": 0.7477564102564102,
    "operational_replacement_score": -0.01882839050146509,
    "balanced_label": "candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve___49fa782c9b",
    "balanced_candidate": "ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00018__shrink=0p55__curve=1p25",
    "balanced_fixed_test_MAPE": 0.2698894975680414,
    "balanced_fixed_test_p95_APE": 0.8073255046591389,
    "balanced_delta_vs_pp64_MAPE": -0.0006745443476189328,
    "balanced_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "balanced_delta_vs_pp228_balanced_MAPE": -5.257381030521202e-09,
    "balanced_delta_vs_pp228_balanced_p95_win_rate": 0.0,
    "balanced_delta_vs_pp228_operational_MAPE": 3.8978966737657217e-07,
    "balanced_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "balanced_avg_pp64_p95_win_rate": 0.7477564102564102,
    "balanced_replacement_score": -0.01882839050146509,
    "mape_challenger_label": "candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve___49fa782c9b",
    "mape_challenger_candidate": "ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00018__shrink=0p55__curve=1p25",
    "mape_challenger_fixed_test_MAPE": 0.2698894975680414,
    "mape_challenger_fixed_test_p95_APE": 0.8073255046591389,
    "mape_challenger_delta_vs_pp64_MAPE": -0.0006745443476189328,
    "mape_challenger_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "mape_challenger_delta_vs_pp228_balanced_MAPE": -5.257381030521202e-09,
    "mape_challenger_delta_vs_pp228_balanced_p95_win_rate": 0.0,
    "mape_challenger_delta_vs_pp228_operational_MAPE": 3.8978966737657217e-07,
    "mape_challenger_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "mape_challenger_avg_pp64_p95_win_rate": 0.7477564102564102,
    "mape_challenger_replacement_score": -0.01882839050146509,
    "p95_recovery_label": "candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve___49fa782c9b",
    "p95_recovery_candidate": "ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00018__shrink=0p55__curve=1p25",
    "p95_recovery_fixed_test_MAPE": 0.2698894975680414,
    "p95_recovery_fixed_test_p95_APE": 0.8073255046591389,
    "p95_recovery_delta_vs_pp64_MAPE": -0.0006745443476189328,
    "p95_recovery_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "p95_recovery_delta_vs_pp228_balanced_MAPE": -5.257381030521202e-09,
    "p95_recovery_delta_vs_pp228_balanced_p95_win_rate": 0.0,
    "p95_recovery_delta_vs_pp228_operational_MAPE": 3.8978966737657217e-07,
    "p95_recovery_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "p95_recovery_avg_pp64_p95_win_rate": 0.7477564102564102,
    "p95_recovery_replacement_score": -0.01882839050146509,
    "p95_guarded_label": "pp228_p95_guarded_reference",
    "p95_guarded_candidate": "ppopt228_p95_guarded_pp222_narrow_balance__source=ppopt222_p95_guarded_p95_regularized_rebuild__source_ppopt210_p95_guarded_pp204_local_refinement__source_ppopt204_p95_gu",
    "p95_guarded_fixed_test_MAPE": 0.26994920114208765,
    "p95_guarded_fixed_test_p95_APE": 0.8072545738314347,
    "p95_guarded_delta_vs_pp64_MAPE": -0.0006148407735727113,
    "p95_guarded_delta_vs_pp64_p95_APE": -0.0002442784746751192,
    "p95_guarded_delta_vs_pp228_balanced_MAPE": 5.969831666519099e-05,
    "p95_guarded_delta_vs_pp228_balanced_p95_win_rate": 0.0038461538461540545,
    "p95_guarded_delta_vs_pp228_operational_MAPE": 6.009336371359808e-05,
    "p95_guarded_avg_pp64_MAPE_win_rate": 0.9509615384615384,
    "p95_guarded_avg_pp64_p95_win_rate": 0.7516025641025642,
    "p95_guarded_replacement_score": -0.01865330231203425,
    "p95_extreme_label": "pp228_p95_extreme_reference",
    "p95_extreme_candidate": "ppopt228_p95_extreme_pp222_narrow_balance__source=reference_pp148_p95",
    "p95_extreme_fixed_test_MAPE": 0.27026892590910795,
    "p95_extreme_fixed_test_p95_APE": 0.8059493758221674,
    "p95_extreme_delta_vs_pp64_MAPE": -0.00029511600655240944,
    "p95_extreme_delta_vs_pp64_p95_APE": -0.0015494764839424358,
    "p95_extreme_delta_vs_pp228_balanced_MAPE": 0.0003794230836854928,
    "p95_extreme_delta_vs_pp228_balanced_p95_win_rate": -0.2467948717948717,
    "p95_extreme_delta_vs_pp228_operational_MAPE": 0.0003798181307338999,
    "p95_extreme_avg_pp64_MAPE_win_rate": 0.5983974358974359,
    "p95_extreme_avg_pp64_p95_win_rate": 0.5009615384615385,
    "p95_extreme_replacement_score": -0.0040792899192624915,
    "operational_protocol_candidate": "ppopt234_operational_pp228_p95_recovery__source=ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve_1p25",
    "balanced_protocol_candidate": "ppopt234_balanced_pp228_p95_recovery__source=ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve_1p25",
    "mape_challenger_protocol_candidate": "ppopt234_mape_challenger_pp228_p95_recovery__source=ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve_1p25",
    "p95_recovery_protocol_candidate": "ppopt234_p95_recovery_pp228_p95_recovery__source=ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve_1p25",
    "p95_guarded_protocol_candidate": "ppopt234_p95_guarded_pp228_p95_recovery__source=ppopt228_p95_guarded_pp222_narrow_balance__source_ppopt222_p95_guarded_p95_regularized_rebuild__source_ppopt210_p95_guar",
    "p95_extreme_protocol_candidate": "ppopt234_p95_extreme_pp228_p95_recovery__source=ppopt228_p95_extreme_pp222_narrow_balance__source_reference_pp148_p95"
  },
  "pp240_decision": {
    "operational_label": "candidate_ppopt236_segment_winner__seg_price_conf__minn_15__gain_0p0__cap_0p00045__shrink_0p5__0e1d316316",
    "operational_candidate": "ppopt236_segment_winner__seg=price_conf__minn=15__gain=0p0__cap=0p00045__shrink=0p5",
    "operational_fixed_test_MAPE": 0.26988910777837405,
    "operational_fixed_test_p95_APE": 0.8073255046591389,
    "operational_delta_vs_pp64_MAPE": -0.0006749341372863094,
    "operational_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "operational_delta_vs_pp234_MAPE": -3.8978966737657217e-07,
    "operational_delta_vs_pp234_p95_win_rate": -0.0006410256410256387,
    "operational_delta_vs_pp228_operational_MAPE": 0.0,
    "operational_avg_pp64_MAPE_win_rate": 0.9541666666666666,
    "operational_avg_pp64_p95_win_rate": 0.7471153846153845,
    "operational_replacement_score": -0.018841600803952974,
    "balanced_label": "candidate_ppopt235_pp234_significance_audit_anchor__47f2cd9b74",
    "balanced_candidate": "ppopt235_pp234_significance_audit_anchor",
    "balanced_fixed_test_MAPE": 0.2698894975680414,
    "balanced_fixed_test_p95_APE": 0.8073255046591389,
    "balanced_delta_vs_pp64_MAPE": -0.0006745443476189328,
    "balanced_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "balanced_delta_vs_pp234_MAPE": 0.0,
    "balanced_delta_vs_pp234_p95_win_rate": 0.0,
    "balanced_delta_vs_pp228_operational_MAPE": 3.8978966737657217e-07,
    "balanced_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "balanced_avg_pp64_p95_win_rate": 0.7477564102564102,
    "balanced_replacement_score": -0.01882839050146509,
    "mape_challenger_label": "candidate_ppopt236_segment_winner__seg_price_conf__minn_15__gain_0p0__cap_0p00045__shrink_0p5__0e1d316316",
    "mape_challenger_candidate": "ppopt236_segment_winner__seg=price_conf__minn=15__gain=0p0__cap=0p00045__shrink=0p5",
    "mape_challenger_fixed_test_MAPE": 0.26988910777837405,
    "mape_challenger_fixed_test_p95_APE": 0.8073255046591389,
    "mape_challenger_delta_vs_pp64_MAPE": -0.0006749341372863094,
    "mape_challenger_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "mape_challenger_delta_vs_pp234_MAPE": -3.8978966737657217e-07,
    "mape_challenger_delta_vs_pp234_p95_win_rate": -0.0006410256410256387,
    "mape_challenger_delta_vs_pp228_operational_MAPE": 0.0,
    "mape_challenger_avg_pp64_MAPE_win_rate": 0.9541666666666666,
    "mape_challenger_avg_pp64_p95_win_rate": 0.7471153846153845,
    "mape_challenger_replacement_score": -0.018841600803952974,
    "p95_recovery_label": "candidate_ppopt239_probability_blend__probs_multiclass_c0p6_seed17__thr_0p35__s_0p8__cap_0p0001__f511ed44fa",
    "p95_recovery_candidate": "ppopt239_probability_blend__probs=multiclass_c0p6_seed17__thr=0p35__s=0p8__cap=0p0001",
    "p95_recovery_fixed_test_MAPE": 0.26989020449203693,
    "p95_recovery_fixed_test_p95_APE": 0.8073230727405295,
    "p95_recovery_delta_vs_pp64_MAPE": -0.0006738374236234246,
    "p95_recovery_delta_vs_pp64_p95_APE": -0.00017577956558034735,
    "p95_recovery_delta_vs_pp234_MAPE": 7.069239955082018e-07,
    "p95_recovery_delta_vs_pp234_p95_win_rate": 0.07916666666666683,
    "p95_recovery_delta_vs_pp228_operational_MAPE": 1.096713662884774e-06,
    "p95_recovery_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "p95_recovery_avg_pp64_p95_win_rate": 0.826923076923077,
    "p95_recovery_replacement_score": -0.01882768357746958,
    "p95_guarded_label": "pp234_p95_guarded_reference",
    "p95_guarded_candidate": "ppopt234_p95_guarded_pp228_p95_recovery__source=ppopt228_p95_guarded_pp222_narrow_balance__source_ppopt222_p95_guarded_p95_regularized_rebuild__source_ppopt210_p95_guar",
    "p95_guarded_fixed_test_MAPE": 0.26994920114208765,
    "p95_guarded_fixed_test_p95_APE": 0.8072545738314347,
    "p95_guarded_delta_vs_pp64_MAPE": -0.0006148407735727113,
    "p95_guarded_delta_vs_pp64_p95_APE": -0.0002442784746751192,
    "p95_guarded_delta_vs_pp234_MAPE": 5.970357404622151e-05,
    "p95_guarded_delta_vs_pp234_p95_win_rate": 0.0038461538461540545,
    "p95_guarded_delta_vs_pp228_operational_MAPE": 6.009336371359808e-05,
    "p95_guarded_avg_pp64_MAPE_win_rate": 0.9509615384615384,
    "p95_guarded_avg_pp64_p95_win_rate": 0.7516025641025642,
    "p95_guarded_replacement_score": -0.01865330231203425,
    "p95_extreme_label": "pp234_p95_extreme_reference",
    "p95_extreme_candidate": "ppopt234_p95_extreme_pp228_p95_recovery__source=ppopt228_p95_extreme_pp222_narrow_balance__source_reference_pp148_p95",
    "p95_extreme_fixed_test_MAPE": 0.27026892590910795,
    "p95_extreme_fixed_test_p95_APE": 0.8059493758221674,
    "p95_extreme_delta_vs_pp64_MAPE": -0.00029511600655240944,
    "p95_extreme_delta_vs_pp64_p95_APE": -0.0015494764839424358,
    "p95_extreme_delta_vs_pp234_MAPE": 0.00037942834106652334,
    "p95_extreme_delta_vs_pp234_p95_win_rate": -0.2467948717948717,
    "p95_extreme_delta_vs_pp228_operational_MAPE": 0.0003798181307338999,
    "p95_extreme_avg_pp64_MAPE_win_rate": 0.5983974358974359,
    "p95_extreme_avg_pp64_p95_win_rate": 0.5009615384615385,
    "p95_extreme_replacement_score": -0.0040792899192624915,
    "operational_protocol_candidate": "ppopt240_operational_pp234_learned_router__source=ppopt236_segment_winner__seg_price_conf__minn_15__gain_0p0__cap_0p00045__shrink_0p5",
    "balanced_protocol_candidate": "ppopt240_balanced_pp234_learned_router__source=ppopt235_pp234_significance_audit_anchor",
    "mape_challenger_protocol_candidate": "ppopt240_mape_challenger_pp234_learned_router__source=ppopt236_segment_winner__seg_price_conf__minn_15__gain_0p0__cap_0p00045__shrink_0p5",
    "p95_recovery_protocol_candidate": "ppopt240_p95_recovery_pp234_learned_router__source=ppopt239_probability_blend__probs_multiclass_c0p6_seed17__thr_0p35__s_0p8__cap_0p0001",
    "p95_guarded_protocol_candidate": "ppopt240_p95_guarded_pp234_learned_router__source=ppopt234_p95_guarded_pp228_p95_recovery__source_ppopt228_p95_guarded_pp222_narrow_balance__source_ppopt222_p95_guarded_p",
    "p95_extreme_protocol_candidate": "ppopt240_p95_extreme_pp234_learned_router__source=ppopt234_p95_extreme_pp228_p95_recovery__source_ppopt228_p95_extreme_pp222_narrow_balance__source_reference_pp148_p95"
  },
  "selection_decision": {
    "operational_label": "candidate_ppopt250_segment_direction_router__seg_price_conf_qwidth__minn_8__gain_0p0__s_0p35__cap_3em0__8fa3e0236b",
    "operational_candidate": "ppopt250_segment_direction_router__seg=price_conf_qwidth__minn=8__gain=0p0__s=0p35__cap=3em05",
    "operational_fixed_test_MAPE": 0.2698897743909076,
    "operational_fixed_test_p95_APE": 0.8073255046591389,
    "operational_delta_vs_pp64_MAPE": -0.0006742675247527474,
    "operational_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "operational_delta_vs_pp246_MAPE": 2.841251309781967e-07,
    "operational_delta_vs_pp246_p95_win_rate": 0.06891025641025661,
    "operational_avg_pp64_MAPE_win_rate": 0.9541666666666666,
    "operational_avg_pp64_p95_win_rate": 0.8166666666666668,
    "operational_replacement_score": -0.01884093419141941,
    "balanced_label": "candidate_ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_huber_1p15__rs_0p05__ps_0p04____dda3fdcffe",
    "balanced_candidate": "ppopt251_residual_support_ensemble__prob=hist35_seed17__resid=huber_1p15__rs=0p05__ps=0p04__cap=0p0001",
    "balanced_fixed_test_MAPE": 0.26988873087551646,
    "balanced_fixed_test_p95_APE": 0.8073244865475181,
    "balanced_delta_vs_pp64_MAPE": -0.0006753110401439,
    "balanced_delta_vs_pp64_p95_APE": -0.00017436575859175463,
    "balanced_delta_vs_pp246_MAPE": -7.59390260174353e-07,
    "balanced_delta_vs_pp246_p95_win_rate": 0.04102564102564121,
    "balanced_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "balanced_avg_pp64_p95_win_rate": 0.7887820512820514,
    "balanced_replacement_score": -0.018829157193990056,
    "mape_challenger_label": "candidate_ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_huber_1p15__rs_0p05__ps_0p04____dda3fdcffe",
    "mape_challenger_candidate": "ppopt251_residual_support_ensemble__prob=hist35_seed17__resid=huber_1p15__rs=0p05__ps=0p04__cap=0p0001",
    "mape_challenger_fixed_test_MAPE": 0.26988873087551646,
    "mape_challenger_fixed_test_p95_APE": 0.8073244865475181,
    "mape_challenger_delta_vs_pp64_MAPE": -0.0006753110401439,
    "mape_challenger_delta_vs_pp64_p95_APE": -0.00017436575859175463,
    "mape_challenger_delta_vs_pp246_MAPE": -7.59390260174353e-07,
    "mape_challenger_delta_vs_pp246_p95_win_rate": 0.04102564102564121,
    "mape_challenger_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "mape_challenger_avg_pp64_p95_win_rate": 0.7887820512820514,
    "mape_challenger_replacement_score": -0.018829157193990056,
    "p95_recovery_label": "candidate_ppopt249_direction_residual__prob_hist35_seed17__resid_huber_1p15__thr_0p1__s_0p14__up_8em05__d96d0de51f",
    "p95_recovery_candidate": "ppopt249_direction_residual__prob=hist35_seed17__resid=huber_1p15__thr=0p1__s=0p14__up=8em05__down=4em05",
    "p95_recovery_fixed_test_MAPE": 0.2698905665651174,
    "p95_recovery_fixed_test_p95_APE": 0.8073206977096223,
    "p95_recovery_delta_vs_pp64_MAPE": -0.0006734753505429625,
    "p95_recovery_delta_vs_pp64_p95_APE": -0.00017815459648751197,
    "p95_recovery_delta_vs_pp246_MAPE": 1.0762993407631427e-06,
    "p95_recovery_delta_vs_pp246_p95_win_rate": 0.04166666666666685,
    "p95_recovery_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "p95_recovery_avg_pp64_p95_win_rate": 0.789423076923077,
    "p95_recovery_replacement_score": -0.01882732150438912,
    "p95_guarded_label": "pp246_p95_guarded_reference",
    "p95_guarded_candidate": "ppopt246_p95_guarded_pp234_p95_constrained__source=ppopt234_p95_guarded_pp228_p95_recovery__source_ppopt228_p95_guarded_pp222_narrow_balance__source_ppopt222_p95_guarded_p",
    "p95_guarded_fixed_test_MAPE": 0.26994920114208765,
    "p95_guarded_fixed_test_p95_APE": 0.8072545738314347,
    "p95_guarded_delta_vs_pp64_MAPE": -0.0006148407735727113,
    "p95_guarded_delta_vs_pp64_p95_APE": -0.0002442784746751192,
    "p95_guarded_delta_vs_pp246_MAPE": 5.971087631101435e-05,
    "p95_guarded_delta_vs_pp246_p95_win_rate": 0.0038461538461540545,
    "p95_guarded_avg_pp64_MAPE_win_rate": 0.9509615384615384,
    "p95_guarded_avg_pp64_p95_win_rate": 0.7516025641025642,
    "p95_guarded_replacement_score": -0.01865330231203425,
    "p95_extreme_label": "pp246_p95_extreme_reference",
    "p95_extreme_candidate": "ppopt246_p95_extreme_pp234_p95_constrained__source=ppopt240_p95_extreme_pp234_learned_router__source_ppopt234_p95_extreme_pp228_p95_recovery__source_ppopt228_p95_extreme_p",
    "p95_extreme_fixed_test_MAPE": 0.27026892590910795,
    "p95_extreme_fixed_test_p95_APE": 0.8059493758221674,
    "p95_extreme_delta_vs_pp64_MAPE": -0.00029511600655240944,
    "p95_extreme_delta_vs_pp64_p95_APE": -0.0015494764839424358,
    "p95_extreme_delta_vs_pp246_MAPE": 0.0003794356433313162,
    "p95_extreme_delta_vs_pp246_p95_win_rate": -0.2467948717948717,
    "p95_extreme_avg_pp64_MAPE_win_rate": 0.5983974358974359,
    "p95_extreme_avg_pp64_p95_win_rate": 0.5009615384615385,
    "p95_extreme_replacement_score": -0.0040792899192624915,
    "operational_protocol_candidate": "ppopt252_operational_pp246_gated_correction__source=ppopt250_segment_direction_router__seg_price_conf_qwidth__minn_8__gain_0p0__s_0p35__cap_3em05",
    "balanced_protocol_candidate": "ppopt252_balanced_pp246_gated_correction__source=ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_huber_1p15__rs_0p05__ps_0p04__cap_0p0001",
    "mape_challenger_protocol_candidate": "ppopt252_mape_challenger_pp246_gated_correction__source=ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_huber_1p15__rs_0p05__ps_0p04__cap_0p0001",
    "p95_recovery_protocol_candidate": "ppopt252_p95_recovery_pp246_gated_correction__source=ppopt249_direction_residual__prob_hist35_seed17__resid_huber_1p15__thr_0p1__s_0p14__up_8em05__down_4em05",
    "p95_guarded_protocol_candidate": "ppopt252_p95_guarded_pp246_gated_correction__source=ppopt246_p95_guarded_pp234_p95_constrained__source_ppopt234_p95_guarded_pp228_p95_recovery__source_ppopt228_p95_guarded_",
    "p95_extreme_protocol_candidate": "ppopt252_p95_extreme_pp246_gated_correction__source=ppopt246_p95_extreme_pp234_p95_constrained__source_ppopt240_p95_extreme_pp234_learned_router__source_ppopt234_p95_extrem"
  },
  "available_direction_models": {
    "logistic": true,
    "hist_gradient_boosting": true,
    "lightgbm": true,
    "catboost": true
  },
  "available_residual_models": {
    "ridge": true,
    "huber": true,
    "hist_gradient_boosting": true,
    "lightgbm": true,
    "catboost": true
  },
  "items": [
    {
      "item_id": "PP-OPT247",
      "priority": "1",
      "title": "residual direction probability gate",
      "description": "validation residual sign classifier로 보정 방향을 먼저 고른 뒤 후보 이동량을 제한 적용."
    },
    {
      "item_id": "PP-OPT248",
      "priority": "2",
      "title": "asymmetric quantile residual cap",
      "description": "잔차 보정의 상향 cap과 하향 cap을 quantile width/risk에 따라 따로 적용."
    },
    {
      "item_id": "PP-OPT249",
      "priority": "3",
      "title": "direction-gated residual correction",
      "description": "잔차 회귀값이 방향 분류 확신과 일치할 때만 Huber/Ridge/LightGBM 계열 보정을 적용."
    },
    {
      "item_id": "PP-OPT250",
      "priority": "4",
      "title": "segment residual-direction router",
      "description": "구간별 validation 성과와 잔차 방향을 함께 사용해 후보별 이동을 제한 라우팅."
    },
    {
      "item_id": "PP-OPT251",
      "priority": "5",
      "title": "direction residual plus p95 support ensemble",
      "description": "방향 gate 잔차 보정과 p95 recovery/support 이동을 신뢰도 가중 평균으로 결합."
    },
    {
      "item_id": "PP-OPT252",
      "priority": "6",
      "title": "final PP246 gated correction decision",
      "description": "PP246 대비 MAPE, p95 win rate, replacement score 제약을 만족하는 후보를 최종 선택."
    }
  ],
  "formula": {
    "base": "PP246 balanced log price",
    "direction_gate": "prob_up = classifier(features); correction applied only when sign(candidate_delta) matches sign(prob_up - 0.5)",
    "asymmetric_cap": "cap = direction_cap * (1 - q_shrink * quantile_width_rank) * (1 - risk_shrink * row_risk)",
    "final_log_price": "PP246_log + clip(correction_log, asymmetric_row_cap)",
    "selection_goal": "MAPE <= PP246 + 0.000001, repeated p95 win rate >= PP246, replacement score <= PP246 + 0.000002"
  }
}
```