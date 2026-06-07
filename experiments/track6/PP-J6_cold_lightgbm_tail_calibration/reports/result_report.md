# PP-J6 Cold LightGBM tail 구간 보정

- 목적: 모델 구조에 맞춘 segment 기준으로 residual 보정 후보를 검증한다.
- 기준: validation residual로 correction map을 만들고 test에는 같은 map을 적용한다.

## Validation 결과

| scope | 후보 | segment 기준 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `cold` | `corrected_lgb_tail_support_size_cap_0.25` | `lgb_tail_support_size_cap_0.25` | `0.3538` | `0.6652` | `1.9302` | `0.6683` |
| `cold` | `corrected_lgb_tail_support_size_cap_0.75` | `lgb_tail_support_size_cap_0.75` | `0.3545` | `0.6571` | `1.9065` | `0.6675` |
| `cold` | `corrected_lgb_tail_support_size_cap_0.5` | `lgb_tail_support_size_cap_0.5` | `0.3545` | `0.6574` | `1.9065` | `0.6675` |
| `cold` | `baseline` | `none` | `0.3851` | `0.7169` | `2.0250` | `0.6901` |
| `cold` | `baseline` | `none` | `0.3851` | `0.7169` | `2.0250` | `0.6901` |
| `cold` | `baseline` | `none` | `0.3851` | `0.7169` | `2.0250` | `0.6901` |

## 코멘터리

- `lgb_tail_support_size_cap_0.25`: MdAPE delta `-0.0314`, MAPE delta `-0.0517`, p95 delta `-0.0949`.
- `lgb_tail_support_size_cap_0.75`: MdAPE delta `-0.0306`, MAPE delta `-0.0597`, p95 delta `-0.1185`.
- `lgb_tail_support_size_cap_0.5`: MdAPE delta `-0.0306`, MAPE delta `-0.0595`, p95 delta `-0.1185`.
- usable correction segment: `45`개.
