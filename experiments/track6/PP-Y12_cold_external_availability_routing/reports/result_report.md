# PP-Y12 Cold 전시/갤러리 사용 여부 라우팅

- 목적: Cold 추가 실험 여지를 줄이기 위해 남은 피처/목적함수/라우팅/보정 축을 닫는다.
- 기준: 기존 split과 기존 PP-Y 강한 후보를 유지하고 validation/test를 함께 기록한다.

## Test 결과 상위

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 정책 |
|---|---:|---:|---:|---:|---|
| `external_available_minexh1_else_h9_search_p95` | 0.4344 | 1.0539 | 3.1004 | 0.8563 | `external_availability_routing` |
| `external_available_minexh2_else_h9_search_p95` | 0.4344 | 1.0539 | 3.1004 | 0.8563 | `external_availability_routing` |
| `external_available_minexh3_else_h9_search_p95` | 0.4344 | 1.0539 | 3.1004 | 0.8563 | `external_availability_routing` |
| `external_available_minexh1_else_w4_p95` | 0.4549 | 1.0709 | 3.1120 | 0.8813 | `external_availability_routing` |
| `external_available_minexh2_else_w4_p95` | 0.4549 | 1.0709 | 3.1120 | 0.8813 | `external_availability_routing` |
| `external_available_minexh3_else_w4_p95` | 0.4549 | 1.0709 | 3.1120 | 0.8813 | `external_availability_routing` |

## 설정/피처 맵

| experiment_id | candidate | risk_source | min_exhibition_available |
| --- | --- | --- | --- |
| PP-Y12 | external_available_minexh1_else_h9_search_p95 | h9_search_p95 | 1 |
| PP-Y12 | external_available_minexh2_else_h9_search_p95 | h9_search_p95 | 2 |
| PP-Y12 | external_available_minexh3_else_h9_search_p95 | h9_search_p95 | 3 |
| PP-Y12 | external_available_minexh1_else_w4_p95 | w4_p95 | 1 |
| PP-Y12 | external_available_minexh2_else_w4_p95 | w4_p95 | 2 |
| PP-Y12 | external_available_minexh3_else_w4_p95 | w4_p95 | 3 |
