# T6-E039 호수 변수 영향 확인

- 상태: 예정
- 상위 일지: `T6-E038 작품 변수 선정 실험 일지`
- 가설 ID: `H1`
- 가설: 호수 변수가 가격 예측에 영향을 미친다.
- 확인할 작품 피처: `ln_estimated_ho`
- 테스트 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- Warm 1차 모델 학습 피처: `artist_name_ko + ln_estimated_ho`
- Warm 1차 테스트 피처: `artist_name_ko + ln_estimated_ho`
- Warm 2차 모델 학습 피처: `ln_estimated_ho`
- Warm 2차 테스트 피처: `ln_estimated_ho`
- Cold 모델 학습 피처: `ln_estimated_ho`
- Cold 테스트 피처: `ln_estimated_ho`
- 학습 정답값: `ln_price_krw`
- 연결 키: `_track6_row_id`
- 비교 기준: 가격 중앙값 기준 모델, 작가명+호수 모델, 호수 only 모델 비교
- 유의미함 기준: 같은 split과 같은 모델에서 median APE 또는 p95 APE가 낮아지면 유지

## 초기 실험 데이터

- 기준 원천 파일: `data/track6/track6_feature_candidates_name_corrected.csv`
- 입력 피처와 정답 가격은 분리해서 생성
- 입력 피처와 라벨은 `_track6_row_id`로 연결
- Warm 학습 피처는 1차 `artist_name_ko + ln_estimated_ho`, 2차 `ln_estimated_ho`로 나눠 비교
- Cold 학습 피처는 `ln_estimated_ho`
- Cold에서는 `artist_name_ko` 제외

## 결과 기록 파일

- `outputs/metrics.csv`
- `outputs/predictions.csv`
- `outputs/slice_metrics.csv`
- `outputs/summary.md`
- `logs/run.log`
