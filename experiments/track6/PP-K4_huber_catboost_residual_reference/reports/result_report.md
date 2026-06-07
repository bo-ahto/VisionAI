# PP-K4 Huber 선행 + CatBoost residual 보정

- 목적: 기본 후처리 이후 추가 조합 또는 보조 정책이 실제 개선을 주는지 확인한다.
- 기준: 새로 학습한 실험은 validation에서 기준을 정하고 test에 그대로 적용한다. 중복 실험은 기존 PP-L/PP-J 결과를 참조한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `cold` | `B1_Cold_CatBoost` | `reference_to_PP-L3` | `0.4370` | `0.7606` | `2.5140` | `0.7153` |
| `cold` | `B4_cold_Huber_CatBoost_residual` | `reference_to_PP-L3` | `0.4558` | `0.8541` | `3.1908` | `0.7864` |
| `warm` | `B0_Warm_Huber` | `reference_to_PP-L3` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |
| `warm` | `B4_warm_Huber_CatBoost_residual` | `reference_to_PP-L3` | `0.2198` | `0.3752` | `1.2590` | `0.5205` |
