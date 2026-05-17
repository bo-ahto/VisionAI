# Track 4 raw 통합본 컬럼 출처 구분

- 목적: `data/track4_primary_market_raw_unified.csv`에서 실제 크롤링/수집된 값과 통합 과정에서 새로 만든 값을 구분함
- 기준 파일: `data/track4_primary_market_raw_unified.csv`
- 기준일: 2026-05-15
- 제외 범위: 갤러리 티어 검증값은 별도 처리 대상이므로 이 문서에서는 제외함

## 1. 결론

- raw 통합본에는 순수 원본 수집값만 있는 것이 아님
- 아래 4종류 값이 섞여 있음
- `원본 수집값`: 크롤링 원본 파일에 있던 값을 이름만 맞춰 넣은 값
- `원본 파싱값`: 원본 문자열에서 숫자만 뽑아 표준 단위로 넣은 값
- `정규화/분류값`: 원본 문자열을 기준으로 카테고리화한 값
- `파생/관리값`: 통합 과정에서 새로 계산하거나 관리 목적으로 만든 값

## 2. 컬럼별 구분

| 컬럼 | 구분 | 원본 수집값인가 | 설명 |
|---|---|---|---|
| `source` | 관리값 | 아니오 | 어느 원천 파일에서 왔는지 통합 과정에서 부여 |
| `source_file` | 관리값 | 아니오 | 원천 파일 경로를 통합 과정에서 부여 |
| `source_artwork_id` | 원본 수집값 | 예 | 원본의 artwork_id, Handle, idx 등을 표준 컬럼으로 매핑 |
| `artist_name_raw` | 원본 수집값 | 예 | 원본 작가명 |
| `artist_slug` | 원본 수집값 | 예 | 원본 slug, Handle, name_eng 등 |
| `title` | 원본 수집값 | 예 | 원본 작품명 |
| `year_made` | 원본 파싱값 | 부분적 | 원본 연도/date 문자열에서 숫자 추출 |
| `medium_raw` | 원본 수집값 | 예 | 원본 재료 문자열 |
| `medium_category` | 정규화/분류값 | 부분적 | 원본에 있으면 사용, 없으면 규칙으로 분류 |
| `support_category` | 정규화/분류값 | 부분적 | 원본 support 값 또는 재료 문자열에서 추정 |
| `width_cm` | 원본 파싱값 | 부분적 | 원본 width 또는 dimensions/size 문자열에서 숫자 추출 |
| `height_cm` | 원본 파싱값 | 부분적 | 원본 height 또는 dimensions/size 문자열에서 숫자 추출 |
| `depth_cm` | 원본 파싱값 | 부분적 | 원본 depth 또는 dimensions 문자열에서 숫자 추출 |
| `has_depth` | 파생값 | 아니오 | depth_cm이 있으면 1, 없으면 0으로 계산 |
| `area_cm2` | 파생값 | 아니오 | width_cm × height_cm |
| `log_area` | 파생값 | 아니오 | log1p(area_cm2) |
| `aspect_ratio` | 파생값 | 아니오 | width_cm / height_cm |
| `estimated_ho` | 원본/파생 혼합 | 부분적 | Saatchi 쪽은 기존 ho 값 사용, 일부 출처는 없음 |
| `price_krw` | 원본/정규화 혼합 | 부분적 | 원본 KRW 또는 사전 환산된 KRW 값 |
| `ln_price` | 파생값 | 아니오 | log(price_krw) |
| `price_raw` | 원본 수집값 | 예 | 원본 가격 문자열 |
| `price_currency` | 원본/보정값 | 부분적 | 원본 통화값이 있으면 사용, 일부는 KRW/USD로 보정 |
| `artwork_url` | 원본 수집값 | 예 | 원본 작품 URL |
| `image_url` | 원본 수집값 | 예 | 원본 이미지 URL |
| `gallery_name` | 원본 수집값 | 예 | 원본 갤러리명 또는 플랫폼명 |
| `gallery_tier` | 제외 | 제외 | 별도 갤러리 티어 검증 대상으로 분리 |
| `is_excluded_for_training` | 원본/관리 혼합 | 부분적 | 원본에 있으면 사용, 없으면 0으로 채움 |
| `exclude_reason` | 원본/관리 혼합 | 부분적 | 원본에 있으면 사용, 없으면 비워둠 |

## 3. 실제 원본 수집값으로 우선 볼 수 있는 컬럼

- `source_artwork_id`
- `artist_name_raw`
- `artist_slug`
- `title`
- `medium_raw`
- `price_raw`
- `artwork_url`
- `image_url`
- `gallery_name`

## 4. 원본이 아니라 통합 과정에서 만들어진 컬럼

- `source`
- `source_file`
- `has_depth`
- `area_cm2`
- `log_area`
- `aspect_ratio`
- `ln_price`

## 5. 원본과 통합 로직이 섞인 컬럼

- `year_made`
- `medium_category`
- `support_category`
- `width_cm`
- `height_cm`
- `depth_cm`
- `estimated_ho`
- `price_krw`
- `price_currency`
- `is_excluded_for_training`
- `exclude_reason`

## 6. 출처별 매핑 요약

### Saatchi

- 원본 파일: `data/saatchi_cleaned.csv`
- 이미 한 번 정리된 파일이므로 순수 크롤링 원본은 아님
- 원본에 가까운 값
- `artwork_id`, `artist_name`, `artist_slug`, `title`, `medium`, `price_raw`, `image_url`, `artwork_url`, `gallery_name`
- 이미 정리/파생되어 있던 값
- `price_krw`, `medium_category`, `support_type`, `ho`, `is_excluded_for_training`, `exclude_reason`
- 통합 과정에서 다시 계산한 값
- `width_cm`, `height_cm`, `depth_cm`, `area_cm2`, `log_area`, `aspect_ratio`, `ln_price`

### Artsy

- 원본 파일: `data/artsy_kr_artworks.csv`
- 원본에 가까운 값
- `artwork_id`, `artist_name`, `artist_slug`, `title`, `medium`, `price_raw`, `price_currency`, `image_url`, `artwork_url`, `gallery_name`
- 원본에 이미 숫자로 들어 있던 값
- `width_cm`, `height_cm`, `depth_cm`, `price_krw`
- 통합 과정에서 만든 값
- `medium_category`, `support_category`, `area_cm2`, `log_area`, `aspect_ratio`, `ln_price`
- 주의
- `date`에서 `year_made`를 숫자로 뽑는 과정에서 `4800000` 같은 잘못된 연도 파싱이 발생함

### Artue

- 원본 파일: `data/artue_테스트_가격포함.csv`
- 원본에 가까운 값
- `Artist`, `Title`, `Year`, `Medium (EN)`, `Medium (KO)`, `Price (KRW)`, `URL`, `Handle`
- 원본에 숫자로 들어 있던 값
- `Width (cm)`, `Height (cm)`, `Depth (cm)`
- 통합 과정에서 만든 값
- `medium_category`, `support_category`, `area_cm2`, `log_area`, `aspect_ratio`, `ln_price`

### Gallery primary

- 원본 파일: `data/1차 시장 데이터 - 전달본_260504.csv`
- 원본에 가까운 값
- `idx`, `name_kor`, `name_eng`, `title`, `materials`, `price_raw`, `price`, `img_src`, `gallery_name(KR)`, `gallery_name(EN)`
- 원본에 숫자로 들어 있던 값
- `width`, `height`
- 통합 과정에서 만든 값
- `medium_category`, `support_category`, `area_cm2`, `log_area`, `aspect_ratio`, `ln_price`
- 주의
- 가격대가 다른 출처보다 높아 별도 시장군 또는 고가 갤러리 데이터로 볼지 검토 필요

## 7. 우선 검증해야 할 컬럼

- `price_krw`
- 원본 가격인지, 환산/파싱 가격인지 출처별로 구분 필요
- `width_cm`, `height_cm`, `depth_cm`
- 크기 문자열에서 파싱된 값이 실제 가로/세로/깊이에 맞는지 샘플 검증 필요
- `year_made`
- Artsy의 date 파싱 오류가 있어 정리 필요
- `medium_category`, `support_category`
- 원본 수집값이 아니라 분류값이므로, 원본 `medium_raw` 기준 재검증 필요
- `estimated_ho`
- 출처별 생성 방식이 다르거나 결측이 많아 통일 규칙 필요

## 8. 다음 작업

- `raw_collected`에 가까운 원본 보존용 데이터와 `model_ready` 데이터 구분
- 원본값 컬럼과 파생값 컬럼의 suffix 또는 문서 기준 확정
- cleaned v2에서 아래 컬럼군을 분리
- 원본 보존 컬럼
- 통합 표준 컬럼
- 파생 학습 컬럼
- 감사/관리 컬럼

