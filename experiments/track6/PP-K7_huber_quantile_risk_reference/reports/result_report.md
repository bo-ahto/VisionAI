# PP-K7 Huber + Quantile 위험 구간 보정

- 목적: 기본 후처리 이후 추가 조합 또는 보조 정책이 실제 개선을 주는지 확인한다.
- 기준: 새로 학습한 실험은 validation에서 기준을 정하고 test에 그대로 적용한다. 중복 실험은 기존 PP-L/PP-J 결과를 참조한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `cold` | `PP-L4_cold_Huber_quantile_width_segment_median` | `reference_to_PP-L4` | `0.4026` | `0.6063` | `1.8607` | `0.7282` |
| `cold` | `B1_Cold_CatBoost` | `reference_to_PP-L4` | `0.4370` | `0.7606` | `2.5140` | `0.7153` |
| `warm` | `B0_Warm_Huber` | `reference_to_PP-L4` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |
| `warm` | `PP-L4_warm_Huber_quantile_width_segment_median` | `reference_to_PP-L4` | `0.2167` | `0.4116` | `1.3235` | `0.6462` |
