# Warm 검색 피처 기반 잔차 보정 검증

- 실험 ID: `PP-H29`
- 실행 시각: 2026-06-03T16:59:08
- 목적: Warm 최종 후보 예측값에 외부 검색 피처별 잔차 보정을 적용했을 때, 이미 강한 Warm 모델도 추가 개선 여지가 있는지 확인한다.
- 보정 학습 기준: Warm validation split의 `actual_log - pred_log` 중앙값
- 적용 기준: validation에서 만든 보정값을 validation/test에 동일 적용
- 보정 강도: log 가격 기준 `±0.05`, `±0.10`, `±0.15`

## 검색 피처 커버리지

| split | row_n | unique_artist_n | search_covered_row_n | search_covered_row_rate | search_covered_artist_n |
| --- | --- | --- | --- | --- | --- |
| test | 607 | 205 | 607 | 1.000000 | 205 |
| validation | 519 | 177 | 489 | 0.942197 | 162 |

## 기준 후보 test 성능

| experiment_id | candidate | base_candidate | feature | split | policy | cap | note | RMSE_log | MdAPE | MAPE | p95_APE | Within_30 | Within_50 | feature_label |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-H29 | baseline__v8_single_mdape | deployment_single_mdape | none | test | baseline_from_pp_v8 | 0.000000 | V8 단일 MdAPE 후보 | 0.421978 | 0.162111 | 0.304424 | 1.033520 | 0.711697 | 0.836903 |  |
| PP-H29 | baseline__v8_compact_mape | compact_blend_mape_guarded | none | test | baseline_from_pp_v8 | 0.000000 | V8 compact blend MAPE 방어 후보 | 0.402820 | 0.163169 | 0.281619 | 0.931104 | 0.736409 | 0.859967 |  |
| PP-H29 | baseline__v8_compact_mdape | compact_blend_mdape | none | test | baseline_from_pp_v8 | 0.000000 | V8 compact blend MdAPE 후보 | 0.406662 | 0.163532 | 0.286770 | 0.919044 | 0.706755 | 0.863262 |  |

## validation 상위 후보

| experiment_id | candidate | base_candidate | feature | split | policy | cap | note | RMSE_log | MdAPE | MAPE | p95_APE | Within_30 | Within_50 | feature_label |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-H29 | h29_v8_compact_mdape_homonym_median_cap0p05 | compact_blend_mdape | search_homonym_risk_ratio | validation | validation_segment_median_residual_correction | 0.050000 | 동명이인 위험 비중 구간별 Warm validation 잔차 중앙값 보정 | 0.373122 | 0.138808 | 0.252295 | 0.724061 | 0.724470 | 0.880539 | 동명이인 위험 비중 |
| PP-H29 | h29_v8_compact_mdape_homonym_median_cap0p1 | compact_blend_mdape | search_homonym_risk_ratio | validation | validation_segment_median_residual_correction | 0.100000 | 동명이인 위험 비중 구간별 Warm validation 잔차 중앙값 보정 | 0.373122 | 0.138808 | 0.252295 | 0.724061 | 0.724470 | 0.880539 | 동명이인 위험 비중 |
| PP-H29 | h29_v8_compact_mdape_homonym_median_cap0p15 | compact_blend_mdape | search_homonym_risk_ratio | validation | validation_segment_median_residual_correction | 0.150000 | 동명이인 위험 비중 구간별 Warm validation 잔차 중앙값 보정 | 0.373122 | 0.138808 | 0.252295 | 0.724061 | 0.724470 | 0.880539 | 동명이인 위험 비중 |
| PP-H29 | h29_v8_compact_mdape_quality_median_cap0p05 | compact_blend_mdape | search_quality_score | validation | validation_segment_median_residual_correction | 0.050000 | 검색 품질 점수 구간별 Warm validation 잔차 중앙값 보정 | 0.372852 | 0.141216 | 0.252515 | 0.714987 | 0.726397 | 0.878613 | 검색 품질 점수 |
| PP-H29 | h29_v8_compact_mdape_quality_median_cap0p1 | compact_blend_mdape | search_quality_score | validation | validation_segment_median_residual_correction | 0.100000 | 검색 품질 점수 구간별 Warm validation 잔차 중앙값 보정 | 0.372852 | 0.141216 | 0.252515 | 0.714987 | 0.726397 | 0.878613 | 검색 품질 점수 |
| PP-H29 | h29_v8_compact_mdape_quality_median_cap0p15 | compact_blend_mdape | search_quality_score | validation | validation_segment_median_residual_correction | 0.150000 | 검색 품질 점수 구간별 Warm validation 잔차 중앙값 보정 | 0.372852 | 0.141216 | 0.252515 | 0.714987 | 0.726397 | 0.878613 | 검색 품질 점수 |
| PP-H29 | baseline__v8_compact_mdape | compact_blend_mdape | none | validation | baseline_from_pp_v8 | 0.000000 | V8 compact blend MdAPE 후보 | 0.373915 | 0.142265 | 0.256939 | 0.757757 | 0.718690 | 0.876686 |  |
| PP-H29 | h29_v8_compact_mdape_social_blog_median_cap0p05 | compact_blend_mdape | source_group_social_blog_ratio | validation | validation_segment_median_residual_correction | 0.050000 | 블로그/소셜 출처 비중 구간별 Warm validation 잔차 중앙값 보정 | 0.373784 | 0.143195 | 0.254149 | 0.730269 | 0.726397 | 0.880539 | 블로그/소셜 출처 비중 |
| PP-H29 | h29_v8_compact_mdape_social_blog_median_cap0p1 | compact_blend_mdape | source_group_social_blog_ratio | validation | validation_segment_median_residual_correction | 0.100000 | 블로그/소셜 출처 비중 구간별 Warm validation 잔차 중앙값 보정 | 0.373784 | 0.143195 | 0.254149 | 0.730269 | 0.726397 | 0.880539 | 블로그/소셜 출처 비중 |
| PP-H29 | h29_v8_compact_mdape_social_blog_median_cap0p15 | compact_blend_mdape | source_group_social_blog_ratio | validation | validation_segment_median_residual_correction | 0.150000 | 블로그/소셜 출처 비중 구간별 Warm validation 잔차 중앙값 보정 | 0.373784 | 0.143195 | 0.254149 | 0.730269 | 0.726397 | 0.880539 | 블로그/소셜 출처 비중 |
| PP-H29 | h29_v8_compact_mape_social_blog_median_cap0p05 | compact_blend_mape_guarded | source_group_social_blog_ratio | validation | validation_segment_median_residual_correction | 0.050000 | 블로그/소셜 출처 비중 구간별 Warm validation 잔차 중앙값 보정 | 0.371406 | 0.148805 | 0.253041 | 0.765287 | 0.728324 | 0.888247 | 블로그/소셜 출처 비중 |
| PP-H29 | h29_v8_compact_mape_social_blog_median_cap0p1 | compact_blend_mape_guarded | source_group_social_blog_ratio | validation | validation_segment_median_residual_correction | 0.100000 | 블로그/소셜 출처 비중 구간별 Warm validation 잔차 중앙값 보정 | 0.371406 | 0.148805 | 0.253041 | 0.765287 | 0.728324 | 0.888247 | 블로그/소셜 출처 비중 |

## test 상위 후보

| experiment_id | candidate | base_candidate | feature | split | policy | cap | note | RMSE_log | MdAPE | MAPE | p95_APE | Within_30 | Within_50 | feature_label |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-H29 | h29_v8_compact_mape_gallery_median_cap0p05 | compact_blend_mape_guarded | source_group_gallery_museum_ratio | test | validation_segment_median_residual_correction | 0.050000 | 갤러리/미술관 출처 비중 구간별 Warm validation 잔차 중앙값 보정 | 0.402829 | 0.161699 | 0.280877 | 0.930942 | 0.731466 | 0.863262 | 갤러리/미술관 출처 비중 |
| PP-H29 | h29_v8_compact_mape_gallery_median_cap0p1 | compact_blend_mape_guarded | source_group_gallery_museum_ratio | test | validation_segment_median_residual_correction | 0.100000 | 갤러리/미술관 출처 비중 구간별 Warm validation 잔차 중앙값 보정 | 0.402829 | 0.161699 | 0.280877 | 0.930942 | 0.731466 | 0.863262 | 갤러리/미술관 출처 비중 |
| PP-H29 | h29_v8_compact_mape_gallery_median_cap0p15 | compact_blend_mape_guarded | source_group_gallery_museum_ratio | test | validation_segment_median_residual_correction | 0.150000 | 갤러리/미술관 출처 비중 구간별 Warm validation 잔차 중앙값 보정 | 0.402829 | 0.161699 | 0.280877 | 0.930942 | 0.731466 | 0.863262 | 갤러리/미술관 출처 비중 |
| PP-H29 | h29_v8_compact_mape_market_median_cap0p05 | compact_blend_mape_guarded | source_group_market_ratio | test | validation_segment_median_residual_correction | 0.050000 | 시장/경매 출처 비중 구간별 Warm validation 잔차 중앙값 보정 | 0.402829 | 0.161699 | 0.280877 | 0.930942 | 0.731466 | 0.863262 | 시장/경매 출처 비중 |
| PP-H29 | h29_v8_compact_mape_market_median_cap0p1 | compact_blend_mape_guarded | source_group_market_ratio | test | validation_segment_median_residual_correction | 0.100000 | 시장/경매 출처 비중 구간별 Warm validation 잔차 중앙값 보정 | 0.402829 | 0.161699 | 0.280877 | 0.930942 | 0.731466 | 0.863262 | 시장/경매 출처 비중 |
| PP-H29 | h29_v8_compact_mape_market_median_cap0p15 | compact_blend_mape_guarded | source_group_market_ratio | test | validation_segment_median_residual_correction | 0.150000 | 시장/경매 출처 비중 구간별 Warm validation 잔차 중앙값 보정 | 0.402829 | 0.161699 | 0.280877 | 0.930942 | 0.731466 | 0.863262 | 시장/경매 출처 비중 |
| PP-H29 | h29_v8_compact_mape_name_match_median_cap0p05 | compact_blend_mape_guarded | search_name_match_ratio | test | validation_segment_median_residual_correction | 0.050000 | 작가명 일치 비중 구간별 Warm validation 잔차 중앙값 보정 | 0.402829 | 0.161699 | 0.280877 | 0.930942 | 0.731466 | 0.863262 | 작가명 일치 비중 |
| PP-H29 | h29_v8_compact_mape_name_match_median_cap0p1 | compact_blend_mape_guarded | search_name_match_ratio | test | validation_segment_median_residual_correction | 0.100000 | 작가명 일치 비중 구간별 Warm validation 잔차 중앙값 보정 | 0.402829 | 0.161699 | 0.280877 | 0.930942 | 0.731466 | 0.863262 | 작가명 일치 비중 |
| PP-H29 | h29_v8_compact_mape_name_match_median_cap0p15 | compact_blend_mape_guarded | search_name_match_ratio | test | validation_segment_median_residual_correction | 0.150000 | 작가명 일치 비중 구간별 Warm validation 잔차 중앙값 보정 | 0.402829 | 0.161699 | 0.280877 | 0.930942 | 0.731466 | 0.863262 | 작가명 일치 비중 |
| PP-H29 | h29_v8_compact_mape_provider_cov_median_cap0p05 | compact_blend_mape_guarded | provider_coverage_count | test | validation_segment_median_residual_correction | 0.050000 | 검색 제공자 커버리지 수 구간별 Warm validation 잔차 중앙값 보정 | 0.402829 | 0.161699 | 0.280877 | 0.930942 | 0.731466 | 0.863262 | 검색 제공자 커버리지 수 |
| PP-H29 | h29_v8_compact_mape_provider_cov_median_cap0p1 | compact_blend_mape_guarded | provider_coverage_count | test | validation_segment_median_residual_correction | 0.100000 | 검색 제공자 커버리지 수 구간별 Warm validation 잔차 중앙값 보정 | 0.402829 | 0.161699 | 0.280877 | 0.930942 | 0.731466 | 0.863262 | 검색 제공자 커버리지 수 |
| PP-H29 | h29_v8_compact_mape_provider_cov_median_cap0p15 | compact_blend_mape_guarded | provider_coverage_count | test | validation_segment_median_residual_correction | 0.150000 | 검색 제공자 커버리지 수 구간별 Warm validation 잔차 중앙값 보정 | 0.402829 | 0.161699 | 0.280877 | 0.930942 | 0.731466 | 0.863262 | 검색 제공자 커버리지 수 |

## 해석

- validation 최상위 후보: `h29_v8_compact_mdape_homonym_median_cap0p05` / MdAPE `0.138808` / MAPE `0.252295`
- test 최상위 후보: `h29_v8_compact_mape_gallery_median_cap0p05` / MdAPE `0.161699` / MAPE `0.280877`
- 이 실험은 검색 피처를 모델 학습 피처로 직접 투입하는 것이 아니라, Warm 예측값이 남긴 오차를 검색 피처 구간별로 보정하는 후처리 실험이다.
- 따라서 효과가 있으면 “Warm 모델의 기본 가격 구조는 유지하되, 외부 인지도/출처 성격에 따라 반복되는 잔차만 작게 조정할 수 있다”는 근거가 된다.
- 반대로 test 개선이 없거나 validation만 좋아지면, Warm에서는 검색 피처가 이미 작가/크기/작품 이력 피처에 상당 부분 흡수됐거나 평가셋 커버리지가 아직 부족하다는 의미다.

## 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/correction_maps.csv`
- `outputs/segment_info.csv`
- `reports/result_report.html`
