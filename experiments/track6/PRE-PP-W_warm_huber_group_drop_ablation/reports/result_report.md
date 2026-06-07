# PRE-PP-W Warm Huber group-drop ablation

- 목적: 후처리 보정 기준으로 사용할 피처/구간 그룹의 실제 성능 기여를 확인한다.
- 방법: final artifact 기준 피처셋에서 그룹을 하나씩 제거하고 같은 split/모델 설정으로 재학습한다.
- 해석: 제거 후 성능이 악화되면 해당 그룹은 후처리 segment 기준으로 유지할 근거가 있다.

## Validation 결과

| 후보 | 제거 그룹 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---:|---:|---:|---:|
| `baseline` | `none` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |
| `without_drop_shape_aspect` | `drop_shape_aspect` | `0.2162` | `0.4161` | `1.2950` | `0.6448` |
| `without_drop_depth_3d` | `drop_depth_3d` | `0.2167` | `0.4216` | `1.4209` | `0.6432` |
| `without_drop_medium_support` | `drop_medium_support` | `0.2170` | `0.4450` | `1.3546` | `0.6651` |
| `without_drop_size` | `drop_size` | `0.5671` | `1.2145` | `4.9148` | `1.0538` |

## 코멘터리

- `drop_shape_aspect` 제거: MdAPE delta `0.0036`, p95 delta `-0.0243`로 `악화`. 악화라면 해당 그룹은 보정 기준으로 남길 근거가 있다.
- `drop_depth_3d` 제거: MdAPE delta `0.0041`, p95 delta `0.1015`로 `악화`. 악화라면 해당 그룹은 보정 기준으로 남길 근거가 있다.
- `drop_medium_support` 제거: MdAPE delta `0.0044`, p95 delta `0.0353`로 `악화`. 악화라면 해당 그룹은 보정 기준으로 남길 근거가 있다.
- `drop_size` 제거: MdAPE delta `0.3545`, p95 delta `3.5954`로 `악화`. 악화라면 해당 그룹은 보정 기준으로 남길 근거가 있다.
