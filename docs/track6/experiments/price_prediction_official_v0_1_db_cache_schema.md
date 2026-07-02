# 가격 예측 서비스 공식 테스트 v0.1 DB/cache 설계서

- 작성일: 2026-06-12
- 공식 버전: `price_prediction_v0.1`
- 문서 목적: 보고서 기준 Warm/Cold 모델을 raw 입력 기반 서비스로 운영하기 위해 필요한 DB/cache 구조 정의
- 기준 문서:
  - `docs/track6/experiments/price_prediction_official_v0_1_test_plan.md`
  - `docs/track6/experiments/report_model_raw_input_gap_audit.md`
  - `docs/track6/experiments/similar_artist_artwork_service_criteria.md`

## 1. 결론

- 공식 테스트 v0.1은 파일만으로 1차 테스트를 시작할 수 있지만, 서비스 적용을 목표로 하므로 DB/cache가 필요
- DB는 모델 학습을 직접 수행하는 장소가 아니라, 예측에 필요한 조회 데이터와 예측 당시 스냅샷을 안정적으로 저장하는 계층
- Warm은 같은 작가 가격 이력, 유사작품 통계, Warm 중간 피처 스냅샷이 필요
- Cold는 작가 메타, 작품 조건, 검색 피처 snapshot, Cold 중간 피처 스냅샷이 필요
- 예측 결과는 반드시 입력값, 파생 피처, 모델 버전, 계산 단계와 함께 저장
- 실제 판매가 피드백은 검수 전에는 학습에 쓰지 않고, `training_candidates`로 승격된 뒤에만 다음 학습 후보로 사용

## 2. DB/cache의 역할

```text
[원천 CSV / 검색 snapshot / 모델 artifact]
        |
        v
[공식 v0.1 local DB/cache]
  - 작가 사전
  - 작가 alias
  - 작품 가격 이력
  - 유사작품 통계 cache
  - 검색 피처 snapshot
  - 모델 artifact registry
        |
        v
[예측 API]
  - 작가 매칭
  - Warm/Cold 라우팅
  - 피처 생성
  - 모델 추론
        |
        v
[예측 저장]
  - 입력 스냅샷
  - 피처 스냅샷
  - 중간 예측값
  - 최종 예측값
  - 계산 단계
        |
        v
[피드백/학습 후보]
  - 실제 판매가
  - 증빙 상태
  - 검수 상태
  - 학습 후보 승격
```

## 3. 로컬/운영 저장소 기준

| 환경 | 권장 저장소 | 목적 |
|---|---|---|
| 로컬 공식 테스트 v0.1 | SQLite | 빠른 개발, 재현 테스트, 파일 기반 공유 |
| 배포 전 staging | PostgreSQL | API와 DB 연결 구조 검증 |
| 운영 후보 | PostgreSQL | 동시 요청, 이벤트 저장, 검수 workflow |

로컬 테스트 기본 경로:

```text
data/track6/service_v0_1/price_prediction_v0_1.sqlite
```

DB schema는 SQLite 기준으로 시작하되, PostgreSQL로 옮길 수 있게 타입을 단순하게 유지한다.

초기 DB 생성 스크립트:

```text
scripts/track6/build_price_prediction_official_v0_1_db.py
```

생성 결과 요약:

```text
docs/track6/experiments/price_prediction_official_v0_1_db_build_summary.md
```

## 4. 원천 데이터 매핑

### 4.1 학습 가격 이력

기준 파일:

```text
models/track6/price_prediction_v0.1/data/training/track6_split/track6_train.csv
```

주요 원천 컬럼:

| 원천 컬럼 | DB 반영 위치 | 역할 |
|---|---|---|
| `_track6_row_id` | `artwork_price_observations.track6_row_id` | 학습 row 추적 |
| `source_artwork_id` | `artwork_price_observations.source_artwork_id` | 외부 작품 ID |
| `artwork_url` | `artwork_price_observations.artwork_url` | 원천 검수 URL |
| `image_url` | `artwork_price_observations.image_url` | 이미지 후속 피처 후보 |
| `artist_key` | `artist_registry.artist_key`, `artwork_price_observations.artist_key` | 내부 작가 식별자 |
| `artist_name_ko` | `artist_registry.name_ko`, `artist_aliases.alias_text` | 한글 작가명 |
| `artist_name_standardized` | `artist_aliases.alias_normalized` | 정규화 작가명 |
| `title_raw` | `artwork_price_observations.title` | 작품명 |
| `price_krw` | `artwork_price_observations.price_krw` | 학습 라벨 가격 |
| `ln_price_krw` | `artwork_price_observations.log_price_krw` | 로그 가격 |
| `width_cm`, `height_cm`, `depth_cm` | `artwork_price_observations` | 크기 피처 |
| `area_cm2`, `log_area`, `aspect_ratio` | `artwork_price_observations` | 파생 크기 피처 |
| `medium_category`, `support_category`, `medium_support_bucket` | `artwork_price_observations` | 재료/지지체 피처 |
| `artist_meta_*` | `artist_registry`, `artist_profile_snapshots` | 작가 메타 피처 |

### 4.2 검색 피처 snapshot

기준 파일:

```text
data/track6/external_search/operational/track6_artist_search_operational_snapshot_latest.csv
```

주요 원천 컬럼:

| 원천 컬럼 | DB 반영 위치 | 역할 |
|---|---|---|
| `artist_search_name` | `artist_search_feature_snapshots.artist_search_name` | 검색 기준 작가명 |
| `search_result_count` | `artist_search_feature_snapshots.search_result_count` | 검색 결과 수 |
| `search_source_count` | `artist_search_feature_snapshots.search_source_count` | source 다양성 |
| `search_art_context_count` | `artist_search_feature_snapshots.search_art_context_count` | 미술 문맥 수 |
| `search_exhibition_context_count` | `artist_search_feature_snapshots.search_exhibition_context_count` | 전시 문맥 수 |
| `search_gallery_context_count` | `artist_search_feature_snapshots.search_gallery_context_count` | 갤러리 문맥 수 |
| `search_market_context_count` | `artist_search_feature_snapshots.search_market_context_count` | 시장 문맥 수 |
| `search_homonym_context_count` | `artist_search_feature_snapshots.search_homonym_context_count` | 동명이인 위험 문맥 |
| `search_name_match_ratio` | `artist_search_feature_snapshots.search_name_match_ratio` | 이름 일치율 |
| `search_art_match_ratio` | `artist_search_feature_snapshots.search_art_match_ratio` | 미술 문맥 비율 |
| `search_quality_score` | `artist_search_feature_snapshots.search_quality_score` | 검색 품질 점수 |
| `search_quality_grade` | `artist_search_feature_snapshots.search_quality_grade` | 검색 품질 등급 |
| `search_homonym_risk_grade` | `artist_search_feature_snapshots.search_homonym_risk_grade` | 동명이인 위험 등급 |

검색 결과 상세 기준 파일:

```text
data/track6/external_search/operational/track6_artist_search_operational_standardized_latest.csv
```

검색 결과 상세는 `artist_search_results`에 적재해 검수와 설명에 사용한다.

## 5. 핵심 테이블 목록

| 테이블 | 목적 | Warm | Cold | 운영 저장 |
|---|---|---:|---:|---:|
| `artist_registry` | 내부 작가 사전 | 예 | 예 | 예 |
| `artist_aliases` | 작가명 매칭 alias | 예 | 예 | 예 |
| `artist_profile_snapshots` | 작가 메타 snapshot | 예 | 예 | 예 |
| `artwork_price_observations` | 작품 가격 이력 | 예 | 예 | 예 |
| `artist_search_feature_snapshots` | 검색 피처 snapshot | 아니오 | 예 | 예 |
| `artist_search_results` | 검색 결과 상세 | 아니오 | 설명/검수 | 예 |
| `similar_artwork_stats_cache` | 유사작품 통계 | 예 | 예 | cache |
| `similar_artist_cache` | 유사 작가 후보 | 설명/후속 | 설명 | cache |
| `model_artifact_registry` | 모델/피처 버전 관리 | 예 | 예 | 예 |
| `warm_feature_snapshots` | Warm 중간 피처 저장 | 예 | 아니오 | 예 |
| `cold_feature_snapshots` | Cold 중간 피처 저장 | 아니오 | 예 | 예 |
| `prediction_events` | 예측 이벤트 저장 | 예 | 예 | 예 |
| `prediction_calculation_steps` | 계산 단계 저장 | 예 | 예 | 예 |
| `sale_price_feedback` | 실제 판매가 피드백 | 예 | 예 | 예 |
| `training_candidates` | 검수 후 학습 후보 | 예 | 예 | 예 |

## 6. 테이블 상세

### 6.1 `artist_registry`

작가의 내부 기준 테이블이다. 사용자가 직접 입력하는 값이 아니라, 작가 매칭 결과로 사용된다.

| 필드 | 타입 | 설명 |
|---|---|---|
| `artist_key` | text primary key | 내부 작가 식별자 |
| `name_ko` | text | 대표 한글명 |
| `name_en` | text | 대표 영문명 |
| `birth_year` | integer | 생년 |
| `nationality` | text | 국적 |
| `nationality_ko` | text | 국적 한글명 |
| `entity_suffix` | text | 동명이인 구분 suffix |
| `is_homonym` | integer | 동명이인 위험 여부 |
| `valid_price_count` | integer | 사용 가능한 가격 이력 수 |
| `primary_medium_category` | text | 주 사용 재료 |
| `primary_support_category` | text | 주 사용 지지체 |
| `median_price_krw` | integer | 작가 가격 이력 중앙값 |
| `median_log_area` | real | 작가 작품 면적 로그 중앙값 |
| `created_at` | text | 생성 시각 |
| `updated_at` | text | 갱신 시각 |

주요 index:

```sql
CREATE INDEX idx_artist_registry_name_ko ON artist_registry(name_ko);
CREATE INDEX idx_artist_registry_name_en ON artist_registry(name_en);
CREATE INDEX idx_artist_registry_valid_price_count ON artist_registry(valid_price_count);
```

### 6.2 `artist_aliases`

한글명, 영문명, slug, 표기 변형을 artist_key에 연결한다.

| 필드 | 타입 | 설명 |
|---|---|---|
| `alias_id` | text primary key | alias 고유 ID |
| `artist_key` | text | 내부 작가 식별자 |
| `alias_text` | text | 원본 alias |
| `alias_normalized` | text | 정규화 alias |
| `alias_type` | text | `ko_name`, `en_name`, `slug`, `manual`, `external` |
| `source` | text | alias 출처 |
| `confidence` | real | alias 신뢰도 |
| `created_at` | text | 생성 시각 |

작가 매칭 기본 조회:

```text
입력작가명정규화값 == artist_aliases.alias_normalized
```

### 6.3 `artist_profile_snapshots`

작가 메타 피처를 snapshot 단위로 저장한다.

| 필드 | 타입 | 설명 |
|---|---|---|
| `snapshot_id` | text primary key | snapshot ID |
| `artist_key` | text | 내부 작가 식별자 |
| `snapshot_version` | text | snapshot 버전 |
| `birth_year` | integer | 생년 |
| `career_age` | real | 기준연도 - 생년 |
| `career_stage` | text | 활동 단계 |
| `total_works` | integer | 수집된 작품 수 |
| `for_sale_works` | integer | 판매 중 작품 수 |
| `followers` | integer | 팔로워 수 |
| `for_sale_ratio` | real | 판매 작품 비율 |
| `is_p1` | integer | P1 작가 여부 |
| `has_international` | integer | 해외 활동 여부 |
| `source` | text | 메타 출처 |
| `feature_json` | text | 추가 메타 JSON |
| `created_at` | text | 생성 시각 |

### 6.4 `artwork_price_observations`

학습/검증/운영에서 사용할 가격 이력 테이블이다.

| 필드 | 타입 | 설명 |
|---|---|---|
| `observation_id` | text primary key | 가격 관측 ID |
| `track6_row_id` | integer | 기존 row 추적 ID |
| `source_artwork_id` | text | 외부 작품 ID |
| `source_name` | text | 원천 데이터 출처 |
| `artwork_url` | text | 작품 URL |
| `image_url` | text | 이미지 URL |
| `artist_key` | text | 내부 작가 식별자 |
| `artist_name_ko` | text | 원천 한글 작가명 |
| `title` | text | 작품명 |
| `price_krw` | integer | 원화 가격 |
| `log_price_krw` | real | 로그 가격 |
| `width_cm` | real | 가로 |
| `height_cm` | real | 세로 |
| `depth_cm` | real | 깊이 |
| `area_cm2` | real | 면적 |
| `log_area` | real | 로그 면적 |
| `aspect_ratio` | real | 가로세로비 |
| `has_depth` | integer | 깊이 존재 여부 |
| `is_3d_candidate` | integer | 입체 후보 여부 |
| `medium_category` | text | 정규화 재료 |
| `support_category` | text | 정규화 지지체 |
| `medium_support_bucket` | text | 재료+지지체 bucket |
| `is_training_candidate` | integer | 학습 후보 여부 |
| `label_quality_tier` | text | 라벨 품질 |
| `split_name` | text | train/validation/test/operational |
| `created_at` | text | 생성 시각 |

주요 index:

```sql
CREATE INDEX idx_price_obs_artist ON artwork_price_observations(artist_key);
CREATE INDEX idx_price_obs_medium_support ON artwork_price_observations(medium_category, support_category);
CREATE INDEX idx_price_obs_area ON artwork_price_observations(log_area);
CREATE INDEX idx_price_obs_split ON artwork_price_observations(split_name);
```

### 6.5 `artist_search_feature_snapshots`

Cold 검색 피처를 작가명 또는 artist_key 기준으로 조회하기 위한 테이블이다.

| 필드 | 타입 | 설명 |
|---|---|---|
| `search_snapshot_id` | text primary key | 검색 snapshot ID |
| `snapshot_version` | text | 검색 snapshot 버전 |
| `artist_key` | text | 매칭된 내부 작가 식별자 |
| `artist_search_name` | text | 검색 기준 작가명 |
| `artist_search_name_normalized` | text | 정규화 검색 작가명 |
| `search_result_count` | integer | 검색 결과 수 |
| `search_source_count` | integer | source 수 |
| `provider_coverage_count` | integer | provider 커버리지 |
| `query_success_count` | integer | 성공 query 수 |
| `search_art_context_count` | integer | 미술 문맥 수 |
| `search_exhibition_context_count` | integer | 전시 문맥 수 |
| `search_gallery_context_count` | integer | 갤러리 문맥 수 |
| `search_market_context_count` | integer | 시장 문맥 수 |
| `search_social_context_count` | integer | 소셜 문맥 수 |
| `search_homonym_context_count` | integer | 동명이인 위험 문맥 수 |
| `search_trusted_domain_count` | integer | 신뢰 domain 수 |
| `search_name_match_ratio` | real | 이름 일치율 |
| `search_art_match_ratio` | real | 미술 문맥 비율 |
| `search_exhibition_ratio` | real | 전시 문맥 비율 |
| `search_quality_score` | real | 검색 품질 점수 |
| `search_quality_grade` | text | 검색 품질 등급 |
| `search_homonym_risk_grade` | text | 동명이인 위험 등급 |
| `search_success_flag` | integer | 검색 성공 여부 |
| `search_collected_flag` | integer | 검색 수집 여부 |
| `raw_feature_json` | text | 전체 검색 피처 JSON |
| `created_at` | text | 생성 시각 |

Cold에서 검색 피처 조회 우선순위:

```text
1. artist_key가 있으면 artist_key로 조회
2. artist_key가 없으면 정규화 작가명으로 조회
3. 동일 후보가 여러 개면 search_quality_score가 가장 높은 snapshot 선택
4. 검색 피처가 없으면 fallback 값 사용 및 신뢰도 하향
```

### 6.6 `artist_search_results`

검색 결과 상세를 저장한다. 예측 계산보다는 검수와 설명 근거에 사용한다.

| 필드 | 타입 | 설명 |
|---|---|---|
| `result_id` | text primary key | 검색 결과 ID |
| `search_snapshot_id` | text | 상위 snapshot ID |
| `artist_search_name` | text | 검색 작가명 |
| `provider` | text | 검색 provider |
| `query_text` | text | 검색 query |
| `rank` | integer | 결과 순위 |
| `title` | text | 결과 제목 |
| `snippet` | text | 결과 요약 |
| `url` | text | 결과 URL |
| `domain` | text | domain |
| `source_group` | text | source group |
| `has_result` | integer | 결과 존재 여부 |
| `is_art_context` | integer | 미술 문맥 여부 |
| `is_exhibition_context` | integer | 전시 문맥 여부 |
| `is_gallery_context` | integer | 갤러리 문맥 여부 |
| `is_market_context` | integer | 시장 문맥 여부 |
| `is_homonym_context` | integer | 동명이인 위험 여부 |
| `artist_name_in_result` | integer | 결과 내 작가명 존재 여부 |
| `collected_at` | text | 수집 시각 |

### 6.7 `similar_artwork_stats_cache`

Warm 기준가격과 화면의 유사작품 근거를 빠르게 조회하기 위한 cache다.

| 필드 | 타입 | 설명 |
|---|---|---|
| `stats_id` | text primary key | 통계 row ID |
| `cache_version` | text | cache 버전 |
| `scope` | text | `same_artist`, `cross_artist`, `similar_artist` |
| `artist_key` | text | 대상 artist_key |
| `medium_category` | text | 재료 |
| `support_category` | text | 지지체 |
| `size_bucket` | text | 크기 구간 |
| `log_area_min` | real | 로그 면적 하한 |
| `log_area_max` | real | 로그 면적 상한 |
| `sample_count` | integer | 표본 수 |
| `median_price_krw` | integer | 가격 중앙값 |
| `q25_price_krw` | integer | 25% 가격 |
| `q75_price_krw` | integer | 75% 가격 |
| `median_log_price` | real | 로그 가격 중앙값 |
| `median_krw_per_ho` | integer | 호당 가격 중앙값 |
| `q25_krw_per_ho` | integer | 호당 가격 25% |
| `q75_krw_per_ho` | integer | 호당 가격 75% |
| `coverage_tier` | text | strong/medium/wide/fallback |
| `created_at` | text | 생성 시각 |

유사작품 등급:

| 등급 | 조건 | 최소 표본 |
|---|---|---:|
| strong | 같은 작가 + 같은 재료/지지체 + 비슷한 크기 | 5 |
| medium | 같은 작가 + 비슷한 크기 | 5 |
| wide_artist | 같은 작가 전체 | 5 |
| cross_condition | 같은 재료/지지체 + 비슷한 크기 | 30 |

### 6.8 `similar_artist_cache`

유사 작가 후보와 설명 근거를 저장한다.

| 필드 | 타입 | 설명 |
|---|---|---|
| `similar_artist_id` | text primary key | 유사 작가 row ID |
| `cache_version` | text | cache 버전 |
| `target_artist_key` | text | 기준 작가 |
| `candidate_artist_key` | text | 유사 작가 후보 |
| `similarity_score` | real | 유사도 점수 |
| `numeric_similarity` | real | 숫자형 유사도 |
| `categorical_similarity` | real | 범주형 유사도 |
| `price_history_count` | integer | 후보 작가 가격 이력 수 |
| `match_reasons_json` | text | 유사 사유 JSON |
| `created_at` | text | 생성 시각 |

유사도 계산 기준:

```text
이력이 있는 작가:
유사도 = 0.55 * 숫자형_유사도 + 0.45 * 범주형_유사도

이력이 부족한 작가:
유사도 = 0.30 * 숫자형_유사도 + 0.70 * 범주형_유사도
```

### 6.9 `model_artifact_registry`

공식 v0.1에서 어떤 모델과 피처 버전을 썼는지 고정한다.

| 필드 | 타입 | 설명 |
|---|---|---|
| `artifact_id` | text primary key | artifact ID |
| `service_version` | text | `price_prediction_v0.1` |
| `route` | text | `warm`, `cold`, `shared` |
| `artifact_role` | text | feature_builder/model/postprocessor/cache |
| `display_name` | text | 기능 중심 이름 |
| `internal_trace_id` | text | 내부 실험/아티팩트 ID |
| `artifact_path` | text | 파일 경로 |
| `artifact_hash` | text | hash |
| `feature_schema_version` | text | 피처 schema 버전 |
| `metrics_json` | text | 성능 지표 JSON |
| `active_flag` | integer | 활성 여부 |
| `created_at` | text | 등록 시각 |

### 6.10 `warm_feature_snapshots`

Warm 최종 예측에 필요한 중간 피처를 저장한다.

| 필드 | 타입 | 설명 |
|---|---|---|
| `warm_feature_id` | text primary key | Warm 피처 snapshot ID |
| `prediction_id` | text | 예측 ID |
| `feature_schema_version` | text | 피처 schema 버전 |
| `artist_key` | text | 내부 작가 식별자 |
| `pp252_log` | real | 미세 보정 전 기준 로그가격 |
| `pp252_stability_log` | real | 안정성 우선 기준 로그가격 |
| `prob_hist35_pp252` | real | 기준가보다 높을 확률 |
| `resid_huber_pp252` | real | Huber 잔차 보정 후보 |
| `quantile_width` | real | 예측 불확실성 폭 |
| `l10_price_range_ratio` | real | 가격 범위 비율 |
| `svc_group_n` | integer | 유사작품 표본 수 |
| `component_prediction_spread` | real | 후보 모델 간 차이 |
| `confidence_tier` | text | high/medium/low |
| `stable_price_band` | text | 안정 가격대 |
| `row_risk` | real | row 위험도 |
| `applied_cap_log` | real | 적용 보정 상한 |
| `applied_correction_log` | real | 적용 보정 로그값 |
| `final_log_price` | real | 최종 로그가격 |
| `feature_json` | text | 전체 피처 JSON |
| `created_at` | text | 생성 시각 |

### 6.11 `cold_feature_snapshots`

Cold 최종 예측에 필요한 중간 피처를 저장한다.

| 필드 | 타입 | 설명 |
|---|---|---|
| `cold_feature_id` | text primary key | Cold 피처 snapshot ID |
| `prediction_id` | text | 예측 ID |
| `feature_schema_version` | text | 피처 schema 버전 |
| `artist_key` | text | 내부 작가 식별자 |
| `search_snapshot_id` | text | 검색 snapshot ID |
| `y18_qwidth_pred_log` | real | 검색 피처 포함 대표 로그가격 |
| `lgb_q40_pred_log` | real | 낮은쪽 40% 지점 로그가격 |
| `quantile_width_log` | real | 예측구간폭 |
| `guard_applied` | integer | 과대예측 방어 적용 여부 |
| `guard_pred_log` | real | 방어 후 로그가격 |
| `search_delta_log` | real | 작가 검색 보정값 |
| `search_covered` | integer | 검색 lookup 적용 여부 |
| `review_flag` | integer | 검수 권장 여부 |
| `confidence_tier` | text | high/medium/low |
| `final_log_price` | real | 최종 로그가격 |
| `feature_json` | text | 전체 피처 JSON |
| `created_at` | text | 생성 시각 |

### 6.12 `prediction_events`

예측 요청 1건의 기준 테이블이다.

| 필드 | 타입 | 설명 |
|---|---|---|
| `prediction_id` | text primary key | 예측 ID |
| `request_id` | text | API 요청 ID |
| `service_version` | text | `price_prediction_v0.1` |
| `route` | text | warm/cold/review_required |
| `display_route` | text | 이력 기반 예측/참고 예측/확인 필요 |
| `artist_key` | text | 확정 artist_key |
| `artist_match_score` | real | 작가 매칭 신뢰도 |
| `same_artist_training_price_count` | integer | 같은 작가 가격 이력 수 |
| `input_snapshot_json` | text | 사용자 입력 원본 |
| `input_quality_json` | text | 입력 품질 |
| `prediction_price_krw` | integer | 예측 가격 |
| `range_low_krw` | integer | 가격 범위 하단 |
| `range_high_krw` | integer | 가격 범위 상단 |
| `confidence_tier` | text | 신뢰도 |
| `model_artifacts_json` | text | 사용 모델/피처 버전 |
| `created_at` | text | 예측 시각 |

### 6.13 `prediction_calculation_steps`

화면에서 계산 과정을 보여주기 위한 단계별 저장 테이블이다.

| 필드 | 타입 | 설명 |
|---|---|---|
| `step_id` | text primary key | 단계 ID |
| `prediction_id` | text | 예측 ID |
| `step_order` | integer | 단계 순서 |
| `step_name` | text | 단계명 |
| `step_role` | text | 단계 역할 |
| `formula_text` | text | 사용자/운영자용 식 |
| `input_json` | text | 단계 입력값 |
| `output_json` | text | 단계 출력값 |
| `display_flag` | integer | 사용자 화면 표시 여부 |
| `created_at` | text | 생성 시각 |

### 6.14 `sale_price_feedback`

사용자가 나중에 입력하는 실제 판매가다.

| 필드 | 타입 | 설명 |
|---|---|---|
| `feedback_id` | text primary key | 피드백 ID |
| `prediction_id` | text | 연결 예측 ID |
| `actual_sale_price_krw` | integer | 실제 판매가 |
| `sale_date` | text | 판매일 |
| `sale_channel` | text | 판매 채널 |
| `evidence_status` | text | none/partial/verified |
| `consent_for_training` | integer | 학습 활용 동의 |
| `review_status` | text | needs_review/approved/rejected |
| `review_note` | text | 검수 메모 |
| `created_at` | text | 입력 시각 |
| `reviewed_at` | text | 검수 시각 |

### 6.15 `training_candidates`

검수 완료 후 학습 후보로 승격된 row를 저장한다.

| 필드 | 타입 | 설명 |
|---|---|---|
| `candidate_id` | text primary key | 학습 후보 ID |
| `feedback_id` | text | 실제 판매가 피드백 ID |
| `prediction_id` | text | 연결 예측 ID |
| `route_at_prediction` | text | 예측 당시 route |
| `artist_key` | text | 내부 작가 식별자 |
| `label_price_krw` | integer | 학습 라벨 가격 |
| `quality_score` | real | 운영 데이터 품질 점수 |
| `candidate_status` | text | training_candidate/holdout_candidate/rejected |
| `feature_snapshot_json` | text | 학습 후보 피처 snapshot |
| `created_at` | text | 승격 시각 |

## 7. Warm 예측 시 DB 조회 순서

```text
1. artist_aliases에서 입력 작가명 매칭
2. artist_registry에서 작가 가격 이력 수와 메타 조회
3. artwork_price_observations에서 같은 작가 가격 이력 조회
4. similar_artwork_stats_cache에서 유사작품 통계 조회
5. model_artifact_registry에서 활성 Warm 모델/피처 버전 조회
6. Warm feature builder가 중간 피처 생성
7. warm_feature_snapshots에 중간 피처 저장
8. prediction_events에 최종 예측 저장
9. prediction_calculation_steps에 계산 과정 저장
```

## 8. Cold 예측 시 DB 조회 순서

```text
1. artist_aliases에서 입력 작가명 매칭 시도
2. artist_registry에서 작가 메타 조회
3. artist_search_feature_snapshots에서 검색 피처 조회
4. 검색 피처가 없으면 fallback search feature 생성
5. model_artifact_registry에서 활성 Cold 모델/피처 버전 조회
6. Cold feature builder가 검색 포함 Quantile 중간 피처 생성
7. 과대예측 방어와 작가 검색 보정 후처리 적용
8. cold_feature_snapshots에 중간 피처 저장
9. prediction_events에 최종 예측 저장
10. prediction_calculation_steps에 계산 과정 저장
```

## 9. 데이터 품질과 학습 후보 승격

```text
운영데이터품질점수 =
  0.30 * 판매가격증빙점수
+ 0.25 * 작가매칭신뢰도점수
+ 0.20 * 작품정보완성도점수
+ 0.15 * 판매채널신뢰도점수
+ 0.10 * 중복검수통과점수
```

```text
학습후보승격 =
  (실제판매가_원화 > 0)
  AND (학습활용동의 = true)
  AND (검수상태 = approved)
  AND (운영데이터품질점수 >= 0.80)
  AND (중복상태 != duplicate_excluded)
```

## 10. 캐시 갱신 정책

| cache | 갱신 조건 | 재검증 |
|---|---|---|
| `similar_artwork_stats_cache` | 학습 가격 이력 추가 또는 정정 | Warm fixed-test parity |
| `similar_artist_cache` | 작가 메타/가격 이력 추가 | 유사 작가 표시 품질 확인 |
| `artist_search_feature_snapshots` | 검색 snapshot 수집/검수 완료 | Cold fixed-test parity |
| `model_artifact_registry` | 모델 파일 교체 | 반복 결과 동일성 + fixed-test 재현 |

## 11. deterministic 운영 원칙

- 같은 입력과 같은 DB snapshot이면 항상 같은 예측값을 반환
- 검색 피처는 예측 시점에 실시간 호출하지 않고 snapshot을 사용
- 예측 이벤트에는 사용한 snapshot version을 저장
- 모델 파일과 피처 schema version을 함께 저장
- cache가 바뀌면 기존 예측값을 덮어쓰지 않고 새 prediction_id로 계산

## 12. 1차 구현 순서

| 순서 | 작업 | 산출물 |
|---:|---|---|
| 1 | SQLite schema 생성 | `price_prediction_v0_1.sqlite` |
| 2 | 학습 가격 이력 import | `artist_registry`, `artwork_price_observations` |
| 3 | alias 생성 | `artist_aliases` |
| 4 | 검색 snapshot import | `artist_search_feature_snapshots`, `artist_search_results` |
| 5 | 유사작품 통계 cache 생성 | `similar_artwork_stats_cache` |
| 6 | 모델 registry seed 입력 | `model_artifact_registry` |
| 7 | 예측 이벤트 저장 API 연결 | `prediction_events`, `prediction_calculation_steps` |

## 13. 완료 기준

```text
DB/cache 1차 완료 =
  (작가명으로 artist_key 후보 조회 가능)
  AND (같은 작가 가격 이력 수 조회 가능)
  AND (유사작품 통계 조회 가능)
  AND (검색 피처 snapshot 조회 가능)
  AND (예측 이벤트 저장 가능)
  AND (계산 단계 저장 가능)
  AND (실제 판매가 피드백 저장 가능)
```
