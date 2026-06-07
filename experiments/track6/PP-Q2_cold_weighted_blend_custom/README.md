# PP-Q2 Cold 모델 가중 결합 커스텀

- 목적: 모델별 장점을 조합하고 커스텀해 Cold 성능 개선 가능성을 확인한다.
- 기준: validation에서 선택한 조합/가중치/정책을 test에 그대로 적용한다.

## Validation 결과

| 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log | coverage | range ratio |
|---|---|---:|---:|---:|---:|---:|---:|
| `weighted_blend_mdape_objective` | `weighted_log_prediction_blend` | `0.3820` | `0.6850` | `1.8897` | `0.6803` | `nan` | `nan` |
| `component_baseline_lgb` | `blend_component` | `0.3851` | `0.7169` | `2.0250` | `0.6901` | `nan` | `nan` |
| `component_hgb` | `blend_component` | `0.3921` | `0.7016` | `1.9836` | `0.6872` | `nan` | `nan` |
| `component_quantile_lgb_q50` | `blend_component` | `0.3972` | `0.6618` | `1.7709` | `0.6798` | `nan` | `nan` |
| `weighted_blend_mape_objective` | `weighted_log_prediction_blend` | `0.3974` | `0.6293` | `1.7765` | `0.6710` | `nan` | `nan` |
| `component_catboost_quantile_q50` | `blend_component` | `0.4087` | `0.6591` | `2.0189` | `0.6893` | `nan` | `nan` |
