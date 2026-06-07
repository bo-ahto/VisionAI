# PP-I4 조건별 모델 선택 기준 조정

- 목적: 최종 후보로 남길 설정, 보정 강도, 라우팅 기준, 통합 후보를 같은 기준으로 확인한다.
- 기준: validation 기준으로 선택하고 test 결과는 재현성 확인으로만 기록한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `cold` | `cold_pred_risk_routing_reference` | `reference_PP-E5_pred_price_risk_routing` | `0.3378` | `0.6019` | `1.9344` | `0.6633` |
| `cold` | `cold_extreme_size_routing_reference` | `reference_PP-E3_extreme_size_routing` | `0.3440` | `0.5787` | `1.7804` | `0.6552` |
| `warm` | `warm_artist_history_routing` | `reference_PP-E1_warm_low_history_routing` | `0.1644` | `0.2887` | `0.8346` | `0.4100` |
