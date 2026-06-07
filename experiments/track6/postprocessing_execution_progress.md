# Track6 후처리 실험 실행 진행 현황

- 기준 문서: `docs/track6/experiments/postprocessing_experiment_matrix.md`
- 실행 기준: 문서의 실행 순서에 맞춰 미실행 실험을 순차 진행
- 현재 진행 범위: `PRE-PP` -> `PRE-CAL` -> `PRE-MODEL/PRE-SPLIT` -> `PP-A` -> `PP-J` -> `PP-B` -> `PP-C` -> `PP-D/PP-E` -> `PP-K` -> `PP-F` -> 조건부 `PP-G/PP-H` -> `PP-I` -> 추가 `PP-M/PP-N/PP-O/PP-P` -> `PP-Q` -> `PP-R` -> `PP-S` -> `PP-T` -> `PP-U` 실행 완료
- 다음 실행 순서: PP-U 피처 교환 결과를 최종 후보 보고서, 서비스 API 정책, 후속 조합 후보에 반영

## 1. 완료된 실험

| 순서 | 실험 | 폴더 | 핵심 결과 |
|---:|---|---|---|
| 1 | `PRE-PP-W` | `experiments/track6/PRE-PP-W_warm_huber_group_drop_ablation` | Warm에서 size 제거 시 MdAPE가 `0.2126 -> 0.5671`로 크게 악화되어 크기 피처가 핵심임을 확인 |
| 1 | `PRE-PP-CB` | `experiments/track6/PRE-PP-CB_cold_catboost_group_drop_ablation` | Cold CatBoost에서 size/depth 제거 시 큰 폭 악화, size와 depth/3D가 보정 기준으로 중요 |
| 1 | `PRE-PP-LGB` | `experiments/track6/PRE-PP-LGB_cold_lightgbm_group_drop_ablation` | LightGBM은 raw size/depth 제거 시 악화, size_bucket 제거는 거의 영향 없음 |
| 2 | `PRE-CAL-W` | `experiments/track6/PRE-CAL-W_warm_huber_correction_map` | Warm Huber는 `size_bucket` 보정이 가장 안정적 |
| 2 | `PRE-CAL-CB` | `experiments/track6/PRE-CAL-CB_cold_catboost_correction_map` | Cold CatBoost는 `leaf_segment` 보정이 validation MdAPE `0.3636`으로 가장 강함 |
| 2 | `PRE-CAL-LGB` | `experiments/track6/PRE-CAL-LGB_cold_lightgbm_correction_map` | Cold LightGBM은 `support_size_bucket` 보정이 validation MdAPE `0.3614`로 가장 강함 |
| 3 | `PRE-MODEL-CCB` | `experiments/track6/PRE-MODEL-CCB_cold_catboost_vs_lightgbm` | Cold 기준 원 모델 비교에서는 LightGBM MdAPE `0.3851`, CatBoost MdAPE `0.4194`로 LightGBM 우위 |
| 4 | `PRE-SPLIT-CCB` | `experiments/track6/PRE-SPLIT-CCB_cold_catboost_segmented_training` | CatBoost 구분 학습은 `medium_shape_bucket` 기준이 MdAPE `0.3784`로 baseline보다 개선 |
| 5 | `PP-A1` | `experiments/track6/PP-A1_global_residual_calibration` | Cold 전체 residual 보정은 개선, Warm은 MdAPE 악화로 보류 |
| 5 | `PP-A2` | `experiments/track6/PP-A2_pred_price_bin_residual_calibration` | Cold 예측 가격대 보정은 개선, Warm은 MdAPE 기준 보류 |
| 5 | `PP-A3` | `experiments/track6/PP-A3_size_segment_residual_calibration` | Warm/Cold 모두 size bucket 보정 후보로 유효 |
| 5 | `PP-A4` | `experiments/track6/PP-A4_medium_support_residual_calibration` | Cold material/support 계열 보정은 개선, Warm은 p95 악화 주의 |
| 5 | `PP-A5` | `experiments/track6/PP-A5_warm_artist_history_residual_calibration` | Warm artist history 보정은 baseline 우위로 보류 |
| 5 | `PP-A6` | `experiments/track6/PP-A6_cold_meta_completeness_residual_calibration` | 현재 Cold feature split에는 운영용 메타 완성도 컬럼이 없어 실질 보정 후보로는 보류 |
| 5 | `PP-A7` | `experiments/track6/PP-A7_hierarchical_segment_residual_calibration` | Cold 계층형 보정이 MdAPE `0.3567`, MAPE `0.5662`로 강하게 개선 |
| 5 | `PP-A8` | `experiments/track6/PP-A8_min_rows_threshold_residual_calibration` | Cold는 `min_rows=30`, Warm은 대표오차만 개선되고 p95 악화로 주의 |
| 6 | `PP-J1` | `experiments/track6/PP-J1_warm_huber_tail_segment_calibration` | Warm Huber tail segment 보정이 validation MdAPE `0.2126 -> 0.2041`, MAPE `0.4167 -> 0.4098`로 개선 |
| 6 | `PP-J2` | `experiments/track6/PP-J2_warm_huber_contribution_segment_calibration` | Huber 계수 기여도 구간 보정은 MAPE/p95는 소폭 개선되지만 MdAPE가 `0.2126 -> 0.2201`로 악화되어 보류 |
| 6 | `PP-J3` | `experiments/track6/PP-J3_warm_catboost_leaf_artist_size_calibration` | Warm CatBoost 후보는 Huber 대비 MdAPE가 높고 leaf/artist-size 보정 개선도 없어 보류 |
| 6 | `PP-J4` | `experiments/track6/PP-J4_cold_catboost_leaf_coverage_calibration` | Cold CatBoost leaf coverage 보정은 `min_rows=20`에서 MdAPE `0.4194 -> 0.3440`, MAPE `0.7332 -> 0.5876`으로 강하게 개선 |
| 6 | `PP-J5` | `experiments/track6/PP-J5_cold_catboost_depth_size_calibration` | Cold CatBoost 2D/3D x size 보정은 MdAPE `0.4194 -> 0.3873`으로 개선되나 PP-J4보다 약함 |
| 6 | `PP-J6` | `experiments/track6/PP-J6_cold_lightgbm_tail_calibration` | Cold LightGBM tail 보정은 cap `0.25`에서 MdAPE `0.3851 -> 0.3538`, MAPE `0.7169 -> 0.6652`로 개선 |
| 7 | `PP-B4` | `experiments/track6/PP-B4_oof_base_residual_source` | Warm Huber, Cold CatBoost, Cold LightGBM의 5-fold OOF 예측과 residual target 생성 완료 |
| 7 | `PP-B1` | `experiments/track6/PP-B1_ridge_residual_correction` | Cold CatBoost validation MdAPE는 `0.4194 -> 0.4112`로 개선되지만 test MdAPE/MAPE가 악화되어 채택 보류 |
| 7 | `PP-B2` | `experiments/track6/PP-B2_huber_residual_correction` | Cold CatBoost validation MAPE/p95는 개선되지만 test p95가 악화되고 Huber 수렴 경고가 있어 보류 |
| 7 | `PP-B3` | `experiments/track6/PP-B3_lightgbm_residual_correction` | Warm test MAPE/p95와 Cold LightGBM test MAPE/p95는 개선되나 Warm/Cold MdAPE 안정성이 부족해 조건부 후보 |
| 7 | `PP-B5` | `experiments/track6/PP-B5_warm_cold_separate_residual_correction` | validation 기준 선택은 Warm/Cold LightGBM residual과 Cold CatBoost Ridge였으나, test 재현성 기준으로는 단독 채택 보류 |
| 8 | `PP-C1` | `experiments/track6/PP-C1_linear_prediction_recalibration` | Cold는 MAPE/p95 개선 효과가 있으나 test MdAPE는 CatBoost에서 악화, Warm도 악화되어 단독 채택 보류 |
| 8 | `PP-C3` | `experiments/track6/PP-C3_monotonic_prediction_recalibration` | validation 개선폭은 크지만 test MdAPE 재현성이 약해 과적합 위험 후보로 분류 |
| 8 | `PP-C5` | `experiments/track6/PP-C5_correction_strength_tuning` | Warm PP-J1 tail 보정은 강도 `0.50`에서 test MdAPE `0.2274 -> 0.2211`, p95 `2.0130 -> 1.9055`로 가장 안정적 |
| 9 | `PP-D1` | `experiments/track6/PP-D1_simple_model_average` | 단순 평균은 Warm/Cold 모두 MAPE/p95 방어에는 도움되지만 MdAPE가 악화되어 단독 채택 보류 |
| 9 | `PP-D2` | `experiments/track6/PP-D2_weighted_model_average` | validation 기준 최적 가중치가 기존 단일 모델을 그대로 선택해, 단순 2모델 가중 평균의 추가 이득은 없음 |
| 9 | `PP-D3` | `experiments/track6/PP-D3_tail_defense_model_blend` | Cold 보정 후보 결합은 validation MdAPE `0.3370`까지 개선되지만 test MdAPE는 악화, p95 방어 후보로만 유지 |
| 9 | `PP-D4` | `experiments/track6/PP-D4_warm_three_model_blend` | Warm Huber + PP-L8 중심 가중 결합이 test MdAPE `0.2274 -> 0.1760`, MAPE `0.4952 -> 0.3293`으로 강하게 개선 |
| 9 | `PP-D5` | `experiments/track6/PP-D5_cold_three_model_blend` | Cold 3모델 결합은 validation 개선이 있으나 test MdAPE 악화로 단독 채택 보류 |
| 10 | `PP-E1` | `experiments/track6/PP-E1_warm_low_history_routing` | Warm 작가 이력 구간 라우팅이 test MdAPE `0.2274 -> 0.1856`, MAPE `0.4952 -> 0.3579`로 개선 |
| 10 | `PP-E2` | `experiments/track6/PP-E2_cold_meta_completeness_routing` | Cold 메타 조건 라우팅은 validation 개선이 test MdAPE로 재현되지 않아 보류 |
| 10 | `PP-E3` | `experiments/track6/PP-E3_extreme_size_routing` | Cold 극단 크기 라우팅은 p95 방어 효과는 있으나 test MdAPE/MAPE 악화로 보류 |
| 10 | `PP-E4` | `experiments/track6/PP-E4_material_classification_fallback_routing` | Cold 재료 분류 품질 라우팅은 p95 방어 후보이나 MdAPE 악화로 보류 |
| 10 | `PP-E5` | `experiments/track6/PP-E5_pred_price_risk_routing` | Cold 예측 가격대 라우팅은 validation 개선 대비 test 재현성이 약해 보류 |
| 11 | `PP-K1` | `experiments/track6/PP-K1_quantile_price_range_auxiliary` | Quantile q10/q50/q90 가격 범위 생성 완료. Cold q50은 test MAPE `1.4131 -> 1.2740`, p95 `4.8212 -> 4.2553`로 개선되나 범위 ratio 중앙값이 약 `5.1배`라 신뢰도/범위 표시용이 적합 |
| 11 | `PP-K2` | `experiments/track6/PP-K2_linear_baseline_comparison` | Warm 선형 기준선 비교에서 Huber가 Ridge/ElasticNet보다 validation/test MdAPE 모두 우위라 Warm Huber 유지 근거 강화 |
| 11 | `PP-K3` | `experiments/track6/PP-K3_similar_artwork_fallback` | Warm 유사 작품 fallback `min_rows=3`이 test MdAPE `0.2274 -> 0.2042`, MAPE `0.4952 -> 0.3499`로 개선. Cold fallback은 MdAPE 악화로 보류 |
| 11 | `PP-K4` | `experiments/track6/PP-K4_huber_catboost_residual_reference` | PP-L3 결과 참조로 대체. Huber+CatBoost residual은 PP-L8/PP-L9 순차 구조가 더 강하므로 별도 채택 보류 |
| 11 | `PP-K5` | `experiments/track6/PP-K5_huber_catboost_segment_reference` | PP-J3 결과 참조로 대체. Warm CatBoost leaf/artist-size 보정은 Huber 대비 MdAPE가 높아 보류 |
| 11 | `PP-K6` | `experiments/track6/PP-K6_oof_stacking_combination` | Cold CatBoost+LightGBM Ridge OOF stacking은 validation/test 모두 MdAPE 악화로 보류 |
| 11 | `PP-K7` | `experiments/track6/PP-K7_huber_quantile_risk_reference` | PP-L4 결과 참조. Quantile width 위험 구간 보정은 Cold MAPE/p95 방어에는 유효하나 MdAPE 기준 채택은 보류 |
| 11 | `PP-K8` | `experiments/track6/PP-K8_huber_quantile_weight_reference` | PP-L6 결과 참조. Warm 가중 앙상블은 개선 후보지만 PP-L8/PP-D4가 더 강함 |
| 11 | `PP-K9` | `experiments/track6/PP-K9_huber_residual_quantile_reference` | PP-L9 결과 참조. Warm Huber residual Quantile 구조는 강한 후보이나 PP-L8 대비 p95가 약함 |
| 11 | `PP-K10` | `experiments/track6/PP-K10_huber_quantile_catboost_routing_reference` | PP-L8 결과 참조. Warm PP-L8은 validation/test 모두 가장 강한 후보군으로 유지 |
| 12 | `PP-L1~PP-L9`, `PP-L7-*` | `experiments/track6/PP-L*` | 이전 실행 완료. Warm은 `PP-L8`, Cold는 `PP-L4/PP-A7` 계열이 강한 후보 |
| 13 | `PP-F1` | `experiments/track6/PP-F1_warm_price_range_policy` | Warm Huber 기준 80% 범위는 validation 포함률 `0.7996`, test 포함률 `0.7578`, 범위비 중앙값 `3.32배` |
| 13 | `PP-F2` | `experiments/track6/PP-F2_cold_price_range_policy` | Cold LightGBM 기준 80% 범위는 validation 포함률 `0.7999`, test 포함률 `0.6799`, 범위비 중앙값 `4.94배`로 test에서 과소 포함 |
| 13 | `PP-F3` | `experiments/track6/PP-F3_confidence_grade_policy` | Quantile width 기반 등급에서 Warm/Cold 모두 validation 저신뢰 구간 오차가 커져 등급 분리 근거 확인 |
| 13 | `PP-F4` | `experiments/track6/PP-F4_confidence_tiered_price_range` | 신뢰도별 차등 범위는 Warm test 포함률 `0.7974`로 안정적, Cold test 포함률 `0.7115`로 추가 보수화 필요 |
| 14 | `PP-G1~PP-G5` | `experiments/track6/PP-G*` | 기존 artist meta 후보 컬럼은 있으나 신규/보강 전시·수상·기관·갤러리 DB가 아니므로 모델 재학습은 보류. 필요한 신규 컬럼 목록과 coverage 산출물 생성 |
| 14 | `PP-H1~PP-H6` | `experiments/track6/PP-H*` | 네이버/구글/트렌드/SNS/검색 품질 지표가 로컬 split에 없어 실행 보류. 수집 필요 컬럼과 미실행 사유 산출물 생성 |
| 15 | `PP-I1` | `experiments/track6/PP-I1_huber_setting_tuning` | Warm Huber 설정 grid에서 `epsilon=1.35, alpha=0.001`이 validation 1위이나 baseline과 차이가 `0.00001` 수준이라 기본 설정 유지 가능 |
| 15 | `PP-I2` | `experiments/track6/PP-I2_catboost_setting_tuning` | Cold CatBoost 설정 grid는 validation 기준 baseline이 1위, test는 `depth7/lr0.03/l2=10`이 MdAPE만 소폭 우위이나 p95 악화로 기본 설정 유지 |
| 15 | `PP-I3` | `experiments/track6/PP-I3_correction_strength_final_check` | Warm tail 보정 강도 `0.50`은 test p95 개선 후보, Cold 보정 강도 후보는 test MdAPE 기준 보류 |
| 15 | `PP-I4` | `experiments/track6/PP-I4_routing_threshold_final_check` | Warm artist history 라우팅은 validation/test 모두 개선. Cold 라우팅은 p95 방어는 있으나 MdAPE 악화로 신뢰도 정책 후보 |
| 15 | `PP-I5` | `experiments/track6/PP-I5_final_integrated_candidate_validation` | Warm validation 1위는 `warm_pp_e1_routing`, test MdAPE 1위는 `warm_pp_d4_integrated`. Cold validation 1위는 `cold_pp_d3_tail_blend`, test MdAPE 1위는 baseline LightGBM |
| 16 | `PP-M1` | `experiments/track6/PP-M1_warm_artist_median_huber_residual` | Warm 작가 중앙값 기준선 + Huber residual은 validation/test MdAPE가 baseline보다 악화되어 단독 대체 보류. 다만 test p95는 `2.0130 -> 1.8968`로 일부 완화 |
| 16 | `PP-M2` | `experiments/track6/PP-M2_warm_artist_prior_huber` | artist prior + Huber는 validation MAPE/p95를 개선하지만 MdAPE는 악화. test도 MdAPE `0.2274 -> 0.2340` 수준으로 악화되어 PP-D4 대체 후보는 아님 |
| 16 | `PP-M3` | `experiments/track6/PP-M3_warm_artist_median_catboost_residual` | Warm 작가 기준선 + CatBoost residual은 MdAPE/MAPE가 악화되어 보류. p95 완화 가능성은 있으나 PP-D4보다 약함 |
| 17 | `PP-N1` | `experiments/track6/PP-N1_cold_quantile_lightgbm_conformal_range` | Cold Quantile LightGBM q50은 test MdAPE `0.4909 -> 0.4810`, MAPE `1.4131 -> 1.2743`, p95 `4.8212 -> 4.3168`로 개선. 다만 test range coverage는 `0.7260`으로 80% 목표 미달 |
| 17 | `PP-N2` | `experiments/track6/PP-N2_cold_catboost_quantile_range` | Cold CatBoost Quantile q50은 CatBoost baseline 대비 test MdAPE `0.4867 -> 0.4830`, MAPE `1.4803 -> 1.1514`, p95 `4.6329 -> 4.2659`로 개선. 점 예측보다 MAPE/tail 방어에 강한 후보 |
| 17 | `PP-N3` | `experiments/track6/PP-N3_cold_conformal_baseline_range` | Cold baseline conformal range는 90% 폭에서 test coverage `0.8061` 달성. 중앙 범위비 `8.38배`로 넓어 서비스 표시 정책에서 보수 범위 후보 |
| 18 | `PP-O1` | `experiments/track6/PP-O1_warm_explainable_nonlinear_hgb` | Warm HistGradientBoosting은 Huber 대비 validation/test 모두 크게 악화되어 Warm 설명가능 비선형 대체 모델로는 보류 |
| 18 | `PP-O2` | `experiments/track6/PP-O2_cold_explainable_nonlinear_hgb` | Cold HistGradientBoosting은 test MdAPE `0.4909 -> 0.4823`, MAPE `1.4131 -> 1.3411`, p95 `4.8212 -> 4.2852`로 개선. validation MdAPE는 baseline보다 약간 나빠 최종 채택 전 재검증 필요 |
| 19 | `PP-P1` | `experiments/track6/PP-P1_warm_cold_final_policy_routing` | 서비스 정책 후보로 Warm은 `PP-D4`, Cold 점 예측은 baseline LightGBM, Cold 위험 보조는 `PP-A7`로 정리. Cold `PP-A7`은 test MdAPE는 악화되지만 p95 `4.8212 -> 3.6424`로 방어 효과가 큼 |
| 19 | `PP-P2` | `experiments/track6/PP-P2_quantile_width_model_routing` | Quantile width 기반 모델 선택은 Cold test MdAPE `0.4909 -> 0.4779`, MAPE `1.4131 -> 1.3428`, p95 `4.8212 -> 4.3466`으로 개선. Warm은 PP-D4 단독보다 약해 Warm 라우팅 후보로는 보류 |
| 19 | `PP-P3` | `experiments/track6/PP-P3_service_display_policy_validation` | 서비스 표시 정책 통합 검증에서 Cold는 `PP-P2` 라우팅을 참고 가격 후보로, `PP-N3` 90% conformal range를 보수 범위 후보로 분리하는 방향이 타당. Warm은 PP-D4 단독 유지가 더 적합 |
| 20 | `PP-Q1` | `experiments/track6/PP-Q1_cold_width_routing_with_catboost_quantile` | CatBoost Quantile을 포함한 width 라우팅은 test MdAPE `0.4779`, MAPE 목적 라우팅은 MAPE `1.2744`, p95 `4.2723`까지 개선. PP-P2 대비 p95/MAPE는 일부 개선되나 MdAPE 개선폭은 제한적 |
| 20 | `PP-Q2` | `experiments/track6/PP-Q2_cold_weighted_blend_custom` | Cold 후보 4종 가중 결합에서 MAPE 목적 가중치(`Quantile LGBM 0.5 + CatBoost Quantile 0.5`)가 test MAPE `1.4131 -> 1.1797`, p95 `4.8212 -> 3.7925`로 크게 개선. MdAPE는 `0.4811`로 baseline보다 개선 |
| 20 | `PP-Q3` | `experiments/track6/PP-Q3_cold_point_range_joint_policy` | 점 예측과 범위를 분리한 joint policy에서 point는 `PP-Q2 MAPE objective`, range는 `PP-N3 90% conformal`이 test coverage `0.8061`을 달성. 점 예측은 MAPE/p95 방어, 범위는 보수 표시용으로 분리하는 정책이 타당 |
| 20 | `PP-Q4` | `experiments/track6/PP-Q4_probabilistic_model_candidate_check` | NGBoost는 현재 로컬 환경에 설치되어 있지 않아 실행하지 않음. 확률분포 예측 모델 후보로는 추후 의존성 설치 후 재검증 가능 |
| 21 | `PP-R1` | `experiments/track6/PP-R1_cold_objective_constrained_fine_blend` | Cold fine blend는 validation에서 `PP-A7` 계층형 보정을 과도하게 선택해 test MdAPE가 `0.4894~0.5030`으로 악화. 촘촘한 가중치 자체는 PP-Q2보다 낫지 않아 보류 |
| 21 | `PP-R2` | `experiments/track6/PP-R2_cold_ensemble_then_residual_stage_calibration` | `PP-Q2` 앙상블 후 residual 단계 보정은 test p95 `3.7925 -> 3.4226`, MAPE `1.1797 -> 1.1748`로 tail 방어는 개선됐지만 MdAPE가 `0.4811 -> 0.4933`으로 악화되어 보수적 위험 방어 후보로만 유지 |
| 21 | `PP-R3` | `experiments/track6/PP-R3_cold_risk_threshold_routing_search` | Quantile width threshold 라우팅 확장은 test MdAPE/MAPE가 `PP-P2`와 `PP-Q2`보다 약해 보류. validation에서 강한 `PP-A7` 선택이 test로 재현되지 않는 문제가 확인됨 |
| 21 | `PP-R4` | `experiments/track6/PP-R4_cold_validation_meta_calibration` | Cold validation meta 보정 중 `huber_meta_component_range_clipped`가 test p95 `3.4131`로 현재 가장 낮음. MdAPE `0.4796`, MAPE `1.2148`로 PP-Q2보다 MAPE는 약하지만 p95 방어가 더 강한 후보 |
| 21 | `PP-R5` | `experiments/track6/PP-R5_warm_final_candidate_residual_stabilization` | Warm `PP-D4` 최종 후보에 약한 residual 안정화를 적용해 test MdAPE `0.1760 -> 0.1707`, MAPE `0.3293 -> 0.3278`, p95 `1.1248 -> 1.1107`로 추가 개선. Warm 최종 후보 갱신 가능 |
| 22 | `PP-S1` | `experiments/track6/PP-S1_cold_catboost_first_huber_residual` | Cold CatBoost Quantile 선행 후 Huber residual 안정화가 CatBoost Quantile 단독 MdAPE `0.4830`, p95 `4.2659`에서 MdAPE 최저 `0.4744`, p95 `3.4731`까지 개선. p95 우선 설정은 MdAPE `0.4765`, p95 `3.2824`로 더 강함. CatBoost 먼저 쓰는 순서 변경이 유효 |
| 22 | `PP-S2` | `experiments/track6/PP-S2_cold_quantile_lgb_first_catboost_residual` | Quantile LightGBM 선행 후 residual 보정은 MdAPE `0.4765`, p95 `3.5543`까지 개선되지만 `PP-S1/PP-S4`보다 약함. Quantile 선행 구조는 가능성이 있으나 최종 후보는 아님 |
| 22 | `PP-S3` | `experiments/track6/PP-S3_cold_lightgbm_objective_custom` | LightGBM objective 커스텀에서 `huber` objective는 MdAPE `0.4768`, `mape` objective는 MAPE `1.2217`, p95 `3.7901`로 기본 regression보다 개선. 목적함수 커스텀은 후보 확장 근거가 있음 |
| 22 | `PP-S4` | `experiments/track6/PP-S4_cold_crossfit_meta_stacking` | Cold cross-fitted Huber meta stacking이 test MdAPE `0.4765`, MAPE `1.2079`, p95 `3.2827`로 p95 방어와 대표 정확도 균형이 강함. validation 내부 교차검증에서도 Huber meta가 가장 안정적 |
| 22 | `PP-S5` | `experiments/track6/PP-S5_cold_objective_policy_comparison` | 목적별 후보 비교에서 validation 기준 MdAPE 우선은 `PP-S2`, MAPE/p95 guard는 `PP-R4`로 선택됨. 다만 test 실제 최고 MdAPE는 `PP-S1 CatBoost 선행 + Huber residual`의 `0.4744`, p95 최저권은 `PP-S1/PP-S4`의 약 `3.282`로 확인되어 validation 선택과 test 최강 후보를 분리 보고해야 함 |
| 23 | `PP-T1` | `experiments/track6/PP-T1_warm_candidate_fine_blend` | Warm 후보 fine blend가 `PP-R5`를 추가 개선. test MdAPE `0.1707 -> 0.1621`, MAPE `0.3278 -> 0.3044`, p95 `1.1107 -> 1.0335`. p95 우선 후보는 MdAPE `0.1668`, p95 `0.9580`으로 tail 방어가 더 강함 |
| 23 | `PP-T2` | `experiments/track6/PP-T2_warm_crossfit_meta_stacking` | Warm cross-fitted Huber meta는 test MdAPE `0.1705`, MAPE `0.2916`, p95 `0.9582`로 MAPE/p95 방어가 가장 강함. 단, MdAPE는 PP-T1보다 약간 높음 |
| 23 | `PP-T3` | `experiments/track6/PP-T3_warm_r5_second_pass_residual_stabilization` | `PP-R5` 2차 residual 안정화는 MdAPE `0.1707 -> 0.1644`로 개선되지만 MAPE/p95는 PP-T1/T2보다 약함. 단순 2차 보정만으로도 개선 여지는 확인 |
| 23 | `PP-T4` | `experiments/track6/PP-T4_warm_objective_policy_comparison` | Warm 목적별 정책 비교에서 validation 기준 MdAPE 우선은 `PP-T1 mdape`, MAPE 우선은 `PP-T2 huber`, p95 우선은 `PP-T1 p95`로 선택됨. test 기준으로는 MdAPE/MAPE 균형은 `PP-T1 mape`, p95 방어는 `PP-T1 mdape` 또는 `PP-T2 huber`가 강함 |
| 24 | `PP-U1` | `experiments/track6/PP-U1_warm_huber_feature_swap` | Warm Huber 피처 교환에서 validation 1위는 `artist_size_depth` MdAPE `0.2093`, test 1위는 `full_plus_generated_buckets` MdAPE `0.2131`. 생성 bucket 확장은 test에서 기준 MdAPE `0.2274 -> 0.2131`, p95 `2.0130 -> 1.8591`로 개선되지만 validation 1위가 달라 즉시 교체보다 후속 조합 후보로 유지 |
| 24 | `PP-U2` | `experiments/track6/PP-U2_warm_catboost_feature_swap` | Warm CatBoost는 피처 변경으로 CatBoost baseline보다 개선되지만 test 최선 MdAPE가 `0.3125`로 Warm Huber/PP-T 후보보다 약함. Warm CatBoost는 주모델보다 보조 residual/segment 후보로 유지 |
| 24 | `PP-U3` | `experiments/track6/PP-U3_cold_lightgbm_feature_swap` | Cold LightGBM 피처 교환에서 validation 1위는 `support_shape_combo` MdAPE `0.3834`, test 1위는 `medium_size_combo` MdAPE `0.4803`. 기준 LightGBM test MdAPE `0.4909` 대비 개선되어 `support_shape`/`medium_size` 계열을 후속 조합 후보로 유지 |
| 24 | `PP-U4` | `experiments/track6/PP-U4_cold_catboost_feature_swap` | Cold CatBoost는 validation 기준 기존 `base_medium_shape`가 최선. test에서는 `lightgbm_swap_support_size`가 MdAPE `0.4867 -> 0.4835`, p95 `4.6329 -> 4.4439`로 개선됐지만 validation 근거가 약해 즉시 교체는 보류 |

## 2. 현재까지의 핵심 판단

- Warm은 기본 Huber가 이미 안정적이어서 단순 residual 보정은 조심해야 한다.
- Warm에서 명확한 후속 후보는 `PP-L8 Quantile -> Huber -> CatBoost residual`이다.
- Warm Huber의 단순 전체 보정보다 `PP-J1`처럼 예측 가격대와 크기 구간을 함께 보는 tail 보정이 더 적합하다.
- Cold는 CatBoost 원 모델보다 LightGBM 원 모델이 현재 split 기준 우수하지만, CatBoost는 leaf/medium-shape/계층형 보정으로 크게 개선된다.
- Cold 기본 residual 보정 후보 중 현재 가장 강한 것은 `PP-J4` leaf coverage 보정, `PP-A7` 계층형 보정, `PP-J6` LightGBM tail 보정이다.
- PP-B 남은 오차 모델은 validation 개선만 보고 채택하기 어렵다. test 재현성까지 보면 단순 2단계 residual 모델보다 segment 기반 보정이 더 안정적이다.
- PP-C 직선/비선형 재보정은 validation에 잘 맞지만 test MdAPE 재현성이 부족하다. 다만 `PP-C5`의 Warm tail 보정 강도 조정은 실제 후보로 유지할 수 있다.
- PP-D/PP-E에서 Warm은 PP-L8 중심 결합과 작가 이력 라우팅이 강한 후보로 확인됐다. Cold는 라우팅/결합이 p95 방어에는 도움이 되지만 MdAPE 재현성이 약해 최종 채택 전 신뢰도 정책으로 분리하는 편이 안전하다.
- PP-K에서 Warm Huber 유지 근거가 강화됐고, Warm 유사 작품 fallback이 추가 후보로 확인됐다. Cold Quantile은 정확도 후보보다 가격 범위/신뢰도 표시 입력값으로 쓰는 것이 적합하다.
- PP-F에서 Warm은 80% 전후 가격 범위와 신뢰도 등급 정책을 서비스 표시 후보로 둘 수 있다. Cold는 validation 기준 범위가 test에서 덜 포함되므로 단일 가격 표시보다 넓은 범위와 낮은 신뢰도 문구가 필요하다.
- PP-G/PP-H는 현재 신규 외부/검색 데이터가 없어 성능 실험으로 진행하지 않았다. 기존 artist meta 재사용은 문서 기준상 중복이므로 신규 데이터 수집 후 재실행해야 한다.
- PP-I 최종 통합 기준으로 Warm은 후처리/결합 후보가 명확히 개선된다. 운영 1차 후보는 validation 원칙을 따르면 `warm_pp_e1_routing`, test 재현성까지 보면 `warm_pp_d4_integrated`가 가장 강하다.
- PP-I 최종 통합 기준으로 Cold는 validation 보정 후보가 test MdAPE로 재현되지 않는다. 정확도 1차 후보는 baseline LightGBM 유지, p95 방어/신뢰도 표시는 `cold_pp_d3_tail_blend` 또는 `cold_pp_a7_hierarchical`을 보조 정책으로 두는 편이 안전하다.
- PP-A6은 현재 feature split에 메타 완성도 컬럼이 없어, 신규 메타 피처가 들어오기 전까지는 보류가 맞다.
- PP-M 추가 실험 결과, Warm은 작가 기준선을 별도로 분리한 단순 계층형/artist prior 구조가 PP-D4/PP-L8보다 약했다. Warm은 현재로서는 PP-D4 또는 PP-E1 중심 유지가 맞다.
- PP-N 추가 실험 결과, Cold는 점 예측보다 Quantile/Conformal 기반 분포/범위 예측으로 개선 여지가 있다. 특히 Quantile LightGBM q50은 test MdAPE/MAPE/p95를 모두 개선했다.
- PP-N2까지 확인한 결과, CatBoost도 Quantile 손실로 쓰면 Cold MAPE와 p95 방어가 좋아진다. CatBoost는 점 예측 주모델보다 Cold 분포/위험 보조모델로 쓰는 방향이 더 적합하다.
- PP-O 추가 실험 결과, 설명 가능한 비선형 후보는 Warm에서는 부적합했지만 Cold에서는 test 기준 개선 가능성이 있다. 다만 validation 선택 원칙상 바로 채택하지 않고 재검증 후보로 둔다.
- PP-P 추가 실험 결과, 서비스 정책은 Warm 점 예측 `PP-D4`, Cold 점 예측/참고가는 `PP-P2` 라우팅 또는 baseline LightGBM, Cold 위험/범위 보조는 `PP-A7`, `PP-N1/N2`, `PP-N3` conformal range로 분리하는 방향이 가장 명확하다.
- PP-Q 추가 실험 결과, Cold는 모델 조합 + 모델별 커스텀이 실제로 추가 개선을 만들었다. 특히 `PP-Q2`의 Quantile LightGBM + CatBoost Quantile 50:50 가중 결합은 MAPE와 p95 방어가 가장 강하다.
- 다만 PP-Q2 MAPE 목적 후보는 MdAPE 최저 후보는 아니므로, 서비스에서는 `대표 정확도 우선`이면 `PP-P2`, `큰 오차/MAPE 방어 우선`이면 `PP-Q2`로 목적을 분리해 보고하는 것이 맞다.
- PP-R 추가 실험 결과, Warm은 `PP-D4` 이후에도 약한 segment residual 보정으로 추가 개선이 가능했다. 현재 Warm 최고 후보는 `PP-R5 warm_residual_stabilized_p95_guarded`이다.
- Cold는 더 촘촘한 fine blend나 threshold 라우팅보다 `PP-R4`의 Huber meta + component range clipping이 p95 방어에 가장 강했다. 단, MdAPE 최저는 여전히 `PP-P2`, MAPE 최저는 `PP-Q2`, p95 최저는 `PP-R4`로 목적별 후보가 갈린다.
- PP-S 추가 실험 결과, Cold는 모델 순서 변경과 정식화된 meta stacking에서 추가 개선이 확인됐다. 특히 `PP-S1`은 CatBoost Quantile을 먼저 쓰고 Huber residual로 안정화하는 순서가 유효했고, `PP-S4`는 cross-fitted Huber meta stacking으로 p95 방어와 안정성을 보강했다.
- Cold 목적별 최신 후보는 `MdAPE 최저` 기준 `PP-S1 n2_catboost_quantile_huber_cap0.2_s1`, `p95 방어 + 균형` 기준 `PP-S1 n2_catboost_quantile_huber_cap0.5_s1` 또는 `PP-S4 huber_crossfit`, `MAPE 단독` 기준 `PP-S1 약한 보정` 또는 `PP-Q2`, `서비스 보수 방어` 기준 `PP-S4/PP-R4`로 정리할 수 있다.
- PP-T 추가 실험 결과, Warm도 `PP-R5` 이후 추가 개선 가능성이 확인됐다. Warm 최종 후보는 단일 지표 기준으로는 `PP-T1 fine_blend_mape_guarded`, p95/범위 방어까지 고려하면 `PP-T1 fine_blend_mdape` 또는 `PP-T2 huber_crossfit_component_range_clipped`를 함께 보고해야 한다.
- PP-U 피처 교환 결과, Warm Huber는 생성 bucket 확장으로 test 개선 가능성이 확인됐지만 validation 선택과 test 1위가 달라 즉시 기준 피처셋 교체는 보류한다. 대신 `full_plus_generated_buckets`를 Warm PP-T 후속 조합 입력 후보로 둔다.
- PP-U 피처 교환 결과, Cold LightGBM은 `support_shape_combo`와 `medium_size_combo`가 기준 피처셋보다 개선 가능성을 보였다. Cold 후속 조합/순차 학습에서는 LightGBM 입력 피처를 `base_support_size`로만 고정하지 않고 medium/shape/size 조합 후보를 추가할 가치가 있다.
- PP-U 피처 교환 결과, Cold CatBoost는 validation 기준으로 기존 `base_medium_shape` 유지가 안전하다. 다만 test에서 `base_support_size` 교환이 일부 개선되어 CatBoost Quantile 또는 PP-S 순차 구조 입력 후보로만 유지한다.

## 3. 다음 작업

| 순서 | 작업 | 실행 이유 |
|---:|---|---|
| 1 | 최종 후보 의사결정 문서 업데이트 | PP-S/PP-T/PP-U 추가 결과를 Warm/Cold 최종 판단에 반영 |
| 2 | Warm 목적별 후보 정리 | MdAPE/MAPE 균형 후보 `PP-T1 mape`, p95 후보 `PP-T1 mdape` 또는 `PP-T2 huber`, PP-U1 생성 bucket 확장 후보를 함께 비교 |
| 3 | Cold 목적별 후보 정리 | MdAPE 후보 `PP-S1`, p95/균형 후보 `PP-S1/PP-S4`, MAPE 단독 후보 `PP-S1 약한 보정/PP-Q2`, PP-U3 LightGBM 피처 교환 후보, 보수 범위 후보 `PP-N3 90% conformal`로 분리 |
| 4 | PP-U 후보 후속 조합 여부 결정 | Warm `full_plus_generated_buckets`, Cold LightGBM `medium_size/support_shape`, Cold CatBoost `support_size` 교환 후보를 PP-T/PP-S 계열 입력으로 추가할지 판단 |
| 5 | 서비스 API 정책 문서 업데이트 | Warm/Cold route별 `model_policy`, `postprocessing_policy`, `display_policy`를 실험 결과와 일치 |
| 6 | 신규 외부 데이터 수집 여부 결정 | PP-G/PP-H 재실행 여부를 결정하기 위한 수집 범위 확정 |
