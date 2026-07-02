# PP-OPT8 Warm 추가 보정 실험 결과

- 작성일: 2026-06-09 10:56
- 목적: PP-OPT7 운영 후보를 1순위 기준으로 고정하고, 추가 보정 실험 20개 방향을 동일 Warm 기본 split에서 비교한다.
- 데이터 기준: 제출용 100건 제외. Warm validation OOF 519건, Warm fixed test 607건.
- 기준 후보: `incumbent_operational_pp_opt7`
- 재현 스크립트: `scripts/track6/run_pp_opt8_warm_extended_correction_experiments.py`

## 1. 현재 운영 후보 기준 성능

| eval_split | n | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| test | 607 | 0.136893 | 0.271395 | 0.808130 | 0.398341 | 0.779242 | 0.883031 |
| validation_oof | 519 | 0.125923 | 0.207023 | 0.636595 | 0.324133 | 0.782274 | 0.911368 |

## 2. 실험 방향별 최선 후보

| priority | title | tested_candidates | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | validation_delta_vs_incumbent_MAPE | operational_pass_vs_incumbent | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8 | 작가 메타 보정 계층화 | 139 | 0.270107 | 0.810444 | -0.001288 | 0.002314 | -0.002138 | False | existing_catboost_artist_focus | existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p15__artist=am_h_birth_gen_total_works_gn_a01_c03_s075__cw=0p8__aw=0p75__totalcap=0p025 |
| L8 | LightGBM tail-risk guard | 1 | 0.271509 | 0.807864 | 0.000114 | -0.000266 | 0.000089 | False | lightgbm_tail_guard | lightgbm_tail_guard__classifier |
| 4 | CatBoost 잔차 모델 price band별 보정 | 1 | 0.270011 | 0.808897 | -0.001384 | 0.000767 | -0.000767 | False | catboost_price_band | catboost_price_band__cap_strength |
| 1 | 퀀타일 폭 기반 보정 강도 세분화 | 3 | 0.270839 | 0.807708 | -0.000556 | -0.000422 | -0.000568 | False | quantile_width_strength | qwidth_strength__continuous_mild |
| 2 | CatBoost 보정값 구간별 cap 최적화 | 1 | 0.270534 | 0.808920 | -0.000861 | 0.000790 | -0.000736 | False | catboost_segment_cap | catboost_segment_cap__price_svc_qwidth |
| L5 | CatBoost/LightGBM 라우팅 | 1 | 0.272345 | 0.807417 | 0.000950 | -0.000713 | 0.000268 | False | catboost_lightgbm_routing | catboost_lightgbm_routing__stable_lgb_else_cat |
| 3 | 과대예측/과소예측 방향 분류 후 보정 | 2 | 0.272438 | 0.807935 | 0.001043 | -0.000195 | 0.000579 | False | direction_guard | direction_guard__prob0p55 |
| L6 | CatBoost + LightGBM 보정 앙상블 | 1 | 0.272177 | 0.807811 | 0.000782 | -0.000319 | 0.000146 | False | catboost_lightgbm_ensemble | catboost_lightgbm_ensemble__risk_weighted |
| 6 | p95 위험 전용 tail guard 모델 | 1 | 0.271975 | 0.806828 | 0.000580 | -0.001302 | 0.000390 | False | tail_guard | tail_guard__logistic |
| L2 | CatBoost vs LightGBM 동일 피쳐 비교 | 1 | 0.271812 | 0.807417 | 0.000417 | -0.000713 | 0.000473 | False | catboost_vs_lightgbm | catboost_same_feature__qwidth_cap_riskstrict |
| 10 | Huber/Ridge 선형 계수 재보정 | 2 | 0.273365 | 0.808383 | 0.001971 | 0.000253 | -0.000035 | False | linear_huber_recalibration | linear_huber_recalibration__huber_cap0p018 |
| 12 | 보정값 앙상블 | 6 | 0.272989 | 0.806366 | 0.001594 | -0.001764 | 0.001183 | False | existing_source | existing_opt5__hcoef_stable |
| 5 | 퀀타일 회귀 잔차 중앙값과 위험폭 동시 예측 | 1 | 0.272485 | 0.809745 | 0.001090 | 0.001615 | 0.000493 | False | quantile_residual | quantile_residual__lgbm_q10_q50_q90 |
| L7 | LightGBM quantile 잔차 모델 | 1 | 0.272485 | 0.809745 | 0.001090 | 0.001615 | 0.000493 | False | lightgbm_quantile | lightgbm_quantile__median_width_guard |
| 7 | 모델 간 예측 gap 기반 라우팅 | 1 | 0.271547 | 0.800825 | 0.000152 | -0.007305 | 0.000026 | False | gap_routing | gap_routing__xgb_tail_else_incumbent__existing_opt5__xgb_xgboost_low_only_diagnostic_cap0p05__rout |
| L4 | LightGBM 구간별 보정 | 1 | 0.273681 | 0.810010 | 0.002286 | 0.001880 | 0.000973 | False | lightgbm_segment | lightgbm_segmented__price_band_models |
| 11 | XGBoost 보조 후보 라우팅 | 5 | 0.272146 | 0.803660 | 0.000751 | -0.004470 | 0.001450 | False | existing_xgboost_focus | existing_opt5__xgboost_focus__xgboost_low_only_diagnostic_cap0p02__route=medium_only |
| L3 | LightGBM + 퀀타일 폭 기반 cap | 1 | 0.272267 | 0.811010 | 0.000872 | 0.002880 | -0.000137 | False | lightgbm_qwidth_cap | lightgbm_qwidth_cap__balanced |
| 9 | 작품 피쳐 조합 보정 | 1 | 0.274410 | 0.834597 | 0.003016 | 0.026467 | 0.000659 | False | artwork_combo | artwork_combo__ridge_cap0p02 |
| L1 | LightGBM 잔차 보정 | 3 | 0.271933 | 0.825642 | 0.000538 | 0.017512 | -0.000050 | False | lightgbm_residual | lightgbm_residual__s0p75_cap0p018 |

## 3. 운영 후보를 통과한 추가 후보

_No rows._

## 4. Test MAPE 기준 상위 후보

| candidate | family | item_id | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MdAPE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | validation_delta_vs_incumbent_MAPE | validation_delta_vs_incumbent_p95_APE | operational_pass_vs_incumbent | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=1p0__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.267972 | 0.813699 | 0.000953 | -0.003423 | 0.005569 | -0.003181 | 0.002840 | False | -0.000758 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=0p75__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268030 | 0.813573 | 0.001418 | -0.003365 | 0.005443 | -0.002715 | 0.005056 | False | 0.000665 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=1p0__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268053 | 0.813699 | 0.002698 | -0.003342 | 0.005569 | -0.003044 | 0.002967 | False | -0.000195 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=0p75__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268120 | 0.813573 | 0.001469 | -0.003275 | 0.005443 | -0.002557 | 0.005110 | False | 0.000597 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=0p5__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268129 | 0.813447 | 0.001016 | -0.003266 | 0.005317 | -0.002192 | 0.007192 | False | 0.002977 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=0p5__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268236 | 0.813447 | -0.000122 | -0.003159 | 0.005317 | -0.002027 | 0.007243 | False | 0.002627 |
| existing_opt5__catboost_focus__tier=same__qmult=same__cap=0p05__capprof=fixed__s=1p15 | existing_catboost_focus | A12 | 0.268249 | 0.820323 | 0.002816 | -0.003146 | 0.012193 | -0.000273 | 0.011845 | False | 0.020041 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=0p75__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=1p0__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268262 | 0.813699 | 0.003904 | -0.003132 | 0.005569 | -0.002766 | 0.003061 | False | 0.000366 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_for_sale_gn_a01_c03_s075__cw=1p0__aw=0p75__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268265 | 0.813772 | 0.000754 | -0.003129 | 0.005642 | -0.002509 | 0.005252 | False | 0.002514 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_for_sale_gn_a01_c03_s075__cw=1p0__aw=0p5__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268270 | 0.813772 | -0.000136 | -0.003125 | 0.005642 | -0.002069 | 0.007323 | False | 0.004208 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p0__artist=am_h_birth_gen_for_sale_gn_a01_c03_s075__cw=1p0__aw=0p75__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268316 | 0.813772 | 0.000754 | -0.003079 | 0.005642 | -0.002386 | 0.005305 | False | 0.002329 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_gallery_gn_a01_c03_s075__cw=1p0__aw=0p5__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268357 | 0.813772 | -0.000136 | -0.003038 | 0.005642 | -0.002334 | 0.007646 | False | 0.004993 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p0__artist=am_h_birth_gen_for_sale_gn_a01_c03_s075__cw=1p0__aw=0p5__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268360 | 0.813772 | -0.001475 | -0.003035 | 0.005642 | -0.001908 | 0.007374 | False | 0.004026 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_for_sale_gn_a01_c03_s075__cw=1p0__aw=1p0__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268369 | 0.813772 | 0.000189 | -0.003026 | 0.005642 | -0.002836 | 0.003171 | False | 0.000741 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=0p75__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=0p75__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268372 | 0.813573 | 0.002805 | -0.003023 | 0.005443 | -0.002250 | 0.005200 | False | 0.000806 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p0__artist=am_h_birth_gen_for_sale_gn_a01_c03_s075__cw=1p0__aw=1p0__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268421 | 0.813772 | -0.000049 | -0.002974 | 0.005642 | -0.002753 | 0.003227 | False | 0.000490 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268426 | 0.813352 | 0.005343 | -0.002969 | 0.005222 | -0.003101 | 0.002397 | False | 0.000176 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p0__artist=am_h_birth_gen_gallery_gn_a01_c03_s075__cw=1p0__aw=0p5__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268451 | 0.813772 | -0.001478 | -0.002943 | 0.005642 | -0.002168 | 0.007696 | False | 0.004873 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=0p75__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268483 | 0.813226 | 0.001952 | -0.002912 | 0.005096 | -0.002593 | 0.004766 | False | -0.000124 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c05_s075__cw=1p0__aw=0p5__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268498 | 0.813447 | 0.001884 | -0.002897 | 0.005317 | -0.002287 | 0.004761 | False | 0.002753 |
| existing_opt5__catboost_focus__tier=same__qmult=same__cap=0p05__capprof=fixed__s=1p0 | existing_catboost_focus | A12 | 0.268498 | 0.820034 | 0.002239 | -0.002897 | 0.011904 | -0.000236 | 0.011540 | False | 0.019103 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268518 | 0.813352 | 0.006588 | -0.002877 | 0.005222 | -0.002935 | 0.002684 | False | 0.000628 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_gallery_gn_a01_c03_s075__cw=1p0__aw=0p75__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268534 | 0.813772 | 0.000565 | -0.002861 | 0.005642 | -0.002823 | 0.005736 | False | 0.004051 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=0p75__artist=am_h_birth_gen_for_sale_gn_a01_c03_s075__cw=1p0__aw=0p75__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268569 | 0.813772 | 0.002729 | -0.002826 | 0.005642 | -0.002123 | 0.005394 | False | 0.002441 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=0p75__artist=am_h_birth_gen_for_sale_gn_a01_c03_s075__cw=1p0__aw=1p0__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268576 | 0.813772 | 0.000942 | -0.002819 | 0.005642 | -0.002537 | 0.003320 | False | 0.000382 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=0p75__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268591 | 0.813226 | 0.004335 | -0.002804 | 0.005096 | -0.002427 | 0.005051 | False | 0.000695 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c05_s075__cw=1p0__aw=0p5__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268592 | 0.813447 | 0.001308 | -0.002803 | 0.005317 | -0.002115 | 0.004815 | False | 0.002468 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=1p0__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268592 | 0.813120 | 0.004114 | -0.002803 | 0.004990 | -0.003214 | 0.001188 | False | -0.000382 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=0p75__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=0p5__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268604 | 0.813101 | 0.002225 | -0.002791 | 0.004971 | -0.001733 | 0.007329 | False | 0.002728 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_total_works_gn_a01_c03_s075__cw=1p0__aw=0p5__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268622 | 0.813203 | -0.000414 | -0.002773 | 0.005073 | -0.002120 | 0.008044 | False | 0.002195 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p0__artist=am_h_birth_gen_gallery_gn_a01_c03_s075__cw=1p0__aw=0p75__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268624 | 0.813772 | 0.000754 | -0.002771 | 0.005642 | -0.002707 | 0.005789 | False | 0.003954 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c05_s075__cw=1p0__aw=0p75__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268628 | 0.813573 | 0.001759 | -0.002767 | 0.005443 | -0.002797 | 0.001382 | False | 0.000181 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=0p5__totalcap=0p03 | existing_catboost_artist_focus | A08 | 0.268646 | 0.811900 | 0.001016 | -0.002749 | 0.003771 | -0.001957 | 0.007192 | False | 0.002852 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_for_sale_gn_a01_c05_s075__cw=1p0__aw=0p5__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268652 | 0.813772 | -0.001284 | -0.002743 | 0.005642 | -0.002157 | 0.004892 | False | 0.003914 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=1p0__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268652 | 0.813120 | 0.004114 | -0.002743 | 0.004990 | -0.003158 | 0.001547 | False | -0.000432 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=0p75__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=1p0__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.268822 | 0.813120 | 0.004534 | -0.002573 | 0.004990 | -0.002915 | 0.002144 | False | -0.000174 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.269123 | 0.812693 | 0.005678 | -0.002272 | 0.004564 | -0.002956 | 0.000379 | False | -0.000124 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p04 | existing_catboost_artist_focus | A08 | 0.269181 | 0.812693 | 0.005662 | -0.002214 | 0.004564 | -0.002902 | 0.000411 | False | -0.000072 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p03 | existing_catboost_artist_focus | A08 | 0.269262 | 0.811593 | 0.006413 | -0.002133 | 0.003463 | -0.002807 | 0.000379 | False | -0.000358 |
| existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=1p0__totalcap=0p025 | existing_catboost_artist_focus | A08 | 0.269262 | 0.810958 | 0.004114 | -0.002133 | 0.002828 | -0.002693 | 0.003119 | False | -0.000966 |

## 5. 해석 기준

- `test_delta_vs_incumbent_MAPE < 0`이면 현재 운영 후보보다 fixed test 평균 오차가 개선된 것이다.
- `test_delta_vs_incumbent_p95_APE <= 0.001`이면 현재 운영 후보 대비 p95 악화가 0.001 이하로 제한된 것이다.
- `operational_pass_vs_incumbent=True`는 validation 반복 안정성과 fixed test 조건을 동시에 만족한 후보만 표시한다.
- 단순 MAPE가 낮아도 p95가 크게 악화되면 운영 후보로 보지 않는다.

## 6. 산출물

- `outputs/candidate_predictions.csv`
- `outputs/candidate_metrics.csv`
- `outputs/repeated_validation_detail.csv`
- `outputs/repeated_validation_summary.csv`
- `outputs/aggregate_candidate_stability.csv`
- `outputs/experiment_item_summary.csv`
- `artifacts/run_config.json`
- `reports/result_report.md`
- `reports/result_report.html`
