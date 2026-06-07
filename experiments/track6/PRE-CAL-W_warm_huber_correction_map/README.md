# PRE-CAL-W Warm Huber 상세 보정값 산출

- 목적: 후속 PP-A/PP-J에서 사용할 수 있는 모델별 residual correction map을 생성한다.
- 기준: correction map은 validation residual에서 산출하고 test에는 같은 map을 그대로 적용한다.
- 해석: 보정 후 p95_APE가 줄고 MdAPE가 악화되지 않으면 해당 segment는 후속 보정 후보로 유지한다.

## Validation 결과

| 후보 | segment 기준 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---:|---:|---:|---:|
| `corrected_size_bucket` | `size_bucket` | `0.2069` | `0.4080` | `1.2651` | `0.6437` |
| `baseline` | `none` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |
| `corrected_pred_bin` | `pred_bin` | `0.2144` | `0.4110` | `1.2652` | `0.6465` |
| `corrected_overall` | `overall` | `0.2177` | `0.4128` | `1.2985` | `0.6451` |

## 코멘터리

- `size_bucket` 보정: MdAPE delta `-0.0057`, MAPE delta `-0.0086`, p95 delta `-0.0543`.
- `pred_bin` 보정: MdAPE delta `0.0018`, MAPE delta `-0.0057`, p95 delta `-0.0541`.
- `overall` 보정: MdAPE delta `0.0051`, MAPE delta `-0.0039`, p95 delta `-0.0209`.
- `overall` correction map: usable segment `1`개.
- `pred_bin` correction map: usable segment `3`개.
- `size_bucket` correction map: usable segment `5`개.
