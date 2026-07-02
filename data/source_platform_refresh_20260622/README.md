# Source Platform Refresh 2026-06-22

이 폴더는 Artsy/Saatchi 원천 플랫폼 재수집과 1차 정리 산출물을 관리한다.

## 목적

- AHTO 뷰어에 저장된 JSON뿐 아니라 원본 플랫폼에서 최신 데이터를 수집한다.
- 기존 실험 데이터와 추가 수집 데이터를 함께 관리한다.
- 기존 `data/`의 학습/실험 입력 파일을 덮어쓰지 않도록 별도 폴더에 저장한다.
- 앞으로는 1차 정리 CSV를 baseline으로 사용해 기존 작품 이후의 새 작품을 증분 수집한다.

## 폴더

- `artsy_latest/`: Artsy 수집 결과
- `saatchi_latest/`: Saatchi 단일 검색 수집 결과
- `saatchi_latest_split/`: Saatchi size 구간별 확장 수집 결과
- `csv_collected_20260622/`: 기존 원본 + 추가 수집본의 1차 정리 패키지
- `scripts/`: 수집 실행 스크립트

## 증분 수집 기준

앞으로 새로 수집할 때는 기본적으로 `csv_collected_20260622/03_outputs`의 1차 정리 CSV를 baseline으로 사용한다.
baseline에 이미 있는 작품은 `source_artwork_id`와 `artwork_url` 기준으로 건너뛰고, 새로 발견된 작품만 출력 폴더에 저장한다.

기본 baseline 후보:

- `csv_collected_20260622/03_outputs/standardized_artworks_merged_deduped.csv`
- `csv_collected_20260622/03_outputs/standardized_artworks_merged_deduped_0622.csv`

현재 baseline 기준 skip 규모:

- Artsy 기존 작품 ID: 10,830건
- Saatchi 기존 작품 ID/URL: 28,289건

## 실행

Artsy 증분 수집:

```bash
cd /Users/bo/VisionAI/data/source_platform_refresh_20260622
python3 scripts/run_artsy_latest_from_platform.py
```

Saatchi 증분 수집:

```bash
cd /Users/bo/VisionAI/data/source_platform_refresh_20260622
python3 scripts/run_saatchi_latest_split_from_platform.py
```

전체 재수집이 필요할 때:

```bash
python3 scripts/run_artsy_latest_from_platform.py --full-refresh
python3 scripts/run_saatchi_latest_split_from_platform.py --full-refresh
```

특정 baseline을 명시할 때:

```bash
python3 scripts/run_saatchi_latest_split_from_platform.py \
  --baseline-csv csv_collected_20260622/03_outputs/standardized_artworks_merged_deduped_0622.csv
```

## 기존 수집 방식

### Artsy

- 코드: `scripts/crawl_artsy_complete.py`
- 방식: Artsy GraphQL API 호출
- 주요 필터:
  - `artistNationalities`: `South Korean`, `Korean`
  - `locationCities`: `Seoul, South Korea`, `Busan, South Korea`
  - 카테고리/재료/정렬 조건을 여러 배치로 나눠 10K 제한을 우회
- 추가 수집:
  - 작품 5건 이상 작가의 전시 이력
- 증분 수집:
  - `source_family=artsy`의 기존 `source_artwork_id`를 baseline으로 사용

### Saatchi

- 권장 코드: `scripts/run_saatchi_latest_split_from_platform.py`
- 방식:
  - Constructor.io API로 작품 목록 수집
  - `size_bin`별로 나눠 10,000건 제한을 우회
  - 작가 프로필 페이지의 `__NEXT_DATA__`에서 바이오/교육/전시 정보 수집
- 주요 필터:
  - `original_availability_status=avail`
  - `country=south korea`
  - `size_bin=oversized/large/medium/small`
- 증분 수집:
  - `source_family=saatchi`의 기존 `source_artwork_id`, `artwork_url`을 baseline으로 사용

## 출력

Artsy:

- `artsy_latest/artsy_kr_artworks.json`
- `artsy_latest/artsy_kr_artworks.csv`
- `artsy_latest/artsy_kr_artists.json`
- `artsy_latest/artsy_kr_artist_shows.json`
- `artsy_latest/artsy_kr_artists_full.json`
- `artsy_latest/artsy_kr_artists_full.csv`

Saatchi split:

- `saatchi_latest_split/saatchi_kr_artworks.json`
- `saatchi_latest_split/saatchi_kr_artworks.csv`
- `saatchi_latest_split/saatchi_kr_artists.json`
- `saatchi_latest_split/saatchi_split_collection_summary.json`

## 1차 정리와의 관계

- 수집 스크립트는 새 원천 데이터를 가져오는 단계다.
- `csv_collected_20260622`의 1차 정리 단계는 기존 원본과 추가 수집 결과를 합쳐 중복/입체/가격 숫자 없음 등을 정리한다.
- 1차 정리 단계는 환율 변환, 가격 보정, 모델 피처 생성을 하지 않는다.
- 새 수집 결과는 이후 `csv_collected_20260622/01_source_raw`에 추가하고 1차 정리 스크립트를 다시 실행한다.

