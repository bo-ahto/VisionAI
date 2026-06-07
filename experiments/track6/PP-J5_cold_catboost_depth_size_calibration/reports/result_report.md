# PP-J5 Cold CatBoost 2D/3D x 크기 보정

- 목적: 모델 구조에 맞춘 segment 기준으로 residual 보정 후보를 검증한다.
- 기준: validation residual로 correction map을 만들고 test에는 같은 map을 적용한다.

## Validation 결과

| scope | 후보 | segment 기준 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `cold` | `corrected_depth_3d_size_medium_shape` | `depth_3d_size_medium_shape` | `0.3873` | `0.6129` | `1.8260` | `0.6740` |
| `cold` | `baseline` | `none` | `0.4194` | `0.7332` | `2.2053` | `0.7037` |

## 코멘터리

- `depth_3d_size_medium_shape`: MdAPE delta `-0.0321`, MAPE delta `-0.1204`, p95 delta `-0.3793`.
- usable correction segment: `21`개.
