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
| run_id | pp_h14_h18_20260603_160602 |
| started_at | 2026-06-03T16:06:02 |
| finished_at | 2026-06-03T16:06:02 |
| base_prediction | experiments/track6/PP-Y2_cold_lgbq_search_external_combo/outputs/predictions.csv |
| base_candidate | lgbq_search_all_external_interaction |
| h12_artist_queue | experiments/track6/PP-H12B_search_match_review_label_refinement/outputs/artist_match_review_queue_refined.csv |
| qwidth_33_validation | 0.734942 |
| qwidth_66_validation | 1.42027 |
| best_h18_candidate | h18_qwidth_x_h12_median_min80_cap0.2 |
| note | H12 labels are automatic triage labels. Treat H14/H18 as policy diagnostics until manual review is complete. |

## Test 전체 결과

| experiment_id | candidate | split | slice | n | RMSE_log | MdAPE | MAPE | p95_APE | Within_30 | Within_50 | range_coverage | median_range_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-H14-H18 | h14_base_range | test | overall | 3099 |  |  |  |  |  |  | 0.608906 | 3.84524 |
| PP-H14-H18 | h14_conformal80_range | test | overall | 3099 |  |  |  |  |  |  | 0.808003 | 8.15647 |
| PP-H14-H18 | h14_conformal90_range | test | overall | 3099 |  |  |  |  |  |  | 0.876734 | 11.7173 |
| PP-H14-H18 | h14_policy_range | test | overall | 3099 |  |  |  |  |  |  | 0.753792 | 7.44614 |
| PP-H14-H18 | h18_qwidth_x_h12_median_min30_cap0.1 | test | overall | 3099 | 0.866321 | 0.426564 | 1.07029 | 3.00769 | 0.349468 | 0.575024 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min30_cap0.2 | test | overall | 3099 | 0.875543 | 0.418103 | 1.13554 | 3.00769 | 0.366247 | 0.577606 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min30_cap0.3 | test | overall | 3099 | 0.888884 | 0.427503 | 1.21425 | 3.02267 | 0.351726 | 0.574056 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min80_cap0.1 | test | overall | 3099 | 0.860202 | 0.425992 | 1.03056 | 3.00769 | 0.337528 | 0.576638 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min80_cap0.2 | test | overall | 3099 | 0.860387 | 0.41797 | 1.04107 | 3.00769 | 0.348822 | 0.579864 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min80_cap0.3 | test | overall | 3099 | 0.863122 | 0.423854 | 1.05642 | 3.00769 | 0.34011 | 0.578896 |  |  |
| PP-H14-H18 | pp_y2_base | test | overall | 3099 | 0.856668 | 0.442147 | 1.0484 | 3.35373 | 0.324944 | 0.560181 |  |  |

## Test confidence별 결과

| experiment_id | candidate | split | slice | n | RMSE_log | MdAPE | MAPE | p95_APE | Within_30 | Within_50 | range_coverage | median_range_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-H14-H18 | h14_conformal80_range | test | confidence=low | 2183 |  | 0.471398 | 0.684465 | 2.16475 |  |  | 0.813101 | 8.8254 |
| PP-H14-H18 | h14_conformal80_range | test | confidence=medium | 916 |  | 0.375334 | 1.91574 | 6.29874 |  |  | 0.795852 | 7.27864 |
| PP-H14-H18 | h14_conformal90_range | test | confidence=low | 2183 |  | 0.471398 | 0.684465 | 2.16475 |  |  | 0.897389 | 13.5435 |
| PP-H14-H18 | h14_conformal90_range | test | confidence=medium | 916 |  | 0.375334 | 1.91574 | 6.29874 |  |  | 0.827511 | 9.76807 |
| PP-H14-H18 | h14_policy_range | test | confidence=low | 2183 |  | 0.471398 | 0.684465 | 2.16475 |  |  | 0.861658 | 12.4135 |
| PP-H14-H18 | h14_policy_range | test | confidence=medium | 916 |  | 0.375334 | 1.91574 | 6.29874 |  |  | 0.496725 | 2.48167 |
| PP-H14-H18 | h18_qwidth_x_h12_median_min30_cap0.1 | test | confidence=low | 2183 | 0.797158 | 0.440762 | 0.633225 | 1.91321 | 0.313788 | 0.562987 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min30_cap0.1 | test | confidence=medium | 916 | 1.01227 | 0.357782 | 2.1119 | 7.06635 | 0.434498 | 0.603712 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min30_cap0.2 | test | confidence=low | 2183 | 0.794605 | 0.435587 | 0.629336 | 1.92165 | 0.32524 | 0.568484 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min30_cap0.2 | test | confidence=medium | 916 | 1.04342 | 0.347562 | 2.34192 | 7.9147 | 0.463974 | 0.599345 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min30_cap0.3 | test | confidence=low | 2183 | 0.793443 | 0.435587 | 0.626968 | 1.92165 | 0.327531 | 0.567109 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min30_cap0.3 | test | confidence=medium | 916 | 1.08294 | 0.389117 | 2.61386 | 8.85227 | 0.409389 | 0.590611 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min80_cap0.1 | test | confidence=low | 2183 | 0.797158 | 0.440762 | 0.633225 | 1.91321 | 0.313788 | 0.562987 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min80_cap0.1 | test | confidence=medium | 916 | 0.994464 | 0.368121 | 1.97748 | 6.58647 | 0.394105 | 0.60917 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min80_cap0.2 | test | confidence=low | 2183 | 0.794605 | 0.435587 | 0.629336 | 1.92165 | 0.32524 | 0.568484 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min80_cap0.2 | test | confidence=medium | 916 | 0.99986 | 0.365121 | 2.02232 | 7.01888 | 0.405022 | 0.606987 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min80_cap0.3 | test | confidence=low | 2183 | 0.793443 | 0.435587 | 0.626968 | 1.92165 | 0.327531 | 0.567109 |  |  |
| PP-H14-H18 | h18_qwidth_x_h12_median_min80_cap0.3 | test | confidence=medium | 916 | 1.00998 | 0.380384 | 2.07987 | 7.04234 | 0.370087 | 0.606987 |  |  |
| PP-H14-H18 | pp_y2_base | test | confidence=low | 2183 | 0.793932 | 0.471398 | 0.684465 | 2.16475 | 0.30371 | 0.541915 |  |  |
| PP-H14-H18 | pp_y2_base | test | confidence=medium | 916 | 0.990284 | 0.375334 | 1.91574 | 6.29874 | 0.375546 | 0.603712 |  |  |

## Test H12 액션별 기준 오차

| experiment_id | candidate | split | slice | n | RMSE_log | MdAPE | MAPE | p95_APE | Within_30 | Within_50 | range_coverage | median_range_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-H14-H18 | pp_y2_base | test | h12_action=candidate_for_h14_h18 | 1039 | 0.959922 | 0.379552 | 1.74169 | 5.88258 | 0.366699 | 0.612127 |  |  |
| PP-H14-H18 | pp_y2_base | test | h12_action=manual_review_required | 153 | 0.424462 | 0.397041 | 0.468122 | 1.24359 | 0.352941 | 0.660131 |  |  |
| PP-H14-H18 | pp_y2_base | test | h12_action=not_collected_by_h11_h12 | 1907 | 0.822259 | 0.481657 | 0.717236 | 2.34541 | 0.299948 | 0.523859 |  |  |

## Confidence 등급 분포

| split | confidence_grade | n |
| --- | --- | --- |
| test | low | 2183 |
| test | medium | 916 |
| validation | low | 2289 |
| validation | medium | 464 |

## 보정 맵

| segment_key | n_validation | raw_median_residual_log | correction_log | min_rows | cap | used_global_fallback | candidate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| caution__candidate_for_h14_h18 | 52 | 0.506851 | 0.1 | 30 | 0.1 | False | h18_qwidth_x_h12_median_min30_cap0.1 |
| caution__confidence_only_or_manual_review | 37 | -0.0447311 | -0.0447311 | 30 | 0.1 | False | h18_qwidth_x_h12_median_min30_cap0.1 |
| caution__do_not_use_for_point_prediction | 77 | -0.0135022 | -0.0135022 | 30 | 0.1 | False | h18_qwidth_x_h12_median_min30_cap0.1 |
| caution__manual_review_required | 385 | -0.300249 | -0.1 | 30 | 0.1 | False | h18_qwidth_x_h12_median_min30_cap0.1 |
| caution__not_collected_by_h11_h12 | 357 | -0.0795952 | -0.0795952 | 30 | 0.1 | False | h18_qwidth_x_h12_median_min30_cap0.1 |
| risk__candidate_for_h14_h18 | 5 | -0.726555 | 0.0184387 | 30 | 0.1 | True | h18_qwidth_x_h12_median_min30_cap0.1 |
| risk__do_not_use_for_point_prediction | 3 | -0.149027 | 0.0184387 | 30 | 0.1 | True | h18_qwidth_x_h12_median_min30_cap0.1 |
| risk__manual_review_required | 17 | -0.642092 | 0.0184387 | 30 | 0.1 | True | h18_qwidth_x_h12_median_min30_cap0.1 |
| risk__not_collected_by_h11_h12 | 911 | -0.0828196 | -0.0828196 | 30 | 0.1 | False | h18_qwidth_x_h12_median_min30_cap0.1 |
| stable__candidate_for_h14_h18 | 83 | 0.516405 | 0.1 | 30 | 0.1 | False | h18_qwidth_x_h12_median_min30_cap0.1 |
| stable__confidence_only_or_manual_review | 329 | 0.546634 | 0.1 | 30 | 0.1 | False | h18_qwidth_x_h12_median_min30_cap0.1 |
| stable__do_not_use_for_point_prediction | 170 | 0.255711 | 0.1 | 30 | 0.1 | False | h18_qwidth_x_h12_median_min30_cap0.1 |
| stable__manual_review_required | 223 | -0.0985585 | -0.0985585 | 30 | 0.1 | False | h18_qwidth_x_h12_median_min30_cap0.1 |
| stable__not_collected_by_h11_h12 | 104 | 0.276924 | 0.1 | 30 | 0.1 | False | h18_qwidth_x_h12_median_min30_cap0.1 |
| __GLOBAL__ | 2753 | 0.0184387 | 0.0184387 | 30 | 0.1 | False | h18_qwidth_x_h12_median_min30_cap0.1 |
| caution__candidate_for_h14_h18 | 52 | 0.506851 | 0.2 | 30 | 0.2 | False | h18_qwidth_x_h12_median_min30_cap0.2 |
| caution__confidence_only_or_manual_review | 37 | -0.0447311 | -0.0447311 | 30 | 0.2 | False | h18_qwidth_x_h12_median_min30_cap0.2 |
| caution__do_not_use_for_point_prediction | 77 | -0.0135022 | -0.0135022 | 30 | 0.2 | False | h18_qwidth_x_h12_median_min30_cap0.2 |
| caution__manual_review_required | 385 | -0.300249 | -0.2 | 30 | 0.2 | False | h18_qwidth_x_h12_median_min30_cap0.2 |
| caution__not_collected_by_h11_h12 | 357 | -0.0795952 | -0.0795952 | 30 | 0.2 | False | h18_qwidth_x_h12_median_min30_cap0.2 |
| risk__candidate_for_h14_h18 | 5 | -0.726555 | 0.0184387 | 30 | 0.2 | True | h18_qwidth_x_h12_median_min30_cap0.2 |
| risk__do_not_use_for_point_prediction | 3 | -0.149027 | 0.0184387 | 30 | 0.2 | True | h18_qwidth_x_h12_median_min30_cap0.2 |
| risk__manual_review_required | 17 | -0.642092 | 0.0184387 | 30 | 0.2 | True | h18_qwidth_x_h12_median_min30_cap0.2 |
| risk__not_collected_by_h11_h12 | 911 | -0.0828196 | -0.0828196 | 30 | 0.2 | False | h18_qwidth_x_h12_median_min30_cap0.2 |
| stable__candidate_for_h14_h18 | 83 | 0.516405 | 0.2 | 30 | 0.2 | False | h18_qwidth_x_h12_median_min30_cap0.2 |
| stable__confidence_only_or_manual_review | 329 | 0.546634 | 0.2 | 30 | 0.2 | False | h18_qwidth_x_h12_median_min30_cap0.2 |
| stable__do_not_use_for_point_prediction | 170 | 0.255711 | 0.2 | 30 | 0.2 | False | h18_qwidth_x_h12_median_min30_cap0.2 |
| stable__manual_review_required | 223 | -0.0985585 | -0.0985585 | 30 | 0.2 | False | h18_qwidth_x_h12_median_min30_cap0.2 |
| stable__not_collected_by_h11_h12 | 104 | 0.276924 | 0.2 | 30 | 0.2 | False | h18_qwidth_x_h12_median_min30_cap0.2 |
| __GLOBAL__ | 2753 | 0.0184387 | 0.0184387 | 30 | 0.2 | False | h18_qwidth_x_h12_median_min30_cap0.2 |
| caution__candidate_for_h14_h18 | 52 | 0.506851 | 0.3 | 30 | 0.3 | False | h18_qwidth_x_h12_median_min30_cap0.3 |
| caution__confidence_only_or_manual_review | 37 | -0.0447311 | -0.0447311 | 30 | 0.3 | False | h18_qwidth_x_h12_median_min30_cap0.3 |
| caution__do_not_use_for_point_prediction | 77 | -0.0135022 | -0.0135022 | 30 | 0.3 | False | h18_qwidth_x_h12_median_min30_cap0.3 |
| caution__manual_review_required | 385 | -0.300249 | -0.3 | 30 | 0.3 | False | h18_qwidth_x_h12_median_min30_cap0.3 |
| caution__not_collected_by_h11_h12 | 357 | -0.0795952 | -0.0795952 | 30 | 0.3 | False | h18_qwidth_x_h12_median_min30_cap0.3 |
| risk__candidate_for_h14_h18 | 5 | -0.726555 | 0.0184387 | 30 | 0.3 | True | h18_qwidth_x_h12_median_min30_cap0.3 |
| risk__do_not_use_for_point_prediction | 3 | -0.149027 | 0.0184387 | 30 | 0.3 | True | h18_qwidth_x_h12_median_min30_cap0.3 |
| risk__manual_review_required | 17 | -0.642092 | 0.0184387 | 30 | 0.3 | True | h18_qwidth_x_h12_median_min30_cap0.3 |
| risk__not_collected_by_h11_h12 | 911 | -0.0828196 | -0.0828196 | 30 | 0.3 | False | h18_qwidth_x_h12_median_min30_cap0.3 |
| stable__candidate_for_h14_h18 | 83 | 0.516405 | 0.3 | 30 | 0.3 | False | h18_qwidth_x_h12_median_min30_cap0.3 |
| stable__confidence_only_or_manual_review | 329 | 0.546634 | 0.3 | 30 | 0.3 | False | h18_qwidth_x_h12_median_min30_cap0.3 |
| stable__do_not_use_for_point_prediction | 170 | 0.255711 | 0.255711 | 30 | 0.3 | False | h18_qwidth_x_h12_median_min30_cap0.3 |
| stable__manual_review_required | 223 | -0.0985585 | -0.0985585 | 30 | 0.3 | False | h18_qwidth_x_h12_median_min30_cap0.3 |
| stable__not_collected_by_h11_h12 | 104 | 0.276924 | 0.276924 | 30 | 0.3 | False | h18_qwidth_x_h12_median_min30_cap0.3 |
| __GLOBAL__ | 2753 | 0.0184387 | 0.0184387 | 30 | 0.3 | False | h18_qwidth_x_h12_median_min30_cap0.3 |
| caution__candidate_for_h14_h18 | 52 | 0.506851 | 0.0184387 | 80 | 0.1 | True | h18_qwidth_x_h12_median_min80_cap0.1 |
| caution__confidence_only_or_manual_review | 37 | -0.0447311 | 0.0184387 | 80 | 0.1 | True | h18_qwidth_x_h12_median_min80_cap0.1 |
| caution__do_not_use_for_point_prediction | 77 | -0.0135022 | 0.0184387 | 80 | 0.1 | True | h18_qwidth_x_h12_median_min80_cap0.1 |
| caution__manual_review_required | 385 | -0.300249 | -0.1 | 80 | 0.1 | False | h18_qwidth_x_h12_median_min80_cap0.1 |
| caution__not_collected_by_h11_h12 | 357 | -0.0795952 | -0.0795952 | 80 | 0.1 | False | h18_qwidth_x_h12_median_min80_cap0.1 |
| risk__candidate_for_h14_h18 | 5 | -0.726555 | 0.0184387 | 80 | 0.1 | True | h18_qwidth_x_h12_median_min80_cap0.1 |
| risk__do_not_use_for_point_prediction | 3 | -0.149027 | 0.0184387 | 80 | 0.1 | True | h18_qwidth_x_h12_median_min80_cap0.1 |
| risk__manual_review_required | 17 | -0.642092 | 0.0184387 | 80 | 0.1 | True | h18_qwidth_x_h12_median_min80_cap0.1 |
| risk__not_collected_by_h11_h12 | 911 | -0.0828196 | -0.0828196 | 80 | 0.1 | False | h18_qwidth_x_h12_median_min80_cap0.1 |
| stable__candidate_for_h14_h18 | 83 | 0.516405 | 0.1 | 80 | 0.1 | False | h18_qwidth_x_h12_median_min80_cap0.1 |
| stable__confidence_only_or_manual_review | 329 | 0.546634 | 0.1 | 80 | 0.1 | False | h18_qwidth_x_h12_median_min80_cap0.1 |
| stable__do_not_use_for_point_prediction | 170 | 0.255711 | 0.1 | 80 | 0.1 | False | h18_qwidth_x_h12_median_min80_cap0.1 |
| stable__manual_review_required | 223 | -0.0985585 | -0.0985585 | 80 | 0.1 | False | h18_qwidth_x_h12_median_min80_cap0.1 |
| stable__not_collected_by_h11_h12 | 104 | 0.276924 | 0.1 | 80 | 0.1 | False | h18_qwidth_x_h12_median_min80_cap0.1 |
| __GLOBAL__ | 2753 | 0.0184387 | 0.0184387 | 80 | 0.1 | False | h18_qwidth_x_h12_median_min80_cap0.1 |

## Conformal 범위 버퍼

| confidence_grade | target_coverage | n_validation | conformal_buffer_log | used_global_fallback | candidate |
| --- | --- | --- | --- | --- | --- |
| low | 0.8 | 2289 | 0.249223 | False | h14_conformal80_range |
| medium | 0.8 | 464 | 0.613751 | False | h14_conformal80_range |
| __GLOBAL__ | 0.8 | 2753 | 0.373755 | False | h14_conformal80_range |
| low | 0.9 | 2289 | 0.463359 | False | h14_conformal90_range |
| medium | 0.9 | 464 | 0.760839 | False | h14_conformal90_range |
| __GLOBAL__ | 0.9 | 2753 | 0.566509 | False | h14_conformal90_range |

## 해석

- H14의 핵심은 range coverage가 오르면서 median range ratio가 과도하게 커지지 않는지다.
- H18의 핵심은 validation에서 만든 q-width x H12 action 보정이 test에서 MdAPE/MAPE/p95를 동시에 악화시키지 않는지다.
- H12가 아직 수동 검수 전 자동 라벨이므로, 이 결과는 운영 정책 후보 검증으로 보고 최종 모델 채택 근거로는 보류한다.
