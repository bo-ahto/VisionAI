# Track 6 Split 정책서 v1

- 목적: Track6에서 사용할 최종 보고용 train/validation/test split 기준을 먼저 고정
- 상태: 초안
- 입력 원본: `data/track4_primary_market_feature_candidates_v1.csv`

## 1. 기본 원칙

- split은 모델 실험 전에 고정함
- split이 바뀌면 T6-E002 이후 실험은 다시 실행함
- Warm / Cold는 작가 기준으로 분리함
- validation은 후보 선택용으로만 사용함
- test는 최종 확인용으로만 사용함

## 2. Cold 기준

- Cold 평가는 신규 작가 상황을 의미함
- Cold 작가는 train에 없어야 함
- 확인 기준:
  - `artist_key` train 겹침 `0`
  - `artist_name_ko` train 겹침 `0`
  - `artist_name_ko_orig` train 겹침 `0`
- Cold 평가셋은 작가당 가능한 여러 작품을 포함함
- Cold 평가에서는 작가명과 작가 이력 피처를 사용하지 않음

## 3. Warm 기준

- Warm 평가는 학습 DB에 작가가 있는 상황을 의미함
- Warm 평가 작가는 train에 반드시 남아 있어야 함
- 우선 검토 기준:
  - Warm 평가 후보 작가는 전체 작품 수 8개 이상
  - 평가로 뺀 뒤 train에 최소 5작품 이상 남김
  - 평가셋에는 작가당 최대 3작품 holdout
- 기준을 만족하지 못하는 작가는 Warm test가 아니라 학습 또는 별도 low-history 분석 대상으로 둠

## 4. 동일 작품 후보 처리

- 같은 작품으로 볼 가능성이 높은 행은 train과 평가셋에 동시에 두지 않음
- 동일 작품 후보 판단 컬럼:
  - `artist_key`
  - `title_raw`
  - `price_krw`
  - `width_cm`
  - `height_cm`
  - `depth_cm`
  - `medium_category`
  - `support_category`
- 평가셋과 중복되는 동일 작품 후보가 train에 있으면 train에서 제거

## 5. 금지 피처

- 아래 컬럼은 모델 피처로 사용하지 않음
- `track4_source`
- `source_artwork_id`
- `artwork_url`
- `image_url`
- `gallery tier`
- `URL`
- 수집 출처 관련 컬럼

## 6. split 산출물

- `data/track6_split/track6_train.csv`
- `data/track6_split/track6_val_warm.csv`
- `data/track6_split/track6_test_warm.csv`
- `data/track6_split/track6_val_cold.csv`
- `data/track6_split/track6_test_cold.csv`
- `data/track6_split/track6_split_summary.json`
- `data/track6_split/track6_split_membership.csv`

## 7. split 검증 항목

- train/validation/test rows 수
- split별 작가 수
- Warm 평가 작가의 train 존재 여부
- Warm 평가 작가의 train 작품 수 분포
- Cold 평가 작가의 train 겹침 여부
- Cold 평가 작가명의 train 겹침 여부
- 동일 작품 후보 중복 제거 수
- 가격 분포 중앙값과 p90
- medium/support/size 결측률
