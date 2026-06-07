# PP-T1 Warm 후보 fine blend

- 목적: Warm 최종 후보 PP-R5 이후에도 조합, 메타 보정, 2차 residual 안정화로 개선 여지가 있는지 확인한다.
- 기준: 가중치, meta 모델, 보정값, 정책 선택은 validation에서 정하고 test에는 그대로 적용한다.

| 후보 | split | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `fine_blend_mape_guarded` | `test` | `warm_fine_blend` | `0.1621` | `0.3044` | `1.0335` | `0.4220` |
| `fine_blend_mdape` | `test` | `warm_fine_blend` | `0.1668` | `0.3067` | `0.9580` | `0.4241` |
| `fine_blend_p95_guarded` | `test` | `warm_fine_blend` | `0.1695` | `0.3168` | `1.0674` | `0.4399` |
| `component_r5_p95` | `test` | `fine_blend_component` | `0.1707` | `0.3278` | `1.1107` | `0.4381` |
| `component_r5_mape` | `test` | `fine_blend_component` | `0.1713` | `0.3271` | `1.1069` | `0.4382` |
| `component_d4_blend` | `test` | `fine_blend_component` | `0.1760` | `0.3293` | `1.1248` | `0.4387` |
| `component_l8_seq` | `test` | `fine_blend_component` | `0.1777` | `0.3383` | `1.1047` | `0.4479` |
| `component_e1_history` | `test` | `fine_blend_component` | `0.1856` | `0.3579` | `1.3398` | `0.4838` |
| `component_l9_seq` | `test` | `fine_blend_component` | `0.1898` | `0.3636` | `1.0841` | `0.4622` |
| `component_k3_similar` | `test` | `fine_blend_component` | `0.2042` | `0.3499` | `1.2149` | `0.5102` |
| `component_huber` | `test` | `fine_blend_component` | `0.2274` | `0.4952` | `2.0130` | `0.6081` |
| `fine_blend_mdape` | `validation` | `warm_fine_blend` | `0.1495` | `0.2680` | `0.8153` | `0.3993` |
| `fine_blend_mape_guarded` | `validation` | `warm_fine_blend` | `0.1540` | `0.2660` | `0.8047` | `0.3920` |
| `fine_blend_p95_guarded` | `validation` | `warm_fine_blend` | `0.1548` | `0.2711` | `0.7864` | `0.3953` |
| `component_e1_history` | `validation` | `fine_blend_component` | `0.1644` | `0.2887` | `0.8346` | `0.4100` |
| `component_d4_blend` | `validation` | `fine_blend_component` | `0.1687` | `0.3053` | `0.9460` | `0.4440` |
| `component_r5_mape` | `validation` | `fine_blend_component` | `0.1688` | `0.2992` | `0.9268` | `0.4405` |
| `component_r5_p95` | `validation` | `fine_blend_component` | `0.1710` | `0.3021` | `0.9268` | `0.4418` |
| `component_l8_seq` | `validation` | `fine_blend_component` | `0.1808` | `0.3152` | `0.9341` | `0.4285` |
| `component_l9_seq` | `validation` | `fine_blend_component` | `0.1824` | `0.3294` | `1.1614` | `0.4863` |
| `component_k3_similar` | `validation` | `fine_blend_component` | `0.1996` | `0.3672` | `1.1230` | `0.5157` |
| `component_huber` | `validation` | `fine_blend_component` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |
