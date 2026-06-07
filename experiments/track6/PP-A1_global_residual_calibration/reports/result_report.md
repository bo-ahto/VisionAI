# PP-A1 전체 예측 오차 보정

- 목적: validation residual 중앙값으로 보정값을 만들고 같은 기준을 test에 적용한다.
- 해석: MdAPE가 유지/개선되고 p95_APE가 악화되지 않으면 PP-A 후보로 유지한다.

## Validation 결과

| scope | 후보 | segment 기준 | MdAPE | MAPE | p95_APE | RMSE_log | 상태 |
|---|---|---|---:|---:|---:|---:|---|
| `cold` | `corrected_overall` | `overall` | `0.4005` | `0.6130` | `1.7342` | `0.6917` | `ok` |
| `cold` | `baseline` | `none` | `0.4194` | `0.7332` | `2.2053` | `0.7037` | `ok` |
| `warm` | `baseline` | `none` | `0.2126` | `0.4167` | `1.3194` | `0.6446` | `ok` |
| `warm` | `corrected_overall` | `overall` | `0.2177` | `0.4128` | `1.2985` | `0.6451` | `ok` |

## 코멘터리

- `cold` `overall`: MdAPE delta `-0.0189`, MAPE delta `-0.1202`, p95 delta `-0.4711`.
- `warm` `overall`: MdAPE delta `0.0051`, MAPE delta `-0.0039`, p95 delta `-0.0209`.
- correction map rows: `2`.
