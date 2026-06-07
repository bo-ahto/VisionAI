# PP-Y10 Cold 불확실성 폭 기반 모델 선택

- 목적: Cold 가격 예측에서 피처 조합과 모델 순서 변경으로 추가 개선 가능성을 확인한다.
- 기준: 기존 Track6 split을 고정하고 validation에서 후보를 비교한 뒤 test 결과를 함께 기록한다.

## Test 결과 상위

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 정책 |
|---|---:|---:|---:|---:|---|
| `route_lgbq_meta_external_interaction_to_h9_search_p95_qwidth_le_1.454` | 0.4302 | 1.0551 | 3.1004 | 0.8591 | `uncertainty_width_routing` |
| `route_lgbq_meta_external_interaction_to_h9_search_p95_qwidth_le_1.779` | 0.4308 | 1.0545 | 3.1209 | 0.8586 | `uncertainty_width_routing` |
| `route_lgbq_meta_external_core_to_h9_search_p95_qwidth_le_1.760` | 0.4374 | 1.1097 | 2.9955 | 0.8708 | `uncertainty_width_routing` |
| `route_lgbq_meta_external_core_to_h9_search_p95_qwidth_le_1.602` | 0.4386 | 1.1076 | 2.9955 | 0.8694 | `uncertainty_width_routing` |
| `route_lgbq_meta_external_interaction_to_w4_p95_qwidth_le_1.779` | 0.4437 | 1.0675 | 3.1120 | 0.8789 | `uncertainty_width_routing` |
| `route_lgbq_search_all_external_interaction_to_w4_p95_qwidth_le_1.861` | 0.4460 | 1.0489 | 2.9656 | 0.8606 | `uncertainty_width_routing` |
| `route_lgbq_search_all_external_interaction_to_h9_search_p95_qwidth_le_1.861` | 0.4464 | 1.0455 | 2.9954 | 0.8574 | `uncertainty_width_routing` |
| `route_lgbq_meta_external_core_to_w4_p95_qwidth_le_1.760` | 0.4473 | 1.1235 | 2.9874 | 0.8929 | `uncertainty_width_routing` |
| `route_lgbq_meta_external_core_to_h9_search_p95_qwidth_le_1.242` | 0.4486 | 1.0979 | 2.9955 | 0.8686 | `uncertainty_width_routing` |
| `route_lgbq_meta_external_interaction_to_w4_p95_qwidth_le_1.454` | 0.4508 | 1.0735 | 3.1120 | 0.8827 | `uncertainty_width_routing` |
| `route_lgbq_meta_external_interaction_to_h9_search_p95_qwidth_le_1.072` | 0.4509 | 1.0674 | 3.1004 | 0.8673 | `uncertainty_width_routing` |
| `route_lgbq_meta_external_core_to_w4_p95_qwidth_le_1.602` | 0.4510 | 1.1249 | 2.9874 | 0.8917 | `uncertainty_width_routing` |
| `route_lgbq_search_all_external_interaction_to_h9_search_p95_qwidth_le_1.092` | 0.4549 | 1.0566 | 2.9954 | 0.8644 | `uncertainty_width_routing` |
| `route_lgbq_search_all_external_interaction_to_h9_search_p95_qwidth_le_1.420` | 0.4573 | 1.0553 | 2.9954 | 0.8623 | `uncertainty_width_routing` |
| `route_lgbq_search_all_external_interaction_to_w4_p95_qwidth_le_1.420` | 0.4602 | 1.0675 | 2.9720 | 0.8740 | `uncertainty_width_routing` |
| `route_lgbq_search_all_external_interaction_to_h9_search_p95_qwidth_le_0.735` | 0.4620 | 1.0369 | 2.9954 | 0.8628 | `uncertainty_width_routing` |
| `route_lgbq_meta_external_core_to_w4_p95_qwidth_le_1.242` | 0.4631 | 1.1283 | 2.9874 | 0.8936 | `uncertainty_width_routing` |
| `route_lgbq_meta_external_interaction_to_w4_p95_qwidth_le_1.072` | 0.4635 | 1.0930 | 3.1316 | 0.8901 | `uncertainty_width_routing` |
| `route_lgbq_search_all_external_interaction_to_w4_p95_qwidth_le_1.092` | 0.4658 | 1.0742 | 2.9720 | 0.8836 | `uncertainty_width_routing` |
| `route_lgbq_meta_external_interaction_to_w4_p95_qwidth_le_0.772` | 0.4660 | 1.0995 | 3.1702 | 0.8933 | `uncertainty_width_routing` |

## 설정/피처 맵

| experiment_id | candidate | stable_source | risk_source | threshold | rule |
| --- | --- | --- | --- | --- | --- |
| PP-Y10 | route_lgbq_search_all_external_interaction_to_h9_search_p95_qwidth_le_0.735 | lgbq_search_all_external_interaction | h9_search_p95 | 0.734942 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_search_all_external_interaction_to_h9_search_p95_qwidth_le_1.092 | lgbq_search_all_external_interaction | h9_search_p95 | 1.09246 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_search_all_external_interaction_to_h9_search_p95_qwidth_le_1.420 | lgbq_search_all_external_interaction | h9_search_p95 | 1.42027 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_search_all_external_interaction_to_h9_search_p95_qwidth_le_1.861 | lgbq_search_all_external_interaction | h9_search_p95 | 1.86073 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_search_all_external_interaction_to_w4_p95_qwidth_le_0.735 | lgbq_search_all_external_interaction | w4_p95 | 0.734942 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_search_all_external_interaction_to_w4_p95_qwidth_le_1.092 | lgbq_search_all_external_interaction | w4_p95 | 1.09246 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_search_all_external_interaction_to_w4_p95_qwidth_le_1.420 | lgbq_search_all_external_interaction | w4_p95 | 1.42027 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_search_all_external_interaction_to_w4_p95_qwidth_le_1.861 | lgbq_search_all_external_interaction | w4_p95 | 1.86073 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_search_all_external_core_to_h9_search_p95_qwidth_le_0.782 | lgbq_search_all_external_core | h9_search_p95 | 0.782471 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_search_all_external_core_to_h9_search_p95_qwidth_le_1.068 | lgbq_search_all_external_core | h9_search_p95 | 1.0681 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_search_all_external_core_to_h9_search_p95_qwidth_le_1.396 | lgbq_search_all_external_core | h9_search_p95 | 1.3963 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_search_all_external_core_to_h9_search_p95_qwidth_le_1.864 | lgbq_search_all_external_core | h9_search_p95 | 1.86419 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_search_all_external_core_to_w4_p95_qwidth_le_0.782 | lgbq_search_all_external_core | w4_p95 | 0.782471 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_search_all_external_core_to_w4_p95_qwidth_le_1.068 | lgbq_search_all_external_core | w4_p95 | 1.0681 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_search_all_external_core_to_w4_p95_qwidth_le_1.396 | lgbq_search_all_external_core | w4_p95 | 1.3963 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_search_all_external_core_to_w4_p95_qwidth_le_1.864 | lgbq_search_all_external_core | w4_p95 | 1.86419 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_meta_external_interaction_to_h9_search_p95_qwidth_le_0.772 | lgbq_meta_external_interaction | h9_search_p95 | 0.772379 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_meta_external_interaction_to_h9_search_p95_qwidth_le_1.072 | lgbq_meta_external_interaction | h9_search_p95 | 1.07153 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_meta_external_interaction_to_h9_search_p95_qwidth_le_1.454 | lgbq_meta_external_interaction | h9_search_p95 | 1.4542 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_meta_external_interaction_to_h9_search_p95_qwidth_le_1.779 | lgbq_meta_external_interaction | h9_search_p95 | 1.77874 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_meta_external_interaction_to_w4_p95_qwidth_le_0.772 | lgbq_meta_external_interaction | w4_p95 | 0.772379 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_meta_external_interaction_to_w4_p95_qwidth_le_1.072 | lgbq_meta_external_interaction | w4_p95 | 1.07153 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_meta_external_interaction_to_w4_p95_qwidth_le_1.454 | lgbq_meta_external_interaction | w4_p95 | 1.4542 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_meta_external_interaction_to_w4_p95_qwidth_le_1.779 | lgbq_meta_external_interaction | w4_p95 | 1.77874 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_meta_external_core_to_h9_search_p95_qwidth_le_0.880 | lgbq_meta_external_core | h9_search_p95 | 0.879734 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_meta_external_core_to_h9_search_p95_qwidth_le_1.242 | lgbq_meta_external_core | h9_search_p95 | 1.24218 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_meta_external_core_to_h9_search_p95_qwidth_le_1.602 | lgbq_meta_external_core | h9_search_p95 | 1.60174 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_meta_external_core_to_h9_search_p95_qwidth_le_1.760 | lgbq_meta_external_core | h9_search_p95 | 1.75978 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_meta_external_core_to_w4_p95_qwidth_le_0.880 | lgbq_meta_external_core | w4_p95 | 0.879734 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_meta_external_core_to_w4_p95_qwidth_le_1.242 | lgbq_meta_external_core | w4_p95 | 1.24218 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_meta_external_core_to_w4_p95_qwidth_le_1.602 | lgbq_meta_external_core | w4_p95 | 1.60174 | use stable model when quantile_width_log <= threshold, otherwise risk model |
| PP-Y10 | route_lgbq_meta_external_core_to_w4_p95_qwidth_le_1.760 | lgbq_meta_external_core | w4_p95 | 1.75978 | use stable model when quantile_width_log <= threshold, otherwise risk model |
