# Track 6 작가 메타데이터 보강 보고서

- 생성일: `2026-05-18`
- 입력 정제 데이터: `data/track6/track6_feature_candidates_name_corrected.csv`
- 원본 raw 데이터: `data/track4_primary_market_raw_collected.csv`
- 출력: `data/track6/track6_feature_candidates_name_corrected.csv`
- 전체 rows: `54,842`
- 작가 메타가 1개 이상 붙은 rows: `54,842`

## 1. 처리 원칙

- raw 수집본의 `track4_source + track4_source_row_index`로 row 단위 매칭
- source별 작가 정보 컬럼을 `artist_meta_` 표준 prefix로 통합
- 팔로워/작품 수/판매 중 작품 수 등은 수집된 경우만 보존
- 값이 없는 source는 빈칸으로 둠
- 현재 모델 feature export에서는 `artist_meta_` 컬럼을 기본 제외함
- 추후 작가 DB 연동 또는 별도 가설 실험에서만 명시적으로 사용

## 2. 추가 컬럼

- `artist_meta_source`: `54,842` rows
- `artist_meta_nationality`: `32,827` rows
- `artist_meta_nationality_ko`: `2,033` rows
- `artist_meta_birth_year`: `28,876` rows
- `artist_meta_total_works`: `51,767` rows
- `artist_meta_for_sale_works`: `30,046` rows
- `artist_meta_followers`: `51,767` rows
- `artist_meta_for_sale_ratio`: `21,721` rows
- `artist_meta_career_age`: `0` rows
- `artist_meta_career_stage`: `21,721` rows
- `artist_meta_is_p1`: `51,767` rows
- `artist_meta_has_international`: `21,721` rows

## 3. source별 작가 메타 보유 rows

| source | rows | any artist meta rows |
|---|---:|---:|
| `artsy` | `30,046` | `30,046` |
| `artue` | `2,783` | `2,783` |
| `gallery_primary` | `292` | `292` |
| `saatchi` | `21,721` | `21,721` |

## 4. 주의

- 이 컬럼들은 운영에서 항상 들어오는 입력값이 아님
- 따라서 기본 모델에는 자동 투입하지 않음
- 작가 DB가 준비되면 Warm 전용 또는 신뢰도 판단용 피처로 별도 실험 필요
