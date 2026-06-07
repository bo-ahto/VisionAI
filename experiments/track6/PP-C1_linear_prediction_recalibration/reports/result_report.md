# PP-C1 전체 예측값 직선 재보정

- 목적: 예측값 자체를 다시 맞추거나, 이미 효과가 있던 보정값의 강도를 조정해 과보정을 줄인다.
- 기준: 보정식은 validation에서만 확정하고 같은 식을 test에 적용한다.

## Validation 결과

| 모델 소스 | 후보 | 보정 방식 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `cold_catboost` | `corrected_linear_slope_intercept` | `linear_slope_intercept` | `0.4117` | `0.6288` | `1.8263` | `0.6909` |
| `cold_catboost` | `baseline` | `none` | `0.4194` | `0.7332` | `2.2053` | `0.7037` |
| `cold_lightgbm` | `baseline` | `none` | `0.3851` | `0.7169` | `2.0250` | `0.6901` |
| `cold_lightgbm` | `corrected_linear_slope_intercept` | `linear_slope_intercept` | `0.3920` | `0.6501` | `1.7614` | `0.6841` |
| `warm_huber` | `baseline` | `none` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |
| `warm_huber` | `corrected_linear_slope_intercept` | `linear_slope_intercept` | `0.2167` | `0.4340` | `1.4580` | `0.6434` |

## 코멘터리

- `cold_catboost` best `corrected_linear_slope_intercept`: baseline 대비 MdAPE `-0.0076`, MAPE `-0.1045`, p95 `-0.3790`.
- `cold_lightgbm` best `baseline`: baseline 대비 MdAPE `0.0000`, MAPE `0.0000`, p95 `0.0000`.
- `warm_huber` best `baseline`: baseline 대비 MdAPE `0.0000`, MAPE `0.0000`, p95 `0.0000`.
