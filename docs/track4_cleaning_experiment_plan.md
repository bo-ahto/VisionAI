# Track 4 클렌징 실험 계획

- 목적: `raw_collected` 데이터를 기준으로 모델 피처를 정할 수 있는 수준의 `model_ready` 데이터를 만들기 위한 클렌징 기준 수립
- 기준 파일: `data/track4_primary_market_raw_collected.csv`
- 기준일: 2026-05-15
- 작성 방식: 개조식

## 1. 기본 원칙

- 클렌징은 모델 성능을 올리기 위한 임의 정리가 아님
- 클렌징의 목표는 원본 데이터를 추적 가능한 방식으로 표준화하는 것임
- 원본값은 최대한 보존함
- 표준화값은 별도 컬럼으로 생성함
- 파생 피처는 표준화값이 검증된 뒤 생성함
- 학습 제외 여부는 row 삭제가 아니라 flag와 사유로 남김
- 어떤 규칙으로 값이 바뀌었는지 audit 컬럼에 남김

## 2. 데이터 흐름

- 1단계: 원본 보존
- `track4_primary_market_raw_collected.csv`
- 원천 컬럼 그대로 보존
- 없는 컬럼은 빈칸
- 파싱/정규화/파생 없음

- 2단계: 표준화
- 목표 파일: `track4_primary_market_standardized_v1.csv`
- 출처별 원본 컬럼을 공통 컬럼으로 매핑
- 가격, 작가명, 작품명, 크기, 재료, 지지체, URL 등을 표준화

- 3단계: 클렌징
- 목표 파일: `track4_primary_market_cleaned_v2.csv`
- 이상값, 결측, 중복, 학습 제외 조건을 flag로 정리

- 4단계: 피처 후보 생성
- 목표 파일: `track4_primary_market_feature_candidates_v1.csv`
- 모델 후보 피처를 생성
- 예: log_area, aspect_ratio, ho, material bucket, size bucket

- 5단계: split 생성
- 목표 파일
- `track4_train.csv`
- `track4_val_warm.csv`
- `track4_val_cold.csv`
- `track4_test_warm.csv`
- `track4_test_cold.csv`

## 3. 표준화 대상 컬럼

| 표준 컬럼 | 역할 | 원본 후보 | 검증 방식 |
|---|---|---|---|
| `source` | 출처 | `track4_source` | 출처별 row 수 확인 |
| `source_row_index` | 원본 row 추적 | `track4_source_row_index` | 원본 파일 row 재조회 가능해야 함 |
| `source_artwork_id` | 원본 작품 ID | 각 출처 artwork_id / Handle / idx | 중복 여부 확인 |
| `artist_name_raw` | 원본 작가명 | 출처별 작가명 컬럼 | 결측/숫자/가격 문자열 여부 확인 |
| `artist_name_standardized` | 표준 작가명 | `artist_name_raw` | 공백/대소문자/한영 표기 정리 |
| `title_raw` | 원본 작품명 | 출처별 title 컬럼 | 결측/URL/가격 문자열 여부 확인 |
| `title_standardized` | 표준 작품명 | `title_raw` | 공백/대소문자 정리 |
| `year_made_raw` | 원본 연도 | 출처별 date/year 컬럼 | 원본 문자열 보존 |
| `year_made` | 표준 제작연도 | `year_made_raw` | 1000~2026 범위 확인 |
| `medium_raw` | 원본 재료 | 출처별 medium/material 컬럼 | 결측/가격 문자열 여부 확인 |
| `medium_category` | 표준 재료 | `medium_raw` | 규칙 기반 분류 후 샘플 검증 |
| `support_category` | 표준 지지체 | `medium_raw`, 원본 support 컬럼 | 규칙 기반 분류 후 샘플 검증 |
| `width_cm` | 표준 가로 | width 또는 size/dimensions 문자열 | 양수, 극단값, 단위 확인 |
| `height_cm` | 표준 세로 | height 또는 size/dimensions 문자열 | 양수, 극단값, 단위 확인 |
| `depth_cm` | 표준 깊이 | depth 또는 dimensions 문자열 | 0/결측/극단값 확인 |
| `price_raw` | 원본 가격 | 출처별 price_raw/price | 원본 문자열 보존 |
| `price_krw` | 표준 KRW 가격 | 출처별 KRW/환산 가격 | 양수, 하한/상한, 통화 확인 |
| `artwork_url` | 작품 URL | 출처별 URL | URL 형식 확인 |
| `image_url` | 이미지 URL | 출처별 이미지 URL | URL 형식 확인 |
| `gallery_name_raw` | 원본 갤러리명 | 출처별 gallery 컬럼 | 원본값 보존 |

## 4. 클렌징 가설

| 가설 ID | 목표 | 가설 | 연구 방법 | 성공 기준 |
|---|---|---|---|---|
| T4-C1 | 가격 정합성 | 가격 하한/상한 규칙을 두면 학습을 왜곡하는 가격 오류를 줄일 수 있다 | 출처별 가격 분포와 극단값 샘플 확인 | 제외 사유가 설명 가능하고 후보 데이터가 과도하게 줄지 않음 |
| T4-C2 | 크기 정합성 | 크기 파싱 오류를 제거하면 면적/호수 피처의 신뢰도가 높아진다 | width/height/depth 범위, aspect ratio, 원본 size 문자열 샘플 비교 | 크기 이상값 flag가 명확하고 수동 샘플에서 오류율이 낮음 |
| T4-C3 | 재료/지지체 정합성 | 재료와 지지체를 원본 문자열 기준으로 다시 분류하면 운영 가능한 피처를 만들 수 있다 | medium_raw 기반 rule mapping과 미분류 샘플 확인 | major category coverage가 높고 unknown 비율이 허용 가능 |
| T4-C4 | 작가명 정합성 | 작가명 표준화와 동명이인 후보 점검이 Warm/Cold split 오류를 줄인다 | artist_name_raw 정규화, slug/URL 보조 확인, 동명이인 후보 추출 | 동일 작가 분산과 다른 작가 병합 위험을 문서화 |
| T4-C5 | 중복 정합성 | 동일 작품 중복을 flag로 관리하면 학습 데이터 편향을 줄일 수 있다 | source_artwork_id 중복과 semantic duplicate 비교 | 중복 제거 후보가 원본 row로 추적 가능 |
| T4-C6 | 출처별 시장 차이 | 출처별 가격대 차이를 확인해야 하나의 모델에 합칠 수 있다 | source별 가격/크기/재료 분포 비교 | source를 피처로 쓰지 않아도 분포 차이를 설명 가능 |
| T4-C7 | 갤러리 메타데이터 | 갤러리명/티어는 원본 검증 후에만 보조 메타로 사용할 수 있다 | 기준표 매칭, 미매칭 샘플 검토 | 학습 피처 사용 여부를 보류/채택으로 명확히 판단 |

## 5. 클렌징 순서

- 1순위: 가격
- 이유: target 오류는 모델 전체를 왜곡함
- 먼저 확인할 항목
- 가격 결측
- 0원/음수
- 1만 원 미만
- 10억 원 초과
- 통화/환산 여부

- 2순위: 크기
- 이유: Track 3에서 크기/호수/면적 피처 영향이 컸음
- 먼저 확인할 항목
- width/height 결측
- 0 또는 음수
- 1000cm 초과
- extreme aspect ratio
- depth가 가로/세로로 잘못 들어간 케이스

- 3순위: 작가명
- 이유: Warm / Cold split 기준이 작가명에 의존함
- 먼저 확인할 항목
- 작가명 결측
- 영문/한글 표기 혼재
- slug와 이름 불일치
- 동명이인 후보

- 4순위: 재료/지지체
- 이유: 운영 입력 피처로 사용할 가능성이 높음
- 먼저 확인할 항목
- medium_raw 결측
- medium_category가 원본 수집값인지 분류값인지 구분
- support_category 추정 정확도
- mixed/other/unknown 비율

- 5순위: 중복
- 이유: 동일 작품 중복은 특정 작가/가격대 가중치를 왜곡함
- 먼저 확인할 항목
- 같은 source_artwork_id
- 같은 source + artist + title + price + size
- 출처 간 동일 작품 중복 가능성

- 6순위: 갤러리/출처 메타
- 이유: 운영 입력 피처로 바로 쓰기 어렵지만 데이터 품질 판단에는 필요함
- 먼저 확인할 항목
- gallery_name 결측
- gallery_tier 기준표 매칭 여부
- source별 가격 분포 차이

## 6. 클렌징 산출물 기준

- 모든 row는 아래 컬럼을 가져야 함
- `is_training_candidate`
- `cleaning_exclude_reasons`
- `audit_price_status`
- `audit_size_status`
- `audit_artist_status`
- `audit_medium_status`
- `audit_duplicate_status`
- `audit_gallery_status`

- 값이 바뀌는 경우 원본과 표준값을 모두 보존함
- 예시
- `price_raw`
- `price_krw`
- `width_raw`
- `width_cm`
- `medium_raw`
- `medium_category`

## 7. 피처 후보와 연결

- 가격 클렌징이 끝나야 target 사용 가능
- 크기 클렌징이 끝나야 아래 피처 생성 가능
- `area_cm2`
- `log_area`
- `aspect_ratio`
- `estimated_ho`
- `size_bucket`
- 재료/지지체 클렌징이 끝나야 아래 피처 생성 가능
- `medium_category`
- `support_category`
- `medium_support_bucket`
- 작가명 클렌징이 끝나야 아래 판단 가능
- Warm / Cold split
- artist_works_log
- artist history feature
- 저이력 작가 구간

## 8. 검증 기준

- 클렌징 전후 row 수를 출처별로 비교함
- 제외 row는 반드시 사유가 있어야 함
- 원본 row로 되돌아갈 수 있어야 함
- 표준 컬럼 결측률을 기록함
- 주요 이상값 샘플을 문서로 남김
- 클렌징 규칙 변경 시 결과 row 수가 얼마나 바뀌는지 기록함

## 9. 다음 실행 제안

- `T4-C1 가격 정합성`부터 진행함
- 이유
- 가격은 target이므로 가장 먼저 닫아야 함
- 가격 오류가 남으면 이후 피처 실험 결과가 의미 없어짐
- 이후 `T4-C2 크기 정합성`, `T4-C4 작가명 정합성` 순서로 진행함

