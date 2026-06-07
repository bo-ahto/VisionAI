# PP-H14-H18 검색 신뢰도 기반 가격 범위/q-width 보정 검증

## 목적

- H12에서 분리한 작가 검색 신뢰도를 Cold 예측의 신뢰도/가격 범위/q-width 보정에 연결한다.
- 검색 피처를 점 예측에 직접 넣는 대신, 신뢰도가 낮은 구간을 넓은 가격 범위와 낮은 confidence로 처리할 수 있는지 확인한다.
- H18 보정은 validation segment median residual로만 correction map을 만들고 test에 적용한다.

## 실행 설정

| 항목 | 값 |
| --- | --- |
| experiment_id | PP-H14-H18 |
| title | 검색 신뢰도 기반 가격 범위/q-width 보정 검증 |
| run_id | pp_h14_h18_20260603_133014 |
| started_at | 2026-06-03T13:30:14 |
| finished_at | 2026-06-03T13:30:14 |
| base_prediction | experiments/track6/PP-Y2_cold_lgbq_search_external_combo/outputs/predictions.csv |
| base_candidate | lgbq_search_all_external_interaction |
| h12_artist_queue | experiments/track6/PP-H12_search_match_disambiguation_review/outputs/artist_match_review_queue.csv |
| qwidth_33_validation | 0.734942 |
| qwidth_66_validation | 1.42027 |
| best_h18_candidate | h18_qwidth_x_h12_median_min80_cap0.2 |
| note | H12 labels are automatic triage labels. Treat H14/H18 as policy diagnostics until manual review is complete. |

## Test 전체 결과

| experiment_id | candidate | split | slice | n | RMSE_log | MdAPE | MAPE | p95_APE | Within_30 | Within_50 | range_coverage | median_range_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-H14-H18 | h14_base_range | test | overall | 3099 |  |  |  |  |  |  | 0.608906 | 3.84524 |
| PP-H14-H18 | h14_conformal80_range | test | overall | 3099 |  |  |  |  |  |  | 0.789932 | 7.63677 |
| PP-H14-H18 | h14_conformal90_range | test | overall | 3099 |  |  |  |  |  |  | 0.875121 | 11.3506 |
| PP-H14-H18 | h14_policy_range | test | overall | 3099 |  |  |  |  |  |  | 0.754114 | 7.34565 |
| PP-H14-H18 | h18_qwidth_x_h12_median_min30_cap0.1 | test | overall | 3099 | 0.865958 | 0.429937 | 1.05691 | 3.00769 | 0.351081 | 0.568893 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min30_cap0.2 | test | overall | 3099 | 0.874312 | 0.426564 | 1.11046 | 3.00769 | 0.366247 | 0.569539 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min30_cap0.3 | test | overall | 3099 | 0.885287 | 0.431931 | 1.18031 | 3.00769 | 0.351081 | 0.566312 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min80_cap0.1 | test | overall | 3099 | 0.860662 | 0.427057 | 1.02832 | 3.00769 | 0.334624 | 0.573411 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min80_cap0.2 | test | overall | 3099 | 0.859805 | 0.423854 | 1.03278 | 3.00769 | 0.343659 | 0.57567 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min80_cap0.3 | test | overall | 3099 | 0.860252 | 0.427618 | 1.04014 | 3.00769 | 0.332043 | 0.573733 |  |  |
| PP-H14-H18 | pp_y2_base | test | overall | 3099 | 0.856668 | 0.442147 | 1.0484 | 3.35373 | 0.324944 | 0.560181 |  |  |

## Test confidence별 결과

| experiment_id | candidate | split | slice | n | RMSE_log | MdAPE | MAPE | p95_APE | Within_30 | Within_50 | range_coverage | median_range_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-H14-H18 | h14_conformal80_range | test | confidence=low | 2192 |  | 0.471789 | 0.693593 | 2.26624 |  |  | 0.78969 | 8.20639 |
| PP-H14-H18 | h14_conformal80_range | test | confidence=medium | 907 |  | 0.375212 | 1.9059 | 6.32139 |  |  | 0.790518 | 6.61003 |
| PP-H14-H18 | h14_conformal90_range | test | confidence=low | 2192 |  | 0.471789 | 0.693593 | 2.26624 |  |  | 0.896442 | 13.8463 |
| PP-H14-H18 | h14_conformal90_range | test | confidence=medium | 907 |  | 0.375212 | 1.9059 | 6.32139 |  |  | 0.823594 | 8.29818 |
| PP-H14-H18 | h14_policy_range | test | confidence=low | 2192 |  | 0.471789 | 0.693593 | 2.26624 |  |  | 0.852646 | 12.3001 |
| PP-H14-H18 | h14_policy_range | test | confidence=medium | 907 |  | 0.375212 | 1.9059 | 6.32139 |  |  | 0.515987 | 2.48167 |
| PP-H14-H18 | h18_qwidth_x_h12_median_min30_cap0.1 | test | confidence=low | 2192 | 0.801454 | 0.443337 | 0.642572 | 2.0114 | 0.312044 | 0.558394 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min30_cap0.1 | test | confidence=medium | 907 | 1.0049 | 0.358831 | 2.05827 | 7.09139 | 0.445424 | 0.594267 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min30_cap0.2 | test | confidence=low | 2192 | 0.799026 | 0.44221 | 0.63902 | 1.95873 | 0.320712 | 0.560219 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min30_cap0.2 | test | confidence=medium | 907 | 1.03387 | 0.337177 | 2.24982 | 7.94237 | 0.476295 | 0.592062 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min30_cap0.3 | test | confidence=low | 2192 | 0.798224 | 0.44594 | 0.638456 | 1.95861 | 0.319343 | 0.558394 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min30_cap0.3 | test | confidence=medium | 907 | 1.06675 | 0.385643 | 2.48986 | 8.88284 | 0.427784 | 0.585447 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min80_cap0.1 | test | confidence=low | 2192 | 0.803043 | 0.443617 | 0.647741 | 2.0114 | 0.310219 | 0.557482 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min80_cap0.1 | test | confidence=medium | 907 | 0.986109 | 0.373419 | 1.9481 | 6.58647 | 0.393605 | 0.611907 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min80_cap0.2 | test | confidence=low | 2192 | 0.80141 | 0.441623 | 0.647055 | 2.0114 | 0.317518 | 0.559307 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min80_cap0.2 | test | confidence=medium | 907 | 0.986768 | 0.373419 | 1.96499 | 7.2025 | 0.406836 | 0.615215 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min80_cap0.3 | test | confidence=low | 2192 | 0.800709 | 0.444982 | 0.646941 | 2.01664 | 0.31615 | 0.557026 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min80_cap0.3 | test | confidence=medium | 907 | 0.989468 | 0.381369 | 1.9904 | 7.26818 | 0.370452 | 0.614112 |  |  |
| PP-H14-H18 | pp_y2_base | test | confidence=low | 2192 | 0.798217 | 0.471789 | 0.693593 | 2.26624 | 0.305201 | 0.540602 |  |  |
| PP-H14-H18 | pp_y2_base | test | confidence=medium | 907 | 0.983692 | 0.375212 | 1.9059 | 6.32139 | 0.372657 | 0.607497 |  |  |

## Test H12 액션별 기준 오차

| experiment_id | candidate | split | slice | n | RMSE_log | MdAPE | MAPE | p95_APE | Within_30 | Within_50 | range_coverage | median_range_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-H14-H18 | pp_y2_base | test | h12_action=candidate_for_h14_h18 | 845 | 0.991704 | 0.352156 | 1.95084 | 6.46645 | 0.409467 | 0.676923 |  |  |
| PP-H14-H18 | pp_y2_base | test | h12_action=confidence_only_or_manual_review | 347 | 0.666002 | 0.514532 | 0.670837 | 1.71392 | 0.256484 | 0.475504 |  |  |
| PP-H14-H18 | pp_y2_base | test | h12_action=not_collected_by_h11_h12 | 1907 | 0.822259 | 0.481657 | 0.717236 | 2.34541 | 0.299948 | 0.523859 |  |  |

## Confidence 등급 분포

| split | confidence_grade | n |
| --- | --- | --- |
| test | low | 2192 |
| test | medium | 907 |
| validation | low | 2120 |
| validation | medium | 633 |

## 보정 맵

| segment_key | n_validation | raw_median_residual_log | correction_log | min_rows | cap | used_global_fallback | candidate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| caution__candidate_for_h14_h18 | 53 | 0.504381 | 0.1 | 30 | 0.1 | False | h18_qwidth_x_h12_median_min30_cap0.1 |
| caution__confidence_only_or_manual_review | 35 | -0.220339 | -0.1 | 30 | 0.1 | False | h18_qwidth_x_h12_median_min30_cap0.1 |
| caution__do_not_use_for_point_prediction | 463 | -0.288453 | -0.1 | 30 | 0.1 | False | h18_qwidth_x_h12_median_min30_cap0.1 |
| caution__not_collected_by_h11_h12 | 357 | -0.0795952 | -0.0795952 | 30 | 0.1 | False | h18_qwidth_x_h12_median_min30_cap0.1 |
| risk__candidate_for_h14_h18 | 5 | -0.726555 | 0.0184387 | 30 | 0.1 | True | h18_qwidth_x_h12_median_min30_cap0.1 |
| risk__do_not_use_for_point_prediction | 20 | -0.631608 | 0.0184387 | 30 | 0.1 | True | h18_qwidth_x_h12_median_min30_cap0.1 |
| risk__not_collected_by_h11_h12 | 911 | -0.0828196 | -0.0828196 | 30 | 0.1 | False | h18_qwidth_x_h12_median_min30_cap0.1 |
| stable__candidate_for_h14_h18 | 528 | 0.373936 | 0.1 | 30 | 0.1 | False | h18_qwidth_x_h12_median_min30_cap0.1 |
| stable__confidence_only_or_manual_review | 52 | -0.16672 | -0.1 | 30 | 0.1 | False | h18_qwidth_x_h12_median_min30_cap0.1 |
| stable__do_not_use_for_point_prediction | 225 | 0.191731 | 0.1 | 30 | 0.1 | False | h18_qwidth_x_h12_median_min30_cap0.1 |
| stable__not_collected_by_h11_h12 | 104 | 0.276924 | 0.1 | 30 | 0.1 | False | h18_qwidth_x_h12_median_min30_cap0.1 |
| __GLOBAL__ | 2753 | 0.0184387 | 0.0184387 | 30 | 0.1 | False | h18_qwidth_x_h12_median_min30_cap0.1 |
| caution__candidate_for_h14_h18 | 53 | 0.504381 | 0.2 | 30 | 0.2 | False | h18_qwidth_x_h12_median_min30_cap0.2 |
| caution__confidence_only_or_manual_review | 35 | -0.220339 | -0.2 | 30 | 0.2 | False | h18_qwidth_x_h12_median_min30_cap0.2 |
| caution__do_not_use_for_point_prediction | 463 | -0.288453 | -0.2 | 30 | 0.2 | False | h18_qwidth_x_h12_median_min30_cap0.2 |
| caution__not_collected_by_h11_h12 | 357 | -0.0795952 | -0.0795952 | 30 | 0.2 | False | h18_qwidth_x_h12_median_min30_cap0.2 |
| risk__candidate_for_h14_h18 | 5 | -0.726555 | 0.0184387 | 30 | 0.2 | True | h18_qwidth_x_h12_median_min30_cap0.2 |
| risk__do_not_use_for_point_prediction | 20 | -0.631608 | 0.0184387 | 30 | 0.2 | True | h18_qwidth_x_h12_median_min30_cap0.2 |
| risk__not_collected_by_h11_h12 | 911 | -0.0828196 | -0.0828196 | 30 | 0.2 | False | h18_qwidth_x_h12_median_min30_cap0.2 |
| stable__candidate_for_h14_h18 | 528 | 0.373936 | 0.2 | 30 | 0.2 | False | h18_qwidth_x_h12_median_min30_cap0.2 |
| stable__confidence_only_or_manual_review | 52 | -0.16672 | -0.16672 | 30 | 0.2 | False | h18_qwidth_x_h12_median_min30_cap0.2 |
| stable__do_not_use_for_point_prediction | 225 | 0.191731 | 0.191731 | 30 | 0.2 | False | h18_qwidth_x_h12_median_min30_cap0.2 |
| stable__not_collected_by_h11_h12 | 104 | 0.276924 | 0.2 | 30 | 0.2 | False | h18_qwidth_x_h12_median_min30_cap0.2 |
| __GLOBAL__ | 2753 | 0.0184387 | 0.0184387 | 30 | 0.2 | False | h18_qwidth_x_h12_median_min30_cap0.2 |
| caution__candidate_for_h14_h18 | 53 | 0.504381 | 0.3 | 30 | 0.3 | False | h18_qwidth_x_h12_median_min30_cap0.3 |
| caution__confidence_only_or_manual_review | 35 | -0.220339 | -0.220339 | 30 | 0.3 | False | h18_qwidth_x_h12_median_min30_cap0.3 |
| caution__do_not_use_for_point_prediction | 463 | -0.288453 | -0.288453 | 30 | 0.3 | False | h18_qwidth_x_h12_median_min30_cap0.3 |
| caution__not_collected_by_h11_h12 | 357 | -0.0795952 | -0.0795952 | 30 | 0.3 | False | h18_qwidth_x_h12_median_min30_cap0.3 |
| risk__candidate_for_h14_h18 | 5 | -0.726555 | 0.0184387 | 30 | 0.3 | True | h18_qwidth_x_h12_median_min30_cap0.3 |
| risk__do_not_use_for_point_prediction | 20 | -0.631608 | 0.0184387 | 30 | 0.3 | True | h18_qwidth_x_h12_median_min30_cap0.3 |
| risk__not_collected_by_h11_h12 | 911 | -0.0828196 | -0.0828196 | 30 | 0.3 | False | h18_qwidth_x_h12_median_min30_cap0.3 |
| stable__candidate_for_h14_h18 | 528 | 0.373936 | 0.3 | 30 | 0.3 | False | h18_qwidth_x_h12_median_min30_cap0.3 |
| stable__confidence_only_or_manual_review | 52 | -0.16672 | -0.16672 | 30 | 0.3 | False | h18_qwidth_x_h12_median_min30_cap0.3 |
| stable__do_not_use_for_point_prediction | 225 | 0.191731 | 0.191731 | 30 | 0.3 | False | h18_qwidth_x_h12_median_min30_cap0.3 |
| stable__not_collected_by_h11_h12 | 104 | 0.276924 | 0.276924 | 30 | 0.3 | False | h18_qwidth_x_h12_median_min30_cap0.3 |
| __GLOBAL__ | 2753 | 0.0184387 | 0.0184387 | 30 | 0.3 | False | h18_qwidth_x_h12_median_min30_cap0.3 |
| caution__candidate_for_h14_h18 | 53 | 0.504381 | 0.0184387 | 80 | 0.1 | True | h18_qwidth_x_h12_median_min80_cap0.1 |
| caution__confidence_only_or_manual_review | 35 | -0.220339 | 0.0184387 | 80 | 0.1 | True | h18_qwidth_x_h12_median_min80_cap0.1 |
| caution__do_not_use_for_point_prediction | 463 | -0.288453 | -0.1 | 80 | 0.1 | False | h18_qwidth_x_h12_median_min80_cap0.1 |
| caution__not_collected_by_h11_h12 | 357 | -0.0795952 | -0.0795952 | 80 | 0.1 | False | h18_qwidth_x_h12_median_min80_cap0.1 |
| risk__candidate_for_h14_h18 | 5 | -0.726555 | 0.0184387 | 80 | 0.1 | True | h18_qwidth_x_h12_median_min80_cap0.1 |
| risk__do_not_use_for_point_prediction | 20 | -0.631608 | 0.0184387 | 80 | 0.1 | True | h18_qwidth_x_h12_median_min80_cap0.1 |
| risk__not_collected_by_h11_h12 | 911 | -0.0828196 | -0.0828196 | 80 | 0.1 | False | h18_qwidth_x_h12_median_min80_cap0.1 |
| stable__candidate_for_h14_h18 | 528 | 0.373936 | 0.1 | 80 | 0.1 | False | h18_qwidth_x_h12_median_min80_cap0.1 |
| stable__confidence_only_or_manual_review | 52 | -0.16672 | 0.0184387 | 80 | 0.1 | True | h18_qwidth_x_h12_median_min80_cap0.1 |
| stable__do_not_use_for_point_prediction | 225 | 0.191731 | 0.1 | 80 | 0.1 | False | h18_qwidth_x_h12_median_min80_cap0.1 |
| stable__not_collected_by_h11_h12 | 104 | 0.276924 | 0.1 | 80 | 0.1 | False | h18_qwidth_x_h12_median_min80_cap0.1 |
| __GLOBAL__ | 2753 | 0.0184387 | 0.0184387 | 80 | 0.1 | False | h18_qwidth_x_h12_median_min80_cap0.1 |
| caution__candidate_for_h14_h18 | 53 | 0.504381 | 0.0184387 | 80 | 0.2 | True | h18_qwidth_x_h12_median_min80_cap0.2 |
| caution__confidence_only_or_manual_review | 35 | -0.220339 | 0.0184387 | 80 | 0.2 | True | h18_qwidth_x_h12_median_min80_cap0.2 |
| caution__do_not_use_for_point_prediction | 463 | -0.288453 | -0.2 | 80 | 0.2 | False | h18_qwidth_x_h12_median_min80_cap0.2 |
| caution__not_collected_by_h11_h12 | 357 | -0.0795952 | -0.0795952 | 80 | 0.2 | False | h18_qwidth_x_h12_median_min80_cap0.2 |
| risk__candidate_for_h14_h18 | 5 | -0.726555 | 0.0184387 | 80 | 0.2 | True | h18_qwidth_x_h12_median_min80_cap0.2 |
| risk__do_not_use_for_point_prediction | 20 | -0.631608 | 0.0184387 | 80 | 0.2 | True | h18_qwidth_x_h12_median_min80_cap0.2 |
| risk__not_collected_by_h11_h12 | 911 | -0.0828196 | -0.0828196 | 80 | 0.2 | False | h18_qwidth_x_h12_median_min80_cap0.2 |
| stable__candidate_for_h14_h18 | 528 | 0.373936 | 0.2 | 80 | 0.2 | False | h18_qwidth_x_h12_median_min80_cap0.2 |
| stable__confidence_only_or_manual_review | 52 | -0.16672 | 0.0184387 | 80 | 0.2 | True | h18_qwidth_x_h12_median_min80_cap0.2 |
| stable__do_not_use_for_point_prediction | 225 | 0.191731 | 0.191731 | 80 | 0.2 | False | h18_qwidth_x_h12_median_min80_cap0.2 |
| stable__not_collected_by_h11_h12 | 104 | 0.276924 | 0.2 | 80 | 0.2 | False | h18_qwidth_x_h12_median_min80_cap0.2 |
| __GLOBAL__ | 2753 | 0.0184387 | 0.0184387 | 80 | 0.2 | False | h18_qwidth_x_h12_median_min80_cap0.2 |

## Conformal 범위 버퍼

| confidence_grade | target_coverage | n_validation | conformal_buffer_log | used_global_fallback | candidate |
| --- | --- | --- | --- | --- | --- |
| low | 0.8 | 2120 | 0.21592 | False | h14_conformal80_range |
| medium | 0.8 | 633 | 0.565574 | False | h14_conformal80_range |
| __GLOBAL__ | 0.8 | 2753 | 0.373755 | False | h14_conformal80_range |
| low | 0.9 | 2120 | 0.477472 | False | h14_conformal90_range |
| medium | 0.9 | 633 | 0.679297 | False | h14_conformal90_range |
| __GLOBAL__ | 0.9 | 2753 | 0.566509 | False | h14_conformal90_range |

## 해석

- H14의 핵심은 range coverage가 오르면서 median range ratio가 과도하게 커지지 않는지다.
- H18의 핵심은 validation에서 만든 q-width x H12 action 보정이 test에서 MdAPE/MAPE/p95를 동시에 악화시키지 않는지다.
- H12가 아직 수동 검수 전 자동 라벨이므로, 이 결과는 운영 정책 후보 검증으로 보고 최종 모델 채택 근거로는 보류한다.
