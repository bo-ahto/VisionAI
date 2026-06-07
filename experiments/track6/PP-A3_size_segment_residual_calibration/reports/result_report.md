# PP-A3 호수/크기 구간별 보정

- 목적: validation residual 중앙값으로 보정값을 만들고 같은 기준을 test에 적용한다.
- 해석: MdAPE가 유지/개선되고 p95_APE가 악화되지 않으면 PP-A 후보로 유지한다.

## Validation 결과

| scope | 후보 | segment 기준 | MdAPE | MAPE | p95_APE | RMSE_log | 상태 |
|---|---|---|---:|---:|---:|---:|---|
| `cold` | `corrected_size_bucket` | `size_bucket` | `0.4132` | `0.6238` | `1.7598` | `0.6893` | `ok` |
| `cold` | `baseline` | `none` | `0.4194` | `0.7332` | `2.2053` | `0.7037` | `ok` |
| `warm` | `corrected_size_bucket` | `size_bucket` | `0.2069` | `0.4080` | `1.2651` | `0.6437` | `ok` |
| `warm` | `baseline` | `none` | `0.2126` | `0.4167` | `1.3194` | `0.6446` | `ok` |

## 코멘터리

- `cold` `size_bucket`: MdAPE delta `-0.0061`, MAPE delta `-0.1094`, p95 delta `-0.4456`.
- `warm` `size_bucket`: MdAPE delta `-0.0057`, MAPE delta `-0.0086`, p95 delta `-0.0543`.
- correction map rows: `10`.
