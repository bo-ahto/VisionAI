# PP-A8 최소 표본 수 기준 보정

- 목적: validation residual 중앙값으로 보정값을 만들고 같은 기준을 test에 적용한다.
- 해석: MdAPE가 유지/개선되고 p95_APE가 악화되지 않으면 PP-A 후보로 유지한다.

## Validation 결과

| scope | 후보 | segment 기준 | MdAPE | MAPE | p95_APE | RMSE_log | 상태 |
|---|---|---|---:|---:|---:|---:|---|
| `cold` | `corrected_min_rows_30` | `hierarchical_min_rows_30` | `0.3567` | `0.5662` | `1.6593` | `0.6616` | `ok` |
| `cold` | `corrected_min_rows_50` | `hierarchical_min_rows_50` | `0.3606` | `0.5698` | `1.6625` | `0.6699` | `ok` |
| `cold` | `corrected_min_rows_100` | `hierarchical_min_rows_100` | `0.3660` | `0.5709` | `1.6575` | `0.6698` | `ok` |
| `cold` | `baseline` | `none` | `0.4194` | `0.7332` | `2.2053` | `0.7037` | `ok` |
| `warm` | `corrected_min_rows_30` | `hierarchical_min_rows_30` | `0.2047` | `0.4184` | `1.4026` | `0.6440` | `ok` |
| `warm` | `corrected_min_rows_50` | `hierarchical_min_rows_50` | `0.2069` | `0.4213` | `1.3988` | `0.6436` | `ok` |
| `warm` | `corrected_min_rows_100` | `hierarchical_min_rows_100` | `0.2091` | `0.4193` | `1.3988` | `0.6443` | `ok` |
| `warm` | `baseline` | `none` | `0.2126` | `0.4167` | `1.3194` | `0.6446` | `ok` |

## 코멘터리

- `cold` `hierarchical_min_rows_30`: MdAPE delta `-0.0626`, MAPE delta `-0.1670`, p95 delta `-0.5460`.
- `cold` `hierarchical_min_rows_50`: MdAPE delta `-0.0587`, MAPE delta `-0.1634`, p95 delta `-0.5428`.
- `cold` `hierarchical_min_rows_100`: MdAPE delta `-0.0533`, MAPE delta `-0.1624`, p95 delta `-0.5478`.
- `warm` `hierarchical_min_rows_30`: MdAPE delta `-0.0079`, MAPE delta `0.0017`, p95 delta `0.0833`.
- `warm` `hierarchical_min_rows_50`: MdAPE delta `-0.0057`, MAPE delta `0.0047`, p95 delta `0.0794`.
- `warm` `hierarchical_min_rows_100`: MdAPE delta `-0.0035`, MAPE delta `0.0026`, p95 delta `0.0794`.
- correction map rows: `888`.
