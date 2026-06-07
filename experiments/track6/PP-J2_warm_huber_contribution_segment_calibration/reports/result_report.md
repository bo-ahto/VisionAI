# PP-J2 Warm Huber 계수 기여도 구간 보정

- 목적: 모델 구조에 맞춘 segment 기준으로 residual 보정 후보를 검증한다.
- 기준: validation residual로 correction map을 만들고 test에는 같은 map을 적용한다.

## Validation 결과

| scope | 후보 | segment 기준 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `warm` | `baseline` | `none` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |
| `warm` | `corrected_huber_contribution_bins` | `huber_contribution_bins` | `0.2201` | `0.4131` | `1.3071` | `0.6468` |

## 코멘터리

- `huber_contribution_bins`: MdAPE delta `0.0075`, MAPE delta `-0.0036`, p95 delta `-0.0123`.
- usable correction segment: `14`개.
