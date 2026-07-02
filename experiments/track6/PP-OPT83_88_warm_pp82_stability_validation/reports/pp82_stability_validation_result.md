# PP-OPT83~88 Warm PP82 안정성 검증 결과

- 작성일: 2026-06-09 13:56
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 검증 방식: 후보 추가 튜닝 없이 PP76~82 산출 후보를 반복 holdout/bootstrap으로 비교
- 결론: PP64/PP70을 운영 기준으로 유지하고 PP82 운영형은 후보로 보류. PP82 운영형 vs PP64: MAPE -0.000007, p95 -0.000049. PP82 p95형은 tail 안정성 우선 모드로 유지할 가치가 있음.

## 후보 라벨
| label | candidate |
| --- | --- |
| hcoef_stable_source | hcoef_stable |
| incumbent_pp7 | incumbent_operational_pp_opt7 |
| pp20_p95_reference | previous_challenger_pp20 |
| pp30_p95_reference | reference_pp30_best |
| pp48_stability_reference | reference_pp48_score |
| pp52_quantile_reference | reference_pp52_challenger |
| pp58_mape_reference | reference_pp58_challenger |
| pp64_current_best | reference_pp64_current_best |
| pp70_refinement_candidate | reference_pp70_refinement |
| pp82_operational_tail_routing | ppopt82_operational_tail_routing_challenger__source=ppopt80_hard_tail__anchor_pp70__helper_pp20__score_p95_prob__thr_0p62__width_0p24__s_1p0 |
| pp82_p95_tail_routing | ppopt82_p95_tail_routing_challenger__source=ppopt77_clf_tail__anchor_pp70__helper_pp20__prob_tail85_only__thr_0p26__width_0p18__s_0p64 |
| pp_opt77_best | ppopt77_clf_tail__anchor=pp70__helper=pp48__prob=tail85_only__thr=0p1__width=0p18__s=0p64 |
| pp_opt77_p95_best | ppopt77_clf_tail__anchor=pp70__helper=pp20__prob=tail85_only__thr=0p26__width=0p18__s=0p64 |
| pp_opt78_best | ppopt78_helper_prob__anchor=pp70__helper=pp48_bias__thr=0p2__width=0p34__s=0p52 |
| pp_opt78_p95_best | ppopt78_helper_prob__anchor=pp70__helper=p95_bias__thr=0p12__width=0p2__s=0p52 |
| pp_opt80_best | ppopt80_hard_tail__anchor=pp70__helper=p95_weighted__score=risk_prob__thr=0p7__width=0p14__s=1p0 |
| pp_opt80_p95_best | ppopt80_hard_tail__anchor=pp70__helper=pp20__score=p95_prob__thr=0p62__width=0p14__s=1p0 |
| pp_opt81_best | ppopt81_tail_ensemble__anchor=pp70__helper=pp48_p95_mix__thr=0p48__width=0p22__s=0p56 |
| top_mape_in_pp76_82 | ppopt80_hard_tail__anchor=pp70__helper=pp20__score=p95_prob__thr=0p62__width=0p24__s=1p0 |

## 전체 후보 안정성 순위
| candidate_label | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_vs_pp64_MAPE | fixed_test_delta_vs_pp64_p95_APE | fixed_test_delta_vs_pp70_MAPE | fixed_test_delta_vs_pp70_p95_APE | avg_delta_vs_pp64_MAPE | avg_delta_vs_pp64_p95_APE | avg_pp64_MAPE_win_rate | avg_pp64_p95_win_rate | avg_pp64_all3_win_rate | avg_incumbent_MAPE_win_rate | avg_incumbent_p95_win_rate | replacement_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pp_opt81_best | 0.270559 | 0.807490 | -0.000005 | -0.000009 | -0.000002 | 0.000000 | -0.000004 | -0.000014 | 0.890705 | 0.410256 | 0.062500 | 0.997756 | 0.533974 | -0.015633 |
| pp_opt80_best | 0.270561 | 0.807490 | -0.000003 | -0.000009 | -0.000000 | 0.000000 | -0.000001 | -0.000001 | 0.786859 | 0.413782 | 0.054167 | 0.997756 | 0.533974 | -0.011477 |
| pp70_refinement_candidate | 0.270561 | 0.807490 | -0.000003 | -0.000009 | 0.000000 | 0.000000 | -0.000001 | -0.000001 | 0.786859 | 0.398077 | 0.054167 | 0.997756 | 0.533974 | -0.011477 |
| pp_opt77_best | 0.270720 | 0.807423 | 0.000156 | -0.000076 | 0.000159 | -0.000067 | 0.000054 | -0.000132 | 0.429808 | 0.731410 | 0.225962 | 0.980449 | 0.620513 | 0.002991 |
| pp48_stability_reference | 0.270816 | 0.807385 | 0.000252 | -0.000113 | 0.000255 | -0.000105 | 0.000116 | -0.000387 | 0.405449 | 0.722756 | 0.204487 | 0.954487 | 0.835577 | 0.004092 |
| pp82_operational_tail_routing | 0.270557 | 0.807450 | -0.000007 | -0.000049 | -0.000004 | -0.000040 | 0.000018 | 0.000050 | 0.362179 | 0.477244 | 0.037179 | 0.996795 | 0.554808 | 0.005532 |
| top_mape_in_pp76_82 | 0.270557 | 0.807450 | -0.000007 | -0.000049 | -0.000004 | -0.000040 | 0.000018 | 0.000050 | 0.362179 | 0.477244 | 0.037179 | 0.996795 | 0.554808 | 0.005532 |
| pp_opt80_p95_best | 0.270557 | 0.807422 | -0.000007 | -0.000077 | -0.000004 | -0.000068 | 0.000024 | 0.000087 | 0.330769 | 0.479808 | 0.035897 | 0.996154 | 0.551282 | 0.006804 |
| pp58_mape_reference | 0.270572 | 0.807811 | 0.000008 | 0.000312 | 0.000011 | 0.000321 | 0.000014 | 0.000109 | 0.250321 | 0.158333 | 0.013462 | 0.997756 | 0.535577 | 0.010259 |
| pp52_quantile_reference | 0.270598 | 0.807660 | 0.000034 | 0.000161 | 0.000037 | 0.000170 | 0.000024 | 0.000132 | 0.219872 | 0.152564 | 0.011218 | 0.997436 | 0.529487 | 0.011411 |
| pp_opt78_best | 0.270585 | 0.807385 | 0.000020 | -0.000114 | 0.000024 | -0.000105 | 0.000016 | -0.000007 | 0.116026 | 0.465705 | 0.006410 | 0.998077 | 0.543590 | 0.015388 |
| pp82_p95_tail_routing | 0.270651 | 0.806840 | 0.000087 | -0.000659 | 0.000090 | -0.000650 | 0.000082 | 0.000179 | 0.056090 | 0.603846 | 0.009615 | 0.995513 | 0.579167 | 0.017948 |
| pp_opt77_p95_best | 0.270651 | 0.806840 | 0.000087 | -0.000659 | 0.000090 | -0.000650 | 0.000082 | 0.000179 | 0.056090 | 0.603846 | 0.009615 | 0.995513 | 0.579167 | 0.017948 |
| pp_opt78_p95_best | 0.270701 | 0.807133 | 0.000137 | -0.000366 | 0.000140 | -0.000357 | 0.000122 | 0.000176 | 0.016026 | 0.576282 | 0.001282 | 0.997756 | 0.559936 | 0.019619 |
| pp64_current_best | 0.270564 | 0.807499 | 0.000000 | 0.000000 | 0.000003 | 0.000009 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.997756 | 0.535577 | 0.020000 |
| pp30_p95_reference | 0.270872 | 0.806932 | 0.000308 | -0.000567 | 0.000311 | -0.000558 | 0.000241 | 0.000433 | 0.007051 | 0.459936 | 0.000962 | 0.988141 | 0.614103 | 0.020298 |
| pp20_p95_reference | 0.271182 | 0.806472 | 0.000618 | -0.001026 | 0.000621 | -0.001018 | 0.000535 | 0.000973 | 0.005769 | 0.461538 | 0.001603 | 0.964103 | 0.592949 | 0.020995 |
| incumbent_pp7 | 0.271395 | 0.808130 | 0.000831 | 0.000631 | 0.000834 | 0.000640 | 0.000748 | 0.001946 | 0.002244 | 0.450641 | 0.000641 | 0.000000 | 0.000000 | 0.022238 |
| hcoef_stable_source | 0.272989 | 0.806366 | 0.002425 | -0.001133 | 0.002428 | -0.001124 | 0.002013 | 0.005297 | 0.002244 | 0.403526 | 0.000641 | 0.002564 | 0.400321 | 0.025195 |

## fixed validation/test metric
| candidate_label | eval_split | n | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| top_mape_in_pp76_82 | test | 607 | 0.137878 | 0.270557 | 0.807450 | 0.397982 | -0.000838 | -0.000680 |
| pp82_operational_tail_routing | test | 607 | 0.137878 | 0.270557 | 0.807450 | 0.397982 | -0.000838 | -0.000680 |
| pp_opt80_p95_best | test | 607 | 0.137878 | 0.270557 | 0.807422 | 0.397978 | -0.000838 | -0.000708 |
| pp_opt81_best | test | 607 | 0.137878 | 0.270559 | 0.807490 | 0.397989 | -0.000836 | -0.000640 |
| pp_opt80_best | test | 607 | 0.137878 | 0.270561 | 0.807490 | 0.397991 | -0.000834 | -0.000640 |
| pp70_refinement_candidate | test | 607 | 0.137878 | 0.270561 | 0.807490 | 0.397991 | -0.000834 | -0.000640 |
| pp64_current_best | test | 607 | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |
| pp58_mape_reference | test | 607 | 0.137878 | 0.270572 | 0.807811 | 0.397997 | -0.000823 | -0.000319 |
| pp_opt78_best | test | 607 | 0.136863 | 0.270585 | 0.807385 | 0.397998 | -0.000810 | -0.000745 |
| pp52_quantile_reference | test | 607 | 0.137878 | 0.270598 | 0.807660 | 0.397987 | -0.000797 | -0.000470 |
| pp_opt77_p95_best | test | 607 | 0.137634 | 0.270651 | 0.806840 | 0.397982 | -0.000744 | -0.001290 |
| pp82_p95_tail_routing | test | 607 | 0.137634 | 0.270651 | 0.806840 | 0.397982 | -0.000744 | -0.001290 |
| pp_opt78_p95_best | test | 607 | 0.137213 | 0.270701 | 0.807133 | 0.398021 | -0.000693 | -0.000997 |
| pp_opt77_best | test | 607 | 0.136617 | 0.270720 | 0.807423 | 0.398076 | -0.000675 | -0.000707 |
| pp48_stability_reference | test | 607 | 0.136800 | 0.270816 | 0.807385 | 0.398121 | -0.000579 | -0.000745 |
| pp30_p95_reference | test | 607 | 0.137546 | 0.270872 | 0.806932 | 0.398014 | -0.000523 | -0.001198 |
| pp20_p95_reference | test | 607 | 0.136835 | 0.271182 | 0.806472 | 0.398134 | -0.000213 | -0.001658 |
| incumbent_pp7 | test | 607 | 0.136893 | 0.271395 | 0.808130 | 0.398341 | 0.000000 | 0.000000 |
| hcoef_stable_source | test | 607 | 0.138803 | 0.272989 | 0.806366 | 0.398822 | 0.001594 | -0.001764 |
| pp48_stability_reference | validation_oof | 519 | 0.122610 | 0.206179 | 0.636376 | 0.323684 | -0.000844 | -0.000219 |
| pp_opt77_best | validation_oof | 519 | 0.121961 | 0.206188 | 0.637867 | 0.323718 | -0.000835 | 0.001272 |
| pp_opt81_best | validation_oof | 519 | 0.122635 | 0.206279 | 0.637897 | 0.323780 | -0.000744 | 0.001302 |
| pp70_refinement_candidate | validation_oof | 519 | 0.122635 | 0.206280 | 0.637897 | 0.323781 | -0.000743 | 0.001302 |
| pp_opt80_best | validation_oof | 519 | 0.122635 | 0.206280 | 0.637897 | 0.323781 | -0.000743 | 0.001302 |
| pp64_current_best | validation_oof | 519 | 0.122635 | 0.206281 | 0.637922 | 0.323780 | -0.000742 | 0.001327 |
| pp_opt78_best | validation_oof | 519 | 0.122635 | 0.206298 | 0.637621 | 0.323790 | -0.000725 | 0.001027 |
| pp52_quantile_reference | validation_oof | 519 | 0.122430 | 0.206301 | 0.638550 | 0.323793 | -0.000722 | 0.001955 |
| pp58_mape_reference | validation_oof | 519 | 0.122635 | 0.206304 | 0.638224 | 0.323798 | -0.000719 | 0.001629 |
| top_mape_in_pp76_82 | validation_oof | 519 | 0.122635 | 0.206316 | 0.637897 | 0.323832 | -0.000707 | 0.001302 |
| pp82_operational_tail_routing | validation_oof | 519 | 0.122635 | 0.206316 | 0.637897 | 0.323832 | -0.000707 | 0.001302 |
| pp_opt80_p95_best | validation_oof | 519 | 0.122635 | 0.206325 | 0.637897 | 0.323848 | -0.000698 | 0.001302 |
| pp_opt77_p95_best | validation_oof | 519 | 0.122780 | 0.206340 | 0.637897 | 0.323887 | -0.000683 | 0.001302 |
| pp82_p95_tail_routing | validation_oof | 519 | 0.122780 | 0.206340 | 0.637897 | 0.323887 | -0.000683 | 0.001302 |
| pp_opt78_p95_best | validation_oof | 519 | 0.122635 | 0.206410 | 0.637782 | 0.323810 | -0.000613 | 0.001187 |
| pp30_p95_reference | validation_oof | 519 | 0.122377 | 0.206462 | 0.638459 | 0.323853 | -0.000562 | 0.001864 |
| pp20_p95_reference | validation_oof | 519 | 0.125408 | 0.206777 | 0.638367 | 0.324048 | -0.000246 | 0.001773 |
| incumbent_pp7 | validation_oof | 519 | 0.125923 | 0.207023 | 0.636595 | 0.324133 | 0.000000 | 0.000000 |
| hcoef_stable_source | validation_oof | 519 | 0.125993 | 0.208206 | 0.647948 | 0.325185 | 0.001183 | 0.011353 |

## PP82 시나리오별 PP64 대비 안정성
| candidate_label | eval_split | scenario | repeats | mean_delta_vs_pp64_MAPE | mean_delta_vs_pp64_p95_APE | pp64_MAPE_win_rate | pp64_p95_win_rate | pp64_all3_win_rate | mean_delta_vs_incumbent_MAPE | mean_delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pp82_operational_tail_routing | test | artist_group_holdout | 260 | -0.000008 | 0.000054 | 0.696154 | 0.384615 | 0.115385 | -0.000839 | -0.004622 |
| pp82_operational_tail_routing | test | confidence_stratified_rows | 260 | -0.000008 | 0.000021 | 0.719231 | 0.519231 | 0.096154 | -0.000838 | -0.003397 |
| pp82_operational_tail_routing | test | full_split | 1 | -0.000007 | -0.000049 | 1.000000 | 1.000000 | 0.000000 | -0.000838 | -0.000680 |
| pp82_operational_tail_routing | test | price_band_stratified_rows | 260 | -0.000008 | 0.000009 | 0.703846 | 0.457692 | 0.130769 | -0.000841 | -0.004174 |
| pp82_operational_tail_routing | test | risk_focus_bootstrap | 260 | -0.000010 | 0.000491 | 0.573077 | 0.384615 | 0.015385 | -0.000599 | -0.001809 |
| pp82_operational_tail_routing | test | row_bootstrap | 260 | -0.000009 | 0.000096 | 0.646154 | 0.411538 | 0.088462 | -0.000814 | -0.005746 |
| pp82_operational_tail_routing | validation_oof | artist_group_holdout | 260 | 0.000035 | -0.000001 | 0.000000 | 0.380769 | 0.000000 | -0.000717 | -0.001064 |
| pp82_operational_tail_routing | validation_oof | confidence_stratified_rows | 260 | 0.000035 | 0.000001 | 0.000000 | 0.342308 | 0.000000 | -0.000706 | -0.000623 |
| pp82_operational_tail_routing | validation_oof | full_split | 1 | 0.000035 | -0.000025 | 0.000000 | 1.000000 | 0.000000 | -0.000707 | 0.001302 |
| pp82_operational_tail_routing | validation_oof | price_band_stratified_rows | 260 | 0.000034 | -0.000002 | 0.000000 | 0.388462 | 0.000000 | -0.000702 | -0.000602 |
| pp82_operational_tail_routing | validation_oof | risk_focus_bootstrap | 260 | 0.000089 | -0.000001 | 0.000000 | 0.161538 | 0.000000 | -0.000445 | -0.000215 |
| pp82_operational_tail_routing | validation_oof | row_bootstrap | 260 | 0.000036 | 0.000009 | 0.007692 | 0.296154 | 0.000000 | -0.000717 | -0.001117 |
| pp82_p95_tail_routing | test | artist_group_holdout | 260 | 0.000090 | 0.000271 | 0.007692 | 0.630769 | 0.003846 | -0.000741 | -0.004404 |
| pp82_p95_tail_routing | test | confidence_stratified_rows | 260 | 0.000087 | 0.000183 | 0.011538 | 0.607692 | 0.000000 | -0.000744 | -0.003235 |
| pp82_p95_tail_routing | test | full_split | 1 | 0.000087 | -0.000659 | 0.000000 | 1.000000 | 0.000000 | -0.000744 | -0.001290 |
| pp82_p95_tail_routing | test | price_band_stratified_rows | 260 | 0.000085 | 0.000279 | 0.019231 | 0.573077 | 0.003846 | -0.000747 | -0.003904 |
| pp82_p95_tail_routing | test | risk_focus_bootstrap | 260 | 0.000143 | 0.001606 | 0.157692 | 0.353846 | 0.023077 | -0.000446 | -0.000694 |
| pp82_p95_tail_routing | test | row_bootstrap | 260 | 0.000084 | 0.000442 | 0.092308 | 0.469231 | 0.019231 | -0.000722 | -0.005400 |
| pp82_p95_tail_routing | validation_oof | artist_group_holdout | 260 | 0.000058 | 0.000076 | 0.065385 | 0.557692 | 0.011538 | -0.000695 | -0.000987 |
| pp82_p95_tail_routing | validation_oof | confidence_stratified_rows | 260 | 0.000060 | 0.000068 | 0.030769 | 0.611538 | 0.011538 | -0.000680 | -0.000556 |
| pp82_p95_tail_routing | validation_oof | full_split | 1 | 0.000059 | -0.000025 | 0.000000 | 1.000000 | 0.000000 | -0.000683 | 0.001302 |
| pp82_p95_tail_routing | validation_oof | price_band_stratified_rows | 260 | 0.000059 | 0.000054 | 0.030769 | 0.626923 | 0.003846 | -0.000678 | -0.000546 |
| pp82_p95_tail_routing | validation_oof | risk_focus_bootstrap | 260 | 0.000116 | -0.000124 | 0.088462 | 0.326923 | 0.011538 | -0.000419 | -0.000338 |
| pp82_p95_tail_routing | validation_oof | row_bootstrap | 260 | 0.000061 | -0.000018 | 0.169231 | 0.488462 | 0.026923 | -0.000692 | -0.001145 |

## 해석
- PP82 운영형은 fixed test에서 PP64/PP70보다 MAPE와 p95가 모두 낮다.
- 운영 교체 여부는 반복 검증에서 p95 승률이 충분히 따라오는지가 핵심이다.
- PP82 p95형은 p95를 크게 낮추지만 MAPE가 PP64보다 높으므로 기본 운영값이 아니라 목적형 옵션으로 분리하는 것이 맞다.

## 실행 설정
```json
{
  "experiment_id": "PP-OPT83-88",
  "experiment_slug": "PP-OPT83_88_warm_pp82_stability_validation",
  "created_at": "2026-06-09T13:56:52",
  "seed": 20260609,
  "repeats_per_resample_scenario": 260,
  "sample_fraction": 0.72,
  "selected_candidates": {
    "hcoef_stable_source": "hcoef_stable",
    "incumbent_pp7": "incumbent_operational_pp_opt7",
    "pp20_p95_reference": "previous_challenger_pp20",
    "pp30_p95_reference": "reference_pp30_best",
    "pp48_stability_reference": "reference_pp48_score",
    "pp52_quantile_reference": "reference_pp52_challenger",
    "pp58_mape_reference": "reference_pp58_challenger",
    "pp64_current_best": "reference_pp64_current_best",
    "pp70_refinement_candidate": "reference_pp70_refinement",
    "pp82_operational_tail_routing": "ppopt82_operational_tail_routing_challenger__source=ppopt80_hard_tail__anchor_pp70__helper_pp20__score_p95_prob__thr_0p62__width_0p24__s_1p0",
    "pp82_p95_tail_routing": "ppopt82_p95_tail_routing_challenger__source=ppopt77_clf_tail__anchor_pp70__helper_pp20__prob_tail85_only__thr_0p26__width_0p18__s_0p64",
    "pp_opt77_best": "ppopt77_clf_tail__anchor=pp70__helper=pp48__prob=tail85_only__thr=0p1__width=0p18__s=0p64",
    "pp_opt77_p95_best": "ppopt77_clf_tail__anchor=pp70__helper=pp20__prob=tail85_only__thr=0p26__width=0p18__s=0p64",
    "pp_opt78_best": "ppopt78_helper_prob__anchor=pp70__helper=pp48_bias__thr=0p2__width=0p34__s=0p52",
    "pp_opt78_p95_best": "ppopt78_helper_prob__anchor=pp70__helper=p95_bias__thr=0p12__width=0p2__s=0p52",
    "pp_opt80_best": "ppopt80_hard_tail__anchor=pp70__helper=p95_weighted__score=risk_prob__thr=0p7__width=0p14__s=1p0",
    "pp_opt80_p95_best": "ppopt80_hard_tail__anchor=pp70__helper=pp20__score=p95_prob__thr=0p62__width=0p14__s=1p0",
    "pp_opt81_best": "ppopt81_tail_ensemble__anchor=pp70__helper=pp48_p95_mix__thr=0p48__width=0p22__s=0p56",
    "top_mape_in_pp76_82": "ppopt80_hard_tail__anchor=pp70__helper=pp20__score=p95_prob__thr=0p62__width=0p24__s=1p0"
  },
  "candidate_count": 19,
  "validation_rows": 519,
  "test_rows": 607,
  "decision": {
    "operational_verdict": "PP64/PP70을 운영 기준으로 유지하고 PP82 운영형은 후보로 보류",
    "p95_mode_verdict": "PP82 p95형은 tail 안정성 우선 모드로 유지할 가치가 있음",
    "pp82_operational_fixed_test_MAPE": 0.2705565870369284,
    "pp82_operational_fixed_test_p95_APE": 0.807450308348755,
    "pp82_operational_delta_vs_pp64_MAPE": -7.454878731938397e-06,
    "pp82_operational_delta_vs_pp64_p95_APE": -4.8543957354874046e-05,
    "pp82_operational_delta_vs_pp70_MAPE": -4.388340047900563e-06,
    "pp82_operational_delta_vs_pp70_p95_APE": -3.975254909294179e-05,
    "pp82_operational_avg_pp64_MAPE_win_rate": 0.36217948717948717,
    "pp82_operational_avg_pp64_p95_win_rate": 0.47724358974358977,
    "pp82_operational_avg_pp64_all3_win_rate": 0.03717948717948718,
    "pp82_p95_fixed_test_MAPE": 0.2706512801714569,
    "pp82_p95_fixed_test_p95_APE": 0.8068395739408173,
    "pp82_p95_delta_vs_pp64_MAPE": 8.72382557965401e-05,
    "pp82_p95_delta_vs_pp64_p95_APE": -0.0006592783652925593,
    "pp82_p95_avg_incumbent_MAPE_win_rate": 0.9955128205128205,
    "pp82_p95_avg_incumbent_p95_win_rate": 0.5791666666666667,
    "reference_pp64_MAPE": 0.27056404191566036,
    "reference_pp64_p95_APE": 0.8074988523061098,
    "reference_pp70_MAPE": 0.2705609753769763,
    "reference_pp70_p95_APE": 0.8074900608978479
  },
  "items": [
    {
      "item_id": "PP-OPT83",
      "priority": "1",
      "title": "fixed validation/test PP82 comparison",
      "description": "PP64, PP70, PP82 운영형, PP82 p95형을 fixed validation/test에서 비교한다."
    },
    {
      "item_id": "PP-OPT84",
      "priority": "2",
      "title": "validation repeated stability",
      "description": "validation OOF에서 confidence, price, artist, risk 기반 반복 부분표본 승률을 계산한다."
    },
    {
      "item_id": "PP-OPT85",
      "priority": "3",
      "title": "test bootstrap stress stability",
      "description": "fixed test를 bootstrap/stratified resample하여 후보 간 승률을 계산한다."
    },
    {
      "item_id": "PP-OPT86",
      "priority": "4",
      "title": "PP82 operational replacement decision",
      "description": "PP82 운영형을 PP64/PP70의 운영 기준으로 교체할 수 있는지 판단한다."
    },
    {
      "item_id": "PP-OPT87",
      "priority": "5",
      "title": "PP82 p95 mode decision",
      "description": "PP82 p95형을 운영 기본값이 아닌 tail 안정성 우선 모드로 둘지 판단한다."
    },
    {
      "item_id": "PP-OPT88",
      "priority": "6",
      "title": "next experiment recommendation",
      "description": "PP82 검증 결과를 바탕으로 다음 실험 방향을 정리한다."
    }
  ],
  "sources": {
    "pp76_config": "experiments/track6/PP-OPT76_82_warm_tail_routing_experiments/artifacts/run_config.json",
    "pp76_predictions": "experiments/track6/PP-OPT76_82_warm_tail_routing_experiments/outputs/candidate_predictions.csv",
    "pp76_aggregate": "experiments/track6/PP-OPT76_82_warm_tail_routing_experiments/outputs/aggregate_candidate_stability.csv",
    "pp76_item_summary": "experiments/track6/PP-OPT76_82_warm_tail_routing_experiments/outputs/experiment_item_summary.csv",
    "pp71_validation_helper": "scripts/track6/run_pp_opt71_75_warm_pp70_stability_validation.py"
  }
}
```