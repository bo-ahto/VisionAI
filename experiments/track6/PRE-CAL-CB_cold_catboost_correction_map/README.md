# PRE-CAL-CB Cold CatBoost 상세 보정값 산출

- 목적: 후속 PP-A/PP-J에서 사용할 수 있는 모델별 residual correction map을 생성한다.
- 기준: correction map은 validation residual에서 산출하고 test에는 같은 map을 그대로 적용한다.
- 해석: 보정 후 p95_APE가 줄고 MdAPE가 악화되지 않으면 해당 segment는 후속 보정 후보로 유지한다.

## Validation 결과

| 후보 | segment 기준 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---:|---:|---:|---:|
| `corrected_leaf_segment` | `leaf_segment` | `0.3636` | `0.5937` | `1.8183` | `0.6612` |
| `corrected_shape_bucket` | `shape_bucket` | `0.3936` | `0.6115` | `1.7257` | `0.6911` |
| `corrected_overall` | `overall` | `0.4005` | `0.6130` | `1.7342` | `0.6917` |
| `corrected_medium_shape_bucket` | `medium_shape_bucket` | `0.4083` | `0.6004` | `1.6551` | `0.6793` |
| `baseline` | `none` | `0.4194` | `0.7332` | `2.2053` | `0.7037` |

## 코멘터리

- `leaf_segment` 보정: MdAPE delta `-0.0557`, MAPE delta `-0.1395`, p95 delta `-0.3870`.
- `shape_bucket` 보정: MdAPE delta `-0.0258`, MAPE delta `-0.1217`, p95 delta `-0.4797`.
- `overall` 보정: MdAPE delta `-0.0189`, MAPE delta `-0.1202`, p95 delta `-0.4711`.
- `medium_shape_bucket` 보정: MdAPE delta `-0.0111`, MAPE delta `-0.1328`, p95 delta `-0.5502`.
- `overall` correction map: usable segment `1`개.
- `leaf_segment` correction map: usable segment `14`개.
- `medium_shape_bucket` correction map: usable segment `7`개.
- `shape_bucket` correction map: usable segment `3`개.
