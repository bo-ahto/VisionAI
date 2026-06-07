# PP-Q1 Cold Quantile width 라우팅 + CatBoost Quantile 추가

- 목적: 모델별 장점을 조합하고 커스텀해 Cold 성능 개선 가능성을 확인한다.
- 기준: validation에서 선택한 조합/가중치/정책을 test에 그대로 적용한다.

## Validation 결과

| 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log | coverage | range ratio |
|---|---|---:|---:|---:|---:|---:|---:|
| `component_baseline_lgb` | `routing_component` | `0.3851` | `0.7169` | `2.0250` | `0.6901` | `nan` | `nan` |
| `width_routing_mdape_objective` | `width_segment_model_selection` | `0.3875` | `0.6737` | `1.8166` | `0.6786` | `nan` | `nan` |
| `component_hgb` | `routing_component` | `0.3921` | `0.7016` | `1.9836` | `0.6872` | `nan` | `nan` |
| `width_routing_mape_objective` | `width_segment_model_selection` | `0.3962` | `0.6544` | `1.7209` | `0.6773` | `nan` | `nan` |
| `component_quantile_lgb_q50` | `routing_component` | `0.3972` | `0.6618` | `1.7709` | `0.6798` | `nan` | `nan` |
| `component_catboost_quantile_q50` | `routing_component` | `0.4087` | `0.6591` | `2.0189` | `0.6893` | `nan` | `nan` |
