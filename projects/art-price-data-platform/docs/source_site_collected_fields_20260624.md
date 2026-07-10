# 4개 원천 사이트별 수집 항목 정리

작성일: 2026-06-24

대상:

- Artsy
- Saatchi
- Print Bakery
- Art1

목적:

- 각 사이트에서 수집되는 원천 데이터 항목을 명확히 정리한다.
- 사이트별 수집 결과가 서로 다르더라도 어떤 값을 공통 스키마로 옮길 수 있는지 확인한다.
- MySQL raw 적재 및 표준화 staging 설계의 기준 문서로 사용한다.

관련 문서:

- [데이터 수집 서비스 시나리오](data_collection_service_scenarios_20260625.md)
- [사용자 / 어드민 화면 구조 및 기능 기획](user_admin_screen_structure_plan_20260625.md)
- [사용자 / 어드민 API 기획](user_admin_api_plan_20260625.md)
- [주기 수집 운영 문서](weekly_crawler_mysql_operation_plan_20260624.md)
- [artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md)
- [4개 원천 사이트 주기 수집 및 MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md)

## 문서 세트에서의 위치

데이터 수집 문서는 아래 순서로 읽는 것을 기준으로 한다.

1. [데이터 수집 서비스 시나리오](data_collection_service_scenarios_20260625.md)
   - 사용자/어드민/수집 job이 어떤 상황에서 어떻게 동작하는지 설명한다.
2. [사용자 / 어드민 화면 구조 및 기능 기획](user_admin_screen_structure_plan_20260625.md)
   - 수집/검수 데이터를 화면에서 어떻게 보여줄지 설명한다.
3. [사용자 / 어드민 API 기획](user_admin_api_plan_20260625.md)
   - 수집/검수 데이터를 화면에 제공하는 API를 설명한다.
4. [주기 수집 운영 문서](weekly_crawler_mysql_operation_plan_20260624.md)
   - 수집 실행, 실패 처리, 운영자 알림, snapshot 반영 기준을 설명한다.
5. [artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md)
   - 작가명 한글화/영문화, alias, 동명이인, 최종 artist_key 생성 기준을 설명한다.
6. [원천 사이트별 수집 항목 정리](source_site_collected_fields_20260624.md)
   - 각 원천에서 어떤 작품/작가 값을 수집하고, 어떤 공통 컬럼으로 옮기는지 설명한다.
7. [MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md)
   - DB 구조, job 구조, migration, 테스트 기준을 설명한다.

이 문서는 데이터 항목과 표준화 기준을 담당한다. 운영 실패 처리나 DB migration보다, 각 원천 데이터가 어떤 의미를 갖고 어떤 컬럼으로 이동하는지에 집중한다. 작가명 표시값과 `artist_key` 생성 흐름은 별도 문서인 [artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md)을 기준으로 한다.

문서 내부 흐름:

```text
공통 수집 원칙
  -> 원천별 수집 방식 요약
  -> 사이트별 작품/작가 수집 항목
  -> 작가 정보 분해/정리 staging 기준
  -> 작품 정보 분해/정리 staging 기준
  -> 공통 표준화 매핑
  -> 학습에 바로 쓰지 않는 항목
  -> 데이터 분석/관리 검토 기준
```

## 1. 공통 수집 원칙

4개 사이트는 데이터 구조가 다르므로, 처음부터 하나의 컬럼 구조로 강제로 맞추지 않는다.

수집 단계에서는 다음을 우선한다.

- 원천 ID를 보존한다.
- 원천 URL을 보존한다.
- 가격 원문과 숫자 가격을 분리한다.
- 통화 정보를 원천 그대로 보존한다.
- 작품명/작가명/크기/재료/판매상태를 원문 기준으로 저장한다.
- 원천별 추가 정보는 `metadata_json`에 보존한다.
- 표준화는 raw 저장 후 바로 수행하지 않고, 원천별 분해/정리 staging을 거친 뒤 수행한다.
- 표준화할 수 없는 값은 억지로 공통 컬럼에 넣지 않고 `metadata_json`, `parsed_parts_json`, `quality_flags_json`(매핑 실패는 `unmapped_*` 키)에 남긴다.
- 원천에 없는 값을 추측해서 채우지 않는다.
- CSV는 최초 원천 보존 포맷으로 쓰지 않는다. 원천 응답은 원래 형식 그대로 보존하고, CSV는 검수/공유가 필요할 때 export한다.

용어는 아래처럼 통일한다.

- `source_*_raw`: 원천 응답과 원천 필드를 최대한 그대로 보존한 테이블
- `source_*_interpreted_staging`: 한 컬럼에 섞인 값을 분해하고, 같은 의미의 다른 명칭을 정리한 중간 테이블
- `normalized_*_staging`: 공통 컬럼/단위/상태값으로 맞춘 1차 표준화 테이블
- `artist_source_id`: 각 원천 사이트 안에서만 의미가 있는 작가 ID/slug
- `normalized_artist_id_candidate`: 기존 artist_key 연결 후보 또는 신규 작가 후보를 검토할 때 쓰는 내부 후보 ID
- `artist_key`: 운영자 검수를 거쳐 데이터 관리자가 승인/확정한 뒤 모델과 서비스에서 사용할 최종 작가 키
- `학습 snapshot export`: 품질 점검을 통과한 row를 특정 시점 기준으로 고정해 parquet로 내보내고, 운영자 검수, 외부 공유, 기존 CSV 기반 코드 호환 목적일 때만 CSV를 추가 생성하는 단계

추측성 보완 금지 원칙:

- 원천에 없는 국적, 생년, 성별, 갤러리, 전시 이력, 재료, 지지체, 제작연도는 자동으로 채우지 않는다.
- 이름, 작품명, 재료명, 가격 문구를 보고 다른 값을 추정하지 않는다.
- 외부 지식이나 과거 데이터로 보완이 필요하면 별도 보강 단계로 분리하고, `value_source`, `confidence`, `reviewer`, `review_status`를 남긴다.
- 자동 분류나 파서 결과가 `confidence=high`가 아닌 값은 `candidate` 또는 `unmapped`로 남기고, 학습 snapshot export 대상에서는 제외하거나 검수 대기 상태로 둔다.

가격 라벨 의미 고정 원칙:

가격 표준 컬럼에는 가격의 의미를 명시하는 컬럼을 함께 둔다. 같은 `price_amount`라도 판매 호가/낙찰가/추정가는 의미가 다르므로, 라벨을 고정하지 않으면 학습 타깃이 섞인다.

- `price_type`: 가격 라벨. 값 집합은 `retail_ask`(판매 호가), `auction_hammer`(경매 낙찰가), `estimate`(추정가)다. **현재 4개 원천(Artsy/Saatchi/Print Bakery/Art1)은 전부 `retail_ask`(판매 호가)로 고정한다.** Art1 판매완료(`is_sold`) row의 가격도 "거래 체결가"가 아니라 "판매 당시 호가"이므로 `auction_hammer`나 체결가로 해석하지 않고 `retail_ask`로 둔다.
- `price_tax_basis`: 세금/수수료 포함 여부. 값 집합은 `tax_incl`(포함), `tax_excl`(미포함), `unknown`(원천별 포함 여부 불명). 현재 4개 원천은 세금·수수료 포함 여부를 신뢰 가능하게 알 수 없으므로 대부분 `unknown`으로 둔다. 원천이 명시적으로 표기한 경우에만 `tax_incl`/`tax_excl`로 채운다.

가격 신뢰 가정(가격예측 트랙 한계):

> 본 트랙은 원천에서 수집되는 가격을 해당 작품의 가격으로 신뢰하고 사용한다. 원천 가격의 진위/일관성 검증은 본 트랙 범위 밖이며, `price_type=retail_ask` 가정 하에 학습 라벨로 사용한다. 즉 모델 타깃은 "원천에 표기된 판매 호가"이지 "실제 거래 체결가"가 아니다.

원천 저장 포맷 원칙:

- API 응답은 원본 JSON으로 보존한다.
- HTML 페이지는 원본 HTML로 보존한다.
- 원천에서 CSV export를 제공한 경우에만 원본 CSV를 그대로 보존한다.
- row 단위 raw 파싱 결과는 JSONL 또는 MySQL raw 테이블에 저장한다.
- CSV는 원천 보존용이 아니라 외부 공유, 수동 검수, 제출, 기존 실험 코드 호환을 위한 export 포맷으로 둔다.

작품/작가 부가 정보 분리 원칙:

- 작품 부가 정보는 `source_artwork_raw.metadata_json`에 저장한다.
- 작가 부가 정보는 `source_artist_raw.metadata_json`에 저장한다.
- 작품과 작가 정보가 한 원문에 섞여 있으면 raw에는 원문 전체를 보존하고, interpreted staging에서 `artwork_description_candidate`, `artist_bio_candidate`처럼 후보로 분리한다.
- 분리 기준이 불확실하면 확정 컬럼에 넣지 않고 `quality_flags_json`에 검수 필요 사유를 남긴다.

권장 흐름:

```text
source raw
  - 원천 응답과 원천 필드 보존
        |
        v
source interpreted staging
  - 한 컬럼에 섞인 값 분해
  - 같은 의미의 다른 명칭 정리
  - 표준화에 쓸 후보값 생성
        |
        v
normalized staging
  - 공통 컬럼/공통 단위/공통 상태값으로 변환
```

작가 정보도 같은 원칙을 따른다.

```text
source_artist_raw
  - 원천 작가 ID, 이름, 국적, 이력, 갤러리/전시/프로필 원문 보존
        |
        v
source_artist_interpreted_staging
  - 이름 분해/정리
  - 국적/출생연도/활동지/전시 이력 후보값 생성
  - artist_key 연결에 참고할 이름/메타 후보값 생성
        |
        v
normalized_artist_staging
  - 공통 작가 메타 컬럼으로 변환
        |
        v
artist_name_alias
  - 한글명/영문명 후보를 검수하고 표시명과 매칭용 alias 확정
        |
        v
artist_identity_candidate
  - 같은 alias 또는 승인 alias에 연결된 기존 artist_key 후보가 있을 때만 검수 후보 생성
  - 기존 후보가 없으면 신규 작가 후보 큐로 둠
        |
        v
artist_identity
  - 자동 확정 또는 데이터 관리자 승인 후 서비스 공통 artist_key 부여
```

## 2. 원천별 수집 방식 요약

| 사이트 | 수집 방식 | 주요 원천 ID | 수집 범위 |
|---|---|---|---|
| Artsy | 기존 Artsy 수집/API/export 기반 | artwork id 또는 artwork slug | 작품 정보 + 작가 메타 + 갤러리 정보 |
| Saatchi | 기존 Saatchi 수집/API/export 기반 | artwork id 또는 artwork URL/slug | 작품 정보 + 작가 메타 |
| Print Bakery | Cafe24 JSON API 우선, HTML fallback | `product_no` | 오리지널 평면 카테고리 작품 |
| Art1 | 내부 AJAX endpoint 우선, HTML fallback | `goods_id` | 원화 카테고리 작품 |

## 3. Artsy 수집 항목

Artsy는 작품 CSV와 작가 CSV를 분리해서 다룬다. 작품 row에는 작품 가격/크기/이미지/갤러리 정보가 들어가고, 작가 CSV에서 작가 메타를 보강한다.

### 3.1 작품 정보

| 항목 | 설명 | 표준화 대상 |
|---|---|---|
| artwork id 또는 slug | Artsy 작품 식별자 | `source_artwork_id` |
| artwork title | 작품명 | `title` |
| artwork year | 제작연도 | `artwork_year` |
| artwork URL | 작품 상세 URL | `source_artwork_url` |
| image URL | 대표 이미지 | `image_url` |
| price raw | 원천 가격 문자열 | `price_raw` |
| price currency | 원천 통화 | `price_currency` |
| price amount | 원천 통화 기준 숫자 가격 | `price_amount` |
| width / height / depth | 작품 크기 | `width_cm`, `height_cm`, `depth_cm` |
| dimensions raw | 크기 원문 | `dimensions_raw` |
| medium | 재료/매체 | `medium_raw` |
| category / medium_type | 원천 분류 | `medium_category_candidate` |
| availability / status | 판매상태 | `availability` |
| gallery name | 갤러리명 | `gallery_name` |
| gallery type | 갤러리 유형 | `gallery_type` |
| gallery cities | 갤러리 도시 | `gallery_cities` |

### 3.2 작가 정보

| 항목 | 설명 | 표준화 대상 |
|---|---|---|
| artist slug | Artsy 작가 식별자 | `artist_source_id` |
| artist name | 작가명 | `artist_name` |
| nationality | 국적 | `artist_nationality` |
| birth year | 출생연도 | `artist_birth_year` |
| gender | 성별 | `artist_gender` |
| total works | 등록 작품 수 | `artist_total_works` |
| for sale works | 판매중 작품 수 | `artist_for_sale` |
| followers | 팔로워 수 | `artist_followers` |
| solo count | 개인전 수 | `artist_solo_count` |
| group count | 단체전 수 | `artist_group_count` |
| fair count | 아트페어 수 | `artist_fair_count` |
| total shows | 전체 전시 수 | `artist_total_shows` |
| is_p1 | 작가 중요도/등급 후보 | `artist_is_p1` |
| biography / bio | 작가 소개문이 있는 경우 | `artist_bio` |
| hometown / location | 출생지/활동지 후보 | `location_city_candidate` |
| website / instagram | 외부 링크가 있는 경우 | `artist_website_url`, `artist_instagram_url` |

### 3.3 주의 사항

- Artsy 수집본에 `price_krw`가 있더라도, 고정 환율로 계산된 값이면 raw 단계에서는 사용하지 않는다.
- 원천 통화와 원천 가격 숫자를 우선 보존한다.
- 원화 환산은 별도 환율 정책 단계에서 수행한다.
- `artist_slug`는 Artsy 내부 ID이지 서비스 최종 artist_key가 아니다.

## 4. Saatchi 수집 항목

Saatchi는 작품 정보와 작가 정보를 별도로 수집하고, 작품 row에 작가 ID를 연결한다.

### 4.1 작품 정보

| 항목 | 설명 | 표준화 대상 |
|---|---|---|
| artwork id / URL | Saatchi 작품 식별자 | `source_artwork_id`, `source_artwork_url` |
| title | 작품명 | `title` |
| year | 제작연도 | `artwork_year` |
| image URL | 대표 이미지 | `image_url` |
| price USD | 달러 가격 | `price_amount`, `price_currency=USD` |
| width / height / depth | 작품 크기 | `width_cm`, `height_cm`, `depth_cm` |
| dimensions raw | 크기 원문 | `dimensions_raw` |
| mediums | 재료/매체 | `medium_raw` |
| category | 원천 카테고리 | `medium_category_candidate` |
| subject / style / orientation | 작품 성격 태그 | `metadata_json` 또는 보조 피처 후보 |
| artist id | Saatchi 작가 식별자 | `artist_source_id` |
| artist first/last name | 작가명 구성 요소 | `artist_name` |

### 4.2 작가 정보

| 항목 | 설명 | 표준화 대상 |
|---|---|---|
| artist id | Saatchi 작가 식별자 | `artist_source_id` |
| first name / last name | 작가명 | `artist_name` |
| gender | 성별 | `artist_gender` |
| country / city | 활동 국가/도시 | `artist_location_country`, `artist_location_city` |
| followers | 팔로워 수 | `artist_followers` |
| total artworks | 등록 작품 수 | `artist_total_works` |
| bio | 작가 소개 | `artist_bio` |
| education | 학력 | `artist_education` |
| exhibitions | 전시 이력 | `artist_exhibitions` |
| instagram | 인스타그램 URL | `artist_instagram_url` |
| website | 홈페이지 URL | `artist_website_url` |
| profile URL | Saatchi 작가 페이지 URL | `artist_source_url` |

### 4.3 주의 사항

- Saatchi는 가격이 주로 USD 기준이다.
- raw 수집 단계에서 KRW로 환산하지 않는다.
- `artist_id`는 Saatchi 내부 ID이며 서비스 최종 artist_key가 아니다.
- `category`, `style`, `subject`는 모델 피처 후보가 될 수 있지만 사용자 입력 가능성과 결측률을 별도로 확인해야 한다.

## 5. Print Bakery 수집 항목

Print Bakery는 Cafe24 상품 API를 우선 사용하고, API 실패 또는 필드 누락 시 HTML 상세 파싱을 fallback으로 둔다.

### 5.1 작품 정보

Print Bakery 작품 정보는 Cafe24 상품 API를 1차 기준으로 수집하고, API 실패 또는 필드 누락 시 HTML 목록/상세 파싱 결과를 보완값으로 사용한다.

#### 5.1.1 Cafe24 API 작품 항목

Cafe24 상품 API에서 확인된 주요 필드:

| 항목 | 설명 | 표준화 대상 |
|---|---|---|
| product_no | 상품/작품 식별자 | `source_artwork_id` |
| product_code | Cafe24 상품 코드 | `metadata_json` |
| custom_product_code | 내부 작품 코드 | `metadata_json` |
| product_name | 상품명/작품명 | `title` |
| eng_product_name | 영문 작품명 | `metadata_json` |
| price | 가격 숫자 문자열 | `price_amount`, `price_currency=KRW` |
| price_content | 가격 표시 문구 | `price_raw`, `availability` |
| sold_out | 품절 여부 | `availability` |
| selling | 판매 상태 | `availability` |
| category | 포함 카테고리 목록 | `metadata_json` |
| detail_image | 상세 이미지 | `image_url` |
| list_image | 목록 이미지 | `image_url` |
| product_tag | 상품 태그 | `metadata_json` |
| description | 작품/작가 설명 | `metadata_json` |
| additional_information | 크기/재료 등 상세 정보 후보 | `metadata_json` 및 표준 필드 |

#### 5.1.2 HTML fallback 작품 항목

기존 HTML 파싱에서 확보 가능한 필드:

| 항목 | 설명 | 표준화 대상 |
|---|---|---|
| product_no | 상품/작품 식별자 | `source_artwork_id` |
| artist_list | 목록 작가명 | `artist_name` |
| title_list | 목록 작품명 | `title` |
| price_text_list | 목록 가격 문구 | `price_raw` |
| price_krw_list | 목록 원화 숫자 가격 | `price_amount`, `price_krw_source` |
| detail_url | 상세 URL | `source_artwork_url` |
| image_url_list | 목록 이미지 | `image_url` |
| artwork | 상세 작품명 | `title` |
| artist | 상세 작가명 | `artist_name` |
| price | 상세 가격 | `price_raw`, `price_amount` |
| maker | 제작자/작가 | `artist_name` 후보 |
| size | 크기 원문 | `dimensions_raw`, `width_cm`, `height_cm`, `depth_cm` |
| method | 제작 방식 | `medium_raw` 또는 `metadata_json` |
| material | 재료/연도 등 원천 표기 | `medium_raw` 또는 `metadata_json` |
| edition | 에디션 | `metadata_json` |
| code | 작품/상품 코드 | `metadata_json` |
| meta description | 설명 | `metadata_json` |
| og image | 대표 이미지 | `image_url` |

### 5.2 작가 정보

Print Bakery는 작품 상세만 보면 작가 컬럼이 적다. 다만 별도 아티스트 목록/상세 페이지가 있으므로 작가 수집을 작품 수집과 분리하면 더 많은 작가 메타를 얻을 수 있다.

확인된 추가 수집 경로:

```text
아티스트 목록:
  /artist/list.html
  -> 내부에서 /api/artist-list.html?cate_no=515 호출

아티스트 상세:
  /artist/detail.html?product_no={artist_product_no}

추천 작가 배너:
  https://back.printbakery.com/infos/?f=get-search-artist-banner
```

| 항목 | 설명 | 표준화 대상 |
|---|---|---|
| artist | 상세 작가명 | `artist_name` |
| maker | 제작자/작가 후보 | `artist_name_candidate` |
| product_tag | 작가명/작품 태그 후보 | `metadata_json` |
| description | 작가/작품 설명이 섞인 본문 | `artist_bio_candidate` 또는 `artwork_description_candidate` |
| brand_code / manufacturer_code | Cafe24 내부 제조사/브랜드 코드 | `metadata_json` |

아티스트 목록/상세에서 추가 가능한 작가 컬럼:

| 항목 | 설명 | 표준화 대상 |
|---|---|---|
| artist_product_no | Print Bakery 아티스트 상세 식별자 | `artist_source_id` |
| artist_source_url | 아티스트 상세 URL | `artist_source_url` |
| han | 원천 한글 작가명 | `artist_name_ko_source` |
| eng | 원천 영문 작가명 | `artist_name_en_source` |
| artist_image | 아티스트 이미지 | `metadata_json` |
| is_exclusive_artist | 전속작가 목록 포함 여부 | `metadata_json` |
| index_flag | 한글/영문 색인 후보 | `metadata_json` |
| artist_meta_description | 아티스트 상세 meta description | `artist_bio_candidate` |
| artist_meta_keywords | 아티스트 상세 meta keywords | `metadata_json` |
| artist_og_title | 아티스트 상세 og title | `artist_name_ko_display` 또는 `artist_name_en_display` 후보 |
| artist_og_description | 아티스트 상세 og description | `artist_bio_candidate` |
| artist_brand_name | JSON-LD brand name | `artist_name_ko_display` 또는 `artist_name_en_display` 후보 |
| life_span_text | `b.1931 - 2023` 같은 생몰연도 문구 | `birth_year_candidate`, `death_year_candidate` |
| birth_place_candidate | meta description 안의 출생/지역 후보 | `location_city_candidate` |

Print Bakery 작가 정보는 상품 상세의 작가명만으로 끝내지 않고, `artist_product_no` 기준으로 `source_artist_raw`를 별도 생성하는 것이 좋다. 단, `artist_product_no`는 Print Bakery 내부 작가 페이지 식별자이므로 운영 공통 `artist_key`로 바로 쓰지 않는다.

### 5.3 주의 사항

- API로 `category=367`, `limit=100`, `offset` 페이지네이션이 가능하다.
- `price_content`가 `구매 별도 문의`일 수 있으므로, 가격 숫자와 가격 문구를 분리해야 한다.
- API가 실패하거나 앱 키/API 버전이 변경될 가능성이 있으므로 HTML fallback을 유지한다.
- `additional_information` 안의 크기/재료 값은 key/value 형태로 별도 파싱이 필요하다.
- 크기(`size_raw`)는 일부 행이 액자 기준만 제공한다. 2026-06-23 수집본 1,743건 기준 Image+Frame 동시 표기 213건, **Frame만 표기 39건**이며, Frame만 있는 행은 추출된 `width_cm`/`height_cm`가 작품 크기가 아니라 액자 치수다(예: `Frame 24.3 x 24.3 x 9 cm`, `20 x 20 cm (액자 포함 사이즈)`). 액자 치수로는 작품 크기를 역산할 수 없으므로 Image/작품 크기를 우선 사용한다. 액자 치수는 `frame_width_cm_candidate`/`frame_height_cm_candidate`에 분리 보존하되 모델 피처로는 쓰지 않는다. 액자만 있는 행은 작품 width/height를 비우고 `size_basis_candidate=frame_inclusive`로 플래그해 학습 snapshot에서 제외/주의 대상으로 둔다.
- 작가 소개와 작품 설명이 한 본문에 섞이면 원천별 분해/정리 단계에서 `artist_bio_candidate`와 `artwork_description_candidate`를 분리 후보로 둔다.
- 아티스트 상세의 meta description은 작가 소개와 생몰연도/지역이 한 문장에 섞일 수 있으므로 `source_artist_interpreted_staging`에서 다시 분해한다.

## 6. Art1 수집 항목

Art1은 원화 카테고리 목록/상세 AJAX endpoint를 사용한다.

### 6.1 작품 정보

Art1 작품 정보는 목록 AJAX에서 기본 카드 정보를 수집하고, 상세 AJAX에서 제작연도, 재료, 액자, 배송, 설명 등 추가 정보를 보완한다.

#### 6.1.1 목록 작품 항목

| 항목 | 설명 | 표준화 대상 |
|---|---|---|
| goods_id | Art1 작품 식별자 | `source_artwork_id` |
| title_list | 목록 작품명 | `title` |
| artist_list | 목록 작가명 | `artist_name` |
| size_text_list | 목록 크기 원문 | `dimensions_raw` |
| width_cm_list | 목록 가로 cm | `width_cm` |
| height_cm_list | 목록 세로 cm | `height_cm` |
| depth_cm_list | 목록 깊이 cm | `depth_cm` |
| ho_size_list | 호수 표기 | `metadata_json` |
| price_text_list | 목록 가격 문구 | `price_raw` |
| price_krw_list | 목록 원화 숫자 가격 | `price_amount`, `price_krw_source` |
| is_sold_list | 판매완료 여부 | `availability` |
| image_url_list | 목록 이미지 | `image_url` |
| list_classes | 목록 HTML class | `metadata_json` |
| detail_url | 상세 AJAX URL | `source_artwork_url` |

#### 6.1.2 상세 작품 항목

| 항목 | 설명 | 표준화 대상 |
|---|---|---|
| title_detail | 상세 작품명 | `title` |
| artist_detail | 상세 작가명 | `artist_name` |
| year_detail | 제작연도 | `artwork_year` |
| genre_detail | 장르 | `medium_category_candidate` 또는 `metadata_json` |
| medium_detail | 재료/매체 | `medium_raw` |
| frame_detail | 액자 정보 | `metadata_json` |
| size_text_detail | 상세 크기 원문 | `dimensions_raw` |
| width_cm_detail | 상세 가로 cm | `width_cm` |
| height_cm_detail | 상세 세로 cm | `height_cm` |
| depth_cm_detail | 상세 깊이 cm | `depth_cm` |
| ho_size_detail | 호수 표기 | `metadata_json` |
| shipping_cost_detail | 배송비 | `metadata_json` |
| shipping_method_detail | 배송방법 | `metadata_json` |
| price_text_detail | 상세 가격 문구 | `price_raw` |
| price_krw_detail | 상세 원화 숫자 가격 | `price_amount`, `price_krw_source` |
| image_url_detail | 상세 이미지 | `image_url` |
| artwork_description | 작품 설명 | `metadata_json` |
| artist_profile | 작가 소개 | `metadata_json` |

### 6.2 작가 정보

Art1은 상세 AJAX에서 작가명과 작가 소개 영역을 얻을 수 있다. 기존 수집 코드에서는 셀렉터가 보수적으로 잡혀 `artist_profile`이 비어 있을 수 있으나, 실제 상세 HTML에는 `#viewPage3`, `article.artistInfo`, `.profile` 아래 작가 프로필이 들어 있다.

| 항목 | 설명 | 표준화 대상 |
|---|---|---|
| artist_detail | 상세 작가명 | `artist_name` |
| artist_list | 목록 작가명 | `artist_name_candidate` |
| artist_idx | `/marketPlace/artist.php?idx={id}`의 작가 식별자 | `artist_source_id` |
| artist_source_url | 작가별 작품 모아보기 URL | `artist_source_url` |
| artist_profile | 작가 프로필 전체 원문 | `artist_bio_candidate`, `metadata_json` |
| artist_statement | 작가 statement | `artist_bio_candidate` |
| education_text | 학력 | `education_text_candidate` |
| selected_solo_exhibition_text | 개인전 이력 | `exhibition_text_candidate` |
| selected_group_exhibition_text | 단체전 이력 | `exhibition_text_candidate` |
| awards_text | 수상 이력 | `metadata_json` |
| project_text | 프로젝트/활동 이력 | `metadata_json` |
| collections_text | 소장처 이력 | `metadata_json` |
| artwork_description | 작품 설명 | `artwork_description_candidate` |

Art1 작가 정보는 작품 상세 안의 작가 프로필을 먼저 파싱하고, `artist_idx`가 있으면 작가별 작품 모아보기 URL을 `source_artist_raw`에 연결한다. 다만 `artist_idx`도 Art1 내부 식별자이므로 운영 공통 `artist_key`로 바로 쓰지 않는다.

### 6.3 주의 사항

- 목록의 판매완료 표시와 상세 가격이 다를 수 있으므로 둘 다 보존한다.
- 판매완료이면서 가격 숫자가 있는 경우와 가격 숫자가 없는 경우를 구분한다.
- 호수는 모델 계산의 기본 단위가 아니라 표시/보조 정보로 저장한다.
- 최종 계산용 크기는 cm 기준 `width_cm`, `height_cm`, `depth_cm`를 사용한다.
- 작가 프로필 영역에는 현재 작품 추천 문구나 작품 가격 문구가 같이 붙을 수 있으므로, 작가 이력과 작품 추천 블록을 분리해야 한다.

## 7. 작가 정보 원천별 분해/정리 staging 기준

작가 정보는 작품 정보와 별도로 분해/정리한다. 이유는 작품 row의 작가명만으로 최종 작가 identity를 확정하면 동명이인, 영문/한글 표기 차이, 플랫폼별 ID 차이를 처리하기 어렵기 때문이다.

### 7.1 작가 중간 staging에서 만드는 후보값

| 후보 컬럼 | 설명 |
|---|---|
| `artist_source_id_candidate` | 원천 작가 ID/slug 후보 |
| `artist_source_url_candidate` | 원천 작가 페이지 URL 후보 |
| `artist_name_raw` | 원천 작가명 |
| `artist_name_display_candidate` | 표시용 작가명 후보 |
| `artist_name_ko_candidate` | 한글명 후보 |
| `artist_name_en_candidate` | 영문명 후보 |
| `artist_name_normalized_candidate` | 비교용 정규화 이름 |
| `birth_year_candidate` | 출생연도 후보 |
| `death_year_candidate` | 사망연도 후보 |
| `nationality_candidate` | 국적 후보 |
| `gender_candidate` | 성별 후보 |
| `location_city_candidate` | 활동 도시 후보 |
| `location_country_candidate` | 활동 국가 후보 |
| `gallery_name_candidate` | 소속/표시 갤러리 후보 |
| `solo_count_candidate` | 개인전 수 후보 |
| `group_count_candidate` | 단체전 수 후보 |
| `fair_count_candidate` | 아트페어 수 후보 |
| `total_shows_candidate` | 전체 전시 수 후보 |
| `followers_candidate` | 팔로워 수 후보 |
| `for_sale_works_candidate` | 판매중 작품 수 후보 |
| `total_works_candidate` | 등록 작품 수 후보 |
| `bio_text_candidate` | 작가 소개문 후보 |
| `education_text_candidate` | 학력 후보 |
| `exhibition_text_candidate` | 전시 이력 후보 |
| `website_url_candidate` | 홈페이지 후보 |
| `instagram_url_candidate` | 인스타그램 후보 |
| `identity_hint_json` | 작가 매칭에 쓸 힌트 |
| `quality_flags_json` | 동명이인 위험, 이름 충돌, 메타 충돌 등 |

### 7.2 사이트별 작가 분해 예시

| 사이트 | raw 값 | 중간 분해/정리 |
|---|---|---|
| Artsy | `artist_slug = "bk-lee"`, `artist_name = "BK Lee"` | 원천 ID와 표시 이름을 분리하고, 비교용 정규화 이름 생성 |
| Artsy | `nationality = "South Korean"`, `birth_year = 1978` | 국적 후보와 출생연도 후보 생성 |
| Artsy | `solo_count`, `group_count`, `fair_count` | 전시/활동량 후보로 보존 |
| Saatchi | `artist_first_name`, `artist_last_name` | 표시 이름과 비교용 이름으로 병합 |
| Saatchi | `country`, `artist_city` | 활동 국가/도시 후보 생성 |
| Saatchi | `bio`, `education`, `exhibitions` | 작가 설명/학력/전시 이력 후보로 분리 |
| Print Bakery | `artist = "정영서 Jung Young Seo"` | 한글명 후보와 영문명 후보 분리 |
| Print Bakery | `description` 안에 작가 소개와 작품 설명이 함께 있음 | 작가 소개 후보와 작품 설명 후보로 분리 시도 |
| Art1 | `artist_detail = "강덕현 | Deokhyun Kang"` | 한글명 후보와 영문명 후보 분리 |
| Art1 | `artist_profile` | 작가 소개 후보로 보존 |

### 7.3 작가 표준화 컬럼

원천별 작가 후보는 최종적으로 아래 공통 컬럼으로 맞춘다. 이 표가 작가 공통 컬럼명의 기준이다. 3.2/4.2 등 원천별 표의 `artist_location_country`/`artist_followers`/`artist_bio` 같은 표준화 대상명은 표시용 라벨이며, 실제 단일 기준 컬럼은 이 표와 `normalized_artist_staging`의 이름(`location_country`/`followers`/`bio_text` 등)을 따른다. 마찬가지로 `artist_bio_candidate`는 단일 기준의 `bio_text_candidate`와 동일 컬럼이다.

| 표준 컬럼 | 설명 |
|---|---|
| `source` | 원천 사이트 |
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
| `birth_year` | 출생연도 |
| `birth_year_source` | 출생연도 출처: `structured_field`, `birth_context_text`, `year_only_text`, `manual` |
| `birth_year_confidence` | 출생연도 신뢰도: `high`, `medium`, `low`. 자동 artist_key 확정에는 `high`만 사용 |
| `death_year` | 사망연도 |
| `nationality` | 국적 |
| `gender` | 성별 |
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
| `bio_text` | 작가 소개 |
| `education_text` | 학력 |
| `exhibition_text` | 전시 이력 |
| `website_url` | 홈페이지 |
| `instagram_url` | 인스타그램 |
| `artist_identity_status` | `unmatched`, `candidate`, `auto_approved`, `approved`, `needs_review`, `match_rejected`. staging 단계의 매칭 상태이며, 최종 `artist_identity.identity_status`(`active`/`merged`)와 이름·의미가 다르다 |
| `quality_flags_json` | 검수 필요 플래그 |

### 7.4 작가 이름 한글화/영문화 보강 기준

작가 이름 보강은 `artist_key` 확정 전에 수행한다. 서비스 표시에는 한글명이 필요하고, 기존 artist_key 연결 후보를 찾거나 신규 작가 후보를 만들 때 한글명과 영문명을 모두 후보로 볼 수 있어야 하기 때문이다.

전체 순서도와 컬럼 역할은 [artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md)을 기준으로 한다. 이 섹션은 원천 사이트별 수집 항목 문맥에서 필요한 요약이다.

처리 기준:

| 상황 | 처리 |
|---|---|
| 원천에 한글명과 영문명이 모두 있음 | 각각 `source` alias로 저장하고 표시명/매칭 후보로 둠 |
| `한글 | English`처럼 한 문자열에 둘 다 있음 | `parsed` alias로 분리하고 표시명/매칭 후보로 둠 |
| 한글명만 있음 | 영문명 후보를 만들되 `transliteration_candidate`로 두고 검수 필요 상태로 둠 |
| 영문명만 있음 | 서비스 표시용 한글 후보를 만들되 `translation_candidate` 또는 `transliteration_candidate`로 두고 검수 필요 상태로 둠 |
| 이름 보강 후보가 동명이인 위험을 키움 | `match_rejected` 또는 `needs_review`로 두고 artist_key 자동 연결 금지 |

주의:

- 자동 한글화/영문화 값은 서비스 표시와 후보 생성에는 쓸 수 있지만, 단독으로 artist_key를 확정하지 않는다.
- 변환 후보는 원천값이 아니므로 `artist_name_ko_source`/`artist_name_en_source`에 바로 덮어쓰지 않는다.
- 서비스 표시가 필요하면 `artist_name_ko_display`/`artist_name_en_display`에 넣고, `artist_name_display_source`와 `artist_name_review_status`를 함께 남긴다.

### 7.5 작가 identity 매핑 기준

작가 identity는 이름 하나만으로 확정하지 않는다.

같은 alias 또는 승인 alias가 기존 `artist_key` 후보와 겹칠 때만 후보 그룹을 만든다. 기존 후보가 없으면 불필요한 동명이인 검토를 하지 않고 신규 작가 후보 큐로 둔다. 같은 이름이 여러 `artist_key` 후보에 걸릴 수 있으므로, alias 일치만으로 병합하지 않는다. 후보 생성과 수동 승인/반려 기준은 [artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md)을 따른다.

1차 후보 생성:

- 정규화 이름이 같음
- 한글명/영문명 중 하나가 같음
- 같은 `source + artist_source_id`가 일치함. 이 경우 같은 원천 안에서는 동일 작가로 보고 기존 `artist_key`가 있으면 바로 연결함

충돌/검수 플래그(요약):

충돌 및 자동 확정/수동 검수/반려의 상세 판정 기준은 [artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md) 6.1을 단일 기준으로 한다. 여기서는 대표 신호만 요약한다.

- 강한 충돌(해당 후보와 연결 금지): 양쪽 고신뢰 생년이 다름, 같은 alias가 이미 다른 `artist_key`에 승인 연결됨, 같은 원천 ID가 다른 `artist_key`에 승인됨, 운영자 반려.
- 수동 검수(`needs_review`): 국적만 다름, 한글명 같고 영문명 다름, 원천 프로필 URL이 다른 인물로 보임, dominant medium이 다르고 양쪽 가격 row 5건 이상에서 같은 통화 기준 가격 중앙값 차이가 2.0 log 이상.
- 검수 참고만(자동 충돌 아님): 활동지/전시/갤러리만 다름.

### 7.6 artist_key 부여 단계

원천 사이트별 작가 ID는 최종 작가 키가 아니다. 같은 작가가 Artsy와 Saatchi에 동시에 있을 수 있으므로, 서비스 공통 작가 키는 별도 단계에서 부여한다.

```text
source_artist_raw
  - 원천별 작가 ID/URL/이름/메타 보존
        |
        v
normalized_artist_staging
  - 이름, 국적, 생년, 활동지, 작가 소개, 전시 이력 정리
        |
        v
artist_identity_candidate
  - 같은 alias 또는 승인 alias에 연결된 기존 artist_key 후보가 있을 때만 후보 그룹 생성
  - 기존 후보가 없으면 신규 작가 후보 큐로 둠
        |
        v
artist_identity
  - 기존 artist_key 연결 확정 또는 신규 artist_key 생성(운영자 검수 후 데이터 관리자 승인)
  - artist_key는 최종 운영 키만 의미
  - Warm 경로와 작가 이력 feature는 artist_key가 확정된 작가만 사용
  - artist_key가 없는 미확정 작가는 Cold 경로로만 예측하고 검수 필요 표시를 강제한다
```

주의:

- 이름만 같다는 이유로 자동 병합하지 않는다.
- 같은 원천 내부 ID는 같은 사이트 안에서만 의미가 있다.
- 잘못 병합하면 서로 다른 작가의 가격 이력이 섞이므로, 자동 확정/반려 기준을 충족하지 못하면 수동 검수로 보낸다.
- 반대로 같은 작가를 계속 분리하면 Warm 경로에서 작가 이력이 쪼개질 수 있으므로, 검수 큐에서 지속적으로 병합 후보를 처리한다.

## 8. 작품 정보 원천별 분해/정리 staging 기준

이 단계는 각 사이트의 수집 결과를 공통 표준 컬럼으로 바로 옮기기 전에 수행한다.

### 8.1 필요한 이유

원천 데이터에는 다음 문제가 자주 있다.

- 한 컬럼에 여러 정보가 같이 들어있다.
  - 예: `Image 29.7x21cm / Frame 38.6x38.6cm`
  - 예: `₩ 500,000 - 판매완료`
- 같은 의미지만 사이트별 명칭이 다르다.
  - 예: `medium`, `mediums`, `method`, `material`, `재료`
  - 예: `sold_out`, `판매완료`, `SOLD`
- 원천별로 같은 가격 컬럼이라도 의미가 다르다.
  - 원천 KRW 가격
  - USD 원 가격
  - 고정 환율로 계산된 KRW 후보
- 작가명에 UI 문구나 영문/국문 병기가 섞일 수 있다.

따라서 raw에서 바로 표준화하지 않고, 먼저 원천별로 값을 분해하고 의미를 구분한다.

### 8.2 중간 staging에서 만드는 후보값

| 후보 컬럼 | 설명 |
|---|---|
| `title_candidate` | 정리된 작품명 후보 |
| `artist_name_candidate` | 정리된 작가명 후보 |
| `artist_source_id_candidate` | 원천 작가 ID 후보 |
| `price_text_candidate` | 가격 원문 후보 |
| `price_currency_candidate` | 통화 후보 |
| `price_amount_candidate` | 숫자 가격 후보 |
| `price_status_candidate` | 가격 문의/판매완료/가격 없음 후보 |
| `width_cm_candidate` | 작품 가로 cm 후보 |
| `height_cm_candidate` | 작품 세로 cm 후보 |
| `depth_cm_candidate` | 작품 깊이 cm 후보 |
| `frame_width_cm_candidate` | 액자 가로 cm 후보(작품 크기와 분리 보존, 모델 피처 아님) |
| `frame_height_cm_candidate` | 액자 세로 cm 후보 |
| `size_basis_candidate` | 크기 기준 플래그: `artwork`/`frame_inclusive`(액자 포함·작품 크기 미상)/`unknown` |
| `medium_text_candidate` | 재료/매체 후보 |
| `support_text_candidate` | 지지체 후보 |
| `availability_candidate` | 판매상태 후보 |
| `parsed_parts_json` | 원문에서 분리된 세부 값 |
| `quality_flags_json` | 분해 실패/충돌/검수 필요 플래그 |

### 8.3 사이트별 분해 예시

| 사이트 | raw 값 | 중간 분해/정리 |
|---|---|---|
| Artsy | `price_raw = "US$2,045.00"` | `price_currency_candidate=USD`, `price_amount_candidate=2045` |
| Artsy | `gallery_name`, `gallery_type`, `gallery_cities` | 갤러리 문맥 후보로 보존하되 즉시 학습 피처로 쓰지 않음 |
| Saatchi | `mediums = "Oil, Canvas"` | `medium_text_candidate=Oil`, `support_text_candidate=Canvas` 후보 생성 |
| Saatchi | `artist_first_name`, `artist_last_name` | `artist_name_candidate`로 병합 |
| Print Bakery | `size = "Image 29.7x21cm / Frame 38.6x38.6cm"` | 작품(Image) 크기를 width/height로, 액자 치수를 frame_* 에 분리 보존. 액자만 있으면 작품 width/height는 비우고 `size_basis_candidate=frame_inclusive` 플래그 |
| Print Bakery | `price_content = "구매 별도 문의"` | 가격 숫자 없음, `availability_candidate=price_on_request` |
| Art1 | `size_text = "60.6x72.7cm | 20호"` | cm 크기와 호수 표시를 분리 |
| Art1 | `price_text = "₩ 500,000 - 판매완료"` | 가격 숫자와 판매완료 상태를 분리 |

### 8.4 중간 단계에서 검수해야 할 항목

- 가격 숫자와 판매상태가 충돌하는 row
- 작품 크기와 액자 크기가 동시에 있고 기준이 모호한 row
- 재료/지지체 분리가 안 되는 row
- 작가명에 UI 문구가 붙은 row
- 같은 원천 ID인데 같은 통화 기준 가격이 50% 이상 바뀌었거나 면적이 20% 이상 바뀐 row
- 재료/상태 매핑 config(정규화 config)에 없는 재료명/상태명

## 9. 작품 공통 표준화 매핑

최종적으로 4개 사이트의 수집 결과는 아래 공통 컬럼으로 맞춘다.

> 라벨 주: 3~6장 원천별 표의 "표준화 대상"은 목표/후보 라벨이다. `normalized_artwork_staging`의 단일 기준은 [MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md) 5.8이며, 공통 컬럼에 없는 값(갤러리명/유형/도시, subject, style 등)은 공통 컬럼이 아니라 `metadata_json`에 보존한다. 모델 피처 승격은 별도 검증 후에 한다(§9.1·10장). 작가 메타 라벨의 단일 기준 컬럼 대응은 §7.3을 따른다.

| 공통 컬럼 | Artsy | Saatchi | Print Bakery | Art1 |
|---|---|---|---|---|
| `source` | artsy | saatchi | printbakery | art1 |
| `source_artwork_id` | artwork id/slug | artwork id/slug | product_no | goods_id |
| `source_artwork_url` | artwork URL | artwork URL | detail URL | detail URL/AJAX URL |
| `title` | title | title | product_name/artwork | title_detail |
| `artist_name` | artist_name | first+last name | artist/maker | artist_detail |
| `artist_source_id` | artist_slug | artist_id | artist_product_no | artist_idx |
| `normalized_artist_id_candidate` | 작가 identity 연결 후보 | 작가 identity 연결 후보 | 작가 identity 연결 후보 | 작가 identity 연결 후보 |
| `artist_identity_status` | unmatched/candidate/auto_approved/approved/needs_review/match_rejected | unmatched/candidate/auto_approved/approved/needs_review/match_rejected | unmatched/candidate/auto_approved/approved/needs_review/match_rejected | unmatched/candidate/auto_approved/approved/needs_review/match_rejected |
| `price_raw` | price_raw | price_usd 원문 | price/price_content | price_text_detail |
| `price_currency` | 원천 통화 | USD | KRW | KRW |
| `price_amount` | 원천 통화 숫자 | USD 숫자 | KRW 숫자 | KRW 숫자 |
| `price_type` | retail_ask | retail_ask | retail_ask | retail_ask (판매완료 row도 호가) |
| `price_tax_basis` | unknown | unknown | unknown | unknown |
| `price_krw_source` | 원천 KRW일 때만 | 보통 없음 | 원천 KRW | 원천 KRW |
| `width_cm` | width | width | size 파싱 | width_cm_detail |
| `height_cm` | height | height | size 파싱 | height_cm_detail |
| `depth_cm` | depth | depth | size 파싱 | depth_cm_detail |
| `medium_raw` | medium | mediums | method/material | medium_detail |
| `availability` | status | status | sold_out/selling/price_content | is_sold/price_text |
| `image_url` | image URL | image URL | list/detail image | image_url_detail |
| `artwork_year` | year | year | product_name/material에서 후보 추출 가능 | year_detail |
| `metadata_json` | 갤러리/태그/작가메타 | 작가메타/태그 | edition/code/tag/description | frame/shipping/profile |

### 9.1 표준화가 안 된 컬럼 처리

원천별로만 존재하거나 의미가 확정되지 않은 컬럼은 아래처럼 처리한다.

| 경우 | 처리 |
|---|---|
| 공통 컬럼으로 의미가 명확히 매핑됨 | `normalized_artwork_staging` 또는 `normalized_artist_staging`의 공통 컬럼에 저장 |
| 의미는 있으나 사이트별 고유 정보임 | `metadata_json`에 원천 필드명과 원천 값을 그대로 저장 |
| 한 컬럼에 여러 값이 섞여 있음 | `source_*_interpreted_staging`에서 분해하고, 분해 결과는 `parsed_parts_json`에 저장 |
| 공통 분류로 매핑 실패 | `unmapped` 또는 `quality_flags_json`에 남기고 공통 컬럼은 비워 둠 |
| 값은 있으나 기준이 모호함 | 후보 컬럼에만 저장하고 `quality_flags_json`에 검수 필요 사유 저장 |
| 원천에 값이 없음 | 빈 값으로 둔다. 추정값으로 채우지 않음 |

작품 부가 정보와 작가 부가 정보는 같은 `metadata_json`에 섞지 않는다.

| 구분 | 저장 위치 | 예시 |
|---|---|---|
| 작품 부가 정보 | `source_artwork_raw.metadata_json` | 호수, 액자 정보, 배송비, edition, 작품 설명, product tag, HTML class |
| 작가 부가 정보 | `source_artist_raw.metadata_json` | 작가 소개문, 학력, 전시 이력, 수상, 프로젝트, 소장처, 홈페이지, 인스타그램 |
| 작품/작가가 섞인 원문 | raw에는 원문 그대로 저장, interpreted staging에서 후보 분리 | Print Bakery description, Art1 artist profile 주변 텍스트 |

예시:

- Art1의 호수 표기는 `metadata_json`에 보존하고, 모델 계산용 크기 컬럼은 cm 기준이 확인될 때만 채운다.
- Print Bakery의 `Image / Frame` 크기는 작품 크기와 액자 크기를 분리하되, 어느 기준인지 불명확하면 `size_basis_candidate`와 `quality_flags_json`에 남긴다.
- Artsy/Saatchi의 갤러리명, subject, style은 수집하되 즉시 공통 학습 피처로 승격하지 않는다.
- 재료명이 mapping table에 없으면 임의로 비슷한 재료로 넣지 않고 `unmapped_medium`으로 남긴다.

## 10. 학습 데이터로 바로 쓰지 않는 항목

아래 값들은 수집은 하되, 바로 모델 학습 피처로 쓰지 않는다.

- 원천 작가 ID
- 갤러리명
- 작가 팔로워 수
- 작가 전시 수
- 상품 태그
- 작품 설명/작가 소개 텍스트
- 배송비/배송방법
- HTML class
- 원천 카테고리 전체 목록
- 작가 소개문 원문
- 작가 팔로워/전시 수 등 원천별 인기도 지표
- 자동 확정되지 않은 artist identity 후보

이 값들은 결측률, 입력 가능성, 중복/오염 가능성을 별도 실험으로 확인한 뒤 피처로 승격한다.

### 10.1 결측 가격 row 처리

가격이 없거나 가격 대신 문의 문구만 있는 row는 수집·보존은 하되 학습 가격 라벨에서는 제외한다.

- `price_on_request`: Print Bakery `price_content = "구매 별도 문의"`처럼 가격 숫자 없이 문의 문구만 있는 경우다. `availability_candidate=price_on_request`로 두고 `price_amount`는 빈 값으로 유지한다.
- 원천에 가격이 아예 없는 row도 같은 규칙을 따른다.
- 빈 값은 빈 값으로 유지하고, 학습 가격 라벨(`price_krw_normalized`/`price_krw_source`) 대상에서만 제외한다. **결측 가격을 `0`이나 임의값으로 대체하지 않는다.**
- 이 row들은 크기/재료/작가 등 다른 메타가 있으면 보존·분석에는 쓰되, 가격 타깃이 없는 학습 snapshot row로 분류한다.

## 11. 데이터 분석/관리 검토 기준

수집 항목은 모델 학습에 바로 쓰기 위한 컬럼과, 향후 검증 후 승격할 수 있는 후보 컬럼을 구분해서 관리한다.

### 11.1 데이터 분석가 관점

분석가가 각 원천의 데이터를 비교할 때 최소 아래 리포트가 필요하다.

| 리포트 | 목적 |
|---|---|
| 원천별 결측률 | 가격, 크기, 작가명, 재료, 작가 메타가 어느 사이트에서 얼마나 비는지 확인 |
| 가격 통화 분포 | KRW/USD/EUR 등 원천 통화가 섞이는지 확인 |
| 가격 상태 분포 | 판매중, 판매완료, 가격문의, 가격없음을 분리해 학습 가능 row를 판단 |
| 크기 파싱 실패 유형 | cm, inch, 액자 포함 크기, 호수 표기가 어떻게 섞이는지 확인 |
| 재료/지지체 unmapped 목록 | 정규화 config(mapping 목록)에 없는 재료명을 사람이 보강 |
| 작가 메타 보유율 | 국적, 생년, 활동지, 갤러리, 전시 이력의 원천별 보유율 확인 |
| identity 후보 신뢰도 분포 | 자동 확정 가능, 수동 검수 필요, 매칭 금지 후보 비율 확인 |

분석용 지표는 원천별 편향을 같이 봐야 한다. 예를 들어 Artsy/Saatchi는 해외 작가와 USD 가격 비중이 높고, Print Bakery/Art1은 국내 원화 가격과 평면 작품 비중이 높을 수 있다. 따라서 단순 row 수만 비교하지 않고, 가격대, 통화, 작가 국적, 매체 분포를 함께 비교한다.

가격을 원천 간 비교하거나 모델 타깃으로 쓸 때는 혼합 통화(`price_currency`+`price_amount`)를 그대로 비교하지 않는다. 학습용 단일 통화 가격은 `price_conversion` 단계에서 환산한 `price_krw_normalized`를 사용한다. 원천이 직접 KRW를 제공한 `price_krw_source`는 환산하지 않고 그대로 쓴다. 설계는 [MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md)의 `fx_rate_daily`/`price_conversion`을 따른다.

환율 기준일은 단일 규칙으로 고정한다.

- **각 row는 그 row의 수집 시점(`collected_at`) 환율로 KRW 환산한다(point-in-time 정합성).** `fx_rate_daily`에서 `collected_at` 날짜의 환율을 조회해 적용한다.
- 환산에 사용한 환율과 기준일을 `price_krw_normalized`와 함께 동반 저장한다(예: `price_fx_rate`, `price_fx_date`). 어떤 환율로 언제 기준 환산했는지 추적 가능해야 한다.
- **snapshot export 시점의 환율을 전체 row에 일괄 적용하지 않는다.** 과거 수집 가격에 최근 환율을 입히면 과거 가격에 환율 노이즈가 유입되어 타깃이 왜곡된다.

### 11.2 데이터 관리자 관점

데이터 관리자는 각 값이 어디서 왔고, 어떤 규칙으로 바뀌었고, 누가 승인했는지를 추적할 수 있어야 한다.

필수 관리 항목:

- `source`: 원천 사이트
- `source_artwork_id`: 원천 작품 ID
- `source_artwork_url`: 원천 작품 URL
- `artist_source_id`: 원천 작가 ID/slug
- `run_id`: 수집 실행 ID
- `collector_version`: 수집 코드 버전(git SHA). 파서도 함께 배포되므로 이 값으로 갈음
- 정규화 규칙 버전: 수집 run이 아니라 snapshot(`artwork_snapshot.rules_version`)과 모델 아티팩트에 기록
- `payload_hash`: 원본 응답 hash
- `quality_flags_json`: 이상치, 충돌, 검수 필요 사유
- `artist_identity_status`(normalized_*_staging의 staging 매칭 상태)와 `artist_identity.identity_status`(최종 `active`/`merged`): 작가 identity 상태를 단계별로 구분. 검수 대기는 최종 artist_key가 아니라 후보 큐 상태로 관리

`artist_key`는 이름만으로 찍어내는 단순 자동 생성값이 아니라, 자동 확정 조건을 통과했거나 데이터 관리자가 승인한 최종 운영 키로 본다. 원천 ID가 같더라도 사이트가 다르면 같은 작가라는 뜻이 아니며, 이름이 같아도 동명이인일 수 있다.

데이터 보관 정책:

- raw payload는 재현성과 감사 목적을 위해 파일/object storage에 보관한다.
- MySQL에는 payload 경로, hash, 파싱 결과, 품질 지표를 저장한다.
- 학습에 사용한 snapshot은 삭제하지 않고 모델 버전과 연결한다.
- 수동 검수 결과는 현재 승인/반려 상태(승인자/시각/사유)로 남긴다. 변경 전체 audit 이력은 별도 고도화 항목으로 두되, 신규 생성·연결 확정·병합·un-merge 같은 비가역 작가 identity 결정은 `identity_event_log`([MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md) 5.12.1)에 append-only로 남긴다.

## 12. 정리

4개 사이트의 수집 항목은 완전히 같지 않다.

- Artsy/Saatchi는 작가 메타가 상대적으로 풍부하다.
- Print Bakery/Art1은 국내 원화 가격, 크기, 재료 정보가 명확하다.
- Print Bakery는 Cafe24 API를 우선 사용하되 HTML fallback이 필요하다.
- Art1은 AJAX endpoint를 우선 사용하되 HTML fallback이 필요하다.

따라서 운영 DB에서는 원천별 raw를 먼저 보존하고, 이후 `source_artwork_interpreted_staging`에서 원천별 값을 분해/정리한 뒤, 마지막으로 `normalized_artwork_staging`에서 공통 컬럼으로 맞추는 구조를 사용한다.

작가 정보도 동일하게 `source_artist_raw`를 먼저 보존하고, `source_artist_interpreted_staging`에서 이름/국적/출생연도/활동지/전시 이력 등을 분해한 뒤, `normalized_artist_staging`에서 공통 컬럼으로 맞춘다. 이후 `artist_name_alias`에서 한글명/영문명 보강 후보를 검수한다. 같은 alias 또는 승인 alias에 연결된 기존 `artist_key` 후보가 있을 때만 `artist_identity_candidate`에서 검수 가능한 구조로 관리하고, 기존 후보가 없으면 신규 작가 후보 큐로 둔다. 신규 작가는 운영자 검수를 거쳐 데이터 관리자가 승인한 뒤에만 `artist_identity`에 최종 `artist_key`를 생성한다. Warm 경로와 작가 이력 feature는 확정된 `artist_key`만 사용하며, 미확정 작가는 Cold 경로로만 예측하고 검수 필요 표시를 강제한다.
