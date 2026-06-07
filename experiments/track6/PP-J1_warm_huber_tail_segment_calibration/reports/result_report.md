# PP-J1 Warm Huber 큰 오차 구간 보정

- 목적: 모델 구조에 맞춘 segment 기준으로 residual 보정 후보를 검증한다.
- 기준: validation residual로 correction map을 만들고 test에는 같은 map을 적용한다.

## Validation 결과

| scope | 후보 | segment 기준 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `warm` | `corrected_pred_bin_size_tail_cap` | `pred_bin_size_tail_cap` | `0.2041` | `0.4098` | `1.3027` | `0.6414` |
| `warm` | `baseline` | `none` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |

## 코멘터리

- `pred_bin_size_tail_cap`: MdAPE delta `-0.0084`, MAPE delta `-0.0068`, p95 delta `-0.0167`.
- usable correction segment: `7`개.
