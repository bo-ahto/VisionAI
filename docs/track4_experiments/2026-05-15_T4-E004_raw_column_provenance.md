# T4-E004 raw 통합본 컬럼 출처 구분

- 실험 ID: `T4-E004_raw_column_provenance`
- 연결 가설: `T4-H0`
- 날짜: 2026-05-15
- 상태: 완료

## 1. 목적

- `track4_primary_market_raw_unified.csv`에 실제 크롤링 수집값과 통합 과정에서 만든 값이 섞여 있는지 구분함
- 갤러리 티어는 별도 검증 대상이므로 제외함
- 원본 데이터 통합이 우선이라는 기준에 맞춰, 어떤 컬럼을 원본값으로 믿을 수 있는지 정리함

## 2. 결과 문서

- `docs/track4_raw_unified_column_provenance.md`

## 3. 핵심 결론

- raw 통합본은 순수 원본 수집값만 있는 파일이 아님
- 원본 수집값, 원본 파싱값, 정규화/분류값, 파생/관리값이 섞여 있음
- 특히 `area_cm2`, `log_area`, `aspect_ratio`, `ln_price`, `has_depth`는 원본 수집값이 아니라 통합 과정에서 만든 값임

## 4. 원본 수집값으로 우선 볼 수 있는 컬럼

- `source_artwork_id`
- `artist_name_raw`
- `artist_slug`
- `title`
- `medium_raw`
- `price_raw`
- `artwork_url`
- `image_url`
- `gallery_name`

## 5. 통합 과정에서 만들어진 컬럼

- `source`
- `source_file`
- `has_depth`
- `area_cm2`
- `log_area`
- `aspect_ratio`
- `ln_price`

## 6. 원본과 통합 로직이 섞인 컬럼

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

## 7. 후속 판단

- 다음 cleaned 버전에서는 원본 보존 컬럼과 파생 학습 컬럼을 더 명확히 나누는 것이 좋음
- 예시
- 원본 보존: `raw_*`
- 통합 표준: `*_standardized`
- 파생 학습: `feature_*`
- 감사/관리: `audit_*`

