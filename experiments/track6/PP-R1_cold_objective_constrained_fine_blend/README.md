# PP-R1 Cold 목적 제약 fine blend

- 목적: PP-Q 이후 남은 개선 여지를 모델 조합, 단계 보정, 라우팅, 메타 보정으로 확인한다.
- 기준: 가중치, 보정값, threshold, meta 모델은 validation에서만 정하고 test에는 그대로 적용한다.

## Metrics

| 후보 | scope | split | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---|---:|---:|---:|---:|
| `component_p2_width_routing` | `cold` | `test` | `fine_blend_component` | `0.4779` | `1.3428` | `4.3466` | `0.9522` |
| `component_q2_mape_blend` | `cold` | `test` | `fine_blend_component` | `0.4811` | `1.1797` | `3.7925` | `0.9236` |
| `component_n2_catboost_quantile` | `cold` | `test` | `fine_blend_component` | `0.4830` | `1.1514` | `4.2659` | `0.9161` |
| `fine_blend_mdape` | `cold` | `test` | `objective_constrained_fine_blend` | `0.4894` | `1.3204` | `3.7911` | `0.9610` |
| `component_baseline_lgb` | `cold` | `test` | `fine_blend_component` | `0.4909` | `1.4131` | `4.8212` | `0.9687` |
| `fine_blend_p95_guarded` | `cold` | `test` | `objective_constrained_fine_blend` | `0.4924` | `1.2526` | `3.7970` | `0.9457` |
| `fine_blend_mape_guarded` | `cold` | `test` | `objective_constrained_fine_blend` | `0.5030` | `1.3431` | `3.7937` | `0.9724` |
| `component_a7_hierarchical` | `cold` | `test` | `fine_blend_component` | `0.5093` | `1.4160` | `3.6424` | `0.9936` |
| `fine_blend_mdape` | `cold` | `validation` | `objective_constrained_fine_blend` | `0.3448` | `0.5754` | `1.7141` | `0.6472` |
| `fine_blend_mape_guarded` | `cold` | `validation` | `objective_constrained_fine_blend` | `0.3555` | `0.5625` | `1.6251` | `0.6495` |
| `component_a7_hierarchical` | `cold` | `validation` | `fine_blend_component` | `0.3567` | `0.5662` | `1.6593` | `0.6616` |
| `fine_blend_p95_guarded` | `cold` | `validation` | `objective_constrained_fine_blend` | `0.3652` | `0.5759` | `1.5542` | `0.6480` |
| `component_baseline_lgb` | `cold` | `validation` | `fine_blend_component` | `0.3851` | `0.7169` | `2.0250` | `0.6901` |
| `component_p2_width_routing` | `cold` | `validation` | `fine_blend_component` | `0.3875` | `0.6737` | `1.8166` | `0.6786` |
| `component_q2_mape_blend` | `cold` | `validation` | `fine_blend_component` | `0.3974` | `0.6293` | `1.7765` | `0.6710` |
| `component_n2_catboost_quantile` | `cold` | `validation` | `fine_blend_component` | `0.4087` | `0.6591` | `2.0189` | `0.6893` |
