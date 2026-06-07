# PP-Y17 Cold PP-Y10 validation 고정 라우팅 재검증

- 목적: Cold 후속 실험에서 남은 validation 고정/재현성 gap을 닫는다.
- 원칙: test 결과만 보고 후보를 새로 고르지 않고, validation/OOF 또는 bootstrap 근거를 함께 기록한다.

## Test 결과 상위

| 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---:|---:|---:|---:|
| `y10_fixed_validation_p95_guarded` | `y10_validation_fixed_routing` | 0.4620 | 1.0369 | 2.9954 | 0.8628 |
| `y10_fixed_validation_best_mdape` | `y10_validation_fixed_routing` | 0.4763 | 1.0786 | 3.0322 | 0.8905 |
| `y10_fixed_validation_mape_guarded` | `y10_validation_fixed_routing` | 0.4763 | 1.0786 | 3.0322 | 0.8905 |
| `y10_fixed_validation_balanced_rank` | `y10_validation_fixed_routing` | 0.4763 | 1.0786 | 3.0322 | 0.8905 |

## Map / Bootstrap

| experiment_id | selector | source_candidate | stable_source | risk_source | threshold | validation_MdAPE | validation_MAPE | validation_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-Y17 | validation_best_mdape | route_lgbq_search_all_external_interaction_to_w4_p95_qwidth_le_0.735 | lgbq_search_all_external_interaction | w4_p95 | 0.734942 | 0.373591 | 0.537024 | 1.4454 |
| PP-Y17 | validation_mape_guarded | route_lgbq_search_all_external_interaction_to_w4_p95_qwidth_le_0.735 | lgbq_search_all_external_interaction | w4_p95 | 0.734942 | 0.373591 | 0.537024 | 1.4454 |
| PP-Y17 | validation_p95_guarded | route_lgbq_search_all_external_interaction_to_h9_search_p95_qwidth_le_0.735 | lgbq_search_all_external_interaction | h9_search_p95 | 0.734942 | 0.386726 | 0.554736 | 1.4077 |
| PP-Y17 | validation_balanced_rank | route_lgbq_search_all_external_interaction_to_w4_p95_qwidth_le_0.735 | lgbq_search_all_external_interaction | w4_p95 | 0.734942 | 0.373591 | 0.537024 | 1.4454 |
