# PP-X1 갤러리/전시 활동 피처 커버리지 재검증

- 목적: 갤러리 티어와 개인전/전시 활동 피처를 현재 최신 Cold 후보 구조에서 재검증한다.
- 기준: 기존 Track6 split은 바꾸지 않고 `_track6_row_id` 기준으로 외부 피처만 추가한다.

## 커버리지

| experiment_id | candidate | scope | split | policy | n_rows | solo_coverage | group_coverage | fair_coverage | gallery_raw_coverage | gallery_validated_coverage | gallery_any_coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-X1 | external_feature_coverage | cold | train | coverage_only | 26914 | 0.577395 | 0.585866 | 0.604332 | 0.605075 | 0.000705952 | 0.605781 |
| PP-X1 | external_feature_coverage | cold | validation | coverage_only | 2753 | 0.680349 | 0.668725 | 0.690883 | 0.690883 | 0 | 0.690883 |
| PP-X1 | external_feature_coverage | cold | test | coverage_only | 3099 | 0.525331 | 0.522749 | 0.546305 | 0.549209 | 0.0103259 | 0.559535 |

## 설정/피처 맵

| experiment_id | source_raw | source_validated | join_key | note |
| --- | --- | --- | --- | --- |
| PP-X1 | data/track4_primary_market_raw_collected.csv | data/track4_primary_market_cleaned_v2.csv | _track6_row_id -> track4_source + track4_source_row_index | Current Track6 split membership is fixed; only external columns are joined. |
