# PRE-MODEL-CCB Cold CatBoost 적합성 재검증

## Validation 결과

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---:|---:|---:|---:|
| `cold_lightgbm_base_support_size` | `0.3851` | `0.7169` | `2.0250` | `0.6901` |
| `cold_catboost_base_medium_shape` | `0.4194` | `0.7332` | `2.2053` | `0.7037` |

## 코멘터리

- Cold CatBoost와 Cold LightGBM을 같은 split에서 다시 비교해 후속 보정의 기준 모델을 확인한다.
