# Warm MAPE 최적화 조합 실험

- 실험 ID: `PP-WMAPE`
- 실행 시각: 2026-06-03T19:02:00
- 목적: Warm에서 MAPE를 최우선으로 줄이는 조합, 라우팅, 구간 보정, 잔차 보정 후보를 한 번에 비교한다.
- 원칙: 모든 조합 선택과 보정값은 Warm validation에서 만들고 Warm test에 그대로 적용한다.
- 현재 비교 기준: `h29__h29_v8_compact_mape_gallery_median_cap0p05` / test MAPE `0.280877`

## 결론 요약

- test MAPE 최상위 후보: `wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_quantile_width`
- test MAPE: `0.267365`
- test MdAPE: `0.163788`
- test p95_APE: `0.832172`
- 기존 기준 대비 MAPE 개선폭: `0.013512`

## 기존 Warm 후보 test MAPE 순위

| candidate | policy | split | MAPE | MdAPE | p95_APE | RMSE_log | Within_30 | Within_50 | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| h29__h29_v8_compact_mape_gallery_median_cap0p05 | W-MAPE-01_existing_source | test | 0.280877 | 0.161699 | 0.930942 | 0.402829 | 0.731466 | 0.863262 | 기존 Warm 예측 산출물 |
| h29__h29_v8_compact_mape_gallery_median_cap0p1 | W-MAPE-01_existing_source | test | 0.280877 | 0.161699 | 0.930942 | 0.402829 | 0.731466 | 0.863262 | 기존 Warm 예측 산출물 |
| h29__h29_v8_compact_mape_market_median_cap0p05 | W-MAPE-01_existing_source | test | 0.280877 | 0.161699 | 0.930942 | 0.402829 | 0.731466 | 0.863262 | 기존 Warm 예측 산출물 |
| h29__h29_v8_compact_mape_name_match_median_cap0p05 | W-MAPE-01_existing_source | test | 0.280877 | 0.161699 | 0.930942 | 0.402829 | 0.731466 | 0.863262 | 기존 Warm 예측 산출물 |
| h29__h29_v8_compact_mape_provider_cov_median_cap0p05 | W-MAPE-01_existing_source | test | 0.280877 | 0.161699 | 0.930942 | 0.402829 | 0.731466 | 0.863262 | 기존 Warm 예측 산출물 |
| h29__h29_v8_compact_mape_quality_median_cap0p05 | W-MAPE-01_existing_source | test | 0.281202 | 0.166693 | 0.915231 | 0.401421 | 0.741351 | 0.861614 | 기존 Warm 예측 산출물 |
| h29__h29_v8_compact_mape_quality_median_cap0p1 | W-MAPE-01_existing_source | test | 0.281202 | 0.166693 | 0.915231 | 0.401421 | 0.741351 | 0.861614 | 기존 Warm 예측 산출물 |
| h29__h29_v8_compact_mape_quality_median_cap0p15 | W-MAPE-01_existing_source | test | 0.281202 | 0.166693 | 0.915231 | 0.401421 | 0.741351 | 0.861614 | 기존 Warm 예측 산출물 |
| h29__h29_v8_compact_mape_news_median_cap0p05 | W-MAPE-01_existing_source | test | 0.281483 | 0.167083 | 0.928810 | 0.403997 | 0.736409 | 0.859967 | 기존 Warm 예측 산출물 |
| h29__h29_v8_compact_mape_news_median_cap0p1 | W-MAPE-01_existing_source | test | 0.281483 | 0.167083 | 0.928810 | 0.403997 | 0.736409 | 0.859967 | 기존 Warm 예측 산출물 |
| h29__h29_v8_compact_mape_news_median_cap0p15 | W-MAPE-01_existing_source | test | 0.281483 | 0.167083 | 0.928810 | 0.403997 | 0.736409 | 0.859967 | 기존 Warm 예측 산출물 |
| v8__compact_blend_mape_guarded | W-MAPE-01_existing_source | test | 0.281619 | 0.163169 | 0.931104 | 0.402820 | 0.736409 | 0.859967 | 기존 Warm 예측 산출물 |
| h29__h29_v8_compact_mdape_news_median_cap0p05 | W-MAPE-01_existing_source | test | 0.281925 | 0.162848 | 0.885008 | 0.406652 | 0.718287 | 0.869852 | 기존 Warm 예측 산출물 |
| h29__h29_v8_compact_mdape_news_median_cap0p1 | W-MAPE-01_existing_source | test | 0.281925 | 0.162848 | 0.885008 | 0.406652 | 0.718287 | 0.869852 | 기존 Warm 예측 산출물 |
| h29__h29_v8_compact_mdape_news_median_cap0p15 | W-MAPE-01_existing_source | test | 0.281925 | 0.162848 | 0.885008 | 0.406652 | 0.718287 | 0.869852 | 기존 Warm 예측 산출물 |

## validation MAPE 상위 후보

| candidate | policy | split | MAPE | MdAPE | p95_APE | RMSE_log | Within_30 | Within_50 | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| wmape_catboost_residual_v8_compact_blend_mape_guarded | W-MAPE-09/10_catboost_residual_model | validation | 0.209760 | 0.112877 | 0.674460 | 0.338070 | 0.780347 | 0.907514 | v8__compact_blend_mape_guarded residual을 CatBoost로 validation 학습 후 cap 적용 |
| wmape_catboost_residual_h29_h29_v8_compact_mape_gallery_median_cap0p05 | W-MAPE-09/10_catboost_residual_model | validation | 0.209793 | 0.112322 | 0.705257 | 0.341043 | 0.786127 | 0.903661 | h29__h29_v8_compact_mape_gallery_median_cap0p05 residual을 CatBoost로 validation 학습 후 cap 적용 |
| wmape_huber_residual_h29_h29_v8_compact_mape_gallery_median_cap0p05 | W-MAPE-09/10_linear_residual_model | validation | 0.242048 | 0.148080 | 0.703280 | 0.365717 | 0.749518 | 0.892100 | h29__h29_v8_compact_mape_gallery_median_cap0p05 residual을 huber_residual로 validation 학습 후 cap 적용 |
| wmape_huber_residual_v8_compact_blend_mape_guarded | W-MAPE-09/10_linear_residual_model | validation | 0.242145 | 0.148203 | 0.703092 | 0.365637 | 0.749518 | 0.892100 | v8__compact_blend_mape_guarded residual을 huber_residual로 validation 학습 후 cap 적용 |
| wmape_segment_v8_compact_blend_mdape_log_area | W-MAPE-05/06/07/08_segment_mape_correction | validation | 0.242563 | 0.157440 | 0.689606 | 0.380227 | 0.751445 | 0.895954 | v8__compact_blend_mdape + 작품 면적 구간별 validation MAPE 최소 보정 |
| wmape_segment_v8_compact_blend_mape_guarded_log_area | W-MAPE-05/06/07/08_segment_mape_correction | validation | 0.243003 | 0.160260 | 0.700053 | 0.378585 | 0.741811 | 0.894027 | v8__compact_blend_mape_guarded + 작품 면적 구간별 validation MAPE 최소 보정 |
| wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_log_area | W-MAPE-05/06/07/08_segment_mape_correction | validation | 0.243044 | 0.159194 | 0.698023 | 0.378913 | 0.741811 | 0.894027 | h29__h29_v8_compact_mape_gallery_median_cap0p05 + 작품 면적 구간별 validation MAPE 최소 보정 |
| wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_quantile_width | W-MAPE-05/06/07/08_segment_mape_correction | validation | 0.243051 | 0.162348 | 0.681790 | 0.380765 | 0.745665 | 0.895954 | h29__h29_v8_compact_mape_gallery_median_cap0p05 + Quantile width 구간별 validation MAPE 최소 보정 |
| wmape_segment_v8_compact_blend_mape_guarded_quantile_width | W-MAPE-05/06/07/08_segment_mape_correction | validation | 0.243068 | 0.162148 | 0.686365 | 0.380509 | 0.745665 | 0.895954 | v8__compact_blend_mape_guarded + Quantile width 구간별 validation MAPE 최소 보정 |
| wmape_segment_v8_compact_blend_mdape_quantile_width | W-MAPE-05/06/07/08_segment_mape_correction | validation | 0.243801 | 0.162533 | 0.675554 | 0.381762 | 0.743738 | 0.894027 | v8__compact_blend_mdape + Quantile width 구간별 validation MAPE 최소 보정 |
| wmape_ridge_residual_h29_h29_v8_compact_mape_gallery_median_cap0p05 | W-MAPE-09/10_linear_residual_model | validation | 0.244118 | 0.145397 | 0.709393 | 0.364470 | 0.749518 | 0.897881 | h29__h29_v8_compact_mape_gallery_median_cap0p05 residual을 ridge_residual로 validation 학습 후 cap 적용 |
| wmape_ridge_residual_v8_compact_blend_mape_guarded | W-MAPE-09/10_linear_residual_model | validation | 0.244297 | 0.145278 | 0.711826 | 0.364401 | 0.749518 | 0.897881 | v8__compact_blend_mape_guarded residual을 ridge_residual로 validation 학습 후 cap 적용 |
| wmape_segment_v8_compact_blend_mdape_artist_works_log | W-MAPE-05/06/07/08_segment_mape_correction | validation | 0.244362 | 0.158241 | 0.699914 | 0.379157 | 0.751445 | 0.890173 | v8__compact_blend_mdape + 작가 학습량 구간별 validation MAPE 최소 보정 |
| wmape_segment_v8_compact_blend_mape_guarded_pred_price_bin | W-MAPE-05/06/07/08_segment_mape_correction | validation | 0.244506 | 0.160572 | 0.701236 | 0.378479 | 0.749518 | 0.897881 | v8__compact_blend_mape_guarded + 예측 가격 구간별 validation MAPE 최소 보정 |
| wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_pred_price_bin | W-MAPE-05/06/07/08_segment_mape_correction | validation | 0.244565 | 0.161278 | 0.701126 | 0.378314 | 0.751445 | 0.897881 | h29__h29_v8_compact_mape_gallery_median_cap0p05 + 예측 가격 구간별 validation MAPE 최소 보정 |
| wmape_segment_v8_compact_blend_mape_guarded_artist_works_log | W-MAPE-05/06/07/08_segment_mape_correction | validation | 0.245167 | 0.159017 | 0.695191 | 0.378268 | 0.743738 | 0.895954 | v8__compact_blend_mape_guarded + 작가 학습량 구간별 validation MAPE 최소 보정 |
| wmape_segment_v8_compact_blend_mdape_pred_price_bin | W-MAPE-05/06/07/08_segment_mape_correction | validation | 0.245209 | 0.161798 | 0.701469 | 0.379672 | 0.741811 | 0.897881 | v8__compact_blend_mdape + 예측 가격 구간별 validation MAPE 최소 보정 |
| wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_artist_works_log | W-MAPE-05/06/07/08_segment_mape_correction | validation | 0.245239 | 0.157333 | 0.693688 | 0.378432 | 0.743738 | 0.895954 | h29__h29_v8_compact_mape_gallery_median_cap0p05 + 작가 학습량 구간별 validation MAPE 최소 보정 |
| wmape_segment_v8_compact_blend_mdape_routing_width | W-MAPE-05/06/07/08_segment_mape_correction | validation | 0.245493 | 0.156110 | 0.695356 | 0.381024 | 0.743738 | 0.888247 | v8__compact_blend_mdape + V8 routing width 구간별 validation MAPE 최소 보정 |
| wmape_segment_v8_compact_blend_mape_guarded_search_quality_score | W-MAPE-05/06/07/08_segment_mape_correction | validation | 0.245495 | 0.159715 | 0.692024 | 0.376676 | 0.743738 | 0.901734 | v8__compact_blend_mape_guarded + 검색 품질 구간별 validation MAPE 최소 보정 |

## test MAPE 상위 후보

| candidate | policy | split | MAPE | MdAPE | p95_APE | RMSE_log | Within_30 | Within_50 | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_quantile_width | W-MAPE-05/06/07/08_segment_mape_correction | test | 0.267365 | 0.163788 | 0.832172 | 0.410206 | 0.705107 | 0.887974 | h29__h29_v8_compact_mape_gallery_median_cap0p05 + Quantile width 구간별 validation MAPE 최소 보정 |
| wmape_segment_v8_compact_blend_mape_guarded_quantile_width | W-MAPE-05/06/07/08_segment_mape_correction | test | 0.267484 | 0.162634 | 0.833161 | 0.409880 | 0.703460 | 0.887974 | v8__compact_blend_mape_guarded + Quantile width 구간별 validation MAPE 최소 보정 |
| wmape_segment_v8_compact_blend_mdape_quantile_width | W-MAPE-05/06/07/08_segment_mape_correction | test | 0.270758 | 0.160991 | 0.815016 | 0.411859 | 0.714992 | 0.886326 | v8__compact_blend_mdape + Quantile width 구간별 validation MAPE 최소 보정 |
| wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_artist_works_log | W-MAPE-05/06/07/08_segment_mape_correction | test | 0.271648 | 0.162864 | 0.856539 | 0.406844 | 0.721582 | 0.879736 | h29__h29_v8_compact_mape_gallery_median_cap0p05 + 작가 학습량 구간별 validation MAPE 최소 보정 |
| wmape_segment_v8_compact_blend_mape_guarded_artist_works_log | W-MAPE-05/06/07/08_segment_mape_correction | test | 0.271674 | 0.163860 | 0.857654 | 0.406704 | 0.721582 | 0.879736 | v8__compact_blend_mape_guarded + 작가 학습량 구간별 validation MAPE 최소 보정 |
| wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_routing_width | W-MAPE-05/06/07/08_segment_mape_correction | test | 0.272237 | 0.167092 | 0.851721 | 0.409924 | 0.718287 | 0.883031 | h29__h29_v8_compact_mape_gallery_median_cap0p05 + V8 routing width 구간별 validation MAPE 최소 보정 |
| wmape_segment_v8_compact_blend_mape_guarded_routing_width | W-MAPE-05/06/07/08_segment_mape_correction | test | 0.272255 | 0.167765 | 0.850234 | 0.409906 | 0.718287 | 0.883031 | v8__compact_blend_mape_guarded + V8 routing width 구간별 validation MAPE 최소 보정 |
| wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_source_group_gallery_museum_ratio | W-MAPE-05/06/07/08_segment_mape_correction | test | 0.272750 | 0.168676 | 0.866631 | 0.406921 | 0.721582 | 0.873147 | h29__h29_v8_compact_mape_gallery_median_cap0p05 + 갤러리/미술관 비중 구간별 validation MAPE 최소 보정 |
| wmape_segment_v8_compact_blend_mape_guarded_source_group_gallery_museum_ratio | W-MAPE-05/06/07/08_segment_mape_correction | test | 0.272807 | 0.168693 | 0.867756 | 0.406844 | 0.723229 | 0.873147 | v8__compact_blend_mape_guarded + 갤러리/미술관 비중 구간별 validation MAPE 최소 보정 |
| wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_search_quality_score | W-MAPE-05/06/07/08_segment_mape_correction | test | 0.272988 | 0.166971 | 0.822696 | 0.403878 | 0.734761 | 0.874794 | h29__h29_v8_compact_mape_gallery_median_cap0p05 + 검색 품질 구간별 validation MAPE 최소 보정 |
| wmape_segment_v8_compact_blend_mape_guarded_search_quality_score | W-MAPE-05/06/07/08_segment_mape_correction | test | 0.273038 | 0.167329 | 0.822646 | 0.403894 | 0.733114 | 0.873147 | v8__compact_blend_mape_guarded + 검색 품질 구간별 validation MAPE 최소 보정 |
| wmape_segment_v8_compact_blend_mdape_artist_works_log | W-MAPE-05/06/07/08_segment_mape_correction | test | 0.274039 | 0.170822 | 0.832970 | 0.408422 | 0.726524 | 0.881384 | v8__compact_blend_mdape + 작가 학습량 구간별 validation MAPE 최소 보정 |
| wmape_segment_v8_compact_blend_mape_guarded_pred_price_bin | W-MAPE-05/06/07/08_segment_mape_correction | test | 0.274194 | 0.162685 | 0.842592 | 0.412802 | 0.723229 | 0.881384 | v8__compact_blend_mape_guarded + 예측 가격 구간별 validation MAPE 최소 보정 |
| wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_source_group_news_ratio | W-MAPE-05/06/07/08_segment_mape_correction | test | 0.274271 | 0.171534 | 0.841791 | 0.408651 | 0.723229 | 0.869852 | h29__h29_v8_compact_mape_gallery_median_cap0p05 + 뉴스 비중 구간별 validation MAPE 최소 보정 |
| wmape_segment_v8_compact_blend_mape_guarded_source_group_news_ratio | W-MAPE-05/06/07/08_segment_mape_correction | test | 0.274302 | 0.170799 | 0.842894 | 0.408516 | 0.723229 | 0.868204 | v8__compact_blend_mape_guarded + 뉴스 비중 구간별 validation MAPE 최소 보정 |
| wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_pred_price_bin | W-MAPE-05/06/07/08_segment_mape_correction | test | 0.274337 | 0.163428 | 0.843017 | 0.412825 | 0.723229 | 0.881384 | h29__h29_v8_compact_mape_gallery_median_cap0p05 + 예측 가격 구간별 validation MAPE 최소 보정 |
| wmape_segment_v8_compact_blend_mape_guarded_log_area | W-MAPE-05/06/07/08_segment_mape_correction | test | 0.274356 | 0.169106 | 0.826846 | 0.409142 | 0.713344 | 0.873147 | v8__compact_blend_mape_guarded + 작품 면적 구간별 validation MAPE 최소 보정 |
| wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_log_area | W-MAPE-05/06/07/08_segment_mape_correction | test | 0.274397 | 0.169247 | 0.825377 | 0.409475 | 0.713344 | 0.878089 | h29__h29_v8_compact_mape_gallery_median_cap0p05 + 작품 면적 구간별 validation MAPE 최소 보정 |
| wmape_segment_v8_compact_blend_mdape_search_quality_score | W-MAPE-05/06/07/08_segment_mape_correction | test | 0.275090 | 0.170490 | 0.826748 | 0.406756 | 0.724876 | 0.886326 | v8__compact_blend_mdape + 검색 품질 구간별 validation MAPE 최소 보정 |
| wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_source_group_social_blog_ratio | W-MAPE-05/06/07/08_segment_mape_correction | test | 0.275309 | 0.168120 | 0.871752 | 0.409110 | 0.718287 | 0.878089 | h29__h29_v8_compact_mape_gallery_median_cap0p05 + 소셜/블로그 비중 구간별 validation MAPE 최소 보정 |
| wmape_segment_v8_compact_blend_mape_guarded_source_group_social_blog_ratio | W-MAPE-05/06/07/08_segment_mape_correction | test | 0.275336 | 0.167382 | 0.873414 | 0.408972 | 0.718287 | 0.878089 | v8__compact_blend_mape_guarded + 소셜/블로그 비중 구간별 validation MAPE 최소 보정 |
| wmape_segment_v8_compact_blend_mdape_routing_width | W-MAPE-05/06/07/08_segment_mape_correction | test | 0.275536 | 0.161627 | 0.834850 | 0.411119 | 0.718287 | 0.884679 | v8__compact_blend_mdape + V8 routing width 구간별 validation MAPE 최소 보정 |
| wmape_segment_v8_compact_blend_mdape_source_group_gallery_museum_ratio | W-MAPE-05/06/07/08_segment_mape_correction | test | 0.276215 | 0.167963 | 0.838924 | 0.409613 | 0.723229 | 0.881384 | v8__compact_blend_mdape + 갤러리/미술관 비중 구간별 validation MAPE 최소 보정 |
| wmape_segment_v8_compact_blend_mdape_source_group_news_ratio | W-MAPE-05/06/07/08_segment_mape_correction | test | 0.276955 | 0.163123 | 0.827441 | 0.411082 | 0.719934 | 0.881384 | v8__compact_blend_mdape + 뉴스 비중 구간별 validation MAPE 최소 보정 |
| wmape_segment_v8_compact_blend_mdape_log_area | W-MAPE-05/06/07/08_segment_mape_correction | test | 0.276966 | 0.168151 | 0.828092 | 0.411602 | 0.716639 | 0.879736 | v8__compact_blend_mdape + 작품 면적 구간별 validation MAPE 최소 보정 |

## 앙상블 구성

| candidate | policy | sources | validation_mape | validation_mdape | validation_p95 | notes |
| --- | --- | --- | --- | --- | --- | --- |
| wmape_global_mape_top4 | global_weighted_blend | {"h29__h29_v8_compact_mdape_news_median_cap0p05": 0.0, "h29__h29_v8_compact_mdape_news_median_cap0p1": 0.0, "h29__h29_v8_compact_mdape_news_median_cap0p15": 0.95, "h29__h29_v8_compact_mdape_homonym_median_cap0p05": 0.05} | 0.251140 | 0.148347 | 0.740493 | validation MAPE 최소 convex log blend |
| wmape_global_mape_top5 | global_weighted_blend | {"h29__h29_v8_compact_mdape_news_median_cap0p05": 0.0, "h29__h29_v8_compact_mdape_news_median_cap0p1": 0.0, "h29__h29_v8_compact_mdape_news_median_cap0p15": 0.95, "h29__h29_v8_compact_mdape_homonym_median_cap0p05": 0.0, "h29__h29_v8_compact_mdape_homonym_median_cap0p1": 0.05} | 0.251140 | 0.148347 | 0.740493 | validation MAPE 최소 convex log blend |
| wmape_global_guarded_top5 | global_weighted_blend | {"h29__h29_v8_compact_mdape_news_median_cap0p05": 0.0, "h29__h29_v8_compact_mdape_news_median_cap0p1": 0.0, "h29__h29_v8_compact_mdape_news_median_cap0p15": 0.95, "h29__h29_v8_compact_mdape_homonym_median_cap0p05": 0.0, "h29__h29_v8_compact_mdape_homonym_median_cap0p1": 0.05} | 0.251140 | 0.148347 | 0.740493 | MAPE 우선 + MdAPE/p95 방어 convex log blend |

## 구간 보정 샘플

| segment | segment_row_count | correction | validation_segment_mape | cap | min_rows | candidate | base_source | segment_name | segment_label | segment_col | mode | valid_train_rows | cuts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bin1 | 173 | -0.096000 | 0.264906 | 0.120000 | 18 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_pred_price_bin | h29__h29_v8_compact_mape_gallery_median_cap0p05 | pred_price_bin | 예측 가격 구간 | pred_price_bin | q3 | 519 | [14.381586946818725, 15.415270659244422] |
| bin2 | 173 | -0.024000 | 0.206882 | 0.120000 | 18 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_pred_price_bin | h29__h29_v8_compact_mape_gallery_median_cap0p05 | pred_price_bin | 예측 가격 구간 | pred_price_bin | q3 | 519 | [14.381586946818725, 15.415270659244422] |
| bin3 | 173 | -0.086000 | 0.261906 | 0.120000 | 18 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_pred_price_bin | h29__h29_v8_compact_mape_gallery_median_cap0p05 | pred_price_bin | 예측 가격 구간 | pred_price_bin | q3 | 519 | [14.381586946818725, 15.415270659244422] |
| bin1 | 174 | -0.120000 | 0.305730 | 0.120000 | 18 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_log_area | h29__h29_v8_compact_mape_gallery_median_cap0p05 | log_area | 작품 면적 구간 | log_area | q3 | 519 | [7.776954403322442, 8.765467587691576] |
| bin2 | 172 | -0.018000 | 0.183692 | 0.120000 | 18 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_log_area | h29__h29_v8_compact_mape_gallery_median_cap0p05 | log_area | 작품 면적 구간 | log_area | q3 | 519 | [7.776954403322442, 8.765467587691576] |
| bin3 | 173 | -0.054000 | 0.239005 | 0.120000 | 18 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_log_area | h29__h29_v8_compact_mape_gallery_median_cap0p05 | log_area | 작품 면적 구간 | log_area | q3 | 519 | [7.776954403322442, 8.765467587691576] |
| bin1 | 180 | -0.064000 | 0.277044 | 0.120000 | 18 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_artist_works_log | h29__h29_v8_compact_mape_gallery_median_cap0p05 | artist_works_log | 작가 학습량 구간 | artist_works_log | q3 | 519 | [2.302585092994046, 3.044522437723423] |
| bin2 | 168 | -0.088000 | 0.253925 | 0.120000 | 18 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_artist_works_log | h29__h29_v8_compact_mape_gallery_median_cap0p05 | artist_works_log | 작가 학습량 구간 | artist_works_log | q3 | 519 | [2.302585092994046, 3.044522437723423] |
| bin3 | 171 | -0.036000 | 0.203227 | 0.120000 | 18 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_artist_works_log | h29__h29_v8_compact_mape_gallery_median_cap0p05 | artist_works_log | 작가 학습량 구간 | artist_works_log | q3 | 519 | [2.302585092994046, 3.044522437723423] |
| bin1 | 173 | -0.052000 | 0.206418 | 0.120000 | 18 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_routing_width | h29__h29_v8_compact_mape_gallery_median_cap0p05 | routing_width | V8 routing width 구간 | routing_width | q3 | 519 | [1.1877903173061888, 1.6162511551879402] |
| bin2 | 173 | -0.062000 | 0.218824 | 0.120000 | 18 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_routing_width | h29__h29_v8_compact_mape_gallery_median_cap0p05 | routing_width | V8 routing width 구간 | routing_width | q3 | 519 | [1.1877903173061888, 1.6162511551879402] |
| bin3 | 173 | -0.098000 | 0.312097 | 0.120000 | 18 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_routing_width | h29__h29_v8_compact_mape_gallery_median_cap0p05 | routing_width | V8 routing width 구간 | routing_width | q3 | 519 | [1.1877903173061888, 1.6162511551879402] |
| bin1 | 173 | -0.034000 | 0.200623 | 0.120000 | 18 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_quantile_width | h29__h29_v8_compact_mape_gallery_median_cap0p05 | quantile_width | Quantile width 구간 | quantile_width | q3 | 519 | [1.148725562845603, 1.4838845434566739] |
| bin2 | 173 | -0.052000 | 0.200092 | 0.120000 | 18 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_quantile_width | h29__h29_v8_compact_mape_gallery_median_cap0p05 | quantile_width | Quantile width 구간 | quantile_width | q3 | 519 | [1.148725562845603, 1.4838845434566739] |
| bin3 | 173 | -0.120000 | 0.328438 | 0.120000 | 18 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_quantile_width | h29__h29_v8_compact_mape_gallery_median_cap0p05 | quantile_width | Quantile width 구간 | quantile_width | q3 | 519 | [1.148725562845603, 1.4838845434566739] |
| bin1 | 168 | -0.018000 | 0.217951 | 0.120000 | 18 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_search_quality_score | h29__h29_v8_compact_mape_gallery_median_cap0p05 | search_quality_score | 검색 품질 구간 | search_quality_score | q3 | 489 | [0.144, 0.174] |
| bin2 | 159 | -0.100000 | 0.273601 | 0.120000 | 18 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_search_quality_score | h29__h29_v8_compact_mape_gallery_median_cap0p05 | search_quality_score | 검색 품질 구간 | search_quality_score | q3 | 489 | [0.144, 0.174] |
| bin3 | 162 | -0.052000 | 0.219475 | 0.120000 | 18 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_search_quality_score | h29__h29_v8_compact_mape_gallery_median_cap0p05 | search_quality_score | 검색 품질 구간 | search_quality_score | q3 | 489 | [0.144, 0.174] |
| nan | 30 | -0.120000 | 0.341875 | 0.120000 | 18 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_search_quality_score | h29__h29_v8_compact_mape_gallery_median_cap0p05 | search_quality_score | 검색 품질 구간 | search_quality_score | q3 | 489 | [0.144, 0.174] |
| bin1 | 228 | -0.048000 | 0.241302 | 0.120000 | 18 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_source_group_news_ratio | h29__h29_v8_compact_mape_gallery_median_cap0p05 | source_group_news_ratio | 뉴스 비중 구간 | source_group_news_ratio | q3 | 489 | [0.0, 0.04] |
| bin2 | 135 | -0.096000 | 0.255234 | 0.120000 | 18 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_source_group_news_ratio | h29__h29_v8_compact_mape_gallery_median_cap0p05 | source_group_news_ratio | 뉴스 비중 구간 | source_group_news_ratio | q3 | 489 | [0.0, 0.04] |
| bin3 | 126 | -0.036000 | 0.214111 | 0.120000 | 18 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_source_group_news_ratio | h29__h29_v8_compact_mape_gallery_median_cap0p05 | source_group_news_ratio | 뉴스 비중 구간 | source_group_news_ratio | q3 | 489 | [0.0, 0.04] |
| nan | 30 | -0.120000 | 0.341875 | 0.120000 | 18 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_source_group_news_ratio | h29__h29_v8_compact_mape_gallery_median_cap0p05 | source_group_news_ratio | 뉴스 비중 구간 | source_group_news_ratio | q3 | 489 | [0.0, 0.04] |
| bin1 | 423 | -0.056000 | 0.248109 | 0.120000 | 18 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_source_group_gallery_museum_ratio | h29__h29_v8_compact_mape_gallery_median_cap0p05 | source_group_gallery_museum_ratio | 갤러리/미술관 비중 구간 | source_group_gallery_museum_ratio | q3 | 489 | [0.0] |
| bin2 | 66 | -0.050000 | 0.180849 | 0.120000 | 18 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_source_group_gallery_museum_ratio | h29__h29_v8_compact_mape_gallery_median_cap0p05 | source_group_gallery_museum_ratio | 갤러리/미술관 비중 구간 | source_group_gallery_museum_ratio | q3 | 489 | [0.0] |
| nan | 30 | -0.120000 | 0.341875 | 0.120000 | 18 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_source_group_gallery_museum_ratio | h29__h29_v8_compact_mape_gallery_median_cap0p05 | source_group_gallery_museum_ratio | 갤러리/미술관 비중 구간 | source_group_gallery_museum_ratio | q3 | 489 | [0.0] |
| bin1 | 213 | -0.060000 | 0.234688 | 0.120000 | 18 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_source_group_social_blog_ratio | h29__h29_v8_compact_mape_gallery_median_cap0p05 | source_group_social_blog_ratio | 소셜/블로그 비중 구간 | source_group_social_blog_ratio | q3 | 489 | [0.1, 0.18] |
| bin2 | 129 | -0.100000 | 0.220498 | 0.120000 | 18 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_source_group_social_blog_ratio | h29__h29_v8_compact_mape_gallery_median_cap0p05 | source_group_social_blog_ratio | 소셜/블로그 비중 구간 | source_group_social_blog_ratio | q3 | 489 | [0.1, 0.18] |
| bin3 | 147 | -0.032000 | 0.258478 | 0.120000 | 18 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_source_group_social_blog_ratio | h29__h29_v8_compact_mape_gallery_median_cap0p05 | source_group_social_blog_ratio | 소셜/블로그 비중 구간 | source_group_social_blog_ratio | q3 | 489 | [0.1, 0.18] |
| nan | 30 | -0.120000 | 0.341875 | 0.120000 | 18 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_source_group_social_blog_ratio | h29__h29_v8_compact_mape_gallery_median_cap0p05 | source_group_social_blog_ratio | 소셜/블로그 비중 구간 | source_group_social_blog_ratio | q3 | 489 | [0.1, 0.18] |
| bin1 | 173 | -0.098000 | 0.264816 | 0.120000 | 18 | wmape_segment_v8_compact_blend_mape_guarded_pred_price_bin | v8__compact_blend_mape_guarded | pred_price_bin | 예측 가격 구간 | pred_price_bin | q3 | 519 | [14.384474198679882, 15.41815791110558] |
| bin2 | 173 | -0.028000 | 0.206795 | 0.120000 | 18 | wmape_segment_v8_compact_blend_mape_guarded_pred_price_bin | v8__compact_blend_mape_guarded | pred_price_bin | 예측 가격 구간 | pred_price_bin | q3 | 519 | [14.384474198679882, 15.41815791110558] |
| bin3 | 173 | -0.090000 | 0.261906 | 0.120000 | 18 | wmape_segment_v8_compact_blend_mape_guarded_pred_price_bin | v8__compact_blend_mape_guarded | pred_price_bin | 예측 가격 구간 | pred_price_bin | q3 | 519 | [14.384474198679882, 15.41815791110558] |
| bin1 | 174 | -0.120000 | 0.305669 | 0.120000 | 18 | wmape_segment_v8_compact_blend_mape_guarded_log_area | v8__compact_blend_mape_guarded | log_area | 작품 면적 구간 | log_area | q3 | 519 | [7.776954403322442, 8.765467587691576] |
| bin2 | 172 | -0.020000 | 0.183638 | 0.120000 | 18 | wmape_segment_v8_compact_blend_mape_guarded_log_area | v8__compact_blend_mape_guarded | log_area | 작품 면적 구간 | log_area | q3 | 519 | [7.776954403322442, 8.765467587691576] |
| bin3 | 173 | -0.056000 | 0.238997 | 0.120000 | 18 | wmape_segment_v8_compact_blend_mape_guarded_log_area | v8__compact_blend_mape_guarded | log_area | 작품 면적 구간 | log_area | q3 | 519 | [7.776954403322442, 8.765467587691576] |
| bin1 | 180 | -0.066000 | 0.276838 | 0.120000 | 18 | wmape_segment_v8_compact_blend_mape_guarded_artist_works_log | v8__compact_blend_mape_guarded | artist_works_log | 작가 학습량 구간 | artist_works_log | q3 | 519 | [2.302585092994046, 3.044522437723423] |
| bin2 | 168 | -0.090000 | 0.253924 | 0.120000 | 18 | wmape_segment_v8_compact_blend_mape_guarded_artist_works_log | v8__compact_blend_mape_guarded | artist_works_log | 작가 학습량 구간 | artist_works_log | q3 | 519 | [2.302585092994046, 3.044522437723423] |
| bin3 | 171 | -0.038000 | 0.203225 | 0.120000 | 18 | wmape_segment_v8_compact_blend_mape_guarded_artist_works_log | v8__compact_blend_mape_guarded | artist_works_log | 작가 학습량 구간 | artist_works_log | q3 | 519 | [2.302585092994046, 3.044522437723423] |
| bin1 | 173 | -0.054000 | 0.206356 | 0.120000 | 18 | wmape_segment_v8_compact_blend_mape_guarded_routing_width | v8__compact_blend_mape_guarded | routing_width | V8 routing width 구간 | routing_width | q3 | 519 | [1.1877903173061888, 1.6162511551879402] |

## 라우팅 구성

| candidate | route_feature | segment | selected_source | validation_segment_mape | segment_row_count | segment_col | mode | valid_train_rows | cuts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| wmape_route_routing_width | routing_width | bin1 | h29__h29_v8_compact_mape_news_median_cap0p05 | 0.210140 | 173 | routing_width | q3 | 519 | [1.1877903173061888, 1.6162511551879402] |
| wmape_route_routing_width | routing_width | bin2 | h29__h29_v8_compact_mdape_news_median_cap0p05 | 0.220397 | 173 | routing_width | q3 | 519 | [1.1877903173061888, 1.6162511551879402] |
| wmape_route_routing_width | routing_width | bin3 | h29__h29_v8_compact_mdape_news_median_cap0p05 | 0.321460 | 173 | routing_width | q3 | 519 | [1.1877903173061888, 1.6162511551879402] |
| wmape_route_quantile_width | quantile_width | bin1 | h29__h29_v8_compact_mape_news_median_cap0p05 | 0.200584 | 173 | quantile_width | q3 | 519 | [1.148725562845603, 1.4838845434566739] |
| wmape_route_quantile_width | quantile_width | bin2 | h29__h29_v8_compact_mape_news_median_cap0p05 | 0.204181 | 173 | quantile_width | q3 | 519 | [1.148725562845603, 1.4838845434566739] |
| wmape_route_quantile_width | quantile_width | bin3 | h29__h29_v8_compact_mdape_homonym_median_cap0p05 | 0.344682 | 173 | quantile_width | q3 | 519 | [1.148725562845603, 1.4838845434566739] |
| wmape_route_log_area | log_area | bin1 | h29__h29_v8_compact_mape_news_median_cap0p05 | 0.327169 | 174 | log_area | q3 | 519 | [7.776954403322442, 8.765467587691576] |
| wmape_route_log_area | log_area | bin2 | h29__h29_v8_compact_mape_news_median_cap0p05 | 0.183559 | 172 | log_area | q3 | 519 | [7.776954403322442, 8.765467587691576] |
| wmape_route_log_area | log_area | bin3 | h29__h29_v8_compact_mdape_homonym_median_cap0p05 | 0.232341 | 173 | log_area | q3 | 519 | [7.776954403322442, 8.765467587691576] |
| wmape_route_artist_works_log | artist_works_log | bin1 | h29__h29_v8_compact_mdape_news_median_cap0p05 | 0.279335 | 180 | artist_works_log | q3 | 519 | [2.302585092994046, 3.044522437723423] |
| wmape_route_artist_works_log | artist_works_log | bin2 | h29__h29_v8_compact_mape_news_median_cap0p05 | 0.268490 | 168 | artist_works_log | q3 | 519 | [2.302585092994046, 3.044522437723423] |
| wmape_route_artist_works_log | artist_works_log | bin3 | h29__h29_v8_compact_mdape_news_median_cap0p05 | 0.202307 | 171 | artist_works_log | q3 | 519 | [2.302585092994046, 3.044522437723423] |

## 잔차 보정 모델

| candidate | base_source | model | feature_count | train_rows | correction_cap |
| --- | --- | --- | --- | --- | --- |
| wmape_ridge_residual_h29_h29_v8_compact_mape_gallery_median_cap0p05 | h29__h29_v8_compact_mape_gallery_median_cap0p05 | ridge_residual | 31 | 519 | 0.120000 |
| wmape_huber_residual_h29_h29_v8_compact_mape_gallery_median_cap0p05 | h29__h29_v8_compact_mape_gallery_median_cap0p05 | huber_residual | 31 | 519 | 0.120000 |
| wmape_catboost_residual_h29_h29_v8_compact_mape_gallery_median_cap0p05 | h29__h29_v8_compact_mape_gallery_median_cap0p05 | catboost_residual | 35 | 519 | 0.120000 |
| wmape_ridge_residual_v8_compact_blend_mape_guarded | v8__compact_blend_mape_guarded | ridge_residual | 31 | 519 | 0.120000 |
| wmape_huber_residual_v8_compact_blend_mape_guarded | v8__compact_blend_mape_guarded | huber_residual | 31 | 519 | 0.120000 |
| wmape_catboost_residual_v8_compact_blend_mape_guarded | v8__compact_blend_mape_guarded | catboost_residual | 35 | 519 | 0.120000 |

## 안정성 검증

| baseline | candidate | row_prob_mape_improvement_gt_0 | row_mean_mape_improvement | row_p05_mape_improvement | artist_prob_mape_improvement_gt_0 | artist_mean_mape_improvement | artist_p05_mape_improvement | bootstrap_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| h29__h29_v8_compact_mape_gallery_median_cap0p05 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_quantile_width | 1.000000 | 0.013513 | 0.007200 | 0.998750 | 0.013988 | 0.005788 | 800 |
| h29__h29_v8_compact_mape_gallery_median_cap0p05 | wmape_segment_v8_compact_blend_mape_guarded_quantile_width | 1.000000 | 0.013499 | 0.007807 | 0.997500 | 0.013514 | 0.004933 | 800 |
| h29__h29_v8_compact_mape_gallery_median_cap0p05 | wmape_segment_v8_compact_blend_mdape_quantile_width | 0.990000 | 0.009991 | 0.003464 | 0.976250 | 0.009790 | 0.001782 | 800 |
| h29__h29_v8_compact_mape_gallery_median_cap0p05 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_artist_works_log | 0.998750 | 0.009123 | 0.004297 | 0.996250 | 0.009172 | 0.002942 | 800 |
| h29__h29_v8_compact_mape_gallery_median_cap0p05 | wmape_segment_v8_compact_blend_mape_guarded_artist_works_log | 0.998750 | 0.009238 | 0.004135 | 0.996250 | 0.009005 | 0.002865 | 800 |
| h29__h29_v8_compact_mape_gallery_median_cap0p05 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_routing_width | 0.998750 | 0.008736 | 0.003691 | 0.981250 | 0.008749 | 0.001995 | 800 |
| h29__h29_v8_compact_mape_gallery_median_cap0p05 | wmape_segment_v8_compact_blend_mape_guarded_routing_width | 0.995000 | 0.008547 | 0.003113 | 0.976250 | 0.008633 | 0.001960 | 800 |
| h29__h29_v8_compact_mape_gallery_median_cap0p05 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_source_group_gallery_museum_ratio | 1.000000 | 0.008145 | 0.003996 | 0.996250 | 0.008002 | 0.003163 | 800 |
| h29__h29_v8_compact_mape_gallery_median_cap0p05 | wmape_segment_v8_compact_blend_mape_guarded_source_group_gallery_museum_ratio | 0.998750 | 0.007912 | 0.004047 | 0.998750 | 0.008011 | 0.003109 | 800 |
| h29__h29_v8_compact_mape_gallery_median_cap0p05 | wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_search_quality_score | 1.000000 | 0.007893 | 0.003354 | 0.988750 | 0.007796 | 0.002160 | 800 |

## 해석

- MAPE는 실제 가격 대비 오차이기 때문에, 전역 평균 개선보다 큰 오차 행의 비율을 줄이는 조합이 유리하다.
- Warm에서는 `PP-V8`/`PP-H29` 계열이 이미 강하므로 새 조합의 개선 폭은 Cold보다 작을 수 있다.
- 그래도 validation 기준으로 만든 조합이 test에서도 MAPE를 낮추면 서비스 적용 후보로 볼 수 있다.
- 단, MdAPE와 p95_APE가 같이 악화되는 후보는 MAPE 단독 개선 후보로만 보류한다.
