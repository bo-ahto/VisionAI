# Track 4 최종 데이터셋 품질 검토

- 기준일: 2026-05-17
- 대상 파일: `data/track4_primary_market_cleaned_v2.csv`
- 피처 후보 파일: `data/track4_primary_market_feature_candidates_v1.csv`
- split 폴더: `data/track4_split/`
- 컬럼별 상세 프로파일: `data/track4_dataset_column_profile_20260517.csv`

## 1. 결론

- 치명적인 split 누수는 발견되지 않음
- Cold 평가셋의 작가는 train과 겹치지 않음
- Cold 평가셋의 `artist_works_log`는 모두 0으로 재계산되어 있음
- train/eval 간 동일 작품 후보 key 겹침은 0건으로 확인됨
- 가격, 면적, 로그 면적, aspect ratio 파생값 계산 불일치는 0건임
- 다만 학습 후보 안에 크기 파싱 재검토가 필요한 극단값이 남아 있음
- `support_category=unknown` 비율이 높아 지지체 피처는 후속 실험에서 보수적으로 사용해야 함
- 따라서 모델 학습 전 최종 보완 우선순위는 크기 파싱 재검토임

## 2. 파일 크기와 row 수

- cleaned_v2 rows: `54,842`
- cleaned_v2 columns: `97`
- feature_candidates rows: `54,842`
- feature_candidates columns: `30`
- 학습 후보 rows: `34,239`

## 3. Split 점검

- train rows: `28,920`
- val_warm rows: `68`
- val_cold rows: `1,835`
- test_warm rows: `137`
- test_cold rows: `3,269`
- train artists: `1,836`
- val_warm artists: `68`
- val_cold artists: `108`
- test_warm artists: `137`
- test_cold artists: `216`
- val_warm 작가 중 train 미존재 수: `0`
- test_warm 작가 중 train 미존재 수: `0`
- val_cold 작가 train 겹침 수: `0`
- test_cold 작가 train 겹침 수: `0`
- val_cold `artist_works_log > 0` rows: `0`
- test_cold `artist_works_log > 0` rows: `0`
- val_warm train 동일 작품 후보 key 겹침 수: `0`
- val_cold train 동일 작품 후보 key 겹침 수: `0`
- test_warm train 동일 작품 후보 key 겹침 수: `0`
- test_cold train 동일 작품 후보 key 겹침 수: `0`

## 4. 핵심 컬럼 정합성

| 점검 항목 | 발견 rows |
|---|---:|
| price_krw <= 0 | 0 |
| ln_price_krw 계산 불일치 | 0 |
| area_cm2 계산 불일치 | 0 |
| log_area 계산 불일치 | 0 |
| aspect_ratio 계산 불일치 | 0 |
| has_depth 계산 불일치 | 0 |
| artist_key 결측 | 0 |
| artist_name_ko 결측 | 2 |
| 학습 후보 중 가격 결측 | 0 |
| 학습 후보 중 크기 결측 | 0 |
| 학습 후보 중 재료 unknown | 26 |
| 학습 후보 중 지지체 unknown | 2,786 |

## 5. 학습 후보 내 크기 재검토 필요 항목

- aspect_ratio > 10 rows: `34`
- depth_cm > 100 rows: `49`
- width_cm > 1000 또는 height_cm > 1000 rows: `7`
- 검토 샘플 파일: `data/track4_dataset_size_review_samples_20260517.csv`
- 해석
- 일부는 대형 설치/조각일 수 있음
- 일부는 `2.0 × 65.1 × 53.0 cm`처럼 두께가 첫 번째 값인데 width/height로 잘못 들어간 것으로 보임
- 일부는 `2227 × 15.8 cm`처럼 단위 또는 소수점 누락 가능성이 있음
- 조치
- 3개 치수에서 가장 작은 값이 두께로 보이는 회화/평면 작품은 depth로 재배치하는 규칙을 검토함
- width/height 1000cm 초과 값은 원문 URL 또는 이미지 기준으로 cm/mm/소수점 오류 여부를 확인함
- 크기 재검토 전에는 `aspect_ratio`, `area_cm2`, `log_area`, `estimated_ho` 계열 피처 해석에 주의해야 함

## 6. 출처별 row 수

- artsy: `30,046`
- saatchi: `21,721`
- artue: `2,783`
- gallery_primary: `292`

## 7. 재료/지지체 분포

- medium_category 상위 값
- mixed_media: `19,491`
- acrylic: `14,127`
- oil: `13,662`
- painting_material: `1,929`
- sculpture_material: `1,248`
- other: `1,142`
- ink: `1,008`
- ceramic: `615`
- print: `456`
- gouache: `345`
- pencil: `225`
- textile: `157`

- support_category 상위 값
- canvas: `32,502`
- paper: `9,752`
- unknown: `6,286`
- panel: `1,833`
- linen: `1,491`
- fabric: `1,124`
- wood: `797`
- metal: `656`
- glass: `401`

## 8. 학습 제외 사유

- missing_price_krw: `18,398`
- duplicate_non_representative: `1,534`
- missing_price_krw;duplicate_non_representative: `415`
- missing_price_krw;missing_core_size: `68`
- price_under_10000: `52`
- missing_core_size: `29`
- missing_medium_raw: `28`
- missing_price_krw;area_over_1m_cm2: `27`
- missing_price_krw;area_under_10cm2: `18`
- area_under_10cm2: `13`
- price_over_1b: `10`
- area_over_1m_cm2: `5`
- price_under_10000;duplicate_non_representative: `3`
- missing_price_krw;artist_audit_issue: `2`
- area_over_1m_cm2;duplicate_non_representative: `1`

## 9. 추적 컬럼 결측

- track4_source: `0`
- track4_source_row_index: `0`
- source_artwork_id: `0`
- artwork_url: `292`
- image_url: `3,108`

## 10. 컬럼별 상세 프로파일

- 전체 컬럼별 결측률, 고유값 수, 숫자 범위, 대표값은 아래 CSV에서 확인함
- `data/track4_dataset_column_profile_20260517.csv`

## 11. 운영/학습 전 주의사항

- `track4_source`, URL, image URL, source row index는 추적용이며 모델 피처로 쓰지 않음
- `gallery_tier_validated`는 현재 모델 피처에서 제외함
- `artist_name_ko`는 표시와 매칭 보조용이며, 최종 운영 라우팅은 내부 작가 ID 기준이 필요함
- Warm 평가셋 row 수가 작아 모델 성능 검증 시 반복 split 또는 내부 CV가 필요함
- 지지체 unknown이 많으므로 support 피처는 ablation으로 가치 확인 후 사용해야 함
- 가격 없는 작품은 예측 입력 후보로는 쓸 수 있지만 학습 target으로는 사용할 수 없음
- 현재 데이터셋은 split 구조 검증은 통과했지만, 크기 파싱 보완 후 다시 생성하는 것이 안전함
