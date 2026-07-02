# PP-HCOEF15 Warm 최신 라벨 stress test

- 작성일: 2026-06-08 01:26
- 목적: 0604 최신 라벨을 외부 stress test로 사용해 HCOEF 안정 후보와 운영 후보의 차이를 비교
- 기준 후보: `hcoef2_size_reliability_cap005_s050`
- 비교 기준: `current_70_30`
- 후보 선택/보정값 산출에는 0604 라벨을 사용하지 않음
- 0604는 외부 확인용이며 fixed test/OOF 결론을 대체하지 않음

## 1. 실행 결론

- HCOEF 안정 후보는 0604에서 `current_70_30`보다 MdAPE/MAPE/p95가 모두 소폭 개선됨.
- 운영 service primary는 0604에서 HCOEF 안정 후보보다 MdAPE/MAPE/p95가 모두 낮음.
- 다만 service primary는 HCOEF 계열 OOF/fixed test 후보 선택 절차로 검증된 새 Huber 후보가 아니므로 바로 Warm 개선 후보로 승격하지 않음.
- 다음 실험은 service primary 또는 PP-V8 운영 component를 Huber 계수/위험도 피처로 넣고 OOF 기준으로 재검증하는 방향이 적절함.
- 0604 actual price join 검증은 아래와 같음.
  - actual price 일치율: `1.0000`
  - actual price 최대 차이: `0.0000`

## 2. 전체 0604 외부 라벨 성능

| candidate | candidate_source | n | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pp_v2_defensive | operational_v0.1 | 829 | 0.2263 | 0.3623 | 1.0902 | 0.7131 | -0.0467 | -0.0121 | 0.1068 |
| pp_v8_compact_blend_mape_guarded_operational | operational_v0.1 | 829 | 0.2298 | 0.3359 | 0.9273 | 0.7124 | -0.0433 | -0.0385 | -0.0561 |
| service_primary_ppv8_operational | operational_v0.1 | 829 | 0.2298 | 0.3359 | 0.9273 | 0.7124 | -0.0433 | -0.0385 | -0.0561 |
| hcoef14_seg_iqr_cap002_s025 | research_hcoef | 829 | 0.2731 | 0.3741 | 0.9834 | 1.3078 | 0.0000 | -0.0002 | -0.0000 |
| hcoef2_size_reliability_cap005_s050 | research_hcoef | 829 | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 |
| hcoef14_shrink_iqr_mid_high_keep050 | research_hcoef | 829 | 0.2734 | 0.3748 | 0.9833 | 1.3081 | 0.0003 | 0.0004 | -0.0002 |
| current_70_30 | research_hcoef | 829 | 0.2779 | 0.3774 | 0.9871 | 1.3117 | 0.0049 | 0.0030 | 0.0036 |
| v01_operational_70_30 | operational_v0.1 | 829 | 0.2779 | 0.3774 | 0.9871 | 1.3117 | 0.0049 | 0.0030 | 0.0036 |
| svc_numeric_seed_mean | operational_v0.1 | 829 | 0.3072 | 0.4318 | 0.9998 | 1.6906 | 0.0342 | 0.0575 | 0.0163 |
| l10_generated_bucket_seq | operational_v0.1 | 829 | 0.3207 | 0.4598 | 1.2569 | 1.0793 | 0.0477 | 0.0854 | 0.2734 |

## 3. HCOEF 안정 후보 대비 bootstrap

| summary_type | candidate | baseline | point_delta_MdAPE | point_delta_MAPE | point_delta_p95_APE | MdAPE_improve_prob | MAPE_improve_prob | p95_improve_prob | all3_improve_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| row_bootstrap | current_70_30 | hcoef2_size_reliability_cap005_s050 | 0.0049 | 0.0030 | 0.0036 | 0.3020 | 0.0000 | 0.1100 | 0.0000 |
| row_bootstrap | service_primary_ppv8_operational | hcoef2_size_reliability_cap005_s050 | -0.0433 | -0.0385 | -0.0561 | 0.9990 | 1.0000 | 0.8760 | 0.8750 |
| row_bootstrap | v01_operational_70_30 | hcoef2_size_reliability_cap005_s050 | 0.0049 | 0.0030 | 0.0036 | 0.3380 | 0.0000 | 0.1150 | 0.0000 |
| artist_bootstrap | current_70_30 | hcoef2_size_reliability_cap005_s050 | 0.0049 | 0.0030 | 0.0036 | 0.3660 | 0.0130 | 0.2090 | 0.0050 |
| artist_bootstrap | service_primary_ppv8_operational | hcoef2_size_reliability_cap005_s050 | -0.0433 | -0.0385 | -0.0561 | 0.9890 | 0.9940 | 0.7560 | 0.7480 |
| artist_bootstrap | v01_operational_70_30 | hcoef2_size_reliability_cap005_s050 | 0.0049 | 0.0030 | 0.0036 | 0.3580 | 0.0100 | 0.2190 | 0.0020 |

## 4. 잔차 요약

| candidate | n | median_residual_log | mean_residual_log | residual_std | ape_median | ape_mean | ape_p95 | over_2x_n | under_half_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pp_v2_defensive | 829 | 0.0695 | 0.1296 | 0.7012 | 0.2263 | 0.3623 | 1.0902 | 47 | 81 |
| pp_v8_compact_blend_mape_guarded_operational | 829 | 0.0703 | 0.1690 | 0.6921 | 0.2298 | 0.3359 | 0.9273 | 31 | 89 |
| service_primary_ppv8_operational | 829 | 0.0703 | 0.1690 | 0.6921 | 0.2298 | 0.3359 | 0.9273 | 31 | 89 |
| hcoef14_seg_iqr_cap002_s025 | 829 | 0.0608 | 0.3281 | 1.2659 | 0.2731 | 0.3741 | 0.9834 | 26 | 152 |
| hcoef2_size_reliability_cap005_s050 | 829 | 0.0608 | 0.3278 | 1.2660 | 0.2731 | 0.3744 | 0.9835 | 26 | 152 |
| hcoef14_shrink_iqr_mid_high_keep050 | 829 | 0.0608 | 0.3286 | 1.2661 | 0.2734 | 0.3748 | 0.9833 | 26 | 154 |
| current_70_30 | 829 | 0.0782 | 0.3370 | 1.2677 | 0.2779 | 0.3774 | 0.9871 | 30 | 153 |
| v01_operational_70_30 | 829 | 0.0782 | 0.3370 | 1.2677 | 0.2779 | 0.3774 | 0.9871 | 30 | 153 |
| svc_numeric_seed_mean | 829 | 0.0829 | 0.4091 | 1.6404 | 0.3072 | 0.4318 | 0.9998 | 38 | 168 |
| l10_generated_bucket_seq | 829 | 0.0475 | 0.2873 | 1.0403 | 0.3207 | 0.4598 | 1.2569 | 63 | 170 |

## 5. service primary가 HCOEF 안정 후보보다 좋아진 구간

| segment_column | segment_value | n | service_improve_rate_vs_stable | median_service_minus_stable_ape | mean_service_minus_stable_ape | median_service_minus_stable_pred_log |
| --- | --- | --- | --- | --- | --- | --- |
| svc_group_level | medium_support_size | 66 | 0.7273 | -0.0951 | -0.1165 | -0.1081 |
| svc_coverage_tier | high_n | 87 | 0.7701 | -0.0812 | -0.1261 | -0.0198 |
| actual_price_band | 500_1k_usd | 168 | 0.6190 | -0.0736 | -0.0873 | 0.0678 |
| service_confidence_tier | high | 22 | 0.6818 | -0.0646 | -0.1468 | -0.1035 |
| actual_price_band | 1k_5k_usd | 285 | 0.5825 | -0.0130 | -0.0748 | 0.0024 |
| service_confidence_tier | medium | 308 | 0.5325 | -0.0075 | -0.0653 | -0.0122 |
| svc_group_level | artist | 412 | 0.5097 | -0.0028 | -0.0219 | -0.0013 |
| service_confidence_tier | low | 499 | 0.5090 | -0.0018 | -0.0172 | 0.0161 |
| svc_group_level | artist_medium_support_size | 91 | 0.5165 | -0.0014 | -0.0330 | 0.0020 |
| svc_coverage_tier | low_n | 569 | 0.4938 | 0.0003 | -0.0155 | 0.0091 |
| actual_price_band | 100_500usd | 104 | 0.4808 | 0.0021 | 0.0551 | 0.1465 |
| actual_price_band | 20k_100k_usd | 65 | 0.4923 | 0.0026 | -0.0164 | 0.0090 |
| svc_coverage_tier | medium_n | 155 | 0.4774 | 0.0095 | -0.0745 | -0.0123 |
| svc_group_level | artist_size | 224 | 0.4464 | 0.0119 | -0.0380 | 0.0749 |
| actual_price_band | 5k_20k_usd | 195 | 0.4051 | 0.0119 | -0.0238 | -0.0123 |

## 6. service primary 개선 상위 작품

| _track6_row_id | title | artist_name | actual_price_krw | actual_price_usd_equiv | svc_group_level | svc_coverage_tier | svc_group_n | actual_price_band | hcoef2_size_reliability_cap005_s050_pred_price_krw | hcoef2_size_reliability_cap005_s050_ape | service_primary_ppv8_operational_pred_price_krw | service_primary_ppv8_operational_ape | service_minus_stable_ape |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4098 | T11- W04 | Yeun Song | 552000.0000 | 400.0000 | artist_size | low_n | 5.0000 | 100_500usd | 2858558.4132 | 4.1785 | 1474200.7414 | 1.6707 | -2.5079 |
| 4165 | Equation-like Forms | Gyul E Kim | 3864000.0000 | 2800.0000 | artist_size | low_n | 10.0000 | 1k_5k_usd | 16788670.0510 | 3.3449 | 9701027.3683 | 1.5106 | -1.8343 |
| 6144 | Rosetta Stone | Nam June Paik | 6900000.0000 | 5000.0000 | artist_size | low_n | 12.0000 | 1k_5k_usd | 28129374.7080 | 3.0767 | 18489371.1055 | 1.6796 | -1.3971 |
| 6143 | Etching on Etching | Nam June Paik | 6900000.0000 | 5000.0000 | artist_size | low_n | 12.0000 | 1k_5k_usd | 28129374.7080 | 3.0767 | 18489371.1055 | 1.6796 | -1.3971 |
| 4698 | Moonlit Glow | A Jihye | 3500000.0000 | 2536.2319 | artist | low_n | 5.0000 | 1k_5k_usd | 8711806.5081 | 1.4891 | 4577997.5601 | 0.3080 | -1.1811 |
| 5407 | The Dust Recorder’s Way of Remembering 222 | Hanna Kim | 1035000.0000 | 750.0000 | artist | medium_n | 27.0000 | 500_1k_usd | 3392177.7265 | 2.2775 | 2356065.1113 | 1.2764 | -1.0011 |
| 5408 | The Dust Recorder’s Way of Remembering 221 | Hanna Kim | 1035000.0000 | 750.0000 | artist | medium_n | 27.0000 | 500_1k_usd | 3392177.7265 | 2.2775 | 2356065.1113 | 1.2764 | -1.0011 |
| 5409 | The Dust Recorder’s Way of Remembering 202 | Hanna Kim | 1035000.0000 | 750.0000 | artist | medium_n | 27.0000 | 500_1k_usd | 3392177.7265 | 2.2775 | 2356065.1113 | 1.2764 | -1.0011 |
| 4999 | Twilight | Moon Eunchae | 1104000.0000 | 800.0000 | artist | low_n | 5.0000 | 500_1k_usd | 50125.0418 | 0.9546 | 1007009.2142 | 0.0879 | -0.8667 |
| 152 | - [Lucky Symbol '#'] "You, Like #, a Symbol Always Connecting by My Side." | Mi Young Um | 372600.0000 | 270.0000 | artist | low_n | 7.0000 | 100_500usd | 1119326.5680 | 2.0041 | 878897.9737 | 1.3588 | -0.6453 |
| 5401 | With my friend | Nina Park | 483000.0000 | 350.0000 | medium_support_size | high_n | 1115.0000 | 100_500usd | 952990.9015 | 0.9731 | 650067.1374 | 0.3459 | -0.6272 |
| 5403 | Cake collectors | Nina Park | 2070000.0000 | 1500.0000 | medium_support_size | high_n | 1512.0000 | 1k_5k_usd | 5050799.8733 | 1.4400 | 3764431.6820 | 0.8186 | -0.6214 |
| 5402 | Feel Like Ice Cream | Nina Park | 2484000.0000 | 1800.0000 | medium_support_size | high_n | 1512.0000 | 1k_5k_usd | 5398298.4628 | 1.1732 | 3866998.7402 | 0.5568 | -0.6165 |
| 6495 | where to go | Qwaya | 828000.0000 | 600.0000 | artist | low_n | 11.0000 | 500_1k_usd | 185156.4746 | 0.7764 | 679003.6152 | 0.1799 | -0.5964 |
| 42 | Dear | Kwon Oon | 372600.0000 | 270.0000 | medium_size | high_n | 103.0000 | 100_500usd | 848025.4432 | 1.2760 | 628986.7322 | 0.6881 | -0.5879 |
| 5760 | the light on the curtain  | Bahk Younghoon | 20700000.0000 | 15000.0000 | artist | low_n | 6.0000 | 5k_20k_usd | 1000.0000 | 1.0000 | 11733494.3839 | 0.4332 | -0.5668 |
| 6169 | Chunju's Multiverse Story- Chunja World 1 | Shin Seung-Hun | 828000.0000 | 600.0000 | artist | medium_n | 15.0000 | 500_1k_usd | 1522163.4108 | 0.8384 | 583496.7644 | 0.2953 | -0.5431 |
| 2869 | warding charm | Do Su Kim | 1449000.0000 | 1050.0000 | artist | low_n | 6.0000 | 1k_5k_usd | 3199857.8007 | 1.2083 | 2416049.4242 | 0.6674 | -0.5409 |
| 2870 | companion plant | Do Su Kim | 1449000.0000 | 1050.0000 | artist | low_n | 6.0000 | 1k_5k_usd | 3199857.8007 | 1.2083 | 2416049.4242 | 0.6674 | -0.5409 |
| 954 | 15 Knots (Gray) | YOON JUNGHEE | 8970000.0000 | 6500.0000 | artist | low_n | 13.0000 | 5k_20k_usd | 3768553.3301 | 0.5799 | 9510750.8211 | 0.0603 | -0.5196 |
| 4534 | 관측과 소화 | Hanna Kim | 13000000.0000 | 9420.2899 | artist_medium_support_size | low_n | 5.0000 | 5k_20k_usd | 22312129.1363 | 0.7163 | 15587495.6443 | 0.1990 | -0.5173 |
| 5332 | Untitled | Jeong Jingab | 4576080.0000 | 3316.0000 | artist_size | low_n | 5.0000 | 1k_5k_usd | 131811.9919 | 0.9712 | 2444377.9725 | 0.4658 | -0.5054 |
| 5293 | WalkingmanHGw | Nam Jeeyeon | 621000.0000 | 450.0000 | artist_medium_support_size | low_n | 7.0000 | 100_500usd | 1089245.6443 | 0.7540 | 777961.0639 | 0.2528 | -0.5013 |
| 2859 | Sanjo 2621 | MAN SOO LEE 이만수 | 7038000.0000 | 5100.0000 | artist | medium_n | 15.0000 | 5k_20k_usd | 10823999.4309 | 0.5379 | 7325916.5156 | 0.0409 | -0.4970 |
| 2861 | Sanjo 2610 | MAN SOO LEE 이만수 | 7038000.0000 | 5100.0000 | artist | medium_n | 15.0000 | 5k_20k_usd | 10823999.4309 | 0.5379 | 7325916.5156 | 0.0409 | -0.4970 |
| 5254 | Triangular energy | Min Kim | 13800000.0000 | 10000.0000 | artist_size | low_n | 10.0000 | 5k_20k_usd | 22664475.4686 | 0.6424 | 15849381.9752 | 0.1485 | -0.4938 |
| 5375 | Rose from the stars | Jamsan | 9798000.0000 | 7100.0000 | artist_medium_support_size | low_n | 6.0000 | 5k_20k_usd | 17681823.4395 | 0.8046 | 12857563.6751 | 0.3123 | -0.4924 |
| 5372 | Rose from the stars | Jamsan | 9798000.0000 | 7100.0000 | artist_medium_support_size | low_n | 6.0000 | 5k_20k_usd | 17512278.4967 | 0.7873 | 12722009.8168 | 0.2984 | -0.4889 |
| 90 | Night Curtain | Yumi Jang | 910800.0000 | 660.0000 | artist_size | low_n | 6.0000 | 500_1k_usd | 404221.1043 | 0.5562 | 848994.9129 | 0.0679 | -0.4883 |
| 2876 | anonymity10-3-24 | Byung Wang Cho | 11040000.0000 | 8000.0000 | artist | medium_n | 18.0000 | 5k_20k_usd | 18564437.4799 | 0.6816 | 13195526.9253 | 0.1952 | -0.4863 |

## 7. 해석

- HCOEF 안정 후보는 기존 70:30 기준 위에 작은 Huber 잔차 보정만 더한 후보라 fixed test와 OOF 근거가 가장 강함.
- 0604에서는 PP-V8 운영 component가 더 강하게 나타남.
- 이 결과는 PP-V8 계열이 신규 운영성 데이터에서 유효한 신호를 갖고 있음을 시사하지만, 0604 라벨로 새 가중치나 보정값을 만들면 과적합 위험이 있음.
- 따라서 다음 후보는 `service_primary_pred_log`, `pp_v8_compact_blend_mape_guarded_pred_log`, `HCOEF stable pred_log`, `svc coverage`, `quantile width`를 저차원 Huber/meta guard 피처로 넣고 validation OOF에서 검증해야 함.
- service primary가 낮은 가격대와 일부 low_n 구간에서 더 나은지, 또는 특정 고가 구간에서만 우연히 좋은지는 segment별 OOF 실험에서 다시 확인해야 함.

## 8. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/residual_analysis.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `outputs/segment_metric_summary.csv`
- `outputs/service_vs_hcoef_gap_analysis.csv`
- `outputs/service_improvement_top100.csv`
- `outputs/actual_price_join_audit.csv`