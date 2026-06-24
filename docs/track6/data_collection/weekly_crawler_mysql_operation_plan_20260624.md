# Artsy / Saatchi / Print Bakery / Art1 주기 수집 운영 문서

작성일: 2026-06-24

대상:

- Artsy
- Saatchi
- Print Bakery
- Art1

목표:

- 4개 원천 사이트의 작품/작가/가격 데이터를 주 1회 자동 수집한다.
- 수집 결과를 MySQL에 저장한다.
- 원천별로 다른 데이터 구조를 공통 스키마로 평준화한다.
- 수집 성공/실패/누락/변경 이력을 운영자가 확인할 수 있게 한다.

관련 문서:

- [4개 원천 사이트별 수집 항목 정리](source_site_collected_fields_20260624.md)
- [artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md)
- [4개 원천 사이트 주기 수집 및 MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md)

## 문서 세트에서의 위치

데이터 수집 문서는 아래 순서로 읽는 것을 기준으로 한다.

1. [주기 수집 운영 문서](weekly_crawler_mysql_operation_plan_20260624.md)
   - 운영자가 매주 수집 결과를 어떻게 확인하고, 실패 시 어떻게 판단하는지 설명한다.
2. [artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md)
   - 작가명 한글화/영문화, alias, 동명이인, 최종 artist_key 생성 기준을 설명한다.
3. [원천 사이트별 수집 항목 정리](source_site_collected_fields_20260624.md)
   - Artsy / Saatchi / Print Bakery / Art1에서 어떤 작품/작가 값을 수집하고 표준화하는지 설명한다.
4. [MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md)
   - 개발자가 DB, job, migration, 재실행 안전성을 어떻게 구현할지 설명한다.

이 문서는 운영 흐름을 담당한다. 따라서 먼저 전체 수집 흐름과 실패 처리, 운영자 알림, snapshot 반영 기준을 설명하고, MySQL 테이블 구성은 운영 흐름을 이해하기 위한 참조 정보로 둔다. 작가명 보강, 동명이인 검수, 최종 `artist_key` 확정 흐름은 [artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md)을 함께 본다.

문서 내부 흐름:

```text
전체 구조
  -> 사이트별 수집 방식
  -> 운영에 필요한 MySQL 참조 테이블
  -> 크론잡 실행 방식
  -> 결과 확인
  -> 실패/부분 실패/품질 미달 알림
  -> 사이트별 데이터 평준화 방식
  -> 학습 snapshot 반영 기준
  -> 운영 알림/관리자 화면/역할별 책임
```

## 1. 전체 구조

```text
[주 1회 크론잡]
  - Artsy crawler 실행
  - Saatchi crawler 실행
  - Print Bakery crawler 실행
  - Art1 crawler 실행
        |
        v
[원본 수집]
  - API / HTML / AJAX 응답을 원본 그대로 저장
  - 요청 URL, HTTP 상태, 응답 hash, 수집 시각 기록
        |
        v
[MySQL raw 적재]
  - collector_run
  - raw_fetch
  - source_artwork_raw
  - source_artist_raw
        |
        v
[원천별 분해/정리 staging]
  - 한 컬럼에 섞인 값 분해
  - 사이트별 명칭 차이 정리
  - 가격/크기/재료/판매상태 후보값 생성
  - 작가명/국적/생년/활동지 후보값 생성
  - 전시/갤러리 원문은 자동 artist_key 판단 근거로 쓰지 않고 보존
        |
        v
[1차 표준화]
  - 분해/정리된 후보값을 공통 컬럼으로 변환
  - 통화, cm 단위, 공통 판매상태, 공통 재료 분류 적용
  - 공통 작가 메타 컬럼 생성
  - 기존 artist_key 후보가 있을 때만 작가 identity 검수 후보 생성
        |
        v
[품질 점검]
  - 수집 성공률
  - 가격 보유율
  - 크기 파싱 성공률
  - 중복률
  - 전주 대비 신규/삭제/변경 건수
        |
        v
[가격 통화 통일(price_conversion)]
  - snapshot 기준일 환율(fx_rate_daily)로 원천 통화를 KRW로 환산
  - 원천 KRW(price_krw_source)는 환산하지 않고 그대로 사용
  - price_krw_normalized 생성
        |
        v
[학습 snapshot export]
  - 승인 가능한 row만 학습 snapshot export 대상으로 고정
  - parquet 우선 export
  - 외부 공유/수동 검수/제출이 필요하면 CSV export 추가 생성
```

저장 포맷 운영 원칙:

- 원천 응답은 원래 형식 그대로 저장한다. JSON API는 JSON, HTML 페이지는 HTML, 원천 CSV export는 CSV 원본으로 보존한다.
- row 단위 raw 파싱 결과는 MySQL raw 테이블과 JSONL export로 관리할 수 있다.
- 운영 조회와 변경 이력 관리는 MySQL을 기준으로 한다.
- 분석/학습 snapshot은 parquet를 우선 사용한다.
- CSV는 운영 저장소가 아니라 사람이 확인하거나 외부에 전달해야 할 때 생성하는 export 포맷으로 둔다.

## 2. 사이트별 수집 방식

사이트별로 실제 수집되는 상세 항목은 [4개 원천 사이트별 수집 항목 정리](source_site_collected_fields_20260624.md)를 기준으로 관리한다.

| 사이트 | 권장 수집 방식 | 원천 ID | 비고 |
|---|---|---|---|
| Artsy | 기존 Artsy 수집/API/export 기반 | artwork id 또는 artwork slug | 작품 CSV와 작가 CSV를 분리 수집하고 MySQL에서 연결 |
| Saatchi | 기존 Saatchi 수집/API/export 기반 | artwork id 또는 artwork URL/slug | 대량 수집 시 구간 분할 수집 가능 |
| Print Bakery | Cafe24 JSON API 우선, HTML fallback + 아티스트 목록/상세 수집 | 작품 `product_no`, 작가 `artist_product_no` | `category=367` 작품 API와 `/api/artist-list.html?cate_no=515` 작가 목록을 분리 수집 |
| Art1 | 내부 AJAX endpoint 우선, HTML fallback + 상세 HTML 작가 프로필 추출 | 작품 `goods_id`, 작가 `artist_idx` | 목록/상세 AJAX endpoint 사용, 작가 프로필은 상세 HTML의 `article.artistInfo`에서 추출 |

### 2.1 Artsy

Artsy는 작품 데이터와 작가 메타 데이터를 분리해서 수집하고, MySQL 적재 단계에서 `artist_slug` 또는 작가 식별자를 기준으로 연결한다.

```text
작품 수집:
  - artwork id 또는 artwork slug
  - 작품명, 제작연도, 작품 URL, 이미지 URL
  - 원천 가격 문자열, 원천 통화, 원천 통화 기준 숫자 가격
  - 크기, 재료/매체, 판매상태
  - 갤러리명, 갤러리 유형, 갤러리 도시

작가 수집:
  - artist_slug
  - 작가명, 국적, 생년, 성별
  - 작품 수, 판매중 작품 수, 팔로워 수
  - 개인전/단체전/아트페어 수
  - biography, website, instagram
```

주의:

- Artsy 원천에 `price_krw`가 있더라도 고정 환율로 계산된 값이면 raw 단계에서 사용하지 않는다.
- 원천 통화와 원천 가격 숫자를 우선 보존하고, 원화 환산은 별도 환율 정책 단계에서 수행한다.
- `artist_slug`는 Artsy 내부 ID이며 운영 공통 `artist_key`가 아니다.

### 2.2 Saatchi

Saatchi는 작품 정보와 작가 정보를 별도로 수집하고, 작품 row의 작가 ID와 작가 export 정보를 연결한다. 대량 수집 시 구간 분할 수집이 가능하다.

```text
작품 수집:
  - artwork id 또는 artwork URL/slug
  - 작품명, 제작연도, 이미지 URL
  - USD 가격, 크기, 재료/매체
  - category, subject, style, orientation
  - artist id, artist first/last name

작가 수집:
  - artist id
  - first name, last name
  - 성별, 국가, 도시
  - 팔로워 수, 등록 작품 수
  - bio, education, exhibitions
  - instagram, website, profile URL
```

주의:

- Saatchi 가격은 주로 USD 기준이므로 raw 수집 단계에서 KRW로 환산하지 않는다.
- `artist_id`는 Saatchi 내부 ID이며 운영 공통 `artist_key`가 아니다.
- `category`, `style`, `subject`는 학습 피처 후보가 될 수 있지만 사용자 입력 가능성과 결측률을 별도 검증한 뒤 사용한다.

### 2.3 Print Bakery

Print Bakery는 기존에는 HTML 파싱으로 수집했지만, 추가 확인 결과 Cafe24 상품 API를 사용할 수 있다.

```text
작품 수집:
https://printbakery.cafe24api.com/api/v2/products
  ?category=367
  &limit=100
  &offset=0
  &cafe24_app_key={page_exposed_key}
  &cafe24_api_version=2022-09-01

HTML fallback:
  - 목록/상세 HTML에서 작품명, 작가명, 가격, 크기, 재료, 이미지 보완
```

작가 수집:

```text
Print Bakery 아티스트 목록:
https://printbakery.com/api/artist-list.html?cate_no=515

Print Bakery 아티스트 상세:
https://printbakery.com/artist/detail.html?product_no={artist_product_no}

추천 작가 배너:
https://back.printbakery.com/infos/?f=get-search-artist-banner
```

주의:

- `price_content`가 `구매 별도 문의`일 수 있으므로 가격 숫자와 가격 문구를 분리한다.
- API가 실패하거나 앱 키/API 버전이 변경될 수 있으므로 HTML fallback을 유지한다.
- `artist_product_no`는 Print Bakery 내부 작가 페이지 식별자이며 운영 공통 `artist_key`가 아니다.

### 2.4 Art1

Art1은 아래처럼 목록/상세 AJAX endpoint를 사용한다.

```text
작품 수집:
목록:
https://www.art1.com/marketPlace/__artworks_list.php?page={page}&medium=0

상세:
https://www.art1.com/marketPlace/__detail_view.php?goods={goods_id}
```

작가 수집/추출:

```text
https://www.art1.com/marketPlace/__detail_view.php?goods={goods_id}
  -> 상세 HTML 내부 article.artistInfo / #viewPage3 / .profile에서 추출
```

주의:

- 목록의 판매완료 표시와 상세 가격이 다를 수 있으므로 둘 다 보존한다.
- 호수는 모델 계산의 기본 단위가 아니라 표시/보조 정보로 저장한다.
- `artist_idx`는 Art1 내부 작가 식별자이며 운영 공통 `artist_key`가 아니다.

실제 수집 건수, 성공률, 가격 보유율, 작가 메타 보유율은 고정 문서에 직접 쓰지 않고 `collector_run.summary_json`과 run별 품질 리포트에서 확인한다. 이렇게 해야 특정 날짜의 실측 결과가 문서 양식을 깨거나 최신 상태처럼 오해되는 일을 줄일 수 있다.

## 3. 운영 참조용 MySQL 테이블 구성

이 섹션은 운영자가 수집 결과와 실패 원인을 이해할 때 필요한 테이블 참조다. 상세 DDL, migration, job 구조는 [MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md)에서 관리한다.

이 절의 테이블/컬럼은 [MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md) 스키마의 운영 참조 부분집합이다. 전체 컬럼·enum의 단일 기준(SoT)은 그 문서이며, 정의가 어긋나면 [MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md)을 기준으로 맞춘다.

### 3.1 collector_run

수집 실행 단위다. 크론잡이 실행될 때 사이트별로 1개 run을 만든다.

| 컬럼 | 설명 |
|---|---|
| `id` | 수집 run ID |
| `source` | `artsy`, `saatchi`, `printbakery`, `art1` |
| `collector_version` | 크롤러 코드 버전 또는 git SHA |
| `started_at` | 시작 시각 |
| `finished_at` | 종료 시각 |
| `status` | `running`, `success`, `partial_success`, `failed` |
| `quality_status` | `ok`, `warning`, `blocked`. 수집 완료 후 품질 기준 미달 여부. `blocked`/`failed`만 snapshot 자동 반영을 막는다 |
| `quality_flags_json` | 품질 경고/차단 사유와 위반 지표 요약 |
| `total_requested` | 요청 수 |
| `total_success` | 성공 요청 수 |
| `total_failed` | 실패 요청 수 |
| `raw_artwork_rows` | raw 작품 row 수 |
| `raw_artist_rows` | raw 작가 row 수 |
| `interpreted_artwork_rows` | 작품 원천별 분해/정리 row 수 |
| `interpreted_artist_rows` | 작가 원천별 분해/정리 row 수 |
| `normalized_artwork_rows` | 작품 표준화 row 수 |
| `normalized_artist_rows` | 작가 표준화 row 수 |
| `summary_json` | 수집 요약 |

### 3.2 raw_fetch

실제 요청/응답 단위 기록이다.

| 컬럼 | 설명 |
|---|---|
| `id` | 요청 ID |
| `run_id` | collector_run ID |
| `source` | 사이트 |
| `fetch_type` | `list`, `detail`, `artist`, `search`, `export` |
| `url` | 요청 URL |
| `http_status` | HTTP 상태 |
| `payload_hash` | 응답 내용 hash |
| `payload_path` | 원본 HTML/JSON 저장 경로 |
| `error_message` | 실패 사유 |
| `fetched_at` | 수집 시각 |

### 3.3 source_artwork_raw

사이트별 작품 원본 파싱 결과다. 원천 구조를 최대한 보존한다.

| 컬럼 | 설명 |
|---|---|
| `id` | raw artwork ID |
| `run_id` | collector_run ID |
| `source` | 사이트 |
| `source_artwork_id` | 원천 작품 ID |
| `source_artwork_url` | 원천 URL |
| `title_raw` | 원천 작품명 |
| `artist_name_raw` | 원천 작가명 |
| `artist_source_id` | 원천 작가 ID/slug |
| `price_raw` | 가격 원문 |
| `price_currency_raw` | 원천 통화 |
| `price_amount_raw` | 원천 숫자 가격 |
| `dimensions_raw` | 크기 원문 |
| `medium_raw` | 재료/매체 원문 |
| `availability_raw` | 판매상태 원문 |
| `image_url` | 이미지 URL |
| `metadata_json` | 사이트별 작품 추가 필드 |
| `row_hash` | 주요 값 hash |

### 3.4 source_artist_raw

사이트별 작가 원본 파싱 결과다. 작품 row에 붙어 있는 작가명만 저장하지 않고, 작가 페이지/API/export에서 얻은 메타도 별도 raw로 보존한다.

| 컬럼 | 설명 |
|---|---|
| `id` | raw artist ID |
| `run_id` | collector_run ID |
| `source` | 사이트 |
| `artist_source_id` | 원천 작가 ID/slug |
| `artist_source_url` | 원천 작가 페이지 URL |
| `artist_name_raw` | 원천 작가명 |
| `nationality_raw` | 국적 원문 |
| `birth_year_raw` | 출생연도 원문 |
| `location_raw` | 활동지/도시 원문 |
| `gallery_raw` | 갤러리 원문 |
| `education_raw` | 학력 원문 |
| `exhibition_raw` | 전시/이력 원문 |
| `bio_raw` | 작가 소개문 원문 |
| `metadata_json` | 사이트별 작가 추가 메타 |
| `row_hash` | 주요 값 hash |

### 3.5 source_artwork_interpreted_staging

raw에서 바로 공통 표준으로 가지 않고, 사이트별 원문을 먼저 분해하고 정리하는 중간 테이블이다.

이 단계의 목적:

- 한 컬럼에 여러 의미가 섞인 값을 분해한다.
- 같은 의미지만 사이트별로 다른 명칭을 쓰는 값을 후보 표준명으로 맞춘다.
- 원문은 보존하되, 표준화가 사용할 후보 컬럼을 만든다.
- 분해 실패/애매한 값을 `quality_flags_json`에 남겨 사람이 검수할 수 있게 한다.

예:

```text
Print Bakery
  additional_information = [
    {"name": "size", "value": "Image 29.7x21cm / Frame 38.6x38.6cm"},
    {"name": "method", "value": "Hand painted"}
  ]
        |
        v
  width_cm_candidate = 29.7         # Image(작품) 크기
  height_cm_candidate = 21.0
  frame_width_cm_candidate = 38.6   # 액자 치수는 분리 보존(모델 피처 아님)
  frame_height_cm_candidate = 38.6
  size_basis_candidate = "artwork"
  method_candidate = "Hand painted"
```

> 위 예시의 `method_candidate`는 컬럼이 아니라 `parsed_parts_json` 분해 결과 예시이며 `medium_text_candidate`로 표준화한다. 작품 크기(width/height)는 Image 값을 쓰고, 액자(Frame) 치수는 `frame_width_cm_candidate`/`frame_height_cm_candidate`에 분리 보존한다(모델 피처로는 쓰지 않음). 액자만 표기된 행은 작품 width/height를 비우고 `size_basis_candidate=frame_inclusive`로 플래그한다.

| 컬럼 | 설명 |
|---|---|
| `id` | 중간 staging row ID |
| `source_artwork_raw_id` | 원본 row ID |
| `source` | 사이트 |
| `source_artwork_id` | 원천 작품 ID |
| `title_candidate` | 정리된 작품명 후보 |
| `artist_name_candidate` | 정리된 작가명 후보 |
| `price_text_candidate` | 정리된 가격 문구 후보 |
| `price_currency_candidate` | 통화 후보 |
| `price_amount_candidate` | 숫자 가격 후보 |
| `width_cm_candidate` | 가로 cm 후보 |
| `height_cm_candidate` | 세로 cm 후보 |
| `depth_cm_candidate` | 깊이 cm 후보 |
| `frame_width_cm_candidate` | 액자 가로 cm 후보(작품 크기와 분리 보존, 모델 피처 아님) |
| `frame_height_cm_candidate` | 액자 세로 cm 후보 |
| `size_basis_candidate` | 작품 이미지 기준/액자 포함 기준 등 크기 기준 |
| `medium_text_candidate` | 재료/매체 문구 후보 |
| `support_text_candidate` | 지지체 문구 후보 |
| `medium_alias_applied` | 사이트별 명칭 매핑 적용 여부 |
| `availability_candidate` | 판매상태 후보 |
| `artist_source_id_candidate` | 원천 작가 ID 후보 |
| `parsed_parts_json` | 분해된 세부 값 |
| `quality_flags_json` | 분해 실패/애매함/충돌 플래그 |
| `interpreted_at` | 중간 정리 시각 |

### 3.6 source_artist_interpreted_staging

작가 raw를 바로 최종 작가 키로 쓰지 않고, 이름/국적/생년/활동지 정보를 먼저 분해하고 정리하는 중간 테이블이다. 전시/갤러리 원문은 수집 보존 대상이지만, 동명이인 판단이나 자동 artist_key 확정 근거로 쓰지 않는다.

| 컬럼 | 설명 |
|---|---|
| `id` | 중간 staging row ID |
| `source_artist_raw_id` | 원본 작가 row ID |
| `source` | 사이트 |
| `artist_source_id_candidate` | 원천 작가 ID/slug 후보 |
| `artist_source_url_candidate` | 작가 페이지 URL 후보 |
| `artist_name_display_candidate` | 표시용 작가명 후보 |
| `artist_name_ko_candidate` | 한글 작가명 후보 |
| `artist_name_en_candidate` | 영문 작가명 후보 |
| `nationality_candidate` | 국적 후보 |
| `birth_year_candidate` | 출생연도 후보 |
| `birth_year_source` | 출생연도 후보의 출처. 예: `structured_field`, `birth_context_text`, `year_only_text`, `manual` |
| `birth_year_confidence` | 출생연도 파싱 신뢰도 |
| `location_city_candidate` | 활동 도시 후보 |
| `location_country_candidate` | 활동 국가 후보 |
| `gallery_name_candidate` | 갤러리명 후보 |
| `education_text_candidate` | 학력 후보 |
| `exhibition_text_candidate` | 전시/이력 후보 |
| `bio_text_candidate` | 작가 소개문 후보 |
| `identity_hint_json` | 작가 매칭에 쓸 보조 힌트 |
| `quality_flags_json` | 동명이인 위험/이름 충돌/메타 부족 플래그 |
| `interpreted_at` | 중간 정리 시각 |

### 3.7 normalized_artwork_staging

원천별 분해/정리 staging을 입력으로 받아, 4개 사이트를 같은 기준으로 맞춘 1차 표준화 테이블이다.

| 컬럼 | 설명 |
|---|---|
| `id` | 표준화 row ID |
| `source_artwork_raw_id` | 원본 row ID |
| `source_artwork_interpreted_id` | 원천별 분해/정리 row ID |
| `source` | 사이트 |
| `source_artwork_key` | `source + source_artwork_id` |
| `title` | 표준 작품명 |
| `artist_name` | 표준 작가명 |
| `artist_source_id` | 원천 작가 ID/slug가 있으면 저장 |
| `normalized_artist_id_candidate` | normalized_artist_staging과 연결 가능한 경우의 후보 ID |
| `artist_identity_status` | `unmatched`, `candidate`, `auto_approved`, `approved`, `needs_review`, `match_rejected` |
| `price_currency` | 통화 |
| `price_amount` | 통화 기준 가격 숫자 |
| `price_krw_source` | 원천이 KRW로 제공한 가격 |
| `width_cm` | 가로 cm |
| `height_cm` | 세로 cm |
| `depth_cm` | 깊이 cm |
| `medium_raw` | 원천 재료 |
| `medium_category_candidate` | 재료 분류 후보 |
| `is_3d_candidate` | 입체/설치 후보 |
| `availability` | 판매상태 |
| `quality_flags_json` | 품질 플래그 |

### 3.8 normalized_artist_staging

원천별 작가 분해/정리 staging을 입력으로 받아, 4개 사이트의 작가 메타를 같은 컬럼 기준으로 맞춘 1차 표준화 테이블이다.

| 컬럼 | 설명 |
|---|---|
| `id` | 표준화 작가 row ID |
| `source_artist_raw_id` | 원본 작가 row ID |
| `source_artist_interpreted_id` | 원천별 작가 분해/정리 row ID |
| `source` | 사이트 |
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
| `artist_name_normalized` | 공백/대소문자/기호를 정리한 매칭용 이름 |
| `nationality` | 표준 국적 |
| `birth_year` | 숫자 출생연도 |
| `location_city` | 활동 도시 |
| `location_country` | 활동 국가 |
| `gallery_name` | 갤러리명 |
| `education_text` | 학력 텍스트 |
| `exhibition_text` | 전시/이력 텍스트 |
| `bio_text` | 작가 소개문 |
| `quality_flags_json` | 작가 메타 품질 플래그 |

### 3.9 artist_name_alias

작가 이름 한글화/영문화 보강과 검수 이력을 관리하는 테이블이다. 서비스 표시와 artist_key 후보 생성을 위해 사용하지만, 자동 변환명만으로 작가 identity를 확정하지 않는다.

| 컬럼 | 설명 |
|---|---|
| `id` | alias ID |
| `artist_key` | 이미 확정된 작가라면 연결되는 최종 작가 키 |
| `normalized_artist_id` | normalized_artist_staging ID |
| `source` | 사이트 |
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

### 3.10 artist_identity_candidate

같은 alias 또는 승인 alias에 연결된 기존 `artist_key` 후보가 있을 때만 생성하는 검수 후보 테이블이다. 모든 작가 row를 이 테이블에 넣지 않는다. 자동으로 최종 artist_key를 확정하지 않고, 사람이 확인할 수 있는 근거를 함께 남긴다.

| 컬럼 | 설명 |
|---|---|
| `id` | 후보 ID |
| `candidate_group_id` | alias 기반 기존 artist_key 후보가 있을 때 생성되는 검수 후보 그룹 ID |
| `normalized_artist_id` | normalized_artist_staging ID |
| `artist_name_normalized` | 매칭용 이름 |
| `source` | 사이트 |
| `artist_source_id` | 원천 작가 ID/slug |
| `match_score` | 후보 정렬용 참고 점수. 자동 확정은 점수 합산이 아니라 alias 일치, 고신뢰 생년 일치, 충돌 없음 조건으로 판단 |
| `match_evidence_json` | 어떤 근거로 묶였는지 |
| `conflict_reasons_json` | 같은 인물로 보기 어려운 충돌 사유 |
| `ambiguity_status` | `unique`, `ambiguous`, `needs_review` |
| `candidate_artist_key_count` | 같은 alias 또는 승인 alias로 연결될 수 있는 후보 artist_key 수 |
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

### 3.11 artist_identity

운영에서 사용하는 최종 작가 키 테이블이다. 같은 작가로 확정된 여러 원천 작가 row는 하나의 `artist_key`에 연결한다.

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

## 4. 크론잡 운영 방식

주 1회 실행을 기본으로 한다.

예시:

```cron
# 매주 월요일 새벽 03:00 실행
0 3 * * 1 /app/scripts/run_weekly_collectors.sh
```

실행 순서:

```text
1. collector_run 생성
2. 사이트별 crawler 실행
3. raw_fetch 저장
4. source_artwork_raw 저장
5. source_artist_raw 저장
   - Artsy/Saatchi는 원천 작가 export/API 결과 저장
   - Print Bakery는 아티스트 목록/상세 별도 수집 결과 저장
   - Art1은 상세 HTML 작가 프로필 추출 결과 저장
6. source_artwork_interpreted_staging 생성
7. source_artist_interpreted_staging 생성
8. normalized_artwork_staging 생성
9. normalized_artist_staging 생성
10. artist_name_alias 후보 생성/검수 상태 갱신
11. artist_identity_candidate 생성/갱신
12. artist_identity 자동 확정 가능 건 연결/신규 생성
13. 자동 확정/반려 기준을 충족하지 못한 후보는 운영자 검수 큐에 등록
14. 품질 점검 결과 저장
15. 알림 발송
```

권장 실행 순서:

1. Artsy
2. Saatchi
3. Print Bakery
4. Art1

이 순서는 중요도가 아니라 운영 안정성 기준이다. 해외 대량 수집을 먼저 실행하고, 국내 사이트는 비교적 짧은 job으로 뒤에 둔다.

## 5. 데이터 수집 결과는 어떻게 확인하는가

수집 결과는 MySQL의 `collector_run`(요청/행 수, `status`, `quality_status`, `summary_json`, `quality_flags_json`)에서 확인한다.

### 5.1 run 단위 확인

운영자가 가장 먼저 확인할 값:

```sql
SELECT
  id,
  source,
  status,
  quality_status,
  started_at,
  finished_at,
  total_requested,
  total_success,
  total_failed,
  raw_artwork_rows,
  raw_artist_rows,
  normalized_artwork_rows,
  normalized_artist_rows
FROM collector_run
ORDER BY started_at DESC
LIMIT 20;
```

확인 기준:

- `status = success`이면 정상 완료
- `status = partial_success`이면 일부 실패가 있으나 사용 가능한 데이터가 있음
- `status = failed`이면 해당 사이트 수집 실패
- `raw_artwork_rows`는 원천에서 수집된 작품 수
- `raw_artist_rows`는 원천에서 수집/추출된 작가 수
- `normalized_artwork_rows`는 1차 표준화까지 통과한 작품 수
- `normalized_artist_rows`는 1차 표준화까지 통과한 작가 수
- 작가 수집은 `source_artist_raw`, `normalized_artist_staging`, `artist_name_alias`, `artist_identity_candidate` 건수를 함께 본다.

### 5.2 사이트별 수집 품질 확인

확인해야 하는 품질 지표:

| 지표 | 의미 |
|---|---|
| 수집 row 수 | 이번 주에 수집된 작품 수 |
| 상세 성공률 | 상세 페이지/API 호출 성공률 |
| 가격 보유율 | 가격 숫자가 있는 작품 비율 |
| 크기 파싱 성공률 | 가로/세로 cm를 추출한 비율 |
| 작가명 보유율 | 작가명이 있는 비율 |
| 작가 메타 보유율 | 국적/생년/활동지/갤러리/소개문 중 하나 이상이 있는 작가 비율 |
| 작가 상세 수집 성공률 | 작가 목록 row 중 작가 상세/프로필까지 수집된 비율 |
| 작가 이력 분해 성공률 | statement, 학력, 전시, 수상, 프로젝트 등 이력 섹션을 분해한 비율 |
| 작가 identity 후보 수 | alias 기반 기존 artist_key 후보가 있어 검수 후보로 올라온 수 |
| 작가 identity 검수 대기 수 | 자동 확정하지 않고 운영자 확인이 필요한 작가 후보 수 |
| 중복률 | 같은 source_artwork_id가 중복된 비율 |
| 신규 작품 수 | 전주에 없고 이번 주에 새로 생긴 작품 |
| 사라진 작품 수 | 전주에는 있었으나 이번 주에는 없는 작품 |
| 가격 변경 작품 수 | 같은 작품의 가격이 바뀐 수 |

품질 리포트는 관리자 화면과 MySQL 집계가 기본이다. CSV는 운영자가 엑셀로 검수하거나 외부 제출/공유가 필요할 때만 별도로 생성한다.

### 5.3 문서 기준 적용 가능성 점검

문서에 적힌 자동 확정, 충돌, 승격 기준은 실제 수집 데이터에서 필요한 필드가 존재하고, 원천쌍 비교에서 사용할 수 있을 때만 운영 규칙으로 유지한다. 매주 수집 run이 끝나면 아래 점검을 수행한다.

| 점검 항목 | 확인 방법 | 운영 판단 |
|---|---|---|
| 자동 규칙 입력 필드 존재 여부 | 규칙에 필요한 컬럼이 raw/staging/normalized 테이블에 실제로 존재하는지 확인 | 컬럼이 없으면 해당 규칙은 적용하지 않고 문서를 수정한다 |
| 원천별 필드 보유율 | source별 `artist_source_id`, 이름, 생년, 국적, 활동지 보유율 집계 | source별 보유율이 30% 미만인 필드는 자동 확정 근거로 쓰지 않는다 |
| 교차 원천 비교 가능성 | 같은 이름 후보를 원천쌍별로 만들고, 양쪽 모두 비교 가능한 메타가 있는지 집계 | 원천쌍별 비교 가능 후보가 20쌍 미만이거나 후보 대비 30% 미만이면 점수화하지 않고 검수 참고값으로 둔다 |
| 추출값 신뢰도 | 자유 텍스트에서 추출한 연도/지역이 실제 의미와 맞는지 샘플 검수 | 단순 4자리 연도처럼 잘못 추출된 값이 있으면 `low`로 두고 자동 확정에 쓰지 않는다 |
| 자동 확정 결과 샘플 검수(cross-source는 MVP 비활성, post-MVP 적용) | `auto_approved` 후보를 원천쌍별 최대 30건 샘플링해 사람이 확인 | 샘플에서 1건 이상 잘못 확정된 후보가 발견되면 해당 규칙은 즉시 `needs_review` 기준으로 낮춘다 |

현재 적용 가능한 보수 기준:

- 같은 `source + artist_source_id`가 이미 확정된 경우는 같은 원천 내부 식별자이므로 바로 연결할 수 있다.
- 서로 다른 원천 간 자동 확정은 `alias_exact` 또는 `alias_approved`와 `birth_year_confidence=high`인 생년 일치가 모두 있을 때만 허용한다. 단, MVP에서는 cross-source 자동 확정을 끄고 cross-source 후보를 전부 `needs_review`로 보낸다. 이 기준은 비교 가능한 메타가 확보된 post-MVP 활성화 시 적용한다.
- 국적, 활동지, 전시, 갤러리는 원천별 보유율과 의미가 다르므로 자동 점수로 쓰지 않고 검수 참고 또는 충돌 경고로만 사용한다.
- 문서에 있는 기준이라도 실제 데이터에서 비교 가능한 필드가 없거나 잘못 추출된 값이 확인되면 운영 규칙에서 제외하고 문서를 업데이트한다.

예시 조회:

```sql
SELECT
  source,
  COUNT(*) AS raw_artwork_rows,
  SUM(price_amount_raw IS NOT NULL) AS price_rows,
  SUM(artist_name_raw IS NOT NULL AND artist_name_raw != '') AS artist_rows,
  SUM(dimensions_raw IS NOT NULL AND dimensions_raw != '') AS dimension_rows
FROM source_artwork_raw
WHERE run_id = :run_id
GROUP BY source;
```

작가 수집 품질은 별도로 본다.

```sql
SELECT
  source,
  COUNT(*) AS raw_artist_rows,
  SUM(artist_name_raw IS NOT NULL AND artist_name_raw != '') AS named_artist_rows,
  SUM(nationality_raw IS NOT NULL OR birth_year_raw IS NOT NULL OR location_raw IS NOT NULL) AS meta_artist_rows
FROM source_artist_raw
WHERE run_id = :run_id
GROUP BY source;
```

### 5.4 관리자 화면에서 보여줄 내용

관리자 화면은 아래 항목을 기본으로 보여준다.

```text
[수집 run 목록]
  - 수집일
  - 사이트
  - 상태
  - 원본 수집 건수
  - 원천별 분해/정리 통과 건수
  - 표준화 통과 건수
  - 실패 건수
  - 전주 대비 증감

[run 상세]
  - 목록 요청 성공/실패
  - 상세 요청 성공/실패
  - 한 컬럼에 섞인 값 분해 실패 row
  - 사이트별 명칭 매핑 실패 row
  - 가격 없음 row
  - 크기 파싱 실패 row
  - 작가 메타 분해 실패 row
  - 작가 identity 후보 검수 대기 row
  - 중복 후보 row
  - 제외 후보 row
```

## 6. 1차 데이터 수집이 안 되었을 때 어떻게 동작하는가

수집 실패와 품질 차단은 크게 5가지 케이스로 나눈다.

공통 원칙:

- 수집 실패, 부분 실패, 분해 실패, 표준화 실패, 품질 기준 미달은 모두 운영자에게 알린다.
- 실패(`failed`) run이나 `blocked` run은 자동으로 학습 snapshot export에 반영하지 않는다. `warning`은 필수 row만 자동 반영하고 운영자가 사후 확인한다.
- 알림은 단순히 "실패"만 보내지 않고, 운영자가 바로 판단할 수 있도록 요점을 같이 보낸다.

운영자 알림에 반드시 포함할 요점:

| 항목 | 설명 |
|---|---|
| 발생 위치 | 사이트, 수집 단계, run ID |
| 실패 유형 | 전체 실패, 일부 상세 실패, 분해/정리 실패, 표준화 실패, 품질 기준 미달 |
| 영향 범위 | 영향받은 요청 수, 작품 row 수, 작가 row 수 |
| 자동 조치 | raw 보존, staging 중단, normalized 생성 보류, snapshot 반영 제외 |
| 운영자 확인 항목 | 실패 URL, parser error, unmapped 값, identity 검수 후보, 전주 대비 급감 사유 |
| 다음 조치 | 재수집, parser 수정, alias table 보강, 수동 승인, 이번 run 폐기 |

### 6.1 전체 사이트 수집 실패

예:

- 사이트 접속 불가
- DNS 실패
- API 인증 실패
- HTML 구조가 완전히 변경됨

동작:

```text
1. collector_run.status = failed 로 저장
2. raw_fetch에 실패 URL과 error_message 저장
3. 해당 사이트의 source_artwork_interpreted_staging 생성 중단
4. 해당 사이트의 source_artist_interpreted_staging 생성 중단
5. 해당 사이트의 normalized_artwork_staging / normalized_artist_staging 생성 중단
6. 이번 주 학습 snapshot에는 해당 사이트의 신규 데이터를 반영하지 않음
7. 마지막 정상 수집본은 유지
8. 운영자에게 알림
```

운영자 알림 요약:

```text
[수집 실패] {source} 전체 수집 실패
- run_id: {run_id}
- 실패 단계: list/detail/API 접속
- 실패 요청: {failed_requests}/{total_requests}
- 주요 원인: {대표 error_message}
- 자동 조치: raw/staging/normalized 생성 중단, 이번 주 snapshot 반영 제외
- 운영자 확인: 사이트 접속 가능 여부, API 인증/endpoint 변경 여부, HTML 구조 변경 여부
- 권장 조치: 원인 확인 후 재수집 또는 parser 수정
```

중요한 점:

- 실패한 수집 결과로 기존 데이터를 덮어쓰지 않는다.
- 이번 주 수집이 실패해도 이전 주 정상 데이터는 유지한다.
- 모델 학습 snapshot은 실패 run을 자동 포함하지 않는다.

### 6.2 일부 상세 수집 실패

예:

- 목록은 성공했지만 일부 상세 URL/API가 실패
- 특정 작품만 404/500
- 요청 제한으로 일부 실패

동작:

```text
1. collector_run.status = partial_success 로 저장
2. 성공 row는 raw에 저장
3. 실패 row는 raw_fetch.error_message에 저장
4. 성공 row만 source_artwork_interpreted_staging 후보로 전달
5. 실패율이 기준 이하이면 이번 run 사용 가능
6. 실패율이 기준 이상이면 staging 승격 보류
7. 실패율과 실패 URL 요약을 운영자에게 알림
```

권장 기준:

| 조건 | 처리 |
|---|---|
| 상세 실패율 5% 미만 | partial_success, 사용 가능 |
| 상세 실패율 5~20% | `quality_status=blocked`, 운영자 승인 전 자동 반영 보류 |
| 상세 실패율 20% 이상 | failed 취급 |

운영자 알림 요약:

```text
[부분 수집 실패] {source} 상세 수집 일부 실패
- run_id: {run_id}
- 목록 수집: 성공
- 상세 실패율: {detail_failed_rate}%
- 실패 row: {failed_detail_rows}/{total_detail_rows}
- 대표 실패 URL: {sample_failed_urls}
- 자동 조치: 성공 row만 raw 저장, 실패 row는 error_message 저장
- snapshot 처리: 실패율 기준에 따라 사용 가능/보류/failed 처리
- 운영자 확인: 요청 제한, 404/500 증가, 특정 URL 패턴 실패 여부
```

### 6.3 원천별 분해/정리 실패

예:

- 한 컬럼에 여러 값이 섞여 있는데 분리 규칙이 없음
- 가격 문구와 판매상태 문구가 같이 들어와 분리 실패
- 크기 표기가 `Image / Frame`처럼 여러 기준으로 들어왔는데 어느 값을 쓸지 불명확
- 같은 의미의 재료명이 사이트별로 다르게 들어왔지만 재료 매핑 config에 없음
- 작가명이 다른 위치로 이동하거나 UI 문구가 섞임
- 작가 소개문/전시 이력/갤러리명이 한 본문에 섞였는데 분리 규칙이 없음
- 같은 이름의 작가가 여러 명인데 생년/국적/활동지 정보가 부족함

동작:

```text
1. raw 수집본은 보존
2. source_artwork_interpreted_staging 또는 source_artist_interpreted_staging에 실패 플래그 저장
3. 해당 row는 normalized_artwork_staging 또는 normalized_artist_staging으로 넘기지 않음
4. 분해 규칙 또는 alias table 수정
5. raw에서 다시 분해/정리 후 표준화 가능
6. 실패 유형과 예시 row를 운영자에게 알림
```

이 구조가 중요한 이유는 raw를 다시 수집하지 않고도, 사이트별 분해 규칙만 고쳐 재처리할 수 있기 때문이다.

운영자 알림 요약:

```text
[분해/정리 실패] {source} 원천별 staging 생성 중 일부 row 실패
- run_id: {run_id}
- 실패 row: 작품 {failed_artwork_rows}, 작가 {failed_artist_rows}
- 주요 실패 유형: 가격/크기/재료/작가명/작가 이력 분해 실패
- 대표 원문: {sample_raw_values}
- 자동 조치: raw는 보존, 실패 row는 normalized로 넘기지 않음
- 운영자 확인: 새 가격 문구, 새 크기 표기, unmapped 재료명, UI 문구 혼입 여부
- 권장 조치: parser 규칙 또는 재료 매핑 config 보강 후 raw에서 재처리
```

### 6.4 공통 표준화 실패

예:

- 분해된 가격 후보는 있지만 통화 확정이 안 됨
- 크기 후보가 여러 개라 공통 `width_cm`, `height_cm`를 확정할 수 없음
- 판매상태 후보가 공통 상태값으로 매핑되지 않음
- 재료 후보가 공통 재료 분류로 매핑되지 않음
- 작가 국적/생년/활동지 후보가 공통 작가 메타 컬럼으로 매핑되지 않음
- 작가 identity 후보가 동명이인 위험 때문에 자동 확정 불가

동작:

```text
1. source_artwork_interpreted_staging / source_artist_interpreted_staging row는 보존
2. normalized_artwork_staging / normalized_artist_staging에는 실패 플래그 저장 또는 생성 보류
3. 해당 row는 학습 snapshot export 대상에서 제외
4. 공통 표준화 규칙 수정 후 interpreted staging에서 재표준화 가능
5. 실패 컬럼과 대표 값을 운영자에게 알림
```

운영자 알림 요약:

```text
[표준화 실패] {source} 공통 컬럼 변환 실패
- run_id: {run_id}
- 실패 row: 작품 {failed_artwork_rows}, 작가 {failed_artist_rows}
- 실패 컬럼: {failed_columns}
- 대표 값: {sample_candidate_values}
- 자동 조치: normalized 생성 보류 또는 실패 플래그 저장, 학습 snapshot 반영 제외
- 운영자 확인: 통화 확정, cm 크기 확정, 판매상태 매핑, 재료 분류, 작가 identity 위험 여부
- 권장 조치: 표준화 규칙 보강 후 interpreted staging에서 재표준화
```

### 6.5 품질 기준 미달

예:

- 전주 대비 수집 건수 30% 이상 감소
- 가격 보유율 기준 미달
- 크기 파싱 성공률 기준 미달
- 중복률 기준 초과

동작:

```text
1. run은 success일 수 있지만 quality_status = warning 또는 blocked
2. warning은 운영자 알림을 보내되, 필수 row 품질이 유지되면 snapshot 반영 가능
3. blocked는 학습 snapshot 자동 반영 중단. 운영자 승인 시 `override_reason` 기록 후 반영 가능
4. warning run은 필수 row만 자동 반영하고, 운영자가 run 요약 확인 후 필요 시 보류/회수한다. 보류/회수/확인 이력은 `collector_run.approved_by`/`approved_at`/`approval_note`/`override_reason`에 기록
5. 품질 기준 미달 요약을 운영자에게 알림
6. `quality_status`는 `collector_run.quality_status` 컬럼에 저장하고, 위반 지표 요약은 `quality_flags_json`에 남긴다
```

운영자 알림 요약:

```text
[품질 기준 미달] {source} 수집은 완료됐지만 품질 기준 미달
- run_id: {run_id}
- quality_status: warning 또는 blocked
- 주요 지표: raw row, normalized row, 가격 보유율, 크기 파싱 성공률, 중복률
- 전주 대비 변화: {week_over_week_delta}
- 자동 조치: warning은 운영자 확인 대상으로 표시, blocked는 학습 snapshot 자동 반영 중단
- 운영자 확인: 사이트 데이터 자체 변화인지, parser 문제인지, source 구조 변경인지 확인
- 권장 조치: 승인 후 반영, 보류, 또는 parser/정규화 규칙 수정 후 재처리
```

품질 경고/차단 기준:

| 조건 | 기준 | 처리 |
|---|---|---|
| 수집 건수 급감 | 직전 정상 run 대비 raw 작품 row가 30% 이상 감소 | `quality_status=warning`, 원천 변경/수집 누락 확인 |
| 수집 건수 급증 | 직전 정상 run 대비 raw 작품 row가 50% 이상 증가 | `quality_status=warning`, 중복/페이지네이션 오류 확인 |
| 가격 보유율 급락 | 직전 정상 run 대비 가격 숫자 보유율이 10%p 이상 감소 | `quality_status=warning`, 가격 parser 확인 |
| 가격 보유율 절대 미달 | 가격 숫자 보유율이 20% 미만 | `quality_status=blocked`, snapshot 자동 반영 금지 |
| 크기 파싱 성공률 미달 | 가로/세로 cm 추출 성공률이 90% 미만 | `quality_status=warning`, 크기 parser 확인 |
| 상세 실패율 초과 | 상세 실패율이 5% 이상 | `partial_success`, 운영자 확인 후 반영 여부 결정 |
| 상세 실패율 차단 | 상세 실패율이 20% 이상 | `failed`, 해당 source snapshot 반영 금지 |
| 중복률 기준 초과 | 같은 `source_artwork_id` 중복률이 5% 이상이거나 직전 정상 run 대비 2배 이상 | `quality_status=warning`, upsert/key 추출 확인 |
| parser error 증가 | parser error row가 전체 row의 1% 이상이거나 직전 정상 run 대비 2배 이상 | `quality_status=warning`, parser regression 확인 |

운영 적용 원칙:

- `warning`은 자동 폐기 조건이 아니다. 필수 컬럼이 있는 row만 snapshot 후보로 넘기고, 운영자가 run 요약을 확인한다.
- `blocked`와 `failed`만 snapshot 자동 반영을 막는다. `blocked`는 운영자 승인(`override_reason`)으로 해제 가능하고, `failed`는 재수집 전까지 반영하지 않는다.
- 초기 2~4주 동안은 기준값을 고정 결론으로 보지 않고, 원천별 정상 변동폭을 쌓은 뒤 조정한다.

## 7. 사이트별로 다른 수집 결과를 어떻게 평준화하는가

핵심은 원천 데이터를 바로 하나의 데이터셋으로 섞지 않는 것이다.

또 하나의 원칙은 추측성 보완을 하지 않는 것이다. 원천에 없는 값을 가격 문구, 작가명, 작품명, 과거 데이터만 보고 임의로 채우면 이후 학습 데이터가 오염된다. 공통 컬럼으로 확정할 수 없는 값은 비워 두고, 후보값과 검수 사유를 남긴다.

다음 4단계로 나눈다.

```text
1. source_artwork_raw
   - 사이트별 원천 구조 보존

2. source_artist_raw
   - 사이트별 작가 원천 구조 보존

3. source_artwork_interpreted_staging / source_artist_interpreted_staging
   - 사이트별 값 분해/정리
   - 한 컬럼에 섞인 값 분리
   - 같은 의미의 다른 명칭을 후보 표준명으로 매핑

4. normalized_artwork_staging / normalized_artist_staging
   - 공통 컬럼으로 변환
   - 공통 단위/상태/재료 분류 적용
   - 공통 작가 메타 컬럼 생성
   - 확정 불가 값은 공통 컬럼에 넣지 않고 quality_flags_json에 사유 기록

5. artist_name_alias
   - 작가명 한글화/영문화 후보 생성
   - 서비스 표시용 한글명과 매칭용 영문/한글 alias 검수
   - 자동 변환명은 단독으로 artist_key 확정에 사용하지 않음

6. artist_identity_candidate
   - 같은 alias 또는 승인 alias에 연결된 기존 artist_key 후보가 있을 때만 검수 후보 생성
   - 기존 후보가 없으면 이 단계를 건너뛰고 신규 artist_key 후보로 둠

7. artwork_snapshot / snapshot export
   - 학습에 넣을 row만 고정
```

### 7.1 원천별 분해/정리 단계

이 단계는 표준화 전의 완충 단계다.

raw에서 바로 `normalized_artwork_staging`으로 가지 않는 이유:

- 사이트마다 같은 의미를 다른 이름으로 부른다.
- 한 컬럼에 여러 의미가 섞여 들어오는 경우가 있다.
- 크기, 가격, 재료, 판매상태는 원천 문구를 분해해야 공통 기준으로 맞출 수 있다.
- 분해 실패와 표준화 실패를 구분해야 운영자가 원인을 빠르게 찾을 수 있다.

예시:

| 원천 | raw 값 | 분해/정리 결과 |
|---|---|---|
| Print Bakery | `size = "Image 29.7x21cm / Frame 38.6x38.6cm"` | 작품 크기 후보와 액자 크기 후보를 분리 |
| Print Bakery | `price_content = "구매 별도 문의"` | 가격 숫자 없음, 판매상태 후보 `price_on_request` |
| Art1 | `size_text = "60.6x72.7cm | 20호"` | cm 크기와 호수 표시를 분리 |
| Art1 | `price_text = "₩ 500,000 - 판매완료"` | 가격 숫자와 판매완료 상태를 분리 |
| Artsy | `price_raw = "US$2,045.00"` | 통화 USD와 숫자 2045를 분리 |
| Saatchi | `mediums = "Oil, Canvas"` | 재료 후보와 지지체 후보를 분리 |

이 단계의 산출물은 아직 최종 공통 컬럼이 아니다. `title_candidate`, `artist_name_candidate`, `width_cm_candidate`, `medium_text_candidate`, `availability_candidate`처럼 후보값을 만든다.

표준화가 안 된 값은 아래처럼 처리한다.

| 경우 | 운영 처리 |
|---|---|
| 사이트 고유 정보 | `metadata_json`에 원천 필드명과 원천 값을 보존 |
| 분해는 됐지만 공통 컬럼 확정 불가 | 후보 컬럼과 `quality_flags_json`에 남김 |
| 재료/상태/카테고리 매핑 실패 | `unmapped` 목록에 남기고 정규화 config 보강 대상으로 표시 |
| 원천 값이 없음 | 빈 값으로 유지 |
| 외부 보강이 필요함 | 별도 enrichment 단계로 분리하고 운영자 승인 전 학습 반영 금지 |

작품/작가 부가 정보는 저장 위치를 분리한다.

| 구분 | 저장 위치 | 운영 판단 |
|---|---|---|
| 작품 부가 정보 | `source_artwork_raw.metadata_json` | 작품 단위 검수 대상 |
| 작가 부가 정보 | `source_artist_raw.metadata_json` | 작가 identity/메타 검수 대상 |
| 작품/작가가 섞인 원문 | raw에 원문 보존 후 interpreted staging에서 후보 분리 | 확정 전 학습 반영 금지 |

예를 들어 Print Bakery의 description에 작품 설명과 작가 소개가 함께 있으면, raw에는 원문 전체를 보존한다. 이후 `source_artwork_interpreted_staging`에서는 `artwork_description_candidate`를 만들고, `source_artist_interpreted_staging`에서는 `artist_bio_candidate`(SoT 컬럼명 `bio_text_candidate`)를 만든다. 분리 기준이 불확실하면 두 후보 모두 확정하지 않고 `quality_flags_json`에 검수 필요 사유를 남긴다.

금지하는 처리:

- 이름을 보고 국적/성별/생년을 자동 추정
- 작품명이나 설명을 보고 제작연도 자동 생성
- 비슷한 재료명이라는 이유로 mapping table에 없는 값을 임의 분류
- 가격 문의 작품에 임의 가격 입력
- 액자 크기만 있을 때 작품 크기처럼 저장
- 다른 원천의 작가 정보로 자동 덮어쓰기

### 7.2 공통 컬럼 기준

4개 사이트가 모두 최종적으로 맞춰야 할 기준 컬럼(운영 참조 부분집합. 전체 공통 컬럼은 [MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md)의 `normalized_*_staging`을 따른다):

| 공통 컬럼 | 설명 |
|---|---|
| `source` | 데이터 출처 |
| `source_artwork_id` | 원천 작품 ID |
| `source_artwork_url` | 원천 작품 URL |
| `title` | 작품명 |
| `artist_name` | 작가명 |
| `artist_source_id` | 원천 작가 ID/slug |
| `price_raw` | 원천 가격 문자열 |
| `price_currency` | 통화 |
| `price_amount` | 통화 기준 숫자 가격 |
| `price_krw_source` | 원천 KRW 가격 |
| `width_cm` | 가로 cm |
| `height_cm` | 세로 cm |
| `depth_cm` | 깊이 cm |
| `medium_raw` | 원천 재료/매체 |
| `medium_category_candidate` | 재료 분류 후보 |
| `availability` | 판매중/판매완료/문의 등 |
| `image_url` | 이미지 URL |
| `artwork_year` | 제작연도 |
| `metadata_json` | 사이트별 작품 추가 정보 |

### 7.3 가격 평준화

가격은 다음처럼 분리한다.

```text
price_raw
  - 사이트에 표시된 원문
  - 예: "₩500,000", "US$2,045.00", "구매 별도 문의", "SOLD"

price_currency
  - KRW, USD, EUR 등 원천 통화

price_amount
  - 원천 통화 기준 숫자
  - USD 2,045이면 2045
  - KRW 500,000이면 500000

price_krw_source
  - 원천이 실제 KRW로 제공한 경우만 저장
  - 고정 환율로 임의 변환한 값은 저장하지 않음
```

중요:

- raw 수집 단계에서 외화를 원화로 변환하지 않는다.
- 환율 변환은 별도 단계에서 기준일 환율과 함께 수행한다.
- 학습용 단일 통화(KRW) 환산은 snapshot export 직전 `price_conversion` 단계에서 `fx_rate_daily` 기준으로 수행하고, 결과는 `price_krw_normalized`로 둔다. 원천이 직접 KRW를 제공한 `price_krw_source`는 환산하지 않고 그대로 사용한다. 자세한 설계는 [MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md)의 `fx_rate_daily`/`price_conversion`을 따른다.
- 가격 문의/판매완료/가격 없음은 가격 숫자와 구분한다.

### 7.4 크기 평준화

사이트별 크기 표기가 다르므로 원문과 파싱값을 모두 저장한다.

```text
dimensions_raw = "60.6x72.7cm | 20호"
width_cm = 60.6
height_cm = 72.7
depth_cm = null
area_cm2 = width_cm * height_cm
```

원칙:

- cm 기준으로 통일한다.
- 호수는 표시/보조 정보로만 저장한다.
- 면적 계산은 표준화 단계에서 수행한다.
- 깊이가 있으면 입체 후보로 플래그를 둔다.

### 7.5 재료/매체 평준화

재료는 원문을 보존하고, 별도 재료 매핑 config(정규화 config)로 분류 후보를 만든다.

예:

```text
medium_raw = "Oil on canvas"
medium_category_candidate = "painting"
support_text_candidate = "canvas"
```

주의:

- 원천의 재료명을 삭제하지 않는다.
- 자동 분류가 실패하면 `quality_flags_json.unmapped_medium`으로 남긴다.
- 학습 반영 전에는 unmapped 목록을 사람이 검토한다.

### 7.6 작가 평준화

작가는 이름만으로 바로 최종 artist_key로 확정하지 않는다. 먼저 `source + artist_source_id`로 기존 연결을 확인하고, 기존 연결이 없을 때만 alias 기반 기존 artist_key 후보를 찾는다. 같은 alias 또는 승인 alias에 연결된 후보가 있을 때 동명이인 가능성과 기존 artist_key 연결 가능성을 검토한다.

작가명 보강, alias, 동명이인 검수, 최종 `artist_key` 확정의 전체 순서도는 [artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md)을 기준으로 한다. 이 섹션은 운영자가 주기 수집 결과를 볼 때 확인해야 할 요약이다.

운영 문서에서 확인할 핵심은 아래 네 가지다.

- 같은 이름의 동명이인이 있을 수 있다.
- 영문/한글 표기가 다를 수 있다.
- 플랫폼별 작가 ID가 서로 다르다.
- 잘못 병합하면 서로 다른 작가의 가격 이력이 섞인다.

운영 화면은 아래 상태를 분리해서 보여줘야 한다.

| 운영 상태 | 운영자가 확인할 내용 |
|---|---|
| 이름 보강 필요 | 한글명/영문명 후보와 원천값 구분 |
| 동명이인 위험 | 같은 alias가 여러 후보에 걸리는지 |
| identity 검수 대기 | 기존 artist_key 연결 후보의 근거와 충돌 사유 |
| 확정/반려 이력 | 승인자, 승인시각, 승인메모, 반려사유 |

운영 판단 기준:

| 운영 상태 | 처리 |
|---|---|
| 같은 원천 ID 기존 연결 | 같은 `source + artist_source_id`에 이미 `artist_key`가 있으면 점수 계산 없이 해당 `artist_key`에 연결 |
| `auto_approved` | [artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md)의 자동 확정 가능 조건을 만족하면 해당 후보 `artist_key`에 연결하고, 자동 확정 시각과 규칙 버전을 기록한다. 서로 다른 원천 간 자동 확정은 이름 alias 일치와 고신뢰 생년 일치가 모두 필요. **MVP에서는 cross-source 자동 확정을 끄고 same-source 연결만 자동 처리하며, cross-source 후보는 전부 수동 검수 큐로 보낸다(자동 확정은 post-MVP).** |
| 신규 `artist_key` 생성 후보 | `source + artist_source_id`가 있고 해당 조합에 연결된 기존 `artist_key`가 없으면 신규 생성 후보로 둠. `artist_source_id`가 없으면 cross-source 신규 생성 조건([artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md) 6.1 신규 artist_key 후보 기준)을 만족할 때만 생성 후보로 둠 |
| `needs_review` | 기존 artist_key 연결 후보가 있으나 alias만 일치하고 고신뢰 생년을 확인할 수 없거나, fuzzy alias만 있거나, 국적/활동지 같은 참고 메타만 있는 경우 artist_key에 바로 연결하지 않고 운영자 검수 큐로 이동 |
| `match_rejected` | 강한 충돌 조건이 있고 운영자가 반려했거나, 기존 승인 이력과 직접 충돌하는 경우 해당 후보 artist_key와의 연결만 금지하고 반려 관리자/시각/사유를 남김. 원천 row는 유지하며 다른 후보 비교 또는 신규 artist_key 후보 처리는 계속 가능 |

운영자 검수 화면에는 최소 아래 정보가 필요하다.

- 후보 그룹 안의 원천 사이트 목록
- 각 원천의 `artist_source_id`, 작가 페이지 URL
- 원문 작가명, 한글명, 영문명, 정규화명
- 생년, 생년 추출 신뢰도, 국적, 활동지
- 작가 소개문, 학력
- 대표 작품 매체와 가격대
- 자동 확정 근거 또는 검수 필요 사유
- 충돌 사유
- 수동 승인/반려 버튼
- 승인 또는 반려 관리자 ID
- 승인 또는 반려 시각
- 승인 메모 또는 반려 사유

운영 원칙:

- 이름만 같다고 자동 병합하지 않는다.
- 자동 확정/반려 기준을 충족하지 못하면 분리 상태로 두고 수동 검수한다.
- 잘못 병합하는 것이 잠시 분리해 두는 것보다 위험하다.
- 검수 승인/반려는 현재 상태(승인자/시각/사유, 반려자/시각/사유)로 남긴다. 변경 전체를 남기는 audit 이력 테이블은 post-MVP다.

### 7.7 판매상태 평준화

사이트별 표현을 공통 상태로 바꾼다.

| 원천 표현 | 공통 상태 |
|---|---|
| 판매중, for sale, selling=T | `available` |
| SOLD, 판매완료, sold_out=T | `sold` |
| 구매 별도 문의, price on request | `price_on_request` |
| 가격 없음 | `missing_price` |
| 비공개/삭제 | `unavailable` |

## 8. 학습 snapshot 반영 기준

수집된 모든 row를 바로 학습에 넣지 않는다.

먼저 run 단위 반영 규칙(`status` × `quality_status`)을 적용하고, 통과한 run 안에서만 row 단위 필수/보류 조건을 적용한다.

| `status` | `quality_status` | snapshot 자동 반영 |
|---|---|---|
| `success` / `partial_success` | `ok` | 반영. 필수 조건 통과 row만 |
| `success` / `partial_success` | `warning` | 필수 조건 통과 row만 자동 반영. 운영자가 run 요약을 확인하고 필요 시 보류/회수. 보류/회수/확인 이력은 `collector_run.approved_*`에 기록 |
| any | `blocked` | 자동 반영 금지. 운영자 승인 시에만 반영하고 `override_reason` 기록 |
| `failed` | any | 자동 반영 금지 |

여기서 `warning`은 자동 반영을 막지 않는 soft 상태(필수 row는 자동 반영하고 운영자가 사후 확인)이고, `blocked`는 운영자 승인 전 자동 반영을 막는 pre-gate다.

`partial_success`의 상세 실패율 처리는 6.2를 따른다. 5% 미만은 `quality_status=ok`로 자동 반영, 5~20%는 `quality_status=blocked`로 두어 운영자 승인 전 자동 반영을 막고, 20% 이상은 `failed`로 처리한다.

학습 snapshot export 대상에 들어가려면 최소 조건을 통과해야 한다.

필수 조건:

- 작가명 있음
- 작품명 있음
- 가격 숫자 있음
- 학습용 단일 통화 가격(price_krw_normalized) 확정됨
- 가로/세로 cm 있음
- `is_3d_candidate=false`이고, `medium_category_candidate`가 `sculpture`, `installation`, `video`, `film`, `animation`, `mixed_media`가 아님
- placeholder 가격 목록에 없음
- 중복 제거 기준 통과

보류 조건:

- 기존 artist_key 연결 후보가 있는데 `alias_exact`/`alias_approved`가 아니고 `alias_fuzzy_only`만 있는 경우
- 재료 분류 실패
- 환율 데이터 없음 등으로 학습용 단일 통화 가격(price_krw_normalized)을 확정하지 못함
- 크기 이상치: `width_cm <= 0`, `height_cm <= 0`, `width_cm > 500`, `height_cm > 500`, `aspect_ratio > 20`, `aspect_ratio < 0.05` 중 하나에 해당. 여기서 `aspect_ratio`는 저장 컬럼이 아니라 snapshot 단계에서 `max(width_cm, height_cm) / min(width_cm, height_cm)`로 계산한 값이다
- 가격이 0 이하이거나, placeholder 가격 목록에 있음
- 동일 source/currency 기준 평가 가능한 가격 row가 100건 이상일 때 p1 미만 또는 p99 초과인 경우
- 동일 작품 중복 후보

placeholder 가격 목록은 원천별로 별도 관리한다. 기본 목록은 `1`, `999999`, `9999999`, `99999999`, `999999999`처럼 실제 판매가보다 임시값일 가능성이 높은 반복 자리수 가격이다.

동일 작품 중복 후보 기준:

- 같은 `source`와 같은 `source_artwork_id`가 2개 이상 존재
- `source_artwork_id`가 없더라도 정규화한 `title + artist_name + width_cm + height_cm + hash(image_url)`가 모두 같음. `hash(image_url)`은 저장 컬럼이 아니라 snapshot 단계 계산값이다

## 9. 운영 알림 기준

크론잡 종료 후 알림에는 아래 내용을 포함한다.

```text
[주간 수집 결과]
기간: 2026-06-24 ~ 2026-06-30

Artsy
- 상태: success
- raw: 00,000건
- normalized: 00,000건
- 신규: 000건
- 가격 없음: 000건
- 경고: 없음

Saatchi
...

Print Bakery
...

Art1
...
```

경고 또는 차단 알림이 필요한 경우:

- 사이트 수집 실패
- 전주 대비 수집량 30% 이상 감소
- 상세 실패율 5% 이상
- 가격 보유율 10%p 이상 감소 또는 20% 미만
- 크기 파싱 성공률 90% 미만
- parser error row 1% 이상 또는 직전 정상 run 대비 2배 이상

## 10. 운영 담당자 확인 화면

운영 담당자는 수집 결과를 코드나 CSV를 열지 않고도 확인할 수 있어야 한다. 관리자 화면이나 주간 리포트에는 최소 아래 항목을 노출한다.

### 10.1 run 단위 요약

| 항목 | 의미 | 조치 기준 |
|---|---|---|
| run 상태 | success / partial_success / failed | failed면 해당 사이트 snapshot 반영 중단 |
| 요청 성공률 | HTTP 요청 중 성공 비율 | 95% 미만이면 상세 로그 확인 |
| raw 작품 row | 원천에서 수집된 작품 수 | 전주 대비 30% 이상 감소하면 경고 |
| raw 작가 row | 원천에서 수집/추출된 작가 수 | 0이면 작가 수집 파이프라인 확인 |
| 표준화 작품 row | normalized까지 통과한 작품 수 | normalized/raw 비율이 직전 정상 run 대비 10%p 이상 감소하거나 70% 미만이면 parser 확인 |
| 표준화 작가 row | normalized까지 통과한 작가 수 | normalized/raw 비율이 직전 정상 run 대비 10%p 이상 감소하거나 70% 미만이면 작가 staging 확인 |
| 가격 보유율 | 가격 숫자가 있는 작품 비율 | 직전 정상 run 대비 10%p 이상 감소하면 경고, 20% 미만이면 차단 검토 |
| 크기 파싱 성공률 | 가로/세로 cm 추출 성공률 | 90% 미만이면 크기 파서 점검 |
| 재료 unmapped 수 | 재료 매핑 config(정규화 config)에 없는 값 | 정규화 config 보강 후보 |
| 이름 alias 검수 대기 수 | 한글명/영문명 보강 수동 확인 필요 건수 | 운영자가 이름 alias 큐에서 처리 |
| 동명이인 alias 수 | 같은 alias가 여러 artist_key 후보에 걸린 건수 | 자동 병합 금지, 운영자가 후보 비교 |
| identity 검수 대기 수 | 작가 매칭 수동 확인 필요 건수 | 운영자가 검수 큐에서 처리 |

### 10.2 실패 시 동작

수집 실패가 발생해도 운영 모델과 기존 학습 snapshot은 바로 바뀌지 않는다.

```text
site collector failed
        |
        v
collector_run.status = failed
        |
        v
raw_fetch에 실패 URL과 error_message 저장
        |
        v
해당 사이트의 staging/normalized 생성 중단
        |
        v
이번 주 학습 snapshot export 자동 반영 제외
        |
        v
운영 알림 발송 및 마지막 정상 snapshot 유지
```

partial_success는 일부 데이터만 수집된 상태다. 상세 실패율이 5% 미만이고 `quality_status`가 `ok`이면 필수 조건 통과 row는 자동 반영된다. 상세 실패율 5~20%는 `quality_status=blocked`로 두어 운영자 승인 전에는 자동 반영하지 않으며, 운영자가 실패 범위·품질을 확인한 뒤 승인(`override_reason` 기록) 또는 반려한다. 20% 이상은 `failed`로 처리한다(8장 반영 규칙).

### 10.3 운영자가 보는 검수 큐

운영 검수 큐는 아래 항목을 우선순위로 보여준다.

1. 가격 숫자와 판매상태가 충돌하는 row
2. 크기 파싱 실패 또는 액자 크기만 있는 row(`size_basis_candidate=frame_inclusive`)
3. 동일 `source_artwork_id`인데 같은 통화 기준 가격이 50% 이상 바뀌었거나 면적이 20% 이상 바뀐 row
4. 작가명은 같지만 생년/국적/활동지가 충돌하는 identity 후보
5. 재료/지지체 unmapped row
6. 가격이 0 이하이거나 placeholder 가격 목록에 있거나, 동일 source/currency 기준 평가 가능한 가격 row가 100건 이상일 때 p1 미만 또는 p99 초과인 row

## 11. 역할별 책임 경계

수집 파이프라인은 여러 직군이 함께 보는 구조이므로, 책임 경계를 아래처럼 둔다.

| 역할 | 주로 보는 항목 | 승인/판단 |
|---|---|---|
| 개발자 | collector 성공률, parser error, schema migration, payload hash, 재실행 안전성 | 코드 배포 가능 여부 |
| 운영 담당자 | run 상태, 사이트별 수집량, 실패 URL, 이름 alias 큐, 동명이인 큐, identity 검수 큐, 알림 | 이번 주 snapshot 반영 가능 여부 |
| 데이터 분석가 | 결측률, 가격/크기/재료 분포, 원천별 편향, unmapped 목록 | 학습 피처 승격 가능 여부 |
| 데이터 관리자 | raw 보존, 데이터 출처 및 처리 이력, 작가 identity 검수 상태, 동명이인 충돌 그룹, 최종 artist_key 승인 이력 | 데이터 자산으로 확정 가능 여부 |

결정 흐름:

```text
개발자
  - 수집/파싱 코드가 정상인지 확인
        |
        v
운영 담당자
  - 이번 run을 사용할 수 있는지 확인
        |
        v
데이터 분석가
  - 학습에 넣어도 되는 품질인지 확인
        |
        v
데이터 관리자
  - 작가 identity와 데이터 출처 및 처리 이력이 관리 가능한지 확인
        |
        v
학습 snapshot export 승인
```

## 12. 검수 큐 운영 부하와 에스컬레이션

자동 처리하지 못한 항목은 운영자 검수 큐로 모인다. 운영 인력을 정하려면 큐에 주당 몇 건이 쌓이는지 가늠해야 한다. 유입량은 **초기 백로그(1회성)**와 **주간 증분(지속)**으로 나눠 본다. 초기 1~2회 수집은 과거 미정리분이 한꺼번에 올라와 크고, 이후 주간 증분은 신규/변경분만이라 훨씬 작다.

### 12.1 큐별 유입량 추정

아래는 2026-06 현재 수집 산출물 기준 초기 추정이다. 실제값은 운영 2~4주 누적 후 보정한다(고정 결론으로 보지 않는다).

| 검수 큐 | 무엇을 보나 | 초기 백로그(개략) | 주간 증분(개략) |
|---|---|---|---|
| 이름 alias 큐 | 한글/영문 보강 `needs_review`(영문명/한글명 누락·자동 변환) | 수백 건(예: Print Bakery 영문명 미보유 약 105건) | 신규 작가 수에 비례, 소량 |
| 동명이인 큐 | 같은 alias가 여러 `artist_key` 후보에 걸림 | 수십 건 | 소량 |
| artist identity 큐 | cross-source 후보(MVP는 전부 `needs_review`) | 정규화 이름 일치쌍 약 110(Artsy-Print Bakery 66, Artsy-Saatchi 37 등) | 신규 작가 등장분만 |
| 작품 검수 큐 | 가격/크기 충돌, 액자만 있는 row, unmapped 재료/상태 | 수십~수백 건(예: Print Bakery frame-only 39건) | 가격/상태 변경분에 비례 |

운영 판단:

- 초기 백로그는 1회성이므로, 런칭 직후 1~2주는 검수 인력을 더 투입해 큐를 비운 뒤 주간 증분 체제로 전환한다.
- 주간 증분이 한 명이 처리 가능한 수준(예: 주당 수십 건)인지를 2~4주 실측으로 확인하고, 초과하면 인력 또는 자동 확정 기준을 조정한다.
- 큐가 계속 쌓이기만 하면(처리량 < 유입량) 자동 확정 기준을 너무 보수적으로 잡은 신호이므로 기준을 재검토한다.

### 12.2 에스컬레이션 SLA

알림과 큐는 방치되면 의미가 없으므로 처리 시한과 담당을 정한다. 아래는 MVP 기본값이며 운영 부하를 보고 조정한다.

| 항목 | 담당 | 처리 시한 | 미처리 시 |
|---|---|---|---|
| 수집 실패 / `blocked` 알림 | 개발자 | 영업일 1일 내 확인 | 다음 주 수집까지 마지막 정상 snapshot 유지 |
| `partial_success`(보류 구간) 검토 | 운영 담당자 | 영업일 2일 내 반영/보류 결정 | 기본 보류, 자동 반영 안 함 |
| 이름 alias / 동명이인 / identity 검수 큐 | 운영 담당자 | 주 1회 정기 처리(수집 주기와 동기) | 미처리분은 다음 주로 이월, 큐 적체 지표로 추적 |
| 작품 검수 큐(가격/크기/unmapped) | 데이터 분석가 + 운영 담당자 | 주 1회 | 해당 row는 학습 snapshot 보류 유지 |
| 개인정보 / 삭제 요청 | 별도 정책(정식 런칭 전 수립) | 별도 정책 | MVP 범위 외, 정식 런칭 전 정책 필요 |

원칙:

- 큐 적체량(유입 − 처리)을 주간 리포트에 함께 노출해, 적체가 늘면 인력 또는 기준을 조정한다.
- 검수 미처리는 데이터 손실이 아니라 "반영 보류"다. 미처리분은 raw/staging에 남고 다음 주에 다시 검토된다.

## 13. 정리

이 구조에서 역할은 명확하다.

```text
크롤러
  - 원천 데이터를 가져온다.
  - 원본 응답을 보존한다.

MySQL raw
  - 언제, 어디서, 어떤 응답을 받았는지 저장한다.

표준화 staging
  - 사이트별로 다른 작품 데이터를 같은 컬럼으로 맞춘다.
  - 사이트별로 다른 작가 메타를 같은 컬럼으로 맞춘다.

작가 identity 후보
  - 이름만으로 작가를 확정하지 않는다.
  - 먼저 source + artist_source_id 기존 연결을 확인한다.
  - 같은 alias 또는 승인 alias에 연결된 기존 후보가 있을 때만 동명이인 가능성과 기존 artist_key 연결 가능성을 검토한다.

품질 점검
  - 이번 주 수집 결과를 사용할 수 있는지 판단한다.

학습 snapshot export
  - 모델 학습에 실제로 사용할 데이터를 고정한다.
```

따라서 1차 수집이 실패해도 기존 학습 데이터나 운영 모델이 바로 오염되지 않는다. 또한 사이트별 데이터 구조가 달라도 raw 보존 후 staging에서 작품 컬럼과 작가 컬럼을 각각 공통 기준으로 맞추기 때문에, Artsy / Saatchi / Print Bakery / Art1 데이터를 같은 학습 snapshot export 대상으로 관리할 수 있다.
