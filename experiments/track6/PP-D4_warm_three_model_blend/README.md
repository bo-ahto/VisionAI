# PP-D4 Warm 모델 3종 예측값 결합

- 목적: 단일 후보보다 예측값 결합 또는 조건별 선택이 안정적인지 확인한다.
- 기준: 결합 가중치와 선택 규칙은 validation에서만 확정하고 test에는 그대로 적용한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `warm` | `weighted_warm_huber_catboost_l8_w_0.25_0.00_0.75` | `weighted_three` | `0.1687` | `0.3053` | `0.9460` | `0.4440` |
| `warm` | `weighted_warm_huber_l6_l8_w_0.25_0.00_0.75` | `weighted_three` | `0.1687` | `0.3053` | `0.9460` | `0.4440` |
| `warm` | `baseline_warm_huber` | `baseline` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |
| `warm` | `baseline_warm_huber` | `baseline` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |

## 코멘터리

- `warm` best `weighted_warm_huber_catboost_l8_w_0.25_0.00_0.75`: baseline 대비 MdAPE `-0.0439`, MAPE `-0.1114`, p95 `-0.3733`.
