# PP-OPT181~186 Warm Huber basis p95-guard refinement 결과

- 작성일: 2026-06-10 10:15
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 목적: PP180의 Huber basis MAPE 개선을 유지하면서 p95 악화를 PP172 근처로 제한
- 결론: 운영 후보 fixed test MAPE 0.269961, p95 0.807231. PP172 대비 MAPE -0.000037, p95 +0.000000. 엄격 p95 후보 MAPE 0.269961, p95 0.807231.

## 주요 후보 test 비교
| candidate | family | item_id | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt180_operational_basis_generation_challenger__source=ppopt174_direct_basis__source_stack_huber_weighted__thr_0p08__s_0p3__cap_0p004 | reference_prior | REFERENCE | 0.140975 | 0.269933 | 0.807326 | 0.397475 | -0.001462 | -0.000804 |
| ppopt186_operational_huber_basis_p95_guard__source=ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p04__s_0p42__cap_0p0045 | huber_basis_p95_guard_operational_selection | PP-OPT186 | 0.139801 | 0.269961 | 0.807231 | 0.397497 | -0.001434 | -0.000899 |
| ppopt186_strict_guarded_huber_basis_p95_guard__source=ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p04__s_0p42__cap_0p0045 | huber_basis_p95_guard_strict_selection | PP-OPT186 | 0.139801 | 0.269961 | 0.807231 | 0.397497 | -0.001434 | -0.000899 |
| ppopt172_operational_pp166_tail_calibration_challenger__source=ppopt169_segment_router__source_pp162_p95_gate__seg_price_conf__thr_m0p04__s_0p5__cap_0p004 | reference_prior | REFERENCE | 0.139801 | 0.269997 | 0.807231 | 0.397516 | -0.001397 | -0.000899 |
| reference_pp126_operational | reference_prior | REFERENCE | 0.136320 | 0.270114 | 0.807490 | 0.397588 | -0.001280 | -0.000640 |
| reference_pp148_operational | reference_prior | REFERENCE | 0.139801 | 0.270140 | 0.807231 | 0.397525 | -0.001255 | -0.000899 |
| reference_pp148_p95 | reference_prior | REFERENCE | 0.141036 | 0.270269 | 0.805949 | 0.397421 | -0.001126 | -0.002181 |
| ppopt186_p95_huber_basis_p95_guard__source=reference_pp148_p95 | huber_basis_p95_guard_p95_selection | PP-OPT186 | 0.141036 | 0.270269 | 0.805949 | 0.397421 | -0.001126 | -0.002181 |
| reference_pp64_current_best | reference_prior | REFERENCE | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | p95_test_MAPE | p95_test_p95_APE | operational_pass_vs_incumbent | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | strict Huber basis p95 guard | 144 | 0.269913 | 0.807827 | 0.269997 | 0.807231 | False | strict_huber_basis_p95_guard | ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p02__s=0p3__cap=0p0045 |
| 4 | Huber and p95-preserving blend | 108 | 0.269961 | 0.807231 | 0.269961 | 0.807231 | False | huber_p95_preserving_blend | ppopt184_huber_p95_blend__partner=cat_plain__hshare=0p65__thr=0p04__s=0p42__cap=0p0045 |
| 6 | final Huber basis p95-guard decision | 3 | 0.269961 | 0.807231 | 0.270269 | 0.805949 | False | huber_basis_p95_guard_operational_selection | ppopt186_operational_huber_basis_p95_guard__source=ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p04__s_0p42__cap_0p0045 |
| 3 | Cat/XGB p95-preserving basis | 144 | 0.269997 | 0.807231 | 0.269997 | 0.807231 | False | cat_xgb_p95_preserving_basis | ppopt183_cat_xgb_basis__source=direct_cat_plain__thr=0p02__s=0p18__cap=0p003 |
| 5 | adaptive p95 cap tier | 81 | 0.269997 | 0.807231 | 0.269997 | 0.807231 | False | adaptive_p95_cap_tier | ppopt185_adaptive_p95_cap__thr=0p08__s=0p18__basecap=0p0035__shrink=0p45 |
| 2 | PP180 rollback by p95 hazard | 32 | 0.269933 | 0.807326 | 0.269933 | 0.807326 | False | pp180_rollback_by_p95_hazard | ppopt182_pp180_rollback__source=pp180__rb=0p25__cap=0p0025 |

## 탐색 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p02__s=0p3__cap=0p0045 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269913 | 0.807827 | -0.001482 | -0.000303 | -0.001618 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p02__s=0p24__cap=0p0045 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269916 | 0.807827 | -0.001478 | -0.000303 | -0.001615 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p06__s=0p3__cap=0p0045 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269920 | 0.807827 | -0.001475 | -0.000303 | -0.001612 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p02__s=0p18__cap=0p0045 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269924 | 0.807827 | -0.001470 | -0.000303 | -0.001610 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p06__s=0p24__cap=0p0045 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269927 | 0.807819 | -0.001468 | -0.000311 | -0.001608 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p02__s=0p3__cap=0p0035 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269928 | 0.807695 | -0.001467 | -0.000435 | -0.001598 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p06__s=0p18__cap=0p0045 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269939 | 0.807672 | -0.001456 | -0.000458 | -0.001595 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p02__s=0p24__cap=0p0035 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269931 | 0.807695 | -0.001464 | -0.000435 | -0.001595 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p02__s=0p12__cap=0p0045 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269941 | 0.807656 | -0.001454 | -0.000474 | -0.001594 |
| ppopt184_huber_p95_blend__partner=cat_plain__hshare=0p65__thr=0p04__s=0p42__cap=0p0045 | PP-OPT184 | huber_p95_preserving_blend | 0.269961 | 0.807231 | -0.001434 | -0.000899 | -0.001594 |
| ppopt184_huber_p95_blend__partner=cat_plain__hshare=0p65__thr=0p08__s=0p42__cap=0p0045 | PP-OPT184 | huber_p95_preserving_blend | 0.269961 | 0.807231 | -0.001434 | -0.000899 | -0.001594 |
| ppopt184_huber_p95_blend__partner=cat_plain__hshare=0p65__thr=0p0__s=0p42__cap=0p0045 | PP-OPT184 | huber_p95_preserving_blend | 0.269961 | 0.807231 | -0.001434 | -0.000899 | -0.001594 |
| ppopt186_operational_huber_basis_p95_guard__source=ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p04__s_0p42__cap_0p0045 | PP-OPT186 | huber_basis_p95_guard_operational_selection | 0.269961 | 0.807231 | -0.001434 | -0.000899 | -0.001594 |
| ppopt186_strict_guarded_huber_basis_p95_guard__source=ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p04__s_0p42__cap_0p0045 | PP-OPT186 | huber_basis_p95_guard_strict_selection | 0.269961 | 0.807231 | -0.001434 | -0.000899 | -0.001594 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p1__s=0p3__cap=0p0045 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269943 | 0.807639 | -0.001452 | -0.000491 | -0.001593 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p06__s=0p3__cap=0p0035 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269933 | 0.807695 | -0.001462 | -0.000435 | -0.001592 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p02__s=0p18__cap=0p0035 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269935 | 0.807695 | -0.001460 | -0.000435 | -0.001591 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p06__s=0p24__cap=0p0035 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269936 | 0.807695 | -0.001458 | -0.000435 | -0.001590 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p1__s=0p24__cap=0p0045 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269954 | 0.807558 | -0.001441 | -0.000572 | -0.001588 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p06__s=0p18__cap=0p0035 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269944 | 0.807672 | -0.001451 | -0.000458 | -0.001586 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p06__s=0p12__cap=0p0045 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269959 | 0.807525 | -0.001436 | -0.000605 | -0.001586 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p02__s=0p12__cap=0p0035 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269945 | 0.807656 | -0.001450 | -0.000474 | -0.001585 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p1__s=0p3__cap=0p0035 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269946 | 0.807639 | -0.001449 | -0.000491 | -0.001585 |
| ppopt184_huber_p95_blend__partner=xgb_weighted__hshare=0p65__thr=0p04__s=0p42__cap=0p0045 | PP-OPT184 | huber_p95_preserving_blend | 0.269963 | 0.807231 | -0.001431 | -0.000899 | -0.001585 |
| ppopt184_huber_p95_blend__partner=xgb_weighted__hshare=0p65__thr=0p0__s=0p42__cap=0p0045 | PP-OPT184 | huber_p95_preserving_blend | 0.269963 | 0.807231 | -0.001431 | -0.000899 | -0.001585 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p02__s=0p3__cap=0p0025 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269944 | 0.807563 | -0.001451 | -0.000567 | -0.001584 |
| ppopt184_huber_p95_blend__partner=xgb_weighted__hshare=0p65__thr=0p08__s=0p42__cap=0p0045 | PP-OPT184 | huber_p95_preserving_blend | 0.269964 | 0.807231 | -0.001430 | -0.000899 | -0.001584 |
| ppopt184_huber_p95_blend__partner=cat_plain__hshare=0p65__thr=0p04__s=0p42__cap=0p003 | PP-OPT184 | huber_p95_preserving_blend | 0.269970 | 0.807231 | -0.001425 | -0.000899 | -0.001584 |
| ppopt184_huber_p95_blend__partner=cat_plain__hshare=0p65__thr=0p08__s=0p42__cap=0p003 | PP-OPT184 | huber_p95_preserving_blend | 0.269970 | 0.807231 | -0.001425 | -0.000899 | -0.001584 |
| ppopt184_huber_p95_blend__partner=cat_plain__hshare=0p65__thr=0p0__s=0p42__cap=0p003 | PP-OPT184 | huber_p95_preserving_blend | 0.269970 | 0.807231 | -0.001425 | -0.000899 | -0.001584 |
| ppopt184_huber_p95_blend__partner=cat_plain__hshare=0p65__thr=0p04__s=0p3__cap=0p0045 | PP-OPT184 | huber_p95_preserving_blend | 0.269964 | 0.807231 | -0.001431 | -0.000899 | -0.001582 |
| ppopt184_huber_p95_blend__partner=cat_plain__hshare=0p65__thr=0p08__s=0p3__cap=0p0045 | PP-OPT184 | huber_p95_preserving_blend | 0.269964 | 0.807231 | -0.001431 | -0.000899 | -0.001582 |
| ppopt184_huber_p95_blend__partner=cat_plain__hshare=0p65__thr=0p0__s=0p3__cap=0p0045 | PP-OPT184 | huber_p95_preserving_blend | 0.269964 | 0.807231 | -0.001431 | -0.000899 | -0.001582 |
| ppopt184_huber_p95_blend__partner=cat_plain__hshare=0p65__thr=0p04__s=0p3__cap=0p003 | PP-OPT184 | huber_p95_preserving_blend | 0.269972 | 0.807231 | -0.001423 | -0.000899 | -0.001582 |
| ppopt184_huber_p95_blend__partner=cat_plain__hshare=0p65__thr=0p08__s=0p3__cap=0p003 | PP-OPT184 | huber_p95_preserving_blend | 0.269972 | 0.807231 | -0.001423 | -0.000899 | -0.001582 |
| ppopt184_huber_p95_blend__partner=cat_plain__hshare=0p65__thr=0p0__s=0p3__cap=0p003 | PP-OPT184 | huber_p95_preserving_blend | 0.269972 | 0.807231 | -0.001423 | -0.000899 | -0.001582 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p02__s=0p24__cap=0p0025 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269946 | 0.807563 | -0.001448 | -0.000567 | -0.001582 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p1__s=0p24__cap=0p0035 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269954 | 0.807558 | -0.001441 | -0.000572 | -0.001582 |
| ppopt184_huber_p95_blend__partner=xgb_weighted__hshare=0p65__thr=0p04__s=0p3__cap=0p0045 | PP-OPT184 | huber_p95_preserving_blend | 0.269971 | 0.807231 | -0.001424 | -0.000899 | -0.001582 |
| ppopt184_huber_p95_blend__partner=xgb_weighted__hshare=0p65__thr=0p0__s=0p3__cap=0p0045 | PP-OPT184 | huber_p95_preserving_blend | 0.269971 | 0.807231 | -0.001424 | -0.000899 | -0.001582 |
| ppopt184_huber_p95_blend__partner=xgb_weighted__hshare=0p65__thr=0p08__s=0p3__cap=0p0045 | PP-OPT184 | huber_p95_preserving_blend | 0.269972 | 0.807231 | -0.001423 | -0.000899 | -0.001581 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p1__s=0p18__cap=0p0045 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269965 | 0.807476 | -0.001430 | -0.000654 | -0.001581 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p06__s=0p3__cap=0p0025 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269948 | 0.807563 | -0.001446 | -0.000567 | -0.001581 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p02__s=0p18__cap=0p0025 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269950 | 0.807563 | -0.001445 | -0.000567 | -0.001580 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p06__s=0p12__cap=0p0035 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269958 | 0.807525 | -0.001437 | -0.000605 | -0.001580 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p06__s=0p24__cap=0p0025 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269950 | 0.807563 | -0.001445 | -0.000567 | -0.001579 |
| ppopt181_strict_huber_guard__seg=price_conf__thr=0p06__s=0p12__cap=0p0025 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269996 | 0.807233 | -0.001399 | -0.000897 | -0.001578 |
| ppopt181_strict_huber_guard__seg=price_conf__thr=0p06__s=0p12__cap=0p0035 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269996 | 0.807233 | -0.001399 | -0.000897 | -0.001578 |
| ppopt181_strict_huber_guard__seg=price_conf__thr=0p06__s=0p12__cap=0p0045 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269996 | 0.807233 | -0.001399 | -0.000897 | -0.001578 |
| ppopt184_huber_p95_blend__partner=xgb_weighted__hshare=0p65__thr=0p04__s=0p18__cap=0p0045 | PP-OPT184 | huber_p95_preserving_blend | 0.269978 | 0.807231 | -0.001417 | -0.000899 | -0.001577 |
| ppopt184_huber_p95_blend__partner=xgb_weighted__hshare=0p65__thr=0p0__s=0p18__cap=0p0045 | PP-OPT184 | huber_p95_preserving_blend | 0.269978 | 0.807231 | -0.001417 | -0.000899 | -0.001577 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p1__s=0p18__cap=0p0035 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269965 | 0.807476 | -0.001430 | -0.000654 | -0.001577 |
| ppopt184_huber_p95_blend__partner=xgb_weighted__hshare=0p65__thr=0p08__s=0p18__cap=0p0045 | PP-OPT184 | huber_p95_preserving_blend | 0.269979 | 0.807231 | -0.001416 | -0.000899 | -0.001577 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p06__s=0p18__cap=0p0025 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269953 | 0.807563 | -0.001442 | -0.000567 | -0.001576 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p02__s=0p12__cap=0p0025 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269954 | 0.807563 | -0.001441 | -0.000567 | -0.001576 |
| ppopt184_huber_p95_blend__partner=xgb_weighted__hshare=0p65__thr=0p08__s=0p42__cap=0p003 | PP-OPT184 | huber_p95_preserving_blend | 0.269972 | 0.807231 | -0.001423 | -0.000899 | -0.001576 |
| ppopt184_huber_p95_blend__partner=xgb_weighted__hshare=0p65__thr=0p04__s=0p42__cap=0p003 | PP-OPT184 | huber_p95_preserving_blend | 0.269972 | 0.807231 | -0.001423 | -0.000899 | -0.001576 |
| ppopt184_huber_p95_blend__partner=xgb_weighted__hshare=0p65__thr=0p0__s=0p42__cap=0p003 | PP-OPT184 | huber_p95_preserving_blend | 0.269972 | 0.807231 | -0.001423 | -0.000899 | -0.001576 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p1__s=0p3__cap=0p0025 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269954 | 0.807563 | -0.001441 | -0.000567 | -0.001576 |
| ppopt184_huber_p95_blend__partner=xgb_weighted__hshare=0p65__thr=0p04__s=0p3__cap=0p003 | PP-OPT184 | huber_p95_preserving_blend | 0.269974 | 0.807231 | -0.001421 | -0.000899 | -0.001576 |
| ppopt184_huber_p95_blend__partner=xgb_weighted__hshare=0p65__thr=0p0__s=0p3__cap=0p003 | PP-OPT184 | huber_p95_preserving_blend | 0.269974 | 0.807231 | -0.001421 | -0.000899 | -0.001576 |
| ppopt184_huber_p95_blend__partner=xgb_weighted__hshare=0p65__thr=0p08__s=0p3__cap=0p003 | PP-OPT184 | huber_p95_preserving_blend | 0.269974 | 0.807231 | -0.001420 | -0.000899 | -0.001576 |
| ppopt181_strict_huber_guard__seg=price_conf__thr=0p06__s=0p18__cap=0p0025 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269996 | 0.807233 | -0.001399 | -0.000897 | -0.001576 |
| ppopt181_strict_huber_guard__seg=price_conf__thr=0p06__s=0p18__cap=0p0035 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269996 | 0.807233 | -0.001399 | -0.000897 | -0.001576 |
| ppopt181_strict_huber_guard__seg=price_conf__thr=0p06__s=0p18__cap=0p0045 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269996 | 0.807233 | -0.001399 | -0.000897 | -0.001576 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p1__s=0p24__cap=0p0025 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269959 | 0.807558 | -0.001436 | -0.000572 | -0.001573 |
| ppopt181_strict_huber_guard__seg=price_conf__thr=0p06__s=0p24__cap=0p0025 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269995 | 0.807234 | -0.001400 | -0.000896 | -0.001573 |
| ppopt181_strict_huber_guard__seg=price_conf__thr=0p06__s=0p24__cap=0p0035 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269995 | 0.807234 | -0.001400 | -0.000896 | -0.001573 |
| ppopt181_strict_huber_guard__seg=price_conf__thr=0p06__s=0p24__cap=0p0045 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269995 | 0.807234 | -0.001400 | -0.000896 | -0.001573 |
| ppopt184_huber_p95_blend__partner=xgb_weighted__hshare=0p65__thr=0p04__s=0p18__cap=0p003 | PP-OPT184 | huber_p95_preserving_blend | 0.269981 | 0.807231 | -0.001414 | -0.000899 | -0.001573 |
| ppopt184_huber_p95_blend__partner=xgb_weighted__hshare=0p65__thr=0p0__s=0p18__cap=0p003 | PP-OPT184 | huber_p95_preserving_blend | 0.269981 | 0.807231 | -0.001414 | -0.000899 | -0.001573 |
| ppopt184_huber_p95_blend__partner=xgb_weighted__hshare=0p65__thr=0p08__s=0p18__cap=0p003 | PP-OPT184 | huber_p95_preserving_blend | 0.269981 | 0.807231 | -0.001414 | -0.000899 | -0.001573 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p06__s=0p12__cap=0p0025 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269961 | 0.807525 | -0.001434 | -0.000605 | -0.001572 |
| ppopt184_huber_p95_blend__partner=cat_plain__hshare=0p65__thr=0p04__s=0p18__cap=0p003 | PP-OPT184 | huber_p95_preserving_blend | 0.269976 | 0.807231 | -0.001419 | -0.000899 | -0.001572 |
| ppopt184_huber_p95_blend__partner=cat_plain__hshare=0p65__thr=0p08__s=0p18__cap=0p003 | PP-OPT184 | huber_p95_preserving_blend | 0.269976 | 0.807231 | -0.001419 | -0.000899 | -0.001572 |
| ppopt184_huber_p95_blend__partner=cat_plain__hshare=0p65__thr=0p0__s=0p18__cap=0p003 | PP-OPT184 | huber_p95_preserving_blend | 0.269976 | 0.807231 | -0.001419 | -0.000899 | -0.001572 |
| ppopt181_strict_huber_guard__seg=price_conf__thr=0p06__s=0p3__cap=0p0025 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269994 | 0.807235 | -0.001401 | -0.000895 | -0.001571 |
| ppopt181_strict_huber_guard__seg=price_conf__thr=0p06__s=0p3__cap=0p0035 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269994 | 0.807235 | -0.001401 | -0.000895 | -0.001571 |
| ppopt181_strict_huber_guard__seg=price_conf__thr=0p06__s=0p3__cap=0p0045 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269994 | 0.807235 | -0.001401 | -0.000895 | -0.001571 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p1__s=0p18__cap=0p0025 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269965 | 0.807476 | -0.001430 | -0.000654 | -0.001571 |
| ppopt184_huber_p95_blend__partner=cat_plain__hshare=0p65__thr=0p04__s=0p18__cap=0p0045 | PP-OPT184 | huber_p95_preserving_blend | 0.269968 | 0.807231 | -0.001427 | -0.000899 | -0.001570 |
| ppopt184_huber_p95_blend__partner=cat_plain__hshare=0p65__thr=0p08__s=0p18__cap=0p0045 | PP-OPT184 | huber_p95_preserving_blend | 0.269968 | 0.807231 | -0.001427 | -0.000899 | -0.001570 |
| ppopt184_huber_p95_blend__partner=cat_plain__hshare=0p65__thr=0p0__s=0p18__cap=0p0045 | PP-OPT184 | huber_p95_preserving_blend | 0.269968 | 0.807231 | -0.001427 | -0.000899 | -0.001570 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p1__s=0p12__cap=0p0035 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269976 | 0.807394 | -0.001419 | -0.000736 | -0.001568 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p1__s=0p12__cap=0p0045 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269976 | 0.807394 | -0.001419 | -0.000736 | -0.001568 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p1__s=0p12__cap=0p0025 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269976 | 0.807394 | -0.001419 | -0.000736 | -0.001566 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p14__s=0p3__cap=0p0025 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269987 | 0.807313 | -0.001408 | -0.000817 | -0.001554 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p14__s=0p3__cap=0p0035 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269987 | 0.807313 | -0.001408 | -0.000817 | -0.001554 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p14__s=0p3__cap=0p0045 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269987 | 0.807313 | -0.001408 | -0.000817 | -0.001554 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p14__s=0p24__cap=0p0025 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269989 | 0.807296 | -0.001406 | -0.000834 | -0.001552 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p14__s=0p24__cap=0p0035 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269989 | 0.807296 | -0.001406 | -0.000834 | -0.001552 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p14__s=0p24__cap=0p0045 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269989 | 0.807296 | -0.001406 | -0.000834 | -0.001552 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p14__s=0p18__cap=0p0025 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269991 | 0.807280 | -0.001404 | -0.000850 | -0.001549 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p14__s=0p18__cap=0p0035 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269991 | 0.807280 | -0.001404 | -0.000850 | -0.001549 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p14__s=0p18__cap=0p0045 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269991 | 0.807280 | -0.001404 | -0.000850 | -0.001549 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p14__s=0p12__cap=0p0025 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269993 | 0.807264 | -0.001402 | -0.000866 | -0.001546 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p14__s=0p12__cap=0p0035 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269993 | 0.807264 | -0.001402 | -0.000866 | -0.001546 |
| ppopt181_strict_huber_guard__seg=price_qwidth__thr=0p14__s=0p12__cap=0p0045 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269993 | 0.807264 | -0.001402 | -0.000866 | -0.001546 |
| ppopt181_strict_huber_guard__seg=price_conf__thr=0p14__s=0p12__cap=0p0025 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269997 | 0.807231 | -0.001397 | -0.000899 | -0.001541 |
| ppopt181_strict_huber_guard__seg=price_conf__thr=0p14__s=0p12__cap=0p0035 | PP-OPT181 | strict_huber_basis_p95_guard | 0.269997 | 0.807231 | -0.001397 | -0.000899 | -0.001541 |

## 선택 후보 반복 안정성
| candidate_label | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_vs_pp64_MAPE | fixed_test_delta_vs_pp64_p95_APE | avg_pp64_MAPE_win_rate | avg_pp64_p95_win_rate | replacement_score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| candidate_ppopt182_pp180_rollback__source_huber_s0p3__rb_0p85__cap_0p004__d4015cb024 | 0.269634 | 0.807939 | -0.000930 | 0.000440 | 0.959936 | 0.536859 | -0.019019 |
| candidate_ppopt182_pp180_rollback__source_huber_s0p24__rb_0p85__cap_0p004__1ae8cb1c59 | 0.269641 | 0.807929 | -0.000923 | 0.000430 | 0.959615 | 0.541026 | -0.019006 |
| candidate_ppopt182_pp180_rollback__source_huber_s0p18__rb_0p85__cap_0p004__041ecfb365 | 0.269663 | 0.807919 | -0.000901 | 0.000420 | 0.958654 | 0.546795 | -0.018953 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p02__s_0p3__cap_0p0045__16c0169ac0 | 0.269892 | 0.807444 | -0.000672 | -0.000055 | 0.956410 | 0.751282 | -0.018929 |
| candidate_ppopt182_pp180_rollback__source_huber_s0p24__rb_0p85__cap_0p0025__a8d2f149f6 | 0.269658 | 0.807929 | -0.000906 | 0.000430 | 0.958013 | 0.532692 | -0.018925 |
| candidate_ppopt182_pp180_rollback__source_huber_s0p3__rb_0p85__cap_0p0025__f5589c6d0f | 0.269650 | 0.807939 | -0.000914 | 0.000440 | 0.957692 | 0.531410 | -0.018914 |
| candidate_ppopt182_pp180_rollback__source_huber_s0p24__rb_0p65__cap_0p004__3fc8a17792 | 0.269622 | 0.807946 | -0.000943 | 0.000447 | 0.957051 | 0.534295 | -0.018912 |
| candidate_ppopt182_pp180_rollback__source_huber_s0p3__rb_0p65__cap_0p004__ffc3f59d12 | 0.269614 | 0.807954 | -0.000950 | 0.000455 | 0.956731 | 0.529487 | -0.018901 |
| candidate_ppopt182_pp180_rollback__source_huber_s0p3__rb_0p65__cap_0p0025__96931b8878 | 0.269616 | 0.807954 | -0.000948 | 0.000455 | 0.956731 | 0.528846 | -0.018899 |
| candidate_ppopt182_pp180_rollback__source_huber_s0p24__rb_0p65__cap_0p0025__ed1fbdbcda | 0.269624 | 0.807946 | -0.000940 | 0.000447 | 0.956731 | 0.532372 | -0.018897 |
| candidate_ppopt182_pp180_rollback__source_huber_s0p18__rb_0p65__cap_0p004__4aa7f650e3 | 0.269648 | 0.807938 | -0.000916 | 0.000439 | 0.956731 | 0.540385 | -0.018878 |
| candidate_ppopt182_pp180_rollback__source_huber_s0p18__rb_0p85__cap_0p0025__07be0adca8 | 0.269686 | 0.807919 | -0.000878 | 0.000420 | 0.957051 | 0.543269 | -0.018866 |
| candidate_ppopt182_pp180_rollback__source_huber_s0p18__rb_0p65__cap_0p0025__0831ad8247 | 0.269650 | 0.807938 | -0.000914 | 0.000439 | 0.956410 | 0.540064 | -0.018863 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p02__s_0p3__cap_0p0035__a090aed33e | 0.269911 | 0.807440 | -0.000653 | -0.000059 | 0.954808 | 0.751282 | -0.018846 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p02__s_0p24__cap_0p0045__7dc819c59f | 0.269899 | 0.807401 | -0.000665 | -0.000098 | 0.954167 | 0.751603 | -0.018831 |
| candidate_ppopt185_adaptive_p95_cap__thr_0p04__s_0p3__basecap_0p0055__shrink_0p45__241624bada | 0.269902 | 0.807388 | -0.000662 | -0.000111 | 0.954167 | 0.754487 | -0.018829 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p02__s_0p24__cap_0p0035__f21ac3e3b0 | 0.269915 | 0.807401 | -0.000649 | -0.000098 | 0.954167 | 0.751603 | -0.018816 |
| candidate_ppopt185_adaptive_p95_cap__thr_0p04__s_0p3__basecap_0p0055__shrink_0p65__dd5fcf46da | 0.269908 | 0.807388 | -0.000656 | -0.000111 | 0.953846 | 0.754487 | -0.018810 |
| candidate_ppopt185_adaptive_p95_cap__thr_0p04__s_0p3__basecap_0p0055__shrink_0p85__b45aceb149 | 0.269914 | 0.807388 | -0.000650 | -0.000111 | 0.953846 | 0.754487 | -0.018804 |
| candidate_ppopt185_adaptive_p95_cap__thr_0p04__s_0p3__basecap_0p0045__shrink_0p45__781be646d7 | 0.269914 | 0.807388 | -0.000650 | -0.000111 | 0.953846 | 0.754487 | -0.018804 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p02__s_0p3__cap_0p0025__bc97964158 | 0.269927 | 0.807381 | -0.000637 | -0.000118 | 0.954167 | 0.751282 | -0.018803 |
| candidate_ppopt185_adaptive_p95_cap__thr_0p04__s_0p3__basecap_0p0045__shrink_0p65__8488d01fa2 | 0.269919 | 0.807388 | -0.000646 | -0.000111 | 0.953846 | 0.754487 | -0.018799 |
| candidate_ppopt185_adaptive_p95_cap__thr_0p04__s_0p3__basecap_0p0045__shrink_0p85__7796f371f8 | 0.269924 | 0.807388 | -0.000641 | -0.000111 | 0.953846 | 0.754487 | -0.018794 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p02__s_0p18__cap_0p0045__ffa2005146 | 0.269911 | 0.807359 | -0.000653 | -0.000140 | 0.953526 | 0.754487 | -0.018794 |
| candidate_ppopt185_adaptive_p95_cap__thr_0p04__s_0p3__basecap_0p0035__shrink_0p45__b47b5d8463 | 0.269927 | 0.807388 | -0.000637 | -0.000111 | 0.953846 | 0.754487 | -0.018791 |
| candidate_ppopt185_adaptive_p95_cap__thr_0p04__s_0p24__basecap_0p0055__shrink_0p45__620be671bd | 0.269912 | 0.807357 | -0.000652 | -0.000142 | 0.953205 | 0.754487 | -0.018780 |
| candidate_ppopt185_adaptive_p95_cap__thr_0p04__s_0p24__basecap_0p0055__shrink_0p65__b377824200 | 0.269915 | 0.807357 | -0.000649 | -0.000142 | 0.953205 | 0.754487 | -0.018777 |
| candidate_ppopt185_adaptive_p95_cap__thr_0p04__s_0p3__basecap_0p0035__shrink_0p65__46d9bf2a36 | 0.269931 | 0.807388 | -0.000633 | -0.000111 | 0.953526 | 0.754487 | -0.018774 |
| candidate_ppopt185_adaptive_p95_cap__thr_0p04__s_0p24__basecap_0p0055__shrink_0p85__ec0061b3d5 | 0.269919 | 0.807357 | -0.000645 | -0.000142 | 0.953205 | 0.754487 | -0.018773 |
| candidate_ppopt185_adaptive_p95_cap__thr_0p04__s_0p24__basecap_0p0045__shrink_0p45__452efcf408 | 0.269919 | 0.807357 | -0.000645 | -0.000142 | 0.953205 | 0.754487 | -0.018773 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p02__s_0p24__cap_0p0025__9f1d91e415 | 0.269933 | 0.807381 | -0.000631 | -0.000118 | 0.953526 | 0.751603 | -0.018772 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p02__s_0p18__cap_0p0035__6872a84200 | 0.269922 | 0.807359 | -0.000642 | -0.000140 | 0.953205 | 0.754487 | -0.018770 |
| candidate_ppopt185_adaptive_p95_cap__thr_0p04__s_0p3__basecap_0p0035__shrink_0p85__70eaae0868 | 0.269936 | 0.807373 | -0.000628 | -0.000125 | 0.953205 | 0.754487 | -0.018756 |
| candidate_ppopt185_adaptive_p95_cap__thr_0p04__s_0p24__basecap_0p0045__shrink_0p65__2cf13cd8b9 | 0.269924 | 0.807357 | -0.000640 | -0.000142 | 0.952885 | 0.754487 | -0.018755 |
| candidate_ppopt185_adaptive_p95_cap__thr_0p04__s_0p24__basecap_0p0045__shrink_0p85__015d836617 | 0.269929 | 0.807357 | -0.000635 | -0.000142 | 0.952885 | 0.754487 | -0.018750 |
| candidate_ppopt185_adaptive_p95_cap__thr_0p04__s_0p24__basecap_0p0035__shrink_0p45__a5e75d589e | 0.269932 | 0.807357 | -0.000632 | -0.000142 | 0.952885 | 0.754487 | -0.018748 |
| candidate_ppopt185_adaptive_p95_cap__thr_0p04__s_0p24__basecap_0p0035__shrink_0p65__e11a6017ba | 0.269935 | 0.807357 | -0.000629 | -0.000142 | 0.952564 | 0.754487 | -0.018731 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p02__s_0p18__cap_0p0025__c66862ca3d | 0.269938 | 0.807359 | -0.000626 | -0.000140 | 0.952564 | 0.754487 | -0.018729 |
| candidate_ppopt185_adaptive_p95_cap__thr_0p04__s_0p24__basecap_0p0035__shrink_0p85__1bd65f776c | 0.269939 | 0.807357 | -0.000625 | -0.000142 | 0.952564 | 0.754487 | -0.018727 |
| candidate_ppopt182_pp180_rollback__source_pp180__rb_0p25__cap_0p0025__542348b79e | 0.269933 | 0.807326 | -0.000631 | -0.000173 | 0.952244 | 0.754487 | -0.018721 |
| candidate_ppopt182_pp180_rollback__source_pp180__rb_0p25__cap_0p004__6fe616cf56 | 0.269933 | 0.807326 | -0.000631 | -0.000173 | 0.952244 | 0.754487 | -0.018721 |
| candidate_ppopt182_pp180_rollback__source_pp180__rb_0p45__cap_0p0025__889822a640 | 0.269933 | 0.807326 | -0.000631 | -0.000173 | 0.952244 | 0.754487 | -0.018721 |
| candidate_ppopt182_pp180_rollback__source_pp180__rb_0p45__cap_0p004__e2caa78f88 | 0.269933 | 0.807326 | -0.000631 | -0.000173 | 0.952244 | 0.754487 | -0.018721 |
| candidate_ppopt182_pp180_rollback__source_pp180__rb_0p65__cap_0p0025__59a82df5b0 | 0.269933 | 0.807326 | -0.000631 | -0.000173 | 0.952244 | 0.754487 | -0.018721 |
| candidate_ppopt182_pp180_rollback__source_pp180__rb_0p65__cap_0p004__522afc0863 | 0.269933 | 0.807326 | -0.000631 | -0.000173 | 0.952244 | 0.754487 | -0.018721 |
| candidate_ppopt182_pp180_rollback__source_pp180__rb_0p85__cap_0p0025__f08a8eb2f5 | 0.269933 | 0.807326 | -0.000631 | -0.000173 | 0.952244 | 0.754487 | -0.018721 |
| candidate_ppopt182_pp180_rollback__source_pp180__rb_0p85__cap_0p004__54976eb1d3 | 0.269933 | 0.807326 | -0.000631 | -0.000173 | 0.952244 | 0.754487 | -0.018721 |
| pp180_operational_reference | 0.269933 | 0.807326 | -0.000631 | -0.000173 | 0.952244 | 0.754487 | -0.018721 |
| candidate_ppopt185_adaptive_p95_cap__thr_0p04__s_0p18__basecap_0p0045__shrink_0p45__eeaeee4817 | 0.269933 | 0.807325 | -0.000631 | -0.000174 | 0.952244 | 0.754487 | -0.018721 |
| candidate_ppopt185_adaptive_p95_cap__thr_0p04__s_0p18__basecap_0p0055__shrink_0p45__30356bc589 | 0.269933 | 0.807325 | -0.000631 | -0.000174 | 0.952244 | 0.754487 | -0.018721 |
| candidate_ppopt185_adaptive_p95_cap__thr_0p04__s_0p18__basecap_0p0055__shrink_0p65__a6c044a145 | 0.269933 | 0.807325 | -0.000631 | -0.000174 | 0.952244 | 0.754487 | -0.018721 |
| candidate_ppopt185_adaptive_p95_cap__thr_0p04__s_0p18__basecap_0p0055__shrink_0p85__7c385f9a54 | 0.269933 | 0.807325 | -0.000631 | -0.000174 | 0.952244 | 0.754487 | -0.018721 |
| candidate_ppopt185_adaptive_p95_cap__thr_0p04__s_0p18__basecap_0p0045__shrink_0p65__14c3ed243e | 0.269933 | 0.807325 | -0.000631 | -0.000174 | 0.952244 | 0.754487 | -0.018721 |
| candidate_ppopt185_adaptive_p95_cap__thr_0p04__s_0p18__basecap_0p0045__shrink_0p85__d60d7edc88 | 0.269936 | 0.807325 | -0.000628 | -0.000174 | 0.952244 | 0.754487 | -0.018718 |
| candidate_ppopt185_adaptive_p95_cap__thr_0p04__s_0p18__basecap_0p0035__shrink_0p45__1c538981c8 | 0.269937 | 0.807325 | -0.000627 | -0.000174 | 0.952244 | 0.754487 | -0.018717 |
| candidate_ppopt185_adaptive_p95_cap__thr_0p04__s_0p18__basecap_0p0035__shrink_0p65__60a63e61f3 | 0.269941 | 0.807325 | -0.000623 | -0.000174 | 0.952244 | 0.754487 | -0.018713 |
| candidate_ppopt185_adaptive_p95_cap__thr_0p04__s_0p18__basecap_0p0035__shrink_0p85__936b7ef64e | 0.269945 | 0.807325 | -0.000619 | -0.000174 | 0.952244 | 0.754487 | -0.018709 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p02__s_0p12__cap_0p0035__aae42e3fec | 0.269938 | 0.807316 | -0.000626 | -0.000183 | 0.951923 | 0.754487 | -0.018703 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p02__s_0p12__cap_0p0045__b74b2d1120 | 0.269938 | 0.807316 | -0.000626 | -0.000183 | 0.951923 | 0.754487 | -0.018703 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p02__s_0p12__cap_0p0025__3e99eb0325 | 0.269944 | 0.807316 | -0.000620 | -0.000183 | 0.951923 | 0.754487 | -0.018697 |
| candidate_ppopt181_strict_huber_guard__seg_price_qwidth__thr_0p02__s_0p3__cap_0p0035__bb34f1eb2f | 0.269928 | 0.807695 | -0.000636 | 0.000196 | 0.954487 | 0.487179 | -0.018678 |
| candidate_ppopt181_strict_huber_guard__seg_price_qwidth__thr_0p02__s_0p24__cap_0p0035__7345cc1105 | 0.269931 | 0.807695 | -0.000633 | 0.000196 | 0.953846 | 0.487179 | -0.018649 |
| candidate_ppopt181_strict_huber_guard__seg_price_qwidth__thr_0p02__s_0p12__cap_0p0045__0a048986dd | 0.269941 | 0.807656 | -0.000623 | 0.000157 | 0.953205 | 0.487179 | -0.018642 |
| candidate_ppopt181_strict_huber_guard__seg_price_qwidth__thr_0p02__s_0p3__cap_0p0045__b28470e889 | 0.269913 | 0.807827 | -0.000651 | 0.000329 | 0.955449 | 0.488141 | -0.018639 |
| candidate_ppopt181_strict_huber_guard__seg_price_qwidth__thr_0p06__s_0p18__cap_0p0045__22c71231cc | 0.269939 | 0.807672 | -0.000625 | 0.000173 | 0.953205 | 0.487179 | -0.018632 |
| candidate_ppopt181_strict_huber_guard__seg_price_qwidth__thr_0p02__s_0p24__cap_0p0045__2e7d697800 | 0.269916 | 0.807827 | -0.000648 | 0.000329 | 0.954808 | 0.488141 | -0.018610 |
| candidate_ppopt181_strict_huber_guard__seg_price_qwidth__thr_0p06__s_0p3__cap_0p0045__4ed0776f59 | 0.269920 | 0.807827 | -0.000644 | 0.000329 | 0.954487 | 0.487179 | -0.018594 |
| candidate_ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p04__s_0p42__cap_0p0045__4ceb825b80 | 0.269961 | 0.807231 | -0.000603 | -0.000268 | 0.949359 | 0.598718 | -0.018578 |
| candidate_ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p08__s_0p42__cap_0p0045__ed08e78f7b | 0.269961 | 0.807231 | -0.000603 | -0.000268 | 0.949359 | 0.598718 | -0.018578 |
| candidate_ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p0__s_0p42__cap_0p0045__5622e1beff | 0.269961 | 0.807231 | -0.000603 | -0.000268 | 0.949359 | 0.598718 | -0.018578 |
| pp186_operational_huber_basis_p95_guard_challenger | 0.269961 | 0.807231 | -0.000603 | -0.000268 | 0.949359 | 0.598718 | -0.018578 |
| pp186_strict_huber_basis_p95_guard_challenger | 0.269961 | 0.807231 | -0.000603 | -0.000268 | 0.949359 | 0.598718 | -0.018578 |
| candidate_ppopt181_strict_huber_guard__seg_price_qwidth__thr_0p02__s_0p18__cap_0p0045__9d31006fd2 | 0.269924 | 0.807827 | -0.000640 | 0.000329 | 0.953846 | 0.487179 | -0.018563 |
| candidate_ppopt184_huber_p95_blend__partner_xgb_weighted__hshare_0p65__thr_0p04__s_0p42__cap_0p0045__b6afdcf5ce | 0.269963 | 0.807231 | -0.000601 | -0.000268 | 0.949038 | 0.598718 | -0.018562 |
| candidate_ppopt184_huber_p95_blend__partner_xgb_weighted__hshare_0p65__thr_0p0__s_0p42__cap_0p0045__eb57ab4dc6 | 0.269963 | 0.807231 | -0.000601 | -0.000268 | 0.949038 | 0.598718 | -0.018562 |
| candidate_ppopt184_huber_p95_blend__partner_xgb_weighted__hshare_0p65__thr_0p08__s_0p42__cap_0p0045__7dbf96b872 | 0.269964 | 0.807231 | -0.000600 | -0.000268 | 0.949038 | 0.598718 | -0.018561 |
| candidate_ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p04__s_0p42__cap_0p003__1addc0ba71 | 0.269970 | 0.807231 | -0.000594 | -0.000268 | 0.949038 | 0.601923 | -0.018556 |
| candidate_ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p08__s_0p42__cap_0p003__ebe4d08b8f | 0.269970 | 0.807231 | -0.000594 | -0.000268 | 0.949038 | 0.601923 | -0.018556 |
| candidate_ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p0__s_0p42__cap_0p003__322620f8bf | 0.269970 | 0.807231 | -0.000594 | -0.000268 | 0.949038 | 0.601923 | -0.018556 |
| candidate_ppopt184_huber_p95_blend__partner_xgb_weighted__hshare_0p65__thr_0p04__s_0p3__cap_0p0045__d30eff0395 | 0.269971 | 0.807231 | -0.000593 | -0.000268 | 0.949038 | 0.598718 | -0.018555 |
| candidate_ppopt184_huber_p95_blend__partner_xgb_weighted__hshare_0p65__thr_0p0__s_0p3__cap_0p0045__3df96cf994 | 0.269971 | 0.807231 | -0.000593 | -0.000268 | 0.949038 | 0.598718 | -0.018555 |
| candidate_ppopt184_huber_p95_blend__partner_xgb_weighted__hshare_0p65__thr_0p08__s_0p3__cap_0p0045__6388dbec8b | 0.269972 | 0.807231 | -0.000592 | -0.000268 | 0.949038 | 0.598718 | -0.018554 |
| candidate_ppopt181_strict_huber_guard__seg_price_qwidth__thr_0p06__s_0p24__cap_0p0045__e4d82519d7 | 0.269927 | 0.807819 | -0.000637 | 0.000320 | 0.953526 | 0.487179 | -0.018554 |
| candidate_ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p04__s_0p3__cap_0p003__578517ea8b | 0.269972 | 0.807231 | -0.000592 | -0.000268 | 0.949038 | 0.601923 | -0.018553 |
| candidate_ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p08__s_0p3__cap_0p003__f451fcf905 | 0.269972 | 0.807231 | -0.000592 | -0.000268 | 0.949038 | 0.601923 | -0.018553 |
| candidate_ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p0__s_0p3__cap_0p003__c521941109 | 0.269972 | 0.807231 | -0.000592 | -0.000268 | 0.949038 | 0.601923 | -0.018553 |
| candidate_ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p04__s_0p3__cap_0p0045__e2ac50c7ae | 0.269964 | 0.807231 | -0.000600 | -0.000268 | 0.948718 | 0.598718 | -0.018548 |
| candidate_ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p08__s_0p3__cap_0p0045__ade0073cc5 | 0.269964 | 0.807231 | -0.000600 | -0.000268 | 0.948718 | 0.598718 | -0.018548 |
| candidate_ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p0__s_0p3__cap_0p0045__07341454a5 | 0.269964 | 0.807231 | -0.000600 | -0.000268 | 0.948718 | 0.598718 | -0.018548 |
| candidate_ppopt184_huber_p95_blend__partner_xgb_weighted__hshare_0p65__thr_0p04__s_0p42__cap_0p003__cbb3f241af | 0.269972 | 0.807231 | -0.000593 | -0.000268 | 0.948397 | 0.601923 | -0.018528 |
| candidate_ppopt184_huber_p95_blend__partner_xgb_weighted__hshare_0p65__thr_0p0__s_0p42__cap_0p003__1c92f69cfe | 0.269972 | 0.807231 | -0.000593 | -0.000268 | 0.948397 | 0.601923 | -0.018528 |
| candidate_ppopt184_huber_p95_blend__partner_xgb_weighted__hshare_0p65__thr_0p08__s_0p42__cap_0p003__4b1cc6f95f | 0.269972 | 0.807231 | -0.000592 | -0.000268 | 0.948397 | 0.601923 | -0.018528 |
| candidate_ppopt181_strict_huber_guard__seg_price_qwidth__thr_0p14__s_0p3__cap_0p0025__9d7f54b0d9 | 0.269987 | 0.807313 | -0.000577 | -0.000186 | 0.948718 | 0.570513 | -0.018526 |
| candidate_ppopt181_strict_huber_guard__seg_price_qwidth__thr_0p14__s_0p3__cap_0p0035__1de2ea4204 | 0.269987 | 0.807313 | -0.000577 | -0.000186 | 0.948718 | 0.570513 | -0.018526 |
| candidate_ppopt181_strict_huber_guard__seg_price_qwidth__thr_0p14__s_0p3__cap_0p0045__ae5411c797 | 0.269987 | 0.807313 | -0.000577 | -0.000186 | 0.948718 | 0.570513 | -0.018526 |
| candidate_ppopt184_huber_p95_blend__partner_xgb_weighted__hshare_0p65__thr_0p04__s_0p3__cap_0p003__4e8f728731 | 0.269974 | 0.807231 | -0.000590 | -0.000268 | 0.948397 | 0.601923 | -0.018526 |
| candidate_ppopt184_huber_p95_blend__partner_xgb_weighted__hshare_0p65__thr_0p0__s_0p3__cap_0p003__a4b85975a8 | 0.269974 | 0.807231 | -0.000590 | -0.000268 | 0.948397 | 0.601923 | -0.018526 |
| candidate_ppopt184_huber_p95_blend__partner_xgb_weighted__hshare_0p65__thr_0p08__s_0p3__cap_0p003__399834153b | 0.269974 | 0.807231 | -0.000590 | -0.000268 | 0.948397 | 0.601923 | -0.018526 |
| candidate_ppopt184_huber_p95_blend__partner_xgb_weighted__hshare_0p65__thr_0p04__s_0p18__cap_0p0045__a47c26c29f | 0.269978 | 0.807231 | -0.000586 | -0.000268 | 0.948397 | 0.598718 | -0.018522 |
| candidate_ppopt184_huber_p95_blend__partner_xgb_weighted__hshare_0p65__thr_0p0__s_0p18__cap_0p0045__ceda00a161 | 0.269978 | 0.807231 | -0.000586 | -0.000268 | 0.948397 | 0.598718 | -0.018522 |
| candidate_ppopt184_huber_p95_blend__partner_xgb_weighted__hshare_0p65__thr_0p08__s_0p18__cap_0p0045__e0e6743c3b | 0.269979 | 0.807231 | -0.000585 | -0.000268 | 0.948397 | 0.598718 | -0.018521 |
| candidate_ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p04__s_0p18__cap_0p0045__966df6384c | 0.269968 | 0.807231 | -0.000596 | -0.000268 | 0.948077 | 0.598718 | -0.018519 |
| candidate_ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p08__s_0p18__cap_0p0045__65ff4cee62 | 0.269968 | 0.807231 | -0.000596 | -0.000268 | 0.948077 | 0.598718 | -0.018519 |
| candidate_ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p0__s_0p18__cap_0p0045__ea85ad7235 | 0.269968 | 0.807231 | -0.000596 | -0.000268 | 0.948077 | 0.598718 | -0.018519 |
| candidate_ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p04__s_0p18__cap_0p003__e9bae400dc | 0.269976 | 0.807231 | -0.000588 | -0.000268 | 0.948077 | 0.601923 | -0.018511 |
| candidate_ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p08__s_0p18__cap_0p003__b51ff05d9b | 0.269976 | 0.807231 | -0.000588 | -0.000268 | 0.948077 | 0.601923 | -0.018511 |
| candidate_ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p0__s_0p18__cap_0p003__d9e65bcc80 | 0.269976 | 0.807231 | -0.000588 | -0.000268 | 0.948077 | 0.601923 | -0.018511 |
| candidate_ppopt184_huber_p95_blend__partner_xgb_weighted__hshare_0p65__thr_0p04__s_0p18__cap_0p003__6cfb4b11c8 | 0.269981 | 0.807231 | -0.000583 | -0.000268 | 0.948077 | 0.601923 | -0.018506 |
| candidate_ppopt184_huber_p95_blend__partner_xgb_weighted__hshare_0p65__thr_0p0__s_0p18__cap_0p003__a8f6b29e2a | 0.269981 | 0.807231 | -0.000583 | -0.000268 | 0.948077 | 0.601923 | -0.018506 |
| candidate_ppopt184_huber_p95_blend__partner_xgb_weighted__hshare_0p65__thr_0p08__s_0p18__cap_0p003__dae26e1553 | 0.269981 | 0.807231 | -0.000583 | -0.000268 | 0.948077 | 0.601923 | -0.018506 |
| candidate_ppopt181_strict_huber_guard__seg_price_qwidth__thr_0p14__s_0p24__cap_0p0025__ce1bc95feb | 0.269989 | 0.807296 | -0.000575 | -0.000203 | 0.947756 | 0.570513 | -0.018486 |
| candidate_ppopt181_strict_huber_guard__seg_price_qwidth__thr_0p14__s_0p24__cap_0p0035__ce21e17aab | 0.269989 | 0.807296 | -0.000575 | -0.000203 | 0.947756 | 0.570513 | -0.018486 |
| candidate_ppopt181_strict_huber_guard__seg_price_qwidth__thr_0p14__s_0p24__cap_0p0045__dc00c787fb | 0.269989 | 0.807296 | -0.000575 | -0.000203 | 0.947756 | 0.570513 | -0.018486 |
| candidate_ppopt181_strict_huber_guard__seg_price_qwidth__thr_0p14__s_0p18__cap_0p0025__9779291a3e | 0.269991 | 0.807280 | -0.000573 | -0.000219 | 0.947756 | 0.570513 | -0.018483 |
| candidate_ppopt181_strict_huber_guard__seg_price_qwidth__thr_0p14__s_0p18__cap_0p0035__8f2e48e5bf | 0.269991 | 0.807280 | -0.000573 | -0.000219 | 0.947756 | 0.570513 | -0.018483 |
| candidate_ppopt181_strict_huber_guard__seg_price_qwidth__thr_0p14__s_0p18__cap_0p0045__2d61d82f8a | 0.269991 | 0.807280 | -0.000573 | -0.000219 | 0.947756 | 0.570513 | -0.018483 |
| candidate_ppopt181_strict_huber_guard__seg_price_qwidth__thr_0p14__s_0p12__cap_0p0025__1a80c1bb2c | 0.269993 | 0.807264 | -0.000571 | -0.000235 | 0.947436 | 0.570513 | -0.018468 |
| candidate_ppopt181_strict_huber_guard__seg_price_qwidth__thr_0p14__s_0p12__cap_0p0035__0b5650f220 | 0.269993 | 0.807264 | -0.000571 | -0.000235 | 0.947436 | 0.570513 | -0.018468 |
| candidate_ppopt181_strict_huber_guard__seg_price_qwidth__thr_0p14__s_0p12__cap_0p0045__a860b5ee9f | 0.269993 | 0.807264 | -0.000571 | -0.000235 | 0.947436 | 0.570513 | -0.018468 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p06__s_0p3__cap_0p0025__389a22a0d4 | 0.269994 | 0.807235 | -0.000570 | -0.000264 | 0.947115 | 0.744872 | -0.018454 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p06__s_0p3__cap_0p0035__79b1f99ccb | 0.269994 | 0.807235 | -0.000570 | -0.000264 | 0.947115 | 0.744872 | -0.018454 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p06__s_0p3__cap_0p0045__b2ed862955 | 0.269994 | 0.807235 | -0.000570 | -0.000264 | 0.947115 | 0.744872 | -0.018454 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p06__s_0p24__cap_0p0025__7e0c509484 | 0.269995 | 0.807234 | -0.000569 | -0.000265 | 0.947115 | 0.744872 | -0.018454 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p06__s_0p24__cap_0p0035__2643e7a5d3 | 0.269995 | 0.807234 | -0.000569 | -0.000265 | 0.947115 | 0.744872 | -0.018454 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p06__s_0p24__cap_0p0045__0536035e48 | 0.269995 | 0.807234 | -0.000569 | -0.000265 | 0.947115 | 0.744872 | -0.018454 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p06__s_0p18__cap_0p0025__a9a02243cf | 0.269996 | 0.807233 | -0.000569 | -0.000265 | 0.947115 | 0.744872 | -0.018453 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p06__s_0p18__cap_0p0035__2c178d46dc | 0.269996 | 0.807233 | -0.000569 | -0.000265 | 0.947115 | 0.744872 | -0.018453 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p06__s_0p18__cap_0p0045__4c6780c396 | 0.269996 | 0.807233 | -0.000569 | -0.000265 | 0.947115 | 0.744872 | -0.018453 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p06__s_0p12__cap_0p0025__8638c4e25f | 0.269996 | 0.807233 | -0.000568 | -0.000266 | 0.947115 | 0.744872 | -0.018452 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p06__s_0p12__cap_0p0035__bb0503fc8a | 0.269996 | 0.807233 | -0.000568 | -0.000266 | 0.947115 | 0.744872 | -0.018452 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p06__s_0p12__cap_0p0045__a982418319 | 0.269996 | 0.807233 | -0.000568 | -0.000266 | 0.947115 | 0.744872 | -0.018452 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p14__s_0p12__cap_0p0025__459702147a | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.947115 | 0.605449 | -0.018451 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p14__s_0p12__cap_0p0035__27733aded1 | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.947115 | 0.605449 | -0.018451 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p14__s_0p12__cap_0p0045__1b4c759190 | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.947115 | 0.605449 | -0.018451 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p14__s_0p18__cap_0p0025__89b750aef6 | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.947115 | 0.605449 | -0.018451 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p14__s_0p18__cap_0p0035__2aacdc78d5 | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.947115 | 0.605449 | -0.018451 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p14__s_0p18__cap_0p0045__f152fccc97 | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.947115 | 0.605449 | -0.018451 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p14__s_0p24__cap_0p0025__244233f78c | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.947115 | 0.605449 | -0.018451 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p14__s_0p24__cap_0p0035__5d39231f62 | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.947115 | 0.605449 | -0.018451 |
| candidate_ppopt181_strict_huber_guard__seg_price_conf__thr_0p14__s_0p24__cap_0p0045__f3f38c16db | 0.269997 | 0.807231 | -0.000567 | -0.000268 | 0.947115 | 0.605449 | -0.018451 |

## 실행 설정
```json
{
  "experiment_id": "PP-OPT181-186",
  "experiment_slug": "PP-OPT181_186_warm_huber_basis_p95_guard_refinement",
  "created_at": "2026-06-10T10:15:40",
  "base_candidate": "hcoef_stable",
  "previous_experiment": "experiments/track6/PP-OPT173_180_warm_basis_generation_challenger",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 526,
  "prediction_rows": 592276,
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
    "pp180_p95": "ppopt180_p95_basis_generation_challenger__source=reference_pp148_p95"
  },
  "selection_decision": {
    "operational_label": "candidate_ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p04__s_0p42__cap_0p0045__4ceb825b80",
    "operational_candidate": "ppopt184_huber_p95_blend__partner=cat_plain__hshare=0p65__thr=0p04__s=0p42__cap=0p0045",
    "operational_fixed_test_MAPE": 0.2699606338662266,
    "operational_fixed_test_p95_APE": 0.8072309115386983,
    "operational_delta_vs_pp64_MAPE": -0.0006034080494337624,
    "operational_delta_vs_pp64_p95_APE": -0.00026794076741154527,
    "operational_delta_vs_pp126_MAPE": -0.00015376288362523027,
    "operational_delta_vs_pp126_p95_APE": -0.000259149359149613,
    "operational_delta_vs_pp148_MAPE": -0.00017935450635281347,
    "operational_delta_vs_pp148_p95_APE": 0.0,
    "operational_delta_vs_pp166_MAPE": -3.635179901201324e-05,
    "operational_delta_vs_pp166_p95_APE": 0.0,
    "operational_delta_vs_pp172_MAPE": -3.6780794923974014e-05,
    "operational_delta_vs_pp172_p95_APE": 0.0,
    "operational_delta_vs_pp180_MAPE": 2.8007278438269e-05,
    "operational_delta_vs_pp180_p95_APE": -9.45931204405781e-05,
    "operational_avg_pp64_MAPE_win_rate": 0.9493589743589744,
    "operational_avg_pp64_p95_win_rate": 0.5987179487179487,
    "operational_replacement_score": -0.01857776702379274,
    "strict_guarded_label": "candidate_ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p04__s_0p42__cap_0p0045__4ceb825b80",
    "strict_guarded_candidate": "ppopt184_huber_p95_blend__partner=cat_plain__hshare=0p65__thr=0p04__s=0p42__cap=0p0045",
    "strict_guarded_fixed_test_MAPE": 0.2699606338662266,
    "strict_guarded_fixed_test_p95_APE": 0.8072309115386983,
    "strict_guarded_delta_vs_pp64_MAPE": -0.0006034080494337624,
    "strict_guarded_delta_vs_pp64_p95_APE": -0.00026794076741154527,
    "strict_guarded_delta_vs_pp126_MAPE": -0.00015376288362523027,
    "strict_guarded_delta_vs_pp126_p95_APE": -0.000259149359149613,
    "strict_guarded_delta_vs_pp148_MAPE": -0.00017935450635281347,
    "strict_guarded_delta_vs_pp148_p95_APE": 0.0,
    "strict_guarded_delta_vs_pp166_MAPE": -3.635179901201324e-05,
    "strict_guarded_delta_vs_pp166_p95_APE": 0.0,
    "strict_guarded_delta_vs_pp172_MAPE": -3.6780794923974014e-05,
    "strict_guarded_delta_vs_pp172_p95_APE": 0.0,
    "strict_guarded_delta_vs_pp180_MAPE": 2.8007278438269e-05,
    "strict_guarded_delta_vs_pp180_p95_APE": -9.45931204405781e-05,
    "strict_guarded_avg_pp64_MAPE_win_rate": 0.9493589743589744,
    "strict_guarded_avg_pp64_p95_win_rate": 0.5987179487179487,
    "strict_guarded_replacement_score": -0.01857776702379274,
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
    "p95_delta_vs_pp180_MAPE": 0.0003362993213196219,
    "p95_delta_vs_pp180_p95_APE": -0.0013761288369714686,
    "p95_avg_pp64_MAPE_win_rate": 0.5983974358974359,
    "p95_avg_pp64_p95_win_rate": 0.5009615384615385,
    "p95_replacement_score": -0.0040792899192624915,
    "operational_protocol_candidate": "ppopt186_operational_huber_basis_p95_guard__source=ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p04__s_0p42__cap_0p0045",
    "strict_guarded_protocol_candidate": "ppopt186_strict_guarded_huber_basis_p95_guard__source=ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p04__s_0p42__cap_0p0045",
    "p95_protocol_candidate": "ppopt186_p95_huber_basis_p95_guard__source=reference_pp148_p95"
  },
  "items": [
    {
      "item_id": "PP-OPT181",
      "priority": "1",
      "title": "strict Huber basis p95 guard",
      "description": "PP180의 stack_huber_weighted 기준가 이동에 p95 손상 segment guard를 더 강하게 건다."
    },
    {
      "item_id": "PP-OPT182",
      "priority": "2",
      "title": "PP180 rollback by p95 hazard",
      "description": "PP180이 PP172보다 p95를 나쁘게 만들 위험이 큰 구간은 PP172 쪽으로 되돌린다."
    },
    {
      "item_id": "PP-OPT183",
      "priority": "3",
      "title": "Cat/XGB p95-preserving basis",
      "description": "p95를 유지한 direct CatBoost/XGBoost basis 후보를 Huber 대체 기준가로 좁게 검증한다."
    },
    {
      "item_id": "PP-OPT184",
      "priority": "4",
      "title": "Huber and p95-preserving blend",
      "description": "Huber basis의 MAPE 개선과 Cat/XGB basis의 p95 유지 신호를 합의 방향에서만 섞는다."
    },
    {
      "item_id": "PP-OPT185",
      "priority": "5",
      "title": "adaptive p95 cap tier",
      "description": "p95 손상 위험 구간에서는 cap을 더 줄이고, 안정 구간에서만 Huber 이동량을 허용한다."
    },
    {
      "item_id": "PP-OPT186",
      "priority": "6",
      "title": "final Huber basis p95-guard decision",
      "description": "PP180/PP172와 신규 p95-guard 후보를 fixed/repeated 기준으로 비교해 선택한다."
    }
  ],
  "sources": {
    "pp173_helper": "scripts/track6/run_pp_opt173_180_warm_basis_generation_challenger.py",
    "basis_model_detail": "experiments/track6/PP-OPT173_180_warm_basis_generation_challenger/artifacts/basis_model_detail_aligned.csv",
    "basis_feature_detail": "experiments/track6/PP-OPT173_180_warm_basis_generation_challenger/artifacts/basis_feature_band_detail.csv"
  }
}
```