# PP-OPT253~258 Warm PP252 narrow direction-residual support refinement 결과

- 작성일: 2026-06-10 13:32
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 목적: PP252 최선 조합 주변의 residual/support strength/cap을 좁게 재탐색
- 결론: 균형 후보 MAPE 0.269888, PP252 대비 MAPE 변화 -0.000000535. stability 후보 p95 win rate 0.816667.

## 주요 후보 test 비교
| candidate | family | item_id | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt258_operational_pp252_narrow_refinement__source=ppopt256_pp252_residual_continue__thr_0p12__rs_0p025__ss_0p0__cap_5em05 | pp252_narrow_operational_selection | PP-OPT258 | 0.140976 | 0.269888 | 0.807325 | 0.397454 | -0.001507 | -0.000805 |
| ppopt258_balanced_pp252_narrow_refinement__source=ppopt256_pp252_residual_continue__thr_0p12__rs_0p025__ss_0p0__cap_5em05 | pp252_narrow_balanced_selection | PP-OPT258 | 0.140976 | 0.269888 | 0.807325 | 0.397454 | -0.001507 | -0.000805 |
| ppopt258_mape_challenger_pp252_narrow_refinement__source=ppopt256_pp252_residual_continue__thr_0p12__rs_0p025__ss_0p0__cap_5em05 | pp252_narrow_mape_selection | PP-OPT258 | 0.140976 | 0.269888 | 0.807325 | 0.397454 | -0.001507 | -0.000805 |
| ppopt252_balanced_pp246_gated_correction__source=ppopt251_residual_support_ensemble__prob_hist35_seed17__resid_huber_1p15__rs_0p05__ps_0p04__cap_0p0001 | reference_prior | REFERENCE | 0.140975 | 0.269889 | 0.807324 | 0.397454 | -0.001506 | -0.000805 |
| ppopt258_p95_recovery_pp252_narrow_refinement__source=ppopt253_narrow_hist35_huber_support__thr_0p12__rs_0p06__ps_0p05__rec_0p03__cap_0p00012__q_0p45 | pp252_narrow_p95_recovery_selection | PP-OPT258 | 0.140975 | 0.269889 | 0.807323 | 0.397454 | -0.001506 | -0.000807 |
| ppopt252_operational_pp246_gated_correction__source=ppopt250_segment_direction_router__seg_price_conf_qwidth__minn_8__gain_0p0__s_0p35__cap_3em05 | reference_prior | REFERENCE | 0.140975 | 0.269890 | 0.807326 | 0.397456 | -0.001505 | -0.000804 |
| ppopt258_stability_pp252_narrow_refinement__source=ppopt252_operational_pp246_gated_correction__source_ppopt250_segment_direction_router__seg_price_conf_qwidth__minn_8__ga | pp252_narrow_stability_selection | PP-OPT258 | 0.140975 | 0.269890 | 0.807326 | 0.397456 | -0.001505 | -0.000804 |
| ppopt252_p95_recovery_pp246_gated_correction__source=ppopt249_direction_residual__prob_hist35_seed17__resid_huber_1p15__thr_0p1__s_0p14__up_8em05__down_4em05 | reference_prior | REFERENCE | 0.140975 | 0.269891 | 0.807321 | 0.397455 | -0.001504 | -0.000809 |
| reference_pp64_current_best | reference_prior | REFERENCE | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | p95_test_MAPE | p95_test_p95_APE | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4 | PP252 source residual continuation | 54 | 0.269888 | 0.807325 | 0.269888 | 0.807324 | pp252_residual_continuation | ppopt256_pp252_residual_continue__thr=0p12__rs=0p025__ss=0p0__cap=5em05 |
| 6 | final PP252 narrow refinement decision | 7 | 0.269888 | 0.807325 | 0.270269 | 0.805949 | pp252_narrow_balanced_selection | ppopt258_balanced_pp252_narrow_refinement__source=ppopt256_pp252_residual_continue__thr_0p12__rs_0p025__ss_0p0__cap_5em05 |
| 1 | narrow hist35 Huber support refinement | 1350 | 0.269888 | 0.807325 | 0.269889 | 0.807323 | pp252_narrow_hist35_huber_support | ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p03__rec=0p01__cap=0p00012__q=0p45 |
| 2 | confidence threshold and cap split refinement | 48 | 0.269888 | 0.807324 | 0.269888 | 0.807324 | pp252_cap_split_refinement | ppopt254_cap_split_refine__up=0p0001__down=7em05__q=0p35__risk=0p65 |
| 5 | direction probability ensemble refinement | 81 | 0.269888 | 0.807325 | 0.269889 | 0.807322 | pp252_probability_ensemble_refinement | ppopt257_prob_ensemble__p=h35_log_80_20__rs=0p04__ps=0p03__cap=0p00012 |
| 3 | weak stability add-on from PP250 | 48 | 0.269889 | 0.807324 | 0.269889 | 0.807324 | pp252_weak_stability_addon | ppopt255_stability_addon__ss=0p01__rs=0p0__cap=1em05 |

## 탐색 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt258_p95_guarded_pp252_narrow_refinement__source=ppopt252_p95_guarded_pp246_gated_correction__source_ppopt246_p95_guarded_pp234_p95_constrained__source_ppopt234_p95_guar | PP-OPT258 | pp252_narrow_p95_guarded_selection | 0.269949 | 0.807255 | -0.001446 | -0.000875 | -0.001537 |
| ppopt258_stability_pp252_narrow_refinement__source=ppopt252_operational_pp246_gated_correction__source_ppopt250_segment_direction_router__seg_price_conf_qwidth__minn_8__ga | PP-OPT258 | pp252_narrow_stability_selection | 0.269890 | 0.807326 | -0.001505 | -0.000804 | -0.001413 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p03__rec=0p01__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p03__rec=0p02__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p035__rec=0p01__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p03__rec=0p03__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p035__rec=0p02__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p04__rec=0p01__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p035__rec=0p03__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p04__rec=0p02__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p045__rec=0p01__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p04__rec=0p03__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p045__rec=0p02__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p05__rec=0p01__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p045__rec=0p03__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p05__rec=0p02__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p05__rec=0p03__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p045__ps=0p03__rec=0p01__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p045__ps=0p03__rec=0p02__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p045__ps=0p035__rec=0p01__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p045__ps=0p03__rec=0p03__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p045__ps=0p035__rec=0p02__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p045__ps=0p04__rec=0p01__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p045__ps=0p035__rec=0p03__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p045__ps=0p04__rec=0p02__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p045__ps=0p045__rec=0p01__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p045__ps=0p04__rec=0p03__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p045__ps=0p045__rec=0p02__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p045__ps=0p05__rec=0p01__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p045__ps=0p045__rec=0p03__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p045__ps=0p05__rec=0p02__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p045__ps=0p05__rec=0p03__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p05__ps=0p03__rec=0p01__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p05__ps=0p03__rec=0p02__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p05__ps=0p035__rec=0p01__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p05__ps=0p03__rec=0p03__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p05__ps=0p035__rec=0p02__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p05__ps=0p04__rec=0p01__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p05__ps=0p035__rec=0p03__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p05__ps=0p04__rec=0p02__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p05__ps=0p045__rec=0p01__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p05__ps=0p04__rec=0p03__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p05__ps=0p045__rec=0p02__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p05__ps=0p05__rec=0p01__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p05__ps=0p045__rec=0p03__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p05__ps=0p05__rec=0p02__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p05__ps=0p05__rec=0p03__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p055__ps=0p03__rec=0p01__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p055__ps=0p03__rec=0p02__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p055__ps=0p035__rec=0p01__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p055__ps=0p03__rec=0p03__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p055__ps=0p035__rec=0p02__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p055__ps=0p04__rec=0p01__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p055__ps=0p035__rec=0p03__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p055__ps=0p04__rec=0p02__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p055__ps=0p045__rec=0p01__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p055__ps=0p04__rec=0p03__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p055__ps=0p045__rec=0p02__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p055__ps=0p05__rec=0p01__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p055__ps=0p045__rec=0p03__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p055__ps=0p05__rec=0p02__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p055__ps=0p05__rec=0p03__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p03__rec=0p01__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p03__rec=0p02__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p035__rec=0p01__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p03__rec=0p03__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p035__rec=0p02__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p04__rec=0p01__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p035__rec=0p03__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p04__rec=0p02__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p045__rec=0p01__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p04__rec=0p03__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p045__rec=0p02__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p05__rec=0p01__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p045__rec=0p03__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p05__rec=0p02__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p04__ps=0p05__rec=0p03__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p045__ps=0p03__rec=0p01__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p045__ps=0p03__rec=0p02__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p045__ps=0p035__rec=0p01__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p045__ps=0p03__rec=0p03__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p045__ps=0p035__rec=0p02__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p045__ps=0p04__rec=0p01__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p045__ps=0p035__rec=0p03__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p045__ps=0p04__rec=0p02__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p045__ps=0p045__rec=0p01__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p045__ps=0p04__rec=0p03__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p045__ps=0p045__rec=0p02__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p045__ps=0p05__rec=0p01__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p045__ps=0p045__rec=0p03__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p045__ps=0p05__rec=0p02__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p045__ps=0p05__rec=0p03__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p06__ps=0p03__rec=0p01__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p06__ps=0p03__rec=0p02__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p06__ps=0p035__rec=0p01__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p06__ps=0p03__rec=0p03__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p06__ps=0p035__rec=0p02__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p06__ps=0p04__rec=0p01__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p06__ps=0p035__rec=0p03__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p06__ps=0p04__rec=0p02__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p06__ps=0p045__rec=0p01__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p06__ps=0p04__rec=0p03__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p06__ps=0p045__rec=0p02__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p06__ps=0p05__rec=0p01__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p06__ps=0p045__rec=0p03__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p06__ps=0p05__rec=0p02__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p06__ps=0p05__rec=0p03__cap=8em05__q=0p45 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p05__ps=0p03__rec=0p01__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p05__ps=0p03__rec=0p02__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p05__ps=0p035__rec=0p01__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p05__ps=0p03__rec=0p03__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p05__ps=0p035__rec=0p02__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p05__ps=0p04__rec=0p01__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p05__ps=0p035__rec=0p03__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p05__ps=0p04__rec=0p02__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p05__ps=0p045__rec=0p01__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p05__ps=0p04__rec=0p03__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p05__ps=0p045__rec=0p02__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p05__ps=0p05__rec=0p01__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p05__ps=0p045__rec=0p03__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p05__ps=0p05__rec=0p02__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p05__ps=0p05__rec=0p03__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt254_cap_split_refine__up=0p0001__down=7em05__q=0p65__risk=0p85 | PP-OPT254 | pp252_cap_split_refinement | 0.269889 | 0.807324 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p055__ps=0p03__rec=0p01__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p055__ps=0p03__rec=0p02__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p055__ps=0p035__rec=0p01__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p055__ps=0p03__rec=0p03__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p055__ps=0p035__rec=0p02__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p055__ps=0p04__rec=0p01__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p055__ps=0p035__rec=0p03__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p055__ps=0p04__rec=0p02__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p055__ps=0p045__rec=0p01__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p055__ps=0p04__rec=0p03__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p055__ps=0p045__rec=0p02__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p055__ps=0p05__rec=0p01__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p055__ps=0p045__rec=0p03__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p055__ps=0p05__rec=0p02__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p055__ps=0p05__rec=0p03__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt254_cap_split_refine__up=8em05__down=4em05__q=0p35__risk=0p85 | PP-OPT254 | pp252_cap_split_refinement | 0.269889 | 0.807324 | -0.001506 | -0.000805 | -0.001412 |
| ppopt254_cap_split_refine__up=8em05__down=4em05__q=0p45__risk=0p75 | PP-OPT254 | pp252_cap_split_refinement | 0.269889 | 0.807324 | -0.001506 | -0.000805 | -0.001412 |
| ppopt254_cap_split_refine__up=8em05__down=4em05__q=0p55__risk=0p65 | PP-OPT254 | pp252_cap_split_refinement | 0.269889 | 0.807324 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p06__ps=0p03__rec=0p01__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p06__ps=0p03__rec=0p02__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p06__ps=0p035__rec=0p01__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p06__ps=0p03__rec=0p03__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p06__ps=0p035__rec=0p02__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p06__ps=0p04__rec=0p01__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p06__ps=0p035__rec=0p03__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807325 | -0.001506 | -0.000805 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p06__ps=0p04__rec=0p02__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p06__ps=0p045__rec=0p01__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p06__ps=0p04__rec=0p03__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p06__ps=0p045__rec=0p02__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p06__ps=0p05__rec=0p01__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p06__ps=0p045__rec=0p03__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p06__ps=0p05__rec=0p02__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt253_narrow_hist35_huber_support__thr=0p14__rs=0p06__ps=0p05__rec=0p03__cap=8em05__q=0p55 | PP-OPT253 | pp252_narrow_hist35_huber_support | 0.269889 | 0.807324 | -0.001506 | -0.000806 | -0.001412 |
| ppopt254_cap_split_refine__up=8em05__down=4em05__q=0p45__risk=0p85 | PP-OPT254 | pp252_cap_split_refinement | 0.269889 | 0.807324 | -0.001506 | -0.000805 | -0.001412 |
| ppopt254_cap_split_refine__up=8em05__down=4em05__q=0p55__risk=0p75 | PP-OPT254 | pp252_cap_split_refinement | 0.269889 | 0.807324 | -0.001506 | -0.000805 | -0.001412 |
| ppopt254_cap_split_refine__up=0p0001__down=5em05__q=0p65__risk=0p85 | PP-OPT254 | pp252_cap_split_refinement | 0.269889 | 0.807324 | -0.001505 | -0.000805 | -0.001412 |
| ppopt254_cap_split_refine__up=8em05__down=4em05__q=0p65__risk=0p65 | PP-OPT254 | pp252_cap_split_refinement | 0.269889 | 0.807324 | -0.001506 | -0.000805 | -0.001412 |

## 선택 후보 반복 안정성
| candidate_label | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_vs_pp64_MAPE | fixed_test_delta_vs_pp64_p95_APE | avg_pp64_MAPE_win_rate | avg_pp64_p95_win_rate | replacement_score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pp240_operational_reference | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018842 |
| pp246_operational_reference | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018842 |
| pp252_operational_reference | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.954167 | 0.816667 | -0.018841 |
| pp258_stability_pp252_narrow_candidate | 0.269890 | 0.807326 | -0.000674 | -0.000173 | 0.954167 | 0.816667 | -0.018841 |
| pp246_p95_recovery_reference | 0.269890 | 0.807321 | -0.000674 | -0.000178 | 0.954167 | 0.814103 | -0.018840 |
| candidate_ppopt256_pp252_residual_continue__thr_0p12__rs_0p025__ss_0p0__cap_5em05__7f3a1e1f66 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018830 |
| pp258_balanced_pp252_narrow_candidate | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018830 |
| pp258_mape_pp252_narrow_candidate | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018830 |
| pp258_operational_pp252_narrow_candidate | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018830 |
| candidate_ppopt256_pp252_residual_continue__thr_0p12__rs_0p025__ss_0p015__cap_5em05__5a0a1a10a2 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018830 |
| candidate_ppopt256_pp252_residual_continue__thr_0p12__rs_0p025__ss_0p03__cap_5em05__e03b9bb62a | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018830 |
| candidate_ppopt256_pp252_residual_continue__thr_0p12__rs_0p04__ss_0p0__cap_5em05__10e0297d0e | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.787179 | -0.018830 |
| candidate_ppopt256_pp252_residual_continue__thr_0p12__rs_0p04__ss_0p015__cap_5em05__8956f50276 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.787179 | -0.018830 |
| candidate_ppopt256_pp252_residual_continue__thr_0p12__rs_0p04__ss_0p03__cap_5em05__1e8bb37f63 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.787179 | -0.018830 |
| candidate_ppopt256_pp252_residual_continue__thr_0p12__rs_0p055__ss_0p03__cap_5em05__4c3af5513d | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.787179 | -0.018830 |
| candidate_ppopt256_pp252_residual_continue__thr_0p12__rs_0p055__ss_0p015__cap_5em05__a895ceecda | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.787179 | -0.018830 |
| candidate_ppopt256_pp252_residual_continue__thr_0p12__rs_0p055__ss_0p0__cap_5em05__0be390b3af | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.787179 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p03__rec_0p01__cap_0p00012__q_0__9220694fe2 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p03__rec_0p02__cap_0p00012__q_0__afce030b48 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p03__rec_0p03__cap_0p00012__q_0__89e7e56c38 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p035__rec_0p01__cap_0p00012__q___0b662c5f21 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p035__rec_0p02__cap_0p00012__q___4261ac50f3 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p035__rec_0p03__cap_0p00012__q___e2fb34f042 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p04__rec_0p01__cap_0p00012__q_0__ed4839dced | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p04__rec_0p02__cap_0p00012__q_0__ece2c9277f | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p04__rec_0p03__cap_0p00012__q_0__1a663e1e7f | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p045__rec_0p01__cap_0p00012__q___78ba5e554a | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p045__rec_0p02__cap_0p00012__q___4e49ed105a | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p045__rec_0p03__cap_0p00012__q___79cfc29e52 | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p05__rec_0p01__cap_0p00012__q_0__8ceac62049 | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p05__rec_0p02__cap_0p00012__q_0__ba533b600a | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p05__rec_0p03__cap_0p00012__q_0__ea643516e4 | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018830 |
| candidate_ppopt254_cap_split_refine__up_0p0001__down_7em05__q_0p35__risk_0p65__825324512e | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p045__ps_0p03__rec_0p01__cap_0p00012__q___98ea294a41 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p045__ps_0p03__rec_0p02__cap_0p00012__q___c70bf67b39 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p045__ps_0p03__rec_0p03__cap_0p00012__q___ca7dd8e9ca | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p045__ps_0p035__rec_0p01__cap_0p00012__q__339ea42088 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p045__ps_0p035__rec_0p02__cap_0p00012__q__9617628b07 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p045__ps_0p035__rec_0p03__cap_0p00012__q__0e4c7a6f95 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p045__ps_0p04__rec_0p01__cap_0p00012__q___53da430f23 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p045__ps_0p04__rec_0p02__cap_0p00012__q___2ab85438de | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p045__ps_0p04__rec_0p03__cap_0p00012__q___c88063dcb7 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p045__ps_0p045__rec_0p01__cap_0p00012__q__f8aac0d05a | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p045__ps_0p045__rec_0p02__cap_0p00012__q__00c836d624 | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p045__ps_0p045__rec_0p03__cap_0p00012__q__11c7f4bada | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p045__ps_0p05__rec_0p01__cap_0p00012__q___72e63d0d3c | 0.269888 | 0.807324 | -0.000676 | -0.000175 | 0.953846 | 0.789423 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p045__ps_0p05__rec_0p02__cap_0p00012__q___22e1203897 | 0.269888 | 0.807324 | -0.000676 | -0.000175 | 0.953846 | 0.789423 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p045__ps_0p05__rec_0p03__cap_0p00012__q___8fef2c6990 | 0.269888 | 0.807324 | -0.000676 | -0.000175 | 0.953846 | 0.789423 | -0.018830 |
| candidate_ppopt256_pp252_residual_continue__thr_0p18__rs_0p055__ss_0p015__cap_5em05__37abf34c0e | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018830 |
| candidate_ppopt256_pp252_residual_continue__thr_0p18__rs_0p055__ss_0p03__cap_5em05__f9c2957f99 | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018830 |
| candidate_ppopt256_pp252_residual_continue__thr_0p18__rs_0p055__ss_0p0__cap_5em05__8e8725495a | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018830 |
| candidate_ppopt256_pp252_residual_continue__thr_0p12__rs_0p025__ss_0p0__cap_3em05__e34708452e | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.787500 | -0.018830 |
| candidate_ppopt256_pp252_residual_continue__thr_0p12__rs_0p025__ss_0p015__cap_3em05__430307a8b8 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.787500 | -0.018830 |
| candidate_ppopt256_pp252_residual_continue__thr_0p12__rs_0p025__ss_0p03__cap_3em05__8353ba0741 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.787500 | -0.018830 |
| candidate_ppopt256_pp252_residual_continue__thr_0p12__rs_0p055__ss_0p03__cap_3em05__8dd6d029eb | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.787500 | -0.018830 |
| candidate_ppopt256_pp252_residual_continue__thr_0p12__rs_0p055__ss_0p015__cap_3em05__646052af79 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.787500 | -0.018830 |
| candidate_ppopt256_pp252_residual_continue__thr_0p12__rs_0p055__ss_0p0__cap_3em05__4a25cee88f | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.787500 | -0.018830 |
| candidate_ppopt256_pp252_residual_continue__thr_0p18__rs_0p04__ss_0p015__cap_5em05__5ba89d8f88 | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018830 |
| candidate_ppopt256_pp252_residual_continue__thr_0p18__rs_0p04__ss_0p03__cap_5em05__a917f482aa | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018830 |
| candidate_ppopt256_pp252_residual_continue__thr_0p18__rs_0p04__ss_0p0__cap_5em05__6c517d5206 | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018830 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p05__ps_0p03__rec_0p01__cap_0p00012__q_0__1955670872 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p05__ps_0p03__rec_0p02__cap_0p00012__q_0__ad1679787b | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p05__ps_0p03__rec_0p03__cap_0p00012__q_0__b4a17f533a | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p05__ps_0p035__rec_0p01__cap_0p00012__q___0034d194d6 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p05__ps_0p035__rec_0p02__cap_0p00012__q___ef0ebb76c6 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p05__ps_0p035__rec_0p03__cap_0p00012__q___c851c174a2 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p05__ps_0p04__rec_0p01__cap_0p00012__q_0__d4f5a44263 | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p05__ps_0p04__rec_0p02__cap_0p00012__q_0__26718ad2ae | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p05__ps_0p04__rec_0p03__cap_0p00012__q_0__7844ca7fc2 | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p05__ps_0p045__rec_0p01__cap_0p00012__q___a9e5f89e8c | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p05__ps_0p045__rec_0p02__cap_0p00012__q___39ac6a71ac | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p05__ps_0p045__rec_0p03__cap_0p00012__q___faa203d738 | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p05__ps_0p05__rec_0p01__cap_0p00012__q_0__6d2da102af | 0.269888 | 0.807324 | -0.000676 | -0.000175 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p05__ps_0p05__rec_0p02__cap_0p00012__q_0__9b0fbc40cb | 0.269888 | 0.807324 | -0.000676 | -0.000175 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p05__ps_0p05__rec_0p03__cap_0p00012__q_0__a605491e40 | 0.269888 | 0.807324 | -0.000676 | -0.000175 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p12__rs_0p04__ss_0p03__cap_3em05__ef0c94884d | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.787500 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p12__rs_0p04__ss_0p015__cap_3em05__065f6136a4 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.787500 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p12__rs_0p04__ss_0p0__cap_3em05__57d0bca794 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.787500 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p18__rs_0p025__ss_0p015__cap_5em05__011f974448 | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p18__rs_0p025__ss_0p03__cap_5em05__7bb2dafbb0 | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p18__rs_0p025__ss_0p0__cap_5em05__b50fad8457 | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt257_prob_ensemble__p_h35_log_80_20__rs_0p04__ps_0p03__cap_0p00012__9d613cbd38 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.781090 | -0.018829 |
| candidate_ppopt257_prob_ensemble__p_h35_log_80_20__rs_0p04__ps_0p04__cap_0p00012__0a1158a01e | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.781090 | -0.018829 |
| candidate_ppopt257_prob_ensemble__p_h35_log_80_20__rs_0p04__ps_0p05__cap_0p00012__a94da7ab38 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.781090 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p12__rs_0p055__ss_0p03__cap_1p5em05__23d1d98f13 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p12__rs_0p055__ss_0p015__cap_1p5em05__19872c300a | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p12__rs_0p055__ss_0p0__cap_1p5em05__a573614392 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p12__rs_0p04__ss_0p03__cap_1p5em05__5fd4e7adb2 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p12__rs_0p04__ss_0p015__cap_1p5em05__a06b21695e | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p12__rs_0p04__ss_0p0__cap_1p5em05__147d255a9c | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p055__ps_0p03__rec_0p01__cap_0p00012__q___29b18e53e2 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p055__ps_0p03__rec_0p02__cap_0p00012__q___c7303fcfb1 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p055__ps_0p03__rec_0p03__cap_0p00012__q___9b392f9043 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p055__ps_0p035__rec_0p01__cap_0p00012__q__d2040a87d6 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p055__ps_0p035__rec_0p02__cap_0p00012__q__1fd98eaffc | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p055__ps_0p035__rec_0p03__cap_0p00012__q__8e3026b034 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p055__ps_0p04__rec_0p01__cap_0p00012__q___7de080dca6 | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p055__ps_0p04__rec_0p02__cap_0p00012__q___4c760e8b14 | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p055__ps_0p04__rec_0p03__cap_0p00012__q___e1ed97e162 | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p055__ps_0p045__rec_0p01__cap_0p00012__q__44672581d0 | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p055__ps_0p045__rec_0p02__cap_0p00012__q__62fbf03805 | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p055__ps_0p045__rec_0p03__cap_0p00012__q__9c98044037 | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p055__ps_0p05__rec_0p01__cap_0p00012__q___5a93d74428 | 0.269888 | 0.807324 | -0.000676 | -0.000175 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p055__ps_0p05__rec_0p02__cap_0p00012__q___384273ad24 | 0.269888 | 0.807324 | -0.000676 | -0.000175 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p055__ps_0p05__rec_0p03__cap_0p00012__q___df6dc18662 | 0.269888 | 0.807324 | -0.000676 | -0.000175 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p12__rs_0p025__ss_0p03__cap_1p5em05__0f1616852c | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p12__rs_0p025__ss_0p015__cap_1p5em05__ba567d6e85 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p12__rs_0p025__ss_0p0__cap_1p5em05__5e70ea12ea | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p06__ps_0p03__rec_0p03__cap_0p00012__q_0__f64e8a2e20 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p06__ps_0p03__rec_0p02__cap_0p00012__q_0__b77e743419 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p06__ps_0p03__rec_0p01__cap_0p00012__q_0__1533be6b27 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p06__ps_0p035__rec_0p03__cap_0p00012__q___08ae66b98b | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p06__ps_0p035__rec_0p02__cap_0p00012__q___f3aeab480f | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p06__ps_0p035__rec_0p01__cap_0p00012__q___166a0b72f1 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p06__ps_0p04__rec_0p03__cap_0p00012__q_0__ff2ff666e6 | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p06__ps_0p04__rec_0p02__cap_0p00012__q_0__8d54cc27aa | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p06__ps_0p04__rec_0p01__cap_0p00012__q_0__5567b5c404 | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p06__ps_0p045__rec_0p03__cap_0p00012__q___5e6177188d | 0.269888 | 0.807324 | -0.000676 | -0.000175 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p06__ps_0p045__rec_0p02__cap_0p00012__q___2c18e75394 | 0.269888 | 0.807324 | -0.000676 | -0.000175 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p06__ps_0p045__rec_0p01__cap_0p00012__q___7fe33c0fb5 | 0.269888 | 0.807324 | -0.000676 | -0.000175 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p18__rs_0p04__ss_0p015__cap_3em05__3321152e02 | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p18__rs_0p04__ss_0p03__cap_3em05__fb71cd1ece | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p18__rs_0p04__ss_0p0__cap_3em05__7f58f83234 | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p06__ps_0p05__rec_0p03__cap_0p00012__q_0__b5fcb0ef8c | 0.269888 | 0.807324 | -0.000676 | -0.000175 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p06__ps_0p05__rec_0p02__cap_0p00012__q_0__723f77a5ef | 0.269888 | 0.807324 | -0.000676 | -0.000175 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p06__ps_0p05__rec_0p01__cap_0p00012__q_0__d5e08266a6 | 0.269888 | 0.807324 | -0.000676 | -0.000175 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p03__rec_0p01__cap_0p00012__q_0__0a4f5043b3 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p03__rec_0p02__cap_0p00012__q_0__5115171639 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p03__rec_0p03__cap_0p00012__q_0__00ead71bfc | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p18__rs_0p055__ss_0p015__cap_3em05__b66da650ef | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p18__rs_0p055__ss_0p03__cap_3em05__c3434f0d0b | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p18__rs_0p055__ss_0p0__cap_3em05__85d8c73316 | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p035__rec_0p01__cap_0p00012__q___42e7ec4d34 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p035__rec_0p02__cap_0p00012__q___737b63a289 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p035__rec_0p03__cap_0p00012__q___84a627d41b | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p04__rec_0p01__cap_0p00012__q_0__6730509f67 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p04__rec_0p02__cap_0p00012__q_0__5ae421cf80 | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p04__rec_0p03__cap_0p00012__q_0__f6893c5c6d | 0.269888 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p18__rs_0p025__ss_0p015__cap_3em05__28d94bf517 | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p18__rs_0p025__ss_0p03__cap_3em05__5e6560ebf3 | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p18__rs_0p025__ss_0p0__cap_3em05__edbf4dc450 | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p045__rec_0p01__cap_0p00012__q___44d121286c | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p045__rec_0p02__cap_0p00012__q___ea4f117356 | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p045__rec_0p03__cap_0p00012__q___43876748ef | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p05__rec_0p01__cap_0p00012__q_0__87c76ccb66 | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p05__rec_0p02__cap_0p00012__q_0__c12079b106 | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p05__rec_0p03__cap_0p00012__q_0__7486c6394a | 0.269888 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt254_cap_split_refine__up_0p0001__down_7em05__q_0p35__risk_0p75__1704420c35 | 0.269889 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt254_cap_split_refine__up_0p0001__down_7em05__q_0p45__risk_0p65__e8da9db201 | 0.269889 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p045__ps_0p03__rec_0p01__cap_0p00012__q___2f23ec3644 | 0.269889 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p045__ps_0p03__rec_0p02__cap_0p00012__q___7c5e663aa6 | 0.269889 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p045__ps_0p03__rec_0p03__cap_0p00012__q___3226df409c | 0.269889 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p045__ps_0p035__rec_0p01__cap_0p00012__q__2c412edb65 | 0.269889 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p045__ps_0p035__rec_0p02__cap_0p00012__q__be64f07c51 | 0.269889 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p045__ps_0p035__rec_0p03__cap_0p00012__q__4b72e69907 | 0.269889 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p045__ps_0p04__rec_0p01__cap_0p00012__q___b4e2c71c83 | 0.269889 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p045__ps_0p04__rec_0p02__cap_0p00012__q___f73837ad60 | 0.269889 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p045__ps_0p04__rec_0p03__cap_0p00012__q___3912d5fa89 | 0.269889 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p045__ps_0p045__rec_0p01__cap_0p00012__q__e1d38fac13 | 0.269889 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p045__ps_0p045__rec_0p02__cap_0p00012__q__2c25eac25e | 0.269889 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p045__ps_0p045__rec_0p03__cap_0p00012__q__d955ffb209 | 0.269889 | 0.807324 | -0.000676 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p045__ps_0p05__rec_0p01__cap_0p00012__q___82549d3462 | 0.269889 | 0.807324 | -0.000676 | -0.000175 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p045__ps_0p05__rec_0p02__cap_0p00012__q___0a31a85b6d | 0.269889 | 0.807324 | -0.000676 | -0.000175 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p045__ps_0p05__rec_0p03__cap_0p00012__q___2bbdeb616d | 0.269889 | 0.807324 | -0.000676 | -0.000175 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt257_prob_ensemble__p_h35_log_80_20__rs_0p05__ps_0p03__cap_0p00012__2a4cf383ea | 0.269889 | 0.807325 | -0.000676 | -0.000174 | 0.953846 | 0.781090 | -0.018829 |
| candidate_ppopt257_prob_ensemble__p_h35_log_80_20__rs_0p05__ps_0p04__cap_0p00012__c84c4b4e35 | 0.269889 | 0.807325 | -0.000675 | -0.000174 | 0.953846 | 0.781090 | -0.018829 |
| candidate_ppopt257_prob_ensemble__p_h35_log_80_20__rs_0p05__ps_0p05__cap_0p00012__d530ad3926 | 0.269889 | 0.807325 | -0.000675 | -0.000174 | 0.953846 | 0.781090 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p18__rs_0p055__ss_0p015__cap_1p5em05__f96be27714 | 0.269889 | 0.807324 | -0.000675 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p18__rs_0p055__ss_0p03__cap_1p5em05__474999e1ff | 0.269889 | 0.807324 | -0.000675 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p18__rs_0p055__ss_0p0__cap_1p5em05__d3b393583f | 0.269889 | 0.807324 | -0.000675 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p18__rs_0p025__ss_0p015__cap_1p5em05__0e9929da2c | 0.269889 | 0.807324 | -0.000675 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p18__rs_0p025__ss_0p03__cap_1p5em05__aabbbf223f | 0.269889 | 0.807324 | -0.000675 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p18__rs_0p025__ss_0p0__cap_1p5em05__aeed49df3b | 0.269889 | 0.807324 | -0.000675 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p18__rs_0p04__ss_0p015__cap_1p5em05__2694758c0a | 0.269889 | 0.807324 | -0.000675 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p18__rs_0p04__ss_0p03__cap_1p5em05__e21b696128 | 0.269889 | 0.807324 | -0.000675 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt256_pp252_residual_continue__thr_0p18__rs_0p04__ss_0p0__cap_1p5em05__e413772032 | 0.269889 | 0.807324 | -0.000675 | -0.000174 | 0.953846 | 0.788782 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p03__rec_0p01__cap_0p0001__q_0p__e12f33e200 | 0.269889 | 0.807325 | -0.000675 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p03__rec_0p02__cap_0p0001__q_0p__a06e3fc242 | 0.269889 | 0.807325 | -0.000675 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p03__rec_0p03__cap_0p0001__q_0p__c9745662c1 | 0.269889 | 0.807325 | -0.000675 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |
| candidate_ppopt253_narrow_hist35_huber_support__thr_0p14__rs_0p04__ps_0p035__rec_0p01__cap_0p0001__q_0__6a58fb05c2 | 0.269889 | 0.807325 | -0.000675 | -0.000174 | 0.953846 | 0.789423 | -0.018829 |

## 실행 설정
```json
{
  "experiment_id": "PP-OPT253-258",
  "experiment_slug": "PP-OPT253_258_warm_pp252_narrow_direction_residual_refinement",
  "created_at": "2026-06-10T13:31:40",
  "previous_experiment": "experiments/track6/PP-OPT247_252_warm_pp246_residual_direction_gated_correction",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 1610,
  "prediction_rows": 1812860,
  "previous_decision": {
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
  "pp246_decision": {
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
  "selection_decision": {
    "operational_label": "candidate_ppopt256_pp252_residual_continue__thr_0p12__rs_0p025__ss_0p0__cap_5em05__7f3a1e1f66",
    "operational_candidate": "ppopt256_pp252_residual_continue__thr=0p12__rs=0p025__ss=0p0__cap=5em05",
    "operational_fixed_test_MAPE": 0.26988819577914586,
    "operational_fixed_test_p95_APE": 0.8073247072914463,
    "operational_delta_vs_pp64_MAPE": -0.0006758461365145019,
    "operational_delta_vs_pp64_p95_APE": -0.00017414501466350707,
    "operational_delta_vs_pp252_MAPE": -5.350963706574063e-07,
    "operational_delta_vs_pp252_p95_win_rate": 0.0,
    "operational_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "operational_avg_pp64_p95_win_rate": 0.7887820512820514,
    "operational_replacement_score": -0.018829692290360658,
    "balanced_label": "candidate_ppopt256_pp252_residual_continue__thr_0p12__rs_0p025__ss_0p0__cap_5em05__7f3a1e1f66",
    "balanced_candidate": "ppopt256_pp252_residual_continue__thr=0p12__rs=0p025__ss=0p0__cap=5em05",
    "balanced_fixed_test_MAPE": 0.26988819577914586,
    "balanced_fixed_test_p95_APE": 0.8073247072914463,
    "balanced_delta_vs_pp64_MAPE": -0.0006758461365145019,
    "balanced_delta_vs_pp64_p95_APE": -0.00017414501466350707,
    "balanced_delta_vs_pp252_MAPE": -5.350963706574063e-07,
    "balanced_delta_vs_pp252_p95_win_rate": 0.0,
    "balanced_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "balanced_avg_pp64_p95_win_rate": 0.7887820512820514,
    "balanced_replacement_score": -0.018829692290360658,
    "mape_challenger_label": "candidate_ppopt256_pp252_residual_continue__thr_0p12__rs_0p025__ss_0p0__cap_5em05__7f3a1e1f66",
    "mape_challenger_candidate": "ppopt256_pp252_residual_continue__thr=0p12__rs=0p025__ss=0p0__cap=5em05",
    "mape_challenger_fixed_test_MAPE": 0.26988819577914586,
    "mape_challenger_fixed_test_p95_APE": 0.8073247072914463,
    "mape_challenger_delta_vs_pp64_MAPE": -0.0006758461365145019,
    "mape_challenger_delta_vs_pp64_p95_APE": -0.00017414501466350707,
    "mape_challenger_delta_vs_pp252_MAPE": -5.350963706574063e-07,
    "mape_challenger_delta_vs_pp252_p95_win_rate": 0.0,
    "mape_challenger_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "mape_challenger_avg_pp64_p95_win_rate": 0.7887820512820514,
    "mape_challenger_replacement_score": -0.018829692290360658,
    "p95_recovery_label": "candidate_ppopt253_narrow_hist35_huber_support__thr_0p12__rs_0p06__ps_0p05__rec_0p03__cap_0p00012__q_0__c821532887",
    "p95_recovery_candidate": "ppopt253_narrow_hist35_huber_support__thr=0p12__rs=0p06__ps=0p05__rec=0p03__cap=0p00012__q=0p45",
    "p95_recovery_fixed_test_MAPE": 0.2698891306774469,
    "p95_recovery_fixed_test_p95_APE": 0.8073226275738279,
    "p95_recovery_delta_vs_pp64_MAPE": -0.0006749112382134492,
    "p95_recovery_delta_vs_pp64_p95_APE": -0.0001762247322819599,
    "p95_recovery_delta_vs_pp252_MAPE": 3.9980193039523826e-07,
    "p95_recovery_delta_vs_pp252_p95_win_rate": 0.0,
    "p95_recovery_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "p95_recovery_avg_pp64_p95_win_rate": 0.7887820512820514,
    "p95_recovery_replacement_score": -0.018828757392059605,
    "stability_label": "pp252_operational_reference",
    "stability_candidate": "ppopt252_operational_pp246_gated_correction__source=ppopt250_segment_direction_router__seg_price_conf_qwidth__minn_8__gain_0p0__s_0p35__cap_3em05",
    "stability_fixed_test_MAPE": 0.2698897743909076,
    "stability_fixed_test_p95_APE": 0.8073255046591389,
    "stability_delta_vs_pp64_MAPE": -0.0006742675247527474,
    "stability_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "stability_delta_vs_pp252_MAPE": 1.0435153910970385e-06,
    "stability_delta_vs_pp252_p95_win_rate": 0.027884615384615397,
    "stability_avg_pp64_MAPE_win_rate": 0.9541666666666666,
    "stability_avg_pp64_p95_win_rate": 0.8166666666666668,
    "stability_replacement_score": -0.01884093419141941,
    "p95_guarded_label": "pp252_p95_guarded_reference",
    "p95_guarded_candidate": "ppopt252_p95_guarded_pp246_gated_correction__source=ppopt246_p95_guarded_pp234_p95_constrained__source_ppopt234_p95_guarded_pp228_p95_recovery__source_ppopt228_p95_guarded_",
    "p95_guarded_fixed_test_MAPE": 0.26994920114208765,
    "p95_guarded_fixed_test_p95_APE": 0.8072545738314347,
    "p95_guarded_delta_vs_pp64_MAPE": -0.0006148407735727113,
    "p95_guarded_delta_vs_pp64_p95_APE": -0.0002442784746751192,
    "p95_guarded_delta_vs_pp252_MAPE": 6.047026657113319e-05,
    "p95_guarded_delta_vs_pp252_p95_win_rate": -0.03717948717948716,
    "p95_guarded_avg_pp64_MAPE_win_rate": 0.9509615384615384,
    "p95_guarded_avg_pp64_p95_win_rate": 0.7516025641025642,
    "p95_guarded_replacement_score": -0.01865330231203425,
    "p95_extreme_label": "pp252_p95_extreme_reference",
    "p95_extreme_candidate": "ppopt252_p95_extreme_pp246_gated_correction__source=ppopt246_p95_extreme_pp234_p95_constrained__source_ppopt240_p95_extreme_pp234_learned_router__source_ppopt234_p95_extrem",
    "p95_extreme_fixed_test_MAPE": 0.27026892590910795,
    "p95_extreme_fixed_test_p95_APE": 0.8059493758221674,
    "p95_extreme_delta_vs_pp64_MAPE": -0.00029511600655240944,
    "p95_extreme_delta_vs_pp64_p95_APE": -0.0015494764839424358,
    "p95_extreme_delta_vs_pp252_MAPE": 0.00038019503359143503,
    "p95_extreme_delta_vs_pp252_p95_win_rate": -0.2878205128205129,
    "p95_extreme_avg_pp64_MAPE_win_rate": 0.5983974358974359,
    "p95_extreme_avg_pp64_p95_win_rate": 0.5009615384615385,
    "p95_extreme_replacement_score": -0.0040792899192624915,
    "operational_protocol_candidate": "ppopt258_operational_pp252_narrow_refinement__source=ppopt256_pp252_residual_continue__thr_0p12__rs_0p025__ss_0p0__cap_5em05",
    "balanced_protocol_candidate": "ppopt258_balanced_pp252_narrow_refinement__source=ppopt256_pp252_residual_continue__thr_0p12__rs_0p025__ss_0p0__cap_5em05",
    "mape_challenger_protocol_candidate": "ppopt258_mape_challenger_pp252_narrow_refinement__source=ppopt256_pp252_residual_continue__thr_0p12__rs_0p025__ss_0p0__cap_5em05",
    "p95_recovery_protocol_candidate": "ppopt258_p95_recovery_pp252_narrow_refinement__source=ppopt253_narrow_hist35_huber_support__thr_0p12__rs_0p06__ps_0p05__rec_0p03__cap_0p00012__q_0p45",
    "stability_protocol_candidate": "ppopt258_stability_pp252_narrow_refinement__source=ppopt252_operational_pp246_gated_correction__source_ppopt250_segment_direction_router__seg_price_conf_qwidth__minn_8__ga",
    "p95_guarded_protocol_candidate": "ppopt258_p95_guarded_pp252_narrow_refinement__source=ppopt252_p95_guarded_pp246_gated_correction__source_ppopt246_p95_guarded_pp234_p95_constrained__source_ppopt234_p95_guar",
    "p95_extreme_protocol_candidate": "ppopt258_p95_extreme_pp252_narrow_refinement__source=ppopt252_p95_extreme_pp246_gated_correction__source_ppopt246_p95_extreme_pp234_p95_constrained__source_ppopt240_p95_extr"
  },
  "items": [
    {
      "item_id": "PP-OPT253",
      "priority": "1",
      "title": "narrow hist35 Huber support refinement",
      "description": "PP252 성공 조합인 hist35 방향 gate + Huber residual + p95 support 주변을 좁게 재탐색."
    },
    {
      "item_id": "PP-OPT254",
      "priority": "2",
      "title": "confidence threshold and cap split refinement",
      "description": "direction confidence threshold, 상향/하향 cap, quantile shrink를 더 세분화."
    },
    {
      "item_id": "PP-OPT255",
      "priority": "3",
      "title": "weak stability add-on from PP250",
      "description": "PP250의 높은 p95 win-rate 이동분을 PP252 균형 후보에 아주 약하게 추가."
    },
    {
      "item_id": "PP-OPT256",
      "priority": "4",
      "title": "PP252 source residual continuation",
      "description": "PP252를 새 기준으로 두고 잔차 방향 gate를 다시 학습해 2차 보정 가능성 확인."
    },
    {
      "item_id": "PP-OPT257",
      "priority": "5",
      "title": "direction probability ensemble refinement",
      "description": "hist35, hist70, logistic direction probability를 약하게 평균해 단일 분류기 의존도를 낮춤."
    },
    {
      "item_id": "PP-OPT258",
      "priority": "6",
      "title": "final PP252 narrow refinement decision",
      "description": "PP252 대비 MAPE, p95 win rate, replacement score 제약을 만족하는 후보를 최종 선택."
    }
  ],
  "formula": {
    "base": "PP246 balanced or PP252 balanced log price",
    "narrow_ensemble": "source + clip((Huber residual * direction_conf * residual_strength) + (p95 support delta * direction_conf * support_strength) + (p95 recovery delta * direction_conf * recovery_strength), asymmetric cap)",
    "stability_addon": "PP252 + clip((PP252 stability target - PP252) * tiny_strength, risk-reduced cap)",
    "selection_goal": "MAPE <= PP252 + 0.000001, repeated p95 win rate >= PP252, replacement score <= PP252 + 0.000002"
  }
}
```