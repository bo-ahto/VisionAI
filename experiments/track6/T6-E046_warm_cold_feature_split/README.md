# T6-E046 Warm/Cold 작품 피처 분리 실험

- 상태: 예정
- 상위 일지: `T6-E038 작품 변수 선정 실험 일지`
- 가설 ID: `H8`
- 가설: Warm과 Cold는 동일한 작품 피처 조합보다 각각 다른 피처 조합을 사용할 때 성능이 좋아질 수 있다.
- 확인할 작품 피처: `Warm/Cold 후보 피처 조합`
- 테스트 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 공통 피처셋: `ln_estimated_ho + nant_material_idx + nant_tool + nant_support + width_cm + height_cm + log_area + aspect_ratio`
- Warm 전용 피처셋: `artist_name_ko + ln_estimated_ho + nant_material_idx + nant_tool + nant_support + width_cm + height_cm + log_area + aspect_ratio`
- Cold 전용 피처셋: `ln_estimated_ho + nant_material_idx + nant_tool + nant_support + depth_cm + has_depth + is_3d_candidate`
- 테스트에 사용된 피처: Warm test는 Warm 전용 피처셋, Cold test는 Cold 전용 피처셋
- 학습 정답값: `ln_price_krw`
- 비교 기준: 공통 피처 모델과 Warm/Cold 분리 피처 모델 비교
- 유의미함 기준: 분리 피처 모델의 각 성능이 더 좋으면 채택

## 초기 실험 데이터

- 기준 원천 파일: `data/track6/track6_feature_candidates_name_corrected.csv`
- 입력 피처와 정답 가격은 분리해서 생성
- Warm 기준 조건: `artist_name_ko + ln_estimated_ho`
- Cold 기준 조건: `ln_estimated_ho`
- Cold에서는 `artist_name_ko` 제외

## 초기 실험 테스트: Warm

- 목적: Warm에서 공통 피처셋보다 Warm 전용 피처셋이 나은지 확인
- 공통 피처셋: `ln_estimated_ho + nant_material_idx + nant_tool + nant_support + width_cm + height_cm + log_area + aspect_ratio`
- Warm 전용 피처셋: `artist_name_ko + ln_estimated_ho + nant_material_idx + nant_tool + nant_support + width_cm + height_cm + log_area + aspect_ratio`
- 판단: Warm 전용 피처셋이 개선되면 Warm/Cold 피처 분리 관리

## 초기 실험 테스트: Cold

- 목적: Cold에서 공통 피처셋보다 Cold 전용 피처셋이 나은지 확인
- 공통 피처셋: `ln_estimated_ho + nant_material_idx + nant_tool + nant_support + width_cm + height_cm + log_area + aspect_ratio`
- Cold 전용 피처셋: `ln_estimated_ho + nant_material_idx + nant_tool + nant_support + depth_cm + has_depth + is_3d_candidate`
- 제외 피처: `artist_name_ko`
- 추가 확인: Cold 2D/3D slice 개선 여부

## 결과 기록 파일

- `outputs/metrics.csv`
- `outputs/predictions.csv`
- `outputs/slice_metrics.csv`
- `outputs/summary.md`
- `logs/run.log`
