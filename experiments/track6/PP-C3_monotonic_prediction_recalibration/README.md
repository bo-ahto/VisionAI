# PP-C3 예측 순서를 유지하는 비선형 재보정

- 목적: 예측값 자체를 다시 맞추거나, 이미 효과가 있던 보정값의 강도를 조정해 과보정을 줄인다.
- 기준: 보정식은 validation에서만 확정하고 같은 식을 test에 적용한다.

## Validation 결과

| 모델 소스 | 후보 | 보정 방식 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `cold_catboost` | `corrected_monotonic_isotonic` | `monotonic_isotonic` | `0.3781` | `0.5773` | `1.5357` | `0.6583` |
| `cold_catboost` | `baseline` | `none` | `0.4194` | `0.7332` | `2.2053` | `0.7037` |
| `cold_lightgbm` | `corrected_monotonic_isotonic` | `monotonic_isotonic` | `0.3628` | `0.5863` | `1.7016` | `0.6529` |
| `cold_lightgbm` | `baseline` | `none` | `0.3851` | `0.7169` | `2.0250` | `0.6901` |
| `warm_huber` | `baseline` | `none` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |
| `warm_huber` | `corrected_monotonic_isotonic` | `monotonic_isotonic` | `0.2270` | `0.4141` | `1.3576` | `0.6150` |

## 코멘터리

- `cold_catboost` best `corrected_monotonic_isotonic`: baseline 대비 MdAPE `-0.0413`, MAPE `-0.1559`, p95 `-0.6696`.
- `cold_lightgbm` best `corrected_monotonic_isotonic`: baseline 대비 MdAPE `-0.0223`, MAPE `-0.1306`, p95 `-0.3234`.
- `warm_huber` best `baseline`: baseline 대비 MdAPE `0.0000`, MAPE `0.0000`, p95 `0.0000`.
