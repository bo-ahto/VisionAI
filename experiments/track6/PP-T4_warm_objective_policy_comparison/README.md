# PP-T4 Warm 목적별 최종 정책 비교

- 목적: Warm 최종 후보 PP-R5 이후에도 조합, 메타 보정, 2차 residual 안정화로 개선 여지가 있는지 확인한다.
- 기준: 가중치, meta 모델, 보정값, 정책 선택은 validation에서 정하고 test에는 그대로 적용한다.

| 후보 | split | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `component_pp_t1_mape` | `test` | `policy_component` | `0.1621` | `0.3044` | `1.0335` | `0.4220` |
| `component_pp_t3_mdape` | `test` | `policy_component` | `0.1644` | `0.3258` | `1.1109` | `0.4382` |
| `component_pp_t3_p95` | `test` | `policy_component` | `0.1667` | `0.3266` | `1.1109` | `0.4381` |
| `component_pp_t1_mdape` | `test` | `policy_component` | `0.1668` | `0.3067` | `0.9580` | `0.4241` |
| `policy_mdape_first` | `test` | `warm_objective_policy_selection` | `0.1668` | `0.3067` | `0.9580` | `0.4241` |
| `component_pp_t3_mape` | `test` | `policy_component` | `0.1690` | `0.3274` | `1.0878` | `0.4386` |
| `component_pp_t1_p95` | `test` | `policy_component` | `0.1695` | `0.3168` | `1.0674` | `0.4399` |
| `policy_p95_guarded` | `test` | `warm_objective_policy_selection` | `0.1695` | `0.3168` | `1.0674` | `0.4399` |
| `component_pp_t2_huber` | `test` | `policy_component` | `0.1705` | `0.2916` | `0.9582` | `0.4098` |
| `policy_mape_guarded` | `test` | `warm_objective_policy_selection` | `0.1705` | `0.2916` | `0.9582` | `0.4098` |
| `component_pp_r5_p95` | `test` | `policy_component` | `0.1707` | `0.3278` | `1.1107` | `0.4381` |
| `component_pp_r5_mape` | `test` | `policy_component` | `0.1713` | `0.3271` | `1.1069` | `0.4382` |
| `component_pp_t2_ridge10` | `test` | `policy_component` | `0.1868` | `0.3000` | `0.9970` | `0.4147` |
| `component_pp_t1_mdape` | `validation` | `policy_component` | `0.1495` | `0.2680` | `0.8153` | `0.3993` |
| `policy_mdape_first` | `validation` | `warm_objective_policy_selection` | `0.1495` | `0.2680` | `0.8153` | `0.3993` |
| `component_pp_t1_mape` | `validation` | `policy_component` | `0.1540` | `0.2660` | `0.8047` | `0.3920` |
| `component_pp_t1_p95` | `validation` | `policy_component` | `0.1548` | `0.2711` | `0.7864` | `0.3953` |
| `policy_p95_guarded` | `validation` | `warm_objective_policy_selection` | `0.1548` | `0.2711` | `0.7864` | `0.3953` |
| `component_pp_t2_huber` | `validation` | `policy_component` | `0.1564` | `0.2610` | `0.8080` | `0.3774` |
| `policy_mape_guarded` | `validation` | `warm_objective_policy_selection` | `0.1564` | `0.2610` | `0.8080` | `0.3774` |
| `component_pp_t2_ridge10` | `validation` | `policy_component` | `0.1569` | `0.2648` | `0.8149` | `0.3763` |
| `component_pp_t3_mdape` | `validation` | `policy_component` | `0.1645` | `0.2990` | `0.9218` | `0.4401` |
| `component_pp_t3_p95` | `validation` | `policy_component` | `0.1648` | `0.3001` | `0.9218` | `0.4404` |
| `component_pp_t3_mape` | `validation` | `policy_component` | `0.1659` | `0.2975` | `0.9457` | `0.4387` |
| `component_pp_r5_mape` | `validation` | `policy_component` | `0.1688` | `0.2992` | `0.9268` | `0.4405` |
| `component_pp_r5_p95` | `validation` | `policy_component` | `0.1710` | `0.3021` | `0.9268` | `0.4418` |
