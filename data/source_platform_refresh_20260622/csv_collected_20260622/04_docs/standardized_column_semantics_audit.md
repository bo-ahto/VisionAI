# Standardized Column Semantics Audit

검토 대상:

- `standardized_artworks_merged_deduped.csv`
- `standardize_merge_collected_artworks.py`

## 수정한 항목

### `support_or_category_raw` 제거

이 컬럼은 실제 지지체 support 정보가 아니라 `medium_category_raw`와 같은 값을 복사하고 있었다.
의미가 같은 컬럼이 중복으로 존재하므로 표준 CSV에서 제거했다.

### Saatchi `medium_type_raw` 중복 제거

Saatchi 원본에는 Artsy의 `medium_type`에 해당하는 별도 컬럼이 없었다.
기존 스크립트는 Saatchi `mediums`를 `medium_raw`와 `medium_type_raw`에 동시에 넣고 있었기 때문에,
Saatchi 행에서는 `medium_type_raw`를 비워두도록 수정했다.

### Artue `price_amount` 기준 정리

`price_amount`는 `price_currency`에 적힌 통화 기준 원 가격 금액으로 정의했다.
기존에는 Artue에서 `default_currency`가 `usd`인데도 `price_amount`에 KRW 금액이 들어갈 수 있었다.
현재는 `default_currency`가 `usd`이면 `price_usd`, `krw`이면 `price_krw`, `eur`이면 `price_eur`를 넣는다.

### `artist_country`, `artist_city` 명칭 변경

Saatchi 원본의 `country`, `artist_city`는 작가 국적이라기보다 작가 위치/활동지 정보에 가깝다.
Artsy/Artue의 `artist_nationality`와 같은 의미로 합치면 안 되므로 아래처럼 이름을 바꿨다.

- `artist_country` -> `artist_location_country`
- `artist_city` -> `artist_location_city`

검증 결과:

- `artist_nationality`: Artsy/Artue에서 채워짐
- `artist_nationality_ko`: Artue에서 채워짐
- `artist_location_country`: Saatchi에서만 채워짐
- `artist_location_city`: Saatchi에서만 채워짐
- `artist_hometown`: Artue에서만 채워짐
- `artist_location_country`와 `artist_nationality`가 동시에 채워진 행은 0건

## 유지한 항목

### `price_krw`, `price_usd`, `price_eur`, `price_raw`, `price_currency`, `price_amount`

서로 겹쳐 보이지만 역할이 다르므로 유지한다.

- `price_krw`: KRW 환산 가격
- `price_usd`: USD 가격
- `price_eur`: EUR 가격
- `price_raw`: 원문 가격 문자열 또는 원천에서 받은 원 가격 표현
- `price_currency`: `price_amount`의 통화
- `price_amount`: `price_currency` 기준 원 가격 숫자

### `medium_raw`, `medium_category_raw`, `medium_type_raw`, `materials_raw`

서로 관련은 있지만 의미가 다르므로 유지한다.

- `medium_raw`: 원문 매체 설명
- `medium_category_raw`: 회화, 조각 등 큰 분류
- `medium_type_raw`: Artsy가 제공하는 세부 매체 타입
- `materials_raw`: Saatchi가 제공하는 재료 목록

### `availability`, `status`

둘 다 상태처럼 보이지만 의미가 다르므로 유지한다.

- `availability`: 판매 가능 여부 또는 노출 상태
- `status`: Artue 내부 게시 상태

### `artist_id_or_slug`, `artist_name`, `artist_first_name`, `artist_last_name`

작가 식별자와 표시명은 다르므로 유지한다.
Saatchi는 first/last name이 분리되어 있어 원본 추적을 위해 분리 컬럼도 유지한다.

### `artist_nationality`, `artist_nationality_ko`, `artist_location_country`, `artist_location_city`, `artist_hometown`

국적과 위치 정보는 의미가 다르므로 분리해서 유지한다.

- `artist_nationality`: 작가 국적/출신 국가
- `artist_nationality_ko`: 작가 국적의 한글 표기
- `artist_location_country`: 작가 위치/활동 국가
- `artist_location_city`: 작가 위치/활동 도시
- `artist_hometown`: 작가 고향 또는 출신지 문자열

## 재생성 결과

- 중복 제거 후 가격 필터 전 행 수: 68,440
- 가격 없음 또는 양수 가격 숫자 없음으로 제거된 행 수: 23,567
- placeholder 가격으로 제거된 행 수: 11
  - `1원`: 3
  - `999,999,999원`: 8
- 입체 작품으로 제거된 행 수: 1,924
- 명백한 크기 오류로 제거된 행 수: 20
- 최종 행 수: 42,918
- 최종 컬럼 수: 63
- `dedupe_key` 중복 수: 0
- `support_or_category_raw`: 제거됨

## 가격 필터 및 이상치 검증

최종 CSV에는 양수 가격 숫자가 최소 하나 이상 있는 행만 남긴다.

가격 있음으로 인정하는 값:

- `price_krw > 0`
- `price_usd > 0`
- `price_eur > 0`
- `price_amount > 0`
- 또는 `price_raw`에 1~9 숫자가 포함된 가격 표현

가격 없음으로 제거한 대표 케이스:

- 빈 가격
- `Sold`
- `On hold`
- `Price on request`
- `0`, `0.0`

placeholder 가격으로 제거한 케이스:

- `1원`
- `999,999,999원`

입체 작품으로 제거한 대표 카테고리:

- `sculpture`
- `installation`
- `ceramics`
- `glass`
- `architecture`
- `video/film/animation`
- `video / installation`
- `design/decorative art`

명백한 크기 오류로 제거한 기준:

- 평면 작품인데 `width_cm > 1000`
- 평면 작품인데 `height_cm > 1000`
- `depth_cm > 500`

현재 최종 CSV에는 위 입체 카테고리와 크기 상한 초과 행이 남아 있지 않다.

이상치 후보는 자동 삭제하지 않고 아래 파일로 분리했다.

- `standardized_artworks_outlier_audit.csv`
- `standardized_artworks_outlier_audit_summary.json`

현재 이상치 후보:

- 전체 검증 행 수: 42,918
- 이상치 후보 행 수: 190
- 가격 0 이하: 0
- KRW 가격 극단 상단: 43
- KRW 가격 극단 하단: 43
- 반복 9 placeholder 의심 가격: 34
- 크기 0 이하: 0
- 크기 cm 수동 상한 초과: 0
- 면적 극단 상단: 40
- 면적당 가격 극단 상단: 39
- 면적당 가격 극단 하단: 43
