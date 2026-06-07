# C6 작가명 + 작품 기본 피처 묶음 실험 지시 기록

- 실험 목적:
  - 작가명만 넣은 기준선에서 작품 기본 피처 묶음이 추가로 가격 예측력을 높이는지 확인한다.
  - 작품 기본 피처 묶음은 운영 입력 가능성이 높은 `ln_estimated_ho`, `nant_material_idx`, `nant_tool`, `nant_support`로 정의한다.

- 학습 데이터:
  - `data/track6_split_with_year_type_edition_size_artist_name/features/warm/track6_train_warm_features.csv`
  - `data/track6_split_with_year_type_edition_size_artist_name/labels/track6_train_labels.csv`

- 테스트 데이터:
  - Warm: `data/track6_split_with_year_type_edition_size_artist_name/features/warm/track6_test_warm_warm_features.csv`
  - Warm label: `data/track6_split_with_year_type_edition_size_artist_name/labels/track6_test_warm_labels.csv`
  - Cold: `data/track6_split_with_year_type_edition_size_artist_name/features/cold/track6_test_cold_cold_features.csv`
  - Cold label: `data/track6_split_with_year_type_edition_size_artist_name/labels/track6_test_cold_labels.csv`

- 비교 피처:
  - 기준선: `artist_name_ko`
  - 추가 1: `artist_name_ko + ln_estimated_ho`
  - 추가 2: `artist_name_ko + ln_estimated_ho + nant_material_idx + nant_tool`
  - 최종 묶음: `artist_name_ko + ln_estimated_ho + nant_material_idx + nant_tool + nant_support`

- 구현 조건:
  - 공통 실행기 `scripts/track6/fixed_variable_experiment_runner.py`를 사용한다.
  - `_track6_row_id` 기준으로 feature와 label을 연결한다.
  - label은 학습 target과 metric 계산에만 사용한다.
  - `ln_estimated_ho`는 숫자형으로 처리하고 `StandardScaler`를 적용한다.
  - `artist_name_ko`, `nant_material_idx`, `nant_tool`, `nant_support`는 범주형으로 처리한다.
  - sampling 없이 전체 split을 사용한다.

- 평가 모델:
  - Warm: Huber / Linear Regression / Ridge
  - Cold: Huber / Quantile-LAD / LightGBM

- 평가 지표:
  - R2
  - RMSE(log)
  - MdAPE
  - p95 APE
  - Within-30
  - Within-50
  - MAPE

- 해석 기준:
  - Warm 결과를 중심으로 판단한다.
  - Cold 결과는 작가명이 학습에 없는 상황이므로 참고값으로만 본다.
