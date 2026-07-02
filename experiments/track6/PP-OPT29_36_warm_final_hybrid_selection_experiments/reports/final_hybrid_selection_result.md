# PP-OPT29~36 Warm 최종 하이브리드 선택 실험 결과

- 작성일: 2026-06-09 11:48
- 데이터 기준: 제출용 제외, Warm validation OOF 519건 + fixed test 607건
- 기준 후보: PP-OPT7 운영 후보
- 전체 후보 수: 483
- 운영 대체 통과 후보 수: 165

## PP-OPT36 최종 선택 후보
- 선택 후보: `ppopt36_final_challenger__source=ppopt31_pp23_tail_guard__thr_0p3__s_0p25__cap_0p01`
- 원본 후보: `ppopt31_pp23_tail_guard__thr=0p3__s=0p25__cap=0p01`
- 원본 실험: `PP-OPT31` / `pp23_emergency_tail_guard`
| eval_split | n | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | delta_vs_incumbent_MdAPE | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | 607 | 0.137878 | 0.270748 | 0.807524 | 0.398008 | 0.784185 | 0.883031 | 0.000986 | -0.000647 | -0.000606 |
| validation_oof | 519 | 0.122430 | 0.206414 | 0.638550 | 0.323788 | 0.782274 | 0.911368 | -0.003493 | -0.000609 | 0.001955 |

## 이전 challenger PP-OPT20
| eval_split | n | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | delta_vs_incumbent_MdAPE | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | 607 | 0.136835 | 0.271182 | 0.806472 | 0.398134 | 0.780890 | 0.883031 | -0.000058 | -0.000213 | -0.001658 |
| validation_oof | 519 | 0.125408 | 0.206777 | 0.638367 | 0.324048 | 0.782274 | 0.911368 | -0.000515 | -0.000246 | 0.001773 |

## 현재 운영 후보 PP-OPT7
| eval_split | n | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| test | 607 | 0.136893 | 0.271395 | 0.808130 | 0.398341 | 0.779242 | 0.883031 |
| validation_oof | 519 | 0.125923 | 0.207023 | 0.636595 | 0.324133 | 0.782274 | 0.911368 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | stable_validation_pass_vs_incumbent | operational_pass_vs_incumbent | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | PP20 vs PP23 row별 선택 classifier | 18 | 0.270872 | 0.806932 | -0.000523 | -0.001198 | 1.000000 | 0.550000 | True | True | pp20_pp23_row_selector | ppopt30_row_selector__model=select_pp23_lgbm__thr=0p18__sharp=1p0 |
| 3 | PP23 + emergency tail guard | 36 | 0.270801 | 0.807375 | -0.000594 | -0.000755 | 1.000000 | 0.529167 | True | True | pp23_emergency_tail_guard | ppopt31_pp23_tail_guard__thr=0p12__s=0p25__cap=0p01 |
| 1 | PP20 + PP23 위험도별 혼합 | 9 | 0.270955 | 0.806992 | -0.000440 | -0.001138 | 1.000000 | 0.558333 | True | True | pp20_pp23_risk_weighted_blend | ppopt29_risk_blend__power=1p0__floor=0p2 |
| 8 | final challenger freeze protocol | 1 | 0.270748 | 0.807524 | -0.000647 | -0.000606 | 1.000000 | 0.533333 | True | True | final_challenger_freeze_protocol | ppopt36_final_challenger__source=ppopt31_pp23_tail_guard__thr_0p3__s_0p25__cap_0p01 |
| 5 | constrained candidate stacking | 348 | 0.270943 | 0.807067 | -0.000452 | -0.001063 | 1.000000 | 0.566667 | True | True | constrained_candidate_stacking | ppopt33_stack__inc=0p0__p20=0p5__p23=0p5__p15=0p0__p27=0p0 |
| 4 | monotonic gate probability calibration | 18 | 0.270826 | 0.807654 | -0.000569 | -0.000476 | 1.000000 | 0.525000 | True | True | monotonic_gate_probability_calibration | ppopt32_monotonic_calibration__prob=pp23_safe_lgbm__thr=0p14__floor=0p4 |
| 6 | p95-safe uplift label 재정의 | 36 | 0.271086 | 0.808003 | -0.000309 | -0.000127 | 1.000000 | 0.475000 | True | True | p95_safe_uplift_gate | ppopt34_p95safe_uplift__src=pp23__prob=pp23_p95safe_lgbm__thr=0p18__s=0p85 |
| 7 | segment별 PP20/PP23/PP27 라우팅 | 14 | 0.270827 | 0.807277 | -0.000568 | -0.000853 | 1.000000 | 0.516667 | True | False | pp20_pp23_pp27_segment_router | ppopt35_segment_router__group=spread_price__obj=guarded |

## 운영 대체 통과 후보 상위
| item_id | candidate | family | test_MdAPE | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MdAPE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | incumbent_all3_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-OPT30 | ppopt30_row_selector__model=select_pp23_lgbm__thr=0p18__sharp=1p0 | pp20_pp23_row_selector | 0.137546 | 0.270872 | 0.806932 | 0.000654 | -0.000523 | -0.001198 | 1.000000 | 0.550000 | 0.495833 | -0.001396 |
| PP-OPT30 | ppopt30_row_selector__model=select_pp23_lgbm__thr=0p18__sharp=1p35 | pp20_pp23_row_selector | 0.137457 | 0.270892 | 0.806805 | 0.000564 | -0.000503 | -0.001325 | 1.000000 | 0.545833 | 0.491667 | -0.001393 |
| PP-OPT30 | ppopt30_row_selector__model=select_pp23_lgbm__thr=0p18__sharp=0p75 | pp20_pp23_row_selector | 0.137618 | 0.270854 | 0.807053 | 0.000725 | -0.000541 | -0.001077 | 1.000000 | 0.545833 | 0.495833 | -0.001392 |
| PP-OPT30 | ppopt30_row_selector__model=select_pp23_lgbm__thr=0p28__sharp=0p75 | pp20_pp23_row_selector | 0.137469 | 0.270901 | 0.806850 | 0.000577 | -0.000494 | -0.001280 | 1.000000 | 0.550000 | 0.491667 | -0.001383 |
| PP-OPT30 | ppopt30_row_selector__model=select_pp23_lgbm__thr=0p28__sharp=1p35 | pp20_pp23_row_selector | 0.137261 | 0.270943 | 0.806630 | 0.000368 | -0.000452 | -0.001500 | 1.000000 | 0.558333 | 0.487500 | -0.001383 |
| PP-OPT30 | ppopt30_row_selector__model=select_pp23_lgbm__thr=0p28__sharp=1p0 | pp20_pp23_row_selector | 0.137372 | 0.270921 | 0.806733 | 0.000480 | -0.000474 | -0.001397 | 1.000000 | 0.558333 | 0.487500 | -0.001378 |
| PP-OPT30 | ppopt30_row_selector__model=select_pp23_lgbm__thr=0p38__sharp=0p75 | pp20_pp23_row_selector | 0.137308 | 0.270955 | 0.806590 | 0.000415 | -0.000440 | -0.001540 | 1.000000 | 0.541667 | 0.475000 | -0.001336 |
| PP-OPT30 | ppopt30_row_selector__model=select_pp23_lgbm__thr=0p38__sharp=1p0 | pp20_pp23_row_selector | 0.137198 | 0.270978 | 0.806535 | 0.000306 | -0.000417 | -0.001595 | 1.000000 | 0.545833 | 0.470833 | -0.001329 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p12__s=0p25__cap=0p01 | pp23_emergency_tail_guard | 0.137878 | 0.270801 | 0.807375 | 0.000986 | -0.000594 | -0.000755 | 1.000000 | 0.529167 | 0.491667 | -0.001319 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p12__s=0p25__cap=0p014 | pp23_emergency_tail_guard | 0.137878 | 0.270801 | 0.807375 | 0.000986 | -0.000594 | -0.000755 | 1.000000 | 0.529167 | 0.491667 | -0.001319 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p12__s=0p25__cap=0p018 | pp23_emergency_tail_guard | 0.137878 | 0.270801 | 0.807375 | 0.000986 | -0.000594 | -0.000755 | 1.000000 | 0.529167 | 0.491667 | -0.001319 |
| PP-OPT29 | ppopt29_risk_blend__power=1p0__floor=0p2 | pp20_pp23_risk_weighted_blend | 0.137391 | 0.270955 | 0.806992 | 0.000498 | -0.000440 | -0.001138 | 1.000000 | 0.558333 | 0.487500 | -0.001314 |
| PP-OPT29 | ppopt29_risk_blend__power=0p75__floor=0p1 | pp20_pp23_risk_weighted_blend | 0.137361 | 0.270968 | 0.806953 | 0.000469 | -0.000427 | -0.001177 | 1.000000 | 0.558333 | 0.487500 | -0.001313 |
| PP-OPT29 | ppopt29_risk_blend__power=1p35__floor=0p3 | pp20_pp23_risk_weighted_blend | 0.137399 | 0.270949 | 0.807017 | 0.000507 | -0.000446 | -0.001113 | 1.000000 | 0.558333 | 0.487500 | -0.001312 |
| PP-OPT30 | ppopt30_row_selector__model=select_pp23_lgbm__thr=0p38__sharp=1p35 | pp20_pp23_row_selector | 0.137086 | 0.271004 | 0.806502 | 0.000193 | -0.000391 | -0.001627 | 1.000000 | 0.550000 | 0.458333 | -0.001305 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p3__s=0p25__cap=0p01 | pp23_emergency_tail_guard | 0.137878 | 0.270748 | 0.807524 | 0.000986 | -0.000647 | -0.000606 | 1.000000 | 0.533333 | 0.466667 | -0.001302 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p3__s=0p25__cap=0p014 | pp23_emergency_tail_guard | 0.137878 | 0.270748 | 0.807524 | 0.000986 | -0.000647 | -0.000606 | 1.000000 | 0.533333 | 0.466667 | -0.001302 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p3__s=0p25__cap=0p018 | pp23_emergency_tail_guard | 0.137878 | 0.270748 | 0.807524 | 0.000986 | -0.000647 | -0.000606 | 1.000000 | 0.533333 | 0.466667 | -0.001302 |
| PP-OPT36 | ppopt36_final_challenger__source=ppopt31_pp23_tail_guard__thr_0p3__s_0p25__cap_0p01 | final_challenger_freeze_protocol | 0.137878 | 0.270748 | 0.807524 | 0.000986 | -0.000647 | -0.000606 | 1.000000 | 0.533333 | 0.466667 | -0.001302 |
| PP-OPT29 | ppopt29_risk_blend__power=1p35__floor=0p1 | pp20_pp23_risk_weighted_blend | 0.137560 | 0.270883 | 0.807172 | 0.000668 | -0.000512 | -0.000958 | 1.000000 | 0.533333 | 0.475000 | -0.001301 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p3__s=0p4__cap=0p01 | pp23_emergency_tail_guard | 0.137878 | 0.270772 | 0.807442 | 0.000986 | -0.000623 | -0.000687 | 1.000000 | 0.533333 | 0.470833 | -0.001301 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p3__s=0p4__cap=0p014 | pp23_emergency_tail_guard | 0.137878 | 0.270772 | 0.807442 | 0.000986 | -0.000623 | -0.000687 | 1.000000 | 0.533333 | 0.470833 | -0.001301 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p3__s=0p4__cap=0p018 | pp23_emergency_tail_guard | 0.137878 | 0.270772 | 0.807442 | 0.000986 | -0.000623 | -0.000687 | 1.000000 | 0.533333 | 0.470833 | -0.001301 |
| PP-OPT29 | ppopt29_risk_blend__power=0p75__floor=0p2 | pp20_pp23_risk_weighted_blend | 0.137303 | 0.270992 | 0.806899 | 0.000410 | -0.000403 | -0.001231 | 1.000000 | 0.566667 | 0.483333 | -0.001297 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p2__s=0p25__cap=0p01 | pp23_emergency_tail_guard | 0.137878 | 0.270771 | 0.807439 | 0.000986 | -0.000624 | -0.000691 | 1.000000 | 0.533333 | 0.470833 | -0.001296 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p2__s=0p25__cap=0p014 | pp23_emergency_tail_guard | 0.137878 | 0.270771 | 0.807439 | 0.000986 | -0.000624 | -0.000691 | 1.000000 | 0.533333 | 0.470833 | -0.001296 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p2__s=0p25__cap=0p018 | pp23_emergency_tail_guard | 0.137878 | 0.270771 | 0.807439 | 0.000986 | -0.000624 | -0.000691 | 1.000000 | 0.533333 | 0.470833 | -0.001296 |
| PP-OPT33 | ppopt33_stack__inc=0p0__p20=0p5__p23=0p5__p15=0p0__p27=0p0 | constrained_candidate_stacking | 0.137357 | 0.270943 | 0.807067 | 0.000464 | -0.000452 | -0.001063 | 1.000000 | 0.566667 | 0.479167 | -0.001295 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p3__s=0p55__cap=0p01 | pp23_emergency_tail_guard | 0.137878 | 0.270797 | 0.807361 | 0.000986 | -0.000598 | -0.000769 | 1.000000 | 0.533333 | 0.470833 | -0.001291 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p3__s=0p55__cap=0p014 | pp23_emergency_tail_guard | 0.137878 | 0.270797 | 0.807361 | 0.000986 | -0.000598 | -0.000769 | 1.000000 | 0.533333 | 0.470833 | -0.001291 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p3__s=0p55__cap=0p018 | pp23_emergency_tail_guard | 0.137878 | 0.270797 | 0.807361 | 0.000986 | -0.000598 | -0.000769 | 1.000000 | 0.533333 | 0.470833 | -0.001291 |
| PP-OPT29 | ppopt29_risk_blend__power=1p35__floor=0p2 | pp20_pp23_risk_weighted_blend | 0.137480 | 0.270916 | 0.807095 | 0.000587 | -0.000479 | -0.001035 | 1.000000 | 0.537500 | 0.470833 | -0.001286 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p3__s=0p7__cap=0p014 | pp23_emergency_tail_guard | 0.137878 | 0.270821 | 0.807279 | 0.000986 | -0.000574 | -0.000851 | 1.000000 | 0.533333 | 0.470833 | -0.001281 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p3__s=0p7__cap=0p018 | pp23_emergency_tail_guard | 0.137878 | 0.270821 | 0.807279 | 0.000986 | -0.000574 | -0.000851 | 1.000000 | 0.533333 | 0.470833 | -0.001281 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p12__s=0p4__cap=0p01 | pp23_emergency_tail_guard | 0.137878 | 0.270857 | 0.807205 | 0.000986 | -0.000538 | -0.000925 | 1.000000 | 0.525000 | 0.487500 | -0.001281 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p12__s=0p4__cap=0p014 | pp23_emergency_tail_guard | 0.137878 | 0.270857 | 0.807205 | 0.000986 | -0.000538 | -0.000925 | 1.000000 | 0.525000 | 0.487500 | -0.001281 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p12__s=0p4__cap=0p018 | pp23_emergency_tail_guard | 0.137878 | 0.270857 | 0.807205 | 0.000986 | -0.000538 | -0.000925 | 1.000000 | 0.525000 | 0.487500 | -0.001281 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p3__s=0p7__cap=0p01 | pp23_emergency_tail_guard | 0.137878 | 0.270819 | 0.807279 | 0.000986 | -0.000576 | -0.000851 | 1.000000 | 0.533333 | 0.470833 | -0.001279 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p2__s=0p4__cap=0p01 | pp23_emergency_tail_guard | 0.137878 | 0.270809 | 0.807306 | 0.000986 | -0.000586 | -0.000824 | 1.000000 | 0.533333 | 0.470833 | -0.001278 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p2__s=0p4__cap=0p014 | pp23_emergency_tail_guard | 0.137878 | 0.270809 | 0.807306 | 0.000986 | -0.000586 | -0.000824 | 1.000000 | 0.533333 | 0.470833 | -0.001278 |

## MAPE와 p95 동시 개선 후보
| item_id | candidate | family | test_MdAPE | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MdAPE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | incumbent_all3_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-OPT30 | ppopt30_row_selector__model=select_pp23_lgbm__thr=0p18__sharp=1p0 | pp20_pp23_row_selector | 0.137546 | 0.270872 | 0.806932 | 0.000654 | -0.000523 | -0.001198 | 1.000000 | 0.550000 | 0.495833 | -0.001396 |
| PP-OPT30 | ppopt30_row_selector__model=select_pp23_lgbm__thr=0p18__sharp=1p35 | pp20_pp23_row_selector | 0.137457 | 0.270892 | 0.806805 | 0.000564 | -0.000503 | -0.001325 | 1.000000 | 0.545833 | 0.491667 | -0.001393 |
| PP-OPT30 | ppopt30_row_selector__model=select_pp23_lgbm__thr=0p18__sharp=0p75 | pp20_pp23_row_selector | 0.137618 | 0.270854 | 0.807053 | 0.000725 | -0.000541 | -0.001077 | 1.000000 | 0.545833 | 0.495833 | -0.001392 |
| PP-OPT30 | ppopt30_row_selector__model=select_pp23_lgbm__thr=0p28__sharp=0p75 | pp20_pp23_row_selector | 0.137469 | 0.270901 | 0.806850 | 0.000577 | -0.000494 | -0.001280 | 1.000000 | 0.550000 | 0.491667 | -0.001383 |
| PP-OPT30 | ppopt30_row_selector__model=select_pp23_lgbm__thr=0p28__sharp=1p35 | pp20_pp23_row_selector | 0.137261 | 0.270943 | 0.806630 | 0.000368 | -0.000452 | -0.001500 | 1.000000 | 0.558333 | 0.487500 | -0.001383 |
| PP-OPT30 | ppopt30_row_selector__model=select_pp23_lgbm__thr=0p28__sharp=1p0 | pp20_pp23_row_selector | 0.137372 | 0.270921 | 0.806733 | 0.000480 | -0.000474 | -0.001397 | 1.000000 | 0.558333 | 0.487500 | -0.001378 |
| PP-OPT30 | ppopt30_row_selector__model=select_pp23_lgbm__thr=0p38__sharp=0p75 | pp20_pp23_row_selector | 0.137308 | 0.270955 | 0.806590 | 0.000415 | -0.000440 | -0.001540 | 1.000000 | 0.541667 | 0.475000 | -0.001336 |
| PP-OPT30 | ppopt30_row_selector__model=select_pp23_lgbm__thr=0p38__sharp=1p0 | pp20_pp23_row_selector | 0.137198 | 0.270978 | 0.806535 | 0.000306 | -0.000417 | -0.001595 | 1.000000 | 0.545833 | 0.470833 | -0.001329 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p12__s=0p25__cap=0p01 | pp23_emergency_tail_guard | 0.137878 | 0.270801 | 0.807375 | 0.000986 | -0.000594 | -0.000755 | 1.000000 | 0.529167 | 0.491667 | -0.001319 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p12__s=0p25__cap=0p014 | pp23_emergency_tail_guard | 0.137878 | 0.270801 | 0.807375 | 0.000986 | -0.000594 | -0.000755 | 1.000000 | 0.529167 | 0.491667 | -0.001319 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p12__s=0p25__cap=0p018 | pp23_emergency_tail_guard | 0.137878 | 0.270801 | 0.807375 | 0.000986 | -0.000594 | -0.000755 | 1.000000 | 0.529167 | 0.491667 | -0.001319 |
| PP-OPT29 | ppopt29_risk_blend__power=1p0__floor=0p2 | pp20_pp23_risk_weighted_blend | 0.137391 | 0.270955 | 0.806992 | 0.000498 | -0.000440 | -0.001138 | 1.000000 | 0.558333 | 0.487500 | -0.001314 |
| PP-OPT29 | ppopt29_risk_blend__power=0p75__floor=0p1 | pp20_pp23_risk_weighted_blend | 0.137361 | 0.270968 | 0.806953 | 0.000469 | -0.000427 | -0.001177 | 1.000000 | 0.558333 | 0.487500 | -0.001313 |
| PP-OPT29 | ppopt29_risk_blend__power=1p35__floor=0p3 | pp20_pp23_risk_weighted_blend | 0.137399 | 0.270949 | 0.807017 | 0.000507 | -0.000446 | -0.001113 | 1.000000 | 0.558333 | 0.487500 | -0.001312 |
| PP-OPT30 | ppopt30_row_selector__model=select_pp23_lgbm__thr=0p38__sharp=1p35 | pp20_pp23_row_selector | 0.137086 | 0.271004 | 0.806502 | 0.000193 | -0.000391 | -0.001627 | 1.000000 | 0.550000 | 0.458333 | -0.001305 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p3__s=0p25__cap=0p01 | pp23_emergency_tail_guard | 0.137878 | 0.270748 | 0.807524 | 0.000986 | -0.000647 | -0.000606 | 1.000000 | 0.533333 | 0.466667 | -0.001302 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p3__s=0p25__cap=0p014 | pp23_emergency_tail_guard | 0.137878 | 0.270748 | 0.807524 | 0.000986 | -0.000647 | -0.000606 | 1.000000 | 0.533333 | 0.466667 | -0.001302 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p3__s=0p25__cap=0p018 | pp23_emergency_tail_guard | 0.137878 | 0.270748 | 0.807524 | 0.000986 | -0.000647 | -0.000606 | 1.000000 | 0.533333 | 0.466667 | -0.001302 |
| PP-OPT36 | ppopt36_final_challenger__source=ppopt31_pp23_tail_guard__thr_0p3__s_0p25__cap_0p01 | final_challenger_freeze_protocol | 0.137878 | 0.270748 | 0.807524 | 0.000986 | -0.000647 | -0.000606 | 1.000000 | 0.533333 | 0.466667 | -0.001302 |
| PP-OPT29 | ppopt29_risk_blend__power=1p35__floor=0p1 | pp20_pp23_risk_weighted_blend | 0.137560 | 0.270883 | 0.807172 | 0.000668 | -0.000512 | -0.000958 | 1.000000 | 0.533333 | 0.475000 | -0.001301 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p3__s=0p4__cap=0p01 | pp23_emergency_tail_guard | 0.137878 | 0.270772 | 0.807442 | 0.000986 | -0.000623 | -0.000687 | 1.000000 | 0.533333 | 0.470833 | -0.001301 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p3__s=0p4__cap=0p014 | pp23_emergency_tail_guard | 0.137878 | 0.270772 | 0.807442 | 0.000986 | -0.000623 | -0.000687 | 1.000000 | 0.533333 | 0.470833 | -0.001301 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p3__s=0p4__cap=0p018 | pp23_emergency_tail_guard | 0.137878 | 0.270772 | 0.807442 | 0.000986 | -0.000623 | -0.000687 | 1.000000 | 0.533333 | 0.470833 | -0.001301 |
| PP-OPT29 | ppopt29_risk_blend__power=0p75__floor=0p2 | pp20_pp23_risk_weighted_blend | 0.137303 | 0.270992 | 0.806899 | 0.000410 | -0.000403 | -0.001231 | 1.000000 | 0.566667 | 0.483333 | -0.001297 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p2__s=0p25__cap=0p01 | pp23_emergency_tail_guard | 0.137878 | 0.270771 | 0.807439 | 0.000986 | -0.000624 | -0.000691 | 1.000000 | 0.533333 | 0.470833 | -0.001296 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p2__s=0p25__cap=0p014 | pp23_emergency_tail_guard | 0.137878 | 0.270771 | 0.807439 | 0.000986 | -0.000624 | -0.000691 | 1.000000 | 0.533333 | 0.470833 | -0.001296 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p2__s=0p25__cap=0p018 | pp23_emergency_tail_guard | 0.137878 | 0.270771 | 0.807439 | 0.000986 | -0.000624 | -0.000691 | 1.000000 | 0.533333 | 0.470833 | -0.001296 |
| PP-OPT33 | ppopt33_stack__inc=0p0__p20=0p5__p23=0p5__p15=0p0__p27=0p0 | constrained_candidate_stacking | 0.137357 | 0.270943 | 0.807067 | 0.000464 | -0.000452 | -0.001063 | 1.000000 | 0.566667 | 0.479167 | -0.001295 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p3__s=0p55__cap=0p01 | pp23_emergency_tail_guard | 0.137878 | 0.270797 | 0.807361 | 0.000986 | -0.000598 | -0.000769 | 1.000000 | 0.533333 | 0.470833 | -0.001291 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p3__s=0p55__cap=0p014 | pp23_emergency_tail_guard | 0.137878 | 0.270797 | 0.807361 | 0.000986 | -0.000598 | -0.000769 | 1.000000 | 0.533333 | 0.470833 | -0.001291 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p3__s=0p55__cap=0p018 | pp23_emergency_tail_guard | 0.137878 | 0.270797 | 0.807361 | 0.000986 | -0.000598 | -0.000769 | 1.000000 | 0.533333 | 0.470833 | -0.001291 |
| PP-OPT29 | ppopt29_risk_blend__power=1p35__floor=0p2 | pp20_pp23_risk_weighted_blend | 0.137480 | 0.270916 | 0.807095 | 0.000587 | -0.000479 | -0.001035 | 1.000000 | 0.537500 | 0.470833 | -0.001286 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p3__s=0p7__cap=0p014 | pp23_emergency_tail_guard | 0.137878 | 0.270821 | 0.807279 | 0.000986 | -0.000574 | -0.000851 | 1.000000 | 0.533333 | 0.470833 | -0.001281 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p3__s=0p7__cap=0p018 | pp23_emergency_tail_guard | 0.137878 | 0.270821 | 0.807279 | 0.000986 | -0.000574 | -0.000851 | 1.000000 | 0.533333 | 0.470833 | -0.001281 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p12__s=0p4__cap=0p01 | pp23_emergency_tail_guard | 0.137878 | 0.270857 | 0.807205 | 0.000986 | -0.000538 | -0.000925 | 1.000000 | 0.525000 | 0.487500 | -0.001281 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p12__s=0p4__cap=0p014 | pp23_emergency_tail_guard | 0.137878 | 0.270857 | 0.807205 | 0.000986 | -0.000538 | -0.000925 | 1.000000 | 0.525000 | 0.487500 | -0.001281 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p12__s=0p4__cap=0p018 | pp23_emergency_tail_guard | 0.137878 | 0.270857 | 0.807205 | 0.000986 | -0.000538 | -0.000925 | 1.000000 | 0.525000 | 0.487500 | -0.001281 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p3__s=0p7__cap=0p01 | pp23_emergency_tail_guard | 0.137878 | 0.270819 | 0.807279 | 0.000986 | -0.000576 | -0.000851 | 1.000000 | 0.533333 | 0.470833 | -0.001279 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p2__s=0p4__cap=0p01 | pp23_emergency_tail_guard | 0.137878 | 0.270809 | 0.807306 | 0.000986 | -0.000586 | -0.000824 | 1.000000 | 0.533333 | 0.470833 | -0.001278 |
| PP-OPT31 | ppopt31_pp23_tail_guard__thr=0p2__s=0p4__cap=0p014 | pp23_emergency_tail_guard | 0.137878 | 0.270809 | 0.807306 | 0.000986 | -0.000586 | -0.000824 | 1.000000 | 0.533333 | 0.470833 | -0.001278 |

## 해석
이번 실험은 PP20 안정성, PP23 성능, PP27 tail 방어를 조합하는 최종 선택 실험이다. PP20보다 MAPE가 낮아지면서 p95를 크게 되돌리지 않는 후보를 우선한다.
만약 PP36 선택 후보가 PP20 대비 MAPE를 낮추되 p95 손실이 제한적이면 운영 challenger를 PP36으로 갱신할 수 있다.

## 실행 설정
```json
{
  "experiment_id": "PP-OPT29-36",
  "experiment_slug": "PP-OPT29_36_warm_final_hybrid_selection_experiments",
  "created_at": "2026-06-09T11:48:35",
  "seed": 20260609,
  "base_candidate": "hcoef_stable",
  "incumbent_candidate": "incumbent_operational_pp_opt7",
  "previous_challenger": "previous_challenger_pp20",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 484,
  "prediction_rows": 544984,
  "items": [
    {
      "item_id": "PP-OPT29",
      "priority": "1",
      "title": "PP20 + PP23 위험도별 혼합",
      "description": "위험 구간은 PP20, 안정 구간은 PP23 비중을 높인다."
    },
    {
      "item_id": "PP-OPT30",
      "priority": "2",
      "title": "PP20 vs PP23 row별 선택 classifier",
      "description": "각 row에서 PP20과 PP23 중 더 좋은 후보를 선택하도록 학습한다."
    },
    {
      "item_id": "PP-OPT31",
      "priority": "3",
      "title": "PP23 + emergency tail guard",
      "description": "PP23에 PP27 tail 방어 신호를 위험 구간에서만 약하게 더한다."
    },
    {
      "item_id": "PP-OPT32",
      "priority": "4",
      "title": "monotonic gate probability calibration",
      "description": "PP23 monotonic gate를 더 보수적으로 보정해 과보정을 줄인다."
    },
    {
      "item_id": "PP-OPT33",
      "priority": "5",
      "title": "constrained candidate stacking",
      "description": "PP7/20/23/15/27 후보를 제한 조건 안에서 가중 결합한다."
    },
    {
      "item_id": "PP-OPT34",
      "priority": "6",
      "title": "p95-safe uplift label 재정의",
      "description": "p95 악화 없이 개선되는 row만 보정하도록 라벨을 재정의한다."
    },
    {
      "item_id": "PP-OPT35",
      "priority": "7",
      "title": "segment별 PP20/PP23/PP27 라우팅",
      "description": "가격대/신뢰도/유사작품수 구간별로 최적 후보를 고른다."
    },
    {
      "item_id": "PP-OPT36",
      "priority": "8",
      "title": "final challenger freeze protocol",
      "description": "PP20 대비 추가 개선까지 고려해 최종 challenger를 선택한다."
    }
  ],
  "selected_components": {
    "pp20": "ppopt20_protocol_selected__source=ppopt19_segment_tuning__profile_low_support_tail__artist_cat_artist_mean__as_0p25__ts_0p55",
    "pp23": "ppopt23_monotonic_gate__src=pp15_best_mape__thr=0p16__s=0p85",
    "pp23_mape": "ppopt23_monotonic_gate__src=opt8_cat_price_band__thr=0p16__s=0p85",
    "pp27_tail": "ppopt27_micro_residual__center=pp19_best_score__s=0p5__cap=0p01",
    "pp15_mape": "ppopt15_absorb_pp12__base=pp9_best_mape__p12s=0p34__p9s=1p05__cap=0p026",
    "pp21_mape": "ppopt21_uplift_gate__src=opt8_artist_mape__model=lgbm__thr=0p18__s=0p95",
    "pp19_stable": "ppopt19_segment_tuning__profile=price_tail_high__artist=artist__as=0p35__ts=0p75",
    "pp14_stable": "ppopt14_gate_grid__artist=artist_stable__sthr=0p12__tthr=0p25__as=0p2__ts=0p75__cap=0p024",
    "pp24_conformal": "ppopt24_conformal_gate__src=pp19_best_score__s=0p95__cap=0p018"
  },
  "thresholds": {
    "p85": 0.38339160296436176,
    "p90": 0.4636774710873784,
    "p95": 0.6365947866362616
  },
  "selection_decision": {
    "selected_source_candidate": "ppopt31_pp23_tail_guard__thr=0p3__s=0p25__cap=0p01",
    "protocol_candidate": "ppopt36_final_challenger__source=ppopt31_pp23_tail_guard__thr_0p3__s_0p25__cap_0p01",
    "selected_source_item_id": "PP-OPT31",
    "selected_source_family": "pp23_emergency_tail_guard",
    "selection_reason": "operational pass first, then PP20 MAPE improvement with p95 give-back <= 0.0015, then recommendation score",
    "test_MdAPE": 0.13787846966744394,
    "test_MAPE": 0.27074787203179984,
    "test_p95_APE": 0.8075240687683035,
    "test_delta_vs_incumbent_MdAPE": 0.000985903768827734,
    "test_delta_vs_incumbent_MAPE": -0.0006470159802666187,
    "test_delta_vs_incumbent_p95_APE": -0.0006059139451651818,
    "recommendation_score_vs_incumbent": -0.0013021416408206578
  },
  "sources": {
    "pp_opt14_predictions": "experiments/track6/PP-OPT14_20_warm_gate_refinement_experiments/outputs/candidate_predictions.csv",
    "pp_opt14_aggregate": "experiments/track6/PP-OPT14_20_warm_gate_refinement_experiments/outputs/aggregate_candidate_stability.csv",
    "pp_opt21_predictions": "experiments/track6/PP-OPT21_28_warm_model_characteristic_experiments/outputs/candidate_predictions.csv",
    "pp_opt21_aggregate": "experiments/track6/PP-OPT21_28_warm_model_characteristic_experiments/outputs/aggregate_candidate_stability.csv",
    "pp_opt8_helper": "scripts/track6/run_pp_opt8_warm_extended_correction_experiments.py",
    "pp_opt9_helper": "scripts/track6/run_pp_opt9_13_warm_followup_improvement_experiments.py",
    "pp_opt14_helper": "scripts/track6/run_pp_opt14_20_warm_gate_refinement_experiments.py",
    "pp_opt21_helper": "scripts/track6/run_pp_opt21_28_warm_model_characteristic_experiments.py"
  }
}
```