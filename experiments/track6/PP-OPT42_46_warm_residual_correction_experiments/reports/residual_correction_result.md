# PP-OPT42~46 Warm 잔차 보정 실험 결과

- 작성일: 2026-06-09 12:13
- 데이터 기준: 제출용 제외, Warm validation OOF 519건 + fixed test 607건
- 기준 후보: PP-OPT7 운영 후보
- 비교 후보: PP20, PP23, PP30, PP36, PP38, PP41
- 전체 후보 수: 1004
- 운영 대체 통과 후보 수: 176

## 선택 후보
- 선택 후보: `ppopt45_high_price_fallback__base=pp23__fallback=pp30__mode=all_very_high__s=0p8`
- 원본 실험: `PP-OPT45` / `very_high_price_fallback`
- 판단: 선택 후보는 PP41 대비 MAPE -0.000042, p95 +0.000073이다.
| eval_split | n | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | 607 | 0.137878 | 0.270682 | 0.807660 | 0.397988 | 0.782537 | 0.883031 | -0.000713 | -0.000470 |
| validation_oof | 519 | 0.122430 | 0.206379 | 0.638550 | 0.323784 | 0.782274 | 0.911368 | -0.000644 | 0.001955 |

## 주요 reference test 비교
| candidate | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- |
| reference_pp23 | 0.137878 | 0.270707 | 0.807660 | 0.398002 | -0.000688 | -0.000470 |
| reference_pp41_challenger | 0.137845 | 0.270724 | 0.807587 | 0.398003 | -0.000671 | -0.000543 |
| reference_pp36_challenger | 0.137878 | 0.270748 | 0.807524 | 0.398008 | -0.000647 | -0.000606 |
| reference_pp38_best | 0.137053 | 0.270836 | 0.807102 | 0.398092 | -0.000559 | -0.001028 |
| reference_pp30_best | 0.137546 | 0.270872 | 0.806932 | 0.398014 | -0.000523 | -0.001198 |
| previous_challenger_pp20 | 0.136835 | 0.271182 | 0.806472 | 0.398134 | -0.000213 | -0.001658 |
| incumbent_operational_pp_opt7 | 0.136893 | 0.271395 | 0.808130 | 0.398341 | 0.000000 | 0.000000 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | stable_validation_pass_vs_incumbent | operational_pass_vs_incumbent | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 구간별 residual median shrinkage | 540 | 0.270715 | 0.808138 | -0.000680 | 0.000008 | 1.000000 | 0.925000 | True | True | segment_median_residual_shrinkage | ppopt43_segment_median__center=pp23__group=price_conf__shrink=55p0__s=0p35__cap=0p008 |
| 5 | monotonic correction cap 재설계 | 144 | 0.270792 | 0.807806 | -0.000603 | -0.000324 | 1.000000 | 0.900000 | True | True | monotonic_correction_cap | ppopt46_monotonic_cap__center=pp38_score__src=segment__s=0p25__cap=0p012 |
| 4 | very-high-price 전용 PP30/PP38 fallback | 60 | 0.270822 | 0.807587 | -0.000573 | -0.000543 | 1.000000 | 0.566667 | True | True | very_high_price_fallback | ppopt45_high_price_fallback__base=pp41__fallback=pp38_score__mode=all_very_high__s=0p8 |
| 3 | LightGBM quantile residual correction | 144 | 0.270728 | 0.807102 | -0.000667 | -0.001028 | 1.000000 | 0.512500 | False | False | quantile_residual_correction | ppopt44_quantile_residual__center=pp38_score__src=consensus__s=0p4__cap=0p02 |
| 1 | 잔차 방향 분류 후 비대칭 cap 보정 | 108 | 0.270493 | 0.808169 | -0.000902 | 0.000039 | 1.000000 | 0.441667 | False | False | directional_asymmetric_residual | ppopt42_direction_asym__center=pp38_score__thr=0p24__s=0p2__pcap=0p01__ncap=0p016 |

## 운영 대체 통과 후보 상위
| item_id | candidate | family | test_MdAPE | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | incumbent_all3_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-OPT43 | ppopt43_segment_median__center=pp23__group=price_conf__shrink=55p0__s=0p35__cap=0p008 | segment_median_residual_shrinkage | 0.136814 | 0.270715 | 0.808138 | -0.000680 | 0.000008 | 1.000000 | 0.925000 | 0.829167 | -0.002396 |
| PP-OPT43 | ppopt43_segment_median__center=pp41__group=price_conf__shrink=55p0__s=0p35__cap=0p008 | segment_median_residual_shrinkage | 0.136831 | 0.270730 | 0.808066 | -0.000665 | -0.000064 | 1.000000 | 0.925000 | 0.829167 | -0.002394 |
| PP-OPT43 | ppopt43_segment_median__center=pp38_score__group=price_conf__shrink=55p0__s=0p35__cap=0p012 | segment_median_residual_shrinkage | 0.136851 | 0.270801 | 0.807858 | -0.000594 | -0.000272 | 1.000000 | 0.916667 | 0.766667 | -0.002389 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp38_score__src=segment__s=0p25__cap=0p012 | monotonic_correction_cap | 0.136703 | 0.270792 | 0.807806 | -0.000603 | -0.000324 | 1.000000 | 0.900000 | 0.762500 | -0.002379 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp23__src=segment__s=0p25__cap=0p008 | monotonic_correction_cap | 0.136819 | 0.270711 | 0.808137 | -0.000684 | 0.000007 | 1.000000 | 0.920833 | 0.825000 | -0.002364 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp41__src=segment__s=0p25__cap=0p008 | monotonic_correction_cap | 0.136840 | 0.270728 | 0.808065 | -0.000667 | -0.000065 | 1.000000 | 0.920833 | 0.825000 | -0.002362 |
| PP-OPT43 | ppopt43_segment_median__center=pp38_score__group=price_conf__shrink=18p0__s=0p35__cap=0p008 | segment_median_residual_shrinkage | 0.136971 | 0.270867 | 0.807571 | -0.000528 | -0.000559 | 1.000000 | 0.883333 | 0.737500 | -0.002323 |
| PP-OPT43 | ppopt43_segment_median__center=pp23__group=price_conf__shrink=55p0__s=0p55__cap=0p008 | segment_median_residual_shrinkage | 0.137225 | 0.270743 | 0.808108 | -0.000652 | -0.000022 | 1.000000 | 0.912500 | 0.812500 | -0.002304 |
| PP-OPT43 | ppopt43_segment_median__center=pp23__group=price_conf__shrink=32p0__s=0p35__cap=0p008 | segment_median_residual_shrinkage | 0.137239 | 0.270726 | 0.808123 | -0.000668 | -0.000007 | 1.000000 | 0.920833 | 0.816667 | -0.002296 |
| PP-OPT43 | ppopt43_segment_median__center=pp41__group=price_conf__shrink=55p0__s=0p55__cap=0p008 | segment_median_residual_shrinkage | 0.137241 | 0.270759 | 0.808036 | -0.000636 | -0.000094 | 1.000000 | 0.912500 | 0.812500 | -0.002292 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp38_score__src=segment__s=0p25__cap=0p016 | monotonic_correction_cap | 0.136703 | 0.270752 | 0.807806 | -0.000643 | -0.000324 | 0.995833 | 0.900000 | 0.725000 | -0.002288 |
| PP-OPT43 | ppopt43_segment_median__center=pp38_score__group=price_conf__shrink=55p0__s=0p35__cap=0p016 | segment_median_residual_shrinkage | 0.136851 | 0.270762 | 0.807908 | -0.000633 | -0.000222 | 1.000000 | 0.916667 | 0.725000 | -0.002288 |
| PP-OPT43 | ppopt43_segment_median__center=pp23__group=price_conf__shrink=55p0__s=0p75__cap=0p008 | segment_median_residual_shrinkage | 0.137225 | 0.270785 | 0.808079 | -0.000609 | -0.000051 | 1.000000 | 0.912500 | 0.804167 | -0.002287 |
| PP-OPT43 | ppopt43_segment_median__center=pp41__group=price_conf__shrink=32p0__s=0p35__cap=0p008 | segment_median_residual_shrinkage | 0.137270 | 0.270741 | 0.808051 | -0.000654 | -0.000079 | 1.000000 | 0.920833 | 0.816667 | -0.002282 |
| PP-OPT43 | ppopt43_segment_median__center=pp41__group=price_conf__shrink=55p0__s=0p75__cap=0p008 | segment_median_residual_shrinkage | 0.137241 | 0.270802 | 0.808007 | -0.000593 | -0.000123 | 1.000000 | 0.904167 | 0.804167 | -0.002278 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp38_score__src=segment__s=0p4__cap=0p012 | monotonic_correction_cap | 0.137290 | 0.270857 | 0.807816 | -0.000537 | -0.000314 | 1.000000 | 0.875000 | 0.716667 | -0.002260 |
| PP-OPT43 | ppopt43_segment_median__center=pp23__group=price_conf__shrink=32p0__s=0p55__cap=0p008 | segment_median_residual_shrinkage | 0.137225 | 0.270766 | 0.808086 | -0.000629 | -0.000044 | 1.000000 | 0.904167 | 0.795833 | -0.002258 |
| PP-OPT43 | ppopt43_segment_median__center=pp38_score__group=price_conf__shrink=18p0__s=0p35__cap=0p012 | segment_median_residual_shrinkage | 0.136971 | 0.270854 | 0.807836 | -0.000541 | -0.000294 | 1.000000 | 0.875000 | 0.704167 | -0.002255 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp23__src=segment__s=0p4__cap=0p008 | monotonic_correction_cap | 0.137225 | 0.270733 | 0.808106 | -0.000662 | -0.000024 | 1.000000 | 0.904167 | 0.795833 | -0.002242 |
| PP-OPT43 | ppopt43_segment_median__center=pp38_score__group=price_conf__shrink=32p0__s=0p35__cap=0p012 | segment_median_residual_shrinkage | 0.137425 | 0.270839 | 0.807847 | -0.000556 | -0.000283 | 1.000000 | 0.883333 | 0.754167 | -0.002242 |
| PP-OPT43 | ppopt43_segment_median__center=pp41__group=price_conf__shrink=32p0__s=0p55__cap=0p008 | segment_median_residual_shrinkage | 0.137241 | 0.270782 | 0.808014 | -0.000613 | -0.000116 | 1.000000 | 0.904167 | 0.791667 | -0.002241 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp38_score__src=segment__s=0p25__cap=0p02 | monotonic_correction_cap | 0.136703 | 0.270713 | 0.807806 | -0.000681 | -0.000324 | 0.995833 | 0.900000 | 0.700000 | -0.002238 |
| PP-OPT43 | ppopt43_segment_median__center=pp41__group=price_conf__shrink=55p0__s=0p35__cap=0p012 | segment_median_residual_shrinkage | 0.136771 | 0.270685 | 0.808330 | -0.000710 | 0.000200 | 1.000000 | 0.925000 | 0.825000 | -0.002238 |
| PP-OPT43 | ppopt43_segment_median__center=pp38_score__group=price_conf__shrink=55p0__s=0p35__cap=0p008 | segment_median_residual_shrinkage | 0.137690 | 0.270846 | 0.807593 | -0.000549 | -0.000537 | 1.000000 | 0.916667 | 0.775000 | -0.002235 |
| PP-OPT43 | ppopt43_segment_median__center=pp23__group=price_conf__shrink=18p0__s=0p35__cap=0p008 | segment_median_residual_shrinkage | 0.137225 | 0.270727 | 0.808110 | -0.000668 | -0.000020 | 1.000000 | 0.908333 | 0.795833 | -0.002235 |
| PP-OPT43 | ppopt43_segment_median__center=pp23__group=price_conf__shrink=32p0__s=0p75__cap=0p008 | segment_median_residual_shrinkage | 0.137225 | 0.270779 | 0.808048 | -0.000616 | -0.000082 | 0.995833 | 0.900000 | 0.787500 | -0.002232 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp23__src=segment__s=0p55__cap=0p008 | monotonic_correction_cap | 0.137225 | 0.270769 | 0.808075 | -0.000626 | -0.000055 | 0.995833 | 0.900000 | 0.783333 | -0.002232 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp41__src=segment__s=0p4__cap=0p008 | monotonic_correction_cap | 0.137241 | 0.270749 | 0.808034 | -0.000646 | -0.000096 | 1.000000 | 0.904167 | 0.795833 | -0.002232 |
| PP-OPT43 | ppopt43_segment_median__center=pp38_score__group=price_conf__shrink=32p0__s=0p35__cap=0p008 | segment_median_residual_shrinkage | 0.137425 | 0.270865 | 0.807582 | -0.000530 | -0.000548 | 1.000000 | 0.883333 | 0.737500 | -0.002230 |
| PP-OPT43 | ppopt43_segment_median__center=pp23__group=price_conf__shrink=18p0__s=0p55__cap=0p008 | segment_median_residual_shrinkage | 0.137225 | 0.270768 | 0.808065 | -0.000627 | -0.000065 | 0.995833 | 0.900000 | 0.783333 | -0.002224 |
| PP-OPT43 | ppopt43_segment_median__center=pp38_score__group=price_conf__shrink=10p0__s=0p35__cap=0p008 | segment_median_residual_shrinkage | 0.137195 | 0.270873 | 0.807563 | -0.000522 | -0.000567 | 1.000000 | 0.883333 | 0.720833 | -0.002220 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp23__src=segment__s=0p7__cap=0p008 | monotonic_correction_cap | 0.137225 | 0.270772 | 0.808044 | -0.000623 | -0.000086 | 0.995833 | 0.900000 | 0.783333 | -0.002220 |
| PP-OPT43 | ppopt43_segment_median__center=pp23__group=price_conf__shrink=10p0__s=0p55__cap=0p008 | segment_median_residual_shrinkage | 0.137225 | 0.270759 | 0.808048 | -0.000636 | -0.000082 | 0.995833 | 0.900000 | 0.783333 | -0.002219 |
| PP-OPT43 | ppopt43_segment_median__center=pp41__group=price_conf__shrink=18p0__s=0p35__cap=0p008 | segment_median_residual_shrinkage | 0.137241 | 0.270742 | 0.808038 | -0.000653 | -0.000092 | 1.000000 | 0.904167 | 0.791667 | -0.002216 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp41__src=segment__s=0p55__cap=0p008 | monotonic_correction_cap | 0.137241 | 0.270785 | 0.808003 | -0.000610 | -0.000127 | 0.995833 | 0.904167 | 0.779167 | -0.002213 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp41__src=segment__s=0p25__cap=0p012 | monotonic_correction_cap | 0.136458 | 0.270687 | 0.808287 | -0.000708 | 0.000157 | 1.000000 | 0.920833 | 0.812500 | -0.002212 |
| PP-OPT43 | ppopt43_segment_median__center=pp23__group=price_conf__shrink=18p0__s=0p75__cap=0p008 | segment_median_residual_shrinkage | 0.137225 | 0.270764 | 0.808019 | -0.000631 | -0.000111 | 0.995833 | 0.900000 | 0.787500 | -0.002209 |
| PP-OPT43 | ppopt43_segment_median__center=pp41__group=price_conf__shrink=18p0__s=0p55__cap=0p008 | segment_median_residual_shrinkage | 0.137241 | 0.270784 | 0.807993 | -0.000610 | -0.000137 | 0.995833 | 0.900000 | 0.779167 | -0.002207 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp41__src=segment__s=0p25__cap=0p016 | monotonic_correction_cap | 0.136458 | 0.270646 | 0.808287 | -0.000748 | 0.000157 | 1.000000 | 0.920833 | 0.816667 | -0.002205 |
| PP-OPT43 | ppopt43_segment_median__center=pp23__group=price_conf__shrink=10p0__s=0p75__cap=0p008 | segment_median_residual_shrinkage | 0.137225 | 0.270764 | 0.808018 | -0.000631 | -0.000112 | 0.995833 | 0.904167 | 0.791667 | -0.002204 |

## 전체 MAPE 상위 후보
| item_id | candidate | family | test_MdAPE | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | incumbent_all3_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp23__src=q50__s=0p7__cap=0p02 | monotonic_correction_cap | 0.135645 | 0.269620 | 0.810289 | -0.001775 | 0.002159 | 0.858333 | 0.279167 | 0.145833 | 0.005188 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp41__src=q50__s=0p7__cap=0p02 | monotonic_correction_cap | 0.135713 | 0.269636 | 0.810248 | -0.001759 | 0.002118 | 0.854167 | 0.258333 | 0.137500 | 0.005198 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp23__src=q50_segment_avg__s=0p7__cap=0p02 | monotonic_correction_cap | 0.136949 | 0.269643 | 0.809405 | -0.001752 | 0.001275 | 0.870833 | 0.250000 | 0.191667 | 0.004208 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp41__src=q50_segment_avg__s=0p7__cap=0p02 | monotonic_correction_cap | 0.136788 | 0.269659 | 0.809333 | -0.001736 | 0.001203 | 0.870833 | 0.250000 | 0.191667 | 0.004163 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp23__src=q50_segment_avg__s=0p55__cap=0p02 | monotonic_correction_cap | 0.136949 | 0.269665 | 0.809405 | -0.001730 | 0.001275 | 0.916667 | 0.266667 | 0.208333 | 0.003416 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp23__src=q50__s=0p55__cap=0p02 | monotonic_correction_cap | 0.134548 | 0.269673 | 0.810289 | -0.001722 | 0.002159 | 0.891667 | 0.279167 | 0.145833 | 0.005049 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp41__src=q50_segment_avg__s=0p55__cap=0p02 | monotonic_correction_cap | 0.136788 | 0.269681 | 0.809333 | -0.001714 | 0.001203 | 0.916667 | 0.266667 | 0.208333 | 0.003373 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp41__src=q50__s=0p55__cap=0p02 | monotonic_correction_cap | 0.134564 | 0.269689 | 0.810248 | -0.001705 | 0.002118 | 0.887500 | 0.258333 | 0.133333 | 0.005067 |
| PP-OPT44 | ppopt44_quantile_residual__center=pp41__src=q50__s=0p7__cap=0p02 | quantile_residual_correction | 0.135076 | 0.269703 | 0.810248 | -0.001692 | 0.002118 | 0.858333 | 0.258333 | 0.137500 | 0.005143 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp23__src=q50__s=0p4__cap=0p02 | monotonic_correction_cap | 0.136423 | 0.269718 | 0.810289 | -0.001677 | 0.002159 | 0.929167 | 0.283333 | 0.195833 | 0.004750 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp23__src=q50__s=0p25__cap=0p02 | monotonic_correction_cap | 0.136949 | 0.269718 | 0.810289 | -0.001677 | 0.002159 | 0.975000 | 0.304167 | 0.229167 | 0.003851 |
| PP-OPT44 | ppopt44_quantile_residual__center=pp41__src=q50__s=0p55__cap=0p02 | quantile_residual_correction | 0.136440 | 0.269723 | 0.810248 | -0.001672 | 0.002118 | 0.895833 | 0.279167 | 0.158333 | 0.004954 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp23__src=q50_segment_avg__s=0p4__cap=0p02 | monotonic_correction_cap | 0.136949 | 0.269732 | 0.809405 | -0.001662 | 0.001275 | 0.975000 | 0.300000 | 0.212500 | 0.002277 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp41__src=q50__s=0p4__cap=0p02 | monotonic_correction_cap | 0.136439 | 0.269734 | 0.810248 | -0.001661 | 0.002118 | 0.929167 | 0.283333 | 0.195833 | 0.004741 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp41__src=q50__s=0p25__cap=0p02 | monotonic_correction_cap | 0.136788 | 0.269734 | 0.810248 | -0.001661 | 0.002118 | 0.975000 | 0.304167 | 0.229167 | 0.003831 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp23__src=q50__s=0p7__cap=0p016 | monotonic_correction_cap | 0.135692 | 0.269735 | 0.809339 | -0.001660 | 0.001209 | 0.937500 | 0.270833 | 0.170833 | 0.003416 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp41__src=q50_segment_avg__s=0p4__cap=0p02 | monotonic_correction_cap | 0.136788 | 0.269749 | 0.809333 | -0.001646 | 0.001203 | 0.979167 | 0.300000 | 0.216667 | 0.002225 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp41__src=q50__s=0p7__cap=0p016 | monotonic_correction_cap | 0.135713 | 0.269751 | 0.809298 | -0.001644 | 0.001168 | 0.941667 | 0.270833 | 0.175000 | 0.003404 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp38_score__src=q50__s=0p7__cap=0p02 | monotonic_correction_cap | 0.137514 | 0.269767 | 0.809109 | -0.001628 | 0.000979 | 0.908333 | 0.233333 | 0.112500 | 0.004659 |
| PP-OPT44 | ppopt44_quantile_residual__center=pp41__src=q50__s=0p4__cap=0p02 | quantile_residual_correction | 0.136132 | 0.269773 | 0.810248 | -0.001622 | 0.002118 | 0.937500 | 0.287500 | 0.208333 | 0.004673 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp23__src=q50__s=0p55__cap=0p016 | monotonic_correction_cap | 0.135692 | 0.269780 | 0.809339 | -0.001615 | 0.001209 | 0.945833 | 0.270833 | 0.158333 | 0.003311 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp23__src=q50_segment_avg__s=0p7__cap=0p016 | monotonic_correction_cap | 0.136705 | 0.269786 | 0.809057 | -0.001608 | 0.000927 | 0.933333 | 0.262500 | 0.200000 | 0.003041 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp38_score__src=q50_segment_avg__s=0p7__cap=0p02 | monotonic_correction_cap | 0.138075 | 0.269787 | 0.808853 | -0.001608 | 0.000723 | 0.925000 | 0.233333 | 0.150000 | 0.004282 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp41__src=q50__s=0p55__cap=0p016 | monotonic_correction_cap | 0.135685 | 0.269796 | 0.809298 | -0.001599 | 0.001168 | 0.945833 | 0.270833 | 0.150000 | 0.003321 |
| PP-OPT44 | ppopt44_quantile_residual__center=pp41__src=q50__s=0p7__cap=0p016 | quantile_residual_correction | 0.135685 | 0.269797 | 0.809298 | -0.001598 | 0.001168 | 0.941667 | 0.270833 | 0.162500 | 0.003340 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp41__src=q50_segment_avg__s=0p7__cap=0p016 | monotonic_correction_cap | 0.136705 | 0.269803 | 0.808985 | -0.001592 | 0.000855 | 0.933333 | 0.262500 | 0.200000 | 0.003012 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp38_score__src=q50_segment_avg__s=0p55__cap=0p02 | monotonic_correction_cap | 0.138075 | 0.269808 | 0.808853 | -0.001587 | 0.000723 | 0.962500 | 0.241667 | 0.166667 | 0.003494 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp23__src=q50_segment_avg__s=0p55__cap=0p016 | monotonic_correction_cap | 0.136705 | 0.269811 | 0.809057 | -0.001584 | 0.000927 | 0.954167 | 0.279167 | 0.216667 | 0.002691 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp38_score__src=q50__s=0p55__cap=0p02 | monotonic_correction_cap | 0.136598 | 0.269820 | 0.809109 | -0.001575 | 0.000979 | 0.929167 | 0.233333 | 0.116667 | 0.004372 |
| PP-OPT44 | ppopt44_quantile_residual__center=pp41__src=q50__s=0p25__cap=0p02 | quantile_residual_correction | 0.136788 | 0.269821 | 0.810248 | -0.001574 | 0.002118 | 0.975000 | 0.295833 | 0.225000 | 0.003490 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp41__src=q50_segment_avg__s=0p55__cap=0p016 | monotonic_correction_cap | 0.136705 | 0.269828 | 0.808985 | -0.001567 | 0.000855 | 0.954167 | 0.275000 | 0.216667 | 0.002664 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp23__src=q50__s=0p4__cap=0p016 | monotonic_correction_cap | 0.136423 | 0.269830 | 0.809339 | -0.001565 | 0.001209 | 0.962500 | 0.275000 | 0.183333 | 0.003131 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp23__src=q50_segment_avg__s=0p4__cap=0p016 | monotonic_correction_cap | 0.136705 | 0.269843 | 0.809057 | -0.001552 | 0.000927 | 0.979167 | 0.300000 | 0.225000 | 0.001887 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp41__src=q50__s=0p4__cap=0p016 | monotonic_correction_cap | 0.136439 | 0.269846 | 0.809298 | -0.001549 | 0.001168 | 0.962500 | 0.275000 | 0.187500 | 0.003115 |
| PP-OPT44 | ppopt44_quantile_residual__center=pp41__src=q50__s=0p55__cap=0p016 | quantile_residual_correction | 0.136440 | 0.269847 | 0.809298 | -0.001548 | 0.001168 | 0.941667 | 0.275000 | 0.162500 | 0.003256 |
| PP-OPT44 | ppopt44_quantile_residual__center=pp41__src=q50_width__s=0p7__cap=0p02 | quantile_residual_correction | 0.136788 | 0.269848 | 0.810248 | -0.001547 | 0.002118 | 0.945833 | 0.266667 | 0.204167 | 0.004058 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp38_score__src=q50__s=0p25__cap=0p02 | monotonic_correction_cap | 0.137968 | 0.269854 | 0.809109 | -0.001541 | 0.000979 | 0.979167 | 0.275000 | 0.150000 | 0.003545 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp23__src=q50__s=0p25__cap=0p016 | monotonic_correction_cap | 0.136705 | 0.269857 | 0.809339 | -0.001538 | 0.001209 | 0.979167 | 0.300000 | 0.225000 | 0.002611 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp41__src=q50_segment_avg__s=0p4__cap=0p016 | monotonic_correction_cap | 0.136705 | 0.269859 | 0.808985 | -0.001536 | 0.000855 | 0.979167 | 0.300000 | 0.225000 | 0.001859 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp38_score__src=q50__s=0p4__cap=0p02 | monotonic_correction_cap | 0.136973 | 0.269863 | 0.809109 | -0.001532 | 0.000979 | 0.950000 | 0.237500 | 0.145833 | 0.004155 |

## MAPE와 p95 동시 개선 후보
| item_id | candidate | family | test_MdAPE | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | incumbent_all3_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-OPT43 | ppopt43_segment_median__center=pp41__group=price_conf__shrink=55p0__s=0p35__cap=0p008 | segment_median_residual_shrinkage | 0.136831 | 0.270730 | 0.808066 | -0.000665 | -0.000064 | 1.000000 | 0.925000 | 0.829167 | -0.002394 |
| PP-OPT43 | ppopt43_segment_median__center=pp38_score__group=price_conf__shrink=55p0__s=0p35__cap=0p012 | segment_median_residual_shrinkage | 0.136851 | 0.270801 | 0.807858 | -0.000594 | -0.000272 | 1.000000 | 0.916667 | 0.766667 | -0.002389 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp38_score__src=segment__s=0p25__cap=0p012 | monotonic_correction_cap | 0.136703 | 0.270792 | 0.807806 | -0.000603 | -0.000324 | 1.000000 | 0.900000 | 0.762500 | -0.002379 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp41__src=segment__s=0p25__cap=0p008 | monotonic_correction_cap | 0.136840 | 0.270728 | 0.808065 | -0.000667 | -0.000065 | 1.000000 | 0.920833 | 0.825000 | -0.002362 |
| PP-OPT43 | ppopt43_segment_median__center=pp38_score__group=price_conf__shrink=18p0__s=0p35__cap=0p008 | segment_median_residual_shrinkage | 0.136971 | 0.270867 | 0.807571 | -0.000528 | -0.000559 | 1.000000 | 0.883333 | 0.737500 | -0.002323 |
| PP-OPT43 | ppopt43_segment_median__center=pp23__group=price_conf__shrink=55p0__s=0p55__cap=0p008 | segment_median_residual_shrinkage | 0.137225 | 0.270743 | 0.808108 | -0.000652 | -0.000022 | 1.000000 | 0.912500 | 0.812500 | -0.002304 |
| PP-OPT43 | ppopt43_segment_median__center=pp23__group=price_conf__shrink=32p0__s=0p35__cap=0p008 | segment_median_residual_shrinkage | 0.137239 | 0.270726 | 0.808123 | -0.000668 | -0.000007 | 1.000000 | 0.920833 | 0.816667 | -0.002296 |
| PP-OPT43 | ppopt43_segment_median__center=pp41__group=price_conf__shrink=55p0__s=0p55__cap=0p008 | segment_median_residual_shrinkage | 0.137241 | 0.270759 | 0.808036 | -0.000636 | -0.000094 | 1.000000 | 0.912500 | 0.812500 | -0.002292 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp38_score__src=segment__s=0p25__cap=0p016 | monotonic_correction_cap | 0.136703 | 0.270752 | 0.807806 | -0.000643 | -0.000324 | 0.995833 | 0.900000 | 0.725000 | -0.002288 |
| PP-OPT43 | ppopt43_segment_median__center=pp38_score__group=price_conf__shrink=55p0__s=0p35__cap=0p016 | segment_median_residual_shrinkage | 0.136851 | 0.270762 | 0.807908 | -0.000633 | -0.000222 | 1.000000 | 0.916667 | 0.725000 | -0.002288 |
| PP-OPT43 | ppopt43_segment_median__center=pp23__group=price_conf__shrink=55p0__s=0p75__cap=0p008 | segment_median_residual_shrinkage | 0.137225 | 0.270785 | 0.808079 | -0.000609 | -0.000051 | 1.000000 | 0.912500 | 0.804167 | -0.002287 |
| PP-OPT43 | ppopt43_segment_median__center=pp41__group=price_conf__shrink=32p0__s=0p35__cap=0p008 | segment_median_residual_shrinkage | 0.137270 | 0.270741 | 0.808051 | -0.000654 | -0.000079 | 1.000000 | 0.920833 | 0.816667 | -0.002282 |
| PP-OPT43 | ppopt43_segment_median__center=pp41__group=price_conf__shrink=55p0__s=0p75__cap=0p008 | segment_median_residual_shrinkage | 0.137241 | 0.270802 | 0.808007 | -0.000593 | -0.000123 | 1.000000 | 0.904167 | 0.804167 | -0.002278 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp38_score__src=segment__s=0p4__cap=0p012 | monotonic_correction_cap | 0.137290 | 0.270857 | 0.807816 | -0.000537 | -0.000314 | 1.000000 | 0.875000 | 0.716667 | -0.002260 |
| PP-OPT43 | ppopt43_segment_median__center=pp23__group=price_conf__shrink=32p0__s=0p55__cap=0p008 | segment_median_residual_shrinkage | 0.137225 | 0.270766 | 0.808086 | -0.000629 | -0.000044 | 1.000000 | 0.904167 | 0.795833 | -0.002258 |
| PP-OPT43 | ppopt43_segment_median__center=pp38_score__group=price_conf__shrink=18p0__s=0p35__cap=0p012 | segment_median_residual_shrinkage | 0.136971 | 0.270854 | 0.807836 | -0.000541 | -0.000294 | 1.000000 | 0.875000 | 0.704167 | -0.002255 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp23__src=segment__s=0p4__cap=0p008 | monotonic_correction_cap | 0.137225 | 0.270733 | 0.808106 | -0.000662 | -0.000024 | 1.000000 | 0.904167 | 0.795833 | -0.002242 |
| PP-OPT43 | ppopt43_segment_median__center=pp38_score__group=price_conf__shrink=32p0__s=0p35__cap=0p012 | segment_median_residual_shrinkage | 0.137425 | 0.270839 | 0.807847 | -0.000556 | -0.000283 | 1.000000 | 0.883333 | 0.754167 | -0.002242 |
| PP-OPT43 | ppopt43_segment_median__center=pp41__group=price_conf__shrink=32p0__s=0p55__cap=0p008 | segment_median_residual_shrinkage | 0.137241 | 0.270782 | 0.808014 | -0.000613 | -0.000116 | 1.000000 | 0.904167 | 0.791667 | -0.002241 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp38_score__src=segment__s=0p25__cap=0p02 | monotonic_correction_cap | 0.136703 | 0.270713 | 0.807806 | -0.000681 | -0.000324 | 0.995833 | 0.900000 | 0.700000 | -0.002238 |
| PP-OPT43 | ppopt43_segment_median__center=pp38_score__group=price_conf__shrink=55p0__s=0p35__cap=0p008 | segment_median_residual_shrinkage | 0.137690 | 0.270846 | 0.807593 | -0.000549 | -0.000537 | 1.000000 | 0.916667 | 0.775000 | -0.002235 |
| PP-OPT43 | ppopt43_segment_median__center=pp23__group=price_conf__shrink=18p0__s=0p35__cap=0p008 | segment_median_residual_shrinkage | 0.137225 | 0.270727 | 0.808110 | -0.000668 | -0.000020 | 1.000000 | 0.908333 | 0.795833 | -0.002235 |
| PP-OPT43 | ppopt43_segment_median__center=pp23__group=price_conf__shrink=32p0__s=0p75__cap=0p008 | segment_median_residual_shrinkage | 0.137225 | 0.270779 | 0.808048 | -0.000616 | -0.000082 | 0.995833 | 0.900000 | 0.787500 | -0.002232 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp23__src=segment__s=0p55__cap=0p008 | monotonic_correction_cap | 0.137225 | 0.270769 | 0.808075 | -0.000626 | -0.000055 | 0.995833 | 0.900000 | 0.783333 | -0.002232 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp41__src=segment__s=0p4__cap=0p008 | monotonic_correction_cap | 0.137241 | 0.270749 | 0.808034 | -0.000646 | -0.000096 | 1.000000 | 0.904167 | 0.795833 | -0.002232 |
| PP-OPT43 | ppopt43_segment_median__center=pp38_score__group=price_conf__shrink=32p0__s=0p35__cap=0p008 | segment_median_residual_shrinkage | 0.137425 | 0.270865 | 0.807582 | -0.000530 | -0.000548 | 1.000000 | 0.883333 | 0.737500 | -0.002230 |
| PP-OPT43 | ppopt43_segment_median__center=pp23__group=price_conf__shrink=18p0__s=0p55__cap=0p008 | segment_median_residual_shrinkage | 0.137225 | 0.270768 | 0.808065 | -0.000627 | -0.000065 | 0.995833 | 0.900000 | 0.783333 | -0.002224 |
| PP-OPT43 | ppopt43_segment_median__center=pp38_score__group=price_conf__shrink=10p0__s=0p35__cap=0p008 | segment_median_residual_shrinkage | 0.137195 | 0.270873 | 0.807563 | -0.000522 | -0.000567 | 1.000000 | 0.883333 | 0.720833 | -0.002220 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp23__src=segment__s=0p7__cap=0p008 | monotonic_correction_cap | 0.137225 | 0.270772 | 0.808044 | -0.000623 | -0.000086 | 0.995833 | 0.900000 | 0.783333 | -0.002220 |
| PP-OPT43 | ppopt43_segment_median__center=pp23__group=price_conf__shrink=10p0__s=0p55__cap=0p008 | segment_median_residual_shrinkage | 0.137225 | 0.270759 | 0.808048 | -0.000636 | -0.000082 | 0.995833 | 0.900000 | 0.783333 | -0.002219 |
| PP-OPT43 | ppopt43_segment_median__center=pp41__group=price_conf__shrink=18p0__s=0p35__cap=0p008 | segment_median_residual_shrinkage | 0.137241 | 0.270742 | 0.808038 | -0.000653 | -0.000092 | 1.000000 | 0.904167 | 0.791667 | -0.002216 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp41__src=segment__s=0p55__cap=0p008 | monotonic_correction_cap | 0.137241 | 0.270785 | 0.808003 | -0.000610 | -0.000127 | 0.995833 | 0.904167 | 0.779167 | -0.002213 |
| PP-OPT43 | ppopt43_segment_median__center=pp23__group=price_conf__shrink=18p0__s=0p75__cap=0p008 | segment_median_residual_shrinkage | 0.137225 | 0.270764 | 0.808019 | -0.000631 | -0.000111 | 0.995833 | 0.900000 | 0.787500 | -0.002209 |
| PP-OPT43 | ppopt43_segment_median__center=pp41__group=price_conf__shrink=18p0__s=0p55__cap=0p008 | segment_median_residual_shrinkage | 0.137241 | 0.270784 | 0.807993 | -0.000610 | -0.000137 | 0.995833 | 0.900000 | 0.779167 | -0.002207 |
| PP-OPT43 | ppopt43_segment_median__center=pp23__group=price_conf__shrink=10p0__s=0p75__cap=0p008 | segment_median_residual_shrinkage | 0.137225 | 0.270764 | 0.808018 | -0.000631 | -0.000112 | 0.995833 | 0.904167 | 0.791667 | -0.002204 |
| PP-OPT43 | ppopt43_segment_median__center=pp41__group=price_conf__shrink=10p0__s=0p55__cap=0p008 | segment_median_residual_shrinkage | 0.137241 | 0.270775 | 0.807977 | -0.000620 | -0.000153 | 0.995833 | 0.900000 | 0.779167 | -0.002201 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp41__src=segment__s=0p7__cap=0p008 | monotonic_correction_cap | 0.137241 | 0.270789 | 0.807972 | -0.000606 | -0.000158 | 0.995833 | 0.900000 | 0.779167 | -0.002201 |
| PP-OPT43 | ppopt43_segment_median__center=pp41__group=price_conf__shrink=32p0__s=0p75__cap=0p008 | segment_median_residual_shrinkage | 0.137241 | 0.270796 | 0.807976 | -0.000599 | -0.000154 | 0.995833 | 0.891667 | 0.775000 | -0.002198 |
| PP-OPT46 | ppopt46_monotonic_cap__center=pp38_score__src=segment__s=0p25__cap=0p008 | monotonic_correction_cap | 0.137762 | 0.270832 | 0.807582 | -0.000563 | -0.000548 | 1.000000 | 0.900000 | 0.762500 | -0.002194 |
| PP-OPT43 | ppopt43_segment_median__center=pp38_score__group=price_conf__shrink=55p0__s=0p55__cap=0p008 | segment_median_residual_shrinkage | 0.137610 | 0.270878 | 0.807569 | -0.000517 | -0.000561 | 1.000000 | 0.875000 | 0.733333 | -0.002193 |

## 해석
이번 배치는 기존 후보 블렌드가 아니라 남은 잔차 자체를 보정했다. 선택 후보가 PP41보다 명확히 좋아지지 않으면 잔차 보정은 운영 반영보다 분석용으로 유지하는 것이 안전하다.
구간 중앙값과 quantile 잔차 보정이 안정적으로 작동하면 다음 단계는 해당 보정을 더 작은 cap으로 freeze하는 것이다.

## 실행 설정
```json
{
  "experiment_id": "PP-OPT42-46",
  "experiment_slug": "PP-OPT42_46_warm_residual_correction_experiments",
  "created_at": "2026-06-09T12:13:06",
  "seed": 20260609,
  "base_candidate": "hcoef_stable",
  "incumbent_candidate": "incumbent_operational_pp_opt7",
  "previous_challenger": "previous_challenger_pp20",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 1005,
  "prediction_rows": 1131630,
  "items": [
    {
      "item_id": "PP-OPT42",
      "priority": "1",
      "title": "잔차 방향 분류 후 비대칭 cap 보정",
      "description": "과대/과소예측 방향 확신이 있을 때만 서로 다른 상한으로 보정한다."
    },
    {
      "item_id": "PP-OPT43",
      "priority": "2",
      "title": "구간별 residual median shrinkage",
      "description": "가격대/신뢰도/불확실성 구간의 잔차 중앙값을 표본 수 기반으로 축소해 적용한다."
    },
    {
      "item_id": "PP-OPT44",
      "priority": "3",
      "title": "LightGBM quantile residual correction",
      "description": "잔차 q25/q50/q75를 학습하고 예측구간 폭이 넓으면 보정 강도를 줄인다."
    },
    {
      "item_id": "PP-OPT45",
      "priority": "4",
      "title": "very-high-price 전용 PP30/PP38 fallback",
      "description": "대부분은 PP23/PP41을 유지하고 초고가 구간에서만 안정 후보로 부분 fallback한다."
    },
    {
      "item_id": "PP-OPT46",
      "priority": "5",
      "title": "monotonic correction cap 재설계",
      "description": "유사작품 수가 적고 불확실성이 클수록 보정 상한을 단조적으로 줄인다."
    }
  ],
  "selected_references": {
    "pp20": "previous_challenger_pp20",
    "pp23": "reference_pp23",
    "pp30": "reference_pp30_best",
    "pp36": "reference_pp36_challenger",
    "pp41": "ppopt41_followup_challenger__source=ppopt40_p95_penalty_stack__pen_0p75__p20_0p0__p23_0p9__p30_0p1__p31_0p0__p36_0p0",
    "pp38_score": "ppopt38_router_shrink__router=pp35_guarded__anchor=pp30_score__max=0p8__floor=0p3",
    "pp38_mape": "ppopt38_router_shrink__router=pp35_mape__anchor=pp36__max=0p8__floor=0p3",
    "pp39_score": "ppopt39_calibrated_selector__prob=raw_calibrated_geomean__thr=0p1__width=0p45__sharp=1p25",
    "pp40_score": "ppopt40_p95_penalty_stack__pen=0p75__p20=0p0__p23=0p30000000000000004__p30=0p7000000000000001__p31=0p0__p36=0p0"
  },
  "selection_decision": {
    "selected_candidate": "ppopt45_high_price_fallback__base=pp23__fallback=pp30__mode=all_very_high__s=0p8",
    "selected_item_id": "PP-OPT45",
    "selected_family": "very_high_price_fallback",
    "selection_reason": "operational pass first; prefer PP41 MAPE improvement with p95 not worse than PP7; fallback to p95-safe recommendation score",
    "test_MdAPE": 0.13787846966744394,
    "test_MAPE": 0.2706816816114496,
    "test_p95_APE": 0.8076599439149326,
    "test_delta_vs_incumbent_MdAPE": 0.000985903768827734,
    "test_delta_vs_incumbent_MAPE": -0.0007132064006168393,
    "test_delta_vs_incumbent_p95_APE": -0.00047003879853613206,
    "recommendation_score_vs_incumbent": -0.0012935511527570828
  },
  "sources": {
    "pp_opt37_config": "PP-OPT37_41_warm_followup_refinement_experiments",
    "pp_opt37_predictions": "experiments/track6/PP-OPT37_41_warm_followup_refinement_experiments/outputs/candidate_predictions.csv",
    "pp_opt37_aggregate": "experiments/track6/PP-OPT37_41_warm_followup_refinement_experiments/outputs/aggregate_candidate_stability.csv",
    "pp_opt37_helper": "scripts/track6/run_pp_opt37_41_warm_followup_refinement_experiments.py"
  }
}
```