# PP-R2 Cold 앙상블 후 residual 단계 보정

- 목적: PP-Q 이후 남은 개선 여지를 모델 조합, 단계 보정, 라우팅, 메타 보정으로 확인한다.
- 기준: 가중치, 보정값, threshold, meta 모델은 validation에서만 정하고 test에는 그대로 적용한다.

## Metrics

| 후보 | scope | split | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---|---:|---:|---:|---:|
| `base_q2_mape_blend` | `cold` | `test` | `stage0_ensemble` | `0.4811` | `1.1797` | `3.7925` | `0.9236` |
| `stage2_residual_mdape` | `cold` | `test` | `ensemble_then_segment_residual` | `0.4886` | `1.2424` | `3.5958` | `0.9515` |
| `stage2_residual_mape_guarded` | `cold` | `test` | `ensemble_then_segment_residual` | `0.4933` | `1.1748` | `3.4226` | `0.9608` |
| `stage2_residual_p95_guarded` | `cold` | `test` | `ensemble_then_segment_residual` | `0.4933` | `1.1748` | `3.4226` | `0.9608` |
| `stage2_residual_mdape` | `cold` | `validation` | `ensemble_then_segment_residual` | `0.3626` | `0.5567` | `1.6134` | `0.6513` |
| `stage2_residual_mape_guarded` | `cold` | `validation` | `ensemble_then_segment_residual` | `0.3807` | `0.5552` | `1.4809` | `0.6635` |
| `stage2_residual_p95_guarded` | `cold` | `validation` | `ensemble_then_segment_residual` | `0.3807` | `0.5552` | `1.4809` | `0.6635` |
| `base_q2_mape_blend` | `cold` | `validation` | `stage0_ensemble` | `0.3974` | `0.6293` | `1.7765` | `0.6710` |
