# PP-B2 Huber 남은 예측 오차 보정

- 목적: 1차 모델이 남긴 오차가 별도 모델로 안정적으로 학습되는지 확인한다.
- 기준: residual 학습 target은 validation 오차가 아니라 train 내부 OOF 예측으로 만든 `actual_log - oof_pred_log`이다.
- 과보정 방지: 2단계 residual 예측값은 로그 기준 `±0.5`로 제한했다.

## Validation 결과

| 모델 소스 | 후보 | 2단계 모델 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `cold_catboost` | `corrected_huber_residual` | `huber` | `0.4116` | `0.6983` | `1.9528` | `0.7049` |
| `cold_catboost` | `baseline` | `none` | `0.4194` | `0.7332` | `2.2053` | `0.7037` |
| `cold_lightgbm` | `baseline` | `none` | `0.3851` | `0.7169` | `2.0250` | `0.6901` |
| `cold_lightgbm` | `corrected_huber_residual` | `huber` | `0.3880` | `0.7323` | `2.0493` | `0.7026` |
| `warm_huber` | `baseline` | `none` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |
| `warm_huber` | `corrected_huber_residual` | `huber` | `0.2435` | `0.4252` | `1.3242` | `0.6461` |

## 코멘터리

- `cold_catboost` `corrected_huber_residual`: baseline 대비 MdAPE `-0.0078`, MAPE `-0.0349`, p95 `-0.2525`.
- `cold_lightgbm` `corrected_huber_residual`: baseline 대비 MdAPE `0.0029`, MAPE `0.0154`, p95 `0.0242`.
- `warm_huber` `corrected_huber_residual`: baseline 대비 MdAPE `0.0309`, MAPE `0.0085`, p95 `0.0049`.
- residual model summary rows: `9`.
