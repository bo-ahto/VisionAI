# PP-OPT21~28 Warm 모델 특성 기반 추가 실험 결과

- 작성일: 2026-06-09 11:33
- 데이터 기준: 제출용 제외, Warm validation OOF 519건 + fixed test 607건
- 기준 후보: PP-OPT7 운영 후보
- 전체 후보 수: 258
- 운영 대체 통과 후보 수: 111

## 최우선 후보
- 후보: `ppopt23_monotonic_gate__src=pp15_best_mape__thr=0p16__s=0p85`
- 실험: `PP-OPT23` / `monotonic_constrained_gate`
| eval_split | n | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | delta_vs_incumbent_MdAPE | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | 607 | 0.137878 | 0.270707 | 0.807660 | 0.398002 | 0.784185 | 0.883031 | 0.000986 | -0.000688 | -0.000470 |
| validation_oof | 519 | 0.122430 | 0.206397 | 0.638550 | 0.323781 | 0.782274 | 0.911368 | -0.003493 | -0.000626 | 0.001955 |

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
| 3 | monotonic constrained gate | 27 | 0.270707 | 0.807660 | -0.000688 | -0.000470 | 1.000000 | 0.504167 | True | True | monotonic_constrained_gate | ppopt23_monotonic_gate__src=pp15_best_mape__thr=0p16__s=0p85 |
| 4 | conformal risk gate | 18 | 0.271222 | 0.807076 | -0.000173 | -0.001054 | 1.000000 | 0.545833 | True | True | conformal_risk_gate | ppopt24_conformal_gate__src=pp19_best_score__s=0p95__cap=0p018 |
| 1 | uplift model 기반 보정 선택 | 90 | 0.271098 | 0.807821 | -0.000297 | -0.000309 | 1.000000 | 0.483333 | True | True | uplift_correction_selector | ppopt21_uplift_gate__src=pp15_best_mape__model=lgbm__thr=0p18__s=0p55 |
| 5 | CatBoost categorical specialist | 18 | 0.271208 | 0.807810 | -0.000187 | -0.000320 | 1.000000 | 0.500000 | True | True | catboost_categorical_specialist | ppopt25_catboost_uplift__thr=0p2__s=0p95 |
| 6 | LightGBM risk classifier specialist | 54 | 0.271276 | 0.806506 | -0.000119 | -0.001624 | 0.920833 | 0.820833 | True | True | lightgbm_risk_classifier_specialist | ppopt26_lgbm_risk__label=p90__src=xgb_tail__thr=0p22__s=0p65 |
| 8 | segment별 model-of-models router | 12 | 0.270844 | 0.806684 | -0.000551 | -0.001446 | 1.000000 | 0.500000 | False | False | segment_model_router | ppopt28_segment_router__group=confidence__obj=mape |
| 7 | two-stage micro residual | 27 | 0.271573 | 0.805943 | 0.000178 | -0.002187 | 0.504167 | 0.262500 | False | False | two_stage_micro_residual | ppopt27_micro_residual__center=pp19_best_score__s=0p2__cap=0p004 |
| 2 | quantile residual shrinkage | 9 | 0.270933 | 0.809136 | -0.000462 | 0.001006 | 0.750000 | 0.325000 | False | False | quantile_residual_shrinkage | ppopt22_quantile_residual__s=0p25__cap=0p01 |

## 운영 대체 통과 후보 상위
| item_id | candidate | family | test_MdAPE | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MdAPE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | incumbent_all3_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-OPT23 | ppopt23_monotonic_gate__src=pp15_best_mape__thr=0p16__s=0p85 | monotonic_constrained_gate | 0.137878 | 0.270707 | 0.807660 | 0.000986 | -0.000688 | -0.000470 | 1.000000 | 0.504167 | 0.400000 | -0.001185 |
| PP-OPT23 | ppopt23_monotonic_gate__src=pp15_best_mape__thr=0p26__s=0p85 | monotonic_constrained_gate | 0.137574 | 0.270842 | 0.807781 | 0.000681 | -0.000553 | -0.000349 | 1.000000 | 0.504167 | 0.395833 | -0.001132 |
| PP-OPT23 | ppopt23_monotonic_gate__src=pp15_best_mape__thr=0p16__s=0p65 | monotonic_constrained_gate | 0.137606 | 0.270866 | 0.807771 | 0.000714 | -0.000529 | -0.000359 | 1.000000 | 0.504167 | 0.391667 | -0.001096 |
| PP-OPT23 | ppopt23_monotonic_gate__src=pp15_best_mape__thr=0p26__s=0p65 | monotonic_constrained_gate | 0.137373 | 0.270971 | 0.807863 | 0.000481 | -0.000424 | -0.000267 | 1.000000 | 0.504167 | 0.387500 | -0.001053 |
| PP-OPT23 | ppopt23_monotonic_gate__src=pp15_best_mape__thr=0p36__s=0p85 | monotonic_constrained_gate | 0.137269 | 0.270978 | 0.807904 | 0.000377 | -0.000417 | -0.000226 | 1.000000 | 0.637500 | 0.383333 | -0.001049 |
| PP-OPT23 | ppopt23_monotonic_gate__src=pp15_best_mape__thr=0p16__s=0p45 | monotonic_constrained_gate | 0.137334 | 0.271027 | 0.807881 | 0.000442 | -0.000368 | -0.000249 | 1.000000 | 0.504167 | 0.383333 | -0.001006 |
| PP-OPT23 | ppopt23_monotonic_gate__src=pp15_best_mape__thr=0p36__s=0p65 | monotonic_constrained_gate | 0.137140 | 0.271074 | 0.807957 | 0.000248 | -0.000321 | -0.000173 | 1.000000 | 0.637500 | 0.366667 | -0.000967 |
| PP-OPT24 | ppopt24_conformal_gate__src=pp19_best_score__s=0p95__cap=0p018 | conformal_risk_gate | 0.136601 | 0.271222 | 0.807076 | -0.000291 | -0.000173 | -0.001054 | 1.000000 | 0.545833 | 0.370833 | -0.000935 |
| PP-OPT24 | ppopt24_conformal_gate__src=pp19_best_score__s=0p95__cap=0p022 | conformal_risk_gate | 0.136601 | 0.271222 | 0.807076 | -0.000291 | -0.000173 | -0.001054 | 1.000000 | 0.545833 | 0.370833 | -0.000935 |
| PP-OPT23 | ppopt23_monotonic_gate__src=pp15_best_mape__thr=0p26__s=0p45 | monotonic_constrained_gate | 0.137173 | 0.271099 | 0.807945 | 0.000280 | -0.000295 | -0.000185 | 1.000000 | 0.504167 | 0.358333 | -0.000930 |
| PP-OPT21 | ppopt21_uplift_gate__src=pp15_best_mape__model=lgbm__thr=0p18__s=0p55 | uplift_correction_selector | 0.137403 | 0.271098 | 0.807821 | 0.000511 | -0.000297 | -0.000309 | 1.000000 | 0.483333 | 0.366667 | -0.000913 |
| PP-OPT21 | ppopt21_uplift_gate__src=pp15_best_mape__model=lgbm__thr=0p28__s=0p95 | uplift_correction_selector | 0.137638 | 0.270984 | 0.807704 | 0.000745 | -0.000411 | -0.000425 | 1.000000 | 0.475000 | 0.350000 | -0.000910 |
| PREV | previous_challenger_pp20 | previous_challenger | 0.136835 | 0.271182 | 0.806472 | -0.000058 | -0.000213 | -0.001658 | 1.000000 | 0.554167 | 0.316667 | -0.000883 |
| PP-OPT24 | ppopt24_conformal_gate__src=pp19_best_score__s=0p75__cap=0p018 | conformal_risk_gate | 0.136627 | 0.271257 | 0.807299 | -0.000266 | -0.000138 | -0.000831 | 1.000000 | 0.545833 | 0.362500 | -0.000878 |
| PP-OPT24 | ppopt24_conformal_gate__src=pp19_best_score__s=0p75__cap=0p022 | conformal_risk_gate | 0.136627 | 0.271257 | 0.807299 | -0.000266 | -0.000138 | -0.000831 | 1.000000 | 0.545833 | 0.362500 | -0.000878 |
| PP-OPT21 | ppopt21_uplift_gate__src=pp15_best_mape__model=lgbm__thr=0p28__s=0p75 | uplift_correction_selector | 0.137445 | 0.271069 | 0.807794 | 0.000552 | -0.000325 | -0.000336 | 1.000000 | 0.475000 | 0.345833 | -0.000874 |
| PP-OPT21 | ppopt21_uplift_gate__src=pp15_best_mape__model=lgbm__thr=0p38__s=0p95 | uplift_correction_selector | 0.137377 | 0.271086 | 0.807813 | 0.000484 | -0.000308 | -0.000317 | 1.000000 | 0.508333 | 0.320833 | -0.000814 |
| PP-OPT24 | ppopt24_conformal_gate__src=pp19_best_score__s=0p55__cap=0p018 | conformal_risk_gate | 0.136652 | 0.271293 | 0.807521 | -0.000241 | -0.000101 | -0.000609 | 1.000000 | 0.545833 | 0.350000 | -0.000812 |
| PP-OPT24 | ppopt24_conformal_gate__src=pp19_best_score__s=0p55__cap=0p022 | conformal_risk_gate | 0.136652 | 0.271293 | 0.807521 | -0.000241 | -0.000101 | -0.000609 | 1.000000 | 0.545833 | 0.350000 | -0.000812 |
| PP-OPT23 | ppopt23_monotonic_gate__src=pp15_best_mape__thr=0p36__s=0p45 | monotonic_constrained_gate | 0.137012 | 0.271171 | 0.808011 | 0.000119 | -0.000224 | -0.000119 | 1.000000 | 0.633333 | 0.304167 | -0.000786 |
| PP-OPT24 | ppopt24_conformal_gate__src=pp20_protocol__s=0p95__cap=0p018 | conformal_risk_gate | 0.136790 | 0.271278 | 0.807157 | -0.000102 | -0.000117 | -0.000973 | 1.000000 | 0.550000 | 0.316667 | -0.000773 |
| PP-OPT24 | ppopt24_conformal_gate__src=pp20_protocol__s=0p95__cap=0p022 | conformal_risk_gate | 0.136790 | 0.271278 | 0.807157 | -0.000102 | -0.000117 | -0.000973 | 1.000000 | 0.550000 | 0.316667 | -0.000773 |
| PP-OPT21 | ppopt21_uplift_gate__src=pp15_best_mape__model=catboost__thr=0p18__s=0p95 | uplift_correction_selector | 0.137278 | 0.271235 | 0.807871 | 0.000385 | -0.000160 | -0.000259 | 1.000000 | 0.491667 | 0.337500 | -0.000771 |
| PP-OPT25 | ppopt25_catboost_uplift__thr=0p2__s=0p95 | catboost_categorical_specialist | 0.137379 | 0.271208 | 0.807810 | 0.000487 | -0.000187 | -0.000320 | 1.000000 | 0.500000 | 0.325000 | -0.000744 |
| PP-OPT21 | ppopt21_uplift_gate__src=pp15_best_mape__model=catboost__thr=0p18__s=0p75 | uplift_correction_selector | 0.137161 | 0.271268 | 0.807925 | 0.000268 | -0.000127 | -0.000205 | 1.000000 | 0.495833 | 0.329167 | -0.000743 |
| PP-OPT24 | ppopt24_conformal_gate__src=pp20_protocol__s=0p75__cap=0p018 | conformal_risk_gate | 0.136776 | 0.271302 | 0.807362 | -0.000117 | -0.000093 | -0.000768 | 1.000000 | 0.550000 | 0.308333 | -0.000727 |
| PP-OPT24 | ppopt24_conformal_gate__src=pp20_protocol__s=0p75__cap=0p022 | conformal_risk_gate | 0.136776 | 0.271302 | 0.807362 | -0.000117 | -0.000093 | -0.000768 | 1.000000 | 0.550000 | 0.308333 | -0.000727 |
| PP-OPT24 | ppopt24_conformal_gate__src=pp20_protocol__s=0p55__cap=0p018 | conformal_risk_gate | 0.136771 | 0.271327 | 0.807568 | -0.000121 | -0.000068 | -0.000562 | 1.000000 | 0.550000 | 0.316667 | -0.000714 |
| PP-OPT24 | ppopt24_conformal_gate__src=pp20_protocol__s=0p55__cap=0p022 | conformal_risk_gate | 0.136771 | 0.271327 | 0.807568 | -0.000121 | -0.000068 | -0.000562 | 1.000000 | 0.550000 | 0.316667 | -0.000714 |
| PP-OPT25 | ppopt25_catboost_uplift__thr=0p2__s=0p75 | catboost_categorical_specialist | 0.137241 | 0.271246 | 0.807877 | 0.000348 | -0.000148 | -0.000253 | 1.000000 | 0.504167 | 0.312500 | -0.000708 |
| PP-OPT21 | ppopt21_uplift_gate__src=pp15_best_mape__model=catboost__thr=0p18__s=0p55 | uplift_correction_selector | 0.137044 | 0.271300 | 0.807980 | 0.000151 | -0.000095 | -0.000150 | 1.000000 | 0.495833 | 0.316667 | -0.000707 |
| PP-OPT21 | ppopt21_uplift_gate__src=pp15_best_mape__model=lgbm__thr=0p28__s=0p55 | uplift_correction_selector | 0.137252 | 0.271155 | 0.807884 | 0.000360 | -0.000240 | -0.000246 | 1.000000 | 0.475000 | 0.279167 | -0.000704 |
| PP-OPT21 | ppopt21_uplift_gate__src=pp15_best_mape__model=lgbm__thr=0p38__s=0p75 | uplift_correction_selector | 0.137239 | 0.271150 | 0.807880 | 0.000346 | -0.000245 | -0.000250 | 1.000000 | 0.508333 | 0.270833 | -0.000689 |
| PP-OPT25 | ppopt25_catboost_uplift__thr=0p2__s=0p55 | catboost_categorical_specialist | 0.137102 | 0.271285 | 0.807945 | 0.000210 | -0.000110 | -0.000185 | 1.000000 | 0.504167 | 0.304167 | -0.000681 |
| PP-OPT21 | ppopt21_uplift_gate__src=pp15_best_mape__model=lgbm__thr=0p38__s=0p55 | uplift_correction_selector | 0.137101 | 0.271214 | 0.807947 | 0.000208 | -0.000181 | -0.000183 | 1.000000 | 0.504167 | 0.258333 | -0.000636 |
| PP-OPT23 | ppopt23_monotonic_gate__src=opt8_cat_price_band__thr=0p36__s=0p45 | monotonic_constrained_gate | 0.137272 | 0.271133 | 0.808248 | 0.000379 | -0.000262 | 0.000118 | 0.975000 | 0.537500 | 0.250000 | -0.000423 |
| PP-OPT23 | ppopt23_monotonic_gate__src=opt8_cat_price_band__thr=0p36__s=0p65 | monotonic_constrained_gate | 0.137777 | 0.271019 | 0.808300 | 0.000884 | -0.000376 | 0.000171 | 0.970833 | 0.537500 | 0.262500 | -0.000329 |
| PP-OPT21 | ppopt21_uplift_gate__src=opt8_artist_mape__model=catboost__thr=0p38__s=0p55 | uplift_correction_selector | 0.137756 | 0.271027 | 0.808698 | 0.000864 | -0.000368 | 0.000568 | 1.000000 | 0.525000 | 0.325000 | -0.000321 |
| PP-OPT23 | ppopt23_monotonic_gate__src=pp19_best_score__thr=0p16__s=0p85 | monotonic_constrained_gate | 0.136756 | 0.271337 | 0.807946 | -0.000137 | -0.000058 | -0.000184 | 1.000000 | 0.816667 | 0.120833 | -0.000314 |
| PP-OPT23 | ppopt23_monotonic_gate__src=opt8_cat_price_band__thr=0p26__s=0p45 | monotonic_constrained_gate | 0.137730 | 0.271043 | 0.808306 | 0.000838 | -0.000352 | 0.000176 | 0.995833 | 0.500000 | 0.237500 | -0.000308 |

## Test에서 MAPE와 p95를 동시에 개선한 후보
| item_id | candidate | family | test_MdAPE | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MdAPE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | incumbent_all3_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-OPT23 | ppopt23_monotonic_gate__src=pp15_best_mape__thr=0p16__s=0p85 | monotonic_constrained_gate | 0.137878 | 0.270707 | 0.807660 | 0.000986 | -0.000688 | -0.000470 | 1.000000 | 0.504167 | 0.400000 | -0.001185 |
| PP-OPT23 | ppopt23_monotonic_gate__src=pp15_best_mape__thr=0p26__s=0p85 | monotonic_constrained_gate | 0.137574 | 0.270842 | 0.807781 | 0.000681 | -0.000553 | -0.000349 | 1.000000 | 0.504167 | 0.395833 | -0.001132 |
| PP-OPT23 | ppopt23_monotonic_gate__src=pp15_best_mape__thr=0p16__s=0p65 | monotonic_constrained_gate | 0.137606 | 0.270866 | 0.807771 | 0.000714 | -0.000529 | -0.000359 | 1.000000 | 0.504167 | 0.391667 | -0.001096 |
| PP-OPT23 | ppopt23_monotonic_gate__src=pp15_best_mape__thr=0p26__s=0p65 | monotonic_constrained_gate | 0.137373 | 0.270971 | 0.807863 | 0.000481 | -0.000424 | -0.000267 | 1.000000 | 0.504167 | 0.387500 | -0.001053 |
| PP-OPT23 | ppopt23_monotonic_gate__src=pp15_best_mape__thr=0p36__s=0p85 | monotonic_constrained_gate | 0.137269 | 0.270978 | 0.807904 | 0.000377 | -0.000417 | -0.000226 | 1.000000 | 0.637500 | 0.383333 | -0.001049 |
| PP-OPT23 | ppopt23_monotonic_gate__src=pp15_best_mape__thr=0p16__s=0p45 | monotonic_constrained_gate | 0.137334 | 0.271027 | 0.807881 | 0.000442 | -0.000368 | -0.000249 | 1.000000 | 0.504167 | 0.383333 | -0.001006 |
| PP-OPT23 | ppopt23_monotonic_gate__src=pp15_best_mape__thr=0p36__s=0p65 | monotonic_constrained_gate | 0.137140 | 0.271074 | 0.807957 | 0.000248 | -0.000321 | -0.000173 | 1.000000 | 0.637500 | 0.366667 | -0.000967 |
| PP-OPT24 | ppopt24_conformal_gate__src=pp19_best_score__s=0p95__cap=0p018 | conformal_risk_gate | 0.136601 | 0.271222 | 0.807076 | -0.000291 | -0.000173 | -0.001054 | 1.000000 | 0.545833 | 0.370833 | -0.000935 |
| PP-OPT24 | ppopt24_conformal_gate__src=pp19_best_score__s=0p95__cap=0p022 | conformal_risk_gate | 0.136601 | 0.271222 | 0.807076 | -0.000291 | -0.000173 | -0.001054 | 1.000000 | 0.545833 | 0.370833 | -0.000935 |
| PP-OPT23 | ppopt23_monotonic_gate__src=pp15_best_mape__thr=0p26__s=0p45 | monotonic_constrained_gate | 0.137173 | 0.271099 | 0.807945 | 0.000280 | -0.000295 | -0.000185 | 1.000000 | 0.504167 | 0.358333 | -0.000930 |
| PP-OPT21 | ppopt21_uplift_gate__src=pp15_best_mape__model=lgbm__thr=0p18__s=0p55 | uplift_correction_selector | 0.137403 | 0.271098 | 0.807821 | 0.000511 | -0.000297 | -0.000309 | 1.000000 | 0.483333 | 0.366667 | -0.000913 |
| PP-OPT21 | ppopt21_uplift_gate__src=pp15_best_mape__model=lgbm__thr=0p28__s=0p95 | uplift_correction_selector | 0.137638 | 0.270984 | 0.807704 | 0.000745 | -0.000411 | -0.000425 | 1.000000 | 0.475000 | 0.350000 | -0.000910 |
| PREV | previous_challenger_pp20 | previous_challenger | 0.136835 | 0.271182 | 0.806472 | -0.000058 | -0.000213 | -0.001658 | 1.000000 | 0.554167 | 0.316667 | -0.000883 |
| PP-OPT24 | ppopt24_conformal_gate__src=pp19_best_score__s=0p75__cap=0p018 | conformal_risk_gate | 0.136627 | 0.271257 | 0.807299 | -0.000266 | -0.000138 | -0.000831 | 1.000000 | 0.545833 | 0.362500 | -0.000878 |
| PP-OPT24 | ppopt24_conformal_gate__src=pp19_best_score__s=0p75__cap=0p022 | conformal_risk_gate | 0.136627 | 0.271257 | 0.807299 | -0.000266 | -0.000138 | -0.000831 | 1.000000 | 0.545833 | 0.362500 | -0.000878 |
| PP-OPT21 | ppopt21_uplift_gate__src=pp15_best_mape__model=lgbm__thr=0p28__s=0p75 | uplift_correction_selector | 0.137445 | 0.271069 | 0.807794 | 0.000552 | -0.000325 | -0.000336 | 1.000000 | 0.475000 | 0.345833 | -0.000874 |
| PP-OPT21 | ppopt21_uplift_gate__src=pp15_best_mape__model=lgbm__thr=0p38__s=0p95 | uplift_correction_selector | 0.137377 | 0.271086 | 0.807813 | 0.000484 | -0.000308 | -0.000317 | 1.000000 | 0.508333 | 0.320833 | -0.000814 |
| PP-OPT24 | ppopt24_conformal_gate__src=pp19_best_score__s=0p55__cap=0p018 | conformal_risk_gate | 0.136652 | 0.271293 | 0.807521 | -0.000241 | -0.000101 | -0.000609 | 1.000000 | 0.545833 | 0.350000 | -0.000812 |
| PP-OPT24 | ppopt24_conformal_gate__src=pp19_best_score__s=0p55__cap=0p022 | conformal_risk_gate | 0.136652 | 0.271293 | 0.807521 | -0.000241 | -0.000101 | -0.000609 | 1.000000 | 0.545833 | 0.350000 | -0.000812 |
| PP-OPT23 | ppopt23_monotonic_gate__src=pp15_best_mape__thr=0p36__s=0p45 | monotonic_constrained_gate | 0.137012 | 0.271171 | 0.808011 | 0.000119 | -0.000224 | -0.000119 | 1.000000 | 0.633333 | 0.304167 | -0.000786 |
| PP-OPT24 | ppopt24_conformal_gate__src=pp20_protocol__s=0p95__cap=0p018 | conformal_risk_gate | 0.136790 | 0.271278 | 0.807157 | -0.000102 | -0.000117 | -0.000973 | 1.000000 | 0.550000 | 0.316667 | -0.000773 |
| PP-OPT24 | ppopt24_conformal_gate__src=pp20_protocol__s=0p95__cap=0p022 | conformal_risk_gate | 0.136790 | 0.271278 | 0.807157 | -0.000102 | -0.000117 | -0.000973 | 1.000000 | 0.550000 | 0.316667 | -0.000773 |
| PP-OPT21 | ppopt21_uplift_gate__src=pp15_best_mape__model=catboost__thr=0p18__s=0p95 | uplift_correction_selector | 0.137278 | 0.271235 | 0.807871 | 0.000385 | -0.000160 | -0.000259 | 1.000000 | 0.491667 | 0.337500 | -0.000771 |
| PP-OPT25 | ppopt25_catboost_uplift__thr=0p2__s=0p95 | catboost_categorical_specialist | 0.137379 | 0.271208 | 0.807810 | 0.000487 | -0.000187 | -0.000320 | 1.000000 | 0.500000 | 0.325000 | -0.000744 |
| PP-OPT21 | ppopt21_uplift_gate__src=pp15_best_mape__model=catboost__thr=0p18__s=0p75 | uplift_correction_selector | 0.137161 | 0.271268 | 0.807925 | 0.000268 | -0.000127 | -0.000205 | 1.000000 | 0.495833 | 0.329167 | -0.000743 |
| PP-OPT24 | ppopt24_conformal_gate__src=pp20_protocol__s=0p75__cap=0p018 | conformal_risk_gate | 0.136776 | 0.271302 | 0.807362 | -0.000117 | -0.000093 | -0.000768 | 1.000000 | 0.550000 | 0.308333 | -0.000727 |
| PP-OPT24 | ppopt24_conformal_gate__src=pp20_protocol__s=0p75__cap=0p022 | conformal_risk_gate | 0.136776 | 0.271302 | 0.807362 | -0.000117 | -0.000093 | -0.000768 | 1.000000 | 0.550000 | 0.308333 | -0.000727 |
| PP-OPT24 | ppopt24_conformal_gate__src=pp20_protocol__s=0p55__cap=0p018 | conformal_risk_gate | 0.136771 | 0.271327 | 0.807568 | -0.000121 | -0.000068 | -0.000562 | 1.000000 | 0.550000 | 0.316667 | -0.000714 |
| PP-OPT24 | ppopt24_conformal_gate__src=pp20_protocol__s=0p55__cap=0p022 | conformal_risk_gate | 0.136771 | 0.271327 | 0.807568 | -0.000121 | -0.000068 | -0.000562 | 1.000000 | 0.550000 | 0.316667 | -0.000714 |
| PP-OPT25 | ppopt25_catboost_uplift__thr=0p2__s=0p75 | catboost_categorical_specialist | 0.137241 | 0.271246 | 0.807877 | 0.000348 | -0.000148 | -0.000253 | 1.000000 | 0.504167 | 0.312500 | -0.000708 |
| PP-OPT21 | ppopt21_uplift_gate__src=pp15_best_mape__model=catboost__thr=0p18__s=0p55 | uplift_correction_selector | 0.137044 | 0.271300 | 0.807980 | 0.000151 | -0.000095 | -0.000150 | 1.000000 | 0.495833 | 0.316667 | -0.000707 |
| PP-OPT21 | ppopt21_uplift_gate__src=pp15_best_mape__model=lgbm__thr=0p28__s=0p55 | uplift_correction_selector | 0.137252 | 0.271155 | 0.807884 | 0.000360 | -0.000240 | -0.000246 | 1.000000 | 0.475000 | 0.279167 | -0.000704 |
| PP-OPT21 | ppopt21_uplift_gate__src=pp15_best_mape__model=lgbm__thr=0p38__s=0p75 | uplift_correction_selector | 0.137239 | 0.271150 | 0.807880 | 0.000346 | -0.000245 | -0.000250 | 1.000000 | 0.508333 | 0.270833 | -0.000689 |
| PP-OPT25 | ppopt25_catboost_uplift__thr=0p2__s=0p55 | catboost_categorical_specialist | 0.137102 | 0.271285 | 0.807945 | 0.000210 | -0.000110 | -0.000185 | 1.000000 | 0.504167 | 0.304167 | -0.000681 |
| PP-OPT21 | ppopt21_uplift_gate__src=pp15_best_mape__model=lgbm__thr=0p38__s=0p55 | uplift_correction_selector | 0.137101 | 0.271214 | 0.807947 | 0.000208 | -0.000181 | -0.000183 | 1.000000 | 0.504167 | 0.258333 | -0.000636 |
| PP-OPT23 | ppopt23_monotonic_gate__src=pp19_best_score__thr=0p16__s=0p85 | monotonic_constrained_gate | 0.136756 | 0.271337 | 0.807946 | -0.000137 | -0.000058 | -0.000184 | 1.000000 | 0.816667 | 0.120833 | -0.000314 |
| PP-OPT23 | ppopt23_monotonic_gate__src=pp19_best_score__thr=0p16__s=0p65 | monotonic_constrained_gate | 0.136788 | 0.271350 | 0.807989 | -0.000105 | -0.000045 | -0.000141 | 1.000000 | 0.816667 | 0.112500 | -0.000280 |
| PP-OPT21 | ppopt21_uplift_gate__src=pp15_best_mape__model=catboost__thr=0p28__s=0p95 | uplift_correction_selector | 0.137017 | 0.271350 | 0.807994 | 0.000124 | -0.000045 | -0.000136 | 1.000000 | 0.745833 | 0.112500 | -0.000271 |
| PP-OPT21 | ppopt21_uplift_gate__src=pp15_best_mape__model=catboost__thr=0p28__s=0p75 | uplift_correction_selector | 0.136955 | 0.271358 | 0.808023 | 0.000062 | -0.000037 | -0.000107 | 1.000000 | 0.745833 | 0.112500 | -0.000270 |
| PP-OPT21 | ppopt21_uplift_gate__src=pp15_best_mape__model=catboost__thr=0p28__s=0p55 | uplift_correction_selector | 0.136893 | 0.271367 | 0.808052 | -0.000000 | -0.000028 | -0.000078 | 1.000000 | 0.745833 | 0.112500 | -0.000269 |

## 해석
이번 실험은 모델 특성 자체를 보정 구조에 넣는 실험이다. 가장 중요한 비교 기준은 PP-OPT7 대비 개선뿐 아니라 PP-OPT20 challenger 대비 추가 개선 여부다.
uplift gate와 segment router 계열이 강하면 보정 선택 문제로, quantile/conformal/monotonic 계열이 강하면 위험도 축소 문제로 다음 단계를 좁히면 된다.

## 실행 설정
```json
{
  "experiment_id": "PP-OPT21-28",
  "experiment_slug": "PP-OPT21_28_warm_model_characteristic_experiments",
  "created_at": "2026-06-09T11:33:07",
  "seed": 20260609,
  "base_candidate": "hcoef_stable",
  "incumbent_candidate": "incumbent_operational_pp_opt7",
  "previous_challenger": "previous_challenger_pp20",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 259,
  "prediction_rows": 291634,
  "items": [
    {
      "item_id": "PP-OPT21",
      "priority": "1",
      "title": "uplift model 기반 보정 선택",
      "description": "row별로 보정하면 좋아지는지를 직접 학습한다."
    },
    {
      "item_id": "PP-OPT22",
      "priority": "2",
      "title": "quantile residual shrinkage",
      "description": "잔차의 q25/q50/q75를 학습해 불확실성이 큰 보정은 줄인다."
    },
    {
      "item_id": "PP-OPT23",
      "priority": "3",
      "title": "monotonic constrained gate",
      "description": "불확실성이 커질수록 보정 사용 확률이 줄도록 제약을 둔다."
    },
    {
      "item_id": "PP-OPT24",
      "priority": "4",
      "title": "conformal risk gate",
      "description": "예측구간 폭과 비순응 점수로 위험한 row의 보정을 축소한다."
    },
    {
      "item_id": "PP-OPT25",
      "priority": "5",
      "title": "CatBoost categorical specialist",
      "description": "범주형 상호작용을 잘 다루는 CatBoost로 보정/선택을 전담시킨다."
    },
    {
      "item_id": "PP-OPT26",
      "priority": "6",
      "title": "LightGBM risk classifier specialist",
      "description": "LightGBM을 가격 보정이 아니라 tail-risk gate 전용으로 사용한다."
    },
    {
      "item_id": "PP-OPT27",
      "priority": "7",
      "title": "two-stage micro residual",
      "description": "선택 후보 이후 남은 잔차만 아주 작은 cap으로 2차 보정한다."
    },
    {
      "item_id": "PP-OPT28",
      "priority": "8",
      "title": "segment별 model-of-models router",
      "description": "구간별로 PP-OPT7/20/15/19/14 후보 중 가장 안정적인 후보를 선택한다."
    }
  ],
  "selected_components": {
    "pp20_protocol": "ppopt20_protocol_selected__source=ppopt19_segment_tuning__profile_low_support_tail__artist_cat_artist_mean__as_0p25__ts_0p55",
    "pp20_source": "ppopt19_segment_tuning__profile=low_support_tail__artist=cat_artist_mean__as=0p25__ts=0p55",
    "pp19_best_score": "ppopt19_segment_tuning__profile=price_tail_high__artist=artist__as=0p35__ts=0p75",
    "pp14_best_score": "ppopt14_gate_grid__artist=artist_stable__sthr=0p12__tthr=0p25__as=0p2__ts=0p75__cap=0p024",
    "pp15_best_mape": "ppopt15_absorb_pp12__base=pp9_best_mape__p12s=0p34__p9s=1p05__cap=0p026",
    "pp16_best_score": "ppopt16_tail_label__label=p90__src=xgb_tail__thr=0p2__s=0p65",
    "pp17_best_score": "ppopt17_mdape_guard__src=pp9_best_operational__floor=0p4__s=0p9",
    "pp18_best_mape": "ppopt18_constrained_ensemble__aw=0p22__cw=0p36__xw=0p35__qw=0p24__p12w=0p16__cap=0p022",
    "opt8_artist_mape": "existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=1p0__totalcap=0p04",
    "opt8_artist_stable": "existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p15__artist=am_h_birth_gen_total_works_gn_a01_c03_s075__cw=0p8__aw=0p75__totalcap=0p025",
    "opt8_cat_price_band": "catboost_price_band__cap_strength",
    "opt8_qwidth_mild": "qwidth_strength__continuous_mild",
    "opt8_qwidth_strict": "qwidth_strength__continuous_strict",
    "opt8_xgb_tail": "gap_routing__xgb_tail_else_incumbent__existing_opt5__xgb_xgboost_low_only_diagnostic_cap0p05__rout",
    "opt8_tail_guard": "tail_guard__logistic",
    "opt8_lightgbm_tail_guard": "lightgbm_tail_guard__classifier",
    "opt8_cat_lgb_equal": "correction_ensemble__cat_lgb_equal"
  },
  "thresholds": {
    "p85": 0.38339160296436176,
    "p90": 0.4636774710873784,
    "p95": 0.6365947866362616
  },
  "sources": {
    "pp_opt14_predictions": "experiments/track6/PP-OPT14_20_warm_gate_refinement_experiments/outputs/candidate_predictions.csv",
    "pp_opt14_aggregate": "experiments/track6/PP-OPT14_20_warm_gate_refinement_experiments/outputs/aggregate_candidate_stability.csv",
    "pp_opt14_config": "experiments/track6/PP-OPT14_20_warm_gate_refinement_experiments/artifacts/run_config.json",
    "pp_opt8_helper": "scripts/track6/run_pp_opt8_warm_extended_correction_experiments.py",
    "pp_opt9_helper": "scripts/track6/run_pp_opt9_13_warm_followup_improvement_experiments.py",
    "pp_opt14_helper": "scripts/track6/run_pp_opt14_20_warm_gate_refinement_experiments.py"
  }
}
```