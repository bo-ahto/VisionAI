# T6-E045 단계적 피처 선택 절차 실험

- 상태: 예정
- 상위 일지: `T6-E038 작품 변수 선정 실험 일지`
- 가설 ID: `H7`
- 가설: 단계적 피처 선택 방식은 전체 조합 탐색 없이도 기준 모델보다 좋은 피처 조합을 찾을 수 있다.
- 확인할 작품 피처: `전체 작품 피처 후보`
- 테스트 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 1단계 단일 추가 피처: `width_cm`, `height_cm`, `log_area`, `aspect_ratio`, `nant_material_idx`, `nant_tool`, `support_category`, `nant_support`, `depth_cm`, `has_depth`, `is_3d_candidate`
- 2단계 그룹 피처: size_group=`width_cm + height_cm + log_area + aspect_ratio`, material_group=`nant_material_idx + nant_tool`, support_group=`support_category + nant_support`, depth_3d_group=`depth_cm + has_depth + is_3d_candidate`
- 3단계 제거 실험: 2단계 채택 조합에서 피처를 하나씩 제거
- 테스트에 사용된 피처: `학습 피처와 동일`
- 학습 정답값: `ln_price_krw`
- 비교 기준: 단일 추가, 그룹 추가, 제거 실험 순서로 후보 축소
- 유의미함 기준: 최종 선택 조합이 기준 모델보다 성능 개선되면 절차 채택

## 초기 실험 데이터

- 기준 원천 파일: `data/track6/track6_feature_candidates_name_corrected.csv`
- 입력 피처와 정답 가격은 분리해서 생성
- Warm 기준 조건: `artist_name_ko + ln_estimated_ho`
- Cold 기준 조건: `ln_estimated_ho`
- Cold에서는 `artist_name_ko` 제외

## 초기 실험 테스트: Warm

- 목적: Warm에서 유효한 작품 피처를 단계적으로 줄여 최종 후보를 찾음
- 시작 기준 피처: `artist_name_ko + ln_estimated_ho`
- 1단계: 단일 피처 추가
- 2단계: size/material/support/depth 그룹 비교
- 3단계: 채택 조합에서 하나씩 제거
- 판단: Warm 개선 피처만 Warm 후보에 남김

## 초기 실험 테스트: Cold

- 목적: 신규 작가 예측에서 작가명 없이 유효한 작품 피처 조합을 별도로 찾음
- 시작 기준 피처: `ln_estimated_ho`
- 제외 피처: `artist_name_ko`
- 1단계: 단일 피처 추가
- 2단계: Cold 개선 피처만 그룹 비교
- 3단계: 제거 실험으로 p95 APE 악화 여부 확인
- 판단: Warm 결과만 보고 Cold 피처를 채택하지 않음

## 결과 기록 파일

- `outputs/metrics.csv`
- `outputs/predictions.csv`
- `outputs/slice_metrics.csv`
- `outputs/summary.md`
- `logs/run.log`
