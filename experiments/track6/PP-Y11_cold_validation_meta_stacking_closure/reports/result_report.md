# PP-Y11 Cold validation meta stacking closure

- 목적: Cold 추가 실험 여지를 줄이기 위해 남은 피처/목적함수/라우팅/보정 축을 닫는다.
- 기준: 기존 split과 기존 PP-Y 강한 후보를 유지하고 validation/test를 함께 기록한다.

## Test 결과 상위

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 정책 |
|---|---:|---:|---:|---:|---|
| `huber_validation_meta_component_range_clipped` | 0.4560 | 1.0995 | 3.9427 | 0.8848 | `validation_meta_stacking_closure` |
| `huber_validation_meta_raw` | 0.4729 | 1.1481 | 4.2109 | 0.8916 | `validation_meta_stacking_closure` |
| `ridge_10_validation_meta_component_range_clipped` | 0.4812 | 1.0957 | 4.0238 | 0.8780 | `validation_meta_stacking_closure` |
| `ridge_10_validation_meta_raw` | 0.4906 | 1.1319 | 4.1322 | 0.8812 | `validation_meta_stacking_closure` |

## 설정/피처 맵

| experiment_id | meta_model | source_labels | feature_columns | note |
| --- | --- | --- | --- | --- |
| PP-Y11 | ridge_10 | y1_external_interaction, y2_search_external_interaction, y6_lgbq_cat_resid, y10_mdape_route, y10_p95_route, h9_search_p95, w4_p95 | y1_external_interaction_pred, y2_search_external_interaction_pred, y6_lgbq_cat_resid_pred, y10_mdape_route_pred, y10_p95_route_pred, h9_search_p95_pred, w4_p95_pred, pred_mean, pred_std, pred_min, pred_max | Validation-trained meta stacking closure; final OOF meta should be run separately before production selection. |
| PP-Y11 | huber | y1_external_interaction, y2_search_external_interaction, y6_lgbq_cat_resid, y10_mdape_route, y10_p95_route, h9_search_p95, w4_p95 | y1_external_interaction_pred, y2_search_external_interaction_pred, y6_lgbq_cat_resid_pred, y10_mdape_route_pred, y10_p95_route_pred, h9_search_p95_pred, w4_p95_pred, pred_mean, pred_std, pred_min, pred_max | Validation-trained meta stacking closure; final OOF meta should be run separately before production selection. |
