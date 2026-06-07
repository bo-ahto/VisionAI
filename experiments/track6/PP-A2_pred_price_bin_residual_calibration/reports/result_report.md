# PP-A2 예측 가격대별 예측 오차 보정

- 목적: validation residual 중앙값으로 보정값을 만들고 같은 기준을 test에 적용한다.
- 해석: MdAPE가 유지/개선되고 p95_APE가 악화되지 않으면 PP-A 후보로 유지한다.

## Validation 결과

| scope | 후보 | segment 기준 | MdAPE | MAPE | p95_APE | RMSE_log | 상태 |
|---|---|---|---:|---:|---:|---:|---|
| `cold` | `corrected_pred_bin` | `pred_bin` | `0.4115` | `0.6236` | `1.7907` | `0.6907` | `ok` |
| `cold` | `baseline` | `none` | `0.4194` | `0.7332` | `2.2053` | `0.7037` | `ok` |
| `warm` | `baseline` | `none` | `0.2126` | `0.4167` | `1.3194` | `0.6446` | `ok` |
| `warm` | `corrected_pred_bin` | `pred_bin` | `0.2144` | `0.4110` | `1.2652` | `0.6465` | `ok` |

## 코멘터리

- `cold` `pred_bin`: MdAPE delta `-0.0079`, MAPE delta `-0.1096`, p95 delta `-0.4146`.
- `warm` `pred_bin`: MdAPE delta `0.0018`, MAPE delta `-0.0057`, p95 delta `-0.0541`.
- correction map rows: `6`.
