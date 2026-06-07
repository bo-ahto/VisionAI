# PRE-CAL-LGB Cold LightGBM 상세 보정값 산출

- 목적: 후속 PP-A/PP-J에서 사용할 수 있는 모델별 residual correction map을 생성한다.
- 기준: correction map은 validation residual에서 산출하고 test에는 같은 map을 그대로 적용한다.
- 해석: 보정 후 p95_APE가 줄고 MdAPE가 악화되지 않으면 해당 segment는 후속 보정 후보로 유지한다.

## Validation 결과

| 후보 | segment 기준 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---:|---:|---:|---:|
| `corrected_support_size_bucket` | `support_size_bucket` | `0.3614` | `0.6517` | `1.8954` | `0.6731` |
| `corrected_tail_risk_segment` | `tail_risk_segment` | `0.3787` | `0.6577` | `1.8645` | `0.6792` |
| `corrected_size_bucket` | `size_bucket` | `0.3801` | `0.6685` | `1.7909` | `0.6878` |
| `baseline` | `none` | `0.3851` | `0.7169` | `2.0250` | `0.6901` |
| `corrected_pred_bin` | `pred_bin` | `0.3866` | `0.6606` | `1.8156` | `0.6857` |
| `corrected_overall` | `overall` | `0.3873` | `0.6612` | `1.8052` | `0.6859` |

## 코멘터리

- `support_size_bucket` 보정: MdAPE delta `-0.0237`, MAPE delta `-0.0652`, p95 delta `-0.1296`.
- `tail_risk_segment` 보정: MdAPE delta `-0.0064`, MAPE delta `-0.0592`, p95 delta `-0.1605`.
- `size_bucket` 보정: MdAPE delta `-0.0051`, MAPE delta `-0.0484`, p95 delta `-0.2341`.
- `pred_bin` 보정: MdAPE delta `0.0015`, MAPE delta `-0.0563`, p95 delta `-0.2095`.
- `overall` 보정: MdAPE delta `0.0022`, MAPE delta `-0.0557`, p95 delta `-0.2198`.
- `overall` correction map: usable segment `1`개.
- `pred_bin` correction map: usable segment `3`개.
- `size_bucket` correction map: usable segment `5`개.
- `support_size_bucket` correction map: usable segment `14`개.
- `tail_risk_segment` correction map: usable segment `9`개.
