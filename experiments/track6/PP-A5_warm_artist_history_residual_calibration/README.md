# PP-A5 Warm 작가 학습량 구간 보정

- 목적: validation residual 중앙값으로 보정값을 만들고 같은 기준을 test에 적용한다.
- 해석: MdAPE가 유지/개선되고 p95_APE가 악화되지 않으면 PP-A 후보로 유지한다.

## Validation 결과

| scope | 후보 | segment 기준 | MdAPE | MAPE | p95_APE | RMSE_log | 상태 |
|---|---|---|---:|---:|---:|---:|---|
| `warm` | `baseline` | `none` | `0.2126` | `0.4167` | `1.3194` | `0.6446` | `ok` |
| `warm` | `corrected_artist_works_bucket` | `artist_works_bucket` | `0.2180` | `0.4097` | `1.2642` | `0.6468` | `ok` |

## 코멘터리

- `warm` `artist_works_bucket`: MdAPE delta `0.0054`, MAPE delta `-0.0070`, p95 delta `-0.0552`.
- correction map rows: `3`.
