# PP-K10 Huber + Quantile 위험도 기반 CatBoost 라우팅

- 목적: 기본 후처리 이후 추가 조합 또는 보조 정책이 실제 개선을 주는지 확인한다.
- 기준: 새로 학습한 실험은 validation에서 기준을 정하고 test에 그대로 적용한다. 중복 실험은 기존 PP-L/PP-J 결과를 참조한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `cold` | `PP-L8_cold_quantile_features_huber_catboost_residual` | `reference_to_PP-L8` | `0.4277` | `0.7485` | `2.3124` | `0.7292` |
| `cold` | `B1_Cold_CatBoost` | `reference_to_PP-L8` | `0.4370` | `0.7606` | `2.5140` | `0.7153` |
| `warm` | `PP-L8_warm_quantile_features_huber_catboost_residual` | `reference_to_PP-L8` | `0.1808` | `0.3152` | `0.9341` | `0.4285` |
| `warm` | `B0_Warm_Huber` | `reference_to_PP-L8` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |
