# PP-K8 Huber + Quantile 중앙 예측 가중 평균

- 목적: 기본 후처리 이후 추가 조합 또는 보조 정책이 실제 개선을 주는지 확인한다.
- 기준: 새로 학습한 실험은 validation에서 기준을 정하고 test에 그대로 적용한다. 중복 실험은 기존 PP-L/PP-J 결과를 참조한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `cold` | `B2_cold_Quantile_q50` | `reference_to_PP-L6` | `0.4188` | `0.7164` | `2.4828` | `0.7193` |
| `cold` | `PP-L6_cold_validation_weighted_ensemble` | `reference_to_PP-L6` | `0.4188` | `0.7164` | `2.4828` | `0.7193` |
| `cold` | `B1_Cold_CatBoost` | `reference_to_PP-L6` | `0.4370` | `0.7606` | `2.5140` | `0.7153` |
| `warm` | `PP-L6_warm_validation_weighted_ensemble` | `reference_to_PP-L6` | `0.1930` | `0.3563` | `1.1304` | `0.5209` |
| `warm` | `B0_Warm_Huber` | `reference_to_PP-L6` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |
| `warm` | `B2_warm_Quantile_q50` | `reference_to_PP-L6` | `0.3231` | `0.4424` | `1.2864` | `0.6058` |
