# OP-V01-CAL-01 라벨 검수 기준 평가 분리 결과

## 1. 실행 요약

- 입력 파일: `models/track6/price_prediction_v0.1/operational/outputs/0604_evaluation/operational_predictions_with_actual.csv`
- 숫자 실제 가격 라벨 수: 837건
- Warm/Cold 라우팅: 0604 라벨 보유 행은 모두 Warm으로 평가됨
- 기준 예측값: `service_primary_pred_price_krw`
- 기준 후보: `pp_v8_compact_blend_mape_guarded`
- 이 실험은 예측값을 바꾸지 않고, 평가 그룹만 분리함

## 2. 핵심 결과

| 구분 | MdAPE | MAPE | p95_APE | RMSE_log | 해석 |
| --- | --- | --- | --- | --- | --- |
| 전체 숫자 라벨 | 0.2342 | 14.2852 | 0.9844 | 0.9199 | 50달러 미만 라벨 때문에 MAPE가 크게 왜곡됨 |
| 50달러 이상 | 0.2298 | 0.3359 | 0.9273 | 0.7124 | 저가 이상 라벨을 제외하면 평균 오차가 안정됨 |
| 50달러 이상 10만 달러 미만 | 0.2234 | 0.3308 | 0.8991 | 0.5667 | 일반 운영 평가의 핵심 구간 |
| 50달러 미만 검수 대상 | 495.3133 | 1459.7850 | 5924.4884 | 5.9949 | 가격 단위/라벨 확인이 먼저 필요 |
| 10만 달러 이상 고가 꼬리 | 0.9451 | 0.8577 | 0.9994 | 4.4319 | 고가 작품 과소 예측 방어 대상 |

## 3. 라벨 검수 그룹 분포

| label_qc_bucket | n | actual_usd_median | pred_usd_median | ape_median | ape_mean | svc_group_n_median | price_range_ratio_median |
| --- | --- | --- | --- | --- | --- | --- | --- |
| core_50_to_100k_usd | 821 | 2000.0 | 1707.293558882564 | 0.22337386534740397 | 0.3307995904777072 | 9.0 | 4.825149015199908 |
| review_over_100k_usd | 6 | 310000.0 | 22139.55869103594 | 0.9307137438224886 | 0.81052239073844 | 13.0 | 9.524652544288854 |
| review_over_1m_usd | 2 | 20750000.0 | 11056.035291651964 | 0.9993968793853425 | 0.9993968793853425 | 7.5 | 7.3830904376160955 |
| review_under_50_usd | 8 | 1.0 | 496.4693677428096 | 495.31331963377113 | 1459.7850086198514 | 709.0 | 4.887625105822065 |

## 4. 실제 가격 구간별 지표

| group | candidate | n | MdAPE | MAPE | p95_APE | RMSE_log | median_ratio | over_3x_n | under_1_3x_n | within_5pct_n | range_coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 100k-1m | service_primary | 6 | 0.9307 | 0.8105 | 0.9767 | 2.7973 | 0.0693 | 0 | 5 | 0 | 0.0000 |
| 10k-100k | service_primary | 161 | 0.2496 | 0.3217 | 0.8161 | 0.8212 | 0.7536 | 0 | 28 | 17 | 0.7516 |
| 1m+ | service_primary | 2 | 0.9994 | 0.9994 | 0.9995 | 7.4224 | 0.0006 | 0 | 2 | 0 | 0.0000 |
| 2k-10k | service_primary | 273 | 0.2395 | 0.3094 | 0.8078 | 0.5602 | 0.9027 | 0 | 17 | 32 | 0.8938 |
| 50-500 | service_primary | 95 | 0.3459 | 0.5341 | 1.4228 | 0.4932 | 1.2968 | 2 | 0 | 7 | 0.6526 |
| 500-2k | service_primary | 292 | 0.1863 | 0.2897 | 0.7997 | 0.3980 | 0.9567 | 2 | 6 | 42 | 0.9212 |
| <50 | service_primary | 8 | 495.3133 | 1459.7850 | 5924.4884 | 5.9949 | 496.3133 | 8 | 0 | 0 | 0.0000 |

## 5. 후보별 그룹 지표

| group | candidate | n | MdAPE | MAPE | p95_APE | RMSE_log | median_ratio | over_3x_n | under_1_3x_n | within_5pct_n | range_coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all_numeric_labels | service_primary | 837 | 0.2342 | 14.2852 | 0.9844 | 0.9199 | 0.9341 | 12 | 58 | 98 | 0.8315 |
| actual_50_plus_usd | service_primary | 829 | 0.2298 | 0.3359 | 0.9273 | 0.7124 | 0.9321 | 4 | 58 | 98 | 0.8396 |
| core_50_to_100k_usd | service_primary | 821 | 0.2234 | 0.3308 | 0.8991 | 0.5667 | 0.9341 | 4 | 51 | 98 | 0.8477 |
| review_under_50_usd | service_primary | 8 | 495.3133 | 1459.7850 | 5924.4884 | 5.9949 | 496.3133 | 8 | 0 | 0 | 0.0000 |
| review_over_100k_usd | service_primary | 8 | 0.9451 | 0.8577 | 0.9994 | 4.4319 | 0.0549 | 0 | 7 | 0 | 0.0000 |
| review_over_1m_usd | service_primary | 2 | 0.9994 | 0.9994 | 0.9995 | 7.4224 | 0.0006 | 0 | 2 | 0 | 0.0000 |
| usd_currency | service_primary | 735 | 0.2357 | 16.2285 | 1.0338 | 0.9682 | 0.9364 | 12 | 56 | 89 | 0.8259 |
| non_usd_currency | service_primary | 102 | 0.2209 | 0.2820 | 0.8185 | 0.4342 | 0.9262 | 0 | 2 | 9 | 0.8725 |

## 6. 50달러 미만 검수 대상

| _v01_row_id | _track6_row_id | artist_name | title | actual_currency | actual_price_native | actual_price_krw | actual_price_usd_equiv | service_primary_pred_price_krw | service_primary_ape | service_primary_ratio | label_qc_bucket | warm_cold_route | service_primary_candidate | svc_group_level | svc_group_n | medium_support_bucket | area_cm2 | l10_price_range_ratio | service_confidence_tier |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6263 | 6263 | Jae Youl Jeoung | Temporal wall | USD | 1.0 | 1380.0 | 1.0 | 11103777.59866642 | 8045.215651207551 | 8046.215651207551 | review_under_50_usd | warm | pp_v8_compact_blend_mape_guarded | artist | 10.0 | other__metal | 62100.0 | 15.700928831700248 | low |
| 6262 | 6262 | Jae Youl Jeoung | A star written in Braille | USD | 1.0 | 1380.0 | 1.0 | 2742052.8606219245 | 1985.9948265376263 | 1986.9948265376263 | review_under_50_usd | warm | pp_v8_compact_blend_mape_guarded | artist | 10.0 | other__other | 6900.0 | 4.819281414182496 | medium |
| 4077 | 4077 | Jeongyoon Park | hot wind | USD | 1.0 | 1380.0 | 1.0 | 797371.3967229039 | 576.8053599441333 | 577.8053599441333 | review_under_50_usd | warm | pp_v8_compact_blend_mape_guarded | medium_size | 1408.0 | acrylic__linen | 820.75 | 4.955968797461634 | medium |
| 6264 | 6264 | Jae Youl Jeoung | small talk | USD | 1.0 | 1380.0 | 1.0 | 748219.7624463186 | 541.1882336567527 | 542.1882336567527 | review_under_50_usd | warm | pp_v8_compact_blend_mape_guarded | artist_size | 8.0 | other__paper | 375.0 | 5.301075569547221 | low |
| 6265 | 6265 | Jae Youl Jeoung | A star written in Braille: Notes of the Star | USD | 1.0 | 1380.0 | 1.0 | 621604.9997428895 | 449.4384056107895 | 450.4384056107895 | review_under_50_usd | warm | pp_v8_compact_blend_mape_guarded | artist_size | 8.0 | other__paper | 273.0 | 5.479015723857468 | low |
| 115 | 115 | HWAYEON | Happy Virus | USD | 10.0 | 13800.0 | 10.0 | 622035.6925238357 | 44.07505018288664 | 45.07505018288664 | review_under_50_usd | warm | pp_v8_compact_blend_mape_guarded | global | 26914.0 | other__other |  | 3.479112375368812 | high |
| 113 | 113 | HWAYEON | 治葬 | USD | 20.0 | 27600.0 | 20.0 | 622035.6925238357 | 21.53752509144332 | 22.53752509144332 | review_under_50_usd | warm | pp_v8_compact_blend_mape_guarded | global | 26914.0 | other__other |  | 3.479112375368812 | high |
| 114 | 114 | HWAYEON | Tin Head | USD | 30.0 | 41400.0 | 30.0 | 622035.6925238357 | 14.02501672762888 | 15.02501672762888 | review_under_50_usd | warm | pp_v8_compact_blend_mape_guarded | global | 26914.0 | other__other |  | 3.479112375368812 | high |

## 7. 10만 달러 이상 고가 꼬리 대상

| _v01_row_id | _track6_row_id | artist_name | title | actual_currency | actual_price_native | actual_price_krw | actual_price_usd_equiv | service_primary_pred_price_krw | service_primary_ape | service_primary_ratio | label_qc_bucket | warm_cold_route | service_primary_candidate | svc_group_level | svc_group_n | medium_support_bucket | area_cm2 | l10_price_range_ratio | service_confidence_tier |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5752 | 5752 | Bahk Younghoon | Invisible precious things NO.002 | USD | 40000000.0 | 55200000000.0 | 40000000.0 | 29109338.24444378 | 0.9994726569158616 | 0.0005273430841384 | review_over_1m_usd | warm | pp_v8_compact_blend_mape_guarded | artist | 6.0 | mixed__panel | 15714.0 | 9.933026017965144 | low |
| 6423 | 6423 | Hwi Kim | Surreal | USD | 1500000.0 | 2070000000.0 | 1500000.0 | 1405319.1605156418 | 0.9993211018548234 | 0.0006788981451766 | review_over_1m_usd | warm | pp_v8_compact_blend_mape_guarded | artist_medium_support_size | 9.0 | acrylic__canvas | 6608.43 | 4.833154857267046 | low |
| 5302 | 5302 | Seo Jiin | Rainbow breeze | USD | 999999.0 | 1379998620.0 | 999999.0 | 20165614.550864138 | 0.9853872212199284 | 0.0146127787800716 | review_over_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist | 16.0 | pencil__canvas | 49200.0 | 11.986850828327936 | low |
| 2892 | 2892 | Jong Sook Kim | ARTIFICIAL LANDSCAPE–White Material 05 | USD | 950000.0 | 1311000000.0 | 950000.0 | 122192142.97485662 | 0.9067947040618942 | 0.0932052959381057 | review_over_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist_size | 10.0 | mixed__canvas | 165256.2 | 15.05002731608292 | low |
| 6600 | 6600 | Park Seo-Bo | Ecriture No. 040710 | USD | 380000.0 | 524400000.0 | 380000.0 | 40939567.436395064 | 0.921930649434792 | 0.0780693505652079 | review_over_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist_size | 8.0 | mixed__paper | 21060.0 | 7.062454260249771 | low |
| 6444 | 6444 | Kim Chong Hak | Summer Gaewoon | USD | 240000.0 | 331200000.0 | 240000.0 | 20038647.184786685 | 0.9394968382101851 | 0.0605031617898148 | review_over_100k_usd | warm | pp_v8_compact_blend_mape_guarded | medium_support_size | 1457.0 | oil__canvas | 36000.0 | 12.068525331789864 | low |
| 3194 | 3194 | Hyungdae KIM 김형대 | HALO 08-424 | USD | 128000.0 | 176640000.0 | 128000.0 | 148584923.44548067 | 0.158826293900132 | 0.841173706099868 | review_over_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist_medium_support_size | 9.0 | acrylic__canvas | 19600.0 | 6.6222002876310695 | low |
| 6599 | 6599 | Park Seo-Bo | Ecriture No.040412 | USD | 120000.0 | 165600000.0 | 120000.0 | 8164305.612825937 | 0.950698637603708 | 0.0493013623962918 | review_over_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist | 21.0 | other__paper | 2397.85 | 5.357241076932739 | medium |

## 8. 후속 보정 타겟

| _v01_row_id | _track6_row_id | artist_name | title | actual_currency | actual_price_native | actual_price_krw | actual_price_usd_equiv | service_primary_pred_price_krw | service_primary_ape | service_primary_ratio | label_qc_bucket | warm_cold_route | service_primary_candidate | svc_group_level | svc_group_n | medium_support_bucket | area_cm2 | l10_price_range_ratio | service_confidence_tier |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 24 | 24 | Dahee Yang | Glass | USD | 110.0 | 151800.0 | 110.0 | 643691.2581812664 | 3.240390370100569 | 4.240390370100569 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist | 9.0 | oil__canvas | 358.66 | 5.4026526063840326 | low |
| 928 | 928 | Beomsik Won | Archisculpture 032 | USD | 500.0 | 690000.0 | 500.0 | 2767337.161321464 | 3.0106335671325564 | 4.010633567132556 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist | 13.0 | other__paper | 1150.0 | 6.067943220396942 | medium |
| 3176 | 3176 | Gilyoung JUNG 정길영 | Cutlery Rest Set (4pcs) | USD | 100.0 | 138000.0 | 100.0 | 437393.84970328794 | 2.1695206500238258 | 3.1695206500238258 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist | 5.0 | other__other | 20.0 | 8.128968641913488 | low |
| 3645 | 3645 | Sohyun Park | Cartographie Memoire_St. Etienne | USD | 1100.0 | 1518000.0 | 1100.0 | 4717581.670806987 | 2.1077613114670535 | 3.1077613114670535 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist | 10.0 | acrylic__paper | 10800.0 | 4.253478781429246 | medium |
| 5752 | 5752 | Bahk Younghoon | Invisible precious things NO.002 | USD | 40000000.0 | 55200000000.0 | 40000000.0 | 29109338.24444378 | 0.9994726569158616 | 0.0005273430841384 | review_over_1m_usd | warm | pp_v8_compact_blend_mape_guarded | artist | 6.0 | mixed__panel | 15714.0 | 9.933026017965144 | low |
| 6423 | 6423 | Hwi Kim | Surreal | USD | 1500000.0 | 2070000000.0 | 1500000.0 | 1405319.1605156418 | 0.9993211018548234 | 0.0006788981451766 | review_over_1m_usd | warm | pp_v8_compact_blend_mape_guarded | artist_medium_support_size | 9.0 | acrylic__canvas | 6608.43 | 4.833154857267046 | low |
| 5302 | 5302 | Seo Jiin | Rainbow breeze | USD | 999999.0 | 1379998620.0 | 999999.0 | 20165614.550864138 | 0.9853872212199284 | 0.0146127787800716 | review_over_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist | 16.0 | pencil__canvas | 49200.0 | 11.986850828327936 | low |
| 6446 | 6446 | Yun Hyong-keun | Work | USD | 61000.0 | 84180000.0 | 61000.0 | 1593915.5418623472 | 0.9810653891439493 | 0.0189346108560506 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | medium_support_size | 58.0 | oil__paper | 1922.0 | 5.026726247411207 | medium |
| 2885 | 2885 | Jeon Byeong Sam | COSMOS 220830002 | USD | 25000.0 | 34500000.0 | 25000.0 | 1542872.686140423 | 0.95527905257564 | 0.04472094742436 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist | 45.0 | other__other |  | 3.1876701305221 | high |
| 6599 | 6599 | Park Seo-Bo | Ecriture No.040412 | USD | 120000.0 | 165600000.0 | 120000.0 | 8164305.612825937 | 0.950698637603708 | 0.0493013623962918 | review_over_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist | 21.0 | other__paper | 2397.85 | 5.357241076932739 | medium |
| 6444 | 6444 | Kim Chong Hak | Summer Gaewoon | USD | 240000.0 | 331200000.0 | 240000.0 | 20038647.184786685 | 0.9394968382101851 | 0.0605031617898148 | review_over_100k_usd | warm | pp_v8_compact_blend_mape_guarded | medium_support_size | 1457.0 | oil__canvas | 36000.0 | 12.068525331789864 | low |
| 6445 | 6445 | Lee Kang So | From an Island-02094 | USD | 37500.0 | 51750000.0 | 37500.0 | 3691262.692802173 | 0.9286712523130014 | 0.0713287476869985 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | medium_support_size | 1388.0 | oil__canvas | 3721.0 | 6.947926756892515 | medium |
| 3177 | 3177 | Gilyoung JUNG 정길영 | Dinnerware for 2 | USD | 4000.0 | 5520000.0 | 4000.0 | 412133.91451814625 | 0.925338058964104 | 0.074661941035896 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist | 5.0 | other__other | 1.0 | 5.541688481112945 | low |
| 6600 | 6600 | Park Seo-Bo | Ecriture No. 040710 | USD | 380000.0 | 524400000.0 | 380000.0 | 40939567.436395064 | 0.921930649434792 | 0.0780693505652079 | review_over_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist_size | 8.0 | mixed__paper | 21060.0 | 7.062454260249771 | low |
| 70 | 70 | Yuyeol Byeon | Impression, Algorithm and Nature — Ocean Waves II | USD | 8070.0 | 11136600.0 | 8070.0 | 939621.2023048744 | 0.915627641981855 | 0.084372358018145 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | global | 26914.0 | other__paper |  | 8.65190240424248 | low |
| 2892 | 2892 | Jong Sook Kim | ARTIFICIAL LANDSCAPE–White Material 05 | USD | 950000.0 | 1311000000.0 | 950000.0 | 122192142.97485662 | 0.9067947040618942 | 0.0932052959381057 | review_over_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist_size | 10.0 | mixed__canvas | 165256.2 | 15.05002731608292 | low |
| 83 | 83 | Yuyeol Byeon | IMPRESSION, Algorithm and Nature | USD | 6750.0 | 9315000.0 | 6750.0 | 939621.2023048744 | 0.8991281586360843 | 0.1008718413639156 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | global | 26914.0 | other__paper |  | 8.65190240424248 | low |
| 82 | 82 | Yuyeol Byeon | IMPRESSION, Algorithm and Nature - Ocean Wave | USD | 6750.0 | 9315000.0 | 6750.0 | 939621.2023048744 | 0.8991281586360843 | 0.1008718413639156 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | global | 26914.0 | other__paper |  | 8.65190240424248 | low |
| 5300 | 5300 | Jung Kwangmin | The Filled Void_lotus | USD | 9000.0 | 12420000.0 | 9000.0 | 1300678.601603679 | 0.8952754749111369 | 0.104724525088863 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist | 17.0 | other__other |  | 4.026851556546105 | medium |
| 6447 | 6447 | Lee Bae | Brushstroke 13 | USD | 61000.0 | 84180000.0 | 61000.0 | 9139462.539740477 | 0.8914295255435915 | 0.1085704744564086 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist_size | 18.0 | pencil__paper | 6732.0 | 4.911883714221825 | medium |
| 5756 | 5756 | Bahk Younghoon | Invisible precious things _blue  | KRW | 40000000.0 | 40000000.0 | 28985.507246376812 | 4416942.2819766095 | 0.8895764429505847 | 0.1104235570494152 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist | 6.0 | mixed__panel | 1571400.0 | 19.249780555708284 | low |
| 6601 | 6601 | Lee Kang So | From An Island - 02013 | USD | 65000.0 | 89700000.0 | 65000.0 | 10742970.27993881 | 0.880234445039701 | 0.1197655549602988 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | medium_support_size | 1457.0 | oil__canvas | 10619.7 | 6.814561397407778 | medium |
| 136 | 136 | Hye Rim Baek | Mom's Sunflower | USD | 25300.0 | 34914000.0 | 25300.0 | 4730463.445491181 | 0.8645109856936707 | 0.1354890143063293 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist | 5.0 | ink__paper | 19200.0 | 8.674739930101822 | low |
| 4536 | 4536 | Hong Kyoung Tack | Pens+Funkchestra | KRW | 25000000.0 | 25000000.0 | 18115.942028985508 | 3945272.550453687 | 0.8421890979818526 | 0.1578109020181475 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist | 5.0 | acrylic__linen |  | 11.294020585927466 | low |
| 952 | 952 | YOON JUNGHEE | 7 Square Loops (Blue) | USD | 32000.0 | 44160000.0 | 32000.0 | 8119678.415040736 | 0.8161304706738963 | 0.1838695293261036 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist | 13.0 | other__other | 2585.0 | 6.783689868455591 | medium |
| 5119 | 5119 | Jeong Yeon Kim | Composition No19 | USD | 31690.0 | 43732200.0 | 31690.0 | 8324286.7871312285 | 0.8096531437446269 | 0.1903468562553731 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist | 5.0 | acrylic__canvas | 21134.66 | 4.678128210162464 | low |
| 953 | 953 | YOON JUNGHEE | Tension Blue 55 (Straight) | USD | 7000.0 | 9660000.0 | 7000.0 | 1850551.9797831855 | 0.808431472072134 | 0.191568527927866 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist_size | 8.0 | other__other | 542.75 | 9.747947260225155 | low |
| 5673 | 5673 | Lee Bae | Untitled 2008 | USD | 19000.0 | 26220000.0 | 19000.0 | 5302889.511190308 | 0.7977540232192865 | 0.2022459767807135 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist | 30.0 | acrylic__canvas | 2411.5 | 5.167231217216254 | medium |
| 5244 | 5244 | Sylbee Kim | Trinity: Finance-Credo-Spirituality | USD | 13000.0 | 17940000.0 | 13000.0 | 3701941.356716381 | 0.7936487538062218 | 0.2063512461937782 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist | 6.0 | other__paper |  | 8.720382472316857 | low |
| 5243 | 5243 | Sylbee Kim | Garden of Regrets | USD | 13000.0 | 17940000.0 | 13000.0 | 3701941.356716381 | 0.7936487538062218 | 0.2063512461937782 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist | 6.0 | other__paper |  | 8.720382472316857 | low |
| 6595 | 6595 | Kim Chun Hwan | V4. Kaleidoscope 230203 | USD | 54000.0 | 74520000.0 | 54000.0 | 16223150.546338338 | 0.7822980334629853 | 0.2177019665370147 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | global | 26914.0 | mixed__paper | 18144.0 | 12.51323540430979 | low |
| 6205 | 6205 | Heesook HAN | 빛의 바다에 물들다 | USD | 50000.0 | 69000000.0 | 50000.0 | 15107606.872070571 | 0.7810491757670931 | 0.2189508242329068 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist | 6.0 | mixed__canvas | 40000.0 | 10.49632569415537 | low |
| 5411 | 5411 | INAE | Memory_you | USD | 30000.0 | 41400000.0 | 30000.0 | 9316217.778233428 | 0.7749705850668254 | 0.2250294149331745 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | medium_support_size | 1275.0 | acrylic__canvas | 18144.0 | 6.207430357826352 | medium |
| 3629 | 3629 | Nam Kyoung Kim | The Moon Within My Times | USD | 3800.0 | 5244000.0 | 3800.0 | 1200815.5926926753 | 0.7710115193187118 | 0.2289884806812882 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist_size | 5.0 | other__other | 2025.0 | 3.896851918110939 | low |
| 4322 | 4322 | ZikSeong Jeong | 202010 | USD | 88000.0 | 121440000.0 | 88000.0 | 29177112.3673713 | 0.7597405108088662 | 0.2402594891911338 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist_size | 33.0 | pigment__canvas | 19280.0 | 6.816457893385438 | medium |
| 4331 | 4331 | ZikSeong Jeong | 202011 | USD | 88000.0 | 121440000.0 | 88000.0 | 29177112.3673713 | 0.7597405108088662 | 0.2402594891911338 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist_size | 33.0 | pigment__canvas | 19280.0 | 6.816457893385438 | medium |
| 951 | 951 | YOON JUNGHEE | 7 Square Loops (Blue) | USD | 24000.0 | 33120000.0 | 24000.0 | 8119678.415040736 | 0.7548406275651952 | 0.2451593724348048 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist | 13.0 | other__other | 2585.0 | 6.783689868455591 | medium |
| 69 | 69 | Yuyeol Byeon | Impression, Algorithm and Nature — Ocean Waves II (Edition 1 of 3) | USD | 2700.0 | 3726000.0 | 2700.0 | 939621.2023048744 | 0.7478203965902108 | 0.2521796034097892 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | global | 26914.0 | other__paper |  | 8.65190240424248 | low |
| 6593 | 6593 | Kim Chun Hwan | V9. Undercurrent 260316 | USD | 54000.0 | 74520000.0 | 54000.0 | 18962566.742714625 | 0.7455372149394173 | 0.2544627850605827 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | medium_size | 81.0 | other__paper | 15714.0 | 10.725568921144456 | low |
| 6267 | 6267 | Jeong Zik Seong | 201932 | USD | 9900.0 | 13662000.0 | 9900.0 | 3735486.690097432 | 0.7265783421096887 | 0.2734216578903112 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | global | 26914.0 | pigment__canvas | 3880.0 | 8.057174033810828 | low |
| 6268 | 6268 | Jeong Zik Seong | 201930 | USD | 9900.0 | 13662000.0 | 9900.0 | 3735486.690097432 | 0.7265783421096887 | 0.2734216578903112 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | global | 26914.0 | pigment__canvas | 3880.0 | 8.057174033810828 | low |
| 6421 | 6421 | Hwi Kim | Collapse of Petals | USD | 1052.0 | 1451760.0 | 1052.0 | 407031.09464973345 | 0.7196292123699968 | 0.2803707876300032 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist | 9.0 | mixed__other | 1.0 | 4.760281120944141 | low |
| 6420 | 6420 | Hwi Kim | Evasive Bloom | USD | 1052.0 | 1451760.0 | 1052.0 | 407031.09464973345 | 0.7196292123699968 | 0.2803707876300032 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist | 9.0 | mixed__other | 1.0 | 4.760281120944141 | low |
| 6422 | 6422 | Hwi Kim | ballet dancer | USD | 1052.0 | 1451760.0 | 1052.0 | 407031.09464973345 | 0.7196292123699968 | 0.2803707876300032 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist | 9.0 | mixed__other | 1.0 | 4.760281120944141 | low |
| 3099 | 3099 | Choi Moon Seok | Chaos in cycle | USD | 3600.0 | 4968000.0 | 3600.0 | 1426288.0609001392 | 0.7129049796899881 | 0.2870950203100119 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | artist | 19.0 | other__metal | 600.0 | 14.063008575857168 | low |
| 6587 | 6587 | Kim Chun Hwan | V5. Undercurrent 260314 | USD | 5400.0 | 7452000.0 | 5400.0 | 2208433.3067953433 | 0.703645557327517 | 0.296354442672483 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | medium_size | 107.0 | other__paper | 2173.0 | 8.646949325109881 | low |
| 6594 | 6594 | Kim Chun Hwan | V3. Undercurrent 2024 | USD | 5400.0 | 7452000.0 | 5400.0 | 2208433.3067953433 | 0.703645557327517 | 0.296354442672483 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | medium_size | 107.0 | other__paper | 2173.0 | 8.646949325109881 | low |
| 6592 | 6592 | Kim Chun Hwan | V6. Undercurrent 260315 | USD | 5400.0 | 7452000.0 | 5400.0 | 2208433.3067953433 | 0.703645557327517 | 0.296354442672483 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | medium_size | 107.0 | other__paper | 2173.0 | 8.646949325109881 | low |
| 6590 | 6590 | Kim Chun Hwan | V2. Undercurrent 2024 | USD | 5400.0 | 7452000.0 | 5400.0 | 2208433.3067953433 | 0.703645557327517 | 0.296354442672483 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | medium_size | 107.0 | other__paper | 2173.0 | 8.646949325109881 | low |
| 6588 | 6588 | Kim Chun Hwan | V1. Undercurrent 260314 | USD | 5400.0 | 7452000.0 | 5400.0 | 2208433.3067953433 | 0.703645557327517 | 0.296354442672483 | core_50_to_100k_usd | warm | pp_v8_compact_blend_mape_guarded | medium_size | 107.0 | other__paper | 2173.0 | 8.646949325109881 | low |

## 9. 판단

- 0604 전체 MAPE는 모델 성능만의 문제가 아니라, 매우 낮은 실제 가격 라벨의 영향이 크다.
- 50달러 미만 라벨은 가격 단위, 수집 라벨, 판매 메시지 해석을 먼저 검수해야 한다.
- 일반 운영 구간은 50달러 이상 10만 달러 미만으로 분리해서 보는 것이 더 현실적이다.
- 고가 작품은 점가격을 바로 올리기보다 가격 범위 상단, 신뢰도, 고가 가능성 플래그부터 보정하는 편이 안전하다.
- 다음 실험은 저가/소형 과대 예측 방어와 고가 과소 예측 방어를 분리해서 진행한다.

## 10. 산출물

- `outputs/label_qc_flags.csv`
- `outputs/metrics_by_candidate_group.csv`
- `outputs/metrics_by_group_service_primary.csv`
- `outputs/metrics_by_actual_usd_band.csv`
- `outputs/label_qc_summary.csv`
- `outputs/review_under_50_usd.csv`
- `outputs/review_over_100k_usd.csv`
- `outputs/next_correction_targets.csv`
- `reports/result_report.md`
- `reports/result_report.html`
