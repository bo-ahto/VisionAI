# 기존 검증 데이터 기반 Warm/Cold 작품별 오차 원인 분석

## 1. 목적

- 0604 신규 데이터가 아니라 기존 validation/test split으로 분석
- Warm/Cold 최종 후보가 어떤 작품에서 크게 틀리는지 원인 분류
- validation에서 원인별 보정값을 만들고 test에서만 검증
- 정답 가격을 보고 붙이는 사후 원인 설명과, 운영에서 사전에 알 수 있는 피처 기반 보정을 분리

## 2. 기준 후보

- Warm 기준 후보: `compact_blend_mape_guarded`
- Cold 기준 후보: `stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min30_cap0.25`
- 조인 키: `_track6_row_id`
- 사용 데이터: `data/track6_split_with_year_type_edition_size_artist_name`

## 3. 결론

- Warm 최선 test 후보: `corrected_global_pred_price` / MdAPE `0.1620`, MAPE `0.2810`, p95_APE `0.9313`
- Cold 최선 test 후보: `corrected_source_area_pred_price` / MdAPE `0.4140`, MAPE `1.0062`, p95_APE `3.1125`
- 보정 후보는 실제 적용 전 반복 split 검증이 필요
- 이번 실험의 1차 목적은 “어떤 원인이 큰 오차를 만드는지”와 “원인 기반 보정 방향이 있는지”를 확인하는 것

## 4. 기준 성능

| route | split | candidate | n | MdAPE | MAPE | p95_APE | RMSE_log | median_ratio | over_3x_n | under_1_3x_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| warm | test | Warm PP-V8 compact blend mape guarded | 607 | 0.1632 | 0.2816 | 0.9311 | 0.4028 | 0.9966 | 6 | 7 |
| warm | validation | Warm PP-V8 compact blend mape guarded | 519 | 0.1544 | 0.2544 | 0.8084 | 0.3721 | 1.0051 | 4 | 4 |
| cold | test | Cold LightGBM Quantile qwidth stable candidate | 3099 | 0.4247 | 0.9910 | 3.3053 | 0.8575 | 0.9197 | 224 | 271 |
| cold | validation | Cold LightGBM Quantile qwidth stable candidate | 2753 | 0.3656 | 0.5460 | 1.4000 | 0.6388 | 0.9607 | 70 | 113 |

## 5. 원인별 오차 요약

| route | diagnostic_error_cause | n | MdAPE | MAPE | p95_APE | RMSE_log | median_ratio | over_3x_n | under_1_3x_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cold | 예측 범위가 넓은 불확실 구간 | 1194 | 0.4023 | 0.4804 | 1.3995 | 0.5451 | 0.9462 | 0 | 0 |
| cold | 정상 범위 또는 세부 잔차 | 1034 | 0.2493 | 0.2477 | 0.4645 | 0.3275 | 0.8765 | 0 | 0 |
| warm | 정상 범위 또는 세부 잔차 | 468 | 0.1524 | 0.2315 | 0.6930 | 0.3010 | 1.0003 | 0 | 0 |
| cold | 작가 메타 부족 구간 | 376 | 0.6662 | 0.8355 | 1.7016 | 0.7436 | 1.6563 | 0 | 0 |
| cold | 저가 작품 과대 예측 | 173 | 3.8706 | 8.8762 | 29.5503 | 2.0819 | 4.8706 | 173 | 0 |
| cold | 불확실성 큰 구간 과소 예측 | 146 | 0.7323 | 0.7370 | 0.8367 | 1.3677 | 0.2677 | 0 | 146 |
| warm | 유사 표본 수 부족 | 126 | 0.2073 | 0.2944 | 0.9483 | 0.3728 | 0.9675 | 0 | 0 |
| cold | 고가 작품 상방 꼬리 과소 예측 | 91 | 0.8441 | 0.8345 | 0.9692 | 2.1070 | 0.1559 | 0 | 91 |
| cold | 작가 이력 부족 과대 예측 | 51 | 2.7631 | 3.5950 | 7.6637 | 1.4971 | 3.7631 | 51 | 0 |
| cold | 과소 예측 잔차 | 34 | 0.7169 | 0.7340 | 0.8404 | 1.3699 | 0.2831 | 0 | 34 |
| warm | 고가 작품 상방 꼬리 과소 예측 | 6 | 0.8254 | 0.8412 | 0.9315 | 2.0237 | 0.1746 | 0 | 6 |
| warm | 과대 예측 잔차 | 5 | 2.9182 | 3.2851 | 4.0123 | 1.4531 | 3.9182 | 5 | 0 |
| warm | 저가 작품 과대 예측 | 1 | 3.3566 | 3.3566 | 3.3566 | 1.4717 | 4.3566 | 1 | 0 |
| warm | 과소 예측 잔차 | 1 | 0.6773 | 0.6773 | 0.6773 | 1.1310 | 0.3227 | 0 | 1 |

## 6. 관측 피처 구간별 취약 구간

| route | area_band | pred_price_band | medium_support_bucket | uncertainty_band | n | MdAPE | MAPE | p95_APE | RMSE_log | median_ratio | over_3x_n | under_1_3x_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cold | medium | 1m_3m | acrylic__canvas | qwidth_high | 115 | 0.8762 | 2.1427 | 4.8287 | 1.2007 | 1.8203 | 55 | 5 |
| cold | large | 3m_10m | mixed_media__canvas | qwidth_mid | 108 | 0.5581 | 1.2711 | 2.4069 | 0.8418 | 1.1416 | 8 | 0 |
| cold | large | 3m_10m | acrylic__canvas | qwidth_mid | 103 | 0.2710 | 8.4313 | 29.5503 | 1.8601 | 1.2589 | 34 | 0 |
| cold | medium | 1m_3m | acrylic__canvas | qwidth_mid | 94 | 0.2528 | 0.7289 | 5.5894 | 0.6331 | 1.0408 | 9 | 0 |
| cold | large | 3m_10m | acrylic__canvas | qwidth_extreme | 92 | 0.4288 | 0.6168 | 1.3600 | 0.9402 | 0.9196 | 3 | 16 |
| cold | large | 3m_10m | acrylic__canvas | qwidth_high | 84 | 0.2596 | 0.3149 | 0.7276 | 0.6460 | 0.7661 | 0 | 17 |
| cold | large | 3m_10m | oil__canvas | qwidth_mid | 81 | 0.5350 | 1.2944 | 1.5995 | 0.8662 | 0.9340 | 4 | 1 |
| cold | large | 3m_10m | oil__canvas | qwidth_extreme | 69 | 0.3373 | 0.5232 | 1.7755 | 0.6349 | 1.0058 | 2 | 2 |
| cold | medium | 1m_3m | mixed_media__canvas | qwidth_extreme | 68 | 0.5747 | 0.8569 | 3.1177 | 0.9266 | 0.6125 | 6 | 17 |
| cold | large | 3m_10m | mixed_media__canvas | qwidth_extreme | 66 | 0.4399 | 0.7148 | 2.1519 | 0.6975 | 1.0054 | 4 | 0 |
| cold | medium | 1m_3m | mixed_media__paper | qwidth_extreme | 49 | 0.4927 | 0.9260 | 2.9772 | 0.7303 | 1.3481 | 8 | 0 |
| cold | medium | 3m_10m | mixed_media__unknown | qwidth_extreme | 47 | 1.3521 | 1.2465 | 2.2227 | 0.9817 | 2.3521 | 3 | 6 |
| cold | medium | 1m_3m | acrylic__canvas | qwidth_extreme | 45 | 0.3097 | 0.4037 | 0.6938 | 0.6012 | 0.7993 | 1 | 2 |
| cold | medium | 3m_10m | acrylic__canvas | qwidth_mid | 43 | 0.3449 | 0.4567 | 1.1405 | 0.4390 | 1.3087 | 0 | 0 |
| cold | medium | 1m_3m | oil__canvas | qwidth_mid | 43 | 0.2845 | 0.4279 | 0.9985 | 0.4480 | 0.8569 | 2 | 0 |
| cold | large | 3m_10m | mixed_media__paper | qwidth_extreme | 40 | 0.6122 | 1.1563 | 3.0414 | 0.8922 | 1.5802 | 9 | 4 |
| cold | medium | 1m_3m | mixed_media__canvas | qwidth_mid | 40 | 0.5221 | 0.6163 | 1.1854 | 0.5380 | 1.5221 | 1 | 0 |
| cold | small | 0_5m_1m | mixed_media__paper | qwidth_extreme | 38 | 0.6727 | 0.6453 | 1.1428 | 0.9243 | 1.2554 | 0 | 12 |
| cold | medium | 1m_3m | oil__canvas | qwidth_extreme | 38 | 0.5117 | 0.5050 | 1.0375 | 0.8864 | 0.8689 | 0 | 1 |
| cold | very_large | 10m_30m | acrylic__canvas | qwidth_extreme | 37 | 0.4185 | 0.4484 | 0.8678 | 0.9043 | 0.5815 | 0 | 7 |
| warm | medium | 1m_3m | oil__canvas | qwidth_low | 37 | 0.1395 | 0.1782 | 0.3993 | 0.2123 | 1.0232 | 0 | 0 |
| cold | medium | 0_5m_1m | mixed_media__paper | qwidth_extreme | 36 | 0.7404 | 0.8308 | 1.3697 | 1.2488 | 0.2751 | 1 | 30 |
| cold | small | 0_5m_1m | acrylic__canvas | qwidth_high | 35 | 0.2981 | 0.4163 | 1.3162 | 0.4448 | 1.0677 | 0 | 0 |
| cold | medium | 1m_3m | oil__canvas | qwidth_high | 33 | 0.3466 | 0.8940 | 6.2859 | 0.7096 | 1.0999 | 3 | 0 |
| cold | medium | 3m_10m | acrylic__canvas | qwidth_extreme | 32 | 0.7030 | 0.7078 | 0.9345 | 1.5237 | 0.5525 | 1 | 14 |
| cold | medium | 1m_3m | mixed_media__canvas | qwidth_high | 31 | 0.6506 | 0.7378 | 1.3336 | 0.5996 | 1.6506 | 1 | 0 |
| cold | large | 10m_30m | print__unknown | qwidth_extreme | 31 | 0.1350 | 0.1929 | 0.4767 | 0.2973 | 0.9119 | 0 | 0 |
| cold | very_large | 10m_30m | mixed_media__canvas | qwidth_extreme | 30 | 0.7562 | 0.8949 | 2.4501 | 1.1785 | 0.5499 | 4 | 12 |
| warm | medium | 1m_3m | acrylic__canvas | qwidth_low | 29 | 0.1201 | 0.1764 | 0.5811 | 0.2229 | 1.0430 | 0 | 0 |
| cold | medium | 1m_3m | mixed_media__paper | qwidth_high | 26 | 0.4242 | 0.9136 | 3.3666 | 0.7058 | 1.3528 | 4 | 0 |
| cold | medium | 3m_10m | oil__canvas | qwidth_mid | 26 | 0.3651 | 0.4580 | 1.0990 | 0.5102 | 0.6464 | 1 | 0 |
| cold | medium | 3m_10m | mixed_media__metal | qwidth_mid | 25 | 0.1922 | 0.1732 | 0.3675 | 0.2600 | 0.8078 | 0 | 0 |
| cold | medium | 1m_3m | acrylic__paper | qwidth_extreme | 24 | 0.4645 | 0.3088 | 0.4754 | 0.4133 | 1.4474 | 0 | 1 |
| cold | very_large | 10m_30m | oil__canvas | qwidth_extreme | 23 | 0.5102 | 0.6196 | 1.4137 | 1.3423 | 0.8735 | 0 | 3 |
| cold | large | 3m_10m | mixed_media__canvas | qwidth_high | 23 | 0.4115 | 0.3925 | 0.7089 | 0.5488 | 1.1657 | 0 | 3 |
| cold | large | 3m_10m | oil__canvas | qwidth_high | 23 | 0.4029 | 0.3816 | 0.6751 | 0.6002 | 0.5996 | 0 | 2 |
| cold | medium | 1m_3m | acrylic__paper | qwidth_high | 22 | 1.8545 | 1.2886 | 2.3653 | 0.9160 | 2.8545 | 2 | 1 |
| cold | large | 3m_10m | acrylic__paper | qwidth_mid | 21 | 0.2698 | 0.2887 | 0.4671 | 0.3863 | 0.7302 | 0 | 0 |
| warm | large | 3m_10m | acrylic__canvas | qwidth_low | 21 | 0.1553 | 0.2634 | 0.2632 | 0.3368 | 1.0366 | 1 | 0 |
| cold | medium | 1m_3m | oil__canvas | qwidth_low | 21 | 0.2369 | 0.2092 | 0.2426 | 0.2422 | 0.7631 | 0 | 0 |

## 7. validation 학습 -> test 적용 보정 후보

| route | candidate | rule | n | MdAPE | MAPE | p95_APE | RMSE_log | median_ratio | over_3x_n | under_1_3x_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| warm | baseline | none | 607 | 0.1632 | 0.2816 | 0.9311 | 0.4028 | 0.9966 | 6 | 7 |
| warm | corrected_global_pred_price | global | 607 | 0.1620 | 0.2810 | 0.9313 | 0.4028 | 0.9941 | 6 | 7 |
| warm | corrected_artist_history_band_pred_price | artist_history_band | 607 | 0.1668 | 0.2828 | 0.9366 | 0.4036 | 0.9977 | 6 | 7 |
| warm | corrected_svc_coverage_group_n_pred_price | svc_coverage_group_n | 607 | 0.1650 | 0.2818 | 0.9312 | 0.4028 | 0.9966 | 6 | 7 |
| warm | corrected_area_pred_price_pred_price | area_pred_price | 607 | 0.1660 | 0.2817 | 0.9311 | 0.4032 | 0.9937 | 6 | 7 |
| warm | corrected_material_support_area_pred_price | material_support_area | 607 | 0.1677 | 0.2830 | 0.9183 | 0.4040 | 0.9972 | 6 | 7 |
| cold | baseline | none | 3099 | 0.4247 | 0.9910 | 3.3053 | 0.8575 | 0.9197 | 224 | 271 |
| cold | corrected_global_pred_price | global | 3099 | 0.4197 | 1.0097 | 3.3924 | 0.8566 | 0.9383 | 227 | 262 |
| cold | corrected_qwidth_pred_price_pred_price | qwidth_pred_price | 3099 | 0.4313 | 0.9602 | 3.1170 | 0.8589 | 0.9192 | 221 | 284 |
| cold | corrected_meta_area_pred_price | meta_area | 3099 | 0.4228 | 1.0135 | 3.3476 | 0.8528 | 0.9452 | 229 | 259 |
| cold | corrected_material_support_area_pred_price | material_support_area | 3099 | 0.4306 | 0.9958 | 3.3053 | 0.8632 | 0.9270 | 226 | 253 |
| cold | corrected_source_area_pred_price | source_area | 3099 | 0.4140 | 1.0062 | 3.1125 | 0.8582 | 0.9566 | 246 | 273 |

## 8. 보정 맵 요약

| route | rule | segment_cols | segments | correction_log_min | correction_log_median | correction_log_max |
| --- | --- | --- | --- | --- | --- | --- |
| warm | global | global | 1 | -0.0025 | -0.0025 | -0.0025 |
| warm | artist_history_band | artist_history_band | 4 | -0.0109 | -0.0001 | 0.0184 |
| warm | svc_coverage_group_n | svc_coverage_tier+svc_group_n_band | 4 | -0.0075 | -0.0068 | 0.0087 |
| warm | area_pred_price | area_band+pred_price_band | 7 | -0.0206 | 0.0106 | 0.0254 |
| warm | material_support_area | medium_support_bucket+area_band | 5 | -0.0488 | -0.0011 | 0.0398 |
| cold | global | global | 1 | 0.0200 | 0.0200 | 0.0200 |
| cold | qwidth_pred_price | uncertainty_band+pred_price_band | 15 | -0.1644 | 0.0741 | 0.2149 |
| cold | meta_area | meta_completeness_band+area_band | 4 | 0.0098 | 0.0280 | 0.1448 |
| cold | material_support_area | medium_support_bucket+area_band | 18 | -0.3000 | -0.0202 | 0.3000 |
| cold | source_area | track4_source+area_band | 11 | -0.3000 | 0.0068 | 0.1911 |

## 9. 큰 오차 상위 사례

| route | split | _track6_row_id | artist_name_ko | artist_key | title_raw | actual_price | pred_price | ape | pred_actual_ratio | diagnostic_error_cause | area_band | pred_price_band | medium_category | support_category | medium_support_bucket | artist_history_band | svc_group_level | svc_coverage_tier | svc_group_n | price_range_ratio | meta_completeness_band |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cold | test | 16284 | 이준희_A | jun hee lee | the heart of gogh | 353280.0000 | 11759261.7673 | 32.2860 | 33.2860 | 저가 작품 과대 예측 | large | 10m_30m | oil | canvas | oil__canvas | artist_n_le_5 |  |  |  | 2.3641 | meta_missing |
| cold | test | 9955 | 이준희_A | jun hee lee | no kettle | 324300.0000 | 9907450.2113 | 29.5503 | 30.5503 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.1328 | meta_missing |
| cold | test | 7133 | 이준희_A | jun hee lee | moving love by pigeon | 324300.0000 | 9907450.2113 | 29.5503 | 30.5503 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.1328 | meta_missing |
| cold | test | 3283 | 이준희_A | jun hee lee | when i meet real father | 324300.0000 | 9907450.2113 | 29.5503 | 30.5503 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.1328 | meta_missing |
| cold | test | 2994 | 이준희_A | jun hee lee | pot and dinner | 324300.0000 | 9907450.2113 | 29.5503 | 30.5503 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.1328 | meta_missing |
| cold | test | 9986 | 이준희_A | jun hee lee | romio and juliet | 324300.0000 | 9907450.2113 | 29.5503 | 30.5503 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.1324 | meta_missing |
| cold | test | 10480 | 이준희_A | jun hee lee | gwan ing bosal - lima | 324300.0000 | 9907450.2113 | 29.5503 | 30.5503 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.1328 | meta_missing |
| cold | test | 9954 | 이준희_A | jun hee lee | ko ho ktyung | 324300.0000 | 9907450.2113 | 29.5503 | 30.5503 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.1328 | meta_missing |
| cold | test | 7132 | 이준희_A | jun hee lee | ac millan | 324300.0000 | 9907450.2113 | 29.5503 | 30.5503 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.1328 | meta_missing |
| cold | test | 3060 | 이준희_A | jun hee lee | super star | 324300.0000 | 9907450.2113 | 29.5503 | 30.5503 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.1328 | meta_missing |
| cold | test | 14421 | 이준희_A | jun hee lee | bird flower | 324300.0000 | 9907450.2113 | 29.5503 | 30.5503 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.1328 | meta_missing |
| cold | test | 2150 | 이준희_A | jun hee lee | apple tree | 324300.0000 | 9907450.2113 | 29.5503 | 30.5503 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.1328 | meta_missing |
| cold | test | 1033 | 이준희_A | jun hee lee | hip hoper | 336720.0000 | 10221548.1273 | 29.3562 | 30.3562 | 저가 작품 과대 예측 | large | 10m_30m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.1397 | meta_missing |
| cold | test | 7080 | 이준희_A | jun hee lee | green hero | 328440.0000 | 9907450.2113 | 29.1652 | 30.1652 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.1328 | meta_missing |
| cold | test | 9949 | 이준희_A | jun hee lee | black sunflower | 328440.0000 | 9907450.2113 | 29.1652 | 30.1652 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.1328 | meta_missing |
| cold | test | 9951 | 이준희_A | jun hee lee | fountain | 328440.0000 | 9907450.2113 | 29.1652 | 30.1652 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.1328 | meta_missing |
| cold | test | 9953 | 이준희_A | jun hee lee | cara - green tear | 324300.0000 | 9444523.4886 | 28.1228 | 29.1228 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.2957 | meta_missing |
| cold | test | 14583 | 이준희_A | jun hee lee | big cat | 324300.0000 | 9444523.4886 | 28.1228 | 29.1228 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.2945 | meta_missing |
| cold | test | 14615 | 이준희_A | jun hee lee | the gourd water is delicious | 324300.0000 | 9444523.4886 | 28.1228 | 29.1228 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.2952 | meta_missing |
| cold | test | 16278 | 이준희_A | jun hee lee | caradelevingne- your fashion looks good | 327060.0000 | 9472166.8168 | 27.9616 | 28.9616 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.2950 | meta_missing |
| cold | test | 10043 | 이준희_A | jun hee lee | henry for matisse | 335340.0000 | 9700465.9797 | 27.9273 | 28.9273 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.3031 | meta_missing |
| cold | test | 10660 | 이준희_A | jun hee lee | secret of easter island | 327060.0000 | 9444523.4886 | 27.8770 | 28.8770 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.2950 | meta_missing |
| cold | test | 16431 | 이준희_A | jun hee lee | pandora | 347760.0000 | 9959597.9702 | 27.6393 | 28.6393 | 저가 작품 과대 예측 | large | 3m_10m | mixed_media | canvas | mixed_media__canvas | artist_n_le_5 |  |  |  | 2.1287 | meta_missing |
| cold | test | 16279 | 이준희_A | jun hee lee | ana- present | 329820.0000 | 9444523.4886 | 27.6354 | 28.6354 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.2950 | meta_missing |
| cold | test | 7082 | 이준희_A | jun hee lee | the man who make destiny | 329820.0000 | 9444523.4886 | 27.6354 | 28.6354 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.2950 | meta_missing |
| cold | test | 803 | 이준희_A | jun hee lee | big love | 351900.0000 | 9907450.2113 | 27.1542 | 28.1542 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.0748 | meta_missing |
| cold | test | 7070 | 이준희_A | jun hee lee | magician girl | 346380.0000 | 9444523.4886 | 26.2664 | 27.2664 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.2950 | meta_missing |
| cold | test | 16429 | 이준희_A | jun hee lee | rainy day in newyork | 331200.0000 | 8995551.1108 | 26.1605 | 27.1605 | 저가 작품 과대 예측 | large | 3m_10m | oil | canvas | oil__canvas | artist_n_le_5 |  |  |  | 2.2187 | meta_missing |
| cold | test | 16297 | 이준희_A | jun hee lee | when waiting her | 368460.0000 | 9907450.2113 | 25.8888 | 26.8888 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.1328 | meta_missing |
| cold | test | 465 | 이준희_A | jun hee lee | emver heard | 369840.0000 | 9907450.2113 | 25.7885 | 26.7885 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.0748 | meta_missing |
| cold | test | 511 | 이준희_A | jun hee lee | margot robbie | 379500.0000 | 9907450.2113 | 25.1066 | 26.1066 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.0748 | meta_missing |
| cold | test | 16432 | 이준희_A | jun hee lee | alita | 383640.0000 | 9722847.5589 | 24.3437 | 25.3437 | 저가 작품 과대 예측 | large | 3m_10m | mixed_media | canvas | mixed_media__canvas | artist_n_le_5 |  |  |  | 2.3629 | meta_missing |
| cold | test | 3636 | 이준희_A | jun hee lee | valerian city of million plenets | 375360.0000 | 9472166.8168 | 24.2349 | 25.2349 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.2950 | meta_missing |
| cold | test | 14439 | 이준희_A | jun hee lee | crazy  love | 397440.0000 | 9907450.2113 | 23.9282 | 24.9282 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.1328 | meta_missing |
| cold | test | 16430 | 이준희_A | jun hee lee | brown skull | 425040.0000 | 9169985.5644 | 20.5744 | 21.5744 | 저가 작품 과대 예측 | large | 3m_10m | oil | canvas | oil__canvas | artist_n_le_5 |  |  |  | 2.3588 | meta_missing |
| cold | test | 10007 | 이준희_A | jun hee lee | full moon, result of crazy love | 614100.0000 | 9907450.2113 | 15.1333 | 16.1333 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.1328 | meta_missing |
| cold | test | 29126 | 유수미 | yoo soo mi | The trace | 462800.0000 | 5558798.2478 | 11.0112 | 12.0112 | 저가 작품 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 6.0862 | meta_missing |
| cold | test | 49985 | 김남경 | namkyoung kim | The Heroes-G | 3174000.0000 | 37307366.2408 | 10.7541 | 11.7541 | 작가 이력 부족 과대 예측 | very_large | 30m_100m | painting_material | paper | painting_material__paper | artist_n_le_5 |  |  |  | 31.1828 | meta_missing |
| cold | test | 16267 | 이준희_A | jun hee lee | blue woman | 484380.0000 | 5068892.8294 | 9.4647 | 10.4647 | 저가 작품 과대 예측 | large | 3m_10m | oil | canvas | oil__canvas | artist_n_le_5 |  |  |  | 1.8260 | meta_missing |
| cold | test | 14441 | 이준희_A | jun hee lee | triump of sha sha | 1098480.0000 | 9907450.2113 | 8.0192 | 9.0192 | 작가 이력 부족 과대 예측 | large | 3m_10m | acrylic | canvas | acrylic__canvas | artist_n_le_5 |  |  |  | 2.1328 | meta_missing |

## 10. 해석

- Warm은 같은 작가 이력과 유사 작품 묶음 정보가 있어, 표본 수/작가 이력/크기 조합별 원인 분류가 가능
- Cold는 작가 가격 기준선이 없기 때문에, quantile width, 작가 메타 정보 완성도, 크기/재료 조합, source별 차이를 중심으로 원인을 봐야 함
- 전체 지표가 좋아도 특정 구간에서 p95_APE가 커지면 서비스 적용 시 가격 범위와 신뢰도 정책을 함께 조정해야 함
- validation에서 만든 구간 보정이 test에서 개선되지 않으면, 그 원인은 가격 보정보다는 신뢰도/범위 표시 정책으로 처리하는 편이 안전

## 11. 산출물

- `outputs/enriched_error_rows.csv`
- `outputs/overall_metrics.csv`
- `outputs/error_cause_summary.csv`
- `outputs/observable_segment_summary.csv`
- `outputs/correction_candidate_metrics.csv`
- `outputs/correction_mapping_summary.csv`
- `outputs/test_predictions_with_corrections.csv`
- `outputs/top_errors.csv`
