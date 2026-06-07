# PP-B3 LightGBM 남은 예측 오차 보정

- 목적: 1차 모델이 남긴 오차가 별도 모델로 안정적으로 학습되는지 확인한다.
- 기준: residual 학습 target은 validation 오차가 아니라 train 내부 OOF 예측으로 만든 `actual_log - oof_pred_log`이다.
- 과보정 방지: 2단계 residual 예측값은 로그 기준 `±0.5`로 제한했다.

## Validation 결과

| 모델 소스 | 후보 | 2단계 모델 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `cold_catboost` | `corrected_lightgbm_residual` | `lightgbm` | `0.4166` | `0.6950` | `1.9803` | `0.6938` |
| `cold_catboost` | `baseline` | `none` | `0.4194` | `0.7332` | `2.2053` | `0.7037` |
| `cold_lightgbm` | `corrected_lightgbm_residual` | `lightgbm` | `0.3837` | `0.7306` | `1.9309` | `0.6904` |
| `cold_lightgbm` | `baseline` | `none` | `0.3851` | `0.7169` | `2.0250` | `0.6901` |
| `warm_huber` | `baseline` | `none` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |
| `warm_huber` | `corrected_lightgbm_residual` | `lightgbm` | `0.2241` | `0.4122` | `1.3678` | `0.6124` |

## 코멘터리

- `cold_catboost` `corrected_lightgbm_residual`: baseline 대비 MdAPE `-0.0028`, MAPE `-0.0382`, p95 `-0.2250`.
- `cold_lightgbm` `corrected_lightgbm_residual`: baseline 대비 MdAPE `-0.0014`, MAPE `0.0137`, p95 `-0.0942`.
- `warm_huber` `corrected_lightgbm_residual`: baseline 대비 MdAPE `0.0115`, MAPE `-0.0045`, p95 `0.0485`.
- residual model summary rows: `9`.
