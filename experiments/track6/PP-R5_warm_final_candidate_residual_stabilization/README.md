# PP-R5 Warm 최종 후보 잔차 안정화

- 목적: PP-Q 이후 남은 개선 여지를 모델 조합, 단계 보정, 라우팅, 메타 보정으로 확인한다.
- 기준: 가중치, 보정값, threshold, meta 모델은 validation에서만 정하고 test에는 그대로 적용한다.

## Metrics

| 후보 | scope | split | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---|---:|---:|---:|---:|
| `warm_residual_stabilized_p95_guarded` | `warm` | `test` | `warm_final_candidate_residual_stabilization` | `0.1707` | `0.3278` | `1.1107` | `0.4381` |
| `warm_residual_stabilized_mape_guarded` | `warm` | `test` | `warm_final_candidate_residual_stabilization` | `0.1713` | `0.3271` | `1.1069` | `0.4382` |
| `warm_residual_stabilized_mdape` | `warm` | `test` | `warm_final_candidate_residual_stabilization` | `0.1725` | `0.3283` | `1.1241` | `0.4384` |
| `base_pp_d4_warm` | `warm` | `test` | `stage0_warm_best_candidate` | `0.1760` | `0.3293` | `1.1248` | `0.4387` |
| `warm_residual_stabilized_mdape` | `warm` | `validation` | `warm_final_candidate_residual_stabilization` | `0.1634` | `0.3039` | `0.9453` | `0.4432` |
| `base_pp_d4_warm` | `warm` | `validation` | `stage0_warm_best_candidate` | `0.1687` | `0.3053` | `0.9460` | `0.4440` |
| `warm_residual_stabilized_mape_guarded` | `warm` | `validation` | `warm_final_candidate_residual_stabilization` | `0.1688` | `0.2992` | `0.9268` | `0.4405` |
| `warm_residual_stabilized_p95_guarded` | `warm` | `validation` | `warm_final_candidate_residual_stabilization` | `0.1710` | `0.3021` | `0.9268` | `0.4418` |
