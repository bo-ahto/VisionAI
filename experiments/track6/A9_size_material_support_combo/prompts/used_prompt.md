# Track6 A9 실험 지시 기록

## 실험 제목

- A9: 크기 + 재료 + 지지체 조합 실험

## 실험 가설

- 크기와 재료에 지지체 정보를 추가하면 작품 자체 정보만 사용하는 가격 예측 성능이 개선될 수 있다.
- NANT 기준 지지체(`nant_support`)는 수집 지지체 대분류(`support_category`)보다 더 안정적인 지지체 표현일 수 있다.

## 실험 목적

- A8에서 확인한 크기 + 재료 조합에 지지체를 추가했을 때 MdAPE와 p95 APE가 낮아지는지 확인한다.
- 작가명을 사용하지 않고 작품 자체 정보만으로 구성한 기본 물성 모델 후보를 정한다.
- 이후 Group C, Group D에서 작가명과 결합할 작품 기본 피처 묶음 후보를 만든다.

## 사용 데이터

- 기준 split: `data/track6_split_with_year_type_edition_size`
- 학습 입력: `data/track6_split_with_year_type_edition_size/features/warm/track6_train_warm_features.csv`
- 학습 정답: `data/track6_split_with_year_type_edition_size/labels/track6_train_labels.csv`
- Warm 테스트 입력: `data/track6_split_with_year_type_edition_size/features/warm/track6_test_warm_warm_features.csv`
- Warm 테스트 정답: `data/track6_split_with_year_type_edition_size/labels/track6_test_warm_labels.csv`
- Cold 테스트 입력: `data/track6_split_with_year_type_edition_size/features/cold/track6_test_cold_cold_features.csv`
- Cold 테스트 정답: `data/track6_split_with_year_type_edition_size/labels/track6_test_cold_labels.csv`

## 라벨 사용 기준

- 가격 라벨은 학습 target과 평가 지표 계산에만 사용한다.
- 가격 라벨은 입력 피처에 포함하지 않는다.
- 입력 피처와 정답 가격은 `_track6_row_id`로만 연결한다.

## 공통 실행 기준

- 공통 실행 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 실험별 차이는 `experiment_config.json`의 변수 조합만 바꾼다.
- 모델군, 데이터 split, 평가 지표, 출력 형식은 고정한다.
- 숫자형 피처는 중앙값 결측 보정 후 `StandardScaler`를 적용한다.

## 변수 타입 처리 기준

- 숫자형 피처:
  - `ln_estimated_ho`
  - `log_area`
  - `width_cm`
  - `height_cm`
- 숫자형 피처는 `numeric_features`에 명시한다.
- 숫자형 피처는 `pd.to_numeric()`으로 변환한다.
- 숫자형 피처는 one-hot 변환하지 않고 `SimpleImputer(strategy="median") + StandardScaler`로 처리한다.
- 범주형 피처:
  - `medium_category`
  - `collected_material_raw_bucket`
  - `nant_material_idx`
  - `nant_tool`
  - `support_category`
  - `nant_support`
- 범주형 피처는 문자열로 변환하고 결측은 `__missing__`으로 처리한다.
- 범주형 피처는 one-hot encoding으로 처리한다.
- `collected_material_raw_bucket`은 수집 원문 재료명(`collected_material_raw`)을 학습 데이터 빈도 기준으로 묶은 변수다.
- `collected_material_raw_bucket`은 상위 80개 원문 재료명은 그대로 유지하고, 나머지는 `other_raw_material`로 합친다.

## 실험 변수 조합

- `log_area + nant_material_idx + nant_support`
- `log_area + nant_material_idx + support_category`
- `log_area + medium_category + nant_support`
- `log_area + medium_category + support_category`
- `ln_estimated_ho + log_area + width_cm + height_cm + collected_material_raw_bucket + nant_support`
- `ln_estimated_ho + log_area + width_cm + height_cm + collected_material_raw_bucket + support_category`
- `log_area + nant_material_idx + nant_tool + nant_support`

## 중복 제거 기준

- 같은 피처셋을 이름만 바꿔 반복하지 않는다.
- A8/A8-2의 최고 후보를 참조하더라도 이미 같은 피처셋이 있으면 별도 블록으로 중복 실행하지 않는다.
- A8-2 Warm 최고 후보는 `collected_material_raw_bucket`을 포함한 조합으로 반영한다.

## 모델군

- Warm:
  - Huber
  - Linear Regression
  - Ridge
- Cold:
  - Huber
  - Quantile-LAD
  - LightGBM

## 평가 지표

- R2
- MdAPE
- p95 APE
- Within-30
- Within-50
- MAPE

## 판단 기준

- A8 또는 A8-2의 같은 크기/재료 기준 대비 MdAPE가 낮아지면 지지체 추가 효과가 있다고 본다.
- MdAPE가 낮아져도 p95 APE가 커지면 안정성은 보류한다.
- Warm에서만 개선되면 Warm 후보 피처로 분리한다.
- Cold에서만 개선되면 Cold 후보 피처로 분리한다.
- `support_category`와 `nant_support`는 의미가 겹칠 수 있으므로 최종 후보에서는 둘 중 하나를 우선 선택한다.

## 재현성 확인 절차

- 1차 실행 결과를 baseline으로 저장한다.
- 동일한 데이터, 동일한 설정, 동일한 공통 실행 코드로 2차 실행을 다시 수행한다.
- 2차 실행 결과는 rerun 파일로 별도 저장한다.
- baseline과 rerun의 row 수, key, 주요 지표를 비교한다.
- 비교 key:
  - `experiment_id`
  - `variable_block`
  - `scope`
  - `model_code`
  - `model_name`
- 재현 성공 기준:
  - row 수가 동일하다.
  - key가 모두 일치한다.
  - `R2`, `MdAPE`, `p95_APE`, `Within_30`, `Within_50`, `MAPE`의 최대 차이가 `1e-12` 이하다.
