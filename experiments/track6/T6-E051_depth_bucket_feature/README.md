# T6-E051 깊이 구간화 피처 실험

- 상태: 예정
- 상위 일지: `T6-E038 작품 변수 선정 실험 일지`
- 가설 ID: `H13`
- 가설: 0에 가까운 깊이와 실제 3D에 가까운 깊이는 가격 차이를 다르게 설명할 수 있다.
- 확인할 작품 피처: `depth_cm, has_depth, is_3d_candidate, depth_bucket`
- 테스트 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 기준 피처: Warm 기준: artist_name_ko + ln_estimated_ho + has_depth + is_3d_candidate / Cold 기준: ln_estimated_ho + has_depth + is_3d_candidate
- 추가 피처: Warm/Cold 추가: depth_cm 기반 depth_bucket
- 학습 정답값: `ln_price_krw`
- 비교 기준: has_depth만 사용한 모델과 depth 구간화 모델 비교
- 유의미함 기준: 3D/depth slice 오차가 개선되면 후보 유지

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
