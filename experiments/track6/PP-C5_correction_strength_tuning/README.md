# PP-C5 보정 강도 줄이기 실험

- 목적: 예측값 자체를 다시 맞추거나, 이미 효과가 있던 보정값의 강도를 조정해 과보정을 줄인다.
- 기준: 보정식은 validation에서만 확정하고 같은 식을 test에 적용한다.

## Validation 결과

| 모델 소스 | 후보 | 보정 방식 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `cold_catboost_ppa7_hierarchical` | `strength_1.00_corrected_hierarchical` | `strength_scaled` | `0.3567` | `0.5662` | `1.6593` | `0.6616` |
| `cold_catboost_ppa7_hierarchical` | `strength_0.75_corrected_hierarchical` | `strength_scaled` | `0.3613` | `0.5876` | `1.7387` | `0.6564` |
| `cold_catboost_ppa7_hierarchical` | `strength_0.50_corrected_hierarchical` | `strength_scaled` | `0.3765` | `0.6206` | `1.8385` | `0.6619` |
| `cold_catboost_ppa7_hierarchical` | `strength_0.25_corrected_hierarchical` | `strength_scaled` | `0.4111` | `0.6679` | `1.9104` | `0.6779` |
| `cold_catboost_ppa7_hierarchical` | `baseline` | `none` | `0.4194` | `0.7332` | `2.2053` | `0.7037` |
| `cold_catboost_ppj4_leaf` | `strength_1.00_corrected_leaf_segment_min_rows_20` | `strength_scaled` | `0.3440` | `0.5876` | `1.8586` | `0.6559` |
| `cold_catboost_ppj4_leaf` | `strength_0.75_corrected_leaf_segment_min_rows_20` | `strength_scaled` | `0.3543` | `0.6105` | `1.8676` | `0.6568` |
| `cold_catboost_ppj4_leaf` | `strength_0.50_corrected_leaf_segment_min_rows_20` | `strength_scaled` | `0.3626` | `0.6411` | `1.8737` | `0.6653` |
| `cold_catboost_ppj4_leaf` | `strength_0.25_corrected_leaf_segment_min_rows_20` | `strength_scaled` | `0.4133` | `0.6814` | `1.9374` | `0.6811` |
| `cold_catboost_ppj4_leaf` | `baseline` | `none` | `0.4194` | `0.7332` | `2.2053` | `0.7037` |
| `cold_lightgbm_ppj6_tail` | `strength_1.00_corrected_lgb_tail_support_size_cap_0.25` | `strength_scaled` | `0.3538` | `0.6652` | `1.9302` | `0.6683` |
| `cold_lightgbm_ppj6_tail` | `strength_0.75_corrected_lgb_tail_support_size_cap_0.25` | `strength_scaled` | `0.3626` | `0.6733` | `1.9448` | `0.6695` |
| `cold_lightgbm_ppj6_tail` | `strength_0.50_corrected_lgb_tail_support_size_cap_0.25` | `strength_scaled` | `0.3709` | `0.6846` | `1.9847` | `0.6736` |
| `cold_lightgbm_ppj6_tail` | `strength_0.25_corrected_lgb_tail_support_size_cap_0.25` | `strength_scaled` | `0.3761` | `0.6992` | `2.0255` | `0.6804` |
| `cold_lightgbm_ppj6_tail` | `baseline` | `none` | `0.3851` | `0.7169` | `2.0250` | `0.6901` |
| `warm_huber_ppj1_tail` | `strength_0.75_corrected_pred_bin_size_tail_cap` | `strength_scaled` | `0.1954` | `0.4102` | `1.3079` | `0.6414` |
| `warm_huber_ppj1_tail` | `strength_1.00_corrected_pred_bin_size_tail_cap` | `strength_scaled` | `0.2041` | `0.4098` | `1.3027` | `0.6414` |
| `warm_huber_ppj1_tail` | `strength_0.50_corrected_pred_bin_size_tail_cap` | `strength_scaled` | `0.2056` | `0.4116` | `1.3082` | `0.6420` |
| `warm_huber_ppj1_tail` | `strength_0.25_corrected_pred_bin_size_tail_cap` | `strength_scaled` | `0.2079` | `0.4138` | `1.3095` | `0.6430` |
| `warm_huber_ppj1_tail` | `baseline` | `none` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |

## 코멘터리

- `cold_catboost_ppa7_hierarchical` best `strength_1.00_corrected_hierarchical`: baseline 대비 MdAPE `-0.0626`, MAPE `-0.1670`, p95 `-0.5460`.
- `cold_catboost_ppj4_leaf` best `strength_1.00_corrected_leaf_segment_min_rows_20`: baseline 대비 MdAPE `-0.0754`, MAPE `-0.1456`, p95 `-0.3467`.
- `cold_lightgbm_ppj6_tail` best `strength_1.00_corrected_lgb_tail_support_size_cap_0.25`: baseline 대비 MdAPE `-0.0314`, MAPE `-0.0517`, p95 `-0.0949`.
- `warm_huber_ppj1_tail` best `strength_0.75_corrected_pred_bin_size_tail_cap`: baseline 대비 MdAPE `-0.0172`, MAPE `-0.0064`, p95 `-0.0115`.
