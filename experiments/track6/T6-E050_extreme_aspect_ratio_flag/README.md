# T6-E050 극단 가로세로 비율 플래그 실험

- 상태: 예정
- 상위 일지: `T6-E038 작품 변수 선정 실험 일지`
- 가설 ID: `H12`
- 가설: 극단적인 가로세로 비율 작품은 일반 작품과 가격 예측 오차 패턴이 다를 수 있다.
- 확인할 작품 피처: `aspect_ratio, is_extreme_aspect_ratio`
- 테스트 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 기준 피처: Warm 기준: artist_name_ko + ln_estimated_ho + aspect_ratio / Cold 기준: ln_estimated_ho + aspect_ratio
- 추가 피처: Warm/Cold 추가: is_extreme_aspect_ratio
- 학습 정답값: `ln_price_krw`
- 비교 기준: 비율 원값 모델과 극단 비율 flag 추가 모델 비교
- 유의미함 기준: 극단 비율 slice의 p95 APE가 감소하면 후보 유지

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
