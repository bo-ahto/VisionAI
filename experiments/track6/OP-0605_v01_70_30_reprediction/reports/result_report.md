# v0.1 70:30 재예측 비교 결과

- 작성일: 2026-06-05T11:33:23
- 예측 파일: `experiments/track6/OP-0605_v01_70_30_reprediction/outputs/predictions/predictions_all.csv`
- 라벨 파일: `data/test_new_artworks_test_0604.csv`
- 전체 행: 6,873
- 숫자 가격 라벨: 837
- 50달러 미만 검수 필요 라벨: 8
- PP-V8 component 재현 방식: PP-V8 원천 후보 전체가 단일 artifact로 없어 기존 PP-V8 예측값을 모사한 component
- PP-V8 component fidelity: test RMSE_log `0.3427`, MdAE_log `0.1521`

## 1. 실행 해석

- `v01_70_30_repred`: v0.1 정책 식 `70% svc_numeric_seed_mean + 30% PP-V8 component`를 적용한 재예측 후보
- `PP-V8 component`: 원천 후보 전체 artifact가 없어 기존 PP-V8 예측을 CatBoost로 모사한 distillation component
- 따라서 이번 결과는 최종 식을 신규 파일에 적용한 재실행이지만, PP-V8 축은 source-decomposed exact가 아닌 재현용 component임
- 완전한 source-decomposed exact 비교를 위해서는 PP-V8 원천 후보별 신규 데이터 추론 artifact가 추가로 필요함

## 2. 전체 숫자 라벨 기준

| scope | candidate | n | MdAPE | MAPE | p95_APE | RMSE_log | median_ratio | over_3x_n | under_1_3x_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| numeric_actual_all | pp_v8_distilled_component | 837 | 0.2301 | 13.6783 | 1.2603 | 0.9302 | 0.9736 | 15 | 44 |
| numeric_actual_all | v01_70_30_repred | 837 | 0.2739 | 30.8957 | 1.0000 | 1.3031 | 0.9283 | 17 | 79 |
| numeric_actual_all | svc_numeric_seed_mean | 837 | 0.3174 | 47.2696 | 1.0882 | 1.4258 | 0.9254 | 19 | 108 |
| numeric_actual_all | legacy_log_blend_svc0p7_huber0p3 | 837 | 0.3694 | 4.9034 | 2.1343 | 1.2001 | 0.9514 | 50 | 90 |
| numeric_actual_all | svc_group_median | 837 | 0.3750 | 3.1595 | 4.5873 | 1.1688 | 1.0000 | 77 | 103 |
| numeric_actual_all | legacy_warm_huber | 837 | 0.5532 | 94.7422 | 2.3912 | 1.4930 | 0.9526 | 56 | 120 |

## 3. 50달러 미만 검수 필요 라벨 제외 기준

| scope | candidate | n | MdAPE | MAPE | p95_APE | RMSE_log | median_ratio | over_3x_n | under_1_3x_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| numeric_actual_excluding_under_50_usd | pp_v8_distilled_component | 829 | 0.2285 | 0.3547 | 1.1018 | 0.7033 | 0.9687 | 7 | 44 |
| numeric_actual_excluding_under_50_usd | v01_70_30_repred | 829 | 0.2708 | 0.3773 | 0.9946 | 1.1462 | 0.9282 | 9 | 79 |
| numeric_actual_excluding_under_50_usd | svc_numeric_seed_mean | 829 | 0.3072 | 0.4318 | 0.9998 | 1.2810 | 0.9204 | 11 | 108 |
| numeric_actual_excluding_under_50_usd | legacy_log_blend_svc0p7_huber0p3 | 829 | 0.3656 | 0.6224 | 1.9915 | 1.0684 | 0.9486 | 42 | 90 |
| numeric_actual_excluding_under_50_usd | svc_group_median | 829 | 0.3714 | 0.8681 | 3.6706 | 1.0491 | 1.0000 | 69 | 103 |
| numeric_actual_excluding_under_50_usd | legacy_warm_huber | 829 | 0.5480 | 0.7173 | 2.1025 | 1.3491 | 0.9444 | 48 | 120 |

## 4. 주요 segment 비교

| scope | candidate | n | MdAPE | MAPE | p95_APE | RMSE_log | median_ratio | over_3x_n | under_1_3x_n | segment_column | segment_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| actual_price_band=100_500usd | v01_70_30_repred | 104 | 0.2829 | 0.4413 | 1.1951 | 0.5459 | 1.1392 | 3 | 6 | actual_price_band | 100_500usd |
| actual_price_band=100_500usd | legacy_log_blend_svc0p7_huber0p3 | 104 | 0.3503 | 1.3952 | 6.5385 | 0.8899 | 1.3131 | 19 | 0 | actual_price_band | 100_500usd |
| actual_price_band=100_500usd | svc_group_median | 104 | 0.3750 | 2.4381 | 13.8148 | 1.1368 | 1.3189 | 25 | 0 | actual_price_band | 100_500usd |
| actual_price_band=100k_plus_usd | v01_70_30_repred | 8 | 0.9391 | 0.8326 | 0.9993 | 4.2732 | 0.0609 | 0 | 7 | actual_price_band | 100k_plus_usd |
| actual_price_band=100k_plus_usd | legacy_log_blend_svc0p7_huber0p3 | 8 | 0.9562 | 0.8424 | 0.9994 | 4.5956 | 0.0438 | 0 | 7 | actual_price_band | 100k_plus_usd |
| actual_price_band=100k_plus_usd | svc_group_median | 8 | 0.9661 | 0.8571 | 0.9995 | 4.8732 | 0.0339 | 0 | 7 | actual_price_band | 100k_plus_usd |
| actual_price_band=1k_5k_usd | v01_70_30_repred | 285 | 0.2498 | 0.3804 | 1.1172 | 0.7965 | 0.9022 | 3 | 16 | actual_price_band | 1k_5k_usd |
| actual_price_band=1k_5k_usd | legacy_log_blend_svc0p7_huber0p3 | 285 | 0.3344 | 0.5063 | 1.2286 | 0.6423 | 0.9115 | 9 | 17 | actual_price_band | 1k_5k_usd |
| actual_price_band=1k_5k_usd | svc_group_median | 285 | 0.3684 | 0.6542 | 2.2455 | 0.7521 | 1.0000 | 16 | 21 | actual_price_band | 1k_5k_usd |
| actual_price_band=20k_100k_usd | v01_70_30_repred | 65 | 0.4514 | 0.4358 | 0.9238 | 1.7656 | 0.5486 | 0 | 18 | actual_price_band | 20k_100k_usd |
| actual_price_band=20k_100k_usd | legacy_log_blend_svc0p7_huber0p3 | 65 | 0.6148 | 0.5408 | 0.9530 | 1.8698 | 0.3958 | 0 | 26 | actual_price_band | 20k_100k_usd |
| actual_price_band=20k_100k_usd | svc_group_median | 65 | 0.6667 | 0.5967 | 1.2000 | 1.4547 | 0.3800 | 0 | 27 | actual_price_band | 20k_100k_usd |
| actual_price_band=500_1k_usd | legacy_log_blend_svc0p7_huber0p3 | 168 | 0.3049 | 0.6163 | 2.1294 | 0.7098 | 1.0925 | 13 | 3 | actual_price_band | 500_1k_usd |
| actual_price_band=500_1k_usd | v01_70_30_repred | 168 | 0.3143 | 0.3629 | 0.9835 | 0.8925 | 0.9699 | 3 | 11 | actual_price_band | 500_1k_usd |
| actual_price_band=500_1k_usd | svc_group_median | 168 | 0.3301 | 0.8846 | 4.4881 | 0.7631 | 1.0000 | 26 | 11 | actual_price_band | 500_1k_usd |
| actual_price_band=5k_20k_usd | v01_70_30_repred | 195 | 0.2252 | 0.3112 | 0.7966 | 1.4216 | 0.9502 | 0 | 21 | actual_price_band | 5k_20k_usd |
| actual_price_band=5k_20k_usd | legacy_log_blend_svc0p7_huber0p3 | 195 | 0.3507 | 0.3866 | 0.8593 | 1.1596 | 0.8215 | 0 | 37 | actual_price_band | 5k_20k_usd |
| actual_price_band=5k_20k_usd | svc_group_median | 195 | 0.3529 | 0.3977 | 0.9462 | 0.9786 | 1.0000 | 0 | 37 | actual_price_band | 5k_20k_usd |
| svc_coverage_tier=fallback_global | svc_group_median | 18 | 0.2824 | 0.6847 | 1.6566 | 1.1502 | 0.9487 | 1 | 6 | svc_coverage_tier | fallback_global |
| svc_coverage_tier=fallback_global | legacy_log_blend_svc0p7_huber0p3 | 18 | 0.4329 | 0.6309 | 1.3249 | 1.1554 | 0.7720 | 1 | 7 | svc_coverage_tier | fallback_global |
| svc_coverage_tier=fallback_global | v01_70_30_repred | 18 | 0.6374 | 0.6800 | 0.9449 | 1.2345 | 0.3883 | 0 | 7 | svc_coverage_tier | fallback_global |
| svc_coverage_tier=high_n | v01_70_30_repred | 87 | 0.4879 | 0.5638 | 1.2301 | 1.0413 | 0.6649 | 0 | 18 | svc_coverage_tier | high_n |
| svc_coverage_tier=high_n | svc_group_median | 87 | 0.5114 | 0.5366 | 1.0730 | 1.0263 | 0.7648 | 0 | 15 | svc_coverage_tier | high_n |
| svc_coverage_tier=high_n | legacy_log_blend_svc0p7_huber0p3 | 87 | 0.5205 | 0.5311 | 1.0948 | 1.0118 | 0.8733 | 0 | 13 | svc_coverage_tier | high_n |
| svc_coverage_tier=low_n | v01_70_30_repred | 569 | 0.2489 | 0.3495 | 0.9664 | 1.2493 | 0.9282 | 6 | 45 | svc_coverage_tier | low_n |
| svc_coverage_tier=low_n | legacy_log_blend_svc0p7_huber0p3 | 569 | 0.3241 | 0.6153 | 1.9141 | 1.1271 | 0.9361 | 28 | 59 | svc_coverage_tier | low_n |
| svc_coverage_tier=low_n | svc_group_median | 569 | 0.3333 | 0.8666 | 3.0784 | 1.0509 | 1.0000 | 42 | 70 | svc_coverage_tier | low_n |
| svc_coverage_tier=medium_n | v01_70_30_repred | 155 | 0.2516 | 0.3393 | 0.8764 | 0.7156 | 0.9687 | 3 | 9 | svc_coverage_tier | medium_n |
| svc_coverage_tier=medium_n | legacy_log_blend_svc0p7_huber0p3 | 155 | 0.3894 | 0.6989 | 2.1406 | 0.8439 | 1.0730 | 13 | 11 | svc_coverage_tier | medium_n |
| svc_coverage_tier=medium_n | svc_group_median | 155 | 0.5000 | 1.0806 | 4.8000 | 1.0427 | 1.1765 | 26 | 12 | svc_coverage_tier | medium_n |
| svc_group_level=artist | v01_70_30_repred | 412 | 0.2885 | 0.3766 | 0.9854 | 1.3148 | 0.9149 | 5 | 33 | svc_group_level | artist |
| svc_group_level=artist | legacy_log_blend_svc0p7_huber0p3 | 412 | 0.5198 | 0.8603 | 2.9481 | 1.2767 | 0.9220 | 38 | 55 | svc_group_level | artist |
| svc_group_level=artist | svc_group_median | 412 | 0.5882 | 1.3555 | 5.5550 | 1.2634 | 1.0000 | 66 | 66 | svc_group_level | artist |
| svc_group_level=artist_medium_support_size | svc_group_median | 91 | 0.1667 | 0.2550 | 0.7188 | 0.8279 | 1.0000 | 0 | 1 | svc_group_level | artist_medium_support_size |
| svc_group_level=artist_medium_support_size | v01_70_30_repred | 91 | 0.1689 | 0.2225 | 0.7521 | 0.7704 | 0.9966 | 0 | 1 | svc_group_level | artist_medium_support_size |
| svc_group_level=artist_medium_support_size | legacy_log_blend_svc0p7_huber0p3 | 91 | 0.1924 | 0.2523 | 0.6372 | 0.7652 | 0.9954 | 0 | 1 | svc_group_level | artist_medium_support_size |
| svc_group_level=artist_size | svc_group_median | 224 | 0.1950 | 0.3653 | 0.9612 | 0.5906 | 1.0000 | 2 | 15 | svc_group_level | artist_size |
| svc_group_level=artist_size | v01_70_30_repred | 224 | 0.2203 | 0.3435 | 0.8489 | 0.9527 | 0.9282 | 4 | 21 | svc_group_level | artist_size |
| svc_group_level=artist_size | legacy_log_blend_svc0p7_huber0p3 | 224 | 0.2206 | 0.3665 | 0.9458 | 0.6964 | 0.9839 | 3 | 14 | svc_group_level | artist_size |
| svc_group_level=global | svc_group_median | 18 | 0.2824 | 0.6847 | 1.6566 | 1.1502 | 0.9487 | 1 | 6 | svc_group_level | global |
| svc_group_level=global | legacy_log_blend_svc0p7_huber0p3 | 18 | 0.4329 | 0.6309 | 1.3249 | 1.1554 | 0.7720 | 1 | 7 | svc_group_level | global |
| svc_group_level=global | v01_70_30_repred | 18 | 0.6374 | 0.6800 | 0.9449 | 1.2345 | 0.3883 | 0 | 7 | svc_group_level | global |
| svc_group_level=medium_size | svc_group_median | 18 | 0.7623 | 0.6316 | 1.0033 | 1.0758 | 0.5487 | 0 | 8 | svc_group_level | medium_size |
| svc_group_level=medium_size | v01_70_30_repred | 18 | 0.7724 | 0.6966 | 0.9370 | 1.2749 | 0.2334 | 0 | 12 | svc_group_level | medium_size |
| svc_group_level=medium_size | legacy_log_blend_svc0p7_huber0p3 | 18 | 0.7820 | 0.6371 | 1.1213 | 1.1713 | 0.3479 | 0 | 8 | svc_group_level | medium_size |
| svc_group_level=medium_support_size | legacy_log_blend_svc0p7_huber0p3 | 66 | 0.4428 | 0.5100 | 1.0828 | 0.9854 | 0.9717 | 0 | 5 | svc_group_level | medium_support_size |
| svc_group_level=medium_support_size | v01_70_30_repred | 66 | 0.4435 | 0.5399 | 1.2311 | 0.9766 | 1.0638 | 0 | 5 | svc_group_level | medium_support_size |
| svc_group_level=medium_support_size | svc_group_median | 66 | 0.4495 | 0.4911 | 1.0665 | 1.0271 | 0.7832 | 0 | 7 | svc_group_level | medium_support_size |

## 5. v0.1 70:30 재예측 큰 오차 상위

| _v01_row_id | title | artist_name | sale_message | actual_price_krw | v01_70_30_repred_price_krw | v01_70_30_repred_ape | svc_group_level | svc_group_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6263 | Temporal wall | Jae Youl Jeoung | US$1.00 | 1380.0000 | 28372361.2049 | 20558.6820 | artist | 10.0000 |
| 6262 | A star written in Braille | Jae Youl Jeoung | US$1.00 | 1380.0000 | 3678488.3640 | 2664.5713 | artist | 10.0000 |
| 6264 | small talk | Jae Youl Jeoung | US$1.00 | 1380.0000 | 1149872.8739 | 832.2412 | artist_size | 8.0000 |
| 4077 | hot wind | Jeongyoon Park | US$1.00 | 1380.0000 | 1141488.2240 | 826.1654 | medium_size | 1408.0000 |
| 6265 | A star written in Braille: Notes of the Star | Jae Youl Jeoung | US$1.00 | 1380.0000 | 740284.7087 | 535.4382 | artist_size | 8.0000 |
| 115 | Happy Virus | HWAYEON | US$10.00 | 13800.0000 | 1000068.1684 | 71.4687 | global | 26914.0000 |
| 113 | 治葬 | HWAYEON | US$20.00 | 27600.0000 | 1000068.1684 | 35.2344 | global | 26914.0000 |
| 114 | Tin Head | HWAYEON | US$30.00 | 41400.0000 | 1000068.1684 | 23.1562 | global | 26914.0000 |
| 4098 | T11- W04 | Yeun Song | US$400.00 | 552000.0000 | 2625676.4065 | 3.7567 | artist_size | 5.0000 |
| 928 | Archisculpture 032 | Beomsik Won | US$500.00 | 690000.0000 | 3218357.9959 | 3.6643 | artist | 13.0000 |
| 6144 | Rosetta Stone | Nam June Paik | US$5,000.00 | 6900000.0000 | 29511395.5042 | 3.2770 | artist_size | 12.0000 |
| 6143 | Etching on Etching | Nam June Paik | US$5,000.00 | 6900000.0000 | 29511395.5042 | 3.2770 | artist_size | 12.0000 |
| 4165 | Equation-like Forms | Gyul E Kim | US$2,800.00 | 3864000.0000 | 16357662.7957 | 3.2333 | artist_size | 10.0000 |
| 5409 | The Dust Recorder’s Way of Remembering 202 | Hanna Kim | US$750.00 | 1035000.0000 | 3331386.1458 | 2.2187 | artist | 27.0000 |
| 5407 | The Dust Recorder’s Way of Remembering 222 | Hanna Kim | US$750.00 | 1035000.0000 | 3331386.1458 | 2.2187 | artist | 27.0000 |
| 5408 | The Dust Recorder’s Way of Remembering 221 | Hanna Kim | US$750.00 | 1035000.0000 | 3331386.1458 | 2.2187 | artist | 27.0000 |
| 152 | - [Lucky Symbol '#'] "You, Like #, a Symbol Always Connecting by My Side." | Mi Young Um | US$270.00 | 372600.0000 | 1144900.1536 | 2.0727 | artist | 7.0000 |
| 3645 | Cartographie Memoire_St. Etienne | Sohyun Park | US$1,100.00 | 1518000.0000 | 4430176.7356 | 1.9184 | artist | 10.0000 |
| 5118 | No Tears Left 5cm 2 | Jeong Yeon Kim | US$3,170.00 | 4374600.0000 | 12654128.3103 | 1.8926 | artist | 5.0000 |
| 24 | Glass | Dahee Yang | US$110.00 | 151800.0000 | 411586.6727 | 1.7114 | artist | 9.0000 |
| 5403 | Cake collectors | Nina Park | US$1,500.00 | 2070000.0000 | 5423532.9255 | 1.6201 | medium_support_size | 1512.0000 |
| 42 | Dear | Kwon Oon | US$270.00 | 372600.0000 | 956386.8404 | 1.5668 | medium_size | 103.0000 |
| 4698 | Moonlit Glow | A Jihye | KRW ₩3,500,000 | 3500000.0000 | 8564654.0976 | 1.4470 | artist | 5.0000 |
| 2868 | a picture of a hug | Kim Hyun Jung | US$2,000.00 | 2760000.0000 | 6525614.6684 | 1.3644 | medium_support_size | 1249.0000 |
| 5402 | Feel Like Ice Cream | Nina Park | US$1,800.00 | 2484000.0000 | 5743881.2118 | 1.3124 | medium_support_size | 1512.0000 |
| 47 | Happiness Delivery | Lim Hong | US$540.00 | 745200.0000 | 1680989.9241 | 1.2558 | artist | 9.0000 |
| 48 | Collect Happiness | Lim Hong | US$540.00 | 745200.0000 | 1680989.9241 | 1.2558 | artist | 9.0000 |
| 4527 | Sweet Dreams Await | Hari Im | KRW ₩1,400,000 | 1400000.0000 | 3130667.4896 | 1.2362 | medium_support_size | 1495.0000 |
| 4529 | Momentary Universe  | Hari Im | KRW ₩1,400,000 | 1400000.0000 | 3102301.3719 | 1.2159 | medium_support_size | 1495.0000 |
| 4528 | Radiant | Hari Im | KRW ₩1,400,000 | 1400000.0000 | 3102301.3719 | 1.2159 | medium_support_size | 1495.0000 |
