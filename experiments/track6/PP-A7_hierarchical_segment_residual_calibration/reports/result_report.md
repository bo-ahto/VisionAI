# PP-A7 계층형 구간 보정

- 목적: validation residual 중앙값으로 보정값을 만들고 같은 기준을 test에 적용한다.
- 해석: MdAPE가 유지/개선되고 p95_APE가 악화되지 않으면 PP-A 후보로 유지한다.

## Validation 결과

| scope | 후보 | segment 기준 | MdAPE | MAPE | p95_APE | RMSE_log | 상태 |
|---|---|---|---:|---:|---:|---:|---|
| `cold` | `corrected_hierarchical` | `hierarchical_pred_size_material` | `0.3567` | `0.5662` | `1.6593` | `0.6616` | `ok` |
| `cold` | `baseline` | `none` | `0.4194` | `0.7332` | `2.2053` | `0.7037` | `ok` |
| `warm` | `corrected_hierarchical` | `hierarchical_pred_size_material` | `0.2047` | `0.4184` | `1.4026` | `0.6440` | `ok` |
| `warm` | `baseline` | `none` | `0.2126` | `0.4167` | `1.3194` | `0.6446` | `ok` |

## 코멘터리

- `cold` `hierarchical_pred_size_material`: MdAPE delta `-0.0626`, MAPE delta `-0.1670`, p95 delta `-0.5460`.
- `warm` `hierarchical_pred_size_material`: MdAPE delta `-0.0079`, MAPE delta `0.0017`, p95 delta `0.0833`.
- correction map rows: `296`.
