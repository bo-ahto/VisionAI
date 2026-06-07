# 원인별 보정/라우팅 후속 실험 결과

## 1. 결론

| route | policy | n | MdAPE | MAPE | p95_APE | RMSE_log | median_ratio | over_3x_n | under_1_3x_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cold | expert_model_structure_guard | 3099 | 0.4174 | 0.9659 | 3.0306 | 0.8577 | 0.9194 | 218 | 285 |
| warm | segment_mape_guard | 607 | 0.1563 | 0.2789 | 0.9253 | 0.4019 | 0.9916 | 6 | 7 |

## 2. 해석

- Warm은 구간별 점가격 보정으로 기준 후보 대비 MdAPE/MAPE/p95가 함께 개선됐으나, 고가/대형 꼬리 구간은 기준값 유지가 더 안전함
- Warm은 추가로 가격 범위와 신뢰도 조정을 병행하면 서비스 표시 안정성을 높일 수 있음
- Cold는 자동 metric 선택보다 모델 구조 기반 고정 정책이 더 안정적이며, MdAPE/MAPE/p95를 함께 낮췄음
- Cold는 대표 가격 후보와 큰 오차 방어 후보를 분리해서 서비스 정책으로 사용할지 판단해야 함
- 모델 구조 기반 고정 정책은 validation 자동 선택과 별도로, Huber/Warm의 안정성 및 Quantile/Cold의 불확실성 정보를 실제 보정에 어떻게 제한적으로 쓸 수 있는지 확인하기 위한 가설형 실험임

## 3. test 정책별 성능

| route | policy | n | MdAPE | MAPE | p95_APE | RMSE_log | median_ratio | over_3x_n | under_1_3x_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cold | expert_model_structure_guard | 3099 | 0.4174 | 0.9659 | 3.0306 | 0.8577 | 0.9194 | 218 | 285 |
| cold | segment_balanced | 3099 | 0.4213 | 0.9979 | 3.0855 | 0.8631 | 0.9293 | 219 | 276 |
| cold | single_best_balanced | 3099 | 0.4238 | 0.9926 | 3.2691 | 0.8599 | 0.9381 | 228 | 276 |
| cold | baseline | 3099 | 0.4247 | 0.9910 | 3.3053 | 0.8575 | 0.9197 | 224 | 271 |
| cold | segment_mape_guard | 3099 | 0.4250 | 0.9957 | 3.3053 | 0.8648 | 0.9228 | 216 | 278 |
| cold | segment_p95_guard | 3099 | 0.4250 | 0.9957 | 3.3053 | 0.8648 | 0.9228 | 216 | 278 |
| cold | segment_objective_aware | 3099 | 0.4250 | 0.9957 | 3.3053 | 0.8648 | 0.9228 | 216 | 278 |
| warm | segment_mape_guard | 607 | 0.1563 | 0.2789 | 0.9253 | 0.4019 | 0.9916 | 6 | 7 |
| warm | segment_p95_guard | 607 | 0.1563 | 0.2789 | 0.9253 | 0.4019 | 0.9916 | 6 | 7 |
| warm | segment_objective_aware | 607 | 0.1563 | 0.2789 | 0.9253 | 0.4019 | 0.9916 | 6 | 7 |
| warm | expert_model_structure_guard | 607 | 0.1563 | 0.2789 | 0.9253 | 0.4019 | 0.9916 | 6 | 7 |
| warm | segment_balanced | 607 | 0.1574 | 0.2785 | 0.9239 | 0.4017 | 0.9896 | 6 | 7 |
| warm | baseline | 607 | 0.1632 | 0.2816 | 0.9311 | 0.4028 | 0.9966 | 6 | 7 |
| warm | single_best_balanced | 607 | 0.1650 | 0.2797 | 0.9239 | 0.4024 | 0.9896 | 6 | 7 |

## 4. test 구간별 성능

| route | policy | operational_segment | n | MdAPE | MAPE | p95_APE | RMSE_log | median_ratio | over_3x_n | under_1_3x_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cold | baseline | cold_extreme_uncertainty | 222 | 0.5092 | 0.6960 | 2.1291 | 0.9234 | 0.7605 | 14 | 30 |
| cold | expert_model_structure_guard | cold_extreme_uncertainty | 222 | 0.5017 | 0.6492 | 1.7952 | 0.9573 | 0.6793 | 8 | 31 |
| cold | segment_balanced | cold_extreme_uncertainty | 222 | 0.5017 | 0.6492 | 1.7952 | 0.9573 | 0.6793 | 8 | 31 |
| cold | segment_mape_guard | cold_extreme_uncertainty | 222 | 0.5017 | 0.6492 | 1.7952 | 0.9573 | 0.6793 | 8 | 31 |
| cold | segment_objective_aware | cold_extreme_uncertainty | 222 | 0.5017 | 0.6492 | 1.7952 | 0.9573 | 0.6793 | 8 | 31 |
| cold | segment_p95_guard | cold_extreme_uncertainty | 222 | 0.5017 | 0.6492 | 1.7952 | 0.9573 | 0.6793 | 8 | 31 |
| cold | single_best_balanced | cold_extreme_uncertainty | 222 | 0.5316 | 0.6602 | 1.8752 | 0.9477 | 0.6988 | 8 | 31 |
| cold | baseline | cold_low_price_uncertain | 158 | 0.6852 | 0.6444 | 1.2427 | 0.9942 | 0.5327 | 2 | 60 |
| cold | expert_model_structure_guard | cold_low_price_uncertain | 158 | 0.6851 | 0.6185 | 1.1578 | 1.0123 | 0.5062 | 2 | 67 |
| cold | segment_balanced | cold_low_price_uncertain | 158 | 0.6851 | 0.6185 | 1.1578 | 1.0123 | 0.5062 | 2 | 67 |
| cold | segment_mape_guard | cold_low_price_uncertain | 158 | 0.6851 | 0.6185 | 1.1578 | 1.0123 | 0.5062 | 2 | 67 |
| cold | segment_objective_aware | cold_low_price_uncertain | 158 | 0.6851 | 0.6185 | 1.1578 | 1.0123 | 0.5062 | 2 | 67 |
| cold | segment_p95_guard | cold_low_price_uncertain | 158 | 0.6851 | 0.6185 | 1.1578 | 1.0123 | 0.5062 | 2 | 67 |
| cold | single_best_balanced | cold_low_price_uncertain | 158 | 0.7049 | 0.6198 | 1.0621 | 1.0370 | 0.4898 | 1 | 65 |
| cold | baseline | cold_meta_sparse | 996 | 0.3772 | 0.7559 | 3.8706 | 0.7259 | 1.0469 | 92 | 48 |
| cold | expert_model_structure_guard | cold_meta_sparse | 996 | 0.3617 | 0.6923 | 3.3102 | 0.7128 | 1.0144 | 92 | 54 |
| cold | segment_balanced | cold_meta_sparse | 996 | 0.3883 | 0.7846 | 4.0013 | 0.7387 | 1.0508 | 90 | 47 |
| cold | segment_mape_guard | cold_meta_sparse | 996 | 0.3883 | 0.7846 | 4.0013 | 0.7387 | 1.0508 | 90 | 47 |
| cold | segment_objective_aware | cold_meta_sparse | 996 | 0.3883 | 0.7846 | 4.0013 | 0.7387 | 1.0508 | 90 | 47 |
| cold | segment_p95_guard | cold_meta_sparse | 996 | 0.3883 | 0.7846 | 4.0013 | 0.7387 | 1.0508 | 90 | 47 |
| cold | single_best_balanced | cold_meta_sparse | 996 | 0.3617 | 0.6923 | 3.3102 | 0.7128 | 1.0144 | 92 | 54 |
| cold | baseline | cold_sparse_artist_high_pred | 1718 | 0.4185 | 1.1993 | 3.0306 | 0.9051 | 0.9138 | 116 | 133 |
| cold | expert_model_structure_guard | cold_sparse_artist_high_pred | 1718 | 0.4185 | 1.1993 | 3.0306 | 0.9051 | 0.9138 | 116 | 133 |
| cold | segment_balanced | cold_sparse_artist_high_pred | 1718 | 0.4145 | 1.2033 | 3.0855 | 0.9023 | 0.9235 | 119 | 131 |
| cold | segment_mape_guard | cold_sparse_artist_high_pred | 1718 | 0.4185 | 1.1993 | 3.0306 | 0.9051 | 0.9138 | 116 | 133 |
| cold | segment_objective_aware | cold_sparse_artist_high_pred | 1718 | 0.4185 | 1.1993 | 3.0306 | 0.9051 | 0.9138 | 116 | 133 |
| cold | segment_p95_guard | cold_sparse_artist_high_pred | 1718 | 0.4185 | 1.1993 | 3.0306 | 0.9051 | 0.9138 | 116 | 133 |
| cold | single_best_balanced | cold_sparse_artist_high_pred | 1718 | 0.4282 | 1.2458 | 3.3082 | 0.9076 | 0.9426 | 127 | 126 |
| cold | baseline | cold_upper_tail_or_large | 5 | 0.3193 | 0.3263 | 0.4340 | 0.4177 | 0.6807 | 0 | 0 |
| cold | expert_model_structure_guard | cold_upper_tail_or_large | 5 | 0.3193 | 0.3263 | 0.4340 | 0.4177 | 0.6807 | 0 | 0 |
| cold | segment_balanced | cold_upper_tail_or_large | 5 | 0.3745 | 0.3810 | 0.4799 | 0.4995 | 0.6255 | 0 | 0 |
| cold | segment_mape_guard | cold_upper_tail_or_large | 5 | 0.3745 | 0.3810 | 0.4799 | 0.4995 | 0.6255 | 0 | 0 |
| cold | segment_objective_aware | cold_upper_tail_or_large | 5 | 0.3745 | 0.3810 | 0.4799 | 0.4995 | 0.6255 | 0 | 0 |
| cold | segment_p95_guard | cold_upper_tail_or_large | 5 | 0.3745 | 0.3810 | 0.4799 | 0.4995 | 0.6255 | 0 | 0 |
| cold | single_best_balanced | cold_upper_tail_or_large | 5 | 0.3745 | 0.3810 | 0.4799 | 0.4995 | 0.6255 | 0 | 0 |
| warm | baseline | warm_low_sample | 399 | 0.1819 | 0.2730 | 0.9265 | 0.3880 | 0.9875 | 0 | 4 |
| warm | expert_model_structure_guard | warm_low_sample | 399 | 0.1735 | 0.2703 | 0.9252 | 0.3867 | 0.9843 | 0 | 4 |
| warm | segment_balanced | warm_low_sample | 399 | 0.1729 | 0.2697 | 0.9213 | 0.3863 | 0.9830 | 0 | 4 |
| warm | segment_mape_guard | warm_low_sample | 399 | 0.1735 | 0.2703 | 0.9252 | 0.3867 | 0.9843 | 0 | 4 |
| warm | segment_objective_aware | warm_low_sample | 399 | 0.1735 | 0.2703 | 0.9252 | 0.3867 | 0.9843 | 0 | 4 |
| warm | segment_p95_guard | warm_low_sample | 399 | 0.1735 | 0.2703 | 0.9252 | 0.3867 | 0.9843 | 0 | 4 |
| warm | single_best_balanced | warm_low_sample | 399 | 0.1729 | 0.2697 | 0.9213 | 0.3863 | 0.9830 | 0 | 4 |
| warm | baseline | warm_material_weak | 23 | 0.2431 | 0.6622 | 2.8108 | 0.9060 | 1.0643 | 2 | 3 |
| warm | expert_model_structure_guard | warm_material_weak | 23 | 0.2431 | 0.6617 | 2.7644 | 0.9105 | 1.0517 | 2 | 3 |
| warm | segment_balanced | warm_material_weak | 23 | 0.2431 | 0.6617 | 2.7644 | 0.9105 | 1.0517 | 2 | 3 |
| warm | segment_mape_guard | warm_material_weak | 23 | 0.2431 | 0.6617 | 2.7644 | 0.9105 | 1.0517 | 2 | 3 |
| warm | segment_objective_aware | warm_material_weak | 23 | 0.2431 | 0.6617 | 2.7644 | 0.9105 | 1.0517 | 2 | 3 |
| warm | segment_p95_guard | warm_material_weak | 23 | 0.2431 | 0.6617 | 2.7644 | 0.9105 | 1.0517 | 2 | 3 |
| warm | single_best_balanced | warm_material_weak | 23 | 0.2431 | 0.6617 | 2.7644 | 0.9105 | 1.0517 | 2 | 3 |
| warm | baseline | warm_regular | 158 | 0.1327 | 0.2344 | 0.5837 | 0.3052 | 1.0208 | 3 | 0 |
| warm | expert_model_structure_guard | warm_regular | 158 | 0.1338 | 0.2311 | 0.5614 | 0.3027 | 1.0174 | 3 | 0 |
| warm | segment_balanced | warm_regular | 158 | 0.1338 | 0.2311 | 0.5614 | 0.3027 | 1.0174 | 3 | 0 |
| warm | segment_mape_guard | warm_regular | 158 | 0.1338 | 0.2311 | 0.5614 | 0.3027 | 1.0174 | 3 | 0 |
| warm | segment_objective_aware | warm_regular | 158 | 0.1338 | 0.2311 | 0.5614 | 0.3027 | 1.0174 | 3 | 0 |
| warm | segment_p95_guard | warm_regular | 158 | 0.1338 | 0.2311 | 0.5614 | 0.3027 | 1.0174 | 3 | 0 |
| warm | single_best_balanced | warm_regular | 158 | 0.1332 | 0.2358 | 0.5933 | 0.3067 | 1.0245 | 3 | 0 |
| warm | baseline | warm_upper_tail_or_large | 27 | 0.1543 | 0.3609 | 1.4501 | 0.4228 | 0.9441 | 1 | 0 |
| warm | expert_model_structure_guard | warm_upper_tail_or_large | 27 | 0.1543 | 0.3609 | 1.4501 | 0.4228 | 0.9441 | 1 | 0 |
| warm | segment_balanced | warm_upper_tail_or_large | 27 | 0.1543 | 0.3609 | 1.4501 | 0.4228 | 0.9441 | 1 | 0 |
| warm | segment_mape_guard | warm_upper_tail_or_large | 27 | 0.1543 | 0.3609 | 1.4501 | 0.4228 | 0.9441 | 1 | 0 |
| warm | segment_objective_aware | warm_upper_tail_or_large | 27 | 0.1543 | 0.3609 | 1.4501 | 0.4228 | 0.9441 | 1 | 0 |
| warm | segment_p95_guard | warm_upper_tail_or_large | 27 | 0.1543 | 0.3609 | 1.4501 | 0.4228 | 0.9441 | 1 | 0 |
| warm | single_best_balanced | warm_upper_tail_or_large | 27 | 0.1543 | 0.3609 | 1.4501 | 0.4228 | 0.9441 | 1 | 0 |

## 5. 라우팅 선택 내역

| route | policy | operational_segment | router_validation_n | objective | selected_candidate | baseline_score | selected_score | fallback_used |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cold | expert_model_structure_guard | cold_extreme_uncertainty | 65 | Cold: 퀀타일 폭이 큰 구간은 qwidth 보정, 저가 불확실 구간은 source/크기 보정, 희소 작가 고예측 구간은 기준값 유지 | cold_qwidth_pred_price_w100_pred_price |  |  | False |
| cold | expert_model_structure_guard | cold_low_price_uncertain | 41 | Cold: 퀀타일 폭이 큰 구간은 qwidth 보정, 저가 불확실 구간은 source/크기 보정, 희소 작가 고예측 구간은 기준값 유지 | cold_source_area_w100_pred_price |  |  | False |
| cold | expert_model_structure_guard | cold_meta_sparse | 500 | Cold: 퀀타일 폭이 큰 구간은 qwidth 보정, 저가 불확실 구간은 source/크기 보정, 희소 작가 고예측 구간은 기준값 유지 | cold_qwidth_pred_price_w75_pred_price |  |  | False |
| cold | expert_model_structure_guard | cold_sparse_artist_high_pred | 491 | Cold: 퀀타일 폭이 큰 구간은 qwidth 보정, 저가 불확실 구간은 source/크기 보정, 희소 작가 고예측 구간은 기준값 유지 | baseline_pred_price |  |  | False |
| cold | expert_model_structure_guard | cold_upper_tail_or_large | 0 | Cold: 퀀타일 폭이 큰 구간은 qwidth 보정, 저가 불확실 구간은 source/크기 보정, 희소 작가 고예측 구간은 기준값 유지 | baseline_pred_price |  |  | False |
| cold | segment_balanced | cold_extreme_uncertainty | 65 | balanced | cold_qwidth_pred_price_w100_pred_price | 1.8129 | 1.6142 | False |
| cold | segment_balanced | cold_low_price_uncertain | 41 | balanced | cold_source_area_w100_pred_price | 0.7522 | 0.6328 | False |
| cold | segment_balanced | cold_meta_sparse | 500 | balanced | cold_material_support_area_w75_pred_price | 0.5403 | 0.5027 | False |
| cold | segment_balanced | cold_sparse_artist_high_pred | 491 | balanced | cold_source_area_w25_pred_price | 0.6033 | 0.6000 | False |
| cold | segment_balanced | cold_upper_tail_or_large | 0 | balanced | cold_qwidth_pred_price_w75_pred_price | 0.6242 | 0.6022 | True |
| cold | segment_mape_guard | cold_extreme_uncertainty | 65 | mape_guard | cold_qwidth_pred_price_w100_pred_price | 2.4654 | 2.1711 | False |
| cold | segment_mape_guard | cold_low_price_uncertain | 41 | mape_guard | cold_source_area_w100_pred_price | 0.9384 | 0.7465 | False |
| cold | segment_mape_guard | cold_meta_sparse | 500 | mape_guard | cold_material_support_area_w75_pred_price | 0.6517 | 0.5892 | False |
| cold | segment_mape_guard | cold_sparse_artist_high_pred | 491 | mape_guard | baseline_pred_price | 0.7385 | 0.7385 | False |
| cold | segment_mape_guard | cold_upper_tail_or_large | 0 | mape_guard | cold_qwidth_pred_price_w75_pred_price | 0.7735 | 0.7466 | True |
| cold | segment_objective_aware | cold_extreme_uncertainty | 65 | p95_guard | cold_qwidth_pred_price_w100_pred_price | 3.5739 | 3.1326 | False |
| cold | segment_objective_aware | cold_low_price_uncertain | 41 | mape_guard | cold_source_area_w100_pred_price | 0.9384 | 0.7465 | False |
| cold | segment_objective_aware | cold_meta_sparse | 500 | balanced | cold_material_support_area_w75_pred_price | 0.5403 | 0.5027 | False |
| cold | segment_objective_aware | cold_sparse_artist_high_pred | 491 | mape_guard | baseline_pred_price | 0.7385 | 0.7385 | False |
| cold | segment_objective_aware | cold_upper_tail_or_large | 0 | p95_guard | cold_qwidth_pred_price_w75_pred_price | 0.6242 | 0.6022 | True |
| cold | segment_p95_guard | cold_extreme_uncertainty | 65 | p95_guard | cold_qwidth_pred_price_w100_pred_price | 3.5739 | 3.1326 | False |
| cold | segment_p95_guard | cold_low_price_uncertain | 41 | p95_guard | cold_source_area_w100_pred_price | 1.2737 | 0.9711 | False |
| cold | segment_p95_guard | cold_meta_sparse | 500 | p95_guard | cold_material_support_area_w75_pred_price | 0.8682 | 0.7634 | False |
| cold | segment_p95_guard | cold_sparse_artist_high_pred | 491 | p95_guard | baseline_pred_price | 0.9503 | 0.9503 | False |
| cold | segment_p95_guard | cold_upper_tail_or_large | 0 | p95_guard | cold_qwidth_pred_price_w75_pred_price | 1.0103 | 0.9712 | True |
| cold | single_best_balanced | cold_extreme_uncertainty | 65 | balanced | cold_qwidth_pred_price_w75_pred_price | 0.6242 | 0.6022 | False |
| cold | single_best_balanced | cold_low_price_uncertain | 41 | balanced | cold_qwidth_pred_price_w75_pred_price | 0.6242 | 0.6022 | False |
| cold | single_best_balanced | cold_meta_sparse | 500 | balanced | cold_qwidth_pred_price_w75_pred_price | 0.6242 | 0.6022 | False |
| cold | single_best_balanced | cold_sparse_artist_high_pred | 491 | balanced | cold_qwidth_pred_price_w75_pred_price | 0.6242 | 0.6022 | False |
| cold | single_best_balanced | cold_upper_tail_or_large | 0 | balanced | cold_qwidth_pred_price_w75_pred_price | 0.6242 | 0.6022 | False |
| warm | expert_model_structure_guard | warm_low_sample | 137 | Warm: 표본 부족 구간은 크기/예측가격 보정, 일반 구간은 작가 이력 보정, 고가/대형 구간은 기준값 유지 | warm_area_pred_price_w75_pred_price |  |  | False |
| warm | expert_model_structure_guard | warm_material_weak | 7 | Warm: 표본 부족 구간은 크기/예측가격 보정, 일반 구간은 작가 이력 보정, 고가/대형 구간은 기준값 유지 | warm_area_pred_price_w100_pred_price |  |  | False |
| warm | expert_model_structure_guard | warm_regular | 56 | Warm: 표본 부족 구간은 크기/예측가격 보정, 일반 구간은 작가 이력 보정, 고가/대형 구간은 기준값 유지 | warm_artist_history_band_w100_pred_price |  |  | False |
| warm | expert_model_structure_guard | warm_upper_tail_or_large | 10 | Warm: 표본 부족 구간은 크기/예측가격 보정, 일반 구간은 작가 이력 보정, 고가/대형 구간은 기준값 유지 | baseline_pred_price |  |  | False |
| warm | segment_balanced | warm_low_sample | 137 | balanced | warm_area_pred_price_w100_pred_price | 0.2847 | 0.2829 | False |
| warm | segment_balanced | warm_material_weak | 7 | balanced | warm_area_pred_price_w100_pred_price | 0.3188 | 0.3145 | True |
| warm | segment_balanced | warm_regular | 56 | balanced | warm_artist_history_band_w100_pred_price | 0.3268 | 0.3184 | False |
| warm | segment_balanced | warm_upper_tail_or_large | 10 | balanced | warm_area_pred_price_w100_pred_price | 0.3188 | 0.3145 | True |
| warm | segment_mape_guard | warm_low_sample | 137 | mape_guard | warm_area_pred_price_w75_pred_price | 0.3492 | 0.3482 | False |
| warm | segment_mape_guard | warm_material_weak | 7 | mape_guard | warm_area_pred_price_w100_pred_price | 0.4193 | 0.4115 | True |
| warm | segment_mape_guard | warm_regular | 56 | mape_guard | warm_artist_history_band_w100_pred_price | 0.4546 | 0.4416 | False |
| warm | segment_mape_guard | warm_upper_tail_or_large | 10 | mape_guard | warm_area_pred_price_w100_pred_price | 0.4193 | 0.4115 | True |
| warm | segment_objective_aware | warm_low_sample | 137 | p95_guard | warm_area_pred_price_w75_pred_price | 0.4683 | 0.4665 | False |
| warm | segment_objective_aware | warm_material_weak | 7 | balanced | warm_area_pred_price_w100_pred_price | 0.3188 | 0.3145 | True |
| warm | segment_objective_aware | warm_regular | 56 | balanced | warm_artist_history_band_w100_pred_price | 0.3268 | 0.3184 | False |
| warm | segment_objective_aware | warm_upper_tail_or_large | 10 | p95_guard | warm_area_pred_price_w100_pred_price | 0.3188 | 0.3145 | True |
| warm | segment_p95_guard | warm_low_sample | 137 | p95_guard | warm_area_pred_price_w75_pred_price | 0.4683 | 0.4665 | False |
| warm | segment_p95_guard | warm_material_weak | 7 | p95_guard | warm_area_pred_price_w100_pred_price | 0.5766 | 0.5601 | True |
| warm | segment_p95_guard | warm_regular | 56 | p95_guard | warm_artist_history_band_w100_pred_price | 0.6628 | 0.6411 | False |
| warm | segment_p95_guard | warm_upper_tail_or_large | 10 | p95_guard | warm_area_pred_price_w100_pred_price | 0.5766 | 0.5601 | True |
| warm | single_best_balanced | warm_low_sample | 137 | balanced | warm_area_pred_price_w100_pred_price | 0.3188 | 0.3145 | False |
| warm | single_best_balanced | warm_material_weak | 7 | balanced | warm_area_pred_price_w100_pred_price | 0.3188 | 0.3145 | False |
| warm | single_best_balanced | warm_regular | 56 | balanced | warm_area_pred_price_w100_pred_price | 0.3188 | 0.3145 | False |
| warm | single_best_balanced | warm_upper_tail_or_large | 10 | balanced | warm_area_pred_price_w100_pred_price | 0.3188 | 0.3145 | False |

## 6. 가격 범위 정책 시뮬레이션

| route | pred_policy | range_policy | n | coverage | median_interval_ratio | p90_interval_ratio | miss_low_n | miss_high_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cold | baseline | base_range | 3099 | 0.6305 | 3.8452 | 9.6647 | 500 | 645 |
| cold | baseline | risk_adjusted_range | 3099 | 0.8351 | 7.4882 | 23.7074 | 252 | 259 |
| cold | expert_model_structure_guard | base_range | 3099 | 0.6350 | 3.8452 | 9.6647 | 473 | 658 |
| cold | expert_model_structure_guard | risk_adjusted_range | 3099 | 0.8338 | 7.4882 | 23.7074 | 247 | 268 |
| cold | segment_objective_aware | base_range | 3099 | 0.6276 | 3.8452 | 9.6647 | 495 | 659 |
| cold | segment_objective_aware | risk_adjusted_range | 3099 | 0.8341 | 7.4882 | 23.7074 | 258 | 256 |
| warm | baseline | base_range | 607 | 0.6771 | 1.9559 | 4.6325 | 101 | 95 |
| warm | baseline | risk_adjusted_range | 607 | 0.7908 | 2.6126 | 6.6708 | 70 | 57 |
| warm | expert_model_structure_guard | base_range | 607 | 0.6820 | 1.9559 | 4.6325 | 97 | 96 |
| warm | expert_model_structure_guard | risk_adjusted_range | 607 | 0.7941 | 2.6126 | 6.6708 | 67 | 58 |
| warm | segment_objective_aware | base_range | 607 | 0.6820 | 1.9559 | 4.6325 | 97 | 96 |
| warm | segment_objective_aware | risk_adjusted_range | 607 | 0.7941 | 2.6126 | 6.6708 | 67 | 58 |

## 7. 보정 맵 요약

| route | rule | segment_cols | segments | correction_log_min | correction_log_median | correction_log_max |
| --- | --- | --- | --- | --- | --- | --- |
| warm | global | global | 1 | -0.0064 | -0.0064 | -0.0064 |
| warm | artist_history_band | artist_history_band | 4 | -0.0175 | 0.0002 | 0.0697 |
| warm | svc_coverage_group_n | svc_coverage_tier+svc_group_n_band | 4 | -0.0237 | -0.0052 | 0.0098 |
| warm | area_pred_price | area_band+pred_price_band | 7 | -0.0481 | -0.0093 | 0.0197 |
| warm | material_support_area | medium_support_bucket+area_band | 5 | -0.0525 | -0.0036 | 0.0412 |
| cold | global | global | 1 | 0.0269 | 0.0269 | 0.0269 |
| cold | qwidth_pred_price | uncertainty_band+pred_price_band | 14 | -0.1630 | 0.0699 | 0.2175 |
| cold | meta_area | meta_completeness_band+area_band | 4 | 0.0034 | 0.0435 | 0.1744 |
| cold | material_support_area | medium_support_bucket+area_band | 14 | -0.3000 | -0.0063 | 0.2747 |
| cold | source_area | track4_source+area_band | 9 | -0.2096 | 0.0170 | 0.1962 |

## 8. 산출물

- `outputs/test_policy_metrics.csv`
- `outputs/test_segment_policy_metrics.csv`
- `outputs/routing_selection.csv`
- `outputs/range_policy_metrics.csv`
- `outputs/test_predictions_with_routing.csv`
- `outputs/correction_mapping_summary.csv`
