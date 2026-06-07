# PP-W5 Cold 작가 메타 후보 목적별 정책 갱신

- 목적: Cold 서비스 적용 가능성을 높이기 위해 작가 메타 피처와 모델 특성 기반 학습 순서를 추가 검증한다.
- 선택 기준: validation에서 후보/보정 강도를 정하고 test에서 재현성을 본다.

## Test 결과 상위

| 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---:|---:|---:|---:|
| `component_w2_best_meta_cb` | `artist_meta_policy_refresh` | 0.4536 | 1.1434 | 4.1897 | 0.8839 |
| `component_w1_best_meta_lgb` | `artist_meta_policy_refresh` | 0.4720 | 1.2345 | 3.3279 | 0.9084 |
| `component_s1_mdape` | `artist_meta_policy_refresh` | 0.4744 | 1.2095 | 3.4731 | 0.9301 |
| `component_s1_p95` | `artist_meta_policy_refresh` | 0.4765 | 1.2067 | 3.2824 | 0.9386 |
| `component_q2_mape` | `artist_meta_policy_refresh` | 0.4811 | 1.1797 | 3.7925 | 0.9236 |
| `component_w4_best_seq` | `artist_meta_policy_refresh` | 0.5173 | 1.1096 | 3.3169 | 0.9249 |
| `cold_artist_meta_policy_mdape_first` | `artist_meta_policy_refresh` | 0.5173 | 1.1096 | 3.3169 | 0.9249 |
| `cold_artist_meta_policy_mape_guarded` | `artist_meta_policy_refresh` | 0.5173 | 1.1096 | 3.3169 | 0.9249 |
| `cold_artist_meta_policy_p95_guarded` | `artist_meta_policy_refresh` | 0.5173 | 1.1096 | 3.3169 | 0.9249 |
| `component_w3_best_seq` | `artist_meta_policy_refresh` | 0.5259 | 1.0420 | 3.7242 | 0.9211 |

## 설정/정책 맵

| experiment_id | objective | selected_label | validation_RMSE_log | validation_MdAPE | validation_MAPE | validation_p95_APE | validation_Within_30 | validation_Within_50 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-W5 | mdape_first | w4_best_seq | 0.559114 | 0.235775 | 0.420199 | 1.20403 | 0.572466 | 0.757356 |
| PP-W5 | mape_guarded | w4_best_seq | 0.559114 | 0.235775 | 0.420199 | 1.20403 | 0.572466 | 0.757356 |
| PP-W5 | p95_guarded | w4_best_seq | 0.559114 | 0.235775 | 0.420199 | 1.20403 | 0.572466 | 0.757356 |
