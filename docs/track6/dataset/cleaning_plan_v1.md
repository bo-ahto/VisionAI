# Track 6 클렌징 계획서 v1

- 목적: Track6 split을 만들기 전에 데이터 품질 기준을 먼저 고정
- 배경: Track4/5에서 평가셋 크기, 작가명, 동명이인, Cold 이름 중복 문제가 성능 해석에 영향을 줌
- 원칙: 클렌징 → 학습 후보 확정 → 검증/테스트 우선 split → 남은 데이터 train 구성 순서로 진행
- 1차 입력 기준: `data/track4_primary_market_feature_candidates_v1.csv`
- Track6 보정 입력 기준: `data/track6/track6_feature_candidates_name_corrected.csv`

## 1. 전체 진행 순서

- 1단계: 입력 데이터 확인
- 2단계: 가격/크기/재료/지지체 핵심값 검증
- 3단계: 작가 이름 한글화 검증
- 4단계: 동명이인 후보 검증
- 5단계: 중복 작품 후보 검증
- 6단계: 학습 후보 row 확정
- 7단계: validation/test 우선 선정
- 8단계: 남은 데이터로 train 구성
- 9단계: split 품질 검증
- 10단계: split 보고서 생성

## 2. Track4에서 가져올 클렌징 기준

- 원본 추적 컬럼은 보존함
  - `track4_source`
  - `track4_source_row_index`
  - `source_artwork_id`
  - `artwork_url`
  - `image_url`
- 단, 위 컬럼은 모델 피처로 사용하지 않음
- 가격 없는 row는 학습 target이 없으므로 학습 후보에서 제외함
- 가격 이상값 기준은 Track4 기준을 우선 사용함
  - 1만 원 미만 제외
  - 10억 원 초과 제외
- 크기 핵심값이 없으면 학습 후보에서 제외함
  - `width_cm`
  - `height_cm`
  - `area_cm2`
  - `log_area`
- 재료 원문이 없으면 학습 후보에서 제외함
- `medium_category=unknown`, `support_category=unknown`은 즉시 제외하지 않고 후속 실험/위험 구간으로 관리함
- source, gallery tier, URL 계열은 모델 피처에서 제외함

## 3. Track6에서 강화할 클렌징 기준

### 작가 이름 한글화

- `artist_name_ko` 결측률을 먼저 확인함
- 학습 후보에서 `artist_name_ko` 결측이 있으면 split 전 보완 또는 제외 후보로 표시함
- `artist_name_ko_orig`가 있으면 원본 한글명을 보존함
- `artist_name_ko`와 `artist_name_ko_orig`가 다른 경우를 집계함
- 운영 라우팅은 작가 ID가 아니라 작가명 입력을 받을 수 있으므로 한글명 기준 검증을 필수로 둠
- 4글자 이상 한글식 이름 중 명백한 오표기는 `scripts/track6/artist_ko_overrides.csv`로 먼저 보정함
- 예명, 외국 작가명, 단체명처럼 확정이 어려운 값은 자동 수정하지 않고 검토 후보로 남김

### 동명이인 필터

- 같은 `artist_name_ko_orig` 안에 여러 `artist_key`가 있는지 확인함
- `is_homonym=True`인 rows 수를 기록함
- `artist_entity_suffix`가 있는 rows 수를 기록함
- 동명이인 후보는 split 전에 별도 목록으로 저장함
- Cold 평가셋에는 train과 같은 원본 한글명을 가진 작가를 넣지 않는 것을 원칙으로 함

### 1작가 1작품 평가 방지

- validation/test를 먼저 설계함
- Warm validation/test는 train에 충분히 남길 수 있는 작가에서만 holdout함
- Stable Warm 평가 작가는 holdout 후 train에 최소 5작품 이상 남기는 기준을 우선 적용함
- `5작품` 기준은 Warm/Cold 구분 기준이 아니라 Stable Warm 평가 안정성 기준임
- train 기준 1~4작품 작가는 Low-history Warm으로 별도 분석함
- Warm 평가셋은 작가당 2~3작품 holdout을 우선함
- Cold validation/test도 작가당 rows 분포를 확인함
- 평가셋 내 1작품 작가 수와 비율을 반드시 보고함

## 4. 학습 후보 row 기준

- 포함 조건:
  - `is_training_candidate=True`
  - `price_krw` 존재
  - `ln_price_krw` 존재
  - `width_cm`, `height_cm`, `area_cm2`, `log_area` 존재
  - `artist_key` 존재
  - `artist_name_ko` 존재
  - `medium_category` 존재
- 제외 후보:
  - 가격 결측
  - 가격 비정상
  - 크기 핵심값 결측
  - 극단 크기/비율 이상값
  - 대표가 아닌 중복 row
  - 작가 식별 불가
  - 한글 작가명 보완 불가

## 5. validation/test 우선 split 계획

- 평가셋을 먼저 충분히 확보한 뒤 남은 데이터를 train으로 둠
- 이유:
  - 평가셋이 작으면 성능 결론을 믿기 어려움
  - Track4의 Warm test 부족 문제를 반복하지 않기 위함
  - validation이 약하면 피처/모델 선택이 흔들림

### 목표 데이터 양

| split | 최소 rows | 최소 작가 수 | 주요 조건 |
|---|---:|---:|---|
| val_warm | 500 | 170 | Stable Warm: train에 최소 5작품 이상 남는 작가 |
| test_warm | 600 | 200 | Stable Warm: train에 최소 5작품 이상 남는 작가 |
| val_cold | 2,500 | 160 | train과 작가 ID/한글명 중복 0 |
| test_cold | 3,000 | 200 | train과 작가 ID/한글명 중복 0 |

## 6. split 생성 우선순위

- 1순위: Cold test 작가 선정
  - `artist_key`, `artist_name_ko`, `artist_name_ko_orig` 기준 train과 겹치지 않게 할 수 있는 작가
  - 작가당 여러 작품이 있는 작가 우선
- 2순위: Cold validation 작가 선정
  - Cold test와 겹치지 않음
  - train과 이름 기준도 겹치지 않음
- 3순위: Warm test 작품 holdout
  - train에 충분히 남길 수 있는 작가만 사용
  - 작가당 2~3작품 holdout 우선
- 4순위: Warm validation 작품 holdout
  - Warm test와 분리
  - 후보 선택에 충분한 rows와 작가 수 확보
- 5순위: 남은 데이터 train 구성
  - Cold val/test 작가는 train에서 완전히 제외
  - Warm val/test 작가는 train에 충분히 남김
  - train/eval 동일 작품 후보 제거

## 7. split 생성 후 검증 항목

- 전체 rows 수
- split별 rows 수
- split별 작가 수
- split별 작가당 rows 중앙값
- split별 1작품 작가 수
- Stable Warm 평가 작가의 train 작품 수 최솟값
- Stable Warm 평가 작가의 train 작품 수 분포
- Cold train `artist_key` 겹침
- Cold train `artist_name_ko` 겹침
- Cold train `artist_name_ko_orig` 겹침
- 동명이인 rows가 split별로 어떻게 배치됐는지
- train/eval 동일 작품 후보 겹침
- 가격 중앙값과 p90
- medium/support unknown 비율
- `artist_works_log`가 Cold에서 0인지 확인

## 8. 산출물

- 클렌징 검토 요약:
  - `docs/track6/dataset/cleaning_review.md`
- split 생성 보고서:
  - `docs/track6/dataset/split_report.md`
- split 요약 JSON:
  - `data/track6_split/track6_split_summary.json`
- split membership:
  - `data/track6_split/track6_split_membership.csv`
- split 파일:
  - `data/track6_split/track6_train.csv`
  - `data/track6_split/track6_val_warm.csv`
  - `data/track6_split/track6_test_warm.csv`
  - `data/track6_split/track6_val_cold.csv`
  - `data/track6_split/track6_test_cold.csv`
- feature/label 분리 파일:
  - `data/track6_split/features/warm/`
  - `data/track6_split/features/cold/`
  - `data/track6_split/labels/`

## 9. 실패 기준

- Cold test 또는 val에서 train과 `artist_key`가 겹치면 실패
- Cold test 또는 val에서 train과 `artist_name_ko_orig`가 겹치면 실패
- Warm test rows가 600 미만이면 실패 또는 기준 재검토
- Warm validation rows가 500 미만이면 실패 또는 기준 재검토
- Cold test rows가 3,000 미만이면 실패 또는 기준 재검토
- Cold validation rows가 2,500 미만이면 실패 또는 기준 재검토
- Warm 평가 작가의 train 남은 작품 수가 5 미만이면 해당 작가는 Warm 평가셋에서 제외
- split 후 `artist_works_log`가 Cold에서 0보다 크면 실패

## 10. 다음 작업

- T6-E001에서 이 계획을 기준으로 Track6 split 생성 스크립트를 작성
- 스크립트 실행 후 `cleaning_review.md`와 `split_report.md`를 자동 생성
- split이 기준을 통과하면 T6-E002 구조-only baseline으로 진행
