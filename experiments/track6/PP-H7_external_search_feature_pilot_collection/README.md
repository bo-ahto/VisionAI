# PP-H7 외부 검색 피처 파일럿 수집

- 목적: 외부 검색 기반 작가 인지도/문맥 피처가 Cold 가격 예측을 개선하는지 확인한다.
- 기준: 기존 데이터 split은 유지하고, 검색 결과는 작가명 기준으로만 수집한다.
- 주의: 이번 파일럿의 `search_result_count`는 검색엔진 전체 결과 수가 아니라 요청당 반환된 상위 결과 수와 그 문맥 분석값이다.

## 수집 커버리지

| experiment_id | candidate | scope | split | policy | n_rows | unique_artists | covered_n | coverage_rate | search_quality_mean | search_high_rate | search_medium_rate | search_low_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-H7 | external_search_collection | cold | train | search_feature_collection_only | 26914 | 1693 | 11962 | 0.444453 | 0.0945197 | 0 | 0.0218102 | 0.422642 |
| PP-H7 | external_search_collection | cold | validation | search_feature_collection_only | 2753 | 168 | 1573 | 0.571377 | 0.093435 | 0 | 0 | 0.571377 |
| PP-H7 | external_search_collection | cold | test | search_feature_collection_only | 3099 | 188 | 1449 | 0.46757 | 0.0963332 | 0 | 0.0271055 | 0.440465 |

## 설정/피처 맵

| experiment_id | selection_policy | limit_artists | max_results_per_artist | feature_path | raw_path | note |
| --- | --- | --- | --- | --- | --- | --- |
| PP-H7 | all_frequency | 120 | 6 | data/track6/external_search/track6_artist_search_pilot_features.csv | data/track6/external_search/track6_artist_search_pilot_raw.jsonl | DuckDuckGo public search snippets are converted into capped count/context features; this is not total web result count. |
