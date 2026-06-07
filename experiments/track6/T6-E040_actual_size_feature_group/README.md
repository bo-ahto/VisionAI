# T6-E040 실제 크기 정보 추가 실험

- 상태: 예정
- 상위 일지: `T6-E038 작품 변수 선정 실험 일지`
- 가설 ID: `H2`
- 가설: 실제 크기 정보는 호수만 사용할 때보다 가격 예측을 개선한다.
- 확인할 작품 피처: `width_cm, height_cm, log_area, aspect_ratio`
- 테스트 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 실제 크기 컬럼: `width_cm + height_cm + log_area + aspect_ratio`
- 학습에 사용된 피처: `Warm 학습: artist_name_ko + ln_estimated_ho + width_cm + height_cm + log_area + aspect_ratio / Cold 학습: ln_estimated_ho + width_cm + height_cm + log_area + aspect_ratio`
- 테스트에 사용된 피처: `학습 피처와 동일`
- 학습 정답값: `ln_price_krw`
- 비교 기준: 기준 모델에 `width_cm + height_cm + log_area + aspect_ratio` 추가해 비교
- 유의미함 기준: Warm/Cold 중 하나 이상에서 median APE가 낮아지면 후보 유지

## 초기 실험 데이터

- 기준 원천 파일: `data/track6/track6_feature_candidates_name_corrected.csv`
- 입력 피처와 정답 가격은 분리해서 생성
- Warm 기준 조건: `artist_name_ko + ln_estimated_ho`
- Cold 기준 조건: `ln_estimated_ho`
- Cold에서는 `artist_name_ko` 제외

## 결과 기록 파일

- `outputs/metrics.csv`
- `outputs/predictions.csv`
- `outputs/slice_metrics.csv`
- `outputs/summary.md`
- `logs/run.log`
