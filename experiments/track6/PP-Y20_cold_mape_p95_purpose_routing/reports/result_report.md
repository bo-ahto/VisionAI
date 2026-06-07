# PP-Y20 Cold MAPE/p95 목적별 라우팅 결합

- 목적: Cold 후속 실험에서 남은 validation 고정/재현성 gap을 닫는다.
- 원칙: test 결과만 보고 후보를 새로 고르지 않고, validation/OOF 또는 bootstrap 근거를 함께 기록한다.

## Test 결과 상위

| 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---:|---:|---:|---:|
| `component_pp_y16_p95_pred` | `purpose_routing_component` | 0.4382 | 1.0981 | 3.3512 | 0.8700 |
| `component_pp_y2_pred` | `purpose_routing_component` | 0.4421 | 1.0484 | 3.3537 | 0.8567 |
| `component_pp_y16_defensive_pred` | `purpose_routing_component` | 0.4438 | 1.1083 | 2.8025 | 0.8905 |
| `route_y2_w4_y16_qwidth_1.092_1.420` | `mape_p95_purpose_routing` | 0.4478 | 1.0740 | 3.9034 | 0.8914 |
| `route_y2_w4_y16_qwidth_0.735_1.092` | `mape_p95_purpose_routing` | 0.4494 | 1.0552 | 3.6483 | 0.8956 |
| `purpose_fixed_validation_p95_guarded` | `mape_p95_purpose_routing_fixed` | 0.4494 | 1.0552 | 3.6483 | 0.8956 |
| `route_y2_w4_y16_qwidth_0.735_1.420` | `mape_p95_purpose_routing` | 0.4603 | 1.0783 | 3.8973 | 0.8982 |
| `purpose_fixed_validation_best_mdape` | `mape_p95_purpose_routing_fixed` | 0.4603 | 1.0783 | 3.8973 | 0.8982 |
| `purpose_fixed_validation_mape_guarded` | `mape_p95_purpose_routing_fixed` | 0.4603 | 1.0783 | 3.8973 | 0.8982 |
| `purpose_fixed_validation_balanced_rank` | `mape_p95_purpose_routing_fixed` | 0.4603 | 1.0783 | 3.8973 | 0.8982 |
| `route_y2_w4_y16_qwidth_1.420_1.861` | `mape_p95_purpose_routing` | 0.4622 | 1.0994 | 3.9039 | 0.8879 |
| `route_y2_w4_y16_qwidth_1.092_1.861` | `mape_p95_purpose_routing` | 0.4669 | 1.1062 | 4.0103 | 0.8974 |
| `component_pp_w4_mape_pred` | `purpose_routing_component` | 0.4766 | 1.0847 | 3.0322 | 0.8907 |
| `route_y2_w4_y16_qwidth_0.735_1.861` | `mape_p95_purpose_routing` | 0.4767 | 1.1105 | 3.9941 | 0.9042 |

## Map / Bootstrap

| experiment_id | candidate | low_threshold | high_threshold | rule | selector | source_candidate | validation_MdAPE | validation_MAPE | validation_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-Y20 | route_y2_w4_y16_qwidth_0.735_1.092 | 0.734942 | 1.09246 | qwidth<=low: PP-Y2, low<qwidth<=high: PP-W4, qwidth>high: PP-Y16 defensive |  |  |  |  |  |
| PP-Y20 | route_y2_w4_y16_qwidth_0.735_1.420 | 0.734942 | 1.42027 | qwidth<=low: PP-Y2, low<qwidth<=high: PP-W4, qwidth>high: PP-Y16 defensive |  |  |  |  |  |
| PP-Y20 | route_y2_w4_y16_qwidth_0.735_1.861 | 0.734942 | 1.86073 | qwidth<=low: PP-Y2, low<qwidth<=high: PP-W4, qwidth>high: PP-Y16 defensive |  |  |  |  |  |
| PP-Y20 | route_y2_w4_y16_qwidth_1.092_1.420 | 1.09246 | 1.42027 | qwidth<=low: PP-Y2, low<qwidth<=high: PP-W4, qwidth>high: PP-Y16 defensive |  |  |  |  |  |
| PP-Y20 | route_y2_w4_y16_qwidth_1.092_1.861 | 1.09246 | 1.86073 | qwidth<=low: PP-Y2, low<qwidth<=high: PP-W4, qwidth>high: PP-Y16 defensive |  |  |  |  |  |
| PP-Y20 | route_y2_w4_y16_qwidth_1.420_1.861 | 1.42027 | 1.86073 | qwidth<=low: PP-Y2, low<qwidth<=high: PP-W4, qwidth>high: PP-Y16 defensive |  |  |  |  |  |
| PP-Y20 | purpose_fixed_validation_best_mdape |  |  |  | validation_best_mdape | route_y2_w4_y16_qwidth_0.735_1.420 | 0.357784 | 0.515428 | 1.41292 |
| PP-Y20 | purpose_fixed_validation_mape_guarded |  |  |  | validation_mape_guarded | route_y2_w4_y16_qwidth_0.735_1.420 | 0.357784 | 0.515428 | 1.41292 |
| PP-Y20 | purpose_fixed_validation_p95_guarded |  |  |  | validation_p95_guarded | route_y2_w4_y16_qwidth_0.735_1.092 | 0.366512 | 0.517751 | 1.36927 |
| PP-Y20 | purpose_fixed_validation_balanced_rank |  |  |  | validation_balanced_rank | route_y2_w4_y16_qwidth_0.735_1.420 | 0.357784 | 0.515428 | 1.41292 |
