# PP-Y13 Cold 검색 품질 기반 fallback

- 목적: Cold 추가 실험 여지를 줄이기 위해 남은 피처/목적함수/라우팅/보정 축을 닫는다.
- 기준: 기존 split과 기존 PP-Y 강한 후보를 유지하고 validation/test를 함께 기록한다.

## Test 결과 상위

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 정책 |
|---|---:|---:|---:|---:|---|
| `route_y2_search_external_interaction_to_w4_p95_y2_search_external_interaction_search_quality_score_gte_0.000` | 0.4421 | 1.0484 | 3.3537 | 0.8567 | `search_quality_fallback` |
| `route_y2_search_external_interaction_to_w4_p95_y2_search_external_interaction_search_quality_score_gte_0.090` | 0.4492 | 1.0614 | 2.9656 | 0.8588 | `search_quality_fallback` |
| `route_y2_search_external_interaction_to_w4_p95_y2_search_external_interaction_search_quality_score_gte_0.210` | 0.4602 | 1.0733 | 3.0322 | 0.8850 | `search_quality_fallback` |

## 설정/피처 맵

| experiment_id | candidate | stable_source | risk_source | score_col | threshold | direction |
| --- | --- | --- | --- | --- | --- | --- |
| PP-Y13 | route_y2_search_external_interaction_to_w4_p95_y2_search_external_interaction_search_quality_score_gte_0.000 | y2_search_external_interaction | w4_p95 | y2_search_external_interaction_search_quality_score | 0 | gte |
| PP-Y13 | route_y2_search_external_interaction_to_w4_p95_y2_search_external_interaction_search_quality_score_gte_0.090 | y2_search_external_interaction | w4_p95 | y2_search_external_interaction_search_quality_score | 0.09 | gte |
| PP-Y13 | route_y2_search_external_interaction_to_w4_p95_y2_search_external_interaction_search_quality_score_gte_0.210 | y2_search_external_interaction | w4_p95 | y2_search_external_interaction_search_quality_score | 0.21 | gte |
