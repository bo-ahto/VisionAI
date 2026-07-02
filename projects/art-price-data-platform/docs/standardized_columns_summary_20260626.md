# 수집 분해/표준화 컬럼 요약 - 작품 / 작가 / 작가메타

작성일: 2026-06-26

## 1. 목적

상위 검토자가 전체 수집/DB 설계 문서를 보지 않고도, raw 이후 분해 후보와 표준화 이후 작품, 작가, 작가메타 관련 테이블에 어떤 컬럼을 넣는지 확인하기 위한 요약 문서다.

상세 DDL, enum, 운영 규칙의 단일 기준은 아래 문서를 따른다.

- [MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md)
- [원천 사이트별 수집 항목 정리](source_site_collected_fields_20260624.md)
- [NANT 재료(지지체/매체) 분류 기준](nant_material_classification_criteria_20260626.md)

## 2. 범위

포함하는 테이블:

| 구분 | 테이블 | 역할 |
|---|---|---|
| 작품 원천 분해 후보 | `source_artwork_interpreted_staging` | 작품 raw 원문에서 작품 관련 후보값만 분리한 중간 결과 |
| 작가 원천 분해 후보 | `source_artist_interpreted_staging` | 작가 raw 원문에서 작가 관련 후보값만 분리한 중간 결과 |
| 표준화 검수 큐 | `standardization_review_item` | 자동 표준화가 막힌 항목을 검수하는 공통 큐. `artist_name_ko`, `artist_key`, `new_artist`, `nant_mapping`, `fx_rate`, `artwork_field` 등을 타입으로 관리 |
| 작품 표준화 | `normalized_artwork_staging` | 원천별 작품 데이터를 공통 컬럼으로 맞추고, 확정된 active artist_key, KRW 환산값, NANT 분류 결과를 함께 담은 학습 직전 작품 staging |
| 작품 가격 환산 기준 | `fx_rate_daily` | 원천 통화를 KRW로 환산할 때 사용하는 기준 환율 |
| 작품 재료 분류 기준 | `nant_mapping_version`, `nant_allowed_category`, `nant_material_mapping` | NANT 지지체/매체 mapping과 학습 제외 기준. 분류 결과는 `normalized_artwork_staging` 컬럼에 저장 |
| 작가 표준화 | `normalized_artist_staging` | 원천별 작가 데이터를 공통 컬럼으로 맞춘 표준화 후보 |
| 작가명 보강 | `artist_name_alias` | 한글명/영문명/원문명/변환 후보와 검수 이력 |
| 작가 최종 키 | `artist_identity` | 서비스/모델에서 쓰는 최종 `artist_key` |
| 작가메타 | `artist_profile_meta` | 학력, 전시, 수상, 소개문, SNS, 현재 표시값을 항목 단위로 관리하는 SoT |

이 문서에서 제외하는 것:

- `source_*_raw`: 원천 보존 테이블
- `normalized_artwork_change_event`, `normalized_artwork_override`: 작품 필드 수동 patch/audit 테이블
- `artist_identity_candidate`, `identity_event_log`, `artist_identity_version`: 작가 identity 검수/버전 관리 상세 테이블. 단, 동명이인 artist_key 배정 흐름은 6장에 요약
- snapshot/export/model feature 컬럼: D1 이후 별도 단계에서 정의

## 3. 전체 흐름

```text
[스케줄러]
  - 매주 원천별 수집 job 실행(전 원천 주 1회)
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
[작가명 한글화/alias 준비]
  - source_artist_interpreted_staging을 normalized_artist_staging으로 표준화
  - 원천 한글명/영문명/원문명은 source 컬럼에 그대로 보존
  - 자동 한글화/영문화 결과는 candidate 컬럼에 후보로 저장
  - 한글화 우선순위는 원천 한글명 -> 승인 alias -> 자동 후보 순서로 판단
  - 자동 후보는 확정값이 아니라 위험 점수와 reason code를 붙인 검수 후보
  - 작가명 한글화 위험 후보는 standardization_review_item(review_type=artist_name_ko)에 등록
  - 승인된 한글명/영문명/원문명은 artist_name_alias에 등록
  - 이 단계에서는 artist_key를 생성/연결하지 않음
        |
        v
[artist_key 후보 산출 / 동명이인 검수]
  - 승인 alias, source + artist_source_id, 생년/국적/활동지, 원천 URL을 함께 비교
  - 같은 원천 ID가 이미 active artist_key에 연결되어 있으면 자동 연결 후보 생성
  - 동일 이름/alias라도 식별값이 충돌하면 동명이인으로 보고 검수 큐에 보류
  - 기존 후보가 없으면 standardization_review_item(review_type=new_artist)에 등록
  - 자동 확정 조건 또는 데이터 관리자 승인 후에만 artist_identity에 active artist_key 생성/연결
  - artist_key 미확정 작품은 표준화 완료 row를 만들지 않고 검수 큐에 보류
        |
        v
[작품 표준화 staging row 생성]
  - source_artwork_interpreted_staging을 공통 작품 컬럼으로 변환
  - 공통 단위, 공통 판매상태, 가격 유형/세금 기준 적용
  - 확정된 active artist_key가 있는 작품만 normalized_artwork_staging row 생성
  - 각 row collected_at 시점 환율(fx_rate_daily)로 원천 통화를 KRW로 환산
  - 원천이 직접 KRW를 제공한 경우(price_krw_source)는 환산하지 않고 그대로 사용
  - price_krw_normalized, price_fx_rate, price_fx_date, price_fx_source, price_krw_is_converted 생성
  - 환율 누락/이상치는 standardization_review_item(review_type=fx_rate)에 보류
  - DB active NANT mapping version을 조회해 NANT 95개 support/medium 조합으로 매핑
  - NANT 미매핑/모호한 재료는 standardization_review_item(review_type=nant_mapping)에 보류
  - nant_mapping_version_id, nant_material_mapping_id, nant_support, nant_medium, nant_category_key 생성
  - artist_key/가격/NANT 결과를 포함해 normalized_artwork_staging에 1회 INSERT
  - 표준화 완료 후 artist_key/가격/NANT 값만 별도 UPDATE하지 않음
  - NANT learning_excluded는 작품 row에 복사하지 않고 mapping row 조인으로 판단
        |
        v
[원천 변경 감지 / 재처리 대상 산출]
  - source_artwork_key/source_artist_id 기준 직전 run과 후보값 hash 비교
  - 가격/상태/재료/작가 후보가 바뀐 row만 표준화 gate 재평가 대상으로 표시
  - 기존 normalized/snapshot row는 직접 수정하지 않고 새 normalized row 또는 review item 생성
        |
        v
[표준화 gate 감사 / 검수 큐 집계]
  - artist_key 미확정, FX 누락/이상치, NANT 미매핑/모호 재료는 standardization_review_item에 보류
  - 가격/크기/재료 파싱 실패와 placeholder 가격은 review_type=artwork_field 또는 snapshot 제외 정책 후보로 분리
  - 완료 row에는 unresolved artist_key/NANT/FX 상태를 남기지 않음
  - run summary에 review_type별 open/approved/applied 건수와 raw->interpreted->normalized 통과율 기록
        |
        v
[완료 row 품질 / snapshot readiness 감사]
  - normalized_artwork_staging의 필수값, 가격 양수 여부, 크기 범위, 중복률, current view 정합성 점검
  - NANT 학습 제외는 nant_material_mapping.learning_excluded 조인으로 판단
  - snapshot item에는 승인된 완료 row와 명시적 제외 사유만 고정
        |
        v
[학습 snapshot 생성/export]
  - 특정 기준일의 stable dataset을 artwork_snapshot/artwork_snapshot_item으로 고정
  - 가격/NANT/artist_key는 normalized_artwork_staging에 저장된 값을 복사
  - NANT learning_excluded=true row는 snapshot item에 제외 사유로 고정
  - price_krw_normalized로 통화가 통일된 row만 학습 가격 대상으로 사용
  - parquet 우선 export, 외부 공유/검수/기존 코드 호환이 필요하면 CSV 추가 생성
  - 모델 학습에는 export snapshot만 사용
```

핵심 원칙:

- raw 원문은 버리지 않고 `source_*_raw`에 보존한다.
- `source_*_interpreted_staging`은 raw 원문을 보고 작품/작가 후보값을 분리하는 단계다. 원천에 없는 값은 임의로 채우지 않고, 보이지 않는 값을 추정/보강하지 않는다.
- interpreted 단계의 후보값은 원천 문자열 안에 명시된 값을 구조화한 결과다. 예를 들어 가격 문구에서 통화/숫자를 분리하거나, 크기 문자열에서 가로/세로 후보를 분리할 수는 있지만 새로운 의미를 계산해 확정하지 않는다.
- 표준화 실패나 매핑 실패는 삭제하지 않고 `standardization_review_item`에 보류하거나, 후보 row의 `quality_flags_json`에 남긴다.
- 작가명 한글화는 원천값, 자동 후보, 표시값, 검수된 alias를 분리한다. 자동 한글화 후보만으로 최종 표시명이나 작가 identity를 확정하지 않는다.
- 동명이인 가능성이 있으면 동일 이름/alias만으로 `artist_key`를 배정하지 않는다. 생년, 국적, 활동지, 원천 작가 ID/URL, 승인 alias를 함께 비교하고, 모호하면 검수 큐에 보류한다.
- 작가 identity와 작가 프로필은 분리한다. `artist_identity`에는 최종 키와 식별 필드만 두고, 소개/학력/전시/팔로워와 현재 표시값은 `artist_profile_meta`로 관리한다.
- NANT 학습 제외는 기존 하드코딩 필터가 아니라 DB active mapping의 `learning_excluded=true`로 판단한다.

표준화 완료 이후 기준:

| 대상 | 표준화 완료 row | 표준화 row 생성 중 처리 | 표준화 이후 파생/확정 | 설명 |
|---|---|---|---|---|
| 작품 | `normalized_artwork_staging` | `artist_key` resolve, `price_conversion`, NANT classification | `artwork_snapshot_item` | 작품 표준화 완료 물리 테이블은 `normalized_artwork_staging`이다. 확정된 active 작가 키, KRW 환산 결과, NANT 분류 결과도 row 생성 시 이 테이블에 1회 저장하고, snapshot/export는 이 값을 복사한다 |
| 작가 | `normalized_artist_staging` | 없음 | `artist_name_alias`, `artist_identity_candidate`, `artist_identity`, `artist_profile_meta` | 작가 표준화 row는 후보/중간 산출이다. 최종 서비스 작가 키는 `artist_identity`, 프로필/현재 표시값은 `artist_profile_meta`에서 확정한다 |

`price_conversion`과 NANT classification은 별도 물리 테이블이 아니라 artwork normalizer 내부 처리 단계다. 환율 기준은 `fx_rate_daily`에 저장하고, NANT 기준은 `nant_material_mapping`에 저장한다. 환산 결과와 NANT 분류 결과는 `normalized_artwork_staging` row INSERT 전에 계산해 같은 row에 저장한다. 표준화 완료 row를 만든 뒤 후속 UPDATE로 가격/NANT/artist_key 컬럼만 채우는 흐름으로 보지 않는다.

## 4. 원천 분해 후보 컬럼

### 4.1 `source_artwork_interpreted_staging`

작품 raw에서 바로 공통 표준으로 가지 않고, 사이트별 원문을 먼저 분해하고 정리하는 중간 결과다. 작품 설명과 작가 소개가 한 원문에 섞여 있으면 raw에는 원문 전체를 보존하고, 이 단계에서는 작품 관련 후보만 분리한다.

| 후보 컬럼명 | 설명 |
|---|---|
| `id` | 작품 interpreted row PK |
| `source_artwork_raw_id` | `source_artwork_raw` 참조 |
| `source` | 원천 사이트 |
| `source_artwork_id` | 원천 작품 ID |
| `title_candidate` | 작품명 후보 |
| `artist_name_candidate` | 작가명 후보 |
| `artist_source_id_candidate` | 원천 작가 ID 후보 |
| `price_text_candidate` | 원천 가격 문구 후보 |
| `price_currency_candidate` | 원천 가격 문구에서 분리한 통화 후보 |
| `price_amount_candidate` | 원천 가격 문구에서 분리한 숫자 가격 후보 |
| `price_status_candidate` | 가격 문의, 판매완료, 가격 없음 등 가격 상태 후보 |
| `width_cm_candidate` | 원천 크기 문자열에서 분리한 가로 cm 후보 |
| `height_cm_candidate` | 원천 크기 문자열에서 분리한 세로 cm 후보 |
| `depth_cm_candidate` | 원천 크기 문자열에서 분리한 깊이 cm 후보 |
| `frame_width_cm_candidate` | 액자 가로 cm 후보. 작품 크기와 분리 보존 |
| `frame_height_cm_candidate` | 액자 세로 cm 후보 |
| `size_basis_candidate` | 크기 기준 후보: `artwork`, `frame_inclusive`, `unknown` |
| `medium_text_candidate` | 재료/매체 후보 |
| `support_text_candidate` | 지지체 후보 |
| `medium_alias_applied` | 사이트별 재료 명칭 매핑 적용 여부 |
| `availability_candidate` | 판매상태 후보 |
| `artwork_description_candidate` | 작품 설명 후보 |
| `parsed_parts_json` | 원문에서 분해된 세부 값 |
| `quality_flags_json` | 분해 실패 또는 검수 필요 플래그 |
| `interpreted_at` | 분해/정리 시각 |

메모:

- 이 단계는 원천 보존 테이블이 아니다. 원천 원문은 `source_artwork_raw`에 남긴다.
- 원천에 없는 가격, 크기, 작가 ID를 임의로 채우지 않는다.
- 액자 크기만 있는 경우 작품 크기와 분리해 보존하고, 모델 피처로 바로 쓰지 않는다.

### 4.2 `source_artist_interpreted_staging`

작가 raw를 바로 최종 작가 키로 쓰지 않고, 원천별 작가 정보를 먼저 분해하고 정리하는 중간 결과다. 작품 row에서 작가 소개문 후보가 발견되더라도 곧바로 작가 확정 컬럼에 넣지 않는다.

| 후보 컬럼명 | 설명 |
|---|---|
| `id` | 작가 interpreted row PK |
| `source_artist_raw_id` | `source_artist_raw` 참조 |
| `source` | 원천 사이트 |
| `artist_source_id_candidate` | 원천 작가 ID/slug 후보 |
| `artist_source_url_candidate` | 원천 작가 페이지 URL 후보 |
| `artist_name_display_candidate` | 표시용 작가명 후보 |
| `artist_name_ko_candidate` | 한글 작가명 후보 |
| `artist_name_en_candidate` | 영문 작가명 후보 |
| `artist_name_normalized_candidate` | 비교용 정규화 이름 후보 |
| `nationality_candidate` | 국적 후보 |
| `gender_candidate` | 성별 후보 |
| `birth_year_candidate` | 출생연도 후보 |
| `birth_year_source` | 출생연도 후보의 출처 |
| `birth_year_confidence` | 출생연도 후보 신뢰도 |
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
| `bio_text_candidate` | 작가 소개문 후보 |
| `website_url_candidate` | 홈페이지 후보 |
| `instagram_url_candidate` | 인스타그램 후보 |
| `identity_hint_json` | 작가 매칭 후보 생성에 사용할 보조 정보 |
| `quality_flags_json` | 동명이인 위험, 이름 충돌, 메타 부족 등 검수 필요 플래그 |
| `interpreted_at` | 분해/정리 시각 |

메모:

- 이 단계는 최종 작가 테이블이 아니다. 최종 작가 키는 검수/승인 후 `artist_identity`에만 생성한다.
- 원천 작가 ID, 작가명, 작가 페이지 URL 등과 연결 가능한 경우에만 후보로 저장한다.
- 불확실한 값은 확정하지 않고 `quality_flags_json`에 검수 필요 사유를 남긴다.

## 5. 작품 표준화 컬럼

### 5.1 `normalized_artwork_staging`

원천별 작품 데이터를 학습 snapshot 생성 전에 공통 컬럼으로 맞춘 표준화 결과다.

| 표준화 컬럼명 | 설명 |
|---|---|
| `id` | 표준화 작품 row PK |
| `source_artwork_raw_id` | 원천 작품 raw row 참조 |
| `source_artwork_interpreted_id` | raw 분해/정리 staging row 참조 |
| `source` | 원천 사이트 |
| `source_artwork_key` | `source + source_artwork_id` 기반 작품 안정 키 |
| `source_artwork_id` | 원천 사이트의 작품 ID |
| `source_artwork_url` | 원천 작품 URL |
| `title` | 정리된 작품명 |
| `artist_name` | 작품 row에서 정리한 작가명 |
| `artist_source_id` | 원천 작가 ID/slug가 있으면 저장 |
| `normalized_artist_id_candidate` | `normalized_artist_staging`과 연결 가능한 후보 ID |
| `artist_identity_status` | 작가 매칭 상태. `normalized_artwork_staging`에 들어온 작품 row는 `auto_approved` 또는 `approved`만 허용한다. `unmatched`, `candidate`, `needs_review`, `match_rejected`는 검수 큐/보류 상태이며 표준화 완료 row를 만들지 않는다 |
| `artist_key` | 최종 운영 작가 키. `normalized_artwork_staging`에서는 필수값이며, 자동 확정 또는 데이터 관리자 승인으로 active `artist_identity`에 연결된 값만 저장한다 |
| `artist_identity_version` | `artist_key`를 해석할 때 사용한 identity membership version. `artist_key`와 함께 필수로 저장한다 |
| `price_raw` | 원천 가격 문자열 |
| `price_currency` | 원천 통화 |
| `price_amount` | 원천 통화 기준 숫자 가격 |
| `price_type` | 가격 유형. 현재 1차 원천은 기본적으로 판매 호가(`retail_ask`) |
| `price_tax_basis` | 세금/수수료 포함 여부: `tax_incl`, `tax_excl`, `unknown` |
| `price_krw_source` | 원천이 KRW 가격을 제공한 경우의 원천 KRW 값 |
| `price_krw_normalized` | KRW로 통일한 가격 |
| `price_fx_rate` | 환산에 사용한 환율 |
| `price_fx_date` | 환산 기준일 |
| `price_fx_source` | 환율 출처 |
| `price_krw_is_converted` | 원천 KRW를 그대로 썼는지, 환산했는지 구분하는 BOOL |
| `width_cm` | 작품 가로 cm |
| `height_cm` | 작품 세로 cm |
| `depth_cm` | 작품 깊이 cm |
| `area_cm2` | 계산 면적 |
| `medium_raw` | 원천 재료/매체 문자열 |
| `medium_category_candidate` | NANT 적용 전 보조 재료 분류 후보 |
| `is_3d_candidate` | NANT 적용 전 입체 여부 보조 후보 |
| `nant_mapping_version_id` | 적용한 NANT mapping version |
| `nant_material_mapping_id` | 매칭된 NANT material mapping row. 완료 row에서는 필수값이며, 미매핑/검수 필요 재료는 `standardization_review_item`에 보류 |
| `nant_material_input_text` | NANT 매핑에 사용한 재료 원문/표준화 후보값 |
| `nant_support` | NANT 기준 재료/지지체 |
| `nant_medium` | NANT 기준 도구/매체 |
| `nant_category_key` | `nant_support + '|' + nant_medium` 조합 key |
| `nant_classified_at` | NANT 분류 시각 |
| `availability` | 판매상태: `available`, `sold`, `price_on_request`, `missing_price`, `unavailable` |
| `image_url` | 대표 이미지 URL |
| `artwork_year` | 제작연도 |
| `metadata_json` | 공통 컬럼으로 승격하지 않은 사이트별 작품 부가 정보 |
| `quality_flags_json` | 가격 없음, 크기 오류, 검수 필요 등 품질 플래그 |
| `normalized_at` | 표준화 시각 |

메모:

- `medium_category_candidate`, `is_3d_candidate`는 정규화 전 보조 후보다.
- 최종 학습 포함/제외 판단은 같은 row의 NANT 컬럼과 `nant_material_mapping.learning_excluded` 조인을 사용한다.
- 가격 환산값은 `normalized_artwork_staging`에 한 번만 저장하고, snapshot/export에는 이 값을 복사해 쓴다.
- NANT 분류값과 확정된 active `artist_key`도 `normalized_artwork_staging`에 한 번만 저장하고, snapshot/export에는 이 값을 복사해 쓴다.
- 검수 대기 상태(`artist_name_ko`, `artist_key`, `new_artist`, `nant_mapping`, `fx_rate`, `artwork_field`)는 `normalized_artwork_staging`에 넣지 않고 `standardization_review_item`에 둔다. 승인 결과가 도메인 SoT에 반영된 뒤 normalizer를 재실행해 완료 row를 만든다.

### 5.1.1 `fx_rate_daily`와 `price_conversion`

`fx_rate_daily`는 원천 통화를 KRW로 환산할 때 사용하는 기준 환율 테이블이다. `price_conversion`은 별도 물리 테이블이 아니라 `fx_rate_daily`를 읽어 `normalized_artwork_staging` row 생성 전에 KRW 컬럼을 계산하는 artwork normalizer 내부 처리 단계다.

| 컬럼명 | 설명 |
|---|---|
| `rate_date` | 환율 기준일 |
| `base_currency` | 환산 대상 통화. 예: `USD`, `EUR` |
| `quote_currency` | 기준 통화. 운영에서는 `KRW` |
| `rate` | `base_currency` 1단위당 KRW 금액 |
| `rate_source` | 환율 출처 |
| `created_at` | 적재 시각 |

환산 결과는 아래 `normalized_artwork_staging` 컬럼에 저장한다.

| 컬럼명 | 설명 |
|---|---|
| `price_krw_normalized` | KRW로 통일한 최종 학습용 가격 |
| `price_krw_is_converted` | 환산값이면 `true`, 원천 KRW를 그대로 썼으면 `false` |
| `price_fx_rate` | 환산에 사용한 환율 |
| `price_fx_date` | 환산에 사용한 환율 기준일. row의 `collected_at` 기준이며, 해당일 결측 시 직전 가용 환율일 |
| `price_fx_source` | 환율 출처 |

처리 기준:

- 원천이 KRW를 직접 제공하면 `price_krw_source`를 그대로 `price_krw_normalized`로 사용하고 `price_krw_is_converted=false`로 둔다.
- 원천 통화가 KRW가 아니면 `price_amount * fx_rate_daily.rate`로 KRW 환산하고 `price_krw_is_converted=true`로 둔다.
- 환율은 snapshot 날짜가 아니라 각 row의 수집일(`collected_at`) 기준으로 적용한다.
- 해당일 환율이 없으면 직전 가용 환율일을 사용하고, 사용한 날짜를 `price_fx_date`에 남긴다.
- 환율이 없으면 임의 환산하지 않고 `quality_flags_json`에 남긴 뒤 snapshot 후보에서 보류한다.
- 환산 결과는 `normalized_artwork_staging` row INSERT 시 함께 저장한다. 표준화 완료 row를 만든 뒤 후속 UPDATE로 채우지 않는다.
- 환율 보강이나 환산 정책 변경이 필요하면 기존 row를 직접 수정하지 않고 새 normalized batch/row를 재생성한다. 이미 snapshot이 참조한 row와 export 산출물은 감사/재현을 위해 보존한다.

### 5.2 NANT 분류 컬럼

NANT 분류 결과는 별도 `artwork_nant_classification` 물리 테이블에 두지 않고, `normalized_artwork_staging`의 `nant_*` 컬럼에 저장한다. NANT 기준표와 학습 제외 기준의 SoT는 `nant_mapping_version`, `nant_allowed_category`, `nant_material_mapping`이다.

메모:

- NANT 기준 조합은 95개 support/medium 조합으로 관리한다.
- CSV `비고2`가 `학습 제외`로 시작하면 import 시 `nant_material_mapping.learning_excluded=true`로 변환한다.
- `normalized_artwork_staging`에는 `learning_excluded`/`learning_exclusion_reason`을 중복 저장하지 않는다.
- snapshot 후보에서는 `nant_material_mapping_id`로 `nant_material_mapping.learning_excluded`를 조인해 `nant_learning_excluded` 제외 사유를 계산한다. 미매핑/검수 필요 재료는 snapshot 후보가 아니라 `standardization_review_item(review_type=nant_mapping)`에서 먼저 해결한다.

## 6. 작가 표준화/identity 컬럼

작가 표준화는 두 단계를 분리한다. 먼저 작가명 한글화/alias를 안정화하고, 그 다음 승인된 이름 근거와 식별 메타를 사용해 `artist_key`를 배정한다.

```text
1. 작가명 한글화/alias 준비
   -> 원천 이름 보존
   -> 자동 한글화 후보 생성
   -> 위험 후보 검수
   -> 승인 alias 생성

2. artist_key 배정/동명이인 검수
   -> 승인 alias + 생년/국적/활동지/source ID 비교
   -> 동일인 자동 연결 후보 생성
   -> 동명이인/신규 작가 후보 검수
   -> artist_identity 확정
```

### 6.1 `normalized_artist_staging`

원천별 작가 데이터를 공통 컬럼으로 맞춘 표준화 후보다. 최종 `artist_key`가 아니라 원천별 작가 row의 표준화 결과다.

| 표준화 컬럼명 | 설명 |
|---|---|
| `id` | 표준화 작가 row PK |
| `source_artist_raw_id` | 원천 작가 raw row 참조 |
| `source_artist_interpreted_id` | raw 분해/정리 staging row 참조 |
| `source` | 원천 사이트 |
| `artist_source_id` | 원천 작가 ID/slug |
| `artist_source_url` | 원천 작가 페이지 URL |
| `artist_name_raw` | 원천 작가명 원문 |
| `artist_name_ko_source` | 원천에서 직접 받은 한글명 또는 명확히 분리한 한글명 |
| `artist_name_en_source` | 원천에서 직접 받은 영문명 또는 명확히 분리한 영문명 |
| `artist_name_ko_candidate` | 자동 한글화/표기 변환 후보 |
| `artist_name_en_candidate` | 자동 영문화/로마자 표기 후보 |
| `artist_name_ko_display` | 서비스 표시용 한글 작가명 |
| `artist_name_en_display` | 서비스 표시용 영문 작가명 |
| `artist_name_display_source` | 표시명이 온 경로: `source`, `parsed`, `alias_approved`, `manual`, `auto_transliteration`, `auto_translation` |
| `artist_name_review_status` | 이름 보강 검수 상태 |
| `artist_name_ko_orig` | 보정 전 한글명 원본 |
| `artist_name_ko_input_type` | 한글화 입력 유형 |
| `artist_name_ko_reason` | 한글명 보정 reason code |
| `artist_name_ko_risk_score` | 자동 위험 점수 |
| `artist_name_ko_risk_reasons` | 위험 패턴 사유 목록 |
| `artist_name_ko_roundtrip_confidence` | 한글명 역검증 신뢰도 |
| `artist_name_ko_override_status` | 한글명 override 등록 여부 |
| `artist_name_normalized` | 작가 매칭용 정규화 이름 |
| `nationality` | 표준 국적 |
| `gender` | 성별 |
| `birth_year` | 숫자 출생연도 |
| `birth_year_source` | 출생연도 출처 |
| `birth_year_confidence` | 출생연도 신뢰도. 자동 artist_key 확정에는 `high`만 사용 |
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
| `education_text` | 학력 텍스트 후보/요약 |
| `exhibition_text` | 전시/이력 텍스트 후보/요약 |
| `bio_text` | 작가 소개문 후보/요약 |
| `website_url` | 홈페이지 URL |
| `instagram_url` | 인스타그램 URL |
| `artist_identity_status` | staging 단계의 작가 매칭 상태 |
| `quality_flags_json` | 작가 메타 품질/검수 필요 플래그 |
| `normalized_at` | 표준화 시각 |

메모:

- `artist_identity_status`는 staging 단계의 매칭 상태다. 최종 `artist_identity.identity_status`와 의미가 다르다.
- `education_text`, `exhibition_text`, `bio_text`, `website_url`, `instagram_url`은 표준화 후보/요약 컬럼이다. 최종 검수 가능한 프로필 SoT는 `artist_profile_meta`다.
- 전시 수, 팔로워 수, 작품 수 같은 지표는 보존하되 모델 피처 사용 여부는 별도 검증 후 결정한다.

한글화 처리 기준:

- 원천에 한글명이 명시되어 있으면 `artist_name_ko_source`에 저장하고, 원천값 자체를 자동 보정값으로 덮어쓰지 않는다.
- 원천에 영문/로마자 표기만 있으면 자동 한글화 결과를 `artist_name_ko_candidate`에 저장한다. 이 값은 후보이며, 검수 전에는 최종 canonical 값으로 보지 않는다.
- 서비스 표시용 값은 `artist_name_ko_display`와 `artist_name_display_source`로 분리한다. 표시 출처는 `source`, `parsed`, `alias_approved`, `manual`, `auto_transliteration`, `auto_translation` 중 하나로 남긴다.
- 자동 한글화의 위험 점수(`artist_name_ko_risk_score`)가 있거나 역검증 신뢰도(`artist_name_ko_roundtrip_confidence`)가 낮으면 `standardization_review_item(review_type=artist_name_ko)`에 등록한다.
- 승인된 한글명은 `artist_name_alias(alias_language='ko', review_status='approved')`에 남기고, 이후 동일 작가 후보 매칭의 근거로 사용한다.

### 6.2 `artist_name_alias`

작가 이름 한글화/영문화 보강과 검수 이력을 관리한다.

| 표준화 컬럼명 | 설명 |
|---|---|
| `id` | alias row PK |
| `artist_key` | 확정된 작가라면 연결되는 최종 작가 키 |
| `normalized_artist_id` | `normalized_artist_staging.id` 참조 |
| `source` | 원천 사이트 |
| `artist_source_id` | 원천 작가 ID/slug |
| `alias_name` | 한글명, 영문명, 원문명, 변환 후보 |
| `alias_language` | alias 언어: `ko`, `en`, `other`, `unknown` |
| `alias_type` | alias 유형: `source`, `parsed`, `manual`, `transliteration_candidate`, `translation_candidate` |
| `display_target` | 표시 대상: `ko_display`, `en_display`, `matching_only` |
| `is_primary_display` | 서비스 대표 표시명 여부 |
| `confidence` | 자동 분리/변환 신뢰도 |
| `ambiguity_status` | 모호성 상태: `unique`, `ambiguous`, `needs_review` |
| `conflict_group_id` | 같은 alias가 여러 작가 후보에 걸릴 때의 충돌 그룹 ID |
| `review_status` | 검수 상태 |
| `source_name_normalized` | override/alias 매칭에 쓰는 정규화된 원문 이름 key |
| `reason_code` | 한글화/alias 등록 사유: `source_hangul`, `obvious_bad_romanization`, `readable_foreign_name_transliteration` 등 |
| `seed_source` | 최초 등록 출처: `source_hangul`, `legacy_override_csv`, `source_alias`, `manual_review`, `admin_override` |
| `seed_batch_id` | 초기 seed/import batch 식별자. 운영 중 수동 등록이면 NULL 가능 |
| `approved_by` | 수동 승인 관리자 ID |
| `approved_at` | 수동 승인 시각 |
| `approval_note` | 승인 메모 |

메모:

- 서비스 표시명과 artist_key 후보 생성을 돕는 테이블이다.
- 자동 변환명만으로 작가 identity를 확정하지 않는다.
- 같은 alias가 여러 작가 후보에 걸리면 `ambiguity_status='ambiguous'`와 `conflict_group_id`로 묶고, `standardization_review_item(review_type=artist_key)`에서 검수한다.
- 작가명 override CSV가 있더라도 운영 SoT는 CSV가 아니라 `artist_name_alias`다. CSV는 최초 seed/migration 입력으로만 사용한다.

### 6.3 작가명 한글화 흐름

작가명 한글화는 artist_key 배정보다 먼저 끝내야 하는 준비 단계다. 이 단계의 산출물은 검수된 이름 alias이며, 최종 작가 키가 아니다.

```text
source_artist_interpreted_staging
  |
  v
normalized_artist_staging
  - artist_name_ko_source
  - artist_name_en_source
  - artist_name_ko_candidate
  - artist_name_en_candidate
  - artist_name_ko_display
  |
  +-- 위험/저신뢰 한글화
  |     -> standardization_review_item(review_type=artist_name_ko)
  |     -> 관리자 검수/승인
  |
  v
artist_name_alias
  - approved alias
  - primary display name
  - matching evidence
```

한글화 자동 처리 로직:

| 순서 | 입력/조건 | 처리 | 결과 |
|---:|---|---|---|
| 1 | 원천에 한글명이 명시됨 | 원천 문자열을 정규화하지 않고 `artist_name_ko_source`에 보존 | 원천 신뢰도가 높고 충돌이 없으면 표시 후보로 사용 |
| 2 | 원천 이름에 한글/영문이 함께 있음 | 괄호, 슬래시, 콤마, 줄바꿈 등을 기준으로 한글명과 영문명을 분리 | 한글은 `artist_name_ko_source`, 영문은 `artist_name_en_source` |
| 3 | 승인된 alias가 있음 | `artist_name_alias.review_status='approved'`이고 `display_target='ko_display'`인 값을 조회 | `artist_name_ko_display`, `artist_name_display_source='alias_approved'` |
| 4 | 한글명은 없고 영문/로마자명만 있음 | 자동 한글화 후보를 생성하되 확정하지 않음 | `artist_name_ko_candidate`, `artist_name_display_source='auto_transliteration'` 후보 |
| 5 | 자동 후보 생성 후 위험 패턴 평가 | 길이, 어색한 음절, 브랜드/스튜디오명 공백, 원문 역검증, alias 충돌을 평가 | 위험이 있으면 `standardization_review_item(review_type=artist_name_ko)` |
| 6 | 관리자가 승인/수정 승인 | 승인값을 `artist_name_alias`에 기록하고 필요 시 display 후보 갱신 | 이후 artist_key 배정의 이름 근거로 사용 |

초기 DB seed 기준:

최초 DB 구축 시에는 확정값과 후보값을 분리해 넣는다. 초기 seed의 목적은 검수된 이름 지식을 DB로 옮기는 것이지, 영문명을 새로 자동 확정하는 것이 아니다.

```text
기존 수집/정제 데이터
  |
  +-- 원천 직접 한글명
  |     -> artist_name_alias(auto_approved)
  |
  +-- 기존 수동 override CSV
  |     -> artist_name_alias(approved, seed_source=legacy_override_csv)
  |
  +-- 원천 영문명/원문명/slug
  |     -> artist_name_alias(matching_only)
  |
  +-- 새 자동 한글화 결과
        -> normalized_artist_staging.artist_name_ko_candidate
        -> standardization_review_item(review_type=artist_name_ko)
```

| seed 대상 | 자동 등록 위치 | 상태 | 기준 |
|---|---|---|---|
| 원천 직접 한글명 | `artist_name_alias` | `auto_approved` | 원천에 한글명이 명시되어 있고 같은 작가 후보 안에서 충돌이 없음 |
| 기존 수동 override | `artist_name_alias` | `approved` | `scripts/track6/artist_ko_overrides.csv`처럼 사람이 검수한 legacy 매핑을 import. import 후 DB가 SoT |
| 원천 영문명/원문명/slug | `artist_name_alias` | `review_status='auto_approved'`, `alias_type='source'` | 한글 확정값이 아니라 검색/매칭용. `display_target='matching_only'` 또는 `en_display` |
| 자동 한글화 후보 | `normalized_artist_staging`, `standardization_review_item` | `needs_review` | 함수가 만든 새 한글 후보. 승인 전에는 `artist_name_alias.approved`로 넣지 않음 |
| 위험 패턴 후보 | `standardization_review_item` | `open`/`hold` | 긴 한글명, 어색한 음역, 브랜드/조직명 가능성, alias 충돌 |

대표 override seed 예시는 아래와 같다. 전체 205건 목록은 [작가 한글명 override seed 목록](artist_name_override_seed_list_20260626.md)에서 별도로 확인한다.

| source_name | artist_name_ko | reason_code | 의미 |
|---|---|---|---|
| `choonjae kim` | 김춘재 | `obvious_bad_romanization` | 로마자 한국 이름 오표기 복원 |
| `matthew anderson` | 매튜 앤더슨 | `readable_foreign_name_transliteration` | 외국 작가명 음역 |
| `gallery hexagon` | 갤러리 헥사곤 | `readable_gallery_name_transliteration` | 갤러리명 음역 |
| `hagley art` | 해글리 아트 | `readable_studio_name_transliteration` | 스튜디오/단체명 음역 |
| `weedong yoon b 1982` | 윤위동 | `metadata_removed_and_romanization_fixed` | 생년 메타 제거 후 복원 |
| `g sim seyeon` | 지심세연 | `alias_spacing_fixed` | alias 공백/표기 정리 |
| `pogoby official` | 포고비 오피셜 | `readable_alias_transliteration` | 예명/브랜드형 alias 음역 |

운영 기준:

- 최초 seed 이후 확정 한글명/override의 단일 기준은 `artist_name_alias`다.
- CSV는 migration 입력 또는 외부 반입물로만 쓰고, 운영 중 직접 참조하는 SoT로 두지 않는다.
- 관리자 화면에서 `register_override`를 실행하면 CSV를 수정하는 것이 아니라 `artist_name_alias`에 `seed_source='admin_override'`, `reason_code`, 승인자, 승인 시각을 남긴다.
- 자동 후보 생성 함수는 DB에 확정값을 쓰지 않고, 후보와 검수 사유만 만든다.

영문 -> 한글 후보 생성 원리:

영문명을 한글로 바꾸는 작업은 의미 번역이 아니라 음역(transliteration) 후보 생성이다. 예를 들어 `Park`을 `공원`으로 번역하지 않고, 이름 발음과 미술계 표기 관례를 기준으로 `박` 또는 `파크` 후보를 만든다. 이 단계의 결과는 자동 확정값이 아니라 `artist_name_ko_candidate`다.

자동 음역으로 전환되는 조건은 명확하다. 먼저 DB 승인 alias/override와 원천 한글명이 있는지 확인하고, 둘 다 없을 때만 영문/로마자 원문을 사용해 한글 후보를 만든다. 즉 자동 음역은 확정값을 찾지 못했을 때 실행되는 fallback 후보 생성 단계다.

```text
artist_name_en_source / artist_name_raw
  |
  +-- DB 승인 alias/override 있음
  |     -> artist_name_alias 승인값 사용, 자동 음역 안 함
  |
  +-- 원천에 한글명 있음
  |     -> artist_name_ko_source 보존, 자동 음역 안 함
  |
  v
자동 음역 후보 생성으로 전환
  - 영문명을 소문자로 통일
  - 괄호/출생연도/내부 suffix 같은 메타 토큰 제거
  - 기호를 제거하고 공백/하이픈 기준으로 토큰 분리
  - 원문은 artist_name_raw, artist_name_en_source에 보존
  |
  v
이름 유형 판단
  - 한국계 로마자명 후보
  - 외국 작가명 후보
  - 브랜드/스튜디오/갤러리명 후보
  - 판단 불가
  |
  v
유형별 음역 후보 생성
  |
  v
위험 점수/사유 부여
  |
  v
artist_name_ko_candidate 또는 review_type=artist_name_ko
```

자동 음역 후보 생성의 내부 순서:

| 순서 | 처리 | 원리 | 결과 |
|---:|---|---|---|
| 1 | 승인 매핑 확인 | `artist_name_alias` 또는 legacy override seed에 이미 검수된 값이 있는지 본다 | 있으면 그 값을 쓰고 자동 음역을 중단 |
| 2 | 원천 한글 확인 | 원문 문자열에 한글이 직접 포함되어 있는지 본다 | 있으면 한글을 분리해 `artist_name_ko_source`로 보존 |
| 3 | 입력 정리 | 영문명을 소문자로 통일하고 괄호 메타, 출생연도, 기호를 제거한다 | `Hongbin Kim`, `hongbin-kim`, `Hongbin Kim (b.1982)`를 같은 후보 입력으로 맞춤 |
| 4 | 성씨 사전 매칭 | `kim`, `lee`, `park`, `choi`, `jung` 같은 한국 성씨 사전을 본다 | 성씨로 판단되면 한국식 성/이름 후보를 만든다 |
| 5 | 영어 이름 사전 매칭 | `matthew -> 매튜`, `john -> 존`처럼 자주 쓰이는 이름 표기를 먼저 본다 | 외국 이름/예명 후보의 기계 음역 오류를 줄인다 |
| 6 | 한글 음절표 매칭 | 사전에 없는 토큰은 앞에서부터 6글자, 5글자, 4글자 순으로 가장 긴 음절을 찾는다 | `hongbin` -> `hong` + `bin` -> `홍빈` 후보 |
| 7 | 후보 조합 | 성씨와 이름 후보를 조합한다 | `Hongbin Kim` -> `김` + `홍빈` -> `김홍빈` 후보 |
| 8 | 확정 금지 | 자동 생성값은 승인 alias가 아니다 | `artist_name_ko_candidate`에 저장하고 필요 시 검수 큐로 보낸다 |

| 유형 | 판단 기준 | 음역 원리 | 예시 |
|---|---|---|---|
| 한국계 로마자명 후보 | 국적/활동지가 한국이거나, `kim`, `lee`, `park`, `choi`, `jung`, `jeong`, `yoo`, `yoon`, `kwon` 등 한국 성씨/이름 로마자 패턴이 있음 | 성씨 사전과 이름 음절 사전을 우선 적용한다. 성/이름 순서가 명확할 때만 한국식 순서로 재배치한다 | `Jihyeon Choi` -> `최지현` 후보 |
| 외국 작가명 후보 | 한국 성씨 패턴이 없고 서구권/기타 외국명으로 보임 | 단어별 발음에 가까운 외래어 표기 후보를 만든다. 서구식 이름 순서와 단어 간 공백을 유지한다 | `Matthew Anderson` -> `매튜 앤더슨` 후보 |
| 브랜드/스튜디오/갤러리명 후보 | `studio`, `gallery`, `official`, `digital`, `label` 등 조직/브랜드 단서가 있음 | 사람 이름처럼 성/이름을 재배치하지 않고, 조직명 단어를 자연스러운 한글 표기로 나눈다 | `Gallery Hexagon` -> `갤러리 헥사곤` 후보 |
| 판단 불가 | 성씨/국적/원천 메타가 부족하거나 여러 읽기가 가능함 | 자동 후보를 만들더라도 낮은 신뢰도로 두고 검수 큐에 보낸다 | `Lacey Kim`, `Karis Kim`처럼 한국 성씨와 외국식 이름이 섞인 경우 |

한국계 로마자명 처리 기준:

- 성씨 후보는 대표 변형을 함께 본다. 예: `kim/gim -> 김`, `lee/rhee/yi -> 이`, `park/bak -> 박`, `choi/choe -> 최`, `jung/jeong/chung -> 정`, `yoo/yu/you -> 유`, `yoon/yun -> 윤`, `kwon/gwon -> 권`.
- 이름 부분은 단어를 한 글자씩 기계적으로 읽지 않고, 한국 이름 음절 조합으로 해석한다. 예를 들어 `hyun`, `joo`, `seung`, `yeon`, `gyu`, `min`, `ji`, `young` 같은 토큰은 한국식 이름 음절 후보로 본다.
- 다만 로마자 표기는 여러 한글 이름으로 대응될 수 있으므로, 생년/국적/원천 프로필/기존 alias 근거가 없으면 자동 확정하지 않는다.
- 성/이름 순서 전환은 위험도가 높다. `artist_name_en_source`가 `First Last`인지 `Last First`인지 불명확하면 후보만 만들고 수동 검수로 보낸다.

외국명/브랜드명 처리 기준:

- 외국명은 한국 성씨 사전을 억지로 적용하지 않는다. 예: `Matthew Anderson`을 `안매튜`처럼 한국식 성/이름 순서로 바꾸지 않는다.
- 브랜드, 스튜디오, 갤러리명은 사람 이름이 아닐 수 있으므로 공백, 접미어, 고유명사 표기를 검수 대상으로 둔다.
- 음역 후보가 지나치게 길거나, `흐`, `운그`, `우르`처럼 기계적으로 끊어 읽은 흔적이 있으면 자동 표시명으로 쓰지 않는다.

자동으로 확정할 수 있는 경우:

- 이미 승인된 `artist_name_alias`가 있고 같은 `source + artist_source_id` 또는 같은 active `artist_key`에 연결되어 있다.
- 원천이 직접 제공한 한글명이고, 같은 작가 후보 안에서 다른 한글명과 충돌하지 않으며, 동명이인/alias 충돌이 없다.
- 자동 처리가 새 이름을 만든 것이 아니라 공백 정리, 괄호 안 영문 분리, `_A` 같은 내부 suffix 제거처럼 표시 형식만 정리한 경우다. 이 경우에도 원천값은 `artist_name_ko_source` 또는 `artist_name_ko_orig`에 보존한다.

자동으로 확정하지 않는 경우:

- 영문/로마자명에서 새 한글명을 만든 경우다. 이 값은 항상 `artist_name_ko_candidate`이며, 승인 전에는 canonical/display 확정값이 아니다.
- 외국 작가명, 예명, 단체명, 스튜디오명, 갤러리명처럼 사람 이름인지 브랜드/조직명인지 애매한 경우다.
- 같은 한글명 또는 같은 영문 alias가 여러 `artist_key` 후보에 걸리는 경우다.

| 단계 | 기준 | 저장 위치 | 확정/보류 기준 |
|---|---|---|---|
| 원천 이름 보존 | 원천 한글명/영문명/원문명 분리 | `normalized_artist_staging.artist_name_*_source` | 원천에 명시된 값만 저장 |
| 자동 한글화 후보 | 영문명/로마자명 기반 한글화 | `artist_name_ko_candidate`, `artist_name_ko_risk_*` | 후보로만 저장. 위험/저신뢰는 `review_type=artist_name_ko` |
| 한글명 검수 | 자동 한글화가 위험하거나 원천값과 충돌 | `standardization_review_item(review_type=artist_name_ko)` | 승인 전에는 후보로만 유지 |
| 표시명 승인 | 관리자가 대표 한글명/영문명 승인 | `artist_name_alias` | 승인 alias만 `alias_approved` 표시 출처로 사용 |

수동 검수 등록 기준:

| 기준 | 수동 검수로 보내는 조건 | risk/reason 예시 |
|---|---|---|
| 자동 후보 생성 | 원천 한글명 없이 영문/로마자명에서 한글 후보를 만든 경우 | `auto_transliteration_candidate` |
| 긴 한글 후보 | 공백/기호 제거 후 한글 음절 수가 8자 이상인 후보 | `long_hangul_ge_8` |
| 어색한 기계 음역 | `흐`, `운그`, `우르`, `에예`, `쿠엔`, `페르`, `엑스응`, `다이`, `그와`, `프하`, `브브`, `크흐` 등이 포함된 후보 | `awkward_*` |
| 브랜드/조직명 가능성 | artist_key 또는 원문에 `studio`, `gallery`, `official`, `artist`, `digital`, `day`, `pen`, `stepper`, `label` 등이 있고 한글 후보가 공백 없이 붙어 있음 | `brand_or_studio_spacing_review` |
| 메타데이터 혼입 | 이름에 출생연도, `b 1982`, 내부 suffix, 국적/활동지 같은 메타값이 섞인 경우 | `metadata_removed_and_romanization_fixed` |
| 명백한 오표기 | 기존 한글명이 로마자 이름을 기계적으로 잘못 끊어 읽은 경우 | `obvious_bad_romanization` |
| 읽기 가능한 외국명/단체명 보정 | 외국 작가명, 스튜디오명, 갤러리명을 자연스러운 한국어 표기로 다듬어야 하는 경우 | `readable_foreign_name_transliteration`, `readable_studio_name_transliteration`, `readable_gallery_name_transliteration` |
| 원문 역검증 실패 | 한글 후보를 다시 영문/로마자 기준으로 비교했을 때 원문과 매칭 신뢰도가 낮은 경우 | `low_roundtrip_confidence` |
| alias 충돌 | 같은 한글 후보가 여러 active `artist_key` 또는 여러 원천 작가 후보에 연결되는 경우 | `alias_conflict`, `homonym_candidate` |

관리자 결정 기준:

| 결정 | 적용 기준 | 반영 위치 |
|---|---|---|
| 승인 | 원천 한글명이 신뢰 가능하거나 기존 승인 alias와 일치함 | `artist_name_alias.review_status='approved'` |
| 수정 후 승인 | 후보는 맞는 방향이지만 띄어쓰기, 성/이름 순서, 외래어 표기가 부자연스러움 | 수정값을 승인 alias로 저장 |
| override 등록 | 같은 `artist_key`에 반복 적용해야 하는 명백한 보정값 | `artist_name_alias`와 override 이력에 저장 |
| alias 추가 | 표시명은 유지하되 검색/매칭용 별칭을 추가해야 함 | `artist_name_alias.display_target='matching_only'` |
| 보류 | 사람/단체 구분, 동명이인, 원천 신뢰도가 부족함 | review item open/hold 유지 |
| 반려 | 후보가 잘못 생성됐거나 원천 근거가 없음 | review item rejected, 후보 표시값 미사용 |

한글화 단계의 원칙:

- `artist_name_ko_source`는 원천값 보존 컬럼이므로 자동 한글화 결과로 덮어쓰지 않는다.
- `artist_name_ko_candidate`는 검수 전 후보이며, 이 값만으로 `artist_identity.canonical_name_ko`를 확정하지 않는다.
- 승인된 alias는 이후 artist_key 배정의 근거로 쓸 수 있지만, alias 일치만으로 같은 작가라고 확정하지 않는다.
- 기존 Track6 정제 기준처럼 자동 음역으로 대량 보정하지 않는다. DB에 등록된 승인 alias/override만 반복 적용한다.
- 보정 전 값은 `artist_name_ko_orig` 또는 source 컬럼에 보존하고, 승인 사유는 `artist_name_ko_reason`/`approval_note`로 남긴다.

### 6.4 동명이인 artist_key 배정 흐름

artist_key 배정은 한글화/alias 준비가 끝난 뒤 실행한다. 이름을 먼저 안정화한 다음, 동일인/동명이인을 판단해 최종 `artist_identity`에 연결한다.

```text
artist_name_alias + normalized_artist_staging
  |
  v
기존 artist_identity 후보 조회
  - source + artist_source_id
  - approved alias
  - birth_year / nationality / activity location
  - artist_source_url / biography evidence
  |
  +-- 후보 1개, 충돌 없음
  |     -> artist_identity_candidate(auto_match)
  |     -> artist_identity 연결
  |
  +-- 후보 여러 개 또는 식별값 충돌
  |     -> artist_identity_candidate(homonym_or_conflict)
  |     -> standardization_review_item(review_type=artist_key)
  |     -> 관리자 승인 후 연결/분리
  |
  +-- 기존 후보 없음
        -> standardization_review_item(review_type=new_artist)
        -> 관리자 승인 후 새 artist_identity 생성
```

| 케이스 | 판단 기준 | 저장 위치 | 처리 |
|---|---|---|---|
| 기존 작가 자동 연결 후보 | 같은 원천의 `source + artist_source_id`가 이미 active `artist_key`에 연결됨 | `artist_identity_candidate` | 충돌이 없으면 자동 연결 가능 |
| 원천 간 동일인 후보 | 승인 alias가 일치하고 고신뢰 생년/국적/활동지가 충돌하지 않음 | `artist_identity_candidate` | 후보가 1개일 때만 자동 연결 가능 |
| 동명이인 후보 | 이름/alias는 같지만 생년, 국적, 활동지, 원천 URL, 작가 설명이 충돌 | `artist_identity_candidate`, `standardization_review_item(review_type=artist_key)` | 동일 이름만으로 병합 금지. 관리자 검수 필요 |
| 신규 작가 후보 | 기존 active `artist_key` 후보가 없고 최소 식별 근거가 있음 | `standardization_review_item(review_type=new_artist)` | 승인 후 `artist_identity`에 새 `artist_key` 생성 |

자동 배정 가능 조건:

- 동일 원천에서 이미 승인된 `source + artist_source_id`가 같은 active `artist_key`에 연결되어 있다.
- 서로 다른 원천이라도 승인된 alias가 일치하고, 고신뢰 `birth_year`와 국적/활동지 중 하나 이상이 충돌하지 않는다.
- 후보 `artist_key`가 1개뿐이고 `conflict_group_id`가 없다.

수동 검수로 보내는 조건:

- 같은 이름 또는 한글화 후보가 여러 active `artist_key`에 걸린다.
- 생년, 국적, 활동지, 작가 URL/설명 중 핵심 식별값이 충돌한다.
- 자동 한글화 후보가 원문 이름과 역검증에서 불안정하다.
- 기존 후보가 없어서 새 작가 키를 만들 수는 있지만, 원천 근거가 부족하다.

작품 표준화와의 연결:

- `artist_key`가 확정되지 않은 작가의 작품은 `normalized_artwork_staging` 완료 row를 만들지 않는다.
- 보류된 작품은 `standardization_review_item(review_type=artist_key)` 해결 후 같은 batch에서 재처리하거나 다음 표준화 run에서 처리한다.
- 최종 `artist_key`의 SoT는 `artist_identity`이고, 후보 근거와 동명이인 판단 이력은 `artist_identity_candidate`와 검수 큐에 남긴다.

### 6.5 `artist_identity`

운영에서 사용하는 최종 작가 키 테이블이다. 같은 작가로 확정된 여러 원천 작가 row는 하나의 `artist_key`에 연결한다.

| 표준화 컬럼명 | 설명 |
|---|---|
| `artist_key` | 서비스 공통 최종 작가 키 |
| `canonical_name` | 대표 표시 작가명 |
| `canonical_name_ko` | 대표 한글명 |
| `canonical_name_en` | 대표 영문명 |
| `birth_year` | 승인된 생년 |
| `nationality` | 승인된 국적 |
| `identity_status` | 최종 작가 키 상태: `active`, `merged` |
| `created_by` | 생성 주체 |
| `created_at` | 최종 작가 키 생성 시각 |
| `approved_by` | 수동 승인 관리자 ID |
| `approved_at` | 수동 승인 시각 |
| `merge_evidence_json` | 최종 병합 근거 |
| `notes` | 운영자 메모 |

메모:

- `identity_status`는 `active`, `merged`만 사용한다.
- 검수 대기 상태는 `artist_identity`가 아니라 후보 큐 또는 `artist_identity_candidate`에서 관리한다.
- `artist_identity`에는 소개, 학력, 전시, 활동지, 팔로워, 홈페이지/SNS를 넣지 않는다.

## 7. 작가메타 컬럼

### 7.1 `artist_profile_meta`

확정된 `artist_key`에 연결된 작가 프로필/메타 항목의 SoT다. 학력, 전시, 수상, 프로젝트, 소장처, 소개문, SNS처럼 반복되거나 충돌할 수 있는 값은 한 row에 긴 문자열로 몰아넣지 않고 항목 단위로 적재한다. 현재 표시/검색/feature 후보용 값도 별도 current 테이블에 중복 적재하지 않고 이 테이블의 `is_current`와 `display_rank`로 관리한다.

효율화 기준:

- `city`, `country`, `url`, `title`처럼 일부 유형에만 쓰이는 전용 컬럼은 두지 않는다.
- `item_type`이 값의 의미를 정하고, 실제 값은 공통 값 컬럼에 넣는다.
- `value_text`는 표시값, `value_key`는 검색/필터/중복판정용 정규화 키다.
- 전시/수상처럼 여러 속성이 묶인 항목은 표시 문자열을 `value_text`에 두고, 세부 구조는 `value_json`에 둔다.
- 원천 응답, 파서 버전, 추출 근거, 원문 조각은 raw/interpreted/normalized 레이어에 이미 있으므로 `artist_profile_meta`에 다시 복제하지 않는다.
- 따라서 `artist_profile_meta`에는 `source`, `source_artist_id`, `raw_text`, `confidence`, `metadata_json` 컬럼을 두지 않는다.
- 생년/국적의 최종 승인값은 `artist_identity`가 SoT이며, `artist_profile_meta`에 중복 SoT를 만들지 않는다.

| 표준화 컬럼명 | 설명 |
|---|---|
| `id` | 프로필 항목 row PK |
| `artist_key` | `artist_identity.artist_key` 참조 |
| `normalized_artist_id` | 원천 표준화 작가 row 참조. 수동 등록이면 NULL 가능 |
| `origin_type` | `normalized`, `manual`, `imported` |
| `profile_meta_hash` | 같은 확정 항목의 중복 적재 방지 hash |
| `item_type` | 프로필 항목 유형 |
| `item_subtype` | 필요 시 세부 유형 |
| `value_text` | 항목 원문 또는 정리된 텍스트 |
| `value_key` | 검색/필터/중복판정용 정규화 키 |
| `value_number` | 숫자값. 팔로워 수, 작품 수, 전시 수 등 |
| `value_year` | 연도 단위 값 |
| `value_date` | 날짜 단위 값 |
| `value_json` | 복합 항목의 추가 구조. 예: 전시 제목, 기관, 도시, 국가, URL |
| `review_status` | 항목 검수 상태: `auto_extracted`, `approved`, `needs_review`, `rejected`, `suppressed` |
| `is_current` | 현재 대표값으로 쓸 수 있는 항목인지 여부 |
| `display_rank` | 같은 `artist_key + item_type` 안에서 현재 표시 우선순위를 정하는 숫자. 낮을수록 우선 |
| `valid_from` | 유효 시작일/연도 |
| `valid_to` | 유효 종료일/연도 |
| `quality_flags_json` | 결측, 충돌, 검수 필요 플래그 |
| `reviewed_by` | 수동 검수자 |
| `reviewed_at` | 수동 검수 시각 |
| `review_note` | 검수 메모 |
| `created_at` | 생성 시각 |
| `updated_at` | 수정 시각 |

`item_type` 후보:

```text
activity_city, activity_country, gallery, bio, statement, education,
solo_exhibition, group_exhibition, fair, award, project, collection,
website, instagram, follower_count, solo_count, group_count, fair_count,
total_shows, total_works, for_sale_works
```

메모:

- 잘못 추출된 항목은 삭제하지 않고 `review_status=rejected` 또는 `suppressed`로 닫는다.
- 수동 정정은 기존 raw를 덮어쓰지 않고 `origin_type=manual` 항목으로 추가한다.
- 이 테이블이 작가 프로필/메타와 현재 표시값의 확정 가능한 원천이다.

### 7.2 현재 표시값 적재 방식

기존 분리안에서 별도 `artist_profile_current` 테이블로 둘 수 있었던 값도 1차 개발에서는 `artist_profile_meta`에 아래 방식으로 적재한다. 화면/API는 이 값을 조회해 필요한 응답 형태로 조립한다.

| 현재 표시값 | `artist_profile_meta` 적재 방식 |
|---|---|
| 활동 도시 | `item_type='activity_city'`, `value_text`, `value_key`, `is_current=true` |
| 활동 국가 | `item_type='activity_country'`, `value_text`, `value_key`, `is_current=true` |
| 대표 갤러리 | `item_type='gallery'`, `value_text`, `is_current=true` |
| 전시 수 | `item_type`이 `solo_count`, `group_count`, `fair_count`, `total_shows` 중 하나, `value_number`, `is_current=true` |
| 팔로워/작품 수 | `item_type`이 `follower_count`, `for_sale_works`, `total_works` 중 하나, `value_number`, `is_current=true` |
| 대표 소개문 | `item_type='bio'`, `value_text`, `is_current=true` |
| 표시용 학력 | `item_type='education'`, `value_text`, `display_rank` |
| 표시용 전시/이력 | `item_type='solo_exhibition'`, `group_exhibition`, `fair` 중 하나, `value_text`, `value_year`, 필요 시 `value_json`, `display_rank` |
| 홈페이지/인스타그램 | `item_type='website'` 또는 `instagram`, `value_text`, 필요 시 `value_key`, `is_current=true` |

메모:

- 1차 개발에서는 별도 current 물리 테이블을 만들지 않는다.
- 사용자 검색, 관리자 목록, feature 후보 산출에서 집계 비용이 실제 병목으로 확인되면 후순위로 `artist_profile_summary` view/cache를 추가할 수 있다.
- summary view/cache를 추가하더라도 SoT는 계속 `artist_profile_meta`다.

## 8. 상사 보고용 한 줄 요약

작품/작가 raw 원문은 `source_*_raw`에 그대로 보존하고, `source_*_interpreted_staging`에서는 원천에 명시된 값을 작품/작가 후보 컬럼으로 분리한다. 자동 표준화가 막힌 `artist_name_ko`, `artist_key`, `new_artist`, `nant_mapping`, `fx_rate`, `artwork_field` 이슈는 `standardization_review_item`에 보류한다. 작가명 한글화는 원천값, 자동 후보, 승인 alias를 분리하고, 확정 한글명/override의 운영 SoT는 CSV가 아니라 `artist_name_alias` DB로 둔다. 동명이인 가능성이 있으면 동일 이름만으로 `artist_key`를 배정하지 않는다. 이후 작품은 확정된 active `artist_key`, KRW 환산 결과, NANT 분류 결과가 모두 준비된 경우에만 `normalized_artwork_staging`에 가격, 크기, 재료 원문과 함께 넣는다. 학습 제외 여부는 `nant_material_mapping_id`로 NANT mapping row를 조인해 판단하고 snapshot item에 제외 사유로 고정한다. 작가는 `normalized_artist_staging`에서 원천별 이름과 기본 메타 후보를 맞춘 뒤, 검수/승인된 최종 키만 `artist_identity`에 넣는다. 작가 소개, 학력, 전시, 수상, SNS, 팔로워, 현재 표시값은 `artist_identity`에 몰아넣지 않고 `artist_profile_meta`에 항목 단위로 관리한다.
