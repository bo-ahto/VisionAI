# T6-E047 크기 대표값 vs 전체 크기 피처 실험

- 상태: 예정
- 상위 일지: `T6-E038 작품 변수 선정 실험 일지`
- 가설 ID: `H9`
- 가설: 크기 대표값 중심 피처는 전체 크기 피처를 모두 쓰는 방식보다 예측 오차를 줄일 수 있다.
- 확인할 작품 피처: `ln_estimated_ho vs width_cm, height_cm, log_area, aspect_ratio`
- 테스트 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 대표 크기 피처셋: Warm `artist_name_ko + ln_estimated_ho`, Cold `ln_estimated_ho`
- 전체 크기 피처셋: Warm `artist_name_ko + ln_estimated_ho + width_cm + height_cm + log_area + aspect_ratio`, Cold `ln_estimated_ho + width_cm + height_cm + log_area + aspect_ratio`
- 테스트에 사용된 피처: `학습 피처와 동일`
- 학습 정답값: `ln_price_krw`
- 비교 기준: 대표 크기 피처 모델과 전체 크기 피처 모델 비교
- 유의미함 기준: 대표값 모델이 성능 유지 또는 p95 APE 개선 시 채택

## 초기 실험 데이터

- 기준 원천 파일: `data/track6/track6_feature_candidates_name_corrected.csv`
- 입력 피처와 정답 가격은 분리해서 생성
- Warm 기준 조건: `artist_name_ko + ln_estimated_ho`
- Cold 기준 조건: `ln_estimated_ho`
- Cold에서는 `artist_name_ko` 제외

## 초기 실험 테스트: Warm

- 목적: Warm에서 크기를 대표값만 사용할지, 전체 크기 피처를 함께 사용할지 결정
- 대표 크기 모델 피처: `artist_name_ko + ln_estimated_ho`
- 전체 크기 모델 피처: `artist_name_ko + ln_estimated_ho + width_cm + height_cm + log_area + aspect_ratio`
- 추가 확인: median APE 개선과 p95 APE 악화 여부

## 초기 실험 테스트: Cold

- 목적: Cold에서 대표 크기만으로 충분한지 전체 크기 피처가 필요한지 확인
- 대표 크기 모델 피처: `ln_estimated_ho`
- 전체 크기 모델 피처: `ln_estimated_ho + width_cm + height_cm + log_area + aspect_ratio`
- 제외 피처: `artist_name_ko`
- 추가 확인: 대형 작품, 극단 비율 작품, 크기 결측 작품의 오차

## 결과 기록 파일

- `outputs/metrics.csv`
- `outputs/predictions.csv`
- `outputs/slice_metrics.csv`
- `outputs/summary.md`
- `logs/run.log`
