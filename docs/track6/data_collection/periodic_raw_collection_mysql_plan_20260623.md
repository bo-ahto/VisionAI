# 4개 원천 사이트 주기 수집 및 MySQL 적재 기획

작성일: 2026-06-23

대상 원천:

- Saatchi
- Artsy
- Art1
- Print Bakery

관련 문서:

- [주기 수집 운영 문서](weekly_crawler_mysql_operation_plan_20260624.md)
- [artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md)
- [4개 원천 사이트별 수집 항목 정리](source_site_collected_fields_20260624.md)

## 문서 세트에서의 위치

데이터 수집 문서는 아래 순서로 읽는 것을 기준으로 한다.

1. [주기 수집 운영 문서](weekly_crawler_mysql_operation_plan_20260624.md)
   - 운영자가 수집 결과를 어떻게 확인하고 실패를 어떻게 처리하는지 설명한다.
2. [artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md)
   - 작가명 한글화/영문화, alias, 동명이인, 최종 artist_key 생성 기준을 설명한다.
3. [원천 사이트별 수집 항목 정리](source_site_collected_fields_20260624.md)
   - 원천별 작품/작가 수집 항목과 표준화 기준을 설명한다.
4. [MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md)
   - 위 운영/데이터 기준을 실제 DB와 job으로 구현하는 방법을 설명한다.

이 문서는 구현 설계를 담당한다. 운영 알림 문구나 사이트별 세부 컬럼 설명은 다른 문서에 두고, 여기서는 MySQL 테이블, 수집 job, upsert, snapshot export, 테스트 기준을 중심으로 정리한다. 작가명/alias/동명이인/`artist_key` 판단 규칙은 [artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md)을 기준으로 구현한다.

> 단일 출처(SoT) 기준: MySQL 테이블/컬럼/enum 정의의 단일 기준은 이 문서다. 다른 문서에 나오는 테이블 설명은 운영 이해를 돕기 위한 참조 부분집합이며, 스키마 정의가 어긋나면 이 문서를 기준으로 맞춘다. 작가 identity 판정 규칙의 단일 기준은 [artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md)이다.

문서 내부 흐름:

```text
목표
  -> 현재 CSV 중심 수집 방식의 한계
  -> raw first, normalize later 원칙
  -> 전체 수집 파이프라인
  -> MySQL 테이블 설계
  -> 원천별 collector 구현 전략
  -> 주기 실행과 upsert/변경 이력
  -> 품질 감사와 모델 학습 연결
  -> MVP 범위와 구현 단계
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
- 따라서 MySQL은 source of truth, parquet는 학습/분석용 snapshot, CSV는 공유/검수/호환용 export로 보는 것이 맞다.

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
| MySQL | 운영 조회, 이력, 품질 감사 | source of truth |
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
| 외부/수동 보강 필요 | post-MVP enrichment 테이블에 기록하고 `value_source`, `confidence`, `reviewer`, `review_status`를 남김(MVP 스키마에는 포함하지 않음) |

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
  - snapshot 기준일 환율(fx_rate_daily)로 원천 통화를 KRW로 환산
  - 원천이 직접 KRW를 제공한 경우(price_krw_source)는 환산하지 않고 그대로 사용
  - price_krw_normalized, fx_rate_date, fx_rate_source, price_krw_is_converted 생성
        |
        v
[학습 snapshot export]
  - 특정 기준일의 stable dataset parquet 생성
  - price_krw_normalized로 통화가 통일된 row만 export 대상
  - 외부 공유/검수/기존 코드 호환이 필요하면 CSV 추가 생성
  - 모델 학습에는 export snapshot만 사용
```

## 5. MySQL 테이블 설계 초안

### 5.1 collector_run

수집 실행 단위를 기록한다.

| 컬럼 | 설명 |
|---|---|
| `id` | run PK |
| `source` | `saatchi`, `artsy`, `art1`, `printbakery` |
| `collector_name` | 실행 스크립트/모듈명 |
| `collector_version` | 코드 버전 또는 git SHA. run 시작 시 자동 캡처. 파서도 함께 배포되므로 이 값으로 갈음 |
| `started_at` | 시작 시각 |
| `finished_at` | 종료 시각 |
| `status` | `running`, `success`, `partial_success`, `failed` |
| `quality_status` | `ok`, `warning`, `blocked`. 수집은 끝났어도 품질 기준 미달 여부를 구분한다. `blocked`와 `failed`만 학습 snapshot 자동 반영을 막는다. `warning`은 soft(필수 row 자동 반영+사후 확인), `blocked`는 운영자 승인(`override_reason`)으로 해제 가능 |
| `quality_flags_json` | 품질 경고/차단 사유와 위반한 기준 지표 요약 |
| `approved_by` | warning/partial_success run을 snapshot 반영 승인한 운영자 ID. 자동 승인은 비우거나 system |
| `approved_at` | run 반영 승인 시각 |
| `approval_note` | 반영 승인/보류/회수/확인 조치 내용과 사유 메모. 조치 유형을 나누는 별도 필드는 post-MVP |
| `override_reason` | `blocked` 해제/수동 반영 사유 |
| `snapshot_date` | 수집 기준일 |
| `request_delay_sec` | 요청 간격 |
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

### 5.2 raw_fetch

URL/API 요청 단위 원본을 저장한다.

| 컬럼 | 설명 |
|---|---|
| `id` | raw fetch PK |
| `run_id` | collector_run FK |
| `source` | 원천 |
| `fetch_type` | `list`, `detail`, `artist`, `search`, `export` |
| `url` | 요청 URL |
| `request_params_json` | 요청 파라미터 |
| `http_status` | HTTP 상태 |
| `content_type` | 응답 타입 |
| `payload_hash` | 응답 hash |
| `payload_size` | 응답 바이트 크기 |
| `payload_text` | 원본 HTML/JSON 본문. 크면 object storage 경로로 대체 가능 |
| `payload_path` | 파일/object storage 경로 |
| `error_message` | 실패 메시지 |
| `fetched_at` | 수집 시각 |

권장: MySQL에는 `payload_hash`, `payload_path`, 요약만 저장하고, 큰 HTML/JSON은 파일 또는 object storage에 저장한다. 단기 MVP에서는 MySQL `MEDIUMTEXT`도 가능하다.

### 5.3 source_artwork_raw

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

### 5.4 source_artist_raw

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

### 5.5 source_artwork_interpreted_staging

raw에서 바로 공통 표준으로 가지 않고, 사이트별 원문을 먼저 분해하고 정리하는 중간 결과다.

작품 설명과 작가 소개가 한 원문에 섞여 있으면 raw에는 원문 전체를 보존하고, 이 단계에서는 작품 관련 후보만 분리한다. 작가 관련 후보는 `source_artist_interpreted_staging`에서 분리한다.

> 설계 메모(interpreted/normalized 분리 근거와 MVP 단순화 옵션): 두 단계를 물리 테이블로 나누는 이유는 분해 실패(원문 파싱 단계)와 표준화 실패(공통 컬럼 변환 단계)를 구분해 운영자가 원인을 빠르게 찾고, raw 재수집 없이 해당 단계만 재처리하기 위해서다. 다만 현재 원천 규모(원천별 수천 row)에서는 물리 테이블 2벌이 과할 수 있다. 따라서 MVP에서는 interpreted 결과를 별도 테이블 대신 `normalized_*_staging`의 `*_candidate` 컬럼과 `parsed_parts_json`/`quality_flags_json`에 흡수하는 단순화 옵션도 허용한다. 단, 이 경우에도 분해 실패와 표준화 실패 플래그는 구분해 남겨야 두 방식의 추적성이 동일해진다. MVP에서 어느 방식을 채택하는지는 §12 MVP 구현 범위를 따른다.

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

### 5.6 source_artist_interpreted_staging

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

### 5.7 normalized_artwork_staging

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
| `price_krw_source` | 원천이 KRW를 제공한 경우만 저장 |
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

### 5.8 normalized_artist_staging

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
| `artist_identity_status` | staging 매칭 상태: `unmatched`/`candidate`/`auto_approved`/`approved`/`needs_review`/`match_rejected`. 최종 `artist_identity.identity_status`(active/merged/needs_review)와 다름 |
| `quality_flags_json` | 작가 메타 품질 플래그 |
| `normalized_at` | 표준화 시각 |

> 컬럼 범위 메모: `solo_count`, `group_count`, `fair_count`, `total_shows`, `followers`, `for_sale_works`, `total_works` 같은 인기도/전시량 지표는 보존은 하되 모델 피처로 바로 쓰지 않는다([원천 사이트별 수집 항목 정리](source_site_collected_fields_20260624.md) 10장). 결측률/입력 가능성 검증 후 승격한다.

### 5.9 artist_name_alias

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

### 5.10 artist_identity_candidate

같은 alias 또는 승인 alias에 연결된 기존 `artist_key` 후보가 있을 때만 생성하는 검수 후보 테이블이다. 원천 ID나 이름을 바로 운영 artist_key로 쓰지 않고, 근거와 상태를 남긴다. 기존 후보가 없으면 이 테이블을 거치지 않고 신규 `artist_key` 후보로 둔다.

신규 `artist_key` 후보(기존 후보가 0개)는 이 테이블을 거치지 않고 `artist_identity`에 `identity_status=needs_review`, `created_by=auto_new_candidate`로 생성해 운영자 확인 큐에 노출한다. 신규 후보는 자동으로 `active`로 두지 않고, 운영자가 승인해야 `identity_status=active`로 전환한다. 다만 같은 `source + artist_source_id`가 이미 active `artist_key`에 연결된 경우는 신규 후보가 아니라 기존 연결이므로 바로 그 키에 연결한다.

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

### 5.11 artist_identity

운영에서 사용하는 작가 키 테이블이다. 같은 작가로 확정된 여러 원천 작가 row는 하나의 `artist_key`에 연결한다. `identity_status`로 `active`(운영 사용)·`needs_review`(신규/검수 대기 provisional)·`merged`를 구분하며, 서비스와 모델은 `active` 키만 사용한다. 신규 작가도 provisional `artist_key`(needs_review)로 이 테이블에 생성되고, 승인 시 `active`로 전환한다.

| 컬럼 | 설명 |
|---|---|
| `artist_key` | 서비스 공통 최종 작가 키 |
| `canonical_name` | 대표 표시 작가명 |
| `canonical_name_ko` | 대표 한글명 |
| `canonical_name_en` | 대표 영문명 |
| `birth_year` | 승인된 생년 |
| `nationality` | 승인된 국적 |
| `identity_status` | `active`, `merged`, `needs_review` |
| `created_by` | 자동 생성 또는 운영자 ID |
| `created_at` | 최종 작가 키 생성 시각 |
| `approved_by` | 수동 승인 관리자 ID. 자동 확정 건은 비워두거나 system으로 기록 |
| `approved_at` | 수동 승인 시각 |
| `merge_evidence_json` | 최종 병합 근거 |
| `notes` | 운영자 메모 |

부여 기준:

자동 확정, 수동 승인, 반려, 보류 판단 기준은 [artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md)을 따른다. 이 테이블에서는 최종 `artist_key`와 승인/병합 근거만 보존한다.

### 5.12 artwork_snapshot

학습/운영 기준 snapshot을 고정한다.

| 컬럼 | 설명 |
|---|---|
| `snapshot_id` | snapshot PK |
| `snapshot_name` | 예: `train_candidate_2026_06_23` |
| `source_cutoff_at` | 이 시각 이전 수집분만 포함 |
| `created_at` | 생성 시각 |
| `rules_version` | 필터/정규화 규칙 버전 |
| `summary_json` | 구성 요약 |

모델 아티팩트의 `training_snapshot_id`/`snapshot_export_id`는 이 `artwork_snapshot.snapshot_id`를 가리킨다. `snapshot_export_id`는 같은 `snapshot_id`에서 만든 export 산출물(parquet/manifest)의 ID이며, 단일 export면 `snapshot_id`와 동일하게 둔다.

### 5.13 artwork_snapshot_item

snapshot에 포함된 작품 row 목록이다.

| 컬럼 | 설명 |
|---|---|
| `snapshot_id` | snapshot FK |
| `normalized_artwork_id` | normalized_artwork_staging FK |
| `price_krw_normalized` | KRW로 통일한 최종 학습용 가격(이 snapshot 기준) |
| `price_krw_is_converted` | 환산값이면 `true`, 원천 KRW면 `false` |
| `fx_rate_date` | 환산에 사용한 환율 기준일 |
| `fx_rate_source` | 환산에 사용한 환율 출처 |
| `include_status` | `included`, `excluded` |
| `exclude_reason` | 제외 사유 |

### 5.14 fx_rate_daily

학습 snapshot에서 가격 통화를 KRW로 통일할 때 사용하는 기준일 환율 테이블이다. raw/normalized 단계에서는 원천 통화를 그대로 보존하고, 환산은 snapshot export 직전의 `price_conversion` 단계에서만 수행한다. 이렇게 해야 환율 정책이 바뀌어도 원천 가격을 다시 환산해 재현할 수 있다.

| 컬럼 | 설명 |
|---|---|
| `rate_date` | 환율 기준일 |
| `base_currency` | 환산 대상 통화. 예: `USD`, `EUR` |
| `quote_currency` | 기준 통화. 운영에서는 `KRW` 고정 |
| `rate` | `base_currency` 1단위당 `quote_currency` 금액 |
| `rate_source` | 환율 출처. 예: 한국은행, ECB, 수동 입력 |
| `created_at` | 적재 시각 |

`price_conversion` 단계 출력 컬럼(학습 snapshot export에 포함):

| 컬럼 | 설명 |
|---|---|
| `price_krw_normalized` | KRW로 통일한 최종 학습용 가격 |
| `price_krw_is_converted` | 환산값이면 `true`, 원천 KRW(price_krw_source)를 그대로 쓰면 `false` |
| `fx_rate_date` | 환산에 사용한 환율 기준일 |
| `fx_rate_source` | 환산에 사용한 환율 출처 |

환산 우선순위: `price_krw_source`(원천이 직접 제공한 KRW)가 있으면 그대로 사용하고, 없으면 `price_currency`+`price_amount`를 snapshot 기준일 환율로 환산한다. 환율 데이터가 없는 통화/기준일은 환산하지 않고 `quality_flags_json`에 사유를 남긴 뒤 해당 row를 학습 snapshot 대상에서 보류한다.

이 출력 컬럼은 학습 snapshot export(parquet)에 포함되는 export 산출물이다. 재현/감사를 위해 환산에 사용한 `fx_rate_date`/`fx_rate_source`와 환율 정책 버전을 `artwork_snapshot.summary_json`(또는 export manifest)에 함께 기록한다.

### 5.15 주요 키/제약/인덱스

재현성과 재실행 안전성을 위해 최소 아래 제약을 둔다. 상세 컬럼은 위 각 테이블 정의를 따른다.

| 대상 | 제약 |
|---|---|
| `collector_run` | PK `id`. `(source, snapshot_date, collector_version)` 조회 인덱스 |
| `raw_fetch` | `(run_id, url, payload_hash)` 유니크로 같은 응답 중복 적재 방지 |
| `source_artwork_raw` | `(run_id, source, source_artwork_id)` 유니크. 재실행 시 중복 insert 금지 |
| `source_artist_raw` | `(run_id, source, artist_source_id)` 유니크 |
| `normalized_artwork_staging` | `source_artwork_key`(= `source + source_artwork_id`) 인덱스, 최신 row 조회용 인덱스 |
| `artist_name_alias` | `(normalized_artist_id, alias_name, alias_language)` 유니크 |
| `artist_identity` | `artist_key` PK |
| 멱등성 | 같은 `(source, source_artwork_id, run_id)` 재처리 시 결과 불변. snapshot export는 같은 입력 + 같은 규칙/환율 버전이면 동일 결과 |

FK는 각 본문 테이블 정의의 `*_id` 컬럼(`run_id`, `raw_fetch_id`, `source_artwork_raw_id`, `source_artwork_interpreted_id`, `source_artist_raw_id`, `source_artist_interpreted_id`, `normalized_artist_id`)을 따른다.

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
| Art1 | 주 1회 | 운영 단순화를 위해 전 원천 주 1회로 통일. 판매 상태/가격 변경이 잦은 것이 확인되면 추후 주기 상향 검토 |
| Print Bakery | 주 1회 | 운영 단순화를 위해 전 원천 주 1회로 통일. 판매 상태/가격 변경이 잦은 것이 확인되면 추후 주기 상향 검토 |

전 원천 주 1회를 기본 운영 주기로 둔다. 초기 안정화 기간에는 더 자주 실행해 실패율/변경률을 관찰하되, 안정화 후에는 주 1회를 기준으로 고정한다. 국내 사이트(Art1, Print Bakery)는 가격/판매상태 변경 빈도가 높은 것이 데이터로 확인되면 그때 주기 상향을 재검토한다.

### 실행 방식

MVP:

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

- 상세 실패율이 5% 이상이면 표준화 단계 중단
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
5. 가격 통화 통일(price_conversion): snapshot 기준일 환율로 KRW 환산, 원천 KRW(price_krw_source)는 그대로 사용
6. 학습 snapshot export 생성
7. snapshot parquet export
8. 운영자 검수, 외부 공유, 기존 CSV 기반 코드 호환이 필요할 때만 CSV export
9. 모델 학습
10. 모델 버전과 학습 snapshot ID 연결

모델 아티팩트에는 반드시 다음을 기록한다.

- `training_snapshot_id` 또는 `snapshot_export_id`
- `source_cutoff_at`
- `fx_rate_date` 또는 환율 정책 버전
- `normalization_rules_version`(사용한 snapshot의 `rules_version`)
- `feature_generation_version`
- `train/validation/test split id`

## 11. MySQL을 쓸 때의 장단점

### 장점

- 주기 수집 이력 관리가 쉽다.
- 작품/작가/원천별 변경 이력을 조회하기 쉽다.
- 중복 제거, 가격 변경, 수집 실패 감사가 쉽다.
- 운영 API나 관리자 검수 화면과 연결하기 쉽다.
- 모델 학습 snapshot을 명확하게 고정할 수 있다.

### 단점

- HTML/JSON raw payload를 전부 DB에 넣으면 DB가 빨리 커진다.
- schema migration 관리가 필요하다.
- 대량 학습에는 parquet export가 필요하고, CSV는 검수/공유/호환용으로만 추가 생성한다.
- 원천별 parser 버전 관리 없이는 DB만으로 재현성이 확보되지 않는다.

### 결론

MySQL은 운영 수집의 source of truth로 적합하다. 다만 원본 대용량 payload는 파일/object storage에 두고, MySQL에는 경로/hash/파싱 결과/품질 지표를 저장하는 하이브리드 방식이 가장 현실적이다.

## 12. MVP 구현 범위

1차 MVP는 아래 범위로 충분하다.

- 공통 collector_run 테이블
- raw_fetch 테이블
- source_artwork_raw 테이블
- source_artist_raw 테이블
- source_artwork_interpreted_staging 테이블(2-table 옵션 선택 시)
- source_artist_interpreted_staging 테이블(2-table 옵션 선택 시)
- normalized_artwork_staging 테이블
- normalized_artist_staging 테이블
- artist_name_alias 테이블
- artist_identity_candidate 테이블
- artist_identity 테이블
- source별 collector 4개를 같은 인터페이스로 래핑
- run summary JSON 저장
- fx_rate_daily 테이블과 가격 통화 통일(price_conversion) 단계
- parquet export 기능
- 검수/공유/기존 코드 호환용 CSV export 기능
- 최소 검수 수단: SQL 뷰 또는 CSV 추출 기반 이름 alias·동명이인·identity 검수 큐와 승인/반려 기록

`artist_identity_candidate`와 `artist_identity` 테이블은 MVP에도 포함하지만, MVP 단계에서는 같은 `source + artist_source_id` 자동 연결과 수동 검수 큐 운영까지만 사용한다. 서로 다른 원천 간 자동 확정은 켜지 않는다.

interpreted/normalized 분리는 택일 설계다. 분해 규칙이 자주 바뀌거나 분해 실패와 표준화 실패를 분리 추적해야 하면 2-table(interpreted+normalized)을 채택하고, 그렇지 않으면 MVP는 단일 staging+`*_candidate`/`quality_flags_json` 흡수안으로 시작한다. §5.5 설계 메모의 단순화 옵션이 이 흡수안이며, 두 방식을 동시에 필수로 두지 않는다.

MVP에서 하지 않아도 되는 것:

- 서로 다른 원천 간(cross-source) 자동 `artist_key` 확정. MVP에서는 같은 `source + artist_source_id` 자동 연결까지만 자동화하고, cross-source 후보는 전부 수동 검수 큐로 보낸다. cross-source 자동 확정 규칙은 비교 가능한 작가 메타가 충분히 확보된 뒤 활성화한다
- 최종 학습 feature 생성
- 자동 모델 재학습
- 고도화된 관리자 검수 UI(대시보드/시각화). 최소 검수 수단은 위 MVP 범위에 포함한다
- 별도 물리 current 테이블. `normalized_artwork_current`는 view로 충분
- 복잡한 canonical artwork merge

## 13. 구현 단계 제안

### 1단계: 스키마와 적재 인터페이스

- MySQL DDL 작성
- Python DB writer 작성
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
- MVP에서는 같은 `source + artist_source_id` 자동 연결만 운영하고, cross-source 자동 확정은 비활성화한 채 후보를 수동 검수 큐로 보낸다. cross-source 자동 확정 규칙은 데이터 축적 후 활성화한다.
- 자동 확정 가능 조건을 만족하는 후보는 `auto_approved`로 기록하고 해당 `artist_key`에 연결한다. 자동 확정/반려 기준을 충족하지 못한 후보는 `needs_review`로 두고 artist_key에 바로 연결하지 않는다. 강한 충돌 조건이 있고 운영자가 반려했거나 기존 승인 이력과 직접 충돌하는 후보는 `match_rejected`로 남기되, 이는 해당 후보 artist_key와의 연결만 금지한다. 원천 row는 유지하며 다른 후보 비교 또는 신규 artist_key 후보 처리는 계속 가능하다.
- 자동 확정 조건을 통과한 후보와 운영자가 승인한 후보만 `artist_identity.artist_key`에 연결한다. MVP에서는 cross-source 자동 확정을 끄므로 여기서 자동 연결되는 것은 같은 `source + artist_source_id` 케이스뿐이고, 나머지는 운영자 승인이 필요하다.

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

이 구조가 좋은 이유:

- 수집 시스템 장애가 예측 API 장애로 번지지 않는다.
- 학습 데이터 재현성이 높다.
- 원천 사이트별 구조 변경에 대응하기 쉽다.
- 장기적으로 작가 메타, 갤러리 티어, 가격 변경 이력을 누적할 수 있다.

## 16. 시니어 개발자 구현 체크리스트

설계가 실제 운영 코드로 옮겨질 때는 아래 항목이 빠지면 재현성과 장애 대응이 약해진다.

### 16.1 스키마/버전 관리

- MySQL DDL은 migration 파일로 관리한다.
- `collector_version`(git SHA)은 run 시작 시 자동 캡처해 run마다 기록한다. 파서가 collector와 함께 배포되므로 별도 `parser_version`은 두지 않고 이 값으로 갈음한다.
- 정규화 규칙 버전은 수집 run이 아니라 snapshot(`artwork_snapshot.rules_version`)과 모델 아티팩트에 기록한다.
- 모델 학습 snapshot에는 `snapshot_export_id`, `source_cutoff_at`, `feature_generation_version`을 기록한다.
- raw payload는 파일/object storage에 두고, DB에는 `payload_path`, `payload_hash`, `payload_size`를 저장한다.

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
- 모델 승격은 학습, validation/test 검증, parity 검증, 아티팩트 등록, API 배포 순서로 진행한다.

## 17. 다음 작업

- MySQL DDL 초안 작성
- 기존 4개 collector의 공통 출력 스키마 정의
- Art1 collector를 DB writer에 먼저 연결
- Print Bakery collector를 같은 방식으로 연결
- 기존 Artsy/Saatchi CSV 수집 결과를 DB 적재하는 backfill job 작성
- run별 품질 감사 리포트 생성
