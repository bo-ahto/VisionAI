# Track 4 1차 시장 데이터 통합 계획

- 목적: Track 4에서 사용할 기준 데이터셋을 Track 3 통합 데이터 재사용이 아니라, 기존에 수집된 1차 시장 데이터를 다시 모아 클렌징하는 방식으로 생성함
- 기준일: 2026-05-15
- 작성 방식: 개조식

## 1. 기본 방향

- Track 4는 split부터 시작하지 않음
- 먼저 파편화된 1차 시장 데이터를 원본 컬럼 그대로 모음
- 그다음 공통 schema로 표준화함
- 그다음 가격, 작가명, 작품명, 크기, 재료, 지지체를 정리함
- 마지막에 학습 / 검증 / 테스트, Warm / Cold split을 생성함

## 2. 포함 대상

- 실제 가격이 있는 1차 시장 데이터만 포함함
- 우선 포함 파일
- `data/saatchi_cleaned.csv`
- `data/artsy_kr_artworks.csv`
- `data/artue_테스트_가격포함.csv`
- `data/1차 시장 데이터 - 전달본_260504.csv`
- 제외 원칙
- 예측값만 있는 파일은 제외함
- 예: `printbakery_predictions.csv`, `artue_price_predictions.csv`
- 모델 결과 파일은 제외함
- Golden set은 최종 검증 후보로 남기고, 초기 학습 통합에는 넣지 않음

## 3. 1차 통합 schema

- `source`
- 데이터 출처
- `source_file`
- 원본 파일명
- `source_artwork_id`
- 원본 작품 ID
- `artist_name_raw`
- 원본 작가명
- `artist_slug`
- 원본 작가 slug 또는 ID
- `title`
- 작품명
- `year_made`
- 제작연도
- `medium_raw`
- 원본 재료 문자열
- `medium_category`
- 1차 정리된 재료 구분
- `support_category`
- 1차 정리된 지지체 구분
- `width_cm`
- 가로 cm
- `height_cm`
- 세로 cm
- `depth_cm`
- 깊이 cm
- `has_depth`
- 깊이 정보 여부
- `area_cm2`
- 면적
- `log_area`
- 로그 면적
- `aspect_ratio`
- 가로/세로 비율
- `estimated_ho`
- 호수 또는 호수 추정값
- `price_krw`
- 학습 정답 가격
- `ln_price`
- 로그 가격
- `price_raw`
- 원본 가격 문자열
- `price_currency`
- 원본 통화
- `artwork_url`
- 작품 URL
- `image_url`
- 이미지 URL
- `gallery_name`
- 갤러리명
- `gallery_tier`
- 갤러리 티어
- `is_excluded_for_training`
- 학습 제외 후보 여부
- `exclude_reason`
- 제외 사유

## 4. 클렌징 원칙

- 가격
- KRW 기준 양수 가격만 학습 후보로 유지함
- 원본 가격 문자열은 보존함
- 로그 가격 `ln_price`를 생성함
- 크기
- width / height / depth를 cm 기준 숫자로 통일함
- 크기 문자열만 있는 경우 가능한 범위에서 파싱함
- width, height가 모두 있으면 `area_cm2`, `log_area`, `aspect_ratio`를 생성함
- 재료
- 원본 재료 문자열은 보존함
- 이미 정리된 `medium_category`가 있으면 우선 사용함
- 없는 경우 1차 규칙 기반으로 oil, acrylic, watercolor, pigment, print, photo, sculpture, mixed, other 등으로 매핑함
- 지지체
- 이미 정리된 support 값이 있으면 우선 사용함
- 없으면 medium/material 문자열에서 canvas, paper, panel, linen, wood, metal, other 등을 1차 추정함
- 작가
- 원본 작가명은 그대로 보존함
- 공백 정리와 빈 값 제거만 먼저 수행함
- 동명이인 통합/분리는 후속 단계에서 별도 처리함

## 5. 산출물

- 원본 보존 통합 데이터
- `data/track4_primary_market_raw_collected.csv`
- 원본 보존 통합 요약
- `data/track4_primary_market_raw_collected_summary.json`
- 원본 보존 생성 스크립트
- `scripts/track4/build_primary_market_raw_collected.py`
- 표준화 raw 통합 데이터
- `data/track4_primary_market_raw_unified.csv`
- 표준화 raw 통합 요약
- `data/track4_primary_market_raw_unified_summary.json`
- 표준화 raw 생성 스크립트
- `scripts/track4/build_primary_market_unified.py`

## 6. 현재 원본 보존 통합 결과

- 생성일: 2026-05-15
- 통합 파일
- `data/track4_primary_market_raw_collected.csv`
- 요약 파일
- `data/track4_primary_market_raw_collected_summary.json`
- 통합 규모
- 전체 rows: `54,842`
- 전체 columns: `132`
- 출처별 rows
- Saatchi: `21,721`
- Artsy: `30,046`
- Artue: `2,783`
- Gallery primary: `292`
- 처리 방식
- 원천 파일의 컬럼명을 `<source>__<original_column>` 형태로 보존함
- 다른 출처에 없는 컬럼은 빈칸으로 둠
- 가격 파싱, 크기 파싱, 재료 분류, 파생값 생성을 하지 않음
- 추가한 컬럼은 추적용 3개뿐임
- `track4_source`
- `track4_source_file`
- `track4_source_row_index`

## 7. 현재 표준화 raw 통합 결과

- 생성일: 2026-05-15
- 통합 파일
- `data/track4_primary_market_raw_unified.csv`
- 요약 파일
- `data/track4_primary_market_raw_unified_summary.json`
- 통합 규모
- 전체 통합 rows: `33,276`
- 기본 학습 후보 rows: `33,182`
- 원본 작가명 기준 작가 수: `2,242`
- 출처별 rows
- Saatchi: `20,278`
- Artsy: `10,111`
- Artue: `2,599`
- Gallery primary: `288`
- 기본 결측률
- 작가명: `0.00%`
- 가격: `0.00%`
- 작품명: `0.003%`
- 가로/세로: `0.28%`
- 깊이: `25.58%`
- 호수: `39.06%`
- 가격 분포
- 중앙값: `3,000,000원`
- Q25: `1,242,000원`
- Q75: `7,245,000원`
- 최대값: `55,200,000,000원`

## 8. 현재 확인된 주의점

- `track4_primary_market_raw_collected.csv`가 최상위 원본 보존 파일임
- `track4_primary_market_raw_unified.csv`는 이미 표준화/파생값이 일부 들어간 중간 산출물임
- `track4_primary_market_cleaned_v1.csv`는 감사 규칙을 반영한 1차 클렌징 산출물임
- cleaned 파일은 아직 최종 학습 데이터가 아님
- 가격 이상치가 남아 있음
- 예: 매우 낮은 가격, 수백억 단위 가격
- 출처별 가격 분포 차이가 큼
- Gallery primary는 다른 출처보다 가격대가 높음
- depth와 estimated_ho 결측이 많음
- 작가명은 아직 원본 문자열 기준임
- 동명이인, 영문/한글명 통합, 표기 흔들림은 아직 정리 전임
- `source`는 감사/분포 확인용으로 보존하되 운영 입력 피처로 사용하지 않음

## 9. 다음 단계

- 1단계: 원천 파일 원본 보존 통합
- 완료: `track4_primary_market_raw_collected.csv`
- 2단계: 표준화 raw 통합
- 진행 중: `track4_primary_market_raw_unified.csv`
- 3단계: 가격/크기/재료/작가명 결측률 점검
- 진행 중
- 4단계: 학습 제외 조건 정의
- 진행 중: `track4_primary_market_cleaned_v1.csv`
- 5단계: 작가명 정규화 및 동명이인 후보 점검
- 6단계: Track 4 기준 split 생성
- 7단계: Warm / Cold baseline 재평가
