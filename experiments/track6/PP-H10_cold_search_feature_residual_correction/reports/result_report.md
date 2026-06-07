# PP-H10 Cold 검색 피처 기반 잔차 보정 검증

- 목적: 외부 검색 기반 작가 인지도/문맥 피처가 Cold 가격 예측을 개선하는지 확인한다.
- 기준: 기존 데이터 split은 유지하고, 검색 결과는 작가명 기준으로만 수집한다.
- 주의: 이번 파일럿의 `search_result_count`는 검색엔진 전체 결과 수가 아니라 요청당 반환된 상위 결과 수와 그 문맥 분석값이다.

## Test 결과 상위

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 검색 커버리지 | 검색 커버 행 MdAPE |
|---|---:|---:|---:|---:|---:|---:|
| `base_catboost_search_interaction` | 0.4686 | 1.2233 | 3.9762 | 0.8887 | 0.468 | 0.3994 |
| `catboost_search_interaction_huber_residual_cap0.15_s0.5` | 0.4765 | 1.2784 | 4.3638 | 0.8953 | 0.468 | 0.4037 |
| `catboost_search_interaction_huber_residual_cap0.25_s0.5` | 0.4839 | 1.3149 | 4.5586 | 0.9012 | 0.468 | 0.4024 |
| `catboost_search_interaction_huber_residual_cap0.15_s0.75` | 0.4868 | 1.3098 | 4.5268 | 0.9007 | 0.468 | 0.4070 |
| `catboost_search_interaction_huber_residual_cap0.35_s0.5` | 0.4980 | 1.3516 | 4.5586 | 0.9082 | 0.468 | 0.4098 |
| `catboost_search_interaction_huber_residual_cap0.15_s1` | 0.4982 | 1.3434 | 4.4951 | 0.9075 | 0.468 | 0.4125 |
| `catboost_search_interaction_huber_residual_cap0.25_s0.75` | 0.5042 | 1.3702 | 4.5268 | 0.9127 | 0.468 | 0.4210 |
| `catboost_search_interaction_huber_residual_cap0.35_s0.75` | 0.5152 | 1.4334 | 4.5268 | 0.9274 | 0.468 | 0.4431 |
| `catboost_search_interaction_huber_residual_cap0.25_s1` | 0.5204 | 1.4320 | 4.4951 | 0.9275 | 0.468 | 0.4514 |
| `catboost_search_interaction_huber_residual_cap0.35_s1` | 0.5465 | 1.5259 | 4.9786 | 0.9525 | 0.468 | 0.4742 |

## 설정/피처 맵

| experiment_id | base_candidate | residual_model | cap | strength | hypothesis |
| --- | --- | --- | --- | --- | --- |
| PP-H10 | catboost_search_interaction | HuberRegressor | 0.15 | 0.5 | 검색 품질로 생기는 과대/과소 예측 구간을 검증 잔차 기반으로 완만하게 보정 |
| PP-H10 | catboost_search_interaction | HuberRegressor | 0.15 | 0.75 | 검색 품질로 생기는 과대/과소 예측 구간을 검증 잔차 기반으로 완만하게 보정 |
| PP-H10 | catboost_search_interaction | HuberRegressor | 0.15 | 1 | 검색 품질로 생기는 과대/과소 예측 구간을 검증 잔차 기반으로 완만하게 보정 |
| PP-H10 | catboost_search_interaction | HuberRegressor | 0.25 | 0.5 | 검색 품질로 생기는 과대/과소 예측 구간을 검증 잔차 기반으로 완만하게 보정 |
| PP-H10 | catboost_search_interaction | HuberRegressor | 0.25 | 0.75 | 검색 품질로 생기는 과대/과소 예측 구간을 검증 잔차 기반으로 완만하게 보정 |
| PP-H10 | catboost_search_interaction | HuberRegressor | 0.25 | 1 | 검색 품질로 생기는 과대/과소 예측 구간을 검증 잔차 기반으로 완만하게 보정 |
| PP-H10 | catboost_search_interaction | HuberRegressor | 0.35 | 0.5 | 검색 품질로 생기는 과대/과소 예측 구간을 검증 잔차 기반으로 완만하게 보정 |
| PP-H10 | catboost_search_interaction | HuberRegressor | 0.35 | 0.75 | 검색 품질로 생기는 과대/과소 예측 구간을 검증 잔차 기반으로 완만하게 보정 |
| PP-H10 | catboost_search_interaction | HuberRegressor | 0.35 | 1 | 검색 품질로 생기는 과대/과소 예측 구간을 검증 잔차 기반으로 완만하게 보정 |
