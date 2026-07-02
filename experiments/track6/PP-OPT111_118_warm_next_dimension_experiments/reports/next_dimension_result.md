# PP-OPT111~118 Warm next-dimension 실험 결과

- 작성일: 2026-06-09 14:50
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 목적: 후보 라우터, 기준가 재생성, 방향 분류 보정, 신뢰도 가중 잔차, 유사작품 proxy 스택킹 검증
- 결론: 운영 후보 candidate_ppopt116_hybrid_stack_router__target_huber_stack_weighted__thr_0p12__s_0p75 fixed test MAPE 0.270139, p95 0.807490. PP64 대비 MAPE -0.000425, p95 -0.000009.
- 해석: 기준가 재생성/스택킹은 기존 보정과 다른 차원의 접근이다. 고정 test에서 더 낮은 후보가 나오더라도 validation 반복 안정성이 PP81/PP95 또는 PP110보다 낮으면 운영 교체 근거는 약하다.

## 주요 후보 test 비교
| candidate | family | item_id | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt118_operational_next_dimension_challenger__source=ppopt116_hybrid_stack_router__target_huber_stack_weighted__thr_0p12__s_0p75 | next_dimension_operational_selection | PP-OPT118 | 0.137878 | 0.270139 | 0.807490 | 0.397618 | -0.001256 | -0.000640 |
| reference_pp110_operational | reference_prior | REFERENCE | 0.137878 | 0.270555 | 0.807490 | 0.397983 | -0.000840 | -0.000640 |
| reference_pp81_best | reference_prior | REFERENCE | 0.137878 | 0.270559 | 0.807490 | 0.397989 | -0.000836 | -0.000640 |
| reference_pp95_operational | reference_prior | REFERENCE | 0.137878 | 0.270559 | 0.807490 | 0.397989 | -0.000836 | -0.000640 |
| reference_pp64_current_best | reference_prior | REFERENCE | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |
| ppopt118_p95_next_dimension_challenger__source=ppopt111_meta_router__set_tail_mix__thr_0p22__s_1p0 | next_dimension_p95_selection | PP-OPT118 | 0.137798 | 0.270593 | 0.807317 | 0.397989 | -0.000802 | -0.000813 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | p95_test_MAPE | p95_test_p95_APE | operational_pass_vs_incumbent | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | hybrid model stack router | 64 | 0.270210 | 0.807490 | 0.269974 | 0.807490 | True | hybrid_model_stack_router | ppopt116_hybrid_stack_router__target=huber_stack_weighted__thr=0p06__s=0p55 |
| 8 | final next-dimension decision | 2 | 0.270139 | 0.807490 | 0.270593 | 0.807317 | True | next_dimension_operational_selection | ppopt118_operational_next_dimension_challenger__source=ppopt116_hybrid_stack_router__target_huber_stack_weighted__thr_0p12__s_0p75 |
| 1 | candidate meta-router | 24 | 0.270559 | 0.807490 | 0.270593 | 0.807317 | True | candidate_meta_router | ppopt111_meta_router__set=operational__thr=0p44__s=0p55 |
| 3 | over/under direction correction | 96 | 0.270551 | 0.807644 | 0.270533 | 0.807532 | False | over_under_direction_correction | ppopt113_direction__anchor=pp110_op__thr=0p04__cap=0p011__s=0p35 |
| 4 | confidence weighted residual model | 60 | 0.270729 | 0.808259 | 0.270577 | 0.807972 | False | confidence_weighted_residual_model | ppopt114_conf_residual__src=lgbm_pp110_plain__cap=0p004__s=0p2 |
| 5 | comparable proxy basis stack | 96 | 0.270639 | 0.808500 | 0.271368 | 0.806707 | False | comparable_proxy_basis_stack | ppopt115_proxy_stack__model=huber_plain__anchor=pp110_op__cap=0p01__s=0p85 |
| 2 | basis regeneration regressors | 120 | 0.270786 | 0.807012 | 0.271243 | 0.806384 | False | basis_regeneration_regressor | ppopt112_basis_regen__model=xgb_weighted__anchor=pp110__cap=0p01__s=0p65 |

## 탐색 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt116_hybrid_stack_router__target=huber_stack_weighted__thr=0p06__s=0p55 | PP-OPT116 | hybrid_model_stack_router | 0.270210 | 0.807490 | -0.001185 | -0.000640 | 0.995833 | 0.587500 | -0.001690 |
| ppopt116_hybrid_stack_router__target=huber_stack_weighted__thr=0p12__s=0p75 | PP-OPT116 | hybrid_model_stack_router | 0.270139 | 0.807490 | -0.001256 | -0.000640 | 0.987500 | 0.600000 | -0.001654 |
| ppopt118_operational_next_dimension_challenger__source=ppopt116_hybrid_stack_router__target_huber_stack_weighted__thr_0p12__s_0p75 | PP-OPT118 | next_dimension_operational_selection | 0.270139 | 0.807490 | -0.001256 | -0.000640 | 0.987500 | 0.600000 | -0.001654 |
| ppopt116_hybrid_stack_router__target=huber_stack_weighted__thr=0p12__s=0p55 | PP-OPT116 | hybrid_model_stack_router | 0.270250 | 0.807490 | -0.001144 | -0.000640 | 1.000000 | 0.587500 | -0.001637 |
| ppopt116_hybrid_stack_router__target=huber_stack_weighted__thr=0p06__s=0p75 | PP-OPT116 | hybrid_model_stack_router | 0.270084 | 0.807490 | -0.001311 | -0.000640 | 0.975000 | 0.604167 | -0.001617 |
| ppopt116_hybrid_stack_router__target=huber_stack_weighted__thr=0p2__s=0p75 | PP-OPT116 | hybrid_model_stack_router | 0.270282 | 0.807490 | -0.001113 | -0.000640 | 0.987500 | 0.583333 | -0.001523 |
| ppopt116_hybrid_stack_router__target=huber_stack_weighted__thr=0p12__s=0p35 | PP-OPT116 | hybrid_model_stack_router | 0.270362 | 0.807490 | -0.001033 | -0.000640 | 1.000000 | 0.566667 | -0.001518 |
| ppopt116_hybrid_stack_router__target=huber_stack_weighted__thr=0p06__s=0p35 | PP-OPT116 | hybrid_model_stack_router | 0.270336 | 0.807490 | -0.001059 | -0.000640 | 1.000000 | 0.562500 | -0.001508 |
| ppopt113_direction__anchor=pp110_op__thr=0p04__cap=0p011__s=0p35 | PP-OPT113 | over_under_direction_correction | 0.270551 | 0.807644 | -0.000844 | -0.000486 | 1.000000 | 0.583333 | -0.001474 |
| ppopt116_hybrid_stack_router__target=huber_stack_weighted__thr=0p02__s=0p55 | PP-OPT116 | hybrid_model_stack_router | 0.270129 | 0.807490 | -0.001266 | -0.000640 | 0.983333 | 0.587500 | -0.001459 |
| ppopt116_hybrid_stack_router__target=huber_stack_weighted__thr=0p12__s=0p2 | PP-OPT116 | hybrid_model_stack_router | 0.270446 | 0.807490 | -0.000949 | -0.000640 | 1.000000 | 0.550000 | -0.001455 |
| ppopt116_hybrid_stack_router__target=huber_stack_weighted__thr=0p02__s=0p35 | PP-OPT116 | hybrid_model_stack_router | 0.270284 | 0.807490 | -0.001111 | -0.000640 | 0.995833 | 0.550000 | -0.001445 |
| ppopt116_hybrid_stack_router__target=huber_stack_weighted__thr=0p2__s=0p55 | PP-OPT116 | hybrid_model_stack_router | 0.270355 | 0.807490 | -0.001040 | -0.000640 | 0.995833 | 0.550000 | -0.001442 |
| ppopt113_direction__anchor=pp81__thr=0p22__cap=0p011__s=0p35 | PP-OPT113 | over_under_direction_correction | 0.270525 | 0.807555 | -0.000870 | -0.000575 | 1.000000 | 0.500000 | -0.001434 |
| ppopt113_direction__anchor=pp81__thr=0p04__cap=0p011__s=0p35 | PP-OPT113 | over_under_direction_correction | 0.270554 | 0.807644 | -0.000840 | -0.000486 | 1.000000 | 0.558333 | -0.001433 |
| ppopt113_direction__anchor=pp110_op__thr=0p22__cap=0p011__s=0p35 | PP-OPT113 | over_under_direction_correction | 0.270521 | 0.807555 | -0.000874 | -0.000575 | 1.000000 | 0.500000 | -0.001433 |
| ppopt116_hybrid_stack_router__target=huber_stack_weighted__thr=0p06__s=0p2 | PP-OPT116 | hybrid_model_stack_router | 0.270431 | 0.807490 | -0.000964 | -0.000640 | 1.000000 | 0.550000 | -0.001432 |
| ppopt113_direction__anchor=pp81__thr=0p22__cap=0p007__s=0p55 | PP-OPT113 | over_under_direction_correction | 0.270524 | 0.807557 | -0.000871 | -0.000573 | 1.000000 | 0.500000 | -0.001429 |
| ppopt113_direction__anchor=pp110_op__thr=0p22__cap=0p007__s=0p55 | PP-OPT113 | over_under_direction_correction | 0.270521 | 0.807557 | -0.000874 | -0.000573 | 1.000000 | 0.500000 | -0.001428 |
| ppopt113_direction__anchor=pp110_op__thr=0p04__cap=0p007__s=0p55 | PP-OPT113 | over_under_direction_correction | 0.270555 | 0.807651 | -0.000840 | -0.000479 | 1.000000 | 0.562500 | -0.001425 |
| ppopt116_hybrid_stack_router__target=huber_stack_weighted__thr=0p2__s=0p35 | PP-OPT116 | hybrid_model_stack_router | 0.270429 | 0.807490 | -0.000966 | -0.000640 | 1.000000 | 0.533333 | -0.001419 |
| ppopt113_direction__anchor=pp110_op__thr=0p14__cap=0p011__s=0p55 | PP-OPT113 | over_under_direction_correction | 0.270528 | 0.807655 | -0.000867 | -0.000475 | 1.000000 | 0.562500 | -0.001417 |
| ppopt113_direction__anchor=pp81__thr=0p04__cap=0p007__s=0p55 | PP-OPT113 | over_under_direction_correction | 0.270558 | 0.807651 | -0.000836 | -0.000479 | 1.000000 | 0.558333 | -0.001417 |
| ppopt113_direction__anchor=pp110_op__thr=0p22__cap=0p007__s=0p35 | PP-OPT113 | over_under_direction_correction | 0.270533 | 0.807532 | -0.000862 | -0.000598 | 1.000000 | 0.512500 | -0.001412 |
| ppopt113_direction__anchor=pp81__thr=0p22__cap=0p007__s=0p75 | PP-OPT113 | over_under_direction_correction | 0.270515 | 0.807581 | -0.000880 | -0.000549 | 1.000000 | 0.487500 | -0.001411 |
| ppopt113_direction__anchor=pp110_op__thr=0p22__cap=0p007__s=0p75 | PP-OPT113 | over_under_direction_correction | 0.270511 | 0.807581 | -0.000883 | -0.000549 | 1.000000 | 0.487500 | -0.001410 |
| ppopt113_direction__anchor=pp81__thr=0p14__cap=0p011__s=0p55 | PP-OPT113 | over_under_direction_correction | 0.270532 | 0.807655 | -0.000863 | -0.000475 | 1.000000 | 0.562500 | -0.001410 |
| ppopt113_direction__anchor=pp110_op__thr=0p08__cap=0p007__s=0p75 | PP-OPT113 | over_under_direction_correction | 0.270545 | 0.807681 | -0.000850 | -0.000449 | 1.000000 | 0.558333 | -0.001408 |
| ppopt113_direction__anchor=pp81__thr=0p22__cap=0p016__s=0p35 | PP-OPT113 | over_under_direction_correction | 0.270513 | 0.807585 | -0.000881 | -0.000545 | 1.000000 | 0.487500 | -0.001402 |
| ppopt113_direction__anchor=pp110_op__thr=0p22__cap=0p016__s=0p35 | PP-OPT113 | over_under_direction_correction | 0.270510 | 0.807585 | -0.000885 | -0.000545 | 1.000000 | 0.487500 | -0.001401 |
| ppopt113_direction__anchor=pp81__thr=0p08__cap=0p007__s=0p75 | PP-OPT113 | over_under_direction_correction | 0.270548 | 0.807681 | -0.000846 | -0.000449 | 1.000000 | 0.558333 | -0.001401 |
| ppopt116_hybrid_stack_router__target=huber_stack_weighted__thr=0p2__s=0p2 | PP-OPT116 | hybrid_model_stack_router | 0.270485 | 0.807490 | -0.000910 | -0.000640 | 1.000000 | 0.525000 | -0.001391 |
| ppopt113_direction__anchor=pp110_op__thr=0p04__cap=0p016__s=0p35 | PP-OPT113 | over_under_direction_correction | 0.270555 | 0.807714 | -0.000840 | -0.000416 | 1.000000 | 0.566667 | -0.001388 |
| ppopt113_direction__anchor=pp110_op__thr=0p04__cap=0p007__s=0p75 | PP-OPT113 | over_under_direction_correction | 0.270559 | 0.807709 | -0.000836 | -0.000421 | 1.000000 | 0.562500 | -0.001386 |
| ppopt113_direction__anchor=pp110_op__thr=0p14__cap=0p007__s=0p35 | PP-OPT113 | over_under_direction_correction | 0.270542 | 0.807559 | -0.000853 | -0.000571 | 1.000000 | 0.512500 | -0.001382 |
| ppopt113_direction__anchor=pp110_op__thr=0p08__cap=0p011__s=0p55 | PP-OPT113 | over_under_direction_correction | 0.270543 | 0.807701 | -0.000852 | -0.000429 | 1.000000 | 0.562500 | -0.001382 |
| ppopt113_direction__anchor=pp81__thr=0p22__cap=0p011__s=0p55 | PP-OPT113 | over_under_direction_correction | 0.270512 | 0.807593 | -0.000883 | -0.000537 | 1.000000 | 0.487500 | -0.001382 |
| ppopt113_direction__anchor=pp110_op__thr=0p22__cap=0p011__s=0p55 | PP-OPT113 | over_under_direction_correction | 0.270508 | 0.807593 | -0.000886 | -0.000537 | 1.000000 | 0.487500 | -0.001381 |
| ppopt113_direction__anchor=pp81__thr=0p04__cap=0p007__s=0p75 | PP-OPT113 | over_under_direction_correction | 0.270562 | 0.807709 | -0.000832 | -0.000421 | 1.000000 | 0.558333 | -0.001379 |
| ppopt113_direction__anchor=pp81__thr=0p08__cap=0p016__s=0p35 | PP-OPT113 | over_under_direction_correction | 0.270544 | 0.807685 | -0.000851 | -0.000445 | 1.000000 | 0.558333 | -0.001379 |
| ppopt113_direction__anchor=pp110_op__thr=0p08__cap=0p016__s=0p35 | PP-OPT113 | over_under_direction_correction | 0.270541 | 0.807685 | -0.000854 | -0.000445 | 1.000000 | 0.558333 | -0.001378 |
| ppopt111_meta_router__set=operational__thr=0p44__s=0p55 | PP-OPT111 | candidate_meta_router | 0.270559 | 0.807490 | -0.000836 | -0.000640 | 1.000000 | 0.508333 | -0.001376 |
| ppopt111_meta_router__set=operational__thr=0p44__s=0p75 | PP-OPT111 | candidate_meta_router | 0.270559 | 0.807490 | -0.000835 | -0.000640 | 1.000000 | 0.508333 | -0.001376 |
| ppopt111_meta_router__set=operational__thr=0p44__s=1p0 | PP-OPT111 | candidate_meta_router | 0.270560 | 0.807490 | -0.000835 | -0.000640 | 1.000000 | 0.508333 | -0.001376 |
| ppopt111_meta_router__set=operational__thr=0p32__s=0p55 | PP-OPT111 | candidate_meta_router | 0.270559 | 0.807490 | -0.000836 | -0.000640 | 1.000000 | 0.508333 | -0.001376 |
| ppopt111_meta_router__set=operational__thr=0p32__s=0p75 | PP-OPT111 | candidate_meta_router | 0.270559 | 0.807490 | -0.000836 | -0.000640 | 1.000000 | 0.508333 | -0.001376 |
| ppopt111_meta_router__set=operational__thr=0p22__s=0p55 | PP-OPT111 | candidate_meta_router | 0.270559 | 0.807490 | -0.000836 | -0.000640 | 1.000000 | 0.508333 | -0.001376 |
| ppopt111_meta_router__set=operational__thr=0p32__s=1p0 | PP-OPT111 | candidate_meta_router | 0.270559 | 0.807490 | -0.000835 | -0.000640 | 1.000000 | 0.508333 | -0.001375 |
| ppopt111_meta_router__set=operational__thr=0p22__s=0p75 | PP-OPT111 | candidate_meta_router | 0.270559 | 0.807490 | -0.000836 | -0.000640 | 1.000000 | 0.508333 | -0.001375 |
| ppopt111_meta_router__set=operational__thr=0p22__s=1p0 | PP-OPT111 | candidate_meta_router | 0.270559 | 0.807490 | -0.000836 | -0.000640 | 1.000000 | 0.508333 | -0.001375 |
| ppopt111_meta_router__set=tail_mix__thr=0p22__s=0p35 | PP-OPT111 | candidate_meta_router | 0.270570 | 0.807430 | -0.000824 | -0.000700 | 1.000000 | 0.508333 | -0.001375 |
| ppopt111_meta_router__set=tail_mix__thr=0p22__s=0p55 | PP-OPT111 | candidate_meta_router | 0.270577 | 0.807395 | -0.000818 | -0.000735 | 1.000000 | 0.508333 | -0.001374 |
| ppopt111_meta_router__set=tail_mix__thr=0p32__s=0p35 | PP-OPT111 | candidate_meta_router | 0.270568 | 0.807436 | -0.000827 | -0.000694 | 1.000000 | 0.508333 | -0.001374 |
| ppopt111_meta_router__set=tail_mix__thr=0p22__s=0p75 | PP-OPT111 | candidate_meta_router | 0.270584 | 0.807361 | -0.000811 | -0.000769 | 1.000000 | 0.508333 | -0.001374 |
| ppopt111_meta_router__set=tail_mix__thr=0p44__s=0p35 | PP-OPT111 | candidate_meta_router | 0.270564 | 0.807452 | -0.000830 | -0.000678 | 1.000000 | 0.508333 | -0.001373 |
| ppopt113_direction__anchor=pp110_op__thr=0p04__cap=0p011__s=0p55 | PP-OPT113 | over_under_direction_correction | 0.270558 | 0.807732 | -0.000837 | -0.000398 | 1.000000 | 0.558333 | -0.001373 |
| ppopt111_meta_router__set=tail_mix__thr=0p22__s=1p0 | PP-OPT111 | candidate_meta_router | 0.270593 | 0.807317 | -0.000802 | -0.000813 | 1.000000 | 0.508333 | -0.001373 |
| ppopt118_p95_next_dimension_challenger__source=ppopt111_meta_router__set_tail_mix__thr_0p22__s_1p0 | PP-OPT118 | next_dimension_p95_selection | 0.270593 | 0.807317 | -0.000802 | -0.000813 | 1.000000 | 0.508333 | -0.001373 |
| ppopt111_meta_router__set=tail_mix__thr=0p32__s=0p55 | PP-OPT111 | candidate_meta_router | 0.270573 | 0.807406 | -0.000822 | -0.000724 | 1.000000 | 0.508333 | -0.001373 |
| ppopt113_direction__anchor=pp81__thr=0p04__cap=0p016__s=0p35 | PP-OPT113 | over_under_direction_correction | 0.270558 | 0.807714 | -0.000837 | -0.000416 | 1.000000 | 0.558333 | -0.001373 |

## p95 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt112_basis_regen__model=xgb_weighted__anchor=pp110__cap=0p018__s=0p25 | PP-OPT112 | basis_regeneration_regressor | 0.271243 | 0.806384 | -0.000152 | -0.001746 | 0.816667 | 0.270833 | 0.004461 |
| ppopt112_basis_regen__model=xgb_weighted__anchor=pp81__cap=0p018__s=0p25 | PP-OPT112 | basis_regeneration_regressor | 0.271246 | 0.806384 | -0.000149 | -0.001746 | 0.825000 | 0.270833 | 0.004483 |
| ppopt112_basis_regen__model=xgb_weighted__anchor=pp110__cap=0p018__s=0p45 | PP-OPT112 | basis_regeneration_regressor | 0.271177 | 0.806575 | -0.000218 | -0.001555 | 0.866667 | 0.245833 | 0.004788 |
| ppopt112_basis_regen__model=xgb_weighted__anchor=pp81__cap=0p018__s=0p45 | PP-OPT112 | basis_regeneration_regressor | 0.271180 | 0.806575 | -0.000215 | -0.001555 | 0.870833 | 0.245833 | 0.004792 |
| ppopt112_basis_regen__model=xgb_weighted__anchor=pp110__cap=0p018__s=0p65 | PP-OPT112 | basis_regeneration_regressor | 0.271199 | 0.806625 | -0.000196 | -0.001505 | 0.895833 | 0.200000 | 0.005257 |
| ppopt112_basis_regen__model=xgb_weighted__anchor=pp81__cap=0p018__s=0p65 | PP-OPT112 | basis_regeneration_regressor | 0.271202 | 0.806625 | -0.000193 | -0.001505 | 0.895833 | 0.200000 | 0.005267 |
| ppopt115_proxy_stack__model=ridge_plain__anchor=pp110_op__cap=0p01__s=0p25 | PP-OPT115 | comparable_proxy_basis_stack | 0.271368 | 0.806707 | -0.000027 | -0.001423 | 0.045833 | 0.254167 | 0.003454 |
| ppopt115_proxy_stack__model=ridge_plain__anchor=pp81__cap=0p01__s=0p25 | PP-OPT115 | comparable_proxy_basis_stack | 0.271371 | 0.806707 | -0.000024 | -0.001423 | 0.045833 | 0.254167 | 0.003468 |
| ppopt112_basis_regen__model=xgb_weighted__anchor=pp110__cap=0p01__s=0p25 | PP-OPT112 | basis_regeneration_regressor | 0.270807 | 0.806983 | -0.000588 | -0.001146 | 0.987500 | 0.354167 | 0.001143 |
| ppopt112_basis_regen__model=xgb_weighted__anchor=pp81__cap=0p01__s=0p25 | PP-OPT112 | basis_regeneration_regressor | 0.270810 | 0.806983 | -0.000585 | -0.001146 | 0.987500 | 0.354167 | 0.001158 |
| ppopt112_basis_regen__model=xgb_weighted__anchor=pp110__cap=0p01__s=0p65 | PP-OPT112 | basis_regeneration_regressor | 0.270786 | 0.807012 | -0.000609 | -0.001118 | 0.991667 | 0.345833 | 0.001092 |
| ppopt112_basis_regen__model=xgb_weighted__anchor=pp81__cap=0p01__s=0p65 | PP-OPT112 | basis_regeneration_regressor | 0.270789 | 0.807012 | -0.000606 | -0.001118 | 0.987500 | 0.345833 | 0.001103 |
| ppopt112_basis_regen__model=xgb_weighted__anchor=pp110__cap=0p01__s=0p45 | PP-OPT112 | basis_regeneration_regressor | 0.270804 | 0.807012 | -0.000591 | -0.001118 | 0.987500 | 0.345833 | 0.001325 |
| ppopt112_basis_regen__model=xgb_weighted__anchor=pp81__cap=0p01__s=0p45 | PP-OPT112 | basis_regeneration_regressor | 0.270807 | 0.807012 | -0.000588 | -0.001118 | 0.987500 | 0.345833 | 0.001338 |
| ppopt115_proxy_stack__model=ridge_weighted__anchor=pp110_op__cap=0p01__s=0p25 | PP-OPT115 | comparable_proxy_basis_stack | 0.271330 | 0.807012 | -0.000064 | -0.001118 | 0.154167 | 0.154167 | 0.004069 |
| ppopt115_proxy_stack__model=ridge_weighted__anchor=pp81__cap=0p01__s=0p25 | PP-OPT115 | comparable_proxy_basis_stack | 0.271334 | 0.807012 | -0.000061 | -0.001118 | 0.150000 | 0.154167 | 0.004095 |
| ppopt111_meta_router__set=tail_mix__thr=0p22__s=1p0 | PP-OPT111 | candidate_meta_router | 0.270593 | 0.807317 | -0.000802 | -0.000813 | 1.000000 | 0.508333 | -0.001373 |
| ppopt118_p95_next_dimension_challenger__source=ppopt111_meta_router__set_tail_mix__thr_0p22__s_1p0 | PP-OPT118 | next_dimension_p95_selection | 0.270593 | 0.807317 | -0.000802 | -0.000813 | 1.000000 | 0.508333 | -0.001373 |
| ppopt111_meta_router__set=tail_mix__thr=0p32__s=1p0 | PP-OPT111 | candidate_meta_router | 0.270585 | 0.807336 | -0.000810 | -0.000794 | 1.000000 | 0.508333 | -0.001370 |
| ppopt111_meta_router__set=tail_mix__thr=0p22__s=0p75 | PP-OPT111 | candidate_meta_router | 0.270584 | 0.807361 | -0.000811 | -0.000769 | 1.000000 | 0.508333 | -0.001374 |
| ppopt111_meta_router__set=tail_mix__thr=0p32__s=0p75 | PP-OPT111 | candidate_meta_router | 0.270579 | 0.807375 | -0.000816 | -0.000755 | 1.000000 | 0.508333 | -0.001371 |
| ppopt111_meta_router__set=tail_mix__thr=0p44__s=1p0 | PP-OPT111 | candidate_meta_router | 0.270575 | 0.807382 | -0.000820 | -0.000748 | 1.000000 | 0.508333 | -0.001368 |
| ppopt111_meta_router__set=tail_mix__thr=0p22__s=0p55 | PP-OPT111 | candidate_meta_router | 0.270577 | 0.807395 | -0.000818 | -0.000735 | 1.000000 | 0.508333 | -0.001374 |
| ppopt111_meta_router__set=tail_mix__thr=0p32__s=0p55 | PP-OPT111 | candidate_meta_router | 0.270573 | 0.807406 | -0.000822 | -0.000724 | 1.000000 | 0.508333 | -0.001373 |
| ppopt111_meta_router__set=tail_mix__thr=0p44__s=0p75 | PP-OPT111 | candidate_meta_router | 0.270571 | 0.807409 | -0.000824 | -0.000721 | 1.000000 | 0.508333 | -0.001370 |
| ppopt111_meta_router__set=tail_mix__thr=0p22__s=0p35 | PP-OPT111 | candidate_meta_router | 0.270570 | 0.807430 | -0.000824 | -0.000700 | 1.000000 | 0.508333 | -0.001375 |
| ppopt111_meta_router__set=tail_mix__thr=0p44__s=0p55 | PP-OPT111 | candidate_meta_router | 0.270568 | 0.807431 | -0.000827 | -0.000699 | 1.000000 | 0.508333 | -0.001372 |
| ppopt111_meta_router__set=tail_mix__thr=0p32__s=0p35 | PP-OPT111 | candidate_meta_router | 0.270568 | 0.807436 | -0.000827 | -0.000694 | 1.000000 | 0.508333 | -0.001374 |
| ppopt111_meta_router__set=tail_mix__thr=0p44__s=0p35 | PP-OPT111 | candidate_meta_router | 0.270564 | 0.807452 | -0.000830 | -0.000678 | 1.000000 | 0.508333 | -0.001373 |
| ppopt111_meta_router__set=operational__thr=0p22__s=1p0 | PP-OPT111 | candidate_meta_router | 0.270559 | 0.807490 | -0.000836 | -0.000640 | 1.000000 | 0.508333 | -0.001375 |
| ppopt111_meta_router__set=operational__thr=0p32__s=1p0 | PP-OPT111 | candidate_meta_router | 0.270559 | 0.807490 | -0.000835 | -0.000640 | 1.000000 | 0.508333 | -0.001375 |
| ppopt111_meta_router__set=operational__thr=0p44__s=1p0 | PP-OPT111 | candidate_meta_router | 0.270560 | 0.807490 | -0.000835 | -0.000640 | 1.000000 | 0.508333 | -0.001376 |
| ppopt111_meta_router__set=operational__thr=0p22__s=0p55 | PP-OPT111 | candidate_meta_router | 0.270559 | 0.807490 | -0.000836 | -0.000640 | 1.000000 | 0.508333 | -0.001376 |
| ppopt111_meta_router__set=operational__thr=0p22__s=0p75 | PP-OPT111 | candidate_meta_router | 0.270559 | 0.807490 | -0.000836 | -0.000640 | 1.000000 | 0.508333 | -0.001375 |
| ppopt111_meta_router__set=operational__thr=0p32__s=0p55 | PP-OPT111 | candidate_meta_router | 0.270559 | 0.807490 | -0.000836 | -0.000640 | 1.000000 | 0.508333 | -0.001376 |
| ppopt111_meta_router__set=operational__thr=0p44__s=0p55 | PP-OPT111 | candidate_meta_router | 0.270559 | 0.807490 | -0.000836 | -0.000640 | 1.000000 | 0.508333 | -0.001376 |
| ppopt111_meta_router__set=operational__thr=0p32__s=0p75 | PP-OPT111 | candidate_meta_router | 0.270559 | 0.807490 | -0.000836 | -0.000640 | 1.000000 | 0.508333 | -0.001376 |
| ppopt111_meta_router__set=operational__thr=0p44__s=0p75 | PP-OPT111 | candidate_meta_router | 0.270559 | 0.807490 | -0.000835 | -0.000640 | 1.000000 | 0.508333 | -0.001376 |
| ppopt111_meta_router__set=operational__thr=0p22__s=0p35 | PP-OPT111 | candidate_meta_router | 0.270559 | 0.807490 | -0.000836 | -0.000640 | 1.000000 | 0.508333 | -0.001326 |
| ppopt111_meta_router__set=operational__thr=0p32__s=0p35 | PP-OPT111 | candidate_meta_router | 0.270559 | 0.807490 | -0.000836 | -0.000640 | 1.000000 | 0.508333 | -0.001326 |

## 선택 후보 반복 안정성
| candidate_label | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_vs_pp64_MAPE | fixed_test_delta_vs_pp64_p95_APE | avg_delta_vs_pp64_MAPE | avg_delta_vs_pp64_p95_APE | avg_pp64_MAPE_win_rate | avg_pp64_p95_win_rate | replacement_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| candidate_ppopt113_direction__anchor_pp110_op__thr_0p22__cap_0p007__s_0p35 | 0.270533 | 0.807532 | -0.000031 | 0.000034 | -0.000040 | 0.000074 | 0.958333 | 0.369551 | -0.018315 |
| candidate_ppopt113_direction__anchor_pp110_op__thr_0p22__cap_0p011__s_0p35 | 0.270521 | 0.807555 | -0.000043 | 0.000056 | -0.000058 | 0.000129 | 0.952244 | 0.369551 | -0.018048 |
| candidate_ppopt113_direction__anchor_pp110_op__thr_0p22__cap_0p007__s_0p55 | 0.270521 | 0.807557 | -0.000043 | 0.000058 | -0.000060 | 0.000129 | 0.951923 | 0.368269 | -0.018035 |
| candidate_ppopt113_direction__anchor_pp81__thr_0p22__cap_0p007__s_0p55 | 0.270524 | 0.807557 | -0.000040 | 0.000058 | -0.000059 | 0.000132 | 0.939423 | 0.363462 | -0.017530 |
| candidate_ppopt113_direction__anchor_pp81__thr_0p22__cap_0p011__s_0p35 | 0.270525 | 0.807555 | -0.000039 | 0.000056 | -0.000056 | 0.000131 | 0.938462 | 0.363462 | -0.017492 |
| candidate_ppopt116_hybrid_stack_router__target_huber_stack_weighted__thr_0p12__s_0p75 | 0.270139 | 0.807490 | -0.000425 | -0.000009 | -0.000389 | -0.001654 | 0.909295 | 0.494551 | -0.016797 |
| pp118_operational_next_dimension_challenger | 0.270139 | 0.807490 | -0.000425 | -0.000009 | -0.000389 | -0.001654 | 0.909295 | 0.494551 | -0.016797 |
| candidate_ppopt116_hybrid_stack_router__target_huber_stack_weighted__thr_0p12__s_0p55 | 0.270250 | 0.807490 | -0.000314 | -0.000009 | -0.000288 | -0.001268 | 0.910897 | 0.491987 | -0.016749 |
| candidate_ppopt116_hybrid_stack_router__target_huber_stack_weighted__thr_0p06__s_0p35 | 0.270336 | 0.807490 | -0.000228 | -0.000009 | -0.000217 | -0.000864 | 0.912821 | 0.487500 | -0.016741 |
| candidate_ppopt116_hybrid_stack_router__target_huber_stack_weighted__thr_0p06__s_0p55 | 0.270210 | 0.807490 | -0.000354 | -0.000009 | -0.000332 | -0.001284 | 0.909295 | 0.494872 | -0.016726 |
| candidate_ppopt116_hybrid_stack_router__target_huber_stack_weighted__thr_0p06__s_0p2 | 0.270431 | 0.807490 | -0.000133 | -0.000009 | -0.000126 | -0.000494 | 0.914744 | 0.488141 | -0.016723 |
| candidate_ppopt116_hybrid_stack_router__target_huber_stack_weighted__thr_0p12__s_0p35 | 0.270362 | 0.807490 | -0.000202 | -0.000009 | -0.000185 | -0.000853 | 0.912500 | 0.484615 | -0.016702 |
| candidate_ppopt116_hybrid_stack_router__target_huber_stack_weighted__thr_0p12__s_0p2 | 0.270446 | 0.807490 | -0.000118 | -0.000009 | -0.000108 | -0.000482 | 0.914423 | 0.488782 | -0.016695 |
| candidate_ppopt116_hybrid_stack_router__target_huber_stack_weighted__thr_0p02__s_0p35 | 0.270284 | 0.807490 | -0.000280 | -0.000009 | -0.000251 | -0.000956 | 0.901923 | 0.397115 | -0.016357 |
| candidate_ppopt116_hybrid_stack_router__target_huber_stack_weighted__thr_0p06__s_0p75 | 0.270084 | 0.807490 | -0.000480 | -0.000009 | -0.000425 | -0.001674 | 0.891667 | 0.497756 | -0.016147 |
| pp81_stable_reference | 0.270559 | 0.807490 | -0.000005 | -0.000009 | -0.000004 | -0.000014 | 0.890705 | 0.410256 | -0.015633 |
| pp95_operational_reference | 0.270559 | 0.807490 | -0.000005 | -0.000009 | -0.000004 | -0.000014 | 0.890705 | 0.410256 | -0.015633 |
| candidate_ppopt116_hybrid_stack_router__target_huber_stack_weighted__thr_0p02__s_0p55 | 0.270129 | 0.807490 | -0.000435 | -0.000009 | -0.000365 | -0.001428 | 0.877564 | 0.404487 | -0.015538 |
| candidate_ppopt116_hybrid_stack_router__target_huber_stack_weighted__thr_0p02__s_0p75 | 0.269974 | 0.807490 | -0.000590 | -0.000009 | -0.000467 | -0.001867 | 0.856090 | 0.409936 | -0.014833 |
| candidate_ppopt115_proxy_stack__model_huber_weighted__anchor_pp110_op__cap_0p01__s_0p25 | 0.270041 | 0.808500 | -0.000523 | 0.001001 | -0.000383 | -0.001134 | 0.858654 | 0.481090 | -0.014168 |
| candidate_ppopt116_hybrid_stack_router__target_huber_stack_weighted__thr_0p2__s_0p2 | 0.270485 | 0.807490 | -0.000079 | -0.000009 | -0.000059 | -0.000377 | 0.842628 | 0.451923 | -0.013784 |
| candidate_ppopt116_hybrid_stack_router__target_huber_stack_weighted__thr_0p2__s_0p75 | 0.270282 | 0.807490 | -0.000282 | -0.000009 | -0.000207 | -0.001231 | 0.837500 | 0.481090 | -0.013782 |
| candidate_ppopt116_hybrid_stack_router__target_huber_stack_weighted__thr_0p2__s_0p55 | 0.270355 | 0.807490 | -0.000209 | -0.000009 | -0.000154 | -0.000958 | 0.838782 | 0.478205 | -0.013760 |
| candidate_ppopt116_hybrid_stack_router__target_huber_stack_weighted__thr_0p2__s_0p35 | 0.270429 | 0.807490 | -0.000135 | -0.000009 | -0.000100 | -0.000654 | 0.839103 | 0.472756 | -0.013699 |
| candidate_ppopt115_proxy_stack__model_huber_weighted__anchor_pp81__cap_0p018__s_0p25 | 0.269656 | 0.809251 | -0.000908 | 0.001752 | -0.000601 | -0.002122 | 0.840385 | 0.483333 | -0.013297 |
| candidate_ppopt115_proxy_stack__model_huber_weighted__anchor_pp110_op__cap_0p018__s_0p25 | 0.269653 | 0.809251 | -0.000911 | 0.001752 | -0.000603 | -0.002120 | 0.840064 | 0.483333 | -0.013287 |
| candidate_ppopt113_direction__anchor_pp110_op__thr_0p14__cap_0p016__s_0p75 | 0.270537 | 0.807816 | -0.000027 | 0.000317 | -0.000145 | 0.000746 | 0.829808 | 0.349359 | -0.012736 |
| candidate_ppopt113_direction__anchor_pp81__thr_0p14__cap_0p016__s_0p75 | 0.270540 | 0.807816 | -0.000024 | 0.000317 | -0.000143 | 0.000748 | 0.821154 | 0.349038 | -0.012386 |
| candidate_ppopt113_direction__anchor_pp110_op__thr_0p08__cap_0p011__s_0p75 | 0.270552 | 0.807778 | -0.000012 | 0.000279 | -0.000109 | 0.000565 | 0.811218 | 0.350000 | -0.012068 |
| candidate_ppopt113_direction__anchor_pp110_op__thr_0p08__cap_0p016__s_0p55 | 0.270554 | 0.807797 | -0.000010 | 0.000298 | -0.000114 | 0.000609 | 0.806731 | 0.350321 | -0.011858 |
| pp70_refinement_candidate | 0.270561 | 0.807490 | -0.000003 | -0.000009 | -0.000001 | -0.000001 | 0.786859 | 0.398077 | -0.011477 |
| pp110_operational_reference | 0.270555 | 0.807490 | -0.000009 | -0.000009 | -0.000005 | -0.000016 | 0.782051 | 0.454808 | -0.011291 |
| candidate_ppopt115_proxy_stack__model_huber_weighted__anchor_pp81__cap_0p03__s_0p25 | 0.269350 | 0.809570 | -0.001214 | 0.002071 | -0.000743 | -0.002617 | 0.716346 | 0.482692 | -0.008418 |
| candidate_ppopt115_proxy_stack__model_huber_weighted__anchor_pp110_op__cap_0p03__s_0p25 | 0.269347 | 0.809570 | -0.001217 | 0.002071 | -0.000745 | -0.002617 | 0.715705 | 0.482692 | -0.008396 |
| candidate_ppopt115_proxy_stack__model_huber_plain__anchor_pp81__cap_0p03__s_0p25 | 0.269978 | 0.808898 | -0.000586 | 0.001399 | -0.000408 | -0.001055 | 0.707051 | 0.388462 | -0.007889 |
| candidate_ppopt115_proxy_stack__model_huber_plain__anchor_pp110_op__cap_0p03__s_0p25 | 0.269975 | 0.808898 | -0.000589 | 0.001399 | -0.000410 | -0.001057 | 0.706731 | 0.388462 | -0.007879 |
| candidate_ppopt115_proxy_stack__model_huber_weighted__anchor_pp110_op__cap_0p018__s_0p45 | 0.269868 | 0.809304 | -0.000696 | 0.001805 | -0.000496 | -0.001773 | 0.704487 | 0.470192 | -0.007612 |
| candidate_ppopt115_proxy_stack__model_huber_weighted__anchor_pp81__cap_0p018__s_0p45 | 0.269872 | 0.809304 | -0.000692 | 0.001805 | -0.000493 | -0.001773 | 0.704487 | 0.470192 | -0.007609 |
| candidate_ppopt113_direction__anchor_pp110_op__thr_0p04__cap_0p011__s_0p75 | 0.270572 | 0.807820 | 0.000008 | 0.000321 | -0.000107 | 0.000645 | 0.695513 | 0.341026 | -0.007362 |
| candidate_ppopt113_direction__anchor_pp110_op__thr_0p08__cap_0p016__s_0p75 | 0.270568 | 0.807908 | 0.000003 | 0.000409 | -0.000142 | 0.000889 | 0.699038 | 0.340064 | -0.007361 |
| candidate_ppopt113_direction__anchor_pp81__thr_0p08__cap_0p016__s_0p75 | 0.270571 | 0.807908 | 0.000007 | 0.000409 | -0.000140 | 0.000891 | 0.692308 | 0.339744 | -0.007087 |
| candidate_ppopt115_proxy_stack__model_huber_weighted__anchor_pp110_op__cap_0p018__s_0p65 | 0.269904 | 0.809304 | -0.000660 | 0.001805 | -0.000465 | -0.001566 | 0.685577 | 0.467308 | -0.006819 |
| candidate_ppopt113_direction__anchor_pp81__thr_0p04__cap_0p016__s_0p55 | 0.270579 | 0.807842 | 0.000015 | 0.000343 | -0.000111 | 0.000697 | 0.681410 | 0.339744 | -0.006757 |
| candidate_ppopt115_proxy_stack__model_huber_weighted__anchor_pp81__cap_0p018__s_0p65 | 0.269908 | 0.809304 | -0.000656 | 0.001805 | -0.000462 | -0.001566 | 0.683974 | 0.467308 | -0.006751 |
| candidate_ppopt115_proxy_stack__model_huber_weighted__anchor_pp81__cap_0p03__s_0p45 | 0.269283 | 0.810503 | -0.001281 | 0.003004 | -0.000800 | -0.003247 | 0.683333 | 0.468910 | -0.006512 |
| candidate_ppopt115_proxy_stack__model_huber_weighted__anchor_pp110_op__cap_0p03__s_0p45 | 0.269279 | 0.810503 | -0.001285 | 0.003004 | -0.000802 | -0.003246 | 0.683013 | 0.468910 | -0.006502 |
| candidate_ppopt115_proxy_stack__model_huber_weighted__anchor_pp110_op__cap_0p018__s_0p85 | 0.269895 | 0.809304 | -0.000669 | 0.001805 | -0.000459 | -0.001255 | 0.672436 | 0.469551 | -0.006303 |
| candidate_ppopt115_proxy_stack__model_huber_weighted__anchor_pp81__cap_0p018__s_0p85 | 0.269897 | 0.809304 | -0.000667 | 0.001805 | -0.000456 | -0.001255 | 0.672436 | 0.469551 | -0.006301 |
| pp102_operational_reference | 0.270555 | 0.807490 | -0.000009 | -0.000009 | -0.000004 | -0.000017 | 0.614423 | 0.454808 | -0.004586 |
| candidate_ppopt115_proxy_stack__model_huber_weighted__anchor_pp110_op__cap_0p03__s_0p65 | 0.269589 | 0.810503 | -0.000975 | 0.003004 | -0.000587 | -0.002805 | 0.617949 | 0.436859 | -0.003590 |
| candidate_ppopt115_proxy_stack__model_huber_weighted__anchor_pp81__cap_0p03__s_0p65 | 0.269592 | 0.810503 | -0.000972 | 0.003004 | -0.000584 | -0.002798 | 0.616667 | 0.436859 | -0.003535 |
| candidate_ppopt115_proxy_stack__model_huber_weighted__anchor_pp110_op__cap_0p03__s_0p85 | 0.269766 | 0.810503 | -0.000798 | 0.003004 | -0.000427 | -0.002426 | 0.570513 | 0.439744 | -0.001516 |
| candidate_ppopt115_proxy_stack__model_huber_weighted__anchor_pp81__cap_0p03__s_0p85 | 0.269770 | 0.810503 | -0.000794 | 0.003004 | -0.000422 | -0.002414 | 0.569231 | 0.438782 | -0.001460 |
| candidate_ppopt114_conf_residual__src_lgbm_pp110_plain__cap_0p007__s_0p2 | 0.270709 | 0.808259 | 0.000145 | 0.000760 | -0.000117 | 0.001429 | 0.555128 | 0.351603 | -0.001028 |
| candidate_ppopt114_conf_residual__src_lgbm_pp110_plain__cap_0p011__s_0p2 | 0.270723 | 0.808482 | 0.000158 | 0.000984 | -0.000127 | 0.001614 | 0.558333 | 0.328846 | -0.000922 |
| candidate_ppopt114_conf_residual__src_lgbm_pp110_plain__cap_0p011__s_0p35 | 0.270761 | 0.808600 | 0.000197 | 0.001102 | -0.000146 | 0.001609 | 0.557372 | 0.334615 | -0.000764 |
| candidate_ppopt114_conf_residual__src_lgbm_pp110_plain__cap_0p004__s_0p2 | 0.270729 | 0.808259 | 0.000165 | 0.000760 | -0.000074 | 0.001076 | 0.532372 | 0.369231 | -0.000221 |
| candidate_ppopt114_conf_residual__src_lgbm_pp110_plain__cap_0p007__s_0p35 | 0.270775 | 0.808259 | 0.000211 | 0.000760 | -0.000095 | 0.001563 | 0.531090 | 0.347756 | 0.000046 |
| candidate_ppopt114_conf_residual__src_lgbm_pp110_plain__cap_0p011__s_0p55 | 0.270864 | 0.808600 | 0.000300 | 0.001102 | -0.000114 | 0.001658 | 0.531410 | 0.322115 | 0.000395 |
| candidate_ppopt114_conf_residual__src_lgbm_pp110_plain__cap_0p004__s_0p35 | 0.270787 | 0.808259 | 0.000223 | 0.000760 | -0.000047 | 0.001275 | 0.517308 | 0.364744 | 0.000509 |
| candidate_ppopt114_conf_residual__src_lgbm_pp110_plain__cap_0p007__s_0p55 | 0.270823 | 0.808259 | 0.000259 | 0.000760 | -0.000069 | 0.001698 | 0.519872 | 0.332372 | 0.000590 |
| candidate_ppopt114_conf_residual__src_lgbm_pp110_plain__cap_0p007__s_0p75 | 0.270829 | 0.808259 | 0.000265 | 0.000760 | -0.000069 | 0.001704 | 0.519872 | 0.329808 | 0.000598 |
| candidate_ppopt114_conf_residual__src_lgbm_pp110_plain__cap_0p004__s_0p55 | 0.270822 | 0.808259 | 0.000258 | 0.000760 | -0.000022 | 0.001354 | 0.510897 | 0.351923 | 0.000828 |
| candidate_ppopt114_conf_residual__src_lgbm_pp110_plain__cap_0p016__s_0p35 | 0.270869 | 0.809639 | 0.000305 | 0.002140 | -0.000132 | 0.001824 | 0.540064 | 0.329487 | 0.000839 |
| candidate_ppopt114_conf_residual__src_lgbm_pp110_plain__cap_0p004__s_0p75 | 0.270833 | 0.808259 | 0.000269 | 0.000760 | -0.000015 | 0.001363 | 0.507692 | 0.351603 | 0.000970 |
| pp110_p95_reference | 0.270557 | 0.807482 | -0.000007 | -0.000017 | 0.000002 | 0.000013 | 0.463141 | 0.572115 | 0.001473 |
| candidate_ppopt112_basis_regen__model_xgb_weighted__anchor_pp110__cap_0p01__s_0p65 | 0.270786 | 0.807012 | 0.000222 | -0.000487 | 0.000046 | 0.002861 | 0.462500 | 0.393269 | 0.002746 |
| candidate_ppopt112_basis_regen__model_xgb_weighted__anchor_pp81__cap_0p01__s_0p65 | 0.270789 | 0.807012 | 0.000225 | -0.000487 | 0.000047 | 0.002859 | 0.461218 | 0.391667 | 0.002800 |
| candidate_ppopt112_basis_regen__model_xgb_weighted__anchor_pp81__cap_0p01__s_0p45 | 0.270807 | 0.807012 | 0.000243 | -0.000487 | 0.000081 | 0.002863 | 0.429808 | 0.391346 | 0.004093 |
| candidate_ppopt112_basis_regen__model_xgb_weighted__anchor_pp110__cap_0p01__s_0p45 | 0.270804 | 0.807012 | 0.000240 | -0.000487 | 0.000080 | 0.002864 | 0.429167 | 0.393269 | 0.004115 |
| pp82_operational_reference | 0.270557 | 0.807450 | -0.000007 | -0.000049 | 0.000018 | 0.000050 | 0.362179 | 0.477244 | 0.005532 |
| candidate_ppopt112_basis_regen__model_xgb_weighted__anchor_pp81__cap_0p01__s_0p25 | 0.270810 | 0.806983 | 0.000246 | -0.000515 | 0.000124 | 0.002650 | 0.372756 | 0.393269 | 0.006325 |
| candidate_ppopt112_basis_regen__model_xgb_weighted__anchor_pp110__cap_0p01__s_0p25 | 0.270807 | 0.806983 | 0.000243 | -0.000515 | 0.000123 | 0.002650 | 0.371154 | 0.398397 | 0.006386 |
| candidate_ppopt112_basis_regen__model_xgb_weighted__anchor_pp81__cap_0p018__s_0p65 | 0.271202 | 0.806625 | 0.000638 | -0.000873 | 0.000403 | 0.004921 | 0.198077 | 0.367308 | 0.014639 |
| candidate_ppopt112_basis_regen__model_xgb_weighted__anchor_pp110__cap_0p018__s_0p65 | 0.271199 | 0.806625 | 0.000635 | -0.000873 | 0.000402 | 0.004923 | 0.197436 | 0.367308 | 0.014662 |
| candidate_ppopt112_basis_regen__model_xgb_weighted__anchor_pp81__cap_0p018__s_0p45 | 0.271180 | 0.806575 | 0.000616 | -0.000924 | 0.000439 | 0.004653 | 0.162821 | 0.371474 | 0.015951 |
| candidate_ppopt112_basis_regen__model_xgb_weighted__anchor_pp110__cap_0p018__s_0p45 | 0.271177 | 0.806575 | 0.000613 | -0.000924 | 0.000438 | 0.004654 | 0.162500 | 0.371795 | 0.015961 |
| candidate_ppopt111_meta_router__set_tail_mix__thr_0p32__s_1p0 | 0.270585 | 0.807336 | 0.000021 | -0.000162 | 0.000023 | 0.000033 | 0.091987 | 0.630769 | 0.016365 |
| candidate_ppopt111_meta_router__set_tail_mix__thr_0p22__s_0p75 | 0.270584 | 0.807361 | 0.000020 | -0.000138 | 0.000020 | 0.000039 | 0.082051 | 0.622115 | 0.016762 |
| candidate_ppopt111_meta_router__set_tail_mix__thr_0p22__s_1p0 | 0.270593 | 0.807317 | 0.000029 | -0.000181 | 0.000028 | 0.000057 | 0.075321 | 0.630128 | 0.017050 |

## 선택 후보 시나리오별 안정성
| candidate_label | eval_split | scenario | mean_delta_vs_pp64_MAPE | mean_delta_vs_pp64_p95_APE | pp64_MAPE_win_rate | pp64_p95_win_rate | pp64_all3_win_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pp110_operational_reference | test | artist_group_holdout | -0.000009 | -0.000004 | 0.992308 | 0.326923 | 0.126923 |
| pp110_operational_reference | test | confidence_stratified_rows | -0.000009 | -0.000003 | 0.992308 | 0.442308 | 0.111538 |
| pp110_operational_reference | test | full_split | -0.000009 | -0.000009 | 1.000000 | 1.000000 | 0.000000 |
| pp110_operational_reference | test | price_band_stratified_rows | -0.000009 | -0.000003 | 1.000000 | 0.376923 | 0.115385 |
| pp110_operational_reference | test | risk_focus_bootstrap | -0.000018 | -0.000044 | 0.950000 | 0.223077 | 0.019231 |
| pp110_operational_reference | test | row_bootstrap | -0.000009 | -0.000018 | 0.934615 | 0.350000 | 0.069231 |
| pp110_operational_reference | validation_oof | artist_group_holdout | -0.000000 | -0.000042 | 0.507692 | 0.480769 | 0.057692 |
| pp110_operational_reference | validation_oof | confidence_stratified_rows | -0.000000 | -0.000020 | 0.500000 | 0.384615 | 0.065385 |
| pp110_operational_reference | validation_oof | full_split | -0.000000 | -0.000025 | 1.000000 | 1.000000 | 0.000000 |
| pp110_operational_reference | validation_oof | price_band_stratified_rows | -0.000001 | -0.000034 | 0.542308 | 0.446154 | 0.076923 |
| pp110_operational_reference | validation_oof | risk_focus_bootstrap | -0.000000 | 0.000031 | 0.476923 | 0.046154 | 0.003846 |
| pp110_operational_reference | validation_oof | row_bootstrap | 0.000000 | -0.000027 | 0.488462 | 0.380769 | 0.050000 |
| pp118_operational_next_dimension_challenger | test | artist_group_holdout | -0.000441 | -0.000002 | 1.000000 | 0.319231 | 0.215385 |
| pp118_operational_next_dimension_challenger | test | confidence_stratified_rows | -0.000409 | 0.000007 | 1.000000 | 0.430769 | 0.253846 |
| pp118_operational_next_dimension_challenger | test | full_split | -0.000425 | -0.000009 | 1.000000 | 1.000000 | 0.000000 |
| pp118_operational_next_dimension_challenger | test | price_band_stratified_rows | -0.000412 | -0.000003 | 1.000000 | 0.376923 | 0.246154 |
| pp118_operational_next_dimension_challenger | test | risk_focus_bootstrap | -0.001032 | -0.007846 | 0.996154 | 0.346154 | 0.050000 |
| pp118_operational_next_dimension_challenger | test | row_bootstrap | -0.000437 | -0.000148 | 1.000000 | 0.315385 | 0.142308 |
| pp118_operational_next_dimension_challenger | validation_oof | artist_group_holdout | -0.000262 | -0.003755 | 0.850000 | 0.576923 | 0.338462 |
| pp118_operational_next_dimension_challenger | validation_oof | confidence_stratified_rows | -0.000268 | -0.002559 | 0.876923 | 0.526923 | 0.311538 |
| pp118_operational_next_dimension_challenger | validation_oof | full_split | -0.000268 | -0.000025 | 1.000000 | 1.000000 | 1.000000 |
| pp118_operational_next_dimension_challenger | validation_oof | price_band_stratified_rows | -0.000268 | -0.002086 | 0.873077 | 0.488462 | 0.265385 |
| pp118_operational_next_dimension_challenger | validation_oof | risk_focus_bootstrap | -0.000171 | -0.001151 | 0.576923 | 0.138462 | 0.069231 |
| pp118_operational_next_dimension_challenger | validation_oof | row_bootstrap | -0.000274 | -0.002269 | 0.738462 | 0.415385 | 0.196154 |
| pp118_p95_next_dimension_challenger | test | artist_group_holdout | 0.000029 | 0.000116 | 0.003846 | 0.619231 | 0.003846 |
| pp118_p95_next_dimension_challenger | test | confidence_stratified_rows | 0.000028 | 0.000096 | 0.011538 | 0.611538 | 0.000000 |
| pp118_p95_next_dimension_challenger | test | full_split | 0.000029 | -0.000181 | 0.000000 | 1.000000 | 0.000000 |
| pp118_p95_next_dimension_challenger | test | price_band_stratified_rows | 0.000028 | 0.000134 | 0.015385 | 0.557692 | 0.003846 |
| pp118_p95_next_dimension_challenger | test | risk_focus_bootstrap | 0.000029 | 0.000253 | 0.250000 | 0.480769 | 0.069231 |
| pp118_p95_next_dimension_challenger | test | row_bootstrap | 0.000027 | 0.000151 | 0.103846 | 0.503846 | 0.042308 |
| pp118_p95_next_dimension_challenger | validation_oof | artist_group_holdout | 0.000023 | 0.000045 | 0.061538 | 0.584615 | 0.015385 |
| pp118_p95_next_dimension_challenger | validation_oof | confidence_stratified_rows | 0.000024 | 0.000055 | 0.065385 | 0.630769 | 0.023077 |
| pp118_p95_next_dimension_challenger | validation_oof | full_split | 0.000023 | -0.000025 | 0.000000 | 1.000000 | 0.000000 |
| pp118_p95_next_dimension_challenger | validation_oof | price_band_stratified_rows | 0.000023 | 0.000050 | 0.069231 | 0.665385 | 0.023077 |
| pp118_p95_next_dimension_challenger | validation_oof | risk_focus_bootstrap | 0.000054 | -0.000027 | 0.126923 | 0.369231 | 0.023077 |
| pp118_p95_next_dimension_challenger | validation_oof | row_bootstrap | 0.000023 | 0.000021 | 0.196154 | 0.538462 | 0.046154 |
| pp81_stable_reference | test | artist_group_holdout | -0.000005 | -0.000002 | 0.996154 | 0.319231 | 0.119231 |
| pp81_stable_reference | test | confidence_stratified_rows | -0.000005 | -0.000001 | 0.996154 | 0.434615 | 0.100000 |
| pp81_stable_reference | test | full_split | -0.000005 | -0.000009 | 1.000000 | 1.000000 | 0.000000 |
| pp81_stable_reference | test | price_band_stratified_rows | -0.000005 | -0.000003 | 0.996154 | 0.376923 | 0.115385 |
| pp81_stable_reference | test | risk_focus_bootstrap | -0.000008 | -0.000184 | 0.880769 | 0.338462 | 0.007692 |
| pp81_stable_reference | test | row_bootstrap | -0.000005 | -0.000014 | 0.953846 | 0.330769 | 0.065385 |
| pp81_stable_reference | validation_oof | artist_group_holdout | -0.000002 | 0.000002 | 0.803846 | 0.280769 | 0.092308 |
| pp81_stable_reference | validation_oof | confidence_stratified_rows | -0.000002 | 0.000003 | 0.911538 | 0.288462 | 0.115385 |
| pp81_stable_reference | validation_oof | full_split | -0.000002 | -0.000025 | 1.000000 | 1.000000 | 0.000000 |
| pp81_stable_reference | validation_oof | price_band_stratified_rows | -0.000002 | 0.000000 | 0.880769 | 0.319231 | 0.076923 |
| pp81_stable_reference | validation_oof | risk_focus_bootstrap | -0.000001 | 0.000048 | 0.569231 | 0.000000 | 0.000000 |
| pp81_stable_reference | validation_oof | row_bootstrap | -0.000002 | 0.000012 | 0.700000 | 0.234615 | 0.057692 |
| pp95_operational_reference | test | artist_group_holdout | -0.000005 | -0.000002 | 0.996154 | 0.319231 | 0.119231 |
| pp95_operational_reference | test | confidence_stratified_rows | -0.000005 | -0.000001 | 0.996154 | 0.434615 | 0.100000 |
| pp95_operational_reference | test | full_split | -0.000005 | -0.000009 | 1.000000 | 1.000000 | 0.000000 |
| pp95_operational_reference | test | price_band_stratified_rows | -0.000005 | -0.000003 | 0.996154 | 0.376923 | 0.115385 |
| pp95_operational_reference | test | risk_focus_bootstrap | -0.000008 | -0.000184 | 0.880769 | 0.338462 | 0.007692 |
| pp95_operational_reference | test | row_bootstrap | -0.000005 | -0.000014 | 0.953846 | 0.330769 | 0.065385 |
| pp95_operational_reference | validation_oof | artist_group_holdout | -0.000002 | 0.000002 | 0.803846 | 0.280769 | 0.092308 |
| pp95_operational_reference | validation_oof | confidence_stratified_rows | -0.000002 | 0.000003 | 0.911538 | 0.288462 | 0.115385 |
| pp95_operational_reference | validation_oof | full_split | -0.000002 | -0.000025 | 1.000000 | 1.000000 | 0.000000 |
| pp95_operational_reference | validation_oof | price_band_stratified_rows | -0.000002 | 0.000000 | 0.880769 | 0.319231 | 0.076923 |
| pp95_operational_reference | validation_oof | risk_focus_bootstrap | -0.000001 | 0.000048 | 0.569231 | 0.000000 | 0.000000 |
| pp95_operational_reference | validation_oof | row_bootstrap | -0.000002 | 0.000012 | 0.700000 | 0.234615 | 0.057692 |

## 실행 설정
```json
{
  "experiment_id": "PP-OPT111-118",
  "experiment_slug": "PP-OPT111_118_warm_next_dimension_experiments",
  "created_at": "2026-06-09T14:50:14",
  "seed": 20260609,
  "base_candidate": "hcoef_stable",
  "incumbent_candidate": "incumbent_operational_pp_opt7",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 475,
  "prediction_rows": 534850,
  "selected_references": {
    "pp64": "reference_pp64_current_best",
    "pp70": "reference_pp70_refinement",
    "pp81": "reference_pp81_best",
    "pp82_op": "reference_pp82_operational",
    "pp82_p95": "reference_pp82_p95",
    "pp95_op": "reference_pp95_operational",
    "pp95_p95": "reference_pp95_p95",
    "pp102_op": "reference_pp102_operational",
    "pp110_op": "ppopt110_operational_guarded_pp102_challenger__source=ppopt104_margin_gate__gain_gain_any__hpen_1p05__rpen_0p0__thr_0p14__s_1p0",
    "pp110_p95": "ppopt110_p95_guarded_pp102_challenger__source=ppopt108_tail_hybrid__target_pp82_p95__opthr_0p02__tailthr_0p08__tails_0p4"
  },
  "selection_decision": {
    "operational_label": "candidate_ppopt116_hybrid_stack_router__target_huber_stack_weighted__thr_0p12__s_0p75",
    "operational_candidate": "ppopt116_hybrid_stack_router__target=huber_stack_weighted__thr=0p12__s=0p75",
    "operational_fixed_test_MAPE": 0.2701392253366791,
    "operational_fixed_test_p95_APE": 0.8074900608978479,
    "operational_delta_vs_pp64_MAPE": -0.00042481657898124636,
    "operational_delta_vs_pp64_p95_APE": -8.791408261932254e-06,
    "operational_avg_pp64_MAPE_win_rate": 0.9092948717948718,
    "operational_avg_pp64_p95_win_rate": 0.49455128205128207,
    "operational_replacement_score": -0.016796611450776117,
    "p95_label": "candidate_ppopt111_meta_router__set_tail_mix__thr_0p22__s_1p0",
    "p95_candidate": "ppopt111_meta_router__set=tail_mix__thr=0p22__s=1p0",
    "p95_fixed_test_MAPE": 0.27059264572313707,
    "p95_fixed_test_p95_APE": 0.8073173847115374,
    "p95_delta_vs_pp64_MAPE": 2.860380747671254e-05,
    "p95_delta_vs_pp64_p95_APE": -0.00018146759457249306,
    "p95_avg_pp64_MAPE_win_rate": 0.07532051282051282,
    "p95_avg_pp64_p95_win_rate": 0.6301282051282051,
    "p95_replacement_score": 0.017050017068165464,
    "operational_protocol_candidate": "ppopt118_operational_next_dimension_challenger__source=ppopt116_hybrid_stack_router__target_huber_stack_weighted__thr_0p12__s_0p75",
    "p95_protocol_candidate": "ppopt118_p95_next_dimension_challenger__source=ppopt111_meta_router__set_tail_mix__thr_0p22__s_1p0"
  },
  "items": [
    {
      "item_id": "PP-OPT111",
      "priority": "1",
      "title": "candidate meta-router",
      "description": "PP81/PP95/PP110/p95 후보 중 row별로 이길 후보를 학습해 선택 또는 가중 평균한다."
    },
    {
      "item_id": "PP-OPT112",
      "priority": "2",
      "title": "basis regeneration regressors",
      "description": "LightGBM, CatBoost, XGBoost로 로그가격 기준가를 직접 재생성하고 안정 후보와 제한적으로 결합한다."
    },
    {
      "item_id": "PP-OPT113",
      "priority": "3",
      "title": "over/under direction correction",
      "description": "기준가가 과대/과소인지 먼저 분류하고 방향 확신이 있을 때만 작은 보정을 적용한다."
    },
    {
      "item_id": "PP-OPT114",
      "priority": "4",
      "title": "confidence weighted residual model",
      "description": "고신뢰 row에 더 큰 sample weight를 주어 남은 잔차를 학습한다."
    },
    {
      "item_id": "PP-OPT115",
      "priority": "5",
      "title": "comparable proxy basis stack",
      "description": "SVC/PPV8/L10/PP110 등 기존 유사작품 proxy 예측값을 선형/Huber 스택킹으로 다시 결합한다."
    },
    {
      "item_id": "PP-OPT116",
      "priority": "6",
      "title": "hybrid model stack router",
      "description": "재생성 기준가와 기존 후보 사이의 gap, risk, gain 확률을 보고 제한적으로 채택한다."
    },
    {
      "item_id": "PP-OPT117",
      "priority": "7",
      "title": "stability-selected next candidate",
      "description": "고정 test뿐 아니라 반복 안정성 점수까지 사용해 후보를 선별한다."
    },
    {
      "item_id": "PP-OPT118",
      "priority": "8",
      "title": "final next-dimension decision",
      "description": "선택 후보를 운영형/p95형으로 복제하고 PP81/PP95/PP110과 비교한다."
    }
  ],
  "sources": {
    "pp103_config": "experiments/track6/PP-OPT103_110_warm_pp102_guard_refinement_experiments/artifacts/run_config.json",
    "pp103_predictions": "experiments/track6/PP-OPT103_110_warm_pp102_guard_refinement_experiments/outputs/candidate_predictions.csv",
    "pp96_label_probabilities": "experiments/track6/PP-OPT96_102_warm_tail_label_refinement_experiments/artifacts/tail_label_probability_detail.csv",
    "pp96_helper": "scripts/track6/run_pp_opt96_102_warm_tail_label_refinement_experiments.py",
    "pp103_helper": "scripts/track6/run_pp_opt103_110_warm_pp102_guard_refinement_experiments.py",
    "pp71_validation_helper": "scripts/track6/run_pp_opt71_75_warm_pp70_stability_validation.py"
  }
}
```