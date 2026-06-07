# PP-J4 Cold CatBoost leaf coverage 보정

- 목적: 모델 구조에 맞춘 segment 기준으로 residual 보정 후보를 검증한다.
- 기준: validation residual로 correction map을 만들고 test에는 같은 map을 적용한다.

## Validation 결과

| scope | 후보 | segment 기준 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `cold` | `corrected_leaf_segment_min_rows_20` | `leaf_segment_min_rows_20` | `0.3440` | `0.5876` | `1.8586` | `0.6559` |
| `cold` | `corrected_leaf_segment_min_rows_50` | `leaf_segment_min_rows_50` | `0.3720` | `0.6310` | `1.8812` | `0.6693` |
| `cold` | `corrected_leaf_segment_min_rows_100` | `leaf_segment_min_rows_100` | `0.3918` | `0.6500` | `1.9024` | `0.6746` |
| `cold` | `baseline` | `none` | `0.4194` | `0.7332` | `2.2053` | `0.7037` |
| `cold` | `baseline` | `none` | `0.4194` | `0.7332` | `2.2053` | `0.7037` |
| `cold` | `baseline` | `none` | `0.4194` | `0.7332` | `2.2053` | `0.7037` |

## 코멘터리

- `leaf_segment_min_rows_20`: MdAPE delta `-0.0754`, MAPE delta `-0.1456`, p95 delta `-0.3467`.
- `leaf_segment_min_rows_50`: MdAPE delta `-0.0474`, MAPE delta `-0.1022`, p95 delta `-0.3241`.
- `leaf_segment_min_rows_100`: MdAPE delta `-0.0276`, MAPE delta `-0.0832`, p95 delta `-0.3029`.
- usable correction segment: `36`개.
