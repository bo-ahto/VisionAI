# PP-I3 보정값 강도 조정

- 목적: 최종 후보로 남길 설정, 보정 강도, 라우팅 기준, 통합 후보를 같은 기준으로 확인한다.
- 기준: validation 기준으로 선택하고 test 결과는 재현성 확인으로만 기록한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `cold` | `cold_catboost_leaf_strength_1.00` | `reference_PP-C5_correction_strength_tuning` | `0.3440` | `0.5876` | `1.8586` | `0.6559` |
| `cold` | `cold_lightgbm_tail_strength_0.25` | `reference_PP-C5_correction_strength_tuning` | `0.3761` | `0.6992` | `2.0255` | `0.6804` |
| `warm` | `warm_tail_strength_0.50` | `reference_PP-C5_correction_strength_tuning` | `0.2056` | `0.4116` | `1.3082` | `0.6420` |
