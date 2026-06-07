# PP-Y15 Cold segment 최소 표본 수/cap 보정

- 목적: Cold 추가 실험 여지를 줄이기 위해 남은 피처/목적함수/라우팅/보정 축을 닫는다.
- 기준: 기존 split과 기존 PP-Y 강한 후보를 유지하고 validation/test를 함께 기록한다.

## Test 결과 상위

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 정책 |
|---|---:|---:|---:|---:|---|
| `y2_search_external_interaction_external_x_qwidth_min30_cap0.1` | 0.4245 | 1.0668 | 3.4110 | 0.8593 | `segment_min_rows_cap_calibration` |
| `y2_search_external_interaction_external_x_qwidth_min50_cap0.1` | 0.4264 | 1.0677 | 3.4110 | 0.8578 | `segment_min_rows_cap_calibration` |
| `y2_search_external_interaction_external_x_qwidth_min100_cap0.1` | 0.4264 | 1.0677 | 3.4110 | 0.8578 | `segment_min_rows_cap_calibration` |
| `y2_search_external_interaction_external_x_qwidth_min150_cap0.1` | 0.4264 | 1.0677 | 3.4110 | 0.8578 | `segment_min_rows_cap_calibration` |
| `y2_search_external_interaction_external_x_qwidth_min30_cap0.15` | 0.4266 | 1.0850 | 3.4110 | 0.8641 | `segment_min_rows_cap_calibration` |
| `y2_search_external_interaction_external_x_qwidth_min50_cap0.15` | 0.4267 | 1.0860 | 3.4110 | 0.8624 | `segment_min_rows_cap_calibration` |
| `y2_search_external_interaction_external_x_qwidth_min100_cap0.15` | 0.4267 | 1.0860 | 3.4110 | 0.8624 | `segment_min_rows_cap_calibration` |
| `y2_search_external_interaction_external_x_qwidth_min150_cap0.15` | 0.4267 | 1.0860 | 3.4110 | 0.8624 | `segment_min_rows_cap_calibration` |
| `y2_search_external_interaction_external_x_qwidth_min30_cap0.25` | 0.4267 | 1.1349 | 3.4110 | 0.8761 | `segment_min_rows_cap_calibration` |
| `y2_search_external_interaction_external_x_qwidth_min50_cap0.25` | 0.4267 | 1.1359 | 3.4110 | 0.8744 | `segment_min_rows_cap_calibration` |
| `y2_search_external_interaction_external_x_qwidth_min100_cap0.25` | 0.4267 | 1.1359 | 3.4110 | 0.8744 | `segment_min_rows_cap_calibration` |
| `y2_search_external_interaction_external_x_qwidth_min150_cap0.25` | 0.4267 | 1.1359 | 3.4110 | 0.8744 | `segment_min_rows_cap_calibration` |
| `y2_search_external_interaction_qwidth_bin_min30_cap0.25` | 0.4269 | 1.1260 | 3.3053 | 0.8775 | `segment_min_rows_cap_calibration` |
| `y2_search_external_interaction_qwidth_bin_min50_cap0.25` | 0.4269 | 1.1260 | 3.3053 | 0.8775 | `segment_min_rows_cap_calibration` |
| `y2_search_external_interaction_qwidth_bin_min100_cap0.25` | 0.4269 | 1.1260 | 3.3053 | 0.8775 | `segment_min_rows_cap_calibration` |
| `y2_search_external_interaction_qwidth_bin_min150_cap0.25` | 0.4269 | 1.1260 | 3.3053 | 0.8775 | `segment_min_rows_cap_calibration` |
| `y2_search_external_interaction_qwidth_bin_min30_cap0.1` | 0.4280 | 1.0628 | 3.3053 | 0.8600 | `segment_min_rows_cap_calibration` |
| `y2_search_external_interaction_qwidth_bin_min50_cap0.1` | 0.4280 | 1.0628 | 3.3053 | 0.8600 | `segment_min_rows_cap_calibration` |
| `y2_search_external_interaction_qwidth_bin_min100_cap0.1` | 0.4280 | 1.0628 | 3.3053 | 0.8600 | `segment_min_rows_cap_calibration` |
| `y2_search_external_interaction_qwidth_bin_min150_cap0.1` | 0.4280 | 1.0628 | 3.3053 | 0.8600 | `segment_min_rows_cap_calibration` |

## 설정/피처 맵

| experiment_id | candidate | source | segment | min_rows | cap |
| --- | --- | --- | --- | --- | --- |
| PP-Y15 | y2_search_external_interaction_pred_bin_min30_cap0.1 | y2_search_external_interaction | pred_bin | 30 | 0.1 |
| PP-Y15 | y2_search_external_interaction_pred_bin_min30_cap0.15 | y2_search_external_interaction | pred_bin | 30 | 0.15 |
| PP-Y15 | y2_search_external_interaction_pred_bin_min30_cap0.25 | y2_search_external_interaction | pred_bin | 30 | 0.25 |
| PP-Y15 | y2_search_external_interaction_pred_bin_min30_cap0.35 | y2_search_external_interaction | pred_bin | 30 | 0.35 |
| PP-Y15 | y2_search_external_interaction_pred_bin_min50_cap0.1 | y2_search_external_interaction | pred_bin | 50 | 0.1 |
| PP-Y15 | y2_search_external_interaction_pred_bin_min50_cap0.15 | y2_search_external_interaction | pred_bin | 50 | 0.15 |
| PP-Y15 | y2_search_external_interaction_pred_bin_min50_cap0.25 | y2_search_external_interaction | pred_bin | 50 | 0.25 |
| PP-Y15 | y2_search_external_interaction_pred_bin_min50_cap0.35 | y2_search_external_interaction | pred_bin | 50 | 0.35 |
| PP-Y15 | y2_search_external_interaction_pred_bin_min100_cap0.1 | y2_search_external_interaction | pred_bin | 100 | 0.1 |
| PP-Y15 | y2_search_external_interaction_pred_bin_min100_cap0.15 | y2_search_external_interaction | pred_bin | 100 | 0.15 |
| PP-Y15 | y2_search_external_interaction_pred_bin_min100_cap0.25 | y2_search_external_interaction | pred_bin | 100 | 0.25 |
| PP-Y15 | y2_search_external_interaction_pred_bin_min100_cap0.35 | y2_search_external_interaction | pred_bin | 100 | 0.35 |
| PP-Y15 | y2_search_external_interaction_pred_bin_min150_cap0.1 | y2_search_external_interaction | pred_bin | 150 | 0.1 |
| PP-Y15 | y2_search_external_interaction_pred_bin_min150_cap0.15 | y2_search_external_interaction | pred_bin | 150 | 0.15 |
| PP-Y15 | y2_search_external_interaction_pred_bin_min150_cap0.25 | y2_search_external_interaction | pred_bin | 150 | 0.25 |
| PP-Y15 | y2_search_external_interaction_pred_bin_min150_cap0.35 | y2_search_external_interaction | pred_bin | 150 | 0.35 |
| PP-Y15 | y2_search_external_interaction_qwidth_bin_min30_cap0.1 | y2_search_external_interaction | qwidth_bin | 30 | 0.1 |
| PP-Y15 | y2_search_external_interaction_qwidth_bin_min30_cap0.15 | y2_search_external_interaction | qwidth_bin | 30 | 0.15 |
| PP-Y15 | y2_search_external_interaction_qwidth_bin_min30_cap0.25 | y2_search_external_interaction | qwidth_bin | 30 | 0.25 |
| PP-Y15 | y2_search_external_interaction_qwidth_bin_min30_cap0.35 | y2_search_external_interaction | qwidth_bin | 30 | 0.35 |
| PP-Y15 | y2_search_external_interaction_qwidth_bin_min50_cap0.1 | y2_search_external_interaction | qwidth_bin | 50 | 0.1 |
| PP-Y15 | y2_search_external_interaction_qwidth_bin_min50_cap0.15 | y2_search_external_interaction | qwidth_bin | 50 | 0.15 |
| PP-Y15 | y2_search_external_interaction_qwidth_bin_min50_cap0.25 | y2_search_external_interaction | qwidth_bin | 50 | 0.25 |
| PP-Y15 | y2_search_external_interaction_qwidth_bin_min50_cap0.35 | y2_search_external_interaction | qwidth_bin | 50 | 0.35 |
| PP-Y15 | y2_search_external_interaction_qwidth_bin_min100_cap0.1 | y2_search_external_interaction | qwidth_bin | 100 | 0.1 |
| PP-Y15 | y2_search_external_interaction_qwidth_bin_min100_cap0.15 | y2_search_external_interaction | qwidth_bin | 100 | 0.15 |
| PP-Y15 | y2_search_external_interaction_qwidth_bin_min100_cap0.25 | y2_search_external_interaction | qwidth_bin | 100 | 0.25 |
| PP-Y15 | y2_search_external_interaction_qwidth_bin_min100_cap0.35 | y2_search_external_interaction | qwidth_bin | 100 | 0.35 |
| PP-Y15 | y2_search_external_interaction_qwidth_bin_min150_cap0.1 | y2_search_external_interaction | qwidth_bin | 150 | 0.1 |
| PP-Y15 | y2_search_external_interaction_qwidth_bin_min150_cap0.15 | y2_search_external_interaction | qwidth_bin | 150 | 0.15 |
| PP-Y15 | y2_search_external_interaction_qwidth_bin_min150_cap0.25 | y2_search_external_interaction | qwidth_bin | 150 | 0.25 |
| PP-Y15 | y2_search_external_interaction_qwidth_bin_min150_cap0.35 | y2_search_external_interaction | qwidth_bin | 150 | 0.35 |
| PP-Y15 | y2_search_external_interaction_pred_x_qwidth_min30_cap0.1 | y2_search_external_interaction | pred_x_qwidth | 30 | 0.1 |
| PP-Y15 | y2_search_external_interaction_pred_x_qwidth_min30_cap0.15 | y2_search_external_interaction | pred_x_qwidth | 30 | 0.15 |
| PP-Y15 | y2_search_external_interaction_pred_x_qwidth_min30_cap0.25 | y2_search_external_interaction | pred_x_qwidth | 30 | 0.25 |
| PP-Y15 | y2_search_external_interaction_pred_x_qwidth_min30_cap0.35 | y2_search_external_interaction | pred_x_qwidth | 30 | 0.35 |
| PP-Y15 | y2_search_external_interaction_pred_x_qwidth_min50_cap0.1 | y2_search_external_interaction | pred_x_qwidth | 50 | 0.1 |
| PP-Y15 | y2_search_external_interaction_pred_x_qwidth_min50_cap0.15 | y2_search_external_interaction | pred_x_qwidth | 50 | 0.15 |
| PP-Y15 | y2_search_external_interaction_pred_x_qwidth_min50_cap0.25 | y2_search_external_interaction | pred_x_qwidth | 50 | 0.25 |
| PP-Y15 | y2_search_external_interaction_pred_x_qwidth_min50_cap0.35 | y2_search_external_interaction | pred_x_qwidth | 50 | 0.35 |
| PP-Y15 | y2_search_external_interaction_pred_x_qwidth_min100_cap0.1 | y2_search_external_interaction | pred_x_qwidth | 100 | 0.1 |
| PP-Y15 | y2_search_external_interaction_pred_x_qwidth_min100_cap0.15 | y2_search_external_interaction | pred_x_qwidth | 100 | 0.15 |
| PP-Y15 | y2_search_external_interaction_pred_x_qwidth_min100_cap0.25 | y2_search_external_interaction | pred_x_qwidth | 100 | 0.25 |
| PP-Y15 | y2_search_external_interaction_pred_x_qwidth_min100_cap0.35 | y2_search_external_interaction | pred_x_qwidth | 100 | 0.35 |
| PP-Y15 | y2_search_external_interaction_pred_x_qwidth_min150_cap0.1 | y2_search_external_interaction | pred_x_qwidth | 150 | 0.1 |
| PP-Y15 | y2_search_external_interaction_pred_x_qwidth_min150_cap0.15 | y2_search_external_interaction | pred_x_qwidth | 150 | 0.15 |
| PP-Y15 | y2_search_external_interaction_pred_x_qwidth_min150_cap0.25 | y2_search_external_interaction | pred_x_qwidth | 150 | 0.25 |
| PP-Y15 | y2_search_external_interaction_pred_x_qwidth_min150_cap0.35 | y2_search_external_interaction | pred_x_qwidth | 150 | 0.35 |
| PP-Y15 | y2_search_external_interaction_external_x_qwidth_min30_cap0.1 | y2_search_external_interaction | external_x_qwidth | 30 | 0.1 |
| PP-Y15 | y2_search_external_interaction_external_x_qwidth_min30_cap0.15 | y2_search_external_interaction | external_x_qwidth | 30 | 0.15 |
| PP-Y15 | y2_search_external_interaction_external_x_qwidth_min30_cap0.25 | y2_search_external_interaction | external_x_qwidth | 30 | 0.25 |
| PP-Y15 | y2_search_external_interaction_external_x_qwidth_min30_cap0.35 | y2_search_external_interaction | external_x_qwidth | 30 | 0.35 |
| PP-Y15 | y2_search_external_interaction_external_x_qwidth_min50_cap0.1 | y2_search_external_interaction | external_x_qwidth | 50 | 0.1 |
| PP-Y15 | y2_search_external_interaction_external_x_qwidth_min50_cap0.15 | y2_search_external_interaction | external_x_qwidth | 50 | 0.15 |
| PP-Y15 | y2_search_external_interaction_external_x_qwidth_min50_cap0.25 | y2_search_external_interaction | external_x_qwidth | 50 | 0.25 |
| PP-Y15 | y2_search_external_interaction_external_x_qwidth_min50_cap0.35 | y2_search_external_interaction | external_x_qwidth | 50 | 0.35 |
| PP-Y15 | y2_search_external_interaction_external_x_qwidth_min100_cap0.1 | y2_search_external_interaction | external_x_qwidth | 100 | 0.1 |
| PP-Y15 | y2_search_external_interaction_external_x_qwidth_min100_cap0.15 | y2_search_external_interaction | external_x_qwidth | 100 | 0.15 |
| PP-Y15 | y2_search_external_interaction_external_x_qwidth_min100_cap0.25 | y2_search_external_interaction | external_x_qwidth | 100 | 0.25 |
| PP-Y15 | y2_search_external_interaction_external_x_qwidth_min100_cap0.35 | y2_search_external_interaction | external_x_qwidth | 100 | 0.35 |
| PP-Y15 | y2_search_external_interaction_external_x_qwidth_min150_cap0.1 | y2_search_external_interaction | external_x_qwidth | 150 | 0.1 |
| PP-Y15 | y2_search_external_interaction_external_x_qwidth_min150_cap0.15 | y2_search_external_interaction | external_x_qwidth | 150 | 0.15 |
| PP-Y15 | y2_search_external_interaction_external_x_qwidth_min150_cap0.25 | y2_search_external_interaction | external_x_qwidth | 150 | 0.25 |
| PP-Y15 | y2_search_external_interaction_external_x_qwidth_min150_cap0.35 | y2_search_external_interaction | external_x_qwidth | 150 | 0.35 |
