# PRE-SPLIT-CCB Cold CatBoost 구분 학습

## Validation 결과

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---:|---:|---:|---:|
| `segmented_by_medium_shape_bucket` | `0.3784` | `0.6960` | `2.0670` | `0.6961` |
| `segmented_by_depth_3d_segment` | `0.4081` | `0.7216` | `2.1309` | `0.6973` |
| `segmented_by_size_bucket` | `0.4106` | `0.7498` | `2.4032` | `0.7197` |
| `baseline_catboost` | `0.4194` | `0.7332` | `2.2053` | `0.7037` |

## 코멘터리

- 조건별 구분 학습이 baseline보다 나아지면 PP-J/PP-E의 조건별 보정 또는 라우팅 근거로 사용한다.
- segment model 사용 구간: `18`개.
