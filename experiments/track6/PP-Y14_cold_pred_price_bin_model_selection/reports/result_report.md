# PP-Y14 Cold 예측 가격대별 모델 선택

- 목적: Cold 추가 실험 여지를 줄이기 위해 남은 피처/목적함수/라우팅/보정 축을 닫는다.
- 기준: 기존 split과 기존 PP-Y 강한 후보를 유지하고 validation/test를 함께 기록한다.

## Test 결과 상위

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 정책 |
|---|---:|---:|---:|---:|---|
| `low_y10mdape_mid_y2_high_y10p95` | 0.4344 | 1.0526 | 3.3537 | 0.8616 | `pred_price_bin_model_selection` |
| `low_y10p95_mid_y10mdape_high_y2` | 0.4346 | 1.0478 | 3.0783 | 0.8534 | `pred_price_bin_model_selection` |
| `low_y2_mid_y10mdape_high_y10p95` | 0.4417 | 1.0546 | 3.0591 | 0.8645 | `pred_price_bin_model_selection` |

## 설정/피처 맵

| experiment_id | candidate | low_source | mid_source | high_source | edge_low_mid | edge_mid_high |
| --- | --- | --- | --- | --- | --- | --- |
| PP-Y14 | low_y10p95_mid_y10mdape_high_y2 | y10_p95_route | y10_mdape_route | y2_search_external_interaction | 14.3306 | 15.1667 |
| PP-Y14 | low_y2_mid_y10mdape_high_y10p95 | y2_search_external_interaction | y10_mdape_route | y10_p95_route | 14.3306 | 15.1667 |
| PP-Y14 | low_y10mdape_mid_y2_high_y10p95 | y10_mdape_route | y2_search_external_interaction | y10_p95_route | 14.3306 | 15.1667 |
