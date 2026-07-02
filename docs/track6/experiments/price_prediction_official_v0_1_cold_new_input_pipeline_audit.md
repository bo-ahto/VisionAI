# 공식 v0.1 Cold 신규 입력 feature pipeline 감사

- 작성일: 2026-06-12T16:47:47+09:00
- 목적: feature store에 없는 신규 입력도 deterministic하게 Cold 피처를 생성하는지 확인

## 1. 결론

- 전체 deterministic 통과: 예
- 전체 feature input mode 기대값 일치: 예
- 해석: row-level feature store가 없으면 공식 DB search snapshot, 작가 단위 전시/갤러리 cache, missing/default 순서로 피처를 생성한다.

## 2. 케이스별 결과

| 케이스 | 기대 모드 | 실제 모드 | deterministic | 가격 | search basis | external basis |
|---|---|---|---|---:|---|---|
| fixed_test_replay_source_id | row_feature_store_replay | row_feature_store_replay | 예 | 28066959 | cold_feature_store_source_artwork_id | cold_feature_store_source_artwork_id |
| new_input_search_cache | service_search_external_cache | service_search_external_cache | 예 | 7614532 | artist_key | artist_key |
| new_input_external_cache | service_external_cache | service_external_cache | 예 | 2558577 | snapshot_not_found | artist_key |
| new_input_default_missing | service_default_missing | service_default_missing | 예 | 2793675 | snapshot_not_found | external_cache_not_found |

## 3. 모드 정의

| 모드 | 의미 |
|---|---|
| `row_feature_store_replay` | `artwork_url` 또는 `source_artwork_id`가 row-level Cold feature store에 적중해 실험 입력 피처를 그대로 재사용 |
| `service_search_external_cache` | 신규 입력이지만 검색 snapshot과 전시/갤러리 cache가 모두 적중 |
| `service_search_cache` | 신규 입력에서 검색 snapshot만 적중 |
| `service_external_cache` | 신규 입력에서 전시/갤러리 cache만 적중 |
| `service_default_missing` | 신규 입력에서 검색/외부 cache가 없어 missing/default 피처로 계산 |

## 4. 산출물

- JSON: `docs/track6/experiments/price_prediction_official_v0_1_cold_new_input_pipeline_audit.json`
- 상세 결과: `experiments/track6/PP-OFFICIAL-V01_cold_new_input_pipeline_audit/outputs/case_results.json`
