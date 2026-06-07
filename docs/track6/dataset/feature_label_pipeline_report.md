# Track 6 feature/label 분리 파이프라인 보고서

- 생성일: `2026-05-18`
- 상태: `pass`
- 목적: 모델 입력 파일에서 가격/정답/출처성 컬럼을 물리적으로 분리해 누수 가능성을 줄임

## 1. 사용 원칙

- 학습/예측 코드는 `features` 파일만 읽음
- 평가 코드는 `labels` 파일을 별도로 읽어 예측값과 결합함
- validation labels는 모델/피처 선택에만 사용함
- test labels는 최종 후보 확정 후 최종 평가에만 사용함

## 2. 제거 기준

- feature 파일에서 제거하는 컬럼
  - `price`, `krw`, `usd`, `currency`, `amount`, `sold`, `sale`, `cost`, `fee` 패턴 포함 컬럼
  - `track4_source`, `source_artwork_id`, URL, image URL 등 출처/추적 컬럼
  - target 컬럼 `price_krw`, `ln_price_krw`
- 예외
  - `estimated_ho`는 가격이 아니라 작품 크기 호수 추정값이므로 제거하지 않음

## 3. 산출물

| task | split | feature rows | feature cols | label rows | label cols | 제거 컬럼 | 누수 의심 컬럼 |
|---|---|---:|---:|---:|---:|---|---|
| `warm` | `train` | `26,914` | `17` | `26,914` | `12` | `artist_entity_suffix`, `artist_meta_birth_year`, `artist_meta_career_age`, `artist_meta_career_stage`, `artist_meta_followers`, `artist_meta_for_sale_ratio`, `artist_meta_for_sale_works`, `artist_meta_has_international`, `artist_meta_is_p1`, `artist_meta_nationality`, `artist_meta_nationality_ko`, `artist_meta_source`, `artist_meta_total_works`, `artist_name_ko`, `artist_name_ko_orig`, `artist_name_standardized`, `artwork_url`, `cleaning_exclude_reasons`, `collected_material_raw`, `image_url`, `is_high_price_candidate`, `is_homonym`, `ln_price_krw`, `nant_material_idx`, `nant_material_match_method`, `nant_material_note`, `nant_support`, `nant_tool`, `price_krw`, `source_artwork_id`, `title_raw`, `track4_source`, `track4_source_row_index` | - |
| `warm` | `val_warm` | `519` | `17` | `519` | `12` | `artist_entity_suffix`, `artist_meta_birth_year`, `artist_meta_career_age`, `artist_meta_career_stage`, `artist_meta_followers`, `artist_meta_for_sale_ratio`, `artist_meta_for_sale_works`, `artist_meta_has_international`, `artist_meta_is_p1`, `artist_meta_nationality`, `artist_meta_nationality_ko`, `artist_meta_source`, `artist_meta_total_works`, `artist_name_ko`, `artist_name_ko_orig`, `artist_name_standardized`, `artwork_url`, `cleaning_exclude_reasons`, `collected_material_raw`, `image_url`, `is_high_price_candidate`, `is_homonym`, `ln_price_krw`, `nant_material_idx`, `nant_material_match_method`, `nant_material_note`, `nant_support`, `nant_tool`, `price_krw`, `source_artwork_id`, `title_raw`, `track4_source`, `track4_source_row_index` | - |
| `warm` | `test_warm` | `607` | `17` | `607` | `12` | `artist_entity_suffix`, `artist_meta_birth_year`, `artist_meta_career_age`, `artist_meta_career_stage`, `artist_meta_followers`, `artist_meta_for_sale_ratio`, `artist_meta_for_sale_works`, `artist_meta_has_international`, `artist_meta_is_p1`, `artist_meta_nationality`, `artist_meta_nationality_ko`, `artist_meta_source`, `artist_meta_total_works`, `artist_name_ko`, `artist_name_ko_orig`, `artist_name_standardized`, `artwork_url`, `cleaning_exclude_reasons`, `collected_material_raw`, `image_url`, `is_high_price_candidate`, `is_homonym`, `ln_price_krw`, `nant_material_idx`, `nant_material_match_method`, `nant_material_note`, `nant_support`, `nant_tool`, `price_krw`, `source_artwork_id`, `title_raw`, `track4_source`, `track4_source_row_index` | - |
| `cold` | `train` | `26,914` | `14` | `26,914` | `12` | `artist_entity_suffix`, `artist_key`, `artist_meta_birth_year`, `artist_meta_career_age`, `artist_meta_career_stage`, `artist_meta_followers`, `artist_meta_for_sale_ratio`, `artist_meta_for_sale_works`, `artist_meta_has_international`, `artist_meta_is_p1`, `artist_meta_nationality`, `artist_meta_nationality_ko`, `artist_meta_source`, `artist_meta_total_works`, `artist_name_ko`, `artist_name_ko_orig`, `artist_name_standardized`, `artist_works_count_train`, `artist_works_log`, `artwork_url`, `cleaning_exclude_reasons`, `collected_material_raw`, `image_url`, `is_high_price_candidate`, `is_homonym`, `ln_price_krw`, `nant_material_idx`, `nant_material_match_method`, `nant_material_note`, `nant_support`, `nant_tool`, `price_krw`, `source_artwork_id`, `title_raw`, `track4_source`, `track4_source_row_index` | - |
| `cold` | `val_cold` | `2,753` | `14` | `2,753` | `12` | `artist_entity_suffix`, `artist_key`, `artist_meta_birth_year`, `artist_meta_career_age`, `artist_meta_career_stage`, `artist_meta_followers`, `artist_meta_for_sale_ratio`, `artist_meta_for_sale_works`, `artist_meta_has_international`, `artist_meta_is_p1`, `artist_meta_nationality`, `artist_meta_nationality_ko`, `artist_meta_source`, `artist_meta_total_works`, `artist_name_ko`, `artist_name_ko_orig`, `artist_name_standardized`, `artist_works_count_train`, `artist_works_log`, `artwork_url`, `cleaning_exclude_reasons`, `collected_material_raw`, `image_url`, `is_high_price_candidate`, `is_homonym`, `ln_price_krw`, `nant_material_idx`, `nant_material_match_method`, `nant_material_note`, `nant_support`, `nant_tool`, `price_krw`, `source_artwork_id`, `title_raw`, `track4_source`, `track4_source_row_index` | - |
| `cold` | `test_cold` | `3,099` | `14` | `3,099` | `12` | `artist_entity_suffix`, `artist_key`, `artist_meta_birth_year`, `artist_meta_career_age`, `artist_meta_career_stage`, `artist_meta_followers`, `artist_meta_for_sale_ratio`, `artist_meta_for_sale_works`, `artist_meta_has_international`, `artist_meta_is_p1`, `artist_meta_nationality`, `artist_meta_nationality_ko`, `artist_meta_source`, `artist_meta_total_works`, `artist_name_ko`, `artist_name_ko_orig`, `artist_name_standardized`, `artist_works_count_train`, `artist_works_log`, `artwork_url`, `cleaning_exclude_reasons`, `collected_material_raw`, `image_url`, `is_high_price_candidate`, `is_homonym`, `ln_price_krw`, `nant_material_idx`, `nant_material_match_method`, `nant_material_note`, `nant_support`, `nant_tool`, `price_krw`, `source_artwork_id`, `title_raw`, `track4_source`, `track4_source_row_index` | - |

## 4. 해석

- feature 파일의 누수 의심 컬럼이 0개이면 모델 실험은 feature 파일 기준으로 진행 가능
- Warm 모델은 `features/warm` 파일만 읽음
- Cold 모델은 작가 식별/작가 이력 컬럼이 제거된 `features/cold` 파일만 읽음
- full split 파일은 감사/재생성용으로 보존하되 모델 코드에서 직접 읽지 않음
- labels 파일은 평가 스크립트에서만 사용함
