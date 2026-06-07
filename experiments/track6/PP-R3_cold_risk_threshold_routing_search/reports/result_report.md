# PP-R3 Cold 위험 구간 라우팅 threshold 탐색

- 목적: PP-Q 이후 남은 개선 여지를 모델 조합, 단계 보정, 라우팅, 메타 보정으로 확인한다.
- 기준: 가중치, 보정값, threshold, meta 모델은 validation에서만 정하고 test에는 그대로 적용한다.

## Metrics

| 후보 | scope | split | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---|---:|---:|---:|---:|
| `threshold_routing_p95_guarded` | `cold` | `test` | `risk_threshold_routing_search` | `0.4905` | `1.2333` | `4.2659` | `0.9335` |
| `threshold_routing_mape_guarded` | `cold` | `test` | `risk_threshold_routing_search` | `0.4925` | `1.3866` | `4.2659` | `0.9690` |
| `threshold_routing_mdape` | `cold` | `test` | `risk_threshold_routing_search` | `0.4946` | `1.4096` | `4.1990` | `0.9711` |
| `threshold_routing_mdape` | `cold` | `validation` | `risk_threshold_routing_search` | `0.3449` | `0.5728` | `1.6949` | `0.6544` |
| `threshold_routing_mape_guarded` | `cold` | `validation` | `risk_threshold_routing_search` | `0.3489` | `0.5501` | `1.6219` | `0.6495` |
| `threshold_routing_p95_guarded` | `cold` | `validation` | `risk_threshold_routing_search` | `0.3714` | `0.5715` | `1.6333` | `0.6526` |
