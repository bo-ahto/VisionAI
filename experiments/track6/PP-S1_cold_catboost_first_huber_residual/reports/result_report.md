# PP-S1 Cold CatBoost 선행 + Huber residual 안정화

- 목적: 모델 순서 변경, 목적함수 커스텀, 메타 조합이 기존 PP-Q/PP-R 이후 추가 개선을 주는지 확인한다.
- 근거: CatBoost/LightGBM의 MAPE/Quantile/Huber 목적함수와 stacking의 모델 출력값 결합 구조를 Track6 후보에 적용한다.
- 기준: 가중치, residual 모델, meta 모델, 정책 선택은 validation에서 정하고 test에는 그대로 적용한다.

## Metrics

| 후보 | split | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `n2_catboost_quantile_huber_cap0.2_s1` | `test` | `ordered_residual_model` | `0.4744` | `1.2095` | `3.4731` | `0.9301` |
| `n2_catboost_quantile_huber_cap0.35_s1` | `test` | `ordered_residual_model` | `0.4763` | `1.2085` | `3.4074` | `0.9354` |
| `n2_catboost_quantile_huber_cap0.5_s1` | `test` | `ordered_residual_model` | `0.4765` | `1.2067` | `3.2824` | `0.9386` |
| `n2_catboost_quantile_ridge_1_cap0.2_s1` | `test` | `ordered_residual_model` | `0.4773` | `1.2231` | `3.4837` | `0.9308` |
| `n2_catboost_quantile_ridge_10_cap0.2_s1` | `test` | `ordered_residual_model` | `0.4778` | `1.2227` | `3.4987` | `0.9307` |
| `n2_catboost_quantile_ridge_10_cap0.5_s1` | `test` | `ordered_residual_model` | `0.4781` | `1.2199` | `3.4357` | `0.9369` |
| `n2_catboost_quantile_ridge_10_cap0.35_s1` | `test` | `ordered_residual_model` | `0.4781` | `1.2220` | `3.4987` | `0.9353` |
| `n2_catboost_quantile_huber_cap0.35_s0.5` | `test` | `ordered_residual_model` | `0.4785` | `1.1734` | `3.6074` | `0.9227` |
| `n2_catboost_quantile_ridge_1_cap0.5_s1` | `test` | `ordered_residual_model` | `0.4786` | `1.2215` | `3.4455` | `0.9375` |
| `n2_catboost_quantile_ridge_1_cap0.35_s1` | `test` | `ordered_residual_model` | `0.4786` | `1.2235` | `3.4837` | `0.9358` |
| `n2_catboost_quantile_huber_cap0.2_s0.5` | `test` | `ordered_residual_model` | `0.4789` | `1.1759` | `3.7648` | `0.9211` |
| `n2_catboost_quantile_ridge_1_cap0.2_s0.5` | `test` | `ordered_residual_model` | `0.4791` | `1.1828` | `3.7648` | `0.9215` |
| `n2_catboost_quantile_ridge_10_cap0.2_s0.5` | `test` | `ordered_residual_model` | `0.4792` | `1.1826` | `3.7648` | `0.9215` |
| `n2_catboost_quantile_ridge_10_cap0.35_s0.5` | `test` | `ordered_residual_model` | `0.4794` | `1.1806` | `3.6436` | `0.9229` |
| `n2_catboost_quantile_ridge_1_cap0.35_s0.5` | `test` | `ordered_residual_model` | `0.4794` | `1.1813` | `3.6501` | `0.9231` |
| `n2_catboost_quantile_huber_cap0.5_s0.5` | `test` | `ordered_residual_model` | `0.4808` | `1.1716` | `3.6074` | `0.9236` |
| `n2_catboost_quantile_ridge_10_cap0.5_s0.5` | `test` | `ordered_residual_model` | `0.4812` | `1.1789` | `3.6436` | `0.9232` |
| `n2_catboost_quantile_ridge_1_cap0.5_s0.5` | `test` | `ordered_residual_model` | `0.4823` | `1.1796` | `3.6501` | `0.9235` |
| `base_n2_catboost_quantile` | `test` | `stage1_base_model` | `0.4830` | `1.1514` | `4.2659` | `0.9161` |
| `n2_catboost_quantile_huber_cap0.5_s1` | `validation` | `ordered_residual_model` | `0.3563` | `0.5594` | `1.5988` | `0.6404` |
| `n2_catboost_quantile_ridge_1_cap0.5_s1` | `validation` | `ordered_residual_model` | `0.3577` | `0.5650` | `1.5988` | `0.6400` |
| `n2_catboost_quantile_ridge_10_cap0.5_s1` | `validation` | `ordered_residual_model` | `0.3587` | `0.5652` | `1.5988` | `0.6401` |
| `n2_catboost_quantile_huber_cap0.35_s1` | `validation` | `ordered_residual_model` | `0.3678` | `0.5766` | `1.7011` | `0.6472` |
| `n2_catboost_quantile_ridge_10_cap0.35_s1` | `validation` | `ordered_residual_model` | `0.3720` | `0.5818` | `1.7297` | `0.6471` |
| `n2_catboost_quantile_ridge_1_cap0.35_s1` | `validation` | `ordered_residual_model` | `0.3725` | `0.5816` | `1.7269` | `0.6471` |
| `n2_catboost_quantile_huber_cap0.2_s1` | `validation` | `ordered_residual_model` | `0.3923` | `0.6091` | `1.8664` | `0.6598` |
| `n2_catboost_quantile_ridge_1_cap0.2_s1` | `validation` | `ordered_residual_model` | `0.3925` | `0.6116` | `1.8778` | `0.6593` |
| `n2_catboost_quantile_huber_cap0.5_s0.5` | `validation` | `ordered_residual_model` | `0.3936` | `0.5953` | `1.8113` | `0.6557` |
| `n2_catboost_quantile_ridge_10_cap0.2_s1` | `validation` | `ordered_residual_model` | `0.3939` | `0.6116` | `1.8736` | `0.6592` |
| `n2_catboost_quantile_huber_cap0.35_s0.5` | `validation` | `ordered_residual_model` | `0.3945` | `0.6101` | `1.8439` | `0.6622` |
| `n2_catboost_quantile_ridge_10_cap0.5_s0.5` | `validation` | `ordered_residual_model` | `0.3956` | `0.5990` | `1.8242` | `0.6564` |
| `n2_catboost_quantile_ridge_1_cap0.5_s0.5` | `validation` | `ordered_residual_model` | `0.3958` | `0.5989` | `1.8238` | `0.6563` |
| `n2_catboost_quantile_ridge_1_cap0.35_s0.5` | `validation` | `ordered_residual_model` | `0.3966` | `0.6129` | `1.8593` | `0.6626` |
| `n2_catboost_quantile_ridge_10_cap0.35_s0.5` | `validation` | `ordered_residual_model` | `0.3968` | `0.6130` | `1.8547` | `0.6627` |
| `n2_catboost_quantile_huber_cap0.2_s0.5` | `validation` | `ordered_residual_model` | `0.4005` | `0.6305` | `1.9010` | `0.6714` |
| `n2_catboost_quantile_ridge_1_cap0.2_s0.5` | `validation` | `ordered_residual_model` | `0.4014` | `0.6318` | `1.9106` | `0.6712` |
| `n2_catboost_quantile_ridge_10_cap0.2_s0.5` | `validation` | `ordered_residual_model` | `0.4019` | `0.6318` | `1.9081` | `0.6712` |
| `base_n2_catboost_quantile` | `validation` | `stage1_base_model` | `0.4087` | `0.6591` | `2.0189` | `0.6893` |
