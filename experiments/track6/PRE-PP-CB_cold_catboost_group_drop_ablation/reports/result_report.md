# PRE-PP-CB Cold CatBoost group-drop ablation

- 목적: 후처리 보정 기준으로 사용할 피처/구간 그룹의 실제 성능 기여를 확인한다.
- 방법: final artifact 기준 피처셋에서 그룹을 하나씩 제거하고 같은 split/모델 설정으로 재학습한다.
- 해석: 제거 후 성능이 악화되면 해당 그룹은 후처리 segment 기준으로 유지할 근거가 있다.

## Validation 결과

| 후보 | 제거 그룹 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---:|---:|---:|---:|
| `baseline` | `none` | `0.4194` | `0.7332` | `2.2053` | `0.7037` |
| `without_drop_medium_shape` | `drop_medium_shape` | `0.4346` | `0.7517` | `2.3929` | `0.7127` |
| `without_drop_shape` | `drop_shape` | `0.4394` | `0.7513` | `2.3700` | `0.7190` |
| `without_drop_depth_3d` | `drop_depth_3d` | `0.4723` | `0.8685` | `3.3281` | `0.7639` |
| `without_drop_size` | `drop_size` | `0.5826` | `1.2685` | `6.3186` | `1.0344` |

## 코멘터리

- `drop_medium_shape` 제거: MdAPE delta `0.0153`, p95 delta `0.1876`로 `악화`. 악화라면 해당 그룹은 보정 기준으로 남길 근거가 있다.
- `drop_shape` 제거: MdAPE delta `0.0200`, p95 delta `0.1647`로 `악화`. 악화라면 해당 그룹은 보정 기준으로 남길 근거가 있다.
- `drop_depth_3d` 제거: MdAPE delta `0.0529`, p95 delta `1.1228`로 `악화`. 악화라면 해당 그룹은 보정 기준으로 남길 근거가 있다.
- `drop_size` 제거: MdAPE delta `0.1632`, p95 delta `4.1132`로 `악화`. 악화라면 해당 그룹은 보정 기준으로 남길 근거가 있다.
