# PP-P1 Warm/Cold 최종 후보 라우팅 통합

- 목적: 모델별 장점을 분리해 추가 개선 가능성을 확인한다.
- 기준: validation에서 후보를 판단하고 test는 재현성 확인으로 기록한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log | 추가정보 |
|---|---|---|---:|---:|---:|---:|---|
| `cold` | `cold_aux_a7_hierarchical` | `final_policy_component` | `0.3567` | `0.5662` | `1.6593` | `0.6616` |  |
| `cold` | `cold_baseline_lightgbm` | `final_policy_component` | `0.3851` | `0.7169` | `2.0250` | `0.6901` |  |
| `warm` | `warm_pp_d4_integrated` | `final_policy_component` | `0.1687` | `0.3053` | `0.9460` | `0.4440` |  |
