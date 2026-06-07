# PP-J3 Warm CatBoost leaf/artist-size 보정

- 목적: 모델 구조에 맞춘 segment 기준으로 residual 보정 후보를 검증한다.
- 기준: validation residual로 correction map을 만들고 test에는 같은 map을 적용한다.

## Validation 결과

| scope | 후보 | segment 기준 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `warm` | `baseline` | `none` | `0.2912` | `0.4063` | `1.2508` | `0.5530` |
| `warm` | `corrected_warm_catboost_leaf_artist_size` | `warm_catboost_leaf_artist_size` | `0.2912` | `0.4063` | `1.2508` | `0.5530` |

## 코멘터리

- `warm_catboost_leaf_artist_size`: MdAPE delta `0.0000`, MAPE delta `0.0000`, p95 delta `0.0000`.
- usable correction segment: `0`개.
