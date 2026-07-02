# Saatchi / Artsy 원본 데이터 표준화 병합 패키지

- 목적
  - Saatchi 원본 데이터와 Artsy 원본 데이터를 같은 컬럼 구조로 맞춘다.
  - 표준화된 두 CSV를 하나의 CSV로 합친다.
  - 같은 폴더 안의 원본 파일만 사용해서 단독 실행되게 한다.

## 포함 파일

- `01_source/saatchi_kr_artworks.csv`
  - Saatchi 원본 후보 파일
  - 원본 위치: `/Users/bo/VisionAI/data/saatchi_kr_artworks.csv`
- `01_source/artsy_kr_artworks.csv`
  - Artsy 원본 후보 파일
  - 원본 위치: `/Users/bo/VisionAI/data/artsy_kr_artworks.csv`
- `standardize_and_merge_saatchi_artsy.py`
  - 두 원본 CSV를 표준 컬럼으로 변환한 뒤 병합하는 단독 실행 스크립트

## 처리 범위

- 하는 일
  - 원본 CSV 읽기
  - 플랫폼별 컬럼명을 공통 컬럼명으로 맞추기
  - 숫자 컬럼의 쉼표, 통화 기호, 공백 정리
  - Saatchi의 `artist_first_name` + `artist_last_name`을 `artist_name`으로 결합
  - Artsy의 `date`에서 4자리 연도만 `artwork_year`로 추출
  - 원본 추적용 `source`, `source_artwork_id`, `source_row_index` 생성
  - 표준화된 Saatchi / Artsy 파일과 병합 파일 출력

- 하지 않는 일
  - 가격 예측
  - 가격 재계산
  - 작가별 가격 통계 생성
  - 작품별 파생 통계 생성
  - 유사작품 그룹핑
  - 모델 학습용 피처 생성
  - DB 조회
  - 외부 CSV lookup

## 실행 방법

```bash
cd /Users/bo/VisionAI/docs/track4/saatchi_artsy_standardization_package_20260622
python3 standardize_and_merge_saatchi_artsy.py
```

스크립트는 실행 위치와 무관하게 자기 파일 위치를 기준으로 `01_source`와 `02_output`을 찾는다.

## 출력 파일

- `02_output/saatchi_standardized.csv`
- `02_output/artsy_standardized.csv`
- `02_output/saatchi_artsy_standardized_merged.csv`
- `02_output/standardization_summary.json`

## 표준화 기준

- 원본 추적
  - `source`
  - `source_artwork_id`
  - `source_row_index`

- 가격 컬럼
  - `price_krw`
  - `price_usd`
  - `price_raw`
  - `price_currency`
  - `price_amount`

- 크기 컬럼
  - `width_cm`
  - `height_cm`
  - `depth_cm`
  - `dimensions_raw`

- 작가 컬럼
  - `artist_id_or_slug`
  - `artist_name`
  - `artist_first_name`
  - `artist_last_name`
  - `artist_nationality`
  - `artist_birth_year`
  - `artist_country`

- 작품 정보 컬럼
  - `medium_raw`
  - `medium_category_raw`
  - `medium_type_raw`
  - `materials_raw`
  - `support_or_category_raw`
  - `subject_raw`
  - `style_raw`
  - `orientation_raw`
  - `size_bin_raw`
