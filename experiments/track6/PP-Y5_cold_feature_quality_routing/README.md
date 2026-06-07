# PP-Y5 Cold 피처 가용성/품질 기반 라우팅

- 목적: Cold 추가 실험 여지를 줄이기 위해 남은 피처/목적함수/라우팅/보정 축을 닫는다.
- 기준: 기존 split과 기존 PP-Y 강한 후보를 유지하고 validation/test를 함께 기록한다.

## Test 결과 상위

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 정책 |
|---|---:|---:|---:|---:|---|
| `route_y2_by_feature_quality_to_h9_search_p95_0.650` | 0.4489 | 1.0506 | 2.9954 | 0.8622 | `feature_quality_routing` |
| `route_y2_by_feature_quality_to_h9_search_p95_0.850` | 0.4599 | 1.0577 | 2.9954 | 0.8649 | `feature_quality_routing` |
| `route_y2_by_feature_quality_to_h9_search_p95_0.890` | 0.4599 | 1.0577 | 2.9954 | 0.8649 | `feature_quality_routing` |
| `route_y2_by_feature_quality_to_h9_search_p95_1.010` | 0.4605 | 1.0338 | 2.9954 | 0.8619 | `feature_quality_routing` |
| `route_y2_by_feature_quality_to_w4_p95_0.650` | 0.4668 | 1.0684 | 2.9656 | 0.8874 | `feature_quality_routing` |
| `route_y2_by_feature_quality_to_w4_p95_1.010` | 0.4753 | 1.0828 | 3.0322 | 0.8923 | `feature_quality_routing` |
| `route_y2_by_feature_quality_to_w4_p95_0.850` | 0.4763 | 1.0789 | 2.9720 | 0.8889 | `feature_quality_routing` |
| `route_y2_by_feature_quality_to_w4_p95_0.890` | 0.4763 | 1.0789 | 2.9720 | 0.8889 | `feature_quality_routing` |

## 설정/피처 맵

| experiment_id | candidate | stable_source | risk_source | threshold | score |
| --- | --- | --- | --- | --- | --- |
| PP-Y5 | route_y2_by_feature_quality_to_h9_search_p95_0.650 | y2_search_external_interaction | h9_search_p95 | 0.65 | search_quality_score + 0.35*gallery_available + 0.15*exhibition_available_count |
| PP-Y5 | route_y2_by_feature_quality_to_h9_search_p95_0.850 | y2_search_external_interaction | h9_search_p95 | 0.85 | search_quality_score + 0.35*gallery_available + 0.15*exhibition_available_count |
| PP-Y5 | route_y2_by_feature_quality_to_h9_search_p95_0.890 | y2_search_external_interaction | h9_search_p95 | 0.89 | search_quality_score + 0.35*gallery_available + 0.15*exhibition_available_count |
| PP-Y5 | route_y2_by_feature_quality_to_h9_search_p95_1.010 | y2_search_external_interaction | h9_search_p95 | 1.01 | search_quality_score + 0.35*gallery_available + 0.15*exhibition_available_count |
| PP-Y5 | route_y2_by_feature_quality_to_w4_p95_0.650 | y2_search_external_interaction | w4_p95 | 0.65 | search_quality_score + 0.35*gallery_available + 0.15*exhibition_available_count |
| PP-Y5 | route_y2_by_feature_quality_to_w4_p95_0.850 | y2_search_external_interaction | w4_p95 | 0.85 | search_quality_score + 0.35*gallery_available + 0.15*exhibition_available_count |
| PP-Y5 | route_y2_by_feature_quality_to_w4_p95_0.890 | y2_search_external_interaction | w4_p95 | 0.89 | search_quality_score + 0.35*gallery_available + 0.15*exhibition_available_count |
| PP-Y5 | route_y2_by_feature_quality_to_w4_p95_1.010 | y2_search_external_interaction | w4_p95 | 1.01 | search_quality_score + 0.35*gallery_available + 0.15*exhibition_available_count |
