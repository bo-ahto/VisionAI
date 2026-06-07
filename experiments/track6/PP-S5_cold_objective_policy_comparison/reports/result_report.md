# PP-S5 Cold 목적별 최종 정책 비교

- 목적: 모델 순서 변경, 목적함수 커스텀, 메타 조합이 기존 PP-Q/PP-R 이후 추가 개선을 주는지 확인한다.
- 근거: CatBoost/LightGBM의 MAPE/Quantile/Huber 목적함수와 stacking의 모델 출력값 결합 구조를 Track6 후보에 적용한다.
- 기준: 가중치, residual 모델, meta 모델, 정책 선택은 validation에서 정하고 test에는 그대로 적용한다.

## Metrics

| 후보 | split | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `component_pp_s1_catboost_huber_mdape` | `test` | `policy_component` | `0.4744` | `1.2095` | `3.4731` | `0.9301` |
| `component_pp_s1_catboost_huber_p95` | `test` | `policy_component` | `0.4765` | `1.2067` | `3.2824` | `0.9386` |
| `component_pp_s2_quantile_huber` | `test` | `policy_component` | `0.4765` | `1.2453` | `3.5543` | `0.9451` |
| `policy_mdape_first` | `test` | `objective_policy_selection` | `0.4765` | `1.2453` | `3.5543` | `0.9451` |
| `component_pp_s4_crossfit_huber` | `test` | `policy_component` | `0.4765` | `1.2079` | `3.2827` | `0.9409` |
| `component_pp_s3_lgbm_huber` | `test` | `policy_component` | `0.4768` | `1.2784` | `4.3209` | `0.9435` |
| `component_pp_p2_mdape` | `test` | `policy_component` | `0.4779` | `1.3428` | `4.3466` | `0.9522` |
| `component_pp_s2_quantile_catboost` | `test` | `policy_component` | `0.4783` | `1.2760` | `3.9859` | `0.9393` |
| `component_pp_r4_p95` | `test` | `policy_component` | `0.4796` | `1.2148` | `3.4131` | `0.9436` |
| `policy_mape_guarded` | `test` | `objective_policy_selection` | `0.4796` | `1.2148` | `3.4131` | `0.9436` |
| `policy_p95_guarded` | `test` | `objective_policy_selection` | `0.4796` | `1.2148` | `3.4131` | `0.9436` |
| `component_pp_s1_catboost_huber_mape` | `test` | `policy_component` | `0.4808` | `1.1716` | `3.6074` | `0.9236` |
| `component_pp_q2_mape` | `test` | `policy_component` | `0.4811` | `1.1797` | `3.7925` | `0.9236` |
| `component_pp_s3_lgbm_mape` | `test` | `policy_component` | `0.4825` | `1.2217` | `3.7901` | `0.9422` |
| `component_pp_s2_quantile_huber` | `validation` | `policy_component` | `0.3528` | `0.5759` | `1.7203` | `0.6476` |
| `policy_mdape_first` | `validation` | `objective_policy_selection` | `0.3528` | `0.5759` | `1.7203` | `0.6476` |
| `component_pp_s4_crossfit_huber` | `validation` | `policy_component` | `0.3547` | `0.5462` | `1.5559` | `0.6399` |
| `component_pp_r4_p95` | `validation` | `policy_component` | `0.3550` | `0.5416` | `1.5292` | `0.6374` |
| `policy_mape_guarded` | `validation` | `objective_policy_selection` | `0.3550` | `0.5416` | `1.5292` | `0.6374` |
| `policy_p95_guarded` | `validation` | `objective_policy_selection` | `0.3550` | `0.5416` | `1.5292` | `0.6374` |
| `component_pp_s1_catboost_huber_p95` | `validation` | `policy_component` | `0.3563` | `0.5594` | `1.5988` | `0.6404` |
| `component_pp_s2_quantile_catboost` | `validation` | `policy_component` | `0.3627` | `0.6180` | `1.7416` | `0.6557` |
| `component_pp_s3_lgbm_huber` | `validation` | `policy_component` | `0.3832` | `0.6529` | `1.6865` | `0.6703` |
| `component_pp_s3_lgbm_mape` | `validation` | `policy_component` | `0.3869` | `0.6056` | `1.5839` | `0.6663` |
| `component_pp_p2_mdape` | `validation` | `policy_component` | `0.3875` | `0.6737` | `1.8166` | `0.6786` |
| `component_pp_s1_catboost_huber_mdape` | `validation` | `policy_component` | `0.3923` | `0.6091` | `1.8664` | `0.6598` |
| `component_pp_s1_catboost_huber_mape` | `validation` | `policy_component` | `0.3936` | `0.5953` | `1.8113` | `0.6557` |
| `component_pp_q2_mape` | `validation` | `policy_component` | `0.3974` | `0.6293` | `1.7765` | `0.6710` |
