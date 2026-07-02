# Cold k320 제한 적용 정책 검증

- 작성일: 2026-06-18T17:06:05
- 목적: k320 combined를 전체 적용하지 않고 저가/과대예측 위험 구간에만 적용할 때 개선되는지 검증한다.
- 조건: `artist_key`, 같은 작가 가격 이력, lookup 후처리, `search_*`, 외부 live 검색 미사용.
- 모든 정책은 실제 가격을 보지 않고 사용 단계에서 알 수 있는 예측가와 유사작품 통계만 사용한다.

## 1. Test 성능: APE > 5 기준
| candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 | APE_gt_10 | k320_selected_rate | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| low_or_above_ref_and_k320_lower | test | 0.504518 | 0.930618 | 1.999310 | 0.945215 | 155 | 53 | 40 | 0.238787 | 저가 또는 유사작품 대비 과대 후보이고 k320이 0.05 log 이상 낮으면 k320 |
| low_or_above_ref_and_k320_not_higher | test | 0.507358 | 0.930865 | 1.997548 | 0.945238 | 154 | 53 | 40 | 0.596967 | 저가 또는 유사작품 대비 과대 후보이고 k320이 크게 높지 않으면 k320 |
| k320_global | test | 0.513510 | 0.926227 | 2.224042 | 0.932185 | 209 | 54 | 40 | 1.000000 | 항상 k320 combined q35 |
| low_pred_500w_and_k320_lower | test | 0.504419 | 0.956858 | 2.006389 | 0.944976 | 158 | 54 | 40 | 0.174895 | k160 예측가 500만원 미만이고 k320이 0.05 log 이상 낮으면 k320 |
| low_ref_500w_and_k320_lower | test | 0.504360 | 0.935543 | 2.006389 | 0.942125 | 158 | 55 | 40 | 0.161988 | 유사작품 중앙 기준가 500만원 미만이고 k320이 0.05 log 이상 낮으면 k320 |
| above_refq25_and_k320_lower | test | 0.498081 | 0.934943 | 2.003293 | 0.943555 | 157 | 56 | 40 | 0.182962 | k160 예측이 유사작품 q25보다 0.20 log 이상 높고 k320이 더 낮으면 k320 |
| high_iqr_above_ref_and_k320_lower | test | 0.498081 | 0.953771 | 2.003293 | 0.944177 | 157 | 56 | 40 | 0.127783 | 유사작품 분산이 크고 과대 후보이며 k320이 더 낮으면 k320 |
| low_pred_300w_and_k320_lower | test | 0.501657 | 0.962548 | 2.011615 | 0.945261 | 159 | 56 | 40 | 0.127460 | k160 예측가 300만원 미만이고 k320이 0.05 log 이상 낮으면 k320 |
| low_ref_300w_and_k320_lower | test | 0.501657 | 0.954190 | 2.067088 | 0.944462 | 161 | 57 | 40 | 0.110358 | 유사작품 중앙 기준가 300만원 미만이고 k320이 0.05 log 이상 낮으면 k320 |
| base_k160 | test | 0.495018 | 0.971691 | 2.090436 | 0.943144 | 163 | 58 | 40 | 0.000000 | 항상 k160 q35 기준선 |

## 2. Validation 성능: APE > 5 기준
| candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 | APE_gt_10 | k320_selected_rate | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| low_or_above_ref_and_k320_not_higher | validation | 0.379808 | 0.467713 | 1.050065 | 0.684340 | 44 | 8 | 1 | 0.660371 | 저가 또는 유사작품 대비 과대 후보이고 k320이 크게 높지 않으면 k320 |
| low_or_above_ref_and_k320_lower | validation | 0.379808 | 0.467829 | 1.065524 | 0.684668 | 44 | 8 | 1 | 0.261896 | 저가 또는 유사작품 대비 과대 후보이고 k320이 0.05 log 이상 낮으면 k320 |
| low_ref_500w_and_k320_lower | validation | 0.379808 | 0.468315 | 1.065524 | 0.682531 | 44 | 8 | 1 | 0.220124 | 유사작품 중앙 기준가 500만원 미만이고 k320이 0.05 log 이상 낮으면 k320 |
| low_pred_500w_and_k320_lower | validation | 0.379808 | 0.468562 | 1.065524 | 0.683015 | 44 | 8 | 1 | 0.231747 | k160 예측가 500만원 미만이고 k320이 0.05 log 이상 낮으면 k320 |
| low_pred_300w_and_k320_lower | validation | 0.379808 | 0.468935 | 1.071175 | 0.680596 | 44 | 8 | 1 | 0.192880 | k160 예측가 300만원 미만이고 k320이 0.05 log 이상 낮으면 k320 |
| high_iqr_above_ref_and_k320_lower | validation | 0.355152 | 0.469440 | 1.071175 | 0.677860 | 46 | 8 | 1 | 0.072648 | 유사작품 분산이 크고 과대 후보이며 k320이 더 낮으면 k320 |
| above_refq25_and_k320_lower | validation | 0.379808 | 0.470518 | 1.071175 | 0.680917 | 46 | 8 | 1 | 0.134036 | k160 예측이 유사작품 q25보다 0.20 log 이상 높고 k320이 더 낮으면 k320 |
| low_ref_300w_and_k320_lower | validation | 0.379808 | 0.470577 | 1.071175 | 0.678761 | 44 | 8 | 1 | 0.172902 | 유사작품 중앙 기준가 300만원 미만이고 k320이 0.05 log 이상 낮으면 k320 |
| base_k160 | validation | 0.359201 | 0.475196 | 1.115400 | 0.673808 | 46 | 8 | 1 | 0.000000 | 항상 k160 q35 기준선 |
| k320_global | validation | 0.377500 | 0.477518 | 1.084326 | 0.679118 | 47 | 8 | 1 | 1.000000 | 항상 k320 combined q35 |

## 3. Paired bootstrap vs base_k160
| split | candidate_a | candidate_b | n | n_boot | delta_MdAPE_a_minus_b_mean | delta_MAPE_a_minus_b_mean | delta_p95_APE_a_minus_b_mean | p_delta_MAPE_a_minus_b_lt_0 | p_delta_p95_APE_a_minus_b_lt_0 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | k320_global | base_k160 | 2753 | 800 | 0.016401 | 0.002390 | -0.024364 | 0.157500 | 0.766250 |
| validation | low_pred_300w_and_k320_lower | base_k160 | 2753 | 800 | 0.019943 | -0.006138 | -0.034387 | 1.000000 | 0.883750 |
| validation | low_pred_500w_and_k320_lower | base_k160 | 2753 | 800 | 0.019881 | -0.006519 | -0.064955 | 1.000000 | 0.985000 |
| validation | low_ref_300w_and_k320_lower | base_k160 | 2753 | 800 | 0.019995 | -0.004538 | -0.030773 | 1.000000 | 0.868750 |
| validation | low_ref_500w_and_k320_lower | base_k160 | 2753 | 800 | 0.019971 | -0.006782 | -0.064955 | 1.000000 | 0.985000 |
| validation | above_refq25_and_k320_lower | base_k160 | 2753 | 800 | 0.018493 | -0.004626 | -0.028376 | 1.000000 | 0.852500 |
| validation | low_or_above_ref_and_k320_lower | base_k160 | 2753 | 800 | 0.019324 | -0.007261 | -0.064916 | 1.000000 | 0.985000 |
| validation | low_or_above_ref_and_k320_not_higher | base_k160 | 2753 | 800 | 0.018661 | -0.007400 | -0.069132 | 1.000000 | 0.995000 |
| validation | high_iqr_above_ref_and_k320_lower | base_k160 | 2753 | 800 | -0.003426 | -0.005717 | -0.021924 | 1.000000 | 0.781250 |
| test | k320_global | base_k160 | 3099 | 800 | 0.016315 | -0.044886 | 0.133802 | 1.000000 | 0.178750 |
| test | low_pred_300w_and_k320_lower | base_k160 | 3099 | 800 | 0.003644 | -0.009262 | -0.052376 | 1.000000 | 0.932500 |
| test | low_pred_500w_and_k320_lower | base_k160 | 3099 | 800 | 0.005142 | -0.014975 | -0.069505 | 1.000000 | 0.953750 |
| test | low_ref_300w_and_k320_lower | base_k160 | 3099 | 800 | 0.003663 | -0.016886 | -0.019917 | 1.000000 | 0.740000 |
| test | low_ref_500w_and_k320_lower | base_k160 | 3099 | 800 | 0.004520 | -0.035595 | -0.061576 | 1.000000 | 0.958750 |
| test | above_refq25_and_k320_lower | base_k160 | 3099 | 800 | 0.001287 | -0.036144 | -0.055888 | 1.000000 | 0.950000 |
| test | low_or_above_ref_and_k320_lower | base_k160 | 3099 | 800 | 0.006566 | -0.040503 | -0.092409 | 1.000000 | 0.966250 |
| test | low_or_above_ref_and_k320_not_higher | base_k160 | 3099 | 800 | 0.009046 | -0.040258 | -0.103137 | 1.000000 | 0.978750 |
| test | high_iqr_above_ref_and_k320_lower | base_k160 | 3099 | 800 | 0.001278 | -0.017658 | -0.052403 | 1.000000 | 0.947500 |

## 4. Test 가격대별 진단
| candidate | split | segment | n | k320_selected_rate | MdAPE | MAPE | p95_APE | APE_gt_2 | APE_gt_5 | APE_gt_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| above_refq25_and_k320_lower | test | 1m_3m | 866 | 0.215935 | 0.448037 | 0.735597 | 2.060400 | 47 | 5 | 2 |
| high_iqr_above_ref_and_k320_lower | test | 1m_3m | 866 | 0.129330 | 0.445874 | 0.762492 | 2.060400 | 47 | 5 | 2 |
| k320_global | test | 1m_3m | 866 | 1.000000 | 0.464200 | 0.744423 | 2.174374 | 54 | 3 | 2 |
| low_or_above_ref_and_k320_lower | test | 1m_3m | 866 | 0.279446 | 0.449739 | 0.729384 | 2.034346 | 47 | 5 | 2 |
| low_or_above_ref_and_k320_not_higher | test | 1m_3m | 866 | 0.678984 | 0.453904 | 0.728474 | 2.054064 | 47 | 5 | 2 |
| low_pred_300w_and_k320_lower | test | 1m_3m | 866 | 0.185912 | 0.451840 | 0.776695 | 2.215003 | 51 | 6 | 2 |
| low_pred_500w_and_k320_lower | test | 1m_3m | 866 | 0.255196 | 0.449739 | 0.759642 | 2.183348 | 50 | 6 | 2 |
| low_ref_500w_and_k320_lower | test | 1m_3m | 866 | 0.252887 | 0.450765 | 0.739395 | 2.212824 | 50 | 6 | 2 |
| above_refq25_and_k320_lower | test | 3m_10m | 1057 | 0.149480 | 0.461938 | 0.476929 | 0.890522 | 7 | 2 | 0 |
| high_iqr_above_ref_and_k320_lower | test | 3m_10m | 1057 | 0.094607 | 0.460171 | 0.480745 | 0.890522 | 7 | 2 | 0 |
| k320_global | test | 3m_10m | 1057 | 1.000000 | 0.463550 | 0.479942 | 0.899843 | 7 | 2 | 0 |
| low_or_above_ref_and_k320_lower | test | 3m_10m | 1057 | 0.220435 | 0.468990 | 0.480556 | 0.890522 | 7 | 2 | 0 |
| low_or_above_ref_and_k320_not_higher | test | 3m_10m | 1057 | 0.593188 | 0.467096 | 0.480042 | 0.890522 | 7 | 2 | 0 |
| low_pred_300w_and_k320_lower | test | 3m_10m | 1057 | 0.105014 | 0.472482 | 0.487030 | 0.895791 | 7 | 2 | 0 |
| low_pred_500w_and_k320_lower | test | 3m_10m | 1057 | 0.168401 | 0.475924 | 0.489099 | 0.895791 | 7 | 2 | 0 |
| low_ref_500w_and_k320_lower | test | 3m_10m | 1057 | 0.145695 | 0.474917 | 0.488217 | 0.895791 | 7 | 2 | 0 |
| above_refq25_and_k320_lower | test | gt_10m | 636 | 0.204403 | 0.556020 | 0.557700 | 0.909753 | 0 | 0 | 0 |
| high_iqr_above_ref_and_k320_lower | test | gt_10m | 636 | 0.174528 | 0.556020 | 0.556316 | 0.909753 | 0 | 0 | 0 |
| k320_global | test | gt_10m | 636 | 1.000000 | 0.541008 | 0.553264 | 0.907861 | 0 | 0 | 0 |
| low_or_above_ref_and_k320_lower | test | gt_10m | 636 | 0.218553 | 0.556020 | 0.558157 | 0.909753 | 0 | 0 | 0 |
| low_or_above_ref_and_k320_not_higher | test | gt_10m | 636 | 0.548742 | 0.557056 | 0.559314 | 0.909628 | 0 | 0 | 0 |
| low_pred_300w_and_k320_lower | test | gt_10m | 636 | 0.001572 | 0.554615 | 0.547320 | 0.909412 | 0 | 0 | 0 |
| low_pred_500w_and_k320_lower | test | gt_10m | 636 | 0.029874 | 0.554615 | 0.548277 | 0.909412 | 0 | 0 | 0 |
| low_ref_500w_and_k320_lower | test | gt_10m | 636 | 0.006289 | 0.554615 | 0.547398 | 0.909412 | 0 | 0 | 0 |
| above_refq25_and_k320_lower | test | lt_1m | 540 | 0.170370 | 0.645185 | 2.595464 | 20.911669 | 103 | 49 | 38 |
| high_iqr_above_ref_and_k320_lower | test | lt_1m | 540 | 0.135185 | 0.648314 | 2.654544 | 20.911669 | 103 | 49 | 38 |
| k320_global | test | lt_1m | 540 | 1.000000 | 0.718872 | 2.530614 | 19.417337 | 148 | 49 | 38 |
| low_or_above_ref_and_k320_lower | test | lt_1m | 540 | 0.233333 | 0.633322 | 2.572971 | 20.911669 | 101 | 46 | 38 |
| low_or_above_ref_and_k320_not_higher | test | lt_1m | 540 | 0.529630 | 0.628247 | 2.575488 | 20.911669 | 100 | 46 | 38 |
| low_pred_300w_and_k320_lower | test | lt_1m | 540 | 0.225926 | 0.633322 | 2.680430 | 20.911669 | 101 | 48 | 38 |
| low_pred_500w_and_k320_lower | test | lt_1m | 540 | 0.229630 | 0.633322 | 2.669949 | 20.911669 | 101 | 46 | 38 |
| low_ref_500w_and_k320_lower | test | lt_1m | 540 | 0.231481 | 0.633322 | 2.582856 | 20.911669 | 101 | 47 | 38 |

## 5. Test 결측 스트레스
| candidate | stress_scenario | split | MdAPE | MAPE | p95_APE | APE_gt_2 | APE_gt_5 | APE_gt_10 | k320_selected_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| above_refq25_and_k320_lower | as_is | test | 0.498081 | 0.934943 | 2.003293 | 157 | 56 | 40 | 0.182962 |
| k320_global | as_is | test | 0.513510 | 0.926227 | 2.224042 | 209 | 54 | 40 | 1.000000 |
| low_or_above_ref_and_k320_lower | as_is | test | 0.504518 | 0.930618 | 1.999310 | 155 | 53 | 40 | 0.238787 |
| low_or_above_ref_and_k320_not_higher | as_is | test | 0.507358 | 0.930865 | 1.997548 | 154 | 53 | 40 | 0.596967 |
| low_pred_500w_and_k320_lower | as_is | test | 0.504419 | 0.956858 | 2.006389 | 158 | 54 | 40 | 0.174895 |
| low_ref_500w_and_k320_lower | as_is | test | 0.504360 | 0.935543 | 2.006389 | 158 | 55 | 40 | 0.161988 |
| above_refq25_and_k320_lower | missing_all_core_numeric | test | 0.497259 | 0.897913 | 2.513550 | 179 | 69 | 36 | 0.180381 |
| k320_global | missing_all_core_numeric | test | 0.498081 | 0.900627 | 2.457310 | 177 | 68 | 36 | 1.000000 |
| low_or_above_ref_and_k320_lower | missing_all_core_numeric | test | 0.498081 | 0.893183 | 2.429976 | 177 | 67 | 36 | 0.251694 |
| low_or_above_ref_and_k320_not_higher | missing_all_core_numeric | test | 0.498081 | 0.895085 | 2.351463 | 175 | 67 | 36 | 0.646015 |
| low_pred_500w_and_k320_lower | missing_all_core_numeric | test | 0.495017 | 0.899415 | 2.429976 | 177 | 68 | 36 | 0.194902 |
| low_ref_500w_and_k320_lower | missing_all_core_numeric | test | 0.497176 | 0.902787 | 2.429976 | 179 | 69 | 36 | 0.174572 |
| above_refq25_and_k320_lower | missing_birth_and_followers | test | 0.504419 | 0.935878 | 2.006389 | 158 | 56 | 40 | 0.189093 |
| k320_global | missing_birth_and_followers | test | 0.513955 | 0.924460 | 2.224042 | 209 | 54 | 40 | 1.000000 |
| low_or_above_ref_and_k320_lower | missing_birth_and_followers | test | 0.507905 | 0.931522 | 2.001313 | 156 | 53 | 40 | 0.244918 |
| low_or_above_ref_and_k320_not_higher | missing_birth_and_followers | test | 0.510326 | 0.931504 | 1.997548 | 154 | 53 | 40 | 0.610520 |
| low_pred_500w_and_k320_lower | missing_birth_and_followers | test | 0.507905 | 0.958223 | 2.006389 | 158 | 54 | 40 | 0.181349 |
| low_ref_500w_and_k320_lower | missing_birth_and_followers | test | 0.507905 | 0.936856 | 2.011615 | 159 | 55 | 40 | 0.168441 |
| above_refq25_and_k320_lower | missing_birth_year | test | 0.504419 | 0.935878 | 2.006389 | 158 | 56 | 40 | 0.189093 |
| k320_global | missing_birth_year | test | 0.513955 | 0.924460 | 2.224042 | 209 | 54 | 40 | 1.000000 |
| low_or_above_ref_and_k320_lower | missing_birth_year | test | 0.507905 | 0.931522 | 2.001313 | 156 | 53 | 40 | 0.244918 |
| low_or_above_ref_and_k320_not_higher | missing_birth_year | test | 0.510326 | 0.931504 | 1.997548 | 154 | 53 | 40 | 0.610520 |
| low_pred_500w_and_k320_lower | missing_birth_year | test | 0.507905 | 0.958223 | 2.006389 | 158 | 54 | 40 | 0.181349 |
| low_ref_500w_and_k320_lower | missing_birth_year | test | 0.507905 | 0.936856 | 2.011615 | 159 | 55 | 40 | 0.168441 |
| above_refq25_and_k320_lower | missing_career_stage | test | 0.497259 | 0.898476 | 2.513550 | 178 | 69 | 36 | 0.171023 |
| k320_global | missing_career_stage | test | 0.500515 | 0.902550 | 2.460385 | 177 | 68 | 36 | 1.000000 |
| low_or_above_ref_and_k320_lower | missing_career_stage | test | 0.500455 | 0.894226 | 2.429976 | 176 | 67 | 36 | 0.240723 |
| low_or_above_ref_and_k320_not_higher | missing_career_stage | test | 0.500515 | 0.896638 | 2.351463 | 175 | 67 | 36 | 0.634398 |
| low_pred_500w_and_k320_lower | missing_career_stage | test | 0.497550 | 0.900137 | 2.429976 | 177 | 68 | 36 | 0.186834 |
| low_ref_500w_and_k320_lower | missing_career_stage | test | 0.497550 | 0.903382 | 2.429976 | 178 | 69 | 36 | 0.166828 |
| above_refq25_and_k320_lower | missing_followers | test | 0.498081 | 0.934943 | 2.003293 | 157 | 56 | 40 | 0.182962 |
| k320_global | missing_followers | test | 0.513510 | 0.926227 | 2.224042 | 209 | 54 | 40 | 1.000000 |
| low_or_above_ref_and_k320_lower | missing_followers | test | 0.504518 | 0.930618 | 1.999310 | 155 | 53 | 40 | 0.238787 |
| low_or_above_ref_and_k320_not_higher | missing_followers | test | 0.507358 | 0.930865 | 1.997548 | 154 | 53 | 40 | 0.596967 |
| low_pred_500w_and_k320_lower | missing_followers | test | 0.504419 | 0.956858 | 2.006389 | 158 | 54 | 40 | 0.174895 |
| low_ref_500w_and_k320_lower | missing_followers | test | 0.504360 | 0.935543 | 2.006389 | 158 | 55 | 40 | 0.161988 |
| above_refq25_and_k320_lower | missing_total_works | test | 0.498081 | 0.934943 | 2.003293 | 157 | 56 | 40 | 0.182962 |
| k320_global | missing_total_works | test | 0.513510 | 0.926227 | 2.224042 | 209 | 54 | 40 | 1.000000 |
| low_or_above_ref_and_k320_lower | missing_total_works | test | 0.504518 | 0.930618 | 1.999310 | 155 | 53 | 40 | 0.238787 |
| low_or_above_ref_and_k320_not_higher | missing_total_works | test | 0.507358 | 0.930865 | 1.997548 | 154 | 53 | 40 | 0.596967 |
| low_pred_500w_and_k320_lower | missing_total_works | test | 0.504419 | 0.956858 | 2.006389 | 158 | 54 | 40 | 0.174895 |
| low_ref_500w_and_k320_lower | missing_total_works | test | 0.504360 | 0.935543 | 2.006389 | 158 | 55 | 40 | 0.161988 |