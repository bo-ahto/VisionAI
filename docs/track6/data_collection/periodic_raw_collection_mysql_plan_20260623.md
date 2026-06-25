# 4개 원천 사이트 주기 수집 및 MySQL 적재 기획

작성일: 2026-06-23

대상 원천:

- Saatchi
- Artsy
- Art1
- Print Bakery

관련 문서:

- [데이터 수집 서비스 시나리오](data_collection_service_scenarios_20260625.md)
- [사용자 / 어드민 화면 구조 및 기능 기획](user_admin_screen_structure_plan_20260625.md)
- [사용자 / 어드민 API 기획](user_admin_api_plan_20260625.md)
- [주기 수집 운영 문서](weekly_crawler_mysql_operation_plan_20260624.md)
- [artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md)
- [4개 원천 사이트별 수집 항목 정리](source_site_collected_fields_20260624.md)

## 문서 세트에서의 위치

데이터 수집 문서는 아래 순서로 읽는 것을 기준으로 한다.

1. [데이터 수집 서비스 시나리오](data_collection_service_scenarios_20260625.md)
   - 사용자/어드민/수집 job이 어떤 상황에서 어떻게 동작하는지 설명한다.
2. [사용자 / 어드민 화면 구조 및 기능 기획](user_admin_screen_structure_plan_20260625.md)
   - DB에 저장된 상태와 검수 데이터를 화면에서 어떻게 쓸지 설명한다.
3. [사용자 / 어드민 API 기획](user_admin_api_plan_20260625.md)
   - 화면 기능이 호출할 사용자/어드민 API와 DB 참조 범위를 설명한다.
4. [주기 수집 운영 문서](weekly_crawler_mysql_operation_plan_20260624.md)
   - 운영자가 수집 결과를 어떻게 확인하고 실패를 어떻게 처리하는지 설명한다.
5. [artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md)
   - 작가명 한글화/영문화, alias, 동명이인, 최종 artist_key 생성 기준을 설명한다.
6. [원천 사이트별 수집 항목 정리](source_site_collected_fields_20260624.md)
   - 원천별 작품/작가 수집 항목과 표준화 기준을 설명한다.
7. [MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md)
   - 위 운영/데이터 기준을 실제 DB와 job으로 구현하는 방법을 설명한다.

이 문서는 구현 설계를 담당한다. 운영 알림 문구나 사이트별 세부 컬럼 설명은 다른 문서에 두고, 여기서는 MySQL 테이블, 수집 job, upsert, snapshot export, 테스트 기준을 중심으로 정리한다. 작가명/alias/동명이인/`artist_key` 판단 규칙은 [artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md)을 기준으로 구현한다.

> 단일 기준: MySQL 테이블/컬럼/enum 정의의 단일 기준은 이 문서다. 다른 문서에 나오는 테이블 설명은 운영 이해를 돕기 위한 참조 부분집합이며, 스키마 정의가 어긋나면 이 문서를 기준으로 맞춘다. 작가 identity 판정 규칙의 단일 기준은 [artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md)이다.

문서 내부 흐름:

```text
목표
  -> 현재 CSV 중심 수집 방식의 한계
  -> raw first, normalize later 원칙
  -> 전체 수집 파이프라인
  -> MySQL 스키마 레이어와 테이블 설계
  -> 화면/API가 참조할 스키마 범위
  -> 원천별 collector 구현 전략
  -> 주기 실행과 upsert/변경 이력
  -> 품질 감사와 모델 학습 연결
  -> 1차 적용 범위와 구현 단계
  -> 개발자 구현 체크리스트
```

## 1. 목표

현재는 사이트별 수집 결과를 CSV로 저장하고, 이후 별도 스크립트로 표준화/중복 제거/학습 데이터 생성을 진행한다. 운영 단계에서는 이 구조를 MySQL 기반의 주기 수집 시스템으로 바꿔야 한다.

목표는 다음과 같다.

- 4개 원천 사이트를 주기적으로 수집한다.
- 수집 당시의 원본 응답을 보존한다.
- 같은 작품이 여러 번 수집되어도 이력과 최신 상태를 구분한다.
- 원천별 컬럼 차이를 표준 컬럼으로 정리한다.
- 가격 예측 학습 데이터 생성에 필요한 raw provenance를 남긴다.
- 향후 모델 재학습 시 특정 날짜 기준 snapshot을 재현할 수 있게 한다.

## 2. 현재 수집 방식 점검

| 원천 | 현재 방식 | 현재 산출물 | 장점 | 한계 |
|---|---|---|---|---|
| Saatchi | 기존 수집 스크립트/플랫폼 export CSV | `source_platform_saatchi_kr_artworks_split_13102.csv`, legacy CSV | 이미 대량 수집 경험 있음, CSV 표준화 로직 존재 | CSV 파일 중심이라 증분 수집/변경 이력 관리가 약함 |
| Artsy | 기존 수집 스크립트/플랫폼 export CSV | `source_platform_artsy_kr_artworks.csv`, artist CSV | 작품/작가 메타가 비교적 풍부함 | 원천 통화/환산 컬럼 구분이 중요하고, 중복 출처 관리가 필요 |
| Print Bakery | Cafe24 상품 API 우선, HTML fallback + 아티스트 목록/상세 수집 | `data/printbakery_collect_20260623` | 국내 원화 가격/작가/크기 정보가 명확함, Cafe24 상품 API로 구조화 수집 가능 | API 앱 키/버전 변경 가능성, sold/out 상태 변화 추적 필요 |
| Art1 | 내부 AJAX endpoint 우선, HTML fallback + 상세 HTML 작가 프로필 추출 | `data/art1_collect_20260623` | 상세 필드가 안정적으로 추출됨, goods_id 기반 중복 관리 가능 | 화면 총 건수와 AJAX 반환 건수가 다를 수 있어 run별 감사가 필요 |

현재 CSV 방식은 실험과 일회성 검증에는 적합하지만, 운영 수집에는 부족하다. 특히 다음 문제가 있다.

- 같은 작품의 가격/판매상태가 바뀌었는지 알기 어렵다.
- 수집 실패와 원천 삭제를 구분하기 어렵다.
- CSV 생성 시점의 코드 버전과 원본 응답을 묶어 추적하기 어렵다.
- 학습 데이터가 어느 수집 run에서 왔는지 재현하기 어렵다.

## 3. 권장 원칙

권장 구조는 `raw first, normalize later`이다.

즉 수집기는 먼저 원본에 가까운 데이터를 저장하고, 정규화/중복 제거/학습용 필터는 후속 단계에서 수행한다.

추가 원칙은 `no guessing`이다. 원천에 없는 값을 표준화 단계에서 추측해 채우지 않는다. 공통 컬럼으로 확정할 수 없는 값은 raw/staging에 보존하고, `quality_flags_json`, `unmapped`, `review_status`로 관리한다.

### 왜 raw를 먼저 저장해야 하는가

- 원천 사이트 HTML/API 구조가 바뀌어도 이전 수집 원본을 다시 파싱할 수 있다.
- 가격 환산, medium 분류, 작가 키 생성 정책이 바뀌어도 raw에서 재생성할 수 있다.
- 모델 성능 이슈가 생겼을 때 어떤 원천 row가 어떤 학습 row로 들어갔는지 추적할 수 있다.
- 운영 중 수집 실패가 있어도 마지막 정상 raw snapshot과 비교할 수 있다.

### CSV를 완전히 버릴 필요는 없음

운영 DB는 MySQL을 기준으로 두되, CSV export는 계속 필요하다.

- 모델 학습/실험은 parquet를 우선 사용한다.
- 외부 공유, 감사, 수동 검수에는 CSV가 편하다.
- 기존 실험 코드가 CSV 입력을 요구하는 경우에는 CSV export를 추가로 생성한다.
- 따라서 MySQL은 운영 단일 기준 저장소, parquet는 학습/분석용 snapshot, CSV는 공유/검수/호환용 export로 보는 것이 맞다.

### 권장 저장 포맷

최초 원천 데이터와 운영 데이터, 학습 데이터는 같은 포맷으로 억지로 통일하지 않는다. 목적별로 포맷을 분리한다.

```text
01_payload/
  - 원본 응답 보존
  - JSON API 응답: .json 또는 .json.gz
  - HTML 응답: .html 또는 .html.gz
  - 원천 CSV export: .csv 또는 .csv.gz

02_raw_jsonl/
  - source_artwork_raw_{source}_{run_id}.jsonl
  - source_artist_raw_{source}_{run_id}.jsonl
  - row 단위 raw 파싱 결과를 파일로 남겨 재처리/공유 가능

03_mysql/
  - collector_run
  - raw_fetch
  - source_artwork_raw
  - source_artist_raw
  - interpreted_staging
  - normalized_staging

04_snapshot_export/
  - normalized_artworks_{snapshot_id}.parquet
  - normalized_artists_{snapshot_id}.parquet
  - training_snapshot_{snapshot_id}.parquet
  - 운영자 검수, 외부 공유, 기존 CSV 기반 코드 호환이 필요할 때만 review_sample_{snapshot_id}.csv 생성
```

포맷별 역할:

| 포맷 | 역할 | 비고 |
|---|---|---|
| 원본 payload | 원천 응답 재현 | 원래 형식 그대로 보관 |
| JSONL | row 단위 raw 파싱 결과 | 사이트별 컬럼 차이와 중첩 구조 보존에 유리 |
| MySQL | 운영 조회, 이력, 품질 감사 | 운영 단일 기준 저장소 |
| Parquet | 학습/분석 snapshot | 타입 보존과 대용량 처리에 유리 |
| CSV | 외부 공유, 수동 검수, 제출, 기존 코드 호환 | 주 저장 포맷으로 사용하지 않음 |

### 표준화 불가 값 처리 원칙

표준화 job은 값을 확정하는 단계이지, 없는 값을 만들어내는 단계가 아니다.

| 상황 | DB 처리 |
|---|---|
| 공통 컬럼으로 확정 가능 | normalized 컬럼에 저장 |
| 사이트 고유 정보 | `metadata_json`에 보존 |
| 공통 매핑 실패 | 원천 값은 보존하고 `unmapped_*` 또는 `quality_flags_json`에 기록 |
| 후보는 있으나 확정 불가 | candidate 컬럼에 저장하고 `review_status=needs_review` |
| 원천 값 없음 | null 유지 |
| 외부/수동 보강 필요 | 별도 enrichment 테이블에 기록하고 `value_source`, `confidence`, `reviewer`, `review_status`를 남김 |

`unmapped_*`(예: `unmapped_medium`)과 `unmapped` 목록은 별도 물리 컬럼이 아니라 `quality_flags_json` 내 키로 기록한다(예: `quality_flags_json.unmapped_medium`). mapping table 보강 대상 표시도 같은 방식이다.

재료/지지체/판매상태 공통 매핑(문서에서 말하는 'mapping table')은 별도 DB 테이블이 아니라 버전 관리되는 정규화 config로 두고 snapshot의 `rules_version`으로 추적한다. 작가 이름 alias만 DB 테이블 `artist_name_alias`로 관리한다.

금지:

- 국적, 생년, 성별, 갤러리, 전시 이력을 이름만 보고 채우기
- 제작연도나 재료를 작품명/설명에서 확정값처럼 추정하기
- 가격 문의 또는 가격 없음 row에 임의 가격 넣기
- 액자 크기만 있는 값을 작품 크기처럼 저장하기
- mapping table에 없는 재료를 임의로 가장 가까운 재료로 분류하기

## 4. 전체 수집 파이프라인

```text
[스케줄러]
  - 매주 원천별 수집 job 실행 (전 원천 주 1회)
  - source + run_id + snapshot_date 생성
        |
        v
[Raw 수집]
  - HTML/API/JSON/CSV 원본 응답 저장
  - HTTP 상태, URL, payload hash, 수집 시각 저장
  - 실패 row도 기록
        |
        v
[Raw 파싱]
  - 원천별 parser로 작품/작가 후보 row 추출
  - 원천 ID, 원천 URL, raw payload 참조 유지
        |
        v
[원천별 분해/정리 staging]
  - 한 컬럼에 섞인 값 분해
  - 사이트별 명칭 차이 정리
  - 작품 가격/크기/재료/판매상태 후보값 생성
  - 작가명/국적/생년/활동지/갤러리/전시 후보값 생성
        |
        v
[표준화 staging]
  - 분해/정리된 후보값을 공통 컬럼으로 변환
  - 공통 단위, 공통 통화 정책, 공통 판매상태 적용
  - 공통 작가 메타 컬럼 생성
  - 기존 artist_key 후보가 있을 때만 작가 identity 검수 후보 생성
        |
        v
[중복/변경 감지]
  - source_artwork_key 기준 upsert
  - canonical artwork 후보 생성
  - 가격/상태/작품 메타/작가 메타 변경 이력 저장
        |
        v
[품질 감사]
  - 가격 없음, placeholder 가격, 입체/영상 후보, 크기 오류, 중복률
  - 원천별 수집량 급감/급증 감지
        |
        v
[가격 통화 통일(price_conversion)]
  - 각 row collected_at 시점 환율(fx_rate_daily)로 원천 통화를 KRW로 환산(point-in-time)
  - 원천이 직접 KRW를 제공한 경우(price_krw_source)는 환산하지 않고 그대로 사용
  - price_krw_normalized, price_fx_rate, price_fx_date, price_fx_source, price_krw_is_converted 생성
        |
        v
[학습 snapshot export]
  - 특정 기준일의 stable dataset parquet 생성
  - price_krw_normalized로 통화가 통일된 row만 export 대상
  - 외부 공유/검수/기존 코드 호환이 필요하면 CSV 추가 생성
  - 모델 학습에는 export snapshot만 사용
```

## 5. MySQL 스키마 설계

이 장은 DB 스키마의 단일 기준이다. API 문서나 화면 문서에서 테이블/컬럼/상태값을 다시 정의하지 않고, 이 장의 정의를 참조한다.

API 문서는 아래 내용만 가져간다.

- 어떤 화면 기능이 어떤 테이블을 읽는지
- 어떤 버튼이 어떤 테이블의 어떤 상태를 바꾸는지
- 응답에 필요한 표시 필드가 어느 테이블에서 오는지

API 문서에는 전체 컬럼 목록을 복사하지 않는다. 컬럼 정의, enum 정의, FK 기준은 이 문서를 기준으로 한다.

### 5.0 스키마 레이어 요약

수집 데이터는 한 번에 최종 테이블로 들어가지 않는다. 운영자가 문제 원인을 추적할 수 있도록 아래 레이어를 분리한다.

```text
collector_run / raw_fetch
  - 수집 실행과 HTTP/파일 응답 단위 기록
        |
        v
source_artwork_raw / source_artist_raw
  - 원천 사이트에서 받은 작품/작가 row 보존
        |
        v
source_*_interpreted_staging
  - 원천 문자열 분해, 가격/크기/작가명 후보 추출
        |
        v
normalized_*_staging
  - 4개 사이트를 공통 컬럼으로 표준화
        |
        v
artist_name_alias / artist_identity_candidate / artist_identity
  - 작가명 표시, 동명이인 검수, 최종 artist_key 확정
        |
        v
artwork_snapshot / artwork_snapshot_item
  - 학습/운영 반영 가능한 고정 snapshot 생성
        |
        v
price_model_registry / price_model_deployment
  - 학습된 모델 버전 등록, 운영 승격, 롤백 이력 관리
```

레이어별 책임:

| 레이어 | 대표 테이블 | 역할 | 직접 수정 주체 |
|---|---|---|---|
| 수집 실행 | `collector_run`, `raw_fetch` | 언제, 어떤 방식으로, 어떤 응답을 수집했는지 기록 | crawler/job |
| 원천 raw | `source_artwork_raw`, `source_artist_raw` | 원천 사이트별 작품/작가 row 보존 | crawler/job |
| 원천 분해 | `source_artwork_interpreted_staging`, `source_artist_interpreted_staging` | 한 컬럼에 섞인 값을 후보값으로 분해 | parser/normalizer job |
| 공통 표준화 | `normalized_artwork_staging`, `normalized_artist_staging` | 4개 사이트 데이터를 공통 컬럼으로 맞춤 | normalizer job, 일부 운영자 수정 |
| 작가 identity | `artist_name_alias`, `artist_identity_candidate`, `artist_identity` | 표시명, alias, 동명이인, 최종 `artist_key` 관리 | 운영자/데이터 관리자, 일부 자동 규칙 |
| snapshot | `artwork_snapshot`, `artwork_snapshot_item` | 학습/운영 반영 기준 데이터 고정 | 데이터 관리자/job |
| 모델 운영 | `price_model_registry`, `price_model_deployment`, `price_prediction_log` | 모델 버전, 배포 이력, 예측 재현 정보 관리 | 데이터 관리자/API |
| 환율 | `fx_rate_daily` | 원천 통화를 KRW 학습 가격으로 환산 | 운영자/job |

확장성 기준:

- Artsy / Saatchi / Print Bakery / Art1 외 원천이 추가되어도 테이블을 원천별로 새로 만들지 않는다.
- 새 원천은 `source` 코드와 원천별 parser/normalizer 버전을 추가하고, 기존 raw -> interpreted staging -> normalized staging -> 검수 -> snapshot 흐름을 그대로 사용한다.
- 운영자가 수동 CSV를 업로드하는 경우도 예외 테이블에 바로 넣지 않는다. `manual_csv` 또는 구체적인 수동 원천 코드로 `source`를 부여하고, 원본 CSV row를 raw 레이어에 보존한 뒤 동일한 표준화/검수/snapshot 흐름을 태운다.
- 새 원천 또는 CSV에만 있는 컬럼은 공통 컬럼에 추측해서 넣지 않고 `metadata_json`, `parsed_parts_json`, `quality_flags_json`, unmapped 목록에 남긴다.
- 원천 등록/비활성화, parser 버전, 마지막 정상 run은 `source_registry` 물리 테이블에서 관리한다. 운영 기준은 DB다.

### 5.0.1 화면/API 참조 범위

화면과 API는 모든 테이블을 직접 다루지 않는다. 아래 표는 API 문서를 작성할 때의 참조 범위다.

| 화면/기능 | 주로 읽는 테이블 | 주로 쓰는 테이블 | 비고 |
|---|---|---|---|
| 사용자 작가 검색 | `artist_identity`, `artist_name_alias`, 필요 시 `normalized_artist_staging` | 없음 | 사용자에게 원천 사이트명/URL/ID는 노출하지 않음 |
| 사용자 신규 작가 후보 제출 | `artist_name_alias`, `artist_identity` | `normalized_artist_staging` 기반 신규 후보 상태, 검수 메모 영역 | 승인 전 `artist_key` 생성 금지 |
| 사용자 예측 결과 | 운영 모델/feature store, `artist_identity`, snapshot에서 만든 요약 feature | 없음 | 수집 DB를 실시간 예측 경로에 직접 연결하지 않는 것이 원칙 |
| 모델 버전 관리 | `price_model_registry`, `price_model_deployment` | `price_model_registry`, `price_model_deployment` | 모델 승인/승격/롤백 |
| 1차 시장 가격 카드 | snapshot 또는 별도 집계 feature store | 없음 | 사용자에게는 호당가 중앙값/범위/매체별 분포/N만 노출 |
| 수집 대시보드 | `collector_run`, `raw_fetch` 집계 | 없음 | 실패/부분 실패/품질 상태 확인 |
| 수집 run 상세 | `collector_run`, `raw_fetch`, `source_*_raw` | `collector_run.approved_*`, `override_reason` | 반영 승인/보류 사유 기록 |
| 작품 품질 검수 | `source_artwork_raw`, `source_artwork_interpreted_staging`, `normalized_artwork_staging` | `normalized_artwork_staging.quality_flags_json`, 검수 상태/메모 | 가격/크기/재료/제외 여부 판단 |
| 작가명 검수 | `normalized_artist_staging`, `artist_name_alias` | `artist_name_alias`, `normalized_artist_staging.artist_name_*_display` | 원천명과 표시명 분리 |
| artist_key 연결 검수 | `artist_identity_candidate`, `artist_identity`, `artist_name_alias` | `artist_identity_candidate.review_status`, `artist_identity` | 기존 key 연결 또는 반려 |
| 신규 작가 승인 | `normalized_artist_staging`, `artist_name_alias` | `artist_identity` | 운영자 검수 후 데이터 관리자 승인이 있을 때만 신규 `artist_key` 생성 |
| snapshot 후보 확인 | `normalized_artwork_staging`, `normalized_artist_staging`, `artist_identity`, `fx_rate_daily` | `artwork_snapshot`, `artwork_snapshot_item` | 포함/제외 사유 확정 |

주의:

- 사용자 화면 API는 원천 추적용 컬럼(`source`, `source_artwork_url`, `artist_source_id`, `artist_source_url`)을 기본 응답에 포함하지 않는다.
- 어드민 화면 API는 원천 추적용 컬럼을 표시해야 한다.
- 예측 API는 수집 DB를 직접 조회하지 않고, 승인된 snapshot과 모델 번들/feature store를 사용한다.

### 5.0.2 상태값 기준

상태값은 화면/API 문서에서 새로 만들지 않는다. 아래 enum을 기준으로 한다.

| 대상 | 컬럼 | 값 |
|---|---|---|
| 수집 run | `collector_run.status` | `running`, `success`, `partial_success`, `failed` |
| 수집 실패 분류 | `collector_run.failure_type` | `fetch_error`, `parse_error`, `rate_limited`, `blocked`, `auth_failed`, `stuck_timeout`(§5.2.1) |
| 수집 품질 | `collector_run.quality_status` | `ok`, `warning`, `blocked` |
| 가격/판매상태 | `normalized_artwork_staging.availability` | `available`, `sold`, `price_on_request`, `missing_price`, `unavailable` |
| 작가 staging 매칭 | `normalized_artist_staging.artist_identity_status` | `unmatched`, `candidate`, `auto_approved`, `approved`, `needs_review`, `match_rejected` |
| alias 검수 | `artist_name_alias.review_status` | `auto_approved`, `approved`, `needs_review`, `match_rejected` |
| alias 동명이인 | `artist_name_alias.ambiguity_status` | `unique`, `ambiguous`, `needs_review` |
| artist identity 후보 | `artist_identity_candidate.review_status` | `pending`, `auto_approved`, `approved`, `match_rejected`, `needs_review` |
| artist identity 후보 모호성 | `artist_identity_candidate.ambiguity_status` | `unique`, `ambiguous`, `needs_review` |
| 최종 작가 키 | `artist_identity.identity_status` | `active`, `merged` |
| snapshot 포함 | `artwork_snapshot_item.include_status` | `included`, `excluded` |
| 모델 버전 | `price_model_registry.model_status` | `candidate`, `approved`, `retired`, `rejected` |
| 모델 배포 | `price_model_deployment.deployment_status` | `active`, `inactive`, `rolled_back` |

`needs_review`는 최종 작가 키 상태가 아니다. 검수 큐 또는 staging 단계의 상태다. 최종 운영 `artist_key`는 `artist_identity.identity_status=active`일 때만 서비스/모델에서 사용한다.

`blocked`는 수집 run 품질 상태다. 사용자 화면에는 노출하지 않고, 어드민에서는 “snapshot 자동 반영 차단”으로 설명한다.

### 5.0.3 쓰기 책임과 승인 이력

운영 중 같은 컬럼을 여러 주체가 동시에 수정하면 재현성이 깨진다. 따라서 쓰기 책임을 아래처럼 둔다.

| 데이터 | 자동 job 쓰기 | 운영자 쓰기 | 비고 |
|---|---|---|---|
| raw 응답/원천 row | 가능 | 불가 | 원천 보존 영역이므로 운영자가 직접 수정하지 않음 |
| interpreted 후보값 | 가능 | 원칙적으로 불가 | parser 재실행으로 수정 |
| normalized 후보값 | 가능 | 제한적 가능 | 운영자 수정은 사유와 처리자 기록 필요 |
| 작가 표시명/alias | 후보 생성 가능 | 승인/수정/반려 가능 | 원천명은 보존, 표시명은 별도 컬럼 |
| artist_key 연결 | 자동 확정 조건 통과 시 가능 | 검수 큐 검토(보류/반려/연결 제안) | 신규 `artist_key` 생성과 기존 키 연결 확정은 데이터 관리자 승인 후 |
| snapshot 생성 | job 생성 가능 | 반영 보류 요청 | snapshot 생성 승인은 데이터 관리자 권한이다. run 단위 반영 보류/승인은 운영자(`collector_run.approved_*`). 생성 시 rules_version과 cutoff 기록 |

운영 초기에는 슈퍼유저가 운영자와 데이터 관리자 권한을 모두 가진 어드민으로 위 수동 조치를 처리할 수 있다. 이 경우에도 실제 처리자, 처리시각, 처리 사유는 반드시 남긴다.

수동 조치가 들어가는 테이블에는 최소 아래 기록이 필요하다.

- `approved_by`
- `approved_at`
- `approval_note`
- `rejected_by`
- `rejected_at`
- `reject_reason`

해당 컬럼이 아직 본문 테이블에 명시되지 않은 경우, DDL 작성 시 위 승인/반려 이력 컬럼을 추가한다.

### 5.0.4 API 문서 작성 전 확정해야 할 스키마 항목

API 문서를 확정하기 전에 아래 항목만 이 문서 기준으로 확인한다.

| 확인 항목 | 기준 위치 |
|---|---|
| 원천 등록/비활성화와 수집 방식 관리 위치 | 5.1 |
| 사용자 작가 검색 응답에 원천 사이트 정보를 제외하는지 | 5.0.1 |
| 신규 작가 후보가 승인 전 `artist_key`를 만들지 않는지 | 5.11, 5.12 |
| 신규 작가 후보 큐가 물리 테이블인지 view/export인지 | 5.0.5 |
| 어드민 검수 큐 상태값이 어디에 저장되는지 | 5.9, 5.10, 5.11 |
| 작품 품질 검수 결과가 어디에 남는지 | 5.8 |
| 수집 실패와 품질 차단이 어떤 상태값인지 | 5.2, 5.0.2 |
| snapshot 포함/제외가 어디에 남는지 | 5.13, 5.14 |
| snapshot 확정요청/생성승인 2단계가 어디에 남는지 | 5.14.1 |
| 작품 필드 단위 변경(approve_with_patch) audit이 어디에 남는지 | 5.8.1 |
| snapshot이 고정한 작가 identity 버전과 멤버십 as-of 조회 | 5.13, 5.12.2 |
| 1차 시장 가격 카드가 어떤 원천 필드를 노출하지 않아야 하는지 | 5.0.1 |
| 모델 버전과 운영 배포 이력이 어디에 남는지 | 5.17, 5.18 |
| 예측 결과가 어떤 모델에서 나왔는지 재현 가능한지 | 5.19 |

### 5.0.5 신규 작가 후보 큐 기준

신규 작가 후보 큐는 최종 `artist_key` 테이블이 아니다. 1차 적용에서는 별도 물리 테이블을 필수로 만들지 않고, `normalized_artist_staging`과 `artist_name_alias`를 기준으로 만든 SQL view 또는 CSV export로 운영해도 된다.

신규 작가 후보가 되는 조건:

- 같은 `source + artist_source_id`에 이미 연결된 active `artist_key`가 없다.
- 같은 alias 또는 승인 alias로 연결 가능한 기존 `artist_key` 후보가 없다.
- 원천 작가명과 원천 작가 URL 또는 `source_artist_raw_id`처럼 최소 식별값이 있다.
- 작품 row 연결 정보가 있다.

처리 원칙:

- 신규 후보 단계에서는 `artist_identity.artist_key`를 만들지 않는다.
- 운영자 검수를 거쳐 데이터 관리자가 신규 작가 생성을 승인하면 그때 `artist_identity`에 `identity_status=active`인 최종 `artist_key`를 생성한다.
- 기존 작가와 같은 인물이라고 판단되면 신규 생성 대신 기존 `artist_key`에 연결한다(연결 확정은 데이터 관리자 승인).
- 보류 또는 반려된 후보는 원천 row를 삭제하지 않고 검수 상태와 사유를 남긴다.

API/화면 관점:

- 사용자 화면은 신규 작가 후보를 제출할 수 있지만, 최종 `artist_key` 생성 여부는 보여주지 않는다.
- 어드민 화면은 신규 후보의 원천 작가명, 표시명 후보, 작품 목록, 후보 없음 사유, 승인/보류/반려 버튼을 제공한다.
- API 문서에서는 “신규 작가 후보 등록”과 “신규 artist_key 생성 승인”을 별도 기능으로 분리한다.

### 5.1 source_registry

수집 원천의 운영 설정을 저장한다. 새 원천 사이트나 수동 CSV source가 추가되어도 코드에 하드코딩하지 않고 이 테이블에 등록한 뒤 같은 수집/검수/snapshot 흐름을 사용한다.

| 컬럼 | 설명 |
|---|---|
| `source` | 원천 코드 PK. 예: `artsy`, `saatchi`, `printbakery`, `art1`, `manual_csv` |
| `display_name` | 어드민 화면 표시명 |
| `source_type` | `marketplace`, `gallery_csv`, `manual_csv`, `internal` 등 원천 유형 |
| `collection_mode` | `api`, `html`, `crawler`, `csv_upload` |
| `raw_payload_format` | `json`, `html`, `csv`, `mixed` |
| `is_enabled` | 정기 수집 활성 여부 |
| `allow_manual_upload` | 해당 source로 수동 업로드를 허용하는지 |
| `default_parser_version` | 이 원천의 기본 parser 버전. run 재현 기준은 `collector_run.collector_version` |
| `default_normalizer_version` | 이 원천의 기본 normalizer 버전. snapshot 재현 기준은 `artwork_snapshot.rules_version` |
| `schedule_cron` | 정기 수집 주기. 수동 CSV 전용이면 null 가능 |
| `request_delay_sec` | 기본 요청 간격 |
| `max_concurrency` | 동시 요청 상한. 원천 부하/차단 대응용. 권장 기본값은 확정 필요 |
| `daily_request_cap` | 1일 요청 상한. 초과 시 수집을 멈추고 다음 주기로 미룬다. 상한값은 확정 필요 |
| `user_agent` | 요청에 사용할 User-Agent 문자열. 원천별로 다르게 둘 수 있다 |
| `backoff_policy_json` | 재시도 backoff 정책: 초기 지연(`initial_delay_sec`), 최대 재시도(`max_retries`), 지수 배수(`multiplier`). 구체 수치는 확정 필요 |
| `robots_policy` | robots.txt 준수 여부와 근거. 예: `respect`/`override_with_reason`와 근거 메모 |
| `last_success_run_id` | 마지막 성공 run 캐시. 물리 FK는 걸지 않는다 |
| `last_failed_run_id` | 마지막 실패 run 캐시. 물리 FK는 걸지 않는다 |
| `paused_reason` | 수집 일시 중지 사유. 원천 차단(`blocked`)/`rate_limited`/`auth_failed`가 반복되면 watchdog 또는 collector가 이 값을 채워 자동 일시 중지한다 |
| `created_by` | 등록자 |
| `created_at` | 등록 시각 |
| `updated_by` | 마지막 수정자 |
| `updated_at` | 마지막 수정 시각 |

운영 원칙:

- `source_registry.is_enabled=false`인 source는 정기 크론에서 제외한다.
- 수동 CSV는 `collection_mode=csv_upload`로 등록한다.
- 기본 parser/normalizer 버전을 바꾸면 이후 run부터 적용하고, 과거 run은 당시 `collector_run.collector_version`과 snapshot `rules_version`으로 재현한다.
- `last_success_run_id`와 `last_failed_run_id`는 어드민 조회 성능을 위한 캐시값이다. `collector_run.source -> source_registry.source` FK만 두고, 반대 방향 FK는 만들지 않는다.
- source를 삭제하지 않는다. 더 이상 쓰지 않는 원천은 `is_enabled=false`와 `paused_reason`으로 관리한다.
- `max_concurrency`, `daily_request_cap`, `request_delay_sec`, `user_agent`, `backoff_policy_json`, `robots_policy`는 원천 차단 대응의 운영 설정이다. 코드에 하드코딩하지 않고 이 테이블 값을 collector가 읽어 적용한다.
- 같은 원천에서 `rate_limited`(429) 또는 `blocked`(403/WAF/challenge)가 반복되면 collector는 즉시 중단하고 `paused_reason`을 채워 자동 일시 중지한다. 재개는 운영자가 `is_enabled`/`paused_reason`을 정리한 뒤에만 한다.

### 5.2 collector_run

수집 실행 단위를 기록한다.

| 컬럼 | 설명 |
|---|---|
| `id` | run PK |
| `source` | `source_registry.source` 참조. `NOT NULL`(generated `active_source_lock`의 활성 분기 base 컬럼이라 NULL이면 NULL-unique 누수가 생긴다) |
| `collector_name` | 실행 스크립트/모듈명 |
| `collector_version` | 코드 버전 또는 git SHA. run 시작 시 자동 캡처. 파서도 함께 배포되므로 이 값으로 갈음 |
| `started_at` | 시작 시각 |
| `finished_at` | 종료 시각 |
| `status` | `running`, `success`, `partial_success`, `failed`. `NOT NULL`(generated `active_source_lock`의 활성 분기 base 컬럼) |
| `failure_type` | `status`가 `failed`/`partial_success`일 때의 실패 분류. §5.2.1 표 참조. 정상 종료면 null |
| `heartbeat_at` | 실행 중인 수집 job이 주기적으로 갱신하는 lease 시각. watchdog 좀비 run 회수와 single-flight 판정에 사용(§5.2.2) |
| `active_source_lock` | 생성 컬럼. 타입은 베이스 컬럼 `source`와 동일한 `VARCHAR(64)`. `VARCHAR(64) GENERATED ALWAYS AS (CASE WHEN status='running' THEN source END) STORED`. source별 `running` 1개만 강제하는 DB 백스톱 유니크(`uq_running_source`)의 키. `running`이 아닌 행은 NULL이라 제약에서 빠진다(§5.2.2, §5.16) |
| `quality_status` | `ok`, `warning`, `blocked`. 수집은 끝났어도 품질 기준 미달 여부를 구분한다. `blocked`와 `failed`만 학습 snapshot 자동 반영을 막는다. `warning`은 soft(필수 row 자동 반영+사후 확인), `blocked`는 운영자 승인(`override_reason`)으로 해제 가능 |
| `quality_flags_json` | 품질 경고/차단 사유와 위반한 기준 지표 요약 |
| `approved_by` | warning/partial_success run을 snapshot 반영 승인한 운영자 ID. 자동 승인은 비우거나 system |
| `approved_at` | run 반영 승인 시각 |
| `approval_note` | 반영 승인/보류/회수/확인 조치 내용과 사유 메모. 조치 유형을 나누는 별도 필드는 후속 고도화 항목 |
| `override_reason` | `blocked` 해제/수동 반영 사유 |
| `snapshot_date` | 수집 기준일 |
| `request_delay_sec` | 요청 간격 |
| `manual_import_file_id` | 수동 CSV 업로드로 생성된 run이면 `manual_import_file.id`, 일반 crawler run이면 null |
| `total_requested` | 요청 수 |
| `total_success` | 성공 수 |
| `total_failed` | 실패 수 |
| `raw_artwork_rows` | raw 작품 row 수 |
| `raw_artist_rows` | raw 작가 row 수 |
| `interpreted_artwork_rows` | 작품 원천별 분해/정리 row 수 |
| `interpreted_artist_rows` | 작가 원천별 분해/정리 row 수 |
| `normalized_artwork_rows` | 작품 표준화 row 수 |
| `normalized_artist_rows` | 작가 표준화 row 수 |
| `summary_json` | run별 요약 |

#### 5.2.1 실패 분류(failure_type)

`collector_run.failure_type`은 `status`가 `failed` 또는 `partial_success`일 때 실패 원인을 분류한다. 정상 종료면 null이다.

| 값 | 의미 | 후속 처리 |
|---|---|---|
| `fetch_error` | 네트워크/HTTP 5xx/타임아웃 등 일반 수집 실패 | backoff 재시도 후 실패면 재수집 대상 |
| `parse_error` | 응답은 받았으나 파싱 실패 | parser fixture 점검, raw 보존 후 재처리 |
| `rate_limited` | HTTP 429 등 원천 요청 제한 | backoff 적용, 반복 시 `paused_reason` 설정 후 자동 일시 중지 |
| `blocked` | HTTP 403/WAF/challenge 등 원천 차단 | 즉시 중단, `source_registry.paused_reason` 설정, 운영자 확인 전까지 재개 금지 |
| `auth_failed` | 인증 실패/API 키·토큰 만료(예: Cafe24 app key) | 자격증명 회전 후 재실행. §5.20 참조 |
| `stuck_timeout` | heartbeat 임계 초과 또는 max runtime 초과로 watchdog가 회수 | watchdog가 `failed` 전환(§5.2.2) |

`rate_limited`/`blocked`/`auth_failed`/`stuck_timeout`은 §5.0.2의 `status`/`quality_status` enum과 별개로 실패 세부 원인을 남기는 값이다. 화면/API 문서에서 새로 정의하지 않고 이 표를 기준으로 한다.

#### 5.2.2 single-flight 보장과 좀비 run 회수

같은 source의 수집 run이 동시에 두 개 이상 실행되면 raw 중복 적재와 `last_success_run_id` 갱신 충돌이 생긴다. 또 cron job이 비정상 종료하면 `status='running'` 행이 남아 이후 수집이 막힌다. 이를 막기 위해 single-flight 락과 watchdog 회수를 둔다.

single-flight 보장(source별 단일 실행):

- 메커니즘은 `flock` 기반 per-source 락파일이 1차 single-flight이고, DB 유니크가 백스톱이다. 락파일은 OS 레벨에서 같은 호스트의 중복 실행을 막는다.
- DB 백스톱: 같은 `source`에 `status='running'`인 `collector_run` 행이 이미 있으면 신규 running 생성을 DB 유니크가 거부한다.
- MySQL/InnoDB는 Postgres식 `... WHERE 조건` 부분 유니크 인덱스를 지원하지 않으므로, 생성 컬럼 + 유니크 키로 같은 효과를 낸다. `collector_run`에 생성 컬럼 `active_source_lock VARCHAR(64) GENERATED ALWAYS AS (CASE WHEN status='running' THEN source END) STORED`를 두고 `UNIQUE KEY uq_running_source (active_source_lock)`를 건다(§5.16). 생성 컬럼 타입은 참조 베이스 컬럼 `source`와 동일하게 `VARCHAR(64)`로 맞춘다(베이스 컬럼 길이가 바뀌면 함께 맞춘다). MySQL 유니크는 NULL을 다중 허용하므로 `running`이 아닌 행은 `active_source_lock`이 NULL이 되어 제약에서 빠지고, source별 `running` 행은 1개만 강제된다. 활성 행의 base 컬럼(`source`/`status`)은 `NOT NULL`이라 활성 분기에서 키가 NULL이 되어 중복 활성이 새는 NULL-unique 누수는 없다.

watchdog 좀비 run 회수:

- 실행 중인 수집 job은 `heartbeat_at`을 주기적으로 갱신한다.
- watchdog는 `heartbeat_at`이 임계(확정 필요, 예: 2h)를 초과했거나 run의 max runtime(확정 필요)을 초과한 `status='running'` 행을 회수한다.
- 회수 시 `status='failed'`, `failure_type='stuck_timeout'`으로 전환한다. 이로써 해당 행의 `active_source_lock`이 NULL이 되어 `uq_running_source` 유니크가 풀려 다음 run이 생성될 수 있고, `last_success_run_id` 갱신이 막히는 문제도 해소된다.
- watchdog는 수집 호스트와 분리된 외부 스케줄러/모니터에서 실행한다. 수집 호스트가 멈춰도 회수가 동작해야 하기 때문이다(스케줄러 미실행 감지는 [주기 수집 운영 문서](weekly_crawler_mysql_operation_plan_20260624.md)의 heartbeat 알림과 연계).

### 5.3 raw_fetch

URL/API 요청 단위 원본을 저장한다.

| 컬럼 | 설명 |
|---|---|
| `id` | raw fetch PK |
| `run_id` | collector_run FK |
| `source` | 원천 |
| `fetch_type` | `list`, `detail`, `artist`, `search`, `export` |
| `url_sanitized` | 비밀 파라미터를 마스킹한 요청 URL. 원문 URL과 비밀 파라미터 원본은 DB에 저장하지 않는다 |
| `url_hash` | `SHA256(request_fingerprint)`. 긴 URL을 고정 길이로 인덱싱하고 같은 요청을 식별하기 위한 값. `request_fingerprint` 정규화 규칙은 아래 참조. 유니크 키 구성에 사용(§5.16) |
| `request_params_json` | 요청 파라미터. 비밀 파라미터(예: `cafe24_app_key`)는 저장 전 마스킹한다. 비밀 원본은 저장 금지 |
| `http_status` | HTTP 상태 |
| `content_type` | 응답 타입 |
| `payload_hash` | 응답 본문 hash. 같은 응답 중복 적재 방지와 유니크 키에 사용 |
| `payload_size` | 응답 바이트 크기 |
| `payload_path` | object storage 경로. raw 본문은 object storage에 저장하고 DB에는 경로만 둔다 |
| `error_message` | 실패 메시지 |
| `fetched_at` | 수집 시각 |

필수: raw payload 본문은 1차 운영부터 object storage에 저장하고, MySQL에는 `payload_hash`, `payload_path`, `payload_size`와 요약만 저장한다. DB에 본문(`MEDIUMTEXT`)을 직접 넣는 방식은 단기 PoC 한정으로만 허용하며, 운영 적용에서는 사용하지 않는다.

마스킹/시크릿 원칙(§5.20과 연계):

- 원문 `url`은 저장하지 않는다. `url_sanitized`(비밀 파라미터 마스킹본)와 `url_hash`만 남긴다. `request_params_json`도 비밀 파라미터(예: `cafe24_app_key`)를 마스킹한 뒤에만 저장하고, 비밀 원본은 DB에 저장하지 않는다.
- 인덱싱과 중복 판정은 마스킹과 무관한 `url_hash`(= `SHA256(request_fingerprint)`)와 `payload_hash`로 한다.

`request_fingerprint` 정규화 규칙(`url_hash` 입력):

- 호스트는 소문자화한다.
- query 파라미터는 키 기준으로 정렬한다.
- 휘발성 tracking 파라미터(예: `utm_*`, `fbclid`, `gclid`, 세션/타임스탬프성 파라미터)는 제거한다.
- 비밀 파라미터(예: `cafe24_app_key`, 토큰)는 fingerprint에서 제외한다. 키 회전 시 같은 요청이 다른 hash로 잡혀 중복 적재되는 것을 막기 위해서다.
- 요청을 구분하는 API 파라미터(페이지/필터/ID 등)와 POST body 파라미터는 포함한다. 서로 다른 요청이 같은 hash가 되지 않도록 한다.
- 제거/포함 대상 목록(특히 tracking·secret 파라미터 화이트/블랙리스트)은 원천별로 다를 수 있으며 구체 목록은 확정 필요.
- 보수적 기본값(목록 확정 전): secret/tracking 목록이 확정되기 전까지는 secret denylist만 제외하고, 나머지 query/body 파라미터는 모두 fingerprint에 포함한다. 서로 다른 요청이 같은 hash가 되는 위험(과병합)을 우선 차단하기 위해서다. 같은 요청이 여러 hash로 잡히는 과분할은 raw가 일부 중복될 뿐 안전하므로, 목록이 확정되면 그때 tracking 제외를 넓힌다.

raw 무한 증가 대비:

- `raw_fetch`와 raw 레이어 테이블은 `snapshot_date`(또는 월) 기준 파티셔닝을 적용해 조회/삭제 비용을 낮춘다.
- raw payload(object storage)와 DB raw row의 보존기간(확정 필요)을 정하고, 만료분은 일괄 정리한다. 비가역 identity 결정과 snapshot은 보존기간 정리 대상이 아니다.

### 5.3.1 manual_import_file

운영자가 업로드한 CSV 파일 메타를 저장한다. 실제 row 처리는 예외 경로로 보내지 않고 `collector_run`에 `collection_mode=csv_upload` 성격의 run을 생성한 뒤 `source_artwork_raw` / `source_artist_raw` 레이어부터 동일하게 처리한다.

| 컬럼 | 설명 |
|---|---|
| `id` | 수동 업로드 파일 ID |
| `source` | `source_registry.source` 참조. 예: `manual_csv`, `gallery_csv_abc` |
| `file_name` | 업로드 원본 파일명 |
| `file_uri` | 파일 저장 위치 |
| `file_hash` | 파일 hash |
| `encoding` | 감지 또는 입력한 encoding |
| `delimiter` | CSV delimiter |
| `uploaded_by` | 업로드 관리자 |
| `uploaded_at` | 업로드 시각 |
| `detected_columns_json` | 감지된 원본 컬럼 목록 |
| `column_mapping_json` | 운영자가 확정한 원본 컬럼 -> 표준 후보 컬럼 매핑 |
| `mapping_status` | `pending`, `approved`, `rejected` |
| `mapping_approved_by` | 매핑 승인자 |
| `mapping_approved_at` | 매핑 승인 시각 |
| `linked_run_id` | 매핑 승인 후 생성한 `collector_run.id`. 캐시값이며 물리 FK는 선택 |

운영 원칙:

- CSV 업로드 직후에는 학습 데이터가 아니다.
- 매핑 승인 전에는 raw row를 표준화하지 않는다.
- 매핑 승인 후 `collector_run.status=running`, `collector_run.source=manual_import_file.source`, `collector_run.manual_import_file_id=manual_import_file.id`인 run을 생성한다.
- 각 CSV row는 원본 그대로 raw payload에 보존하고, 이후 일반 수집 row와 동일하게 interpreted/normalized/검수/snapshot 흐름을 탄다.

### 5.4 source_artwork_raw

원천별 작품 row를 저장한다. 원천별 컬럼 차이를 보존하기 위한 raw structured table이다. 작품 관련 부가 정보는 이 테이블의 `metadata_json`에 저장하고, 작가 프로필/이력처럼 작가 자체에 속하는 정보는 `source_artist_raw.metadata_json`에 분리 저장한다.

| 컬럼 | 설명 |
|---|---|
| `id` | PK |
| `run_id` | collector_run FK |
| `raw_fetch_id` | raw_fetch FK |
| `source` | 원천 |
| `source_artwork_id` | 원천 작품 ID. Art1 `goods_id`, Print Bakery `product_no`, Artsy/Saatchi id/slug |
| `source_artwork_url` | 작품 URL |
| `title_raw` | 원천 작품명 |
| `artist_name_raw` | 원천 작가명 |
| `artist_source_id` | 원천 작가 ID/slug가 있으면 저장 |
| `price_raw` | 가격 원문 |
| `price_currency_raw` | 원천 통화 |
| `price_amount_raw` | 원천 숫자 가격 |
| `width_raw` | 원천 가로 |
| `height_raw` | 원천 세로 |
| `depth_raw` | 원천 깊이 |
| `dimensions_raw` | 크기 원문 |
| `medium_raw` | 재료/매체 원문 |
| `category_raw` | 원천 카테고리 |
| `availability_raw` | 판매상태 원문 |
| `image_url` | 이미지 URL |
| `year_raw` | 제작연도 원문 |
| `metadata_json` | 원천별 추가 필드 |
| `row_hash` | 주요 필드 hash |
| `collected_at` | 수집 시각 |

멱등 기준:

- `source_artwork_raw`는 run별 append다. 같은 작품이라도 run이 다르면 새 row가 쌓인다.
- 유니크 `(run_id, source, source_artwork_id)`는 한 run 안에서 같은 작품을 중복 insert하지 않게 하는 run 내 멱등용이다. run 간 중복 방지가 아니다.
- `row_hash`는 raw insert 제약(유니크)이 아니다. 정규화/`_current` view에서 직전 row 대비 unchanged vs changed를 판정하고 변경을 감지하는 데 쓴다. 즉 raw는 무조건 append하고, 변경 여부 판정은 `row_hash` 비교로 한다.

### 5.5 source_artist_raw

작가 메타를 원천별로 저장한다. 작가 소개문, 학력, 전시, 수상, 프로젝트, 소장처, 홈페이지, SNS처럼 작가 자체에 속하는 부가 정보는 이 테이블의 `metadata_json`에 저장한다. 작품 설명, 액자, 배송, edition처럼 작품에 속하는 정보는 `source_artwork_raw.metadata_json`에 둔다.

| 컬럼 | 설명 |
|---|---|
| `id` | PK |
| `run_id` | collector_run FK |
| `source` | 원천 |
| `artist_source_id` | 원천 작가 ID/slug |
| `artist_source_url` | 원천 작가 페이지 URL |
| `artist_name_raw` | 작가명 |
| `nationality_raw` | 국적 |
| `birth_year_raw` | 출생연도 |
| `gender_raw` | 성별 |
| `location_raw` | 활동지/도시 |
| `gallery_raw` | 갤러리 |
| `bio_raw` | 소개문 |
| `education_raw` | 학력 원문 |
| `exhibition_raw` | 전시/이력 |
| `metadata_json` | 추가 메타 |
| `row_hash` | 주요 필드 hash |
| `collected_at` | 수집 시각 |

### 5.6 source_artwork_interpreted_staging

raw에서 바로 공통 표준으로 가지 않고, 사이트별 원문을 먼저 분해하고 정리하는 중간 결과다.

작품 설명과 작가 소개가 한 원문에 섞여 있으면 raw에는 원문 전체를 보존하고, 이 단계에서는 작품 관련 후보만 분리한다. 작가 관련 후보는 `source_artist_interpreted_staging`에서 분리한다.

> 설계 메모(interpreted/normalized 분리 근거와 단순화 옵션): 두 단계를 물리 테이블로 나누는 이유는 분해 실패(원문 파싱 단계)와 표준화 실패(공통 컬럼 변환 단계)를 구분해 운영자가 원인을 빠르게 찾고, raw 재수집 없이 해당 단계만 재처리하기 위해서다. 다만 현재 원천 규모(원천별 수천 row)에서는 물리 테이블 2벌이 과할 수 있다. 따라서 interpreted 결과를 별도 테이블 대신 `normalized_*_staging`의 `*_candidate` 컬럼과 `parsed_parts_json`/`quality_flags_json`에 흡수하는 단순화 옵션도 허용한다. 단, 이 경우에도 분해 실패와 표준화 실패 플래그는 구분해 남겨야 두 방식의 추적성이 동일해진다. 어느 방식을 채택하는지는 §12 1차 적용 범위를 따른다.

| 컬럼 | 설명 |
|---|---|
| `id` | PK |
| `source_artwork_raw_id` | source_artwork_raw FK |
| `source` | 원천 |
| `source_artwork_id` | 원천 작품 ID |
| `title_candidate` | 작품명 후보 |
| `artist_name_candidate` | 작가명 후보 |
| `artist_source_id_candidate` | 원천 작가 ID 후보 |
| `price_text_candidate` | 가격 문구 후보 |
| `price_currency_candidate` | 통화 후보 |
| `price_amount_candidate` | 숫자 가격 후보 |
| `price_status_candidate` | 가격 문의/판매완료/가격 없음 후보 |
| `width_cm_candidate` | 가로 cm 후보 |
| `height_cm_candidate` | 세로 cm 후보 |
| `depth_cm_candidate` | 깊이 cm 후보 |
| `frame_width_cm_candidate` | 액자 가로 cm 후보. 작품 크기와 분리 보존(모델 피처로는 쓰지 않음) |
| `frame_height_cm_candidate` | 액자 세로 cm 후보 |
| `size_basis_candidate` | 크기 기준 플래그: `artwork`/`frame_inclusive`(액자 포함·작품 크기 미상)/`unknown`. 액자만 표기된 row는 작품 width/height를 비우고 액자 치수는 frame_* 에 보존 |
| `medium_text_candidate` | 재료/매체 후보 |
| `support_text_candidate` | 지지체 후보 |
| `medium_alias_applied` | 사이트별 재료 명칭 매핑 적용 여부 |
| `availability_candidate` | 판매상태 후보 |
| `artwork_description_candidate` | 작품 설명 후보 |
| `parsed_parts_json` | 원문에서 분해된 세부 값 |
| `quality_flags_json` | 분해 실패/검수 필요 플래그 |
| `interpreted_at` | 분해/정리 시각 |

### 5.7 source_artist_interpreted_staging

작가 raw를 바로 최종 작가 키로 쓰지 않고, 원천별 작가 정보를 먼저 분해하고 정리하는 중간 결과다.

작품 row에서 작가 소개문 후보가 발견되더라도 곧바로 작가 확정 컬럼에 넣지 않는다. 원천 작가 ID, 작가명, 작가 페이지 URL 등과 연결 가능한 경우에만 후보로 저장하고, 불확실하면 `quality_flags_json`에 검수 필요 사유를 남긴다.

| 컬럼 | 설명 |
|---|---|
| `id` | PK |
| `source_artist_raw_id` | source_artist_raw FK |
| `source` | 원천 |
| `artist_source_id_candidate` | 원천 작가 ID/slug 후보 |
| `artist_source_url_candidate` | 원천 작가 페이지 URL 후보 |
| `artist_name_display_candidate` | 표시용 작가명 후보 |
| `artist_name_ko_candidate` | 한글 작가명 후보 |
| `artist_name_en_candidate` | 영문 작가명 후보 |
| `artist_name_normalized_candidate` | 비교용 정규화 이름 후보 |
| `nationality_candidate` | 국적 후보 |
| `gender_candidate` | 성별 후보 |
| `birth_year_candidate` | 출생연도 후보 |
| `birth_year_source` | 출생연도 후보의 출처. 예: `structured_field`, `birth_context_text`, `year_only_text`, `manual` |
| `birth_year_confidence` | 출생연도 후보 신뢰도. 자동 artist_key 확정에는 `high`만 사용 |
| `death_year_candidate` | 사망연도 후보 |
| `location_city_candidate` | 활동 도시 후보 |
| `location_country_candidate` | 활동 국가 후보 |
| `gallery_name_candidate` | 갤러리 후보 |
| `solo_count_candidate` | 개인전 수 후보 |
| `group_count_candidate` | 단체전 수 후보 |
| `fair_count_candidate` | 아트페어 수 후보 |
| `total_shows_candidate` | 전체 전시 수 후보 |
| `followers_candidate` | 팔로워 수 후보 |
| `for_sale_works_candidate` | 판매중 작품 수 후보 |
| `total_works_candidate` | 등록 작품 수 후보 |
| `education_text_candidate` | 학력 후보 |
| `exhibition_text_candidate` | 전시/이력 후보 |
| `bio_text_candidate` | 작가 소개문 후보. 다른 문서의 `artist_bio_candidate`와 동일 컬럼 |
| `website_url_candidate` | 홈페이지 후보 |
| `instagram_url_candidate` | 인스타그램 후보 |
| `identity_hint_json` | 작가 매칭 후보 생성에 사용할 보조 정보 |
| `quality_flags_json` | 동명이인 위험/이름 충돌/메타 부족 플래그 |
| `interpreted_at` | 분해/정리 시각 |

### 5.8 normalized_artwork_staging

원천별 분해/정리 staging을 입력으로 받아 만든 학습 데이터 생성 전의 표준화 결과다.

| 컬럼 | 설명 |
|---|---|
| `id` | PK |
| `source_artwork_raw_id` | source_artwork_raw FK |
| `source_artwork_interpreted_id` | source_artwork_interpreted_staging FK |
| `source` | 원천 |
| `source_artwork_key` | `source + source_artwork_id` 기반 고유키 |
| `source_artwork_id` | 원천 작품 ID |
| `source_artwork_url` | 원천 작품 URL |
| `title` | 정리된 작품명 |
| `artist_name` | 정리된 작가명 |
| `artist_source_id` | 원천 작가 ID/slug가 있으면 저장 |
| `normalized_artist_id_candidate` | normalized_artist_staging과 연결 가능한 경우의 후보 ID |
| `artist_identity_status` | `unmatched`, `candidate`, `auto_approved`, `approved`, `needs_review`, `match_rejected` |
| `price_raw` | 원천 가격 문자열 원문 |
| `price_currency` | 통화 |
| `price_amount` | 통화 기준 숫자 가격 |
| `price_type` | 가격 라벨: `retail_ask`(판매 호가)/`auction_hammer`(경매 낙찰가)/`estimate`(추정가). 현재 4개 원천은 전부 `retail_ask`([원천 사이트별 수집 항목 정리](source_site_collected_fields_20260624.md)) |
| `price_tax_basis` | 세금/수수료 포함 여부: `tax_incl`/`tax_excl`/`unknown`. 현재 4개 원천은 대부분 `unknown` |
| `price_krw_source` | 원천이 KRW를 제공한 경우만 저장 |
| `price_krw_normalized` | KRW로 통일한 가격. `price_conversion` 단계에서 채운다. 원천 KRW(`price_krw_source`)가 있으면 그대로, 없으면 `price_currency`+`price_amount`를 row `collected_at` 시점 기준일 환율로 환산(§5.15) |
| `price_fx_rate` | 환산에 사용한 환율값. point-in-time 재현용 |
| `price_fx_date` | 환산에 사용한 환율 기준일(= 각 row `collected_at` 시점 기준). 환율 정책이 바뀌어도 이 기준일로 재환산해 재현 가능 |
| `price_fx_source` | 환산에 사용한 환율 출처(§5.15). point-in-time 재현용 |
| `price_krw_is_converted` | 환산값이면 `true`, 원천 KRW(`price_krw_source`)를 그대로 쓰면 `false`(BOOL). 이후 절·`artwork_snapshot_item`이 요구하는 값을 단일 물리 기록점인 이 staging에 둔다 |
| `width_cm` | cm 가로 |
| `height_cm` | cm 세로 |
| `depth_cm` | cm 깊이 |
| `area_cm2` | 계산 면적 |
| `medium_raw` | 원천 재료 |
| `medium_category_candidate` | 분류 후보 |
| `is_3d_candidate` | 입체 후보 |
| `availability` | 판매상태: `available`/`sold`/`price_on_request`/`missing_price`/`unavailable` |
| `image_url` | 이미지 URL |
| `artwork_year` | 제작연도 |
| `metadata_json` | 사이트별 작품 추가 정보 |
| `quality_flags_json` | 가격 없음, 크기 오류 등 |
| `normalized_at` | 표준화 시각 |

가격/환율 재현 메모:

- `price_type`/`price_tax_basis`/`price_krw_normalized`/`price_fx_rate`/`price_fx_date` 컬럼명은 [원천 사이트별 수집 항목 정리](source_site_collected_fields_20260624.md)와 일치한다.
- 물리적 기록점은 한 곳이다: `price_type`/`price_tax_basis`/`price_krw_normalized`/`price_fx_rate`/`price_fx_date`/`price_fx_source`/`price_krw_is_converted`는 `price_conversion` 단계에서 1회 계산되어 `normalized_artwork_staging`에 저장된다. 이 `price_conversion` 단계는 snapshot export 준비 과정의 일부로 실행되며, 동일 값이 export 산출물에 그대로 반영된다(이중 기록 없음). raw/interpreted 단계에서는 원천 통화를 그대로 보존한다(§5.15).
- 각 row의 `price_fx_date`를 그 row의 `collected_at` 시점 기준일로 고정하므로, 환율 정책/소스가 바뀌어도 같은 기준일 환율로 재환산해 point-in-time 가격을 재현할 수 있다. 환율 재현은 이 문서(SoT)의 `fx_rate_daily`(§5.15)와 위 컬럼만으로 충족된다.

### 5.8.1 normalized_artwork_change_event (append-only)

작품 normalized 값에 대한 어드민 검수 결정(특히 필드 단위 patch)은 현재 상태 컬럼만으로는 before/after 추적이 약하다. normalized 후보값 자체는 불변(parser/normalizer 재실행으로만 갱신)으로 두고, 운영자 patch는 override 레이어로 분리한다. 그 변경 이력을 append-only로 남기는 테이블이며, 어드민 audit before/after의 SoT다.

| 컬럼 | 설명 |
|---|---|
| `change_event_id` | PK. **커밋 순서로 부여되는 gap-free 단조 증가 시퀀스**다(이것이 id 의미의 단일 정의다). 즉 id는 트랜잭션 커밋 시점에 커밋 순서대로 확정 발급되며(미커밋 트랜잭션은 id를 점유하지 않음), 작은 id가 큰 id보다 항상 먼저 커밋된 것이 보장된다. 이 단조성이 watermark 재생 결정성의 기준이다(§5.14.1). 구현은 커밋 시 순번을 발급하는 시퀀스 테이블/단조 카운터로 하며, "auto_increment 발급 순서 ≠ 커밋 순서"가 생기는 방식은 쓰지 않는다 |
| `source_artwork_key` | 대상 작품의 안정 키(= `source + source_artwork_id`, `normalized_artwork_staging.source_artwork_key`). 다른 테이블과 동일한 기준 키를 쓴다. normalized 후보값은 parser/normalizer 재실행으로 row가 갈릴 수 있으므로 행 ID가 아니라 이 안정 키를 기준으로 한다 |
| `field` | 변경된 필드명 |
| `value_type` | 값 타입 enum: `number`/`string`/`date`/`json`/`bool`. `old_value_json`/`new_value_json` 해석과 export 캐스팅 기준 |
| `old_value_json` | 변경 전 값. canonical JSON으로 저장 |
| `new_value_json` | 변경 후 값. canonical JSON으로 저장. `change_type=clear`이면 `NULL`(override 해제 tombstone) |
| `change_type` | 변경 유형 enum: `set`(override 신규 적용)/`update`(override 값 변경)/`clear`(override 해제 = rollback). `set`/`update`는 해당 필드를 활성으로 만들고, `clear`는 비활성으로 만든다(tombstone). 검수 결정 유형(`approve_with_patch` 등)은 `review_decision`에 기록한다 |
| `actor_id` | 처리자 ID |
| `changed_at` | 변경 시각 |
| `review_decision` | 검수 결정 |
| `reason` | 사유 |

운영 원칙:

- 이 테이블은 normalized **작품 필드 변경 전용**이다. artist identity(신규 생성/연결/병합 등) 및 기타 엔티티 결정은 여기 남기지 않고, identity 결정의 SoT는 §5.12.1 `identity_event_log`다. 값 컬럼(`*_value_json`)도 작품 필드 값만 담는다.
- 이벤트는 수정/삭제하지 않고 append만 한다. normalized 후보값은 불변이고, patch는 override 레이어(§5.8.2)로 적용한다.
- 작품의 필드 단위 변경(`approve_with_patch` 등)은 이 테이블에 append한다. 단순 승인/반려 상태는 각 테이블의 상태/승인/반려 컬럼을 그대로 쓴다.
- 어드민 audit의 작품 before/after 조회는 이 테이블을 source로 쓴다(작가 identity 결정은 §5.12.1 `identity_event_log`).
- 역할 분리: 이 테이블은 **감사 로그**이고, "현재 적용 중인 patch 값"은 §5.8.2 `normalized_artwork_override`(현재 적용 상태)가 가진다. append-only 이벤트만으로는 export가 현재 유효한 override 값을 단번에 알 수 없으므로 두 테이블을 분리한다.
- watermark 재생 결정성: 특정 `(source_artwork_key, field)`의 override 활성/비활성은 watermark 이하 `change_event_id`까지 재생해 결정한다. 그 범위에서 **마지막 이벤트가 `set`/`update`면 활성(그 `new_value_json`을 적용), `clear`면 비활성**(override 없음)이다. `clear` tombstone의 `new_value_json`은 NULL이다. `change_event_id`가 커밋 순서의 gap-free 단조 시퀀스이고 watermark가 low-water mark(§5.14.1)이므로, 같은 watermark로 재생하면 항상 같은 활성/비활성 상태가 복원된다.

### 5.8.2 normalized_artwork_override (현재 적용 상태)

`normalized_artwork_change_event`(§5.8.1)는 append-only 감사 로그라 "지금 export에 반영해야 할 patch 값"을 직접 조회하기 어렵다. snapshot export가 현재 적용 중인 override를 한 번에 읽을 수 있도록, 필드별 현재 적용 상태를 보관하는 테이블을 둔다.

| 컬럼 | 설명 |
|---|---|
| `override_id` | PK |
| `source_artwork_key` | 대상 작품 안정 키(= `source + source_artwork_id`). 다른 테이블과 동일 기준 키. `NOT NULL`(generated `active_override_artwork_key`의 활성 분기 base 컬럼) |
| `field` | override 대상 필드명. `NOT NULL`(generated `active_override_field`의 활성 분기 base 컬럼) |
| `value_type` | 값 타입 enum: `number`/`string`/`date`/`json`/`bool`. `override_value_json` 해석과 export 캐스팅 기준 |
| `override_value_json` | 현재 적용 중인 값. canonical JSON으로 저장 |
| `is_active` | 적용 여부(BOOL). rollback/override 해제(clear) 시 `false`. `NOT NULL`(generated `active_override_artwork_key`/`active_override_field`의 활성 분기 base 컬럼) |
| `applied_by` | 적용 처리자 |
| `applied_at` | 적용 시각 |
| `source_change_event_id` | 이 override를 만든 `normalized_artwork_change_event.change_event_id` FK |
| `active_override_artwork_key` | 생성 컬럼. 타입은 베이스 컬럼 `source_artwork_key`와 동일(`<source_artwork_key 타입> GENERATED ALWAYS AS (CASE WHEN is_active THEN source_artwork_key END) STORED`). `active_override_field`와 함께 `(source_artwork_key, field)`당 `is_active` 행 1개를 강제하는 복합 유니크(`uq_active_override`)의 키. `is_active=false` 행은 NULL이라 제약에서 빠진다 |
| `active_override_field` | 생성 컬럼. 타입은 베이스 컬럼 `field`와 동일(`<field 타입> GENERATED ALWAYS AS (CASE WHEN is_active THEN field END) STORED`). `active_override_artwork_key`와 같은 CASE 조건을 쓴다. 두 컬럼을 원본 타입으로 두고 복합 유니크를 걸어, `CONCAT_WS` 단일 키의 길이 비유계(truncation)·구분자 충돌 위험을 없앤다 |

운영 원칙(역할 분리):

- normalized 후보값은 불변이다(파서/normalizer 재실행으로만 재생성). override는 그 후보값 위에 덮는 현재 적용 상태다.
- snapshot export 최종값 = normalized 후보값 위에 `is_active=true` override를 덮어 산출한다. override 값은 `override_value_json`(canonical JSON)으로 저장되고, export는 대상 컬럼 타입에 맞춰 `value_type` 기준으로 캐스팅한다(`number`→숫자, `date`→날짜, `bool`→불리언 등).
- patch = override row upsert(`is_active=true`) + `normalized_artwork_change_event`에 `change_type=set`(신규)/`update`(값 변경) 1건 append를 함께 한다.
- rollback(override 해제) = 해당 override `is_active=false`로 닫고 `normalized_artwork_change_event`에 `change_type=clear`(`new_value_json=NULL`) 1건 append한다(이력 보존·watermark 재생용 tombstone).
- 따라서 `normalized_artwork_change_event`는 감사 로그, `normalized_artwork_override`는 현재 적용 상태로 역할이 분리된다.
- MySQL은 부분 유니크(`... WHERE is_active`)를 지원하지 않으므로, 두 생성 컬럼 `active_override_artwork_key`/`active_override_field`(각각 베이스 `source_artwork_key`/`field`와 동일 타입) + 복합 유니크 `uq_active_override (active_override_artwork_key, active_override_field)`로 `(source_artwork_key, field)`당 활성 override 1개를 강제한다(§5.14.1 `snapshot_request`의 2-컬럼 복합 유니크와 동일 패턴). 단일 `CONCAT_WS('::', ...)` 키를 쓰지 않는 이유는 합성 문자열 길이가 비유계라 `VARCHAR(N)` truncation·구분자 충돌로 서로 다른 `(key, field)`가 같은 유니크 값이 될 수 있어서다. 활성 행의 base 컬럼(`source_artwork_key`/`field`/`is_active`)은 `NOT NULL`이라 활성 분기에서 두 키 컬럼이 NULL이 되어 중복 활성이 새는 NULL-unique 누수는 없다.

### 5.9 normalized_artist_staging

원천별 작가 분해/정리 staging을 입력으로 받아 만든 공통 작가 메타 테이블이다.

| 컬럼 | 설명 |
|---|---|
| `id` | PK |
| `source_artist_raw_id` | source_artist_raw FK |
| `source_artist_interpreted_id` | source_artist_interpreted_staging FK |
| `source` | 원천 |
| `artist_source_id` | 원천 작가 ID/slug |
| `artist_source_url` | 원천 작가 페이지 URL |
| `artist_name_raw` | 원천 작가명 원문 |
| `artist_name_ko_source` | 원천에서 직접 받은 한글명 또는 원천 문자열에서 명확히 분리한 한글명 |
| `artist_name_en_source` | 원천에서 직접 받은 영문명 또는 원천 문자열에서 명확히 분리한 영문명 |
| `artist_name_ko_candidate` | 자동 한글화/표기 변환 후보 |
| `artist_name_en_candidate` | 자동 영문화/로마자 표기 후보 |
| `artist_name_ko_display` | 서비스 표시용 한글 작가명 |
| `artist_name_en_display` | 서비스 표시용 영문 작가명 |
| `artist_name_display_source` | 표시명이 온 경로: `source`, `parsed`, `alias_approved`, `manual`, `auto_transliteration`, `auto_translation` |
| `artist_name_review_status` | 이름 보강 검수 상태 |
| `artist_name_ko_orig` | 보정 전 한글명 원본(검수·복구용 보존) |
| `artist_name_ko_input_type` | 한글화 입력 유형([표준화 흐름](artist_key_standardization_flow_20260624.md) 4.1) 최종값: `source_hangul`/`parsed_mixed`/`hangul_restore`/`foreign_translit`/`pen_name`. `meta_polluted`는 메타 오염 제거 전 임시값으로, 정리 후 위 최종값으로 재분류하며 최종값에는 남지 않는다 |
| `artist_name_ko_reason` | 한글명 reason code([표준화 흐름](artist_key_standardization_flow_20260624.md) 4.4): `source_hangul`/`obvious_bad_romanization`/`metadata_removed_and_romanization_fixed`/`readable_foreign_name_transliteration`/`readable_gallery_name_transliteration`/`readable_studio_name_transliteration`/`pen_name_official` |
| `artist_name_ko_risk_score` | 자동 위험 점수(클수록 우선 검수) |
| `artist_name_ko_risk_reasons` | 위험 패턴 사유 목록(예: `long_hangul_ge_8`, `awkward_운그`, `brand_or_studio_spacing_review`) |
| `artist_name_ko_roundtrip_confidence` | RR 역검증 신뢰도(복원 한글명을 다시 로마자화해 원천 로마자와 비교) |
| `artist_name_ko_override_status` | override 등록 여부: `none`/`registered` |
| `artist_name_normalized` | 매칭용 정규화 이름 |
| `nationality` | 표준 국적 |
| `gender` | 성별 |
| `birth_year` | 숫자 출생연도 |
| `birth_year_source` | 출생연도 출처: `structured_field`, `birth_context_text`, `year_only_text`, `manual` |
| `birth_year_confidence` | 출생연도 신뢰도: `high`/`medium`/`low`. 자동 artist_key 확정에는 `high`만 사용 |
| `death_year` | 사망연도 |
| `location_city` | 활동 도시 |
| `location_country` | 활동 국가 |
| `gallery_name` | 갤러리명 |
| `solo_count` | 개인전 수 |
| `group_count` | 단체전 수 |
| `fair_count` | 아트페어 수 |
| `total_shows` | 전체 전시 수 |
| `followers` | 팔로워 수 |
| `for_sale_works` | 판매중 작품 수 |
| `total_works` | 등록 작품 수 |
| `education_text` | 학력 텍스트 |
| `exhibition_text` | 전시/이력 텍스트 |
| `bio_text` | 작가 소개문 |
| `website_url` | 홈페이지 |
| `instagram_url` | 인스타그램 |
| `artist_identity_status` | staging 매칭 상태: `unmatched`/`candidate`/`auto_approved`/`approved`/`needs_review`/`match_rejected`. 최종 `artist_identity.identity_status`(`active`/`merged`)와 다름 |
| `quality_flags_json` | 작가 메타 품질 플래그 |
| `normalized_at` | 표준화 시각 |

> 컬럼 범위 메모: `solo_count`, `group_count`, `fair_count`, `total_shows`, `followers`, `for_sale_works`, `total_works` 같은 인기도/전시량 지표는 보존은 하되 모델 피처로 바로 쓰지 않는다([원천 사이트별 수집 항목 정리](source_site_collected_fields_20260624.md) 10장). 결측률/입력 가능성 검증 후 승격한다.

### 5.10 artist_name_alias

작가 이름 한글화/영문화 보강과 검수 이력을 관리하는 테이블이다. 서비스 표시와 artist_key 후보 생성을 위해 사용하지만, 자동 변환명만으로 작가 identity를 확정하지 않는다.

테이블 간 흐름과 운영 검수 기준은 [artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md)을 기준으로 한다. 여기서는 MySQL 구현에 필요한 테이블 구조만 정리한다.

| 컬럼 | 설명 |
|---|---|
| `id` | alias ID |
| `artist_key` | 이미 확정된 작가라면 연결되는 최종 작가 키 |
| `normalized_artist_id` | normalized_artist_staging FK |
| `source` | 원천 |
| `artist_source_id` | 원천 작가 ID/slug |
| `alias_name` | 한글명/영문명/원문명/변환 후보 |
| `alias_language` | `ko`, `en`, `other`, `unknown` |
| `alias_type` | `source`, `parsed`, `manual`, `transliteration_candidate`, `translation_candidate` |
| `display_target` | `ko_display`, `en_display`, `matching_only` |
| `is_primary_display` | 서비스 대표 표시명 여부 |
| `confidence` | 자동 분리/변환 신뢰도 |
| `ambiguity_status` | `unique`, `ambiguous`, `needs_review` |
| `conflict_group_id` | 같은 alias가 여러 작가 후보에 걸릴 때의 충돌 그룹 ID |
| `review_status` | `auto_approved`, `approved`, `needs_review`, `match_rejected` |
| `approved_by` | 수동 승인 관리자 ID |
| `approved_at` | 수동 승인 시각 |
| `approval_note` | 승인 메모 |

### 5.11 artist_identity_candidate

같은 alias 또는 승인 alias에 연결된 기존 `artist_key` 후보가 있을 때만 생성하는 검수 후보 테이블이다. 원천 ID나 이름을 바로 운영 artist_key로 쓰지 않고, 근거와 상태를 남긴다. 기존 후보가 없으면 이 테이블을 거치지 않고 신규 작가 후보 큐로 둔다.

신규 작가 후보(기존 후보가 0개)는 `normalized_artist_staging` 기반 검수 큐로 노출한다. `artist_identity`에는 넣지 않는다. 운영자 검수를 거쳐 데이터 관리자가 신규 작가로 승인한 뒤에만 `artist_identity.artist_key`를 생성한다. 다만 같은 `source + artist_source_id`가 이미 active `artist_key`에 연결된 경우는 신규 후보가 아니라 기존 연결이므로 바로 그 키에 연결한다.

| 컬럼 | 설명 |
|---|---|
| `id` | PK |
| `candidate_group_id` | alias 기반 기존 artist_key 후보가 있을 때 생성되는 검수 후보 그룹 ID |
| `normalized_artist_id` | normalized_artist_staging FK |
| `artist_name_normalized` | 매칭용 이름 |
| `source` | 원천 |
| `artist_source_id` | 원천 작가 ID/slug |
| `match_score` | 후보 정렬용 참고 점수. 자동 확정은 점수 합산이 아니라 alias 일치, 고신뢰 생년 일치, 충돌 없음 조건으로 판단 |
| `alias_match_type` | `alias_exact`/`alias_approved`/`alias_fuzzy_only`. 정규화 이름 정확 일치=`alias_exact`, 승인 alias 일치=`alias_approved`, fuzzy 일치만=`alias_fuzzy_only` |
| `match_evidence_json` | 어떤 근거로 묶였는지 |
| `conflict_reasons_json` | 같은 인물로 보기 어려운 충돌 사유 |
| `ambiguity_status` | `unique`, `ambiguous`, `needs_review` |
| `candidate_artist_key_count` | 같은 alias/메타로 연결될 수 있는 후보 artist_key 수 |
| `candidate_artist_keys_json` | 후보 artist_key 목록 |
| `review_status` | `pending`, `auto_approved`, `approved`, `match_rejected`, `needs_review` |
| `proposed_artist_key` | 연결 후보 artist_key. 최종 키가 아니라 검토 대상 |
| `auto_approved_at` | 자동 확정 시각 |
| `auto_approved_rule_version` | 자동 확정에 사용한 규칙 버전 |
| `approved_by` | 수동 승인 관리자 ID |
| `approved_at` | 수동 승인 시각 |
| `approval_note` | 수동 승인 메모 |
| `rejected_by` | 매칭 반려 관리자 ID |
| `rejected_at` | 매칭 반려 시각 |
| `reject_reason` | 매칭 반려 사유 |

### 5.12 artist_identity

운영에서 사용하는 최종 작가 키 테이블이다. 같은 작가로 확정된 여러 원천 작가 row는 하나의 `artist_key`에 연결한다. `identity_status`는 `active`(운영 사용)와 `merged`를 사용한다. 검수 대기 상태는 `artist_identity`가 아니라 `artist_identity_candidate` 또는 신규 작가 후보 큐에서 관리한다. 신규 작가는 운영자 검수를 거쳐 데이터 관리자가 승인한 뒤에만 `artist_identity.artist_key`가 생성된다.

| 컬럼 | 설명 |
|---|---|
| `artist_key` | 서비스 공통 최종 작가 키 |
| `canonical_name` | 대표 표시 작가명 |
| `canonical_name_ko` | 대표 한글명 |
| `canonical_name_en` | 대표 영문명 |
| `birth_year` | 승인된 생년 |
| `nationality` | 승인된 국적 |
| `identity_status` | `active`, `merged` |
| `created_by` | 자동 생성(system) 또는 데이터 관리자 ID |
| `created_at` | 최종 작가 키 생성 시각 |
| `approved_by` | 수동 승인 관리자 ID. 자동 확정 건은 비워두거나 system으로 기록 |
| `approved_at` | 수동 승인 시각 |
| `merge_evidence_json` | 최종 병합 근거 |
| `notes` | 운영자 메모 |

부여 기준:

자동 확정, 수동 승인, 반려, 보류 판단 기준은 [artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md)을 따른다. 이 테이블에서는 최종 `artist_key`와 승인/병합 근거만 보존한다.

### 5.12.1 identity_event_log (append-only)

비가역 작가 identity 결정(신규 `artist_key` 생성, 기존 키 연결 확정/반려, 병합, 병합 취소)과 개인정보 요청에 따른 서비스 노출 억제/해제는 현재 상태 컬럼만으로는 사후 추적이 약하므로 append-only 이벤트 로그로 남긴다. 작품/가격 등 전체 필드의 변경 audit은 여전히 고도화 항목이지만, 되돌리기 어려운 identity 결정은 1차 적용에 포함한다.

| 컬럼 | 설명 |
|---|---|
| `id` | PK |
| `event_type` | `create`, `link`, `reject`, `merge`, `unmerge`, `reactivate`, `suppress`, `unsuppress` |
| `artist_key` | 대상 최종 작가 키 |
| `related_artist_key` | 병합/un-merge 상대 키(있을 때) |
| `normalized_artist_id` | 관련 staging row |
| `before_status` | 직전 `identity_status`/연결/서비스 노출 상태 |
| `after_status` | 변경 후 `identity_status`/연결/서비스 노출 상태 |
| `actor_id` | 처리자 ID |
| `actor_role` | `data_admin`, `superuser`, `system`(자동 확정) |
| `reason` | 사유 |
| `evidence_json` | 결정 근거 |
| `created_at` | 발생 시각 |

운영 원칙:

- 이벤트는 수정/삭제하지 않고 append만 한다.
- 자동 확정(`auto_approved`)도 `actor_role=system`으로 1건 남긴다.
- 운영 초기 슈퍼유저가 신규 `artist_key` 생성, 기존 키 연결 확정, 병합 등 데이터 관리자 권한 작업을 수행한 경우 `actor_role=superuser`로 남긴다. 이력에는 실제 처리자의 `actor_id`와 `reason`을 반드시 기록한다.
- 개인정보/삭제 요청으로 작가의 서비스 노출을 억제/해제하면 `event_type=suppress`/`unsuppress`로 남긴다(raw 물리 삭제 정책은 정식 정책에서 확정).
- API `GET /api/v1/admin/audit-logs`의 `entity_type=artist_identity` 조회는 이 테이블을 source로 쓴다. 다른 엔티티의 변경 이력은 각 테이블의 승인/반려 필드를 그대로 사용한다(단, 작품 필드 단위 변경은 §5.8.1 참조).

### 5.12.2 artist_identity_version / artist_key_membership_history

`artist_key`의 멤버십(어떤 원천 작가 row가 어떤 `artist_key`에 묶여 있는지)은 merge/un-merge로 시간에 따라 바뀐다. snapshot이 한 시점의 `artist_key` 의미로 고정되려면, "특정 시점의 멤버십"을 as-of로 재현할 수 있어야 한다. 이를 위해 단조 증가 identity 버전과 멤버십 이력 테이블을 둔다.

`artist_identity_version`(버전 발급 이력):

| 컬럼 | 설명 |
|---|---|
| `artist_identity_version` | PK. 단조 증가 int |
| `created_at` | 버전 생성 시각 |
| `created_by` | 데이터 관리자 ID 또는 `system` |
| `trigger_event` | 멤버십을 바꾸는 모든 identity 결정을 포함: `initial`(첫 버전), `new_artist`(신규 작가 생성), `merge`, `un_merge`, `link_confirm`(기존 키 연결/확정). 본문의 "모든 멤버십 변경이 버전 발급" 서술과 일치한다 |
| `source_event_id` | 이 버전을 유발한 `identity_event_log.id` FK(있을 때) |
| `note` | 메모 |

버전 생성 주체/시점(이벤트 기반 단일화): artist_key 멤버십을 바꾸는 승인된 identity 결정(신규 작가 생성, 기존 키 연결/확정, merge, un-merge)이 멤버십을 바꾸는 순간, 그 이벤트가 새 `artist_identity_version`을 발급한다. snapshot export는 새 버전을 만들지 않고 그 시점의 최신 `artist_identity_version`을 `artwork_snapshot.artist_identity_version`에 기록만 한다(§5.13). 첫 버전은 `trigger_event=initial`이다.

재현 결정성: 버전 id는 멤버십 변경 이벤트 **커밋 시 확정**된다(미커밋 버전은 존재하지 않음). `snapshot_request.artist_identity_version`이 "요청 생성 시점에 커밋 완료된 최신 버전"을 동결하므로(§5.14.1), 같은 요청은 항상 같은 identity 버전으로 멤버십을 고정한다.

`artist_key_membership_history`(as-of 멤버십 이력):

| 컬럼 | 설명 |
|---|---|
| `membership_id` | PK. `BIGINT` |
| `artist_key` | 멤버가 묶인 최종 작가 키. `artist_identity(artist_key)` FK |
| `member_type` | 멤버 식별자 종류. enum: `artwork_key`(= `source_artwork_key`) / `artist_source_id`(= `source + artist_source_id`) |
| `member_id` | `member_type`에 해당하는 키 값. `member_type=artwork_key`면 `source_artwork_key`, `member_type=artist_source_id`면 `source + artist_source_id` 합성값 |
| `valid_from_version` | 이 멤버십이 유효해진 `artist_identity_version`. `artist_identity_version(artist_identity_version)` FK |
| `valid_to_version` | 이 멤버십이 끝난 버전. NULL이면 현재 유효. `artist_identity_version(artist_identity_version)` FK(nullable) |

운영 원칙:

- 멤버 식별자는 다형 문자열 `member_ref`를 쓰지 않고 `member_type` + `member_id` 두 컬럼으로 분리한다(키 종류와 키 값을 명시).
- no-overlap 불변식: "임의 버전 시점에 한 member는 정확히 하나의 `artist_key`에만 속한다." 유니크 `(member_type, member_id, valid_from_version)`는 같은 시작 버전에서의 중복 소속만 막으므로, 서로 다른 `valid_from`/`valid_to` 구간이 겹치지 않는 것(구간 중첩 금지)은 app/trigger 레벨에서 강제한다(멤버십을 옮길 때 기존 행의 `valid_to_version`을 먼저 닫고 새 행을 연다). 이로써 as-of 조회가 항상 단일 `artist_key`를 반환함을 보장한다.
- "특정 `artist_identity_version` 시점의 `artist_key` 멤버십"은 `valid_from_version <= V AND (valid_to_version IS NULL OR valid_to_version > V)` as-of 조회로 재현하며, 위 불변식에 따라 멤버당 정확히 한 행이 매칭된다.
- snapshot은 `artwork_snapshot.artist_identity_version`을 기록하고(§5.13), 서빙 Warm 이력 조회는 그 버전 기준으로 멤버십을 고정한다.
- 구간 정합성은 `CHECK (valid_to_version IS NULL OR valid_to_version > valid_from_version)`(MySQL 8.0 CHECK)로 강제한다. 닫힌 구간이 시작 버전보다 같거나 작아지는 행을 차단한다. 구간 중첩 금지(no-overlap)는 위 불변식대로 app/trigger 레벨에서 유지한다.
- `artist_key`는 `artist_identity(artist_key)`에 FK를 둬 존재하지 않는 작가 키로 멤버십이 생기지 않게 한다.
- 멤버십 행은 삭제하지 않고 `valid_to_version`을 채워 닫는다. [artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md) 문서가 이 테이블을 참조한다.

### 5.13 artwork_snapshot

학습/운영 기준 snapshot을 고정한다.

| 컬럼 | 설명 |
|---|---|
| `snapshot_id` | snapshot PK |
| `snapshot_name` | 예: `train_candidate_2026_06_23`. 영속 출처는 `snapshot_request.snapshot_name`이다. 승인 시 요청 row의 이름을 그대로 복사하므로, 승인 endpoint가 `snapshot_request_id`만 넘겨도 이름을 재현한다(§5.14.1) |
| `source_cutoff_at` | 이 시각 이전 수집분만 포함. 요청의 `snapshot_request.source_cutoff_at`과 동일 값 |
| `created_at` | 생성 시각 |
| `status` | snapshot 라이프사이클 상태. enum: `building`(생성 중) → `generated`(빌드 완료/고정, **비서빙**: 내부 검증용이며 서빙·freshness 대상이 아님) → `approved`(운영 승인, 서빙 가능), 그리고 실패/폐기 terminal `failed`/`discarded`. 서빙/freshness 기준 정상 snapshot은 `approved`만이다(SoT 확정). `generated`는 빌드만 끝난 비서빙 상태다. 전이: `building`→`generated`→`approved`(정상), `building`→`failed`(빌드 실패), `generated`/`approved`→`discarded`(폐기) |
| `rules_version` | 필터/정규화 규칙 버전 |
| `artist_identity_version` | 이 snapshot이 고정한 작가 identity 버전(`artist_identity_version.artist_identity_version` 참조, §5.12.2). 영속 출처는 `snapshot_request.artist_identity_version`(요청 생성 시점에 **커밋 완료된** 최신 버전을 동결)이며 생성 시 그 값을 복사한다. 요청~승인~생성 사이 identity 변경이 같은 요청 산출을 바꾸지 못한다. 이는 identity watermark이며 엄밀한 cutoff point-in-time이 아니다(§5.14.1, 의도된 설계). 서빙 Warm 이력 조회는 이 버전 기준으로 멤버십을 고정한다([artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md)) |
| `approved_by` | 서빙 승인(`generated`→`approved`)한 데이터 관리자 ID. 미승인(`building`/`generated`)이면 NULL. API §9.3.3(`POST /api/v1/admin/snapshots/{snapshot_id}/approve`)이 이 컬럼을 채운다 |
| `approved_at` | 서빙 승인 시각. 미승인이면 NULL. API §9.3.3이 채운다 |
| `approval_note` | 서빙 승인 사유/메모(선택). API §9.3.3이 채운다 |
| `serving_approval_idempotency_key` | 서빙 승인(`generated`→`approved`) 전용 멱등 키. **전역 UNIQUE**(§5.16). API §9.3.3 서빙 승인의 멱등 키가 여기 저장·replay되어 같은 서빙 승인이 중복 전이를 일으키지 않게 한다. 같은 키 + 다른 payload(다른 `snapshot_id`/승인 대상) 호출은 충돌로 거부한다. 미승인이면 NULL. 이는 생성승인 멱등 키(`snapshot_request.approval_idempotency_key`)와 별개 저장소다(생성승인 vs 서빙승인 구분, §5.14.1) |
| `summary_json` | 구성 요약 |

서빙 승인 이력의 SoT 고정: `generated`→`approved` 전이의 영속 이력은 운영 로그가 아니라 위 `approved_by`/`approved_at`/`approval_note` 컬럼이다(구현자 선택 여지 없음). status 전이는 `approved_by`/`approved_at`을 채우며 일어나고, 누가·언제·왜 서빙 승인했는지는 이 컬럼으로만 재현한다. API §9.3.3(`POST /api/v1/admin/snapshots/{snapshot_id}/approve`)이 status를 `approved`로 올리며 동시에 이 컬럼을 채운다.

두 멱등 키의 역할 구분(생성승인 vs 서빙승인): 생성승인(`snapshot_request.status`를 `approved`로 올려 snapshot 생성에 진입시키는 승인) 멱등은 `snapshot_request.approval_idempotency_key`가, 서빙승인(`artwork_snapshot.status`를 `generated`→`approved`로 올리는 승인) 멱등은 여기 `artwork_snapshot.serving_approval_idempotency_key`가 담당한다. 두 승인은 서로 다른 레이어(요청 워크플로우 vs snapshot 산출물)의 멱등이므로 별개 컬럼·별개 전역 UNIQUE 저장소로 둔다(한 컬럼이 두 키를 겸하지 않는다).

모델 아티팩트의 `training_snapshot_id`/`snapshot_export_id`는 이 `artwork_snapshot.snapshot_id`를 가리킨다. `snapshot_export_id`는 같은 `snapshot_id`에서 만든 export 산출물(parquet/manifest)의 ID이며, 단일 export면 `snapshot_id`와 동일하게 둔다.

snapshot row는 `snapshot_request` 승인 후 생성에 진입할 때 `status=building`으로 만들어지며, 이 `snapshot_id`가 그 요청의 `snapshot_request.resulting_snapshot_id`에 채워진다(§5.14.1). 생성이 끝나면 `artwork_snapshot.status`를 `generated`(비서빙)로 둔다. 데이터 관리자가 검증 후 운영 사용을 승인하는 시점에만 `approved`로 전이하며, 이때부터 서빙·freshness 대상이 된다.

`snapshot_request.status`(`requested`/`approved`/`generating`/`generated`/`rejected`/`failed`/`cancelled`)와 `artwork_snapshot.status`(`building`/`generated`/`approved`/`failed`/`discarded`)는 서로 다른 레이어다. 전자는 생성 요청·승인 워크플로우의 상태이고, 후자는 생성된 snapshot 산출물의 서빙 가능 여부 상태다(요청의 `generated`=생성 완료, snapshot의 `approved`=서빙 가능).

### 5.14 artwork_snapshot_item

snapshot에 포함된 작품 row 목록이다.

| 컬럼 | 설명 |
|---|---|
| `snapshot_id` | snapshot FK |
| `normalized_artwork_id` | normalized_artwork_staging FK |
| `price_krw_normalized` | KRW로 통일한 최종 학습용 가격(이 snapshot 기준). `normalized_artwork_staging`의 값을 snapshot 시점에 그대로 복사 저장한다(재현·감사) |
| `price_krw_is_converted` | 환산값이면 `true`, 원천 KRW면 `false` |
| `price_fx_rate` | 환산에 사용한 실제 환율값. `normalized_artwork_staging`의 값을 복사 저장한다. 이후 환율 정책/환율표가 바뀌어도 이 snapshot row가 쓴 환율을 그대로 재현·감사할 수 있다 |
| `price_fx_date` | 환산에 사용한 환율 기준일(= row `collected_at` 시점, 결측 시 직전 가용 환율일). §5.15와 동일 컬럼명 |
| `price_fx_source` | 환산에 사용한 환율 출처 |
| `include_status` | `included`, `excluded` |
| `exclude_reason` | 제외 사유 |

`artwork_snapshot_item`은 고정된 학습 row의 감사 출처다. 따라서 환율 기준일/출처(`price_fx_date`/`price_fx_source`)뿐 아니라 실제 적용 환율(`price_fx_rate`)과 환산 결과(`price_krw_normalized`)값도 snapshot 시점 값으로 복사 저장한다. `normalized_artwork_staging`의 환산 컬럼이 이후 갱신되어도 이 snapshot row로 당시 가격·환율을 재현·감사할 수 있다.

### 5.14.1 snapshot_request

snapshot 생성은 운영자 확정요청과 데이터 관리자 생성승인의 2단계로 나눈다. 운영자가 바로 snapshot을 생성하지 못하게 하고, 동시 생성을 잠그기 위한 요청 테이블이다. 실제 snapshot row(`artwork_snapshot`)는 승인 후에만 만들어진다.

| 컬럼 | 설명 |
|---|---|
| `snapshot_request_id` | PK |
| `idempotency_key` | 요청(확정요청) 멱등 키. 전역 UNIQUE. 같은 확정요청 제출의 중복 생성을 막는다. 승인 멱등 키(`approval_idempotency_key`)와 구분한다 |
| `snapshot_name` | 요청 시 입력한 snapshot 이름. 승인 후 생성되는 `artwork_snapshot.snapshot_name`의 영속 출처다. 승인 endpoint가 `snapshot_request_id`만 넘겨도 이 값으로 snapshot 이름을 재현한다 |
| `requested_by` | 확정요청한 운영자 ID |
| `requested_at` | 확정요청 시각 |
| `status` | `requested`, `approved`, `generating`, `generated`, `rejected`, `failed`, `cancelled`. `requested`/`approved`/`generating`은 진행 중(non-terminal), `generated`/`rejected`/`failed`/`cancelled`는 종료(terminal). `NOT NULL`(generated `active_cutoff_at`/`active_rules_version`의 활성 분기 base 컬럼). `generated`는 요청(request) 레이어의 terminal(생성 완료)일 뿐이며, 그 요청이 산출한 `artwork_snapshot`은 별도로 서빙 승인(`generated`→`approved`) 대기 상태다(요청 status와 snapshot status는 다른 레이어, §5.13) |
| `heartbeat_at` | `approved`/`generating` 진행 중 요청을 처리하는 job이 주기적으로 갱신하는 lease 시각. watchdog가 lock wedge(좀비 요청)를 회수하는 데 사용(§5.2.2 collector_run watchdog와 동일 패턴) |
| `artist_identity_version` | 요청 생성 시점에 **커밋 완료된** 최신 `artist_identity_version`을 동결(`artist_identity_version.artist_identity_version` FK). 버전 id는 멤버십 변경 이벤트 커밋 시 확정되므로, 미커밋 버전은 동결 대상이 아니다. snapshot export는 이 버전 기준으로 identity를 고정하므로, 요청~승인~생성 사이 identity 변경이 같은 요청의 산출을 바꾸지 못한다. 이는 identity watermark이며 엄밀한 `source_cutoff_at` point-in-time이 아님(의도된 설계: cutoff 시점이 아니라 요청 생성 시점의 커밋된 최신 멤버십을 동결). 생성된 snapshot의 `artwork_snapshot.artist_identity_version`이 된다 |
| `override_watermark_event_id` | cutoff 시점의 override low-water mark(BIGINT) = `id ≤ N`이 모두 커밋 완료(가시)된 최대 N. `change_event_id`는 커밋 순서 gap-free 단조라(§5.8.1) 정상 상태에서는 watermark 산정이 단순 MAX와 같지만, 산정 순간에 진행 중(미커밋) 트랜잭션이 있으면 잠깐 gap이 보일 수 있으므로 "그 시점에 빈틈없이 가시인 최대 N"을 low-water mark로 잡는다. 이렇게 해야 산정 직후 커밋되는 더 큰 id가 같은 watermark 재생에 끼지 않아 결정성이 보장된다. export는 이 watermark까지 change_event(§5.8.1)를 재생해 그 시점에 유효했던 override를 재구성한다(현재상태 `normalized_artwork_override`는 라이브 머티리얼라이즈라 시점 재현이 안 됨). 이 방어 덕분에 같은 snapshot 재export가 동일 override 산출을 낸다 |
| `approved_by` | 생성승인한 데이터 관리자 ID |
| `approved_at` | 승인 시각 |
| `approval_idempotency_key` | 생성승인 전용 멱등 키(요청 `idempotency_key`와 구분). **전역 UNIQUE**(요청 `idempotency_key`와 동일 정책, §5.16). API 생성승인(`status`→`approved`, snapshot 생성 진입)의 멱등 키가 여기 저장·replay되어 같은 승인이 중복 생성을 일으키지 않게 한다. 같은 키 + 다른 payload 호출은 충돌로 거부한다. 서빙승인(`generated`→`approved`) 멱등은 이 컬럼이 아니라 `artwork_snapshot.serving_approval_idempotency_key`가 담당한다(별개 키·별개 저장소, §5.13) |
| `source_cutoff_at` | 이 요청이 고정한 cutoff 시점(= 생성될 snapshot의 `artwork_snapshot.source_cutoff_at`). 컬럼명은 API/snapshot과 통일한다. `NOT NULL`(generated `active_cutoff_at`의 활성 분기 base 컬럼) |
| `rules_version` | 이 요청이 고정한 필터/정규화 규칙 버전(= 생성될 snapshot의 `artwork_snapshot.rules_version`). 물리 타입 `VARCHAR(64) NOT NULL`. `NOT NULL`인 이유는 generated `active_rules_version`의 활성 분기 base 컬럼이기 때문이다 |
| `active_cutoff_at` | 생성 컬럼. `TIMESTAMP GENERATED ALWAYS AS (CASE WHEN status IN ('requested','approved','generating') THEN source_cutoff_at END) STORED`. 타입은 베이스 `source_cutoff_at`와 동일한 `TIMESTAMP`. `active_rules_version`과 함께 동시 생성 가드 유니크(`uq_active_snapshot_request`)를 구성한다. terminal(`generated`/`rejected`/`failed`/`cancelled`) 행은 NULL이라 제약에서 빠진다(§5.16) |
| `active_rules_version` | 생성 컬럼. `VARCHAR(64) GENERATED ALWAYS AS (CASE WHEN status IN ('requested','approved','generating') THEN rules_version END) STORED`. 타입은 베이스 컬럼 `rules_version`(`VARCHAR(64)`)과 동일하다. `active_cutoff_at`와 같은 CASE 조건을 쓴다 |
| `resulting_snapshot_id` | 생성된 snapshot의 `artwork_snapshot.snapshot_id` FK. 생성 후 채운다 |
| `request_note` | 요청/승인/반려 메모 |

2단계 운영:

- 운영자가 확정요청하면 `status=requested` row를 만든다(`snapshot_name`/`source_cutoff_at`/`rules_version` 고정).
- 데이터 관리자가 생성을 승인하면 `status=approved`로 전이한 뒤 `status=generating`으로 생성에 진입하고, 생성 완료 시 `status=generated` + `resulting_snapshot_id`를 채운다. 승인 endpoint는 `snapshot_request_id`만 받아도 요청 row의 `snapshot_name`/`source_cutoff_at`/`rules_version`/`artist_identity_version`/`override_watermark_event_id`로 snapshot을 재현한다. 승인 자체는 `approval_idempotency_key`로 멱등 처리해 같은 승인이 중복 생성을 일으키지 않는다.
- `generating` 중 생성이 실패하면 `status=failed`로 전이한다. 이때 두 생성 컬럼(`active_cutoff_at`/`active_rules_version`)이 NULL이 되어 활성 lock(`uq_active_snapshot_request`)이 풀리므로, 같은 `(source_cutoff_at, rules_version)`로 재시도(새 요청)가 가능하다.
- lock wedge 방지(watchdog): `approved`/`generating`에서 처리 job이 죽으면 진행 중 행이 남아 같은 `(source_cutoff_at, rules_version)`의 재시도가 영구 차단된다. 이를 막기 위해 처리 job은 `heartbeat_at`을 주기적으로 갱신하고, watchdog가 `heartbeat_at`이 임계(확정 필요)를 초과한 `approved`/`generating` 행을 `status=failed`로 전이한다. 그러면 두 생성 컬럼이 NULL이 되어 `uq_active_snapshot_request`가 풀려 같은 cutoff/rules로 재시도가 가능해진다. watchdog는 §5.2.2 `collector_run` 회수와 동일 패턴이며, 처리 호스트와 분리된 외부 스케줄러/모니터에서 실행한다(처리 호스트가 멈춰도 회수가 동작해야 함).
- 반려하면 `status=rejected`로 두고 snapshot은 만들지 않는다.
- 동시 생성 가드는 두 겹이다. (1) `idempotency_key` UNIQUE로 같은 확정요청의 중복 제출/중복 승인을 막고, (2) 생성 컬럼 `(active_cutoff_at, active_rules_version)` + `UNIQUE KEY uq_active_snapshot_request`로 같은 `(source_cutoff_at, rules_version)`에 대해 진행 중 요청이 1개만 존재하도록 강제한다. 이로써 `idempotency_key`가 서로 다른 두 요청이 같은 cutoff/rules로 둘 다 snapshot을 생성하는 경합을 차단한다. 진행 중 행의 base 컬럼(`status`/`source_cutoff_at`/`rules_version`)은 `NOT NULL`이라 활성 분기에서 생성 컬럼이 NULL이 되어 중복 활성이 새는 NULL-unique 누수는 없다. 단일 `CONCAT` lock을 쓰지 않는 이유는 TIMESTAMP를 문자열로 합치면 타임존/SQL모드에 따라 표현이 흔들려 유니크 판정이 깨질 수 있어서다. 두 컬럼을 각자의 원본 타입으로 두고 복합 유니크를 건다.
- 승인 잠금 절차: 상태 전이는 expected status 조건부 UPDATE(낙관적 잠금)로 한다. 예) `UPDATE snapshot_request SET status='approved', approved_by=?, approved_at=NOW() WHERE snapshot_request_id=? AND status='requested'` — `affected_rows=0`이면 이미 다른 트랜잭션이 전이한 것이므로 실패 처리한다. 같은 cutoff/rules로 동시에 진입하려는 별개 요청은 `uq_active_snapshot_request` 복합 유니크가 거부한다. 같은 요청을 두 관리자가 동시에 승인해도 조건부 UPDATE에서 한쪽만 성공한다.
- 재생성 정책(의도된 재생성 허용): 활성 lock(`uq_active_snapshot_request`)은 생성 컬럼이 `generated`/terminal에서 NULL로 풀리므로 영속 유니크가 아니다. 따라서 같은 `(source_cutoff_at, rules_version)`로 다시 확정요청·승인하면 새 `snapshot_request`와 새 `artwork_snapshot.snapshot_id`(새 버전 snapshot)가 만들어진다. 이는 금지 사항이 아니라 **의도된 재생성 허용**이다(영속 유니크로 중복 snapshot 생성을 막지 않는다). 같은 cutoff/rules의 재생성은 기존 snapshot을 덮어쓰지 않고 별도 snapshot_id를 누적하며, 서빙은 항상 최신 `approved` snapshot을 본다(§5.13, 서빙·freshness 기준). 활성 lock은 "같은 cutoff/rules의 **동시** 진행 1개"만 강제하고, 시점이 다른 재생성은 허용한다.
- 승인 멱등 키 유니크: `approval_idempotency_key`는 요청 `idempotency_key`와 동일하게 **전역 UNIQUE**다(§5.16). 같은 키 + 다른 payload(다른 `snapshot_request_id`/승인 대상) 호출은 충돌로 거부한다. "`snapshot_request_id` 범위 내 유니크" 대안은 두지 않는다(스코프 단일화).

### 5.15 fx_rate_daily

학습 snapshot에서 가격 통화를 KRW로 통일할 때 사용하는 기준일 환율 테이블이다. raw/interpreted 단계에서는 원천 통화를 그대로 보존하고, 환산은 `price_conversion` 단계에서만 수행한다. 이 단계는 snapshot export 준비 과정의 일부로 실행되며, 환산 결과(`price_type`/`price_tax_basis`/`price_krw_normalized`/`price_fx_rate`/`price_fx_date`/`price_fx_source`)는 `normalized_artwork_staging`에 1회 저장된다(§5.8, 단일 물리 기록점). export 산출물에는 이 저장값이 그대로 반영되고 별도 재계산/이중 기록은 하지 않는다. 이렇게 해야 환율 정책이 바뀌어도 원천 가격을 다시 환산해 재현할 수 있다.

환율 적용 규칙(point-in-time 단일화): 각 row는 그 row의 `collected_at` 날짜 환율로 환산한다. snapshot 기준일 환율 fallback은 쓰지 않는다(snapshot 날짜가 아니라 row 수집 시점 기준). 해당 날짜의 환율이 결측이면 직전 가용 환율일을 사용하고, `price_fx_date`에는 snapshot 날짜가 아니라 **실제 사용한 환율일**을 기록한다.

| 컬럼 | 설명 |
|---|---|
| `rate_date` | 환율 기준일 |
| `base_currency` | 환산 대상 통화. 예: `USD`, `EUR` |
| `quote_currency` | 기준 통화. 운영에서는 `KRW` 고정 |
| `rate` | `base_currency` 1단위당 `quote_currency` 금액 |
| `rate_source` | 환율 출처. 예: 한국은행, ECB, 수동 입력 |
| `created_at` | 적재 시각 |

`price_conversion` 단계 출력 컬럼(`normalized_artwork_staging`에 1회 저장되어 학습 snapshot export에 그대로 포함):

| 컬럼 | 설명 |
|---|---|
| `price_krw_normalized` | KRW로 통일한 최종 학습용 가격 |
| `price_krw_is_converted` | 환산값이면 `true`, 원천 KRW(price_krw_source)를 그대로 쓰면 `false` |
| `price_fx_rate` | 환산에 사용한 환율값(point-in-time 재현용) |
| `price_fx_date` | 환산에 사용한 환율 기준일(= 각 row `collected_at` 시점. 해당일 결측 시 직전 가용 환율일). snapshot 날짜가 아니다 |
| `price_fx_source` | 환산에 사용한 환율 출처 |

컬럼명은 `price_fx_date`/`price_fx_rate`/`price_fx_source`로 통일한다(이전 `fx_rate_date`/`fx_rate_source` 혼용 표기를 폐기). §5.8 `normalized_artwork_staging` 정의와 동일하다.

환산 우선순위: `price_krw_source`(원천이 직접 제공한 KRW)가 있으면 그대로 사용하고, 없으면 `price_currency`+`price_amount`를 각 row `collected_at` 날짜 환율로 환산한다(point-in-time). 해당 날짜 환율이 결측이면 직전 가용 환율일을 사용하고 `price_fx_date`에 그 날짜를 기록한다. 직전 가용 환율도 없는 통화/기준일은 환산하지 않고 `quality_flags_json`에 사유를 남긴 뒤 해당 row를 학습 snapshot 대상에서 보류한다.

이 출력 컬럼은 `normalized_artwork_staging`에 저장된 값이 학습 snapshot export(parquet)에 그대로 포함되는 것이다(export 시 재계산하지 않음). 재현/감사를 위해 환산에 사용한 `price_fx_date`/`price_fx_source`와 환율 정책 버전을 `artwork_snapshot.summary_json`(또는 export manifest)에 함께 기록한다.

### 5.16 주요 키/제약/인덱스

재현성과 재실행 안전성을 위해 최소 아래 제약을 둔다. 상세 컬럼은 위 각 테이블 정의를 따른다.

| 대상 | 제약 |
|---|---|
| `source_registry` | PK `source` |
| `collector_run` | PK `id`. `(source, snapshot_date, collector_version)` 조회 인덱스. `source`는 `source_registry.source` 참조. single-flight DB 백스톱: 생성 컬럼 `active_source_lock VARCHAR(64) GENERATED ALWAYS AS (CASE WHEN status='running' THEN source END) STORED`(타입은 베이스 컬럼 `source`와 동일) + `UNIQUE KEY uq_running_source (active_source_lock)`로 source별 `running` 1개만 강제(§5.2.2). 활성 분기 base 컬럼 `source`/`status`는 `NOT NULL`이라 NULL-unique 누수 없음. MySQL은 NULL 다중 허용이라 `running`이 아닌 행은 제약에서 빠진다. flock이 1차 single-flight, 이 유니크는 DB 백스톱 |
| `manual_import_file` | PK `id`. `(source, uploaded_at)` 조회 인덱스. `linked_run_id`는 캐시값이며 FK 필수 아님 |
| `price_model_registry` | PK `model_version`. `(route, model_status)` 조회 인덱스 |
| `price_model_deployment` | PK `deployment_id`. route별 active deployment는 1개만 허용. 생성 컬럼 `active_route_lock VARCHAR(32) GENERATED ALWAYS AS (CASE WHEN deployment_status='active' THEN route END) STORED`(타입은 베이스 컬럼 `route`와 동일) + `UNIQUE KEY uq_active_route (active_route_lock)`로 강제. 활성 분기 base 컬럼 `route`/`deployment_status`는 `NOT NULL`이라 NULL-unique 누수 없음. MySQL은 NULL 다중 허용이라 `active`가 아닌 행은 제약에서 빠진다. 활성화 트랜잭션에서 기존 active를 `inactive` 전환 후 신규 active 생성 |
| `price_prediction_log` | PK `prediction_id`. `(model_version, deployment_id, predicted_at)` 조회 인덱스 |
| `raw_fetch` | `(run_id, url_hash, payload_hash)` 유니크로 같은 응답 중복 적재 방지. `url_hash`=`SHA256(request_fingerprint)`(정규화 규칙은 §5.3). 긴 URL을 직접 인덱싱하지 않고 고정 길이 hash를 쓴다. 원문 `url`은 저장하지 않는다 |
| `source_artwork_raw` | `(run_id, source, source_artwork_id)` 유니크. 재실행 시 중복 insert 금지 |
| `source_artist_raw` | `(run_id, source, artist_source_id)` 유니크 |
| `normalized_artwork_staging` | `source_artwork_key`(= `source + source_artwork_id`) 인덱스, 최신 row 조회용 인덱스 |
| `artist_name_alias` | `(normalized_artist_id, alias_name, alias_language)` 유니크 |
| `artist_identity` | `artist_key` PK |
| `identity_event_log` | PK `id`. `(artist_key, created_at)` 조회 인덱스. append-only(수정/삭제 금지) |
| `artist_identity_version` | PK `artist_identity_version`(단조 증가 int). `source_event_id`는 `identity_event_log.id` 참조 |
| `artist_key_membership_history` | PK `membership_id`(`BIGINT`). `(member_type, member_id, valid_from_version)` 유니크. 한 멤버가 한 버전 구간(`valid_from_version`)에 복수 `artist_key`에 동시에 속하는 행을 차단한다(`artist_key`를 유니크에 포함하지 않는 이유). as-of 조회용 `(member_type, member_id, valid_from_version)`/`(artist_key, valid_from_version)` 인덱스. `artist_key`는 `artist_identity(artist_key)` FK. `valid_from_version`/`valid_to_version`은 `artist_identity_version.artist_identity_version` 참조(`valid_to_version`은 nullable). `CHECK (valid_to_version IS NULL OR valid_to_version > valid_from_version)`(MySQL 8.0 CHECK). 구간 중첩 금지(no-overlap)는 app/trigger 유지 |
| `normalized_artwork_change_event` | PK `change_event_id`(커밋 순서 gap-free 단조 시퀀스/시퀀스 테이블 발급, watermark 재생 결정성 기준). `(source_artwork_key, changed_at)` 조회 인덱스. 대상 작품은 안정 키 `source_artwork_key`(= `source + source_artwork_id`)로 식별(행 ID가 아닌 안정 키 기준, 다른 테이블과 일치). `change_type` enum `set`/`update`/`clear`(clear는 tombstone, `new_value_json=NULL`). append-only(수정/삭제 금지) |
| `normalized_artwork_override` | PK `override_id`. `(source_artwork_key, field)` 조회 인덱스. 활성 override 1개 강제: 두 생성 컬럼 `active_override_artwork_key`(베이스 `source_artwork_key`와 동일 타입) `GENERATED ALWAYS AS (CASE WHEN is_active THEN source_artwork_key END) STORED` + `active_override_field`(베이스 `field`와 동일 타입) `GENERATED ALWAYS AS (CASE WHEN is_active THEN field END) STORED` + `UNIQUE KEY uq_active_override (active_override_artwork_key, active_override_field)`. 두 컬럼을 원본 타입으로 둔 복합 유니크라 `CONCAT_WS` 단일 키의 길이 비유계(truncation)·구분자 충돌 위험이 없다. 활성 분기 base 컬럼 `source_artwork_key`/`field`/`is_active`는 `NOT NULL`이라 NULL-unique 누수 없음. `is_active=false` 행은 NULL이라 제약에서 빠진다(§5.8.2). `source_change_event_id`는 `normalized_artwork_change_event.change_event_id` 참조 |
| `snapshot_request` | PK `snapshot_request_id`. `idempotency_key`(요청 멱등) 전역 UNIQUE. `approval_idempotency_key`(승인 멱등)도 **전역 UNIQUE**(요청 `idempotency_key`와 동일 정책으로 스코프 단일화; `snapshot_request_id` 범위 내 유니크 대안은 두지 않는다). 같은 `approval_idempotency_key` + 다른 payload(다른 `snapshot_request_id`/승인 대상) 호출은 충돌로 거부한다. 요청 멱등 키와 승인 멱등 키는 별개 키다. 동시 생성 가드: 생성 컬럼 `active_cutoff_at TIMESTAMP GENERATED ALWAYS AS (CASE WHEN status IN ('requested','approved','generating') THEN source_cutoff_at END) STORED`(타입은 베이스 `source_cutoff_at`와 동일 `TIMESTAMP`) + `active_rules_version VARCHAR(64) GENERATED ALWAYS AS (CASE WHEN status IN ('requested','approved','generating') THEN rules_version END) STORED`(타입은 베이스 `rules_version VARCHAR(64) NOT NULL`과 동일) + `UNIQUE KEY uq_active_snapshot_request (active_cutoff_at, active_rules_version)`로 같은 `(source_cutoff_at, rules_version)`에 진행 중 요청 1개만 강제(§5.14.1). terminal(`generated`/`rejected`/`failed`/`cancelled`) 행은 두 생성 컬럼이 NULL이라 제약에서 빠진다. 활성 분기 base 컬럼 `status`/`source_cutoff_at`/`rules_version`은 `NOT NULL`이라 NULL-unique 누수 없음. `CONCAT(cutoff_at, ...)` 단일 문자열 lock은 TIMESTAMP→문자열 변환이 타임존/SQL모드에 흔들려 쓰지 않고, 두 컬럼을 원본 타입으로 둔 복합 유니크를 쓴다. 상태 전이는 expected status 조건부 UPDATE(낙관적)로 한다. `artist_identity_version`은 `artist_identity_version.artist_identity_version` 참조, `resulting_snapshot_id`는 `artwork_snapshot.snapshot_id` 참조 |
| `artwork_snapshot` | PK `snapshot_id`. `artist_identity_version`은 `artist_identity_version.artist_identity_version` 참조. `serving_approval_idempotency_key`(서빙승인 멱등) **전역 UNIQUE**(`snapshot_request.approval_idempotency_key` 생성승인 멱등과 별개 키·별개 저장소; 한 컬럼이 두 멱등키를 겸하지 않는다, §5.13/§5.14.1). 같은 `serving_approval_idempotency_key` + 다른 payload(다른 `snapshot_id`/승인 대상) 호출은 충돌로 거부한다 |
| 멱등성 | 같은 `(source, source_artwork_id, run_id)` 재처리 시 결과 불변. snapshot export는 같은 입력 + 같은 규칙/환율 버전이면 동일 결과 |

합성키 생성 규칙: `source_artwork_key`(= `source` + `source_artwork_id`)와 `member_id`(= `source` + `artist_source_id`)는 표준 구분자 `::`로 합성한다(예: `art1::goods_12345`). escaping/금지 규칙은 `source`뿐 아니라 합성에 들어가는 **모든 구성요소**(`source_artwork_id`, `artist_source_id` 등)에 동일하게 적용한다. 즉 원천 ID 자체에 `::`가 들어갈 가능성에 대비해, 각 구성요소를 합성 전에 escape하거나(권장: 모든 구성요소의 `::`를 일관되게 escape) 그보다 단순하게 모든 구성요소 값에 구분자 `::`를 금지한다(`source` 코드만 금지하는 것으로는 불충분). 모든 서비스/job이 동일 규칙으로 키를 생성해 서로 다른 서비스가 같은 키를 만들도록 보장한다(§5.3, §5.8).

FK는 각 본문 테이블 정의의 `*_id` 컬럼(`run_id`, `raw_fetch_id`, `source_artwork_raw_id`, `source_artwork_interpreted_id`, `source_artist_raw_id`, `source_artist_interpreted_id`, `normalized_artist_id`)을 따른다.

### 5.17 price_model_registry

학습된 가격 예측 모델 버전을 등록하는 테이블이다. 모델 파일이 object storage나 파일 시스템에 있더라도, 운영에서 어떤 모델을 쓸 수 있는지는 이 테이블을 기준으로 판단한다.

| 컬럼 | 설명 |
|---|---|
| `model_version` | 모델 버전 PK. 예: `official_v0_1_warm_20260625_01` |
| `route` | `warm`, `cold`, `unified` 등 모델 경로 |
| `model_status` | `candidate`, `approved`, `retired`, `rejected` |
| `training_snapshot_id` | 학습에 사용한 `artwork_snapshot.snapshot_id` |
| `snapshot_export_id` | 학습 parquet/export 산출물 ID |
| `feature_generation_version` | feature 생성 코드/규칙 버전 |
| `training_code_version` | 학습 코드 git SHA 또는 버전 |
| `artifact_uri` | model bundle/joblib 등 아티팩트 위치 |
| `feature_store_uri` | 운영 feature store 위치 |
| `metrics_json` | validation/test 성능 지표 |
| `parity_report_uri` | parity 검증 리포트 위치 |
| `approved_by` | 승인자 |
| `approved_at` | 승인 시각 |
| `approval_note` | 승인/반려 사유 |
| `created_at` | 등록 시각 |

운영 원칙:

- 새 모델은 처음에 `candidate`로 등록한다.
- validation/test 검증과 parity 검증을 통과한 모델만 `approved`로 바꾼다.
- `approved` 모델만 운영 배포 대상이 될 수 있다.
- 모델이 바뀌어도 과거 `model_version` row는 삭제하지 않는다.
- 현재 운영 중인지 여부는 이 테이블의 `model_status`가 아니라 `price_model_deployment.deployment_status=active`를 단일 기준으로 본다.

### 5.18 price_model_deployment

운영 API가 현재 어떤 모델 버전을 사용하는지 기록한다. 모델 승격과 롤백은 이 테이블에 남긴다.

| 컬럼 | 설명 |
|---|---|
| `deployment_id` | 배포 ID PK |
| `route` | `warm`, `cold`, `unified` 등 모델 경로. `NOT NULL`(generated `active_route_lock`의 활성 분기 base 컬럼) |
| `model_version` | `price_model_registry.model_version` 참조 |
| `deployment_status` | `active`, `inactive`, `rolled_back`. `NOT NULL`(generated `active_route_lock`의 활성 분기 base 컬럼) |
| `active_route_lock` | 생성 컬럼. 타입은 베이스 컬럼 `route`와 동일한 `VARCHAR(32)`. `VARCHAR(32) GENERATED ALWAYS AS (CASE WHEN deployment_status='active' THEN route END) STORED`. route별 `active` 1개만 강제하는 유니크(`uq_active_route`)의 키. `active`가 아닌 행은 NULL이라 제약에서 빠진다(§5.16) |
| `deployed_by` | 배포 승인자 |
| `deployed_at` | 배포 시각 |
| `deployment_note` | 배포 사유 |
| `rolled_back_by` | 롤백 처리자 |
| `rolled_back_at` | 롤백 시각 |
| `rollback_reason` | 롤백 사유 |

운영 원칙:

- route별 `active` deployment는 하나만 허용한다. 생성 컬럼 `active_route_lock` + `uq_active_route` 유니크가 DB 레벨에서 이를 강제한다(§5.16).
- 새 deployment를 활성화하면 같은 route의 이전 active deployment를 먼저 `inactive`로 전환한 뒤 신규 active를 생성한다. 같은 트랜잭션 안에서 처리하면 `uq_active_route`가 중복 active를 막는다.
- 문제가 생기면 이전 검증 완료 모델로 `rollback` deployment를 생성하거나 이전 deployment를 다시 active로 전환한다.
- 수집 snapshot 생성, 모델 학습, 모델 운영 승격은 서로 다른 단계다. 새 수집 데이터가 들어와도 운영 모델은 자동으로 바뀌지 않는다.

### 5.19 price_prediction_log

사용자에게 반환한 가격 예측이 어느 모델에서 나온 것인지 재현하기 위한 로그다.

| 컬럼 | 설명 |
|---|---|
| `prediction_id` | 예측 요청 ID PK |
| `deployment_id` | 사용된 운영 배포 ID |
| `model_version` | 사용된 모델 버전 |
| `route` | 실제 적용된 모델 경로 |
| `artist_key` | 확정 작가 키. 없으면 null |
| `input_hash` | 입력값 hash. 원문 전체 저장이 부담되면 hash와 요약만 보존 |
| `input_summary_json` | 가격 예측에 사용한 주요 입력 요약 |
| `predicted_price_krw` | 예측 가격 |
| `confidence_label` | 사용자 표시 신뢰도 |
| `review_required` | 검수 필요 여부 |
| `created_at` | 예측 시각 |

운영 원칙:

- 개인정보나 민감 입력을 장기 보존하지 않도록 `input_summary_json` 범위를 제한한다.
- 예측 장애 또는 모델 품질 이슈가 발생하면 `prediction_id`로 모델 버전과 입력 요약을 추적한다.
- 모델 업데이트 전후 성능/응답 차이를 비교할 때 이 로그를 사용한다.

### 5.20 자격증명 관리

수집/적재/환산에 필요한 자격증명은 코드나 DB raw에 평문으로 두지 않는다.

- 대상 자격증명: 원천 API 앱 키(예: Cafe24 app key), DB 접속 정보, object storage 키, 환율 API 키.
- 주입 경로: secret manager 또는 환경변수(env)로 주입한다. DB row, raw payload, `request_params_json`, `url`에는 저장하지 않는다(§5.3 마스킹 원칙).
- 회전: 키는 주기적으로 회전한다. 회전 주기(확정 필요)와 회전 절차(신규 키 발급 → 무중단 교체 → 구 키 폐기)를 운영 런북에 둔다.
- 만료/실패: 키 만료로 수집이 실패하면 `collector_run.failure_type=auth_failed`로 남기고, 회전 후 재실행한다.

## 6. 원천별 수집 전략

### 6.1 Saatchi

현재 상태:

- 기존 수집본과 최신 split 수집본이 있다.
- size 구간별 split 수집으로 더 많은 작품을 확보한 이력이 있다.
- 가격은 주로 USD 기반으로 보인다.

권장 방식:

- API/페이지 요청 결과를 raw_fetch에 저장한다.
- 작품 ID 또는 URL slug를 `source_artwork_id`로 사용한다.
- 같은 작품의 가격/판매 상태가 바뀔 수 있으므로 row를 덮어쓰지 않고 run별 raw를 보존한다.
- normalized 단계에서 최신 row를 대표값으로 선택한다.

주의:

- 가격 통화는 원천 값 그대로 유지한다.
- KRW 환산은 raw 수집 단계에서 하지 않는다.
- 작가 ID/slug가 있어도 서비스의 최종 artist_key와 동일하다고 보지 않는다. 원천 식별자로만 저장한다.

### 6.2 Artsy

현재 상태:

- 작품 CSV와 작가 CSV가 분리되어 있다.
- 작가 국적, 생년, 갤러리 등 메타가 상대적으로 풍부하다.
- 기존 수집 과정에서 `price_krw`가 환산값으로 생성된 적이 있어 원천 가격과 계산 가격 구분이 중요하다.

권장 방식:

- 작품 raw와 작가 raw를 별도 테이블로 저장한다.
- 원천 제공 가격은 `price_raw`, `price_currency_raw`, `price_amount_raw`에 저장한다.
- 원천이 직접 KRW 가격을 제공하지 않으면 `price_krw_source`는 비워둔다.
- 환율 변환은 별도 `price_conversion` 단계에서 수행한다.

주의:

- `artist_id_or_slug`는 원천 작가 ID/slug로 저장하고, 최종 운영 artist_key로 바로 쓰지 않는다.
- 국적/갤러리/전시 메타는 입력 가능성과 품질을 따로 평가한 뒤 모델 피처로 승격한다.

### 6.3 Art1

현재 확인된 수집 구조:

- 원화 카테고리는 목록 AJAX와 상세 AJAX를 분리해서 수집한다.
- 상세 필드에서 작가명, 제작연도, 장르, 재료, 액자, 크기, 배송, 가격, 이미지 등을 얻을 수 있다.
- 상세 HTML 안의 `article.artistInfo` / `#viewPage3` / `.profile`에서 작가 프로필과 이력 섹션을 추출할 수 있다.
- 추출 가능한 작가 이력은 artist statement, 학력, 개인전, 단체전, 수상, 프로젝트, 소장처다.
- `goods_id`가 안정적인 원천 작품 ID로 보인다.
- 실제 수집 건수, 성공률, 가격 보유율, 작가 프로필 추출률은 문서에 고정하지 않고 run별 `collector_run.summary_json`과 품질 리포트에서 확인한다.

권장 방식:

- 목록 페이지 raw와 상세 페이지 raw를 모두 저장한다.
- 상세 페이지 기준으로 작품 row를 생성하되, 목록의 가격/판매완료 표시도 함께 저장한다.
- `goods_id`를 `source_artwork_id`로 사용한다.
- 상세 HTML의 작가별 작품 모아보기 링크에서 `artist_idx`를 추출해 `source_artist_raw.artist_source_id`에 저장한다.
- 작가 프로필 원문은 `source_artist_raw.bio_raw`와 `metadata_json`에 보존하고, statement/education/exhibition/awards/project/collections는 `source_artist_interpreted_staging`에서 분리한다.
- 판매완료이면서 가격이 표시되는 행과 판매완료로 가격이 없는 행을 구분한다.

주의:

- 화면 표시 총 건수와 실제 목록 반환 건수가 다를 수 있으므로 run summary에 둘 다 저장한다.
- HTML 내부 UI 텍스트가 필드에 섞일 수 있으므로 parser regression test가 필요하다.
- 작가 프로필 영역 끝에 현재 작품 추천/가격 문구가 붙을 수 있으므로 작가 이력 블록과 작품 추천 블록을 분리해야 한다.

### 6.4 Print Bakery

현재 상태:

- 작품 수집은 Cafe24 상품 API(`category=367`)를 1차 기준으로 사용하고, API 실패/필드 누락 시 HTML 목록·상세 파싱을 fallback으로 둔다.
- 오리지널 평면 카테고리에서 1,743건 상세 수집 성공.
- 상세 필드: 작품명, 작가명, 가격, 작가/제조사, 크기, 방식, 재료, edition, code, 설명.
- 2026-06-24 별도 아티스트 수집에서 작가 상세 629건 모두 성공.
- 작가 한글명 629건, 영문명 524건, meta description 605건 확보.
- meta description에서 생년 후보 120건, 사망연도 후보 14건, 출생/지역 후보 119건 추출.

권장 방식:

- Cafe24 상품 API 응답을 1차 raw로 저장하고, API 실패 시 HTML 목록/상세 raw로 보완한다.
- 목록 raw와 상세 raw를 모두 저장한다.
- `product_no`를 `source_artwork_id`로 사용한다.
- 아티스트 목록은 `/api/artist-list.html?cate_no=515`를 별도 수집한다.
- 아티스트 상세는 `/artist/detail.html?product_no={artist_product_no}`를 별도 수집한다.
- `artist_product_no`를 `source_artist_raw.artist_source_id`에 저장한다.
- 아티스트 상세의 meta description, og description, JSON-LD brand name은 `source_artist_raw`에 보존하고, 생몰연도/지역 후보는 `source_artist_interpreted_staging`에서 분리한다.
- 상세 페이지에서 가격과 품절/문의 상태를 분리한다.
- 국내 플랫폼이므로 KRW 원천 가격으로 볼 수 있는지 필드별로 명확히 표시한다.

주의:

- 상품 설명/작가 설명 등 긴 텍스트는 MySQL 본문 저장보다 payload_path 방식이 안전하다.
- 크기 표기 중 일부는 액자 기준만 제공한다(2026-06-23 수집 1,743건 중 Frame만 표기 39건). 이 행은 작품 크기 미상이므로 작품 width/height는 비우고, 액자 치수는 `frame_width_cm_candidate`/`frame_height_cm_candidate`에 보존하며 `size_basis_candidate=frame_inclusive`로 플래그한다. 액자 치수는 작품 크기 복원에 쓸 수 없으므로 보존/검수용으로만 두고 모델 피처로는 쓰지 않는다.
- 카테고리 확장 시 `cate_no`를 수집 파라미터로 저장해야 한다.
- `artist_product_no`는 Print Bakery 내부 작가 페이지 식별자이므로 운영 공통 `artist_key`로 바로 쓰지 않는다.

## 7. 주기 수집 운영 방식

### 권장 스케줄

| 원천 | 권장 주기 | 이유 |
|---|---:|---|
| Saatchi | 주 1회 | 대량 수집, 해외 원천, 변경 속도 중간 |
| Artsy | 주 1회 | 작가/작품 메타 갱신 가능 |
| Art1 | 주 1회 | 운영 단순화를 위해 전 원천 주 1회로 통일. 최근 4회 정상 run 평균 가격/판매상태 변경률이 10% 이상이면 주 2회로 상향 검토 |
| Print Bakery | 주 1회 | 운영 단순화를 위해 전 원천 주 1회로 통일. 최근 4회 정상 run 평균 가격/판매상태 변경률이 10% 이상이면 주 2회로 상향 검토 |

전 원천 주 1회를 기본 운영 주기로 둔다. 초기 안정화 기간에는 더 자주 실행해 실패율/변경률을 관찰하되, 안정화 후에는 주 1회를 기준으로 고정한다. 국내 사이트(Art1, Print Bakery)는 최근 4회 정상 run에서 `price_amount`, `price_currency`, `availability` 중 하나 이상이 바뀐 row 비율의 평균이 10% 이상이면 주 2회 수집으로 상향 검토한다. 10% 미만이면 주 1회를 유지한다.

### 실행 방식

1차 적용:

- cron 또는 GitHub Actions/self-hosted runner
- Python collector 실행
- MySQL 적재
- run summary Slack/메일 알림

운영 안정화:

- Airflow, Prefect, Dagster 중 하나로 DAG 관리
- 원천별 retry/backoff
- run별 품질 기준 미달 시 downstream 표준화 중단

## 8. Upsert와 변경 이력

작품 row는 단순히 `source_artwork_id`로 덮어쓰면 안 된다.

권장 방식:

1. 모든 수집 결과는 `source_artwork_raw`에 run별 append로 저장한다.
2. `row_hash`가 직전 최신 row와 같으면 `unchanged`로 표시한다.
3. `row_hash`가 다르면 변경 이력으로 남긴다.
4. `normalized_artwork_current`는 `normalized_artwork_staging`에서 `source_artwork_key`별 최신 정상 row만 가리키는 view다. 구현 단계에서 view로 정의하며, 별도 물리 테이블은 필수가 아니다.

이렇게 해야 가격 변동, 판매완료 전환, 작품 삭제/재등장을 추적할 수 있다.

## 9. 품질 감사 기준

run마다 최소 아래 지표를 남긴다.

- 목록 수집 건수
- 상세 수집 성공/실패 건수
- 중복 원천 ID 수
- 가격 숫자 보유 건수
- 가격 없음/문의/판매완료 건수
- 크기 파싱 성공 건수
- 작가명 누락 건수
- 이미지 URL 누락 건수
- 전회 대비 신규 작품 수
- 전회 대비 사라진 작품 수
- 전회 대비 가격 변경 작품 수
- parser warning 수

중단 기준 예시:

- 상세 실패율 5~20%는 `quality_status=blocked`로 두어 학습 snapshot 자동 반영을 보류한다(표준화 자체는 수행). 20% 이상이면 `failed`로 처리한다. 상세 기준은 [주기 수집 운영 문서](weekly_crawler_mysql_operation_plan_20260624.md) 6.2·8장을 따른다.
- 전회 대비 수집 건수가 30% 이상 감소하면 알림
- 주요 필드 파싱 성공률이 90% 미만이면 알림
- 같은 `source_artwork_id` 중복률이 5% 이상이거나 직전 정상 run 대비 2배 이상이면 알림

## 10. 모델 학습과의 연결

수집 DB를 곧바로 모델 학습에 사용하지 않는다.

권장 순서:

1. raw 수집
2. 원천별 분해/정리 staging 생성
3. normalized staging 생성
4. 품질 감사
5. 가격 통화 통일(price_conversion): 각 row collected_at 시점 환율로 KRW 환산(point-in-time), 원천 KRW(price_krw_source)는 그대로 사용
6. `artwork_snapshot`과 `artwork_snapshot_item`으로 포함/제외 row 고정
7. snapshot parquet export 생성
8. 운영자 검수, 외부 공유, 기존 CSV 기반 코드 호환이 필요할 때만 CSV export
9. 모델 학습
10. `price_model_registry`에 모델 버전과 학습 snapshot ID 연결
11. validation/test 검증과 parity 검증 통과 시 `approved` 처리
12. 운영 승격 시 `price_model_deployment`에 active deployment 기록

모델 아티팩트에는 반드시 다음을 기록한다.

- `training_snapshot_id` 또는 `snapshot_export_id`
- `source_cutoff_at`
- `price_fx_date` 또는 환율 정책 버전
- `normalization_rules_version`(사용한 snapshot의 `rules_version`)
- `feature_generation_version`
- `train/validation/test split id`
- `model_version`
- `deployment_id`(운영 승격 후)

모델 업데이트 원칙:

- 새 모델이 학습되었다고 바로 운영 API에 반영하지 않는다.
- 모델 버전은 `candidate -> approved -> retired` 흐름으로 관리하고, 운영 배포 여부는 `price_model_deployment.deployment_status=active`로 판단한다.
- 동일한 입력이라도 모델 버전이 다르면 예측값이 달라질 수 있으므로, 예측 응답과 예측 로그에는 항상 `model_version`과 `deployment_id`를 남긴다.
- 롤백 가능한 상태를 유지하기 위해 직전 운영 모델 아티팩트와 feature store는 삭제하지 않는다.

## 11. MySQL을 쓸 때의 장단점

### 장점

- 주기 수집 이력 관리가 쉽다.
- 작품/작가/원천별 변경 이력을 조회하기 쉽다.
- 중복 제거, 가격 변경, 수집 실패 감사가 쉽다.
- 운영 API나 관리자 검수 화면과 연결하기 쉽다.
- 모델 학습 snapshot을 명확하게 고정할 수 있다.

### 단점

- HTML/JSON raw payload를 전부 DB에 넣으면 DB가 빨리 커진다. 따라서 raw 본문은 1차 운영부터 object storage 분리가 필수다(권장이 아님, §5.3).
- schema migration 관리가 필요하다.
- 대량 학습에는 parquet export가 필요하고, CSV는 검수/공유/호환용으로만 추가 생성한다.
- 원천별 parser 버전 관리 없이는 DB만으로 재현성이 확보되지 않는다.

### 결론

MySQL은 운영 단일 기준 저장소로 적합하다. 다만 원본 대용량 payload는 object storage에 두고(1차 운영부터 필수), MySQL에는 경로/hash/파싱 결과/품질 지표를 저장하는 하이브리드 방식이 가장 현실적이다.

## 12. 1차 적용 범위

바로 운영 적용할 1차 범위는 아래와 같다.

- 공통 collector_run 테이블
- source_registry 테이블
- raw_fetch 테이블
- raw payload object storage 분리(필수): DB에는 `payload_path`/`payload_hash`/`payload_size`만 저장
- 비밀 파라미터 마스킹(`url_sanitized`/마스킹된 `request_params_json`)과 자격증명 secret manager/env 주입(§5.20)
- source_artwork_raw 테이블
- source_artist_raw 테이블
- source_artwork_interpreted_staging 테이블(2-table 옵션 선택 시)
- source_artist_interpreted_staging 테이블(2-table 옵션 선택 시)
- normalized_artwork_staging 테이블
- normalized_artist_staging 테이블
- artist_name_alias 테이블
- artist_identity_candidate 테이블
- artist_identity 테이블
- 신규 작가 후보 큐 SQL view 또는 export
- source별 collector 4개를 같은 인터페이스로 래핑
- run summary JSON 저장
- fx_rate_daily 테이블과 가격 통화 통일(price_conversion) 단계
- parquet export 기능
- 검수/공유/기존 코드 호환용 CSV export 기능
- 최소 검수 수단: SQL 뷰 또는 CSV 추출 기반 이름 alias·동명이인·identity 검수 큐와 승인/반려 기록
- `identity_event_log` 테이블(신규 생성·연결 확정·병합·un-merge 등 비가역 identity 결정 append-only 기록)

`artist_identity_candidate`와 `artist_identity` 테이블을 포함한다. 같은 `source + artist_source_id` 기존 연결은 자동 연결하고, 서로 다른 원천 간 자동 확정은 `alias_exact` 또는 `alias_approved`와 `birth_year_confidence=high`인 생년 일치가 모두 있을 때만 허용한다. 신규 작가 후보는 `artist_identity`에 미리 넣지 않고 후보 큐에서 관리하며, 운영자 검수 후 데이터 관리자 승인이 있을 때만 최종 `artist_key`를 생성한다.

interpreted/normalized 분리는 택일 설계다. 분해 규칙이 자주 바뀌거나 분해 실패와 표준화 실패를 분리 추적해야 하면 2-table(interpreted+normalized)을 채택하고, 그렇지 않으면 단일 staging+`*_candidate`/`quality_flags_json` 흡수안으로 시작한다. §5.6 설계 메모의 단순화 옵션이 이 흡수안이며, 두 방식을 동시에 필수로 두지 않는다.

후속 고도화 항목:

- 최종 학습 feature 생성
- 자동 모델 재학습
- 고도화된 관리자 검수 UI(대시보드/시각화). 최소 검수 수단은 위 1차 적용 범위에 포함한다
- 별도 물리 current 테이블. `normalized_artwork_current`는 view로 충분
- 복잡한 canonical artwork merge

## 13. 구현 단계 제안

### 1단계: 스키마와 적재 인터페이스

- MySQL DDL 작성
- Python DB writer 작성
- raw payload object storage 분리 적용(필수). DB에는 경로/hash/크기만 저장
- 비밀 파라미터 마스킹과 자격증명 secret manager/env 주입 적용(§5.3, §5.20)
- collector 공통 결과 포맷 정의
- 기존 CSV 출력은 호환용으로 유지

### 2단계: Art1/Print Bakery부터 DB 적재

- 이미 HTML 수집 구조가 명확하므로 DB 적재 전환이 빠르다.
- list/detail raw_fetch 저장
- source_artwork_raw 저장
- Print Bakery artist-list/detail raw_fetch 저장
- Art1 상세 HTML 기반 artist profile 추출 결과 저장
- source_artist_raw 저장
- source_artist_interpreted_staging 생성
- normalized staging 생성

### 3단계: Artsy/Saatchi DB 적재

- 기존 CSV/export 수집 스크립트 결과를 DB writer에 연결한다.
- price_raw, price_currency, price_amount, price_krw_source 구분을 강제한다.
- artist raw 테이블까지 연결한다.

### 4단계: 통합 표준화

- 기존 `standardize_merge_collected_artworks.py`의 규칙을 DB 기반 staging job으로 옮긴다.
- 기존 파일 입력 방식 대신 MySQL snapshot query를 입력으로 사용한다.
- 결과는 MySQL staging과 parquet export를 기본으로 생성한다.
- 검수/공유/기존 코드 호환이 필요하면 CSV export를 추가로 생성한다.
- 작품 표준화와 별도로 작가 표준화 job을 둔다.
- `artist_name_alias`에서 한글명/영문명 보강 후보를 만들고 검수 상태를 남긴다.
- 같은 alias 또는 승인 alias에 연결된 기존 `artist_key` 후보가 있을 때만 작가 identity 검수 후보를 생성한다.
- 같은 alias가 여러 기존 `artist_key` 후보에 걸리면 `ambiguity_status=ambiguous`로 두고 자동 확정하지 않는다.
- 작가 identity는 이름만으로 자동 확정하지 않고, 기존 후보 확인과 최종 키 부여 단계를 분리한다.
- 같은 `source + artist_source_id` 기존 연결은 자동 연결한다. 서로 다른 원천 간 자동 확정은 `alias_exact` 또는 `alias_approved`와 `birth_year_confidence=high`인 생년 일치가 모두 있을 때만 허용한다.
- 자동 확정 가능 조건을 만족하는 후보는 `auto_approved`로 기록하고 해당 `artist_key`에 연결한다. 자동 확정/반려 기준을 충족하지 못한 후보는 `needs_review`로 두고 artist_key에 바로 연결하지 않는다. 강한 충돌 조건이 있고 운영자가 반려했거나 기존 승인 이력과 직접 충돌하는 후보는 `match_rejected`로 남기되, 이는 해당 후보 artist_key와의 연결만 금지한다. 원천 row는 유지하며 다른 후보 비교 또는 신규 작가 후보 처리는 계속 가능하다.
- 자동 확정 조건을 통과했거나 데이터 관리자가 승인한 후보만 `artist_identity.artist_key`에 연결한다(운영자 검수 큐 검토를 거친 뒤).

### 5단계: 학습 snapshot 고정

- 특정 날짜 기준 stable snapshot 생성
- snapshot별 parquet export
- 운영자 검수, 외부 공유, 기존 CSV 기반 코드 호환 목적일 때만 CSV export
- 모델 학습 결과와 snapshot ID 연결
- 승인된 작가 identity 또는 검수 대기 상태를 snapshot metadata에 함께 기록

## 14. 추천 최종 구조

```text
collectors/
  art1_collector.py
  printbakery_collector.py
  artsy_collector.py
  saatchi_collector.py
  common/
    db_writer.py
    http_client.py
    payload_store.py
    schemas.py

jobs/
  run_collector.py
  interpret_artwork_staging.py
  interpret_artist_staging.py
  normalize_artwork_staging.py
  normalize_artist_staging.py
  build_artist_name_aliases.py
  build_artist_identity_candidates.py
  resolve_artist_identity_keys.py
  audit_collection_run.py
  export_training_snapshot.py

mysql/
  ddl_raw_collection.sql
  ddl_normalized_staging.sql

data_exports/
  snapshots/
    snapshot_2026_06_23/
      artworks.parquet
      artists.parquet
      training_snapshot.parquet
      summary.json
      review_sample.csv
```

## 15. 운영 판단

현재 단계에서 가장 좋은 방식은 다음이다.

- 수집 raw는 MySQL + 파일 payload store에 저장한다.
- 정규화 결과는 MySQL staging에 저장한다.
- 학습에는 MySQL에서 고정 snapshot을 export한 parquet를 우선 사용한다.
- CSV는 외부 공유, 수동 검수, 제출, 기존 코드 호환이 필요할 때만 추가 생성한다.
- 모델 운영 API는 수집 DB를 직접 보지 않고, 학습된 모델 번들과 별도 운영 feature store를 사용한다.
- 운영 모델 버전은 `price_model_deployment`의 active row를 기준으로 결정한다.

이 구조가 좋은 이유:

- 수집 시스템 장애가 예측 API 장애로 번지지 않는다.
- 학습 데이터 재현성이 높다.
- 원천 사이트별 구조 변경에 대응하기 쉽다.
- 장기적으로 작가 메타, 갤러리 티어, 가격 변경 이력을 누적할 수 있다.

## 16. 시니어 개발자 구현 체크리스트

설계가 실제 운영 코드로 옮겨질 때는 아래 항목이 빠지면 재현성과 장애 대응이 약해진다.

### 16.1 스키마/버전 관리

- MySQL DDL은 migration 파일로 관리한다.
- `collector_version`(git SHA)은 run 시작 시 자동 캡처해 run마다 기록한다. 파서가 collector와 함께 배포되므로 run 단위 provenance로는 별도 `parser_version`을 두지 않고 이 값으로 갈음한다.
- `source_registry.default_parser_version`/`default_normalizer_version`은 원천별 현재 기본 설정값이며 run 재현 기준이 아니다. 재현 기준은 run의 `collector_version`과 snapshot의 `rules_version`이다.
- 정규화 규칙 버전은 수집 run이 아니라 snapshot(`artwork_snapshot.rules_version`)과 모델 아티팩트에 기록한다.
- 버전 개념 단일 기준: 코드/파서=`collector_run.collector_version`, 정규화·필터 규칙=`artwork_snapshot.rules_version`, feature 생성=`price_model_registry.feature_generation_version`, 원천별 기본 설정 표시값=`source_registry.default_parser_version`/`default_normalizer_version`.
- 모델 학습 snapshot에는 `snapshot_export_id`, `source_cutoff_at`, `feature_generation_version`을 기록한다.
- raw payload는 object storage에 두고(1차 운영부터 필수), DB에는 `payload_path`, `payload_hash`, `payload_size`만 저장한다. DB 본문 저장은 단기 PoC 한정.

### 16.2 재실행 안전성

- 같은 `source`, `source_artwork_id`, `run_id` 조합은 중복 insert되지 않게 한다.
- 같은 URL을 재수집해도 `payload_hash`가 같으면 같은 응답으로 판정할 수 있어야 한다.
- 수집 중간 실패 후 재실행할 때 이미 성공한 list/detail 요청을 다시 써도 결과가 깨지지 않아야 한다.
- snapshot export는 같은 입력과 같은 규칙 버전이면 같은 결과를 만들어야 한다.

### 16.3 테스트 기준

필수 테스트:

- 사이트별 list/detail parser fixture test
- 가격 파싱 test
- 크기 파싱 test
- 재료/지지체 mapping test
- 작가명 한글/영문 분해 test
- Art1 작가 프로필 섹션 분해 test
- Print Bakery 아티스트 상세 meta description 분해 test
- source raw에서 normalized staging까지 row 수가 의도대로 줄어드는지 보는 integration test

### 16.4 배포/운영 분리

- 수집 DB 장애가 예측 API 장애로 이어지지 않게 한다.
- 예측 API는 운영 모델 번들과 검증된 feature store만 본다.
- 새 수집 데이터는 검수와 snapshot export를 거친 뒤 다음 모델 학습에만 반영한다.
- 모델 승격은 학습, validation/test 검증, parity 검증, `price_model_registry` 등록/승인, `price_model_deployment` 활성화, API smoke test 순서로 진행한다.

## 17. 다음 작업

- MySQL DDL 초안 작성
- 기존 4개 collector의 공통 출력 스키마 정의
- Art1 collector를 DB writer에 먼저 연결
- Print Bakery collector를 같은 방식으로 연결
- 기존 Artsy/Saatchi CSV 수집 결과를 DB 적재하는 backfill job 작성
- run별 품질 감사 리포트 생성
