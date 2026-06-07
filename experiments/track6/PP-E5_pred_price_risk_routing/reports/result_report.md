# PP-E5 예측 가격대 위험 조건별 모델 선택

- 목적: 단일 후보보다 예측값 결합 또는 조건별 선택이 안정적인지 확인한다.
- 기준: 결합 가중치와 선택 규칙은 validation에서만 확정하고 test에는 그대로 적용한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `cold` | `routed_by_pred_risk_bin` | `pred_risk_bin` | `0.3378` | `0.6019` | `1.9344` | `0.6633` |
| `cold` | `baseline_cold_lightgbm` | `baseline` | `0.3851` | `0.7169` | `2.0250` | `0.6901` |

## 코멘터리

- `cold` best `routed_by_pred_risk_bin`: baseline 대비 MdAPE `-0.0473`, MAPE `-0.1150`, p95 `-0.0906`.
