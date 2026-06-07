# PRE-PP-LGB Cold LightGBM group-drop ablation

- 목적: 후처리 보정 기준으로 사용할 피처/구간 그룹의 실제 성능 기여를 확인한다.
- 방법: final artifact 기준 피처셋에서 그룹을 하나씩 제거하고 같은 split/모델 설정으로 재학습한다.
- 해석: 제거 후 성능이 악화되면 해당 그룹은 후처리 segment 기준으로 유지할 근거가 있다.

## Validation 결과

| 후보 | 제거 그룹 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---:|---:|---:|---:|
| `without_drop_size_bucket` | `drop_size_bucket` | `0.3850` | `0.7034` | `1.9659` | `0.6868` |
| `baseline` | `none` | `0.3851` | `0.7169` | `2.0250` | `0.6901` |
| `without_drop_support_size` | `drop_support_size` | `0.3897` | `0.7018` | `2.0208` | `0.6869` |
| `without_drop_raw_size` | `drop_raw_size` | `0.4195` | `0.7369` | `2.3103` | `0.7163` |
| `without_drop_depth_3d` | `drop_depth_3d` | `0.4255` | `0.8698` | `2.6844` | `0.7583` |

## 코멘터리

- `drop_size_bucket` 제거: MdAPE delta `-0.0001`, p95 delta `-0.0592`로 `개선`. 악화라면 해당 그룹은 보정 기준으로 남길 근거가 있다.
- `drop_support_size` 제거: MdAPE delta `0.0046`, p95 delta `-0.0043`로 `악화`. 악화라면 해당 그룹은 보정 기준으로 남길 근거가 있다.
- `drop_raw_size` 제거: MdAPE delta `0.0344`, p95 delta `0.2852`로 `악화`. 악화라면 해당 그룹은 보정 기준으로 남길 근거가 있다.
- `drop_depth_3d` 제거: MdAPE delta `0.0404`, p95 delta `0.6594`로 `악화`. 악화라면 해당 그룹은 보정 기준으로 남길 근거가 있다.
