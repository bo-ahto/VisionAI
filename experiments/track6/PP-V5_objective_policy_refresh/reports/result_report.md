# PP-V5 Warm/Cold 목적별 정책 재정리

- 목적: 종합 보고서에서 남은 후속 후보를 기존 조합 구조에 넣어 추가 개선 여부를 확인한다.
- 선택 기준: validation에서 조합/정책을 정하고 test에서 재현성을 확인한다.

## Test 결과 상위

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `cold` | `component_pp_s1_mdape` | `policy_component` | 0.4744 | 1.2095 | 3.4731 | 0.9301 |
| `cold` | `component_pp_s1_p95` | `policy_component` | 0.4765 | 1.2067 | 3.2824 | 0.9386 |
| `cold` | `component_pp_s4_huber` | `policy_component` | 0.4765 | 1.2079 | 3.2827 | 0.9409 |
| `cold` | `component_pp_v4_huber` | `policy_component` | 0.4771 | 1.2207 | 3.6200 | 0.9457 |
| `cold` | `cold_policy_mdape_first` | `objective_policy_refresh` | 0.4771 | 1.2207 | 3.6200 | 0.9457 |
| `cold` | `component_pp_v3_p95` | `policy_component` | 0.4771 | 1.2073 | 3.4092 | 0.9396 |
| `cold` | `cold_policy_p95_guarded` | `objective_policy_refresh` | 0.4771 | 1.2073 | 3.4092 | 0.9396 |
| `cold` | `component_pp_v3_mape` | `policy_component` | 0.4796 | 1.2148 | 3.4131 | 0.9436 |
| `cold` | `cold_policy_mape_guarded` | `objective_policy_refresh` | 0.4796 | 1.2148 | 3.4131 | 0.9436 |
| `cold` | `component_pp_q2_mape` | `policy_component` | 0.4811 | 1.1797 | 3.7925 | 0.9236 |
| `warm` | `component_pp_t1_mape` | `policy_component` | 0.1621 | 0.3044 | 1.0335 | 0.4220 |
| `warm` | `component_pp_v1_mape` | `policy_component` | 0.1621 | 0.3044 | 1.0335 | 0.4220 |
| `warm` | `component_pp_t1_mdape` | `policy_component` | 0.1668 | 0.3067 | 0.9580 | 0.4241 |
| `warm` | `warm_policy_mdape_first` | `objective_policy_refresh` | 0.1668 | 0.3067 | 0.9580 | 0.4241 |
| `warm` | `component_pp_v2_huber` | `policy_component` | 0.1680 | 0.2873 | 0.9287 | 0.4102 |
| `warm` | `component_pp_v1_p95` | `policy_component` | 0.1695 | 0.3168 | 1.0674 | 0.4399 |
| `warm` | `warm_policy_p95_guarded` | `objective_policy_refresh` | 0.1695 | 0.3168 | 1.0674 | 0.4399 |
| `warm` | `component_pp_t2_huber` | `policy_component` | 0.1705 | 0.2916 | 0.9582 | 0.4098 |
| `warm` | `warm_policy_mape_guarded` | `objective_policy_refresh` | 0.1705 | 0.2916 | 0.9582 | 0.4098 |

## 선택/가중치 맵

| experiment_id | scope | objective | selected_label | validation_RMSE_log | validation_MdAPE | validation_MAPE | validation_p95_APE | validation_Within_30 | validation_Within_50 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-V5 | warm | mdape_first | pp_t1_mdape | 0.399277 | 0.149528 | 0.268022 | 0.815347 | 0.73025 | 0.868979 |
| PP-V5 | warm | mape_guarded | pp_t2_huber | 0.377425 | 0.156378 | 0.260976 | 0.807969 | 0.728324 | 0.88632 |
| PP-V5 | warm | p95_guarded | pp_v1_p95 | 0.395339 | 0.154797 | 0.271071 | 0.786373 | 0.722543 | 0.868979 |
| PP-V5 | cold | mdape_first | pp_v4_huber | 0.630319 | 0.352335 | 0.544065 | 1.54379 | 0.430076 | 0.667272 |
| PP-V5 | cold | mape_guarded | pp_v3_mape | 0.637386 | 0.354967 | 0.541622 | 1.52918 | 0.429713 | 0.667635 |
| PP-V5 | cold | p95_guarded | pp_v3_p95 | 0.637146 | 0.360209 | 0.546665 | 1.52284 | 0.421722 | 0.652742 |
