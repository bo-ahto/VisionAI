# T6-E053 긴 변/짧은 변 크기 피처 실험

- 상태: 예정
- 상위 일지: `T6-E038 작품 변수 선정 실험 일지`
- 가설 ID: `H15`
- 가설: 가격 예측에는 면적보다 긴 변 또는 짧은 변 정보가 더 도움이 될 수 있다.
- 확인할 작품 피처: `width_cm, height_cm, log_area, max_side_cm, min_side_cm`
- 테스트 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 기준 피처: Warm 기준: artist_name_ko + ln_estimated_ho + log_area / Cold 기준: ln_estimated_ho + log_area
- 추가 피처: Warm/Cold 추가: max_side_cm + min_side_cm
- 학습 정답값: `ln_price_krw`
- 비교 기준: 면적 중심 모델과 긴 변/짧은 변 모델 비교
- 유의미함 기준: 전체 또는 대형 작품 slice 오차가 개선되면 후보 유지

## 초기 실험 데이터

- 기준 원천 파일: `data/track6/track6_feature_candidates_name_corrected.csv`
- 입력 피처와 정답 가격은 분리해서 생성
- Cold에서는 `artist_name_ko` 제외

## 결과 기록 파일

- `outputs/metrics.csv`
- `outputs/predictions.csv`
- `outputs/slice_metrics.csv`
- `outputs/summary.md`
- `logs/run.log`
