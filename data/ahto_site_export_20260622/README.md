# AHTO Artsy / Saatchi 데이터 다운로드

- 목적
  - `https://artsy.ahto.city/`
  - `https://saatchi.ahto.city/`
  - 위 두 데이터 뷰어가 사용하는 JSON을 내려받아 CSV로 변환한다.

- 실행

```bash
cd /Users/bo/VisionAI/data/ahto_site_export_20260622
python3 scripts/download_ahto_artist_artwork_data.py
```

- 출력
  - `raw_json/artsy_artworks.json`
  - `raw_json/artsy_artists.json`
  - `raw_json/saatchi_artworks.json`
  - `raw_json/saatchi_artists.json`
  - `csv/artsy_artworks.csv`
  - `csv/artsy_artists.csv`
  - `csv/saatchi_artworks.csv`
  - `csv/saatchi_artists.csv`
  - `export_summary.json`

- 처리 범위
  - JSON 원본 저장
  - JSON을 CSV로 변환
  - 중첩 필드는 `.` 구분 컬럼으로 펼침

- 하지 않는 일
  - 가격 재계산
  - 작가 키 재생성
  - 작품/작가 매칭 보정
  - 모델 학습용 피처 생성
  - 데이터 정제 규칙 적용
