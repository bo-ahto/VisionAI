# Track6 작가 메타 feature 보강 보고서

- 생성일: `2026-05-27`
- 대상 split: `data/track6_split_with_year_type_edition_size_artist_name`
- 목적: Group E 작가 변수 실험을 위해 기존 split 멤버십은 유지하고 feature 파일에 작가 메타를 추가
- 원칙: 가격/라벨/출처 컬럼은 feature에 추가하지 않음

## 1. 추가 컬럼

- `artist_works_log`
- `artist_meta_birth_year`
- `artist_meta_career_stage`
- `artist_meta_nationality`
- `artist_meta_total_works`
- `artist_meta_for_sale_works`
- `artist_meta_followers`
- `artist_meta_is_p1`
- `artist_works_log_is_missing`
- `artist_meta_birth_year_is_missing`
- `artist_meta_career_stage_is_missing`
- `artist_meta_total_works_is_missing`
- `artist_meta_for_sale_works_is_missing`
- `artist_meta_followers_is_missing`
- `artist_meta_is_p1_is_missing`
- `artist_meta_nationality_is_missing`
- `artist_meta_available_count`
- `artist_meta_completeness_score`
- `artist_exhibition_solo_count`
- `artist_exhibition_solo_count_is_missing`
- `artist_exhibition_group_count`
- `artist_exhibition_group_count_is_missing`
- `artist_exhibition_fair_count`
- `artist_exhibition_fair_count_is_missing`
- `artist_exhibition_total_count`
- `artist_exhibition_available_count`

## 2. 파일별 보강 결과

| 파일 | rows | columns before | columns after | join 누락 rows |
|---|---:|---:|---:|---:|
| `data/track6_split_with_year_type_edition_size_artist_name/features/warm/track6_train_warm_features.csv` | `26,914` | `74` | `75` | `0` |
| `data/track6_split_with_year_type_edition_size_artist_name/features/warm/track6_val_warm_warm_features.csv` | `519` | `73` | `74` | `0` |
| `data/track6_split_with_year_type_edition_size_artist_name/features/warm/track6_test_warm_warm_features.csv` | `607` | `74` | `75` | `0` |
| `data/track6_split_with_year_type_edition_size_artist_name/features/cold/track6_train_cold_features.csv` | `26,914` | `70` | `72` | `0` |
| `data/track6_split_with_year_type_edition_size_artist_name/features/cold/track6_val_cold_cold_features.csv` | `2,753` | `70` | `72` | `0` |
| `data/track6_split_with_year_type_edition_size_artist_name/features/cold/track6_test_cold_cold_features.csv` | `3,099` | `71` | `73` | `0` |

## 3. 해석

- `artist_meta_*_is_missing`은 값이 비어 있는지 알려주는 결측 flag
- `artist_meta_available_count`는 사용 가능한 작가 메타 개수
- `artist_meta_completeness_score`는 사용 가능한 작가 메타 비율
- `artist_meta_source`는 출처 편향 위험이 있어 feature 파일에는 추가하지 않음
- `artist_meta_for_sale_ratio`, `artist_meta_has_international`, `artist_meta_career_age`는 값 품질 문제가 있어 이번 보강에서 제외
- `artist_exhibition_*_count`는 원본 `saatchi__solo_count/group_count/fair_count`에서 가져온 값
- 전시 횟수 컬럼의 `200` 초과 값은 연도가 잘못 들어간 것으로 보고 결측 처리
