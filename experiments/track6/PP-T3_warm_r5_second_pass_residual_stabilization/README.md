# PP-T3 Warm PP-R5 2차 residual 안정화

- 목적: Warm 최종 후보 PP-R5 이후에도 조합, 메타 보정, 2차 residual 안정화로 개선 여지가 있는지 확인한다.
- 기준: 가중치, meta 모델, 보정값, 정책 선택은 validation에서 정하고 test에는 그대로 적용한다.

| 후보 | split | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `second_pass_mdape` | `test` | `warm_r5_second_pass_residual` | `0.1644` | `0.3258` | `1.1109` | `0.4382` |
| `second_pass_p95_guarded` | `test` | `warm_r5_second_pass_residual` | `0.1667` | `0.3266` | `1.1109` | `0.4381` |
| `second_pass_mape_guarded` | `test` | `warm_r5_second_pass_residual` | `0.1690` | `0.3274` | `1.0878` | `0.4386` |
| `base_r5_p95` | `test` | `stage0_r5` | `0.1707` | `0.3278` | `1.1107` | `0.4381` |
| `second_pass_mdape` | `validation` | `warm_r5_second_pass_residual` | `0.1645` | `0.2990` | `0.9218` | `0.4401` |
| `second_pass_p95_guarded` | `validation` | `warm_r5_second_pass_residual` | `0.1648` | `0.3001` | `0.9218` | `0.4404` |
| `second_pass_mape_guarded` | `validation` | `warm_r5_second_pass_residual` | `0.1659` | `0.2975` | `0.9457` | `0.4387` |
| `base_r5_p95` | `validation` | `stage0_r5` | `0.1710` | `0.3021` | `0.9268` | `0.4418` |
