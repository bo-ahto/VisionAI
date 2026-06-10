# PP-OPT14~20 Warm Gate Refinement 결과

- 작성일: 2026-06-09 11:23
- 데이터 기준: 제출용 제외, Warm validation OOF 519건 + fixed test 607건
- 기준 후보: PP-OPT7 운영 후보
- 전체 후보 수: 822
- 운영 대체 통과 후보 수: 172

## 최종 selection protocol 후보
- 선택 후보: `ppopt20_protocol_selected__source=ppopt19_segment_tuning__profile_low_support_tail__artist_cat_artist_mean__as_0p25__ts_0p55`
- 원본 후보: `ppopt19_segment_tuning__profile=low_support_tail__artist=cat_artist_mean__as=0p25__ts=0p55`
- 원본 실험: `PP-OPT19` / `segment_specific_gate_tuning`

| eval_split | n | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | delta_vs_incumbent_MdAPE | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | 607 | 0.136835 | 0.271182 | 0.806472 | 0.398134 | 0.780890 | 0.883031 | -0.000058 | -0.000213 | -0.001658 |
| validation_oof | 519 | 0.125408 | 0.206777 | 0.638367 | 0.324048 | 0.782274 | 0.911368 | -0.000515 | -0.000246 | 0.001773 |

## 현재 운영 후보 성능
| eval_split | n | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| test | 607 | 0.136893 | 0.271395 | 0.808130 | 0.398341 | 0.779242 | 0.883031 |
| validation_oof | 519 | 0.125923 | 0.207023 | 0.636595 | 0.324133 | 0.782274 | 0.911368 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | stable_validation_pass_vs_incumbent | operational_pass_vs_incumbent | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | 구간별 PP-OPT9 분리 튜닝 | 90 | 0.271062 | 0.806313 | -0.000332 | -0.001817 | 1.000000 | 0.541667 | True | True | segment_specific_gate_tuning | ppopt19_segment_tuning__profile=price_tail_high__artist=artist__as=0p35__ts=0p75 |
| 1 | PP-OPT9 gate threshold 정밀 탐색 | 216 | 0.271103 | 0.806659 | -0.000292 | -0.001471 | 1.000000 | 0.541667 | True | True | gate_threshold_grid | ppopt14_gate_grid__artist=artist_stable__sthr=0p12__tthr=0p25__as=0p2__ts=0p75__cap=0p024 |
| 7 | 최종 후보 selection protocol | 1 | 0.271182 | 0.806472 | -0.000213 | -0.001658 | 1.000000 | 0.554167 | True | True | selection_protocol | ppopt20_protocol_selected__source=ppopt19_segment_tuning__profile_low_support_tail__artist_cat_artist_mean__as_0p25__ts_0p55 |
| 4 | MdAPE 악화 방지 guard | 27 | 0.271240 | 0.807031 | -0.000154 | -0.001099 | 0.970833 | 0.529167 | True | True | mdape_guard | ppopt17_mdape_guard__src=pp9_best_operational__floor=0p4__s=0p9 |
| 3 | tail-risk label 재정의 | 90 | 0.271280 | 0.806409 | -0.000115 | -0.001721 | 0.900000 | 0.679167 | True | True | tail_label_redefinition | ppopt16_tail_label__label=p90__src=xgb_tail__thr=0p2__s=0p65 |
| 2 | PP-OPT12 MAPE 신호의 안정 흡수 | 72 | 0.270374 | 0.807277 | -0.001021 | -0.000853 | 1.000000 | 0.500000 | False | False | pp12_signal_absorption | ppopt15_absorb_pp12__base=pp9_best_mape__p12s=0p34__p9s=1p05__cap=0p026 |
| 5 | 제약 조건 기반 보정값 앙상블 | 324 | 0.270837 | 0.807174 | -0.000558 | -0.000956 | 1.000000 | 0.533333 | False | False | constrained_correction_ensemble | ppopt18_constrained_ensemble__aw=0p22__cw=0p24__xw=0p5__qw=0p12__p12w=0p16__cap=0p022 |

## 운영 대체 통과 후보 상위
| item_id | candidate | family | test_MdAPE | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MdAPE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | incumbent_all3_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-OPT19 | ppopt19_segment_tuning__profile=price_tail_high__artist=artist__as=0p35__ts=0p75 | segment_specific_gate_tuning | 0.136523 | 0.271062 | 0.806313 | -0.000369 | -0.000332 | -0.001817 | 1.000000 | 0.541667 | 0.391667 | -0.001116 |
| PP-OPT19 | ppopt19_segment_tuning__profile=price_tail_high__artist=artist__as=0p35__ts=0p55 | segment_specific_gate_tuning | 0.136523 | 0.271067 | 0.806581 | -0.000369 | -0.000328 | -0.001549 | 1.000000 | 0.541667 | 0.391667 | -0.001102 |
| PP-OPT19 | ppopt19_segment_tuning__profile=balanced_segments__artist=artist__as=0p25__ts=0p55 | segment_specific_gate_tuning | 0.136615 | 0.271202 | 0.806551 | -0.000277 | -0.000193 | -0.001579 | 0.995833 | 0.533333 | 0.383333 | -0.001098 |
| PP-OPT19 | ppopt19_segment_tuning__profile=balanced_segments__artist=artist__as=0p25__ts=0p75 | segment_specific_gate_tuning | 0.136615 | 0.271190 | 0.806297 | -0.000277 | -0.000205 | -0.001833 | 0.995833 | 0.533333 | 0.379167 | -0.001096 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p12__tthr=0p25__as=0p2__ts=0p75__cap=0p024 | gate_threshold_grid | 0.136578 | 0.271103 | 0.806659 | -0.000315 | -0.000292 | -0.001471 | 1.000000 | 0.541667 | 0.391667 | -0.001091 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p12__tthr=0p25__as=0p2__ts=0p75__cap=0p02 | gate_threshold_grid | 0.136578 | 0.271122 | 0.806659 | -0.000315 | -0.000273 | -0.001471 | 1.000000 | 0.541667 | 0.391667 | -0.001066 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p12__tthr=0p25__as=0p2__ts=0p55__cap=0p024 | gate_threshold_grid | 0.136578 | 0.271136 | 0.807089 | -0.000315 | -0.000259 | -0.001041 | 1.000000 | 0.541667 | 0.383333 | -0.001058 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p12__tthr=0p25__as=0p2__ts=0p55__cap=0p02 | gate_threshold_grid | 0.136578 | 0.271137 | 0.807089 | -0.000315 | -0.000258 | -0.001041 | 1.000000 | 0.541667 | 0.383333 | -0.001051 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p12__tthr=0p35__as=0p2__ts=0p75__cap=0p024 | gate_threshold_grid | 0.136578 | 0.271124 | 0.807776 | -0.000315 | -0.000270 | -0.000354 | 1.000000 | 0.541667 | 0.387500 | -0.001044 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p12__tthr=0p35__as=0p2__ts=0p75__cap=0p02 | gate_threshold_grid | 0.136578 | 0.271126 | 0.807776 | -0.000315 | -0.000269 | -0.000354 | 1.000000 | 0.541667 | 0.387500 | -0.001038 |
| PP-OPT19 | ppopt19_segment_tuning__profile=price_tail_high__artist=artist__as=0p25__ts=0p75 | segment_specific_gate_tuning | 0.136580 | 0.271107 | 0.806287 | -0.000313 | -0.000288 | -0.001843 | 0.987500 | 0.550000 | 0.375000 | -0.001027 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p12__tthr=0p35__as=0p2__ts=0p55__cap=0p02 | gate_threshold_grid | 0.136578 | 0.271155 | 0.807909 | -0.000315 | -0.000240 | -0.000221 | 1.000000 | 0.541667 | 0.387500 | -0.001021 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p12__tthr=0p35__as=0p2__ts=0p55__cap=0p024 | gate_threshold_grid | 0.136578 | 0.271155 | 0.807909 | -0.000315 | -0.000240 | -0.000221 | 1.000000 | 0.541667 | 0.387500 | -0.001021 |
| PP-OPT19 | ppopt19_segment_tuning__profile=price_tail_high__artist=artist__as=0p25__ts=0p55 | segment_specific_gate_tuning | 0.136580 | 0.271113 | 0.806532 | -0.000313 | -0.000282 | -0.001598 | 0.995833 | 0.541667 | 0.375000 | -0.001014 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p12__tthr=0p15__as=0p2__ts=0p55__cap=0p024 | gate_threshold_grid | 0.136578 | 0.271141 | 0.806325 | -0.000315 | -0.000253 | -0.001805 | 0.987500 | 0.529167 | 0.391667 | -0.000998 |
| PP-OPT19 | ppopt19_segment_tuning__profile=confidence_tail__artist=artist__as=0p25__ts=0p75 | segment_specific_gate_tuning | 0.136615 | 0.271155 | 0.806257 | -0.000277 | -0.000240 | -0.001873 | 0.987500 | 0.545833 | 0.375000 | -0.000995 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p18__tthr=0p25__as=0p2__ts=0p75__cap=0p024 | gate_threshold_grid | 0.136608 | 0.271120 | 0.806633 | -0.000284 | -0.000275 | -0.001497 | 0.987500 | 0.541667 | 0.354167 | -0.000989 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p18__tthr=0p25__as=0p2__ts=0p55__cap=0p024 | gate_threshold_grid | 0.136608 | 0.271153 | 0.807063 | -0.000284 | -0.000242 | -0.001067 | 1.000000 | 0.541667 | 0.358333 | -0.000982 |
| PP-OPT19 | ppopt19_segment_tuning__profile=confidence_tail__artist=artist__as=0p25__ts=0p55 | segment_specific_gate_tuning | 0.136615 | 0.271176 | 0.806776 | -0.000277 | -0.000219 | -0.001354 | 0.991667 | 0.529167 | 0.366667 | -0.000977 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p12__tthr=0p15__as=0p2__ts=0p55__cap=0p02 | gate_threshold_grid | 0.136578 | 0.271157 | 0.806625 | -0.000315 | -0.000238 | -0.001505 | 0.987500 | 0.529167 | 0.391667 | -0.000975 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p18__tthr=0p25__as=0p2__ts=0p55__cap=0p02 | gate_threshold_grid | 0.136608 | 0.271154 | 0.807063 | -0.000284 | -0.000241 | -0.001067 | 1.000000 | 0.541667 | 0.358333 | -0.000974 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p18__tthr=0p35__as=0p2__ts=0p75__cap=0p02 | gate_threshold_grid | 0.136608 | 0.271143 | 0.807748 | -0.000284 | -0.000252 | -0.000382 | 1.000000 | 0.537500 | 0.366667 | -0.000969 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p18__tthr=0p35__as=0p2__ts=0p75__cap=0p024 | gate_threshold_grid | 0.136608 | 0.271142 | 0.807748 | -0.000284 | -0.000253 | -0.000382 | 0.995833 | 0.537500 | 0.362500 | -0.000966 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p18__tthr=0p25__as=0p2__ts=0p75__cap=0p02 | gate_threshold_grid | 0.136608 | 0.271139 | 0.806633 | -0.000284 | -0.000256 | -0.001497 | 0.987500 | 0.541667 | 0.354167 | -0.000964 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p18__tthr=0p35__as=0p2__ts=0p55__cap=0p02 | gate_threshold_grid | 0.136608 | 0.271173 | 0.807881 | -0.000284 | -0.000222 | -0.000248 | 1.000000 | 0.537500 | 0.366667 | -0.000952 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p18__tthr=0p35__as=0p2__ts=0p55__cap=0p024 | gate_threshold_grid | 0.136608 | 0.271173 | 0.807881 | -0.000284 | -0.000222 | -0.000248 | 1.000000 | 0.537500 | 0.366667 | -0.000952 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p12__tthr=0p15__as=0p2__ts=0p75__cap=0p024 | gate_threshold_grid | 0.136578 | 0.271139 | 0.806300 | -0.000315 | -0.000256 | -0.001830 | 0.975000 | 0.529167 | 0.387500 | -0.000931 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p24__tthr=0p25__as=0p2__ts=0p75__cap=0p024 | gate_threshold_grid | 0.136639 | 0.271139 | 0.806608 | -0.000254 | -0.000256 | -0.001522 | 0.987500 | 0.550000 | 0.337500 | -0.000924 |
| PP-OPT19 | ppopt19_segment_tuning__profile=balanced_segments__artist=cat_artist_mean__as=0p35__ts=0p75 | segment_specific_gate_tuning | 0.136938 | 0.271150 | 0.806299 | 0.000045 | -0.000245 | -0.001831 | 0.995833 | 0.541667 | 0.320833 | -0.000924 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p12__tthr=0p15__as=0p2__ts=0p75__cap=0p02 | gate_threshold_grid | 0.136578 | 0.271169 | 0.806599 | -0.000315 | -0.000226 | -0.001531 | 0.975000 | 0.529167 | 0.387500 | -0.000909 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p18__tthr=0p15__as=0p2__ts=0p55__cap=0p024 | gate_threshold_grid | 0.136608 | 0.271158 | 0.806320 | -0.000284 | -0.000237 | -0.001810 | 0.987500 | 0.525000 | 0.358333 | -0.000902 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p24__tthr=0p25__as=0p2__ts=0p75__cap=0p02 | gate_threshold_grid | 0.136639 | 0.271158 | 0.806608 | -0.000254 | -0.000237 | -0.001522 | 0.987500 | 0.550000 | 0.337500 | -0.000899 |
| PP-OPT19 | ppopt19_segment_tuning__profile=balanced_segments__artist=cat_artist_mean__as=0p35__ts=0p55 | segment_specific_gate_tuning | 0.136938 | 0.271162 | 0.806536 | 0.000045 | -0.000233 | -0.001594 | 1.000000 | 0.537500 | 0.312500 | -0.000898 |
| PP-OPT19 | ppopt19_segment_tuning__profile=low_support_tail__artist=cat_artist_mean__as=0p25__ts=0p55 | segment_specific_gate_tuning | 0.136835 | 0.271182 | 0.806472 | -0.000058 | -0.000213 | -0.001658 | 1.000000 | 0.554167 | 0.316667 | -0.000883 |
| PP-OPT20 | ppopt20_protocol_selected__source=ppopt19_segment_tuning__profile_low_support_tail__artist_cat_artist_mean__as_0p25__ts_0p55 | selection_protocol | 0.136835 | 0.271182 | 0.806472 | -0.000058 | -0.000213 | -0.001658 | 1.000000 | 0.554167 | 0.316667 | -0.000883 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p18__tthr=0p15__as=0p2__ts=0p55__cap=0p02 | gate_threshold_grid | 0.136608 | 0.271174 | 0.806619 | -0.000284 | -0.000221 | -0.001511 | 0.987500 | 0.525000 | 0.358333 | -0.000879 |
| PP-OPT19 | ppopt19_segment_tuning__profile=balanced_segments__artist=cat_artist_mean__as=0p25__ts=0p55 | segment_specific_gate_tuning | 0.136876 | 0.271215 | 0.806500 | -0.000017 | -0.000180 | -0.001630 | 0.995833 | 0.545833 | 0.312500 | -0.000872 |
| PP-OPT19 | ppopt19_segment_tuning__profile=price_tail_high__artist=cat_artist_mean__as=0p25__ts=0p55 | segment_specific_gate_tuning | 0.136927 | 0.271115 | 0.806488 | 0.000035 | -0.000280 | -0.001642 | 0.987500 | 0.579167 | 0.333333 | -0.000868 |
| PP-OPT19 | ppopt19_segment_tuning__profile=low_support_tail__artist=cat_artist_mean__as=0p25__ts=0p75 | segment_specific_gate_tuning | 0.136835 | 0.271155 | 0.806334 | -0.000058 | -0.000240 | -0.001796 | 0.987500 | 0.558333 | 0.304167 | -0.000867 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p24__tthr=0p35__as=0p2__ts=0p75__cap=0p024 | gate_threshold_grid | 0.136639 | 0.271163 | 0.807721 | -0.000254 | -0.000232 | -0.000409 | 0.995833 | 0.541667 | 0.329167 | -0.000867 |

## Test에서 MAPE와 p95를 동시에 개선한 후보
| item_id | candidate | family | test_MdAPE | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MdAPE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | incumbent_all3_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-OPT19 | ppopt19_segment_tuning__profile=price_tail_high__artist=artist__as=0p35__ts=0p75 | segment_specific_gate_tuning | 0.136523 | 0.271062 | 0.806313 | -0.000369 | -0.000332 | -0.001817 | 1.000000 | 0.541667 | 0.391667 | -0.001116 |
| PP-OPT19 | ppopt19_segment_tuning__profile=price_tail_high__artist=artist__as=0p35__ts=0p55 | segment_specific_gate_tuning | 0.136523 | 0.271067 | 0.806581 | -0.000369 | -0.000328 | -0.001549 | 1.000000 | 0.541667 | 0.391667 | -0.001102 |
| PP-OPT19 | ppopt19_segment_tuning__profile=balanced_segments__artist=artist__as=0p25__ts=0p55 | segment_specific_gate_tuning | 0.136615 | 0.271202 | 0.806551 | -0.000277 | -0.000193 | -0.001579 | 0.995833 | 0.533333 | 0.383333 | -0.001098 |
| PP-OPT19 | ppopt19_segment_tuning__profile=balanced_segments__artist=artist__as=0p25__ts=0p75 | segment_specific_gate_tuning | 0.136615 | 0.271190 | 0.806297 | -0.000277 | -0.000205 | -0.001833 | 0.995833 | 0.533333 | 0.379167 | -0.001096 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p12__tthr=0p25__as=0p2__ts=0p75__cap=0p024 | gate_threshold_grid | 0.136578 | 0.271103 | 0.806659 | -0.000315 | -0.000292 | -0.001471 | 1.000000 | 0.541667 | 0.391667 | -0.001091 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p12__tthr=0p25__as=0p2__ts=0p75__cap=0p02 | gate_threshold_grid | 0.136578 | 0.271122 | 0.806659 | -0.000315 | -0.000273 | -0.001471 | 1.000000 | 0.541667 | 0.391667 | -0.001066 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p12__tthr=0p25__as=0p2__ts=0p55__cap=0p024 | gate_threshold_grid | 0.136578 | 0.271136 | 0.807089 | -0.000315 | -0.000259 | -0.001041 | 1.000000 | 0.541667 | 0.383333 | -0.001058 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p12__tthr=0p25__as=0p2__ts=0p55__cap=0p02 | gate_threshold_grid | 0.136578 | 0.271137 | 0.807089 | -0.000315 | -0.000258 | -0.001041 | 1.000000 | 0.541667 | 0.383333 | -0.001051 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p12__tthr=0p35__as=0p2__ts=0p75__cap=0p024 | gate_threshold_grid | 0.136578 | 0.271124 | 0.807776 | -0.000315 | -0.000270 | -0.000354 | 1.000000 | 0.541667 | 0.387500 | -0.001044 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p12__tthr=0p35__as=0p2__ts=0p75__cap=0p02 | gate_threshold_grid | 0.136578 | 0.271126 | 0.807776 | -0.000315 | -0.000269 | -0.000354 | 1.000000 | 0.541667 | 0.387500 | -0.001038 |
| PP-OPT19 | ppopt19_segment_tuning__profile=price_tail_high__artist=artist__as=0p25__ts=0p75 | segment_specific_gate_tuning | 0.136580 | 0.271107 | 0.806287 | -0.000313 | -0.000288 | -0.001843 | 0.987500 | 0.550000 | 0.375000 | -0.001027 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p12__tthr=0p35__as=0p2__ts=0p55__cap=0p02 | gate_threshold_grid | 0.136578 | 0.271155 | 0.807909 | -0.000315 | -0.000240 | -0.000221 | 1.000000 | 0.541667 | 0.387500 | -0.001021 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p12__tthr=0p35__as=0p2__ts=0p55__cap=0p024 | gate_threshold_grid | 0.136578 | 0.271155 | 0.807909 | -0.000315 | -0.000240 | -0.000221 | 1.000000 | 0.541667 | 0.387500 | -0.001021 |
| PP-OPT19 | ppopt19_segment_tuning__profile=price_tail_high__artist=artist__as=0p25__ts=0p55 | segment_specific_gate_tuning | 0.136580 | 0.271113 | 0.806532 | -0.000313 | -0.000282 | -0.001598 | 0.995833 | 0.541667 | 0.375000 | -0.001014 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p12__tthr=0p15__as=0p2__ts=0p55__cap=0p024 | gate_threshold_grid | 0.136578 | 0.271141 | 0.806325 | -0.000315 | -0.000253 | -0.001805 | 0.987500 | 0.529167 | 0.391667 | -0.000998 |
| PP-OPT19 | ppopt19_segment_tuning__profile=confidence_tail__artist=artist__as=0p25__ts=0p75 | segment_specific_gate_tuning | 0.136615 | 0.271155 | 0.806257 | -0.000277 | -0.000240 | -0.001873 | 0.987500 | 0.545833 | 0.375000 | -0.000995 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p18__tthr=0p25__as=0p2__ts=0p75__cap=0p024 | gate_threshold_grid | 0.136608 | 0.271120 | 0.806633 | -0.000284 | -0.000275 | -0.001497 | 0.987500 | 0.541667 | 0.354167 | -0.000989 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p18__tthr=0p25__as=0p2__ts=0p55__cap=0p024 | gate_threshold_grid | 0.136608 | 0.271153 | 0.807063 | -0.000284 | -0.000242 | -0.001067 | 1.000000 | 0.541667 | 0.358333 | -0.000982 |
| PP-OPT19 | ppopt19_segment_tuning__profile=confidence_tail__artist=artist__as=0p25__ts=0p55 | segment_specific_gate_tuning | 0.136615 | 0.271176 | 0.806776 | -0.000277 | -0.000219 | -0.001354 | 0.991667 | 0.529167 | 0.366667 | -0.000977 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p12__tthr=0p15__as=0p2__ts=0p55__cap=0p02 | gate_threshold_grid | 0.136578 | 0.271157 | 0.806625 | -0.000315 | -0.000238 | -0.001505 | 0.987500 | 0.529167 | 0.391667 | -0.000975 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p18__tthr=0p25__as=0p2__ts=0p55__cap=0p02 | gate_threshold_grid | 0.136608 | 0.271154 | 0.807063 | -0.000284 | -0.000241 | -0.001067 | 1.000000 | 0.541667 | 0.358333 | -0.000974 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p18__tthr=0p35__as=0p2__ts=0p75__cap=0p02 | gate_threshold_grid | 0.136608 | 0.271143 | 0.807748 | -0.000284 | -0.000252 | -0.000382 | 1.000000 | 0.537500 | 0.366667 | -0.000969 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p18__tthr=0p35__as=0p2__ts=0p75__cap=0p024 | gate_threshold_grid | 0.136608 | 0.271142 | 0.807748 | -0.000284 | -0.000253 | -0.000382 | 0.995833 | 0.537500 | 0.362500 | -0.000966 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p18__tthr=0p25__as=0p2__ts=0p75__cap=0p02 | gate_threshold_grid | 0.136608 | 0.271139 | 0.806633 | -0.000284 | -0.000256 | -0.001497 | 0.987500 | 0.541667 | 0.354167 | -0.000964 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p18__tthr=0p35__as=0p2__ts=0p55__cap=0p02 | gate_threshold_grid | 0.136608 | 0.271173 | 0.807881 | -0.000284 | -0.000222 | -0.000248 | 1.000000 | 0.537500 | 0.366667 | -0.000952 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p18__tthr=0p35__as=0p2__ts=0p55__cap=0p024 | gate_threshold_grid | 0.136608 | 0.271173 | 0.807881 | -0.000284 | -0.000222 | -0.000248 | 1.000000 | 0.537500 | 0.366667 | -0.000952 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p12__tthr=0p15__as=0p2__ts=0p75__cap=0p024 | gate_threshold_grid | 0.136578 | 0.271139 | 0.806300 | -0.000315 | -0.000256 | -0.001830 | 0.975000 | 0.529167 | 0.387500 | -0.000931 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p24__tthr=0p25__as=0p2__ts=0p75__cap=0p024 | gate_threshold_grid | 0.136639 | 0.271139 | 0.806608 | -0.000254 | -0.000256 | -0.001522 | 0.987500 | 0.550000 | 0.337500 | -0.000924 |
| PP-OPT19 | ppopt19_segment_tuning__profile=balanced_segments__artist=cat_artist_mean__as=0p35__ts=0p75 | segment_specific_gate_tuning | 0.136938 | 0.271150 | 0.806299 | 0.000045 | -0.000245 | -0.001831 | 0.995833 | 0.541667 | 0.320833 | -0.000924 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p12__tthr=0p15__as=0p2__ts=0p75__cap=0p02 | gate_threshold_grid | 0.136578 | 0.271169 | 0.806599 | -0.000315 | -0.000226 | -0.001531 | 0.975000 | 0.529167 | 0.387500 | -0.000909 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p18__tthr=0p15__as=0p2__ts=0p55__cap=0p024 | gate_threshold_grid | 0.136608 | 0.271158 | 0.806320 | -0.000284 | -0.000237 | -0.001810 | 0.987500 | 0.525000 | 0.358333 | -0.000902 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p24__tthr=0p25__as=0p2__ts=0p75__cap=0p02 | gate_threshold_grid | 0.136639 | 0.271158 | 0.806608 | -0.000254 | -0.000237 | -0.001522 | 0.987500 | 0.550000 | 0.337500 | -0.000899 |
| PP-OPT19 | ppopt19_segment_tuning__profile=balanced_segments__artist=cat_artist_mean__as=0p35__ts=0p55 | segment_specific_gate_tuning | 0.136938 | 0.271162 | 0.806536 | 0.000045 | -0.000233 | -0.001594 | 1.000000 | 0.537500 | 0.312500 | -0.000898 |
| PP-OPT19 | ppopt19_segment_tuning__profile=low_support_tail__artist=cat_artist_mean__as=0p25__ts=0p55 | segment_specific_gate_tuning | 0.136835 | 0.271182 | 0.806472 | -0.000058 | -0.000213 | -0.001658 | 1.000000 | 0.554167 | 0.316667 | -0.000883 |
| PP-OPT20 | ppopt20_protocol_selected__source=ppopt19_segment_tuning__profile_low_support_tail__artist_cat_artist_mean__as_0p25__ts_0p55 | selection_protocol | 0.136835 | 0.271182 | 0.806472 | -0.000058 | -0.000213 | -0.001658 | 1.000000 | 0.554167 | 0.316667 | -0.000883 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p18__tthr=0p15__as=0p2__ts=0p55__cap=0p02 | gate_threshold_grid | 0.136608 | 0.271174 | 0.806619 | -0.000284 | -0.000221 | -0.001511 | 0.987500 | 0.525000 | 0.358333 | -0.000879 |
| PP-OPT19 | ppopt19_segment_tuning__profile=balanced_segments__artist=cat_artist_mean__as=0p25__ts=0p55 | segment_specific_gate_tuning | 0.136876 | 0.271215 | 0.806500 | -0.000017 | -0.000180 | -0.001630 | 0.995833 | 0.545833 | 0.312500 | -0.000872 |
| PP-OPT19 | ppopt19_segment_tuning__profile=price_tail_high__artist=cat_artist_mean__as=0p25__ts=0p55 | segment_specific_gate_tuning | 0.136927 | 0.271115 | 0.806488 | 0.000035 | -0.000280 | -0.001642 | 0.987500 | 0.579167 | 0.333333 | -0.000868 |
| PP-OPT19 | ppopt19_segment_tuning__profile=low_support_tail__artist=cat_artist_mean__as=0p25__ts=0p75 | segment_specific_gate_tuning | 0.136835 | 0.271155 | 0.806334 | -0.000058 | -0.000240 | -0.001796 | 0.987500 | 0.558333 | 0.304167 | -0.000867 |
| PP-OPT14 | ppopt14_gate_grid__artist=artist_stable__sthr=0p24__tthr=0p35__as=0p2__ts=0p75__cap=0p024 | gate_threshold_grid | 0.136639 | 0.271163 | 0.807721 | -0.000254 | -0.000232 | -0.000409 | 0.995833 | 0.541667 | 0.329167 | -0.000867 |

## 해석
PP-OPT14~20은 PP-OPT9 구조를 더 촘촘히 조정한 실험이다. 결과적으로 개선 여지는 gate threshold와 constrained ensemble 쪽에서 가장 크게 나타났다.
선택 후보는 반복 검증 개선율을 우선하는 selection protocol로 고른 후보이며, fixed test 성능만 가장 좋은 후보와 다를 수 있다.

## 실행 설정
```json
{
  "experiment_id": "PP-OPT14-20",
  "experiment_slug": "PP-OPT14_20_warm_gate_refinement_experiments",
  "created_at": "2026-06-09T11:22:46",
  "seed": 20260609,
  "base_candidate": "hcoef_stable",
  "incumbent_candidate": "incumbent_operational_pp_opt7",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 823,
  "prediction_rows": 926698,
  "items": [
    {
      "item_id": "PP-OPT14",
      "priority": "1",
      "title": "PP-OPT9 gate threshold 정밀 탐색",
      "description": "안전구간 gate, tail-risk gate, 보정 강도, cap을 촘촘히 탐색한다."
    },
    {
      "item_id": "PP-OPT15",
      "priority": "2",
      "title": "PP-OPT12 MAPE 신호의 안정 흡수",
      "description": "PP-OPT12의 평균오차 개선 신호를 PP-OPT9 구조 안에서 약하게 사용한다."
    },
    {
      "item_id": "PP-OPT16",
      "priority": "3",
      "title": "tail-risk label 재정의",
      "description": "p95, p90, p85, soft risk label로 큰 오차 위험 gate를 다시 학습한다."
    },
    {
      "item_id": "PP-OPT17",
      "priority": "4",
      "title": "MdAPE 악화 방지 guard",
      "description": "중앙 오차를 악화시킬 가능성이 있는 row에서 보정 강도를 줄인다."
    },
    {
      "item_id": "PP-OPT18",
      "priority": "5",
      "title": "제약 조건 기반 보정값 앙상블",
      "description": "비음수 가중치와 log cap을 둔 평균오차/tail 보정값 가중합을 탐색한다."
    },
    {
      "item_id": "PP-OPT19",
      "priority": "6",
      "title": "구간별 PP-OPT9 분리 튜닝",
      "description": "가격대, 유사작품 수, 퀀타일 폭, 신뢰도 구간별 보정 강도를 다르게 적용한다."
    },
    {
      "item_id": "PP-OPT20",
      "priority": "7",
      "title": "최종 후보 selection protocol",
      "description": "반복 검증 안정성과 fixed test 확인을 함께 쓰는 최종 후보 선택 기준을 적용한다."
    }
  ],
  "pp_opt8_components": {
    "artist_mape": "existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=1p0__totalcap=0p04",
    "artist_stable": "existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p15__artist=am_h_birth_gen_total_works_gn_a01_c03_s075__cw=0p8__aw=0p75__totalcap=0p025",
    "cat_price_band": "catboost_price_band__cap_strength",
    "qwidth_mild": "qwidth_strength__continuous_mild",
    "qwidth_strict": "qwidth_strength__continuous_strict",
    "xgb_tail": "gap_routing__xgb_tail_else_incumbent__existing_opt5__xgb_xgboost_low_only_diagnostic_cap0p05__rout",
    "tail_guard": "tail_guard__logistic",
    "lightgbm_tail_guard": "lightgbm_tail_guard__classifier",
    "cat_lgb_equal": "correction_ensemble__cat_lgb_equal"
  },
  "pp_opt9_components": {
    "pp9_best_operational": "ppopt9_hybrid__artist=cat_price_band__tail=xgb_tail__as=0p3__ts=0p75",
    "pp9_best_mape": "ppopt9_hybrid__artist=artist_mape__tail=xgb_tail__as=0p6__ts=0p55",
    "pp11_best_operational": "ppopt11_tail_router__src=xgb_tail__gate=lgbm__s=0p75",
    "pp12_best_mape": "ppopt12_multiobjective_grid__aw=0p45__cw=0p35__tw=0p3__cap=0p022",
    "pp13_best_p95": "ppopt13_artwork_shrinkage__group=medium_price__prior=8p0__s=0p7__cap=0p018"
  },
  "label_info": {
    "incumbent_validation_p90_ape": 0.4636774710873784,
    "incumbent_validation_p95_ape": 0.6365947866362616,
    "artist_safety_positive_rate": 0.35452793834296725,
    "tail_risk_positive_rate": 0.1001926782273603,
    "median_guard_threshold": 0.14292885078886003,
    "median_guard_positive_rate": 0.5337186897880539
  },
  "tail_thresholds": {
    "p95": 0.6365947866362616,
    "p90": 0.4636774710873784,
    "p85": 0.38339160296436176
  },
  "selection_decision": {
    "selected_source_candidate": "ppopt19_segment_tuning__profile=low_support_tail__artist=cat_artist_mean__as=0p25__ts=0p55",
    "protocol_candidate": "ppopt20_protocol_selected__source=ppopt19_segment_tuning__profile_low_support_tail__artist_cat_artist_mean__as_0p25__ts_0p55",
    "selected_source_item_id": "PP-OPT19",
    "selected_source_family": "segment_specific_gate_tuning",
    "selection_reason": "operational pass candidates sorted by repeated validation improve rates, p95 not-worse rate, all3 rate, recommendation score, then fixed test MAPE",
    "test_MdAPE": 0.13683480909611148,
    "test_MAPE": 0.27118155989915116,
    "test_p95_APE": 0.8064724784402645,
    "test_delta_vs_incumbent_MdAPE": -5.775680250472148e-05,
    "test_delta_vs_incumbent_MAPE": -0.00021332811291530085,
    "test_delta_vs_incumbent_p95_APE": -0.0016575042732042133,
    "incumbent_MAPE_improve_rate": 1.0,
    "incumbent_p95_not_worse_rate": 0.5541666666666667,
    "incumbent_all3_rate": 0.31666666666666665,
    "recommendation_score_vs_incumbent": -0.0008832651179173228
  },
  "sources": {
    "pp_opt9_predictions": "experiments/track6/PP-OPT9_13_warm_followup_improvement_experiments/outputs/candidate_predictions.csv",
    "pp_opt9_aggregate": "experiments/track6/PP-OPT9_13_warm_followup_improvement_experiments/outputs/aggregate_candidate_stability.csv",
    "pp_opt8_helper": "scripts/track6/run_pp_opt8_warm_extended_correction_experiments.py",
    "pp_opt9_helper": "scripts/track6/run_pp_opt9_13_warm_followup_improvement_experiments.py"
  }
}
```