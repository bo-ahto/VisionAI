# PP-E3 극단 크기 조건별 모델 선택

- 목적: 단일 후보보다 예측값 결합 또는 조건별 선택이 안정적인지 확인한다.
- 기준: 결합 가중치와 선택 규칙은 validation에서만 확정하고 test에는 그대로 적용한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `cold` | `routed_by_extreme_size_bin` | `extreme_size_bin` | `0.3440` | `0.5787` | `1.7804` | `0.6552` |
| `cold` | `baseline_cold_lightgbm` | `baseline` | `0.3851` | `0.7169` | `2.0250` | `0.6901` |

## 코멘터리

- `cold` best `routed_by_extreme_size_bin`: baseline 대비 MdAPE `-0.0411`, MAPE `-0.1382`, p95 `-0.2446`.
