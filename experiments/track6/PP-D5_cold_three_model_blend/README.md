# PP-D5 Cold 모델 3종 예측값 결합

- 목적: 단일 후보보다 예측값 결합 또는 조건별 선택이 안정적인지 확인한다.
- 기준: 결합 가중치와 선택 규칙은 validation에서만 확정하고 test에는 그대로 적용한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `cold` | `weighted_cold_corrected_l8_w_0.75_0.25_0.00` | `weighted_three` | `0.3370` | `0.5862` | `1.8242` | `0.6455` |
| `cold` | `baseline_cold_j4` | `baseline` | `0.3440` | `0.5876` | `1.8586` | `0.6559` |
| `cold` | `baseline_cold_lightgbm` | `baseline` | `0.3851` | `0.7169` | `2.0250` | `0.6901` |
| `cold` | `weighted_cold_raw_q50_w_0.00_1.00_0.00` | `weighted_three` | `0.3851` | `0.7169` | `2.0250` | `0.6901` |

## 코멘터리

- `cold` best `weighted_cold_corrected_l8_w_0.75_0.25_0.00`: baseline 대비 MdAPE `-0.0070`, MAPE `-0.0014`, p95 `-0.0344`.
