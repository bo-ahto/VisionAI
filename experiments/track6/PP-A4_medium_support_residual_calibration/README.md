# PP-A4 재료/지지체 구간별 보정

- 목적: validation residual 중앙값으로 보정값을 만들고 같은 기준을 test에 적용한다.
- 해석: MdAPE가 유지/개선되고 p95_APE가 악화되지 않으면 PP-A 후보로 유지한다.

## Validation 결과

| scope | 후보 | segment 기준 | MdAPE | MAPE | p95_APE | RMSE_log | 상태 |
|---|---|---|---:|---:|---:|---:|---|
| `cold` | `corrected_material_support` | `material_support` | `0.4083` | `0.6004` | `1.6551` | `0.6793` | `ok` |
| `cold` | `baseline` | `none` | `0.4194` | `0.7332` | `2.2053` | `0.7037` | `ok` |
| `warm` | `corrected_material_support` | `material_support` | `0.2112` | `0.4171` | `1.3697` | `0.6449` | `ok` |
| `warm` | `baseline` | `none` | `0.2126` | `0.4167` | `1.3194` | `0.6446` | `ok` |

## 코멘터리

- `cold` `material_support`: MdAPE delta `-0.0111`, MAPE delta `-0.1328`, p95 delta `-0.5502`.
- `warm` `material_support`: MdAPE delta `-0.0014`, MAPE delta `0.0004`, p95 delta `0.0504`.
- correction map rows: `68`.
