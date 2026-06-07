# PP-D2 두 모델 가중 평균

- 목적: 단일 후보보다 예측값 결합 또는 조건별 선택이 안정적인지 확인한다.
- 기준: 결합 가중치와 선택 규칙은 validation에서만 확정하고 test에는 그대로 적용한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `cold` | `baseline_cold_lightgbm` | `baseline` | `0.3851` | `0.7169` | `2.0250` | `0.6901` |
| `cold` | `weighted_cold_catboost_lightgbm_w_0.00_cold_catboost` | `weighted_pair` | `0.3851` | `0.7169` | `2.0250` | `0.6901` |
| `warm` | `baseline_warm_huber` | `baseline` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |
| `warm` | `weighted_warm_huber_catboost_w_1.00_warm_huber` | `weighted_pair` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |

## 코멘터리

- `cold` best `baseline_cold_lightgbm`: baseline 대비 MdAPE `0.0000`, MAPE `0.0000`, p95 `0.0000`.
- `warm` best `baseline_warm_huber`: baseline 대비 MdAPE `0.0000`, MAPE `0.0000`, p95 `0.0000`.
