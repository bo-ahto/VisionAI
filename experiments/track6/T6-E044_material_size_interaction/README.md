# T6-E044 재료 x 크기 조합 피처 실험

- 상태: 예정
- 상위 일지: `T6-E038 작품 변수 선정 실험 일지`
- 가설 ID: `H6`
- 가설: 재료와 크기 조합 피처는 재료와 크기를 따로 넣는 것보다 가격 예측을 개선한다.
- 확인할 작품 피처: `nant_material_support_bucket, nant_material_idx_x_ho_bucket`
- 테스트 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 기준 피처: Warm `artist_name_ko + ln_estimated_ho`, Cold `ln_estimated_ho`
- 단독 재료 피처: `nant_material_idx + nant_tool`
- 단독 크기 피처: `width_cm + height_cm + log_area + aspect_ratio + ln_estimated_ho`
- 조합 피처: `nant_material_idx_x_ho_bucket`
- 학습에 사용된 피처:
  - Warm 단독 모델: `artist_name_ko + ln_estimated_ho + nant_material_idx + nant_tool + width_cm + height_cm + log_area + aspect_ratio`
  - Warm 조합 모델: `artist_name_ko + ln_estimated_ho + nant_material_idx_x_ho_bucket`
  - Cold 단독 모델: `ln_estimated_ho + nant_material_idx + nant_tool + width_cm + height_cm + log_area + aspect_ratio`
  - Cold 조합 모델: `ln_estimated_ho + nant_material_idx_x_ho_bucket`
- 테스트에 사용된 피처: `학습 피처와 동일`
- 학습 정답값: `ln_price_krw`
- 비교 기준: 단독 피처 모델과 조합 피처 모델 비교
- 유의미함 기준: 조합 피처 모델이 단독 피처 모델보다 성능이 좋으면 유지

## 초기 실험 데이터

- 기준 원천 파일: `data/track6/track6_feature_candidates_name_corrected.csv`
- 입력 피처와 정답 가격은 분리해서 생성
- Warm 기준 조건: `artist_name_ko + ln_estimated_ho`
- Cold 기준 조건: `ln_estimated_ho`
- Cold에서는 `artist_name_ko` 제외

## 초기 실험 테스트: Warm

- 목적: Warm에서 재료와 크기를 따로 넣는 방식보다 조합 피처가 더 나은지 확인
- 단독 모델 피처: `artist_name_ko + ln_estimated_ho + nant_material_idx + nant_tool + width_cm + height_cm + log_area + aspect_ratio`
- 조합 모델 피처: `artist_name_ko + ln_estimated_ho + nant_material_idx_x_ho_bucket`
- 추가 확인: 희소 bucket의 p95 APE

## 초기 실험 테스트: Cold

- 목적: 신규 작가에서 재료 x 크기 조합이 작품 자체 가격대를 더 잘 나누는지 확인
- 단독 모델 피처: `ln_estimated_ho + nant_material_idx + nant_tool + width_cm + height_cm + log_area + aspect_ratio`
- 조합 모델 피처: `ln_estimated_ho + nant_material_idx_x_ho_bucket`
- 제외 피처: `artist_name_ko`
- 추가 확인: 처음 보는 조합 bucket과 unknown bucket 비율

## 결과 기록 파일

- `outputs/metrics.csv`
- `outputs/predictions.csv`
- `outputs/slice_metrics.csv`
- `outputs/summary.md`
- `logs/run.log`
