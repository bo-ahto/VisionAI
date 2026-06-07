# Track 6 컬럼 품질 검증 보고서

- 생성일: `2026-05-18`
- 상태: `review`
- fail 이슈: `0`
- review 이슈: `15`
- 이슈 CSV: `data/track6/quality/track6_column_quality_issues.csv`

## 1. 검증 범위

- 대상 파일: `track6_train`, `track6_val_warm`, `track6_test_warm`, `track6_val_cold`, `track6_test_cold`
- 확인 항목: 스키마, 필수 컬럼 결측, 숫자 범위, 파생값 계산 일치, 카테고리 unknown, Warm/Cold 누수
- 원본 추적 컬럼은 보존하되 모델 피처에서는 제외함

## 2. split 요약

| split | rows | artists | columns | medium unknown | support unknown |
|---|---:|---:|---:|---:|---:|
| `train` | `26,914` | `1,773` | `50` | `26` | `2,104` |
| `val_warm` | `519` | `178` | `50` | `0` | `53` |
| `test_warm` | `607` | `207` | `50` | `0` | `67` |
| `val_cold` | `2,753` | `172` | `50` | `0` | `148` |
| `test_cold` | `3,099` | `200` | `50` | `0` | `362` |

## 3. 핵심 통과 항목

- split 간 `_track6_row_id` 중복: `0`
- val_warm 작가 train 누락 rows: `0`
- test_warm 작가 train 누락 rows: `0`
- val_warm 최소 train 작품 수: `5`
- test_warm 최소 train 작품 수: `5`
- val_warm 1작품 작가 수: `0`
- test_warm 1작품 작가 수: `0`
- val_cold train 작가명 겹침: `0`
- test_cold train 작가명 겹침: `0`
- val_cold artist history nonzero rows: `0`
- test_cold artist history nonzero rows: `0`

## 4. 학습 후보 제외 사유 점검

- 전체 정제 rows: `54,842`
- `is_training_candidate=true`: `34,219`
- `is_training_candidate=false`: `20,623`
- false인데 제외 사유가 빈 rows: `0`
- true인데 제외 사유가 있는 rows: `0`
- 후보 플래그와 제외 사유 불일치 rows: `0`

제외 사유별 rows:

| reason | rows |
|---|---:|
| `missing_price_krw` | `18,928` |
| `duplicate_non_representative` | `1,956` |
| `missing_core_size` | `97` |
| `price_under_10000` | `55` |
| `width_or_height_over_1000cm` | `54` |
| `extreme_aspect_ratio` | `52` |
| `area_over_1m_cm2` | `33` |
| `area_under_10cm2` | `31` |
| `missing_medium_raw` | `28` |
| `price_over_1b` | `10` |
| `artist_audit_issue` | `2` |

## 5. 검토 필요 항목

| split | column | check | count | severity | note |
|---|---|---|---:|---|---|
| `train` | `title_raw` | `title_missing_or_blank` | `1` | `review` | 모델 피처는 아니지만 중복/감사용 확인 필요 |
| `train` | `width` | `width_above_review_max` | `3` | `review` | 극단값 후보. 모델 제외가 아니라 slice 확인 대상 |
| `train` | `height` | `height_above_review_max` | `17` | `review` | 극단값 후보. 모델 제외가 아니라 slice 확인 대상 |
| `train` | `depth` | `depth_above_review_max` | `6` | `review` | 극단값 후보. 모델 제외가 아니라 slice 확인 대상 |
| `train` | `aspect_ratio` | `aspect_ratio_above_review_max` | `4` | `review` | 극단값 후보. 모델 제외가 아니라 slice 확인 대상 |
| `train` | `medium_category` | `unknown_or_blank_category` | `26` | `review` |  |
| `train` | `support_category` | `unknown_or_blank_category` | `2,104` | `review` |  |
| `val_warm` | `support_category` | `unknown_or_blank_category` | `53` | `review` |  |
| `test_warm` | `support_category` | `unknown_or_blank_category` | `67` | `review` |  |
| `val_cold` | `width` | `width_above_review_max` | `11` | `review` | 극단값 후보. 모델 제외가 아니라 slice 확인 대상 |
| `val_cold` | `height` | `height_above_review_max` | `5` | `review` | 극단값 후보. 모델 제외가 아니라 slice 확인 대상 |
| `val_cold` | `depth` | `depth_above_review_max` | `1` | `review` | 극단값 후보. 모델 제외가 아니라 slice 확인 대상 |
| `val_cold` | `support_category` | `unknown_or_blank_category` | `148` | `review` |  |
| `test_cold` | `height` | `height_above_review_max` | `2` | `review` | 극단값 후보. 모델 제외가 아니라 slice 확인 대상 |
| `test_cold` | `support_category` | `unknown_or_blank_category` | `362` | `review` |  |

## 6. 해석

- 모델 실험을 막는 fail 이슈가 없으면 T6-E002 baseline으로 진행 가능
- `is_training_candidate=false`는 `cleaning_exclude_reasons`가 있는 row와 일치해야 함
- `support_category=unknown`은 일부 남아 있으므로 모델 입력 시 unknown 카테고리로 유지하고 slice 성능을 따로 확인
- `track4_source`, URL, image URL, source artwork ID는 품질 감사용이며 모델 피처로 사용하지 않음
