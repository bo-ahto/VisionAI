# Raw Files By Month And Platform

이 폴더는 종합 표준화본이 아니라 월/플랫폼별 raw CSV를 따로 확인하기 위한 폴더다.

## 생성 기준

- 5월 Artsy raw: 기존 실험 원본 `legacy_artsy_kr_artworks.csv`
- 5월 Saatchi raw: 기존 실험 원본 `legacy_saatchi_cleaned.csv`
- 6월 Artsy raw: 2026-06 신규 수집 원본 `source_platform_artsy_kr_artworks.csv`
- 6월 Saatchi raw: 2026-06 신규 수집 원본 `source_platform_saatchi_kr_artworks_split_13102.csv`

## 처리 원칙

- 종합 표준화, 중복 제거, 필터링, 통화 변환을 하지 않는다.
- 원본 row 수와 원본 컬럼 순서를 유지한다.
- 단, Artsy/Saatchi의 `price_krw`는 수집 과정에서 고정 환율로 계산된 값이므로 제거한다.
- `price_krw` 외 컬럼은 제거하거나 보정하지 않는다.

## 파일

- `202605_artsy_raw_no_calculated_price_krw.csv`
  - 원본: `01_source_raw/legacy_experiment_sources/legacy_artsy_kr_artworks.csv`
  - 행 수: 30,046
  - 제거 컬럼: `price_krw`

- `202605_saatchi_raw_no_calculated_price_krw.csv`
  - 원본: `01_source_raw/legacy_experiment_sources/legacy_saatchi_cleaned.csv`
  - 행 수: 21,721
  - 제거 컬럼: `price_krw`

- `202606_artsy_raw_no_calculated_price_krw.csv`
  - 원본: `01_source_raw/source_platform_latest/source_platform_artsy_kr_artworks.csv`
  - 행 수: 31,518
  - 제거 컬럼: `price_krw`

- `202606_saatchi_raw_no_calculated_price_krw.csv`
  - 원본: `01_source_raw/source_platform_latest/source_platform_saatchi_kr_artworks_split_13102.csv`
  - 행 수: 13,102
  - 제거 컬럼: `price_krw`

- `raw_by_month_platform_summary.json`
  - 각 파일의 원본 경로, 출력 경로, 행 수, 컬럼 수, 제거 컬럼을 기록한 요약 파일이다.
