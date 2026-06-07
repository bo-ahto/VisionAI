# PP-B1 Ridge 남은 예측 오차 보정

- 목적: 1차 모델이 남긴 오차가 별도 모델로 안정적으로 학습되는지 확인한다.
- 기준: residual 학습 target은 validation 오차가 아니라 train 내부 OOF 예측으로 만든 `actual_log - oof_pred_log`이다.
- 과보정 방지: 2단계 residual 예측값은 로그 기준 `±0.5`로 제한했다.

## Validation 결과

| 모델 소스 | 후보 | 2단계 모델 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `cold_catboost` | `corrected_ridge_residual` | `ridge` | `0.4112` | `0.7255` | `2.0447` | `0.7075` |
| `cold_catboost` | `baseline` | `none` | `0.4194` | `0.7332` | `2.2053` | `0.7037` |
| `cold_lightgbm` | `corrected_ridge_residual` | `ridge` | `0.3843` | `0.7466` | `2.0684` | `0.7036` |
| `cold_lightgbm` | `baseline` | `none` | `0.3851` | `0.7169` | `2.0250` | `0.6901` |
| `warm_huber` | `baseline` | `none` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |
| `warm_huber` | `corrected_ridge_residual` | `ridge` | `0.2658` | `0.4691` | `1.5367` | `0.6330` |

## 코멘터리

- `cold_catboost` `corrected_ridge_residual`: baseline 대비 MdAPE `-0.0081`, MAPE `-0.0077`, p95 `-0.1606`.
- `cold_lightgbm` `corrected_ridge_residual`: baseline 대비 MdAPE `-0.0008`, MAPE `0.0297`, p95 `0.0433`.
- `warm_huber` `corrected_ridge_residual`: baseline 대비 MdAPE `0.0532`, MAPE `0.0525`, p95 `0.2173`.
- residual model summary rows: `9`.
