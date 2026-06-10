# PP-OPT89~95 Warm guarded tail-routing 실험 결과

- 작성일: 2026-06-09 14:04
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 결론: PP95 운영형도 운영 교체는 보류. 운영형 fixed test는 PP64 대비 MAPE -0.000005, p95 -0.000009.

## 주요 후보 test 비교
| candidate | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- |
| reference_pp82_operational | 0.137878 | 0.270557 | 0.807450 | 0.397982 | -0.000838 | -0.000680 |
| reference_pp81_best | 0.137878 | 0.270559 | 0.807490 | 0.397989 | -0.000836 | -0.000640 |
| ppopt95_operational_guarded_tail_challenger__source=ppopt93_pp81_tail_boost__target_pp82op__score_risk_prob__thr_0p76__width_0p18__s_0p1 | 0.137878 | 0.270559 | 0.807490 | 0.397989 | -0.000836 | -0.000640 |
| reference_pp70_refinement | 0.137878 | 0.270561 | 0.807490 | 0.397991 | -0.000834 | -0.000640 |
| reference_pp64_current_best | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |
| ppopt95_p95_guarded_tail_challenger__source=ppopt94_p95_guard__target_pp82op__score_risk_focus__thr_0p7__width_0p32__s_0p2 | 0.137634 | 0.270651 | 0.806840 | 0.397982 | -0.000744 | -0.001290 |
| reference_pp82_p95 | 0.137634 | 0.270651 | 0.806840 | 0.397982 | -0.000744 | -0.001290 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | p95_test_MAPE | p95_test_p95_APE | operational_pass_vs_incumbent | best_family | best_candidate | p95_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | p95 mode guard | 144 | 0.270627 | 0.806871 | 0.270651 | 0.806840 | True | p95_mode_mape_guard | ppopt94_p95_guard__target=pp81__score=generic_risk__thr=0p5__width=0p32__s=0p75 | ppopt94_p95_guard__target=pp82op__score=risk_focus__thr=0p7__width=0p32__s=0p2 |
| 7 | final guarded tail-routing challenger | 2 | 0.270651 | 0.806840 | 0.270651 | 0.806840 | True | guarded_tail_p95_selection | ppopt95_p95_guarded_tail_challenger__source=ppopt94_p95_guard__target_pp82op__score_risk_focus__thr_0p7__width_0p32__s_0p2 | ppopt95_p95_guarded_tail_challenger__source=ppopt94_p95_guard__target_pp82op__score_risk_focus__thr_0p7__width_0p32__s_0p2 |
| 5 | PP81 stable route plus PP82 tail boost | 192 | 0.270559 | 0.807490 | 0.270566 | 0.807463 | True | pp81_stable_tail_boost | ppopt93_pp81_tail_boost__target=pp82op__score=risk_prob__thr=0p76__width=0p18__s=0p1 | ppopt93_pp81_tail_boost__target=pp82p95__score=p95_prob__thr=0p46__width=0p18__s=0p5 |
| 2 | weaker hard-tail fallback local grid | 450 | 0.270560 | 0.807490 | 0.270556 | 0.807437 | True | weaker_hard_tail_local_grid | ppopt90_weaker_tail__helper=balanced_stable__score=risk_prob__thr=0p62__width=0p18__s=1p0 | ppopt90_weaker_tail__helper=pp20__score=p95_prob__thr=0p62__width=0p18__s=1p0 |
| 3 | soft helper tail fallback | 144 | 0.270561 | 0.807490 | 0.270574 | 0.807470 | True | soft_helper_tail_fallback | ppopt91_soft_helper__helper=pp48_bias__thr=0p78__width=0p42__s=0p25 | ppopt91_soft_helper__helper=p95_weighted__thr=0p54__width=0p18__s=0p76 |
| 4 | quantile-direction guarded fallback | 288 | 0.270561 | 0.807490 | 0.270571 | 0.807432 | True | quantile_direction_guarded_tail | ppopt92_qdir_guard__helper=balanced_stable__pen=0p0__thr=0p74__width=0p3__s=0p45 | ppopt92_qdir_guard__helper=pp20__pen=0p65__thr=0p58__width=0p18__s=1p0 |
| 1 | PP82 risk-focus rollback shrink | 360 | 0.270548 | 0.807482 | 0.270557 | 0.807451 | True | pp82_risk_focus_shrink | ppopt89_risk_shrink__target=pp81__score=generic_risk__thr=0p48__width=0p3__s=0p9 | ppopt89_risk_shrink__target=pp81__score=p95_prob__thr=0p72__width=0p42__s=0p2 |

## 운영 통과 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| reference_pp48_score | REFERENCE | reference_prior | 0.270816 | 0.807385 | -0.000579 | -0.000745 | 1.000000 | 0.900000 | -0.002413 |
| ppopt94_p95_guard__target=pp81__score=generic_risk__thr=0p5__width=0p32__s=0p75 | PP-OPT94 | p95_mode_mape_guard | 0.270627 | 0.806871 | -0.000767 | -0.001259 | 1.000000 | 0.550000 | -0.001437 |
| ppopt94_p95_guard__target=pp81__score=risk_focus__thr=0p5__width=0p32__s=0p75 | PP-OPT94 | p95_mode_mape_guard | 0.270636 | 0.806870 | -0.000759 | -0.001260 | 1.000000 | 0.550000 | -0.001436 |
| ppopt94_p95_guard__target=pp70__score=generic_risk__thr=0p5__width=0p32__s=0p75 | PP-OPT94 | p95_mode_mape_guard | 0.270629 | 0.806871 | -0.000766 | -0.001259 | 1.000000 | 0.550000 | -0.001436 |
| ppopt94_p95_guard__target=pp70__score=risk_focus__thr=0p5__width=0p32__s=0p75 | PP-OPT94 | p95_mode_mape_guard | 0.270638 | 0.806870 | -0.000757 | -0.001260 | 1.000000 | 0.550000 | -0.001435 |
| ppopt94_p95_guard__target=pp81__score=generic_risk__thr=0p6__width=0p18__s=0p75 | PP-OPT94 | p95_mode_mape_guard | 0.270636 | 0.806873 | -0.000759 | -0.001257 | 1.000000 | 0.550000 | -0.001433 |
| ppopt94_p95_guard__target=pp81__score=generic_risk__thr=0p5__width=0p18__s=0p55 | PP-OPT94 | p95_mode_mape_guard | 0.270626 | 0.806869 | -0.000769 | -0.001261 | 1.000000 | 0.550000 | -0.001433 |
| ppopt94_p95_guard__target=pp70__score=generic_risk__thr=0p5__width=0p18__s=0p55 | PP-OPT94 | p95_mode_mape_guard | 0.270627 | 0.806869 | -0.000767 | -0.001261 | 1.000000 | 0.550000 | -0.001432 |
| ppopt94_p95_guard__target=pp70__score=generic_risk__thr=0p6__width=0p18__s=0p75 | PP-OPT94 | p95_mode_mape_guard | 0.270637 | 0.806873 | -0.000758 | -0.001257 | 1.000000 | 0.550000 | -0.001432 |
| ppopt94_p95_guard__target=pp81__score=risk_focus__thr=0p6__width=0p18__s=0p75 | PP-OPT94 | p95_mode_mape_guard | 0.270640 | 0.806871 | -0.000754 | -0.001259 | 1.000000 | 0.550000 | -0.001432 |
| ppopt94_p95_guard__target=pp70__score=risk_focus__thr=0p6__width=0p18__s=0p75 | PP-OPT94 | p95_mode_mape_guard | 0.270642 | 0.806871 | -0.000753 | -0.001259 | 1.000000 | 0.550000 | -0.001431 |
| ppopt94_p95_guard__target=pp81__score=generic_risk__thr=0p5__width=0p32__s=0p55 | PP-OPT94 | p95_mode_mape_guard | 0.270634 | 0.806863 | -0.000761 | -0.001267 | 1.000000 | 0.550000 | -0.001430 |
| ppopt94_p95_guard__target=pp81__score=generic_risk__thr=0p7__width=0p18__s=0p75 | PP-OPT94 | p95_mode_mape_guard | 0.270643 | 0.806850 | -0.000752 | -0.001280 | 1.000000 | 0.550000 | -0.001430 |
| ppopt94_p95_guard__target=pp81__score=generic_risk__thr=0p6__width=0p32__s=0p75 | PP-OPT94 | p95_mode_mape_guard | 0.270640 | 0.806858 | -0.000755 | -0.001272 | 1.000000 | 0.550000 | -0.001430 |
| ppopt94_p95_guard__target=pp81__score=risk_focus__thr=0p5__width=0p32__s=0p55 | PP-OPT94 | p95_mode_mape_guard | 0.270640 | 0.806862 | -0.000755 | -0.001268 | 1.000000 | 0.550000 | -0.001430 |
| ppopt94_p95_guard__target=pp70__score=generic_risk__thr=0p5__width=0p32__s=0p55 | PP-OPT94 | p95_mode_mape_guard | 0.270635 | 0.806863 | -0.000760 | -0.001267 | 1.000000 | 0.550000 | -0.001430 |
| ppopt94_p95_guard__target=pp70__score=generic_risk__thr=0p7__width=0p18__s=0p75 | PP-OPT94 | p95_mode_mape_guard | 0.270644 | 0.806850 | -0.000751 | -0.001280 | 1.000000 | 0.550000 | -0.001429 |
| ppopt94_p95_guard__target=pp70__score=risk_focus__thr=0p5__width=0p32__s=0p55 | PP-OPT94 | p95_mode_mape_guard | 0.270641 | 0.806862 | -0.000754 | -0.001268 | 1.000000 | 0.550000 | -0.001429 |
| ppopt94_p95_guard__target=pp70__score=generic_risk__thr=0p6__width=0p32__s=0p75 | PP-OPT94 | p95_mode_mape_guard | 0.270641 | 0.806858 | -0.000754 | -0.001272 | 1.000000 | 0.550000 | -0.001429 |
| ppopt94_p95_guard__target=pp81__score=generic_risk__thr=0p6__width=0p18__s=0p55 | PP-OPT94 | p95_mode_mape_guard | 0.270640 | 0.806864 | -0.000755 | -0.001266 | 1.000000 | 0.550000 | -0.001428 |
| ppopt94_p95_guard__target=pp70__score=generic_risk__thr=0p6__width=0p18__s=0p55 | PP-OPT94 | p95_mode_mape_guard | 0.270641 | 0.806864 | -0.000754 | -0.001266 | 1.000000 | 0.550000 | -0.001427 |
| ppopt94_p95_guard__target=pp81__score=risk_focus__thr=0p6__width=0p18__s=0p55 | PP-OPT94 | p95_mode_mape_guard | 0.270643 | 0.806863 | -0.000752 | -0.001267 | 1.000000 | 0.550000 | -0.001427 |
| ppopt94_p95_guard__target=pp70__score=risk_focus__thr=0p6__width=0p18__s=0p55 | PP-OPT94 | p95_mode_mape_guard | 0.270644 | 0.806863 | -0.000750 | -0.001267 | 1.000000 | 0.550000 | -0.001426 |
| ppopt94_p95_guard__target=pp81__score=risk_focus__thr=0p6__width=0p32__s=0p75 | PP-OPT94 | p95_mode_mape_guard | 0.270645 | 0.806857 | -0.000750 | -0.001273 | 1.000000 | 0.550000 | -0.001426 |
| ppopt94_p95_guard__target=pp81__score=risk_focus__thr=0p7__width=0p18__s=0p75 | PP-OPT94 | p95_mode_mape_guard | 0.270646 | 0.806849 | -0.000749 | -0.001281 | 1.000000 | 0.550000 | -0.001426 |
| ppopt94_p95_guard__target=pp81__score=generic_risk__thr=0p5__width=0p18__s=0p35 | PP-OPT94 | p95_mode_mape_guard | 0.270635 | 0.806859 | -0.000760 | -0.001271 | 1.000000 | 0.550000 | -0.001426 |
| ppopt94_p95_guard__target=pp70__score=risk_focus__thr=0p7__width=0p18__s=0p75 | PP-OPT94 | p95_mode_mape_guard | 0.270646 | 0.806849 | -0.000749 | -0.001281 | 1.000000 | 0.550000 | -0.001426 |
| ppopt94_p95_guard__target=pp81__score=generic_risk__thr=0p7__width=0p18__s=0p55 | PP-OPT94 | p95_mode_mape_guard | 0.270645 | 0.806847 | -0.000750 | -0.001283 | 1.000000 | 0.550000 | -0.001425 |
| ppopt94_p95_guard__target=pp70__score=risk_focus__thr=0p6__width=0p32__s=0p75 | PP-OPT94 | p95_mode_mape_guard | 0.270646 | 0.806857 | -0.000749 | -0.001273 | 1.000000 | 0.550000 | -0.001425 |
| ppopt94_p95_guard__target=pp81__score=generic_risk__thr=0p6__width=0p32__s=0p55 | PP-OPT94 | p95_mode_mape_guard | 0.270643 | 0.806853 | -0.000752 | -0.001277 | 1.000000 | 0.550000 | -0.001425 |
| ppopt94_p95_guard__target=pp70__score=generic_risk__thr=0p5__width=0p18__s=0p35 | PP-OPT94 | p95_mode_mape_guard | 0.270636 | 0.806859 | -0.000759 | -0.001271 | 1.000000 | 0.550000 | -0.001425 |
| ppopt94_p95_guard__target=pp81__score=risk_focus__thr=0p5__width=0p18__s=0p35 | PP-OPT94 | p95_mode_mape_guard | 0.270642 | 0.806859 | -0.000753 | -0.001271 | 1.000000 | 0.550000 | -0.001425 |
| ppopt94_p95_guard__target=pp70__score=generic_risk__thr=0p7__width=0p18__s=0p55 | PP-OPT94 | p95_mode_mape_guard | 0.270646 | 0.806847 | -0.000749 | -0.001283 | 1.000000 | 0.550000 | -0.001425 |
| ppopt94_p95_guard__target=pp70__score=generic_risk__thr=0p6__width=0p32__s=0p55 | PP-OPT94 | p95_mode_mape_guard | 0.270644 | 0.806853 | -0.000751 | -0.001277 | 1.000000 | 0.550000 | -0.001425 |
| ppopt94_p95_guard__target=pp70__score=risk_focus__thr=0p5__width=0p18__s=0p35 | PP-OPT94 | p95_mode_mape_guard | 0.270643 | 0.806859 | -0.000752 | -0.001271 | 1.000000 | 0.550000 | -0.001424 |
| ppopt94_p95_guard__target=pp81__score=generic_risk__thr=0p5__width=0p32__s=0p35 | PP-OPT94 | p95_mode_mape_guard | 0.270640 | 0.806854 | -0.000755 | -0.001276 | 1.000000 | 0.550000 | -0.001424 |
| ppopt94_p95_guard__target=pp81__score=generic_risk__thr=0p7__width=0p32__s=0p75 | PP-OPT94 | p95_mode_mape_guard | 0.270647 | 0.806845 | -0.000748 | -0.001285 | 1.000000 | 0.550000 | -0.001423 |
| ppopt94_p95_guard__target=pp81__score=risk_focus__thr=0p5__width=0p32__s=0p35 | PP-OPT94 | p95_mode_mape_guard | 0.270644 | 0.806854 | -0.000751 | -0.001276 | 1.000000 | 0.550000 | -0.001423 |
| ppopt94_p95_guard__target=pp70__score=generic_risk__thr=0p5__width=0p32__s=0p35 | PP-OPT94 | p95_mode_mape_guard | 0.270641 | 0.806854 | -0.000754 | -0.001276 | 1.000000 | 0.550000 | -0.001423 |
| ppopt94_p95_guard__target=pp70__score=risk_focus__thr=0p5__width=0p32__s=0p35 | PP-OPT94 | p95_mode_mape_guard | 0.270645 | 0.806854 | -0.000750 | -0.001276 | 1.000000 | 0.550000 | -0.001423 |
| ppopt94_p95_guard__target=pp70__score=generic_risk__thr=0p7__width=0p32__s=0p75 | PP-OPT94 | p95_mode_mape_guard | 0.270647 | 0.806845 | -0.000748 | -0.001285 | 1.000000 | 0.550000 | -0.001423 |
| ppopt94_p95_guard__target=pp81__score=risk_focus__thr=0p6__width=0p32__s=0p55 | PP-OPT94 | p95_mode_mape_guard | 0.270647 | 0.806853 | -0.000748 | -0.001277 | 1.000000 | 0.550000 | -0.001422 |
| ppopt94_p95_guard__target=pp81__score=risk_focus__thr=0p7__width=0p18__s=0p55 | PP-OPT94 | p95_mode_mape_guard | 0.270647 | 0.806846 | -0.000748 | -0.001284 | 1.000000 | 0.550000 | -0.001422 |
| ppopt94_p95_guard__target=pp81__score=generic_risk__thr=0p6__width=0p18__s=0p35 | PP-OPT94 | p95_mode_mape_guard | 0.270644 | 0.806855 | -0.000751 | -0.001275 | 1.000000 | 0.550000 | -0.001422 |
| ppopt94_p95_guard__target=pp70__score=risk_focus__thr=0p7__width=0p18__s=0p55 | PP-OPT94 | p95_mode_mape_guard | 0.270648 | 0.806846 | -0.000747 | -0.001284 | 1.000000 | 0.550000 | -0.001422 |
| ppopt94_p95_guard__target=pp70__score=risk_focus__thr=0p6__width=0p32__s=0p55 | PP-OPT94 | p95_mode_mape_guard | 0.270647 | 0.806853 | -0.000748 | -0.001277 | 1.000000 | 0.550000 | -0.001422 |
| ppopt94_p95_guard__target=pp70__score=generic_risk__thr=0p6__width=0p18__s=0p35 | PP-OPT94 | p95_mode_mape_guard | 0.270645 | 0.806855 | -0.000750 | -0.001275 | 1.000000 | 0.550000 | -0.001422 |
| ppopt94_p95_guard__target=pp81__score=risk_focus__thr=0p6__width=0p18__s=0p35 | PP-OPT94 | p95_mode_mape_guard | 0.270646 | 0.806854 | -0.000749 | -0.001276 | 1.000000 | 0.550000 | -0.001422 |
| ppopt94_p95_guard__target=pp70__score=risk_focus__thr=0p6__width=0p18__s=0p35 | PP-OPT94 | p95_mode_mape_guard | 0.270647 | 0.806854 | -0.000748 | -0.001276 | 1.000000 | 0.550000 | -0.001421 |
| ppopt94_p95_guard__target=pp81__score=generic_risk__thr=0p7__width=0p18__s=0p35 | PP-OPT94 | p95_mode_mape_guard | 0.270647 | 0.806844 | -0.000747 | -0.001286 | 1.000000 | 0.550000 | -0.001421 |

## p95 상위 후보
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| previous_challenger_pp20 | REFERENCE | reference_prior | 0.271182 | 0.806472 | -0.000213 | -0.001658 | 1.000000 | 0.554167 | -0.000883 |
| reference_pp82_p95 | REFERENCE | reference_prior | 0.270651 | 0.806840 | -0.000744 | -0.001290 | 1.000000 | 0.550000 | -0.001412 |
| ppopt94_p95_guard__target=pp82op__score=risk_focus__thr=0p7__width=0p32__s=0p2 | PP-OPT94 | p95_mode_mape_guard | 0.270651 | 0.806840 | -0.000744 | -0.001290 | 1.000000 | 0.550000 | -0.001412 |
| ppopt95_p95_guarded_tail_challenger__source=ppopt94_p95_guard__target_pp82op__score_risk_focus__thr_0p7__width_0p32__s_0p2 | PP-OPT95 | guarded_tail_p95_selection | 0.270651 | 0.806840 | -0.000744 | -0.001290 | 1.000000 | 0.550000 | -0.001412 |
| ppopt94_p95_guard__target=pp82op__score=generic_risk__thr=0p7__width=0p32__s=0p2 | PP-OPT94 | p95_mode_mape_guard | 0.270651 | 0.806840 | -0.000744 | -0.001290 | 1.000000 | 0.550000 | -0.001411 |
| ppopt94_p95_guard__target=pp82op__score=risk_focus__thr=0p7__width=0p32__s=0p35 | PP-OPT94 | p95_mode_mape_guard | 0.270651 | 0.806840 | -0.000744 | -0.001290 | 1.000000 | 0.550000 | -0.001411 |
| ppopt94_p95_guard__target=pp82op__score=risk_focus__thr=0p7__width=0p18__s=0p2 | PP-OPT94 | p95_mode_mape_guard | 0.270651 | 0.806840 | -0.000744 | -0.001290 | 1.000000 | 0.550000 | -0.001411 |
| ppopt94_p95_guard__target=pp82op__score=generic_risk__thr=0p7__width=0p32__s=0p35 | PP-OPT94 | p95_mode_mape_guard | 0.270651 | 0.806840 | -0.000744 | -0.001290 | 1.000000 | 0.550000 | -0.001410 |
| ppopt94_p95_guard__target=pp82op__score=generic_risk__thr=0p7__width=0p18__s=0p2 | PP-OPT94 | p95_mode_mape_guard | 0.270651 | 0.806840 | -0.000744 | -0.001290 | 1.000000 | 0.550000 | -0.001410 |
| ppopt94_p95_guard__target=pp82op__score=risk_focus__thr=0p7__width=0p32__s=0p55 | PP-OPT94 | p95_mode_mape_guard | 0.270651 | 0.806841 | -0.000744 | -0.001289 | 1.000000 | 0.550000 | -0.001411 |
| ppopt94_p95_guard__target=pp82op__score=risk_focus__thr=0p7__width=0p18__s=0p35 | PP-OPT94 | p95_mode_mape_guard | 0.270651 | 0.806841 | -0.000744 | -0.001289 | 1.000000 | 0.550000 | -0.001410 |
| ppopt94_p95_guard__target=pp82op__score=generic_risk__thr=0p7__width=0p32__s=0p55 | PP-OPT94 | p95_mode_mape_guard | 0.270651 | 0.806841 | -0.000744 | -0.001289 | 1.000000 | 0.550000 | -0.001409 |
| ppopt94_p95_guard__target=pp82op__score=risk_focus__thr=0p6__width=0p32__s=0p2 | PP-OPT94 | p95_mode_mape_guard | 0.270651 | 0.806841 | -0.000744 | -0.001289 | 1.000000 | 0.550000 | -0.001411 |
| ppopt94_p95_guard__target=pp82op__score=generic_risk__thr=0p7__width=0p18__s=0p35 | PP-OPT94 | p95_mode_mape_guard | 0.270651 | 0.806841 | -0.000744 | -0.001289 | 1.000000 | 0.550000 | -0.001409 |
| ppopt94_p95_guard__target=pp82op__score=generic_risk__thr=0p6__width=0p32__s=0p2 | PP-OPT94 | p95_mode_mape_guard | 0.270650 | 0.806841 | -0.000745 | -0.001289 | 1.000000 | 0.550000 | -0.001411 |
| ppopt94_p95_guard__target=pp81__score=risk_focus__thr=0p7__width=0p32__s=0p2 | PP-OPT94 | p95_mode_mape_guard | 0.270650 | 0.806841 | -0.000744 | -0.001289 | 1.000000 | 0.550000 | -0.001414 |
| ppopt94_p95_guard__target=pp70__score=risk_focus__thr=0p7__width=0p32__s=0p2 | PP-OPT94 | p95_mode_mape_guard | 0.270651 | 0.806841 | -0.000744 | -0.001289 | 1.000000 | 0.550000 | -0.001414 |
| ppopt94_p95_guard__target=pp82op__score=risk_focus__thr=0p7__width=0p32__s=0p75 | PP-OPT94 | p95_mode_mape_guard | 0.270651 | 0.806841 | -0.000744 | -0.001289 | 1.000000 | 0.550000 | -0.001410 |
| ppopt94_p95_guard__target=pp81__score=generic_risk__thr=0p7__width=0p32__s=0p2 | PP-OPT94 | p95_mode_mape_guard | 0.270650 | 0.806841 | -0.000745 | -0.001289 | 1.000000 | 0.550000 | -0.001415 |
| ppopt94_p95_guard__target=pp70__score=generic_risk__thr=0p7__width=0p32__s=0p2 | PP-OPT94 | p95_mode_mape_guard | 0.270650 | 0.806841 | -0.000745 | -0.001289 | 1.000000 | 0.550000 | -0.001415 |
| ppopt94_p95_guard__target=pp82op__score=generic_risk__thr=0p7__width=0p32__s=0p75 | PP-OPT94 | p95_mode_mape_guard | 0.270651 | 0.806841 | -0.000744 | -0.001289 | 1.000000 | 0.550000 | -0.001408 |
| ppopt94_p95_guard__target=pp82op__score=risk_focus__thr=0p7__width=0p18__s=0p55 | PP-OPT94 | p95_mode_mape_guard | 0.270651 | 0.806841 | -0.000744 | -0.001289 | 1.000000 | 0.550000 | -0.001409 |
| ppopt94_p95_guard__target=pp82op__score=generic_risk__thr=0p7__width=0p18__s=0p55 | PP-OPT94 | p95_mode_mape_guard | 0.270651 | 0.806842 | -0.000744 | -0.001288 | 1.000000 | 0.550000 | -0.001407 |
| ppopt94_p95_guard__target=pp82op__score=risk_focus__thr=0p5__width=0p32__s=0p2 | PP-OPT94 | p95_mode_mape_guard | 0.270649 | 0.806842 | -0.000746 | -0.001288 | 1.000000 | 0.550000 | -0.001411 |
| ppopt94_p95_guard__target=pp82op__score=risk_focus__thr=0p6__width=0p32__s=0p35 | PP-OPT94 | p95_mode_mape_guard | 0.270651 | 0.806842 | -0.000744 | -0.001288 | 1.000000 | 0.550000 | -0.001410 |
| ppopt94_p95_guard__target=pp82op__score=generic_risk__thr=0p5__width=0p32__s=0p2 | PP-OPT94 | p95_mode_mape_guard | 0.270647 | 0.806842 | -0.000748 | -0.001288 | 1.000000 | 0.550000 | -0.001411 |
| ppopt94_p95_guard__target=pp82op__score=risk_focus__thr=0p6__width=0p18__s=0p2 | PP-OPT94 | p95_mode_mape_guard | 0.270651 | 0.806842 | -0.000744 | -0.001288 | 1.000000 | 0.550000 | -0.001410 |
| ppopt94_p95_guard__target=pp82op__score=generic_risk__thr=0p6__width=0p32__s=0p35 | PP-OPT94 | p95_mode_mape_guard | 0.270649 | 0.806842 | -0.000745 | -0.001288 | 1.000000 | 0.550000 | -0.001409 |
| ppopt94_p95_guard__target=pp82op__score=generic_risk__thr=0p6__width=0p18__s=0p2 | PP-OPT94 | p95_mode_mape_guard | 0.270649 | 0.806842 | -0.000745 | -0.001288 | 1.000000 | 0.550000 | -0.001410 |
| ppopt94_p95_guard__target=pp81__score=risk_focus__thr=0p7__width=0p32__s=0p35 | PP-OPT94 | p95_mode_mape_guard | 0.270650 | 0.806842 | -0.000745 | -0.001288 | 1.000000 | 0.550000 | -0.001416 |
| ppopt94_p95_guard__target=pp70__score=risk_focus__thr=0p7__width=0p32__s=0p35 | PP-OPT94 | p95_mode_mape_guard | 0.270650 | 0.806842 | -0.000745 | -0.001288 | 1.000000 | 0.550000 | -0.001416 |
| ppopt94_p95_guard__target=pp81__score=risk_focus__thr=0p7__width=0p18__s=0p2 | PP-OPT94 | p95_mode_mape_guard | 0.270650 | 0.806842 | -0.000745 | -0.001288 | 1.000000 | 0.550000 | -0.001416 |
| ppopt94_p95_guard__target=pp70__score=risk_focus__thr=0p7__width=0p18__s=0p2 | PP-OPT94 | p95_mode_mape_guard | 0.270650 | 0.806842 | -0.000745 | -0.001288 | 1.000000 | 0.550000 | -0.001416 |
| ppopt94_p95_guard__target=pp82op__score=risk_focus__thr=0p7__width=0p18__s=0p75 | PP-OPT94 | p95_mode_mape_guard | 0.270650 | 0.806842 | -0.000745 | -0.001288 | 1.000000 | 0.550000 | -0.001408 |
| ppopt94_p95_guard__target=pp81__score=generic_risk__thr=0p7__width=0p32__s=0p35 | PP-OPT94 | p95_mode_mape_guard | 0.270649 | 0.806842 | -0.000746 | -0.001288 | 1.000000 | 0.550000 | -0.001417 |
| ppopt94_p95_guard__target=pp70__score=generic_risk__thr=0p7__width=0p32__s=0p35 | PP-OPT94 | p95_mode_mape_guard | 0.270649 | 0.806842 | -0.000745 | -0.001288 | 1.000000 | 0.550000 | -0.001417 |
| ppopt94_p95_guard__target=pp81__score=generic_risk__thr=0p7__width=0p18__s=0p2 | PP-OPT94 | p95_mode_mape_guard | 0.270649 | 0.806842 | -0.000746 | -0.001288 | 1.000000 | 0.550000 | -0.001417 |
| ppopt94_p95_guard__target=pp70__score=generic_risk__thr=0p7__width=0p18__s=0p2 | PP-OPT94 | p95_mode_mape_guard | 0.270649 | 0.806842 | -0.000746 | -0.001288 | 1.000000 | 0.550000 | -0.001417 |
| ppopt94_p95_guard__target=pp82op__score=generic_risk__thr=0p7__width=0p18__s=0p75 | PP-OPT94 | p95_mode_mape_guard | 0.270651 | 0.806842 | -0.000744 | -0.001288 | 1.000000 | 0.550000 | -0.001405 |
| ppopt94_p95_guard__target=pp82op__score=generic_risk__thr=0p5__width=0p18__s=0p2 | PP-OPT94 | p95_mode_mape_guard | 0.270644 | 0.806842 | -0.000751 | -0.001287 | 1.000000 | 0.550000 | -0.001412 |

## 반복 안정성 검증
| candidate_label | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_vs_pp64_MAPE | fixed_test_delta_vs_pp64_p95_APE | avg_delta_vs_pp64_MAPE | avg_delta_vs_pp64_p95_APE | avg_pp64_MAPE_win_rate | avg_pp64_p95_win_rate | avg_pp64_all3_win_rate | replacement_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pp81_stable_reference | 0.270559 | 0.807490 | -0.000005 | -0.000009 | -0.000004 | -0.000014 | 0.890705 | 0.410256 | 0.062500 | -0.015633 |
| pp95_operational_guarded_tail | 0.270559 | 0.807490 | -0.000005 | -0.000009 | -0.000004 | -0.000014 | 0.890705 | 0.410256 | 0.062500 | -0.015633 |
| pp70_refinement_candidate | 0.270561 | 0.807490 | -0.000003 | -0.000009 | -0.000001 | -0.000001 | 0.786859 | 0.398077 | 0.054167 | -0.011477 |
| pp82_operational_reference | 0.270557 | 0.807450 | -0.000007 | -0.000049 | 0.000018 | 0.000050 | 0.362179 | 0.477244 | 0.037179 | 0.005532 |
| pp82_p95_reference | 0.270651 | 0.806840 | 0.000087 | -0.000659 | 0.000082 | 0.000179 | 0.056090 | 0.603846 | 0.009615 | 0.017948 |
| pp95_p95_guarded_tail | 0.270651 | 0.806840 | 0.000087 | -0.000659 | 0.000083 | 0.000178 | 0.055128 | 0.603846 | 0.009615 | 0.017986 |
| pp64_current_best | 0.270564 | 0.807499 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.020000 |
| incumbent_pp7 | 0.271395 | 0.808130 | 0.000831 | 0.000631 | 0.000748 | 0.001946 | 0.002244 | 0.450641 | 0.000641 | 0.022238 |
| hcoef_stable_source | 0.272989 | 0.806366 | 0.002425 | -0.001133 | 0.002013 | 0.005297 | 0.002244 | 0.403526 | 0.000641 | 0.025195 |

## 신규 후보 시나리오별 안정성
| candidate_label | eval_split | scenario | mean_delta_vs_pp64_MAPE | mean_delta_vs_pp64_p95_APE | pp64_MAPE_win_rate | pp64_p95_win_rate | pp64_all3_win_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pp95_operational_guarded_tail | test | artist_group_holdout | -0.000005 | -0.000002 | 0.996154 | 0.319231 | 0.119231 |
| pp95_operational_guarded_tail | test | confidence_stratified_rows | -0.000005 | -0.000001 | 0.996154 | 0.434615 | 0.100000 |
| pp95_operational_guarded_tail | test | full_split | -0.000005 | -0.000009 | 1.000000 | 1.000000 | 0.000000 |
| pp95_operational_guarded_tail | test | price_band_stratified_rows | -0.000005 | -0.000003 | 0.996154 | 0.376923 | 0.115385 |
| pp95_operational_guarded_tail | test | risk_focus_bootstrap | -0.000008 | -0.000184 | 0.880769 | 0.338462 | 0.007692 |
| pp95_operational_guarded_tail | test | row_bootstrap | -0.000005 | -0.000014 | 0.953846 | 0.330769 | 0.065385 |
| pp95_operational_guarded_tail | validation_oof | artist_group_holdout | -0.000002 | 0.000002 | 0.803846 | 0.280769 | 0.092308 |
| pp95_operational_guarded_tail | validation_oof | confidence_stratified_rows | -0.000002 | 0.000003 | 0.911538 | 0.288462 | 0.115385 |
| pp95_operational_guarded_tail | validation_oof | full_split | -0.000002 | -0.000025 | 1.000000 | 1.000000 | 0.000000 |
| pp95_operational_guarded_tail | validation_oof | price_band_stratified_rows | -0.000002 | 0.000000 | 0.880769 | 0.319231 | 0.076923 |
| pp95_operational_guarded_tail | validation_oof | risk_focus_bootstrap | -0.000001 | 0.000048 | 0.569231 | 0.000000 | 0.000000 |
| pp95_operational_guarded_tail | validation_oof | row_bootstrap | -0.000002 | 0.000012 | 0.700000 | 0.234615 | 0.057692 |
| pp95_p95_guarded_tail | test | artist_group_holdout | 0.000090 | 0.000271 | 0.007692 | 0.630769 | 0.003846 |
| pp95_p95_guarded_tail | test | confidence_stratified_rows | 0.000086 | 0.000183 | 0.011538 | 0.607692 | 0.000000 |
| pp95_p95_guarded_tail | test | full_split | 0.000087 | -0.000659 | 0.000000 | 1.000000 | 0.000000 |
| pp95_p95_guarded_tail | test | price_band_stratified_rows | 0.000085 | 0.000278 | 0.019231 | 0.573077 | 0.003846 |
| pp95_p95_guarded_tail | test | risk_focus_bootstrap | 0.000143 | 0.001598 | 0.157692 | 0.353846 | 0.023077 |
| pp95_p95_guarded_tail | test | row_bootstrap | 0.000083 | 0.000441 | 0.092308 | 0.469231 | 0.019231 |
| pp95_p95_guarded_tail | validation_oof | artist_group_holdout | 0.000058 | 0.000076 | 0.065385 | 0.557692 | 0.011538 |
| pp95_p95_guarded_tail | validation_oof | confidence_stratified_rows | 0.000061 | 0.000068 | 0.026923 | 0.611538 | 0.011538 |
| pp95_p95_guarded_tail | validation_oof | full_split | 0.000060 | -0.000025 | 0.000000 | 1.000000 | 0.000000 |
| pp95_p95_guarded_tail | validation_oof | price_band_stratified_rows | 0.000059 | 0.000054 | 0.030769 | 0.626923 | 0.003846 |
| pp95_p95_guarded_tail | validation_oof | risk_focus_bootstrap | 0.000117 | -0.000124 | 0.084615 | 0.326923 | 0.011538 |
| pp95_p95_guarded_tail | validation_oof | row_bootstrap | 0.000061 | -0.000018 | 0.165385 | 0.488462 | 0.026923 |

## 실행 설정
```json
{
  "experiment_id": "PP-OPT89-95",
  "experiment_slug": "PP-OPT89_95_warm_tail_guarded_stability_experiments",
  "created_at": "2026-06-09T14:04:21",
  "seed": 20260609,
  "base_candidate": "hcoef_stable",
  "incumbent_candidate": "incumbent_operational_pp_opt7",
  "previous_challenger": "previous_challenger_pp20",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 1590,
  "prediction_rows": 1790340,
  "selected_references": {
    "pp20": "previous_challenger_pp20",
    "pp30": "reference_pp30_best",
    "pp48": "reference_pp48_score",
    "pp64": "reference_pp64_current_best",
    "pp70": "reference_pp70_refinement",
    "pp82_op": "ppopt82_operational_tail_routing_challenger__source=ppopt80_hard_tail__anchor_pp70__helper_pp20__score_p95_prob__thr_0p62__width_0p24__s_1p0",
    "pp82_p95": "ppopt82_p95_tail_routing_challenger__source=ppopt77_clf_tail__anchor_pp70__helper_pp20__prob_tail85_only__thr_0p26__width_0p18__s_0p64",
    "pp81_best": "ppopt81_tail_ensemble__anchor=pp70__helper=pp48_p95_mix__thr=0p48__width=0p22__s=0p56"
  },
  "stability_labels": {
    "hcoef_stable_source": "hcoef_stable",
    "incumbent_pp7": "incumbent_operational_pp_opt7",
    "pp64_current_best": "reference_pp64_current_best",
    "pp70_refinement_candidate": "reference_pp70_refinement",
    "pp81_stable_reference": "reference_pp81_best",
    "pp82_operational_reference": "reference_pp82_operational",
    "pp82_p95_reference": "reference_pp82_p95",
    "pp95_operational_guarded_tail": "ppopt95_operational_guarded_tail_challenger__source=ppopt93_pp81_tail_boost__target_pp82op__score_risk_prob__thr_0p76__width_0p18__s_0p1",
    "pp95_p95_guarded_tail": "ppopt95_p95_guarded_tail_challenger__source=ppopt94_p95_guard__target_pp82op__score_risk_focus__thr_0p7__width_0p32__s_0p2"
  },
  "selection_decision": {
    "reference_pp64_test_MAPE": 0.27056404191566036,
    "reference_pp64_test_p95_APE": 0.8074988523061098,
    "reference_pp70_test_MAPE": 0.2705609753769763,
    "reference_pp70_test_p95_APE": 0.8074900608978479,
    "operational_source_candidate": "ppopt93_pp81_tail_boost__target=pp82op__score=risk_prob__thr=0p76__width=0p18__s=0p1",
    "operational_source_item_id": "PP-OPT93",
    "operational_source_family": "pp81_stable_tail_boost",
    "operational_test_MAPE": 0.27055890188066634,
    "operational_test_p95_APE": 0.8074900608978479,
    "operational_delta_vs_pp64_MAPE": -5.140034994022269e-06,
    "operational_delta_vs_pp64_p95_APE": -8.791408261932254e-06,
    "p95_source_candidate": "ppopt94_p95_guard__target=pp82op__score=risk_focus__thr=0p7__width=0p32__s=0p2",
    "p95_source_item_id": "PP-OPT94",
    "p95_source_family": "p95_mode_mape_guard",
    "p95_test_MAPE": 0.27065114574415167,
    "p95_test_p95_APE": 0.8068399400330787,
    "p95_delta_vs_pp64_MAPE": 8.710382849130838e-05,
    "p95_delta_vs_pp64_p95_APE": -0.0006589122730311647,
    "selection_reason": "select stable operational candidate first; keep a separate p95-focused candidate if MAPE still beats incumbent",
    "operational_protocol_candidate": "ppopt95_operational_guarded_tail_challenger__source=ppopt93_pp81_tail_boost__target_pp82op__score_risk_prob__thr_0p76__width_0p18__s_0p1",
    "p95_protocol_candidate": "ppopt95_p95_guarded_tail_challenger__source=ppopt94_p95_guard__target_pp82op__score_risk_focus__thr_0p7__width_0p32__s_0p2"
  },
  "stability_decision": {
    "operational_verdict": "PP95 운영형도 운영 교체는 보류",
    "p95_verdict": "PP95 p95형은 tail 안정성 우선 옵션으로 유지",
    "pp95_operational_fixed_test_MAPE": 0.27055890188066634,
    "pp95_operational_fixed_test_p95_APE": 0.8074900608978479,
    "pp95_operational_delta_vs_pp64_MAPE": -5.140034994022269e-06,
    "pp95_operational_delta_vs_pp64_p95_APE": -8.791408261932254e-06,
    "pp95_operational_avg_pp64_MAPE_win_rate": 0.8907051282051283,
    "pp95_operational_avg_pp64_p95_win_rate": 0.4102564102564103,
    "pp95_operational_avg_pp64_all3_win_rate": 0.0625,
    "pp95_p95_fixed_test_MAPE": 0.27065114574415167,
    "pp95_p95_fixed_test_p95_APE": 0.8068399400330787,
    "pp95_p95_delta_vs_pp64_MAPE": 8.710382849130838e-05,
    "pp95_p95_delta_vs_pp64_p95_APE": -0.0006589122730311647,
    "pp95_p95_avg_pp64_MAPE_win_rate": 0.05512820512820513,
    "pp95_p95_avg_pp64_p95_win_rate": 0.6038461538461538
  },
  "items": [
    {
      "item_id": "PP-OPT89",
      "priority": "1",
      "title": "PP82 risk-focus rollback shrink",
      "description": "risk-focus에서 PP82 fallback을 PP70 쪽으로 되돌려 MAPE 악화를 줄인다."
    },
    {
      "item_id": "PP-OPT90",
      "priority": "2",
      "title": "weaker hard-tail fallback local grid",
      "description": "PP80/PP82와 같은 구조에서 threshold, width, strength를 보수적으로 재탐색한다."
    },
    {
      "item_id": "PP-OPT91",
      "priority": "3",
      "title": "soft helper tail fallback",
      "description": "PP20 단독 대신 PP20/PP30/PP48 혼합 helper로 fallback 방향을 부드럽게 만든다."
    },
    {
      "item_id": "PP-OPT92",
      "priority": "4",
      "title": "quantile-direction guarded fallback",
      "description": "잔차 quantile 방향과 fallback 이동 방향이 맞지 않으면 fallback 강도를 줄인다."
    },
    {
      "item_id": "PP-OPT93",
      "priority": "5",
      "title": "PP81 stable route plus PP82 tail boost",
      "description": "반복 안정성이 좋았던 PP81 계열을 기준으로 tail에서만 PP82를 일부 반영한다."
    },
    {
      "item_id": "PP-OPT94",
      "priority": "6",
      "title": "p95 mode guard",
      "description": "PP82 p95형을 PP70/PP82 운영형 쪽으로 되돌려 MAPE 손실을 줄인다."
    },
    {
      "item_id": "PP-OPT95",
      "priority": "7",
      "title": "final guarded tail-routing challenger",
      "description": "운영형과 p95 목적형 후보를 분리해 최종 선택한다."
    }
  ],
  "sources": {
    "pp76_config": "experiments/track6/PP-OPT76_82_warm_tail_routing_experiments/artifacts/run_config.json",
    "pp76_predictions": "experiments/track6/PP-OPT76_82_warm_tail_routing_experiments/outputs/candidate_predictions.csv",
    "pp76_tail_probability": "experiments/track6/PP-OPT76_82_warm_tail_routing_experiments/artifacts/tail_classifier_detail.csv",
    "pp76_tail_score": "experiments/track6/PP-OPT76_82_warm_tail_routing_experiments/artifacts/tail_risk_scores.csv",
    "pp47_quantile": "experiments/track6/PP-OPT47_52_warm_residual_finetune_experiments/artifacts/quantile_residual_predictions.csv",
    "pp76_helper": "scripts/track6/run_pp_opt76_82_warm_tail_routing_experiments.py",
    "pp71_validation_helper": "scripts/track6/run_pp_opt71_75_warm_pp70_stability_validation.py"
  }
}
```