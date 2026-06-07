# T6-E043 깊이/3D 정보 추가 실험

- 상태: 예정
- 상위 일지: `T6-E038 작품 변수 선정 실험 일지`
- 가설 ID: `H5`
- 가설: 깊이/3D 정보는 2D와 3D 작품을 구분해 예측하는 데 도움이 된다.
- 확인할 작품 피처: `depth_cm, has_depth, is_3d_candidate`
- 테스트 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 깊이/3D 컬럼: `depth_cm + has_depth + is_3d_candidate`
- 학습에 사용된 피처: `Warm 학습: artist_name_ko + ln_estimated_ho + depth_cm + has_depth + is_3d_candidate / Cold 학습: ln_estimated_ho + depth_cm + has_depth + is_3d_candidate`
- 테스트에 사용된 피처: `학습 피처와 동일`
- 학습 정답값: `ln_price_krw`
- 비교 기준: 깊이/3D 피처 추가 전후와 2D/3D slice별 오차 비교
- 유의미함 기준: 3D slice의 median APE 또는 p95 APE가 개선되면 후보 유지

## 초기 실험 데이터

- 기준 원천 파일: `data/track6/track6_feature_candidates_name_corrected.csv`
- 입력 피처와 정답 가격은 분리해서 생성
- Warm 기준 조건: `artist_name_ko + ln_estimated_ho`
- Cold 기준 조건: `ln_estimated_ho`
- Cold에서는 `artist_name_ko` 제외

## 초기 실험 테스트: Warm

- 목적: 기존 작가 작품에서 깊이/3D 정보가 2D와 3D 가격 차이를 설명하는지 확인
- 기준 모델 피처: `artist_name_ko + ln_estimated_ho`
- 깊이/3D 추가 모델 피처: `artist_name_ko + ln_estimated_ho + depth_cm + has_depth + is_3d_candidate`
- 추가 확인: 2D/3D slice, depth 결측 구간, p95 APE

## 초기 실험 테스트: Cold

- 목적: 신규 작가 3D 작품의 큰 오차를 줄일 수 있는지 확인
- 기준 모델 피처: `ln_estimated_ho`
- 깊이/3D 추가 모델 피처: `ln_estimated_ho + depth_cm + has_depth + is_3d_candidate`
- 제외 피처: `artist_name_ko`
- 추가 확인: 3D slice 개선과 2D slice 악화 여부

## 결과 기록 파일

- `outputs/metrics.csv`
- `outputs/predictions.csv`
- `outputs/slice_metrics.csv`
- `outputs/summary.md`
- `logs/run.log`
