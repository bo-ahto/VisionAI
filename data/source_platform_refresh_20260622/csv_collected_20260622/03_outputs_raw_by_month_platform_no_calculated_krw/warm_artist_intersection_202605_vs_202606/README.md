# Warm Artist Intersection 202605 vs 202606

이 폴더는 Warm 테스트 데이터 후보를 만들기 위해 5월 raw 데이터와 6월 raw 데이터의 작가 교집합을 플랫폼별로 정리한 결과다.

## 작가 교집합 기준

- Artsy: `artist_slug`
- Saatchi: 5월 `artist_slug`와 6월 `artist_id`

## 작품 신규 여부 기준

- `artwork_id`를 1순위 작품 키로 사용한다.
- `artwork_id`가 비어 있으면 `artwork_url`을 사용한다.
- 둘 다 비어 있으면 작가키, 제목, 크기 정보를 조합한 fallback 키를 사용한다.

## 주요 파일

- `artsy_artist_intersection_202605_vs_202606.csv`
  - 5월과 6월에 모두 등장한 Artsy 작가 1,881명 목록

- `saatchi_artist_intersection_202605_vs_202606.csv`
  - 5월과 6월에 모두 등장한 Saatchi 작가 307명 목록

- `artsy_202606_new_artwork_rows_intersection_artists_not_in_202605.csv`
  - Artsy 교집합 작가의 6월 작품 중 5월 작품 키에 없는 신규 작품 row
  - 행 수: 1,504

- `saatchi_202606_new_artwork_rows_intersection_artists_not_in_202605.csv`
  - Saatchi 교집합 작가의 6월 작품 중 5월 작품 키에 없는 신규 작품 row
  - 행 수: 2,017

- `artsy_202606_new_artwork_rows_intersection_artists_not_in_202605_priced_only.csv`
  - Artsy 신규 작품 row 중 실제 가격 숫자가 있는 row만 남긴 파일
  - `Price on request`, `Sold`, 빈 가격 row 제거
  - 행 수: 693

- `saatchi_202606_new_artwork_rows_intersection_artists_not_in_202605_priced_only.csv`
  - Saatchi 신규 작품 row 중 실제 가격 숫자가 있는 row만 남긴 파일
  - 제거 행 없음
  - 행 수: 2,017

- `artsy_202606_new_artwork_rows_intersection_artists_not_in_202605_removed_no_price.csv`
  - Artsy 신규 작품 row에서 가격 정보가 없어 제거한 row
  - 행 수: 811

- `saatchi_202606_new_artwork_rows_intersection_artists_not_in_202605_removed_no_price.csv`
  - Saatchi 신규 작품 row에서 가격 정보가 없어 제거한 row
  - 행 수: 0

- `artsy_202606_existing_artwork_rows_intersection_artists_already_in_202605.csv`
  - Artsy 교집합 작가의 6월 작품 중 5월에도 같은 작품 키가 있던 row
  - 행 수: 28,919

- `saatchi_202606_existing_artwork_rows_intersection_artists_already_in_202605.csv`
  - Saatchi 교집합 작가의 6월 작품 중 5월에도 같은 작품 키가 있던 row
  - 행 수: 8,814

- `artsy_new_artwork_artist_counts.csv`
  - Artsy 신규 작품 row를 작가별로 집계한 파일

- `saatchi_new_artwork_artist_counts.csv`
  - Saatchi 신규 작품 row를 작가별로 집계한 파일

- `warm_new_artwork_rows_intersection_artists_summary.json`
  - 신규 작품 추출 결과 요약

- `new_artwork_priced_only_filter_summary.json`
  - 가격 없는 row 제거 결과 요약
