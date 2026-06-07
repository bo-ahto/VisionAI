# PP-I5 최종 후보 통합 검증

- 목적: 최종 후보로 남길 설정, 보정 강도, 라우팅 기준, 통합 후보를 같은 기준으로 확인한다.
- 기준: validation 기준으로 선택하고 test 결과는 재현성 확인으로만 기록한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `cold` | `cold_pp_d3_tail_blend` | `reference_PP-D3_tail_defense_model_blend` | `0.3370` | `0.5862` | `1.8242` | `0.6455` |
| `cold` | `cold_pp_j4_leaf` | `reference_PP-J4_cold_catboost_leaf_coverage_calibration` | `0.3440` | `0.5876` | `1.8586` | `0.6559` |
| `cold` | `cold_pp_j6_lgb_tail` | `reference_PP-J6_cold_lightgbm_tail_calibration` | `0.3538` | `0.6652` | `1.9302` | `0.6683` |
| `cold` | `cold_pp_a7_hierarchical` | `reference_PP-A7_hierarchical_segment_residual_calibration` | `0.3567` | `0.5662` | `1.6593` | `0.6616` |
| `cold` | `cold_baseline_lightgbm` | `reference_PP-B4_oof_base_residual_source` | `0.3851` | `0.7169` | `2.0250` | `0.6901` |
| `warm` | `warm_pp_e1_routing` | `reference_PP-E1_warm_low_history_routing` | `0.1644` | `0.2887` | `0.8346` | `0.4100` |
| `warm` | `warm_pp_d4_integrated` | `reference_PP-D4_warm_three_model_blend` | `0.1687` | `0.3053` | `0.9460` | `0.4440` |
| `warm` | `warm_pp_l8_sequential` | `reference_PP-L8_quantile_huber_catboost_sequential` | `0.1808` | `0.3152` | `0.9341` | `0.4285` |
| `warm` | `warm_pp_k3_similar_fallback` | `reference_PP-K3_similar_artwork_fallback` | `0.1996` | `0.3672` | `1.1230` | `0.5157` |
| `warm` | `warm_baseline_huber` | `reference_PP-B4_oof_base_residual_source` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |
