# PP-E1 Warm 저이력 작가 대체 적용

- 목적: 단일 후보보다 예측값 결합 또는 조건별 선택이 안정적인지 확인한다.
- 기준: 결합 가중치와 선택 규칙은 validation에서만 확정하고 test에는 그대로 적용한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `warm` | `routed_by_artist_history_bin` | `artist_history_bin` | `0.1644` | `0.2887` | `0.8346` | `0.4100` |
| `warm` | `baseline_warm_huber` | `baseline` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |

## 코멘터리

- `warm` best `routed_by_artist_history_bin`: baseline 대비 MdAPE `-0.0482`, MAPE `-0.1279`, p95 `-0.4848`.
